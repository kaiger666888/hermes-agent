"""Unit tests for ``agent.fitness_battery`` (EVAL-01 fitness battery runner).

Tests are hermetic: ``monkeypatch`` stubs the LLM judge so NO real
GLM call is made. A separate ``@pytest.mark.human_needed`` smoke test
(invoked manually) calls real GLM.

All five behavior contracts from plan 54-01 Task 2 are covered:

1. ``load_scenario`` returns dict with 5 required keys.
2. ``run_battery`` returns summary with mean_score + 8 scenarios_run.
3. Determinism: same fake_judge → same mean_score.
4. CLI writes ``fitness_trend.jsonl`` entry with persona_sha256 + model_id.
5. ``score_scenario`` weights criteria by ``scoring_rubric[].weight``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Test 1: load_scenario
# --------------------------------------------------------------------------- #
class TestLoadScenario:
    def test_returns_dict_with_required_keys(self, scenarios_dir: Path):
        from agent.fitness_battery import load_scenario

        scenario = load_scenario("screenplay-step3-hook09", battery_dir=scenarios_dir)
        assert isinstance(scenario, dict)
        required = {"id", "description", "input", "expected_output", "scoring_rubric"}
        assert set(scenario.keys()) == required

    def test_raises_on_missing_scenario(self, scenarios_dir: Path):
        from agent.fitness_battery import load_scenario

        with pytest.raises(FileNotFoundError):
            load_scenario("does-not-exist-xyz", battery_dir=scenarios_dir)


# --------------------------------------------------------------------------- #
# Test 2: run_battery summary shape
# --------------------------------------------------------------------------- #
class TestRunBattery:
    def test_summary_has_eight_scenarios(
        self, scenarios_dir: Path, fake_judge_high, monkeypatch
    ):
        from agent import fitness_battery

        # Stub agent dispatch — every scenario returns a fixed stub output.
        monkeypatch.setattr(
            fitness_battery,
            "_dispatch_agent",
            lambda scenario, **kw: "STUB OUTPUT",
        )
        summary = fitness_battery.run_battery(
            battery_dir=scenarios_dir,
            judge_llm=fake_judge_high,
            persona_sha256="test-sha256",
        )
        assert summary["scenarios_run"] == 8
        assert "mean_score" in summary
        assert isinstance(summary["mean_score"], float)
        assert isinstance(summary["per_prompt_scores"], dict)
        assert len(summary["per_prompt_scores"]) == 8


# --------------------------------------------------------------------------- #
# Test 3: determinism under fixed fake_judge
# --------------------------------------------------------------------------- #
class TestDeterminism:
    def test_fixed_judge_yields_known_mean(self, scenarios_dir: Path, fake_judge_high, monkeypatch):
        from agent import fitness_battery

        monkeypatch.setattr(
            fitness_battery,
            "_dispatch_agent",
            lambda scenario, **kw: "STUB OUTPUT",
        )
        summary = fitness_battery.run_battery(
            battery_dir=scenarios_dir,
            judge_llm=fake_judge_high,
            persona_sha256="test-sha256",
        )
        # fake_judge_high always returns 0.8 overall; weighted sum stays 0.8.
        assert summary["mean_score"] == pytest.approx(0.8, abs=1e-6)


# --------------------------------------------------------------------------- #
# Test 5: score_scenario weighting
# --------------------------------------------------------------------------- #
class TestScoreScenario:
    def test_weights_criteria(self, fake_judge_high):
        from agent.fitness_battery import score_scenario

        scenario = {
            "id": "test-weight",
            "description": "weight probe",
            "input": {},
            "expected_output": {"feature": "f", "rationale": "r"},
            "scoring_rubric": [
                {"criterion": "a", "weight": 0.25},
                {"criterion": "b", "weight": 0.75},
            ],
        }
        score = score_scenario(scenario, "agent output", judge_llm=fake_judge_high)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # fake_judge_high returns overall=0.8 for every criterion → 0.8.
        assert score == pytest.approx(0.8, abs=1e-6)


# --------------------------------------------------------------------------- #
# Test 4: CLI writes fitness_trend.jsonl
# --------------------------------------------------------------------------- #
class TestCli:
    def test_cli_writes_trend_entry(
        self, scenarios_dir: Path, hermes_home_tmp: Path, monkeypatch
    ):
        # Stub _dispatch_agent + auxiliary_client.call_llm so the CLI never
        # hits real GLM.
        from agent import fitness_battery

        monkeypatch.setattr(
            fitness_battery,
            "_dispatch_agent",
            lambda scenario, **kw: "STUB OUTPUT",
        )

        def fake_judge(**kwargs):
            import types
            content = json.dumps({"scores": [{"criterion": "stub", "score": 0.7}], "overall": 0.7})
            msg = types.SimpleNamespace(content=content)
            choice = types.SimpleNamespace(message=msg)
            return types.SimpleNamespace(choices=[choice])

        monkeypatch.setattr(fitness_battery, "_default_judge_llm", fake_judge)

        cli_path = REPO_ROOT / "scripts" / "run_fitness_battery.py"
        result = subprocess.run(
            [
                sys.executable,
                str(cli_path),
                "--battery",
                str(scenarios_dir),
                "--persona-sha256",
                "test-sha256-abc",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, f"CLI failed:\nstdout={result.stdout}\nstderr={result.stderr}"

        trend_path = hermes_home_tmp / "eval" / "fitness_trend.jsonl"
        assert trend_path.exists(), f"fitness_trend.jsonl missing at {trend_path}"
        line = trend_path.read_text(encoding="utf-8").strip().split("\n")[-1]
        entry = json.loads(line)
        assert entry["persona_sha256"] == "test-sha256-abc"
        assert entry["model_id"] == "glm-5.2"
        assert entry["provider"] == "zai"
        assert "mean_score" in entry
        assert isinstance(entry["per_prompt_scores"], dict)
        assert len(entry["per_prompt_scores"]) == 8
        # stdout should print a mean_score line for the verification grep
        assert "mean_score" in result.stdout


# --------------------------------------------------------------------------- #
# GLM-only enforcement: every call_llm passes provider="glm"
# --------------------------------------------------------------------------- #
class TestGlmOnly:
    def test_score_scenario_dispatches_via_glm(self, monkeypatch):
        from agent import fitness_battery

        captured = {}

        def spy_call_llm(**kwargs):
            captured.update(kwargs)
            import types
            content = json.dumps({"scores": [{"criterion": "x", "score": 0.5}], "overall": 0.5})
            msg = types.SimpleNamespace(content=content)
            choice = types.SimpleNamespace(message=msg)
            return types.SimpleNamespace(choices=[choice])

        # Patch the symbol the runner module reads at call-time.
        monkeypatch.setattr(fitness_battery, "_call_llm", spy_call_llm)

        scenario = {
            "id": "glm-probe",
            "description": "glm enforcement",
            "input": {},
            "expected_output": {"feature": "f", "rationale": "r"},
            "scoring_rubric": [{"criterion": "x", "weight": 1.0}],
        }
        fitness_battery.score_scenario(scenario, "agent output")
        assert captured.get("provider") == "glm"
        assert captured.get("task") == "fitness_judge"


# --------------------------------------------------------------------------- #
# Trend-entry append (direct unit test)
# --------------------------------------------------------------------------- #
class TestAppendTrendEntry:
    def test_appends_jsonl_line(self, tmp_path: Path):
        from agent.fitness_battery import append_trend_entry

        trend = tmp_path / "fitness_trend.jsonl"
        entry_a = {"ts": "2026-07-07T00:00:00Z", "battery_version": "v1", "mean_score": 0.7}
        entry_b = {"ts": "2026-07-08T00:00:00Z", "battery_version": "v1", "mean_score": 0.8}
        append_trend_entry(entry_a, trend)
        append_trend_entry(entry_b, trend)
        lines = trend.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["mean_score"] == 0.7
        assert json.loads(lines[1])["mean_score"] == 0.8


# --------------------------------------------------------------------------- #
# Malformed judge fallback (T-54-03 mitigation)
# --------------------------------------------------------------------------- #
class TestMalformedJudgeFallback:
    def test_malformed_response_returns_zero(self, monkeypatch):
        from agent import fitness_battery

        def malformed_judge(**kwargs):
            import types
            # Garbage content — not JSON-parseable
            msg = types.SimpleNamespace(content="this is not json {{{")
            choice = types.SimpleNamespace(message=msg)
            return types.SimpleNamespace(choices=[choice])

        scenario = {
            "id": "malformed",
            "description": "test",
            "input": {},
            "expected_output": {"feature": "f", "rationale": "r"},
            "scoring_rubric": [{"criterion": "x", "weight": 1.0}],
        }
        score = fitness_battery.score_scenario(scenario, "agent output", judge_llm=malformed_judge)
        assert score == 0.0
