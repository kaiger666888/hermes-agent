---
phase: 80-dub-03-voice-sample-protocol
fixed_at: 2026-07-10T06:50:00Z
review_path: .planning/phases/80-dub-03-voice-sample-protocol/80-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 80: Code Review Fix Report

**Fixed at:** 2026-07-10T06:50:00Z
**Source review:** `.planning/phases/80-dub-03-voice-sample-protocol/80-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (1 Critical + 6 Warnings)
- Fixed: 7
- Skipped: 0

**Test results:** 28 tests pass (21 validate_voice_clone_batch + 7 voice_clone_ref). 4 new tests added (2 for CR-01, 1 for WR-01, 1 for WR-02).

## Fixed Issues

### CR-01: Permission/path errors misclassified as format violations

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py`, `skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py`
**Commit:** `71d3d76`
**Status:** fixed: requires human verification
**Applied fix:** Split the catch-all `except (wave.Error, OSError, Exception)` handler into two branches: `wave.Error` records a genuine format violation (actual="non-WAV or corrupt"), `OSError` records an I/O error with a distinct message pointing at filesystem causes (actual="OS error: {type}", message contains "filesystem error, not format"). The `Exception` fallback was kept temporarily (removed in WR-03). Added 2 tests: `test_permission_denied_reports_io_error_not_format` (chmod 000) and `test_directory_as_wav_reports_io_error_not_format` (IsADirectoryError). Both verify the message contains "filesystem error" and the actual contains the specific OS error type name.

### WR-01: rglob silently swallows permission errors — no visibility into skipped files

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py`, `skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py`
**Commit:** `e658a61`
**Applied fix:** Replaced `rglob("*.wav")` with `os.walk`-based traversal that checks each subdirectory for readability (`os.access R_OK|X_OK`) before descending. Unreadable dirs are pruned from the walk, logged as warnings, and recorded in a new `skipped_dirs` field on `ValidationMetadata` (default empty list for backward compat). Added `test_permission_denied_dir_recorded_in_skipped_dirs` test. Updated `test_report_json_schema` to include `skipped_dirs` in expected metadata keys.

### WR-02: --verbose CLI flag declared but never used

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py`, `skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py`
**Commit:** `c682e3c`
**Applied fix:** Implemented `emit_verbose_details()` function called from `main()` when `args.verbose` is True. Prints a "Per-file details:" section after the Rich summary table: PASS files get a green marker + name + path; FAIL files get a red marker + name + path + each violation with `[rule_id] message`. Also surfaces `skipped_dirs` (WR-01) if any. Added to `__all__`. Added `test_verbose_flag_prints_per_file_details` CLI test verifying stdout contains "Per-file details:", PASS/FAIL markers, character names, and violation details.

### WR-03: Exception tuple (wave.Error, OSError, Exception) — Exception is redundant and overly broad

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py`
**Commit:** `d77161b`
**Applied fix:** Removed the `except Exception` fallback (added in CR-01 as a temporary bridge). Only `wave.Error` (format violation) and `OSError` (I/O error) are caught — both are expected error types from `wave.open` on bad files. Unexpected errors (TypeError, KeyError, AttributeError, etc.) now propagate as exit-2 crashes with a traceback, per the documented exit code semantics.

### WR-04: Dead tmp_wav_factory call in test_mixed_batch_exit_code_and_report writes stray file

**Files modified:** `skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py`
**Commit:** `ed3a743`
**Applied fix:** Removed the dead `tmp_wav_factory(duration_sec=5.0, sample_rate_hz=16000, channels=1)` call on line 223 that discarded the return value and wrote a stray WAV to `tmp_path` root (not in `voice_refs_dir`). Also removed the now-unused `tmp_wav_factory` fixture parameter from the test method signature. All 4 test files are now written via `_write_wav` directly into `voice_refs_dir`.

### WR-05: Unused tmp_wav_factory fixture on 9 tests

**Files modified:** `skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py`
**Commit:** `323dfee`
**Applied fix:** Removed the unused `tmp_wav_factory` fixture parameter from 6 test methods that use `_write_wav` instead: `test_character_extracted_from_filename`, `test_episode_extracted_from_voice_refs_parent`, `test_episode_null_when_no_voice_refs_in_path`, `test_recursive_search_finds_nested_wavs`, `test_report_json_schema`, `test_by_rule_violation_count_aggregation`. Also updated `_write_wav` and `test_stereo_fails_channels` docstrings to reflect the WR-06 conftest fix. Note: REVIEW.md listed 9 tests, but 3 of them (`test_too_short`, `test_too_long`, `test_low_sample_rate`) do call `tmp_wav_factory` — only 6 were actually unused.

### WR-06: tmp_wav_factory produces wrong-duration stereo (latent bug)

**Files modified:** `skills/movie-experts/audio_pipeline/tests/conftest.py`
**Commit:** `3c42858`
**Applied fix:** Fixed the conftest `tmp_wav_factory` to pack interleaved frames for stereo. Previously wrote one sample per `writeframes` call, producing half-duration files for stereo (5.0s request yielded 2.5s because `wave.writeframes` expects interleaved multi-channel frames). Now uses `struct.pack("<" + "h" * channels, *([sample] * channels))` per frame, mirroring the `_write_wav` helper pattern. Also added `_{channels}ch` suffix to the filename so mono/stereo variants of the same duration/rate don't collide. Verified no regressions: `test_voice_clone_ref_rejects_stereo` still passes because `validate_voice_clone_ref` checks channels before duration.

---

_Fixed: 2026-07-10T06:50:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
