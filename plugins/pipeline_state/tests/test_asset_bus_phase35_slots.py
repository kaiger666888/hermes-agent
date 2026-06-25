"""test_asset_bus_phase35_slots.py — Phase 35-02 Task 1 (TDD RED→GREEN).

Verifies the 6 new phase-output slots registered in ASSET_SCHEMA per D-35-05:

* requirement / topic-kernel / hook-design / story-framework /
  script-draft / audit-report

The original 4 Phase 33 slots MUST remain unchanged — that's verified by
running the existing ``test_asset_bus.py`` (Phase 33 regression) alongside.

Test layout mirrors Phase 33's test_asset_bus.py (pytest class groups +
``tmp_path`` isolation + envelope round-trip). All new slots are JSON format
(envelope-wrapped, atomic write).
"""

from __future__ import annotations

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA, AssetBus, AssetBusError


# The 6 new Phase 35 phase-output slots (D-35-05).
PHASE35_NEW_SLOTS = (
    "requirement",
    "topic-kernel",
    "hook-design",
    "story-framework",
    "script-draft",
    "audit-report",
)

# The 4 original Phase 33 slots that MUST remain byte-equivalent.
PHASE33_ORIGINAL_SLOTS = (
    "creative-history",
    "failed-shots",
    "finetune-dataset",
    "review-outcomes",
)


# ═══════════════════════════════════════════════════════════════════
# Test 1: write + read each new slot via envelope round-trip
# ═══════════════════════════════════════════════════════════════════
class TestPhase35NewSlotsRoundTrip:
    @pytest.mark.parametrize("slot", PHASE35_NEW_SLOTS)
    def test_write_read_envelope_roundtrip(self, tmp_path, slot):
        """Envelope-wrapped write then read returns the original payload."""
        bus = AssetBus(str(tmp_path))
        payload = {"slot_name": slot, "title": "测试-" + slot, "n": 42}
        path = bus.write(slot, payload, envelope=True)

        assert path.endswith(".json")
        # read() auto-unwraps the envelope → returns the raw payload
        result = bus.read(slot)
        assert result == payload

    @pytest.mark.parametrize("slot", PHASE35_NEW_SLOTS)
    def test_write_then_read_preserves_nested_struct(self, tmp_path, slot):
        """Nested arrays/dicts survive round-trip for each new slot."""
        bus = AssetBus(str(tmp_path))
        payload = {
            "topic": "灵活就业者",
            "anchors": [{"id": 1, "label": "情绪钩"}, {"id": 2}],
            "meta": {"tags": ["a", "b"], "count": 2},
        }
        bus.write(slot, payload, envelope=True)
        assert bus.read(slot) == payload

    @pytest.mark.parametrize("slot", PHASE35_NEW_SLOTS)
    def test_read_returns_none_for_empty_slot(self, tmp_path, slot):
        """Unwritten new slot reads as None (no spurious file)."""
        bus = AssetBus(str(tmp_path))
        assert bus.read(slot) is None


# ═══════════════════════════════════════════════════════════════════
# Test 2: original 4 Phase 33 slots still work (smoke regression —
# full Phase 33 suite is also re-run separately).
# ═══════════════════════════════════════════════════════════════════
class TestPhase33SlotsPreserved:
    @pytest.mark.parametrize("slot", PHASE33_ORIGINAL_SLOTS)
    def test_original_slot_still_registered(self, slot):
        assert slot in ASSET_SCHEMA, f"Phase 33 slot {slot} removed — REGRESSION"

    def test_creative_history_round_trip(self, tmp_path):
        bus = AssetBus(str(tmp_path))
        payload = {"shots": [], "version": 1}
        bus.write("creative-history", payload, envelope=True)
        assert bus.read("creative-history") == payload

    def test_failed_shots_round_trip(self, tmp_path):
        bus = AssetBus(str(tmp_path))
        payload = {"failures": [], "version": 1}
        bus.write("failed-shots", payload, envelope=True)
        assert bus.read("failed-shots") == payload

    def test_review_outcomes_round_trip(self, tmp_path):
        bus = AssetBus(str(tmp_path))
        payload = {"gate_id": "g1", "outcome": "approved"}
        bus.write("review-outcomes", payload, envelope=True)
        assert bus.read("review-outcomes") == payload

    def test_finetune_dataset_append_and_read(self, tmp_path):
        """JSONL slot still uses append_line / read_lines."""
        bus = AssetBus(str(tmp_path))
        bus.append_line("finetune-dataset", {"id": 1})
        bus.append_line("finetune-dataset", {"id": 2})
        assert bus.read_lines("finetune-dataset") == [{"id": 1}, {"id": 2}]


# ═══════════════════════════════════════════════════════════════════
# Test 3: writing to an unknown slot name still raises AssetBusError
# ═══════════════════════════════════════════════════════════════════
class TestUnknownSlotStillRaises:
    def test_write_unknown_slot_raises(self, tmp_path):
        bus = AssetBus(str(tmp_path))
        with pytest.raises(AssetBusError):
            bus.write("not-a-real-slot", {"x": 1})

    def test_read_unknown_slot_raises(self, tmp_path):
        bus = AssetBus(str(tmp_path))
        with pytest.raises(AssetBusError):
            bus.read("not-a-real-slot")

    def test_unknown_slot_does_not_silently_pass(self, tmp_path):
        """Regression: typo'd slot names must fail loud, not no-op."""
        bus = AssetBus(str(tmp_path))
        # Close-but-not-quite typos that should all raise:
        for typo in ("topic_kernel", "topicKernel", "Topic-Kernel", "topics-kernel"):
            with pytest.raises(AssetBusError):
                bus.write(typo, {"x": 1})


# ═══════════════════════════════════════════════════════════════════
# Test 4: new slots appear in ASSET_SCHEMA with format="json"
# ═══════════════════════════════════════════════════════════════════
class TestNewSlotsSchemaMetadata:
    @pytest.mark.parametrize("slot", PHASE35_NEW_SLOTS)
    def test_slot_registered(self, slot):
        assert slot in ASSET_SCHEMA, f"new slot {slot} not registered"

    @pytest.mark.parametrize("slot", PHASE35_NEW_SLOTS)
    def test_slot_format_is_json(self, slot):
        assert ASSET_SCHEMA[slot].get("format") == "json", (
            f"slot {slot} must be JSON (envelope-wrapped); "
            f"got {ASSET_SCHEMA[slot].get('format')!r}"
        )

    @pytest.mark.parametrize("slot", PHASE35_NEW_SLOTS)
    def test_slot_filename_is_json(self, slot):
        fname = ASSET_SCHEMA[slot].get("file", "")
        assert fname.endswith(".json"), (
            f"slot {slot} file must end in .json; got {fname!r}"
        )

    def test_total_slot_count_is_10(self):
        """4 Phase 33 slots + 6 Phase 35 additions = 10 total."""
        assert len(ASSET_SCHEMA) == 10, (
            f"expected 10 slots (4+6), got {len(ASSET_SCHEMA)}; "
            f"keys={sorted(ASSET_SCHEMA.keys())}"
        )

    def test_jsonl_slots_unchanged(self):
        """finetune-dataset remains the only JSONL slot (Phase 33 contract)."""
        jsonl = [s for s, cfg in ASSET_SCHEMA.items() if cfg.get("format") == "jsonl"]
        assert jsonl == ["finetune-dataset"], (
            f"JSONL slot set drifted: {jsonl}"
        )
