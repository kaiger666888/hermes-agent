"""Tests for ``agent/memory_arbitration.py`` (Phase 53 CREATIVE-02).

Replaces Phase 52 STUB behavior with the full 5-mechanism conflict
arbitration runtime per ``02-ROUND-TABLE-PROTOCOL.md §3``:

1. Memory annotation enrichment (via ``memory_retrieve_scoped`` routing)
2. Comparator LLM pass (verbatim §3.2 ``COMPARATOR_PROMPT_TEMPLATE``)
3. Scope precedence (``session > project > global``)
4. Confidence-weighted voting (Δconfidence < 0.05 → deferred-to-operator)
5. Conflict log JSONL writer

The Phase 52 ``_scoped_agent_id`` ``contextvars.ContextVar`` primitive
MUST remain unchanged — Test 8 verifies that contract.

TDD: This file is RED until Task 1 lands ``arbitrate_two_memories`` /
``apply_tie_break`` / ``append_conflict_record`` /
``COMPARATOR_PROMPT_TEMPLATE`` in ``agent/memory_arbitration.py``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def memory_module():
    """Lazy-import so RED phase collects cleanly before implementation lands."""
    from agent import memory_arbitration
    return memory_arbitration


@pytest.fixture
def fixture_data():
    """Load the 2-conflict scenario fixture."""
    p = Path(__file__).parent.parent / "fixtures" / "memory-conflict-2conflict.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _make_llm_response(content: str):
    """Build a synthetic call_llm response object."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


# ── Test 1: COMPARATOR_PROMPT_TEMPLATE verbatim substrings ─────────────────


class TestComparatorPromptTemplate:
    def test_comparator_prompt_template_verbatim(self, memory_module):
        """The prompt template must contain the §3.2 verbatim substrings."""
        template = memory_module.COMPARATOR_PROMPT_TEMPLATE
        # Opening line verbatim per §3.2 line 628
        assert "You are arbitrating a memory conflict in a Hermes round table." in template
        # Scope-precedence rule per §3.2 line 646
        assert "Apply scope precedence: session > project > global" in template
        # Δconfidence threshold per §3.2 line 651-652
        assert "confidence within 0.05" in template
        # evidence_operator_ids field per §3.2 line 637
        assert "evidence_operator_ids" in template
        # 5-value enum per §3.2 line 659
        assert '"resolution": "A-wins" | "B-wins" | "both-kept" | "both-quarantined" | "deferred-to-operator"' in template


# ── Test 2: arbitrate_two_memories with session-over-global ────────────────


class TestArbitrateTwoMemories:
    def test_arbitrate_two_memories_session_over_global(self, memory_module):
        """LLM-driven arbitration with session vs global; well-behaved LLM returns A-wins."""
        spy = MagicMock(return_value=_make_llm_response(
            '{"resolution": "A-wins", "rationale": "session scope overrides global per rule", "confidence": 0.9}'
        ))
        memory_a = {
            "scope": "session",
            "confidence": 0.7,
            "content": "session-scoped memory content",
            "evidence_chain": [1, 2],
            "evidence_operator_ids": ["kai"],
        }
        memory_b = {
            "scope": "global",
            "confidence": 0.95,
            "content": "global-scoped memory content",
            "evidence_chain": [1],
            "evidence_operator_ids": ["data"],
        }
        result = memory_module.arbitrate_two_memories(
            memory_a, memory_b,
            panelist_a="screenplay", panelist_b="theory_critic",
            project_id="proj-x", question="which ending?",
            comparator_llm=spy,
        )
        assert spy.call_count == 1
        # The comparator was called once with the formatted prompt
        call_kwargs = spy.call_args.kwargs
        assert "messages" in call_kwargs
        # Result is LLM-driven (A-wins, with deterministic tie-break passing through
        # because scopes differ)
        assert result["resolution"] == "A-wins"

    def test_call_llm_uses_memory_comparator_task(self, memory_module):
        """The default comparator_llm wrapper calls call_llm with task=memory_comparator,
        temperature=0.0, max_tokens=200, provider=glm."""
        # Use the default (no injection); capture via monkeypatch on auxiliary_client
        import agent.auxiliary_client as aux
        original = aux.call_llm
        captured = {}

        def fake_call_llm(task=None, *, provider=None, messages=None,
                          temperature=None, max_tokens=None, **kw):
            captured["task"] = task
            captured["provider"] = provider
            captured["temperature"] = temperature
            captured["max_tokens"] = max_tokens
            captured["messages"] = messages
            return _make_llm_response(
                '{"resolution": "both-kept", "rationale": "test", "confidence": 0.5}'
            )

        aux.call_llm = fake_call_llm
        try:
            memory_module.arbitrate_two_memories(
                {"scope": "session", "confidence": 0.8, "content": "a",
                 "evidence_chain": [], "evidence_operator_ids": []},
                {"scope": "global", "confidence": 0.5, "content": "b",
                 "evidence_chain": [], "evidence_operator_ids": []},
                panelist_a="A", panelist_b="B",
                project_id="p", question="q?",
            )
        finally:
            aux.call_llm = original

        assert captured["task"] == "memory_comparator"
        assert captured["provider"] == "glm"
        assert captured["temperature"] == 0.0
        assert captured["max_tokens"] == 200
        assert isinstance(captured["messages"], list)
        assert captured["messages"][0]["role"] == "user"

    def test_arbitrate_handles_malformed_llm_json(self, memory_module):
        """When the comparator returns non-JSON text, never raise — fall back to deferred."""
        spy = MagicMock(return_value=_make_llm_response(
            "I think A wins because it has better evidence..."
        ))
        result = memory_module.arbitrate_two_memories(
            {"scope": "session", "confidence": 0.9, "content": "a",
             "evidence_chain": [1], "evidence_operator_ids": ["kai"]},
            {"scope": "global", "confidence": 0.4, "content": "b",
             "evidence_chain": [], "evidence_operator_ids": []},
            panelist_a="A", panelist_b="B",
            project_id="p", question="q?",
            comparator_llm=spy,
        )
        assert result["resolution"] == "deferred-to-operator"
        assert "malformed JSON" in result["rationale"]
        assert result["confidence"] == 0.0


# ── Test 3, 4: apply_tie_break ─────────────────────────────────────────────


class TestApplyTieBreak:
    def test_apply_tie_break_forces_deferral(self, memory_module):
        """At the same scope with Δconfidence < 0.05 → deferred-to-operator."""
        memory_a = {"scope": "project", "confidence": 0.95}
        memory_b = {"scope": "project", "confidence": 0.92}
        llm_resolution = {"resolution": "A-wins", "rationale": "LLM says A",
                          "confidence": 0.85}
        out = memory_module.apply_tie_break(memory_a, memory_b, llm_resolution)
        assert out["resolution"] == "deferred-to-operator"
        assert "Δconfidence" in out["rationale"]
        assert "< 0.05" in out["rationale"]

    def test_apply_tie_break_no_tie_passes_through(self, memory_module):
        """Same scope but Δconfidence ≥ 0.05 → LLM resolution preserved."""
        memory_a = {"scope": "project", "confidence": 0.95}
        memory_b = {"scope": "project", "confidence": 0.65}
        llm_resolution = {"resolution": "A-wins", "rationale": "A wins clearly",
                          "confidence": 0.9}
        out = memory_module.apply_tie_break(memory_a, memory_b, llm_resolution)
        assert out == llm_resolution


# ── Test 6: 2-conflict scenario end-to-end ─────────────────────────────────


class TestTwoConflictScenario:
    def test_2conflict_scenario_end_to_end(self, memory_module, fixture_data, tmp_path):
        """Both scenario pairs arbitrate + write to a temp JSONL cleanly."""
        jsonl = tmp_path / "x" / "round-abc" / "conflicts.jsonl"

        for scenario in fixture_data["scenarios"]:
            # Mock LLM: scenario 1 returns A-wins; scenario 2 returns A-wins
            # (the tie-break should force deferral for scenario 2).
            llm_resp = '{"resolution": "A-wins", "rationale": "test rationale", "confidence": 0.85}'
            spy = MagicMock(return_value=_make_llm_response(llm_resp))
            result = memory_module.arbitrate_two_memories(
                scenario["memory_a"], scenario["memory_b"],
                panelist_a=scenario["panelist_a"],
                panelist_b=scenario["panelist_b"],
                project_id="volvo-2026",
                question=scenario["question"],
                comparator_llm=spy,
            )
            assert result["resolution"] == scenario["expected_resolution"], (
                f"scenario={scenario['name']}: expected {scenario['expected_resolution']}, "
                f"got {result['resolution']}"
            )
            # Append the conflict record
            record = {
                "scenario": scenario["name"],
                "resolution": result["resolution"],
                "rationale": result["rationale"],
                "confidence": result["confidence"],
            }
            memory_module.append_conflict_record(jsonl, record)

        # Verify both lines parse
        assert jsonl.exists()
        lines = jsonl.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        for ln in lines:
            parsed = json.loads(ln)
            assert "resolution" in parsed


# ── Test 8: Phase 52 primitive unchanged ───────────────────────────────────


class TestPhase52Primitive:
    def test_phase52_scoped_agent_id_primitive_unchanged(self, memory_module):
        """The _scoped_agent_id ContextVar + set/get helpers must remain verbatim."""
        # Initially None (either unset or explicitly None)
        assert memory_module.get_scoped_agent_id() is None
        memory_module.set_scoped_agent_id("agent_x")
        assert memory_module.get_scoped_agent_id() == "agent_x"
        memory_module.set_scoped_agent_id(None)
        assert memory_module.get_scoped_agent_id() is None
        # Primitive symbols exist
        assert hasattr(memory_module, "_SCOPED_AGENT_ID")
        assert hasattr(memory_module, "_UNSET")
