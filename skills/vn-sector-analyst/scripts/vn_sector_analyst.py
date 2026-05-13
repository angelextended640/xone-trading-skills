"""VN Sector Analyst — phân tích rotation theo ngành cho VN-Index.

Consumes batch OHLCV JSON from vn-data-fetcher and computes per-sector
returns over multiple windows, relative strength vs VN-Index, trend
signals, and rotation hints.

Sector mapping is static, loaded from references/vn_sector_mapping.json.
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

DEFAULT_WINDOWS = [5, 20, 60]

# Module-relative path to the sector mapping
MAPPING_PATH = Path(__file__).resolve().parent.parent / "references" / "vn_sector_mapping.json"


# ---------------------------------------------------------------------------
# Sector mapping
# ---------------------------------------------------------------------------


def load_sector_mapping(path: Path = MAPPING_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def symbol_to_sector(mapping: dict) -> dict[str, str]:
    """Invert mapping: {'VCB': 'Banking', 'VIC': 'Real Estate', ...}."""
    out = {}
    for sector_name, info in mapping["sectors"].items():
        for sym in info["symbols"]:
            out[sym.upper()] = sector_name
    return out


# ---------------------------------------------------------------------------
# OHLCV loading
# ---------------------------------------------------------------------------


def load_ohlcv_batch(path: str) -> dict[str, list[dict]]:
    """Load a batch-mode JSON from vn-data-fetcher → {symbol: [rows]}."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    # Multi-symbol shape: {"symbols": [...], "data": {SYM: [rows]}}
    if "symbols" in raw and isinstance(raw.get("data"), dict):
        return {sym.upper(): rows for sym, rows in raw["data"].items()}

    # Single-symbol shape: {"symbol": "VIC", "data": [rows]}
    if "symbol" in raw and isinstance(raw.get("data"), list):
        return {raw["symbol"].upper(): raw["data"]}

    raise ValueError(
        "Định dạng OHLCV không nhận dạng được. Cần output từ vn-data-fetcher."
    )


def load_ohlcv_multiple(paths: list[str]) -> dict[str, list[dict]]:
    """Merge multiple JSON files (single or batch shape) into a single dict."""
    out: dict[str, list[dict]] = {}
    for p in paths:
        batch = load_ohlcv_batch(p)
        out.update(batch)
    return out


# ---------------------------------------------------------------------------
# Returns calculation
# ---------------------------------------------------------------------------


def compute_window_return(rows: list[dict], window: int) -> Optional[float]:
    """Compute % return over the last `window` trading days. None if insufficient data."""
    if not rows or len(rows) < window + 1:
        return None
    # Use close prices; rows are sorted by time ascending
    closes = [float(r["close"]) for r in rows]
    end = closes[-1]
    start = closes[-1 - window]
    if start == 0:
        return None
    return round((end - start) / start * 100, 3)


def compute_returns(rows: list[dict], windows: list[int]) -> dict[str, Optional[float]]:
    """Return {'5D': ..., '20D': ..., '60D': ...}."""
    return {f"{w}D": compute_window_return(rows, w) for w in windows}


# ---------------------------------------------------------------------------
# Per-symbol and per-sector aggregation
# ---------------------------------------------------------------------------


def per_symbol_returns(
    ohlcv: dict[str, list[dict]], windows: list[int]
) -> dict[str, dict[str, Optional[float]]]:
    return {sym: compute_returns(rows, windows) for sym, rows in ohlcv.items()}


def average_returns(
    returns_list: list[dict[str, Optional[float]]], windows: list[int]
) -> dict[str, Optional[float]]:
    """Average returns across symbols within a sector. None entries are excluded."""
    out: dict[str, Optional[float]] = {}
    for w in windows:
        key = f"{w}D"
        values = [r[key] for r in returns_list if r.get(key) is not None]
        out[key] = round(sum(values) / len(values), 3) if values else None
    return out


def relative_strength(
    sector_returns: dict[str, Optional[float]],
    benchmark_returns: dict[str, Optional[float]],
) -> dict[str, Optional[float]]:
    """RS = sector_return - benchmark_return (in percentage points)."""
    out: dict[str, Optional[float]] = {}
    for key, val in sector_returns.items():
        b = benchmark_returns.get(key)
        if val is None or b is None:
            out[key] = None
        else:
            out[key] = round(val - b, 3)
    return out


def trend_signal(returns: dict[str, Optional[float]], rs: dict[str, Optional[float]]) -> str:
    r5 = returns.get("5D")
    r20 = returns.get("20D")
    rs5 = rs.get("5D")
    rs20 = rs.get("20D")

    if r5 is None or r20 is None:
        return "unknown"
    if r5 > r20 > 0:
        return "accelerating"
    if r5 < r20 < 0:
        return "falling"
    if r5 > 0 and rs5 is not None and rs20 is not None and rs5 > rs20:
        return "improving"
    if r5 < 0 and rs5 is not None and rs20 is not None and rs5 < rs20:
        return "deteriorating"
    return "stable"


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------


def analyze(
    ohlcv: dict[str, list[dict]],
    benchmark_rows: list[dict] | None,
    mapping: dict,
    windows: list[int] = None,
) -> dict:
    windows = windows or DEFAULT_WINDOWS
    sym_to_sec = symbol_to_sector(mapping)
    per_sym = per_symbol_returns(ohlcv, windows)

    # Benchmark
    if benchmark_rows is not None:
        bench_returns = compute_returns(benchmark_rows, windows)
    else:
        # Equal-weight average across all available symbols as a proxy
        bench_returns = average_returns(list(per_sym.values()), windows)

    # Group by sector
    sectors_out = []
    sector_to_syms: dict[str, list[str]] = {}
    for sym in ohlcv.keys():
        sec = sym_to_sec.get(sym)
        if sec is None:
            sec = "Other"
        sector_to_syms.setdefault(sec, []).append(sym)

    for sector_name, syms in sector_to_syms.items():
        sym_returns = [per_sym[s] for s in syms]
        sec_returns = average_returns(sym_returns, windows)
        rs = relative_strength(sec_returns, bench_returns)
        signal = trend_signal(sec_returns, rs)

        # Top/bottom by 20D
        ranked = sorted(
            [
                {"symbol": s, "return_20D": per_sym[s].get("20D"), "return_5D": per_sym[s].get("5D")}
                for s in syms
                if per_sym[s].get("20D") is not None
            ],
            key=lambda r: r["return_20D"],
            reverse=True,
        )
        top_3 = ranked[:3]
        bottom_3 = list(reversed(ranked[-3:])) if len(ranked) >= 3 else ranked[-len(ranked):]

        weight_info = mapping["sectors"].get(sector_name, {})
        sectors_out.append(
            {
                "name": sector_name,
                "vn_index_weight_approx_pct": weight_info.get(
                    "vn_index_weight_approx_pct"
                ),
                "symbols_count": len(syms),
                "symbols_with_data": sum(
                    1 for s in syms if per_sym[s].get("20D") is not None
                ),
                "returns": sec_returns,
                "relative_strength": rs,
                "trend_signal": signal,
                "top_3_by_20D": top_3,
                "bottom_3_by_20D": bottom_3,
            }
        )

    # Sort sectors by RS_20D desc (leaders first)
    def _rs20(s):
        v = s["relative_strength"].get("20D")
        return v if v is not None else -1e9

    sectors_out.sort(key=_rs20, reverse=True)

    # Rotation hints
    hints = []
    for sec in sectors_out:
        rs20 = sec["relative_strength"].get("20D")
        rs5 = sec["relative_strength"].get("5D")
        if rs20 is None:
            continue
        if rs20 > 1.0 and (rs5 or 0) > 0:
            hints.append(
                {
                    "type": "leader",
                    "sector": sec["name"],
                    "msg": f"{sec['name']} dẫn dắt (RS_20D +{rs20}, RS_5D +{rs5 or 0})",
                }
            )
        elif rs20 < -1.0 and (rs5 or 0) < 0:
            hints.append(
                {
                    "type": "laggard",
                    "sector": sec["name"],
                    "msg": f"{sec['name']} yếu (RS_20D {rs20})",
                }
            )

    # Regime hint
    banking = next((s for s in sectors_out if s["name"] == "Banking"), None)
    real_estate = next((s for s in sectors_out if s["name"] == "Real Estate"), None)
    regime_note = None
    if banking and real_estate:
        b_rs = banking["relative_strength"].get("20D")
        re_rs = real_estate["relative_strength"].get("20D")
        if b_rs is not None and re_rs is not None:
            if b_rs > 0 and re_rs > 0:
                regime_note = "Banking + Real Estate có cùng diễn biến mạnh — xu hướng tăng có cơ sở"
            elif b_rs < -1.0 and re_rs < -1.0:
                regime_note = (
                    "Banking + Real Estate cùng yếu — có dấu hiệu risk-off, "
                    "cẩn trọng khi mở vị thế mới"
                )
            elif b_rs > 1.0 and re_rs < -1.0:
                regime_note = (
                    "Banking dẫn nhưng Real Estate tụt — phân hoá nội bộ, "
                    "có thể là rotation từ growth sang banking"
                )

    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "windows": windows,
        "benchmark": "VNINDEX" if benchmark_rows is not None else "equal_weight_universe",
        "benchmark_returns": bench_returns,
        "sectors": sectors_out,
        "rotation_hints": hints,
        "regime_note": regime_note,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phân tích rotation theo ngành VN-Index"
    )
    parser.add_argument(
        "--ohlcv-file",
        action="append",
        help="Path tới JSON output của vn-data-fetcher (lặp lại nếu nhiều file)",
    )
    parser.add_argument(
        "--ohlcv-glob",
        help="Glob pattern để match nhiều file OHLCV (ví dụ 'reports/vn_ohlcv_*.json')",
    )
    parser.add_argument(
        "--benchmark-file",
        help="Path tới OHLCV JSON cho VN-Index (nếu không có, dùng equal-weight universe)",
    )
    parser.add_argument(
        "--fixture",
        help="Fixture JSON chứa multi-symbol OHLCV (cho test offline)",
    )
    parser.add_argument(
        "--mapping-file",
        default=str(MAPPING_PATH),
        help="Path tới sector mapping JSON (mặc định: references/vn_sector_mapping.json)",
    )
    parser.add_argument(
        "--windows",
        default="5,20,60",
        help="Cửa sổ tính return (CSV của ints), mặc định '5,20,60'",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/",
        help="Thư mục báo cáo (mặc định reports/)",
    )
    return parser


def collect_ohlcv_paths(args: argparse.Namespace) -> list[str]:
    paths: list[str] = []
    if args.ohlcv_file:
        paths.extend(args.ohlcv_file)
    if args.ohlcv_glob:
        paths.extend(sorted(glob.glob(args.ohlcv_glob)))
    return paths


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        mapping = load_sector_mapping(Path(args.mapping_file))
        windows = [int(x.strip()) for x in args.windows.split(",")]

        # Load OHLCV
        if args.fixture:
            ohlcv = load_ohlcv_batch(args.fixture)
        else:
            paths = collect_ohlcv_paths(args)
            if not paths:
                parser.error("Cần --ohlcv-file, --ohlcv-glob, hoặc --fixture")
            ohlcv = load_ohlcv_multiple(paths)

        # Load benchmark
        benchmark_rows = None
        if args.benchmark_file:
            bench_batch = load_ohlcv_batch(args.benchmark_file)
            # Take the first (and presumably only) symbol's rows
            if bench_batch:
                benchmark_rows = next(iter(bench_batch.values()))

        result = analyze(ohlcv, benchmark_rows, mapping, windows=windows)
    except (ValueError, FileNotFoundError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    out_path = Path(args.output_dir) / f"vn_sector_analysis_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {out_path}")

    # Stdout summary
    print(f"\nBenchmark ({result['benchmark']}) returns:")
    for k, v in result["benchmark_returns"].items():
        print(f"  {k}: {v}%" if v is not None else f"  {k}: n/a")

    print(f"\n{'Sector':30s} {'5D':>8s} {'20D':>8s} {'60D':>8s} {'RS_20D':>8s} {'Signal':>15s}")
    for sec in result["sectors"]:
        r = sec["returns"]
        rs = sec["relative_strength"]
        print(
            f"{sec['name']:30s} "
            f"{(r.get('5D') if r.get('5D') is not None else 0):>7.2f}% "
            f"{(r.get('20D') if r.get('20D') is not None else 0):>7.2f}% "
            f"{(r.get('60D') if r.get('60D') is not None else 0):>7.2f}% "
            f"{(rs.get('20D') if rs.get('20D') is not None else 0):>+7.2f} "
            f"{sec['trend_signal']:>15s}"
        )

    if result["rotation_hints"]:
        print("\nRotation hints:")
        for h in result["rotation_hints"]:
            print(f"  {h['msg']}")

    if result["regime_note"]:
        print(f"\nRegime: {result['regime_note']}")


if __name__ == "__main__":
    main()
