"""test_p01_unit.py — Phase 35-03 Task 1 unit tests (TDD RED→GREEN).

Mocked tests for ``pipeline/phases/p01_hook_topic.py``. Per CONTEXT D-35-08
all tests inject mocks via the run() signature — no real subagents, no real
network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - the right expert is invoked (goal mentions skill_view(name='hook_retention'))
  - the requirement slot is read and embedded in the goal/context
  - topic-kernel + hook-design slots are written from parsed expert output
  - gate "selection-topic-hook" is triggered when trigger_gate is provided
  - gate is None when trigger_gate is None
  - _parse_expert_output raises ValueError on malformed summary
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_runner.py).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p01_hook_topic as p01  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "topic_kernel": {"title": "灵活就业者", "audience": "都市青年"},
        "hook_design": {"type": "情感钩", "duration_sec": 3},
    }
    return f"Expert reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _make_delegate_spy(captured: dict):
    """Return a mock delegate_task that records its args + returns ok summary."""

    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}

    return _mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p01_goal_invokes_hook_retention_expert():
    """Test 1: run() calls delegate_task with goal mentioning skill_view(name='hook_retention')."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)

    p01.run(
        episode_id="ep-001",
        asset_bus_read=lambda slot: {"topic": "x"} if slot == "requirement" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )

    assert "skill_view(name='hook_retention')" in captured["goal"], (
        f"goal must mention skill_view(name='hook_retention'); got: {captured['goal']!r}"
    )


def test_p01_reads_requirement_slot_and_embeds_in_goal():
    """Test 2: run() reads requirement slot and embeds its content in goal/context."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)
    requirement = {"topic": "灵活就业者", "tone": "warm"}

    p01.run(
        episode_id="ep-001",
        asset_bus_read=lambda slot: requirement if slot == "requirement" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )

    # Goal OR context must carry the requirement content.
    combined = captured["goal"] + captured["context"]
    assert "灵活就业者" in combined, (
        f"requirement content must reach the expert; combined={combined!r}"
    )


def test_p01_writes_topic_kernel_and_hook_design_slots():
    """Test 3: run() writes topic-kernel + hook-design from parsed expert output."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p01.run(
        episode_id="ep-001",
        asset_bus_read=lambda slot: {"topic": "x"} if slot == "requirement" else None,
        asset_bus_write=write_spy,
        delegate_task=delegate,
        trigger_gate=None,
    )

    assert "topic-kernel" in written, "topic-kernel slot must be written"
    assert "hook-design" in written, "hook-design slot must be written"
    assert written["topic-kernel"]["title"] == "灵活就业者"
    assert written["hook-design"]["type"] == "情感钩"


def test_p01_triggers_gate_when_provided():
    """Test 4: run() calls trigger_gate('selection-topic-hook', episode_id) and returns result."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    result = p01.run(
        episode_id="ep-001",
        asset_bus_read=lambda slot: {"topic": "x"} if slot == "requirement" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )

    assert gate_calls == [("selection-topic-hook", "ep-001")], (
        f"trigger_gate must be called once with (selection-topic-hook, ep-001); got {gate_calls}"
    )
    assert result["gate"] == {"status": "paused", "gate_id": "selection-topic-hook"}


def test_p01_gate_none_when_trigger_gate_is_none():
    """Test 5: run() sets gate=None when trigger_gate is None."""
    result = p01.run(
        episode_id="ep-001",
        asset_bus_read=lambda slot: {"topic": "x"} if slot == "requirement" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None
    assert result["phase"] == "p01_hook_topic"


def test_p01_parse_expert_output_raises_on_missing_json_block():
    """Test 6: _parse_expert_output raises ValueError when summary has no fenced JSON."""
    with pytest.raises(ValueError, match="missing JSON block"):
        p01._parse_expert_output({"summary": "no json here at all"})
