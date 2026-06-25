"""test_p03_unit.py + test_registry.py — Phase 35-03 Task 3 (TDD RED→GREEN).

Tests for:
  - p03_script_audit.py (V8.6 §3 atomic: screenplay + script_auditor loop)
  - PHASE_REGISTRY in pipeline/phases/__init__.py (3 entries, correct DAG)

All tests inject mocks via run() signature (D-35-08). No real subagents.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

# Force a fresh import of the registry so test_registry tests see the
# populated entries (the module may have been imported earlier with the stub).
import importlib  # noqa: E402

from pipeline.phases import p03_script_audit as p03  # noqa: E402
from pipeline import phases as phases_mod  # noqa: E402


# ---------------------------------------------------------------------------
# p03 helpers
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    payload = {
        "script": {"scenes": [{"scene_id": 1, "content": "..."}]},
        "audit": {
            "scores": {"drama": 80, "rhythm": 75, "character": 82, "logic": 78, "theme": 85},
            "total_score": 80,
            "predicted_completion_band": "A",
        },
    }
    return f"Reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\n"


def _make_delegate_spy(captured: dict):
    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}

    return _mock


# ---------------------------------------------------------------------------
# p03 tests
# ---------------------------------------------------------------------------


def test_p03_goal_invokes_screenplay_and_script_auditor():
    """Test 1: V8.6 §3 atomic — goal mentions screenplay + script_auditor."""
    captured: dict = {}
    p03.run(
        episode_id="ep-003",
        asset_bus_read=lambda slot: {"story_kernel": {}} if slot == "story-framework" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "skill_view(name='screenplay')" in captured["goal"]
    assert "skill_view(name='script_auditor')" in captured["goal"]


def test_p03_reads_story_framework_and_embeds_in_goal():
    """Test 2: reads story-framework (p02 output) and embeds in goal/context."""
    captured: dict = {}
    sf = {"story_kernel": {"title": "灵活就业者"}}

    p03.run(
        episode_id="ep-003",
        asset_bus_read=lambda slot: sf if slot == "story-framework" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    combined = captured["goal"] + captured["context"]
    assert "灵活就业者" in combined


def test_p03_writes_script_draft_and_audit_report():
    """Test 3: writes script-draft + audit-report from parsed output."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p03.run(
        episode_id="ep-003",
        asset_bus_read=lambda slot: {"story_kernel": {}} if slot == "story-framework" else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "script-draft" in written
    assert "audit-report" in written
    assert written["script-draft"]["scenes"][0]["scene_id"] == 1
    assert written["audit-report"]["total_score"] == 80


def test_p03_triggers_gate_when_provided():
    """Test 4: triggers Gate 3 'script-audit'."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    result = p03.run(
        episode_id="ep-003",
        asset_bus_read=lambda slot: {"story_kernel": {}} if slot == "story-framework" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [("script-audit", "ep-003")]
    assert result["gate"]["gate_id"] == "script-audit"


# ---------------------------------------------------------------------------
# PHASE_REGISTRY tests
# ---------------------------------------------------------------------------


def test_registry_has_three_entries():
    """Test 5: PHASE_REGISTRY contains p01/p02/p03 with correct depends_on graph."""
    # Force reimport in case the stub was loaded earlier.
    importlib.reload(phases_mod)
    assert len(phases_mod.PHASE_REGISTRY) == 3, (
        f"expected 3 phases, got {len(phases_mod.PHASE_REGISTRY)}"
    )
    ids = [e["id"] for e in phases_mod.PHASE_REGISTRY]
    assert ids == ["p01_hook_topic", "p02_outline", "p03_script_audit"], (
        f"wrong ids: {ids}"
    )
    assert phases_mod.PHASE_REGISTRY[1]["depends_on"] == ["p01_hook_topic"]
    assert phases_mod.PHASE_REGISTRY[2]["depends_on"] == ["p02_outline"]


def test_registry_modules_expose_run():
    """Test 6: each PHASE_REGISTRY entry exposes a callable `run` on its module."""
    importlib.reload(phases_mod)
    for entry in phases_mod.PHASE_REGISTRY:
        assert hasattr(entry["module"], "run"), (
            f"module {entry['id']} missing run()"
        )
        assert callable(entry["module"].run), (
            f"module {entry['id']}.run is not callable"
        )
