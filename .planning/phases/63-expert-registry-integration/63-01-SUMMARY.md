---
phase: 63-expert-registry-integration
plan: 01
subsystem: infra
tags: [agent-registry, missing-expert-alarm, observability, frozenset, logger-warning]

# Dependency graph
requires:
  - phase: 52-infra-foundation
    provides: load_agent_registry + load_one_agent_yaml + RegistryValidationError (v11.0 registry loader API)
  - phase: 62-expert-yaml-transform
    provides: 21 agent YAMLs at ~/.hermes/agents/*.agent.yaml (15 DAG + 6 supporting)
provides:
  - REQUIRED_DAG_EXPERTS frozenset (15 active DAG expert IDs, v10.0 §6.2 verbatim)
  - _check_required_experts pure helper (sorted set difference)
  - load_agent_registry_with_warnings sibling returning tuple[list[dict], list[str]]
  - _load_with_warnings shared implementation (logger.warning emission + structured return)
affects: [63-02-canary-test, 63-04-integration-verification, 67-observability-phase, 68-orchestrator-status-cli]

# Tech tracking
tech-stack:
  added: []  # zero new packages — Phase 63 installs nothing (RESEARCH §Package Legitimacy Audit)
  patterns:
    - "Sibling-function backward-compat pattern: existing load_agent_registry returns list[dict] unchanged; new load_agent_registry_with_warnings returns tuple for structured consumers"
    - "Pure helper pattern: _check_required_experts has no I/O, no logging — trivially testable with controlled input sets"
    - "Hard-coded required-set pattern (G1 Option A): REQUIRED_DAG_EXPERTS frozenset with §6.2 source citation, auditable as module constant"

key-files:
  created: []
  modified:
    - agent/registry_loader.py  # +167/-5 lines: REQUIRED_DAG_EXPERTS + _check_required_experts + _load_with_warnings + load_agent_registry_with_warnings + module docstring update

key-decisions:
  - "G1 Option A: hard-coded 15-expert frozenset from v10.0 §6.2 (not config-driven, not graph-closure) — stable since 2026-07-06, one-line edit in Phase 68 if operator needs override"
  - "G2 Option C: logger.warning for operator visibility + structured load_agent_registry_with_warnings sibling for Phase 67 OBSRV-01 collector — avoids breaking load_agent_registry callers (mcp_serve.py:1541, 1608)"
  - "6 supporting agents (animation_studio, documentary_maker, performer, production, scene_builder, storyboard_designer) intentionally NOT in required set — Pitfall #5 mitigation"
  - "Cache stores entries only (not tuple); warnings recomputed on every force_reload=True call — cheap set difference on ≤21 names"

patterns-established:
  - "Required-set alarm pattern: module-level frozenset + pure _check_* helper + thin forwarder preserving existing signature + sibling returning structured warnings"
  - "Backward-compat sibling pattern: when extending a load_* function with structured warnings, add a load_*_with_warnings sibling rather than changing the return type — existing callers stay unchanged"

requirements-completed: [EXPERT-04]  # partial — alarm scaffolding wired; Plan 02 canary proves it fires

# Metrics
duration: 3min
completed: 2026-07-08
---

# Phase 63 Plan 01: Missing-Expert Alarm Scaffolding Summary

**REQUIRED_DAG_EXPERTS frozenset (15 expert IDs, v10.0 §6.2 verbatim) + _check_required_experts pure helper + load_agent_registry_with_warnings sibling — load_agent_registry signature preserved for zero-caller-breakage**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-08T01:27:49Z
- **Completed:** 2026-07-08T01:30:35Z
- **Tasks:** 1
- **Files modified:** 1 (agent/registry_loader.py, +167/-5)

## Accomplishments

- Added `REQUIRED_DAG_EXPERTS` frozenset (15 active DAG expert IDs verbatim from v10.0 design doc §6.2) as a module-level constant with a docstring citing the source
- Added `_check_required_experts(loaded_names: set[str]) -> list[str]` pure helper — sorted set difference, no side effects, trivially testable
- Added `load_agent_registry_with_warnings(*, force_reload=False) -> tuple[list[dict], list[str]]` sibling for Phase 67 OBSRV-01 collector consumption
- Extracted `_load_with_warnings` shared implementation; rewrote `load_agent_registry` as a thin forwarder preserving the `list[dict]` return signature (zero caller breakage for mcp_serve.py:1541, 1608)
- Per-missing-expert `logger.warning` emission with lazy %-formatting (CLAUDE.md compliant) — operator-visible in `~/.hermes/logs/agent.log`
- Updated module docstring Public exports section to document the new sibling function and the REQUIRED_DAG_EXPERTS constant

## Task Commits

Each task was committed atomically:

1. **Task 1: Add REQUIRED_DAG_EXPERTS + _check_required_experts + sibling function to registry_loader.py** - `c8caee505` (feat)

_Note: TDD task — RED confirmed via inline `python3 -c` verification failing with ImportError on REQUIRED_DAG_EXPERTS; GREEN implemented the 4 new symbols; no REFACTOR needed (clean extraction)._

## Files Created/Modified

- `agent/registry_loader.py` - Added 4 new symbols (REQUIRED_DAG_EXPERTS, _check_required_experts, load_agent_registry_with_warnings, _load_with_warnings) + rewrote load_agent_registry as thin forwarder + updated module docstring Public exports section. Existing load_one_agent_yaml and RegistryValidationError unchanged.

## Decisions Made

- **G1 Option A (hard-coded 15-expert frozenset):** Followed RESEARCH recommendation. The 15-expert set is stable since v10.0 design (2026-07-06); config-driven adds parsing overhead for no v13.0 benefit; graph-closure is fragile (one typo silently drops an expert). Module-level constant with §6.2 source citation is trivially auditable.
- **G2 Option C (logger.warning + structured sibling):** Followed RESEARCH recommendation. Returning a tuple from `load_agent_registry` (Option B) would break every `for agent in load_agent_registry():` caller. The sibling-function pattern preserves the existing signature AND gives Phase 67 a structured-data path.
- **Cache stores entries only, not the tuple:** The warnings list is recomputed on every `force_reload=True` call. Rationale: operators who temporarily rename a YAML to trigger the alarm (canary test, manual triage) need the warning to fire even if the entries list was cached before the rename. The recompute is O(15) set difference — negligible.
- **No REFACTOR phase needed:** The extraction of `_load_with_warnings` from the original `load_agent_registry` body was done as part of the GREEN implementation directly — the resulting code is clean (single-responsibility helpers, thin forwarder, no duplication).

## Deviations from Plan

None - plan executed exactly as written.

- All 5 acceptance_criteria commands from the plan exit 0 (verified).
- All 16 existing tests in `tests/agent/test_registry_loader.py` pass unchanged (no caller breakage).
- The 6 supporting agents (animation_studio, documentary_maker, performer, production, scene_builder, storyboard_designer) are correctly NOT in `REQUIRED_DAG_EXPERTS` (Pitfall #5 avoided).
- `load_agent_registry()` returns `list[dict]`, NOT a tuple (Pitfall #1 avoided).
- `from __future__ import annotations` preserved at top; no f-strings in logger calls; `get_hermes_home()` used (no `Path.home()`); both `open()` calls have `encoding="utf-8"` — full CLAUDE.md compliance.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The alarm surfaces via `logger.warning` to the existing `~/.hermes/logs/agent.log` (no new log destination). The structured sibling is available for Phase 67 to consume; no operator action needed in v13.0.

## Next Phase Readiness

- **Plan 02 (canary test):** Ready. The `_check_required_experts` pure helper and `load_agent_registry_with_warnings` structured-return sibling give the canary test two verification paths — call `_check_required_experts` directly with a controlled input set (unit-level), OR call `load_agent_registry_with_warnings` after staging fixtures in redirected HERMES_HOME (integration-level). The `_reset_registry_cache()` helper in `tests/agent/test_registry_loader.py:127` is reusable.
- **Plan 03 (round table smoke):** Ready. `load_agent_registry` signature unchanged — the smoke's `agents_list` / `agent_describe` MCP tool calls continue to work without modification.
- **Plan 04 (integration verification):** Ready. The inline SC#1 command `python3 -c "from agent.registry_loader import load_agent_registry; r=load_agent_registry(); assert len(r)==21"` will pass (verified as AC5 in this plan).
- **Phase 67 OBSRV-01:** The `load_agent_registry_with_warnings` sibling is the structured-data input the future observability collector will consume.
- **No blockers.**

## TDD Gate Compliance

This plan executed a single TDD task (`tdd="true"`). Gate sequence verified:

1. **RED gate:** Confirmed via inline `python3 -c` verification command — failed with `ImportError: cannot import name 'REQUIRED_DAG_EXPERTS'` before any implementation. RED was genuine (feature did not exist).
2. **GREEN gate:** Implemented the 4 new symbols; inline verification passes; all 16 existing tests still pass.
3. **REFACTOR gate:** No separate refactor commit — the extraction of `_load_with_warnings` was done as part of GREEN (the plan `<action>` step 3 explicitly specified this extraction). Code is clean; no further refactor needed.

Note: This plan does NOT add a pytest test file (Plan 02 owns `tests/agent/test_registry_loader.py::TestMissingExpertAlarm`). The TDD verification for this plan uses the plan-specified inline `python3 -c` assertions (the `<verify>` block), which is appropriate for scaffolding-only work — the behavioral canary test belongs in Plan 02 per the plan's explicit scope boundary.

## Self-Check: PASSED

Verified post-commit:

- `agent/registry_loader.py` exists and is modified (1 file changed, +167/-5 in commit `c8caee505`).
- Commit `c8caee505` exists in `git log --oneline` on branch `worktree-agent-a0a623773e8e99839`.
- `load_agent_registry()` returns `list` (not `tuple`) — verified via AC3.
- `load_agent_registry_with_warnings()` returns `tuple[list, list]` — verified via AC4.
- `REQUIRED_DAG_EXPERTS` is `frozenset` of 15 — verified via AC2.
- Against real `~/.hermes/agents/` (21 YAMLs): `load_agent_registry_with_warnings(force_reload=True)` returns `(21 entries, 0 warnings)` — verified via AC5.

---
*Phase: 63-expert-registry-integration*
*Plan: 01*
*Completed: 2026-07-08*
