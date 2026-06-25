"""p09_shot_breakdown.py — Phase 09: shot breakdown + E-Konte (V8.6 Step 9).

Reference port of Node.js step9 (shot list construction + E-Konte 5-layer
decomposition + continuity pre-check). Per CONTEXT D-35-04 this module is
PURE ORCHESTRATION — no LLM calls, no prompt templates, no business logic.

Per the V8.6 Step 9 contract, cinematographer and continuity_auditor
collaborate in a SINGLE delegate_task call (CF-36-03, Pattern 3):
  - cinematographer decomposes each selected scene into a shot list and
    produces the E-Konte 5-layer sheets (composition / camera / lighting /
    action / dialogue per shot)
  - continuity_auditor runs the pre-render continuity check (character
    anchors + geometry-bed + spatio-temporal axis adherence) and flags
    any cross-shot inconsistencies for fix-up before p11 video render

The subagent orchestrates this 2-expert collaboration internally.

Inputs (asset bus READ):
  - ``scene-selection`` — output of p08 (operator-approved scene subset)
  - ``spatio-temporal-script`` — output of p06 (shot intent + axis + locks)
  - ``character-bible`` — Character Bible 2.0 from p04 (4D-Anchor + style)

Outputs (asset bus WRITE):
  - ``shot-list`` — shot list (one entry per shot with intent + duration)
  - ``e-konte-sheets`` — E-Konte 5-layer shot decomposition sheets

Gate triggered: None — p09 has no review gate (per CONTEXT D-36-02 table).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p09_shot_breakdown"
EXPERT = "cinematographer"  # primary; continuity_auditor collaborates
INPUT_SLOTS = ["scene-selection", "spatio-temporal-script", "character-bible"]
OUTPUT_SLOTS = ["shot-list", "e-konte-sheets"]
GATE_ID = None  # no review gate for p09 (per CONTEXT D-36-02 table)


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p09 (V8.6 Step 9 shot breakdown + E-Konte).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p09_shot_breakdown", "outputs": {...}, "gate": None}``.
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    scene_selection = asset_bus_read("scene-selection") or []
    spatio_temporal_script = asset_bus_read("spatio-temporal-script") or {}
    character_bible = asset_bus_read("character-bible") or {}

    # 2. Construct the V8.6 Step 9 goal: cinematographer +
    #    continuity_auditor collaborate in a single delegate_task call.
    #    cinematographer decomposes selected scenes into a shot list and
    #    produces the E-Konte 5-layer sheets; continuity_auditor runs the
    #    pre-render continuity check against character-bible + geometry-bed.
    ss_json = json.dumps(scene_selection, ensure_ascii=False)
    sts_json = json.dumps(spatio_temporal_script, ensure_ascii=False)
    cb_json = json.dumps(character_bible, ensure_ascii=False)
    goal = (
        f"Apply the cinematographer AND continuity_auditor expert skills in a "
        f"V8.6 Step 9 shot breakdown + E-Konte decomposition for episode "
        f"{episode_id}. "
        f"First call skill_view(name='cinematographer') and "
        f"skill_view(name='continuity_auditor') to load both experts, then "
        f"have them collaborate: cinematographer decomposes each selected "
        f"scene into a shot list (one entry per shot with intent + duration) "
        f"and produces the E-Konte 5-layer sheets (composition / camera / "
        f"lighting / action / dialogue per shot, per cinematographer SKILL.md "
        f"§Workflow); continuity_auditor runs the pre-render continuity check "
        f"against the character-bible 4D-Anchor + style_prefix + the geometry "
        f"bed + spatio-temporal axis adherence, flagging any cross-shot "
        f"inconsistencies for fix-up before video render (per "
        f"continuity_auditor SKILL.md §Workflow). "
        f"Scene selection from p08: {ss_json}. "
        f"Spatio-temporal script from p06: {sts_json}. "
        f"Character bible from p04: {cb_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"shot_list": [...], '
        f'"e_konte_sheets": [...]}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "scene_selection": scene_selection,
            "spatio_temporal_script": spatio_temporal_script,
            "character_bible": character_bible,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: shot-list + e-konte-sheets are separate slots so
    #    downstream phases (p10 voice, p11 video render) can read each
    #    independently without re-parsing a mega-payload.
    shot_list = expert_output.get("shot_list", [])
    e_konte_sheets = expert_output.get("e_konte_sheets", [])
    asset_bus_write("shot-list", shot_list)
    asset_bus_write("e-konte-sheets", e_konte_sheets)

    # 5. No gate for p09 (GATE_ID is None — CF-36-04 conditional skip).
    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": None,
    }
