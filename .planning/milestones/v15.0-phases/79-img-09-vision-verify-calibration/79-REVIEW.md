---
phase: 79-img-09-vision-verify-calibration
reviewed: 2026-07-10T15:45:00Z
depth: quick
files_reviewed: 3
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/calibrate_vision_verify.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/apply_vision_verify_thresholds.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
iteration: 2
previous_findings_resolved:
  critical: 2
  warning: 5
  total: 7
---

# Phase 79: Code Review Report (Re-Review — Iteration 2)

**Reviewed:** 2026-07-10T15:45:00Z
**Depth:** quick
**Files Reviewed:** 3
**Status:** clean

## Summary

Re-review after fixes for Phase 79 (IMG-09 Vision-Verify Calibration). The original review (iteration 1, 2026-07-10T14:30:00Z) found 2 Critical + 5 Warning + 3 Info issues across 6 files. All 7 Critical+Warning findings have been resolved. No new Critical or Warning issues were introduced by the fixes.

The 3 Info findings from iteration 1 (IN-01 regex float parse, IN-02 get_hermes_home fallback, IN-03 bool ref_count type confusion) were in files outside this re-review's scope (`dreamina_manager.py`, pre-existing regex in `vision_verify.py`) and were not required to be fixed. They remain tracked in the iteration-1 report for future cleanup.

## Finding Resolution Verification

### CR-01: write_config() crashes on malformed config.yaml — RESOLVED

**File:** `apply_vision_verify_thresholds.py:335-347`
**Verification:** Added `isinstance(existing_vv, dict)` guard after `config.get("vision_verify")` at line 341. When `vision_verify` is a non-mapping type (string, list, int), the guard raises `ValueError` with a clear message instructing the operator to fix config.yaml. The `ValueError` is caught by `main()`'s handler at line 520 (`except (OSError, ValueError)`), producing a clean error message + exit code 1 instead of an unhandled traceback.

Note: `isinstance(existing_vv, dict)` correctly returns `True` for ruamel's `CommentedMap` (which subclasses `dict`), so valid configs are not rejected.

### CR-02: estimate_fp_rate() counts success=None as false positive — RESOLVED

**File:** `calibrate_vision_verify.py:385-394`
**Verification:** Changed from `if not entry.get("success", True):` (truthiness) to `if entry.get("success") is False:` (explicit identity check). Now only entries with `success=False` (boolean) are counted as false positives. Entries with `success=None`, missing `success`, or non-boolean types (`0`, `""`) are excluded from the FP numerator but remain in the denominator (conservative choice, documented in the inline comment at lines 390-392).

### WR-01: Empty thresholds dict passes validation silently — RESOLVED

**File:** `apply_vision_verify_thresholds.py:185-193`
**Verification:** Added `elif len(thresholds) == 0:` branch after the `isinstance(thresholds, dict)` check. When the thresholds dict is empty, an error message is appended to the errors list, and `thresholds` is reset to `{}`. The `main()` function checks `if errors:` at line 511 and refuses the apply. An empty thresholds dict no longer silently passes validation.

### WR-02: total_entries undercounts when metrics buffer exceeds ring buffer limit — RESOLVED

**File:** `calibrate_vision_verify.py:217-262, 136-144, 498, 511-512`
**Verification:** `load_metrics_buffer()` now returns `tuple[list[dict], int]` — the loaded entries (subject to ring buffer limit) AND the total non-empty line count in the file (lines 256-260, second pass through the file). `CalibrationMetadata` has a new `total_entries_in_buffer: int` field (lines 136-144) with documentation explaining that when this exceeds `total_entries`, the ring buffer truncated older entries. `run_calibration()` passes both values to the metadata at lines 511-512. The operator can now see both counts and understand the limitation.

### WR-03: Bimodal valley detection picks first zero bucket, not valley midpoint — RESOLVED

**File:** `calibrate_vision_verify.py:338-357`
**Verification:** The minimum-count scan (lines 333-336) computes `min_count` as before. Then lines 346-349 build `min_indices` — a list of ALL bucket indices between the two peaks that share `min_count`. Line 354 selects the midpoint: `mid_idx = min_indices[len(min_indices) // 2]`. For a distribution with peaks at buckets 0 and 19 (all intermediates zero), `min_indices` has 18 entries, and `mid_idx` is `min_indices[9]` = bucket 10, yielding threshold ~0.525 instead of the old 0.075. Correct.

### WR-04: _threshold_cache poisons on config-read error — RESOLVED

**File:** `vision_verify.py:135-149`
**Verification:** The cache write (`_threshold_cache[stratum] = threshold` at line 141) is inside the `try` block, positioned after all config-reading code paths complete successfully. The `except Exception` block at lines 143-149 logs the warning and returns `_CONFIDENCE_THRESHOLD` WITHOUT writing to `_threshold_cache`. On the next call, the cache miss (`cached = _threshold_cache.get(stratum)` returns `None` at line 114) triggers a fresh config read. A transient config-read failure no longer poisons the cache for the process lifetime.

### WR-05: Audit log ring-buffer trim is non-atomic — RESOLVED

**File:** `apply_vision_verify_thresholds.py:393-439`
**Verification:** The `append_audit_log()` function is now purely append-only (line 429: `audit_path.open("a", encoding="utf-8")`). The non-atomic read-trim-write cycle has been completely removed. The docstring at lines 404-416 documents the removal and rationale, and instructs the operator to truncate manually if needed. The `AUDIT_LOG_MAX_ENTRIES` constant (lines 72-76) is retained as documentation/reference only. No data loss risk from concurrent appends.

## New Issues Check

Quick pattern-matching scan (depth=quick) was performed on all 3 reviewed files for:
- Hardcoded secrets: none found
- Dangerous functions (eval, exec, system, etc.): none found
- Debug artifacts (console.log, debugger, TODO, FIXME, HACK): none found
- Empty/bare except blocks: none found

No new Critical or Warning issues were introduced by the fixes.

---

_Reviewed: 2026-07-10T15:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
_Iteration: 2 (re-review after fixes)_
