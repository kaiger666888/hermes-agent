"""p04_character_design.py — Phase 04: character design atomic (V8.6 Step 4).

Reference port of Node.js step4 (Character Bible 2.0 + L1-L4 asset manifest).
Per CONTEXT D-35-04 + D-36-01 this module is PURE ORCHESTRATION — no LLM
calls, no prompt templates, no business logic. All creative work delegated
to the ``character_designer`` + ``visual_executor`` movie-expert skills via
``delegate_task``.

Per V8.6 Step 4 atomic operation, the two experts collaborate in a SINGLE
delegate_task call. The subagent loads both expert SKILL.md files via
skill_view and orchestrates their collaboration:
  - character_designer produces Character Bible 2.0 (4D-Anchor + style_prefix)
  - visual_executor (drawer sub-step) renders the L1-L4 asset manifest
    (identity anchors + costume cards)

Inputs (asset bus READ):
  - ``script-draft`` — output of p03 (scene-level script)

Outputs (asset bus WRITE):
  - ``character-bible``  — Character Bible 2.0 JSON
  - ``character-assets`` — L1-L4 asset manifest JSON

Gate triggered: None — per V8.6 gates.yaml, Gate 4 ``shot-prep`` fires after
p05 (pain discovery), not p04. Cf. CONTEXT.md D-36-02 table note.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p04_character_design"
EXPERT = "character_designer"  # primary; visual_executor collaborates (drawer)
INPUT_SLOTS = ["script-draft"]
OUTPUT_SLOTS = ["character-bible", "character-assets"]
GATE_ID = None  # Gate 4 shot-prep fires after p05, not p04


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p04 (V8.6 Step 4 character design atomic).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p04_character_design", "outputs": {...}, "gate": None}``.
    """
    # 1. Gather inputs (graceful when slot empty).
    script_draft = asset_bus_read("script-draft") or {}

    # 2. Construct the V8.6 Step 4 atomic goal: character_designer +
    #    visual_executor collaborate in a single delegate_task call.
    #    character_designer produces Character Bible 2.0 (4D-Anchor +
    #    style_prefix); visual_executor renders the L1-L4 asset manifest
    #    (identity anchors + costume cards).
    script_json = json.dumps(script_draft, ensure_ascii=False)
    goal = (
        f"Apply the character_designer AND visual_executor expert skills in "
        f"a V8.6 Step 4 atomic operation for episode {episode_id}: produce a "
        f"Character Bible 2.0 and an L1-L4 asset manifest. "
        f"First call skill_view(name='character_designer') and "
        f"skill_view(name='visual_executor') to load both experts, then have "
        f"them collaborate: character_designer drafts the Character Bible 2.0 "
        f"(4D-Anchor identity + style_prefix per character_designer SKILL.md "
        f"§Workflow), and visual_executor renders the L1-L4 asset manifest "
        f"(L1 identity anchors, L2 expression sheets, L3 costume cards, L4 "
        f"prop cards). Script draft from p03: {script_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"character_bible": {{...}}, '
        f'"character_assets": {{...}}}}.'
    )
    context = json.dumps(
        {"episode_id": episode_id, "script_draft": script_draft},
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous — D-35-02 confirms blocking).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: character bible and asset manifest are separate slots
    #    so downstream phases (p05 pain discovery, p06 spatio-temporal, p07
    #    scene generation) and the L1-L4 asset consumers read them independently.
    character_bible = expert_output.get("character_bible", {})
    character_assets = expert_output.get("character_assets", {})
    asset_bus_write("character-bible", character_bible)
    asset_bus_write("character-assets", character_assets)

    # 5. No gate for p04 (GATE_ID is None — Gate 4 shot-prep fires after p05).
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p04: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
