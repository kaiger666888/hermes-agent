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
# CR-01: CURATE-05 auto-apply eligibility marker on evolve-produced patches
# ---------------------------------------------------------------------------


class TestEvolveCmdAutoApplyEligible:
    """CR-01 regression: ``hermes feedback evolve`` MUST set
    ``auto_apply_eligible=True`` on the produced PatchRecord when ALL of:
      - the skill is agent-created (NOT bundled)
      - ``feedback.curator.auto_apply_enabled`` is True
      - the gate passed AND ``mean_delta >= auto_apply_min_delta``
      - ``evidence_count >= auto_apply_min_evidence``

    Without this marker, the CURATE-05 consumer (_cmd_auto_apply_eligible)
    filtered on ``auto_apply_eligible`` and skipped every pending patch —
    making CURATE-05 dead code. Bundled skills MUST NEVER get the marker
    (T-32-05 defense-in-depth).
    """

    def _build_repo_with_skill(self, tmp_path, *, skill_id: str) -> Path:
        """Build a tmp git repo with a SKILL.md for *skill_id*."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skill_md = (
            repo_root / "skills" / "movie-experts" / skill_id / "SKILL.md"
        )
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text(
            "---\nname: " + skill_id + "\nmetadata:\n  hermes:\n    "
            "expert_id: " + skill_id + "\n    related_skills: []\n---\n\n"
            "# " + skill_id + " Expert\n\n## When to use\n\nTrigger.\n\n"
            "## References\n\n- [X](x.md)\n",
            encoding="utf-8",
        )
        return repo_root

    def _make_passing_gate_mock(self, *, mean_delta: float = 0.15):
        """Return a side_effect for ``hermes_cli.feedback._run_eval_gate``
        that always reports a pass with the requested mean_delta.

        Mocking _run_eval_gate directly (rather than subprocess.run) lets
        us control the score dict shape exactly — the production report
        filename is keyed on patch_id_for_report which is generated
        dynamically inside _cmd_evolve, making subprocess-level mocking
        fragile for assertions on score content.
        """
        def fake_gate(**kwargs):
            return "pass", {
                "verdict": "pass",
                "mean_delta": mean_delta,
                "per_prompt_max_drop": -0.3,
            }
        return fake_gate

    def test_agent_created_with_signals_pass_marks_eligible(
        self, monkeypatch, tmp_path,
    ):
        """Agent-created skill + auto_apply_enabled + signals pass →
        PatchRecord.auto_apply_eligible=True + confidence_score populated.
        End-to-end CURATE-05 producer path.
        """
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        repo_root = self._build_repo_with_skill(tmp_path, skill_id="agent_x")

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["evolve", "--skill", "agent_x"])

        sample_payload = json.loads(
            (FIXTURES_DIR / "sample_insights.json").read_text(encoding="utf-8")
        )
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(message=MagicMock(content=json.dumps(sample_payload)))
        ]
        mock_client.chat.completions.create.return_value = mock_resp

        # 4 fake records so evidence_count >= 3.
        fake_records = [
            {"record_id": f"fb_{i:03d}", "verdict": "needs_work"}
            for i in range(4)
        ]

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=repo_root
        ), patch(
            "agent.evolution.make_aggregation_client",
            return_value=(mock_client, "stub-model"),
        ), patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls, patch(
            "hermes_cli.feedback._run_eval_gate",
            side_effect=self._make_passing_gate_mock(),
        ), patch(
            # CR-01: auto_apply_enabled must be ON for the marker to be set.
            "agent.curator.get_auto_apply_enabled", return_value=True,
        ), patch(
            "agent.curator.get_auto_apply_min_delta", return_value=0.1,
        ), patch(
            # min_evidence=2 matches the sample_insights.json first insight
            # evidence_chain length (["fb_001", "fb_002"]).
            "agent.curator.get_auto_apply_min_evidence", return_value=2,
        ), patch(
            # agent_x is NOT in the bundled manifest → is_agent_created=True.
            "tools.skill_usage.is_agent_created", return_value=True,
        ):
            mock_store = MagicMock()
            mock_store.query.return_value = fake_records
            mock_store.summary.return_value = {"needs_work": 4}
            mock_store_cls.return_value = mock_store
            exit_code = args.func(args)

        assert exit_code == 0
        queue_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" /
            "evolution" / "queue.jsonl"
        )
        assert queue_path.is_file()
        from agent.evolution.queue import read_queue
        records = read_queue(
            evolution_dir=queue_path.parent, status="pending",
        )
        assert len(records) >= 1
        for r in records:
            assert r.skill_id == "agent_x"
            # CR-01 headline assertion: the marker IS set.
            assert r.auto_apply_eligible is True, (
                "CR-01 regression: evolve-produced agent-created patch "
                "must have auto_apply_eligible=True when auto_apply_enabled "
                "is on and both signals pass"
            )
            assert r.confidence_score is not None
            assert r.confidence_score["eligible"] is True
            assert r.confidence_score["mean_delta"] >= 0.1
            assert r.confidence_score["evidence_count"] >= 2

    def test_bundled_skill_never_marked_eligible(
        self, monkeypatch, tmp_path,
    ):
        """Bundled skill (is_agent_created=False) NEVER gets the marker
        even when auto_apply_enabled is on and signals pass. T-32-05
        defense-in-depth at the producer.
        """
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        # Use 'screenplay' — a real bundled skill name.
        repo_root = self._build_repo_with_skill(tmp_path, skill_id="screenplay")

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["evolve", "--skill", "screenplay"])

        sample_payload = json.loads(
            (FIXTURES_DIR / "sample_insights.json").read_text(encoding="utf-8")
        )
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(message=MagicMock(content=json.dumps(sample_payload)))
        ]
        mock_client.chat.completions.create.return_value = mock_resp

        fake_records = [
            {"record_id": f"fb_{i:03d}", "verdict": "needs_work"}
            for i in range(4)
        ]

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=repo_root
        ), patch(
            "agent.evolution.make_aggregation_client",
            return_value=(mock_client, "stub-model"),
        ), patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls, patch(
            "hermes_cli.feedback._run_eval_gate",
            side_effect=self._make_passing_gate_mock(),
        ), patch(
            "agent.curator.get_auto_apply_enabled", return_value=True,
        ), patch(
            "agent.curator.get_auto_apply_min_delta", return_value=0.1,
        ), patch(
            "agent.curator.get_auto_apply_min_evidence", return_value=3,
        ), patch(
            # screenplay IS bundled → is_agent_created=False.
            "tools.skill_usage.is_agent_created", return_value=False,
        ):
            mock_store = MagicMock()
            mock_store.query.return_value = fake_records
            mock_store.summary.return_value = {"needs_work": 4}
            mock_store_cls.return_value = mock_store
            exit_code = args.func(args)

        assert exit_code == 0
        queue_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" /
            "evolution" / "queue.jsonl"
        )
        assert queue_path.is_file()
        from agent.evolution.queue import read_queue
        records = read_queue(
            evolution_dir=queue_path.parent, status="pending",
        )
        assert len(records) >= 1
        for r in records:
            # T-32-05: bundled NEVER auto-apply eligible, even when
            # auto_apply_enabled is on and signals would otherwise pass.
            assert r.auto_apply_eligible is False

    def test_auto_apply_disabled_leaves_marker_false(
        self, monkeypatch, tmp_path,
    ):
        """When auto_apply_enabled=false (the default), the marker stays
        False even for agent-created skills with passing signals.
        """
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        repo_root = self._build_repo_with_skill(tmp_path, skill_id="agent_y")

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["evolve", "--skill", "agent_y"])

        sample_payload = json.loads(
            (FIXTURES_DIR / "sample_insights.json").read_text(encoding="utf-8")
        )
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(message=MagicMock(content=json.dumps(sample_payload)))
        ]
        mock_client.chat.completions.create.return_value = mock_resp

        fake_records = [
            {"record_id": f"fb_{i:03d}", "verdict": "needs_work"}
            for i in range(4)
        ]

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=repo_root
        ), patch(
            "agent.evolution.make_aggregation_client",
            return_value=(mock_client, "stub-model"),
        ), patch(
            "agent.feedback_store.FeedbackStore"
        ) as mock_store_cls, patch(
            "hermes_cli.feedback._run_eval_gate",
            side_effect=self._make_passing_gate_mock(),
        ), patch(
            # auto_apply_enabled=False — default config.
            "agent.curator.get_auto_apply_enabled", return_value=False,
        ), patch(
            "tools.skill_usage.is_agent_created", return_value=True,
        ):
            mock_store = MagicMock()
            mock_store.query.return_value = fake_records
            mock_store.summary.return_value = {"needs_work": 4}
            mock_store_cls.return_value = mock_store
            exit_code = args.func(args)

        assert exit_code == 0
        queue_path = (
            tmp_path / "hermes_home" / "skills" / ".feedback" /
            "evolution" / "queue.jsonl"
        )
        assert queue_path.is_file()
        from agent.evolution.queue import read_queue
        records = read_queue(
            evolution_dir=queue_path.parent, status="pending",
        )
        assert len(records) >= 1
        for r in records:
            # auto_apply_enabled=False → marker stays False.
            assert r.auto_apply_eligible is False


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


# ---------------------------------------------------------------------------
# approve — EVOL-04 non-bypassable human-in-loop + EVOL-05 atomic apply
# ---------------------------------------------------------------------------


class TestApproveCmdRequiresYes:
    """Per Plan-checker Warning 2/3: ``--yes`` is REQUIRED (no default-yes)."""

    def test_approve_without_yes_exits_nonzero_without_apply(
        self, monkeypatch, tmp_path, capsys
    ):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["approve", "some_patch_id"])  # no --yes

        with patch(
            "agent.evolution.apply_patch_transaction"
        ) as mock_apply:
            exit_code = args.func(args)

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "approval required" in captured.err.lower() or "--yes" in captured.err
        # CRITICAL: apply_patch_transaction MUST NOT be called without --yes.
        mock_apply.assert_not_called()


class TestApproveCmdNotFound:
    def test_approve_unknown_patch_exits_nonzero(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["approve", "unknown_pid", "--yes"])

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=tmp_path
        ):
            exit_code = args.func(args)

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "not found" in captured.out.lower()


class TestApproveCmdAppliesAndMoves:
    def test_approve_with_yes_calls_apply_and_moves(
        self, monkeypatch, tmp_path, capsys
    ):
        from hermes_cli.feedback import register_cli, _resolve_evolution_dir
        from agent.evolution import PatchRecord, append_patch, ApplyResult, read_queue

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        evolution_dir = _resolve_evolution_dir()

        record = PatchRecord(
            patch_id="approve_target",
            skill_id="screenplay",
            insight_id="insight_1",
            unified_diff="--- a/x.md\n+++ b/x.md\n@@ -1,1 +1,2 @@\n ctx\n+new\n",
            feedback_chain=["fb_001"],
            llm_rationale="x",
            eval_gate_score={"verdict": "pass", "mean_delta": 0.1},
            status="pending",
            ts_queued=datetime.now(timezone.utc).isoformat(),
        )
        append_patch(record, evolution_dir)

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["approve", "approve_target", "--yes"])

        fake_result = ApplyResult(
            commit_sha="abc123def456789012",
            files_modified=["skills/movie-experts/screenplay/SKILL.md"],
        )

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=tmp_path
        ), patch(
            "agent.evolution.apply_patch_transaction",
            return_value=fake_result,
        ) as mock_apply:
            exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "applied" in captured.out.lower()
        assert "abc123" in captured.out  # commit_sha[:12]
        mock_apply.assert_called_once()

        # The patch must have moved to applied.jsonl.
        applied = read_queue(evolution_dir=evolution_dir, status="applied")
        assert any(r.patch_id == "approve_target" for r in applied)


class TestApproveCmdOnApplyError:
    """ApplyError must NOT move the patch (stays pending)."""

    def test_apply_error_keeps_patch_pending(
        self, monkeypatch, tmp_path, capsys
    ):
        from hermes_cli.feedback import register_cli, _resolve_evolution_dir
        from agent.evolution import (
            PatchRecord, append_patch, ApplyError,
        )

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))
        evolution_dir = _resolve_evolution_dir()

        record = PatchRecord(
            patch_id="err_target",
            skill_id="screenplay",
            insight_id="insight_1",
            unified_diff="--- a/x.md\n+++ b/x.md\n",
            feedback_chain=["fb_001"],
            llm_rationale="x",
            eval_gate_score={"verdict": "pass"},
            status="pending",
            ts_queued=datetime.now(timezone.utc).isoformat(),
        )
        append_patch(record, evolution_dir)

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["approve", "err_target", "--yes"])

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=tmp_path
        ), patch(
            "agent.evolution.apply_patch_transaction",
            side_effect=ApplyError("FOUND-08 violation"),
        ), patch(
            "agent.evolution.move_patch"
        ) as mock_move:
            exit_code = args.func(args)

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "apply failed" in captured.err.lower() or "apply failed" in captured.out.lower()
        # CRITICAL: patch must NOT move to applied on ApplyError.
        mock_move.assert_not_called()


# ---------------------------------------------------------------------------
# rollback — EVOL-05 git revert
# ---------------------------------------------------------------------------


class TestRollbackCmdRequiresYes:
    """``--yes`` is required — git revert is destructive."""

    def test_rollback_without_yes_exits_nonzero_no_revert(
        self, monkeypatch, tmp_path, capsys
    ):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["rollback", "abc123"])  # no --yes

        with patch("subprocess.run") as mock_run:
            exit_code = args.func(args)

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "--yes" in captured.err
        mock_run.assert_not_called()


class TestRollbackCmdInvalidSha:
    def test_invalid_sha_exits_nonzero(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["rollback", "notasha", "--yes"])

        # Make git rev-parse fail (sha doesn't exist).
        def fake_run(cmd, **kwargs):
            mock_result = MagicMock()
            if "rev-parse" in cmd and "--verify" in cmd:
                mock_result.returncode = 1
                mock_result.stdout = ""
                mock_result.stderr = "fatal: ambiguous argument"
            else:
                mock_result.returncode = 0
                mock_result.stdout = ""
                mock_result.stderr = ""
            return mock_result

        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=tmp_path
        ), patch("subprocess.run", side_effect=fake_run):
            exit_code = args.func(args)

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "not found" in captured.out.lower()


class TestRollbackCmdHappyPath:
    """Rollback a real commit in a tmp git repo."""

    def test_rollback_reverts_commit(self, monkeypatch, tmp_path, capsys):
        from hermes_cli.feedback import register_cli

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes_home"))

        # Set up a real tmp git repo with one commit.
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        env = os.environ.copy()
        env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        env["GIT_AUTHOR_EMAIL"] = "test@example.com"
        env["GIT_AUTHOR_NAME"] = "Test"
        env["GIT_COMMITTER_EMAIL"] = "test@example.com"
        env["GIT_COMMITTER_NAME"] = "Test"

        def git(*cmd):
            return subprocess.run(
                ["git", *cmd],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )

        git("init", "-b", "main")
        (repo_root / "file.txt").write_text("v1\n", encoding="utf-8")
        git("add", "file.txt")
        git("commit", "-m", "initial")
        commit_sha = git("rev-parse", "HEAD").stdout.strip()

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        args = parser.parse_args(["rollback", commit_sha, "--yes"])

        # Use the real subprocess for git revert (no patch).
        with patch(
            "hermes_cli.feedback._resolve_repo_root", return_value=repo_root
        ):
            # Need to pass through env vars for git author.
            monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@example.com")
            monkeypatch.setenv("GIT_AUTHOR_NAME", "Test")
            monkeypatch.setenv("GIT_COMMITTER_EMAIL", "test@example.com")
            monkeypatch.setenv("GIT_COMMITTER_NAME", "Test")
            exit_code = args.func(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "reverted" in captured.out.lower()
        # Verify the revert commit exists.
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        ).stdout
        assert "revert" in log.lower() or len(log.splitlines()) >= 2


# ---------------------------------------------------------------------------
# EVOL-04 structural invariant — non-bypassable human-in-loop
# ---------------------------------------------------------------------------


class TestNonBypassableHumanInLoop:
    """The CRITICAL invariant: only ``_cmd_approve`` calls ``apply_patch_transaction``.

    We parse ``hermes_cli/feedback.py`` with :mod:`ast` and walk every Call
    node whose function name is ``apply_patch_transaction``. Each such Call
    must be enclosed in a function definition named ``_cmd_approve``.

    This is the structural enforcement of EVOL-04 — no auto-apply path
    exists. If a future contributor adds ``apply_patch_transaction()`` inside
    (say) ``_cmd_evolve`` or a curator module, this test fails and blocks
    the regression.
    """

    def test_only_cmd_approve_calls_apply_patch_transaction(self):
        feedback_path = (
            Path(__file__).resolve().parent.parent.parent
            / "hermes_cli" / "feedback.py"
        )
        source = feedback_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        violators: list[str] = []

        class _Walker(ast.NodeVisitor):
            def __init__(self) -> None:
                # Stack of enclosing FunctionDef names.
                self.func_stack: list[str] = []

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.func_stack.append(node.name)
                self.generic_visit(node)
                self.func_stack.pop()

            def visit_AsyncFunctionDef(self, node) -> None:
                self.func_stack.append(node.name)
                self.generic_visit(node)
                self.func_stack.pop()

            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                name: str | None = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name == "apply_patch_transaction":
                    enclosing = self.func_stack[-1] if self.func_stack else "<module>"
                    if enclosing != "_cmd_approve":
                        violators.append(
                            f"line {node.lineno}: apply_patch_transaction "
                            f"called from {enclosing!r} (must be _cmd_approve)"
                        )
                self.generic_visit(node)

        _Walker().visit(tree)

        assert not violators, (
            "EVOL-04 non-bypassable human-in-loop VIOLATED: "
            + "; ".join(violators)
        )

    def test_apply_patch_transaction_not_called_in_agent_or_runtime(self):
        """Beyond hermes_cli/feedback.py, the runtime must never call it.

        Verifies the broader isolation: agent/, run_agent.py, cli.py, gateway/
        contain zero ``apply_patch_transaction(`` calls (excluding the
        evolution subpackage itself, which owns the function definition).
        """
        repo_root = Path(__file__).resolve().parent.parent.parent
        violators: list[str] = []
        for sub in ("agent", "gateway", "run_agent.py", "cli.py"):
            root = repo_root / sub
            if root.is_file():
                files = [root]
            elif root.is_dir():
                files = list(root.rglob("*.py"))
            else:
                continue
            for f in files:
                # Skip test files, __pycache__, evolution subpackage itself.
                if "tests" in f.parts or "__pycache__" in f.parts:
                    continue
                if "agent/evolution" in str(f):
                    continue
                try:
                    source = f.read_text(encoding="utf-8")
                    tree = ast.parse(source)
                except (SyntaxError, UnicodeDecodeError):
                    continue

                class _Walker(ast.NodeVisitor):
                    def visit_Call(self, node: ast.Call) -> None:
                        func = node.func
                        name: str | None = None
                        if isinstance(func, ast.Name):
                            name = func.id
                        elif isinstance(func, ast.Attribute):
                            name = func.attr
                        if name == "apply_patch_transaction":
                            violators.append(str(f.relative_to(repo_root)))
                        self.generic_visit(node)

                _Walker().visit(tree)
        assert not violators, (
            "apply_patch_transaction called outside hermes_cli/feedback.py "
            "in runtime code: " + ", ".join(violators)
        )
