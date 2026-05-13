"""VN30 Derivatives Planner — VN30 Index Futures hedge / plan / roll / cost.

Subcommands:
  roll     — roll-date calendar + basis snapshot for current contract
  hedge    — beta-adjusted contract count to hedge a cash-equity exposure
  plan     — full short (or long) futures trade plan with IM check
  cost     — round-trip cost comparison across brokers

VN30 Futures specifics:
  - multiplier: 100,000 VND per VN30 index point
  - tick: 0.1 point = 10,000 VND
  - IM: ~18% of notional (typical retail)
  - settlement: T+0 cash-settled vs VN30 close
  - NO sale tax (futures are exempt; different from cash equities)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

VN_TZ = timezone(timedelta(hours=7))

# Contract specifications
MULTIPLIER = 100_000  # VND per index point
TICK_SIZE_POINTS = 0.1
TICK_SIZE_VND = 10_000
DEFAULT_IM_PCT = 18.0
DEFAULT_PRICE_BAND_PCT = 7.0  # same as HOSE

# Per-CTCK broker commission per contract (one side, VND)
BROKER_FEES_PER_CONTRACT = {
    "vps": 2_700,
    "ssi": 3_000,
    "vndirect": 3_000,
    "hsc": 2_700,
    "mbs": 2_700,
    "tcbs": 2_500,
    "dnse": 1_000,
    "vci": 3_000,
}

# Mandatory exchange / clearing fees per contract (one side, VND)
HNX_FEE_PER_CONTRACT = 2_700
VSDC_FEE_PER_CONTRACT = 2_550
OVERNIGHT_FEE_PER_CONTRACT = 3_000


# ---------------------------------------------------------------------------
# Tick + price rounding
# ---------------------------------------------------------------------------


def round_to_futures_tick(price: float, mode: str = "nearest") -> float:
    """Round a VN30 futures price to the 0.1 tick."""
    if mode == "down":
        return round((price * 10) // 10 / 10 + 1e-9, 1) if False else (int(price * 10) / 10)
    if mode == "up":
        return -(-(int(price * 10 + 0.999999))) / 10
    return round(price, 1)


def contract_notional(price: float) -> float:
    """Notional value of one contract at the given price."""
    return price * MULTIPLIER


def im_required(price: float, im_pct: float = DEFAULT_IM_PCT) -> float:
    """Initial margin requirement for one contract."""
    return contract_notional(price) * im_pct / 100


# ---------------------------------------------------------------------------
# Roll calendar
# ---------------------------------------------------------------------------


def third_thursday(year: int, month: int) -> date:
    """Return the date of the 3rd Thursday in the given month."""
    first = date(year, month, 1)
    # weekday(): Mon=0 .. Thu=3, Sun=6
    offset = (3 - first.weekday()) % 7  # days until first Thursday
    first_thu = first + timedelta(days=offset)
    return first_thu + timedelta(days=14)


def front_month_expiry(reference: date) -> date:
    """Return the next 3rd-Thursday expiry on/after the reference date."""
    candidate = third_thursday(reference.year, reference.month)
    if candidate >= reference:
        return candidate
    # Roll to next month
    if reference.month == 12:
        return third_thursday(reference.year + 1, 1)
    return third_thursday(reference.year, reference.month + 1)


def days_until(reference: date, target: date) -> int:
    return (target - reference).days


def basis_points(futures_price: float, spot_price: float) -> float:
    """Basis = futures - spot, in index points."""
    return futures_price - spot_price


def run_roll(args: argparse.Namespace) -> dict:
    """Compute roll calendar + basis snapshot."""
    ref_date = date.fromisoformat(args.reference_date) if args.reference_date else date.today()
    expiry = front_month_expiry(ref_date)
    days_to_expiry = days_until(ref_date, expiry)
    suggested_roll_start = expiry - timedelta(days=4)
    suggested_roll_end = expiry - timedelta(days=2)

    basis = None
    if args.vn30_spot is not None and args.futures_price is not None:
        basis = basis_points(args.futures_price, args.vn30_spot)

    in_roll_window = suggested_roll_start <= ref_date <= suggested_roll_end

    return {
        "schema_version": "1.0",
        "subcommand": "roll",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "current_contract": args.current_contract,
        "reference_date": ref_date.isoformat(),
        "front_month_expiry": expiry.isoformat(),
        "days_to_expiry": days_to_expiry,
        "suggested_roll_window_start": suggested_roll_start.isoformat(),
        "suggested_roll_window_end": suggested_roll_end.isoformat(),
        "in_roll_window": in_roll_window,
        "vn30_spot": args.vn30_spot,
        "futures_price": args.futures_price,
        "basis_points": round(basis, 2) if basis is not None else None,
        "basis_vnd_per_contract": round(basis * MULTIPLIER) if basis is not None else None,
        "action": (
            "Roll within window — close current contract, open next month"
            if in_roll_window
            else f"Hold; roll in {days_until(ref_date, suggested_roll_start)} days"
        ),
    }


# ---------------------------------------------------------------------------
# Hedge sizing
# ---------------------------------------------------------------------------


def compute_hedge_contracts(
    cash_exposure_vnd: float,
    portfolio_beta: float,
    vn30_spot: float,
    hedge_ratio: float = 1.0,
) -> dict:
    """Return contracts needed to hedge cash equity exposure."""
    if cash_exposure_vnd <= 0:
        raise ValueError("cash_exposure_vnd phải dương")
    if vn30_spot <= 0:
        raise ValueError("vn30_spot phải dương")
    if portfolio_beta <= 0:
        raise ValueError("portfolio_beta phải dương")
    if not 0 <= hedge_ratio <= 1.5:
        raise ValueError("hedge_ratio phải trong [0, 1.5]")

    contract_value = vn30_spot * MULTIPLIER
    contracts_raw = (cash_exposure_vnd * portfolio_beta * hedge_ratio) / contract_value
    contracts_actual = int(round(contracts_raw))
    total_notional = contracts_actual * contract_value
    im_total = total_notional * DEFAULT_IM_PCT / 100
    # Coverage relative to target hedge notional
    target_hedge = cash_exposure_vnd * portfolio_beta * hedge_ratio
    coverage_pct = (
        contracts_actual * contract_value / target_hedge * 100
        if target_hedge > 0
        else 0
    )
    return {
        "contracts_raw": round(contracts_raw, 3),
        "contracts_actual": contracts_actual,
        "contract_notional_vnd": round(contract_value),
        "total_notional_vnd": round(total_notional),
        "im_required_vnd": round(im_total),
        "hedge_coverage_pct": round(coverage_pct, 2),
        "basis_assumed": "spot",
        "slippage_note": (
            "Assumes futures = spot. Real basis typically 2-5 points away — "
            "add 0.2-0.4% margin if precision matters."
        ),
    }


def run_hedge(args: argparse.Namespace) -> dict:
    result = compute_hedge_contracts(
        args.cash_exposure_vnd,
        args.portfolio_beta,
        args.vn30_spot,
        args.hedge_ratio,
    )
    return {
        "schema_version": "1.0",
        "subcommand": "hedge",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "inputs": {
            "cash_exposure_vnd": args.cash_exposure_vnd,
            "portfolio_beta": args.portfolio_beta,
            "vn30_spot": args.vn30_spot,
            "hedge_ratio": args.hedge_ratio,
        },
        "result": result,
    }


# ---------------------------------------------------------------------------
# Trade plan
# ---------------------------------------------------------------------------


def compute_trade_plan(
    account_size_vnd: float,
    side: str,
    entry: float,
    stop: float,
    risk_pct: float,
    im_pct: float,
    target_r_multiples: list[float],
) -> dict:
    """Build a full long/short futures trade plan."""
    if account_size_vnd <= 0:
        raise ValueError("account_size phải dương")
    if entry <= 0 or stop <= 0:
        raise ValueError("entry và stop phải dương")
    if side not in ("long", "short"):
        raise ValueError("side phải là 'long' hoặc 'short'")
    if side == "long" and stop >= entry:
        raise ValueError("Long trade: stop phải nhỏ hơn entry")
    if side == "short" and stop <= entry:
        raise ValueError("Short trade: stop phải lớn hơn entry")
    if risk_pct <= 0:
        raise ValueError("risk_pct phải dương")

    risk_per_point = abs(entry - stop)
    risk_per_contract_vnd = risk_per_point * MULTIPLIER
    account_risk_vnd = account_size_vnd * risk_pct / 100
    contracts_raw = account_risk_vnd / risk_per_contract_vnd if risk_per_contract_vnd > 0 else 0
    contracts = int(contracts_raw)  # floor — never overshoot risk

    if contracts == 0:
        raise ValueError(
            "Risk per contract quá lớn so với budget — không đủ cho 1 contract. "
            "Giảm khoảng cách stop hoặc tăng risk_pct."
        )

    notional = entry * MULTIPLIER * contracts
    im_total = notional * im_pct / 100
    max_loss_vnd = risk_per_contract_vnd * contracts
    max_loss_pct = max_loss_vnd / account_size_vnd * 100
    leverage = notional / account_size_vnd if account_size_vnd > 0 else 0

    # Targets (R-multiples)
    targets: list[dict] = []
    n_targets = len(target_r_multiples)
    fractions = [round(1.0 / n_targets, 2)] * (n_targets - 1) + [
        round(1.0 - (n_targets - 1) * round(1.0 / n_targets, 2), 2)
    ]
    for r, frac in zip(target_r_multiples, fractions):
        if side == "long":
            price = entry + risk_per_point * r
        else:
            price = entry - risk_per_point * r
        targets.append(
            {
                "name": f"T{len(targets) + 1} ({r}R)",
                "r_multiple": r,
                "price": round(price, 1),
                "size_fraction": frac,
            }
        )

    # IM warning if too high
    im_warning = None
    if im_total / account_size_vnd > 0.30:
        im_warning = (
            f"IM {round(im_total / account_size_vnd * 100, 1)}% of account > 30% threshold — "
            f"over-leveraged. Reduce contracts."
        )

    return {
        "trade_plan": {
            "side": side,
            "entry": round(entry, 1),
            "stop": round(stop, 1),
            "risk_per_point": round(risk_per_point, 2),
            "risk_per_contract_vnd": round(risk_per_contract_vnd),
            "contracts": contracts,
            "notional_vnd": round(notional),
            "max_loss_vnd": round(max_loss_vnd),
            "max_loss_pct": round(max_loss_pct, 3),
            "im_required_vnd": round(im_total),
            "im_pct_of_account": round(im_total / account_size_vnd * 100, 2),
            "leverage_implied": round(leverage, 2),
            "targets": targets,
        },
        "im_warning": im_warning,
        "settlement_note": (
            "T+0 cash settlement. Position can be closed within the same session. "
            "Daily mark-to-market — equity adjusted at each daily close."
        ),
    }


def run_plan(args: argparse.Namespace) -> dict:
    r_multiples = [float(x.strip()) for x in args.targets.split(",")]
    plan = compute_trade_plan(
        args.account_size_vnd,
        args.side,
        args.entry,
        args.stop,
        args.risk_pct,
        args.im_pct,
        r_multiples,
    )
    return {
        "schema_version": "1.0",
        "subcommand": "plan",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "inputs": {
            "account_size_vnd": args.account_size_vnd,
            "side": args.side,
            "entry": args.entry,
            "stop": args.stop,
            "risk_pct": args.risk_pct,
            "im_pct": args.im_pct,
        },
        **plan,
    }


# ---------------------------------------------------------------------------
# Cost comparison
# ---------------------------------------------------------------------------


def compute_cost_per_broker(
    contracts: int,
    entry: float,
    exit_price: float,
    side: str,
    broker_fee: float,
    nights_held: int = 0,
) -> dict:
    """Compute round-trip cost + P&L for one broker."""
    # Gross P&L
    if side == "long":
        gross_pnl = (exit_price - entry) * MULTIPLIER * contracts
    else:
        gross_pnl = (entry - exit_price) * MULTIPLIER * contracts

    round_trip_fee = (2 * broker_fee + 2 * HNX_FEE_PER_CONTRACT + 2 * VSDC_FEE_PER_CONTRACT) * contracts
    overnight_fee = nights_held * OVERNIGHT_FEE_PER_CONTRACT * contracts
    total_cost = round_trip_fee + overnight_fee
    net_pnl = gross_pnl - total_cost
    notional = entry * MULTIPLIER * contracts
    net_pnl_pct = net_pnl / notional * 100 if notional > 0 else 0

    return {
        "broker_fee_per_side_vnd": round(broker_fee),
        "round_trip_fee_vnd": round(round_trip_fee),
        "overnight_fee_vnd": round(overnight_fee),
        "total_cost_vnd": round(total_cost),
        "gross_pnl_vnd": round(gross_pnl),
        "net_pnl_vnd": round(net_pnl),
        "net_pnl_pct_of_notional": round(net_pnl_pct, 3),
    }


def run_cost(args: argparse.Namespace) -> dict:
    if args.brokers:
        broker_keys = [b.strip().lower() for b in args.brokers.split(",")]
    else:
        broker_keys = sorted(BROKER_FEES_PER_CONTRACT.keys())

    rows = []
    for key in broker_keys:
        if key not in BROKER_FEES_PER_CONTRACT:
            raise ValueError(
                f"Unknown broker '{key}'. Available: {sorted(BROKER_FEES_PER_CONTRACT)}"
            )
        fee = BROKER_FEES_PER_CONTRACT[key]
        calc = compute_cost_per_broker(
            args.contracts, args.entry, args.exit, args.side, fee, args.nights_held
        )
        rows.append({"broker": key.upper(), **calc})

    rows.sort(key=lambda r: -r["net_pnl_vnd"])

    return {
        "schema_version": "1.0",
        "subcommand": "cost",
        "as_of": datetime.now(VN_TZ).isoformat(),
        "inputs": {
            "contracts": args.contracts,
            "entry": args.entry,
            "exit": args.exit,
            "side": args.side,
            "nights_held": args.nights_held,
        },
        "rows": rows,
        "best_broker": rows[0]["broker"] if rows else None,
        "worst_broker": rows[-1]["broker"] if rows else None,
        "spread_vnd": (
            rows[0]["net_pnl_vnd"] - rows[-1]["net_pnl_vnd"] if len(rows) >= 2 else 0
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def format_vnd(x: int | float | None) -> str:
    if x is None:
        return "n/a"
    return f"{int(x):,} VND"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VN30 Index Futures planner — hedge, plan, roll, cost"
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # roll
    p_roll = sub.add_parser("roll", help="Roll calendar + basis snapshot")
    p_roll.add_argument(
        "--current-contract",
        default="VN30F1M",
        help="Current contract symbol (default VN30F1M)",
    )
    p_roll.add_argument("--reference-date", help="YYYY-MM-DD (default: today)")
    p_roll.add_argument("--vn30-spot", type=float, help="Current VN30 spot index")
    p_roll.add_argument("--futures-price", type=float, help="Current futures price")
    p_roll.add_argument("--output-dir", default="reports/")

    # hedge
    p_hedge = sub.add_parser("hedge", help="Hedge cash equity exposure with short futures")
    p_hedge.add_argument(
        "--cash-exposure-vnd",
        type=float,
        required=True,
        help="Total cash equity long exposure (VND)",
    )
    p_hedge.add_argument(
        "--portfolio-beta",
        type=float,
        required=True,
        help="Portfolio beta vs VN30 (typical 0.8-1.3 for HOSE blue-chips)",
    )
    p_hedge.add_argument("--vn30-spot", type=float, required=True)
    p_hedge.add_argument(
        "--hedge-ratio",
        type=float,
        default=1.0,
        help="0 = no hedge, 1.0 = full hedge, 0.5 = half hedge",
    )
    p_hedge.add_argument("--output-dir", default="reports/")

    # plan
    p_plan = sub.add_parser("plan", help="Full short/long futures trade plan")
    p_plan.add_argument(
        "--account-size",
        type=float,
        required=True,
        dest="account_size_vnd",
        help="Total account equity (VND)",
    )
    p_plan.add_argument(
        "--side",
        choices=["long", "short"],
        required=True,
        help="Trade side",
    )
    p_plan.add_argument("--entry", type=float, required=True, help="Entry price (points)")
    p_plan.add_argument("--stop", type=float, required=True, help="Stop price (points)")
    p_plan.add_argument(
        "--risk-pct",
        type=float,
        default=1.0,
        help="Risk % per trade (default 1.0)",
    )
    p_plan.add_argument(
        "--im-pct",
        type=float,
        default=DEFAULT_IM_PCT,
        help=f"Initial margin %% (default {DEFAULT_IM_PCT})",
    )
    p_plan.add_argument(
        "--targets",
        default="1,2,3",
        help="R-multiples CSV (default '1,2,3')",
    )
    p_plan.add_argument("--output-dir", default="reports/")

    # cost
    p_cost = sub.add_parser("cost", help="Compare round-trip cost across brokers")
    p_cost.add_argument("--contracts", type=int, required=True)
    p_cost.add_argument("--entry", type=float, required=True)
    p_cost.add_argument("--exit", type=float, required=True)
    p_cost.add_argument("--side", choices=["long", "short"], required=True)
    p_cost.add_argument(
        "--brokers",
        help="CSV of broker keys (default: all built-in)",
    )
    p_cost.add_argument(
        "--nights-held",
        type=int,
        default=0,
        help="Number of nights position held (overnight fee)",
    )
    p_cost.add_argument("--output-dir", default="reports/")

    return parser


def print_summary(result: dict) -> None:
    sub = result["subcommand"]
    print()
    if sub == "roll":
        print(f"=== Roll Calendar — {result['current_contract']} ===")
        print(f"Reference date     : {result['reference_date']}")
        print(f"Front month expiry : {result['front_month_expiry']}")
        print(f"Days to expiry     : {result['days_to_expiry']}")
        print(f"Roll window        : {result['suggested_roll_window_start']} → {result['suggested_roll_window_end']}")
        print(f"In roll window?    : {result['in_roll_window']}")
        if result["basis_points"] is not None:
            print(f"Basis (F - S)      : {result['basis_points']} pts = {format_vnd(result['basis_vnd_per_contract'])}/contract")
        print(f"\nAction: {result['action']}")
    elif sub == "hedge":
        r = result["result"]
        i = result["inputs"]
        print(f"=== Hedge Sizing ===")
        print(f"Cash exposure : {format_vnd(i['cash_exposure_vnd'])}")
        print(f"Portfolio beta: {i['portfolio_beta']}")
        print(f"VN30 spot     : {i['vn30_spot']}")
        print(f"Hedge ratio   : {i['hedge_ratio'] * 100}%")
        print()
        print(f"Contracts (raw)   : {r['contracts_raw']}")
        print(f"Contracts (actual): {r['contracts_actual']}")
        print(f"Notional/contract : {format_vnd(r['contract_notional_vnd'])}")
        print(f"Total notional    : {format_vnd(r['total_notional_vnd'])}")
        print(f"IM required       : {format_vnd(r['im_required_vnd'])}")
        print(f"Hedge coverage    : {r['hedge_coverage_pct']}%")
        print(f"\nNote: {r['slippage_note']}")
    elif sub == "plan":
        tp = result["trade_plan"]
        print(f"=== {tp['side'].upper()} VN30 Futures Plan ===")
        print(f"Entry          : {tp['entry']} pts")
        print(f"Stop           : {tp['stop']} pts (risk/contract = {format_vnd(tp['risk_per_contract_vnd'])})")
        print(f"Contracts      : {tp['contracts']}")
        print(f"Notional       : {format_vnd(tp['notional_vnd'])}  (leverage {tp['leverage_implied']}x)")
        print(f"IM required    : {format_vnd(tp['im_required_vnd'])}  ({tp['im_pct_of_account']}% of account)")
        print(f"Max loss       : {format_vnd(tp['max_loss_vnd'])}  ({tp['max_loss_pct']}%)")
        print("\nTargets:")
        for t in tp["targets"]:
            print(f"  {t['name']:>10s}: {t['price']:>7.1f} pts  ({t['size_fraction'] * 100:.0f}% size)")
        if result.get("im_warning"):
            print(f"\n⚠️  {result['im_warning']}")
        print(f"\n{result['settlement_note']}")
    elif sub == "cost":
        i = result["inputs"]
        print(
            f"=== Cost ({i['contracts']} contracts, "
            f"{i['side']} @ {i['entry']} → {i['exit']}, {i['nights_held']} nights) ==="
        )
        print(f"{'Broker':<10s} {'RT fee':>14s} {'Ovn fee':>12s} {'Total':>14s} {'Net P&L':>16s} {'Net %':>8s}")
        for r in result["rows"]:
            print(
                f"{r['broker']:<10s} {format_vnd(r['round_trip_fee_vnd']):>14s} "
                f"{format_vnd(r['overnight_fee_vnd']):>12s} {format_vnd(r['total_cost_vnd']):>14s} "
                f"{format_vnd(r['net_pnl_vnd']):>16s} {r['net_pnl_pct_of_notional']:>7.3f}%"
            )
        print(f"\nBest: {result['best_broker']}, worst: {result['worst_broker']}, spread: {format_vnd(result['spread_vnd'])}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.subcommand == "roll":
            result = run_roll(args)
        elif args.subcommand == "hedge":
            result = run_hedge(args)
        elif args.subcommand == "plan":
            result = run_plan(args)
        elif args.subcommand == "cost":
            result = run_cost(args)
        else:
            parser.error(f"Unknown subcommand: {args.subcommand}")
            return
    except (ValueError, FileNotFoundError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    path = Path(args.output_dir) / f"vn30_derivatives_{args.subcommand}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {path}")
    print_summary(result)


if __name__ == "__main__":
    main()
