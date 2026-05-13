"""Tests for vn-canslim-screener."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import vn_canslim_screener as mod


# Reusable records --------------------------------------------------------------


def _grade_a_record() -> dict:
    return {
        "symbol": "FPT",
        "sector": "Công nghệ thông tin",
        "price": 135_000,
        "high_52w": 136_000,
        "volume_20d_avg": 2_500_000,
        "eps_growth_yoy_pct": 22.5,
        "rs_rating": 85,
        "foreign_net_buy_10d_vnd": 50_000_000_000,
    }


def _grade_b_record() -> dict:
    """All pillars except I (foreign flow negative) → 4/5 → B."""
    return {
        "symbol": "VIC",
        "price": 50_000,
        "high_52w": 51_000,
        "volume_20d_avg": 500_000,
        "eps_growth_yoy_pct": 25.0,
        "rs_rating": 85,
        "foreign_net_buy_10d_vnd": -5_000_000_000,
    }


# -----------------------------------------------------------------------------
# evaluate_canslim
# -----------------------------------------------------------------------------


def test_evaluate_canslim_grade_a():
    res = mod.evaluate_canslim(_grade_a_record())
    assert res["score"] == 5
    assert res["grade"] == "A"
    assert all(res["pillars"].values())
    assert res["pct_below_52w"] is not None
    assert res["pct_below_52w"] < 5


def test_evaluate_canslim_grade_b():
    res = mod.evaluate_canslim(_grade_b_record())
    assert res["score"] == 4
    assert res["grade"] == "B"
    assert res["pillars"]["I"] is False
    assert res["pillars"]["L"] is True


def test_evaluate_canslim_grade_c_low_eps():
    rec = _grade_a_record() | {"eps_growth_yoy_pct": 5.0, "rs_rating": 45}
    res = mod.evaluate_canslim(rec)
    assert res["score"] == 3  # N, S, I pass; C_A and L fail
    assert res["grade"] == "C"


def test_evaluate_canslim_missing_optional_fields():
    rec = {"symbol": "X", "price": 0, "volume_20d_avg": 0}
    res = mod.evaluate_canslim(rec)
    assert res["score"] == 1  # only I (default 0 ≥ 0) passes
    assert res["pillars"]["C_A"] is False
    assert res["pillars"]["N"] is False
    assert res["pillars"]["S"] is False
    assert res["pillars"]["L"] is False
    assert res["pillars"]["I"] is True


def test_evaluate_canslim_pct_below_52w_calculation():
    rec = _grade_a_record() | {"price": 100_000, "high_52w": 105_000}
    res = mod.evaluate_canslim(rec)
    # (1 - 100/105) * 100 ≈ 4.76
    assert abs(res["pct_below_52w"] - 4.76) < 0.05


def test_evaluate_canslim_n_pillar_at_5_percent_edge():
    """price = 95% of 52w → exactly at threshold, should pass."""
    rec = _grade_a_record() | {"price": 95_000, "high_52w": 100_000}
    res = mod.evaluate_canslim(rec)
    assert res["pillars"]["N"] is True


def test_evaluate_canslim_n_pillar_below_edge_fails():
    """price = 94% of 52w → below threshold, should fail."""
    rec = _grade_a_record() | {"price": 94_000, "high_52w": 100_000}
    res = mod.evaluate_canslim(rec)
    assert res["pillars"]["N"] is False


# -----------------------------------------------------------------------------
# Status filter
# -----------------------------------------------------------------------------


def test_filter_status_kiem_soat_skipped():
    keep, reason = mod.filter_status(
        {"symbol": "X", "status": "Kiểm soát"}, include_flagged=False
    )
    assert keep is False
    assert "Kiểm soát" in reason


def test_filter_status_canh_bao_skipped():
    keep, _ = mod.filter_status(
        {"symbol": "X", "status": "Cảnh báo"}, include_flagged=False
    )
    assert keep is False


def test_filter_status_normal_kept():
    keep, _ = mod.filter_status({"symbol": "X", "status": "Normal"}, include_flagged=False)
    assert keep is True


def test_filter_status_include_flagged_keeps_all():
    keep, _ = mod.filter_status(
        {"symbol": "X", "status": "Kiểm soát"}, include_flagged=True
    )
    assert keep is True


# -----------------------------------------------------------------------------
# Full screen pipeline
# -----------------------------------------------------------------------------


def test_screen_filters_below_min_grade():
    universe = [
        _grade_a_record(),
        _grade_a_record() | {"symbol": "WEAK", "eps_growth_yoy_pct": 5.0, "rs_rating": 30},
    ]
    res = mod.screen(universe, min_grade="A")
    assert res["results_count"] == 1
    assert res["results"][0]["symbol"] == "FPT"


def test_screen_skips_flagged():
    universe = [
        _grade_a_record() | {"status": "Kiểm soát"},
        _grade_b_record(),
    ]
    res = mod.screen(universe)
    assert res["skipped_count"] == 1
    assert res["results_count"] == 1
    assert res["results"][0]["symbol"] == "VIC"


def test_screen_sorts_by_score_desc():
    universe = [
        _grade_b_record(),
        _grade_a_record(),
    ]
    res = mod.screen(universe)
    assert res["results"][0]["grade"] == "A"
    assert res["results"][1]["grade"] == "B"


def test_screen_emits_risk_off_advisory():
    universe = [_grade_a_record()]
    res = mod.screen(universe, market_regime="risk-off")
    assert res["market_advisory"] is not None
    assert "risk-off" in res["market_advisory"]


def test_screen_no_advisory_when_neutral():
    universe = [_grade_a_record()]
    res = mod.screen(universe, market_regime="neutral")
    assert res["market_advisory"] is None


# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------


def test_write_outputs_creates_files(tmp_path):
    universe = [_grade_a_record()]
    result = mod.screen(universe)
    j, m = mod.write_outputs(result, str(tmp_path))
    assert j.exists() and m.exists()
    md = m.read_text(encoding="utf-8")
    assert "FPT" in md
    assert "135,000 VND" in md  # VND formatting


def test_format_vnd_thousands_separator():
    assert mod.format_vnd(148_500_000) == "148,500,000 VND"
    assert mod.format_vnd(None) == "n/a"
