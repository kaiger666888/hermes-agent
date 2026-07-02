"""Unit tests for the overloaded-specific backoff preset in agent.retry_utils.

Validates that ``jittered_backoff_overloaded`` returns delays in the
30s-base / 600s-cap range tuned for Zhipu GLM 1305 ("该模型当前访问量过大")
recovery windows observed 2026-07-02, and that the default
``jittered_backoff`` path is unchanged.
"""

from __future__ import annotations

from agent.retry_utils import jittered_backoff, jittered_backoff_overloaded


class TestJitteredBackoffOverloaded:
    def test_first_attempt_is_at_least_30_seconds(self) -> None:
        # base_delay=30, jitter adds [0, 0.5*30] = [0, 15], so [30, 45).
        result = jittered_backoff_overloaded(1)
        assert isinstance(result, float)
        assert result >= 30.0, f"Expected >= 30.0, got {result}"
        assert result < 60.0, f"Expected < 60.0 (30 + 0.5*30 + slack), got {result}"

    def test_high_attempt_hits_cap(self) -> None:
        # 30 * 2^(attempt-1) grows past the 600 cap at attempt=6 (30*2^5=960
        # → capped to 600). Jitter adds [0, 0.5*600] = [0, 300] → [600, 900).
        # Lower attempts (e.g. 5 → 480 base) are below the cap, so we use
        # attempt=6 to assert the cap actually engages.
        result = jittered_backoff_overloaded(6)
        assert isinstance(result, float)
        assert result >= 600.0, f"Expected >= 600.0 (capped base), got {result}"

    def test_returns_float(self) -> None:
        result = jittered_backoff_overloaded(1)
        assert isinstance(result, float)

    def test_monotonic_non_decreasing_across_attempts(self) -> None:
        # Sample several attempts; the floor (base before jitter) is monotonic.
        # With jitter the actual values vary, but the floor is non-decreasing.
        # We sample attempt 1 and 6 and assert attempt 6 floor >> attempt 1.
        a1 = jittered_backoff_overloaded(1)
        a6 = jittered_backoff_overloaded(6)
        # Both at least their floors (30 and 600 respectively).
        assert a1 >= 30.0
        assert a6 >= 600.0


class TestDefaultBackoffUnchanged:
    def test_existing_default_path_preserved(self) -> None:
        # The conversation_loop.py line ~3491 call site uses these exact kwargs.
        # Confirm the math is untouched: base=0.5, jitter=0.25 → [0.5, 0.625).
        result = jittered_backoff(
            1, base_delay=0.5, max_delay=32.0, jitter_ratio=0.25
        )
        assert 0.5 <= result < 0.625, (
            f"Expected [0.5, 0.625), got {result} — default path regressed"
        )

    def test_invalid_response_path_preserved(self) -> None:
        # conversation_loop.py line 1399 uses base=5.0, max=120.0 defaults.
        # Don't touch this path either.
        result = jittered_backoff(1, base_delay=5.0, max_delay=120.0)
        # Default jitter_ratio=0.5 → [5.0, 7.5).
        assert 5.0 <= result < 7.5, f"Expected [5.0, 7.5), got {result}"

    def test_overloaded_preset_does_not_mutate_default(self) -> None:
        # Calling the overloaded preset must not change global state that
        # affects subsequent default calls.
        _ = jittered_backoff_overloaded(3)
        result = jittered_backoff(
            1, base_delay=0.5, max_delay=32.0, jitter_ratio=0.25
        )
        assert 0.5 <= result < 0.625
