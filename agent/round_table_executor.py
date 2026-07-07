"""INFRA-04 — per-roundId asyncio.Lock registry for round-table serial enforcement.

This module enforces the hard serial-execution constraint of the v11.0 PoC
expert-agents system: **one panelist, one turn, sequential `await`**. Any
second concurrent ``get_agent_opinion`` call for the same ``roundId`` is
rejected with 429 + MEMORY.md citation, NOT queued.

Policy root
-----------
The serial constraint is locked by user-memory policy
``feedback-glm-overload-reduce-concurrency.md``:

    global_concurrency 已是 1(从 5→3→1);concurrency==1 后别再重启,
    让 4-key rotation + 3-strike early-abort 自动工作

Hermes enforces ``concurrency==1`` at the turn level via this per-roundId
``asyncio.Lock``; the round-table runtime therefore composes safely with
the GLM 4-key rotation logic in the underlying model client.

DISTINCT FROM ``agent/glm_concurrency_guard.py``
------------------------------------------------
``glm_concurrency_guard`` uses a sync ``Semaphore`` to throttle
**blocking SDK calls** dispatched inside ``ThreadPoolExecutor`` workers
(see its module docstring, lines 11-15). That is a *different layer* from
this module's ``asyncio.Lock``:

- ``glm_concurrency_guard``  — API-call-level throttling (max N in-flight
                               HTTP requests to ``*.bigmodel.cn``)
- ``round_table_executor``   — turn-level ordering (no two
                               ``get_agent_opinion`` calls for the same
                               ``roundId`` may overlap)

The two layers COMPOSE — a correctly-serialized round table still goes
through ``glm_concurrency_guard`` on every actual LLM call. Do NOT
collapse them into one primitive (RESEARCH.md "Don't Hand-Roll" table).

Acceptance contract: SC#4 of ROADMAP Phase 52
---------------------------------------------
- Concurrent second ``get_agent_opinion`` for the same ``roundId`` is
  rejected with 429 + literal substring
  ``feedback-glm-overload-reduce-concurrency.md``.
- Single sequential submission proceeds and returns the panelist opinion.
- Different ``roundId`` values use independent locks (no cross-round
  false positive).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Module-level lock registry ──────────────────────────────────────────────
# One asyncio.Lock per roundId. Lives in the FastMCP event loop. Lazily
# created on first ``acquire_round_or_reject`` call for a given roundId.
_ROUND_LOCKS: dict[str, asyncio.Lock] = {}

# Guard around the registry itself — prevents two coroutines from racing
# on get-or-create for the same roundId. Held only for the dict mutation,
# never for the lifetime of the per-roundId lock.
_ROUND_LOCKS_GUARD = asyncio.Lock()


async def _get_or_create_round_lock(round_id: str) -> asyncio.Lock:
    """Return the per-``round_id`` ``asyncio.Lock``, creating it if absent.

    The registry mutation is guarded by ``_ROUND_LOCKS_GUARD`` so that two
    coroutines acquiring the same roundId for the first time do not race
    on ``dict.__setitem__``. The guard is released before the per-roundId
    lock is acquired, so it never blocks subsequent unrelated roundIds.
    """
    async with _ROUND_LOCKS_GUARD:
        if round_id not in _ROUND_LOCKS:
            _ROUND_LOCKS[round_id] = asyncio.Lock()
        return _ROUND_LOCKS[round_id]


def _serial_violation_response(round_id: str) -> str:
    """SC#4: build the 429 serial-violation JSON response.

    The literal substring ``feedback-glm-overload-reduce-concurrency.md``
    is load-bearing — SC#4 acceptance contract requires the response to
    cite the MEMORY.md policy file by name so operators can trace the
    serial constraint back to its policy root.
    """
    return json.dumps(
        {
            "error": "serial_violation",
            "status": 429,
            "round_id": round_id,
            "message": (
                "Concurrent get_agent_opinion for the same roundId is "
                "rejected. Hermes enforces 1 panelist 1 turn sequential "
                "execution by design (global concurrency==1; GLM 4-key "
                "rotation compatible). See MEMORY.md "
                "feedback-glm-overload-reduce-concurrency.md."
            ),
        },
        indent=2,
    )


async def acquire_round_or_reject(round_id: str) -> Optional[asyncio.Lock]:
    """Try to acquire the per-``round_id`` lock. Return ``None`` if contended.

    SC#4 mandates **rejection** of concurrent submissions, NOT queueing.
    Under asyncio cooperative scheduling, the check-then-acquire pattern
    is safe AS LONG AS no ``await`` happens between ``lock.locked()``
    and ``await lock.acquire()`` — no other coroutine can run in that
    window. (See RESEARCH.md Pitfall #2 "TOCTOU race in check-then-acquire
    lock pattern".)

    Returns:
        The acquired ``asyncio.Lock`` on success (caller MUST release it
        via ``release_round_lock`` or direct ``lock.release()`` in a
        ``finally`` block), or ``None`` if a concurrent call already holds
        the lock for this ``round_id``.
    """
    lock = await _get_or_create_round_lock(round_id)
    # Check-then-acquire. No `await` between these two lines — safe under
    # asyncio cooperative scheduling.
    if lock.locked():
        logger.info(
            "round_table_executor: rejected concurrent acquire for roundId=%s",
            round_id,
        )
        return None
    await lock.acquire()
    return lock


async def release_round_lock(round_id: str) -> None:
    """Release the per-``round_id`` lock if it is currently held.

    Symmetric helper for ``acquire_round_or_reject``. Direct
    ``lock.release()`` from the caller also works — this helper exists
    so call sites can pair ``acquire_round_or_reject`` /
    ``release_round_lock`` for readability.

    Logs a warning if the lock is missing or already released (defensive
    — indicates a double-release bug in the caller).
    """
    lock = _ROUND_LOCKS.get(round_id)
    if lock is None:
        logger.warning(
            "round_table_executor: release_round_lock called for unknown "
            "roundId=%s (never acquired?)",
            round_id,
        )
        return
    if not lock.locked():
        logger.warning(
            "round_table_executor: release_round_lock called for roundId=%s "
            "but lock is not held (double release?)",
            round_id,
        )
        return
    lock.release()
