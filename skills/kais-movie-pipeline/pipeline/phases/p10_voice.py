"""p10_voice.py — Phase 10: voice generation (V8.6 Step 7B + Step 10 TTS portion).

Reference port of the Node.js Step 7B audio skeleton + Step 10 TTS voice
generation. Per CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM
calls, no prompt templates, no business logic. All voice work is delegated
to the ``audio_pipeline`` movie-expert skill (voicer sub-step) via
``delegate_task``.

Behavioral contract (mirrors ``lib/phases/index.js`` voice-generation
handler): a SINGLE ``delegate_task`` call per phase. The audio_pipeline
expert skill encapsulates the voicer Workflow (TTS for narration + dialogue
per shot, voice timeline alignment with lip-sync cues).

Inputs (asset bus READ):
  - ``shot-list`` — output of p09 (one entry per shot with intent + duration)
  - ``script-draft`` — output of p03 (narration + dialogue text per beat)

Outputs (asset bus WRITE):
  - ``voice-clips`` — TTS voice clips per shot (narration + dialogue)
  - ``voice-timeline`` — voice timeline alignment (per-shot start/end + cues)

Gate triggered: None — p10 has no review gate (per CONTEXT D-36-02 table).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phase metadata — referenced by runner.py + tests
# ---------------------------------------------------------------------------

PHASE_ID = "p10_voice"
EXPERT = "audio_pipeline"  # voicer sub-step
INPUT_SLOTS = ["shot-list", "script-draft"]
OUTPUT_SLOTS = ["voice-clips", "voice-timeline"]
GATE_ID = None  # no review gate for p10 (per CONTEXT D-36-02 table)


# ---------------------------------------------------------------------------
# run() — the orchestration entry point
# ---------------------------------------------------------------------------


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p10 (V8.6 Step 7B + Step 10 TTS voice generation).

    Args:
        episode_id: Episode identifier.
        asset_bus_read: Callable(slot) -> data (injected; tests pass mock).
        asset_bus_write: Callable(slot, entry) -> None (injected).
        delegate_task: Callable(goal, context, toolsets) -> dict with a
            "summary" key whose value is text containing a fenced JSON block
            (D-35-07 contract).
        trigger_gate: Optional Callable(gate_id, episode_id) -> dict. Ignored
            for p10 — GATE_ID is None (CF-36-04 conditional skip).

    Returns:
        ``{"phase": "p10_voice", "outputs": {...}, "gate": None}`` where
        ``outputs`` carries the parsed expert payload (voice_clips +
        voice_timeline).
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    shot_list = asset_bus_read("shot-list") or []
    script_draft = asset_bus_read("script-draft") or {}

    # 2. Construct a self-contained goal for the audio_pipeline (voicer)
    #    expert. The subagent loads the expert via skill_view first, then
    #    applies its voicer Workflow (TTS for narration + dialogue per shot,
    #    voice timeline alignment with lip-sync cues per audio_pipeline
    #    SKILL.md §Workflow).
    sl_json = json.dumps(shot_list, ensure_ascii=False)
    sd_json = json.dumps(script_draft, ensure_ascii=False)
    goal = (
        f"Apply the audio_pipeline expert skill (voicer sub-step) to perform "
        f"V8.6 Step 7B + Step 10 TTS voice generation for episode "
        f"{episode_id}. First call skill_view(name='audio_pipeline') to load "
        f"the expert, then follow its voicer Workflow: generate TTS voice "
        f"clips for narration + dialogue per shot (matching the shot-list "
        f"durations and script-draft text), and produce a voice timeline "
        f"alignment (per-shot start/end timestamps + lip-sync cues for "
        f"downstream p11 video render). "
        f"Shot list from p09: {sl_json}. "
        f"Script draft from p03: {sd_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"voice_clips": [...], '
        f'"voice_timeline": {{...}}}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "shot_list": shot_list,
            "script_draft": script_draft,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous — D-35-02 confirms blocking).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: voice-clips + voice-timeline are separate slots so
    #    downstream phases (p11 video render, p12 composition) can read each
    #    independently.
    voice_clips = expert_output.get("voice_clips", [])
    voice_timeline = expert_output.get("voice_timeline", {})
    asset_bus_write("voice-clips", voice_clips)
    asset_bus_write("voice-timeline", voice_timeline)

    # 5. No gate for p10 (GATE_ID is None — CF-36-04 conditional skip).
    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": None,
    }
