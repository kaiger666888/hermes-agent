---
phase: 72-dub
reviewed: 2026-07-09T19:55:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py
  - /data/workspace/kais-hermes-skills/plugins/pipeline_state/dub_validators.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_dub_division.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p10_unit.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/conftest.py
  - /data/workspace/kais-hermes-skills/VERSION.json
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md
findings:
  critical: 2
  warning: 9
  info: 6
  total: 17
status: issues_found
---

# Phase 72: Code Review Report

**Reviewed:** 2026-07-09T19:55:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Phase 72 (DUB) delivers the TTS engine division rule (DUB-02), CosyVoice clone fail-fast (DUB-03), IndexTTS2 DEPRECATED demotion (DUB-04), and the AIIA CosyVoice workflow + ref docs. The structural pieces are sound: `validate_tts_engine_division` correctly enforces the strict enum + both-on rejection; `validate_voice_clone_ref` correctly validates duration/sample-rate/format with a safe ordering (sample_rate ≤ 0 checked before division); the XCUT-02 dual injection (`.task(steps=)` + `.constraints()`) is present in both p04 and p10; MAX_CONSTRAINTS=7 budget is preserved (p10 has 6 constraints); the ref docs are properly templated with `<operator fills>` placeholders.

However, the review surfaced **2 BLOCKER correctness bugs** and **9 WARNINGs**:

1. **CRITICAL:** `generate_tts()` in `tts_batch.py` silently discards the DUB-03 fail-fast gate by falling through to the gold-team API path after `validate_voice_clone_ref()` succeeds — the TODO stub at line 123 explicitly says "fall through to the existing gold-team path", which means CosyVoice clone mode **never actually clones**. The workflow submission is unimplemented; today every `tts_engine='cosyvoice'` call routes to the generic Qwen3-TTS / CosyVoice-300M gold-team endpoint that **ignores `voice_clone_ref` entirely**. This is a data-correctness bug masquerading as a TODO — production runs will produce non-cloned audio while the pipeline reports success with `tts_engine='cosyvoice'`.
2. **CRITICAL:** Module-level mutable globals `_last_tts_engine_used` / `_last_deprecated_fallback` in `tts_batch.py` create a **race condition** when `main()` is later parallelized (or any concurrent caller invokes `generate_tts()`). The "DUB-04 progress metadata" feature these globals enable is inherently thread-unsafe; the test `test_progress_metadata_records_engine` passes only because tests run single-threaded.

The 9 WARNINGs cover: 4 Ruff PLW1514 `open()` violations in `tts_batch.py` (CLAUDE.md mandates `encoding="utf-8"`); missing `__init__.py` in `audio_pipeline/tests/` (breaks pytest collection under some import modes); a JSON-injection vector in `probe-tts-routing.sh` (printf with unescaped `$TEXT`); workflow JSON uses `PreviewAudio` instead of `SaveAudio` (config requirement #4 explicitly asked for `SaveAudio`); and several robustness gaps in the validators.

## Critical Issues

### CR-01: `generate_tts(tts_engine='cosyvoice')` silently falls through to gold-team path — clone mode never executes

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py:112-128`
**Issue:** After `validate_voice_clone_ref(voice_clone_ref)` passes at line 122, the code hits a `TODO(72-02)` stub at line 123 and **falls through** to the unchanged gold-team API path at lines 151-193. That gold-team path uses `VOICE_MAP[character]` + Qwen3-TTS payload (line 154-166) and **completely ignores `voice_clone_ref`**. The result: every `tts_engine='cosyvoice'` invocation produces generic preset-voice audio (CosyVoice-300M default routing), NOT zero-shot cloned audio. The pipeline then records `_last_tts_engine_used = "cosyvoice"` (line 128) and `success=True` — the operator sees "cosyvoice" in the progress metadata and believes cloning happened.

This defeats the entire DUB-03 contract: the fail-fast gate at lines 113-122 enforces that a reference wav EXISTS and is VALID, but the subsequent code path **never uses it**. The TODO comment at line 123-127 admits Plan 72-02 wires the actual workflow, but until 72-02 ships, the feature is a no-op that reports false success.

The config explicitly asked the reviewer to check "is the fallback code path reachable today?" — **yes, it is the ONLY reachable code path for cosyvoice today**, and it does not clone.

**Fix:** Either (a) raise `NotImplementedError` after validation until 72-02 ships (honest "not yet implemented" rather than silent wrong-voice audio), or (b) actually submit the `cosyvoice-comfyui.json` workflow via ComfyUI `/prompt` API as the TODO promises. Option (a) is the minimal correct fix:
```python
if tts_engine == "cosyvoice":
    if not voice_clone_ref:
        raise ValueError(
            f"voice_clone_reference_wav missing for character_id={character}. "
            f"Operator action: provide 3-10s clean sample at "
            f"assets/voice_refs/{character}.wav. See DUB phase operator-action "
            f"checklist. (DUB-03)"
        )
    from plugins.pipeline_state.dub_validators import validate_voice_clone_ref
    validate_voice_clone_ref(voice_clone_ref)  # raises on invalid format/duration/sr
    # BLOCKER (CR-01): workflow submission NOT YET WIRED (Plan 72-02 Task 1+2).
    # Raise rather than silently fall through to gold-team — that path ignores
    # voice_clone_ref and produces non-cloned audio, violating DUB-03.
    raise NotImplementedError(
        f"generate_tts(tts_engine='cosyvoice'): ComfyUI AIIA_CosyVoice_TTS workflow "
        f"submission not yet implemented (Plan 72-02). voice_clone_ref={voice_clone_ref} "
        f"validated but cannot be used. Operator action: wait for 72-02 OR use "
        f"tts_engine='indextts2_fallback' (DEPRECATED) for now."
    )
```

### CR-02: Module-level mutable globals `_last_tts_engine_used` / `_last_deprecated_fallback` are thread-unsafe

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py:47-48, 108-109, 128-129, 139-140, 243-244`
**Issue:** `_last_tts_engine_used` and `_last_deprecated_fallback` are module-level globals mutated inside `generate_tts()` (lines 108-109, 128-129, 139-140) and read by `main()` at lines 243-244 to stamp progress metadata. If two `generate_tts()` calls overlap (which they will once the pipeline parallelizes TTS per-shot — the codebase already has `MAX_CONCURRENT_GL` / `parallel_shots` infra in `pipeline/ratelimit.py` per SKILL.md:471-483), the second call overwrites the globals before the first call's `main()` loop reads them, producing **cross-contaminated progress metadata**: shot A's progress entry records shot B's `tts_engine`. The DUB-04 dashboard visibility feature this mechanism enables is therefore unreliable under any concurrency.

The existing test `test_progress_metadata_records_engine` passes only because pytest runs `generate_tts()` single-threaded with no overlapping calls; it does not exercise the race.

**Fix:** Return the metadata from `generate_tts()` instead of mutating globals. Change the return shape from `(success: bool, info: int|str)` to `(success: bool, info: int|str, metadata: dict)`:
```python
def generate_tts(text, character, output_path, *, tts_engine=DEFAULT_TTS_ENGINE,
                 voice_clone_ref=None, character_bible_entry=None):
    """...Returns: (success, info, metadata) where metadata={'tts_engine': str, 'deprecated_fallback': bool}."""
    metadata = {"tts_engine": None, "deprecated_fallback": False}
    if tts_engine == "ltx_native":
        _emit_silent_marker(output_path)
        metadata["tts_engine"] = "ltx_native"
        return True, 0, metadata
    # ... etc; main() then reads metadata locally per-iteration:
    # success, info, meta = generate_tts(...)
    # progress["completed"][line_id] = {..., "tts_engine": meta["tts_engine"], ...}
```
This eliminates the globals entirely and is concurrency-safe.

## Warnings

### WR-01: 4× `open()` without `encoding="utf-8"` — violates Ruff PLW1514 (load-bearing rule)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py:201, 211, 253, 256`
**Issue:** CLAUDE.md "Code Style" mandates `encoding="utf-8"` on every text-mode `open()` (Ruff PLW1514 is the single load-bearing lint rule; CI blocks merge). Four violations in `main()`:
- Line 201: `with open(TTS_LINES_PATH) as f:` (reads `tts_lines.json` — contains Chinese dialogue)
- Line 211: `with open(TTS_PROGRESS) as f:` (reads `tts_progress.json` — contains Chinese character names)
- Line 253: `with open(TTS_PROGRESS, "w") as f:` (writes progress with Chinese)
- Line 256: `with open(TTS_PROGRESS, "w") as f:` (writes progress with Chinese)

On Windows (cp1252 default) these silently corrupt non-ASCII JSON. The codebase's entire i18n story depends on this rule.

**Fix:**
```python
with open(TTS_LINES_PATH, encoding="utf-8") as f:
    lines = json.load(f)
# ... and for each progress write:
with open(TTS_PROGRESS, "w", encoding="utf-8") as f:
    json.dump(progress, f, indent=2, ensure_ascii=False)
```
Also consider adding `ensure_ascii=False` to the `json.dump` at lines 254, 257 (currently absent — produces `\uXXXX` escapes for Chinese, inflating file size and hurting debuggability).

### WR-02: `audio_pipeline/tests/` directory missing `__init__.py` — inconsistent with sibling test dirs

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/` (directory)
**Issue:** The sibling test directory `kais-movie-pipeline/tests/__init__.py` exists (verified via `ls`), but `audio_pipeline/tests/` has only `conftest.py` + `test_voice_clone_ref.py` — no `__init__.py`. Under pytest's default `rootdir` import mode, the missing `__init__.py` can cause "module not found" errors when tests are collected from the repo root (the `conftest.py` sys.path bootstrap at line 25 compensates for the deeper nesting, but `__init__.py` is still needed for pytest to treat the directory as a package under some invocation modes). This is an asymmetry that will bite when CI adds `audio_pipeline` to the test suite.

**Fix:** Add an empty `__init__.py` to `skills/movie-experts/audio_pipeline/tests/` mirroring the `kais-movie-pipeline/tests/__init__.py` convention.

### WR-03: `probe-tts-routing.sh` line 102 — JSON injection via unescaped `$TEXT` in printf

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh:100-103`
**Issue:** The submit-task curl builds its JSON payload via:
```bash
-d "$(printf '{"task_id":"%s","type":"%s","params":{"text":"%s","voice":"%s"}}' \
      "$TASK_ID" "$TASK_TYPE" "$TEXT" "$VOICE")"
```
`printf` does not JSON-escape. If `$TEXT` contains a double-quote (`"`), backslash (`\`), or control character, the resulting JSON is malformed and the gold-team `/api/v1/tasks` endpoint returns 400. The script then continues to poll for a task that was never accepted, eventually printing "Final task: status: ?". Not shell injection (printf does not execute backticks/`$()` in its format args after expansion — confirmed), but JSON-injection breakage. An operator probing with `bash probe-tts-routing.sh 'He said "hi"'` gets a confusing silent failure.

**Fix:** Use `jq` to construct the JSON safely, or python3 (already a dependency elsewhere in the script):
```bash
PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({'task_id': sys.argv[1], 'type': sys.argv[2],
                  'params': {'text': sys.argv[3], 'voice': sys.argv[4]}}))
" "$TASK_ID" "$TASK_TYPE" "$TEXT" "$VOICE")
curl -s -m 10 -X POST "$API/api/v1/tasks" -H 'Content-Type: application/json' -d "$PAYLOAD"
```

### WR-04: Workflow JSON uses `PreviewAudio` instead of `SaveAudio` — does not persist audio to disk

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json:37-42`
**Issue:** The workflow graph ends with a `PreviewAudio` node (line 38), which renders audio inline in the ComfyUI UI but does **not** save a persistent file to `/root/ComfyUI/output/`. The review config requirement #4 explicitly asked for "Loader → TTS → SaveAudio" — the node graph is Loader(3) → TTS(2) → PreviewAudio(4), missing `SaveAudio`. For batch automated submission (the documented use case in `cosyvoice-deployment.md:131-169`), `PreviewAudio` output is not retrievable via the `/history` + `/view?filename=` polling pattern the deployment doc documents. The deployment doc even contradicts itself: line 167 says `audio = nout["audio"][0]; url = f".../view?filename={audio['filename']}"` — but `PreviewAudio` does not populate `outputs[].audio[].filename` the same way `SaveAudio` does.

**Fix:** Replace node "4" class_type `PreviewAudio` with `SaveAudio`:
```json
"4": {
  "class_type": "SaveAudio",
  "inputs": {
    "audio": ["2", 0],
    "filename_prefix": "cosyvoice_tts"
  }
}
```
Verify against the live AIIA node registry via `curl -s http://127.0.0.1:8188/object_info/SaveAudio`.

### WR-05: `validate_voice_clone_ref` does not check `nchannels==1` despite docstring claiming "mono"

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/dub_validators.py:48-87` and `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py:76`
**Issue:** The DUB-03 contract as documented in p04_character_design.py:76 says the wav must be "mono, >=16kHz". The docstring of `validate_voice_clone_ref` (lines 30-31) lists "Duration in [3.0, 10.0] seconds" and "Sample rate >= 16000 Hz" but does NOT list mono. The implementation reads `n_frames` and `sample_rate` but never calls `wf.getnchannels()` — a stereo wav passes validation, then may produce unexpected results when CosyVoice's `reference_audio` input receives a 2-channel file. The fixture `tmp_wav_factory` defaults `channels=1` but accepts `channels=2` as a parameter — the test suite has no negative test for stereo rejection (because the validator doesn't reject it).

Either (a) drop "mono" from the p04 instruction text and DUB-03 docstring (if CosyVoice accepts stereo), or (b) add a mono check. The current state is internally inconsistent.

**Fix (option b — add the check):**
```python
n_channels = wf.getnchannels()
# ...
if n_channels != 1:
    raise ValueError(
        f"voice_clone_reference_wav at {path} must be mono (1 channel), "
        f"got {n_channels} channels. (DUB-03 — CosyVoice reference must be mono)"
    )
```

### WR-06: `validate_voice_clone_ref` accepts >10s wavs but no upper bound on file size / frame count

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/dub_validators.py:74-78`
**Issue:** The validator enforces `3.0 <= duration <= 10.0` but a 10s wav at 192kHz stereo is ~7.6MB; a malicious or buggy upstream could craft a wav with `n_frames=999999999, sample_rate=16000` reporting duration≈62500s (correctly rejected), but the inverse — a 10s wav with a malformed `sample_rate=1` frame count — would pass the duration check only if `n_frames` is correspondingly small. More importantly, there is no `n_frames` ceiling: a 10s@48kHz wav is fine, but the validator does not reject a 10s@192kHz wav (1.92M frames). Not a security issue per se (operator-sourced), but it would let a poorly-downsampled reference through.

**Fix:** Consider adding `if sample_rate > 48000: raise ValueError(...)` or normalizing the message to "16kHz–48kHz expected".

### WR-07: `validate_tts_engine_division` silently skips non-dict shots — masks data corruption

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py:174-178`
**Issue:** The validator's "defensive" branch:
```python
if not isinstance(shot, dict):
    # Silently skip non-dict entries.
    continue
```
silently skips malformed entries. The comment claims "validator must not crash on malformed input" but the consequence is that a shot_list like `[{"shot_id": "s1", ...}, "garbage", {"shot_id": "s3", "tts_engine": "cosyvoice", "ltx_native_dialogue": True}]` would **skip both** the garbage entry AND never validate s3's both-on violation if the iteration breaks early (it doesn't break here, but the pattern of silently skipping is suspect). More concretely: a shot_list containing `None` (common JSON-decode artifact for missing entries) is silently accepted — the pipeline proceeds and may crash later with a less actionable error.

The strict-enum philosophy of DUB-02 (no fuzzy matching, no warnings-and-continue) is undercut by this silent skip.

**Fix:** Either reject non-dict entries explicitly, or log a warning:
```python
if not isinstance(shot, dict):
    logger.warning(
        "validate_tts_engine_division: skipping non-dict shot entry %r "
        "(possible asset-bus corruption)", shot
    )
    continue
```

### WR-08: `tts_batch.py` `main()` swallows all exceptions from `generate_tts()` — masks CR-01

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py:192-193`
**Issue:** The broad `except Exception as e: return False, str(e)` at lines 192-193 catches every error from the gold-team HTTP path. Once CR-01 is fixed by raising `NotImplementedError` for cosyvoice, that NotImplementedError will be caught here, recorded as `progress["failed"]` with message "NotImplementedError(...)", and the pipeline continues to the next line. The operator sees a generic "failed" entry without the DUB-03-specific operator-action text. The `generate_tts` docstring promises DUB-03 fail-fast with operator-action guidance — that guidance is swallowed by this broad except.

**Fix:** Narrow the except or re-raise on specific DUB exceptions:
```python
except (ValueError, NotImplementedError) as dub_exc:
    raise  # DUB-03 fail-fast + CR-01 NotImplemented must propagate, not be swallowed
except Exception as e:
    return False, str(e)
```

### WR-09: `_drive_p10_dub` test helper — `script_draft` factory parameter unused in assertions

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p10_unit.py:250-269`
**Issue:** The `_drive_p10_dub` helper accepts a `script_draft` parameter (line 259) and threads it through `asset_bus_read`, but no test in the Phase 72-02 block (lines 272-345) ever passes a custom `script_draft` or asserts on its content. The existing assertion at line 288 (`"MUST propagate tts_engine" in captured["goal"]`) checks only the goal string, not that `script_draft` made it into the context. This leaves a coverage gap: if `p10.run()` ever stops threading `script_draft` into the goal/context (regression), the 72-02 tests still pass.

Minor — the older Test 1 (`test_p10_reads_shot_list_and_script_draft_slots`, line 85) does cover this, but not in the 72-02 DUB-specific test class.

**Fix:** Add one assertion in `test_p10_goal_includes_tts_engine_instruction` verifying `script_draft` content reached the goal:
```python
assert "b1" in captured["context"] or "narration" in captured["context"], \
    "script_draft content must reach the expert context"
```

## Info

### IN-01: `tts_batch.py` line 26 — overly broad import (`import json, os, sys, re, time, requests, base64, logging, wave, struct, math`)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py:26`
**Issue:** Single-line multi-import violates PEP 8 and CLAUDE.md "no `from x import *`" guidance (not strictly the same rule, but the spirit of explicit-imports applies). Also imports `time`, `math` that appear unused in the file.

**Fix:** Split into separate lines; drop unused `time` and `math` (verify via `grep -n 'time\.\|math\.' tts_batch.py`).

### IN-02: `test_dub_division.py:308-315` — constraint-counting test subtracts empty placeholder but counts ALL bullets

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p10_unit.py:308-315`
**Issue:** The `test_p10_constraints_within_budget` test counts bullets via `line.strip().startswith("- ")` then subtracts empty `fix_feedback` placeholder via `line.strip() != "-"`. But an empty `fix_feedback` string still renders as `- ` (dash-space), not `-` (bare dash), so the `!= "-"` check never matches and the subtraction never happens. The test still passes because the count is 6 ≤ 7 even without subtracting, but the test's stated intent ("Subtract empty fix_feedback placeholder if present") does not actually execute.

**Fix:** Change the empty-bullet check to `line.strip() not in ("-", "- ")` or just `line.strip("- ").strip() != ""`.

### IN-03: `cosyvoice-comfyui.json` — `tts_text` placeholder `<your Chinese dialogue>` is an inline placeholder, not `<operator fills>`

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json:20`
**Issue:** The `tts_text` value is `"<your Chinese dialogue>"` — inconsistent with the `<operator fills>` convention used elsewhere in the phase (e.g., `cosyvoice-benchmark.md`). Minor style inconsistency, but a grep for `<operator fills>` will miss this placeholder.

**Fix:** Standardize to `"<operator fills: Chinese dialogue text>"` for grep-ability, or document the `<your X>` convention as a distinct category.

### IN-04: `VERSION.json` line 4 — `_comment` key is non-standard for JSON

**File:** `/data/workspace/kais-hermes-skills/VERSION.json:4`
**Issue:** JSON does not support comments; the `_comment` key is a convention but `json5` or `jsonc` parsers may treat it differently. The leading underscore is a reasonable disambiguator. Minor — no action required unless downstream consumers reject unknown keys.

**Fix:** No change needed; the `_meta` block in `cosyvoice-comfyui.json:2-8` shows the preferred richer-metadata pattern. Consider migrating `VERSION.json` to a `_meta` block for consistency.

### IN-05: `p04_character_design.py:166-167` — `ch_id` truncation can produce duplicate IDs

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py:166-167`
**Issue:** `ch_id = ch_name.replace(" ", "_").replace("/", "_")[:30]` truncates to 30 chars. Two characters with names sharing the first 30 chars (e.g., "守护者·星渊纪·第一形态" and "守护者·星渊纪·第二形态") would collide on `p04/char-守护者_星渊纪_第一形态` (truncated). Pre-existing code, not Phase 72-introduced, but the `_VOICE_CLONE_INSTRUCTION` injection at line 119 increases the stakes (colliding IDs now mean colliding voice-ref paths).

**Fix:** Hash-suffix on collision, or include the full name in the ID (canvas can handle long labels).

### IN-06: `validate_tts_engine_division` — `sid` fallback to `"<unknown>"` makes error messages hard to trace

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py:179`
**Issue:** When a shot lacks `shot_id`, errors say "Shot `<unknown>`". For a shot_list of 50+ entries, the operator cannot identify which shot triggered the violation. Minor UX issue.

**Fix:** Include the shot index: `sid = shot.get("shot_id") or f"<index {i}>"` (requires `enumerate`).

---

_Reviewed: 2026-07-09T19:55:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
