"""
Tests for BasePlatformAdapter._send_with_retry and _is_retryable_error.

Verifies that:
- Transient network errors trigger retry with backoff
- Permanent errors fall back to plain-text immediately (no retry)
- User receives a delivery-failure notice when all retries are exhausted
- Successful sends on retry return success
- SendResult.retryable flag is respected
- Flood-control errors wait the clamped retry_after seconds (3-60s, default 5s)
  instead of exponential backoff, mirroring gateway/stream_consumer.py
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from gateway.platforms.base import (
    BasePlatformAdapter,
    SendResult,
    _RETRYABLE_ERROR_PATTERNS,
    _FLOOD_RETRY_AFTER_RE,
    _FLOOD_WAIT_MAX_SECONDS,
    _FLOOD_WAIT_MIN_SECONDS,
    _FLOOD_WAIT_DEFAULT_SECONDS,
)
from gateway.platforms.base import Platform, PlatformConfig


# ---------------------------------------------------------------------------
# Minimal concrete adapter for testing (no real network)
# ---------------------------------------------------------------------------

class _StubAdapter(BasePlatformAdapter):
    def __init__(self):
        cfg = PlatformConfig()
        super().__init__(cfg, Platform.TELEGRAM)
        self._send_results = []   # queue of SendResult to return per call
        self._send_calls = []     # record of (chat_id, content) sent

    def _next_result(self) -> SendResult:
        if self._send_results:
            return self._send_results.pop(0)
        return SendResult(success=True, message_id="ok")

    async def send(self, chat_id, content, reply_to=None, metadata=None, **kwargs) -> SendResult:
        self._send_calls.append((chat_id, content))
        return self._next_result()

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def send_typing(self, chat_id, metadata=None) -> None:
        pass

    async def get_chat_info(self, chat_id):
        return {"name": "test", "type": "direct", "chat_id": chat_id}


# ---------------------------------------------------------------------------
# _is_retryable_error
# ---------------------------------------------------------------------------

class TestIsRetryableError:
    def test_none_is_not_retryable(self):
        assert not _StubAdapter._is_retryable_error(None)

    def test_empty_string_is_not_retryable(self):
        assert not _StubAdapter._is_retryable_error("")

    @pytest.mark.parametrize("pattern", _RETRYABLE_ERROR_PATTERNS)
    def test_known_pattern_is_retryable(self, pattern):
        assert _StubAdapter._is_retryable_error(f"httpx.{pattern.title()}: connection dropped")

    def test_permission_error_not_retryable(self):
        assert not _StubAdapter._is_retryable_error("Forbidden: bot was blocked by the user")

    def test_bad_request_not_retryable(self):
        assert not _StubAdapter._is_retryable_error("Bad Request: can't parse entities")

    def test_case_insensitive(self):
        assert _StubAdapter._is_retryable_error("CONNECTERROR: host unreachable")

    def test_timeout_not_retryable(self):
        assert not _StubAdapter._is_retryable_error("ReadTimeout: request timed out")

    def test_timed_out_not_retryable(self):
        assert not _StubAdapter._is_retryable_error("Timed out waiting for response")

    def test_connect_timeout_is_retryable(self):
        assert _StubAdapter._is_retryable_error("ConnectTimeout: connection timed out")


# ---------------------------------------------------------------------------
# _is_timeout_error
# ---------------------------------------------------------------------------

class TestIsTimeoutError:
    def test_none_is_not_timeout(self):
        assert not _StubAdapter._is_timeout_error(None)

    def test_empty_is_not_timeout(self):
        assert not _StubAdapter._is_timeout_error("")

    def test_timed_out(self):
        assert _StubAdapter._is_timeout_error("Timed out waiting for response")

    def test_read_timeout(self):
        assert _StubAdapter._is_timeout_error("ReadTimeout: request timed out")

    def test_write_timeout(self):
        assert _StubAdapter._is_timeout_error("WriteTimeout: send stalled")

    def test_connect_timeout_not_flagged(self):
        """ConnectTimeout is a connection error, not a delivery-ambiguous timeout."""
        assert not _StubAdapter._is_timeout_error("ConnectTimeout: host unreachable")

    def test_connection_error_not_timeout(self):
        assert not _StubAdapter._is_timeout_error("ConnectionError: host unreachable")


# ---------------------------------------------------------------------------
# _send_with_retry — success on first attempt
# ---------------------------------------------------------------------------

class TestSendWithRetrySuccess:
    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        adapter = _StubAdapter()
        adapter._send_results = [SendResult(success=True, message_id="123")]
        result = await adapter._send_with_retry("chat1", "hello")
        assert result.success
        assert len(adapter._send_calls) == 1

    @pytest.mark.asyncio
    async def test_returns_message_id(self):
        adapter = _StubAdapter()
        adapter._send_results = [SendResult(success=True, message_id="abc")]
        result = await adapter._send_with_retry("chat1", "hi")
        assert result.message_id == "abc"


# ---------------------------------------------------------------------------
# _send_with_retry — network error with successful retry
# ---------------------------------------------------------------------------

class TestSendWithRetryNetworkRetry:
    @pytest.mark.asyncio
    async def test_retries_on_connect_error_and_succeeds(self):
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="httpx.ConnectError: connection refused"),
            SendResult(success=True, message_id="ok"),
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "hello", max_retries=2, base_delay=0)
        assert result.success
        assert len(adapter._send_calls) == 2  # initial + 1 retry

    @pytest.mark.asyncio
    async def test_timeout_not_retried_to_prevent_duplicates(self):
        """ReadTimeout is NOT retried because the request may have reached
        the server — retrying a non-idempotent send risks duplicate delivery.
        It also skips plain-text fallback (timeout is not a formatting issue)."""
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="ReadTimeout: request timed out"),
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._send_with_retry("chat1", "hello", max_retries=3, base_delay=0)
        # No retry, no fallback — timeout returns failure immediately
        mock_sleep.assert_not_called()
        assert not result.success
        assert len(adapter._send_calls) == 1

    @pytest.mark.asyncio
    async def test_connect_timeout_still_retried(self):
        """ConnectTimeout is safe to retry — the connection was never established."""
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="ConnectTimeout: connection timed out"),
            SendResult(success=True, message_id="ok"),
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "hello", max_retries=2, base_delay=0)
        assert result.success
        assert len(adapter._send_calls) == 2

    @pytest.mark.asyncio
    async def test_retryable_flag_respected(self):
        """SendResult.retryable=True should trigger retry even if error string doesn't match."""
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="internal platform error", retryable=True),
            SendResult(success=True, message_id="ok"),
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "hello", max_retries=2, base_delay=0)
        assert result.success
        assert len(adapter._send_calls) == 2

    @pytest.mark.asyncio
    async def test_network_to_nonnetwork_transition_falls_back_to_plaintext(self):
        """If error switches from network to formatting mid-retry, fall through to plain-text fallback."""
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="httpx.ConnectError: host unreachable"),
            SendResult(success=False, error="Bad Request: can't parse entities"),
            SendResult(success=True, message_id="fallback_ok"),  # plain-text fallback
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "**bold**", max_retries=2, base_delay=0)
        assert result.success
        # 3 calls: initial (network) + 1 retry (non-network, breaks loop) + plain-text fallback
        assert len(adapter._send_calls) == 3
        assert "plain text" in adapter._send_calls[-1][1].lower()


# ---------------------------------------------------------------------------
# _send_with_retry — all retries exhausted → user notification
# ---------------------------------------------------------------------------

class TestSendWithRetryExhausted:
    @pytest.mark.asyncio
    async def test_sends_user_notice_after_exhaustion(self):
        adapter = _StubAdapter()
        network_err = SendResult(success=False, error="httpx.ConnectError: host unreachable")
        # initial + 2 retries + notice attempt
        adapter._send_results = [network_err, network_err, network_err, SendResult(success=True)]
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "hello", max_retries=2, base_delay=0)
        # Result is the last failed one (before notice)
        assert not result.success
        # 4 total calls: 1 initial + 2 retries + 1 notice
        assert len(adapter._send_calls) == 4
        # The notice content should mention delivery failure
        notice_content = adapter._send_calls[-1][1]
        assert "delivery failed" in notice_content.lower() or "Message delivery failed" in notice_content

    @pytest.mark.asyncio
    async def test_notice_send_exception_doesnt_propagate(self):
        """If the notice itself throws, _send_with_retry should not raise."""
        adapter = _StubAdapter()
        network_err = SendResult(success=False, error="ConnectError")
        adapter._send_results = [network_err, network_err, network_err]

        original_send = adapter.send
        call_count = [0]

        async def send_with_notice_failure(chat_id, content, **kwargs):
            call_count[0] += 1
            if call_count[0] > 3:
                raise RuntimeError("notice send also failed")
            return network_err

        adapter.send = send_with_notice_failure
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "hello", max_retries=2, base_delay=0)
        assert not result.success  # still failed, but no exception raised


# ---------------------------------------------------------------------------
# _send_with_retry — non-network failure → plain-text fallback (no retry)
# ---------------------------------------------------------------------------

class TestSendWithRetryFallback:
    @pytest.mark.asyncio
    async def test_non_network_error_falls_back_immediately(self):
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="Bad Request: can't parse entities"),
            SendResult(success=True, message_id="fallback_ok"),
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._send_with_retry("chat1", "**bold**", max_retries=2, base_delay=0)
        # No sleep — no retry loop for non-network errors
        mock_sleep.assert_not_called()
        assert result.success
        assert len(adapter._send_calls) == 2
        # Fallback content should be plain-text notice
        assert "plain text" in adapter._send_calls[1][1].lower()

    @pytest.mark.asyncio
    async def test_fallback_failure_logged_but_not_raised(self):
        adapter = _StubAdapter()
        adapter._send_results = [
            SendResult(success=False, error="Forbidden: bot blocked"),
            SendResult(success=False, error="Forbidden: bot blocked"),
        ]
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._send_with_retry("chat1", "hello", max_retries=2)
        assert not result.success
        assert len(adapter._send_calls) == 2  # original + fallback only


# ---------------------------------------------------------------------------
# Flood-control module constants (parity with stream_consumer.py)
# ---------------------------------------------------------------------------

class TestFloodModuleConstants:
    """Constants for flood-aware retry must match the stream_consumer contract."""

    def test_flood_retry_after_regex_compiles(self):
        assert _FLOOD_RETRY_AFTER_RE.search("Retry in 27 seconds") is not None
        assert _FLOOD_RETRY_AFTER_RE.search("retry after 30 seconds") is not None
        # singular form
        assert _FLOOD_RETRY_AFTER_RE.search("Retry in 1 second") is not None
        # non-match (the regex requires the trailing "second(s)" suffix,
        # mirroring stream_consumer._FLOOD_RETRY_AFTER_RE byte-for-byte;
        # bare "retry after 30" without a unit is not a parseable hint and
        # falls through to the _FLOOD_WAIT_DEFAULT_SECONDS fallback in the
        # retry path).
        assert _FLOOD_RETRY_AFTER_RE.search("no hint here") is None
        assert _FLOOD_RETRY_AFTER_RE.search("retry after 30") is None

    def test_max_seconds_is_60(self):
        assert _FLOOD_WAIT_MAX_SECONDS == 60.0

    def test_min_seconds_is_3(self):
        assert _FLOOD_WAIT_MIN_SECONDS == 3.0

    def test_default_seconds_is_5(self):
        assert _FLOOD_WAIT_DEFAULT_SECONDS == 5.0


# ---------------------------------------------------------------------------
# _is_flood_error / _extract_retry_after_seconds — pure function tests
# ---------------------------------------------------------------------------

class TestFloodAwareRetryHelpers:
    """Pure-function tests for the flood detection helpers.

    Mirrors the stream_consumer vocabulary so both layers speak the same
    flood language.
    """

    # ---- _is_flood_error (string-based) ----

    @pytest.mark.parametrize("err", [
        "Flood control exceeded. Retry in 27 seconds",
        "Too Many Requests: retry after 30",
        "429 flood",
        "Rate limit exceeded",
        "429 Too Many Requests",
    ])
    def test_is_flood_error_true(self, err):
        assert _StubAdapter._is_flood_error(err) is True

    @pytest.mark.parametrize("err", [
        "ConnectError: refused",
        "Bad Request: can't parse entities",
        "",
        None,
    ])
    def test_is_flood_error_false(self, err):
        assert _StubAdapter._is_flood_error(err) is False

    def test_is_flood_error_case_insensitive(self):
        assert _StubAdapter._is_flood_error("FLOOD CONTROL EXCEEDED") is True
        assert _StubAdapter._is_flood_error("RETRY AFTER 30") is True

    # ---- _extract_retry_after_seconds ----

    def test_extract_from_error_string_retry_in(self):
        result = SendResult(success=False, error="Retry in 27 seconds", raw_response=None)
        assert _StubAdapter._extract_retry_after_seconds(result) == 27.0

    def test_extract_from_error_string_retry_after(self):
        # Regex requires the trailing "seconds" suffix (parity with
        # stream_consumer._FLOOD_RETRY_AFTER_RE).
        result = SendResult(success=False, error="retry after 30 seconds", raw_response=None)
        assert _StubAdapter._extract_retry_after_seconds(result) == 30.0

    def test_extract_from_raw_response_dict(self):
        result = SendResult(success=False, error="flood", raw_response={"retry_after": 42})
        assert _StubAdapter._extract_retry_after_seconds(result) == 42.0

    def test_extract_from_raw_response_attribute(self):
        # PTB RetryAfter shape: raw_response.retry_after attribute
        result = SendResult(
            success=False,
            error="flood",
            raw_response=SimpleNamespace(retry_after=18),
        )
        assert _StubAdapter._extract_retry_after_seconds(result) == 18.0

    def test_extract_returns_none_when_no_hint(self):
        result = SendResult(success=False, error="flood", raw_response=None)
        assert _StubAdapter._extract_retry_after_seconds(result) is None

    def test_extract_returns_none_when_not_flood_error(self):
        # Mirrors stream_consumer test_handles_garbage_retry_after: when the
        # error string isn't flood-shaped AND raw_response has no parseable
        # retry_after, the helper returns None (no false positive).
        result = SendResult(success=False, error="other error", raw_response=None)
        assert _StubAdapter._extract_retry_after_seconds(result) is None

    def test_extract_returns_none_for_garbage_retry_after(self):
        # raw_response.retry_after is a non-numeric string AND the error
        # string carries no regex match -> helper must return None, not crash.
        result = SendResult(
            success=False,
            error="flood",
            raw_response={"retry_after": "not-a-number"},
        )
        assert _StubAdapter._extract_retry_after_seconds(result) is None

    def test_extract_prefers_raw_response_over_regex(self):
        # When both sources are present, the structured value wins.
        result = SendResult(
            success=False,
            error="Retry in 27 seconds",
            raw_response={"retry_after": 99},
        )
        assert _StubAdapter._extract_retry_after_seconds(result) == 99.0

    def test_extract_handles_int_retry_after(self):
        result = SendResult(success=False, error="flood", raw_response={"retry_after": 15})
        # int should coerce to float cleanly
        assert _StubAdapter._extract_retry_after_seconds(result) == 15.0
