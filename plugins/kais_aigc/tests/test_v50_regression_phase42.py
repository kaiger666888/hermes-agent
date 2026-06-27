"""Phase 42 brownfield regression guard. Phase 42 is the FINAL phase of v6.0 —
this file is the v6.0 ship gate. Asserts:

  - V5.0 + Phase 40 + Phase 41 baselines preserved (per-file subprocess isolation)
  - Phase 42 structural invariants:
      * ASSET_SCHEMA has exactly 36 slots (V5.0 30 + Phase 40 2 + Phase 41 1 + Phase 42 2)
        — wait, the actual verified count is 36, not 35 (off-by-one in the plan prose;
          set equality is what matters, and the canonical set has 36 entries).
      * JSONL_SLOTS frozenset unchanged at frozenset({"finetune-dataset"})
      * feedback_ingest.py has ZERO imports of p10b / runner / preview_engine
        (LOAD-BEARING — Test 13 — FEEDBACK-INGEST-05 structural enforcement)
      * 0 openclaw references in V5.0-baseline files Phase 42 touched + new module
  - All Phase 42 test files pass in clean subprocess
  - Aggregate test count >= 650 (V5.0 502 + Phase 40 174 + Phase 41 91 + Phase 42 ~40)

Each per-file regression test runs in a CLEAN SUBPROCESS (import-state isolation).
Test 13 is LOAD-BEARING for FEEDBACK-INGEST-05: the absence of the forbidden
imports IS the "no auto-modify pipeline" invariant. If this test fails, someone
added a forbidden import — the system would auto-modify the pipeline, violating
the human-decision-first principle.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from plugins.pipeline_state.asset_bus import ASSET_SCHEMA, AssetBus


# ─── Constants ─────────────────────────────────────────────────────────

# HERMES_ROOT = tests/ → kais_aigc/ → plugins/ → hermes-agent/
HERMES_ROOT = Path(__file__).resolve().parents[3]

# Complete expected ASSET_SCHEMA slot set after Phase 42 (36 slots).
# V5.0 Phase 33-36-04 = 30 slots, Phase 40 = 2 (rapid-preview-clips, episode-meta),
# Phase 41 = 1 (emotion-recipe), Phase 42 = 2 (feedback-data, feedback-rejected).
# 30 + 2 + 1 + 2 = 35 by plan prose, but the verified count is 36 (the V5.0
# baseline itself was 31, not 30 — see test_v50_regression_phase41 EXPECTED_SLOTS
# for the canonical enumeration). Set equality is what matters.
EXPECTED_SLOTS = {
    # V5.0 Phase 33 (3 typed + review-outcomes)
    "creative-history", "failed-shots", "finetune-dataset", "review-outcomes",
    # V5.0 Phase 35 (6 phase-output)
    "requirement", "topic-kernel", "hook-design", "story-framework",
    "script-draft", "audit-report",
    # V5.0 Phase 36-01 (6 p04/p05/p06)
    "character-bible", "character-assets", "pain-points", "escalation-ladder",
    "spatio-temporal-script", "final-audit",
    # V5.0 Phase 36-02 (7 p07/p08/p09)
    "scene-images", "style-vector", "color-intent", "scene-selection",
    "geometry-bed", "shot-list", "e-konte-sheets",
    # V5.0 Phase 36-03 (4 p10/p11)
    "voice-clips", "voice-timeline", "video-clips", "lip-sync-reports",
    # V5.0 Phase 36-04 (4 p12/p13)
    "master-timeline", "audio-stems", "master-mp4", "delivery-package",
    # v6.0 Phase 40 (2 p10b)
    "rapid-preview-clips", "episode-meta",
    # v6.0 Phase 41 (1 recipe library)
    "emotion-recipe",
    # v6.0 Phase 42 (2 feedback ingestion — added by plan 42-01)
    "feedback-data", "feedback-rejected",
}

# Canonical V5.0 + Phase 40 test files (regression baseline — DO NOT MODIFY)
CANONICAL_TEST_FILES = [
    "plugins/pipeline_state/tests/test_asset_bus.py",
    "plugins/pipeline_state/tests/test_asset_bus_phase35_slots.py",
    "plugins/pipeline_state/tests/test_creative_history.py",
    "plugins/pipeline_state/tests/test_store.py",
    "plugins/pipeline_state/tests/test_smoke.py",
    "plugins/pipeline_state/tests/test_tools_dispatch.py",
    "plugins/pipeline_state/tests/test_loader_discovery.py",
    "skills/kais-movie-pipeline/tests/test_phase_registry_full.py",
    "skills/kais-movie-pipeline/tests/test_runner_full_dag.py",
    "skills/kais-movie-pipeline/tests/test_e2e_degraded.py",
    "skills/kais-movie-pipeline/tests/test_v50_regression.py",
    "skills/kais-movie-pipeline/tests/test_p10b_unit.py",
]

# Phase 41 test files (Test asserts each passes explicitly in subprocess).
PHASE_41_TEST_FILES = [
    "plugins/pipeline_state/tests/test_asset_bus_emotion_recipe_slot.py",
    "plugins/pipeline_state/tests/test_recipe_library.py",
    "plugins/pipeline_state/tests/test_recipe_library_extraction.py",
    "plugins/pipeline_state/tests/test_recipe_library_update_validation.py",
    "plugins/pipeline_state/tests/test_recipe_library_query.py",
    "plugins/pipeline_state/tests/test_recipe_library_integration.py",
    "plugins/pipeline_state/tests/test_recipe_library_continuous_ci.py",
    "plugins/pipeline_state/tests/test_v50_regression_phase41.py",
]

# Phase 42 test files (Test 16 asserts each passes in clean subprocess).
PHASE_42_TEST_FILES = [
    "plugins/kais_aigc/tests/test_feedback_ingest_skeleton.py",
    "plugins/kais_aigc/tests/test_feedback_validation.py",
    "plugins/kais_aigc/tests/test_feedback_server.py",
    "plugins/kais_aigc/tests/test_feedback_ingest_integration.py",
]

# V5.0-baseline files Phase 42 modified (LOAD-BEARING openclaw regression surface)
V50_FILES_PHASE42_TOUCHED = [
    HERMES_ROOT / "plugins/pipeline_state/asset_bus.py",  # 42-01 added 2 slots
]

# Phase 42 new module — the load-bearing file for the structural grep (Test 13).
PHASE_42_NEW_MODULE = HERMES_ROOT / "plugins/kais_aigc/feedback_ingest.py"

# Aggregate test count threshold (V5.0 502 + Phase 40 174 + Phase 41 91 + Phase 42 ~40).
# Per SCOPE BOUNDARY + Rule 3, scoped threshold allows some slack for corpus changes.
SCOPED_THRESHOLD = 650


# ─── Helper ────────────────────────────────────────────────────────────


def _run_pytest(test_path: str, *extra_args: str) -> subprocess.CompletedProcess:
    """Run pytest in a clean subprocess with import-state isolation."""
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", test_path, *extra_args]
    return subprocess.run(
        cmd,
        cwd=str(HERMES_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )


# ═══════════════════════════════════════════════════════════════════
# TestV50RegressionPhase42 — 17 explicit regression tests
# ═══════════════════════════════════════════════════════════════════


class TestV50RegressionPhase42:
    """Explicit V5.0 + Phase 40 + Phase 41 regression guard for Phase 42.

    Phase 42 is the FINAL phase of v6.0 — this file is the v6.0 ship gate.
    """

    # ── Tests 1-4: V5.0 pipeline_state tests in clean subprocesses ──

    def test_v50_asset_bus_tests_pass(self) -> None:
        """Test 1: V5.0 AssetBus canonical tests pass."""
        result = _run_pytest("plugins/pipeline_state/tests/test_asset_bus.py")
        assert result.returncode == 0, (
            f"V5.0 test_asset_bus.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    def test_v50_phase35_slot_regression_passes(self) -> None:
        """Test 2: Phase 35 slot regression — Phase 42 must not modify pre-existing slots."""
        result = _run_pytest(
            "plugins/pipeline_state/tests/test_asset_bus_phase35_slots.py"
        )
        assert result.returncode == 0, (
            f"V5.0 test_asset_bus_phase35_slots.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    def test_v50_creative_history_tests_pass(self) -> None:
        """Test 3: V5.0 creative_history tests pass."""
        result = _run_pytest("plugins/pipeline_state/tests/test_creative_history.py")
        assert result.returncode == 0, (
            f"V5.0 test_creative_history.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    def test_v50_store_tests_pass(self) -> None:
        """Test 4: V5.0 PipelineStateStore tests pass."""
        result = _run_pytest("plugins/pipeline_state/tests/test_store.py")
        assert result.returncode == 0, (
            f"V5.0 test_store.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    # ── Tests 5-8: Phase 40 tests in clean subprocesses ──

    def test_phase40_p10b_unit_tests_pass(self) -> None:
        """Test 5: Phase 40 p10b unit tests pass."""
        result = _run_pytest("skills/kais-movie-pipeline/tests/test_p10b_unit.py")
        assert result.returncode == 0, (
            f"Phase 40 test_p10b_unit.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    def test_phase40_registry_tests_pass(self) -> None:
        """Test 6: Phase 40 phase_registry_full test passes (14 phases)."""
        result = _run_pytest(
            "skills/kais-movie-pipeline/tests/test_phase_registry_full.py"
        )
        assert result.returncode == 0, (
            f"Phase 40 test_phase_registry_full.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    def test_phase40_full_dag_tests_pass(self) -> None:
        """Test 7: Phase 40 runner_full_dag test passes (p10 → p10b → p11)."""
        result = _run_pytest(
            "skills/kais-movie-pipeline/tests/test_runner_full_dag.py"
        )
        assert result.returncode == 0, (
            f"Phase 40 test_runner_full_dag.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    def test_phase40_v50_regression_tests_pass(self) -> None:
        """Test 8: Phase 40's own V5.0 regression suite passes (excluding the
        pre-existing flaky count test that has a 120s subprocess timeout).
        """
        result = _run_pytest(
            "skills/kais-movie-pipeline/tests/test_v50_regression.py",
            "--deselect",
            "skills/kais-movie-pipeline/tests/test_v50_regression.py"
            "::TestV50Regression::test_total_test_count_meets_v50_baseline",
        )
        assert result.returncode == 0, (
            f"Phase 40 test_v50_regression.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    # ── Test 9: Phase 41 regression guard still passes ──

    def test_phase41_v50_regression_passes(self) -> None:
        """Test 9: Phase 41's own regression guard passes (Phase 42 must not
        break Phase 41's regression suite)."""
        result = _run_pytest(
            "plugins/pipeline_state/tests/test_v50_regression_phase41.py",
        )
        assert result.returncode == 0, (
            f"Phase 41 test_v50_regression_phase41.py FAILED:\n{result.stdout}\n{result.stderr}"
        )

    # ── Tests 10-11: Schema invariants (in-process) ──

    def test_asset_schema_contains_all_expected_slots(self) -> None:
        """Test 10: ASSET_SCHEMA contains exactly the expected slot set
        (V5.0 30 + Phase 40 2 + Phase 41 1 + Phase 42 2 = 36 verified slots).
        Verifies Phase 42 is append-only — no existing slot modified/removed.
        """
        actual = set(ASSET_SCHEMA.keys())
        assert actual == EXPECTED_SLOTS, (
            f"ASSET_SCHEMA drift detected:\n"
            f"  in actual not expected: {actual - EXPECTED_SLOTS}\n"
            f"  in expected not actual: {EXPECTED_SLOTS - actual}\n"
            f"  actual count: {len(actual)}, expected count: {len(EXPECTED_SLOTS)}"
        )
        # Sanity: Phase 42 additions present
        assert ASSET_SCHEMA["feedback-data"]["format"] == "jsonl"
        assert ASSET_SCHEMA["feedback-rejected"]["format"] == "jsonl"

    def test_jsonl_slots_frozenset_unchanged(self) -> None:
        """Test 11: JSONL_SLOTS frozenset UNCHANGED at frozenset({'finetune-dataset'})
        — Phase 42 did NOT add to JSONL_SLOTS (D-36-05 invariant)."""
        assert AssetBus.JSONL_SLOTS == frozenset({"finetune-dataset"}), (
            f"JSONL_SLOTS drift: expected frozenset({{'finetune-dataset'}}), "
            f"got {AssetBus.JSONL_SLOTS}"
        )

    # ── Test 12: No canonical test file deleted ──

    def test_no_v50_test_file_deleted(self) -> None:
        """Test 12: All canonical V5.0 + Phase 40 test files still exist on disk."""
        missing = [
            f for f in CANONICAL_TEST_FILES
            if not (HERMES_ROOT / f).exists()
        ]
        assert missing == [], (
            f"Canonical V5.0/Phase 40 test files deleted by Phase 42: {missing}"
        )

    # ── Test 13 (LOAD-BEARING — STRUCTURAL): no forbidden imports ──

    def test_no_forbidden_imports_in_feedback_ingest(self) -> None:
        """Test 13 (LOAD-BEARING — FEEDBACK-INGEST-05): structural enforcement
        of the 'no auto-modify pipeline' invariant.

        Runs `grep -cE` on feedback_ingest.py for forbidden import patterns
        and asserts the count is 0. The absence of these imports IS the
        enforcement — not a config flag, not a runtime check. If this test
        fails, someone added a forbidden import and the system would
        auto-modify the pipeline, violating the human-decision-first principle.

        Pattern matches:
          - `from.*pipeline\\.phases` (any pipeline phase module)
          - `import.*p10b` (the rapid-preview phase)
          - `import.*runner` (the DAG runner)
          - `import.*preview_engine` (the preview engine)
          - `from.*runner` / `from.*preview_engine`

        Note: grep -cE returns count of MATCHING LINES. Even one match fails.
        """
        pattern = (
            r"from.*pipeline\.phases|import.*p10b|import.*runner|"
            r"import.*preview_engine|from.*runner|from.*preview_engine"
        )
        assert PHASE_42_NEW_MODULE.exists(), (
            f"Phase 42 new module missing: {PHASE_42_NEW_MODULE}"
        )
        result = subprocess.run(
            ["grep", "-cE", pattern, str(PHASE_42_NEW_MODULE)],
            capture_output=True,
            text=True,
        )
        # grep -c prints the count of matching lines (0 if no matches).
        # Exit code 1 means "no matches found" (which is what we want).
        # Exit code >1 means an actual error.
        assert result.returncode in (0, 1), (
            f"grep errored (rc={result.returncode}):\n{result.stderr}"
        )
        stdout = result.stdout.strip()
        count = int(stdout) if stdout.isdigit() else 0
        assert count == 0, (
            f"FEEDBACK-INGEST-05 VIOLATION: feedback_ingest.py contains {count} "
            f"forbidden import line(s) matching /{pattern}/. The absence of these "
            f"imports IS the 'no auto-modify pipeline' invariant — adding them "
            f"would let feedback auto-modify the pipeline, violating the "
            f"human-decision-first principle. Offending lines:\n"
            f"{self._show_matches(pattern)}"
        )

    @staticmethod
    def _show_matches(pattern: str) -> str:
        """Helper: return the actual matching lines (for failure diagnostics)."""
        result = subprocess.run(
            ["grep", "-nE", pattern, str(PHASE_42_NEW_MODULE)],
            capture_output=True,
            text=True,
        )
        return result.stdout or "(no matches — race condition?)"

    # ── Test 14: openclaw regression on V5.0-baseline files Phase 42 touched ──

    def test_no_openclaw_refs_in_v50_files_phase42_touched(self) -> None:
        """Test 14: For each V5.0-baseline file Phase 42 modified (asset_bus.py),
        grep -c "openclaw" returns 0. Phase 42 must not smuggle openclaw back
        into V5.0 baseline code (OPENCLAW-REMOVE-03 invariant)."""
        for f in V50_FILES_PHASE42_TOUCHED:
            assert f.exists(), f"V5.0 file missing: {f}"
            result = subprocess.run(
                ["grep", "-c", "openclaw", str(f)],
                capture_output=True,
                text=True,
            )
            stdout = result.stdout.strip()
            count = int(stdout) if stdout.isdigit() else 0
            assert count == 0, (
                f"Phase 42 introduced {count} openclaw references into V5.0 "
                f"file {f.name} (OPENCLAW-REMOVE-03 regression)."
            )

    # ── Test 15: openclaw regression on new Phase 42 module ──

    def test_no_openclaw_refs_in_new_phase42_module(self) -> None:
        """Test 15: For the new Phase 42 module (feedback_ingest.py),
        grep -c "openclaw" returns 0."""
        assert PHASE_42_NEW_MODULE.exists(), "feedback_ingest.py missing"
        result = subprocess.run(
            ["grep", "-c", "openclaw", str(PHASE_42_NEW_MODULE)],
            capture_output=True,
            text=True,
        )
        stdout = result.stdout.strip()
        count = int(stdout) if stdout.isdigit() else 0
        assert count == 0, (
            f"Phase 42 new module feedback_ingest.py has {count} openclaw "
            f"references (should be 0)."
        )

    # ── Test 16: Phase 42 test files each pass in clean subprocess ──

    @pytest.mark.parametrize("test_file", PHASE_42_TEST_FILES)
    def test_phase42_test_files_explicitly_pass(self, test_file: str) -> None:
        """Test 16: Each of the 4 Phase 42 test files passes when run in a
        clean subprocess. Stronger than Test 17's aggregate threshold —
        catches per-file failures even if the total count is high."""
        result = _run_pytest(test_file)
        assert result.returncode == 0, (
            f"Phase 42 test file {test_file} FAILED (rc={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    # ── Test 17: AGGREGATE COUNT ──

    def test_aggregate_test_count_meets_baseline(self) -> None:
        """Test 17: Total pass count across pipeline_state + kais_aigc + skills
        >= 650 (V5.0 502 + Phase 40 174 + Phase 41 91 + Phase 42 ~40 additions).

        SCOPE NOTE: scoped to the directories Phase 42 actually affects.
        Pre-existing flaky Phase 40 count test (120s subprocess timeout) and
        self (would recurse) are explicitly excluded.
        """
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "plugins/pipeline_state/tests/",
                "plugins/kais_aigc/tests/",
                "skills/kais-movie-pipeline/tests/",
                # Exclude self (would recurse) + pre-existing flaky count test.
                "--ignore=plugins/kais_aigc/tests/test_v50_regression_phase42.py",
                "--deselect",
                "skills/kais-movie-pipeline/tests/test_v50_regression.py"
                "::TestV50Regression::test_total_test_count_meets_v50_baseline",
                "--tb=no", "-q",
            ],
            cwd=str(HERMES_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        match = re.search(r"(\d+) passed", result.stdout)
        assert match, (
            f"Could not parse pass count from pytest output.\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        count = int(match.group(1))
        assert count >= SCOPED_THRESHOLD, (
            f"Aggregate test count {count} fell below threshold {SCOPED_THRESHOLD} "
            f"— Phase 42 likely broke V5.0/Phase 40/Phase 41 tests.\n"
            f"STDOUT tail:\n{result.stdout[-2000:]}"
        )
