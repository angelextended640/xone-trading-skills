---
layout: default
title: "Vn Foreign Room Tracker"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 67
permalink: /vi/skills/vn-foreign-room-tracker/
---

# Vn Foreign Room Tracker
{: .no_toc }

Theo dõi room ngoại (foreign ownership room) cho watchlist cổ phiếu HOSE/HNX. Lưu snapshot hàng ngày, phát hiện room đầy / room giải phóng, alert thay đổi đột biến. State CSV dưới state/vn_foreign_room/. Kích hoạt khi user muốn theo dõi sở hữu khối ngoại, kiểm tra room còn lại cho mã, hoặc nhận alert về thay đổi room. Vietnam foreign ownership room tracker for HOSE/HNX watchlists — daily snapshots, full-room/release detection, change alerts. Local CSV state.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-foreign-room-tracker){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Foreign Room Tracker — Theo dõi room ngoại

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
# 1. Tạo CSV input (manual nhập từ bảng giá CTCK)
cat > /tmp/today_room.csv <<EOF
symbol,room_total,room_used,room_remaining
VIC,1869983116,1812345678,57637438
FPT,981234567,981234567,0
HPG,2456789012,1456789012,1000000000
MWG,584567890,584000000,567890
EOF

# 2. Record snapshot vào state
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input /tmp/today_room.csv \
  --as-of 2026-05-13 \
  --state-dir state/vn_foreign_room/

# 3. Báo cáo với alert
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py report \
  --state-dir state/vn_foreign_room/ \
  --output-dir reports/ \
  --full-threshold 99 --release-threshold 90 \
  --lookback-days 5

# 4. Xem history 1 mã
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py history \
  --symbol VIC --days 30 \
  --state-dir state/vn_foreign_room/
```

---

## 4. Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `record` | Ingest CSV/JSON snapshot vào history.csv |
| `report` | Báo cáo room hiện tại + delta + alerts |
| `history` | Xem chuỗi thời gian của 1 mã |

### Lệnh mẫu

```bash
# 1. Tạo CSV input (manual nhập từ bảng giá CTCK)
cat > /tmp/today_room.csv <<EOF
symbol,room_total,room_used,room_remaining
VIC,1869983116,1812345678,57637438
FPT,981234567,981234567,0
HPG,2456789012,1456789012,1000000000
MWG,584567890,584000000,567890
EOF

# 2. Record snapshot vào state
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input /tmp/today_room.csv \
  --as-of 2026-05-13 \
  --state-dir state/vn_foreign_room/

# 3. Báo cáo với alert
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py report \
  --state-dir state/vn_foreign_room/ \
  --output-dir reports/ \
  --full-threshold 99 --release-threshold 90 \
  --lookback-days 5

# 4. Xem history 1 mã
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py history \
  --symbol VIC --days 30 \
  --state-dir state/vn_foreign_room/
```

---

## 5. Resources

**Scripts:**

- `skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py`
