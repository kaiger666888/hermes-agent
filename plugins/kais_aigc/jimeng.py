"""jimeng.py — JimengClient (jimeng-free-api :5100).

Reference port of Node.js ``lib/jimeng-client.js`` (the 6-subcommand +
session-rotation + exponential-backoff contract). The Node.js file is marked
``@deprecated`` (replaced by the ``dreamina`` CLI in production) — Phase 32
ports the *contract*, not the deprecated implementation details, per
CRITICAL-FINDING-04 + REQUIREMENTS GPU-DIRECT-04.

Key v5.0 deltas vs the Node.js ref:
- Default base URL ``http://localhost:5100`` (REQUIREMENTS GPU-DIRECT-04),
  NOT ``:8003`` (the deprecated Node.js default).
- Ports only the 6 generic subcommands
  (``text2image / image2image / multimodal2video / multiframe2video /
  frames2video / image_upscale``). Specialized composition helpers
  (``submitSeedanceTask``, ``omniReferenceVideo``,
  ``generateIdentityVerification``, ``generateWithSeedLock``,
  ``generateKeyframesBatch``, ``generateCharacterAnchor``) belong to Phase 35/36
  orchestration and are intentionally NOT ported here.
- Auth: ``Authorization: Bearer <session_id>`` header (matches Node.js ref).
- Sessions: ``KAIS_JIMENG_SESSION_ID`` env var supports a comma-separated list
  for rotation on rate-limit strikes.
- Backoff: exponential (1s, 2s, 4s, 8s, 16s cap) on HTTP 429, with session
  rotation after 3 consecutive 429 strikes when multiple sessions are
  configured.

Per CONTEXT.md D-03 (httpx), D-04 (transport + sleep_fn kwargs for tests),
D-06 (env vars), D-09 (degrade envelope). Sync httpx.Client (D-07).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Optional

import httpx

logger = logging.getLogger(__name__)


# 6 subcommands (REQUIREMENTS GPU-DIRECT-04) → (method, path, default_model).
# Endpoints derived from Node.js ref ``lib/jimeng-client.js``:
#   text2image  → POST /v1/images/generations   (generateImage)
#   image2image → POST /v1/images/compositions  (compositions)
#   *_video     → POST /v1/videos/generations   (generateVideo / submitSeedanceTask)
#   upscale     → POST /v1/images/upscales      (Phase 39 E2E will confirm exact path)
SUBCOMMAND_ENDPOINTS: dict[str, tuple[str, str, str]] = {
    "text2image":       ("POST", "/v1/images/generations",  "jimeng-5.0"),
    "image2image":      ("POST", "/v1/images/compositions", "jimeng-5.0"),
    "multimodal2video": ("POST", "/v1/videos/generations",  "jimeng-video-seedance-2.0"),
    "multiframe2video": ("POST", "/v1/videos/generations",  "jimeng-video-seedance-2.0"),
    "frames2video":     ("POST", "/v1/videos/generations",  "jimeng-video-3.5-pro"),
    "image_upscale":    ("POST", "/v1/images/upscales",     "jimeng-upscale-4x"),
}


class JimengError(Exception):
    """Raised for 4xx client errors (caller bug) and unrecoverable failures.

    Mirrors the Node.js ref error class: carries ``status`` (HTTP code, if
    applicable) and ``url`` for diagnostics. Degrade paths do NOT raise —
    they return a degrade envelope (D-09).
    """

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        url: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.url = url

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.status is not None:
            return f"{self.message} (status={self.status})"
        return self.message


class JimengClient:
    """Sync httpx client for the jimeng-free-api service (:5100).

    Dispatches the 6 generic subcommands (REQUIREMENTS GPU-DIRECT-04) to the
    matching endpoint, with rate-limit-aware retry, exponential backoff on
    429, and session rotation when multiple ``KAIS_JIMENG_SESSION_ID`` tokens
    are configured.

    Behavior contract:
    - 2xx → return ``data`` array (Node.js ref unwraps ``json.data``).
    - 429 → exponential backoff (1s, 2s, 4s, 8s, 16s cap). Rotate session
      after ``ROTATE_AFTER_STRIKES`` (default 3) strikes when multiple
      sessions configured. Degrade when ``max_retries`` exhausted.
    - 5xx → degrade immediately (caller may retry via a different session).
    - 4xx (except 429) → raise ``JimengError`` (caller bug).
    - Connect/timeout → backoff and retry once, then degrade.

    Tests inject ``transport=httpx.MockTransport(handler)`` and
    ``sleep_fn=lambda s: None`` to keep the test suite fast and offline.
    """

    DEFAULT_BASE_URL = "http://localhost:5100"  # REQUIREMENTS GPU-DIRECT-04 (NOT :8003)
    DEFAULT_TIMEOUT = 120.0  # Node.js ref image timeout
    MAX_RETRIES = 5
    RATE_LIMIT_SLEEP_SEC = 1.0  # 1-second spacing between requests (Node.js ref)
    BACKOFF_CAP_SEC = 16.0  # Node.js ref Math.min(2^n, 16000ms)
    ROTATE_AFTER_STRIKES = 3  # Node.js ref rotates session after 3 consecutive 429s
    CONNECT_RETRY_SLEEP_SEC = 2.0  # Node.js ref 2s sleep on fetch() throw
    UNUSUAL_STATUS_SLEEP_SEC = 5.0  # Node.js ref 5s sleep on HTTP 45
    BACKOFF_BASE_SEC = 1.0  # 2^0 = 1s first backoff

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        transport: Optional[httpx.BaseTransport] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Construct a JimengClient.

        Args:
            base_url: Override ``KAIS_JIMENG_URL`` env / ``DEFAULT_BASE_URL``.
            session_id: Comma-separated session IDs (overrides
                ``KAIS_JIMENG_SESSION_ID`` env). Empty string allowed →
                requests are sent unauthenticated.
            timeout: Per-request httpx timeout (seconds).
            max_retries: Max attempts per ``call`` (default 5).
            transport: httpx transport — tests pass ``httpx.MockTransport``.
            sleep_fn: Sleeper callable — tests pass ``lambda s: None``.
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_JIMENG_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")

        sessions_env = (
            session_id if session_id is not None
            else os.environ.get("KAIS_JIMENG_SESSION_ID", "")
        )
        # Comma-separated rotation pool. Filter empties so trailing commas
        # don't pollute the index modulo.
        self._session_ids = [s.strip() for s in sessions_env.split(",") if s.strip()]
        self._session_index = 0
        self._session_id = self._session_ids[0] if self._session_ids else ""

        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self._max_retries = max_retries if max_retries is not None else self.MAX_RETRIES

        # transport=None → real network; tests inject MockTransport
        self._client = httpx.Client(timeout=self._timeout, transport=transport)
        # Tests inject a no-op sleeper so the suite doesn't really sleep.
        self._sleep: Callable[[float], None] = sleep_fn or time.sleep

        # Rate-limit strike counter (reset on success or session rotation).
        self._rate_limit_count = 0
        # Last-request monotonic timestamp — Node.js ref enforces 1s spacing.
        self._last_request_time = 0.0

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _headers(self) -> dict[str, str]:
        """Build request headers. ``Authorization`` omitted when no session."""
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self._session_id:
            h["Authorization"] = f"Bearer {self._session_id}"
        return h

    def _rotate_session(self) -> None:
        """Advance to the next session in the rotation pool (no-op if 1)."""
        if len(self._session_ids) <= 1:
            return
        self._session_index = (self._session_index + 1) % len(self._session_ids)
        self._session_id = self._session_ids[self._session_index]
        self._rate_limit_count = 0
        logger.info(
            "jimeng session rotated → index=%d/%d",
            self._session_index + 1,
            len(self._session_ids),
        )

    def _degrade(self, operation: str, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope (D-09). Logs at WARNING."""
        logger.warning("jimeng %s degraded: %s", operation, reason)
        return {
            "degraded": True,
            "client": "jimeng",
            "operation": operation,
            "reason": reason,
        }

    def _enforce_rate_spacing(self) -> None:
        """Enforce the 1-second spacing between requests (Node.js ref)."""
        if self._last_request_time > 0:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self.RATE_LIMIT_SLEEP_SEC:
                self._sleep(self.RATE_LIMIT_SLEEP_SEC - elapsed)
        self._last_request_time = time.monotonic()

    def _request_with_retry(
        self,
        method: str,
        path: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """Port of Node.js ``_requestWithRetry`` — backoff + rotation.

        Returns:
            Parsed JSON body on 2xx, or a degrade envelope on terminal failure.
        """
        url = f"{self._base_url}{path}"

        for attempt in range(self._max_retries):
            self._enforce_rate_spacing()

            try:
                response = self._client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=body,
                )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                # Node.js ref sleeps 2s and retries until last attempt.
                if attempt < self._max_retries - 1:
                    self._sleep(self.CONNECT_RETRY_SLEEP_SEC)
                    continue
                return self._degrade("request", f"{type(exc).__name__}: {exc}")

            status = response.status_code

            if status == 429:
                # Exponential backoff: 1s, 2s, 4s, 8s, 16s cap.
                wait = min(
                    self.BACKOFF_BASE_SEC * (2 ** self._rate_limit_count),
                    self.BACKOFF_CAP_SEC,
                )
                self._rate_limit_count += 1
                logger.warning(
                    "jimeng rate-limited (429), sleeping %.1fs (strike #%d)",
                    wait,
                    self._rate_limit_count,
                )
                self._sleep(wait)

                # Rotate after ROTATE_AFTER_STRIKES strikes if multiple sessions.
                if (
                    self._rate_limit_count >= self.ROTATE_AFTER_STRIKES
                    and len(self._session_ids) > 1
                ):
                    self._rotate_session()
                continue

            if status == 45:
                # Unusual jimeng status — Node.js ref sleeps 5s and retries.
                logger.warning("jimeng unusual status 45, retrying after 5s")
                self._sleep(self.UNUSUAL_STATUS_SLEEP_SEC)
                continue

            if status >= 500:
                # Server errors degrade (D-09) — caller may rotate manually.
                return self._degrade("request", f"HTTP {status}")

            if status >= 400:
                # 4xx (except 429 above) → caller bug → raise.
                text = response.text or ""
                raise JimengError(
                    f"HTTP {status}: {text[:200]}",
                    status=status,
                    url=url,
                )

            # 2xx — success. Reset the strike counter and unwrap ``data``.
            self._rate_limit_count = 0
            try:
                return response.json()
            except ValueError as exc:
                return self._degrade(
                    "request",
                    f"invalid JSON response: {exc}",
                )

        # All retries exhausted (e.g. continuous 429s).
        return self._degrade(
            "request",
            f"max_retries ({self._max_retries}) exceeded",
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def call(self, subcommand: str, payload: dict[str, Any]) -> Any:
        """Dispatch a subcommand to its endpoint and return the result.

        Args:
            subcommand: One of ``SUBCOMMAND_ENDPOINTS`` keys.
            payload: Request body fields. ``model`` defaults to the
                subcommand's default model if not provided. The caller is
                responsible for subcommand-specific fields (e.g.
                ``functionMode="omni_reference"`` for multimodal2video —
                the client is subcommand-agnostic).

        Returns:
            The ``data`` array from the JSON response on success (mirrors
            Node.js ref which returns ``json.data``), or a degrade envelope
            on terminal failure.

        Raises:
            JimengError: On unknown subcommand or HTTP 4xx.
        """
        if subcommand not in SUBCOMMAND_ENDPOINTS:
            raise JimengError(
                f"unknown subcommand: {subcommand!r} "
                f"(expected one of: {sorted(SUBCOMMAND_ENDPOINTS)})"
            )

        method, path, default_model = SUBCOMMAND_ENDPOINTS[subcommand]

        # Caller's payload wins; default model injected otherwise. Build a
        # fresh dict so the caller's payload isn't mutated.
        body: dict[str, Any] = {"model": default_model, **payload}

        result = self._request_with_retry(method, path, body)
        if isinstance(result, dict) and result.get("degraded"):
            return result
        # Node.js ref returns ``json.data`` for image/video endpoints.
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "JimengClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
