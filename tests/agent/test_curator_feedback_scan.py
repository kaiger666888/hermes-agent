"""Curator feedback-scan phase tests (CURATE-01/02/03 — Phase 32 Plan 01).

Covers _scan_for_hot_skills (threshold detection + session diversity),
_feedback_scan_phase (propose + audit wiring, bundled-never-auto, scan
failure isolation), and _compute_confidence (two-signal CURATE-05 gate).

All LLM calls are mocked — no real API calls. Uses the FeedbackStore
fixture pattern from tests/agent/test_feedback_*.py.
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from agent.curator_audit import read_audit, verify_chain
from agent.evolution.queue import PatchRecord, read_queue


# --------------------------------------------------------------------------- #
# Fixture
# --------------------------------------------------------------------------- #


@pytest.fixture
def scan_env(tmp_path, monkeypatch):
    """Isolated HERMES_HOME + freshly reloaded curator + FeedbackStore."""
    home = tmp_path / ".hermes"
    (home / "skills").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))

    import tools.skill_usage as usage
    importlib.reload(usage)
    import agent.curator as curator
    importlib.reload(curator)
    import agent.feedback_store as feedback_store
    importlib.reload(feedback_store)

    # Neutralize the real LLM pass — we only test the scan phase.
    monkeypatch.setattr(curator, "_run_llm_review", lambda prompt: {
        "final": "", "summary": "stub", "model": "", "provider": "",
        "tool_calls": [], "error": None,
    })
    monkeypatch.setattr(curator, "_load_config", lambda: {})
    monkeypatch.setattr(usage, "_prune_builtins_enabled", lambda: False)

    return {
        "home": home, "curator": curator, "usage": usage,
        "feedback_store": feedback_store,
    }


def _make_feedback_record(
    *, skill_id: str, verdict: str, ts: datetime, correction: str = "c",
    source: str = "cli",
):
    """Build a minimal FeedbackRecord for store.record_feedback."""
    import hashlib
    from agent.feedback_schema import FeedbackRecord, OutputSnapshot
    output_text = f"sample output {ts.isoformat()} {correction}"
    return FeedbackRecord(
        skill_id=skill_id,
        expert_id=skill_id,
        source=source,
        verdict=verdict,
        correction=correction,
        output_snapshot=OutputSnapshot(
            sha256=hashlib.sha256(output_text.encode("utf-8")).hexdigest(),
            output_text=output_text,
            prompt="test prompt",
            model="test-model",
            provider="test",
            params={},
            captured_at=ts,
        ),
        ts=ts,
    )


def _seed_feedback(env, skill_id: str, records: list[dict]) -> Any:
    """Write feedback records to a fresh FeedbackStore, return the store."""
    fs = env["feedback_store"]
    home = env["home"]
    store = fs.FeedbackStore(hermes_home=home)
    for spec in records:
        ts = datetime.fromisoformat(spec["ts"])
        rec = _make_feedback_record(
            skill_id=skill_id, verdict=spec["verdict"], ts=ts,
            correction=spec.get("correction", "c"),
        )
        store.record_feedback(rec)
    return store


# --------------------------------------------------------------------------- #
# _scan_for_hot_skills
# --------------------------------------------------------------------------- #


class TestThresholdDetection:
    def test_below_threshold_count_not_hot(self, scan_env):
        c = scan_env["curator"]
        store = _seed_feedback(scan_env, "screenplay", [
            {"verdict": "needs_work", "ts": "2026-06-01T10:00:00+00:00"},
            {"verdict": "needs_work", "ts": "2026-06-01T14:00:00+00:00"},
        ])
        hot = c._scan_for_hot_skills(
            store, threshold_count=3, threshold_sessions=2,
        )
        assert hot == []

    def test_below_threshold_sessions_not_hot(self, scan_env):
        """3 needs_work but all same UTC day → count passes, sessions fails."""
        c = scan_env["curator"]
        store = _seed_feedback(scan_env, "screenplay", [
            {"verdict": "needs_work", "ts": "2026-06-01T10:00:00+00:00"},
            {"verdict": "needs_work", "ts": "2026-06-01T14:00:00+00:00"},
            {"verdict": "needs_work", "ts": "2026-06-01T16:00:00+00:00"},
        ])
        hot = c._scan_for_hot_skills(
            store, threshold_count=3, threshold_sessions=2,
        )
        assert hot == []

    def test_above_threshold_crosses(self, scan_env):
        """3 negative across 2 distinct UTC days → hot."""
        c = scan_env["curator"]
        store = _seed_feedback(scan_env, "screenplay", [
            {"verdict": "needs_work", "ts": "2026-06-01T10:00:00+00:00"},
            {"verdict": "bad", "ts": "2026-06-02T11:00:00+00:00"},
            {"verdict": "needs_work", "ts": "2026-06-03T09:00:00+00:00"},
        ])
        hot = c._scan_for_hot_skills(
            store, threshold_count=3, threshold_sessions=2,
        )
        assert hot == ["screenplay"]

    def test_good_verdicts_excluded(self, scan_env):
        """Good verdicts don't count toward the negative threshold."""
        c = scan_env["curator"]
        store = _seed_feedback(scan_env, "screenplay", [
            {"verdict": "good", "ts": "2026-06-01T10:00:00+00:00"},
            {"verdict": "good", "ts": "2026-06-02T11:00:00+00:00"},
            {"verdict": "good", "ts": "2026-06-03T09:00:00+00:00"},
        ])
        hot = c._scan_for_hot_skills(
            store, threshold_count=3, threshold_sessions=2,
        )
        assert hot == []


# --------------------------------------------------------------------------- #
# _feedback_scan_phase — propose wiring
# --------------------------------------------------------------------------- #


class TestProposeHotBundledSkill:
    def test_propose_invokes_aggregate_emit_generate_append_audit(
        self, scan_env, monkeypatch,
    ):
        """End-to-end: hot skill → aggregate → emit → generate → append_patch +
        append_audit(action='propose'). All LLM calls mocked.
        """
        c = scan_env["curator"]
        store = _seed_feedback(scan_env, "screenplay", [
            {"verdict": "needs_work", "ts": "2026-06-01T10:00:00+00:00"},
            {"verdict": "bad", "ts": "2026-06-02T11:00:00+00:00"},
            {"verdict": "needs_work", "ts": "2026-06-03T09:00:00+00:00"},
        ])

        # Mock the FeedbackStore constructor inside _feedback_scan_phase.
        monkeypatch.setattr(
            c, "_scan_for_hot_skills",
            lambda store_, **kw: ["screenplay"],
        )

        # Mock all lazy imports inside _feedback_scan_phase. The lazy import
        # resolves via `from agent.evolution import X` which binds the symbol
        # from agent.evolution.__init__'s namespace — so we patch the
        # agent.evolution module directly.
        import agent.evolution as evol_pkg
        from agent.evolution.insights import InsightRecord

        fake_insight = InsightRecord(
            insight_id="ins1", skill_id="screenplay", theme="t",
            evidence_chain=["fb1", "fb2", "fb3"], rationale="r",
            proposed_addition="p", insert_after_marker="## X",
            ts="2026-06-24T00:00:00+00:00",
        )
        monkeypatch.setattr(
            evol_pkg, "aggregate_feedback",
            lambda *, skill_id, store, client, model: [fake_insight],
        )
        monkeypatch.setattr(
            evol_pkg, "make_aggregation_client",
            lambda: (object(), "test-model"),
        )
        monkeypatch.setattr(
            evol_pkg, "emit_evol02_instructions",
            lambda *, insight, current_files, client, model: [{
                "file": "skills/movie-experts/screenplay/references/x.md",
                "anchor_section": "## X",
                "add_after": True,
                "content_en": "# EN\nbody",
                "content_zh": "### 中文\n正文",
            }],
        )
        monkeypatch.setattr(
            evol_pkg, "generate_patch_from_knowledge_point",
            lambda *, insight, current_files, instructions: "fake diff content",
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_bundled", lambda name: True,
        )

        # Also mock FeedbackStore init to return our seeded store.
        fs = scan_env["feedback_store"]
        monkeypatch.setattr(
            fs.FeedbackStore, "__init__",
            lambda self, **kw: None,
        )
        monkeypatch.setattr(
            fs.FeedbackStore, "query",
            lambda self, **kw: store.query(**kw),
        )

        result = c._feedback_scan_phase(datetime.now(timezone.utc))
        assert result["scanned"] == 1
        assert len(result["proposed"]) == 1

        # Verify patch landed in the queue.
        from hermes_constants import get_hermes_home
        evolution_dir = get_hermes_home() / "skills" / ".feedback" / "evolution"
        patches = read_queue(evolution_dir=evolution_dir, status="pending")
        assert len(patches) == 1
        assert patches[0].skill_id == "screenplay"
        assert patches[0].status == "pending"
        # Bundled NEVER auto-apply eligible.
        assert patches[0].auto_apply_eligible is False

        # Verify audit entry was logged with action='propose'.
        audit_entries = read_audit(action="propose")
        assert len(audit_entries) == 1
        assert audit_entries[0]["skill_id"] == "screenplay"
        assert audit_entries[0]["action"] == "propose"


# --------------------------------------------------------------------------- #
# CR-03: current_files keys must be repo-relative, not HERMES_HOME-relative
# --------------------------------------------------------------------------- #


class TestCurrentFilesRepoRelativePaths:
    """CR-03 regression: the LLM is told the paths are 'repo-relative',
    so the keys MUST be repo-relative (``skills/movie-experts/...``), not
    HERMES_HOME-relative (``.hermes/skills/movie-experts/...``).

    The generated diff's fromfile/tofile (``a/<key>`` / ``b/<key>``) is
    what apply_patch_transaction resolves against the git repo root.
    HERMES_HOME-relative keys produce diffs that don't apply.
    """

    def test_current_files_keys_are_repo_relative(
        self, scan_env, monkeypatch, tmp_path,
    ):
        """When the repo tree contains the skill, paths passed to the
        LLM (via emit_evol02_instructions) MUST start with
        ``skills/movie-experts/``, not ``.hermes/``.
        """
        c = scan_env["curator"]
        store = _seed_feedback(scan_env, "screenplay", [
            {"verdict": "needs_work", "ts": "2026-06-01T10:00:00+00:00"},
            {"verdict": "bad", "ts": "2026-06-02T11:00:00+00:00"},
            {"verdict": "needs_work", "ts": "2026-06-03T09:00:00+00:00"},
        ])
        monkeypatch.setattr(
            c, "_scan_for_hot_skills",
            lambda store_, **kw: ["screenplay"],
        )

        # Set up a fake repo root with the skill layout.
        fake_repo = tmp_path / "fake-repo"
        skill_repo_dir = fake_repo / "skills" / "movie-experts" / "screenplay"
        skill_repo_dir.mkdir(parents=True)
        (skill_repo_dir / "SKILL.md").write_text(
            "---\nname: screenplay\n---\n## Section\nbody\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            c, "_resolve_repo_root_or_none", lambda: fake_repo,
        )

        # Capture the current_files passed to emit_evol02_instructions.
        captured: dict[str, str] = {}

        def capture_emit(*, insight, current_files, client, model):
            captured.update(current_files)
            return []

        import agent.evolution as evol_pkg
        from agent.evolution.insights import InsightRecord
        fake_insight = InsightRecord(
            insight_id="ins1", skill_id="screenplay", theme="t",
            evidence_chain=["fb1", "fb2", "fb3"], rationale="r",
            proposed_addition="p", insert_after_marker="## X",
            ts="2026-06-24T00:00:00+00:00",
        )
        monkeypatch.setattr(
            evol_pkg, "aggregate_feedback",
            lambda *, skill_id, store, client, model: [fake_insight],
        )
        monkeypatch.setattr(
            evol_pkg, "make_aggregation_client",
            lambda: (object(), "test-model"),
        )
        monkeypatch.setattr(
            evol_pkg, "emit_evol02_instructions", capture_emit,
        )
        monkeypatch.setattr(
            "tools.skill_usage.is_bundled", lambda name: True,
        )

        fs = scan_env["feedback_store"]
        monkeypatch.setattr(fs.FeedbackStore, "__init__", lambda self, **kw: None)
        monkeypatch.setattr(fs.FeedbackStore, "query", lambda self, **kw: [])

        c._feedback_scan_phase(datetime.now(timezone.utc))

        # Path MUST be repo-relative, NOT HERMES_HOME-relative.
        assert captured, "emit_evol02_instructions was not called"
        for key in captured:
            assert key.startswith("skills/movie-experts/"), (
                f"current_files key {key!r} is not repo-relative — "
                f"should start with 'skills/movie-experts/'"
            )
            assert not key.startswith(".hermes"), (
                f"current_files key {key!r} is HERMES_HOME-relative — "
                f"diffs generated against this path would not apply via "
                f"apply_patch_transaction"
            )


# --------------------------------------------------------------------------- #
# Scan failure isolation
# --------------------------------------------------------------------------- #


class TestScanFailureDoesNotAbortCurator:
    def test_scan_phase_raises_curator_still_completes(
        self, scan_env, monkeypatch,
    ):
        """If _feedback_scan_phase raises internally, run_curator_review
        must still complete and return its normal result.
        """
        c = scan_env["curator"]
        # Force the scan phase to raise by making FeedbackStore init fail.
        monkeypatch.setattr(
            c, "_feedback_scan_phase",
            lambda start: (_ for _ in ()).throw(RuntimeError("scan boom")),
        )
        # Create an agent-created skill so the run has something to do.
        u = scan_env["usage"]
        skills_dir = scan_env["home"] / "skills"
        d = skills_dir / "test-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: x\n---\nbody\n",
            encoding="utf-8",
        )
        old_ts = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
        data = u.load_usage()
        data["test-skill"] = u._empty_record()
        data["test-skill"]["created_by"] = "agent"
        data["test-skill"]["last_used_at"] = old_ts
        data["test-skill"]["created_at"] = old_ts
        u.save_usage(data)

        # This must NOT raise despite the scan phase throwing.
        result = c.run_curator_review(
            dry_run=False, synchronous=True, consolidate=False,
        )
        assert "auto_transitions" in result
        # The curator completed the deterministic phase.
        assert result["auto_transitions"]["archived"] == 1


# --------------------------------------------------------------------------- #
# Bundled NEVER auto-apply eligible
# --------------------------------------------------------------------------- #


class TestBundledNeverAutoApplyEligible:
    def test_bundled_patch_always_false(self, scan_env, monkeypatch):
        """Even if confidence passes, bundled patches have auto_apply_eligible=False."""
        c = scan_env["curator"]
        monkeypatch.setattr(
            c, "_scan_for_hot_skills",
            lambda store_, **kw: ["screenplay"],
        )

        from agent.evolution.insights import InsightRecord
        import agent.evolution as evol_pkg

        fake_insight = InsightRecord(
            insight_id="ins1", skill_id="screenplay", theme="t",
            evidence_chain=["fb1", "fb2", "fb3"], rationale="r",
            proposed_addition="p", insert_after_marker="## X",
            ts="2026-06-24T00:00:00+00:00",
        )
        monkeypatch.setattr(
            evol_pkg, "aggregate_feedback",
            lambda *, skill_id, store, client, model: [fake_insight],
        )
        monkeypatch.setattr(
            evol_pkg, "make_aggregation_client",
            lambda: (object(), "test-model"),
        )
        monkeypatch.setattr(
            evol_pkg, "emit_evol02_instructions",
            lambda *, insight, current_files, client, model: [{
                "file": "x.md", "anchor_section": "## X", "add_after": True,
                "content_en": "# EN\nb", "content_zh": "### 中\n正",
            }],
        )
        monkeypatch.setattr(
            evol_pkg, "generate_patch_from_knowledge_point",
            lambda *, insight, current_files, instructions: "fake diff",
        )
        # Screenplay IS bundled.
        monkeypatch.setattr(
            "tools.skill_usage.is_bundled", lambda name: True,
        )

        fs = scan_env["feedback_store"]
        monkeypatch.setattr(fs.FeedbackStore, "__init__", lambda self, **kw: None)
        monkeypatch.setattr(fs.FeedbackStore, "query", lambda self, **kw: [])

        c._feedback_scan_phase(datetime.now(timezone.utc))

        from hermes_constants import get_hermes_home
        evolution_dir = get_hermes_home() / "skills" / ".feedback" / "evolution"
        patches = read_queue(evolution_dir=evolution_dir, status="pending")
        assert len(patches) == 1
        assert patches[0].auto_apply_eligible is False


# --------------------------------------------------------------------------- #
# _compute_confidence
# --------------------------------------------------------------------------- #


class TestComputeConfidence:
    def test_both_signals_pass_eligible(self, scan_env):
        c = scan_env["curator"]
        result = c._compute_confidence(
            eval_score={"mean_delta": 0.15}, evidence_count=5,
            min_delta=0.1, min_evidence=3,
        )
        assert result["eligible"] is True
        assert result["mean_delta"] == 0.15
        assert result["evidence_count"] == 5

    def test_delta_below_threshold_not_eligible(self, scan_env):
        c = scan_env["curator"]
        result = c._compute_confidence(
            eval_score={"mean_delta": 0.05}, evidence_count=5,
            min_delta=0.1, min_evidence=3,
        )
        assert result["eligible"] is False
        assert "mean_delta" in result["reason"]

    def test_evidence_below_threshold_not_eligible(self, scan_env):
        c = scan_env["curator"]
        result = c._compute_confidence(
            eval_score={"mean_delta": 0.15}, evidence_count=2,
            min_delta=0.1, min_evidence=3,
        )
        assert result["eligible"] is False
        assert "evidence_count" in result["reason"]

    def test_missing_mean_delta_treated_as_zero(self, scan_env):
        c = scan_env["curator"]
        result = c._compute_confidence(
            eval_score={}, evidence_count=5,
            min_delta=0.1, min_evidence=3,
        )
        assert result["eligible"] is False
        assert result["mean_delta"] == 0.0


# --------------------------------------------------------------------------- #
# Config getters
# --------------------------------------------------------------------------- #


class TestFeedbackConfigGetters:
    def test_defaults_when_no_config(self, scan_env, monkeypatch):
        c = scan_env["curator"]
        monkeypatch.setattr(c, "_load_feedback_config", lambda: {})
        assert c.get_feedback_threshold_count() == 3
        assert c.get_feedback_threshold_sessions() == 2
        assert c.get_auto_apply_enabled() is False
        assert c.get_auto_apply_min_delta() == 0.1
        assert c.get_auto_apply_min_evidence() == 3

    def test_config_overrides(self, scan_env, monkeypatch):
        c = scan_env["curator"]
        monkeypatch.setattr(c, "_load_feedback_config", lambda: {
            "feedback_threshold_count": 5,
            "feedback_threshold_sessions": 3,
            "auto_apply_enabled": True,
            "auto_apply_min_delta": 0.2,
            "auto_apply_min_evidence": 10,
        })
        assert c.get_feedback_threshold_count() == 5
        assert c.get_feedback_threshold_sessions() == 3
        assert c.get_auto_apply_enabled() is True
        assert c.get_auto_apply_min_delta() == 0.2
        assert c.get_auto_apply_min_evidence() == 10
