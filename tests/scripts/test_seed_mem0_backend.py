"""Tests for ``scripts/seed_mem0_backend.py`` + the ``backend`` adapter
in ``plugins.memory.mem0`` (Phase 60 plan 01 Task 1).

Covers three behaviors:

1. ``plugins.memory.mem0.backend`` adapter exposes the contract that
   ``agent.memory_arbitration._get_mem0_backend`` expects:
   ``is_available()``, ``search()``, ``add()``. ``search()`` / ``add()``
   never raise — they degrade to ``[]`` / ``None`` on any exception.
2. ``scripts/seed_mem0_backend.py --dry-run`` enumerates ``count``
   records and emits ``would seed ...`` lines without touching the
   network (works without ``MEM0_API_KEY``).
3. Live mode (``--dry-run`` omitted) without ``MEM0_API_KEY`` exits 2
   with the documented stderr message.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Test 1: backend adapter contract
# ---------------------------------------------------------------------------


class TestBackendAdapterContract:
    """The module-level ``backend`` singleton must satisfy the
    ``_get_mem0_backend()`` resolver contract.
    """

    def test_backend_singleton_importable(self):
        from plugins.memory.mem0 import backend
        assert backend is not None
        assert hasattr(backend, "is_available")
        assert hasattr(backend, "search")
        assert hasattr(backend, "add")

    def test_is_available_returns_bool_without_raising(self, monkeypatch):
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        from plugins.memory.mem0 import backend
        # Without MEM0_API_KEY, is_available() must return False (no key configured).
        result = backend.is_available()
        assert isinstance(result, bool)
        assert result is False

    def test_search_returns_empty_list_on_unavailable_backend(self, monkeypatch):
        """Without MEM0_API_KEY, search() must return [] (never raise)."""
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        from plugins.memory.mem0 import backend
        hits = backend.search(query="test", agent_id="ag1", top_k=5)
        assert hits == []

    def test_add_returns_none_on_unavailable_backend(self, monkeypatch):
        """Without MEM0_API_KEY, add() must return None (never raise)."""
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        from plugins.memory.mem0 import backend
        result = backend.add(content="x", agent_id="ag1")
        assert result is None

    def test_search_swallows_provider_exception(self, monkeypatch):
        """Even if the underlying provider raises, search() returns [] —
        the adapter contract is "never raise into the benchmark loop"."""

        def _boom(self, *args, **kwargs):
            raise RuntimeError("injected provider failure")

        monkeypatch.setattr(
            "plugins.memory.mem0.Mem0MemoryProvider.handle_tool_call", _boom
        )
        # Force is_available() True so search() actually invokes the provider.
        monkeypatch.setenv("MEM0_API_KEY", "fake-key-for-test")

        from plugins.memory.mem0 import backend
        # Force re-import of config by deleting cached attr if any.
        hits = backend.search(query="x", agent_id="ag1")
        assert hits == []

    def test_add_swallows_provider_exception(self, monkeypatch):
        """Same contract for add() — returns None on provider exception."""

        def _boom(self, *args, **kwargs):
            raise RuntimeError("injected provider failure")

        monkeypatch.setattr(
            "plugins.memory.mem0.Mem0MemoryProvider.handle_tool_call", _boom
        )
        monkeypatch.setenv("MEM0_API_KEY", "fake-key-for-test")

        from plugins.memory.mem0 import backend
        result = backend.add(content="x", agent_id="ag1")
        assert result is None

    def test_search_injects_agent_id_into_hits(self, monkeypatch):
        """mem0 Platform API does not echo agent_id back; adapter must
        inject it from the request so the T-53-06 layered defense works.
        """

        # Fake the provider's handle_tool_call to return a mem0_search-shaped JSON.
        class _FakeProvider:
            def __init__(self):
                self._agent_id = "hermes"

            def initialize(self, *args, **kwargs):
                pass

            def handle_tool_call(self, tool_name, args, **kwargs):
                return json.dumps({
                    "results": [
                        {"memory": "fact one", "score": 0.9},
                        {"memory": "fact two", "score": 0.7},
                    ],
                    "count": 2,
                })

        monkeypatch.setattr(
            "plugins.memory.mem0.Mem0MemoryProvider", lambda: _FakeProvider()
        )
        monkeypatch.setenv("MEM0_API_KEY", "fake-key-for-test")

        from plugins.memory.mem0 import backend
        hits = backend.search(query="q", agent_id="screenplay", top_k=5)
        assert len(hits) == 2
        assert all(h["agent_id"] == "screenplay" for h in hits)
        assert hits[0]["memory"] == "fact one"


# ---------------------------------------------------------------------------
# Test 2: seeder script — dry-run path
# ---------------------------------------------------------------------------


class TestSeedScriptDryRun:
    """``--dry-run`` enumerates records, prints ``would seed`` per record,
    requires no MEM0_API_KEY."""

    def test_dry_run_emits_would_seed_lines(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "seed_mem0_backend.py"),
                "--dry-run",
                "--count", "100",
                "--agent-id", "smoke-test",
            ],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"dry-run failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        would_seed_lines = [
            line for line in result.stdout.splitlines()
            if line.startswith("would seed")
        ]
        assert len(would_seed_lines) == 100, (
            f"expected 100 would-seed lines, got {len(would_seed_lines)}"
        )

    def test_dry_run_emits_idempotency_key_prefix(self, tmp_path):
        """Records must be prefixed with the idempotency key."""
        result = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "seed_mem0_backend.py"),
                "--dry-run",
                "--count", "100",
                "--agent-id", "smoke-test",
                "--idempotency-key", "test-key",
            ],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
        )
        assert result.returncode == 0
        # Every would-seed line must mention the idempotency key.
        for line in result.stdout.splitlines():
            if line.startswith("would seed"):
                assert "[test-key]" in line, (
                    f"idempotency key not in content: {line}"
                )

    def test_dry_run_does_not_require_mem0_api_key(self, tmp_path, monkeypatch):
        """Dry-run must work even when MEM0_API_KEY is unset — this is
        the whole point of the mode (mirrors batch_ingest.py)."""
        # subprocess.run inherits the parent env; explicitly clear the key.
        import os
        env = os.environ.copy()
        env.pop("MEM0_API_KEY", None)
        result = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "seed_mem0_backend.py"),
                "--dry-run",
                "--count", "100",
            ],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
            env=env,
        )
        assert result.returncode == 0
        assert "would seed" in result.stdout

    def test_record_content_pattern_matches_fixture(self):
        """Content pattern must mirror seed_500_records.py for
        cross-comparable benchmark numbers."""
        from scripts.seed_mem0_backend import _build_record_content
        content = _build_record_content(
            idempotency_key="phase60-eval01-seed",
            index=42,
            count=500,
            agent_id="screenplay",
        )
        assert content == (
            "[phase60-eval01-seed] record 42/500 for agent screenplay: "
            "deterministic content #42"
        )


# ---------------------------------------------------------------------------
# Test 3: seeder script — live-mode missing-key gate
# ---------------------------------------------------------------------------


class TestSeedScriptMissingKeyGate:
    """Without ``--dry-run`` and without MEM0_API_KEY, the script must
    exit 2 with the documented stderr message."""

    def test_live_mode_without_key_exits_2(self):
        import os
        env = os.environ.copy()
        env.pop("MEM0_API_KEY", None)
        result = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "seed_mem0_backend.py"),
                "--count", "100",
            ],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=30,
            env=env,
        )
        assert result.returncode == 2, (
            f"expected exit 2, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "MEM0_API_KEY not set" in result.stderr
