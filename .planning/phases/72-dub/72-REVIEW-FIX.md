---
phase: 72-dub
fixed_at: 2026-07-09T20:45:00Z
review_path: .planning/phases/72-dub/72-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
status: all_fixed
---

# Phase 72: Code Review Fix Report

**Fixed at:** 2026-07-09T20:45:00Z
**Source review:** `.planning/phases/72-dub/72-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 11 (2 critical + 9 warnings; 6 info findings out of scope per `fix_scope: critical_warning`)
- Fixed: 11
- Skipped: 0

**Cross-repo topology:** All 11 fix commits live in the `kais-hermes-skills` repo on branch `gsd-reviewfix/72-1367301` (worktree `/tmp/sv-72-reviewfix-reyNMi`), fast-forwarded to `master` during cleanup. Commit hashes referenced below are from that repo. REVIEW-FIX.md itself commits in `hermes-agent` via the orchestrator.

**Verification:** All 31 DUB-related tests pass after the full fix sweep:
- `skills/kais-movie-pipeline/tests/test_dub_division.py` — 11 tests (was 10, +1 WR-07)
- `skills/kais-movie-pipeline/tests/test_p10_unit.py` — 13 tests (WR-09 adds assertion)
- `skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py` — 7 tests (was 5, +1 WR-05, +1 WR-06)

## Fixed Issues

### CR-01: `generate_tts(tts_engine='cosyvoice')` silently falls through to gold-team path — clone mode never executes

**Files modified:** `skills/kais-movie-pipeline/templates/tts_batch.py`
**Commit:** `e6154f3` (kais-hermes-skills)
**Applied fix:** Replaced the `TODO(72-02)` fall-through comment + silent routing to the gold-team path with an explicit `raise NotImplementedError(...)` after `validate_voice_clone_ref()` succeeds. Callers now get an honest "ComfyUI AIIA_CosyVoice_TTS workflow submission not yet implemented (Plan 72-02)" error instead of silent wrong-voice audio while `_last_tts_engine_used='cosyvoice'` reported false success. The `_last_tts_engine_used` / `_last_deprecated_fallback` mutations are kept BEFORE the raise so any except clause that catches the NotImplementedError still sees the metadata (superseded by CR-02 which removed the globals entirely). Option (a) from REVIEW.md applied as recommended — the actual ComfyUI workflow submission is deferred to Plan 72-02 execution.

### CR-02: Module-level mutable globals `_last_tts_engine_used` / `_last_deprecated_fallback` are thread-unsafe

**Files modified:** `skills/kais-movie-pipeline/templates/tts_batch.py`, `skills/kais-movie-pipeline/tests/test_dub_division.py`
**Commit:** `68475ea` (kais-hermes-skills)
**Applied fix:** Removed the module-level globals `_last_tts_engine_used` and `_last_deprecated_fallback`. Refactored `generate_tts()` return shape from `(success, info)` to `(success, info, metadata)` where `metadata = {'tts_engine': str|None, 'deprecated_fallback': bool}` is built per-call as a local dict (concurrency-safe — no shared mutable state). Updated `main()` to unpack the third element and read `meta['tts_engine']` / `meta['deprecated_fallback']` locally per-iteration. Updated 3 test call sites in `test_dub_division.py`: `test_indextts2_fallback_logs_deprecated` (unpack `_meta`), `test_progress_metadata_records_engine` (assert on returned dict instead of module globals — the meat of the contract change), `test_ltx_native_emits_silent_marker` (unpack `meta`, assert engine/deprecated fields). Left an explanatory comment at the old globals site documenting why they were removed. Status: fixed (requires human verification — semantic refactor; all 10 DUB tests pass but logic-bug limitation applies per verification_strategy).

### WR-01: 4× `open()` without `encoding="utf-8"` — violates Ruff PLW1514

**Files modified:** `skills/kais-movie-pipeline/templates/tts_batch.py`
**Commit:** `8fb0f20` (kais-hermes-skills)
**Applied fix:** Added `encoding="utf-8"` to all 4 text-mode `open()` calls in `main()`:
- line 214: `open(TTS_LINES_PATH, encoding="utf-8")` (reads `tts_lines.json` — Chinese dialogue)
- line 224: `open(TTS_PROGRESS, encoding="utf-8")` (reads `tts_progress.json` — Chinese character names)
- lines 266, 269: `open(TTS_PROGRESS, "w", encoding="utf-8")` (writes progress with Chinese)

Also added `ensure_ascii=False` to the two `json.dump` calls per REVIEW.md suggestion — currently Chinese characters inflate file size with `\uXXXX` escapes and hurt debuggability. Verified no remaining text-mode `open()` without encoding in the file.

### WR-02: `audio_pipeline/tests/` directory missing `__init__.py`

**Files modified:** `skills/movie-experts/audio_pipeline/tests/__init__.py` (new file)
**Commit:** `e8bea1f` (kais-hermes-skills)
**Applied fix:** Created `skills/movie-experts/audio_pipeline/tests/__init__.py` with a single-line docstring package marker, mirroring the `kais-movie-pipeline/tests/__init__.py` convention (`"""Test package marker for kais-movie-pipeline tests (Phase 35-05)."""`). Under pytest's default rootdir import mode, the missing `__init__.py` could cause "module not found" errors when tests are collected from the repo root — the `conftest.py` sys.path bootstrap compensated for the deeper nesting but `__init__.py` was still needed for pytest to treat the directory as a package under some invocation modes.

### WR-03: `probe-tts-routing.sh` line 102 — JSON injection via unescaped `$TEXT` in printf

**Files modified:** `skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh`
**Commit:** `81b9e4f` (kais-hermes-skills)
**Applied fix:** Replaced the `printf` JSON construction with `python3 -c "import json, sys; print(json.dumps({...}, ensure_ascii=False))"`. `python3` is already a dependency at lines 39-47 and 64-73 for ComfyUI `object_info` parsing. Verified with adversarial input `'He said "hi" and back\slash'` — the python builder correctly escapes quotes and backslashes, whereas the previous printf would have produced malformed JSON causing a 400 from `/api/v1/tasks` and a confusing silent polling failure. `ensure_ascii=False` preserves Chinese characters in the payload.

### WR-04: Workflow JSON uses `PreviewAudio` instead of `SaveAudio` — does not persist audio to disk

**Files modified:** `skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json`
**Commit:** `6b00902` (kais-hermes-skills)
**Applied fix:** Replaced node "4" `class_type: PreviewAudio` with `class_type: SaveAudio` and added `filename_prefix: "cosyvoice_tts"` (SaveAudio requires this input; ComfyUI default is "audio" but an explicit prefix aids downstream filename grep-ability). Verified JSON parses and node 4 is SaveAudio with the expected filename_prefix. The deployment doc at `cosyvoice-deployment.md:167` previously contradicted itself by polling `/view?filename=...` against a PreviewAudio node that doesn't populate `outputs[].audio[].filename` — SaveAudio fixes this. Operator action: verify against the live AIIA node registry via `curl -s http://127.0.0.1:8188/object_info/SaveAudio` (deferred — node availability is runtime-dependent).

### WR-05: `validate_voice_clone_ref` does not check `nchannels==1` despite docstring claiming "mono"

**Files modified:** `plugins/pipeline_state/dub_validators.py`, `skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py`
**Commit:** `53e77f1` (kais-hermes-skills)
**Applied fix:** Applied option (b) from REVIEW.md (add mono check). Added `wf.getnchannels()` call inside the existing `with contextlib.closing(wave.open(...))` block, plus a new `if n_channels != 1: raise ValueError(...)` check with message suffix `(DUB-03 — CosyVoice reference_audio expects mono per p04:76)`. Updated docstring acceptance rules + Raises clause to mention mono. Added negative test `test_voice_clone_ref_rejects_stereo` using `tmp_wav_factory(channels=2)`. All 6 test_voice_clone_ref tests pass (5 existing using default channels=1 + 1 new). The p04:76 instruction text "mono, >=16kHz" is now internally consistent with the validator.

### WR-06: `validate_voice_clone_ref` accepts >10s wavs but no upper bound on file size / frame count

**Files modified:** `plugins/pipeline_state/dub_validators.py`, `skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py`
**Commit:** `b8a7f66` (kais-hermes-skills)
**Applied fix:** Added upper bound: `if sample_rate > 48000: raise ValueError(...)` with message suffix `(DUB-03 — downsample to <=48kHz before submitting; CosyVoice resamples internally anyway)`. Tightened both sample_rate error messages to `[16kHz, 48kHz]` range form (was `>=16kHz`). Added negative test `test_voice_clone_ref_rejects_high_sr` using `tmp_wav_factory(sample_rate_hz=192000)`. All 7 test_voice_clone_ref tests pass. The existing `test_voice_clone_ref_rejects_low_sr` `match="16kHz"` still matches the new message text.

### WR-07: `validate_tts_engine_division` silently skips non-dict shots — masks data corruption

**Files modified:** `plugins/pipeline_state/store.py`, `skills/kais-movie-pipeline/tests/test_dub_division.py`
**Commit:** `491bea1` (kais-hermes-skills)
**Applied fix:** Replaced the silent `continue` for non-dict shot entries with an explicit `raise ValueError(...)` containing the shot index: `shot_list[N] is not a dict (got NoneType: None). Possible asset-bus corruption — every shot entry must be a dict...`. Switched the loop to `enumerate(shot_list)` so error messages can reference the index. Also addressed IN-06 (sid fallback now `f"<index {i}>"` instead of `"<unknown>"` for traceability when shot_id is absent). Added `test_division_rejects_non_dict_shot` covering both `None` and string entries. All 11 test_dub_division tests pass (10 existing + 1 new). The strict-enum philosophy of DUB-02 (no fuzzy matching, no warnings-and-continue) is no longer undercut by silent skip.

### WR-08: `tts_batch.py` broad `except Exception` swallows DUB-03 fail-fast errors

**Files modified:** `skills/kais-movie-pipeline/templates/tts_batch.py`
**Commit:** `e324b06` (kais-hermes-skills)
**Applied fix:** Added an explicit `except (ValueError, NotImplementedError): raise` BEFORE the broad `except Exception` around the gold-team HTTP path in `generate_tts()`. Today CR-01's `NotImplementedError` and DUB-03's `ValueError` are raised BEFORE entering the try block so they propagate regardless, but future code changes (e.g. 72-02 wiring the ComfyUI workflow submission inside the try block) could silently regress this. The broad catch remains for genuine HTTP/transport errors (`requests.HTTPError`, `ConnectionError`, `Timeout`, `JSONDecodeError`) which should be recorded as "failed" and the batch continued. All 11 test_dub_division tests still pass.

### WR-09: `_drive_p10_dub` test helper — `script_draft` factory parameter unused in assertions

**Files modified:** `skills/kais-movie-pipeline/tests/test_p10_unit.py`
**Commit:** `398eaec` (kais-hermes-skills)
**Applied fix:** Added an assertion to `test_p10_goal_includes_tts_engine_instruction` verifying `script_draft` content reaches the delegate context: `combined = captured["goal"] + captured["context"]; assert "beats" in combined or "b1" in combined or "narration" in combined`. Closes the coverage gap where a regression in `p10.run()` stopping the script_draft threading would go undetected by the 72-02 DUB test class. Mirrors the assertion pattern from the older `test_p10_reads_shot_list_and_script_draft_slots` (Test 1, line 85-106) but applied to the 72-02 DUB-specific test class. All 13 test_p10_unit tests still pass.

---

_Fixed: 2026-07-09T20:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
