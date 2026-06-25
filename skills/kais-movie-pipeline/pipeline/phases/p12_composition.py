"""p12_composition.py — Phase 12: composition (V8.6 §11 audio half + §12 edit).

Reference port of Node.js step11 (audio half) + step12 (timeline edit). Per
CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM calls, no prompt
templates, no business logic.

Per CF-36-03 (Pattern 3 — Atomic §6), p12 is a SINGLE delegate_task call
despite the audio_pipeline expert encapsulating 6 atomic sub-steps
internally (composer BGM + foley SFX + mixer balance + spatial_audio +
lip_sync final alignment + dialog cleanup). The audio_pipeline SKILL.md
already documents these 6 sub-steps as its internal Workflow; the phase
module does NOT split them into separate delegate calls (that would
re-introduce V8.4-era 25-step complexity). The editor expert collaborates
in the same delegate call to assemble the FxRxT master timeline.

Inputs (asset bus READ):
  - ``video-clips``        — rendered video clips from p11
  - ``voice-clips``        — voiced dialog clips from p10
  - ``lip-sync-reports``   — lip-sync alignment reports from p11
  - ``style-vector``       — 5D style genome from p07 (drives audio mood)

Outputs (asset bus WRITE):
  - ``master-timeline``    — FxRxT master timeline (edit decision list)
  - ``audio-stems``        — audio stems {bgm, sfx, voice, mix}

Gate triggered: None — p12 has no review gate (per CONTEXT D-36-02 table).
The final Gate 8 ``final-delivery`` fires in p13.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p12_composition"
EXPERT = "audio_pipeline"  # primary; editor collaborates (single delegate call)
INPUT_SLOTS = ["video-clips", "voice-clips", "lip-sync-reports", "style-vector"]
OUTPUT_SLOTS = ["master-timeline", "audio-stems"]
GATE_ID = None  # no review gate for p12 (per CONTEXT D-36-02 table)


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p12 (V8.6 §11 audio half + §12 timeline composition).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p12_composition", "outputs": {...}, "gate": None}``.

    The single delegate_task call instructs the subagent to load BOTH the
    audio_pipeline and editor expert skills, then have them collaborate:
    audio_pipeline runs its 6 internal sub-steps atomically (BGM compose +
    foley SFX + mixer balance + spatial_audio + lip_sync final alignment +
    dialog cleanup), while editor assembles the FxRxT master timeline.
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    video_clips = asset_bus_read("video-clips") or []
    voice_clips = asset_bus_read("voice-clips") or []
    lip_sync_reports = asset_bus_read("lip-sync-reports") or []
    style_vector = asset_bus_read("style-vector") or {}

    # 2. Construct the V8.6 §11+§12 goal: audio_pipeline + editor collaborate
    #    in a SINGLE delegate_task call (CF-36-03 atomic §6). The
    #    audio_pipeline SKILL.md encapsulates the 6 sub-steps as its internal
    #    Workflow; the phase module must NOT split them across delegate calls.
    vc_json = json.dumps(video_clips, ensure_ascii=False)
    voc_json = json.dumps(voice_clips, ensure_ascii=False)
    lsr_json = json.dumps(lip_sync_reports, ensure_ascii=False)
    sv_json = json.dumps(style_vector, ensure_ascii=False)
    goal = (
        f"Apply the audio_pipeline AND editor expert skills in a V8.6 §11+§12 "
        f"composition operation for episode {episode_id}. "
        f"First call skill_view(name='audio_pipeline') and "
        f"skill_view(name='editor') to load both experts, then have them "
        f"collaborate. audio_pipeline runs the 6 atomic sub-steps from its "
        f"SKILL.md §Workflow internally (composer BGM + foley SFX + mixer "
        f"balance + spatial_audio + lip_sync final alignment + dialog cleanup) "
        f"as a single coordinated pass — do NOT split these into separate "
        f"calls; the audio_pipeline expert orchestrates them itself. editor "
        f"assembles the FxRxT master timeline (edit decision list: frame, "
        f"rate, time per cut) from the video clips and aligned audio stems "
        f"per editor SKILL.md §Workflow. "
        f"Video clips from p11: {vc_json}. "
        f"Voice clips from p10: {voc_json}. "
        f"Lip-sync reports from p11: {lsr_json}. "
        f"Style vector from p07 (drives audio mood): {sv_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"master_timeline": {{...}}, '
        f'"audio_stems": {{"bgm": {{...}}, "sfx": {{...}}, '
        f'"voice": {{...}}, "mix": {{...}}}}}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "video_clips": video_clips,
            "voice_clips": voice_clips,
            "lip_sync_reports": lip_sync_reports,
            "style_vector": style_vector,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous — D-35-02 confirms blocking). SINGLE call.
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: master-timeline + audio-stems are separate slots so
    #    p13_delivery can read each independently.
    master_timeline = expert_output.get("master_timeline", {})
    audio_stems = expert_output.get("audio_stems", {})
    asset_bus_write("master-timeline", master_timeline)
    asset_bus_write("audio-stems", audio_stems)

    # 5. No gate for p12 (GATE_ID is None — CF-36-04 conditional skip).
    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": None,
    }
