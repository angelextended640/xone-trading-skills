# VN30 Futures — Fee Structure

**Last updated:** 2026-05-13
**Different from cash equities** — review carefully if migrating from cash.

## Key differences vs cash equities

| Fee type | Cash equity | VN30 Futures |
| --- | --- | --- |
| **Sale tax (0.1%)** | Applied to every sell | **None** — futures are not subject to securities transfer tax |
| **Broker fee** | % of notional (0.03-0.15%) | Flat per-contract (1,000-3,000 VND) |
| **HNX fee** | Embedded in broker fee | 2,700 VND/contract |
| **VSDC fee** | 0.27 VND/CP/month | 2,550 VND/contract (per side) |
| **Overnight position** | n/a | ~3,000 VND/contract/night |
| **Margin call cost** | n/a | Free (margin call itself) but broker may charge for force-close |

## Per-CTCK fee table (T05/2026 retail online tier)

| CTCK | Broker commission/contract (mỗi chiều) | Round-trip cost per contract | Notes |
| --- | --- | --- | --- |
| **VPS** | 2,700 VND | ~10,950 VND | Most common retail; competitive |
| **SSI** | 3,000 VND | ~11,550 VND | Quality execution, slight premium |
| **VNDirect** | 3,000 VND | ~11,550 VND | Standard |
| **HSC** | 2,700 VND | ~10,950 VND | Standard |
| **MBS** | 2,700 VND | ~10,950 VND | Standard |
| **TCBS** | 2,500 VND | ~10,550 VND | Slightly cheaper |
| **DNSE** | 1,000 VND | ~7,550 VND | Cheapest retail (self-service) |
| **VCI (Vietcap)** | 3,000 VND | ~11,550 VND | Strong derivatives focus |

**Round-trip cost formula** (per contract):
```
round_trip = 2 × broker_commission + 2 × hnx_fee + 2 × vsdc_fee
           = 2 × broker_commission + 2 × 2,700 + 2 × 2,550
           = 2 × broker_commission + 10,500
```

## Overnight position cost

If you hold a futures position past 14:45 ATC close, you pay an "overnight" fee:

- Typical: **~3,000 VND per contract per night**
- Some brokers charge differently per side (long vs short)

For a position held over a 3-day weekend: 3 × 3,000 = 9,000 VND extra.

This is **separate** from any financing cost — it's a flat operational fee.

## Margin financing (if using broker's IM credit)

Some brokers extend "futures margin" credit beyond your cash IM. Rates:

- Typical: **9-12% per annum**
- Daily: ~0.025-0.033% × notional

For 1B VND notional held 30 days on financed margin:
```
financing_cost = 1B × 10%/year × 30/365 = ~8,219,000 VND
```

Not all brokers offer this; verify availability before relying on it.

## Cost comparison: cash equity vs VN30 Futures hedging

**Scenario:** Hedge 1B VND cash long with VN30 Futures short for 30 days.

| Approach | Round-trip cost |
| --- | --- |
| **Sell cash equity then re-buy** | 1B × 0.4% × 2 = 8,000,000 VND (fees + tax both directions) |
| **Short 8 VN30F1M (cover with VPS)** | 8 × 10,950 = 87,600 VND |
| **Plus 30 nights overnight** | 8 × 3,000 × 30 = 720,000 VND |
| **Total (futures hedge)** | **~810,000 VND** |

Hedging via VN30 Futures is ~10x cheaper than rotating cash positions for short-term defensive moves.

## When fees matter most

1. **Frequent intraday trades** — flat per-contract fees mean fee % is much higher for tight scalping. A 1-tick (10,000 VND) gain barely covers round-trip cost on most CTCK.
2. **Many contracts** — At 50+ contracts/day, choose lowest-fee CTCK (DNSE or TCBS).
3. **Overnight positions** — Daily 3,000 VND/contract adds up. For weekly+ holds, factor this in.
4. **Hedging cost analysis** — When comparing "rotate cash" vs "hedge with futures", fees + slippage matter more than directional view.

## Comparison helper: compute net P&L

For a short trade on N contracts entry → exit:

```python
gross_pnl = (entry - exit) × 100,000 × N        # short profits when exit < entry
round_trip_fee = (2 × broker_commission + 10,500) × N
overnight_fee = nights × 3,000 × N              # if held overnight
net_pnl = gross_pnl - round_trip_fee - overnight_fee
```

No 0.1% sale tax to subtract (futures are exempt).

## Default for the planner

The `cost` subcommand in `vn30_derivatives_planner.py` uses **VPS at 2,700 VND/contract** as the default. Override with `--broker tcbs` or `--custom-broker-fee 2500`.
