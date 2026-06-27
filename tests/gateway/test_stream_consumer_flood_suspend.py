"""Unit tests for flood-control suspend/resume in GatewayStreamConsumer.

Ported from openclaw extensions/telegram/src/draft-stream.ts lines 339-452.
Verifies the three mechanisms that hermes was missing:

1. ``_suspended_until_monotonic`` timestamp set on flood detection.
2. ``retry_after`` parsing from SendResult (error string + raw_response).
3. Pending text preservation: zero API calls during suspend, single edit
   on resume delivers the latest accumulated text.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.stream_consumer import GatewayStreamConsumer, StreamConsumerConfig


def _flood_result(error: str = "Flood control exceeded. Retry in 30 seconds",
                  retry_after=None) -> SimpleNamespace:
    """Build a flood-control SendResult mock."""
    raw = {"retry_after": retry_after} if retry_after is not None else None
    return SimpleNamespace(
        success=False,
        message_id=None,
        error=error,
        raw_response=raw,
        retryable=True,
        continuation_message_ids=(),
    )


def _ok_result(message_id: str = "msg_1") -> SimpleNamespace:
    return SimpleNamespace(
        success=True,
        message_id=message_id,
        error=None,
        raw_response=None,
        retryable=False,
        continuation_message_ids=(),
    )


def _make_consumer(cursor: str = "") -> GatewayStreamConsumer:
    adapter = MagicMock()
    adapter.MAX_MESSAGE_LENGTH = 4096
    adapter.send = AsyncMock(return_value=_ok_result())
    adapter.edit_message = AsyncMock(return_value=_ok_result())
    adapter.delete_message = AsyncMock(return_value=_ok_result())
    cfg = StreamConsumerConfig(cursor=cursor, edit_interval=0.0)
    return GatewayStreamConsumer(adapter, "chat_1", cfg)


class TestExtractRetryAfter:
    """Verify _extract_retry_after_seconds parses retry_after from all sources."""

    def test_parses_from_error_string_retry_in(self):
        c = _make_consumer()
        r = _flood_result("Flood control exceeded. Retry in 35 seconds")
        assert c._extract_retry_after_seconds(r) == 35.0

    def test_parses_from_error_string_retry_after(self):
        c = _make_consumer()
        r = _flood_result("Too Many Requests: retry after 12 seconds")
        assert c._extract_retry_after_seconds(r) == 12.0

    def test_parses_from_raw_response_dict(self):
        c = _make_consumer()
        r = _flood_result(retry_after=42)
        assert c._extract_retry_after_seconds(r) == 42.0

    def test_parses_from_raw_response_attribute(self):
        c = _make_consumer()
        r = SimpleNamespace(
            success=False,
            error="flood",
            raw_response=SimpleNamespace(retry_after=18),
            retryable=True,
        )
        assert c._extract_retry_after_seconds(r) == 18.0

    def test_returns_none_when_no_hint(self):
        c = _make_consumer()
        r = SimpleNamespace(
            success=False,
            error="some other transient error",
            raw_response=None,
            retryable=True,
        )
        assert c._extract_retry_after_seconds(r) is None

    def test_handles_garbage_retry_after(self):
        c = _make_consumer()
        r = SimpleNamespace(
            success=False,
            error="flood",
            raw_response={"retry_after": "not-a-number"},
            retryable=True,
        )
        # Dict value not parseable -> falls through to regex on error; "flood"
        # alone has no "Retry in N" -> None.
        assert c._extract_retry_after_seconds(r) is None


class TestApplyFloodSuspend:
    """Verify _apply_flood_suspend stamps the window with caps applied."""

    def test_uses_parsed_retry_after(self):
        c = _make_consumer()
        secs = c._apply_flood_suspend(_flood_result("Retry in 30 seconds"))
        assert secs == 30.0
        assert c._suspended_until_monotonic > 0.0

    def test_caps_at_max(self):
        c = _make_consumer()
        secs = c._apply_flood_suspend(_flood_result("Retry in 9999 seconds"))
        assert secs == c._MAX_FLOOD_SUSPEND_SECONDS

    def test_floors_at_min_when_no_hint(self):
        c = _make_consumer()
        secs = c._apply_flood_suspend(_flood_result("flood", retry_after=None))
        assert secs == c._MIN_FLOOD_SUSPEND_SECONDS


class TestIsSuspended:
    """Verify _is_suspended toggles correctly."""

    def test_fresh_consumer_not_suspended(self):
        c = _make_consumer()
        assert not c._is_suspended()

    def test_after_apply_flood_suspend_is_suspended(self):
        c = _make_consumer()
        c._apply_flood_suspend(_flood_result("Retry in 30 seconds"))
        assert c._is_suspended()

    def test_is_suspended_respects_finalize_bypass_in_send_or_edit(self):
        """The suspend gate is checked inside _send_or_edit, not in _is_suspended
        itself.  Verify the gate behavior end-to-end."""
        # See TestSendOrEditSuspendGate below for the integration assertion.
        pass


class TestSendOrEditSuspendGate:
    """Verify _send_or_edit skips platform calls while suspended."""

    @pytest.mark.asyncio
    async def test_mid_stream_edit_skipped_during_suspend(self):
        """When suspended, a mid-stream edit returns False and does NOT call
        edit_message — the text stays buffered in _accumulated for later."""
        consumer = _make_consumer()
        # Establish an existing message (so subsequent _send_or_edit edits).
        consumer._message_id = "msg_1"
        consumer._last_sent_text = "previous text"
        # Enter suspend window.
        consumer._apply_flood_suspend(_flood_result("Retry in 30 seconds"))

        result = await consumer._send_or_edit("newer text accumulation")

        assert result is False
        consumer.adapter.edit_message.assert_not_called()
        consumer.adapter.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_finalize_bypasses_suspend_gate(self):
        """Final flush (finalize=True) still attempts the edit even mid-suspend
        so the completed answer has a chance to land.  Ported from openclaw
        draft-stream.ts line 339 comment."""
        consumer = _make_consumer()
        consumer._message_id = "msg_1"
        consumer._last_sent_text = "previous"
        consumer._apply_flood_suspend(_flood_result("Retry in 30 seconds"))
        # Finalize edit succeeds.
        consumer.adapter.edit_message = AsyncMock(return_value=_ok_result("msg_1"))

        result = await consumer._send_or_edit("final answer", finalize=True)

        assert result is True
        consumer.adapter.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_after_suspend_delivers_latest_text(self):
        """After the suspend window expires, the next edit delivers the latest
        accumulated text in a single call (not the stale oldest)."""
        consumer = _make_consumer()
        consumer._message_id = "msg_1"
        consumer._last_sent_text = "old"
        # Stamp an already-expired suspend window (1ns in the past).
        consumer._suspended_until_monotonic = 0.0
        consumer.adapter.edit_message = AsyncMock(return_value=_ok_result("msg_1"))

        result = await consumer._send_or_edit("the latest accumulated text")

        assert result is True
        consumer.adapter.edit_message.assert_called_once()
        sent_content = consumer.adapter.edit_message.call_args[1]["content"]
        assert sent_content == "the latest accumulated text"


class TestSuspendOnFloodStrike:
    """Verify a flood-control edit failure stamps the suspend window."""

    @pytest.mark.asyncio
    async def test_flood_edit_failure_sets_suspend_window(self):
        consumer = _make_consumer()
        consumer._message_id = "msg_1"
        consumer._last_sent_text = "previous"
        flood = _flood_result("Flood control exceeded. Retry in 25 seconds")
        consumer.adapter.edit_message = AsyncMock(return_value=flood)

        assert not consumer._is_suspended()
        result = await consumer._send_or_edit("more text")
        # Mid-stream flood failure returns False (existing contract).
        assert result is False
        # Critical fix: suspend window is now set to ~now + 25s.
        assert consumer._is_suspended()
        assert consumer._flood_strikes == 1

    @pytest.mark.asyncio
    async def test_successful_edit_clears_suspend_window(self):
        """A subsequent successful edit resets _suspended_until_monotonic to 0
        (mirrors openclaw resetting suspendedUntilMs = 0 on
        consecutivePreviewFailures = 0)."""
        consumer = _make_consumer()
        consumer._message_id = "msg_1"
        consumer._last_sent_text = "previous"
        # Pre-suspend (use finalize=True below to bypass the gate and reach
        # the success branch — mid-stream edits are correctly skipped while
        # suspended).
        consumer._suspended_until_monotonic = float("inf")
        consumer.adapter.edit_message = AsyncMock(return_value=_ok_result("msg_1"))

        result = await consumer._send_or_edit("fresh text", finalize=True)

        assert result is True
        assert consumer._suspended_until_monotonic == 0.0
        assert not consumer._is_suspended()
