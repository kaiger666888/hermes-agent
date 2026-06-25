---
phase: 33
plan: 01
subsystem: observability-cli
tags: [observability, cli, curator, stats, read-only, feedback-loop, obs]
requires:
  - "P29 FeedbackStore.summary() (agent/feedback_store.py:990)"
  - "P31 read_queue (agent/evolution/__init__.py)"
  - "P32 read_audit (agent/curator_audit.py:345)"
  - "P32 register_cli extension pattern (hermes_cli/curator.py:994-1005)"
provides:
  - "hermes curator stats — per-skill / cross-skill / source-breakdown observability CLI (OBS-01/02/03)"
  - "_cmd_stats handler + _render_per_skill_dashboard / _render_cross_skill_view / _render_source_breakdown"
  - "_sparkline helper (unicode block chars per CONTEXT.md D-sparkline)"
  - "_collapse_verdicts helper (collapses FeedbackStore.summary() to per-verdict totals)"
affects:
  - "hermes_cli/curator.py (additive — new handler + helpers + subparser)"
  - "tests/hermes_cli/test_curator_stats.py (NEW — 18 tests across 8 classes)"
tech-stack:
  added: []
  patterns:
    - "P32 register_cli subparser extension (mirrored exactly)"
    - "Lazy in-handler imports (P31 runtime-isolation invariant preserved)"
    - "TDD RED → GREEN cycle (RED commit first, then GREEN commit)"
    - "rich.table.Table for human output (consistent with hermes_cli/bundles.py:52)"
    - "--json counts-only pattern (T-33-01 information-disclosure mitigation)"
key-files:
  created:
    - tests/hermes_cli/test_curator_stats.py
  modified:
    - hermes_cli/curator.py
decisions:
  - "D-stats-format: rich.table.Table for human; --json flag for machine (CONTEXT.md line 28) — honored"
  - "D-runs-default: --runs default 10 (CONTEXT.md line 33) — honored"
  - "D-json-counts-only: --json emits counts only, no correction text (CONTEXT.md line 29; research OQ#4) — honored + tested"
  - "D-empty-store: exit 0 + friendly message, mirrors P32 _cmd_audit_log (research OQ#2) — honored + tested"
  - "D-sparkline: unicode block chars ▁▂▃▄▅▆▇█ for mean_delta trend (CONTEXT.md line 35) — implemented in _sparkline"
  - "D-read-only: stats MUST NOT mutate any store (CONTEXT.md line 113) — honored + filesystem-snapshot tested"
  - "D-lazy-imports: ALL agent.* imports INSIDE _cmd_stats body (P32 runtime-isolation invariant) — honored + ast-walk tested"
metrics:
  duration: "~4.6 minutes (276s)"
  completed: "2026-06-25"
  tasks_complete: 2
  files_created: 1
  files_modified: 1
  tests_added: 18
  tests_passing: 18
  regression_tests_passing: 209
---

# Phase 33 Plan 01: `hermes curator stats` CLI Summary

Read-only observability surface (`hermes curator stats`) aggregating over the three shipped data stores from Phase 28-32 (FeedbackStore + evolution queue + audit log) to expose feedback-driven learning health for operators. Pure presentation layer: zero new persistence, zero new schema, zero new dependencies.

## What Shipped

### New CLI subcommand family (OBS-01/02/03)

```bash
# Per-skill dashboard — verdict buckets + patch history + eval-score trend
hermes curator stats <skill_id> [--runs N] [--json]

# Cross-skill view — top-N negative feedback + zero-feedback bundled list
hermes curator stats --all [--top N] [--json]

# Source breakdown — verdict distribution across cli / kais_aigc / manual
hermes curator stats --by-source [--skill <id>] [--json]
```

### Handler + render helpers (`hermes_cli/curator.py`)

- `_cmd_stats(args)` — dispatcher with lazy imports inside body (T-33-06).
- `_render_per_skill_dashboard` — OBS-01. Collapses `FeedbackStore.summary()` to per-verdict totals via `_collapse_verdicts`; pulls patch history from `read_queue(status="applied")`; pulls eval trend from `read_audit(action="apply")` filtered to entries with `eval_score`, bounded to last `runs` entries; renders sparkline via `_sparkline`.
- `_render_cross_skill_view` — OBS-02. Iterates all `summary()` buckets, tallies per-skill verdicts, computes neg_count = needs_work + bad, emits top-N; scans `~/.hermes/skills/movie-experts/` for bundled expert list, derives zero-feedback set.
- `_render_source_breakdown` — OBS-03. Calls `summary(source=s)` for each of cli/kais_aigc/manual, tallies verdicts.
- `_sparkline(values)` — unicode block chars `▁▂▃▄▅▆▇█` per CONTEXT.md D-sparkline. All-identical → middle-tier (index 4).
- `_collapse_verdicts(summary)` — input `{<skill>:<source>:<verdict>: {...}}`, output `{good/needs_work/bad: {count, weighted, first_ts, last_ts}}`.
- `_empty_store_message()` — friendly "no feedback yet" string (T-33-05).
- `_stats_hermes_home()` — `get_hermes_home()` indirection for readability.

### Subparser wiring (after P32 `p_auto` block at curator.py:1005)

6 flags: `skill_id` (positional, `nargs="?"`), `--all`, `--by-source`, `--top` (int, default 10), `--runs` (int, default 10), `--skill` (filter), `--json`. All surface in `hermes curator stats --help`.

## Test Coverage (18 tests, 8 classes)

| Class | Tests | Behavior |
|-------|-------|----------|
| `TestStatsPerSkill` | 2 | OBS-01 per-skill dashboard (3 verdicts rendered, title present) |
| `TestStatsAll` | 2 | OBS-02 cross-skill view (top negative, top-N limit) |
| `TestStatsBySource` | 1 | OBS-03 source breakdown |
| `TestRunsFlag` | 2 | OBS-01 `--runs N` trend depth + default-10 |
| `TestJsonOutput` | 2 | T-33-01 counts-only (no `correction` key in payload; no leak phrase in stdout) |
| `TestEmptyStore` | 3 | T-33-05 exit 0 + friendly message (all 3 modes) |
| `TestReadOnly` | 1 | T-33-02 filesystem snapshot — zero mutations across all 3 modes |
| `TestLazyImportIsolation` | 3 | T-33-06 zero module-level agent.evolution imports + subparser resolves all flags |
| `TestNoNewSubcommandBreakage` | 2 | P32 subcommands still resolve + stats registered |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sha256 non-hex in `_seed_verdicts` test helper**
- **Found during:** Task 1 RED state — collection succeeded but first test raised pydantic ValidationError on `OutputSnapshot.sha256`.
- **Issue:** Initial helper used `verdict[0]` (e.g. "g", "n", "b") as the sha prefix — not hex characters. OutputSnapshot validator requires `[0-9a-fA-F]{64}`.
- **Fix:** Mapped verdicts to hex prefix chars (`good→a`, `needs_work→b`, `bad→c`) and used `f"{prefix}{idx:063d}"[:64]` to produce 64-char hex strings.
- **Files modified:** `tests/hermes_cli/test_curator_stats.py`
- **Commit:** `73edd32e2`

**2. [Rule 1 - Bug] Fixed `skill_0..skill_4` invalid skill_ids in TestStatsAll**
- **Found during:** Task 2 GREEN run — FeedbackRecord validator rejected `skill_0` etc. as not-a-known-movie-expert.
- **Issue:** Used synthetic `skill_{i}` IDs for the top-N test; FeedbackRecord schema validates skill_id against the bundled expert list.
- **Fix:** Swapped to real bundled names: `screenplay`, `editor`, `colorist`, `composer`, `animator`. Adjusted assertions accordingly.
- **Files modified:** `tests/hermes_cli/test_curator_stats.py`
- **Commit:** `3d6a03424`

**3. [Rule 1 - Bug] Fixed `z*64` non-hex sha256 in TestJsonOutput**
- **Found during:** Task 2 GREEN run — same ValidationError class as deviation #1.
- **Issue:** Used `"z" * 64` as the sha256 for the leak-phrase test record.
- **Fix:** Swapped to `"f" * 64` (valid hex).
- **Files modified:** `tests/hermes_cli/test_curator_stats.py`
- **Commit:** `3d6a03424`

## Authentication Gates

None — pure CLI read path with no auth surface.

## Known Stubs

None — every data source is wired to its shipped P29/P31/P32 query API. No placeholder text, no mock data paths in production code.

## Threat Flags

None — the plan's `<threat_model>` covered all introduced surface (T-33-01 through T-33-06). The `--json` boundary is the only new trust-crossing output path and it is explicitly mitigated as counts-only with an automated assertion.

## TDD Gate Compliance

- [x] RED gate commit exists: `73edd32e2 test(33-01): add RED tests for hermes curator stats (OBS-01/02/03)` — 16/18 tests failed with `AttributeError: module 'hermes_cli.curator' has no attribute '_cmd_stats'` and `argparse.ArgumentError: invalid choice: 'stats'`. The 2 passing tests were pre-existing structural invariants (no module-level agent.evolution imports today; P32 subcommands still resolve).
- [x] GREEN gate commit exists: `3d6a03424 feat(33-01): implement hermes curator stats (OBS-01/02/03, GREEN)` — 18/18 tests pass after implementation.
- [x] REFACTOR gate: skipped (no refactor needed; GREEN implementation is clean).

## Self-Check: PASSED

**Files verified to exist:**
- [FOUND] `tests/hermes_cli/test_curator_stats.py` (created)
- [FOUND] `hermes_cli/curator.py` (modified — additive)

**Commits verified to exist:**
- [FOUND] `73edd32e2` — `test(33-01): add RED tests for hermes curator stats (OBS-01/02/03)`
- [FOUND] `3d6a03424` — `feat(33-01): implement hermes curator stats (OBS-01/02/03, GREEN)`

**Verification commands re-run:**
- `python -m pytest tests/hermes_cli/test_curator_stats.py -x`: 18 passed in 0.73s
- `ruff check hermes_cli/curator.py`: All checks passed
- `python -m pytest tests/hermes_cli/test_curator_cli.py tests/agent/test_feedback_store.py tests/agent/test_audit_log.py tests/agent/evolution/`: 209 passed (regression)
- `hermes curator stats --help`: lists all 6 flags
- `grep -c '^from agent\.evolution\|^import agent\.evolution' hermes_cli/curator.py`: 0
- `git diff --name-only HEAD~2 HEAD -- skills/movie-experts/`: empty (FOUND-08 preserved)
