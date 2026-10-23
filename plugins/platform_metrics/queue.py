"""queue.py — JSONL queue for formula tuning suggestions (DATA-03).

Mirrors the v6.0 EVOL-02 queue pattern (``agent/evolution/queue.py``)
but with :class:`TuningSuggestion` records instead of ``PatchRecord``.

Persistence layout under ``<HERMES_HOME>/skills/.feedback/tuning/``::

    queue.jsonl        # pending suggestions (one TuningSuggestion per line)
    applied.jsonl      # approved + applied suggestions (with commit_sha)
    rejected.jsonl     # rejected suggestions (with reason)

Single-process assumption (mirror v6.0 RESEARCH Pitfall 5): JSONL append
is NOT atomic across processes. Phase 42 assumes only one
``hermes formula`` CLI invocation writes at a time. Worst case is a
duplicate ``suggestion_id`` (content-addressed, detectable on read) or
a corrupt line (caught by ``json.loads``, logged + skipped).

Atomic rewrite for :func:`move_suggestion` (temp + os.replace, mirroring
``agent/evolution/queue.py:_atomic_rewrite_jsonl``).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - Lazy %-logging; specific exceptions bound.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from plugins.platform_metrics.schema import TuningSuggestion

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants (mirror agent/evolution/queue.py:60-70)
# --------------------------------------------------------------------------- #

QUEUE_FILENAME = "queue.jsonl"
APPLIED_FILENAME = "applied.jsonl"
REJECTED_FILENAME = "rejected.jsonl"

_STATUS_TO_FILENAME: dict[str, str] = {
    "pending": QUEUE_FILENAME,
    "applied": APPLIED_FILENAME,
    "rejected": REJECTED_FILENAME,
}


# --------------------------------------------------------------------------- #
# JSONL helpers (mirror agent/evolution/queue.py:137 pattern)
# --------------------------------------------------------------------------- #


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one JSON record as a single line to *path*.

    Single-process assumption (mirror v6.0): no file locking.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _read_jsonl(path: Path, *, strict: bool = False) -> list[dict[str, Any]]:
    """Read a JSONL file, skipping + logging malformed lines.

    Mirrors ``agent/feedback_store.py:654`` and
    ``agent/evolution/queue.py:_read_jsonl`` patterns.

    WR-03 (audit-critical): for ``applied.jsonl`` and ``rejected.jsonl``,
    pass ``strict=True`` to raise on malformed lines instead of silently
    skipping. A malformed entry in an audit trail means a suggestion that
    WAS applied is invisible to ``read_queue(status="applied")`` —
    operators cannot rollback what they cannot see.
    """
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                if strict:
                    raise ValueError(
                        f"malformed JSON at {path}:{lineno} ({exc}) — "
                        f"audit-critical file requires manual recovery"
                    ) from exc
                logger.warning(
                    "malformed JSON at %s:%d (%s) — skipping line",
                    path, lineno, exc,
                )
                continue
            if isinstance(parsed, dict):
                out.append(parsed)
            else:
                if strict:
                    raise ValueError(
                        f"non-object JSON at {path}:{lineno} — audit-"
                        f"critical file requires manual recovery"
                    )
                logger.warning(
                    "non-object JSON at %s:%d — skipping line", path, lineno
                )
    return out


def _atomic_rewrite_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Rewrite *path* with *records* atomically (temp + os.replace).

    Used by :func:`move_suggestion` to remove the moved record from
    queue.jsonl. Writes to a temp file first, then atomically renames
    into place. Mirrors ``agent/evolution/queue.py:_atomic_rewrite_jsonl``
    verbatim (same temp+os.replace+cleanup pattern).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=".queue.", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file on any failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def append_suggestion(record: TuningSuggestion, tuning_dir: Path) -> None:
    """Append a pending TuningSuggestion to ``queue.jsonl``.

    Args:
        record: TuningSuggestion with status == "pending".
        tuning_dir: The tuning persistence directory
            (``<HERMES_HOME>/skills/.feedback/tuning/``).

    Raises:
        ValueError: if record.status != "pending" (only pending records
            may enter the queue — applied/rejected go via
            :func:`move_suggestion`).
    """
    if record.status != "pending":
        raise ValueError(
            f"append_suggestion requires status='pending', got "
            f"{record.status!r}"
        )
    # mode="json" ensures enums (MetricTrigger) serialize to their values
    # instead of returning the enum object (Pydantic v2 default is python mode).
    _append_jsonl(tuning_dir / QUEUE_FILENAME, record.model_dump(mode="json"))
    logger.info(
        "appended suggestion %s to %s",
        record.suggestion_id, QUEUE_FILENAME,
    )


def move_suggestion(
    *,
    suggestion_id: str,
    target_status: str,
    tuning_dir: Path,
    commit_sha: str | None = None,
    reason: str | None = None,
) -> TuningSuggestion:
    """Move a suggestion from ``queue.jsonl`` to ``applied.jsonl`` or ``rejected.jsonl``.

    Args:
        suggestion_id: The ID of the suggestion to move.
        target_status: Either "applied" or "rejected".
        tuning_dir: The tuning persistence directory.
        commit_sha: Required when target_status == "applied".
        reason: Required when target_status == "rejected".

    Returns:
        The updated TuningSuggestion (with status + transition metadata set).

    Raises:
        KeyError: if ``suggestion_id`` not found in ``queue.jsonl``.
        ValueError: if target_status is not "applied" or "rejected", or
            if commit_sha/reason is missing for the respective branch.
    """
    if target_status not in ("applied", "rejected"):
        raise ValueError(
            f"move_suggestion target_status must be 'applied' or "
            f"'rejected', got {target_status!r}"
        )
    if target_status == "applied" and not commit_sha:
        raise ValueError("move_suggestion to 'applied' requires commit_sha")
    if target_status == "rejected" and not reason:
        raise ValueError("move_suggestion to 'rejected' requires reason")

    queue_path = tuning_dir / QUEUE_FILENAME
    records = _read_jsonl(queue_path)
    target_idx: int | None = None
    for i, r in enumerate(records):
        if r.get("suggestion_id") == suggestion_id:
            target_idx = i
            break
    if target_idx is None:
        raise KeyError(
            f"suggestion_id {suggestion_id!r} not found in {QUEUE_FILENAME}"
        )

    raw = records[target_idx]
    now_iso = datetime.now(timezone.utc).isoformat()
    raw["status"] = target_status
    if target_status == "applied":
        raw["commit_sha"] = commit_sha
        raw["ts_applied"] = now_iso
        dest_filename = APPLIED_FILENAME
    else:
        raw["reason"] = reason
        raw["ts_rejected"] = now_iso
        dest_filename = REJECTED_FILENAME

    updated = TuningSuggestion.model_validate(raw)

    # WR-02 ordering: remove from queue FIRST, then append to destination.
    # A crash between the two writes leaves the suggestion "in flight"
    # (neither pending nor applied/rejected), which the operator can
    # recover from insights.jsonl + git history. Mirror v6.0 EVOL-02.
    remaining = [r for j, r in enumerate(records) if j != target_idx]
    _atomic_rewrite_jsonl(queue_path, remaining)
    _append_jsonl(tuning_dir / dest_filename, raw)

    logger.info(
        "moved suggestion %s from %s to %s",
        suggestion_id, QUEUE_FILENAME, dest_filename,
    )
    return updated


def read_queue(
    *,
    tuning_dir: Path,
    status: str = "pending",
    formula_id: str | None = None,
) -> list[TuningSuggestion]:
    """Read suggestions from the queue, filtered by status + optional formula.

    Args:
        tuning_dir: The tuning persistence directory.
        status: One of "pending", "applied", "rejected".
        formula_id: Optional formula_id filter.

    Returns:
        list of :class:`TuningSuggestion`. Sorted by ``ts_queued`` for
        deterministic ordering. Malformed lines in queue.jsonl are
        skipped + logged; malformed lines in applied.jsonl / rejected.jsonl
        raise (WR-03 audit-critical strict mode).
    """
    filename = _STATUS_TO_FILENAME.get(status)
    if filename is None:
        raise ValueError(
            f"read_queue status must be one of "
            f"{sorted(_STATUS_TO_FILENAME)}, got {status!r}"
        )
    path = tuning_dir / filename
    # WR-03: applied/rejected are audit-critical — raise on malformed.
    strict = status in ("applied", "rejected")
    raw_records = _read_jsonl(path, strict=strict)
    out: list[TuningSuggestion] = []
    for raw in raw_records:
        try:
            rec = TuningSuggestion.model_validate(raw)
        except ValidationError as exc:
            logger.warning(
                "skipping malformed TuningSuggestion in %s: %s", path, exc
            )
            continue
        if formula_id is not None and rec.formula_id != formula_id:
            continue
        out.append(rec)
    # Deterministic sort by ts_queued (ISO 8601 UTC strings sort
    # chronologically). Stable sort preserves file order for ties.
    out.sort(key=lambda r: r.ts_queued)
    return out


__all__ = [
    "QUEUE_FILENAME",
    "APPLIED_FILENAME",
    "REJECTED_FILENAME",
    "append_suggestion",
    "move_suggestion",
    "read_queue",
]
