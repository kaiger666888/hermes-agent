"""test_p01_p02_p03.py — vertical slice lifecycle tests for phase modules (Phase 35-05).

Per the Phase 35-05 plan, these tests verify each phase module (p01, p02, p03)
exercised end-to-end with mocked delegate_task / mocked gates / tmp_path asset
bus (per CONTEXT D-35-08 — no real subagents, no real network, no real GPU).

**Status update (Phase 35-05 execution):** 35-03 has shipped the phase modules,
so the ``@pytest.mark.skip`` markers from the earlier pre-35-03 stub are
REMOVED. All 13 tests now execute against the real modules. The lifecycle
under test is exactly the contract p01/p02/p03 expose to ``runner.py``:

    read asset-bus slot  ->  delegate_task(goal, context, toolsets)
                           ->  parse fenced JSON from summary
                           ->  write asset-bus slot(s)
                           ->  trigger gate (if configured & callable)

Each test asserts ONE specific aspect of that contract (single-responsibility
test design). Shared fixtures come from conftest.py.
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


# ---------------------------------------------------------------------------
# p01_hook_topic lifecycle tests (V8.6 §1: hook + topic atomic)
# ---------------------------------------------------------------------------


class TestP01HookTopic:
    """p01_hook_topic lifecycle tests.

    Contract (per pipeline/phases/p01_hook_topic.py):
      - READ ``requirement`` slot
      - DELEGATE to hook_retention expert (single delegate_task call)
      - WRITE ``topic-kernel`` + ``hook-design`` slots
      - GATE 1 ``selection-topic-hook`` when trigger_gate provided
    """

    def test_p01_invokes_hook_retention_expert(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        """Goal embeds skill_view(name='hook_retention') so the subagent
        loads the expert before applying it."""
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
        """The requirement slot's content reaches the delegate context."""
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
        """Expert payload is split into the two output slots."""
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
        """When trigger_gate is callable, Gate 1 fires with the right id."""
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
        """trigger_gate=None → no gate fires and result['gate'] is None."""
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
# p02_outline lifecycle tests (V8.6 §2: story framework + outline atomic)
# ---------------------------------------------------------------------------


class TestP02Outline:
    """p02_outline lifecycle tests.

    Contract (per pipeline/phases/p02_outline.py):
      - READ ``topic-kernel`` slot (p01's output)
      - DELEGATE to creative_source + screenplay in a SINGLE delegate_task
        (V8.6 §2 atomic — subagent orchestrates the collaboration)
      - WRITE ``story-framework`` slot (StoryKernel + snowflake + snyder beats)
      - GATE 2 ``story-framework-outline`` when trigger_gate provided
    """

    def test_p02_invokes_creative_source_and_screenplay(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        """Goal mentions BOTH experts' skill_view calls (single delegate_task)."""
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
        """The topic-kernel slot's content reaches the delegate context."""
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
        """The full expert payload (story_kernel + snowflake + snyder) is
        written as ONE cohesive story-framework slot."""
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
        assert sf["snowflake_artifacts"] == {"snapshots": []}
        assert sf["snyder_beats"] == [{"beat": "opening"}]

    def test_p02_triggers_gate_2_when_enabled(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        """Gate 2 fires with the canonical id 'story-framework-outline'."""
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

        # Gate id matches p02_outline.GATE_ID — 'story-framework-outline'
        # (NOT the shorter 'framework-outline'; canonical id is in the module).
        assert gate_calls == [("story-framework-outline", "ep-001")]


# ---------------------------------------------------------------------------
# p03_script_audit lifecycle tests (V8.6 §3: script + audit atomic loop)
# ---------------------------------------------------------------------------


class TestP03ScriptAudit:
    """p03_script_audit lifecycle tests.

    Contract (per pipeline/phases/p03_script_audit.py):
      - READ ``story-framework`` slot (p02's output)
      - DELEGATE to screenplay + script_auditor in a SINGLE delegate_task
        (V8.6 §3 atomic revise loop — subagent runs write-audit-revise)
      - WRITE ``script-draft`` + ``audit-report`` slots
      - GATE 3 ``script-audit`` when trigger_gate provided
    """

    def test_p03_invokes_screenplay_and_script_auditor(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        """Goal mentions BOTH experts' skill_view calls."""
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
        """The story-framework slot's content reaches the delegate context."""
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
        """Expert payload splits into separate script-draft + audit-report slots."""
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
        """Gate 3 fires with the canonical id 'script-audit'."""
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
