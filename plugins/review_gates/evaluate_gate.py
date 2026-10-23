"""evaluate_gate.py — T2: automated gate evaluation via blocking_policies.

Given a gate's ``blocking_policies`` block (from gates.yaml) and a ``data``
dict produced by the phase's QC/audit pass, evaluate every rule and return
a verdict: pass or block + the list of triggered rules + the default
rollback target.

Design principles:
  - **ANY rule fires → block** (fail-closed: OR semantics).
  - **Missing / malformed data**: rules that cannot be evaluated are treated
    as "did not fire" (non-blocking) rather than raising. The caller is
    responsible for deciding whether a missing data field is itself a
    reason to block (it can add a ``field_present`` rule for that).
    FIX-3 (2026-10-12): this is deliberately scoped to DATA problems only —
    a rule whose evaluation RAISES (bug in an evaluator, unexpected data
    shape crashing an operator) is NOT data-missing, it is a rule-evaluation
    error, and it is fail-closed: the rule is treated as fired (blocking)
    and recorded in ``rule_errors``. Rationale: under OR semantics, skipping
    a raising rule can turn a would-be block into a pass — 宁可误 block
    （人工放行）不可静默放行 (infra ≠ verdict 三态，与
    quality_gate_error.InfrastructureGateError 同批裁决心法).
  - **Pure function**: no I/O, no state, no side effects. Easy to unit-test.
  - **Operates on raw YAML dicts**, not GateConfig — the blocking_policies
    field is intentionally not on the frozen dataclass (it's an evaluation-
    time concern, not a lifecycle one).

Rule types (mirrors ``_VALID_RULE_TYPES`` in ``gate_config.py``):
  - ``critical_count``: compares a numeric field to a threshold via
    ``operator`` (gt/gte/eq/lt/lte).
  - ``score_floor``: blocks when ``data[field] < min`` (or field absent).
  - ``pass_ratio``: blocks when ``data[field] / data[total_field] < min_ratio``.
    Handles zero denominator (0/0 → blocks, since 0 pass is always a fail).
  - ``field_present``: blocks when ``data[field]`` is falsy (None / 0 / "" /
    empty list / etc.).
  - ``stigma_unresolved``: blocks when ``data[field]`` (a list of stigma dicts)
    contains items NOT matched by any override. Supports optional
    ``min_severity`` filter (default: any unresolved stigma blocks).

Field paths are simple top-level keys (not dotted — each phase flattens
its evaluation-relevant data into the top-level dict it passes in).

T4 (overrides): callers may pass ``overrides`` (list of dicts with
``stigma_id`` or ``finding_key`` + ``approved_by`` + ``source``). Overrides
neutralize matching triggered rules / stigma items. Overridden items move
from ``triggered_rules`` to ``overrides_applied`` (with provenance).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_gate(
    blocking_policies: dict,
    data: dict,
    *,
    phase_id: str = "",
    overrides: list[dict] | None = None,
) -> dict:
    """Evaluate all rules in ``blocking_policies.rules`` against ``data``.

    Args:
        blocking_policies: The raw ``blocking_policies`` dict from gates.yaml
            (validated at load time by gate_config._validate_blocking_policies).
        data: Phase-produced evaluation data (flat dict). Each phase is
            responsible for flattening its QC/audit outputs into the top-level
            keys referenced by its rules' ``field`` / ``total_field`` values.
        phase_id: Optional phase_id for context in log messages.
        overrides: Optional list of operator override dicts. Each override
            has ``{stigma_id | finding_key, approved_by, source, note?}``.
            Overrides neutralize matching triggered rules or stigma items —
            the item moves from ``triggered_rules`` to ``overrides_applied``.
            Matching logic:
              - Stigma items match on ``stigma_id == item["id"]``.
              - Rule-based findings match on ``finding_key == rule["field"]``
                OR on a per-item ``finding_key`` embedded in the trigger reason.

    Returns:
        Verdict dict with keys:
          - ``block`` (bool): True if ANY rule fired AND not overridden.
          - ``triggered_rules`` (list[dict]): rules that fired AND are not
            overridden. Empty when block=False.
          - ``overrides_applied`` (list[dict]): overrides that neutralized
            triggered items. Each entry carries the override's provenance
            (approved_by, source, note) plus the matched item info.
          - ``rollback_target`` (str): default rollback target from
            ``blocking_policies.rollback_target_default``.
          - ``rules_evaluated`` (int): number of rules that were successfully
            evaluated (rules with missing data are skipped, not counted).
          - ``rules_skipped`` (int): rules that could not be evaluated
            (e.g., missing data field).
          - ``rule_errors`` (list[dict]): rules whose evaluation RAISED —
            each entry is ``{"rule_index": int, "rule_type": str,
            "error": str}``. Fail-closed (FIX-3): each such rule is ALSO
            treated as fired (blocking).
    """
    if not isinstance(blocking_policies, dict):
        logger.warning(
            "%s: evaluate_gate called with non-dict blocking_policies — "
            "treating as pass (no policy = no auto-block)",
            phase_id or "evaluate_gate",
        )
        return _pass_result("", 0, 0)

    if not blocking_policies.get("auto_evaluate", False):
        return _pass_result(
            blocking_policies.get("rollback_target_default", ""), 0, 0,
        )

    rules = blocking_policies.get("rules") or []
    rollback_target = blocking_policies.get("rollback_target_default", "")
    override_list = overrides if isinstance(overrides, list) else []

    triggered: list[dict] = []
    rule_errors: list[dict] = []
    evaluated = 0
    skipped = 0

    for i, rule in enumerate(rules):
        try:
            fired, reason, extra = _evaluate_rule(rule, data)
        except Exception as exc:  # noqa: BLE001 — defensive: never raise
            # FIX-3 (2026-10-12): fail-closed —— 规则求值异常 ≠ 数据缺失。
            # OR 语义下跳过一条异常规则可能把 would-be block 变 pass；
            # 宁可误 block（人工放行）不可静默放行。该规则视作 fired
            # (blocking) 并记入 rule_errors 台账（异常仍不外抛——本函数
            # 保持纯函数"永不 raise"契约）。
            logger.error(
                "%s: blocking_policies.rules[%d] raised during evaluation: %s "
                "— treating rule as FIRED (fail-closed for rule-evaluation "
                "errors; see rule_errors in the verdict)",
                phase_id or "evaluate_gate", i, exc,
            )
            rule_errors.append({
                "rule_index": i,
                "rule_type": rule.get("type", "unknown") if isinstance(rule, dict) else "non_dict_rule",
                "error": str(exc),
            })
            triggered.append({
                "type": rule.get("type", "unknown") if isinstance(rule, dict) else "non_dict_rule",
                "field": rule.get("field", "") if isinstance(rule, dict) else "",
                "reason": (
                    f"rule evaluation raised: {exc} — fail-closed, treated "
                    f"as fired (blocking)"
                ),
            })
            skipped += 1
            continue

        if fired is None:
            # Rule could not be evaluated (missing data etc.)
            skipped += 1
            continue

        evaluated += 1
        if fired:
            entry = {
                "type": rule.get("type", "unknown"),
                "field": rule.get("field", ""),
                "reason": reason,
            }
            if extra:
                entry["items"] = extra  # e.g. individual stigma items
            triggered.append(entry)

    # --- T4: Apply overrides ---
    triggered, overrides_applied = _apply_overrides(triggered, override_list)

    block = len(triggered) > 0
    return {
        "block": block,
        "triggered_rules": triggered,
        "overrides_applied": overrides_applied,
        "rollback_target": rollback_target,
        "rules_evaluated": evaluated,
        "rules_skipped": skipped,
        "rule_errors": rule_errors,
    }


# ---------------------------------------------------------------------------
# Per-rule evaluators
# ---------------------------------------------------------------------------


def _evaluate_rule(rule: dict, data: dict) -> tuple[bool | None, str, list[dict]]:
    """Evaluate a single rule.

    Returns:
        (fired, reason, extra_items):
          - fired=True  → rule triggered (block)
          - fired=False → rule evaluated and passed
          - fired=None  → rule could not be evaluated (skip)
          - reason: human-readable string explaining the trigger or skip.
          - extra_items: per-item detail list (for stigma_unresolved etc.)
    """
    rtype = rule.get("type")
    field = rule.get("field", "")

    if rtype == "critical_count":
        fired, reason = _eval_critical_count(rule, data)
        return fired, reason, []
    elif rtype == "score_floor":
        fired, reason = _eval_score_floor(rule, data)
        return fired, reason, []
    elif rtype == "pass_ratio":
        fired, reason = _eval_pass_ratio(rule, data)
        return fired, reason, []
    elif rtype == "field_present":
        fired, reason = _eval_field_present(rule, data)
        return fired, reason, []
    elif rtype == "stigma_unresolved":
        return _eval_stigma_unresolved(rule, data)
    else:
        # Unknown type — should have been caught by YAML validation, but
        # be defensive here.
        return None, f"unknown rule type: {rtype!r}", []


def _eval_critical_count(rule: dict, data: dict) -> tuple[bool | None, str]:
    field = rule.get("field", "")
    threshold = rule.get("threshold", 0)
    operator = rule.get("operator", "gt")

    value = data.get(field)
    if value is None:
        return None, f"field '{field}' missing from data"
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None, f"field '{field}' is not numeric (got {type(value).__name__})"

    if operator == "gt":
        fired = value > threshold
    elif operator == "gte":
        fired = value >= threshold
    elif operator == "eq":
        fired = value == threshold
    elif operator == "lt":
        fired = value < threshold
    elif operator == "lte":
        fired = value <= threshold
    else:
        return None, f"unknown operator: {operator!r}"

    reason = f"{field} = {value} {operator} {threshold} → {'BLOCK' if fired else 'pass'}"
    return fired, reason


def _eval_score_floor(rule: dict, data: dict) -> tuple[bool | None, str]:
    field = rule.get("field", "")
    minimum = rule.get("min", 0)

    value = data.get(field)
    if value is None:
        return None, f"field '{field}' missing from data"
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None, f"field '{field}' is not numeric (got {type(value).__name__})"

    fired = value < minimum
    reason = (
        f"{field} = {value} < {minimum} → BLOCK" if fired
        else f"{field} = {value} >= {minimum} → pass"
    )
    return fired, reason


def _eval_pass_ratio(rule: dict, data: dict) -> tuple[bool | None, str]:
    field = rule.get("field", "")
    total_field = rule.get("total_field", "")
    min_ratio = rule.get("min_ratio", 0.0)

    numerator = data.get(field)
    denominator = data.get(total_field)

    if numerator is None:
        return None, f"field '{field}' missing from data"
    if denominator is None:
        return None, f"total_field '{total_field}' missing from data"
    if not isinstance(numerator, (int, float)) or isinstance(numerator, bool):
        return None, f"field '{field}' is not numeric"
    if not isinstance(denominator, (int, float)) or isinstance(denominator, bool):
        return None, f"total_field '{total_field}' is not numeric"
    if denominator < 0:
        return None, f"total_field '{total_field}' is negative"

    if denominator == 0:
        # Zero checked items: treat as 0% pass → block (fail-closed for
        # pass_ratio when there's nothing to evaluate).
        fired = True
        reason = f"{total_field}=0 (nothing checked) → BLOCK (fail-closed)"
        return fired, reason

    ratio = numerator / denominator
    fired = ratio < min_ratio
    reason = (
        f"{field}/{total_field} = {numerator}/{denominator} = {ratio:.2%} "
        f"< {min_ratio:.0%} → BLOCK" if fired
        else f"{field}/{total_field} = {numerator}/{denominator} = {ratio:.2%} "
             f">= {min_ratio:.0%} → pass"
    )
    return fired, reason


def _eval_field_present(rule: dict, data: dict) -> tuple[bool | None, str]:
    field = rule.get("field", "")
    value = data.get(field)

    # Falsy values → block (field is "not present / not set / empty").
    fired = not bool(value)
    reason = (
        f"{field} is falsy ({value!r}) → BLOCK" if fired
        else f"{field} is present and truthy → pass"
    )
    return fired, reason


def _eval_stigma_unresolved(
    rule: dict, data: dict,
) -> tuple[bool | None, str, list[dict]]:
    """Evaluate a stigma_unresolved rule.

    Blocks when ``data[field]`` (a list of stigma dicts) has any unresolved
    items. Each stigma dict has ``{id, stigma, source_phase, severity, ...}``.
    Overrides (matching on ``stigma_id``) neutralize per-item; the remaining
    unresolved count determines the block.

    Optional rule fields:
      - ``min_severity``: only consider stigma items with severity >= this
        level (using an ordered scale). Default: "warning" (any stigma counts).

    Returns (fired, reason, extra_items) where extra_items is the list of
    unresolved stigma entries (each with an ``id`` key for override matching).
    """
    field = rule.get("field", "stigmas")
    min_severity = rule.get("min_severity", "warning")
    items = data.get(field)

    if items is None:
        return None, f"field '{field}' missing from data", []
    if not isinstance(items, list):
        return None, f"field '{field}' is not a list (got {type(items).__name__})", []

    # Filter by min_severity if specified
    candidate_items = [
        s for s in items
        if isinstance(s, dict) and _severity_ge(s.get("severity", "warning"), min_severity)
    ]

    # Unresolved = items without "resolved": true or "overridden": true
    unresolved = [
        s for s in candidate_items
        if not s.get("resolved", False) and not s.get("overridden", False)
    ]

    if not unresolved:
        return False, f"{field}: 0 unresolved stigmas (min_severity={min_severity}) → pass", []

    return True, (
        f"{field}: {len(unresolved)} unresolved stigma(s) "
        f"(min_severity={min_severity}) → BLOCK"
    ), unresolved


# ---------------------------------------------------------------------------
# T4: Override application
# ---------------------------------------------------------------------------


def _apply_overrides(
    triggered: list[dict],
    overrides: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Apply operator overrides to triggered rules.

    Returns (remaining_triggered, overrides_applied).
    Matching rules:
      - Rule with ``field == override["finding_key"]`` → entire rule overridden
      - Per-item overrides: stigma items where ``item["id"] == override["stigma_id"]``
        → item removed from the rule's ``items`` list; if all items gone, rule dropped
    """
    if not overrides:
        return triggered, []

    overrides_applied: list[dict] = []
    remaining: list[dict] = []

    for rule_entry in triggered:
        rtype = rule_entry.get("type", "")
        rfield = rule_entry.get("field", "")

        # Check whole-rule override (by finding_key)
        whole_rule_override = None
        for ov in overrides:
            fk = ov.get("finding_key")
            if fk and fk == rfield:
                whole_rule_override = ov
                break

        if whole_rule_override:
            overrides_applied.append({
                "rule_type": rtype,
                "field": rfield,
                "approved_by": whole_rule_override.get("approved_by", ""),
                "source": whole_rule_override.get("source", ""),
                "note": whole_rule_override.get("note", ""),
                "override_type": "whole_rule",
            })
            continue

        # For stigma_unresolved: check per-item overrides (by stigma_id)
        if rtype == "stigma_unresolved":
            items = rule_entry.get("items", [])
            kept_items: list[dict] = []
            for item in items:
                item_id = item.get("id", "") if isinstance(item, dict) else ""
                item_override = None
                for ov in overrides:
                    sid = ov.get("stigma_id")
                    if sid and sid == item_id:
                        item_override = ov
                        break
                if item_override:
                    overrides_applied.append({
                        "rule_type": "stigma_unresolved",
                        "field": rfield,
                        "stigma_id": item_id,
                        "approved_by": item_override.get("approved_by", ""),
                        "source": item_override.get("source", ""),
                        "note": item_override.get("note", ""),
                        "override_type": "per_stigma",
                    })
                else:
                    kept_items.append(item)

            if not kept_items:
                # All items overridden → rule fully resolved
                continue

            # Some items remain → keep rule with remaining items
            new_entry = dict(rule_entry)
            new_entry["items"] = kept_items
            new_entry["reason"] = (
                f"{rfield}: {len(kept_items)} unresolved stigma(s) after overrides → BLOCK"
            )
            remaining.append(new_entry)
            continue

        # No override matched → keep as-is
        remaining.append(rule_entry)

    return remaining, overrides_applied


# ---------------------------------------------------------------------------
# Severity comparison helper
# ---------------------------------------------------------------------------


_SEVERITY_ORDER = {
    "info": 0,
    "warning": 1,
    "major": 2,
    "critical": 3,
}


def _severity_ge(severity: str, threshold: str) -> bool:
    """Compare severity levels: returns True if severity >= threshold."""
    s = _SEVERITY_ORDER.get(severity, 0)
    t = _SEVERITY_ORDER.get(threshold, 0)
    return s >= t


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pass_result(
    rollback_target: str,
    evaluated: int,
    skipped: int,
) -> dict:
    """Construct a non-blocking verdict result."""
    return {
        "block": False,
        "triggered_rules": [],
        "overrides_applied": [],
        "rollback_target": rollback_target,
        "rules_evaluated": evaluated,
        "rules_skipped": skipped,
        "rule_errors": [],
    }
