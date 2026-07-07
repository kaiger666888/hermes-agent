"""Per-agent memory arbitration layer (Phase 52 STUB).

This module provides the wire surface for two MCP tools:

- ``memory_retrieve_scoped`` — scoped recall of prior memories
- ``memory_submit_record`` — store a new memory record

**Phase 52 ships STUBS.** Both functions return a fixed
``phase53_not_implemented`` payload. Phase 53 (CREATIVE-SLICE) wires the
real mem0 backend routing per ``agents-schema.yaml §2.6`` ``memory_scope``
(``shared`` / ``per_agent`` / ``project_scoped``).

The module also exposes the ``_scoped_agent_id`` ``contextvars.ContextVar``
primitive referenced by ``01-AGENT-REGISTRY-SCHEMA.md §5.5``. The primitive
is asyncio-correct (``contextvars``, NOT ``threading.local``) because
``ThreadPoolExecutor`` worker reuse makes ``threading.local`` leak scope
across tasks. Phase 53's memory routing hooks into this primitive via
``set_scoped_agent_id`` / ``get_scoped_agent_id`` from inside the
round-table executor.

Why stubs in Phase 52
---------------------
Per ``52-CONTEXT.md`` "Resolved by Kai" point 3, Phase 52's job is the
wire-up + primitive; Phase 53's job is the routing. Shipping stubs also
avoids eagerly coupling Phase 52 to ``plugins.memory.mem0`` — without
``MEM0_API_KEY`` set the mem0 backend's ``is_available()`` returns False
and its ``search()`` raises (see RESEARCH.md §"Pitfall 5").

DO NOT ADD ``import plugins.memory.mem0`` here — Phase 53 will add it
when it fills in the routing.

Locked return contract (CONTEXT.md point 3)
-------------------------------------------
- ``memory_retrieve_scoped(...)`` →
  ``{"status": "phase53_not_implemented", "hits": []}``
- ``memory_submit_record(...)`` →
  ``{"status": "phase53_not_implemented", "record_id": None}``

Design sources (cite, do not re-derive)
---------------------------------------
- ``52-CONTEXT.md`` "Resolved by Kai" point 3 — locked stub return contract
- ``.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md §5.5``
  — ``_scoped_agent_id`` contextvars primitive spec
- ``52-PATTERNS.md`` §"agent/memory_arbitration.py" + §"Contextvars primitive"
- ``gateway/session_context.py:39-83`` — canonical ContextVar pattern
  (``_UNSET`` sentinel + setter/getter)
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# _scoped_agent_id contextvars primitive
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

    Called by the round-table executor (Phase 53) before delegating to a
    panelist's memory retrieval / record submission so the routing layer
    knows which agent's namespace to consult.

    Pass ``None`` to clear the scope (e.g. when leaving a panelist's
    context). The scoped value is local to the current asyncio task and
    does NOT leak across ``asyncio.create_task`` boundaries — verified
    by ``tests/agent/test_memory_arbitration_stub.py``.
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
# Memory tool STUBS — Phase 53 fills in real routing
# --------------------------------------------------------------------------- #
#
# Both functions are ``async def`` so they integrate natively with FastMCP's
# async tool dispatch (Phase 53's real routing will likely ``await`` mem0
# network calls). Phase 52's stubs don't actually await anything, but the
# ``async`` signature is reserved now so adding routing later is non-breaking.


async def memory_retrieve_scoped(
    query: str,
    agent_id: str,
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    """STUB. Returns ``phase53_not_implemented``.

    Phase 53 wires real mem0 routing per ``agents-schema.yaml §2.6``
    ``memory_scope`` (``shared`` / ``per_agent`` / ``project_scoped``).

    Args:
        query: Free-text recall query.
        agent_id: The agent whose memory namespace to consult.
        top_k: Max results to return (Phase 53 will honor this; stub ignores).

    Returns:
        ``{"status": "phase53_not_implemented", "hits": []}`` — locked by
        ``52-CONTEXT.md`` "Resolved by Kai" point 3. Do NOT change the
        status string or the empty-list shape without re-running the
        Phase 52 acceptance tests; downstream Phase 53 routing code keys
        off this exact payload.
    """
    logger.debug(
        "memory_retrieve_scoped stub called: query=%s agent_id=%s top_k=%d",
        query,
        agent_id,
        top_k,
    )
    return {"status": "phase53_not_implemented", "hits": []}


async def memory_submit_record(
    agent_id: str,
    content: str,
    *,
    scope: str = "per_agent",
    confidence: float = 0.5,
) -> dict[str, Any]:
    """STUB. Returns ``phase53_not_implemented`` with ``record_id=None``.

    Phase 53 wires real mem0 routing per ``agents-schema.yaml §2.6``
    ``memory_scope``.

    Args:
        agent_id: The agent whose memory namespace to write into.
        content: Free-text memory content to persist.
        scope: One of ``shared`` / ``per_agent`` / ``project_scoped`` (Phase
            53 validates; Phase 52 stub accepts any string and ignores).
        confidence: Optional confidence score in ``[0.0, 1.0]`` (Phase 53
            uses for memory consolidation; stub ignores).

    Returns:
        ``{"status": "phase53_not_implemented", "record_id": None}`` —
        locked by ``52-CONTEXT.md`` "Resolved by Kai" point 3.
    """
    logger.debug(
        "memory_submit_record stub called: agent_id=%s scope=%s confidence=%.2f content_len=%d",
        agent_id,
        scope,
        confidence,
        len(content),
    )
    return {"status": "phase53_not_implemented", "record_id": None}
