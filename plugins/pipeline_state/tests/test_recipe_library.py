"""test_recipe_library.py — Phase 41-01 Task 2 (TDD RED→GREEN).

Unit tests for ``RecipeLibrary`` (3 of 5 core methods + helpers):
  - create_recipe (RECIPE-LIB-01)
  - get_recipe   (RECIPE-LIB-01)
  - list_recipes (RECIPE-LIB-01, RECIPE-LIB-05)
  - _slugify     (RECIPE-LIB-06 — recipe_id naming)
  - recipe_id sequencing (RECIPE-LIB-06)

JSONL schema strict (RECIPE-LIB-02): 16 fields, types enforced.
Provenance chain (RECIPE-LIB-06): source_episode present.
Multi-version semantics: latest by default, specific on request.
Degrade path: returns None + logs warning (mirror creative_history.py).

Tests use real AssetBus instances backed by pytest tmp_path — no mocks.
Version=2 rows for Test 8 / Test 13 are seeded manually via bus.append_line
to prove the version-handling logic without depending on Phase 41-02.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.recipe_library import RecipeLibrary, _slugify


# ─── Shared structure fixture ──────────────────────────────────────────

VALID_STRUCTURE: dict[str, Any] = {
    "hook_position_sec": 3,
    "emotion_sequence": ["suppress", "thrill", "doubt", "thrill"],
    "turning_points_sec": [3, 15, 30, 55],
    "emotion_drop_level": 4,
    "ending_state": "new_suspense",
}


def _fresh_bus(tmp_path) -> AssetBus:
    """Construct a real AssetBus over the test tmp_path."""
    return AssetBus(tmp_path)


# ═══════════════════════════════════════════════════════════════════
# Test 1: constructor signature — kw-only asset_bus, raises on None
# ═══════════════════════════════════════════════════════════════════
class TestConstructor:
    def test_kw_only_asset_bus_succeeds(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        assert rl is not None

    def test_asset_bus_none_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="asset_bus required"):
            RecipeLibrary(asset_bus=None)

    def test_positional_asset_bus_raises_type_error(self, tmp_path):
        """Constructor is kw-only — positional asset_bus must TypeError."""
        bus = _fresh_bus(tmp_path)
        with pytest.raises(TypeError):
            RecipeLibrary(bus)  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════
# Tests 2-5: create_recipe + recipe_id sequencing
# ═══════════════════════════════════════════════════════════════════
class TestCreateRecipe:
    def test_create_recipe_returns_recipe_id(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        rid = rl.create_recipe(
            genre="Urban Fantasy",
            structure=VALID_STRUCTURE,
            source_episode="ep-001",
        )
        assert rid == "urban-fantasy-001"

    def test_create_recipe_writes_version_1_row(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rid = rl.create_recipe(
            genre="Urban Fantasy",
            structure=VALID_STRUCTURE,
            source_episode="ep-001",
        )

        rows = bus.read_lines("emotion-recipe")
        assert len(rows) == 1
        row = rows[0]

        # Top-level fields
        assert row["recipe_id"] == rid == "urban-fantasy-001"
        assert row["version"] == 1
        assert row["genre"] == "Urban Fantasy"

        # structure copied from input (all 5 fields)
        assert row["structure"] == VALID_STRUCTURE

        # validation initial values (5 fields)
        val = row["validation"]
        assert val["platform"] == ""
        assert val["completion_rate"] == 0.0
        assert val["confidence_interval"] == "±0%"
        assert val["sample_size"] == 0
        assert val["converged"] is False

        # provenance (3 fields)
        prov = row["provenance"]
        assert prov["source_episode"] == "ep-001"
        assert isinstance(prov["created"], str) and len(prov["created"]) > 0
        assert prov["last_validated"] is None

    def test_recipe_id_sequencing_same_genre(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        rid1 = rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")
        rid2 = rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-002")
        assert rid1 == "urban-fantasy-001"
        assert rid2 == "urban-fantasy-002"

    def test_recipe_id_sequencing_different_genre(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-002")
        rid3 = rl.create_recipe("Sci-Fi Thriller", VALID_STRUCTURE, "ep-003")
        assert rid3 == "sci-fi-thriller-001"


# ═══════════════════════════════════════════════════════════════════
# Test 6: slugify — Chinese genre falls back to "recipe"
# ═══════════════════════════════════════════════════════════════════
class TestSlugifyChineseFallback:
    def test_chinese_genre_falls_back_to_recipe_slug(self, tmp_path):
        """All-non-ASCII genre → empty slug → fallback 'recipe' → recipe-001."""
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        rid = rl.create_recipe(
            genre="都市奇幻·轻喜剧",
            structure=VALID_STRUCTURE,
            source_episode="ep-001",
        )
        assert rid == "recipe-001"


# ═══════════════════════════════════════════════════════════════════
# Test 7: _slugify direct calls — whitespace, special chars, hyphens
# ═══════════════════════════════════════════════════════════════════
class TestSlugifyDirect:
    def test_whitespace_and_special_chars(self):
        assert _slugify("  Urban   Fantasy!!  ") == "urban-fantasy"

    def test_consecutive_hyphens_collapsed(self):
        assert _slugify("A---B") == "a-b"

    def test_empty_string_returns_recipe_fallback(self):
        assert _slugify("") == "recipe"

    def test_all_chinese_returns_recipe_fallback(self):
        assert _slugify("都市奇幻") == "recipe"

    def test_mixed_alpha_and_chinese_keeps_alpha(self):
        # ASCII parts preserved; Chinese stripped; result non-empty → no fallback
        assert _slugify("Urban 奇幻") == "urban"


# ═══════════════════════════════════════════════════════════════════
# Tests 8-10: get_recipe — latest, specific version, unknown
# ═══════════════════════════════════════════════════════════════════
class TestGetRecipe:
    def test_get_recipe_returns_latest_by_default(self, tmp_path):
        """Manually seed v1 + v2 rows; get_recipe returns v2."""
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")

        # Manually append a v2 row (simulates Phase 41-02 update_validation)
        rows = bus.read_lines("emotion-recipe")
        v1 = rows[0]
        v2 = dict(v1)
        v2["version"] = 2
        v2["validation"] = dict(v1["validation"])
        v2["validation"]["sample_size"] = 5
        bus.append_line("emotion-recipe", v2)

        latest = rl.get_recipe("urban-fantasy-001")
        assert latest is not None
        assert latest["version"] == 2
        assert latest["validation"]["sample_size"] == 5

    def test_get_recipe_with_explicit_version(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")

        rows = bus.read_lines("emotion-recipe")
        v1 = rows[0]
        v2 = dict(v1)
        v2["version"] = 2
        bus.append_line("emotion-recipe", v2)

        specific = rl.get_recipe("urban-fantasy-001", version=1)
        assert specific is not None
        assert specific["version"] == 1

    def test_get_recipe_unknown_raises_key_error(self, tmp_path):
        rl = RecipeLibrary(asset_bus=_fresh_bus(tmp_path))
        with pytest.raises(KeyError, match="recipe_id not found"):
            rl.get_recipe("nonexistent-999")


# ═══════════════════════════════════════════════════════════════════
# Tests 11-14: list_recipes — no filter / genre / converged / combined
# ═══════════════════════════════════════════════════════════════════
class TestListRecipes:
    def _seed_three_recipes(self, tmp_path):
        """Helper: seed 3 recipes across 2 genres; return RecipeLibrary."""
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-002")
        rl.create_recipe("Sci-Fi Thriller", VALID_STRUCTURE, "ep-003")
        return rl

    def test_list_no_filter_returns_latest_per_recipe_id(self, tmp_path):
        rl = self._seed_three_recipes(tmp_path)
        results = rl.list_recipes()
        assert len(results) == 3
        ids = {r["recipe_id"] for r in results}
        assert ids == {"urban-fantasy-001", "urban-fantasy-002", "sci-fi-thriller-001"}

    def test_list_genre_filter(self, tmp_path):
        rl = self._seed_three_recipes(tmp_path)
        results = rl.list_recipes(genre="Urban Fantasy")
        assert len(results) == 2
        assert all(r["genre"] == "Urban Fantasy" for r in results)

    def test_list_converged_filter(self, tmp_path):
        """Seed recipes, manually append v2 with converged=True for one."""
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")
        rl.create_recipe("Sci-Fi Thriller", VALID_STRUCTURE, "ep-002")

        # Mark urban-fantasy-001 as converged by appending a v2 row
        rows = bus.read_lines("emotion-recipe")
        v1_uf = rows[0]
        v2_uf = dict(v1_uf)
        v2_uf["version"] = 2
        v2_uf["validation"] = dict(v1_uf["validation"])
        v2_uf["validation"]["converged"] = True
        bus.append_line("emotion-recipe", v2_uf)

        converged = rl.list_recipes(converged=True)
        assert len(converged) == 1
        assert converged[0]["recipe_id"] == "urban-fantasy-001"
        assert converged[0]["validation"]["converged"] is True

    def test_list_combined_genre_and_converged_filter(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")
        rl.create_recipe("Sci-Fi Thriller", VALID_STRUCTURE, "ep-002")

        # Mark BOTH as converged via v2 rows
        rows = bus.read_lines("emotion-recipe")
        for v1 in rows:
            v2 = dict(v1)
            v2["version"] = 2
            v2["validation"] = dict(v1["validation"])
            v2["validation"]["converged"] = True
            bus.append_line("emotion-recipe", v2)

        # Combined filter
        uf_converged = rl.list_recipes(genre="Urban Fantasy", converged=True)
        assert len(uf_converged) == 1
        assert uf_converged[0]["recipe_id"] == "urban-fantasy-001"


# ═══════════════════════════════════════════════════════════════════
# Test 15: full schema strict — 16 fields, correct types
# ═══════════════════════════════════════════════════════════════════
class TestSchemaStrict:
    def test_full_schema_16_fields_correct_types(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)
        rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")

        rows = bus.read_lines("emotion-recipe")
        assert len(rows) == 1
        r = rows[0]

        # Top-level (3 fields)
        assert isinstance(r["recipe_id"], str)
        assert isinstance(r["version"], int) and r["version"] == 1
        assert isinstance(r["genre"], str)

        # structure (5 fields)
        s = r["structure"]
        assert isinstance(s["hook_position_sec"], int)
        assert isinstance(s["emotion_sequence"], list) and all(isinstance(x, str) for x in s["emotion_sequence"])
        assert isinstance(s["turning_points_sec"], list) and all(isinstance(x, int) for x in s["turning_points_sec"])
        assert isinstance(s["emotion_drop_level"], int) and 1 <= s["emotion_drop_level"] <= 5
        assert isinstance(s["ending_state"], str) and s["ending_state"] in {"resolved", "new_suspense", "cliffhanger"}

        # validation (5 fields)
        v = r["validation"]
        assert isinstance(v["platform"], str)
        assert isinstance(v["completion_rate"], float)
        assert isinstance(v["confidence_interval"], str)
        assert isinstance(v["sample_size"], int)
        assert isinstance(v["converged"], bool)

        # provenance (3 fields)
        p = r["provenance"]
        assert isinstance(p["source_episode"], str)
        assert isinstance(p["created"], str)
        assert p["last_validated"] is None

        # Count: 3 top-level + 5 structure + 5 validation + 3 provenance = 16
        total = 3 + len(s) + len(v) + len(p)
        assert total == 16, f"expected 16 fields, got {total}"


# ═══════════════════════════════════════════════════════════════════
# Test 16: degrade handling — AssetBus unreachable
# ═══════════════════════════════════════════════════════════════════
class TestDegradeMode:
    def test_create_recipe_returns_none_on_bus_failure(self, tmp_path, monkeypatch, caplog):
        """If bus.append_line raises, create_recipe logs warning + returns None."""
        bus = _fresh_bus(tmp_path)
        rl = RecipeLibrary(asset_bus=bus)

        def _boom(slot: str, line_obj: dict) -> str:
            raise IOError("disk full (simulated)")

        monkeypatch.setattr(bus, "append_line", _boom)

        with caplog.at_level(logging.WARNING):
            rid = rl.create_recipe("Urban Fantasy", VALID_STRUCTURE, "ep-001")

        assert rid is None
        assert any("degraded" in rec.message.lower() or "create_recipe" in rec.message.lower()
                   for rec in caplog.records), (
            f"expected degraded-mode warning log; got: {[r.message for r in caplog.records]}"
        )
