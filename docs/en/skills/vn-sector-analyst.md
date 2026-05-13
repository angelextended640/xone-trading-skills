---
layout: default
title: "Vn Sector Analyst"
grand_parent: English
parent: Skill Guides
nav_order: 71
permalink: /en/skills/vn-sector-analyst/
---

# Vn Sector Analyst
{: .no_toc }

Phân tích rotation theo ngành VN-Index — tính return 5D/20D/60D theo ngành, relative strength vs VN-Index, top/bottom mã trong mỗi ngành. Banking ~30% trọng số, Bất động sản ~20%, khác hẳn cấu trúc Mỹ. Tiêu thụ output OHLCV từ vn-data-fetcher. Vietnam sector rotation analysis — sector returns over 5D/20D/60D, relative strength vs VN-Index, top/bottom symbols per sector. Banking dominates ~30% of VN-Index weight, very different from US sector composition.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-sector-analyst){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN Sector Analyst — Phân tích rotation theo ngành VN

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
# Fetch OHLCV cho toàn bộ universe trong sector mapping (mặc định ~80 mã)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,TCB,MBB,ACB,VPB,TPB,STB,HDB,VIC,VHM,VRE,NVL,KDH,DXG,PDR,DIG,HPG,HSG,NKG,DGC,MWG,DGW,PNJ,VNM,MSN,MCH,SAB,GAS,PLX,BSR,PVD,VJC,GMD,FPT,REE,SSI,VCI,HCM,BVH,DHG \
  --start 2026-02-01 --end 2026-05-13 \
  --output-dir reports/

# Cũng lấy VN-Index làm benchmark
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VNINDEX --start 2026-02-01 --end 2026-05-13 \
  --output-dir reports/
```

---

## 4. Workflow

### Bước 1: Lấy OHLCV cho watchlist

```bash
# Fetch OHLCV cho toàn bộ universe trong sector mapping (mặc định ~80 mã)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,TCB,MBB,ACB,VPB,TPB,STB,HDB,VIC,VHM,VRE,NVL,KDH,DXG,PDR,DIG,HPG,HSG,NKG,DGC,MWG,DGW,PNJ,VNM,MSN,MCH,SAB,GAS,PLX,BSR,PVD,VJC,GMD,FPT,REE,SSI,VCI,HCM,BVH,DHG \
  --start 2026-02-01 --end 2026-05-13 \
  --output-dir reports/

# Cũng lấy VN-Index làm benchmark
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VNINDEX --start 2026-02-01 --end 2026-05-13 \
  --output-dir reports/
```

### Bước 2: Phân tích rotation

```bash
python3 skills/vn-sector-analyst/scripts/vn_sector_analyst.py \
  --ohlcv-file reports/vn_ohlcv_*_2026-05-13_*.json \
  --benchmark-file reports/vn_ohlcv_VNINDEX_2026-05-13_*.json \
  --output-dir reports/
```

Hoặc dùng fixture cho test offline:

```bash
python3 skills/vn-sector-analyst/scripts/vn_sector_analyst.py \
  --fixture skills/vn-sector-analyst/scripts/tests/fixtures/sample_batch.json \
  --output-dir reports/
```

### Bước 3: Đọc output

Skill trả về:

- **Bảng ngành xếp hạng:** sector → return_5D, return_20D, return_60D, relative_strength_vs_index
- **Top/bottom 3 mã trong mỗi ngành** theo return 20D
- **Rotation hints:** ngành nào vào uptrend (5D > 20D), ngành nào yếu dần (5D < 20D)
- **Cảnh báo:** nếu Banking weak (RS < −2%) và Real Estate weak → có thể market đang vào risk-off

---

## 5. Resources

**References:**

- `skills/vn-sector-analyst/references/vn_sector_mapping.json`

**Scripts:**

- `skills/vn-sector-analyst/scripts/vn_sector_analyst.py`
