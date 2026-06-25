"""test_p09_unit.py — Phase 36-02 unit tests for p09_shot_breakdown.

Mocked tests for ``pipeline/phases/p09_shot_breakdown.py``. Per CONTEXT
D-35-08 all tests inject mocks via the run() signature — no real subagents,
no real network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - reads the correct input slots (scene-selection + spatio-temporal-script
    + character-bible)
  - goal mentions both assigned experts (cinematographer + continuity_auditor)
    via skill_view
  - calls delegate_task exactly ONCE
  - calls delegate_task with ["skills", "file"] toolsets
  - writes the correct output slots (shot-list + e-konte-sheets)
  - GATE_ID is None (no gate for p09)
  - gate result is None regardless of trigger_gate
  - handles empty input slots gracefully
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p09_shot_breakdown as p09  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "shot_list": [
            {"shot_id": "shot-1", "intent": "establish", "duration": 3.5},
            {"shot_id": "shot-2", "intent": "reaction", "duration": 2.0},
        ],
        "e_konte_sheets": [
            {
                "shot_id": "shot-1",
                "layers": ["composition", "camera", "lighting", "action", "dialogue"],
            },
        ],
    }
    return f"Expert reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _make_delegate_spy(captured: dict):
    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}

    return _mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p09_reads_correct_input_slots():
    """Test 1: run() reads scene-selection + spatio-temporal-script + character-bible."""
    read_slots: list = []

    def read_spy(slot):
        read_slots.append(slot)
        if slot == "scene-selection":
            return [{"scene_id": "s1"}]
        if slot == "spatio-temporal-script":
            return {"scenes": [{"id": "s1"}]}
        if slot == "character-bible":
            return {"anchors": {"lead": "L1"}}
        return None

    p09.run(
        episode_id="ep-009",
        asset_bus_read=read_spy,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    assert "scene-selection" in read_slots, (
        f"p09 must read scene-selection slot; got {read_slots}"
    )
    assert "spatio-temporal-script" in read_slots, (
        f"p09 must read spatio-temporal-script slot; got {read_slots}"
    )
    assert "character-bible" in read_slots, (
        f"p09 must read character-bible slot; got {read_slots}"
    )


def test_p09_goal_mentions_both_assigned_experts_via_skill_view():
    """Test 2: run() goal mentions cinematographer + continuity_auditor via skill_view."""
    captured: dict = {}
    p09.run(
        episode_id="ep-009",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    goal = captured["goal"]
    assert "skill_view(name='cinematographer')" in goal, (
        f"goal must mention skill_view(name='cinematographer'); got: {goal!r}"
    )
    assert "skill_view(name='continuity_auditor')" in goal, (
        f"goal must mention skill_view(name='continuity_auditor'); got: {goal!r}"
    )


def test_p09_calls_delegate_task_once_with_skills_file_toolsets():
    """Test 3: run() calls delegate_task once with ['skills', 'file'] toolsets."""
    captured: dict = {}
    call_count = {"n": 0}

    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["toolsets"] = toolsets
        call_count["n"] += 1
        return {"summary": _ok_summary()}

    p09.run(
        episode_id="ep-009",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_mock,
        trigger_gate=None,
    )
    assert call_count["n"] == 1, (
        f"p09 must call delegate_task exactly once; got {call_count['n']}"
    )
    assert captured["toolsets"] == ["skills", "file"]


def test_p09_writes_correct_output_slots():
    """Test 4: run() writes shot-list + e-konte-sheets slots."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p09.run(
        episode_id="ep-009",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible"
        ) else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "shot-list" in written, "shot-list slot must be written"
    assert "e-konte-sheets" in written, "e-konte-sheets slot must be written"
    assert written["shot-list"][0]["shot_id"] == "shot-1"
    assert written["e-konte-sheets"][0]["shot_id"] == "shot-1"


def test_p09_gate_id_is_none():
    """Test 5: p09 module GATE_ID constant is None (no gate for p09)."""
    assert p09.GATE_ID is None, (
        f"p09 GATE_ID must be None per CONTEXT D-36-02 table; got {p09.GATE_ID!r}"
    )


def test_p09_gate_result_always_none_even_when_trigger_gate_provided():
    """Test 6: gate result is None regardless of trigger_gate arg (GATE_ID=None)."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "should-not-happen"}

    result = p09.run(
        episode_id="ep-009",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-selection", "spatio-temporal-script", "character-bible"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [], (
        f"p09 must NOT call trigger_gate (GATE_ID=None); got {gate_calls}"
    )
    assert result["gate"] is None
    assert result["phase"] == "p09_shot_breakdown"


def test_p09_handles_empty_input_slots_gracefully():
    """Test 7: run() does not crash when input slots are empty/missing."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    result = p09.run(
        episode_id="ep-009",
        asset_bus_read=lambda slot: None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "shot-list" in written
    assert "e-konte-sheets" in written
    assert result["gate"] is None
