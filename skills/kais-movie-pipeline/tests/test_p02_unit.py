"""test_p02_unit.py — Phase 35-03 Task 2 unit tests (TDD RED→GREEN).

Mocked tests for ``pipeline/phases/p02_outline.py``. Per CONTEXT D-35-08
all tests inject mocks via the run() signature — no real subagents, no
network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - V8.6 §2 atomic operation: goal mentions BOTH creative_source AND screenplay
  - reads topic-kernel slot (output of p01) and embeds in goal/context
  - writes story-framework slot (StoryKernel + Snowflake + Snyder beats)
  - triggers Gate 2 'story-framework-outline' when trigger_gate provided
  - gate is None when trigger_gate is None
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p02_outline as p02  # noqa: E402


def _ok_summary() -> str:
    payload = {
        "story_kernel": {"title": "x", "premise": "y"},
        "snowflake_artifacts": {"step4_synopsis": "..."},
        "snyder_beats": [{"beat": "Opening Image", "content": "..."}],
    }
    return f"Reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\n"


def _make_delegate_spy(captured: dict):
    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}

    return _mock


def test_p02_goal_invokes_creative_source_and_screenplay():
    """Test 1: goal must mention BOTH expert skill_views (V8.6 §2 atomic)."""
    captured: dict = {}
    p02.run(
        episode_id="ep-002",
        asset_bus_read=lambda slot: {"title": "x"} if slot == "topic-kernel" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    assert "skill_view(name='creative_source')" in captured["goal"], (
        f"goal must mention creative_source; got: {captured['goal']!r}"
    )
    assert "skill_view(name='screenplay')" in captured["goal"], (
        f"goal must mention screenplay; got: {captured['goal']!r}"
    )


def test_p02_reads_topic_kernel_and_embeds_in_goal():
    """Test 2: reads topic-kernel slot and embeds content in goal/context."""
    captured: dict = {}
    topic_kernel = {"title": "灵活就业者", "audience": "都市青年"}

    p02.run(
        episode_id="ep-002",
        asset_bus_read=lambda slot: topic_kernel if slot == "topic-kernel" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    combined = captured["goal"] + captured["context"]
    assert "灵活就业者" in combined, f"topic-kernel content must reach expert; combined={combined!r}"


def test_p02_writes_story_framework_slot():
    """Test 3: writes story-framework with StoryKernel + Snowflake + Snyder beats."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p02.run(
        episode_id="ep-002",
        asset_bus_read=lambda slot: {"title": "x"} if slot == "topic-kernel" else None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    assert "story-framework" in written, "story-framework slot must be written"
    sf = written["story-framework"]
    # StoryKernel + Snowflake + Snyder beats structure per V8.6 §2 atomic output.
    assert "story_kernel" in sf
    assert "snowflake_artifacts" in sf
    assert "snyder_beats" in sf


def test_p02_triggers_gate_when_provided():
    """Test 4: triggers Gate 2 'story-framework-outline' when trigger_gate provided."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    result = p02.run(
        episode_id="ep-002",
        asset_bus_read=lambda slot: {"title": "x"} if slot == "topic-kernel" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )

    assert gate_calls == [("story-framework-outline", "ep-002")]
    assert result["gate"] == {"status": "paused", "gate_id": "story-framework-outline"}


def test_p02_gate_none_when_trigger_gate_is_none():
    """Test 5: gate is None when trigger_gate is None."""
    result = p02.run(
        episode_id="ep-002",
        asset_bus_read=lambda slot: {"title": "x"} if slot == "topic-kernel" else None,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None
    assert result["phase"] == "p02_outline"
