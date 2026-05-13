---
layout: default
title: "Vn Breakout Trade Planner"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 65
permalink: /vi/skills/vn-breakout-trade-planner/
---

# Vn Breakout Trade Planner
{: .no_toc }

Lập kế hoạch giao dịch breakout (long) cho cổ phiếu Việt Nam — pivot, stop, target R-multiple, position size lô 100, kiểm tra giá trần/sàn, kế hoạch T+2.5 (ngày sellable đầu tiên), tích hợp ngữ cảnh sector/room ngoại. Plan VN long breakout trades — pivot, stop, R-multiple targets, lot-100 sizing, ceiling/floor checks, T+2.5 sellable-day plan, optional sector + foreign-room context. Trigger when user wants to plan a breakout/pullback/VCP entry on HOSE/HNX/UPCOM stock.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-breakout-trade-planner){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Breakout Trade Planner — Lập kế hoạch breakout cổ phiếu Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

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

---

## 4. Workflow

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

---

## 5. Resources

**Scripts:**

- `skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py`
