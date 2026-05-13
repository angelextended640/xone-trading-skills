---
name: vn-dividend-screener
description: Sàng lọc cổ phiếu cổ tức cao bền vững cho Core portfolio Việt Nam. Filter theo yield, payout ratio, EPS growth, ROE, debt. Phát hiện yield trap (yield cao nhưng EPS giảm). Đầu vào JSON universe có dividend history + fundamentals. Kích hoạt khi user hỏi "tìm cổ phiếu cổ tức", "yield cao bền vững", "dividend safe", "income portfolio" cho cổ phiếu VN. Vietnam dividend-stock screener — yield + sustainability + growth quality + yield trap detection. Geared for Core (income) portfolio building.
---

# VN Dividend Screener — Sàng lọc cổ phiếu cổ tức VN

## Tổng quan

Sàng lọc cổ phiếu **cổ tức cao bền vững** cho Core (income) portfolio Việt Nam. Skill này tránh "yield trap" (yield cao do giá giảm, EPS đi xuống) và ưu tiên cổ phiếu có:

- **Yield hấp dẫn** (4%+ trên giá hiện tại)
- **Payout ratio bền vững** (< 80% — còn dư địa giữ cổ tức trong khó khăn)
- **EPS không suy giảm** trong 3 năm gần
- **Chất lượng tài chính:** ROE > 12%, D/E hợp lý
- **Sector diversification awareness**

5 components scoring → grade A / B / C.

## Khi nào dùng

- Xây dựng Core (income) portfolio dài hạn
- Tìm cổ phiếu blue-chip có cổ tức ổn định để giữ qua chu kỳ
- Re-balance income portfolio hàng quý / năm
- Kết hợp với `vn-tax-fee-calculator dividend` để tính net cash income sau thuế 5%

**KHÔNG** dùng cho:
- Swing trading ngắn hạn (đó là việc của `vn-vcp-screener` / `vn-pullback-screener`)
- Cổ phiếu mới niêm yết chưa có dividend history

## Điều kiện tiên quyết

- Python 3.9+ (chỉ standard library)
- Universe JSON với dividend history + fundamentals (xem schema bên dưới)
- Tham chiếu: `references/vn_dividend_methodology.md`

## Workflow

### Bước 1: Chuẩn bị Universe JSON

Tạo file `universe.json` với schema:

```json
{
  "as_of": "2026-05-13",
  "universe": [
    {
      "symbol": "NT2",
      "exchange": "hose",
      "sector": "Utilities",
      "current_price": 32500,
      "market_cap_vnd": 12500000000000,
      "fundamentals": {
        "eps_ttm_vnd": 4200,
        "eps_3y_cagr_pct": 8.5,
        "payout_ratio_pct": 65.0,
        "roe_pct": 18.2,
        "debt_to_equity": 0.6
      },
      "dividend_history": [
        {"year": 2025, "type": "cash", "amount_vnd_per_share": 2500},
        {"year": 2024, "type": "cash", "amount_vnd_per_share": 2200},
        {"year": 2023, "type": "cash", "amount_vnd_per_share": 2000},
        {"year": 2022, "type": "cash", "amount_vnd_per_share": 1800}
      ]
    }
  ]
}
```

User có thể build universe.json:
- **Manual:** copy từ trang công ty, báo cáo phân tích CTCK
- **Future:** `vn-data-fetcher dividends --symbols ... ` (sắp ra mắt)

### Bước 2: Chạy screener

```bash
python skills/vn-dividend-screener/scripts/vn_dividend_screener.py \
  --universe universe.json \
  --min-yield 4.0 \
  --max-payout 80.0 \
  --min-roe 12.0 \
  --min-eps-3y-cagr -5.0 \
  --output-dir reports/
```

### Bước 3: Đọc output

Output:
- **Candidates list:** ranked by score
- **Yield traps:** mã yield cao nhưng failed sustainability
- **Sector breakdown:** đa dạng hoá theo ngành

### Bước 4: Apply tax + position-sizing

```bash
# Tính net dividend income sau thuế 5%
python skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py dividend \
  --shares 1000 --dividend-per-share 2500 \
  --output-dir reports/

# Build position size cho long-term hold
python skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol NT2 --exchange hose \
  --entry 32500 --stop 28000 \
  --risk-pct 0.5 \
  --output-dir reports/
```

## Tiêu chí scoring (5 components)

| Component | Weight | Pass criteria |
| --- | --- | --- |
| **Yield** | 25 | Current dividend yield ≥ 4% (target tier) |
| **Payout sustainability** | 25 | Payout ratio ≤ 80% AND EPS_TTM > 0 |
| **Dividend growth** | 20 | Average annual dividend growth ≥ 0% over 3-4y (no cuts) |
| **Financial quality** | 20 | ROE ≥ 12% AND D/E ≤ 1.5 |
| **EPS trajectory** | 10 | EPS 3y CAGR ≥ −5% (not collapsing) |

### Grade

- **A (80-100):** All 5 criteria met; ideal income holding
- **B (60-79):** 4/5 criteria; viable with smaller weight
- **C (40-59):** Income-only, monitor quality
- **<40 OR yield trap:** Reject

### Yield trap detection

Một mã bị flag là **yield trap** nếu:
- Yield > 8% (suspiciously high) AND
- EPS 3y CAGR < −10% OR payout > 100%

Yield trap được reject ngay, không qua grading.

## Output Format

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T10:00:00+07:00",
  "universe_size": 25,
  "candidates_count": 8,
  "yield_traps_count": 2,
  "rejected_count": 15,
  "candidates": [
    {
      "symbol": "NT2",
      "exchange": "hose",
      "sector": "Utilities",
      "grade": "A",
      "score": 88,
      "components": {
        "yield": 22,
        "payout_sustainability": 25,
        "dividend_growth": 18,
        "financial_quality": 18,
        "eps_trajectory": 10
      },
      "current_price": 32500,
      "current_yield_pct": 7.69,
      "last_dividend_vnd": 2500,
      "dividend_3y_cagr_pct": 11.6,
      "payout_ratio_pct": 65.0,
      "eps_ttm_vnd": 4200,
      "eps_3y_cagr_pct": 8.5,
      "roe_pct": 18.2,
      "debt_to_equity": 0.6,
      "consecutive_paying_years": 4,
      "is_yield_trap": false,
      "notes": ["Steady utility — predictable cash flows", "Yield 7.69% > 4% target"]
    }
  ],
  "yield_traps": [
    {
      "symbol": "XYZ",
      "current_yield_pct": 12.5,
      "eps_3y_cagr_pct": -25.0,
      "payout_ratio_pct": 110.0,
      "trap_reasons": ["EPS declining 25%/year", "Payout > 100% — unsustainable"]
    }
  ],
  "sector_distribution": {
    "Utilities": 3,
    "Banking": 2,
    "Consumer Staples": 2,
    "Real Estate": 1
  }
}
```

## Resources

- `references/vn_dividend_methodology.md` — Methodology + VN-specific notes
- `references/sample_universe.json` — Example universe input
- `scripts/vn_dividend_screener.py` — Main script
- Cross-references:
  - `skills/vn-tax-fee-calculator/` — Net dividend after 5% tax
  - `skills/vn-portfolio-manager/` — Track income portfolio

## Nguyên tắc

1. **Yield không phải tất cả** — Yield 12% với EPS sụp đổ = yield trap. Yield 5% bền vững > yield 10% sắp cắt.
2. **Payout < 80% là benchmark VN** — Cổ phiếu VN tăng trưởng nhanh hơn US average; payout cao như US (90%+) ít gặp ở blue-chip VN healthy.
3. **Stock dividend != cash dividend** — Chỉ tính dividend tiền mặt cho yield calculation. Stock dividend là pha loãng (giảm giá tự động).
4. **Tax-adjusted yield** — 5% thuế cổ tức → net yield = gross yield × 0.95. Combine với `vn-tax-fee-calculator`.
5. **Diversify by sector** — Đừng tập trung vào 1 ngành cổ tức (utilities, banking, REIT). Lý tưởng: top 5 holdings ở 4+ sectors.
6. **Review yearly** — Dividend history thay đổi. Re-screen mỗi năm (sau mùa AGM tháng 4-6).
