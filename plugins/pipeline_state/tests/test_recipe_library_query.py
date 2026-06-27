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

import pytest

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
