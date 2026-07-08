"""OBSRV-02: Round-table metrics collector (Plan 67-02 Task 1).

Provides the OBSRV-02 observability surface for the v10.0 round-table
orchestrator:

* :class:`RoundTableMetricEntry` -- structured metric record (one per
  captured round-table operation: a single ``get_agent_opinion`` turn
  or a single ``submit_round_table_result`` call).
* :func:`record_round_table_entry` -- thread-safe append to the
  module-level :class:`MetricsBuffer` (Wave 0 primitive).
* :func:`get_round_table_metrics` -- on-demand snapshot + percentile
  computation; consumed by the ``/orchestrator/agents/status`` endpoint
  (Plan 67-04) and the ``hermes orchestrator status`` CLI (Phase 68).
* :func:`_turn_capture` / :func:`_submit_capture` -- sync context
  managers wrapping the bodies of ``mcp_serve.get_agent_opinion`` and
  ``mcp_serve.submit_round_table_result`` so the existing control flow
  is preserved (minimal-diff instrumentation).

Design notes
------------
* **Pull model** (CONTEXT.md G2): collectors store; the endpoint reads
  on demand. No background tasks, no log scraping.
* **Count-based window** (CONTEXT.md G3): the buffer retains the last
  ``100`` entries (deque maxlen) -- deterministic "recent workload"
  semantics.
* **Per-round-table granularity** (CONTEXT.md G4): one entry per
  ``submit`` call (the round-level summary) plus one entry per
  ``get_agent_opinion`` call (per-turn latency). Turn-level entries
  have ``turn_count=1`` and ``cost_usd=0.0``; submit entries carry the
  round totals (``tokensConsumed``, ``costUsdEstimate``).
* **Pitfall 1 (StatisticsError)**: :func:`_percentiles` length-checks
  FIRST and returns zeros on empty input -- ``statistics.quantiles``
  is never called with fewer than 2 samples.
* **Pitfall 2 (capture on exception)**: the context managers use
  ``try/finally`` internally so an entry is recorded on EVERY exit
  path (happy, error, ``BaseException``). Verified by
  ``test_capture_records_on_exception_path``.
* **INFRA-04 compliance**: the context managers are SYNC
  (``@contextmanager``, NOT ``@asynccontextmanager``). All
  ``perf_counter()`` reads are sync. No new ``asyncio.create_task``.
  Verified by inspecting the import line: ``from contextlib import
  contextmanager``.
* **Lazy import**: ``mcp_serve.py`` imports this module lazily inside
  the two function bodies to avoid a module-load cycle (RESEARCH
  Pitfall 6). The module itself imports only from
  ``agent.observability._ring_buffer`` (Wave 0) -- no circular risk.

Threat register
---------------
Mitigates:
* T-67-02-torn (Tampering: concurrent append+snapshot) -- via the
  ``threading.Lock`` inside :class:`MetricsBuffer` (inherited from
  Wave 0).
* T-67-02-infRA04 (DoS: async dispatch violates serial constraint) --
  via the sync ``@contextmanager`` decorator.
* T-67-02-exception (Tampering: exception path skips recording) -- via
  the ``try/finally`` block inside each context manager.
"""

from __future__ import annotations

import statistics
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

from agent.observability._ring_buffer import MetricsBuffer

__all__ = [
    "RoundTableMetricEntry",
    "record_round_table_entry",
    "get_round_table_metrics",
    "_percentiles",
    "_turn_capture",
    "_submit_capture",
    "_reset_for_test",
]


def _now_iso_utc() -> str:
    """Current UTC time as ISO-8601 (mirrors agent_registry_metrics convention)."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Entry dataclass + module-level buffer
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class RoundTableMetricEntry:
    """One captured round-table operation (turn or submit).

    Attributes:
        round_id: The roundId this entry belongs to.
        snapshot_at_iso: ISO-8601 UTC timestamp at capture time.
        duration_ms: Wall time of the captured operation (milliseconds).
        token_cost: ``total_tokens`` for a turn; ``tokensConsumed`` for a submit.
        cost_usd: USD estimate. ``0.0`` for per-turn; ``costUsdEstimate``
            for submit.
        turn_count: ``1`` for per-turn entries; ``len(result["turns"])`` for
            submit entries.
        serial_lock_wait_ms: Time spent waiting for
            ``acquire_round_or_reject`` (turn entries). ``0.0`` for submit
            entries (submit does not acquire the serial lock).
        early_stop_triggered: ``True`` if a ``budget_exceeded`` event fired
            during the round (submit entries only). ``False`` for turns.
        status: Outcome label -- ``"ok"``, ``"completed"``,
            ``"serial_violation"``, ``"round_not_found"``, ``"error"``,
            ``"conflict_409"``, etc.
    """

    round_id: str
    snapshot_at_iso: str
    duration_ms: float
    token_cost: int
    cost_usd: float
    turn_count: int
    serial_lock_wait_ms: float
    early_stop_triggered: bool
    status: str


#: Module-level ring buffer. One per process (CONTEXT.md G1). Thread-safe
#: via MetricsBuffer's internal threading.Lock (T-67-02-torn mitigation).
#: Collectors in Plans 67-02 and 67-03 each own their own MetricsBuffer
#: instance -- this one is OBSRV-02 only.
_BUFFER: MetricsBuffer[RoundTableMetricEntry] = MetricsBuffer(maxlen=100)


def record_round_table_entry(entry: RoundTableMetricEntry) -> None:
    """Append ``entry`` to the module-level buffer. Thread-safe.

    Called by the ``_turn_capture`` / ``_submit_capture`` context managers
    on exit. Direct calls are also valid (e.g. for ad-hoc instrumentation).
    """
    _BUFFER.append(entry)


def _reset_for_test() -> None:
    """Clear the module-level buffer. TEST-ONLY helper.

    Cross-test isolation: pytest's autouse fixture in
    ``test_round_table_metrics.py`` calls this before each test so prior
    appends cannot leak into later assertions. NOT for production use --
    production callers should never reset the buffer.

    Phase 67 WR-05 fix: switched from rebinding the module global
    (``_BUFFER = MetricsBuffer(...)``) to in-place ``_BUFFER.clear()``.
    The rebind pattern silently broke any caller that imported the
    reference via ``from ... import _BUFFER`` — their reference would
    still point at the old deque while tests reset the new one. The
    in-place clear preserves the singleton identity and uses the public
    ``MetricsBuffer.clear()`` API rather than reaching into ``_buf``.
    Consistent with ``memory_backend_metrics._reset_for_test``.
    """
    _BUFFER.clear()


# ---------------------------------------------------------------------------
# p50/p95 computation -- RESEARCH Pattern 3 (Pitfall 1 mitigation)
# ---------------------------------------------------------------------------


def _percentiles(samples: list[float]) -> dict[str, float]:
    """Compute p50/p95 over ``samples``.

    Returns a dict with ``{"p50", "p95", "count"}``.

    Pitfall 1 mitigation: ``statistics.quantiles`` raises
    ``StatisticsError`` on fewer than 2 data points. We length-check
    FIRST and return zeros (empty) or the single value (count=1).

    Args:
        samples: Latency samples (milliseconds). Order is irrelevant;
            ``statistics.quantiles`` sorts internally.

    Returns:
        Dict with ``p50``, ``p95``, ``count`` keys.
    """
    if not samples:
        return {"p50": 0.0, "p95": 0.0, "count": 0}
    if len(samples) == 1:
        v = float(samples[0])
        return {"p50": v, "p95": v, "count": 1}
    # statistics.quantiles(data, n=100) returns 99 cut points (q_1..q_99).
    # p50 is index 49 (the 50th percentile cut); p95 is index 94.
    qs = statistics.quantiles(samples, n=100)
    return {"p50": qs[49], "p95": qs[94], "count": len(samples)}


# ---------------------------------------------------------------------------
# On-demand snapshot getter (pull model -- Plan 67-04 endpoint consumer)
# ---------------------------------------------------------------------------


def get_round_table_metrics() -> dict[str, Any]:
    """Snapshot the round-table buffer and compute aggregate metrics.

    Returns a fresh dict on every call. Computed from a point-in-time
    snapshot of the module-level buffer (thread-safe copy).

    Returns:
        Dict with keys:
            * ``count`` (int) -- entries in the buffer.
            * ``p50_latency_ms`` (float) -- median duration.
            * ``p95_latency_ms`` (float) -- 95th percentile duration.
            * ``avg_token_cost`` (float) -- mean token_cost across entries.
            * ``total_token_cost`` (int) -- sum of token_cost.
            * ``status_distribution`` (dict[str, int]) -- Counter over status.
            * ``serial_lock_wait_p95_ms`` (float) -- p95 of serial_lock_wait_ms.
            * ``early_stop_rate`` (float) -- fraction with early_stop_triggered.
            * ``snapshot_at_iso`` (str) -- ISO-8601 UTC timestamp.
    """
    snap = _BUFFER.snapshot()
    count = len(snap)
    if count == 0:
        return {
            "count": 0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "avg_token_cost": 0.0,
            "total_token_cost": 0,
            "status_distribution": {},
            "serial_lock_wait_p95_ms": 0.0,
            "early_stop_rate": 0.0,
            "snapshot_at_iso": _now_iso_utc(),
        }

    durations = [float(e.duration_ms) for e in snap]
    lock_waits = [float(e.serial_lock_wait_ms) for e in snap]
    total_tokens = int(sum(int(e.token_cost) for e in snap))
    status_counts = Counter(e.status for e in snap)
    early_stop_count = sum(1 for e in snap if e.early_stop_triggered)

    pct = _percentiles(durations)
    lock_pct = _percentiles(lock_waits)

    return {
        "count": count,
        "p50_latency_ms": pct["p50"],
        "p95_latency_ms": pct["p95"],
        "avg_token_cost": total_tokens / count,
        "total_token_cost": total_tokens,
        "status_distribution": dict(status_counts),
        "serial_lock_wait_p95_ms": lock_pct["p95"],
        "early_stop_rate": early_stop_count / count,
        "snapshot_at_iso": _now_iso_utc(),
    }


# ---------------------------------------------------------------------------
# Sync context managers -- RESEARCH Pattern 2 (minimal-diff instrumentation)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _CaptureState:
    """Mutable holder yielded by the capture context managers.

    The caller (``mcp_serve`` instrumentation in Task 2) sets attributes
    on this object DURING the ``with`` block so the context manager's
    ``__exit__`` can read them when assembling the metric entry. Defaults
    are conservative (``status="ok"``, ``token_cost=0``) so a no-op
    ``with _turn_capture("rid"): pass`` still records a valid entry.
    """

    round_id: str
    t_start: float
    status: str = "ok"
    token_cost: int = 0
    cost_usd: float = 0.0
    turn_count: int = 1
    serial_lock_wait_ms: float = 0.0
    early_stop_triggered: bool = False


@contextmanager
def _turn_capture(round_id: str) -> Iterator[_CaptureState]:
    """Wrap one ``get_agent_opinion`` turn body.

    Records a :class:`RoundTableMetricEntry` on every exit path (happy,
    error, ``BaseException``). Re-raises on exception.

    Yields a :class:`_CaptureState` -- the caller sets ``.status``,
    ``.token_cost``, ``.serial_lock_wait_ms`` etc. on it during the
    ``with`` block. On exit the context manager reads those values and
    assembles the entry.

    Example::

        with _turn_capture(round_id) as cap:
            t_lock_req = time.perf_counter()
            lock = await acquire_round_or_reject(round_id)
            cap.serial_lock_wait_ms = (time.perf_counter() - t_lock_req) * 1000.0
            if lock is None:
                cap.status = "serial_violation"
                return _serial_violation_response(round_id)
            # ... happy path ...
            cap.status = "ok"
            cap.token_cost = int(get_last_call_usage().get("total_tokens", 0))
    """
    cap = _CaptureState(round_id=round_id, t_start=time.perf_counter())
    try:
        yield cap
    except BaseException as exc:
        # Pitfall 2 mitigation: record on exception BEFORE re-raising.
        # Override status to "error" -- the caller may have set a more
        # specific status earlier, but if we got here via an unforeseen
        # exception, "error" is the honest label.
        cap.status = "error"
        _record_from_capture(cap)
        raise
    else:
        _record_from_capture(cap)


@contextmanager
def _submit_capture(round_id: str) -> Iterator[_CaptureState]:
    """Wrap one ``submit_round_table_result`` body.

    Same shape as :func:`_turn_capture` but the caller populates
    ``token_cost`` (from ``result["tokensConsumed"]``), ``cost_usd``
    (from ``result["costUsdEstimate"]``), ``turn_count`` (from
    ``len(result["turns"])``), and ``early_stop_triggered`` (from
    ``result["events"]``) after the ``_submit(...)`` call returns.
    """
    cap = _CaptureState(
        round_id=round_id,
        t_start=time.perf_counter(),
        # Defaults: submit entries carry turn_count=0 until the caller
        # populates it from result["turns"]. token_cost=0 until populated
        # from result["tokensConsumed"].
        turn_count=0,
        status="completed",
    )
    try:
        yield cap
    except BaseException as exc:
        cap.status = "error"
        _record_from_capture(cap)
        raise
    else:
        _record_from_capture(cap)


def _record_from_capture(cap: _CaptureState) -> None:
    """Assemble a :class:`RoundTableMetricEntry` from a capture state and append.

    Called by both context managers on exit. Centralizes the entry-assembly
    logic so the two managers stay small.
    """
    duration_ms = (time.perf_counter() - cap.t_start) * 1000.0
    entry = RoundTableMetricEntry(
        round_id=cap.round_id,
        snapshot_at_iso=_now_iso_utc(),
        duration_ms=duration_ms,
        token_cost=int(cap.token_cost),
        cost_usd=float(cap.cost_usd),
        turn_count=int(cap.turn_count),
        serial_lock_wait_ms=float(cap.serial_lock_wait_ms),
        early_stop_triggered=bool(cap.early_stop_triggered),
        status=cap.status,
    )
    record_round_table_entry(entry)
