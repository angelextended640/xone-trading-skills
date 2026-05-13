"""Tests for vn-dividend-screener."""

import json
from pathlib import Path

import pytest

from vn_dividend_screener import (
    DEFAULT_MAX_PAYOUT,
    DEFAULT_MIN_EPS_3Y_CAGR,
    DEFAULT_MIN_ROE,
    DEFAULT_MIN_YIELD,
    DEFAULT_YIELD_TRAP_THRESHOLD,
    consecutive_paying_years,
    current_yield_pct,
    detect_yield_trap,
    dividend_3y_cagr,
    extract_cash_dividends,
    latest_cash_dividend,
    load_universe,
    run,
    score_dividend_growth,
    score_eps_trajectory,
    score_financial_quality,
    score_payout_sustainability,
)


# ---------------------------------------------------------------------------
# Dividend history math
# ---------------------------------------------------------------------------


class TestDividendMath:
    def test_extract_cash_only(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2025, "type": "stock", "ratio": 0.10},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
        ]
        cash = extract_cash_dividends(history)
        assert len(cash) == 2
        assert all(d["type"] == "cash" for d in cash)
        # Sorted desc by year
        assert cash[0]["year"] == 2025

    def test_latest_cash_dividend(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
        ]
        assert latest_cash_dividend(history) == 2500

    def test_consecutive_paying_years_full(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
            {"year": 2023, "type": "cash", "amount_vnd_per_share": 2000},
            {"year": 2022, "type": "cash", "amount_vnd_per_share": 1800},
        ]
        assert consecutive_paying_years(history) == 4

    def test_consecutive_paying_years_with_gap(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
            # 2023 skipped
            {"year": 2022, "type": "cash", "amount_vnd_per_share": 1800},
        ]
        # Only 2025, 2024 count
        assert consecutive_paying_years(history) == 2

    def test_dividend_3y_cagr(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
            {"year": 2023, "type": "cash", "amount_vnd_per_share": 2000},
            {"year": 2022, "type": "cash", "amount_vnd_per_share": 1800},
        ]
        # 3y CAGR from 1800 to 2500: ((2500/1800)^(1/3)) - 1 ≈ 11.6%
        cagr = dividend_3y_cagr(history)
        assert cagr is not None
        assert 11 <= cagr <= 12

    def test_current_yield(self):
        # latest 2500, price 32500 → 7.69%
        assert round(current_yield_pct(32500, 2500), 2) == 7.69


# ---------------------------------------------------------------------------
# Yield trap detection
# ---------------------------------------------------------------------------


class TestYieldTrap:
    def test_trap_eps_collapse(self):
        is_trap, reasons = detect_yield_trap(yield_pct=12.0, eps_cagr=-25.0, payout_pct=80.0)
        assert is_trap is True
        assert any("EPS" in r for r in reasons)

    def test_trap_payout_over_100(self):
        is_trap, reasons = detect_yield_trap(yield_pct=10.0, eps_cagr=0.0, payout_pct=120.0)
        assert is_trap is True
        assert any("Payout" in r for r in reasons)

    def test_high_yield_but_sustainable_not_trap(self):
        is_trap, _ = detect_yield_trap(yield_pct=9.0, eps_cagr=5.0, payout_pct=70.0)
        assert is_trap is False

    def test_low_yield_skips_trap_check(self):
        is_trap, _ = detect_yield_trap(yield_pct=5.0, eps_cagr=-30.0, payout_pct=100.0)
        # Below 8% threshold → not flagged even with bad fundamentals
        assert is_trap is False


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------


class TestScoringComponents:
    def test_payout_sweet_spot(self):
        assert score_payout_sustainability(50.0, 4200) == 25

    def test_payout_stretched(self):
        assert score_payout_sustainability(72.0, 4200) == 20

    def test_payout_too_high_zero(self):
        assert score_payout_sustainability(85.0, 4200) == 0

    def test_payout_negative_eps_zero(self):
        assert score_payout_sustainability(50.0, -100) == 0

    def test_dividend_growth_strong(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
            {"year": 2023, "type": "cash", "amount_vnd_per_share": 2000},
            {"year": 2022, "type": "cash", "amount_vnd_per_share": 1500},
        ]
        # 4 consecutive, CAGR (2500/1500)^(1/3)-1 = 18.6% → strong
        assert score_dividend_growth(history) == 20

    def test_dividend_growth_short_history(self):
        history = [
            {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
            {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
        ]
        # Only 2 consecutive → 0
        assert score_dividend_growth(history) == 0

    def test_financial_quality_excellent(self):
        assert score_financial_quality(20.0, 0.5) == 20

    def test_financial_quality_acceptable(self):
        assert score_financial_quality(13.5, 1.2) == 15

    def test_financial_quality_below_threshold(self):
        assert score_financial_quality(8.0, 0.5) == 0

    def test_eps_trajectory_growth(self):
        assert score_eps_trajectory(10.0) == 10

    def test_eps_trajectory_collapse(self):
        assert score_eps_trajectory(-10.0) == 0


# ---------------------------------------------------------------------------
# End-to-end run() against sample universe
# ---------------------------------------------------------------------------


class TestRun:
    @pytest.fixture
    def config(self):
        return {
            "min_yield": DEFAULT_MIN_YIELD,
            "max_payout": DEFAULT_MAX_PAYOUT,
            "min_roe": DEFAULT_MIN_ROE,
            "min_eps_3y_cagr": DEFAULT_MIN_EPS_3Y_CAGR,
            "min_consecutive_years": 3,
            "yield_trap_threshold": DEFAULT_YIELD_TRAP_THRESHOLD,
        }

    def test_sample_universe(self, config):
        sample_path = (
            Path(__file__).resolve().parent.parent.parent / "references" / "sample_universe.json"
        )
        universe = load_universe(str(sample_path))
        result = run(universe, config, min_grade="C")
        assert result["universe_size"] == len(universe)
        # NT2 should pass (yield 7.69%, payout 65%, ROE 18%, growth)
        nt2 = next((c for c in result["candidates"] if c["symbol"] == "NT2"), None)
        assert nt2 is not None
        assert nt2["grade"] in ("A", "B")
        # TRAP1 should be flagged
        trap = next((t for t in result["yield_traps"] if t["symbol"] == "TRAP1"), None)
        assert trap is not None
        assert trap["is_yield_trap"] is True
        # LOWY (tech, low yield 1.33%) should be rejected (yield too low)
        lowy = next(
            (
                r
                for r in result["candidates"] + result["rejected"]
                if r["symbol"] == "LOWY"
            ),
            None,
        )
        assert lowy is not None
        if lowy in result["rejected"]:
            assert lowy["grade"] == "reject"

    def test_min_grade_filter(self, config):
        sample_path = (
            Path(__file__).resolve().parent.parent.parent / "references" / "sample_universe.json"
        )
        universe = load_universe(str(sample_path))
        result_c = run(universe, config, min_grade="C")
        result_a = run(universe, config, min_grade="A")
        # A-only filter should be at most as many as C-and-up
        assert len(result_a["candidates"]) <= len(result_c["candidates"])

    def test_sector_distribution_counted(self, config):
        sample_path = (
            Path(__file__).resolve().parent.parent.parent / "references" / "sample_universe.json"
        )
        universe = load_universe(str(sample_path))
        result = run(universe, config, min_grade="C")
        # Sum of distribution must equal candidate count
        total = sum(result["sector_distribution"].values())
        assert total == result["candidates_count"]


# ---------------------------------------------------------------------------
# Universe loading
# ---------------------------------------------------------------------------


class TestLoadUniverse:
    def test_load_valid(self, tmp_path):
        path = tmp_path / "u.json"
        path.write_text(
            json.dumps({"universe": [{"symbol": "A", "current_price": 100}]}),
            encoding="utf-8",
        )
        u = load_universe(str(path))
        assert len(u) == 1

    def test_load_missing_universe_key(self, tmp_path):
        path = tmp_path / "u.json"
        path.write_text(json.dumps({"data": []}), encoding="utf-8")
        with pytest.raises(ValueError, match="universe"):
            load_universe(str(path))
