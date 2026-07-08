"""Unit tests for ``agent.observability._ring_buffer.MetricsBuffer``.

Covers:
    - eviction: oldest entry dropped on append beyond maxlen
    - thread safety: concurrent append + snapshot cannot produce torn state
    - empty-buffer snapshot returns an empty list (no StatisticsError here --
      quantile math lives in the collector layer, not the buffer)
    - snapshot returns a COPY: mutating the returned list does not affect
      subsequent appends

References: Plan 67-01 Task 1 <behavior>; threat register T-67-01-thread
and T-67-01-mitigate (mitigated by the threading.Lock acquired on both
``append`` and ``snapshot``).
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from agent.observability._ring_buffer import MetricsBuffer


class TestMetricsBuffer:
    """SHARED tests for the ring-buffer primitive consumed by all 3 collectors."""

    def test_eviction_oldest_dropped(self) -> None:
        """MetricsBuffer(maxlen=100) silently evicts oldest on the 101st append."""
        buf: MetricsBuffer[int] = MetricsBuffer(maxlen=100)
        for i in range(101):
            buf.append(i)

        snap = buf.snapshot()
        assert len(snap) == 100
        # The 0th entry (oldest) was evicted; entries 1..100 are present.
        assert 0 not in snap
        assert 1 in snap
        assert 100 in snap
        assert len(buf) == 100

    def test_thread_safety_concurrent_append(self) -> None:
        """10 threads x 1000 appends on a MetricsBuffer(maxlen=100).

        After join:
            - len(buf) == 100 (never > maxlen -- no torn growth)
            - snapshot() returns exactly 100 entries (no duplicates, no holes)
        Validates threat T-67-01-thread mitigation: Lock on append+snapshot.
        """
        buf: MetricsBuffer[int] = MetricsBuffer(maxlen=100)

        def worker(thread_id: int) -> None:
            for j in range(1000):
                buf.append(thread_id * 10_000 + j)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(worker, tid) for tid in range(10)]
            for fut in futures:
                fut.result()

        snap = buf.snapshot()
        assert len(snap) == 100
        assert len(buf) == 100
        # All entries unique (no torn appends duplicated into the deque).
        assert len(set(snap)) == 100

    def test_snapshot_empty_buffer(self) -> None:
        """snapshot() on a fresh buffer returns [] (no error at this layer)."""
        buf: MetricsBuffer[int] = MetricsBuffer(maxlen=100)
        assert buf.snapshot() == []
        assert len(buf) == 0

    def test_snapshot_returns_copy(self) -> None:
        """Mutating the list returned by snapshot() must not affect the buffer.

        Otherwise a downstream consumer could clear the buffer by accident
        via ``snap.clear()``.
        """
        buf: MetricsBuffer[int] = MetricsBuffer(maxlen=100)
        buf.append(1)
        buf.append(2)

        snap = buf.snapshot()
        assert snap == [1, 2]
        # Mutate the snapshot list.
        snap.clear()
        snap.append(999)

        # Buffer is unaffected.
        next_snap = buf.snapshot()
        assert next_snap == [1, 2]
        assert len(buf) == 2

    def test_default_maxlen_is_100(self) -> None:
        """Default maxlen matches the Phase 67 CONTEXT.md G3 contract (100 entries)."""
        buf: MetricsBuffer[int] = MetricsBuffer()
        for i in range(150):
            buf.append(i)
        assert len(buf) == 100
        snap = buf.snapshot()
        # Oldest 50 evicted; newest 100 retained.
        assert snap[0] == 50
        assert snap[-1] == 149

    def test_concurrent_append_and_snapshot_interleaved(self) -> None:
        """snapshot() during concurrent appends never raises and never tears.

        One thread appends; another reads snapshots in a tight loop. Both
        must complete without exception; final length must be the maxlen.
        """
        buf: MetricsBuffer[int] = MetricsBuffer(maxlen=100)
        stop = threading.Event()
        errors: list[BaseException] = []

        def appender() -> None:
            try:
                i = 0
                while not stop.is_set():
                    buf.append(i)
                    i += 1
            except BaseException as exc:  # pragma: no cover - defensive
                errors.append(exc)

        def snapshotter() -> None:
            try:
                while not stop.is_set():
                    snap = buf.snapshot()
                    # Snapshot length is bounded by maxlen by construction.
                    assert len(snap) <= 100
            except BaseException as exc:  # pragma: no cover - defensive
                errors.append(exc)

        appender_thread = threading.Thread(target=appender)
        snapshotter_thread = threading.Thread(target=snapshotter)
        appender_thread.start()
        snapshotter_thread.start()
        # Run the interleaved workload briefly.
        threading.Event().wait(0.1)
        stop.set()
        appender_thread.join(timeout=2.0)
        snapshotter_thread.join(timeout=2.0)

        assert errors == [], f"concurrent errors observed: {errors}"
        # Final state still consistent.
        assert len(buf) == 100
        assert len(buf.snapshot()) == 100
