"""Pytest fixtures for v11.0 schema migration tests (EVAL-07 / Phase 55 Plan 04).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - ``@pytest.mark.asyncio`` explicit on async tests (not needed here — all sync).
  - ``monkeypatch.setenv`` for HERMES_HOME redirection (never raw ``Path.home()``).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Repo root (worktree root) — resolve from this file's location.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "migrate_v6_feedback_to_memory_schema.py"
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "sample_v6_feedbackstore"


@pytest.fixture
def hermes_home_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated HERMES_HOME per test.

    Redirects ``hermes_constants.get_hermes_home()`` (which reads the HERMES_HOME
    env var) to a tmp_path so the migration script writes nothing to the real
    ``~/.hermes``. Pattern mirrors ``tests/conftest.py::hermes_home``.
    """
    hermes_home = tmp_path / "hermes_home"
    hermes_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    return hermes_home


@pytest.fixture
def sample_feedbackstore(hermes_home_tmp: Path) -> Path:
    """Copy the sample fixture FeedbackStore into ``$HERMES_HOME/skills/.feedback``.

    The migration script's default ``--source`` resolves to this path, so the
    script can be invoked with no explicit ``--source`` and will read the
    fixture. Returns the absolute source path for explicit-source invocations.
    """
    # Source FeedbackStore lives at $HERMES_HOME/skills/.feedback per
    # agent/feedback_store.py:230 (root = hermes_home / "skills" / ".feedback").
    target_root = hermes_home_tmp / "skills" / ".feedback"
    target_root.parent.mkdir(parents=True, exist_ok=True)
    # Copy the entire fixture tree (preserves buckets/<skill>/<source>.jsonl +
    # index.json).
    shutil.copytree(FIXTURE_ROOT, target_root)
    return target_root


@pytest.fixture
def mock_audit_chain(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Intercept ``curator_audit.append_audit`` calls.

    Returns a list that records each call's kwargs. Tests assert
    ``len(calls) == 0`` in dry-run mode (T-55-14 mitigation).
    """
    calls: list[dict[str, Any]] = []

    def _fake_append_audit(**kwargs: Any) -> str:
        calls.append(dict(kwargs))
        return "fake-entry-id-for-test"

    # Patch where the migration script imports it from. The script imports
    # ``from agent import curator_audit`` so we patch ``agent.curator_audit``.
    import agent.curator_audit as curator_audit_mod

    monkeypatch.setattr(curator_audit_mod, "append_audit", _fake_append_audit)
    return calls


@pytest.fixture
def run_migration(sample_feedbackstore: Path, tmp_path: Path):
    """Helper that invokes the migration script via subprocess.

    Returns a callable. Subprocess invocation matches the operator CLI pattern
    and correctly catches ``sys.exit`` / stdout buffering. The parsed JSON
    summary is returned alongside the CompletedProcess for assertion.
    """

    def _run(
        *args: str,
        expect_exit: int = 0,
        stdin_input: str | None = None,
    ) -> tuple[subprocess.CompletedProcess, dict[str, Any]]:
        cmd = [sys.executable, str(SCRIPT_PATH)] + list(args)
        # Default --out to a tmp file unless overridden by caller.
        has_out = any("--out" in a for a in args)
        out_path = tmp_path / "migration-report.json"
        if not has_out:
            cmd += ["--out", str(out_path)]
        else:
            # Extract the --out path the caller specified.
            out_idx = list(args).index("--out") + 1
            out_path = Path(args[out_idx])

        result = subprocess.run(
            cmd,
            input=stdin_input,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(REPO_ROOT),
        )
        if expect_exit is not None:
            assert result.returncode == expect_exit, (
                f"script exited {result.returncode}, expected {expect_exit}.\n"
                f"cmd: {' '.join(cmd)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        summary: dict[str, Any] = {}
        if out_path.exists():
            summary = json.loads(out_path.read_text(encoding="utf-8"))
        return result, summary

    return _run
