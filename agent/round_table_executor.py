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
from pathlib import Path
from typing import Any, Optional

from agent import round_table_state as _rts

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

    Implementation note (CR-02 fix): the previous check-then-acquire form
    ``if lock.locked(): reject; else: await lock.acquire()`` was NOT atomic
    — ``await lock.acquire()`` is itself an await point that yields to the
    event loop, so a second coroutine could observe ``lock.locked() == False``
    between the first coroutine's check and its actual acquisition, then
    pass its own check and block forever on ``await lock.acquire()`` instead
    of being rejected with 429.

    The fix holds ``_ROUND_LOCKS_GUARD`` across BOTH the lookup AND the
    ``await lock.acquire()``. ``_ROUND_LOCKS_GUARD`` serializes all
    acquire_round_or_reject calls, so the check-and-acquire is atomic with
    respect to other dispatchers. The guard is held only for the
    microseconds needed to mutate the registry and acquire the per-roundId
    lock — it does not gate any LLM/IO work — so it does not bottleneck
    throughput.

    Returns:
        The acquired ``asyncio.Lock`` on success (caller MUST release it
        via ``release_round_lock`` or direct ``lock.release()`` in a
        ``finally`` block), or ``None`` if a concurrent call already holds
        the lock for this ``round_id``.
    """
    # Hold _ROUND_LOCKS_GUARD across check + acquire so the check-then-acquire
    # is atomic w.r.t. other dispatchers. Without this, the await point inside
    # lock.acquire() yields to the event loop and a racing coroutine can pass
    # the lock.locked() check and then block forever (CR-02).
    async with _ROUND_LOCKS_GUARD:
        if round_id not in _ROUND_LOCKS:
            _ROUND_LOCKS[round_id] = asyncio.Lock()
        lock = _ROUND_LOCKS[round_id]
        if lock.locked():
            logger.info(
                "round_table_executor: rejected concurrent acquire for roundId=%s",
                round_id,
            )
            return None
        # Inside the guard — no other coroutine can acquire this lock between
        # the locked() check above and this acquire() call.
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


# ── Phase 58 THROTTLE-02: per-round-table TPM budget ────────────────────
# The lock primitives above enforce per-roundId async serialization
# (Phase 52 INFRA-04 SC#4). The helpers below enforce per-round-table
# TOKEN budget — a DIFFERENT concern: a serialized round table can still
# consume unbounded tokens if a panelist generates a 50K-token response
# or retries inflate cost.
#
# Budget thresholds per .planning/phases/58-rpm-throttling/58-CONTEXT.md
# decisions #5-#6:
#   < 2× expected next call → budget_warning event (proceed)
#   < 1× expected next call → budget_exceeded event (abort)
#
# Pricing constants + record_token_usage / append_event live in
# ``agent.round_table_state`` (single source of truth for state-file
# schema). These helpers are the budget DECISION layer; the state module
# is the budget ACCOUNTING layer.

DEFAULT_EXPECTED_NEXT_TOKENS: int = 5000
"""Conservative panelist call cost (Phase 58 THROTTLE-02 default).

Used by :func:`check_budget_before_turn` when the caller does not pass an
explicit ``expected_next_tokens``. The actual cost of a panelist call
varies (3-7K depending on prompt+response length); 5000 is the planning
estimate per .planning/research/v11-poc-eval/smoke-test-report.md §3.1.
"""


def check_budget_before_turn(
    state_path: Path,
    expected_next_tokens: int = DEFAULT_EXPECTED_NEXT_TOKENS,
) -> bool:
    """Return ``True`` if the round can proceed with another panelist call.

    Emits a ``budget_warning`` event to the state file's ``events`` array
    when ``remaining < 2 × expected_next_tokens`` (caller still proceeds).

    Emits a ``budget_exceeded`` event AND returns ``False`` when
    ``remaining < expected_next_tokens`` — the caller MUST abort the round
    (typically via ``round_table_state.abort_round_table(reason='budget_exceeded')``).

    Idempotent warning emission: ``append_event`` is called every time the
    threshold is crossed, so a round that lingers at the warning boundary
    may emit multiple warnings. That's intentional — operators want a
    complete threshold-crossing log for post-hoc analysis.

    Args:
        state_path: State file path (must already exist with ``tokenBudget``
            and ``tokensConsumed`` fields — i.e. opened via
            ``open_round_table`` post-Phase 58).
        expected_next_tokens: Estimated cost of the next panelist call.
            Defaults to :data:`DEFAULT_EXPECTED_NEXT_TOKENS` = 5000.

    Returns:
        True if the round can proceed; False if budget exhausted (caller
        MUST abort).
    """
    state = _rts._read_state_sync(state_path)
    budget = state.get("tokenBudget", _rts.DEFAULT_TOKEN_BUDGET)
    consumed = state.get("tokensConsumed", 0)
    remaining = int(budget) - int(consumed)
    threshold_warning = 2 * expected_next_tokens
    threshold_exceeded = expected_next_tokens

    if remaining < threshold_exceeded:
        _rts.append_event(state_path, {
            "type": "budget_exceeded",
            "threshold": 1.0,
            "remaining_tokens": remaining,
            "expected_next_tokens": expected_next_tokens,
            "timestamp": _rts._now_iso(),
        })
        logger.warning(
            "round_table budget_exceeded: budget=%d consumed=%d remaining=%d < %d",
            int(budget), int(consumed), remaining, expected_next_tokens,
        )
        return False
    if remaining < threshold_warning:
        _rts.append_event(state_path, {
            "type": "budget_warning",
            "threshold": 2.0,
            "remaining_tokens": remaining,
            "expected_next_tokens": expected_next_tokens,
            "timestamp": _rts._now_iso(),
        })
        logger.info(
            "round_table budget_warning: budget=%d consumed=%d remaining=%d < %d",
            int(budget), int(consumed), remaining, threshold_warning,
        )
    return True


def record_panelist_tokens(state_path: Path, tokens: int) -> dict[str, Any]:
    """Record actual token consumption for the just-completed panelist call.

    Thin delegation to :func:`round_table_state.record_token_usage` (the
    atomic read-modify-write lives there). This helper exists in the
    executor module so call sites can pair ``check_budget_before_turn`` /
    ``record_panelist_tokens`` for readability — both budget decisions
    and token accounting flow through the same module at the call site.

    Args:
        state_path: State file path.
        tokens: Total tokens (prompt + completion) consumed by the
            just-completed call. ``0`` is a no-op.

    Returns:
        The updated state dict.
    """
    return _rts.record_token_usage(state_path, tokens)
