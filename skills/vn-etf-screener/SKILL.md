---
name: vn-etf-screener
description: Sàng lọc các quỹ ETF niêm yết tại Việt Nam (E1VFVN30, FUEVFVND, FUESSV50, FUEVN100, ...) dựa trên 4 yếu tố — tracking error, premium/discount NAV, expense ratio, thanh khoản 20 ngày. Grade A→F. Phù hợp chọn Core portfolio passive sleeve. Trigger khi user hỏi "ETF VN tốt nhất", "chọn ETF cho danh mục dài hạn", "VFMVN30 vs Diamond ETF". Vietnam-listed ETF screener for Core portfolio passive sleeve selection.
---

# Lọc Chứng chỉ quỹ (VN ETF Screener)

## Tổng quan

Đánh giá các ETF niêm yết HOSE/HNX theo 4 yếu tố:

| Yếu tố | Ngưỡng "đạt" | Ý nghĩa |
| --- | --- | --- |
| **Tracking Error** | ≤ 1.0% | TE thấp = bám index sát |
| **Premium/Discount NAV** | abs ≤ 1.0% | Market efficient, không overpay/underpay |
| **Expense Ratio** | ≤ 0.7%/năm | Phí thấp = compound nhanh hơn |
| **Volume 20D** | ≥ 100,000 CCQ | Đủ thanh khoản |

Output là grade A/B/C/D/F. ETF grade A đủ điều kiện làm Core portfolio passive sleeve (long-term hold).

## Khi nào dùng

- Chọn ETF cho **Core sleeve** của Core+Satellite portfolio (passive backbone)
- So sánh các ETF cùng track 1 index (E1VFVN30 vs FUESSV30 — cả 2 đều track VN30)
- Định kỳ quarterly review để xem ETF nắm giữ còn "khoẻ" không (TE drift?)

**KHÔNG dùng để:**

- Swing trade ETF — ETF không phù hợp short-term trading do TE + premium/discount drift
- Phân tích sector ETF của thị trường Mỹ — skill này chỉ cho VN

## Workflow

### Bước 1 — Cập nhật universe JSON

```bash
# Mở references/vn_etf_list.json và cập nhật nav_per_share / market_price / volume_20d_avg
# từ bảng giá CTCK hoặc HOSE. Tracking error + expense ratio lấy từ fact sheet quỹ.
```

### Bước 2 — Chạy screener

```bash
python skills/vn-etf-screener/scripts/vn_etf_screener.py \
  --input skills/vn-etf-screener/references/vn_etf_list.json \
  --output-dir reports/

# Bao gồm cả ETF bị flag (Kiểm soát/Hạn chế) — mặc định loại
python skills/vn-etf-screener/scripts/vn_etf_screener.py \
  --input ... --include-flagged
```

### Bước 3 — Đọc báo cáo

Báo cáo tại `reports/vn_etf_screener_<timestamp>.{json,md}`. Markdown có bảng so sánh side-by-side; JSON cho integration với `vn-trader-memory` (khi register ETF làm long-term hold).

## Output

`vn_etf_screener_<timestamp>.json` cấu trúc:

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T08:30:00+07:00",
  "universe_size": 5,
  "scored_count": 5,
  "skipped_count": 0,
  "results": [
    {
      "symbol": "E1VFVN30",
      "grade": "A",
      "score": 4,
      "factors": {"low_tracking_error": true, ...},
      "nav_per_share_vnd": 21500,
      "market_price_vnd": 21600,
      "premium_discount_vnd": 100,
      "premium_discount_pct": 0.465,
      "tracking_error_pct": 0.8,
      "expense_ratio_pct": 0.65,
      "volume_20d_avg": 1500000
    }
  ]
}
```

Markdown report là bảng cùng dữ liệu với VND format thousands separators.

## Tham chiếu vn-market-mechanics

- [`vn_foreign_ownership.md`](../vn-market-mechanics/references/vn_foreign_ownership.md) — ETF Diamond bypass room ngoại
- [`vn_fees_and_taxes.md`](../vn-market-mechanics/references/vn_fees_and_taxes.md) — phí ETF giống phí cổ phiếu
- [`vn_price_limits_orders.md`](../vn-market-mechanics/references/vn_price_limits_orders.md) — ETF tuân thủ ±7%/lô 100/tick size như cổ phiếu

Chi tiết methodology + universe ETF chính: [`references/vn_etf_methodology.md`](references/vn_etf_methodology.md).
