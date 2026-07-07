"""Timing-instrumented wrapper around ``memory_retrieve_scoped`` (Phase 54 plan 02).

This module provides the EVAL-02 latency SLO benchmark harness per
``.planning/research/v10-orchestrator-design/05-POC-PLAN.md §4.2``. It
exposes:

1. ``LatencySample`` — structured record of one retrieval call.
2. ``timed_retrieval`` — wraps ``memory_arbitration.memory_retrieve_scoped``
   (or accepts an explicit ``backend`` for fixture-only benchmarks) in a
   ``time.perf_counter()`` bracket, returns a ``LatencySample``.
3. ``compute_percentiles`` — stdlib-only p50/p95/p99 of a latency list.

Design constraints (per ``54-02-PLAN.md`` Task 1):
- ZERO LLM dispatch invocations — the §4.2 SLO explicitly excludes
  LLM-bound paths (per STACK §7.4: LLM call = 2-15s, not in 500ms budget).
  The test ``TestNoLLMInTimedRetrievalPath`` patches the auxiliary LLM
  dispatcher with a detector to enforce this at runtime; the SLO budget
  is mem0 ``backend.search()`` cost only.
- Uses stdlib ``statistics.quantiles`` only — no scipy, no new deps
  (Phase 52 dependency hygiene, threat T-54-SC).
- Async — matches ``memory_arbitration.memory_retrieve_scoped``'s async
  signature.
- On exception, returns ``status="error"`` with the measured partial
  latency — never raises (the benchmark runs 100 sequential calls and
  must not abort on a single backend hiccup).

Citations:
- ``05-POC-PLAN.md §4.2`` task (a) — log field + timing wrapper
- ``05-POC-PLAN.md §4.2`` task (c) — 3-count benchmark protocol
- PITFALLS §P3 mitigation 4 — observability for read-path latency SLO
- STACK §7.4 — latency budget (stdio <5ms, MCP <10ms, LLM 2-15s excluded)
"""

from __future__ import annotations

import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# LatencySample
# --------------------------------------------------------------------------- #


@dataclass
class LatencySample:
    """One retrieval call's measurement.

    Fields:
        latency_ms: Wall-clock cost of the ``backend.search()`` call in
            milliseconds (monotonic ``time.perf_counter()`` delta × 1000).
            Always > 0 for both ``ok`` and ``error`` statuses (the timer
            starts before the call and is read after — exceptions still
            produce a measured partial latency).
        status: One of ``"ok"``, ``"unavailable"``, ``"error"``.
            - ``"ok"`` — backend returned hits (possibly empty list).
            - ``"unavailable"`` — backend not configured (CI fallback).
            - ``"error"`` — backend raised; benchmark treats as a single
              failed sample, does NOT abort the 100-call run.
        hits: The list of dict records returned (``[]`` on error/unavailable).
        ts: ISO-8601 UTC timestamp when the sample was finalized. Used
            only for log correlation; not load-bearing for SLO math.
    """

    latency_ms: float
    status: str
    hits: list[dict[str, Any]] = field(default_factory=list)
    ts: str = ""


# --------------------------------------------------------------------------- #
# timed_retrieval
# --------------------------------------------------------------------------- #


async def timed_retrieval(
    *,
    query: str,
    agent_id: str,
    backend: Any = None,
    top_k: int = 5,
) -> LatencySample:
    """Time one scoped retrieval call; return a ``LatencySample``.

    Two call modes (mutually exclusive via the ``backend`` kwarg):

    1. **Fixture mode** (used by benchmark + tests): caller passes a
       ``backend`` object exposing ``search(*, query, agent_id, top_k)``.
       The wrapper measures the call directly against the supplied object.
       This bypasses ``memory_arbitration._get_mem0_backend`` so the
       benchmark is deterministic in CI (no live mem0 Platform API).

    2. **Production mode** (no ``backend`` kwarg): the wrapper delegates
       to ``memory_arbitration.memory_retrieve_scoped``, which lazy-imports
       the mem0 plugin and returns ``status="unavailable"`` when
       ``MEM0_API_KEY`` is unset or the plugin reports unavailable.

    The wrapper NEVER dispatches an LLM call — the §4.2 SLO explicitly
    excludes LLM-bound paths (per STACK §7.4). ``TestNoLLMInTimedRetrievalPath``
    enforces this at test time.

    Args:
        query: Free-text retrieval query.
        agent_id: Scoped agent namespace (per Phase 45 memory-record-schema).
        backend: Optional pre-built backend (fixture mode). ``None`` →
            production routing via ``memory_arbitration``.
        top_k: Maximum hits to return (default 5).

    Returns:
        ``LatencySample`` — never raises.
    """
    ts_start = time.perf_counter()
    status = "ok"
    hits: list[dict[str, Any]] = []

    try:
        if backend is not None:
            # Fixture mode — call the supplied backend's search() directly.
            raw_hits = backend.search(query=query, agent_id=agent_id, top_k=top_k)
            hits = [h for h in (raw_hits or []) if isinstance(h, dict)]
        else:
            # Production mode — delegate to memory_arbitration.
            from agent.memory_arbitration import memory_retrieve_scoped
            result = await memory_retrieve_scoped(
                query=query, agent_id=agent_id, top_k=top_k,
            )
            status = str(result.get("status", "ok"))
            hits = [h for h in (result.get("hits") or []) if isinstance(h, dict)]
    except Exception as exc:  # noqa: BLE001 — never raise; record as error sample
        logger.debug("timed_retrieval backend call failed: %s", exc)
        status = "error"
        hits = []

    ts_end = time.perf_counter()
    latency_ms = (ts_end - ts_start) * 1000.0

    return LatencySample(
        latency_ms=latency_ms,
        status=status,
        hits=hits,
        ts=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    )


# --------------------------------------------------------------------------- #
# compute_percentiles
# --------------------------------------------------------------------------- #


def compute_percentiles(samples_ms: list[float]) -> dict[str, float]:
    """Compute p50/p95/p99 from a list of latency measurements (ms).

    Uses stdlib ``statistics.quantiles`` with ``method="inclusive"`` so
    the 100-percentile grid covers the [0, 100) range including the
    endpoints. No scipy/numpy dependency (per threat T-54-SC + Phase 52
    dependency hygiene).

    Edge cases:
        - Empty list → returns all zeros (defensive; benchmark treats this
          as "no samples collected" rather than crashing).
        - Single sample → returns the same value at p50/p95/p99
          (``statistics.quantiles`` requires len ≥ 2 for n=100; we
          short-circuit before calling it).
        - Two samples → uses linear interpolation (``inclusive`` method).

    Args:
        samples_ms: Latency measurements in milliseconds. Order does not
            matter (``statistics.quantiles`` sorts internally).

    Returns:
        ``{"p50": float, "p95": float, "p99": float}``.
    """
    if not samples_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    if len(samples_ms) == 1:
        v = float(samples_ms[0])
        return {"p50": v, "p95": v, "p99": v}

    # ``statistics.quantiles`` returns n-1 cut points dividing the data
    # into n equal-sized buckets. With n=100, indices 0..98 correspond
    # to the 1st..99th percentile cut points. We pick indices 49/94/98
    # for p50/p95/p99.
    #
    # ``method="inclusive"`` is the right choice here: latency samples
    # are a finite population (the 100 sequential calls in a benchmark
    # run are themselves the complete universe we care about), not a
    # sample drawn from a larger distribution. ``inclusive`` uses the
    # same interpolation rule as Excel/Google Sheets percentile.inc.
    cuts = statistics.quantiles(samples_ms, n=100, method="inclusive")
    return {
        "p50": float(cuts[49]),  # 50th percentile cut index
        "p95": float(cuts[94]),  # 95th percentile cut index
        "p99": float(cuts[98]),  # 99th percentile cut index
    }
