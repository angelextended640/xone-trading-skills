---
name: vn30-derivatives-planner
description: Lập kế hoạch giao dịch phái sinh VN30 Futures (VN30F1M, VN30F2M, VN30F1Q, VN30F2Q). Tính roll calendar, basis vs spot, hedge sizing cho exposure cash equity, full short trade plan với IM + max loss, so sánh chi phí giữa CTCK. T+0 settlement — short tool hợp pháp duy nhất ở VN. Kích hoạt khi user hỏi "VN30 futures", "phái sinh", "short VN30", "hedge danh mục", "roll hợp đồng". Vietnam VN30 Index Futures planner — roll, hedge sizing, short trade plan, broker cost comparison. The only legal short-exposure tool on Vietnam markets.
---

# VN30 Derivatives Planner — Phái sinh VN30 Futures

## Tổng quan

Lập kế hoạch giao dịch **VN30 Index Futures** — sản phẩm phái sinh duy nhất phổ biến trên TTCK Việt Nam, và **cách duy nhất hợp pháp để short** (cổ phiếu cơ sở không được short).

Hỗ trợ 4 subcommands:

- **`roll`** — Roll calendar, basis spot vs futures, suggested roll window cho contract đang nắm
- **`hedge`** — Tính số contract short để hedge cash equity exposure (theta-neutral / beta-adjusted)
- **`plan`** — Full short trade plan: entry, stop, R-multiple targets, IM required, max loss
- **`cost`** — So sánh chi phí round-trip giữa các CTCK (different fee structure từ cash equities)

## Khi nào dùng

- User muốn short VN-Index khi sector regime risk-off (`vn-sector-analyst` regime note = negative)
- Hedge một portfolio cash equity lớn trong giai đoạn macro risk
- Lên kế hoạch roll hợp đồng (cuối tháng / cuối quý)
- So sánh phí phái sinh giữa CTCK trước khi mở tài khoản phái sinh
- Pair với `vn-portfolio-manager` để tính net exposure (cash long − futures short)

**KHÔNG** dùng cho:
- Speculation đơn thuần không có kế hoạch (T+0 = drawdown nhanh nếu sai)
- Hedge với contract sai (luôn dùng VN30F1M trừ khi sắp roll)
- Trader chưa quen với phái sinh — IM 17-20% nghĩa là 5-6x leverage

## Điều kiện tiên quyết

- Python 3.9+ (chỉ standard library)
- Tài khoản phái sinh ở CTCK (yêu cầu setup riêng — không phải mọi CTCK đều có sẵn)
- Tham chiếu: `references/vn_futures_mechanics.md`, `references/vn_futures_fees.md`

## Đặc thù VN30 Futures vs cash equities

| Aspect | Cash equity | VN30 Futures |
| --- | --- | --- |
| Sàn | HOSE / HNX / UPCOM | HNX (phái sinh sàn riêng) |
| Lô | 100 CP | 1 contract |
| Multiplier | n/a | 100,000 VND × VN30 point |
| Tick size | 10/50/100 VND | 0.1 point = 10,000 VND |
| Daily price band | ±7% (HOSE) | ±7% từ giá tham chiếu hôm trước |
| Settlement | T+2.5 | **T+0** (cash-settled vs VN30 close) |
| Short | Không cho phép | **Cho phép** |
| Sale tax | 0.1% trên giá bán | **Không có** |
| Broker fee | 0.03-0.15% notional | 1,000-3,000 VND/HĐ |
| IM required | n/a (full cash) | ~17-20% notional |
| Leverage | 1x (cash) | ~5-6x |
| Overnight position cost | Phí lưu ký 0.27 VND/CP/month | ~3,000 VND/contract/đêm |

## Workflow

### Subcommands

#### `roll` — Roll calendar + basis

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py roll \
  --current-contract VN30F1M \
  --reference-date 2026-05-13 \
  --vn30-spot 1280.5 --futures-price 1283.0 \
  --output-dir reports/
```

Output: ngày roll tới (last Thursday of front month), basis (futures - spot), suggested action.

#### `hedge` — Tính số contract để hedge

```bash
# Bạn có 1B VND cash equity long, beta 1.05 vs VN30; muốn hedge 100%
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py hedge \
  --cash-exposure-vnd 1000000000 \
  --portfolio-beta 1.05 \
  --vn30-spot 1280 \
  --hedge-ratio 1.0 \
  --output-dir reports/
```

Output: số contract cần short, IM cần thiết, notional value, basis-adjusted slippage estimate.

#### `plan` — Full short trade plan

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py plan \
  --account-size 1000000000 \
  --side short \
  --entry 1283.0 --stop 1300.0 \
  --risk-pct 1.0 \
  --output-dir reports/
```

Output: contracts cần thiết, IM bị khóa, max loss, R-multiple targets, T+0 fast-exit note.

#### `cost` — So sánh phí broker

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py cost \
  --contracts 5 --entry 1283.0 --exit 1265.0 \
  --side short \
  --brokers vps,ssi,vndirect,hsc,mbs,tcbs,dnse \
  --output-dir reports/
```

Output: cost / net P&L per broker, spread.

## Tiêu chí cho hedge sizing

Số contract short để hedge cash equity:

```
contracts_needed = (cash_exposure_vnd × portfolio_beta × hedge_ratio) /
                   (vn30_spot × 100,000)
```

Round to integer (contracts không chia nhỏ được). Hedge ratio 1.0 = full hedge, 0.5 = half hedge.

## Trade plan risk math

Trên VN30 Futures, mỗi 0.1 point thay đổi = 10,000 VND/HĐ.

```
risk_per_contract_vnd = |entry - stop| × 100,000
contracts = floor(account_risk_vnd / risk_per_contract_vnd)
im_required_per_contract = entry × 100,000 × 0.18  (approx 18% IM)
```

## Output Format

### `hedge` output

```json
{
  "schema_version": "1.0",
  "subcommand": "hedge",
  "inputs": {
    "cash_exposure_vnd": 1000000000,
    "portfolio_beta": 1.05,
    "vn30_spot": 1280.0,
    "hedge_ratio": 1.0
  },
  "result": {
    "contracts_raw": 8.20,
    "contracts_actual": 8,
    "contract_notional_vnd": 128000000,
    "total_notional_vnd": 1024000000,
    "im_required_vnd": 184320000,
    "hedge_coverage_pct": 97.5,
    "basis_assumed": "spot",
    "slippage_note": "Assumes futures = spot. Real basis typically 2-5 points away — add 0.2-0.4% margin."
  }
}
```

### `plan` output

```json
{
  "schema_version": "1.0",
  "subcommand": "plan",
  "side": "short",
  "trade_plan": {
    "entry": 1283.0,
    "stop": 1300.0,
    "risk_per_contract_vnd": 1700000,
    "contracts": 5,
    "max_loss_vnd": 8500000,
    "max_loss_pct": 0.85,
    "im_required_vnd": 115470000,
    "leverage_implied": 5.55,
    "targets": [
      {"name": "T1 (1R)", "price": 1266.0, "size_fraction": 0.33},
      {"name": "T2 (2R)", "price": 1249.0, "size_fraction": 0.33},
      {"name": "T3 (3R)", "price": 1232.0, "size_fraction": 0.34}
    ]
  },
  "fees_estimate": {
    "round_trip_fee_per_contract_vnd": 18000,
    "total_fees_vnd": 90000
  },
  "settlement_note": "T+0 cash settlement. Position can be closed same session."
}
```

## Resources

- `references/vn_futures_mechanics.md` — Contract spec, roll calendar, trading hours
- `references/vn_futures_fees.md` — Per-CTCK fee table
- `scripts/vn30_derivatives_planner.py` — Main CLI
- Cross-references:
  - `skills/vn-sector-analyst/` — regime hint → hedge timing
  - `skills/vn-portfolio-manager/` — net exposure (long cash − short futures)
  - `skills/vn-tax-fee-calculator/` — parent for fee patterns

## Nguyên tắc

1. **VN30 Futures là leverage** — IM 18% = 5.5x. Lỗ nhanh nếu sai. Position-size theo total notional, không phải IM.
2. **T+0 = không có cushion** — Stop loss phải nghiêm túc. Không hold qua đêm position lớn nếu chưa quen.
3. **Roll trước expiry** — VN30F1M expire last Thursday. Roll 2-3 sessions trước để tránh thin liquidity.
4. **Basis volatility** — Futures có thể trade premium/discount vs spot. Khi spread > 5 points, cẩn trọng (signal vốn ngoại defensive hoặc speculate mạnh).
5. **Hedge ≠ Speculation** — Khi hedge cash portfolio, mục tiêu là **neutral risk**, không phải lãi từ futures. P&L futures bù P&L cash.
6. **Trade plan có IM check** — Một trade plan không hợp lệ nếu IM > 30% account (over-leveraged).
