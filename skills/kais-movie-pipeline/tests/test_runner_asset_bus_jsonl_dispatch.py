"""test_runner_asset_bus_jsonl_dispatch.py — Phase 40 CR-01 regression test.

This test exists specifically to catch the Phase 40 CR-01 defect documented
in ``40-REVIEW.md``:

    The runner's injected ``_asset_bus_write`` unconditionally called
    ``bus.write(slot, entry, envelope=True)``, but ``AssetBus.write()``
    explicitly raises ``AssetBusError`` for JSONL-format slots. The very
    first successful p10b variant record would raise, propagate up through
    ``_run_body``, be caught by p10b's broad ``except Exception``, and
    silently downgrade every episode to ``preview_skipped=True``
    regardless of actual engine health.

The existing ``test_p10b_full_dag_integration.py`` test masked this defect
because it substitutes a custom ``_StubBus`` whose ``write`` method
dispatches on slot format. This test does NOT use a stub: it constructs a
REAL ``AssetBus`` on a tmp workdir and drives it through the REAL runner's
``run_episode`` (with the real injected ``_asset_bus_write`` closure).

The test would have FAILED (asserting an ``AssetBusError``-swallow) against
the pre-fix runner, and PASSES against the post-fix runner where
``_asset_bus_write`` dispatches on ``ASSET_SCHEMA[slot]["format"]``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Make the skill-local ``pipeline`` package importable.
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.runner import RunnerConfig, run_episode  # noqa: E402
from plugins.pipeline_state.asset_bus import AssetBus  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal fake phase module that writes one record to a JSONL slot via the
# injected ``asset_bus_write`` callable. The whole point of this test is to
# exercise that injected callable against the REAL AssetBus.
# ---------------------------------------------------------------------------


def _make_jsonl_writing_phase(phase_id: str, slot: str, record: dict):
    """Return a fake phase module whose ``run`` writes ``record`` to ``slot``.

    Mirrors how p10b writes successful variant records to
    ``rapid-preview-clips`` (the JSONL slot at the heart of CR-01).
    """
    calls: dict = {"count": 0}

    def run(
        episode_id: str,
        asset_bus_read,
        asset_bus_write,
        delegate_task,
        trigger_gate=None,
    ):
        calls["count"] += 1
        # Write the record through the runner-injected callable — exactly
        # what p10b does at p10b_rapid_preview.py:376.
        asset_bus_write(slot, record)
        return {
            "phase": phase_id,
            "outputs": {"wrote": True},
            "gate": None,
        }

    class _FakeModule:
        __name__ = f"fake_{phase_id}"

    _FakeModule.run = staticmethod(run)  # type: ignore[attr-defined]
    _FakeModule.calls = calls  # type: ignore[attr-defined]
    _FakeModule.phase_id = phase_id  # type: ignore[attr-defined]
    return _FakeModule


# ---------------------------------------------------------------------------
# Real AssetBus against the real runner — JSONL slot dispatch
# ---------------------------------------------------------------------------


def test_runner_injected_write_dispatches_jsonl_to_append_line(tmp_path):
    """The runner's injected ``_asset_bus_write`` MUST route JSONL-format
    slots to ``AssetBus.append_line`` (not ``AssetBus.write``).

    Pre-fix: this test FAILS with an ``AssetBusError`` propagating up out
    of the fake phase's ``run`` (the broad ``except Exception`` of p10b is
    NOT in play here — we use a minimal fake phase with no try/except, so
    the AssetBusError surfaces directly to ``run_episode`` and the test).

    Post-fix: ``_asset_bus_write`` dispatches on ``ASSET_SCHEMA[slot]
    ["format"]``; JSONL-format slots route to ``append_line`` and the
    record is appended to ``{workdir}/.pipeline-assets/{file}.jsonl``.
    """
    workdir = str(tmp_path)
    bus = AssetBus(workdir)

    record = {"shot_id": "s1", "variant_id": "s1__v1", "engine": "test"}
    fake_phase = _make_jsonl_writing_phase(
        phase_id="fake_jsonl_writer",
        slot="rapid-preview-clips",
        record=record,
    )

    # Install a single-phase registry pointing at our fake phase.
    from pipeline import phases as phases_mod
    from pipeline import runner as runner_mod

    saved_runner_list = list(runner_mod.PHASE_REGISTRY)
    saved_phases_list = list(phases_mod.PHASE_REGISTRY)

    shared = [{"id": "fake_jsonl_writer", "module": fake_phase, "depends_on": []}]
    phases_mod.PHASE_REGISTRY = shared
    runner_mod.PHASE_REGISTRY = shared

    # Minimal stub store (the runner needs load_latest_checkpoint /
    # save_checkpoint). Real AssetBus is passed via inject.
    class _StubStore:
        def load_latest_checkpoint(self, episode_id):
            return None

        def save_checkpoint(self, episode_id, phase, payload):
            pass

    try:
        # Inject the REAL AssetBus so the runner's _asset_bus_write closure
        # holds a reference to a real bus (not a stub). This is the scenario
        # p10b faces in production.
        cfg = RunnerConfig(workdir=workdir, enable_gates=False)
        result = run_episode(
            "ep-jsonl-dispatch", cfg,
            inject={
                "store": _StubStore(),
                "bus": bus,
            },
        )
    finally:
        phases_mod.PHASE_REGISTRY = list(saved_phases_list)
        runner_mod.PHASE_REGISTRY = list(saved_runner_list)

    # The fake phase ran without raising — its result is recorded.
    assert "fake_jsonl_writer" in result["phases"]
    assert result["phases"]["fake_jsonl_writer"]["outputs"]["wrote"] is True

    # The JSONL file exists on disk and contains exactly one line — the
    # record we wrote through the runner-injected callable.
    jsonl_path = Path(workdir) / ".pipeline-assets" / "rapid-preview-clips.jsonl"
    assert jsonl_path.exists(), (
        f"rapid-preview-clips.jsonl missing at {jsonl_path} — "
        f"runner's _asset_bus_write likely called write() instead of append_line()"
    )
    lines = [
        json.loads(line)
        for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 1, f"expected 1 JSONL line; got {len(lines)}"
    assert lines[0] == record


def test_runner_injected_write_still_routes_json_slots_to_write(tmp_path):
    """JSON-format slots MUST still route to ``AssetBus.write`` (envelope-wrapped).

    Regression guard: the Phase 40 CR-01 fix added format dispatch; this
    asserts the JSON path is unchanged. ``episode-meta`` is a JSON slot.
    """
    workdir = str(tmp_path)
    bus = AssetBus(workdir)

    record = {"episode_id": "ep1", "preview_skipped": False}
    fake_phase = _make_jsonl_writing_phase(
        phase_id="fake_json_writer",
        slot="episode-meta",
        record=record,
    )

    from pipeline import phases as phases_mod
    from pipeline import runner as runner_mod

    saved_runner_list = list(runner_mod.PHASE_REGISTRY)
    saved_phases_list = list(phases_mod.PHASE_REGISTRY)

    shared = [{"id": "fake_json_writer", "module": fake_phase, "depends_on": []}]
    phases_mod.PHASE_REGISTRY = shared
    runner_mod.PHASE_REGISTRY = shared

    class _StubStore:
        def load_latest_checkpoint(self, episode_id):
            return None

        def save_checkpoint(self, episode_id, phase, payload):
            pass

    try:
        cfg = RunnerConfig(workdir=workdir, enable_gates=False)
        run_episode(
            "ep-json-dispatch", cfg,
            inject={"store": _StubStore(), "bus": bus},
        )
    finally:
        phases_mod.PHASE_REGISTRY = list(saved_phases_list)
        runner_mod.PHASE_REGISTRY = list(saved_runner_list)

    # JSON slot written via write() — file is a JSON envelope (NOT jsonl).
    json_path = Path(workdir) / ".pipeline-assets" / "episode-meta.json"
    assert json_path.exists(), f"episode-meta.json missing at {json_path}"
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    # AssetBus.write wraps in v3.0 envelope when envelope=True (default).
    assert parsed.get("schema_version") == "3.0", (
        f"JSON slot must be envelope-wrapped; got {parsed!r}"
    )
    assert parsed.get("value") == record
