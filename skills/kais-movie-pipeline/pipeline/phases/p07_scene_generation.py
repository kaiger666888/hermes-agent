"""p07_scene_generation.py — Phase 07: scene generation + style + color atomic (V8.6 §4).

Reference port of Node.js step7 (scene image generation + style genome
construction + color intent design). Per CONTEXT D-35-04 this module is
PURE ORCHESTRATION — no LLM calls, no prompt templates, no business logic.

Per V8.6 §4 atomic operation, four experts collaborate in a SINGLE
delegate_task call (CF-36-03, Pattern 3):
  - visual_executor generates scene images (5-view per scene per its
    SKILL.md §Workflow — front/side/back/turnaround/zoom-in)
  - prompt_injector injects the 5D style genome + character anchors into
    every image prompt (consistency enforcement)
  - style_genome constructs the 5D style vector (genre/mood/aesthetic/
    pace/color)
  - colorist designs the CxSxZ 28-combination color intent + LUT plan

The subagent orchestrates this 4-expert collaboration internally; the
phase module does NOT loop, does NOT call skill_view in parent context,
and does NOT split the atomic op across multiple delegate_task calls
(that would re-introduce the V8.4-era 25-step complexity V8.6 collapsed).

Inputs (asset bus READ):
  - ``spatio-temporal-script`` — output of p06 (shot intent + axis + locks)
  - ``character-assets`` — L1-L4 character asset manifest from p04

Outputs (asset bus WRITE):
  - ``scene-images`` — 5-view scene image set per scene
  - ``style-vector`` — 5D style genome vector
  - ``color-intent`` — CxSxZ 28-combination color intent + LUT design

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 5 ``scene-design`` — operator confirms 4-dim consistency (per
    references/review-gates.md).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p07_scene_generation"
# Primary expert; prompt_injector + style_genome + colorist collaborate
# (V8.6 §4 atomic — 4 experts in ONE delegate_task call).
EXPERT = "visual_executor"
INPUT_SLOTS = ["spatio-temporal-script", "character-assets"]
OUTPUT_SLOTS = ["scene-images", "style-vector", "color-intent"]
GATE_ID = "scene-design"


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p07 (V8.6 §4 scene generation + style + color atomic).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p07_scene_generation", "outputs": {...}, "gate": {...} | None}``.

    The atomic §4 invariant: despite 4 collaborating experts, there is
    exactly ONE delegate_task call. Tests assert this invariant.
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    spatio_temporal_script = asset_bus_read("spatio-temporal-script") or {}
    character_assets = asset_bus_read("character-assets") or {}

    # 2. Construct the V8.6 §4 atomic goal: visual_executor +
    #    prompt_injector + style_genome + colorist collaborate in a single
    #    delegate_task call. The subagent loads all 4 expert SKILL.md files
    #    via skill_view and orchestrates the 4-expert collaboration:
    #      (a) style_genome constructs the 5D style vector
    #      (b) visual_executor generates 5-view scene images per scene
    #      (c) prompt_injector enforces character/style consistency across
    #          all generated image prompts
    #      (d) colorist designs the CxSxZ 28-combination color intent + LUT
    sts_json = json.dumps(spatio_temporal_script, ensure_ascii=False)
    ca_json = json.dumps(character_assets, ensure_ascii=False)
    goal = (
        f"Apply the visual_executor AND prompt_injector AND style_genome AND "
        f"colorist expert skills in a V8.6 §4 atomic operation to produce "
        f"scene images + style vector + color intent for episode "
        f"{episode_id}. "
        f"First call skill_view(name='visual_executor') and "
        f"skill_view(name='prompt_injector') and skill_view(name='style_genome') "
        f"and skill_view(name='colorist') to load all four experts, then have "
        f"them collaborate atomically: style_genome constructs the 5D style "
        f"vector (genre/mood/aesthetic/pace/color); visual_executor generates "
        f"the 5-view scene image set per scene (front/side/back/turnaround/"
        f"zoom-in per visual_executor SKILL.md §Workflow); prompt_injector "
        f"enforces character anchor + style consistency across every generated "
        f"image prompt; colorist designs the CxSxZ 28-combination color intent "
        f"+ LUT plan (per colorist SKILL.md §Workflow). "
        f"Spatio-temporal script from p06: {sts_json}. "
        f"Character assets from p04: {ca_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"scene_images": [...], '
        f'"style_vector": {{"genre": ..., "mood": ..., "aesthetic": ..., '
        f'"pace": ..., "color": ...}}, "color_intent": {{...}}}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "spatio_temporal_script": spatio_temporal_script,
            "character_assets": character_assets,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous — D-35-02 confirms blocking). Atomic §4
    #    invariant: ONE delegate_task call despite 4 experts.
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: scene images, style vector, color intent are
    #    separate slots so downstream phases (p08 scene selection, p11
    #    video render, p12 composition, p13 delivery) can read each
    #    independently without re-parsing a mega-payload.
    scene_images = expert_output.get("scene_images", [])
    style_vector = expert_output.get("style_vector", {})
    color_intent = expert_output.get("color_intent", {})
    asset_bus_write("scene-images", scene_images)
    asset_bus_write("style-vector", style_vector)
    asset_bus_write("color-intent", color_intent)

    # 5. Trigger gate if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p07: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
