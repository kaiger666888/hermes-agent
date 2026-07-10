---
phase: 80-dub-03-voice-sample-protocol
reviewed: 2026-07-10T06:42:01Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: issues_found
---

# Phase 80: Code Review Report

**Reviewed:** 2026-07-10T06:42:01Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Phase 80 (DUB-03 Voice Sample Protocol) implements a sync-only batch validator for voice clone reference WAVs plus a protocol doc + tests. The implementation is generally sound — stdlib `wave` module usage, Pydantic v2 schema with `extra="forbid"`, atomic JSON write via `os.replace`, and a comprehensive test suite. However, one BLOCKER and several robustness defects warrant attention before this ships.

The most significant issue is a **misclassification of permission errors as format violations** (CR-01): the catch-all `except (wave.Error, OSError, Exception)` tuple lumps `PermissionError`, `IsADirectoryError`, and any other `OSError` into the `format` rule, which misleads the operator into re-recording samples when the real fix is a `chmod` or path correction. Several WARNING-tier issues follow: `rglob` silently skips permission-denied directories without surfacing the skip, the `--verbose` flag is declared but never read, the exception tuple lists `Exception` redundantly after the specific types, and a test contains dead code that writes a stray WAV file.

The protocol doc is mostly accurate but documents `.WAV` (uppercase) as discoverable on Windows without flagging that Linux (the primary deployment target per CLAUDE.md) silently skips uppercase extensions — this is a documentation gap, not a code bug.

## Critical Issues

### CR-01: Permission/path errors misclassified as format violations

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py:268`
**Issue:** The exception handler catches `(wave.Error, OSError, Exception)` and unconditionally records a `format` violation with message `"Not a valid WAV file: {exc}"`. This misclassifies operational errors that have nothing to do with file format:

- `PermissionError` (unreadable file) — operator is told to re-record, but the real fix is `chmod`.
- `IsADirectoryError` (path is a directory) — operator is told the file is corrupt.
- `FileNotFoundError` (race: file deleted between `rglob` and `wave.open`) — same misdirection.

Verified by reproducing: `wave.open` on a `chmod 000` WAV raises `PermissionError`, which is an `OSError` subclass, so it lands in this handler and is reported as `rule_id="format"` with `actual="non-WAV or corrupt"`. The operator's next action (per the protocol doc's Troubleshooting section) would be to re-export the file — wasted effort when the actual problem is file permissions.

**Fix:** Split the exception handler into two branches — true format errors (`wave.Error`) vs. I/O errors (`OSError`). Record format violations only for `wave.Error`; for `OSError`, record a separate operational-error outcome (or at minimum, a different `rule_id` / message that points the operator at filesystem causes).

```python
    except wave.Error as exc:
        # Genuine format violation — corrupt RIFF header, non-WAV content, etc.
        violations.append(Violation(
            rule_id="format",
            expected="WAV (RIFF)",
            actual="non-WAV or corrupt",
            message=f"Not a valid WAV file: {exc}",
        ))
    except OSError as exc:
        # I/O error — permission denied, file vanished, is a directory, etc.
        # NOT a format problem. Report as format violation but with a message
        # that points the operator at filesystem causes, not re-recording.
        violations.append(Violation(
            rule_id="format",
            expected="readable WAV file",
            actual=f"OS error: {type(exc).__name__}",
            message=f"Could not read file (filesystem error, not format): {exc}. "
                    f"Check permissions / path.",
        ))
```

(If a distinct `rule_id` like `"io_error"` is preferable, add it to `RULES` and `by_rule_violation_count` — but that is a larger change. The minimal fix above at least gives the operator an accurate message.)

## Warnings

### WR-01: `rglob` silently swallows permission errors — no visibility into skipped files

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py:308`
**Issue:** `voice_refs_dir.rglob("*.wav")` silently skips directories it cannot enter (`PermissionError` on the directory itself is swallowed by CPython's `Path.rglob` implementation — it uses `os.scandir` which raises, but `rglob` catches and continues). Verified: with a `chmod 000` subdirectory containing a valid WAV, `rglob` returns only the files in readable directories and emits no warning. The validator then reports `total_files` as the count of files it could see, with no indication that some directories were skipped.

This is a silent-failure pattern: an operator runs the validator, sees "all 3 files passed", and assumes their sample set is complete — unaware that 2 more samples existed in a subdirectory the validator couldn't enter.

**Fix:** Either (a) catch `OSError` during `rglob` and log a warning for each skipped directory, or (b) do an explicit recursive walk with `os.walk` and surface permission errors:

```python
    wav_files: list[Path] = []
    for root, dirs, files in os.walk(voice_refs_dir):
        for name in files:
            if name.lower().endswith(".wav"):
                wav_files.append(Path(root) / name)
        # os.walk does not prune on permission errors by default; catch and log
    # If you want to detect unreadable dirs explicitly:
    for root, dirs, _ in os.walk(voice_refs_dir):
        for d in dirs:
            full = Path(root) / d
            if not os.access(full, os.R_OK | os.X_OK):
                logger.warning("Skipping unreadable directory: %s", full)
    wav_files.sort(key=lambda p: str(p))
```

### WR-02: `--verbose` CLI flag declared but never used

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py:421-425`
**Issue:** The `--verbose` argument is added to the parser (line 421) and parsed into `args.verbose` (line 427), but `args.verbose` is never referenced anywhere in `main()`. The flag is a no-op — an operator passing `--verbose` gets the same output as without it. The docstring says "Print per-file details (default: summary table only)" but no per-file details are ever printed.

**Fix:** Either implement the verbose behavior (print per-file violation details) or remove the flag to avoid misleading the operator. Minimal implementation:

```python
    if args.verbose:
        for char in report.characters:
            if not char.passed:
                print(f"\n  {char.character} ({char.path}):")
                for v in char.violations:
                    print(f"    [{v.rule_id}] {v.message}")
```

### WR-03: Exception tuple `(wave.Error, OSError, Exception)` — `Exception` is redundant and overly broad

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py:268`
**Issue:** The `except (wave.Error, OSError, Exception) as exc:` clause lists `Exception` as the third tuple element. Since `Exception` is the base class of both `wave.Error` and `OSError`, listing it makes the first two redundant — and more importantly, it catches *every* exception including `KeyError`, `ValueError`, `AttributeError`, and other programming errors that indicate a bug rather than a bad file. A `TypeError` from a Pydantic schema mismatch, for example, would be silently reported as a "format violation" instead of surfacing as a crash for the developer to fix.

This is related to CR-01 (which addresses the misclassification of `OSError` subclasses). Even after splitting `wave.Error` and `OSError`, the bare `Exception` should be removed — let unexpected exceptions propagate so they surface as exit-code-2 crashes with a traceback, per the documented exit code semantics ("2 = crash").

**Fix:** Remove `Exception` from the tuple. Catch only the specific, expected error types:

```python
    except wave.Error as exc:
        # format violation
        ...
    except OSError as exc:
        # I/O error (permission, missing file, etc.)
        ...
    # Do NOT catch Exception here — let unexpected errors propagate as exit 2.
```

### WR-04: Dead `tmp_wav_factory` call in `test_mixed_batch_exit_code_and_report` writes stray file

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py:223`
**Issue:** Line 223 calls `tmp_wav_factory(duration_sec=5.0, sample_rate_hz=16000, channels=1)` but discards the return value. The factory writes a WAV file to `tmp_path / "ref_5.0s_16000hz.wav"` (in `tmp_path` root, not in `voice_refs_dir`). The test then calls `_write_wav` for all 4 actual test files inside `voice_refs_dir`. The stray file is not counted by `run_validation(voice_refs_dir)` because the validator only scans `voice_refs_dir` — but if a future test variant passes `tmp_path` instead of `voice_refs_dir`, it would pick up the stray file as a 5th character and break the assertion `report.summary.total == 4`.

The `tmp_path` and `tmp_wav_factory` parameters on this test function are both unused except for this dead call — `tmp_wav_factory` can be removed from the signature entirely.

**Fix:** Remove the dead call and the unused fixture parameter:

```python
    def test_mixed_batch_exit_code_and_report(self, tmp_path):
        """80-01i: mixed pass/fail batch — full report with all characters."""
        voice_refs_dir = tmp_path / "voice_refs"
        voice_refs_dir.mkdir()
        _write_wav(voice_refs_dir / "alice.wav", 5.0, 16000, 1)
        _write_wav(voice_refs_dir / "bob.wav", 5.0, 22050, 1)
        _write_wav(voice_refs_dir / "short.wav", 2.0, 16000, 1)
        _write_wav(voice_refs_dir / "stereo.wav", 5.0, 16000, 2)
        ...
```

### WR-05: Several test functions take `tmp_wav_factory` but don't use it

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py:118,131,161,244,255,268,281,336,381`
**Issue:** Multiple test methods declare `tmp_wav_factory` as a parameter but never call it — they use `_write_wav` instead (because the conftest factory has a known stereo bug, see WR-06 below, and cannot write to arbitrary paths). Unused fixture parameters are harmless at runtime (pytest will still set them up) but they add noise and mislead readers into thinking the factory is used. Examples: `test_too_short_fails_duration` (line 118), `test_too_long_fails_duration` (line 131), `test_low_sample_rate_fails_sample_rate` (line 161), `test_character_extracted_from_filename` (line 244), `test_episode_extracted_from_voice_refs_parent` (line 255), `test_episode_null_when_no_voice_refs_in_path` (line 268), `test_recursive_search_finds_nested_wavs` (line 281), `test_report_json_schema` (line 336), `test_by_rule_violation_count_aggregation` (line 381).

**Fix:** Remove `tmp_wav_factory` from the parameter lists of all test methods that don't call it. Only `test_valid_wav_passes_all_rules` (line 104) actually uses the factory.

### WR-06: `tmp_wav_factory` conftest fixture produces wrong-duration output for stereo

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/conftest.py:54-58`
**Issue:** The conftest `tmp_wav_factory` writes one sample per `wf.writeframes(struct.pack("<h", sample))` call, but when `channels=2`, `wave.writeframes` expects interleaved multi-channel frames (i.e., 2 samples per frame for stereo). Writing one sample per call produces a file with half the declared duration: a 5.0s stereo request yields a 2.5s file (verified by reproducing — `wf.getnframes()` returns 40000 instead of 80000 for 5s@16kHz stereo, giving `40000/16000 = 2.5s`). The test file's `_write_wav` helper at line 67-93 correctly packs interleaved samples (`struct.pack("<" + "h" * channels, *([sample] * channels))`), which is why the stereo test uses `_write_wav` instead.

This is a latent bug in the shared fixture — any future test that uses `tmp_wav_factory` with `channels=2` will get a wrong-duration file and likely a confusing assertion failure.

**Fix:** Fix the conftest factory to pack interleaved frames (mirror the `_write_wav` pattern in the test file):

```python
    def _factory(duration_sec: float = 5.0, sample_rate_hz: int = 16000,
                 channels: int = 1) -> Path:
        p = tmp_path / f"ref_{duration_sec}s_{sample_rate_hz}hz_{channels}ch.wav"
        n_frames = int(duration_sec * sample_rate_hz)
        with wave.open(str(p), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate_hz)
            for i in range(n_frames):
                sample = int(32767 * 0.3 * math.sin(2 * math.pi * 220 * i / sample_rate_hz))
                frame_data = struct.pack("<" + "h" * channels, *([sample] * channels))
                wf.writeframes(frame_data)
        return p
```

(Also add `_{channels}ch` to the filename so mono and stereo variants of the same duration/rate don't collide.)

## Info

### IN-01: Protocol doc case-sensitivity note is accurate but understates Linux risk

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/voice-sample-collection-protocol.md:70`
**Issue:** The doc states: "The validator finds files via `rglob("*.wav")` — case-insensitive on Windows, case-sensitive on Linux." This is technically correct, but the primary deployment target (per CLAUDE.md) is a Linux Docker container. An operator who saves a file as `alice.WAV` (common on macOS, where the default recording app may uppercase the extension) and runs the validator on Linux will see "No .wav files found" — a confusing result. Verified: `rglob("*.wav")` on Linux does not match `bob.WAV` or `carol.Wav`.

**Fix:** Either (a) make the validator case-insensitive by globbing `*.wav` and `*.WAV` (and `.Wav`), or (b) add a stronger warning in the protocol doc: "On Linux (the production deployment target), files with uppercase `.WAV` extensions are silently skipped. Always save with lowercase `.wav`."

### IN-02: Duration boundary semantics not documented in protocol

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/voice-sample-collection-protocol.md:79-83`
**Issue:** The protocol says "Minimum: 3.0s" and "Maximum: 10.0s" but doesn't clarify whether the boundaries are inclusive or exclusive. The validator uses strict `<` and `>` (lines 235, 242), so exactly 3.0s and exactly 10.0s pass. This is a reasonable choice, but the doc should state it explicitly to avoid operator confusion ("is 3.0s exactly OK?").

**Fix:** Add to the protocol doc: "Boundaries are inclusive: exactly 3.0s and exactly 10.0s pass."

### IN-03: `RULES` constants dict uses `object` value type — loses type safety

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py:82`
**Issue:** `RULES: dict[str, dict[str, object]]` types all values as `object`, which forces `# type: ignore[operator]` on every comparison (lines 235, 242, 251, 260). The dict mixes `float` (`min`/`max` for duration), `int` (`min` for sample_rate, `expected` for channels), and `str` (`expected` for format). A `TypedDict` or per-rule dataclass would give proper type safety and eliminate the `# type: ignore` comments.

**Fix:** (Optional — this is a maintainability improvement, not a bug.) Define each rule as a small dataclass or `TypedDict`:

```python
from typing import TypedDict

class DurationRule(TypedDict):
    rule_id: str
    description: str
    min: float
    max: float
# ... etc, then RULES: dict[str, DurationRule | FormatRule | ...]
```

### IN-04: `extract_episode` has an undocumented second branch

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py:193-194`
**Issue:** The second branch (`if path.parent.parent.name == "voice_refs"`) is documented as "handles rglob started from a parent" but this scenario is not covered by any test. All tested paths use the first branch (`voice_refs/alice.wav` -> episode is grandparent). The second branch would fire for a path like `ep-001/voice_refs/subdir/alice.wav` (where `subdir.parent == voice_refs`), returning `episode="subdir"` — which is likely wrong (the episode should be `ep-001`, not `subdir`). This logic appears to be attempting to handle a case that doesn't match the documented convention, and the return value may be incorrect.

**Fix:** Either add a test that exercises the second branch with a clear expected outcome, or remove the branch if it doesn't correspond to a real use case. If the intent is "rglob started from `voice_refs/` itself, so `alice.wav` has `parent = voice_refs` and `parent.parent = voice_refs`'s parent", that's already handled by the first branch — the second branch only fires for deeper nesting that the convention doesn't define.

---

_Reviewed: 2026-07-10T06:42:01Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
