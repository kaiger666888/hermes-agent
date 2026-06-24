"""Tests for build_output_snapshot() (INGEST-04 output_snapshot capture).

Verifies sha256 determinism, agent param extraction, content-shape
defense (str / list-of-dicts / None), preceding user prompt discovery,
and non-serializable request_overrides filtering.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import pytest

from agent.feedback_snapshot import build_output_snapshot, _extract_text


class FakeAgent:
    """Minimal test double for AIAgent.

    Sets the attrs the snapshot builder reads via getattr. DO NOT import
    AIAgent — the builder is a pure function of agent + history.
    """

    def __init__(self, **attrs: Any) -> None:
        self.model = "test-model"
        self.provider = "openai"
        self.api_mode = "chat_completions"
        self.max_tokens = 4096
        self.reasoning_config = None
        self.service_tier = "default"
        self.request_overrides: dict[str, Any] = {}
        for k, v in attrs.items():
            setattr(self, k, v)


def _history(*msgs: dict[str, Any]) -> list[dict[str, Any]]:
    return list(msgs)


class TestOutputSnapshotBuilder:
    """build_output_snapshot() behavior tests."""

    def test_sha256_deterministic(self):
        """Same assistant_text + same agent state -> identical sha256."""
        agent = FakeAgent()
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "yo"},
        )
        snap1 = build_output_snapshot(agent, history, assistant_idx=1)
        snap2 = build_output_snapshot(agent, history, assistant_idx=1)
        assert snap1.sha256 == snap2.sha256, "sha256 must be deterministic"
        # And it matches a manual sha256 of the text encoded utf-8
        expected = hashlib.sha256("yo".encode("utf-8")).hexdigest()
        assert snap1.sha256 == expected

    def test_sha256_matches_manual_hash(self):
        """sha256 equals hashlib.sha256(output_text.encode('utf-8'))."""
        agent = FakeAgent()
        text = "the quick brown fox"
        history = _history(
            {"role": "user", "content": "x"},
            {"role": "assistant", "content": text},
        )
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        assert snap.sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert snap.output_text == text

    def test_captures_agent_params(self):
        """Builder reads agent.max_tokens / provider / model / api_mode."""
        agent = FakeAgent(
            max_tokens=8192,
            provider="openai",
            model="gpt-4",
            api_mode="chat_completions",
        )
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "response"},
        )
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        assert snap.model == "gpt-4"
        assert snap.provider == "openai"
        assert snap.api_mode == "chat_completions"
        assert "max_tokens" in snap.params
        assert snap.params["max_tokens"] == 8192

    def test_captures_request_overrides(self):
        agent = FakeAgent(request_overrides={"temperature": 0.7})
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "response"},
        )
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        assert "request_overrides" in snap.params
        assert snap.params["request_overrides"]["temperature"] == 0.7

    def test_extract_text_all_shapes(self):
        """_extract_text handles str, list-of-dicts, None, and mixed shapes."""
        # plain string
        assert _extract_text("hello") == "hello"
        # None -> empty
        assert _extract_text(None) == ""
        # Anthropic-style list of dicts with text parts
        content = [
            {"type": "text", "text": "a"},
            {"type": "text", "text": "b"},
        ]
        assert _extract_text(content) == "ab"
        # list with non-text parts (tool_use etc.) -> only text parts concat
        mixed = [
            {"type": "tool_use", "id": "x"},
            {"type": "text", "text": "only this"},
        ]
        assert _extract_text(mixed) == "only this"
        # empty list
        assert _extract_text([]) == ""
        # list with no text parts -> empty
        assert _extract_text([{"type": "tool_use"}]) == ""

    def test_extract_text_does_not_mutate_input(self):
        content = [{"type": "text", "text": "abc"}]
        _ = _extract_text(content)
        assert content == [{"type": "text", "text": "abc"}], "input list must not be mutated"

    def test_finds_preceding_user_prompt(self):
        """Builder scans backward from assistant_idx-1 for the most recent user msg."""
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "yo"},
        )
        snap = build_output_snapshot(
            agent=FakeAgent(), conversation_history=history, assistant_idx=1
        )
        assert snap.prompt == "hi"

    def test_prompt_empty_when_no_preceding_user(self):
        """If no user msg precedes the assistant turn, prompt is empty."""
        history = _history({"role": "assistant", "content": "yo"})
        snap = build_output_snapshot(
            agent=FakeAgent(), conversation_history=history, assistant_idx=0
        )
        assert snap.prompt == ""

    def test_prompt_finds_most_recent_user_when_multiple(self):
        """When multiple user msgs precede, pick the one closest to assistant_idx."""
        history = _history(
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "resp1"},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": "resp2"},
        )
        snap = build_output_snapshot(
            agent=FakeAgent(), conversation_history=history, assistant_idx=3
        )
        assert snap.prompt == "second"

    def test_drops_non_serializable_request_overrides(self):
        """Lambdas/callables in request_overrides must not crash the builder.

        Per RESEARCH Pitfall #8 — request_overrides is Dict[str, Any] and may
        contain callables. The snapshot must filter them out gracefully
        (either omit or convert), not raise TypeError.
        """
        # lambda is the classic non-serializable value
        agent = FakeAgent(
            request_overrides={
                "temperature": 0.7,
                "callback": lambda x: x,  # type: ignore[dict-item]
            }
        )
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "response"},
        )
        # The call must NOT raise
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        # temperature survives
        assert snap.params["request_overrides"]["temperature"] == 0.7
        # callback key either dropped or sanitized — but no crash either way
        assert "callback" not in snap.params["request_overrides"] or not callable(
            snap.params["request_overrides"].get("callback")
        )

    def test_captured_at_is_timezone_aware(self):
        agent = FakeAgent()
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "yo"},
        )
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        assert snap.captured_at.tzinfo is not None, "captured_at must be tz-aware"

    def test_handles_assistant_with_list_content(self):
        """Anthropic-style assistant content list (multiple text blocks)."""
        agent = FakeAgent()
        history = _history(
            {"role": "user", "content": "hi"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "part1 "},
                    {"type": "text", "text": "part2"},
                ],
            },
        )
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        assert snap.output_text == "part1 part2"
        assert (
            snap.sha256
            == hashlib.sha256("part1 part2".encode("utf-8")).hexdigest()
        )

    def test_missing_agent_attrs_default_gracefully(self):
        """Agent missing optional attrs (reasoning_config etc.) doesn't crash."""
        agent = FakeAgent()
        # remove an optional attr
        del agent.reasoning_config
        history = _history(
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "yo"},
        )
        snap = build_output_snapshot(agent, history, assistant_idx=1)
        # missing attr -> not added to params (getattr default None is skipped)
        assert "reasoning_config" not in snap.params or snap.params["reasoning_config"] is None
