"""test_p06_unit.py — Phase 36-01 Task 7: unit tests for p06_spatio_temporal_script.

Tests the V8.6 Step 6 / §5 atomic operation (screenplay + cinematographer +
script_auditor collaborate in a SINGLE delegate_task call despite 3 experts —
the atomic §5 invariant per CF-36-03). Mirrors Phase 35 test_p0N_unit.py
pattern (Pattern 5). All tests inject mocks via run() signature (D-35-08) —
no real subagent spawns.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p06_spatio_temporal_script as p06  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    payload = {
        "spatio_temporal_script": {
            "shots": [
                {"shot_id": "s1", "axis": "180-left", "composition_lock": "OTS"},
            ],
        },
        "final_audit": {
            "scores": {"drama": 85, "rhythm": 80, "character": 82,
                       "logic": 88, "theme": 90},
            "total_score": 85,
            "predicted_completion_band": "A",
        },
    }
    return f"Reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\n"


def _make_delegate_spy(captured: dict, call_counter: list | None = None):
    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        if call_counter is not None:
            call_counter.append(1)
        return {"summary": _ok_summary()}

    return _mock


def _bus_with(script=None, bible=None):
    def _read(slot):
        if slot == "script-draft":
            return script
        if slot == "character-bible":
            return bible
        return None
    return _read


# ---------------------------------------------------------------------------
# Tests — atomic §5 invariant: 3 experts, 1 delegate_task call
# ---------------------------------------------------------------------------


def test_p06_goal_invokes_all_three_experts_via_skill_view():
    """Test 1: V8.6 §5 atomic — goal mentions screenplay + cinematographer +
    script_auditor (all 3 skill_views)."""
    captured: dict = {}
    p06.run(
        episode_id="ep-006",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "skill_view(name='screenplay')" in captured["goal"]
    assert "skill_view(name='cinematographer')" in captured["goal"]
    assert "skill_view(name='script_auditor')" in captured["goal"]


def test_p06_atomic_single_delegate_call_despite_three_experts():
    """Test 2: CF-36-03 invariant — exactly 1 delegate_task call despite 3
    collaborating experts (atomic §5)."""
    call_counter: list = []
    p06.run(
        episode_id="ep-006",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}, call_counter),
        trigger_gate=None,
    )
    assert len(call_counter) == 1, (
        f"atomic §5 violated: expected 1 delegate_task call, got {len(call_counter)}"
    )


def test_p06_reads_script_draft_and_character_bible():
    """Test 3: reads both script-draft (p03) + character-bible (p04)."""
    captured: dict = {}
    script = {"scenes": [{"scene_id": 1, "content": "灵活就业者"}]}
    bible = {"characters": [{"name": "Lin Mo"}]}

    p06.run(
        episode_id="ep-006",
        asset_bus_read=_bus_with(script=script, bible=bible),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    combined = captured["goal"] + captured["context"]
    assert "灵活就业者" in combined
    assert "Lin Mo" in combined


def test_p06_writes_spatio_temporal_script_and_final_audit():
    """Test 4: writes spatio-temporal-script + final-audit from parsed output."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p06.run(
        episode_id="ep-006",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "spatio-temporal-script" in written
    assert "final-audit" in written
    assert written["spatio-temporal-script"]["shots"][0]["shot_id"] == "s1"
    assert written["final-audit"]["total_score"] == 85


def test_p06_triggers_gate_spatio_temporal_when_provided():
    """Test 5: triggers Gate 6 'spatio-temporal' when trigger_gate provided."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    result = p06.run(
        episode_id="ep-006",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [("spatio-temporal", "ep-006")]
    assert result["gate"]["gate_id"] == "spatio-temporal"
    assert p06.GATE_ID == "spatio-temporal"


def test_p06_skips_gate_when_trigger_gate_is_none():
    """Test 6: when trigger_gate is None, gate skipped despite GATE_ID set."""
    result = p06.run(
        episode_id="ep-006",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None


def test_p06_handles_empty_input_slots_gracefully():
    """Test 7: empty script-draft + character-bible → empty dicts, no crash."""
    result = p06.run(
        episode_id="ep-006",
        asset_bus_read=lambda slot: None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["phase"] == "p06_spatio_temporal_script"
