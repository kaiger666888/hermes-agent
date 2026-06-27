"""test_recipe_library_query.py — Phase 41-03 tests.

Covers:
  Task 1 — similarity helpers (cosine + jaccard + structure→vector mapping)
            in `TestSimilarityHelpers` (14 tests).
  Task 2 — RecipeLibrary.query_by_structure public method
            in `TestRecipeLibraryQuery` (15 tests).

Similarity algorithm lock (CONTEXT.md):
    score = 0.7 * cosine(numerical) + 0.3 * jaccard(emotion_sequence)
    pure stdlib (math.sqrt + set built-in — NO scipy/numpy/sklearn).
"""
from __future__ import annotations

import inspect
from typing import Any

import pytest

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.recipe_library import (
    RecipeLibrary,
    _cosine_similarity,
    _jaccard_similarity,
    _structure_to_numerical_vector,
)


# ─── Task 1: similarity helper unit tests ──────────────────────────────


class TestSimilarityHelpers:
    """Pure-std lib similarity helpers (cosine + jaccard + vector mapping)."""

    # ── cosine similarity ──────────────────────────────────────────────

    def test_cosine_identical_vectors_is_one(self):
        # Direction identical -> cosine == 1.0
        assert _cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0, abs=1e-9)

    def test_cosine_orthogonal_vectors_is_zero(self):
        # 90-degree angle -> dot product zero -> cosine == 0.0
        assert _cosine_similarity([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]) == pytest.approx(0.0, abs=1e-9)

    def test_cosine_opposite_vectors_is_negative_one(self):
        # Anti-parallel -> cosine == -1.0
        assert _cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0, abs=1e-9)

    def test_cosine_zero_vector_returns_zero_no_divide_by_zero(self):
        # Either norm == 0 -> early return 0.0 (threat T-41-14 mitigation)
        assert _cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == pytest.approx(0.0, abs=1e-9)

    def test_cosine_different_magnitude_same_direction_is_one(self):
        # Magnitude shouldn't matter for cosine — only direction
        assert _cosine_similarity([1.0, 1.0], [2.0, 2.0]) == pytest.approx(1.0, abs=1e-9)

    # ── jaccard similarity ─────────────────────────────────────────────

    def test_jaccard_identical_sets_is_one(self):
        assert _jaccard_similarity(["a", "b", "c"], ["a", "b", "c"]) == pytest.approx(1.0, abs=1e-9)

    def test_jaccard_disjoint_sets_is_zero(self):
        assert _jaccard_similarity(["a", "b"], ["c", "d"]) == pytest.approx(0.0, abs=1e-9)

    def test_jaccard_partial_overlap_is_one_third(self):
        # intersection {b} = 1, union {a,b,c} = 3 -> 1/3
        assert _jaccard_similarity(["a", "b"], ["b", "c"]) == pytest.approx(1.0 / 3.0, abs=1e-9)

    def test_jaccard_empty_lists_is_zero(self):
        # Union empty -> 0.0 (no division by zero)
        assert _jaccard_similarity([], []) == pytest.approx(0.0, abs=1e-9)

    def test_jaccard_order_insensitive(self):
        # Set semantics -> [a,b] and [b,a] are equivalent
        assert _jaccard_similarity(["a", "b"], ["b", "a"]) == pytest.approx(1.0, abs=1e-9)

    def test_jaccard_duplicates_collapse_via_set(self):
        # Duplicates must not inflate the score
        assert _jaccard_similarity(["a", "a", "b"], ["a", "b"]) == pytest.approx(1.0, abs=1e-9)

    # ── structure -> numerical vector mapping ─────────────────────────

    def test_structure_to_vector_with_full_structure(self):
        # mean([3, 15, 30, 55]) = (3+15+30+55)/4 = 103/4 = 25.75
        structure = {
            "hook_position_sec": 3,
            "turning_points_sec": [3, 15, 30, 55],
            "emotion_drop_level": 4,
        }
        assert _structure_to_numerical_vector(structure) == [3.0, 25.75, 4.0]

    def test_structure_to_vector_with_empty_turning_points(self):
        # Empty turning_points list -> mean 0.0 (degrade gracefully)
        structure = {
            "hook_position_sec": 3,
            "turning_points_sec": [],
            "emotion_drop_level": 4,
        }
        assert _structure_to_numerical_vector(structure) == [3.0, 0.0, 4.0]

    # ── pure-stdlib inspection (threat T-41-15 mitigation) ────────────

    def test_similarity_helpers_use_pure_stdlib(self):
        """Source must use math.sqrt / set built-in and contain no
        third-party scientific-library tokens (scipy / numpy / sklearn)."""
        forbidden = ("scipy", "numpy", "sklearn")

        cosine_src = inspect.getsource(_cosine_similarity)
        assert "math.sqrt" in cosine_src, "cosine helper must use math.sqrt"
        for tok in forbidden:
            assert tok not in cosine_src, f"_cosine_similarity source contains forbidden token {tok!r}"

        jaccard_src = inspect.getsource(_jaccard_similarity)
        # Jaccard uses the `set(...)` built-in; ensure no forbidden imports leak in.
        assert "set(" in jaccard_src, "jaccard helper must use set() built-in"
        for tok in forbidden:
            assert tok not in jaccard_src, f"_jaccard_similarity source contains forbidden token {tok!r}"


# ─── Task 2: query_by_structure public method tests ───────────────────


def _fresh_bus(tmp_path) -> AssetBus:
    """Construct a real AssetBus over the test tmp_path."""
    return AssetBus(tmp_path)


# Canonical structure for recipe creation (matches test_recipe_library.py
# fixture — kept local here so the query tests are self-contained).
_BASE_STRUCTURE: dict[str, Any] = {
    "hook_position_sec": 3,
    "emotion_sequence": ["suppress", "thrill", "doubt", "thrill"],
    "turning_points_sec": [3, 15, 30, 55],
    "emotion_drop_level": 4,
    "ending_state": "new_suspense",
}


class TestRecipeLibraryQuery:
    """query_by_structure — combined cosine+jaccard ranking + top_k/min_score."""

    # ── Test 1: empty library returns empty list ──────────────────────

    def test_empty_library_returns_empty_list(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        result = rl.query_by_structure(_BASE_STRUCTURE)
        assert result == []

    # ── Test 2: exact match -> score 1.0 ranked first ─────────────────

    def test_exact_match_scores_one(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rid = rl.create_recipe("Urban Fantasy", _BASE_STRUCTURE, "ep-001")

        result = rl.query_by_structure(_BASE_STRUCTURE)
        assert len(result) == 1
        recipe, score = result[0]
        assert recipe["recipe_id"] == rid
        # cosine=1.0 (identical vector) + jaccard=1.0 (identical set) -> 1.0
        assert score == pytest.approx(1.0, abs=1e-9)

    # ── Test 3: ranking — most similar first ──────────────────────────

    def test_ranking_most_similar_first(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = {
            "hook_position_sec": 3,
            "emotion_sequence": ["suppress", "thrill", "doubt", "thrill"],
            "turning_points_sec": [3, 15, 30, 55],
            "emotion_drop_level": 4,
            "ending_state": "new_suspense",
        }
        # near: identical structure
        rl.create_recipe("Near", query, "ep-near")
        # medium: differs in turning_points mean only
        medium_struct = dict(query)
        medium_struct["turning_points_sec"] = [10, 25, 40, 70]  # mean ~36.25 vs 25.75
        rl.create_recipe("Medium", medium_struct, "ep-medium")
        # far: differs in everything
        far_struct = {
            "hook_position_sec": 30,
            "emotion_sequence": ["joy", "calm", "wonder", "peace"],
            "turning_points_sec": [50, 100, 150, 200],
            "emotion_drop_level": 1,
            "ending_state": "resolved",
        }
        rl.create_recipe("Far", far_struct, "ep-far")

        # min_score=0.0 returns all (subject to ranking)
        result = rl.query_by_structure(query, min_score=0.0)
        assert len(result) == 3
        # Ranking descending: near > medium > far
        assert result[0][0]["genre"] == "Near"
        assert result[1][0]["genre"] == "Medium"
        assert result[2][0]["genre"] == "Far"
        # Scores monotonically non-increasing
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    # ── Test 4: min_score default filters out low-similarity ──────────

    def test_min_score_default_filters_low_similarity(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        # 2 high-similarity (identical structure)
        rl.create_recipe("Match A", dict(query), "ep-a1")
        rl.create_recipe("Match B", dict(query), "ep-a2")
        # 3 low-similarity (different in every field)
        for i in range(3):
            rl.create_recipe(
                f"NonMatch {i}",
                {
                    "hook_position_sec": 60,
                    "emotion_sequence": ["unrelated", "tokens", "here", "now"],
                    "turning_points_sec": [80, 120, 160, 200],
                    "emotion_drop_level": 1,
                    "ending_state": "resolved",
                },
                f"ep-nm-{i}",
            )

        # Default min_score=0.7 — should return only the 2 identical matches
        result = rl.query_by_structure(query)
        assert len(result) == 2
        for recipe, score in result:
            assert score >= 0.7
            assert recipe["genre"].startswith("Match")

    # ── Test 5: min_score explicit — stricter ─────────────────────────

    def test_min_score_explicit_stricter(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        # identical (score 1.0)
        rl.create_recipe("Perfect", dict(query), "ep-perfect")
        # Partial match: share emotion_sequence (jaccard=1.0) but a numerical
        # vector clearly off-direction from the query. We zero out
        # turning_points_sec (pulls the dominant middle component to 0), so
        # cosine drops well below the 0.857 threshold that would put the
        # combined score above 0.9. Verifiable: query_vec=[3,25.75,4]
        # (||q||≈26.23); candidate_vec=[3,0,4] (||c||=5); dot=25; cos≈0.19;
        # combined = 0.7*0.19 + 0.3*1.0 ≈ 0.43.
        partial = {
            "hook_position_sec": 3,
            "emotion_sequence": list(query["emotion_sequence"]),  # jaccard=1.0
            "turning_points_sec": [],  # mean 0 — orthogonal-ish pull
            "emotion_drop_level": 4,
            "ending_state": "new_suspense",
        }
        rl.create_recipe("Partial", partial, "ep-partial")

        strict = rl.query_by_structure(query, min_score=0.9)
        loose = rl.query_by_structure(query, min_score=0.0)
        # Strict (>=0.9) returns only Perfect; loose (>=0.0) returns both
        assert len(strict) == 1
        assert strict[0][0]["genre"] == "Perfect"
        assert len(loose) == 2
        # Sanity: strict is a subset of loose
        strict_ids = {r["recipe_id"] for r, _ in strict}
        loose_ids = {r["recipe_id"] for r, _ in loose}
        assert strict_ids.issubset(loose_ids)

    # ── Test 6: min_score=0.0 returns everything (subject to top_k) ───

    def test_min_score_zero_returns_everything(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        for i in range(4):
            rl.create_recipe(
                f"R{i}",
                {
                    "hook_position_sec": i * 10,
                    "emotion_sequence": [f"e{i}a", f"e{i}b"],
                    "turning_points_sec": [i, i * 2],
                    "emotion_drop_level": (i % 5) + 1,
                    "ending_state": "cliffhanger",
                },
                f"ep-{i}",
            )

        # top_k large enough to admit all 4
        result = rl.query_by_structure(query, min_score=0.0, top_k=100)
        assert len(result) == 4

    # ── Test 7: top_k default caps at 5 ───────────────────────────────

    def test_top_k_default_caps_at_five(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        # 10 identical recipes — all score 1.0 (well above default min_score)
        for i in range(10):
            rl.create_recipe(f"Match{i}", dict(query), f"ep-{i}")

        result = rl.query_by_structure(query)  # default top_k=5, min_score=0.7
        assert len(result) == 5
        for _, score in result:
            assert score == pytest.approx(1.0, abs=1e-9)

    # ── Test 8: top_k explicit cap ─────────────────────────────────────

    def test_top_k_explicit_cap(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        for i in range(10):
            rl.create_recipe(f"Match{i}", dict(query), f"ep-{i}")

        result = rl.query_by_structure(query, top_k=3, min_score=0.0)
        assert len(result) == 3

    # ── Test 9: top_k larger than library ─────────────────────────────

    def test_top_k_larger_than_library(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        for i in range(3):
            rl.create_recipe(f"R{i}", dict(query), f"ep-{i}")

        result = rl.query_by_structure(query, top_k=100, min_score=0.0)
        assert len(result) == 3  # no error, just all available

    # ── Test 10: combined score formula = 0.7*cosine + 0.3*jaccard ────

    def test_combined_score_formula(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        # Construct a candidate whose combined score we can verify numerically.
        # Keep emotion_sequence identical (forces jaccard=1.0) and zero out
        # turning_points_sec (forces the middle vector component to 0.0),
        # giving a deterministic cosine we can compute via the helpers.
        candidate = {
            "hook_position_sec": 3,
            "emotion_sequence": list(query["emotion_sequence"]),  # jaccard=1.0
            "turning_points_sec": [],  # mean 0 — pulls middle component to 0
            "emotion_drop_level": 4,
            "ending_state": "new_suspense",
        }
        rl.create_recipe("Formula", candidate, "ep-formula")

        # Verify the helper-derived cosine + jaccard + combined score.
        q_vec = _structure_to_numerical_vector(query)
        c_vec = _structure_to_numerical_vector(candidate)
        cos = _cosine_similarity(q_vec, c_vec)
        jac = _jaccard_similarity(
            query["emotion_sequence"], candidate["emotion_sequence"]
        )
        expected = 0.7 * cos + 0.3 * jac

        # Default min_score=0.7 should NOT return this (expected < 0.7).
        default_result = rl.query_by_structure(query)
        assert all(r["recipe_id"] != "formula-001" for r, _ in default_result), \
            "candidate below default min_score=0.7 should be filtered out"

        # min_score=0.4 surfaces it; score matches expected formula output.
        loose_result = rl.query_by_structure(query, min_score=0.4)
        assert len(loose_result) == 1
        recipe, score = loose_result[0]
        assert recipe["recipe_id"] == "formula-001"
        assert score == pytest.approx(expected, abs=1e-9)
        # And jaccard was indeed 1.0 (sanity)
        assert jac == pytest.approx(1.0, abs=1e-9)

    # ── Test 11: latest version only — multi-version doesn't double-count ─

    def test_latest_version_only_no_double_count(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        query = _BASE_STRUCTURE
        rl.create_recipe("Urban Fantasy", _BASE_STRUCTURE, "ep-001")
        # Manually append versions 2 and 3 (bypassing update_validation to
        # avoid needing platform/completion_rate plumbing for this test).
        v1 = bus.read_lines("emotion-recipe")[0]
        import copy as _copy
        for new_ver in (2, 3):
            new_row = _copy.deepcopy(v1)
            new_row["version"] = new_ver
            bus.append_line("emotion-recipe", new_row)

        # list_recipes returns only the latest (v3) — query should match that
        result = rl.query_by_structure(query, min_score=0.0)
        assert len(result) == 1, "multi-version recipe must count once"
        assert result[0][0]["version"] == 3

    # ── Test 12: returns (recipe, score) tuples with float in [0,1] ───

    def test_returns_recipe_score_tuples(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Match", _BASE_STRUCTURE, "ep-001")

        result = rl.query_by_structure(_BASE_STRUCTURE)
        assert len(result) == 1
        recipe, score = result[0]
        # recipe is a full dict with all 16 fields
        assert isinstance(recipe, dict)
        for top_field in ("recipe_id", "version", "genre", "structure", "validation", "provenance"):
            assert top_field in recipe
        # score is a float in [0.0, 1.0]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    # ── Test 13: structure_query missing fields — degrade to defaults ─

    def test_structure_query_missing_fields_degrades(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        # Seed one recipe — query against a structure missing most fields.
        rl.create_recipe("Match", _BASE_STRUCTURE, "ep-001")

        partial_query = {"hook_position_sec": 3}  # missing emotion_seq, tp, drop
        # Must NOT crash — missing fields default to 0/[].
        result = rl.query_by_structure(partial_query, min_score=0.0)
        assert isinstance(result, list)
        # The query's emotion_sequence is missing -> treated as [] -> jaccard
        # against the recipe's ["suppress",...] returns 0 (disjoint with empty).
        # Numerical vector is [3.0, 0.0, 0.0] vs recipe [3.0, 25.75, 4.0].
        if result:
            _, score = result[0]
            assert 0.0 <= score <= 1.0

    # ── Test 14: deterministic ordering on ties (stable sort) ─────────

    def test_tiebreaker_stable_sort_preserves_insertion_order(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        query = _BASE_STRUCTURE

        # Two recipes with IDENTICAL structure (will tie at score=1.0).
        # Insertion order: First-001, then Second-001.
        first_rid = rl.create_recipe("First", dict(query), "ep-1")
        second_rid = rl.create_recipe("Second", dict(query), "ep-2")

        result = rl.query_by_structure(query, min_score=0.0)
        assert len(result) == 2
        # Tied scores
        assert result[0][1] == pytest.approx(result[1][1], abs=1e-9)
        # First-inserted appears first (Python sorted() is stable)
        assert result[0][0]["recipe_id"] == first_rid
        assert result[1][0]["recipe_id"] == second_rid

    # ── Test 15: zero-magnitude query vector — all structures zeroed ─

    def test_zero_magnitude_query_vector_returns_empty(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Match", _BASE_STRUCTURE, "ep-001")

        zero_query = {
            "hook_position_sec": 0,
            "turning_points_sec": [],
            "emotion_drop_level": 0,
            "emotion_sequence": [],
        }
        # cosine component is 0.0 (zero vector guard); jaccard also 0.0
        # (empty vs non-empty -> disjoint). Combined = 0.0 < default 0.7.
        result = rl.query_by_structure(zero_query)
        assert result == [], "zero-magnitude query vector -> score 0.0 -> filtered"

    # ── Threat T-41-18 mitigation: input validation ───────────────────

    def test_invalid_top_k_raises_value_error(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        with pytest.raises(ValueError, match="top_k"):
            rl.query_by_structure(_BASE_STRUCTURE, top_k=0)
        with pytest.raises(ValueError, match="top_k"):
            rl.query_by_structure(_BASE_STRUCTURE, top_k=-1)

    def test_invalid_min_score_raises_value_error(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        with pytest.raises(ValueError, match="min_score"):
            rl.query_by_structure(_BASE_STRUCTURE, min_score=-0.1)
        with pytest.raises(ValueError, match="min_score"):
            rl.query_by_structure(_BASE_STRUCTURE, min_score=1.5)
