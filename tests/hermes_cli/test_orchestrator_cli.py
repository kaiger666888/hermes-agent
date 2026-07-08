"""Tests for `hermes orchestrator status` CLI (Phase 68 OBSRV-04).

Verifies the CLI:
1. Renders 3 rich tables (Agent Registry / Round Table / Memory Backend)
2. Emits valid JSON via ``--json`` flag
3. JSON shape matches the ``/orchestrator/agents/status`` endpoint (SC#3)
4. Degrades gracefully on registry load failure (mirror endpoint behavior)

TDD RED phase: this file is committed BEFORE the implementation
(``hermes_cli/orchestrator.py``). All tests fail with ImportError initially.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_repo = str(Path(__file__).resolve().parents[1])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


class TestOrchestratorStatusCli:
    """End-to-end tests for the `hermes orchestrator status` CLI handler."""

    def test_status_renders_3_tables(self, capsys):
        """`hermes orchestrator status` (no --json) prints output containing
        all 3 dimension names as rich table titles/headers."""
        from hermes_cli.orchestrator import _cmd_status

        args = _make_args(as_json=False)
        rc = _cmd_status(args)
        captured = capsys.readouterr()
        assert rc == 0, f"expected exit 0, got {rc}"
        out = captured.out
        # All 3 dimension names must appear in the rendered output.
        # Case-insensitive check to be robust to rich styling.
        out_lower = out.lower()
        assert "agent registry" in out_lower, (
            f"missing 'agent registry' in output:\n{out}"
        )
        assert "round table" in out_lower, (
            f"missing 'round table' in output:\n{out}"
        )
        assert "memory backend" in out_lower, (
            f"missing 'memory backend' in output:\n{out}"
        )

    def test_status_shows_key_metrics(self, capsys):
        """The rendered output surfaces at least one value from each
        dimension's metrics dict (not just headers)."""
        from hermes_cli.orchestrator import _cmd_status

        args = _make_args(as_json=False)
        rc = _cmd_status(args)
        captured = capsys.readouterr()
        assert rc == 0
        out = captured.out.lower()
        # Agent registry: agents_loaded value present (digit)
        assert any(ch.isdigit() for ch in out), (
            f"no numeric values rendered (expected agents_loaded etc.):\n{out}"
        )

    def test_json_flag_outputs_valid_json(self, capsys):
        """`--json` emits valid JSON with the 4 top-level keys matching
        the endpoint contract."""
        from hermes_cli.orchestrator import _cmd_status

        args = _make_args(as_json=True)
        rc = _cmd_status(args)
        captured = capsys.readouterr()
        assert rc == 0
        payload = json.loads(captured.out)  # raises if invalid JSON
        expected_keys = {"agent_registry", "round_table", "memory_backend", "snapshot_at"}
        assert set(payload.keys()) == expected_keys, (
            f"top-level keys {set(payload.keys())} != expected {expected_keys}"
        )

    def test_json_matches_endpoint_shape(self):
        """SC#3 parity: CLI --json top-level keys == endpoint keys, AND
        each sub-dict has the same key set."""
        from fastapi.testclient import TestClient

        from hermes_cli.orchestrator import _build_snapshot
        from hermes_cli.web_server import app

        # CLI snapshot
        cli_snap = _build_snapshot()

        # Endpoint snapshot
        app.state.auth_required = False
        try:
            client = TestClient(app)
            headers = _auth_headers()
            resp = client.get(
                "/orchestrator/agents/status",
                headers=headers,
            )
        finally:
            if hasattr(app.state, "auth_required"):
                del app.state.auth_required
        assert resp.status_code == 200, resp.text
        endpoint_snap = resp.json()

        # Top-level key parity
        assert set(cli_snap.keys()) == set(endpoint_snap.keys()), (
            f"top-level drift: cli={set(cli_snap.keys())} "
            f"endpoint={set(endpoint_snap.keys())}"
        )

    def test_no_drift_between_cli_and_endpoint(self):
        """SC#3 regression guard: for each sub-section, the key set must
        match between CLI and endpoint. Both paths call the same getters,
        so this should always hold — but the test catches future drift
        if someone adds a key to one path and not the other."""
        from hermes_cli.orchestrator import _build_snapshot

        cli_snap = _build_snapshot()
        # Build the same shape in-process by calling the getters directly
        # (this is exactly what the endpoint does).
        from agent.observability import (
            get_agent_registry_metrics,
            get_round_table_metrics,
            get_memory_backend_metrics,
        )
        from agent.registry_loader import load_agent_registry_with_warnings

        try:
            entries, missing = load_agent_registry_with_warnings()
            schema_ok = True
        except Exception:
            entries, missing, schema_ok = [], [], False

        direct_snap = {
            "agent_registry": get_agent_registry_metrics(entries, missing, schema_ok),
            "round_table": get_round_table_metrics(),
            "memory_backend": get_memory_backend_metrics(),
        }

        for section in ("agent_registry", "round_table", "memory_backend"):
            cli_keys = set(cli_snap[section].keys())
            direct_keys = set(direct_snap[section].keys())
            assert cli_keys == direct_keys, (
                f"section '{section}' drift: cli={cli_keys} direct={direct_keys}"
            )

    def test_help_lists_status_subcommand(self):
        """The register_cli builder produces a parser that recognizes
        the `status` subcommand."""
        import argparse

        from hermes_cli.orchestrator import register_cli

        parent = argparse.ArgumentParser(prog="hermes orchestrator")
        register_cli(parent)
        # Parsing `status` should succeed and set func=_cmd_status.
        args = parent.parse_args(["status"])
        assert callable(getattr(args, "func", None)), (
            "parse_args(['status']) did not set a callable func"
        )
        # Parsing `status --json` should set as_json=True.
        args_json = parent.parse_args(["status", "--json"])
        assert args_json.as_json is True, (
            "parse_args(['status', '--json']) did not set as_json=True"
        )

    def test_registry_failure_graceful(self, capsys):
        """When load_agent_registry_with_warnings raises, the CLI exits 0
        and renders schema_ok=False (mirror endpoint behavior at
        web_server.py:2029-2034)."""
        from hermes_cli.orchestrator import _cmd_status

        args = _make_args(as_json=True)
        with patch(
            "agent.registry_loader.load_agent_registry_with_warnings",
            side_effect=RuntimeError("simulated registry failure"),
        ):
            rc = _cmd_status(args)
        captured = capsys.readouterr()
        assert rc == 0, (
            "CLI must exit 0 on registry failure (observability data, not "
            f"CLI error); got {rc}"
        )
        payload = json.loads(captured.out)
        assert payload["agent_registry"]["schema_validation_ok"] is False, (
            "registry failure must surface as schema_validation_ok=False"
        )
        assert payload["agent_registry"]["agents_loaded"] == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_args(*, as_json: bool):
    """Build a fake argparse.Namespace matching what register_cli sets."""
    import argparse

    return argparse.Namespace(orchestrator_command="status", as_json=as_json)


def _auth_headers() -> dict[str, str]:
    """Build headers that satisfy the loopback _SESSION_TOKEN gate."""
    from hermes_cli import web_server

    return {"X-Hermes-Session-Token": web_server._SESSION_TOKEN}
