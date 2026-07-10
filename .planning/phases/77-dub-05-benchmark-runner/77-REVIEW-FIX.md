---
phase: 77-dub-05-benchmark-runner
fixed_at: 2026-07-10T13:00:00Z
review_path: .planning/phases/77-dub-05-benchmark-runner/77-REVIEW.md
iteration: 1
findings_in_scope: 12
fixed: 12
skipped: 0
status: all_fixed
---

# Phase 77: Code Review Fix Report

**Fixed at:** 2026-07-10T13:00:00Z
**Source review:** `.planning/phases/77-dub-05-benchmark-runner/77-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 12 (3 Critical + 9 Warning)
- Fixed: 12
- Skipped: 0

## Fixed Issues

### CR-01: check_silent/compute_wer exceptions mark successful audio as failed

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`
**Commit:** `bc322c6`
**Applied fix:** Moved `check_silent()` and `compute_wer()` outside the main try/except block. Audio analysis is now best-effort: if audio was generated successfully, analysis failures are logged as warnings but do not set the VariantResult error field. Previously, `FileNotFoundError` from missing ffmpeg was caught by the outer `except Exception`, causing VariantResult to have both `audio_path` AND `error` set — an inconsistent state.

### CR-02: validate_lock crashes with TypeError on non-string variant (JSON array)

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py`, `skills/movie-experts/audio_pipeline/tests/test_lock_cosyvoice_default.py`
**Commit:** `7d838f1`
**Applied fix:** Added `isinstance(variant_id, (str, type(None)))` guard before `VARIANT_ID_MAP.get(variant_id, ...)`. Non-string, non-None variants (e.g. JSON arrays `[]` or dicts `{}`) now produce a clean validation error instead of crashing with `TypeError: unhashable type: 'list'`. Added 2 tests: `test_validate_lock_refuses_array_variant` and `test_validate_lock_refuses_dict_variant`.

### CR-03: write_lock performs non-atomic write of VERSION.json (data loss risk)

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py`
**Commit:** `5345547`
**Applied fix:** Replaced direct `open("w")` write with atomic write pattern: write to `NamedTemporaryFile` in the same directory, then `os.replace()` to atomically swap into place. Prevents VERSION.json corruption if the process crashes (SIGKILL, OOM) between truncation and `json.dump` completing.

### WR-01: check_silent does not catch FileNotFoundError or TimeoutExpired

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`, `skills/movie-experts/audio_pipeline/tests/test_run_cosyvoice_benchmark.py`
**Commit:** `d00c64e`
**Applied fix:** Wrapped `subprocess.run(["ffmpeg", ...])` in `check_silent()` with try/except for `FileNotFoundError` and `subprocess.TimeoutExpired`. Returns `False` (assume non-silent) on failure. Added 2 tests: `test_check_silent_ffmpeg_missing` and `test_check_silent_ffmpeg_timeout`.

### WR-02: poll_comfyui and _poll_gold_team silently swallow all RequestException

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`
**Commit:** `49b87df`
**Applied fix:** Replaced bare `pass` in `poll_comfyui` and `_poll_gold_team` `RequestException` handlers with `logger.debug()` calls. Operators now have visibility into network failures during polling instead of the runner appearing to hang silently.

### WR-03: _VARIANT_TO_VERSION_JSON is dead code (never referenced)

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`
**Commit:** `79b8dc1`
**Applied fix:** Removed the `_VARIANT_TO_VERSION_JSON` dict that was defined at module level but never referenced. It duplicated `VARIANT_ID_MAP` in `lock_cosyvoice_default.py`.

### WR-04: load_benchmark_report and load_version_json do not validate nested dict types

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py`
**Commit:** `552e0bb`
**Applied fix:** Added `isinstance(data.get("operator_decision"), dict)` check in `load_benchmark_report()` and `isinstance(data.get("tts"), dict)` check in `load_version_json()`. Non-dict nested fields now produce a clean `ValueError` at load time instead of crashing later with `AttributeError` or `TypeError`.

### WR-05: Gold-team task_id not unique across re-runs (collides with stale tasks)

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`
**Commit:** `05b5c45`
**Applied fix:** Added a run-level `_RUN_ID = uuid.uuid4().hex[:8]` and changed task_id format from `f"bench_{line_id}"` to `f"bench_{_RUN_ID}_{line_id}"`. Ensures uniqueness across re-runs with the same dialogue lines.

### WR-06: WER formula can exceed 1.0, contradicting docstring and Rich table display

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`
**Commit:** `e44f53e`
**Applied fix:** Clamped WER to `min(distance / len(reference_text), 1.0)`. Updated docstrings to clarify this is technically Character Error Rate (CER) since Chinese has no word boundaries. The field remains named `wer` for schema consistency.

### WR-07: lock_date uses local date, runner timestamp uses UTC (timezone inconsistency)

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py`
**Commit:** `6659ebc`
**Applied fix:** Changed `write_lock()` and `main()` from `datetime.date.today()` (local) to `datetime.datetime.now(datetime.timezone.utc).date().isoformat()` (UTC). Ensures consistency with the runner's UTC timestamp.

### WR-08: metadata.dialogue_lines_file records copied path, not original input path

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`, `skills/movie-experts/audio_pipeline/tests/test_run_cosyvoice_benchmark.py`
**Commit:** `7f3cf7f`
**Applied fix:** Added `dialogue_lines_source` parameter to `run_benchmark()` and passed the original `--dialogue-lines` argument from `main()`. `BenchmarkMetadata.dialogue_lines_file` now records the original input path. Falls back to the copied path if source not provided (backward compatibility). Updated test to verify.

### WR-09: Gold-team pre-check is redundant — each line re-checks reachability

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`
**Commit:** `9d598c3`
**Applied fix:** Populated a `gold_team_unreachable` set during the pre-check loop. The main loop now consults this set instead of re-calling `_check_gold_team_reachable()` for every dialogue line. Reduces reachability checks from N+1 to 1 per gold-team variant.

## Skipped Issues

None — all in-scope findings were fixed.

---

_Fixed: 2026-07-10T13:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
