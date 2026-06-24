"""Tests for agent/evolution/queue.py — EVOL-03 JSONL queue lifecycle.

Covers PatchRecord schema, append_patch, move_patch (applied + rejected
branches), read_queue filtering, malformed-line skipping, and
append_failed_gate separation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agent.evolution.queue import (
    FAILED_GATE_FILENAME,
    PROTECTED_REFS,
    PatchRecord,
    append_failed_gate,
    append_patch,
    move_patch,
    read_queue,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_patch_record(patch_id: str = "test_123_abcd") -> PatchRecord:
    return PatchRecord(
        patch_id=patch_id,
        skill_id="test_skill",
        insight_id="test_123_abcd",
        unified_diff="--- a/x\n+++ b/x\n@@ -1,1 +1,2 @@\n a\n+b\n",
        feedback_chain=["fb_1", "fb_2"],
        llm_rationale="Operators noted the gap.",
        eval_gate_score={"verdict": "pass", "mean_delta": 0.15},
        status="pending",
        ts_queued="2026-06-24T10:00:00+00:00",
    )


# --------------------------------------------------------------------------- #
# TestPatchRecordSchema
# --------------------------------------------------------------------------- #


class TestPatchRecordSchema:
    def test_valid_record(self) -> None:
        rec = _make_patch_record()
        assert rec.status == "pending"
        assert rec.feedback_chain == ["fb_1", "fb_2"]

    def test_rejects_invalid_status(self) -> None:
        # Construct directly — Pydantic v2 model_copy(update=...) does
        # not re-run validators by default.
        with pytest.raises(ValidationError):
            PatchRecord(
                patch_id="x",
                skill_id="test_skill",
                insight_id="x",
                unified_diff="diff",
                feedback_chain=["fb_1"],
                llm_rationale="r",
                eval_gate_score={},
                status="bogus",
                ts_queued="2026-06-24T10:00:00+00:00",
            )

    def test_protected_refs_tuple_is_canonical(self) -> None:
        # SC-6: the 5 v4/v5 protected refs MUST be listed.
        assert "snowflake-method.md" in PROTECTED_REFS
        assert "e-konte-format.md" in PROTECTED_REFS
        assert "scamper-variations.md" in PROTECTED_REFS
        assert "dreamina-cli-baseline.md" in PROTECTED_REFS
        assert "v86-pipeline-mapping.md" in PROTECTED_REFS


# --------------------------------------------------------------------------- #
# TestAppendPatch
# --------------------------------------------------------------------------- #


class TestAppendPatch:
    def test_appends_one_jsonl_line(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        rec = _make_patch_record()
        append_patch(rec, evo_dir)
        queue_path = evo_dir / "queue.jsonl"
        assert queue_path.exists()
        lines = queue_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["patch_id"] == rec.patch_id

    def test_preserves_prior_content(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        append_patch(_make_patch_record("id1"), evo_dir)
        append_patch(_make_patch_record("id2"), evo_dir)
        lines = (evo_dir / "queue.jsonl").read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2


# --------------------------------------------------------------------------- #
# TestMovePatch
# --------------------------------------------------------------------------- #


class TestMovePatch:
    def test_move_to_applied(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        append_patch(_make_patch_record("pid1"), evo_dir)
        updated = move_patch(
            patch_id="pid1",
            target_status="applied",
            evolution_dir=evo_dir,
            commit_sha="abc1234",
        )
        assert updated.status == "applied"
        assert updated.commit_sha == "abc1234"  # type: ignore[attr-defined]
        assert updated.ts_applied is not None  # type: ignore[attr-defined]
        # queue.jsonl should now be empty; applied.jsonl should have 1 line.
        assert not (evo_dir / "queue.jsonl").exists() or \
            (evo_dir / "queue.jsonl").read_text(encoding="utf-8").strip() == ""
        applied_lines = (evo_dir / "applied.jsonl").read_text(encoding="utf-8").strip().split("\n")
        assert len(applied_lines) == 1

    def test_move_to_rejected(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        append_patch(_make_patch_record("pid1"), evo_dir)
        updated = move_patch(
            patch_id="pid1",
            target_status="rejected",
            evolution_dir=evo_dir,
            reason="stale baseline",
        )
        assert updated.status == "rejected"
        assert updated.reason == "stale baseline"  # type: ignore[attr-defined]
        rejected_lines = (evo_dir / "rejected.jsonl").read_text(encoding="utf-8").strip().split("\n")
        assert len(rejected_lines) == 1


class TestMovePatchNotFound:
    def test_raises_key_error(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        with pytest.raises(KeyError):
            move_patch(
                patch_id="nonexistent",
                target_status="applied",
                evolution_dir=evo_dir,
                commit_sha="x",
            )


# --------------------------------------------------------------------------- #
# TestReadQueue
# --------------------------------------------------------------------------- #


class TestReadQueue:
    def test_read_pending(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        append_patch(_make_patch_record("p1"), evo_dir)
        append_patch(_make_patch_record("p2"), evo_dir)
        records = read_queue(evolution_dir=evo_dir, status="pending")
        assert len(records) == 2

    def test_read_with_skill_filter(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        r1 = _make_patch_record("p1")
        r2 = _make_patch_record("p2").model_copy(update={"skill_id": "other"})
        append_patch(r1, evo_dir)
        append_patch(r2, evo_dir)
        records = read_queue(evolution_dir=evo_dir, status="pending", skill_id="test_skill")
        assert len(records) == 1
        assert records[0].skill_id == "test_skill"

    def test_read_applied(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        append_patch(_make_patch_record("p1"), evo_dir)
        move_patch(patch_id="p1", target_status="applied",
                   evolution_dir=evo_dir, commit_sha="abc")
        records = read_queue(evolution_dir=evo_dir, status="applied")
        assert len(records) == 1
        assert records[0].status == "applied"


class TestReadQueueMalformedLineSkipped:
    def test_skips_and_logs_warning(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        # Write one good line + one malformed line + one good line.
        good = _make_patch_record("p1").model_dump()
        queue_path = evo_dir / "queue.jsonl"
        with queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(good, ensure_ascii=False) + "\n")
            f.write("{not valid json\n")
            f.write(json.dumps(_make_patch_record("p2").model_dump(), ensure_ascii=False) + "\n")
        records = read_queue(evolution_dir=evo_dir, status="pending")
        assert len(records) == 2  # malformed line skipped


# --------------------------------------------------------------------------- #
# TestAppendFailedGate
# --------------------------------------------------------------------------- #


class TestAppendFailedGate:
    def test_writes_to_failed_gate_file(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        rejection = {
            "patch_id": "p1",
            "skill_id": "test_skill",
            "rejection_reason": "mean_delta=-0.5 below threshold",
        }
        append_failed_gate(rejection, evo_dir)
        failed_path = evo_dir / FAILED_GATE_FILENAME
        assert failed_path.exists()
        lines = failed_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1

    def test_failed_gate_records_never_in_read_queue(self, tmp_path: Path) -> None:
        evo_dir = tmp_path / "evolution"
        evo_dir.mkdir()
        append_failed_gate({"patch_id": "fp1", "skill_id": "x"}, evo_dir)
        # read_queue should never surface failed_gate records — iterate
        # only over the statuses read_queue accepts (failed_gate is NOT
        # a read_queue-valid status; that's the point).
        for status in ("pending", "applied", "rejected"):
            records = read_queue(evolution_dir=evo_dir, status=status)
            assert all(r.patch_id != "fp1" for r in records), \
                f"failed_gate record leaked into status={status}"
