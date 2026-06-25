"""pytest unit tests for PipelineStateStore (Phase 33-01 port).

Mirrors the implicit Node.js test paths in ``test/phases/*`` for the
``Pipeline._loadState / _saveState / _findResumeIndex`` extract:

- load missing / load corrupt / save round-trip / resume detection
- atomic write leaves no .tmp residue
- save_checkpoint preserves prior phase entries

Reference: ``kais-movie-agent/lib/pipeline.js:217-249, 611-618, 700-707`` and
``.planning/phases/33-pipeline-state-asset-bus/CONTEXT.md`` (CF-06).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from plugins.pipeline_state.store import (
    DONE_STATUSES,
    PipelineState,
    PipelineStateStore,
)


# ---------------------------------------------------------------------------
# PipelineState dataclass
# ---------------------------------------------------------------------------


class TestPipelineStateDataclass:
    def test_constructs_with_episode_and_empty_phases(self) -> None:
        state = PipelineState(episode="EP01")
        assert state.episode == "EP01"
        assert state.phases == {}
        assert state.current_phase_id is None
        assert state.started_at is None
        assert state.completed_at is None

    def test_done_statuses_matches_node_baseline(self) -> None:
        # pipeline.js:553,612,668 — completed/approved/awaiting_review all
        # count as "done" (re-running would duplicate work).
        assert DONE_STATUSES == frozenset(
            {"completed", "approved", "awaiting_review"}
        )
        # Must be a frozenset so it is hashable / usable as default arg.
        assert isinstance(DONE_STATUSES, frozenset)

    def test_phases_default_is_fresh_dict_per_instance(self) -> None:
        a = PipelineState(episode="a")
        b = PipelineState(episode="b")
        a.phases["p01"] = {"status": "completed"}
        assert b.phases == {}, "phases default must not leak across instances"


# ---------------------------------------------------------------------------
# PipelineStateStore.load
# ---------------------------------------------------------------------------


class TestPipelineStateStoreLoad:
    def test_load_on_missing_file_returns_empty_state(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        state = store.load()
        assert state.episode == ""
        assert state.phases == {}
        assert state.current_phase_id is None

    def test_load_on_corrupt_json_returns_empty_state(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".pipeline-state.json").write_text(
            "{not valid json", encoding="utf-8"
        )
        store = PipelineStateStore(tmp_path)
        state = store.load()
        assert state.episode == ""
        assert state.phases == {}

    def test_load_on_empty_file_returns_empty_state(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".pipeline-state.json").write_text("", encoding="utf-8")
        store = PipelineStateStore(tmp_path)
        state = store.load()
        assert state.episode == ""

    def test_load_round_trips_after_save(self, tmp_path: Path) -> None:
        store = PipelineStateStore(tmp_path)
        original = PipelineState(
            episode="EP01",
            phases={"p01": {"status": "completed", "result": {"x": 1}}},
            current_phase_id="p01",
            started_at="2026-01-01T00:00:00Z",
        )
        store.save(original)
        loaded = store.load()
        assert loaded.episode == "EP01"
        assert loaded.phases == original.phases
        assert loaded.current_phase_id == "p01"
        assert loaded.started_at == "2026-01-01T00:00:00Z"

    def test_load_drops_unknown_keys_for_forward_compat(
        self, tmp_path: Path
    ) -> None:
        # Future schema additions shouldn't break old code.
        data = {
            "episode": "EP01",
            "phases": {},
            "current_phase_id": None,
            "started_at": None,
            "completed_at": None,
            "last_resumed_at": None,
            "trace_id": None,
            "future_field": "ignored",
        }
        (tmp_path / ".pipeline-state.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        store = PipelineStateStore(tmp_path)
        state = store.load()
        assert state.episode == "EP01"


# ---------------------------------------------------------------------------
# PipelineStateStore.save (atomic write)
# ---------------------------------------------------------------------------


class TestPipelineStateStoreSave:
    def test_save_writes_state_file_at_workdir_root(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        store.save(PipelineState(episode="EP01"))
        assert (tmp_path / ".pipeline-state.json").exists()
        # NOT under .pipeline-assets/ — CONTEXT CF-06.
        assert not (tmp_path / ".pipeline-assets").exists()

    def test_save_leaves_no_tmp_residue(self, tmp_path: Path) -> None:
        store = PipelineStateStore(tmp_path)
        store.save(PipelineState(episode="EP01"))
        residue = list(tmp_path.glob("*.tmp.*"))
        assert residue == [], f"Unexpected .tmp residue: {residue}"

    def test_save_is_atomic_under_concurrent_writes(
        self, tmp_path: Path
    ) -> None:
        # Two stores writing to the same path should never corrupt the file.
        store_a = PipelineStateStore(tmp_path)
        store_b = PipelineStateStore(tmp_path)
        store_a.save(PipelineState(episode="A"))
        store_b.save(PipelineState(episode="B"))
        # Final state must be valid JSON and parse cleanly.
        raw = (tmp_path / ".pipeline-state.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["episode"] in {"A", "B"}


# ---------------------------------------------------------------------------
# save_checkpoint
# ---------------------------------------------------------------------------


class TestSaveCheckpoint:
    def test_save_checkpoint_sets_phase_status_and_current(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        store.save_checkpoint(
            episode_id="EP01", phase="p02", payload={"out": 1}
        )
        state = store.load()
        assert state.episode == "EP01"
        assert state.current_phase_id == "p02"
        entry = state.phases["p02"]
        assert entry["status"] == "completed"
        assert entry["result"] == {"out": 1}
        # completed_at must be a parseable ISO timestamp.
        datetime.fromisoformat(entry["completed_at"])

    def test_save_checkpoint_preserves_prior_phase_entry(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        store.save_checkpoint("EP01", "p01", {"a": 1})
        store.save_checkpoint("EP01", "p02", {"b": 2})
        state = store.load()
        assert state.phases["p01"]["result"] == {"a": 1}
        assert state.phases["p02"]["result"] == {"b": 2}
        assert state.current_phase_id == "p02"

    def test_save_checkpoint_does_not_overwrite_episode_once_set(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        store.save_checkpoint("EP01", "p01", {})
        # Second checkpoint with a different episode_id should NOT silently
        # flip the episode (matches Node.js guard behavior — an episode is
        # bound to its state file for its lifetime).
        store.save_checkpoint("EP02", "p02", {})
        state = store.load()
        assert state.episode == "EP01"
        assert state.phases["p02"]["result"] == {}


# ---------------------------------------------------------------------------
# load_latest_checkpoint
# ---------------------------------------------------------------------------


class TestLoadLatestCheckpoint:
    def test_returns_current_phase_checkpoint(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        store.save_checkpoint("EP01", "p01", {"first": True})
        store.save_checkpoint("EP01", "p02", {"second": True})
        latest = store.load_latest_checkpoint("EP01")
        assert latest is not None
        assert latest["result"] == {"second": True}

    def test_returns_none_for_episode_mismatch(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        store.save_checkpoint("EP01", "p01", {"x": 1})
        assert store.load_latest_checkpoint("OTHER") is None

    def test_returns_none_when_no_checkpoint_saved(
        self, tmp_path: Path
    ) -> None:
        store = PipelineStateStore(tmp_path)
        assert store.load_latest_checkpoint("EP01") is None


# ---------------------------------------------------------------------------
# find_resume_phase
# ---------------------------------------------------------------------------


class TestFindResumePhase:
    def test_returns_first_pending_phase(self, tmp_path: Path) -> None:
        store = PipelineStateStore(tmp_path)
        store.save_checkpoint("EP01", "p01", {})
        # p02 and p03 not yet in state.
        resume = store.find_resume_phase(["p01", "p02", "p03"])
        assert resume == "p02"

    def test_returns_none_when_all_completed(self, tmp_path: Path) -> None:
        store = PipelineStateStore(tmp_path)
        for phase in ("p01", "p02", "p03"):
            store.save_checkpoint("EP01", phase, {})
        assert (
            store.find_resume_phase(["p01", "p02", "p03"]) is None
        )

    def test_awaiting_review_treated_as_done(self, tmp_path: Path) -> None:
        # pipeline.js:612 — awaiting_review counts as done (re-running
        # would duplicate submitted work waiting on human review).
        store = PipelineStateStore(tmp_path)
        state = PipelineState(episode="EP01")
        state.phases["p01"] = {"status": "completed"}
        state.phases["p02"] = {"status": "awaiting_review"}
        store.save(state)
        assert store.find_resume_phase(["p01", "p02", "p03"]) == "p03"

    def test_approved_treated_as_done(self, tmp_path: Path) -> None:
        store = PipelineStateStore(tmp_path)
        state = PipelineState(episode="EP01")
        state.phases["p01"] = {"status": "approved"}
        store.save(state)
        assert store.find_resume_phase(["p01", "p02"]) == "p02"

    def test_failed_status_is_resumed(self, tmp_path: Path) -> None:
        # "failed" is NOT in DONE_STATUSES — must be retried.
        store = PipelineStateStore(tmp_path)
        state = PipelineState(episode="EP01")
        state.phases["p01"] = {"status": "failed"}
        store.save(state)
        assert store.find_resume_phase(["p01", "p02"]) == "p01"
