"""Tests for vn-earnings-analyzer."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import vn_earnings_analyzer as mod


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


def _grade_a_record() -> dict:
    return {
        "symbol": "FPT",
        "report_date": "2026-04-25",
        "gap_pct": 2.5,
        "volume_relative": 1.6,
        "trend_20d_pct": 5.0,
        "above_ma50": True,
        "above_ma200": True,
        "eps_surprise_pct": 10.0,
        "current_price": 142_000,
        "report_day_low": 138_000,
    }


# -----------------------------------------------------------------------------
# analyze_earnings
# -----------------------------------------------------------------------------


def test_analyze_earnings_grade_a():
    res = mod.analyze_earnings(_grade_a_record())
    assert res["score"] == 5
    assert res["grade"] == "A"
    assert all(res["factors"].values())


def test_analyze_earnings_grade_f_when_score_one():
    """Renamed from test_grade_d — score=1 maps to F."""
    rec = _grade_a_record() | {
        "gap_pct": 0.5,
        "volume_relative": 1.0,
        "trend_20d_pct": -2.0,
        "above_ma50": False,
        "above_ma200": False,
        # eps_surprise_pct still 10 → only eps_beat passes → score 1
    }
    res = mod.analyze_earnings(rec)
    assert res["score"] == 1
    assert res["grade"] == "F"
    assert res["factors"]["eps_beat"] is True
    assert res["factors"]["gap_up"] is False


def test_analyze_earnings_grade_b_when_score_four():
    rec = _grade_a_record() | {"eps_surprise_pct": -1.0}  # eps_beat fails
    res = mod.analyze_earnings(rec)
    assert res["score"] == 4
    assert res["grade"] == "B"
    assert res["factors"]["eps_beat"] is False


def test_analyze_earnings_grade_c_when_score_three():
    rec = _grade_a_record() | {
        "eps_surprise_pct": -1.0,
        "above_ma200": False,  # above_ma fails (50 ok, 200 not)
    }
    res = mod.analyze_earnings(rec)
    assert res["score"] == 3
    assert res["grade"] == "C"


def test_analyze_earnings_gap_at_edge_passes():
    """gap_pct = 2.0 exactly → factor passes."""
    rec = _grade_a_record() | {"gap_pct": 2.0}
    res = mod.analyze_earnings(rec)
    assert res["factors"]["gap_up"] is True


def test_analyze_earnings_volume_at_edge_passes():
    rec = _grade_a_record() | {"volume_relative": 1.5}
    res = mod.analyze_earnings(rec)
    assert res["factors"]["high_volume"] is True


def test_analyze_earnings_ma_requires_both():
    """above_ma factor requires BOTH above_ma50 and above_ma200."""
    rec1 = _grade_a_record() | {"above_ma50": True, "above_ma200": False}
    assert mod.analyze_earnings(rec1)["factors"]["above_ma"] is False

    rec2 = _grade_a_record() | {"above_ma50": False, "above_ma200": True}
    assert mod.analyze_earnings(rec2)["factors"]["above_ma"] is False


def test_analyze_earnings_eps_surprise_must_be_positive():
    """eps_surprise_pct = 0 fails (must be > 0)."""
    rec = _grade_a_record() | {"eps_surprise_pct": 0.0}
    res = mod.analyze_earnings(rec)
    assert res["factors"]["eps_beat"] is False


# -----------------------------------------------------------------------------
# filter_status
# -----------------------------------------------------------------------------


def test_filter_status_kiem_soat_skipped():
    keep, reason = mod.filter_status(
        {"symbol": "X", "status": "Kiểm soát"}, include_flagged=False
    )
    assert keep is False
    assert "Kiểm soát" in reason


def test_filter_status_include_flagged_keeps_all():
    keep, _ = mod.filter_status(
        {"symbol": "X", "status": "Tạm ngừng"}, include_flagged=True
    )
    assert keep is True


# -----------------------------------------------------------------------------
# analyze (full pipeline)
# -----------------------------------------------------------------------------


def test_analyze_sorts_by_score_desc():
    earnings = [
        _grade_a_record() | {"symbol": "BAD", "gap_pct": 0, "volume_relative": 0,
                              "trend_20d_pct": -5, "above_ma50": False,
                              "above_ma200": False, "eps_surprise_pct": -10},
        _grade_a_record(),
    ]
    res = mod.analyze(earnings)
    assert res["results"][0]["symbol"] == "FPT"
    assert res["results"][1]["symbol"] == "BAD"


def test_analyze_filters_by_min_grade():
    earnings = [
        _grade_a_record(),
        _grade_a_record() | {"symbol": "WEAK", "gap_pct": 0, "volume_relative": 0,
                              "trend_20d_pct": -5, "above_ma50": False,
                              "above_ma200": False, "eps_surprise_pct": -10},
    ]
    res = mod.analyze(earnings, min_grade="B")
    assert res["scored_count"] == 1
    assert res["results"][0]["grade"] == "A"


def test_analyze_skips_flagged_by_default():
    earnings = [_grade_a_record() | {"status": "Kiểm soát"}, _grade_a_record() | {"symbol": "OK"}]
    res = mod.analyze(earnings)
    assert res["scored_count"] == 1
    assert res["skipped_count"] == 1


# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------


def test_format_vnd_thousands_separator():
    assert mod.format_vnd(148_500_000) == "148,500,000 VND"
    assert mod.format_vnd(None) == "n/a"


def test_write_outputs_creates_files(tmp_path):
    res = mod.analyze([_grade_a_record()])
    j, m = mod.write_outputs(res, str(tmp_path))
    assert j.exists() and m.exists()
    md = m.read_text(encoding="utf-8")
    assert "FPT" in md
    assert "142,000 VND" in md
