"""Unit tests for ``_check_evidence_coverage`` (EVAL-03 bias canary check #1).

Behavior per 54-03-PLAN.md Task 1:
  - Test 1 (PASS): identical text → cosine 1.0 → passed=True
  - Test 2 (FAIL): unrelated text → cosine < 0.7 → passed=False, low_cosine_records=[0]
  - Edge: empty new_memory_text + empty evidence → cosine 0.0 → fail + flag
"""
from __future__ import annotations

import pytest


def test_evidence_coverage_pass_identical_text(deterministic_embed):
    """Identical new + evidence text → cosine 1.0 → check passes."""
    from agent.curator_bias_canary import _check_evidence_coverage

    result = _check_evidence_coverage(
        new_memory_text="flamingo sunset palette",
        evidence_records=[{"text": "flamingo sunset palette"}],
        threshold=0.7,
        embed_fn=deterministic_embed,
    )
    assert result["passed"] is True
    assert result["low_cosine_records"] == []
    assert result.get("min_cosine") is not None


def test_evidence_coverage_fail_unrelated_text(deterministic_embed):
    """Unrelated new + evidence text → cosine < 0.7 → check fails, index flagged."""
    from agent.curator_bias_canary import _check_evidence_coverage

    result = _check_evidence_coverage(
        new_memory_text="XYZ unrelated claim about cats and dogs",
        evidence_records=[
            {"text": "completely different content about quantum mechanics and lasers"}
        ],
        threshold=0.7,
        embed_fn=deterministic_embed,
    )
    assert result["passed"] is False
    assert 0 in result["low_cosine_records"]


def test_evidence_coverage_empty_strings_yield_zero_cosine(deterministic_embed):
    """Empty new + empty evidence → cosine 0.0 (no division by zero)."""
    from agent.curator_bias_canary import _check_evidence_coverage

    result = _check_evidence_coverage(
        new_memory_text="",
        evidence_records=[{"text": ""}],
        threshold=0.7,
        embed_fn=deterministic_embed,
    )
    assert result["passed"] is False
    assert 0 in result["low_cosine_records"]


def test_evidence_coverage_multi_record_partial_failure(deterministic_embed):
    """3 evidence records, 1 unrelated → that one index flagged, others pass."""
    from agent.curator_bias_canary import _check_evidence_coverage

    result = _check_evidence_coverage(
        new_memory_text="cinematographer prefers warm color palettes for sunset shots",
        evidence_records=[
            {"text": "warm color palettes for sunset shots preferred by cinematographer"},
            {"text": "cinematographer likes warm sunset colors"},
            {"text": "completely unrelated topic about deep sea creatures"},
        ],
        threshold=0.7,
        embed_fn=deterministic_embed,
    )
    # At least index 2 must be flagged. Indices 0,1 may pass or fail depending
    # on embedding granularity — we only assert the unrelated one is caught.
    assert 2 in result["low_cosine_records"]


def test_evidence_coverage_uses_default_embed_fn_when_none():
    """Default ``embed_fn=None`` falls back to deterministic bag-of-words (no LLM)."""
    from agent.curator_bias_canary import _check_evidence_coverage

    # Identical text → cosine 1.0 with the default embed too.
    result = _check_evidence_coverage(
        new_memory_text="flamingo sunset palette",
        evidence_records=[{"text": "flamingo sunset palette"}],
        threshold=0.7,
        embed_fn=None,
    )
    assert result["passed"] is True


def test_evidence_coverage_missing_text_field_treated_as_empty(deterministic_embed):
    """Evidence record missing the ``text`` key → treated as empty string (cosine 0.0)."""
    from agent.curator_bias_canary import _check_evidence_coverage

    result = _check_evidence_coverage(
        new_memory_text="some claim",
        evidence_records=[{}],  # no "text" key
        threshold=0.7,
        embed_fn=deterministic_embed,
    )
    assert result["passed"] is False
    assert 0 in result["low_cosine_records"]


@pytest.mark.parametrize("threshold,expected_pass", [(0.0, True), (1.01, False)])
def test_evidence_coverage_threshold_bounds(deterministic_embed, threshold, expected_pass):
    """Threshold=0.0 → anything passes; threshold>1.0 → nothing passes."""
    from agent.curator_bias_canary import _check_evidence_coverage

    result = _check_evidence_coverage(
        new_memory_text="alpha beta gamma",
        evidence_records=[{"text": "alpha beta gamma"}],
        threshold=threshold,
        embed_fn=deterministic_embed,
    )
    assert result["passed"] is expected_pass
