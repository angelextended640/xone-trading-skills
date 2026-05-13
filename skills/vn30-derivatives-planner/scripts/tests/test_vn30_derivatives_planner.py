"""Tests for vn30-derivatives-planner."""

import argparse
from datetime import date

import pytest

from vn30_derivatives_planner import (
    BROKER_FEES_PER_CONTRACT,
    DEFAULT_IM_PCT,
    HNX_FEE_PER_CONTRACT,
    MULTIPLIER,
    OVERNIGHT_FEE_PER_CONTRACT,
    VSDC_FEE_PER_CONTRACT,
    basis_points,
    build_parser,
    compute_cost_per_broker,
    compute_hedge_contracts,
    compute_trade_plan,
    contract_notional,
    days_until,
    front_month_expiry,
    im_required,
    run_cost,
    run_hedge,
    run_plan,
    run_roll,
    third_thursday,
)


# ---------------------------------------------------------------------------
# Contract spec constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_multiplier(self):
        assert MULTIPLIER == 100_000

    def test_im_default(self):
        assert DEFAULT_IM_PCT == 18.0

    def test_brokers_loaded(self):
        assert "vps" in BROKER_FEES_PER_CONTRACT
        assert "dnse" in BROKER_FEES_PER_CONTRACT
        # DNSE should be cheapest
        cheapest = min(BROKER_FEES_PER_CONTRACT, key=BROKER_FEES_PER_CONTRACT.get)
        assert cheapest == "dnse"


# ---------------------------------------------------------------------------
# Notional + IM
# ---------------------------------------------------------------------------


class TestNotionalAndIM:
    def test_contract_notional(self):
        # 1283.0 points × 100,000 = 128,300,000 VND
        assert contract_notional(1283.0) == 128_300_000

    def test_im_default_18pct(self):
        # 128.3M × 18% = 23,094,000
        assert im_required(1283.0) == pytest.approx(23_094_000, abs=1)

    def test_im_custom_20pct(self):
        assert im_required(1283.0, im_pct=20) == pytest.approx(25_660_000, abs=1)


# ---------------------------------------------------------------------------
# Third Thursday + roll calendar
# ---------------------------------------------------------------------------


class TestThirdThursday:
    def test_may_2026(self):
        # May 2026: 1st is Friday, so 1st Thu is May 7, 3rd Thu is May 21
        assert third_thursday(2026, 5) == date(2026, 5, 21)

    def test_jan_2026(self):
        # Jan 2026: 1st is Thursday, so 1st Thu is Jan 1, 3rd Thu is Jan 15
        assert third_thursday(2026, 1) == date(2026, 1, 15)


class TestFrontMonthExpiry:
    def test_before_3rd_thursday_same_month(self):
        # 2026-05-13 (Wed before 3rd Thu of May)
        assert front_month_expiry(date(2026, 5, 13)) == date(2026, 5, 21)

    def test_after_3rd_thursday_rolls_to_next(self):
        # 2026-05-22 (Fri after 3rd Thu of May) → roll to June 3rd Thu
        next_expiry = front_month_expiry(date(2026, 5, 22))
        assert next_expiry == date(2026, 6, 18)

    def test_december_rolls_to_january(self):
        # 2026-12-31 after Dec 3rd Thu → Jan 2027 3rd Thu
        # Jan 2027: 1st is Friday → 1st Thu is Jan 7 → 3rd Thu is Jan 21
        assert front_month_expiry(date(2026, 12, 31)) == date(2027, 1, 21)


class TestBasis:
    def test_positive_basis(self):
        assert basis_points(1285.0, 1280.0) == 5.0

    def test_negative_basis(self):
        assert basis_points(1278.0, 1280.0) == -2.0


# ---------------------------------------------------------------------------
# Hedge sizing
# ---------------------------------------------------------------------------


class TestComputeHedgeContracts:
    def test_basic_hedge(self):
        # 1B VND, beta 1.0, VN30 spot 1280 → notional/contract = 128M
        # Hedge contracts = 1B / 128M = 7.81 → 8 contracts
        r = compute_hedge_contracts(
            cash_exposure_vnd=1_000_000_000,
            portfolio_beta=1.0,
            vn30_spot=1280.0,
            hedge_ratio=1.0,
        )
        assert r["contracts_actual"] == 8
        assert r["contract_notional_vnd"] == 128_000_000
        assert r["total_notional_vnd"] == 1_024_000_000
        # IM at 18% = 184.32M
        assert r["im_required_vnd"] == pytest.approx(184_320_000, abs=10)

    def test_beta_adjusted(self):
        # Beta 1.5 → need 50% more contracts
        r = compute_hedge_contracts(
            cash_exposure_vnd=1_000_000_000,
            portfolio_beta=1.5,
            vn30_spot=1280.0,
            hedge_ratio=1.0,
        )
        # 1B × 1.5 / 128M = 11.72 → 12
        assert r["contracts_actual"] == 12

    def test_half_hedge(self):
        r = compute_hedge_contracts(
            cash_exposure_vnd=1_000_000_000,
            portfolio_beta=1.0,
            vn30_spot=1280.0,
            hedge_ratio=0.5,
        )
        # Half of basic = 4
        assert r["contracts_actual"] == 4

    def test_validation_negative_exposure(self):
        with pytest.raises(ValueError, match="exposure"):
            compute_hedge_contracts(-1000, 1.0, 1280.0, 1.0)

    def test_validation_bad_hedge_ratio(self):
        with pytest.raises(ValueError, match="hedge_ratio"):
            compute_hedge_contracts(1_000_000_000, 1.0, 1280.0, 2.0)


# ---------------------------------------------------------------------------
# Trade plan
# ---------------------------------------------------------------------------


class TestComputeTradePlan:
    def test_short_plan_basic(self):
        # 1B account, short 1283 → 1300 stop (17 pt risk = 1.7M/contract)
        # 1% risk = 10M → 5 contracts
        plan = compute_trade_plan(
            account_size_vnd=1_000_000_000,
            side="short",
            entry=1283.0,
            stop=1300.0,
            risk_pct=1.0,
            im_pct=18.0,
            target_r_multiples=[1, 2, 3],
        )
        tp = plan["trade_plan"]
        assert tp["side"] == "short"
        assert tp["risk_per_point"] == 17.0
        assert tp["risk_per_contract_vnd"] == 1_700_000
        assert tp["contracts"] == 5  # floor of 10M/1.7M
        assert tp["max_loss_vnd"] == 8_500_000  # 5 × 1.7M
        # Notional = 5 × 1283 × 100k = 641.5M
        assert tp["notional_vnd"] == 641_500_000

    def test_short_targets_decrease(self):
        plan = compute_trade_plan(
            1_000_000_000, "short", 1283.0, 1300.0, 1.0, 18.0, [1, 2, 3]
        )
        tp = plan["trade_plan"]
        # Short: targets are BELOW entry, decreasing
        prices = [t["price"] for t in tp["targets"]]
        assert prices[0] == 1266.0  # 1283 - 17
        assert prices[1] == 1249.0  # 1283 - 34
        assert prices[2] == 1232.0  # 1283 - 51

    def test_long_plan(self):
        plan = compute_trade_plan(
            1_000_000_000, "long", 1280.0, 1265.0, 1.0, 18.0, [1, 2]
        )
        tp = plan["trade_plan"]
        # Long targets above entry
        assert tp["targets"][0]["price"] == 1295.0  # 1280 + 15
        assert tp["targets"][1]["price"] == 1310.0

    def test_validation_short_stop_below_entry_rejected(self):
        with pytest.raises(ValueError, match="Short"):
            compute_trade_plan(
                1_000_000_000, "short", 1283.0, 1260.0, 1.0, 18.0, [1, 2, 3]
            )

    def test_validation_long_stop_above_entry_rejected(self):
        with pytest.raises(ValueError, match="Long"):
            compute_trade_plan(
                1_000_000_000, "long", 1280.0, 1300.0, 1.0, 18.0, [1, 2, 3]
            )

    def test_im_warning_when_overleveraged(self):
        # Very tight stop → many contracts → high IM
        plan = compute_trade_plan(
            account_size_vnd=100_000_000,  # small account
            side="short",
            entry=1283.0,
            stop=1284.0,  # very tight 1 point
            risk_pct=5.0,
            im_pct=18.0,
            target_r_multiples=[1, 2, 3],
        )
        # 5% of 100M = 5M risk → 5M / 100k = 50 contracts
        # Notional 50 × 128.3M = 6.4B; IM at 18% = 1.15B (way over account)
        assert plan["im_warning"] is not None
        assert "over-leveraged" in plan["im_warning"]

    def test_zero_contracts_raises(self):
        # Huge stop distance with tiny account
        with pytest.raises(ValueError, match="không đủ"):
            compute_trade_plan(
                account_size_vnd=10_000_000,  # 10M
                side="short",
                entry=1283.0,
                stop=1400.0,  # 117 pt = 11.7M/contract
                risk_pct=1.0,  # 100k risk budget
                im_pct=18.0,
                target_r_multiples=[1, 2, 3],
            )


# ---------------------------------------------------------------------------
# Cost comparison
# ---------------------------------------------------------------------------


class TestComputeCostPerBroker:
    def test_short_winning_trade_no_overnight(self):
        # 5 contracts short, 1283 → 1265 (18 pt drop), VPS 2700/side
        r = compute_cost_per_broker(
            contracts=5,
            entry=1283.0,
            exit_price=1265.0,
            side="short",
            broker_fee=2_700,
            nights_held=0,
        )
        # Gross P&L = (1283 - 1265) × 100k × 5 = 9M
        assert r["gross_pnl_vnd"] == 9_000_000
        # Round-trip per contract: 2×broker(2700) + 2×HNX(2700) + 2×VSDC(2550) = 15,900
        # × 5 contracts = 79,500
        assert r["round_trip_fee_vnd"] == 79_500
        assert r["overnight_fee_vnd"] == 0
        # Net = 9M - 79,500 = 8,920,500
        assert r["net_pnl_vnd"] == 8_920_500

    def test_overnight_adds_cost(self):
        r = compute_cost_per_broker(
            contracts=5, entry=1283.0, exit_price=1265.0, side="short",
            broker_fee=2_700, nights_held=3,
        )
        # Overnight = 3 × 3000 × 5 = 45,000
        assert r["overnight_fee_vnd"] == 45_000

    def test_no_sale_tax_unlike_cash(self):
        # Confirm net P&L doesn't deduct 0.1% sale tax
        r = compute_cost_per_broker(
            contracts=1, entry=1283.0, exit_price=1283.0, side="short",
            broker_fee=2_700, nights_held=0,
        )
        # Same entry / exit: gross = 0, net = -fees only (no tax)
        # Round-trip = 2×broker(2700) + 2×HNX(2700) + 2×VSDC(2550) = 15,900
        assert r["round_trip_fee_vnd"] == 15_900
        assert r["gross_pnl_vnd"] == 0
        assert r["net_pnl_vnd"] == -15_900


# ---------------------------------------------------------------------------
# Run subcommands end-to-end
# ---------------------------------------------------------------------------


def make_args(**kwargs):
    defaults = dict(
        current_contract="VN30F1M",
        reference_date=None,
        vn30_spot=None,
        futures_price=None,
        cash_exposure_vnd=1_000_000_000,
        portfolio_beta=1.0,
        hedge_ratio=1.0,
        account_size_vnd=1_000_000_000,
        side="short",
        entry=1283.0,
        stop=1300.0,
        risk_pct=1.0,
        im_pct=DEFAULT_IM_PCT,
        targets="1,2,3",
        contracts=5,
        exit=1265.0,
        brokers=None,
        nights_held=0,
        output_dir="/tmp",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestRunRoll:
    def test_roll_with_basis(self):
        result = run_roll(
            make_args(reference_date="2026-05-13", vn30_spot=1280.0, futures_price=1283.0)
        )
        assert result["front_month_expiry"] == "2026-05-21"
        assert result["basis_points"] == 3.0
        assert result["basis_vnd_per_contract"] == 300_000

    def test_roll_in_window(self):
        # 2026-05-18 is Mon, within 4 days of May 21 Thu
        result = run_roll(make_args(reference_date="2026-05-18"))
        assert result["in_roll_window"] is True

    def test_roll_not_in_window(self):
        # 2026-05-05 is way before
        result = run_roll(make_args(reference_date="2026-05-05"))
        assert result["in_roll_window"] is False


class TestRunHedge:
    def test_basic(self):
        result = run_hedge(
            make_args(cash_exposure_vnd=1_000_000_000, portfolio_beta=1.0, vn30_spot=1280.0)
        )
        assert result["result"]["contracts_actual"] == 8


class TestRunPlan:
    def test_short_plan_produces_targets(self):
        result = run_plan(make_args())
        assert result["trade_plan"]["contracts"] == 5
        assert len(result["trade_plan"]["targets"]) == 3


class TestRunCost:
    def test_compare_default_brokers(self):
        result = run_cost(make_args())
        # All 8 built-in brokers
        assert len(result["rows"]) == 8
        # DNSE should be best (cheapest fee → highest net)
        assert result["best_broker"] == "DNSE"

    def test_specific_brokers(self):
        result = run_cost(make_args(brokers="vps,dnse"))
        assert len(result["rows"]) == 2

    def test_invalid_broker_rejected(self):
        with pytest.raises(ValueError, match="Unknown broker"):
            run_cost(make_args(brokers="notarealbroker"))


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


class TestArgParser:
    def test_hedge_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "hedge",
                "--cash-exposure-vnd", "1000000000",
                "--portfolio-beta", "1.05",
                "--vn30-spot", "1280",
            ]
        )
        assert args.subcommand == "hedge"
        assert args.cash_exposure_vnd == 1_000_000_000

    def test_plan_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "plan",
                "--account-size", "1000000000",
                "--side", "short",
                "--entry", "1283",
                "--stop", "1300",
            ]
        )
        assert args.subcommand == "plan"
        assert args.side == "short"

    def test_invalid_side_rejected(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "plan",
                    "--account-size", "1000000000",
                    "--side", "flat",
                    "--entry", "1283",
                    "--stop", "1300",
                ]
            )
