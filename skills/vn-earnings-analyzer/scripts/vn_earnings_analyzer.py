"""VN Earnings Analyzer — score recent earnings reactions on 5 factors.

5 factors (each +1 point, max 5):
  gap_up        — gap_pct >= 2.0 (VN ±7% band caps daily moves; 2% is the meaningful threshold)
  high_volume   — volume_relative >= 1.5
  uptrend_20d   — trend_20d_pct >= 0
  above_ma      — above_ma50 AND above_ma200
  eps_beat      — eps_surprise_pct > 0

Methodology details: references/vn_earnings_methodology.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))

SKIP_STATUSES = {"Kiểm soát", "Hạn chế", "Tạm ngừng", "Cảnh báo"}

GRADE_MAP = {5: "A", 4: "B", 3: "C", 2: "D", 1: "F", 0: "F"}


def format_vnd(x: float | int | None) -> str:
    if x is None:
        return "n/a"
    return f"{int(round(float(x))):,} VND"


def analyze_earnings(record: dict) -> dict:
    """Score one earnings record on 5 factors; return full result dict."""
    factors = {
        "gap_up": False,
        "high_volume": False,
        "uptrend_20d": False,
        "above_ma": False,
        "eps_beat": False,
    }
    score = 0

    if (record.get("gap_pct") or 0) >= 2.0:
        factors["gap_up"] = True
        score += 1

    if (record.get("volume_relative") or 0) >= 1.5:
        factors["high_volume"] = True
        score += 1

    if (record.get("trend_20d_pct") or 0) >= 0.0:
        factors["uptrend_20d"] = True
        score += 1

    if bool(record.get("above_ma50")) and bool(record.get("above_ma200")):
        factors["above_ma"] = True
        score += 1

    if (record.get("eps_surprise_pct") or 0) > 0.0:
        factors["eps_beat"] = True
        score += 1

    grade = GRADE_MAP.get(score, "F")

    return {
        "symbol": record.get("symbol", "UNKNOWN"),
        "report_date": record.get("report_date", ""),
        "score": score,
        "grade": grade,
        "factors": factors,
        "gap_pct": record.get("gap_pct"),
        "volume_relative": record.get("volume_relative"),
        "trend_20d_pct": record.get("trend_20d_pct"),
        "above_ma50": bool(record.get("above_ma50")),
        "above_ma200": bool(record.get("above_ma200")),
        "eps_surprise_pct": record.get("eps_surprise_pct"),
        "current_price_vnd": record.get("current_price"),
        "report_day_low_vnd": record.get("report_day_low"),
        "raw_data": record,
    }


def filter_status(record: dict, include_flagged: bool) -> tuple[bool, str | None]:
    status = record.get("status")
    if not status or include_flagged:
        return True, None
    if status in SKIP_STATUSES:
        return False, f"status={status}"
    return True, None


def analyze(
    earnings: list[dict],
    include_flagged: bool = False,
    min_grade: str = "F",
) -> dict:
    """Run scoring on a list of earnings records, sorted by score desc."""
    grade_order = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}
    threshold = grade_order.get(min_grade.upper(), 0)

    results: list[dict] = []
    skipped: list[dict] = []
    for r in earnings:
        keep, reason = filter_status(r, include_flagged)
        if not keep:
            skipped.append({"symbol": r.get("symbol"), "reason": reason})
            continue
        scored = analyze_earnings(r)
        if grade_order[scored["grade"]] >= threshold:
            results.append(scored)
    results.sort(key=lambda x: (-x["score"], x["symbol"] or ""))

    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "input_count": len(earnings),
        "scored_count": len(results),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "min_grade": min_grade.upper(),
        "results": results,
    }


def render_markdown(result: dict) -> str:
    lines = [
        f"# VN Earnings Analyzer — {result['as_of'][:10]}",
        "",
        f"Input: **{result['input_count']}** / Scored: **{result['scored_count']}** "
        f"/ Skipped: **{result['skipped_count']}** / Min grade: **{result['min_grade']}**",
        "",
        "| Symbol | Report | Grade | Score | Gap% | Vol× | Trend20% | MA | EPS Surprise | Price |",
        "| --- | --- | :---: | :---: | ---: | ---: | ---: | :---: | ---: | ---: |",
    ]
    for r in result["results"]:
        ma = "✓50/200" if r["above_ma50"] and r["above_ma200"] else (
            "✓50" if r["above_ma50"] else ("✓200" if r["above_ma200"] else "—")
        )
        lines.append(
            f"| **{r['symbol']}** | {r['report_date']} | {r['grade']} | {r['score']}/5 | "
            f"{r['gap_pct']} | {r['volume_relative']}× | {r['trend_20d_pct']}% | {ma} | "
            f"{r['eps_surprise_pct']}% | {format_vnd(r['current_price_vnd'])} |"
        )
    if result["skipped"]:
        lines += ["", "## Skipped", ""]
        for s in result["skipped"]:
            lines.append(f"- {s['symbol']}: {s['reason']}")
    return "\n".join(lines) + "\n"


def write_outputs(result: dict, output_dir: str) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    j = out / f"vn_earnings_analyzer_{ts}.json"
    m = out / f"vn_earnings_analyzer_{ts}.md"
    j.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    m.write_text(render_markdown(result), encoding="utf-8")
    return j, m


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VN Earnings Analyzer")
    parser.add_argument("--input", required=True, help="Path to earnings JSON")
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument("--min-grade", choices=["A", "B", "C", "D", "F"], default="F")
    parser.add_argument(
        "--include-flagged",
        action="store_true",
        help="Include Kiểm soát/Hạn chế/Tạm ngừng/Cảnh báo (default: skip)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Lỗi: không tìm thấy {in_path}", file=sys.stderr)
        return 1

    try:
        with open(in_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Lỗi parse JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("Lỗi: input phải là list of earnings records", file=sys.stderr)
        return 1

    result = analyze(data, include_flagged=args.include_flagged, min_grade=args.min_grade)
    j, m = write_outputs(result, args.output_dir)

    print(f"JSON: {j}")
    print(f"MD  : {m}")
    print(
        f"\nScored {result['scored_count']} (grade ≥ {result['min_grade']}), "
        f"skipped {result['skipped_count']} flagged"
    )
    for r in result["results"][:20]:
        print(
            f"  {r['symbol']:6s} {r['report_date']} grade={r['grade']} score={r['score']}/5 "
            f"gap={r['gap_pct']}% vol×{r['volume_relative']} eps_surprise={r['eps_surprise_pct']}%"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
