"""VN Position Sizer — Tính position size cho cổ phiếu Việt Nam.

Áp dụng quy tắc thị trường Việt Nam:
- Lô tròn 100 cổ phiếu (HOSE/HNX/UPCOM)
- Biên độ giá ±7% HOSE / ±10% HNX / ±15% UPCOM
- Bước giá theo sàn và khoảng giá
- Phí môi giới mặc định 0.15%, thuế bán 0.1%
- VND là đơn vị tiền tệ

Hỗ trợ Fixed Fractional, ATR-based, Kelly Criterion.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime

# VN market constants
LOT_SIZE = 100

PRICE_BAND_PCT = {
    "hose": 7.0,
    "hnx": 10.0,
    "upcom": 15.0,
}

# Phí và thuế mặc định (xem references/vn_fees_and_taxes.md)
DEFAULT_BROKER_FEE_PCT = 0.15
DEFAULT_SALE_TAX_PCT = 0.10


@dataclass
class VnSizingParameters:
    account_size_vnd: float
    exchange: str = "hose"
    symbol: str | None = None
    entry_price: float | None = None
    stop_price: float | None = None
    reference_price: float | None = None
    risk_pct: float | None = None
    atr: float | None = None
    atr_multiplier: float = 2.0
    win_rate: float | None = None
    avg_win: float | None = None
    avg_loss: float | None = None
    max_position_pct: float | None = None
    max_sector_pct: float | None = None
    sector: str | None = None
    current_sector_exposure: float = 0.0
    lot_size: int = LOT_SIZE
    broker_fee_pct: float = DEFAULT_BROKER_FEE_PCT
    sale_tax_pct: float = DEFAULT_SALE_TAX_PCT


def tick_size_hose(price: float) -> int:
    """HOSE tick size theo khoảng giá."""
    if price < 10_000:
        return 10
    if price < 50_000:
        return 50
    return 100


def tick_size(exchange: str, price: float) -> int:
    """Bước giá theo sàn và khoảng giá."""
    if exchange == "hose":
        return tick_size_hose(price)
    # HNX, UPCOM: 100 VND mọi mức
    return 100


def round_to_tick(price: float, exchange: str, mode: str = "nearest") -> int:
    """Làm tròn giá theo bước giá hợp lệ.

    mode: 'nearest' | 'down' | 'up'
    """
    tick = tick_size(exchange, price)
    if mode == "down":
        return int(price // tick * tick)
    if mode == "up":
        return int(-(-price // tick) * tick)  # ceil
    return int(round(price / tick) * tick)


def compute_price_band(reference_price: float, exchange: str) -> dict:
    """Tính giá trần/sàn theo sàn và giá tham chiếu."""
    pct = PRICE_BAND_PCT.get(exchange, 7.0)
    raw_ceiling = reference_price * (1 + pct / 100)
    raw_floor = reference_price * (1 - pct / 100)
    return {
        "reference_price": int(reference_price),
        "ceiling_price": round_to_tick(raw_ceiling, exchange, mode="down"),
        "floor_price": round_to_tick(raw_floor, exchange, mode="up"),
        "price_band_pct": pct,
    }


def validate_parameters(params: VnSizingParameters) -> None:
    """Validate input. Raise ValueError nếu sai."""
    if params.account_size_vnd <= 0:
        raise ValueError("account_size_vnd phải dương")
    if params.exchange not in PRICE_BAND_PCT:
        raise ValueError(f"exchange phải là một trong {list(PRICE_BAND_PCT)}")
    if params.entry_price is not None and params.entry_price <= 0:
        raise ValueError("entry_price phải dương")
    if params.stop_price is not None and params.entry_price is not None:
        if params.stop_price >= params.entry_price:
            raise ValueError("stop_price phải thấp hơn entry_price cho lệnh long")
    if params.risk_pct is not None and params.risk_pct <= 0:
        raise ValueError("risk_pct phải dương")
    if params.atr is not None and params.atr <= 0:
        raise ValueError("atr phải dương")
    if params.win_rate is not None:
        if params.win_rate <= 0 or params.win_rate > 1.0:
            raise ValueError("win_rate phải nằm trong (0, 1]")
    if params.avg_win is not None and params.avg_win <= 0:
        raise ValueError("avg_win phải dương")
    if params.avg_loss is not None and params.avg_loss <= 0:
        raise ValueError("avg_loss phải dương")
    if params.lot_size <= 0:
        raise ValueError("lot_size phải dương")
    if params.broker_fee_pct < 0:
        raise ValueError("broker_fee_pct không được âm")
    if params.sale_tax_pct < 0:
        raise ValueError("sale_tax_pct không được âm")


def round_to_lot(raw_shares: int, lot_size: int) -> int:
    """Làm tròn xuống bội số lô."""
    return (raw_shares // lot_size) * lot_size


def calculate_fixed_fractional(params: VnSizingParameters) -> dict:
    """Fixed fractional sizing với lô 100."""
    risk_per_share = params.entry_price - params.stop_price
    target_risk_vnd = params.account_size_vnd * params.risk_pct / 100
    raw_shares = int(target_risk_vnd / risk_per_share)
    rounded = round_to_lot(raw_shares, params.lot_size)
    return {
        "method": "fixed_fractional",
        "raw_shares": raw_shares,
        "lot_rounded_shares": rounded,
        "risk_per_share_vnd": round(risk_per_share),
        "target_dollar_risk_vnd": round(target_risk_vnd),
        "actual_dollar_risk_vnd": round(rounded * risk_per_share),
        "stop_price": params.stop_price,
    }


def calculate_atr_based(params: VnSizingParameters) -> dict:
    """ATR-based sizing.

    stop_distance = atr × atr_multiplier (VND)
    stop_price = entry_price - stop_distance, làm tròn xuống tick.
    """
    stop_distance = params.atr * params.atr_multiplier
    raw_stop = params.entry_price - stop_distance
    stop_price = round_to_tick(raw_stop, params.exchange, mode="down")
    risk_per_share = params.entry_price - stop_price
    target_risk_vnd = params.account_size_vnd * params.risk_pct / 100
    raw_shares = int(target_risk_vnd / risk_per_share)
    rounded = round_to_lot(raw_shares, params.lot_size)
    return {
        "method": "atr_based",
        "raw_shares": raw_shares,
        "lot_rounded_shares": rounded,
        "risk_per_share_vnd": round(risk_per_share),
        "target_dollar_risk_vnd": round(target_risk_vnd),
        "actual_dollar_risk_vnd": round(rounded * risk_per_share),
        "stop_price": stop_price,
        "atr": params.atr,
        "atr_multiplier": params.atr_multiplier,
    }


def calculate_kelly(params: VnSizingParameters) -> dict:
    """Kelly Criterion. Floor at 0; return half-Kelly recommendation."""
    w = params.win_rate
    r = params.avg_win / params.avg_loss
    kelly_pct = w - (1 - w) / r
    kelly_pct = max(0.0, kelly_pct) * 100
    half_kelly_pct = kelly_pct / 2
    return {
        "method": "kelly",
        "kelly_pct": round(kelly_pct, 2),
        "half_kelly_pct": round(half_kelly_pct, 2),
    }


def estimate_fees_and_taxes(
    shares: int, entry_price: float, params: VnSizingParameters
) -> dict:
    """Ước tính phí và thuế cho một round-trip mua-bán giả định tại entry."""
    position_value = shares * entry_price
    buy_fee = position_value * params.broker_fee_pct / 100
    sell_fee = position_value * params.broker_fee_pct / 100
    sell_tax = position_value * params.sale_tax_pct / 100
    total = buy_fee + sell_fee + sell_tax
    pct = (total / position_value * 100) if position_value > 0 else 0.0
    return {
        "buy_fee_vnd": round(buy_fee),
        "sell_fee_vnd_at_entry": round(sell_fee),
        "sell_tax_vnd_at_entry": round(sell_tax),
        "round_trip_cost_vnd": round(total),
        "round_trip_cost_pct": round(pct, 3),
    }


def apply_constraints(
    shares: int, params: VnSizingParameters
) -> tuple[int, list[dict], str | None]:
    """Áp ràng buộc max_position_pct, max_sector_pct, lot size."""
    constraints: list[dict] = []
    candidates = [shares]
    binding: str | None = None

    if params.max_position_pct is not None and params.entry_price:
        max_by_pos_raw = int(
            params.account_size_vnd * params.max_position_pct / 100 / params.entry_price
        )
        max_by_pos = round_to_lot(max_by_pos_raw, params.lot_size)
        constraints.append(
            {
                "type": "max_position_pct",
                "limit": params.max_position_pct,
                "max_shares": max_by_pos,
                "binding": False,
            }
        )
        candidates.append(max_by_pos)

    if params.max_sector_pct is not None and params.entry_price:
        remaining_pct = params.max_sector_pct - params.current_sector_exposure
        remaining_vnd = remaining_pct / 100 * params.account_size_vnd
        max_by_sector_raw = max(0, int(remaining_vnd / params.entry_price))
        max_by_sector = round_to_lot(max_by_sector_raw, params.lot_size)
        constraints.append(
            {
                "type": "max_sector_pct",
                "limit": params.max_sector_pct,
                "current": params.current_sector_exposure,
                "max_shares": max_by_sector,
                "binding": False,
            }
        )
        candidates.append(max_by_sector)

    final = max(0, min(candidates))

    for c in constraints:
        if c["max_shares"] == final and final < shares:
            c["binding"] = True
            binding = c["type"]

    return final, constraints, binding


def calculate_position(params: VnSizingParameters) -> dict:
    """Tính toán chính."""
    validate_parameters(params)

    is_kelly_mode = params.win_rate is not None
    has_entry = params.entry_price is not None

    result: dict = {
        "schema_version": "1.0",
        "market": "vn",
        "exchange": params.exchange,
        "symbol": params.symbol,
        "parameters": {
            "account_size_vnd": params.account_size_vnd,
            "lot_size": params.lot_size,
            "broker_fee_pct": params.broker_fee_pct,
            "sale_tax_pct": params.sale_tax_pct,
        },
    }

    # VN market context (price band) if we have a reference price
    ref = params.reference_price or params.entry_price
    if ref:
        band = compute_price_band(ref, params.exchange)
        stop_below_floor = (
            params.stop_price is not None and params.stop_price < band["floor_price"]
        )
        result["vn_market_context"] = {
            **band,
            "stop_below_floor": stop_below_floor,
        }
        if stop_below_floor:
            result.setdefault("warnings", []).append(
                f"Stop ({params.stop_price:,.0f}) thấp hơn giá sàn "
                f"({band['floor_price']:,}) — biên độ sẽ chặn lệnh cắt lỗ trong phiên đầu."
            )

    # ----- Kelly budget mode -----
    if is_kelly_mode and not has_entry:
        kelly = calculate_kelly(params)
        result["mode"] = "budget"
        result["parameters"].update(
            {
                "win_rate": params.win_rate,
                "avg_win": params.avg_win,
                "avg_loss": params.avg_loss,
            }
        )
        result["calculations"] = {
            "kelly": kelly,
            "fixed_fractional": None,
            "atr_based": None,
        }
        budget = params.account_size_vnd * kelly["half_kelly_pct"] / 100
        result["recommended_risk_budget_vnd"] = round(budget)
        result["recommended_risk_budget_pct"] = kelly["half_kelly_pct"]
        result["note"] = "Chạy lại với --entry và --stop để tính số cổ phiếu."
        return result

    # ----- Shares mode -----
    result["mode"] = "shares"
    result["parameters"]["entry_price"] = params.entry_price

    calculations: dict = {
        "fixed_fractional": None,
        "atr_based": None,
        "kelly": None,
    }
    risk_shares = 0

    if is_kelly_mode:
        kelly = calculate_kelly(params)
        calculations["kelly"] = kelly
        budget = params.account_size_vnd * kelly["half_kelly_pct"] / 100
        if params.stop_price:
            risk_per_share = params.entry_price - params.stop_price
            raw = int(budget / risk_per_share)
            risk_shares = round_to_lot(raw, params.lot_size)
            result["parameters"]["stop_price"] = params.stop_price
        else:
            raw = int(budget / params.entry_price)
            risk_shares = round_to_lot(raw, params.lot_size)
    elif params.atr is not None:
        atr_result = calculate_atr_based(params)
        calculations["atr_based"] = atr_result
        risk_shares = atr_result["lot_rounded_shares"]
        result["parameters"]["stop_price"] = atr_result["stop_price"]
        result["parameters"]["risk_pct"] = params.risk_pct
    else:
        ff_result = calculate_fixed_fractional(params)
        calculations["fixed_fractional"] = ff_result
        risk_shares = ff_result["lot_rounded_shares"]
        result["parameters"]["stop_price"] = params.stop_price
        result["parameters"]["risk_pct"] = params.risk_pct

    result["calculations"] = calculations

    final_shares, constraints, binding = apply_constraints(risk_shares, params)
    result["constraints_applied"] = constraints
    result["final_recommended_shares"] = final_shares
    result["final_position_value_vnd"] = round(final_shares * params.entry_price)

    # Phí + thuế ước tính
    result["fees_and_taxes_estimate"] = estimate_fees_and_taxes(
        final_shares, params.entry_price, params
    )

    # Rủi ro thực tế sau khi làm tròn lô
    if params.stop_price:
        risk_per_share = params.entry_price - params.stop_price
        result["final_risk_vnd"] = round(final_shares * risk_per_share)
        result["final_risk_pct"] = round(
            final_shares * risk_per_share / params.account_size_vnd * 100, 3
        )
    elif params.atr:
        risk_per_share = params.atr * params.atr_multiplier
        result["final_risk_vnd"] = round(final_shares * risk_per_share)
        result["final_risk_pct"] = round(
            final_shares * risk_per_share / params.account_size_vnd * 100, 3
        )
    else:
        result["final_risk_vnd"] = None
        result["final_risk_pct"] = None
        result["risk_note"] = "Chưa định nghĩa stop. Thêm --stop để tính rủi ro VND."

    result["binding_constraint"] = binding
    result["settlement_note"] = (
        "T+2.5: tiền và CP sẽ thanh toán đầy đủ vào chiều T+2 "
        "(không thể bán intraday)."
    )

    return result


def format_vnd(x: float | int | None) -> str:
    if x is None:
        return "n/a"
    return f"{int(x):,} VND"


def generate_markdown_report(result: dict) -> str:
    lines = [
        "# VN Position Sizing Report",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Market:** {result['market'].upper()} ({result['exchange'].upper()})",
    ]
    if result.get("symbol"):
        lines.append(f"**Symbol:** {result['symbol']}")
    lines.append(f"**Mode:** {result['mode']}")
    lines.append("")

    lines.append("## Tham số đầu vào")
    p = result.get("parameters", {})
    for key, label in [
        ("account_size_vnd", "Account size"),
        ("entry_price", "Entry price"),
        ("stop_price", "Stop price"),
        ("risk_pct", "Risk %"),
        ("win_rate", "Win rate"),
        ("avg_win", "Avg win"),
        ("avg_loss", "Avg loss"),
        ("lot_size", "Lot size"),
        ("broker_fee_pct", "Broker fee %"),
        ("sale_tax_pct", "Sale tax %"),
    ]:
        if key in p:
            val = p[key]
            if "vnd" in key or key in ("entry_price", "stop_price"):
                lines.append(f"- **{label}:** {format_vnd(val)}")
            else:
                lines.append(f"- **{label}:** {val}")
    lines.append("")

    # VN market context
    ctx = result.get("vn_market_context")
    if ctx:
        lines.append("## Bối cảnh thị trường VN")
        lines.append(f"- **Giá tham chiếu:** {format_vnd(ctx['reference_price'])}")
        lines.append(
            f"- **Giá trần:** {format_vnd(ctx['ceiling_price'])} "
            f"(+{ctx['price_band_pct']}%)"
        )
        lines.append(
            f"- **Giá sàn:** {format_vnd(ctx['floor_price'])} "
            f"(−{ctx['price_band_pct']}%)"
        )
        if ctx.get("stop_below_floor"):
            lines.append("- ⚠️ **Cảnh báo:** Stop dưới giá sàn — biên độ sẽ chặn lệnh cắt lỗ phiên đầu")
        lines.append("")

    # Warnings
    if result.get("warnings"):
        lines.append("## Cảnh báo")
        for w in result["warnings"]:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    # Mode: budget vs shares
    if result["mode"] == "budget":
        lines.append("## Kelly Criterion")
        kelly = result["calculations"]["kelly"]
        lines.append(f"- Full Kelly: {kelly['kelly_pct']}%")
        lines.append(f"- Half Kelly (khuyến nghị): {kelly['half_kelly_pct']}%")
        lines.append(
            f"- **Risk budget khuyến nghị:** "
            f"{format_vnd(result['recommended_risk_budget_vnd'])} "
            f"({result['recommended_risk_budget_pct']}% tài khoản)"
        )
        lines.append("")
        lines.append(f"*{result['note']}*")
    else:
        lines.append("## Tính toán")
        for method, calc in result.get("calculations", {}).items():
            if calc:
                lines.append(f"### {method.replace('_', ' ').title()}")
                for k, v in calc.items():
                    if k == "method":
                        continue
                    if "vnd" in k or k in ("stop_price",):
                        lines.append(f"- {k}: {format_vnd(v)}")
                    else:
                        lines.append(f"- {k}: {v}")
                lines.append("")

        # Phí + thuế
        fees = result.get("fees_and_taxes_estimate", {})
        if fees:
            lines.append("## Phí và thuế ước tính (round-trip tại giá entry)")
            lines.append(f"- Phí mua: {format_vnd(fees['buy_fee_vnd'])}")
            lines.append(f"- Phí bán: {format_vnd(fees['sell_fee_vnd_at_entry'])}")
            lines.append(f"- Thuế bán: {format_vnd(fees['sell_tax_vnd_at_entry'])}")
            lines.append(
                f"- **Tổng cost round-trip:** {format_vnd(fees['round_trip_cost_vnd'])} "
                f"({fees['round_trip_cost_pct']}%)"
            )
            lines.append("")

        if result.get("constraints_applied"):
            lines.append("## Ràng buộc")
            for c in result["constraints_applied"]:
                binding_label = " **[BINDING]**" if c.get("binding") else ""
                lines.append(
                    f"- {c['type']}: limit={c['limit']}%, "
                    f"max_shares={c['max_shares']:,}{binding_label}"
                )
            lines.append("")

        lines.append("## Khuyến nghị cuối")
        lines.append(f"- **Shares:** {result['final_recommended_shares']:,} CP")
        lines.append(
            f"- **Giá trị vị thế:** {format_vnd(result['final_position_value_vnd'])}"
        )
        if result.get("final_risk_vnd") is not None:
            lines.append(
                f"- **Rủi ro:** {format_vnd(result['final_risk_vnd'])} "
                f"({result['final_risk_pct']}%)"
            )
        if result.get("risk_note"):
            lines.append(f"- **Ghi chú:** {result['risk_note']}")
        if result.get("binding_constraint"):
            lines.append(f"- **Binding constraint:** {result['binding_constraint']}")
        lines.append(f"- **Settlement:** {result['settlement_note']}")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tính position size cho cổ phiếu Việt Nam (long-only)"
    )
    parser.add_argument(
        "--account-size",
        type=float,
        required=True,
        dest="account_size_vnd",
        help="Quy mô tài khoản (VND)",
    )
    parser.add_argument(
        "--exchange",
        type=str,
        default="hose",
        choices=["hose", "hnx", "upcom"],
        help="Sàn niêm yết (mặc định: hose)",
    )
    parser.add_argument("--symbol", type=str, help="Mã CP (ví dụ: VIC, HPG)")
    parser.add_argument("--entry", type=float, dest="entry_price", help="Giá entry (VND)")
    parser.add_argument("--stop", type=float, dest="stop_price", help="Giá stop (VND)")
    parser.add_argument(
        "--reference-price",
        type=float,
        help="Giá tham chiếu cho biên độ (mặc định = entry)",
    )
    parser.add_argument("--risk-pct", type=float, help="% rủi ro mỗi lệnh (ví dụ 1.0)")
    parser.add_argument("--atr", type=float, help="Giá trị ATR (VND)")
    parser.add_argument(
        "--atr-multiplier",
        type=float,
        default=2.0,
        help="Hệ số ATR cho stop distance (mặc định 2.0)",
    )
    parser.add_argument("--win-rate", type=float, help="Win rate (0-1) cho Kelly")
    parser.add_argument("--avg-win", type=float, help="Avg win cho Kelly")
    parser.add_argument("--avg-loss", type=float, help="Avg loss cho Kelly")
    parser.add_argument(
        "--max-position-pct",
        type=float,
        help="% tối đa cho 1 vị thế",
    )
    parser.add_argument(
        "--max-sector-pct",
        type=float,
        help="% tối đa cho 1 ngành",
    )
    parser.add_argument("--sector", type=str, help="Tên ngành")
    parser.add_argument(
        "--current-sector-exposure",
        type=float,
        default=0.0,
        help="% ngành hiện tại đang nắm",
    )
    parser.add_argument(
        "--lot-size",
        type=int,
        default=LOT_SIZE,
        help=f"Lô tròn (mặc định {LOT_SIZE})",
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
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/",
        help="Thư mục xuất báo cáo",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.risk_pct is not None and args.win_rate is not None:
        parser.error("Phải chọn risk-pct mode HOẶC kelly mode, không cả hai")

    if args.win_rate is not None:
        if args.avg_win is None or args.avg_loss is None:
            parser.error("Kelly mode cần --win-rate, --avg-win, --avg-loss")
    elif args.risk_pct is not None:
        if args.entry_price is None:
            parser.error("Risk-pct mode cần --entry")
        if args.stop_price is None and args.atr is None:
            parser.error("Risk-pct mode cần --stop hoặc --atr")
    else:
        parser.error("Phải chọn --risk-pct hoặc --win-rate mode")

    params = VnSizingParameters(
        account_size_vnd=args.account_size_vnd,
        exchange=args.exchange,
        symbol=args.symbol,
        entry_price=args.entry_price,
        stop_price=args.stop_price,
        reference_price=args.reference_price,
        risk_pct=args.risk_pct,
        atr=args.atr,
        atr_multiplier=args.atr_multiplier,
        win_rate=args.win_rate,
        avg_win=args.avg_win,
        avg_loss=args.avg_loss,
        max_position_pct=args.max_position_pct,
        max_sector_pct=args.max_sector_pct,
        sector=args.sector,
        current_sector_exposure=args.current_sector_exposure,
        lot_size=args.lot_size,
        broker_fee_pct=args.broker_fee_pct,
        sale_tax_pct=args.sale_tax_pct,
    )

    try:
        result = calculate_position(params)
    except ValueError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    json_path = os.path.join(args.output_dir, f"vn_position_sizer_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"JSON: {json_path}")

    md_report = generate_markdown_report(result)
    md_path = os.path.join(args.output_dir, f"vn_position_sizer_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"Markdown: {md_path}")

    # Summary
    if result["mode"] == "shares":
        print(
            f"\nKết quả: {result['final_recommended_shares']:,} CP "
            f"@ {format_vnd(params.entry_price)}"
        )
        print(f"Vị thế: {format_vnd(result['final_position_value_vnd'])}")
        if result.get("final_risk_vnd") is not None:
            print(
                f"Rủi ro: {format_vnd(result['final_risk_vnd'])} "
                f"({result['final_risk_pct']}%)"
            )
        if result.get("warnings"):
            for w in result["warnings"]:
                print(f"⚠️  {w}")
    else:
        print(
            f"\nRisk budget khuyến nghị: "
            f"{format_vnd(result['recommended_risk_budget_vnd'])} "
            f"({result['recommended_risk_budget_pct']}%)"
        )


if __name__ == "__main__":
    main()
