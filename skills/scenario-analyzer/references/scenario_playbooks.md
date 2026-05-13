# Scenario Playbooks

This reference provides templates and best practices for building 18-month scenarios.
Consult it during scenario analysis to produce consistent, high-quality scenarios.

## Core Principles for Scenario Construction

### 1. MECE (Mutually Exclusive, Collectively Exhaustive)

Scenarios should be:
- **Mutually exclusive:** scenarios do not overlap
- **Collectively exhaustive:** main possibilities are all covered

### 2. Probability Allocation Guidelines

| Scenario | Typical range | Allocation rationale |
|---------|----------|-----------|
| Base Case | 50–65% | Most likely path |
| Bull Case | 15–25% | Positive upside |
| Bear Case | 20–30% | Negative downside |
| Total | 100% | Always normalise to 100% |

**When asymmetric allocation is appropriate:**
- Bull > Bear: environment with many positive catalysts
- Bear > Bull: environment with many risk factors
- Base > 60%: situation has low uncertainty
- Base < 50%: situation has very high uncertainty (even Base is uncertain)

### 3. Timeline Breakdown

**Three-phase structure:**
- **0–6 months:** short-term reaction, initial moves
- **6–12 months:** medium-term development, trend formation
- **12–18 months:** long-term consequences, new equilibrium

---

## Scenario Templates

### Base Case Template

```markdown
### Base Case (XX% probability)

**Summary:**
[1–2 sentences summarising the scenario. State the most likely development.]

**Assumptions:**
- [Assumption 1]: [specific condition]
- [Assumption 2]: [specific condition]
- [Assumption 3]: [specific condition]

**Timeline:**

**0–6 months:**
- [Key development 1]
- [Key development 2]
- [Expected market reaction]

**6–12 months:**
- [Medium-term development 1]
- [Medium-term development 2]
- [Trend direction]

**12–18 months:**
- [Long-term consequence 1]
- [New equilibrium state]
- [Structural change (if any)]

**Economic indicator impact:**
| Indicator | Current | 6M | 12M | 18M |
|------|------|------------|-------------|-------------|
| GDP growth | X% | X% | X% | X% |
| Inflation | X% | X% | X% | X% |
| Policy rate | X% | X% | X% | X% |
| Unemployment | X% | X% | X% | X% |

**Key catalysts:**
- [Factor pushing the scenario forward 1]
- [Factor pushing the scenario forward 2]

**Invalidation signals:**
- [Sign the scenario is breaking 1]
- [Sign the scenario is breaking 2]
```

### Bull Case Template

```markdown
### Bull Case (XX% probability)

**Summary:**
[1–2 sentences summarising the optimistic scenario. What upside materialises?]

**Assumptions:**
- [Optimistic assumption 1]: [specific condition]
- [Optimistic assumption 2]: [specific condition]
- [Optimistic assumption 3]: [specific condition]

**Timeline:**

**0–6 months:**
- [Positive development 1]
- [Positive development 2]
- [Expected favourable market reaction]

**6–12 months:**
- [Upside trend continuation]
- [Additional positive factors]
- [Improvement in market sentiment]

**12–18 months:**
- [Outcome of the optimistic scenario]
- [Achieved state]
- [Sustainability assessment]

**Economic indicator impact:**
[Numbers better than Base Case]

**Upside catalysts:**
- [Factor that brings about this scenario 1]
- [Factor that brings about this scenario 2]

**Conditions that increase the probability of this scenario:**
- [Condition 1]
- [Condition 2]
```

### Bear Case Template

```markdown
### Bear Case (XX% probability)

**Summary:**
[1–2 sentences summarising the risk scenario. What downside materialises?]

**Assumptions:**
- [Risk assumption 1]: [specific condition]
- [Risk assumption 2]: [specific condition]
- [Risk assumption 3]: [specific condition]

**Timeline:**

**0–6 months:**
- [Negative development 1]
- [Negative development 2]
- [Expected adverse market reaction]

**6–12 months:**
- [Downside trend continuation / deepening]
- [Secondary problems surface]
- [Sentiment deteriorates]

**12–18 months:**
- [Outcome of the risk scenario]
- [Worst-case state]
- [Path to recovery (if any)]

**Economic indicator impact:**
[Numbers worse than Base Case]

**Downside risk factors:**
- [Factor that triggers this scenario 1]
- [Factor that triggers this scenario 2]

**Conditions that increase the probability of this scenario:**
- [Condition 1]
- [Condition 2]

**Risk-mitigation factors:**
- [Factor that could blunt this scenario 1]
- [Factor that could blunt this scenario 2]
```

---

## Event-Type Playbooks

### 1. Monetary Policy (Rate Hike)

**Base Case (55%):**
- Hike delivered as expected
- Largely priced in
- Mild equity dip, small rise in bond yields

**Bull Case (20%):**
- Hike smaller than expected
- Dovish forward guidance
- Equity market rallies

**Bear Case (25%):**
- Hike larger than expected
- Hawkish forward guidance
- Sharp equity sell-off, credit spreads widen

### 2. Geopolitics (Conflict Outbreak)

**Base Case (50%):**
- Conflict expands in a limited way
- Short-term commodity price rises
- Situation stabilises over a few months

**Bull Case (15%):**
- Early ceasefire / peace agreement
- Commodity prices normalise
- Market recovers quickly

**Bear Case (35%):**
- Conflict prolongs / escalates
- Serious commodity-supply disruption
- Global inflation accelerates, recession risk rises

### 3. Technology Shift (AI Regulation)

**Base Case (50%):**
- Moderate regulation introduced
- Industry self-regulation leads
- Limited impact on innovation

**Bull Case (25%):**
- Regulation drafted in an industry-favourable way
- Clarity actually accelerates investment
- Barriers to entry favour incumbents

**Bear Case (25%):**
- Strict regulation introduced
- Significant restrictions on AI development
- US competitiveness declines

### 4. Corporate (Large M&A)

**Base Case (60%):**
- Regulatory approval obtained
- Closes on schedule
- Synergies realised incrementally

**Bull Case (15%):**
- Synergies exceed expectations
- Integration runs smoothly
- Further M&A strategy succeeds

**Bear Case (25%):**
- Regulators block or impose conditions
- Integration delayed or fails
- Synergy targets missed

---

## Scenario Quality Checklist

### Internal consistency
- [ ] Are the assumptions logically consistent within each scenario?
- [ ] Is the timeline driven by clear cause-effect chains?
- [ ] Are the economic-indicator forecasts consistent with each other?

### External validity
- [ ] Is the scenario consistent with analogous past events?
- [ ] Does it appropriately reflect the current market environment?
- [ ] Is it not wildly out of line with expert views?

### Practical usefulness
- [ ] Is there enough specificity to inform investment decisions?
- [ ] Are monitorable catalysts identified?
- [ ] Are invalidation signals clear?

### Coverage
- [ ] Are the main risk scenarios included?
- [ ] Is upside potential considered appropriately?
- [ ] Is tail risk acknowledged?

---

## Common Mistakes and How to Avoid Them

### 1. Status-quo bias
**Problem:** Over-allocating to Base Case (>70%)
**Fix:** Historically, the probability that "nothing changes" is low

### 2. Recency bias
**Problem:** Over-weighting the most recent event
**Fix:** Keep a long-term perspective; refer to past patterns

### 3. Confirmation bias
**Problem:** Only adopting interpretations aligned with the headline
**Fix:** Deliberately seek counterarguments

### 4. False precision
**Problem:** Forecasting numbers 18 months ahead to multiple decimal places
**Fix:** Acknowledge uncertainty; express with ranges

### 5. Overlapping scenarios
**Problem:** Base/Bull/Bear partially overlap
**Fix:** Make boundary conditions for each scenario explicit

---

## Probability-Update Guidelines

When new information arrives:

| New information | Probability adjustment |
|-------------|---------------|
| Data supporting the scenario | +5–15% |
| Data contradicting the scenario | –5–15% |
| Decisive evidence | +20–30% or –20–30% |
| New risk factor emerges | Bear Case +5–10% |
| Risk factor dissipates | Bear Case –5–10% |

**Always re-normalise to 100% after adjusting.**

---

## Output Quality Bar

High-quality scenarios share these traits:
1. **Specificity:** numbers, dates, names — not abstractions
2. **Logical:** clear causal chains
3. **Verifiable:** can be judged true / false in hindsight
4. **Practical:** information directly relevant to investment decisions
5. **Humble:** uncertainty is acknowledged appropriately
