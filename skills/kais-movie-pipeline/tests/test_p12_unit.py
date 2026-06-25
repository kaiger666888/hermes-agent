"""test_p12_unit.py — Phase 36-04 unit tests for p12_composition.

Mocked tests for ``pipeline/phases/p12_composition.py``. Per CONTEXT
D-35-08 all tests inject mocks via the run() signature — no real subagents,
no real network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only:

  - reads the correct input slots (video-clips + voice-clips +
    lip-sync-reports + style-vector)
  - goal mentions both assigned experts (audio_pipeline + editor) via
    skill_view
  - calls delegate_task exactly ONCE despite audio_pipeline encapsulating
    6 atomic sub-steps (CF-36-03 invariant — sub-steps are internal to the
    audio_pipeline expert, NOT separate delegate calls)
  - calls delegate_task with ["skills", "file"] toolsets
  - writes the correct output slots (master-timeline + audio-stems)
  - GATE_ID is None (no gate for p12)
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

from pipeline.phases import p12_composition as p12  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "master_timeline": {
            "edition": "v1",
            "cuts": [
                {"frame": 0, "rate": 24, "time": 0.0, "clip_id": "clip-1"},
                {"frame": 72, "rate": 24, "time": 3.0, "clip_id": "clip-2"},
            ],
        },
        "audio_stems": {
            "bgm": {"path": "bgm.wav", "duration": 6.0},
            "sfx": {"path": "sfx.wav", "duration": 6.0},
            "voice": {"path": "voice.wav", "duration": 5.8},
            "mix": {"path": "mix.wav", "duration": 6.0},
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


_P12_INPUTS = ("video-clips", "voice-clips", "lip-sync-reports", "style-vector")


def _read_returns_value(slot):
    if slot == "video-clips":
        return [{"clip_id": "clip-1"}]
    if slot == "voice-clips":
        return [{"clip_id": "voc-1"}]
    if slot == "lip-sync-reports":
        return [{"shot_id": "shot-1", "offset": 0.0}]
    if slot == "style-vector":
        return {"mood": "tense"}
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p12_reads_correct_input_slots():
    """Test 1: run() reads video-clips + voice-clips + lip-sync-reports + style-vector."""
    read_slots: list = []

    def read_spy(slot):
        read_slots.append(slot)
        return _read_returns_value(slot)

    p12.run(
        episode_id="ep-012",
        asset_bus_read=read_spy,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    for expected in _P12_INPUTS:
        assert expected in read_slots, (
            f"p12 must read {expected} slot; got {read_slots}"
        )


def test_p12_goal_mentions_both_assigned_experts_via_skill_view():
    """Test 2: run() goal mentions audio_pipeline + editor via skill_view."""
    captured: dict = {}
    p12.run(
        episode_id="ep-012",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy(captured),
        trigger_gate=None,
    )
    goal = captured["goal"]
    assert "skill_view(name='audio_pipeline')" in goal, (
        f"goal must mention skill_view(name='audio_pipeline'); got: {goal!r}"
    )
    assert "skill_view(name='editor')" in goal, (
        f"goal must mention skill_view(name='editor'); got: {goal!r}"
    )


def test_p12_calls_delegate_task_once_despite_6_sub_steps():
    """Test 3: run() calls delegate_task exactly ONCE.

    CF-36-03 invariant: audio_pipeline's 6 atomic sub-steps (composer BGM +
    foley SFX + mixer balance + spatial_audio + lip_sync final alignment +
    dialog cleanup) are INTERNAL to the audio_pipeline expert — the phase
    module must NOT split them into separate delegate calls (that would
    re-introduce V8.4-era 25-step complexity).
    """
    captured: dict = {}
    call_count = {"n": 0}

    def _mock(goal, context, toolsets):
        captured["goal"] = goal
        captured["toolsets"] = toolsets
        call_count["n"] += 1
        return {"summary": _ok_summary()}

    p12.run(
        episode_id="ep-012",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_mock,
        trigger_gate=None,
    )
    assert call_count["n"] == 1, (
        f"p12 must call delegate_task exactly once (CF-36-03 atomic §6); "
        f"got {call_count['n']}"
    )
    assert captured["toolsets"] == ["skills", "file"]


def test_p12_writes_correct_output_slots():
    """Test 4: run() writes master-timeline + audio-stems slots."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    p12.run(
        episode_id="ep-012",
        asset_bus_read=_read_returns_value,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "master-timeline" in written, "master-timeline slot must be written"
    assert "audio-stems" in written, "audio-stems slot must be written"
    assert written["master-timeline"]["cuts"][0]["clip_id"] == "clip-1"
    assert "bgm" in written["audio-stems"]
    assert "mix" in written["audio-stems"]


def test_p12_gate_id_is_none():
    """Test 5: p12 module GATE_ID constant is None (no gate for p12)."""
    assert p12.GATE_ID is None, (
        f"p12 GATE_ID must be None per CONTEXT D-36-02 table; got {p12.GATE_ID!r}"
    )


def test_p12_gate_result_always_none_even_when_trigger_gate_provided():
    """Test 6: gate result is None regardless of trigger_gate arg (GATE_ID=None)."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "should-not-happen"}

    result = p12.run(
        episode_id="ep-012",
        asset_bus_read=_read_returns_value,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [], (
        f"p12 must NOT call trigger_gate (GATE_ID=None); got {gate_calls}"
    )
    assert result["gate"] is None
    assert result["phase"] == "p12_composition"


def test_p12_handles_empty_input_slots_gracefully():
    """Test 7: run() does not crash when input slots are empty/missing."""
    written: dict = {}

    def write_spy(slot, entry):
        written[slot] = entry

    result = p12.run(
        episode_id="ep-012",
        asset_bus_read=lambda slot: None,
        asset_bus_write=write_spy,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "master-timeline" in written
    assert "audio-stems" in written
    assert result["gate"] is None
