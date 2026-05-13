---
layout: default
title: "Vn Pullback Screener"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 11
permalink: /vi/skills/vn-pullback-screener/
---

# Vn Pullback Screener
{: .no_toc }

Sàng lọc cổ phiếu Việt Nam đang pullback đẹp trong uptrend. Tìm mã giá điều chỉnh về MA20/MA50, RSI giảm về 35-50, nhưng vẫn giữ trên MA200 và uptrend dài hạn. Yêu cầu OHLCV 200+ phiên từ vn-data-fetcher. Kích hoạt khi user hỏi "tìm mã pullback", "cổ phiếu test MA20/MA50", "cổ phiếu test hỗ trợ", "buy the dip" cho cổ phiếu VN. Vietnam pullback screener — uptrending stocks pulling back to MA20 / MA50 with RSI 35-50, still above MA200. Lower-risk swing entry than breakout buying.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-pullback-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Pullback Screener — Sàng lọc mã pullback trong uptrend

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
# 1. Fetch OHLCV cho universe
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,VIC,VHM,HPG,FPT,MWG,VNM,SSI,GAS \
  --start 2025-07-01 --end 2026-05-13 \
  --output-dir reports/

# 2. Chạy pullback screener
python skills/vn-pullback-screener/scripts/vn_pullback_screener.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-13*.json' \
  --min-pullback-pct 3 --max-pullback-pct 12 \
  --rsi-low 35 --rsi-high 50 \
  --output-dir reports/

# 3. Top candidates → build trade plan
python skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol <top candidate> \
  --pivot <pivot from pullback output> \
  --stop <stop suggested> \
  --setup-type pullback \
  --risk-pct 1.0 \
  --output-dir reports/
```

---

## 4. Workflow

```bash
# 1. Fetch OHLCV cho universe
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,VIC,VHM,HPG,FPT,MWG,VNM,SSI,GAS \
  --start 2025-07-01 --end 2026-05-13 \
  --output-dir reports/

# 2. Chạy pullback screener
python skills/vn-pullback-screener/scripts/vn_pullback_screener.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-13*.json' \
  --min-pullback-pct 3 --max-pullback-pct 12 \
  --rsi-low 35 --rsi-high 50 \
  --output-dir reports/

# 3. Top candidates → build trade plan
python skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol <top candidate> \
  --pivot <pivot from pullback output> \
  --stop <stop suggested> \
  --setup-type pullback \
  --risk-pct 1.0 \
  --output-dir reports/
```

---

## 5. Resources

**References:**

- `skills/vn-pullback-screener/references/vn_pullback_methodology.md`

**Scripts:**

- `skills/vn-pullback-screener/scripts/vn_pullback_screener.py`
