---
layout: default
title: "Vn30 Derivatives Planner"
grand_parent: English
parent: Skill Guides
nav_order: 11
permalink: /en/skills/vn30-derivatives-planner/
---

# Vn30 Derivatives Planner
{: .no_toc }

Lập kế hoạch giao dịch phái sinh VN30 Futures (VN30F1M, VN30F2M, VN30F1Q, VN30F2Q). Tính roll calendar, basis vs spot, hedge sizing cho exposure cash equity, full short trade plan với IM + max loss, so sánh chi phí giữa CTCK. T+0 settlement — short tool hợp pháp duy nhất ở VN. Kích hoạt khi user hỏi "VN30 futures", "phái sinh", "short VN30", "hedge danh mục", "roll hợp đồng". Vietnam VN30 Index Futures planner — roll, hedge sizing, short trade plan, broker cost comparison. The only legal short-exposure tool on Vietnam markets.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn30-derivatives-planner){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN30 Derivatives Planner — Phái sinh VN30 Futures

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py roll \
  --current-contract VN30F1M \
  --reference-date 2026-05-13 \
  --vn30-spot 1280.5 --futures-price 1283.0 \
  --output-dir reports/
```

---

## 4. Workflow

### Subcommands

#### `roll` — Roll calendar + basis

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py roll \
  --current-contract VN30F1M \
  --reference-date 2026-05-13 \
  --vn30-spot 1280.5 --futures-price 1283.0 \
  --output-dir reports/
```

Output: ngày roll tới (last Thursday of front month), basis (futures - spot), suggested action.

#### `hedge` — Tính số contract để hedge

```bash
# Bạn có 1B VND cash equity long, beta 1.05 vs VN30; muốn hedge 100%
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py hedge \
  --cash-exposure-vnd 1000000000 \
  --portfolio-beta 1.05 \
  --vn30-spot 1280 \
  --hedge-ratio 1.0 \
  --output-dir reports/
```

Output: số contract cần short, IM cần thiết, notional value, basis-adjusted slippage estimate.

#### `plan` — Full short trade plan

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py plan \
  --account-size 1000000000 \
  --side short \
  --entry 1283.0 --stop 1300.0 \
  --risk-pct 1.0 \
  --output-dir reports/
```

Output: contracts cần thiết, IM bị khóa, max loss, R-multiple targets, T+0 fast-exit note.

#### `cost` — So sánh phí broker

```bash
python skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py cost \
  --contracts 5 --entry 1283.0 --exit 1265.0 \
  --side short \
  --brokers vps,ssi,vndirect,hsc,mbs,tcbs,dnse \
  --output-dir reports/
```

Output: cost / net P&L per broker, spread.

---

## 5. Resources

**References:**

- `skills/vn30-derivatives-planner/references/vn_futures_fees.md`
- `skills/vn30-derivatives-planner/references/vn_futures_mechanics.md`

**Scripts:**

- `skills/vn30-derivatives-planner/scripts/vn30_derivatives_planner.py`
