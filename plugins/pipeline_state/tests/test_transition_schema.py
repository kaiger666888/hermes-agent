"""test_transition_schema.py — Phase 74-01 Tasks 1+2 (TDD RED→GREEN).

Verifies the TRANS-01 (12-enum transition_method + 6-enum camera_continuity)
and TRANS-02 (backward-compat next_shot_link reader) contracts authored in
``plugins/pipeline_state/transition_schema.py``; plus the TRANS-03
3-system registration (ASSET_SCHEMA slot + canvas_sync _PHASE_OUTPUT_MAP
tuple) authored in ``asset_bus.py`` + ``canvas_sync.py``.

Test layout mirrors Phase 72's ``test_dub_division.py`` (enum rejection
pattern) + Phase 71's ``test_form_factor.py`` (default preservation) + Phase
35's ``test_asset_bus_phase35_slots.py`` (slot-registered assertion).

Per CLAUDE.md Code Style: ``from __future__ import annotations`` + PEP 604
unions + Ruff PLW1514 compliant (no open() in this file — pure function
tests).
"""

from __future__ import annotations

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA
from plugins.pipeline_state.transition_schema import (
    _CAMERA_CONTINUITY_SET,
    _TRANSITION_METHOD_SET,
    load_next_shot_link,
)


# ═══════════════════════════════════════════════════════════════════
# TRANS-02: backward-compat next_shot_link reader behavior
# ═══════════════════════════════════════════════════════════════════
def test_load_string_next_shot_link():
    """TRANS-02: legacy string next_shot_link coerces to structured default.

    Validates VALIDATION 74-01-03: load_next_shot_link("shot_02") returns
    the structured default with shot_id="shot_02" + safe defaults
    (hard_cut / none / None / None).
    """
    result = load_next_shot_link("shot_02")
    assert result == {
        "shot_id": "shot_02",
        "transition_method": "hard_cut",
        "visual_hook": None,
        "camera_continuity": "none",
        "generation_path": None,
    }


def test_load_structured_next_shot_link():
    """TRANS-02: dict next_shot_link passes through with defaults filled.

    Validates VALIDATION 74-01-04: structured form validates and unfilled
    fields default to safe values (camera_continuity="none", etc.).
    """
    result = load_next_shot_link({"shot_id": "s3", "transition_method": "dissolve"})
    assert result["shot_id"] == "s3"
    assert result["transition_method"] == "dissolve"
    assert result["camera_continuity"] == "none"
    assert result["visual_hook"] is None
    assert result["generation_path"] is None


def test_load_next_shot_link_rejects_invalid_transition_method():
    """TRANS-01: invalid transition_method raises ValueError with audit suffix.

    The "(TRANS-01 strict enum ...)" suffix is grep-auditable traceability —
    mirrors the DUB-02 / FORM-01 audit-suffix convention.
    """
    with pytest.raises(ValueError, match="TRANS-01 strict enum"):
        load_next_shot_link({"shot_id": "s1", "transition_method": "fake_transition"})


def test_load_next_shot_link_rejects_invalid_camera_continuity():
    """TRANS-01: invalid camera_continuity raises ValueError with audit suffix."""
    with pytest.raises(ValueError, match="TRANS-01 strict enum"):
        load_next_shot_link({"shot_id": "s1", "camera_continuity": "fake_continuity"})


def test_load_next_shot_link_rejects_missing_shot_id():
    """WR-02: dict without shot_id raises ValueError (fail-fast).

    Previously ``value.get("shot_id")`` silently returned None, violating
    the implicit type contract that shot_id is always a string. The docstring
    claims fail-fast behavior — this test enforces it for the missing-key
    case.
    """
    with pytest.raises(ValueError, match="non-empty string shot_id"):
        load_next_shot_link({"transition_method": "dissolve"})


def test_load_next_shot_link_rejects_none_shot_id():
    """WR-02: dict with shot_id=None raises ValueError (fail-fast)."""
    with pytest.raises(ValueError, match="non-empty string shot_id"):
        load_next_shot_link({"shot_id": None, "transition_method": "dissolve"})


def test_load_next_shot_link_rejects_empty_shot_id():
    """WR-02: dict with shot_id='' raises ValueError (fail-fast)."""
    with pytest.raises(ValueError, match="non-empty string shot_id"):
        load_next_shot_link({"shot_id": "", "transition_method": "dissolve"})


def test_load_next_shot_link_rejects_non_str_non_dict():
    """TRANS-02: neither str nor dict raises TypeError with audit suffix.

    int / list / None are all rejected — no silent fuzzy coercion.
    """
    with pytest.raises(TypeError, match="TRANS-02 strict type"):
        load_next_shot_link(42)
    with pytest.raises(TypeError, match="TRANS-02 strict type"):
        load_next_shot_link(["shot_02"])
    with pytest.raises(TypeError, match="TRANS-02 strict type"):
        load_next_shot_link(None)


# ═══════════════════════════════════════════════════════════════════
# TRANS-01: enum set sanity (Literal is type-checker only; frozenset is
# the runtime authority)
# ═══════════════════════════════════════════════════════════════════
def test_transition_method_enum_has_12_values():
    """TRANS-01: 12-value enum per REQUIREMENTS.md line 41.

    Validates VALIDATION 74-01-01: strict Pydantic Literal schema enforces
    exactly the 12 industry-standard transition types.
    """
    assert len(_TRANSITION_METHOD_SET) == 12
    # Sanity-check key values from REQUIREMENTS.md TRANS-01.
    for required in ("hard_cut", "match_cut_shared_object", "whip_pan", "none"):
        assert required in _TRANSITION_METHOD_SET, (
            f"transition_method enum missing required value: {required!r}"
        )


def test_camera_continuity_enum_has_6_values():
    """TRANS-01: 6-value camera_continuity enum per REQUIREMENTS.md line 41.

    Validates VALIDATION 74-01-02: strict Pydantic Literal schema enforces
    exactly the 6 camera-continuity options.
    """
    assert len(_CAMERA_CONTINUITY_SET) == 6
    for required in ("pan_to", "match_cut_on_motion", "none"):
        assert required in _CAMERA_CONTINUITY_SET, (
            f"camera_continuity enum missing required value: {required!r}"
        )


# ═══════════════════════════════════════════════════════════════════
# TRANS-03: ASSET_SCHEMA slot registration (system 1 of 3)
# ═══════════════════════════════════════════════════════════════════
def test_asset_bus_slot_registered():
    """TRANS-03 system 1: ASSET_SCHEMA contains the transition-design slot.

    Validates VALIDATION 74-01-05: the kebab-case slot name
    "transition-design" is registered (mirroring "shot-list" +
    "e-konte-sheets" convention per D-04).
    """
    assert "transition-design" in ASSET_SCHEMA, (
        f"transition-design slot not registered in ASSET_SCHEMA; "
        f"got keys={sorted(ASSET_SCHEMA.keys())}"
    )


def test_transition_design_slot_format_json():
    """TRANS-03: slot format is json (envelope-wrapped atomic write)."""
    assert ASSET_SCHEMA["transition-design"].get("format") == "json"


def test_transition_design_slot_writer_phase_p09():
    """TRANS-04 ownership: writer_phase = p09 (cinematographer Step 9).

    Cinematographer writes creative intent (transition_method / visual_hook
    / camera_continuity); editor at p13 reads it for post-production
    execution. The ownership split is encoded in the slot registry.
    """
    assert ASSET_SCHEMA["transition-design"]["writer_phase"] == "p09_shot_breakdown"


def test_transition_design_slot_reader_phase_p13():
    """TRANS-04 ownership: transition-design readers are p12a/p12b (p13 dropped).

    p13_delivery no longer reads transition-design directly — it now reads
    transitions from the master-timeline EDL (commit a299837). The readers are
    p11a_preview_clips / p12a_timeline_composition / p12b_audio_composition
    (the phases that consume transition cues for preview/timeline/audio).
    """
    readers = ASSET_SCHEMA["transition-design"]["reader_phases"]
    assert "p12b_audio_composition" in readers, (
        f"p12b_audio_composition not in transition-design reader_phases; got {readers!r}"
    )
    assert "p13_delivery" not in readers, (
        f"p13_delivery should no longer read transition-design (uses EDL); got {readers!r}"
    )


def test_backward_compat_string_next_shot_link():
    """TRANS-02 legacy episode smoke: pre-v14.0 layer_5 with bare-string
    next_shot_link loads cleanly via load_next_shot_link coercion.

    Validates VALIDATION 74-03-02: no migration script needed — the
    backward-compat reader handles any legacy form at read time. Mirrors
    the DUB-02 .get(key, default) coercion precedent.
    """
    legacy_layer_5 = {
        "duration_sec": 3.2,
        "frame_count": 77,
        "fps": 24,
        "cut_transition_type": "hard_cut",  # legacy 4-value field
        "next_shot_link": "shot_02",  # legacy bare-string form
    }
    coerced = load_next_shot_link(legacy_layer_5["next_shot_link"])
    assert coerced["shot_id"] == "shot_02"
    assert coerced["transition_method"] == "hard_cut"  # safe default
    assert coerced["camera_continuity"] == "none"
