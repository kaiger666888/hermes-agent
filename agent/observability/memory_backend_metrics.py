"""OBSRV-03: Memory backend metrics collector (Plan 67-03 Task 1).

Exposes the OBSRV-03 surface consumed by the ``/orchestrator/agents/status``
FastAPI endpoint (Plan 67-04) and the Phase 68 CLI
``hermes orchestrator status``:

* :class:`MemoryOpMetricEntry` -- one recorded search/add op
* :func:`record_memory_op_entry` -- low-level thread-safe buffer append
* :func:`record_conflict` -- thread-safe conflict-counter increment
* :func:`get_memory_backend_metrics` -- snapshot dict (p95 read/write,
  conflict count, error rate, status)
* :func:`_memory_op_capture` -- ``@contextmanager`` wrapping search/add;
  caller sets ``cap.hit_count`` before normal exit; on exception the
  entry is recorded with ``success=False`` + ``error_type`` and the
  exception re-raises (preserving the adapter's "never raise" contract
  because the outer try/except in the adapter still catches it)

Design notes
------------
* **Pull model (CONTEXT.md G2).** The collector populates a module-level
  ring buffer on every search/add op; the endpoint computes p95 on demand
  from the current snapshot. No push, no async background tasks.
* **Count-based window (CONTEXT.md G3).** ``MetricsBuffer(maxlen=100)``
  retains the last 100 ops (any mix of search + add). Older entries are
  auto-evicted.
* **Pitfall 1 (empty buffer).** ``statistics.quantiles([])`` raises
  ``StatisticsError``. We short-circuit to ``0.0`` when the partition
  has ``< 2`` samples (mirrors the OBSRV-02 collector's helper).
* **Pitfall 2 (thread safety).** Buffer mutations and snapshots are
  guarded by the ``MetricsBuffer``'s internal ``threading.Lock``. The
  conflict counter has its own lock because it is mutated independently
  of the buffer (``record_conflict`` does not append an entry).
* **Pitfall 6 (circular import).** ``plugins.memory.mem0`` lazy-imports
  ``_memory_op_capture`` inside method bodies (Task 2 instrumentation),
  so this module must NOT import ``plugins.*`` at module top. We import
  only from ``agent.observability._ring_buffer`` here.
* **compaction_triggers** is reported as a constant ``0``. Mem0 Platform
  performs server-side compaction that is not observable from the client
  (RESEARCH Assumption A1). Revisit in v14 if we move to self-hosted
  mem0. This is an honest empty value, not a fabricated metric
  (threat T-67-03-compaction mitigation).

Threat register
---------------
Mitigates:
* T-67-03-counter (Tampering: concurrent counter increment) -- via the
  dedicated ``_CONFLICT_LOCK``.
* T-67-03-adapter (DoS: instrumentation breaks "never raise" adapter
  contract) -- ``_memory_op_capture`` records the failure entry in
  ``__exit__`` and re-raises; the outer try/except in
  ``_BackendAdapter.search/add`` still catches. Verified by
  ``test_capture_on_exception_records_failure_and_reraises``.
* T-67-03-compaction (Information Disclosure via false data) -- inline
  comment + honest zero for ``compaction_triggers``.
* T-67-03-torn (Tampering: torn buffer snapshot) -- inherits Wave 0
  ``MetricsBuffer`` threading.Lock.
"""

from __future__ import annotations

import logging
import statistics
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Iterator

from agent.observability._ring_buffer import MetricsBuffer

__all__ = [
    "MemoryOpMetricEntry",
    "record_memory_op_entry",
    "record_conflict",
    "get_memory_backend_metrics",
    "_memory_op_capture",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entry dataclass
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class MemoryOpMetricEntry:
    """One recorded memory-backend operation (search or add).

    Attributes
    ----------
    op_type:
        ``"search"`` for ``_BackendAdapter.search``, ``"add"`` for
        ``_BackendAdapter.add``.
    started_at_iso:
        ISO-8601 UTC timestamp captured at context-manager entry.
    duration_ms:
        Wall-clock duration in milliseconds, from context-manager entry
        to exit (success or exception). Measured via
        :func:`time.perf_counter` for monotonicity.
    success:
        ``True`` on normal exit, ``False`` if an exception propagated
        through the ``with`` block.
    hit_count:
        Number of results returned (``len(out)`` for search). Always
        ``0`` for ``add`` (add has no hits). Set by the caller via
        ``cap.hit_count`` before normal exit.
    error_type:
        Exception class name if ``success=False``, else ``None``.
    """

    op_type: str
    started_at_iso: str
    duration_ms: float
    success: bool
    hit_count: int
    error_type: str | None


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

#: Ring buffer retaining the last 100 memory op entries (CONTEXT.md G3).
#: Thread-safe append + snapshot via the MetricsBuffer's internal lock.
_BUFFER: MetricsBuffer[MemoryOpMetricEntry] = MetricsBuffer(maxlen=100)

#: Dedicated lock for the conflict counter. Kept separate from the buffer
#: lock so that ``record_conflict`` (which does NOT append an entry) does
#: not contend with buffer snapshots (threat T-67-03-counter).
_CONFLICT_LOCK = threading.Lock()

#: Number of times ``record_conflict`` has been called since module load
#: (or since the last ``_reset_for_test`` call). Reset is test-only.
_CONFLICT_COUNT = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso_utc() -> str:
    """Current UTC time as ISO-8601.

    Mirrors the codebase convention (see
    ``agent_registry_metrics._now_iso_utc``).
    """
    return datetime.now(timezone.utc).isoformat()


def _percentile_p95(samples: list[float]) -> float:
    """Return the p95 of ``samples``.

    Returns ``0.0`` for empty or single-element lists to avoid the
    ``statistics.StatisticsError`` that ``statistics.quantiles`` raises
    on ``< 2`` data points (RESEARCH Pitfall 1).

    For ``len(samples) >= 2``, delegates to
    ``statistics.quantiles(samples, n=100)[94]`` -- the 95th percentile
    via inclusive interpolation. Matches the OBSRV-02 collector's helper
    semantics.

    Args:
        samples: List of durations (ms). May be empty.

    Returns:
        The p95 value, or ``0.0`` if ``len(samples) < 2``.
    """
    if len(samples) < 2:
        # Empty -> 0.0 (no data); single element -> would be the p95
        # itself but we report 0.0 for consistency with the
        # empty-buffer contract (Pitfall 1 says "return zeros").
        return 0.0
    qs = statistics.quantiles(samples, n=100)
    return float(qs[94])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record_memory_op_entry(entry: MemoryOpMetricEntry) -> None:
    """Append one entry to the metrics buffer. Thread-safe.

    Called automatically by ``_memory_op_capture`` on context exit.
    Exposed publicly so that callers using non-context-manager code
    paths (e.g. test setup) can populate the buffer directly.

    Args:
        entry: A fully-populated :class:`MemoryOpMetricEntry`.
    """
    _BUFFER.append(entry)


def record_conflict() -> None:
    """Increment the conflict-arbitration counter. Thread-safe.

    Called by the instrumentation in
    :func:`agent.memory_arbitration.append_conflict_record` (Task 2).
    Each call represents one observed memory conflict (two agents'
    memories disagreeing, requiring arbitration).

    The counter is reset only by ``_reset_for_test`` (test-only). In
    production it accumulates over the lifetime of the process.
    """
    global _CONFLICT_COUNT
    with _CONFLICT_LOCK:
        _CONFLICT_COUNT += 1


def get_memory_backend_metrics() -> dict[str, Any]:
    """Snapshot the memory-backend metrics buffer.

    Computes the OBSRV-03 percentile + count aggregates on demand
    (CONTEXT.md G2 pull model). The endpoint calls this live on each
    HTTP GET.

    Returns a dict with these keys:

    * ``search_p95_ms`` (float) -- p95 of search op durations, or
      ``0.0`` if ``< 2`` search samples in the buffer
    * ``add_p95_ms`` (float) -- p95 of add op durations, or ``0.0``
    * ``search_count`` (int) -- number of search ops in the buffer
    * ``add_count`` (int) -- number of add ops in the buffer
    * ``error_rate`` (float) -- ``failures / total`` across both op
      types; ``0.0`` if buffer empty
    * ``conflict_count`` (int) -- lifetime conflict-arbitration count
    * ``compaction_triggers`` (int) -- always ``0`` (see module
      docstring + RESEARCH A1; Mem0 Platform compaction is not
      client-observable)
    * ``status`` (str) -- ``"no_data"`` when buffer is empty,
      ``"ok"`` otherwise
    """
    snapshot = _BUFFER.snapshot()
    search_durations = [
        e.duration_ms for e in snapshot if e.op_type == "search"
    ]
    add_durations = [
        e.duration_ms for e in snapshot if e.op_type == "add"
    ]

    search_p95 = _percentile_p95(search_durations)
    add_p95 = _percentile_p95(add_durations)

    total = len(snapshot)
    failures = sum(1 for e in snapshot if not e.success)
    error_rate = (failures / total) if total else 0.0

    with _CONFLICT_LOCK:
        conflict_count = _CONFLICT_COUNT

    return {
        "search_p95_ms": search_p95,
        "add_p95_ms": add_p95,
        "search_count": len(search_durations),
        "add_count": len(add_durations),
        "error_rate": error_rate,
        "conflict_count": conflict_count,
        # Mem0 Platform performs server-side compaction that is not
        # client-observable (RESEARCH Assumption A1). Honest zero rather
        # than a fabricated metric. Revisit in v14 if we move to
        # self-hosted mem0 (threat T-67-03-compaction).
        "compaction_triggers": 0,
        "status": "no_data" if total == 0 else "ok",
    }


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class _CaptureState:
    """Mutable state yielded by :func:`_memory_op_capture`.

    The caller mutates ``hit_count`` inside the ``with`` block (e.g.
    ``cap.hit_count = len(out)`` for search). On normal exit, the
    context manager reads ``hit_count`` to build the metric entry.

    Using a small class rather than ``types.SimpleNamespace`` so the
    type is explicit and the attribute is documented.
    """

    __slots__ = ("hit_count",)

    def __init__(self) -> None:
        # Default hit_count is 0. ``add`` never overrides this; ``search``
        # sets it to ``len(out)`` just before normal exit.
        self.hit_count = 0


@contextmanager
def _memory_op_capture(op_type: str) -> Iterator[_CaptureState]:
    """Context manager wrapping one memory-backend op (search or add).

    Records the op's latency, success/failure, and (for search)
    hit count into the metrics buffer. On exception, the entry is
    recorded with ``success=False`` + ``error_type`` set to the
    exception class name, and the exception is RE-RAISED so the
    outer try/except in ``_BackendAdapter.search/add`` still catches
    it (preserving the adapter's "never raise" contract -- threat
    T-67-03-adapter).

    Usage::

        with _memory_op_capture("search") as cap:
            out = backend._raw_search(...)
            cap.hit_count = len(out)
        # entry recorded with success=True, hit_count=len(out)

    Args:
        op_type: ``"search"`` or ``"add"``.

    Yields:
        A :class:`_CaptureState` instance. Set ``cap.hit_count`` before
        normal exit (search only; add leaves it at 0).
    """
    started_at_iso = _now_iso_utc()
    t0 = time.perf_counter()
    state = _CaptureState()
    success = True
    error_type: str | None = None

    try:
        yield state
    except BaseException as exc:
        # BaseException so we also capture KeyboardInterrupt /
        # SystemExit -- they're rare in production but the metric
        # should still record the failure. The exception is re-raised
        # so the adapter's outer try/except still applies.
        success = False
        error_type = type(exc).__name__
        raise
    finally:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        entry = MemoryOpMetricEntry(
            op_type=op_type,
            started_at_iso=started_at_iso,
            duration_ms=duration_ms,
            success=success,
            hit_count=state.hit_count,
            error_type=error_type,
        )
        record_memory_op_entry(entry)


# ---------------------------------------------------------------------------
# Test-only helpers
# ---------------------------------------------------------------------------

def _reset_for_test() -> None:
    """Clear the buffer + reset the conflict counter. Test-only.

    Used by the autouse fixture in
    ``test_memory_backend_metrics.py`` to ensure tests do not leak
    state into each other. NOT for production use -- calling this in
    production would discard real metrics.

    Mirrors the Wave 0 pattern (``_reset_registry_cache`` in
    ``agent/registry_loader.py``).
    """
    global _CONFLICT_COUNT
    # Clear the buffer by appending to a fresh deque. MetricsBuffer has
    # no public ``clear()`` -- we replace the singleton instead.
    # NOTE: must reassign the module-level name, not mutate, because
    # MetricsBuffer's internal deque is not exposed for clearing.
    # Use a sentinel: append N placeholders to evict? No -- that would
    # leave N stale entries. Instead, rebind the module global.
    global _BUFFER
    _BUFFER = MetricsBuffer(maxlen=100)
    with _CONFLICT_LOCK:
        _CONFLICT_COUNT = 0
