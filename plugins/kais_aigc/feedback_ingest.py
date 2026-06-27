"""feedback_ingest.py - FeedbackIngestClient (Phase 42, v6.0 final phase).

Phase 42 is the final phase of the v6.0 milestone. It closes the
"最速收敛闭环" (rapid-convergence closed loop) by ingesting platform
feedback metrics (completion_rate / interaction_rate / follow_rate) and
forwarding them to RecipeLibrary.update_validation (Phase 41). The
entire "smart" Wilson-CI + convergence-detection logic lives in Phase
41's RecipeLibrary - Phase 42 is deliberately small and dull:
receive -> verify -> store -> forward.

This module ships the client skeleton in plan 42-01:
  - ``__init__`` (constructor): validates required deps, reads env vars
    (D-06: at construction time, never at module import).
  - ``get_feedback(episode_id=...)``: reads raw feedback records from
    the feedback-data AssetBus JSONL slot (mirrors RecipeLibrary.
    list_recipes read pattern).
  - ``submit_feedback(body, signature)``: STUB. Full HMAC verification +
    validation pipeline lands in 42-02; HTTP server wiring lands in
    42-03. The stub returns a not_implemented envelope so callers /
    tests can pin the skeleton contract today.

Sibling modules: ``gold_team.py``, ``review_platform.py`` (V5.0) -
mirrors their constructor pattern (env-var config, sync API per D-07,
context-manager lifecycle).

DESIGN INVARIANTS:
- D-06: env vars (KAIS_FEEDBACK_PORT, KAIS_FEEDBACK_SECRET) read at
  construction time, never at module import.
- D-07: sync API (no async, no threads) - mirrors V5.0 kais_aigc
  clients.
- HTTP server deps (httpx, starlette) are deliberately NOT imported in
  this skeleton - plan 42-03 adds them when the HTTP handler lands.

STRUCTURAL 'not auto-modify pipeline' INVARIANT (FEEDBACK-INGEST-05):
This module MUST NOT import pipeline.phases.p10b_rapid_preview, runner,
or preview_engine. Verified by grep test in 42-04. The ONLY references
are: RecipeLibrary (Phase 41) + AssetBus (V5.0) + stdlib. The recipe
library is consumed by HUMANS making creative decisions, not by the
pipeline itself.
"""

from __future__ import annotations

import logging
import os
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

__all__ = ["FeedbackIngestClient"]


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

    # ── Write path stub (full impl in 42-02 + 42-03) ──────────────────

    def submit_feedback(self, body: bytes, signature: str) -> dict:
        """STUB - full implementation arrives in 42-02 (HMAC verification
        + validation pipeline) and 42-03 (HTTP handler wiring).

        Returns a documented ``not_implemented`` envelope so callers and
        tests can pin the skeleton contract today without coupling to
        implementation details that haven't landed yet.

        Args:
            body: raw request body bytes (POST /api/v1/feedback payload).
            signature: ``X-Signature`` header value (``sha256=<hex>``).

        Returns:
            Dict with keys:
              - ``status``: always ``"not_implemented"`` for the stub.
              - ``reason``: human-readable string citing 42-02 / 42-03.
        """
        return {
            "status": "not_implemented",
            "reason": (
                "Phase 42-02 (HMAC + validation) + "
                "42-03 (HTTP server) pending"
            ),
        }

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
