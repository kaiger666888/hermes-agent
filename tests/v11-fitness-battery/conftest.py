"""Pytest fixtures for the v11.0 fitness battery test suite.

These fixtures keep the unit tests hermetic — no real GLM calls, no
leaks into the operator's ``~/.hermes``. Per CLAUDE.md anti-patterns:

- ``Path.home() / ".hermes"`` is forbidden in production code — the
  per-test HERMES_HOME redirection relies on ``get_hermes_home()``.
- ``encoding="utf-8"`` on every text-mode ``open()`` (PLW1514).
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = REPO_ROOT / "tests" / "v11-fitness-battery" / "scenarios"
FIXTURES_DIR = REPO_ROOT / "tests" / "v11-fitness-battery" / "fixtures"


@pytest.fixture
def scenarios_dir() -> Path:
    """Absolute path to the 8 frozen battery scenarios."""
    return SCENARIOS_DIR


@pytest.fixture
def fake_judge_high():
    """LLM judge stub that always returns 0.8 per criterion.

    Returns a callable matching ``agent.auxiliary_client.call_llm``'s
    return shape: object with ``.choices[0].message.content`` JSON.
    """

    def _judge(**kwargs):
        content = json.dumps(
            {
                "scores": [
                    {"criterion": "stub", "score": 0.8, "reason": "fake_judge_high"},
                ],
                "overall": 0.8,
            }
        )
        msg = types.SimpleNamespace(content=content)
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    return _judge


@pytest.fixture
def hermes_home_tmp(tmp_path, monkeypatch) -> Path:
    """Redirect HERMES_HOME to a per-test tmp dir.

    Uses ``monkeypatch.setenv`` so any code reading the env var (via
    ``hermes_constants.get_hermes_home``) lands inside the sandbox.
    """
    home = tmp_path / "hermes-home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home


@pytest.fixture
def screenplay_stub_output():
    """A high-quality screenplay Step 3 output for stub-driven scoring tests."""
    return FIXTURES_DIR / "expected_outputs.py"
