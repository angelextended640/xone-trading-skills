# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary market: Vietnam (v0.2 — 2026-05-13)

This project is **Vietnam-first**. New skills target HOSE / HNX / UPCOM and follow the conventions below. International (US/JP) skills are retained for advanced users — do **not** delete or break them, but new development priority is the `vn-*` family.

### Naming and language conventions for new skills

- Skills targeting Vietnam use the prefix `vn-` (e.g. `vn-position-sizer`, `vn-foreign-room-tracker`)
- VN skill `SKILL.md`, in-skill `references/*.md`, report templates, and CLI error messages are written in **Vietnamese** as the primary language. SKILL.md `description:` should include both Vietnamese and English keywords so the skill triggers for users typing in either language.
- US/international skills keep their existing English content. When adapting a US skill for VN, **create a new `vn-<name>` skill** rather than adding a `--market=vn` flag (migration strategy chosen 2026-05-13).
- Japanese is no longer supported. `README.ja.md`, `PROJECT_VISION.ja.md`, and `docs/ja/` were removed on 2026-05-13. Do not generate new JA pages; the doc generator and `docs-completeness` hook only check EN.
- Reports use **VND** as currency and **Asia/Ho_Chi_Minh (UTC+7)** timezone. Format VND with thousands separators (e.g. `148,500,000 VND`). In JSON, store VND amounts as integer or float — never strings.

### Shared knowledge base — every `vn-*` skill must reference it

`skills/vn-market-mechanics/` is a knowledge-only skill (no scripts). When building a new `vn-*` skill, **read and cite** the relevant file rather than re-deriving rules:

- `references/vn_trading_rules.md` — sessions, T+2.5 settlement, short-selling restrictions, margin, status flags
- `references/vn_price_limits_orders.md` — ±7% (HOSE) / ±10% (HNX) / ±15% (UPCOM) bands, tick sizes (10/50/100 VND), order types, lot size 100
- `references/vn_fees_and_taxes.md` — broker fees (default 0.15%), 0.1% sale tax, 5% dividend tax, fee tables per broker
- `references/vn_foreign_ownership.md` — foreign room limits (49% default, 30% banks)
- `references/vn_data_sources.md` — `vnstock` library conventions, fallback sources, symbol/timezone conventions

### Data layer for `vn-*` skills

- Primary: `vnstock` (open source, wraps TCBS/SSI/VCI/VND APIs). Install via `pip install -e ".[vn]"` — declared as optional dependency in `pyproject.toml` under `[project.optional-dependencies] vn`.
- Pure-calculation VN skills (e.g. `vn-position-sizer`) do **not** depend on `vnstock` and must remain importable without it.
- VN data-fetching scripts should support `--data-source vci|tcbs|ssi` and `--fixture <path>` for offline tests.
- Cache OHLCV under `state/vn_market_data/<symbol>_<interval>.parquet`.

### VN-specific gotchas to bake into every relevant skill

1. **Lot size 100** — share counts must `floor` to multiples of 100; never round up
2. **Tick size** — HOSE varies by price band (10/50/100 VND); HNX/UPCOM uniform 100
3. **Price ceiling/floor** — every long plan must compute `ceiling_price` and `floor_price` from `reference_price × (1 ± band%)` and verify the stop is **above** floor (warn otherwise)
4. **T+2.5 settlement** — newly bought shares cannot be sold until afternoon of T+2; intraday flip strategies don't apply
5. **No short selling on cash equities** — only VN30 Futures (`vn30-derivatives-planner`) support short exposure
6. **Status flags** — skip stocks flagged Kiểm soát / Hạn chế / Tạm ngừng by default
7. **Fees and taxes are ~0.4% round-trip** — break-even threshold higher than US markets

### Migration strategy for US-coupled skills

The 25+ skills depending on FMP / FINVIZ / Alpaca stay in place. They are **not** being deleted or moved to a `legacy/` folder. The strategy is **additive**: build VN equivalents alongside (`vn-portfolio-manager` next to `portfolio-manager`, etc.). Users pick the version that matches their market.

## Repository purpose

This repository contains Claude Skills for equity investors and traders. Each skill packages domain-specific prompts, knowledge bases, and helper scripts. Skills work in both Claude's web app and Claude Code. Some skills require paid API subscriptions (FMP / FINVIZ Elite / Alpaca) — see the API key matrix in `docs/en/skill-catalog.md`.

## Repository architecture

### Skill structure

```
<skill-name>/
├── SKILL.md              # Required: skill definition with YAML frontmatter
├── references/           # Knowledge bases loaded into Claude's context
├── scripts/              # Executable Python scripts (not auto-loaded)
└── assets/               # Templates and resources for output generation
```

**SKILL.md format:**
- YAML frontmatter with `name` and `description` fields
- `name` must match the directory name for proper skill detection
- Description defines when the skill should be triggered
- Body uses imperative/infinitive verbs ("Analyze...", "Generate..."), not "You should..."
- Structure: Overview → When to Use → Workflow → Output Format → Resources

**Progressive loading:**
1. YAML frontmatter loads first for skill detection
2. SKILL.md body loads when skill is invoked
3. References load conditionally based on analysis needs
4. Scripts execute on demand, never auto-loaded into context

### Design patterns

- **Scripts vs. references** — scripts (`scripts/`) handle I/O (API calls, fetching, report generation); references (`references/`) hold knowledge for Claude to read and apply
- **Output** — reports save to `reports/` (markdown + JSON). Filename: `<skill>_<analysis-type>_<date>.{md,json}`. Scripts default `--output-dir reports/`
- **Knowledge bases** — declarative facts, decision frameworks, historical examples; organized hierarchically (H2 for major sections, H3 for subsections)

## Common development tasks

### Creating a new skill

Use the `skill-creator` plugin in Claude Code. It walks through: understanding → planning → initializing → editing → packaging → iterating.

**Mandatory after creating a new skill:**

1. **Generate documentation pages:**
   ```bash
   python3 scripts/generate_skill_docs.py --skill <skill-name>
   ```
2. Add to category sections in `docs/en/skill-catalog.md`
3. Add to API Requirements Matrix in `docs/en/skill-catalog.md`
4. Add description to `README.md` and `README.vi.md`
5. If API keys needed, add to the API Requirements table in `README.md`

> The `docs-completeness` pre-commit hook blocks commits if any `skills/*/SKILL.md` lacks a matching `docs/en/skills/<name>.md`. Run `generate_skill_docs.py` to fix.

### Documentation pages

```bash
# Auto-generate EN page + index update for one skill
python3 scripts/generate_skill_docs.py --skill <skill-name>

# Regenerate all auto-generated pages
python3 scripts/generate_skill_docs.py --overwrite
```

Hand-written ★ guides (10 sections — Overview, Prerequisites, Quick Start, How It Works, Examples, Output, Tips, Combining, Troubleshooting, Reference) are for key skills only. See `docs/README.md` for the template.

| Task | Auto-gen | Manual |
|------|----------|--------|
| EN doc page (`docs/en/skills/<name>.md`) | ✅ | -- |
| Index table (`docs/en/skills/index.md`) | ✅ | -- |
| Catalog category section (`docs/en/skill-catalog.md`) | -- | ✅ |
| API Requirements Matrix | -- | ✅ |
| README.md / README.vi.md | -- | ✅ |

### Packaging for distribution

```bash
python3 scripts/package_skill.py <skill-name>
```

Packaged `.skill` files live in `skill-packages/` and should be regenerated after any skill modification.

### Testing skills

1. Copy skill folder to Claude Code skills directory
2. Restart Claude Code to detect the skill
3. Trigger it with input matching the description
4. Verify: skill loads (YAML frontmatter), references load when needed, scripts handle errors, output matches the expected format

### TDD workflow

When generating or modifying code:
1. Write or update tests first (expected to fail initially)
2. Implement the minimal change to pass tests
3. Refactor while tests stay green
4. Run the relevant test suite before finishing

If no test exists for the changed behavior, add one whenever practical.

### Pre-commit hooks

Install after cloning:
```bash
pre-commit install && pre-commit install --hook-type pre-push
```

| Hook | What it checks |
|------|----------------|
| trailing-whitespace, end-of-file-fixer | Whitespace and trailing newline |
| check-yaml, check-toml, check-merge-conflict | Syntax and merge-conflict markers |
| check-added-large-files | Files exceeding 500KB |
| ruff, ruff-format | Python lint + format |
| codespell | Typo detection |
| detect-secrets | Secret/credential leaks |
| no-absolute-paths | `/Users/username/` path leaks in public repo |
| skill-frontmatter | SKILL.md `name` matches directory, `description` exists |
| docs-completeness | Every `skills/*/SKILL.md` has an EN doc page |
| pytest-pre-push | Runs all skill-level tests via `scripts/run_all_tests.sh` |

Suppress `no-absolute-paths` false positives with `# noqa: absolute-path`; the hook auto-skips regex definitions and test files. Config: `.pre-commit-config.yaml`; local scripts: `scripts/hooks/`.

## API key management

⚠️ Several skills require paid API subscriptions. The full per-skill matrix lives in `docs/en/skill-catalog.md`.

**Environment variables (preferred — all scripts accept these):**

```bash
export FMP_API_KEY=your_key       # Financial Modeling Prep — most US screeners
export FINVIZ_API_KEY=your_key    # FINVIZ Elite — optional, accelerates dividend screeners
export ALPACA_API_KEY=your_id     # Alpaca — portfolio-manager only
export ALPACA_SECRET_KEY=your_secret
export ALPACA_PAPER=true          # false for live trading
```

All API scripts fall back to `--api-key <key>` if the env var is absent.

**Pricing:**

- **FMP** — free 250 calls/day; Starter $29.99/mo (750/day); Professional $79.99/mo (2,000/day). [Sign up](https://site.financialmodelingprep.com/developer/docs)
- **FINVIZ Elite** — $39.50/mo or $299.50/yr. Optional but reduces dividend-screener time from 10–15 min to 2–3 min. [Sign up](https://elite.finviz.com/)
- **Alpaca** — paper trading free; live trading free brokerage, no commissions. Required for `portfolio-manager`. [Sign up](https://alpaca.markets/)

**Script pattern (all API scripts):**
1. Check env var first
2. Fall back to `--api-key` CLI argument
3. Clear error if missing
4. Retry with exponential backoff on rate limits

Per-skill CLI invocation examples live in `docs/en/skills/<skill-name>.md`. Multi-skill workflow recipes (Daily Market Monitoring, Earnings Momentum, Kanchi Dividend, Parabolic Short, Edge Research, Thesis-Driven Trading, etc.) live in `docs/en/development/multi-skill-workflows.md`.

## Conventions

### Analysis outputs

All analysis outputs must:
- Save to `reports/` (create if missing)
- Include date/time stamps
- Use English (or Vietnamese for `vn-*` skills — see VN section above)
- Provide probability assessments where applicable
- Include specific trigger levels for actionable scenarios
- Cite knowledge-base sources

### Script error handling

- Check for API keys before making requests
- Validate date ranges and input parameters
- Send errors to stderr; return non-zero exit codes
- Retry with exponential backoff on rate limits

### No personal information in committed files

This is a **public repository**. Never hardcode:

- **Absolute paths with usernames** (`/Users/username/...`) — use relative paths or `Path(__file__).resolve().parents[N]`
- **API keys / secrets** — use env vars or `.gitignore`-listed config files (`.mcp.json`, `.envrc`)
- **PII** — usernames, email addresses

Files containing secrets (`.mcp.json`, `.envrc`) must be in `.gitignore` and never committed.

## Legacy and infrastructure

### US skill family

The pre-v0.2 US-market skill family is retained. Each US skill has its own SKILL.md, references, scripts, and `docs/en/skills/<name>.md` page with full CLI examples. New US development is paused; bugfixes welcome. See `docs/en/skill-catalog.md` for the full list grouped by category.

A couple of legacy skills (`scenario-analyzer`, `stanley-druckenmiller-investment`) still contain Japanese text; prefer English when editing them.

### Auto-generated improvement and skill-creation pipelines

Two automated pipelines run on a daily/weekly cadence and produce PRs:

- **Skill self-improvement loop** — scores existing skills, runs improvement via Claude CLI, applies quality gate. Daily at 05:00 (macOS launchd).
- **Skill auto-generation** — mines session logs (weekly Saturday 06:00), designs new skills from highest-scoring backlog ideas (daily 07:00).

Full architecture, design decisions, and run/test commands: `docs/en/development/auto-pipelines.md`.

### Distribution

When skills are ready:

1. Test thoroughly in Claude Code
2. Package with `python3 scripts/package_skill.py <skill-name>` → moves `.skill` to `skill-packages/`
3. Update `README.md` and `README.vi.md` with skill description and API requirements
4. Commit with descriptive message

When the skill needs API keys, document setup (env var + CLI fallback), link to signup, and distinguish required vs. optional APIs.
