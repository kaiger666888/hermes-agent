"""test_p13_unit.py — Phase 36-04 unit tests for p13_delivery.

Mocked tests for ``pipeline/phases/p13_delivery.py``. Per CONTEXT
D-35-08 all tests inject mocks via the run() signature — no real subagents,
no real network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - reads the correct input slots (master-timeline + audio-stems + color-intent)
  - goal mentions all three assigned experts (colorist + compliance_gate +
    editor) via skill_view
  - calls delegate_task exactly ONCE with ["skills", "file"] toolsets
  - writes the correct output slots (master-mp4 + delivery-package)
  - GATE_ID is "final-delivery" (Gate 8)
  - triggers Gate 8 final-delivery when trigger_gate is provided
  - skips gate when trigger_gate is None
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

from pipeline.phases import p13_delivery as p13  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "master_mp4": {
            "path": "/out/ep-013/master.mp4",
            "duration": 6.0,
            "resolution": "1080x1920",
            "codec": "h264",
        },
        "delivery_package": {
            "manifest": ["master.mp4", "captions.srt", "compliance.json"],
            "metadata": {"episode_id": "ep-013", "version": "v1"},
            "compliance_report": {
                "cn_redline": "pass",
                "aigc_labeling": "pass",
                "status": "cleared",
            },
        },
    }
    return f"Expert reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _make_delegate_spy(captured: dict):
    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}

    return _mock


_P13_INPUTS = ("master-timeline", "audio-stems", "color-intent")


def _read_returns_value(slot):
    if slot == "master-timeline":
        return {"cuts": [{"frame": 0}]}
    if slot == "audio-stems":
        return {"bgm": {"path": "bgm.wav"}}
    if slot == "color-intent":
        return {"lut": "warm_orange"}
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p13_reads_correct_input_slots():
    """Test 1: run() reads master-timeline + audio-stems + color-intent."""
    read_slots: list = []

    def read_spy(slot):
        read_slots.append(slot)
        return _read_returns_value(slot)

    p13.run(
        episode_id="ep-013",
        asset_bus_read=read_spy,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    for expected in _P13_INPUTS:
        assert expected in read_slots, (
            f"p13 must read {expected} slot; got {read_slots}"
        )


def test_p13_goal_mentions_all_three_experts_via_skill_view():
    """Test 2: run() goal mentions colorist + compliance_gate + editor via skill_view."""
    captured: dict = {}
    p13.run(
        episode_id="ep-013",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    goal = captured["goal"]
    assert "skill_view(name='colorist')" in goal, (
        f"goal must mention skill_view(name='colorist'); got: {goal!r}"
    )
    assert "skill_view(name='compliance_gate')" in goal, (
        f"goal must mention skill_view(name='compliance_gate'); got: {goal!r}"
    )
    assert "skill_view(name='editor')" in goal, (
        f"goal must mention skill_view(name='editor'); got: {goal!r}"
    )


def test_p13_calls_delegate_task_once_with_skills_file_toolsets():
    """Test 3: run() calls delegate_task once with ['skills', 'file'] toolsets."""
    captured: dict = {}
    call_count = {"n": 0}

    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["toolsets"] = toolsets
        call_count["n"] += 1
        return {"summary": _ok_summary()}

    p13.run(
        episode_id="ep-013",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_mock,
        trigger_gate=None,
    )
    assert call_count["n"] == 1, (
        f"p13 must call delegate_task exactly once; got {call_count['n']}"
    )
    assert captured["toolsets"] == ["skills", "file"]


def test_p13_writes_correct_output_slots():
    """Test 4: run() writes master-mp4 + delivery-package slots."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p13.run(
        episode_id="ep-013",
        asset_bus_read=_read_returns_value,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "master-mp4" in written, "master-mp4 slot must be written"
    assert "delivery-package" in written, "delivery-package slot must be written"
    assert written["master-mp4"]["path"].endswith("master.mp4")
    assert "compliance_report" in written["delivery-package"]


def test_p13_gate_id_is_final_delivery():
    """Test 5: p13 module GATE_ID constant is 'final-delivery' (Gate 8)."""
    assert p13.GATE_ID == "final-delivery", (
        f"p13 GATE_ID must be 'final-delivery' per V8.6 gates.yaml; "
        f"got {p13.GATE_ID!r}"
    )


def test_p13_triggers_gate_8_when_trigger_gate_provided():
    """Test 6: run() triggers Gate 8 'final-delivery' when trigger_gate is set."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "approved", "operator": "kai"}

    result = p13.run(
        episode_id="ep-013",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [("final-delivery", "ep-013")], (
        f"p13 must call trigger_gate('final-delivery', ep-013); got {gate_calls}"
    )
    assert result["gate"] == {"status": "approved", "operator": "kai"}


def test_p13_skips_gate_when_trigger_gate_is_none():
    """Test 7: run() does NOT trigger gate when trigger_gate is None."""
    result = p13.run(
        episode_id="ep-013",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None
    assert result["phase"] == "p13_delivery"


def test_p13_handles_empty_input_slots_gracefully():
    """Test 8: run() does not crash when input slots are empty/missing."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    result = p13.run(
        episode_id="ep-013",
        asset_bus_read=lambda slot: None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "master-mp4" in written
    assert "delivery-package" in written
    assert result["gate"] is None
