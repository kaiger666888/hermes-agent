"""p01_hook_topic.py — Phase 01: hook + topic atomic (V8.6 §1).

Reference port of the Node.js Step 1 + Step 2 atomic merge (V8.6 §1).
Per CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM calls, no
prompt templates, no business logic. All creative work is delegated to the
``hook_retention`` movie-expert skill via ``delegate_task``.

Behavioral contract (mirrors ``lib/phases/index.js`` topic-selection +
audienceMatch hook, lines ~592 + ~1639-1676 — but ported as a SINGLE
delegate_task call because the hook_retention EXPERT skill encapsulates
the full Workflow including the 10-dim emotional resonance scan, Topic
Kernel resonance formula, and 3-sec hook candidates).

Inputs (asset bus READ):
  - ``requirement`` — operator's high-level ask (topic, tone, audience, etc.)

Outputs (asset bus WRITE):
  - ``topic-kernel`` — TopicKernel JSON (title, audience, resonance dims)
  - ``hook-design``  — hook_design JSON (type, duration_sec, script)

Gate triggered (when ``trigger_gate`` is provided):
  - Gate 1 ``selection-topic-hook`` — operator confirms topic + hook candidates
    (per references/review-gates.md).

D-35-07 delegate_task contract: the ``goal`` is self-contained — it tells the
subagent to call ``skill_view(name='hook_retention')`` first to load the
expert SKILL.md, then follow the expert's Workflow to produce the demanded
JSON shape. The phase module does NOT call ``skill_view`` in parent context
(anti-pattern: that burns parent context).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phase metadata — referenced by runner.py + tests
# ---------------------------------------------------------------------------

PHASE_ID = "p01_hook_topic"
EXPERT = "hook_retention"
INPUT_SLOTS = ["requirement"]
OUTPUT_SLOTS = ["topic-kernel", "hook-design"]
GATE_ID = "selection-topic-hook"


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
    """Execute phase p01 (V8.6 §1 hook + topic atomic).

    Args:
        episode_id: Episode identifier.
        asset_bus_read: Callable(slot) -> data (injected; tests pass mock).
        asset_bus_write: Callable(slot, entry) -> None (injected).
        delegate_task: Callable(goal, context, toolsets) -> dict with a
            "summary" key whose value is a text containing a fenced JSON
            block (D-35-07 contract).
        trigger_gate: Optional Callable(gate_id, episode_id) -> dict. When
            provided, Gate 1 "selection-topic-hook" is triggered after the
            asset-bus writes; when ``None`` no gate is triggered.

    Returns:
        ``{"phase": PHASE_ID, "outputs": {...}, "gate": {...} | None}`` where
        ``outputs`` carries the parsed expert payload (topic_kernel +
        hook_design) and ``gate`` is the gate result (or None).
    """
    # 1. Gather inputs (graceful when the slot is empty — tests/first run).
    requirement = asset_bus_read("requirement") or {}

    # 2. Construct a self-contained goal for the hook_retention expert.
    #    The subagent loads the expert via skill_view first, then applies its
    #    Workflow (10-dim emotional resonance scan + Topic Kernel selection +
    #    3-sec hook candidates per hook_retention/SKILL.md §Workflow).
    requirement_json = json.dumps(requirement, ensure_ascii=False)
    goal = (
        f"Apply the hook_retention expert skill to perform the V8.6 §1 atomic "
        f"operation for episode {episode_id}: 10-dimension emotional resonance "
        f"scan + Topic Kernel selection + 3-second hook design. "
        f"First call skill_view(name='hook_retention') to load the expert, "
        f"then follow its Workflow to produce a TopicKernel JSON and a "
        f"hook_design JSON. Operator requirement: {requirement_json}. "
        f"Emit both as a single fenced JSON block at end of your summary, "
        f'shaped as {{"topic_kernel": {{...}}, "hook_design": {{...}}}}.'
    )
    context = json.dumps(
        {"episode_id": episode_id, "requirement": requirement},
        ensure_ascii=False,
    )

    # 3. Delegate to the expert (synchronous — D-35-02 confirms blocking).
    delegate_result = delegate_task(goal, context, ["skills", "file"])
    expert_output = _parse_expert_output(delegate_result)

    # 4. Write outputs to the asset bus (envelope wrapping handled by the
    #    bus itself when write(..., envelope=True) is called by the runner).
    topic_kernel = expert_output.get("topic_kernel", {})
    hook_design = expert_output.get("hook_design", {})
    asset_bus_write("topic-kernel", topic_kernel)
    asset_bus_write("hook-design", hook_design)

    # 5. Trigger gate if configured.
    gate_result = None
    if GATE_ID and trigger_gate is not None:
        gate_result = trigger_gate(GATE_ID, episode_id)
        logger.info(
            "p01: gate %s triggered for episode %s -> %s",
            GATE_ID, episode_id, gate_result,
        )

    return {
        "phase": PHASE_ID,
        "outputs": expert_output,
        "gate": gate_result,
    }


# ---------------------------------------------------------------------------
# Output parsing helper
# ---------------------------------------------------------------------------


def _parse_expert_output(delegate_result: dict) -> dict:
    """Extract the fenced JSON block from a ``delegate_task`` summary.

    Per D-35-07 phase modules instruct the expert in ``goal`` to emit a
    fenced JSON block at end of its summary. This helper finds the LAST
    ``\\`\\`\\`json ... \\`\\`\\``` block (the expert may emit scratch
    blocks earlier) and ``json.loads`` its body.

    Args:
        delegate_result: dict returned by ``delegate_task`` (must have a
            ``"summary"`` key) OR a plain string.

    Returns:
        Parsed dict (the expert's structured payload).

    Raises:
        ValueError: when the summary contains no parseable fenced JSON block.
        json.JSONDecodeError: when the block body is not valid JSON.
    """
    if isinstance(delegate_result, dict):
        summary = delegate_result.get("summary", "")
    else:
        summary = str(delegate_result)

    if "```json" not in summary:
        raise ValueError(
            f"delegate_task summary missing JSON block; got: {summary[:200]!r}"
        )

    # Take everything after the last ```json fence opener.
    *_, tail = summary.rsplit("```json", 1)
    # The body ends at the next ``` fence closer.
    if "```" not in tail:
        raise ValueError(
            f"delegate_task summary has unclosed ```json block; got: {summary[:200]!r}"
        )
    json_str = tail.split("```", 1)[0].strip()
    return json.loads(json_str)
