---
phase: 63-expert-registry-integration
plan: 02
subsystem: test
tags: [agent-registry, missing-expert-alarm, canary-test, pytest, caplog, tdd]

# Dependency graph
requires:
  - phase: 63-expert-registry-integration
    plan: 01
    provides: REQUIRED_DAG_EXPERTS frozenset + _check_required_experts pure helper + load_agent_registry_with_warnings sibling (Plan 01 shipped these 4 symbols in commit c8caee505)
provides:
  - TestMissingExpertAlarm pytest class (3 tests: fires + silent + sorted)
  - _stage_required_experts helper (copies 15 real DAG YAMLs into redirected HERMES_HOME)
  - _capture_missing_warnings helper (cache-reset + load + return warnings list)
affects: [63-04-integration-verification, 67-observability-phase]

# Tech tracking
tech-stack:
  added: []  # zero new packages — reuses pytest + pytest-asyncio from [dev] extra
  patterns:
    - "Real-YAML staging pattern: _stage_required_experts reads from _REAL_AGENTS_DIR (READ-ONLY constant) and writes via _agents_dir() (get_hermes_home-resolved, redirected per-test by _hermetic_environment autouse fixture)"
    - "caplog + structural-return dual verification: each test asserts BOTH the warnings list contains the expected expert_id AND a logger.warning citing that expert_id was captured by caplog (proves operator-visible alarm path)"
    - "Pitfall #6 enforcement: _capture_missing_warnings calls _reset_registry_cache() before loading so prior-test cache cannot poison the current test"

key-files:
  created: []
  modified:
    - tests/agent/test_registry_loader.py  # +138/-4 lines: import logging + _REAL_AGENTS_DIR + _stage_required_experts + _capture_missing_warnings + TestMissingExpertAlarm class (3 tests)

key-decisions:
  - "3 tests instead of 2: added test_alarm_warnings_sorted_when_multiple_missing to prove _check_required_experts returns sorted output (deterministic contract from Plan 01). The plan called this an 'optional 3rd test' but it was trivially cheap to add and locks the sorted contract."
  - "_REAL_AGENTS_DIR module-level constant (READ-ONLY source) documents Pitfall #2 mitigation inline: the staging helper ONLY writes via _agents_dir() (get_hermes_home-resolved), never via Path.home()."
  - "caplog.at_level(logging.WARNING, logger='agent.registry_loader') context manager captures the logger.warning emission — the canonical pytest log-capture pattern per 63-RESEARCH.md Example 2."
  - "pytest.skip() defensively if a source YAML is missing from real home (Phase 62 shipped all 21, but the canary should fail gracefully on incomplete operator environments)."

patterns-established:
  - "Canary fixture-staging pattern: real YAMLs read from READ-ONLY module-level Path constant + copied to redirected HERMES_HOME via shutil.copyfile. Reusable for any future test that needs to stage production YAMLs hermetically."

requirements-completed: [EXPERT-04]  # SC#2 canary now has automated pytest coverage

# Metrics
duration: 5min
completed: 2026-07-08
---

# Phase 63 Plan 02: Missing-Expert Alarm Canary Test Summary

**TestMissingExpertAlarm class (3 tests) added to tests/agent/test_registry_loader.py proving EXPERT-04 SC#2 — the missing-expert alarm fires when screenplay YAML is absent, is silent when all 15 required DAG experts are staged, and returns alphabetically-sorted warnings when multiple are missing**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-08T01:34:06Z
- **Completed:** 2026-07-08T01:38:48Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 1 (`tests/agent/test_registry_loader.py`, +138/-4)

## Accomplishments

- Added `TestMissingExpertAlarm` class with 3 test methods covering both EXPERT-04 SC#2 polarities + the sorted-output contract:
  - `test_alarm_fires_when_screenplay_missing` — stages 14-of-15 required DAG experts (omits `screenplay`), calls `load_agent_registry_with_warnings(force_reload=True)`, asserts `"screenplay" in warnings` AND a `logger.warning` citing screenplay + "missing" was captured by `caplog`.
  - `test_alarm_silent_when_all_15_present` — stages all 15 required DAG experts, asserts warnings list is `[]` AND no missing-expert `logger.warning` was emitted.
  - `test_alarm_warnings_sorted_when_multiple_missing` — stages 13-of-15 (omits `screenplay` + `hook_retention`), asserts warnings list equals `["hook_retention", "screenplay"]` (alphabetically sorted, mirroring `_check_required_experts`'s sorted set difference contract).
- Added `_stage_required_experts(exclude: set[str] | None = None)` module-level helper — copies each YAML in `REQUIRED_DAG_EXPERTS` (minus `exclude`) from the READ-ONLY `_REAL_AGENTS_DIR` to the redirected `_agents_dir()`. Defensive `pytest.skip()` if a source YAML is missing.
- Added `_capture_missing_warnings() -> list[str]` module-level helper — resets the registry cache (Pitfall #6 mitigation) then calls `load_agent_registry_with_warnings(force_reload=True)` and returns only the warnings list.
- Added `import logging` + `_REAL_AGENTS_DIR` module-level constant (READ-ONLY source path documenting Pitfall #2 mitigation inline).
- All 3 canary tests PASS. All 16 pre-existing test classes still PASS (no regression — full file: 19 passed in 0.55s).
- Real `/home/kai/.hermes/agents/` directory is provably untouched: 21 YAMLs still present after test run (acceptance criterion met).
- Zero `Path.home()` calls in the file — Pitfall #2 mitigation verified by `grep -c "Path.home()" tests/agent/test_registry_loader.py == 0`.

## Task Commits

Each phase of the TDD cycle was committed atomically:

1. **RED — test scaffolding + stub helpers** - `78a4d9396` (test)
   - Added `TestMissingExpertAlarm` class with 3 test methods + `_stage_required_experts` / `_capture_missing_warnings` as `NotImplementedError` stubs. All 3 tests fail at the stub call site, proving the test infrastructure is wired correctly before any implementation lands.

2. **GREEN — implement staging + capture helpers** - `411690eea` (feat)
   - Replaced the stubs with full implementations. All 3 tests now pass; all 16 pre-existing tests still pass.

_Note: no REFACTOR commit — the helpers are short (15 lines + 7 lines), single-responsibility, and the resulting code is clean. No duplication to extract._

## Files Created/Modified

- `tests/agent/test_registry_loader.py` - Added 4 new symbols at module level / class level:
  - `import logging` (top of file, alongside existing `shutil` / `Path` imports)
  - `_REAL_AGENTS_DIR = Path("/home/kai/.hermes/agents")` module-level constant (READ-ONLY source for staging)
  - `_stage_required_experts(exclude)` helper (copies 15 required DAG YAMLs to redirected home, omits `exclude` set)
  - `_capture_missing_warnings()` helper (cache-reset + load + return warnings)
  - `class TestMissingExpertAlarm` with 3 test methods (fires / silent / sorted)
  - Total diff: +138/-4 lines (the -4 is from reorganizing the existing import block to insert `import logging` + `_REAL_AGENTS_DIR`).

## Decisions Made

- **3 tests instead of 2:** The plan called the 3rd test (sorted-output) "optional" but it was trivially cheap (4 lines of assertions on top of the existing staging pattern) and locks the sorted-contract from Plan 01's `_check_required_experts`. If a future refactor accidentally drops the `sorted()` call, this test catches the regression.
- **`_REAL_AGENTS_DIR` as a module-level constant:** The plan's `<action>` step 1 specified copying from `/home/kai/.hermes/agents/{expert_id}.agent.yaml` inline. Hoisting it to a named constant with a docstring documenting the READ-ONLY constraint makes Pitfall #2 mitigation auditable at a glance.
- **`pytest.skip()` on missing source YAML:** Phase 62 shipped all 21 agents so this branch should never fire in practice. But the canary should degrade gracefully (skip with a clear message) rather than crash with `FileNotFoundError` if an operator's home is incomplete — defensive testing.
- **No REFACTOR phase:** The two helpers are short, single-responsibility, and CLAUDE.md-compliant out of the gate. A separate refactor commit would be ceremony for no value.

## Deviations from Plan

None - plan executed exactly as written. All 6 acceptance criteria from the plan's `<acceptance_criteria>` block verified green:

1. `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm::test_alarm_fires_when_screenplay_missing -x` exits 0.
2. `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm::test_alarm_silent_when_all_15_present -x` exits 0.
3. `python -m pytest tests/agent/test_registry_loader.py -x` exits 0 (full file — all 19 tests green, no regression).
4. `ls /home/kai/.hermes/agents/*.agent.yaml | wc -l` returns 21 after test run (real home untouched).
5. `grep -c "Path.home()" tests/agent/test_registry_loader.py` returns 0 (Pitfall #2 mitigation verified).
6. All 16 pre-existing test classes still pass (no regression).

## Issues Encountered

- **Pre-execution HEAD drift:** On agent spawn, the `<worktree_branch_check>` reported `BASE=d2c53ff55...` (not the expected `298bae66d...`), but the conditional reset did not appear to fire (HEAD was on a different lineage at first `git log`). A manual `git reset --hard 298bae66d0667ab44ab99021b863d87b9bcf7b1b` was required before any file edit. After reset, the test file appeared in the worktree at the correct lineage and edits applied cleanly. No data loss.
- **Worktree path safety (#3099):** Initial Edit tool calls used the absolute path `/data/workspace/hermes-agent/tests/agent/test_registry_loader.py` (the MAIN repo path, not the worktree path). The edits landed in the main repo, contaminating it. This was detected before commit and reverted via `git -C /data/workspace/hermes-agent checkout -- tests/agent/test_registry_loader.py`. All subsequent Edits used the worktree-rooted absolute path `/data/workspace/hermes-agent/.claude/worktrees/agent-a0880d51e728b8e77/tests/agent/test_registry_loader.py`. Lesson: in worktree mode, derive absolute paths from `git rev-parse --show-toplevel`, never from the orchestrator's cwd.

## User Setup Required

None - no external service configuration required. The canary runs entirely in pytest with the `_hermetic_environment` autouse fixture redirecting HERMES_HOME per-test. The READ-ONLY access to `/home/kai/.hermes/agents/` for fixture staging is satisfied by Phase 62's shipped 21 YAMLs (verified present: `ls /home/kai/.hermes/agents/*.agent.yaml | wc -l == 21`).

## Next Phase Readiness

- **Plan 03 (round table smoke):** Independent — proceeds in parallel Wave 2 (separate worktree, separate test file `tests/agent/test_phase63_round_table_smoke.py`). Plan 02 does not block Plan 03.
- **Plan 04 (integration verification):** Ready. The SC#2 canary now has automated pytest coverage (this plan). Plan 04 runs the inline SC#1 verification (`python3 -c "...assert len(r)==21..."`) and consumes the SC#2 test results from this plan.
- **Phase 67 OBSRV-01:** The `load_agent_registry_with_warnings` sibling (Plan 01) + the canary coverage (this plan) together prove the structured-data path the future observability collector will consume.
- **No blockers.**

## TDD Gate Compliance

This plan executed a single TDD task (`tdd="true"`). Gate sequence verified in git log:

1. **RED gate:** Commit `78a4d9396` — `TestMissingExpertAlarm` class + stub helpers. Verified RED by `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm -x` failing with `NotImplementedError: RED stub — implemented in GREEN step`. RED was genuine (helpers did not exist).
2. **GREEN gate:** Commit `411690eea` — `_stage_required_experts` + `_capture_missing_warnings` implementations. Verified GREEN by `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm -x -v` passing all 3 tests, plus full-file run `python -m pytest tests/agent/test_registry_loader.py` showing 19 passed (no regression).
3. **REFACTOR gate:** No separate refactor commit — the helpers are short (15 + 7 lines), single-responsibility, CLAUDE.md-compliant out of the gate. The plan's `<action>` step did not specify further refactoring.

## Self-Check: PASSED

Verified post-commit:

- `tests/agent/test_registry_loader.py` exists and is modified (1 file changed, +138/-4 across the two commits).
- Commit `78a4d9396` (RED) exists in `git log --oneline` on branch `worktree-agent-a0880d51e728b8e77`.
- Commit `411690eea` (GREEN) exists in `git log --oneline` on the same branch.
- `TestMissingExpertAlarm` class has 3 test methods — verified by `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm --collect-only -q` (3 items collected).
- All 3 canary tests PASS — verified by `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm -x` (3 passed in 0.36s).
- All 19 tests in the file PASS (no regression) — verified by `python -m pytest tests/agent/test_registry_loader.py` (19 passed in 0.55s).
- Real `/home/kai/.hermes/agents/` untouched — verified by `ls /home/kai/.hermes/agents/*.agent.yaml | wc -l == 21`.
- Zero `Path.home()` in the file — verified by `grep -c "Path.home()" tests/agent/test_registry_loader.py == 0`.

---
*Phase: 63-expert-registry-integration*
*Plan: 02*
*Completed: 2026-07-08*
