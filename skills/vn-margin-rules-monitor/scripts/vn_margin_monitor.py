"""VN Margin Rules Monitor — track per-broker margin-eligible lists.

Subcommands:
  record   — Ingest a CTCK margin CSV (snapshotted by date)
  check    — Look up a symbol across all brokers; optional Q-rated warning
  report   — Aggregate stats per broker (count, avg rate, Q-rated count)
  history  — List snapshot history for a broker

State layout:
  state/vn_margin/<broker>_margin_list.csv     — latest snapshot
  state/vn_margin/history/<broker>_<date>.csv  — append-only history
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))
DEFAULT_STATE_DIR = "state/vn_margin"

Q_RATED_HINTS = ("q-rated", "kiểm soát", "hạn chế", "tạm ngừng", "cảnh báo", "suspended", "warning")


def state_dir(base: str = DEFAULT_STATE_DIR) -> Path:
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def history_dir(base: str = DEFAULT_STATE_DIR) -> Path:
    p = state_dir(base) / "history"
    p.mkdir(parents=True, exist_ok=True)
    return p


def is_q_rated(note: str) -> bool:
    """Return True if the note string looks like a Q-rated flag."""
    if not note:
        return False
    lower = note.lower()
    return any(hint in lower for hint in Q_RATED_HINTS)


# ---------------------------------------------------------------------------
# Subcommand: record
# ---------------------------------------------------------------------------


def record_margin(broker: str, csv_path: str, base_dir: str = DEFAULT_STATE_DIR) -> bool:
    """Copy the broker's margin CSV into state, with a date-stamped history copy."""
    input_p = Path(csv_path)
    if not input_p.exists():
        print(f"Lỗi: không tìm thấy {input_p}", file=sys.stderr)
        return False

    content = input_p.read_text(encoding="utf-8")
    broker_l = broker.lower()
    state = state_dir(base_dir)
    hist = history_dir(base_dir)

    latest = state / f"{broker_l}_margin_list.csv"
    latest.write_text(content, encoding="utf-8")

    today = datetime.now(VN_TZ).strftime("%Y-%m-%d")
    snapshot = hist / f"{broker_l}_{today}.csv"
    snapshot.write_text(content, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Subcommand: check
# ---------------------------------------------------------------------------


def check_symbol(symbol: str, base_dir: str = DEFAULT_STATE_DIR) -> dict:
    """Look up a symbol across all broker margin lists."""
    p = state_dir(base_dir)
    target = symbol.upper()
    results: dict[str, dict] = {}
    for f in sorted(p.glob("*_margin_list.csv")):
        broker = f.name.replace("_margin_list.csv", "").upper()
        try:
            with open(f, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    if (row.get("symbol", "") or "").strip().upper() == target:
                        results[broker] = row
                        break
        except (OSError, csv.Error):
            continue
    return results


# ---------------------------------------------------------------------------
# Subcommand: report
# ---------------------------------------------------------------------------


def report_brokers(base_dir: str = DEFAULT_STATE_DIR) -> dict:
    """Aggregate per-broker stats: count, avg rate, Q-rated count."""
    p = state_dir(base_dir)
    rows = []
    for f in sorted(p.glob("*_margin_list.csv")):
        broker = f.name.replace("_margin_list.csv", "").upper()
        total = 0
        zero_rate = 0
        q_rated = 0
        rate_sum = 0.0
        symbols_q_rated: list[str] = []
        try:
            with open(f, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    sym = (row.get("symbol", "") or "").strip()
                    if not sym:
                        continue
                    total += 1
                    try:
                        rate = float(row.get("rate", "0") or "0")
                    except ValueError:
                        rate = 0.0
                    rate_sum += rate
                    if rate == 0:
                        zero_rate += 1
                    if is_q_rated(row.get("note", "") or ""):
                        q_rated += 1
                        symbols_q_rated.append(sym)
        except (OSError, csv.Error) as e:
            rows.append({"broker": broker, "error": str(e)})
            continue
        avg_rate = round(rate_sum / total, 2) if total else 0.0
        rows.append(
            {
                "broker": broker,
                "total_symbols": total,
                "avg_rate_pct": avg_rate,
                "zero_rate_count": zero_rate,
                "q_rated_count": q_rated,
                "q_rated_symbols": symbols_q_rated[:50],  # cap list
            }
        )
    return {
        "schema_version": "1.0",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "brokers": rows,
        "broker_count": len(rows),
    }


# ---------------------------------------------------------------------------
# Subcommand: history
# ---------------------------------------------------------------------------


def list_history(broker: str, base_dir: str = DEFAULT_STATE_DIR) -> dict:
    """List snapshot dates + row counts for one broker."""
    hist = history_dir(base_dir)
    broker_l = broker.lower()
    snapshots = []
    for f in sorted(hist.glob(f"{broker_l}_*.csv")):
        try:
            with open(f, encoding="utf-8") as fh:
                count = sum(1 for _ in csv.DictReader(fh))
        except (OSError, csv.Error):
            count = -1
        # Extract date from filename: <broker>_YYYY-MM-DD.csv
        stem = f.stem  # broker_2026-05-13
        date_part = stem[len(broker_l) + 1 :]
        snapshots.append({"date": date_part, "row_count": count, "path": str(f)})
    return {
        "schema_version": "1.0",
        "broker": broker.upper(),
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VN Margin Rules Monitor")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_rec = sub.add_parser("record", help="Ingest a broker's margin CSV")
    p_rec.add_argument("--broker", required=True)
    p_rec.add_argument("--csv", required=True)
    p_rec.add_argument("--state-dir", default=DEFAULT_STATE_DIR)

    p_chk = sub.add_parser("check", help="Look up a symbol across brokers")
    p_chk.add_argument("--symbol", required=True)
    p_chk.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    p_chk.add_argument(
        "--warn-q-rated",
        action="store_true",
        help="Print warning if any broker tagged the symbol as Q-rated",
    )

    p_rep = sub.add_parser("report", help="Per-broker stats")
    p_rep.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    p_rep.add_argument("--output-dir", default="reports/")

    p_his = sub.add_parser("history", help="Snapshot history for one broker")
    p_his.add_argument("--broker", required=True)
    p_his.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    p_his.add_argument("--output-dir", default="reports/")

    return parser


def write_json(payload: dict, output_dir: str, name: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    p = out / f"vn_margin_{name}_{ts}.json"
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "record":
        ok = record_margin(args.broker, args.csv, args.state_dir)
        if ok:
            print(f"Đã ghi danh sách margin của {args.broker.upper()}")
            return 0
        return 1

    if args.cmd == "check":
        res = check_symbol(args.symbol, args.state_dir)
        if not res:
            print(f"{args.symbol.upper()}: không tìm thấy trong danh sách margin nào.")
            return 0
        q_hit = False
        for broker, row in res.items():
            note = row.get("note", "") or ""
            rate = row.get("rate", "0")
            q = is_q_rated(note)
            q_hit = q_hit or q
            marker = " ⚠️ Q-rated" if (args.warn_q_rated and q) else ""
            print(f"[{broker}] {args.symbol.upper()}: rate {rate}%, note='{note}'{marker}")
        if args.warn_q_rated and q_hit:
            print(
                f"\n⚠️ {args.symbol.upper()} bị flag Q-rated ở ít nhất 1 CTCK — "
                f"cảnh báo cắt margin tiềm năng.",
                file=sys.stderr,
            )
        return 0

    if args.cmd == "report":
        payload = report_brokers(args.state_dir)
        p = write_json(payload, args.output_dir, "report")
        print(f"JSON: {p}")
        print(f"\nBroker count: {payload['broker_count']}")
        for row in payload["brokers"]:
            if "error" in row:
                print(f"  {row['broker']}: ERROR {row['error']}")
                continue
            print(
                f"  {row['broker']:8s} total={row['total_symbols']:4d} "
                f"avg_rate={row['avg_rate_pct']:5.2f}%  "
                f"zero={row['zero_rate_count']:3d}  q-rated={row['q_rated_count']:3d}"
            )
        return 0

    if args.cmd == "history":
        payload = list_history(args.broker, args.state_dir)
        p = write_json(payload, args.output_dir, f"history_{args.broker.lower()}")
        print(f"JSON: {p}")
        print(
            f"\n{payload['broker']}: {payload['snapshot_count']} snapshot(s)"
        )
        for s in payload["snapshots"][-10:]:
            print(f"  {s['date']}: {s['row_count']} rows")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
