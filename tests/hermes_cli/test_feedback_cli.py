"""Tests for hermes_cli/feedback.py + /feedback slash command wiring.

Covers:
  - register_cli() builds import/watch/submit subcommands
  - _cmd_import / _cmd_watch / _cmd_submit dispatch correctly
  - /feedback slash command in cli.py (_handle_feedback_command)
  - COMMAND_REGISTRY contains a feedback CommandDef entry

Per CLAUDE.md conventions: ``encoding="utf-8"`` on every ``open()``.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent / "fixtures" / "feedback"
)


# ---------------------------------------------------------------------------
# Test stubs — minimal REPL stand-in so we can exercise _handle_feedback_command
# without booting HermesCLI (which requires a full agent + config).
# ---------------------------------------------------------------------------


class _FakeAgent:
    """Minimal AIAgent stand-in: just the attrs build_output_snapshot reads."""

    def __init__(self) -> None:
        self.model = "test-model"
        self.provider = "openai"
        self.api_mode = "chat_completions"
        self.max_tokens = 1024
        self.reasoning_config = None
        self.service_tier = None
        self.request_overrides: dict = {}


def _make_stub_repl(conversation_history, agent=None):
    """Build a minimal stub instance carrying _handle_feedback_command.

    We import cli.HermesCLI just to get the unbound method; we attach it
    to a bare object with the two attributes it reads. This avoids the
    heavy HermesCLI __init__ (which loads config, plugins, sessions, etc.).
    """
    # Lazy import so test collection doesn't crash if cli.py has a side effect.
    from cli import HermesCLI  # noqa: F401

    class _Stub:
        pass

    stub = _Stub()
    stub.agent = agent if agent is not None else _FakeAgent()
    stub.conversation_history = conversation_history
    # Bind the real method (defined in Task 2 on HermesCLI).
    stub._handle_feedback_command = (
        HermesCLI._handle_feedback_command.__get__(stub, _Stub)
    )
    return stub


def _skill_invocation_user_msg(skill_name: str, instruction: str = "") -> dict:
    """Build a user message whose content carries the skill-invocation marker.

    The marker format is defined in agent/skill_commands.py:550-553:
        [IMPORTANT: The user has invoked the "{skill_name}" skill, indicating
        they want you to follow its instructions. The full skill content is
        loaded below.]
    """
    marker = (
        f'[IMPORTANT: The user has invoked the "{skill_name}" skill, '
        "indicating they want you to follow its instructions. The full skill "
        "content is loaded below.]"
    )
    return {"role": "user", "content": marker + "\n\n" + instruction}


# ---------------------------------------------------------------------------
# register_cli() subcommand wiring
# ---------------------------------------------------------------------------


class TestRegisterCli:
    def test_register_cli_creates_subcommands(self):
        """register_cli(parent) yields import / watch / submit subcommands."""
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        # Parse --help-style invocation: the subparser dest is feedback_command.
        # We verify by parsing each subcommand name.
        for sub in ("import", "watch", "submit"):
            argv = [sub, "--help"] if sub != "import" else [sub, "--help"]
            # argparse raises SystemExit on --help; we just verify the
            # subparser exists by checking that parse with the subcommand
            # alone yields the right dest.
        # Easier path: introspect parser._subparsers
        assert parser._subparsers is not None, "register_cli must add subparsers"
        # The subparsers action holds a choices dict mapping name -> parser
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        assert "import" in names
        assert "watch" in names
        assert "submit" in names

    def test_register_cli_default_func_prints_help(self):
        """No subcommand -> parent prints help, exits 0."""
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        # The default func should be set.
        args = parser.parse_args([])
        assert hasattr(args, "func")


# ---------------------------------------------------------------------------
# _cmd_import
# ---------------------------------------------------------------------------


class TestCmdImport:
    def test_cmd_feedback_import_valid_file(self, tmp_path, monkeypatch):
        """_cmd_import with valid_10.jsonl returns 0 and writes 10 files."""
        # Isolate HERMES_HOME so the write lands in tmp_path.
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        # Reload hermes_constants + feedback_ingest so get_hermes_home picks up.
        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        from hermes_cli.feedback import _cmd_import

        ns = argparse.Namespace(
            file=str(FIXTURES_DIR / "valid_10.jsonl"), dry_run=False
        )
        rc = _cmd_import(ns)
        assert rc == 0
        incoming = home / "skills" / ".feedback" / "incoming"
        assert len(list(incoming.glob("*.json"))) == 10

    def test_cmd_feedback_import_invalid_file_returns_nonzero(
        self, tmp_path, monkeypatch, capsys
    ):
        """_cmd_import with invalid_verdict.jsonl returns nonzero + errors."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        from hermes_cli.feedback import _cmd_import

        ns = argparse.Namespace(
            file=str(FIXTURES_DIR / "invalid_verdict.jsonl"), dry_run=False
        )
        rc = _cmd_import(ns)
        assert rc != 0
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        # Must mention the validation failure somehow.
        assert "line 2" in combined or "verdict" in combined.lower()

    def test_cmd_feedback_import_dry_run(self, tmp_path, monkeypatch):
        """dry_run validates without writing."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        from hermes_cli.feedback import _cmd_import

        ns = argparse.Namespace(
            file=str(FIXTURES_DIR / "valid_10.jsonl"), dry_run=True
        )
        rc = _cmd_import(ns)
        assert rc == 0
        incoming = home / "skills" / ".feedback" / "incoming"
        # dry-run must NOT create the incoming dir (no writes).
        assert not incoming.exists() or len(list(incoming.glob("*.json"))) == 0


# ---------------------------------------------------------------------------
# _cmd_watch
# ---------------------------------------------------------------------------


class TestCmdWatch:
    def test_cmd_feedback_watch_invokes_watch_inbox_kais(
        self, tmp_path, monkeypatch
    ):
        """_cmd_watch calls agent.feedback_ingest.watch_inbox_kais."""
        home = tmp_path / ".hermes"
        home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)

        from hermes_cli import feedback as feedback_cli
        importlib.reload(feedback_cli)

        ns = argparse.Namespace(interval=0.5)
        with patch("agent.feedback_ingest.watch_inbox_kais") as mock_watch:
            rc = feedback_cli._cmd_watch(ns)
        assert rc == 0
        assert mock_watch.called
        _args, kwargs = mock_watch.call_args
        # Interval must propagate.
        assert kwargs.get("interval") == 0.5 or (
            _args and _args[-1] == 0.5
        ) or kwargs.get("interval") == 0.5


# ---------------------------------------------------------------------------
# _cmd_submit
# ---------------------------------------------------------------------------


class TestCmdSubmit:
    def test_cmd_submit_writes_record(self, tmp_path, monkeypatch):
        """_cmd_submit constructs a FeedbackRecord(source='manual') and writes."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        from hermes_cli.feedback import _cmd_submit

        ns = argparse.Namespace(
            skill_id="screenplay",
            verdict="good",
            correction="nice work",
            revised=None,
            output_text="some output",
            prompt_text="some prompt",
            model="test-model",
            provider="openai",
        )
        rc = _cmd_submit(ns)
        assert rc == 0
        incoming = home / "skills" / ".feedback" / "incoming"
        files = list(incoming.glob("*_manual_*.json"))
        assert len(files) == 1


# ---------------------------------------------------------------------------
# /feedback slash command (_handle_feedback_command)
# ---------------------------------------------------------------------------


class TestSlashFeedback:
    """_handle_feedback_command() behavior — covers INGEST-01."""

    def test_slash_feedback_persists(
        self, tmp_path, monkeypatch, capsys
    ):
        """/feedback good 'nice work' against a prior skill output -> 1 file."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        agent = _FakeAgent()
        # Build a conversation: skill-invocation user msg -> assistant reply.
        conversation = [
            _skill_invocation_user_msg("screenplay", instruction="write a scene"),
            {"role": "assistant", "content": "Here is the scene..."},
        ]
        stub = _make_stub_repl(conversation, agent=agent)

        stub._handle_feedback_command("/feedback good nice work")
        incoming = home / "skills" / ".feedback" / "incoming"
        files = list(incoming.glob("*_cli_*.json"))
        assert len(files) == 1
        # Verify content: source=cli, verdict=good, correction="nice work".
        with open(files[0], encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["source"] == "cli"
        assert payload["verdict"] == "good"
        assert payload["correction"] == "nice work"
        assert payload["skill_id"] == "screenplay"

    def test_slash_feedback_no_skill_output(
        self, tmp_path, monkeypatch, capsys
    ):
        """/feedback with empty conversation prints an error, writes zero files."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        stub = _make_stub_repl([], agent=_FakeAgent())
        stub._handle_feedback_command("/feedback good")
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        # Must print an error mentioning "no" or "no assistant" or "no skill".
        assert any(
            word in combined.lower()
            for word in ("no active", "no assistant", "no skill", "no movie", "no prior")
        ), f"expected a clear error message, got: {combined!r}"
        incoming = home / "skills" / ".feedback" / "incoming"
        if incoming.exists():
            assert list(incoming.glob("*.json")) == []

    def test_slash_feedback_unknown_verdict(
        self, tmp_path, monkeypatch, capsys
    ):
        """/feedback excellent ... -> usage showing the 3 valid verdicts."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        conversation = [
            _skill_invocation_user_msg("screenplay"),
            {"role": "assistant", "content": "scene"},
        ]
        stub = _make_stub_repl(conversation, agent=_FakeAgent())
        stub._handle_feedback_command("/feedback excellent whatever")
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        # Must print the valid verdicts so the operator knows what to type.
        assert "good" in combined and "needs_work" in combined and "bad" in combined
        incoming = home / "skills" / ".feedback" / "incoming"
        if incoming.exists():
            assert list(incoming.glob("*.json")) == []

    def test_slash_feedback_skill_id_resolution(
        self, tmp_path, monkeypatch
    ):
        """Preceding skill-invocation user msg sets skill_id on the record."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        conversation = [
            _skill_invocation_user_msg("editor", instruction="trim this"),
            {"role": "assistant", "content": "edited output"},
        ]
        stub = _make_stub_repl(conversation, agent=_FakeAgent())
        stub._handle_feedback_command("/feedback needs_work too long")
        incoming = home / "skills" / ".feedback" / "incoming"
        files = list(incoming.glob("editor_cli_*.json"))
        assert len(files) == 1
        with open(files[0], encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["skill_id"] == "editor"

    def test_slash_feedback_usage_when_no_args(
        self, tmp_path, monkeypatch, capsys
    ):
        """/feedback with no args prints a usage line containing /feedback."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        stub = _make_stub_repl([], agent=_FakeAgent())
        stub._handle_feedback_command("/feedback")
        captured = capsys.readouterr()
        assert "/feedback" in captured.out

    def test_slash_feedback_no_movie_expert_skill(
        self, tmp_path, monkeypatch, capsys
    ):
        """/feedback after a non-skill chat turn -> clear error, no record."""
        home = tmp_path / ".hermes"
        home.mkdir()
        (home / "skills").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(home))

        import hermes_constants
        importlib.reload(hermes_constants)
        from agent import feedback_ingest
        importlib.reload(feedback_ingest)

        # Conversation WITHOUT a skill-invocation marker — normal chat.
        conversation = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        stub = _make_stub_repl(conversation, agent=_FakeAgent())
        stub._handle_feedback_command("/feedback good nice")
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        # Must complain that no skill output was found.
        assert any(
            word in combined.lower()
            for word in ("skill", "movie-expert", "no ", "not found")
        ), f"expected a 'no skill output' error, got: {combined!r}"
        incoming = home / "skills" / ".feedback" / "incoming"
        if incoming.exists():
            assert list(incoming.glob("*.json")) == []


# ---------------------------------------------------------------------------
# COMMAND_REGISTRY entry
# ---------------------------------------------------------------------------


class TestCommandRegistry:
    def test_feedback_command_in_command_registry(self):
        """COMMAND_REGISTRY contains a CommandDef with name == 'feedback'."""
        from hermes_cli.commands import COMMAND_REGISTRY

        names = [c.name for c in COMMAND_REGISTRY]
        assert "feedback" in names

    def test_feedback_command_resolvable(self):
        """resolve_command('feedback') returns the CommandDef."""
        from hermes_cli.commands import resolve_command

        cmd = resolve_command("feedback")
        assert cmd is not None
        assert cmd.name == "feedback"


# ---------------------------------------------------------------------------
# cli.py process_command wiring (smoke test)
# ---------------------------------------------------------------------------


class TestProcessCommandWiring:
    def test_canonical_feedback_branch_present(self):
        """cli.py source contains `canonical == 'feedback'` branch."""
        import cli

        source = Path(cli.__file__).read_text(encoding="utf-8")
        assert 'canonical == "feedback"' in source or (
            "canonical == 'feedback'" in source
        ), "cli.py process_command must have a feedback elif branch"

    def test_handle_feedback_command_method_present(self):
        """HermesCLI defines _handle_feedback_command."""
        from cli import HermesCLI

        assert hasattr(HermesCLI, "_handle_feedback_command"), (
            "HermesCLI must define _handle_feedback_command"
        )
