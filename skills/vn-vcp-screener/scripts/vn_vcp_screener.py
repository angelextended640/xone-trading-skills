"""VN VCP Screener — detect Volatility Contraction Pattern in VN stocks.

Consumes batch OHLCV JSON from vn-data-fetcher. Detects:
  - Uptrend baseline (price > MA50 > MA200)
  - Multiple contractions with decreasing depth
  - Volume dry-up at contractions
  - Pivot near 52-week high
  - Wide-and-loose rejection

Outputs candidates with grade A/B/C, score 0-100, pivot, suggested stop.
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
DEFAULT_MIN_BASE_LENGTH = 25
DEFAULT_MAX_BASE_LENGTH = 90
DEFAULT_MIN_CONTRACTIONS = 2
DEFAULT_MAX_CONTRACTIONS = 5
DEFAULT_MAX_BASE_RANGE_PCT = 25.0
DEFAULT_MAX_PIVOT_DISTANCE_52W_PCT = 10.0
DEFAULT_VOLUME_DRYUP_THRESHOLD = 0.7
DEFAULT_MA_SHORT = 50
DEFAULT_MA_LONG = 200
DEFAULT_VOL_MA = 50


# ---------------------------------------------------------------------------
# OHLCV loading
# ---------------------------------------------------------------------------


def load_ohlcv_batch(path: str) -> dict[str, list[dict]]:
    """Load batch (multi-symbol) or single-symbol JSON from vn-data-fetcher."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if "symbols" in raw and isinstance(raw.get("data"), dict):
        return {sym.upper(): rows for sym, rows in raw["data"].items()}
    if "symbol" in raw and isinstance(raw.get("data"), list):
        return {raw["symbol"].upper(): raw["data"]}
    raise ValueError(
        f"Unknown OHLCV shape in {path}. Expected vn-data-fetcher output."
    )


def load_multiple(paths: list[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for p in paths:
        out.update(load_ohlcv_batch(p))
    return out


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


def moving_average(values: list[float], window: int) -> list[Optional[float]]:
    """Simple moving average; entries before `window` size are None."""
    out: list[Optional[float]] = []
    for i in range(len(values)):
        if i < window - 1:
            out.append(None)
        else:
            out.append(sum(values[i - window + 1 : i + 1]) / window)
    return out


def closes(rows: list[dict]) -> list[float]:
    return [float(r["close"]) for r in rows]


def highs(rows: list[dict]) -> list[float]:
    return [float(r["high"]) for r in rows]


def lows(rows: list[dict]) -> list[float]:
    return [float(r["low"]) for r in rows]


def volumes(rows: list[dict]) -> list[int]:
    return [int(r["volume"]) for r in rows]


# ---------------------------------------------------------------------------
# Contraction detection
# ---------------------------------------------------------------------------


def find_contractions(
    rows: list[dict],
    base_start: int,
    base_end: int,
    min_pivot_advance: int = 3,
) -> list[dict]:
    """Find contractions within rows[base_start:base_end+1].

    A contraction is a (peak, trough) pair where:
      - peak is a local max preceded by an advance of >= min_pivot_advance bars
      - trough is the lowest low between this peak and the next higher peak
      - depth = (peak - trough) / peak * 100

    Returns list of dicts with peak_idx, trough_idx, depth_pct, duration_days.
    """
    if base_end - base_start < 5:
        return []

    hs = highs(rows)
    ls = lows(rows)

    # Find local maxima in the base window using a simple "higher than 2 left and 2 right neighbours" filter
    peaks: list[int] = []
    for i in range(base_start + 2, base_end - 1):
        if (
            hs[i] > hs[i - 1]
            and hs[i] > hs[i - 2]
            and hs[i] >= hs[i + 1]
            and hs[i] >= hs[i + 2]
        ):
            peaks.append(i)

    if len(peaks) < 2:
        return []

    contractions: list[dict] = []
    for idx in range(len(peaks) - 1):
        peak_i = peaks[idx]
        next_peak_i = peaks[idx + 1]
        # Trough = lowest low between this peak and the next
        trough_i = peak_i + 1
        for j in range(peak_i + 1, next_peak_i):
            if ls[j] < ls[trough_i]:
                trough_i = j
        peak_price = hs[peak_i]
        trough_price = ls[trough_i]
        if peak_price <= 0:
            continue
        depth_pct = (peak_price - trough_price) / peak_price * 100
        duration = next_peak_i - peak_i
        contractions.append(
            {
                "index": idx + 1,
                "peak_idx": peak_i,
                "trough_idx": trough_i,
                "peak_price": round(peak_price),
                "trough_price": round(trough_price),
                "depth_pct": round(depth_pct, 2),
                "duration_days": duration,
            }
        )

    # Also add the final contraction (from last peak to base end)
    last_peak = peaks[-1]
    if base_end > last_peak + 1:
        trough_i = last_peak + 1
        for j in range(last_peak + 1, base_end + 1):
            if ls[j] < ls[trough_i]:
                trough_i = j
        peak_price = hs[last_peak]
        trough_price = ls[trough_i]
        depth_pct = (peak_price - trough_price) / peak_price * 100
        if depth_pct > 0.5:  # filter out trivial micro-contractions
            contractions.append(
                {
                    "index": len(contractions) + 1,
                    "peak_idx": last_peak,
                    "trough_idx": trough_i,
                    "peak_price": round(peak_price),
                    "trough_price": round(trough_price),
                    "depth_pct": round(depth_pct, 2),
                    "duration_days": base_end - last_peak,
                }
            )

    return contractions


def contractions_decreasing(contractions: list[dict]) -> bool:
    """True if contraction depths are strictly decreasing."""
    if len(contractions) < 2:
        return False
    depths = [c["depth_pct"] for c in contractions]
    return all(depths[i] > depths[i + 1] for i in range(len(depths) - 1))


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_uptrend(
    closes_arr: list[float],
    ma50: list[Optional[float]],
    ma200: list[Optional[float]],
    base_start: int,
) -> tuple[int, str]:
    """Return (points 0-25, signal label)."""
    i = base_start
    if i >= len(closes_arr) or ma50[i] is None or ma200[i] is None:
        return 0, "insufficient_data"
    price = closes_arr[i]
    m50 = ma50[i]
    m200 = ma200[i]
    if price > m50 > m200:
        # Check MA50 slope: positive over last 20 sessions
        if i >= 20 and ma50[i - 20] is not None:
            slope_up = m50 > ma50[i - 20]
            if slope_up:
                return 25, "strong"
            return 18, "flat"
        return 18, "flat"
    if price > m50 and m50 < m200:
        return 10, "weak"
    return 0, "no_uptrend"


def score_contractions(contractions: list[dict], thresholds: dict) -> tuple[int, list[str]]:
    """Return (points 0-25, notes)."""
    notes: list[str] = []
    n = len(contractions)
    if n < thresholds["min_contractions"]:
        return 0, [f"only {n} contractions (need ≥{thresholds['min_contractions']})"]
    if n > thresholds["max_contractions"]:
        notes.append(f"{n} contractions (above typical max)")
    decreasing = contractions_decreasing(contractions)
    if decreasing and 3 <= n <= 4:
        # Check all depths under thresholds (approx 15/10/6/3)
        max_depths = [15, 10, 6, 4, 3]
        ok = all(c["depth_pct"] <= max_depths[i] for i, c in enumerate(contractions) if i < len(max_depths))
        if ok:
            notes.append(f"{n} contractions, strictly decreasing, depths within thresholds")
            return 25, notes
        notes.append(f"{n} contractions decreasing but a depth exceeds threshold")
        return 18, notes
    if decreasing and n == 2:
        notes.append("2 contractions, decreasing")
        return 18, notes
    notes.append(f"{n} contractions but not strictly decreasing")
    return 10, notes


def score_volume_dryup(
    rows: list[dict],
    contractions: list[dict],
    vol_ma: list[Optional[float]],
) -> tuple[int, float]:
    """Score volume dry-up at the final contraction. Return (points 0-20, ratio)."""
    if not contractions:
        return 0, 0.0
    last = contractions[-1]
    vol_at_trough = float(rows[last["trough_idx"]]["volume"])
    vol_baseline = vol_ma[last["trough_idx"]]
    if vol_baseline is None or vol_baseline <= 0:
        return 0, 0.0
    ratio = vol_at_trough / vol_baseline
    if ratio <= 0.6:
        return 20, round(ratio, 3)
    if ratio <= 0.7:
        return 14, round(ratio, 3)
    if ratio <= 0.85:
        return 8, round(ratio, 3)
    return 0, round(ratio, 3)


def score_pivot_quality(
    rows: list[dict],
    contractions: list[dict],
    base_end: int,
    window_52w: int = 252,
) -> tuple[int, float, int, bool]:
    """Score pivot quality. Return (points, pivot_distance_from_52w_pct, pivot_price, is_tight)."""
    if not contractions:
        return 0, 100.0, 0, False
    pivot_idx = contractions[-1]["peak_idx"]
    # Use highest close in the last 10 sessions of the base as pivot
    pivot_lookback_start = max(base_end - 10, contractions[-1]["peak_idx"])
    cs = closes(rows)
    pivot_price = max(cs[pivot_lookback_start : base_end + 1])

    # 52-week high
    start_52w = max(0, base_end - window_52w)
    hs = highs(rows)
    high_52w = max(hs[start_52w : base_end + 1])
    distance_pct = (high_52w - pivot_price) / high_52w * 100 if high_52w > 0 else 100

    # Tightness: last 3 sessions within 2% range
    last_5 = cs[max(0, base_end - 4) : base_end + 1]
    if len(last_5) >= 3:
        rng = (max(last_5) - min(last_5)) / min(last_5) * 100 if min(last_5) > 0 else 100
        is_tight = rng <= 2.0
    else:
        is_tight = False

    if distance_pct <= 5 and is_tight:
        return 15, round(distance_pct, 2), int(pivot_price), is_tight
    if distance_pct <= 10 and is_tight:
        return 11, round(distance_pct, 2), int(pivot_price), is_tight
    if distance_pct <= 10:
        return 6, round(distance_pct, 2), int(pivot_price), is_tight
    return 0, round(distance_pct, 2), int(pivot_price), is_tight


def score_wide_and_loose(
    rows: list[dict],
    contractions: list[dict],
    base_start: int,
    base_end: int,
) -> tuple[int, float, list[str]]:
    """Score wide-and-loose penalty. Return (points, base_range_pct, notes)."""
    notes: list[str] = []
    if not contractions:
        return 0, 0.0, notes
    hs = highs(rows[base_start : base_end + 1])
    ls = lows(rows[base_start : base_end + 1])
    base_high = max(hs)
    base_low = min(ls)
    base_range_pct = (base_high - base_low) / base_low * 100 if base_low > 0 else 100
    max_contraction = max(c["depth_pct"] for c in contractions)

    if base_range_pct > 35:
        notes.append(f"base range {round(base_range_pct, 1)}% > 35% — REJECT (wide-and-loose)")
        return -1, round(base_range_pct, 2), notes  # special: reject
    if base_range_pct > 25 or max_contraction > 18:
        notes.append(f"base range {round(base_range_pct, 1)}% or max contraction {max_contraction}% triggers grade cap")
        return 0, round(base_range_pct, 2), notes
    if base_range_pct < 15 and max_contraction < 12:
        return 15, round(base_range_pct, 2), notes
    return 9, round(base_range_pct, 2), notes


# ---------------------------------------------------------------------------
# Stop / pivot calculation
# ---------------------------------------------------------------------------


def compute_pivot_and_stop(
    rows: list[dict], contractions: list[dict], base_end: int
) -> tuple[int, int, float]:
    """Return (pivot, suggested_stop, stop_pct_from_pivot)."""
    if not contractions:
        return 0, 0, 0.0
    cs = closes(rows)
    pivot_lookback_start = max(base_end - 10, contractions[-1]["peak_idx"])
    pivot = max(cs[pivot_lookback_start : base_end + 1])
    final_contraction_low = contractions[-1]["trough_price"]
    pct_5 = pivot * 0.95
    pct_7 = pivot * 0.93
    # Stop = max(pct_7, final_contraction_low) — whichever gives tighter stop
    stop_candidate = max(pct_7, final_contraction_low)
    stop_pct = (pivot - stop_candidate) / pivot * 100
    return int(round(pivot)), int(round(stop_candidate)), round(stop_pct, 2)


# ---------------------------------------------------------------------------
# Main VCP detection
# ---------------------------------------------------------------------------


def detect_vcp_for_symbol(
    symbol: str,
    rows: list[dict],
    config: dict,
) -> dict:
    """Run full VCP analysis on one symbol's OHLCV. Return result dict."""
    if len(rows) < max(config["ma_long"] + 10, config["min_base_length"] + 20):
        return {
            "symbol": symbol,
            "skipped": True,
            "reason": f"Insufficient bars ({len(rows)}); need ≥{config['ma_long'] + 10}",
        }

    cs = closes(rows)
    ma50 = moving_average(cs, config["ma_short"])
    ma200 = moving_average(cs, config["ma_long"])
    vols = volumes(rows)
    vol_ma = moving_average([float(v) for v in vols], config["vol_ma"])

    base_end = len(rows) - 1
    base_start = max(0, base_end - config["max_base_length"])

    contractions = find_contractions(rows, base_start, base_end)

    if len(contractions) < config["min_contractions"]:
        return {
            "symbol": symbol,
            "grade": "reject",
            "score": 0,
            "rejection_reasons": [
                f"only {len(contractions)} contractions (need ≥{config['min_contractions']})"
            ],
        }

    # Score components
    uptrend_pts, uptrend_signal = score_uptrend(cs, ma50, ma200, base_start)
    contractions_pts, contractions_notes = score_contractions(
        contractions,
        {
            "min_contractions": config["min_contractions"],
            "max_contractions": config["max_contractions"],
        },
    )
    volume_pts, vol_ratio = score_volume_dryup(rows, contractions, vol_ma)
    pivot_pts, pivot_dist_52w, pivot_price_score, is_tight = score_pivot_quality(
        rows, contractions, base_end
    )
    wide_pts, base_range_pct, wide_notes = score_wide_and_loose(
        rows, contractions, base_start, base_end
    )

    if wide_pts == -1:
        return {
            "symbol": symbol,
            "grade": "reject",
            "score": 0,
            "rejection_reasons": wide_notes,
        }

    total = uptrend_pts + contractions_pts + volume_pts + pivot_pts + wide_pts

    # Grade
    cap_at_C = wide_pts == 0 and base_range_pct > 25
    if total >= 80 and not cap_at_C:
        grade = "A"
    elif total >= 60 and not cap_at_C:
        grade = "B"
    elif total >= 40:
        grade = "C"
    else:
        grade = "reject"

    pivot, stop, stop_pct = compute_pivot_and_stop(rows, contractions, base_end)

    return {
        "symbol": symbol,
        "exchange": "hose",
        "grade": grade,
        "score": total,
        "components": {
            "uptrend": uptrend_pts,
            "contractions": contractions_pts,
            "volume_dryup": volume_pts,
            "pivot_quality": pivot_pts,
            "wide_loose": wide_pts,
        },
        "pivot_price": pivot,
        "suggested_stop": stop,
        "stop_pct": stop_pct,
        "contractions": [
            {
                "index": c["index"],
                "depth_pct": c["depth_pct"],
                "duration_days": c["duration_days"],
            }
            for c in contractions
        ],
        "base_total_range_pct": base_range_pct,
        "pivot_to_52w_high_pct": pivot_dist_52w,
        "volume_at_pivot_vs_ma50": vol_ratio,
        "trend_signal": uptrend_signal,
        "is_tight_pivot": is_tight,
        "notes": contractions_notes + wide_notes,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VCP screener for VN stocks (Minervini-style, ±7% band adjusted)"
    )
    parser.add_argument(
        "--ohlcv-file",
        action="append",
        help="Path to vn-data-fetcher OHLCV JSON (repeatable)",
    )
    parser.add_argument(
        "--ohlcv-glob",
        help="Glob pattern for multiple OHLCV files",
    )
    parser.add_argument(
        "--fixture",
        help="Path to a single fixture JSON for offline tests",
    )
    parser.add_argument("--min-base-length", type=int, default=DEFAULT_MIN_BASE_LENGTH)
    parser.add_argument("--max-base-length", type=int, default=DEFAULT_MAX_BASE_LENGTH)
    parser.add_argument("--min-contractions", type=int, default=DEFAULT_MIN_CONTRACTIONS)
    parser.add_argument("--max-contractions", type=int, default=DEFAULT_MAX_CONTRACTIONS)
    parser.add_argument(
        "--max-base-range-pct",
        type=float,
        default=DEFAULT_MAX_BASE_RANGE_PCT,
    )
    parser.add_argument(
        "--max-pivot-distance-pct",
        type=float,
        default=DEFAULT_MAX_PIVOT_DISTANCE_52W_PCT,
    )
    parser.add_argument(
        "--volume-dryup-threshold",
        type=float,
        default=DEFAULT_VOLUME_DRYUP_THRESHOLD,
    )
    parser.add_argument("--ma-short", type=int, default=DEFAULT_MA_SHORT)
    parser.add_argument("--ma-long", type=int, default=DEFAULT_MA_LONG)
    parser.add_argument("--vol-ma", type=int, default=DEFAULT_VOL_MA)
    parser.add_argument(
        "--min-grade",
        choices=["A", "B", "C"],
        default="C",
        help="Min grade to include in candidates output (default C)",
    )
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
        "min_base_length": args.min_base_length,
        "max_base_length": args.max_base_length,
        "min_contractions": args.min_contractions,
        "max_contractions": args.max_contractions,
        "max_base_range_pct": args.max_base_range_pct,
        "max_pivot_distance_pct": args.max_pivot_distance_pct,
        "volume_dryup_threshold": args.volume_dryup_threshold,
        "ma_short": args.ma_short,
        "ma_long": args.ma_long,
        "vol_ma": args.vol_ma,
    }

    candidates: list[dict] = []
    rejected: list[dict] = []
    skipped: list[dict] = []

    grade_order = {"A": 3, "B": 2, "C": 1, "reject": 0}
    min_grade_threshold = grade_order[args.min_grade]

    for sym, rows in sorted(ohlcv.items()):
        result = detect_vcp_for_symbol(sym, rows, config)
        if result.get("skipped"):
            skipped.append(result)
        elif result.get("grade") == "reject":
            rejected.append(result)
        elif grade_order.get(result.get("grade", "reject"), 0) >= min_grade_threshold:
            candidates.append(result)
        else:
            rejected.append(result)

    # Sort candidates by score desc
    candidates.sort(key=lambda r: -r["score"])

    output = {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "universe_size": len(ohlcv),
        "candidates_count": len(candidates),
        "rejected_count": len(rejected),
        "skipped_count": len(skipped),
        "windows": {
            "trend": config["ma_short"],
            "long_trend": config["ma_long"],
            "volume_avg": config["vol_ma"],
        },
        "config": config,
        "candidates": candidates,
        "rejected": rejected,
        "skipped": skipped,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_vcp_screener_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")

    print(f"\nUniverse: {output['universe_size']} symbols")
    print(f"Candidates ({output['candidates_count']}):")
    for c in candidates[:20]:
        print(
            f"  {c['symbol']:6s} grade={c['grade']:1s} score={c['score']:3d}  "
            f"pivot={c['pivot_price']:>8,}  stop={c['suggested_stop']:>8,} "
            f"({c['stop_pct']:>4.1f}% drop)  contractions={len(c['contractions'])}"
        )
    if rejected:
        print(f"\nRejected: {len(rejected)} (top 5 by score)")
        for r in sorted(rejected, key=lambda x: -x.get("score", 0))[:5]:
            reasons = r.get("rejection_reasons") or r.get("notes", [])
            reason = reasons[0] if reasons else "low score"
            print(f"  {r['symbol']:6s} score={r.get('score', 0):3d}  → {reason}")


if __name__ == "__main__":
    main()
