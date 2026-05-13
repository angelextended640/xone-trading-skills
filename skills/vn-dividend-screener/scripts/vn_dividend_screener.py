"""VN Dividend Screener — sàng lọc cổ phiếu cổ tức bền vững cho Core portfolio.

Consumes a universe JSON with per-symbol dividend history + fundamentals.
Scores on 5 pillars: yield, payout sustainability, dividend growth, financial
quality, EPS trajectory. Flags yield traps (high yield + collapsing EPS).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

VN_TZ = timezone(timedelta(hours=7))

# Defaults
DEFAULT_MIN_YIELD = 4.0
DEFAULT_MAX_PAYOUT = 80.0
DEFAULT_MIN_ROE = 12.0
DEFAULT_MIN_EPS_3Y_CAGR = -5.0
DEFAULT_MIN_CONSECUTIVE_YEARS = 3
DEFAULT_YIELD_TRAP_THRESHOLD = 8.0


# ---------------------------------------------------------------------------
# Universe loading
# ---------------------------------------------------------------------------


def load_universe(path: str) -> list[dict]:
    """Load a universe JSON and return the symbol list."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "universe" not in data:
        raise ValueError(f"Expected 'universe' key in {path}")
    return data["universe"]


# ---------------------------------------------------------------------------
# Dividend math (cash-only, stock dividends excluded for yield)
# ---------------------------------------------------------------------------


def extract_cash_dividends(history: list[dict]) -> list[dict]:
    """Filter to cash-only dividends, sorted by year descending."""
    cash = [d for d in history if d.get("type") == "cash"]
    cash.sort(key=lambda d: d.get("year", 0), reverse=True)
    return cash


def latest_cash_dividend(history: list[dict]) -> Optional[float]:
    """Return the most recent cash dividend amount, or None."""
    cash = extract_cash_dividends(history)
    if not cash:
        return None
    return float(cash[0].get("amount_vnd_per_share", 0))


def consecutive_paying_years(history: list[dict], min_amount: float = 1.0) -> int:
    """Count consecutive years from latest with cash dividend >= min_amount."""
    cash = extract_cash_dividends(history)
    if not cash:
        return 0
    # Walk back from latest year; gap or zero breaks the streak
    years = sorted({d["year"] for d in cash}, reverse=True)
    count = 0
    expected = years[0]
    for year in years:
        if year != expected:
            break
        # Sum all cash payments that year
        total = sum(
            float(d.get("amount_vnd_per_share", 0))
            for d in cash
            if d.get("year") == year
        )
        if total < min_amount:
            break
        count += 1
        expected = year - 1
    return count


def dividend_3y_cagr(history: list[dict]) -> Optional[float]:
    """Compute 3-year CAGR of cash dividends (latest vs 3 years prior)."""
    cash = extract_cash_dividends(history)
    if len(cash) < 2:
        return None
    latest = cash[0]
    latest_year = latest["year"]
    latest_amt = float(latest["amount_vnd_per_share"])
    # Find the entry from approximately 3 years prior
    target_year = latest_year - 3
    older = next((d for d in cash if d["year"] == target_year), None)
    if older is None:
        # Use oldest available if 3 years prior is missing
        older = cash[-1]
        years_back = latest_year - older["year"]
        if years_back < 1:
            return None
        older_amt = float(older["amount_vnd_per_share"])
        if older_amt <= 0:
            return None
        return ((latest_amt / older_amt) ** (1 / years_back) - 1) * 100
    older_amt = float(older["amount_vnd_per_share"])
    if older_amt <= 0:
        return None
    return ((latest_amt / older_amt) ** (1 / 3) - 1) * 100


def current_yield_pct(price: float, latest_cash: Optional[float]) -> Optional[float]:
    """Current yield = latest cash dividend / current price."""
    if not price or price <= 0 or latest_cash is None:
        return None
    return latest_cash / price * 100


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------


def score_yield(yield_pct: Optional[float]) -> int:
    if yield_pct is None:
        return 0
    y = yield_pct
    if 5 <= y <= 8:
        return 25
    if 4 <= y < 5 or 8 < y <= 10:
        return 22
    if 3 <= y < 4:
        return 15
    if 2 <= y < 3:
        return 8
    return 0


def score_payout_sustainability(
    payout_pct: Optional[float], eps_ttm: Optional[float]
) -> int:
    if payout_pct is None or eps_ttm is None or eps_ttm <= 0:
        return 0
    if payout_pct > 80:
        return 0
    if 30 <= payout_pct <= 65:
        return 25
    if 65 < payout_pct <= 80:
        return 20
    if payout_pct < 30:
        # Could be conservative or hoarding — moderate score
        return 10
    return 0


def score_dividend_growth(history: list[dict]) -> int:
    cagr = dividend_3y_cagr(history)
    consec = consecutive_paying_years(history)
    if cagr is None or consec < 3:
        return 0
    if consec >= 4 and cagr > 5:
        return 20
    if consec >= 4 and 0 <= cagr <= 5:
        return 15
    if consec >= 3 and cagr >= 0:
        return 8
    return 0


def score_financial_quality(roe: Optional[float], de: Optional[float]) -> int:
    if roe is None or de is None:
        return 0
    if roe > 15 and de < 1.0:
        return 20
    if roe >= 12 and de < 1.5:
        return 15
    if roe >= 10 and de < 1.5:
        return 8
    return 0


def score_eps_trajectory(eps_cagr: Optional[float]) -> int:
    if eps_cagr is None:
        return 0
    if eps_cagr > 5:
        return 10
    if 0 <= eps_cagr <= 5:
        return 7
    if -5 <= eps_cagr < 0:
        return 4
    return 0


# ---------------------------------------------------------------------------
# Yield trap detection
# ---------------------------------------------------------------------------


def detect_yield_trap(
    yield_pct: Optional[float],
    eps_cagr: Optional[float],
    payout_pct: Optional[float],
    threshold: float = DEFAULT_YIELD_TRAP_THRESHOLD,
) -> tuple[bool, list[str]]:
    """Return (is_trap, reasons)."""
    reasons: list[str] = []
    if yield_pct is None or yield_pct < threshold:
        return False, []
    # High yield — check sustainability
    if eps_cagr is not None and eps_cagr < -10:
        reasons.append(f"EPS declining {round(-eps_cagr, 1)}%/year (3y CAGR)")
    if payout_pct is not None and payout_pct > 100:
        reasons.append(f"Payout {round(payout_pct, 1)}% > 100% — unsustainable")
    return len(reasons) > 0, reasons


# ---------------------------------------------------------------------------
# Per-symbol screening
# ---------------------------------------------------------------------------


def screen_symbol(record: dict, config: dict) -> dict:
    """Score one symbol; return structured result."""
    symbol = record.get("symbol", "UNKNOWN")
    sector = record.get("sector", "Unknown")
    price = float(record.get("current_price", 0))
    fund = record.get("fundamentals", {})
    history = record.get("dividend_history", [])

    eps_ttm = fund.get("eps_ttm_vnd")
    eps_cagr = fund.get("eps_3y_cagr_pct")
    payout = fund.get("payout_ratio_pct")
    roe = fund.get("roe_pct")
    de = fund.get("debt_to_equity")

    latest_cash = latest_cash_dividend(history)
    yield_pct = current_yield_pct(price, latest_cash)
    div_cagr = dividend_3y_cagr(history)
    consec = consecutive_paying_years(history)

    # Yield trap check first
    is_trap, trap_reasons = detect_yield_trap(
        yield_pct, eps_cagr, payout, config["yield_trap_threshold"]
    )
    if is_trap:
        return {
            "symbol": symbol,
            "sector": sector,
            "current_price": int(round(price)),
            "current_yield_pct": round(yield_pct, 2) if yield_pct else None,
            "last_dividend_vnd": int(round(latest_cash)) if latest_cash else None,
            "eps_3y_cagr_pct": eps_cagr,
            "payout_ratio_pct": payout,
            "is_yield_trap": True,
            "trap_reasons": trap_reasons,
            "grade": "reject",
            "score": 0,
        }

    # Score
    yield_pts = score_yield(yield_pct)
    payout_pts = score_payout_sustainability(payout, eps_ttm)
    growth_pts = score_dividend_growth(history)
    quality_pts = score_financial_quality(roe, de)
    eps_pts = score_eps_trajectory(eps_cagr)
    total = yield_pts + payout_pts + growth_pts + quality_pts + eps_pts

    # Grade
    if total >= 80:
        grade = "A"
    elif total >= 60:
        grade = "B"
    elif total >= 40:
        grade = "C"
    else:
        grade = "reject"

    # Reasons / notes
    notes: list[str] = []
    rejection_reasons: list[str] = []

    if yield_pts == 0:
        rejection_reasons.append(
            f"Yield {round(yield_pct, 2) if yield_pct else 'n/a'}% < 2% threshold"
        )
    elif yield_pct and yield_pct >= config["min_yield"]:
        notes.append(f"Yield {round(yield_pct, 2)}% ≥ {config['min_yield']}% target")

    if payout_pts == 0:
        if payout is None or eps_ttm is None or eps_ttm <= 0:
            rejection_reasons.append("Missing payout or EPS data")
        else:
            rejection_reasons.append(f"Payout {round(payout, 1)}% > 80% threshold")

    if growth_pts == 0:
        rejection_reasons.append(
            f"Dividend history: {consec} consecutive years, CAGR not qualifying"
        )

    if quality_pts == 0:
        rejection_reasons.append(
            f"Quality: ROE={roe}%, D/E={de} — below benchmarks"
        )

    if eps_pts == 0 and eps_cagr is not None and eps_cagr < -5:
        rejection_reasons.append(f"EPS 3y CAGR {round(eps_cagr, 1)}% < -5%")

    return {
        "symbol": symbol,
        "sector": sector,
        "grade": grade,
        "score": total,
        "components": {
            "yield": yield_pts,
            "payout_sustainability": payout_pts,
            "dividend_growth": growth_pts,
            "financial_quality": quality_pts,
            "eps_trajectory": eps_pts,
        },
        "current_price": int(round(price)),
        "current_yield_pct": round(yield_pct, 2) if yield_pct else None,
        "last_dividend_vnd": int(round(latest_cash)) if latest_cash else None,
        "dividend_3y_cagr_pct": round(div_cagr, 2) if div_cagr else None,
        "payout_ratio_pct": payout,
        "eps_ttm_vnd": eps_ttm,
        "eps_3y_cagr_pct": eps_cagr,
        "roe_pct": roe,
        "debt_to_equity": de,
        "consecutive_paying_years": consec,
        "is_yield_trap": False,
        "notes": notes,
        "rejection_reasons": rejection_reasons if grade == "reject" else [],
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run(universe: list[dict], config: dict, min_grade: str = "C") -> dict:
    grade_order = {"A": 3, "B": 2, "C": 1, "reject": 0}
    threshold = grade_order[min_grade]

    candidates: list[dict] = []
    yield_traps: list[dict] = []
    rejected: list[dict] = []

    for rec in universe:
        result = screen_symbol(rec, config)
        if result.get("is_yield_trap"):
            yield_traps.append(result)
        elif grade_order.get(result.get("grade", "reject"), 0) >= threshold:
            candidates.append(result)
        else:
            rejected.append(result)

    # Sort candidates by score desc
    candidates.sort(key=lambda r: -r["score"])

    # Sector distribution
    sector_dist: dict[str, int] = {}
    for c in candidates:
        sec = c.get("sector", "Unknown")
        sector_dist[sec] = sector_dist.get(sec, 0) + 1

    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "universe_size": len(universe),
        "candidates_count": len(candidates),
        "yield_traps_count": len(yield_traps),
        "rejected_count": len(rejected),
        "config": config,
        "candidates": candidates,
        "yield_traps": yield_traps,
        "rejected": rejected,
        "sector_distribution": sector_dist,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VN dividend-stock screener — yield + sustainability + quality + yield-trap detection"
    )
    parser.add_argument("--universe", required=True, help="Path to universe JSON")
    parser.add_argument("--min-yield", type=float, default=DEFAULT_MIN_YIELD)
    parser.add_argument("--max-payout", type=float, default=DEFAULT_MAX_PAYOUT)
    parser.add_argument("--min-roe", type=float, default=DEFAULT_MIN_ROE)
    parser.add_argument(
        "--min-eps-3y-cagr", type=float, default=DEFAULT_MIN_EPS_3Y_CAGR
    )
    parser.add_argument(
        "--min-consecutive-years",
        type=int,
        default=DEFAULT_MIN_CONSECUTIVE_YEARS,
    )
    parser.add_argument(
        "--yield-trap-threshold",
        type=float,
        default=DEFAULT_YIELD_TRAP_THRESHOLD,
    )
    parser.add_argument("--min-grade", choices=["A", "B", "C"], default="C")
    parser.add_argument("--output-dir", default="reports/")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        universe = load_universe(args.universe)
    except (FileNotFoundError, ValueError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    config = {
        "min_yield": args.min_yield,
        "max_payout": args.max_payout,
        "min_roe": args.min_roe,
        "min_eps_3y_cagr": args.min_eps_3y_cagr,
        "min_consecutive_years": args.min_consecutive_years,
        "yield_trap_threshold": args.yield_trap_threshold,
    }

    result = run(universe, config, args.min_grade)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_dividend_screener_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")

    print(f"\nUniverse: {result['universe_size']} symbols")
    print(f"Candidates ({result['candidates_count']}):")
    for c in result["candidates"][:20]:
        print(
            f"  {c['symbol']:6s} grade={c['grade']:1s} score={c['score']:3d}  "
            f"yield={c.get('current_yield_pct', 0):>5.2f}%  "
            f"payout={c.get('payout_ratio_pct', 0):>5.1f}%  "
            f"ROE={c.get('roe_pct', 0):>4.1f}%  "
            f"sector={c.get('sector', '')[:20]}"
        )

    if result["yield_traps"]:
        print(f"\n⚠️  Yield traps ({result['yield_traps_count']}):")
        for t in result["yield_traps"]:
            reasons = ", ".join(t.get("trap_reasons", []))
            print(
                f"  {t['symbol']:6s} yield={t.get('current_yield_pct', 0):>5.2f}%  → {reasons}"
            )

    if result["sector_distribution"]:
        print(f"\nSector distribution (candidates):")
        for sec, n in sorted(result["sector_distribution"].items(), key=lambda x: -x[1]):
            print(f"  {sec}: {n}")


if __name__ == "__main__":
    main()
