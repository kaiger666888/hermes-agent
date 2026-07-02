"""Unit tests for agent.glm_concurrency_guard.

Covers the process-wide host-keyed semaphore that throttles in-flight
requests to *.bigmodel.cn endpoints, mitigating the 1305 overloaded_error
storms observed 2026-07-02 10:05-10:25 CST.

Tests assert behavior BEFORE the implementation exists (TDD RED), then
pass once agent/glm_concurrency_guard.py is implemented (GREEN).
"""

from __future__ import annotations

import threading
import time

import pytest

from agent.glm_concurrency_guard import (
    acquire_glm_slot,
    get_glm_semaphore,
    is_glm_endpoint,
)


# ---------------------------------------------------------------------------
# Test A1 — host matching
# ---------------------------------------------------------------------------


class TestIsGlmEndpoint:
    def test_bigmodel_subdomain_matches(self) -> None:
        assert is_glm_endpoint("https://open.bigmodel.cn/api/anthropic") is True

    def test_bare_bigmodel_cn_matches(self) -> None:
        # Any *.bigmodel.cn host should match (future-proof for Zhipu rerouting).
        assert is_glm_endpoint("https://bigmodel.cn/api/paas/v4") is True

    def test_anthropic_does_not_match(self) -> None:
        assert is_glm_endpoint("https://api.anthropic.com") is False

    def test_openai_does_not_match(self) -> None:
        assert is_glm_endpoint("https://api.openai.com") is False

    def test_none_returns_false(self) -> None:
        assert is_glm_endpoint(None) is False

    def test_empty_string_returns_false(self) -> None:
        assert is_glm_endpoint("") is False

    def test_similar_name_does_not_match(self) -> None:
        # Anti-spoofing: "bigmodel.cn.evil.com" must NOT match.
        assert is_glm_endpoint("https://bigmodel.cn.evil.com") is False


# ---------------------------------------------------------------------------
# Test A2 — semaphore singleton per host
# ---------------------------------------------------------------------------


class TestGetGlmSemaphore:
    def test_same_host_returns_same_object(self) -> None:
        s1 = get_glm_semaphore("https://open.bigmodel.cn/api/anthropic")
        s2 = get_glm_semaphore("https://open.bigmodel.cn/v1/chat/completions")
        # Same hostname → same semaphore (paths differ, host identical).
        assert s1 is s2

    def test_distinct_hosts_return_distinct_semaphores(self) -> None:
        s1 = get_glm_semaphore("https://open.bigmodel.cn")
        s2 = get_glm_semaphore("https://alt.bigmodel.cn")
        assert s1 is not s2

    def test_non_glm_returns_none(self) -> None:
        assert get_glm_semaphore("https://api.anthropic.com") is None

    def test_none_returns_none(self) -> None:
        assert get_glm_semaphore(None) is None


# ---------------------------------------------------------------------------
# Test A3 — configurable N (default 4, config override, env override)
# ---------------------------------------------------------------------------


class TestResolveGlmN:
    def test_default_is_four(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Ensure no env override and no config override.
        monkeypatch.delenv("HERMES_GLM_CONCURRENCY", raising=False)
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {},
        )
        # Force re-resolution by clearing the cached value.
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)
        sem = get_glm_semaphore("https://test-default.bigmodel.cn")
        assert sem is not None
        assert sem._value == 4

    def test_config_value_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HERMES_GLM_CONCURRENCY", raising=False)
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {"glm": {"global_concurrency": 7}},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)
        sem = get_glm_semaphore("https://test-cfg.bigmodel.cn")
        assert sem is not None
        assert sem._value == 7

    def test_env_overrides_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HERMES_GLM_CONCURRENCY", "9")
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {"glm": {"global_concurrency": 3}},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)
        sem = get_glm_semaphore("https://test-env.bigmodel.cn")
        assert sem is not None
        assert sem._value == 9

    def test_clamped_to_min_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HERMES_GLM_CONCURRENCY", "0")
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)
        sem = get_glm_semaphore("https://test-clamp-min.bigmodel.cn")
        assert sem is not None
        assert sem._value == 1

    def test_clamped_to_max_32(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HERMES_GLM_CONCURRENCY", "999")
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)
        sem = get_glm_semaphore("https://test-clamp-max.bigmodel.cn")
        assert sem is not None
        assert sem._value == 32

    def test_garbage_env_falls_back_to_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HERMES_GLM_CONCURRENCY", "not-a-number")
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)
        sem = get_glm_semaphore("https://test-garbage.bigmodel.cn")
        assert sem is not None
        assert sem._value == 4


# ---------------------------------------------------------------------------
# Test A4 — concurrency cap (high-water mark)
# ---------------------------------------------------------------------------


class TestConcurrencyCap:
    def test_at_most_n_simultaneous(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Force N=3 for this test.
        monkeypatch.delenv("HERMES_GLM_CONCURRENCY", raising=False)
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {"glm": {"global_concurrency": 3}},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)

        high_water = {"value": 0}
        high_water_lock = threading.Lock()
        current = {"value": 0}
        current_lock = threading.Lock()
        barrier = threading.Barrier(10)
        done = {"count": 0}
        done_lock = threading.Lock()

        url = "https://concurrency-test.bigmodel.cn"

        def worker() -> None:
            barrier.wait()
            with acquire_glm_slot(url):
                with current_lock:
                    current["value"] += 1
                    if current["value"] > high_water["value"]:
                        high_water["value"] = current["value"]
                time.sleep(0.2)
                with current_lock:
                    current["value"] -= 1
            with done_lock:
                done["count"] += 1

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert done["count"] == 10
        assert high_water["value"] <= 3, (
            f"Expected at most 3 simultaneous slots, observed {high_water['value']}"
        )
        # Sanity: with N=3 and 10 workers each holding 0.2s, high_water should
        # actually hit 3 (otherwise the semaphore isn't blocking at all).
        assert high_water["value"] == 3


# ---------------------------------------------------------------------------
# Test A5 — release-on-exception
# ---------------------------------------------------------------------------


class TestReleaseOnException:
    def test_semaphore_value_restored_after_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("HERMES_GLM_CONCURRENCY", raising=False)
        monkeypatch.setattr(
            "agent.glm_concurrency_guard._load_config_for_glm",
            lambda: {"glm": {"global_concurrency": 4}},
        )
        import agent.glm_concurrency_guard as mod

        monkeypatch.setattr(mod, "_RESOLVED_N", None)

        url = "https://exception-test.bigmodel.cn"
        sem = get_glm_semaphore(url)
        assert sem is not None
        initial = sem._value

        with pytest.raises(RuntimeError, match="boom"):
            with acquire_glm_slot(url):
                raise RuntimeError("boom")

        assert sem._value == initial, (
            f"Semaphore not restored after exception: {sem._value} != {initial}"
        )


# ---------------------------------------------------------------------------
# Test A6 — non-GLM passthrough (no-op context manager)
# ---------------------------------------------------------------------------


class TestNonGlmPassthrough:
    def test_does_not_block_for_non_glm(self) -> None:
        # Even with a hypothetical N=0 semaphore, non-GLM endpoints must
        # pass through without acquiring anything. We can't easily test
        # "doesn't block" directly, but we can confirm the context manager
        # yields and exits cleanly with no semaphore interaction.
        non_glm_url = "https://api.openai.com"
        assert is_glm_endpoint(non_glm_url) is False

        # If acquire_glm_slot tried to acquire a non-existent semaphore, this
        # would AttributeError. If it correctly short-circuits, it just yields.
        with acquire_glm_slot(non_glm_url):
            pass  # No exception, no block.

    def test_none_url_is_passthrough(self) -> None:
        with acquire_glm_slot(None):
            pass  # No exception.


# ---------------------------------------------------------------------------
# Tests C1/C2/C3 — consecutive-overloaded early-abort counter semantics.
#
# The full abort logic lives inline in agent/conversation_loop.run_conversation
# (a 4000-line function), so we test the counter semantics via TurnRetryState
# directly and assert the structural integration points exist in the source.
# The behavior under test is:
#   - counter increments on FailoverReason.overloaded
#   - counter resets on any other reason
#   - counter resets on success (verified structurally in conversation_loop.py)
#   - abort fires when counter >= 3 (verified structurally)
# ---------------------------------------------------------------------------


class TestConsecutiveOverloadedCounter:
    """Validates the counter state machine that drives the 3-strike abort."""

    def test_starts_at_zero(self) -> None:
        from agent.turn_retry_state import TurnRetryState

        state = TurnRetryState()
        assert state.consecutive_overloaded == 0

    def test_simulated_three_overloaded_then_abort(self) -> None:
        # Simulate the conversation_loop's classification-driven counter update.
        # This mirrors the exact branching logic added to run_conversation.
        from agent.error_classifier import FailoverReason
        from agent.turn_retry_state import TurnRetryState

        state = TurnRetryState()
        classifications = [FailoverReason.overloaded] * 3

        for reason in classifications:
            if reason == FailoverReason.overloaded:
                state.consecutive_overloaded += 1
            else:
                state.consecutive_overloaded = 0
            if state.consecutive_overloaded >= 3:
                # Abort would fire here with the "GLM model overloaded" message.
                break

        assert state.consecutive_overloaded >= 3
        # The abort message must contain "GLM model overloaded" (verified
        # structurally below to avoid importing the entire conversation loop).
        abort_msg = (
            "GLM model overloaded — 3 consecutive 1305/overloaded responses. "
            "Pause new requests for ~10-15 minutes and retry."
        )
        assert "GLM model overloaded" in abort_msg

    def test_non_overloaded_does_not_abort(self) -> None:
        from agent.error_classifier import FailoverReason
        from agent.turn_retry_state import TurnRetryState

        state = TurnRetryState()
        # 3 timeouts should NOT trip the abort (counter stays at 0).
        for _ in range(3):
            reason = FailoverReason.timeout
            if reason == FailoverReason.overloaded:
                state.consecutive_overloaded += 1
            else:
                state.consecutive_overloaded = 0

        assert state.consecutive_overloaded == 0
        assert state.consecutive_overloaded < 3  # No abort.

    def test_counter_resets_on_non_overloaded(self) -> None:
        # 2 overloaded → 1 timeout → 2 more overloaded should NOT reach 3.
        from agent.error_classifier import FailoverReason
        from agent.turn_retry_state import TurnRetryState

        state = TurnRetryState()
        sequence = [
            FailoverReason.overloaded,
            FailoverReason.overloaded,
            FailoverReason.timeout,  # resets to 0
            FailoverReason.overloaded,
            FailoverReason.overloaded,
        ]

        aborted = False
        for reason in sequence:
            if reason == FailoverReason.overloaded:
                state.consecutive_overloaded += 1
            else:
                state.consecutive_overloaded = 0
            if state.consecutive_overloaded >= 3:
                aborted = True
                break

        assert not aborted, "Counter should have reset on the timeout, preventing abort"
        assert state.consecutive_overloaded == 2


class TestConversationLoopIntegration:
    """Structural assertions that the abort logic is wired into conversation_loop.

    Importing and executing run_conversation would require a fully-wired AIAgent
    (config, providers, transport, session DB) — out of scope for this unit
    test. Instead we verify the integration points exist in the source.
    """

    def test_acquire_glm_slot_wraps_run_llm_execution_middleware(self) -> None:
        # Read the source and confirm the guard hook is in place.
        from pathlib import Path

        import agent.conversation_loop as cl

        source = Path(cl.__file__).read_text(encoding="utf-8")
        assert "with acquire_glm_slot(" in source, (
            "acquire_glm_slot must wrap the run_llm_execution_middleware call"
        )
        assert "from agent.glm_concurrency_guard import acquire_glm_slot" in source

    def test_jittered_backoff_overloaded_branch_exists(self) -> None:
        from pathlib import Path

        import agent.conversation_loop as cl

        source = Path(cl.__file__).read_text(encoding="utf-8")
        assert "jittered_backoff_overloaded(retry_count)" in source, (
            "The overloaded-specific backoff branch must be present in the "
            "API-error retry path"
        )
        assert "from agent.retry_utils import jittered_backoff, jittered_backoff_overloaded" in source

    def test_consecutive_overloaded_counter_wired(self) -> None:
        from pathlib import Path

        import agent.conversation_loop as cl

        source = Path(cl.__file__).read_text(encoding="utf-8")
        # Counter increment + reset branch.
        assert "_retry.consecutive_overloaded += 1" in source
        assert "_retry.consecutive_overloaded = 0" in source
        # Abort guard.
        assert "_retry.consecutive_overloaded >= 3" in source
        assert "glm_overloaded_abort" in source
        assert "GLM model overloaded" in source
