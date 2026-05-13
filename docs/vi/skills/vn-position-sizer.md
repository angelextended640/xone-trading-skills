---
layout: default
title: "Vn Position Sizer"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 70
permalink: /vi/skills/vn-position-sizer/
---

# Vn Position Sizer
{: .no_toc }

Tính số cổ phiếu tối ưu cho lệnh mua (long) trên TTCK Việt Nam dựa trên quản trị rủi ro — áp dụng lô 100, biên độ giá trần/sàn, phí môi giới 0.15%, thuế bán 0.1%, T+2.5 settlement. Hỗ trợ Fixed Fractional, ATR-based, Kelly Criterion. Kích hoạt khi user hỏi "mua bao nhiêu CP", "size lệnh", "position sizing cho mã VN" bằng tiếng Việt hoặc Anh. Calculate optimal share count for long stock trades on Vietnam stock market with VN-specific rules — lot size 100, price ceiling/floor, 0.15% broker fee, 0.1% sale tax, T+2.5 settlement. Supports Fixed Fractional, ATR-based, Kelly Criterion.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-position-sizer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Position Sizer — Tính position size cho cổ phiếu Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

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

---

## 4. Workflow

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

---

## 5. Resources

**References:**

- `skills/vn-position-sizer/references/vn_sizing_methodologies.md`

**Scripts:**

- `skills/vn-position-sizer/scripts/vn_position_sizer.py`
