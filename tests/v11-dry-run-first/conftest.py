"""Shared fixtures for EVAL-06 dry-run-first invariant tests.

Provides:
  * ``hermes_home_tmp`` (autouse) — isolated tmp HERMES_HOME per test.
  * ``mock_audit_chain`` — intercepts ``agent.curator_audit.append_audit``
    and records call count + arguments. Used to assert zero audit entries
    in default mode.
  * ``mock_apply_automatic_transitions`` — intercepts
    ``agent.curator.apply_automatic_transitions`` to record call count.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def hermes_home_tmp(tmp_path, monkeypatch):
    """Isolated HERMES_HOME per test (copy pattern from v11-bias-canary).

    Prevents curator tests from leaking state into the real ``~/.hermes/``.
    """
    home = tmp_path / "hermes_home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    yield home


@pytest.fixture()
def mock_audit_chain(monkeypatch):
    """Intercept ``append_audit`` calls and record them.

    Returns a ``_CallRecorder`` instance exposing ``.call_count`` and
    ``.calls`` (list of kwargs dicts). Default behavior is a no-op so
    tests can assert "zero audit entries in default mode" without
    triggering real audit-log writes.
    """
    class _CallRecorder:
        def __init__(self) -> None:
            self.call_count: int = 0
            self.calls: list[dict[str, Any]] = []

        def __call__(self, *args: Any, **kwargs: Any) -> None:
            self.call_count += 1
            self.calls.append({"args": args, "kwargs": kwargs})

    recorder = _CallRecorder()
    # Late import so the fixture module itself has no hard dependency on
    # agent.curator_audit at collection time.
    import agent.curator_audit as curator_audit  # noqa: WPS433 (local import OK)
    monkeypatch.setattr(curator_audit, "append_audit", recorder)
    # ``agent.curator`` does ``from agent.curator_audit import append_audit``
    # at module top (line 1738 is inside _feedback_scan_phase, lazy import).
    # Patch both the source module attribute and any rebound reference.
    import agent.curator as curator  # noqa: WPS433
    monkeypatch.setattr(curator, "append_audit", recorder, raising=False)
    return recorder


@pytest.fixture()
def mock_apply_automatic_transitions(monkeypatch):
    """Intercept ``apply_automatic_transitions`` and record calls.

    Used to assert the function is NOT called in default mode (dry_run=True).
    """
    class _CallRecorder:
        def __init__(self) -> None:
            self.call_count: int = 0

        def __call__(self, *args: Any, **kwargs: Any) -> dict[str, int]:
            self.call_count += 1
            return {"checked": 0, "marked_stale": 0, "archived": 0, "reactivated": 0}

    recorder = _CallRecorder()
    import agent.curator as curator  # noqa: WPS433
    monkeypatch.setattr(curator, "apply_automatic_transitions", recorder)
    return recorder
