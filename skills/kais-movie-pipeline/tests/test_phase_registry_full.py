"""test_phase_registry_full.py — Phase 36-05 Task 2: PHASE_REGISTRY full DAG.

Verifies that ``pipeline.phases.PHASE_REGISTRY`` contains all 13 V8.6 phase
entries (p01..p13) in DAG order with correct ``depends_on`` chain.

These tests do NOT clear the registry (unlike test_runner.py's fake_registry
fixture) — they assert on the real Phase 36-05 production registry. The
conftest.py sys.path setup makes ``pipeline`` importable.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_p01_unit).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import PHASE_REGISTRY  # noqa: E402


# The canonical 13-phase V8.6 DAG in order (Phase 35 + Phase 36).
EXPECTED_PHASE_IDS: list[str] = [
    "p01_hook_topic",
    "p02_outline",
    "p03_script_audit",
    "p04_character_design",
    "p05_pain_discovery",
    "p06_spatio_temporal_script",
    "p07_scene_generation",
    "p08_scene_selection",
    "p09_shot_breakdown",
    "p10_voice",
    "p11_video_render",
    "p12_composition",
    "p13_delivery",
]


class TestPhaseRegistryFullDag:
    def test_phase_registry_has_13_entries(self):
        """After Phase 36-05, the registry must list all 13 V8.6 phases."""
        assert len(PHASE_REGISTRY) == 13, (
            f"PHASE_REGISTRY should have 13 entries (p01..p13); "
            f"got {len(PHASE_REGISTRY)}"
        )

    def test_phase_registry_order_is_dag(self):
        """Phase ids in registry must match the canonical V8.6 DAG order."""
        ids = [entry["id"] for entry in PHASE_REGISTRY]
        assert ids == EXPECTED_PHASE_IDS, (
            f"phase order mismatch;\n  expected: {EXPECTED_PHASE_IDS}\n  got:      {ids}"
        )
        # Sanity: first + last anchored.
        assert ids[0] == "p01_hook_topic"
        assert ids[-1] == "p13_delivery"

    def test_phase_registry_depends_on_chain(self):
        """Each entry's depends_on must reference the immediately-preceding phase.

        Linear DAG: p0N depends_on [p0(N-1)]. p01 has empty depends_on.
        Branching lives only inside p11 (intra-phase shot-level fan-out, not
        expressed in the registry).
        """
        for idx, entry in enumerate(PHASE_REGISTRY):
            phase_id = entry["id"]
            depends_on = entry.get("depends_on", [])
            if idx == 0:
                assert depends_on == [], (
                    f"{phase_id} is the DAG root; depends_on must be empty, "
                    f"got {depends_on}"
                )
            else:
                expected_prev = EXPECTED_PHASE_IDS[idx - 1]
                assert depends_on == [expected_prev], (
                    f"{phase_id} must depend_on [{expected_prev!r}] "
                    f"(linear DAG); got {depends_on}"
                )

    def test_phase_registry_modules_all_importable(self):
        """Every registry ``module`` value must be a real imported module with run()."""
        for entry in PHASE_REGISTRY:
            module = entry["module"]
            assert hasattr(module, "run"), (
                f"module for {entry['id']} must expose a run() callable"
            )
            assert callable(module.run), (
                f"module.run for {entry['id']} must be callable"
            )

    def test_phase_registry_module_constants_match_id(self):
        """Each phase module's PHASE_ID constant must match its registry id.

        Catches the classic bug where a module is wired under the wrong id
        (e.g. p10_voice module bound to the p09_shot_breakdown entry).
        """
        for entry in PHASE_REGISTRY:
            module = entry["module"]
            module_phase_id = getattr(module, "PHASE_ID", None)
            assert module_phase_id == entry["id"], (
                f"registry id {entry['id']!r} != module.PHASE_ID "
                f"{module_phase_id!r} (module mis-wired)"
            )

    def test_phase_registry_entries_well_formed(self):
        """Every entry must have id/module/depends_on keys with correct types."""
        for entry in PHASE_REGISTRY:
            assert isinstance(entry, dict), f"entry must be dict, got {type(entry)}"
            assert "id" in entry and isinstance(entry["id"], str)
            assert "module" in entry
            assert "depends_on" in entry and isinstance(entry["depends_on"], list)

    def test_phase_registry_no_duplicates(self):
        """No duplicate phase ids allowed (would corrupt resume cursor)."""
        ids = [entry["id"] for entry in PHASE_REGISTRY]
        assert len(ids) == len(set(ids)), (
            f"duplicate phase ids in registry: {ids}"
        )

    def test_all_thirteen_phase_modules_importable_by_long_name(self):
        """All 13 canonical module names must be importable from pipeline.phases."""
        import pipeline.phases as phases_mod

        for phase_id in EXPECTED_PHASE_IDS:
            assert hasattr(phases_mod, phase_id), (
                f"pipeline.phases must re-export {phase_id} under its long name"
            )

    def test_module_exposes_required_slots_constants(self):
        """Each phase module must expose the Phase 35 template constants.

        PHASE_ID / EXPERT / INPUT_SLOTS / OUTPUT_SLOTS / GATE_ID — runner +
        per-phase unit tests rely on these. p11 also exposes parallel_shots
        kwarg on run() but that's a signature check, not a module constant.
        """
        required = ["PHASE_ID", "EXPERT", "INPUT_SLOTS", "OUTPUT_SLOTS", "GATE_ID"]
        for entry in PHASE_REGISTRY:
            module = entry["module"]
            for const in required:
                assert hasattr(module, const), (
                    f"{entry['id']} module missing required constant {const}"
                )
