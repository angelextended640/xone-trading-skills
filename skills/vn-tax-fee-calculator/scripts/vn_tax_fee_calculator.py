"""VN Tax & Fee Calculator — chi phí giao dịch cổ phiếu Việt Nam.

Subcommands:
  trade     — Total round-trip cost (buy + sell fee + sale tax) for one trade
  compare   — Compare net P&L across brokers for the same trade
  dividend  — Cash / stock dividend tax
  monthly   — Custody fee + advance-cash-sale fee per month

Fee defaults from references/broker_fee_profiles.json. Override via CLI flags.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))

PROFILES_PATH = Path(__file__).resolve().parent.parent / "references" / "broker_fee_profiles.json"


# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------


def load_profiles(path: Path = PROFILES_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_broker(profiles: dict, broker_key: str) -> dict:
    """Return the broker profile dict, raising ValueError if not found."""
    brokers = profiles["brokers"]
    key = broker_key.lower()
    if key not in brokers:
        available = ", ".join(sorted(brokers.keys()))
        raise ValueError(f"Unknown broker '{broker_key}'. Available: {available}")
    return brokers[key]


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------


def compute_trade_costs(
    shares: int,
    entry: float,
    exit_price: float,
    broker_fee_pct: float,
    sale_tax_pct: float,
) -> dict:
    """Compute total cost of one round-trip (buy + sell)."""
    if shares <= 0:
        raise ValueError("shares phải dương")
    if entry <= 0 or exit_price <= 0:
        raise ValueError("entry và exit phải dương")
    if broker_fee_pct < 0 or sale_tax_pct < 0:
        raise ValueError("phí và thuế không được âm")

    entry_value = shares * entry
    exit_value = shares * exit_price
    buy_fee = entry_value * broker_fee_pct / 100
    sell_fee = exit_value * broker_fee_pct / 100
    sell_tax = exit_value * sale_tax_pct / 100
    total_cost = buy_fee + sell_fee + sell_tax

    gross_pnl = exit_value - entry_value
    net_pnl = gross_pnl - total_cost
    net_pnl_pct = net_pnl / entry_value * 100 if entry_value > 0 else 0

    # Break-even: exit price such that net_pnl == 0
    # entry_value * (1 + broker_fee_pct/100) ≤ exit_value * (1 - broker_fee_pct/100 - sale_tax_pct/100)
    # → exit_value_min = entry_value * (1 + bf/100) / (1 - bf/100 - st/100)
    sell_side_keep = 1 - (broker_fee_pct + sale_tax_pct) / 100
    if sell_side_keep <= 0:
        raise ValueError("phí + thuế bán >= 100% — không có break-even")
    exit_value_min = entry_value * (1 + broker_fee_pct / 100) / sell_side_keep
    exit_price_min = exit_value_min / shares
    pct_to_breakeven = (exit_price_min - entry) / entry * 100

    return {
        "inputs": {
            "shares": shares,
            "entry_price": entry,
            "exit_price": exit_price,
            "broker_fee_pct": broker_fee_pct,
            "sale_tax_pct": sale_tax_pct,
        },
        "costs": {
            "entry_value_vnd": round(entry_value),
            "exit_value_vnd": round(exit_value),
            "buy_fee_vnd": round(buy_fee),
            "sell_fee_vnd": round(sell_fee),
            "sell_tax_vnd": round(sell_tax),
            "total_cost_vnd": round(total_cost),
            "total_cost_pct_of_entry": (
                round(total_cost / entry_value * 100, 3) if entry_value > 0 else 0
            ),
        },
        "pnl": {
            "gross_pnl_vnd": round(gross_pnl),
            "net_pnl_vnd": round(net_pnl),
            "net_pnl_pct": round(net_pnl_pct, 3),
            "pct_eaten_by_costs": (
                round(total_cost / abs(gross_pnl) * 100, 2)
                if abs(gross_pnl) > 0
                else None
            ),
        },
        "breakeven": {
            "min_exit_price_to_breakeven": round(exit_price_min, 2),
            "min_pct_gain_to_breakeven": round(pct_to_breakeven, 3),
        },
    }


def compute_dividend_tax(
    shares: int,
    dividend_per_share: float,
    is_stock_dividend: bool,
    profiles: dict,
) -> dict:
    """Compute dividend tax — cash or stock dividend."""
    if shares <= 0:
        raise ValueError("shares phải dương")
    if dividend_per_share <= 0:
        raise ValueError("dividend_per_share phải dương")

    global_cfg = profiles["global"]
    if is_stock_dividend:
        tax_rate_pct = global_cfg["stock_dividend_tax_pct"]
        par_value = global_cfg["stock_dividend_par_value_vnd"]
        # Stock dividend: ratio = dividend_per_share = how many new shares per 1 old share's worth
        # Tax base = par value × shares received
        # For simplicity, dividend_per_share here represents shares received per original share
        shares_received = shares * dividend_per_share
        gross_value = shares_received * par_value
        tax = gross_value * tax_rate_pct / 100
        return {
            "dividend_type": "stock",
            "shares_held": shares,
            "shares_received": shares_received,
            "par_value_vnd": par_value,
            "gross_dividend_vnd": round(gross_value),
            "tax_rate_pct": tax_rate_pct,
            "tax_vnd": round(tax),
            "net_value_vnd": round(gross_value - tax),
            "note": "Stock dividend tax is collected when you sell the received shares.",
        }
    else:
        tax_rate_pct = global_cfg["cash_dividend_tax_pct"]
        gross = shares * dividend_per_share
        tax = gross * tax_rate_pct / 100
        return {
            "dividend_type": "cash",
            "shares": shares,
            "dividend_per_share_vnd": dividend_per_share,
            "gross_dividend_vnd": round(gross),
            "tax_rate_pct": tax_rate_pct,
            "tax_vnd": round(tax),
            "net_dividend_vnd": round(gross - tax),
        }


def compute_monthly_overhead(
    total_shares: int,
    advance_cash_vnd: float,
    advance_days: int,
    profiles: dict,
    advance_fee_pct_per_day: float | None = None,
) -> dict:
    """Estimate monthly custody + (optional) advance-cash-sale overhead."""
    if total_shares < 0 or advance_cash_vnd < 0 or advance_days < 0:
        raise ValueError("Các giá trị không được âm")

    global_cfg = profiles["global"]
    custody_per_share = global_cfg["custody_fee_per_share_per_month_vnd"]
    custody_fee = total_shares * custody_per_share

    advance_pct = (
        advance_fee_pct_per_day
        if advance_fee_pct_per_day is not None
        else global_cfg["advance_cash_fee_pct_per_day_default"]
    )
    advance_fee = advance_cash_vnd * advance_pct / 100 * advance_days

    return {
        "custody_fee_per_share_vnd": custody_per_share,
        "total_shares_held": total_shares,
        "custody_fee_monthly_vnd": round(custody_fee),
        "advance_cash_vnd": round(advance_cash_vnd),
        "advance_days": advance_days,
        "advance_fee_pct_per_day": advance_pct,
        "advance_fee_vnd": round(advance_fee),
        "total_monthly_overhead_vnd": round(custody_fee + advance_fee),
    }


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def run_trade(args: argparse.Namespace) -> dict:
    profiles = load_profiles()

    if args.custom_broker:
        if args.custom_fee_pct is None:
            raise ValueError("--custom-broker yêu cầu --custom-fee-pct")
        broker_name = args.custom_broker
        fee_pct = args.custom_fee_pct
    else:
        broker_key = args.broker or "vps"
        prof = resolve_broker(profiles, broker_key)
        broker_name = prof["display_name"]
        fee_pct = args.custom_fee_pct if args.custom_fee_pct is not None else prof["fee_pct"]

    sale_tax_pct = (
        args.sale_tax_pct
        if args.sale_tax_pct is not None
        else profiles["global"]["sale_tax_pct"]
    )

    result = compute_trade_costs(args.shares, args.entry, args.exit, fee_pct, sale_tax_pct)
    return {
        "schema_version": "1.0",
        "subcommand": "trade",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "broker": broker_name,
        **result,
    }


def run_compare(args: argparse.Namespace) -> dict:
    profiles = load_profiles()

    if args.brokers:
        broker_keys = [k.strip().lower() for k in args.brokers.split(",")]
    else:
        broker_keys = sorted(profiles["brokers"].keys())

    sale_tax_pct = (
        args.sale_tax_pct
        if args.sale_tax_pct is not None
        else profiles["global"]["sale_tax_pct"]
    )

    rows = []
    for key in broker_keys:
        prof = resolve_broker(profiles, key)
        calc = compute_trade_costs(args.shares, args.entry, args.exit, prof["fee_pct"], sale_tax_pct)
        rows.append(
            {
                "broker": prof["display_name"],
                "fee_pct": prof["fee_pct"],
                "total_cost_vnd": calc["costs"]["total_cost_vnd"],
                "net_pnl_vnd": calc["pnl"]["net_pnl_vnd"],
                "net_pnl_pct": calc["pnl"]["net_pnl_pct"],
                "min_pct_to_breakeven": calc["breakeven"]["min_pct_gain_to_breakeven"],
            }
        )

    # Sort by net_pnl desc (best first)
    rows.sort(key=lambda r: -r["net_pnl_vnd"])

    return {
        "schema_version": "1.0",
        "subcommand": "compare",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "inputs": {
            "shares": args.shares,
            "entry_price": args.entry,
            "exit_price": args.exit,
            "sale_tax_pct": sale_tax_pct,
        },
        "rows": rows,
        "best_broker": rows[0]["broker"] if rows else None,
        "worst_broker": rows[-1]["broker"] if rows else None,
        "spread_vnd": (
            rows[0]["net_pnl_vnd"] - rows[-1]["net_pnl_vnd"] if len(rows) >= 2 else 0
        ),
    }


def run_dividend(args: argparse.Namespace) -> dict:
    profiles = load_profiles()
    result = compute_dividend_tax(
        args.shares, args.dividend_per_share, args.stock, profiles
    )
    return {
        "schema_version": "1.0",
        "subcommand": "dividend",
        "as_of": datetime.now(VN_TZ).isoformat(),
        **result,
    }


def run_monthly(args: argparse.Namespace) -> dict:
    profiles = load_profiles()
    result = compute_monthly_overhead(
        args.total_shares,
        args.advance_cash_vnd or 0,
        args.advance_days or 0,
        profiles,
        advance_fee_pct_per_day=args.advance_fee_pct,
    )
    return {
        "schema_version": "1.0",
        "subcommand": "monthly",
        "as_of": datetime.now(VN_TZ).isoformat(),
        **result,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        default="reports/",
        help="Thư mục báo cáo (mặc định reports/)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tính phí + thuế giao dịch CK Việt Nam"
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # trade
    p_trade = sub.add_parser("trade", help="Tổng phí + thuế cho 1 trade round-trip")
    p_trade.add_argument("--shares", type=int, required=True)
    p_trade.add_argument("--entry", type=float, required=True, help="Giá entry (VND)")
    p_trade.add_argument("--exit", type=float, required=True, help="Giá exit (VND)")
    p_trade.add_argument(
        "--broker",
        help="CTCK (vps/ssi/vndirect/hsc/mbs/tcbs/dnse/vci/abs/kbsv)",
    )
    p_trade.add_argument("--custom-broker", help="Tên CTCK tuỳ chỉnh")
    p_trade.add_argument(
        "--custom-fee-pct",
        type=float,
        help="Phí broker tuỳ chỉnh (%), override mặc định",
    )
    p_trade.add_argument(
        "--sale-tax-pct",
        type=float,
        help="Thuế bán % (mặc định 0.1)",
    )
    add_common_args(p_trade)

    # compare
    p_cmp = sub.add_parser("compare", help="So sánh net P&L giữa các CTCK")
    p_cmp.add_argument("--shares", type=int, required=True)
    p_cmp.add_argument("--entry", type=float, required=True)
    p_cmp.add_argument("--exit", type=float, required=True)
    p_cmp.add_argument(
        "--brokers",
        help="Danh sách CTCK (CSV). Bỏ trống = so sánh tất cả built-in.",
    )
    p_cmp.add_argument("--sale-tax-pct", type=float)
    add_common_args(p_cmp)

    # dividend
    p_div = sub.add_parser("dividend", help="Tính thuế cổ tức")
    p_div.add_argument("--shares", type=int, required=True)
    p_div.add_argument(
        "--dividend-per-share",
        type=float,
        required=True,
        help="VND/CP (cash) hoặc tỷ lệ (stock, ví dụ 0.05 = 5%%)",
    )
    p_div.add_argument(
        "--stock",
        action="store_true",
        help="Cổ tức bằng cổ phiếu (mặc định: cash)",
    )
    add_common_args(p_div)

    # monthly
    p_mon = sub.add_parser("monthly", help="Phí lưu ký + ứng trước hàng tháng")
    p_mon.add_argument(
        "--total-shares",
        type=int,
        required=True,
        help="Tổng CP đang nắm",
    )
    p_mon.add_argument(
        "--advance-cash-vnd",
        type=float,
        help="Số tiền ứng trước (VND)",
    )
    p_mon.add_argument(
        "--advance-days",
        type=int,
        help="Số ngày ứng trước",
    )
    p_mon.add_argument(
        "--advance-fee-pct",
        type=float,
        help="%%/ngày phí ứng trước (mặc định 0.04)",
    )
    add_common_args(p_mon)

    return parser


def format_vnd(x: float | int | None) -> str:
    if x is None:
        return "n/a"
    return f"{int(x):,} VND"


def print_summary(result: dict) -> None:
    sub = result["subcommand"]
    print()
    if sub == "trade":
        print(f"=== Trade Cost — {result['broker']} ===")
        c = result["costs"]
        p = result["pnl"]
        b = result["breakeven"]
        print(f"Entry value : {format_vnd(c['entry_value_vnd'])}")
        print(f"Exit value  : {format_vnd(c['exit_value_vnd'])}")
        print(f"Buy fee     : {format_vnd(c['buy_fee_vnd'])}")
        print(f"Sell fee    : {format_vnd(c['sell_fee_vnd'])}")
        print(f"Sell tax    : {format_vnd(c['sell_tax_vnd'])}")
        print(f"Total cost  : {format_vnd(c['total_cost_vnd'])} ({c['total_cost_pct_of_entry']}%)")
        print(f"Gross P&L   : {format_vnd(p['gross_pnl_vnd'])}")
        print(f"Net P&L     : {format_vnd(p['net_pnl_vnd'])} ({p['net_pnl_pct']}%)")
        if p.get("pct_eaten_by_costs") is not None:
            print(f"Cost eats   : {p['pct_eaten_by_costs']}% of gross P&L")
        print(
            f"Break-even  : {format_vnd(int(b['min_exit_price_to_breakeven']))} "
            f"({b['min_pct_gain_to_breakeven']:+.3f}%)"
        )
    elif sub == "compare":
        i = result["inputs"]
        print(
            f"=== Compare ({i['shares']:,} CP, entry {format_vnd(i['entry_price'])}, "
            f"exit {format_vnd(i['exit_price'])}) ==="
        )
        print(f"{'Broker':<14s} {'Fee%':>6s} {'Cost':>15s} {'Net P&L':>17s} {'Net%':>8s} {'BE%':>8s}")
        for r in result["rows"]:
            print(
                f"{r['broker']:<14s} {r['fee_pct']:>5.3f}% "
                f"{format_vnd(r['total_cost_vnd']):>15s} "
                f"{format_vnd(r['net_pnl_vnd']):>17s} "
                f"{r['net_pnl_pct']:>7.3f}% "
                f"{r['min_pct_to_breakeven']:>7.3f}%"
            )
        print(
            f"\nBest: {result['best_broker']}, worst: {result['worst_broker']}, "
            f"spread: {format_vnd(result['spread_vnd'])}"
        )
    elif sub == "dividend":
        print("=== Dividend Tax ===")
        if result["dividend_type"] == "cash":
            print(f"Shares: {result['shares']:,}")
            print(f"Dividend per share: {format_vnd(result['dividend_per_share_vnd'])}")
            print(f"Gross : {format_vnd(result['gross_dividend_vnd'])}")
            print(f"Tax ({result['tax_rate_pct']}%): {format_vnd(result['tax_vnd'])}")
            print(f"Net   : {format_vnd(result['net_dividend_vnd'])}")
        else:
            print(f"Shares held: {result['shares_held']:,}")
            print(f"Shares received: {result['shares_received']:,.2f}")
            print(f"Par value: {format_vnd(result['par_value_vnd'])}/CP")
            print(f"Gross value: {format_vnd(result['gross_dividend_vnd'])}")
            print(f"Tax ({result['tax_rate_pct']}%): {format_vnd(result['tax_vnd'])}")
            print(f"Net value : {format_vnd(result['net_value_vnd'])}")
            print(f"\nNote: {result['note']}")
    elif sub == "monthly":
        print("=== Monthly Overhead ===")
        print(
            f"Custody : {result['total_shares_held']:,} CP × "
            f"{result['custody_fee_per_share_vnd']} VND = "
            f"{format_vnd(result['custody_fee_monthly_vnd'])}/month"
        )
        if result["advance_cash_vnd"] > 0:
            print(
                f"Advance : {format_vnd(result['advance_cash_vnd'])} × "
                f"{result['advance_fee_pct_per_day']}%/ngày × {result['advance_days']} ngày = "
                f"{format_vnd(result['advance_fee_vnd'])}"
            )
        print(f"Total   : {format_vnd(result['total_monthly_overhead_vnd'])}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.subcommand == "trade":
            result = run_trade(args)
        elif args.subcommand == "compare":
            result = run_compare(args)
        elif args.subcommand == "dividend":
            result = run_dividend(args)
        elif args.subcommand == "monthly":
            result = run_monthly(args)
        else:
            parser.error(f"Unknown subcommand: {args.subcommand}")
            return
    except (ValueError, FileNotFoundError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_tax_fee_{args.subcommand}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")
    print_summary(result)


if __name__ == "__main__":
    main()
