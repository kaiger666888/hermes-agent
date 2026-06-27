"""test_recipe_library_extraction.py — Phase 41-02 Task 1 (TDD RED->GREEN).

Unit tests for ``RecipeLibrary.extract_structure_from_episode`` helper
(RECIPE-LIB-04 — DATA SOURCE PIVOT applied):

  - Reads V5.0 ``story-framework`` slot (mcmahon_arc, snowflake_artifacts.
    anchor_validation, snyder_beats_summary) + ``final-audit`` slot
    (scores.D1-D5 0-20 scale). NOT creative-history (plan-checker BLOCKER #1).
  - Applies the 5-field structure mapping table per CONTEXT.md.
  - Degrades gracefully: missing/malformed slot -> None + WARNING log.

15 tests:
  Tests 1-3   : McMahon arc lookup (man_in_a_hole / rags_to_riches / unknown fallback)
  Tests 4-6   : anchor_validation parsing (Catalyst hook, all turning_points, fallback)
  Test  7     : D2_emotion -> emotion_drop_level mapping (3 cases)
  Tests 8-10  : D5_completion -> ending_state (resolved / new_suspense / cliffhanger)
  Test  11    : Full episode extract against ACTUAL V5.0 fixtures from ep-001
  Tests 12-14 : Missing-data degrade (no story-framework / no final-audit / malformed)
  Test  15    : Integration with create_recipe (extracted structure is valid input)
"""

from __future__ import annotations

import copy
import logging
from typing import Any

import pytest

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.recipe_library import RecipeLibrary


# ─── Shared seed helpers (NOT creative_history — DATA SOURCE PIVOT) ────

def _seed_story_framework(bus: AssetBus, framework_dict: dict) -> None:
    """Write story-framework slot with given dict (envelope-wrapped by bus.write)."""
    bus.write("story-framework", framework_dict)


def _seed_final_audit(bus: AssetBus, audit_dict: dict) -> None:
    """Write final-audit slot with given dict (envelope-wrapped by bus.write)."""
    bus.write("final-audit", audit_dict)


def _fresh_bus(tmp_path) -> AssetBus:
    return AssetBus(tmp_path)


# ─── Fixture builders (compose only the fields the mapping reads) ─────

def _framework(
    *,
    mcmahon_arc: str = "man_in_a_hole",
    anchor_validation: str = "Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓",
    snyder_beats_summary: list[str] | None = None,
) -> dict:
    """Minimal story-framework dict (only fields the mapping reads)."""
    if snyder_beats_summary is None:
        snyder_beats_summary = [
            "Opening Image (0-3s): ...",
            "Catalyst+Theme (6-9s): ...",
        ]
    return {
        "story_kernel": {"mcmahon_arc": mcmahon_arc},
        "snowflake_artifacts": {"anchor_validation": anchor_validation},
        "snyder_beats_summary": snyder_beats_summary,
    }


def _audit(*, d2: int = 17, d5: int = 16) -> dict:
    """Minimal final-audit dict (only the scores the mapping reads)."""
    return {
        "total_score": 84,
        "scores": {
            "D1_narrative": 17,
            "D2_emotion": d2,
            "D3_hook": 18,
            "D4_character": 16,
            "D5_completion": d5,
        },
    }


# ═══════════════════════════════════════════════════════════════════
# Tests 1-3: McMahon arc lookup -> emotion_sequence
# ═══════════════════════════════════════════════════════════════════
class TestMcmahonArcLookup:
    def test_man_in_a_hole_emotion_sequence(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework(mcmahon_arc="man_in_a_hole"))
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["emotion_sequence"] == ["hope", "descent", "crisis", "recovery"]

    def test_rags_to_riches_emotion_sequence(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework(mcmahon_arc="rags_to_riches"))
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["emotion_sequence"] == ["low", "rise", "peak", "fall"]

    def test_unknown_arc_falls_back_with_warning(self, tmp_path, caplog):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework(mcmahon_arc="totally_unknown_arc"))
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        with caplog.at_level(logging.WARNING):
            result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["emotion_sequence"] == ["setup", "rising", "climax", "resolution"]
        # WARNING log emitted for unknown arc fallback
        assert any("unknown" in rec.message.lower() and "mcmahon" in rec.message.lower()
                   for rec in caplog.records), (
            f"expected unknown-arc WARNING; got: {[r.message for r in caplog.records]}"
        )


# ═══════════════════════════════════════════════════════════════════
# Tests 4-6: anchor_validation parsing
# ═══════════════════════════════════════════════════════════════════
class TestAnchorValidationParsing:
    def test_catalyst_7_5s_parses_to_hook_position_7(self, tmp_path):
        """int(7.5) = 7 (Python round-toward-zero)."""
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(
            bus,
            _framework(anchor_validation="Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓"),
        )
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["hook_position_sec"] == 7

    def test_all_timestamps_parse_to_turning_points(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(
            bus,
            _framework(anchor_validation="Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓"),
        )
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["turning_points_sec"] == [7, 37, 55]

    def test_catalyst_absent_falls_back_to_first_snyder_beat(self, tmp_path):
        """When Catalyst timestamp absent in anchor_validation, hook falls back
        to the lower bound of the first snyder_beats_summary range.
        Example: first beat "(6-9s)" -> hook=6.
        """
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(
            bus,
            _framework(
                anchor_validation="Midpoint ~37s ✓",  # no Catalyst token
                snyder_beats_summary=[
                    "Opening Image (0-3s): ...",
                    "Catalyst+Theme (6-9s): ...",
                ],
            ),
        )
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        # First beat "(0-3s)" -> lower bound 0
        assert result["hook_position_sec"] == 0


# ═══════════════════════════════════════════════════════════════════
# Test 7: D2_emotion -> emotion_drop_level
# ═══════════════════════════════════════════════════════════════════
class TestD2EmotionMapping:
    @pytest.mark.parametrize("d2,expected", [
        (20, 1),  # int((20-20)/4)+1 = int(0)+1 = 1
        (10, 3),  # int((20-10)/4)+1 = int(2.5)+1 = 2+1 = 3
        (0, 5),   # int(20/4)+1 = 5+1 = 6 -> clamp 5
    ])
    def test_d2_to_drop_level_three_cases(self, tmp_path, d2, expected):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework())
        _seed_final_audit(bus, _audit(d2=d2))
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["emotion_drop_level"] == expected


# ═══════════════════════════════════════════════════════════════════
# Tests 8-10: D5_completion -> ending_state
# ═══════════════════════════════════════════════════════════════════
class TestD5CompletionMapping:
    def test_d5_16_resolved(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework())
        _seed_final_audit(bus, _audit(d5=16))
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["ending_state"] == "resolved"

    def test_d5_12_new_suspense(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework())
        _seed_final_audit(bus, _audit(d5=12))
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["ending_state"] == "new_suspense"

    def test_d5_8_cliffhanger(self, tmp_path):
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework())
        _seed_final_audit(bus, _audit(d5=8))
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        assert result["ending_state"] == "cliffhanger"


# ═══════════════════════════════════════════════════════════════════
# Test 11: Full episode extract against ACTUAL V5.0 fixtures (ep-001)
# ═══════════════════════════════════════════════════════════════════
class TestFullEpisodeExtractFromV5Fixtures:
    def test_canonical_ep_001_extraction(self, tmp_path):
        """End-to-end test against ACTUAL V5.0 fixtures from
        pipeline-runs/ep-001/. Verifies the mapping table end-to-end:
          story-framework.json + final-audit.json -> canonical structure{}
        """
        # Inner .value of pipeline-runs/ep-001/.pipeline-assets/story-framework.json
        # (envelope stripped — bus.write re-wraps)
        sf_fixture = {
            "story_kernel": {
                "kernel_id": "kernel_ep001_001",
                "title_working": "消失的外卖",
                "episode_id": "ep-001",
                "strata_overlay_coefficient": 2.6,
                "unspeakability_score": 4,
                "dramatic_potential_overall": 0.826,
                "mcmahon_arc": "man_in_a_hole",
                "structural_formula": "独居老人用AI伪造家人声音...",
            },
            "snowflake_artifacts": {
                "snowflake_id": "snowflake_ep001_001",
                "mcmahon_arc_selected": "man_in_a_hole",
                "step_1_premise": "外卖小哥追查...",
                "story_spine_sentences": 5,
                "character_count": 3,
                "synopsis_paragraphs": 4,
                "anchor_validation": "Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓",
            },
            "snyder_beats_count": 10,
            "snyder_beats_summary": [
                "Opening Image (0-3s): 诡异订单特写",
                "Set-Up (3-6s): 字幕锚定7张订单",
                "Catalyst+Theme (6-9s): '你终于来了'",
                "Debate (9-14s): 电梯犹豫",
                "Fun & Games (14-37s): 楼道蹲守+扑空+发现AI",
                "Midpoint (37-40s): 极性反转 破案→孤独",
                "Bad Guys Close In (40-52s): 接近真相",
                "All Is Lost+Dark Night (52-58s): '我知道她们不是真的'",
                "Finale (58-70s): '妈妈,我到了'",
                "Final Image (70-75s): 门缝暖光定格",
            ],
        }
        # Inner .value of pipeline-runs/ep-001/.pipeline-assets/final-audit.json
        fa_fixture = {
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
            "axis_180": "PASS",
            "compliance": "all green",
            "improvement_priorities": 3,
            "full_audit_ref": "p06_final_audit_ep001.json",
        }

        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, sf_fixture)
        _seed_final_audit(bus, fa_fixture)
        rl = RecipeLibrary(asset_bus=bus)

        result = rl.extract_structure_from_episode("ep-001")
        assert result is not None
        # Per CONTEXT.md mapping table:
        #   hook=7 (Catalyst ~7.5s -> int(7.5)=7)
        #   emotion_sequence=man_in_a_hole sequence
        #   turning_points=[7,37,55]
        #   emotion_drop_level: int((20-17)/4)+1 = int(0.75)+1 = 0+1 = 1
        #   ending_state: D5=16 >= 16 -> "resolved"
        assert result == {
            "hook_position_sec": 7,
            "emotion_sequence": ["hope", "descent", "crisis", "recovery"],
            "turning_points_sec": [7, 37, 55],
            "emotion_drop_level": 1,
            "ending_state": "resolved",
        }


# ═══════════════════════════════════════════════════════════════════
# Tests 12-14: Missing-data / malformed-data degrade
# ═══════════════════════════════════════════════════════════════════
class TestMissingDataDegrade:
    def test_missing_story_framework_slot_returns_none(self, tmp_path, caplog):
        """No story-framework slot written -> bus.read returns None -> None + WARNING."""
        bus = _fresh_bus(tmp_path)
        _seed_final_audit(bus, _audit())  # audit present, no story-framework
        rl = RecipeLibrary(asset_bus=bus)

        with caplog.at_level(logging.WARNING):
            result = rl.extract_structure_from_episode("ep-001")
        assert result is None
        assert any("story-framework" in rec.message or "missing" in rec.message.lower()
                   for rec in caplog.records), (
            f"expected missing-slot WARNING; got: {[r.message for r in caplog.records]}"
        )

    def test_missing_final_audit_slot_returns_none(self, tmp_path, caplog):
        """story-framework present, final-audit missing -> None + WARNING."""
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework())
        rl = RecipeLibrary(asset_bus=bus)

        with caplog.at_level(logging.WARNING):
            result = rl.extract_structure_from_episode("ep-001")
        assert result is None
        assert any("final-audit" in rec.message or "missing" in rec.message.lower()
                   for rec in caplog.records), (
            f"expected missing-slot WARNING; got: {[r.message for r in caplog.records]}"
        )

    def test_malformed_story_framework_missing_snowflake_returns_none(self, tmp_path, caplog):
        """story-framework dict lacks snowflake_artifacts key -> malformed -> None + WARNING."""
        bus = _fresh_bus(tmp_path)
        # snowflake_artifacts intentionally absent
        bus.write("story-framework", {"story_kernel": {"mcmahon_arc": "man_in_a_hole"}})
        _seed_final_audit(bus, _audit())
        rl = RecipeLibrary(asset_bus=bus)

        with caplog.at_level(logging.WARNING):
            result = rl.extract_structure_from_episode("ep-001")
        assert result is None
        # No exception raised — helper is non-raising by design.


# ═══════════════════════════════════════════════════════════════════
# Test 15: Integration with create_recipe
# ═══════════════════════════════════════════════════════════════════
class TestExtractThenCreateRecipe:
    def test_extracted_structure_is_valid_create_recipe_input(self, tmp_path):
        """After extracting a structure{} from V5.0 fixtures, create_recipe
        accepts it and writes a valid recipe row."""
        bus = _fresh_bus(tmp_path)
        _seed_story_framework(bus, _framework(mcmahon_arc="man_in_a_hole"))
        _seed_final_audit(bus, _audit(d2=17, d5=16))
        rl = RecipeLibrary(asset_bus=bus)

        extracted = rl.extract_structure_from_episode("ep-001")
        assert extracted is not None

        rid = rl.create_recipe(
            genre="Test Genre",
            structure=extracted,
            source_episode="ep-001",
        )
        assert rid is not None

        recipe = rl.get_recipe(rid)
        assert recipe["structure"] == extracted
        assert recipe["provenance"]["source_episode"] == "ep-001"
