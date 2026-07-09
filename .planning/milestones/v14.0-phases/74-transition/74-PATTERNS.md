# Phase 74: TRANSITION - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 11 (4 Plan A code/schema/tests + 4 Plan B SKILL.md/routing + 3 Plan C validation/smoke)
**Analogs found:** 11 / 11 (4 exact, 5 role-match or twin-by-spec, 2 sibling-precedent)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `kais-hermes-skills/plugins/pipeline_state/transition_schema.py` (NEW) | model/validator | CRUD | `plugins/pipeline_state/dub_validators.py` (Phase 72 sibling — module layout + ValueError pattern) + `store.py:111-140 validate_form_factor_invariant` (recursive scan) + `store.py:150 TTS_ENGINE_VALUES` (frozenset enum) | exact |
| `kais-hermes-skills/plugins/pipeline_state/asset_bus.py` (MODIFY — +1 ASSET_SCHEMA entry) | model/registry | CRUD | `asset_bus.py:230-236` (`e-konte-sheets` slot — p09 sibling) | exact |
| `kais-hermes-skills/plugins/kais_aigc/canvas_sync.py` (MODIFY — +1 tuple in `_PHASE_OUTPUT_MAP["p09"]`) | config/registry | request-response | `canvas_sync.py:1721-1724` (existing p09 2-entry list) | exact |
| `kais-hermes-skills/plugins/pipeline_state/tests/test_transition_schema.py` (NEW) | test | CRUD | `tests/test_store.py` (form_factor __post_init__ test) + `tests/test_asset_bus_phase35_slots.py:138-168` (slot-registered assertion) + Phase 72 test_dub_division.py pattern (per 72-PATTERNS) | exact |
| `kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` (MODIFY body — Step 9 + ownership subsection) | skill-body | request-response | same file's Step 9 procedure (line 189-208) + Phase 71 Tier 1 append pattern (body-only, FOUND-08 frontmatter freeze) | exact |
| `kais-hermes-skills/skills/movie-experts/editor/SKILL.md` (MODIFY body — Workflow Step 7 + ownership subsection) | skill-body | request-response | same file's Workflow Step 7 "Transition Design" (line 197) + Transition Parameters (line 126-131) | exact |
| `kais-hermes-skills/skills/movie-experts/cinematographer/references/transition-design.md` (NEW — 12-type taxonomy) | reference-doc | file-I/O | `cinematographer/references/e-konte-format.md` (twin-by-spec — header block + 5-layer schema doc) + `kais-movie-pipeline/references/video-engine-comparison.md` (ref-doc structure with comparison tables) | role-match |
| `kais-hermes-skills/skills/kais-movie-pipeline/references/transition-engine-routing.md` (NEW — routing table) | reference-doc | file-I/O | `references/video-engine-comparison.md` (engine comparison structure — 15 LTX/Wan/Hailuo/Vidu references verified) | exact-twin |
| `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` (MODIFY — +`_TRANSITION_DESIGN_INSTRUCTION` + consolidate form_factor) | service/orchestration | event-driven | `p09_shot_breakdown.py:51-89` (`_CROSS_CUTTING_INSTRUCTION` + `_FORM_FACTOR_INSTRUCTION`) + `p04_character_design.py:48-70` (sibling _INSTRUCTION block) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py` (MODIFY — +`_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` + read transition_design slot) | service/orchestration | event-driven | `p13_delivery.py:50-100` (existing 3-expert GoalBuilder chain) + Phase 72 p10_voice.py precedent | exact |
| `kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md` (MODIFY — Layer 5 schema + Output Schema) | reference-doc | file-I/O | same file's Layer 5 (line 116-130) + Output Schema (line 271-342) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md` (NEW — research report template) | reference-doc | file-I/O | `references/video-engine-comparison.md` (validation-report structure) + `audio_pipeline/references/voicer/cosyvoice-deployment.md` (template-with-placeholders pattern per 72-PATTERNS) | role-match |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py` (NEW — goal-content assertion) | test | event-driven | `tests/test_p09_unit.py:56-63, 159-184` (`_make_delegate_spy` + `captured["goal"]` assertion) | exact |
| `.planning/phases/74-transition/74-smoke.sh` (NEW — bash smoke runner) | test/smoke | request-response | `.planning/phases/70-foundation-audit/70-smoke.sh` (80-line skeleton) + Phase 71/72/73 smoke siblings | exact |

## Pattern Assignments

### `plugins/pipeline_state/transition_schema.py` (model/validator, CRUD — NEW)

**Primary analog:** `plugins/pipeline_state/dub_validators.py` (Phase 72 sibling — exact module layout to mirror)
**Secondary analogs:** `store.py:111-140 validate_form_factor_invariant` (ValueError audit-suffix pattern) + `store.py:150 TTS_ENGINE_VALUES` (frozenset enum lookup)

**File-level docstring pattern to mirror** (`dub_validators.py:1-15`):
```python
"""dub_validators.py — DUB-03 voice clone reference wav validation helpers.

Phase 72-01 module providing ``validate_voice_clone_ref(path)`` for the DUB-03
contract: CosyVoice clone mode requires a 3-10s clean wav at >=16kHz sample
rate. This helper enforces the rule at fail-fast time (called from
``tts_batch.generate_tts`` before submitting to ComfyUI AIIA_CosyVoice_TTS).

Design decisions:
- Sibling module to ``store.py`` (kept separate so store.py stays focused on
  state I/O per RESEARCH assumption A7).
- Uses stdlib ``wave`` module only (no pydub / librosa — CLAUDE.md "no new deps").
- Per CLAUDE.md Code Style: ``from __future__ import annotations`` + PEP 604
  unions (``str | Path``) + Ruff PLW1514 compliant (explicit encoding on open
  not needed — stdlib wave manages file handles internally).
"""
```

**Plan A transition_schema.py mirrors this EXACTLY** — same docstring structure (purpose → fail-fast contract → design decisions: sibling module / stdlib only / CLAUDE.md compliance).

**Module structure to mirror** (`dub_validators.py:17-22`):
```python
from __future__ import annotations

import contextlib
import wave
from pathlib import Path
```

**Plan A transition_schema.py imports** (per RESEARCH.md TRANS-02 example):
```python
from __future__ import annotations

from typing import Any, Literal
```

**frozenset enum lookup pattern** (`store.py:150` — Phase 72 precedent, the strict-enum template for transition_method + camera_continuity):
```python
TTS_ENGINE_VALUES = frozenset({"ltx_native", "cosyvoice", "indextts2_fallback"})
```

**Plan A transition_schema.py — TRANS-01 + TRANS-02 enums** (per RESEARCH.md TRANS-01/02 lock):
```python
# TRANS-01: 12-value enum (REQUIREMENTS.md line 41)
TRANSITION_METHOD_VALUES = Literal[
    "hard_cut", "dissolve", "wipe", "fade",
    "match_cut_shared_object", "match_cut_shared_landscape",
    "motion_vector_match", "color_match",
    "j_cut", "l_cut", "whip_pan", "none",
]
# TRANS-01: 6-value enum (REQUIREMENTS.md line 41)
CAMERA_CONTINUITY_VALUES = Literal[
    "pan_to", "zoom_to", "dolly_through",
    "whip_pan", "match_cut_on_motion", "none",
]

# Allow Python-level set for runtime validation (Literal is type-hint only).
_TRANSITION_METHOD_SET = frozenset({
    "hard_cut", "dissolve", "wipe", "fade",
    "match_cut_shared_object", "match_cut_shared_landscape",
    "motion_vector_match", "color_match",
    "j_cut", "l_cut", "whip_pan", "none",
})
_CAMERA_CONTINUITY_SET = frozenset({
    "pan_to", "zoom_to", "dolly_through",
    "whip_pan", "match_cut_on_motion", "none",
})
```

**ValueError audit-suffix pattern** (mirror `store.py:90-94` form_factor `__post_init__` + `store.py:194-200` validate_tts_engine_division):
```python
if tts_engine not in TTS_ENGINE_VALUES:
    raise ValueError(
        f"Shot {sid}: tts_engine must be one of "
        f"{sorted(TTS_ENGINE_VALUES)}, got {tts_engine!r} "
        f"(DUB-02 strict enum — no fuzzy matching, no "
        f"warnings-and-continue)."
    )
```

**Plan A `load_next_shot_link(value)` helper** (per RESEARCH.md TRANS-02 Code Example — full body in RESEARCH §TRANS-02 Backward-Compat Reader):
```python
def load_next_shot_link(value: Any) -> dict:
    """TRANS-02 backward-compat reader.

    Coerces legacy string form to structured default. Validates dict form
    against TRANS-01 enum. Mirrors FORM-01 form_factor __post_init__ pattern
    (store.py:111-140) + DUB-02 validate_tts_engine_division pattern
    (dub_validators.py).

    Examples:
        >>> load_next_shot_link("shot_02")
        {'shot_id': 'shot_02', 'transition_method': 'hard_cut',
         'visual_hook': None, 'camera_continuity': 'none', 'generation_path': None}

        >>> load_next_shot_link({"shot_id": "s3", "transition_method": "dissolve"})
        {'shot_id': 's3', 'transition_method': 'dissolve',
         'visual_hook': None, 'camera_continuity': 'none', 'generation_path': None}
    """
    if isinstance(value, str):
        return {
            "shot_id": value,
            "transition_method": "hard_cut",
            "visual_hook": None,
            "camera_continuity": "none",
            "generation_path": None,
        }
    if isinstance(value, dict):
        tm = value.get("transition_method", "hard_cut")
        if tm not in _TRANSITION_METHOD_SET:
            raise ValueError(
                f"invalid transition_method: {tm!r}; must be one of "
                f"{sorted(_TRANSITION_METHOD_SET)} "
                f"(TRANS-01 strict enum — no fuzzy matching, no warnings-and-continue)."
            )
        cc = value.get("camera_continuity", "none")
        if cc not in _CAMERA_CONTINUITY_SET:
            raise ValueError(
                f"invalid camera_continuity: {cc!r}; must be one of "
                f"{sorted(_CAMERA_CONTINUITY_SET)} "
                f"(TRANS-01 strict enum — no fuzzy matching, no warnings-and-continue)."
            )
        return {
            "shot_id": value.get("shot_id"),
            "transition_method": tm,
            "visual_hook": value.get("visual_hook"),
            "camera_continuity": cc,
            "generation_path": value.get("generation_path"),
        }
    raise TypeError(
        f"next_shot_link must be str (legacy) or dict (v14.0+), "
        f"got {type(value).__name__} (TRANS-02 strict type — no fuzzy coercion)."
    )
```

**Key mirroring decisions:**
1. **Sibling module to store.py, NOT `@model_validator`** — `dub_validators.py` is the established precedent (kept separate so store.py stays focused on state I/O).
2. **Module-level `frozenset` enum sets** — matches `_TRANSITION_METHOD_SET` / `_CAMERA_CONTINUITY_SET` to the `TTS_ENGINE_VALUES` / `_STATE_FIELDS` patterns.
3. **ValueError with `(TRANS-01 strict enum — no fuzzy matching)` suffix** — matches the DUB-02 / FORM-01 audit-suffix convention for grep-auditable traceability.
4. **No `@model_validator`, no `BaseModel`** — Shot is a plain dict; load_next_shot_link is a standalone coercion helper. The only Pydantic use is `Literal[...]` for type-checker hints (mirrors FORM-01 form_factor `Literal["landscape", "portrait"]` at store.py:79).

---

### `plugins/pipeline_state/asset_bus.py` (model/registry, CRUD — +1 ASSET_SCHEMA entry)

**Analog:** `asset_bus.py:230-236` (`e-konte-sheets` slot — Phase 36-02 p09 sibling — exact slot-addition pattern to mirror)

**ASSET_SCHEMA slot-entry pattern** (asset_bus.py:223-236 — the p09 output slot pair `shot-list` + `e-konte-sheets`):
```python
"shot-list": {
    "file": "shot-list.json",
    "format": "json",
    "description": "Shot list (one entry per shot with intent + duration)",
    "writer_phase": "p09_shot_breakdown",
    "reader_phases": ["p10_voice", "p11_video_render"],
},
"e-konte-sheets": {
    "file": "e-konte-sheets.json",
    "format": "json",
    "description": "E-Konte 5-layer shot decomposition sheets",
    "writer_phase": "p09_shot_breakdown",
    "reader_phases": ["p11_video_render"],
},
```

**Plan A appends `transition-design` slot** (insert AFTER `e-konte-sheets` to keep p09 outputs grouped, per RESEARCH.md TRANS-03 Pattern 1):
```python
# ── Phase 74 additions — transition design slot (TRANS-03) ──────────
# Phase 74 registers this slot so p09_shot_breakdown (cinematographer)
# can write transition design, and p13_delivery (editor) can read it
# for post-production execution. JSON format (envelope-wrapped, atomic
# write). Per-plan asset-bus extension (D-36-05): PRESERVES existing
# slots byte-equivalent — only appends.
"transition-design": {
    "file": "transition-design.json",
    "format": "json",
    "description": "Transition design (creative intent from cinematographer "
                   "Step 9; consumed by editor Step 13 for post-production "
                   "execution). Per-shot transition_method (12-enum) + "
                   "visual_hook + camera_continuity.",
    "writer_phase": "p09_shot_breakdown",
    "reader_phases": ["p13_delivery"],
},
```

**Key invariants:**
1. **`kebab-case` slot name** (NOT `transition_design` snake_case) — matches the existing 35+ slot convention (`shot-list`, `e-konte-sheets`, `master-mp4`).
2. **`format: "json"` + envelope-wrapped** — the slot goes through the standard AssetBus.write envelope path (`{value, derived_from, content_hash, schema_version}`) per asset_bus.py:223-236 precedent. Atomic write via tempfile.mkstemp + os.replace (D-33-02).
3. **writer_phase = `"p09_shot_breakdown"`, reader_phases = `["p13_delivery"]`** — the TRANS-04 ownership split encoded in the registry (cinematographer writes, editor reads).
4. **Append-only** — the existing 35+ slots MUST stay byte-equivalent per CONTEXT.md D-36-05 / D-74 invariant.

**Asset-bus-schema.md slot-table update** — slot count grows from 35 to 36 (NOT 31 → 32 as CONTEXT.md states — RESEARCH §TRANS-03 Pattern 1 verified 31 in Phase 36, but Phase 40/41/42/43 v6.0 + Phase 71/72/73 v14.0 added more). Planner re-verifies the count via `grep -c '^| `' asset-bus-schema.md` at execution time (returned 35 on 2026-07-09).

---

### `plugins/kais_aigc/canvas_sync.py` (config/registry, request-response — +1 tuple in `_PHASE_OUTPUT_MAP["p09"]`)

**Analog:** `canvas_sync.py:1721-1724` (existing p09 entry — exact pattern to extend)

**`_PHASE_OUTPUT_MAP` entry pattern** (canvas_sync.py:1676, 1721-1724 — the p09 2-entry list):
```python
_PHASE_OUTPUT_MAP: dict[str, list[tuple[str, str, str, bool]]] = {
    # ...
    "p09": [
        ("shot_list", "分镜列表", "storyboard", False),
        ("e_konte_sheets", "Eコンテ", "storyboard", False),
    ],
    # ...
}
```

**Tuple schema** (canvas_sync.py:1673-1675 — the 4-tuple contract):
```python
# Per-phase output key → artifact metadata.
# Each entry: (output_key, label, canvas_type, expand_subkeys)
# expand_subkeys: if the value is a dict, create child nodes from
#   its top-level keys/sublists.
```

**Plan A appends the 3rd p09 entry** (per RESEARCH.md TRANS-03 Pattern 2 — reuse `storyboard` canvas_type per PITFALL T-4 / Assumption A1):
```python
"p09": [
    ("shot_list", "分镜列表", "storyboard", False),
    ("e_konte_sheets", "Eコンテ", "storyboard", False),
    ("transition_design", "转场设计", "storyboard", False),  # NEW TRANS-03
],
```

**Key invariants:**
1. **`canvas_type="storyboard"`** — RESEARCH.md A1 confirmed the frontend zod schema (`canvasAssetSchema.ts`) has 5 node types (audio/video/asset/storyboard/script) with NO "transition" type. Reusing `storyboard` = **zero frontend change** (PITFALL T-4 mitigation #1).
2. **`expand_subkeys=False`** — the `transition_design` slot is a per-shot list (dict-of-arrays), NOT a flat dict. Matches `shot_list` (also `False`) rather than `story_framework` (`True`).
3. **Tuple order MUST match `(output_key, label, canvas_type, expand_subkeys)`** — a typo here silently breaks canvas sync (PITFALL T-4 silent invisibility).
4. **3-system registration in one commit** (PITFALL T-4): (1) ASSET_SCHEMA slot; (2) `_PHASE_OUTPUT_MAP` tuple; (3) frontend zod enum (REUSE storyboard = zero change, so this site is no-op).

**`_ARTIFACT_LIST_KEYS` consideration** (canvas_sync.py:1767-1771): the transition_design slot is keyed under `transitions` (per RESEARCH.md TRANS-01 example). If planner uses `transitions` as the top-level list key inside the JSON, add `"transitions"` to `_ARTIFACT_LIST_KEYS` so canvas sync expands it as a list. Alternative: use `shots` (already in the tuple) — then no `_ARTIFACT_LIST_KEYS` change needed.

---

### `plugins/pipeline_state/tests/test_transition_schema.py` (test, CRUD — NEW)

**Primary analog:** `tests/test_asset_bus_phase35_slots.py:138-168` (`test_slot_registered` + `test_slot_format_is_json` + `test_total_slot_count_at_least_10` pattern)
**Secondary analogs:** `tests/test_store.py` (form_factor __post_init__ ValueError test, per 71-PATTERNS) + Phase 72 test_dub_division.py (per 72-PATTERNS — `validate_tts_engine_division` raises ValueError on invalid enum)

**Imports + fixture pattern** (`test_asset_bus_phase35_slots.py:16-21`):
```python
from __future__ import annotations

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA, AssetBus, AssetBusError
```

**Plan A test_transition_schema.py imports** (TRANS-01/02 validator + TRANS-03 slot assertions):
```python
from __future__ import annotations

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA
from plugins.pipeline_state.transition_schema import (
    TRANSITION_METHOD_VALUES,
    CAMERA_CONTINUITY_VALUES,
    _TRANSITION_METHOD_SET,
    _CAMERA_CONTINUITY_SET,
    load_next_shot_link,
)
```

**TRANS-01 enum validation tests** (5 tests — mirror Phase 72 `test_division_rejects_*` pattern from 72-PATTERNS):
```python
def test_load_next_shot_link_string_coerces_to_default():
    """TRANS-02: legacy string next_shot_link coerces to structured default."""
    result = load_next_shot_link("shot_02")
    assert result == {
        "shot_id": "shot_02",
        "transition_method": "hard_cut",
        "visual_hook": None,
        "camera_continuity": "none",
        "generation_path": None,
    }

def test_load_next_shot_link_dict_validates():
    """TRANS-02: dict next_shot_link passes through with defaults filled."""
    result = load_next_shot_link({"shot_id": "s3", "transition_method": "dissolve"})
    assert result["shot_id"] == "s3"
    assert result["transition_method"] == "dissolve"
    assert result["camera_continuity"] == "none"

def test_load_next_shot_link_rejects_invalid_transition_method():
    """TRANS-01: invalid transition_method raises ValueError with audit suffix."""
    with pytest.raises(ValueError, match="TRANS-01 strict enum"):
        load_next_shot_link({"shot_id": "s1", "transition_method": "fake_transition"})

def test_load_next_shot_link_rejects_invalid_camera_continuity():
    """TRANS-01: invalid camera_continuity raises ValueError with audit suffix."""
    with pytest.raises(ValueError, match="TRANS-01 strict enum"):
        load_next_shot_link({"shot_id": "s1", "camera_continuity": "fake_continuity"})

def test_load_next_shot_link_rejects_non_str_non_dict():
    """TRANS-02: neither str nor dict raises TypeError."""
    with pytest.raises(TypeError, match="TRANS-02 strict type"):
        load_next_shot_link(42)
```

**TRANS-01 enum set sanity tests** (3 tests):
```python
def test_transition_method_enum_has_12_values():
    assert len(_TRANSITION_METHOD_SET) == 12
    # Sanity-check key values from REQUIREMENTS.md TRANS-01 line 41
    for required in ("hard_cut", "match_cut_shared_object", "whip_pan", "none"):
        assert required in _TRANSITION_METHOD_SET

def test_camera_continuity_enum_has_6_values():
    assert len(_CAMERA_CONTINUITY_SET) == 6
    for required in ("pan_to", "match_cut_on_motion", "none"):
        assert required in _CAMERA_CONTINUITY_SET

def test_legacy_cut_transition_type_alias_compatibility():
    """Pre-v14.0 episodes used 4-value cut_transition_type. Verify the 4
    legacy values are subsumed by the 12-value transition_method enum."""
    legacy_4 = {"hard_cut", "dissolve", "wipe", "fade"}
    assert legacy_4.issubset(_TRANSITION_METHOD_SET)
```

**TRANS-03 slot-registered test** (mirror `test_asset_bus_phase35_slots.py:138-168`):
```python
def test_transition_design_slot_registered():
    """TRANS-03 system 1: ASSET_SCHEMA contains transition-design slot."""
    assert "transition-design" in ASSET_SCHEMA, (
        f"transition-design slot not registered in ASSET_SCHEMA; "
        f"got keys={sorted(ASSET_SCHEMA.keys())}"
    )

def test_transition_design_slot_format_json():
    assert ASSET_SCHEMA["transition-design"].get("format") == "json"

def test_transition_design_slot_writer_phase_p09():
    """TRANS-04 ownership: writer_phase = p09 (cinematographer)."""
    assert ASSET_SCHEMA["transition-design"]["writer_phase"] == "p09_shot_breakdown"

def test_transition_design_slot_reader_phase_p13():
    """TRANS-04 ownership: reader_phases = [p13] (editor)."""
    readers = ASSET_SCHEMA["transition-design"]["reader_phases"]
    assert "p13_delivery" in readers
```

**Backward-compat legacy episode round-trip** (TRANS-02 smoke):
```python
def test_legacy_episode_loads_cleanly_with_string_next_shot_link():
    """TRANS-02: an old episode JSON with bare-string next_shot_link values
    loads cleanly via load_next_shot_link (no migration script needed)."""
    legacy_layer_5 = {
        "duration_sec": 3.2,
        "frame_count": 77,
        "fps": 24,
        "cut_transition_type": "hard_cut",  # legacy 4-value field
        "next_shot_link": "shot_02",         # legacy string form
    }
    coerced = load_next_shot_link(legacy_layer_5["next_shot_link"])
    assert coerced["shot_id"] == "shot_02"
    assert coerced["transition_method"] == "hard_cut"  # safe default
```

**Total: 11 unit tests. All run under 2s; no Docker, no network (pure function tests).**

---

### `skills/movie-experts/cinematographer/SKILL.md` (skill-body, request-response — Step 9 + ownership subsection)

**Analog:** same file's Step 9 procedure (line 189-208) + Phase 71 body-append pattern (FOUND-08 frontmatter freeze)

**Current Step 9 sub-step 5** (cinematographer/SKILL.md:199 — Layer 5 timing includes `cut_transition + next_shot_link`):
```markdown
5. **E-Konte 5-layer sheets** — For each shot, produce all 5 layers: composition (stage_geometry + props + blocking + power_point + headroom), camera (shot_scale + angle + camera_move + lens_mm + motion_intensity + axis_line), lighting (key/fill/temp/contrast), action (character pose/expression/action_beat), dialogue (dialogue_lines + sfx + bgm_cue), timing (duration_sec + frame_count + fps + cut_transition + next_shot_link).
```

**Plan A edits Step 9 sub-step 5** (extend Layer 5 to include TRANS-01 fields):
```markdown
5. **E-Konte 5-layer sheets** — For each shot, produce all 5 layers: composition (...), camera (...), lighting (...), action (...), dialogue (...), timing (duration_sec + frame_count + fps + transition_method (12-value enum: hard_cut / dissolve / wipe / fade / match_cut_shared_object / match_cut_shared_landscape / motion_vector_match / color_match / j_cut / l_cut / whip_pan / none) + visual_hook (free-text, str|None) + camera_continuity (6-value enum: pan_to / zoom_to / dolly_through / whip_pan / match_cut_on_motion / none) + next_shot_link (structured object — see `references/transition-design.md` + `references/e-konte-format.md` Layer 5 extension)).
```

**Plan A appends a new "### TRANSITION DESIGN Field Ownership" subsection** (after sub-step 9 of the Step 9 Procedure, before §Key technique — body-only append per FOUND-08 frontmatter freeze):
```markdown
### TRANSITION DESIGN Field Ownership (TRANS-04 — v14.0)

Cinematographer Step 9 owns the **CREATIVE INTENT** fields of transition design:

| Field | Type | Owned by Cinematographer Step 9 |
|-------|------|--------------------------------|
| `transition_method` | Literal (12-value enum) | YES — creative routing intent |
| `visual_hook` | str \| None | YES — the connecting visual element (e.g., "red mug → next shot red car") |
| `camera_continuity` | Literal (6-value enum) | YES — creative camera bridge intent |

Editor Workflow Step 7 + p13_delivery owns the **POST-PRODUCTION EXECUTION** fields (`cut_duration_frames` / `dissolve_curve` / `match_cut_alignment_point`). Cinematographer MUST NOT emit execution fields here — see `references/transition-design.md` §12-type taxonomy for the creative vocabulary + `references/transition-engine-routing.md` §per-transition routing for downstream execution paths.

No new `transition_designer` expert_id is added (FOUND-08 preserved — 15-expert frozen set).
```

**Frontmatter freeze (FOUND-08):** edit body prose only. Do NOT mutate the YAML frontmatter (`name`, `description`, `tags`, `related_skills`, `expert_id`, `metrics`). Phase 71/72/73 precedent — body-only patches.

---

### `skills/movie-experts/editor/SKILL.md` (skill-body, request-response — Workflow Step 7 + ownership subsection)

**Analog:** same file's Workflow Step 7 "Transition Design" (line 197) + Transition Parameters (line 126-131)

**Current Workflow Step 7** (editor/SKILL.md:197):
```markdown
7. **Transition Design** — Determine transition type and duration between shots;match cut 优先在场景转换处
```

**Current Transition Parameters** (editor/SKILL.md:126-131):
```markdown
### Transition Parameters(unchanged from Phase 0)
- **hard_cut**: 0 frames
- **dissolve**: 12-24 frames (0.5-1.0s @24fps)
- **overlap**: 6-12 frames (match cut,per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §Match Cut Design)
- **wipe**: 24-36 frames (stylized only)
- **fade_in/out**: 24-48 frames (scene boundaries)
```

**Plan A edits Workflow Step 7** (extend to cite TRANS-04 ownership + read transition_design slot):
```markdown
7. **Transition Design (TRANS-04 — v14.0 ownership split)** — Reads `transition-design` asset (cinematographer Step 9 creative intent: `transition_method` / `visual_hook` / `camera_continuity`) and emits post-production execution fields: `cut_duration_frames` (int) / `dissolve_curve` (Literal["linear", "ease_in", "ease_out", "ease_in_out"]) / `match_cut_alignment_point` (int frame number, optional). Match cut 优先在场景转换处. See `references/transition-design.md` §12-type taxonomy for creative intent + `references/transition-engine-routing.md` §per-transition routing for the execution path of each transition_method (ffmpeg xfade vs Wan2.2 FLF2V vs Hailuo/Vidu cloud).
```

**Plan A appends a new "### TRANSITION DESIGN Execution Ownership" subsection** (after Workflow Step 13, before §Quality Thresholds):
```markdown
### TRANSITION DESIGN Execution Ownership (TRANS-04 — v14.0)

Editor Workflow Step 7 (Transition Design) + p13_delivery (Step 13 = pipeline phase, NOT editor SKILL.md Workflow Step 13) own the **POST-PRODUCTION EXECUTION** fields:

| Field | Type | Owned by Editor (Step 7 + p13) |
|-------|------|--------------------------------|
| `cut_duration_frames` | int | YES — frame-precise cut timing |
| `dissolve_curve` | Literal["linear", "ease_in", "ease_out", "ease_in_out"] | YES — dissolve easing curve |
| `match_cut_alignment_point` | int (frame number, optional) | YES — exact frame to match-cut on |

Cinematographer Step 9 owns the creative intent fields (`transition_method` / `visual_hook` / `camera_continuity`). Editor MUST read `transition-design` slot — do NOT re-decide creative intent; only emit execution parameters. See `references/transition-engine-routing.md` §routing table for which transition_method values map to ffmpeg xfade (post-production) vs Wan2.2 FLF2V / Hailuo / Vidu (generation-time).

**PITFALL T-4 disambiguation (per RESEARCH):** "Step 13" in TRANS-04 refers to the **pipeline phase** `p13_delivery.py` (line 89: editor performs final-cut + render), which corresponds to editor SKILL.md Workflow Steps 7-13 collectively. Both locations are documented here.
```

**Frontmatter freeze (FOUND-08):** body-only edit.

---

### `skills/movie-experts/cinematographer/references/transition-design.md` (reference-doc, file-I/O — NEW 12-type taxonomy)

**Analog 1 (structural twin):** `cinematographer/references/e-konte-format.md` (5-layer schema doc — header block + YAML schema + heuristic sections)
**Analog 2 (taxonomy structure):** `references/video-engine-comparison.md` (comparison table with engine trade-offs — 15 LTX/Wan/Hailuo/Vidu references verified)
**Analog 3 (header block format):** `cinematographer/references/vertical-screen-framing.md:1-6` (per 71-PATTERNS — Source / Copyright / Last-verified / verified_date block)

**Header block to mirror** (vertical-screen-framing.md:1-6 — Phase 71 established header convention):
```markdown
# <Title> — <subtitle>

**Source:** <provenance>
**Copyright:** Fair Use — <rationale>
**Last-verified:** 2026-07-09
verified_date: 2026-07
```

**Plan A transition-design.md header:**
```markdown
# Transition Design 12-Type Taxonomy — Creative Intent + Engine Routing

**Source:** Industry-standard transition taxonomy (StudioBinder "Types of Editing Transitions in Film", Adobe Premiere transition reference); film citations under Fair Use with attribution per CLAUDE.md copyright discipline.
**Copyright:** Fair Use — taxonomy is industry-standard vocabulary; film examples paraphrased + cited.
**Last-verified:** 2026-07-09
verified_date: 2026-07
```

**Per-type section structure** (per CONTEXT.md TRANS-05 locked spec — 12 sections, one per transition_method):
```markdown
## 1. `hard_cut` (硬切)

**Definition:** Direct concatenation of two shots with no transition effect.
**When to use:** Default transition; use when action drives the cut (cut on action), when rhythm demands it, or when any effect would distract.
**Execution path classification:** post-production (ffmpeg concat, no generation).
**Concrete film examples:** *The French Connection* (1971) chase sequence; most narrative feature films (>80% of all cuts).
**Engine routing:** ffmpeg only — no GLM cost, no GPU. See `transition-engine-routing.md` §hard_cut.

## 2. `dissolve` (溶解)
... (repeat structure for all 12 types)
```

**Citation discipline (per CLAUDE.md copyright):** Each film example MUST cite title + year + director. Examples under fair-use paraphrase + attribution only. Match-cut bone-to-spaceship = *2001: A Space Odyssey* (1968, Kubrick); whip-pan = *La La Land* (2016, Chazelle) opening.

---

### `skills/kais-movie-pipeline/references/transition-engine-routing.md` (reference-doc, file-I/O — NEW per-transition routing)

**Analog (exact twin):** `references/video-engine-comparison.md` (engine comparison structure — verified 15 LTX/Wan/Hailuo/Vidu references on 2026-07-09)

**Header block to mirror** (video-engine-comparison.md:1-7 — established pipeline ref structure):
```markdown
# Video Engine Comparison — LTX vs Wan vs Hailuo vs Vidu

**Source:** ...
**Copyright:** ...
**Last-verified:** 2026-07-09
```

**Plan A transition-engine-routing.md content structure** (per RESEARCH.md TRANS-06 Code Example — routing table):
```markdown
## Per-Transition Engine Routing (TRANS-06)

| transition_method | Primary Engine | Fallback | LTX-2.3 FLF Evaluation |
|-------------------|----------------|----------|------------------------|
| `hard_cut` | ffmpeg (no generation — direct concat in P12) | — | N/A (no generation) |
| `j_cut` | ffmpeg (audio lead 0.3-0.8s before visual cut) | — | N/A |
| `l_cut` | ffmpeg (visual lead 0.2-0.5s before audio cut) | — | N/A |
| `dissolve` | ffmpeg xfade=fade (12-24 frames @24fps) | — | LTX native time-based exists but adds VRAM cost; ffmpeg wins |
| `wipe` | ffmpeg xfade=wipeleft/wiperight (24-36 frames) | — | N/A |
| `fade` | ffmpeg xfade=fade (24-48 frames, scene boundaries) | — | N/A |
| `match_cut_shared_object` | Wan2.2 14B FLF2V (local, ~21GB VRAM) | ffmpeg manual cut on action | LTX-2.3 FLF viable BUT no identity continuity from previous shot (drift risk per PITFALL T-1) |
| `match_cut_shared_landscape` | Hailuo 02 i2v Pro (cloud, opt-in MINIMAX_API_KEY) | Vidu keyframe-to-video (cloud, opt-in VIDU_API_KEY) → ffmpeg manual cut | LTX-2.3 FLF viable for landscape match; same drift caveat |
| `motion_vector_match` | Hailuo / Vidu (motion-vector generation is cloud-native strength) | ffmpeg motion-based cut | LTX-2.3 not trained for motion-vector matching |
| `color_match` | ffmpeg color adjustment (post-production) | — | N/A |
| `whip_pan` | ffmpeg whippan simulation + operator manual override | — | AI unreliable per TRANS-08 deferred; v15+ candidate |
| `none` | ffmpeg (direct concat, no transition) | — | N/A |

### LTX-2.3 FLF + ICLoRA Combined Workflow Note (PITFALL T-1)

LTX-2.3 has TWO ORTHOGONAL capabilities — they are SEPARATE workflows with no
merged turnkey option today:
- **ICLoRA** (`ltx/msr` LiconMSR): identity preservation via ref1-ref5 multi-reference
- **FLF** (`ltx/fflf` + `ltx/singularityFFLF`): first/last frame conditioning

Per-transition routing MUST state the trade-off explicitly:
- IF transition needs identity continuity → MSR + post-production match-cut
- IF transition needs frame-interpolation → FLF + accept identity drift risk

### INFRA-04 Compliance (PITFALL X-5)

All transition engine calls (Wan2.2 FLF2V / Hailuo / Vidu / LTX-2.3) run under the existing `glm_concurrent` semaphore (`MAX_CONCURRENT_GL=1`). NO separate transition semaphore. Routing decisions are **declarative** (this table) — NOT runtime LLM decisions (TRANS-10 deferred). Subagent reads this table at goal-construction time and routes deterministically.
```

**Key invariants:**
1. **`INFRA-04 compliance` section is load-bearing** — prevents a v15+ engineer from accidentally adding a `transition_concurrent` semaphore that violates the serial constraint.
2. **Each row cites the fallback engine** — Hailuo/Vidu cloud engines are opt-in (XCUT-04b operator-action handoff); ffmpeg fallback MUST be documented.
3. **PITFALL T-1 cross-reference** — every LTX-2.3 FLF entry must state the drift risk.

---

### `pipeline/phases/p09_shot_breakdown.py` (service/orchestration, event-driven — +`_TRANSITION_DESIGN_INSTRUCTION`)

**Analog 1 (constant definition):** same file's `_CROSS_CUTTING_INSTRUCTION` (lines 51-70) + `_FORM_FACTOR_INSTRUCTION` (lines 80-89 — Phase 71 precedent)
**Analog 2 (alternative multi-constant style):** `pipeline/phases/p04_character_design.py:48-70` (3 sibling _INSTRUCTION constants — per 71-PATTERNS)
**Analog 3 (DUB/IMG sibling):** Phase 72 `p10_voice.py` `_TTS_ENGINE_INSTRUCTION` + Phase 73 `p07_scene_generation.py` `_VISION_VERIFY_INSTRUCTION` (per 72/73-PATTERNS)

**`_FORM_FACTOR_INSTRUCTION` placement pattern** (p09_shot_breakdown.py:80-89 — Phase 71 placement):
```python
# ―― Form factor adaptation (v14.0 FORM-01 / XCUT-02 / META-RULE X-2) ――
# Per PITFALL X-2: subagents see ONLY the goal string. They do NOT read
# SKILL.md at runtime. Therefore the form_factor MUST rule must be encoded
# as a constant and injected into the .task(steps=[...]) goal f-string AND
# a .constraints([...]) entry — both injection sites are required for the
# rule to be enforceable rather than advisory.
# Per PITFALL F-1: landscape is NOT "just resize 9:16" — power points,
# headroom, subtitle safe area, and camera-move priority all differ.
_FORM_FACTOR_INSTRUCTION = (
    "FORM FACTOR ADAPTATION (mandatory — MUST read form_factor from pipeline_state "
    "context and propagate it to every shot_intent.power_point and framing decision). "
    "Portrait (9:16) uses vertical power points (1/3, 1/4) with 5-10% headroom and "
    "tilt/crane priority; load vertical-screen-framing.md. "
    "Landscape (16:9) uses horizontal rule-of-thirds (1/3, 1/3) with 8-15% headroom, "
    "lead room 15-25% for profiles, and pan/tracking/Steadicam priority; load "
    "horizontal-screen-framing.md. "
    "16:9 is NOT 'just resize 9:16' — creative framing rules differ between forms."
)
```

**Plan A adds `_TRANSITION_DESIGN_INSTRUCTION` near other `_INSTRUCTION` constants** (per RESEARCH.md TRANS-06 Pattern 3 + CONTEXT.md XCUT-02 lock):
```python
# ―― Transition design (v14.0 TRANS-01..04 / XCUT-02 / META-RULE X-2) ――
# Per PITFALL X-2: subagents see ONLY the goal string. They do NOT read
# SKILL.md at runtime. Therefore the transition_design rule MUST be encoded
# as a constant and injected into .task(steps=[...]) AND .constraints([...]) —
# both injection sites are required for the rule to be enforceable.
_TRANSITION_DESIGN_INSTRUCTION = (
    "TRANSITION DESIGN (v14.0 TRANS-01..04 — mandatory for every shot):\n"
    "1. Each shot's E-Konte Layer 5 timing MUST include:\n"
    "   - transition_method: one of 12 values (hard_cut / dissolve / wipe / fade / "
    "     match_cut_shared_object / match_cut_shared_landscape / motion_vector_match / "
    "     color_match / j_cut / l_cut / whip_pan / none). Default 'hard_cut'.\n"
    "   - visual_hook: free-text describing the connecting element (e.g., 'red mug → "
    "     next shot red car'); null when not applicable.\n"
    "   - camera_continuity: one of 6 values (pan_to / zoom_to / dolly_through / "
    "     whip_pan / match_cut_on_motion / none). Default 'none'.\n"
    "2. next_shot_link MUST be a structured object {shot_id, transition_method, "
    "   visual_hook, camera_continuity, generation_path} — NOT a bare string. "
    "   Backward-compat: if reading an old episode, coerce string to "
    "   {shot_id: <string>, transition_method: 'hard_cut', ...defaults}.\n"
    "3. Emit transition_design.json as a first-class asset: per-shot entries with "
    "   {shot_id, transition_method, visual_hook, camera_continuity, form_factor}.\n"
    "4. Ownership split (TRANS-04): cinematographer owns creative intent "
    "   (transition_method / visual_hook / camera_continuity); editor Step 13 owns "
    "   post-production execution (cut_duration_frames / dissolve_curve / "
    "   match_cut_alignment_point). DO NOT emit execution fields here.\n"
    "5. Routing (TRANS-06 — declarative, NOT runtime LLM): hard_cut/j_cut/l_cut → "
    "   ffmpeg; dissolve/wipe/fade → ffmpeg xfade; match_cut_shared_object → "
    "   Wan2.2 FLF2V; match_cut_shared_landscape/motion_vector_match → Hailuo/Vidu "
    "   (opt-in operator API key); color_match → ffmpeg color; whip_pan → ffmpeg "
    "   whippan (AI unreliable per TRANS-08 deferred)."
)
```

**MAX_CONSTRAINTS=7 budget — CRITICAL CONSOLIDATION** (RESEARCH §Pitfall 2):

Current p09 has **6 constraints** (p09_shot_breakdown.py:396-404):
```python
.constraints([
    "MUST produce E-Konte 5-layer sheets for EVERY shot (not optional)",               # 1
    "MUST check all 4 continuity dimensions (face/figure/scene/style) via continuity_auditor",  # 2
    "MUST inject all 5 cross-cutting params per shot (character_refs/scene_ref/style_prefix/color_guidance/physics_state) AND MUST read form_factor from pipeline_state and propagate it to shot_intent.power_point and framing decisions",  # 3 (consolidated)
    "MUST use ≥5 DIFFERENT camera_movement values across shots (≥6 shots); static (固定) ≤30% of total; each shot needs camera_move_motivation explaining WHY this move serves the narrative emotion",  # 4
    "MUST use ≥3 DIFFERENT framing values across shots (≥4 shots); final shot favors 特写/大特写; 远景 ≤20%",  # 5
    "MUST output all 9 canvas structured fields per shot: camera_movement/framing/composition/pacing/timeline/axis_line/emotion/audio_cue/ltx_prompt — derive from E-Konte layers when possible",  # 6
    fix_feedback,  # 7 (empty placeholder — counts against budget)
])
```

**Adding 1 transition constraint = 7 (at limit, just fits). Adding 2 = 8 (BUDGET EXCEEDED).** RESEARCH §Pitfall 2 + Assumption A2 recommend: **consolidate the transition MUST with the existing consolidated constraint #3** (both are Layer 5 E-Konte fields, semantically cohesive). Plan A edits constraint #3 to absorb the transition_method MUST:

```python
"MUST inject all 5 cross-cutting params per shot (character_refs/scene_ref/style_prefix/color_guidance/physics_state) AND MUST read form_factor from pipeline_state and propagate it to shot_intent.power_point and framing decisions AND MUST emit per-shot transition_method (12-value enum) + visual_hook + camera_continuity + structured next_shot_link in E-Konte Layer 5 (TRANS-01..04)",  # 3 — consolidated Layer 5 fields
```

**Plan A injects `_TRANSITION_DESIGN_INSTRUCTION` into `.task(steps=[...])`** at p09:367-379 (the task block is NOT budget-counted — safe to append freely):
```python
.task(steps=[
    "Load both experts via skill_view",
    "cinematographer decomposes each selected scene into shot list (intent + duration per shot)",
    f"{_DURATION_DECISION_INSTRUCTION}",
    f"{_CAMERA_MOVE_SELECTION_INSTRUCTION}",
    f"{_PACING_SHOTTYPE_INSTRUCTION}",
    f"{_LTX_PROMPT_WRITING_GUIDE}",
    "cinematographer produces E-Konte 5-layer sheets: composition / camera / lighting / action / dialogue",
    f"{_CROSS_CUTTING_INSTRUCTION}",
    f"{_FORM_FACTOR_INSTRUCTION}",
    f"{_TRANSITION_DESIGN_INSTRUCTION}",   # NEW Plan A XCUT-02
    "continuity_auditor runs pre-render continuity check (...)",
    "Flag cross-shot inconsistencies for fix-up before video render",
])
```

**Plan A writes the `transition-design` slot** (after the existing asset_bus_write calls at p09:446-447):
```python
asset_bus_write("shot-list", shot_list)
asset_bus_write("e-konte-sheets", e_konte_sheets)
# Plan A TRANS-03: transition-design slot (creative intent from cinematographer Step 9).
transition_design = expert_output.get("transition_design", [])
asset_bus_write("transition-design", transition_design)
```

**Alternative to consolidation** (if planner prefers NOT to merge with form_factor): convert one existing constraint to a `.task(steps=[...])` entry (task steps are NOT budget-counted). Recommend migrating constraint #5 (shot scale diversity) into the existing `_PACING_SHOTTYPE_INSTRUCTION` body. **RESEARCH §Pitfall 2 explicitly recommends consolidation; defer the choice to planner.**

---

### `pipeline/phases/p13_delivery.py` (service/orchestration, event-driven — +`_EDITOR_TRANSITION_EXECUTION_INSTRUCTION`)

**Analog:** same file's existing 3-expert GoalBuilder chain (lines 50-108) + Phase 72 p10_voice.py `_TTS_ENGINE_INSTRUCTION` precedent (per 72-PATTERNS)

**Current p13 state** (verified — 160 lines read):
- Line 43-47: phase metadata (`PHASE_ID = "p13_delivery"`, `INPUT_SLOTS = ["master-timeline", "audio-stems", "color-intent"]`, `OUTPUT_SLOTS = ["master-mp4", "delivery-package"]`)
- Line 67-69: 3 input slots read (`master_timeline`, `audio_stems`, `color_intent`)
- Line 77-108: GoalBuilder chain (`.role(expert_skills=["colorist", "compliance_gate", "editor"])` → `.context(...)` → `.task(steps=[4 items])` → `.schema(shape={...})` → `.constraints([4 items])` → `.quality([4 items])`)
- **No `_INSTRUCTION` constants currently defined** — Phase 74 is the first to add them to p13

**Plan A adds `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` near top** (mirror p09:80 placement):
```python
# ―― Editor transition execution (v14.0 TRANS-04 / XCUT-02 / META-RULE X-2) ――
# Per PITFALL X-2: subagents see ONLY the goal string. They do NOT read
# SKILL.md at runtime. Therefore the editor execution-ownership rule MUST
# be encoded as a constant and injected into .task(steps=[...]) AND
# .constraints([...]).
_EDITOR_TRANSITION_EXECUTION_INSTRUCTION = (
    "EDITOR TRANSITION EXECUTION (v14.0 TRANS-04 — mandatory):\n"
    "1. Read the `transition-design` asset (written by cinematographer Step 9). "
    "It contains per-shot creative intent: transition_method (12-enum) + visual_hook + "
    "camera_continuity. DO NOT re-decide creative intent.\n"
    "2. Emit per-shot POST-PRODUCTION EXECUTION fields:\n"
    "   - cut_duration_frames (int) — frame-precise cut timing.\n"
    "   - dissolve_curve (Literal['linear', 'ease_in', 'ease_out', 'ease_in_out']) — "
    "     dissolve easing curve (only meaningful when transition_method ∈ {dissolve, fade}).\n"
    "   - match_cut_alignment_point (int, optional) — exact frame number to match-cut on "
    "     (only meaningful when transition_method ∈ {match_cut_shared_object, "
    "     match_cut_shared_landscape, motion_vector_match}).\n"
    "3. Routing (TRANS-06 — declarative): hard_cut/j_cut/l_cut → ffmpeg concat; "
    "   dissolve/wipe/fade → ffmpeg xfade; match_cut → Wan2.2 FLF2V / Hailuo / Vidu "
    "   (opt-in operator API key); color_match → ffmpeg color; whip_pan → ffmpeg whippan.\n"
    "4. Found-08 ownership: NO new transition_designer expert_id. Cinematographer owns "
    "   creative; editor owns execution. See references/transition-engine-routing.md."
)
```

**Plan A extends INPUT_SLOTS + the read call** (line 45 + line 70):
```python
INPUT_SLOTS = ["master-timeline", "audio-stems", "color-intent", "transition-design"]
# ...
color_intent = asset_bus_read("color-intent") or {}
transition_design = asset_bus_read("transition-design") or {}   # NEW Plan A TRANS-04
```

**Plan A injects into `.task(steps=[...])`** (line 85-90):
```python
.task(steps=[
    "Load all three experts via skill_view",
    "colorist applies LUT + final grade per color-intent (CxSxZ 28-combination)",
    "compliance_gate runs CN red-line content-rules check + AIGC labeling verification",
    "editor performs final-cut conform and renders master.mp4 (PIPE-COMPOSE-01 contract)",
    f"{_EDITOR_TRANSITION_EXECUTION_INSTRUCTION}",   # NEW Plan A XCUT-02
])
```

**Plan A adds a MUST constraint** (p13 has 4 current constraints — adding 1 = 5, within MAX_CONSTRAINTS=7 budget):
```python
.constraints([
    "MUST emit master.mp4 as canonical output artifact (PIPE-COMPOSE-01 contract)",
    "MUST pass compliance_gate before delivery (CN red-line)",
    "MUST match LUT to CxSxZ combination from p07 color-intent",
    "MUST include checksums for all assets in delivery manifest",
    "MUST read transition-design asset and emit per-shot cut_duration_frames + dissolve_curve + match_cut_alignment_point (TRANS-04 editor execution ownership)",  # NEW
])
```

**Plan A adds `transition_design` to `.context(...)`** so the subagent sees it in the goal context:
```python
.context(
    master_timeline=master_timeline,
    audio_stems=audio_stems,
    color_intent=color_intent,
    transition_design=transition_design,   # NEW Plan A TRANS-04
)
```

**Key invariants:**
1. **p13 reads the slot; p09 writes it** — TRANS-04 ownership split encoded in the asset-bus registry (writer_phase=p09, reader_phases=[p13]).
2. **p13 MAX_CONSTRAINTS budget = 5 after addition** (within limit 7) — no consolidation needed for p13 (unlike p09 which is at the limit).
3. **`_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` body explicitly states "DO NOT re-decide creative intent"** — prevents the editor from re-deciding transition_method (FOUND-08 ownership boundary).

---

### `cinematographer/references/e-konte-format.md` (reference-doc, file-I/O — Layer 5 schema + Output Schema MODIFY)

**Analog:** same file's Layer 5 section (line 116-130) + Output Schema (line 271-342)

**Current Layer 5 schema** (e-konte-format.md:118-127):
```yaml
layer_5_timing:
  duration_sec: 3.2
  frame_count: 77          # 24fps × 3.2s = 77 frames(短剧标准 24fps)
  fps: 24                  # 详见 vertical-screen-framing.md §FPS Standards
  cut_transition_type: "hard_cut"  # hard_cut / dissolve / wipe / fade
  next_shot_link: "shot_02"  # 絵切り 后续 shot id
```

**Plan A extends Layer 5 schema** (insert AFTER `cut_transition_type`, BEFORE `next_shot_link` — per RESEARCH.md TRANS-01 Code Example):
```yaml
layer_5_timing:
  duration_sec: 3.2
  frame_count: 77
  fps: 24
  # ── v14.0 TRANS-01 extension (transition_method replaces cut_transition_type) ──
  transition_method: "match_cut_shared_object"  # 12-value enum (supersedes cut_transition_type 4-value)
  visual_hook: "red mug on desk → next shot red car passing window"  # str | None
  camera_continuity: "match_cut_on_motion"  # 6-value enum
  # Legacy field preserved as alias for backward compat (pre-v14.0 episodes).
  cut_transition_type: "hard_cut"  # DEPRECATED alias — transition_method supersedes
  # ── v14.0 TRANS-02 structured migration (was: next_shot_link: "shot_02") ──
  next_shot_link:
    shot_id: "ep01_shot_008"
    transition_method: "match_cut_shared_object"
    visual_hook: "red mug → red car"
    camera_continuity: "match_cut_on_motion"
    generation_path: null  # filled by generation layer (p11) or operator
```

**Current Output Schema Layer 5** (e-konte-format.md:327-329):
```yaml
layer_5_timing:
  duration_sec: 3.0
  frame_count: 72              # 24fps × 3s
```

**Plan A extends the Output Schema Layer 5 example** (mirror the same fields as above).

**Backward-compat note to add at end of Layer 5 section** (per RESEARCH.md §Runtime State Inventory — `cut_transition_type` preserved as alias):
```markdown
### Layer 5 字段演变 (v14.0 TRANS-01..02)

**v13.0 fields (legacy, preserved as aliases):**
- `cut_transition_type`: 4-value enum (hard_cut / dissolve / wipe / fade) — superseded by `transition_method` (12-value)
- `next_shot_link: "shot_02"` — bare string, superseded by structured object

**v14.0 fields (TRANS-01 + TRANS-02):**
- `transition_method`: 12-value enum — see `transition-design.md` §12-type taxonomy
- `visual_hook`: str | None — free-text connecting element
- `camera_continuity`: 6-value enum
- `next_shot_link`: structured object `{shot_id, transition_method, visual_hook, camera_continuity, generation_path}`

**Backward-compat reader:** `load_next_shot_link(value)` in `plugins/pipeline_state/transition_schema.py` coerces legacy string form to structured default. Pre-v14.0 episode JSON loads cleanly with no migration script.
```

---

### `references/ltx-flf-iclora-validation.md` (reference-doc, file-I/O — NEW validation report template)

**Analog 1 (template structure):** `references/video-engine-comparison.md` (engine-comparison structure)
**Analog 2 (template-with-placeholders):** `audio_pipeline/references/voicer/cosyvoice-benchmark.md` per 72-PATTERNS (operator-filled template — skeleton with explicit "operator fills" placeholders)
**Analog 3 (deployment setup):** `audio_pipeline/references/voicer/cosyvoice-deployment.md` per 72-PATTERNS (9-section structural twin — install / healthcheck / known issues)

**Header block to mirror** (per 71-PATTERNS + 72-PATTERNS — established ref header convention):
```markdown
# LTX-2.3 FLF + ICLoRA Combined Workflow Validation (TRANS-07)

**Source:** LTX-2.3 IC-LoRA docs (docs.ltx.video); community ComfyUI workflows (ltx23.org, Reddit r/StableDiffusion); PITFALLS.md T-1 (FLF vs ICLoRA orthogonality).
**Copyright:** Fair Use — workflow setup paraphrased from public docs; validation results are operator-private.
**Last-verified:** <operator fills at validation close>
verified_date: <YYYY-MM>

**Scope:** Research-scope validation on 1-2 reference shots ONLY. NOT pipeline-integrated. Operator runs the actual shots; this phase produces the report TEMPLATE + setup instructions (CONTEXT.md TRANS-07 lock).
```

**Plan A content structure** (per RESEARCH.md TRANS-07 Open Question #2 — detailed setup with operator-fills placeholders):
```markdown
## ComfyUI Node Graph Setup

1. Load `LiconMSR` model (ltx/msr) via LiconMSR Loader node — provides ref1-ref5 multi-reference identity preservation.
2. Load `ltx/fflf` OR `ltx/singularityFFLF` via Loader node — provides first/last frame conditioning.
3. Add `LTXVConditioning` node — combines ICLoRA identity with FLF first/last frame.
4. Add `SamplerCustomAdvanced` node — samples with combined conditioning.
5. Connect: Loader → LTXVConditioning → SamplerCustomAdvanced → VAEDecode → SaveVideo.

**Note:** No turnkey combined workflow exists today (per PITFALL T-1). The above node graph is the community-reported combination from [Reddit r/StableDiffusion LTX-2.3 ID-LoRA with FLF](https://www.reddit.com/r/StableDiffusion/comments/1t71x0r/). Operator validates + reports results below.

## Reference Shots (operator fills)

### Shot 1: <operator describes>
- **Setup:** <first frame path> → <last frame path>; ref1-ref5 = <character identity references>
- **Identity continuity assessment:** <operator fills — character face/clothing consistency across frames>
- **Drift risk observation:** <operator fills — does identity drift between FLF frames?>
- **Verdict:** <pass | drift_unacceptable | partial>

### Shot 2: <operator describes>
... (same template)

## Production-Readiness Verdict

- [ ] **Ready for v15+ production rollout (TRANS-11):** identity continuity preserved across FLF frames; combined workflow stable.
- [ ] **Deferred to v15+:** identity drift observed; document rationale + alternative paths (Wan2.2 FLF2V + post-production match-cut).

**Operator signature:** _______________  **Date:** ___________
```

**Scope guardrail:** this is a TEMPLATE. Plan A creates the skeleton; validation results are operator-action handoff (per CONTEXT.md TRANS-07 lock — NOT auto-run).

---

### `tests/test_p09_transition_unit.py` (test, event-driven — NEW goal-content assertion)

**Analog:** `tests/test_p09_unit.py:56-63, 159-184` (`_make_delegate_spy` + `captured["goal"]` assertion — exact pattern)

**sys.path bootstrap + spy pattern** (test_p09_unit.py:27-29, 56-63):
```python
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))


def _make_delegate_spy(captured: dict):
    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}
    return _mock
```

**Goal-content assertion pattern** (test_p09_unit.py:159-184 — `test_p09_goal_includes_cross_cutting_injection_instruction`):
```python
def test_p09_goal_includes_cross_cutting_injection_instruction():
    captured: dict = {}
    p09.run(
        episode_id="ep-009",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible",
            "character-assets", "style-vector", "color-intent"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "CROSS-CUTTING PARAMETER INJECTION" in captured["goal"], (
        "p09 goal must include cross-cutting injection instruction"
    )
    assert "character_refs" in captured["goal"]
    # ... one assert per MUST keyword
```

**Plan A test_p09_transition_unit.py — TRANSITION DESIGN assertion** (mirror the pattern):
```python
def test_p09_goal_includes_transition_design_instruction():
    """XCUT-02: goal MUST include TRANSITION DESIGN injection instruction."""
    captured: dict = {}
    p09.run(
        episode_id="ep-074",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible",
            "character-assets", "style-vector", "color-intent"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    goal = captured["goal"]
    assert "TRANSITION DESIGN" in goal, (
        f"p09 goal must include TRANSITION DESIGN injection instruction; got: {goal!r}"
    )
    assert "transition_method" in goal
    assert "visual_hook" in goal
    assert "camera_continuity" in goal
    # TRANS-02: structured next_shot_link (not bare string)
    assert "next_shot_link MUST be a structured object" in goal
    # TRANS-04 ownership
    assert "DO NOT emit execution fields" in goal
    # TRANS-06 routing table keywords
    assert "Wan2.2" in goal
    assert "ffmpeg xfade" in goal


def test_p09_writes_transition_design_slot():
    """TRANS-03: p09 writes transition-design slot (creative intent from cinematographer)."""
    written: dict = {}
    def write_spy(slot, entry):
        written[slot] = entry

    p09.run(
        episode_id="ep-074",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible",
            "character-assets", "style-vector", "color-intent"
        ) else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "transition-design" in written, (
        "p09 must write transition-design slot (TRANS-03 system 1)"
    )
```

**Context.md discretion alternative:** if planner prefers, EXTEND `test_p09_unit.py` with these 2 tests instead of creating a new file (per CONTEXT.md `## Claude's Discretion` — both are valid). Recommend new file for cleaner diff + per-requirement test isolation.

---

### `.planning/phases/74-transition/74-smoke.sh` (test/smoke, request-response — NEW bash runner)

**Analog (exact skeleton):** `.planning/phases/70-foundation-audit/70-smoke.sh` (80 lines) + Phase 71/72/73 smoke siblings (per 71/72/73-PATTERNS)

**Smoke script skeleton to mirror** (70-smoke.sh:1-18 — full skeleton, copy verbatim and substitute phase number):
```bash
#!/usr/bin/env bash
# Phase 74 TRANSITION smoke runner — N assertions. Usage: bash .planning/phases/74-transition/74-smoke.sh
set -euo pipefail
# Exits 0 only if all sub-claims pass. Hard-fails on first error, undefined var, or pipe failure.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 74 TRANSITION smoke — N assertions"
echo "Repo root: $REPO_ROOT"
echo "KHS root: $KHS_ROOT"
echo ""
```

**Per-assertion block pattern** (70-smoke.sh:20-25 — file-existence + grep-count + python-import assertions):
```bash
# TRANS-XXa: <description>
if [ ! -f "$TARGET_FILE" ]; then
    echo "FAIL: TRANS-XXa — <reason>"
    exit 1
fi
echo "OK: TRANS-XXa — <success>"

COUNT=$(grep -c 'pattern' "$FILE" || true)
if [ "$COUNT" -lt N ]; then
    echo "FAIL: TRANS-XXb — expected >=N, got $COUNT"
    exit 1
fi
echo "OK: TRANS-XXb — $COUNT entries (>= N)"
```

**Phase 74 smoke assertions to draft** (per RESEARCH.md §Validation Architecture → Test Map — 13+ smoke assertions):
- TRANS-01a: `grep -c "transition_method" $KHS_ROOT/skills/movie-experts/cinematographer/references/e-konte-format.md` returns `>= 1`
- TRANS-01b: `grep -c "12-value enum\|12-type taxonomy" $KHS_ROOT/skills/movie-experts/cinematographer/references/e-konte-format.md` returns `>= 1`
- TRANS-02a: `python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from transition_schema import load_next_shot_link; r = load_next_shot_link('shot_02'); assert r['transition_method'] == 'hard_cut'"`
- TRANS-02b: `python3 -c "...from transition_schema import _TRANSITION_METHOD_SET; assert len(_TRANSITION_METHOD_SET) == 12"`
- TRANS-03a: `python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from asset_bus import ASSET_SCHEMA; assert 'transition-design' in ASSET_SCHEMA"`
- TRANS-03b: `grep -c "transition_design" $KHS_ROOT/plugins/kais_aigc/canvas_sync.py` returns `>= 1`
- TRANS-04a: `grep -c "transition_method\|visual_hook\|camera_continuity" $KHS_ROOT/skills/movie-experts/cinematographer/SKILL.md` returns `>= 1`
- TRANS-04b: `grep -c "cut_duration_frames\|dissolve_curve\|match_cut_alignment_point" $KHS_ROOT/skills/movie-experts/editor/SKILL.md` returns `>= 1`
- TRANS-05a: `test -f $KHS_ROOT/skills/movie-experts/cinematographer/references/transition-design.md`
- TRANS-05b: `grep -c "match_cut_shared_object\|whip_pan\|j_cut" $KHS_ROOT/skills/movie-experts/cinematographer/references/transition-design.md` returns `>= 3`
- TRANS-06a: `test -f $KHS_ROOT/skills/kais-movie-pipeline/references/transition-engine-routing.md`
- TRANS-06b: `grep -c "Wan2.2" $KHS_ROOT/skills/kais-movie-pipeline/references/transition-engine-routing.md` returns `>= 1`
- TRANS-06c: `grep -c "ffmpeg xfade" $KHS_ROOT/skills/kais-movie-pipeline/references/transition-engine-routing.md` returns `>= 1`
- TRANS-07a: `test -f $KHS_ROOT/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md`
- TRANS-07b: `grep -c "ICLoRA" $KHS_ROOT/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md` returns `>= 1`
- XCUT-02a: `grep -c "_TRANSITION_DESIGN_INSTRUCTION" $KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` returns `>= 1`
- XCUT-02b: `grep -c "_EDITOR_TRANSITION_EXECUTION_INSTRUCTION" $KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py` returns `>= 1`

Plus a final line: `echo "Phase 74 smoke status: ALL N ASSERTIONS PASSED"`.

**Note:** the bash smoke runner does NOT invoke live Docker / ComfyUI / Wan2.2 / Hailuo / Vidu (those are operator-action handoff per XCUT-04b). Live integration probes are documented in `transition-engine-routing.md` for operator pre-flight use.

---

## Shared Patterns

### Pydantic Literal Strict Enum + frozenset Validator (TRANS-01)
**Source:** `store.py:79` (`form_factor: Literal["landscape", "portrait"]` + `__post_init__` enforcement) + `store.py:150` (`TTS_ENGINE_VALUES = frozenset(...)`) + `store.py:153-210` (`validate_tts_engine_division`)
**Apply to:** `transition_schema.py` `_TRANSITION_METHOD_SET` + `_CAMERA_CONTINUITY_SET` + `load_next_shot_link()`
**Core invariant:** 3-phase precedent (FORM-01 form_factor → DUB-02 tts_engine → TRANS-01 transition_method/camera_continuity): `Literal[...]` for type-checker hints + module-level `frozenset({...})` for runtime O(1) membership test + standalone validator function raising `ValueError` with `(TRANS-XX strict enum — no fuzzy matching)` audit suffix.

### Backward-Compat Reader (TRANS-02)
**Source:** `dub_validators.py:24-80` (`validate_voice_clone_ref` — `.get(key, default)` coercion) + `store.py:81-94` (`form_factor` `__post_init__` defaults to `"portrait"` for old state files)
**Apply to:** `transition_schema.py::load_next_shot_link(value)`
**Core invariant:** Old episode JSON without the new field loads cleanly via:
1. `isinstance(value, str)` → coerce to structured default (legacy `next_shot_link: "shot_02"` → `{shot_id: "shot_02", transition_method: "hard_cut", ...}`)
2. `isinstance(value, dict)` → validate via TRANS-01 enum sets
3. Neither → raise `TypeError` with audit suffix
Zero migration script needed — backward-compat reader handles any legacy form at read time.

### Asset-Bus Slot Registration (TRANS-03 system 1)
**Source:** `asset_bus.py:223-236` (`shot-list` + `e-konte-sheets` slots — Phase 36-02 p09 sibling pattern)
**Apply to:** `transition-design` slot addition
**Core invariant:** kebab-case slot name + `format: "json"` envelope-wrapped + `writer_phase` / `reader_phases` declared + append-only to `ASSET_SCHEMA` dict (existing slots byte-equivalent per D-36-05).

### Canvas Sync `_PHASE_OUTPUT_MAP` (TRANS-03 system 2)
**Source:** `canvas_sync.py:1676-1764` (`_PHASE_OUTPUT_MAP` dict + 4-tuple schema `(output_key, label, canvas_type, expand_subkeys)`)
**Apply to:** `transition_design` tuple added to `"p09"` entry
**Core invariant:** Reuse `canvas_type="storyboard"` (zero frontend change — PITFALL T-4 mitigation #1; the frontend zod schema has 5 node types with no "transition" type). Tuple order MUST match `(output_key, label, canvas_type, expand_subkeys)`.

### Frontend Zod Reuse Decision (TRANS-03 system 3 — PITFALL T-4)
**Source:** RESEARCH.md §System Architecture Diagram + §Pitfall 1 + §Assumption A1
**Apply to:** ALL canvas node registrations in v14.0
**Core invariant:** The frontend zod schema (`canvasAssetSchema.ts`) defines 5 node types (audio/video/asset/storyboard/script). NO new "transition" type is added in v14.0. `transition_design` reuses `storyboard` canvas_type (shares p09's pre-production storyboard semantic — no media). v15+ may add a distinct "transition" React Flow nodeType if operator requests visual separation.

### XCUT-02 `_INSTRUCTION` Constant Injection (META-RULE X-2 — 4-phase precedent)
**Source:** `p09_shot_breakdown.py:51-70, 80-89` (`_CROSS_CUTTING_INSTRUCTION` + `_FORM_FACTOR_INSTRUCTION`) + Phase 72 `p10_voice.py` `_TTS_ENGINE_INSTRUCTION` + Phase 73 `p07_scene_generation.py` `_VISION_VERIFY_INSTRUCTION`
**Apply to:** `_TRANSITION_DESIGN_INSTRUCTION` in p09 + `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` in p13
**Core invariant (3-site injection):**
1. Define `_SOME_INSTRUCTION = "..."` constant with MUST/MANDATORY keyword at module top
2. Inject via `.task(steps=[f"{_SOME_INSTRUCTION}", ...])` AND a parallel `.constraints(["MUST ..."])` line
3. Assert via `test_*_unit.py` `captured["goal"]` goal-content test
Without all 3 sites, the rule is invisible to the subagent at runtime (subagents see ONLY the goal string, NOT SKILL.md).

### MAX_CONSTRAINTS=7 Budget Consolidation (p09)
**Source:** `p09_shot_breakdown.py:396-404` (6 current constraints including `fix_feedback` placeholder) + RESEARCH.md §Pitfall 2 + §Assumption A2 + Phase 71 STATE.md decision log
**Apply to:** `_TRANSITION_DESIGN_INSTRUCTION` constraint addition in p09
**Core invariant:** p09 is at 6/7 constraints. Adding 1 = 7 (at limit). Plan A consolidates the transition_method MUST with the existing consolidated constraint #3 (form_factor + cross-cutting params — both are Layer 5 E-Konte fields, semantically cohesive). Alternative: migrate constraint #5 to `.task(steps=[...])` (task steps are NOT budget-counted). Planner picks.

### Editor Step 7 vs Step 13 Disambiguation (TRANS-04 — PITFALL 4)
**Source:** RESEARCH.md §Pitfall 4 + §Assumption A5
**Apply to:** BOTH `editor/SKILL.md` Workflow Step 7 AND `p13_delivery.py` line 89
**Core invariant:** "Step 13" in TRANS-04 refers to the **pipeline phase** `p13_delivery.py` (line 89: editor performs final-cut + render), which corresponds to editor SKILL.md Workflow Steps 7-13 collectively. Both locations need ownership documentation:
- `editor/SKILL.md` Workflow Step 7 (Transition Design — reads `transition-design` slot, validates against FxRxT matrix)
- `p13_delivery.py` (execution — emits `cut_duration_frames` / `dissolve_curve` / `match_cut_alignment_point`)

### ffmpeg xfade Availability (TRANS-06)
**Source:** RESEARCH.md §Standard Stack (verified ffmpeg 6.1.1-3ubuntu5 in Docker stack + xfade filter supported via `ffmpeg -h filter=xfade`)
**Apply to:** `transition-engine-routing.md` routing table for `dissolve` / `wipe` / `fade` / `j_cut` / `l_cut` / `color_match` / `whip_pan` rows
**Core invariant:** ffmpeg 6.1.1 + xfade filter is the post-production fallback for 7 of the 12 transition_method values. Zero new Docker deps; deterministic + GPU-free.

### Ref Twin Authoring (transition-design.md + transition-engine-routing.md + ltx-flf-iclora-validation.md)
**Source:** `e-konte-format.md` (5-layer schema doc twin for transition-design.md) + `video-engine-comparison.md` (engine-comparison twin for transition-engine-routing.md — 15 LTX/Wan/Hailuo/Vidu references verified) + `audio_pipeline/references/voicer/cosyvoice-benchmark.md` per 72-PATTERNS (template-with-placeholders twin for ltx-flf-iclora-validation.md)
**Apply to:** All 3 new refs
**Core invariant:** Header block (Source / Copyright / Last-verified / verified_date per 71/72/73-PATTERNS established convention) + structural twin of the closest existing ref + per-section content depth matching the twin.

### SKILL.md Body Edit (FOUND-08 frontmatter freeze)
**Source:** `_shared/SKILL-LAYOUT.md` + CLAUDE.md §Skill File Conventions + Phase 71/72/73 precedent
**Apply to:** `cinematographer/SKILL.md` Step 9 + ownership subsection AND `editor/SKILL.md` Workflow Step 7 + ownership subsection
**Core invariant:** YAML frontmatter (`name` / `description` / `tags` / `related_skills` / `expert_id` / `metrics`) is FROZEN byte-identical. Edit body prose only. Insert inline near the relevant step; do not restructure H2 headings.

### Goal-Content Test Assertion
**Source:** `tests/test_p09_unit.py:56-63, 159-184` + Phase 71 `test_form_factor.py` + Phase 72 `test_dub_division.py` + Phase 73 `test_img_integration.py`
**Apply to:** `test_p09_transition_unit.py::test_p09_goal_includes_transition_design_instruction`
**Core invariant:**
```python
captured: dict = {}
p09.run(..., delegate_task=_make_delegate_spy(captured), ...)
assert "TRANSITION DESIGN" in captured["goal"]
assert "transition_method" in captured["goal"]
assert "MUST emit per-shot transition_method" in captured["goal"]
```
One test function per MUST keyword; all run under 2s; no Docker, no network.

### Smoke Script grep/file Assertions
**Source:** `.planning/phases/70-foundation-audit/70-smoke.sh` (80 lines) + `.planning/phases/71-form/71-smoke.sh` + `.planning/phases/72-dub/72-smoke.sh` + `.planning/phases/73-img/73-smoke.sh`
**Apply to:** `.planning/phases/74-transition/74-smoke.sh`
**Core invariant:** `set -euo pipefail` + `SCRIPT_DIR` / `REPO_ROOT` / `KHS_ROOT` resolution via `BASH_SOURCE` + per-assertion block (grep-count OR file-existence OR python-import check) + final `echo "ALL N ASSERTIONS PASSED"`. Exits non-zero on first failure. Does NOT invoke live Docker / Wan2.2 / Hailuo / Vidu (those are operator-action probes documented in transition-engine-routing.md).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `transition-design.md` (12-type taxonomy body content) | reference-doc | file-I/O | Structural twin (`e-konte-format.md` + `video-engine-comparison.md`) IS the analog for structure, but the 12-type taxonomy content is greenfield — no existing ref documents per-transition-type sections with Definition / When-to-use / Execution-path classification / Concrete film examples / Engine routing cross-ref. Planner uses CONTEXT.md TRANS-05 structure + RESEARCH.md §Code Examples TRANS-06 routing table directly. Film citations under fair-use with attribution per CLAUDE.md. |
| `ltx-flf-iclora-validation.md` (validation results body content) | reference-doc | file-I/O | Template skeleton only — actual A/B validation results are operator-action handoff (TRANS-07 locked decision: research-scope validation, operator runs the actual shots). Planner uses RESEARCH.md TRANS-07 + §Open Question #2 + §Code Examples §LTX-FLF vs ICLoRA conflation directly. Data is deferred (operator fills at validation time). |

## Metadata

**Analog search scope:**
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/dub_validators.py` (full read, 80 lines — exact sibling module layout twin for transition_schema.py)
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py` (targeted read, lines 1-220 — form_factor __post_init__ + TTS_ENGINE_VALUES + validate_tts_engine_division + _STATE_FIELDS pattern)
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/asset_bus.py` (targeted read, lines 1-280 — ASSET_SCHEMA slot-addition pattern; e-konte-sheets p09 sibling)
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/tests/test_asset_bus_phase35_slots.py` (full read, 180+ lines — slot-registered assertion + test_total_slot_count_at_least_10 pattern)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/canvas_sync.py` (targeted read, lines 1670-1780 — _PHASE_OUTPUT_MAP dict + 4-tuple schema + _ARTIFACT_LIST_KEYS)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` (full read, 491 lines — 6 _INSTRUCTION constants + GoalBuilder chain + 6 current constraints + asset_bus_write site)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py` (targeted read, lines 1-160 — 3-expert GoalBuilder chain + INPUT_SLOTS + constraint block)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` (targeted read, lines 180-240 — Step 9 procedure sub-step 5)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/editor/SKILL.md` (targeted read, lines 115-225 — Transition Parameters + Workflow Steps 7 + 13 + Collaboration)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md` (targeted reads, lines 110-150 + 270-330 — Layer 5 schema + Output Schema)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/asset-bus-schema.md` (targeted read, lines 1-90 — slot table reference + slot count verification via grep)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_unit.py` (targeted reads, lines 50-110 + 158-260 — _make_delegate_spy + goal-content assertion pattern + write_spy)
- `/data/workspace/hermes-agent/.planning/phases/70-foundation-audit/70-smoke.sh` (full read, 80 lines — smoke skeleton)
- `/data/workspace/hermes-agent/.planning/phases/71-form/71-PATTERNS.md` (full read — XCUT-02 _INSTRUCTION 3-phase precedent + smoke assertion drafting pattern)
- `/data/workspace/hermes-agent/.planning/phases/72-dub/72-PATTERNS.md` (full read — DUB-02 validate_tts_engine_division sibling + cosyvoice-benchmark.md template-with-placeholders pattern)
- `/data/workspace/hermes-agent/.planning/phases/73-img/73-PATTERNS.md` (full read — IMG-03 vision_verify sibling + ref-authoring pattern)
- `grep -c "next_shot_link" /data/workspace/kais-hermes-skills --include="*.py"` (0 hits — verified next_shot_link is doc-only, NOT a code migration)
- `grep -c "^| \`" asset-bus-schema.md` (35 slots — slot count verified)
- `grep -c "Wan2.2\|ffmpeg xfade\|LTX" video-engine-comparison.md` (15 hits — ref-doc twin verified)

**Files scanned:** 13 primary reads + 3 grep verification probes
**Pattern extraction date:** 2026-07-09
