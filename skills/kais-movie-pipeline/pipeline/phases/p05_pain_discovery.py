"""p05_pain_discovery.py — Phase 05: pain point mining atomic (V8.6 Step 5).

Reference port of Node.js step5 pain-point mining (L1-L6 strata + escalation
ladder). Per CONTEXT D-35-04 + D-36-01 this module is PURE ORCHESTRATION — no
LLM calls, no prompt templates, no business logic. All creative work delegated
to the ``creative_source`` (re-invoked) + ``theory_critic`` movie-expert skills
via ``delegate_task``.

Per V8.6 Step 5 atomic operation, the two experts collaborate in a SINGLE
delegate_task call. The subagent loads both expert SKILL.md files via
skill_view and orchestrates their collaboration:
  - creative_source mines the L1-L6 pain point strata from the Character Bible
  - theory_critic stress-tests the strata and constructs the escalation ladder
    (step-by-step intensity curve)

Inputs (asset bus READ):
  - ``character-bible`` — output of p04 (Character Bible 2.0)
  - ``script-draft``    — output of p03 (scene-level script, for context)

Outputs (asset bus WRITE):
  - ``pain-points``        — L1-L6 pain point strata JSON
  - ``escalation-ladder``  — escalation ladder JSON

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 4 ``shot-prep`` (per V8.6 gates.yaml + CONTEXT D-36-02 — operator
    confirms pain points + escalation ladder before visual design in p06-p07).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p05_pain_discovery"
EXPERT = "creative_source"  # primary (re-invoked); theory_critic collaborates
INPUT_SLOTS = ["character-bible", "script-draft"]
OUTPUT_SLOTS = ["pain-points", "escalation-ladder"]
GATE_ID = "shot-prep"  # Gate 4 — operator confirms pain+escalation


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p05 (V8.6 Step 5 pain point mining atomic).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p05_pain_discovery", "outputs": {...}, "gate": {...} | None}``.
    """
    # 1. Gather inputs (graceful when slots empty).
    character_bible = asset_bus_read("character-bible") or {}
    script_draft = asset_bus_read("script-draft") or {}

    # 2. Construct the V8.6 Step 5 atomic goal: creative_source +
    #    theory_critic collaborate in a single delegate_task call.
    #    creative_source mines L1-L6 pain strata from the Character Bible;
    #    theory_critic stress-tests the strata and constructs the escalation
    #    ladder (step-by-step intensity curve).
    bible_json = json.dumps(character_bible, ensure_ascii=False)
    script_json = json.dumps(script_draft, ensure_ascii=False)
    goal = (
        f"Apply the creative_source AND theory_critic expert skills in a "
        f"V8.6 Step 5 atomic operation for episode {episode_id}: mine the "
        f"L1-L6 pain point strata and construct the escalation ladder. "
        f"First call skill_view(name='creative_source') and "
        f"skill_view(name='theory_critic') to load both experts, then have "
        f"them collaborate: creative_source mines the L1-L6 pain strata "
        f"(surface annoyance → deep existential wounds) from the Character "
        f"Bible per creative_source SKILL.md §Workflow, and theory_critic "
        f"stress-tests the strata for escalation validity and constructs the "
        f"step-by-step escalation ladder. Character Bible from p04: "
        f"{bible_json}. Script draft from p03 (context): {script_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"pain_points": [...], '
        f'"escalation_ladder": [...]}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "character_bible": character_bible,
            "script_draft": script_draft,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: pain points and escalation ladder as separate slots so
    #    p06 (spatio-temporal script) can consume them and Gate 4 reviewer
    #    can inspect them independently.
    pain_points = expert_output.get("pain_points", [])
    escalation_ladder = expert_output.get("escalation_ladder", [])
    asset_bus_write("pain-points", pain_points)
    asset_bus_write("escalation-ladder", escalation_ladder)

    # 5. Trigger Gate 4 shot-prep if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p05: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
