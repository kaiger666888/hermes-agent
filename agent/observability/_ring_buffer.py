"""Shared ring-buffer primitive for Phase 67 observability collectors.

Provides :class:`MetricsBuffer` -- a generic, bounded, thread-safe buffer
backed by :class:`collections.deque(maxlen=...)`. Used by the OBSRV-01,
OBSRV-02, and OBSRV-03 collectors (Plans 67-01/02/03) to retain the last
``N`` metric entries for on-demand snapshotting.

Design notes
------------
* ``deque(maxlen=N)`` auto-evicts the oldest entry on append beyond ``N``,
  so we never need to hand-roll eviction logic (RESEARCH "Don't Hand-Roll
  table, row 1).
* Although ``deque.append`` is CPython-atomic under the GIL, the iteration
  performed by ``list(deque)`` during ``snapshot()`` is NOT atomic: a GIL
  switch mid-iteration can yield a torn read (RESEARCH Pitfall 2).
  We therefore guard BOTH ``append`` and ``snapshot`` with the same
  ``threading.Lock``. The lock is held for microseconds (O(1) deque ops),
  so contention is negligible.
* ``snapshot()`` returns a fresh ``list`` copy each call -- downstream
  consumers can mutate it freely without affecting the buffer. Tested by
  ``test_snapshot_returns_copy``.
* The buffer is generic (``MetricsBuffer[T]``): collectors parameterize
  ``T`` with their own ``@dataclass(slots=True)`` entry types.

Threat register
---------------
Mitigates:
* T-67-01-thread (Tampering: concurrent append+snapshot) -- via the
  ``threading.Lock`` acquired on both ``append`` and ``snapshot``.
* T-67-01-mem (Denial of Service: unbounded growth) -- via ``deque(maxlen=N)``;
  the bound is set at construction time and cannot be exceeded by definition.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Generic, TypeVar

__all__ = ["MetricsBuffer"]

# Generic entry type. Bound by the collector -- e.g.
# ``MetricsBuffer[RoundTableMetricEntry]`` for OBSRV-02.
T = TypeVar("T")

#: Default ring size. Matches CONTEXT.md decision G3 ("count-based window,
#: last 100 ops"). Collectors may override per-buffer if needed.
DEFAULT_MAXLEN = 100


class MetricsBuffer(Generic[T]):
    """Thread-safe bounded ring buffer for metric entries.

    Parameters
    ----------
    maxlen:
        Maximum number of entries retained. Once the buffer is full, each
        subsequent :meth:`append` silently drops the oldest entry. Defaults
        to :data:`DEFAULT_MAXLEN` (100) per Phase 67 CONTEXT.md G3.

    Examples
    --------
    >>> buf: MetricsBuffer[int] = MetricsBuffer(maxlen=3)
    >>> buf.append(1); buf.append(2); buf.append(3)
    >>> buf.snapshot()
    [1, 2, 3]
    >>> buf.append(4)  # 1 is evicted
    >>> buf.snapshot()
    [2, 3, 4]
    """

    __slots__ = ("_buf", "_lock", "_maxlen")

    def __init__(self, maxlen: int = DEFAULT_MAXLEN) -> None:
        if maxlen < 1:
            raise ValueError(
                f"MetricsBuffer maxlen must be >= 1 (got {maxlen})"
            )
        self._maxlen = maxlen
        # deque(maxlen=N) auto-evicts the oldest entry on append beyond N.
        # This is the bounded-by-construction guarantee (T-67-01-mitigate-mem).
        self._buf: deque[T] = deque(maxlen=maxlen)
        # Single lock guards both append and snapshot. Held for microseconds
        # only (deque ops are O(1)), so contention is negligible even under
        # 10-thread x 1000-append workloads (see test_thread_safety_concurrent_append).
        self._lock = threading.Lock()

    def append(self, entry: T) -> None:
        """Append ``entry`` to the buffer. Thread-safe.

        If the buffer is full, the oldest entry is silently dropped.
        """
        with self._lock:
            self._buf.append(entry)

    def snapshot(self) -> list[T]:
        """Return a point-in-time copy of the buffer contents. Thread-safe.

        The returned list is a fresh copy -- mutating it does not affect
        subsequent appends or snapshots. Order is oldest-to-newest.
        """
        with self._lock:
            # list(deque) iterates; we hold the lock to prevent a torn read
            # if another thread appends mid-iteration (RESEARCH Pitfall 2).
            return list(self._buf)

    def __len__(self) -> int:
        """Current entry count. Bounded by ``maxlen``."""
        with self._lock:
            return len(self._buf)

    @property
    def maxlen(self) -> int:
        """The configured maximum entry count (read-only)."""
        return self._maxlen
