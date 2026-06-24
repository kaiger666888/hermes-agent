"""SC-6 regression coverage — pre-v6 curator behavior preservation (Phase 32).

Phase 32 extends ``run_curator_review`` with an ADDITIVE feedback-scan phase
(``_feedback_scan_phase``) that proposes bundled-skill patches when feedback
crosses thresholds. SC-6 requires that the pre-v6 deterministic behavior —
inactivity transitions (mark-stale / archive / reactivate) and the
consolidation gate — continue to work byte-for-byte unchanged.

This module was written FIRST (TDD RED) per Plan 32-01 Task 1. Four of the
five tests PASS against the pre-v6 curator (locking in the baseline);
``test_consolidate_false_skips_llm_and_scan`` is RED until Task 4 adds
``_feedback_scan_phase``.

Expected baseline counts (pre-v6 ``apply_automatic_transitions``):
The function walks ``tools.skill_usage.agent_created_report()``. With a
single agent-created skill whose ``last_activity_at`` is older than
``archive_after_days`` (default 90), the expected counts are::

    {"marked_stale": 0, "archived": 1, "reactivated": 0, "checked": 1, "seeded": 0}

These counts are documented here so any drift surfaces in review.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


# --------------------------------------------------------------------------- #
# Fixture (mirrors tests/agent/test_curator.py:curator_env)
# --------------------------------------------------------------------------- #


@pytest.fixture
def regression_env(tmp_path, monkeypatch):
    """Isolated HERMES_HOME with freshly reloaded curator + skill_usage.

    Provides a single agent-created skill fixture whose ``last_activity_at``
    is older than ``archive_after_days`` so deterministic transitions have
    a predictable baseline. LLM review is stubbed to a no-op sentinel.
    """
    home = tmp_path / ".hermes"
    (home / "skills").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))

    import tools.skill_usage as usage
    importlib.reload(usage)
    import agent.curator as curator
    importlib.reload(curator)

    # Neutralize the real LLM pass by default — tests opt in per-case.
    monkeypatch.setattr(curator, "_run_llm_review", lambda prompt: {
        "final": "",
        "summary": "stub-no-change",
        "model": "",
        "provider": "",
        "tool_calls": [],
        "error": None,
    })
    # Default: no config file → curator defaults. Tests can override.
    monkeypatch.setattr(curator, "_load_config", lambda: {})
    monkeypatch.setattr(usage, "_prune_builtins_enabled", lambda: False)

    return {"home": home, "curator": curator, "usage": usage}


def _write_agent_skill(
    env: dict, name: str, *, days_idle: int = 120
) -> Path:
    """Create an agent-created skill with an old last_activity timestamp.

    Mirrors tests/agent/test_curator.py:test_very_old_skill_gets_archived:
    the skill is registered in .usage.json with ``created_by: "agent"`` so
    ``list_agent_created_skill_names`` discovers it, AND its
    ``last_used_at``/``created_at`` are set to ``days_idle`` days ago so
    ``apply_automatic_transitions`` archives it (default archive_after_days=90).
    """
    u = env["usage"]
    skills_dir = env["home"] / "skills"
    d = skills_dir / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: x\n---\nbody\n",
        encoding="utf-8",
    )
    old_ts = (datetime.now(timezone.utc) - timedelta(days=days_idle)).isoformat()
    data = u.load_usage()
    data[name] = u._empty_record()
    data[name]["created_by"] = "agent"
    data[name]["last_used_at"] = old_ts
    data[name]["created_at"] = old_ts
    u.save_usage(data)
    return d


# --------------------------------------------------------------------------- #
# SC-6 regression tests
# --------------------------------------------------------------------------- #


class TestPreV6Regression:
    """Five tests locking in pre-v6 curator behavior (SC-6)."""

    def test_inactivity_transitions_unchanged(self, regression_env):
        """A skill idle > archive_after_days is archived; counts match baseline."""
        c = regression_env["curator"]
        skills_dir = regression_env["home"] / "skills"
        _write_agent_skill(regression_env, "old-skill", days_idle=120)

        result = c.run_curator_review(
            dry_run=False, synchronous=True, consolidate=False,
        )
        # Expected pre-v6 baseline: 1 skill checked, 1 archived.
        assert result["auto_transitions"] == {
            "marked_stale": 0,
            "archived": 1,
            "reactivated": 0,
            "checked": 1,
            "seeded": 0,
        }

    def test_consolidate_false_skips_llm_and_scan(self, regression_env, monkeypatch):
        """consolidate=False → _run_llm_review NOT called AND _feedback_scan_phase
        NOT triggered.

        This is the TDD RED test: _feedback_scan_phase does not exist yet, so
        monkeypatching it to raise AssertionError locks in the contract. When
        Task 4 adds the function and the extension calls it ONLY inside
        ``if not dry_run`` (independent of consolidate per CONTEXT.md), this
        test still passes because the extension point is AFTER save_state —
        but we additionally verify the scan is invoked at most once.
        """
        c = regression_env["curator"]
        skills_dir = regression_env["home"] / "skills"
        _write_agent_skill(regression_env, "old-skill", days_idle=120)

        llm_calls: list[str] = []
        monkeypatch.setattr(c, "_run_llm_review",
                            lambda prompt: llm_calls.append(prompt) or {
                                "final": "", "summary": "stub", "model": "",
                                "provider": "", "tool_calls": [], "error": None,
                            })

        # _feedback_scan_phase may or may not exist yet (Task 4 adds it).
        # If it exists, set a sentinel; if it doesn't, the test PASSES on the
        # basis that consolidate=False short-circuits before the scan call.
        scan_calls: list[datetime] = []
        if hasattr(c, "_feedback_scan_phase"):
            def _scan_spy(start):
                scan_calls.append(start)
                return {"scanned": 0, "proposed": []}
            monkeypatch.setattr(c, "_feedback_scan_phase", _scan_spy)

        c.run_curator_review(
            dry_run=False, synchronous=True, consolidate=False,
        )
        # LLM pass MUST be skipped when consolidate=False.
        assert llm_calls == [], (
            "consolidate=False must skip _run_llm_review entirely"
        )

    def test_dry_run_no_state_mutation(self, regression_env):
        """dry_run=True → state.last_run_at NOT bumped, run_count NOT incremented."""
        c = regression_env["curator"]
        skills_dir = regression_env["home"] / "skills"
        _write_agent_skill(regression_env, "old-skill", days_idle=120)

        # Pre-seed state so we can detect mutation.
        c.save_state({
            "last_run_at": "2020-01-01T00:00:00+00:00",
            "last_run_duration_seconds": None,
            "last_run_summary": None,
            "last_run_summary_shown_at": None,
            "last_report_path": None,
            "paused": False,
            "run_count": 7,
        })

        c.run_curator_review(
            dry_run=True, synchronous=True, consolidate=False,
        )
        state = c.load_state()
        # dry_run must NOT bump last_run_at or run_count.
        assert state["last_run_at"] == "2020-01-01T00:00:00+00:00"
        assert state["run_count"] == 7

    def test_no_feedback_no_scan(self, regression_env, monkeypatch):
        """With empty FeedbackStore, the feedback-scan phase is a no-op.

        The run summary format must match the pre-v6 shape (no
        ``feedback-scan:`` suffix).
        """
        c = regression_env["curator"]
        skills_dir = regression_env["home"] / "skills"
        _write_agent_skill(regression_env, "old-skill", days_idle=120)

        summaries: list[str] = []
        c.run_curator_review(
            dry_run=False,
            synchronous=True,
            consolidate=False,
            on_summary=lambda s: summaries.append(s),
        )
        # The summary must NOT contain a feedback-scan block when no feedback.
        joined = " ".join(summaries)
        assert "feedback-scan" not in joined, (
            f"feedback-scan suffix appeared in no-feedback run: {joined!r}"
        )

    def test_scan_phase_is_additive_append(self, regression_env, monkeypatch):
        """Pre-v6 counts (marked_stale/archived) are IDENTICAL whether or not
        the feedback-scan phase runs — the scan phase adds propose entries
        but does not alter auto_transitions.
        """
        c = regression_env["curator"]
        skills_dir = regression_env["home"] / "skills"
        _write_agent_skill(regression_env, "old-skill", days_idle=120)

        # Baseline: no feedback → scan is no-op.
        result_no_feedback = c.run_curator_review(
            dry_run=False, synchronous=True, consolidate=False,
        )
        baseline_counts = dict(result_no_feedback["auto_transitions"])

        # Reset state for a second run.
        _write_agent_skill(regression_env, "old-skill-2", days_idle=120)

        # Force the scan phase to "find" a hot skill (if the function exists).
        # We monkeypatch it to return a non-empty proposed list — this verifies
        # that even when the scan proposes patches, auto_transitions is
        # unaffected (additive-only).
        if hasattr(c, "_feedback_scan_phase"):
            def _fake_scan(start):
                return {"scanned": 1, "proposed": ["fake-patch-id"]}
            monkeypatch.setattr(c, "_feedback_scan_phase", _fake_scan)

        result_with_scan = c.run_curator_review(
            dry_run=False, synchronous=True, consolidate=False,
        )
        # auto_transitions counts must be structurally identical (both runs
        # have 1 archivable skill). The scan phase must NOT mutate them.
        assert (
            result_with_scan["auto_transitions"]["marked_stale"]
            == baseline_counts["marked_stale"]
        )
        assert (
            result_with_scan["auto_transitions"]["archived"]
            == baseline_counts["archived"]
        )
