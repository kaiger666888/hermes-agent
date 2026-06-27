"""test_recipe_library_update_validation.py — Phase 41-02 Tasks 2+3 (TDD RED->GREEN).

Unit tests for:
  - ``_wilson_ci`` (Task 2) — pure-stdlib Wilson score confidence interval
    (uses math.sqrt only, NO scipy/numpy) + converged flag rule.
  - ``RecipeLibrary.update_validation`` (Task 3) — Phase 42 contract; multi-
    version append-only semantics; running average + CI recomputation.

Test layout:
  - ``TestWilsonCi`` (Task 2): 10 tests for Wilson CI + converged flag.
  - ``TestRecipeLibraryUpdateValidation`` (Task 3, added in next TDD cycle):
    14 tests for update_validation multi-version semantics.
"""

from __future__ import annotations

import inspect
import logging
import math
import re
from datetime import datetime
from typing import Any

import pytest

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.recipe_library import (
    RecipeLibrary,
    _is_converged,
    _wilson_ci,
)


def _fresh_bus(tmp_path) -> AssetBus:
    return AssetBus(tmp_path)


# ═══════════════════════════════════════════════════════════════════
# Task 2: Wilson CI pure-stdlib helper + converged flag
# ═══════════════════════════════════════════════════════════════════
class TestWilsonCi:
    # Test 1: total=0 returns widest interval (0.0, 1.0)
    def test_total_zero_returns_widest_interval(self):
        assert _wilson_ci(0, 0) == (0.0, 1.0)

    # Test 2: all passed, large sample — narrow interval near 1.0
    def test_all_passed_large_sample_narrow_near_one(self):
        lower, upper = _wilson_ci(100, 100)
        assert lower > 0.9
        assert upper <= 1.0
        assert (upper - lower) < 0.10

    # Test 3: all failed, large sample — narrow interval near 0.0
    def test_all_failed_large_sample_narrow_near_zero(self):
        lower, upper = _wilson_ci(0, 100)
        assert lower >= 0.0
        assert upper < 0.1
        assert (upper - lower) < 0.10

    # Test 4: 50/50 large sample — interval around 0.5
    def test_50_50_large_sample_centered_near_half(self):
        lower, upper = _wilson_ci(50, 100)
        # Wilson CI for 50/100 at 95% CI ~ [0.40, 0.60]; spread ~0.19
        # (still wider than 0.10 — convergence requires much larger samples
        # for a 50/50 split, or sample_size threshold alone won't suffice)
        assert 0.35 < lower < 0.45
        assert 0.55 < upper < 0.65
        # Centered near 0.5
        mid = (lower + upper) / 2
        assert 0.45 < mid < 0.55

    # Test 5: small sample, wide interval — NOT converged
    def test_small_sample_wide_interval(self):
        lower, upper = _wilson_ci(5, 10)
        assert (upper - lower) > 0.10

    # Test 6: z parameter — 99% CI (z=2.576) wider than 95% (z=1.96)
    def test_z_99_wider_than_z_95(self):
        lower_95, upper_95 = _wilson_ci(50, 100, z=1.96)
        lower_99, upper_99 = _wilson_ci(50, 100, z=2.576)
        spread_95 = upper_95 - lower_95
        spread_99 = upper_99 - lower_99
        assert spread_99 > spread_95

    # Test 7: math.sqrt used, no scipy/numpy
    def test_uses_math_sqrt_no_scipy_numpy(self):
        source = inspect.getsource(_wilson_ci)
        assert "math.sqrt" in source
        assert "scipy" not in source
        assert "numpy" not in source
        assert "np." not in source

    # Test 8: converged flag — sample_size>=10, spread<=0.10 -> True
    def test_converged_true_at_sample_10_tight_ci(self):
        # Wilson CI for 500/1000 (50% pass) has spread ~0.06 (<=0.10),
        # and sample_size=1000 >= 10 -> converged True
        lower, upper = _wilson_ci(500, 1000)
        assert (upper - lower) <= 0.10
        assert _is_converged(1000, lower, upper) is True
        # Rule fires explicitly when BOTH conditions met (synthetic)
        assert _is_converged(10, 0.45, 0.50) is True   # spread 0.05 <= 0.10

    # Test 9: converged stays False below sample threshold
    def test_converged_false_below_sample_threshold(self):
        # Tight CI but sample_size < 10
        assert _is_converged(9, 0.45, 0.50) is False
        assert _is_converged(0, 0.0, 1.0) is False

    # Test 10: converged False when spread too wide
    def test_converged_false_when_spread_too_wide(self):
        # sample_size sufficient but spread > 0.10
        assert _is_converged(10, 0.40, 0.55) is False   # spread 0.15
        assert _is_converged(100, 0.30, 0.50) is False  # spread 0.20


# ═══════════════════════════════════════════════════════════════════
# Task 3: RecipeLibrary.update_validation — Phase 42 contract +
# multi-version append-only semantics (14 tests)
# ═══════════════════════════════════════════════════════════════════

_VALID_STRUCTURE_UV: dict[str, Any] = {
    "hook_position_sec": 3,
    "emotion_sequence": ["suppress", "thrill", "doubt", "thrill"],
    "turning_points_sec": [3, 15, 30, 55],
    "emotion_drop_level": 4,
    "ending_state": "new_suspense",
}


def _seed_recipe(tmp_path, *, genre: str = "Test", source: str = "ep-001") -> tuple[AssetBus, RecipeLibrary, str]:
    """Helper: seed a single v1 recipe (sample_size=0) for update_validation tests."""
    bus = _fresh_bus(tmp_path)
    rl = RecipeLibrary(asset_bus=bus)
    rid = rl.create_recipe(genre=genre, structure=_VALID_STRUCTURE_UV, source_episode=source)
    assert rid is not None
    return (bus, rl, rid)


class TestRecipeLibraryUpdateValidation:
    # Test 1: basic update — version bumps 1 -> 2
    def test_basic_update_bumps_version(self, tmp_path):
        bus, rl, rid = _seed_recipe(tmp_path)
        new_row = rl.update_validation(rid, platform="douyin", completion_rate=0.45)
        assert new_row is not None
        assert new_row["version"] == 2
        assert new_row["validation"]["sample_size"] == 1
        assert new_row["validation"]["completion_rate"] == pytest.approx(0.45)
        assert new_row["validation"]["platform"] == "douyin"
        # latest read-back is also v2
        latest = rl.get_recipe(rid)
        assert latest["version"] == 2

    # Test 2: running average blends multiple updates
    def test_running_average_blends_multiple_updates(self, tmp_path):
        bus, rl, rid = _seed_recipe(tmp_path)
        rl.update_validation(rid, platform="douyin", completion_rate=0.40)
        rl.update_validation(rid, platform="douyin", completion_rate=0.60)
        latest = rl.get_recipe(rid)
        # (0.40*1 + 0.60*1) / 2 = 0.50
        assert latest["validation"]["completion_rate"] == pytest.approx(0.50)
        assert latest["validation"]["sample_size"] == 2
        assert latest["version"] == 3

    # Test 3: confidence_interval format "±N%"
    def test_confidence_interval_format(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        new_row = rl.update_validation(rid, platform="douyin", completion_rate=0.5)
        assert new_row is not None
        ci = new_row["validation"]["confidence_interval"]
        assert re.match(r"^±\d+%$", ci), f"expected ±N% format, got {ci!r}"

    # Test 4: sample_size_delta default = 1
    def test_sample_size_delta_default_one(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        new_row = rl.update_validation(rid, platform="douyin", completion_rate=0.5)
        assert new_row["validation"]["sample_size"] == 1   # 0 + 1 (default)

    # Test 5: sample_size_delta explicit batch update
    def test_sample_size_delta_explicit_batch(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        new_row = rl.update_validation(
            rid, platform="douyin", completion_rate=0.5, sample_size_delta=5,
        )
        assert new_row["validation"]["sample_size"] == 5   # 0 + 5

    # Test 6: converged flips True at sample_size>=10 + tight CI
    def test_converged_flips_true_at_sample_10(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        # 10 batch updates at completion_rate=0.5, sample_size_delta=10 in one
        # call gives sample_size=10 with ~0.5 pass rate; CI still ~0.19 (too wide).
        # To get converged, need much larger sample: use sample_size_delta=1000
        # with completion_rate=0.5 -> sample_size=1000, spread ~0.06.
        new_row = rl.update_validation(
            rid, platform="douyin", completion_rate=0.5, sample_size_delta=1000,
        )
        assert new_row["validation"]["sample_size"] == 1000
        assert new_row["validation"]["converged"] is True

    # Test 7: converged stays False below sample_size threshold
    def test_converged_false_below_sample_threshold(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        # sample_size_delta=9 -> sample_size=9, below threshold of 10
        new_row = rl.update_validation(
            rid, platform="douyin", completion_rate=0.5, sample_size_delta=9,
        )
        assert new_row["validation"]["sample_size"] == 9
        assert new_row["validation"]["converged"] is False

    # Test 8: multi-version append-only invariant — old versions NEVER mutated
    def test_multi_version_append_only_invariant(self, tmp_path):
        bus, rl, rid = _seed_recipe(tmp_path)
        rl.update_validation(rid, platform="douyin", completion_rate=0.40)
        rl.update_validation(rid, platform="douyin", completion_rate=0.60)
        rl.update_validation(rid, platform="douyin", completion_rate=0.50)

        rows = bus.read_lines("emotion-recipe")
        recipe_rows = [r for r in rows if r.get("recipe_id") == rid]
        # 1 create + 3 updates = 4 rows, versions [1, 2, 3, 4]
        versions = sorted(r["version"] for r in recipe_rows)
        assert versions == [1, 2, 3, 4]
        # v1 row is byte-identical to initial state: sample_size=0, last_validated=None
        v1 = next(r for r in recipe_rows if r["version"] == 1)
        assert v1["validation"]["sample_size"] == 0
        assert v1["provenance"]["last_validated"] is None
        # v2 row still has its original sample_size (1), last_validated from that call
        v2 = next(r for r in recipe_rows if r["version"] == 2)
        assert v2["validation"]["sample_size"] == 1

    # Test 9: KeyError on unknown recipe_id
    def test_key_error_on_unknown_recipe_id(self, tmp_path):
        _, rl, _rid = _seed_recipe(tmp_path)
        with pytest.raises(KeyError):
            rl.update_validation("nonexistent-999", platform="douyin", completion_rate=0.5)

    # Test 10: degrade handling — bus.append_line raises -> None + warning
    def test_degrade_on_bus_failure(self, tmp_path, monkeypatch, caplog):
        bus, rl, rid = _seed_recipe(tmp_path)

        def _boom(slot: str, line_obj: dict) -> str:
            raise IOError("disk full (simulated)")

        monkeypatch.setattr(bus, "append_line", _boom)
        with caplog.at_level(logging.WARNING):
            result = rl.update_validation(rid, platform="douyin", completion_rate=0.5)
        assert result is None
        assert any("update_validation" in rec.message or "degraded" in rec.message.lower()
                   for rec in caplog.records), (
            f"expected degraded WARNING; got: {[r.message for r in caplog.records]}"
        )

    # Test 11: platform recorded in new row
    def test_platform_recorded(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        new_row = rl.update_validation(rid, platform="bilibili", completion_rate=0.5)
        assert new_row["validation"]["platform"] == "bilibili"

    # Test 12: last_validated timestamp is ISO 8601 UTC (tz-aware)
    def test_last_validated_iso_8601_utc(self, tmp_path):
        _, rl, rid = _seed_recipe(tmp_path)
        new_row = rl.update_validation(rid, platform="douyin", completion_rate=0.5)
        ts = new_row["provenance"]["last_validated"]
        assert ts is not None
        parsed = datetime.fromisoformat(ts)
        assert parsed.tzinfo is not None

    # Test 13: completion_rate clamped — out-of-range raises ValueError
    @pytest.mark.parametrize("bad_cr", [1.5, -0.2, 2.0, -1.0])
    def test_completion_rate_out_of_range_raises(self, tmp_path, bad_cr):
        _, rl, rid = _seed_recipe(tmp_path)
        with pytest.raises(ValueError):
            rl.update_validation(rid, platform="douyin", completion_rate=bad_cr)

    # Test 14: Phase 42 contract — signature is exactly
    # (self, recipe_id, platform, completion_rate, sample_size_delta=1)
    def test_phase_42_signature_stability(self):
        sig = inspect.signature(RecipeLibrary.update_validation)
        params = list(sig.parameters.keys())
        assert params == ["self", "recipe_id", "platform", "completion_rate", "sample_size_delta"]
        # default for sample_size_delta must be 1
        assert sig.parameters["sample_size_delta"].default == 1
        # required params (no default): recipe_id, platform, completion_rate
        for name in ("recipe_id", "platform", "completion_rate"):
            assert sig.parameters[name].default is inspect.Parameter.empty
