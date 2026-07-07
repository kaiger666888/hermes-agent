"""Pytest fixtures for v11.0 latency benchmark tests (Phase 54 plan 02).

Provides the in-memory ``FakeBackend`` that implements the subset of the
``Mem0MemoryProvider`` contract used by ``timed_retrieval``:

  - ``search(*, query, agent_id, top_k) -> list[dict]``
  - ``add(*, content, agent_id, scope, confidence) -> str``

This fake is used by the latency benchmark so CI does not depend on a live
mem0 Platform API (per CONTEXT.md decision #2 — fixture-only store).
"""

from __future__ import annotations

from typing import Any


class FakeBackend:
    """In-memory deterministic stand-in for ``Mem0MemoryProvider``.

    Implements the ``backend.search(query=, agent_id=, top_k=)`` +
    ``backend.add(content=, agent_id=, scope=, confidence=) -> str`` contract
    that ``memory_arbitration.memory_retrieve_scoped`` and
    ``agent.memory_scoped_retrieval.timed_retrieval`` both call.

    The fake is intentionally synchronous (matching the real mem0 plugin's
    synchronous ``search``/``add`` methods) and deterministic (no network,
    no LLM, no randomness). Records are stored in insertion order; ``search``
    returns the most-recently-added ``top_k`` records whose ``agent_id``
    matches, simulating a server-side scoped filter (per ARCHITECTURE §3.2
    "Option B" routing).
    """

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []
        self._next_id: int = 1
        # Failure injection (used by Test 3 — error path coverage).
        self.search_raises: bool = False

    # ------------------------------------------------------------------ #
    # Mem0MemoryProvider contract
    # ------------------------------------------------------------------ #

    def search(
        self,
        *,
        query: str,
        agent_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Return up to ``top_k`` records matching ``agent_id`` (most-recent first).

        No keyword/ranking logic — the latency SLO is about the
        ``backend.search()`` call cost, not about result quality. The real
        mem0 backend runs HNSW + post-filter; the fake just simulates a
        deterministic O(N) scan so the benchmark exercises the wrapper
        instrumentation rather than a real vector index.
        """
        if self.search_raises:
            raise RuntimeError("FakeBackend.search injected failure")
        if agent_id is None:
            return list(reversed(self._records[-top_k:]))
        scoped = [r for r in self._records if r.get("agent_id") == agent_id]
        return list(reversed(scoped[-top_k:]))

    def add(
        self,
        *,
        content: str,
        agent_id: str | None = None,
        scope: str = "global",
        confidence: float = 0.5,
    ) -> str:
        """Append one record; return its synthetic id."""
        record_id = f"fake-{self._next_id:08d}"
        self._next_id += 1
        self._records.append({
            "id": record_id,
            "content": content,
            "agent_id": agent_id,
            "scope": scope,
            "confidence": confidence,
        })
        return record_id

    # ------------------------------------------------------------------ #
    # Test helpers
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> list[dict[str, Any]]:
        """Read-only view of stored records (for fixture assertions)."""
        return list(self._records)
