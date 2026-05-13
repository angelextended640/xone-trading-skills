# VN30 Futures — Contract Mechanics

**Last updated:** 2026-05-13
**Source:** HNX (sàn giao dịch phái sinh), VSDC

## Contract specification

| Item | Value |
| --- | --- |
| **Underlying** | VN30 Index (top 30 cổ phiếu HOSE theo vốn hóa) |
| **Listed contracts** | 4 — VN30F1M (front month), VN30F2M (next month), VN30F1Q (front quarter), VN30F2Q (next quarter) |
| **Multiplier** | 100,000 VND × VN30 index point |
| **Tick size** | 0.1 point = 10,000 VND |
| **Daily price band** | ±7% from previous day reference price |
| **Trading unit** | 1 contract |
| **Position limits** | Set by VSDC per individual; typically 5,000 contracts cá nhân |
| **Settlement** | Cash-settled at the average of the underlying VN30 index in the last 30 minutes of the last trading day |

## Roll calendar — last trading day

Front-month contract (VN30F1M) expires on the **3rd Thursday** of the contract month. After expiry, VN30F1M rolls forward to the next month.

| Month | Last trading day pattern | Roll window |
| --- | --- | --- |
| Front month (F1M) | 3rd Thursday | 2-3 sessions before |
| Next month (F2M) | 3rd Thursday of next month | After F1M expiry |
| Front quarter (F1Q) | 3rd Thursday of quarter-end month | 1 week before |
| Next quarter (F2Q) | 3rd Thursday of next quarter-end | After F1Q expiry |

**Example:** If today is 2026-05-13 (Wednesday), front month is VN30F1M = May contract.
- May expiry: 3rd Thursday of May = 2026-05-15 (Friday — but expiry is Thursday; check HNX calendar)
- After May expiry, F1M rolls to June contract
- Typical roll window: 2-3 sessions before, so 2026-05-13 / 14 / 15

**Liquidity:**
- VN30F1M: by far the most liquid (typical daily volume 200,000+ contracts)
- VN30F2M: secondary; thinner
- Quarters (F1Q, F2Q): primarily for longer hedges

## Trading hours

VN30 Futures trade on HNX, slightly different schedule from cash equities:

| Phase | Time (ICT) |
| --- | --- |
| Pre-open (ATO) | 08:45 – 09:00 |
| Continuous matching (morning) | 09:00 – 11:30 |
| Lunch break | 11:30 – 13:00 |
| Continuous matching (afternoon) | 13:00 – 14:30 |
| Closing auction (ATC) | 14:30 – 14:45 |

Note: HOSE cash equities open ATO at 09:00 (later than HNX phái sinh's 08:45). The 15-minute gap creates an arbitrage window for the open.

## Settlement & cash flow

- **T+0 settlement.** Position can be opened and closed in the same session.
- **No physical delivery** — cash-settled at expiry vs VN30 average of last 30 minutes.
- **Mark-to-market daily.** Daily P&L is realized in cash account at the daily settlement price.
- **No T+2.5 lockup** (unlike cash equities) — this is the key advantage for active risk management.

## Initial Margin (IM)

VSDC sets initial margin requirements; typical range:

- **17-20%** of contract notional value
- **Higher during volatility** — IM can be increased temporarily by VSDC

For a contract priced at 1,283.0 points:
- Contract notional = 1,283.0 × 100,000 = 128,300,000 VND
- IM at 18% = ~23,100,000 VND per contract

If your account has 1B VND, you can theoretically hold ~43 contracts at 18% IM — but **don't**. Practical max is 5-10 contracts for retail to keep stress-test cushion.

## Maintenance margin & forced close

- **Variation Margin (VM)** is recomputed daily based on mark-to-market.
- If account equity falls below 60% of required IM, broker issues a margin call.
- **Auto-liquidation** when equity falls to 30% of required IM — broker force-closes positions starting from largest loss.

Force-close happens during the same session — no "wait for tomorrow" cushion.

## Position limits

- Retail individuals: typically 5,000 contracts (rarely a constraint for normal users)
- Aggregate position limit (long + short) applies per individual

## Roll mechanics

When rolling from VN30F1M → VN30F2M (or VN30F1Q → VN30F2Q):

1. **Close** the current contract (e.g., short 5 VN30F1M → buy 5 VN30F1M to close)
2. **Open** the new contract (e.g., short 5 VN30F2M)

The basis (futures - spot) differs between the two contracts → potential roll cost. Track this:

```
roll_cost_per_contract = (new_basis - old_basis) × 100,000
```

**Typical pattern:** F2M trades slightly higher premium than F1M (cost of carry / time premium). Rolling a short means paying this premium.

## Common pitfalls

1. **Holding past expiry** — your contract is auto-settled at the average of last 30 min. You may not like the settle price. Always roll before expiry.
2. **Confusing contracts** — VN30F1M is current month, not "first month of year". Watch the symbol carefully.
3. **Underestimating tick value** — 0.1 point = 10,000 VND. A 10-point swing = 1,000,000 VND per contract. With 5 contracts that's 5M VND in minutes.
4. **No daily price band cushion** — ±7% band exists, but in a fast move you can be locked at limit, unable to exit.
5. **Treating IM as cost** — IM is collateral, returned when you close. The actual cost is fees + slippage + financing if held overnight.

## Resources

- HNX phái sinh: https://www.hnx.vn/vi-vn/phai-sinh.html
- VSDC: https://www.vsd.vn/
- VN30 Index: https://www.hsx.vn/Modules/Listed/Web/SymbolView/View
