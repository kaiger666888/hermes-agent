"""EVAL-01 fitness battery runner.

Loads frozen scenario YAMLs from ``tests/v11-fitness-battery/scenarios/``,
dispatches the agent per scenario, scores each output via an LLM judge
(GLM-only per MEMORY.md ``feedback-glm-5-2-only.md``), and emits a
longitudinal ``fitness_trend.jsonl`` entry per the schema in
``.planning/research/v11-poc-eval/fitness-battery-spec.md §4``.

Public API (re-exported by ``scripts/run_fitness_battery.py``):

    load_scenario(name, battery_dir=None) -> dict
    score_scenario(scenario, agent_output, *, judge_llm=None) -> float
    run_battery(battery_dir, *, judge_llm=None, persona_sha256, ...) -> dict
    append_trend_entry(entry, trend_path) -> None

Design invariants (cite, do not re-derive):
- T-54-01 (Tampering) mitigated: yaml.safe_load only.
- T-54-03 (DoS) mitigated: max_tokens clamp + timeout=30s, malformed
  judge response falls back to score=0.0 + warning log.
- GLM-only enforcement: every default-judge dispatch passes
  ``provider="glm"`` (test ``TestGlmOnly`` verifies).
- ``encoding="utf-8"`` on every text-mode ``open()`` (PLW1514).
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable

import yaml

logger = logging.getLogger(__name__)

BATTERY_VERSION = "v1-screenplay-baseline-real"
DEFAULT_BATTERY_DIR = Path(__file__).resolve().parents[1] / "tests" / "v11-fitness-battery" / "scenarios"
JUDGE_TIMEOUT_SECONDS = 30.0
JUDGE_MAX_TOKENS = 600

# Phase 60 EVAL-02: real-mode agent dispatch via auxiliary_client. Per
# CONTEXT.md decision #3, every dispatch hits the Phase 59 auxiliary pool
# (GLM_AUX_API_KEY_1..4) so gateway never contends for keys.
AGENT_DISPATCH_TIMEOUT_SECONDS = 60.0
AGENT_DISPATCH_MAX_TOKENS = 2048

# Ordered keys to try when extracting a user-message string from a scenario's
# ``input`` block. Different scenario dimensions use different shapes:
#   - screenplay/hook09:  input.storykernel (dict) → JSON-stringified
#   - persona-drift:      input.prompt (str)
#   - conflict-resolution: input.question (str) + mem_a/mem_b
# The fallback builds a canonical user message that captures every input key.
_USER_MESSAGE_KEYS = ("prompt", "user_message", "user", "question")


# --------------------------------------------------------------------------- #
# Default judge LLM dispatch (lazy import — keeps test patch surface small)
# --------------------------------------------------------------------------- #
def _call_llm(**kwargs: Any) -> Any:
    """Lazy proxy to ``agent.auxiliary_client.call_llm``.

    Tests ``monkeypatch.setattr(fitness_battery, "_call_llm", stub)``
    so no real GLM call is ever made in unit tests.
    """
    from agent.auxiliary_client import call_llm  # local import — circular-safe
    return call_llm(**kwargs)


def _default_judge_llm(**kwargs: Any) -> Any:
    """Default judge dispatcher — GLM-only."""
    return _call_llm(**kwargs)


# --------------------------------------------------------------------------- #
# Agent dispatch (screenplay / conflict / persona-drift)
# --------------------------------------------------------------------------- #
def _extract_user_message(scenario: dict) -> str:
    """Build a canonical user-message string from ``scenario["input"]``.

    Different scenario dimensions use different input shapes:
      - screenplay-step3-*: ``input.storykernel`` (dict)
      - hook09-emotion-curve-marker: ``input.storykernel`` (dict)
      - persona-drift-probe: ``input.prompt`` (str)
      - conflict-resolution-*: ``input.question`` + ``mem_a`` + ``mem_b``

    Strategy:
      1. If a single narrative key (``prompt`` / ``user_message`` / ``user``
         / ``question``) is present as a string, return that string.
      2. If a ``storykernel`` dict is present, JSON-stringify it.
      3. Fallback: JSON-stringify the entire input block. This preserves
         every input field so the dispatched agent / generic-LLM sees the
         complete scenario payload.
    """
    input_block = scenario.get("input") or {}
    if isinstance(input_block, dict):
        for key in _USER_MESSAGE_KEYS:
            value = input_block.get(key)
            if isinstance(value, str) and value.strip():
                return value
        if "storykernel" in input_block:
            return json.dumps(input_block, ensure_ascii=False, default=str)
    # Fallback: serialize the whole input block.
    return json.dumps(input_block, ensure_ascii=False, default=str)


def _load_persona_system_prompt(agent_name: str = "screenplay") -> str | None:
    """Load the ``persona:`` field from ``$HERMES_HOME/agents/<name>.agent.yaml``.

    Returns ``None`` if the file is missing or unparsable — the caller
    decides whether to proceed without a persona (generic-LLM mode never
    uses a persona anyway; persona_aligned mode falls back to an empty
    system prompt on load failure and logs a warning).
    """
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.warning(
            "could not resolve HERMES_HOME for persona load (%s); "
            "using empty persona",
            exc,
        )
        return None
    path = home / "agents" / f"{agent_name}.agent.yaml"
    if not path.is_file():
        logger.warning(
            "persona YAML not found at %s; persona_aligned dispatch "
            "will run without a system prompt",
            path,
        )
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("failed to read persona YAML %s: %s", path, exc)
        return None
    if isinstance(data, dict):
        persona = data.get("persona")
        if isinstance(persona, str) and persona.strip():
            return persona
    return None


def _dispatch_agent(
    scenario: dict,
    *,
    shadow: bool = False,
    baseline_mode: str | None = None,
) -> str:
    """Dispatch the agent on ``scenario["input"]``.

    Dispatch modes (mutually exclusive; ``baseline_mode`` takes precedence
    over ``shadow`` when both are set — operator-friendly):

      - ``baseline_mode=None`` (default):
          Phase 54 behavior preserved verbatim. If ``shadow=True``, return
          a fixed stub. Otherwise, route by scenario dimension:
          conflict-resolution → ``arbitrate_two_memories``; screenplay +
          persona-drift → v1 stub (live round-table dispatch is a Phase 56
          VALIDATE concern, NOT this plan's scope).

      - ``baseline_mode="persona_aligned"`` (Phase 60 EVAL-02 NEW):
          Load the screenplay agent persona from
          ``$HERMES_HOME/agents/screenplay.agent.yaml``, prepend it as a
          system message, and dispatch the user payload via
          ``auxiliary_client.call_llm`` (Phase 59 aux pool). Measures how
          the persona-equipped screenplay agent scores on the rubric.

      - ``baseline_mode="generic_llm"`` (Phase 60 EVAL-02 NEW):
          Dispatch the same user payload with NO system prompt. Measures
          how a generic GLM-5.2 without any persona scores on the same
          rubric. The discrimination delta is
          ``persona_aligned_mean - generic_llm_mean``.

    Args:
        scenario: Parsed scenario dict.
        shadow: Shadow-mode stub flag (Phase 54).
        baseline_mode: ``"persona_aligned"`` or ``"generic_llm"`` for
            Phase 60 EVAL-02 real-mode discrimination baseline. ``None``
            preserves Phase 54 behavior.

    Returns:
        Agent output as a string. For real-mode dispatch, this is the
        raw ``choices[0].message.content``. On dispatch failure, returns
        a JSON stub with an error marker so the battery can continue.

    Tests override this via ``monkeypatch.setattr(fitness_battery,
    "_dispatch_agent", stub)`` OR by patching ``fitness_battery._call_llm``
    for the real-mode branches.
    """
    scenario_id = scenario.get("id", "<unknown>")

    # ----- Phase 60 EVAL-02 real-mode dispatch paths -------------------- #
    if baseline_mode in ("persona_aligned", "generic_llm"):
        return _dispatch_real_mode(
            scenario,
            baseline_mode=baseline_mode,
            scenario_id=scenario_id,
        )

    # ----- Phase 54 behavior (shadow + dimension routing) --------------- #
    if shadow:
        logger.info(
            "fitness battery shadow mode: scenario=%s — returning stub "
            "(live dispatch deferred to Phase 56 VALIDATE per spec §8)",
            scenario_id,
        )
        return json.dumps({"shadow": True, "scenario_id": scenario_id})

    input_block = scenario.get("input") or {}
    # Conflict resolution dimension — has mem_a + mem_b keys.
    if {"mem_a", "mem_b"} <= set(input_block.keys()):
        try:
            from agent.memory_arbitration import arbitrate_two_memories
        except Exception as exc:  # noqa: BLE001 — module missing in minimal env
            logger.warning(
                "memory_arbitration unavailable (%s); falling back to stub "
                "for scenario=%s",
                exc,
                scenario_id,
            )
            return json.dumps({"resolution": "stub", "scenario_id": scenario_id})
        try:
            result = arbitrate_two_memories(
                memory_a=input_block["mem_a"],
                memory_b=input_block["mem_b"],
                panelist_a=input_block.get("panelist_a", "screenplay"),
                panelist_b=input_block.get("panelist_b", "theory_critic"),
                project_id=input_block.get("project_id", "v11-poc"),
                question=input_block.get("question", scenario.get("description", "")),
            )
        except Exception as exc:  # noqa: BLE001 — conflict dispatch failure must not crash battery
            logger.warning(
                "arbitrate_two_memories failed for scenario=%s: %s — stub returned",
                scenario_id,
                exc,
            )
            return json.dumps({"resolution": "stub-error", "scenario_id": scenario_id})
        return json.dumps(result, ensure_ascii=False)

    # Screenplay + persona drift — v1 stub (live round-table dispatch is
    # Phase 56 VALIDATE scope).
    logger.info(
        "fitness battery v1 stub dispatch: scenario=%s (live dispatch "
        "deferred to Phase 56 VALIDATE)",
        scenario_id,
    )
    return json.dumps({"stub": True, "scenario_id": scenario_id})


def _dispatch_real_mode(
    scenario: dict,
    *,
    baseline_mode: str,
    scenario_id: str,
) -> str:
    """Real-mode agent dispatch via ``auxiliary_client.call_llm``.

    Phase 60 EVAL-02. Both modes build the SAME user message (apples-to-
    apples comparison). The only difference is whether a persona system
    prompt is prepended.

    Args:
        scenario: Parsed scenario dict.
        baseline_mode: ``"persona_aligned"`` or ``"generic_llm"``.
        scenario_id: Pre-extracted scenario id for logging.

    Returns:
        ``choices[0].message.content`` string on success. On any
        exception, logs a warning + returns a JSON stub with
        ``{"real_mode_error": str(exc), "scenario_id": scenario_id}`` so
        the battery can score it (likely low) without crashing.
    """
    user_message = _extract_user_message(scenario)
    messages: list[dict] = []
    if baseline_mode == "persona_aligned":
        persona = _load_persona_system_prompt("screenplay")
        if persona:
            messages.append({"role": "system", "content": persona})
        else:
            logger.warning(
                "persona_aligned dispatch for scenario=%s running WITHOUT "
                "a persona (YAML load failed) — score will reflect "
                "persona-less behavior",
                scenario_id,
            )
    # generic_llm: no system message at all — by design.
    messages.append({"role": "user", "content": user_message})

    try:
        response = _call_llm(
            task="fitness_battery_agent",
            provider="glm",  # GLM-only — MEMORY.md feedback-glm-5-2-only.md
            messages=messages,
            temperature=0.0,
            max_tokens=AGENT_DISPATCH_MAX_TOKENS,
            timeout=AGENT_DISPATCH_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001 — dispatch failure must not crash battery
        logger.warning(
            "real-mode agent dispatch failed (baseline_mode=%s, "
            "scenario=%s): %s — returning error stub",
            baseline_mode,
            scenario_id,
            exc,
        )
        return json.dumps(
            {
                "real_mode_error": str(exc),
                "scenario_id": scenario_id,
                "baseline_mode": baseline_mode,
            },
            ensure_ascii=False,
        )
    content = _extract_content(response)
    if not content:
        logger.warning(
            "real-mode dispatch returned empty content (baseline_mode=%s, "
            "scenario=%s) — returning empty-marker stub",
            baseline_mode,
            scenario_id,
        )
        return json.dumps(
            {
                "real_mode_empty": True,
                "scenario_id": scenario_id,
                "baseline_mode": baseline_mode,
            },
            ensure_ascii=False,
        )
    return content


# --------------------------------------------------------------------------- #
# Scenario loading
# --------------------------------------------------------------------------- #
def load_scenario(name: str, battery_dir: Path | None = None) -> dict:
    """Load a scenario YAML by id (filename minus ``.yaml``).

    Args:
        name: Scenario id (matches filename stem).
        battery_dir: Directory containing ``<name>.yaml``. Defaults to
            ``tests/v11-fitness-battery/scenarios/``.

    Returns:
        Parsed YAML dict with 5 required keys.

    Raises:
        FileNotFoundError: If the YAML file does not exist. Message
            includes the explicit path tried.
    """
    directory = Path(battery_dir) if battery_dir else DEFAULT_BATTERY_DIR
    path = directory / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(
            f"fitness battery scenario not found: {path} (id={name!r})"
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)  # T-54-01 mitigation — safe_load only
    if not isinstance(data, dict):
        raise ValueError(f"scenario YAML did not parse to a dict: {path}")
    return data


def _list_scenarios(battery_dir: Path) -> list[Path]:
    """List scenario YAMLs in deterministic alphabetical order."""
    return sorted(Path(battery_dir).glob("*.yaml"))


# --------------------------------------------------------------------------- #
# LLM judge prompt + scoring
# --------------------------------------------------------------------------- #
def _build_judge_prompt(scenario: dict, agent_output: str) -> list[dict]:
    expected = scenario.get("expected_output", {}) or {}
    rubric = scenario.get("scoring_rubric", []) or []
    criteria_lines = "\n".join(
        f"  - criterion: {item.get('criterion', '<missing>')} (weight={item.get('weight', 0.0)})"
        for item in rubric
    )
    system = (
        "You are a strict screenplay + memory-arbitration fitness judge. "
        "Score the AGENT OUTPUT against the expected feature description + "
        "rubric criteria. Return ONLY a JSON object with this shape: "
        '{"scores": [{"criterion": str, "score": float in [0,1], "reason": str}], '
        '"overall": float in [0,1]}. No prose around the JSON.'
    )
    user = (
        f"SCENARIO: {scenario.get('id', '<unknown>')}\n\n"
        f"EXPECTED FEATURE:\n{expected.get('feature', '<unspecified>')}\n\n"
        f"RATIONALE:\n{expected.get('rationale', '<unspecified>')}\n\n"
        f"RUBRIC CRITERIA (score each 0.0-1.0):\n{criteria_lines}\n\n"
        f"AGENT OUTPUT:\n{agent_output}\n\n"
        "Return the JSON object now."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _parse_judge_scores(content: str, rubric: list[dict]) -> list[float]:
    """Extract a per-criterion score list aligned to ``rubric`` order.

    Falls back to the top-level ``overall`` field if per-criterion
    scores are missing. Falls back to ``0.0`` for every criterion on
    malformed responses (T-54-03 mitigation).
    """
    if not content:
        logger.warning("empty judge content — falling back to 0.0 scores")
        return [0.0] * len(rubric)
    # Strip markdown code fences (GLM/Claude often wrap JSON in ```json ... ```)
    stripped = content.strip()
    if stripped.startswith("```"):
        # Remove opening fence (with optional language tag like 'json')
        first_nl = stripped.find("\n")
        if first_nl > 0:
            stripped = stripped[first_nl + 1 :]
        # Remove closing fence
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
        stripped = stripped.strip()
    try:
        parsed = json.loads(stripped if stripped else content)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("malformed judge response (%s): %r", exc, content[:200])
        return [0.0] * len(rubric)

    if not isinstance(parsed, dict):
        logger.warning("judge response is not a dict: %r", parsed)
        return [0.0] * len(rubric)

    overall = parsed.get("overall")
    overall_fallback = (
        [_clamp01(float(overall))] * len(rubric)
        if isinstance(overall, (int, float))
        else [0.0] * len(rubric)
    )

    scores_list = parsed.get("scores")
    if isinstance(scores_list, list) and scores_list:
        # Map by criterion name → score
        by_name: dict[str, float] = {}
        for item in scores_list:
            if isinstance(item, dict) and "criterion" in item and "score" in item:
                try:
                    by_name[str(item["criterion"])] = float(item["score"])
                except (TypeError, ValueError):
                    continue
        out: list[float] = []
        matched = 0
        for entry in rubric:
            name = str(entry.get("criterion", ""))
            # exact match first, then prefix match (LLM may shorten)
            if name in by_name:
                out.append(_clamp01(by_name[name]))
                matched += 1
                continue
            match = next(
                (v for k, v in by_name.items() if name and (k.startswith(name) or name.startswith(k))),
                None,
            )
            if match is not None:
                out.append(_clamp01(match))
                matched += 1
            else:
                out.append(0.0)
        # If per-criterion names failed to match anything (judge used
        # different criterion names than the rubric), fall back to the
        # overall field. This is the common case for stub judges in unit
        # tests + for terse real judges.
        if matched == 0:
            return overall_fallback
        return out

    # No scores list — fall back to overall (or 0.0 if overall also missing).
    return overall_fallback


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def score_scenario(
    scenario: dict,
    agent_output: str,
    *,
    judge_llm: Callable[..., Any] | None = None,
) -> float:
    """Score an agent output against the scenario's rubric.

    Args:
        scenario: Parsed scenario dict (must contain ``expected_output``
            and ``scoring_rubric``).
        agent_output: The agent's output as a string.
        judge_llm: Optional callable matching
            ``agent.auxiliary_client.call_llm``'s signature. Defaults
            to a GLM dispatch via ``_default_judge_llm``.

    Returns:
        Weighted score in ``[0.0, 1.0]`` — sum of ``score[i] * weight[i]``
        clamped to ``[0,1]``.
    """
    rubric = scenario.get("scoring_rubric") or []
    if not rubric:
        logger.warning("scenario %r has empty scoring_rubric — score=0.0", scenario.get("id"))
        return 0.0

    dispatch = judge_llm or _default_judge_llm
    messages = _build_judge_prompt(scenario, agent_output)
    try:
        response = dispatch(
            task="fitness_judge",
            provider="glm",  # GLM-only — MEMORY.md feedback-glm-5-2-only.md
            messages=messages,
            temperature=0.0,
            max_tokens=JUDGE_MAX_TOKENS,  # T-54-03 mitigation
            timeout=JUDGE_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001 — judge dispatch failure must not crash battery
        logger.warning(
            "judge dispatch failed for scenario=%s: %s — score=0.0",
            scenario.get("id"),
            exc,
        )
        return 0.0

    content = _extract_content(response)
    per_criterion = _parse_judge_scores(content, rubric)
    weighted = sum(
        _clamp01(per_criterion[i]) * float(rubric[i].get("weight", 0.0))
        for i in range(len(rubric))
    )
    return _clamp01(weighted)


def _extract_content(response: Any) -> str:
    """Best-effort extraction of ``choices[0].message.content``.

    Accepts objects (OpenAI SDK shape), dicts, or strings. Returns
    empty string on any unexpected shape.
    """
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")
    if not choices:
        return ""
    first = choices[0]
    message = getattr(first, "message", None)
    if message is None and isinstance(first, dict):
        message = first.get("message")
    if message is None:
        return ""
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    return content or ""


# --------------------------------------------------------------------------- #
# Battery runner
# --------------------------------------------------------------------------- #
def run_battery(
    battery_dir: Path,
    *,
    judge_llm: Callable[..., Any] | None = None,
    persona_sha256: str,
    model_id: str = "glm-5.2",
    provider: str = "zai",
    shadow: bool = False,
    baseline_mode: str | None = None,
) -> dict:
    """Run every scenario in ``battery_dir`` + return a summary dict.

    Args:
        battery_dir: Directory of ``*.yaml`` scenario files.
        judge_llm: Optional LLM judge callable (defaults to GLM dispatch).
        persona_sha256: Agent persona hash (P1 drift-probe baseline).
        model_id: Judge model id (for the trend entry).
        provider: Judge provider id (for the trend entry).
        shadow: If True, dispatch agent in shadow mode (no live calls).
            Ignored when ``baseline_mode`` is set (real-mode dispatch
            paths are mutually exclusive with shadow).
        baseline_mode: Phase 60 EVAL-02 real-mode selector. ``None``
            preserves Phase 54 behavior. ``"persona_aligned"`` runs the
            screenplay agent with its persona system prompt.
            ``"generic_llm"`` runs GLM-5.2 with NO system prompt. Both
            modes dispatch sequentially via
            ``auxiliary_client.call_llm`` (Phase 59 aux pool).

    Returns:
        ``{
            "battery_version": str,
            "mean_score": float,
            "per_prompt_scores": dict[str, float],
            "scenarios_run": int,
            "persona_sha256": str,
            "model_id": str,
            "provider": str,
            "baseline_mode": str | None,  # Phase 60 EVAL-02
        }``
    """
    scenarios = _list_scenarios(Path(battery_dir))
    per_prompt_scores: dict[str, float] = {}
    for path in scenarios:
        with path.open("r", encoding="utf-8") as fh:
            scenario = yaml.safe_load(fh)
        if not isinstance(scenario, dict) or "id" not in scenario:
            logger.warning("skipping malformed scenario: %s", path)
            continue
        agent_output = _dispatch_agent(
            scenario,
            shadow=shadow,
            baseline_mode=baseline_mode,
        )
        score = score_scenario(scenario, agent_output, judge_llm=judge_llm)
        per_prompt_scores[str(scenario["id"])] = score

    if per_prompt_scores:
        mean_score = sum(per_prompt_scores.values()) / len(per_prompt_scores)
    else:
        mean_score = 0.0

    return {
        "battery_version": BATTERY_VERSION,
        "mean_score": _clamp01(mean_score),
        "per_prompt_scores": per_prompt_scores,
        "scenarios_run": len(per_prompt_scores),
        "persona_sha256": persona_sha256,
        "model_id": model_id,
        "provider": provider,
        "baseline_mode": baseline_mode,
    }


# --------------------------------------------------------------------------- #
# Trend entry persistence
# --------------------------------------------------------------------------- #
def append_trend_entry(entry: dict, trend_path: Path) -> None:
    """Append ``entry`` as a single JSONL line at ``trend_path``.

    Creates parent directories on first write. Uses ``encoding="utf-8"``
    per CLAUDE.md PLW1514 rule.
    """
    path = Path(trend_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.write("\n")
