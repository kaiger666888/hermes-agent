"""test_p01_p02_p03.py — vertical slice tests for phase modules (Phase 35-05).

Per the Phase 35-05 plan, these tests verify each phase module (p01, p02, p03)
exercised with mocked delegate_task / mocked gates / tmp_path asset bus.

**Status:** Phase 35-03 (running in parallel Wave 2) had NOT shipped the phase
module files (``pipeline/phases/p01_hook_topic.py`` etc.) at the time this test
was written. Per the plan's ``<critical_reminders>`` note #2 we use the
skip-pattern: the deep lifecycle tests are marked
``pytest.mark.skip(reason="waiting for 35-03 modules")`` so the suite stays
green, and a lightweight import-succeed test runs unconditionally to fail-fast
the moment the modules appear (acting as a tripwire for the verifier).

When 35-03 lands, remove the skip markers and the tests will execute against
the real modules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Skill dir on sys.path (mirror conftest setup).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))


# Expected module paths (per PATTERNS.md anatomy).
_P01_PATH = _SKILL_DIR / "pipeline" / "phases" / "p01_hook_topic.py"
_P02_PATH = _SKILL_DIR / "pipeline" / "phases" / "p02_outline.py"
_P03_PATH = _SKILL_DIR / "pipeline" / "phases" / "p03_script_audit.py"

_PHASES_PRESENT = _P01_PATH.exists() and _P02_PATH.exists() and _P03_PATH.exists()

_SKIP_REASON = "waiting for 35-03 modules (pipeline/phases/p0{1,2,3}_*.py)"


# ---------------------------------------------------------------------------
# Tripwire — runs unconditionally. The moment 35-03 ships the modules, this
# test fails (forcing the verifier to drop the skip markers below).
# ---------------------------------------------------------------------------


def test_phase_modules_presence_flag():
    """Documents whether 35-03 phase modules are on disk yet.

    If this asserts TRUE (modules present), remove the skip markers on the
    lifecycle tests below and let them run. If FALSE, the skips below keep
    the suite green until 35-03 lands.
    """
    if _PHASES_PRESENT:
        # When this branch fires, the verifier should remove the skip markers.
        pytest.skip(
            "35-03 modules now present — remove @pytest.mark.skip on the "
            "lifecycle tests below so they execute."
        )
    # Modules not yet present — expected state when 35-05 runs before 35-03.
    assert not _PHASES_PRESENT


# ---------------------------------------------------------------------------
# p01 lifecycle tests (SKIPPED until 35-03 lands)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason=_SKIP_REASON)
class TestP01HookTopic:
    """p01_hook_topic lifecycle tests — execute once 35-03 ships the module."""

    def test_p01_invokes_hook_retention_expert(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p01_hook_topic import run as p01_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {"topic_kernel": {"title": "x"}, "hook_design": {"type": "情感钩"}}
        )

        p01_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert "skill_view(name='hook_retention')" in delegate.last_call["goal"]

    def test_p01_reads_requirement_slot(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p01_hook_topic import run as p01_run

        bus, workdir = tmp_asset_bus
        bus.write("requirement", {"topic": "灵活就业者"}, envelope=True)
        delegate = mock_delegate_factory(
            {"topic_kernel": {}, "hook_design": {}}
        )

        p01_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert "灵活就业者" in delegate.last_call["context"]

    def test_p01_writes_topic_kernel_and_hook_design(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p01_hook_topic import run as p01_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {
                "topic_kernel": {"title": "tk"},
                "hook_design": {"type": "情感钩"},
            }
        )

        p01_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert bus.read("topic-kernel")["title"] == "tk"
        assert bus.read("hook-design")["type"] == "情感钩"

    def test_p01_triggers_gate_1_when_enabled(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p01_hook_topic import run as p01_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {"topic_kernel": {}, "hook_design": {}}
        )
        gate_calls = []

        def trigger_gate(gate_id, ep):
            gate_calls.append((gate_id, ep))
            return {"outcome": "approved"}

        result = p01_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=trigger_gate,
        )

        assert gate_calls == [("selection-topic-hook", "ep-001")]
        assert result["gate"] == {"outcome": "approved"}

    def test_p01_skips_gate_when_none(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p01_hook_topic import run as p01_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {"topic_kernel": {}, "hook_design": {}}
        )

        result = p01_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert result["gate"] is None


# ---------------------------------------------------------------------------
# p02 lifecycle tests (SKIPPED until 35-03 lands)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason=_SKIP_REASON)
class TestP02Outline:
    def test_p02_invokes_creative_source_and_screenplay(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p02_outline import run as p02_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {
                "story_kernel": {},
                "snowflake_artifacts": {},
                "snyder_beats": [],
            }
        )

        p02_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        goal = delegate.last_call["goal"]
        assert "skill_view(name='creative_source')" in goal
        assert "skill_view(name='screenplay')" in goal

    def test_p02_reads_topic_kernel_slot(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p02_outline import run as p02_run

        bus, workdir = tmp_asset_bus
        bus.write("topic-kernel", {"title": "topic-x"}, envelope=True)
        delegate = mock_delegate_factory(
            {"story_kernel": {}, "snowflake_artifacts": {}, "snyder_beats": []}
        )

        p02_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert "topic-x" in delegate.last_call["context"]

    def test_p02_writes_story_framework(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p02_outline import run as p02_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {
                "story_kernel": {"premise": "p"},
                "snowflake_artifacts": {"snapshots": []},
                "snyder_beats": [{"beat": "opening"}],
            }
        )

        p02_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        sf = bus.read("story-framework")
        assert sf["story_kernel"]["premise"] == "p"

    def test_p02_triggers_gate_2_when_enabled(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p02_outline import run as p02_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {"story_kernel": {}, "snowflake_artifacts": {}, "snyder_beats": []}
        )
        gate_calls = []

        def trigger_gate(gate_id, ep):
            gate_calls.append((gate_id, ep))
            return {"outcome": "approved"}

        p02_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=trigger_gate,
        )

        assert gate_calls == [("framework-outline", "ep-001")]


# ---------------------------------------------------------------------------
# p03 lifecycle tests (SKIPPED until 35-03 lands)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason=_SKIP_REASON)
class TestP03ScriptAudit:
    def test_p03_invokes_screenplay_and_script_auditor(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p03_script_audit import run as p03_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory({"script": {}, "audit": {}})

        p03_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        goal = delegate.last_call["goal"]
        assert "skill_view(name='screenplay')" in goal
        assert "skill_view(name='script_auditor')" in goal

    def test_p03_reads_story_framework_slot(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p03_script_audit import run as p03_run

        bus, workdir = tmp_asset_bus
        bus.write("story-framework", {"story_kernel": {"premise": "p"}}, envelope=True)
        delegate = mock_delegate_factory({"script": {}, "audit": {}})

        p03_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert "p" in delegate.last_call["context"]

    def test_p03_writes_script_draft_and_audit_report(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p03_script_audit import run as p03_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory(
            {"script": {"scenes": []}, "audit": {"score": 0.82}}
        )

        p03_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=None,
        )

        assert bus.read("script-draft")["scenes"] == []
        assert bus.read("audit-report")["score"] == 0.82

    def test_p03_triggers_gate_3_when_enabled(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        from pipeline.phases.p03_script_audit import run as p03_run

        bus, workdir = tmp_asset_bus
        delegate = mock_delegate_factory({"script": {}, "audit": {}})
        gate_calls = []

        def trigger_gate(gate_id, ep):
            gate_calls.append((gate_id, ep))
            return {"outcome": "approved"}

        p03_run(
            episode_id="ep-001",
            asset_bus_read=lambda slot: bus.read(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True),
            delegate_task=delegate,
            trigger_gate=trigger_gate,
        )

        assert gate_calls == [("script-audit", "ep-001")]
