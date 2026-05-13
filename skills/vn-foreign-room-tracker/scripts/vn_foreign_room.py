"""VN Foreign Room Tracker — theo dõi room ngoại cho watchlist HOSE/HNX.

Ingest daily snapshots from CSV/JSON, store rolling history under
state/vn_foreign_room/, and emit reports with alerts for room-full,
room-released, and spike events.

Manual entry by default — vnstock has no unified foreign-room endpoint
across sources. See SKILL.md for data source options.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

VN_TZ = timezone(timedelta(hours=7))

HISTORY_FIELDS = [
    "as_of_date",
    "symbol",
    "room_total",
    "room_used",
    "room_remaining",
    "room_used_pct",
]


# ---------------------------------------------------------------------------
# State I/O
# ---------------------------------------------------------------------------


def history_path(state_dir: Path) -> Path:
    return state_dir / "history.csv"


def load_history(state_dir: Path) -> list[dict]:
    p = history_path(state_dir)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_history(state_dir: Path, rows: list[dict]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    p = history_path(state_dir)
    write_header = not p.exists() or p.stat().st_size == 0
    with open(p, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in HISTORY_FIELDS})


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


def parse_input_csv(path: str, as_of_date: str) -> list[dict]:
    """Read input CSV with columns: symbol, room_total, room_used, room_remaining."""
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = parse_input_row(raw, as_of_date)
            rows.append(row)
    return rows


def parse_input_json(path: str, as_of_date: str) -> list[dict]:
    """Read JSON list-of-records or dict."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "rows" in data:
        data = data["rows"]
    if not isinstance(data, list):
        raise ValueError("JSON đầu vào phải là list of records hoặc {'rows': [...]}")
    return [parse_input_row(r, as_of_date) for r in data]


def parse_input_row(raw: dict, as_of_date: str) -> dict:
    """Validate and normalize a single input row."""
    sym = (raw.get("symbol") or "").strip().upper()
    if not sym:
        raise ValueError("Mỗi dòng phải có symbol")
    room_total = int(float(raw["room_total"]))
    if "room_used" in raw and "room_remaining" in raw:
        room_used = int(float(raw["room_used"]))
        room_remaining = int(float(raw["room_remaining"]))
    elif "room_used" in raw:
        room_used = int(float(raw["room_used"]))
        room_remaining = room_total - room_used
    elif "room_remaining" in raw:
        room_remaining = int(float(raw["room_remaining"]))
        room_used = room_total - room_remaining
    else:
        raise ValueError(f"{sym}: cần room_used hoặc room_remaining")

    if room_total <= 0:
        raise ValueError(f"{sym}: room_total phải dương")
    if room_used < 0 or room_remaining < 0:
        raise ValueError(f"{sym}: room_used và room_remaining không được âm")

    room_used_pct = round(room_used / room_total * 100, 4)
    return {
        "as_of_date": as_of_date,
        "symbol": sym,
        "room_total": room_total,
        "room_used": room_used,
        "room_remaining": room_remaining,
        "room_used_pct": room_used_pct,
    }


# ---------------------------------------------------------------------------
# Subcommand: record
# ---------------------------------------------------------------------------


def run_record(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    as_of = args.as_of or datetime.now(VN_TZ).strftime("%Y-%m-%d")

    if args.input.endswith(".json"):
        rows = parse_input_json(args.input, as_of)
    else:
        rows = parse_input_csv(args.input, as_of)

    append_history(state_dir, rows)

    return {
        "schema_version": "1.0",
        "subcommand": "record",
        "as_of_date": as_of,
        "rows_ingested": len(rows),
        "symbols": sorted({r["symbol"] for r in rows}),
    }


# ---------------------------------------------------------------------------
# Subcommand: report
# ---------------------------------------------------------------------------


def find_latest_date(history: list[dict]) -> str | None:
    if not history:
        return None
    return max(r["as_of_date"] for r in history)


def date_n_days_before(date_str: str, days: int) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return (d - timedelta(days=days)).strftime("%Y-%m-%d")


def find_comparison_date(history: list[dict], latest: str, lookback_days: int) -> str | None:
    """Find the latest history date that is ≥ lookback_days before `latest`."""
    target = date_n_days_before(latest, lookback_days)
    candidates = sorted({r["as_of_date"] for r in history if r["as_of_date"] <= target})
    return candidates[-1] if candidates else None


def classify_status(
    row: dict,
    prior: dict | None,
    full_threshold: float,
    release_threshold: float,
    spike_threshold: float,
) -> tuple[str, str | None]:
    """Return (status, alert_message_or_None)."""
    pct = float(row["room_used_pct"])

    # Base status
    if pct >= full_threshold:
        base = "full"
    elif pct >= release_threshold:
        base = "high_usage"
    else:
        base = "normal"

    # Transition detection vs prior
    if prior is None:
        return base, None

    prior_pct = float(prior["room_used_pct"])
    delta = pct - prior_pct

    # Released: was full, now below release_threshold
    if prior_pct >= full_threshold and pct < release_threshold:
        return "released", f"{row['symbol']} vừa giải phóng room ({pct}% xuống dưới {release_threshold}%)"

    # Spike up
    if delta > spike_threshold:
        return "spike_up", f"{row['symbol']} room dùng tăng {round(delta,2)}% (từ {prior_pct}% lên {pct}%)"

    # Spike down (but not enough to count as released)
    if delta < -spike_threshold:
        return "spike_down", f"{row['symbol']} room dùng giảm {round(-delta,2)}% (từ {prior_pct}% xuống {pct}%)"

    # Just-now full
    if prior_pct < full_threshold and pct >= full_threshold:
        return "full", f"{row['symbol']} vừa đầy room ({pct}%)"

    # No alert
    return base, None


def run_report(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    history = load_history(state_dir)
    if not history:
        raise ValueError("Chưa có history. Chạy 'record' trước.")

    latest = find_latest_date(history)
    if latest is None:
        raise ValueError("Không xác định được latest_date")

    comparison = find_comparison_date(history, latest, args.lookback_days)

    latest_rows = [r for r in history if r["as_of_date"] == latest]
    comparison_rows = (
        {r["symbol"]: r for r in history if r["as_of_date"] == comparison}
        if comparison
        else {}
    )

    output_rows = []
    alerts = []
    for row in latest_rows:
        prior = comparison_rows.get(row["symbol"])
        status, alert_msg = classify_status(
            row,
            prior,
            args.full_threshold,
            args.release_threshold,
            args.spike_threshold,
        )
        pct = float(row["room_used_pct"])
        prior_pct = float(prior["room_used_pct"]) if prior else None
        change_pct = round(pct - prior_pct, 4) if prior_pct is not None else None
        change_remaining = (
            int(row["room_remaining"]) - int(prior["room_remaining"]) if prior else None
        )

        output_rows.append(
            {
                "symbol": row["symbol"],
                "room_used_pct": pct,
                "room_remaining": int(row["room_remaining"]),
                "room_total": int(row["room_total"]),
                "change_pct": change_pct,
                "change_remaining": change_remaining,
                "status": status,
            }
        )
        if alert_msg:
            alerts.append({"symbol": row["symbol"], "type": status, "msg": alert_msg})

    # Sort: alerts first, then by room_used_pct desc
    output_rows.sort(key=lambda r: (-r["room_used_pct"]))

    return {
        "schema_version": "1.0",
        "subcommand": "report",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "latest_date": latest,
        "comparison_date": comparison,
        "lookback_days": args.lookback_days,
        "thresholds": {
            "full": args.full_threshold,
            "release": args.release_threshold,
            "spike": args.spike_threshold,
        },
        "row_count": len(output_rows),
        "rows": output_rows,
        "alerts": alerts,
    }


# ---------------------------------------------------------------------------
# Subcommand: history
# ---------------------------------------------------------------------------


def run_history(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    history = load_history(state_dir)
    sym = args.symbol.upper()
    rows = [r for r in history if r["symbol"] == sym]
    rows.sort(key=lambda r: r["as_of_date"])
    if args.days:
        # Keep only rows where as_of_date is within args.days of latest
        if rows:
            latest = rows[-1]["as_of_date"]
            cutoff = date_n_days_before(latest, args.days)
            rows = [r for r in rows if r["as_of_date"] >= cutoff]

    return {
        "schema_version": "1.0",
        "subcommand": "history",
        "symbol": sym,
        "row_count": len(rows),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state-dir",
        default="state/vn_foreign_room/",
        help="Thư mục state CSV (mặc định state/vn_foreign_room/)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/",
        help="Thư mục báo cáo (mặc định reports/)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Theo dõi room ngoại cho watchlist cổ phiếu Việt Nam"
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_rec = sub.add_parser("record", help="Ingest CSV/JSON room snapshot")
    p_rec.add_argument("--input", required=True, help="File CSV hoặc JSON đầu vào")
    p_rec.add_argument(
        "--as-of",
        help="Ngày snapshot YYYY-MM-DD (mặc định hôm nay)",
    )
    add_common_args(p_rec)

    p_rep = sub.add_parser("report", help="Báo cáo room hiện tại + alerts")
    p_rep.add_argument(
        "--lookback-days",
        type=int,
        default=5,
        help="So sánh với N ngày trước (mặc định 5)",
    )
    p_rep.add_argument(
        "--full-threshold",
        type=float,
        default=99.0,
        help="%% coi là 'full' (mặc định 99)",
    )
    p_rep.add_argument(
        "--release-threshold",
        type=float,
        default=90.0,
        help="%% coi là 'high_usage' (mặc định 90)",
    )
    p_rep.add_argument(
        "--spike-threshold",
        type=float,
        default=5.0,
        help="%% thay đổi để alert spike (mặc định 5)",
    )
    add_common_args(p_rep)

    p_hist = sub.add_parser("history", help="Xem chuỗi thời gian 1 mã")
    p_hist.add_argument("--symbol", required=True)
    p_hist.add_argument("--days", type=int, default=30, help="Số ngày gần nhất")
    add_common_args(p_hist)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.subcommand == "record":
            result = run_record(args)
        elif args.subcommand == "report":
            result = run_report(args)
        elif args.subcommand == "history":
            result = run_history(args)
        else:
            parser.error(f"Unknown subcommand: {args.subcommand}")
            return
    except (ValueError, FileNotFoundError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_foreign_room_{args.subcommand}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")

    # Compact stdout summary
    if args.subcommand == "record":
        print(
            f"\nĐã ghi {result['rows_ingested']} dòng cho {result['as_of_date']} — "
            f"{len(result['symbols'])} mã"
        )
    elif args.subcommand == "report":
        print(f"\nBáo cáo {result['latest_date']} (so với {result['comparison_date']}):")
        for r in result["rows"][:10]:
            ch = f" Δ{r['change_pct']:+.2f}%" if r["change_pct"] is not None else ""
            print(
                f"  {r['symbol']:8s} {r['room_used_pct']:6.2f}%{ch}  "
                f"[{r['status']}]"
            )
        if result["alerts"]:
            print("\nAlerts:")
            for a in result["alerts"]:
                print(f"  ⚠️  {a['msg']}")
    elif args.subcommand == "history":
        print(f"\n{result['symbol']} — {result['row_count']} snapshot:")
        for r in result["rows"][-10:]:
            print(
                f"  {r['as_of_date']}: used {r['room_used_pct']}% "
                f"(remaining {int(r['room_remaining']):,})"
            )


if __name__ == "__main__":
    main()
