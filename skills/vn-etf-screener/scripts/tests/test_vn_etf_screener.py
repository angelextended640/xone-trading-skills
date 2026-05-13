"""Tests for vn-etf-screener."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import vn_etf_screener as mod


# -----------------------------------------------------------------------------
# Scoring
# -----------------------------------------------------------------------------


def test_score_etf_grade_a():
    etf = {
        "symbol": "E1VFVN30",
        "name": "DCVFMVN30 ETF",
        "nav_per_share": 21500,
        "market_price": 21600,  # +0.47% premium
        "tracking_error_pct": 0.8,
        "expense_ratio_pct": 0.65,
        "volume_20d_avg": 1_500_000,
    }
    res = mod.score_etf(etf)
    assert res["score"] == 4
    assert res["grade"] == "A"
    assert all(res["factors"].values())
    assert res["premium_discount_pct"] is not None
    assert res["premium_discount_pct"] < 1.0


def test_score_etf_grade_b_high_te():
    """Tracking error just over the 1.0% threshold drops one point."""
    etf = {
        "symbol": "FUEVFVND",
        "name": "VN Diamond",
        "nav_per_share": 31_000,
        "market_price": 31_100,
        "tracking_error_pct": 1.2,  # fails
        "expense_ratio_pct": 0.70,
        "volume_20d_avg": 1_000_000,
    }
    res = mod.score_etf(etf)
    assert res["score"] == 3
    assert res["grade"] == "B"
    assert res["factors"]["low_tracking_error"] is False


def test_score_etf_grade_f_fails_all():
    """test_grade_f (formerly mis-named test_grade_c) — 0/4 factors."""
    etf = {
        "symbol": "BADETF",
        "name": "Bad ETF",
        "nav_per_share": 10_000,
        "market_price": 10_300,  # +3% premium → fails
        "tracking_error_pct": 2.0,  # fails
        "expense_ratio_pct": 1.0,  # fails
        "volume_20d_avg": 5_000,  # fails
    }
    res = mod.score_etf(etf)
    assert res["score"] == 0
    assert res["grade"] == "F"
    assert not any(res["factors"].values())


def test_score_etf_missing_nav_skips_premium_check():
    """If NAV is missing/0, premium/discount factor cannot trigger."""
    etf = {
        "symbol": "NONAV",
        "name": "No NAV",
        "nav_per_share": 0,
        "market_price": 20_000,
        "tracking_error_pct": 0.5,
        "expense_ratio_pct": 0.5,
        "volume_20d_avg": 500_000,
    }
    res = mod.score_etf(etf)
    # 3 factors pass; premium check cannot
    assert res["score"] == 3
    assert res["factors"]["low_premium_discount"] is False
    assert res["premium_discount_pct"] is None


# -----------------------------------------------------------------------------
# Status flag filter
# -----------------------------------------------------------------------------


def test_filter_status_normal_kept():
    keep, reason = mod.filter_status({"symbol": "X"}, include_flagged=False)
    assert keep is True
    assert reason is None


def test_filter_status_kiem_soat_skipped():
    keep, reason = mod.filter_status(
        {"symbol": "X", "status": "Kiểm soát"}, include_flagged=False
    )
    assert keep is False
    assert "Kiểm soát" in reason


def test_filter_status_han_che_skipped():
    keep, _ = mod.filter_status(
        {"symbol": "X", "status": "Hạn chế"}, include_flagged=False
    )
    assert keep is False


def test_filter_status_include_flagged_keeps_all():
    keep, _ = mod.filter_status(
        {"symbol": "X", "status": "Kiểm soát"}, include_flagged=True
    )
    assert keep is True


# -----------------------------------------------------------------------------
# Screen (full pipeline)
# -----------------------------------------------------------------------------


def test_screen_sorts_by_score_desc():
    universe = [
        {  # F — score 0
            "symbol": "BAD",
            "name": "Bad",
            "nav_per_share": 10_000,
            "market_price": 11_000,
            "tracking_error_pct": 3.0,
            "expense_ratio_pct": 1.5,
            "volume_20d_avg": 10,
        },
        {  # A — score 4
            "symbol": "GOOD",
            "name": "Good",
            "nav_per_share": 20_000,
            "market_price": 20_050,
            "tracking_error_pct": 0.5,
            "expense_ratio_pct": 0.5,
            "volume_20d_avg": 1_000_000,
        },
    ]
    res = mod.screen(universe)
    assert res["scored_count"] == 2
    assert res["results"][0]["symbol"] == "GOOD"
    assert res["results"][1]["symbol"] == "BAD"


def test_screen_skips_flagged_by_default():
    universe = [
        {"symbol": "FLAG", "status": "Tạm ngừng"},
        {
            "symbol": "OK",
            "nav_per_share": 20_000,
            "market_price": 20_050,
            "tracking_error_pct": 0.5,
            "expense_ratio_pct": 0.5,
            "volume_20d_avg": 1_000_000,
        },
    ]
    res = mod.screen(universe)
    assert res["scored_count"] == 1
    assert res["skipped_count"] == 1
    assert res["skipped"][0]["symbol"] == "FLAG"


# -----------------------------------------------------------------------------
# VND formatting + report output
# -----------------------------------------------------------------------------


def test_format_vnd_thousands_separator():
    assert mod.format_vnd(148_500_000) == "148,500,000 VND"
    assert mod.format_vnd(None) == "n/a"


def test_write_outputs_creates_both_files(tmp_path):
    result = {
        "schema_version": "1.0",
        "as_of": "2026-05-13T08:30:00+07:00",
        "universe_size": 1,
        "scored_count": 1,
        "skipped_count": 0,
        "skipped": [],
        "results": [
            {
                "symbol": "X",
                "name": "X ETF",
                "score": 4,
                "grade": "A",
                "factors": {},
                "nav_per_share_vnd": 21500,
                "market_price_vnd": 21600,
                "premium_discount_vnd": 100,
                "premium_discount_pct": 0.46,
                "tracking_error_pct": 0.5,
                "expense_ratio_pct": 0.5,
                "volume_20d_avg": 500_000,
                "foreign_room_pct": 5.0,
                "raw_data": {},
            }
        ],
    }
    j, m = mod.write_outputs(result, str(tmp_path))
    assert j.exists() and m.exists()
    md = m.read_text(encoding="utf-8")
    assert "21,500 VND" in md or "21500" in md  # VND formatted
    assert "**X**" in md  # markdown table row
