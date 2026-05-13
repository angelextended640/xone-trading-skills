---
layout: default
title: "Vn VCP Screener"
grand_parent: English
parent: Skill Guides
nav_order: 11
permalink: /en/skills/vn-vcp-screener/
---

# Vn VCP Screener
{: .no_toc }

Sàng lọc cổ phiếu Việt Nam theo mô hình VCP (Volatility Contraction Pattern) của Mark Minervini, hiệu chỉnh cho biên độ ±7% HOSE. Phát hiện các đợt contraction liên tiếp với range thu hẹp dần, volume giảm dần. Yêu cầu OHLCV ít nhất 60 phiên từ vn-data-fetcher. Kích hoạt khi user hỏi "tìm mã VCP", "stock đang siết biên độ", "breakout candidate kiểu Minervini" cho cổ phiếu VN. Vietnam VCP (Volatility Contraction Pattern) screener — Minervini-style pattern adapted for HOSE ±7% bands. Detects successive volatility contractions with declining volume.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-vcp-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN VCP Screener — Sàng lọc VCP cho cổ phiếu Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,VIC,VHM,HPG,FPT,MWG,VNM,SSI,VCI,GAS,PLX \
  --start 2026-01-01 --end 2026-05-13 \
  --output-dir reports/
```

---

## 4. Workflow

### Bước 1: Lấy OHLCV cho universe

```bash
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,VIC,VHM,HPG,FPT,MWG,VNM,SSI,VCI,GAS,PLX \
  --start 2026-01-01 --end 2026-05-13 \
  --output-dir reports/
```

### Bước 2: Chạy screener

```bash
# Single-symbol mode
python skills/vn-vcp-screener/scripts/vn_vcp_screener.py \
  --ohlcv-file reports/vn_ohlcv_VIC_*.json \
  --output-dir reports/

# Batch mode (consumes multi-symbol JSON)
python skills/vn-vcp-screener/scripts/vn_vcp_screener.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-13*.json' \
  --min-contractions 2 \
  --max-contractions 5 \
  --output-dir reports/
```

### Bước 3: Đọc output

Output JSON gồm:

- **Mỗi mã có VCP detected**: pivot price, stop price gợi ý, contractions detail
- **Score 0-100**: tổng hợp 5 tiêu chí
- **Grade A/B/C**: A = đầy đủ tất cả 5 đặc trưng, B = 4/5, C = 3/5
- **Rejection reasons**: nếu không qua, lý do cụ thể

### Bước 4: Combine với context

```bash
# Lấy top 3 từ VCP output, build trade plan
python skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol <từ VCP output> \
  --pivot <pivot từ VCP> --stop <stop từ VCP> \
  --risk-pct 1.0 \
  --sector-analysis-file reports/vn_sector_*.json \
  --foreign-room-file reports/vn_foreign_room_*.json \
  --output-dir reports/
```

---

## 5. Resources

**References:**

- `skills/vn-vcp-screener/references/vn_vcp_methodology.md`

**Scripts:**

- `skills/vn-vcp-screener/scripts/vn_vcp_screener.py`
