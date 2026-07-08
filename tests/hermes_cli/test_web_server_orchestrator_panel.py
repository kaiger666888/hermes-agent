"""Tests for GET /orchestrator dashboard panel (Phase 68 OBSRV-05).

Verifies the dashboard observability panel:
1. Returns auth-gated HTML (200 + text/html with valid auth, 401 without)
2. HTML body contains 3 dimension section markers
3. Path NOT in PUBLIC_API_PATHS (security invariant)

TDD RED phase: this file is committed BEFORE the route + template exist.
Tests fail because `/orchestrator` either 404s or falls through to the SPA
catchall (returning index.html, not our panel).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_repo = str(Path(__file__).resolve().parents[1])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


class TestOrchestratorDashboardPanel:
    """Integration tests for the /orchestrator panel via FastAPI TestClient."""

    def _auth_headers(self) -> dict[str, str]:
        """Build headers that satisfy the loopback _SESSION_TOKEN gate."""
        from hermes_cli import web_server

        return {"X-Hermes-Session-Token": web_server._SESSION_TOKEN}

    def test_orchestrator_panel_returns_html(self):
        """GET /orchestrator with valid auth returns 200 + text/html."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        app.state.auth_required = False
        try:
            client = TestClient(app)
            resp = client.get("/orchestrator", headers=self._auth_headers())
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 200, (
            f"expected 200, got {resp.status_code}: {resp.text[:200]}"
        )
        content_type = resp.headers.get("content-type", "")
        assert "text/html" in content_type, (
            f"expected text/html content-type, got {content_type}"
        )
        # Body must be HTML (start with <!DOCTYPE or <html).
        body_start = resp.text.lstrip().lower()[:50]
        assert "<!doctype html" in body_start or "<html" in body_start, (
            f"response body is not HTML; first 50 chars: {body_start!r}"
        )

    def test_orchestrator_panel_requires_auth(self):
        """GET /orchestrator WITHOUT auth returns 401 (Pitfall: panel
        surfaces agent names + lineage SHAs via the embedded fetch —
        the page itself must be operator-only)."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        app.state.auth_required = False
        try:
            client = TestClient(app)
            resp = client.get("/orchestrator")  # no auth headers
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 401, (
            f"expected 401 without auth, got {resp.status_code}: "
            f"{resp.text[:200]}"
        )

    def test_orchestrator_panel_contains_3_dimension_sections(self):
        """The panel HTML contains markers for all 3 observability
        dimensions so the JS can populate them independently."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        app.state.auth_required = False
        try:
            client = TestClient(app)
            resp = client.get("/orchestrator", headers=self._auth_headers())
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 200, resp.text[:200]
        body = resp.text
        # The 3 dimension sections must have stable element IDs so the
        # client-side JS can populate them via getElementById.
        assert 'id="agent-registry"' in body, (
            "missing element with id='agent-registry'"
        )
        assert 'id="round-table"' in body, (
            "missing element with id='round-table'"
        )
        assert 'id="memory-backend"' in body, (
            "missing element with id='memory-backend'"
        )

    def test_orchestrator_panel_not_in_public_paths(self):
        """The panel path is NOT in PUBLIC_API_PATHS — guards against
        accidentally promoting it to the unauthenticated allowlist
        (it surfaces agent names + lineage SHAs via the embedded fetch)."""
        from hermes_cli.dashboard_auth.public_paths import PUBLIC_API_PATHS

        assert "/orchestrator" not in PUBLIC_API_PATHS, (
            "/orchestrator leaked into PUBLIC_API_PATHS — this would let "
            "unauthenticated callers load the panel HTML (the data fetch is "
            "still gated, but the page structure itself is operator-only)."
        )
