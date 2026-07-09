# Phase 72: DUB - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 13 (5 Plan A code/schema/tests + 4 Plan B routing/deprecated + 4 Plan C docs/VERSION.json)
**Analogs found:** 12 / 13 (1 with no analog: VERSION.json is greenfield schema, no prior top-level repo meta)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `kais-hermes-skills/plugins/pipeline_state/store.py` (MODIFY: +2 Shot fields via docstring + +1 validator function) | model/validator | CRUD | `store.py:111 validate_form_factor_invariant` (Phase 71 precedent) | exact |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/character_bible_schema.py` or inline in p04 (VERIFY location; if no schema module, patch is in p04 goal schema) | config/schema | request-response | `p04_character_design.py:112 schema shape` (declares `4d_anchor{identity,arc,voice,visual}`) | exact (inline) |
| `kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py` (MODIFY: +tts_engine routing + +voice_clone_reference_wav fail-fast) | utility/script | request-response | same file (current `VOICE_MAP` + `generate_tts()` path at lines 33-82) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_dub_division.py` (NEW) | test | request-response | `tests/test_p09_unit.py:56-63 _make_delegate_spy` + `test_form_factor.py` (Phase 71) | exact |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py` (NEW) | test | file-I/O | `tests/test_p10b_unit.py` + stdlib `wave` header round-trip (greenfield wav fixture) | role-match |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json` (NEW) | config/workflow | file-I/O | `references/comfyui-indextts2-setup.md:33-50` (IndexTTS2 workflow JSON block) | exact |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh` (MODIFY: +ComfyUI AIIA CosyVoice healthcheck block) | utility/probe | request-response | same file (current gold-team log-tail + status poll at lines 32-75) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` line 457 (MODIFY: IndexTTS2 → CosyVoice primary + IndexTTS2 DEPRECATED fallback) | documentation/skill-body | request-response | `SKILL.md:433` (authoritative source rule) + `cn-tts-model-matrix.md:8` (phantom strip pattern) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py` (MODIFY: +`_TTS_ENGINE_INSTRUCTION` constant + inject into .task + .constraints + pre-flight validator call) | service/orchestration | event-driven | `p09_shot_breakdown.py:80 _FORM_FACTOR_INSTRUCTION` + `p04_character_design.py:48-70 _GROWTH_CHAIN/_SCENE_FITTING/_FOUR_D` | exact |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md` (NEW) | reference-doc | file-I/O | `references/comfyui-indextts2-setup.md` (176-line 9-step install pattern) | exact-twin |
| `kais-hermes-skills/VERSION.json` (NEW top-level) | config/meta | file-I/O | (none — greenfield; no prior top-level VERSION.json in repo) | no-analog |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md` (NEW) | reference-doc | file-I/O | `references/voicer/cn-tts-model-matrix.md` (provider capability matrix structure) | role-match |
| `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md` (NEW) | reference-doc | request-response | `references/voicer/gold-team-tts-api.md:124` (CosyVoice-300M auto-route note) | role-match |
| `.planning/phases/72-dub/72-smoke.sh` (NEW) | test/smoke | request-response | `.planning/phases/70-foundation-audit/70-smoke.sh` (80-line skeleton) | exact |

## Pattern Assignments

### `plugins/pipeline_state/store.py` (model/validator, CRUD — +1 validator function)

**Analog:** `validate_form_factor_invariant` at `store.py:111-140` (Phase 71 precedent — exact pattern to mirror)

**Imports pattern** (lines 29-37 — current, UNCHANGED):
```python
from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal
```
Plan A's validator function uses only `typing` + stdlib; no new imports needed at the module level (function body uses only what's already there).

**Validator function pattern to mirror** (`store.py:111-140`):
```python
def validate_form_factor_invariant(state: PipelineState) -> bool:
    """Reject per-shot ``form_factor`` overrides in ``state.phases``.
    ...docstring with rationale + invariant explanation...
    Returns ``True`` if the invariant holds ..., ``False`` if ...
    """
    def _scan(obj) -> bool:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "form_factor":
                    return False
                if not _scan(v):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not _scan(item):
                    return False
        return True

    return _scan(state.phases)
```

**Plan A adds `validate_tts_engine_division`** (sibling function, placed AFTER `validate_form_factor_invariant` at approximately line 141):

```python
TTS_ENGINE_VALUES = frozenset({"ltx_native", "cosyvoice", "indextts2_fallback"})


def validate_tts_engine_division(shot_list: list[dict]) -> None:
    """Reject shots that violate the DUB-02 division rule.

    Per PITFALL D-1 (BLOCKER): if BOTH LTX 2.3 native dialogue AND CosyVoice
    overlay fire for the same shot, the result is doubled audio / phase
    cancellation / lip-sync mismatch. This validator enforces the rule at
    pre-flight time (called from p10_voice.run() before any TTS submission).

    Each shot dict MAY declare:
      - ``tts_engine``: Literal["ltx_native", "cosyvoice", "indextts2_fallback"]
        (defaults to ``"cosyvoice"`` per CONTEXT.md D-01 when absent)
      - ``ltx_native_dialogue``: bool (defaults ``False``; explicit operator
        opt-in per RESEARCH Critical Correction — no existing implicit flag)

    Raises:
        ValueError: if any shot has conflicting flags or an invalid enum value.
    """
    for shot in shot_list:
        if not isinstance(shot, dict):
            continue
        sid = shot.get("shot_id", "<unknown>")
        tts_engine = shot.get("tts_engine", "cosyvoice")
        ltx_native = shot.get("ltx_native_dialogue", False)

        if tts_engine not in TTS_ENGINE_VALUES:
            raise ValueError(
                f"Shot {sid}: tts_engine must be one of "
                f"{sorted(TTS_ENGINE_VALUES)}, got {tts_engine!r} "
                f"(DUB-02 strict enum — no fuzzy matching, no warnings-and-continue)."
            )

        # Consistency: ltx_native_dialogue=True implies tts_engine="ltx_native".
        # Forbids the doubled-audio state where both fire.
        if ltx_native and tts_engine != "ltx_native":
            raise ValueError(
                f"Shot {sid}: cannot enable both ltx_native_dialogue=True AND "
                f"tts_engine={tts_engine!r} (DUB-02 / PITFALL D-1 — doubled "
                f"audio / phase cancellation / lip-sync mismatch). "
                f"Set tts_engine='ltx_native' OR ltx_native_dialogue=False."
            )
```

**Key mirroring decisions:**
1. **Standalone function, NOT `@model_validator`** — Shot is a plain dict (RESEARCH Critical Correction #3); the existing `validate_form_factor_invariant` is the established precedent.
2. **Raises `ValueError`** — matches CONTEXT.md locked decision (strict reject, no fuzzy matching) and the form_factor `__post_init__` ValueError pattern at `store.py:90-94`.
3. **Module-level `TTS_ENGINE_VALUES = frozenset(...)`** — matches the `_STATIC_MOVES = frozenset({...})` pattern at `p09_shot_breakdown.py:238` and `_STATE_FIELDS` at `store.py:108`.
4. **SHOT-level (not PipelineState-level)** — `tts_engine` is per-shot inside the `shot-list` asset-bus slot; NOT added as a PipelineState dataclass field (per RESEARCH §Runtime State Inventory).

**Backward-compat behavior:** old shot-lists without `tts_engine`/`ltx_native_dialogue` keys load cleanly via `.get(..., default)` — zero migration script. This mirrors how `PipelineState.form_factor` defaults to `"portrait"` for old state files.

---

### `character_bible_schema.py` (config/schema, request-response — +1 sibling field)

**Reality check:** RESEARCH verified NO standalone schema module exists; the `4d_anchor` shape is declared inline in `p04_character_design.py:112` schema f-string:
```python
.schema(shape={
    "character_bible": "{characters: [{name, role, archetype (enum: ...), age_range (enum: ...), 4d_anchor{identity,arc,voice,visual}, style_prefix}]}",
    ...
})
```

**Live envelope structure verified** (`formc-test-01/.pipeline-assets/character-bible.json`):
```json
{
  "value": { "characters": [{ ..., "4d_anchor": {"identity":..., "arc":..., "voice": "<free-text str>", "visual":...}, "style_prefix": ...}] },
  "derived_from": "p04_character_design",
  "content_hash": "...",
  "schema_version": 3.0
}
```

**Plan A edit direction** (two-site patch):

1. **`p04_character_design.py:112` schema f-string** — extend `4d_anchor` sub-keys to include the new field:
```python
# Before
"4d_anchor{identity,arc,voice,visual}"
# After
"4d_anchor{identity,arc,voice,visual,voice_clone_reference_wav (str|None — relative path to 3-10s wav at assets/voice_refs/<char>.wav; required for CosyVoice clone mode per DUB-03)}"
```

2. **Add a sibling `_VOICE_CLONE_INSTRUCTION` constant** near `_FOUR_D_INSTRUCTION` (`p04_character_design.py:48-70`):
```python
_VOICE_CLONE_INSTRUCTION = (
    "VOICE CLONE REFERENCE (DUB-03 — optional but mandatory when downstream P10 uses CosyVoice clone mode): "
    "If the character will be voiced via CosyVoice zero-shot clone, declare a relative path "
    "`voice_clone_reference_wav` as a SIBLING to `4d_anchor.voice`. Path must resolve to a 3-10s "
    "clean wav (mono, >=16kHz) at assets/voice_refs/<character>.wav. Set to null if not yet available; "
    "p10 will fail-fast at TTS submission time (not silently fall back to generic voice)."
)
```
Inject via `.task(steps=[f"{_VOICE_CLONE_INSTRUCTION}", ...])` per the XCUT-02 META-RULE X-2 pattern (see Shared Patterns below).

**Backward-compat:** existing character-bibles without the field load cleanly via `.get("4d_anchor", {}).get("voice_clone_reference_wav")` returning `None`. Schema bump from `3.0` → `3.1` is optional (additive); operators may leave at `3.0` since no consumer hard-rejects on version.

---

### `templates/tts_batch.py` (utility/script, request-response — +tts_engine routing)

**Analog:** same file (`tts_batch.py:33-82` current IndexTTS2/Qwen3-TTS path)

**Current routing pattern** (lines 33-44):
```python
VOICE_MAP = {
    "Kael": {"spk": "Alex", "instruction": "..."},
    ...
}

def generate_tts(text, character, output_path):
    """Generate TTS via gold-team API."""
    voice = VOICE_MAP.get(character, VOICE_MAP["narrator"])
    payload = {"task_type": "tts_zh", "payload": {...}}
    ...
```

**Plan A adds (after line 32):**
```python
# Per-shot TTS engine routing (DUB-01 / DUB-02). Default "cosyvoice".
# Valid values: "ltx_native" (skip TTS, LTX prompt carries dialogue),
# "cosyvoice" (submit ComfyUI AIIA_CosyVoice_TTS workflow), "indextts2_fallback"
# (DEPRECATED; auto-triggered on CosyVoice failure per DUB-04).
DEFAULT_TTS_ENGINE = "cosyvoice"
```

**Plan A adds to `generate_tts()` signature + routing** (mirror existing return shape `tuple[bool, str|int]`):
```python
def generate_tts(text, character, output_path, tts_engine="cosyvoice",
                 voice_clone_ref=None, character_bible_entry=None):
    """Generate TTS via gold-team API or ComfyUI AIIA CosyVoice per tts_engine."""
    if tts_engine == "ltx_native":
        # LTX prompt carries dialogue; emit a marker silent wav so downstream
        # asset-bus consumers see a slot entry. (DUB-02 consistency.)
        _emit_silent_marker(output_path)
        return True, 0
    if tts_engine == "cosyvoice":
        if not voice_clone_ref:
            raise ValueError(
                f"voice_clone_reference_wav missing for character_id={character}. "
                f"Operator action: provide 3-10s clean sample at "
                f"assets/voice_refs/{character}.wav. See DUB phase operator-action checklist."
            )
        from plugins.pipeline_state.dub_validators import validate_voice_clone_ref
        validate_voice_clone_ref(voice_clone_ref)  # raises on invalid format/duration/sr
        # ... submit ComfyUI AIIA_CosyVoice_TTS workflow ...
    elif tts_engine == "indextts2_fallback":
        logger.warning(
            "DEPRECATED: IndexTTS2 fallback fired for character=%s. "
            "CosyVoice primary unavailable or operator override. (DUB-04)",
            character,
        )
        # ... existing IndexTTS2 path (unchanged) ...
```

**DEPRECATED warning visibility (DUB-04 locked decision):** Plan A must ALSO write a `tts_engine_used` + `deprecated_fallback: bool` into the per-clip metadata slot so downstream dashboards surface it. Mirror the existing `progress["completed"][line_id] = {"path":..., "character":..., "size_kb":...}` pattern at `tts_batch.py:130-132`:
```python
progress["completed"][line_id] = {
    "path": output_path, "character": char, "size_kb": info // 1024,
    "tts_engine": tts_engine_used,  # NEW DUB-04
    "deprecated_fallback": tts_engine_used == "indextts2_fallback",  # NEW DUB-04
}
```

**Don't hand-roll:** silent-output detection, duration matching via ffmpeg atempo/trim/apad, and the gold-team retry-on-trailing-punctuation pattern are ALL already implemented in `scripts/gold-team-tts-batch.py:74-110, 144-167`. Plan A's CosyVoice path reuses those helpers if it routes through gold-team :8002 (which already defaults to CosyVoice-300M per RESEARCH).

---

### `tests/test_dub_division.py` (test, request-response — NEW)

**Analog 1:** `tests/test_p09_unit.py:56-63` (`_make_delegate_spy` + captured["goal"] assertion)
**Analog 2:** `tests/conftest.py:104-111` (`tmp_state_store` fixture for PipelineState round-trip)
**Analog 3:** `tests/test_form_factor.py` (Phase 71 strict-enum precedent — direct sibling)

**sys.path bootstrap pattern** (test_p09_unit.py:27-29):
```python
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))
```

**Delegate spy + goal-content assertion pattern** (test_p09_unit.py:56-63, 159-184):
```python
def _make_delegate_spy(captured: dict):
    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}
    return _mock

def test_p09_goal_includes_cross_cutting_injection_instruction():
    captured: dict = {}
    p09.run(..., delegate_task=_make_delegate_spy(captured), ...)
    assert "CROSS-CUTTING PARAMETER INJECTION" in captured["goal"]
    assert "character_refs" in captured["goal"]
```

**Plan A test_dub_division.py — division rule tests** (5 tests mapping to RESEARCH §Phase Requirements → Test Map):

```python
import pytest
from plugins.pipeline_state.store import (
    validate_tts_engine_division, TTS_ENGINE_VALUES,
)

def _shot(sid, **kw):
    base = {"shot_id": sid, "tts_engine": "cosyvoice"}
    base.update(kw)
    return base

def test_division_rejects_both_on():
    # ltx_native_dialogue=True AND tts_engine != "ltx_native" → ValueError
    with pytest.raises(ValueError, match="DUB-02"):
        validate_tts_engine_division([_shot("s1", tts_engine="cosyvoice", ltx_native_dialogue=True)])

def test_division_allows_ltx_native_only():
    validate_tts_engine_division([_shot("s1", tts_engine="ltx_native", ltx_native_dialogue=True)])

def test_division_allows_cosyvoice_only():
    validate_tts_engine_division([_shot("s1", tts_engine="cosyvoice", ltx_native_dialogue=False)])

def test_division_allows_both_off():
    # Both-off = silence/SFX only (no tts_engine, no ltx_native — defaults are compatible)
    validate_tts_engine_division([{"shot_id": "s1"}])  # no keys → defaults apply

def test_division_rejects_invalid_tts_engine():
    with pytest.raises(ValueError, match="strict enum"):
        validate_tts_engine_division([_shot("s1", tts_engine="azure")])
```

**XCUT-02 goal injection test** (1 test — mirrors `test_p09_goal_includes_cross_cutting_injection_instruction`):
```python
def test_p10_goal_includes_tts_engine_instruction():
    captured: dict = {}
    p10.run(
        episode_id="ep-dub",
        asset_bus_read=lambda slot: [{"shot_id": "s1"}] if slot == "shot-list" else ({"beat":"x"} if slot == "script-draft" else None),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "TTS ENGINE ROUTING" in captured["goal"]
    assert "tts_engine" in captured["goal"]
    assert "MUST propagate tts_engine" in captured["goal"]
```

**DUB-04 DEPRECATED fallback logging test** (1 test):
```python
import logging

def test_indextts2_fallback_logs_deprecated(caplog):
    # drive tts_batch.generate_tts(tts_engine="indextts2_fallback") and assert
    # a WARNING-level log with "DEPRECATED" text was emitted
    with caplog.at_level(logging.WARNING):
        generate_tts("test", "Kael", "/tmp/x.wav", tts_engine="indextts2_fallback")
    assert any("DEPRECATED" in r.message and "DUB-04" in r.message for r in caplog.records)
```

**Total: 7 unit tests in `test_dub_division.py`.** All run under 2s; no Docker, no network (pure function tests).

---

### `tests/test_voice_clone_ref.py` (test, file-I/O — NEW)

**Analog:** `tests/test_p10b_unit.py` (existing p10 test convention — READ at execution time for fixture pattern) + stdlib `wave` round-trip.

**Conftest fixture extension** (add to `conftest.py` after `tmp_state_store` at line 111):
```python
@pytest.fixture
def tmp_wav_factory(tmp_path):
    """Return a factory ``(duration_sec, sample_rate_hz, channels=1) -> Path``
    that generates a real wav file via stdlib wave + a numpy-free sine wave
    (or ffmpeg lavfi sine source for non-stdlib fallback). Used by
    test_voice_clone_ref for DUB-03 validation tests."""
    import math
    import struct
    import wave

    def _factory(duration_sec=5.0, sample_rate_hz=16000, channels=1):
        p = tmp_path / f"ref_{duration_sec}s_{sample_rate_hz}hz.wav"
        n_frames = int(duration_sec * sample_rate_hz)
        with wave.open(str(p), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate_hz)
            # numpy-free sine: 220Hz at low amplitude
            for i in range(n_frames):
                sample = int(32767 * 0.3 * math.sin(2 * math.pi * 220 * i / sample_rate_hz))
                wf.writeframes(struct.pack("<h", sample))
        return p

    return _factory
```

**Plan A test_voice_clone_ref.py tests** (4 tests):
```python
def test_voice_clone_ref_accepts_valid(tmp_wav_factory):
    p = tmp_wav_factory(duration_sec=5.0, sample_rate_hz=16000)
    duration, sr = validate_voice_clone_ref(p)
    assert duration == pytest.approx(5.0, abs=0.1)
    assert sr == 16000

def test_voice_clone_ref_rejects_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="Operator action"):
        validate_voice_clone_ref(tmp_path / "nonexistent.wav")

def test_voice_clone_ref_rejects_short(tmp_wav_factory):
    p = tmp_wav_factory(duration_sec=2.0)  # < 3s floor
    with pytest.raises(ValueError, match="3-10s"):
        validate_voice_clone_ref(p)

def test_voice_clone_ref_rejects_low_sr(tmp_wav_factory):
    p = tmp_wav_factory(duration_sec=5.0, sample_rate_hz=8000)  # < 16kHz
    with pytest.raises(ValueError, match="16kHz"):
        validate_voice_clone_ref(p)
```

---

### `references/workflows/cosyvoice-comfyui.json` (config/workflow, file-I/O — NEW)

**Analog:** `comfyui-indextts2-setup.md:33-50` IndexTTS2 workflow JSON block (same AIIA vendor pattern).

**Note:** `references/workflows/` directory does NOT yet exist in `audio_pipeline/`. Plan A creates it as a new subdir (mirrors `references/voicer/` organization).

**IndexTTS2 workflow JSON pattern to mirror** (`comfyui-indextts2-setup.md:33-50`):
```json
{
  "4": {
    "class_type": "AIIA_IndexTTS2_TTS",
    "inputs": {
      "indextts_model": ["6", 0],
      "text": "你的中文文本",
      "voice_preset": "Male_HQ",
      "sad": 0.3, "calm": 0.2, "melancholic": 0.4,
      "use_emo_text": true,
      "seed": 42
    }
  },
  "5": { "class_type": "PreviewAudio", "inputs": { "audio": ["4", 0] } },
  "6": { "class_type": "AIIA_IndexTTS2_Loader", "inputs": { "use_fp16": true, "use_cuda_kernel": true } }
}
```

**Plan A CosyVoice workflow JSON** (per RESEARCH §Code Examples — verified live via `/object_info` 2026-07-09):
```json
{
  "1": {
    "class_type": "AIIA_CosyVoice_ModelLoader",
    "inputs": {
      "model_dir": "/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512",
      "use_fp16": true,
      "use_rl_model": false
    }
  },
  "2": {
    "class_type": "AIIA_CosyVoice_TTS",
    "inputs": {
      "model": ["1", 0],
      "tts_text": "<your Chinese dialogue>",
      "instruct_text": "语速自然，情感饱满。",
      "base_gender": "Female",
      "dialect": "None (Auto)",
      "emotion": "None (Neutral)",
      "speed": 1.0,
      "seed": 42,
      "reference_audio": ["3", 0]
    }
  },
  "3": { "class_type": "LoadAudio", "inputs": { "audio": "voice_refs/<character>.wav" } },
  "4": { "class_type": "PreviewAudio", "inputs": { "audio": ["2", 0] } }
}
```

**CRITICAL:** Plan A uses AIIA nodes (already installed), NOT `filliptm/ComfyUI_FL-CosyVoice3` (NOT installed — RESEARCH Critical Correction #1). Any deviation from this requires explicit operator escalation as scope-expansion.

---

### `scripts/probe-tts-routing.sh` (utility/probe, request-response — +ComfyUI CosyVoice healthcheck)

**Analog:** same file (lines 32-75 — current gold-team task poll + log tail pattern).

**Current pattern** (`probe-tts-routing.sh:30-51`):
```bash
echo "▶ Submitting $TASK_TYPE task: $TASK_ID"
curl -s -m 10 -X POST "$API/api/v1/tasks" \
  -H 'Content-Type: application/json' \
  -d "$(printf '{"task_id":"%s",...}' "$TASK_ID" ...)"
# Tail container log + poll task status up to 60s
docker logs -f --tail 0 kais-gold-team 2>&1 | grep --line-buffered -iE '...' > "$LOG_FILE" &
```

**Plan A adds (prepend as pre-flight section BEFORE the existing gold-team task submission):**
```bash
# === ComfyUI CosyVoice node healthcheck (DUB-01 / DUB-04 fallback gate) ===
COMFY_URL="http://127.0.0.1:8188"
COSY_NODES=$(curl -s -m 5 "$COMFY_URL/object_info" 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    cosy = sorted(k for k in d.keys() if 'CosyVoice' in k)
    print(','.join(cosy) if cosy else 'NONE')
except Exception:
    print('ERROR')
" 2>/dev/null || echo "ERROR")

if [[ "$COSY_NODES" == "NONE" || "$COSY_NODES" == "ERROR" ]]; then
    echo "WARN: ComfyUI CosyVoice nodes NOT available ($COSY_NODES)."
    echo "      Auto-fallback to indextts2_fallback (DEPRECATED per DUB-04)."
    TTS_ENGINE_DEFAULT="indextts2_fallback"
else
    echo "OK: ComfyUI CosyVoice nodes available: $COSY_NODES"
    TTS_ENGINE_DEFAULT="cosyvoice"
fi
echo ""
```

This reuses the existing curl + python3 filter idiom from `probe-tts-routing.sh:46-48` (task-status poll), applied to the ComfyUI `/object_info` endpoint instead of the gold-team task-status endpoint.

---

### `SKILL.md:457` (documentation, request-response — IndexTTS2 demotion)

**Analog:** `cn-tts-model-matrix.md:8` phantom-strip note pattern (de-phantom'ing CosyVoice-300M as the gold-team default).

**Current SKILL.md:457 context** (per RESEARCH §State of the Art table): the line says "Use ComfyUI IndexTTS2" but the gold-team `tts-tracker` already auto-routes `tts_zh` → `CosyVoice-300M`. Plan B must reconcile docs with reality.

**Plan B edit direction** (mirror the authoritative-source rule at SKILL.md:433):
```markdown
<!-- BEFORE -->
**P10 Voice:** Use ComfyUI IndexTTS2 (AIIA_IndexTTS2_TTS node) for TTS generation.

<!-- AFTER -->
**P10 Voice (v14.0 DUB-01):** CosyVoice is the primary TTS engine. Two paths:
1. **ComfyUI AIIA CosyVoice** (`AIIA_CosyVoice_TTS` + `Fun-CosyVoice3-0.5B-2512` model) — SOTA path for in-pipeline synchronous TTS. See `references/comfyui-indextts2-setup.md` sister doc `cosyvoice-deployment.md`.
2. **Gold-team tts-tracker** (`:8002/api/v1/tasks` with `type=tts_zh`) — async batch path; auto-routes to `CosyVoice-300M` by default (per `probe-tts-routing.sh` de-phantom note).

IndexTTS2 (`AIIA_IndexTTS2_TTS`) is **DEPRECATED** (DUB-04). Auto-fallback on CosyVoice failure OR `/object_info` healthcheck fail. Do NOT use as the primary path for new projects.
```

**Frontmatter freeze (FOUND-08):** edit body only; do NOT mutate the YAML frontmatter (`name`, `description`, `tags`, `related_skills`, `expert_id`, `metrics`).

---

### `pipeline/phases/p10_voice.py` (service/orchestration, event-driven — +`_TTS_ENGINE_INSTRUCTION` + pre-flight validator)

**Analog 1 (constant definition):** `p09_shot_breakdown.py:80-89` `_FORM_FACTOR_INSTRUCTION`
**Analog 2 (alternative multi-constant style):** `p04_character_design.py:48-70` three sibling constants
**Analog 3 (runtime validator invocation):** `p09_shot_breakdown.py:439` `_validate_camera_move_diversity(...)` call after delegate returns

**Current p10_voice.py state** (full file = 234 lines, read in full):
- Lines 40-44: phase metadata (`PHASE_ID`, `EXPERT`, `INPUT_SLOTS`, `OUTPUT_SLOTS`, `GATE_ID`)
- Lines 100-170: `GoalBuilder` chain with `.task(steps=[...])` (4 items at 108-113), `.execution_hint(...)`, `.schema(...)`, `.constraints([...])` (5 items at 157-163), `.quality([...])`
- No `_INSTRUCTION` constants currently defined (Phase 72 is the first to add them to p10)

**Plan B adds after line 44** (mirroring `_FORM_FACTOR_INSTRUCTION` placement at `p09:80`):
```python
# ―― TTS engine routing (v14.0 DUB-01 / DUB-02 / XCUT-02 / META-RULE X-2) ――
# Subagents see ONLY the goal string; they do NOT read SKILL.md at runtime.
# Therefore the tts_engine division rule MUST be encoded as a constant and
# injected into .task(steps=[...]) AND .constraints([...]) — both injection
# sites are required for the rule to be enforceable rather than advisory.
_TTS_ENGINE_INSTRUCTION = (
    "TTS ENGINE ROUTING (mandatory — MUST read shot.tts_engine for every shot and route accordingly):\n"
    "1. If tts_engine='ltx_native': SKIP TTS generation. LTX-2.3 video prompt carries dialogue text; "
    "LTXVEmptyLatentAudio fills the audio latent. Emit a silent marker wav so the voice-clips slot is populated.\n"
    "2. If tts_engine='cosyvoice': Submit ComfyUI AIIA_CosyVoice_TTS workflow with reference_audio from "
    "character_bible.characters[].4d_anchor.voice_clone_reference_wav. FAIL FAST if reference is missing "
    "(DUB-03 operator-action handoff — do NOT silently fall back to generic voice).\n"
    "3. If tts_engine='indextts2_fallback': Submit ComfyUI AIIA_IndexTTS2_TTS workflow. Log DEPRECATED "
    "warning (DUB-04). Only reachable via auto-fallback from CosyVoice failure.\n\n"
    "DIVISION RULE (DUB-02 / PITFALL D-1 BLOCKER): NEVER allow both ltx_native dialogue AND cosyvoice overlay "
    "on the same shot — causes doubled audio / phase cancellation / lip-sync mismatch. "
    "validate_tts_engine_division() runs at pre-flight to enforce this."
)
```

**Plan B injects into `.task(steps=[...])`** at line 108-113:
```python
.task(steps=[
    "Load expert via skill_view(name='audio_pipeline')",
    "Generate TTS voice clips for narration + dialogue per shot",
    "Match voice durations to shot-list durations from p09",
    "Produce voice timeline alignment (per-shot start/end timestamps + lip-sync cues)",
    f"{_TTS_ENGINE_INSTRUCTION}",   # NEW Plan B XCUT-02
])
```

**Plan B adds a MUST constraint** at lines 157-163:
```python
.constraints([
    "MUST match shot durations from p09 shot_list",
    "MUST use script-draft text from p03 (no ad-libbing)",
    "Each voice clip MUST have audio_path + duration_sec",
    "MUST output canvas structured fields per clip: audio_type/engine/emotion/speaker",
    "MUST propagate tts_engine selection per shot (ltx_native / cosyvoice / indextts2_fallback)",  # NEW DUB
    fix_feedback,  # empty on first run, fix instructions on retry
])
```

**MAX_CONSTRAINTS=7 budget** — current p10 has 5 constraints (4 + fix_feedback placeholder). Adding 1 brings it to 6. Within budget.

**Plan B pre-flight validator invocation** (insert after line 80 in run(), mirroring `p09_shot_breakdown.py:439` validator-call pattern):
```python
# Pre-flight DUB-02 division rule validation (Plan A function, Plan B wire-up)
from plugins.pipeline_state.store import validate_tts_engine_division
try:
    validate_tts_engine_division(shot_list)
except ValueError as exc:
    # Re-raise with phase context; p10 refuses to run if division rule violated
    raise ValueError(f"p10_voice pre-flight failed: {exc}") from exc
```

---

### `references/voicer/cosyvoice-deployment.md` (reference-doc, file-I/O — NEW)

**Analog (twin):** `references/comfyui-indextts2-setup.md` (176 lines, full 9-step install pattern — exact structural template to mirror).

**Twin section structure to mirror EXACTLY (comfyui-indextts2-setup.md line map):**
| Section | indextts2 line range | cosyvoice Plan A equivalent |
|---------|----------------------|------------------------------|
| Title + Source + Context + Container name | 1-6 | Mirror header block; AIIA package + Fun-CosyVoice3-0.5B-2512 context |
| `## Node Overview` table | 9-17 | AIIA_CosyVoice_TTS / AIIA_CosyVoice_ModelLoader / AIIA_CosyVoice_VoiceConversion |
| `## Voice Presets` | 21-23 | CosyVoice equivalent (base_gender + dialect + emotion + instruct_text + reference_audio) |
| `## Emotion Sliders` | 25-29 | CosyVoice emotion tags + instruct2 control |
| `## Working API-Format Workflow` JSON block | 31-50 | Mirror (use the cosyvoice-comfyui.json content from Plan A) |
| `## Dependency Setup` (9-step fix sequence) | 59-267 | CosyVoice-specific deps (verify in container — RESEARCH says deps already installed for AIIA; document any delta) |
| `## Non-blocking Batch Submission Pattern` | 333-356 | Mirror (python requests + ComfyUI /prompt + /history poll) |
| `## Alternative: Gold-team TTS` | 358-366 | REFINE — gold-team CosyVoice-300M IS operational (de-phantom); document as batch alternative |
| `## Model Location` | 368-371 | `/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512/` |

**Additional CosyVoice-specific sections to ADD (no IndexTTS2 analog):**
- `## GPU VRAM Budget` — document CosyVoice 2.0-0.5B (~1.5GB) vs Fun-CosyVoice3-0.5B-2512 (~2GB actual, ~3GB with RL model) + LTX-MSR ~23GB concurrent budget (PITFALL D-5)
- `## Healthcheck` — `curl -s http://127.0.0.1:8188/object_info/AIIA_CosyVoice_TTS` returns 200 with INPUT_TYPES schema
- `## Known Issues` — silent-output detection on trailing punctuation (link to `gold-team-tts-batch.py:144-167` mitigation); gold-team CosyVoice-300M permission denied issue (historical, per `comfyui-indextts2-setup.md:363`)

---

### `VERSION.json` (config/meta, file-I/O — NEW top-level repo file)

**No analog exists.** RESEARCH confirmed no VERSION.json anywhere in `kais-hermes-skills` repo (verified via find). This is greenfield.

**Plan A schema** (per RESEARCH §Pattern 4 + CONTEXT.md D-05 lock decision):
```json
{
  "schema_version": "1.0",
  "pipeline_version": "v14.0",
  "tts": {
    "cosyvoice_default_variant": "fun_cosyvoice_3.0_0.5B_2512",
    "lock_date": null,
    "lock_rationale": null,
    "alternative_tested": ["cosyvoice_2.0_0.5B", "cosyvoice_300M_gold_team"],
    "benchmark_report_path": "skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md"
  }
}
```

`lock_date` and `lock_rationale` start as `null`; operator fills after DUB-05 A/B benchmark review. This is the operator-action handoff site.

**Convention precedent to follow:** the `cli-config.yaml` + `.env.example` pattern from the parent hermes-agent project — top-level meta files at repo root, documented inline. Plan A adds inline JSON comments (where allowed) or a sibling `VERSION.md` if the schema needs prose explanation (Claude's Discretion per CONTEXT.md).

---

### `references/voicer/cosyvoice-benchmark.md` (reference-doc, file-I/O — NEW template)

**Analog:** `references/voicer/cn-tts-model-matrix.md` (provider capability matrix structure + Last-verified + Copyright header).

**Header block to mirror** (`cn-tts-model-matrix.md:1-7`):
```markdown
# CosyVoice Variant A/B Benchmark Report

**Source:** Operator-run A/B benchmark (DUB-05) — 3-5 representative Chinese dialogue lines
**Copyright:** Operator-private — benchmark results are project-specific; do not redistribute.
**Last-verified:** <operator fills at benchmark close>
verified_date: <YYYY-MM>
```

**Template body structure** (operator fills at benchmark time):
- `## Reference Dialogue Lines` — 3-5 representative lines (emotional / voiceover / fast / slow / technical mix) — operator choice per CONTEXT.md DUB-05
- `## Variants Tested` — table: variant / model_dir / VRAM / first-call latency / steady-state latency
- `## A/B Results` — table: line_id / variant / MOS (mean opinion score) / WER% / operator preference / notes
- `## Default Lock Decision` — operator's manual pick recorded in `VERSION.json.tts.cosyvoice_default_variant` + rationale
- `## Open Questions` — follow-ups for v15+

**Scope guardrail:** this is a TEMPLATE the operator fills. Plan A creates the skeleton only; benchmark data is operator-action handoff (per CONTEXT.md DUB-05 locked decision — NOT auto-pick-lower-WER).

---

### `references/voicer/indextts2-to-cosyvoice-migration.md` (reference-doc, request-response — NEW)

**Analog:** `references/voicer/gold-team-tts-api.md:124` (CosyVoice-300M auto-route note) + `comfyui-indextts2-setup.md:21-29` (IndexTTS2 voice_preset + emotion sliders schema).

**Mapping table to author:**
| IndexTTS2 `voice_preset` | IndexTTS2 emotion sliders | CosyVoice equivalent | Migration notes |
|--------------------------|---------------------------|----------------------|-----------------|
| `Female_HQ` | `sad=0.3, calm=0.2` | `base_gender=Female, emotion=Sad, instruct_text="..."` | CosyVoice uses `instruct_text` for fine-grained prosody; sliders → emotion enum |
| `Male_HQ` | `happy=0.5` | `base_gender=Male, emotion=Happy` | ... |
| `Female` | `angry=0.7` | `base_gender=Female, emotion=Angry` | ... |
| `Male` | (neutral) | `base_gender=Male, emotion=None (Neutral)` | ... |

**Plus:** IndexTTS2 `use_emo_text=True` → CosyVoice multi-emotion segment detection (auto-enabled in AIIA_CosyVoice_TTS per live INPUT_TYPES verification).

**Anti-pattern section** — document that voice cloning (CosyVoice `reference_audio` input) has NO IndexTTS2 equivalent (IndexTTS2 only supports voice_preset + ref audio for emotion vector, not zero-shot clone). Migration to clone mode requires operator-supplied wavs (DUB-03 operator-action handoff).

---

### `.planning/phases/72-dub/72-smoke.sh` (test/smoke, request-response — NEW bash runner)

**Analog:** `.planning/phases/70-foundation-audit/70-smoke.sh` (80 lines, exact skeleton to mirror).

**Smoke script skeleton to mirror** (`70-smoke.sh:1-18`):
```bash
#!/usr/bin/env bash
# Phase 72 DUB smoke runner — N assertions. Usage: bash .planning/phases/72-dub/72-smoke.sh
set -euo pipefail
# Exits 0 only if all sub-claims pass. Hard-fails on first error, undefined var, or pipe failure.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 72 DUB smoke — N assertions"
echo "Repo root: $REPO_ROOT"
echo "KHS root: $KHS_ROOT"
echo ""
```

**Per-assertion block pattern** (`70-smoke.sh:20-25`):
```bash
# XCUT-XXa: <description>
if [ ! -f "$TARGET_FILE" ]; then
    echo "FAIL: XCUT-XXa — <reason>"
    exit 1
fi
echo "OK: XCUT-XXa — <success>"
```

**Grep-count assertion pattern** (`70-smoke.sh:28-33`):
```bash
COUNT=$(grep -c 'pattern' "$FILE" || true)
if [ "$COUNT" -lt N ]; then
    echo "FAIL: XCUT-XXb — expected >=N, got $COUNT"
    exit 1
fi
echo "OK: XCUT-XXb — $COUNT entries (>= N)"
```

**Phase 72 smoke assertions to draft** (from RESEARCH §Validation Architecture → Test Map — 11 smoke assertions):
- DUB-01a: `test -f $KHS_ROOT/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json`
- DUB-01b: `grep -c "^## " $KHS_ROOT/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md` returns `>= 5`
- DUB-01c: `grep -c "Fun-CosyVoice3" $KHS_ROOT/skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` returns `>= 1`
- DUB-02a: `python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from store import validate_tts_engine_division; print('OK')"`
- DUB-02b: `grep -c "TTS_ENGINE_VALUES" $KHS_ROOT/plugins/pipeline_state/store.py` returns `>= 1`
- DUB-03a: `python3 -c "...from store import TTS_ENGINE_VALUES; assert 'ltx_native' in TTS_ENGINE_VALUES and 'cosyvoice' in TTS_ENGINE_VALUES"`
- DUB-04a: `grep -A2 "IndexTTS2" $KHS_ROOT/skills/kais-movie-pipeline/SKILL.md | grep -ci "deprecated\|fallback"` returns `>= 1`
- DUB-05a: `python3 -c "import json; d=json.load(open('$KHS_ROOT/VERSION.json')); assert 'cosyvoice_default_variant' in d.get('tts', {})"`
- DUB-05b: `test -f $KHS_ROOT/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md`
- XCUT-02a: `grep -c "_TTS_ENGINE_INSTRUCTION" $KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py` returns `>= 1`
- XCUT-02b: `grep -c "MUST propagate tts_engine" $KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py` returns `>= 1`

Plus a final line: `echo "Phase 72 smoke status: ALL N ASSERTIONS PASSED"`.

**Note:** the bash smoke runner does NOT invoke live Docker / ComfyUI / gold-team (those are operator-action handoff; the smoke runner only verifies file/code presence). Live integration probes are documented in `cosyvoice-deployment.md` Healthcheck section for operator pre-flight use.

---

## Shared Patterns

### XCUT-02 `_INSTRUCTION` Constant Injection (META-RULE X-2)
**Source:** `p09_shot_breakdown.py:80-89` (`_FORM_FACTOR_INSTRUCTION`) + `p04_character_design.py:48-70` (3 sibling constants) + `p09:51-70` (`_CROSS_CUTTING_INSTRUCTION`)
**Apply to:** `_TTS_ENGINE_INSTRUCTION` in p10_voice.py; `_VOICE_CLONE_INSTRUCTION` in p04_character_design.py
**Core invariant (3-site injection):**
1. Define `_SOME_INSTRUCTION = "..."` constant with MUST/MANDATORY keyword at module top
2. Inject via `.task(steps=[f"{_SOME_INSTRUCTION}", ...])` AND a parallel `.constraints(["MUST ..."])` line
3. Assert via `test_*_unit.py` captured["goal"] goal-content test
Without all three sites, the rule is invisible to the subagent at runtime (per PITFALL X-2: subagents see ONLY the goal string, NOT SKILL.md).
**Budget rule:** MAX_CONSTRAINTS=7 per goal (per `references/prompt-design-standards.md`); current p10 has 5, adding 1 → 6 (within budget).

### Plain-Dict Schema Validation (DUB-02)
**Source:** `store.py:111-140` (`validate_form_factor_invariant`) — Phase 71 strict-enum precedent
**Apply to:** `validate_tts_engine_division(shot_list)` in store.py
**Core invariant:**
- Standalone function, NOT `@model_validator` (Shot is plain dict; no Pydantic Shot model exists)
- `frozenset` lookup table for enum values (matches `_STATIC_MOVES` at `p09:238`)
- `ValueError` on violation with explicit `(DUB-02 strict enum — no fuzzy matching)` suffix
- Called from p10_voice.run() pre-flight (NOT from a dataclass `__post_init__`)

### Goal-Content Test Assertion
**Source:** `tests/test_p09_unit.py:56-63, 159-184`
**Apply to:** `test_dub_division.py::test_p10_goal_includes_tts_engine_instruction`
**Core invariant:**
```python
captured: dict = {}
p10.run(..., delegate_task=_make_delegate_spy(captured), ...)
assert "TTS ENGINE ROUTING" in captured["goal"]
assert "MUST propagate tts_engine" in captured["goal"]
```
One test function per MUST keyword; all run under 2s; no Docker, no network.

### ComfyUI Workflow JSON Twin Authoring
**Source:** `comfyui-indextts2-setup.md:33-50` (IndexTTS2 AIIA workflow JSON)
**Apply to:** `cosyvoice-comfyui.json` (NEW)
**Core invariant:** Same AIIA vendor pattern (Loader + TTS + PreviewAudio nodes); CosyVoice swaps `AIIA_IndexTTS2_*` → `AIIA_CosyVoice_*` + adds `LoadAudio` node for `reference_audio` input (zero-shot clone).

### Ref Twin Authoring (cosyvoice-deployment.md)
**Source:** `comfyui-indextts2-setup.md` (176 lines, 9-section structure)
**Apply to:** `cosyvoice-deployment.md` (NEW)
**Core invariant:** Mirror section structure EXACTLY (Title block → Node Overview table → Voice Presets → Emotion control → Working API-Format Workflow JSON → Dependency Setup → Batch Submission → Alternative Paths → Model Location). Add CosyVoice-specific GPU VRAM Budget + Healthcheck + Known Issues sections.

### SKILL.md Body Edit (FOUND-08 frontmatter freeze)
**Source:** `_shared/SKILL-LAYOUT.md` + CLAUDE.md §Skill File Conventions + Phase 71 precedent
**Apply to:** `kais-movie-pipeline/SKILL.md:457` edit + `audio_pipeline/SKILL.md` updates
**Core invariant:** YAML frontmatter (`name`/`description`/`tags`/`related_skills`/`expert_id`/`metrics`) is FROZEN byte-identical. Edit body prose only. Insert inline near the relevant section; do not restructure H2 headings.

### Schema Migration with Defaults (additive fields)
**Source:** `store.py:79 form_factor: Literal[...] = "portrait"` (Phase 71 precedent) + `_STATE_FIELDS` auto-derivation at `store.py:108`
**Apply to:** `tts_engine` + `ltx_native_dialogue` Shot dict keys; `voice_clone_reference_wav` character_bible sibling field; `cosyvoice_default_variant` VERSION.json field
**Core invariant:** Additive fields default via `.get(key, default)` at read time. Old episode JSON loads cleanly with no migration script. Schema version bump optional for additive changes.

### Smoke Script grep/file Assertions
**Source:** `.planning/phases/70-foundation-audit/70-smoke.sh` (80 lines)
**Apply to:** `.planning/phases/72-dub/72-smoke.sh`
**Core invariant:** `set -euo pipefail` + `SCRIPT_DIR`/`REPO_ROOT`/`KHS_ROOT` resolution via `BASH_SOURCE` + per-assertion block (grep-count OR file-existence OR python-import check) + final `echo "ALL N ASSERTIONS PASSED"`. Exits non-zero on first failure. Does NOT invoke live Docker (those are operator-action probes documented in deployment doc).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `kais-hermes-skills/VERSION.json` | config/meta | file-I/O | Greenfield — no prior top-level VERSION.json anywhere in repo (`find` returned 0 results). Plan A uses RESEARCH §Pattern 4 schema directly. Convention precedent: `cli-config.yaml` top-level placement pattern from parent hermes-agent project. |
| `cosyvoice-benchmark.md` (operator-filled content) | reference-doc | file-I/O | Template skeleton only — actual A/B benchmark data is operator-action handoff (DUB-05 locked decision: NOT auto-pick-lower-WER). Planner uses RESEARCH §Pattern 4 schema + cn-tts-model-matrix.md header block; data is deferred. |
| `cosyvoice-deployment.md` (CosyVoice-specific Dependency Setup section content) | reference-doc | file-I/O | Structural twin of `comfyui-indextts2-setup.md` IS the analog for structure, but the actual 9-step dep-fix content differs (RESEARCH verified AIIA CosyVoice deps are mostly pre-installed; document the delta at execution time via `docker exec ... pip list`). |

## Metadata

**Analog search scope:**
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py` (full read, 312 lines)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py` (full read, 234 lines — the direct modify target)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` (full read, 491 lines — XCUT-02 + validator invocation precedent)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py` (targeted read, lines 1-120 — alternative multi-constant _INSTRUCTION pattern + character_bible schema declaration)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/comfyui-indextts2-setup.md` (full read, 371 lines — structural twin for cosyvoice-deployment.md)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py` (full read, 152 lines — direct modify target)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` (full read, 112 lines — de-phantom pattern + capability matrix structure)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh` (full read, 76 lines — direct modify target)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/gold-team-tts-batch.py` (full read, 185 lines — silent-output detection + duration matching patterns to reuse)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_unit.py` (full read, 259 lines — delegate spy + goal-content assertion pattern)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/conftest.py` (full read, 215 lines — fixture pattern for tmp_state_store + tmp_asset_bus + mock_delegate_factory)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/episodes/formc-test-01/.pipeline-assets/character-bible.json` (schema inspection via python json.load — V3 envelope `{value, derived_from, content_hash, schema_version=3.0}` with `value.characters[].4d_anchor.{identity,arc,voice,visual}`)
- `/data/workspace/hermes-agent/.planning/phases/70-foundation-audit/70-smoke.sh` (full read, 80 lines — smoke skeleton for 72-smoke.sh)
- `/data/workspace/hermes-agent/.planning/phases/71-form/71-PATTERNS.md` (full read — XCUT-02 precedent + smoke assertion drafting pattern)
- `find /data/workspace/kais-hermes-skills -name 'VERSION.json'` (0 results — confirms greenfield)
- `ls .../audio_pipeline/references/voicer/` (6 existing files — confirms no cosyvoice-* yet, no workflows/ dir)
- `ls .../kais-movie-pipeline/tests/` (existing test naming convention — `test_p<N>_*.py` + topic-named tests like `test_form_factor.py`)

**Files scanned:** 14 primary reads + 3 ls/find probes
**Pattern extraction date:** 2026-07-09
