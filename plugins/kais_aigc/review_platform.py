"""review_platform.py — ReviewPlatformClient (review platform REST API).

Phase 32 plan 32-02. Reference port of Node.js ``lib/review-platform-client.js``
plus the HMAC callback verifier (``bin/callback-server.js``).

v5.0 hardenings vs the Node.js reference (documented in CONTEXT.md):

* **CRITICAL-FINDING-03 (JWT bearer auth):** the Node.js ``submitReview`` and
  ``queryReviewStatus`` methods do NOT attach any ``Authorization`` header — the
  Python port generates a short-lived HS256 JWT (5 min expiration, signed with
  ``KAIS_REVIEW_JWT_SECRET``) and attaches it as ``Authorization: Bearer <jwt>``
  on every outbound request when the secret is set. Required by GPU-DIRECT-02.
* **CRITICAL-FINDING-04 / D-11 (HMAC 5-minute timestamp window):** the Node.js
  ``verifyHmac()`` is a plain body HMAC match. The Python ``verify_callback``
  adds a 300-second timestamp tolerance check (``abs(now - ts) > 300`` rejects)
  and uses ``hmac.compare_digest`` for constant-time comparison.

All env reads happen at construction time. Missing URL → falls back to the
default internal-network URL (does NOT raise). Degrade-mode is uniform: every
network error / 5xx / timeout returns a ``{"degraded": True, ...}`` envelope
(DEGRADED_AUTO disposition = APPROVED — pipeline auto-advances when the human
review service is unavailable). 4xx client errors raise ``ReviewClientError``.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any, Optional

import httpx
import jwt  # PyJWT[crypto]==2.13.0 — already in pyproject.toml

logger = logging.getLogger(__name__)


class ReviewClientError(Exception):
    """Raised for HTTP 4xx client errors and unrecoverable failures.

    Mirrors the Node.js ``ReviewClientError``: carries a ``status`` and ``url``
    so callers can distinguish transient (degrade) from caller-bug (raise)
    failures.

    Attributes:
        status: HTTP status code when the error originated from a response.
        url: Request URL when known.
    """

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        url: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.url = url


class ReviewPlatformClient:
    """Sync httpx client for the review platform REST API.

    Two public operations plus the callback verifier:

    - ``submit_review(...)`` → ``POST /api/v1/reviews`` (JWT bearer auth).
    - ``query_review_status(review_id)`` → ``GET /api/v1/reviews/{id}``.
    - ``verify_callback(body, signature, timestamp)`` → HMAC-SHA256 verifier
      with 5-min timestamp window (constant-time comparison).

    Degrade envelope (returned, never raised, on 5xx / connect-error / timeout):

    .. code-block:: python

        {
            "degraded": True,
            "client": "review_platform",
            "operation": "submit" | "query",
            "reason": "<short error message>",
            "state": "DEGRADED_AUTO",
            "disposition": "APPROVED",
        }

    4xx errors raise ``ReviewClientError`` — they indicate a caller bug
    (wrong content_ref, malformed body, etc.).
    """

    # Node.js ref default (review-platform-client.js line 34).
    DEFAULT_BASE_URL = "http://192.168.71.140:8090"
    # Node.js ref default timeout (10s).
    DEFAULT_TIMEOUT = 10.0
    # GPU-DIRECT-02 / D-11: 5-minute timestamp tolerance for callbacks.
    CALLBACK_TIMESTAMP_TOLERANCE_SEC = 300
    # JWT lifetime matches the callback window (5 min).
    JWT_LIFETIME_SEC = 300

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        jwt_secret: Optional[str] = None,
        callback_secret: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        # Resolve base URL: explicit arg → KAIS_REVIEW_URL → default.
        self._base_url = (
            base_url
            or os.environ.get("KAIS_REVIEW_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        # JWT secret: explicit arg (incl. "") → KAIS_REVIEW_JWT_SECRET → None.
        # Note: explicit "" disables JWT (dev mode), explicit None falls back to env.
        self._jwt_secret = (
            jwt_secret
            if jwt_secret is not None
            else os.environ.get("KAIS_REVIEW_JWT_SECRET")
        )
        # Callback secret: explicit arg → KAIS_REVIEW_CALLBACK_SECRET → "" (dev).
        self._callback_secret = (
            callback_secret
            if callback_secret is not None
            else os.environ.get("KAIS_REVIEW_CALLBACK_SECRET", "")
        )
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        # transport=None → real network; tests inject httpx.MockTransport(handler).
        self._client = httpx.Client(timeout=self._timeout, transport=transport)

    # ────────────────── Internal helpers ──────────────────

    def _make_jwt(self) -> Optional[str]:
        """Generate a short-lived HS256 JWT for outbound auth.

        Claims: ``iat`` (issued-at), ``exp`` (expiry = now + 300s),
        ``sub`` ("kais-movie-agent"). Returns ``None`` when the JWT secret is
        unset or empty (dev mode — no auth attached, mirrors Node.js behavior).
        """
        if not self._jwt_secret:
            return None
        now = int(time.time())
        token = jwt.encode(
            {
                "iat": now,
                "exp": now + self.JWT_LIFETIME_SEC,
                "sub": "kais-movie-agent",
            },
            self._jwt_secret,
            algorithm="HS256",
        )
        # PyJWT >= 2 returns str (not bytes).
        return token

    def _headers(self) -> dict[str, str]:
        """Build request headers, attaching JWT bearer when configured.

        CRITICAL-FINDING-03: the Node.js ref does NOT attach Authorization —
        this Python port does, per GPU-DIRECT-02.
        """
        h: dict[str, str] = {"Content-Type": "application/json"}
        token = self._make_jwt()
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _degrade(
        self,
        operation: str,
        reason: str,
        *,
        state: str = "DEGRADED_AUTO",
        disposition: str = "APPROVED",
    ) -> dict[str, Any]:
        """Return the uniform degrade envelope and log a WARNING.

        Matches the Node.js ref's DEGRADED_AUTO behavior: when the review
        service is unavailable, the pipeline auto-advances rather than block.
        """
        logger.warning(
            "review_platform %s degraded: %s (state=%s disposition=%s)",
            operation,
            reason,
            state,
            disposition,
        )
        return {
            "degraded": True,
            "client": "review_platform",
            "operation": operation,
            "reason": reason,
            "state": state,
            "disposition": disposition,
        }

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Central HTTP wrapper applying degrade/raise rules.

        - ``httpx.ConnectError`` / ``httpx.TimeoutException`` → degrade.
        - HTTP >= 500 → degrade (server error — service unavailable).
        - HTTP 4xx → raise ``ReviewClientError`` (caller bug).
        - 2xx → parse JSON body, return parsed dict.

        Returns either the parsed JSON dict (2xx) or a degrade envelope
        (transient failures).
        """
        url = f"{self._base_url}{path}"
        try:
            response = self._client.request(
                method,
                url,
                headers=self._headers(),
                json=body if body is not None else None,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            return self._degrade("request", str(exc))
        except httpx.HTTPError as exc:
            # Other transport errors (read error, etc.) — also degrade.
            return self._degrade("request", str(exc))

        status = response.status_code
        if status >= 500:
            return self._degrade("request", f"HTTP {status}")
        if status >= 400:
            text = response.text[:200] if response.text else ""
            raise ReviewClientError(
                f"HTTP {status}: {text}" if text else f"HTTP {status}",
                status=status,
                url=url,
            )
        try:
            return response.json()
        except ValueError as exc:
            # Non-JSON 2xx response — caller bug (server contract violation).
            raise ReviewClientError(
                f"Non-JSON response: {exc}",
                status=status,
                url=url,
            )

    # ────────────────── Public API ──────────────────

    def submit_review(
        self,
        *,
        type: str,
        content_ref: str,
        metadata: Optional[dict[str, Any]] = None,
        callback_url: Optional[str] = None,
        callback_secret: Optional[str] = None,
        priority: str = "normal",
        risk_score: float = 0.5,
    ) -> dict[str, Any]:
        """Submit a review to ``POST /api/v1/reviews``.

        Mirrors Node.js ``submitReview`` request body shape. On success
        returns ``{"review_id", "state", "routing"}`` extracted from the
        ``data`` envelope. On degrade returns the degrade envelope unchanged.
        """
        body: dict[str, Any] = {
            "type": type,
            "content_ref": content_ref,
            "source_system": "kais-movie-agent",
            "metadata": metadata,
            "priority": priority,
            "risk_score": risk_score,
        }
        if callback_url:
            body["callback_url"] = callback_url
        # Per-review callback secret falls back to the client-level secret.
        effective_callback_secret = callback_secret or self._callback_secret or None
        if effective_callback_secret:
            body["callback_secret"] = effective_callback_secret

        result = self._request("POST", "/api/v1/reviews", body)
        if isinstance(result, dict) and result.get("degraded"):
            return result

        data = (result or {}).get("data", {}) if isinstance(result, dict) else {}
        return {
            "review_id": data.get("review_id"),
            "state": data.get("state"),
            "routing": data.get("routing"),
        }

    def query_review_status(self, review_id: Any) -> dict[str, Any]:
        """Query review status via ``GET /api/v1/reviews/{review_id}``.

        Mirrors Node.js ``queryReviewStatus``. Returns
        ``{"review_id", "state", "disposition", "version"}`` extracted from the
        ``data`` envelope. On degrade returns the degrade envelope unchanged.
        """
        result = self._request("GET", f"/api/v1/reviews/{review_id}")
        if isinstance(result, dict) and result.get("degraded"):
            return result

        data = (result or {}).get("data", {}) if isinstance(result, dict) else {}
        return {
            "review_id": data.get("review_id", data.get("id")),
            "state": data.get("state"),
            "disposition": data.get("disposition"),
            "version": data.get("version"),
        }

    def verify_callback(
        self,
        body: str | bytes,
        signature: str,
        timestamp: int | float | str,
    ) -> bool:
        """Verify an HMAC-SHA256 callback signature with a 5-min window.

        Three-step verification (D-11 + CRITICAL-FINDING-04):

        1. **Dev-mode escape:** if ``callback_secret`` is unset, accept all
           callbacks (mirrors Node.js ``bin/callback-server.js`` dev mode).
        2. **Timestamp window:** reject if
           ``abs(int(time.time()) - int(timestamp)) > 300`` seconds. Mitigates
           replay attacks.
        3. **Constant-time HMAC match:** compute
           ``sha256=<hex(hmac_sha256(secret, body))>`` and compare with
           ``hmac.compare_digest`` (timing-attack resistant).

        Args:
            body: Raw callback body (str or bytes).
            signature: ``X-Callback-Signature`` header value (``sha256=<hex>``).
            timestamp: ``X-Timestamp`` header value (Unix seconds).

        Returns:
            True if the callback is valid (or dev mode), False otherwise.
        """
        # Step 1: dev-mode escape (no secret → accept all).
        if not self._callback_secret:
            return True

        # Step 2: timestamp window (replay protection — CRITICAL-FINDING-04).
        try:
            ts_int = int(timestamp)
        except (TypeError, ValueError):
            logger.warning("review_platform callback rejected: bad timestamp")
            return False
        now_int = int(time.time())
        if abs(now_int - ts_int) > self.CALLBACK_TIMESTAMP_TOLERANCE_SEC:
            logger.warning(
                "review_platform callback rejected: timestamp outside %ss window (now=%s ts=%s)",
                self.CALLBACK_TIMESTAMP_TOLERANCE_SEC,
                now_int,
                ts_int,
            )
            return False

        # Step 3: constant-time HMAC match.
        body_bytes = body.encode("utf-8") if isinstance(body, str) else body
        expected = (
            "sha256="
            + hmac.new(
                self._callback_secret.encode("utf-8"),
                body_bytes,
                hashlib.sha256,
            ).hexdigest()
        )
        return hmac.compare_digest(expected, signature)

    # ────────────────── Lifecycle ──────────────────

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "ReviewPlatformClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
