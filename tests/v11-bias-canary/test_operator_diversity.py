"""Unit tests for ``_check_operator_diversity`` (EVAL-03 bias canary check #2).

Behavior per 54-03-PLAN.md Task 1:
  - Test 3 (PASS): 2 distinct operators among 3 IDs → passed=True, distinct_count=2
  - Test 4 (FAIL): same operator repeated → passed=False, distinct_count=1
  - Test 5 (FAIL): empty list → passed=False, distinct_count=0
"""
from __future__ import annotations

import pytest


def test_operator_diversity_pass_two_distinct():
    """3 IDs, 2 distinct → passes min_distinct_operators=2."""
    from agent.curator_bias_canary import _check_operator_diversity

    result = _check_operator_diversity(
        evidence_operator_ids=["op1", "op2", "op1"],
        min_distinct_operators=2,
    )
    assert result["passed"] is True
    assert result["distinct_count"] == 2


def test_operator_diversity_fail_single_operator():
    """Both IDs are op1 → distinct_count=1, fails min=2."""
    from agent.curator_bias_canary import _check_operator_diversity

    result = _check_operator_diversity(
        evidence_operator_ids=["op1", "op1"],
        min_distinct_operators=2,
    )
    assert result["passed"] is False
    assert result["distinct_count"] == 1


def test_operator_diversity_fail_empty_list():
    """Empty evidence_operator_ids → distinct_count=0, fails."""
    from agent.curator_bias_canary import _check_operator_diversity

    result = _check_operator_diversity(
        evidence_operator_ids=[],
        min_distinct_operators=2,
    )
    assert result["passed"] is False
    assert result["distinct_count"] == 0


def test_operator_diversity_filters_none_and_empty_strings():
    """None / empty-string operator IDs are not counted toward distinct set."""
    from agent.curator_bias_canary import _check_operator_diversity

    result = _check_operator_diversity(
        evidence_operator_ids=["op1", None, "", "op2"],
        min_distinct_operators=2,
    )
    assert result["passed"] is True
    assert result["distinct_count"] == 2


def test_operator_diversity_higher_min_threshold():
    """3 distinct operators, min_distinct_operators=4 → fails."""
    from agent.curator_bias_canary import _check_operator_diversity

    result = _check_operator_diversity(
        evidence_operator_ids=["op1", "op2", "op3"],
        min_distinct_operators=4,
    )
    assert result["passed"] is False
    assert result["distinct_count"] == 3


@pytest.mark.parametrize("min_distinct", [1, 2, 3])
def test_operator_diversity_default_min(min_distinct):
    """Passing min_distinct explicitly works across sensible values."""
    from agent.curator_bias_canary import _check_operator_diversity

    result = _check_operator_diversity(
        evidence_operator_ids=["op1", "op2", "op1"],
        min_distinct_operators=min_distinct,
    )
    expected = min_distinct <= 2
    assert result["passed"] is expected
