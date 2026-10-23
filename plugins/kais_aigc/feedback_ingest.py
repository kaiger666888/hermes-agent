"""feedback_ingest.py - FeedbackIngestClient (Phase 42, v6.0 final phase).

Phase 42 is the final phase of the v6.0 milestone. It closes the
"最速收敛闭环" (rapid-convergence closed loop) by ingesting platform
feedback metrics (completion_rate / interaction_rate / follow_rate) and
forwarding them to RecipeLibrary.update_validation (Phase 41). The
entire "smart" Wilson-CI + convergence-detection logic lives in Phase
41's RecipeLibrary - Phase 42 is deliberately small and dull:
receive -> verify -> store -> forward.

Plan 42-01 shipped the client skeleton (__init__, get_feedback,
submit_feedback stub). Plan 42-02 implemented:
  - HMAC-SHA256 signature verification helper (``_verify_signature``)
    using ``hmac.compare_digest`` (constant-time). Phase 42 ALWAYS
    requires a secret — NO dev-mode escape (deliberate divergence from
    V5.0 review_platform which accepts all callbacks when secret unset).
  - Schema + semantic validators (``_validate_schema``,
    ``_validate_semantic``).
  - Full ``submit_feedback`` implementation with the 4-stage validation
    pipeline (LOCKED in CONTEXT.md):
        1. Signature (401)  — HMAC BEFORE json.loads (DoS mitigation)
        2. Schema (422)     — json.loads + required fields
        3. Semantic (400)   — metrics in [0,1], platform in valid set
        4. Episode (404)    — recipe_library.get_recipe_by_episode lookup
    Each rejection logs to the ``feedback-rejected`` JSONL slot with
    ``{feedback_id, reason, payload_snippet, timestamp}``. RecipeLibrary
    is NEVER touched on any rejection (structural invariant — only after
    all 4 stages pass).
  - Continuous-rate Wilson CI update: on accept, calls
    ``recipe_library.update_validation(..., use_continuous_rate=True)``
    so completion_rate is passed as a float to ``_wilson_ci``
    (passed += cr, total += 1.0 per feedback).

Plan 42-03 (this module version) adds the HTTP server:
  - ``list_pending_updates``: operator-side "pending review queue" reader.
  - ``_build_starlette_app``: pure ASGI factory wiring POST /api/v1/feedback
    to ``submit_feedback``.
  - ``start_feedback_server``: context manager that runs uvicorn in a
    daemon thread (test/in-process use) and shuts it down on exit
    (``server.should_exit = True`` + ``thread.join``).
  - ``__main__`` CLI block for production ``python -m
    plugins.kais_aigc.feedback_ingest`` invocation.

Sibling modules: ``gold_team.py``, ``review_platform.py`` (V5.0) -
mirrors their constructor pattern (env-var config, sync API per D-07,
context-manager lifecycle).

DESIGN INVARIANTS:
- D-06: env vars (KAIS_FEEDBACK_PORT, KAIS_FEEDBACK_SECRET) read at
  construction time, never at module import.
- D-07: sync API for the validation pipeline (no async, no threads) -
  mirrors V5.0 kais_aigc clients. The Starlette route handler is async
  (ASGI contract) but delegates to the sync ``submit_feedback``; the
  daemon thread that hosts uvicorn is the ONLY thread used.
- HTTP server deps (starlette, uvicorn) are V5.0-blessed deps and are
  imported lazily inside ``_build_starlette_app`` /
  ``start_feedback_server`` / ``__main__`` so importing this module for
  the validation-only path (42-01 / 42-02 callers) does NOT pull them
  in. httpx is imported by tests + ``__main__`` only.
- HMAC verification happens BEFORE JSON parsing - deliberate DoS
  mitigation (reject invalid signatures without burning CPU on
  potentially-malicious JSON).
- ``hmac.compare_digest`` for constant-time compare (NEVER ``==``).
- Rejection logs store only first 200 chars of body (``payload_snippet``)
  to avoid leaking full payloads (threat T-42-06).

STRUCTURAL 'not auto-modify pipeline' INVARIANT (FEEDBACK-INGEST-05):
This module MUST NOT pull in any pipeline-runner module — specifically
the rapid-preview phase, the DAG runner, or the preview engine. Verified
by a grep test in plan 42-04 (Test 13) which asserts 0 matches for the
forbidden import patterns. The ONLY references this module makes are:
RecipeLibrary (Phase 41) + AssetBus (V5.0) + stdlib. The recipe library
is consumed by HUMANS making creative decisions, not by the pipeline
itself.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ─── Constants ─────────────────────────────────────────────────────────

# CONTEXT.md decision: KAIS_FEEDBACK_PORT default is 8091 - sibling to
# gold-team :8002 and review-platform :8090 (so a single host can run
# all three feedback / scheduling services without port conflicts).
DEFAULT_FEEDBACK_PORT = 8091

# AssetBus slot names (canonical - defined once here so callers don't
# repeat the string literal). Mirrors the RecipeLibrary.SLOT pattern.
SLOT_FEEDBACK_DATA = "feedback-data"
SLOT_FEEDBACK_REJECTED = "feedback-rejected"

# Phase 42-02 validation-pipeline constants (LOCKED in CONTEXT.md).
TIMESTAMP_TOLERANCE_SEC = 300  # 5-minute window (replay protection).
VALID_PLATFORMS = frozenset({"douyin", "bilibili", "youtube"})
REQUIRED_FIELDS = ("episode_id", "platform", "metrics", "measured_at")
REQUIRED_METRICS = ("completion_rate", "interaction_rate", "follow_rate")

__all__ = [
    "FeedbackIngestClient",
    "FeedbackValidationError",
    "_verify_signature",
    "_validate_schema",
    "_validate_semantic",
    "_build_starlette_app",
    "start_feedback_server",
]


# ─── Helpers ──────────────────────────────────────────────────────────


def _now_iso() -> str:
    """UTC now as ISO 8601 string (tz-aware).

    Local redefinition (mirrors recipe_library._now_iso) — avoids a
    private-symbol cross-module import.
    """
    return datetime.now(timezone.utc).isoformat()


class FeedbackValidationError(Exception):
    """Raised by ``_validate_schema`` / ``_validate_semantic`` helpers.

    Carries a stable ``reason`` string (one of ``"schema"``,
    ``"semantic"``) and the matching HTTP status code so callers can
    build a uniform rejection envelope without re-deriving the mapping.
    """

    def __init__(self, reason: str, message: str, http_status: int) -> None:
        super().__init__(f"{reason}: {message}")
        self.reason = reason
        self.http_status = http_status


def _verify_signature(body: bytes, signature: str, secret: str | None) -> bool:
    """HMAC-SHA256 verification with ``sha256=`` prefix requirement.

    Phase 42 ALWAYS requires a secret — NO dev-mode escape (deliberate
    divergence from V5.0 ``review_platform.verify_callback`` which
    accepts all callbacks when the secret is unset). Phase 42 is a
    production-facing endpoint; an unset secret is a misconfiguration
    that must reject rather than silently accept.

    Args:
        body: Raw request body bytes (HMAC is computed over bytes, not
            decoded text — caller responsibility).
        signature: ``X-Signature`` header value. Must start with
            ``sha256=``.
        secret: HMAC secret. ``None`` or empty string -> reject.

    Returns:
        ``True`` if the signature matches; ``False`` otherwise. NEVER
        raises (callers branch on the bool).
    """
    if not secret:
        logger.warning(
            "feedback_ingest: secret not configured — rejecting "
            "(NO dev-mode escape; production endpoint requires KAIS_FEEDBACK_SECRET)"
        )
        return False
    if not isinstance(signature, str) or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256,
    ).hexdigest()
    # Constant-time compare (threat T-42-03 mitigation).
    return hmac.compare_digest(expected, signature)


def _validate_schema(body: bytes) -> dict:
    """Parse JSON body + validate required fields.

    Args:
        body: Raw request body bytes (already past HMAC verification).

    Returns:
        Parsed payload dict on success.

    Raises:
        FeedbackValidationError: ``reason="schema"``, ``http_status=422``
            on malformed JSON, non-object payload, missing required
            field, or malformed metrics block.
    """
    try:
        payload = json.loads(body)
    except (ValueError, TypeError) as e:
        raise FeedbackValidationError("schema", f"malformed JSON: {e}", 422)
    if not isinstance(payload, dict):
        raise FeedbackValidationError("schema", "payload must be JSON object", 422)
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise FeedbackValidationError("schema", f"missing field: {field}", 422)
    metrics = payload.get("metrics", {})
    if not isinstance(metrics, dict):
        raise FeedbackValidationError("schema", "metrics must be object", 422)
    for m in REQUIRED_METRICS:
        if m not in metrics:
            raise FeedbackValidationError("schema", f"missing metric: {m}", 422)
    return payload


def _validate_semantic(payload: dict) -> None:
    """Validate platform enum + metrics ranges.

    Args:
        payload: Parsed payload dict (already past schema validation).

    Raises:
        FeedbackValidationError: ``reason="semantic"``,
            ``http_status=400`` on unknown platform, non-numeric metric,
            or metric value outside ``[0, 1]``.
    """
    platform = payload.get("platform")
    if platform not in VALID_PLATFORMS:
        raise FeedbackValidationError(
            "semantic", f"unknown platform: {platform!r}", 400,
        )
    metrics = payload["metrics"]
    for m in REQUIRED_METRICS:
        v = metrics[m]
        # bool is a subclass of int — explicitly reject it so True/False
        # don't silently pass the numeric range check.
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise FeedbackValidationError(
                "semantic", f"{m} must be number, got {type(v).__name__}", 400,
            )
        if not (0.0 <= float(v) <= 1.0):
            raise FeedbackValidationError(
                "semantic", f"{m} out of [0,1]: {v}", 400,
            )


# ─── FeedbackIngestClient ─────────────────────────────────────────────


class FeedbackIngestClient:
    """Receive + persist + forward platform feedback.

    Constructed with a RecipeLibrary (Phase 41) + AssetBus (V5.0). The
    client reads raw feedback records from the ``feedback-data`` JSONL
    slot; rejected submissions are written to ``feedback-rejected`` (the
    append happens in 42-02 - the skeleton here only ships the read path
    + the stub).

    Plan 42-01 scope: skeleton + ``get_feedback``. Plan 42-02 adds HMAC
    verification + validation pipeline. Plan 42-03 adds the HTTP server.

    Environment:
    - ``KAIS_FEEDBACK_PORT``: TCP port the HTTP server binds to in 42-03
      (default 8091 per CONTEXT.md).
    - ``KAIS_FEEDBACK_SECRET``: HMAC secret for inbound signature
      verification (default None - dev mode, signature checks skipped
      or always-pass depending on 42-02 impl).
    """

    DEFAULT_FEEDBACK_PORT = DEFAULT_FEEDBACK_PORT  # class-level alias

    def __init__(
        self,
        *,
        asset_bus: Any,
        recipe_library: Any,  # Phase 41 RecipeLibrary - duck-typed (avoid hard import -> cycle)
        port: int | None = None,
        secret: str | None = None,
    ) -> None:
        """Construct the client.

        Args:
            asset_bus: AssetBus instance (V5.0). Required.
            recipe_library: RecipeLibrary instance (Phase 41). Required -
                Phase 42-02 calls ``update_validation`` on this object.
                Duck-typed to avoid a hard import (prevents potential
                cycle if RecipeLibrary ever imports this module).
            port: TCP port for the HTTP server (42-03). Falls back to
                ``KAIS_FEEDBACK_PORT`` env then ``DEFAULT_FEEDBACK_PORT``
                (8091).
            secret: HMAC secret for inbound signature verification
                (42-02). Falls back to ``KAIS_FEEDBACK_SECRET`` env then
                None (dev mode).

        Raises:
            ValueError: if ``asset_bus`` or ``recipe_library`` is None.
        """
        if asset_bus is None:
            raise ValueError("FeedbackIngestClient: asset_bus required")
        if recipe_library is None:
            raise ValueError("FeedbackIngestClient: recipe_library required")

        self._bus = asset_bus
        self._rl = recipe_library
        # D-06: env-var resolution at construction time.
        self._port = (
            port
            if port is not None
            else int(os.environ.get("KAIS_FEEDBACK_PORT", str(self.DEFAULT_FEEDBACK_PORT)))
        )
        self._secret = (
            secret
            if secret is not None
            else os.environ.get("KAIS_FEEDBACK_SECRET")
        )
        # NOTE: no httpx client yet - 42-03 adds the server. close() is
        # currently a no-op so __exit__ works today.

    # ── Read path (shipped in 42-01) ──────────────────────────────────

    def get_feedback(self, *, episode_id: str | None = None) -> list[dict]:
        """Read raw feedback records from the ``feedback-data`` slot.

        Args:
            episode_id: if provided, filter to records whose
                ``episode_id`` field matches. If None (default), return
                all records.

        Returns:
            List of feedback record dicts in insertion order. Returns
            [] if the slot is empty (no file yet).
        """
        rows = self._bus.read_lines(SLOT_FEEDBACK_DATA)
        if episode_id is not None:
            rows = [r for r in rows if r.get("episode_id") == episode_id]
        return rows

    def list_pending_updates(self, *, limit: int = 10) -> list[dict]:
        """Return the most-recent N ``feedback-data`` records (newest first).

        This is the operator-facing "pending review queue" — a human can
        poll it to inspect recently-ingested platform feedback without
        running a full SQL query against the JSONL slot. Sorting is by
        ``received_at`` descending (ISO 8601 sorts lexicographically for
        a fixed format, which ``_now_iso`` guarantees).

        Args:
            limit: Maximum number of records to return. Must be an int
                >= 1. Default 10.

        Returns:
            List of at most ``limit`` feedback record dicts, newest
            first. Returns ``[]`` when the slot is empty.

        Raises:
            ValueError: if ``limit`` is not an int or is < 1.
        """
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError(f"limit must be int >= 1, got {limit!r}")
        rows = self._bus.read_lines(SLOT_FEEDBACK_DATA)
        rows_sorted = sorted(
            rows, key=lambda r: r.get("received_at", ""), reverse=True,
        )
        return rows_sorted[:limit]

    # ── Write path (full impl landed in 42-02) ────────────────────────

    def submit_feedback(self, body: bytes, signature: str) -> dict:
        """Full validation pipeline (4 stages, strict order) + RecipeLibrary update.

        Pipeline order (LOCKED in CONTEXT.md):
            1. **Signature (401)** — HMAC-SHA256 via ``hmac.compare_digest``
               BEFORE ``json.loads`` (DoS mitigation — reject invalid
               signatures without burning CPU on potentially-malicious
               JSON). Threat T-42-07 mitigation.
            2. **Schema (422)** — ``json.loads`` succeeds + required fields
               present (``episode_id``, ``platform``, ``metrics``,
               ``measured_at``).
            3. **Semantic (400)** — ``platform`` in ``{douyin, bilibili,
               youtube}``; each metric in ``[0, 1]``.
            4. **Episode existence (404)** — ``recipe_library.
               get_recipe_by_episode(episode_id)`` returns a recipe.

        Each failure logs to the ``feedback-rejected`` JSONL slot with
        ``{feedback_id, reason, payload_snippet, timestamp}`` (snippet
        truncated to 200 chars — threat T-42-06 mitigation).

        Structural invariant (WARNING #2 in plan 42-02):
            ``self._rl.update_validation`` is NEVER called on signature /
            schema / semantic failures — only after stage 4 passes. The
            only ``self._rl`` touch on rejection paths is the
            ``get_recipe_by_episode`` lookup at stage 4 (read-only).

        On full pass:
            - Appends the accepted record to ``feedback-data`` JSONL.
            - Calls ``recipe_library.update_validation(recipe_id, platform,
              completion_rate, sample_size_delta=1, use_continuous_rate=True)``
              so the continuous-rate Wilson CI accumulates ``passed += cr``
              (CONTEXT.md "Wilson CI: completion_rate is continuous binomial
              rate").

        Args:
            body: Raw request body bytes.
            signature: ``X-Signature`` header value (``sha256=<hex>``).

        Returns:
            Dict envelope:
              - On accept: ``{"status": "accepted", "feedback_id": ...,
                "recipe_id": ...}``.
              - On reject: ``{"status": "rejected", "reason": <stage>,
                "http_status": <401|422|400|404>, "feedback_id": ...}``.
              - ``feedback_id`` is ``sha256(body)[:16]`` — stable across
                resubmissions of the same body (Test 18).
        """
        feedback_id = hashlib.sha256(body).hexdigest()[:16]
        ts = _now_iso()

        # Stage 1: signature (HMAC BEFORE JSON parse — DoS mitigation).
        if not _verify_signature(body, signature, self._secret):
            self._reject(feedback_id, "signature", body, ts)
            return {
                "status": "rejected",
                "reason": "signature",
                "http_status": 401,
                "feedback_id": feedback_id,
            }

        # Stage 2: schema.
        try:
            payload = _validate_schema(body)
        except FeedbackValidationError as e:
            self._reject(feedback_id, e.reason, body, ts)
            return {
                "status": "rejected",
                "reason": e.reason,
                "http_status": e.http_status,
                "feedback_id": feedback_id,
            }

        # Stage 3: semantic.
        try:
            _validate_semantic(payload)
        except FeedbackValidationError as e:
            self._reject(feedback_id, e.reason, body, ts)
            return {
                "status": "rejected",
                "reason": e.reason,
                "http_status": e.http_status,
                "feedback_id": feedback_id,
            }

        # Stage 4: episode existence (404 if no recipe for episode_id).
        # This is the ONLY self._rl touch on the rejection path — and it
        # is a read-only lookup (get_recipe_by_episode). update_validation
        # is NEVER called on rejection (verified by Test 17/17b).
        recipe = self._rl.get_recipe_by_episode(payload["episode_id"])
        if recipe is None:
            self._reject(feedback_id, "episode_not_found", body, ts)
            return {
                "status": "rejected",
                "reason": "episode_not_found",
                "http_status": 404,
                "feedback_id": feedback_id,
            }

        # All 4 stages passed — persist + trigger RecipeLibrary update.
        record = {
            "feedback_id": feedback_id,
            "episode_id": payload["episode_id"],
            "platform": payload["platform"],
            "metrics": payload["metrics"],
            "measured_at": payload["measured_at"],
            "received_at": ts,
            "signature_valid": True,
            "recipe_id": recipe["recipe_id"],
        }
        try:
            self._bus.append_line(SLOT_FEEDBACK_DATA, record)
        except Exception as e:
            # Persistence failure: log and surface as a 500-shape reject.
            # RecipeLibrary is NOT updated (we couldn't persist the audit
            # trail — threat T-42-05 repudiation mitigation).
            logger.error(
                "feedback_ingest: feedback-data append failed for %s: %s",
                feedback_id, e,
            )
            self._reject(feedback_id, "internal_persist_error", body, ts)
            return {
                "status": "rejected",
                "reason": "internal_persist_error",
                "http_status": 500,
                "feedback_id": feedback_id,
            }

        # Continuous-rate Wilson CI update (CONTEXT.md "Wilson CI continuous
        # binomial rate"). Passed += completion_rate, total += 1.0.
        try:
            self._rl.update_validation(
                recipe["recipe_id"],
                payload["platform"],
                payload["metrics"]["completion_rate"],
                sample_size_delta=1,
                use_continuous_rate=True,
            )
        except Exception as e:
            # RecipeLibrary update failed AFTER we persisted the feedback
            # record. The feedback is accepted (audit trail intact) but
            # the convergence loop didn't advance. Log and continue — do
            # NOT raise (the platform ack is independent of CI math).
            logger.error(
                "feedback_ingest: recipe_library.update_validation failed "
                "for feedback %s (recipe %s): %s",
                feedback_id, recipe["recipe_id"], e,
            )

        logger.info(
            "feedback_ingest: accepted feedback %s (episode=%s, platform=%s, "
            "recipe=%s)",
            feedback_id, payload["episode_id"], payload["platform"],
            recipe["recipe_id"],
        )
        return {
            "status": "accepted",
            "feedback_id": feedback_id,
            "recipe_id": recipe["recipe_id"],
        }

    def _reject(
        self,
        feedback_id: str,
        reason: str,
        body: bytes,
        ts: str,
    ) -> None:
        """Write a rejection record to the ``feedback-rejected`` JSONL slot.

        NEVER raises — rejection logging is best-effort. If the bus append
        fails, we log an error and move on (the caller has already built
        the rejection envelope to return to the caller).

        Threat T-42-06 mitigation: stores only the first 200 chars of the
        body as ``payload_snippet`` (truncated, UTF-8 with replace) so the
        rejection log does not become a full-body exfiltration vector.
        """
        snippet = body.decode("utf-8", errors="replace")[:200]
        try:
            self._bus.append_line(SLOT_FEEDBACK_REJECTED, {
                "feedback_id": feedback_id,
                "reason": reason,
                "payload_snippet": snippet,
                "timestamp": ts,
            })
        except Exception as e:
            logger.error(
                "feedback_ingest: failed to log rejection %s (%s): %s",
                feedback_id, reason, e,
            )

    # ── Lifecycle ────────────────────────────────────────────────────

    def close(self) -> None:
        """Release any resources held by the client.

        Currently a no-op - the skeleton has no httpx client, no open
        files, no threads. Plan 42-03 will add httpx client teardown
        here when the HTTP server lands. Defined today so the context-
        manager protocol works for callers that wrap construction in a
        ``with`` block.
        """
        # No resources yet - 42-03 may add httpx client close.
        pass

    def __enter__(self) -> "FeedbackIngestClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ─── HTTP server wiring (plan 42-03) ──────────────────────────────────
#
# The Starlette + uvicorn imports live INSIDE the functions so that
# callers using only the validation pipeline (42-01 / 42-02 paths) do
# not pay the import cost or require the optional ASGI deps at module
# import time. Both are V5.0-blessed deps — this is a laziness
# optimization, not a soft-dependency escape.


def _build_starlette_app(client: "FeedbackIngestClient"):
    """Construct the Starlette ASGI app with ``POST /api/v1/feedback``.

    Pure factory: builds the route table and returns the Starlette
    application WITHOUT starting a server. Used by
    ``start_feedback_server`` (real uvicorn) and by tests via
    ``starlette.testclient.TestClient`` (in-process ASGI driving — no
    socket bound).

    The route handler:
      1. Reads the raw body bytes via ``await request.body()``.
      2. Reads the ``X-Signature`` header (empty string if missing).
      3. Delegates to the SYNC ``client.submit_feedback(body, signature)``
         — handler is async but the validation client is sync per D-07.
      4. Strips the internal ``http_status`` key from the response body
         (it is a transport concern, not part of the API contract) and
         uses it to set the HTTP status code on the JSONResponse.

    Args:
        client: A constructed ``FeedbackIngestClient`` whose
            ``submit_feedback`` will be called on every inbound request.

    Returns:
        ``starlette.applications.Starlette`` instance with one route.
    """
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    async def feedback_handler(request: Request) -> JSONResponse:
        body = await request.body()
        signature = request.headers.get("X-Signature", "")
        # Delegate to sync submit_feedback (handler is async but client
        # is sync per D-07). No thread offload needed — the work is CPU-
        # bound HMAC + JSON validation, sub-millisecond at typical load.
        result = client.submit_feedback(body, signature)
        http_status = result.get("http_status", 200)
        # ``http_status`` is internal — strip from the JSON envelope so
        # the public API is {status, feedback_id, ...} only (threat
        # T-42-13 mitigation: response body carries no internal state).
        response_body = {k: v for k, v in result.items() if k != "http_status"}
        return JSONResponse(response_body, status_code=http_status)

    return Starlette(routes=[
        Route("/api/v1/feedback", feedback_handler, methods=["POST"]),
    ])


@contextlib.contextmanager
def start_feedback_server(
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    secret: str | None = None,
    recipe_library: Any,
    asset_bus: Any,
):
    """Context manager: start a uvicorn server in a daemon thread.

    Yields a ``types.SimpleNamespace`` handle with attributes:
      - ``client``: the constructed ``FeedbackIngestClient``.
      - ``base_url``: ``f"http://{host}:{effective_port}"``.
      - ``server``: the underlying ``uvicorn.Server`` (exposed for
        advanced test cases that need to inspect server state).

    On exit: signals ``server.should_exit = True`` and joins the thread
    (timeout 5s) so the port is released deterministically. The daemon
    flag means the thread will not block process exit even if the join
    times out — but the join should succeed for any healthy uvicorn.

    Port resolution mirrors ``FeedbackIngestClient.__init__`` D-06:
    explicit ``port`` arg wins, else ``KAIS_FEEDBACK_PORT`` env, else
    ``DEFAULT_FEEDBACK_PORT`` (8091).

    Args:
        host: Bind address. Default ``127.0.0.1`` (loopback only —
            test-safe). Production callers set ``0.0.0.0`` explicitly.
        port: TCP port. ``None`` -> env / default resolution.
        secret: HMAC secret. ``None`` -> ``KAIS_FEEDBACK_SECRET`` env.
        recipe_library: Phase 41 RecipeLibrary (duck-typed).
        asset_bus: V5.0 AssetBus.

    Yields:
        The server handle namespace (see above).

    Example:
        with start_feedback_server(
            port=18091, secret="...",
            recipe_library=rl, asset_bus=bus,
        ) as srv:
            httpx.post(srv.base_url + "/api/v1/feedback", ...)
    """
    import threading
    import time
    import types as _types_mod

    import uvicorn

    effective_port = (
        port if port is not None
        else int(os.environ.get("KAIS_FEEDBACK_PORT", str(DEFAULT_FEEDBACK_PORT)))
    )
    effective_secret = (
        secret if secret is not None
        else os.environ.get("KAIS_FEEDBACK_SECRET")
    )

    client = FeedbackIngestClient(
        asset_bus=asset_bus,
        recipe_library=recipe_library,
        port=effective_port,
        secret=effective_secret,
    )
    app = _build_starlette_app(client)
    # worker=1 implicit (single Server instance, no --workers flag).
    # log_level="warning" keeps the test output quiet; operators
    # overriding via ``__main__`` get INFO-level logging instead.
    config = uvicorn.Config(
        app, host=host, port=effective_port, log_level="warning",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for uvicorn to signal startup (it sets ``server.started``).
    # Poll for up to 5 seconds; if uvicorn fails to bind we will see it
    # as the loop exiting without ``started`` flipping — caller will
    # then hit ECONNREFUSED on the first request and the test fails
    # loudly rather than hanging.
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)

    handle = _types_mod.SimpleNamespace(
        client=client,
        base_url=f"http://{host}:{effective_port}",
        server=server,
    )
    try:
        yield handle
    finally:
        # Graceful shutdown: ask uvicorn to exit, then join the worker
        # thread so the port is released before the context body
        # returns. SIGTERM-equivalent for in-process uvicorn.
        server.should_exit = True
        thread.join(timeout=5.0)


# ─── Production CLI (``python -m plugins.kais_aigc.feedback_ingest``) ──


def _run_cli() -> None:
    """``__main__`` entry point: wire real deps and serve forever.

    Constructs AssetBus + RecipeLibrary from ``KAIS_WORKDIR`` (default
    current directory), builds the Starlette app, and runs uvicorn
    directly on the calling thread (BLOCKING ``serve_forever`` per
    CONTEXT.md LOCKED decision). SIGINT / SIGTERM triggers uvicorn's
    built-in graceful shutdown handler — no extra signal wiring needed.
    """
    import logging as _logging

    import uvicorn

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    workdir = os.environ.get("KAIS_WORKDIR", ".")
    # Lazy imports — only needed for the CLI path, not for library use.
    from plugins.pipeline_state.asset_bus import AssetBus
    from plugins.pipeline_state.recipe_library import RecipeLibrary

    bus = AssetBus(workdir)
    rl = RecipeLibrary(asset_bus=bus)

    # Construct the client + app directly (NOT via the context manager,
    # which spins up a daemon thread suitable for tests — production
    # wants uvicorn on the main thread so SIGINT/SIGTERM propagate).
    client = FeedbackIngestClient(
        asset_bus=bus,
        recipe_library=rl,
        port=int(os.environ.get("KAIS_FEEDBACK_PORT", str(DEFAULT_FEEDBACK_PORT))),
        secret=os.environ.get("KAIS_FEEDBACK_SECRET"),
    )
    app = _build_starlette_app(client)
    host = os.environ.get("KAIS_FEEDBACK_HOST", "0.0.0.0")
    port = client._port  # noqa: SLF001 — already env-resolved in __init__

    logger.info(
        "feedback_ingest: starting uvicorn on %s:%s (workdir=%s)",
        host, port, workdir,
    )
    # uvicorn.run blocks the main thread until SIGINT/SIGTERM. Its
    # installed signal handlers perform graceful shutdown (in-flight
    # requests complete, then the loop drains).
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    _run_cli()
