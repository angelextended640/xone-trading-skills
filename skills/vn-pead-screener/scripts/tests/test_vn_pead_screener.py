"""Tests for vn-pead-screener."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import vn_pead_screener as mod


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


def _valid_candidate(exchange: str = "hose") -> dict:
    return {
        "symbol": "FPT",
        "grade": "B",
        "report_date": "2026-04-25",
        "current_price": 142_000,
        "report_day_low": 138_000,
        "reference_price": 142_000,
        "exchange": exchange,
        "has_red_candle_pullback": True,
    }


# -----------------------------------------------------------------------------
# Ceiling/floor band calculations
# -----------------------------------------------------------------------------


def test_compute_price_band_hose_7pct():
    band = mod.compute_price_band(142_000, "hose")
    assert band["price_band_pct"] == 7.0
    # 142000 * 1.07 = 151940 → round down to tick 100 = 151900
    assert band["ceiling_price_vnd"] == 151_900
    # 142000 * 0.93 = 132060 → round up to 100 = 132100
    assert band["floor_price_vnd"] == 132_100


def test_compute_price_band_hnx_10pct():
    band = mod.compute_price_band(20_000, "hnx")
    assert band["price_band_pct"] == 10.0
    # 20000 * 1.1 = 22000 → tick 100, already aligned
    assert band["ceiling_price_vnd"] == 22_000
    # 20000 * 0.9 = 18000
    assert band["floor_price_vnd"] == 18_000


def test_compute_price_band_upcom_15pct():
    band = mod.compute_price_band(10_000, "upcom")
    assert band["price_band_pct"] == 15.0
    assert band["ceiling_price_vnd"] == 11_500
    assert band["floor_price_vnd"] == 8_500


def test_round_to_tick_hose_below_10k():
    # tick = 10 below 10k
    assert mod.round_to_tick(9_437, "hose", "nearest") == 9_440
    assert mod.round_to_tick(9_437, "hose", "down") == 9_430
    assert mod.round_to_tick(9_437, "hose", "up") == 9_440


def test_round_to_tick_hose_above_50k():
    # tick = 100 at/above 50k
    assert mod.round_to_tick(67_350, "hose", "nearest") == 67_400
    assert mod.round_to_tick(67_350, "hose", "down") == 67_300


# -----------------------------------------------------------------------------
# unwrap_candidates
# -----------------------------------------------------------------------------


def test_unwrap_candidates_accepts_list():
    assert mod.unwrap_candidates([{"a": 1}]) == [{"a": 1}]


def test_unwrap_candidates_accepts_analyzer_dict():
    """Mode B: vn-earnings-analyzer output is {results: [...]}."""
    payload = {"results": [{"a": 1}], "as_of": "x"}
    assert mod.unwrap_candidates(payload) == [{"a": 1}]


def test_unwrap_candidates_rejects_other():
    import pytest
    with pytest.raises(ValueError):
        mod.unwrap_candidates({"foo": "bar"})


# -----------------------------------------------------------------------------
# screen_one
# -----------------------------------------------------------------------------


def test_screen_one_valid_returns_entry_plan():
    res = mod.screen_one(_valid_candidate(), r_multiples=[2.0], min_grade="B")
    assert res is not None
    assert res["symbol"] == "FPT"
    assert res["entry_price_vnd"] == 142_000
    assert res["stop_loss_vnd"] == 138_000
    assert res["risk_per_share_vnd"] == 4_000
    # 2R: 142000 + 2*4000 = 150000
    assert res["target_price_vnd"] == 150_000
    assert res["stop_above_floor"] is True  # 138k > 132.1k
    assert res["warnings"] == []


def test_screen_one_rejects_below_min_grade():
    rec = _valid_candidate() | {"grade": "C"}
    assert mod.screen_one(rec, r_multiples=[2.0], min_grade="B") is None


def test_screen_one_rejects_no_pullback():
    rec = _valid_candidate() | {"has_red_candle_pullback": False}
    assert mod.screen_one(rec, r_multiples=[2.0], min_grade="B") is None


def test_screen_one_rejects_below_report_day_low():
    """If current_price ≤ report_day_low, setup invalidated."""
    rec = _valid_candidate() | {"current_price": 137_000}  # below 138k stop
    assert mod.screen_one(rec, r_multiples=[2.0], min_grade="B") is None


def test_screen_one_warns_when_stop_below_floor():
    """Stop too far below entry → fails floor check, but result still returned with warning."""
    # Need entry to be high, stop to be very low — but band floor is set by reference_price
    # If reference=10k HOSE, floor = 9300; pick stop below 9300
    rec = {
        "symbol": "X",
        "grade": "A",
        "report_date": "2026-05-01",
        "current_price": 10_000,
        "report_day_low": 9_000,  # below HOSE floor (9300)
        "reference_price": 10_000,
        "exchange": "hose",
        "has_red_candle_pullback": True,
    }
    res = mod.screen_one(rec, r_multiples=[2.0], min_grade="B")
    assert res is not None
    assert res["stop_above_floor"] is False
    assert len(res["warnings"]) == 1
    assert "floor" in res["warnings"][0].lower()


def test_screen_one_supports_multiple_r_targets():
    res = mod.screen_one(_valid_candidate(), r_multiples=[1.0, 2.0, 3.0], min_grade="B")
    assert res is not None
    assert len(res["targets"]) == 3
    # 1R → 146k, 2R → 150k, 3R → 154k
    assert res["targets"][0]["target_price_vnd"] == 146_000
    assert res["targets"][1]["target_price_vnd"] == 150_000
    assert res["targets"][2]["target_price_vnd"] == 154_000


def test_screen_one_pipeline_mode_with_raw_data():
    """Mode B: analyzer output has fields inside raw_data nested dict."""
    candidate = {
        "symbol": "FPT",
        "grade": "B",
        "report_date": "2026-04-25",
        "current_price_vnd": 142_000,  # analyzer's _vnd suffix variant
        "report_day_low_vnd": 138_000,
        "raw_data": {
            "current_price": 142_000,
            "report_day_low": 138_000,
            "has_red_candle_pullback": True,
        },
    }
    res = mod.screen_one(candidate, r_multiples=[2.0], min_grade="B")
    assert res is not None
    assert res["entry_price_vnd"] == 142_000


# -----------------------------------------------------------------------------
# screen (full pipeline)
# -----------------------------------------------------------------------------


def test_screen_filters_and_sorts():
    candidates = [
        _valid_candidate() | {"symbol": "ZZZ", "grade": "B"},
        _valid_candidate() | {"symbol": "AAA", "grade": "A"},
        _valid_candidate() | {"symbol": "WEAK", "grade": "C"},
    ]
    res = mod.screen(candidates, r_multiples=[2.0], min_grade="B")
    assert res["valid_count"] == 2
    # A grade first
    assert res["results"][0]["grade"] == "A"
    assert res["results"][0]["symbol"] == "AAA"


def test_screen_counts_rejections():
    candidates = [
        _valid_candidate(),
        _valid_candidate() | {"symbol": "PB", "has_red_candle_pullback": False},
    ]
    res = mod.screen(candidates, r_multiples=[2.0], min_grade="B")
    assert res["valid_count"] == 1
    assert res["rejected_count"] == 1


# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------


def test_format_vnd_thousands_separator():
    assert mod.format_vnd(148_500_000) == "148,500,000 VND"
    assert mod.format_vnd(None) == "n/a"


def test_write_outputs_creates_files(tmp_path):
    res = mod.screen([_valid_candidate()], r_multiples=[2.0])
    j, m = mod.write_outputs(res, str(tmp_path))
    assert j.exists() and m.exists()
    md = m.read_text(encoding="utf-8")
    assert "FPT" in md
    assert "142,000 VND" in md  # entry
    assert "150,000 VND" in md  # 2R target
