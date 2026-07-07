"""INFRA-04 SC#4 — async unit tests for the per-roundId serial lock.

Acceptance contract coverage (Phase 52 INFRA-04 / SC#4):

- ``test_concurrent_submission_rejected`` — two concurrent
  ``acquire_round_or_reject`` calls for the same roundId: first wins,
  second returns ``None`` (NOT a queue, NOT a block).
- ``test_sequential_submission_succeeds`` — acquire → release → acquire
  the same roundId twice in a row: both succeed (lock is reusable, not
  stuck).
- ``test_429_message_cites_memory_md`` — ``_serial_violation_response``
  return value contains the literal substring
  ``feedback-glm-overload-reduce-concurrency.md`` (SC#4 hard requirement),
  plus ``"429"`` and ``"serial_violation"`` markers.
- ``test_different_roundids_use_different_locks`` — independent roundIds
  acquire concurrently (no false-positive cross-round rejection).

TDD note: this file is RED until Task 2 lands ``agent/round_table_executor.py``
with ``acquire_round_or_reject``, ``release_round_lock``, and
``_serial_violation_response``.

pytest-asyncio note: the project's pyproject.toml does NOT set
``asyncio_mode=auto`` (default is ``strict``), so every async test must
carry an explicit ``@pytest.mark.asyncio`` marker. See
``tests/test_trajectory_compressor.py`` for the canonical marker pattern.
"""

from __future__ import annotations

import asyncio

import pytest


class TestSerialEnforcement:
    """INFRA-04 SC#4 — per-roundId asyncio.Lock serial enforcement."""

    @pytest.mark.asyncio
    async def test_concurrent_submission_rejected(self):
        """SC#4: second concurrent acquire for same roundId returns None."""
        from agent.round_table_executor import (
            acquire_round_or_reject,
            release_round_lock,
        )

        lock1 = await acquire_round_or_reject("round-1")
        assert lock1 is not None, "first acquire must succeed"

        # Second concurrent acquire for the same roundId WITHOUT releasing
        # the first — must be rejected (return None), NOT queued/blocked.
        lock2 = await acquire_round_or_reject("round-1")
        assert lock2 is None, (
            "second concurrent acquire must return None (rejected, not queued)"
        )

        # Cleanup: release the first lock so subsequent tests see a clean slate.
        await release_round_lock("round-1")

    @pytest.mark.asyncio
    async def test_sequential_submission_succeeds(self):
        """SC#4: after release, the same roundId can be re-acquired (lock reusable)."""
        from agent.round_table_executor import (
            acquire_round_or_reject,
            release_round_lock,
        )

        # First acquire + release
        lock1 = await acquire_round_or_reject("round-2")
        assert lock1 is not None, "first acquire must succeed"
        await release_round_lock("round-2")

        # Second acquire on the same roundId — must succeed (lock not stuck)
        lock2 = await acquire_round_or_reject("round-2")
        assert lock2 is not None, (
            "second sequential acquire after release must succeed (lock not stuck)"
        )
        await release_round_lock("round-2")

    def test_429_message_cites_memory_md(self):
        """SC#4: 429 response message MUST cite MEMORY.md policy file by name."""
        from agent.round_table_executor import _serial_violation_response

        response_str = _serial_violation_response("round-x")

        # Load-bearing substring per SC#4 acceptance contract:
        # must literally reference the MEMORY.md policy filename.
        assert "feedback-glm-overload-reduce-concurrency.md" in response_str, (
            "429 response must cite MEMORY.md feedback-glm-overload-reduce-concurrency.md"
        )
        # Status code marker
        assert "429" in response_str, "response must mention status code 429"
        # Error code marker
        assert "serial_violation" in response_str, (
            "response must use the serial_violation error code"
        )

    @pytest.mark.asyncio
    async def test_different_roundids_use_different_locks(self):
        """SC#4: different roundIds acquire concurrently (no cross-round false positive)."""
        from agent.round_table_executor import (
            acquire_round_or_reject,
            release_round_lock,
        )

        # Acquire two different roundIds at the same time — both must succeed.
        lock_a = await acquire_round_or_reject("round-a")
        lock_b = await acquire_round_or_reject("round-b")
        assert lock_a is not None, "round-a acquire must succeed"
        assert lock_b is not None, (
            "round-b acquire must succeed even while round-a is held "
            "(different roundId → different lock)"
        )

        # Cleanup.
        await release_round_lock("round-a")
        await release_round_lock("round-b")
