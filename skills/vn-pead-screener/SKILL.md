---
name: vn-pead-screener
description: Sàng lọc setup PEAD (Post-Earnings Announcement Drift) cho thị trường Việt Nam. Hai mode — Mode A scan universe độc lập, Mode B nhận output của vn-earnings-analyzer. Tính chính xác ceiling/floor theo biên độ ±7%/10%/15%, cảnh báo khi stop ≤ floor. R-multiple targets (mặc định 2R). Trigger khi user hỏi "lọc PEAD VN", "FPT đã pullback xong chưa", "post-earnings drift HOSE". Vietnam PEAD screener with proper ±7%/10%/15% ceiling/floor band check and red-candle pullback detection.
---

# VN PEAD Screener — Sàng lọc PEAD (Post-Earnings Drift)

## Tổng quan

PEAD = pattern thực nghiệm: cổ phiếu beat đáng kể tiếp tục **drift** tăng giá trong 5-20 phiên sau ngày báo cáo. Thị trường dưới-phản-ứng với earnings, drift kéo dài để price absorb thông tin.

Setup VN cổ điển:
1. **D0 (earnings day)** — gap up + volume + close near high
2. **D1-D5** — red-candle pullback về vùng `D0_low` đến `D0_close × 0.97`
3. **D5-D15** — `report_day_low` được giữ (chưa thủng đáy)
4. **Entry** — breakout qua `D0_high`

Skill này detect bước 3-4 (đã pullback, đang chờ breakout) và tính:
- Entry = `current_price`
- Stop loss = `report_day_low` (đáy ngày báo cáo)
- Target = `current_price + R × risk` (mặc định 2R)
- **Verify** stop > floor (ceiling/floor theo ±7%/10%/15% mỗi exchange)

## Khi nào dùng

- 1-2 tuần sau mỗi window earnings (Q1 Apr, Q2 Jul-Aug, Q3 Oct, Q4 Jan-Feb)
- Sau khi đã chạy `vn-earnings-analyzer` để có grade A/B candidates (Mode B)
- Hoặc khi user cung cấp universe tự build (Mode A)

**KHÔNG dùng khi:**

- Không có universe (cần grade + report_day_low + current_price min)
- Thị trường downtrend mạnh (M-pillar fail từ `vn-sector-analyst`)
- Cổ phiếu thủng `report_day_low` rồi (setup invalidated)

## Workflow

### Mode A — Standalone universe scan

Build universe JSON với fields cần thiết:

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

```bash
python skills/vn-pead-screener/scripts/vn_pead_screener.py \
  --candidates my_pead_candidates.json \
  --min-grade B \
  --r-targets 1,2,3 \
  --output-dir reports/
```

### Mode B — Pipeline từ vn-earnings-analyzer

Chạy analyzer trước, output của nó là input cho PEAD:

```bash
# 1. Earnings analyzer
python skills/vn-earnings-analyzer/scripts/vn_earnings_analyzer.py \
  --input my_earnings.json --output-dir reports/

# 2. PEAD screener nhận output JSON
python skills/vn-pead-screener/scripts/vn_pead_screener.py \
  --candidates reports/vn_earnings_analyzer_<timestamp>.json \
  --min-grade B --output-dir reports/
```

Script tự detect Mode A vs B qua schema (list vs `{results: [...]}`).

### Khi có warnings về floor

Nếu output có warning `Stop X ≤ floor Y`:
1. Điều chỉnh stop lên trên floor (nhưng giữ trên cao hơn so với entry để vẫn là long setup)
2. Hoặc skip setup nếu không có level technical hợp lý trên floor

Floor được tính theo exchange:
- HOSE: `reference × (1 − 7%)` round-up to tick (10/50/100 VND)
- HNX: `reference × (1 − 10%)` round-up to 100 VND tick
- UPCOM: `reference × (1 − 15%)` round-up to 100 VND tick

## Output

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T08:30:00+07:00",
  "input_count": 8,
  "valid_count": 3,
  "rejected_count": 5,
  "min_grade": "B",
  "r_multiples": [2.0],
  "results": [
    {
      "symbol": "FPT",
      "grade": "A",
      "report_date": "2026-04-25",
      "exchange": "hose",
      "entry_price_vnd": 142000,
      "stop_loss_vnd": 138000,
      "risk_per_share_vnd": 4000,
      "targets": [{"r_multiple": 2.0, "target_price_vnd": 150000}],
      "target_price_vnd": 150000,
      "r_multiple": 2.0,
      "reference_price_vnd": 142000,
      "ceiling_price_vnd": 151900,
      "floor_price_vnd": 132100,
      "price_band_pct": 7.0,
      "stop_above_floor": true,
      "warnings": []
    }
  ]
}
```

Markdown report là bảng entry/stop/target side-by-side với warnings.

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../vn-market-mechanics/references/vn_trading_rules.md) — T+2.5 (PEAD setup không phù hợp intraday)
- [`vn_price_limits_orders.md`](../vn-market-mechanics/references/vn_price_limits_orders.md) — load-bearing cho ceiling/floor calc
- [`vn_fees_and_taxes.md`](../vn-market-mechanics/references/vn_fees_and_taxes.md) — round-trip 0.4% → 2R target khả thi
- [`vn_data_sources.md`](../vn-market-mechanics/references/vn_data_sources.md) — vnstock OHLCV cho red-candle detection

Chi tiết phương pháp luận + bốn cửa sổ earnings + setup pattern: [`references/vn_pead_methodology.md`](references/vn_pead_methodology.md).
