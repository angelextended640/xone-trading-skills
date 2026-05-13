---
layout: default
title: "Vn Tax Fee Calculator"
grand_parent: English
parent: Skill Guides
nav_order: 11
permalink: /en/skills/vn-tax-fee-calculator/
---

# Vn Tax Fee Calculator
{: .no_toc }

Tính chi tiết phí broker + thuế bán 0.1% + thuế cổ tức 5% + phí lưu ký + phí ứng trước cho giao dịch cổ phiếu Việt Nam. So sánh net return giữa các CTCK (VPS, SSI, VNDirect, HSC, MBS, TCBS, DNSE). Kích hoạt khi user hỏi "phí giao dịch", "thuế chứng khoán", "net P&L sau phí", "so sánh phí giữa các CTCK", "phí cổ tức". Vietnam stock fees + taxes calculator. Broker fee per CTCK, 0.1% sale tax, 5% dividend tax, custody fee, advance-cash fee. Trigger when user asks about fees / taxes / net P&L / broker comparison.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-tax-fee-calculator){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Tax & Fee Calculator — Tính phí và thuế giao dịch CK Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

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

---

## 4. Workflow

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

---

## 5. Resources

**References:**

- `skills/vn-tax-fee-calculator/references/broker_fee_profiles.json`

**Scripts:**

- `skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py`
