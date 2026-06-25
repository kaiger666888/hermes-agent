"""test_p07_unit.py — Phase 36-02 unit tests for p07_scene_generation.

Mocked tests for ``pipeline/phases/p07_scene_generation.py``. Per CONTEXT
D-35-08 all tests inject mocks via the run() signature — no real subagents,
no real network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - reads the correct input slots (spatio-temporal-script + character-assets)
  - goal mentions all 4 assigned experts via skill_view (atomic §4 invariant)
  - calls delegate_task exactly ONCE despite 4 experts (atomic §4 invariant)
  - calls delegate_task with ["skills", "file"] toolsets
  - writes the correct output slots (scene-images/style-vector/color-intent)
  - triggers Gate 5 "scene-design" when trigger_gate is provided
  - skips gate (gate=None) when trigger_gate is None
  - handles empty input slots gracefully
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_p01_unit.py).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p07_scene_generation as p07  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "scene_images": [{"scene_id": "s1", "views": ["front", "side"]}],
        "style_vector": {
            "genre": "urban-fantasy",
            "mood": "warm",
            "aesthetic": "cinematic",
            "pace": "medium",
            "color": "amber",
        },
        "color_intent": {"cxsxz": 28, "lut_plan": {"shadows": "cool"}},
    }
    return f"Expert reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _make_delegate_spy(captured: dict, call_count: dict | None = None):
    """Return a mock delegate_task that records its args + returns ok summary.

    Tracks call count so the atomic §4 invariant (exactly 1 delegate_task
    call despite 4 experts) can be asserted.
    """

    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        if call_count is not None:
            call_count["n"] = call_count.get("n", 0) + 1
        return {"summary": _ok_summary()}

    return _mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p07_reads_correct_input_slots():
    """Test 1: run() reads spatio-temporal-script + character-assets slots."""
    read_slots: list = []

    def read_spy(slot):
        read_slots.append(slot)
        if slot == "spatio-temporal-script":
            return {"scenes": [{"id": "s1"}]}
        if slot == "character-assets":
            return {"anchors": {"lead": "L1"}}
        return None

    p07.run(
        episode_id="ep-007",
        asset_bus_read=read_spy,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    assert "spatio-temporal-script" in read_slots, (
        f"p07 must read spatio-temporal-script slot; got {read_slots}"
    )
    assert "character-assets" in read_slots, (
        f"p07 must read character-assets slot; got {read_slots}"
    )


def test_p07_goal_mentions_all_four_assigned_experts_via_skill_view():
    """Test 2: run() goal mentions all 4 experts via skill_view (atomic §4 invariant)."""
    captured: dict = {}
    p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "spatio-temporal-script", "character-assets"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    goal = captured["goal"]
    # All 4 experts must appear via skill_view — this is the atomic §4 contract.
    for expert in (
        "skill_view(name='visual_executor')",
        "skill_view(name='prompt_injector')",
        "skill_view(name='style_genome')",
        "skill_view(name='colorist')",
    ):
        assert expert in goal, (
            f"goal must mention {expert}; got: {goal!r}"
        )


def test_p07_calls_delegate_task_exactly_once_atomic_invariant():
    """Test 3: run() calls delegate_task EXACTLY ONCE despite 4 experts.

    This is the V8.6 §4 atomic operation invariant (CF-36-03, Pattern 3) —
    splitting atomic ops across multiple delegate_task calls would
    re-introduce V8.4-era 25-step complexity.
    """
    call_count: dict = {}
    delegate = _make_delegate_spy({}, call_count)
    p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "spatio-temporal-script", "character-assets"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )
    assert call_count.get("n", 0) == 1, (
        f"p07 must call delegate_task exactly once (atomic §4 invariant); "
        f"got {call_count.get('n', 0)} calls"
    )


def test_p07_calls_delegate_task_with_skills_file_toolsets():
    """Test 4: run() passes ["skills", "file"] as toolsets."""
    captured: dict = {}
    p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "spatio-temporal-script", "character-assets"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert captured["toolsets"] == ["skills", "file"], (
        f"toolsets must be ['skills', 'file']; got {captured['toolsets']!r}"
    )


def test_p07_writes_correct_output_slots():
    """Test 5: run() writes scene-images + style-vector + color-intent slots."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "spatio-temporal-script", "character-assets"
        ) else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "scene-images" in written, "scene-images slot must be written"
    assert "style-vector" in written, "style-vector slot must be written"
    assert "color-intent" in written, "color-intent slot must be written"
    # Verify the parsed payload flows through.
    assert written["scene-images"][0]["scene_id"] == "s1"
    assert written["style-vector"]["genre"] == "urban-fantasy"
    assert written["color-intent"]["cxsxz"] == 28


def test_p07_triggers_scene_design_gate_when_provided():
    """Test 6: run() calls trigger_gate('scene-design', episode_id) and returns result."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    result = p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "spatio-temporal-script", "character-assets"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [("scene-design", "ep-007")], (
        f"trigger_gate must be called once with (scene-design, ep-007); "
        f"got {gate_calls}"
    )
    assert result["gate"] == {"status": "paused", "gate_id": "scene-design"}
    assert result["phase"] == "p07_scene_generation"


def test_p07_gate_none_when_trigger_gate_is_none():
    """Test 7: run() sets gate=None when trigger_gate is None."""
    result = p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: {"x": 1} if slot in (
            "spatio-temporal-script", "character-assets"
        ) else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None
    assert result["phase"] == "p07_scene_generation"


def test_p07_handles_empty_input_slots_gracefully():
    """Test 8: run() does not crash when input slots are empty/missing."""
    # All slots return None — first-run / missing-data scenario.
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    result = p07.run(
        episode_id="ep-007",
        asset_bus_read=lambda slot: None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    # Should still write all 3 output slots (with empty defaults).
    assert "scene-images" in written
    assert "style-vector" in written
    assert "color-intent" in written
    assert result["gate"] is None
