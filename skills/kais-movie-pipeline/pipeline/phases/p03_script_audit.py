"""p03_script_audit.py — Phase 03: script + audit atomic loop (V8.6 §3).

Reference port of Node.js step5 + step5B + step6 (script_draft + audit +
revise loop). Per CONTEXT D-35-04 this module is PURE ORCHESTRATION.

Per V8.6 §3 atomic operation, screenplay and script_auditor collaborate in
a SINGLE delegate_task call in an atomic loop:
  1. screenplay writes scene-level script
  2. script_auditor runs the 5-dimension audit (drama / rhythm / character /
     logic / theme)
  3. screenplay revises if ``predicted_completion_band`` < target (per
     script_auditor SKILL.md the revise threshold is band C/D, ~65%)

The subagent orchestrates this loop internally (the phase module does not
loop — the EXPERT skill encapsulates the revise logic).

Inputs (asset bus READ):
  - ``story-framework`` — output of p02 (StoryKernel + Snowflake + Snyder)

Outputs (asset bus WRITE):
  - ``script-draft``  — scene-level script JSON
  - ``audit-report``  — 5-dim audit scores JSON

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 3 ``script-audit`` (per references/review-gates.md).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p03_script_audit"
EXPERT = "screenplay"  # primary; script_auditor collaborates (V8.6 §3 atomic)
INPUT_SLOTS = ["story-framework"]
OUTPUT_SLOTS = ["script-draft", "audit-report"]
GATE_ID = "script-audit"


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p03 (V8.6 §3 script + audit atomic loop).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p03_script_audit", "outputs": {...}, "gate": {...} | None}``.
    """
    # 1. Gather inputs.
    story_framework = asset_bus_read("story-framework") or {}

    # 2. Construct the V8.6 §3 atomic goal: screenplay + script_auditor
    #    collaborate in a revise loop inside a single delegate_task call.
    sf_json = json.dumps(story_framework, ensure_ascii=False)
    goal = (
        f"Apply the screenplay AND script_auditor expert skills in a V8.6 §3 "
        f"atomic loop for episode {episode_id}: screenplay writes the "
        f"scene-level script, script_auditor runs the 5-dimension audit "
        f"(drama / rhythm / character / logic / theme), and screenplay "
        f"revises if the predicted completion band falls below target "
        f"(< 65% / band C or D per script_auditor SKILL.md). "
        f"First call skill_view(name='screenplay') and "
        f"skill_view(name='script_auditor') to load both experts, then run "
        f"the write-audit-revise loop until the audit reaches an acceptable "
        f"band. Story framework from p02: {sf_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"script": {{"scenes": [...]}}, '
        f'"audit": {{"scores": {{...}}, "total_score": N, '
        f'"predicted_completion_band": "A|B|C|D"}}}}.'
    )
    context = json.dumps(
        {"episode_id": episode_id, "story_framework": story_framework},
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs: script and audit are emitted as separate slots so
    #    downstream phases (p04+ scene/character design) and the gate
    #    reviewer can read them independently.
    script = expert_output.get("script", {})
    audit = expert_output.get("audit", {})
    asset_bus_write("script-draft", script)
    asset_bus_write("audit-report", audit)

    # 5. Trigger gate if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p03: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
