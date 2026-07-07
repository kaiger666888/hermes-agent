"""Behavior tests for ``run_curator_review`` default-mode dry-run-first invariant.

Cites ``55-03-PLAN.md`` Task 1 <behavior>:
  1. ``run_curator_review()`` (no args) performs ZERO state mutation.
  2. ``run_curator_review(dry_run=None)`` also performs ZERO state mutation.
  3. ``run_curator_review(dry_run=False)`` DOES perform state mutation.
  4. Default-mode invocation logs ``CURATOR_DRY_RUN_BANNER``.
  5. Live-mode invocation does NOT log the banner.
"""
from __future__ import annotations

import logging

import pytest

from agent import curator


# ---------------------------------------------------------------------------
# Test 1 + 2: default mode + None arg → zero state mutation
# ---------------------------------------------------------------------------


def test_default_invocation_zero_audit_entries(mock_audit_chain):
    """run_curator_review() with no args produces ZERO append_audit calls."""
    result = curator.run_curator_review(synchronous=True)
    assert mock_audit_chain.call_count == 0, (
        f"Expected zero audit entries in default mode, got "
        f"{mock_audit_chain.call_count}: {mock_audit_chain.calls}"
    )
    assert result is not None
    assert isinstance(result, dict)


def test_none_arg_treated_as_true(mock_audit_chain):
    """run_curator_review(dry_run=None) is treated as dry_run=True
    (defense-in-depth per planning_context contract #4)."""
    result = curator.run_curator_review(synchronous=True, dry_run=None)
    assert mock_audit_chain.call_count == 0, (
        f"Expected zero audit entries when dry_run=None, got "
        f"{mock_audit_chain.call_count}: {mock_audit_chain.calls}"
    )
    assert result is not None


def test_default_invocation_skips_apply_automatic_transitions(
    mock_apply_automatic_transitions,
):
    """Default mode must NOT call apply_automatic_transitions (the
    deterministic inactivity prune that mutates skill state)."""
    curator.run_curator_review(synchronous=True)
    assert mock_apply_automatic_transitions.call_count == 0, (
        "Default mode (dry_run=True) called apply_automatic_transitions — "
        "the inactivity prune should be SKIPPED in dry-run mode."
    )


# ---------------------------------------------------------------------------
# Test 3: explicit dry_run=False → state mutation occurs
# ---------------------------------------------------------------------------


def test_explicit_false_performs_writes(mock_apply_automatic_transitions):
    """run_curator_review(dry_run=False) DOES run the deterministic
    inactivity prune. Verifies the default flip did NOT break live mode."""
    curator.run_curator_review(synchronous=True, dry_run=False)
    assert mock_apply_automatic_transitions.call_count > 0, (
        "Expected apply_automatic_transitions to be called when dry_run=False "
        "(live mode). The default flip should not have broken live mode."
    )


# ---------------------------------------------------------------------------
# Test 4 + 5: banner logging visibility
# ---------------------------------------------------------------------------


def test_default_logs_dry_run_banner(caplog):
    """Default-mode invocation logs CURATOR_DRY_RUN_BANNER so operators
    see the dry-run indication + how to enable live writes."""
    caplog.set_level(logging.INFO, logger="agent.curator")
    curator.run_curator_review(synchronous=True)
    banner_text = curator.CURATOR_DRY_RUN_BANNER
    # The banner is a multi-line string; check at least one distinctive
    # substring appears in any INFO log record emitted by agent.curator.
    records_text = "\n".join(
        r.getMessage() for r in caplog.records if r.name == "agent.curator"
    )
    assert "DRY-RUN" in records_text, (
        "Default-mode invocation did not log a DRY-RUN banner. Operators "
        "must see the dry-run indication. Captured agent.curator logs:\n"
        f"{records_text}"
    )


def test_live_mode_does_not_log_banner(caplog):
    """Live-mode invocation (dry_run=False) must NOT log the dry-run banner."""
    caplog.set_level(logging.INFO, logger="agent.curator")
    curator.run_curator_review(synchronous=True, dry_run=False)
    records_text = "\n".join(
        r.getMessage() for r in caplog.records if r.name == "agent.curator"
    )
    # The dry-run banner only appears in dry-run mode. Live mode may emit
    # other "auto:" logs but never the "DRY-RUN" banner.
    assert "DRY-RUN — REPORT ONLY" not in records_text, (
        "Live-mode invocation unexpectedly logged the dry-run banner. "
        "Captured agent.curator logs:\n" f"{records_text}"
    )
