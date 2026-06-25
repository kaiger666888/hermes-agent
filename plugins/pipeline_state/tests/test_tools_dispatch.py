"""Dispatch + integration tests for pipeline_state tools.py (Phase 33-04, Wave 2).

Verifies the 4 Phase 33 handlers dispatch to real Wave 1 modules
(PipelineStateStore / AssetBus / CreativeHistoryTracker) without mocks of
those modules — every test exercises real filesystem I/O under ``tmp_path``
via ``monkeypatch.chdir``. This is the "wiring half" of SC#4 (Python unit
tests cover core operations); Wave 1's per-module tests cover the data layer.

Test plan (9 tests across 3 classes):

- ``TestCheckpointSaveLoad`` (4):
  - save_then_load round-trips a payload through .pipeline-state.json
  - save with missing args returns tool_error
  - load with missing episode returns tool_error
  - load returns status=no_checkpoint for an episode with no state

- ``TestAssetBusDispatch`` (4):
  - write/read round-trip for failed-shots (JSON slot)
  - double-write to finetune-dataset appends 2 JSONL lines
  - read for a slot with no file returns data=None
  - write with missing args returns tool_error

- ``TestEndToEndCreativeHistory`` (1):
  - CreativeHistoryTracker.stamp then asset_bus_read for creative-history
    returns the stamped record via the dispatch handler

All tests chdir into ``tmp_path`` so the handler factory helpers
(``_state_store()`` / ``_asset_bus()``) using ``os.getcwd()`` operate in
the temp directory. No test pollutes the real working tree.
"""
from __future__ import annotations

import json
from pathlib import Path

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.creative_history import CreativeHistoryTracker
from plugins.pipeline_state.tools import (
    _handle_asset_bus_read,
    _handle_asset_bus_write,
    _handle_pipeline_checkpoint_load,
    _handle_pipeline_checkpoint_save,
)


def _parse(result_str: str) -> dict:
    """Parse a handler's JSON string into a dict."""
    return json.loads(result_str)


# ---------------------------------------------------------------------------
# checkpoint_save / checkpoint_load dispatch
# ---------------------------------------------------------------------------


class TestCheckpointSaveLoad:
    """Verify _handle_pipeline_checkpoint_{save,load} dispatch to
    PipelineStateStore.{save_checkpoint,load_latest_checkpoint}."""

    def test_save_then_load_round_trips(self, tmp_path: Path, monkeypatch):
        """save_checkpoint writes .pipeline-state.json; load returns the payload."""
        monkeypatch.chdir(tmp_path)
        save_result = _parse(_handle_pipeline_checkpoint_save({
            "episode_id": "EP01",
            "phase": "p02",
            "payload": {"shots": 10, "name": "scene-gen"},
        }))
        assert save_result["status"] == "saved"
        assert save_result["episode_id"] == "EP01"
        assert save_result["phase"] == "p02"

        # State file at workdir root (NOT under .pipeline-assets/).
        assert (tmp_path / ".pipeline-state.json").exists()
        assert not (tmp_path / ".pipeline-assets" / ".pipeline-state.json").exists()

        load_result = _parse(_handle_pipeline_checkpoint_load({"episode_id": "EP01"}))
        assert load_result["status"] == "loaded"
        assert load_result["episode_id"] == "EP01"
        checkpoint = load_result["checkpoint"]
        assert checkpoint["status"] == "completed"
        assert checkpoint["result"] == {"shots": 10, "name": "scene-gen"}
        assert "completed_at" in checkpoint  # ISO timestamp recorded

    def test_save_missing_args_returns_error(self):
        """save with no episode_id/phase returns tool_error JSON."""
        result = _parse(_handle_pipeline_checkpoint_save({}))
        assert "error" in result
        assert "episode_id" in result["error"]
        assert "phase" in result["error"]

    def test_load_missing_episode_returns_error(self):
        """load with no episode_id returns tool_error JSON."""
        result = _parse(_handle_pipeline_checkpoint_load({}))
        assert "error" in result
        assert "episode_id" in result["error"]

    def test_load_returns_no_checkpoint_when_empty(
        self, tmp_path: Path, monkeypatch
    ):
        """load for an episode with no saved state returns status=no_checkpoint."""
        monkeypatch.chdir(tmp_path)
        result = _parse(_handle_pipeline_checkpoint_load({"episode_id": "EPMISSING"}))
        assert result["status"] == "no_checkpoint"
        assert result["episode_id"] == "EPMISSING"


# ---------------------------------------------------------------------------
# asset_bus_read / asset_bus_write dispatch
# ---------------------------------------------------------------------------


class TestAssetBusDispatch:
    """Verify _handle_asset_bus_{read,write} dispatch to the correct AssetBus
    method (read/read_lines for JSON/JSONL, write/append_line for JSON/JSONL)."""

    def test_write_failed_shots_then_read_back(
        self, tmp_path: Path, monkeypatch
    ):
        """write handler for failed-shots (JSON slot) round-trips via read handler."""
        monkeypatch.chdir(tmp_path)
        entry = {"failures": [{"shot_id": "s01", "error": "timeout"}], "version": 1}
        write_result = _parse(_handle_asset_bus_write({
            "episode_id": "EP01",
            "slot": "failed-shots",
            "entry": entry,
        }))
        assert write_result["status"] == "written"
        assert write_result["slot"] == "failed-shots"
        assert write_result["path"].endswith("failed-shots.json")

        read_result = _parse(_handle_asset_bus_read({
            "episode_id": "EP01",
            "slot": "failed-shots",
        }))
        assert read_result["status"] == "read"
        # read() unwraps the envelope — the raw payload comes back.
        assert read_result["data"] == entry

    def test_write_finetune_dataset_appends_jsonl(
        self, tmp_path: Path, monkeypatch
    ):
        """write handler twice for finetune-dataset (JSONL) appends 2 lines."""
        monkeypatch.chdir(tmp_path)
        for i in (1, 2):
            result = _parse(_handle_asset_bus_write({
                "episode_id": "EP01",
                "slot": "finetune-dataset",
                "entry": {"sample": i, "label": f"l{i}"},
            }))
            assert result["status"] == "written"
            assert result["path"].endswith("finetune-dataset.jsonl")

        read_result = _parse(_handle_asset_bus_read({
            "episode_id": "EP01",
            "slot": "finetune-dataset",
        }))
        assert read_result["status"] == "read"
        assert isinstance(read_result["data"], list)
        assert len(read_result["data"]) == 2
        assert read_result["data"][0] == {"sample": 1, "label": "l1"}
        assert read_result["data"][1] == {"sample": 2, "label": "l2"}

    def test_read_missing_slot_returns_null_data(
        self, tmp_path: Path, monkeypatch
    ):
        """read for a slot whose file doesn't exist returns data=None (JSON) or [] (JSONL)."""
        monkeypatch.chdir(tmp_path)
        # JSON slot — AssetBus.read returns None on missing file.
        result = _parse(_handle_asset_bus_read({
            "episode_id": "EP01",
            "slot": "failed-shots",
        }))
        assert result["status"] == "read"
        assert result["data"] is None

    def test_write_missing_args_returns_error(self):
        """write with no episode_id/slot/entry returns tool_error JSON."""
        result = _parse(_handle_asset_bus_write({}))
        assert "error" in result
        # Error message mentions the required fields.
        assert "episode_id" in result["error"]


# ---------------------------------------------------------------------------
# End-to-end: CreativeHistoryTracker (Plan 33-03) → asset_bus_read dispatch
# ---------------------------------------------------------------------------


class TestEndToEndCreativeHistory:
    """Proves Plan 33-03 integration with Plan 33-04 dispatch: a real stamp
    flows through AssetBus (Plan 33-02) and is reachable via the
    asset_bus_read tool handler."""

    def test_creative_history_stamp_then_asset_bus_read(
        self, tmp_path: Path, monkeypatch
    ):
        """Tracker.stamp() then dispatch handler returns the stamped record."""
        monkeypatch.chdir(tmp_path)
        bus = AssetBus(tmp_path)
        tracker = CreativeHistoryTracker(asset_bus=bus)
        stamped = tracker.stamp({
            "asset_slot": "final-shots",
            "asset_id": "shot-001",
            "source_hashes": ["abc123"],
        })
        assert stamped is True

        # Now the tool handler reads via os.getcwd() factory — same tmp dir.
        result = _parse(_handle_asset_bus_read({
            "episode_id": "EP01",
            "slot": "creative-history",
        }))
        assert result["status"] == "read"
        data = result["data"]
        assert isinstance(data, dict)
        assert "shots" in data
        assert len(data["shots"]) == 1
        record = data["shots"][0]
        assert record["asset_id"] == "shot-001"
        assert record["asset_slot"] == "final-shots"
        assert record["source_hashes"] == ["abc123"]
        assert "content_hash" in record
        assert "timestamp" in record
