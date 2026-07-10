---
phase: 80-dub-03-voice-sample-protocol
plan: 01
subsystem: dub
tags: [voice-clone, wav-validation, cosyvoice, stdlib-wave, pydantic-v2, rich-table]

# Dependency graph
requires:
  - phase: 72-dub
    provides: DUB-03 voice_clone_reference_wav JSON field + validate_voice_clone_ref single-file validator (4-rule contract)
provides:
  - Voice sample collection protocol doc (DUB-03-PROTOCOL)
  - Batch validator script for voice clone reference wavs (DUB-03-BATCH-VALIDATE)
  - 17 unit tests covering all 4 rules + batch behavior + extraction + CLI
affects: [phase-83-validate, cosyvoice-benchmark-runner, tts-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [stdlib-wave-batch-validation, pydantic-v2-report-schema, atomic-json-write, rich-table-summary]

key-files:
  created:
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/voice-sample-collection-protocol.md
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py
  modified: []

key-decisions:
  - "Single-script design (no operator_decision needed) — validation is pass/fail, not an operator decision"
  - "4 hard rules hardcoded (duration 3-10s + WAV format + >=16kHz + mono) — no config flags"
  - "stdlib wave module only (no pydub/librosa/numpy) per INFRA-04 + CLAUDE.md no-new-deps"
  - "Best-effort episode/character extraction — validator works even if path doesn't match assets/<episode>/voice_refs/<character>.wav convention"
  - "Exit code 1 on any failure (CI-friendly) — operator can gate pipeline ingestion on exit code"

patterns-established:
  - "Batch validator pattern: rglob + per-file validation + structured JSON report + Rich table (complements Phase 77/78/79 runner pattern)"
  - "T-80-01 mitigation: catch wave.Error + OSError + Exception on wave.open, mark as format violation (never crash)"
  - "T-80-04 mitigation: atomic JSON write via temp file + os.replace (mirror Phase 78/79)"

requirements-completed: [DUB-03-PROTOCOL, DUB-03-BATCH-VALIDATE]

# Metrics
duration: 6min
completed: 2026-07-10
---

# Phase 80: DUB-03 Voice Sample Protocol Summary

**Voice sample collection protocol doc + stdlib-wave batch validator with Pydantic v2 report schema enforcing 4 hard rules (duration 3-10s + WAV + >=16kHz + mono) with CI-friendly exit codes**

## Performance

- **Duration:** 6 min (358s)
- **Started:** 2026-07-10T06:27:07Z
- **Completed:** 2026-07-10T06:33:05Z
- **Tasks:** 2
- **Files modified:** 3 (all new)

## Accomplishments

- Created `voice-sample-collection-protocol.md` with 5 sections (Collection Guidelines, File Naming Convention, Technical Requirements, Troubleshooting, Validator Usage) closing the DUB-03-PROTOCOL operator-action handoff
- Created `validate_voice_clone_batch.py` — batch validator with Pydantic v2 report schema, 4-rule validation (duration/format/sample_rate/channels), recursive `.wav` search, Rich table output, atomic JSON write, CI-friendly exit codes (0/1/2)
- 17/17 unit tests passing covering all 4 rules + batch behavior + character/episode extraction + recursive search + CLI + report schema + aggregation

## Task Commits

Each task was committed atomically (kais-hermes-skills repo):

1. **Task 1: Protocol doc** - `8b603e6` (docs)
2. **Task 2: Validator + tests (RED)** - `1e09c6f` (test)
3. **Task 2: Validator + tests (GREEN)** - `21598dc` (feat)

**Plan metadata:** pending (hermes-agent repo)

_TDD: Task 2 followed RED/GREEN cycle. RED commit (`1e09c6f`) wrote failing tests first. GREEN commit (`21598dc`) implemented the validator to make all tests pass._

## Files Created/Modified

- `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/voice-sample-collection-protocol.md` — Voice sample collection protocol doc with 5 sections: collection guidelines (3-10s, environment requirements), file naming convention (`assets/<episode>/voice_refs/<character>.wav`), technical requirements (4 hard rules), troubleshooting (ffmpeg solutions), validator usage (CLI examples + exit codes + JSON schema)
- `kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py` — Batch validator script: Pydantic v2 report schema (ValidationReport with metadata/characters/summary), 4-rule validation via stdlib wave module, recursive `.wav` search via `rglob("*.wav")`, Rich table output, argparse CLI with `--voice-refs-dir` flag, atomic JSON write (temp + os.replace), exit codes (0=all pass, 1=any fail, 2=crash)
- `kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py` — 17 unit tests in `TestValidateVoiceCloneBatch` class covering: valid wav passes, too short/long fails duration, stereo fails channels, low sample rate fails sample_rate, non-WAV/corrupt fails format, empty directory, mixed batch, character extraction, episode extraction (voice_refs parent + null), recursive search, CLI --help, nonexistent dir exit 2, report JSON schema, by_rule_violation_count aggregation

## Decisions Made

- **Single-script design (no operator_decision):** Unlike Phase 77/78/79 which have a 2-script pattern (runner + lock/verdict/apply), Phase 80 is a single validator script. Validation is a pass/fail check, not an operator decision — no "lock" or "apply" step. Operator runs validator, reviews failures, re-records samples, re-runs until all pass.
- **4 hard rules hardcoded:** Duration 3-10s + WAV format + >=16kHz + mono are hardcoded per success criterion. No `--min-duration` / `--max-duration` / `--min-sample-rate` flags. If operator needs different thresholds, they edit the script (documented in protocol doc).
- **Best-effort episode/character extraction:** Character always extracted from filename stem. Episode extracted from parent dir if path matches `voice_refs/<character>.wav` or `<episode>/voice_refs/<character>.wav`. Episode is `None` if path doesn't match — validator still runs (path-agnostic).
- **Format failure skips other 3 rules:** If `wave.open()` fails (corrupt header, non-WAV file), only the format violation is recorded. Can't check duration/rate/channels without reading the header.
- **`_write_wav` test helper with proper interleaved multi-channel frames:** The conftest `tmp_wav_factory` writes one sample per `writeframes` call, which produces half-length data for stereo (the wave module adjusts `nframes` based on actual data length). The test helper uses `struct.pack("<" + "h" * channels, ...)` to write proper interleaved frames.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _write_wav helper for proper stereo WAV data**
- **Found during:** Task 2 (GREEN phase — stereo test failed)
- **Issue:** The conftest `tmp_wav_factory` writes one sample per `writeframes` call. For stereo (`channels=2`), `writeframes` expects `nchannels * sampwidth` bytes per frame (4 bytes for stereo 16-bit), but the factory passes only 2 bytes. The wave module adjusts `nframes` based on actual data length, so a 5s@16kHz stereo recording reports `nframes=40000` instead of `80000`, making `duration=2.5s` instead of `5.0s`. This caused the stereo test to fail with 2 violations (duration + channels) instead of just 1 (channels).
- **Fix:** Created `_write_wav` helper in the test file that writes proper interleaved multi-channel frames using `struct.pack("<" + "h" * channels, *([sample] * channels))`. Updated the stereo test to use `_write_wav` instead of `tmp_wav_factory`.
- **Files modified:** `test_validate_voice_clone_batch.py` (_write_wav helper + test_stereo_fails_channels)
- **Verification:** All 17 tests pass, stereo test now produces exactly 1 channels violation
- **Committed in:** `21598dc` (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix necessary for test correctness. No scope creep. The conftest `tmp_wav_factory` was NOT modified (preserving existing Phase 72 tests).

## Issues Encountered

- conftest `tmp_wav_factory` produces incorrect stereo WAV files (half-length data). Did NOT modify the fixture — created a local `_write_wav` helper instead to avoid breaking existing Phase 72 tests.

## User Setup Required

None - no external service configuration required. The validator is a pure stdlib script with no dependencies beyond pydantic + rich (already in the project).

## Next Phase Readiness

- DUB-03 operator-action handoff is now closed: operator reads the protocol doc, sources samples per guidelines, runs the validator, gets a pass/fail report identifying exactly which samples need re-recording and which rule(s) they violated.
- Phase 81 (XCUT-04b Cloud Engine Bootstrap) is unblocked — Phase 80 was the next sequential phase on the critical path.
- No blockers or concerns for Phase 81.

## TDD Gate Compliance

- RED gate: `1e09c6f` — `test(80-01): add failing tests for batch validator (RED phase)` — tests fail with `ModuleNotFoundError` (module not yet created)
- GREEN gate: `21598dc` — `feat(80-01): implement batch validator + fix test helper (GREEN phase)` — all 17 tests pass
- REFACTOR gate: skipped (code is already clean, no refactoring needed)

Both RED and GREEN gate commits present in git log. TDD cycle compliant.

## Self-Check: PASSED

**Files created:**
- FOUND: `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/voice-sample-collection-protocol.md`
- FOUND: `kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py`
- FOUND: `kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_validate_voice_clone_batch.py`

**Commits:**
- FOUND: `8b603e6` (Task 1 — protocol doc)
- FOUND: `1e09c6f` (Task 2 RED — failing tests)
- FOUND: `21598dc` (Task 2 GREEN — validator implementation)

**Tests:** 17/17 passing
**Existing tests:** 7/7 Phase 72 tests still passing (no regressions)

---
*Phase: 80-dub-03-voice-sample-protocol*
*Completed: 2026-07-10*
