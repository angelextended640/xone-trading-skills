# VCP Methodology — VN Adjusted

**Last updated:** 2026-05-13
**Based on:** Mark Minervini, *Trade Like a Stock Market Wizard* (2013), adjusted for HOSE / HNX market mechanics.

## What is VCP?

Volatility Contraction Pattern (VCP) is a base-and-breakout setup where price action shows successive **contractions** — each pullback is shallower than the previous, and trading range narrows toward a tight pivot. The pattern signals institutional accumulation: large buyers are absorbing supply, reducing volatility, before a breakout.

## The 5 Essential VCP Characteristics

### 1. Uptrend baseline

The stock must be in a confirmed uptrend before the base:
- Price > MA50 > MA200
- MA50 slope positive (rising over last 20 sessions)
- Trend duration: at least 30 sessions of uptrend

### 2. Multiple contractions

Inside the base, count distinct contractions (a contraction is a pullback followed by a recovery):
- **Minimum:** 2 contractions
- **Typical:** 3-4 contractions
- **Maximum:** 5-6 (more than this usually means base is too long)

### 3. Decreasing depth (the key signature)

Each contraction's depth (high to low) must be **smaller than the previous one**:

```
T1: 12% depth   (deepest)
T2: 7%  depth   (about half of T1)
T3: 4%  depth   (about half of T2)
T4: 2%  depth   (final tight contraction = pivot zone)
```

If a later contraction is deeper than an earlier one → not VCP (failed pattern).

### 4. Volume dry-up

As contractions tighten, volume must contract too:
- At the deepest part of each contraction, volume should be ≤ 70% of MA50 volume
- Final contraction: volume often drops to 50-60% of average (the "stillness")
- A volume spike at the pivot is the breakout signal

### 5. Pivot near recent high

The pivot point (top of the tightest contraction) should be:
- Within 5-10% of the 52-week high
- Above the previous high in the base (each contraction's recovery makes new local high)

## VN-Specific Adjustments

### Why VN differs from US

| US (S&P 500 names) | VN (HOSE blue-chips) |
| --- | --- |
| No intraday price limit | ±7% HOSE band per session |
| Tight 1-2% intraday range is "tight" | A "tight" 1-2% in VN means 1/3 of max band — that's exceptional |
| ATR commonly 1-3% daily | ATR commonly 1.5-3% daily on HOSE blue-chips, but 3-5% on small caps |

### Adjusted contraction depth thresholds

For HOSE blue-chips (typical):
- **T1 max:** 15% (some flexibility for early base contraction)
- **T2 max:** 10% (must be smaller than T1)
- **T3 max:** 6%
- **T4 max:** 3%

For HOSE mid-caps and HNX:
- Add ~1-2% to each threshold (more natural volatility)

### Wide-and-loose detection

A "wide-and-loose" base is **not** a VCP — it's a sloppy range. Reject if:
- Total base range (overall high to low) > 25% of the lowest point
- OR if any contraction depth > 18% on HOSE blue-chip

Why this matters in VN: the ±7% band means an 18%+ contraction takes 3+ floor sessions. That's not consolidation — that's a serious correction.

### Pivot quality

The pivot must:
- Be within 10% of 52-week high (vs Minervini's 25% guideline) — VN bases tend to form closer to highs because the ±7% band caps fast moves both ways
- Have at least 3 sessions of close prices within 2% of each other (the "tightness")
- Be above MA20 and MA50 at the pivot point

### Volume reading

Volume dry-up is a hard requirement:
- Compute MA50 of volume over the 50 sessions preceding the base start
- At the deepest point of each contraction, volume should be ≤ 70% of that MA50
- At the pivot zone (last 5-10 sessions), volume should be ≤ 60% of MA50

If volume **doesn't dry up** → reject. Without volume contraction, the price tightening is meaningless.

## Scoring

5 components, weighted 25 / 25 / 20 / 15 / 15 → total 100.

### Uptrend (25 points)

| Condition | Points |
| --- | --- |
| Price > MA50 > MA200, MA50 rising | 25 |
| Price > MA50 > MA200, MA50 flat | 18 |
| Price > MA50, MA50 < MA200 | 10 |
| Else | 0 |

### Contractions (25 points)

| Condition | Points |
| --- | --- |
| 3-4 contractions, decreasing depth, all under thresholds | 25 |
| 2 contractions, decreasing depth | 18 |
| 3+ contractions but depth not strictly decreasing | 10 |
| < 2 contractions detected | 0 (reject) |

### Volume dry-up (20 points)

| Condition | Points |
| --- | --- |
| Final contraction volume ≤ 60% of MA50 | 20 |
| Final contraction volume 60-70% of MA50 | 14 |
| Final contraction volume 70-85% of MA50 | 8 |
| Final contraction volume > 85% of MA50 | 0 |

### Pivot quality (15 points)

| Condition | Points |
| --- | --- |
| Within 5% of 52w high, tight (≤2% range over 3+ sessions) | 15 |
| Within 10% of 52w high, tight | 11 |
| Within 10% of 52w high, not tight | 6 |
| > 10% from 52w high | 0 |

### Wide-and-loose check (15 points)

| Condition | Points |
| --- | --- |
| Base range < 15%, no contraction > 12% | 15 |
| Base range 15-25%, all contractions < 18% | 9 |
| Base range 25-35% or contraction > 18% | 0 (cap grade at C) |
| Base range > 35% | reject entirely |

## Pivot and stop calculation

Once VCP is detected:

- **Pivot:** highest close in the final contraction zone (last 10 sessions), rounded to nearest tick
- **Suggested stop:** 5-7% below pivot OR low of the final contraction (whichever is higher)
  - Constraint: stop must be above the price floor of the day after entry (use `compute_price_band` from `vn-market-mechanics`)
- **Target:** R-multiple based (1R = pivot - stop)

## When VCP fails

Even a perfect VCP can fail. Common failure modes:
- **Failed breakout:** price breaks pivot, then closes back below within 3-5 sessions. Exit on close back below pivot.
- **Volume failure on breakout:** breakout day's volume < 50% of MA50 → low conviction breakout. Tighter stop.
- **News-driven gap below stop:** at-market exit next morning, accept the loss.
- **Market regime change:** if VN-Index falls below MA50 while you hold a VCP entry, tighten stop or exit.

## Suggested defaults

| Parameter | Default | Notes |
| --- | --- | --- |
| `--min-base-length` | 25 sessions | Minimum days from base start to pivot |
| `--max-base-length` | 90 sessions | Beyond this, base is too long |
| `--min-contractions` | 2 | Hard minimum |
| `--max-contractions` | 5 | Above this, often messy |
| `--max-base-range-pct` | 25 | Wide-and-loose threshold |
| `--max-pivot-distance-from-52w-pct` | 10 | Pivot proximity |
| `--volume-dryup-threshold` | 0.7 | Final contraction vol / MA50 vol |
