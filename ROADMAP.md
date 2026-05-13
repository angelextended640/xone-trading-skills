# Vietnam Stock Skills — Detailed Roadmap

**Last updated:** 2026-05-13 (Asia/Ho_Chi_Minh)
**Status:** Phase A + Phase B + Phase C + Phase D1/D2/D3 all complete. Remaining: Phase D4 (broker MCP integration) is opportunistic.

This document is the working roadmap for the `vn-*` skill family.
It replaces the in-flight `/plans/` file used during approval so the team
has a stable, reviewable artifact in-tree.

## TL;DR — where the project stands today

- **21 VN skills shipped, ~400 VN tests passing.**
- Phase A closed three strategic gaps (short tool, live universe build, learning loop).
- Phase B rounded out methodology coverage: `vn-canslim-screener`, `vn-earnings-analyzer`, `vn-pead-screener`, `vn-margin-rules-monitor`.
- Phase C delivered ship-readiness: local `scripts/package_skill.py`, CI testpaths covering all 21 VN skills, all `.skill` ZIPs committed under `skill-packages/`.
- Phase D stretches landed: `vn-etf-screener` (D1), `vn-daily-brief` composite (D2), Vietnamese documentation site under `docs/vi/` (D3).
- Post-implementation review (2026-05-13) caught + fixed: silent CI test omission for 6 new skills, broken Jekyll frontmatter on 75 VI doc pages (copy-pasted EN), stale `/ja/` lang_peer references, README/catalog/ROADMAP accuracy drift.

What remains: **D4 (broker MCP integration)** — opportunistic; depends on a VN broker shipping a stable public API.

---

## Status grid

| PR | Phase | Subject | Tests | Commit | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | A1 | `vn30-derivatives-planner` | 39 | `fac369b` | done |
| 2 | A2 | `vn-data-fetcher` extensions (`dividends`, `fundamentals`, `foreign-flow` snapshot) | 33 | `7241bd5` | done |
| 3 | A3 | `vn-trader-memory` | 27 | `ab6a158` | done |
| 4 | C3 | Fix 2 pre-existing pipeline test failures | 161/161 | `f3d289e` | done |
| 5 | C1 | Local skill-packaging script (`scripts/package_skill.py`) | 3 | pending | done |
| 6 | C2 | CI workflow + `pyproject.toml` testpaths cover all VN skills | n/a | pending | done |
| 7 | B1 | `vn-canslim-screener` | 15 | pending | done |
| 8 | B2 | `vn-earnings-analyzer` + `vn-pead-screener` | 30 | pending | done |
| 9 | B3 | `vn-margin-rules-monitor` | 13 | pending | done |
| 10 | C4 | Generate and commit `.skill` ZIPs for all VN skills | n/a | pending | done |
| 11 | D1 | `vn-etf-screener` | 12 | pending | done |
| 12 | D2 | `vn-daily-brief` composite skill | 8 | pending | done |
| 13 | D3 | Vietnamese documentation site (`docs/vi/`) | n/a | pending | done |
| 14 | D4 | Broker MCP integration | — | — | not started |

Phase D4 is intentionally opportunistic — pursue when a VN broker ships a stable public API worth wrapping.

---

## Phase A — Strategic value [COMPLETE]

Kept here for the audit trail. Detailed write-ups live in each skill's `SKILL.md`.

### A1. `vn30-derivatives-planner` — committed `fac369b`

Subcommands:

- `roll` — third-Thursday calendar + futures-vs-spot basis
- `hedge` — beta-adjusted contract count for cash-equity exposure
- `plan` — short/long full trade plan with initial-margin check
- `cost` — round-trip cost per contract across 10 CTCK

Multiplier 100,000 VND/point, tick 0.1 pt = 10,000 VND, IM ≈ 18%, T+0 cash-settled, **no sale tax** (key differentiator vs cash equities).

### A2. `vn-data-fetcher` extensions — committed `7241bd5`

Three subcommands added on top of `ohlcv` + `info`:

- `dividends` — `Company(symbol, source).dividends()`; normalises cash vs stock and converts `cash_dividend_percentage` (% of 10,000 VND par) into absolute VND/share
- `fundamentals` — `Vnstock().stock().finance.ratio(period=quarter|annual)`; emits P/E, P/B, ROE, EPS, payout
- `foreign-flow` — replaces the previous `NotImplementedError` stub with a **point-in-time snapshot** via `Trading().price_board()`. Daily series is explicitly **not** supported — users wanting time-series should use `vn-foreign-room-tracker record` with manual CSV ingest. We don't fake support we don't have.

Fixtures (`vic_dividends.csv`, `vic_fundamentals.csv`, `vic_foreign_flow_snapshot.json`) keep tests offline.

### A3. `vn-trader-memory` — committed `ab6a158`

Closes the Plan → Trade → Record → Review loop:

- **Lifecycle:** `IDEA → ENTRY_READY → ACTIVE → CLOSED|INVALIDATED` (forward-only; reaching `ACTIVE` is gated on entry data, reaching `CLOSED` is gated on exit data + valid `exit_reason`).
- **VN accounting in `close()`:** `gross_pnl_vnd`, `broker_fee_vnd` (0.15% × 2 by default), `sale_tax_vnd` (0.1%), `net_pnl_vnd`, `net_pnl_pct`. `--broker-fee-pct` lets private-banking tiers override the default.
- **Lot rule enforced** at schema + at `attach_position()` + at `open_position(shares=…)`.
- **MAE/MFE via `VNPriceAdapter`** (vnstock direct, fallback to `vn-data-fetcher` subprocess, `FixtureAdapter` for tests). T+0 and T+1 are skipped — shares aren't liquidatable, so including them would overstate excursions.
- **Default review interval = 5 days** (T+2.5 + 2 sessions to assess), down from the international 30.
- **State separation:** `state/vn_theses/` (YAML) and `state/vn_journal/` (postmortem markdown), distinct from international `state/theses/` / `state/journal/`.

Ingest adapters: `vn-vcp-screener`, `vn-pullback-screener`, `vn-dividend-screener`, `vn-breakout-trade-planner`. Idempotent on origin fingerprint.

---

## Phase B — Round out the screener / lifecycle stack

Goal: cover the remaining swing/event methodologies. Each item is independent; PR order is suggested, not mandatory.

### B1. `vn-canslim-screener`

**Why this matters:** CANSLIM is the third major swing methodology after VCP and pullback. The VN-adapted version rethinks **N** (new high — same 5% threshold as VCP), **L** (sector leader — wires into `vn-sector-analyst`), and **I** (institutional buying — uses foreign net flow from `vn-foreign-room-tracker` as a proxy, since VN funds don't publish 13F-equivalents). **M** (market direction) requires `vn-sector-analyst` regime ≠ `"risk-off"`.

**Deliverables:**

- `skills/vn-canslim-screener/SKILL.md` (Vietnamese primary)
- `skills/vn-canslim-screener/references/vn_canslim_methodology.md` — pillar definitions, VN-specific calibrations (foreign-room thresholds for "I", sector-leader rank for "L")
- `skills/vn-canslim-screener/scripts/vn_canslim_screener.py` — universe-JSON-in, ranked-candidates-out; 5-pillar score → A/B/C grade
- `skills/vn-canslim-screener/scripts/tests/` with synthetic fixtures
- `skills/vn-canslim-screener/references/sample_universe.json` — schema extends `vn-dividend-screener` universe with EPS growth fields

**Integration:** registers as an ingest source in `vn-trader-memory` (`growth_momentum` thesis type, abbr `grw`).

**Effort estimate:** ~2 days; 20-25 tests.

### B2. `vn-earnings-analyzer` + `vn-pead-screener` (paired)

**Why this matters:** VN earnings season runs Jan-Feb, Apr, Jul-Aug, Oct-Nov (the four quarterly close-out windows). PEAD (post-earnings announcement drift) is well-documented on the VN market — beat-and-rally patterns extend 5-20 sessions, especially when paired with a red-candle pullback that holds the report-day low.

**Two skills, one PR:**

- **`vn-earnings-analyzer`** — scores recent reports on five factors: (1) gap size on report day, (2) volume on report day, (3) pre-earnings 20-day trend, (4) MA50/MA200 position, (5) EPS surprise %. Consumes OHLCV from `vn-data-fetcher` + earnings dates from the user (or from `vn-data-fetcher`'s `fundamentals` subcommand when the company calendar endpoint is wired).
- **`vn-pead-screener`** — two modes: **Mode A** standalone (scan universe for drift candidates over a lookback), **Mode B** pipeline (consume `vn-earnings-analyzer` JSON, filter for grade ≥ B + red-candle pullback). Outputs entry-ready candidates with stop at report-day low and 2R targets.

**Pattern reuse:** heavy reuse of the international `skills/earnings-trade-analyzer/` and `skills/pead-screener/` scoring logic. The hard part is the **earnings-date source** — VN doesn't have a clean equivalent of FMP's earnings-calendar endpoint, so the initial release accepts user-provided dates with `vn-data-fetcher fundamentals` (the `report_date` field on quarterly ratios) as a fallback.

**Integration:** registers as ingest sources in `vn-trader-memory` (`earnings_drift` thesis type, abbr `ern`).

**Effort estimate:** ~3 days combined; 30-40 tests.

### B3. `vn-margin-rules-monitor`

**Why this matters:** before sizing a position, you want to know (a) is the candidate on the margin-eligible list at all, (b) at what tier, (c) is it Q-rated (control-warning status). Margin-eligible stocks have tighter spreads + better liquidity; force-sell cascades after gap-downs disproportionately hit Q-rated names. Knowing margin status pre-trade is risk-management hygiene.

**Deliverables:**

- `skills/vn-margin-rules-monitor/SKILL.md`
- `skills/vn-margin-rules-monitor/scripts/vn_margin_monitor.py` — subcommands: `record` (ingest a manually-curated CTCK margin list CSV), `check --symbol VIC` (lookup + tier), `report` (full distribution + recent changes), `history` (changes over time)
- `skills/vn-margin-rules-monitor/references/vn_margin_rules.md` — UBCKNN baseline rules, per-CTCK tier conventions, Q-rated list semantics, force-sell triggers
- State: `state/vn_margin/<broker>_margin_list.csv` (one per broker)
- Tests + sample fixtures

**Pattern reuse:** mirror `vn-foreign-room-tracker` (append-only history + record/report/history loop).

**Effort estimate:** ~1.5 days; ~20 tests.

---

## Phase C — Operational polish

Phase C3 already landed in PR 4. The remaining three items make the project releasable and CI-protected.

### C1. Local skill-packaging script — PR 5

**Why this matters:** without this, the 15 VN skills can't be distributed as `.skill` ZIPs for Claude web app users. The current `CLAUDE.md` line 173 references an external `skill-creator` plugin path that isn't checked in.

**Deliverable:** `scripts/package_skill.py` — pure-Python implementation:

- Reads a skill directory, validates `SKILL.md` frontmatter (name = directory name, description present), builds a ZIP archive of `SKILL.md` + `references/` + `scripts/` (exclude `tests/`, `__pycache__/`, fixture data).
- Output filename: `<skill-name>.skill` → `skill-packages/`.
- Unit tests in `scripts/tests/test_package_skill.py` using a temp skill directory fixture.
- Updates `CLAUDE.md:173` to reference the local script.

**Effort estimate:** ~1 day.

### C2. CI workflow auto-discovers testpaths — PR 6

**Why this matters:** `pyproject.toml:55-122` lists all skill test directories, but `.github/workflows/ci.yml:169-175` hard-codes pytest invocations. Adding a new skill to `pyproject.toml` doesn't get CI coverage — silently.

**Deliverable:** replace the hard-coded loop with `python -m pytest -q --co` (collect-only) for discovery, then run. Preserve the `KNOWN_SKIP` list (`theme-detector`, `canslim-screener`) via `--ignore-glob` flags so the existing skip list still applies.

**Verification:** local run of `python -m pytest --co -q skills/vn-*/scripts/tests/` should match what CI discovers.

**Effort estimate:** ~0.5 day.

### C4. Package and publish `.skill` ZIPs — PR 10

Run `scripts/package_skill.py` (from C1) against each `skills/vn-*` directory, commit the resulting `skill-packages/vn-*.skill` files, update `README.vi.md` with the "Use with Claude web app" section. Trivial work that depends on C1 being in.

**Effort estimate:** ~0.5 day.

---

## Phase D — Stretch / nice-to-have

Each is independent; pick up when interest aligns.

### D1. `vn-etf-screener`

Scan VN ETFs (VFMVN30, FUEVFVND, E1VFVN30, etc.) for tracking error, premium/discount to NAV, expense ratio, and foreign-room status. Useful for the Core portfolio sleeve — many VN investors hold one or two ETFs as a passive backbone.

### D2. `vn-daily-brief` composite skill

Single command that runs the morning routine: news scan + sector rotation + foreign-room delta + portfolio status. Wraps existing skills via subprocess. Lives in `skills/vn-daily-brief/`. The most "agent-y" skill in the family — composes rather than computes.

### D3. Vietnamese documentation site

`docs/` is English-only after the JA removal. A Jekyll `docs/vi/` tree mirroring `docs/en/` would help VN users who want web docs rather than reading `README.vi.md` + the per-skill `SKILL.md`. Lower priority because the in-repo Vietnamese coverage is already strong.

### D4. Broker MCP integration

If a VN broker exposes a clean public API (DNSE, SSI iBoard, and TCBS are the most likely candidates), a thin MCP server adapter would let Claude Code query live positions, place limit orders, monitor margin. Significant effort — one broker at a time. Worth doing only after confirming a broker's API is stable.

---

## Recommended execution order

If you only build **B1, B2, B3, C1, C2, C4** you cover the originally-planned methodology breadth + ship-readiness work. Suggested PR sequence:

1. **PR 5** — Phase C1, packaging script (~1 day) — unblocks C4
2. **PR 6** — Phase C2, CI workflow update (~0.5 day)
3. **PR 7** — Phase B1, `vn-canslim-screener` (~2 days)
4. **PR 8** — Phase B2, `vn-earnings-analyzer` + `vn-pead-screener` (~3 days)
5. **PR 9** — Phase B3, `vn-margin-rules-monitor` (~1.5 days)
6. **PR 10** — Phase C4, generate `.skill` packages, README updates (~0.5 day)

Total: ~8.5 working days. Phase D items are opportunistic.

---

## End-state after Phase B + remaining Phase C

- **19 VN skills shipped** (15 today + 4 new: `vn-canslim-screener`, `vn-earnings-analyzer`, `vn-pead-screener`, `vn-margin-rules-monitor`)
- **~400 VN tests** all passing
- **CI auto-discovers** all VN testpaths from `pyproject.toml` — no more silent skips
- **All 19 VN skills packaged** as `.skill` ZIPs in `skill-packages/`
- **Local packaging script** removes external-plugin dependency
- **End-to-end automation** demonstrated: live data fetch → screener → trade plan → portfolio record → postmortem, all within VN skills

---

## Cross-cutting verification (run after every PR)

```bash
# All VN tests pass
python -m pytest skills/vn-*/scripts/tests/ -q

# Pre-commit hooks green
python scripts/hooks/check_docs_completeness.py
python scripts/hooks/check_skill_frontmatter.py skills/*/SKILL.md

# No Japanese regression (one-off scan)
python -c "
import os, re
jpat = re.compile(r'[぀-ゟ゠-ヿ一-龯]')
hits = 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in {'.git', '.venv', 'node_modules', '__pycache__', '.claude', 'skill-packages', 'reports', 'state'}]
    for f in files:
        if not f.endswith(('.md', '.py', '.yml', '.yaml', '.json', '.toml', '.sh', '.txt')): continue
        p = os.path.join(root, f)
        try:
            with open(p, encoding='utf-8') as fh: txt = fh.read()
        except: continue
        if jpat.search(txt): hits += 1
print(f'JP files: {hits}')
"
```

At the end of Phase B: extend `examples/vn-daily-swing/run_demo.sh` to demo the CANSLIM + earnings flows end-to-end.

---

## Key files to read before starting each PR

| Phase | Files to study first |
| --- | --- |
| B1 | `skills/vn-vcp-screener/`, `skills/vn-dividend-screener/`, `skills/vn-sector-analyst/`, `skills/vn-foreign-room-tracker/` |
| B2 | `skills/earnings-trade-analyzer/`, `skills/pead-screener/`, `skills/vn-data-fetcher/scripts/vn_data_fetcher.py` (fundamentals) |
| B3 | `skills/vn-foreign-room-tracker/` (closest pattern match) |
| C1 | `scripts/hooks/check_skill_frontmatter.py`, `CLAUDE.md:173`, any external `package_skill.py` (for reference only) |
| C2 | `.github/workflows/ci.yml:169-175`, `pyproject.toml:55-122` |
| C4 | Depends on C1 shipping first |

---

## What is intentionally NOT in this plan

Some adjacent ideas surfaced in earlier audits but were deliberately deprioritised because they'd add scope without strategic leverage. They live here for completeness — revisit if the landscape changes.

- **Real-time intraday alerting.** Out of scope; this project is long-term memory + decision support.
- **Automated order routing.** Requires broker MCP first (D4), and even then is high-risk relative to the value vs the journaling story.
- **Backtest harness for VN skills.** International `backtest-expert` already exists and is parameterisable; rather than fork it, the recommendation is to feed VN OHLCV through it via universe JSON.
- **Translating `scenario-analyzer` / `stanley-druckenmiller-investment`.** Two legacy skills still contain some Japanese; per CLAUDE.md, edit them to English if touched, but don't fork to `vn-*` — international audience is small and the topics aren't VN-specific.

---

## Reviewing this plan

You can:

1. **Approve as-is** — proceed with PR 5 (C1, packaging script) next.
2. **Re-prioritise** — pick a different PR from the recommended order; each is self-contained.
3. **Cut scope** — drop any B/C/D item; the project remains shippable at Phase A.
4. **Add scope** — propose new VN skills; they slot into Phase B or Phase D.

Comments on this file or amendments via PR are both fine. The roadmap is meant to evolve.
