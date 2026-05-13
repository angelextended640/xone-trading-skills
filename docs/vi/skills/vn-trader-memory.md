---
layout: default
title: "Vn Trader Memory"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 11
permalink: /vi/skills/vn-trader-memory/
---

# Vn Trader Memory
{: .no_toc }

Quản lý vòng đời thesis giao dịch cho cổ phiếu Việt Nam — Plan → Trade → Record → Review → Improve. Đăng ký từ vn-*screener output, lifecycle IDEA → ENTRY_READY → ACTIVE → CLOSED, attach position size, generate postmortem với MAE/MFE từ vnstock. VND-aware, lot 100, fee + tax trong realized P&L. Kích hoạt khi user hỏi "ghi thesis", "lifecycle trade", "review nào tới hạn", "postmortem mã VIC", "trade memory". Vietnam trader memory — thesis lifecycle + postmortem for VN equity trades, vnstock-backed (no FMP dependency), VND + lot-100 + fee/tax aware.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-trader-memory){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Trader Memory — Vòng lặp học hỏi cho VN trader

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
# Sau khi vn-vcp-screener output candidates
python3 skills/vn-trader-memory/scripts/vn_thesis_ingest.py \
  --source vn-vcp-screener \
  --input reports/vn_vcp_screener_2026-05-13_*.json \
  --ticker FPT \
  --state-dir state/vn_theses/
```

---

## 4. Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `register` | Đăng ký thesis mới từ vn-*screener JSON output |
| `list` | Liệt kê theses theo filter (status, ticker, sector) |
| `get` | Xem chi tiết một thesis |
| `transition` | Chuyển status (IDEA → ENTRY_READY → ACTIVE → CLOSED) |
| `attach-position` | Gắn output từ vn-position-sizer vào thesis |
| `close` | Đóng vị thế với exit price + date; auto compute net P&L |
| `review-due` | Liệt kê theses tới hạn review |
| `mark-reviewed` | Đánh dấu thesis đã review (cập nhật next_review_date) |
| `postmortem` | Generate markdown journal entry với MAE/MFE từ vnstock |
| `summary` | Stats: win rate, avg P&L%, sector breakdown |

### Bước 1: Register thesis từ screener output

```bash
# Sau khi vn-vcp-screener output candidates
python3 skills/vn-trader-memory/scripts/vn_thesis_ingest.py \
  --source vn-vcp-screener \
  --input reports/vn_vcp_screener_2026-05-13_*.json \
  --ticker FPT \
  --state-dir state/vn_theses/
```

Tạo file `state/vn_theses/th_fpt_pvt_20260513_xxxx.yaml` với status IDEA.

### Bước 2: Attach position size

```bash
# Sau khi vn-position-sizer compute size
python3 skills/vn-trader-memory/scripts/vn_thesis_store.py attach-position \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --position-sizer-output reports/vn_position_sizer_*.json \
  --state-dir state/vn_theses/
```

### Bước 3: Transition lifecycle

```bash
# Sau khi đặt lệnh thành công
python3 skills/vn-trader-memory/scripts/vn_thesis_store.py transition \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --to ACTIVE \
  --actual-entry-price 142000 --actual-entry-date 2026-05-13 \
  --state-dir state/vn_theses/
```

### Bước 4: Review định kỳ

```bash
# Liệt kê theses tới hạn review (default 5 ngày sau entry)
python3 skills/vn-trader-memory/scripts/vn_thesis_review.py review-due \
  --as-of 2026-05-20 \
  --state-dir state/vn_theses/

# Đánh dấu đã review
python3 skills/vn-trader-memory/scripts/vn_thesis_review.py mark-reviewed \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --status OK \
  --note "FPT vẫn trên MA20, room ngoại 99.8%" \
  --state-dir state/vn_theses/
```

### Bước 5: Close + postmortem

```bash
# Đóng vị thế
python3 skills/vn-trader-memory/scripts/vn_thesis_store.py close \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --exit-price 152000 --exit-date 2026-06-04 \
  --exit-reason target_hit \
  --state-dir state/vn_theses/

# Generate postmortem với MAE/MFE
python3 skills/vn-trader-memory/scripts/vn_thesis_review.py postmortem \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --state-dir state/vn_theses/ \
  --journal-dir state/vn_journal/
```

---

## 5. Resources

**References:**

- `skills/vn-trader-memory/references/vn_ingest_adapters.md`

**Scripts:**

- `skills/vn-trader-memory/scripts/vn_price_adapter.py`
- `skills/vn-trader-memory/scripts/vn_thesis_ingest.py`
- `skills/vn-trader-memory/scripts/vn_thesis_review.py`
- `skills/vn-trader-memory/scripts/vn_thesis_store.py`
