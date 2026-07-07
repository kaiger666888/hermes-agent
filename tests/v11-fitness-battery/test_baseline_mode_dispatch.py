"""Phase 60 EVAL-02 — real-mode dispatch tests for ``agent.fitness_battery``.

Verifies the two new dispatch paths introduced by plan 60-02 Task 1:

  - ``baseline_mode="persona_aligned"``: dispatches via
    ``auxiliary_client.call_llm`` WITH the screenplay persona system
    prompt prepended.
  - ``baseline_mode="generic_llm"``: dispatches via
    ``auxiliary_client.call_llm`` with NO system prompt (raw user
    message only).

All tests are hermetic — ``monkeypatch.setattr(fitness_battery,
"_call_llm", stub)`` ensures no real GLM call is made in CI.

Per plan 60-02 Task 1 done criteria:
  - ``_dispatch_agent`` accepts ``baseline_mode`` kwarg
  - Both modes invoke ``call_llm`` with the documented message shape
  - ``run_battery`` threads ``baseline_mode`` to every dispatch call
  - At least 4 tests (we have 6 — covering the helper branches too)
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Stub helpers — mirror the OpenAI SDK response shape used elsewhere
# --------------------------------------------------------------------------- #
def _stub_response(content: str = "stub agent output"):
    msg = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=msg)
    return types.SimpleNamespace(choices=[choice])


def _recording_stub(record: dict):
    """Build a stub that records the ``messages`` kwarg into ``record``."""

    def _stub(**kwargs):
        record["messages"] = kwargs.get("messages")
        record["kwargs"] = kwargs
        return _stub_response()

    return _stub


# --------------------------------------------------------------------------- #
# Test 1: persona_aligned dispatch prepends system prompt
# --------------------------------------------------------------------------- #
class TestPersonaAlignedDispatch:
    def test_persona_aligned_calls_auxiliary_client(
        self, scenarios_dir: Path, monkeypatch
    ):
        """baseline_mode='persona_aligned' must invoke _call_llm."""
        from agent import fitness_battery

        record: dict = {}
        monkeypatch.setattr(fitness_battery, "_call_llm", _recording_stub(record))
        # Force a known persona so the test is hermetic.
        monkeypatch.setattr(
            fitness_battery,
            "_load_persona_system_prompt",
            lambda name: "PERSONA-BLOCK-TEST",
        )

        scenario = fitness_battery.load_scenario(
            "screenplay-step3-hook09", battery_dir=scenarios_dir
        )
        result = fitness_battery._dispatch_agent(
            scenario, baseline_mode="persona_aligned"
        )
        assert result == "stub agent output"
        assert "messages" in record
        messages = record["messages"]
        # Persona-aligned mode MUST prepend a system message.
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "PERSONA-BLOCK-TEST"
        # User message must follow the system message.
        assert messages[-1]["role"] == "user"
        assert isinstance(messages[-1]["content"], str)
        assert messages[-1]["content"]  # non-empty

    def test_persona_aligned_records_glm_provider(self, scenarios_dir, monkeypatch):
        """All dispatch must pass provider='glm' (MEMORY.md GLM-only rule)."""
        from agent import fitness_battery

        record: dict = {}
        monkeypatch.setattr(fitness_battery, "_call_llm", _recording_stub(record))
        monkeypatch.setattr(
            fitness_battery,
            "_load_persona_system_prompt",
            lambda name: "P",
        )
        scenario = fitness_battery.load_scenario(
            "persona-drift-probe", battery_dir=scenarios_dir
        )
        fitness_battery._dispatch_agent(scenario, baseline_mode="persona_aligned")
        assert record["kwargs"]["provider"] == "glm"
        assert record["kwargs"]["task"] == "fitness_battery_agent"


# --------------------------------------------------------------------------- #
# Test 2: generic_llm dispatch omits system prompt
# --------------------------------------------------------------------------- #
class TestGenericLlmDispatch:
    def test_generic_llm_has_no_system_prompt(self, scenarios_dir, monkeypatch):
        """generic_llm mode MUST NOT include a system message."""
        from agent import fitness_battery

        record: dict = {}
        monkeypatch.setattr(fitness_battery, "_call_llm", _recording_stub(record))

        scenario = fitness_battery.load_scenario(
            "screenplay-step3-snyder-beat", battery_dir=scenarios_dir
        )
        fitness_battery._dispatch_agent(scenario, baseline_mode="generic_llm")
        messages = record["messages"]
        assert isinstance(messages, list)
        # CRITICAL: no system message at all.
        assert all(m["role"] != "system" for m in messages), (
            f"generic_llm mode leaked a system message: {messages!r}"
        )
        # Exactly one user message.
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert isinstance(user_msgs[0]["content"], str)
        assert user_msgs[0]["content"]

    def test_generic_llm_returns_content_string(self, scenarios_dir, monkeypatch):
        """Return value must be the raw content string, not a JSON stub."""
        from agent import fitness_battery

        monkeypatch.setattr(
            fitness_battery,
            "_call_llm",
            lambda **kw: _stub_response(content="RAW GLM OUTPUT"),
        )
        scenario = fitness_battery.load_scenario(
            "persona-drift-probe", battery_dir=scenarios_dir
        )
        result = fitness_battery._dispatch_agent(
            scenario, baseline_mode="generic_llm"
        )
        assert result == "RAW GLM OUTPUT"
        # Must NOT be a JSON-encoded stub like {"stub": true, ...}
        try:
            decoded = json.loads(result)
            assert not isinstance(decoded, dict) or "stub" not in decoded, (
                "generic_llm returned a stub dict — real-mode dispatch broken"
            )
        except json.JSONDecodeError:
            pass  # raw text content is the expected shape

    def test_generic_llm_dispatch_failure_returns_error_stub(
        self, scenarios_dir, monkeypatch
    ):
        """Dispatch failure must NOT crash the battery — returns error JSON."""
        from agent import fitness_battery

        def failing_call(**kwargs):
            raise RuntimeError("simulated aux pool exhaustion")

        monkeypatch.setattr(fitness_battery, "_call_llm", failing_call)
        scenario = fitness_battery.load_scenario(
            "hook09-emotion-curve-marker", battery_dir=scenarios_dir
        )
        result = fitness_battery._dispatch_agent(
            scenario, baseline_mode="generic_llm"
        )
        # Must return a JSON stub with an error marker so scoring continues.
        decoded = json.loads(result)
        assert "real_mode_error" in decoded
        assert decoded["scenario_id"] == "hook09-emotion-curve-marker"
        assert decoded["baseline_mode"] == "generic_llm"


# --------------------------------------------------------------------------- #
# Test 3: run_battery threads baseline_mode to every dispatch call
# --------------------------------------------------------------------------- #
class TestRunBatteryThreading:
    def test_run_battery_threads_baseline_mode(
        self, scenarios_dir, monkeypatch, tmp_path
    ):
        """run_battery must forward baseline_mode to _dispatch_agent."""
        from agent import fitness_battery

        seen_modes: list[str | None] = []
        original_dispatch = fitness_battery._dispatch_agent

        def spy_dispatch(scenario, **kwargs):
            seen_modes.append(kwargs.get("baseline_mode"))
            # Force a deterministic agent output so scoring proceeds.
            return "STUB OUTPUT FOR BASELINE THREAD TEST"

        monkeypatch.setattr(fitness_battery, "_dispatch_agent", spy_dispatch)

        # Use a stub judge so no real GLM judge call happens.
        def fake_judge(**kwargs):
            content = json.dumps(
                {"scores": [{"criterion": "x", "score": 0.5}], "overall": 0.5}
            )
            return _stub_response(content=content)

        summary = fitness_battery.run_battery(
            battery_dir=scenarios_dir,
            judge_llm=fake_judge,
            persona_sha256="baseline-thread-test",
            baseline_mode="generic_llm",
        )
        # Every scenario must have seen baseline_mode='generic_llm'.
        assert len(seen_modes) == summary["scenarios_run"]
        assert all(mode == "generic_llm" for mode in seen_modes), (
            f"run_battery failed to thread baseline_mode; saw: {seen_modes!r}"
        )
        # Summary must echo the mode for downstream filtering.
        assert summary["baseline_mode"] == "generic_llm"

    def test_run_battery_default_baseline_mode_is_none(
        self, scenarios_dir, monkeypatch
    ):
        """Default baseline_mode MUST be None (Phase 54 behavior preserved)."""
        from agent import fitness_battery

        seen_modes: list[str | None] = []
        monkeypatch.setattr(
            fitness_battery,
            "_dispatch_agent",
            lambda scenario, **kw: (
                seen_modes.append(kw.get("baseline_mode")),
                "STUB",
            )[1],
        )

        def fake_judge(**kwargs):
            content = json.dumps(
                {"scores": [{"criterion": "x", "score": 0.5}], "overall": 0.5}
            )
            return _stub_response(content=content)

        summary = fitness_battery.run_battery(
            battery_dir=scenarios_dir,
            judge_llm=fake_judge,
            persona_sha256="phase54-compat",
        )
        assert all(mode is None for mode in seen_modes)
        assert summary["baseline_mode"] is None


# --------------------------------------------------------------------------- #
# Test 4: _extract_user_message covers all scenario shapes
# --------------------------------------------------------------------------- #
class TestExtractUserMessage:
    def test_prompt_key_used_for_persona_drift(self, scenarios_dir):
        from agent import fitness_battery

        scenario = fitness_battery.load_scenario(
            "persona-drift-probe", battery_dir=scenarios_dir
        )
        msg = fitness_battery._extract_user_message(scenario)
        assert "twist" in msg.lower()  # persona-drift prompt mentions twist

    def test_storykernel_dict_for_screenplay(self, scenarios_dir):
        from agent import fitness_battery

        scenario = fitness_battery.load_scenario(
            "screenplay-step3-hook09", battery_dir=scenarios_dir
        )
        msg = fitness_battery._extract_user_message(scenario)
        # JSON-stringified input — should include the storykernel title.
        assert "storykernel" in msg or "The Last Delivery" in msg

    def test_question_key_for_conflict_resolution(self, scenarios_dir):
        from agent import fitness_battery

        scenario = fitness_battery.load_scenario(
            "conflict-resolution-2party", battery_dir=scenarios_dir
        )
        msg = fitness_battery._extract_user_message(scenario)
        assert "ending" in msg.lower() or "question" in msg.lower()


# --------------------------------------------------------------------------- #
# Test 5: BATTERY_VERSION distinguishes real-mode runs
# --------------------------------------------------------------------------- #
class TestBatteryVersion:
    def test_battery_version_carries_real_suffix(self):
        """BATTERY_VERSION must distinguish real-mode from shadow runs."""
        from agent import fitness_battery

        assert fitness_battery.BATTERY_VERSION == "v1-screenplay-baseline-real", (
            f"BATTERY_VERSION must be 'v1-screenplay-baseline-real' for "
            f"Phase 60; got {fitness_battery.BATTERY_VERSION!r}"
        )
