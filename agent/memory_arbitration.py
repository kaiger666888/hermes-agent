"""Per-agent memory arbitration layer (Phase 53 CREATIVE-02).

This module implements the 5-mechanism conflict arbitration runtime per
``02-ROUND-TABLE-PROTOCOL.md §3``:

1. **Memory annotation enrichment** — ``memory_retrieve_scoped`` routes
   to the mem0 backend (lazy import, graceful ``unavailable`` fallback).
2. **Comparator LLM pass** — ``arbitrate_two_memories`` formats the
   verbatim §3.2 ``COMPARATOR_PROMPT_TEMPLATE`` and dispatches to
   ``auxiliary_client.call_llm`` (provider=``glm``).
3. **Scope precedence** — the prompt instructs the LLM; the Python
   tie-break layer applies deterministic scope-aware rules only at the
   tie case.
4. **Confidence-weighted voting** — ``apply_tie_break`` forces
   ``deferred-to-operator`` when same-scope Δconfidence < 0.05.
5. **Conflict log** — ``append_conflict_record`` writes one
   fsync'd JSONL line per conflict for curator review.

Phase 52 contract preserved verbatim
------------------------------------
- ``_UNSET`` sentinel, ``_SCOPED_AGENT_ID`` ``ContextVar``, plus
  ``set_scoped_agent_id`` / ``get_scoped_agent_id`` are unchanged.

Phase 52 stub contract REPLACED in Phase 53
-------------------------------------------
- ``memory_retrieve_scoped`` no longer returns
  ``{"status": "phase53_not_implemented", "hits": []}`` — it now
  routes to mem0 (or returns ``{"status": "unavailable", ...}`` when
  the backend is not configured). Per CONTEXT.md decision #3.
- ``memory_submit_record`` similarly replaced.

Design sources (cite, do not re-derive)
---------------------------------------
- ``02-ROUND-TABLE-PROTOCOL.md §3.0-§3.5`` — 5-mechanism contract
- ``02-ROUND-TABLE-PROTOCOL.md §3.2 lines 627-663`` — comparator prompt verbatim
- ``53-CONTEXT.md`` decision #2 (full 5-mechanism) + decision #5 (path convention)
- ``MEMORY.md::feedback-glm-5-2-only.md`` — explicit ``provider="glm"``
- ``gateway/session_context.py:39-83`` — canonical ``ContextVar`` pattern
"""

from __future__ import annotations

import json
import logging
import os
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# _scoped_agent_id contextvars primitive — Phase 52 contract, UNCHANGED
# --------------------------------------------------------------------------- #
#
# Mirror of the canonical pattern in ``gateway/session_context.py:39-62``.
# Uses an ``_UNSET`` sentinel (rather than ``default=None``) so that
# ``get_scoped_agent_id()`` can distinguish "explicitly set to None" from
# "never set" if debugging ever needs that distinction. (Currently both
# states return None from the public getter — explicit None means "clear
# the scope", unset means "no agent context active".)


_UNSET: Any = object()
_SCOPED_AGENT_ID: ContextVar = ContextVar(
    "HERMES_SCOPED_AGENT_ID",
    default=_UNSET,
)


def set_scoped_agent_id(agent_id: str | None) -> None:
    """Set the current asyncio task's scoped agent_id for memory routing.

    Called by the round-table executor before delegating to a
    panelist's memory retrieval / record submission so the routing layer
    knows which agent's namespace to consult.

    Pass ``None`` to clear the scope (e.g. when leaving a panelist's
    context). The scoped value is local to the current asyncio task and
    does NOT leak across ``asyncio.create_task`` boundaries.
    """
    _SCOPED_AGENT_ID.set(agent_id)


def get_scoped_agent_id() -> str | None:
    """Read the current asyncio task's scoped agent_id.

    Returns ``None`` in three cases:
    - scope never set (ContextVar still at ``_UNSET`` sentinel)
    - scope explicitly cleared via ``set_scoped_agent_id(None)``
    - scope set to a falsy value by buggy caller (defensive)
    """
    val = _SCOPED_AGENT_ID.get()
    if val is _UNSET or val is None:
        return None
    return str(val)


# --------------------------------------------------------------------------- #
# Comparator LLM prompt template (§3.2 verbatim, lines 627-663)
# --------------------------------------------------------------------------- #
#
# The template is a Python ``str.format()`` template. Placeholders use
# single braces ``{name}`` for the 16 substitution fields below; the
# JSON example block uses doubled braces ``{{`` / ``}}`` so it survives
# ``str.format()`` verbatim. Substrings marked verbatim by Test 1:
#   - "You are arbitrating a memory conflict in a Hermes round table."
#   - "Apply scope precedence: session > project > global"
#   - "confidence within 0.05"
#   - "evidence_operator_ids"
#   - "≥2 distinct operators" (Unicode U+2265, NOT ASCII >= — CR-04)
#   - the 5-value resolution enum line

COMPARATOR_PROMPT_TEMPLATE: str = """You are arbitrating a memory conflict in a Hermes round table.
Project context: {project_id}
Question under debate: {question}

Memory A (cited by panelist {panelistA}):
- content: {memoryA_content}
- scope: {memoryA_scope} (global | project | session)
- confidence: {memoryA_confidence} (0.0-1.0)
- evidence_chain length: {memoryA_evidence_len}
- evidence_operator_ids: {memoryA_operator_ids}

Memory B (cited by panelist {panelistB}):
- content: {memoryB_content}
- scope: {memoryB_scope}
- confidence: {memoryB_confidence}
- evidence_chain length: {memoryB_evidence_len}
- evidence_operator_ids: {memoryB_operator_ids}

Apply scope precedence: session > project > global
  (a session-scoped memory overrides global for THIS session;
   a project-scoped memory overrides global for THIS project).

Apply confidence-weighting: at the same scope level, higher confidence wins.
  If both memories are at the same scope level AND confidence within 0.05 of
  each other, defer to operator (human review).

Apply evidence diversity check: prefer memory with more diverse
  evidence_operator_ids (≥2 distinct operators per Phase 45 §3.7).

Output JSON:
{{
  "resolution": "A-wins" | "B-wins" | "both-kept" | "both-quarantined" | "deferred-to-operator",
  "rationale": "<=200 chars human-readable",
  "confidence": 0.0-1.0
}}
"""


# --------------------------------------------------------------------------- #
# Default comparator LLM dispatcher (GLM-only per MEMORY.md)
# --------------------------------------------------------------------------- #


def _default_comparator_llm(*, messages: list, **kwargs: Any) -> Any:
    """Default LLM dispatcher for the comparator pass.

    Routes through ``agent.auxiliary_client.call_llm`` with explicit
    ``provider="glm"`` per ``MEMORY.md::feedback-glm-5-2-only.md``
    (never let the auto-chain pick OpenRouter — RESEARCH Pitfall 6).
    """
    from agent.auxiliary_client import call_llm  # lazy import; avoids circulars
    return call_llm(
        task="memory_comparator",
        provider="glm",
        messages=messages,
        temperature=0.0,
        max_tokens=200,
    )


def _format_operator_ids(ids: Any) -> str:
    """Render ``evidence_operator_ids`` for prompt injection."""
    if not ids:
        return "[]"
    if isinstance(ids, (list, tuple)):
        return "[" + ", ".join(str(x) for x in ids) + "]"
    return str(ids)


def _build_comparator_prompt(
    memory_a: dict[str, Any],
    memory_b: dict[str, Any],
    panelist_a: str,
    panelist_b: str,
    project_id: str,
    question: str,
) -> str:
    """Format ``COMPARATOR_PROMPT_TEMPLATE`` with the 16 substitution fields."""
    return COMPARATOR_PROMPT_TEMPLATE.format(
        project_id=project_id,
        question=question,
        panelistA=panelist_a,
        panelistB=panelist_b,
        memoryA_content=memory_a.get("content", ""),
        memoryA_scope=memory_a.get("scope", "global"),
        memoryA_confidence=memory_a.get("confidence", 0.5),
        memoryA_evidence_len=len(memory_a.get("evidence_chain", []) or []),
        memoryA_operator_ids=_format_operator_ids(memory_a.get("evidence_operator_ids")),
        memoryB_content=memory_b.get("content", ""),
        memoryB_scope=memory_b.get("scope", "global"),
        memoryB_confidence=memory_b.get("confidence", 0.5),
        memoryB_evidence_len=len(memory_b.get("evidence_chain", []) or []),
        memoryB_operator_ids=_format_operator_ids(memory_b.get("evidence_operator_ids")),
    )


# --------------------------------------------------------------------------- #
# Confidence tie-break (P7 mitigation 4, §3.4)
# --------------------------------------------------------------------------- #


_TIE_THRESHOLD: float = 0.05


def apply_tie_break(
    memory_a: dict[str, Any],
    memory_b: dict[str, Any],
    llm_resolution: dict[str, Any],
) -> dict[str, Any]:
    """Apply deterministic Python tie-break on top of LLM arbitration.

    Rule: when the LLM returned ``A-wins`` or ``B-wins`` AND both memories
    are at the same scope level AND Δconfidence < 0.05, force
    ``deferred-to-operator`` (per §3.4 "Tie-break rule"). The LLM is
    told the same rule in the prompt, but the Python layer is
    authoritative — this avoids any single misbehaving LLM call landing
    a tie case as a decisive win.

    Returns a new resolution dict (does not mutate ``llm_resolution``).
    """
    resolution = llm_resolution.get("resolution")
    if resolution not in ("A-wins", "B-wins"):
        return llm_resolution

    scope_a = memory_a.get("scope")
    scope_b = memory_b.get("scope")
    if scope_a != scope_b:
        # Different scopes — scope-precedence rule applies (handled by LLM)
        return llm_resolution

    conf_a = float(memory_a.get("confidence", 0.5))
    conf_b = float(memory_b.get("confidence", 0.5))
    delta = abs(conf_a - conf_b)
    if delta < _TIE_THRESHOLD:
        return {
            "resolution": "deferred-to-operator",
            "rationale": (
                f"Tie at {scope_a} scope (Δconfidence={delta:.3f} < 0.05)"
            ),
            "confidence": llm_resolution.get("confidence", 0.5),
        }

    return llm_resolution


# --------------------------------------------------------------------------- #
# arbitrate_two_memories — comparator LLM pass + tie-break (§3.2 + §3.4)
# --------------------------------------------------------------------------- #


def arbitrate_two_memories(
    memory_a: dict[str, Any],
    memory_b: dict[str, Any],
    panelist_a: str,
    panelist_b: str,
    project_id: str,
    question: str,
    *,
    comparator_llm: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Run a single memory-vs-memory arbitration pass.

    Args:
        memory_a, memory_b: Memory record dicts (cite Phase 45 memory-record-schema).
        panelist_a, panelist_b: Agent IDs of the citing panelists.
        project_id: Project slug for prompt context.
        question: The debate question.
        comparator_llm: Optional callable to dispatch the LLM call. If
            ``None``, defaults to ``_default_comparator_llm`` (GLM via
            ``auxiliary_client.call_llm``). Tests inject a mock here.

    Returns:
        ``{"resolution": str, "rationale": str, "confidence": float}`` —
        one of the 5 §3.6 enum values, post-tie-break.
    """
    dispatch = comparator_llm or _default_comparator_llm
    prompt = _build_comparator_prompt(
        memory_a, memory_b, panelist_a, panelist_b, project_id, question
    )

    try:
        response = dispatch(messages=[{"role": "user", "content": prompt}])
        content = _extract_content(response)
    except Exception as exc:  # noqa: BLE001 — comparator LLM failure must not crash round table
        logger.warning("comparator LLM dispatch failed: %s", exc)
        return {
            "resolution": "deferred-to-operator",
            "rationale": f"comparator LLM dispatch failed: {exc}",
            "confidence": 0.0,
        }

    llm_resolution = _parse_llm_json(content)
    return apply_tie_break(memory_a, memory_b, llm_resolution)


def _extract_content(response: Any) -> str:
    """Pull ``.choices[0].message.content`` (str) from a call_llm response."""
    try:
        return str(response.choices[0].message.content)
    except (AttributeError, IndexError, TypeError) as exc:
        logger.warning(
            "comparator LLM returned malformed response shape: %s", exc
        )
        return ""


def _parse_llm_json(content: str) -> dict[str, Any]:
    """Parse comparator LLM JSON content defensively (RESEARCH Pitfall 4).

    Falls back to ``deferred-to-operator`` on any ``JSONDecodeError`` —
    never raises. The LLM is untrusted; we trust only the parsed schema.
    """
    if not content:
        return {
            "resolution": "deferred-to-operator",
            "rationale": "comparator LLM returned empty content",
            "confidence": 0.0,
        }
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {
            "resolution": "deferred-to-operator",
            "rationale": "comparator LLM returned malformed JSON",
            "confidence": 0.0,
        }
    if not isinstance(parsed, dict):
        return {
            "resolution": "deferred-to-operator",
            "rationale": "comparator LLM returned non-object JSON",
            "confidence": 0.0,
        }
    # Defensive: ensure required keys exist
    parsed.setdefault("resolution", "deferred-to-operator")
    parsed.setdefault("rationale", "")
    parsed.setdefault("confidence", 0.5)
    return parsed


# --------------------------------------------------------------------------- #
# Conflict log writer (§3.5, JSONL append + fsync)
# --------------------------------------------------------------------------- #


def append_conflict_record(
    conflicts_jsonl_path: Path,
    record: dict[str, Any],
) -> None:
    """Append one conflict record as a single JSONL line, fsync'd.

    Per RESEARCH Pattern 3 (JSONL is line-delimited, atomic per line):
      - ``parent.mkdir(parents=True, exist_ok=True)``
      - one ``json.dumps(...)`` + ``"\\n"`` per record
      - ``flush()`` + ``os.fsync(fileno)`` for durability
      - explicit ``encoding="utf-8"`` (CLAUDE.md PLW1514)

    The writer trusts the caller-constructed path. Path-traversal
    defense lives at the call site (Phase 52 ``validate_project_slug``
    + ``validate_round_id`` reject ``..`` / ``/`` — see threat T-53-08).
    """
    path = Path(conflicts_jsonl_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


# --------------------------------------------------------------------------- #
# memory_retrieve_scoped — Phase 53 routing (replaces Phase 52 stub)
# --------------------------------------------------------------------------- #
#
# Lazy-imports ``plugins.memory.mem0`` inside the function body. If the
# import fails OR ``MEM0_API_KEY`` is unset OR ``backend.is_available()``
# returns False, return ``{"status": "unavailable", "hits": []}`` — graceful
# degradation, NEVER raise. (RESEARCH.md §"Don't Hand-Roll" + Pitfall 5.)


async def memory_retrieve_scoped(
    query: str,
    agent_id: str,
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    """Scoped recall of prior memories (Phase 53 routing).

    Honors the ``_scoped_agent_id`` ContextVar when set; otherwise routes
    by the explicit ``agent_id`` parameter.

    Returns:
        ``{"status": "ok", "hits": [...]}`` when mem0 backend is available.
        ``{"status": "unavailable", "hits": []}`` when the backend is not
        configured (no ``MEM0_API_KEY`` or backend reports unavailable).
    """
    scoped = get_scoped_agent_id()
    effective_agent_id = scoped or agent_id
    logger.debug(
        "memory_retrieve_scoped: query=%s agent_id=%s scoped=%s top_k=%d",
        query,
        agent_id,
        scoped,
        top_k,
    )
    try:
        backend = _get_mem0_backend()
    except Exception as exc:  # noqa: BLE001 — import / config failures are recoverable
        logger.debug("mem0 backend unavailable: %s", exc)
        return {"status": "unavailable", "hits": []}

    if backend is None:
        return {"status": "unavailable", "hits": []}

    try:
        hits = backend.search(query=query, agent_id=effective_agent_id, top_k=top_k)
    except Exception as exc:  # noqa: BLE001 — backend errors degrade, never crash
        logger.warning("mem0 backend search failed: %s", exc)
        return {"status": "unavailable", "hits": []}

    # Layered defense (T-53-06): only return records whose agent_id matches
    # the requested scope. mem0 should already filter, but we re-check.
    # WR-06 fix: drop the ``not isinstance(h, dict) OR ...`` short-circuit
    # (it KEPT non-dict hits, then crashed downstream _format_memory_context).
    # Only KEEP dict hits whose agent_id is unset (legacy record) or matches.
    filtered = [
        h for h in (hits or [])
        if isinstance(h, dict)
        and h.get("agent_id") in (None, effective_agent_id)
    ]
    return {"status": "ok", "hits": filtered}


# --------------------------------------------------------------------------- #
# memory_submit_record — Phase 53 routing (replaces Phase 52 stub)
# --------------------------------------------------------------------------- #


async def memory_submit_record(
    agent_id: str,
    content: str,
    *,
    scope: str = "global",
    confidence: float = 0.5,
) -> dict[str, Any]:
    """Store a new memory record (Phase 53 routing).

    Args:
        agent_id: The agent namespace to write into (routes via memory_scope).
        content: Free-text memory content.
        scope: Visibility tier per memory-record-schema.yaml §3.9
            (``global`` / ``project`` / ``session``). Distinct from the
            agent-YAML's ``memory_scope`` field (shared|per_agent|project_scoped)
            which governs mem0 namespace routing. The comparator's
            ``apply_tie_break`` + ``COMPARATOR_PROMPT_TEMPLATE`` use this
            §3.9 vocabulary; submitting a record with the agents-schema
            ``memory_scope`` vocabulary would never round-trip through the
            comparator (CR-01 fix).
        confidence: ``[0.0, 1.0]`` score for downstream arbitration.

    Returns:
        ``{"status": "ok", "record_id": "<new_id>"}`` on success.
        ``{"status": "unavailable", "record_id": None}`` when the mem0
        backend is not configured.
    """
    scope = _normalize_scope_for_arbitration(scope)
    scoped = get_scoped_agent_id()
    effective_agent_id = scoped or agent_id
    logger.debug(
        "memory_submit_record: agent_id=%s scoped=%s scope=%s confidence=%.2f",
        agent_id,
        scoped,
        scope,
        confidence,
    )
    try:
        backend = _get_mem0_backend()
    except Exception as exc:  # noqa: BLE001
        logger.debug("mem0 backend unavailable: %s", exc)
        return {"status": "unavailable", "record_id": None}

    if backend is None:
        return {"status": "unavailable", "record_id": None}

    try:
        record_id = backend.add(
            content=content,
            agent_id=effective_agent_id,
            scope=scope,
            confidence=confidence,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("mem0 backend add failed: %s", exc)
        return {"status": "unavailable", "record_id": None}

    return {"status": "ok", "record_id": record_id}


#: Authoritative §3.9 scope vocabulary per memory-record-schema.yaml:89.
#: Distinct from agents-schema.yaml §2.6 ``memory_scope`` enum
#: (shared|per_agent|project_scoped) — that field routes mem0 namespaces;
#: the §3.9 ``scope`` field governs cross-project VISIBILITY at retrieve
#: time and is the enum the comparator's ``apply_tie_break`` keys against.
_ARBITRATION_SCOPE_VALUES: frozenset[str] = frozenset({"global", "project", "session"})


def _normalize_scope_for_arbitration(scope: Any) -> str:
    """Coerce a scope value to the memory-record-schema §3.9 vocabulary.

    The 5-mechanism arbitration runtime (comparator prompt +
    ``apply_tie_break``) speaks ONLY the §3.9 enum
    (``global|project|session``). Callers occasionally hand in
    agents-schema §2.6 ``memory_scope`` values
    (``shared|per_agent|project_scoped``) — those are a DIFFERENT axis
    (mem0 namespace routing) and must be translated before arbitration.

    Translation map (CR-01 fix):

    - ``shared`` → ``global`` (cross-agent shared == global visibility)
    - ``project_scoped`` → ``project``
    - ``per_agent`` → ``session`` (agent-private == session-scoped for
      arbitration purposes; same-scope ties are the comparator's only
      project-level deferral path, and per_agent records belong to one
      agent's namespace exactly like session-scoped records belong to
      one conversation)

    Any value already in the §3.9 vocabulary is passed through.
    Unknown values coerce to ``global`` with a warning (defensive —
    the comparator prompt labels ``global|project|session``, so an
    out-of-vocab string would mislead the LLM).
    """
    if scope is None:
        return "global"
    s = str(scope).strip()
    if s in _ARBITRATION_SCOPE_VALUES:
        return s
    mapped = {
        "shared": "global",
        "project_scoped": "project",
        "per_agent": "session",
    }.get(s)
    if mapped is not None:
        logger.debug(
            "scope %r is agents-schema memory_scope vocabulary; "
            "coerced to §3.9 %r for arbitration", s, mapped,
        )
        return mapped
    logger.warning(
        "scope=%r is outside §3.9 vocabulary (global|project|session) "
        "and outside agents-schema memory_scope (shared|per_agent|project_scoped); "
        "coercing to global", s,
    )
    return "global"


def _get_mem0_backend() -> Any:
    """Lazy-import mem0 backend; return ``None`` if unavailable.

    Function-level import (NOT module-level) per RESEARCH Pitfall 5 +
    Phase 52 ``TestNoEagerMem0Import`` AST guard, which is preserved.
    """
    import os as _os
    if not _os.environ.get("MEM0_API_KEY"):
        return None
    try:
        from plugins.memory.mem0 import backend as _backend  # type: ignore[import-not-found]
    except ImportError:
        return None
    if not getattr(_backend, "is_available", lambda: False)():
        return None
    return _backend
