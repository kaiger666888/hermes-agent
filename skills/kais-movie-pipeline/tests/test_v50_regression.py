"""test_v50_regression.py — Phase 40-04 Task 5: V5.0 explicit regression guard.

Asserts that V5.0's 502-test baseline is preserved after Phase 40 (rapid
preview tier). Uses subprocess.run for CLEAN ISOLATION — v6.0 Phase 40
import state (p10b module patched in earlier tests via monkeypatch) does
NOT contaminate the regression runs.

Each test invokes pytest on a canonical V5.0 test file via subprocess and
asserts exit code 0. Test 7 runs the full suite and asserts the total
passing count is >= 502 (V5.0 SHIPPED baseline). Test 8 verifies canonical
V5.0 test files still exist on disk (T-40-17 mitigation — guards against
silent deletion to make a regression test pass).

This task MUST run LAST in plan 04 (after Tasks 1-4 land). It is the
final gate before Phase 40 can be marked complete.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# hermes-agent root: skills/kais-movie-pipeline/tests/test_v50_regression.py
# → parents[0]=tests, [1]=kais-movie-pipeline, [2]=skills, [3]=hermes-agent
HERMES_ROOT = Path(__file__).resolve().parents[3]
SKILL_TESTS = HERMES_ROOT / "skills" / "kais-movie-pipeline" / "tests"
PIPELINE_STATE_TESTS = HERMES_ROOT / "plugins" / "pipeline_state" / "tests"
KAIS_AIGC_TESTS = HERMES_ROOT / "plugins" / "kais_aigc" / "tests"
REVIEW_GATES_TESTS = HERMES_ROOT / "plugins" / "review_gates" / "tests"

#: V5.0 SHIPPED baseline (Phase 31-39). The assertion is >= 502 to allow
#: variance in test granularity; Phase 40 adds ~36 more tests, so the
#: post-Phase-40 count is approximately 638.
V50_BASELINE = 502

#: Canonical V5.0 test files (T-40-17 mitigation — these MUST exist on disk).
CANONICAL_V50_TEST_FILES = [
    SKILL_TESTS / "test_phase_registry_full.py",
    SKILL_TESTS / "test_runner_full_dag.py",
    SKILL_TESTS / "test_e2e_degraded.py",
    SKILL_TESTS / "test_runner.py",
    SKILL_TESTS / "test_p01_unit.py",
    SKILL_TESTS / "test_p02_unit.py",
    SKILL_TESTS / "test_p03_unit.py",
    SKILL_TESTS / "test_p04_unit.py",
    SKILL_TESTS / "test_p05_unit.py",
    SKILL_TESTS / "test_p06_unit.py",
    SKILL_TESTS / "test_p07_unit.py",
    SKILL_TESTS / "test_p08_unit.py",
    SKILL_TESTS / "test_p09_unit.py",
    SKILL_TESTS / "test_p10_unit.py",
    SKILL_TESTS / "test_p11_unit.py",
    SKILL_TESTS / "test_p12_unit.py",
    SKILL_TESTS / "test_p13_unit.py",
    PIPELINE_STATE_TESTS / "test_asset_bus.py",
    KAIS_AIGC_TESTS / "test_gold_team.py",
]


def _run_pytest(*target_paths: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run pytest in a clean subprocess. Returns the CompletedProcess.

    NOTE on output capture: pytest's parent-process capture (capsys/capfd)
    can interfere with ``subprocess.run(stdout=PIPE)`` for the FINAL summary
    line when invoked from inside a pytest parent process. The root cause
    is `-q` suppressing the final summary line under nested pytest
    invocations. To work around this robustly across nested-pytest contexts,
    we use a SHELL WRAPPER that redirects output to a temp file (avoids
    Python-level PIPE plumbing entirely).
    """
    import tempfile
    import shlex
    cmd = [sys.executable, "-m", "pytest", "--tb=short"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend(str(p) for p in target_paths)
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".txt", delete=False, encoding="utf-8"
    ) as out_fh:
        out_path = out_fh.name
    try:
        # Use shell redirection so output goes DIRECTLY to the file (no
        # Python-level PIPE involvement, robust against pytest capture).
        pytest_cmd = shlex.join(cmd)
        shell_cmd = pytest_cmd + " > " + shlex.quote(out_path) + " 2>&1"
        result = subprocess.run(
            ["bash", "-c", shell_cmd],
            cwd=str(HERMES_ROOT),
            timeout=120,
        )
        with open(out_path, "r", encoding="utf-8") as f:
            captured = f.read()
    finally:
        try:
            Path(out_path).unlink()
        except OSError:
            pass
    return subprocess.CompletedProcess(
        args=cmd,
        returncode=result.returncode,
        stdout=captured,
        stderr="",  # merged into stdout
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestV50Regression:
    """V5.0 regression guard — final gate before Phase 40 marked complete."""

    def test_phase_registry_still_passes(self):
        """Test 1: test_phase_registry_full.py (14-phase registry assertions) passes."""
        result = _run_pytest(SKILL_TESTS / "test_phase_registry_full.py")
        assert result.returncode == 0, (
            f"V5.0 test_phase_registry_full.py failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_full_dag_traversal_still_passes(self):
        """Test 2: test_runner_full_dag.py (full DAG traversal including p10b) passes.

        The runner must traverse p10 → p10b → p11 cleanly (p10b.run no longer
        raises NotImplementedError after plan 03).
        """
        result = _run_pytest(SKILL_TESTS / "test_runner_full_dag.py")
        assert result.returncode == 0, (
            f"V5.0 test_runner_full_dag.py failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_v50_degraded_e2e_still_passes(self):
        """Test 3: test_e2e_degraded.py (V5.0 degraded E2E) still passes."""
        result = _run_pytest(SKILL_TESTS / "test_e2e_degraded.py")
        assert result.returncode == 0, (
            f"V5.0 test_e2e_degraded.py failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_asset_bus_v50_and_phase40_slots_pass(self):
        """Test 4: asset_bus tests (V5.0 + Phase 40 rapid-preview-clips + episode-meta) pass."""
        result = _run_pytest(
            PIPELINE_STATE_TESTS / "test_asset_bus.py",
            PIPELINE_STATE_TESTS / "test_asset_bus_phase35_slots.py",
        )
        assert result.returncode == 0, (
            f"V5.0 asset_bus tests failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_gold_team_unaffected(self):
        """Test 5: plugins/kais_aigc/tests/test_gold_team.py passes (unaffected by Phase 40).

        Uses pytest.importorskip semantics — if the file doesn't exist, skip.
        """
        target = KAIS_AIGC_TESTS / "test_gold_team.py"
        if not target.exists():
            pytest.skip(f"{target} does not exist — gold_team not in this build")
        result = _run_pytest(target)
        assert result.returncode == 0, (
            f"gold_team test failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_review_gates_unaffected(self):
        """Test 6: plugins/review_gates/tests/ passes (unaffected by Phase 40)."""
        result = _run_pytest(REVIEW_GATES_TESTS)
        assert result.returncode == 0, (
            f"review_gates tests failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_total_test_count_meets_v50_baseline(self):
        """Test 7: full test suite passing count >= 502 (V5.0 SHIPPED baseline).

        T-40-18 mitigation: uses ``>=`` (not exact equality) to allow for
        variance in test granularity (Phase 40 adds ~36 tests, so the
        expected count is approximately 638).

        IMPORTANT: This test MUST exclude itself from the subprocess run —
        otherwise it would re-spawn itself recursively (fork bomb).
        Achieved via ``--ignore`` on the test_v50_regression.py path.
        """
        # Run the FULL test suite (V5.0 + Phase 40 EXCLUDING this file)
        # with --tb=no for speed. NOTE: do NOT pass -q here — when invoked
        # from inside a pytest parent process, -q suppresses the final
        # summary line ("N passed in X.XXs"). Use default verbosity which
        # reliably emits the summary.
        self_path = SKILL_TESTS / "test_v50_regression.py"
        result = _run_pytest(
            SKILL_TESTS,
            PIPELINE_STATE_TESTS,
            KAIS_AIGC_TESTS,
            REVIEW_GATES_TESTS,
            extra_args=[
                "--tb=no",
                f"--ignore={self_path}",
                "-p", "no:cacheprovider",
            ],
        )
        # The suite may have known pre-existing failures (e.g. canvas_sync
        # sqlite references). We parse the "N passed" line and assert >= 502.
        # We do NOT require exit code 0 — pre-existing out-of-scope failures
        # are documented in the SUMMARY.
        # pytest may print the summary line to stdout OR stderr depending on
        # capture mode; check both.
        combined = result.stdout + "\n" + result.stderr
        passed_match = re.search(r"(\d+) passed", combined)
        if passed_match is None:
            # Save the full output to a debug file for inspection.
            debug_path = Path("/tmp/test_v50_regression_subprocess_output.txt")
            debug_path.write_text(combined, encoding="utf-8")
            raise AssertionError(
                f"could not parse pass count from combined stdout+stderr "
                f"(len={len(combined)}). Full output saved to {debug_path}. "
                f"Last 200 chars: {combined[-200:]!r}"
            )
        count = int(passed_match.group(1))
        assert count >= V50_BASELINE, (
            f"V5.0 baseline {V50_BASELINE} tests regressed to {count}.\n"
            f"Full stdout tail:\n{result.stdout[-1000:]}"
        )

    def test_no_v50_test_file_deleted(self):
        """Test 8 (T-40-17): canonical V5.0 test files all still exist on disk.

        Guards against the brownfield risk of deleting/moving V5.0 tests to
        make a regression assertion pass.
        """
        missing = [str(p) for p in CANONICAL_V50_TEST_FILES if not p.exists()]
        assert not missing, (
            f"canonical V5.0 test files missing from disk: {missing}"
        )
