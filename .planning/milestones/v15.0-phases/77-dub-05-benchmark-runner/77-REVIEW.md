---
phase: 77-dub-05-benchmark-runner
reviewed: 2026-07-10T14:15:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_run_cosyvoice_benchmark.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_lock_cosyvoice_default.py
findings:
  critical: 0
  warning: 0
  info: 6
  total: 6
status: clean
iteration: 2
previous_iteration:
  critical: 3
  warning: 9
  info: 6
  total: 18
---

# Phase 77: Code Review Report (Re-Review — Iteration 2)

**Reviewed:** 2026-07-10T14:15:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** clean
**Iteration:** 2 (re-review after fixes)

## Summary

Re-review of 2 CLI scripts (`run_cosyvoice_benchmark.py` — 998 lines, `lock_cosyvoice_default.py` — 421 lines) plus 2 test files (24 tests total, all passing) after iteration-1 fixes. All 3 Critical findings (CR-01, CR-02, CR-03) and all 9 Warning findings (WR-01 through WR-09) from the original review are verified as resolved in the source code. No new Critical or Warning issues were introduced by the fixes.

The 6 Info findings from iteration 1 (IN-01 through IN-06) were not in scope for fixing and remain as-is. They are documented below for completeness but do not block shipment.

### Verification Method

Each fix was verified by:
1. Reading the current source code at the exact line ranges cited in the original review.
2. Confirming the fix code matches the suggested fix pattern from the original review.
3. Running the full test suite (24 tests, all pass).
4. Cross-referencing the fix commits (`bc322c6` through `9d598c3`) in git history.
5. Scanning for new issues introduced by the fixes (none found at Critical/Warning level).

## Fix Verification

### CR-01: check_silent/compute_wer exceptions mark successful audio as failed — RESOLVED

**File:** `run_cosyvoice_benchmark.py:744-764`
**Verification:** `check_silent()` (line 749) and `compute_wer()` (line 760) are now in separate try/except blocks OUTSIDE the main try/except that covers ComfyUI/gold-team submission + download (ends at line 742). If either raises, the error is logged as a `logger.warning()` and `error_msg` is NOT set. The VariantResult correctly records `audio_path` without an `error` field. Defense-in-depth: `check_silent` also has its own internal try/except (WR-01 fix), so the outer guard is a secondary safety net.

### CR-02: validate_lock crashes with TypeError on non-string variant (JSON array) — RESOLVED

**File:** `lock_cosyvoice_default.py:199-214`
**Verification:** `isinstance(variant_id, (str, type(None)))` guard at line 203 catches non-string/non-None variants before they reach `VARIANT_ID_MAP.get()`. Non-string variants produce a clean validation error (`"operator_decision.variant must be a string or null"`) and set `variant_id = ""` to prevent downstream crashes. Tests `test_validate_lock_refuses_array_variant` and `test_validate_lock_refuses_dict_variant` both pass.

### CR-03: write_lock performs non-atomic write of VERSION.json — RESOLVED

**File:** `lock_cosyvoice_default.py:304-321`
**Verification:** `write_lock()` now uses `tempfile.NamedTemporaryFile(delete=False, dir=dest_parent)` + `os.replace(tmp_path, version_json_path)` for atomic write. The temp file is created in the same directory as the target (required for `os.replace` atomicity on POSIX). If `json.dump` raises, the temp file is left on disk but VERSION.json remains intact. `os.replace` is atomic on both POSIX and Windows.

### WR-01: check_silent does not catch FileNotFoundError or TimeoutExpired — RESOLVED

**File:** `run_cosyvoice_benchmark.py:401-410`
**Verification:** `subprocess.run(["ffmpeg", ...])` is wrapped in `try/except (FileNotFoundError, subprocess.TimeoutExpired)`. Returns `False` (assume non-silent) on failure. Tests `test_check_silent_ffmpeg_missing` and `test_check_silent_ffmpeg_timeout` both pass.

### WR-02: poll_comfyui and _poll_gold_team silently swallow all RequestException — RESOLVED

**File:** `run_cosyvoice_benchmark.py:349-350, 550-551`
**Verification:** Both `except requests.RequestException` blocks now call `logger.debug(...)` instead of bare `pass`. Operators have visibility into network failures during polling.

### WR-03: _VARIANT_TO_VERSION_JSON is dead code — RESOLVED

**File:** `run_cosyvoice_benchmark.py`
**Verification:** The `_VARIANT_TO_VERSION_JSON` dict has been removed from the module. No references remain.

### WR-04: load_benchmark_report and load_version_json do not validate nested dict types — RESOLVED

**File:** `lock_cosyvoice_default.py:118-122, 162-166`
**Verification:** `load_benchmark_report()` checks `isinstance(data.get("operator_decision"), dict)` at line 118. `load_version_json()` checks `isinstance(data.get("tts"), dict)` at line 162. Both raise `ValueError` with a descriptive message on type mismatch.

### WR-05: Gold-team task_id not unique across re-runs — RESOLVED

**File:** `run_cosyvoice_benchmark.py:110, 521`
**Verification:** `_RUN_ID = uuid.uuid4().hex[:8]` at module level (line 110). `task_id = f"bench_{_RUN_ID}_{line_id}"` at line 521. Task IDs are now unique per process invocation.

### WR-06: WER formula can exceed 1.0 — RESOLVED

**File:** `run_cosyvoice_benchmark.py:503-508`
**Verification:** `return min(distance / len(reference_text), 1.0)` clamps the value to [0.0, 1.0]. Docstring at lines 445-451 updated to clarify this is technically CER (Character Error Rate) and explain the clamping rationale. No division-by-zero risk: `reference_text` emptiness is checked at line 500.

### WR-07: lock_date uses local date, runner timestamp uses UTC — RESOLVED

**File:** `lock_cosyvoice_default.py:299-301, 400`
**Verification:** `write_lock()` uses `datetime.datetime.now(datetime.timezone.utc).date().isoformat()` at line 300. `main()` uses the same UTC expression at line 400. Both are consistent with the runner's UTC timestamp.

### WR-08: metadata.dialogue_lines_file records copied path, not original input path — RESOLVED

**File:** `run_cosyvoice_benchmark.py:597, 784-791, 972`
**Verification:** `run_benchmark()` accepts `dialogue_lines_source` parameter (line 597). `main()` passes `str(dialogue_lines_path)` (line 972). Metadata records the original input path with a fallback to the copied path for backward compatibility (lines 787-791). Test assertion at `test_run_benchmark_mocked_comfyui` lines 193-198 verifies `dialogue_lines_file == str(lines_path)`.

### WR-09: Gold-team pre-check is redundant — RESOLVED

**File:** `run_cosyvoice_benchmark.py:630-646, 711-717`
**Verification:** Pre-check populates `gold_team_unreachable: set[str]` (line 634). Main loop checks `if variant_id in gold_team_unreachable` (line 713) and raises `RuntimeError` if the pre-check failed. No per-line `_check_gold_team_reachable()` call in the main loop. Reduces reachability checks from N+1 to 1 per gold-team variant.

## Test Coverage Verification

All 24 tests pass (verified by running `python3 -m pytest` against both test files):

- `test_run_cosyvoice_benchmark.py`: 11 tests (including 2 new tests for WR-01: `test_check_silent_ffmpeg_missing`, `test_check_silent_ffmpeg_timeout`)
- `test_lock_cosyvoice_default.py`: 13 tests (including 2 new tests for CR-02: `test_validate_lock_refuses_array_variant`, `test_validate_lock_refuses_dict_variant`)
- The WR-08 fix is covered by an assertion in `test_run_benchmark_mocked_comfyui` (lines 193-198).

## Info (Carried Forward — Not in Fix Scope)

These 6 Info findings from iteration 1 were not in scope for fixing (only Critical+Warning were fixed). They are carried forward for awareness but do not block shipment.

### IN-01: Redundant `import shutil as shutil_mod` inside main()

**File:** `run_cosyvoice_benchmark.py:949`
**Issue:** `shutil` is already imported at module level (line 49). The local `import shutil as shutil_mod` is redundant.
**Fix:** Replace `shutil_mod.copy2(...)` with `shutil.copy2(...)` and remove the local import.

### IN-02: /dev/null hardcoded in ffmpeg command (POSIX-only)

**File:** `run_cosyvoice_benchmark.py:403`
**Issue:** Hardcodes `/dev/null` which is POSIX-only. Acceptable since ComfyUI runs on Linux in practice.

### IN-03: prompt_id and filename not URL-encoded in ComfyUI HTTP paths

**File:** `run_cosyvoice_benchmark.py:342, 372`
**Issue:** `prompt_id`, `filename`, `subfolder`, `file_type` are not URL-encoded. Primarily a correctness issue (wrong file fetched), not security.

### IN-04: _download_gold_team_audio file:// path not validated

**File:** `run_cosyvoice_benchmark.py:566-568`
**Issue:** `file://` paths from the gold-team API are copied without path validation. Defense-in-depth only (gold-team API is trusted localhost).

### IN-05: Test coverage gaps

**File:** both test files
**Issue:** Gold-team backend, error paths, and main() entry points remain untested. Gold-team backend tests are most critical.

### IN-06: emit_rich_summary avg_wer can display >100% (no clamping)

**File:** `run_cosyvoice_benchmark.py:864`
**Issue:** Now mitigated by WR-06 clamping at the `compute_wer` level — `wer` values in VariantResult are guaranteed to be <= 1.0, so `avg_wer` cannot exceed 100%. This Info finding is effectively resolved as a side effect of WR-06, though no explicit display-level clamp was added.

---

_Reviewed: 2026-07-10T14:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 2 (re-review after fixes)_
