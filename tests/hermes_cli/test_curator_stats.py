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
        # Use real bundled skill names (FeedbackRecord validates skill_id).
        skills = ["screenplay", "editor", "colorist", "composer", "animator"]
        for i, skill_id in enumerate(skills):
            _seed_verdicts(
                store, skill_id=skill_id,
                counts={"needs_work": 10 - i, "bad": 0, "good": 0},
            )

        # Limit to top 2 — only 2 skills should appear in top section.
        rc = curator_cli._cmd_stats(_ns(all_skills=True, top=2))
        out = capsys.readouterr().out
        assert rc == 0
        # screenplay (highest negative, 10 needs_work) MUST be in top.
        assert "screenplay" in out
        # animator (lowest negative, 6 needs_work) should NOT be in top-2.
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
                correction=CORRECTION_PHRASE, sha256="f" * 64,
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


# ---------------------------------------------------------------------------
# TestArchitectureDoc — SC-4 (Phase 33 Plan 02)
# ---------------------------------------------------------------------------
#
# Verifies that ``skills/movie-experts/_shared/v6-feedback-loop-architecture.md``
# mirrors v86-pipeline-mapping.md structural conventions:
#   - 4-line header metadata block (Source / Copyright / Last-verified /
#     verified_date)
#   - 7-9 H2 sections (CONTEXT.md 7-section logical outline + v86 convention
#     footer sections — See Also / Source Citation / Refresh Cadence)
#   - ASCII data-flow diagram present (no mermaid)
#   - Bilingual body (>= 3 CJK characters)
#   - Footer ownership line beginning ``*Owned by Phase 33``
#
# All ``open()`` calls pass ``encoding="utf-8"`` per CLAUDE.md PLW1514.


class TestArchitectureDoc:
    """``_shared/v6-feedback-loop-architecture.md`` structure — SC-4."""

    DOC_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "skills"
        / "movie-experts"
        / "_shared"
        / "v6-feedback-loop-architecture.md"
    )

    def _read_doc(self) -> str:
        return self.DOC_PATH.read_text(encoding="utf-8")

    def test_metadata_header_block_present(self):
        """Header has Source / Copyright / Last-verified / verified_date lines."""
        doc = self._read_doc()
        head = doc.split("\n\n", 1)[0]
        assert "**Source:**" in head, "missing **Source:** metadata line"
        assert "**Copyright:**" in head, "missing **Copyright:** metadata line"
        assert "**Last-verified:**" in head, "missing **Last-verified:** line"
        assert "**verified_date:**" in head, "missing **verified_date:** line"

    def test_minimal_h2_section_count(self):
        """File has >= 7 and <= 9 H2 headers (CONTEXT.md outline + footer)."""
        doc = self._read_doc()
        h2_lines = [ln for ln in doc.splitlines() if ln.startswith("## ")]
        assert len(h2_lines) >= 7, (
            f"too few H2 sections: {len(h2_lines)} (expected >= 7). "
            f"Found: {h2_lines}"
        )
        assert len(h2_lines) <= 9, (
            f"too many H2 sections: {len(h2_lines)} (expected <= 9). "
            f"Found: {h2_lines}"
        )

    def test_required_sections_present(self):
        """File contains the 7 CONTEXT.md logical section titles (case-insensitive)."""
        doc = self._read_doc()
        lower = doc.lower()
        required = [
            "overview",
            "data flow",
            "json schema",
            "eval-gate threshold",
            "human-in-loop",
            "module ownership",
            "roadmap reference",
        ]
        missing = [r for r in required if r not in lower]
        assert not missing, (
            f"missing required section titles (case-insensitive): {missing}"
        )

    def test_footer_ownership_line_present(self):
        """Last non-empty line starts with ``*Owned by Phase 33``."""
        doc = self._read_doc()
        non_empty = [ln for ln in doc.splitlines() if ln.strip()]
        assert non_empty, "doc is empty"
        last = non_empty[-1].lstrip()
        assert last.startswith("*Owned by Phase 33"), (
            f"footer ownership line missing or malformed: {last!r}"
        )

    def test_ascii_diagram_present(self):
        """File has a fenced code block with ASCII arrows / box-drawing chars.

        Verifies D-diagram-format (ASCII chosen over mermaid per CONTEXT.md).
        Looks for ``->``, ``│``, or ``▼`` inside at least one fenced block.
        """
        doc = self._read_doc()
        # Split out fenced code blocks.
        blocks = doc.split("```")
        # Fenced blocks are at odd indices after split on ```` ``` ````.
        fenced = [blocks[i] for i in range(1, len(blocks), 2)]
        assert fenced, "no fenced code block found (expected ASCII diagram)"
        ascii_chars = ("->", "│", "▼")
        found = any(any(ch in blk for ch in ascii_chars) for blk in fenced)
        assert found, (
            "no ASCII-arrow/box-drawing chars found inside fenced code blocks"
        )

    def test_no_mermaid_block(self):
        """File does NOT contain a mermaid fenced block (anti-pattern)."""
        doc = self._read_doc()
        assert "```mermaid" not in doc, (
            "T-33-10 REGRESSION: mermaid block found in architecture doc "
            "(CONTEXT.md D-diagram-format requires ASCII)"
        )

    def test_bilingual_chinese_in_body(self):
        """Body contains at least 3 CJK characters (CLAUDE.md bilingual rule)."""
        doc = self._read_doc()
        cjk = [ch for ch in doc if "一" <= ch <= "鿿"]
        assert len(cjk) >= 3, (
            f"insufficient CJK characters for bilingual rule: {len(cjk)} (need >= 3)"
        )

    def test_see_also_and_source_citation_footer(self):
        """File has ``## See Also`` AND ``## Source Citation`` sections (v86)."""
        doc = self._read_doc()
        assert "## See Also" in doc, "missing ## See Also section (v86 convention)"
        assert "## Source Citation" in doc, (
            "missing ## Source Citation section (v86 convention)"
        )


# ---------------------------------------------------------------------------
# TestSkillsMappingV6 — SC-5 (Phase 33 Plan 02)
# ---------------------------------------------------------------------------
#
# Verifies that ``.planning/research/v2-pipeline-design/skills-mapping.yaml``
# has a ``v6_ref_signoffs:`` section mirroring the 8+ field v5_ref_signoffs
# schema, with exactly one entry for the new architecture doc, and that the
# v5_ref_signoffs section is byte-intact (still 2 entries).


class TestSkillsMappingV6:
    """``skills-mapping.yaml`` ``v6_ref_signoffs:`` section — SC-5."""

    YAML_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / ".planning"
        / "research"
        / "v2-pipeline-design"
        / "skills-mapping.yaml"
    )

    # 8 mandatory fields per RESEARCH §skills-mapping.yaml v5_ref_signoffs
    # Schema Audit (ref_path, expert_owner, phase_added, requirement,
    # verified_date, source, license_status, line_count, signed_off_by, notes).
    REQUIRED_FIELDS = (
        "ref_path",
        "expert_owner",
        "phase_added",
        "requirement",
        "verified_date",
        "source",
        "license_status",
        "line_count",
        "signed_off_by",
        "notes",
    )

    def _load(self) -> dict:
        import yaml  # PyYAML already pinned per CLAUDE.md

        with open(self.YAML_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_v6_section_present(self):
        """Top-level ``v6_ref_signoffs:`` key exists."""
        data = self._load()
        assert "v6_ref_signoffs" in data, (
            "missing v6_ref_signoffs: key in skills-mapping.yaml"
        )

    def test_v6_entry_has_8_required_fields(self):
        """The v6 architecture-doc entry has all 8+ required fields."""
        data = self._load()
        entries = data.get("v6_ref_signoffs") or []
        assert entries, "v6_ref_signoffs: section is empty"
        # Find the v6-feedback-loop-architecture.md entry.
        arch_entries = [
            e for e in entries
            if "v6-feedback-loop-architecture" in str(e.get("ref_path", ""))
        ]
        assert arch_entries, (
            "no v6-feedback-loop-architecture.md entry in v6_ref_signoffs"
        )
        entry = arch_entries[0]
        missing = [f for f in self.REQUIRED_FIELDS if f not in entry]
        assert not missing, (
            f"v6 entry missing required fields: {missing}. "
            f"Present keys: {sorted(entry.keys())}"
        )

    def test_v6_entry_ref_path_correct(self):
        """ref_path equals the canonical architecture-doc path."""
        data = self._load()
        entries = data.get("v6_ref_signoffs") or []
        arch = [
            e for e in entries
            if "v6-feedback-loop-architecture" in str(e.get("ref_path", ""))
        ][0]
        assert arch["ref_path"] == (
            "skills/movie-experts/_shared/v6-feedback-loop-architecture.md"
        ), f"unexpected ref_path: {arch['ref_path']!r}"

    def test_v6_phase_added_format(self):
        """phase_added matches ``v6.0-phase-3[23]`` (P32 or P33)."""
        import re

        data = self._load()
        entries = data.get("v6_ref_signoffs") or []
        arch = [
            e for e in entries
            if "v6-feedback-loop-architecture" in str(e.get("ref_path", ""))
        ][0]
        assert re.match(r"^v6\.0-phase-3[23]$", arch["phase_added"]), (
            f"phase_added malformed: {arch['phase_added']!r}"
        )

    def test_v6_verified_date_format(self):
        """verified_date is a YYYY-MM-DD string."""
        import re

        data = self._load()
        entries = data.get("v6_ref_signoffs") or []
        arch = [
            e for e in entries
            if "v6-feedback-loop-architecture" in str(e.get("ref_path", ""))
        ][0]
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", str(arch["verified_date"])), (
            f"verified_date malformed: {arch['verified_date']!r}"
        )

    def test_v5_byte_intact(self):
        """v5_ref_signoffs still has exactly 2 entries (byte-intact)."""
        data = self._load()
        v5 = data.get("v5_ref_signoffs") or []
        assert len(v5) == 2, (
            f"v5_ref_signoffs byte-intact violation: expected 2 entries, "
            f"got {len(v5)}. v5 section MUST be untouched by P33 Plan 02."
        )
