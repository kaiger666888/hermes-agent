---
phase: 80-dub-03-voice-sample-protocol
reviewed: 2026-07-10T07:15:00Z
depth: quick
files_reviewed: 3
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/conftest.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 80: Code Review Report (Re-Review, Iteration 2)

**Reviewed:** 2026-07-10T07:15:00Z
**Depth:** quick
**Files Reviewed:** 3
**Status:** clean

## Summary

Re-review after fixes for Phase 80 (DUB-03 Voice Sample Protocol). The original review (iteration 1) found 1 Critical + 6 Warning + 4 Info findings. All 7 Critical+Warning findings have been verified as resolved. No new Critical or Warning issues were introduced by the fixes.

All 21 tests in `test_validate_voice_clone_batch.py` pass. All 7 tests in `test_voice_clone_ref.py` (which depends on the shared `conftest.py` fixture) pass. The full `audio_pipeline/tests/` suite (52 tests) passes with zero failures — confirming the conftest WR-06 fix is backward-compatible.

## Verification of Original Findings

### CR-01: Permission/path errors misclassified as format violations — RESOLVED

**File:** `validate_voice_clone_batch.py:274-304`
**Verification:** The exception handler is now split into two branches:
- `except wave.Error as exc:` (line 274) — genuine format violations, records `actual="non-WAV or corrupt"`.
- `except OSError as exc:` (line 285) — I/O errors (PermissionError, IsADirectoryError, FileNotFoundError), records `actual=f"OS error: {type(exc).__name__}"` with a message pointing at filesystem causes.
- The bare `Exception` has been removed; a comment at lines 300-304 documents the decision to let unexpected errors propagate as exit-2 crashes.

Two new tests verify the fix:
- `test_permission_denied_reports_io_error_not_format` (line 203) — chmod 000 file, asserts `"filesystem error" in message` and `"PermissionError" in actual`.
- `test_directory_as_wav_reports_io_error_not_format` (line 231) — directory with .wav suffix, asserts `"filesystem error" in message` and `"IsADirectoryError" in actual`.

Both tests pass.

### WR-01: rglob silently swallows permission errors — RESOLVED

**File:** `validate_voice_clone_batch.py:335-356`
**Verification:** `rglob` replaced with `os.walk` that explicitly checks each subdirectory via `os.access(full, os.R_OK | os.X_OK)` (line 351). Unreadable dirs are pruned from `dirs[:]` in-place (standard os.walk convention, line 356) and recorded in `skipped_dirs` list (line 354). A `logger.warning` is emitted for each skipped dir (line 355).

A new `skipped_dirs: list[str]` field was added to `ValidationMetadata` (line 146) with a descriptive docstring. The field defaults to an empty list via `default_factory=list`.

New test `test_permission_denied_dir_recorded_in_skipped_dirs` (line 347) verifies: a locked subdir is not traversed, `total_files` excludes its contents, and `skipped_dirs` contains the locked dir path. Test passes.

### WR-02: --verbose CLI flag declared but never used — RESOLVED

**File:** `validate_voice_clone_batch.py:445-468, 555-557`
**Verification:** New `emit_verbose_details(report)` function (line 445) prints per-file PASS/FAIL status with violation details (rule_id + message for each violation). It also surfaces skipped directories if any (lines 464-468). Called from `main()` at line 555-557 when `args.verbose` is set.

New test `test_verbose_flag_prints_per_file_details` (line 412) runs the CLI with `--verbose` and asserts the output contains `"Per-file details:"`, `"PASS"`, `"FAIL"`, `"alice"`, `"short"`, `"duration"`, and `"below minimum"`. Test passes.

### WR-03: Exception tuple redundantly lists Exception — RESOLVED

**File:** `validate_voice_clone_batch.py:274-304`
**Verification:** `Exception` removed from the catch tuple. The handler now catches only `wave.Error` (line 274) and `OSError` (line 285). Comment at lines 300-304 explicitly documents that unexpected errors (TypeError, KeyError, AttributeError) should propagate as exit-2 crashes per the documented exit code semantics. This was resolved as part of the CR-01 fix.

### WR-04: Dead tmp_wav_factory call in test_mixed_batch — RESOLVED

**File:** `test_validate_voice_clone_batch.py:265`
**Verification:** The dead `tmp_wav_factory(duration_sec=5.0, ...)` call is gone. The test signature is now `def test_mixed_batch_exit_code_and_report(self, tmp_path):` — `tmp_wav_factory` removed from the parameter list. The test body (lines 267-283) uses only `_write_wav` to create the 4 test files. Test passes.

### WR-05: Unused tmp_wav_factory parameters in test methods — RESOLVED

**File:** `test_validate_voice_clone_batch.py`
**Verification:** `tmp_wav_factory` remains in only 4 test signatures, all of which actually call it:
- `test_valid_wav_passes_all_rules` (line 104) — calls it at line 106.
- `test_too_short_fails_duration` (line 118) — calls it at line 120.
- `test_too_long_fails_duration` (line 131) — calls it at line 133.
- `test_low_sample_rate_fails_sample_rate` (line 161) — calls it at line 163.

All 9 test methods flagged in the original review (`test_character_extracted_from_filename`, `test_episode_extracted_from_voice_refs_parent`, `test_episode_null_when_no_voice_refs_in_path`, `test_recursive_search_finds_nested_wavs`, `test_report_json_schema`, `test_by_rule_violation_count_aggregation`, `test_mixed_batch_exit_code_and_report`, `test_stereo_fails_channels`, `test_non_wav_fails_format`, `test_corrupt_wav_fails_format`, `test_permission_denied_reports_io_error_not_format`, `test_directory_as_wav_reports_io_error_not_format`, `test_empty_directory_produces_empty_report`, `test_permission_denied_dir_recorded_in_skipped_dirs`, `test_cli_help_exits_zero`, `test_nonexistent_dir_exits_2`, `test_verbose_flag_prints_per_file_details`) no longer have `tmp_wav_factory` in their signatures unless they use it.

### WR-06: conftest tmp_wav_factory produces wrong-duration stereo — RESOLVED

**File:** `conftest.py:45-63`
**Verification:** The factory now packs interleaved frames for all channels:
```python
frame_data = struct.pack("<" + "h" * channels, *([sample] * channels))
wf.writeframes(frame_data)
```
(line 61). This mirrors the `_write_wav` helper pattern in the test file. The filename now includes `_{channels}ch` to prevent mono/stereo collisions (line 47). Comment at lines 54-56 documents the rationale and references Phase 80 WR-06.

**Backward compatibility verified:** All 7 tests in `test_voice_clone_ref.py` pass, including `test_voice_clone_ref_rejects_stereo` (line 62) which uses `tmp_wav_factory(duration_sec=5.0, sample_rate_hz=16000, channels=2)` and expects a ValueError matching "mono". The stereo file now has the correct 5.0s duration (previously 2.5s), and the validator correctly rejects it for being stereo. The full `audio_pipeline/tests/` suite (52 tests) passes with zero failures.

## New Issues Introduced by Fixes

None. The fixes are clean, well-commented, and well-tested. No new Critical or Warning issues found.

## Info-Tier Findings (carried forward, not blocking)

The 4 Info findings from the original review (IN-01 through IN-04) are not blocking and were not required to be fixed. For completeness:
- IN-01 (case-sensitivity): The switch from `rglob("*.wav")` to `name.lower().endswith(".wav")` (line 343) actually resolves this as a side effect — the validator is now case-insensitive on all platforms, matching `.WAV`, `.Wav`, etc.
- IN-02, IN-03, IN-04: No changes observed; these remain as documented info-tier notes.

---

_Reviewed: 2026-07-10T07:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
_Iteration: 2 (re-review after fixes)_
