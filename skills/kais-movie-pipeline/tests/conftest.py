"""conftest.py — shared pytest fixtures for kais-movie-pipeline tests (Phase 35-05).

All fixtures honor D-35-08: no real subagents / network / GPU. Each test that
needs an injected delegate / gate / store / bus builds them via these factories
or via the ``inject=`` parameter on ``run_episode`` (preferred — avoids
monkeypatching production code).

Fixtures exposed
----------------
- ``mock_delegate_factory`` — callable ``(output_dict) -> delegate_task``
  Each call returns a fresh mock whose summary embeds ``output_dict`` as a
  fenced JSON block (matches the phase-module parse contract).
- ``tmp_asset_bus`` — ``(bus, workdir)`` tuple. ``bus`` is a real
  ``AssetBus(str(tmp_path))``; tests read/write slots through it.
- ``tmp_state_store`` — ``(store, workdir)`` tuple. ``store`` is a real
  ``PipelineStateStore(str(tmp_path))`` for checkpoint round-trip tests.
- ``fake_registry`` — monkeypatches ``pipeline.phases.PHASE_REGISTRY`` with
  an empty list, restores the original on teardown. Tests append entries.
- ``make_fake_phase`` — factory ``(phase_id, output_dict, gate_id=None) ->
  fake_module``. The returned module exposes ``run()`` with the standard
  phase-module signature and records its calls for assertions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

# Put the skill directory on sys.path so ``pipeline`` is importable. The
# skill directory uses hyphens which aren't a valid Python identifier, so
# we add the parent path and import the ``pipeline`` subpackage directly.
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))


# ---------------------------------------------------------------------------
# mock_delegate_factory
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_delegate_factory():
    """Return a factory ``(output_dict) -> delegate_task_callable``.

    The returned callable matches the production ``delegate_task`` signature
    ``(goal, context, toolsets) -> dict`` and emits ``output_dict`` as a
    fenced JSON block inside ``summary`` (the contract phase modules parse).

    The mock also captures its most recent invocation arguments on the
    ``.last_call`` attribute so tests can assert on goal/context/toolsets
    without an extra closure.
    """

    def _factory(output_dict: dict) -> Callable[..., dict]:
        summary = (
            "Expert completed. Output:\n"
            f"```json\n{json.dumps(output_dict, ensure_ascii=False)}\n```"
        )

        def _delegate(goal: str, context: str, toolsets: list[str]) -> dict:
            _delegate.last_call = {  # type: ignore[attr-defined]
                "goal": goal,
                "context": context,
                "toolsets": list(toolsets),
            }
            return {"summary": summary}

        _delegate.last_call = None  # type: ignore[attr-defined]
        _delegate.canned_output = output_dict  # type: ignore[attr-defined]
        return _delegate

    return _factory


# ---------------------------------------------------------------------------
# tmp_asset_bus — real AssetBus on tmp_path (D-35-08: real fs, isolated)
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_asset_bus(tmp_path):
    """Return ``(bus, workdir)`` — a real AssetBus rooted at tmp_path.

    Uses the production AssetBus class so tests exercise the real write/read
    envelope logic. Isolated per test via pytest's ``tmp_path``.
    """
    from plugins.pipeline_state.asset_bus import AssetBus

    workdir = str(tmp_path)
    bus = AssetBus(workdir)
    return bus, workdir


# ---------------------------------------------------------------------------
# tmp_state_store — real PipelineStateStore on tmp_path
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_state_store(tmp_path):
    """Return ``(store, workdir)`` — a real PipelineStateStore on tmp_path."""
    from plugins.pipeline_state.store import PipelineStateStore

    workdir = str(tmp_path)
    store = PipelineStateStore(workdir)
    return store, workdir


# ---------------------------------------------------------------------------
# fake_registry — save/restore PHASE_REGISTRY around each test
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_registry():
    """Yield ``PHASE_REGISTRY`` after clearing it; restore on teardown.

    Tests append entries (``{"id": ..., "module": ..., "depends_on": [...]}``)
    to drive ``run_episode``. The registry is a module-level mutable list.

    **Cross-module binding care:** ``runner.py`` does
    ``from pipeline.phases import PHASE_REGISTRY`` at import time, which binds
    ``runner.PHASE_REGISTRY`` to the SAME list object. As long as we mutate
    the list IN PLACE (``.clear()`` / ``.extend()``), both modules see the
    change. However, sibling test ``test_p03_unit.py`` (Phase 35-03) calls
    ``importlib.reload(phases_mod)``, which RE-BINDS ``phases_mod.PHASE_REGISTRY``
    to a NEW list. After that the runner still holds the OLD list reference
    and our in-place mutations on the new list never reach it.

    We therefore also rebind ``runner.PHASE_REGISTRY`` to point at the same
    shared list object the test mutates. On teardown we restore both module
    attributes to their pre-test snapshots.
    """
    from pipeline import phases as phases_mod
    from pipeline import runner as runner_mod

    saved_runner_list = list(runner_mod.PHASE_REGISTRY)
    saved_phases_list = list(phases_mod.PHASE_REGISTRY)

    shared: list = []  # fresh shared object both modules will look at
    phases_mod.PHASE_REGISTRY = shared
    runner_mod.PHASE_REGISTRY = shared

    yield shared

    # Restore both modules to their pre-test views.
    phases_mod.PHASE_REGISTRY = list(saved_phases_list)
    runner_mod.PHASE_REGISTRY = list(saved_runner_list)


# ---------------------------------------------------------------------------
# make_fake_phase — factory for stub phase modules
# ---------------------------------------------------------------------------


@pytest.fixture
def make_fake_phase():
    """Return a factory ``(phase_id, output_dict, gate_id=None) -> fake_module``.

    The fake module exposes ``run(episode_id, asset_bus_read, asset_bus_write,
    delegate_task, trigger_gate=None)`` matching the production phase-module
    signature. It records its invocation on ``module.calls`` and exercises
    the gate (if ``gate_id`` set + ``trigger_gate`` wired) so tests can assert
    on gate triggering behavior.
    """

    def _factory(
        phase_id: str,
        output_dict: dict | None = None,
        gate_id: str | None = None,
    ) -> Any:
        calls: dict = {"count": 0, "args": None}
        canned_output = output_dict or {}

        def run(
            episode_id,
            asset_bus_read,
            asset_bus_write,
            delegate_task,
            trigger_gate=None,
        ):
            calls["count"] += 1
            calls["args"] = {
                "episode_id": episode_id,
                "has_read": callable(asset_bus_read),
                "has_write": callable(asset_bus_write),
                "has_delegate": callable(delegate_task),
                "trigger_gate": trigger_gate,
            }
            # Drive the gate if configured + wired (mirrors real phase modules)
            gate_result = None
            if gate_id and trigger_gate:
                gate_result = trigger_gate(gate_id, episode_id)
            return {
                "phase": phase_id,
                "outputs": canned_output,
                "gate": gate_result,
            }

        class _FakeModule:
            __name__ = f"fake_{phase_id}"

        _FakeModule.run = staticmethod(run)
        _FakeModule.calls = calls  # type: ignore[attr-defined]
        _FakeModule.phase_id = phase_id  # type: ignore[attr-defined]
        _FakeModule.gate_id = gate_id  # type: ignore[attr-defined]
        return _FakeModule

    return _factory
