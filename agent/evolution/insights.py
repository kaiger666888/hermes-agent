"""EVOL-01 — LLM aggregation of accumulated feedback into structured insights.

Operator-invoked only. NOT imported by Hermes runtime (run_agent.py,
agent/conversation_loop.py, agent/curator.py, cli.py, gateway/).

Pipeline (per RESEARCH §"Pattern 1"):
  1. Read FeedbackStore.query(skill_id=...) + .summary(skill_id=...)
  2. If empty → return [] (legitimate; distinct from parse failure)
  3. Truncate to most-recent 50 records
  4. Build messages = [system, user] using AGGREGATION_SYSTEM_PROMPT
  5. Call client.chat.completions.create(..., response_format=json_object)
     — retry once WITHOUT response_format if the SDK rejects it (Pitfall 1)
  6. Strip ```json fences from response
  7. json.loads — on JSONDecodeError raise AggregationError (NEVER silent empty)
  8. Pydantic-validate each insight; collect ValidationError per-bad-record
     and raise AggregationError listing all bad records (atomicity)
  9. Return list[InsightRecord]

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - Specific exceptions bound with ``as exc``; lazy %-logging (no f-strings
    in logger calls).
  - Never log OPENROUTER_API_KEY (T-31-02).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError, model_validator

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

DEFAULT_MODEL: str = "claude-sonnet-4-6"
"""Default LLM model for aggregation when neither --model nor
HERMES_EVOLUTION_MODEL is set."""

MAX_FEEDBACK_RECORDS_IN_PROMPT: int = 50
"""Truncation ceiling for feedback_details in the user prompt.
Most-recent records are kept; older ones are dropped (RESEARCH §"Pattern 1"
step 3). Keeps prompt token budget bounded for skills with 100+ records."""

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)
"""Matches leading/trailing markdown ```json fences for stripping."""


AGGREGATION_SYSTEM_PROMPT = """\
You are reviewing operator feedback for a movie-expert skill in the Hermes
short-film production suite. Your job is to identify COMMON THEMES across
multiple feedback records and propose ADDITIVE improvements.

CRITICAL RULES:
1. Group feedback by theme (e.g., "missing X method", "unclear Y section").
2. Cite specific feedback record IDs in each insight's evidence_chain.
3. Propose ADDITIVE-ONLY changes — NEVER delete or restructure existing
   content. New sections, new examples, new methods only.
4. Preserve expert_id and related_skills frontmatter byte-for-byte; do NOT
   propose changes to the YAML frontmatter block.
5. Output STRICT JSON with this schema:
   {
     "insights": [
       {
         "theme": "short description of the improvement theme",
         "evidence_chain": ["fb_id_1", "fb_id_2"],
         "rationale": "why this improvement matters, citing feedback",
         "proposed_addition": "the exact markdown content to append",
         "insert_after_marker": "a unique substring identifying where to insert"
       }
     ]
   }
6. Emit 1-5 insights. If feedback is sparse or contradictory, emit fewer.
7. NEVER propose changes to v4/v5 protected refs (snowflake-method.md,
   e-konte-format.md, scamper-variations.md, dreamina-cli-baseline.md,
   v86-pipeline-mapping.md) — only propose additions to SKILL.md or
   non-protected refs.
"""


# --------------------------------------------------------------------------- #
# Pydantic schema
# --------------------------------------------------------------------------- #


class InsightRecord(BaseModel):
    """A single aggregated improvement insight for one skill.

    Produced by :func:`aggregate_feedback` from LLM JSON output. Each
    record cites the feedback IDs that motivated it (evidence chain) and
    proposes a single additive markdown block to insert at a marker.

    Attributes:
        insight_id: Content-addressed ID ``f"{skill_id}_{ts_unix}_{sha256[:8]}"``.
        skill_id: The expert_id this insight applies to.
        theme: Short human-readable summary of the improvement theme.
        evidence_chain: Non-empty list of feedback record IDs motivating
            this insight. Pydantic enforces min_length=1.
        rationale: Why this improvement matters (citing feedback).
        proposed_addition: The exact markdown content to append.
        insert_after_marker: Substring identifying where to insert.
        ts: ISO-8601 UTC timestamp when this record was created.
    """

    insight_id: str
    skill_id: str
    theme: str = Field(min_length=1)
    evidence_chain: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    proposed_addition: str = Field(min_length=1)
    insert_after_marker: str = Field(min_length=1)
    ts: str

    @model_validator(mode="after")
    def _evidence_chain_defense_in_depth(self) -> "InsightRecord":
        # Defense-in-depth: min_length=1 already enforces non-empty list,
        # but also reject lists whose only element is the empty string.
        if not any(e.strip() for e in self.evidence_chain):
            raise ValueError("evidence_chain must contain at least one non-empty ID")
        return self


class AggregationError(Exception):
    """Raised when LLM aggregation fails (malformed JSON, bad records).

    NEVER silently returns an empty list on a parse failure — that would
    mask a real LLM-output problem. Empty lists are returned ONLY when the
    FeedbackStore legitimately has zero records for the skill (Pitfall 1).
    """


# --------------------------------------------------------------------------- #
# Client construction
# --------------------------------------------------------------------------- #


def make_aggregation_client(
    *, model_override: str | None = None
) -> "tuple[Any, str]":
    """Construct a sync OpenAI client for feedback aggregation (EVOL-01).

    Mirrors runner.make_judge_client (skills/movie-experts/_eval/runner.py:524).
    Fail-fast on missing OPENROUTER_API_KEY — surface the error at
    construction time, not deep in chat.completions.create.

    Args:
        model_override: If provided, use this model name. Otherwise read
            HERMES_EVOLUTION_MODEL env, falling back to DEFAULT_MODEL.

    Returns:
        ``(client, model_name)`` tuple.

    Raises:
        RuntimeError: if OPENROUTER_API_KEY (or OPENAI_API_KEY fallback)
            is absent or empty.

    The ``openai`` import is deferred until AFTER the key check so the
    RuntimeError surfaces cleanly in environments where openai isn't
    installed (the key check must never depend on the SDK being importable).
    """
    base_url = os.environ.get(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    api_key = os.environ.get("OPENROUTER_API_KEY", "") or os.environ.get(
        "OPENAI_API_KEY", ""
    )
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Set it in ~/.hermes/.env "
            "or your shell, or pass --dry-run for offline testing."
        )
    from openai import OpenAI

    client: Any = OpenAI(base_url=base_url, api_key=api_key)
    model = model_override or os.environ.get(
        "HERMES_EVOLUTION_MODEL", DEFAULT_MODEL
    )
    return client, model


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #


def build_aggregation_user_prompt(
    *,
    skill_id: str,
    feedback_summary: dict,
    feedback_details: list[dict],
) -> str:
    """Build the user message with feedback context for the LLM.

    Truncates ``feedback_details`` to the most-recent
    :data:`MAX_FEEDBACK_RECORDS_IN_PROMPT` records to bound the prompt
    token budget. The caller is expected to pass records in most-recent-
    first order.

    Uses ``ensure_ascii=False`` so CN content in corrections round-trips
    cleanly (matches Phase 28/29 convention).
    """
    truncated = list(feedback_details)[:MAX_FEEDBACK_RECORDS_IN_PROMPT]
    return (
        f"Skill under review: {skill_id}\n\n"
        f"Feedback summary (counts by verdict):\n"
        f"{json.dumps(feedback_summary, indent=2, ensure_ascii=False)}\n\n"
        f"Feedback details (most recent first, max {MAX_FEEDBACK_RECORDS_IN_PROMPT}):\n"
        f"{json.dumps(truncated, indent=2, ensure_ascii=False)}\n\n"
        f"Identify improvement themes and propose additive changes."
    )


# --------------------------------------------------------------------------- #
# Core aggregation
# --------------------------------------------------------------------------- #


def _strip_fences(text: str) -> str:
    """Strip ```json ... ``` markdown fences from LLM output."""
    return _FENCE_RE.sub("", text)


def _compute_insight_id(*, skill_id: str, theme: str, rationale: str) -> str:
    """Content-addressed insight_id per CONTEXT.md Claude's Discretion."""
    ts_unix = int(datetime.now(timezone.utc).timestamp())
    digest = hashlib.sha256(
        f"{theme}|{rationale}".encode("utf-8")
    ).hexdigest()[:8]
    return f"{skill_id}_{ts_unix}_{digest}"


def aggregate_feedback(
    *,
    skill_id: str,
    store: Any,
    client: Any,
    model: str,
) -> list[InsightRecord]:
    """Aggregate feedback for a skill into structured insights (EVOL-01).

    Args:
        skill_id: Target expert_id.
        store: FeedbackStore (or stub) with .query(skill_id=...) and
            .summary(skill_id=...) methods.
        client: OpenAI-shaped client with .chat.completions.create(...).
        model: Model name to pass to client.

    Returns:
        list of :class:`InsightRecord`. Empty list ONLY when the store
        has zero records for the skill (legitimate "no signal").

    Raises:
        AggregationError: on malformed LLM JSON output, missing
            ``insights`` key, non-list ``insights``, or any Pydantic
            ValidationError on individual records (atomic — all bad
            records are listed in the error message).
    """
    records = store.query(skill_id=skill_id)
    if not records:
        logger.info("no feedback for skill %s — returning empty insights", skill_id)
        return []

    summary = store.summary(skill_id=skill_id)
    # CR-02: store.query() is typed list[FeedbackRecord] (Pydantic objects),
    # but build_aggregation_user_prompt calls json.dumps(feedback_details)
    # which raises TypeError on Pydantic models. Convert to dicts first,
    # and attach record_id (computed via store._make_record_id) so the
    # LLM can cite the same IDs the operator sees in feedback.jsonl.
    # Tolerate pre-converted dicts (some test stubs pass dicts directly).
    make_record_id = getattr(store, "_make_record_id", None)
    records_as_dicts: list[dict] = []
    for r in records:
        if isinstance(r, dict):
            d = dict(r)
        else:
            d = r.model_dump(mode="json")
        if make_record_id is not None and "record_id" not in d:
            try:
                d["record_id"] = make_record_id(r)
            except Exception as exc:
                # Defensive: don't crash aggregation if record_id computation
                # fails for one record — log and continue.
                logger.warning(
                    "record_id computation failed for a feedback record: %s",
                    exc,
                )
        records_as_dicts.append(d)
    user_prompt = build_aggregation_user_prompt(
        skill_id=skill_id,
        feedback_summary=summary,
        feedback_details=records_as_dicts,
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": AGGREGATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # Step 5: try with response_format=json_object; on SDK error retry once
    # without it (Pitfall 1 mitigation per RESEARCH A2).
    content: str | None = None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
    except Exception as exc:
        # Could be SDK rejection of response_format or transport error.
        # Retry once WITHOUT response_format. If THIS also fails, let it
        # propagate (operator can re-run).
        logger.warning(
            "aggregation LLM call with response_format failed (%s); "
            "retrying without response_format",
            exc,
        )
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        content = resp.choices[0].message.content

    if content is None:
        raise AggregationError("LLM returned None content")

    # Step 6: strip markdown fences.
    stripped = _strip_fences(content)

    # Step 7: parse JSON. DEBUG-only raw logging (may contain feedback
    # snippets — T-31-02 data protection).
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        logger.debug("malformed LLM JSON (raw below): %s", stripped)
        raise AggregationError(
            f"LLM returned malformed JSON: {exc}"
        ) from exc

    # Step 8: validate payload structure.
    if not isinstance(payload, dict):
        raise AggregationError(
            f"LLM JSON top-level must be an object, got {type(payload).__name__}"
        )
    raw_insights = payload.get("insights")
    if raw_insights is None:
        raise AggregationError("LLM JSON missing 'insights' key")
    if not isinstance(raw_insights, list):
        raise AggregationError(
            f"'insights' must be a list, got {type(raw_insights).__name__}"
        )

    # Step 9: Pydantic-validate each record. Collect ALL errors (atomic).
    ts = datetime.now(timezone.utc).isoformat()
    results: list[InsightRecord] = []
    errors: list[str] = []
    for i, raw in enumerate(raw_insights):
        if not isinstance(raw, dict):
            errors.append(f"insight[{i}] not an object: {type(raw).__name__}")
            continue
        theme = str(raw.get("theme", ""))
        rationale = str(raw.get("rationale", ""))
        try:
            rec = InsightRecord(
                insight_id=_compute_insight_id(
                    skill_id=skill_id, theme=theme, rationale=rationale
                ),
                skill_id=skill_id,
                theme=theme,
                evidence_chain=list(raw.get("evidence_chain", [])),
                rationale=rationale,
                proposed_addition=str(raw.get("proposed_addition", "")),
                insert_after_marker=str(raw.get("insert_after_marker", "")),
                ts=ts,
            )
            results.append(rec)
        except ValidationError as exc:
            errors.append(f"insight[{i}] theme={theme!r}: {exc}")

    if errors:
        raise AggregationError(
            f"{len(errors)} insight(s) failed validation: " + "; ".join(errors)
        )

    # Step 10: return.
    logger.info(
        "aggregated %d insight(s) for skill %s from %d feedback record(s)",
        len(results), skill_id, len(records),
    )
    return results
