# Phase 80: DUB-03 Voice Sample Protocol - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-action handoff closure for DUB-03: deliver a voice sample collection protocol doc + batch validator script that turns per-character voice sample sourcing into a 5-minute operator task. Validator catches technical requirement violations before pipeline ingestion.

**In scope:**
- `references/voicer/voice-sample-collection-protocol.md` — per-character voice sample collection guidelines (3-10s clean recording, environment requirements, file naming convention `assets/<episode>/voice_refs/<character>.wav`, troubleshooting).
- `scripts/validate_voice_clone_batch.py` — batch validator that recursively finds all `.wav` files in a directory, validates each against 4 hard rules (duration 3-10s + WAV format + sample rate ≥16kHz + mono channel), outputs structured JSON report + Rich table summary, exits 0 if all pass / 1 if any fail (CI-friendly).
- Unit tests covering happy path + each violation rule + batch behavior.

**Out of scope (per REQUIREMENTS.md):**
- The actual voice sample recordings (operator-action handoff — v15.0 delivers protocol + validator, NOT the recordings themselves).
- DUB-06 real-time TTS streaming (v16+ scope).
- DUB-07 per-line emotion/speed/volume fine control (v16+ scope).
- DUB-08 cross-shot voice_identity dimension in continuity_auditor (v16+ scope).
- SKILL.md body changes (L1-L6 read-only invariant reverts post-v14.0 — not touched in this phase).
- Voice sample quality assessment (MOS, WER) — validator checks technical requirements only, not audio quality. Operator reviews quality manually.

**Cross-repo topology:** protocol doc + validator script + tests in kais-hermes-skills repo; planning artifacts in hermes-agent repo. Cross-repo pin recorded at milestone close.

</domain>

<decisions>
## Implementation Decisions

### Protocol Doc & File Organization
- Protocol doc location: `skills/movie-experts/audio_pipeline/references/voicer/voice-sample-collection-protocol.md` — alongside `cosyvoice-benchmark.md` + `cosyvoice-deployment.md` + `indextts2-to-cosyvoice-migration.md`. Co-located with other DUB refs.
- Validator script location: `skills/movie-experts/audio_pipeline/scripts/validate_voice_clone_batch.py` — alongside `run_cosyvoice_benchmark.py` + `gold-team-tts-batch.py`. Co-located with other audio scripts.
- File naming convention enforcement: validator checks wav files regardless of path (just validates technical requirements). Protocol doc documents the `assets/<episode>/voice_refs/<character>.wav` convention. Validator extracts character name from filename stem (e.g. `alice.wav` → `alice`).
- Episode + character extraction: character from filename stem; episode from parent dir name (if parent dir matches `voice_refs`, grandparent is episode). Best-effort extraction — validator works even if path doesn't match convention (character always extracted from filename; episode may be `null` if path doesn't match expected structure).

### Validator I/O & Rules
- `--voice-refs-dir` input format: directory of .wav files (flat) OR directory with per-episode subdirs containing .wav files. Validator recursively finds all `.wav` files via `pathlib.Path.rglob("*.wav")`. Flexible — operator can point at `voice_refs/` or at `assets/`.
- WAV header reading: **stdlib `wave` module** — no external dependencies. Reads `nchannels` / `sampwidth` / `framerate` / `nframes` from WAV header. Duration = `nframes / framerate`. If `wave.open()` fails (corrupt header or non-WAV file with .wav extension), mark as WAV format violation.
- Validation rules: **4 hard rules per success criterion:**
  1. **duration** — 3.0s ≤ duration ≤ 10.0s (computed as `nframes / framerate`)
  2. **format** — WAV format (RIFF header readable by `wave` module)
  3. **sample_rate** — `framerate >= 16000` Hz
  4. **channels** — `nchannels == 1` (mono)
  Hardcoded — no config needed. Each rule has a `rule_id`, `expected`, `actual` field for structured violation reporting.
- Exit code: **0 if all pass, non-zero (1) if any fail.** CI-friendly — operator can gate pipeline ingestion on exit code. Validator always produces full report regardless of exit code. Exit code 2 only on crash (e.g. `--voice-refs-dir` doesn't exist).

### Report Schema & Batch Behavior
- Report schema: `{metadata, characters[], summary}`:
  - `metadata`: `{timestamp, voice_refs_dir, total_files, tool_version}`
  - `characters[]`: per-character `{character, episode, path, passed, duration_s, sample_rate_hz, channels, violations[]}`. `violations[]` lists each violated rule with `{rule_id, expected, actual, message}`.
  - `summary`: `{total, passed, failed, by_rule_violation_count}`. `by_rule_violation_count` is a dict mapping rule_id → count (e.g. `{"duration": 2, "sample_rate": 1, "channels": 0, "format": 0}`).
- Output format: JSON report to `runs/voice-clone-validation/{YYYYMMDD-HHMMSS}/report.json` + Rich table to terminal. Matches Phase 77/78/79 pattern. Operator can review JSON later.
- Batch behavior: **validate ALL files even if some fail.** Partial results are useful for operator (see which characters need re-recording). Never stop on first failure.
- Per-character violation details: `violations[]` lists each violated rule with `rule_id` + `expected` + `actual` + `message`. E.g. `{rule_id: "duration", expected: "3-10s", actual: "2.1s", message: "duration 2.1s below minimum 3.0s"}`. Enables targeted re-recording.

### Claude's Discretion
- **Protocol doc structure:** Follow `cosyvoice-benchmark.md` structure (template style). Sections: `## Collection Guidelines` (3-10s clean recording, environment requirements — quiet room, no background noise, no echo, microphone distance), `## File Naming Convention` (`assets/<episode>/voice_refs/<character>.wav`), `## Technical Requirements` (4 rules with exact thresholds), `## Troubleshooting` (common issues — too short, stereo instead of mono, low sample rate, background noise), `## Validator Usage` (link to `validate_voice_clone_batch.py` with example invocation).
- **WAV header reading robustness:** `wave.open()` raises `wave.Error` on corrupt/non-WAV files. Catch `wave.Error` + mark as format violation (don't crash the validator). Also catch `OSError` (file not readable) + mark as format violation. Other exceptions (e.g. `FileNotFoundError`) → mark as format violation with message.
- **Rich table format:** Per-character rows with columns: Character | Episode | Duration | Sample Rate | Channels | Status. Color: green for pass, red for fail. Summary table at bottom: total/passed/failed + per-rule violation counts.
- **Episode extraction logic:** `episode = path.parent.name if path.parent.name == "voice_refs" else path.parent.parent.name if path.parent.parent.name == "voice_refs" else None`. If path doesn't match `voice_refs/<character>.wav` or `<episode>/voice_refs/<character>.wav`, episode is `None` but validation still runs.
- **Tests:** Mock wav files using `tempfile.NamedTemporaryFile` + `wave` module to write valid/invalid wav files. Test cases: (a) valid wav passes all 4 rules; (b) too short (< 3s) fails duration; (c) too long (> 10s) fails duration; (d) stereo (2 channels) fails channels; (e) low sample rate (8kHz) fails sample_rate; (f) non-WAV file (e.g. mp3 renamed to .wav) fails format; (g) corrupt WAV header fails format; (h) empty directory produces empty report with exit 0; (h) mixed pass/fail batch — exit code 1 + full report.
- **CLI ergonomics:** `--help` follows Phase 77/78/79 argparse style. `--voice-refs-dir` required flag. `--output-dir` optional (default `runs/voice-clone-validation/{ts}/`). `--verbose` flag for per-file details (default: summary only).
- **Error handling:** If `--voice-refs-dir` doesn't exist, fail fast with clear error + exit 2. If directory exists but has no .wav files, produce empty report + exit 0 (not an error — operator may have pointed at wrong dir, but that's their decision). If individual file read fails, mark as format violation + continue.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`** (Phase 77 output) — Pydantic v2 report schema + Rich summary table + argparse + `build_comfyui_workflow()` pattern. Direct template for validator script structure.
- **`skills/movie-experts/audio_pipeline/scripts/gold-team-tts-batch.py`** — existing TTS batch script. Audio file iteration + naming pattern reference.
- **`skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md`** — existing ref doc structure. Template for protocol doc.
- **`skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md`** — line 64 documents `assets/<episode>/voice_refs/<character>.wav` convention (DUB-03 operator-action handoff).
- **`skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json`** — line 34 references `voice_refs/<character>.wav` as the LoadAudio input. Confirms the convention.
- **`skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py`** (Phase 72 output) — tests the `character_bible.json` `voice_clone_reference_wav` JSON field, NOT actual wav file validation. Phase 80 validator is complementary — it validates the actual wav files that the JSON field points to.

### Established Patterns
- **Pydantic v2 BaseModel** for report schema — `dreamina_stats.DreaminaTaskMetrics` + Phase 77 `BenchmarkReport` + Phase 78 `ValidationReport` + Phase 79 `CalibrationReport` precedent.
- **stdlib `wave` module** for WAV header reading — no external dependencies. Already used by Python stdlib, no pip install needed.
- **`pathlib.Path.rglob()`** for recursive file finding.
- **Rich table for CLI output** — Phase 77/78/79 `emit_rich_summary()` pattern.
- **`encoding="utf-8"`** on every `open()` call (Ruff PLW1514).
- **`from __future__ import annotations`** at module top.
- **Sync-only execution** — no GLM calls, no async needed. Pure stdlib validation.
- **Atomic file write** — temp file + `os.replace()` for JSON report (mirrors Phase 78/79 pattern).

### Integration Points
- **`assets/<episode>/voice_refs/<character>.wav`** — canonical voice sample path convention (per `indextts2-to-cosyvoice-migration.md` + `cosyvoice-comfyui.json`). Validator validates files at this path (or any path operator points to).
- **`character_bible.json` → `voice_clone_reference_wav`** — existing JSON field (Phase 72) that points to the wav file path. Phase 80 validator validates the actual wav files that this field references. Complementary — Phase 72 tests the JSON field exists; Phase 80 validates the file the field points to.
- **`cosyvoice-comfyui.json` workflow** — Phase 77 runner uses `voice_refs/<character>.wav` as LoadAudio input. Phase 80 validator ensures these files meet technical requirements before pipeline ingestion.

</code_context>

<specifics>
## Specific Ideas

- **Single-script design (no operator_decision needed):** Unlike Phase 77/78/79 which have a 2-script pattern (runner + lock/verdict/apply), Phase 80 is a single validator script. Validation is a pass/fail check, not an operator decision — no "lock" or "apply" step. Operator runs validator, reviews failures, re-records samples, re-runs validator until all pass. Simple loop.
- **Exit code 1 on any failure (CI-friendly):** Operator can wire `validate_voice_clone_batch.py` into pre-pipeline CI: `python scripts/validate_voice_clone_batch.py --voice-refs-dir assets/ep-001/voice_refs/ && python scripts/run_cosyvoice_benchmark.py ...`. Pipeline only runs if validation passes.
- **Best-effort episode/character extraction:** Validator doesn't enforce the `assets/<episode>/voice_refs/<character>.wav` path structure — it extracts character from filename + episode from parent dir if possible. This means validator works even if operator has a different directory structure (e.g. `voice_samples/alice.wav` → character=alice, episode=null). Flexible + forgiving.
- **4 hard rules, no config:** The 4 rules (duration 3-10s + WAV + ≥16kHz + mono) are hardcoded per success criterion. No `--min-duration` / `--max-duration` / `--min-sample-rate` flags. If operator needs different thresholds, they edit the script (documented in protocol doc). Keeps CLI simple.
- **Protocol doc is the primary deliverable:** The validator is a tool; the protocol doc is the knowledge. Operator reads the protocol doc FIRST to understand how to source voice samples, THEN runs the validator to check their samples meet the spec. Doc + tool = complete operator-action handoff closure.

</specifics>

<deferred>
## Deferred Ideas

- **DUB-06 real-time TTS streaming** — v16+ scope (race-condition architecture needed; current sync model sufficient).
- **DUB-07 per-line emotion/speed/volume fine control** — v16+ scope (CosyVoice `instruct2` fine-grained control).
- **DUB-08 cross-shot voice_identity dimension in continuity_auditor** — v16+ scope (5th dimension).
- **Audio quality assessment (MOS, WER)** — validator checks technical requirements only, not audio quality. Operator reviews quality manually. Automated quality assessment is v16+ scope if pattern emerges.
- **Voice sample format conversion** — validator doesn't convert stereo→mono or resample 8kHz→16kHz. Operator re-records with correct settings. Conversion tool is v16+ scope if needed.
- **Batch re-recording workflow** — validator identifies failures but doesn't automate re-recording. Operator re-records manually per protocol doc. v16+ scope for workflow automation.
- **Per-character threshold customization** — all characters use same 4 rules. Per-character thresholds (e.g. longer samples for main characters) are v16+ scope.
- **Integration with character_bible.json** — validator doesn't read `character_bible.json` to know which characters should have voice samples. Operator points validator at a directory. v16+ scope for character_bible-aware validation.

</deferred>
