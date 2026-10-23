"""test_cli.py — tests for plugins/platform_metrics/cli.py (Phase 42 Plan 04).

DATA-04 dashboard: ``hermes formula stats`` CLI subcommand registered via the
plugin CLI hook (``ctx.register_cli_command``). These tests cover:

  - argparse tree construction (register_formula_cli)
  - dispatch (_formula_command: stats / unknown / None)
  - stats implementation (_cmd_stats: rich tables + --json mode + empty queue)

Per CLAUDE.md conventions: ``from __future__ import annotations``,
double-quoted strings, specific exceptions bound with ``as exc``,
``encoding="utf-8"`` on every ``open()``.

Parallel-safety note: Plan 42-03 ships ``queue.py`` (``read_queue``) in
parallel with this plan. These tests must pass BEFORE 42-03 lands — the
CLI uses a defensive lazy import so it degrades gracefully when
``queue.py`` is absent (the v9.0 stub scenario: no metrics collected
yet, queue files absent). When 42-03 ships, the same tests still pass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build an ArgumentParser wired with the formula subcommand tree."""
    from plugins.platform_metrics.cli import register_formula_cli

    parser = argparse.ArgumentParser(prog="hermes formula")
    register_formula_cli(parser)
    return parser


# ---------------------------------------------------------------------------
# Test 1: register_formula_cli adds the stats subparser
# ---------------------------------------------------------------------------


def test_register_formula_cli_adds_stats_subparser() -> None:
    """register_formula_cli wires a ``stats`` subcommand."""
    parser = _build_parser()
    args = parser.parse_args(["stats"])
    assert args.formula_command == "stats"


# ---------------------------------------------------------------------------
# Test 2: stats subcommand has the --json flag
# ---------------------------------------------------------------------------


def test_stats_subcommand_has_json_flag() -> None:
    """``stats --json`` parses with args.json == True."""
    parser = _build_parser()
    args = parser.parse_args(["stats", "--json"])
    assert args.json is True


# ---------------------------------------------------------------------------
# Test 3: stats default has args.json == False
# ---------------------------------------------------------------------------


def test_stats_default_no_json() -> None:
    """``stats`` alone leaves args.json == False (the default)."""
    parser = _build_parser()
    args = parser.parse_args(["stats"])
    assert args.json is False


# ---------------------------------------------------------------------------
# Test 4: _formula_command stats outputs rich tables
# ---------------------------------------------------------------------------


def test_formula_command_stats_outputs_tables(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``stats`` with no --json prints the rich table title to stdout."""
    from plugins.platform_metrics import cli as cli_mod

    # Redirect HERMES_HOME so the CLI reads from tmp_path.
    monkeypatch.setattr(
        "plugins.platform_metrics.cli.get_hermes_home",
        lambda: str(tmp_path),
    )

    args = argparse.Namespace(formula_command="stats", json=False)
    rc = cli_mod._formula_command(args)
    assert rc == 0

    captured = capsys.readouterr()
    # The Formula Library Overview table title appears in output.
    assert "Formula" in captured.out


# ---------------------------------------------------------------------------
# Test 5: stats --json emits valid JSON with no ANSI codes
# ---------------------------------------------------------------------------


def test_formula_command_stats_json_mode(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``stats --json`` emits valid counts-only JSON (no rich, no ANSI)."""
    from plugins.platform_metrics import cli as cli_mod

    monkeypatch.setattr(
        "plugins.platform_metrics.cli.get_hermes_home",
        lambda: str(tmp_path),
    )

    args = argparse.Namespace(formula_command="stats", json=True)
    rc = cli_mod._formula_command(args)
    assert rc == 0

    captured = capsys.readouterr()
    # No ANSI escape codes (rich is bypassed in JSON mode).
    assert "\x1b[" not in captured.out
    # Output parses as JSON.
    payload = json.loads(captured.out)
    assert isinstance(payload, dict)
    assert "formulas" in payload
    assert "queue" in payload
    assert isinstance(payload["formulas"], list)
    assert isinstance(payload["queue"], dict)
    # Queue sub-object has the 3 expected keys.
    for key in ("pending", "applied", "rejected"):
        assert key in payload["queue"]


# ---------------------------------------------------------------------------
# Test 6: empty queue (or missing tuning/ dir) does not crash
# ---------------------------------------------------------------------------


def test_formula_command_stats_empty_queue(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Missing tuning/ dir surfaces zero counts in both rich and JSON mode."""
    from plugins.platform_metrics import cli as cli_mod

    monkeypatch.setattr(
        "plugins.platform_metrics.cli.get_hermes_home",
        lambda: str(tmp_path),
    )

    # JSON path: all three queue counts are 0.
    args = argparse.Namespace(formula_command="stats", json=True)
    rc = cli_mod._formula_command(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["queue"] == {"pending": 0, "applied": 0, "rejected": 0}

    # Rich path: still exits 0 with the table title.
    args = argparse.Namespace(formula_command="stats", json=False)
    rc = cli_mod._formula_command(args)
    assert rc == 0
    assert "Formula" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Test 7: unknown subcommand returns a non-zero exit + helpful message
# ---------------------------------------------------------------------------


def test_formula_command_unknown_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unknown formula_command returns exit code 2 + error message."""
    from plugins.platform_metrics import cli as cli_mod

    args = argparse.Namespace(formula_command="bogus", json=False)
    rc = cli_mod._formula_command(args)
    assert rc == 2
    captured = capsys.readouterr()
    assert "bogus" in captured.out.lower() or "unknown" in captured.out.lower()


# ---------------------------------------------------------------------------
# Test 8: no subcommand prints top-level help
# ---------------------------------------------------------------------------


def test_formula_command_no_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing formula_command prints help and returns 0."""
    from plugins.platform_metrics import cli as cli_mod

    args = argparse.Namespace(formula_command=None, json=False)
    rc = cli_mod._formula_command(args)
    assert rc == 0
    captured = capsys.readouterr()
    # Help text mentions the stats subcommand.
    assert "stats" in captured.out


# ---------------------------------------------------------------------------
# Test 9 (Plan 42-04 Task 2): register(ctx) wires ctx.register_cli_command
# ---------------------------------------------------------------------------


def test_register_wires_cli_command() -> None:
    """register(ctx) calls ctx.register_cli_command with name='formula'."""
    from plugins.platform_metrics import register

    ctx = MagicMock()
    register(ctx)

    assert ctx.register_cli_command.called, (
        "register(ctx) must call ctx.register_cli_command"
    )
    call = ctx.register_cli_command.call_args
    # name positional or kwarg
    name = call.kwargs.get("name") or (
        call.args[0] if call.args else None
    )
    assert name == "formula"
    # setup_fn + handler_fn are callable
    setup_fn = call.kwargs.get("setup_fn")
    handler_fn = call.kwargs.get("handler_fn")
    assert callable(setup_fn), "setup_fn must be callable"
    assert callable(handler_fn), "handler_fn must be callable"
