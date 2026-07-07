#!/usr/bin/env python3
"""EVAL-01 fitness battery CLI entry point.

Usage::

    python scripts/run_fitness_battery.py \\
        --battery tests/v11-fitness-battery/scenarios \\
        --persona-sha256 <agent_persona_sha256>

Optional flags:
    --shadow       Run agent dispatch in shadow mode (live dispatch deferred
                   to Phase 56 VALIDATE per spec §8).
    --trend-path   Override the fitness_trend.jsonl path. Defaults to
                   ``$HERMES_HOME/eval/fitness_trend.jsonl``.

The CLI prints a summary table to stdout (including a
``mean_score = <float>`` line for grep-based verification) + appends a
single JSONL entry to ``fitness_trend.jsonl`` per spec §4.

Per MEMORY.md ``feedback-glm-5-2-only.md``: every LLM judge call goes
through ``agent.auxiliary_client.call_llm(task="fitness_judge",
provider="glm")``. Set ``GLM_API_KEY`` / ``ZAI_API_KEY`` in
``~/.hermes/.env`` before running against real GLM.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make repo-importable when invoked as a script (PEP 366 + sys.path bump)
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent.fitness_battery import (  # noqa: E402 — sys.path bump above
    BATTERY_VERSION,
    append_trend_entry,
    run_battery,
)

DEFAULT_BATTERY = _REPO_ROOT / "tests" / "v11-fitness-battery" / "scenarios"


def _resolve_default_trend_path() -> Path:
    """Locate ``$HERMES_HOME/eval/fitness_trend.jsonl``.

    Uses ``hermes_constants.get_hermes_home()`` per CLAUDE.md
    anti-pattern (never hard-code ``Path.home() / ".hermes"``).
    """
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:  # noqa: BLE001 — defensive fallback for minimal env
        from pathlib import Path as _P
        home = _P.home() / ".hermes"
    return home / "eval" / "fitness_trend.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the EVAL-01 fitness battery + emit a fitness_trend.jsonl entry.",
    )
    parser.add_argument(
        "--battery",
        default=str(DEFAULT_BATTERY),
        help=f"Directory of scenario YAMLs (default: {DEFAULT_BATTERY}).",
    )
    parser.add_argument(
        "--persona-sha256",
        required=True,
        help="Agent persona hash being probed (P1 drift-probe baseline).",
    )
    parser.add_argument(
        "--shadow",
        action="store_true",
        help="Shadow mode: agent dispatch returns stubs (live dispatch deferred to Phase 56 VALIDATE).",
    )
    parser.add_argument(
        "--trend-path",
        default=None,
        help="Override fitness_trend.jsonl path (default: $HERMES_HOME/eval/fitness_trend.jsonl).",
    )
    parser.add_argument(
        "--model-id",
        default="glm-5.2",
        help="Judge model id for the trend entry (default: glm-5.2).",
    )
    parser.add_argument(
        "--provider",
        default="zai",
        help="Judge provider id for the trend entry (default: zai).",
    )
    args = parser.parse_args(argv)

    battery_dir = Path(args.battery)
    if not battery_dir.is_dir():
        print(f"ERROR: battery dir not found: {battery_dir}", file=sys.stderr)
        return 2

    if args.shadow:
        print(
            "NOTE: shadow mode active — agent dispatch is stubbed. Live "
            "dispatch deferred to Phase 56 VALIDATE per spec §8.",
            file=sys.stderr,
        )

    summary = run_battery(
        battery_dir=battery_dir,
        persona_sha256=args.persona_sha256,
        model_id=args.model_id,
        provider=args.provider,
        shadow=args.shadow,
    )

    # Print a per-scenario breakdown + a greppable mean_score line.
    print(f"battery_version = {summary['battery_version']}")
    print(f"persona_sha256  = {summary['persona_sha256']}")
    print(f"scenarios_run   = {summary['scenarios_run']}")
    print(f"mean_score      = {summary['mean_score']:.4f}")
    print(f"model_id        = {summary['model_id']}")
    print(f"provider        = {summary['provider']}")
    print("--- per-prompt scores ---")
    for scenario_id, score in sorted(summary["per_prompt_scores"].items()):
        print(f"  {scenario_id:<48s} {score:.4f}")

    # Assemble + append the trend entry per spec §4 schema.
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "battery_version": summary["battery_version"],
        "mean_score": summary["mean_score"],
        "per_prompt_scores": summary["per_prompt_scores"],
        "persona_sha256": summary["persona_sha256"],
        "model_id": summary["model_id"],
        "provider": summary["provider"],
    }
    trend_path = Path(args.trend_path) if args.trend_path else _resolve_default_trend_path()
    append_trend_entry(entry, trend_path)
    print(f"--- appended trend entry to {trend_path} ---")
    # Also print the line the verification grep expects:
    print(f"mean_score = {summary['mean_score']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
