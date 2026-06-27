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
