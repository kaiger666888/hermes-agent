"""CLI tests for ``hermes curator evolve`` (Phase 65 Plan 02 — Wave 1).

Covers CURATE-01 (CLI flag exists, default dry-run) + CURATE-02 (canary
failure aborts with exit 2 + structured BIAS_CANARY_FAILED message).

The evolve subcommand is the operator-facing surface for live curator
self-evolution. Default path is a dry-run preview; ``--live`` is the
explicit opt-in for actual memory writes, gated by a deterministic bias
canary pre-check (Plan 01 primitive). ``--skip-canary`` is the
operator-only escape hatch (audit-logged with ``canary_pass=None``).

Per CLAUDE.md: ``encoding="utf-8"`` on every ``open()``; lazy %-logging;
specific exceptions; ``print(..., file=sys.stderr)`` for error messages.
"""

from __future__ import annotations

import argparse
import re
import sys
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# register_cli — subparser + flag parsing (Task 1 behavior)
# ---------------------------------------------------------------------------


class TestEvolveCommand:
    """``hermes curator evolve [--live] [--skip-canary] [--sync]``."""

    def _build_parser(self):
        from hermes_cli.curator import register_cli
        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        return parser

    # --- Task 1: parsing ----------------------------------------------

    def test_evolve_subcommand_registered(self):
        parser = self._build_parser()
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        assert "evolve" in names, "evolve subcommand not registered"

    def test_default_is_dry_run(self):
        """Parsing ["evolve"] yields args.live=False, skip_canary=False."""
        parser = self._build_parser()
        ns = parser.parse_args(["evolve"])
        assert ns.live is False
        assert ns.skip_canary is False
        assert callable(ns.func)

    def test_live_flag_parsed(self):
        """Parsing ["evolve", "--live"] yields args.live=True."""
        parser = self._build_parser()
        ns = parser.parse_args(["evolve", "--live"])
        assert ns.live is True

    def test_skip_canary_parsed(self):
        """Parsing ["evolve", "--live", "--skip-canary"] yields skip_canary=True."""
        parser = self._build_parser()
        ns = parser.parse_args(["evolve", "--live", "--skip-canary"])
        assert ns.skip_canary is True

    def test_sync_alias(self):
        """Both --sync and --synchronous yield args.synchronous=True."""
        parser = self._build_parser()
        ns_sync = parser.parse_args(["evolve", "--sync"])
        ns_synchronous = parser.parse_args(["evolve", "--synchronous"])
        assert ns_sync.synchronous is True
        assert ns_synchronous.synchronous is True

    # --- Task 2: exit codes, canary abort path, audit logging ----------

    def test_curator_disabled_returns_1(self, monkeypatch, tmp_path):
        """When curator is disabled, _cmd_evolve mirrors _cmd_run: exit 1."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: False)
        args = argparse.Namespace(
            live=False, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 1

    def test_default_path_calls_dry_run(self, monkeypatch, tmp_path):
        """Default path (no --live) calls run_curator_review(dry_run=True)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        review = MagicMock(return_value={"auto_transitions": {}})
        monkeypatch.setattr("agent.curator.run_curator_review", review)

        args = argparse.Namespace(
            live=False, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 0
        review.assert_called_once()
        # Pitfall 2: explicit dry_run=True boolean (never None)
        assert review.call_args.kwargs["dry_run"] is True

    def test_default_path_prints_dry_run_marker(self, monkeypatch, tmp_path, capsys):
        """Default path prints a DRY-RUN marker to stdout."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={"auto_transitions": {}}),
        )
        args = argparse.Namespace(
            live=False, skip_canary=False, synchronous=False,
        )
        curator_cli._cmd_evolve(args)
        out = capsys.readouterr().out
        assert "DRY-RUN" in out or "dry-run" in out.lower()

    def test_live_aborts_on_canary_failure(self, monkeypatch, tmp_path):
        """Canary failure (<4/5) → exit 2, run_curator_review NOT called with dry_run=False."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        # Canary returns (passed=False, caught=3, failed_ids=[...])
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (False, 3, ["bad-unsupported-claim", "other"]),
        )
        review = MagicMock(return_value={"auto_transitions": {}})
        monkeypatch.setattr("agent.curator.run_curator_review", review)

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 2  # G4 locked: exit code 2 for canary failure
        # Must NOT have called the live path
        for call in review.call_args_list:
            assert call.kwargs.get("dry_run", True) is not False, (
                "run_curator_review was called with dry_run=False despite "
                "canary failure — abort path must not reach the live path"
            )

    def test_canary_failure_message_format(self, monkeypatch, tmp_path, capsys):
        """Canary failure prints exact G4 message to stderr."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (False, 3, ["bad-unsupported-claim"]),
        )
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={}),
        )
        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        err = capsys.readouterr().err
        assert rc == 2
        # G4 exact format: BIAS_CANARY_FAILED: caught N/5 (threshold: 4); ...
        pattern = r"^BIAS_CANARY_FAILED: caught 3/5 \(threshold: 4\); live tick aborted; run 'hermes curator evolve' \(no --live\) for dry-run preview$"
        # Message may have other output before; check it appears on a line.
        lines = err.strip().splitlines()
        matched = any(re.match(pattern, line.strip()) for line in lines)
        assert matched, (
            f"BIAS_CANARY_FAILED message not found in stderr with exact format.\n"
            f"stderr: {err!r}\n"
            f"expected pattern: {pattern}"
        )

    def test_live_flag_triggers_live_path(self, monkeypatch, tmp_path):
        """Canary pass → run_curator_review called with dry_run=False exactly once."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (True, 4, []),
        )
        review = MagicMock(return_value={"auto_transitions": {}})
        monkeypatch.setattr("agent.curator.run_curator_review", review)
        monkeypatch.setattr(
            "agent.curator_audit.append_audit", MagicMock()
        )

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 0
        review.assert_called_once()
        # Pitfall 2: explicit dry_run=False boolean
        assert review.call_args.kwargs["dry_run"] is False

    def test_skip_canary_bypasses_pre_check(self, monkeypatch, tmp_path):
        """--skip-canary: canary NOT called, live path proceeds, audit logs None."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        canary = MagicMock()
        monkeypatch.setattr("agent.curator.run_bias_canary_pre_check", canary)
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={"auto_transitions": {}}),
        )
        audit = MagicMock()
        monkeypatch.setattr("agent.curator_audit.append_audit", audit)

        args = argparse.Namespace(
            live=True, skip_canary=True, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 0
        # Canary was NOT called
        canary.assert_not_called()
        # Audit was called with canary_pass=None (Pitfall 5: not False!)
        audit.assert_called_once()
        assert audit.call_args.kwargs.get("canary_pass") is None, (
            "--skip-canary audit entry must have canary_pass=None "
            "(distinct from True/False per Pitfall 5)"
        )
        # tick_mode must be "live"
        assert audit.call_args.kwargs.get("tick_mode") == "live"

    def test_audit_logged_on_live_tick(self, monkeypatch, tmp_path):
        """After successful --live tick, append_audit called with tick_mode=live,
        canary_pass=True, caught_count=<actual>."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (True, 4, ["bad-unsupported-claim"]),
        )
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={"auto_transitions": {"checked": 5}}),
        )
        audit = MagicMock()
        monkeypatch.setattr("agent.curator_audit.append_audit", audit)

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 0
        audit.assert_called_once()
        kwargs = audit.call_args.kwargs
        assert kwargs.get("tick_mode") == "live"
        assert kwargs.get("canary_pass") is True
        assert kwargs.get("caught_count") == 4

    def test_audit_failure_does_not_crash_tick(self, monkeypatch, tmp_path, capsys):
        """If append_audit raises, the tick still succeeds (best-effort audit).

        RESEARCH A4 / T-65-09: audit is best-effort. A failed audit write
        must NOT mask a successful live tick.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (True, 4, []),
        )
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={"auto_transitions": {}}),
        )
        monkeypatch.setattr(
            "agent.curator_audit.append_audit",
            MagicMock(side_effect=OSError("disk full")),
        )

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        # Tick succeeded; audit failure was a warning, not fatal
        assert rc == 0

    def test_audit_chain_corruption_does_not_crash_tick(self, monkeypatch, tmp_path):
        """WR-03 (Phase 65 review): AuditChainError path regression.

        CR-02 fixed that append_audit raises AuditChainError when the audit
        log tail is corrupt (truncated final line, interrupted flush — see
        agent/curator_audit.py:79-87, :255-260). The pre-fix except clause
        only caught (OSError, ValueError); issubclass(AuditChainError,
        OSError|ValueError) is False, so a corrupted tail would crash the
        CLI AFTER the live memory writes already succeeded — the exact
        inversion of the documented best-effort guarantee.

        This is the regression test that would have caught CR-02.
        """
        from agent.curator_audit import AuditChainError

        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (True, 4, []),
        )
        # Mock run_curator_review to verify the live tick DID complete
        # (dry_run=False called) — proving the audit failure did not
        # roll back the successful tick.
        review = MagicMock(return_value={"auto_transitions": {}})
        monkeypatch.setattr("agent.curator.run_curator_review", review)
        monkeypatch.setattr(
            "agent.curator_audit.append_audit",
            MagicMock(
                side_effect=AuditChainError(
                    "audit log tail is malformed — prev_sha256 chain broken"
                ),
            ),
        )

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        # CR-02 contract: tick succeeded despite AuditChainError; CLI must
        # return 0 (not crash with traceback).
        assert rc == 0, (
            "AuditChainError from corrupted audit log tail must NOT crash "
            "_cmd_evolve — the live tick already completed and the audit "
            "append is documented best-effort. Got rc=%d" % rc
        )
        # The live tick (dry_run=False) was actually invoked — proving the
        # audit failure did not prevent the memory mutation from running.
        review.assert_called_once()
        assert review.call_args.kwargs["dry_run"] is False

    def test_audit_failure_on_skip_canary_does_not_crash(self, monkeypatch, tmp_path):
        """Same best-effort audit guarantee for the --skip-canary path."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={"auto_transitions": {}}),
        )
        monkeypatch.setattr(
            "agent.curator_audit.append_audit",
            MagicMock(side_effect=ValueError("schema")),
        )

        args = argparse.Namespace(
            live=True, skip_canary=True, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 0

    def test_canary_failure_does_not_append_audit(self, monkeypatch, tmp_path):
        """On canary failure (abort path), append_audit is NOT called.

        The canary failure is reported via exit 2 + stderr; the audit chain
        only records actual tick attempts (live success or skip-canary).
        Recording the abort would conflate "tried and failed pre-check"
        with "tick ran" in the audit trail.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (False, 3, ["bad-low-confidence"]),
        )
        audit = MagicMock()
        monkeypatch.setattr("agent.curator_audit.append_audit", audit)

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        rc = curator_cli._cmd_evolve(args)
        assert rc == 2
        audit.assert_not_called()

    def test_mutation_summary_extracted_from_result(self, monkeypatch, tmp_path):
        """mutation_summary in audit entry reflects run_curator_review result.

        Per Plan Task 2 action: extract auto_transitions counts from the
        result dict and pass as mutation_summary. Wrap in try/except for
        forward-compat (RESEARCH: mutation_summary is free-form).
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr("agent.curator.is_enabled", lambda: True)
        monkeypatch.setattr(
            "agent.curator.run_bias_canary_pre_check",
            lambda **kw: (True, 4, []),
        )
        monkeypatch.setattr(
            "agent.curator.run_curator_review",
            MagicMock(return_value={
                "auto_transitions": {
                    "checked": 10,
                    "archived": 2,
                    "marked_stale": 1,
                    "reactivated": 0,
                },
            }),
        )
        audit = MagicMock()
        monkeypatch.setattr("agent.curator_audit.append_audit", audit)

        args = argparse.Namespace(
            live=True, skip_canary=False, synchronous=False,
        )
        curator_cli._cmd_evolve(args)
        kwargs = audit.call_args.kwargs
        # mutation_summary should be a dict reflecting the auto_transitions
        ms = kwargs.get("mutation_summary")
        assert isinstance(ms, dict)
        # Some subset of these keys should be present
        assert ms.get("checked") == 10 or ms.get("archived") == 2
