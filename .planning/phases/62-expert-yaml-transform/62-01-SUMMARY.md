---
phase: 62-expert-yaml-transform
plan: 01
subsystem: testing
tags: [validation, infra, jsonschema, argparse, wave-0]

# Dependency graph
requires: []
provides:
  - "scripts/validate_phase62_yamls.py — argparse CLI validator for agent YAMLs (SC#2 gate)"
  - "--batch A / --batch B CLI contract cited verbatim by Plan 02 / 03 acceptance criteria"
  - "Draft202012Validator.iter_errors() pattern with sorted-by-json-path ordering"
affects: [62-02, 62-03, 62-04]

# Tech tracking
tech-stack:
  added: []  # zero new packages — PyYAML + jsonschema + hashlib all pre-existing in pyproject.toml core
  patterns:
    - "get_hermes_home() resolved per-call (NOT at module import) so conftest HERMES_HOME redirect works"
    - "Draft202012Validator.iter_errors() sorted by list(e.absolute_path) — surfaces ALL errors deterministically"
    - "yaml.safe_load only (T-62-01 tag-injection mitigation); never yaml.load"

key-files:
  created:
    - "scripts/validate_phase62_yamls.py"
    - "tests/scripts/test_validate_phase62_yamls.py"
  modified: []

key-decisions:
  - "Resolve HERMES_HOME per-call, not at module import — test isolation requires conftest redirect to work"
  - "Glob *.agent.yaml at runtime (do NOT hardcode 21) — Wave 0 runs against 9 shipped YAMLs, Wave 1 adds 6+6, Wave 2 completes 21"
  - "Date strings in agent YAMLs MUST be quoted (single or double) to bypass PyYAML's auto date-object parsing — mirrors shipped YAML convention"

patterns-established:
  - "Wave 0 validation infra pattern: Plan 02/03/04 cite `python3 scripts/validate_phase62_yamls.py --batch {A|B}` verbatim in acceptance_criteria"
  - "Per-call get_hermes_home() for any code path that reads ~/.hermes/* AND is exercised by tests using _hermetic_environment fixture"

requirements-completed: [EXPERT-02]

# Metrics
duration: 12min
completed: 2026-07-08
---

# Phase 62 Plan 01: Wave 0 Validator Summary

**Batch jsonschema.Draft202012Validator CLI script for agent YAMLs — the SC#2 gate cited by Plan 02/03/04 acceptance criteria (no new deps, executable, 9/9 PASS today + loud MISSING on the 6 unshipped Wave-1-A names)**

## Performance

- **Duration:** ~12 min
- **Tasks:** 1 (TDD: RED → GREEN)
- **Files created:** 2 (script + test)
- **Lines added:** 547 (225 script + 322 tests)
- **New deps installed:** 0 (PyYAML 6.0.3 + jsonschema 4.26.0 + hashlib stdlib — all pre-existing)

## Accomplishments

- `scripts/validate_phase62_yamls.py` is the canonical SC#2 byte-pass `Draft202012Validator.validate()` gate for Plan 02/03/04
- No-arg invocation globs `*.agent.yaml` under `$HERMES_HOME/agents/` — exits 0 with `OK: 9/9` against the 9 v11.0-shipped YAMLs
- `--batch A` / `--batch B` target the 6-name constant lists Plan 02/03 will cite verbatim
- Missing files surface as `MISSING {name}: {path}` and exit 1 (proves the validator fails loud, not silent — required by Plan must_haves.truths[1])
- Schema failures surface as `FAIL {name}: {json_path}: {message}` with all errors sorted by JSON path (mirrors `agent/registry_loader.py:246`)
- T-62-01 mitigation: only `yaml.safe_load` used; grep confirms zero `yaml.load(` outside comments
- 14 pytest tests green; 7 acceptance criteria verified

## Task Commits

1. **RED: failing tests** — `6bf1be89e` (test) — 14 tests covering 8 behaviors + 7 AC
2. **GREEN: implement script** — `b6e1ec9d0` (feat) — script + test fixture date-format fix

**Plan metadata:** pending (committed by orchestrator wave completion)

## Files Created/Modified

- `scripts/validate_phase62_yamls.py` — argparse-driven CLI validator (225 lines, executable)
  - `load_schema()` → parses `.planning/research/v10-orchestrator-design/agents-schema.yaml` via `yaml.safe_load`
  - `validate_one(name, schema)` → returns `(ok, message)` with `MISSING`/`FAIL`/`PASS` prefixes
  - `main(argv)` → exit 0 with `OK: {N}/{N}` or exit 1 with `FAILED: {N}/{N}`
- `tests/scripts/test_validate_phase62_yamls.py` — 14 tests (322 lines)
  - subprocess `--help` exits 0 test
  - `load_schema` returns Draft 2020-12 dict test
  - `BATCH_A` / `BATCH_B` constants match plan 6-name lists
  - `validate_one` missing/schema-fail/missing-required/valid cases
  - `main()` no-batch glob + `--batch A` (all valid + all missing) + `--batch B` partial failure
  - source lint: no `yaml.load(`, `Draft202012Validator` referenced, `yaml.safe_load` ≥ 2

## Decisions Made

- **Per-call `get_hermes_home()` resolution** (not module-import-time caching): The original draft had `AGENTS_DIR = get_hermes_home() / "agents"` as a module constant. Tests failed because `import scripts.validate_phase62_yamls` resolves `get_hermes_home()` BEFORE conftest's `_hermetic_environment` fixture sets `HERMES_HOME` to the per-test tmpdir. Fixed by wrapping in `_agents_dir()` function called per-validation. Mirrors the resolve-on-use pattern in `agent/registry_loader.py:305`.
- **Glob at runtime, do NOT hardcode 21**: Plan must_haves.truths[2] requires the script to work against current state (9 YAMLs at Wave 0). Hardcoding 21 would break Wave 0 execution; globbing handles 9/15/21 uniformly.
- **Date string quoting**: PyYAML auto-parses unquoted ISO dates into `datetime.date` objects, which fail the schema's `type: string` constraint. Verified the 9 shipped YAMLs all use single-quote (`'2026-07-07'`) for `transform_date`. Test fixtures follow the same convention with double-quotes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test isolation: module-import-time HERMES_HOME caching**
- **Found during:** Task 1 GREEN phase
- **Issue:** Initial draft cached `AGENTS_DIR = get_hermes_home() / "agents"` at module import, binding to the real `/home/kai/.hermes/agents/` before conftest's tmpdir redirect took effect. 7 tests failed because they wrote fixtures to tmpdir but the validator read from real `~/.hermes/`.
- **Fix:** Replaced module constant with `_agents_dir()` helper called per-validation. Two call sites updated (`validate_one` + `main`).
- **Files modified:** `scripts/validate_phase62_yamls.py`
- **Verification:** All 14 tests pass after fix; `test_main_no_batch_validates_glob_and_reports_ok` confirms glob reads tmpdir, not real home.
- **Committed in:** `b6e1ec9d0` (Task 1 GREEN commit)

**2. [Rule 1 - Bug] Fixed test fixture date format**
- **Found during:** Task 1 GREEN phase
- **Issue:** Test fixture used unquoted `transform_date: 2026-07-08`, which PyYAML parses as `datetime.date(2026, 7, 8)`. Schema declares `type: string` + `format: date` → validator correctly rejected as "not of type 'string'".
- **Fix:** Changed fixture template to quote dates (`transform_date: "2026-07-08"`). Matches shipped-YAML convention (single-quote `'2026-07-07'` in all 9 v11.0 YAMLs).
- **Files modified:** `tests/scripts/test_validate_phase62_yamls.py`
- **Verification:** 3 previously-failing tests (`test_validate_one_valid_yaml_returns_pass`, `test_main_no_batch_validates_glob_and_reports_ok`, `test_main_batch_a_all_valid_exits_0`) now pass.
- **Committed in:** `b6e1ec9d0` (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs — both correctness issues caught by TDD RED→GREEN cycle)
**Impact on plan:** Zero scope creep. Both fixes essential for the script's stated contract (test isolation + schema correctness). No new functionality added beyond Plan spec.

## Issues Encountered

None beyond the two auto-fixed bugs above. The Plan's `<interfaces>` block was accurate:
- `agents-schema.yaml` confirmed at the cited line numbers (additionalProperties:false at line 42, Lineage $def at 354, skill_sha256 pattern at 375)
- `agent/registry_loader.py:246` pattern (`sorted(validator.iter_errors(...), key=lambda e: list(e.absolute_path))`) replicated verbatim
- `get_hermes_home()` import path confirmed at `hermes_constants.py:53`

## Verification (7 Acceptance Criteria)

| AC | Command | Result |
|---|---|---|
| AC1 | `test -x scripts/validate_phase62_yamls.py` | PASS (executable bit set) |
| AC2 | `python3 scripts/validate_phase62_yamls.py --help` | rc=0 |
| AC3 | `python3 scripts/validate_phase62_yamls.py` (no args) | rc=0, stdout contains `OK: 9/9` |
| AC4 | `python3 scripts/validate_phase62_yamls.py --batch A` | rc=1, stdout contains `MISSING animation_studio` |
| AC5 | `grep -c "yaml.safe_load" scripts/validate_phase62_yamls.py` | 5 (≥2 ✓) |
| AC6 | `grep -c "Draft202012Validator" scripts/validate_phase62_yamls.py` | 5 (≥1 ✓) |
| AC7 | `grep -v '^#' scripts/validate_phase62_yamls.py \| grep -c "yaml\.load("` | 0 (✓ — T-62-01 mitigation) |

Plus Plan `<verify>` block: `python3 scripts/validate_phase62_yamls.py --help >/dev/null && python3 scripts/validate_phase62_yamls.py && echo "WAVE0_OK"` → prints `WAVE0_OK`.

## User Setup Required

None — zero external service configuration. PyYAML + jsonschema already in `pyproject.toml` core deps.

## Carry-Down (Interface for Plan 02 / 03 / 04)

Plan 02/03/04 acceptance_criteria should cite the following verbatim:

- **Plan 02 (Wave 1 Batch A — 6 experts)**: `python3 scripts/validate_phase62_yamls.py --batch A` exits 0
- **Plan 03 (Wave 1 Batch B — 6 experts incl. visual_executor)**: `python3 scripts/validate_phase62_yamls.py --batch B` exits 0
- **Plan 04 (Wave 2 — full registry smoke)**: `python3 scripts/validate_phase62_yamls.py` (no flag) exits 0 with `OK: 21/21`

Output format contract (do NOT change in Plan 02/03):
- Success per-file: `PASS {name}`
- Missing file: `MISSING {name}: {path}`
- Schema failure: `FAIL {name}: {json_path}: {first_error_message}`
- Summary success: `OK: {pass_n}/{total}`
- Summary failure: `FAILED: {fail_n}/{total}`

## Threat Mitigations Verified

| Threat ID | Mitigation | Status |
|---|---|---|
| T-62-01 (YAML tag injection) | `yaml.safe_load` exclusively; AC7 grep confirms 0 `yaml.load(` outside comments | ✓ |
| T-62-02 (undeclared field injection) | `Draft202012Validator` enforces `additionalProperties: false` (schema line 42 + Lineage $def line 354) | ✓ |
| T-62-03 (schema path traversal) | `SCHEMA_PATH` hardcoded repo-relative; no user input flows into path construction | accepted |
| T-62-04 (info disclosure via errors) | jsonschema error messages safe to print (field names + constraints, no secrets) | accepted |
| T-62-SC (supply chain) | Zero new package installs — all 3 deps pre-existing in `pyproject.toml` core | ✓ |

## Next Phase Readiness

- Plan 02 (Wave 1 Batch A) can cite `python3 scripts/validate_phase62_yamls.py --batch A` in acceptance criteria
- Plan 03 (Wave 1 Batch B) can cite `python3 scripts/validate_phase62_yamls.py --batch B`
- Plan 04 (Wave 2 registry smoke) can cite the no-flag sweep
- Zero blockers — Wave 0 complete, Wave 1 unblocked

## Self-Check: PASSED

- All 3 created files exist on disk: `scripts/validate_phase62_yamls.py`, `tests/scripts/test_validate_phase62_yamls.py`, `.planning/phases/62-expert-yaml-transform/62-01-SUMMARY.md`
- Both task commits present in git log: `6bf1be89e` (RED), `b6e1ec9d0` (GREEN)
- Executable bit set on `scripts/validate_phase62_yamls.py`
- 14 pytest tests green (0.58s)
- Wave 0 smoke against 9 shipped YAMLs prints `OK: 9/9`

---
*Phase: 62-expert-yaml-transform*
*Plan: 01 (Wave 0)*
*Completed: 2026-07-08*
