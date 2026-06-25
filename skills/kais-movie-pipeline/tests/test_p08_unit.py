"""test_p08_unit.py — Phase 36-02 unit tests for p08_scene_selection.

Mocked tests for ``pipeline/phases/p08_scene_selection.py``. Per CONTEXT
D-35-08 all tests inject mocks via the run() signature — no real subagents,
no real network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - reads the correct input slots (scene-images + spatio-temporal-script)
  - goal mentions both assigned experts (cinematographer + editor) via skill_view
  - calls delegate_task exactly ONCE
  - calls delegate_task with ["skills", "file"] toolsets
  - writes the correct output slots (scene-selection + geometry-bed)
  - GATE_ID is None (no gate for p08)
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

from pipeline.phases import p08_scene_selection as p08  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "scene_selection": [{"scene_id": "s1", "approved": True}],
        "geometry_bed": {"anchor_frame": "shared-3D", "shots_aligned": 12},
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


def test_p08_reads_correct_input_slots():
    """Test 1: run() reads scene-images + spatio-temporal-script slots."""
    read_slots: list = []

    def read_spy(slot):
        read_slots.append(slot)
        if slot == "scene-images":
            return [{"scene_id": "s1"}]
        if slot == "spatio-temporal-script":
            return {"scenes": [{"id": "s1"}]}
        return None

    p08.run(
        episode_id="ep-008",
        asset_bus_read=read_spy,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    assert "scene-images" in read_slots, (
        f"p08 must read scene-images slot; got {read_slots}"
    )
    assert "spatio-temporal-script" in read_slots, (
        f"p08 must read spatio-temporal-script slot; got {read_slots}"
    )


def test_p08_goal_mentions_both_assigned_experts_via_skill_view():
    """Test 2: run() goal mentions cinematographer + editor via skill_view."""
    captured: dict = {}
    p08.run(
        episode_id="ep-008",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-images", "spatio-temporal-script"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    goal = captured["goal"]
    assert "skill_view(name='cinematographer')" in goal, (
        f"goal must mention skill_view(name='cinematographer'); got: {goal!r}"
    )
    assert "skill_view(name='editor')" in goal, (
        f"goal must mention skill_view(name='editor'); got: {goal!r}"
    )


def test_p08_calls_delegate_task_once_with_skills_file_toolsets():
    """Test 3: run() calls delegate_task once with ['skills', 'file'] toolsets."""
    captured: dict = {}
    call_count = {"n": 0}

    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["toolsets"] = toolsets
        call_count["n"] += 1
        return {"summary": _ok_summary()}

    p08.run(
        episode_id="ep-008",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-images", "spatio-temporal-script"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_mock,
        trigger_gate=None,
    )
    assert call_count["n"] == 1, (
        f"p08 must call delegate_task exactly once; got {call_count['n']}"
    )
    assert captured["toolsets"] == ["skills", "file"]


def test_p08_writes_correct_output_slots():
    """Test 4: run() writes scene-selection + geometry-bed slots."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p08.run(
        episode_id="ep-008",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-images", "spatio-temporal-script"
        ) else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "scene-selection" in written, "scene-selection slot must be written"
    assert "geometry-bed" in written, "geometry-bed slot must be written"
    assert written["scene-selection"][0]["scene_id"] == "s1"
    assert written["geometry-bed"]["anchor_frame"] == "shared-3D"


def test_p08_gate_id_is_none():
    """Test 5: p08 module GATE_ID constant is None (no gate for p08)."""
    assert p08.GATE_ID is None, (
        f"p08 GATE_ID must be None per CONTEXT D-36-02 table; got {p08.GATE_ID!r}"
    )


def test_p08_gate_result_always_none_even_when_trigger_gate_provided():
    """Test 6: gate result is None regardless of trigger_gate arg (GATE_ID=None).

    Even if a trigger_gate callable is passed in, p08's run() must NOT call
    it because GATE_ID is None (CF-36-04 conditional gate triggering).
    """
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "should-not-happen"}

    result = p08.run(
        episode_id="ep-008",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "scene-images", "spatio-temporal-script"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [], (
        f"p08 must NOT call trigger_gate (GATE_ID=None); got {gate_calls}"
    )
    assert result["gate"] is None
    assert result["phase"] == "p08_scene_selection"


def test_p08_handles_empty_input_slots_gracefully():
    """Test 7: run() does not crash when input slots are empty/missing."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    result = p08.run(
        episode_id="ep-008",
        asset_bus_read=lambda slot: None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "scene-selection" in written
    assert "geometry-bed" in written
    assert result["gate"] is None
