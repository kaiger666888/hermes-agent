"""EVOL-03 — JSONL review queue lifecycle for candidate patches.

Persistence layout under ``<HERMES_HOME>/skills/.feedback/evolution/``::

    queue.jsonl        # pending patches (one PatchRecord per line)
    applied.jsonl      # approved + applied patches (with commit_sha)
    rejected.jsonl     # rejected patches (with reason)
    failed_gate.jsonl  # patches that failed the eval gate (never enter queue)
    insights.jsonl     # raw LLM aggregation output (append-only audit log)

Single-process assumption (RESEARCH Pitfall 5 + CONTEXT.md Claude's
Discretion): JSONL append is NOT atomic across processes. Phase 31
assumes only one ``hermes feedback`` CLI invocation writes at a time.
Worst case is a duplicate ``patch_id`` (content-addressed, detectable on
read) or a corrupt line (caught by ``json.loads``, logged + skipped per
the feedback_store.py:654 pattern).

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

from pydantic import BaseModel, Field, ValidationError, model_validator

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Canonical v4/v5 protected refs (SC-6 additive-only check). Reused by
# apply.py's apply_patch_transaction. The check is filename-suffix based
# (``any(protected in f for protected in PROTECTED_REFS)``) so it matches
# regardless of which expert's references/ subdir the file lives under.
PROTECTED_REFS: tuple[str, ...] = (
    "snowflake-method.md",
    "e-konte-format.md",
    "scamper-variations.md",
    "dreamina-cli-baseline.md",
    "v86-pipeline-mapping.md",
)

PATCH_STATUSES: frozenset[str] = frozenset({
    "pending", "applied", "rejected", "failed_gate",
})
"""Allowed values for :attr:`PatchRecord.status`."""

QUEUE_FILENAME = "queue.jsonl"
APPLIED_FILENAME = "applied.jsonl"
REJECTED_FILENAME = "rejected.jsonl"
FAILED_GATE_FILENAME = "failed_gate.jsonl"
INSIGHTS_FILENAME = "insights.jsonl"

_STATUS_TO_FILENAME: dict[str, str] = {
    "pending": QUEUE_FILENAME,
    "applied": APPLIED_FILENAME,
    "rejected": REJECTED_FILENAME,
}


# --------------------------------------------------------------------------- #
# Pydantic schema
# --------------------------------------------------------------------------- #


class PatchRecord(BaseModel):
    """A candidate patch pending operator review (EVOL-03).

    Attributes:
        patch_id: Content-addressed ID ``f"{skill_id}_{ts_unix}_{sha256[:16]}"``.
        skill_id: The expert_id this patch targets.
        insight_id: The InsightRecord that motivated this patch.
        unified_diff: Git-compatible unified diff text.
        feedback_chain: Feedback record IDs cited as evidence.
        llm_rationale: LLM's stated reason for proposing the change.
        eval_gate_score: gate.py result snapshot (verdict, mean_delta, ...).
        status: Lifecycle status (pending / applied / rejected / failed_gate).
        ts_queued: ISO-8601 UTC timestamp when the patch entered the queue.
        commit_sha: Set when status == "applied" (the apply commit's SHA).
        ts_applied: Set when status == "applied".
        reason: Set when status == "rejected" (operator's rejection reason).
        ts_rejected: Set when status == "rejected".
    """

    patch_id: str = Field(min_length=1)
    skill_id: str = Field(min_length=1)
    insight_id: str = Field(min_length=1)
    unified_diff: str = Field(min_length=1)
    feedback_chain: list[str] = Field(min_length=1)
    llm_rationale: str = Field(min_length=1)
    eval_gate_score: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    ts_queued: str = Field(min_length=1)
    # Optional status-transition metadata.
    commit_sha: str | None = None
    ts_applied: str | None = None
    reason: str | None = None
    ts_rejected: str | None = None

    @model_validator(mode="after")
    def _status_in_allowed_set(self) -> "PatchRecord":
        if self.status not in PATCH_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(PATCH_STATUSES)}, "
                f"got {self.status!r}"
            )
        return self


# --------------------------------------------------------------------------- #
# JSONL helpers (mirror agent/feedback_store.py:336 pattern)
# --------------------------------------------------------------------------- #


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one JSON record as a single line to *path*.

    Single-process assumption (RESEARCH Pitfall 5): no file locking.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _read_jsonl(path: Path, *, strict: bool = False) -> list[dict[str, Any]]:
    """Read a JSONL file, skipping + logging malformed lines.

    Mirrors the ``_read_bucket_records`` pattern at
    agent/feedback_store.py:654 — malformed lines are logged at WARNING
    with line number and skipped, never raised.

    WR-03: for audit-critical files (``applied.jsonl``, ``rejected.jsonl``,
    ``insights.jsonl``), pass ``strict=True`` to raise on malformed lines
    instead of silently skipping. A malformed entry in an audit trail
    means a patch that WAS applied/committed is invisible to
    ``read_queue(status="applied")`` — operators cannot rollback what
    they cannot see.
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


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def append_patch(record: PatchRecord, evolution_dir: Path) -> None:
    """Append a pending patch record to ``queue.jsonl``.

    Args:
        record: PatchRecord with status == "pending".
        evolution_dir: The evolution persistence directory
            (``<HERMES_HOME>/skills/.feedback/evolution/``).

    Raises:
        ValueError: if record.status != "pending".
    """
    if record.status != "pending":
        raise ValueError(
            f"append_patch requires status='pending', got {record.status!r}"
        )
    _append_jsonl(evolution_dir / QUEUE_FILENAME, record.model_dump())
    logger.info("appended patch %s to %s", record.patch_id, QUEUE_FILENAME)


def move_patch(
    *,
    patch_id: str,
    target_status: str,
    evolution_dir: Path,
    commit_sha: str | None = None,
    reason: str | None = None,
) -> PatchRecord:
    """Move a patch from ``queue.jsonl`` to ``applied.jsonl`` or ``rejected.jsonl``.

    Args:
        patch_id: The ID of the patch to move.
        target_status: Either "applied" or "rejected".
        evolution_dir: The evolution persistence directory.
        commit_sha: Required when target_status == "applied".
        reason: Required when target_status == "rejected".

    Returns:
        The updated PatchRecord (with status + transition metadata set).

    Raises:
        KeyError: if ``patch_id`` not found in ``queue.jsonl``.
        ValueError: if target_status is not "applied" or "rejected", or
            if commit_sha/reason is missing for the respective branch.
    """
    if target_status not in ("applied", "rejected"):
        raise ValueError(
            f"move_patch target_status must be 'applied' or 'rejected', "
            f"got {target_status!r}"
        )
    if target_status == "applied" and not commit_sha:
        raise ValueError("move_patch to 'applied' requires commit_sha")
    if target_status == "rejected" and not reason:
        raise ValueError("move_patch to 'rejected' requires reason")

    queue_path = evolution_dir / QUEUE_FILENAME
    records = _read_jsonl(queue_path)
    target_idx: int | None = None
    for i, r in enumerate(records):
        if r.get("patch_id") == patch_id:
            target_idx = i
            break
    if target_idx is None:
        raise KeyError(
            f"patch_id {patch_id!r} not found in {QUEUE_FILENAME}"
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

    updated = PatchRecord.model_validate(raw)

    # WR-02: safer ordering — remove from queue FIRST, then append to
    # destination. A crash between the two writes leaves the patch "in
    # flight" (neither pending nor applied/rejected), which the operator
    # can recover from insights.jsonl + git history. A crash after the
    # OLD order (append-then-rewrite) left the patch in BOTH files — a
    # duplicate that could trigger a double-apply on the next approve.
    remaining = [r for j, r in enumerate(records) if j != target_idx]
    _atomic_rewrite_jsonl(queue_path, remaining)
    _append_jsonl(evolution_dir / dest_filename, raw)

    logger.info(
        "moved patch %s from %s to %s",
        patch_id, QUEUE_FILENAME, dest_filename,
    )
    return updated


def read_queue(
    *,
    evolution_dir: Path,
    status: str = "pending",
    skill_id: str | None = None,
) -> list[PatchRecord]:
    """Read patches from the queue, filtered by status + optional skill.

    Args:
        evolution_dir: The evolution persistence directory.
        status: One of "pending", "applied", "rejected". (failed_gate
            records are intentionally not surfaced here — use the file
            directly if needed.)
        skill_id: Optional skill filter.

    Returns:
        list of :class:`PatchRecord`. Malformed lines are skipped + logged
        (mirrors feedback_store.py:654).
    """
    filename = _STATUS_TO_FILENAME.get(status)
    if filename is None:
        raise ValueError(
            f"read_queue status must be one of "
            f"{sorted(_STATUS_TO_FILENAME)}, got {status!r}"
        )
    path = evolution_dir / filename
    # WR-03: applied/rejected are audit-critical — raise on malformed
    # lines so operators notice data loss rather than silently skipping.
    strict = status in ("applied", "rejected")
    raw_records = _read_jsonl(path, strict=strict)
    out: list[PatchRecord] = []
    for raw in raw_records:
        try:
            rec = PatchRecord.model_validate(raw)
        except ValidationError as exc:
            logger.warning(
                "skipping malformed PatchRecord in %s: %s", path, exc
            )
            continue
        if skill_id is not None and rec.skill_id != skill_id:
            continue
        out.append(rec)
    return out


def append_failed_gate(rejection: dict[str, Any], evolution_dir: Path) -> None:
    """Append a failed-gate rejection record to ``failed_gate.jsonl``.

    These records NEVER appear in :func:`read_queue` output — they are
    kept separate so operators can audit gate failures without polluting
    the review queue.
    """
    _append_jsonl(evolution_dir / FAILED_GATE_FILENAME, rejection)
    logger.info(
        "appended failed-gate rejection for patch %s",
        rejection.get("patch_id", "<unknown>"),
    )


# --------------------------------------------------------------------------- #
# Internal: atomic rewrite (temp + os.replace)
# --------------------------------------------------------------------------- #


def _atomic_rewrite_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Rewrite *path* with *records* atomically (temp + os.replace).

    Used by :func:`move_patch` to remove the moved record from
    queue.jsonl. Writes to a temp file first, then atomically renames
    into place (mirrors utils.atomic_json_write's os.replace pattern).
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
