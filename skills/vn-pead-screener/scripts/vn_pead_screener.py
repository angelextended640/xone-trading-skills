"""VN PEAD Screener — Post-Earnings Announcement Drift entry-planner.

Mode A — standalone universe scan (--candidates)
Mode B — pipeline from vn-earnings-analyzer JSON (--candidates)

Both modes share the screening logic; Mode B unwraps the `results` wrapper
emitted by the analyzer. Each candidate is screened for:
  - grade ≥ --min-grade (default B)
  - has_red_candle_pullback flag
  - current_price > report_day_low (setup still valid)
  - stop_loss > floor_price (VN ±band check) — warn but include

Methodology: references/vn_pead_methodology.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))

PRICE_BAND_PCT = {"hose": 7.0, "hnx": 10.0, "upcom": 15.0}

GRADE_ORDER = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}


def format_vnd(x: float | int | None) -> str:
    if x is None:
        return "n/a"
    return f"{int(round(float(x))):,} VND"


def tick_size_hose(price: float) -> int:
    if price < 10_000:
        return 10
    if price < 50_000:
        return 50
    return 100


def tick_size(exchange: str, price: float) -> int:
    return tick_size_hose(price) if exchange == "hose" else 100


def round_to_tick(price: float, exchange: str, mode: str = "nearest") -> int:
    tick = tick_size(exchange, price)
    if mode == "down":
        return int(price // tick * tick)
    if mode == "up":
        return int(-(-price // tick) * tick)
    return int(round(price / tick) * tick)


def compute_price_band(reference_price: float, exchange: str) -> dict:
    """Compute VN ceiling/floor per exchange band (HOSE 7%, HNX 10%, UPCOM 15%)."""
    pct = PRICE_BAND_PCT.get(exchange.lower(), 7.0)
    raw_ceiling = reference_price * (1 + pct / 100)
    raw_floor = reference_price * (1 - pct / 100)
    return {
        "reference_price_vnd": int(round(reference_price)),
        "ceiling_price_vnd": round_to_tick(raw_ceiling, exchange.lower(), mode="down"),
        "floor_price_vnd": round_to_tick(raw_floor, exchange.lower(), mode="up"),
        "price_band_pct": pct,
    }


def unwrap_candidates(data) -> list[dict]:
    """Mode B: data is {results: [...]} from vn-earnings-analyzer.
    Mode A: data is a plain list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    raise ValueError("Input phải là list hoặc dict có khoá 'results'")


def screen_one(
    candidate: dict,
    r_multiples: list[float],
    min_grade: str = "B",
) -> dict | None:
    """Return a screened result dict, or None if the candidate is invalid."""
    grade = candidate.get("grade", "F")
    if GRADE_ORDER.get(grade, 0) < GRADE_ORDER.get(min_grade, 4):
        return None

    raw = candidate.get("raw_data") or candidate
    has_pullback = raw.get("has_red_candle_pullback") if "has_red_candle_pullback" in raw else candidate.get(
        "has_red_candle_pullback"
    )
    if not has_pullback:
        return None

    # Prefer top-level fields (Mode A) over raw_data fields (Mode B)
    current_price = candidate.get("current_price_vnd") or candidate.get("current_price") or raw.get("current_price")
    report_day_low = candidate.get("report_day_low_vnd") or candidate.get("report_day_low") or raw.get(
        "report_day_low"
    )
    if not current_price or not report_day_low:
        return None
    current_price = float(current_price)
    report_day_low = float(report_day_low)

    # Stop ≤ floor invalidates (setup already broken)
    if current_price <= report_day_low or report_day_low <= 0:
        return None

    exchange = (candidate.get("exchange") or raw.get("exchange") or "hose").lower()
    reference_price = float(
        candidate.get("reference_price")
        or raw.get("reference_price")
        or current_price
    )

    risk = current_price - report_day_low
    band = compute_price_band(reference_price, exchange)

    stop_above_floor = report_day_low > band["floor_price_vnd"]

    targets = []
    for r in r_multiples:
        raw_target = current_price + r * risk
        targets.append(
            {
                "r_multiple": r,
                "target_price_vnd": round_to_tick(raw_target, exchange, mode="nearest"),
            }
        )

    warnings: list[str] = []
    if not stop_above_floor:
        warnings.append(
            f"Stop {int(report_day_low):,} ≤ floor {band['floor_price_vnd']:,} — "
            f"biên độ sẽ chặn lệnh stop trong phiên đầu. Điều chỉnh stop lên trên floor hoặc skip."
        )

    return {
        "symbol": candidate.get("symbol"),
        "grade": grade,
        "report_date": candidate.get("report_date") or raw.get("report_date"),
        "exchange": exchange,
        "entry_price_vnd": int(round(current_price)),
        "stop_loss_vnd": int(round(report_day_low)),
        "risk_per_share_vnd": int(round(risk)),
        "targets": targets,
        # Default 2R as the primary target (legacy field name preserved)
        "target_price_vnd": targets[-1]["target_price_vnd"] if targets else None,
        "r_multiple": targets[-1]["r_multiple"] if targets else None,
        **band,
        "stop_above_floor": stop_above_floor,
        "warnings": warnings,
    }


def screen(
    candidates: list[dict],
    r_multiples: list[float] | None = None,
    min_grade: str = "B",
) -> dict:
    r_multiples = r_multiples or [2.0]
    results: list[dict] = []
    rejected: list[dict] = []
    for c in candidates:
        screened = screen_one(c, r_multiples, min_grade)
        if screened is None:
            rejected.append(
                {"symbol": c.get("symbol"), "grade": c.get("grade"), "reason": "filtered or invalid"}
            )
        else:
            results.append(screened)
    # Sort by grade (A first), then by R achieved at primary target descending
    results.sort(key=lambda r: (-GRADE_ORDER.get(r["grade"], 0), r["symbol"] or ""))
    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "input_count": len(candidates),
        "valid_count": len(results),
        "rejected_count": len(rejected),
        "min_grade": min_grade,
        "r_multiples": r_multiples,
        "results": results,
        "rejected": rejected,
    }


def render_markdown(result: dict) -> str:
    lines = [
        f"# VN PEAD Screener — {result['as_of'][:10]}",
        "",
        f"Input: **{result['input_count']}** / Valid: **{result['valid_count']}** "
        f"/ Rejected: **{result['rejected_count']}** / Min grade: **{result['min_grade']}**",
        "",
        "| Symbol | Grade | Report | Exch | Entry | Stop | Floor | Risk/sh | Target | Warnings |",
        "| --- | :---: | --- | :---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in result["results"]:
        warn = "; ".join(r["warnings"]) if r["warnings"] else "—"
        lines.append(
            f"| **{r['symbol']}** | {r['grade']} | {r['report_date']} | {r['exchange'].upper()} | "
            f"{format_vnd(r['entry_price_vnd'])} | {format_vnd(r['stop_loss_vnd'])} | "
            f"{format_vnd(r['floor_price_vnd'])} | {format_vnd(r['risk_per_share_vnd'])} | "
            f"{format_vnd(r['target_price_vnd'])} ({r['r_multiple']}R) | {warn} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(result: dict, output_dir: str) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    j = out / f"vn_pead_screener_{ts}.json"
    m = out / f"vn_pead_screener_{ts}.md"
    j.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    m.write_text(render_markdown(result), encoding="utf-8")
    return j, m


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VN PEAD Screener")
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidate JSON — accepts vn-earnings-analyzer output (Mode B) or plain list (Mode A)",
    )
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument("--min-grade", choices=["A", "B", "C", "D"], default="B")
    parser.add_argument(
        "--r-targets",
        default="2",
        help="Comma-separated R multiples for targets (e.g. '1,2,3'); default '2'",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    in_path = Path(args.candidates)
    if not in_path.exists():
        print(f"Lỗi: không tìm thấy {in_path}", file=sys.stderr)
        return 1
    try:
        with open(in_path, encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Lỗi parse JSON: {e}", file=sys.stderr)
        return 1

    try:
        candidates = unwrap_candidates(raw_data)
    except ValueError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 1

    r_multiples = [float(x.strip()) for x in args.r_targets.split(",") if x.strip()]
    result = screen(candidates, r_multiples=r_multiples, min_grade=args.min_grade)
    j, m = write_outputs(result, args.output_dir)

    print(f"JSON: {j}")
    print(f"MD  : {m}")
    print(
        f"\nValid setups: {result['valid_count']} / {result['input_count']} "
        f"input (min grade {args.min_grade})"
    )
    for r in result["results"][:20]:
        warn_marker = " ⚠️" if r["warnings"] else ""
        print(
            f"  {r['symbol']:6s} grade={r['grade']} entry={r['entry_price_vnd']:>8,} "
            f"stop={r['stop_loss_vnd']:>8,} target={r['target_price_vnd']:>8,} "
            f"({r['r_multiple']}R){warn_marker}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
