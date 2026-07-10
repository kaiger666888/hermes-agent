---
phase: 77-dub-05-benchmark-runner
plan: 02
subsystem: audio_pipeline
tags: [dub-05, cosyvoice, lock, version-json, operator-action-closure]
requires:
  - 77-01 benchmark runner (BenchmarkReport JSON schema)
  - VERSION.json tts block (alternative_tested[] + 3 lock fields)
provides:
  - VERSION.json lock script with 3-check validation + overwrite guard
  - 11 unit tests covering all validation guards + write scope
  - cosyvoice-benchmark.md Runner Usage section (4-step operator workflow)
affects:
  - VERSION.json tts.cosyvoice_default_variant (locked by operator via this script)
  - VERSION.json tts.lock_date (written by this script)
  - VERSION.json tts.lock_rationale (written by this script)
tech-stack:
  added:
    - Stdlib-only sync lock script (argparse + json + datetime, no Pydantic needed)
    - VARIANT_ID_MAP CLI-to-VERSION.json ID mapping (underscores -> dots)
  patterns:
    - 3-check validation pipeline (non-null + in alternative_tested + actually benchmarked)
    - Overwrite guard pattern (refuse without --force)
    - Write-scope-limited file mutation (only 3 fields, preserves alternative_tested + benchmark_report_path)
key-files:
  created:
    - skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py
    - skills/movie-experts/audio_pipeline/tests/test_lock_cosyvoice_default.py
  modified:
    - skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md
decisions:
  - Lock script reads raw JSON dicts (not Pydantic models) — simpler, no Pydantic dependency for lock path
  - VARIANT_ID_MAP duplicated from runner's _VARIANT_TO_VERSION_JSON (single-responsibility: lock script is standalone)
  - Rationale guard added as 4th validation check (T-77-09 repudiation mitigation)
  - Report JSON Schema documented in cosyvoice-benchmark.md for operator reference
metrics:
  duration: 195s
  tasks: 3
  files: 3
  commits: 3
  completed: 2026-07-10
---

# Phase 77 Plan 02: CosyVoice Default Variant Lock Script Summary

VERSION.json lock script that reads the operator's decision from the benchmark report JSON, validates it against 3 safety checks + lock_ready guard + overwrite guard, and writes the lock block to VERSION.json — closing the DUB-05 operator-action handoff with a 5-minute CLI workflow (benchmark -> review -> fill decision -> lock).

## What Was Built

### Task 1: Lock Script (`lock_cosyvoice_default.py`)

**380-line sync-only Python script** implementing the DUB-05-LOCK contract:

- **VARIANT_ID_MAP** — maps runner CLI underscore IDs to VERSION.json dotted IDs:
  - `cosyvoice_2_0_0_5b` -> `cosyvoice_2.0_0.5B`
  - `fun_cosyvoice_3_0` -> `fun_cosyvoice_3.0_0.5B_2512`
  - `cosyvoice_300M_gold_team` -> `cosyvoice_300M_gold_team` (unchanged)

- **Core functions**:
  - `load_benchmark_report(path)` — reads JSON report, raises FileNotFoundError/ValueError with context
  - `load_version_json(path)` — reads VERSION.json, validates `tts` key exists
  - `validate_lock(report, version_json)` — 3-check + 2-guard validation, returns `(variant_id, rationale, errors)`
  - `check_overwrite_guard(version_json, force)` — returns error string if already locked without --force
  - `write_lock(version_json_path, variant_id, rationale)` — writes only 3 fields (T-77-06 mitigation)
  - `main()` — argparse CLI with --benchmark-report, --version-json, --force

- **Validation checks** (per CONTEXT.md D-09):
  - Check 0: lock_ready guard — refuses if `operator_decision.lock_ready` is false
  - Check 1: non-null variant — refuses if `operator_decision.variant` is null/empty
  - Check 2: in alternative_tested — refuses if mapped variant ID not in `alternative_tested[]`
  - Check 3: actually benchmarked — refuses if variant not in any `lines[].variants[]`
  - Rationale guard — refuses if `operator_decision.rationale` is null/empty (T-77-09)

- **Overwrite guard** (T-77-07): refuses if `cosyvoice_default_variant` already non-null without `--force`

- **Write scope** (T-77-06): only modifies `cosyvoice_default_variant` + `lock_date` + `lock_rationale`; does NOT touch `alternative_tested[]` or `benchmark_report_path`

- **No --variant flag** (per D-09): variant comes from `operator_decision.variant` in the report
- **No auto-pick-lower-WER** (per DUB-05-AUTO-LOCK deferral): operator decision required

### Task 2: Unit Tests (`test_lock_cosyvoice_default.py`)

**11 tests in `TestLockCosyVoiceDefault` class**, all passing (0.03s):

1. `test_validate_lock_refuses_null_variant` — 3+ errors for all-null operator_decision
2. `test_validate_lock_refuses_variant_not_in_alternative_tested` — error mentions "alternative_tested"
3. `test_validate_lock_refuses_variant_not_benchmarked` — error mentions "does not appear" / "actually benchmarked"
4. `test_validate_lock_refuses_lock_ready_false` — error mentions "lock_ready"
5. `test_validate_lock_passes_valid_decision` — 0 errors for valid report (happy path)
6. `test_check_overwrite_guard_refuses_without_force` — error string when already locked, force=False
7. `test_check_overwrite_guard_allows_with_force` — None when force=True
8. `test_check_overwrite_guard_allows_when_null` — None when cosyvoice_default_variant is null
9. `test_write_lock_writes_three_fields_only` — verifies alternative_tested + benchmark_report_path unchanged
10. `test_variant_id_map_covers_all_variants` — all 3 CLI -> VERSION.json ID mappings verified
11. `test_load_benchmark_report_missing_file` — FileNotFoundError for missing report

### Task 3: cosyvoice-benchmark.md Runner Usage Section

**109-line additive insert** extending the existing benchmark protocol template:

- `### Step 1: Prepare dialogue-lines JSON` — JSON format + 2-line example
- `### Step 2: Run the benchmark` — runner CLI + 5-flag table
- `### Step 3: Review audio + fill operator_decision` — variant + rationale + lock_ready instructions
- `### Step 4: Lock the chosen variant` — lock CLI + 3 validation checks + 2 guards + 3-flag table
- `### Report JSON Schema` — top-level `{metadata, lines[], operator_decision}` structure

Section positioned after `## Default Lock Decision` and before `## Open Questions (v15+)`. No existing content modified or deleted.

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Message | Files |
|------|---------|-------|
| `478c8f3` | feat(77-02): add VERSION.json lock script for CosyVoice default variant | `scripts/lock_cosyvoice_default.py` |
| `14d006e` | test(77-02): add unit tests for lock script validation guards | `tests/test_lock_cosyvoice_default.py` |
| `517a427` | docs(77-02): extend cosyvoice-benchmark.md with Runner Usage section | `references/voicer/cosyvoice-benchmark.md` |

## Verification Results

- `--help` output shows `--benchmark-report`, `--version-json`, `--force` flags (no `--variant` flag)
- `validate_lock` returns 3+ errors for all-null operator_decision (lock_ready + variant + rationale)
- `validate_lock` returns 0 errors for valid report with lock_ready=true
- `check_overwrite_guard` returns error string when already locked without --force
- `write_lock` modifies only 3 fields — alternative_tested[] and benchmark_report_path unchanged
- All 11 unit tests pass (0.03s, zero warnings)
- cosyvoice-benchmark.md has exactly one `## Runner Usage` section with 4 step subsections
- No `async`/`await` keywords (INFRA-04 compliant)
- All `open()` calls have `encoding="utf-8"` (Ruff PLW1514 compliant)
- Script does NOT have a `--variant` flag (per D-09)
- Script does NOT auto-pick-lower-WER (per DUB-05-AUTO-LOCK deferral)
- Pre-existing dirty state in kais-hermes-skills repo untouched (only 3 plan files committed)

## Self-Check: PASSED

All created files exist. All 3 commits verified in git log.
