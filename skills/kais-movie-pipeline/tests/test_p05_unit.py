"""test_p05_unit.py — Phase 36-01 Task 6: unit tests for p05_pain_discovery.

Tests the V8.6 Step 5 atomic operation (creative_source + theory_critic
collaborate in a SINGLE delegate_task call). Mirrors Phase 35 test_p0N_unit.py
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

from pipeline.phases import p05_pain_discovery as p05  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    payload = {
        "pain_points": [
            {"level": "L1", "desc": "minor annoyance"},
            {"level": "L6", "desc": "existential wound"},
        ],
        "escalation_ladder": [
            {"step": 1, "intensity": 0.2},
            {"step": 6, "intensity": 1.0},
        ],
    }
    return f"Reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\n"


def _make_delegate_spy(captured: dict):
    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}

    return _mock


def _bus_with(script=None, bible=None):
    """Build an asset_bus_read lambda returning the given slot values."""
    def _read(slot):
        if slot == "script-draft":
            return script
        if slot == "character-bible":
            return bible
        return None
    return _read


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p05_goal_invokes_creative_source_and_theory_critic():
    """Test 1: V8.6 Step 5 atomic — goal mentions both experts via skill_view."""
    captured: dict = {}
    p05.run(
        episode_id="ep-005",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "skill_view(name='creative_source')" in captured["goal"]
    assert "skill_view(name='theory_critic')" in captured["goal"]


def test_p05_reads_character_bible_and_script_draft():
    """Test 2: reads both character-bible (p04) + script-draft (p03)."""
    captured: dict = {}
    bible = {"characters": [{"name": "Lin Mo", "wound": "abandonment"}]}
    script = {"scenes": [{"scene_id": 1, "content": "灵活就业者"}]}

    p05.run(
        episode_id="ep-005",
        asset_bus_read=_bus_with(script=script, bible=bible),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    combined = captured["goal"] + captured["context"]
    assert "Lin Mo" in combined
    assert "灵活就业者" in combined


def test_p05_calls_delegate_once_with_skills_file_toolsets():
    """Test 3: single delegate_task call with ['skills', 'file'] toolsets."""
    captured: dict = {}
    p05.run(
        episode_id="ep-005",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert captured["toolsets"] == ["skills", "file"]


def test_p05_writes_pain_points_and_escalation_ladder():
    """Test 4: writes pain-points + escalation-ladder from parsed output."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p05.run(
        episode_id="ep-005",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "pain-points" in written
    assert "escalation-ladder" in written
    assert written["pain-points"][0]["level"] == "L1"
    assert written["escalation-ladder"][-1]["intensity"] == 1.0


def test_p05_triggers_gate_shot_prep_when_provided():
    """Test 5: triggers Gate 4 'shot-prep' when trigger_gate is provided."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    result = p05.run(
        episode_id="ep-005",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [("shot-prep", "ep-005")]
    assert result["gate"]["gate_id"] == "shot-prep"
    assert p05.GATE_ID == "shot-prep"


def test_p05_skips_gate_when_trigger_gate_is_none():
    """Test 6: when trigger_gate is None, gate is skipped despite GATE_ID set."""
    result = p05.run(
        episode_id="ep-005",
        asset_bus_read=_bus_with(script={}, bible={}),
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None


def test_p05_handles_empty_input_slots_gracefully():
    """Test 7: empty character-bible + script-draft → empty dicts, no crash."""
    result = p05.run(
        episode_id="ep-005",
        asset_bus_read=lambda slot: None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["phase"] == "p05_pain_discovery"
