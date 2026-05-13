# VN PEAD Screener — Phương pháp luận

## PEAD là gì?

**Post-Earnings Announcement Drift** — pattern thực nghiệm: cổ phiếu beat đáng kể tiếp tục tăng giá trong 5-60 phiên giao dịch sau ngày báo cáo, do thị trường **dưới-phản-ứng** với thông tin earnings.

Lý do giả định:
1. Phân tích viên cập nhật forecast chậm
2. Quỹ đầu tư tổ chức tích luỹ position trong nhiều phiên
3. Retail mất nhiều phiên để nhận ra báo cáo positive

Trên VN, drift thường 5-20 phiên do market nhỏ hơn + price band cap ±7% kéo dài quá trình release thông tin.

## Bốn cửa sổ KQKD VN — khi nào PEAD setup nhiều

| Quý | Window công bố | Window setup PEAD (5-20 phiên sau) |
| --- | --- | --- |
| Q4 (năm trước) | Mid Jan – Feb | Late Jan – early Mar |
| Q1 | Late Apr | Early – mid May |
| Q2 (bán niên) | Late Jul – Aug | Mid Aug – early Sep |
| Q3 | Late Oct – early Nov | Mid Nov – early Dec |

## Pattern cụ thể: Red-candle pullback then breakout

Setup VN PEAD cổ điển:

1. **Earnings day (D0)** — gap up + volume + close gần đỉnh phiên
2. **D1-D5: Pullback (red candle)** — giá pullback về vùng `D0_low` đến `D0_close * 0.97`
3. **D5-D15: Holding the low** — `report_day_low` được giữ; có 2-3 candle dừng ở vùng đó
4. **Breakout entry** — giá vượt qua `D0_high` (đỉnh ngày báo cáo)

Skill này detect bước 3-4 (cổ phiếu đã pullback, đang chờ breakout):
- Filter `grade ≥ B` từ `vn-earnings-analyzer`
- Yêu cầu `has_red_candle_pullback = True`
- Verify `current_price > report_day_low` (chưa thủng đáy)

## Ceiling/Floor calculation VN

**Mỗi entry plan VN phải tính chính xác ceiling/floor theo exchange:**

| Exchange | Band ± | Tick (theo giá) |
| --- | --- | --- |
| HOSE | 7% | <10k: 10 VND; <50k: 50; ≥50k: 100 |
| HNX | 10% | 100 VND uniform |
| UPCOM | 15% | 100 VND uniform |

Công thức:
```
ceiling_price = reference_price × (1 + band%)  → round down to tick
floor_price   = reference_price × (1 - band%)  → round up to tick
```

Trong đó `reference_price` = giá tham chiếu phiên (T-1 close).

**Stop-loss MUST be above floor_price**, nếu không lệnh cắt lỗ sẽ bị chặn bởi biên độ phiên đầu — không thể thực thi.

## Hai mode

### Mode A — Standalone universe scan

Scan universe symbols (không cần earnings analyzer output) với data đầy đủ về gần đây earnings + price levels. Phù hợp khi user muốn scan rộng.

Input schema:
```json
[
  {
    "symbol": "FPT",
    "report_date": "2026-04-25",
    "grade": "B",
    "current_price": 142000,
    "report_day_low": 138000,
    "reference_price": 142000,
    "exchange": "hose",
    "has_red_candle_pullback": true
  }
]
```

### Mode B — Pipeline từ vn-earnings-analyzer

Nhận output JSON của `vn-earnings-analyzer` (schema: `{results: [...]}`), filter grade ≥ B, screen như Mode A.

## R-multiple targets

Mặc định 2R target:
```
risk = current_price - stop_loss (report_day_low)
target = current_price + 2 × risk
```

Có thể configure khác qua `--r-targets 1,2,3` để có 3 partial exits.

## Output

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T08:30:00+07:00",
  "input_count": 8,
  "valid_count": 3,
  "results": [
    {
      "symbol": "FPT",
      "grade": "B",
      "entry_price_vnd": 142000,
      "stop_loss_vnd": 138000,
      "target_price_vnd": 150000,
      "risk_per_share_vnd": 4000,
      "r_multiple": 2.0,
      "exchange": "hose",
      "reference_price_vnd": 142000,
      "ceiling_price_vnd": 151900,
      "floor_price_vnd": 132100,
      "stop_above_floor": true,
      "warnings": []
    }
  ]
}
```

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../../vn-market-mechanics/references/vn_trading_rules.md) — T+2.5, sessions
- [`vn_price_limits_orders.md`](../../vn-market-mechanics/references/vn_price_limits_orders.md) — ceiling/floor + tick size cho mỗi exchange (LOAD-BEARING cho mode A)
- [`vn_fees_and_taxes.md`](../../vn-market-mechanics/references/vn_fees_and_taxes.md) — round-trip 0.4% → 2R target khả thi
- [`vn_data_sources.md`](../../vn-market-mechanics/references/vn_data_sources.md) — OHLCV để xác định `report_day_low` và `has_red_candle_pullback`

## Lưu ý

- **PEAD không phải breakout trade**: stop-loss đặt tại `report_day_low`, không phải pivot. Nếu giá thủng đáy → invalidate.
- Khi `current_price ≤ report_day_low` → screener loại; setup invalidated.
- Khi `stop_loss < floor_price` → screener vẫn output nhưng có warning; user cần điều chỉnh stop hoặc skip entry.
- Cần `vn-margin-rules-monitor check --symbol X --warn-q-rated` trước khi đặt lệnh — Q-rated cắt margin có thể ép thoát vị thế.
