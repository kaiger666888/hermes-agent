---
phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto
plan: 02
subsystem: infra
tags: [cli, glm-4.6v, cost-tracking, metrics, rich-tables, argparse]

# Dependency graph
requires:
  - phase: 82-01
    provides: "DreaminaTaskMetrics with input_tokens/output_tokens/estimated_cost_usd fields + MetricsBuffer populated by dreamina_manager"
provides:
  - "register_glm_cli + _glm_command + _aggregate_glm_metrics + _emit_glm_rich + _emit_glm_json in dreamina_stats.py"
  - "hermes glm stats CLI subcommand (--json + --month flags) registered in __init__.py"
  - "Monthly + per-stratum GLM-4.6V cost aggregation with legacy-entry warning"
affects: [83]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Parallel CLI namespace registration (register_glm_cli mirrors register_dreamina_cli pattern — same MetricsBuffer, different aggregation)"
    - "Month extraction via ts[:7] slice for YYYY-MM grouping"
    - "Legacy entry detection via 'input_tokens' key presence (pre-v15.0 backward compat)"

key-files:
  created: []
  modified:
    - "plugins/kais_aigc/dreamina_stats.py — register_glm_cli + _glm_command + _cmd_glm_stats + _aggregate_glm_metrics + _emit_glm_rich + _emit_glm_json + _GLM_HELP_TEXT"
    - "plugins/kais_aigc/__init__.py — ctx.register_cli_command for 'glm' namespace"
    - "plugins/kais_aigc/tests/test_dreamina_stats.py — TestGlmCli class (10 tests)"

key-decisions:
  - "Reuses same MetricsBuffer JSONL as dreamina stats (single source of truth — no separate GLM log)"
  - "Legacy entries (no input_tokens key) counted in task_count but excluded from cost totals; warning to stderr"
  - "--month filter applies before aggregation (not after) so filtered months don't appear in output at all"
  - "Monthly table sorted ascending by month; stratum table sorted alphabetically"
  - "sys import added to module top (was previously lazy-imported via __import__ during initial draft — cleaned up)"

patterns-established:
  - "Parallel CLI namespace pattern: multiple register_*_cli functions reading same MetricsBuffer with different aggregation views"

requirements-completed: [XCUT-04c-CLI]

# Metrics
duration: 3min
completed: 2026-07-10
---

# Phase 82 Plan 02: XCUT-04c-CLI GLM Stats Subcommand Summary

**`hermes glm stats` CLI subcommand with monthly + per-stratum GLM-4.6V cost aggregation, --json/--month flags, and Rich table rendering — all reading from the same MetricsBuffer as `hermes dreamina stats`**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-10T13:16:36Z
- **Completed:** 2026-07-10T13:19:24Z
- **Tasks:** 2 (TDD: RED + GREEN for Task 1; direct implementation for Task 2)
- **Files modified:** 3 (1 source + 1 test + 1 registration)

## Accomplishments

- register_glm_cli creates "stats" subcommand with --json and --month YYYY-MM flags
- _glm_command dispatches: no subcommand → help (return 0), "stats" → dashboard, unknown → error (return 2)
- _aggregate_glm_metrics groups by month (YYYY-MM from ts[:7]) and by stratum, sums input_tokens + output_tokens + estimated_cost_usd
- Legacy entries (no input_tokens key) counted in task_count, contribute 0 tokens/cost, increment no_token_count
- _cmd_glm_stats reads MetricsBuffer, applies --month filter, warns on legacy entries (stderr), dispatches to Rich or JSON emitter
- _emit_glm_rich renders two Rich tables: monthly (Month | Task Count | Input Tokens | Output Tokens | Est. Cost USD) + per-stratum (Stratum | Task Count | Total Tokens | Est. Cost USD)
- _emit_glm_json emits {"monthly": {...}, "stratum": {...}} JSON for machine-readable output
- __init__.py registers "glm" CLI namespace via ctx.register_cli_command alongside existing "dreamina" registration
- 10 new tests added (TestGlmCli), all 17 tests in test_dreamina_stats.py passing

## Task Commits

Each task was committed atomically (TDD RED → GREEN for Task 1; direct for Task 2):

1. **Task 1 RED: Failing tests for GLM stats CLI** — `b2a9d8c` (test)
2. **Task 1 GREEN: register_glm_cli + _glm_command + aggregation** — `415d31f` (feat)
3. **Task 2: Register hermes glm CLI in __init__.py** — `f37832a` (feat)

## Files Created/Modified

- `plugins/kais_aigc/dreamina_stats.py` — Added _GLM_HELP_TEXT, register_glm_cli, _glm_command, _cmd_glm_stats, _aggregate_glm_metrics, _emit_glm_rich, _emit_glm_json; __all__ extended with register_glm_cli + _glm_command; sys import added to module top
- `plugins/kais_aigc/__init__.py` — Added ctx.register_cli_command for "glm" namespace with setup_fn=register_glm_cli, handler_fn=_glm_command; existing dreamina registration block unchanged
- `plugins/kais_aigc/tests/test_dreamina_stats.py` — Added TestGlmCli class (10 tests); imports extended with _aggregate_glm_metrics, _glm_command, _cmd_glm_stats, register_glm_cli

## Decisions Made

- **Same MetricsBuffer, different view** — `hermes glm stats` reads the exact same `dreamina_stats.jsonl` as `hermes dreamina stats`. No separate GLM log file. The two CLI commands are different aggregation views of the same underlying metric records (dreamina = latency/SLA view; glm = cost/token view).
- **--month filter pre-aggregation** — The month filter is applied to the raw metrics list BEFORE _aggregate_glm_metrics runs. This means filtered-out months don't appear in the output at all, rather than appearing with zero counts. Cleaner for both Rich and JSON output.
- **Legacy entry detection via key presence** — Entries are flagged as "no token data" if the `input_tokens` key is absent from the dict. This distinguishes pre-v15.0 entries (written before Plan 82-01 added the fields) from genuine zero-token entries (cache hits that legitimately consumed 0 tokens). The warning count reflects only true legacy entries.
- **sys import at module top** — During initial draft, `sys.stderr` was accessed via `__import__("sys")` inline. Cleaned up to a proper `import sys` at module top for clarity + Ruff compliance.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. The CLI reads the existing MetricsBuffer.

## Next Phase Readiness

- Plan 82-03 (XCUT-05-AUTO) is independent of this plan (lineage bump script in hermes-agent repo)
- Phase 83 (VALIDATE) will verify the CLI registration works end-to-end via `hermes glm stats` invocation
- Operators can now run `hermes glm stats` to monitor GLM-4.6V vision-verify spend

## TDD Gate Compliance

- [x] RED gate: `test(82-02)` commit exists (b2a9d8c)
- [x] GREEN gate: `feat(82-02)` commit exists after RED (415d31f)
- [x] All tests pass after GREEN phase (17/17 in test_dreamina_stats.py)

## Self-Check: PASSED

- [x] `plugins/kais_aigc/dreamina_stats.py` — FOUND (register_glm_cli + _glm_command + _aggregate_glm_metrics + _emit_glm_rich + _emit_glm_json)
- [x] `plugins/kais_aigc/__init__.py` — FOUND (ctx.register_cli_command for "glm")
- [x] `plugins/kais_aigc/tests/test_dreamina_stats.py` — FOUND (TestGlmCli with 10 tests)
- [x] Commit `b2a9d8c` — FOUND
- [x] Commit `415d31f` — FOUND
- [x] Commit `f37832a` — FOUND
- [x] Plan 82-01's 3 token fields preserved (DreaminaTaskMetrics unchanged)
- [x] All 17 tests pass
- [x] All open() calls have encoding="utf-8"

---
*Phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto*
*Completed: 2026-07-10*
