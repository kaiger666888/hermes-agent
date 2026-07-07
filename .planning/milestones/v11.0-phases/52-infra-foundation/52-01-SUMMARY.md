---
phase: 52-infra-foundation
plan: 01
subsystem: infra
tags: [agent-registry, yaml-validation, jsonschema, draft-2020-12, lazy-cache, flat-glob]

# Dependency graph
requires: []
provides:
  - "agent.registry_loader.load_agent_registry — cached YAML discovery + Draft 2020-12 validation of ~/.hermes/agents/*.agent.yaml"
  - "agent.registry_loader.load_one_agent_yaml — single-file validation with JSON-path-specific error messages"
  - "agent.registry_loader.RegistryValidationError — single exception type for schema violations + filename invariant"
  - "3 fixture YAMLs (valid / malformed / name-mismatch) under tests/agent/fixtures/agents/"
  - "10-test pytest suite covering INFRA-01 SC#1 (valid/malformed/name-mismatch/caching/flat-glob)"
affects:
  - "52-02 (MCP tools wire-up) — agents_list + agent_describe consume load_agent_registry()"
  - "52-03 (round table state) — registry_loader supplies panelist identity snapshots"
  - "53 (creative slice) — 9-sample-agent transform YAMLs must pass schema validation"
  - "54 (eval harness) — fitness battery needs registry enumeration"

# Tech tracking
tech-stack:
  added: []  # zero new deps — jsonschema 4.26.0 + PyYAML 6.0.3 already pinned
  patterns:
    - "Lazy-load + double-checked-locking module cache (_REGISTRY_CACHE + _REGISTRY_CACHE_LOCK)"
    - "Draft202012Validator.iter_errors() sorted by absolute_path → first-error-wins reporting"
    - "JSON-path synthesis for required-violations (default err.json_path is bare '$' for root-level required errors; loader parses the missing field name out of the message to produce $.<field>)"
    - "Filename-stem invariant: data['name'] == yaml_path.name.removesuffix('.agent.yaml') (T-52-03 spoofing mitigation)"
    - "Flat glob('*.agent.yaml') — no recursive walk (Pitfall #8 from 52-RESEARCH.md)"

key-files:
  created:
    - "agent/registry_loader.py"
    - "tests/agent/test_registry_loader.py"
    - "tests/agent/fixtures/agents/test-coordinator.agent.yaml"
    - "tests/agent/fixtures/agents/malformed.agent.yaml"
    - "tests/agent/fixtures/agents/name-mismatch.agent.yaml"
  modified: []

key-decisions:
  - "Used e.json_path + special-case for required-validator: when validator=='required' and path is empty, parse the missing field name out of the message ('X' is a required property) and synthesize '$.<field>'. This satisfies the SC#1 acceptance criterion that the error message contains a literal '$.' marker."
  - "Deferred agent.registry_loader import inside the test file's _Registry fixture so pytest --collect-only succeeds under TDD RED (module not yet shipped). Each test still RED-fails at runtime with ModuleNotFoundError as expected."
  - "Quoted the date string in all 3 fixture YAMLs (transform_date: \"2026-07-07\") to prevent PyYAML auto-coercion to datetime.date — schema declares type: string and YAML 1.1 implicit-date-parsing violates that. Documented as Rule 1 deviation."

patterns-established:
  - "Pattern: agent YAML filename invariant — name field MUST match filename stem; load_one_agent_yaml enforces this AFTER schema validation passes"
  - "Pattern: flat-glob discovery for ~/.hermes/agents/*.agent.yaml (NOT recursive — distinct from skills/movie-experts/<category>/<name>/SKILL.md nested layout)"
  - "Pattern: RegistryValidationError carries a single specific message with file path + JSON path + violation text (e.g. 'path: schema violation at $.persona: ...')"

requirements-completed:
  - INFRA-01

# Metrics
duration: 6min
completed: 2026-07-07
---

# Phase 52 Plan 01: Agent Registry YAML Loader Summary

**Draft 2020-12 schema validation + lazy flat-glob discovery for `~/.hermes/agents/*.agent.yaml` with filename-stem invariant, JSON-path-specific error messages, and double-checked-locking cache**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-07T01:20:36Z
- **Completed:** 2026-07-07T01:27:12Z
- **Tasks:** 2 (TDD: RED then GREEN)
- **Files modified:** 5 (1 module + 1 test file + 3 fixture YAMLs)

## Accomplishments
- Shipped `agent/registry_loader.py` with the three public exports the rest of Phase 52 + Phase 53 will consume: `load_agent_registry`, `load_one_agent_yaml`, `RegistryValidationError`
- 10-test pytest suite covers all four SC#1 behaviors (valid/malformed/name-mismatch/caching) + the flat-glob invariant (Pitfall #8) + missing-agents-dir edge case
- Schema-violation errors cite a specific JSON path (`$.persona`, `$.version`, etc.) rather than a generic "schema validation failed", satisfying the SC#1 field-path acceptance
- Filename-stem invariant enforced AFTER schema validation so a schema-valid YAML with mismatched `name` surfaces a clean "does not match filename stem" error (T-52-03 spoofing mitigation)
- Zero new dependencies — `jsonschema 4.26.0` + `PyYAML 6.0.3` already pinned in `pyproject.toml`; no slopcheck gate triggered
- Module-level cache with double-checked locking mirrors the `providers/__init__.py:140 _discover_providers` pattern; `force_reload=True` returns a new list object

## Task Commits

Each task was committed atomically (TDD gate sequence: RED → GREEN):

1. **Task 1: RED tests + fixtures** — `5f53e9c1a` (`test`)
   - 3 fixture YAMLs (`tests/agent/fixtures/agents/{test-coordinator,malformed,name-mismatch}.agent.yaml`)
   - `tests/agent/test_registry_loader.py` (10 tests across 4 classes, deferred-import fixture so `pytest --collect-only` is clean)
2. **Task 2: GREEN implementation + Rule 1 fix** — `e18316a01` (`feat`)
   - `agent/registry_loader.py` (3 public exports + 2 private schema helpers + JSON-path formatter)
   - Fixture date-quote fix applied to all 3 YAMLs (Rule 1 deviation)

**Plan metadata commit:** this summary (docs).

## Files Created/Modified
- `agent/registry_loader.py` — INFRA-01 loader: flat-glob discovery + Draft 2020-12 validation + filename invariant + lazy cache
- `tests/agent/test_registry_loader.py` — 10 tests across 4 classes (TestValidYamlLoading, TestMalformedYamlRejection, TestNameFilenameMismatch, TestRegistryCaching)
- `tests/agent/fixtures/agents/test-coordinator.agent.yaml` — minimal valid synthetic agent (7 required fields + tags)
- `tests/agent/fixtures/agents/malformed.agent.yaml` — multi-violation negative fixture (omitted persona + 4 other violations; first sorted error is `$.persona`)
- `tests/agent/fixtures/agents/name-mismatch.agent.yaml` — schema-valid YAML with `name: wrong-name` (fails at filename invariant, NOT at schema)

## Decisions Made

1. **Synthesize JSON path for `required` violations.** jsonschema's `e.json_path` attribute returns `"$"` (no field suffix) for required-property violations because the path lives at the object root. The SC#1 acceptance criterion mandates a `"$.` substring in the error message. `_format_json_path()` detects `validator == "required"`, parses the missing field name out of the message (`'X' is a required property`), and synthesizes `"$.<field>"`. All other validator types use `e.json_path` directly. Verified against the malformed fixture: the actual error is `"schema violation at $.persona: 'persona' is a required property"`.

2. **Defer the `agent.registry_loader` import in tests via a pytest fixture.** The plan's Task 1 `<done>` criteria were internally contradictory: "tests collect cleanly under `pytest --collect-only`" AND "tests are RED because agent/registry_loader.py does not yet exist." A top-level `from agent.registry_loader import ...` fails collection entirely (not RED, just an error). The fix: a `_Registry` helper class with a lazy `_load()` method, accessed via the `registry` pytest fixture. Collection succeeds (test count visible); each test RED-fails at runtime with ModuleNotFoundError until Task 2 ships.

3. **Quote the date string in all 3 fixture YAMLs.** PyYAML's implicit-type-resolution auto-parses `transform_date: 2026-07-07` into a `datetime.date` object, but `agents-schema.yaml` declares `transform_date: type: string, format: date`. The first test run failed with `"$.lineage.transform_date: datetime.date(2026, 7, 7) is not of type 'string'"`. The fix quotes the date in the YAML so PyYAML preserves it as a string. This is a fixture-only fix; the loader itself is correct. Documented as Rule 1 deviation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed YAML schema/type mismatch in fixtures (date auto-coercion)**
- **Found during:** Task 2 (GREEN phase — first test run)
- **Issue:** All 3 fixture YAMLs had `transform_date: 2026-07-07` (unquoted). PyYAML's YAML 1.1 implicit-type-resolution parses this into a `datetime.date` object. The `agents-schema.yaml` declares `lineage.transform_date: type: string, format: date`. Schema validation failed on the valid fixture with `"$.lineage.transform_date: datetime.date(2026, 7, 7) is not of type 'string'"`, blocking all tests.
- **Fix:** Quoted the date string in all 3 fixtures (`transform_date: "2026-07-07"`) so PyYAML preserves the string type. The loader itself needed no change — the schema-vs-YAML impedance mismatch is purely a fixture authoring concern.
- **Files modified:** `tests/agent/fixtures/agents/test-coordinator.agent.yaml`, `tests/agent/fixtures/agents/malformed.agent.yaml`, `tests/agent/fixtures/agents/name-mismatch.agent.yaml`
- **Verification:** All 10 tests pass after the fix (verified by `pytest tests/agent/test_registry_loader.py -v` → 10 passed in 0.35s)
- **Committed in:** `e18316a01` (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** Fixture-only fix, no scope creep, no plan change. The schema-vs-YAML impedance mismatch is an operator trap worth flagging in Phase 53 (creative slice) where 9 real agent YAMLs get authored — operator must quote all date strings.

## Issues Encountered
- `e.json_path` returns bare `"$"` for required-property violations (root-level). Resolved by special-casing `validator == "required"` in `_format_json_path()` and parsing the missing field name out of the message. Verified against the malformed fixture: actual error is `"$.persona: 'persona' is a required property"`.
- jsonschema `format: date` is NOT enforced by default (no `format_checker` passed). This is fine — the schema's `type: string` constraint catches the type-mismatch case. Phase 53+ may add a `format_checker` if strict date validation becomes valuable.

## User Setup Required

None — no external service configuration required. The loader reads only local filesystem paths (`~/.hermes/agents/` via `get_hermes_home()` and `.planning/research/v10-orchestrator-design/agents-schema.yaml` via repo-relative path).

## Next Phase Readiness
- **Phase 52-02 (MCP tools wire-up):** Ready. `agents_list` and `agent_describe` MCP tools can import `load_agent_registry()` / `load_one_agent_yaml()` directly. The expected call pattern is documented in 52-RESEARCH.md §"MCP Tool Registration Pattern".
- **Phase 52-03 (round table state):** Ready. `round_table_open` will snapshot panelist identity by calling `load_one_agent_yaml()` to validate agent IDs before writing the state file.
- **Phase 53 (creative slice):** Ready. The 9 sample agent YAMLs must pass `load_one_agent_yaml()` validation before they ship; operators authoring those YAMLs should quote date strings and ensure `name == filename-stem` or the transform will fail at registry load time.
- **Blockers:** None.

## TDD Gate Compliance

TDD gate sequence verified in `git log --oneline`:
1. `5f53e9c1a` `test(52-01): add INFRA-01 SC#1 RED tests + fixtures for registry_loader` (RED gate)
2. `e18316a01` `feat(52-01): implement agent/registry_loader.py (INFRA-01 SC#1 GREEN)` (GREEN gate)

RED phase confirmed (post-Task-1): `pytest tests/agent/test_registry_loader.py -x` failed with `ModuleNotFoundError: No module named 'agent.registry_loader'` as expected. GREEN phase confirmed (post-Task-2): all 10 tests pass in 0.35s. No REFACTOR gate commit (no cleanup needed — implementation was clean on first GREEN).

## Self-Check: PASSED

All 6 created files exist on disk; both task commit hashes (`5f53e9c1a`, `e18316a01`) present in `git log`. Test suite verified green post-commit: `pytest tests/agent/test_registry_loader.py -v` → 10 passed in 0.35s. Ruff PLW1514 compliance verified: `ruff check agent/registry_loader.py tests/agent/test_registry_loader.py` → All checks passed.

---
*Phase: 52-infra-foundation*
*Completed: 2026-07-07*
