"""VN Breakout Trade Planner — end-to-end long breakout planning for VN stocks.

Integrates:
  - Lot-100 position sizing with VN fees + tax
  - Price ceiling/floor checks
  - R-multiple targets (default 1R/2R/3R, partial exits)
  - T+2.5 sellable-day calendar
  - Optional context from vn-sector-analyst and vn-foreign-room-tracker

Position-sizing logic is vendored inline rather than imported from vn-position-sizer
to keep per-skill sys.path isolation clean (see CLAUDE.md).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

VN_TZ = timezone(timedelta(hours=7))

LOT_SIZE = 100

PRICE_BAND_PCT = {
    "hose": 7.0,
    "hnx": 10.0,
    "upcom": 15.0,
}

DEFAULT_BROKER_FEE_PCT = 0.15
DEFAULT_SALE_TAX_PCT = 0.10
DEFAULT_TARGETS = [1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# Tick size & rounding (mirrors vn-position-sizer)
# ---------------------------------------------------------------------------


def tick_size_hose(price: float) -> int:
    if price < 10_000:
        return 10
    if price < 50_000:
        return 50
    return 100


def tick_size(exchange: str, price: float) -> int:
    if exchange == "hose":
        return tick_size_hose(price)
    return 100


def round_to_tick(price: float, exchange: str, mode: str = "nearest") -> int:
    tick = tick_size(exchange, price)
    if mode == "down":
        return int(price // tick * tick)
    if mode == "up":
        return int(-(-price // tick) * tick)
    return int(round(price / tick) * tick)


def round_to_lot(raw_shares: int, lot_size: int = LOT_SIZE) -> int:
    return (raw_shares // lot_size) * lot_size


def compute_price_band(reference_price: float, exchange: str) -> dict:
    pct = PRICE_BAND_PCT.get(exchange, 7.0)
    raw_ceiling = reference_price * (1 + pct / 100)
    raw_floor = reference_price * (1 - pct / 100)
    return {
        "reference_price": int(reference_price),
        "ceiling_price": round_to_tick(raw_ceiling, exchange, mode="down"),
        "floor_price": round_to_tick(raw_floor, exchange, mode="up"),
        "price_band_pct": pct,
    }


# ---------------------------------------------------------------------------
# Sizing & fees
# ---------------------------------------------------------------------------


def compute_sizing(
    account_size_vnd: float,
    pivot: float,
    stop: float,
    risk_pct: float,
    lot_size: int = LOT_SIZE,
) -> dict:
    if pivot <= 0 or stop <= 0:
        raise ValueError("pivot và stop phải dương")
    if stop >= pivot:
        raise ValueError("stop phải thấp hơn pivot cho lệnh long")
    if risk_pct <= 0:
        raise ValueError("risk_pct phải dương")

    risk_per_share = pivot - stop
    target_risk_vnd = account_size_vnd * risk_pct / 100
    raw_shares = int(target_risk_vnd / risk_per_share)
    shares = round_to_lot(raw_shares, lot_size)
    return {
        "raw_shares": raw_shares,
        "shares": shares,
        "risk_per_share_vnd": round(risk_per_share),
        "target_dollar_risk_vnd": round(target_risk_vnd),
        "position_value_vnd": round(shares * pivot),
        "actual_risk_vnd": round(shares * risk_per_share),
        "actual_risk_pct": round(
            shares * risk_per_share / account_size_vnd * 100, 3
        ),
    }


def estimate_fees(
    shares: int,
    pivot: float,
    broker_fee_pct: float,
    sale_tax_pct: float,
) -> dict:
    value = shares * pivot
    buy_fee = value * broker_fee_pct / 100
    sell_fee = value * broker_fee_pct / 100
    sell_tax = value * sale_tax_pct / 100
    total = buy_fee + sell_fee + sell_tax
    pct = total / value * 100 if value > 0 else 0
    return {
        "buy_fee_vnd": round(buy_fee),
        "sell_fee_vnd_at_pivot": round(sell_fee),
        "sell_tax_vnd_at_pivot": round(sell_tax),
        "round_trip_cost_vnd": round(total),
        "round_trip_cost_pct": round(pct, 3),
    }


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def compute_targets(
    pivot: float, stop: float, r_multiples: list[float], exchange: str
) -> list[dict]:
    risk_per_share = pivot - stop
    n = len(r_multiples)
    # Distribute fractions: roughly equal, last absorbs remainder so they sum to 1.0
    fractions = [round(1.0 / n, 2)] * (n - 1) + [round(1.0 - (n - 1) * round(1.0 / n, 2), 2)]
    targets = []
    for r, frac in zip(r_multiples, fractions):
        raw_price = pivot + risk_per_share * r
        price = round_to_tick(raw_price, exchange, mode="nearest")
        targets.append(
            {
                "name": f"T{len(targets)+1} ({r}R)",
                "r_multiple": r,
                "price": price,
                "size_fraction": frac,
            }
        )
    return targets


# ---------------------------------------------------------------------------
# T+ calendar
# ---------------------------------------------------------------------------


def t_plus_calendar(buy_date_str: str | None = None) -> dict:
    """Compute the T+2.5 sellable date label.

    If buy_date_str provided, calculate explicit dates (skipping weekends).
    Otherwise return relative labels.
    """
    notes = [
        "Không thể bán intraday vào D0",
        "D+1 và sáng D+2: CP chưa về tài khoản; chỉ có thể đặt lệnh chờ",
        "Stop intraday hiệu lực bằng cảnh báo, không phải lệnh tự động",
        "Stop thực hiện sớm nhất là chiều D+2 sau khi CP về tài khoản",
    ]

    if buy_date_str:
        try:
            d0 = datetime.strptime(buy_date_str, "%Y-%m-%d")
            d_plus_2 = add_business_days(d0, 2)
            return {
                "buy_date_label": f"D0 = {d0.strftime('%Y-%m-%d')}",
                "stock_in_account_label": f"{d_plus_2.strftime('%Y-%m-%d')} chiều (T+2 PM)",
                "first_sellable_label": f"{d_plus_2.strftime('%Y-%m-%d')} chiều",
                "notes": notes,
            }
        except ValueError:
            pass

    return {
        "buy_date_label": "D0 (ngày mua)",
        "stock_in_account_label": "D+2 chiều",
        "first_sellable_label": "D+2 chiều",
        "notes": notes,
    }


def add_business_days(start: datetime, n: int) -> datetime:
    """Add n business days (Mon-Fri) to start. Doesn't account for VN holidays."""
    d = start
    added = 0
    while added < n:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


# ---------------------------------------------------------------------------
# Context: sector + foreign room
# ---------------------------------------------------------------------------


def load_sector_context(path: str, symbol: str) -> dict | None:
    """Load vn-sector-analyst JSON; return context for this symbol's sector."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    # Find which sector this symbol belongs to by scanning top_3/bottom_3 lists
    # (sector mapping is also in vn-sector-analyst, but we can derive from output)
    for sec in data.get("sectors", []):
        members = [r["symbol"] for r in sec.get("top_3_by_20D", [])]
        members += [r["symbol"] for r in sec.get("bottom_3_by_20D", [])]
        if symbol in members:
            rs_20d = sec["relative_strength"].get("20D")
            # Determine status
            status = "stable"
            if rs_20d is not None:
                if rs_20d > 1.0:
                    status = "leader"
                elif rs_20d < -1.0:
                    status = "laggard"
            return {
                "name": sec["name"],
                "status": status,
                "rs_20d": rs_20d,
                "trend_signal": sec.get("trend_signal"),
            }
    return None


def load_foreign_room_context(path: str, symbol: str) -> dict | None:
    """Load vn-foreign-room-tracker JSON; return context for symbol."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    for row in data.get("rows", []):
        if row.get("symbol") == symbol:
            return {
                "status": row.get("status"),
                "room_used_pct": row.get("room_used_pct"),
                "change_pct": row.get("change_pct"),
            }
    return None


# ---------------------------------------------------------------------------
# Plan assembly
# ---------------------------------------------------------------------------


def assemble_plan(args: argparse.Namespace) -> dict:
    exchange = args.exchange.lower()
    symbol = args.symbol.upper()

    # Determine stop
    if args.stop is None and args.atr is None:
        raise ValueError("Cần --stop hoặc --atr để tính stop")

    if args.stop is None:
        stop_distance = args.atr * args.atr_multiplier
        stop_raw = args.pivot - stop_distance
        stop = round_to_tick(stop_raw, exchange, mode="down")
    else:
        stop = args.stop

    if stop >= args.pivot:
        raise ValueError("Stop phải thấp hơn pivot")

    # Sizing
    sizing = compute_sizing(
        args.account_size_vnd, args.pivot, stop, args.risk_pct
    )

    if sizing["shares"] == 0:
        raise ValueError(
            "Risk per share quá lớn so với budget — không đủ tiền cho 1 lô. "
            "Giảm --risk-pct hoặc nới stop."
        )

    # VN market context (band)
    ref = args.reference_price or args.pivot
    band = compute_price_band(ref, exchange)
    pivot_below_ceiling = args.pivot <= band["ceiling_price"]
    stop_above_floor = stop >= band["floor_price"]
    pivot_above_ref_pct = round((args.pivot - ref) / ref * 100, 3) if ref > 0 else 0

    # Targets
    r_multiples = [float(x.strip()) for x in args.targets.split(",")]
    targets = compute_targets(args.pivot, stop, r_multiples, exchange)

    # Fees
    fees = estimate_fees(
        sizing["shares"], args.pivot, args.broker_fee_pct, args.sale_tax_pct
    )

    # T+
    tcal = t_plus_calendar(args.buy_date)

    # Warnings
    warnings = []
    if not pivot_below_ceiling:
        warnings.append(
            f"Pivot ({args.pivot:,}) nằm trên/bằng giá trần "
            f"({band['ceiling_price']:,}) — lệnh mua không khớp trong phiên."
        )
    if not stop_above_floor:
        warnings.append(
            f"Stop ({stop:,}) thấp hơn giá sàn ({band['floor_price']:,}) — "
            f"biên độ sẽ chặn lệnh cắt lỗ trong phiên đầu."
        )
    if pivot_above_ref_pct > PRICE_BAND_PCT.get(exchange, 7.0) * 0.5:
        warnings.append(
            f"Pivot cao hơn reference {pivot_above_ref_pct}% — "
            f"setup có thể đã muộn (giá đã chạy quá xa)."
        )
    if sizing["actual_risk_pct"] > args.risk_pct * 1.05:
        # Lot rounding shouldn't blow up risk; sanity check
        warnings.append(
            f"Risk thực tế ({sizing['actual_risk_pct']}%) vượt target."
        )

    # Context
    context: dict = {}
    if args.sector_analysis_file:
        sec_ctx = load_sector_context(args.sector_analysis_file, symbol)
        if sec_ctx:
            context["sector"] = sec_ctx
    if args.foreign_room_file:
        room_ctx = load_foreign_room_context(args.foreign_room_file, symbol)
        if room_ctx:
            context["foreign_room"] = room_ctx

    return {
        "schema_version": "1.0",
        "subcommand": "plan",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "symbol": symbol,
        "exchange": exchange,
        "setup_type": args.setup_type,
        "trade_plan": {
            "pivot": args.pivot,
            "stop": stop,
            "risk_per_share_vnd": sizing["risk_per_share_vnd"],
            "shares": sizing["shares"],
            "position_value_vnd": sizing["position_value_vnd"],
            "risk_vnd": sizing["actual_risk_vnd"],
            "risk_pct": sizing["actual_risk_pct"],
            "targets": targets,
        },
        "vn_market_context": {
            **band,
            "pivot_below_ceiling": pivot_below_ceiling,
            "stop_above_floor": stop_above_floor,
            "pivot_above_reference_pct": pivot_above_ref_pct,
        },
        "fees_and_taxes_estimate": fees,
        "t_plus_calendar": tcal,
        "context": context,
        "warnings": warnings,
        "checklist": [
            "Đã ghi thesis vào journal trước khi đặt lệnh",
            "Stop nằm trên giá sàn phiên đầu",
            "Vị thế ≤ 10% account",
            "Ngành ≤ 30% account",
            "Tổng portfolio heat (open risk) ≤ 6-8%",
            "Có plan partial exit tại các target R",
            "Hiểu T+2.5 nghĩa là không exit intraday được trong 2 phiên đầu",
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lập kế hoạch breakout long cho cổ phiếu Việt Nam"
    )
    parser.add_argument(
        "--account-size",
        type=float,
        required=True,
        dest="account_size_vnd",
        help="Quy mô tài khoản (VND)",
    )
    parser.add_argument("--symbol", required=True, help="Mã CP (ví dụ VIC)")
    parser.add_argument(
        "--exchange", default="hose", choices=["hose", "hnx", "upcom"]
    )
    parser.add_argument(
        "--setup-type",
        default="breakout",
        choices=["breakout", "pullback", "vcp"],
    )
    parser.add_argument("--pivot", type=float, required=True, help="Giá entry/breakout (VND)")
    parser.add_argument("--stop", type=float, help="Giá stop (VND)")
    parser.add_argument("--atr", type=float, help="ATR (VND) để tính stop nếu không có --stop")
    parser.add_argument("--atr-multiplier", type=float, default=2.0)
    parser.add_argument(
        "--reference-price",
        type=float,
        help="Giá tham chiếu cho biên độ (mặc định = pivot)",
    )
    parser.add_argument("--risk-pct", type=float, default=1.0, help="% rủi ro (mặc định 1.0)")
    parser.add_argument(
        "--targets",
        default="1,2,3",
        help="R-multiples cho targets (CSV, mặc định '1,2,3')",
    )
    parser.add_argument(
        "--broker-fee-pct",
        type=float,
        default=DEFAULT_BROKER_FEE_PCT,
    )
    parser.add_argument(
        "--sale-tax-pct",
        type=float,
        default=DEFAULT_SALE_TAX_PCT,
    )
    parser.add_argument(
        "--buy-date",
        help="Ngày mua dự kiến YYYY-MM-DD (để tính T+2.5 calendar)",
    )
    parser.add_argument(
        "--sector-analysis-file",
        help="JSON output của vn-sector-analyst để lấy ngữ cảnh ngành",
    )
    parser.add_argument(
        "--foreign-room-file",
        help="JSON output của vn-foreign-room-tracker để lấy ngữ cảnh room",
    )
    parser.add_argument("--output-dir", default="reports/")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        plan = assemble_plan(args)
    except ValueError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_breakout_plan_{plan['symbol']}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")

    # Stdout summary
    tp = plan["trade_plan"]
    vm = plan["vn_market_context"]
    print(f"\n=== {plan['symbol']} ({plan['exchange'].upper()}) — {plan['setup_type']} ===")
    print(f"Pivot:        {tp['pivot']:>12,} VND")
    print(f"Stop:         {tp['stop']:>12,} VND  (risk/share {tp['risk_per_share_vnd']:,})")
    print(f"Shares:       {tp['shares']:>12,} CP")
    print(f"Position:     {tp['position_value_vnd']:>12,} VND")
    print(f"Risk:         {tp['risk_vnd']:>12,} VND  ({tp['risk_pct']}%)")
    print(f"Trần / Sàn:   {vm['ceiling_price']:,} / {vm['floor_price']:,} ({vm['price_band_pct']}%)")
    print("\nTargets:")
    for t in tp["targets"]:
        print(f"  {t['name']:>10s}: {t['price']:>10,} VND ({t['size_fraction']*100:.0f}% size)")

    print(f"\nT+2.5: {plan['t_plus_calendar']['first_sellable_label']}")
    print(f"Round-trip cost: {plan['fees_and_taxes_estimate']['round_trip_cost_pct']}%")

    if plan["context"]:
        print("\nContext:")
        if "sector" in plan["context"]:
            sc = plan["context"]["sector"]
            print(f"  Sector {sc['name']}: {sc['status']} (RS_20D {sc.get('rs_20d')})")
        if "foreign_room" in plan["context"]:
            fr = plan["context"]["foreign_room"]
            print(f"  Foreign room: {fr['status']} ({fr.get('room_used_pct')}% used)")

    if plan["warnings"]:
        print("\nCảnh báo:")
        for w in plan["warnings"]:
            print(f"  ⚠️  {w}")


if __name__ == "__main__":
    main()
