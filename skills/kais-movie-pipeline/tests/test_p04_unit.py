"""test_p04_unit.py — Phase 36-01 Task 5: unit tests for p04_character_design.

Tests the V8.6 Step 4 atomic operation (character_designer + visual_executor
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

from pipeline.phases import p04_character_design as p04  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    payload = {
        "character_bible": {
            "characters": [
                {"id": "c1", "name": "Lin Mo", "anchor_4d": {"trait": "stoic"}},
            ],
        },
        "character_assets": {
            "L1_anchors": [{"char_id": "c1", "type": "identity"}],
            "L2_expressions": [],
            "L3_costumes": [],
            "L4_props": [],
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
# Tests
# ---------------------------------------------------------------------------


def test_p04_goal_invokes_character_designer_and_visual_executor():
    """Test 1: V8.6 Step 4 atomic — goal mentions both experts via skill_view."""
    captured: dict = {}
    p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: {"scenes": []} if slot == "script-draft" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "skill_view(name='character_designer')" in captured["goal"]
    assert "skill_view(name='visual_executor')" in captured["goal"]


def test_p04_reads_script_draft_and_embeds_in_goal():
    """Test 2: reads script-draft (p03 output) and embeds in goal/context."""
    captured: dict = {}
    script = {"scenes": [{"scene_id": 1, "content": "灵活就业者"}]}

    p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: script if slot == "script-draft" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    combined = captured["goal"] + captured["context"]
    assert "灵活就业者" in combined


def test_p04_calls_delegate_once_with_skills_file_toolsets():
    """Test 3: single delegate_task call with ['skills', 'file'] toolsets."""
    captured: dict = {}
    p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: {} if slot == "script-draft" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert captured["toolsets"] == ["skills", "file"]


def test_p04_writes_character_bible_and_character_assets():
    """Test 4: writes character-bible + character-assets from parsed output."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: {"scenes": []} if slot == "script-draft" else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "character-bible" in written
    assert "character-assets" in written
    assert written["character-bible"]["characters"][0]["name"] == "Lin Mo"
    assert written["character-assets"]["L1_anchors"][0]["char_id"] == "c1"


def test_p04_skips_gate_when_trigger_gate_is_none():
    """Test 5: GATE_ID is None for p04 — no gate triggered regardless."""
    result = p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: {} if slot == "script-draft" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None
    assert p04.GATE_ID is None  # documents the no-gate contract


def test_p04_does_not_trigger_gate_even_when_trigger_gate_provided():
    """Test 6: even with trigger_gate provided, p04 skips (GATE_ID is None)."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused"}

    p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: {} if slot == "script-draft" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == []  # GATE_ID None means gate never fires


def test_p04_handles_empty_input_slot_gracefully():
    """Test 7: empty script-draft slot → empty dict, no crash."""
    captured: dict = {}
    result = p04.run(
        episode_id="ep-004",
        asset_bus_read=lambda slot: None,  # empty everywhere
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert result["phase"] == "p04_character_design"
    # Empty input should still serialize cleanly into the goal
    assert "script_draft" in captured["context"]
