"""test_asset_bus_emotion_recipe_slot.py — Phase 41-01 Task 1 (TDD RED→GREEN).

Verifies the new ``emotion-recipe`` AssetBus JSONL slot registered in
ASSET_SCHEMA per plan 41-01. Append-only extension (D-36-05 invariant):
all existing V5.0 + Phase 40 slots MUST remain byte-equivalent.

Tests:
  1. emotion-recipe slot is registered in ASSET_SCHEMA
  2. slot metadata (file/format/writer_phase/reader_phases) matches blueprint
  3. V5.0+Phase40 slots byte-equivalent — REGRESSION GUARD (hardcoded snapshot)
  4. AssetBus.JSONL_SLOTS frozenset UNCHANGED (D-36-05) — emotion-recipe NOT added
  5. round-trip via append_line / read_lines preserves insertion order
  6. write() raises AssetBusError for the jsonl slot
  7. read() raises AssetBusError for the jsonl slot
  8. empty slot reads as [] when no file exists yet
"""

from __future__ import annotations

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA, AssetBus, AssetBusError


# ═══════════════════════════════════════════════════════════════════
# Test 1 + 2: emotion-recipe slot registered + metadata correct
# ═══════════════════════════════════════════════════════════════════
class TestEmotionRecipeSlotRegistered:
    def test_slot_registered(self):
        """emotion-recipe key exists in ASSET_SCHEMA."""
        assert "emotion-recipe" in ASSET_SCHEMA, (
            "emotion-recipe slot missing from ASSET_SCHEMA — "
            "Task 1 GREEN not yet applied"
        )

    def test_slot_file_metadata(self):
        assert ASSET_SCHEMA["emotion-recipe"]["file"] == "emotion-recipe.jsonl"

    def test_slot_format_is_jsonl(self):
        assert ASSET_SCHEMA["emotion-recipe"]["format"] == "jsonl"

    def test_slot_writer_phase(self):
        """writer_phase MUST be 'recipe_library' (Phase 41 owns the slot)."""
        assert ASSET_SCHEMA["emotion-recipe"]["writer_phase"] == "recipe_library"

    def test_slot_reader_phases_empty(self):
        """reader_phases is empty per blueprint Out of Scope."""
        assert ASSET_SCHEMA["emotion-recipe"]["reader_phases"] == []


# ═══════════════════════════════════════════════════════════════════
# Test 3: V5.0 + Phase 40 slots byte-equivalent (REGRESSION GUARD)
# Hardcoded snapshot of {slot: {"file": ..., "format": ...}} from
# pre-Phase-41 asset_bus.py. Any drift fails the test.
# ═══════════════════════════════════════════════════════════════════
PRE_PHASE_41_SLOT_SNAPSHOT: dict[str, dict[str, str]] = {
    # Phase 33 — original 4 typed slots
    "creative-history": {"file": "creative-history.json", "format": "json"},
    "failed-shots": {"file": "failed-shots.json", "format": "json"},
    "finetune-dataset": {"file": "finetune-dataset.jsonl", "format": "jsonl"},
    "review-outcomes": {"file": "review-outcomes.json", "format": "json"},
    # Phase 35 — 6 phase-output slots
    "requirement": {"file": "requirement.json", "format": "json"},
    "topic-kernel": {"file": "topic-kernel.json", "format": "json"},
    "hook-design": {"file": "hook-design.json", "format": "json"},
    "story-framework": {"file": "story-framework.json", "format": "json"},
    "script-draft": {"file": "script-draft.json", "format": "json"},
    "audit-report": {"file": "audit-report.json", "format": "json"},
    # Phase 36-01 — p04/p05/p06
    "character-bible": {"file": "character-bible.json", "format": "json"},
    "character-assets": {"file": "character-assets.json", "format": "json"},
    "pain-points": {"file": "pain-points.json", "format": "json"},
    "escalation-ladder": {"file": "escalation-ladder.json", "format": "json"},
    "spatio-temporal-script": {"file": "spatio-temporal-script.json", "format": "json"},
    "final-audit": {"file": "final-audit.json", "format": "json"},
    # Phase 36-02 — p07/p08/p09
    "scene-images": {"file": "scene-images.json", "format": "json"},
    "style-vector": {"file": "style-vector.json", "format": "json"},
    "color-intent": {"file": "color-intent.json", "format": "json"},
    "scene-selection": {"file": "scene-selection.json", "format": "json"},
    "geometry-bed": {"file": "geometry-bed.json", "format": "json"},
    "shot-list": {"file": "shot-list.json", "format": "json"},
    "e-konte-sheets": {"file": "e-konte-sheets.json", "format": "json"},
    # Phase 36-03 — p10/p11
    "voice-clips": {"file": "voice-clips.json", "format": "json"},
    "voice-timeline": {"file": "voice-timeline.json", "format": "json"},
    "video-clips": {"file": "video-clips.json", "format": "json"},
    "lip-sync-reports": {"file": "lip-sync-reports.json", "format": "json"},
    # Phase 36-04 — p12/p13
    "master-timeline": {"file": "master-timeline.json", "format": "json"},
    "audio-stems": {"file": "audio-stems.json", "format": "json"},
    "master-mp4": {"file": "master-mp4.json", "format": "json"},
    "delivery-package": {"file": "delivery-package.json", "format": "json"},
    # Phase 40-01 — p10b
    "rapid-preview-clips": {"file": "rapid-preview-clips.jsonl", "format": "jsonl"},
    "episode-meta": {"file": "episode-meta.json", "format": "json"},
}


class TestPrePhase41SlotsPreserved:
    @pytest.mark.parametrize("slot_name,expected", sorted(PRE_PHASE_41_SLOT_SNAPSHOT.items()))
    def test_pre_phase_41_slot_file_unchanged(self, slot_name: str, expected: dict):
        """Each V5.0 + Phase 40 slot retains its pre-Phase-41 file + format."""
        assert slot_name in ASSET_SCHEMA, (
            f"REGRESSION: pre-Phase-41 slot {slot_name!r} was removed"
        )
        actual_file = ASSET_SCHEMA[slot_name].get("file")
        actual_format = ASSET_SCHEMA[slot_name].get("format")
        assert actual_file == expected["file"], (
            f"REGRESSION: slot {slot_name!r} file changed "
            f"from {expected['file']!r} to {actual_file!r}"
        )
        assert actual_format == expected["format"], (
            f"REGRESSION: slot {slot_name!r} format changed "
            f"from {expected['format']!r} to {actual_format!r}"
        )

    def test_no_pre_phase_41_slot_removed(self):
        """All 32 pre-Phase-41 slots still present."""
        missing = [
            s for s in PRE_PHASE_41_SLOT_SNAPSHOT
            if s not in ASSET_SCHEMA
        ]
        assert not missing, f"pre-Phase-41 slots removed: {missing}"


# ═══════════════════════════════════════════════════════════════════
# Test 4: AssetBus.JSONL_SLOTS frozenset UNCHANGED (D-36-05)
# emotion-recipe is NOT added to JSONL_SLOTS — dispatch consults
# ASSET_SCHEMA[slot]["format"] directly, not the frozenset.
# ═══════════════════════════════════════════════════════════════════
class TestJsonlFrozensetUnchanged:
    def test_jsonl_slots_frozenset_unchanged(self):
        """JSONL_SLOTS frozenset MUST be exactly {finetune-dataset}.

        The frozenset is INFORMATIONAL ONLY — actual dispatch consults
        ASSET_SCHEMA[slot]["format"] directly. Keeping the frozenset
        unchanged preserves test_asset_bus.py::test_jsonl_slots_unchanged.
        Adding emotion-recipe here would be a violation of D-36-05.
        """
        assert AssetBus.JSONL_SLOTS == frozenset({"finetune-dataset"}), (
            f"JSONL_SLOTS drifted: {AssetBus.JSONL_SLOTS} — "
            "emotion-recipe must NOT be added (dispatch uses ASSET_SCHEMA format)"
        )

    def test_emotion_recipe_not_in_jsonl_slots(self):
        """Belt-and-suspenders: emotion-recipe explicitly excluded from frozenset."""
        assert "emotion-recipe" not in AssetBus.JSONL_SLOTS


# ═══════════════════════════════════════════════════════════════════
# Tests 5-8: emotion-recipe slot round-trip + dispatch behavior
# ═══════════════════════════════════════════════════════════════════
class TestEmotionRecipeSlotRoundTrip:
    def test_append_line_then_read_lines_preserves_order(self, tmp_path):
        """Two appends → read_lines returns both in insertion order."""
        bus = AssetBus(tmp_path)
        bus.append_line("emotion-recipe", {"recipe_id": "test-001", "v": 1})
        bus.append_line("emotion-recipe", {"recipe_id": "test-002", "v": 2})

        lines = bus.read_lines("emotion-recipe")
        assert len(lines) == 2
        assert lines[0] == {"recipe_id": "test-001", "v": 1}
        assert lines[1] == {"recipe_id": "test-002", "v": 2}

    def test_append_line_returns_jsonl_path(self, tmp_path):
        """append_line returns a path ending in emotion-recipe.jsonl."""
        bus = AssetBus(tmp_path)
        path = bus.append_line("emotion-recipe", {"x": 1})
        assert path.endswith("emotion-recipe.jsonl"), (
            f"append_line must return .jsonl path; got {path!r}"
        )

    def test_write_rejects_jsonl_slot(self, tmp_path):
        """write() must raise AssetBusError on jsonl slot — use append_line."""
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError, match="JSONL"):
            bus.write("emotion-recipe", {"recipe_id": "x"})

    def test_read_rejects_jsonl_slot(self, tmp_path):
        """read() must raise AssetBusError on jsonl slot — use read_lines."""
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError):
            bus.read("emotion-recipe")

    def test_empty_slot_reads_as_empty_list(self, tmp_path):
        """No file written yet → read_lines returns []."""
        bus = AssetBus(tmp_path)
        assert bus.read_lines("emotion-recipe") == []
