"""p02_outline.py — Phase 02: story framework + outline atomic (V8.6 §2).

Reference port of Node.js step2.5 + step3 (creative_source produces
StoryKernel via Snowflake Method; screenplay consumes Snowflake Step 4
to produce Snyder 15-beat sheet). Per CONTEXT D-35-04 this module is
PURE ORCHESTRATION — all creative work delegated to movie-expert skills.

Per V8.6 §2 atomic operation, the two experts (creative_source + screenplay)
collaborate in a SINGLE delegate_task call. The subagent loads both expert
SKILL.md files via skill_view and orchestrates their collaboration:
  - creative_source produces StoryKernel + Snowflake Method artifacts
  - screenplay consumes Snowflake Step 4 to produce the Snyder 15-beat sheet

Inputs (asset bus READ):
  - ``topic-kernel`` — output of p01 (TopicKernel JSON)

Outputs (asset bus WRITE):
  - ``story-framework`` — StoryKernel + snowflake_artifacts + Snyder 15 beats

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 2 ``story-framework-outline`` (per references/review-gates.md).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .p01_hook_topic import _parse_expert_output  # reuse parser

logger = logging.getLogger(__name__)

PHASE_ID = "p02_outline"
EXPERT = "creative_source"  # primary; screenplay collaborates (V8.6 §2 atomic)
INPUT_SLOTS = ["topic-kernel"]
OUTPUT_SLOTS = ["story-framework"]
GATE_ID = "story-framework-outline"


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
) -> dict:
    """Execute phase p02 (V8.6 §2 story framework + outline atomic).

    See ``p01_hook_topic.run`` for the full arg contract. Returns
    ``{"phase": "p02_outline", "outputs": {...}, "gate": {...} | None}``.
    """
    # 1. Gather inputs (graceful when slot empty).
    topic_kernel = asset_bus_read("topic-kernel") or {}

    # 2. Construct the V8.6 §2 atomic goal: both experts collaborate in
    #    a single delegate_task call. creative_source produces StoryKernel
    #    via Snowflake Method; screenplay consumes Snowflake Step 4 to
    #    produce Snyder 15-beat sheet (per screenplay SKILL.md §Workflow).
    topic_kernel_json = json.dumps(topic_kernel, ensure_ascii=False)
    goal = (
        f"Apply the creative_source AND screenplay expert skills in a single "
        f"V8.6 §2 atomic operation to produce a story framework + Snyder "
        f"15-beat outline for episode {episode_id}. "
        f"First call skill_view(name='creative_source') and "
        f"skill_view(name='screenplay') to load both experts, then have them "
        f"collaborate: creative_source produces a StoryKernel via the Snowflake "
        f"Method and emits Snowflake artifacts; screenplay consumes Snowflake "
        f"Step 4 to produce the Snyder 15-beat sheet (per screenplay SKILL.md "
        f"§Workflow Step 1.5). Topic Kernel from p01: {topic_kernel_json}. "
        f"Emit the final output as a single fenced JSON block at end of your "
        f'summary, shaped as {{"story_kernel": {{...}}, '
        f'"snowflake_artifacts": {{...}}, "snyder_beats": [...]}}.'
    )
    context = json.dumps(
        {"episode_id": episode_id, "topic_kernel": topic_kernel},
        ensure_ascii=False,
    )

    # 3. Delegate (synchronous).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write the whole expert payload as the story-framework slot
    #    (StoryKernel + Snowflake artifacts + Snyder beats live together
    #    per the V8.6 §2 atomic output contract; downstream phases and the
    #    gate reviewer see one cohesive framework).
    asset_bus_write("story-framework", expert_output)

    # 5. Trigger gate if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p02: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }
