# VN Pullback Methodology

**Last updated:** 2026-05-13

## Why pullback entries?

Pullback entries are a lower-risk alternative to breakout entries:

| Aspect | Breakout entry | Pullback entry |
| --- | --- | --- |
| Where you buy | At the pivot (recent high) | At a support test (lower than recent high) |
| Stop distance | 5-7% from pivot | 2-5% from MA20 / MA50 |
| Risk per share | Higher | Lower |
| Hit rate | Lower (many false breakouts) | Higher (uptrend resumption common) |
| T+2.5 fit | Tight — must catch intraday | Loose — can wait for confirmation |

For Vietnam swing traders constrained by T+2.5, pullbacks are particularly attractive because you don't need intraday execution.

## The healthy pullback profile

### 1. Long-term uptrend must remain intact

Before considering a pullback, the long-term trend must be **unambiguously up**:

- **Price > MA200** — primary uptrend marker
- **MA50 > MA200** — confirmed intermediate trend
- **MA200 sloping up** — long-term direction. Check MA200 today vs MA200 one month ago: should be higher.

If MA200 is sloping down or flat, what looks like a pullback is more likely a topping pattern. Skip.

### 2. Pullback magnitude: 3-12%

Measure from the **20-day high** (recent peak) to the **current close**:

- **< 3%:** too shallow — no real pullback yet
- **3-7%:** normal pullback to MA20 area
- **7-12%:** deeper pullback, likely testing MA50
- **> 12%:** large drawdown — could be reversal, not pullback

For VN's ±7% band, even a single-session 7% drop is dramatic. So pullbacks usually unfold over 3-10 sessions.

### 3. Support test

A genuine pullback should test a known support:

- **MA20 test:** distance to MA20 < 3% (price within 3% above or 1% below MA20)
- **MA50 test:** distance to MA50 < 5% (price within 5% of MA50)

If the pullback overshoots MA50 by more than 5%, it's no longer a "test" — it may be a fail.

### 4. RSI sweet spot: 35-50

RSI(14) values during a healthy pullback:

- **< 30:** oversold — could be panic selling, not orderly pullback
- **30-35:** at the edge — needs other confirmation
- **35-50:** sweet spot for pullback entries
- **50-60:** pullback is shallow or already recovering
- **> 60:** not pulled back enough to call this a pullback

### 5. Volume dry-up at the pullback low

A healthy pullback shows **decreasing volume** as price falls toward support:

- Volume on the down days should be **lower than the rally volume**
- Volume at the trough should be ≤ 85% of MA50 volume
- A volume spike at the low is suspicious — could be capitulation, but more often institutional distribution

## VN-specific tweaks

### Adjusted pullback bounds

For HOSE blue-chips (typical):
- Pullback range: **3-10%** is the sweet spot
- > 10% pullback in a single week suggests trend change

For HNX and mid-caps:
- Pullback range: **5-15%** (more natural volatility)

### Floor price interaction

The ±7% daily floor means a stock can hit the daily floor (-7%) only once per session. If you see 2-3 consecutive floor sessions, this is **not** a healthy pullback — that's a panic / news event. Skip and re-evaluate after the dust settles.

### Foreign room context

Pullbacks combined with **foreign net buying** are particularly bullish:
- Use `vn-foreign-room-tracker` to check if foreign accumulation is happening during the pullback
- Pullback + foreign buying = institutional accumulation signal

### Sector context

Pullbacks in leading sectors recover; pullbacks in lagging sectors often deepen:
- Pair with `vn-sector-analyst` RS_20D > 0 filter
- If sector is in "deteriorating" or "falling" signal → skip the pullback

## Scoring

5 components, 25 / 20 / 20 / 20 / 15 → total 100.

### Long-term uptrend (25)

| Condition | Points |
| --- | --- |
| Price > MA200, MA50 > MA200, MA200 slope > +1% per month | 25 |
| Price > MA200, MA50 > MA200, MA200 slope > 0 | 18 |
| Price > MA200, MA50 > MA200, MA200 flat | 10 |
| Else | 0 |

### Pullback magnitude (20)

| Pullback % from 20D high | Points |
| --- | --- |
| 4-8 | 20 |
| 3-4 or 8-10 | 15 |
| 10-12 | 10 |
| Else | 0 |

### Support test (20)

| Condition | Points |
| --- | --- |
| Distance to MA20 < 3% AND price > MA20 | 20 |
| Distance to MA50 < 5% AND price > MA50 | 15 |
| Distance to MA50 < 8% AND price > MA50 | 8 |
| Else | 0 |

### RSI sweet spot (20)

| RSI(14) | Points |
| --- | --- |
| 38-48 | 20 |
| 35-38 or 48-52 | 14 |
| 30-35 or 52-55 | 8 |
| Else | 0 |

### Volume dry-up (15)

| Vol at low / MA50 vol | Points |
| --- | --- |
| ≤ 0.70 | 15 |
| 0.70-0.85 | 10 |
| 0.85-1.0 | 5 |
| > 1.0 | 0 |

## Entry, stop, target

### Entry

Place a buy limit at:
- **MA20 + 0.5%** (or current price if already at MA20)
- For deeper pullback: **midpoint between current and MA50**

### Stop

Stop loss at:
- **Pullback low × 0.97** (3% below recent low), OR
- **MA50 × 0.97** (3% below MA50), OR
- **Pivot from before pullback × 0.93** (7% below pre-pullback peak)

Use the highest of these three (tightest stop that still gives the trade room).

### Target

R-multiple based:
- **T1:** 1R (cover risk)
- **T2:** 2R (typical pullback rally)
- **T3:** revisit previous high + breakout extension

## Common pullback failure modes

| Failure | Recognition | Action |
| --- | --- | --- |
| Pullback turns to reversal | Price breaks below MA50 with volume | Exit on close below MA50 |
| Fake bottom | Pullback "ends" but new low arrives within 5 sessions | Re-evaluate; may not be ready |
| News-driven gap down | Overnight gap takes out stop | Accept loss, don't re-enter same day |
| Sector failure | Sector RS_20D drops below -1 | Cut size 50% or exit |

## Defaults

| Parameter | Default | Reason |
| --- | --- | --- |
| `--min-pullback-pct` | 3 | Below this, no real pullback |
| `--max-pullback-pct` | 12 | Above this, likely reversal |
| `--rsi-low` | 35 | Lower bound of sweet spot |
| `--rsi-high` | 50 | Upper bound |
| `--max-distance-ma20-pct` | 3 | MA20 test threshold |
| `--max-distance-ma50-pct` | 5 | MA50 test threshold |
| `--volume-dryup-threshold` | 0.85 | Healthy pullback volume |
