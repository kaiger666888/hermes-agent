"""test_asset_bus_feedback_slots.py - Phase 42-01 Task 1 (TDD RED->GREEN).

Verifies the 2 new AssetBus JSONL slots registered in ASSET_SCHEMA per plan
42-01: ``feedback-data`` and ``feedback-rejected``. Append-only extension
(D-36-05 invariant): all existing V5.0 + Phase 40 + Phase 41 slots MUST
remain byte-equivalent.

Tests (10 total):
  1-3. feedback-data slot metadata (file/format/writer_phase)
  4-6. feedback-rejected slot metadata (file/format/writer_phase)
  7.   AssetBus.JSONL_SLOTS frozenset UNCHANGED (D-36-05) - neither new
       slot added (dispatch consults ASSET_SCHEMA[slot]["format"])
  8.   append_line("feedback-data", {...}) writes 1 JSONL line
  9.   append_line("feedback-rejected", {...}) writes 1 JSONL line
  10.  read_lines("feedback-data") round-trips the appended dict
"""

from __future__ import annotations

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA, AssetBus


# ===================================================================
# Tests 1-3: feedback-data slot metadata
# ===================================================================
class TestFeedbackDataSlot:
    def test_file_metadata(self):
        """feedback-data file is feedback-data.jsonl."""
        assert "feedback-data" in ASSET_SCHEMA, (
            "feedback-data slot missing from ASSET_SCHEMA - "
            "Task 1 GREEN not yet applied"
        )
        assert ASSET_SCHEMA["feedback-data"]["file"] == "feedback-data.jsonl"

    def test_format_is_jsonl(self):
        """feedback-data format MUST be 'jsonl' (append-only)."""
        assert ASSET_SCHEMA["feedback-data"]["format"] == "jsonl"

    def test_writer_phase_is_feedback_ingest(self):
        """writer_phase MUST be 'feedback_ingest' (Phase 42 owns both slots)."""
        assert ASSET_SCHEMA["feedback-data"]["writer_phase"] == "feedback_ingest"


# ===================================================================
# Tests 4-6: feedback-rejected slot metadata
# ===================================================================
class TestFeedbackRejectedSlot:
    def test_file_metadata(self):
        """feedback-rejected file is feedback-rejected.jsonl."""
        assert "feedback-rejected" in ASSET_SCHEMA, (
            "feedback-rejected slot missing from ASSET_SCHEMA - "
            "Task 1 GREEN not yet applied"
        )
        assert ASSET_SCHEMA["feedback-rejected"]["file"] == "feedback-rejected.jsonl"

    def test_format_is_jsonl(self):
        """feedback-rejected format MUST be 'jsonl' (append-only)."""
        assert ASSET_SCHEMA["feedback-rejected"]["format"] == "jsonl"

    def test_writer_phase_is_feedback_ingest(self):
        """writer_phase MUST be 'feedback_ingest' (Phase 42 owns both slots)."""
        assert ASSET_SCHEMA["feedback-rejected"]["writer_phase"] == "feedback_ingest"


# ===================================================================
# Test 7: JSONL_SLOTS frozenset UNCHANGED (D-36-05)
# feedback-data + feedback-rejected are NOT added to JSONL_SLOTS -
# dispatch consults ASSET_SCHEMA[slot]["format"] directly, not the
# frozenset. Keeping the frozenset unchanged preserves the V5.0 invariant
# asserted by test_asset_bus_phase35_slots.py::test_jsonl_slots_unchanged.
# ===================================================================
class TestJsonlFrozensetUnchanged:
    def test_jsonl_slots_frozenset_unchanged(self):
        """JSONL_SLOTS MUST be exactly {finetune-dataset}.

        Per D-36-05 (append-only invariant) + verified Phase 40-01 +
        Phase 41-01: the frozenset is INFORMATIONAL ONLY - actual
        dispatch consults ASSET_SCHEMA[slot]["format"] directly. Adding
        feedback-data / feedback-rejected here would be a violation.
        """
        assert AssetBus.JSONL_SLOTS == frozenset({"finetune-dataset"}), (
            f"JSONL_SLOTS drifted: {AssetBus.JSONL_SLOTS} - "
            "feedback-data + feedback-rejected must NOT be added "
            "(dispatch uses ASSET_SCHEMA format)"
        )

    def test_feedback_slots_not_in_jsonl_slots(self):
        """Belt-and-suspenders: both new slots explicitly excluded from frozenset."""
        assert "feedback-data" not in AssetBus.JSONL_SLOTS
        assert "feedback-rejected" not in AssetBus.JSONL_SLOTS


# ===================================================================
# Tests 8-10: round-trip via append_line / read_lines
# ===================================================================
class TestFeedbackSlotsRoundTrip:
    def test_append_line_feedback_data_writes_one_jsonl_line(self, tmp_path):
        """Test 8: append_line('feedback-data', {...}) writes exactly 1 line
        to .pipeline-assets/feedback-data.jsonl and returns a path ending
        in feedback-data.jsonl."""
        bus = AssetBus(tmp_path)
        path = bus.append_line(
            "feedback-data",
            {"feedback_id": "fb-001", "episode_id": "ep-001"},
        )
        assert path.endswith("feedback-data.jsonl"), (
            f"append_line must return .jsonl path; got {path!r}"
        )
        # File on disk should contain exactly 1 non-blank line
        file_path = tmp_path / ".pipeline-assets" / "feedback-data.jsonl"
        raw = file_path.read_text(encoding="utf-8")
        non_blank = [ln for ln in raw.split("\n") if ln.strip()]
        assert len(non_blank) == 1, (
            f"expected exactly 1 JSONL line, got {len(non_blank)}: {raw!r}"
        )

    def test_append_line_feedback_rejected_writes_one_jsonl_line(self, tmp_path):
        """Test 9: append_line('feedback-rejected', {...}) writes exactly 1
        line to .pipeline-assets/feedback-rejected.jsonl."""
        bus = AssetBus(tmp_path)
        path = bus.append_line(
            "feedback-rejected",
            {"feedback_id": "fb-002", "reason": "invalid_signature"},
        )
        assert path.endswith("feedback-rejected.jsonl"), (
            f"append_line must return .jsonl path; got {path!r}"
        )
        file_path = tmp_path / ".pipeline-assets" / "feedback-rejected.jsonl"
        raw = file_path.read_text(encoding="utf-8")
        non_blank = [ln for ln in raw.split("\n") if ln.strip()]
        assert len(non_blank) == 1, (
            f"expected exactly 1 JSONL line, got {len(non_blank)}: {raw!r}"
        )

    def test_read_lines_feedback_data_round_trips_dict(self, tmp_path):
        """Test 10: read_lines('feedback-data') returns the list of dicts
        that were appended (round-trip)."""
        bus = AssetBus(tmp_path)
        bus.append_line("feedback-data", {"feedback_id": "fb-001", "v": 1})
        bus.append_line("feedback-data", {"feedback_id": "fb-002", "v": 2})

        rows = bus.read_lines("feedback-data")
        assert len(rows) == 2
        assert rows[0] == {"feedback_id": "fb-001", "v": 1}
        assert rows[1] == {"feedback_id": "fb-002", "v": 2}
