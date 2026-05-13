"""Tests for vn-sector-analyst.

Uses programmatically-generated OHLCV data to test sector aggregation,
relative strength, trend signals, and rotation hints.
"""

import json
from pathlib import Path

import pytest

from vn_sector_analyst import (
    DEFAULT_WINDOWS,
    MAPPING_PATH,
    analyze,
    average_returns,
    compute_returns,
    compute_window_return,
    load_ohlcv_batch,
    load_sector_mapping,
    per_symbol_returns,
    relative_strength,
    symbol_to_sector,
    trend_signal,
)


# ---------------------------------------------------------------------------
# Helpers for synthetic OHLCV
# ---------------------------------------------------------------------------


def make_ohlcv(close_series: list[float]) -> list[dict]:
    """Build a minimal OHLCV row list from a series of closes."""
    rows = []
    for i, c in enumerate(close_series):
        rows.append(
            {
                "time": f"2026-{((i // 30) + 1):02d}-{((i % 30) + 1):02d}",
                "open": c,
                "high": c,
                "low": c,
                "close": c,
                "volume": 1000000,
            }
        )
    return rows


def linear_growth(start: float, growth_pct: float, n_days: int) -> list[float]:
    """Generate a series that grows linearly by total growth_pct over n_days."""
    step = (growth_pct / 100) * start / n_days
    return [start + step * i for i in range(n_days + 1)]


# ---------------------------------------------------------------------------
# Sector mapping
# ---------------------------------------------------------------------------


class TestSectorMapping:
    def test_mapping_loads(self):
        mapping = load_sector_mapping()
        assert "sectors" in mapping
        assert "Banking" in mapping["sectors"]
        assert mapping["sectors"]["Banking"]["vn_index_weight_approx_pct"] == 30.0

    def test_symbol_to_sector_inverts(self):
        mapping = load_sector_mapping()
        sym_to_sec = symbol_to_sector(mapping)
        assert sym_to_sec["VCB"] == "Banking"
        assert sym_to_sec["VIC"] == "Real Estate"
        assert sym_to_sec["HPG"] == "Materials"
        assert sym_to_sec["FPT"] == "Technology"

    def test_mapping_path_exists(self):
        assert MAPPING_PATH.exists()


# ---------------------------------------------------------------------------
# Return computation
# ---------------------------------------------------------------------------


class TestReturns:
    def test_window_return_basic(self):
        # 11 rows, all growing 10% over 10 days
        closes = linear_growth(100.0, 10.0, 10)
        rows = make_ohlcv(closes)
        # 10D return: from closes[0]=100 to closes[10]=110 → 10%
        r = compute_window_return(rows, 10)
        assert r == 10.0

    def test_window_return_insufficient_data(self):
        rows = make_ohlcv([100.0, 101.0])
        assert compute_window_return(rows, 5) is None

    def test_window_return_negative(self):
        # Drop 5% over 5 days
        rows = make_ohlcv([100.0, 99.0, 98.0, 97.0, 96.0, 95.0])
        r = compute_window_return(rows, 5)
        assert r == -5.0

    def test_compute_returns_dict_shape(self):
        rows = make_ohlcv(linear_growth(100.0, 30.0, 60))
        r = compute_returns(rows, [5, 20, 60])
        assert "5D" in r and "20D" in r and "60D" in r
        assert r["60D"] == 30.0


# ---------------------------------------------------------------------------
# Per-symbol & sector aggregation
# ---------------------------------------------------------------------------


class TestPerSymbolAndAverage:
    def test_per_symbol_returns(self):
        ohlcv = {
            "A": make_ohlcv(linear_growth(100.0, 10.0, 20)),
            "B": make_ohlcv(linear_growth(100.0, 20.0, 20)),
        }
        per_sym = per_symbol_returns(ohlcv, [5, 20])
        assert per_sym["A"]["20D"] == 10.0
        assert per_sym["B"]["20D"] == 20.0

    def test_average_returns_excludes_none(self):
        rl = [
            {"5D": 1.0, "20D": None},
            {"5D": 3.0, "20D": 5.0},
        ]
        avg = average_returns(rl, [5, 20])
        assert avg["5D"] == 2.0  # (1+3)/2
        assert avg["20D"] == 5.0  # only one valid → that value


# ---------------------------------------------------------------------------
# Relative strength
# ---------------------------------------------------------------------------


class TestRelativeStrength:
    def test_rs_basic(self):
        sec = {"5D": 3.0, "20D": -1.5}
        bench = {"5D": 1.0, "20D": 2.0}
        rs = relative_strength(sec, bench)
        assert rs["5D"] == 2.0
        assert rs["20D"] == -3.5

    def test_rs_none_when_missing(self):
        sec = {"5D": 3.0, "20D": None}
        bench = {"5D": None, "20D": 2.0}
        rs = relative_strength(sec, bench)
        assert rs["5D"] is None
        assert rs["20D"] is None


# ---------------------------------------------------------------------------
# Trend signal
# ---------------------------------------------------------------------------


class TestTrendSignal:
    def test_accelerating(self):
        ret = {"5D": 3.0, "20D": 1.0, "60D": 0.5}
        rs = {"5D": 1.0, "20D": 0.5}
        assert trend_signal(ret, rs) == "accelerating"

    def test_falling(self):
        ret = {"5D": -3.0, "20D": -1.0, "60D": -0.5}
        rs = {"5D": -1.5, "20D": -0.5}
        assert trend_signal(ret, rs) == "falling"

    def test_improving(self):
        ret = {"5D": 0.5, "20D": 1.0, "60D": 0.0}
        rs = {"5D": 1.5, "20D": 0.5}
        # r5 > 0 (0.5 > 0), rs5 > rs20 (1.5 > 0.5) → improving
        assert trend_signal(ret, rs) == "improving"

    def test_unknown_when_missing(self):
        ret = {"5D": None, "20D": 1.0}
        rs = {"5D": None, "20D": 0.5}
        assert trend_signal(ret, rs) == "unknown"


# ---------------------------------------------------------------------------
# End-to-end analyze()
# ---------------------------------------------------------------------------


class TestAnalyze:
    @pytest.fixture
    def mapping(self):
        return load_sector_mapping()

    def test_banking_outperforms(self, mapping):
        """Banking up 5%, Materials flat → Banking should rank #1 with high RS."""
        # Use 21 rows so 5D and 20D windows are available
        ohlcv = {
            "VCB": make_ohlcv(linear_growth(100.0, 5.0, 20)),
            "BID": make_ohlcv(linear_growth(100.0, 5.0, 20)),
            "HPG": make_ohlcv(linear_growth(100.0, 0.0, 20)),
            "HSG": make_ohlcv(linear_growth(100.0, 0.0, 20)),
        }
        # Benchmark also up 2.5% (midway)
        benchmark = make_ohlcv(linear_growth(100.0, 2.5, 20))
        result = analyze(ohlcv, benchmark, mapping, windows=[5, 20])

        # Banking should be first (highest RS_20D)
        assert result["sectors"][0]["name"] == "Banking"
        assert result["sectors"][0]["returns"]["20D"] == 5.0
        # RS = 5.0 - 2.5 = 2.5
        assert result["sectors"][0]["relative_strength"]["20D"] == 2.5

        # Materials should be after Banking
        materials_idx = next(
            i for i, s in enumerate(result["sectors"]) if s["name"] == "Materials"
        )
        assert materials_idx > 0

    def test_rotation_hint_leader(self, mapping):
        # Banking strongly leads
        ohlcv = {
            "VCB": make_ohlcv(linear_growth(100.0, 10.0, 20)),
            "BID": make_ohlcv(linear_growth(100.0, 10.0, 20)),
        }
        benchmark = make_ohlcv(linear_growth(100.0, 5.0, 20))
        result = analyze(ohlcv, benchmark, mapping, windows=[5, 20])

        leader_hints = [h for h in result["rotation_hints"] if h["type"] == "leader"]
        assert any(h["sector"] == "Banking" for h in leader_hints)

    def test_regime_note_when_banking_and_realestate_strong(self, mapping):
        ohlcv = {
            "VCB": make_ohlcv(linear_growth(100.0, 5.0, 20)),
            "VIC": make_ohlcv(linear_growth(100.0, 5.0, 20)),
        }
        benchmark = make_ohlcv(linear_growth(100.0, 2.0, 20))
        result = analyze(ohlcv, benchmark, mapping, windows=[5, 20])
        # Both Banking and Real Estate >0 RS → "tăng có cơ sở" note
        assert result["regime_note"] is not None
        assert "tăng" in result["regime_note"]

    def test_top_bottom_within_sector(self, mapping):
        """VCB up 10%, BID up 5%, CTG up 1% → VCB top, CTG bottom."""
        ohlcv = {
            "VCB": make_ohlcv(linear_growth(100.0, 10.0, 20)),
            "BID": make_ohlcv(linear_growth(100.0, 5.0, 20)),
            "CTG": make_ohlcv(linear_growth(100.0, 1.0, 20)),
        }
        benchmark = make_ohlcv(linear_growth(100.0, 5.0, 20))
        result = analyze(ohlcv, benchmark, mapping, windows=[5, 20])

        banking = next(s for s in result["sectors"] if s["name"] == "Banking")
        assert banking["top_3_by_20D"][0]["symbol"] == "VCB"
        assert banking["bottom_3_by_20D"][0]["symbol"] == "CTG"

    def test_unknown_symbol_goes_to_other(self, mapping):
        ohlcv = {
            "ZZZ": make_ohlcv(linear_growth(100.0, 3.0, 20)),
        }
        benchmark = make_ohlcv(linear_growth(100.0, 2.0, 20))
        result = analyze(ohlcv, benchmark, mapping, windows=[5, 20])
        # Should land in "Other"
        other = next((s for s in result["sectors"] if s["name"] == "Other"), None)
        assert other is not None
        assert other["symbols_count"] == 1


# ---------------------------------------------------------------------------
# OHLCV loading
# ---------------------------------------------------------------------------


class TestLoadOhlcv:
    def test_load_multi_symbol_shape(self, tmp_path):
        path = tmp_path / "ohlcv.json"
        payload = {
            "symbols": ["VIC", "HPG"],
            "data": {
                "VIC": [{"time": "2026-05-12", "open": 45000, "high": 46000, "low": 44500, "close": 45500, "volume": 100000}],
                "HPG": [{"time": "2026-05-12", "open": 28000, "high": 28500, "low": 27800, "close": 28200, "volume": 50000}],
            },
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        out = load_ohlcv_batch(str(path))
        assert set(out.keys()) == {"VIC", "HPG"}
        assert out["VIC"][0]["close"] == 45500

    def test_load_single_symbol_shape(self, tmp_path):
        path = tmp_path / "ohlcv.json"
        payload = {
            "symbol": "VIC",
            "data": [{"time": "2026-05-12", "open": 45000, "high": 46000, "low": 44500, "close": 45500, "volume": 100000}],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        out = load_ohlcv_batch(str(path))
        assert "VIC" in out
        assert out["VIC"][0]["close"] == 45500

    def test_load_invalid_shape_raises(self, tmp_path):
        path = tmp_path / "ohlcv.json"
        path.write_text(json.dumps({"unrelated": "blob"}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_ohlcv_batch(str(path))
