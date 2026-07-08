"""Unit tests for ``agent.observability.memory_backend_metrics``.

Covers OBSRV-03 (memory backend metrics collector):
    - ``_memory_op_capture("search")`` happy path: hit_count + latency recorded
    - ``_memory_op_capture("add")`` happy path: success recorded, hit_count=0
    - ``_memory_op_capture`` exception path: entry still recorded with
      ``success=False`` + ``error_type`` populated, then exception propagates
    - ``record_conflict()`` increments a thread-safe counter
    - ``get_memory_backend_metrics()`` on empty buffer returns zeros (no
      ``StatisticsError``; Pitfall 1)
    - ``get_memory_backend_metrics()`` on full 100-entry buffer returns a
      sane p95 (within the expected range, not 0.0)
    - ``status`` field reflects whether any op has been recorded

References: Plan 67-03 Task 1 <behavior>; RESEARCH "Instrumentation Points
§OBSRV-03"; OBSRV-03 requirement spec.
"""

from __future__ import annotations

import pytest

from agent.observability.memory_backend_metrics import (
    MemoryOpMetricEntry,
    _memory_op_capture,
    _reset_for_test,
    get_memory_backend_metrics,
    record_conflict,
    record_memory_op_entry,
)


@pytest.fixture(autouse=True)
def _reset_buffer_between_tests():
    """Clear module-level buffer + counter before each test.

    Without this, test ordering would affect results (e.g. a test that
    appends 100 entries would leave the buffer full for the next test).
    """
    _reset_for_test()
    yield
    _reset_for_test()


class TestMemoryBackendMetrics:
    """OBSRV-03 collector unit tests."""

    def test_search_capture_records_entry_with_hit_count(self):
        """``_memory_op_capture("search")`` happy path records 1 entry with
        ``op_type="search"``, ``success=True``, ``hit_count`` from cap,
        ``error_type=None``, and a non-negative ``duration_ms``."""
        with _memory_op_capture("search") as cap:
            cap.hit_count = 3

        metrics = get_memory_backend_metrics()
        assert metrics["search_count"] == 1
        assert metrics["add_count"] == 0

        # The entry itself is not directly inspectable via the public API,
        # but the buffer snapshot is queryable for verification.
        from agent.observability.memory_backend_metrics import _BUFFER
        snapshot = _BUFFER.snapshot()
        assert len(snapshot) == 1
        entry: MemoryOpMetricEntry = snapshot[0]
        assert entry.op_type == "search"
        assert entry.success is True
        assert entry.hit_count == 3
        assert entry.error_type is None
        assert entry.duration_ms >= 0.0

    def test_add_capture_records_success_with_zero_hits(self):
        """``_memory_op_capture("add")`` happy path records ``hit_count=0``
        (add has no hits) and ``success=True``."""
        with _memory_op_capture("add") as cap:
            # add has no hits; caller does not set hit_count
            assert cap.hit_count == 0

        from agent.observability.memory_backend_metrics import _BUFFER
        snapshot = _BUFFER.snapshot()
        assert len(snapshot) == 1
        entry: MemoryOpMetricEntry = snapshot[0]
        assert entry.op_type == "add"
        assert entry.success is True
        assert entry.hit_count == 0
        assert entry.error_type is None

        metrics = get_memory_backend_metrics()
        assert metrics["add_count"] == 1
        assert metrics["search_count"] == 0

    def test_capture_on_exception_records_failure_and_reraises(self):
        """When an exception is raised inside the ``with`` block, an entry
        is STILL recorded with ``success=False`` and ``error_type`` set to
        the exception class name, BEFORE the exception propagates."""
        with pytest.raises(RuntimeError, match="network"):
            with _memory_op_capture("search") as cap:
                cap.hit_count = 0
                raise RuntimeError("network")

        from agent.observability.memory_backend_metrics import _BUFFER
        snapshot = _BUFFER.snapshot()
        assert len(snapshot) == 1
        entry: MemoryOpMetricEntry = snapshot[0]
        assert entry.op_type == "search"
        assert entry.success is False
        assert entry.error_type == "RuntimeError"

        metrics = get_memory_backend_metrics()
        # 1 total op, 1 failure -> error_rate = 1.0
        assert metrics["search_count"] == 1
        assert metrics["error_rate"] == 1.0

    def test_record_conflict_increments_counter(self):
        """``record_conflict()`` increments the thread-safe counter.
        Three calls -> ``conflict_count == 3`` in the metrics snapshot."""
        assert get_memory_backend_metrics()["conflict_count"] == 0

        record_conflict()
        record_conflict()
        record_conflict()

        metrics = get_memory_backend_metrics()
        assert metrics["conflict_count"] == 3

    def test_empty_buffer_returns_zero_percentiles(self):
        """``get_memory_backend_metrics()`` on a fresh module returns zeros,
        NOT a ``StatisticsError``. This is RESEARCH Pitfall 1.

        Expected shape:
            search_p95_ms == 0.0
            add_p95_ms == 0.0
            search_count == 0
            add_count == 0
            error_rate == 0.0
            conflict_count == 0
            compaction_triggers == 0
            status == "no_data"
        """
        metrics = get_memory_backend_metrics()
        assert metrics["search_p95_ms"] == 0.0
        assert metrics["add_p95_ms"] == 0.0
        assert metrics["search_count"] == 0
        assert metrics["add_count"] == 0
        assert metrics["error_rate"] == 0.0
        assert metrics["conflict_count"] == 0
        assert metrics["compaction_triggers"] == 0
        assert metrics["status"] == "no_data"

    def test_full_buffer_p95_in_expected_range(self):
        """100 search entries with latencies [1..100]ms -> p95 is in the
        ~95ms range. ``statistics.quantiles`` interpolation yields ~95.05
        for n=100, n=100 quantiles, samples 1..100."""
        from agent.observability.memory_backend_metrics import _BUFFER

        for i in range(1, 101):
            _BUFFER.append(MemoryOpMetricEntry(
                op_type="search",
                started_at_iso="2026-07-08T00:00:00+00:00",
                duration_ms=float(i),
                success=True,
                hit_count=0,
                error_type=None,
            ))

        metrics = get_memory_backend_metrics()
        assert metrics["search_count"] == 100
        # statistics.quantiles([1..100], n=100)[94] -> ~95.05
        # Allow some interpolation slack but require > 90 (sanity check
        # that p95 is NOT 0.0 or stuck at the median).
        assert metrics["search_p95_ms"] > 90.0
        assert metrics["search_p95_ms"] < 100.0

    def test_status_reflects_ops_recorded(self):
        """``status`` is ``"no_data"`` when buffer is empty, ``"ok"`` once
        at least one op (search or add) has been recorded."""
        assert get_memory_backend_metrics()["status"] == "no_data"

        with _memory_op_capture("add"):
            pass

        assert get_memory_backend_metrics()["status"] == "ok"

    def test_record_memory_op_entry_appends_directly(self):
        """``record_memory_op_entry`` is the low-level append primitive.
        Calling it directly (without the context manager) appends one
        entry to the buffer."""
        record_memory_op_entry(MemoryOpMetricEntry(
            op_type="search",
            started_at_iso="2026-07-08T00:00:00+00:00",
            duration_ms=12.5,
            success=True,
            hit_count=2,
            error_type=None,
        ))

        metrics = get_memory_backend_metrics()
        assert metrics["search_count"] == 1
