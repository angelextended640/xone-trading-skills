---
layout: default
title: "Vn Dividend Screener"
grand_parent: English
parent: Skill Guides
nav_order: 11
permalink: /en/skills/vn-dividend-screener/
---

# Vn Dividend Screener
{: .no_toc }

Sàng lọc cổ phiếu cổ tức cao bền vững cho Core portfolio Việt Nam. Filter theo yield, payout ratio, EPS growth, ROE, debt. Phát hiện yield trap (yield cao nhưng EPS giảm). Đầu vào JSON universe có dividend history + fundamentals. Kích hoạt khi user hỏi "tìm cổ phiếu cổ tức", "yield cao bền vững", "dividend safe", "income portfolio" cho cổ phiếu VN. Vietnam dividend-stock screener — yield + sustainability + growth quality + yield trap detection. Geared for Core (income) portfolio building.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-dividend-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Dividend Screener — Sàng lọc cổ phiếu cổ tức VN

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
User có thể build universe.json:
- **Manual:** copy từ trang công ty, báo cáo phân tích CTCK
- **Future:** `vn-data-fetcher dividends --symbols ... ` (sắp ra mắt)

### Bước 2: Chạy screener
```

---

## 4. Workflow

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

---

## 5. Resources

**References:**

- `skills/vn-dividend-screener/references/sample_universe.json`
- `skills/vn-dividend-screener/references/vn_dividend_methodology.md`

**Scripts:**

- `skills/vn-dividend-screener/scripts/vn_dividend_screener.py`
