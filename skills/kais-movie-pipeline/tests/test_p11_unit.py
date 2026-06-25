"""test_p11_unit.py — Phase 36-03 unit tests for p11_video_render.

Mocked tests (per CONTEXT D-35-08 all tests inject mocks via the run()
signature — no real subagents, no real network, no real LLM). Tests
verify ORCHESTRATION CORRECTNESS only, plus D-36-08 parallel_shots-specific
behavior:

  - reads correct input slots (shot-list + scene-images + character-assets
    + voice-timeline)
  - goal per shot mentions skill_view for both experts (visual_executor
    animator + audio_pipeline lip_sync)
  - calls delegate_task exactly once PER SHOT
  - parallel_shots=4 + 4-shot fixture → 4 delegate calls
  - parallel_shots=1 → deterministic sequential ordering
  - aggregates all shot results into single video-clips + lip-sync-reports
  - writes correct output slots
  - triggers Gate 7 render-preview when configured; skips when None
  - handles empty shot-list gracefully

Determinism note: ThreadPoolExecutor with parallel_shots=1 dispatches
shots sequentially in shot-list order, so the recorded call order is
deterministic. For parallel_shots>1 tests we assert call COUNT, not order.
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

from pipeline.phases import p11_video_render as p11  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _shot_summary(shot_idx: int) -> str:
    """Return a delegate_task summary with a per-shot fenced JSON block."""
    payload = {
        "video_clip": {
            "shot_index": shot_idx,
            "path": f"/v/clip_{shot_idx}.mp4",
            "duration_ms": 3000,
        },
        "lip_sync_report": {
            "shot_index": shot_idx,
            "score": 0.92,
        },
    }
    return (
        f"Shot {shot_idx} render...\n```json\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n```\nDone."
    )


def _make_per_shot_delegate(captured: dict):
    """Return a mock delegate_task that records args per call + returns per-shot summary.

    captured keys: goals (list), contexts (list), toolsets (list), calls (int).
    The shot_index is extracted from the goal text (the goal embeds "render
    shot N of episode").
    """

    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured.setdefault("goals", []).append(goal)
        captured.setdefault("contexts", []).append(context)
        captured.setdefault("toolsets", []).append(toolsets)
        captured["calls"] = captured.get("calls", 0) + 1
        # Extract shot index from the goal's "render shot N of episode" prefix.
        # Falls back to the calls count if parsing fails (defensive).
        shot_idx = captured["calls"] - 1
        try:
            # Goal text format: "render shot <idx> of episode"
            marker = "render shot "
            after = goal.split(marker, 1)[1]
            shot_idx = int(after.split(" ", 1)[0])
        except (IndexError, ValueError):
            pass
        return {"summary": _shot_summary(shot_idx)}

    return _mock


def _asset_bus_factory(slots: dict):
    """Return (read_fn, write_fn, written_dict) backed by an in-memory dict."""
    written: dict = {}

    def _read(slot: str):
        return slots.get(slot)

    def _write(slot: str, entry) -> None:
        written[slot] = entry

    return _read, _write, written


def _four_shot_list():
    return [
        {"shot_id": f"s{i}", "duration_sec": 3.0}
        for i in range(4)
    ]


def _full_slots():
    return {
        "shot-list": _four_shot_list(),
        "scene-images": {"scenes": [{"id": "c1"}]},
        "character-assets": {"characters": [{"id": "alex"}]},
        "voice-timeline": {"shots": [{"shot_id": "s0", "start_ms": 0}]},
    }


# ---------------------------------------------------------------------------
# Tests — basic orchestration
# ---------------------------------------------------------------------------


def test_p11_reads_all_four_input_slots():
    """Test 1: run() reads shot-list + scene-images + character-assets + voice-timeline."""
    captured: dict = {}
    delegate = _make_per_shot_delegate(captured)
    slots = _full_slots()
    read, _, _ = _asset_bus_factory(slots)

    p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
        parallel_shots=1,
    )

    combined_all = "".join(captured["goals"]) + "".join(captured["contexts"])
    # All 4 input payloads should reach the expert across shots.
    assert "shot_id" in combined_all, "shot-list content must reach expert"
    assert "scenes" in combined_all, "scene-images content must reach expert"
    assert "characters" in combined_all, "character-assets content must reach expert"
    assert "start_ms" in combined_all, "voice-timeline content must reach expert"


def test_p11_goal_mentions_both_experts_per_shot():
    """Test 2: each per-shot goal mentions skill_view for visual_executor + audio_pipeline."""
    captured: dict = {}
    delegate = _make_per_shot_delegate(captured)
    read, _, _ = _asset_bus_factory(_full_slots())

    p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
        parallel_shots=1,
    )

    assert len(captured["goals"]) == 4, "one goal per shot expected"
    for idx, goal in enumerate(captured["goals"]):
        assert "skill_view(name='visual_executor')" in goal, (
            f"shot {idx} goal missing visual_executor skill_view: {goal!r}"
        )
        assert "skill_view(name='audio_pipeline')" in goal, (
            f"shot {idx} goal missing audio_pipeline skill_view: {goal!r}"
        )
        # Sub-step references should be present.
        assert "animator" in goal.lower(), f"shot {idx} goal missing animator sub-step"
        assert "lip_sync" in goal.lower(), f"shot {idx} goal missing lip_sync sub-step"


# ---------------------------------------------------------------------------
# Tests — D-36-08 parallel_shots-specific behavior
# ---------------------------------------------------------------------------


def test_p11_parallel_shots_fans_out_one_delegate_per_shot():
    """Test 3: parallel_shots=4 with 4-shot fixture → exactly 4 delegate_task calls."""
    captured: dict = {}
    delegate = _make_per_shot_delegate(captured)
    read, _, _ = _asset_bus_factory(_full_slots())

    p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
        parallel_shots=4,
    )

    assert captured["calls"] == 4, (
        f"expected 4 delegate calls (one per shot); got {captured.get('calls')}"
    )


def test_p11_parallel_shots_sequential_when_set_to_1():
    """Test 4: parallel_shots=1 → deterministic shot-order dispatch (s0, s1, s2, s3)."""
    captured: dict = {}
    delegate = _make_per_shot_delegate(captured)
    read, _, _ = _asset_bus_factory(_full_slots())

    p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=delegate,
        trigger_gate=None,
        parallel_shots=1,
    )

    # Each goal embeds the shot payload; verify shot_ids land in list order.
    shot_ids_in_order = []
    for goal in captured["goals"]:
        # shot payload appears as JSON in the goal: "shot_id": "sN"
        match = goal.split('"shot_id": "', 1)[1].split('"', 1)[0]
        shot_ids_in_order.append(match)
    assert shot_ids_in_order == ["s0", "s1", "s2", "s3"], (
        f"parallel_shots=1 must preserve shot-list order; got {shot_ids_in_order}"
    )


def test_p11_aggregates_all_shot_results_into_single_write():
    """Test 5: aggregated video-clips + lip-sync-reports contain all shots, written once each."""
    read, write_fn, written = _asset_bus_factory(_full_slots())

    p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=write_fn,
        delegate_task=_make_per_shot_delegate({}),
        trigger_gate=None,
        parallel_shots=1,
    )

    assert "video-clips" in written, "video-clips slot must be written"
    assert "lip-sync-reports" in written, "lip-sync-reports slot must be written"
    # Aggregated arrays — one entry per shot.
    assert len(written["video-clips"]) == 4, (
        f"video-clips must aggregate all 4 shots; got {len(written['video-clips'])}"
    )
    assert len(written["lip-sync-reports"]) == 4, (
        f"lip-sync-reports must aggregate all 4 shots; got {len(written['lip-sync-reports'])}"
    )
    # Each clip path embeds shot_index — verify all 4 are present.
    paths = sorted(clip["path"] for clip in written["video-clips"])
    assert paths == ["/v/clip_0.mp4", "/v/clip_1.mp4", "/v/clip_2.mp4", "/v/clip_3.mp4"], (
        f"aggregated video clips missing shots; got {paths}"
    )


def test_p11_default_parallel_shots_is_4():
    """Test 6: parallel_shots kwarg defaults to 4 when omitted (D-36-08)."""
    import inspect
    sig = inspect.signature(p11.run)
    param = sig.parameters["parallel_shots"]
    assert param.default == 4, (
        f"parallel_shots default must be 4 (D-36-08); got {param.default}"
    )
    # Must be keyword-only (after *) to distinguish from the 5-arg base signature.
    # Inspect the kind — KEYWORD_ONLY means it follows a '*' marker.
    assert param.kind == inspect.Parameter.KEYWORD_ONLY, (
        f"parallel_shots must be keyword-only; got kind={param.kind}"
    )


# ---------------------------------------------------------------------------
# Tests — gate + output slot lifecycle
# ---------------------------------------------------------------------------


def test_p11_triggers_gate_render_preview_when_configured():
    """Test 7: run() calls trigger_gate('render-preview', episode_id) when provided."""
    gate_calls: list = []

    def gate_spy(gate_id, episode_id):
        gate_calls.append((gate_id, episode_id))
        return {"status": "paused", "gate_id": gate_id}

    read, _, _ = _asset_bus_factory(_full_slots())
    result = p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_per_shot_delegate({}),
        trigger_gate=gate_spy,
        parallel_shots=1,
    )

    assert gate_calls == [("render-preview", "ep-001")], (
        f"trigger_gate must fire once with (render-preview, ep-001); got {gate_calls}"
    )
    assert result["gate"] == {"status": "paused", "gate_id": "render-preview"}


def test_p11_gate_none_when_trigger_gate_is_none():
    """Test 8: run() sets gate=None when trigger_gate is None."""
    read, _, _ = _asset_bus_factory(_full_slots())
    result = p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=lambda slot, entry: None,
        delegate_task=_make_per_shot_delegate({}),
        trigger_gate=None,
        parallel_shots=1,
    )
    assert result["gate"] is None
    assert result["phase"] == "p11_video_render"


def test_p11_handles_empty_shot_list_gracefully():
    """Test 9: run() with empty shot-list writes empty aggregates, fires gate (if configured)."""
    captured: dict = {}
    delegate = _make_per_shot_delegate(captured)
    # Empty shot-list, other slots present.
    slots = _full_slots()
    slots["shot-list"] = []
    read, write_fn, written = _asset_bus_factory(slots)

    result = p11.run(
        episode_id="ep-001",
        asset_bus_read=read,
        asset_bus_write=write_fn,
        delegate_task=delegate,
        trigger_gate=None,
        parallel_shots=4,
    )

    # No delegate calls fired (no shots to render).
    assert captured.get("calls", 0) == 0
    # Empty arrays written.
    assert written["video-clips"] == []
    assert written["lip-sync-reports"] == []
    assert result["outputs"]["video_clips"] == []


def test_p11_module_constants_match_contract():
    """Test 10: module constants match the V8.6 contract for p11."""
    assert p11.PHASE_ID == "p11_video_render"
    assert p11.EXPERT == "visual_executor"
    assert p11.INPUT_SLOTS == [
        "shot-list", "scene-images", "character-assets", "voice-timeline",
    ]
    assert p11.OUTPUT_SLOTS == ["video-clips", "lip-sync-reports"]
    assert p11.GATE_ID == "render-preview"
