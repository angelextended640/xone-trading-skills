---
layout: default
title: "Vn Market Mechanics"
grand_parent: English
parent: Skill Guides
nav_order: 68
permalink: /en/skills/vn-market-mechanics/
---

# Vn Market Mechanics
{: .no_toc }

Cơ chế thị trường chứng khoán Việt Nam — HOSE/HNX/UPCOM, biên độ giá ±7%/±10%/±15%, T+2.5, lô 100, room ngoại, phí giao dịch, thuế. Kích hoạt khi câu hỏi liên quan đến luật/quy tắc/cơ chế giao dịch CK Việt Nam, hoặc khi một skill VN khác cần tham chiếu chuẩn. Vietnam stock market mechanics reference — HOSE/HNX/UPCOM exchanges, ±7%/±10%/±15% daily price limits, T+2.5 settlement, lot size 100, foreign room, fees, taxes. Trigger when user asks about VN market trading rules, or when another vn-* skill needs canonical reference.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-market-mechanics){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Market Mechanics — Kiến thức nền thị trường CK Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

1. Đọc file tham chiếu phù hợp trong `references/` tùy theo câu hỏi:
   - Quy tắc giao dịch chung → `vn_trading_rules.md`
   - Biên độ giá và lệnh → `vn_price_limits_orders.md`
   - Phí và thuế → `vn_fees_and_taxes.md`
   - Room ngoại → `vn_foreign_ownership.md`
   - Nguồn dữ liệu (vnstock) → `vn_data_sources.md`
2. Áp dụng các con số chính xác trong câu trả lời hoặc tính toán
3. Nếu có thay đổi gần đây từ UBCKNN/Sở GDCK, **luôn ghi rõ ngày tham chiếu** của tài liệu và khuyến nghị người dùng kiểm tra lại nguồn chính thức

---

## 4. Workflow

1. Đọc file tham chiếu phù hợp trong `references/` tùy theo câu hỏi:
   - Quy tắc giao dịch chung → `vn_trading_rules.md`
   - Biên độ giá và lệnh → `vn_price_limits_orders.md`
   - Phí và thuế → `vn_fees_and_taxes.md`
   - Room ngoại → `vn_foreign_ownership.md`
   - Nguồn dữ liệu (vnstock) → `vn_data_sources.md`
2. Áp dụng các con số chính xác trong câu trả lời hoặc tính toán
3. Nếu có thay đổi gần đây từ UBCKNN/Sở GDCK, **luôn ghi rõ ngày tham chiếu** của tài liệu và khuyến nghị người dùng kiểm tra lại nguồn chính thức

---

## 5. Resources

**References:**

- `skills/vn-market-mechanics/references/vn_data_sources.md`
- `skills/vn-market-mechanics/references/vn_fees_and_taxes.md`
- `skills/vn-market-mechanics/references/vn_foreign_ownership.md`
- `skills/vn-market-mechanics/references/vn_price_limits_orders.md`
- `skills/vn-market-mechanics/references/vn_trading_rules.md`
