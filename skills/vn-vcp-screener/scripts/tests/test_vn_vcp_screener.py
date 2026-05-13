"""Tests for vn-vcp-screener.

Uses synthetic OHLCV data — programmatically generated patterns that
either match or fail the VCP detection criteria.
"""

import json

import pytest

from vn_vcp_screener import (
    DEFAULT_MA_LONG,
    closes,
    compute_pivot_and_stop,
    contractions_decreasing,
    detect_vcp_for_symbol,
    find_contractions,
    load_ohlcv_batch,
    moving_average,
    score_contractions,
    score_uptrend,
    score_volume_dryup,
)


# ---------------------------------------------------------------------------
# Synthetic OHLCV builders
# ---------------------------------------------------------------------------


def bar(time: str, o: float, h: float, l: float, c: float, v: int) -> dict:
    return {"time": time, "open": o, "high": h, "low": l, "close": c, "volume": v}


def make_uptrend(start: float, n: int, slope_pct_per_bar: float = 0.3, vol: int = 100_000) -> list[dict]:
    """N bars of steady uptrend."""
    rows = []
    price = start
    for i in range(n):
        next_price = price * (1 + slope_pct_per_bar / 100)
        rows.append(bar(f"D-{i:03d}", price, next_price * 1.005, price * 0.995, next_price, vol))
        price = next_price
    return rows


def make_vcp_base(start: float, n_pre_uptrend: int = 220) -> list[dict]:
    """Generate a synthetic VCP: long uptrend then 3 contractions with decreasing depth."""
    rows = make_uptrend(start, n_pre_uptrend, slope_pct_per_bar=0.5, vol=500_000)
    pivot_high = rows[-1]["close"]

    # Contraction 1: drop 12% then back to pivot, dropping volume each bar
    c1_low = pivot_high * 0.88
    for i in range(10):
        p = pivot_high - (pivot_high - c1_low) * (i + 1) / 10
        rows.append(bar(f"C1-{i}", p, p * 1.005, p * 0.995, p, 400_000 - i * 20_000))
    # Recover to pivot
    for i in range(10):
        p = c1_low + (pivot_high - c1_low) * (i + 1) / 10
        rows.append(bar(f"R1-{i}", p, p * 1.01, p * 0.99, p, 350_000))

    # Contraction 2: drop 7%
    c2_low = pivot_high * 0.93
    for i in range(8):
        p = pivot_high - (pivot_high - c2_low) * (i + 1) / 8
        rows.append(bar(f"C2-{i}", p, p * 1.005, p * 0.995, p, 300_000 - i * 15_000))
    for i in range(8):
        p = c2_low + (pivot_high - c2_low) * (i + 1) / 8
        rows.append(bar(f"R2-{i}", p, p * 1.005, p * 0.99, p, 250_000))

    # Contraction 3: drop 3% — final tight contraction
    c3_low = pivot_high * 0.97
    for i in range(6):
        p = pivot_high - (pivot_high - c3_low) * (i + 1) / 6
        rows.append(bar(f"C3-{i}", p, p * 1.003, p * 0.997, p, 180_000 - i * 15_000))
    # Final 3-5 sessions at the tight pivot zone
    for i in range(4):
        p = pivot_high * (0.985 + 0.005 * i)
        rows.append(bar(f"P-{i}", p, p * 1.005, p * 0.998, p, 120_000))

    return rows


def make_wide_loose_base(start: float) -> list[dict]:
    """Generate a wide-and-loose base — large swings, no contraction pattern."""
    rows = make_uptrend(start, 220, slope_pct_per_bar=0.5, vol=500_000)
    pivot_high = rows[-1]["close"]
    # Wide swings: 30% range, no narrowing
    for i in range(30):
        if i % 6 < 3:
            p = pivot_high * 0.70
        else:
            p = pivot_high
        rows.append(bar(f"W-{i}", p, p * 1.02, p * 0.98, p, 500_000))
    return rows


def make_short_data(n: int = 50) -> list[dict]:
    return make_uptrend(100, n)


# ---------------------------------------------------------------------------
# Moving average
# ---------------------------------------------------------------------------


class TestMovingAverage:
    def test_basic_ma(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        ma = moving_average(values, 3)
        assert ma[0] is None
        assert ma[1] is None
        assert ma[2] == 2.0
        assert ma[3] == 3.0
        assert ma[4] == 4.0


# ---------------------------------------------------------------------------
# Contraction detection
# ---------------------------------------------------------------------------


class TestFindContractions:
    def test_decreasing_contractions_detected(self):
        rows = make_vcp_base(start=100, n_pre_uptrend=220)
        base_start = len(rows) - 50
        base_end = len(rows) - 1
        contractions = find_contractions(rows, base_start, base_end)
        assert len(contractions) >= 2, f"Expected ≥2 contractions, got {len(contractions)}"

    def test_decreasing_check(self):
        contractions = [
            {"depth_pct": 12.0},
            {"depth_pct": 7.0},
            {"depth_pct": 3.0},
        ]
        assert contractions_decreasing(contractions) is True

    def test_non_decreasing_check(self):
        contractions = [
            {"depth_pct": 5.0},
            {"depth_pct": 8.0},
        ]
        assert contractions_decreasing(contractions) is False


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------


class TestScoreUptrend:
    def test_strong_uptrend(self):
        rows = make_uptrend(100, 220, slope_pct_per_bar=0.5)
        cs = closes(rows)
        ma50 = moving_average(cs, 50)
        ma200 = moving_average(cs, 200)
        points, signal = score_uptrend(cs, ma50, ma200, 219)
        assert points == 25
        assert signal == "strong"

    def test_no_uptrend(self):
        # Flat then declining
        rows = make_uptrend(100, 220, slope_pct_per_bar=-0.3)
        cs = closes(rows)
        ma50 = moving_average(cs, 50)
        ma200 = moving_average(cs, 200)
        points, signal = score_uptrend(cs, ma50, ma200, 219)
        assert points == 0


class TestScoreContractions:
    def test_three_decreasing(self):
        contractions = [
            {"depth_pct": 12.0},
            {"depth_pct": 7.0},
            {"depth_pct": 3.0},
        ]
        points, notes = score_contractions(contractions, {"min_contractions": 2, "max_contractions": 5})
        assert points == 25

    def test_two_decreasing(self):
        contractions = [
            {"depth_pct": 10.0},
            {"depth_pct": 5.0},
        ]
        points, notes = score_contractions(contractions, {"min_contractions": 2, "max_contractions": 5})
        assert points == 18

    def test_too_few(self):
        contractions = [{"depth_pct": 5.0}]
        points, notes = score_contractions(contractions, {"min_contractions": 2, "max_contractions": 5})
        assert points == 0


class TestScoreVolumeDryup:
    def test_good_dryup(self):
        rows = make_vcp_base(start=100, n_pre_uptrend=220)
        cs = closes(rows)
        vol_ma = moving_average([float(r["volume"]) for r in rows], 50)
        contractions = find_contractions(rows, len(rows) - 50, len(rows) - 1)
        points, ratio = score_volume_dryup(rows, contractions, vol_ma)
        assert ratio < 0.85, f"Expected volume dry-up, got ratio {ratio}"


# ---------------------------------------------------------------------------
# End-to-end detection
# ---------------------------------------------------------------------------


class TestDetectVcpForSymbol:
    @pytest.fixture
    def config(self):
        return {
            "min_base_length": 25,
            "max_base_length": 90,
            "min_contractions": 2,
            "max_contractions": 5,
            "max_base_range_pct": 25.0,
            "max_pivot_distance_pct": 10.0,
            "volume_dryup_threshold": 0.7,
            "ma_short": 50,
            "ma_long": 200,
            "vol_ma": 50,
        }

    def test_synthetic_vcp_gets_grade(self, config):
        rows = make_vcp_base(100, n_pre_uptrend=220)
        result = detect_vcp_for_symbol("TEST", rows, config)
        # Should pass with at least grade C or better
        assert result.get("grade") in ("A", "B", "C"), f"Got: {result}"
        assert result["score"] > 40

    def test_wide_and_loose_rejected(self, config):
        rows = make_wide_loose_base(100)
        result = detect_vcp_for_symbol("WIDE", rows, config)
        assert result["grade"] == "reject"

    def test_insufficient_data_skipped(self, config):
        rows = make_short_data(50)
        result = detect_vcp_for_symbol("SHORT", rows, config)
        assert result.get("skipped") is True

    def test_pivot_and_stop_computed(self, config):
        rows = make_vcp_base(100, n_pre_uptrend=220)
        result = detect_vcp_for_symbol("PVT", rows, config)
        if result.get("grade") in ("A", "B", "C"):
            assert result["pivot_price"] > 0
            assert result["suggested_stop"] > 0
            # Stop = max(pivot*0.93, final_contraction_low). With shallow final
            # contractions, stop can be tighter than 7%.
            assert 1 <= result["stop_pct"] <= 8, f"Stop pct {result['stop_pct']} outside expected band"


# ---------------------------------------------------------------------------
# OHLCV loading
# ---------------------------------------------------------------------------


class TestLoadOhlcv:
    def test_load_batch(self, tmp_path):
        payload = {
            "symbols": ["VIC", "HPG"],
            "data": {
                "VIC": [{"time": "2026-05-01", "open": 45, "high": 46, "low": 44, "close": 45.5, "volume": 1000}],
                "HPG": [{"time": "2026-05-01", "open": 28, "high": 29, "low": 27, "close": 28.5, "volume": 500}],
            },
        }
        p = tmp_path / "ohlcv.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        out = load_ohlcv_batch(str(p))
        assert "VIC" in out and "HPG" in out

    def test_load_single(self, tmp_path):
        payload = {
            "symbol": "FPT",
            "data": [{"time": "2026-05-01", "open": 140, "high": 142, "low": 139, "close": 141, "volume": 200_000}],
        }
        p = tmp_path / "fpt.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        out = load_ohlcv_batch(str(p))
        assert "FPT" in out

    def test_invalid_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({"unrelated": "blob"}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_ohlcv_batch(str(p))


# ---------------------------------------------------------------------------
# compute_pivot_and_stop
# ---------------------------------------------------------------------------


class TestComputePivotAndStop:
    def test_pivot_above_stop(self):
        rows = make_vcp_base(100, n_pre_uptrend=220)
        contractions = find_contractions(rows, len(rows) - 50, len(rows) - 1)
        pivot, stop, pct = compute_pivot_and_stop(rows, contractions, len(rows) - 1)
        assert pivot > stop
        assert pct > 0
