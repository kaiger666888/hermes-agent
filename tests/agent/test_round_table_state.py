"""Round-table state machine tests (INFRA-03).

Covers SC#2 (lifecycle atomicity — interrupted submit never leaves status
outside the schema enum {open, completed, aborted, stalled}) and SC#3 a/b/c
(3 crash-recovery failure modes per 06-CROSS-REPO-IMPACT.md §6.4):

    (a) Partial-write corruption → archived to .corrupt + json.JSONDecodeError
    (b) Mid-turn crash (status=open + stale lastUpdatedAt) → flipped to stalled
    (c) Orphaned session (same recovery path as (b))

State enum values are authoritative per
.planning/research/v10-orchestrator-design/round-table-state-schema.yaml:127-141
(open | completed | aborted | stalled). DO NOT use in_progress or closed —
those are stale CONTEXT.md shorthand (52-CONTEXT.md "Resolved by Kai" point 2).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent.round_table_state import (
    RoundTableStatus,
    abort_round_table,
    append_turn,
    open_round_table,
    read_and_recover_state,
    submit_round_table_result,
)
from hermes_constants import get_hermes_home


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _state_dir(project_slug: str = "test-slug") -> Path:
    """Return the canonical state dir under the (autouse-redirected) HERMES_HOME.

    Mirrors the path locked by round-table-state-schema.yaml header lines 1-4
    + 06-CROSS-REPO-IMPACT.md §5.1:
        ~/.hermes/agents/.runtime/{slug}/round_tables/
    """
    return (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / project_slug
        / "round_tables"
    )


def _make_turn(panelist_id: str = "agent-a", opinion: str = "yes") -> dict:
    """Build a minimal Turn dict matching round-table-state-schema.yaml $defs.Turn."""
    return {
        "turnIndex": 1,
        "panelistId": panelist_id,
        "opinion": opinion,
        "citedMemoryIds": [],
        "submittedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _write_raw_state(state_path: Path, body: str) -> None:
    """Bypass atomic_json_write to plant a corrupt/stale fixture for SC#3 tests."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(body, encoding="utf-8")


def _stale_iso(minutes_ago: int) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    ).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Lifecycle — SC#2 positive round trip + idempotency contracts
# --------------------------------------------------------------------------- #


class TestRoundTableLifecycle:
    def test_open_creates_state_file_with_status_open(self):
        state_dir = _state_dir()
        state = open_round_table(
            state_dir=state_dir,
            round_id="round-001",
            project_id="test-slug",
            question="Ship feature X?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-session-1",
        )

        # File exists at the canonical path with `agents/` parent
        state_path = state_dir / "round-001.json"
        assert state_path.exists()
        assert state["status"] == "open"
        assert state["roundId"] == "round-001"
        assert state["roundTableOpen"]["caller"] == "cc-session-1"
        assert state["projectId"] == "test-slug"

        # Confirm path actually nests under agents/.runtime/ (per schema YAML header)
        assert "agents" in state_path.parts
        assert ".runtime" in state_path.parts
        assert "round_tables" in state_path.parts

    def test_duplicate_open_returns_409_conflict(self):
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-dup",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["a", "b"],
            caller="cc-1",
        )
        result = open_round_table(
            state_dir=state_dir,
            round_id="round-dup",
            project_id="test-slug",
            question="Q again?",
            panelist_agent_ids=["a", "b"],
            caller="cc-2",
        )
        assert result["status"] == 409
        assert result["error"] == "round_already_open"
        assert result["round_id"] == "round-dup"

    def test_append_turn_grows_turns_list(self):
        state_dir = _state_dir()
        state = open_round_table(
            state_dir=state_dir,
            round_id="round-append",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-append.json"
        turn = _make_turn(panelist_id="agent-a", opinion="ship it")
        updated = append_turn(state_path, turn)

        assert len(updated["turns"]) == 1
        assert updated["turns"][0]["panelistId"] == "agent-a"
        assert updated["lastUpdatedAt"] is not None

        # Reload from disk to confirm atomic write persisted
        with open(state_path, encoding="utf-8") as f:
            reloaded = json.load(f)
        assert len(reloaded["turns"]) == 1
        assert reloaded["turns"][0]["panelistId"] == "agent-a"

    def test_submit_flips_status_to_completed(self):
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-submit",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-submit.json"
        append_turn(state_path, _make_turn(panelist_id="agent-a"))

        result = submit_round_table_result(
            state_path=state_path,
            conclusion="ship after consensus",
            cited_memories=[],
            closed_by="cc-1",
        )
        assert result["status"] == "completed"
        assert result["submitRoundTableResult"]["closedBy"] == "cc-1"
        assert result["submitRoundTableResult"]["conclusion"] == "ship after consensus"

    def test_second_submit_returns_409_conflict(self):
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-idem",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-idem.json"
        submit_round_table_result(
            state_path=state_path,
            conclusion="first",
            cited_memories=[],
            closed_by="cc-1",
        )
        result = submit_round_table_result(
            state_path=state_path,
            conclusion="second",
            cited_memories=[],
            closed_by="cc-2",
        )
        assert result["status"] == 409
        assert result["error"] == "round_not_open"


# --------------------------------------------------------------------------- #
# Crash recovery — SC#2 atomicity + SC#3 a/b/c
# --------------------------------------------------------------------------- #


class TestCrashRecovery:
    def test_interrupted_submit_no_status_outside_enum(self, tmp_path):
        """SC#2 atomicity: a corrupt mid-submit file is recovered, not silently
        flipped to a value outside the schema enum (in_progress/closed are
        FORBIDDEN per round-table-state-schema.yaml:127-141).
        """
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-crash",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-crash.json"

        # Simulate crash mid-submit by truncating to broken JSON
        _write_raw_state(state_path, "{")

        with pytest.raises(json.JSONDecodeError):
            read_and_recover_state(state_path)

        # Recovery must archive the corrupt file
        assert state_path.with_suffix(".json.corrupt").exists()
        # Corrupt archive contains the original bytes
        assert (
            state_path.with_suffix(".json.corrupt").read_text(encoding="utf-8")
            == "{"
        )

    def test_partial_write_recovery_defense_in_depth(self, tmp_path):
        """SC#3a: defense-in-depth. atomic_json_write guarantees no partial
        body, but if a kernel/EXT4-fsync race somehow corrupts the file,
        read_and_recover_state archives it + raises.
        """
        state_dir = _state_dir()
        state_path = state_dir / "round-partial.json"
        _write_raw_state(state_path, "{ broken json")

        with pytest.raises(json.JSONDecodeError):
            read_and_recover_state(state_path)

        assert state_path.with_suffix(".json.corrupt").exists()

    def test_corrupt_archive_fsyncs_parent_dir(self, tmp_path, monkeypatch):
        """CR-03: the rename(2) durability hole is closed.

        POSIX ``rename(2)`` atomically swaps the directory entry but does
        NOT guarantee the parent directory's metadata change is flushed to
        disk. Without an explicit ``fsync(dir_fd)`` after the rename, a
        power loss can lose BOTH the original and the archive on ext4 /
        XFS default mount options. This test asserts the fsync call is
        made through the rename path.
        """
        from agent import round_table_state as rts_module

        fsync_calls: list[int] = []
        real_fsync = os.fsync

        def _track_fsync(fd):
            fsync_calls.append(fd)
            # Don't actually call real_fsync — the fd is a real dir fd
            # opened by the helper; we want to record + still let the
            # fsync execute so the dir metadata is durable on this CI run.
            return real_fsync(fd)

        monkeypatch.setattr(rts_module.os, "fsync", _track_fsync)

        state_dir = _state_dir()
        state_path = state_dir / "round-fsync.json"
        _write_raw_state(state_path, "{ broken json")

        with pytest.raises(json.JSONDecodeError):
            read_and_recover_state(state_path)

        # The corrupt archive must exist, AND at least one fsync must have
        # been called against a dir fd (CR-03 fix). We don't assert the
        # exact fd identity because os.open is internal to the helper; we
        # only assert that >= 1 fsync call happened post-rename.
        assert state_path.with_suffix(".json.corrupt").exists(), (
            "archive file must exist after recovery"
        )
        assert len(fsync_calls) >= 1, (
            f"expected parent-dir fsync after corrupt-archive rename, "
            f"got {len(fsync_calls)} fsync calls"
        )

    def test_mid_turn_crash_recovers_via_stall(self, tmp_path):
        """SC#3b: process died between turn append + status flip. State file
        shows status=open with lastUpdatedAt > stall_threshold_minutes. On next
        read, status is auto-flipped to 'stalled'.
        """
        state_dir = _state_dir()
        state_path = state_dir / "round-stall.json"
        # Build a stale-open fixture (2 hours old > default 30-minute threshold)
        stale_body = json.dumps({
            "roundId": "round-stall",
            "projectId": "test-slug",
            "question": "Q?",
            "panelists": [],
            "turnOrder": {"strategy": "round-robin", "currentIndex": 0},
            "status": "open",
            "turns": [],
            "roundTableOpen": {
                "caller": "cc-1",
                "openedAt": _stale_iso(120),
                "project": "test-slug",
                "question": "Q?",
            },
            "createdAt": _stale_iso(120),
            "lastUpdatedAt": _stale_iso(120),  # 2h ago
        })
        _write_raw_state(state_path, stale_body)

        recovered = read_and_recover_state(state_path, stall_threshold_minutes=30)
        assert recovered["status"] == "stalled"

        # Verify atomic write persisted the flip
        with open(state_path, encoding="utf-8") as f:
            persisted = json.load(f)
        assert persisted["status"] == "stalled"

    def test_orphaned_session_recovers_on_next_read(self, tmp_path):
        """SC#3c: orphaned session (same recovery path as SC#3b). The default
        stall_threshold is 30 minutes; 90 minutes old triggers recovery.
        """
        state_dir = _state_dir()
        state_path = state_dir / "round-orphan.json"
        stale_body = json.dumps({
            "roundId": "round-orphan",
            "projectId": "test-slug",
            "question": "Q?",
            "panelists": [],
            "turnOrder": {"strategy": "round-robin", "currentIndex": 0},
            "status": "open",
            "turns": [],
            "roundTableOpen": {
                "caller": "cc-1",
                "openedAt": _stale_iso(90),
                "project": "test-slug",
                "question": "Q?",
            },
            "createdAt": _stale_iso(90),
            "lastUpdatedAt": _stale_iso(90),  # 90 min ago
        })
        _write_raw_state(state_path, stale_body)

        recovered = read_and_recover_state(state_path)
        assert recovered["status"] == "stalled"


# --------------------------------------------------------------------------- #
# Schema-enum authority — explicit guard against in_progress / closed
# --------------------------------------------------------------------------- #


class TestAbortRoundTable:
    """CR-04 fix: ``abort_round_table`` programmatic API.

    The schema enum (round-table-state-schema.yaml:127-141) includes
    ``aborted`` (operator / CC cancellation). Before CR-04, no function
    produced it — cancelled rounds looked identical to open rounds for
    the 30-minute stall timeout. These tests pin the transition.
    """

    def test_abort_round_table_open_to_aborted_happy_path(self):
        """Happy path: ``open → aborted`` with reason + aborted_by sealed."""
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-abort-1",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-abort-1.json"

        result = abort_round_table(
            state_path,
            reason="operator cancelled — wrong panel",
            aborted_by="operator-kai",
        )
        assert result["status"] == "aborted"
        assert result["abortRoundTable"]["reason"] == "operator cancelled — wrong panel"
        assert result["abortRoundTable"]["abortedBy"] == "operator-kai"
        assert result["abortRoundTable"]["abortedAt"] == result["lastUpdatedAt"], (
            "abortRoundTable.abortedAt MUST match lastUpdatedAt — they are "
            "computed from the same _now_iso() call so future refactors don't drift"
        )

        # Reload from disk to confirm atomic write persisted the abort
        with open(state_path, encoding="utf-8") as f:
            reloaded = json.load(f)
        assert reloaded["status"] == "aborted"
        assert reloaded["abortRoundTable"]["abortedBy"] == "operator-kai"

    def test_abort_round_table_rejects_already_completed(self):
        """Already-terminal (completed) round rejects abort with 409."""
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-abort-2",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-abort-2.json"
        # First complete the round
        submit_round_table_result(
            state_path=state_path,
            conclusion="done",
            cited_memories=[],
            closed_by="cc-1",
        )
        # Now attempt to abort — must reject
        result = abort_round_table(
            state_path,
            reason="too late",
            aborted_by="operator",
        )
        assert result["status"] == 409
        assert result["error"] == "round_not_open"
        assert result["current_status"] == "completed"

    def test_abort_round_table_rejects_already_aborted_idempotent(self):
        """Re-aborting an aborted round rejects with 409 (idempotent contract)."""
        state_dir = _state_dir()
        open_round_table(
            state_dir=state_dir,
            round_id="round-abort-3",
            project_id="test-slug",
            question="Q?",
            panelist_agent_ids=["agent-a", "agent-b"],
            caller="cc-1",
        )
        state_path = state_dir / "round-abort-3.json"
        # First abort succeeds
        first = abort_round_table(state_path, reason="first", aborted_by="op")
        assert first["status"] == "aborted"
        # Second abort rejects (already terminal)
        second = abort_round_table(state_path, reason="second", aborted_by="op")
        assert second["status"] == 409
        assert second["error"] == "round_not_open"
        assert second["current_status"] == "aborted"


# --------------------------------------------------------------------------- #
# Schema-enum authority — explicit guard against in_progress / closed
# --------------------------------------------------------------------------- #


class TestRoundTableStatusEnum:
    def test_enum_values_match_schema_yaml_exactly(self):
        """round-table-state-schema.yaml:127-141 enum is the authoritative
        4-value form. in_progress / closed are NOT in the enum.
        """
        values = {s.value for s in RoundTableStatus}
        assert values == {"open", "completed", "aborted", "stalled"}
        assert "in_progress" not in values
        assert "closed" not in values
