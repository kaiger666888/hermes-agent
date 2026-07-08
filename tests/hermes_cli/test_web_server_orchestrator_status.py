"""Integration tests for GET /orchestrator/agents/status (Phase 67 OBSRV-01/02/03).

Verifies the unified observability endpoint exposes all 3 sections
(agent_registry, round_table, memory_backend) to authenticated operators,
rejects unauthenticated callers with 401, is NOT in PUBLIC_API_PATHS
(Pitfall 5), and degrades gracefully when the registry loader fails.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_repo = str(Path(__file__).resolve().parents[1])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


class TestOrchestratorAgentsStatus:
    """End-to-end integration tests via the FastAPI TestClient."""

    def _auth_headers(self) -> dict[str, str]:
        """Build headers that satisfy the loopback _SESSION_TOKEN gate."""
        from hermes_cli import web_server

        return {"X-Hermes-Session-Token": web_server._SESSION_TOKEN}

    def test_status_returns_all_sections(self):
        """GET /orchestrator/agents/status with valid auth returns 200 and
        the 4 top-level keys (agent_registry, round_table, memory_backend,
        snapshot_at)."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        # Ensure loopback token mode (not OAuth gate) for the test
        app.state.auth_required = False
        try:
            client = TestClient(app)
            resp = client.get(
                "/orchestrator/agents/status",
                headers=self._auth_headers(),
            )
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "agent_registry" in body, f"missing agent_registry: {body.keys()}"
        assert "round_table" in body, f"missing round_table: {body.keys()}"
        assert "memory_backend" in body, f"missing memory_backend: {body.keys()}"
        assert "snapshot_at" in body, f"missing snapshot_at: {body.keys()}"
        # Top-level sections must be dict-shaped (except snapshot_at string)
        assert isinstance(body["agent_registry"], dict)
        assert isinstance(body["round_table"], dict)
        assert isinstance(body["memory_backend"], dict)
        assert isinstance(body["snapshot_at"], str)
        assert body["snapshot_at"]  # non-empty

    def test_agent_registry_section_shape(self):
        """The agent_registry sub-dict has the 6 OBSRV-01 fields."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        app.state.auth_required = False
        try:
            client = TestClient(app)
            resp = client.get(
                "/orchestrator/agents/status",
                headers=self._auth_headers(),
            )
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 200, resp.text
        registry_section = resp.json()["agent_registry"]
        required_keys = {
            "agents_loaded",
            "schema_validation_ok",
            "missing_experts",
            "lineage_integrity_ok",
            "agent_names",
            "snapshot_at_iso",
        }
        missing = required_keys - set(registry_section.keys())
        assert not missing, f"agent_registry missing keys: {missing}"
        # Type assertions on the OBSRV-01 contract
        assert isinstance(registry_section["agents_loaded"], int)
        assert isinstance(registry_section["schema_validation_ok"], bool)
        assert isinstance(registry_section["missing_experts"], list)
        assert isinstance(registry_section["lineage_integrity_ok"], bool)
        assert isinstance(registry_section["agent_names"], list)
        assert isinstance(registry_section["snapshot_at_iso"], str)

    def test_status_requires_auth(self):
        """GET /orchestrator/agents/status WITHOUT a valid token returns 401
        (Pitfall 5 — endpoint is operator-sensitive, never in PUBLIC_API_PATHS)."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        app.state.auth_required = False
        try:
            client = TestClient(app)
            # No auth header at all
            resp = client.get("/orchestrator/agents/status")
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 401, (
            f"expected 401 without auth, got {resp.status_code}: {resp.text}"
        )

    def test_status_not_in_public_paths(self):
        """The endpoint path is NOT in PUBLIC_API_PATHS — guards against
        accidentally promoting it to the unauthenticated allowlist (RESEARCH
        Pitfall 5 security invariant)."""
        from hermes_cli.dashboard_auth.public_paths import PUBLIC_API_PATHS

        assert "/orchestrator/agents/status" not in PUBLIC_API_PATHS, (
            "/orchestrator/agents/status leaked into PUBLIC_API_PATHS — "
            "this exposes agent names + lineage SHAs + missing-expert list "
            "to unauthenticated callers (RESEARCH Pitfall 5)."
        )

    def test_registry_failure_graceful(self):
        """When load_agent_registry_with_warnings raises (simulated), the
        endpoint returns 200 with agent_registry.schema_validation_ok == False
        — NOT a 500. V7 error handling: never crash the endpoint."""
        from fastapi.testclient import TestClient

        from hermes_cli.web_server import app

        app.state.auth_required = False
        try:
            client = TestClient(app)
            # Patch the source function the handler imports lazily.
            # Pitfall 6 (lazy import) is what makes this patch land.
            with patch(
                "agent.registry_loader.load_agent_registry_with_warnings",
                side_effect=RuntimeError("simulated registry failure"),
            ):
                resp = client.get(
                    "/orchestrator/agents/status",
                    headers=self._auth_headers(),
                )
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required

        assert resp.status_code == 200, (
            f"endpoint must NOT 500 on registry failure, got {resp.status_code}: {resp.text}"
        )
        registry_section = resp.json()["agent_registry"]
        assert registry_section["schema_validation_ok"] is False, (
            "registry failure must surface as schema_validation_ok=False"
        )
        assert registry_section["agents_loaded"] == 0
        assert registry_section["missing_experts"] == []
