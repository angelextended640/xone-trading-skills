---
description: "Build an 18-month scenario from a news headline. Produces an integrated report covering 1st/2nd/3rd-order sector impacts, stock picks, and a second-opinion review."
argument-hint: "<headline>"
---

# Scenario Analyzer

Take a news headline and produce an 18-month investment scenario covering sector and stock impacts.

## Arguments

```
$ARGUMENTS
```

**Argument handling:**
- If a headline is provided, analyse it.
- If the argument is empty, prompt the user for a headline.

**Examples:**
- `/scenario-analyzer Fed raises rates by 50bp` → analyse Fed rate-hike scenario
- `/scenario-analyzer China announces new tariffs on US semiconductors` → analyse the tariff scenario
- `/scenario-analyzer OPEC+ agrees to cut oil production` → analyse the oil supply-cut scenario
- `/scenario-analyzer` → ask for a headline, then analyse

## What the analysis covers

| Item | Description |
|------|------|
| **Related news** | WebSearch for related articles from the past two weeks |
| **Scenarios** | Three scenarios (Base / Bull / Bear) with probabilities |
| **Impact analysis** | 1st / 2nd / 3rd-order sector impacts |
| **Stock picks** | 3–5 stocks each for positive and negative exposure (US market) |
| **Review** | Second opinion (blind spots, biases) |

## Procedure

1. **Parse the headline:**
   - Extract the headline from the argument.
   - If empty, prompt the user.
   - Classify the event type (monetary policy / geopolitics / regulation / technology / commodity / corporate).

2. **Load references:**
   ```
   Read skills/scenario-analyzer/references/headline_event_patterns.md
   Read skills/scenario-analyzer/references/sector_sensitivity_matrix.md
   Read skills/scenario-analyzer/references/scenario_playbooks.md
   ```

3. **Primary analysis (scenario-analyst agent):**
   ```
   Agent tool:
   - subagent_type: "scenario-analyst"
   - prompt: headline + event type + reference notes
   ```

   Output:
   - Related news article list
   - Three scenarios (Base / Bull / Bear)
   - Sector impact analysis (1st / 2nd / 3rd)
   - Stock recommendation list

4. **Second opinion (strategy-reviewer agent):**
   ```
   Agent tool:
   - subagent_type: "strategy-reviewer"
   - prompt: full output from step 3
   ```

   Output:
   - Blind-spot call-outs
   - Comments on scenario probabilities
   - Bias detection
   - Alternative scenario proposals

5. **Generate the report:**
   - Integrate both agents' outputs.
   - Append a final investment view.
   - Save to `reports/scenario_analysis_<topic>_YYYYMMDD.md`.

## Reference resources

- `skills/scenario-analyzer/references/headline_event_patterns.md` — event patterns
- `skills/scenario-analyzer/references/sector_sensitivity_matrix.md` — sector sensitivities
- `skills/scenario-analyzer/references/scenario_playbooks.md` — scenario templates

## Important directives

- **Language:** All analysis and output in **English**.
- **Target market:** Stock picks must be **US-listed only**.
- **Time horizon:** Scenarios cover **18 months**.
- **Probability:** Base + Bull + Bear = **100%**.
- **Second opinion:** **Always required** — invoke strategy-reviewer every time.

## Output

Produce a `Headline Scenario Analysis Report` containing:
- Related news articles
- 18-month scenario summary
- 1st / 2nd / 3rd-order sector / industry impacts
- Positively impacted stocks (3–5)
- Negatively impacted stocks (3–5)
- Second-opinion review
- Final investment view
