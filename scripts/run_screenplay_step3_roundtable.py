#!/usr/bin/env python3
"""CREATIVE-01 — driver for the 9-agent screenplay Step 3 round table.

Plan 53-03 Task 2: orchestrates the vertical-slice smoke test that proves
the three-layer Hermes architecture (SKILL→agent YAML + MCP round-table
state machine + GLM dispatch) works end-to-end.

Lifecycle:

  1. ``round_table_open`` — create state file at
     ``~/.hermes/agents/.runtime/screenplay-step3-poc/round_tables/{uuid}.json``
  2. **STRICT SERIAL** — ``for agent_id in PANEL_9: await get_agent_opinion(...)``
     Each panelist's opinion is chained into the next via ``panel_context``
     (round-table deliberation mechanism — T-53-12 accepted).
     NO concurrent-parallel dispatch (e.g. ``asyncio gather``) — INFRA-04
     hard constraint (Phase 52 SC#4 + MEMORY.md
     ``feedback-glm-overload-reduce-concurrency.md``).
  3. Synthesis pass (10th GLM call) — screenplay expert consolidates the
     9 panelist opinions into final HOOK-09-valid Step 3 JSON.
  4. ``submit_round_table_result`` — flip state to ``completed`` + seal.
  5. Validate output against ``tests/fixtures/screenplay-step3-schema.json``.

Operator invocation:

    python scripts/run_screenplay_step3_roundtable.py \\
        --storykernel tests/fixtures/storykernel-sample.json \\
        --output build/screenplay-step3-output.json \\
        --smoke

Pre-conditions for ``--smoke`` (real GLM):

  - ``~/.hermes/.env`` has a valid GLM API key (GLM_API_KEY / ZAI_API_KEY)
  - ``cli-config.yaml`` has ``auxiliary.round_table_opinion.provider: glm``
    + ``auxiliary.memory_comparator.provider: glm``
  - 9 agent YAMLs at ``~/.hermes/agents/*.agent.yaml`` (run
    ``python scripts/transform_skill_to_agent.py`` first if missing)

When GLM is unavailable, exits with non-zero status + a clear
``configure GLM_API_KEY`` message (no traceback) per CONTEXT.md
"Claude's Discretion" point 6.

CLAUDE.md compliance
--------------------
- ``from __future__ import annotations`` at top
- ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514)
- ``get_hermes_home()`` from ``hermes_constants`` (NEVER ``Path.home()``)
- Lazy %-formatting in log calls
- ``except X as exc:`` with bound name; preserve chains via ``raise ... from exc``
- NO top-level ``run_agent`` import (anti-pattern; this module imports from
  ``mcp_serve`` + ``agent.auxiliary_client`` only — all safe top-level).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# Make the agent.* + mcp_serve imports resolvable when this script is invoked
# directly via ``python scripts/run_screenplay_step3_roundtable.py`` (no
# installed package).
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import mcp_serve  # noqa: E402  (after sys.path insert)
import agent.auxiliary_client  # noqa: E402  — used for call_llm lookup at call-time so monkeypatch works

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# 9-agent panel per CONTEXT.md decision #1 — v3.0+ canonical names, NOT
# the legacy scene_builder / continuity / performer / composer names.
PANEL_9: list[str] = [
    "screenplay",
    "cinematographer",
    "hook_retention",
    "theory_critic",
    "editor",
    "character_designer",
    "continuity_auditor",
    "audio_pipeline",
    "style_genome",
]

PROJECT_SLUG = "screenplay-step3-poc"

# Path to the HOOK-09 schema — same fixture the Wave 0 contract test loads.
SCHEMA_PATH = _ROOT / "tests" / "fixtures" / "screenplay-step3-schema.json"


# --------------------------------------------------------------------------- #
# Public API — run_roundtable()
# --------------------------------------------------------------------------- #


async def run_roundtable(
    storykernel_path: Path,
    output_path: Path,
    *,
    smoke: bool = False,
) -> dict[str, Any]:
    """Drive the 9-agent screenplay Step 3 round table end-to-end.

    Args:
        storykernel_path: Path to a StoryKernel Step 1 JSON file.
        output_path: Where to write the HOOK-09-valid Step 3 JSON artifact.
        smoke: When True, the driver is being run as the SC#2 real-GLM
            smoke test (prints latency + token-cost summary).

    Returns:
        Summary dict ``{"round_id", "panelist_count", "output_path",
        "latency_seconds"}``. On error, returns ``{"error": ...}``.

    Raises:
        RuntimeError: re-raised from ``call_llm`` when GLM is unavailable.
        The CLI ``main()`` wraps this in a friendly message + sys.exit(2).
    """
    started = time.monotonic()

    # Load StoryKernel input.
    storykernel = json.loads(storykernel_path.read_text(encoding="utf-8"))
    logline = storykernel.get("logline", "(no logline)")
    logger.info("run_screenplay_step3: logline=%s", logline)

    # Generate a stable round_id for this run.
    round_id = uuid.uuid4().hex
    logger.info("run_screenplay_step3: round_id=%s", round_id)

    # ------------------------------------------------------------------ #
    # Step 1 — round_table_open
    # ------------------------------------------------------------------ #
    open_resp = await mcp_serve.round_table_open(
        round_id=round_id,
        project_slug=PROJECT_SLUG,
        question=f"Generate screenplay Step 3 for: {logline}",
        panelist_agent_ids=PANEL_9,
        caller="run_screenplay_step3_roundtable.py",
    )
    open_data = json.loads(open_resp)
    if "error" in open_data:
        logger.error("round_table_open failed: %s", open_data)
        return {
            "error": "round_table_open_failed",
            "detail": open_data,
            "round_id": round_id,
        }

    # ------------------------------------------------------------------ #
    # Step 2 — 9 sequential get_agent_opinion calls
    # ------------------------------------------------------------------ #
    # STRICT SERIAL — no concurrent dispatch (INFRA-04 hard constraint).
    # The chained ``panel_context`` IS the round-table deliberation mechanism
    # (T-53-12 accepted threat — panelist B sees panelist A's opinion).
    panel_context: str | None = None
    panel_opinions: list[dict[str, Any]] = []
    for agent_id in PANEL_9:
        resp = await mcp_serve.get_agent_opinion(
            round_id=round_id,
            project_slug=PROJECT_SLUG,
            agent_id=agent_id,
            topic=f"Screenplay Step 3 scene design for: {logline}",
            panel_context=panel_context,
        )
        opinion_data = json.loads(resp)
        if opinion_data.get("status") != "ok":
            logger.error(
                "get_agent_opinion failed for %s: %s", agent_id, opinion_data
            )
            return {
                "error": "get_agent_opinion_failed",
                "agent_id": agent_id,
                "detail": opinion_data,
                "round_id": round_id,
            }
        opinion_text = opinion_data.get("opinion", "")
        panel_opinions.append({"agent_id": agent_id, "opinion": opinion_text})
        panel_context = opinion_text  # chain for the next panelist

    # ------------------------------------------------------------------ #
    # Step 3 — synthesis pass (10th GLM call) → HOOK-09-valid Step 3 JSON
    # ------------------------------------------------------------------ #
    conclusion = await _synthesize_step3_output(
        storykernel=storykernel, panel_opinions=panel_opinions
    )

    # ------------------------------------------------------------------ #
    # Step 4 — submit_round_table_result (terminal transition)
    # ------------------------------------------------------------------ #
    submit_resp = await mcp_serve.submit_round_table_result(
        round_id=round_id,
        project_slug=PROJECT_SLUG,
        conclusion=conclusion,
        cited_memories=[],
        closed_by="run_screenplay_step3_roundtable.py",
    )
    submit_data = json.loads(submit_resp)
    if "error" in submit_data:
        logger.error("submit_round_table_result failed: %s", submit_data)
        return {
            "error": "submit_failed",
            "detail": submit_data,
            "round_id": round_id,
        }

    # ------------------------------------------------------------------ #
    # Step 5 — validate output against HOOK-09 schema + write artifact
    # ------------------------------------------------------------------ #
    try:
        output = json.loads(conclusion)
    except json.JSONDecodeError as exc:
        logger.error("synthesis output is not valid JSON: %s", exc)
        return {
            "error": "synthesis_invalid_json",
            "detail": str(exc),
            "raw": conclusion[:500],
            "round_id": round_id,
        }

    _validate_step3_schema(output, output_path)

    latency = time.monotonic() - started
    summary = {
        "round_id": round_id,
        "panelist_count": len(PANEL_9),
        "output_path": str(output_path),
        "latency_seconds": round(latency, 3),
    }
    if smoke:
        # Real-GLM smoke summary — SC#2 acceptance evidence.
        print(
            "[smoke] round_id=%s panelists=%d latency=%.2fs output=%s"
            % (
                round_id,
                len(PANEL_9),
                latency,
                output_path,
            )
        )
    logger.info("run_screenplay_step3: complete summary=%s", summary)
    return summary


# --------------------------------------------------------------------------- #
# Synthesis pass — consolidate 9 panelist opinions into final Step 3 JSON
# --------------------------------------------------------------------------- #


async def _synthesize_step3_output(
    storykernel: dict[str, Any],
    panel_opinions: list[dict[str, Any]],
) -> str:
    """10th GLM call — screenplay expert consolidates opinions → Step 3 JSON.

    Builds a synthesis prompt with all 9 panelist opinions as context, asks
    the screenplay expert to emit final HOOK-09-valid Step 3 JSON. Returns
    the raw response content (a JSON string) for the caller to validate +
    parse.

    Token budget: ~22K for the round (9 panelist × ~2K + 1 synthesis × ~4K)
    — within the RESEARCH §3.2 estimate.
    """
    persona = (
        "You are the screenplay expert (编剧). Your job is to consolidate "
        "the round-table discussion into final Step 3 output — a JSON "
        "object matching the HOOK-09 emotion_curve marker contract.\n\n"
        "Output schema (Draft 2020-12):\n"
        "  - logline: string (>= 10 chars)\n"
        "  - scene_breakdown: array of {scene_id, beats[], emotion_curve[]}\n"
        "  - hooks: array of {timestamp_seconds, type, payload}; "
        "type in [cold_open|curiosity|shock|cliffhanger|paywall]\n"
        "  - payoffs: array of {setup_scene_id, payoff_scene_id, payload}\n"
        "  - cliffhangers: array of {scene_id, tension_level[0-1], "
        "cut_point_seconds}\n"
        "  - emotion_curve: array of {timestamp_seconds, arousal[0-1], "
        "valence[-1..1]}\n\n"
        "Output ONLY the JSON object — no markdown fences, no preamble."
    )

    opinions_block = "\n\n".join(
        f"## {p['agent_id']}\n{p['opinion']}" for p in panel_opinions
    )

    user_prompt = (
        f"# StoryKernel input\n```json\n{json.dumps(storykernel, ensure_ascii=False, indent=2)}\n```\n\n"
        f"# Round-table panelist opinions (9 experts)\n{opinions_block}\n\n"
        f"# Your task\nConsolidate the 9 panelist opinions into the final "
        f"screenplay Step 3 JSON. Honor every expert's contribution. Emit "
        f"the HOOK-09-valid JSON object only — no commentary."
    )

    response = agent.auxiliary_client.call_llm(
        task="round_table_opinion",
        provider="glm",  # MEMORY.md feedback-glm-5-2-only.md (RESEARCH Pitfall 6)
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,  # more deterministic than per-panelist (0.7)
        max_tokens=4096,
    )
    return response.choices[0].message.content


# --------------------------------------------------------------------------- #
# Schema validation
# --------------------------------------------------------------------------- #


def _validate_step3_schema(output: dict[str, Any], output_path: Path) -> None:
    """Validate ``output`` against HOOK-09 schema; write to ``output_path``.

    Raises ``jsonschema.ValidationError`` on failure. The caller decides
    whether to swallow + return an error dict (driver script) or propagate.
    """
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(output)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("run_screenplay_step3: HOOK-09-valid output written to %s", output_path)


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    """CLI entry. Wraps run_roundtable with argparse + error handling."""
    parser = argparse.ArgumentParser(
        description=(
            "9-agent screenplay Step 3 round-table driver "
            "(Phase 53 CREATIVE-01 vertical-slice smoke test)."
        )
    )
    parser.add_argument(
        "--storykernel",
        default="tests/fixtures/storykernel-sample.json",
        help="Path to StoryKernel Step 1 JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default="build/screenplay-step3-output.json",
        help="Where to write the HOOK-09-valid Step 3 JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Real-GLM smoke test — print latency + token-cost summary.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    storykernel_path = Path(args.storykernel).resolve()
    output_path = Path(args.output).resolve()

    try:
        summary = asyncio.run(
            run_roundtable(
                storykernel_path=storykernel_path,
                output_path=output_path,
                smoke=args.smoke,
            )
        )
    except RuntimeError as exc:
        # auxiliary_client.call_llm raises RuntimeError when no provider is
        # configured. Emit a clear operator-facing message — no traceback.
        # CONTEXT.md "Claude's Discretion" point 6 graceful-skip policy.
        if "provider" in str(exc).lower() or "api key" in str(exc).lower():
            print(
                "ERROR: GLM provider is not configured. Configure "
                "GLM_API_KEY (or ZAI_API_KEY) in ~/.hermes/.env and add "
                "'auxiliary.round_table_opinion.provider: glm' to "
                "cli-config.yaml. See cli-config.yaml.example for the "
                "full template.",
                file=sys.stderr,
            )
            sys.exit(2)
        # Some other RuntimeError — re-raise with traceback.
        raise
    if "error" in summary:
        print(f"ERROR: {summary['error']} — {summary.get('detail')}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: wrote HOOK-09-valid Step 3 JSON to {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
