"""canvas.py — CanvasClient (kais-aigc-platform infinite-canvas HTTP API v2).

Phase 32 Plan 03 — Python port of Node.js ``lib/canvas-client.js`` (HTTP subset)
and the saveGraph helper in ``lib/canvas-content-sync.js``.

Scope (CRITICAL-FINDING-08 / D-08):
  - Exposes ``save_canvas(graph)`` and ``load_canvas()`` ONLY — the two
    operations the v5.0 pipeline needs.
  - The rich Node.js node/edge/branch/variant ops (addNode, addLink,
    createBranch, patchCanvas, variant groups, etc.) are intentionally out
    of scope — orchestration (Phase 35+) builds the full FlowGraph in Python
    then calls ``save_canvas(merged_graph)``.
  - WebSocket support (``socket.io-client`` in Node.js) is NOT ported. Phase 32
    is sync HTTP only. Live canvas events return in Phase 37+ if needed.

v4.0 PIPE-INTEGRITY-01 preserved: HTTP API v2 only — NO direct DB-layer access.
The Node.js ``canvas-content-sync.js`` still *reads* via an in-process DB CLI
for the legacy path, but the v5.0 Python standardizes on HTTP for both read
and write (CANVAS-IN-HERMES-03). Single write path eliminates the double-write
race fixed in v4.0. ZERO direct DB access or shell-out calls below.

Reference contracts:
  - CRITICAL-FINDING-05: save-v2 body = ``{projectId, episodesId, graph}``,
    response wraps in ``{code, msg, data}`` (unwrapped by client).
  - D-08: HTTP-only, never raise to pipeline caller (degrade warn).
  - D-09: uniform degrade envelope ``{degraded, reason, client, operation}``.
  - D-03/D-04: sync ``httpx.Client`` + ``transport`` kwarg for MockTransport.
  - D-06: reads ``KAIS_CANVAS_URL`` env var at construction.
  - D-07: behavior parity with Node.js ref.
  - GPU-DIRECT-03, CANVAS-IN-HERMES-03.
"""
# v4.0 PIPE-INTEGRITY-01 preserved: HTTP API v2 only, no DB-layer direct access.

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class CanvasClientError(Exception):
    """Raised for 4xx client errors and caller bugs against the canvas API.

    Mirrors Node.js ``CanvasClientError``. Degrade triggers (5xx, connect
    errors, timeouts) do NOT raise — they return the degrade envelope.
    """

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        url: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status = status
        self.url = url

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        if self.status is not None and self.url is not None:
            return f"{self.message} (status={self.status}, url={self.url})"
        return self.message


# ── Task 1: total_duration_sec 数值→str 强制转换 ──────────────────────────
# canvas save-v2 的 Zod schema 要求 total_duration_sec 必须是 string；pipeline 各
# phase (p01 topic-kernel / p03 script 等) 会以 int/float 形式产出该字段，且可能
# 嵌套在 node.data 的子 dict 中 (例如 creative_constraints.total_duration_sec)。
# save_canvas() 是唯一 HTTP 出口，这里递归地把每一个 total_duration_sec 数值都
# cast 成 str，确保发往 API 的请求体里永远不会出现数值类型 (HTTP 400 根因)。
_NUMERIC_DURATION_FIELDS = ("total_duration_sec",)


def _coerce_duration_fields_to_str(obj: Any) -> Any:
    """递归地把 total_duration_sec 数值转换为 str。

    覆盖 node.data 顶层、嵌套 dict (如 creative_constraints) 以及 list 中的所有
    出现位置。在 save_canvas() 发送前原地 (in-place) 修改，作为最后一道防线。
    bool 不算数值 (isinstance(True, int) 为真，需排除)。
    """
    if isinstance(obj, dict):
        for _k, _v in list(obj.items()):
            if (
                _k in _NUMERIC_DURATION_FIELDS
                and isinstance(_v, (int, float))
                and not isinstance(_v, bool)
            ):
                obj[_k] = str(_v)
            else:
                _coerce_duration_fields_to_str(_v)
    elif isinstance(obj, list):
        for _item in obj:
            _coerce_duration_fields_to_str(_item)
    return obj


class CanvasClient:
    """Sync httpx client for the kais-aigc-platform infinite-canvas API v2.

    HTTP-only (v4.0 PIPE-INTEGRITY-01). All public methods either return the
    parsed response payload or a degrade envelope ``{degraded: True, ...}`` —
    they never raise to the pipeline caller except on caller-side bugs
    (missing context, non-dict graph, 4xx HTTP).
    """

    # Node.js ref DEFAULT_BASE_URL (lib/canvas-client.js line 34).
    DEFAULT_BASE_URL = "http://192.168.71.176:10588"
    # Node.js ref DEFAULT_TIMEOUT (lib/canvas-client.js line 39) — 15s in ms.
    DEFAULT_TIMEOUT = 15.0
    # v2 REST API prefix (Node.js ref apiPrefix).
    API_PREFIX = "/api/canvas/v2"

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        project_id: Optional[int] = None,
        episodes_id: Optional[int] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        """
        Args:
            base_url: canvas platform base URL. Falls back to ``KAIS_CANVAS_URL``
                env var, then ``DEFAULT_BASE_URL`` (D-06).
            project_id: canvas project ID. Set later via ``set_context()`` if
                unknown at construction.
            episodes_id: canvas episodes ID. Set later via ``set_context()``.
            timeout: HTTP request timeout in seconds. Defaults to 15.0.
            transport: ``httpx.BaseTransport`` for testing (MockTransport). When
                ``None``, real network transport is used (D-04).
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_CANVAS_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._project_id = project_id
        self._episodes_id = episodes_id
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        # transport=None → real network; tests inject httpx.MockTransport(handler).
        self._client = httpx.Client(timeout=self._timeout, transport=transport)

    # ─── context ───────────────────────────────────────

    def set_context(
        self,
        *,
        project_id: Optional[int] = None,
        episodes_id: Optional[int] = None,
    ) -> None:
        """Update project/episodes IDs (mirrors Node.js ``setContext``).

        Used when one client is shared across multiple pipelines.
        """
        if project_id is not None:
            self._project_id = project_id
        if episodes_id is not None:
            self._episodes_id = episodes_id

    def _require_context(self) -> None:
        """Raise if project_id / episodes_id not set (mirrors _requireContext)."""
        if self._project_id is None:
            raise CanvasClientError("projectId not set")
        if self._episodes_id is None:
            raise CanvasClientError("episodesId not set")

    # ─── http helpers ──────────────────────────────────

    def _headers(self) -> dict[str, str]:
        """Request headers. No auth — canvas is internal-network (D-06)."""
        return {"Content-Type": "application/json"}

    def _degrade(self, operation: str, reason: str) -> dict[str, Any]:
        """Uniform degrade envelope (D-09). Logs WARNING, never raises."""
        logger.warning("canvas %s degraded: %s", operation, reason)
        return {
            "degraded": True,
            "client": "canvas",
            "operation": operation,
            "reason": reason,
        }

    # ─── retry config ──────────────────────────────────
    # Network errors (ConnectError, TimeoutException, 5xx) are transient and
    # worth retrying. 4xx (CanvasClientError) are data problems — never retried.
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0  # seconds; exponential: 1s, 2s, 4s

    def _request(self, path: str, body: dict[str, Any]) -> Any:
        """POST-only wrapper for canvas v2 endpoints.

        Retry policy:
        - Connect/timeout errors → retry up to MAX_RETRIES with exponential
          backoff (1s, 2s, 4s). If all retries fail → degrade envelope.
        - HTTP 5xx → retry up to MAX_RETRIES. If all fail → degrade envelope.
        - HTTP 4xx → raise ``CanvasClientError`` immediately (NEVER retried).
        - HTTP 2xx → parsed JSON, unwrapping {code, msg, data} envelope if present.

        Returns the parsed payload (may be the degrade envelope on failure).
        """
        import time

        url = f"{self._base_url}{self.API_PREFIX}/{path}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.request(
                    "POST",
                    url,
                    json=body,
                    headers=self._headers(),
                )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "canvas request failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt + 1, self.MAX_RETRIES, exc, delay,
                    )
                    time.sleep(delay)
                    continue
                return self._degrade("request", f"{type(exc).__name__}: {exc}")
            except httpx.HTTPError as exc:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "canvas request failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt + 1, self.MAX_RETRIES, exc, delay,
                    )
                    time.sleep(delay)
                    continue
                return self._degrade("request", f"{type(exc).__name__}: {exc}")

            status = response.status_code
            if status >= 500:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "canvas request got HTTP %d (attempt %d/%d) — retrying in %.1fs",
                        status, attempt + 1, self.MAX_RETRIES, delay,
                    )
                    time.sleep(delay)
                    continue
                return self._degrade("request", f"HTTP {status}")
            if status >= 400:
                text = response.text or ""
                raise CanvasClientError(
                    f"HTTP {status}: {text[:200]}",
                    status=status,
                    url=url,
                )

            # 2xx — parse JSON. Some endpoints may return empty bodies.
            raw = response.text
            if not raw.strip():
                return None
            try:
                parsed = response.json()
            except ValueError:
                # Non-JSON 2xx — return raw text. Rare for v2 endpoints.
                return raw

            # Unwrap aigc-platform envelope {code, msg, data} (CRITICAL-FINDING-05).
            if (
                isinstance(parsed, dict)
                and "data" in parsed
                and "code" in parsed
            ):
                return parsed["data"]
            return parsed

        # All retries exhausted — unreachable (loops above return or continue),
        # but included for type safety.
        return self._degrade("request", f"retries exhausted for {url}")

    def raw_post(self, path: str, body: dict[str, Any]) -> Any:
        """POST to an arbitrary platform path (non-canvas-v2).

        ``_request`` is scoped to ``/api/canvas/v2`` (API_PREFIX). The asset
        registry lives at ``/api/v1/assets-registry`` — this helper targets it
        (and any other platform service) by full path. Degrade-tolerant: on any
        network/HTTP/business error it returns ``None`` and never raises, so
        callers (e.g. pipeline asset registration) can treat a missing registry
        as non-fatal.

        Returns the unwrapped ``data`` payload on success, else ``None``.
        """
        import time

        url = f"{self._base_url}{path}"
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.request(
                    "POST", url, json=body, headers=self._headers(),
                )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_BASE_DELAY * (2 ** attempt))
                    continue
                logger.warning("raw_post %s unreachable: %s", path, exc)
                return None
            except httpx.HTTPError as exc:
                logger.warning("raw_post %s http error: %s", path, exc)
                return None

            if response.status_code >= 500:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_BASE_DELAY * (2 ** attempt))
                    continue
                logger.warning("raw_post %s HTTP %d", path, response.status_code)
                return None
            if response.status_code >= 400:
                logger.warning(
                    "raw_post %s HTTP %d: %s",
                    path, response.status_code, (response.text or "")[:200],
                )
                return None

            try:
                parsed = response.json()
            except ValueError:
                return None
            if isinstance(parsed, dict) and "data" in parsed and "code" in parsed:
                if parsed.get("code") in (200, 201, 0):
                    return parsed.get("data")
                logger.warning("raw_post %s biz code %s: %s", path, parsed.get("code"), parsed.get("message"))
                return None
            return parsed
        return None

    # ─── public API (HTTP v2 ONLY) ─────────────────────

    def save_canvas(self, graph: dict[str, Any]) -> Any:
        """Save a FlowGraph via ``POST /api/canvas/v2/save-v2``.

        Body: ``{projectId, episodesId, graph}`` (CRITICAL-FINDING-05).
        Stamps ``graph.meta.updatedAt`` (ms epoch) before save — mirrors the
        v4.0 PIPE-INTEGRITY-01 saveGraph helper in canvas-content-sync.js.

        Returns the unwrapped response data, or a degrade envelope on
        network/5xx failure. Raises ``CanvasClientError`` on 4xx or caller bug
        (missing context, non-dict graph).
        """
        self._require_context()
        if not isinstance(graph, dict):
            raise CanvasClientError("save_canvas: graph must be a dict")

        # Stamp updatedAt (Node.js canvas-content-sync.js line 53).
        # Also ensure the full meta block is valid for save-v2 (the v2
        # Zod schema requires version, projectId, episodesId, createdAt,
        # updatedAt). sanitize_v2_graph() is the primary guarantor, but
        # save_canvas() is the last line of defense — stamp the client
        # context's IDs here so they always match.
        meta = graph.setdefault("meta", {})
        if not isinstance(meta, dict):
            meta = {}
            graph["meta"] = meta
        now_ms = int(time.time() * 1000)
        meta["updatedAt"] = now_ms
        if meta.get("version") != "2":
            meta["version"] = "2"
        if not isinstance(meta.get("projectId"), (int, float)):
            meta["projectId"] = self._project_id if self._project_id is not None else 0
        if not isinstance(meta.get("episodesId"), (int, float)):
            meta["episodesId"] = self._episodes_id if self._episodes_id is not None else 0
        if not isinstance(meta.get("createdAt"), (int, float)):
            meta["createdAt"] = now_ms

        # Task 1: canvas save-v2 Zod schema 要求 total_duration_sec 为 string。
        # pipeline 各 phase (p01/p03) 可能以 int/float 形式产出该字段，且可能嵌套
        # 在 node.data 的子 dict (如 creative_constraints) 中。save_canvas() 是唯一
        # HTTP 出口，对每个 node 递归强制 str 转换，确保 API 永远不会收到数值
        # (HTTP 400 根因)。原 M4 fix 只覆盖 node.data 顶层，这里升级为递归。
        for _node in graph.get("nodes", []):
            if isinstance(_node, dict):
                _coerce_duration_fields_to_str(_node)

        body = {
            "projectId": self._project_id,
            "episodesId": self._episodes_id,
            "graph": graph,
        }
        return self._request("save-v2", body)

    def load_canvas(self) -> Any:
        """Load a FlowGraph via ``POST /api/canvas/v2/load-v2``.

        Body: ``{projectId, episodesId}``. Returns the FlowGraph dict, ``None``
        when no graph exists yet, or a degrade envelope on failure.

        HTTP-only (D-08): never touches the DB layer directly.
        """
        self._require_context()
        body = {
            "projectId": self._project_id,
            "episodesId": self._episodes_id,
        }
        return self._request("load-v2", body)

    def save_canvas_degraded(self, graph: dict[str, Any]) -> Any:
        """Convenience wrapper matching Node.js ``saveGraph`` (content-sync.js).

        Try ``save_canvas(graph)``; on any ``CanvasClientError`` return a
        degrade envelope instead of raising. Pipeline callers that must never
        block on canvas-write failure use this. The graph is still stamped
        with ``meta.updatedAt`` before the attempt.
        """
        try:
            return self.save_canvas(graph)
        except CanvasClientError as exc:
            return self._degrade("save", str(exc))

    # ─── lifecycle ─────────────────────────────────────

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "CanvasClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
