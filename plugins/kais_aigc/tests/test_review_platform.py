"""test_review_platform.py — mocked-HTTP tests for ReviewPlatformClient.

Mirrors ``tests/tools/test_microsoft_graph_client.py`` MockTransport pattern
(per CONTEXT.md D-04). No real network calls — every HTTP-exercising client is
constructed with ``transport=httpx.MockTransport(handler)``.

Covers (target 8-12 tests):

- ``TestReviewPlatformClient`` (HTTP): happy path submit/query, JWT attachment,
  degrade on 5xx + connect-error, raise on 4xx, no-JWT-when-secret-unset.
- ``TestReviewCallbackVerifier`` (HMAC): valid signature, expired timestamp,
  future timestamp, tampered body, dev-mode escape.
"""

from __future__ import annotations

import hashlib
import hmac
import time

import httpx
import jwt
import pytest

from plugins.kais_aigc.review_platform import (
    ReviewClientError,
    ReviewPlatformClient,
)

# ────────────────── Helpers ──────────────────


def _client(handler, **kw) -> ReviewPlatformClient:
    """Build a ReviewPlatformClient whose httpx calls are mocked by ``handler``.

    Defaults: base_url + jwt_secret + callback_secret set so tests can exercise
    JWT bearer attachment and HMAC verification uniformly. Callers may override
    any of these via kwargs (e.g. ``jwt_secret=None`` for the no-JWT test).
    """
    kw.setdefault("base_url", "http://test-review")
    kw.setdefault("jwt_secret", "test-jwt-secret")
    kw.setdefault("callback_secret", "test-callback-secret")
    kw["transport"] = httpx.MockTransport(handler)
    return ReviewPlatformClient(**kw)


def _hmac_sig(secret: str, body: str) -> str:
    """Compute the ``sha256=<hex>`` signature the callback server would send."""
    digest = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


# ────────────────── HTTP client tests ──────────────────


class TestReviewPlatformClient:
    """HTTP-layer tests for submit_review / query_review_status / _headers."""

    def test_submit_review_happy_path_attaches_jwt(self):
        """submit_review returns review_id/state/routing AND attaches a valid
        HS256 JWT (CRITICAL-FINDING-03 — Node.js ref does NOT attach JWT)."""
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert request.url.path == "/api/v1/reviews"
            assert request.method == "POST"
            return httpx.Response(
                200,
                json={
                    "data": {
                        "review_id": 42,
                        "state": "pending",
                        "routing": "director",
                    }
                },
            )

        with _client(handler) as c:
            result = c.submit_review(
                type="pipeline_phase",
                content_ref="EP01:art-direction",
            )

        assert result["review_id"] == 42
        assert result["state"] == "pending"
        assert result["routing"] == "director"

        # JWT bearer attached + decodable with the configured secret.
        assert len(captured) == 1
        auth = captured[0].headers.get("Authorization")
        assert auth is not None
        assert auth.startswith("Bearer ")
        token = auth[len("Bearer "):]
        decoded = jwt.decode(token, "test-jwt-secret", algorithms=["HS256"])
        assert decoded["sub"] == "kais-movie-agent"
        # exp must be within 5 minutes of now.
        now = int(time.time())
        assert decoded["exp"] - now <= 300
        assert decoded["exp"] - now > 0
        # iat present.
        assert "iat" in decoded

    def test_submit_review_degrades_on_503_to_auto_approved(self):
        """5xx → DEGRADED_AUTO envelope with disposition APPROVED (pipeline
        auto-advances when the review service is unavailable)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        with _client(handler) as c:
            result = c.submit_review(
                type="pipeline_phase",
                content_ref="EP01:character",
            )

        assert result["degraded"] is True
        assert result["client"] == "review_platform"
        assert result["state"] == "DEGRADED_AUTO"
        assert result["disposition"] == "APPROVED"
        assert "HTTP 503" in result["reason"]

    def test_submit_review_degrades_on_connect_error(self):
        """ConnectError → degrade envelope (network unreachable)."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        with _client(handler) as c:
            result = c.submit_review(
                type="pipeline_phase",
                content_ref="EP01:scene",
            )

        assert result["degraded"] is True
        assert "refused" in result["reason"]

    def test_submit_review_degrades_on_timeout(self):
        """TimeoutException → degrade envelope (service slow / unresponsive)."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timed out", request=request)

        with _client(handler) as c:
            result = c.submit_review(
                type="pipeline_phase",
                content_ref="EP01:storyboard",
            )

        assert result["degraded"] is True

    def test_submit_review_raises_on_400(self):
        """4xx → ReviewClientError with status (caller bug, not transient)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad type"})

        with _client(handler) as c:
            with pytest.raises(ReviewClientError) as exc_info:
                c.submit_review(type="invalid_type", content_ref="EP01:x")

        assert exc_info.value.status == 400

    def test_query_review_status_happy_path(self):
        """query_review_status extracts review_id/state/disposition/version."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/reviews/42"
            assert request.method == "GET"
            return httpx.Response(
                200,
                json={
                    "data": {
                        "review_id": 42,
                        "state": "approved",
                        "disposition": "APPROVED",
                        "version": 3,
                    }
                },
            )

        with _client(handler) as c:
            result = c.query_review_status(42)

        assert result["review_id"] == 42
        assert result["state"] == "approved"
        assert result["disposition"] == "APPROVED"
        assert result["version"] == 3

    def test_query_review_status_degrades_on_500(self):
        """5xx on query → degrade envelope."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        with _client(handler) as c:
            result = c.query_review_status(99)

        assert result["degraded"] is True
        assert result["state"] == "DEGRADED_AUTO"

    def test_no_jwt_header_when_secret_unset(self, monkeypatch):
        """When jwt_secret is unset (None) AND env is cleared, no Authorization
        header is attached (dev mode — matches Node.js ref behavior)."""
        monkeypatch.delenv("KAIS_REVIEW_JWT_SECRET", raising=False)
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                json={"data": {"review_id": 1, "state": "pending", "routing": "auto"}},
            )

        with _client(handler, jwt_secret=None) as c:
            c.submit_review(type="pipeline_phase", content_ref="EP01:x")

        assert len(captured) == 1
        assert "Authorization" not in captured[0].headers


# ────────────────── HMAC verifier tests ──────────────────


class TestReviewCallbackVerifier:
    """HMAC verifier tests — verify_callback is pure compute (no HTTP)."""

    def _verifier(self, **kw) -> ReviewPlatformClient:
        """Build a client with the test callback secret (no transport needed
        — verify_callback never touches the network)."""
        return ReviewPlatformClient(
            base_url="http://test-review",
            jwt_secret="test-jwt-secret",
            callback_secret="test-callback-secret",
            **kw,
        )

    def test_verify_callback_accepts_valid_signature(self):
        """Valid HMAC signature + fresh timestamp → True."""
        body = '{"review_id":42,"action":"approve"}'
        ts = int(time.time())
        sig = _hmac_sig("test-callback-secret", body)

        with self._verifier() as c:
            assert c.verify_callback(body, sig, ts) is True

    def test_verify_callback_rejects_expired_timestamp(self):
        """Timestamp 10 min ago (> 5min window) → False (CRITICAL-FINDING-04)."""
        body = '{"review_id":42,"action":"approve"}'
        ts = int(time.time()) - 600  # 10 minutes ago.
        sig = _hmac_sig("test-callback-secret", body)

        with self._verifier() as c:
            assert c.verify_callback(body, sig, ts) is False

    def test_verify_callback_rejects_future_timestamp(self):
        """Timestamp 10 min in the future (> 5min window) → False (replay
        protection in both directions)."""
        body = '{"review_id":42,"action":"approve"}'
        ts = int(time.time()) + 600  # 10 minutes ahead.
        sig = _hmac_sig("test-callback-secret", body)

        with self._verifier() as c:
            assert c.verify_callback(body, sig, ts) is False

    def test_verify_callback_rejects_tampered_body(self):
        """Signature computed over a different body → False (constant-time
        compare_digest — CRITICAL-FINDING-04 / D-11)."""
        signed_body = '{"review_id":42,"action":"approve"}'
        tampered_body = '{"review_id":99,"action":"reject"}'
        ts = int(time.time())
        # Signature computed over the ORIGINAL body, sent with the TAMPERED body.
        sig = _hmac_sig("test-callback-secret", signed_body)

        with self._verifier() as c:
            assert c.verify_callback(tampered_body, sig, ts) is False

    def test_verify_callback_rejects_wrong_signature_format(self):
        """Malformed signature (no sha256= prefix) → False."""
        body = '{"review_id":42}'
        ts = int(time.time())

        with self._verifier() as c:
            # Garbage signature.
            assert c.verify_callback(body, "garbage", ts) is False
            # Empty signature.
            assert c.verify_callback(body, "", ts) is False

    def test_verify_callback_dev_mode_when_secret_unset(self):
        """When callback_secret is empty (""), accept all callbacks (matches
        Node.js bin/callback-server.js dev mode — line 48)."""
        body = '{"review_id":42}'
        # No real signature — dev mode should accept regardless.
        with ReviewPlatformClient(
            base_url="http://test-review",
            jwt_secret=None,
            callback_secret="",
        ) as c:
            assert c.verify_callback(body, "anything", int(time.time())) is True
            assert c.verify_callback(body, "", 0) is True

    def test_verify_callback_accepts_bytes_body(self):
        """verify_callback handles both str and bytes bodies (callback servers
        may pass raw bytes)."""
        body_str = '{"review_id":42,"action":"approve"}'
        body_bytes = body_str.encode("utf-8")
        ts = int(time.time())
        sig = _hmac_sig("test-callback-secret", body_str)

        with self._verifier() as c:
            assert c.verify_callback(body_bytes, sig, ts) is True

    def test_verify_callback_rejects_bad_timestamp(self):
        """Non-integer timestamp → False (defensive against malformed input)."""
        body = '{"review_id":42}'
        sig = _hmac_sig("test-callback-secret", body)

        with self._verifier() as c:
            assert c.verify_callback(body, sig, "not-a-number") is False
