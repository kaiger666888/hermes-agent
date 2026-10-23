"""feedback_client.py — Asset Feedback API client for pipeline integration.

Lets pipeline phases, review gates, and AI reviewers submit feedback to the
kais-aigc-platform ``kv_assetFeedback`` table via HTTP. Mirrors the style of
``canvas.py`` and ``gold_team.py``: sync ``httpx.Client``, ``KAIS_CANVAS_URL``
env var fallback, degrade-tolerant contract.

Endpoints covered (all under /api/v1/feedback on the canvas platform):
  - POST /                           → create
  - POST /batch                      → batch_create
  - GET  /:assetId                   → get_feedback
  - GET  /stats/:assetId             → get_stats
  - GET  /propagation/:assetId       → get_propagation
  - PATCH /:id                       → update_status

Degrade policy:
  - Connect / timeout / 5xx → return ``{"degraded": True, ...}``, never raise.
  - 4xx → raise ``FeedbackClientError`` (caller bug — bad params / 404).
  - Successful responses unwrapped from the ``{code, msg, data}`` envelope.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class FeedbackClientError(Exception):
    """Raised for 4xx client errors against the feedback API.

    Connect errors, timeouts, and 5xx do NOT raise — they return the
    degrade envelope instead. Mirrors ``CanvasClientError`` /
    ``GoldTeamError``.
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

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        if self.status is not None and self.url is not None:
            return f"{self.message} (status={self.status}, url={self.url})"
        return self.message


class FeedbackClient:
    """Sync httpx client for the Asset Feedback API.

    Usage::

        client = FeedbackClient(base_url="http://localhost:10588")
        client.create(asset_id="a-p04-xiaoju", project_id=9999,
                      score=0.8, verdict="approve", source="pipeline_self",
                      reviewer="character_designer")
        stats = client.get_stats("a-p04-xiaoju")
        propagation = client.get_propagation("a-p04-xiaoju")
    """

    # v4.0 PIPE-INTEGRITY-01: HTTP only, never touch DB layer directly.
    DEFAULT_BASE_URL = "http://127.0.0.1:10588"
    DEFAULT_TIMEOUT = 15.0
    API_PREFIX = "/api/v1/feedback"

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        """Construct a client.

        Args:
            base_url: Canvas platform base URL. Falls back to the
                ``KAIS_CANVAS_URL`` env var, then ``DEFAULT_BASE_URL``.
            timeout: Per-request HTTP timeout in seconds.
            transport: ``httpx.BaseTransport`` for test injection
                (MockTransport). ``None`` uses real networking.
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_CANVAS_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self._client = httpx.Client(timeout=self._timeout, transport=transport)

    # ─── internal helpers ───────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _degrade(self, operation: str, reason: str) -> dict[str, Any]:
        logger.warning("feedback %s degraded: %s", operation, reason)
        return {
            "degraded": True,
            "client": "feedback",
            "operation": operation,
            "reason": reason,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = None,
        operation: str = "request",
    ) -> Any:
        """Central HTTP wrapper enforcing degrade / raise contract.

        - Connect/timeout/5xx → degrade envelope.
        - 4xx → raise ``FeedbackClientError``.
        - 2xx → parsed JSON, unwrapping ``{code, msg, data}`` if present.
        """
        url = f"{self._base_url}{self.API_PREFIX}{path}"
        try:
            response = self._client.request(
                method,
                url,
                headers=self._headers(),
                json=body if body is not None else None,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            return self._degrade(operation, f"{type(exc).__name__}: {exc}")
        except httpx.HTTPError as exc:
            return self._degrade(operation, f"{type(exc).__name__}: {exc}")

        status = response.status_code
        if status >= 500 or status == 429:
            return self._degrade(operation, f"HTTP {status}")
        if status >= 400:
            text = response.text or ""
            raise FeedbackClientError(
                f"HTTP {status}: {text[:200]}",
                status=status,
                url=url,
            )

        raw = response.text
        if not raw.strip():
            return None
        try:
            parsed = response.json()
        except ValueError:
            return raw

        # Unwrap aigc-platform envelope {code, msg, data}.
        if (
            isinstance(parsed, dict)
            and "data" in parsed
            and "code" in parsed
        ):
            return parsed["data"]
        return parsed

    # ─── public API ─────────────────────────────────────

    def create(
        self,
        *,
        asset_id: str,
        project_id: int,
        score: Optional[float] = None,
        verdict: Optional[str] = None,
        content: str = "",
        tags: Optional[list[str]] = None,
        source: str = "pipeline_self",
        reviewer: str = "pipeline",
        context: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Create a single feedback entry (POST /).

        Returns the created feedback dict (the API echoes back id + fields).
        On network/5xx failure returns the degrade envelope — callers that
        must never block should call ``create_degraded`` instead.
        """
        body: dict[str, Any] = {
            "assetId": asset_id,
            "projectId": project_id,
            "source": source,
            "reviewer": reviewer,
        }
        if score is not None:
            body["score"] = score
        if verdict is not None:
            body["verdict"] = verdict
        if content:
            body["content"] = content
        if tags is not None:
            body["tags"] = tags
        if context is not None:
            body["context"] = context
        return self._request("POST", "/", body=body, operation="create")

    def create_degraded(self, **kwargs: Any) -> dict:
        """Same as ``create`` but never raises — returns degrade envelope.

        Use this from degrade-tolerant callers (gate hooks, async sync
        paths) where a feedback write failure must not bubble up.
        """
        try:
            return self.create(**kwargs)
        except FeedbackClientError as exc:
            return self._degrade("create", str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            return self._degrade("create", f"{type(exc).__name__}: {exc}")

    def batch_create(
        self,
        feedbacks: list[dict],
        *,
        source: str = "ai_reviewer",
        reviewer: Optional[str] = None,
    ) -> dict:
        """Batch create feedback (POST /batch).

        Each entry in ``feedbacks`` should have at minimum ``assetId`` and
        ``projectId``. Optional fields mirror ``create``. Returns
        ``{"created": N, "ids": [...]}`` from the server.
        """
        body: dict[str, Any] = {
            "feedbacks": feedbacks,
            "source": source,
        }
        if reviewer is not None:
            body["reviewer"] = reviewer
        return self._request(
            "POST", "/batch", body=body, operation="batch_create",
        )

    def get_feedback(self, asset_id: str) -> list[dict]:
        """Get all feedback for an asset (timeline, GET /:assetId).

        Returns the list (newest first). On degrade returns a dict envelope
        — callers should check ``isinstance(result, list)``.
        """
        result = self._request(
            "GET",
            f"/{asset_id}",
            operation="get_feedback",
        )
        if isinstance(result, list):
            return result
        return result if isinstance(result, dict) else []

    def get_stats(self, asset_id: str) -> Optional[dict]:
        """Get aggregate stats for an asset (GET /stats/:assetId)."""
        return self._request(
            "GET",
            f"/stats/{asset_id}",
            operation="get_stats",
        )

    def get_propagation(
        self,
        asset_id: str,
        *,
        project_id: Optional[int] = None,
        direction: str = "downstream",
    ) -> Optional[dict]:
        """Get topology propagation for an asset (GET /propagation/:assetId).

        ``project_id`` is required by the backend to locate the canvas graph.
        If omitted, the call will likely 400 — caller should supply it.
        """
        params = f"?direction={direction}"
        if project_id is not None:
            params += f"&projectId={project_id}"
        return self._request(
            "GET",
            f"/propagation/{asset_id}{params}",
            operation="get_propagation",
        )

    def update_status(self, feedback_id: str, status: str) -> dict:
        """Update feedback status (PATCH /:id).

        ``status`` must be one of: open, acknowledged, resolved, contested.
        """
        return self._request(
            "PATCH",
            f"/{feedback_id}",
            body={"status": status},
            operation="update_status",
        )

    # ─── lifecycle ──────────────────────────────────────

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FeedbackClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
