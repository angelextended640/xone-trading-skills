"""VN Trader Memory — review-due, postmortem, summary stats.

Postmortem markdown lives under ``state/vn_journal/`` (separate from the
international ``state/journal/``). MAE/MFE excludes T+0/T+1 because shares
are not liquidatable until T+2.5.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vn_thesis_store  # noqa: E402

logger = logging.getLogger(__name__)

JOURNAL_DIR_NAME = "vn_journal"


# -- MAE / MFE ----------------------------------------------------------------


def compute_mae_mfe(thesis: dict, price_adapter: Any | None = None) -> dict[str, Any]:
    """Compute Maximum Adverse / Favourable Excursion from daily closes.

    Args:
        thesis: Thesis dict (must have entry.actual_price + actual_date).
        price_adapter: object exposing ``get_daily_closes(ticker, from, to)``.

    Returns: ``{"mae_pct", "mfe_pct", "mae_mfe_source"}`` — values are None
    when prices can't be fetched and ``mae_mfe_source = "manual"`` so the
    user knows the postmortem needs hand-entered numbers.
    """
    result = {"mae_pct": None, "mfe_pct": None, "mae_mfe_source": "manual"}

    if price_adapter is None:
        return result

    entry_price = thesis.get("entry", {}).get("actual_price")
    entry_date = thesis.get("entry", {}).get("actual_date")
    if not entry_price or not entry_date:
        return result

    exit_date = thesis.get("exit", {}).get("actual_date")
    if not exit_date:
        exit_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    from_date = entry_date[:10]
    to_date = exit_date[:10]

    try:
        prices = price_adapter.get_daily_closes(thesis["ticker"], from_date, to_date)
    except Exception as e:
        logger.warning("Failed to fetch prices for %s: %s", thesis["ticker"], e)
        return result

    if not prices:
        return result

    closes = [p["close"] for p in prices]
    if not closes:
        return result

    mae_pct = ((min(closes) - entry_price) / entry_price) * 100
    mfe_pct = ((max(closes) - entry_price) / entry_price) * 100

    result["mae_pct"] = round(mae_pct, 2)
    result["mfe_pct"] = round(mfe_pct, 2)
    result["mae_mfe_source"] = "vnstock"
    return result


# -- Postmortem ---------------------------------------------------------------


def generate_postmortem(
    thesis_id: str,
    state_dir: str,
    price_adapter: Any | None = None,
    journal_dir: str | None = None,
) -> str:
    state_path = Path(state_dir)
    thesis = vn_thesis_store.get(state_path, thesis_id)

    if thesis["status"] not in ("CLOSED", "INVALIDATED"):
        raise ValueError(
            f"Postmortem requires CLOSED or INVALIDATED thesis, got status={thesis['status']}"
        )

    mae_mfe = compute_mae_mfe(thesis, price_adapter)
    if thesis.get("outcome") is None:
        thesis["outcome"] = {}
    thesis["outcome"]["mae_pct"] = mae_mfe["mae_pct"]
    thesis["outcome"]["mfe_pct"] = mae_mfe["mfe_pct"]
    thesis["outcome"]["mae_mfe_source"] = mae_mfe["mae_mfe_source"]

    # Persist MAE/MFE on the thesis YAML so reruns are idempotent.
    state_dir_path = Path(state_dir)
    path = state_dir_path / f"{thesis_id}.yaml"
    vn_thesis_store._validate_thesis(thesis)
    vn_thesis_store._atomic_write_yaml(path, thesis)
    index = vn_thesis_store._load_index(state_dir_path)
    vn_thesis_store._update_index_entry(index, thesis)
    vn_thesis_store._save_index(state_dir_path, index)

    if journal_dir:
        j_dir = Path(journal_dir)
    else:
        j_dir = state_path.parent / JOURNAL_DIR_NAME
    j_dir.mkdir(parents=True, exist_ok=True)

    content = _render_postmortem(thesis)
    pm_path = j_dir / f"pm_{thesis_id}.md"
    pm_path.write_text(content, encoding="utf-8")
    logger.info("Generated postmortem: %s", pm_path)
    return str(pm_path)


def _fmt_vnd(val) -> str:
    if val is None:
        return "—"
    try:
        return f"{val:,.0f} VND"
    except (TypeError, ValueError):
        return str(val)


def _fmt_pct(val) -> str:
    if val is None:
        return "—"
    try:
        return f"{val:+.2f}%"
    except (TypeError, ValueError):
        return str(val)


def _render_postmortem(thesis: dict) -> str:
    entry = thesis.get("entry") or {}
    exit_data = thesis.get("exit") or {}
    outcome = thesis.get("outcome") or {}
    position = thesis.get("position") or {}
    market = thesis.get("market_context") or {}

    evidence = "\n".join(f"- {e}" for e in thesis.get("evidence", [])) or "- (chưa ghi nhận)"
    kill = "\n".join(f"- {k}" for k in thesis.get("kill_criteria", [])) or "- (chưa ghi nhận)"

    shares = position.get("shares") or 0
    entry_price = entry.get("actual_price")
    exit_price = exit_data.get("actual_price")
    entry_value = (entry_price or 0) * shares if entry_price else None
    exit_value = (exit_price or 0) * shares if exit_price else None
    net_outcome = "—"
    if outcome.get("net_pnl_vnd") is not None:
        net_outcome = "WIN" if outcome["net_pnl_vnd"] >= 0 else "LOSS"

    return f"""# Postmortem — {thesis["ticker"]} ({thesis.get("setup_type") or thesis.get("thesis_type")})

**Thesis:** {thesis["thesis_id"]}
**Trạng thái:** {thesis["status"]} — {net_outcome}
**Sàn:** {thesis.get("exchange") or "—"} | **Ngành:** {market.get("sector") or "—"}
**Holding:** {entry.get("actual_date", "—")[:10]} → {exit_data.get("actual_date", "—")[:10]} ({outcome.get("holding_days", "—")} trading days)

## Original thesis

{thesis.get("thesis_statement", "(không có statement)")}

## Trade execution

| Mốc | Ngày | Giá | Khối lượng | Giá trị |
|---|---|---|---|---|
| Entry | {entry.get("actual_date", "—")[:10]} | {_fmt_vnd(entry_price)} | {shares:,} | {_fmt_vnd(entry_value)} |
| Exit | {exit_data.get("actual_date", "—")[:10]} | {_fmt_vnd(exit_price)} | {shares:,} | {_fmt_vnd(exit_value)} |

- **Gross P&L:** {_fmt_vnd(outcome.get("gross_pnl_vnd"))}
- **Phí môi giới:** {_fmt_vnd(outcome.get("broker_fee_vnd"))}
- **Thuế bán:** {_fmt_vnd(outcome.get("sale_tax_vnd"))}
- **Net P&L:** {_fmt_vnd(outcome.get("net_pnl_vnd"))} ({_fmt_pct(outcome.get("net_pnl_pct"))})

## Excursion analysis (T+2 trở đi)

- MAE: {_fmt_pct(outcome.get("mae_pct"))}
- MFE: {_fmt_pct(outcome.get("mfe_pct"))}
- Nguồn MAE/MFE: {outcome.get("mae_mfe_source") or "manual"}

> Lưu ý: T+0/T+1 bị loại khỏi tính toán vì cổ phiếu chưa về tài khoản (HOSE/HNX/UPCOM = T+2.5).

## Evidence at entry

{evidence}

## Kill criteria

{kill}

## Lessons learned

{outcome.get("lessons_learned") or "(điền thủ công sau khi review)"}
"""


# -- Summary stats ------------------------------------------------------------


def summary_stats(state_dir: str) -> dict:
    state_path = Path(state_dir)
    closed = vn_thesis_store.query(state_path, status="CLOSED")
    invalidated = vn_thesis_store.query(state_path, status="INVALIDATED")
    all_terminal = closed + invalidated

    if not all_terminal:
        return {"count": 0, "win_rate": None, "avg_net_pnl_pct": None, "by_type": {}}

    stats = {"count": 0, "wins": 0, "total_pnl_pct": 0.0, "by_type": {}}

    for entry in all_terminal:
        thesis = vn_thesis_store.get(state_path, entry["thesis_id"])
        pnl_pct = (thesis.get("outcome") or {}).get("net_pnl_pct")
        if pnl_pct is None:
            continue
        stats["count"] += 1
        stats["total_pnl_pct"] += pnl_pct
        if pnl_pct >= 0:
            stats["wins"] += 1
        ttype = thesis.get("thesis_type", "unknown")
        bucket = stats["by_type"].setdefault(
            ttype, {"count": 0, "wins": 0, "total_pnl_pct": 0.0}
        )
        bucket["count"] += 1
        bucket["total_pnl_pct"] += pnl_pct
        if pnl_pct >= 0:
            bucket["wins"] += 1

    n = stats["count"]
    out = {
        "count": n,
        "win_rate": round(stats["wins"] / n, 4) if n else None,
        "avg_net_pnl_pct": round(stats["total_pnl_pct"] / n, 2) if n else None,
        "by_type": {},
    }
    for ttype, b in stats["by_type"].items():
        out["by_type"][ttype] = {
            "count": b["count"],
            "win_rate": round(b["wins"] / b["count"], 4) if b["count"] else None,
            "avg_net_pnl_pct": round(b["total_pnl_pct"] / b["count"], 2) if b["count"] else None,
        }
    return out


# -- CLI ----------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="VN Trader Memory — review tools")
    parser.add_argument("--state-dir", default="state/vn_theses")
    sub = parser.add_subparsers(dest="command")

    due_p = sub.add_parser("review-due", help="List theses due for review")
    due_p.add_argument("--as-of", default=None)

    mr_p = sub.add_parser("mark-reviewed", help="Record a periodic review")
    mr_p.add_argument("--thesis-id", required=True)
    mr_p.add_argument(
        "--status",
        dest="outcome",
        default="OK",
        choices=["OK", "WARN", "REVIEW"],
    )
    mr_p.add_argument("--review-date", default=None)
    mr_p.add_argument("--note", default=None)

    pm_p = sub.add_parser("postmortem", help="Generate postmortem for a thesis")
    pm_p.add_argument("--thesis-id", required=True)
    pm_p.add_argument("--journal-dir", default=None)
    pm_p.add_argument(
        "--no-prices",
        action="store_true",
        help="Skip vnstock fetch — mae_mfe_source becomes 'manual'",
    )

    sub.add_parser("summary", help="Show portfolio summary stats")

    args = parser.parse_args()

    if args.command == "review-due":
        as_of = args.as_of or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        results = vn_thesis_store.list_review_due(Path(args.state_dir), as_of)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.command == "mark-reviewed":
        review_date = args.review_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        t = vn_thesis_store.mark_reviewed(
            Path(args.state_dir),
            args.thesis_id,
            review_date=review_date,
            outcome=args.outcome,
            notes=args.note,
        )
        print(
            f"Reviewed {args.thesis_id}: {args.outcome}, next: "
            f"{t['monitoring']['next_review_date']}"
        )
    elif args.command == "postmortem":
        adapter = None
        if not args.no_prices:
            from vn_price_adapter import VNPriceAdapter

            adapter = VNPriceAdapter()
        path = generate_postmortem(
            args.thesis_id,
            args.state_dir,
            price_adapter=adapter,
            journal_dir=args.journal_dir,
        )
        print(f"Postmortem generated: {path}")
    elif args.command == "summary":
        s = summary_stats(args.state_dir)
        print(json.dumps(s, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
