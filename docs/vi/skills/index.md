---
layout: default
title: Skill Guides
parent: Tiếng Việt
nav_order: 3
has_children: true
permalink: /vi/skills/
---

# Skill Guides
{: .no_toc }

Practical guides for individual skills with real-world examples, workflow explanations, and tips for power users.

Hand-written guides (marked with ★) follow a detailed 10-section structure. Auto-generated guides provide an overview, prerequisites, workflow, and resource listing extracted from each skill's SKILL.md.

---

## Available Guides

| Skill | Description | API |
|-------|-------------|-----|
| [Backtest Expert]({{ '/en/skills/backtest-expert/' | relative_url }}) ★ | Expert guidance for systematic backtesting of trading strategies | <span class="badge badge-free">No API</span> |
| [Breadth Chart Analyst]({{ '/en/skills/breadth-chart-analyst/' | relative_url }}) | This skill should be used when analyzing market breadth charts, specifically the S&P 500 Breadth Index (200-Day MA ba... | <span class="badge badge-free">No API</span> |
| [Breakout Trade Planner]({{ '/en/skills/breakout-trade-planner/' | relative_url }}) | Generate Minervini-style breakout trade plans from VCP screener output with worst-case risk calculation, portfolio he... | <span class="badge badge-free">No API</span> |
| [CANSLIM Screener]({{ '/en/skills/canslim-screener/' | relative_url }}) ★ | Screen US stocks using William O'Neil's CANSLIM growth stock methodology | <span class="badge badge-free">No API</span> |
| [Data Quality Checker]({{ '/en/skills/data-quality-checker/' | relative_url }}) | Validate data quality in market analysis documents and blog articles before publication | <span class="badge badge-free">No API</span> |
| [Dividend Growth Pullback Screener]({{ '/en/skills/dividend-growth-pullback-screener/' | relative_url }}) | Use this skill to find high-quality dividend growth stocks (12%+ annual dividend growth, 1 | <span class="badge badge-api">FMP Required</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [Downtrend Duration Analyzer]({{ '/en/skills/downtrend-duration-analyzer/' | relative_url }}) | Analyze historical downtrend durations and generate interactive HTML histograms showing typical correction lengths by... | <span class="badge badge-free">No API</span> |
| [Dual Axis Skill Reviewer]({{ '/en/skills/dual-axis-skill-reviewer/' | relative_url }}) | Review skills in any project using a dual-axis method: (1) deterministic code-based checks (structure, scripts, tests... | <span class="badge badge-free">No API</span> |
| [Earnings Calendar]({{ '/en/skills/earnings-calendar/' | relative_url }}) | This skill retrieves upcoming earnings announcements for US stocks using the Financial Modeling Prep (FMP) API | <span class="badge badge-api">FMP Required</span> |
| [Earnings Trade Analyzer]({{ '/en/skills/earnings-trade-analyzer/' | relative_url }}) | Analyze recent post-earnings stocks using a 5-factor scoring system (Gap Size, Pre-Earnings Trend, Volume Trend, MA20... | <span class="badge badge-api">FMP Required</span> |
| [Economic Calendar Fetcher]({{ '/en/skills/economic-calendar-fetcher/' | relative_url }}) | Fetch upcoming economic events and data releases using FMP API | <span class="badge badge-api">FMP Required</span> |
| [Edge Candidate Agent]({{ '/en/skills/edge-candidate-agent/' | relative_url }}) | Generate and prioritize US equity long-side edge research tickets from EOD observations, then export pipeline-ready c... | <span class="badge badge-free">No API</span> |
| [Edge Concept Synthesizer]({{ '/en/skills/edge-concept-synthesizer/' | relative_url }}) | Abstract detector tickets and hints into reusable edge concepts with thesis, invalidation signals, and strategy playb... | <span class="badge badge-free">No API</span> |
| [Edge Hint Extractor]({{ '/en/skills/edge-hint-extractor/' | relative_url }}) | Extract edge hints from daily market observations and news reactions, with optional LLM ideation, and output canonica... | <span class="badge badge-free">No API</span> |
| [Edge Pipeline Orchestrator]({{ '/en/skills/edge-pipeline-orchestrator/' | relative_url }}) | Orchestrate the full edge research pipeline from candidate detection through strategy design, review, revision, and e... | <span class="badge badge-free">No API</span> |
| [Edge Signal Aggregator]({{ '/en/skills/edge-signal-aggregator/' | relative_url }}) | Aggregate and rank signals from multiple edge-finding skills (edge-candidate-agent, theme-detector, sector-analyst, i... | <span class="badge badge-free">No API</span> |
| [Edge Strategy Designer]({{ '/en/skills/edge-strategy-designer/' | relative_url }}) | Convert abstract edge concepts into strategy draft variants and optional exportable ticket YAMLs for edge-candidate-a... | <span class="badge badge-free">No API</span> |
| [Edge Strategy Reviewer]({{ '/en/skills/edge-strategy-reviewer/' | relative_url }}) | Critically review strategy drafts from edge-strategy-designer for edge plausibility, overfitting risk, sample size ad... | <span class="badge badge-free">No API</span> |
| [Exposure Coach]({{ '/en/skills/exposure-coach/' | relative_url }}) | Generate a one-page Market Posture summary with net exposure ceiling, growth-vs-value bias, participation breadth, an... | <span class="badge badge-free">No API</span> |
| [Finviz Screener]({{ '/en/skills/finviz-screener/' | relative_url }}) ★ | Build and open FinViz screener URLs from natural language requests | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [FTD Detector]({{ '/en/skills/ftd-detector/' | relative_url }}) | Detects Follow-Through Day (FTD) signals for market bottom confirmation using William O'Neil's methodology | <span class="badge badge-free">No API</span> |
| [Ibd Distribution Day Monitor]({{ '/en/skills/ibd-distribution-day-monitor/' | relative_url }}) | Detect IBD-style Distribution Days for QQQ/SPY (close down at least 0 | <span class="badge badge-api">FMP Required</span> |
| [Institutional Flow Tracker]({{ '/en/skills/institutional-flow-tracker/' | relative_url }}) | Use this skill to track institutional investor ownership changes and portfolio flows using 13F filings data | <span class="badge badge-api">FMP Required</span> |
| [Kanchi Dividend Review Monitor]({{ '/en/skills/kanchi-dividend-review-monitor/' | relative_url }}) | Monitor dividend portfolios with Kanchi-style forced-review triggers (T1-T5) and convert anomalies into OK/WARN/REVIE... | <span class="badge badge-free">No API</span> |
| [Kanchi Dividend SOP]({{ '/en/skills/kanchi-dividend-sop/' | relative_url }}) | Convert Kanchi-style dividend investing into a repeatable US-stock operating procedure | <span class="badge badge-free">No API</span> |
| [Kanchi Dividend US Tax Accounting]({{ '/en/skills/kanchi-dividend-us-tax-accounting/' | relative_url }}) | Provide US dividend tax and account-location workflow for Kanchi-style income portfolios | <span class="badge badge-free">No API</span> |
| [Macro Regime Detector]({{ '/en/skills/macro-regime-detector/' | relative_url }}) | Detect structural macro regime transitions (1-2 year horizon) using cross-asset ratio analysis | <span class="badge badge-free">No API</span> |
| [Market Breadth Analyzer]({{ '/en/skills/market-breadth-analyzer/' | relative_url }}) ★ | Quantifies market breadth health using Xone.VN's public CSV data | <span class="badge badge-free">No API</span> |
| [Market Environment Analysis]({{ '/en/skills/market-environment-analysis/' | relative_url }}) | Comprehensive market environment analysis and reporting tool | <span class="badge badge-free">No API</span> |
| [Market News Analyst]({{ '/en/skills/market-news-analyst/' | relative_url }}) ★ | This skill should be used when analyzing recent market-moving news events and their impact on equity markets and comm... | <span class="badge badge-free">No API</span> |
| [Market Top Detector]({{ '/en/skills/market-top-detector/' | relative_url }}) | Detects market top probability using O'Neil Distribution Days, Minervini Leading Stock Deterioration, and Monty Defen... | <span class="badge badge-free">No API</span> |
| [Options Strategy Advisor]({{ '/en/skills/options-strategy-advisor/' | relative_url }}) | Options trading strategy analysis and simulation tool | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Pair Trade Screener]({{ '/en/skills/pair-trade-screener/' | relative_url }}) | Statistical arbitrage tool for identifying and analyzing pair trading opportunities | <span class="badge badge-api">FMP Required</span> |
| [Parabolic Short Trade Planner]({{ '/en/skills/parabolic-short-trade-planner/' | relative_url }}) | Screen US equities for parabolic exhaustion patterns and generate conditional pre-market short plans, then evaluate i... | <span class="badge badge-api">FMP Required</span> |
| [PEAD Screener]({{ '/en/skills/pead-screener/' | relative_url }}) | Screen post-earnings gap-up stocks for PEAD (Post-Earnings Announcement Drift) patterns | <span class="badge badge-api">FMP Required</span> |
| [Portfolio Manager]({{ '/en/skills/portfolio-manager/' | relative_url }}) | Comprehensive portfolio analysis using Alpaca MCP Server integration to fetch holdings and positions, then analyze as... | <span class="badge badge-api">Alpaca Required</span> |
| [Position Sizer]({{ '/en/skills/position-sizer/' | relative_url }}) ★ | Calculate risk-based position sizes for long stock trades | <span class="badge badge-free">No API</span> |
| [Scenario Analyzer]({{ '/en/skills/scenario-analyzer/' | relative_url }}) | Build 18-month investment scenarios from news headlines | <span class="badge badge-free">No API</span> |
| [Sector Analyst]({{ '/en/skills/sector-analyst/' | relative_url }}) | This skill should be used when analyzing sector rotation patterns and market cycle positioning | <span class="badge badge-free">No API</span> |
| [Signal Postmortem]({{ '/en/skills/signal-postmortem/' | relative_url }}) | Record and analyze post-trade outcomes for signals generated by edge pipeline and other skills | <span class="badge badge-free">No API</span> |
| [Skill Designer]({{ '/en/skills/skill-designer/' | relative_url }}) | Design new Claude skills from structured idea specifications | <span class="badge badge-free">No API</span> |
| [Skill Idea Miner]({{ '/en/skills/skill-idea-miner/' | relative_url }}) | Mine Claude Code session logs for skill idea candidates | <span class="badge badge-free">No API</span> |
| [Skill Integration Tester]({{ '/en/skills/skill-integration-tester/' | relative_url }}) | Validate multi-skill workflows defined in CLAUDE | <span class="badge badge-free">No API</span> |
| [Stanley Druckenmiller Investment]({{ '/en/skills/stanley-druckenmiller-investment/' | relative_url }}) | Druckenmiller Strategy Synthesizer - Integrates 8 upstream skill outputs (Market Breadth, Uptrend Analysis, Market To... | <span class="badge badge-free">No API</span> |
| [Strategy Pivot Designer]({{ '/en/skills/strategy-pivot-designer/' | relative_url }}) | Detect backtest iteration stagnation and generate structurally different strategy pivot proposals when parameter tuni... | <span class="badge badge-free">No API</span> |
| [Technical Analyst]({{ '/en/skills/technical-analyst/' | relative_url }}) | This skill should be used when analyzing weekly price charts for stocks, stock indices, cryptocurrencies, or forex pairs | <span class="badge badge-free">No API</span> |
| [Theme Detector]({{ '/en/skills/theme-detector/' | relative_url }}) ★ | Detect and analyze trending market themes across sectors | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [Trade Hypothesis Ideator]({{ '/en/skills/trade-hypothesis-ideator/' | relative_url }}) | Generate falsifiable trade strategy hypotheses from market data, trade logs, and journal snippets | <span class="badge badge-free">No API</span> |
| [Trader Memory Core]({{ '/en/skills/trader-memory-core/' | relative_url }}) | Track investment theses across their lifecycle — from screening idea to closed position with postmortem | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Uptrend Analyzer]({{ '/en/skills/uptrend-analyzer/' | relative_url }}) | Analyzes market breadth using Monty's Uptrend Ratio Dashboard data to diagnose the current market environment | <span class="badge badge-free">No API</span> |
| [US Market Bubble Detector]({{ '/en/skills/us-market-bubble-detector/' | relative_url }}) ★ | Evaluates market bubble risk through quantitative data-driven analysis using the revised Minsky/Kindleberger framewor... | <span class="badge badge-free">No API</span> |
| [US Stock Analysis]({{ '/en/skills/us-stock-analysis/' | relative_url }}) ★ | Comprehensive US stock analysis including fundamental analysis (financial metrics, business quality, valuation), tech... | <span class="badge badge-free">No API</span> |
| [Value Dividend Screener]({{ '/en/skills/value-dividend-screener/' | relative_url }}) | Screen US stocks for high-quality dividend opportunities combining value characteristics (P/E ratio under 20, P/B rat... | <span class="badge badge-api">FMP Required</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [VCP Screener]({{ '/en/skills/vcp-screener/' | relative_url }}) ★ | Screen S&P 500 stocks for Mark Minervini's Volatility Contraction Pattern (VCP) | <span class="badge badge-free">No API</span> |
| [Vn Breakout Trade Planner]({{ '/en/skills/vn-breakout-trade-planner/' | relative_url }}) | Lập kế hoạch giao dịch breakout (long) cho cổ phiếu Việt Nam — pivot, stop, target R-multiple, position size lô 100, ... | <span class="badge badge-free">No API</span> |
| [Vn CANSLIM Screener]({{ '/en/skills/vn-canslim-screener/' | relative_url }}) | Screening tool for the Vietnam market using the CANSLIM methodology | <span class="badge badge-free">No API</span> |
| [Vn Daily Brief]({{ '/en/skills/vn-daily-brief/' | relative_url }}) | Báo cáo tổng hợp đầu ngày (Morning Routine) | <span class="badge badge-free">No API</span> |
| [Vn Data Fetcher]({{ '/en/skills/vn-data-fetcher/' | relative_url }}) | Lấy dữ liệu thị trường chứng khoán Việt Nam qua thư viện vnstock — OHLCV, thông tin niêm yết, lịch sử cổ tức, fundame... | <span class="badge badge-free">No API</span> |
| [Vn Dividend Screener]({{ '/en/skills/vn-dividend-screener/' | relative_url }}) | Sàng lọc cổ phiếu cổ tức cao bền vững cho Core portfolio Việt Nam | <span class="badge badge-free">No API</span> |
| [Vn Earnings Analyzer]({{ '/en/skills/vn-earnings-analyzer/' | relative_url }}) | Analyze earnings report reactions and post-earnings drift setups for the Vietnam stock market | <span class="badge badge-free">No API</span> |
| [Vn Economic Calendar]({{ '/en/skills/vn-economic-calendar/' | relative_url }}) | Lịch sự kiện vĩ mô Việt Nam — quyết định lãi suất SBV (định kỳ và bất thường), công bố GDP/CPI/FDI/xuất nhập khẩu của... | <span class="badge badge-free">No API</span> |
| [Vn ETF Screener]({{ '/en/skills/vn-etf-screener/' | relative_url }}) | Screen Vietnamese Exchange Traded Funds (ETFs) based on tracking error, premium/discount, expense ratio, and foreign ... | <span class="badge badge-free">No API</span> |
| [Vn Foreign Room Tracker]({{ '/en/skills/vn-foreign-room-tracker/' | relative_url }}) | Theo dõi room ngoại (foreign ownership room) cho watchlist cổ phiếu HOSE/HNX | <span class="badge badge-free">No API</span> |
| [Vn Margin Rules Monitor]({{ '/en/skills/vn-margin-rules-monitor/' | relative_url }}) | Monitor margin eligibility, tier rules, and Q-rated flags for Vietnam stocks | <span class="badge badge-free">No API</span> |
| [Vn Market Mechanics]({{ '/en/skills/vn-market-mechanics/' | relative_url }}) | Cơ chế thị trường chứng khoán Việt Nam — HOSE/HNX/UPCOM, biên độ giá ±7%/±10%/±15%, T+2 | <span class="badge badge-free">No API</span> |
| [Vn News Analyst]({{ '/en/skills/vn-news-analyst/' | relative_url }}) | Phân tích tin tức TTCK Việt Nam qua WebSearch và WebFetch | <span class="badge badge-free">No API</span> |
| [Vn PEAD Screener]({{ '/en/skills/vn-pead-screener/' | relative_url }}) | Screen for Post-Earnings Announcement Drift (PEAD) setups in the Vietnam market | <span class="badge badge-free">No API</span> |
| [Vn Portfolio Manager]({{ '/en/skills/vn-portfolio-manager/' | relative_url }}) | Quản lý danh mục cổ phiếu Việt Nam (VND) — thêm/bớt vị thế, theo dõi P&L sau phí 0 | <span class="badge badge-free">No API</span> |
| [Vn Position Sizer]({{ '/en/skills/vn-position-sizer/' | relative_url }}) | Tính số cổ phiếu tối ưu cho lệnh mua (long) trên TTCK Việt Nam dựa trên quản trị rủi ro — áp dụng lô 100, biên độ giá... | <span class="badge badge-free">No API</span> |
| [Vn Pullback Screener]({{ '/en/skills/vn-pullback-screener/' | relative_url }}) | Sàng lọc cổ phiếu Việt Nam đang pullback đẹp trong uptrend | <span class="badge badge-free">No API</span> |
| [Vn Sector Analyst]({{ '/en/skills/vn-sector-analyst/' | relative_url }}) | Phân tích rotation theo ngành VN-Index — tính return 5D/20D/60D theo ngành, relative strength vs VN-Index, top/bottom... | <span class="badge badge-free">No API</span> |
| [Vn Tax Fee Calculator]({{ '/en/skills/vn-tax-fee-calculator/' | relative_url }}) | Tính chi tiết phí broker + thuế bán 0 | <span class="badge badge-free">No API</span> |
| [Vn Trader Memory]({{ '/en/skills/vn-trader-memory/' | relative_url }}) | Quản lý vòng đời thesis giao dịch cho cổ phiếu Việt Nam — Plan → Trade → Record → Review → Improve | <span class="badge badge-free">No API</span> |
| [Vn VCP Screener]({{ '/en/skills/vn-vcp-screener/' | relative_url }}) | Sàng lọc cổ phiếu Việt Nam theo mô hình VCP (Volatility Contraction Pattern) của Mark Minervini, hiệu chỉnh cho biên ... | <span class="badge badge-free">No API</span> |
| [Vn30 Derivatives Planner]({{ '/en/skills/vn30-derivatives-planner/' | relative_url }}) | Lập kế hoạch giao dịch phái sinh VN30 Futures (VN30F1M, VN30F2M, VN30F1Q, VN30F2Q) | <span class="badge badge-free">No API</span> |

