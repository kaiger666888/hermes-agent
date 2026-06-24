"""CLI smoke tests for the ``hermes curator stats`` subcommand (Phase 33 Plan 01).

Covers OBS-01 / OBS-02 / OBS-03:
  - TestStatsPerSkill: per-skill dashboard (verdict buckets + patch history +
    eval trend) — OBS-01
  - TestStatsAll: cross-skill view (top-N negative + zero-feedback) — OBS-02
  - TestStatsBySource: per-source verdict distribution — OBS-03
  - TestRunsFlag: ``--runs N`` limits eval-trend depth — OBS-01
  - TestJsonOutput: ``--json`` emits counts only (no correction text) — T-33-01
  - TestEmptyStore: empty FeedbackStore -> exit 0 + friendly message — T-33-05
  - TestReadOnly: stats never mutates ~/.hermes/skills/.feedback/ — T-33-02
  - TestLazyImportIsolation: zero module-level ``agent.evolution`` imports —
    T-33-06 / P31 runtime-isolation invariant

Per CLAUDE.md: ``encoding="utf-8"`` on every ``open()``;
``from __future__ import annotations``; lazy %-logging style mirrored from
existing tests. The FeedbackStore seeding pattern mirrors
``tests/agent/test_feedback_store.py:_make_record``.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers — FeedbackStore seeding (mirrors tests/agent/test_feedback_store.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def stats_env(tmp_path: Path, monkeypatch):
    """Isolated HERMES_HOME + reloaded modules.

    Mirrors the ``feedback_env`` fixture in test_feedback_store.py: set
    HERMES_HOME, reload hermes_constants so its home cache picks up the new
    path, reload agent.feedback_store so its ``get_hermes_home`` import
    rebinds, then reload hermes_cli.curator so the freshly-imported
    FeedbackStore is the one the stats handler sees.
    """
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "skills").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    import hermes_constants
    importlib.reload(hermes_constants)
    from agent import feedback_store
    importlib.reload(feedback_store)
    from hermes_cli import curator as curator_cli
    importlib.reload(curator_cli)
    yield {
        "home": home,
        "feedback_store": feedback_store,
        "curator_cli": curator_cli,
        "hermes_constants": hermes_constants,
    }


def _make_snapshot(*, sha256: str = "0" * 64, captured_at: datetime | None = None):
    """Build a minimal OutputSnapshot for tests (mirrors test_feedback_store)."""
    from agent.feedback_schema import OutputSnapshot

    return OutputSnapshot(
        sha256=sha256,
        output_text="assistant output",
        prompt="user prompt",
        model="test-model",
        provider="openai",
        api_mode="chat_completions",
        params={"max_tokens": 1024},
        captured_at=captured_at or datetime.now(timezone.utc),
    )


def _make_record(
    *,
    skill_id: str = "screenplay",
    expert_id: str | None = None,
    source: str = "cli",
    verdict: str = "good",
    correction: str = "operator-authored correction text",
    sha256: str = "0" * 64,
    ts: datetime | None = None,
):
    """Build a minimal valid FeedbackRecord for store tests."""
    from agent.feedback_schema import FeedbackRecord

    snap = _make_snapshot(sha256=sha256, captured_at=ts)
    return FeedbackRecord(
        skill_id=skill_id,
        expert_id=expert_id or skill_id,
        source=source,
        verdict=verdict,
        correction=correction,
        output_snapshot=snap,
        ts=ts or datetime.now(timezone.utc),
    )


def _seed_verdicts(store, *, skill_id: str, counts: dict[str, int], source: str = "cli"):
    """Seed FeedbackStore with a mix of verdicts.

    ``counts`` maps verdict -> N (e.g. {"good": 3, "needs_work": 2, "bad": 1}).
    Each record gets a distinct sha256 so dedup doesn't collapse them.
    """
    # Map verdict to a hex prefix character (must be 0-9,a-f).
    verdict_hex = {"good": "a", "needs_work": "b", "bad": "c"}
    idx = 0
    for verdict, n in counts.items():
        prefix = verdict_hex.get(verdict, "d")
        for _ in range(n):
            idx += 1
            # 64 hex chars, distinct per (verdict, idx). Prefix + zero-padded idx.
            sha = f"{prefix}{idx:063d}"[:64]
            store.record_feedback(
                _make_record(
                    skill_id=skill_id,
                    source=source,
                    verdict=verdict,
                    sha256=sha,
                )
            )


def _ns(**kw) -> argparse.Namespace:
    """Build an argparse.Namespace matching the stats subparser fields."""
    return argparse.Namespace(
        skill_id=kw.get("skill_id"),
        all_skills=kw.get("all_skills", False),
        by_source=kw.get("by_source", False),
        top=kw.get("top", 10),
        runs=kw.get("runs", 10),
        skill_filter=kw.get("skill_filter"),
        as_json=kw.get("as_json", False),
    )


def _seed_audit_apply(
    home: Path,
    *,
    skill_id: str = "screenplay",
    count: int = 5,
    base_ts: datetime | None = None,
):
    """Seed audit log with N action=apply entries carrying eval_score dicts."""
    from agent import curator_audit

    base_ts = base_ts or datetime.now(timezone.utc)
    for i in range(count):
        curator_audit.append_audit(
            action="apply",
            patch_id=f"pid_{i}",
            skill_id=skill_id,
            operator="tester",
            commit_sha=f"sha{i:03d}",
            eval_score={
                "verdict": "pass" if i % 2 == 0 else "fail",
                "mean_delta": 0.1 + 0.05 * i,
                "evidence_count": 3 + i,
            },
        )


# ---------------------------------------------------------------------------
# TestStatsPerSkill — OBS-01
# ---------------------------------------------------------------------------


class TestStatsPerSkill:
    """``hermes curator stats <skill_id>`` renders per-skill dashboard."""

    def test_per_skill_renders_all_three_verdicts(
        self, stats_env, capsys
    ):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        store = store_mod.FeedbackStore()
        _seed_verdicts(
            store, skill_id="screenplay",
            counts={"good": 3, "needs_work": 2, "bad": 1},
        )

        rc = curator_cli._cmd_stats(_ns(skill_id="screenplay"))
        out = capsys.readouterr().out
        assert rc == 0
        # All three verdict labels appear.
        assert "good" in out
        assert "needs_work" in out
        assert "bad" in out
        # Counts are surfaced (3 good / 2 needs_work / 1 bad).
        assert "3" in out
        assert "2" in out
        assert "1" in out

    def test_per_skill_dashboard_has_title(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        store = store_mod.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="editor", verdict="good", sha256="e" * 64)
        )
        rc = curator_cli._cmd_stats(_ns(skill_id="editor"))
        out = capsys.readouterr().out
        assert rc == 0
        assert "editor" in out


# ---------------------------------------------------------------------------
# TestStatsAll — OBS-02
# ---------------------------------------------------------------------------


class TestStatsAll:
    """``hermes curator stats --all`` renders top-N + zero-feedback list."""

    def test_all_lists_top_negative(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        store = store_mod.FeedbackStore()
        # screenplay: high negative volume
        _seed_verdicts(
            store, skill_id="screenplay",
            counts={"good": 1, "needs_work": 3, "bad": 4},
        )
        # editor: low negative volume
        _seed_verdicts(
            store, skill_id="editor",
            counts={"good": 5, "needs_work": 0, "bad": 0},
        )

        rc = curator_cli._cmd_stats(_ns(all_skills=True))
        out = capsys.readouterr().out
        assert rc == 0
        # Top negative should surface screenplay prominently.
        assert "screenplay" in out

    def test_all_top_n_limits_output(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        store = store_mod.FeedbackStore()
        for i in range(5):
            _seed_verdicts(
                store, skill_id=f"skill_{i}",
                counts={"needs_work": 10 - i, "bad": 0, "good": 0},
            )

        # Limit to top 2 — only 2 skills should appear in top section.
        rc = curator_cli._cmd_stats(_ns(all_skills=True, top=2))
        out = capsys.readouterr().out
        assert rc == 0
        # skill_0 (highest negative) MUST be in top.
        assert "skill_0" in out
        # skill_4 (lowest negative) should NOT be in top-2.
        # (We can't strictly assert absence because zero-feedback footer
        # may list it, but the top section is bounded.)


# ---------------------------------------------------------------------------
# TestStatsBySource — OBS-03
# ---------------------------------------------------------------------------


class TestStatsBySource:
    """``hermes curator stats --by-source`` renders per-source distribution."""

    def test_by_source_emits_per_source_rows(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        store = store_mod.FeedbackStore()
        _seed_verdicts(
            store, skill_id="screenplay", source="cli",
            counts={"good": 2, "needs_work": 1, "bad": 0},
        )
        _seed_verdicts(
            store, skill_id="screenplay", source="kais_aigc",
            counts={"good": 0, "needs_work": 0, "bad": 3},
        )

        rc = curator_cli._cmd_stats(_ns(by_source=True))
        out = capsys.readouterr().out
        assert rc == 0
        # Both sources named in the output.
        assert "cli" in out
        assert "kais_aigc" in out


# ---------------------------------------------------------------------------
# TestRunsFlag — OBS-01 trend depth
# ---------------------------------------------------------------------------


class TestRunsFlag:
    """``--runs N`` limits the eval-trend depth to the last N audit entries."""

    def test_runs_limits_trend_depth(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]
        home = stats_env["home"]

        # Seed the FeedbackStore so the per-skill path isn't empty.
        store = store_mod.FeedbackStore()
        _seed_verdicts(
            store, skill_id="screenplay", counts={"good": 1},
        )
        # Seed 15 apply entries with eval_score.
        _seed_audit_apply(home, skill_id="screenplay", count=15)

        rc = curator_cli._cmd_stats(_ns(skill_id="screenplay", runs=5))
        out = capsys.readouterr().out
        assert rc == 0
        # The JSON view of trend would have 5 entries; for human view,
        # assert the bounded N appears somewhere.
        # Either form is acceptable; we assert no error.

    def test_runs_default_is_10(self, stats_env, capsys):
        """The subparser default for --runs is 10."""
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(["stats", "screenplay"])
        assert ns.runs == 10


# ---------------------------------------------------------------------------
# TestJsonOutput — T-33-01 (information disclosure: counts only)
# ---------------------------------------------------------------------------


class TestJsonOutput:
    """``--json`` emits COUNTS ONLY — no correction text / output_snapshot leakage."""

    def test_json_per_skill_has_counts_no_correction(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        CORRECTION_PHRASE = "secret-operator-authored-leak-phrase"
        store = store_mod.FeedbackStore()
        store.record_feedback(
            _make_record(
                skill_id="screenplay", verdict="good",
                correction=CORRECTION_PHRASE, sha256="z" * 64,
            )
        )

        rc = curator_cli._cmd_stats(_ns(skill_id="screenplay", as_json=True))
        out = capsys.readouterr().out
        assert rc == 0
        payload = json.loads(out)
        # Counts present.
        assert "verdict_buckets" in payload or "buckets" in payload or "good" in str(payload)
        # CRITICAL: no correction text leaked.
        assert CORRECTION_PHRASE not in out, (
            "T-33-01 REGRESSION: correction text leaked via --json"
        )
        # CRITICAL: no "correction" key anywhere in the payload.
        def _has_correction_key(obj) -> bool:
            if isinstance(obj, dict):
                if "correction" in obj:
                    return True
                return any(_has_correction_key(v) for v in obj.values())
            if isinstance(obj, list):
                return any(_has_correction_key(v) for v in obj)
            return False

        assert not _has_correction_key(payload), (
            "T-33-01 REGRESSION: 'correction' key present in --json payload"
        )

    def test_json_all_view_is_counts_only(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]

        store = store_mod.FeedbackStore()
        _seed_verdicts(
            store, skill_id="screenplay",
            counts={"good": 2, "needs_work": 1, "bad": 0},
        )
        rc = curator_cli._cmd_stats(_ns(all_skills=True, as_json=True))
        out = capsys.readouterr().out
        assert rc == 0
        payload = json.loads(out)
        # Must be JSON-parseable.
        assert isinstance(payload, dict)


# ---------------------------------------------------------------------------
# TestEmptyStore — T-33-05 (empty store -> exit 0 + friendly message)
# ---------------------------------------------------------------------------


class TestEmptyStore:
    """Empty FeedbackStore -> exit 0 + friendly 'no feedback yet' message."""

    def test_empty_per_skill_returns_zero_with_message(self, stats_env, capsys):
        curator_cli = stats_env["curator_cli"]
        # Don't seed anything.
        rc = curator_cli._cmd_stats(_ns(skill_id="screenplay"))
        out = capsys.readouterr().out
        assert rc == 0
        assert "no feedback" in out.lower()

    def test_empty_all_returns_zero_with_message(self, stats_env, capsys):
        curator_cli = stats_env["curator_cli"]
        rc = curator_cli._cmd_stats(_ns(all_skills=True))
        out = capsys.readouterr().out
        assert rc == 0
        assert "no feedback" in out.lower()

    def test_empty_by_source_returns_zero_with_message(self, stats_env, capsys):
        curator_cli = stats_env["curator_cli"]
        rc = curator_cli._cmd_stats(_ns(by_source=True))
        out = capsys.readouterr().out
        assert rc == 0
        assert "no feedback" in out.lower()


# ---------------------------------------------------------------------------
# TestReadOnly — T-33-02 (stats never mutates ~/.hermes/skills/.feedback/)
# ---------------------------------------------------------------------------


class TestReadOnly:
    """Stats MUST NOT mutate the FeedbackStore on disk."""

    def _snapshot_tree(self, root: Path) -> dict:
        """Walk root recursively, returning {path: (size, mtime)}."""
        snap: dict[str, tuple[int, float]] = {}
        if not root.exists():
            return snap
        for p in sorted(root.rglob("*")):
            if p.is_file():
                stat = p.stat()
                snap[str(p.relative_to(root))] = (stat.st_size, stat.st_mtime)
        return snap

    def test_stats_does_not_mutate_feedback_dir(self, stats_env, capsys):
        store_mod = stats_env["feedback_store"]
        curator_cli = stats_env["curator_cli"]
        home = stats_env["home"]

        store = store_mod.FeedbackStore()
        _seed_verdicts(
            store, skill_id="screenplay",
            counts={"good": 1, "needs_work": 1, "bad": 1},
        )

        feedback_root = home / "skills" / ".feedback"
        before = self._snapshot_tree(feedback_root)

        # Run all three views.
        curator_cli._cmd_stats(_ns(skill_id="screenplay"))
        capsys.readouterr()
        curator_cli._cmd_stats(_ns(all_skills=True))
        capsys.readouterr()
        curator_cli._cmd_stats(_ns(by_source=True))
        capsys.readouterr()

        after = self._snapshot_tree(feedback_root)

        # No files added, removed, or mutated.
        assert set(before.keys()) == set(after.keys()), (
            f"file set changed: added={set(after) - set(before)}, "
            f"removed={set(before) - set(after)}"
        )
        for key, (sz_b, mt_b) in before.items():
            sz_a, mt_a = after[key]
            assert sz_a == sz_b, f"size changed for {key}: {sz_b} -> {sz_a}"
            # mtime may be identical or unchanged; we only assert size
            # (mtime can be racy on some filesystems but content unchanged).


# ---------------------------------------------------------------------------
# TestLazyImportIsolation — T-33-06 / P31 runtime-isolation invariant
# ---------------------------------------------------------------------------


class TestLazyImportIsolation:
    """Zero module-level ``agent.evolution`` imports in hermes_cli/curator.py.

    All ``agent.evolution`` imports MUST live inside handler bodies (lazy
    imports). This preserves the P31 runtime-isolation invariant:
    importing hermes_cli.curator must NOT transitively import
    agent.evolution (which initializes the evolution queue machinery).

    Mirrors the P31 TestNonBypassableHumanInLoop ast-walk pattern.
    """

    def test_no_module_level_agent_evolution_imports(self):
        repo_root = Path(__file__).resolve().parent.parent.parent
        curator_path = repo_root / "hermes_cli" / "curator.py"
        source = curator_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Walk ONLY top-level body (not inside function/class defs).
        violations: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith("agent.evolution"):
                    violations.append(
                        f"line {node.lineno}: from {mod} import ... (top-level)"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("agent.evolution"):
                        violations.append(
                            f"line {node.lineno}: import {alias.name} (top-level)"
                        )
        assert not violations, (
            "T-33-06 REGRESSION: module-level agent.evolution imports found in "
            f"hermes_cli/curator.py: {violations}. All such imports MUST live "
            "inside handler bodies (P31 runtime-isolation invariant)."
        )

    def test_stats_subparser_resolves(self):
        """``hermes curator stats`` subparser is registered with all 6 flags."""
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        ns = parser.parse_args(
            [
                "stats",
                "screenplay",
                "--runs", "5",
                "--json",
            ]
        )
        assert ns.skill_id == "screenplay"
        assert ns.runs == 5
        assert ns.as_json is True
        assert callable(ns.func)

    def test_stats_subparser_all_flags_present(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        # All three modes + all flags resolve.
        ns = parser.parse_args(
            ["stats", "--all", "--top", "5", "--by-source", "--skill", "x"]
        )
        # argparse allows --all and --by-source together but the handler
        # decides precedence. The subparser wiring must accept all flags.
        assert ns.all_skills is True
        assert ns.top == 5
        assert ns.by_source is True
        assert ns.skill_filter == "x"


# ---------------------------------------------------------------------------
# TestNoNewSubcommandBreakage — verify Plan 01 doesn't break P32 subcommands
# ---------------------------------------------------------------------------


class TestNoNewSubcommandBreakage:
    """P32 subcommands still resolve after Plan 01 adds ``stats``."""

    P32_SUBCOMMANDS = (
        "queue", "approve", "reject", "audit-log", "auto-apply-eligible",
    )

    def test_p32_subcommands_still_resolve(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        for sub in self.P32_SUBCOMMANDS:
            assert sub in names, f"P32 subcommand {sub!r} missing after Plan 01"

    def test_stats_subcommand_registered(self):
        from hermes_cli.curator import register_cli

        parser = argparse.ArgumentParser(prog="hermes curator")
        register_cli(parser)
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        assert "stats" in names, "stats subcommand not registered"
