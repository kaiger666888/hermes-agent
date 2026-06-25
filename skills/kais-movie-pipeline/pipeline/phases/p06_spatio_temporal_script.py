"""p06_spatio_temporal_script.py — Phase 06: spatio-temporal script + final
audit atomic (V8.6 Step 6 / §5 atomic operation).

Reference port of Node.js step6 spatio-temporal script + final audit. Per
CONTEXT D-35-04 + D-36-01 + CF-36-03 this module is PURE ORCHESTRATION — no
LLM calls, no prompt templates, no business logic. All creative work delegated
to the ``screenplay`` + ``cinematographer`` + ``script_auditor`` movie-expert
skills via a SINGLE ``delegate_task`` call (atomic §5 invariant per
CF-36-03 — despite 3 collaborating experts, this is ONE delegate call).

The subagent loads all three expert SKILL.md files via skill_view and
orchestrates their collaboration internally:
  - screenplay produces the spatio-temporal script (shot intent + dialogue
    timing + scene transitions)
  - cinematographer locks the axis (180° rule) + composition + camera intent
    per shot
  - script_auditor runs the final 5-dimension audit on the spatio-temporal
    script (post-spatio-temporal pass)

Inputs (asset bus READ):
  - ``script-draft``     — output of p03 (scene-level script)
  - ``character-bible``  — output of p04 (Character Bible 2.0)

Outputs (asset bus WRITE):
  - ``spatio-temporal-script`` — shot intent + axis + composition_lock JSON
  - ``final-audit``           — final 5-dim audit report JSON

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 6 ``spatio-temporal`` (per V8.6 gates.yaml — operator confirms the
    spatio-temporal script + final audit before scene generation).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p06_spatio_temporal_script"
EXPERT = "screenplay"  # primary; cinematographer + script_auditor collaborate
INPUT_SLOTS = ["script-draft", "character-bible"]
OUTPUT_SLOTS = ["spatio-temporal-script", "final-audit"]
GATE_ID = "spatio-temporal"  # Gate 6


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p06 (V8.6 Step 6 / §5 atomic spatio-temporal + audit).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p06_spatio_temporal_script", "outputs": {...}, "gate": {...} | None}``.

    Note: Despite 3 collaborating experts, this is ONE delegate_task call
    (atomic §5 invariant per CF-36-03).
    """
    # 1. Gather inputs (graceful when slots empty).
    script_draft = asset_bus_read("script-draft") or {}
    character_bible = asset_bus_read("character-bible") or {}

    # 2. Construct the V8.6 §5 atomic goal: screenplay + cinematographer +
    #    script_auditor collaborate in a SINGLE delegate_task call. All three
    #    skill_views MUST be mentioned (atomic §5 invariant).
    script_json = json.dumps(script_draft, ensure_ascii=False)
    bible_json = json.dumps(character_bible, ensure_ascii=False)
    goal = (
        f"Apply the screenplay AND cinematographer AND script_auditor expert "
        f"skills in a V8.6 §5 atomic operation for episode {episode_id}: "
        f"produce a spatio-temporal script and a final audit report. "
        f"First call skill_view(name='screenplay'), "
        f"skill_view(name='cinematographer'), and "
        f"skill_view(name='script_auditor') to load all three experts, then "
        f"have them collaborate in a single atomic pass: screenplay produces "
        f"the spatio-temporal script (shot intent + dialogue timing + scene "
        f"transitions), cinematographer locks the axis (180° rule) + "
        f"composition + camera intent per shot, and script_auditor runs the "
        f"final 5-dimension audit on the spatio-temporal script. Script draft "
        f"from p03: {script_json}. Character Bible from p04: {bible_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"spatio_temporal_script": {{...}}, '
        f'"final_audit": {{...}}}}.'
    )
    context = json.dumps(
        {
            "episode_id": episode_id,
            "script_draft": script_draft,
            "character_bible": character_bible,
        },
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous) — SINGLE call despite 3 experts (atomic §5).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: spatio-temporal script and final audit as separate
    #    slots so downstream phases (p07 scene generation, p08 scene selection,
    #    p09 shot breakdown) and Gate 6 reviewer read them independently.
    spatio_temporal_script = expert_output.get("spatio_temporal_script", {})
    final_audit = expert_output.get("final_audit", {})
    asset_bus_write("spatio-temporal-script", spatio_temporal_script)
    asset_bus_write("final-audit", final_audit)

    # 5. Trigger Gate 6 spatio-temporal if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p06: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
