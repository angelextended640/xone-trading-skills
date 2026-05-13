---
name: vn-tax-fee-calculator
description: Tính chi tiết phí broker + thuế bán 0.1% + thuế cổ tức 5% + phí lưu ký + phí ứng trước cho giao dịch cổ phiếu Việt Nam. So sánh net return giữa các CTCK (VPS, SSI, VNDirect, HSC, MBS, TCBS, DNSE). Kích hoạt khi user hỏi "phí giao dịch", "thuế chứng khoán", "net P&L sau phí", "so sánh phí giữa các CTCK", "phí cổ tức". Vietnam stock fees + taxes calculator. Broker fee per CTCK, 0.1% sale tax, 5% dividend tax, custody fee, advance-cash fee. Trigger when user asks about fees / taxes / net P&L / broker comparison.
---

# VN Tax & Fee Calculator — Tính phí và thuế giao dịch CK Việt Nam

## Tổng quan

Tính chi tiết các khoản phí + thuế cho giao dịch cổ phiếu Việt Nam theo từng CTCK:

- **Phí môi giới** (broker commission): khác nhau theo CTCK (0.03% – 0.35%)
- **Thuế bán** (sale tax): 0.1% trên giá trị bán (áp dụng kể cả lỗ)
- **Thuế cổ tức tiền mặt** (cash dividend tax): 5%
- **Thuế cổ tức bằng cổ phiếu** (stock dividend tax): 5% trên mệnh giá khi bán
- **Phí lưu ký VSDC**: 0.27 VND/CP/tháng
- **Phí UBCKNN**: 0.02% trên giá trị giao dịch (thường đã gộp trong phí broker)
- **Phí ứng trước tiền bán**: ~0.04%/ngày (khi muốn dùng tiền bán trước T+2)

Cung cấp:
- **`trade`** subcommand: tính cost của 1 trade round-trip (mua + bán)
- **`compare`** subcommand: so sánh net return giữa các CTCK cho cùng trade
- **`dividend`** subcommand: tính thuế cổ tức
- **`monthly`** subcommand: ước tính phí lưu ký + ứng trước theo tháng

## Khi nào dùng

- User hỏi "phí giao dịch bao nhiêu?" / "thuế chứng khoán tính sao?"
- Chọn CTCK trước khi mở tài khoản — cần so sánh phí thực tế
- Tính break-even cho swing trade (giá phải vượt entry bao nhiêu % mới hoà vốn?)
- Tính net P&L sau khi đã có lãi gộp
- Ước tính chi phí ứng trước tiền bán khi cần cash flow nhanh
- Bổ sung context cho `vn-portfolio-manager`, `vn-position-sizer`, `vn-breakout-trade-planner`

## Điều kiện tiên quyết

- Python 3.9+ (chỉ standard library)
- Không cần API key, không cần Internet
- Tham chiếu: `skills/vn-market-mechanics/references/vn_fees_and_taxes.md`

## Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `trade` | Tính tổng phí + thuế cho 1 trade round-trip (mua-bán) |
| `compare` | So sánh phí giữa các CTCK cho cùng trade |
| `dividend` | Tính thuế cổ tức tiền mặt hoặc bằng cổ phiếu |
| `monthly` | Phí lưu ký + (tuỳ chọn) ứng trước hàng tháng |

### Lệnh mẫu

```bash
# 1. Tính cost cho 1 trade (VIC 1000 CP, entry 45k, exit 48k, broker VPS 0.15%)
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py trade \
  --shares 1000 --entry 45000 --exit 48000 \
  --broker vps \
  --output-dir reports/

# 2. So sánh phí giữa CTCK cho cùng trade
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py compare \
  --shares 3300 --entry 45000 --exit 47000 \
  --brokers vps,ssi,vndirect,hsc,mbs,tcbs,dnse \
  --output-dir reports/

# 3. Tính thuế cổ tức tiền mặt
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py dividend \
  --shares 3300 --dividend-per-share 2500 \
  --output-dir reports/

# 4. Phí lưu ký tháng cho portfolio
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py monthly \
  --total-shares 50000 \
  --advance-cash-vnd 100000000 --advance-days 5 \
  --output-dir reports/

# 5. Broker tuỳ chỉnh (CTCK chưa có trong defaults)
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py trade \
  --shares 1000 --entry 45000 --exit 48000 \
  --custom-broker "MyBroker" --custom-fee-pct 0.20 \
  --output-dir reports/
```

## CTCK profiles (built-in)

Skill có sẵn profile phí cho các CTCK phổ biến (cập nhật T05/2026):

| CTCK | Phí online (mặc định) | Ghi chú |
| --- | --- | --- |
| **VPS** | 0.15% | Phổ biến nhất, online standard |
| **SSI** | 0.15% | Online standard |
| **VNDirect** | 0.15% | Online standard |
| **HSC** | 0.15% | Online standard |
| **MBS** | 0.12% | Online standard |
| **TCBS** | 0.10% | Online standard |
| **DNSE** | 0.03% | Rẻ nhất (online tự thực hiện) |

Tất cả đều cộng:
- Thuế UBCKNN 0.02% (đã gộp trong nhiều CTCK)
- Thuế bán 0.1% (chỉ chiều bán)

User có thể override bằng `--custom-fee-pct` hoặc thêm CTCK qua `--brokers-config`.

## Output Format

### `trade` subcommand

```json
{
  "schema_version": "1.0",
  "subcommand": "trade",
  "as_of": "2026-05-13T08:00:00+07:00",
  "broker": "VPS",
  "inputs": {
    "shares": 1000,
    "entry_price": 45000,
    "exit_price": 48000,
    "broker_fee_pct": 0.15,
    "sale_tax_pct": 0.10
  },
  "costs": {
    "entry_value_vnd": 45000000,
    "exit_value_vnd": 48000000,
    "buy_fee_vnd": 67500,
    "sell_fee_vnd": 72000,
    "sell_tax_vnd": 48000,
    "total_cost_vnd": 187500,
    "total_cost_pct_of_entry": 0.417
  },
  "pnl": {
    "gross_pnl_vnd": 3000000,
    "net_pnl_vnd": 2812500,
    "net_pnl_pct": 6.25,
    "pct_eaten_by_costs": 6.25
  },
  "breakeven": {
    "min_exit_price_to_breakeven": 45188,
    "min_pct_gain_to_breakeven": 0.417
  }
}
```

### `compare` subcommand

Bảng so sánh các CTCK theo `net_pnl_vnd` giảm dần. Cột chính:
- `broker`, `total_cost_vnd`, `net_pnl_vnd`, `net_pnl_pct`, `min_pct_to_breakeven`

### `dividend` subcommand

```json
{
  "schema_version": "1.0",
  "subcommand": "dividend",
  "shares": 3300,
  "dividend_per_share_vnd": 2500,
  "gross_dividend_vnd": 8250000,
  "tax_rate_pct": 5.0,
  "tax_vnd": 412500,
  "net_dividend_vnd": 7837500
}
```

### `monthly` subcommand

Ước tính phí lưu ký + (tuỳ chọn) ứng trước:

```json
{
  "schema_version": "1.0",
  "subcommand": "monthly",
  "custody_fee_per_share_vnd": 0.27,
  "total_shares_held": 50000,
  "custody_fee_monthly_vnd": 13500,
  "advance_cash_vnd": 100000000,
  "advance_days": 5,
  "advance_fee_pct_per_day": 0.04,
  "advance_fee_vnd": 200000,
  "total_monthly_overhead_vnd": 213500
}
```

## Resources

- `scripts/vn_tax_fee_calculator.py` — script chính
- `references/broker_fee_profiles.json` — bảng phí từng CTCK
- Tham chiếu chéo: `skills/vn-market-mechanics/references/vn_fees_and_taxes.md`

## Nguyên tắc

1. **Cập nhật định kỳ** — phí và thuế có thể thay đổi. Tham chiếu chính thức của CTCK và UBCKNN khi có nghi vấn.
2. **Thuế bán áp dụng kể cả lỗ** — 0.1% trên giá trị bán, không phụ thuộc P&L. Đây là điểm khác Mỹ rất quan trọng.
3. **Break-even thực tế** — Một lệnh "đi ngang" (giá entry = exit) thực ra **lỗ** ~0.4% do phí + thuế. Đừng nhầm với gross P&L.
4. **Ứng trước tiền bán đắt** — 0.04%/ngày = ~14.6%/năm. Chỉ dùng khi thực sự cần.
5. **Phí broker khác nhau lớn** — Từ 0.03% (DNSE) đến 0.35% (truyền thống). Với volume cao, chọn CTCK rẻ tiết kiệm đáng kể.
