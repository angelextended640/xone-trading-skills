---
name: scenario-analyzer
description: |
  Build 18-month investment scenarios from news headlines. The skill orchestrates two subagents:
  scenario-analyst runs the primary analysis (Base/Bull/Bear cases, 1st/2nd/3rd-order sector impacts,
  positive/negative stock picks), and strategy-reviewer provides a critical second opinion (missed sectors,
  bias detection, probability sanity-check, alternative scenarios). Produces a single integrated Markdown
  report under reports/. Use when the user wants to think through how a news event will play out over
  ~18 months. Example: /scenario-analyzer "Fed raises rates by 50bp".
  Triggers: news headline analysis, scenario analysis, 18-month outlook, medium-term investment strategy.
---

# Scenario Analyzer

## Overview

This skill takes a news headline and builds a structured 18-month investment scenario from it.
It chains two specialised subagents — `scenario-analyst` (primary multi-scenario analyst) and
`strategy-reviewer` (critical second opinion) — and integrates their outputs into a single
report covering scenarios, sector impacts, stock picks, and a reviewer-informed final view.

## When to Use This Skill

Use this skill when:

- The user wants to think through the medium-term investment impact of a news event
- Multiple 18-month scenarios (Base / Bull / Bear) need to be constructed
- Sector and stock impacts need to be organised by 1st/2nd/3rd-order linkages
- A second opinion / red-team pass is wanted alongside the primary analysis

**Examples:**
```
/scenario-analyzer "Fed raises interest rates by 50bp, signals more hikes ahead"
/scenario-analyzer "China announces new tariffs on US semiconductors"
/scenario-analyzer "OPEC+ agrees to cut oil production by 2 million barrels per day"
```

## Prerequisites

- **API keys:** none (uses WebSearch / WebFetch only)
- **MCP servers:** none
- **Dependencies:** the `scenario-analyst` and `strategy-reviewer` agents must be available via the Agent tool

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Skill (orchestrator)                              │
│                                                                      │
│  Phase 1: Preparation                                                │
│  ├─ Headline parsing                                                 │
│  ├─ Event-type classification                                        │
│  └─ Reference loading                                                │
│                                                                      │
│  Phase 2: Subagent calls                                             │
│  ├─ scenario-analyst (primary analysis)                              │
│  └─ strategy-reviewer (second opinion)                               │
│                                                                      │
│  Phase 3: Integration and report generation                          │
│  └─ reports/scenario_analysis_<topic>_YYYYMMDD.md                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflow

### Phase 1: Preparation

#### Step 1.1: Parse the headline

Examine the user-provided headline:

1. **Confirm the headline**
   - If a headline is supplied as an argument, use it.
   - If not, prompt the user for one.

2. **Extract keywords**
   - Main entities (company names, country names, institutions)
   - Numeric data (rates, prices, quantities)
   - Actions (raise, cut, announce, agree, etc.)

#### Step 1.2: Classify the event type

Map the headline to one of the categories below:

| Category | Examples |
|---------|-----|
| Monetary policy | FOMC, ECB, BoJ, rate hike/cut, QE/QT |
| Geopolitics | War, sanctions, tariffs, trade frictions |
| Regulation / policy | Environmental, financial, antitrust |
| Technology | AI, EV, renewables, semiconductors |
| Commodities | Oil, gold, copper, agriculture |
| Corporate / M&A | Acquisitions, bankruptcies, earnings, industry restructuring |

#### Step 1.3: Load references

Based on the event type, read the relevant references:

```
Read references/headline_event_patterns.md
Read references/sector_sensitivity_matrix.md
Read references/scenario_playbooks.md
```

**Reference contents:**
- `headline_event_patterns.md`: Historical event patterns and market reactions
- `sector_sensitivity_matrix.md`: Event × sector impact matrix
- `scenario_playbooks.md`: Templates and best practices for building scenarios

---

### Phase 2: Subagent calls

#### Step 2.1: Call `scenario-analyst`

Invoke the primary analysis agent via the Agent tool:

```
Agent tool:
- subagent_type: "scenario-analyst"
- prompt: |
    Run an 18-month scenario analysis on the following headline.

    ## Target headline
    [the user's headline]

    ## Event type
    [classification result]

    ## Reference notes
    [summary of the references that were loaded]

    ## Requirements
    1. Use WebSearch to collect relevant news from the past two weeks.
    2. Build 3 scenarios (Base / Bull / Bear) with probabilities summing to 100%.
    3. Analyse 1st / 2nd / 3rd-order impacts by sector.
    4. Recommend 3–5 stocks each for positive and negative exposure (US-listed only).
    5. Output entirely in English.
```

**Expected outputs:**
- A list of relevant news articles
- Three scenarios (Base / Bull / Bear) in detail
- Sector impact analysis (1st / 2nd / 3rd order)
- Stock recommendation list

#### Step 2.2: Call `strategy-reviewer`

Feed the scenario-analyst output into the reviewer agent:

```
Agent tool:
- subagent_type: "strategy-reviewer"
- prompt: |
    Review the following scenario analysis.

    ## Target headline
    [the user's headline]

    ## Primary analysis
    [full output from scenario-analyst]

    ## Review requirements
    Critique the analysis along these axes:
    1. Missed sectors / stocks
    2. Reasonableness of scenario probability allocation
    3. Logical consistency of impact analysis
    4. Detection of optimism / pessimism bias
    5. Alternative scenarios to consider
    6. Timeline realism

    Output constructive, specific feedback in English.
```

**Expected outputs:**
- Identified blind spots
- Comments on scenario probabilities
- Bias call-outs
- Alternative scenario proposals
- Final recommendations

---

### Phase 3: Integration and report generation

#### Step 3.1: Integrate the two analyses

Combine the agents' outputs into a final investment view:

**Integration points:**
1. Fill in gaps that the reviewer identified.
2. Adjust probability allocation if warranted.
3. Reflect reviewer's bias warnings in the final view.
4. Lay out a concrete action plan.

#### Step 3.2: Generate the report

Write the final report to `reports/scenario_analysis_<topic>_YYYYMMDD.md`:

```markdown
# Headline Scenario Analysis Report

**Analysis date:** YYYY-MM-DD HH:MM
**Headline:** [user input]
**Event type:** [classification]

---

## 1. Related News
[news list from scenario-analyst]

## 2. Scenarios (18-month outlook)

### Base Case (XX% probability)
[scenario detail]

### Bull Case (XX% probability)
[scenario detail]

### Bear Case (XX% probability)
[scenario detail]

## 3. Sector / Industry Impact

### 1st-order impact (direct)
[impact table]

### 2nd-order impact (value chain / adjacent industries)
[impact table]

### 3rd-order impact (macro / regulation / technology)
[impact table]

## 4. Positively Impacted Stocks (3–5)
[stock table]

## 5. Negatively Impacted Stocks (3–5)
[stock table]

## 6. Second Opinion / Review
[strategy-reviewer output]

## 7. Final Investment View

### Recommended actions
[reviewer-informed concrete actions]

### Key risks
[principal risks]

### Monitoring points
[indicators and events to track]

---
**Generated by:** scenario-analyzer skill
**Agents:** scenario-analyst, strategy-reviewer
```

#### Step 3.3: Save the report

1. Create the `reports/` directory if it does not exist.
2. Save as `scenario_analysis_<topic>_YYYYMMDD.md` (e.g. `scenario_analysis_venezuela_20260104.md`).
3. Notify the user that the report has been saved.
4. **Never write the report to the project root.**

---

## Output

This skill produces the following file:

| File | Format | Description |
|---------|------|------|
| `reports/scenario_analysis_<topic>_YYYYMMDD.md` | Markdown | Integrated scenario analysis report |

**Contents:**
- Related news list
- Base / Bull / Bear scenarios with probability allocation
- Sector impact analysis (1st / 2nd / 3rd order)
- Positive / negative stock recommendations
- Second-opinion review
- Final investment view

## Resources

### References
- `references/headline_event_patterns.md` — Event patterns and historical market reactions
- `references/sector_sensitivity_matrix.md` — Sector sensitivity matrix
- `references/scenario_playbooks.md` — Scenario construction templates

### Agents
- `scenario-analyst` — Primary scenario analysis
- `strategy-reviewer` — Second-opinion review

---

## Important Notes

### Language
- All analysis and output is in **English**.
- Stock tickers stay in their native (English) form.

### Target market
- Stock recommendations are limited to **US-listed instruments** (ADRs included).

### Time horizon
- Scenarios cover **18 months**, broken into 0–6 / 6–12 / 12–18-month phases.

### Probability allocation
- Base + Bull + Bear must sum to **100%**.
- Each scenario's probability must be justified.

### Second opinion
- The reviewer agent is **always** invoked — the second opinion is not optional.
- Reviewer findings must be reflected in the final view.

### Output location (important)
- The report **must** be saved under `reports/`.
- Path: `reports/scenario_analysis_<topic>_YYYYMMDD.md`
- Example: `reports/scenario_analysis_fed_rate_hike_20260104.md`
- Create `reports/` if it does not exist.
- **Never write the report directly to the project root.**

---

## Quality Checklist

Before finalising the report, confirm:

- [ ] The headline has been parsed correctly.
- [ ] The event-type classification is appropriate.
- [ ] The three scenario probabilities sum to 100%.
- [ ] 1st / 2nd / 3rd-order impacts connect logically.
- [ ] Stock picks are backed by specific reasoning.
- [ ] The strategy-reviewer output is included.
- [ ] The final view reflects the reviewer's findings.
- [ ] The report has been saved to the correct path.
