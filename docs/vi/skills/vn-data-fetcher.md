---
layout: default
title: "Vn Data Fetcher"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 11
permalink: /vi/skills/vn-data-fetcher/
---

# Vn Data Fetcher
{: .no_toc }

Lấy dữ liệu thị trường chứng khoán Việt Nam qua thư viện vnstock — OHLCV, thông tin niêm yết, lịch sử cổ tức, fundamentals (P/E, P/B, ROE, EPS, payout), và snapshot khối ngoại. Cache local dưới state/vn_market_data/. Hỗ trợ fixture mode cho test offline. Kích hoạt khi cần lấy giá lịch sử, thông tin niêm yết, cổ tức, hoặc tỷ số tài chính cho cổ phiếu HOSE/HNX/UPCOM. Vietnam stock data fetcher — OHLCV, info, dividends, fundamentals (ratios), foreign-flow snapshot via vnstock.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-data-fetcher){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Data Fetcher — Lấy dữ liệu thị trường CK Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
# OHLCV: 1 mã, 1 ngày tròn năm
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2025-05-01 --end 2026-05-12 \
  --interval 1D --source VCI \
  --output-dir reports/

# OHLCV: nhiều mã batch
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VIC,HPG,VNM,FPT \
  --start 2026-01-01 --end 2026-05-12 \
  --output-dir reports/

# Info công ty
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py info \
  --symbol VIC --source VCI \
  --output-dir reports/

# Foreign flow snapshot (point-in-time)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py foreign-flow \
  --symbol VIC \
  --output-dir reports/

# Lịch sử cổ tức (cash + stock)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py dividends \
  --symbol VIC --source VCI \
  --output-dir reports/

# Fundamentals theo quý (P/E, P/B, ROE, EPS, payout)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbol VIC --period quarter \
  --output-dir reports/

# Fundamentals theo năm
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbol VIC --period year \
  --output-dir reports/

# Test offline với fixture
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2026-05-01 --end 2026-05-12 \
  --fixture tests/fixtures/vic_daily.csv \
  --output-dir reports/

# Skip cache (lấy data tươi)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2026-05-01 --end 2026-05-12 \
  --no-cache --output-dir reports/
```

---

## 4. Workflow

### Bước 1: Xác định subcommand

| Subcommand | Mục đích |
| --- | --- |
| `ohlcv` | Open/High/Low/Close/Volume theo ngày, tuần, tháng, hoặc intraday |
| `info` | Thông tin niêm yết (sàn, ngành, vốn hoá, số CP lưu hành) |
| `dividends` | Lịch sử cổ tức (cash + stock). Tự động phân loại type, convert % → VND/CP |
| `fundamentals` | Báo cáo tỷ số tài chính theo `quarter` hoặc `year` (P/E, P/B, ROE, EPS, payout) |
| `foreign-flow` | Snapshot khối ngoại (point-in-time only — không có daily series) |

> **Lưu ý:** `foreign-flow` chỉ trả snapshot tại thời điểm gọi. vnstock không cung cấp daily-series endpoint thống nhất cho khối ngoại. Để xây history theo ngày, dùng `vn-foreign-room-tracker record` với CSV nhập thủ công.

### Bước 2: Chạy lệnh

```bash
# OHLCV: 1 mã, 1 ngày tròn năm
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2025-05-01 --end 2026-05-12 \
  --interval 1D --source VCI \
  --output-dir reports/

# OHLCV: nhiều mã batch
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VIC,HPG,VNM,FPT \
  --start 2026-01-01 --end 2026-05-12 \
  --output-dir reports/

# Info công ty
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py info \
  --symbol VIC --source VCI \
  --output-dir reports/

# Foreign flow snapshot (point-in-time)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py foreign-flow \
  --symbol VIC \
  --output-dir reports/

# Lịch sử cổ tức (cash + stock)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py dividends \
  --symbol VIC --source VCI \
  --output-dir reports/

# Fundamentals theo quý (P/E, P/B, ROE, EPS, payout)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbol VIC --period quarter \
  --output-dir reports/

# Fundamentals theo năm
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbol VIC --period year \
  --output-dir reports/

# Test offline với fixture
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2026-05-01 --end 2026-05-12 \
  --fixture tests/fixtures/vic_daily.csv \
  --output-dir reports/

# Skip cache (lấy data tươi)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2026-05-01 --end 2026-05-12 \
  --no-cache --output-dir reports/
```

### Bước 3: Đọc output

Mỗi lệnh xuất hai file:

- `<symbol>_<subcommand>_<timestamp>.json` — metadata + dữ liệu (record-oriented)
- `<symbol>_<subcommand>_<timestamp>.csv` (cho ohlcv) — CSV phẳng dễ đọc

Cache lưu tại `state/vn_market_data/<symbol>_<source>_<interval>.csv` — không có timestamp; lần fetch sau cùng phủ lên (full refresh).

### Bước 4: Báo cáo cho user

Tóm tắt số dòng, khoảng ngày, mã, và ghi chú nếu data thiếu hoặc có gap.

---

## 5. Resources

**Scripts:**

- `skills/vn-data-fetcher/scripts/vn_data_fetcher.py`
