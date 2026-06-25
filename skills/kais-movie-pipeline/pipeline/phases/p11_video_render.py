"""p11_video_render.py — Phase 11: video render with parallel shot fan-out.

Reference port of the Node.js Step 10 video half + Step 11 video render.
Per CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM calls, no
prompt templates, no business logic. All render work is delegated to the
``visual_executor`` (animator sub-step) and ``audio_pipeline`` (lip_sync
sub-step) movie-expert skills via ``delegate_task``.

This is the ONLY phase that uses ``parallel_shots`` (D-36-08). The run()
signature extends the standard 5-arg Phase 35 contract with an extra
keyword-only ``parallel_shots: int = 4`` parameter. The phase fans out
shot-level ``delegate_task`` calls concurrently via
``concurrent.futures.ThreadPoolExecutor(max_workers=parallel_shots)``,
then aggregates results into single consolidated asset-bus writes.

Behavioral contract (mirrors ``lib/phases/index.js`` video-render handler
but ports the parallel shot dispatch natively in Python per D-36-08).
Per-shot work (CF-36-03, Pattern 3): visual_executor animator + audio_pipeline
lip_sync collaborate in a SINGLE delegate_task call per shot — the subagent
orchestrates the 2-expert collaboration internally for that shot.

Inputs (asset bus READ):
  - ``shot-list`` — output of p09 (one entry per shot)
  - ``scene-images`` — output of p07 (5-view per scene)
  - ``character-assets`` — output of p04 (L1-L4 character asset manifest)
  - ``voice-timeline`` — output of p10 (per-shot start/end + lip-sync cues)

Outputs (asset bus WRITE):
  - ``video-clips`` — aggregated rendered video clips (one entry per shot)
  - ``lip-sync-reports`` — aggregated lip-sync alignment reports per shot

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 7 ``render-preview`` — operator confirms video clips meet quality
    bar (per references/review-gates.md).
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phase metadata — referenced by runner.py + tests
# ---------------------------------------------------------------------------

PHASE_ID = "p11_video_render"
EXPERT = "visual_executor"  # primary; audio_pipeline lip_sync collaborates
INPUT_SLOTS = ["shot-list", "scene-images", "character-assets", "voice-timeline"]
OUTPUT_SLOTS = ["video-clips", "lip-sync-reports"]
GATE_ID = "render-preview"  # Gate 7 per V8.6


# ---------------------------------------------------------------------------
# run() — the orchestration entry point (D-36-08 parallel_shots extension)
# ---------------------------------------------------------------------------


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
    *,
    parallel_shots: int = 4,  # D-36-08 — p11 ONLY
) -> dict:
    """Execute phase p11 (V8.6 Step 10 + Step 11 video render, parallel shots).

    Args:
        episode_id: Episode identifier.
        asset_bus_read: Callable(slot) -> data (injected; tests pass mock).
        asset_bus_write: Callable(slot, entry) -> None (injected).
        delegate_task: Callable(goal, context, toolsets) -> dict with a
            "summary" key whose value is text containing a fenced JSON block
            (D-35-07 contract). Called once PER SHOT in this phase.
        trigger_gate: Optional Callable(gate_id, episode_id) -> dict. When
            provided, Gate 7 "render-preview" is triggered after the asset-bus
            writes; when ``None`` no gate is triggered.
        parallel_shots: Shot-level parallelism (D-36-08). Defaults to 4. p11
            is the ONLY phase that accepts this kwarg — fans out per-shot
            delegate_task calls via ThreadPoolExecutor(max_workers=...).
            Tests pass ``parallel_shots=1`` for sequential determinism.

    Returns:
        ``{"phase": "p11_video_render", "outputs": {...}, "gate": {...} | None}``
        where ``outputs`` carries the aggregated expert payload
        (video_clips + lip_sync_reports arrays across all shots).
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    shot_list = asset_bus_read("shot-list") or []
    scene_images = asset_bus_read("scene-images") or {}
    character_assets = asset_bus_read("character-assets") or {}
    voice_timeline = asset_bus_read("voice-timeline") or {}

    # Serialize the shared (non-shot-specific) payload once. Each per-shot
    # goal embeds these so the subagent has full context for that shot.
    si_json = json.dumps(scene_images, ensure_ascii=False)
    ca_json = json.dumps(character_assets, ensure_ascii=False)
    vt_json = json.dumps(voice_timeline, ensure_ascii=False)

    def _goal_for_shot(shot: dict, shot_idx: int) -> tuple[str, str]:
        """Build (goal, context) for one shot's delegate_task call."""
        shot_json = json.dumps(shot, ensure_ascii=False)
        goal = (
            f"Apply the visual_executor (animator) AND audio_pipeline "
            f"(lip_sync) expert skills to render shot {shot_idx} of episode "
            f"{episode_id}. First call skill_view(name='visual_executor') "
            f"and skill_view(name='audio_pipeline') to load both experts, "
            f"then have them collaborate on this single shot: visual_executor "
            f"animator renders the video clip from scene-images + "
            f"character-assets + E-Konte sheets (per visual_executor SKILL.md "
            f"§animator Workflow); audio_pipeline lip_sync aligns the "
            f"character mouth shapes to the voice-timeline cues (per "
            f"audio_pipeline SKILL.md §lip_sync Workflow). "
            f"Shot {shot_idx} payload: {shot_json}. "
            f"Scene images from p07: {si_json}. "
            f"Character assets from p04: {ca_json}. "
            f"Voice timeline from p10: {vt_json}. "
            f"Emit the final output as a single fenced JSON block at end of "
            f'your summary, shaped as {{"video_clip": {{...}}, '
            f'"lip_sync_report": {{...}}}}.'
        )
        context = json.dumps(
            {
                "episode_id": episode_id,
                "shot_index": shot_idx,
                "shot": shot,
                "scene_images": scene_images,
                "character_assets": character_assets,
                "voice_timeline": voice_timeline,
            },
            ensure_ascii=False,
        )
        return goal, context

    # 2. Fan out shot-level delegate_task calls concurrently (D-36-08).
    #    ThreadPoolExecutor is appropriate because delegate_task is a blocking
    #    sync callable (D-35-02) — threads release the GIL during the
    #    underlying delegate dispatch, giving real concurrency in production.
    #    Tests typically pass parallel_shots=1 for sequential determinism OR
    #    monkeypatch ThreadPoolExecutor with a FakePool.
    def _dispatch_shot(shot_idx: int, shot: dict) -> dict:
        goal, ctx = _goal_for_shot(shot, shot_idx)
        return delegate_task(goal, ctx, ["skills", "file"])

    video_clips: list[dict] = []
    lip_sync_reports: list[dict] = []
    if shot_list:
        with ThreadPoolExecutor(max_workers=parallel_shots) as pool:
            futures = [
                pool.submit(_dispatch_shot, idx, shot)
                for idx, shot in enumerate(shot_list)
            ]
            for idx, future in enumerate(futures):
                delegate_result = future.result()
                expert_output = _parse_expert_output(delegate_result)
                # Annotate with shot_index so aggregated writes preserve order.
                video_clip = expert_output.get("video_clip", {})
                lip_sync_report = expert_output.get("lip_sync_report", {})
                video_clip.setdefault("shot_index", idx)
                lip_sync_report.setdefault("shot_index", idx)
                video_clips.append(video_clip)
                lip_sync_reports.append(lip_sync_report)

    aggregated = {
        "video_clips": video_clips,
        "lip_sync_reports": lip_sync_reports,
    }

    # 3. Write aggregated outputs as SINGLE writes per slot (per the plan's
    #    asset_bus_slots_to_add — "aggregated single write", not per-shot
    #    appends). Downstream p12_composition reads the consolidated arrays.
    asset_bus_write("video-clips", video_clips)
    asset_bus_write("lip-sync-reports", lip_sync_reports)

    # 4. Trigger gate if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p11: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": aggregated,
        "gate": gate_result,
    }
