"""VN CANSLIM Screener — adapted for Vietnam market mechanics.

5 pillars (each +1 point, max 5):
  C/A  — eps_growth_yoy_pct >= 20%
  N    — price within 5% of 52-week high
  S    — 20-day average volume >= 100k
  L    — rs_rating >= 80
  I    — foreign_net_buy_10d_vnd >= 0 (institutional proxy)

Methodology details: references/vn_canslim_methodology.md
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


def format_vnd(x: float | int | None) -> str:
    if x is None:
        return "n/a"
    return f"{int(round(float(x))):,} VND"


def evaluate_canslim(record: dict) -> dict:
    """Score one symbol on 5 pillars; return full result dict."""
    pillars = {"C_A": False, "N": False, "S": False, "L": False, "I": False}
    score = 0

    # C & A: EPS Growth YoY >= 20%
    if (record.get("eps_growth_yoy_pct") or 0) >= 20.0:
        pillars["C_A"] = True
        score += 1

    # N: Price within 5% of 52-week high
    price = record.get("price", 0) or 0
    high_52w = record.get("high_52w") or 0
    if price > 0 and high_52w > 0 and price >= high_52w * 0.95:
        pillars["N"] = True
        score += 1

    # S: Volume 20d avg >= 100k
    vol = record.get("volume_20d_avg", 0) or 0
    if vol >= 100_000:
        pillars["S"] = True
        score += 1

    # L: RS rating >= 80
    if (record.get("rs_rating") or 0) >= 80:
        pillars["L"] = True
        score += 1

    # I: Foreign net buy 10d >= 0
    if (record.get("foreign_net_buy_10d_vnd", 0) or 0) >= 0:
        pillars["I"] = True
        score += 1

    if score == 5:
        grade = "A"
    elif score == 4:
        grade = "B"
    else:
        grade = "C"

    return {
        "symbol": record.get("symbol", "UNKNOWN"),
        "sector": record.get("sector"),
        "score": score,
        "grade": grade,
        "pillars": pillars,
        "price_vnd": int(price) if price else None,
        "high_52w_vnd": int(high_52w) if high_52w else None,
        "pct_below_52w": (
            round((1 - price / high_52w) * 100, 2) if (price > 0 and high_52w > 0) else None
        ),
        "volume_20d_avg": vol,
        "eps_growth_yoy_pct": record.get("eps_growth_yoy_pct"),
        "rs_rating": record.get("rs_rating"),
        "foreign_net_buy_10d_vnd": record.get("foreign_net_buy_10d_vnd"),
        "raw_data": record,
    }


def filter_status(record: dict, include_flagged: bool) -> tuple[bool, str | None]:
    status = record.get("status")
    if not status or include_flagged:
        return True, None
    if status in SKIP_STATUSES:
        return False, f"status={status}"
    return True, None


def screen(
    universe: list[dict],
    include_flagged: bool = False,
    min_grade: str = "C",
    market_regime: str | None = None,
) -> dict:
    """Score every symbol. Optionally filter by minimum grade and market regime."""
    grade_order = {"A": 3, "B": 2, "C": 1}
    threshold = grade_order.get(min_grade.upper(), 1)

    results: list[dict] = []
    skipped: list[dict] = []
    for rec in universe:
        keep, reason = filter_status(rec, include_flagged)
        if not keep:
            skipped.append({"symbol": rec.get("symbol"), "reason": reason})
            continue
        scored = evaluate_canslim(rec)
        if grade_order[scored["grade"]] >= threshold:
            results.append(scored)
    results.sort(key=lambda r: (-r["score"], r["symbol"] or ""))

    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "universe_size": len(universe),
        "results_count": len(results),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "market_regime": market_regime,
        "market_advisory": (
            "⚠️ M-pillar: regime='risk-off' — hold off on new entries"
            if market_regime == "risk-off"
            else None
        ),
        "min_grade": min_grade.upper(),
        "results": results,
    }


def render_markdown(result: dict) -> str:
    lines = [
        f"# VN CANSLIM Screener — {result['as_of'][:10]}",
        "",
        f"Universe: **{result['universe_size']}** / Scored: **{result['results_count']}** "
        f"/ Skipped: **{result['skipped_count']}** / Min grade: **{result['min_grade']}**",
        "",
    ]
    if result.get("market_advisory"):
        lines += [f"> {result['market_advisory']}", ""]

    lines += [
        "| Symbol | Sector | Grade | Score | Price | Δ to 52w | EPS YoY | RS | NN10D |",
        "| --- | --- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in result["results"]:
        delta = (
            f"−{r['pct_below_52w']}%"
            if (r["pct_below_52w"] is not None and r["pct_below_52w"] > 0)
            else "at peak"
        )
        nn = format_vnd(r["foreign_net_buy_10d_vnd"]) if r["foreign_net_buy_10d_vnd"] is not None else "—"
        lines.append(
            f"| **{r['symbol']}** | {r['sector'] or '—'} | {r['grade']} | {r['score']}/5 | "
            f"{format_vnd(r['price_vnd'])} | {delta} | {r['eps_growth_yoy_pct']}% | "
            f"{r['rs_rating']} | {nn} |"
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
    j = out / f"vn_canslim_screener_{ts}.json"
    m = out / f"vn_canslim_screener_{ts}.md"
    j.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    m.write_text(render_markdown(result), encoding="utf-8")
    return j, m


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VN CANSLIM Screener")
    parser.add_argument("--universe", required=True, help="Path to universe JSON")
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument(
        "--min-grade", choices=["A", "B", "C"], default="C", help="Minimum grade in results"
    )
    parser.add_argument(
        "--include-flagged",
        action="store_true",
        help="Include Kiểm soát/Hạn chế/Tạm ngừng/Cảnh báo (default: skip)",
    )
    parser.add_argument(
        "--market-regime",
        choices=["risk-on", "neutral", "risk-off"],
        default=None,
        help="M-pillar context from vn-sector-analyst; advisory only",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    universe_path = Path(args.universe)
    if not universe_path.exists():
        print(f"Lỗi: không tìm thấy universe {universe_path}", file=sys.stderr)
        return 1

    try:
        with open(universe_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Lỗi parse JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("Lỗi: universe phải là list of records", file=sys.stderr)
        return 1

    result = screen(
        data,
        include_flagged=args.include_flagged,
        min_grade=args.min_grade,
        market_regime=args.market_regime,
    )
    j, m = write_outputs(result, args.output_dir)

    print(f"JSON: {j}")
    print(f"MD  : {m}")
    if result.get("market_advisory"):
        print(f"\n{result['market_advisory']}", file=sys.stderr)
    print(
        f"\nScored {result['results_count']} (grade ≥ {result['min_grade']}), "
        f"skipped {result['skipped_count']} flagged"
    )
    for r in result["results"][:20]:
        print(
            f"  {r['symbol']:6s} grade={r['grade']} score={r['score']}/5  "
            f"EPS_YoY={r['eps_growth_yoy_pct']}%  RS={r['rs_rating']}  "
            f"sector={(r['sector'] or '')[:25]}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
