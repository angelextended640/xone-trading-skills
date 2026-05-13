---
name: vn-position-sizer
description: Tính số cổ phiếu tối ưu cho lệnh mua (long) trên TTCK Việt Nam dựa trên quản trị rủi ro — áp dụng lô 100, biên độ giá trần/sàn, phí môi giới 0.15%, thuế bán 0.1%, T+2.5 settlement. Hỗ trợ Fixed Fractional, ATR-based, Kelly Criterion. Kích hoạt khi user hỏi "mua bao nhiêu CP", "size lệnh", "position sizing cho mã VN" bằng tiếng Việt hoặc Anh. Calculate optimal share count for long stock trades on Vietnam stock market with VN-specific rules — lot size 100, price ceiling/floor, 0.15% broker fee, 0.1% sale tax, T+2.5 settlement. Supports Fixed Fractional, ATR-based, Kelly Criterion.
---

# VN Position Sizer — Tính position size cho cổ phiếu Việt Nam

## Tổng quan

Tính số cổ phiếu tối ưu cho lệnh **mua (long)** trên TTCK Việt Nam dựa trên nguyên tắc quản trị rủi ro, có tính đến:

- **Lô tròn 100 cổ phiếu** (HOSE/HNX/UPCOM)
- **Biên độ giá trần/sàn** theo sàn (±7% HOSE / ±10% HNX / ±15% UPCOM)
- **Phí môi giới** (mặc định 0.15% mỗi chiều) và **thuế bán** 0.1%
- **Thanh toán T+2.5** — không thể bán intraday, ảnh hưởng đến tái sử dụng vốn
- **VND** là đơn vị tiền tệ duy nhất

Hỗ trợ ba phương pháp:
- **Fixed Fractional** (mặc định 1% rủi ro mỗi lệnh)
- **ATR-Based** (stop dựa trên độ biến động)
- **Kelly Criterion** (từ thống kê hit-rate quá khứ)

## Khi nào dùng

- Người dùng hỏi "mua bao nhiêu cổ phiếu VIC?", "size cho HPG", "đặt bao nhiêu lô"
- Người dùng đề cập rủi ro mỗi lệnh, stop-loss size, hoặc phân bổ portfolio cho cổ phiếu VN
- Cần kiểm tra một lệnh có vi phạm giới hạn concentration hay không
- Đang lập kế hoạch breakout / VCP / CANSLIM cho cổ phiếu Việt Nam

**KHÔNG** dùng skill này cho:
- Cổ phiếu Mỹ — dùng `position-sizer` thay thế
- Bán khống cổ phiếu cơ sở (không được phép tại VN — xem `vn-market-mechanics/references/vn_trading_rules.md`)
- Phái sinh VN30 Futures — sẽ có skill riêng `vn30-derivatives-planner`

## Điều kiện tiên quyết

- Không cần API key
- Python 3.9+ với standard library
- **Tham khảo** `skills/vn-market-mechanics/references/` để hiểu biên độ, lô, phí, thuế

## Workflow

### Bước 1: Thu thập tham số

Hỏi người dùng:
- **Bắt buộc:**
  - Quy mô tài khoản (VND) — ví dụ 1,000,000,000 (1 tỷ)
  - Mã cổ phiếu (để skill xác định sàn và áp biên độ tương ứng)
- **Mode A (Fixed Fractional):** Giá entry, giá stop, %rủi ro (mặc định 1%)
- **Mode B (ATR-based):** Giá entry, giá trị ATR, ATR multiplier (mặc định 2.0), %rủi ro
- **Mode C (Kelly):** Win rate, avg win, avg loss; tuỳ chọn entry/stop để tính shares
- **Tuỳ chọn ràng buộc:**
  - %tối đa cho 1 vị thế (mặc định 10%)
  - %tối đa cho 1 ngành (mặc định 30%)
  - %ngành hiện tại đang nắm

### Bước 2: Xác định sàn (HOSE/HNX/UPCOM) và biên độ

- Nếu user cung cấp mã, dùng tham số `--exchange hose|hnx|upcom` để chỉ định
- Mặc định: `hose` (±7%, bước giá 10/50/100 theo khoảng giá)
- Tính giá trần/sàn từ giá tham chiếu (giá đóng cửa phiên trước, có thể user cung cấp qua `--reference-price`)
- **Cảnh báo nếu giá stop đề xuất nằm thấp hơn giá sàn** — biên độ sẽ chặn lệnh cắt lỗ trong phiên đầu

### Bước 3: Chạy script

```bash
# Fixed Fractional cơ bản (HOSE)
python3 skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol VIC --exchange hose \
  --entry 45000 --stop 42000 \
  --risk-pct 1.0 \
  --output-dir reports/

# ATR-based (HOSE)
python3 skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol HPG --exchange hose \
  --entry 28000 --atr 800 --atr-multiplier 2.0 \
  --risk-pct 1.0 \
  --output-dir reports/

# HNX với ràng buộc concentration
python3 skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 500000000 \
  --symbol SHS --exchange hnx \
  --entry 18000 --stop 16500 \
  --risk-pct 1.0 \
  --max-position-pct 8 --max-sector-pct 25 \
  --sector "Tài chính" --current-sector-exposure 18 \
  --output-dir reports/

# Kelly Criterion (budget mode)
python3 skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --win-rate 0.55 --avg-win 2.5 --avg-loss 1.0 \
  --output-dir reports/
```

### Bước 4: Đọc tham chiếu nếu cần

- `skills/vn-position-sizer/references/vn_sizing_methodologies.md` — so sánh 3 phương pháp
- `skills/vn-market-mechanics/references/vn_price_limits_orders.md` — biên độ, lô, bước giá
- `skills/vn-market-mechanics/references/vn_fees_and_taxes.md` — phí, thuế

### Bước 5: So sánh nhiều kịch bản (nếu user chưa chọn method)

Chạy với 3 mức %rủi ro: 0.5%, 1.0%, 1.5% và trình bày bảng so sánh:
- Số CP (đã làm tròn lô 100)
- Giá trị vị thế (VND)
- Rủi ro VND
- Rủi ro % thực tế (sau khi làm tròn)

### Bước 6: Áp ràng buộc và xác định size cuối

Ràng buộc nào chặt nhất sẽ thắng. Giải thích rõ:
- `risk-based`: số CP theo phương pháp rủi ro
- `max-position-pct`: bị chặn bởi giới hạn %1 mã
- `max-sector-pct`: bị chặn bởi giới hạn %ngành
- `lot-size`: bị làm tròn xuống bội số 100

### Bước 7: Tạo báo cáo

Output gồm JSON + Markdown với:
- Tham số đầu vào
- Tính toán theo phương pháp đã chọn
- Bảng phí + thuế dự kiến (mua, bán, thuế bán 0.1%)
- Giá trần/sàn của phiên tiếp theo (cảnh báo nếu stop nằm dưới sàn)
- Số CP, giá trị vị thế, rủi ro VND, %rủi ro thực tế
- Ghi chú T+2.5: "Vốn sẽ bị khoá đến chiều T+2"
- Ràng buộc nào đang binding

## Output Format

### JSON

```json
{
  "schema_version": "1.0",
  "market": "vn",
  "exchange": "hose",
  "symbol": "VIC",
  "mode": "shares",
  "parameters": {
    "account_size_vnd": 1000000000,
    "entry_price": 45000,
    "stop_price": 42000,
    "risk_pct": 1.0,
    "lot_size": 100,
    "broker_fee_pct": 0.15,
    "sale_tax_pct": 0.1
  },
  "vn_market_context": {
    "reference_price": 45000,
    "ceiling_price": 48150,
    "floor_price": 41850,
    "price_band_pct": 7.0,
    "stop_below_floor": false
  },
  "calculations": {
    "fixed_fractional": {
      "method": "fixed_fractional",
      "raw_shares": 3333,
      "lot_rounded_shares": 3300,
      "risk_per_share_vnd": 3000,
      "target_dollar_risk_vnd": 10000000,
      "actual_dollar_risk_vnd": 9900000
    },
    "atr_based": null,
    "kelly": null
  },
  "fees_and_taxes_estimate": {
    "buy_fee_vnd": 222750,
    "sell_fee_vnd_at_entry": 222750,
    "sell_tax_vnd_at_entry": 148500,
    "round_trip_cost_vnd": 594000,
    "round_trip_cost_pct": 0.40
  },
  "constraints_applied": [],
  "final_recommended_shares": 3300,
  "final_position_value_vnd": 148500000,
  "final_risk_vnd": 9900000,
  "final_risk_pct": 0.99,
  "binding_constraint": null,
  "settlement_note": "T+2.5: tiền và CP sẽ thanh toán đầy đủ vào chiều T+2"
}
```

### Markdown

Báo cáo Markdown đi kèm có cùng nội dung, được lưu vào `reports/vn_position_sizer_YYYY-MM-DD_HHMMSS.md`.

## Resources

- `references/vn_sizing_methodologies.md` — Hướng dẫn 3 phương pháp (Fixed Fractional, ATR, Kelly) với ví dụ tiếng Việt
- `scripts/vn_position_sizer.py` — Script tính toán chính (CLI)
- Tham chiếu chéo: `skills/vn-market-mechanics/references/` cho biên độ, lô, phí, thuế

## Nguyên tắc chính

1. **Sống sót trước, lợi nhuận sau** — Position sizing để vượt qua chuỗi thua, không phải tối đa hoá lệnh thắng
2. **Quy tắc 1%** — Mặc định rủi ro 1%/lệnh; **không bao giờ** vượt 2% trừ khi có lý do đặc biệt
3. **Làm tròn xuống lô 100** — Luôn `floor(shares / 100) × 100`; không bao giờ làm tròn lên
4. **Ràng buộc chặt nhất thắng** — Khi có nhiều giới hạn, cái chặt nhất quyết định size cuối
5. **Half-Kelly thôi** — Không bao giờ dùng full Kelly thực tế; half Kelly nắm 75% growth với rủi ro thấp hơn nhiều
6. **Total portfolio heat** — Tổng rủi ro mở không vượt 6-8% tài khoản
7. **Tính cả phí và thuế** — Lợi nhuận sau phí+thuế mới là lợi nhuận thật; break-even cần ≥ 0.4%
8. **T+2.5 nhớ rõ** — Tiền và CP bị khoá đến chiều T+2; quản trị cash flow tương ứng
9. **Stop dưới sàn = stop không hiệu lực phiên đầu** — Nếu stop < floor_price, biên độ sẽ chặn lệnh bán → mất tới 7-15% trước khi exit được
