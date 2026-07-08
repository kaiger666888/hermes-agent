"""Phase 65 (CURATOR-LIVE-GUARDS) tests — bias canary pre-check + audit tick_mode.

Wave 0 unit tests for the runtime primitives Plan 02 (CLI wiring) depends on:

* :func:`agent.curator.run_bias_canary_pre_check` — sync deterministic pre-check
  wrapping :func:`agent.curator_bias_canary.check_record` over 5 known-bad
  fixtures. Catches >=4/5 required per v12.0 EVAL-03 baseline.
* :func:`agent.curator_audit.append_audit` — extended with optional
  ``tick_mode`` / ``canary_pass`` / ``caught_count`` / ``mutation_summary``
  kwargs (CURATE-03). Backward compatible: legacy callers omit the kwargs and
  produce entries with those fields absent.
* :func:`agent.curator_audit.verify_chain` — passes on mixed-schema logs
  (legacy entries without ``tick_mode`` + extended entries with).

Per CLAUDE.md: ``encoding="utf-8"`` on every ``open()``; ``HERMES_HOME``
redirected by conftest fixture per test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent import curator
from agent.curator_audit import (
    ACTION_VALUES,
    append_audit,
    verify_chain,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "curator_bias_canary"
    / "known_bad_records.jsonl"
)


# ---------------------------------------------------------------------------
# run_bias_canary_pre_check tests (CURATE-02)
# ---------------------------------------------------------------------------


def test_pre_check_catches_four_of_five() -> None:
    """Pre-check against repo-bundled fixtures catches >=4/5 records.

    Record #5 (bad-unsupported-claim) is LLM-only by design — its 3
    deterministic checks pass and only the async LLM ``claim_support`` pass
    would flag it. v12.0 EVAL-03 baseline threshold of >=4 suffices.
    """
    passed, caught, failed_ids = curator.run_bias_canary_pre_check()

    assert passed is True, f"expected pass at threshold 4, got caught={caught}"
    assert caught >= 4, f"expected >=4 deterministic catches, got {caught}"
    # The only record that may be in failed_ids is the LLM-only one.
    assert set(failed_ids).issubset({"bad-unsupported-claim"}), (
        f"unexpected non-LLM-only record not caught: {failed_ids}"
    )


def test_pre_check_threshold_respected() -> None:
    """Setting threshold=5 returns passed=False because record #5 is LLM-only."""
    passed, caught, _failed_ids = curator.run_bias_canary_pre_check(threshold=5)

    assert passed is False, "threshold=5 must fail since max deterministic catch is 4"
    assert caught == 4, f"expected exactly 4 deterministic catches, got {caught}"


def test_pre_check_missing_fixtures(tmp_path: Path) -> None:
    """When fixtures_path points to a non-existent file, fail safe.

    Returns ``(False, 0, ["<fixtures-missing>"])`` and logs a warning — never
    raises. Operators relying on the canary gate must never get a green light
    just because the fixture file was accidentally deleted.
    """
    bogus = tmp_path / "nope.jsonl"
    passed, caught, failed_ids = curator.run_bias_canary_pre_check(
        fixtures_path=bogus,
    )

    assert passed is False
    assert caught == 0
    assert failed_ids == ["<fixtures-missing>"]


def test_pre_check_custom_threshold() -> None:
    """Custom threshold=3 passes when the fixtures yield 4 deterministic catches."""
    passed, caught, _failed_ids = curator.run_bias_canary_pre_check(
        threshold=3,
    )

    assert passed is True
    assert caught == 4


def test_pre_check_uses_bundled_default_path() -> None:
    """Default fixtures_path points at the repo-bundled JSONL (REPO_FIXTURES)."""
    # Sanity: the default path resolution should match REPO_FIXTURES so the
    # pre-check works when operators run `hermes` from a repo checkout.
    from agent.curator import _bias_canary_fixtures_path

    assert _bias_canary_fixtures_path() == REPO_FIXTURES


# ---------------------------------------------------------------------------
# append_audit tick_mode extension tests (CURATE-03)
# ---------------------------------------------------------------------------


def test_append_audit_with_tick_mode(tmp_path, monkeypatch) -> None:
    """append_audit with tick_mode='live' writes entry with all new fields."""
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(
        "agent.curator_audit._audit_log_path", lambda: log
    )

    entry_id = append_audit(
        action="auto_apply",
        patch_id="live-tick-test",
        skill_id="<live-tick>",
        operator="test",
        tick_mode="live",
        canary_pass=True,
        caught_count=4,
        mutation_summary={"skills_archived": ["old-utility"]},
    )

    assert entry_id, "append_audit must return a non-empty entry_id"

    entries = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    e = entries[0]
    assert e["tick_mode"] == "live"
    assert e["canary_pass"] is True
    assert e["caught_count"] == 4
    assert e["mutation_summary"] == {"skills_archived": ["old-utility"]}
    # Verify chain is intact.
    assert verify_chain(log) == []


def test_append_audit_backward_compat(tmp_path, monkeypatch) -> None:
    """Legacy caller passing no new kwargs produces an entry WITHOUT tick_mode key."""
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(
        "agent.curator_audit._audit_log_path", lambda: log
    )

    append_audit(
        action="propose",
        patch_id="legacy-patch",
        skill_id="some-skill",
    )

    entries = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    e = entries[0]
    # Critical backward-compat invariant: new keys absent when kwargs not passed.
    assert "tick_mode" not in e, "legacy entry must NOT contain tick_mode key"
    assert "canary_pass" not in e
    assert "caught_count" not in e
    assert "mutation_summary" not in e
    assert verify_chain(log) == []


def test_append_audit_rejects_invalid_tick_mode(tmp_path, monkeypatch) -> None:
    """tick_mode must be one of {'live', 'dry_run'} or None."""
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(
        "agent.curator_audit._audit_log_path", lambda: log
    )

    with pytest.raises(ValueError, match="tick_mode"):
        append_audit(
            action="auto_apply",
            patch_id="p1",
            skill_id="s1",
            tick_mode="bogus",
        )


def test_append_audit_canary_pass_requires_live(tmp_path, monkeypatch) -> None:
    """canary_pass=True requires tick_mode='live' (consistency invariant)."""
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(
        "agent.curator_audit._audit_log_path", lambda: log
    )

    with pytest.raises(ValueError, match="canary_pass"):
        append_audit(
            action="auto_apply",
            patch_id="p1",
            skill_id="s1",
            tick_mode="dry_run",
            canary_pass=True,
        )

    # canary_pass=False with tick_mode='dry_run' is fine (no inconsistency).
    append_audit(
        action="auto_apply",
        patch_id="p2",
        skill_id="s2",
        tick_mode="dry_run",
        canary_pass=False,
    )


def test_verify_chain_mixed_schema(tmp_path, monkeypatch) -> None:
    """verify_chain passes on a log mixing legacy + tick_mode-extended entries."""
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(
        "agent.curator_audit._audit_log_path", lambda: log
    )

    # Entry 1: legacy (no tick_mode).
    append_audit(
        action="propose",
        patch_id="legacy",
        skill_id="legacy-skill",
    )
    # Entry 2: extended with tick_mode.
    append_audit(
        action="auto_apply",
        patch_id="live-tick",
        skill_id="<live-tick>",
        tick_mode="live",
        canary_pass=True,
        caught_count=4,
    )
    # Entry 3: legacy again (mixed ordering).
    append_audit(
        action="apply",
        patch_id="manual-apply",
        skill_id="manual-skill",
    )

    breaks = verify_chain(log)
    assert breaks == [], f"expected no breaks in mixed-schema log, got {breaks}"


def test_append_audit_dry_run_tick_mode(tmp_path, monkeypatch) -> None:
    """tick_mode='dry_run' writes a valid entry with that field."""
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(
        "agent.curator_audit._audit_log_path", lambda: log
    )

    append_audit(
        action="auto_apply",
        patch_id="dry-run-tick",
        skill_id="<dry-run-tick>",
        tick_mode="dry_run",
        canary_pass=False,
        caught_count=0,
    )

    entries = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    e = entries[0]
    assert e["tick_mode"] == "dry_run"
    assert e["canary_pass"] is False
    assert e["caught_count"] == 0
    assert verify_chain(log) == []


# Sanity check that ACTION_VALUES is unchanged (regression guard).
def test_action_values_unchanged() -> None:
    """ACTION_VALUES must not lose any existing action (regression guard)."""
    expected = {
        "propose", "approve", "reject", "apply",
        "rollback", "auto_apply", "retract",
    }
    assert set(ACTION_VALUES) == expected, (
        f"ACTION_VALUES drifted: {set(ACTION_VALUES)} != {expected}"
    )
