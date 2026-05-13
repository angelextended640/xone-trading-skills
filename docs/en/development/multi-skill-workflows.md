---
layout: default
title: Multi-Skill Workflows
parent: English
nav_order: 5
permalink: /en/development/multi-skill-workflows/
---

# Multi-Skill Workflows

Skills are designed to be combined for comprehensive analysis. The recipes below capture common multi-step pipelines that the trading-skills project supports today.

## Daily Market Monitoring

1. Economic Calendar Fetcher → Check today's events
2. Earnings Calendar → Identify reporting companies
3. Market News Analyst → Review overnight developments
4. Breadth Chart Analyst → Assess market health

## Weekly Strategy Review

1. Sector Analyst → Identify rotation patterns
2. Technical Analyst → Confirm trends
3. Market Environment Analysis → Macro briefing
4. US Market Bubble Detector → Risk assessment

## Individual Stock Research

1. US Stock Analysis → Fundamental/technical review
2. Earnings Calendar → Check earnings dates
3. Market News Analyst → Recent news
4. Backtest Expert → Validate entry/exit strategy

## Options Strategy Development

1. Options Strategy Advisor → Simulate and compare strategies
2. Technical Analyst → Identify optimal entry timing
3. Earnings Calendar → Plan earnings-based strategies
4. US Stock Analysis → Validate fundamental thesis

## Portfolio Review & Rebalancing

1. Portfolio Manager → Fetch holdings via Alpaca MCP
2. Review asset allocation and risk metrics
3. Market Environment Analysis → Assess macro conditions
4. Execute rebalancing plan with buy/sell actions

## Earnings Momentum Trading

1. Earnings Trade Analyzer → Score recent earnings reactions (5-factor: gap, trend, volume, MA200, MA50)
2. PEAD Screener (Mode B) → Feed analyzer output, screen for red candle pullback → breakout patterns
3. Technical Analyst → Confirm weekly chart setups on SIGNAL_READY/BREAKOUT candidates
4. Monitor BREAKOUT entries with stop-loss (red candle low) and 2R profit targets

## Statistical Arbitrage

1. Pair Trade Screener → Identify cointegrated pairs
2. Technical Analyst → Confirm setups for both legs
3. Monitor z-score signals and spread convergence
4. Manage market-neutral positions

## Income Portfolio Construction

1. Value Dividend Screener → High-yield opportunities
2. Dividend Growth Pullback Screener → Growth stocks at pullbacks
3. US Stock Analysis → Deep-dive analysis
4. Portfolio Manager → Monitor and rebalance holdings

## Trade Execution Planning

1. Screener skills (VCP, CANSLIM, Dividend, Earnings) → Identify candidates
2. Position Sizer → Calculate risk-based share count with portfolio constraints
3. Data Quality Checker → Validate analysis document before publishing
4. Portfolio Manager → Execute and monitor positions

## Kanchi Dividend Workflow (US stocks)

1. kanchi-dividend-sop → Run Kanchi 5-step screening and pullback entry planning
2. kanchi-dividend-review-monitor → Execute T1-T5 anomaly detection and review queueing
3. kanchi-dividend-us-tax-accounting → Validate qualified/ordinary assumptions and account location
4. Feed REVIEW findings back to kanchi-dividend-sop before any additional buys

## Edge Research Pipeline (end-to-end)

1. edge-candidate-agent (`--ohlcv`) → `market_summary.json` + `anomalies.json` + `tickets/`
2. edge-hint-extractor (`--market-summary`, `--anomalies`) → `hints.yaml`
3. edge-concept-synthesizer (`--tickets-dir`, `--hints`) → `edge_concepts.yaml`
4. edge-strategy-designer (`--concepts`) → `strategy_drafts/*.yaml`
5. edge-strategy-reviewer (`--drafts-dir`) → `review.yaml` (PASS / REVISE / REJECT)
6. **REVISE** → revision → re-review (max 2 cycles)
7. **PASS + export eligible** → edge-candidate-agent export → `strategy.yaml` + `metadata.json`

**Orchestrated mode:** `edge-pipeline-orchestrator` runs all stages automatically with feedback loop.

## Thesis-Driven Trading Pipeline

1. Screener skills (kanchi, earnings-trade-analyzer, vcp, pead, canslim) → Generate candidates
2. Trader Memory Core (register) → `thesis_ingest.py --source <skill> --input <report>` creates IDEA thesis
3. US Stock Analysis / Technical Analyst → Deep-dive validation, link report via `link_report()`
4. Trader Memory Core (transition) → IDEA → ENTRY_READY → ACTIVE with `transition()`
5. Position Sizer → Calculate risk-based sizing, attach via `attach_position()`
6. Portfolio Manager → Execute entry, update thesis with actual price/date
7. Trader Memory Core (review) → `list_review_due()` for periodic checks
8. Trader Memory Core (close + postmortem) → Record exit, generate journal entry with MAE/MFE

## Parabolic Short Pipeline (Phase 1 + 2 + 3)

1. `screen_parabolic.py` (Phase 1) → daily watchlist JSON; 5-factor weighted score (MA Extension 30 / Acceleration 25 / Volume Climax 20 / Range Expansion 15 / Liquidity 10) → A/B/C/D grade. Hard-rejects via `invalidation_rules` (mode-aware), then attaches `state_caps` / `warnings`. `--dry-run --fixture` for offline pipeline verification.
2. Review the `reports/parabolic_short_<date>.md` watchlist and decide which candidates to promote (A/B by default).
3. `generate_pre_market_plan.py` (Phase 2) → reads Phase 1 JSON, filters by `--tradable-min-grade B`, looks up Alpaca short inventory (or `ManualBrokerAdapter` when env vars missing), inherits `prior_close` for SSR Rule 201 evaluation, splits manual-confirmation reasons into blocking vs advisory, and emits three trigger plans per candidate (5-min ORL break, first red 5-min, VWAP fail).
4. Trader confirms `blocking_manual_reasons` are cleared at the broker (HTB locate, premarket high/low resolved, etc.).
5. `monitor_intraday_trigger.py` (Phase 3) → reads the Phase 2 plan, fetches 5-min bars (Alpaca live or fixture), walks each plan's FSM forward by one step (per-trigger evaluator: ORL break, first red, VWAP fail), and writes `parabolic_short_intraday_<date>.json` with `state` (armed/triggered/invalidated/...), bar-derived transition timestamps, and `size_recipe_resolved.shares_actual` when triggered. One-shot — wrap in `watch -n 60 'python3 ...'` or 5-min cron during market hours. Replay-deterministic: re-runs against the same `--now-et` produce byte-identical output.
6. Optional: `trader-memory-core` `thesis_ingest.py --source parabolic-short-trade-planner --input reports/parabolic_short_plan_<date>.json` to register theses for postmortem tracking.
