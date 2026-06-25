"""p08_scene_selection.py — Phase 08: scene selection + geometry-bed (V8.6 Step 8).

Reference port of Node.js step8 (operator-approved scene subset selection +
cross-shot geometry-bed consistency construction). Per CONTEXT D-35-04 this
module is PURE ORCHESTRATION — no LLM calls, no prompt templates, no
business logic.

Per the V8.6 Step 8 contract, cinematographer and editor collaborate in a
SINGLE delegate_task call (CF-36-03, Pattern 3):
  - cinematographer selects the operator-approved scene subset and
    establishes the geometric continuity rules across shots
  - editor validates the selection for narrative pacing + cut rhythm and
    constructs the geometry-bed (shared 3D anchor frame for cross-shot
    consistency)

The subagent orchestrates this 2-expert collaboration internally.

Inputs (asset bus READ):
  - ``scene-images`` — output of p07 (5-view scene image set per scene)
  - ``spatio-temporal-script`` — output of p06 (shot intent + axis + locks)

Outputs (asset bus WRITE):
  - ``scene-selection`` — operator-approved scene subset
  - ``geometry-bed`` — cross-shot geometry consistency bed

Gate triggered: None — p08 has no review gate (per CONTEXT D-36-02 table).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p08_scene_selection"
EXPERT = "cinematographer"  # primary; editor collaborates (V8.6 Step 8)
INPUT_SLOTS = ["scene-images", "spatio-temporal-script"]
OUTPUT_SLOTS = ["scene-selection", "geometry-bed"]
GATE_ID = None  # no review gate for p08 (per CONTEXT D-36-02 table)


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p08 (V8.6 Step 8 scene selection + geometry-bed).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p08_scene_selection", "outputs": {...}, "gate": None}``.
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    scene_images = asset_bus_read("scene-images") or []
    spatio_temporal_script = asset_bus_read("spatio-temporal-script") or {}

    # 2. Construct the V8.6 Step 8 goal: cinematographer + editor
    #    collaborate in a single delegate_task call. cinematographer
    #    selects the operator-approved scene subset; editor validates the
    #    selection for narrative pacing + cut rhythm and constructs the
    #    geometry-bed (cross-shot 3D anchor frame consistency).
    si_json = json.dumps(scene_images, ensure_ascii=False)
    sts_json = json.dumps(spatio_temporal_script, ensure_ascii=False)
    goal = (
        f"Apply the cinematographer AND editor expert skills in a V8.6 Step 8 "
        f"scene selection + geometry-bed construction operation for episode "
        f"{episode_id}. "
        f"First call skill_view(name='cinematographer') and "
        f"skill_view(name='editor') to load both experts, then have them "
        f"collaborate: cinematographer selects the operator-approved scene "
        f"subset based on shot intent + axis + composition locks (per "
        f"cinematographer SKILL.md §Workflow); editor validates the selection "
        f"for narrative pacing + cut rhythm and constructs the geometry-bed "
        f"(cross-shot 3D anchor frame for geometry consistency per editor "
        f"SKILL.md §Workflow). "
        f"Scene images from p07: {si_json}. "
        f"Spatio-temporal script from p06: {sts_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"scene_selection": [...], '
        f'"geometry_bed": {{...}}}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "scene_images": scene_images,
            "spatio_temporal_script": spatio_temporal_script,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: scene selection + geometry-bed are separate slots
    #    so downstream phases (p09 shot breakdown, p11 video render) can
    #    read each independently.
    scene_selection = expert_output.get("scene_selection", [])
    geometry_bed = expert_output.get("geometry_bed", {})
    asset_bus_write("scene-selection", scene_selection)
    asset_bus_write("geometry-bed", geometry_bed)

    # 5. No gate for p08 (GATE_ID is None — CF-36-04 conditional skip).
    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": None,
    }
