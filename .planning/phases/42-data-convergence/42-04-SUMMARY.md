---
phase: 42-data-convergence
plan: 04
subsystem: cli-docs
tags: [cli, rich-tables, documentation, skill-md, env-vars, operator-handoff, data-convergence, step-15, found-08]

# Dependency graph
requires:
  - phase: 42-data-convergence
    provides: "Plan 42-01 (schema) + Plan 42-02 (adapters) — both shipped"
  - phase: 39-FORM
    provides: "plugins/formula_library/ (CLI reads library for stats)"
  - phase: 38-SLICE
    provides: "variants[] schema (data-convergence.md references)"
provides:
  - "hermes formula stats CLI subcommand (register_formula_cli + _formula_command + _cmd_stats)"
  - "Plugin CLI hook wiring (register(ctx) → ctx.register_cli_command)"
  - "references/data-convergence.md bilingual data-flow doc (338 lines, 10 sections)"
  - "SKILL.md Step 15 body section (additive, FOUND-08 preserved)"
  - "pipeline-dag.md Step 15 annotation (Step 14 + 6.5 preserved)"
  - ".env.example 5 platform API key documentation block"
affects: [43-VALIDATE (Step 14 → Step 15 wiring audit + FOUND-08 byte-diff)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Plugin CLI registration via ctx.register_cli_command (mirror google_meet pattern)"
    - "Defensive lazy import for parallel-plan dependency (queue.py from Plan 42-03)"
    - "Rich tables for operator dashboard (Formula Library Overview + Tuning Queue Summary)"
    - "JSON mode (--json flag) for scripting — no ANSI codes, valid JSON output"
    - "TDD: RED test commit → GREEN implementation commit per task"

key-files:
  created:
    - path: plugins/platform_metrics/cli.py
      lines: 348
      exports: ["register_formula_cli", "_formula_command"]
    - path: plugins/platform_metrics/tests/test_cli.py
      lines: 240
      tests: 9
    - path: skills/kais-movie-pipeline/references/data-convergence.md
      lines: 338
      sections: 10
  modified:
    - path: plugins/platform_metrics/__init__.py
      change: "register(ctx) body — added ctx.register_cli_command wiring"
    - path: skills/kais-movie-pipeline/SKILL.md
      change: "body-only — Step 15 section + References row (frontmatter byte-identical, FOUND-08 preserved)"
    - path: skills/kais-movie-pipeline/references/pipeline-dag.md
      change: "Step 15 section after Step 14 + See Also entry (Step 14 + 6.5 preserved)"
    - path: .env.example
      change: "appended 5 platform API key documentation block (commented out)"

decisions:
  - "Defensive lazy import of read_queue (Rule 3 — blocking-issue deviation): Plan 42-03 ships queue.py in parallel with this plan. cli.py wraps the import in try/except ImportError → returns zeros, so the CLI works whether or not queue.py has landed yet. Survives the parallel-race window AND the v9.0 stub scenario."
  - "Test 9 (register wiring) committed in Task 1 RED, made GREEN by Task 2 __init__.py patch. This follows the plan's instruction to place the test in test_cli.py even though it tests __init__.py — keeps all CLI-related tests in one file."
  - "JSON mode uses json.dumps(ensure_ascii=False, indent=2) — Chinese characters (genre / mood) render correctly in operator terminals with UTF-8 locales."
  - "Rich tables use title_style='bold cyan' + per-column styles (cyan / magenta / yellow) for visual hierarchy. Matches Hermes core rich usage patterns."
  - "scope discipline: logged Plan 42-03's test_library_writer.py failures (6 tests) to deferred-items.md — out of Plan 42-04 scope."

requirements-completed: [DATA-04]

# Metrics
duration: 14min
completed: 2026-06-27
---

# Phase 42 Plan 04: hermes formula stats CLI + data-convergence.md + Step 15 Summary

**Shipped the operator-facing observability + documentation layer for Phase 42 (DATA-04): `hermes formula stats` CLI subcommand registered via plugin hook, 338-line bilingual data-convergence.md ref, SKILL.md + pipeline-dag.md Step 15 additive patches (FOUND-08 byte-preserved), and .env.example operator-handoff for 5 platform API keys.**

## Performance

- **Duration:** ~14 min
- **Tasks:** 4 (1 TDD RED→GREEN + 3 atomic)
- **Files modified:** 7 (3 new + 4 patched)
- **Commits:** 5 (1 RED test + 4 task commits)

## Accomplishments

- **`hermes formula stats` CLI** (DATA-04 dashboard half): registers via `ctx.register_cli_command(name="formula", ...)` — auto-discovered at `hermes_cli/main.py:11942`, zero edits to main.py. Two modes: rich tables (Formula Library Overview + Tuning Queue Summary) by default; counts-only JSON via `--json` flag (no ANSI codes, valid JSON for scripting/jq).
- **data-convergence.md** (DATA-04 doc half, SC#5): 338-line bilingual reference with ASCII data-flow diagram, 10 sections (overview / data flow / schema / 5 platform adapters / trigger rules / JSONL lifecycle / dashboard usage / operator setup / Option A scope discipline / see-also). Mirrors ltx2-preview-loop.md + platform-master-slicing.md structure.
- **SKILL.md Step 15** (additive): new "## Step 15 — Data Convergence & Formula Tuning (Additive)" section after Step 14, before Asset Bus Schema. References table gets data-convergence.md row. Frontmatter byte-identical to `a2a20d2be` baseline (FOUND-08 milestone-wide preservation verified via diff).
- **pipeline-dag.md Step 15**: new "## Step 15 — Additive Extension (Phase 42 v9.0)" section mirroring Step 14 structure (purpose, DAG ASCII, does-NOT list, Phase 43 contract). Step 14 + Step 6.5 rows byte-preserved. See Also gets data-convergence.md bullet.
- **.env.example**: 5 platform API key documentation block appended (DOUYIN_API_KEY / KUAISHOU_API_KEY / WEIXIN_VIDEO_API_KEY / XIAOHONGSHU_API_KEY / BILIBILI_API_KEY), all commented out, with auth model notes (OAuth2 vs cookie-based) + cookie-rotation caveat + cross-ref to data-convergence.md §Operator Setup.
- **9/9 test_cli.py tests GREEN** covering argparse tree, dispatch logic, stats implementation, JSON mode, empty queue handling, register(ctx) wiring.
- **Scope discipline verified**: zero edits to `agent/*`, `hermes_cli/main.py`, `plugins/formula_library/*`, or any of the 16 `skills/movie-experts/*/SKILL.md` (FOUND-08 milestone-wide).

## Task Commits

| Task | Name | Commit | Type |
|------|------|--------|------|
| 1 RED | add failing tests for hermes formula stats CLI | `2086786b0` | test |
| 1 GREEN | implement hermes formula stats CLI | `64861398f` | feat |
| 2 | wire register(ctx) CLI hook + document 5 platform API keys | `5a22f7319` | feat |
| 3 | add data-convergence.md reference | `538c9830d` | docs |
| 4 | add Step 15 to SKILL.md + pipeline-dag.md (additive) | `dfdb110bf` | docs |

## Files Created/Modified

### Created (3 files)
- `plugins/platform_metrics/cli.py` — 348 lines. `register_formula_cli(subparser)` + `_formula_command(args)` + `_cmd_stats(args)` + `_emit_json(formulas, counts)` + `_emit_rich(formulas, counts)` + `_queue_counts(tuning_dir)` defensive helper.
- `plugins/platform_metrics/tests/test_cli.py` — 240 lines, 9 tests covering argparse tree, dispatch, stats rich/JSON modes, empty queue, register(ctx) wiring.
- `skills/kais-movie-pipeline/references/data-convergence.md` — 338 lines, 10 sections, ASCII data-flow diagram, MetricTrigger rules table, 5-platform operator setup, Option A scope discipline.

### Modified (4 files)
- `plugins/platform_metrics/__init__.py` — register(ctx) body extended from no-op to call `ctx.register_cli_command(name="formula", setup_fn=register_formula_cli, handler_fn=_formula_command, ...)`.
- `skills/kais-movie-pipeline/SKILL.md` — body-only patch: References table +1 row, Step 15 section inserted between Step 14 and Asset Bus Schema. Frontmatter byte-identical (FOUND-08 verified via `diff <(git show a2a20d2be:...SKILL.md | head -21) <(head -21 ...SKILL.md)` → no output).
- `skills/kais-movie-pipeline/references/pipeline-dag.md` — Step 15 section inserted after Step 14 (before Refresh Cadence). See Also +1 bullet. Step 14 + Step 6.5 + Step 1-13 sections byte-preserved.
- `.env.example` — appended 5 platform API key documentation block at end of file (after GOOGLE_CHAT section). All 5 keys commented out, with auth model + cookie-rotation notes + cross-ref to data-convergence.md.

## Decisions Made

1. **Defensive lazy import of `read_queue`** [Rule 3 — blocking-issue auto-fix]: Plan 42-03 ships `queue.py` in parallel with Plan 42-04. The CLI's `_queue_counts()` helper wraps `from plugins.platform_metrics.queue import read_queue` in try/except ImportError → returns zeros. This survives the parallel-race window (Plan 42-03 not yet landed when Plan 42-04 starts) AND the v9.0 stub scenario (no metrics collected yet, queue files absent). When Plan 42-03 ships, the same code works unchanged.

2. **Test 9 (register wiring) committed in Task 1 RED** per plan instruction. The plan explicitly says "add a single test to test_cli.py" for the register(ctx) wiring (even though it tests `__init__.py`). This keeps all CLI-related tests in one file. Task 1 GREEN ships 8/9 passing (Test 9 reserved for Task 2's `__init__.py` patch). Task 2 makes Test 9 GREEN.

3. **JSON mode uses `ensure_ascii=False`** so Chinese characters (genre = "都市奇幻", mood = "轻喜剧") render correctly in operator terminals with UTF-8 locales. Hermes core convention.

4. **Rich tables use `title_style="bold cyan"`** + per-column styles (cyan / magenta / yellow / right-justified numeric). Matches Hermes core rich usage patterns (CLI banners, dashboard panels).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Defensive lazy import of `read_queue` for parallel-race window**
- **Found during:** Task 1 (cli.py implementation start — discovered `queue.py` did not exist yet)
- **Issue:** Plan 42-04 explicitly imports `from plugins.platform_metrics.queue import read_queue` (per `<action>` block + `<interfaces>` block). Plan 42-03 ships `queue.py` in parallel. When Plan 42-04 starts, `queue.py` is absent → import would crash the CLI on every invocation.
- **Fix:** Wrapped the import in `_queue_counts()` helper with `try/except ImportError as exc: logger.debug(...); return zeros`. The CLI degrades gracefully whether or not Plan 42-03 has landed. When Plan 42-03 ships, the same code works unchanged.
- **Files modified:** `plugins/platform_metrics/cli.py` (the `_queue_counts()` helper is the deviation — not in the original plan's `<action>` block)
- **Verification:** All 9 tests pass both before AND after Plan 42-03's parallel ship. `test_formula_command_stats_empty_queue` explicitly covers the missing-queue.py scenario.
- **Committed in:** `64861398f` (Task 1 GREEN)

**2. [Rule 2 — Missing Critical] Logged Plan 42-03's test_library_writer.py failures to deferred-items.md**
- **Found during:** Post-task verification (full test suite run)
- **Issue:** `plugins/platform_metrics/tests/test_library_writer.py` has 6 failing tests (owned by Plan 42-03, commit `66597a1f3`). Root cause: tests construct `TuningSuggestion(status='approved', ...)` but `schema.py` declares `Literal['pending', 'applied', 'rejected']`.
- **Why NOT auto-fixed:** Out of scope — `test_library_writer.py` is Plan 42-03's RED gate waiting for its GREEN implementation. Scope discipline forbids Plan 42-04 from editing Plan 42-03's test files.
- **Fix:** Logged to `.planning/phases/42-data-convergence/deferred-items.md` per CLAUDE.md scope boundary rule. Plan 42-03 will resolve when it ships `library_writer.py`.
- **Files modified:** `.planning/phases/42-data-convergence/deferred-items.md` (new file)
- **Committed in:** (will be in final docs commit)

---

**Total deviations:** 2 (1 blocking-issue auto-fix + 1 missing-critical logging)
**Impact on plan:** Both deviations necessary for correctness. Zero scope creep — same files, same contracts, same requirement (DATA-04). The defensive import is forward-compatible (works before AND after Plan 42-03 ships).

## Issues Encountered

None — TDD cycle was clean. RED tests failed for expected reason (missing `cli.py` module); GREEN implementation passed on first run after the defensive-import deviation was applied.

## Authentication Gates

None — Plan 42-04 ships no live API calls. The 5 platform API keys are documented in `.env.example` but the adapters themselves are owned by Plan 42-02 (stubs raise NotImplementedError on the live HTTP path — V9-FUTURE-01 deferred).

## User Setup Required

**Operator-action-handoff (V9-FUTURE-01):** To activate live platform metrics ingestion, operator must:
1. Register developer accounts at the 5 platform developer portals (URLs in `data-convergence.md` §8).
2. Obtain credentials (OAuth2 app_id+app_secret for douyin/kuaishou/bilibili; cookies for weixin_video/xiaohongshu).
3. Uncomment + fill the 5 corresponding lines in `~/.hermes/.env` (templates in `.env.example`).
4. Restart hermes.
5. (V9-FUTURE-01) Implement live HTTP path in each adapter (currently raises NotImplementedError).

v9.0 ships the schema + adapter stubs + tuning loop + CLI dashboard + docs. The CLI dashboard works immediately (`hermes formula stats` shows formula library + zero-count queue) — it just won't have real metrics until V9-FUTURE-01.

## Known Stubs

None in Plan 42-04's deliverables. The CLI's "# Pending" column always shows "0" in v9.0 because `tuning_loop` is V9-FUTURE-01 deferred — but this is documented behavior (see Tuning Queue Summary table + the dim-text note about the Python API approve workflow), not a hidden stub. The `# Pending` column exists for forward-compat so operators see where suggestions will land once V9-FUTURE-01 ships.

## Scope Discipline Verification

| Check | Result |
|-------|--------|
| Files modified under `agent/` | 0 ✓ |
| Files modified under `hermes_cli/` (CLI registered via plugin hook) | 0 ✓ |
| Files modified under `skills/movie-experts/` (FOUND-08) | 0 ✓ |
| Files modified under `plugins/formula_library/` (Phase 39 READ ONLY) | 0 ✓ |
| Edits to `hermes_cli/main.py` | 0 ✓ (plugin CLI hook only) |
| SKILL.md frontmatter byte-identical to `a2a20d2be` (FOUND-08) | ✓ (diff produces no output on `head -21`) |
| pipeline-dag.md Step 14 + Step 6.5 rows byte-preserved | ✓ |
| Plan 42-01/02/03 owned files (schema.py / adapters/* / queue.py / tuning_loop.py / library_writer.py) modified | 0 ✓ (only `__init__.py` per plan — Plan 42-04 is its sole Wave 2 owner) |
| Plan 42-01 tests still pass (63/63) | ✓ |
| My plan's tests pass (9/9) | ✓ |

## FOUND-08 Verification (mandatory check)

```bash
$ diff <(git show a2a20d2be:skills/kais-movie-pipeline/SKILL.md | head -21) <(head -21 skills/kais-movie-pipeline/SKILL.md)
# (no output — byte-identical)
```

Frontmatter (lines 1-21: H1 heading + YAML `---` block with name / description / version / metadata.hermes.{tags, related_skills, expert_id, metrics, pipeline.{version, step_count=13, gate_count=8, parallel_shots=4}}) is byte-identical to the FOUND-08 milestone-wide frozen baseline.

## Self-Check: PASSED

**Files verified to exist:**
- [x] `plugins/platform_metrics/cli.py` — FOUND (348 lines, exports `register_formula_cli` + `_formula_command`)
- [x] `plugins/platform_metrics/tests/test_cli.py` — FOUND (240 lines, 9 tests)
- [x] `skills/kais-movie-pipeline/references/data-convergence.md` — FOUND (338 lines, 10 sections)
- [x] `.env.example` modified — FOUND (5 platform API key lines appended)

**Patches verified:**
- [x] `plugins/platform_metrics/__init__.py` — register(ctx) calls `ctx.register_cli_command(name="formula", ...)`
- [x] `skills/kais-movie-pipeline/SKILL.md` — Step 15 section present + References row added
- [x] `skills/kais-movie-pipeline/references/pipeline-dag.md` — Step 15 section + See Also bullet

**Commits verified in git log:**
- [x] `2086786b0` — test(phase-42-04): add failing tests for hermes formula stats CLI (RED)
- [x] `64861398f` — feat(phase-42-04): implement hermes formula stats CLI (GREEN)
- [x] `5a22f7319` — feat(phase-42-04): wire register(ctx) CLI hook + document 5 platform API keys
- [x] `538c9830d` — docs(phase-42-04): add data-convergence.md reference (DATA-04)
- [x] `dfdb110bf` — docs(phase-42-04): add Step 15 to SKILL.md + pipeline-dag.md (additive)

**Tests verified:**
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_cli.py -v` — 9 passed
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_schema.py plugins/platform_metrics/tests/test_adapter_base.py plugins/platform_metrics/tests/test_plugin_registration.py plugins/platform_metrics/tests/test_adapters.py -q` — 63 passed (no regressions on Plan 42-01/02)
- [x] FOUND-08 diff check produces no output (frontmatter byte-identical)

**Plan 42-03 parallel ship observed:**
- [x] `queue.py` + `tuning_loop.py` + `library_writer.py` all exist on disk by end of Plan 42-04 execution
- [x] `test_queue.py` 12 tests now GREEN (Plan 42-03 GREEN landed)
- [x] `test_library_writer.py` 6 tests still RED — Plan 42-03 RED gate (logged to deferred-items.md)

---

*Phase: 42-data-convergence*
*Plan: 04*
*Completed: 2026-06-27*
*FOUND-08 milestone-wide preservation verified.*
