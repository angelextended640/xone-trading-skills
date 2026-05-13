---
name: vn-earnings-analyzer
description: Đánh giá phản ứng giá sau công bố BCTC cho cổ phiếu Việt Nam. Chấm điểm 5 yếu tố — gap %, volume tương đối, xu hướng 20D trước báo cáo, vị trí MA50/MA200, EPS surprise %. Hiệu chỉnh ngưỡng cho biên độ ±7% VN. Mặc định loại Kiểm soát/Hạn chế/Tạm ngừng. Output Grade A→F. Trigger khi user hỏi "BCTC quý 1 mã nào mạnh nhất", "FPT báo cáo tốt thế nào", "earnings season VN ai winner". Vietnam earnings-reaction scorer adapted for ±7% price-band cap.
---

# VN Earnings Analyzer — Đánh giá phản ứng sau BCTC

## Tổng quan

Sau mỗi mùa BCTC (Q1 cuối Apr, Q2 cuối Jul + Aug, Q3 cuối Oct, Q4 cuối Jan + Feb), skill chấm điểm các báo cáo gần đây theo 5 yếu tố:

| Yếu tố | Ngưỡng VN | Ý nghĩa |
| --- | --- | --- |
| **Gap** | `gap_pct ≥ 2.0` | VN ±7% band → gap 2% đã rất mạnh |
| **Volume** | `volume_relative ≥ 1.5×` | Volume = 1.5× trung bình 20 phiên |
| **Trend 20D** | `trend_20d_pct ≥ 0` | Up-trend trước báo cáo + báo cáo positive = momentum kép |
| **MA position** | trên cả MA50 **và** MA200 | Long-term trend intact |
| **EPS surprise** | `eps_surprise_pct > 0` | Beat estimate (so với YoY hoặc QoQ) |

Output: Grade A (5/5) → F (0-1).

Skill này là tiền đề cho `vn-pead-screener` Mode B — feed output JSON này → screener tìm setup entry sau pullback.

## Khi nào dùng

- 1-2 tuần sau mỗi window earnings (Q1: late Apr; Q2: late Jul + Aug; Q3: late Oct; Q4: Jan-Feb)
- Khi có universe symbols đã công bố BCTC trong 5-10 phiên gần nhất
- Tiền đề cho `vn-pead-screener`

**KHÔNG dùng khi:**

- Không có BCTC gần đây trong window scan
- Universe không có thông tin EPS surprise (skill dùng giá trị 0 → fail EPS beat, hạ grade nhầm)

## Workflow

### Bước 1 — Build earnings.json

Schema (xem `references/vn_earnings_methodology.md` cho chi tiết):

```json
[
  {
    "symbol": "FPT",
    "report_date": "2026-04-25",
    "gap_pct": 2.5,
    "volume_relative": 1.6,
    "trend_20d_pct": 5.0,
    "above_ma50": true,
    "above_ma200": true,
    "eps_surprise_pct": 10.0,
    "has_red_candle_pullback": true,
    "current_price": 142000,
    "report_day_low": 138000,
    "status": "Normal"
  }
]
```

Cách build từ live data:

```bash
# 1. Lấy fundamentals (gồm EPS YoY/QoQ → tính eps_surprise_pct)
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbols FPT,VIC,HPG,MWG,VNM --period quarter

# 2. Lấy OHLCV ±30 phiên quanh ngày báo cáo (tính gap, volume_relative, trend_20d, MA50, MA200)
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols FPT,VIC,HPG,MWG,VNM \
  --start 2026-03-01 --end 2026-05-13

# 3. Tổng hợp manually hoặc nhờ Claude build earnings.json
```

### Bước 2 — Chạy analyzer

```bash
python skills/vn-earnings-analyzer/scripts/vn_earnings_analyzer.py \
  --input my_earnings.json \
  --min-grade B \
  --output-dir reports/
```

Output tại `reports/vn_earnings_analyzer_<timestamp>.{json,md}`.

### Bước 3 — Feed vào PEAD screener

```bash
python skills/vn-pead-screener/scripts/vn_pead_screener.py \
  --candidates reports/vn_earnings_analyzer_<timestamp>.json \
  --output-dir reports/
```

PEAD screener filter grade ≥ B + check red-candle pullback + tính ceiling/floor + stop > floor.

## Output

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T08:30:00+07:00",
  "input_count": 25,
  "scored_count": 8,
  "skipped_count": 2,
  "min_grade": "B",
  "results": [
    {
      "symbol": "FPT",
      "report_date": "2026-04-25",
      "grade": "A",
      "score": 5,
      "factors": {"gap_up": true, "high_volume": true, ...},
      "gap_pct": 2.5,
      "volume_relative": 1.6,
      ...
    }
  ]
}
```

Markdown: bảng `Symbol / Report / Grade / Score / Gap / Vol / Trend / MA / EPS Surprise / Price` với VND format.

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../vn-market-mechanics/references/vn_trading_rules.md) — sessions, status flags
- [`vn_price_limits_orders.md`](../vn-market-mechanics/references/vn_price_limits_orders.md) — biên độ ±7/10/15% cap gap size
- [`vn_fees_and_taxes.md`](../vn-market-mechanics/references/vn_fees_and_taxes.md) — round-trip cost ~0.4%
- [`vn_data_sources.md`](../vn-market-mechanics/references/vn_data_sources.md) — vnstock fundamentals endpoint

Chi tiết methodology + bốn cửa sổ BCTC + calibration: [`references/vn_earnings_methodology.md`](references/vn_earnings_methodology.md).
