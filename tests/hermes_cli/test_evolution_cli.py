"""CLI smoke tests for the 6 evolution subcommands added in Phase 31 Plan 02.

Covers:
  - ``hermes feedback evolve``: --dry-run, --insights-only, full pipeline
    (mock LLM + mock gate subprocess), no-feedback path.
  - ``hermes feedback review-queue``: empty, filtered, populated.
  - ``hermes feedback show-patch``: happy path + not-found.
  - ``hermes feedback reject``: happy path + not-found.
  - ``hermes feedback approve``: requires --yes, applies + moves, ApplyError
    path, not-found.
  - ``hermes feedback rollback``: requires --yes, invalid sha, happy path
    (tmp git repo).
  - ``TestNonBypassableHumanInLoop``: structural invariant — only
    ``_cmd_approve`` calls ``apply_patch_transaction``.
  - ``TestRegisterCliPreservesExistingSubcommands``: import/watch/submit/
    rebuild-index still resolve after the 6 new subparsers are added.

Per CLAUDE.md: ``encoding="utf-8"`` on every ``open()``; argv-list only for
subprocess; lazy %-logging.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent / "fixtures" / "evolution"
)


# ---------------------------------------------------------------------------
# register_cli test — existing 4 subcommands preserved
# ---------------------------------------------------------------------------


class TestRegisterCliPreservesExistingSubcommands:
    """Plan 02 must ADD 6 subparsers without breaking the existing 4."""

    def test_existing_four_subcommands_still_resolve(self):
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        # Existing 4 from P28/29.
        for existing in ("import", "watch", "submit", "rebuild-index"):
            assert existing in names, (
                f"existing subcommand {existing!r} missing after Plan 02 extension"
            )

    def test_new_six_subcommands_resolve(self):
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        for new in ("evolve", "review-queue", "show-patch", "approve", "reject", "rollback"):
            assert new in names, f"new subcommand {new!r} not registered"

    def test_evolve_requires_skill_arg(self):
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        # --skill is required; parsing without it must error (SystemExit).
        with pytest.raises(SystemExit):
            parser.parse_args(["evolve"])

    def test_evolve_dry_run_parses(self):
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        ns = parser.parse_args(
            ["evolve", "--skill", "screenplay", "--dry-run"]
        )
        assert ns.skill == "screenplay"
        assert ns.dry_run is True
        assert callable(ns.func)

    def test_evolve_insights_only_flag_exists(self):
        """--insights-only flag must exist per RESEARCH Open Question 3 RESOLVED."""
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        ns = parser.parse_args(
            ["evolve", "--skill", "screenplay", "--insights-only"]
        )
        assert ns.insights_only is True

    def test_approve_has_yes_flag(self):
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        ns = parser.parse_args(["approve", "pid_123", "--yes"])
        assert ns.patch_id == "pid_123"
        assert ns.yes is True

    def test_rollback_has_yes_flag(self):
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        ns = parser.parse_args(["rollback", "abc123", "--yes"])
        assert ns.commit_sha == "abc123"
        assert ns.yes is True


# ---------------------------------------------------------------------------
# evolve — dry-run path (no LLM call, no API key needed)
# ---------------------------------------------------------------------------


class TestEvolveCmdDryRun:
    """``--dry-run`` writes a stub insight without invoking the LLM."""

    def test_dry_run_writes_stub_insight_and_exits_zero(
        self, monkeypatch, tmp_path
    ):
        from hermes_cli.feedback import register_cli

        # Isolate HERMES_HOME so we don't touch the real ~/.hermes.
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        # Inside a repo root marker for _resolve_repo_root.
        (tmp_path / ".git").mkdir()

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(
            ["evolve", "--skill", "screenplay", "--dry-run"]
        )

        # Also need a sample SKILL.md so the stub insight can find a marker.
        skill_md = tmp_path / "skills" / "movie-experts" / "screenplay" / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text(
            "---\nname: screenplay\n---\n\n# Screenplay\n\n## When to use\n",
            encoding="utf-8",
        )

        # Seed at least one feedback record so the dry-run stub has an
        # evidence chain reference.
        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=tmp_path
        ), patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls:
            mock_store = MagicMock()
            mock_store.query.return_value = [{"record_id": "fb_001", "verdict": "needs_work"}]
            mock_store_cls.return_value = mock_store

            exit_code = args.func(args)

        assert exit_code == 0
        insights_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" / "evolution" / "insights.jsonl"
        )
        assert insights_path.is_file()
        lines = [
            ln for ln in insights_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(lines) >= 1
        record = json.loads(lines[0])
        assert "dry-run" in record["theme"]


# ---------------------------------------------------------------------------
# evolve --insights-only (RESEARCH Open Question 3)
# ---------------------------------------------------------------------------


class TestEvolveCmdInsightsOnly:
    """``--insights-only`` writes insights.jsonl but skips patch generation."""

    def test_insights_only_skips_patch_generation(
        self, monkeypatch, tmp_path
    ):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        (tmp_path / ".git").mkdir()

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(
            ["evolve", "--skill", "screenplay", "--insights-only"]
        )

        # Build a stub LLM client that returns the sample insights payload.
        sample_payload = json.loads(
            (FIXTURES_DIR / "sample_insights.json").read_text(encoding="utf-8")
        )
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=json.dumps(sample_payload)))]
        mock_client.chat.completions.create.return_value = mock_resp

        # Mock FeedbackStore.query to return non-empty so aggregation proceeds.
        fake_records = [{"record_id": "fb_001", "verdict": "needs_work"}]

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=tmp_path
        ), patch(
            "agent.evolution.make_aggregation_client",
            return_value=(mock_client, "stub-model"),
        ), patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls:
            mock_store = MagicMock()
            mock_store.query.return_value = fake_records
            mock_store.summary.return_value = {"good": 0, "needs_work": 1}
            mock_store_cls.return_value = mock_store

            exit_code = args.func(args)

        assert exit_code == 0
        insights_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" / "evolution" / "insights.jsonl"
        )
        assert insights_path.is_file()
        # queue.jsonl must NOT exist (insights-only skips patch generation).
        queue_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" / "evolution" / "queue.jsonl"
        )
        assert not queue_path.exists()


# ---------------------------------------------------------------------------
# evolve — no feedback path
# ---------------------------------------------------------------------------


class TestEvolveCmdNoFeedback:
    """``evolve`` on a skill with zero feedback prints a friendly message."""

    def test_no_feedback_exits_zero_with_message(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["evolve", "--skill", "screenplay"])

        with patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls:
            mock_store = MagicMock()
            mock_store.query.return_value = []  # empty feedback
            mock_store_cls.return_value = mock_store

            exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "nothing to evolve" in captured.out


# ---------------------------------------------------------------------------
# evolve — full pipeline (mock LLM + mock gate subprocess)
# ---------------------------------------------------------------------------


class TestEvolveCmdFullPipeline:
    """End-to-end evolve with mock LLM + mock gate subprocess.

    Asserts: insights written, passing patches → queue.jsonl, failing patches
    → failed_gate.jsonl, summary printed.
    """

    def test_full_pipeline_populates_queue(
        self, monkeypatch, tmp_path
    ):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        # Build a tmp git repo with a real SKILL.md so generate_additive_diff works.
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skill_md = repo_root / "skills" / "movie-experts" / "screenplay" / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text(
            "---\nname: screenplay\nmetadata:\n  hermes:\n    expert_id: screenplay\n    related_skills: []\n---\n\n"
            "# Screenplay Expert\n\n## When to use this skill\n\nTrigger.\n\n## References\n\n- [X](x.md)\n",
            encoding="utf-8",
        )

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["evolve", "--skill", "screenplay"])

        # Mock LLM client returns sample insights.
        sample_payload = json.loads(
            (FIXTURES_DIR / "sample_insights.json").read_text(encoding="utf-8")
        )
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=json.dumps(sample_payload)))]
        mock_client.chat.completions.create.return_value = mock_resp

        # Mock the gate subprocess to "pass" with a canned report.
        def fake_run(cmd, **kwargs):
            # cmd is argv-list; the gate invocation has --reports-dir <dir>.
            mock_result = MagicMock()
            # Find reports-dir in argv to write the report there.
            if "--reports-dir" in cmd:
                idx = cmd.index("--reports-dir")
                reports_dir = Path(cmd[idx + 1])
                reports_dir.mkdir(parents=True, exist_ok=True)
                # Find --patch to derive patch_id (we use the patch filename).
                patch_idx = cmd.index("--patch")
                patch_name = Path(cmd[patch_idx + 1]).stem
                report_path = reports_dir / f"{patch_name}.json"
                report_path.write_text(
                    json.dumps({
                        "verdict": "pass",
                        "mean_delta": 0.15,
                        "per_prompt_max_drop": -0.3,
                    }),
                    encoding="utf-8",
                )
                mock_result.returncode = 0
                mock_result.stdout = ""
                mock_result.stderr = ""
                return mock_result
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            return mock_result

        fake_records = [{"record_id": "fb_001", "verdict": "needs_work"}]

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=repo_root
        ), patch(
            "agent.evolution.make_aggregation_client",
            return_value=(mock_client, "stub-model"),
        ), patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls, patch(
            "subprocess.run", side_effect=fake_run
        ):
            mock_store = MagicMock()
            mock_store.query.return_value = fake_records
            mock_store.summary.return_value = {"needs_work": 1}
            mock_store_cls.return_value = mock_store

            exit_code = args.func(args)

        assert exit_code == 0
        queue_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" / "evolution" / "queue.jsonl"
        )
        assert queue_path.is_file()
        lines = [
            ln for ln in queue_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(lines) >= 1


# ---------------------------------------------------------------------------
# review-queue
# ---------------------------------------------------------------------------


class TestReviewQueueCmd:
    def test_empty_queue_prints_no_patches(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["review-queue"])
        exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "no pending patches" in captured.out or "no " in captured.out.lower()

    def test_populated_queue_lists_patches(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli, _resolve_evolution_dir
        from agent.evolution import PatchRecord, append_patch

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        evolution_dir = _resolve_evolution_dir()

        record = PatchRecord(
            patch_id="screenplay_test_patch",
            skill_id="screenplay",
            insight_id="insight_1",
            unified_diff="--- a\n+++ b\n",
            feedback_chain=["fb_001"],
            llm_rationale="Test rationale for verification",
            eval_gate_score={"verdict": "pass", "mean_delta": 0.15},
            status="pending",
            ts_queued=datetime.now(timezone.utc).isoformat(),
        )
        append_patch(record, evolution_dir)

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["review-queue"])
        exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "screenplay" in captured.out

    def test_skill_filter(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli, _resolve_evolution_dir
        from agent.evolution import PatchRecord, append_patch

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        evolution_dir = _resolve_evolution_dir()

        for skill in ("screenplay", "colorist"):
            rec = PatchRecord(
                patch_id=f"{skill}_test_patch",
                skill_id=skill,
                insight_id=f"{skill}_insight",
                unified_diff="--- a\n+++ b\n",
                feedback_chain=["fb_001"],
                llm_rationale="x",
                eval_gate_score={"verdict": "pass"},
                status="pending",
                ts_queued=datetime.now(timezone.utc).isoformat(),
            )
            append_patch(rec, evolution_dir)

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["review-queue", "--skill", "screenplay"])
        exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "screenplay" in captured.out
        assert "colorist" not in captured.out


# ---------------------------------------------------------------------------
# show-patch
# ---------------------------------------------------------------------------


class TestShowPatchCmd:
    def test_show_patch_not_found_exits_nonzero(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["show-patch", "nonexistent_patch_id"])
        exit_code = args.func(args)

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "not found" in captured.out.lower()

    def test_show_patch_happy_path(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli, _resolve_evolution_dir
        from agent.evolution import PatchRecord, append_patch

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        evolution_dir = _resolve_evolution_dir()

        record = PatchRecord(
            patch_id="screenplay_show_test",
            skill_id="screenplay",
            insight_id="insight_1",
            unified_diff="--- a/x.md\n+++ b/x.md\n@@ -1,1 +1,2 @@\n ctx\n+new line\n",
            feedback_chain=["fb_001", "fb_002"],
            llm_rationale="Operators consistently noted X is missing.",
            eval_gate_score={"verdict": "pass", "mean_delta": 0.2},
            status="pending",
            ts_queued=datetime.now(timezone.utc).isoformat(),
        )
        append_patch(record, evolution_dir)

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["show-patch", "screenplay_show_test"])
        exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "screenplay_show_test" in captured.out
        assert "Operators consistently noted" in captured.out
        assert "new line" in captured.out


# ---------------------------------------------------------------------------
# reject
# ---------------------------------------------------------------------------


class TestRejectCmd:
    def test_reject_moves_to_rejected(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli, _resolve_evolution_dir
        from agent.evolution import PatchRecord, append_patch, read_queue

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        evolution_dir = _resolve_evolution_dir()

        record = PatchRecord(
            patch_id="reject_target",
            skill_id="screenplay",
            insight_id="insight_1",
            unified_diff="--- a\n+++ b\n",
            feedback_chain=["fb_001"],
            llm_rationale="x",
            eval_gate_score={"verdict": "pass"},
            status="pending",
            ts_queued=datetime.now(timezone.utc).isoformat(),
        )
        append_patch(record, evolution_dir)

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["reject", "reject_target", "stale_baseline"])
        exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "reject_target" in captured.out

        rejected = read_queue(evolution_dir=evolution_dir, status="rejected")
        assert any(r.patch_id == "reject_target" for r in rejected)

    def test_reject_not_found_exits_nonzero(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["reject", "nope", "because"])
        exit_code = args.func(args)

        assert exit_code != 0
