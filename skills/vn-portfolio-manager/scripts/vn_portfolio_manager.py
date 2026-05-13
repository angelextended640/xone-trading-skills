"""VN Portfolio Manager — quản lý danh mục cổ phiếu Việt Nam (VND).

Manual entry of buy/sell trades; state stored as CSV under state/vn_portfolio/.
Computes P&L after broker fees (default 0.15% per side) and sale tax (0.1%).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

VN_TZ = timezone(timedelta(hours=7))

# Defaults from vn-market-mechanics/references/vn_fees_and_taxes.md
DEFAULT_BROKER_FEE_PCT = 0.15
DEFAULT_SALE_TAX_PCT = 0.10

HOLDINGS_FIELDS = [
    "symbol",
    "exchange",
    "shares",
    "avg_price",
    "buy_date",
    "sector",
    "notes",
]

CLOSED_FIELDS = [
    "symbol",
    "exchange",
    "shares",
    "avg_buy_price",
    "buy_date",
    "close_price",
    "close_date",
    "sector",
    "gross_pnl_vnd",
    "fees_vnd",
    "tax_vnd",
    "net_pnl_vnd",
    "net_pnl_pct",
    "hold_days",
]


@dataclass
class Holding:
    symbol: str
    exchange: str
    shares: int
    avg_price: float
    buy_date: str
    sector: str
    notes: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "Holding":
        return cls(
            symbol=row["symbol"].upper(),
            exchange=row.get("exchange", "hose").lower(),
            shares=int(row["shares"]),
            avg_price=float(row["avg_price"]),
            buy_date=row.get("buy_date", ""),
            sector=row.get("sector", ""),
            notes=row.get("notes", ""),
        )

    def to_row(self) -> dict:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "shares": self.shares,
            "avg_price": self.avg_price,
            "buy_date": self.buy_date,
            "sector": self.sector,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# CSV state I/O
# ---------------------------------------------------------------------------


def holdings_path(state_dir: Path) -> Path:
    return state_dir / "holdings.csv"


def closed_path(state_dir: Path) -> Path:
    return state_dir / "closed.csv"


def load_holdings(state_dir: Path) -> list[Holding]:
    p = holdings_path(state_dir)
    if not p.exists():
        return []
    out: list[Holding] = []
    with open(p, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(Holding.from_row(row))
    return out


def save_holdings(state_dir: Path, holdings: list[Holding]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    p = holdings_path(state_dir)
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HOLDINGS_FIELDS)
        writer.writeheader()
        for h in holdings:
            writer.writerow(h.to_row())


def append_closed(state_dir: Path, record: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    p = closed_path(state_dir)
    write_header = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLOSED_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(record)


def load_closed(state_dir: Path) -> list[dict]:
    p = closed_path(state_dir)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Fee & tax calculations
# ---------------------------------------------------------------------------


def buy_fee(value: float, broker_fee_pct: float = DEFAULT_BROKER_FEE_PCT) -> float:
    return value * broker_fee_pct / 100


def sell_fee_and_tax(
    value: float,
    broker_fee_pct: float = DEFAULT_BROKER_FEE_PCT,
    sale_tax_pct: float = DEFAULT_SALE_TAX_PCT,
) -> tuple[float, float]:
    return value * broker_fee_pct / 100, value * sale_tax_pct / 100


def net_pnl(
    shares: int,
    buy_price: float,
    sell_price: float,
    broker_fee_pct: float = DEFAULT_BROKER_FEE_PCT,
    sale_tax_pct: float = DEFAULT_SALE_TAX_PCT,
) -> dict:
    cost = shares * buy_price
    proceeds = shares * sell_price
    gross = proceeds - cost
    fee_buy = buy_fee(cost, broker_fee_pct)
    fee_sell, tax_sell = sell_fee_and_tax(proceeds, broker_fee_pct, sale_tax_pct)
    fees = fee_buy + fee_sell
    net = gross - fees - tax_sell
    return {
        "gross_pnl_vnd": round(gross),
        "fees_vnd": round(fees),
        "tax_vnd": round(tax_sell),
        "net_pnl_vnd": round(net),
        "net_pnl_pct": round(net / cost * 100, 3) if cost > 0 else 0,
    }


# ---------------------------------------------------------------------------
# Price loading
# ---------------------------------------------------------------------------


def parse_prices_cli(spec: str) -> dict[str, float]:
    """Parse 'VIC:46500,HPG:28500' → {'VIC': 46500.0, 'HPG': 28500.0}."""
    out = {}
    for pair in spec.split(","):
        if ":" not in pair:
            raise ValueError(f"Sai format giá '{pair}', cần SYMBOL:PRICE")
        sym, price = pair.split(":", 1)
        out[sym.strip().upper()] = float(price)
    return out


def load_prices_file(path: str) -> dict[str, float]:
    """Load prices from JSON file. Supports two shapes:

    1. Flat: {"VIC": 46500, "HPG": 28500}
    2. Nested (vn-data-fetcher output): {"data": [{"time": ..., "close": ..., ...}], ...}
       — uses last 'close' as current price for symbol named in 'symbol'.
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("File giá phải là JSON dict")

    # Case 1: flat {"VIC": 46500, ...}
    if all(isinstance(v, (int, float)) for v in raw.values()):
        return {k.upper(): float(v) for k, v in raw.items()}

    # Case 2: vn-data-fetcher single-symbol shape
    if "symbol" in raw and "data" in raw and isinstance(raw["data"], list):
        rows = raw["data"]
        if rows:
            return {raw["symbol"].upper(): float(rows[-1]["close"])}

    # Case 3: vn-data-fetcher multi-symbol shape
    if "symbols" in raw and "data" in raw and isinstance(raw["data"], dict):
        out = {}
        for sym, rows in raw["data"].items():
            if rows:
                out[sym.upper()] = float(rows[-1]["close"])
        return out

    raise ValueError("Không nhận dạng được format file giá")


def resolve_prices(args: argparse.Namespace) -> dict[str, float]:
    if args.prices_file:
        return load_prices_file(args.prices_file)
    if args.prices:
        return parse_prices_cli(args.prices)
    return {}


# ---------------------------------------------------------------------------
# Subcommand: add
# ---------------------------------------------------------------------------


def run_add(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    holdings = load_holdings(state_dir)

    sym = args.symbol.upper()
    # If already exists, average down/up
    existing_idx = next(
        (i for i, h in enumerate(holdings) if h.symbol == sym), None
    )
    if existing_idx is not None:
        old = holdings[existing_idx]
        total_shares = old.shares + args.shares
        new_avg = (
            old.shares * old.avg_price + args.shares * args.avg_price
        ) / total_shares
        holdings[existing_idx] = Holding(
            symbol=sym,
            exchange=old.exchange,
            shares=total_shares,
            avg_price=round(new_avg, 2),
            buy_date=old.buy_date,  # keep original entry date
            sector=old.sector,
            notes=args.notes or old.notes,
        )
        action = "averaged"
    else:
        holdings.append(
            Holding(
                symbol=sym,
                exchange=args.exchange,
                shares=args.shares,
                avg_price=args.avg_price,
                buy_date=args.buy_date,
                sector=args.sector or "",
                notes=args.notes or "",
            )
        )
        action = "added"

    save_holdings(state_dir, holdings)

    return {
        "schema_version": "1.0",
        "subcommand": "add",
        "action": action,
        "symbol": sym,
        "exchange": args.exchange,
        "shares": args.shares,
        "avg_price": args.avg_price,
        "buy_date": args.buy_date,
        "sector": args.sector or "",
        "total_open_positions": len(holdings),
    }


# ---------------------------------------------------------------------------
# Subcommand: remove
# ---------------------------------------------------------------------------


def hold_days_between(buy: str, close: str) -> int:
    fmt = "%Y-%m-%d"
    try:
        b = datetime.strptime(buy, fmt)
        c = datetime.strptime(close, fmt)
        return (c - b).days
    except (ValueError, TypeError):
        return 0


def run_remove(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    holdings = load_holdings(state_dir)

    sym = args.symbol.upper()
    idx = next((i for i, h in enumerate(holdings) if h.symbol == sym), None)
    if idx is None:
        raise ValueError(f"Không tìm thấy vị thế {sym} trong holdings")

    holding = holdings[idx]
    pnl = net_pnl(
        holding.shares,
        holding.avg_price,
        args.close_price,
        broker_fee_pct=args.broker_fee_pct,
        sale_tax_pct=args.sale_tax_pct,
    )

    closed_record = {
        "symbol": sym,
        "exchange": holding.exchange,
        "shares": holding.shares,
        "avg_buy_price": holding.avg_price,
        "buy_date": holding.buy_date,
        "close_price": args.close_price,
        "close_date": args.close_date,
        "sector": holding.sector,
        "gross_pnl_vnd": pnl["gross_pnl_vnd"],
        "fees_vnd": pnl["fees_vnd"],
        "tax_vnd": pnl["tax_vnd"],
        "net_pnl_vnd": pnl["net_pnl_vnd"],
        "net_pnl_pct": pnl["net_pnl_pct"],
        "hold_days": hold_days_between(holding.buy_date, args.close_date),
    }
    append_closed(state_dir, closed_record)

    holdings.pop(idx)
    save_holdings(state_dir, holdings)

    return {
        "schema_version": "1.0",
        "subcommand": "remove",
        "closed": closed_record,
        "remaining_open_positions": len(holdings),
    }


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------


def days_held_to_today(buy_date: str) -> int:
    fmt = "%Y-%m-%d"
    try:
        b = datetime.strptime(buy_date, fmt)
        now = datetime.now(VN_TZ).replace(tzinfo=None)
        return (now - b).days
    except (ValueError, TypeError):
        return 0


def compute_position_snapshot(
    holding: Holding,
    current_price: float,
    broker_fee_pct: float,
    sale_tax_pct: float,
) -> dict:
    cost = holding.shares * holding.avg_price
    market_value = holding.shares * current_price
    gross_pnl = market_value - cost
    # Unrealized "after-fee/tax" assumes a hypothetical exit at current price
    fee_buy = buy_fee(cost, broker_fee_pct)
    fee_sell, tax_sell = sell_fee_and_tax(market_value, broker_fee_pct, sale_tax_pct)
    after_pnl = gross_pnl - fee_buy - fee_sell - tax_sell
    pnl_pct = gross_pnl / cost * 100 if cost > 0 else 0
    return {
        "symbol": holding.symbol,
        "exchange": holding.exchange,
        "sector": holding.sector,
        "shares": holding.shares,
        "avg_price": holding.avg_price,
        "current_price": current_price,
        "cost_basis_vnd": round(cost),
        "market_value_vnd": round(market_value),
        "unrealized_gross_pnl_vnd": round(gross_pnl),
        "unrealized_after_fee_tax_pnl_vnd": round(after_pnl),
        "unrealized_pnl_pct": round(pnl_pct, 3),
        "hold_days": days_held_to_today(holding.buy_date),
    }


def run_status(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    holdings = load_holdings(state_dir)
    prices = resolve_prices(args)

    snapshots = []
    missing_prices = []
    for h in holdings:
        if h.symbol not in prices:
            missing_prices.append(h.symbol)
            continue
        snapshots.append(
            compute_position_snapshot(
                h, prices[h.symbol], args.broker_fee_pct, args.sale_tax_pct
            )
        )

    total_cost = sum(s["cost_basis_vnd"] for s in snapshots)
    total_mv = sum(s["market_value_vnd"] for s in snapshots)
    total_pnl = total_mv - total_cost

    return {
        "schema_version": "1.0",
        "subcommand": "status",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "positions": snapshots,
        "missing_prices_for": missing_prices,
        "total_cost_basis_vnd": round(total_cost),
        "total_market_value_vnd": round(total_mv),
        "total_unrealized_pnl_vnd": round(total_pnl),
        "total_unrealized_pnl_pct": (
            round(total_pnl / total_cost * 100, 3) if total_cost > 0 else 0
        ),
    }


# ---------------------------------------------------------------------------
# Subcommand: summary
# ---------------------------------------------------------------------------


def run_summary(args: argparse.Namespace) -> dict:
    base = run_status(args)
    snaps = base["positions"]

    sector_breakdown: dict[str, float] = {}
    for s in snaps:
        sector_breakdown.setdefault(s["sector"] or "Chưa phân loại", 0)
        sector_breakdown[s["sector"] or "Chưa phân loại"] += s["market_value_vnd"]

    nav = base["total_market_value_vnd"]
    if args.account_size:
        cash = max(0, args.account_size - nav)
        full_nav = args.account_size
    else:
        cash = None
        full_nav = nav

    sector_pct = {
        k: round(v / full_nav * 100, 2) if full_nav else 0
        for k, v in sector_breakdown.items()
    }

    # Position % per symbol (vs full NAV)
    position_pct = [
        {
            "symbol": s["symbol"],
            "pct_of_nav": round(s["market_value_vnd"] / full_nav * 100, 2)
            if full_nav
            else 0,
        }
        for s in snaps
    ]

    # Concentration warnings
    warnings = []
    if args.max_position_pct is not None:
        for p in position_pct:
            if p["pct_of_nav"] > args.max_position_pct:
                warnings.append(
                    f"{p['symbol']} chiếm {p['pct_of_nav']}% NAV, "
                    f"vượt giới hạn {args.max_position_pct}%"
                )
    if args.max_sector_pct is not None:
        for sec, pct in sector_pct.items():
            if pct > args.max_sector_pct:
                warnings.append(
                    f"Ngành '{sec}' chiếm {pct}% NAV, "
                    f"vượt giới hạn {args.max_sector_pct}%"
                )

    # Top winners / losers
    sorted_by_pct = sorted(snaps, key=lambda s: s["unrealized_pnl_pct"], reverse=True)
    top_winners = sorted_by_pct[:3]
    top_losers = list(reversed(sorted_by_pct[-3:]))

    return {
        **base,
        "subcommand": "summary",
        "account_size_vnd": args.account_size,
        "cash_vnd": cash,
        "nav_vnd": full_nav,
        "sector_breakdown_vnd": {k: round(v) for k, v in sector_breakdown.items()},
        "sector_breakdown_pct": sector_pct,
        "position_pct": position_pct,
        "concentration_warnings": warnings,
        "top_winners": [
            {"symbol": w["symbol"], "pnl_pct": w["unrealized_pnl_pct"]}
            for w in top_winners
        ],
        "top_losers": [
            {"symbol": l["symbol"], "pnl_pct": l["unrealized_pnl_pct"]}
            for l in top_losers
        ],
    }


# ---------------------------------------------------------------------------
# Subcommand: closed
# ---------------------------------------------------------------------------


def run_closed(args: argparse.Namespace) -> dict:
    state_dir = Path(args.state_dir)
    records = load_closed(state_dir)
    return {
        "schema_version": "1.0",
        "subcommand": "closed",
        "count": len(records),
        "records": records,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_state_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state-dir",
        default="state/vn_portfolio/",
        help="Thư mục state CSV (mặc định state/vn_portfolio/)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/",
        help="Thư mục báo cáo (mặc định reports/)",
    )
    parser.add_argument(
        "--broker-fee-pct",
        type=float,
        default=DEFAULT_BROKER_FEE_PCT,
        help=f"Phí môi giới % (mặc định {DEFAULT_BROKER_FEE_PCT})",
    )
    parser.add_argument(
        "--sale-tax-pct",
        type=float,
        default=DEFAULT_SALE_TAX_PCT,
        help=f"Thuế bán % (mặc định {DEFAULT_SALE_TAX_PCT})",
    )


def add_price_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--prices",
        help='Giá hiện tại theo format SYMBOL:PRICE,SYMBOL:PRICE (ví dụ "VIC:46500,HPG:28500")',
    )
    group.add_argument(
        "--prices-file",
        help="Đường dẫn JSON chứa giá (flat hoặc output từ vn-data-fetcher)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Quản lý danh mục cổ phiếu Việt Nam"
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_add = sub.add_parser("add", help="Thêm vị thế mới")
    p_add.add_argument("--symbol", required=True)
    p_add.add_argument("--exchange", default="hose", choices=["hose", "hnx", "upcom"])
    p_add.add_argument("--shares", type=int, required=True)
    p_add.add_argument("--avg-price", type=float, required=True)
    p_add.add_argument("--buy-date", required=True, help="YYYY-MM-DD")
    p_add.add_argument("--sector", default="")
    p_add.add_argument("--notes", default="")
    add_state_args(p_add)

    p_rm = sub.add_parser("remove", help="Đóng vị thế")
    p_rm.add_argument("--symbol", required=True)
    p_rm.add_argument("--close-price", type=float, required=True)
    p_rm.add_argument("--close-date", required=True, help="YYYY-MM-DD")
    add_state_args(p_rm)

    p_status = sub.add_parser("status", help="Snapshot vị thế mở")
    add_price_args(p_status)
    add_state_args(p_status)

    p_sum = sub.add_parser("summary", help="Báo cáo tổng hợp NAV / ngành")
    p_sum.add_argument(
        "--account-size",
        type=float,
        help="Tổng tài khoản (tính cả tiền mặt) — nếu cung cấp, sẽ tính cash_vnd",
    )
    p_sum.add_argument(
        "--max-position-pct",
        type=float,
        help="Giới hạn % cho 1 vị thế (cảnh báo nếu vượt)",
    )
    p_sum.add_argument(
        "--max-sector-pct",
        type=float,
        help="Giới hạn % cho 1 ngành (cảnh báo nếu vượt)",
    )
    add_price_args(p_sum)
    add_state_args(p_sum)

    p_closed = sub.add_parser("closed", help="Liệt kê giao dịch đã đóng")
    add_state_args(p_closed)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.subcommand == "add":
            result = run_add(args)
        elif args.subcommand == "remove":
            result = run_remove(args)
        elif args.subcommand == "status":
            result = run_status(args)
        elif args.subcommand == "summary":
            result = run_summary(args)
        elif args.subcommand == "closed":
            result = run_closed(args)
        else:
            parser.error(f"Unknown subcommand: {args.subcommand}")
            return
    except (ValueError, FileNotFoundError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn_portfolio_{args.subcommand}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")

    # Compact summary to stdout
    if args.subcommand in ("status", "summary"):
        print(f"\nVị thế mở: {len(result.get('positions', []))}")
        print(
            f"Tổng cost basis: {result['total_cost_basis_vnd']:,} VND"
            if result.get("total_cost_basis_vnd")
            else ""
        )
        print(f"Tổng market value: {result['total_market_value_vnd']:,} VND")
        print(
            f"P&L chưa thực hiện: {result['total_unrealized_pnl_vnd']:,} VND "
            f"({result['total_unrealized_pnl_pct']}%)"
        )
        if args.subcommand == "summary":
            if result.get("concentration_warnings"):
                print("\nCảnh báo:")
                for w in result["concentration_warnings"]:
                    print(f"  ⚠️  {w}")
            print("\nTop winners:")
            for w in result["top_winners"]:
                print(f"  {w['symbol']}: {w['pnl_pct']}%")
    elif args.subcommand == "add":
        print(f"{result['action']} {result['symbol']}: {result['shares']:,} CP @ {result['avg_price']:,.0f}")
    elif args.subcommand == "remove":
        c = result["closed"]
        print(
            f"Đã đóng {c['symbol']}: net P&L {c['net_pnl_vnd']:,} VND "
            f"({c['net_pnl_pct']}%), giữ {c['hold_days']} ngày"
        )


if __name__ == "__main__":
    main()
