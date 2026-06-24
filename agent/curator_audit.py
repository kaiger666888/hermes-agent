"""Tamper-evident audit log for curator patch lifecycle (CURATE-04).

Append-only JSONL log at ``<HERMES_HOME>/skills/.audit/log.jsonl`` where every
entry's ``entry_sha256`` chains to the previous entry's hash. Any edit or
deletion breaks the chain and is detectable via :func:`verify_chain`.

Genesis entry chaining:
    The very first entry's ``prev_sha256`` is the SHA-256 of empty bytes::

        GENESIS_PREV_SHA256 = hashlib.sha256(b"").hexdigest()
                           = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

Trust model (single-operator):
    v6 assumes one trusted operator per PROJECT.md. The sha256 chain detects
    tampering but does not prevent it (any process with write access to the
    file can rewrite the entire chain). Cryptographic signing (GPG) is
    FUTURE-V6; v6's threat model is "did I or a bug accidentally mutate
    this?" not "did an adversary forge entries?".

Append-only contract:
    This module exposes NO edit or delete API. Retraction = append a new
    entry with ``action="retract"`` referencing the original ``entry_id``.

Concurrency (Pitfall #6):
    Single-process assumption. If a future version allows concurrent curator
    + CLI writes, add file locking (deferred).

Serialization consistency (Pitfall #2 + #8):
    A single private :func:`_serialize_entry_for_sha256` helper computes
    the canonical JSON form used by BOTH append and verify. This prevents
    drift (e.g., one path using ``ensure_ascii=True`` and the other
    ``ensure_ascii=False`` would silently break the chain on CN content).
    ``ensure_ascii=False`` is pinned in both paths so feedback_ids and
    content with Chinese characters round-trip cleanly.

Per CLAUDE.md conventions:
    - ``from __future__ import annotations`` for PEP 604 unions.
    - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
    - Lazy %-logging; specific exceptions bound with ``as exc``.
    - ``get_hermes_home()`` from :mod:`hermes_constants` (NEVER Path.home()).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

GENESIS_PREV_SHA256: str = hashlib.sha256(b"").hexdigest()
"""SHA-256 of empty bytes — the ``prev_sha256`` of the very first entry.

Literal value: ``e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855``
"""

ACTION_VALUES: frozenset[str] = frozenset({
    "propose", "approve", "reject", "apply", "rollback", "auto_apply", "retract",
})


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #


class AuditChainError(Exception):
    """Raised when the audit log tail is corrupt (malformed final line).

    :func:`append_audit` refuses to chain from a broken entry — silently
    continuing would produce an entry whose ``prev_sha256`` references a
    malformed record that :func:`verify_chain` cannot recompute. The
    operator must repair the tail (e.g. via ``hermes curator audit-log
    --verify``) before new appends succeed.
    """


# --------------------------------------------------------------------------- #
# Path + serialization helpers
# --------------------------------------------------------------------------- #


def _audit_log_path() -> Path:
    """Return ``<HERMES_HOME>/skills/.audit/log.jsonl`` (parent auto-created)."""
    path = get_hermes_home() / "skills" / ".audit" / "log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _serialize_entry_for_sha256(entry: dict[str, Any]) -> str:
    """Canonical JSON form for sha256 computation (Pitfall #2 mitigation).

    Drops ``entry_sha256`` (it is the computed output, not an input),
    sorts keys for determinism, pins compact separators, and forces
    ``ensure_ascii=False`` so non-ASCII content (CN feedback_ids, skill
    names) round-trips identically in :func:`append_audit` and
    :func:`verify_chain`.

    Args:
        entry: Audit log entry dict (must NOT already be canonicalized).

    Returns:
        JSON string suitable for hashing. NEVER includes ``entry_sha256``.
    """
    payload = {k: v for k, v in entry.items() if k != "entry_sha256"}
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )


def _compute_entry_sha256(prev_sha256: str, entry: dict[str, Any]) -> str:
    """Compute ``sha256(prev_sha256 + canonical_json(entry))``.

    The ``prev_sha256`` prefix binds each entry to its predecessor — any
    mutation of an earlier entry changes every downstream hash.
    """
    payload = _serialize_entry_for_sha256(entry)
    return hashlib.sha256(
        (prev_sha256 + payload).encode("utf-8")
    ).hexdigest()


def _read_existing_lines(path: Path) -> list[str]:
    """Read non-blank lines from the audit log.

    Used by :func:`append_audit` to find the previous entry's sha256 and
    by :func:`verify_chain` to walk the chain.

    Returns an empty list when the log file does not exist yet (genesis
    case).
    """
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# --------------------------------------------------------------------------- #
# Public API — append
# --------------------------------------------------------------------------- #


def append_audit(
    *,
    action: str,
    patch_id: str,
    skill_id: str,
    operator: str = "system",
    feedback_ids: list[str] | None = None,
    eval_score: dict[str, Any] | None = None,
    commit_sha: str | None = None,
) -> str:
    """Append one entry to the audit log and return its ``entry_id``.

    Computes ``prev_sha256`` from the last line of the existing log (or
    :data:`GENESIS_PREV_SHA256` for the first entry), then computes
    ``entry_sha256`` via :func:`_compute_entry_sha256`.

    Args:
        action: One of :data:`ACTION_VALUES` (propose/approve/reject/apply/
            rollback/auto_apply/retract).
        patch_id: Evolution patch_id this entry references.
        skill_id: Target expert_id.
        operator: Username or ``"system"`` (default) for curator-proposed.
        feedback_ids: FeedbackRecord IDs cited as evidence (for propose).
        eval_score: Gate result snapshot (verdict, mean_delta, ...).
        commit_sha: Git sha set on apply/rollback entries; None otherwise.

    Returns:
        The new entry's ``entry_id`` (uuid4 hex string).

    Raises:
        ValueError: if ``action`` is not in :data:`ACTION_VALUES`.
        AuditChainError: if the existing log's final line is malformed
            JSON (refuses to chain from a broken tail).
    """
    if action not in ACTION_VALUES:
        raise ValueError(
            f"action must be one of {sorted(ACTION_VALUES)}, got {action!r}"
        )

    path = _audit_log_path()
    existing = _read_existing_lines(path)

    # Resolve prev_sha256 from the last line (or GENESIS).
    if not existing:
        prev_sha256 = GENESIS_PREV_SHA256
    else:
        last_line = existing[-1]
        try:
            last_entry = json.loads(last_line)
        except json.JSONDecodeError as exc:
            raise AuditChainError(
                f"audit log tail is malformed (line {len(existing)}: {exc}) "
                f"— refusing to chain from corrupt entry; repair with "
                f"`hermes curator audit-log --verify` before appending"
            ) from exc
        prev_sha256 = last_entry.get("entry_sha256") or GENESIS_PREV_SHA256

    entry_id = uuid.uuid4().hex
    ts = datetime.now(timezone.utc).isoformat()
    entry: dict[str, Any] = {
        "entry_id": entry_id,
        "prev_sha256": prev_sha256,
        "action": action,
        "ts": ts,
        "operator": operator,
        "patch_id": patch_id,
        "skill_id": skill_id,
        "feedback_ids": feedback_ids or [],
        "eval_score": eval_score or {},
        "commit_sha": commit_sha,
    }
    entry["entry_sha256"] = _compute_entry_sha256(prev_sha256, entry)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # WR-01: flush + fsync so the audit entry is durable on disk
        # before we report success. A single write() longer than
        # PIPE_BUF (4KB on POSIX) is NOT guaranteed atomic — entries
        # with rich eval_score dicts and CN feedback_ids easily exceed
        # that. A crash mid-write would leave a partial JSON line that
        # the next append_audit rejects as AuditChainError ("audit log
        # tail is malformed"), bricking the chain until manual repair.
        # fsync is the minimum durability guarantee for an append-only
        # chain whose integrity derives from every entry being present.
        f.flush()
        os.fsync(f.fileno())

    logger.info(
        "appended audit entry %s action=%s patch_id=%s skill_id=%s",
        entry_id, action, patch_id, skill_id,
    )
    return entry_id


# --------------------------------------------------------------------------- #
# Public API — verify
# --------------------------------------------------------------------------- #


def verify_chain(path: Path | None = None) -> list[dict[str, Any]]:
    """Walk the audit log and report any sha256 chain breaks.

    Args:
        path: Optional explicit log path (defaults to
            :func:`_audit_log_path`). Used by tests that point at fixture
            files.

    Returns:
        List of break dicts, one per broken entry::

            {"line": <int 1-based>, "error": "<str>"}

        Empty list when the log is missing/empty OR fully consistent. Does
        NOT raise on a break — callers (CLI ``--verify``, tests) decide
        how to surface. Enumerates ALL breaks rather than stopping at the
        first (per RESEARCH Pattern 3).
    """
    if path is None:
        path = _audit_log_path()
    lines = _read_existing_lines(path)
    if not lines:
        return []

    breaks: list[dict[str, Any]] = []
    prev_sha256: str = GENESIS_PREV_SHA256

    for i, raw in enumerate(lines, start=1):
        # Step 1: parse JSON.
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            breaks.append({
                "line": i,
                "error": f"malformed JSON: {exc}",
            })
            # Cannot continue — we don't know this entry's sha256 to chain
            # forward. Mark every subsequent line as "orphaned" with a
            # prev-mismatch.
            for j in range(i + 1, len(lines) + 1):
                breaks.append({
                    "line": j,
                    "error": "orphaned (previous line was malformed)",
                })
            return breaks

        # Step 2: verify prev_sha256 field matches expected.
        actual_prev = entry.get("prev_sha256")
        if actual_prev != prev_sha256:
            breaks.append({
                "line": i,
                "error": (
                    f"prev_sha256 mismatch: expected {prev_sha256[:12]}..., "
                    f"got {(actual_prev or '<missing>')[:12]}..."
                ),
            })
            # Continue chaining from the entry's STATED prev so we catch
            # downstream breaks too — but only if it's present.
            if actual_prev:
                prev_sha256 = actual_prev

        # Step 3: recompute entry_sha256 and compare.
        stated_sha = entry.get("entry_sha256")
        recomputed = _compute_entry_sha256(
            entry.get("prev_sha256") or GENESIS_PREV_SHA256, entry,
        )
        if stated_sha != recomputed:
            breaks.append({
                "line": i,
                "error": (
                    f"entry_sha256 mismatch: stated "
                    f"{(stated_sha or '<missing>')[:12]}..., recomputed "
                    f"{recomputed[:12]}..."
                ),
            })

        # Chain forward using the STATED entry_sha256 so a single mutation
        # surfaces as exactly one break rather than cascading.
        prev_sha256 = stated_sha or recomputed

    return breaks


# --------------------------------------------------------------------------- #
# Public API — read with filters
# --------------------------------------------------------------------------- #


def read_audit(
    *,
    action: str | None = None,
    since: str | None = None,
    skill: str | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Read audit entries with optional filters.

    Args:
        action: Filter to entries with this action value (e.g. ``"apply"``).
            None returns all actions.
        since: ISO-8601 date/datetime lower bound on ``ts``. Parsed via
            :func:`datetime.fromisoformat`. None returns all dates.
        skill: Filter to entries targeting this ``skill_id``. None returns
            all skills.
        path: Optional explicit log path (for tests).

    Returns:
        List of entry dicts (parsed JSON), in file order (append-order).
        Malformed lines are logged + skipped (non-strict — use
        :func:`verify_chain` to surface them as breaks).
    """
    if path is None:
        path = _audit_log_path()
    lines = _read_existing_lines(path)

    since_dt: datetime | None = None
    if since is not None:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError as exc:
            raise ValueError(
                f"since must be ISO-8601 parseable, got {since!r}: {exc}"
            ) from exc
        # CR-02: ``--since 2026-06-01`` parses as a naive datetime, but
        # audit entries are always aware (``datetime.now(timezone.utc)
        # .isoformat()`` → ``+00:00``). Without normalization, the
        # naive-vs-aware comparison raised TypeError, was caught as
        # "unparseable ts", and silently dropped every entry. Promote
        # naive since to aware UTC (midnight UTC by convention).
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)

    out: list[dict[str, Any]] = []
    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("skipping malformed audit line: %s", exc)
            continue
        if action is not None and entry.get("action") != action:
            continue
        if skill is not None and entry.get("skill_id") != skill:
            continue
        if since_dt is not None:
            # WR-02: split parse from compare so the diagnostic is
            # accurate. The TypeError from the comparison (naive vs
            # aware — see CR-02) used to be caught here and logged
            # misleadingly as "unparseable ts". Now the parse only
            # catches genuine parse failures; the comparison is its
            # own statement and operates on normalized-aware values.
            try:
                entry_ts = datetime.fromisoformat(entry.get("ts", ""))
            except (ValueError, TypeError):
                logger.warning(
                    "audit entry %s has unparseable ts=%r — skipping",
                    entry.get("entry_id", "<unknown>"), entry.get("ts"),
                )
                continue
            # CR-02: defensive — production writes are always aware, but
            # legacy data or hand-edited fixtures could be naive. Promote
            # to aware UTC so the comparison never raises TypeError.
            if entry_ts.tzinfo is None:
                entry_ts = entry_ts.replace(tzinfo=timezone.utc)
            if entry_ts < since_dt:
                continue
        out.append(entry)
    return out
