---
phase: 78-trans-07-ltx-flf-validation-runner
reviewed: 2026-07-10T14:30:00Z
depth: quick
iteration: 3
files_reviewed: 2
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py
findings:
  critical: 0
  warning: 0
  info: 5
  total: 5
status: clean
---

# Phase 78: Code Review Report (Final Re-Review, Iteration 3/3)

**Reviewed:** 2026-07-10T14:30:00Z
**Depth:** quick
**Iteration:** 3 (final — max iterations)
**Files Reviewed:** 2
**Status:** clean

## Summary

Final re-review (iteration 3 of 3, max) verifying that WR-09 from iteration 2 is resolved and that no new Critical/Warning issues were introduced by the fix.

**Verification result:** WR-09 is confirmed RESOLVED. The fix correctly introduced a `total_template_refs = expected_refs + 1` variable (= 5, accounting for the PLACEHOLDER_BACKGROUND node) and changed the upper-bound condition from `num_refs > expected_refs` (> 4) to `num_refs > total_template_refs` (> 5). With the CLI default `num_refs=5`, neither warning branch fires — the spurious "ref5 not wired" warning no longer appears on default invocations.

**No new Critical or Warning issues** were introduced by the WR-09 fix. Quick-pattern scans (hardcoded secrets, dangerous functions, debug artifacts, empty catch blocks) all returned clean. Boundary-value trace for num_refs = 3, 4, 5, 6 confirms the warning logic is correct at all boundaries.

The 5 Info findings from iteration 1/2 are carried forward unchanged (not in fix scope).

## WR-09 Resolution Verification

### WR-09: WR-03 fix produces spurious warning on default `num_refs=5` configuration — RESOLVED

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:265-284`

**Verification:** The fix introduced a new variable `total_template_refs = expected_refs + 1` (line 266, = 5) that accounts for the PLACEHOLDER_BACKGROUND node (which uses the last ref image per the LiconMSR convention at line 209: `background = refs[-1]`). The upper-bound warning condition was changed from `num_refs > expected_refs` (> 4) to `num_refs > total_template_refs` (> 5) at line 276.

Boundary-value trace confirms correctness:

| num_refs | `< 4` branch | `> 5` branch | Warning fires? | Correct? |
|----------|-------------|-------------|----------------|----------|
| 3        | True        | —           | "REF nodes ref4-4 will get empty image names" | Yes — REF4 placeholder gets empty string (line 297 guard) |
| 4        | False       | False       | None           | Yes — 4 REF nodes filled; BACKGROUND = ref4 (shared with REF4, pre-existing behavior) |
| 5 (default) | False    | False       | None           | Yes — **WR-09 resolved: no spurious warning on default** |
| 6        | —           | True        | "ref6-6 will not be wired" | Yes — ref6 loaded but no placeholder exists |

The warning message format strings are also correct:
- `< 4` case (line 274): `num_refs + 1` to `expected_refs` (e.g., num_refs=3 → "ref4-4")
- `> 5` case (line 283): `total_template_refs + 1` to `num_refs` (e.g., num_refs=6 → "ref6-6")

The comment block at lines 258-264 was also updated to document the 5-ref capacity (4 REF + 1 BACKGROUND) and the no-warning behavior at num_refs=5.

**Status:** RESOLVED

## Quick-Pattern Scan Results

All quick-pattern scans returned clean (no matches):

- **Hardcoded secrets:** None found
- **Dangerous functions** (`eval`, `exec`, `system`, `innerHTML`, etc.): None found
- **Debug artifacts** (`console.log`, `debugger`, `TODO`, `FIXME`, `HACK`): None found
- **Empty catch blocks:** None found

## Info (carried forward from iterations 1-2)

The following 5 Info findings were identified in iteration 1 and carried forward in iteration 2. They are not in the fix scope for this phase and remain unchanged. They do not affect the clean status of this review.

### IN-01: `metadata.reference_shots_dir` is empty in test — `shots_dir` not injected into shot dicts

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py:289-298`
**Issue:** The `test_run_validation_mocked_comfyui` test does not inject `shots_dir` into shot dicts (unlike `main_async` at line 979). The metadata reads `shots[0].get("shots_dir", "")` which returns `""` in the test.
**Fix:** Either inject `shots_dir` in the test, or add a metadata verification assertion.
**Status:** Carried forward (not in fix scope)

### IN-02: `_no_vision_verify` stub uses `"pass"` key while `FrameIdentityResult` field is `passed`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:1002-1008`
**Issue:** The no-op stub returns `{"pass": None, ...}`. The caller at line 789 does `result.get("pass")` which correctly maps to `FrameIdentityResult.passed`. Key naming inconsistency is a cognitive tax but functionally correct.
**Fix:** No code change needed. Consider adding a comment at the stub noting the `pass` key convention.
**Status:** Carried forward (not in fix scope)

### IN-03: `poll_comfyui` actual wait can exceed `max_wait` by up to 15 seconds

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:401-430`
**Issue:** Loop condition checks `time.time() - start < max_wait` at iteration top, but each iteration can take up to 10s (HTTP timeout) + 5s (sleep) = 15s. Actual wait can be `max_wait + 15`. Minor overshoot.
**Fix:** No fix needed for this use case. If precision matters, check time inside the loop after each HTTP call.
**Status:** Carried forward (not in fix scope)

### IN-04: Verdict doc section heading has no anchor for programmatic detection

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py:381-386`
**Issue:** `write_verdict` uses a regex to find the `## Production-Readiness Verdict` heading. If someone renames the heading, the regex fails and `write_verdict` raises `ValueError`. No test for the heading-not-found case.
**Fix:** Consider a more resilient section marker (e.g., HTML comment) or add a test for the error path.
**Status:** Carried forward (not in fix scope)

### IN-05: Workflow JSON `_meta.flf_model_default` is not used by `build_validation_workflow`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:253-254`
**Issue:** The workflow JSON has a `_meta.flf_model_default` field, but `build_validation_workflow` never reads it. The `flf_model` parameter comes from the CLI argument. The `_meta` field is informational only.
**Fix:** No code change needed. Consider adding a comment noting `_meta` fields are informational.
**Status:** Carried forward (not in fix scope)

---

_Reviewed: 2026-07-10T14:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
_Iteration: 3 (final — max iterations)_
