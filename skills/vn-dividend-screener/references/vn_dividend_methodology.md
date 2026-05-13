# VN Dividend Screening Methodology

**Last updated:** 2026-05-13

## Why screen dividends differently in VN

The Vietnamese dividend landscape differs from US in important ways:

| Aspect | US | VN |
| --- | --- | --- |
| Frequency | Quarterly (most common) | Annual (most), some semi-annual |
| Yield range (blue-chip) | 1-4% | 3-8% (higher absolute yields) |
| Tax treatment | Qualified dividends 0-23.8% | Flat 5% withheld at source |
| Payout ratio (typical) | 30-50% | 30-70% |
| Stock dividends | Rare | Very common — every other AGM |
| Special dividends | Occasional | Rare |
| Re-investment | DRIPs common | Rarely offered by broker |

**Key implication:** VN yields look higher in nominal terms, but you need to:
- Distinguish cash dividends from stock dividends (only cash counts for yield)
- Apply 5% tax to get net yield
- Watch for yield trap (companies cutting dividend after a poor year)

## The 5 Quality Pillars

### Pillar 1: Yield (25 points)

Current dividend yield = trailing 12-month cash dividends / current price.

For VN blue-chip universe:
- **< 3%:** Sub-target — skip unless growth story
- **3-4%:** Borderline — pass with caveat
- **4-7%:** Sweet spot — main target zone
- **7-10%:** High yield, scrutinise sustainability
- **> 10%:** Suspicious — likely yield trap unless special situation

Scoring:
- 25 pts: yield 5-8%
- 22 pts: yield 4-5% or 8-10%
- 15 pts: yield 3-4%
- 8 pts: yield 2-3%
- 0 pts: yield < 2%

### Pillar 2: Payout sustainability (25 points)

Payout ratio = annual dividend per share / EPS_TTM.

The VN benchmark for "sustainable":
- **< 50%:** Excellent buffer — can sustain dividend through 2 bad years
- **50-70%:** Healthy — typical for mature VN blue-chip
- **70-80%:** Stretched but workable
- **> 80%:** Marginal — risk of cut if EPS dips
- **> 100%:** Unsustainable — paying out of cash reserves or debt

Scoring:
- 25 pts: payout 30-65%, EPS_TTM > 0
- 20 pts: payout 65-80%, EPS_TTM > 0
- 10 pts: payout < 30% (under-payer; could be conservative or hoarding)
- 0 pts: payout > 80% or EPS_TTM ≤ 0

### Pillar 3: Dividend growth (20 points)

Calculate **dividend 3-year CAGR**:
```
CAGR = (latest_div / div_3y_ago) ^ (1/3) - 1
```

Plus check **consecutive paying years** — how many years did the company pay dividends without skipping?

VN expectations:
- ≥ 4 consecutive years of paying = "track record"
- Positive CAGR = growth
- Negative CAGR or skip year = warning

Scoring:
- 20 pts: 4+ years consecutive, CAGR > +5%
- 15 pts: 4+ years consecutive, CAGR 0% to +5%
- 8 pts: 3 years consecutive, CAGR ≥ 0%
- 0 pts: < 3 years history OR any cut/skip in last 4 years

### Pillar 4: Financial quality (20 points)

Two metrics:
- **ROE (Return on Equity):** sustainability of dividends depends on profitability
- **D/E (Debt to Equity):** highly leveraged companies cut dividends first in downturns

VN benchmarks:
- **ROE > 15%:** strong (most VN blue-chip in this zone)
- **ROE 12-15%:** acceptable
- **ROE < 12%:** weak quality
- **D/E < 1.0:** conservative
- **D/E 1.0-1.5:** moderate (acceptable for banks / property where leverage is structural)
- **D/E > 1.5:** elevated risk

Scoring:
- 20 pts: ROE > 15% AND D/E < 1.0
- 15 pts: ROE 12-15% AND D/E < 1.5
- 8 pts: ROE 10-12% AND D/E < 1.5
- 0 pts: ROE < 10% OR D/E > 1.5

### Pillar 5: EPS trajectory (10 points)

EPS 3-year CAGR. A negative trajectory is the strongest yield-trap signal.

Scoring:
- 10 pts: EPS 3y CAGR > +5%
- 7 pts: EPS 3y CAGR 0% to +5%
- 4 pts: EPS 3y CAGR −5% to 0%
- 0 pts: EPS 3y CAGR < −5%

## Yield trap detection

A stock is flagged as **yield trap** if **all** of:
- Current yield > 8%
- AND (EPS 3y CAGR < −10% OR payout ratio > 100%)

These are auto-rejected, regardless of total score.

Additional warning signs (not auto-reject, but flag):
- Recent dividend cut (latest dividend < previous year)
- Skipped year in last 4
- Sector under structural pressure (e.g., legacy utilities replaced by renewables)

## Sector concentration

VN dividend-yielding sectors:
- **Utilities** (NT2, PPC, GEG) — most stable, lowest growth
- **Banking** (VCB, BID, CTG) — moderate yield, moderate growth, regulatory risk
- **Real Estate Tier-1** (VIC, VHM) — yield variable, growth high
- **Consumer Staples** (VNM, SAB) — historically high yield, recent cuts
- **Pharma** (DHG, IMP) — stable but small
- **REITs** (limited in VN)

**Diversification rule:** Aim for top 5 dividend holdings across **at least 4 sectors**.

## Grade interpretation

| Grade | Score | Interpretation | Action |
| --- | --- | --- | --- |
| **A** | 80-100 | Ideal income holding | Core position (up to 10-15% NAV) |
| **B** | 60-79 | Viable but weak in 1 area | Smaller weight (5-8%) |
| **C** | 40-59 | Marginal — income-only motivation | Consider only if yield very high (>7%) AND no traps |
| **Reject** | <40 OR trap | Skip | — |

## VN-specific gotchas

### Stock dividends pollute yield calculations

If a company pays 10% stock dividend + 1,500 VND cash dividend, the **yield** is calculated **only** on the cash portion:
- 1,500 / current_price × 100 = cash yield
- The stock dividend is a 10% share dilution → price adjusts automatically

Many VN trader reports incorrectly include stock dividend in yield. This skill **excludes** stock dividends.

### Quarter-end and AGM timing

- Most VN companies finalise dividend at AGM (T4-T6)
- Ex-dividend date can be 2-4 months after AGM announcement
- Some companies pay interim dividends (especially banks, T3-T5; second tranche T9-T11)
- For YTM accuracy, sum **all cash dividends with ex-date** in the last 12 months

### Tax-adjusted yield

Net yield = gross yield × (1 − 0.05) = gross yield × 0.95

For a 5% gross yield, net is 4.75%. Combine with `vn-tax-fee-calculator dividend` for precise per-trade math.

### Defaults

| Parameter | Default | Reason |
| --- | --- | --- |
| `--min-yield` | 4.0 | Below this, yield isn't worth the opportunity cost |
| `--max-payout` | 80.0 | Above this, dividend sustainability fragile |
| `--min-roe` | 12.0 | Below this, quality of earnings questionable |
| `--min-eps-3y-cagr` | −5.0 | More negative = EPS collapsing, yield trap risk |
| `--min-consecutive-years` | 3 | Need a track record |
| `--yield-trap-threshold` | 8.0 | Yield above this triggers extra sustainability checks |
