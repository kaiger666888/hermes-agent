"""test_p10_unit.py — Phase 36-03 unit tests for p10_voice.

Mocked tests (per CONTEXT D-35-08 all tests inject mocks via the run()
signature — no real subagents, no real network, no real LLM). Tests
verify ORCHESTRATION CORRECTNESS only:

  - reads correct input slots (shot-list + script-draft)
  - goal mentions skill_view(name='audio_pipeline') + voicer sub-step
  - calls delegate_task once with ["skills", "file"] toolsets
  - writes voice-clips + voice-timeline slots from parsed expert output
  - gate is None (GATE_ID is None — CF-36-04 conditional skip)
  - parses expert JSON output correctly
  - handles empty input slot gracefully
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_p01_unit).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p10_voice as p10  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _ok_summary() -> str:
    """Return a delegate_task summary containing a valid fenced JSON block."""
    payload = {
        "voice_clips": [
            {"shot_id": "s1", "narration_path": "/v/narr1.wav"},
            {"shot_id": "s2", "dialogue_path": "/v/dial2.wav"},
        ],
        "voice_timeline": {
            "shots": [
                {"shot_id": "s1", "start_ms": 0, "end_ms": 3000},
                {"shot_id": "s2", "start_ms": 3000, "end_ms": 6500},
            ],
        },
    }
    return f"Voicer reasoning...\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _make_delegate_spy(captured: dict):
    """Return a mock delegate_task that records its args + returns ok summary."""

    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        captured["calls"] = captured.get("calls", 0) + 1
        return {"summary": _ok_summary()}

    return _mock


def _asset_bus_factory(slots: dict):
    """Return (read_fn, write_fn, written_dict) backed by an in-memory dict."""
    written: dict = {}

    def _read(slot: str):
        return slots.get(slot)

    def _write(slot: str, entry) -> None:
        written[slot] = entry

    return _read, _write, written


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_p10_reads_shot_list_and_script_draft_slots():
    """Test 1: run() reads shot-list + script-draft slots and embeds in goal/context."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)
    shot_list = [{"shot_id": "s1", "duration_sec": 3.0}]
    script_draft = {"beats": [{"id": "b1", "narration": "x"}]}
    read, _, _ = _asset_bus_factory({
        "shot-list": shot_list,
        "script-draft": script_draft,
    })

    p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )

    combined = captured["goal"] + captured["context"]
    assert "shot_id" in combined, "shot-list content must reach the expert"
    assert "beats" in combined, "script-draft content must reach the expert"


def test_p10_goal_invokes_audio_pipeline_expert():
    """Test 2: run() calls delegate_task with goal mentioning skill_view(name='audio_pipeline')."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)
    read, _, _ = _asset_bus_factory({"shot-list": [{}], "script-draft": {}})

    p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )

    assert "skill_view(name='audio_pipeline')" in captured["goal"], (
        f"goal must mention skill_view(name='audio_pipeline'); got: {captured['goal']!r}"
    )
    # voicer sub-step should be referenced in the goal.
    assert "voicer" in captured["goal"].lower(), (
        f"goal must reference the voicer sub-step; got: {captured['goal']!r}"
    )


def test_p10_calls_delegate_once_with_skills_file_toolsets():
    """Test 3: run() calls delegate_task exactly once with ['skills','file']."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)
    read, _, _ = _asset_bus_factory({"shot-list": [{}], "script-draft": {}})

    p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )

    assert captured.get("calls") == 1, "p10 must call delegate_task exactly once"
    assert captured["toolsets"] == ["skills", "file"], (
        f"toolsets must be ['skills','file']; got {captured['toolsets']!r}"
    )


def test_p10_writes_voice_clips_and_voice_timeline_slots():
    """Test 4: run() writes voice-clips + voice-timeline from parsed expert output."""
    read, write_fn, written = _asset_bus_factory({"shot-list": [{}], "script-draft": {}})

    p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=write_fn,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )

    assert "voice-clips" in written, "voice-clips slot must be written"
    assert "voice-timeline" in written, "voice-timeline slot must be written"
    assert len(written["voice-clips"]) == 2
    assert written["voice-clips"][0]["shot_id"] == "s1"
    assert written["voice-timeline"]["shots"][1]["end_ms"] == 6500


def test_p10_gate_none_when_trigger_gate_is_none():
    """Test 5: run() sets gate=None when trigger_gate is None (GATE_ID is None)."""
    read, _, _ = _asset_bus_factory({"shot-list": [{}], "script-draft": {}})
    result = p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert result["gate"] is None
    assert result["phase"] == "p10_voice"


def test_p10_gate_none_even_when_trigger_gate_provided():
    """Test 6: GATE_ID is None so no gate fires even if trigger_gate is provided."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused"}

    read, _, _ = _asset_bus_factory({"shot-list": [{}], "script-draft": {}})
    result = p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=gate_spy,
    )
    assert gate_calls == [], "p10 GATE_ID is None — trigger_gate must not fire"
    assert result["gate"] is None


def test_p10_parses_expert_json_output_correctly():
    """Test 7: run() parses expert output and returns it under 'outputs'."""
    read, _, _ = _asset_bus_factory({"shot-list": [{}], "script-draft": {}})
    result = p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_delegate_spy({}),
        trigger_gate=None,
    )
    assert "voice_clips" in result["outputs"]
    assert "voice_timeline" in result["outputs"]
    assert result["outputs"]["voice_clips"][0]["shot_id"] == "s1"


def test_p10_handles_empty_input_slot_gracefully():
    """Test 8: run() handles empty/missing slots without crashing."""
    captured: dict = {}
    delegate = _make_delegate_spy(captured)
    # Both slots missing — read returns None for all.
    read, _, _ = _asset_bus_factory({})

    result = p10.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
    )
    # Delegate still called once with empty-converted-to-defaults payload.
    assert captured.get("calls") == 1
    assert result["phase"] == "p10_voice"
    assert result["gate"] is None


def test_p10_module_constants_match_contract():
    """Test 9: module constants match the V8.6 contract for p10."""
    assert p10.PHASE_ID == "p10_voice"
    assert p10.EXPERT == "audio_pipeline"
    assert p10.INPUT_SLOTS == ["shot-list", "script-draft"]
    assert p10.OUTPUT_SLOTS == ["voice-clips", "voice-timeline"]
    assert p10.GATE_ID is None
