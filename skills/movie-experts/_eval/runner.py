"""MT-Bench position-swap LLM-as-judge harness for movie-experts skills.

Implements the position-bias-mitigation pattern from MT-Bench:
for every (prompt, condition-pair) comparison the judge sees two
answers in BOTH orderings (A,B) and (B,A). If the two orderings
disagree on a winner, the final verdict is "tie" — a position-bias
signal, not a genuine quality difference.

The harness also supports ablation over N>=2 conditions via
``run_ablation``, which enumerates all C(N,2) pairs.

Design constraints (from 00-03-PLAN.md):
- EVAL-03: judge temperature HARD-PINNED at 0.0 in every code path.
- EVAL-04: ablation supports N>=2 conditions with pairwise comparison.
- EVAL-08: zero new packages — uses only ``openai``, ``pyyaml``,
  ``jinja2`` (all already pinned in pyproject.toml).
- EVAL-09: does NOT register with Hermes tool registry.
- T-00-09: never logs ``OPENROUTER_API_KEY``.
- T-00-11: malformed judge output (no <decision> tag) defaults to "tie".
- CLAUDE.md PLW1514: every ``open()`` passes ``encoding="utf-8"``.

This module is OFFLINE DEVELOPER TOOLING. It is not imported by the
Hermes runtime and does not call ``registry.register(...)``.
"""
from __future__ import annotations

import argparse
import itertools
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Protocol

import yaml
from jinja2 import Template

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

DEFAULT_TAG = "eval-baseline-v1"
# EVAL-03 hard-pin: judge temperature is 0.0 in every code path. No
# other value is permitted anywhere in this module.
DEFAULT_TEMPERATURE = 0.0
SUPPORTED_DECISIONS = frozenset({"A", "B", "tie"})

# Regex is case-insensitive so <decision>a</decision> and
# <decision>TIE</decision> both parse. The capture group is the
# canonical decision token.
_DECISION_RE = re.compile(r"<decision>\s*(A|B|tie)\s*</decision>", re.IGNORECASE)

logger = logging.getLogger("eval.runner")

# Path to the Jinja2 judge prompt template, resolved relative to this
# module so the script works from any cwd.
_JUDGE_PROMPT_PATH = Path(__file__).resolve().parent / "judge_prompt.md"


# --------------------------------------------------------------------------- #
# Judge client protocol (duck-typed; real impl is openai.OpenAI)
# --------------------------------------------------------------------------- #


class JudgeClient(Protocol):
    """Structural type for the judge LLM client.

    Any object exposing ``chat.completions.create(model=..., temperature=...,
    messages=..., extra_body=...)`` satisfies this. The real implementation
    is ``openai.OpenAI``; tests pass a ``MockJudgeClient``.
    """

    @property
    def chat(self) -> Any:  # pragma: no cover - protocol body
        ...


# --------------------------------------------------------------------------- #
# Decision parsing (T-00-11 mitigation)
# --------------------------------------------------------------------------- #


def parse_judge_decision(raw_text: str) -> str:
    """Extract the judge's decision from a CoT response.

    Looks for ``<decision>A|B|tie</decision>`` (case-insensitive on both
    the tag and the value). Returns one of ``"A"``, ``"B"``, ``"tie"``.

    Fail-safe (T-00-11): if no decision tag is found, returns ``"tie"``.
    A missing tag is treated as position-bias / low-confidence rather
    than a hard error so the harness never crashes on a malformed judge
    response. The event is logged as a warning.
    """
    match = _DECISION_RE.search(raw_text)
    if match is None:
        logger.warning(
            "judge response had no <decision> tag; defaulting to 'tie'. "
            "raw_text preview: %s",
            raw_text[:120],
        )
        return "tie"
    token = match.group(1).lower()
    # Canonicalize: "a"->"A", "b"->"B", "tie"->"tie". Anything else
    # (shouldn't happen given the regex, but defense in depth) -> "tie".
    if token == "a":
        return "A"
    if token == "b":
        return "B"
    return "tie"


# --------------------------------------------------------------------------- #
# Message + kwargs construction (EVAL-03 hard-pin lives here)
# --------------------------------------------------------------------------- #


def _load_judge_prompt_template() -> str:
    """Load the Jinja2 judge prompt template from disk.

    Cached at module level after first load. Re-reads on each call would
    be wasteful for a Phase 0 skeleton, but the template source is small
    enough that even repeated reads are cheap.
    """
    return _JUDGE_PROMPT_PATH.read_text(encoding="utf-8")


def build_judge_messages(
    prompt: str,
    answer_a: str,
    answer_b: str,
    swap: bool,
) -> list[dict[str, str]]:
    """Build the OpenAI chat messages list for one judge call.

    ``swap=False`` -> A is presented first (position 1).
    ``swap=True``  -> B is presented first (position 1).

    The system message is the Jinja2-rendered ``judge_prompt.md``
    template. The user message contains the original prompt plus the
    two candidate answers in the requested order. Answers are labeled
    "Answer 1" and "Answer 2" so the judge never sees which condition
    produced which answer (blind evaluation).
    """
    system_text = Template(_load_judge_prompt_template()).render()

    first, second = (answer_b, answer_a) if swap else (answer_a, answer_b)
    user_text = (
        f"## Original prompt\n{prompt}\n\n"
        f"## Answer 1\n{first}\n\n"
        f"## Answer 2\n{second}\n\n"
        f"Evaluate the two answers above on the four dimensions in the "
        f"system prompt, then emit your final <decision>A|B|tie</decision>."
    )

    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def build_judge_kwargs(
    messages: list[dict[str, str]],
    model: str,
    *,
    swap: bool = False,
) -> dict[str, Any]:
    """Build the kwargs dict for ``client.chat.completions.create``.

    EVAL-03 hard-pin: ``temperature`` is ALWAYS ``0.0``. No caller can
    override it. The ``swap`` flag is passed through ``extra_body`` so
    the judge client (real or mock) can record which ordering it saw
    without polluting the OpenAI request schema.
    """
    return {
        "model": model,
        # Hard-pinned (EVAL-03). Do NOT make this configurable.
        "temperature": DEFAULT_TEMPERATURE,
        "messages": messages,
        "extra_body": {"swap": swap},
    }


def _call_judge(
    judge_client: JudgeClient,
    messages: list[dict[str, str]],
    model: str,
    *,
    swap: bool,
) -> str:
    """Invoke the judge client and return its raw response text.

    Normalises across the OpenAI SDK v1/v2 response shape (``model_dump()``
    vs raw dict) so the rest of the harness can treat the result as a dict.
    """
    kwargs = build_judge_kwargs(messages, model, swap=swap)
    # ``chat.completions.create`` is the OpenAI SDK entrypoint. Mock
    # clients expose ``chat_completions_create`` instead; accept both.
    if hasattr(judge_client, "chat") and hasattr(
        judge_client.chat, "completions"
    ):
        resp = judge_client.chat.completions.create(**kwargs)
    elif hasattr(judge_client, "chat_completions_create"):
        resp = judge_client.chat_completions_create(**kwargs)
    else:  # pragma: no cover - defensive
        raise TypeError(
            f"judge_client {type(judge_client).__name__} exposes neither "
            "chat.completions.create nor chat_completions_create"
        )

    # Normalise to dict.
    if hasattr(resp, "model_dump"):
        resp = resp.model_dump()
    elif hasattr(resp, "to_dict"):
        resp = resp.to_dict()

    return resp["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------- #
# Position-swap core
# --------------------------------------------------------------------------- #


def _final_verdict(ordering_ab: str, ordering_ba: str) -> str:
    """Collapse two orderings into one final verdict.

    Agreement on A -> ``A_wins``.
    Agreement on B -> ``B_wins``.
    Disagreement (incl. any tie in one ordering) -> ``tie``.
    Both tie -> ``tie``.
    """
    if ordering_ab == "A" and ordering_ba == "A":
        return "A_wins"
    if ordering_ab == "B" and ordering_ba == "B":
        return "B_wins"
    return "tie"


def run_position_swap(
    prompt: str,
    answer_a: str,
    answer_b: str,
    judge_client: JudgeClient,
    judge_model: str,
    *,
    prompt_id: str = "",
) -> dict[str, Any]:
    """Run one position-swap comparison.

    Calls the judge twice: once with A first (``swap=False``) and once
    with B first (``swap=True``). Parses both decisions and collapses
    them via :func:`_final_verdict`.

    Returns a verdict dict with keys:
      ``prompt_id``, ``ordering_ab``, ``ordering_ba``, ``final``.
    """
    msgs_ab = build_judge_messages(prompt, answer_a, answer_b, swap=False)
    raw_ab = _call_judge(judge_client, msgs_ab, judge_model, swap=False)
    ordering_ab = parse_judge_decision(raw_ab)

    msgs_ba = build_judge_messages(prompt, answer_a, answer_b, swap=True)
    raw_ba = _call_judge(judge_client, msgs_ba, judge_model, swap=True)
    ordering_ba = parse_judge_decision(raw_ba)

    return {
        "prompt_id": prompt_id,
        "ordering_ab": ordering_ab,
        "ordering_ba": ordering_ba,
        "final": _final_verdict(ordering_ab, ordering_ba),
    }


# --------------------------------------------------------------------------- #
# Ablation (EVAL-04: N>=2 conditions, pairwise)
# --------------------------------------------------------------------------- #


def run_ablation(
    conditions: dict[str, list[str]],
    prompts: list[dict[str, str]],
    judge_client: JudgeClient,
    judge_model: str,
) -> list[dict[str, Any]]:
    """Pairwise ablation over N>=2 conditions.

    ``conditions`` maps condition_label -> list of model answers, aligned
    positionally with ``prompts`` (i.e. ``conditions[c][i]`` is the
    answer that condition ``c`` produced for ``prompts[i]``).

    For every unordered pair ``(c_i, c_j)`` with ``i<j`` (alphabetical
    ordering on the labels for determinism), and for every prompt, runs
    :func:`run_position_swap` and records the verdict along with the
    pair and the judge model id.

    Returns a flat list of verdict dicts. For C conditions and P prompts,
    yields C*(C-1)/2 * P verdicts.
    """
    labels = sorted(conditions.keys())
    if len(labels) < 2:
        raise ValueError(
            f"run_ablation needs >=2 conditions, got {len(labels)}"
        )

    # Validate alignment.
    for label in labels:
        if len(conditions[label]) != len(prompts):
            raise ValueError(
                f"condition '{label}' has {len(conditions[label])} answers "
                f"but {len(prompts)} prompts were given"
            )

    verdicts: list[dict[str, Any]] = []
    for c_i, c_j in itertools.combinations(labels, 2):
        for idx, p in enumerate(prompts):
            v = run_position_swap(
                prompt=p["text"],
                answer_a=conditions[c_i][idx],
                answer_b=conditions[c_j][idx],
                judge_client=judge_client,
                judge_model=judge_model,
                prompt_id=p["id"],
            )
            v["pair"] = [c_i, c_j]
            v["judge"] = judge_model
            verdicts.append(v)
    return verdicts


# --------------------------------------------------------------------------- #
# Output formatting
# --------------------------------------------------------------------------- #


def format_results(
    verdicts: list[dict[str, Any]],
    *,
    judge_label: str = "",
) -> tuple[dict[str, Any], str]:
    """Format verdicts as (JSON-serializable dict, Markdown table).

    JSON shape::

        {"total_comparisons": int, "verdicts": [...]}

    Markdown: pipe table with header
    ``| prompt_id | pair | winner | judge |``.
    """
    json_out = {
        "total_comparisons": len(verdicts),
        "verdicts": verdicts,
    }

    lines = [
        "| prompt_id | pair | winner | judge |",
        "|-----------|------|--------|-------|",
    ]
    for v in verdicts:
        pair_str = " vs ".join(v.get("pair", []))
        winner = v.get("final", "")
        # Use the verdict's judge if present, else the override label.
        judge = v.get("judge", judge_label)
        lines.append(
            f"| {v.get('prompt_id', '')} | {pair_str} | {winner} | {judge} |"
        )
    md_out = "\n".join(lines) + "\n"
    return json_out, md_out


# --------------------------------------------------------------------------- #
# Config + client construction
# --------------------------------------------------------------------------- #


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file. Honors CLAUDE.md PLW1514 (encoding)."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompts(prompts_path: str | Path) -> list[dict[str, str]]:
    """Load demo prompts for an expert.

    Expects YAML schema::

        expert_id: <str>
        prompts:
          - id: <str>
            text: |
              <prompt body>

    Returns just the ``prompts`` list.
    """
    with open(prompts_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["prompts"]


def make_judge_client(config: dict[str, Any]) -> Any:
    """Construct an OpenAI client pointing at OpenRouter (or generic base).

    Reads ``OPENROUTER_API_KEY`` from the environment. Never logs the
    key (T-00-09). The key is passed directly to the OpenAI client
    constructor and not retained on this object.
    """
    from openai import OpenAI

    judge_cfg = config.get("judge", {})
    base_url = judge_cfg.get(
        "base_url",
        os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
    )
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        # Do NOT print the key. Surface a redacted hint.
        logger.warning(
            "OPENROUTER_API_KEY is not set; judge calls will fail. "
            "Set it in ~/.hermes/.env or your shell."
        )
    return OpenAI(base_url=base_url, api_key=api_key)


# --------------------------------------------------------------------------- #
# Dry-run stub client (for SC #3 — no API key required)
# --------------------------------------------------------------------------- #


class _StubJudgeClient:
    """Deterministic stub used by ``--dry-run``.

    Returns a canned CoT response containing ``<decision>A</decision>``
    when A is first (swap=False) and ``<decision>B</decision>`` when B
    is first (swap=True). This is the classic position-bias pattern and
    produces ``final="tie"`` for every comparison — exactly what we
    want to demonstrate the position-swap output shape without burning
    real API quota.

    Contract: ``chat.completions.create`` is a ``@staticmethod`` that
    matches the OpenAI SDK's call signature (``client.chat.completions.
    create(model=..., messages=..., ...)``). Each instance owns its own
    ``_Chat`` / ``_Completions`` objects so two stub instances do not
    share call state.
    """

    def __init__(self) -> None:
        # Per-instance chat object — two _StubJudgeClient instances do
        # not share state (WR-02). ``_Completions.create`` remains a
        # @staticmethod to match the OpenAI SDK's invocation contract
        # (``judge_client.chat.completions.create(**kwargs)``).
        self.chat = self._Chat()

    class _Chat:
        def __init__(self) -> None:
            self.completions = _StubJudgeClient._Completions()

    class _Completions:
        @staticmethod
        def create(**kwargs: Any) -> dict:
            swap = bool(kwargs.get("extra_body", {}).get("swap", False))
            decision = "B" if swap else "A"
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                f"<reasoning>stub decision for "
                                f"swap={swap}</reasoning>\n"
                                f"<decision>{decision}</decision>"
                            )
                        }
                    }
                ]
            }


def _stub_answers(prompts: list[dict[str, str]], conditions: list[str]) -> dict[str, list[str]]:
    """Generate deterministic stub answers for each condition.

    Each condition produces a unique canned string per prompt so the
    verdict output is non-trivial.
    """
    out: dict[str, list[str]] = {}
    for ci, cond in enumerate(conditions):
        out[cond] = [
            f"[stub:{cond}] answer for prompt '{p['id']}' (variant {ci})"
            for p in prompts
        ]
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "MT-Bench position-swap LLM-as-judge harness for "
            "movie-experts skills (EVAL-01/03/04/08/09)."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "config.yaml.example",
        help="Path to runner config YAML (default: config.yaml.example).",
    )
    parser.add_argument(
        "--expert",
        default="animator",
        help="expert_id whose prompts file to load (default: animator).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip real API calls; use a stub judge client (SC #3 fallback).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Write JSON report to this path.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=None,
        help="Write Markdown report to this path.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="[runner] %(levelname)s %(message)s",
    )

    # Load config + prompts.
    if not args.config.is_file():
        logger.error("config file not found: %s", args.config)
        return 2
    config = load_config(args.config)

    prompts_path = (
        Path(__file__).resolve().parent / "prompts" / f"{args.expert}_demo.yaml"
    )
    if not prompts_path.is_file():
        logger.error("prompts file not found: %s", prompts_path)
        return 2
    prompts = load_prompts(prompts_path)
    logger.info("loaded %d prompts for expert '%s'", len(prompts), args.expert)

    # Pick judge model + conditions from config.
    judge_cfg = config.get("judge", {})
    judges = judge_cfg.get("models", [])
    if not judges:
        logger.error("config declares no judge models")
        return 2
    judge_model = judges[0]
    conditions_labels = config.get("conditions", ["baseline", "candidate"])
    if len(conditions_labels) < 2:
        logger.error("config must declare >=2 conditions for ablation")
        return 2

    # Pick judge client.
    if args.dry_run:
        judge_client: Any = _StubJudgeClient()
        logger.info("dry-run: using stub judge client (no API calls)")
    else:
        judge_client = make_judge_client(config)

    # Generate per-condition answers. In dry-run, use stubs. In live
    # mode, the operator is expected to pre-populate these (Phase 0
    # skeleton: live mode is out of scope; Phase 6 wires real generation).
    if args.dry_run:
        conditions_map = _stub_answers(prompts, conditions_labels)
    else:
        # Phase 0 live mode: we still need answers. For the skeleton we
        # use stubs here too but make real judge calls — the judge call
        # is the expensive part and that's what OPENROUTER_API_KEY gates.
        # If the operator wants fully live answers, Phase 6 will replace
        # this branch with actual test-model invocation.
        conditions_map = _stub_answers(prompts, conditions_labels)

    # Run ablation.
    verdicts = run_ablation(
        conditions=conditions_map,
        prompts=prompts,
        judge_client=judge_client,
        judge_model=judge_model,
    )
    logger.info(
        "ablation produced %d verdicts (%d conditions x %d prompts)",
        len(verdicts),
        len(conditions_labels),
        len(prompts),
    )

    json_out, md_out = format_results(verdicts, judge_label=judge_model)

    # Write outputs.
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(json_out, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("wrote JSON report -> %s", args.output_json)
    if args.output_md is not None:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(md_out, encoding="utf-8")
        logger.info("wrote Markdown report -> %s", args.output_md)

    # Echo a short summary to stdout for shell pipelines.
    print(
        f"total_comparisons={json_out['total_comparisons']} "
        f"expert={args.expert} judge={judge_model} "
        f"dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
