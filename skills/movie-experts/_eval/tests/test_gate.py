"""Pytest coverage for the Phase 30 eval gate (gate.py).

RED phase of TDD: these tests import the not-yet-implemented ``gate``
module and therefore fail at collection time until Task 2 GREEN lands.

Test organization (mirrors 30-VALIDATION.md Per-Task Verification Map):
  - TestExtractPatchedFiles     — patch header parsing + path-traversal guard (T-30-01)
  - TestDecideVerdict           — GATE-02 mean delta + GATE-04 per-prompt regression
  - TestLoadGateConfig          — config precedence (defaults < YAML < CLI) + validation
  - TestExitCode                — verdict -> exit code mapping
  - TestPatchMechanics          — git apply --check + apply + revert (integration)
  - TestRevertOnException       — try/finally guarantees clean working tree
  - TestRunGateEndToEnd         — run_gate() with MockJudgeClient + pre-generated answers
  - TestGeneratePatchId         — patch_id format + determinism
  - TestGateCli                 — main() CLI surface (--help, flag parsing)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Sibling-import convention matching test_runner.py:25-29.
_EVAL_DIR = Path(__file__).resolve().parent.parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import gate  # noqa: E402  — RED until gate.py exists
import runner  # noqa: E402  — for MockJudgeClient + composite_score


# --------------------------------------------------------------------------- #
# Mock judge client (returns canned responses WITH numeric scores)
# --------------------------------------------------------------------------- #


class MockJudgeClient:
    """Duck-typed stand-in for an OpenAI client used by gate tests.

    Returns canned judge responses (containing per-dimension numeric
    scores + <decision> tag) keyed on the swap flag. NO real API calls.
    """

    def __init__(self, response_ab: str, response_ba: str) -> None:
        self._response_ab = response_ab
        self._response_ba = response_ba
        self.calls: list[dict] = []

    def chat_completions_create(self, **kwargs: object) -> dict:
        swap = bool(kwargs.get("extra_body", {}).get("swap", False))
        self.calls.append(kwargs)
        content = self._response_ba if swap else self._response_ab
        return {"choices": [{"message": {"content": content}}]}


def _judge_response(scores: dict[str, float], decision: str) -> str:
    """Build a canned judge response string with the given scores + decision."""
    lines = [
        f"{dim}: {score} — canned justification"
        for dim, score in scores.items()
    ]
    lines.append(f"<decision>{decision}</decision>")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def pass_patch_path() -> Path:
    return FIXTURES_DIR / "pass.patch"


@pytest.fixture
def multi_skill_patch_path() -> Path:
    return FIXTURES_DIR / "multi_skill.patch"


@pytest.fixture
def path_traversal_patch_path() -> Path:
    return FIXTURES_DIR / "path_traversal.patch"


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with a fake screenplay SKILL.md committed.

    Used by TestPatchMechanics to verify apply_patch / revert_patch
    actually invoke git subprocesses and restore bytes exactly.
    """
    repo = tmp_path / "repo"
    skills_dir = repo / "skills" / "movie-experts" / "screenplay"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text(
        "---\nname: screenplay\nexpert_id: screenplay\n---\noriginal content\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo), check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "add", "."], cwd=str(repo), check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=str(repo), check=True, capture_output=True,
    )
    return repo


# --------------------------------------------------------------------------- #
# TestExtractPatchedFiles — T-30-01 path-traversal mitigation
# --------------------------------------------------------------------------- #


class TestExtractPatchedFiles:
    def test_single_file(self, pass_patch_path: Path) -> None:
        files = gate.extract_patched_files(pass_patch_path)
        assert files == ["skills/movie-experts/screenplay/SKILL.md"]

    def test_rejects_path_traversal(self, path_traversal_patch_path: Path) -> None:
        # T-30-01: patch with +++ b/../../../etc/passwd must raise ValueError.
        with pytest.raises(ValueError, match="(?i)path traversal|escapes|outside"):
            gate.extract_patched_files(path_traversal_patch_path)

    def test_rejects_outside_skills(self, tmp_path: Path) -> None:
        # Patch touching agent/curator.py (outside skills/movie-experts/) must
        # be rejected.
        patch = tmp_path / "bad.patch"
        patch.write_text(
            "--- a/agent/curator.py\n"
            "+++ b/agent/curator.py\n"
            "@@ -1,1 +1,2 @@\n"
            "+# injected\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="(?i)outside|skills"):
            gate.extract_patched_files(patch)

    def test_multiple_files(self, multi_skill_patch_path: Path) -> None:
        files = gate.extract_patched_files(multi_skill_patch_path)
        assert "skills/movie-experts/screenplay/SKILL.md" in files
        assert "skills/movie-experts/drawer/SKILL.md" in files


# --------------------------------------------------------------------------- #
# TestDecideVerdict — GATE-02 + GATE-04 core logic (pure function)
# --------------------------------------------------------------------------- #


class TestDecideVerdict:
    def test_pass(self) -> None:
        baseline = [3.5, 3.0, 4.0, 3.5, 3.2]
        candidate = [3.4, 3.1, 4.0, 3.5, 3.3]
        verdict, evidence = gate.decide_verdict(
            baseline, candidate,
            delta_threshold=0.3,
            per_prompt_threshold=1.0,
            min_prompts=5,
        )
        assert verdict == "pass"
        assert "mean_delta" in evidence

    def test_fail_mean(self) -> None:
        # Mean drops 0.5 > threshold 0.3 -> fail_mean.
        baseline = [4.0, 4.0, 4.0, 4.0, 4.0]
        candidate = [3.5, 3.5, 3.5, 3.5, 3.5]
        verdict, evidence = gate.decide_verdict(
            baseline, candidate,
            delta_threshold=0.3,
            per_prompt_threshold=1.0,
            min_prompts=5,
        )
        assert verdict == "fail_mean"
        assert evidence["mean_delta"] == pytest.approx(-0.5)

    def test_fail_regression(self) -> None:
        # One prompt drops -1.5 < -1.0 threshold -> fail_regression even
        # though mean is acceptable.
        baseline = [4.0, 4.0, 4.0, 4.0, 4.0]
        candidate = [4.0, 4.0, 2.5, 4.0, 4.0]
        verdict, evidence = gate.decide_verdict(
            baseline, candidate,
            delta_threshold=0.3,
            per_prompt_threshold=1.0,
            min_prompts=5,
        )
        assert verdict == "fail_regression"
        assert "regressing_prompt_idx" in evidence

    def test_regression_boundary_passes(self) -> None:
        # Drop of exactly -1.0 is NOT < -1.0, so it passes the regression
        # threshold (boundary is strict-less-than).
        baseline = [4.0, 4.0, 4.0, 4.0, 4.0]
        candidate = [4.0, 4.0, 3.0, 4.0, 4.0]
        verdict, _ = gate.decide_verdict(
            baseline, candidate,
            delta_threshold=0.3,
            per_prompt_threshold=1.0,
            min_prompts=5,
        )
        assert verdict == "pass"

    def test_inconclusive(self) -> None:
        # Only 3 valid prompts < min_prompts=5 -> inconclusive.
        verdict, evidence = gate.decide_verdict(
            [3.0, 4.0, 3.5], [3.0, 4.0, 3.5],
            delta_threshold=0.3,
            per_prompt_threshold=1.0,
            min_prompts=5,
        )
        assert verdict == "inconclusive"
        assert evidence["n_valid"] == 3
        assert evidence["min_prompts"] == 5

    def test_deterministic(self) -> None:
        # Pure function: same inputs -> identical outputs.
        baseline = [3.5, 3.0, 4.0, 3.5, 3.2]
        candidate = [3.4, 3.1, 4.0, 3.5, 3.3]
        args = (baseline, candidate)
        kwargs = {
            "delta_threshold": 0.3,
            "per_prompt_threshold": 1.0,
            "min_prompts": 5,
        }
        v1, e1 = gate.decide_verdict(*args, **kwargs)
        v2, e2 = gate.decide_verdict(*args, **kwargs)
        assert v1 == v2
        assert e1 == e2


# --------------------------------------------------------------------------- #
# TestLoadGateConfig — defaults < YAML < CLI precedence + validation
# --------------------------------------------------------------------------- #


class TestLoadGateConfig:
    def test_defaults_when_no_file(self) -> None:
        cfg = gate.load_gate_config(None, {})
        assert cfg["delta_threshold"] == 0.3
        assert cfg["per_prompt_threshold"] == 1.0
        assert cfg["min_prompts"] == 5
        assert cfg["ab_positions"] == 2

    def test_loads_from_yaml(self, tmp_path: Path) -> None:
        config_path = tmp_path / "gate_config.yaml"
        config_path.write_text(
            "delta_threshold: 0.2\n"
            "per_prompt_threshold: 0.8\n"
            "min_prompts: 3\n"
            "ab_positions: 1\n"
            "judge_model: qwen3\n",
            encoding="utf-8",
        )
        cfg = gate.load_gate_config(config_path, {})
        assert cfg["delta_threshold"] == 0.2
        assert cfg["per_prompt_threshold"] == 0.8
        assert cfg["min_prompts"] == 3
        assert cfg["ab_positions"] == 1
        assert cfg["judge_model"] == "qwen3"

    def test_cli_override(self) -> None:
        # CLI flags override YAML values.
        cfg = gate.load_gate_config(
            None,
            {"delta_threshold": 0.15},
        )
        assert cfg["delta_threshold"] == 0.15
        # Non-overridden fields keep defaults.
        assert cfg["per_prompt_threshold"] == 1.0

    def test_rejects_invalid_delta(self) -> None:
        with pytest.raises(ValueError, match="(?i)delta_threshold"):
            gate.load_gate_config(None, {"delta_threshold": 5.5})

    def test_rejects_invalid_min_prompts(self) -> None:
        with pytest.raises(ValueError, match="(?i)min_prompts"):
            gate.load_gate_config(None, {"min_prompts": 0})


# --------------------------------------------------------------------------- #
# TestExitCode — verdict -> exit code mapping
# --------------------------------------------------------------------------- #


class TestExitCode:
    def test_pass_to_0(self) -> None:
        assert gate.VERDICT_TO_EXIT["pass"] == 0

    def test_fail_mean_to_1(self) -> None:
        assert gate.VERDICT_TO_EXIT["fail_mean"] == 1

    def test_fail_regression_to_2(self) -> None:
        assert gate.VERDICT_TO_EXIT["fail_regression"] == 2

    def test_inconclusive_to_3(self) -> None:
        assert gate.VERDICT_TO_EXIT["inconclusive"] == 3


# --------------------------------------------------------------------------- #
# TestPatchMechanics — git apply --check + apply + revert (integration)
# --------------------------------------------------------------------------- #


class TestPatchMechanics:
    def test_apply_then_revert_restores_bytes(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        # Create a real patch against the committed file.
        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        original_bytes = skill_file.read_bytes()
        original_sha = hashlib.sha256(original_bytes).hexdigest()

        # Make a working-tree change, diff it, then revert the working tree.
        skill_file.write_text(
            original_bytes.decode("utf-8") + "\n# candidate change\n",
            encoding="utf-8",
        )
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        patch_path = tmp_path / "candidate.patch"
        patch_path.write_text(diff_result.stdout, encoding="utf-8")
        # Restore the working tree so apply_patch starts from clean.
        subprocess.run(
            ["git", "checkout", "--", "skills/movie-experts/screenplay/SKILL.md"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            check=True,
        )

        files = gate.extract_patched_files(patch_path)
        gate.apply_patch(patch_path, tmp_git_repo)
        # Working tree now has the candidate change.
        assert b"candidate change" in skill_file.read_bytes()
        # Revert.
        gate.revert_patch(files, tmp_git_repo)
        # Bytes exactly restored.
        reverted_sha = hashlib.sha256(skill_file.read_bytes()).hexdigest()
        assert reverted_sha == original_sha, (
            "revert did not restore bytes exactly: "
            f"original={original_sha} reverted={reverted_sha}"
        )

    def test_apply_check_failure_raises(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        # Patch that does not apply cleanly -> CalledProcessError BEFORE
        # any working-tree mutation.
        bad_patch = tmp_path / "bad.patch"
        bad_patch.write_text(
            "--- a/skills/movie-experts/screenplay/SKILL.md\n"
            "+++ b/skills/movie-experts/screenplay/SKILL.md\n"
            "@@ -999,1 +999,1 @@\n"
            "-nonexistent line\n"
            "+replacement\n",
            encoding="utf-8",
        )
        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        original_bytes = skill_file.read_bytes()
        with pytest.raises(subprocess.CalledProcessError):
            gate.apply_patch(bad_patch, tmp_git_repo)
        # Working tree NOT mutated (--check failed first).
        assert skill_file.read_bytes() == original_bytes


# --------------------------------------------------------------------------- #
# TestRevertOnException — try/finally guarantees clean working tree
# --------------------------------------------------------------------------- #


class TestRevertOnException:
    def test_revert_runs_in_finally(
        self, tmp_git_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # If evaluate raises mid-run, revert_patch must still run.
        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        original_bytes = skill_file.read_bytes()

        # Build a real patch.
        skill_file.write_text(
            original_bytes.decode("utf-8") + "\n# wip\n",
            encoding="utf-8",
        )
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        patch_path = tmp_path / "c.patch"
        patch_path.write_text(diff_result.stdout, encoding="utf-8")
        subprocess.run(
            ["git", "checkout", "--", "skills/movie-experts/screenplay/SKILL.md"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            check=True,
        )

        # Make revert_patch observable — wrap the real one with a counter.
        revert_calls: list[int] = []
        real_revert = gate.revert_patch

        def counting_revert(files, repo_root):
            revert_calls.append(1)
            return real_revert(files, repo_root)

        monkeypatch.setattr(gate, "revert_patch", counting_revert)

        # Make evaluate_candidate blow up.
        def boom(*args, **kwargs):
            raise RuntimeError("simulated judge failure")

        monkeypatch.setattr(gate, "evaluate_candidate", boom)

        # Prepare minimal inputs for run_gate.
        baseline_answers = tmp_path / "baseline.json"
        candidate_answers = tmp_path / "candidate.json"
        baseline_answers.write_text("[]", encoding="utf-8")
        candidate_answers.write_text("[]", encoding="utf-8")
        prompts_path = tmp_path / "prompts.yaml"
        prompts_path.write_text(
            "expert_id: screenplay\nprompts:\n  - id: p1\n    text: x\n",
            encoding="utf-8",
        )

        config = gate.load_gate_config(None, {})

        with pytest.raises(RuntimeError, match="simulated judge failure"):
            gate.run_gate(
                patch_path=patch_path,
                skill_id="screenplay",
                baseline_answers_path=baseline_answers,
                candidate_answers_path=candidate_answers,
                config=config,
                repo_root=tmp_git_repo,
                prompts_path=prompts_path,
                judge_client=MockJudgeClient(
                    _judge_response(
                        {"industry_accuracy": 4.0}, "A"
                    ),
                    _judge_response(
                        {"industry_accuracy": 4.0}, "B"
                    ),
                ),
            )

        # revert_patch MUST have been called even though evaluate raised.
        assert len(revert_calls) >= 1, (
            "revert_patch was not invoked in the finally block"
        )
        # And the working tree is clean.
        assert skill_file.read_bytes() == original_bytes


# --------------------------------------------------------------------------- #
# TestRunGateEndToEnd — run_gate() with MockJudgeClient + pre-gen answers
# --------------------------------------------------------------------------- #


class TestRunGateEndToEnd:
    def _setup_prompts_and_answers(
        self, tmp_path: Path, n: int = 5
    ) -> tuple[Path, Path, Path]:
        prompts_path = tmp_path / "prompts.yaml"
        prompt_entries = "\n".join(
            f"  - id: p{i}\n    text: prompt {i}" for i in range(n)
        )
        prompts_path.write_text(
            f"expert_id: screenplay\nprompts:\n{prompt_entries}\n",
            encoding="utf-8",
        )
        baseline_answers = tmp_path / "baseline.json"
        candidate_answers = tmp_path / "candidate.json"
        baseline_answers.write_text(
            json.dumps([f"baseline answer {i}" for i in range(n)]),
            encoding="utf-8",
        )
        candidate_answers.write_text(
            json.dumps([f"candidate answer {i}" for i in range(n)]),
            encoding="utf-8",
        )
        return prompts_path, baseline_answers, candidate_answers

    def test_with_mock_judge_and_pregenerated_answers(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        # Candidate scores slightly higher than baseline -> pass.
        prompts_path, baseline_ans, candidate_ans = (
            self._setup_prompts_and_answers(tmp_path, n=5)
        )

        # Build a real patch.
        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8") + "\n# candidate\n",
            encoding="utf-8",
        )
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        patch_path = tmp_path / "c.patch"
        patch_path.write_text(diff_result.stdout, encoding="utf-8")
        subprocess.run(
            ["git", "checkout", "--", "skills/movie-experts/screenplay/SKILL.md"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            check=True,
        )

        judge = MockJudgeClient(
            response_ab=_judge_response(
                {
                    "industry_accuracy": 4.0,
                    "professional_depth": 4.0,
                    "actionability": 4.0,
                    "language_quality": 4.0,
                },
                "A",
            ),
            response_ba=_judge_response(
                {
                    "industry_accuracy": 4.0,
                    "professional_depth": 4.0,
                    "actionability": 4.0,
                    "language_quality": 4.0,
                },
                "B",
            ),
        )

        config = gate.load_gate_config(None, {})
        result = gate.run_gate(
            patch_path=patch_path,
            skill_id="screenplay",
            baseline_answers_path=baseline_ans,
            candidate_answers_path=candidate_ans,
            config=config,
            repo_root=tmp_git_repo,
            prompts_path=prompts_path,
            judge_client=judge,
        )
        assert result.verdict == "pass"
        assert result.exit_code == 0

    def test_writes_report_json(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        prompts_path, baseline_ans, candidate_ans = (
            self._setup_prompts_and_answers(tmp_path, n=5)
        )

        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8") + "\n# c\n",
            encoding="utf-8",
        )
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        patch_path = tmp_path / "c.patch"
        patch_path.write_text(diff_result.stdout, encoding="utf-8")
        subprocess.run(
            ["git", "checkout", "--", "skills/movie-experts/screenplay/SKILL.md"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            check=True,
        )

        reports_dir = tmp_path / "reports"
        judge = MockJudgeClient(
            response_ab=_judge_response(
                {"industry_accuracy": 4.0}, "A"
            ),
            response_ba=_judge_response(
                {"industry_accuracy": 4.0}, "B"
            ),
        )
        config = gate.load_gate_config(None, {})
        result = gate.run_gate(
            patch_path=patch_path,
            skill_id="screenplay",
            baseline_answers_path=baseline_ans,
            candidate_answers_path=candidate_ans,
            config=config,
            repo_root=tmp_git_repo,
            prompts_path=prompts_path,
            judge_client=judge,
            reports_dir=reports_dir,
        )
        assert result.report_path is not None
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        assert report["schema_version"] == 1
        assert "verdict" in report
        assert "thresholds" in report
        assert "per_prompt" in report
        assert "judge_model" in report
        assert "ts" in report

    def test_writes_reject_log_on_failure(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        # Candidate scores much lower than baseline -> fail_mean -> reject log.
        prompts_path, baseline_ans, candidate_ans = (
            self._setup_prompts_and_answers(tmp_path, n=5)
        )

        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8") + "\n# c\n",
            encoding="utf-8",
        )
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        patch_path = tmp_path / "c.patch"
        patch_path.write_text(diff_result.stdout, encoding="utf-8")
        subprocess.run(
            ["git", "checkout", "--", "skills/movie-experts/screenplay/SKILL.md"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            check=True,
        )

        reports_dir = tmp_path / "reports"
        # Baseline judge says 5.0, candidate judge says 2.0 -> mean delta -3.0.
        judge = MockJudgeClient(
            response_ab=_judge_response(
                {
                    "industry_accuracy": 2.0,
                    "professional_depth": 2.0,
                    "actionability": 2.0,
                    "language_quality": 2.0,
                },
                "A",
            ),
            response_ba=_judge_response(
                {
                    "industry_accuracy": 2.0,
                    "professional_depth": 2.0,
                    "actionability": 2.0,
                    "language_quality": 2.0,
                },
                "B",
            ),
        )
        config = gate.load_gate_config(None, {})
        # Pre-populate baseline cache with high scores so candidate drops.
        baseline_cache = reports_dir / "baseline_scores.json"
        baseline_cache.parent.mkdir(parents=True, exist_ok=True)
        baseline_cache.write_text(
            json.dumps([5.0, 5.0, 5.0, 5.0, 5.0]),
            encoding="utf-8",
        )

        result = gate.run_gate(
            patch_path=patch_path,
            skill_id="screenplay",
            baseline_answers_path=baseline_ans,
            candidate_answers_path=candidate_ans,
            config=config,
            repo_root=tmp_git_repo,
            prompts_path=prompts_path,
            judge_client=judge,
            reports_dir=reports_dir,
            baseline_scores_cache=baseline_cache,
        )
        assert result.verdict == "fail_mean"
        assert result.exit_code == 1
        # Reject log MUST exist alongside the report.
        reject_path = result.report_path.with_suffix(".reject.json")
        assert reject_path.is_file(), (
            f"reject log not written at {reject_path}"
        )
        reject = json.loads(reject_path.read_text(encoding="utf-8"))
        assert "operator_hint" in reject


# --------------------------------------------------------------------------- #
# TestGeneratePatchId
# --------------------------------------------------------------------------- #


class TestGeneratePatchId:
    def test_format_contains_skill_ts_sha(self, tmp_path: Path) -> None:
        patch = tmp_path / "p.patch"
        patch.write_text("dummy", encoding="utf-8")
        patch_id = gate.generate_patch_id("screenplay", patch)
        # Format: <skill>_<ts_unix>_<sha256[:8]>
        parts = patch_id.split("_")
        assert parts[0] == "screenplay"
        assert len(parts) == 3
        assert parts[1].isdigit(), f"timestamp not numeric: {parts[1]}"
        assert len(parts[2]) == 8, f"sha prefix not 8 chars: {parts[2]}"

    def test_sha_matches_patch_bytes(self, tmp_path: Path) -> None:
        patch = tmp_path / "p.patch"
        patch.write_text("content", encoding="utf-8")
        patch_id = gate.generate_patch_id("drawer", patch)
        expected_sha = hashlib.sha256(b"content").hexdigest()[:8]
        assert patch_id.endswith(expected_sha)


# --------------------------------------------------------------------------- #
# TestGateCli — main() CLI surface
# --------------------------------------------------------------------------- #


class TestGateCli:
    def test_help_exits_zero(self, capsys) -> None:
        # --help MUST exit 0 and print usage (per SC #5).
        with pytest.raises(SystemExit) as exc:
            gate.main(["--help"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "patch" in captured.out.lower()

    def test_dry_run_with_stub_judge(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        # --dry-run uses runner._StubJudgeClient; no live API call.
        # Build a real patch first.
        skill_file = (
            tmp_git_repo
            / "skills"
            / "movie-experts"
            / "screenplay"
            / "SKILL.md"
        )
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8") + "\n# c\n",
            encoding="utf-8",
        )
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        patch_path = tmp_path / "c.patch"
        patch_path.write_text(diff_result.stdout, encoding="utf-8")
        subprocess.run(
            ["git", "checkout", "--", "skills/movie-experts/screenplay/SKILL.md"],
            cwd=str(tmp_git_repo),
            capture_output=True,
            check=True,
        )

        prompts_path = tmp_path / "prompts.yaml"
        prompts_path.write_text(
            "expert_id: screenplay\nprompts:\n  - id: p1\n    text: x\n",
            encoding="utf-8",
        )
        baseline_ans = tmp_path / "b.json"
        candidate_ans = tmp_path / "c.json"
        baseline_ans.write_text(
            json.dumps(["baseline"]), encoding="utf-8"
        )
        candidate_ans.write_text(
            json.dumps(["candidate"]), encoding="utf-8"
        )

        rc = gate.main(
            [
                "--patch", str(patch_path),
                "--skill", "screenplay",
                "--baseline-answers", str(baseline_ans),
                "--candidate-answers", str(candidate_ans),
                "--prompts-dir", str(prompts_path),
                "--dry-run",
                "--repo-root", str(tmp_git_repo),
            ]
        )
        # Stub returns no scores -> inconclusive is acceptable for dry-run.
        assert rc in (0, 3)
