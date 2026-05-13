"""Tests for vn-tax-fee-calculator."""

import argparse
import json
from pathlib import Path

import pytest

from vn_tax_fee_calculator import (
    PROFILES_PATH,
    build_parser,
    compute_dividend_tax,
    compute_monthly_overhead,
    compute_trade_costs,
    load_profiles,
    resolve_broker,
    run_compare,
    run_dividend,
    run_monthly,
    run_trade,
)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


class TestProfiles:
    def test_profiles_load(self):
        p = load_profiles()
        assert "brokers" in p
        assert "global" in p
        assert "vps" in p["brokers"]

    def test_global_constants(self):
        p = load_profiles()
        g = p["global"]
        assert g["sale_tax_pct"] == 0.10
        assert g["cash_dividend_tax_pct"] == 5.0
        assert g["custody_fee_per_share_per_month_vnd"] == 0.27

    def test_resolve_broker_case_insensitive(self):
        p = load_profiles()
        assert resolve_broker(p, "VPS")["display_name"] == "VPS"
        assert resolve_broker(p, "vps")["display_name"] == "VPS"

    def test_resolve_broker_unknown_raises(self):
        p = load_profiles()
        with pytest.raises(ValueError, match="Unknown broker"):
            resolve_broker(p, "nonexistent")


# ---------------------------------------------------------------------------
# compute_trade_costs
# ---------------------------------------------------------------------------


class TestTradeCosts:
    def test_winning_trade_vic_golden(self):
        """1000 VIC bought 45k, sold 48k, VPS 0.15%."""
        result = compute_trade_costs(1000, 45_000, 48_000, 0.15, 0.10)
        c = result["costs"]
        p = result["pnl"]
        assert c["entry_value_vnd"] == 45_000_000
        assert c["exit_value_vnd"] == 48_000_000
        # buy_fee = 45M × 0.15% = 67,500
        assert c["buy_fee_vnd"] == 67_500
        # sell_fee = 48M × 0.15% = 72,000
        assert c["sell_fee_vnd"] == 72_000
        # sell_tax = 48M × 0.1% = 48,000
        assert c["sell_tax_vnd"] == 48_000
        assert c["total_cost_vnd"] == 67_500 + 72_000 + 48_000  # 187,500
        # round-trip pct of entry: 187,500 / 45,000,000 = 0.417%
        assert c["total_cost_pct_of_entry"] == 0.417
        # gross = 3M, net = 2,812,500
        assert p["gross_pnl_vnd"] == 3_000_000
        assert p["net_pnl_vnd"] == 2_812_500
        assert p["net_pnl_pct"] == round(2_812_500 / 45_000_000 * 100, 3)

    def test_losing_trade_still_taxed(self):
        """Loss case: sale tax still applies even on losing trade."""
        result = compute_trade_costs(1000, 45_000, 43_000, 0.15, 0.10)
        c = result["costs"]
        p = result["pnl"]
        # sale tax = 43M × 0.1% = 43,000 (still charged)
        assert c["sell_tax_vnd"] == 43_000
        # gross = -2M, total cost = 67,500 + 64,500 + 43,000 = 175,000
        assert p["gross_pnl_vnd"] == -2_000_000
        assert p["net_pnl_vnd"] == -2_000_000 - 175_000

    def test_breakeven_is_about_04_pct(self):
        """For 0.15% fee + 0.1% sale tax, break-even ~0.4%."""
        result = compute_trade_costs(1000, 45_000, 45_000, 0.15, 0.10)
        b = result["breakeven"]
        assert 0.35 < b["min_pct_gain_to_breakeven"] < 0.45

    def test_validation_errors(self):
        with pytest.raises(ValueError):
            compute_trade_costs(0, 45_000, 48_000, 0.15, 0.10)
        with pytest.raises(ValueError):
            compute_trade_costs(1000, 0, 48_000, 0.15, 0.10)
        with pytest.raises(ValueError):
            compute_trade_costs(1000, 45_000, 48_000, -0.1, 0.10)


# ---------------------------------------------------------------------------
# compute_dividend_tax
# ---------------------------------------------------------------------------


class TestDividendTax:
    def test_cash_dividend(self):
        p = load_profiles()
        result = compute_dividend_tax(3300, 2500, is_stock_dividend=False, profiles=p)
        assert result["dividend_type"] == "cash"
        # gross = 3300 × 2500 = 8,250,000
        # tax = 5% = 412,500
        # net = 7,837,500
        assert result["gross_dividend_vnd"] == 8_250_000
        assert result["tax_vnd"] == 412_500
        assert result["net_dividend_vnd"] == 7_837_500

    def test_stock_dividend(self):
        """Stock dividend ratio 10% → 100 shares get 10 new shares; tax = par × shares × 5%."""
        p = load_profiles()
        result = compute_dividend_tax(1000, 0.10, is_stock_dividend=True, profiles=p)
        assert result["dividend_type"] == "stock"
        # shares_received = 1000 × 0.10 = 100
        # gross = 100 × 10,000 (par) = 1,000,000
        # tax = 5% × 1M = 50,000
        assert result["shares_received"] == 100
        assert result["gross_dividend_vnd"] == 1_000_000
        assert result["tax_vnd"] == 50_000


# ---------------------------------------------------------------------------
# compute_monthly_overhead
# ---------------------------------------------------------------------------


class TestMonthlyOverhead:
    def test_custody_only(self):
        p = load_profiles()
        result = compute_monthly_overhead(50_000, 0, 0, p)
        # 50,000 × 0.27 = 13,500
        assert result["custody_fee_monthly_vnd"] == 13_500
        assert result["advance_fee_vnd"] == 0
        assert result["total_monthly_overhead_vnd"] == 13_500

    def test_with_advance(self):
        p = load_profiles()
        result = compute_monthly_overhead(50_000, 100_000_000, 5, p)
        # advance = 100M × 0.04% × 5 = 200,000
        assert result["advance_fee_vnd"] == 200_000
        assert result["total_monthly_overhead_vnd"] == 13_500 + 200_000

    def test_custom_advance_rate(self):
        p = load_profiles()
        result = compute_monthly_overhead(0, 100_000_000, 10, p, advance_fee_pct_per_day=0.05)
        assert result["advance_fee_pct_per_day"] == 0.05
        # 100M × 0.05% × 10 = 500,000
        assert result["advance_fee_vnd"] == 500_000


# ---------------------------------------------------------------------------
# Run subcommands
# ---------------------------------------------------------------------------


def make_args(**kwargs):
    defaults = dict(
        shares=1000,
        entry=45_000,
        exit=48_000,
        broker=None,
        custom_broker=None,
        custom_fee_pct=None,
        sale_tax_pct=None,
        brokers=None,
        dividend_per_share=2500,
        stock=False,
        total_shares=50_000,
        advance_cash_vnd=None,
        advance_days=None,
        advance_fee_pct=None,
        output_dir="/tmp",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestRunTrade:
    def test_default_broker_vps(self):
        result = run_trade(make_args(broker="vps"))
        assert result["broker"] == "VPS"
        assert result["pnl"]["gross_pnl_vnd"] == 3_000_000

    def test_custom_broker(self):
        result = run_trade(make_args(custom_broker="MyBroker", custom_fee_pct=0.05))
        assert result["broker"] == "MyBroker"
        assert result["inputs"]["broker_fee_pct"] == 0.05

    def test_dnse_cheapest(self):
        """DNSE 0.03% should produce lower cost than VPS 0.15%."""
        vps = run_trade(make_args(broker="vps"))
        dnse = run_trade(make_args(broker="dnse"))
        assert dnse["costs"]["total_cost_vnd"] < vps["costs"]["total_cost_vnd"]
        assert dnse["pnl"]["net_pnl_vnd"] > vps["pnl"]["net_pnl_vnd"]


class TestRunCompare:
    def test_compare_default_brokers(self):
        result = run_compare(make_args())
        assert len(result["rows"]) >= 7  # at least the major brokers
        # DNSE should be best (lowest fee)
        assert result["best_broker"] == "DNSE"

    def test_compare_specific_brokers(self):
        result = run_compare(make_args(brokers="vps,dnse"))
        assert len(result["rows"]) == 2
        names = {r["broker"] for r in result["rows"]}
        assert names == {"VPS", "DNSE"}

    def test_compare_spread_positive(self):
        result = run_compare(make_args(brokers="vps,dnse"))
        assert result["spread_vnd"] > 0


class TestRunDividend:
    def test_cash_dividend(self):
        result = run_dividend(make_args(shares=3300, dividend_per_share=2500, stock=False))
        assert result["dividend_type"] == "cash"
        assert result["tax_vnd"] == 412_500


class TestRunMonthly:
    def test_with_advance(self):
        result = run_monthly(make_args(total_shares=50_000, advance_cash_vnd=100_000_000, advance_days=5))
        assert result["total_monthly_overhead_vnd"] == 13_500 + 200_000


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


class TestArgParser:
    def test_trade_required_args(self):
        parser = build_parser()
        args = parser.parse_args(
            ["trade", "--shares", "1000", "--entry", "45000", "--exit", "48000"]
        )
        assert args.subcommand == "trade"
        assert args.shares == 1000

    def test_compare_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(
            ["compare", "--shares", "1000", "--entry", "45000", "--exit", "48000"]
        )
        assert args.subcommand == "compare"

    def test_dividend_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(
            ["dividend", "--shares", "3300", "--dividend-per-share", "2500"]
        )
        assert args.subcommand == "dividend"
        assert args.stock is False

    def test_dividend_stock_flag(self):
        parser = build_parser()
        args = parser.parse_args(
            ["dividend", "--shares", "1000", "--dividend-per-share", "0.10", "--stock"]
        )
        assert args.stock is True
