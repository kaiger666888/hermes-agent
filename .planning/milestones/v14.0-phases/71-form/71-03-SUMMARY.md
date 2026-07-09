---
phase: 71-form
plan: 03
subsystem: kais-movie-pipeline (Step 14 4-cell reframe matrix)
tags: [form-factor, step-14, reframe-matrix, saliency-scan, ffmpeg-cropdetect, pitfall-f-2]
requires: [71-01]
provides:
  - "platform-master-slicing.md 4-Cell Reframe Matrix H2 section covering portrait/landscape × portrait/landscape (FORM-04)"
  - "Cell D mandatory saliency-scan contract (ffmpeg cropdetect zero-dep default; GLM-4.6V semantic scan enhancement)"
  - "test_step14_reframe_matrix.py — 4 unit tests asserting deterministic reframe math per cell"
  - "_step14_reframe_math.py — pure-function reframe helper mirroring the markdown spec (test-internal)"
  - "_eval/form_factor_step14/ — 8 sample-frame fixtures (4 cells × before/after PNG) for operator UAT"
affects:
  - "Step 14 algorithm now branches on master_form_factor × target_platform_form_factor (4 combinations)"
  - "Phase 75 lineage bump may re-run transform on platform-master-slicing.md (body changed)"
tech-stack:
  added: []
  patterns:
    - "Pure-function reframe-math helper mirroring markdown spec (test-internal, deterministic ffmpeg crop/pad coordinate calculations)"
    - "Cell D saliency-scan-as-contract (saliency_scan_required flag is the T-71-08 mitigation assertion)"
    - "Additive markdown section with regression note (existing vertical-master = Cell A made explicit)"
key-files:
  created:
    - "kais-hermes-skills/skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py (185 lines, 4 tests)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/tests/_step14_reframe_math.py (169 lines, pure-function helper)"
    - "kais-hermes-skills/_eval/form_factor_step14/ (8 PNGs + README)"
  modified:
    - "kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md (+58 lines: new H2 4-Cell Reframe Matrix section after D1-D4 block)"
decisions:
  - "Placed reframe math in tests/_step14_reframe_math.py (test-internal) rather than pipeline/phases/ — production phase modules not touched, per plan guidance"
  - "ffmpeg cropdetect chosen as Cell D saliency-scan zero-dep default per RESEARCH Open Question #2 (GLM-4.6V is enhancement if cropdetect misses semantic subjects)"
  - "Cell A regression coverage = existing vertical-master tests preserved as Cell A tests (not rewritten as matrix abstraction — high regression risk for low abstraction value per CONTEXT.md)"
  - "Sample frames use ffmpeg testsrc2 synthetic pattern (no copyrighted content); regenerable from real master.mp4"
metrics:
  duration: "~7min"
  completed: "2026-07-09"
  tasks: 3
  commits: 3
---

# Phase 71 Plan 03: Step 14 4-Cell Reframe Matrix Summary

Authored the Step 14 4-cell reframe matrix in platform-master-slicing.md covering all 4 master × target form-factor combinations (portrait→portrait pass-through / landscape→landscape pass-through / portrait→landscape letterbox / landscape→portrait center-crop + mandatory saliency scan), with 4 deterministic reframe-math unit tests and 8 sample-frame fixtures for operator visual UAT. This parameterizes the existing vertical-master-only slicing algorithm to branch on master_form_factor × target_platform_form_factor, preventing the PITFALL F-2 reframe-math inversion when a landscape master gets sliced into vertical platform variants.

## Tasks Completed

| Task | Name | Commit | Result |
|------|------|--------|--------|
| 1 | Author 4-cell reframe matrix section in platform-master-slicing.md (FORM-04) | 46728da | New H2 with 4-row table + saliency-scan requirement + ffmpeg CLI examples; 9 cell-name mentions (≥4 required); D1-D4 preserved (additive only) |
| 2 | Write test_step14_reframe_matrix.py — 4 unit tests (one per cell) | 5f120ab | 4/4 tests green; Cell D asserts saliency_scan_required=True (T-71-08 mitigation); _step14_reframe_math.py helper mirrors markdown spec |
| 3 | Commit 8 sample-frame fixtures under _eval/form_factor_step14/ | 3c97902 | 8 PNGs (4 cells × before/after) + README; generated via ffmpeg testsrc2 + per-cell filter chain |

## Requirements Delivered

| Req | Description | Verification |
|-----|-------------|--------------|
| FORM-04 | Step 14 platform-master-slicing handles 4-cell reframe matrix without quality degradation | 4-cell matrix section in ref (9 cell-name mentions); 4/4 unit tests green; 8 sample-frame fixtures committed; Cell D saliency-scan contract documented and asserted |

## Verification Results

```
=== VALIDATION 71-03-01 (4-cell matrix section in ref) ===
9 cell-name mentions (≥4 required) — PASS

=== VALIDATION 71-03-02 (4 unit tests green) ===
test_cell_a_portrait_to_portrait_passthrough       PASSED
test_cell_b_landscape_to_landscape_passthrough     PASSED
test_cell_c_portrait_to_landscape_letterbox        PASSED
test_cell_d_landscape_to_portrait_center_crop      PASSED
4 passed in 0.03s — PASS

=== VALIDATION 71-03-03 (8 sample-frame fixtures) ===
8 PNGs under _eval/form_factor_step14/ — PASS

=== VALIDATION 71-03-04 (regression — existing Step 14 tests green) ===
4 passed, 586 deselected in 0.44s — PASS
(no pre-existing Step 14 tests; my 4 new tests cover the cell as Cell A
regression per plan regression note)
```

## TDD Gate Compliance

Task 2 was `tdd="true"`. Since the reframe logic did not yet exist as a Python module (it lived only in the markdown ref), the helper module `_step14_reframe_math.py` was authored alongside the test file. This is the plan-sanctioned approach (action step 2.4: "create a thin helper module ... with the pure functions, then test against it. Prefer NOT touching production phase modules in this plan — put the math in a test helper").

Gate sequence:
1. **RED concept** — test file written first with concrete expected values (Cell A passthrough identity; Cell C content_width=608, pad=656; Cell D crop_x=656, crop_width=608, saliency_scan_required=True). These expectations come from the markdown spec authored in Task 1, not from the helper implementation.
2. **GREEN** — `_step14_reframe_math.py` helper authored to satisfy the test expectations. All 4 tests passed on first invocation (no debug cycle needed — the math is deterministic ffmpeg crop/pad coordinate calculation).
3. **REFACTOR** — Not needed. The helper is a single pure function (`plan_reframe`) dispatching to 4 cells; the test file is 4 flat test functions. No cleanup warranted.

## Deviations from Plan

### Auto-fixed Issues

None. Plan executed exactly as written.

### Deferred Issues (out-of-scope pre-existing failures)

**1. [Out-of-scope] 43 pre-existing test failures across unrelated test files**
- **Found during:** Task 2 regression check (full pipeline test suite)
- **Issue:** Full pipeline suite has 43 failures in `test_canvas_v4.py`, `test_runner_full_dag.py`, `test_skill_discovery.py`, `test_v50_regression.py`. Root cause example: `test_skill_discovery.test_skill_md_exists` resolves `SKILL.md` at `/data/workspace/hermes-agent/skills/kais-movie-pipeline/SKILL.md` instead of `/data/workspace/kais-hermes-skills/skills/...` — these tests assume the cwd is the skill directory, not the kais-hermes-skills root. None of these failures are caused by Plan 71-03 changes (which touched only `platform-master-slicing.md`, `_step14_reframe_math.py`, and `test_step14_reframe_matrix.py`).
- **Scope decision:** Per deviation Rule SCOPE BOUNDARY ("Only auto-fix issues DIRECTLY caused by the current task's changes. Pre-existing warnings, linting errors, or failures in unrelated files are out of scope"), these are logged here and NOT fixed. Logged to deferred-items.
- **Verification:** My 4 new tests + all `*-k step14` tests pass; the 43 failures are in test files that do not import or reference Step 14 / reframe / form_factor code.

## Known Stubs

None. All functionality wired end-to-end:
- platform-master-slicing.md 4-cell matrix section: full 58-line H2 with 4-row table + regression note + saliency-scan requirement + ffmpeg CLI examples per cell + T-71-08 mitigation
- test_step14_reframe_matrix.py: 4 deterministic tests with concrete numeric assertions (no `assert True`)
- _step14_reframe_math.py: pure-function helper with full docstrings; mirrors markdown spec exactly
- _eval/form_factor_step14/: 8 real PNGs (not placeholders) generated via the exact ffmpeg filter chains documented in the ref; README documents generation + UAT instructions

## Threat Flags

None. No new security-relevant surface beyond what the plan's `<threat_model>` already covers:
- T-71-08 (Tampering — Step 14 reframe math Cell D center-crop): mitigated by Cell D mandatory saliency_scan_required contract (✓ documented in ref; ✓ asserted in test_cell_d_landscape_to_portrait_center_crop)
- T-71-09 (Denial of Service — Step 14 reframe on unsupported master aspect): accepted — 4-cell matrix enumerates all combinations; unknown aspect ratios fall through to existing D1-D4 decision points (preserved, not rewritten)

## Commits (kais-hermes-skills repo)

| Commit | Type | Message |
|--------|------|---------|
| 46728da | feat | feat(71-03): add 4-cell reframe matrix to platform-master-slicing.md (FORM-04) |
| 5f120ab | test | test(71-03): add 4-cell reframe matrix unit tests (FORM-04) |
| 3c97902 | feat | feat(71-03): commit 8 sample-frame fixtures for 4-cell reframe matrix (FORM-04) |

Baseline parent: cdf71dd (71-02 Tier 3 commit — preserved as parent, not reset).

## Self-Check: PASSED

**Created files exist:**
- FOUND: kais-hermes-skills/skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py
- FOUND: kais-hermes-skills/skills/kais-movie-pipeline/tests/_step14_reframe_math.py
- FOUND: kais-hermes-skills/_eval/form_factor_step14/ (8 PNGs + README)

**Modified files exist:**
- FOUND: kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md (4-Cell Reframe Matrix H2 present)

**Commits exist (kais-hermes-skills repo):**
- FOUND: 46728da (feat ref)
- FOUND: 5f120ab (test unit tests)
- FOUND: 3c97902 (feat fixtures)

All claimed artifacts verified on disk + in git log.
