---
layout: default
title: "Finviz Screener"
grand_parent: Tiếng Việt
parent: Hướng dẫn Kỹ năng
nav_order: 30
permalink: /vi/skills/finviz-screener/
---

# Finviz Screener
{: .no_toc }

Build and open FinViz screener URLs from natural language requests. Use when user wants to screen stocks, find stocks matching criteria, filter by fundamentals or technicals, or asks to open FinViz with specific conditions. Example input: "Find oversold large caps with high ROE".
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span> <span class="badge badge-optional">FINVIZ Optional</span>

[Download Skill Package (.skill)](https://github.com/xonevn-ai/xone-trading-skills/raw/main/skill-packages/finviz-screener.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/finviz-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

Translate natural-language stock screening requests into FinViz screener filter codes, build the URL, and open it in Chrome. No API key required for public screener; FINVIZ Elite is auto-detected from `$FINVIZ_API_KEY` for enhanced functionality.

**Key Features:**
- Natural language → filter code mapping (English)
- URL construction with view type and sort order selection
- Elite/Public auto-detection (environment variable or explicit flag)
- Chrome-first browser opening with OS-appropriate fallbacks
- Strict filter validation to prevent URL injection

---

---

## 2. When to Use

**Explicit Triggers:**
- "Find oversold large caps near 52-week lows"
- "Screen for tech sector value stocks"
- "Show me high-growth small caps on FinViz"
- "Screen for stocks with insider buying"
- "Show me FinViz breakout candidates"
- "Find stocks with dividend yield > 5% and ROE > 15%"

**Implicit Triggers:**
- User describes stock screening criteria using fundamental or technical terms
- User mentions FinViz screener or stock filtering
- User asks to find stocks matching specific financial characteristics

**When NOT to Use:**
- Deep fundamental analysis of a specific stock (use us-stock-analysis)
- Portfolio review with holdings (use portfolio-manager)
- Chart pattern analysis on images (use technical-analyst)
- Earnings-based screening (use earnings-trade-analyzer or pead-screener)

---

---

## 3. Prerequisites

- **FINVIZ Elite** optional (improves performance)
- Public screener free; Elite auto-detected from env var
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
cat references/finviz_screener_filters.md
```

---

## 5. Workflow

### Step 1: Load Filter Reference

Read the filter knowledge base:

```bash
cat references/finviz_screener_filters.md
```

### Step 2: Interpret User Request

Map the user's natural-language request to FinViz filter codes. Use the Common Concept Mapping table below for quick translation, and reference the full filter list for precise code selection.

**Note:** For range criteria (e.g., "dividend 3-8%", "P/E between 10 and 20"), use the `{from}to{to}` range syntax as a single filter token (e.g., `fa_div_3to8`, `fa_pe_10to20`) instead of combining separate `_o` and `_u` filters.

**Common Concept Mapping:**

| User Concept | Filter Codes |
|---|---|
| High dividend | `fa_div_o3` or `fa_div_o5` |
| Small cap | `cap_small` |
| Mid cap | `cap_mid` |
| Large cap | `cap_large` |
| Mega cap | `cap_mega` |
| Value / cheap | `fa_pe_u20,fa_pb_u2` |
| Growth stock | `fa_epsqoq_o25,fa_salesqoq_o15` |
| Oversold | `ta_rsi_os30` |
| Overbought | `ta_rsi_ob70` |
| Near 52W high | `ta_highlow52w_b0to5h` |
| Near 52W low | `ta_highlow52w_a0to5l` |
| Breakout | `ta_highlow52w_b0to5h,sh_relvol_o1.5` |
| Technology | `sec_technology` |
| Healthcare | `sec_healthcare` |
| Energy | `sec_energy` |
| Financial | `sec_financial` |
| Semiconductors | `ind_semiconductors` |
| Biotechnology | `ind_biotechnology` |
| US stocks | `geo_usa` |
| Profitable | `fa_pe_profitable` |
| High ROE | `fa_roe_o15` or `fa_roe_o20` |
| Low debt | `fa_debteq_u0.5` |
| Insider buying | `sh_insidertrans_verypos` |
| Short squeeze | `sh_short_o20,sh_relvol_o2` |
| Dividend growth | `fa_divgrowth_3yo10` |
| Deep value | `fa_pb_u1,fa_pe_u10` |
| Momentum | `ta_perf_13wup,ta_sma50_pa,ta_sma200_pa` |
| Defensive | `ta_beta_u0.5` or `sec_utilities,sec_consumerdefensive` |
| Liquid / high volume | `sh_avgvol_o500` or `sh_avgvol_o1000` |
| Pullback from high | `ta_highlow52w_10to30-bhx` |
| Near 52W low reversal | `ta_highlow52w_10to30-alx` |
| Fallen angel | `ta_highlow52w_b20to30h,ta_rsi_os40` |
| AI theme | `--themes "artificialintelligence"` |
| Cybersecurity theme | `--themes "cybersecurity"` |
| AI + Cybersecurity | `--themes "artificialintelligence,cybersecurity"` |
| AI Cloud sub-theme | `--subthemes "aicloud"` |
| AI Compute sub-theme | `--subthemes "aicompute"` |
| Yield 3-8% (trap excluded) | `fa_div_3to8` |
| Mid-range P/E | `fa_pe_10to20` |
| EV undervalued | `fa_evebitda_u10` |
| Earnings next week | `earningsdate_nextweek` |
| IPO recent | `ipodate_thismonth` |
| Target price above | `targetprice_a20` |
| Recent news | `news_date_today` |
| High institutional | `sh_instown_o60` |
| Low float | `sh_float_u20` |
| Near all-time high | `ta_alltime_b0to5h` |
| High ATR | `ta_averagetruerange_o1.5` |

### Step 3: Present Filter Selection

Before executing, present the selected filters in a table for user confirmation:

```markdown
| Type | Value | Meaning |
|---|---|---|
| Theme | artificialintelligence | Artificial Intelligence |
| Sub-theme | aicloud | AI - Cloud & Infrastructure |
| Filter | cap_small | Small Cap ($300M–$2B) |
| Filter | fa_div_o3 | Dividend Yield > 3% |
| Filter | fa_pe_u20 | P/E < 20 |
| Filter | geo_usa | USA |

View: Overview (v=111)
Mode: Public / Elite (auto-detected)
```

Ask the user to confirm or adjust before proceeding.

### Step 4: Execute Script

Run the screener script to build the URL and open Chrome:

```bash
python3 scripts/open_finviz_screener.py \
  --filters "cap_small,fa_div_o3,fa_pe_u20,geo_usa" \
  --view overview

# Theme-only screening (no --filters required)
python3 scripts/open_finviz_screener.py \
  --themes "artificialintelligence,cybersecurity" \
  --url-only

# Theme + sub-theme + filters combined
python3 scripts/open_finviz_screener.py \
  --themes "artificialintelligence" \
  --subthemes "aicloud,aicompute" \
  --filters "cap_midover" \
  --url-only
```

**Script arguments:**
- `--filters` (optional): Comma-separated filter codes. **Note:** `theme_*` and `subtheme_*` tokens are not allowed here — use `--themes` / `--subthemes` instead.
- `--themes` (optional): Comma-separated theme slugs (e.g., `artificialintelligence,cybersecurity`). Accepts bare slugs or `theme_`-prefixed values.
- `--subthemes` (optional): Comma-separated sub-theme slugs (e.g., `aicloud,aicompute`). Accepts bare slugs or `subtheme_`-prefixed values.
- `--elite`: Force Elite mode (auto-detected from `$FINVIZ_API_KEY` if not set)
- `--view`: View type — overview, valuation, financial, technical, ownership, performance, custom
- `--order`: Sort order (e.g., `-marketcap`, `dividendyield`, `-change`)
- `--url-only`: Print URL without opening browser

At least one of `--filters`, `--themes`, or `--subthemes` must be provided.

### Step 5: Report Results

After opening the screener, report:
1. The constructed URL
2. Elite or Public mode used
3. Summary of applied filters
4. Suggested next steps (e.g., "Sort by dividend yield", "Switch to Financial view for detailed ratios")

---

---

## 6. Resources

**References:**

- `skills/finviz-screener/references/finviz_screener_filters.md`

**Scripts:**

- `skills/finviz-screener/scripts/open_finviz_screener.py`
