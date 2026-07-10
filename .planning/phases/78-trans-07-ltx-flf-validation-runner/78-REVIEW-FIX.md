---
phase: 78-trans-07-ltx-flf-validation-runner
fixed_at: 2026-07-10T05:00:00Z
review_path: .planning/phases/78-trans-07-ltx-flf-validation-runner/78-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 78: Code Review Fix Report

**Fixed at:** 2026-07-10T05:00:00Z
**Source review:** `.planning/phases/78-trans-07-ltx-flf-validation-runner/78-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (2 Critical + 8 Warning)
- Fixed: 10
- Skipped: 0
- Tests: 34/34 passed (30 original + 4 new)

**Cross-repo note:** All source fixes were committed to the `kais-hermes-skills` repo (at `/data/workspace/kais-hermes-skills`), not `hermes-agent`. This is by design — the Phase 78 deliverables live in the kais-hermes-skills repo.

## Fixed Issues

### CR-01: `ref_image_path` parameter is dead code — identity continuity check does not use the reference image

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`, `skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py`
**Commit:** `fd416e2`
**Applied fix:** Removed the dead `ref_image_path` parameter from `verify_identity_continuity` and updated the docstring to be honest about the check being text-prompt-based (not image-to-image comparison). The `verify_image_content` API only accepts `image_path` + `expected_content` text — it cannot compare two images. Updated the caller in `run_validation` to not pass `ref_image_path`, and updated both tests (`test_verify_identity_continuity_success` and `test_verify_identity_continuity_failure`) to use the new 2-arg signature.

### CR-02: `poll_comfyui` ignores ComfyUI execution errors — 600s wasted on failed generations

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`
**Commit:** `2685d1d`
**Applied fix:** `poll_comfyui` now inspects the `status.status_str` field in the `/history` response. If `status_str == "error"`, it returns a sentinel dict `{"_execution_error": True, "messages": [...]}` immediately instead of retrying for 600s. The caller in `run_validation` checks for the `_execution_error` sentinel and sets `gen_status="failed"` with the error message. This avoids 10-minute wasted polls on doomed generations (OOM, node errors, model loading failures).
**Status:** fixed: requires human verification (logic change — new error handling condition)

### WR-01: `download_video` does not URL-encode filename/subfolder parameters

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`
**Commit:** `1d61f48`
**Applied fix:** Replaced raw string interpolation with `httpx` `params=` dict for the `/view` endpoint query parameters. `httpx` automatically URL-encodes the values, handling spaces and special characters in shot IDs (e.g., `shot 01_validation.mp4`) that would produce malformed URLs.

### WR-02: `validate_verdict` does not type-check `rationale` — non-string types pass through

**Files modified:** `skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py`, `skills/kais-movie-pipeline/tests/test_update_ltx_flf_verdict.py`
**Commit:** `050ac6b`
**Applied fix:** Added `isinstance(rationale, (str, type(None)))` check mirroring the `verdict` field's guard. Non-string types (JSON arrays, numbers, booleans) now produce an error message instead of passing through to markdown interpolation. Added `test_validate_verdict_refuses_non_string_rationale` test to cover this case.

### WR-03: `build_validation_workflow` produces empty image names when `num_refs < 4`

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`
**Commit:** `ce37be8`
**Applied fix:** Added warning logs at the top of `build_validation_workflow` that fire when `num_refs < 4` (placeholder REF nodes would get empty image names, which ComfyUI rejects) or `num_refs > 4` (extra refs not wired into the template). The template hardcodes 4 REF nodes + 1 BACKGROUND node.

### WR-04: `latency_ms` discarded for failed/timeout shots — diagnostic value lost

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`
**Commit:** `b6b040b`
**Applied fix:** Changed `latency_ms=latency_ms if actual_video_path is not None else None` to `latency_ms=latency_ms`. Now latency is always recorded, even for failed/timeout shots. This lets operators see how long a timeout took (e.g., 600000ms vs 5000ms) to distinguish "ComfyUI was slow" from "hung immediately". The `ShotResult.latency_ms` field is `int | None`, so a non-None value is type-safe.

### WR-05: `verify_identity_continuity` docstring says `passed` but return dict uses `pass`

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`
**Commit:** `fd416e2` (fixed as part of CR-01)
**Applied fix:** The docstring was rewritten as part of the CR-01 fix. The new docstring correctly documents the return keys as `pass`, `confidence`, `description`, `cached` (matching the actual `verify_image_content` return dict). No separate commit was needed — the CR-01 docstring rewrite resolved this finding.

### WR-06: No test for `poll_comfyui` timeout (returns `None`) or execution error paths

**Files modified:** `skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py`
**Commit:** `eb161e6`
**Applied fix:** Added `test_poll_comfyui_timeout_returns_none` — mocks `time.time` to advance past `max_wait` and `asyncio.sleep` to be a no-op, verifying `poll_comfyui` returns `None` (timeout sentinel) without waiting 600s. Also added `test_poll_comfyui_execution_error` for the CR-02 `status_str=error` sentinel path. Added `poll_comfyui` to the test imports.

### WR-07: No test for `download_video` HTTP error (`raise_for_status` raises)

**Files modified:** `skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py`
**Commit:** `eb161e6` (committed together with WR-06)
**Applied fix:** Added `test_run_validation_download_http_error` — mocks ComfyUI to return a successful generation but a 404 on the `/view` download endpoint, causing `raise_for_status` to raise `HTTPStatusError`. Verifies `run_validation` records `gen_status="failed"` with the error message and `video_path=None`.

### WR-08: `emit_rich_summary` shows "0%" for `passed=True, confidence=None` (misleading)

**Files modified:** `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py`
**Commit:** `688d276`
**Applied fix:** Added an explicit `elif frame.passed:` branch in the confidence display logic. Now `passed=True, confidence=None` shows "pass" instead of the misleading "0%". The display hierarchy is: confidence (if available) > "-" (if passed is None) > "pass" (if passed=True) > "0%" (if passed=False).

---

_Fixed: 2026-07-10T05:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
