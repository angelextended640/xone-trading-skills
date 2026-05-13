---
layout: default
title: "Vn Portfolio Manager"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 69
permalink: /vi/skills/vn-portfolio-manager/
---

# Vn Portfolio Manager
{: .no_toc }

Quản lý danh mục cổ phiếu Việt Nam (VND) — thêm/bớt vị thế, theo dõi P&L sau phí 0.15% và thuế bán 0.1%, phân bổ theo ngành, exposure tổng. Lưu state local dưới state/vn_portfolio/. Kích hoạt khi user muốn theo dõi danh mục, kiểm tra phân bổ ngành, hoặc tính lợi nhuận sau phí thuế cho cổ phiếu VN. Vietnam portfolio manager (VND) — add/remove positions, after-fee/after-tax P&L, sector breakdown, total exposure. Local CSV state under state/vn_portfolio/.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-portfolio-manager){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Portfolio Manager — Quản lý danh mục cổ phiếu Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
# Thêm vị thế VIC: 3300 CP @ 45,000 mua 2026-05-04
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py add \
  --symbol VIC --exchange hose \
  --shares 3300 --avg-price 45000 \
  --buy-date 2026-05-04 --sector "Bất động sản" \
  --state-dir state/vn_portfolio/

# Snapshot với giá hiện tại
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices VIC:46500,HPG:28500,FPT:142000 \
  --state-dir state/vn_portfolio/

# Hoặc nạp giá từ file (output của vn-data-fetcher)
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices-file reports/latest_prices.json \
  --state-dir state/vn_portfolio/

# Tóm tắt với phân bổ ngành
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py summary \
  --prices VIC:46500,HPG:28500,FPT:142000 \
  --account-size 1000000000 \
  --max-position-pct 10 --max-sector-pct 30 \
  --state-dir state/vn_portfolio/ \
  --output-dir reports/

# Đóng vị thế VIC
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py remove \
  --symbol VIC --close-price 47000 --close-date 2026-05-13 \
  --state-dir state/vn_portfolio/
```

---

## 4. Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `add` | Thêm vị thế mới (sau khi mua) |
| `remove` | Đóng một vị thế (sau khi bán) |
| `status` | Snapshot vị thế đang mở với giá hiện tại |
| `summary` | Báo cáo tổng hợp NAV, phân bổ ngành, top winners/losers |
| `closed` | Liệt kê giao dịch đã đóng |

### Lệnh mẫu

```bash
# Thêm vị thế VIC: 3300 CP @ 45,000 mua 2026-05-04
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py add \
  --symbol VIC --exchange hose \
  --shares 3300 --avg-price 45000 \
  --buy-date 2026-05-04 --sector "Bất động sản" \
  --state-dir state/vn_portfolio/

# Snapshot với giá hiện tại
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices VIC:46500,HPG:28500,FPT:142000 \
  --state-dir state/vn_portfolio/

# Hoặc nạp giá từ file (output của vn-data-fetcher)
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices-file reports/latest_prices.json \
  --state-dir state/vn_portfolio/

# Tóm tắt với phân bổ ngành
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py summary \
  --prices VIC:46500,HPG:28500,FPT:142000 \
  --account-size 1000000000 \
  --max-position-pct 10 --max-sector-pct 30 \
  --state-dir state/vn_portfolio/ \
  --output-dir reports/

# Đóng vị thế VIC
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py remove \
  --symbol VIC --close-price 47000 --close-date 2026-05-13 \
  --state-dir state/vn_portfolio/
```

### Pipeline với vn-data-fetcher

```bash
# Lấy giá đóng cửa mới nhất
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VIC,HPG,FPT --start 2026-05-12 --end 2026-05-13 \
  --output-dir /tmp/

# Tạo file prices.json (manual hoặc qua small helper script)
# Format: {"VIC": 46500, "HPG": 28500, "FPT": 142000}

# Run status với file prices
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices-file /tmp/prices.json --state-dir state/vn_portfolio/
```

---

## 5. Resources

**Scripts:**

- `skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py`
