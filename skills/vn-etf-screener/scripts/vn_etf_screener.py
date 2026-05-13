"""VN ETF Screener — score Vietnam-listed ETFs on tracking error, premium/discount,
expense ratio, and liquidity. Core portfolio passive-sleeve selection.

Universe schema in references/vn_etf_methodology.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))

# Convention: skip flagged statuses by default (same as equity screeners)
SKIP_STATUSES = {"Kiểm soát", "Hạn chế", "Tạm ngừng"}

GRADE_MAP = {4: "A", 3: "B", 2: "C", 1: "D", 0: "F"}


def format_vnd(x: float | int | None) -> str:
    """Render a VND amount with thousands separators."""
    if x is None:
        return "n/a"
    return f"{int(round(float(x))):,} VND"


def score_etf(etf: dict) -> dict:
    """Score one ETF on 4 factors. Returns full result dict."""
    factors = {
        "low_tracking_error": False,
        "low_premium_discount": False,
        "low_expense": False,
        "high_liquidity": False,
    }
    score = 0

    # 1. Tracking Error <= 1.0%
    te = etf.get("tracking_error_pct", 99)
    if te <= 1.0:
        factors["low_tracking_error"] = True
        score += 1

    # 2. Premium/Discount absolute <= 1.0%
    nav = etf.get("nav_per_share", 0) or 0
    market = etf.get("market_price", 0) or 0
    diff_pct = None
    if nav > 0:
        diff_pct = abs(market - nav) / nav * 100
        if diff_pct <= 1.0:
            factors["low_premium_discount"] = True
            score += 1

    # 3. Expense Ratio <= 0.7%
    er = etf.get("expense_ratio_pct", 99)
    if er <= 0.7:
        factors["low_expense"] = True
        score += 1

    # 4. Volume >= 100,000
    vol = etf.get("volume_20d_avg", 0) or 0
    if vol >= 100_000:
        factors["high_liquidity"] = True
        score += 1

    premium_discount_vnd = round(market - nav) if (nav > 0 and market > 0) else None

    return {
        "symbol": etf.get("symbol"),
        "name": etf.get("name"),
        "score": score,
        "grade": GRADE_MAP.get(score, "F"),
        "factors": factors,
        "nav_per_share_vnd": int(nav) if nav else None,
        "market_price_vnd": int(market) if market else None,
        "premium_discount_vnd": premium_discount_vnd,
        "premium_discount_pct": round(diff_pct, 3) if diff_pct is not None else None,
        "tracking_error_pct": te,
        "expense_ratio_pct": er,
        "volume_20d_avg": vol,
        "foreign_room_pct": etf.get("foreign_room_pct"),
        "raw_data": etf,
    }


def filter_status(etf: dict, include_flagged: bool) -> tuple[bool, str | None]:
    """Return (keep, skip_reason). status field is optional."""
    status = etf.get("status")
    if not status or include_flagged:
        return True, None
    if status in SKIP_STATUSES:
        return False, f"status={status}"
    return True, None


def screen(universe: list[dict], include_flagged: bool = False) -> dict:
    """Score every ETF in the universe. Returns full result dict."""
    results: list[dict] = []
    skipped: list[dict] = []
    for etf in universe:
        keep, reason = filter_status(etf, include_flagged)
        if not keep:
            skipped.append({"symbol": etf.get("symbol"), "reason": reason})
            continue
        results.append(score_etf(etf))
    results.sort(key=lambda r: (-r["score"], r["symbol"] or ""))
    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "universe_size": len(universe),
        "scored_count": len(results),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "results": results,
    }


def render_markdown(result: dict) -> str:
    """Render the screen result as a markdown report."""
    lines = [
        f"# VN ETF Screener — {result['as_of'][:10]}",
        "",
        f"Scored: **{result['scored_count']}** / Skipped: **{result['skipped_count']}** / Universe: {result['universe_size']}",
        "",
        "| ETF | Grade | Score | NAV | Market | Δ% | TE% | ER% | Vol20D |",
        "| --- | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in result["results"]:
        diff = f"{r['premium_discount_pct']:+.2f}" if r.get("premium_discount_pct") is not None else "—"
        lines.append(
            f"| **{r['symbol']}** ({r['name']}) | {r['grade']} | {r['score']}/4 | "
            f"{format_vnd(r['nav_per_share_vnd'])} | {format_vnd(r['market_price_vnd'])} | "
            f"{diff} | {r['tracking_error_pct']} | {r['expense_ratio_pct']} | "
            f"{(r['volume_20d_avg'] or 0):,} |"
        )
    if result["skipped"]:
        lines.append("")
        lines.append("## Skipped")
        for s in result["skipped"]:
            lines.append(f"- {s['symbol']}: {s['reason']}")
    return "\n".join(lines) + "\n"


def write_outputs(result: dict, output_dir: str) -> tuple[Path, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    json_path = out_dir / f"vn_etf_screener_{timestamp}.json"
    md_path = out_dir / f"vn_etf_screener_{timestamp}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return json_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VN ETF Screener")
    parser.add_argument("--input", required=True, help="Path to ETF universe JSON")
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument(
        "--include-flagged",
        action="store_true",
        help="Include ETFs with status flags (Kiểm soát/Hạn chế/Tạm ngừng); default skip",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Lỗi: không tìm thấy {input_path}", file=sys.stderr)
        return 1

    try:
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Lỗi parse JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("Lỗi: input phải là list of ETF objects", file=sys.stderr)
        return 1

    result = screen(data, include_flagged=args.include_flagged)
    json_path, md_path = write_outputs(result, args.output_dir)

    print(f"JSON: {json_path}")
    print(f"MD  : {md_path}")
    print(f"\n{result['scored_count']} ETF scored, {result['skipped_count']} skipped")
    for r in result["results"]:
        print(
            f"  {r['symbol']:10s} grade={r['grade']} score={r['score']}/4  "
            f"TE={r['tracking_error_pct']}%  ER={r['expense_ratio_pct']}%  "
            f"Vol={(r['volume_20d_avg'] or 0):,}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
