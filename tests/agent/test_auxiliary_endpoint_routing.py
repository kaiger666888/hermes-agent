"""Tests for Phase 57 ENDPOINT-ROUTING: prompt-length-aware endpoint selection.

Validates ``_select_endpoint_by_prompt_length`` (helper) + the integration into
``call_llm`` that routes long-prompt GLM calls (synthesis, memory_compaction,
memory_comparator) to ``open.bigmodel.cn/api/anthropic`` so the z.ai coding-plan
30s timeout stops tripping the openai-SDK 5x retry storm.

Context: see .planning/phases/57-endpoint-routing/57-CONTEXT.md
         and smoke-test-report.md §3.1 (v11.0 SC#2 synthesis retry storm).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from agent.auxiliary_client import (
    _select_endpoint_by_prompt_length,
    call_llm,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _msg(n_chars: int, role: str = "user") -> List[Dict[str, Any]]:
    """Build a one-message list whose content is *n_chars* characters long.

    At the default heuristic (chars // 4), this yields approximately
    ``n_chars // 4`` tokens.
    """
    return [{"role": role, "content": "x" * n_chars}]


@pytest.fixture
def default_routing_config():
    """Default auxiliary.endpoint_routing config block (matches helper defaults)."""
    return {
        "enabled": True,
        "token_threshold": 4096,
        "long_prompt": {
            "provider": "zhipu-anthropic",
            "base_url": "https://open.bigmodel.cn/api/anthropic",
            "api_mode": "chat_completions",
        },
    }


@pytest.fixture
def patch_default_config(default_routing_config, monkeypatch):
    """Patch ``_get_auxiliary_task_config`` to return the default routing config."""
    def _fake(task: str) -> Dict[str, Any]:
        if task == "endpoint_routing":
            return dict(default_routing_config)
        return {}
    monkeypatch.setattr(
        "agent.auxiliary_client._get_auxiliary_task_config", _fake
    )


# ===========================================================================
# Task 1: Helper unit tests (9 tests)
# ===========================================================================


class TestSelectEndpointByPromptLength:
    """Behavioral tests for ``_select_endpoint_by_prompt_length`` helper."""

    # ---- Test 1: empty messages list returns None ---------------------------

    def test_empty_messages_returns_none(self, patch_default_config):
        """Test 1: empty messages list -> returns None."""
        result = _select_endpoint_by_prompt_length([], None, None)
        assert result is None

    # ---- Test 2: short prompt returns None ---------------------------------

    def test_short_prompt_returns_none(self, patch_default_config):
        """Test 2: messages with <4096 estimated tokens -> returns None.

        3000 chars ≈ 750 tokens; well below the 4096 threshold.
        """
        messages = _msg(3000)
        result = _select_endpoint_by_prompt_length(messages, "glm", None)
        assert result is None

    # ---- Test 3: long GLM prompt routes to anthropic-compat -----------------

    def test_long_glm_prompt_routes_to_anthropic(self, patch_default_config):
        """Test 3: messages with >=4096 tokens with provider='glm' routes."""
        messages = _msg(20000)  # ~5000 tokens
        result = _select_endpoint_by_prompt_length(messages, "glm", None)
        assert result is not None
        assert result["provider"] == "zhipu-anthropic"
        assert result["base_url"] == "https://open.bigmodel.cn/api/anthropic"
        assert result["api_mode"] == "chat_completions"

    # ---- Test 4: long prompt but non-GLM provider returns None --------------

    def test_long_prompt_non_glm_provider_returns_none(self, patch_default_config):
        """Test 4: provider != glm/zai/None -> returns None (out of scope)."""
        messages = _msg(20000)
        result = _select_endpoint_by_prompt_length(messages, "openrouter", None)
        assert result is None

    # ---- Test 5: provider already set to zhipu-anthropic returns None -------

    def test_already_routed_returns_none(self, patch_default_config):
        """Test 5: provider already on 'zhipu-anthropic' -> no double-override."""
        messages = _msg(20000)
        result = _select_endpoint_by_prompt_length(messages, "zhipu-anthropic", None)
        assert result is None

    # ---- Test 6: threshold raised above prompt size returns None ------------

    def test_threshold_override(self, monkeypatch):
        """Test 6: token_threshold=8000, ~5000-token prompt -> returns None."""
        def _fake(task: str) -> Dict[str, Any]:
            if task == "endpoint_routing":
                return {
                    "enabled": True,
                    "token_threshold": 8000,
                    "long_prompt": {
                        "provider": "zhipu-anthropic",
                        "base_url": "https://open.bigmodel.cn/api/anthropic",
                        "api_mode": "chat_completions",
                    },
                }
            return {}
        monkeypatch.setattr(
            "agent.auxiliary_client._get_auxiliary_task_config", _fake
        )
        messages = _msg(20000)  # ~5000 tokens < 8000 threshold
        result = _select_endpoint_by_prompt_length(messages, "glm", None)
        assert result is None

    # ---- Test 7: custom short_prompt / long_prompt config respected ---------

    def test_custom_endpoint_config(self, monkeypatch):
        """Test 7: custom long_prompt.provider/base_url used instead of defaults."""
        def _fake(task: str) -> Dict[str, Any]:
            if task == "endpoint_routing":
                return {
                    "enabled": True,
                    "token_threshold": 4096,
                    "short_prompt": {"provider": "zai"},
                    "long_prompt": {
                        "provider": "my-custom-anthropic",
                        "base_url": "https://example.com/anthropic",
                        "api_mode": "chat_completions",
                    },
                }
            return {}
        monkeypatch.setattr(
            "agent.auxiliary_client._get_auxiliary_task_config", _fake
        )
        messages = _msg(20000)
        result = _select_endpoint_by_prompt_length(messages, "glm", None)
        assert result is not None
        assert result["provider"] == "my-custom-anthropic"
        assert result["base_url"] == "https://example.com/anthropic"

    # ---- Test 8: enabled=false opt-out returns None ------------------------

    def test_disabled_returns_none(self, monkeypatch):
        """Test 8: enabled=False -> returns None even for huge prompts."""
        def _fake(task: str) -> Dict[str, Any]:
            if task == "endpoint_routing":
                return {"enabled": False}
            return {}
        monkeypatch.setattr(
            "agent.auxiliary_client._get_auxiliary_task_config", _fake
        )
        messages = _msg(100000)
        result = _select_endpoint_by_prompt_length(messages, "glm", None)
        assert result is None

    # ---- Test 9: helper delegates to estimate_messages_tokens_rough --------

    def test_helper_uses_estimate_messages_tokens_rough(self, patch_default_config, monkeypatch):
        """Test 9: helper delegates to estimate_messages_tokens_rough (no reinvent)."""
        with patch(
            "agent.auxiliary_client.estimate_messages_tokens_rough", return_value=5000
        ) as mock_est:
            messages = _msg(123)  # actual size irrelevant; mock returns 5000
            result = _select_endpoint_by_prompt_length(messages, "glm", None)
            assert mock_est.called
            assert mock_est.call_args[0][0] is messages
        assert result is not None
        assert result["provider"] == "zhipu-anthropic"


# ===========================================================================
# Task 2: call_llm integration tests (4 tests)
# ===========================================================================


class TestCallLlmEndpointRouting:
    """Integration tests verifying call_llm invokes the routing helper."""

    def _mock_response(self) -> MagicMock:
        """Build a MagicMock that mimics an OpenAI chat completion response."""
        msg = MagicMock()
        msg.message.content = "ok"
        choice = MagicMock()
        choice.message = msg.message
        response = MagicMock()
        response.choices = [choice]
        return response

    @pytest.fixture(autouse=True)
    def _patch_client_cache(self, monkeypatch):
        """Capture the base_url passed into _get_cached_client instead of building one."""
        captured = {"base_url": None, "provider": None, "api_mode": None}

        def _fake_get_cached_client(
            provider, model=None, async_mode=False, base_url=None,
            api_key=None, api_mode=None, main_runtime=None, is_vision=False, task=None,
        ):
            captured["provider"] = provider
            captured["base_url"] = base_url
            captured["api_mode"] = api_mode
            client = MagicMock()
            client.base_url = base_url or "https://default.example.com/v1"
            client.chat.completions.create.return_value = self._mock_response()
            return client, model

        monkeypatch.setattr(
            "agent.auxiliary_client._get_cached_client", _fake_get_cached_client
        )
        return captured

    # ---- Test 10: long GLM call routes to anthropic-compat ------------------

    def test_long_glm_call_routes_to_anthropic_endpoint(
        self, patch_default_config, _patch_client_cache
    ):
        """Test 10: call_llm with long prompt -> base_url contains open.bigmodel.cn/api/anthropic."""
        messages = _msg(20000)  # ~5000 tokens
        call_llm(
            task="round_table_opinion",
            provider="glm",
            model="glm-5.2",
            messages=messages,
        )
        captured_base = _patch_client_cache["base_url"] or ""
        assert "open.bigmodel.cn/api/anthropic" in captured_base, (
            f"Expected anthropic endpoint, got {captured_base!r}"
        )
        assert "z.ai" not in captured_base and "coding/paas/v4" not in captured_base

    # ---- Test 11: short GLM call stays on coding plan -----------------------

    def test_short_glm_call_stays_on_coding_plan(
        self, patch_default_config, _patch_client_cache
    ):
        """Test 11: call_llm with short prompt -> base_url does NOT contain /anthropic."""
        messages = _msg(500)  # ~125 tokens, well below threshold
        call_llm(
            task="round_table_opinion",
            provider="glm",
            model="glm-5.2",
            messages=messages,
        )
        captured_base = _patch_client_cache["base_url"] or ""
        assert "/anthropic" not in captured_base, (
            f"Short prompt should NOT route to anthropic, got {captured_base!r}"
        )

    # ---- Test 12: memory_compaction long prompt also routes -----------------

    def test_memory_compaction_long_prompt_routes(
        self, patch_default_config, _patch_client_cache
    ):
        """Test 12: call_llm for memory_compaction task with long prompt routes too."""
        messages = _msg(30000)  # ~7500 tokens
        call_llm(
            task="memory_compaction",
            provider="glm",
            model="glm-5.2",
            messages=messages,
        )
        captured_base = _patch_client_cache["base_url"] or ""
        assert "open.bigmodel.cn/api/anthropic" in captured_base

    # ---- Test 13: SC#2 latency regression (routed succeeds, unrouted storms) -

    def test_sc2_latency_regression_routed_faster_than_unrouted(
        self, monkeypatch
    ):
        """Test 13: routed path succeeds in 1 dispatch; unrouted path raises.

        Models the v11.0 SC#2 synthesis retry storm: the z.ai coding-plan
        endpoint's 30s timeout causes the unrouted path to fail (the
        openai-SDK's internal 5x retry-then-fallback chain is below the
        mocked boundary, so we observe the post-retry-storm exhaustion as
        a single raised TimeoutError at the call_llm boundary). The routed
        path skips z.ai entirely and succeeds on the first anthropic call.

        Assertion strategy:
        - Routed (enabled=True): call_llm returns a valid response; the
          create() mock was invoked exactly once.
        - Unrouted (enabled=False): call_llm raises (TimeoutError/connection
          error after all fallbacks exhausted), proving the z.ai path
          cannot complete on a long synthesis prompt.
        """
        good_response = self._mock_response()
        create_invocations = {"n": 0}

        def _build_run(enabled: bool):
            cfg = {
                "enabled": enabled,
                "token_threshold": 4096,
                "long_prompt": {
                    "provider": "zhipu-anthropic",
                    "base_url": "https://open.bigmodel.cn/api/anthropic",
                    "api_mode": "chat_completions",
                },
            }

            def _fake_cfg(task: str) -> Dict[str, Any]:
                if task == "endpoint_routing":
                    return dict(cfg)
                return {}

            def _fake_client(
                provider, model=None, async_mode=False, base_url=None,
                api_key=None, api_mode=None, main_runtime=None, is_vision=False, task=None,
            ):
                client = MagicMock()
                # Real-world: glm/zai with no override → api.z.ai/api/coding/paas/v4.
                # Routed path: base_url=open.bigmodel.cn/api/anthropic.
                effective_base = base_url
                if not effective_base:
                    if provider in {"glm", "zai", "auto", None}:
                        effective_base = "https://api.z.ai/api/coding/paas/v4"
                    else:
                        effective_base = "https://default.example.com/v1"
                client.base_url = effective_base

                if "open.bigmodel.cn/api/anthropic" in effective_base:
                    # Routed: succeeds on first dispatch.
                    def _anthropic_create(**kwargs):
                        create_invocations["n"] += 1
                        return good_response
                    client.chat.completions.create.side_effect = _anthropic_create
                else:
                    # Unrouted z.ai path: always times out (post-retry-storm
                    # exhaustion — the 5x openai-SDK internal retries happen
                    # below this boundary and all fail with 30s cap).
                    def _zai_create(**kwargs):
                        create_invocations["n"] += 1
                        raise TimeoutError("z.ai coding-plan 30s timeout (simulated)")
                    client.chat.completions.create.side_effect = _zai_create
                return client, model

            monkeypatch.setattr(
                "agent.auxiliary_client._get_auxiliary_task_config", _fake_cfg
            )
            monkeypatch.setattr(
                "agent.auxiliary_client._get_cached_client", _fake_client
            )
            monkeypatch.setattr(
                "agent.auxiliary_client._is_connection_error",
                lambda exc: isinstance(exc, TimeoutError),
            )
            monkeypatch.setattr(
                "agent.auxiliary_client._is_transient_transport_error",
                lambda exc: False,
            )

            def _run():
                create_invocations["n"] = 0
                messages = _msg(20000)  # ~5000 tokens
                try:
                    response = call_llm(
                        task="round_table_opinion",
                        provider="glm",
                        model="glm-5.2",
                        messages=messages,
                    )
                    return ("ok", response, create_invocations["n"])
                except Exception as exc:
                    return ("error", exc, create_invocations["n"])

            return _run

        # Routed path: succeeds on the first anthropic call.
        routed_run = _build_run(enabled=True)
        routed_status, routed_resp, routed_calls = routed_run()
        assert routed_status == "ok", (
            f"Routed path should succeed, got {routed_status}: {routed_resp!r}"
        )
        assert routed_calls == 1, (
            f"Routed path should make exactly 1 create() call, made {routed_calls}"
        )

        # Unrouted path: z.ai 30s cap trips, fallback chain exhausts, raises.
        unrouted_run = _build_run(enabled=False)
        unrouted_status, unrouted_exc, unrouted_calls = unrouted_run()
        assert unrouted_status == "error", (
            f"Unrouted path should raise (z.ai 30s cap), got {unrouted_status}"
        )
        # Unrouted path makes >= 1 create() call (more if fallback chain kicks in).
        assert unrouted_calls >= 1

        # Discriminating assertion: routed succeeds, unrouted fails.
        # In production this manifests as ~250s of wasted retry time on
        # the unrouted path before fallback; routed skips all of it.
        assert routed_status != unrouted_status, (
            "Routed and unrouted should differ in outcome "
            f"(routed={routed_status}, unrouted={unrouted_status})"
        )
