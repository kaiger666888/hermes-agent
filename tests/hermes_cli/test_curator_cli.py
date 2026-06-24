"""CLI smoke tests for the 5 curator subcommands added in Phase 32 Plan 02.

Covers:
  - ``hermes curator queue``: delegates to P31 ``_cmd_review_queue``.
  - ``hermes curator approve``: requires ``--yes``, delegates to P31
    ``_cmd_approve``, audit entry appended on success.
  - ``hermes curator reject``: delegates to P31 ``_cmd_reject``, audit
    entry appended on success.
  - ``hermes curator audit-log``: filter by action/since/skill;
    ``--verify`` walks the sha256 chain (OK / N breaks / empty).
  - ``hermes curator auto-apply-eligible``: CURATE-05 — default OFF,
    bundled NEVER, two-signal confidence, routes through ``_cmd_approve``
    per Architectural Constraint #1 (Option A — P31 structural invariant
    TestNonBypassableHumanInLoop passes UNCHANGED).
  - Delegation tests (monkeypatch P31 handlers to sentinels).
  - Audit-append best-effort (audit failure does NOT block approve).

Per CLAUDE.md: ``encoding="utf-8"`` on every ``open()``; argv-list only
for subprocess; lazy %-logging.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# register_cli test — existing subcommands preserved + new 5 added
# ---------------------------------------------------------------------------


class TestRegisterCliPreservesExistingSubcommands:
    """Plan 02 must ADD 5 subparsers without breaking the existing ones."""

    PRE_V6_SUBCOMMANDS = (
        "status", "run", "pause", "resume", "pin", "unpin",
        "restore", "list-archived", "archive", "prune", "backup", "rollback",
    )
    NEW_V6_SUBCOMMANDS = (
        "queue", "approve", "reject", "audit-log", "auto-apply-eligible",
    )

    def test_existing_subcommands_still_resolve(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        for existing in self.PRE_V6_SUBCOMMANDS:
            assert existing in names, (
                f"existing subcommand {existing!r} missing after Plan 02 extension"
            )

    def test_new_five_subcommands_resolve(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        for new in self.NEW_V6_SUBCOMMANDS:
            assert new in names, f"new subcommand {new!r} not registered"

    def test_queue_parses_skill_and_status(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(
            ["queue", "--skill", "screenplay", "--status", "applied"]
        )
        assert ns.skill == "screenplay"
        assert ns.status == "applied"
        assert callable(ns.func)

    def test_approve_parses_patch_id_and_yes(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(["approve", "pid_abc", "--yes"])
        assert ns.patch_id == "pid_abc"
        assert ns.yes is True

    def test_reject_parses_patch_id_and_reason(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(["reject", "pid_xyz", "bad rationale"])
        assert ns.patch_id == "pid_xyz"
        assert ns.reason == "bad rationale"

    def test_audit_log_parses_filters_and_verify(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(
            [
                "audit-log",
                "--action", "apply",
                "--since", "2026-06-01",
                "--skill", "screenplay",
                "--verify",
            ]
        )
        assert ns.action == "apply"
        assert ns.since == "2026-06-01"
        assert ns.skill == "screenplay"
        assert ns.verify is True

    def test_auto_apply_parses_dry_run(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(["auto-apply-eligible", "--dry-run"])
        assert ns.dry_run is True
        assert callable(ns.func)


# ---------------------------------------------------------------------------
# queue — delegates to P31 _cmd_review_queue
# ---------------------------------------------------------------------------


class TestQueueCmd:
    """``hermes curator queue`` delegates to P31 ``_cmd_review_queue``."""

    def test_queue_delegates_to_p31_review_queue(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        sentinel = MagicMock(return_value=0)
        monkeypatch.setattr(
            "hermes_cli.feedback._cmd_review_queue", sentinel
        )
        args = argparse.Namespace(
            skill="screenplay", status="pending",
        )
        rc = curator_cli._cmd_queue(args)
        assert rc == 0
        sentinel.assert_called_once_with(args)


# ---------------------------------------------------------------------------
# approve — delegates to P31 _cmd_approve; audit appended on success
# ---------------------------------------------------------------------------


class TestApproveCmdCurator:
    """``hermes curator approve <pid> --yes`` delegates to P31 ``_cmd_approve``."""

    def test_approve_without_yes_refuses(self, monkeypatch, tmp_path, capsys):
        """Mirrors P31 ``_cmd_approve`` --yes gate.

        _cmd_approve itself enforces --yes; the curator wrapper is a pure
        passthrough. The P31 path returns 1 without applying.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        # Simulate the P31 path: _cmd_approve refuses without --yes.
        def fake_approve(args):
            if not getattr(args, "yes", False):
                print("approval required (pass --yes to confirm)", file=sys.stderr)
                return 1
            return 0

        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", fake_approve)
        args = argparse.Namespace(patch_id="pid1", yes=False)
        rc = curator_cli._cmd_approve_curator(args)
        assert rc == 1

    def test_approve_delegates_to_p31_approve(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        sentinel = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", sentinel)
        args = argparse.Namespace(patch_id="pid1", yes=True)
        rc = curator_cli._cmd_approve_curator(args)
        assert rc == 0
        sentinel.assert_called_once_with(args)


# ---------------------------------------------------------------------------
# reject — delegates to P31 _cmd_reject; audit appended on success
# ---------------------------------------------------------------------------


class TestRejectCmdCurator:
    """``hermes curator reject <pid> <reason>`` delegates to P31 ``_cmd_reject``."""

    def test_reject_delegates_to_p31_reject(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        sentinel = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_reject", sentinel)
        args = argparse.Namespace(patch_id="pid1", reason="bad")
        rc = curator_cli._cmd_reject_curator(args)
        assert rc == 0
        sentinel.assert_called_once_with(args)

    def test_reject_failure_does_not_append_audit(self, monkeypatch, tmp_path):
        """If _cmd_reject returns non-zero, no audit append happens."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "hermes_cli.feedback._cmd_reject", MagicMock(return_value=1)
        )
        audit = MagicMock()
        monkeypatch.setattr("agent.curator_audit.append_audit", audit)
        args = argparse.Namespace(patch_id="pid1", reason="bad")
        rc = curator_cli._cmd_reject_curator(args)
        assert rc == 1
        audit.assert_not_called()


# ---------------------------------------------------------------------------
# audit-log — query and verify
# ---------------------------------------------------------------------------


class TestAuditLogCmd:
    """``hermes curator audit-log [--action X] [--since D] [--skill Y] [--verify]``."""

    def test_verify_on_empty_log_prints_ok(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        args = argparse.Namespace(verify=True, action=None, since=None, skill=None)
        rc = curator_cli._cmd_audit_log(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_verify_on_valid_chain_prints_ok(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli
        from agent import curator_audit

        # Append a few entries to build a valid chain.
        curator_audit.append_audit(
            action="propose", patch_id="p1", skill_id="screenplay",
            operator="tester",
        )
        curator_audit.append_audit(
            action="apply", patch_id="p1", skill_id="screenplay",
            operator="tester", commit_sha="abc123",
        )

        args = argparse.Namespace(verify=True, action=None, since=None, skill=None)
        rc = curator_cli._cmd_audit_log(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out
        assert "all entries verify" in out

    def test_verify_on_tampered_chain_returns_nonzero(
        self, monkeypatch, tmp_path, capsys
    ):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli
        from agent import curator_audit

        curator_audit.append_audit(
            action="propose", patch_id="p1", skill_id="s1", operator="t",
        )
        # Tamper: rewrite the log with a mutated action field.
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        first["action"] = "apply"  # mutated — breaks entry_sha256
        lines[0] = json.dumps(first, ensure_ascii=False)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        args = argparse.Namespace(verify=True, action=None, since=None, skill=None)
        rc = curator_cli._cmd_audit_log(args)
        out = capsys.readouterr().out
        assert rc == 1
        assert "break" in out.lower()

    def test_no_filter_prints_all_entries(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli
        from agent import curator_audit

        curator_audit.append_audit(
            action="propose", patch_id="p1", skill_id="s1", operator="t",
        )
        curator_audit.append_audit(
            action="apply", patch_id="p1", skill_id="s1", operator="t",
            commit_sha="abc",
        )

        args = argparse.Namespace(verify=False, action=None, since=None, skill=None)
        rc = curator_cli._cmd_audit_log(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "propose" in out
        assert "apply" in out
        assert "p1" in out

    def test_action_filter_restricts_output(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli
        from agent import curator_audit

        curator_audit.append_audit(
            action="propose", patch_id="p1", skill_id="s1", operator="t",
        )
        curator_audit.append_audit(
            action="apply", patch_id="p1", skill_id="s1", operator="t",
            commit_sha="abc",
        )

        args = argparse.Namespace(verify=False, action="apply", since=None, skill=None)
        rc = curator_cli._cmd_audit_log(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "apply" in out
        assert "propose" not in out

    def test_skill_filter_restricts_output(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli
        from agent import curator_audit

        curator_audit.append_audit(
            action="propose", patch_id="p1", skill_id="alpha", operator="t",
        )
        curator_audit.append_audit(
            action="propose", patch_id="p2", skill_id="beta", operator="t",
        )

        args = argparse.Namespace(verify=False, action=None, since=None, skill="alpha")
        rc = curator_cli._cmd_audit_log(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "p1" in out
        assert "p2" not in out


# ---------------------------------------------------------------------------
# Delegation: structural assertion that curator handlers forward to P31
# ---------------------------------------------------------------------------


class TestDelegation:
    """Curator handlers are thin wrappers around P31 handlers."""

    def test_approve_curator_forwards_args_object(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        captured = []

        def fake_approve(args):
            captured.append(args)
            return 0

        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", fake_approve)
        args = argparse.Namespace(patch_id="pid_xyz", yes=True)
        curator_cli._cmd_approve_curator(args)
        assert captured == [args]

    def test_reject_curator_forwards_args_object(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        captured = []

        def fake_reject(args):
            captured.append(args)
            return 0

        monkeypatch.setattr("hermes_cli.feedback._cmd_reject", fake_reject)
        args = argparse.Namespace(patch_id="pid_abc", reason="test reason")
        curator_cli._cmd_reject_curator(args)
        assert captured == [args]

    def test_queue_forwards_args_object(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        captured = []

        def fake_review_queue(args):
            captured.append(args)
            return 0

        monkeypatch.setattr("hermes_cli.feedback._cmd_review_queue", fake_review_queue)
        args = argparse.Namespace(skill="scene", status="pending")
        curator_cli._cmd_queue(args)
        assert captured == [args]


# ---------------------------------------------------------------------------
# Audit append is best-effort (audit failure does NOT block approve)
# ---------------------------------------------------------------------------


class TestAuditAppendBestEffort:
    """If append_audit raises, the underlying approve/reject still succeeds.

    RESEARCH A4: audit is best-effort. T-32-12 mitigation.
    """

    def test_approve_succeeds_even_if_audit_append_raises(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        # P31 _cmd_approve succeeds.
        monkeypatch.setattr(
            "hermes_cli.feedback._cmd_approve", MagicMock(return_value=0)
        )
        # Audit append fails.
        monkeypatch.setattr(
            "agent.curator_audit.append_audit",
            MagicMock(side_effect=RuntimeError("disk full")),
        )
        args = argparse.Namespace(patch_id="pid1", yes=True)
        rc = curator_cli._cmd_approve_curator(args)
        assert rc == 0  # apply succeeded; audit failure logged WARNING, not fatal

    def test_reject_succeeds_even_if_audit_append_raises(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "hermes_cli.feedback._cmd_reject", MagicMock(return_value=0)
        )
        monkeypatch.setattr(
            "agent.curator_audit.append_audit",
            MagicMock(side_effect=RuntimeError("disk full")),
        )
        args = argparse.Namespace(patch_id="pid1", reason="r")
        rc = curator_cli._cmd_reject_curator(args)
        assert rc == 0


# ---------------------------------------------------------------------------
# _get_operator — returns OS username or "unknown"
# ---------------------------------------------------------------------------


class TestGetOperator:
    def test_returns_string(self, monkeypatch):
        from hermes_cli import curator as curator_cli
        op = curator_cli._get_operator()
        assert isinstance(op, str)
        assert op  # non-empty

    def test_falls_back_to_unknown_on_failure(self, monkeypatch):
        from hermes_cli import curator as curator_cli

        # getpass is imported at module top-level; patch the bound function.
        def raise_runtime(*a, **kw):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr("getpass.getuser", raise_runtime)
        op = curator_cli._get_operator()
        assert op == "unknown"


# ---------------------------------------------------------------------------
# CURATE-05 auto-apply path (Task 2)
# ---------------------------------------------------------------------------


def _make_patch(
    *,
    patch_id: str = "pid_auto",
    skill_id: str = "agent_skill_1",
    auto_apply_eligible: bool = True,
    mean_delta: float = 0.15,
    evidence_count: int = 4,
) -> "MagicMock":
    """Construct a fake PatchRecord-like object for auto-apply tests."""
    p = MagicMock()
    p.patch_id = patch_id
    p.skill_id = skill_id
    p.auto_apply_eligible = auto_apply_eligible
    p.confidence_score = {
        "mean_delta": mean_delta,
        "evidence_count": evidence_count,
        "reason": "both signals pass",
    }
    p.eval_gate_score = {"verdict": "pass", "mean_delta": mean_delta}
    p.feedback_chain = ["fb1", "fb2", "fb3", "fb4"]
    p.llm_rationale = "test rationale"
    p.unified_diff = "+added\n"
    p.insight_id = "insight_1"
    p.ts_queued = "2026-06-25T00:00:00+00:00"
    return p


class TestAutoApplyCmd:
    """CURATE-05 — semi-automatic apply path for agent-created skills.

    Architectural Constraint #1 Option A: routes through _cmd_approve.
    apply_patch_transaction is STILL called only from _cmd_approve, so
    P31 TestNonBypassableHumanInLoop passes UNCHANGED.
    """

    def test_auto_apply_default_off(self, monkeypatch, tmp_path, capsys):
        """When auto_apply_enabled=false, _cmd_auto_apply_eligible no-ops."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: False
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=False)
        rc = curator_cli._cmd_auto_apply_eligible(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "disabled" in out.lower()
        approve.assert_not_called()

    def test_auto_apply_refuses_bundled(
        self, monkeypatch, tmp_path, capsys
    ):
        """Bundled skill patch NEVER auto-applies even if marked eligible.

        Defense-in-depth (T-32-05): even if Plan 01 incorrectly marked a
        bundled patch auto_apply_eligible=True, this CLI gate refuses it.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        # Bundled skill — is_agent_created returns False.
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: False
        )
        # Patch marked eligible (the buggy-proposer scenario).
        bundled_patch = _make_patch(
            skill_id="screenplay", auto_apply_eligible=True,
            mean_delta=0.5, evidence_count=10,
        )
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [bundled_patch],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=False)
        rc = curator_cli._cmd_auto_apply_eligible(args)
        out = capsys.readouterr().out
        # Did NOT fire.
        approve.assert_not_called()
        assert "skipped" in out.lower() or "0" in out

    def test_auto_apply_fires_for_agent_created(
        self, monkeypatch, tmp_path, capsys
    ):
        """Agent-created skill + two-signal confidence → _cmd_approve called.

        Option A: the auto-apply handler DELEGATES to _cmd_approve — it
        does NOT call apply_patch_transaction directly. P31 structural
        invariant TestNonBypassableHumanInLoop passes unchanged.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: True
        )
        good_patch = _make_patch(
            skill_id="agent_x", auto_apply_eligible=True,
            mean_delta=0.15, evidence_count=4,
        )
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [good_patch],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)
        monkeypatch.setattr(
            "agent.curator_audit.append_audit", MagicMock()
        )

        args = argparse.Namespace(dry_run=False)
        rc = curator_cli._cmd_auto_apply_eligible(args)
        out = capsys.readouterr().out
        assert rc == 0
        approve.assert_called_once()
        # Verify it passed yes=True programmatically (operator opt-in via
        # running the command).
        called_args = approve.call_args[0][0]
        assert called_args.yes is True
        assert called_args.patch_id == "pid_auto"
        assert "auto-applied" in out.lower() or "1" in out

    def test_auto_apply_skips_low_confidence_delta(
        self, monkeypatch, tmp_path
    ):
        """mean_delta below threshold → SKIPPED even if evidence_count passes."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: True
        )
        low_delta_patch = _make_patch(
            skill_id="agent_x", auto_apply_eligible=True,
            mean_delta=0.05, evidence_count=4,  # delta fails
        )
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [low_delta_patch],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=False)
        curator_cli._cmd_auto_apply_eligible(args)
        approve.assert_not_called()

    def test_auto_apply_skips_low_confidence_evidence(
        self, monkeypatch, tmp_path
    ):
        """evidence_count below threshold → SKIPPED even if mean_delta passes."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: True
        )
        low_ev_patch = _make_patch(
            skill_id="agent_x", auto_apply_eligible=True,
            mean_delta=0.15, evidence_count=2,  # evidence fails
        )
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [low_ev_patch],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=False)
        curator_cli._cmd_auto_apply_eligible(args)
        approve.assert_not_called()

    def test_auto_apply_skips_not_marked_eligible(
        self, monkeypatch, tmp_path
    ):
        """auto_apply_eligible=False → SKIPPED regardless of confidence."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: True
        )
        unmarked_patch = _make_patch(
            skill_id="agent_x", auto_apply_eligible=False,
            mean_delta=0.5, evidence_count=10,
        )
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [unmarked_patch],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=False)
        curator_cli._cmd_auto_apply_eligible(args)
        approve.assert_not_called()

    def test_dry_run_lists_without_applying(
        self, monkeypatch, tmp_path, capsys
    ):
        """--dry-run prints eligible patches without calling _cmd_approve."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: True
        )
        good_patch = _make_patch(
            skill_id="agent_x", auto_apply_eligible=True,
            mean_delta=0.15, evidence_count=4,
        )
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [good_patch],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=True)
        rc = curator_cli._cmd_auto_apply_eligible(args)
        out = capsys.readouterr().out
        assert rc == 0
        approve.assert_not_called()
        assert "pid_auto" in out

    def test_two_signal_required_both_pass_simultaneously(
        self, monkeypatch, tmp_path
    ):
        """Both signals must pass at the same time — either failing skips."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_cli import curator as curator_cli

        monkeypatch.setattr(
            "agent.curator.get_auto_apply_enabled", lambda: True
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_delta", lambda: 0.1
        )
        monkeypatch.setattr(
            "agent.curator.get_auto_apply_min_evidence", lambda: 3
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_agent_created", lambda name: True
        )
        # delta passes, evidence fails
        p1 = _make_patch(mean_delta=0.15, evidence_count=2)
        # delta fails, evidence passes
        p2 = _make_patch(mean_delta=0.05, evidence_count=5)
        monkeypatch.setattr(
            "agent.evolution.read_queue",
            lambda **kw: [p1, p2],
        )
        approve = MagicMock(return_value=0)
        monkeypatch.setattr("hermes_cli.feedback._cmd_approve", approve)

        args = argparse.Namespace(dry_run=False)
        curator_cli._cmd_auto_apply_eligible(args)
        approve.assert_not_called()


# ---------------------------------------------------------------------------
# Structural invariant preservation (Task 2 gate)
# ---------------------------------------------------------------------------


class TestStructuralInvariantPreserved:
    """Option A preserves the P31 TestNonBypassableHumanInLoop invariant.

    The actual P31 ast-walk test is the source of truth — this class
    verifies the Plan 02-specific guarantees via grep counts so a regression
    is caught here too.
    """

    def test_curator_cli_has_zero_apply_patch_transaction_calls(self):
        """curator.py CLI handler DELEGATES — never calls apply directly.

        Option A: ``_cmd_auto_apply_eligible`` routes through
        ``_cmd_approve``; ``apply_patch_transaction`` count in
        hermes_cli/curator.py MUST be 0.
        """
        repo_root = Path(__file__).resolve().parent.parent.parent
        curator_cli_path = repo_root / "hermes_cli" / "curator.py"
        source = curator_cli_path.read_text(encoding="utf-8")
        # Count actual Call nodes (not docstrings/comments).
        import ast as _ast
        tree = _ast.parse(source)
        count = 0

        class _Walker(_ast.NodeVisitor):
            def visit_Call(self, node: _ast.Call) -> None:
                nonlocal count
                func = node.func
                name = None
                if isinstance(func, _ast.Name):
                    name = func.id
                elif isinstance(func, _ast.Attribute):
                    name = func.attr
                if name == "apply_patch_transaction":
                    count += 1
                self.generic_visit(node)

        _Walker().visit(tree)
        assert count == 0, (
            f"hermes_cli/curator.py has {count} apply_patch_transaction "
            f"Call node(s) — must be 0 (Option A: delegate to _cmd_approve)"
        )
