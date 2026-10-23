"""gate_verdict.py — Pure-function verdict computation for review gates.

A leaf module (D-34-01 pattern: pure stdlib, no network / config / plugin
imports) that owns the *decision logic* between detector results and the
gate state machine. Detectors emit individual ``(decision,
suggested_action)`` tuples; this module aggregates them into a single
verdict that ``runner_hooks`` feeds into ``Gate.resolve()``.

Why a separate module:
- The 3 redline detectors in ``gates/`` are per-rule atomic detectors.
  When multiple detectors apply to the same gate (e.g. all three p13
  redlines under a single delivery-gate), their results must be
  aggregated. This module owns that aggregation policy.
- Keeps aggregation rules unit-testable in isolation — no dependency on
  ``gate.py`` state machine, no ``gates.yaml`` config, no asset bus.
- Mirror of the Phase 34 ``gate.py`` pattern: a leaf pure-function
  module with its own test file, enforced by the same D-34-01 purity
  guard.

Aggregation policy (reject-wins, also called "any-fail" semantics):
  * If **any** detector returns ``"reject"`` → verdict is ``"reject"``,
    ``suggested_action`` is the first reject's action (deterministic:
    input order determines priority).
  * If **no** rejects but **any** detector returns ``"contest"`` →
    verdict is ``"contest"``, ``suggested_action`` is the first contest's
    action.
  * If **all** detectors return ``"approve"`` → verdict is ``"approve"``,
    ``suggested_action`` is ``None``.
  * Empty input list → ``("approve", None)`` (vacuous truth: no
    detectors found violations).

This module imports **only** from stdlib and from
``plugins.review_gates.gates.types`` (itself a pure-typing sibling
module). It does NOT import ``gate.py`` / ``gate_config.py`` /
``runner_hooks.py`` — those modules depend on it (or on its return
type), not the other way around.
"""

from __future__ import annotations

from typing import Sequence

from plugins.review_gates.gates.types import Decision, DetectorResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Precedence order for verdict aggregation — lower index = higher priority.
# "reject" dominates everything; "contest" dominates "approve".
_DECISION_PRECEDENCE: dict[str, int] = {
    "reject": 0,
    "contest": 1,
    "approve": 2,
}

_VALID_DECISIONS = frozenset({"approve", "reject", "contest"})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_verdict(results: Sequence[DetectorResult]) -> DetectorResult:
    """Aggregate multiple detector results into a single gate verdict.

    Uses **reject-wins** (any-fail) semantics:
      * Any ``"reject"`` → verdict is ``"reject"`` (first reject's action).
      * No rejects but any ``"contest"`` → verdict is ``"contest"``.
      * All ``"approve"`` → verdict is ``"approve"``.
      * Empty input → ``("approve", None)``.

    Determinism: when multiple results have the same winning decision,
    the **first** one in ``results`` contributes its ``suggested_action``.
    Callers are responsible for ordering detectors by priority.

    Purity guarantee: no side effects, no I/O, no mutation of inputs.
    Same input → same output (referentially transparent).

    Args:
        results: Sequence of ``(decision, suggested_action)`` tuples from
            one or more detectors. Each decision must be one of
            ``"approve"``, ``"reject"``, ``"contest"``.

    Returns:
        A single ``(decision, suggested_action)`` tuple — the aggregated
        verdict, ready to feed into ``Gate.resolve()``.

    Raises:
        ValueError: if any result's decision is not a valid decision
            string. Defensive: callers should validate detector output,
            but we fail loud rather than silently promoting unknown
            values to "approve".
    """
    if not results:
        return ("approve", None)

    winning_decision: Decision = "approve"
    winning_action: str | None = None
    winning_priority = _DECISION_PRECEDENCE["approve"]

    for result in results:
        if not isinstance(result, tuple) or len(result) != 2:
            raise ValueError(
                f"compute_verdict: each result must be a 2-tuple "
                f"(decision, suggested_action), got {result!r}"
            )
        decision, action = result
        if decision not in _VALID_DECISIONS:
            raise ValueError(
                f"compute_verdict: invalid decision {decision!r} "
                f"(expected approve/reject/contest)"
            )
        priority = _DECISION_PRECEDENCE[decision]
        if priority < winning_priority:
            winning_decision = decision  # type: ignore[assignment]
            winning_action = action
            winning_priority = priority
            # Early-exit optimization: "reject" is the highest priority,
            # once we see one we can't get any more severe.
            if winning_decision == "reject":
                break

    return (winning_decision, winning_action)


def verdict_status(decision: str) -> str:
    """Map a verdict decision string to its corresponding gate status.

    Pure lookup — no state, no I/O. Used by callers that need to convert
    a detector/verdict decision into a ``GateStatus`` value without
    importing the full gate module (e.g. in pure-function tests or
    adapters that want to avoid coupling to gate.py).

    Args:
        decision: One of ``"approve"``, ``"reject"``, ``"contest"``.

    Returns:
        Corresponding status string: ``"approved"``, ``"rejected"``,
        or ``"contested"``.

    Raises:
        ValueError: if ``decision`` is not a valid decision string.
    """
    if decision not in _VALID_DECISIONS:
        raise ValueError(
            f"verdict_status: invalid decision {decision!r} "
            f"(expected approve/reject/contest)"
        )
    return {
        "approve": "approved",
        "reject": "rejected",
        "contest": "contested",
    }[decision]


def validate_verdict(decision: str, suggested_action: str | None) -> bool:
    """Validate that a verdict tuple has the expected shape and invariants.

    Checks:
      1. ``decision`` is one of ``"approve"`` / ``"reject"`` / ``"contest"``.
      2. ``suggested_action`` is either ``None`` or a non-empty ``str``.
      3. If ``decision == "approve"``, ``suggested_action`` MUST be ``None``
         (approve carries no action — this is the D-34-01 / Plan 40-01
         convention enforced across all detectors).
      4. If ``decision == "reject"``, ``suggested_action`` SHOULD be
         non-None (warned but not enforced — some reject paths may not
         have a formula action yet).

    Args:
        decision: Verdict decision string.
        suggested_action: Optional action hint (``None`` or ``str``).

    Returns:
        ``True`` if the verdict passes all structural invariants.
        ``False`` otherwise (caller decides how to handle — log, raise,
        or default to approve).
    """
    # Invariant 1: valid decision
    if decision not in _VALID_DECISIONS:
        return False

    # Invariant 2: suggested_action is None or non-empty str
    if suggested_action is not None:
        if not isinstance(suggested_action, str) or not suggested_action:
            return False

    # Invariant 3: approve must carry no action
    if decision == "approve" and suggested_action is not None:
        return False

    return True


# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------

__all__ = [
    "compute_verdict",
    "validate_verdict",
    "verdict_status",
]
