"""Tests for Phase 58 THROTTLE-01: per-task RPM token bucket.

Validates ``agent/glm_throttle.py`` (NEW module) — classic leaky bucket:
capacity N tokens, refills 1 token every (60/RPM) seconds.

Context: see .planning/phases/58-rpm-throttling/58-CONTEXT.md
         and MEMORY.md feedback-glm-overload-reduce-concurrency.md
         (root policy: cap per-task RPM before it hits GLM single-key ceiling).

Test strategy: deterministic time mocking via monkeypatch of ``time.monotonic``
+ ``time.sleep`` (no real wall-clock waits — keeps the suite fast and flake-free).
"""
from __future__ import annotations

import pytest

# Import will fail until agent/glm_throttle.py exists — this is the RED gate.
from agent.glm_throttle import (  # noqa: E402
    DEFAULT_RPM,
    TokenBucket,
    acquire_slot,
    try_acquire_slot,
    reset_for_testing,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_buckets_and_clock(monkeypatch):
    """Start each test with empty bucket registry + a controllable clock.

    The fake clock starts at t=1000.0 (arbitrary offset; tests advance it
    explicitly via ``_ADVANCE``). ``time.sleep`` becomes a no-op that also
    advances the fake clock so blocking-acquire loops terminate.
    """
    reset_for_testing()
    _now = [1000.0]

    def _fake_monotonic() -> float:
        return _now[0]

    def _fake_sleep(seconds: float) -> None:
        _now[0] += float(seconds)

    # glm_throttle looks up ``time.monotonic`` and ``time.sleep`` at call
    # time (module-level reference), so patching the module attr is enough.
    import agent.glm_throttle as _mod

    monkeypatch.setattr(_mod.time, "monotonic", _fake_monotonic)
    monkeypatch.setattr(_mod.time, "sleep", _fake_sleep)

    # Expose advance helper to tests that want to move the clock without
    # going through ``time.sleep`` (e.g. testing refill but not blocking).
    yield

    reset_for_testing()


# ===========================================================================
# Task 1: Token bucket behavior (9 tests)
# ===========================================================================


class TestTokenBucketBasics:
    """Behavioral coverage for TokenBucket + module-level acquire APIs."""

    # ---- Test 1: acquire under capacity returns immediately ----------------

    def test_acquire_under_capacity_returns_immediately(self, monkeypatch):
        """Test 1: fresh bucket with rpm=30 → first acquire_slot returns
        without blocking and decrements the available count."""
        # Bucket starts full (capacity=rpm=30). First acquire must succeed
        # without invoking time.sleep — we detect "no blocking" by ensuring
        # the fake clock did not advance past its starting offset via sleep.
        import agent.glm_throttle as _mod

        slept_for: list[float] = []

        def _track_sleep(seconds: float) -> None:
            slept_for.append(seconds)
            # Advance the clock so any subsequent monotonic reads see the jump.
            # We do NOT patch the auto-advancing sleep from the autouse fixture
            # here because we want to observe the sleep value.
            _mod.time.monotonic  # ensure attr exists
            # Manually advance via the real fixture mechanism:
            # Re-patch monotonic to return current + seconds.
            _current = _mod.time.monotonic()
            monkeypatch.setattr(
                _mod.time, "monotonic", lambda: _current + seconds
            )

        monkeypatch.setattr(_mod.time, "sleep", _track_sleep)

        acquire_slot("test_task_under_capacity")

        assert slept_for == [], (
            "First acquire on a full bucket must not block — expected zero "
            f"sleep calls, got {slept_for}"
        )

    # ---- Test 2: try_acquire returns False when empty ---------------------

    def test_try_acquire_returns_false_when_empty(self):
        """Test 2: bucket with rpm=1 → first try succeeds, second immediate
        try returns False (capacity exhausted, no time elapsed)."""
        # Use a task name that has no config override so the bucket gets the
        # DEFAULT_RPM; we then construct a fresh TokenBucket directly with
        # capacity=1 to make the assertion tight.
        bucket = TokenBucket(
            capacity=1, refill_interval_seconds=60.0,
            available=1.0, last_refill_time=0.0,
        )
        assert bucket.try_acquire() is True   # first token consumed
        assert bucket.try_acquire() is False  # empty → non-blocking False

    # ---- Test 3: refill after interval ------------------------------------

    def test_refill_after_interval(self):
        """Test 3: rpm=60 (refill_interval=1.0s). Drain both tokens, advance
        clock 1s, next try_acquire succeeds (1 token refilled)."""
        bucket = TokenBucket(
            capacity=2, refill_interval_seconds=1.0,
            available=2.0, last_refill_time=0.0,
        )
        assert bucket.try_acquire() is True
        assert bucket.try_acquire() is True
        # Drain complete. At t=0, no refill yet.
        bucket.refill(now=0.0)  # no-op if last_refill_time == now
        assert bucket.try_acquire() is False
        # Advance 1s → one token should refill.
        bucket.refill(now=1.0)
        assert bucket.try_acquire() is True

    # ---- Test 4: per-task isolation ---------------------------------------

    def test_per_task_isolation(self):
        """Test 4: acquire_slot('task_a') and acquire_slot('task_b') use
        INDEPENDENT buckets — draining task_a does not affect task_b."""
        # Drain task_a completely (capacity defaults to DEFAULT_RPM).
        bucket_a = try_acquire_slot("iso_task_a")
        assert bucket_a is True
        # task_b must still have its full capacity available.
        for _ in range(DEFAULT_RPM):
            assert try_acquire_slot("iso_task_b") is True
        # task_b is now drained; task_a still has DEFAULT_RPM - 1 tokens.
        assert try_acquire_slot("iso_task_b") is False
        # task_a still has capacity remaining (drain only 1 above).
        assert try_acquire_slot("iso_task_a") is True

    # ---- Test 5: config override via auxiliary.{task}.rpm ------------------

    def test_config_override_propagates_to_bucket(self, monkeypatch):
        """Test 5: monkeypatch ``_resolve_rpm`` to return 60 for
        ``custom_task``. The bucket must reflect capacity 60 (refill_interval
        1.0s) rather than the default 30."""
        import agent.glm_throttle as _mod

        # Direct patch at the bucket-resolution seam — cleaner than
        # sys.modules swapping (which doesn't reliably propagate to the
        # lazy ``from agent.auxiliary_client import ...`` inside _resolve_rpm).
        def _fake_resolve(task: str) -> int:
            if task == "custom_task":
                return 60
            return _mod.DEFAULT_RPM

        monkeypatch.setattr(_mod, "_resolve_rpm", _fake_resolve)

        # Acquire 60 tokens (capacity). 61st must fail.
        for _ in range(60):
            assert try_acquire_slot("custom_task") is True
        assert try_acquire_slot("custom_task") is False

    # ---- Test 6: default RPM is 30 ----------------------------------------

    def test_default_rpm_is_30_for_unknown_task(self):
        """Test 6: unknown task with no config → capacity 30, refill_interval
        60/30 = 2.0s. Verified by draining exactly 30 tokens then failing."""
        assert DEFAULT_RPM == 30
        for _ in range(30):
            assert try_acquire_slot("unknown_default_task") is True
        assert try_acquire_slot("unknown_default_task") is False

    # ---- Test 7: lazy-init reuses same bucket instance --------------------

    def test_lazy_init_creates_bucket_once(self):
        """Test 7: bucket registry starts empty; first call lazily creates
        the bucket, second call reuses the SAME instance."""
        import agent.glm_throttle as _mod

        reset_for_testing()
        assert _mod._BUCKETS == {}

        acquire_slot("lazy_init_task")  # triggers creation
        assert "lazy_init_task" in _mod._BUCKETS
        first = _mod._BUCKETS["lazy_init_task"]

        acquire_slot("lazy_init_task")  # must reuse, not recreate
        assert _mod._BUCKETS["lazy_init_task"] is first

    # ---- Test 8: acquire_slot blocks via time.sleep -----------------------

    def test_acquire_slot_blocks_until_refill(self, monkeypatch):
        """Test 8: drained bucket → acquire_slot must sleep for the refill
        interval, then succeed. Use a tracked sleep to assert the duration."""
        import agent.glm_throttle as _mod

        reset_for_testing()
        _mod._BUCKETS["blocking_task"] = TokenBucket(
            capacity=1, refill_interval_seconds=10.0,
            available=1.0, last_refill_time=1000.0,
        )
        # Drain.
        assert try_acquire_slot("blocking_task") is True
        assert try_acquire_slot("blocking_task") is False

        slept: list[float] = []

        # Replace the auto-advancing fixture sleep with a tracker that ALSO
        # advances monotonic so the refill() inside acquire_slot sees the
        # elapsed time and breaks out of the loop on the first iteration.
        _clock = [1000.0]
        monkeypatch.setattr(_mod.time, "monotonic", lambda: _clock[0])

        def _track_and_advance(seconds: float) -> None:
            slept.append(seconds)
            _clock[0] += seconds

        monkeypatch.setattr(_mod.time, "sleep", _track_and_advance)

        # Should block once for ~10s, then succeed.
        acquire_slot("blocking_task")

        assert len(slept) == 1, f"Expected exactly one sleep, got {slept}"
        assert 0 < slept[0] <= 10.0, (
            f"Sleep duration must be in (0, 10] — got {slept[0]}"
        )

    # ---- Test 9: invalid rpm falls back to default ------------------------

    def test_invalid_rpm_falls_back_to_default(self, monkeypatch):
        """Test 9: ``rpm=0`` / negative / non-numeric must NOT cause an
        infinite loop or division-by-zero. Falls back to DEFAULT_RPM=30."""
        import agent.glm_throttle as _mod

        # Verify _resolve_rpm itself handles each bad input by patching it
        # to consult a stub that returns the raw bad config value. We then
        # call _get_or_create_bucket and check the resulting capacity.
        def _fake_resolve(task: str) -> int:
            # Simulate the real _resolve_rpm's fallback logic by reusing it
            # against a fake config dict.
            if task == "bad_rpm_task":
                raw = 0
            elif task == "negative_rpm_task":
                raw = -5
            elif task == "non_numeric_rpm_task":
                raw = "fast"
            else:
                return _mod.DEFAULT_RPM
            # Mirror _resolve_rpm's validation: non-int / <= 0 → DEFAULT_RPM.
            try:
                rpm = int(raw)
            except (TypeError, ValueError):
                return _mod.DEFAULT_RPM
            if rpm <= 0:
                return _mod.DEFAULT_RPM
            return rpm

        # Stronger assertion: directly test _resolve_rpm with real misconfigs.
        # Patch the lazy-import seam by swapping the config helper. We do
        # this by replacing _resolve_rpm with a version that consults a
        # fake task-config map, then run the real validation logic.
        import sys
        import types

        _bad_configs = {
            "bad_rpm_task": {"rpm": 0},
            "negative_rpm_task": {"rpm": -5},
            "non_numeric_rpm_task": {"rpm": "fast"},
        }

        fake_aux = types.ModuleType("agent._fake_aux_for_bad_rpm")
        fake_aux._get_auxiliary_task_config = lambda t: _bad_configs.get(t, {})
        # Cache the real module so we can restore it.
        _real_aux = sys.modules.get("agent.auxiliary_client")
        sys.modules["agent.auxiliary_client"] = fake_aux
        try:
            for task in (
                "bad_rpm_task",
                "negative_rpm_task",
                "non_numeric_rpm_task",
            ):
                reset_for_testing()
                rpm = _mod._resolve_rpm(task)
                assert rpm == _mod.DEFAULT_RPM, (
                    f"task={task} with bad rpm must fall back to "
                    f"DEFAULT_RPM={_mod.DEFAULT_RPM}, got {rpm}"
                )
                # Drain DEFAULT_RPM tokens — proves the bucket is usable.
                for _ in range(_mod.DEFAULT_RPM):
                    assert try_acquire_slot(task) is True, (
                        f"task={task} bucket unusable after fallback"
                    )
                assert try_acquire_slot(task) is False
        finally:
            if _real_aux is not None:
                sys.modules["agent.auxiliary_client"] = _real_aux
            else:
                sys.modules.pop("agent.auxiliary_client", None)
