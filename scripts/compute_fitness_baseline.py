#!/usr/bin/env python3
"""Phase 60 EVAL-02 — dual-mode fitness baseline orchestrator.

Runs the v11.0 fitness battery TWICE in real-mode (no ``--shadow``):
  1. ``persona_aligned`` — the screenplay agent with its persona system
     prompt loaded from ``$HERMES_HOME/agents/screenplay.agent.yaml``.
  2. ``generic_llm`` — GLM-5.2 with NO system prompt (raw user message).

Computes the discrimination delta + writes a structured JSON summary.
The operator runs this ONCE to produce the baseline numbers that the
Task 3 baseline doc (``fitness-battery-baseline.md``) reports.

Per CONTEXT.md decisions:
  - #3 — both runs go through the Phase 59 auxiliary pool
    (``GLM_AUX_API_KEY_1..4``); zero main gateway pool consumption.
  - #4 — delta >= 0.3 = meaningful discrimination (persona-aligned
    expected >= 0.7 vs generic 0.4-0.5).
  - #5 — token budget ~400K (~0.20 CNY at glm-5.2 pricing).

Per MEMORY.md ``feedback-glm-5-2-only.md`` + ``feedback-glm-overload-
reduce-concurrency.md``:
  - GLM-only; every dispatch passes provider="glm".
  - Sequential execution (global_concurrency==1). The two modes run
    back-to-back; the Phase 58 RPM throttle (30/task) paces them.

Usage::

    python scripts/compute_fitness_baseline.py \\
        --battery tests/v11-fitness-battery/scenarios \\
        --out /tmp/fitness-baseline-phase60.json

Optional flags:
    --persona-sha256  Override auto-computed persona hash.
    --skip-generic    Run only persona-aligned (debugging).
    --model-id        GLM model id (default: glm-5.2; locked).
    --provider        GLM provider id (default: zai; locked).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make repo-importable when invoked as a script (PEP 366 + sys.path bump).
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent.fitness_battery import (  # noqa: E402 — sys.path bump above
    append_trend_entry,
    run_battery,
)

DEFAULT_BATTERY = _REPO_ROOT / "tests" / "v11-fitness-battery" / "scenarios"

# CONTEXT.md decision #4 — discrimination threshold.
DISCRIMINATION_DELTA_THRESHOLD = 0.3

# CONTEXT.md decision #5 — token cost estimate (upper bound).
TOKEN_BUDGET_ESTIMATE = 400_000
GLM_PRICE_PER_1K_TOKENS_CNY = 0.0005  # glm-5.2 approximate blended pricing
TOKEN_COST_ESTIMATE_CNY = (TOKEN_BUDGET_ESTIMATE / 1000.0) * GLM_PRICE_PER_1K_TOKENS_CNY


def _resolve_default_trend_path() -> Path:
    """Locate ``$HERMES_HOME/eval/fitness_trend.jsonl``.

    Uses ``hermes_constants.get_hermes_home()`` per CLAUDE.md anti-pattern
    (never hard-code ``Path.home() / ".hermes"``).
    """
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:  # noqa: BLE001 — defensive fallback for minimal env
        home = Path.home() / ".hermes"
    return home / "eval" / "fitness_trend.jsonl"


def _compute_persona_sha256(agent_name: str = "screenplay") -> str:
    """SHA-256 of the ``persona:`` block in ``<agent_name>.agent.yaml``.

    Used to (a) identify the persona under test in ``fitness_trend.jsonl``
    and (b) detect drift between runs (a curator edit to the persona YAML
    changes the hash, surfacing in the trend line).

    Falls back to ``"unknown-persona"`` if the YAML is unreadable. The
    operator can override via ``--persona-sha256`` for explicit pinning.
    """
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:  # noqa: BLE001 — defensive
        home = Path.home() / ".hermes"
    yaml_path = home / "agents" / f"{agent_name}.agent.yaml"
    if not yaml_path.is_file():
        return "unknown-persona"
    try:
        import yaml
        with yaml_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return "unknown-persona"
    persona_block = ""
    if isinstance(data, dict):
        persona = data.get("persona")
        if isinstance(persona, str):
            persona_block = persona
        else:
            # Fallback: hash the whole YAML content if no persona field.
            persona_block = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(persona_block.encode("utf-8")).hexdigest()


def _format_per_scenario(scores: dict[str, float]) -> str:
    """Pretty-print a per-scenario score dict for stdout."""
    if not scores:
        return "{}"
    lines = []
    for scenario_id in sorted(scores.keys()):
        lines.append(f"    {scenario_id}: {scores[scenario_id]:.4f}")
    return "\n".join(lines)


def _run_one_mode(
    *,
    battery_dir: Path,
    baseline_mode: str,
    persona_sha256: str,
    model_id: str,
    provider: str,
    trend_path: Path,
) -> dict:
    """Run one battery pass + append its trend entry.

    Returns the ``run_battery`` summary dict. The appended trend entry
    carries a new ``"mode"`` field so downstream analysis can distinguish
    ``persona_aligned`` vs ``generic_llm`` rows.
    """
    print(
        f"\n--- running battery in baseline_mode={baseline_mode} ---",
        file=sys.stderr,
    )
    summary = run_battery(
        battery_dir=battery_dir,
        persona_sha256=persona_sha256,
        model_id=model_id,
        provider=provider,
        baseline_mode=baseline_mode,
    )
    # Build + append the trend entry. The "mode" field distinguishes
    # real-mode runs from shadow stubs in the longitudinal log.
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "battery_version": summary["battery_version"],
        "mean_score": summary["mean_score"],
        "per_prompt_scores": summary["per_prompt_scores"],
        "persona_sha256": summary["persona_sha256"],
        "model_id": summary["model_id"],
        "provider": summary["provider"],
        "mode": baseline_mode,  # Phase 60 EVAL-02 marker
    }
    append_trend_entry(entry, trend_path)
    print(
        f"--- appended {baseline_mode} trend entry to {trend_path} ---",
        file=sys.stderr,
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 60 EVAL-02: run persona-aligned + generic-LLM fitness "
            "batteries in real-mode, compute discrimination delta."
        ),
    )
    parser.add_argument(
        "--battery",
        default=str(DEFAULT_BATTERY),
        help=f"Directory of scenario YAMLs (default: {DEFAULT_BATTERY}).",
    )
    parser.add_argument(
        "--persona-sha256",
        default=None,
        help=(
            "Agent persona hash being probed. Auto-computed from "
            "$HERMES_HOME/agents/screenplay.agent.yaml if omitted."
        ),
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output JSON path (will be overwritten if exists).",
    )
    parser.add_argument(
        "--model-id",
        default="glm-5.2",
        help="Model id for trend entries (default: glm-5.2; MEMORY.md locked).",
    )
    parser.add_argument(
        "--provider",
        default="zai",
        help="Provider id for trend entries (default: zai; MEMORY.md locked).",
    )
    parser.add_argument(
        "--skip-generic",
        action="store_true",
        help="Skip the generic-LLM battery (debugging; delta not computed).",
    )
    parser.add_argument(
        "--trend-path",
        default=None,
        help=(
            "Override fitness_trend.jsonl path (default: "
            "$HERMES_HOME/eval/fitness_trend.jsonl)."
        ),
    )
    args = parser.parse_args(argv)

    battery_dir = Path(args.battery)
    if not battery_dir.is_dir():
        print(f"ERROR: battery dir not found: {battery_dir}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Resolve persona hash — explicit override wins; else auto-compute.
    if args.persona_sha256:
        persona_sha256 = args.persona_sha256
    else:
        persona_sha256 = _compute_persona_sha256("screenplay")
    print(f"persona_sha256 = {persona_sha256}", file=sys.stderr)

    trend_path = (
        Path(args.trend_path) if args.trend_path else _resolve_default_trend_path()
    )

    # ---- Run persona-aligned mode ---------------------------------------- #
    summary_persona = _run_one_mode(
        battery_dir=battery_dir,
        baseline_mode="persona_aligned",
        persona_sha256=persona_sha256,
        model_id=args.model_id,
        provider=args.provider,
        trend_path=trend_path,
    )

    # ---- Run generic-LLM mode (unless --skip-generic) -------------------- #
    summary_generic: dict[str, Any] | None = None
    delta: float | None = None
    verdict: str | None = None
    if not args.skip_generic:
        summary_generic = _run_one_mode(
            battery_dir=battery_dir,
            baseline_mode="generic_llm",
            # Generic-LLM baseline uses a stable identifier so trend rows
            # are filterable. Reuse the screenplay persona_sha256 in the
            # trend entry's "persona_sha256" field (machine-readable), but
            # the "mode" field marks it as generic_llm.
            persona_sha256="generic-llm-baseline",
            model_id=args.model_id,
            provider=args.provider,
            trend_path=trend_path,
        )
        delta = summary_persona["mean_score"] - summary_generic["mean_score"]
        verdict = (
            "meaningful"
            if delta >= DISCRIMINATION_DELTA_THRESHOLD
            else "not_meaningful"
        )

    # ---- Stdout summary (machine-parseable) ------------------------------ #
    print()
    print("=" * 60)
    print("Phase 60 EVAL-02 — Fitness Battery Baseline Summary")
    print("=" * 60)
    print(
        f"persona_aligned: mean={summary_persona['mean_score']:.4f}\n"
        f"    per-scenario:\n{_format_per_scenario(summary_persona['per_prompt_scores'])}"
    )
    if summary_generic is not None:
        print(
            f"\ngeneric_llm:     mean={summary_generic['mean_score']:.4f}\n"
            f"    per-scenario:\n{_format_per_scenario(summary_generic['per_prompt_scores'])}"
        )
        assert delta is not None
        print(f"\ndelta:           {delta:+.4f}")
        print(
            f"verdict:         {verdict}   "
            f"(threshold={DISCRIMINATION_DELTA_THRESHOLD:.2f} per CONTEXT.md decision #4)"
        )
    else:
        print("\ngeneric_llm:     SKIPPED (--skip-generic)")
        print("delta:           N/A")
        print("verdict:         N/A")
    print(f"\ntoken budget:    ~{TOKEN_BUDGET_ESTIMATE:,} tokens "
          f"(CONTEXT.md decision #5)")
    print(f"cost estimate:   ~{TOKEN_COST_ESTIMATE_CNY:.4f} CNY at glm-5.2 pricing")
    print(f"trend log:       {trend_path}")
    print(f"summary JSON:    {out_path}")
    print("=" * 60)

    # ---- Write JSON summary ---------------------------------------------- #
    payload: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": "60-eval-02",
        "battery_version": summary_persona["battery_version"],
        "persona_aligned": summary_persona,
        "generic_llm": summary_generic,
        "delta": delta,
        "verdict": verdict,
        "discrimination_threshold": DISCRIMINATION_DELTA_THRESHOLD,
        "token_budget_estimate": TOKEN_BUDGET_ESTIMATE,
        "token_cost_estimate_cny": TOKEN_COST_ESTIMATE_CNY,
        "trend_path": str(trend_path),
    }
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\nwrote JSON summary to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
