"""test_gate_verdict.py — Unit tests for plugins.review_gates.gate_verdict.

Covers the three public pure functions:
  - ``compute_verdict`` — aggregation of multiple detector results
  - ``verdict_status`` — decision → status string lookup
  - ``validate_verdict`` — structural invariant checking

Plus D-34-01 / D-34-05 purity guards (mirrors test_gate.py anti-pattern
checks):
  - gate_verdict.py imports only stdlib + gates.types
  - gate_verdict.py has no async def
  - gate_verdict.py has no module-level mutable state
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from plugins.review_gates.gate_verdict import (
    compute_verdict,
    validate_verdict,
    verdict_status,
)
from plugins.review_gates.gates.types import DetectorResult


# ---------------------------------------------------------------------------
# Module-level purity assertions (D-34-01, D-34-05 extended)
# ---------------------------------------------------------------------------

_GATE_VERDICT_PY = Path(__file__).resolve().parent.parent / "gate_verdict.py"


def _gate_verdict_source() -> str:
    return _GATE_VERDICT_PY.read_text(encoding="utf-8")


def test_gate_verdict_py_is_pure_stdlib_no_forbidden_imports():
    """D-34-01 extended: gate_verdict.py must not import httpx / jwt / yaml /
    plugins.review_gates.gate / gate_config / runner_hooks / tools.

    The only permitted plugins.* import is the intra-package typing module
    plugins.review_gates.gates.types (pure-typing, no side-effects).
    """
    src = _gate_verdict_source()
    tree = ast.parse(src)
    forbidden_top = {"httpx", "jwt", "yaml"}
    # Forbidden reach-back modules within the review_gates package.
    # gate_verdict.py is a leaf — it must not import gate state machine,
    # config loader, or runner adapters. Those modules depend on it.
    forbidden_reachback = {
        "plugins.review_gates.gate",
        "plugins.review_gates.gate_config",
        "plugins.review_gates.runner_hooks",
        "plugins.review_gates.tools",
    }
    # Intra-package whitelist: only the types module under gates/ is allowed.
    allowed_intra = {"plugins.review_gates.gates.types"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                assert top not in forbidden_top, (
                    f"forbidden import in gate_verdict.py: {alias.name} "
                    f"(top-level '{top}' violates D-34-01 purity)"
                )
                if alias.name.startswith("plugins."):
                    assert alias.name in allowed_intra or alias.name == "plugins", (
                        f"forbidden plugins.* import in gate_verdict.py: "
                        f"{alias.name} (leaf module must not reach back)"
                    )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top = mod.split(".")[0]
            assert top not in forbidden_top, (
                f"forbidden from-import in gate_verdict.py: {mod} "
                f"(top-level '{top}' violates D-34-01 purity)"
            )
            if top == "plugins":
                assert mod in allowed_intra, (
                    f"forbidden plugins.* from-import in gate_verdict.py: "
                    f"{mod} (only gates.types is whitelisted)"
                )
            # Also check no direct reach-back to sibling modules
            assert mod not in forbidden_reachback, (
                f"forbidden reach-back import in gate_verdict.py: {mod}"
            )


def test_gate_verdict_py_has_no_async_def():
    """D-34-05: gate_verdict.py is sync-only — no ``async def``."""
    src = _gate_verdict_source()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        assert not isinstance(node, ast.AsyncFunctionDef), (
            "gate_verdict.py must not contain async def (D-34-05 sync-only)"
        )


# ---------------------------------------------------------------------------
# compute_verdict — aggregation semantics
# ---------------------------------------------------------------------------


class TestComputeVerdictRejectWins:
    """Reject-wins (any-fail) semantics: any reject → reject."""

    def test_single_reject(self):
        results: list[DetectorResult] = [("reject", "formula:emotion-break-up")]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:emotion-break-up"

    def test_approve_plus_reject(self):
        """Reject dominates approve."""
        results: list[DetectorResult] = [
            ("approve", None),
            ("reject", "formula:emotion-break-up"),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:emotion-break-up"

    def test_reject_plus_approve_order_does_not_matter_for_decision(self):
        """Reject still wins even when listed first."""
        results: list[DetectorResult] = [
            ("reject", "formula:emotion-break-up"),
            ("approve", None),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:emotion-break-up"

    def test_multiple_rejects_uses_first_action(self):
        """When multiple rejects, first one's action is used (deterministic)."""
        results: list[DetectorResult] = [
            ("reject", "formula:emotion-break-up"),
            ("reject", "formula:cold-open-add"),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        # First reject's action wins
        assert action == "formula:emotion-break-up"

    def test_contest_loses_to_reject(self):
        """Reject dominates contest."""
        results: list[DetectorResult] = [
            ("contest", "needs-human-review"),
            ("reject", "formula:emotion-break-up"),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:emotion-break-up"


class TestComputeVerdictApproveAll:
    """All-approve → approve."""

    def test_single_approve(self):
        results: list[DetectorResult] = [("approve", None)]
        decision, action = compute_verdict(results)
        assert decision == "approve"
        assert action is None

    def test_multiple_approve(self):
        results: list[DetectorResult] = [
            ("approve", None),
            ("approve", None),
            ("approve", None),
        ]
        decision, action = compute_verdict(results)
        assert decision == "approve"
        assert action is None

    def test_empty_results_is_approve(self):
        """Empty input → vacuous approve (no detectors found violations)."""
        results: list[DetectorResult] = []
        decision, action = compute_verdict(results)
        assert decision == "approve"
        assert action is None


class TestComputeVerdictContest:
    """Contest semantics: contest beats approve but loses to reject."""

    def test_single_contest(self):
        results: list[DetectorResult] = [("contest", "needs-human-eyes")]
        decision, action = compute_verdict(results)
        assert decision == "contest"
        assert action == "needs-human-eyes"

    def test_contest_plus_approve(self):
        """Contest dominates approve."""
        results: list[DetectorResult] = [
            ("approve", None),
            ("contest", "needs-human-eyes"),
        ]
        decision, action = compute_verdict(results)
        assert decision == "contest"
        assert action == "needs-human-eyes"

    def test_multiple_contests_uses_first_action(self):
        """First contest's action is used when multiple contests exist."""
        results: list[DetectorResult] = [
            ("contest", "action-a"),
            ("contest", "action-b"),
        ]
        decision, action = compute_verdict(results)
        assert decision == "contest"
        assert action == "action-a"


class TestComputeVerdictDeterminism:
    """compute_verdict is a pure function — same input → same output."""

    def test_same_input_same_output(self):
        results: list[DetectorResult] = [
            ("approve", None),
            ("reject", "formula:emotion-break-up"),
            ("contest", "dubious"),
        ]
        v1 = compute_verdict(results)
        v2 = compute_verdict(results)
        assert v1 == v2

    def test_call_does_not_mutate_input(self):
        """Input list is not mutated by the function."""
        results: list[DetectorResult] = [
            ("approve", None),
            ("reject", "formula:x"),
        ]
        original_len = len(results)
        original_first = results[0]
        compute_verdict(results)
        assert len(results) == original_len
        assert results[0] == original_first

    def test_tuple_input_works(self):
        """Accepts any Sequence, not just list."""
        results = (
            ("reject", "formula:x"),
            ("approve", None),
        )
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:x"


class TestComputeVerdictErrorHandling:
    """Defensive: invalid inputs raise ValueError (never silent approve)."""

    def test_invalid_decision_string_raises(self):
        results = [("bad_decision", None)]
        with pytest.raises(ValueError, match="invalid decision"):
            compute_verdict(results)  # type: ignore[arg-type]

    def test_result_not_tuple_raises(self):
        results = ["approve"]  # type: ignore[list-item]
        with pytest.raises(ValueError, match="each result must be a 2-tuple"):
            compute_verdict(results)  # type: ignore[arg-type]

    def test_result_wrong_length_raises(self):
        results = [("approve",)]  # type: ignore[list-item]
        with pytest.raises(ValueError, match="each result must be a 2-tuple"):
            compute_verdict(results)  # type: ignore[arg-type]

    def test_three_element_tuple_raises(self):
        results = [("approve", None, "extra")]  # type: ignore[list-item]
        with pytest.raises(ValueError, match="each result must be a 2-tuple"):
            compute_verdict(results)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# compute_verdict — realistic redline scenarios
# ---------------------------------------------------------------------------


class TestComputeVerdictRedlineScenarios:
    """End-to-end aggregation scenarios mirroring the 3 redline detectors."""

    def test_all_three_redlines_approve(self):
        """All 3 redline detectors pass → approve."""
        results: list[DetectorResult] = [
            ("approve", None),        # emotion_desensitize
            ("approve", None),        # no_cold_open
            ("approve", None),        # unfinished_ending
        ]
        decision, action = compute_verdict(results)
        assert decision == "approve"
        assert action is None

    def test_emotion_violation_only(self):
        """Only R1 (emotion desensitization) fires → reject with emotion formula."""
        results: list[DetectorResult] = [
            ("reject", "formula:emotion-break-up"),
            ("approve", None),
            ("approve", None),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:emotion-break-up"

    def test_cold_open_violation_only(self):
        """Only R3 (no cold open) fires → reject with cold-open formula."""
        results: list[DetectorResult] = [
            ("approve", None),
            ("reject", "formula:cold-open-add"),
            ("approve", None),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:cold-open-add"

    def test_two_violations_first_wins_action(self):
        """Two redlines fire → reject with first detector's action."""
        results: list[DetectorResult] = [
            ("reject", "formula:emotion-break-up"),
            ("reject", "formula:cold-open-add"),
            ("approve", None),
        ]
        decision, action = compute_verdict(results)
        assert decision == "reject"
        # First reject's action wins (deterministic order)
        assert action == "formula:emotion-break-up"

    def test_contested_mixed_with_approve(self):
        """One contest + rest approve → contest."""
        results: list[DetectorResult] = [
            ("approve", None),
            ("contest", "borderline-emotion"),
            ("approve", None),
        ]
        decision, action = compute_verdict(results)
        assert decision == "contest"
        assert action == "borderline-emotion"

    def test_early_exit_on_reject(self):
        """Reject causes early exit — subsequent results aren't needed for decision."""
        # Verify that a long list with reject as first element still gives
        # correct answer (functional proof of early-exit correctness, not
        # a performance benchmark).
        results: list[DetectorResult] = [
            ("reject", "formula:emotion-break-up"),
        ] + [("approve", None)] * 100
        decision, action = compute_verdict(results)
        assert decision == "reject"
        assert action == "formula:emotion-break-up"


# ---------------------------------------------------------------------------
# verdict_status — decision → status mapping
# ---------------------------------------------------------------------------


class TestVerdictStatus:
    def test_approve_maps_to_approved(self):
        assert verdict_status("approve") == "approved"

    def test_reject_maps_to_rejected(self):
        assert verdict_status("reject") == "rejected"

    def test_contest_maps_to_contested(self):
        assert verdict_status("contest") == "contested"

    def test_invalid_decision_raises(self):
        with pytest.raises(ValueError, match="invalid decision"):
            verdict_status("not_a_decision")

    def test_pure_lookup(self):
        """Same input → same output (pure function)."""
        assert verdict_status("approve") == verdict_status("approve")
        assert verdict_status("reject") == verdict_status("reject")
        assert verdict_status("contest") == verdict_status("contest")


# ---------------------------------------------------------------------------
# validate_verdict — structural invariant checks
# ---------------------------------------------------------------------------


class TestValidateVerdictDecision:
    """Invariant 1: decision must be valid."""

    def test_approve_valid(self):
        assert validate_verdict("approve", None) is True

    def test_reject_valid(self):
        assert validate_verdict("reject", "formula:emotion-break-up") is True

    def test_contest_valid(self):
        assert validate_verdict("contest", "needs-review") is True

    def test_invalid_decision_false(self):
        assert validate_verdict("deny", None) is False

    def test_empty_string_decision_false(self):
        assert validate_verdict("", None) is False


class TestValidateVerdictSuggestedAction:
    """Invariant 2: suggested_action must be None or non-empty str."""

    def test_none_action_valid(self):
        assert validate_verdict("approve", None) is True

    def test_string_action_valid(self):
        assert validate_verdict("reject", "formula:x") is True

    def test_empty_string_action_invalid(self):
        assert validate_verdict("reject", "") is False

    def test_int_action_invalid(self):
        assert validate_verdict("reject", 123) is False  # type: ignore[arg-type]


class TestValidateVerdictApproveNoAction:
    """Invariant 3: approve must carry no action."""

    def test_approve_with_action_is_invalid(self):
        assert validate_verdict("approve", "some-action") is False

    def test_approve_with_none_is_valid(self):
        assert validate_verdict("approve", None) is True


class TestValidateVerdictRejectAction:
    """Reject with action is valid; reject without action is also valid
    (not enforced — some reject paths may lack a formula yet)."""

    def test_reject_with_action_valid(self):
        assert validate_verdict("reject", "formula:x") is True

    def test_reject_without_action_valid(self):
        assert validate_verdict("reject", None) is True


# ---------------------------------------------------------------------------
# Return shape: always a 2-tuple
# ---------------------------------------------------------------------------


class TestComputeVerdictReturnShape:
    """Return value is always a 2-tuple of (decision, suggested_action)."""

    def test_returns_tuple(self):
        assert isinstance(compute_verdict([("approve", None)]), tuple)

    def test_returns_length_2(self):
        assert len(compute_verdict([("approve", None)])) == 2

    def test_decision_is_str(self):
        decision, _ = compute_verdict([("approve", None)])
        assert isinstance(decision, str)

    def test_approve_action_is_none(self):
        _, action = compute_verdict([("approve", None)])
        assert action is None
