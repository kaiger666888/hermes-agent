"""Phase 58 THROTTLE-01: per-task RPM token bucket.

Classic leaky-bucket rate limiter keyed by auxiliary task name. Each task
(``round_table_opinion``, ``memory_compaction``, ``fitness_judge``,
``bias_canary_claim_check``, ``memory_comparator``) gets its own refillable
token bucket. ``acquire_slot(task)`` blocks until a slot is available;
``try_acquire_slot(task)`` is the non-blocking variant (returns False when
the bucket is empty).

Policy context
--------------
This module is the structural fix for the GLM 429 retry storm documented
in ``.planning/research/v11-poc-eval/smoke-test-report.md §3.1`` (5x z.ai
retries → fallback to ``open.bigmodel.cn/api/anthropic``, total 490s wall
clock). Phase 57 (ENDPOINT-01) removed the cause of the 5x retries by
routing long prompts to the anthropic-compat endpoint; Phase 58 removes
the v11.0 ``asyncio.sleep(2.5)`` "Strategy A" workaround by enforcing a
per-task RPM ceiling at the auxiliary call layer instead.

MEMORY.md ``feedback-glm-overload-reduce-concurrency.md`` is the root
policy: cap per-task RPM *before* it hits the GLM single-key ceiling.
Default 30 RPM/task is well under the typical 60 RPM/key × 4-key pool.

Algorithm (CONTEXT.md decisions #1-#5)
--------------------------------------
1. Each task name maps to one ``TokenBucket`` (lazy-init on first call).
2. Capacity = RPM (one burst token per request per minute of allowed rate).
3. Refill: 1 token every ``60 / RPM`` seconds (continuous, fractional tokens
   allowed — classic token bucket).
4. Default RPM = 30 (configurable per task via ``auxiliary.{task}.rpm``).
5. Misconfiguration (``rpm <= 0`` or non-numeric) falls back to default
   with a warning — never infinite-loops the caller.

Configuration
-------------
Reads ``auxiliary.{task}.rpm`` from ``cli-config.yaml`` via the existing
``agent.auxiliary_client._get_auxiliary_task_config`` helper (lazy import
inside ``_get_or_create_bucket`` to avoid a circular import —
``auxiliary_client`` imports ``glm_throttle`` lazily too).

Integration point: ``agent.auxiliary_client.call_llm`` calls
``acquire_slot(task)`` BEFORE Phase 57 endpoint routing runs, so both
the z.ai (short prompt) and anthropic-compat (long prompt) routes count
against the same per-task bucket (CONTEXT.md decision #8).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger(__name__)

# Load-bearing default per CONTEXT.md decision #3: "well under GLM single-key
# RPM ceiling". The 4-key pool can theoretically serve 240 RPM steady-state,
# but burst is the failure mode — 30/task keeps a 9-agent round table (9
# panelist calls in rapid succession) comfortably under burst ceiling even
# when gateway traffic shares the same key pool.
DEFAULT_RPM: int = 30


@dataclass
class TokenBucket:
    """Classic leaky-bucket counter.

    Fields use ``float`` for ``available`` (fractional tokens accumulate
    during partial refill intervals) and ``last_refill_time`` (monotonic
    seconds — NEVER wall-clock ``time.time()`` which can jump on NTP sync).
    """

    capacity: int
    refill_interval_seconds: float
    available: float
    last_refill_time: float

    def refill(self, now: float) -> None:
        """Lazily add tokens based on elapsed time since ``last_refill_time``.

        Caps at ``capacity`` (a bucket never overflows past its burst size).
        Idempotent: calling with the same ``now`` twice is a no-op.
        """
        elapsed = now - self.last_refill_time
        if elapsed <= 0:
            return
        if self.refill_interval_seconds <= 0:
            # Defensive: a misconfigured bucket (refill_interval=0) would
            # divide by zero. Treat as "instant refill to capacity".
            self.available = float(self.capacity)
            self.last_refill_time = now
            return
        refilled = elapsed / self.refill_interval_seconds
        self.available = min(float(self.capacity), self.available + refilled)
        self.last_refill_time = now

    def try_acquire(self) -> bool:
        """Non-blocking acquire. Returns True + decrements if a token is
        available, False otherwise. Does NOT refill — caller must invoke
        :meth:`refill` first if it wants time-elapsed tokens counted.
        """
        if self.available >= 1.0:
            self.available -= 1.0
            return True
        return False


# Module-level registry (lazy-init pattern per CONTEXT.md "Claude's
# Discretion": in-memory dict keyed by task name). Single-writer (this
# module) + single-reader (call_llm) within the gateway process.
_BUCKETS: Dict[str, TokenBucket] = {}


def _resolve_rpm(task: str) -> int:
    """Read ``auxiliary.{task}.rpm`` from config, falling back to DEFAULT_RPM.

    Lazy-imports ``agent.auxiliary_client._get_auxiliary_task_config`` to
    avoid a circular import (``auxiliary_client`` lazy-imports this module
    inside ``call_llm``).

    Invalid values (``<= 0``, non-numeric) log a warning and return the
    default — never raise, never infinite-loop the caller (T-58-01-01
    mitigation in the threat register).
    """
    try:
        # Lazy import: auxiliary_client imports acquire_slot inside call_llm,
        # so a top-level import here would deadlock on first aux call.
        from agent.auxiliary_client import _get_auxiliary_task_config
        task_config = _get_auxiliary_task_config(task)
    except Exception as exc:  # noqa: BLE001 — config-load failure must not crash callers
        logger.warning(
            "glm_throttle: config lookup failed for task=%s: %s — "
            "using DEFAULT_RPM=%d",
            task, exc, DEFAULT_RPM,
        )
        return DEFAULT_RPM

    raw = task_config.get("rpm") if isinstance(task_config, dict) else None
    if raw is None:
        return DEFAULT_RPM
    try:
        rpm = int(raw)
    except (TypeError, ValueError) as exc:
        logger.warning(
            "glm_throttle: auxiliary.%s.rpm=%r is not an int (%s) — "
            "falling back to DEFAULT_RPM=%d",
            task, raw, exc, DEFAULT_RPM,
        )
        return DEFAULT_RPM
    if rpm <= 0:
        logger.warning(
            "glm_throttle: auxiliary.%s.rpm=%d <= 0 — falling back to "
            "DEFAULT_RPM=%d (negative/zero RPM would starve the bucket)",
            task, rpm, DEFAULT_RPM,
        )
        return DEFAULT_RPM
    return rpm


def _get_or_create_bucket(task: str) -> TokenBucket:
    """Lazy lookup: read from registry or construct a fresh bucket.

    Construction reads RPM via :func:`_resolve_rpm`; capacity is set to RPM
    (one burst token per minute of allowed rate) and refill_interval is
    ``60 / rpm`` seconds.
    """
    bucket = _BUCKETS.get(task)
    if bucket is not None:
        return bucket
    rpm = _resolve_rpm(task)
    now = time.monotonic()
    bucket = TokenBucket(
        capacity=rpm,
        refill_interval_seconds=60.0 / float(rpm),
        available=float(rpm),
        last_refill_time=now,
    )
    _BUCKETS[task] = bucket
    return bucket


def acquire_slot(task: str) -> None:
    """Blocking RPM acquire for *task*.

    Refills the bucket based on elapsed wall time, then tries to take a
    token. If empty, sleeps for the refill interval (so the next refill
    produces a token), then tries again. Returns ``None`` on success —
    callers do not need the return value, only the rate-limiting side
    effect.

    Used by ``auxiliary_client.call_llm`` (Phase 58 wire-in).
    """
    bucket = _get_or_create_bucket(task)
    while True:
        now = time.monotonic()
        bucket.refill(now)
        if bucket.try_acquire():
            return
        # Compute how long until the next whole token is available.
        deficit = 1.0 - bucket.available
        sleep_seconds = deficit * bucket.refill_interval_seconds
        # Clamp: never sleep negative (clock jitter) and never longer than
        # one full refill interval (the wait caps at "one token's worth").
        if sleep_seconds <= 0:
            sleep_seconds = 0.0
        elif sleep_seconds > bucket.refill_interval_seconds:
            sleep_seconds = bucket.refill_interval_seconds
        time.sleep(sleep_seconds)


def try_acquire_slot(task: str) -> bool:
    """Non-blocking RPM acquire for *task*.

    Same refill-then-try semantics as :func:`acquire_slot`, but returns
    ``False`` immediately when the bucket is empty (no sleep). Used by
    ``round_table_open`` (Phase 58-02 plan) to fail-fast when quota is
    exhausted rather than blocking the round-table dispatcher.
    """
    bucket = _get_or_create_bucket(task)
    bucket.refill(time.monotonic())
    return bucket.try_acquire()


def reset_for_testing() -> None:
    """Clear the bucket registry. Test-only — production callers must not
    invoke this (it would discard in-flight rate-limit state).

    Mirrors the pattern in ``agent/nous_rate_guard._reset_state_for_tests``
    (if present) and other Hermes modules with module-level singletons.
    """
    _BUCKETS.clear()
