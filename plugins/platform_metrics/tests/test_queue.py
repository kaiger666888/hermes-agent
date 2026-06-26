"""Tests for plugins.platform_metrics.queue (DATA-03 JSONL queue).

Phase 42 Plan 03 Task 1 — TDD RED: tests assert the JSONL queue contract
that ``queue.py`` must satisfy. Mirrors the v6.0 EVOL-02 pattern
(``agent/evolution/queue.py``) but with ``TuningSuggestion`` instead of
``PatchRecord``.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ──────────────────────────────────────────────────────────────────────────
# Fixture helpers
# ──────────────────────────────────────────────────────────────────────────


def _make_suggestion(
    *,
    suggestion_id: str = "urban-fantasy-light-01_high_hook_dropoff_1700000000",
    formula_id: str = "urban-fantasy-light-01",
    status: str = "pending",
    ts_queued: str | None = None,
) -> "object":
    """Build a TuningSuggestion fixture with sensible defaults."""
    from plugins.platform_metrics.schema import (
        MetricTrigger,
        TuningSuggestion,
    )

    if ts_queued is None:
        ts_queued = datetime.now(timezone.utc).isoformat()
    return TuningSuggestion(
        suggestion_id=suggestion_id,
        formula_id=formula_id,
        trigger=MetricTrigger.HIGH_HOOK_DROPOFF,
        observed_metric=0.32,
        threshold=0.20,
        suggested_action="加 hook 强度",
        rationale="hook_dropoff exceeds threshold",
        evidence=["fb_1", "v1"],
        status=status,
        ts_queued=ts_queued,
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 1: append_suggestion writes queue.jsonl
# ──────────────────────────────────────────────────────────────────────────


def test_append_suggestion_writes_queue_jsonl(tmp_path: Path) -> None:
    """append_suggestion writes a single JSON line to queue.jsonl."""
    from plugins.platform_metrics.queue import append_suggestion

    suggestion = _make_suggestion()
    append_suggestion(suggestion, tuning_dir=tmp_path)

    queue_path = tmp_path / "queue.jsonl"
    assert queue_path.exists()
    lines = queue_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["suggestion_id"] == suggestion.suggestion_id
    assert parsed["status"] == "pending"


# ──────────────────────────────────────────────────────────────────────────
# Test 2: append rejects non-pending status
# ──────────────────────────────────────────────────────────────────────────


def test_append_rejects_non_pending(tmp_path: Path) -> None:
    """append_suggestion raises ValueError on status != 'pending'."""
    from plugins.platform_metrics.queue import append_suggestion

    suggestion = _make_suggestion(status="applied")
    with pytest.raises(ValueError, match="pending"):
        append_suggestion(suggestion, tuning_dir=tmp_path)


# ──────────────────────────────────────────────────────────────────────────
# Test 3: read_queue pending returns only pending
# ──────────────────────────────────────────────────────────────────────────


def test_read_queue_pending_returns_only_pending(tmp_path: Path) -> None:
    """read_queue(status='pending') returns all pending suggestions."""
    from plugins.platform_metrics.queue import append_suggestion, read_queue

    for i in range(3):
        s = _make_suggestion(
            suggestion_id=f"id_{i}",
            ts_queued=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc).isoformat(),
        )
        append_suggestion(s, tuning_dir=tmp_path)

    pending = read_queue(tuning_dir=tmp_path, status="pending")
    assert len(pending) == 3
    # Sorted by ts_queued (ISO strings sort chronologically).
    assert pending[0].suggestion_id == "id_0"
    assert pending[2].suggestion_id == "id_2"


# ──────────────────────────────────────────────────────────────────────────
# Test 4: read_queue applied reads applied.jsonl
# ──────────────────────────────────────────────────────────────────────────


def test_read_queue_applied_reads_applied_file(tmp_path: Path) -> None:
    """read_queue(status='applied') reads applied.jsonl directly."""
    from plugins.platform_metrics.queue import read_queue

    # Simulate post-approval state: write a record to applied.jsonl.
    applied_path = tmp_path / "applied.jsonl"
    record = {
        "suggestion_id": "abc",
        "formula_id": "f1",
        "trigger": "high_hook_dropoff",
        "observed_metric": 0.3,
        "threshold": 0.2,
        "suggested_action": "act",
        "rationale": "why",
        "evidence": [],
        "status": "applied",
        "ts_queued": "2026-01-01T00:00:00+00:00",
        "commit_sha": "deadbeef",
        "ts_applied": "2026-01-02T00:00:00+00:00",
    }
    applied_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    applied = read_queue(tuning_dir=tmp_path, status="applied")
    assert len(applied) == 1
    assert applied[0].suggestion_id == "abc"
    assert applied[0].commit_sha == "deadbeef"


# ──────────────────────────────────────────────────────────────────────────
# Test 5: move_suggestion pending → applied
# ──────────────────────────────────────────────────────────────────────────


def test_move_suggestion_pending_to_applied(tmp_path: Path) -> None:
    """move_suggestion moves a record from queue.jsonl to applied.jsonl."""
    from plugins.platform_metrics.queue import (
        append_suggestion,
        move_suggestion,
        read_queue,
    )

    suggestion = _make_suggestion(suggestion_id="move_me")
    append_suggestion(suggestion, tuning_dir=tmp_path)

    updated = move_suggestion(
        suggestion_id="move_me",
        target_status="applied",
        tuning_dir=tmp_path,
        commit_sha="abc123",
    )

    assert updated.status == "applied"
    assert updated.commit_sha == "abc123"
    assert updated.ts_applied is not None

    # queue.jsonl is now empty.
    assert read_queue(tuning_dir=tmp_path, status="pending") == []
    # applied.jsonl has the record.
    applied = read_queue(tuning_dir=tmp_path, status="applied")
    assert len(applied) == 1
    assert applied[0].suggestion_id == "move_me"
    assert applied[0].commit_sha == "abc123"


# ──────────────────────────────────────────────────────────────────────────
# Test 6: move_suggestion pending → rejected
# ──────────────────────────────────────────────────────────────────────────


def test_move_suggestion_pending_to_rejected(tmp_path: Path) -> None:
    """move_suggestion moves a record to rejected.jsonl with a reason."""
    from plugins.platform_metrics.queue import (
        append_suggestion,
        move_suggestion,
        read_queue,
    )

    suggestion = _make_suggestion(suggestion_id="reject_me")
    append_suggestion(suggestion, tuning_dir=tmp_path)

    updated = move_suggestion(
        suggestion_id="reject_me",
        target_status="rejected",
        tuning_dir=tmp_path,
        reason="test rejection",
    )

    assert updated.status == "rejected"
    assert updated.reason == "test rejection"
    assert updated.ts_rejected is not None

    rejected = read_queue(tuning_dir=tmp_path, status="rejected")
    assert len(rejected) == 1
    assert rejected[0].suggestion_id == "reject_me"


# ──────────────────────────────────────────────────────────────────────────
# Test 7: move_suggestion unknown id raises KeyError
# ──────────────────────────────────────────────────────────────────────────


def test_move_suggestion_unknown_id_raises(tmp_path: Path) -> None:
    """move_suggestion raises KeyError for an unknown suggestion_id."""
    from plugins.platform_metrics.queue import move_suggestion

    with pytest.raises(KeyError):
        move_suggestion(
            suggestion_id="bogus_id",
            target_status="applied",
            tuning_dir=tmp_path,
            commit_sha="abc",
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 8: move to applied requires commit_sha
# ──────────────────────────────────────────────────────────────────────────


def test_move_suggestion_applied_requires_commit_sha(tmp_path: Path) -> None:
    """move_suggestion(target_status='applied') requires commit_sha."""
    from plugins.platform_metrics.queue import (
        append_suggestion,
        move_suggestion,
    )

    suggestion = _make_suggestion(suggestion_id="no_sha")
    append_suggestion(suggestion, tuning_dir=tmp_path)

    with pytest.raises(ValueError, match="commit_sha"):
        move_suggestion(
            suggestion_id="no_sha",
            target_status="applied",
            tuning_dir=tmp_path,
            commit_sha=None,
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 9: move to rejected requires reason
# ──────────────────────────────────────────────────────────────────────────


def test_move_suggestion_rejected_requires_reason(tmp_path: Path) -> None:
    """move_suggestion(target_status='rejected') requires reason."""
    from plugins.platform_metrics.queue import (
        append_suggestion,
        move_suggestion,
    )

    suggestion = _make_suggestion(suggestion_id="no_reason")
    append_suggestion(suggestion, tuning_dir=tmp_path)

    with pytest.raises(ValueError, match="reason"):
        move_suggestion(
            suggestion_id="no_reason",
            target_status="rejected",
            tuning_dir=tmp_path,
            reason=None,
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 10: read_queue skips malformed lines (queue.jsonl)
# ──────────────────────────────────────────────────────────────────────────


def test_read_queue_malformed_line_skipped(tmp_path: Path) -> None:
    """read_queue logs + skips malformed lines in queue.jsonl."""
    from plugins.platform_metrics.queue import read_queue

    queue_path = tmp_path / "queue.jsonl"
    # A good line followed by a corrupt line followed by another good line.
    good = {
        "suggestion_id": "good_1",
        "formula_id": "f1",
        "trigger": "high_hook_dropoff",
        "observed_metric": 0.3,
        "threshold": 0.2,
        "suggested_action": "act",
        "rationale": "why",
        "evidence": [],
        "status": "pending",
        "ts_queued": "2026-01-01T00:00:00+00:00",
    }
    payload = (
        json.dumps(good) + "\n"
        + "{ this is not json\n"
        + json.dumps(good).replace("good_1", "good_2") + "\n"
    )
    queue_path.write_text(payload, encoding="utf-8")

    pending = read_queue(tuning_dir=tmp_path, status="pending")
    assert len(pending) == 2  # 2 good records, 1 corrupt skipped
    ids = {p.suggestion_id for p in pending}
    assert ids == {"good_1", "good_2"}


# ──────────────────────────────────────────────────────────────────────────
# Test 11: atomic rewrite preserves sibling records
# ──────────────────────────────────────────────────────────────────────────


def test_atomic_rewrite_preserves_other_records(tmp_path: Path) -> None:
    """Moving the middle of 3 records leaves the other 2 in queue.jsonl."""
    from plugins.platform_metrics.queue import (
        append_suggestion,
        move_suggestion,
        read_queue,
    )

    for i in range(3):
        s = _make_suggestion(
            suggestion_id=f"sib_{i}",
            ts_queued=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc).isoformat(),
        )
        append_suggestion(s, tuning_dir=tmp_path)

    move_suggestion(
        suggestion_id="sib_1",
        target_status="applied",
        tuning_dir=tmp_path,
        commit_sha="abc",
    )

    remaining = read_queue(tuning_dir=tmp_path, status="pending")
    assert len(remaining) == 2
    ids = {r.suggestion_id for r in remaining}
    assert ids == {"sib_0", "sib_2"}


# ──────────────────────────────────────────────────────────────────────────
# Test 12: strict mode raises on malformed applied.jsonl (WR-03 mirror)
# ──────────────────────────────────────────────────────────────────────────


def test_strict_mode_on_applied(tmp_path: Path) -> None:
    """read_queue(status='applied') raises on malformed lines (audit)."""
    from plugins.platform_metrics.queue import read_queue

    applied_path = tmp_path / "applied.jsonl"
    applied_path.write_text("{ corrupt\n", encoding="utf-8")

    with pytest.raises(ValueError, match="audit"):
        read_queue(tuning_dir=tmp_path, status="applied")
