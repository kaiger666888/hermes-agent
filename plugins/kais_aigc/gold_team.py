"""gold_team.py - GoldTeamClient (GPU task scheduler :8002).

Python port of Node.js ``lib/gold-team-client.js`` for Phase 32 of the
v5.0 milestone (Plan 32-01). Talks to the gold-team Control Node REST API
to submit, query, list, and poll GPU tasks.

v5.0 hardenings vs the Node.js reference (per CONTEXT.md):
- **CRITICAL-FINDING-01**: Default URL is ``http://192.168.71.140:8002``
  per REQUIREMENTS GPU-DIRECT-01 (authoritative). The Node.js ref uses
  ``:8900`` (older API version); v5.0 follows REQUIREMENTS.
- **CRITICAL-FINDING-02**: Outbound requests carry the ``X-API-Key``
  header whenever ``KAIS_GOLD_TEAM_API_KEY`` is set. The Node.js ref
  removed auth ("neiwang hutoff"); v5.0 re-adds it as a hardening.
- Endpoint path is ``/api/v1/tasks`` per REQUIREMENTS (Node.js ref uses
  ``/api/tasks`` without the version segment).

Design invariants (per CONTEXT.md):
- D-03: ``httpx`` only - no ``requests``, no ``aiohttp``, no ``jwt``,
  no ``tenacity``. Gold-team uses static API-key auth, not bearer tokens.
- D-04: ``transport`` constructor kwarg lets tests inject
  ``httpx.MockTransport`` for hermetic HTTP mocking.
- D-06: All configuration is read from env vars at construction time
  (never at module import).
- D-07: Sync ``httpx.Client`` (not async) - matches the sync tool-handler
  dispatch path in hermes-agent.
- D-09: Degrade-first contract. Connection errors, timeouts, 5xx, and 429
  return a degrade envelope ``{"degraded": True, ...}`` - they never raise
  to the caller. 4xx errors raise ``GoldTeamError`` (caller bug). Tests
  must cover both paths.

GPU-DIRECT-01 (17 task types) is enforced in ``tools.py`` (Plan 32-05);
this client passes ``task_type`` through as an opaque string and performs
no enum validation.

SSE real-event verification is deferred to Phase 39 (CONTEXT.md Deferred
Ideas); ``subscribe_events()`` returns a documented degrade envelope.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GoldTeamError(Exception):
    """Raised for 4xx client errors and unrecoverable GPU task failures.

    Mirrors the Node.js ``GoldTeamError`` (carries ``message``, ``status``,
    and ``url``). 5xx / timeout / connection errors are *not* raised - they
    degrade. Poll failures inside ``wait_for_task`` are also raised: by the
    time you have a ``task_id`` a poll failure is a real failure, not a
    degrade (matches the Node.js ref).
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        url: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.url = url


class GoldTeamClient:
    """Sync httpx client for the gold-team GPU task API (:8002).

    All public methods return dicts. Network / 5xx / timeout / connection
    errors degrade (return ``{"degraded": True, ...}``) per D-09 and
    GPU-DIRECT-05. 4xx errors raise ``GoldTeamError`` (caller bug).

    The client is a context manager: ``with GoldTeamClient() as c: ...``
    ensures the underlying ``httpx.Client`` is closed cleanly.
    """

    # REQUIREMENTS GPU-DIRECT-01 (CRITICAL-FINDING-01 - :8002, not :8900)
    DEFAULT_BASE_URL = "http://192.168.71.140:8002"
    DEFAULT_TIMEOUT = 60.0  # GPU tasks may be long
    DEFAULT_POLL_INTERVAL = 5.0  # matches Node.js pollIntervalMs=5000
    DEFAULT_POLL_TIMEOUT = 600.0  # 10min, matches Node.js timeoutMs=600000

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Construct a client.

        Parameters mirror CONTEXT.md D-06 env-var configuration:
        - ``base_url`` / ``KAIS_GOLD_TEAM_URL``: Control Node base URL.
        - ``api_key`` / ``KAIS_GOLD_TEAM_API_KEY``: optional X-API-Key.
        - ``timeout``: per-request timeout in seconds (GPU tasks are long).

        ``transport`` exists purely for tests: pass
        ``httpx.MockTransport(handler)`` to intercept every HTTP call.
        The default (``None``) uses real networking.
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_GOLD_TEAM_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._api_key = (
            api_key if api_key is not None
            else os.environ.get("KAIS_GOLD_TEAM_API_KEY")
        )
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        # transport=None -> real network; tests inject httpx.MockTransport
        self._client = httpx.Client(timeout=self._timeout, transport=transport)
        # Callback wiring (inbound GPU-task callbacks only). Used by
        # verify_callback() - NOT for outbound auth.
        self._callback_base_url = os.environ.get(
            "KAIS_CALLBACK_BASE_URL",
            "http://192.168.71.140:3000",
        )
        self._callback_secret = os.environ.get("KAIS_HMAC_SECRET_MA_GT", "")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        """Build outbound headers.

        Always sets ``Content-Type: application/json``. Conditionally sets
        ``X-API-Key`` when ``KAIS_GOLD_TEAM_API_KEY`` is configured
        (CRITICAL-FINDING-02).
        """
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            h["X-API-Key"] = self._api_key
        return h

    def _degrade(self, operation: str, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope (D-09) and log a warning."""
        logger.warning("gold_team %s degraded: %s", operation, reason)
        return {
            "degraded": True,
            "client": "gold_team",
            "operation": operation,
            "reason": reason,
        }

    @staticmethod
    def _unwrap(payload: Any) -> Any:
        """Extract ``data`` from the service envelope.

        The gold-team Control Node wraps responses as ``{"data": {...}}``
        (matches the Node.js ref). If a ``data`` key is present, return it
        directly; otherwise return the payload as-is (defensive against
        future service evolution).
        """
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
    ) -> Any:
        """Central HTTP wrapper enforcing the degrade / raise contract.

        Returns the parsed JSON body (still envelope-wrapped - callers use
        ``_unwrap``). Degrades on connect errors, timeouts, 5xx. Raises
        ``GoldTeamError`` on 4xx (caller bug) and on non-JSON 2xx
        responses.
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
            # D-09: degrade on connect / timeout (server-side problem).
            return self._degrade("request", f"{type(exc).__name__}: {exc}")
        except httpx.HTTPError as exc:
            # Catch-all for other httpx transport errors (also degrade).
            return self._degrade("request", f"{type(exc).__name__}: {exc}")

        status = response.status_code
        text = response.text

        if status >= 500 or status == 429:
            # D-09: degrade on server errors and rate limiting.
            return self._degrade("request", f"HTTP {status}")

        if status >= 400:
            # 4xx is a caller bug - raise, do not degrade.
            raise GoldTeamError(
                f"HTTP {status}: {text[:200]}",
                status=status,
                url=url,
            )

        # 2xx - parse JSON. Invalid JSON is a service-side bug, so raise.
        try:
            return response.json()
        except Exception:
            raise GoldTeamError(
                f"Invalid JSON response: {text[:200]}",
                status=status,
                url=url,
            )

    # ------------------------------------------------------------------
    # Public API (mirrors Node.js lib/gold-team-client.js)
    # ------------------------------------------------------------------

    def submit_task(
        self,
        *,
        task_type: str,
        params: dict,
        assets: list | None = None,
        priority: int = 5,
        description: str | None = None,
        callback_path: str | None = None,
    ) -> dict:
        """Submit a GPU task.

        Mirrors Node.js ``submitTask``. POSTs to ``/api/v1/tasks`` with the
        task_type / params / assets / priority / description / callback_url
        / callback_secret body and returns the unwrapped task dict
        (``task_id`` / ``state`` / ``created_at``).

        On degrade (5xx / timeout / connect error) returns the degrade
        envelope directly - callers should check ``result.get("degraded")``
        before indexing into ``task_id``.
        """
        callback_url = (
            f"{self._callback_base_url}{callback_path or '/callback/gpu-task'}"
        )
        body = {
            "task_type": task_type,
            "params": params,
            "assets": assets or [],
            "priority": priority,
            "description": description,
            "callback_url": callback_url,
            "callback_secret": self._callback_secret,
        }
        result = self._request("POST", "/api/v1/tasks", body)
        if isinstance(result, dict) and result.get("degraded"):
            return result
        return self._unwrap(result)

    def get_task(self, task_id: str) -> dict:
        """Query a single task by id (GET /api/v1/tasks/{id})."""
        result = self._request("GET", f"/api/v1/tasks/{task_id}")
        if isinstance(result, dict) and result.get("degraded"):
            return result
        return self._unwrap(result)

    def list_tasks(
        self,
        *,
        state: str | None = None,
        task_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Any:
        """List tasks with optional filters (GET /api/v1/tasks?...)."""
        query_parts: list[str] = [f"limit={limit}", f"offset={offset}"]
        if state is not None:
            query_parts.append(f"state={state}")
        if task_type is not None:
            query_parts.append(f"task_type={task_type}")
        query = "&".join(query_parts)
        result = self._request("GET", f"/api/v1/tasks?{query}")
        if isinstance(result, dict) and result.get("degraded"):
            return result
        return self._unwrap(result)

    def wait_for_task(
        self,
        task_id: str,
        *,
        poll_interval: float | None = None,
        timeout: float | None = None,
    ) -> dict:
        """Poll ``get_task`` until state is ``done`` or ``failed``.

        Unlike ``submit_task``, this method RAISES on failure - by the
        time you have a task_id, a poll failure is a real failure (the
        task was accepted but something went wrong). Matches the
        Node.js ``waitForTask`` semantics.

        Raises ``GoldTeamError`` on ``state == "failed"`` or on poll
        timeout.
        """
        interval = poll_interval if poll_interval is not None else self.DEFAULT_POLL_INTERVAL
        deadline = timeout if timeout is not None else self.DEFAULT_POLL_TIMEOUT
        start = time.monotonic()
        while time.monotonic() - start < deadline:
            task = self.get_task(task_id)
            if isinstance(task, dict) and task.get("degraded"):
                # Degrade mid-poll: surface as a real failure (raise).
                raise GoldTeamError(
                    f"GPU task poll degraded: {task.get('reason', 'unknown')}",
                )
            state = task.get("state") if isinstance(task, dict) else None
            if state == "done":
                return task
            if state == "failed":
                err = task.get("error", "") if isinstance(task, dict) else ""
                raise GoldTeamError(f"GPU task failed: {err}")
            time.sleep(interval)
        raise GoldTeamError(f"GPU task timeout: {task_id}")

    def submit_task_degraded(self, **kwargs: Any) -> dict:
        """Submit a task, degrading on any error.

        Convenience wrapper around ``submit_task`` that swallows
        ``GoldTeamError`` (and any other exception) and returns the
        degrade envelope instead. Matches Node.js ``submitTaskDegraded``.
        """
        try:
            return self.submit_task(**kwargs)
        except GoldTeamError as exc:
            return self._degrade("submit", str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            return self._degrade("submit", f"{type(exc).__name__}: {exc}")

    def verify_callback(self, body: bytes | str, signature: str) -> bool:
        """Verify an inbound GPU-task callback HMAC-SHA256 signature.

        Computes ``HMAC-SHA256(secret, body)`` and compares against the
        caller-supplied ``signature`` (expected format ``sha256=<hex>``)
        using ``hmac.compare_digest`` for constant-time comparison.
        Mirrors the Node.js ``verifyCallback``.
        """
        if not self._callback_secret:
            logger.warning("gold_team verify_callback: no secret configured")
            return False
        if isinstance(body, str):
            body_bytes = body.encode()
        else:
            body_bytes = body
        expected = hmac.new(
            self._callback_secret.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def ping(self, timeout_ms: int = 5000) -> bool:
        """Health check - GET ``/health`` with a short timeout.

        Returns ``True`` on HTTP 2xx, ``False`` on any error. Uses a
        throwaway ``httpx.Client`` so it does not interfere with the
        primary client's timeout setting.
        """
        try:
            with httpx.Client(timeout=timeout_ms / 1000) as probe:
                resp = probe.get(f"{self._base_url}/health")
            return resp.is_success
        except Exception:
            return False

    def subscribe_events(self) -> dict:
        """SSE event subscription stub.

        Real SSE event streaming is out of scope for Phase 32 (CONTEXT.md
        Deferred Ideas - Phase 39 will do real GPU E2E including SSE).
        Returns a documented degrade envelope so callers can wire a
        graceful "SSE not available in v5.0 backend" path today.
        """
        return self._degrade(
            "subscribe_events",
            "SSE not implemented in Phase 32 - see Phase 39 for real GPU E2E",
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "GoldTeamClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
