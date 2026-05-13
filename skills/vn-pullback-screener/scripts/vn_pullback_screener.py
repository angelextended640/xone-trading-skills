"""VN Pullback Screener — detect healthy pullbacks to MA20 / MA50.

Consumes batch OHLCV JSON from vn-data-fetcher. Detects:
  - Long-term uptrend (price > MA200, MA50 > MA200, MA200 rising)
  - Pullback 3-12% from 20-day high
  - Price testing MA20 or MA50 support
  - RSI(14) in 35-50 sweet spot
  - Volume dry-up at pullback low

Outputs candidates with grade A/B/C, suggested entry/stop.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

VN_TZ = timezone(timedelta(hours=7))

# Defaults
DEFAULT_MIN_PULLBACK_PCT = 3.0
DEFAULT_MAX_PULLBACK_PCT = 12.0
DEFAULT_RSI_LOW = 35.0
DEFAULT_RSI_HIGH = 50.0
DEFAULT_MAX_DIST_MA20_PCT = 3.0
DEFAULT_MAX_DIST_MA50_PCT = 5.0
DEFAULT_VOLUME_DRYUP_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# OHLCV loading (reused pattern)
# ---------------------------------------------------------------------------


def load_ohlcv_batch(path: str) -> dict[str, list[dict]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if "symbols" in raw and isinstance(raw.get("data"), dict):
        return {sym.upper(): rows for sym, rows in raw["data"].items()}
    if "symbol" in raw and isinstance(raw.get("data"), list):
        return {raw["symbol"].upper(): raw["data"]}
    raise ValueError(f"Unknown OHLCV shape in {path}")


def load_multiple(paths: list[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for p in paths:
        out.update(load_ohlcv_batch(p))
    return out


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


def moving_average(values: list[float], window: int) -> list[Optional[float]]:
    out: list[Optional[float]] = []
    for i in range(len(values)):
        if i < window - 1:
            out.append(None)
        else:
            out.append(sum(values[i - window + 1 : i + 1]) / window)
    return out


def rsi(closes: list[float], period: int = 14) -> list[Optional[float]]:
    """Simple RSI implementation (Wilder smoothing)."""
    if len(closes) < period + 1:
        return [None] * len(closes)
    out: list[Optional[float]] = [None] * len(closes)
    gains: list[float] = [0.0]
    losses: list[float] = [0.0]
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    for i in range(period, len(closes)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            out[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            out[i] = 100 - (100 / (1 + rs))
    return out


def slope_pct_per_month(ma: list[Optional[float]], idx: int, sessions_per_month: int = 22) -> Optional[float]:
    """% change of MA over last N sessions."""
    if idx < sessions_per_month or ma[idx] is None or ma[idx - sessions_per_month] is None:
        return None
    prev = ma[idx - sessions_per_month]
    cur = ma[idx]
    if prev == 0:
        return None
    return (cur - prev) / prev * 100


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------


def score_long_term_uptrend(
    closes: list[float],
    ma50: list[Optional[float]],
    ma200: list[Optional[float]],
    idx: int,
) -> tuple[int, Optional[float]]:
    """Return (points 0-25, ma200_slope_pct_per_month)."""
    if idx >= len(closes) or ma50[idx] is None or ma200[idx] is None:
        return 0, None
    p = closes[idx]
    m50 = ma50[idx]
    m200 = ma200[idx]
    if not (p > m200 and m50 > m200):
        return 0, None
    slope = slope_pct_per_month(ma200, idx)
    if slope is None:
        return 10, None
    if slope > 1.0:
        return 25, round(slope, 2)
    if slope > 0:
        return 18, round(slope, 2)
    return 10, round(slope, 2)


def score_pullback_magnitude(closes: list[float], idx: int) -> tuple[int, float, float]:
    """Return (points 0-20, pullback_pct, high_20d).

    Window = 20 days inclusive of idx (so requires idx >= 19).
    """
    if idx < 19:
        return 0, 0.0, 0.0
    window = closes[idx - 19 : idx + 1]
    high_20d = max(window)
    if high_20d <= 0:
        return 0, 0.0, 0.0
    pullback_pct = (closes[idx] - high_20d) / high_20d * 100
    abs_pct = abs(pullback_pct)
    if pullback_pct >= 0:
        # Not in pullback
        return 0, round(pullback_pct, 2), high_20d
    if 4 <= abs_pct <= 8:
        pts = 20
    elif 3 <= abs_pct < 4 or 8 < abs_pct <= 10:
        pts = 15
    elif 10 < abs_pct <= 12:
        pts = 10
    else:
        pts = 0
    return pts, round(pullback_pct, 2), high_20d


def score_support_test(
    closes: list[float],
    ma20: list[Optional[float]],
    ma50: list[Optional[float]],
    idx: int,
) -> tuple[int, Optional[float], Optional[float]]:
    """Return (points 0-20, dist_to_ma20_pct, dist_to_ma50_pct)."""
    p = closes[idx]
    m20 = ma20[idx]
    m50 = ma50[idx]
    dist_20 = (p - m20) / m20 * 100 if m20 else None
    dist_50 = (p - m50) / m50 * 100 if m50 else None
    # Want price >= MA (or just barely below) and close to MA
    if dist_20 is not None and -1 <= dist_20 <= 3:
        return 20, round(dist_20, 2), round(dist_50, 2) if dist_50 is not None else None
    if dist_50 is not None and -1 <= dist_50 <= 5:
        return 15, round(dist_20, 2) if dist_20 is not None else None, round(dist_50, 2)
    if dist_50 is not None and -1 <= dist_50 <= 8:
        return 8, round(dist_20, 2) if dist_20 is not None else None, round(dist_50, 2)
    return 0, round(dist_20, 2) if dist_20 is not None else None, round(dist_50, 2) if dist_50 is not None else None


def score_rsi_sweet_spot(rsi_value: Optional[float]) -> tuple[int, Optional[float]]:
    if rsi_value is None:
        return 0, None
    v = rsi_value
    if 38 <= v <= 48:
        return 20, round(v, 2)
    if 35 <= v < 38 or 48 < v <= 52:
        return 14, round(v, 2)
    if 30 <= v < 35 or 52 < v <= 55:
        return 8, round(v, 2)
    return 0, round(v, 2)


def score_volume_dryup(
    volumes: list[int],
    vol_ma: list[Optional[float]],
    idx: int,
    pullback_window: int = 10,
) -> tuple[int, Optional[float]]:
    """Score volume dry-up at the pullback low.

    Find the min-volume bar in the last `pullback_window` sessions, compute its
    ratio to MA50 volume at that bar.
    """
    start = max(0, idx - pullback_window + 1)
    window = volumes[start : idx + 1]
    if not window:
        return 0, None
    # Find low-price bar in window
    if vol_ma[idx] is None or vol_ma[idx] <= 0:
        return 0, None
    # Use the lowest-volume bar in the pullback window
    min_vol = min(window)
    ratio = min_vol / vol_ma[idx]
    if ratio <= 0.70:
        return 15, round(ratio, 3)
    if ratio <= 0.85:
        return 10, round(ratio, 3)
    if ratio <= 1.0:
        return 5, round(ratio, 3)
    return 0, round(ratio, 3)


# ---------------------------------------------------------------------------
# Entry / stop calculation
# ---------------------------------------------------------------------------


def compute_entry_stop(
    rows: list[dict],
    ma20: list[Optional[float]],
    ma50: list[Optional[float]],
    idx: int,
    pullback_window: int = 10,
) -> tuple[int, int, float]:
    """Suggest entry just above MA20 (or current price), stop below pullback low / MA50."""
    closes = [float(r["close"]) for r in rows]
    lows = [float(r["low"]) for r in rows]

    m20 = ma20[idx]
    m50 = ma50[idx]

    # Entry: slightly above current price (limit order at MA20 + 0.5%)
    if m20:
        entry = int(round(max(closes[idx], m20 * 1.005)))
    else:
        entry = int(round(closes[idx]))

    # Stop: max of (recent pullback low × 0.97, MA50 × 0.97)
    start = max(0, idx - pullback_window + 1)
    pullback_low = min(lows[start : idx + 1])
    candidates = [pullback_low * 0.97]
    if m50:
        candidates.append(m50 * 0.97)
    stop = int(round(max(candidates)))

    stop_pct = (entry - stop) / entry * 100 if entry > 0 else 0
    return entry, stop, round(stop_pct, 2)


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------


def detect_pullback_for_symbol(symbol: str, rows: list[dict], config: dict) -> dict:
    """Run full pullback analysis on one symbol's OHLCV."""
    if len(rows) < 220:
        return {
            "symbol": symbol,
            "skipped": True,
            "reason": f"Insufficient bars ({len(rows)}); need ≥220",
        }

    closes = [float(r["close"]) for r in rows]
    vols = [int(r["volume"]) for r in rows]
    ma20 = moving_average(closes, 20)
    ma50 = moving_average(closes, 50)
    ma200 = moving_average(closes, 200)
    vol_ma = moving_average([float(v) for v in vols], 50)
    rsi_arr = rsi(closes, 14)

    idx = len(rows) - 1

    # Score
    uptrend_pts, slope_pm = score_long_term_uptrend(closes, ma50, ma200, idx)
    pullback_pts, pullback_pct, high_20d = score_pullback_magnitude(closes, idx)
    support_pts, dist_20, dist_50 = score_support_test(closes, ma20, ma50, idx)
    rsi_pts, rsi_value = score_rsi_sweet_spot(rsi_arr[idx])
    vol_pts, vol_ratio = score_volume_dryup(vols, vol_ma, idx)

    total = uptrend_pts + pullback_pts + support_pts + rsi_pts + vol_pts

    # Grade
    if total >= 80:
        grade = "A"
    elif total >= 60:
        grade = "B"
    elif total >= 40:
        grade = "C"
    else:
        grade = "reject"

    # Rejection reasons (for clarity)
    reasons: list[str] = []
    if uptrend_pts == 0:
        reasons.append("Not in long-term uptrend (price < MA200 or MA50 < MA200)")
    if pullback_pts == 0:
        reasons.append(f"Pullback {pullback_pct:.1f}% outside 3-12% range")
    if support_pts == 0:
        reasons.append("Not testing MA20 or MA50 support")
    if rsi_pts == 0:
        reasons.append(f"RSI {rsi_value} outside 30-55 band")
    if vol_pts == 0:
        reasons.append(f"Volume ratio {vol_ratio} > 1.0 (no dry-up)")

    # Notes (positive context)
    notes: list[str] = []
    if dist_20 is not None and -1 <= dist_20 <= 3:
        notes.append("Testing MA20 support")
    elif dist_50 is not None and -1 <= dist_50 <= 5:
        notes.append("Testing MA50 support")
    if rsi_value and 38 <= rsi_value <= 48:
        notes.append("RSI in healthy oversold zone")

    entry, stop, stop_pct = compute_entry_stop(rows, ma20, ma50, idx)

    result = {
        "symbol": symbol,
        "exchange": "hose",
        "grade": grade,
        "score": total,
        "components": {
            "long_term_uptrend": uptrend_pts,
            "pullback_magnitude": pullback_pts,
            "support_test": support_pts,
            "rsi_sweet_spot": rsi_pts,
            "volume_dryup": vol_pts,
        },
        "current_price": int(round(closes[idx])),
        "high_20d": int(round(high_20d)) if high_20d else 0,
        "pullback_pct": pullback_pct,
        "ma20": int(round(ma20[idx])) if ma20[idx] else None,
        "ma50": int(round(ma50[idx])) if ma50[idx] else None,
        "ma200": int(round(ma200[idx])) if ma200[idx] else None,
        "distance_to_ma20_pct": dist_20,
        "distance_to_ma50_pct": dist_50,
        "rsi_14": rsi_value,
        "volume_ratio_low_vs_ma50": vol_ratio,
        "ma200_slope_pct_per_month": slope_pm,
        "suggested_entry": entry,
        "suggested_stop": stop,
        "stop_pct": stop_pct,
        "notes": notes,
    }

    if grade == "reject":
        result["rejection_reasons"] = reasons

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VN pullback screener — uptrending stocks pulling back to MA20/MA50"
    )
    parser.add_argument("--ohlcv-file", action="append")
    parser.add_argument("--ohlcv-glob")
    parser.add_argument("--fixture")
    parser.add_argument("--min-pullback-pct", type=float, default=DEFAULT_MIN_PULLBACK_PCT)
    parser.add_argument("--max-pullback-pct", type=float, default=DEFAULT_MAX_PULLBACK_PCT)
    parser.add_argument("--rsi-low", type=float, default=DEFAULT_RSI_LOW)
    parser.add_argument("--rsi-high", type=float, default=DEFAULT_RSI_HIGH)
    parser.add_argument("--max-distance-ma20-pct", type=float, default=DEFAULT_MAX_DIST_MA20_PCT)
    parser.add_argument("--max-distance-ma50-pct", type=float, default=DEFAULT_MAX_DIST_MA50_PCT)
    parser.add_argument(
        "--volume-dryup-threshold", type=float, default=DEFAULT_VOLUME_DRYUP_THRESHOLD
    )
    parser.add_argument("--min-grade", choices=["A", "B", "C"], default="C")
    parser.add_argument("--output-dir", default="reports/")
    return parser


def collect_paths(args: argparse.Namespace) -> list[str]:
    paths: list[str] = []
    if args.ohlcv_file:
        paths.extend(args.ohlcv_file)
    if args.ohlcv_glob:
        paths.extend(sorted(glob.glob(args.ohlcv_glob)))
    if args.fixture:
        paths.append(args.fixture)
    return paths


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    paths = collect_paths(args)
    if not paths:
        parser.error("Cần --ohlcv-file, --ohlcv-glob, hoặc --fixture")

    try:
        ohlcv = load_multiple(paths)
    except (FileNotFoundError, ValueError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    config = {
        "min_pullback_pct": args.min_pullback_pct,
        "max_pullback_pct": args.max_pullback_pct,
        "rsi_low": args.rsi_low,
        "rsi_high": args.rsi_high,
        "max_distance_ma20_pct": args.max_distance_ma20_pct,
        "max_distance_ma50_pct": args.max_distance_ma50_pct,
        "volume_dryup_threshold": args.volume_dryup_threshold,
    }

    candidates: list[dict] = []
    rejected: list[dict] = []
    skipped: list[dict] = []

    grade_order = {"A": 3, "B": 2, "C": 1, "reject": 0}
    min_grade_threshold = grade_order[args.min_grade]

    for sym, rows in sorted(ohlcv.items()):
        result = detect_pullback_for_symbol(sym, rows, config)
        if result.get("skipped"):
            skipped.append(result)
        elif result.get("grade") == "reject":
            rejected.append(result)
        elif grade_order.get(result.get("grade", "reject"), 0) >= min_grade_threshold:
            candidates.append(result)
        else:
            rejected.append(result)

    candidates.sort(key=lambda r: -r["score"])

    output = {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "universe_size": len(ohlcv),
        "candidates_count": len(candidates),
        "rejected_count": len(rejected),
        "skipped_count": len(skipped),
        "config": config,
        "candidates": candidates,
        "rejected": rejected,
        "skipped": skipped,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_pullback_screener_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")

    print(f"\nUniverse: {output['universe_size']} symbols")
    print(f"Candidates ({output['candidates_count']}):")
    for c in candidates[:20]:
        print(
            f"  {c['symbol']:6s} grade={c['grade']:1s} score={c['score']:3d}  "
            f"price={c['current_price']:>8,}  pullback={c['pullback_pct']:>6.2f}%  "
            f"RSI={c.get('rsi_14', 0):>5.1f}  entry={c['suggested_entry']:>8,} "
            f"stop={c['suggested_stop']:>8,} ({c['stop_pct']:>4.1f}%)"
        )
    if rejected:
        print(f"\nRejected: {len(rejected)} (top 5 by score)")
        for r in sorted(rejected, key=lambda x: -x.get("score", 0))[:5]:
            reasons = r.get("rejection_reasons", ["low score"])
            print(f"  {r['symbol']:6s} score={r.get('score', 0):3d}  → {reasons[0]}")


if __name__ == "__main__":
    main()
