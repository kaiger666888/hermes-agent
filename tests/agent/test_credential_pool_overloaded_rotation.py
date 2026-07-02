"""Tests for non-marking rotation on FailoverReason.overloaded.

Background: 2026-07-02 incident — when the overloaded branch in
``recover_with_credential_pool`` called ``pool.mark_exhausted_and_rotate``,
each 1305 ("model capacity exceeded") permanently marked one GLM key
``STATUS_EXHAUSTED``.  After 4× 1305 across a 4-key pool, all keys were
dead and rotation silently became a no-op, surfacing "model provider
failed after retries" to the user even though the keys themselves were
fine.

Fix: ``CredentialPool.rotate_to_next()`` advances ``_current_id`` to the
next available entry WITHOUT touching ``last_status``.  The overloaded
branch in ``recover_with_credential_pool`` calls ``rotate_to_next``;
billing (402) and rate_limit (429) keep calling
``mark_exhausted_and_rotate``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent.credential_pool import (
    STATUS_EXHAUSTED,
    STRATEGY_ROUND_ROBIN,
    CredentialPool,
    PooledCredential,
)
from agent.error_classifier import FailoverReason


# ---------------------------------------------------------------------------
# Helpers — real pool construction (no MagicMock for the pool itself)
# ---------------------------------------------------------------------------

def _make_real_pool(
    n_entries: int,
    monkeypatch,
    *,
    strategy: str = STRATEGY_ROUND_ROBIN,
) -> tuple[CredentialPool, list[PooledCredential]]:
    """Build a real CredentialPool without touching disk.

    ``_persist`` is stubbed so the test never writes to ~/.hermes/auth.json.
    The first entry is pre-selected as current so ``rotate_to_next`` has a
    concrete entry to rotate away from.

    Strategy defaults to ROUND_ROBIN because the default FILL_FIRST always
    re-selects the lowest-priority entry — a no-op for rotation. Multi-key
    GLM setups that want rotation on 1305 storms use round_robin.
    """
    # Stub out _persist so the test doesn't write to ~/.hermes/auth.json
    monkeypatch.setattr(CredentialPool, "_persist", lambda self: None)
    entries = [
        PooledCredential(
            provider="zai",
            id=f"key-{i}",
            label=f"key-{i}",
            auth_type="api_key",
            priority=i,
            source=f"manual:test{i}",
            access_token=f"tok-{i}",
        )
        for i in range(n_entries)
    ]
    pool = CredentialPool("zai", entries)
    pool._strategy = strategy
    # Force-select the first entry so current() is non-None for rotation tests
    pool._current_id = entries[0].id if entries else None
    return pool, entries


# ---------------------------------------------------------------------------
# Pool-level tests for CredentialPool.rotate_to_next
# ---------------------------------------------------------------------------

class TestRotateToNext:
    """Verify rotate_to_next advances _current_id without marking exhausted."""

    def test_overloaded_rotation_leaves_last_status_untouched(self, monkeypatch):
        """Test 1: rotate_to_next must NOT mutate last_status / last_error_*."""
        pool, entries = _make_real_pool(3, monkeypatch)
        original_id = entries[0].id
        assert pool.current() is not None
        assert pool.current().id == original_id

        next_entry = pool.rotate_to_next()

        # Must return a DIFFERENT entry
        assert next_entry is not None
        assert next_entry.id != original_id

        # The just-rotated-away entry must remain unmarked
        original_after = next(e for e in pool.entries() if e.id == original_id)
        assert original_after.last_status is None
        assert original_after.last_error_code is None
        assert original_after.last_error_reason is None

    def test_rotate_to_next_cycles_through_distinct_entries(self, monkeypatch):
        """Test 2: in a 3-entry pool, each rotation yields a DIFFERENT entry.

        The pool does NOT give up after one cycle — that's by design. The
        ezx 3-strike abort at the conversation-loop level terminates the
        retry sequence; the pool itself keeps offering alternatives so
        multi-key setups survive transient capacity storms.

        What this test verifies: rotate_to_next never immediately re-selects
        the entry it just rotated away from (no tight A->A loop). Across
        several rotations, the just-rotated-away entry is always excluded.
        """
        pool, entries = _make_real_pool(3, monkeypatch)
        seen_ids = []
        prev_id = entries[0].id
        for _ in range(6):
            nxt = pool.rotate_to_next()
            assert nxt is not None, "3-entry round_robin pool must always have an alternative"
            assert nxt.id != prev_id, (
                f"rotate_to_next re-selected the just-rotated-away entry "
                f"{prev_id} — tight loop bug"
            )
            seen_ids.append(nxt.id)
            prev_id = nxt.id
        # Across 6 rotations on a 3-entry pool, we should have visited all
        # 3 entries at least once (round_robin distribution).
        assert len(set(seen_ids)) == 3

    def test_rotate_to_next_empty_pool_returns_none(self, monkeypatch):
        """Test 3: 0-entry pool → rotate_to_next returns None."""
        pool, _entries = _make_real_pool(0, monkeypatch)
        assert pool.rotate_to_next() is None

    def test_rotate_to_next_single_entry_returns_none(self, monkeypatch):
        """Test 4: 1-entry pool → rotate_to_next returns None (no alternative).

        _select_unlocked would re-pick the same entry, but the
        ``next_entry.id == previous_id`` guard catches it.
        """
        pool, _entries = _make_real_pool(1, monkeypatch)
        assert pool.rotate_to_next() is None


# ---------------------------------------------------------------------------
# Integration tests for recover_with_credential_pool (MagicMock pool)
# ---------------------------------------------------------------------------

def _make_agent_with_mock_pool(pool_entries: int = 3):
    """Mirror _make_agent_with_pool from test_credential_pool_routing.py.

    Both ``mark_exhausted_and_rotate`` AND ``rotate_to_next`` are MagicMock
    objects — the test asserts which one was called. This isolates the
    branch-selection logic from real pool internals.
    """
    from run_agent import AIAgent

    # Suppress AIAgent.__init__ side effects
    AIAgent_init = AIAgent.__init__
    AIAgent.__init__ = lambda self, **kw: None  # type: ignore[assignment]
    try:
        agent = AIAgent()
    finally:
        AIAgent.__init__ = AIAgent_init  # type: ignore[assignment]

    entries = []
    for i in range(pool_entries):
        e = MagicMock(name=f"entry_{i}")
        e.id = f"cred-{i}"
        entries.append(e)

    pool = MagicMock()
    pool.has_credentials.return_value = True
    pool.provider = "zai"  # match agent.provider to bypass mismatch guard
    pool.mark_exhausted_and_rotate = MagicMock(return_value=None)
    pool.rotate_to_next = MagicMock(return_value=None)
    pool.current = MagicMock(return_value=None)

    agent._credential_pool = pool
    agent._swap_credential = MagicMock()
    agent.provider = "zai"
    agent.base_url = "https://api.bigmodel.cn"
    agent.log_prefix = ""

    return agent, pool, entries


class TestRecoverWithCredentialPoolOverloaded:
    """Verify the overloaded branch in recover_with_credential_pool."""

    def test_overloaded_does_not_call_mark_exhausted_and_rotate(self):
        """Test 5: overloaded must use rotate_to_next, NOT mark_exhausted_and_rotate."""
        from agent.agent_runtime_helpers import recover_with_credential_pool

        agent, pool, _entries = _make_agent_with_mock_pool(3)
        recover_with_credential_pool(
            agent,
            status_code=503,
            has_retried_429=False,
            classified_reason=FailoverReason.overloaded,
        )
        pool.mark_exhausted_and_rotate.assert_not_called()
        pool.rotate_to_next.assert_called_once_with()

    def test_overloaded_rotates_and_swaps(self):
        """Test 6: when rotate_to_next returns an entry, swap and return (True, False)."""
        from agent.agent_runtime_helpers import recover_with_credential_pool

        agent, pool, entries = _make_agent_with_mock_pool(3)
        pool.rotate_to_next.return_value = entries[1]

        recovered, retried = recover_with_credential_pool(
            agent,
            status_code=503,
            has_retried_429=False,
            classified_reason=FailoverReason.overloaded,
        )
        assert recovered is True
        assert retried is False
        agent._swap_credential.assert_called_once_with(entries[1])

    def test_overloaded_pool_cycled_returns_false(self):
        """Test 7: when rotate_to_next returns None, return (False, has_retried_429)."""
        from agent.agent_runtime_helpers import recover_with_credential_pool

        agent, pool, _entries = _make_agent_with_mock_pool(3)
        pool.rotate_to_next.return_value = None

        recovered, retried = recover_with_credential_pool(
            agent,
            status_code=503,
            has_retried_429=True,  # pass True in, expect True out
            classified_reason=FailoverReason.overloaded,
        )
        assert recovered is False
        assert retried is True  # unchanged
        agent._swap_credential.assert_not_called()

    def test_regression_rate_limit_second_strike_still_marks_exhausted(self):
        """Test 8: rate_limit with has_retried_429=True must call mark_exhausted_and_rotate."""
        from agent.agent_runtime_helpers import recover_with_credential_pool

        agent, pool, entries = _make_agent_with_mock_pool(3)
        # First-strike guard: current entry is NOT pre-exhausted
        current_entry = MagicMock()
        current_entry.last_status = None
        pool.current = MagicMock(return_value=current_entry)
        pool.mark_exhausted_and_rotate.return_value = entries[1]

        recover_with_credential_pool(
            agent,
            status_code=429,
            has_retried_429=True,
            classified_reason=FailoverReason.rate_limit,
        )
        pool.mark_exhausted_and_rotate.assert_called_once_with(
            status_code=429, error_context=None,
        )
        pool.rotate_to_next.assert_not_called()

    def test_regression_billing_still_marks_exhausted(self):
        """Test 9: billing (402) must call mark_exhausted_and_rotate."""
        from agent.agent_runtime_helpers import recover_with_credential_pool

        agent, pool, entries = _make_agent_with_mock_pool(3)
        pool.mark_exhausted_and_rotate.return_value = entries[1]

        recover_with_credential_pool(
            agent,
            status_code=402,
            has_retried_429=False,
            classified_reason=FailoverReason.billing,
        )
        pool.mark_exhausted_and_rotate.assert_called_once_with(
            status_code=402, error_context=None,
        )
        pool.rotate_to_next.assert_not_called()


# ---------------------------------------------------------------------------
# End-to-end behavioral test with a REAL pool
# ---------------------------------------------------------------------------

class TestRealPoolOverloadedRotation:
    """Codifies the exact 2026-07-02 incident scenario.

    4 consecutive 1305s across a 4-key GLM pool:
    * NO key may be marked STATUS_EXHAUSTED (the bug)
    * Rotation happens (each call swaps to a different key)
    * The conversation-loop-level ezx 3-strike abort handles termination;
      the pool itself keeps offering alternatives so multi-key setups
      survive transient capacity storms without manual cleanup.
    """

    def test_four_consecutive_1305s_no_key_marked_exhausted(self, monkeypatch):
        from agent.agent_runtime_helpers import recover_with_credential_pool

        monkeypatch.setattr(CredentialPool, "_persist", lambda self: None)
        entries = [
            PooledCredential(
                provider="zai",
                id=f"glm-key-{i}",
                label=f"glm-key-{i}",
                auth_type="api_key",
                priority=i,
                source=f"manual:incident2026{i}",
                access_token=f"tok-{i}",
            )
            for i in range(4)
        ]
        pool = CredentialPool("zai", entries)
        pool._strategy = STRATEGY_ROUND_ROBIN
        pool._current_id = entries[0].id

        # Agent stub: track which credential is "current" via _swap_credential
        agent = MagicMock()
        agent._credential_pool = pool
        agent.provider = "zai"
        agent.base_url = "https://api.bigmodel.cn"
        swapped_to = []

        def _swap(new_entry):
            pool._current_id = new_entry.id
            swapped_to.append(new_entry.id)
        agent._swap_credential = _swap
        agent.log_prefix = ""

        # Simulate 4 consecutive 1305s. In production the conversation loop's
        # ezx 3-strike abort (turn_retry_state.consecutive_overloaded >= 3)
        # terminates after the 3rd — here we bound at 4 to verify pool health.
        results = []
        for _ in range(4):
            recovered, retried = recover_with_credential_pool(
                agent,
                status_code=503,  # 1305 maps to overloaded
                has_retried_429=False,
                classified_reason=FailoverReason.overloaded,
            )
            results.append((recovered, retried))

        # Assertion 1 (THE BUG): NONE of the 4 entries may be STATUS_EXHAUSTED.
        # Before the fix, each 1305 killed one key; after 4× 1305 all keys
        # were dead and rotation silently died.
        for entry in pool.entries():
            assert entry.last_status != STATUS_EXHAUSTED, (
                f"entry {entry.id} was marked exhausted — this is the bug! "
                f"last_status={entry.last_status!r}"
            )
            assert entry.last_error_code is None
            assert entry.last_error_reason is None

        # Assertion 2: rotation actually happened — at least 3 distinct keys
        # were swapped to across the 4 calls (round_robin distribution).
        assert len(swapped_to) == 4, "all 4 calls should have rotated successfully"
        assert len(set(swapped_to)) >= 3, (
            f"expected round_robin to distribute across >=3 keys, got {set(swapped_to)}"
        )

        # Assertion 3: all 4 calls returned (True, False) — pool kept
        # offering alternatives. In production, the ezx 3-strike abort at
        # the conversation-loop level surfaces "GLM model overloaded" after
        # the 3rd consecutive 1305; the pool itself never gives up on a
        # healthy multi-key setup.
        assert all(rec for rec, _ in results), (
            "healthy 4-key pool should always find an alternative — "
            "termination is the conversation loop's job (ezx 3-strike)"
        )

    def test_overloaded_yields_when_pool_has_no_alternative(self, monkeypatch):
        """Complement to the 4-key test: when the pool genuinely has no
        NEW entry (single-entry pool, or all-but-one exhausted), the
        overloaded branch must return (False, has_retried_429) so the
        caller surfaces a clean error. This is the must-have truth #2
        scenario — a pool with only one live entry cannot rotate.
        """
        from agent.agent_runtime_helpers import recover_with_credential_pool

        monkeypatch.setattr(CredentialPool, "_persist", lambda self: None)
        # Single-entry pool — no alternative to rotate to
        entries = [
            PooledCredential(
                provider="zai",
                id="only-key",
                label="only-key",
                auth_type="api_key",
                priority=0,
                source="manual:single",
                access_token="tok",
            )
        ]
        pool = CredentialPool("zai", entries)
        pool._strategy = STRATEGY_ROUND_ROBIN
        pool._current_id = entries[0].id

        agent = MagicMock()
        agent._credential_pool = pool
        agent.provider = "zai"
        agent.base_url = "https://api.bigmodel.cn"
        agent._swap_credential = MagicMock()
        agent.log_prefix = ""

        recovered, retried = recover_with_credential_pool(
            agent,
            status_code=503,
            has_retried_429=False,
            classified_reason=FailoverReason.overloaded,
        )
        assert recovered is False, (
            "single-entry pool must yield (False) — no alternative to rotate to"
        )
        agent._swap_credential.assert_not_called()
        # And the single key must NOT be marked exhausted
        assert pool.entries()[0].last_status is None
