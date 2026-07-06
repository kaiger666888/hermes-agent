---
phase: 42-data-convergence
plan: 01
subsystem: data
tags: [plugin, pydantic, platform-metrics, schema, scope-discipline, option-a, tdd]

# Dependency graph
requires:
  - phase: 38-SLICE
    provides: variants[] schema (variant_id FK target)
  - phase: 39-FORM
    provides: plugins/formula_library/ (TuningSuggestion.formula_id FK target)
  - phase: 28-INGEST (v6.0)
    provides: agent/feedback_schema.py FeedbackRecord (READ ONLY — composed via feedback_id string FK)
provides:
  - plugins/platform_metrics/ plugin scaffold (kind=standalone, provides_tools=[])
  - PlatformMetrics Pydantic schema (DATA-01 — 5 metrics clamped [0.0,1.0])
  - FeedbackRecordExtension Pydantic model (DATA-02 — Option A composition via feedback_id string FK)
  - TuningSuggestion + MetricTrigger Pydantic shapes (DATA-03 — JSONL queue contract)
  - BasePlatformAdapter ABC + AdapterNotActivatedError + get_adapter factory
  - ADAPTER_REGISTRY empty dict + register_adapter(name, cls) helper (populated by Plan 42-02)
  - SUPPORTED_PLATFORMS_WITH_ADAPTERS 5-tuple constant (Plan 42-02 asserts against)
affects: [42-02 (adapter stubs), 42-03 (tuning_loop + library_writer), 42-04 (CLI + ref + SKILL.md), 43-VALIDATE]

# Tech tracking
tech-stack:
  added: []  # Pure stdlib + pydantic v2 + pyyaml — all already Hermes core deps
  patterns:
    - "Option A scope discipline: compose WITH v6.0 records via string FK, never import the class"
    - "Self-registration adapter registry (mirror tools/registry.py pattern)"
    - "Lazy import to break circular dep (adapters/__init__.py ↔ adapters/base.py)"
    - "Pydantic v2 field_validator + model_validator + ConfigDict(extra='forbid')"

key-files:
  created:
    - plugins/platform_metrics/plugin.yaml
    - plugins/platform_metrics/__init__.py
    - plugins/platform_metrics/schema.py
    - plugins/platform_metrics/adapters/__init__.py
    - plugins/platform_metrics/adapters/base.py
    - plugins/platform_metrics/README.md
    - plugins/platform_metrics/tests/__init__.py
    - plugins/platform_metrics/tests/test_plugin_registration.py
    - plugins/platform_metrics/tests/test_schema.py
    - plugins/platform_metrics/tests/test_adapter_base.py
  modified: []

key-decisions:
  - "Option A scope discipline applied: FeedbackRecordExtension composes with v6.0 FeedbackRecord via feedback_id STRING FK. Zero imports of agent.feedback_schema / agent.feedback_store (grep-enforced)."
  - "adapters/base.py shipped in Task 1 GREEN (not Task 3 as plan TDD order suggested) because register_adapter's issubclass gate required BasePlatformAdapter to exist. Same file, same contract, same plan — Rule 3 auto-fix of a blocking circular dependency."
  - "get_adapter factory raises KeyError (not ValueError) on unknown name — KeyError is the canonical 'unknown registry key' signal in Python (matches dict[k] semantics)."
  - "Async fetch contract: all 5 platforms are HTTP-based (httpx.AsyncClient) so the ABC declares async def fetch. v9.0 stubs in Plan 42-02 raise NotImplementedError after the env-key check; live HTTP path is V9-FUTURE-01 deferred."
  - "Platform Literal has 7 values (5 with adapters + 红果 + 视频号). SUPPORTED_PLATFORMS_WITH_ADAPTERS is the 5-tuple Plan 42-02 asserts against — separation lets variants[] carry platform slots without adapters."

patterns-established:
  - "Scope-discipline grep test pattern: subprocess.run(['grep', '-c', 'from agent.feedback_schema', path]) enforces zero v6.0 imports at test-time. Reusable in Plan 42-02/03/04."
  - "Pydantic range-clamp helper function (_in_unit_interval) shared across multiple field_validators — avoids duplicating the [0.0,1.0] check 5 times."
  - "Bilingual plugin README (EN structure + 中文 notes) — mirrors formula_library/README.md format."
  - "ADAPTER_REGISTRY as module-level mutable dict + register_adapter helper with issubclass gate. Self-registration at adapter module import time."

requirements-completed: [DATA-01, DATA-02]

# Metrics
duration: 7min
completed: 2026-06-27
---

# Phase 42 Plan 01: platform_metrics Plugin Scaffold + Option A Schema Summary

**Plugin scaffold + 3 Pydantic schemas (PlatformMetrics + FeedbackRecordExtension + TuningSuggestion) + BasePlatformAdapter ABC + factory, all composable with v6.0 FeedbackRecord via string FK (Option A — zero Hermes core imports).**

## Performance

- **Duration:** 7 min
- **Started:** 2026-06-26T17:01:16Z
- **Completed:** 2026-06-26T17:08:26Z
- **Tasks:** 3 (all TDD)
- **Files modified:** 10 (all new)

## Accomplishments

- Shipped the `plugins/platform_metrics/` plugin skeleton — kind=standalone, provides_tools=[] (Plan 42-04 adds the formula stats CLI hook). Loads via existing `hermes_cli/plugins.py` registry; zero core code changes.
- **PlatformMetrics** (DATA-01): 5 metric fields clamped to [0.0, 1.0] via shared `_in_unit_interval` helper + tz-aware `fetched_at` validator. 7-value `Platform` Literal covers the variants[] slot identifiers.
- **FeedbackRecordExtension** (DATA-02 Option A): composes WITH v6.0 `FeedbackRecord` via `feedback_id` string FK. Empty `platform_metrics` dict is valid (DATA-02 backward-compat — a v6.0 record with no platform data has no extension). Zero imports of `agent.feedback_schema` (grep-enforced).
- **TuningSuggestion + MetricTrigger** (DATA-03): 13-field shape mirroring `agent/evolution/queue.py:PatchRecord` + 4-value trigger enum. Ready for Plan 42-03's JSONL review queue.
- **BasePlatformAdapter ABC + AdapterNotActivatedError + get_adapter factory**: contract Plan 42-02's 5 stubs conform to. Lazy import breaks the circular dep between `adapters/__init__.py` and `adapters/base.py`.
- **31/31 tests GREEN** across 3 test files. 2 scope-discipline grep tests enforce the Option A invariant at test time.

## Task Commits

Each task was committed atomically (TDD RED → GREEN → test cycle):

1. **Task 1: Plugin scaffold + ABC** — RED `d8d5ce325` (test) → GREEN `718385638` (feat: plugin.yaml + __init__.py + adapters/__init__.py + adapters/base.py + README.md)
2. **Task 2: schema.py** — RED `0bd22500b` (test) → GREEN `f96737e4d` (feat: PlatformMetrics + FeedbackRecordExtension + TuningSuggestion + MetricTrigger)
3. **Task 3: test_adapter_base.py** — `bbda1c60d` (test: 8 tests for BasePlatformAdapter ABC + factory, all GREEN on first run since base.py shipped in Task 1)

**Plan metadata:** `pending` (docs: complete plan — will be the next commit)

## Files Created/Modified

All files NEW (zero modifications to existing files):

- `plugins/platform_metrics/plugin.yaml` — Manifest (name, version=0.1.0, kind=standalone, provides_tools=[])
- `plugins/platform_metrics/__init__.py` — `register(ctx)` entrypoint; no-op in Plan 01 (Plan 04 adds CLI hook)
- `plugins/platform_metrics/schema.py` — 3 Pydantic v2 models + Platform Literal + MetricTrigger enum + SUPPORTED_PLATFORMS_WITH_ADAPTERS constant
- `plugins/platform_metrics/adapters/__init__.py` — ADAPTER_REGISTRY empty dict + register_adapter helper with issubclass gate
- `plugins/platform_metrics/adapters/base.py` — BasePlatformAdapter ABC + AdapterNotActivatedError(RuntimeError) + get_adapter factory
- `plugins/platform_metrics/README.md` — Bilingual plugin README documenting Option A scope discipline + DATA-01..04 mapping + operator-action-handoff + V9-FUTURE-01 deferral
- `plugins/platform_metrics/tests/__init__.py` — Test package marker
- `plugins/platform_metrics/tests/test_plugin_registration.py` — 4 tests (plugin.yaml fields, register no-op, registry empty, register_adapter issubclass gate)
- `plugins/platform_metrics/tests/test_schema.py` — 19 tests (PlatformMetrics range clamps, FeedbackRecordExtension composition, TuningSuggestion round-trip, MetricTrigger enum, scope-discipline grep)
- `plugins/platform_metrics/tests/test_adapter_base.py` — 8 tests (AdapterNotActivatedError, ABC instantiation, env activation, factory lookup, scope-discipline grep)

## Decisions Made

1. **adapters/base.py shipped in Task 1 GREEN (not Task 3).** The plan's TDD order suggested Task 1 = scaffold and Task 3 = base.py, but Task 1's `register_adapter` test (#4: rejects non-subclass) requires `BasePlatformAdapter` to exist for the `issubclass` gate. Re-sequenced within the same plan (Rule 3 auto-fix of blocking circular dependency). No scope change — same files, same contract.
2. **get_adapter raises KeyError (not ValueError).** Canonical Python signal for "unknown registry key" — matches `dict[k]` semantics. Message includes registered names for operator visibility.
3. **Async fetch contract.** All 5 platforms are HTTP-based, so `async def fetch(variant_id) -> PlatformMetrics` is the ABC signature. Plan 42-02's stubs raise NotImplementedError after the env-key check; V9-FUTURE-01 ships the live httpx call.
4. **Platform Literal 7 values, SUPPORTED_PLATFORMS_WITH_ADAPTERS 5-tuple.** The 7-value Literal covers variants[] slot identifiers (红果 and 视频号 appear in Phase 38 variants but lack open APIs in v9.0). The 5-tuple is the contract Plan 42-02's registry keys must match exactly.
5. **Scope-discipline grep tests as test-time invariant.** Two tests (`test_feedback_record_extension_does_not_import_v6` in test_schema.py + `test_base_does_not_import_feedback_core` in test_adapter_base.py) grep the source files for forbidden imports. These run on every test invocation — any future regression that introduces a v6.0 import fails CI immediately.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] adapters/base.py shipped in Task 1 instead of Task 3**
- **Found during:** Task 1 (Plugin scaffold + plugin.yaml + __init__.py + adapters/__init__.py)
- **Issue:** Task 1's test `test_register_adapter_rejects_non_subclass` calls `register_adapter("foo", DummyClass)` and expects `TypeError`. The `register_adapter` implementation requires `BasePlatformAdapter` to exist for the `issubclass(cls, BasePlatformAdapter)` gate. Without base.py, the test cannot pass.
- **Fix:** Shipped `adapters/base.py` as part of Task 1 GREEN (instead of Task 3 GREEN). Task 3 then becomes the test layer (`tests/test_adapter_base.py`) exercising already-shipped behavior.
- **Files modified:** `plugins/platform_metrics/adapters/base.py` (moved from Task 3 deliverable to Task 1 deliverable)
- **Verification:** All 4 Task 1 tests GREEN; all 8 Task 3 tests GREEN on first run.
- **Committed in:** `718385638` (Task 1 GREEN) + `bbda1c60d` (Task 3 test commit)

**2. [Rule 2 - Missing Critical] Added scope-discipline grep test for adapters/base.py**
- **Found during:** Task 3 (test_adapter_base.py)
- **Issue:** Plan only specified a scope-discipline grep test for `schema.py`. The adapter layer is equally critical — it must not import v6.0 core (the adapter contract is independent of FeedbackRecord).
- **Fix:** Added `test_base_does_not_import_feedback_core` to test_adapter_base.py — greps adapters/base.py for both `agent.feedback_schema` and `agent.feedback_store` imports.
- **Files modified:** `plugins/platform_metrics/tests/test_adapter_base.py`
- **Verification:** Test passes; grep returns 0 for both forbidden imports.
- **Committed in:** `bbda1c60d` (Task 3 test commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical test coverage)
**Impact on plan:** Both auto-fixes necessary for correctness. Zero scope creep — same files, same contracts, same requirements (DATA-01 + DATA-02). The Rule 3 re-sequence is internal to Plan 42-01; downstream plans (42-02/03/04) see the same final contract.

## Issues Encountered

None. TDD cycles were clean: RED tests failed for the expected reasons (missing modules / missing classes); GREEN implementations passed on first run.

## User Setup Required

None — Plan 01 ships pure scaffold + schemas. The 5 platform API keys (DOUYIN_API_KEY / KUAISHOU_API_KEY / WEIXIN_VIDEO_API_KEY / XIAOHONGSHU_API_KEY / BILIBILI_API_KEY) are documented in the README's Operator-Action-Handoff section but are NOT required for Plan 01 (they activate Plan 42-02's adapter stubs). Plan 42-04 will patch `.env.example` with the documented key templates.

## Next Phase Readiness

- **Plan 42-02 (5 adapter stubs):** READY. `BasePlatformAdapter` ABC + `ADAPTER_REGISTRY` + `register_adapter` factory + `PlatformMetrics` schema all in place. Plan 42-02 ships 5 concrete subclasses that self-register via `register_adapter(name, cls)` at module import time. Integration test asserts `set(ADAPTER_REGISTRY.keys()) == set(SUPPORTED_PLATFORMS_WITH_ADAPTERS)`.
- **Plan 42-03 (tuning_loop + library_writer):** READY. `TuningSuggestion` + `MetricTrigger` schemas are in place. Plan 42-03 implements the trigger rules (HIGH_HOOK_DROPOFF > threshold etc.) and the JSONL queue under `<HERMES_HOME>/skills/.feedback/tuning/`.
- **Plan 42-04 (CLI + ref + SKILL.md):** READY. `register(ctx)` is a no-op hook waiting for `ctx.register_cli_command(name="formula", ...)` to be added in Plan 42-04. SKILL.md Step 15 body patch + `references/data-convergence.md` + `.env.example` patch all unblocked.
- **Phase 43 VALIDATE:** Plan 42-01 contributes the schema contract that VALIDATE-01's cross-phase integration checker will verify (variant_id FK from SLICE → PlatformMetrics; formula_id FK to FORM → TuningSuggestion).

**Blockers:** None.

## Scope Discipline Verification

| Check | Result |
|-------|--------|
| `grep -c "from agent.feedback_schema" plugins/platform_metrics/schema.py` | 0 ✓ |
| `grep -c "from agent.feedback_store" plugins/platform_metrics/schema.py` | 0 ✓ |
| `grep -c "from agent.feedback_schema" plugins/platform_metrics/adapters/base.py` | 0 ✓ |
| `grep -c "from agent.feedback_store" plugins/platform_metrics/adapters/base.py` | 0 ✓ |
| Files modified under `agent/` | 0 ✓ |
| Files modified under `hermes_cli/` | 0 ✓ |
| Files modified under `skills/movie-experts/` (FOUND-08) | 0 ✓ |
| Files modified outside `plugins/platform_metrics/` | 0 ✓ |

## Self-Check: PASSED

- All 10 created files verified present on disk.
- All 5 task commits verified in `git log` (`d8d5ce325` `718385638` `0bd22500b` `f96737e4d` `bbda1c60d`).
- 31/31 plugin tests GREEN (`python3 -m pytest plugins/platform_metrics/tests/ -v`).
- Scope-discipline grep checks all return 0.
- Zero files modified outside `plugins/platform_metrics/` + `.planning/`.

---

*Phase: 42-data-convergence*
*Plan: 01*
*Completed: 2026-06-27*
