---
name: vn-breakout-trade-planner
description: Lập kế hoạch giao dịch breakout (long) cho cổ phiếu Việt Nam — pivot, stop, target R-multiple, position size lô 100, kiểm tra giá trần/sàn, kế hoạch T+2.5 (ngày sellable đầu tiên), tích hợp ngữ cảnh sector/room ngoại. Plan VN long breakout trades — pivot, stop, R-multiple targets, lot-100 sizing, ceiling/floor checks, T+2.5 sellable-day plan, optional sector + foreign-room context. Trigger when user wants to plan a breakout/pullback/VCP entry on HOSE/HNX/UPCOM stock.
---

# VN Breakout Trade Planner — Lập kế hoạch breakout cổ phiếu Việt Nam

## Tổng quan

Skill **tích hợp** kết hợp các skill VN khác để lập kế hoạch giao dịch breakout long hoàn chỉnh:

- **Position size** với lô 100, biên độ giá, phí + thuế (logic từ `vn-position-sizer`)
- **VN guardrails:**
  - Stop phải nằm trên giá sàn của phiên đầu (nếu không, biên độ sẽ chặn cắt lỗ)
  - Pivot không thể nằm trên giá trần (lệnh breakout không khớp)
  - Plan T+2.5: ngày đầu tiên có thể bán
- **Target levels** R-multiple (mặc định 1R, 2R, 3R)
- **Optional ngữ cảnh:**
  - Sector của mã có đang dẫn dắt không? (feed từ `vn-sector-analyst`)
  - Room ngoại của mã có "hot" không? (feed từ `vn-foreign-room-tracker`)

## Khi nào dùng

- User xác định một setup breakout cụ thể trên cổ phiếu VN
- Cần kế hoạch entry/stop/target trước khi đặt lệnh
- Muốn xác minh setup không vi phạm guardrails VN (biên độ, T+2.5)
- Trước khi commit vốn cho một swing trade

## Điều kiện tiên quyết

- Python 3.9+ (chỉ standard library)
- Không cần API key
- Hữu ích nếu có sẵn output của `vn-sector-analyst` và `vn-foreign-room-tracker`
- Tham chiếu: `skills/vn-market-mechanics/references/`

## Workflow

### Bước 1: Xác định setup

User cung cấp:
- **Symbol + exchange**
- **Setup type:** `breakout` (vượt đỉnh nền), `pullback` (pullback tới EMA/MA), `vcp` (volatility contraction)
- **Pivot price:** mức giá breakout (entry trigger)
- **Stop price:** giá cắt lỗ (mức invalidate setup)
- **Reference price:** giá đóng cửa phiên gần nhất (để tính trần/sàn — tùy chọn, mặc định = pivot)
- **Account size + risk %**
- **Tuỳ chọn:** ATR cho stop-distance gợi ý, target_r_multiples (mặc định 1,2,3)

### Bước 2: Chạy script

```bash
# Breakout cơ bản
python3 skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol VIC --exchange hose \
  --setup-type breakout \
  --pivot 45000 --stop 42000 \
  --risk-pct 1.0 \
  --output-dir reports/

# Pullback với ATR-based stop
python3 skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 500000000 \
  --symbol HPG --exchange hose \
  --setup-type pullback \
  --pivot 28000 --atr 800 --atr-multiplier 2.0 \
  --risk-pct 1.0 --reference-price 27500 \
  --output-dir reports/

# Với ngữ cảnh sector + room
python3 skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol FPT --exchange hose \
  --setup-type breakout \
  --pivot 142000 --stop 135000 \
  --risk-pct 1.0 \
  --sector-analysis-file reports/vn_sector_analysis_2026-05-13_*.json \
  --foreign-room-file reports/vn_foreign_room_report_2026-05-13_*.json \
  --output-dir reports/
```

### Bước 3: Đọc kế hoạch

Output gồm:
- **Vị thế:** số CP (lô 100), giá trị vị thế, rủi ro VND, %rủi ro thực tế
- **Trigger conditions:**
  - Buy: giá ≥ pivot (giả định breakout intraday)
  - Stop: giá ≤ stop (đặt thủ công sau khi mua, hoặc cảnh báo)
- **Targets:**
  - T1 (1R): chốt 1/3
  - T2 (2R): chốt 1/3
  - T3 (3R): trail stop hoặc chốt 1/3
- **VN warnings:**
  - Stop dưới giá sàn → biên độ chặn cắt lỗ
  - Pivot trên giá trần → lệnh không khớp
  - Trên giá trần (giá đã chạy) → setup đã muộn
- **Lịch T+:**
  - D0 (hôm nay): Mua nếu giá vượt pivot
  - D+1, D+2 sáng: CP chưa về tài khoản, không thể bán
  - D+2 chiều: CP về, có thể bán cắt lỗ tích cực
- **Context (nếu có):**
  - Sector của mã đang `leader` / `laggard` / `stable`
  - Room ngoại đang `full` / `high_usage` / `released` / `normal`

## Output Format

```json
{
  "schema_version": "1.0",
  "subcommand": "plan",
  "as_of": "2026-05-13T10:00:00+07:00",
  "symbol": "VIC",
  "exchange": "hose",
  "setup_type": "breakout",
  "trade_plan": {
    "pivot": 45000,
    "stop": 42000,
    "risk_per_share_vnd": 3000,
    "shares": 3300,
    "position_value_vnd": 148500000,
    "risk_vnd": 9900000,
    "risk_pct": 0.99,
    "targets": [
      {"name": "T1 (1R)", "price": 48000, "size_fraction": 0.33},
      {"name": "T2 (2R)", "price": 51000, "size_fraction": 0.33},
      {"name": "T3 (3R)", "price": 54000, "size_fraction": 0.34}
    ]
  },
  "vn_market_context": {
    "reference_price": 45000,
    "ceiling_price": 48150,
    "floor_price": 41850,
    "price_band_pct": 7.0,
    "pivot_below_ceiling": true,
    "stop_above_floor": true,
    "pivot_above_yesterday_close_pct": 0.0
  },
  "fees_and_taxes_estimate": {
    "buy_fee_vnd": 222750,
    "sell_fee_vnd_at_pivot": 222750,
    "sell_tax_vnd_at_pivot": 148500,
    "round_trip_cost_vnd": 594000,
    "round_trip_cost_pct": 0.4
  },
  "t_plus_calendar": {
    "buy_date_label": "D0 (hôm nay)",
    "stock_in_account_label": "D+2 chiều",
    "first_sellable_label": "D+2 chiều",
    "notes": [
      "Không thể bán intraday vào D0",
      "D+1 và sáng D+2: CP chưa về, chỉ có thể đặt lệnh chờ",
      "Stop intraday giả định bằng giá đóng cửa cho đến D+2 chiều"
    ]
  },
  "context": {
    "sector": {"name": "Real Estate", "status": "leader", "rs_20d": 2.5},
    "foreign_room": {"status": "high_usage", "room_used_pct": 92.0, "msg": "..."}
  },
  "warnings": [],
  "checklist": [
    "Đã ghi thesis vào journal",
    "Stop nằm trên giá sàn phiên đầu",
    "Tổng portfolio heat (open risk) ≤ 6-8%",
    "Vị thế ≤ 10% account, ngành ≤ 30%"
  ]
}
```

## Resources

- `scripts/vn_breakout_planner.py` — script chính
- Tham chiếu chéo:
  - `skills/vn-position-sizer/` — chia sẻ logic sizing (vendor inline)
  - `skills/vn-market-mechanics/references/vn_price_limits_orders.md` — biên độ
  - `skills/vn-sector-analyst/` — input sector context
  - `skills/vn-foreign-room-tracker/` — input foreign room context

## Nguyên tắc

1. **Setup invalid → reject, không cố tính** — Pivot trên trần, stop dưới sàn quá xa, hay risk_per_share quá lớn vs giá → fail fast với cảnh báo rõ ràng.
2. **Lô 100 không tránh được** — Sau khi tính shares, làm tròn xuống. Risk thực tế hơi thấp hơn target.
3. **R-multiple targets có ý nghĩa** — Chốt 1/3 mỗi mức để vừa lock profit vừa cho phần còn lại chạy. Nếu user muốn khác, cho phép custom qua `--targets 1,2,3` hoặc `--targets 2,4`.
4. **T+2.5 phải xuất hiện trong plan** — Đây là điểm khác biệt lớn nhất với Mỹ; bỏ sót dễ dẫn tới surprise.
5. **Context optional, không bắt buộc** — User có thể chạy plan mà không cần sector + room data; chúng là bonus.
