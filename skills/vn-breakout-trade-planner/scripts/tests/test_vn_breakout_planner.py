"""Tests for vn-breakout-trade-planner."""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pytest

from vn_breakout_planner import (
    DEFAULT_BROKER_FEE_PCT,
    DEFAULT_SALE_TAX_PCT,
    PRICE_BAND_PCT,
    add_business_days,
    assemble_plan,
    compute_price_band,
    compute_sizing,
    compute_targets,
    estimate_fees,
    load_foreign_room_context,
    load_sector_context,
    round_to_lot,
    round_to_tick,
    t_plus_calendar,
)


# ---------------------------------------------------------------------------
# Sizing (mirrors vn-position-sizer logic)
# ---------------------------------------------------------------------------


class TestSizing:
    def test_vic_golden_case(self):
        s = compute_sizing(1_000_000_000, 45_000, 42_000, 1.0)
        assert s["shares"] == 3300
        assert s["risk_per_share_vnd"] == 3000
        assert s["actual_risk_vnd"] == 9_900_000
        assert s["actual_risk_pct"] == 0.99

    def test_stop_above_pivot_raises(self):
        with pytest.raises(ValueError, match="stop"):
            compute_sizing(1_000_000_000, 45_000, 46_000, 1.0)

    def test_zero_pivot_raises(self):
        with pytest.raises(ValueError):
            compute_sizing(1_000_000_000, 0, 42_000, 1.0)

    def test_negative_risk_raises(self):
        with pytest.raises(ValueError):
            compute_sizing(1_000_000_000, 45_000, 42_000, -1.0)

    def test_lot_rounding(self):
        # Tight stop = high shares; lot rounding should bring down
        s = compute_sizing(10_000_000_000, 45_000, 44_000, 1.0)
        # risk per share = 1000; budget = 100M → 100,000 shares; rounded to lot
        assert s["shares"] % 100 == 0


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


class TestTargets:
    def test_default_1_2_3_R(self):
        targets = compute_targets(45_000, 42_000, [1, 2, 3], "hose")
        # risk = 3000
        # T1 = 48,000; T2 = 51,000; T3 = 54,000 — all on 50 VND tick
        assert targets[0]["price"] == 48_000
        assert targets[1]["price"] == 51_000
        assert targets[2]["price"] == 54_000
        # Fractions sum to 1
        total_frac = sum(t["size_fraction"] for t in targets)
        assert abs(total_frac - 1.0) < 0.01

    def test_custom_targets(self):
        targets = compute_targets(45_000, 42_000, [2, 4], "hose")
        # T1 (2R) = 51,000; T2 (4R) = 57,000
        assert targets[0]["price"] == 51_000
        assert targets[1]["price"] == 57_000

    def test_tick_rounding_in_targets(self):
        # At 100k+ price, tick is 100
        targets = compute_targets(100_000, 95_000, [1.5], "hose")
        # T = 100k + 1.5*5k = 107,500 → tick 100 → 107,500 (on tick)
        assert targets[0]["price"] == 107_500


# ---------------------------------------------------------------------------
# Fees & taxes
# ---------------------------------------------------------------------------


class TestFees:
    def test_round_trip_pct_is_04(self):
        fees = estimate_fees(3300, 45_000, 0.15, 0.10)
        # 0.15 + 0.15 + 0.10 = 0.40%
        assert fees["round_trip_cost_pct"] == 0.4

    def test_zero_shares_pct_zero(self):
        fees = estimate_fees(0, 45_000, 0.15, 0.10)
        assert fees["round_trip_cost_pct"] == 0


# ---------------------------------------------------------------------------
# T+ calendar
# ---------------------------------------------------------------------------


class TestTPlusCalendar:
    def test_default_labels(self):
        cal = t_plus_calendar()
        assert "D0" in cal["buy_date_label"]
        assert "T+2" in cal["stock_in_account_label"] or "D+2" in cal["stock_in_account_label"]

    def test_with_date_computes_business_days(self):
        # Mon 2026-05-04 → T+2 should be Wed 2026-05-06
        cal = t_plus_calendar("2026-05-04")
        assert "2026-05-06" in cal["first_sellable_label"]

    def test_with_date_skips_weekend(self):
        # Thu 2026-05-07 → T+2 should be Mon 2026-05-11 (skip Sat/Sun)
        cal = t_plus_calendar("2026-05-07")
        assert "2026-05-11" in cal["first_sellable_label"]


class TestBusinessDays:
    def test_skip_weekend(self):
        # Fri + 2 → Tue
        start = datetime(2026, 5, 8)  # Friday
        end = add_business_days(start, 2)
        assert end.weekday() < 5
        assert (end - start).days == 4  # Fri+4 = Tue

    def test_mid_week(self):
        # Mon + 2 → Wed
        start = datetime(2026, 5, 4)  # Monday
        end = add_business_days(start, 2)
        assert end == datetime(2026, 5, 6)


# ---------------------------------------------------------------------------
# Context loading
# ---------------------------------------------------------------------------


class TestSectorContext:
    def test_finds_symbol_in_sector(self, tmp_path):
        sector_data = {
            "sectors": [
                {
                    "name": "Real Estate",
                    "relative_strength": {"20D": 2.5},
                    "trend_signal": "improving",
                    "top_3_by_20D": [{"symbol": "VIC"}, {"symbol": "VHM"}],
                    "bottom_3_by_20D": [{"symbol": "NVL"}],
                },
                {
                    "name": "Banking",
                    "relative_strength": {"20D": 1.5},
                    "trend_signal": "stable",
                    "top_3_by_20D": [{"symbol": "VCB"}],
                    "bottom_3_by_20D": [],
                },
            ]
        }
        path = tmp_path / "sec.json"
        path.write_text(json.dumps(sector_data), encoding="utf-8")
        ctx = load_sector_context(str(path), "VIC")
        assert ctx is not None
        assert ctx["name"] == "Real Estate"
        assert ctx["status"] == "leader"

    def test_returns_none_for_unknown_symbol(self, tmp_path):
        sector_data = {"sectors": [{"name": "X", "relative_strength": {"20D": 0.0}, "top_3_by_20D": [], "bottom_3_by_20D": []}]}
        path = tmp_path / "sec.json"
        path.write_text(json.dumps(sector_data), encoding="utf-8")
        assert load_sector_context(str(path), "UNKNOWN") is None

    def test_returns_none_for_bad_file(self):
        assert load_sector_context("/nonexistent.json", "VIC") is None


class TestRoomContext:
    def test_finds_symbol(self, tmp_path):
        room_data = {
            "rows": [
                {"symbol": "VIC", "status": "high_usage", "room_used_pct": 92.0, "change_pct": 0.5},
                {"symbol": "FPT", "status": "full", "room_used_pct": 99.9, "change_pct": 0.0},
            ]
        }
        path = tmp_path / "room.json"
        path.write_text(json.dumps(room_data), encoding="utf-8")
        ctx = load_foreign_room_context(str(path), "VIC")
        assert ctx["status"] == "high_usage"
        assert ctx["room_used_pct"] == 92.0


# ---------------------------------------------------------------------------
# End-to-end assembly
# ---------------------------------------------------------------------------


def make_args(**kwargs):
    defaults = dict(
        account_size_vnd=1_000_000_000,
        symbol="VIC",
        exchange="hose",
        setup_type="breakout",
        pivot=45_000,
        stop=42_000,
        atr=None,
        atr_multiplier=2.0,
        reference_price=None,
        risk_pct=1.0,
        targets="1,2,3",
        broker_fee_pct=DEFAULT_BROKER_FEE_PCT,
        sale_tax_pct=DEFAULT_SALE_TAX_PCT,
        buy_date=None,
        sector_analysis_file=None,
        foreign_room_file=None,
        output_dir="/tmp/test",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAssemblePlan:
    def test_vic_basic_plan(self):
        plan = assemble_plan(make_args())
        assert plan["symbol"] == "VIC"
        assert plan["trade_plan"]["shares"] == 3300
        assert plan["trade_plan"]["risk_vnd"] == 9_900_000
        assert plan["vn_market_context"]["pivot_below_ceiling"] is True
        assert plan["vn_market_context"]["stop_above_floor"] is True
        assert len(plan["trade_plan"]["targets"]) == 3
        assert plan["fees_and_taxes_estimate"]["round_trip_cost_pct"] == 0.4
        assert plan["warnings"] == []

    def test_stop_below_floor_warns(self):
        # HPG 28k pivot, stop 25,500 below floor 26,050
        plan = assemble_plan(
            make_args(symbol="HPG", pivot=28_000, stop=25_500)
        )
        assert plan["vn_market_context"]["stop_above_floor"] is False
        assert any("sàn" in w for w in plan["warnings"])

    def test_pivot_above_ceiling_warns(self):
        # ref 45k → ceiling 48,150. Pivot at 49,000 → above ceiling
        plan = assemble_plan(
            make_args(pivot=49_000, stop=46_000, reference_price=45_000)
        )
        assert plan["vn_market_context"]["pivot_below_ceiling"] is False
        assert any("trần" in w for w in plan["warnings"])

    def test_atr_based_stop(self):
        plan = assemble_plan(
            make_args(symbol="HPG", pivot=28_000, stop=None, atr=800, atr_multiplier=2.0)
        )
        # ATR×2 = 1600 → stop ≈ 26,400, tick 50 down → 26,400
        assert plan["trade_plan"]["stop"] == 26_400

    def test_atr_stop_below_floor_warns(self):
        # Heavy ATR pushes stop below floor
        plan = assemble_plan(
            make_args(
                symbol="HPG",
                pivot=28_000,
                stop=None,
                atr=2000,
                atr_multiplier=2.0,
                reference_price=28_000,
            )
        )
        # Stop = 28k - 4000 = 24,000 < floor 26,050
        assert plan["vn_market_context"]["stop_above_floor"] is False

    def test_missing_stop_and_atr_raises(self):
        with pytest.raises(ValueError, match="stop|atr"):
            assemble_plan(make_args(stop=None, atr=None))

    def test_pivot_too_far_above_reference(self):
        # Pivot 4% above ref on HOSE (band half = 3.5%) → warning
        plan = assemble_plan(
            make_args(
                pivot=46_800,
                stop=43_500,
                reference_price=45_000,
            )
        )
        # Some "muộn" warning
        assert any("muộn" in w for w in plan["warnings"])

    def test_zero_shares_raises(self):
        """Risk per share larger than account → 0 shares → reject."""
        with pytest.raises(ValueError, match="lô"):
            assemble_plan(
                make_args(
                    account_size_vnd=10_000,  # too small
                    pivot=1_000_000,
                    stop=900_000,
                    risk_pct=1.0,
                )
            )

    def test_context_integration(self, tmp_path):
        # Sector file with VIC
        sec = tmp_path / "sec.json"
        sec.write_text(
            json.dumps(
                {
                    "sectors": [
                        {
                            "name": "Real Estate",
                            "relative_strength": {"20D": 2.5},
                            "trend_signal": "improving",
                            "top_3_by_20D": [{"symbol": "VIC"}],
                            "bottom_3_by_20D": [],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        room = tmp_path / "room.json"
        room.write_text(
            json.dumps(
                {
                    "rows": [
                        {
                            "symbol": "VIC",
                            "status": "high_usage",
                            "room_used_pct": 92.0,
                            "change_pct": 0.5,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        plan = assemble_plan(
            make_args(
                sector_analysis_file=str(sec),
                foreign_room_file=str(room),
            )
        )
        assert plan["context"]["sector"]["name"] == "Real Estate"
        assert plan["context"]["sector"]["status"] == "leader"
        assert plan["context"]["foreign_room"]["status"] == "high_usage"
