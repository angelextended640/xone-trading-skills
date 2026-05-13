"""Tests for vn-pullback-screener."""

import json

import pytest

from vn_pullback_screener import (
    compute_entry_stop,
    detect_pullback_for_symbol,
    load_ohlcv_batch,
    moving_average,
    rsi,
    score_long_term_uptrend,
    score_pullback_magnitude,
    score_rsi_sweet_spot,
    score_support_test,
    score_volume_dryup,
    slope_pct_per_month,
)


# ---------------------------------------------------------------------------
# Synthetic data builders
# ---------------------------------------------------------------------------


def bar(time: str, o: float, h: float, l: float, c: float, v: int) -> dict:
    return {"time": time, "open": o, "high": h, "low": l, "close": c, "volume": v}


def make_uptrend(start: float, n: int, slope: float = 0.3, vol: int = 300_000) -> list[dict]:
    rows = []
    p = start
    for i in range(n):
        nxt = p * (1 + slope / 100)
        rows.append(bar(f"D{i:03d}", p, nxt * 1.005, p * 0.995, nxt, vol))
        p = nxt
    return rows


def make_pullback_setup(start: float = 100.0) -> list[dict]:
    """220 sessions uptrend, then 7 sessions of -5% pullback to MA20 with declining volume."""
    rows = make_uptrend(start, 220, slope=0.4, vol=500_000)
    peak = rows[-1]["close"]
    # Pullback over 7 sessions, ending ~5% below peak
    target = peak * 0.95
    for i in range(7):
        p = peak - (peak - target) * (i + 1) / 7
        # Volume declining
        v = int(450_000 - i * 30_000)
        rows.append(bar(f"PB{i}", p, p * 1.005, p * 0.995, p, v))
    return rows


def make_no_uptrend(start: float = 100.0) -> list[dict]:
    """Declining trend → not in uptrend."""
    return make_uptrend(start, 220, slope=-0.3, vol=300_000)


def make_overshoot_pullback(start: float = 100.0) -> list[dict]:
    """Long uptrend then >20% pullback."""
    rows = make_uptrend(start, 220, slope=0.4)
    peak = rows[-1]["close"]
    target = peak * 0.78
    for i in range(20):
        p = peak - (peak - target) * (i + 1) / 20
        rows.append(bar(f"PB{i}", p, p * 1.005, p * 0.995, p, 500_000))
    return rows


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


class TestMovingAverage:
    def test_basic(self):
        v = [1.0, 2.0, 3.0, 4.0, 5.0]
        ma = moving_average(v, 3)
        assert ma[2] == 2.0
        assert ma[4] == 4.0


class TestRsi:
    def test_basic_rsi_smoothed(self):
        # Series alternating up/down → RSI ~50
        v = []
        p = 100
        for i in range(50):
            p = p * (1.01 if i % 2 == 0 else 0.99)
            v.append(p)
        r = rsi(v, 14)
        assert r[-1] is not None
        # Alternating series shouldn't give extreme RSI
        assert 30 < r[-1] < 70

    def test_strong_uptrend_rsi_high(self):
        v = [100 * 1.01 ** i for i in range(50)]
        r = rsi(v, 14)
        assert r[-1] is not None
        assert r[-1] > 70  # strong uptrend → high RSI


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------


class TestScoreLongTermUptrend:
    def test_strong_uptrend(self):
        # Need 200 + 22 = 222+ bars so MA200 has 22 sessions of history for slope
        rows = make_uptrend(100, 240, slope=0.4)
        cs = [r["close"] for r in rows]
        ma50 = moving_average(cs, 50)
        ma200 = moving_average(cs, 200)
        pts, slope = score_long_term_uptrend(cs, ma50, ma200, 239)
        assert pts == 25, f"got {pts}, slope {slope}"

    def test_no_uptrend(self):
        rows = make_uptrend(100, 240, slope=-0.3)
        cs = [r["close"] for r in rows]
        ma50 = moving_average(cs, 50)
        ma200 = moving_average(cs, 200)
        pts, _ = score_long_term_uptrend(cs, ma50, ma200, 239)
        assert pts == 0


class TestScorePullbackMagnitude:
    def test_5pct_pullback_high_score(self):
        # Construct closes where last is 5% below 20-day high
        cs = [100.0] * 19 + [95.0]
        pts, pct, _ = score_pullback_magnitude(cs, 19)
        assert pts == 20
        assert pct == -5.0

    def test_15pct_pullback_zero(self):
        cs = [100.0] * 19 + [85.0]
        pts, pct, _ = score_pullback_magnitude(cs, 19)
        assert pts == 0

    def test_no_pullback_zero(self):
        cs = [100.0 * (1.005 ** i) for i in range(20)]
        pts, pct, _ = score_pullback_magnitude(cs, 19)
        assert pts == 0
        assert pct >= 0


class TestScoreRsiSweetSpot:
    def test_42_is_sweet(self):
        pts, _ = score_rsi_sweet_spot(42.0)
        assert pts == 20

    def test_60_is_too_high(self):
        pts, _ = score_rsi_sweet_spot(60.0)
        assert pts == 0

    def test_20_is_too_low(self):
        pts, _ = score_rsi_sweet_spot(20.0)
        assert pts == 0


class TestScoreSupportTest:
    def test_near_ma20(self):
        cs = [100.0]
        ma20 = [99.5]
        ma50 = [98.0]
        pts, dist_20, dist_50 = score_support_test(cs, ma20, ma50, 0)
        # Distance to MA20 = 0.50%, in [-1, 3] → 20 points
        assert pts == 20

    def test_near_ma50_not_ma20(self):
        cs = [100.0]
        ma20 = [105.0]  # 4.76% above; not testing MA20
        ma50 = [97.0]   # 3.09% below; within MA50 test range
        pts, _, _ = score_support_test(cs, ma20, ma50, 0)
        assert pts == 15


# ---------------------------------------------------------------------------
# End-to-end detection
# ---------------------------------------------------------------------------


class TestDetectPullbackForSymbol:
    @pytest.fixture
    def config(self):
        return {
            "min_pullback_pct": 3.0,
            "max_pullback_pct": 12.0,
            "rsi_low": 35.0,
            "rsi_high": 50.0,
            "max_distance_ma20_pct": 3.0,
            "max_distance_ma50_pct": 5.0,
            "volume_dryup_threshold": 0.85,
        }

    def test_synthetic_pullback_passes(self, config):
        rows = make_pullback_setup()
        result = detect_pullback_for_symbol("TEST", rows, config)
        assert result.get("grade") in ("A", "B", "C"), f"Got {result}"
        assert result["pullback_pct"] < 0
        assert result["score"] > 40

    def test_downtrend_rejected(self, config):
        rows = make_no_uptrend()
        result = detect_pullback_for_symbol("DOWN", rows, config)
        assert result["grade"] == "reject"
        assert "uptrend" in str(result.get("rejection_reasons", [])).lower()

    def test_too_deep_rejected(self, config):
        rows = make_overshoot_pullback()
        result = detect_pullback_for_symbol("DEEP", rows, config)
        # 22% pullback should not score in pullback_magnitude → likely reject or C
        assert result["components"]["pullback_magnitude"] == 0

    def test_insufficient_data_skipped(self, config):
        rows = make_uptrend(100, 50)
        result = detect_pullback_for_symbol("SHORT", rows, config)
        assert result.get("skipped") is True


# ---------------------------------------------------------------------------
# OHLCV loading
# ---------------------------------------------------------------------------


class TestLoadOhlcv:
    def test_batch(self, tmp_path):
        p = tmp_path / "o.json"
        p.write_text(
            json.dumps(
                {
                    "symbols": ["A"],
                    "data": {"A": [{"time": "2026-01-01", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 100}]},
                }
            ),
            encoding="utf-8",
        )
        out = load_ohlcv_batch(str(p))
        assert "A" in out
