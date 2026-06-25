"""p13_delivery.py — Phase 13: final delivery (V8.6 §13).

Reference port of Node.js step13 (color grade + compliance check + final
package). Per CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM
calls, no prompt templates, no business logic.

Per CF-36-03 (Pattern 3), p13 is a SINGLE delegate_task call: colorist
applies the LUT + final grade per color-intent; compliance_gate runs the
CN red-line + AIGC labeling check; editor performs the final-cut + render
of master.mp4. The subagent orchestrates this 3-expert collaboration
internally.

Inputs (asset bus READ):
  - ``master-timeline`` — FxRxT master timeline from p12
  - ``audio-stems``     — audio stems (BGM/SFX/voice/mix) from p12
  - ``color-intent``    — CxSxZ color intent + LUT design from p07

Outputs (asset bus WRITE):
  - ``master-mp4``        — Final master.mp4 metadata (path, duration,
                            resolution, codec). Preserves the v4.0
                            PIPE-COMPOSE-01 contract — master.mp4 is the
                            canonical pipeline output artifact.
  - ``delivery-package``  — Delivery package manifest (master + captions +
                            compliance report + metadata)

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 8 ``final-delivery`` — operator + compliance_gate confirm CN
    content-rules + AIGC labeling before release (per references/review-gates.md
    + V8.6 gates.yaml).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p13_delivery"
EXPERT = "colorist"  # primary; compliance_gate + editor collaborate
INPUT_SLOTS = ["master-timeline", "audio-stems", "color-intent"]
OUTPUT_SLOTS = ["master-mp4", "delivery-package"]
GATE_ID = "final-delivery"  # Gate 8 per V8.6 gates.yaml


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p13 (V8.6 §13 final delivery).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p13_delivery", "outputs": {...}, "gate": {...} | None}``.

    The single delegate_task call instructs the subagent to load the
    colorist, compliance_gate, and editor expert skills, then have them
    collaborate to produce the final master.mp4 + delivery package.
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    master_timeline = asset_bus_read("master-timeline") or {}
    audio_stems = asset_bus_read("audio-stems") or {}
    color_intent = asset_bus_read("color-intent") or {}

    # 2. Construct the V8.6 §13 goal: colorist + compliance_gate + editor
    #    collaborate in a SINGLE delegate_task call (CF-36-03).
    mt_json = json.dumps(master_timeline, ensure_ascii=False)
    as_json = json.dumps(audio_stems, ensure_ascii=False)
    ci_json = json.dumps(color_intent, ensure_ascii=False)
    goal = (
        f"Apply the colorist AND compliance_gate AND editor expert skills in "
        f"a V8.6 Step 13 final delivery operation for episode {episode_id}. "
        f"First call skill_view(name='colorist') and "
        f"skill_view(name='compliance_gate') and skill_view(name='editor') "
        f"to load all three experts, then have them collaborate. "
        f"colorist applies the LUT + final grade per the color-intent "
        f"(CxSxZ 28-combination) per colorist SKILL.md §Workflow; "
        f"compliance_gate runs the CN red-line content-rules check + AIGC "
        f"labeling verification per compliance_gate SKILL.md §Workflow and "
        f"emits a compliance_report; editor performs the final-cut conform "
        f"and renders the master.mp4 (per editor SKILL.md §Workflow) — "
        f"master.mp4 is the canonical pipeline output artifact (v4.0 "
        f"PIPE-COMPOSE-01 contract). "
        f"Master timeline from p12: {mt_json}. "
        f"Audio stems from p12: {as_json}. "
        f"Color intent from p07: {ci_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"master_mp4": {{"path": ..., "duration": ..., '
        f'"resolution": ..., "codec": ...}}, "delivery_package": '
        f'{{"manifest": [...], "metadata": {{...}}, '
        f'"compliance_report": {{...}}}}}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "master_timeline": master_timeline,
            "audio_stems": audio_stems,
            "color_intent": color_intent,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous — D-35-02 confirms blocking). SINGLE call.
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: master-mp4 + delivery-package are separate slots.
    #    master-mp4 preserves the v4.0 PIPE-COMPOSE-01 contract.
    master_mp4 = expert_output.get("master_mp4", {})
    delivery_package = expert_output.get("delivery_package", {})
    asset_bus_write("master-mp4", master_mp4)
    asset_bus_write("delivery-package", delivery_package)

    # 5. Trigger Gate 8 final-delivery if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p13: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
