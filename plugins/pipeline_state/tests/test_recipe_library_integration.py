"""End-to-end integration tests for RecipeLibrary convergence loop (Phase 41-04).

Verifies the full v6.0 blueprint convergence loop composes correctly:
    调研萃取 → 配方建模 → 定向赛马 → 数据收敛 → 资产化沉淀
    extract    create       (p10b)     update_validation  query_by_structure

These are NOT unit tests — plans 41-01/02/03 already proved each method in
isolation. This plan proves the ASSEMBLY: 12 integration tests covering the
full extract → create → update × 10 → query convergence loop, multi-recipe
ranking, all 3 query modes, JSONL format invariants across the flow,
provenance traceability, degrade resilience, and cross-method consistency.

Uses REAL AssetBus(tmp_path) + REAL RecipeLibrary — NO MOCKS. The file-backed
round-trip is what makes this an integration test.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import pytest

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.recipe_library import RecipeLibrary


# ═══════════════════════════════════════════════════════════════════
# V5.0-verified fixtures (copied from test_recipe_library_extraction.py
# TestFullEpisodeExtractFromV5Fixtures::test_canonical_ep_001_extraction —
# these mirror pipeline-runs/ep-001/.pipeline-assets/ slot .value objects,
# envelope stripped since bus.write re-wraps).
# ═══════════════════════════════════════════════════════════════════

_STORY_FRAMEWORK_FIXTURE = {
    "story_kernel": {
        "kernel_id": "kernel_ep001_001",
        "title_working": "消失的外卖",
        "episode_id": "ep-001",
        "mcmahon_arc": "man_in_a_hole",
        "structural_formula": "独居老人用AI伪造家人声音...",
    },
    "snowflake_artifacts": {
        "snowflake_id": "snowflake_ep001_001",
        "mcmahon_arc_selected": "man_in_a_hole",
        "anchor_validation": "Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓",
    },
    "snyder_beats_summary": [
        "Opening Image (0-3s): 诡异订单特写",
        "Catalyst+Theme (6-9s): '你终于来了'",
        "Midpoint (37-40s): 极性反转",
        "All Is Lost+Dark Night (52-58s): '我知道她们不是真的'",
        "Finale (58-70s): '妈妈,我到了'",
    ],
}

_FINAL_AUDIT_FIXTURE = {
    "total_score": 84,
    "grade": "A",
    "verdict": "PASS",
    "scores": {
        "D1_narrative": 17,
        "D2_emotion": 17,
        "D3_hook": 18,
        "D4_character": 16,
        "D5_completion": 16,
    },
}


# ═══════════════════════════════════════════════════════════════════
# Helpers + fixtures
# ═══════════════════════════════════════════════════════════════════


def _seed_story_framework(bus: AssetBus, framework_dict: dict) -> None:
    """Write story-framework slot (envelope-wrapped by bus.write)."""
    bus.write("story-framework", framework_dict)


def _seed_final_audit(bus: AssetBus, audit_dict: dict) -> None:
    """Write final-audit slot (envelope-wrapped by bus.write)."""
    bus.write("final-audit", audit_dict)


def _make_structure(
    *,
    hook: int = 7,
    sequence: list[str] | None = None,
    tps: list[int] | None = None,
    drop: int = 1,
    ending: str = "resolved",
) -> dict:
    """Build a valid 5-field structure dict (defaults match ep-001 extraction)."""
    return {
        "hook_position_sec": hook,
        "emotion_sequence": sequence if sequence is not None else ["hope", "descent", "crisis", "recovery"],
        "turning_points_sec": tps if tps is not None else [7, 37, 55],
        "emotion_drop_level": drop,
        "ending_state": ending,
    }


@pytest.fixture
def bus(tmp_path: Path) -> AssetBus:
    return AssetBus(tmp_path)


@pytest.fixture
def rl(bus: AssetBus) -> RecipeLibrary:
    return RecipeLibrary(asset_bus=bus)


# ═══════════════════════════════════════════════════════════════════
# TestRecipeLibraryIntegration — 12 end-to-end tests
# ═══════════════════════════════════════════════════════════════════


class TestRecipeLibraryIntegration:
    """End-to-end RecipeLibrary convergence-loop integration tests."""

    # ── Test 1: Full happy path — extract → create → update × 10 → query ──

    def test_full_convergence_loop(self, bus: AssetBus, rl: RecipeLibrary) -> None:
        """Canonical convergence loop (single linear flow, top-to-bottom)."""
        # Stage 1: extract (调研萃取)
        _seed_story_framework(bus, _STORY_FRAMEWORK_FIXTURE)
        _seed_final_audit(bus, _FINAL_AUDIT_FIXTURE)
        structure = rl.extract_structure_from_episode("ep-001")
        assert structure is not None
        assert "emotion_sequence" in structure
        assert structure == {
            "hook_position_sec": 7,
            "emotion_sequence": ["hope", "descent", "crisis", "recovery"],
            "turning_points_sec": [7, 37, 55],
            "emotion_drop_level": 1,
            "ending_state": "resolved",
        }

        # Stage 2: create (配方建模)
        recipe_id = rl.create_recipe(
            genre="Urban Fantasy",
            structure=structure,
            source_episode="ep-001",
        )
        assert recipe_id == "urban-fantasy-001"

        # Stage 3: data convergence (数据收敛) — 10 feedback batches
        # Each batch reports 100 samples at completion_rate=0.50 (consistent
        # feedback). After 10 batches: sample_size=1000, Wilson CI spread ~0.06
        # (well below 0.10 threshold) -> converged=True. Pure-stdlib Wilson
        # math (41-02 _wilson_ci) requires large N for tight CI; the
        # convergence loop models bulk feedback ingest, not 1-by-1 submissions.
        for _ in range(10):
            result = rl.update_validation(
                recipe_id,
                platform="douyin",
                completion_rate=0.50,
                sample_size_delta=100,
            )
            assert result is not None
        converged_recipe = rl.get_recipe(recipe_id)
        assert converged_recipe["validation"]["converged"] is True
        assert converged_recipe["validation"]["sample_size"] == 1000

        # Stage 4: asset precipitation (资产化沉淀) — query returns converged recipe first
        results = rl.query_by_structure(structure)
        assert len(results) >= 1
        top_recipe, top_score = results[0]
        assert top_recipe["recipe_id"] == recipe_id
        assert top_score >= 0.99  # near-exact match

    # ── Test 2: Multiple recipes — query returns correct ranking ──

    def test_query_returns_correct_ranking(self, rl: RecipeLibrary) -> None:
        """3 recipes with progressively different structures — query desc."""
        query_structure = _make_structure(hook=10, tps=[10, 30, 50], drop=2)

        # Recipe A: near query
        rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=10, tps=[10, 30, 50], drop=2),
            source_episode="ep-A",
        )
        # Recipe B: medium distance
        rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=20, tps=[20, 40, 60], drop=3),
            source_episode="ep-B",
        )
        # Recipe C: far
        rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=100, tps=[100, 200, 300], drop=5),
            source_episode="ep-C",
        )

        results = rl.query_by_structure(query_structure, min_score=0.0)
        # Expect at least 3 results, ordered A, B, C descending by score
        assert len(results) >= 3
        ids = [r["recipe_id"] for r, _ in results[:3]]
        assert ids == ["urban-fantasy-001", "urban-fantasy-002", "urban-fantasy-003"]
        # Scores must strictly descend for distinct recipes
        scores = [s for _, s in results[:3]]
        assert scores[0] > scores[1] > scores[2], (
            f"scores not strictly descending: {scores}"
        )

    # ── Test 3: Genre filter returns only matching genre ──

    def test_genre_filter_returns_only_matching(self, rl: RecipeLibrary) -> None:
        rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-A",
        )
        rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=20),
            source_episode="ep-B",
        )
        rl.create_recipe(
            genre="Sci-Fi",
            structure=_make_structure(hook=30),
            source_episode="ep-C",
        )
        results = rl.list_recipes(genre="Urban Fantasy")
        assert len(results) == 2
        for r in results:
            assert r["genre"] == "Urban Fantasy"

    # ── Test 4: Converged filter returns only converged ──

    def test_converged_filter_returns_only_converged(
        self, rl: RecipeLibrary
    ) -> None:
        rid1 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-1",
        )
        rid2 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=20),
            source_episode="ep-2",
        )
        rid3 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=30),
            source_episode="ep-3",
        )
        # Recipe 1: 10 bulk-sample updates -> converged (sample_size=1000)
        for _ in range(10):
            rl.update_validation(
                rid1, platform="douyin", completion_rate=0.50, sample_size_delta=100
            )
        # Recipe 2: 3 updates -> not converged (sample_size=3, below min 10)
        for _ in range(3):
            rl.update_validation(rid2, platform="douyin", completion_rate=0.50)
        # Recipe 3: no updates -> sample_size=0, not converged

        results = rl.list_recipes(converged=True)
        assert len(results) == 1
        assert results[0]["recipe_id"] == rid1

    # ── Test 5: Combined filter — genre + converged ──

    def test_combined_filter_genre_and_converged(self, rl: RecipeLibrary) -> None:
        uf1 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-1",
        )
        rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=20),
            source_episode="ep-2",
        )
        sf1 = rl.create_recipe(
            genre="Sci-Fi",
            structure=_make_structure(hook=30),
            source_episode="ep-3",
        )
        rl.create_recipe(
            genre="Sci-Fi",
            structure=_make_structure(hook=40),
            source_episode="ep-4",
        )
        # Converge 1 Urban Fantasy + 1 Sci-Fi (bulk samples for tight CI)
        for _ in range(10):
            rl.update_validation(
                uf1, platform="douyin", completion_rate=0.50, sample_size_delta=100
            )
        for _ in range(10):
            rl.update_validation(
                sf1, platform="bilibili", completion_rate=0.60, sample_size_delta=100
            )

        # Combined filter: only the converged Urban Fantasy
        results = rl.list_recipes(genre="Urban Fantasy", converged=True)
        assert len(results) == 1
        assert results[0]["recipe_id"] == uf1

    # ── Test 6: Multi-version preservation — full history queryable ──

    def test_multi_version_history_queryable(self, bus: AssetBus, rl: RecipeLibrary) -> None:
        rid = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-1",
        )
        for _ in range(5):
            rl.update_validation(rid, platform="douyin", completion_rate=0.50)

        rows = bus.read_lines("emotion-recipe")
        matching = [r for r in rows if r["recipe_id"] == rid]
        # 1 create + 5 updates = 6 rows
        assert len(matching) == 6
        versions = sorted(r["version"] for r in matching)
        assert versions == [1, 2, 3, 4, 5, 6]
        # Version 3 should have sample_size=2 (1 from create at v1, +1 at v2,
        # +1 at v3 = 3 total — wait: v1=0, v2=1, v3=2, v4=3, v5=4, v6=5)
        v3 = next(r for r in matching if r["version"] == 3)
        assert v3["validation"]["sample_size"] == 2

    # ── Test 7: JSONL format invariants hold across full flow ──

    def test_jsonl_format_invariants(self, bus: AssetBus, rl: RecipeLibrary) -> None:
        """After convergence loop, every line in emotion-recipe.jsonl is valid
        JSON with all 16 required fields and correct types."""
        # Run a small convergence loop
        _seed_story_framework(bus, _STORY_FRAMEWORK_FIXTURE)
        _seed_final_audit(bus, _FINAL_AUDIT_FIXTURE)
        structure = rl.extract_structure_from_episode("ep-001")
        assert structure is not None
        rid = rl.create_recipe(
            genre="Urban Fantasy",
            structure=structure,
            source_episode="ep-001",
        )
        for _ in range(3):
            rl.update_validation(rid, platform="douyin", completion_rate=0.50)

        # Read the RAW file (not via bus.read_lines which already parses)
        jsonl_path = bus._dir / "emotion-recipe.jsonl"
        raw = jsonl_path.read_text(encoding="utf-8")
        lines = [ln for ln in raw.split("\n") if ln.strip()]
        assert len(lines) >= 4  # 1 create + 3 updates

        required_top = {"recipe_id", "version", "genre"}
        required_structure = {
            "hook_position_sec", "emotion_sequence", "turning_points_sec",
            "emotion_drop_level", "ending_state",
        }
        required_validation = {
            "platform", "completion_rate", "confidence_interval",
            "sample_size", "converged",
        }
        required_provenance = {"source_episode", "created", "last_validated"}

        for i, line in enumerate(lines):
            row = json.loads(line)  # raises if not valid JSON
            # Top-level (3)
            assert required_top <= set(row.keys()), (
                f"line {i}: missing top-level fields"
            )
            assert isinstance(row["recipe_id"], str)
            assert isinstance(row["version"], int) and not isinstance(row["version"], bool)
            assert isinstance(row["genre"], str)
            # structure (5)
            struct = row["structure"]
            assert required_structure <= set(struct.keys()), (
                f"line {i}: missing structure fields"
            )
            assert isinstance(struct["hook_position_sec"], int)
            assert isinstance(struct["emotion_sequence"], list)
            assert isinstance(struct["turning_points_sec"], list)
            assert isinstance(struct["emotion_drop_level"], int)
            assert isinstance(struct["ending_state"], str)
            # validation (5)
            val = row["validation"]
            assert required_validation <= set(val.keys()), (
                f"line {i}: missing validation fields"
            )
            assert isinstance(val["platform"], str)
            assert isinstance(val["completion_rate"], (int, float))
            assert isinstance(val["confidence_interval"], str)
            assert isinstance(val["sample_size"], int)
            assert isinstance(val["converged"], bool)
            # provenance (3)
            prov = row["provenance"]
            assert required_provenance <= set(prov.keys()), (
                f"line {i}: missing provenance fields"
            )
            assert isinstance(prov["source_episode"], str)

    # ── Test 8: Provenance traceability (RECIPE-LIB-06) ──

    def test_provenance_traceability(self, rl: RecipeLibrary) -> None:
        _seed_story_framework(rl._bus, _STORY_FRAMEWORK_FIXTURE)
        _seed_final_audit(rl._bus, _FINAL_AUDIT_FIXTURE)
        structure = rl.extract_structure_from_episode("ep-001")
        assert structure is not None
        rid = rl.create_recipe(
            genre="Urban Fantasy",
            structure=structure,
            source_episode="ep-001",
        )
        # Run updates to populate last_validated (bulk samples for convergence)
        for _ in range(10):
            rl.update_validation(
                rid, platform="douyin", completion_rate=0.50, sample_size_delta=100
            )
        recipe = rl.get_recipe(rid)
        prov = recipe["provenance"]
        assert prov["source_episode"] == "ep-001"
        # ISO 8601 parseable
        created_dt = datetime.fromisoformat(prov["created"])
        last_val_dt = datetime.fromisoformat(prov["last_validated"])
        # last_validated is later than (or equal to) created
        assert last_val_dt >= created_dt, (
            f"last_validated ({prov['last_validated']}) < created ({prov['created']})"
        )

    # ── Test 9: Degrade resilience — AssetBus failure doesn't corrupt library ──

    def test_degrade_resilience_bus_failure(self, bus: AssetBus, rl: RecipeLibrary) -> None:
        rid = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-1",
        )
        # Run 5 successful updates
        for _ in range(5):
            result = rl.update_validation(rid, platform="douyin", completion_rate=0.50)
            assert result is not None

        # Snapshot current state
        before = rl.get_recipe(rid)
        assert before["version"] == 6  # 1 create + 5 updates
        assert before["validation"]["sample_size"] == 5

        # Monkeypatch bus.append_line to raise IOError
        original = bus.append_line

        call_count = {"n": 0}

        def broken_append(slot, line_obj):
            call_count["n"] += 1
            if call_count["n"] >= 1:
                raise IOError("simulated bus failure")
            return original(slot, line_obj)

        bus.append_line = broken_append  # type: ignore[assignment]

        # 6th update should return None + log warning (degraded mode)
        with caplog_warning_captured():
            result = rl.update_validation(rid, platform="douyin", completion_rate=0.50)
        assert result is None

        # Restore
        bus.append_line = original  # type: ignore[assignment]

        # Library state unchanged — no partial write corruption
        after = rl.get_recipe(rid)
        assert after["version"] == before["version"]
        assert after["validation"]["sample_size"] == before["validation"]["sample_size"]

    # ── Test 10: Cross-method consistency — get_recipe matches list_recipes ──

    def test_cross_method_consistency(self, rl: RecipeLibrary) -> None:
        rid1 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-1",
        )
        rid2 = rl.create_recipe(
            genre="Sci-Fi",
            structure=_make_structure(hook=50),
            source_episode="ep-2",
        )
        rid3 = rl.create_recipe(
            genre="Comedy",
            structure=_make_structure(hook=20, drop=3),
            source_episode="ep-3",
        )
        # Add updates to introduce version > 1
        rl.update_validation(rid1, platform="douyin", completion_rate=0.5)
        rl.update_validation(rid2, platform="bilibili", completion_rate=0.7)

        listed = {r["recipe_id"]: r for r in rl.list_recipes()}
        assert set(listed.keys()) == {rid1, rid2, rid3}

        for rid in [rid1, rid2, rid3]:
            got = rl.get_recipe(rid)
            listed_row = listed[rid]
            # latest-version dicts must be identical (deep equality)
            assert got == listed_row, (
                f"drift between get_recipe and list_recipes for {rid}"
            )

    # ── Test 11: recipe_id sequencing across genres — no collision ──

    def test_recipe_id_sequencing_no_collision(self, rl: RecipeLibrary) -> None:
        uf1 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(),
            source_episode="ep-1",
        )
        uf2 = rl.create_recipe(
            genre="Urban Fantasy",
            structure=_make_structure(hook=20),
            source_episode="ep-2",
        )
        sf1 = rl.create_recipe(
            genre="Sci-Fi",
            structure=_make_structure(hook=30),
            source_episode="ep-3",
        )
        assert uf1 == "urban-fantasy-001"
        assert uf2 == "urban-fantasy-002"
        assert sf1 == "sci-fi-001"
        # All unique
        assert len({uf1, uf2, sf1}) == 3
        # All match the <slug>-<NNN> pattern
        for rid in [uf1, uf2, sf1]:
            assert re.match(r"^[a-z]+(?:-[a-z]+)*-\d{3}$", rid), (
                f"recipe_id {rid} does not match <slug>-<NNN> pattern"
            )

    # ── Test 12: Empty library query returns empty list ──

    def test_empty_library_returns_empty(self, tmp_path: Path) -> None:
        bus = AssetBus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        # query_by_structure on empty library
        results = rl.query_by_structure(_make_structure())
        assert results == []
        # list_recipes on empty library
        listed = rl.list_recipes()
        assert listed == []


# ═══════════════════════════════════════════════════════════════════
# Helper context manager for caplog warning capture in Test 9
# (kept local to avoid pytest fixture scope complications)
# ═══════════════════════════════════════════════════════════════════


class _WarningCapture:
    """Context manager that captures logging.WARNING records."""

    def __init__(self) -> None:
        self.records: list[logging.LogRecord] = []

    def __enter__(self) -> "_WarningCapture":
        self._handler = logging.Handler()
        self._handler.emit = self.records.append  # type: ignore[assignment]
        logger = logging.getLogger("plugins.pipeline_state.recipe_library")
        logger.addHandler(self._handler)
        return self

    def __exit__(self, *exc) -> None:
        logger = logging.getLogger("plugins.pipeline_state.recipe_library")
        logger.removeHandler(self._handler)


def caplog_warning_captured() -> _WarningCapture:
    return _WarningCapture()
