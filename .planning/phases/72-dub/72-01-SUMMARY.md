---
phase: 72-dub
plan: 01
subsystem: dub (TTS / voice layer)
tags: [dub, tts, cosyvoice, indextts2, voice-clone, division-rule, schema-validation, dub-02, dub-03, dub-04, dub-01]
requires: [p71-form (form_factor precedent for standalone validator pattern)]
provides:
  - validate_tts_engine_division() standalone function (DUB-02 contract)
  - TTS_ENGINE_VALUES frozenset enum {ltx_native, cosyvoice, indextts2_fallback}
  - validate_voice_clone_ref() helper (DUB-03 3-10s / >=16kHz / wav rules)
  - Shot dict tts_engine + ltx_native_dialogue field conventions (.get() backward-compat)
  - character_bible V3 envelope voice_clone_reference_wav sibling field (additive)
  - _VOICE_CLONE_INSTRUCTION constant in p04 (XCUT-02 injection)
  - generate_tts() tts_engine routing (ltx_native/cosyvoice/indextts2_fallback)
  - DUB-04 DEPRECATED warning + deprecated_fallback progress metadata field
affects:
  - Plan 72-02 (routing wire-up: workflow JSON submission + healthcheck fallback)
  - Plan 72-03 (docs: cosyvoice-deployment.md + VERSION.json + benchmark template)
  - Phase 75 LINEAGE-BUMP (p04_character_design.py SKILL.md-adjacent code changed)
tech-stack:
  added: []  # zero new packages — stdlib wave/struct/math only
  patterns:
    - plain-dict standalone validator (mirrors validate_form_factor_invariant store.py:111-140)
    - TDD RED→GREEN per task (failing test commits precede implementation commits)
    - keyword-only args on generate_tts() for backward-compatible signature extension
    - module-level _last_tts_engine_used hook for testability + progress metadata
key-files:
  created:
    - kais-hermes-skills/plugins/pipeline_state/dub_validators.py
    - kais-hermes-skills/skills/kais-movie-pipeline/tests/test_dub_division.py
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/conftest.py
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py
  modified:
    - kais-hermes-skills/plugins/pipeline_state/store.py
    - kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py
    - kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py
decisions:
  - "Standalone function validate_tts_engine_division (NOT @model_validator) — Shot is plain dict per RESEARCH Critical Correction #3"
  - "tts_engine defaults to 'cosyvoice' per CONTEXT D-01 (CosyVoice primary); ltx_native_dialogue defaults False"
  - "voice_clone_reference_wav as sibling to 4d_anchor.voice (additive; .get() returns None for old bibles)"
  - "Fail-fast ValueError on missing voice_clone_ref when CosyVoice clone mode selected (NO silent fallback)"
  - "DEPRECATED warning visible in progress metadata (deprecated_fallback bool) — NOT log-warning-only per CONTEXT"
  - "ltx_native emits silent marker wav for DUB-02 slot consistency (voice-clips slot MUST have entry)"
metrics:
  duration: ~6min
  completed: 2026-07-09
  tasks: 3
  files_created: 4
  files_modified: 3
  tests_added: 15
  commits: 8 (4 RED test + 3 GREEN impl + 1 Rule-3 fix)
---

# Phase 72 Plan 01: DUB Foundation — Division Rule + Voice Clone Schema + Routing Summary

DUB-02 schema-enforced TTS engine division rule (validate_tts_engine_division standalone function preventing PITFALL D-1 doubled audio) + DUB-03 voice_clone_reference_wav V3 envelope schema extension with validate_voice_clone_ref helper (3-10s / >=16kHz / wav / exists fail-fast) + DUB-04 IndexTTS2 DEPRECATED fallback code path with progress metadata visibility.

## What Was Built

### Task 1: DUB-02 division rule validator (commits bc2f041, 26ad6d8)

**`plugins/pipeline_state/store.py`** — Added `TTS_ENGINE_VALUES = frozenset({"ltx_native", "cosyvoice", "indextts2_fallback"})` + `validate_tts_engine_division(shot_list)` standalone function. The validator iterates a list of plain-dict shots, reads `tts_engine` (default `"cosyvoice"`) and `ltx_native_dialogue` (default `False`) via `.get()`, and raises `ValueError` on:
- Unknown `tts_engine` enum value (T-72-01 tampering mitigation, strict no-fuzzy-matching)
- `ltx_native_dialogue=True` AND `tts_engine != "ltx_native"` (PITFALL D-1 doubled-audio BLOCKER)

Pattern mirrors the existing `validate_form_factor_invariant(state)` at store.py:111-140 — standalone function, NOT `@model_validator`, because Shot is a plain dict (not a Pydantic model) per RESEARCH Critical Correction #3. Non-dict items in shot_list are silently skipped (defensive against malformed input per CONTEXT.md).

**`skills/kais-movie-pipeline/tests/test_dub_division.py`** — 6 unit tests covering: reject-both-on, allow-ltx-native-only, allow-cosyvoice-only, allow-indextts2-fallback, allow-both-off-defaults, reject-invalid-enum. Uses `_shot(sid, **kw)` factory with `tts_engine='cosyvoice'` default. All pass under 0.04s, no network.

### Task 2: DUB-03 voice_clone_reference_wav schema + validation (commits 2c31d0d, 662ccda)

**`plugins/pipeline_state/dub_validators.py`** (NEW) — `validate_voice_clone_ref(path) -> tuple[float, int]` helper using stdlib `wave` module (zero new deps per CLAUDE.md). Enforces DUB-03 rules: file exists (FileNotFoundError with "Operator action" suffix), wav format (ValueError on `wave.Error`), duration in [3.0, 10.0]s, sample_rate >= 16000Hz. Returns `(duration_sec, sample_rate_hz)` on success. Error messages include `(DUB-03 — ...)` suffix for grep-auditable traceability.

**`skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py`** — Two changes:
1. `_VOICE_CLONE_INSTRUCTION` constant added after `_FOUR_D_INSTRUCTION` (line 72), injected into `.task(steps=[...])` as the 6th step per XCUT-02 META-RULE X-2 (subagents see ONLY the goal string, not SKILL.md).
2. `.schema(shape=...)` f-string extended: `4d_anchor{identity,arc,voice,visual,voice_clone_reference_wav (str|None — ...)}` — additive field, old bibles load cleanly via `.get()` returning None.

**`skills/movie-experts/audio_pipeline/tests/conftest.py`** (NEW) — `tmp_wav_factory` fixture: `(duration_sec, sample_rate_hz, channels=1) -> Path`. Generates real wav via stdlib `wave` + `struct` + `math` (numpy-free 220Hz sine at 30% amplitude, 16-bit signed PCM). sys.path bootstrap reaches repo root for `plugins/` imports.

**`skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py`** (NEW) — 5 unit tests: accepts_valid (5s@16kHz → (5.0, 16000)), rejects_missing (FileNotFoundError matching "Operator action"), rejects_short (<3s ValueError matching "3-10s"), rejects_low_sr (<16kHz ValueError matching "16kHz"), character_bible_field_additive (pre-v14 bible loads cleanly).

### Task 3: tts_batch routing + DUB-03 fail-fast + DUB-04 DEPRECATED (commits f4d4f51, d59df89)

**`skills/kais-movie-pipeline/templates/tts_batch.py`** — Three extensions:
1. `DEFAULT_TTS_ENGINE = "cosyvoice"` module constant + `logger = logging.getLogger(__name__)`.
2. `generate_tts()` signature extended with keyword-only `tts_engine=DEFAULT_TTS_ENGINE, voice_clone_ref=None, character_bible_entry=None` (positional callers backward-compatible per CLAUDE.md Function Design).
3. Routing branches:
   - `ltx_native`: `_emit_silent_marker(output_path)` writes 1-frame silent wav, return `(True, 0)` — DUB-02 slot consistency.
   - `cosyvoice`: fail-fast `ValueError` on missing `voice_clone_ref` (DUB-03, NO silent fallback), then `validate_voice_clone_ref()` gate, then `# TODO(72-02): submit cosyvoice-comfyui.json workflow` — the fail-fast gate is the Plan 72-01 deliverable; workflow submission is Plan 72-02 Task 1.
   - `indextts2_fallback`: `logger.warning("DEPRECATED: ... (DUB-04)")` (lazy %-formatting per CLAUDE.md Logging), proceed with existing gold-team path.
4. `_last_tts_engine_used` + `_last_deprecated_fallback` module-level hooks for testability + downstream progress metadata.
5. `main()` `progress["completed"][line_id]` gains `tts_engine` + `deprecated_fallback` keys (DUB-04 dashboard visibility — NOT log-warning-only per CONTEXT.md).

**`test_dub_division.py`** extended with 4 new tests: cosyvoice_fail_fast_missing_ref, indextts2_fallback_logs_deprecated (caplog WARNING), progress_metadata_records_engine (_last_tts_engine_used == "indextts2_fallback"), ltx_native_emits_silent_marker (output_path exists). Uses `_FakeResponse` class + monkeypatch `requests.post`/`requests.get` for network-free testing (D-35-08 isolation).

## Commits (kais-hermes-skills repo)

| Hash | Message | Task | Phase |
|------|---------|------|-------|
| 26ad6d8 | test(72-01): add failing DUB-02 division rule tests | 1 | RED |
| bc2f041 | feat(72-01): implement validate_tts_engine_division (DUB-02) | 1 | GREEN |
| 662ccda | test(72-01): add failing DUB-03 voice_clone_ref validation tests | 2 | RED |
| 2c31d0d | feat(72-01): implement validate_voice_clone_ref + extend p04 schema (DUB-03) | 2 | GREEN |
| d59df89 | test(72-01): add failing DUB-03/DUB-04 tts_batch routing tests | 3 | RED |
| f4d4f51 | feat(72-01): tts_batch tts_engine routing + DUB-03 fail-fast + DUB-04 DEPRECATED | 3 | GREEN |
| 4d1f907 | fix(72-01): remove audio_pipeline/tests/__init__.py (pytest namespace collision) | 3 | Rule 3 fix |

**kais-hermes-skills HEAD:** `5772f55` (P71 baseline) → `4d1f907` (Plan 72-01 complete)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Removed audio_pipeline/tests/__init__.py to fix pytest namespace collision**
- **Found during:** Plan-level verification (running both test files together)
- **Issue:** Both `kais-movie-pipeline/tests/__init__.py` and `audio_pipeline/tests/__init__.py` exist, creating two `tests` packages. Pytest raises `_pytest.pathlib.ImportPathMismatchError` when collecting both test files in one session.
- **Fix:** Removed the empty `audio_pipeline/tests/__init__.py`. pytest discovers test modules via `conftest.py` without needing `__init__.py`. The plan specified creating this file, but the plan didn't account for the naming collision.
- **Files modified:** `kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/__init__.py` (deleted)
- **Commit:** 4d1f907

### Advisory Warning Accepted (DUB-04 generation-failure fallback)

**Warning #1 (from plan critical_context):** DUB-04 generation-failure auto-fallback path leaves a `# TODO(72-02): submit cosyvoice-comfyui.json workflow` stub in `tts_batch.py` for the CosyVoice workflow submission. The fail-fast gate (voice_clone_ref validation) IS implemented in Plan 72-01. The healthcheck-based fallback (probe ComfyUI `/object_info/AIIA_CosyVoice_TTS` → auto-fallback to IndexTTS2) IS implemented in Plan 72-02 Task 2. This is intentional and documented — Plan 72-01 delivers the contract layer (validator + fail-fast), Plan 72-02 delivers the integration layer (workflow submission + healthcheck).

## TDD Gate Compliance

All 3 tasks followed RED→GREEN per `tdd="true"` frontmatter:

| Task | RED commit | GREEN commit | Gate |
|------|-----------|-------------|------|
| 1 | 26ad6d8 (6 failing tests) | bc2f041 (validator impl) | PASSED |
| 2 | 662ccda (5 failing tests) | 2c31d0d (dub_validators + p04) | PASSED |
| 3 | d59df89 (4 failing tests) | f4d4f51 (tts_batch routing) | PASSED |

**Fail-fast rule honored:** RED tests failed with ImportError/TypeError BEFORE implementation (verified at each phase). No test passed unexpectedly during RED.

## Known Stubs

| File | Line | Stub | Reason | Resolution |
|------|------|------|--------|------------|
| `templates/tts_batch.py` | ~155 | `# TODO(72-02): submit cosyvoice-comfyui.json workflow` | Plan 72-01 delivers the fail-fast gate (voice_clone_ref validation); workflow submission + healthcheck-based fallback IS Plan 72-02 Task 1+2 | Plan 72-02 wires the ComfyUI AIIA_CosyVoice_TTS workflow JSON submission + `/object_info` healthcheck auto-fallback |

This stub does NOT prevent the plan's goal from being achieved — the fail-fast contract IS delivered (the gate raises ValueError before reaching the stub). The stub is in the post-validation code path which Plan 72-02 completes.

## Test Results

```
skills/kais-movie-pipeline/tests/test_dub_division.py: 10 passed (0.11s)
skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py: 5 passed (1.24s)
Total: 15 passed (1.34s combined)
```

No regression: `test_form_factor.py` 5/5 still green.

## Self-Check: PASSED

**Files exist:**
- FOUND: kais-hermes-skills/plugins/pipeline_state/dub_validators.py
- FOUND: kais-hermes-skills/skills/kais-movie-pipeline/tests/test_dub_division.py
- FOUND: kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/conftest.py
- FOUND: kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py

**Commits exist (kais-hermes-skills repo):**
- FOUND: 26ad6d8 (test RED Task 1)
- FOUND: bc2f041 (feat GREEN Task 1)
- FOUND: 662ccda (test RED Task 2)
- FOUND: 2c31d0d (feat GREEN Task 2)
- FOUND: d59df89 (test RED Task 3)
- FOUND: f4d4f51 (feat GREEN Task 3)
- FOUND: 4d1f907 (fix Rule 3 namespace collision)
