"""Durable feedback store with bucketed jsonl persistence + decay-weighted index.

Phase 29 Plan 01 — the persistence foundation for the v6.0 feedback loop.

This module owns ALL feedback persistence under
``<HERMES_HOME>/skills/.feedback/``. On-disk layout (per CONTEXT.md storage
layout decision + RESEARCH Pattern 2)::

    ~/.hermes/skills/.feedback/
    +-- index.json                  # atomic, single source of truth (STORE-02)
    +-- buckets/
    |   +-- <skill_id>/
    |       +-- <source>.jsonl      # append-only, one FeedbackRecord per line
    +-- dedup/
    |   +-- sha256-registry.jsonl   # append-only audit log
    +-- archive/                    # migration originals preserved here
    +-- incoming/                   # Phase 28 flat staging (migration source)

The index is updated atomically on every write (``utils.atomic_json_write``
— temp + fsync + os.replace). Bucket files are appended to directly (O(1)
per write) because they are append-only and ``atomic_json_write`` would be
O(N) per write.

Single-process MVP (per CONTEXT.md Deferred Ideas + RESEARCH Pitfall #3):
Phase 29 assumes only one ``FeedbackStore`` instance writes at a time. No
file locking. If Phase 32's Curator runs concurrently with operator CLI,
a future phase will add ``fcntl.flock`` / ``msvcrt.locking``. The worst
case today is a duplicate record that Plan 02's dedup catches or a
``hermes feedback dedup-repair`` command cleans up.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - ``encoding="utf-8"`` on every ``open()`` / ``read_text()`` /
    ``write_text()`` (Ruff PLW1514 — RESEARCH Pitfall #1).
  - ``get_hermes_home()`` for path resolution (never the raw home-dir call).
  - Specific exceptions bound with ``as exc``, lazy %-logging.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.feedback_schema import FeedbackRecord
from hermes_constants import get_hermes_home
from utils import atomic_json_write

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_DECAY_WINDOW_DAYS: int = 180
"""Default time-decay window (CONTEXT.md STORE-03).

``weight = max(0.1, 1.0 - age_days / DEFAULT_DECAY_WINDOW_DAYS)``.
Operator can override via ``feedback.decay_window_days`` in config.yaml.
"""

_INDEX_VERSION: int = 1
"""On-disk index.json schema version (forward-compat for future changes)."""

_WEIGHT_FLOOR: float = 0.1
"""Linear decay floor (CONTEXT.md STORE-03): old signal never fully zeroes."""


# ── Decay primitives (STORE-03) ──────────────────────────────────────────────


def compute_weight(
    ts: datetime,
    *,
    now: datetime | None = None,
    decay_window_days: int = DEFAULT_DECAY_WINDOW_DAYS,
) -> float:
    """Linear time-decay weight for a feedback record.

    - 0 days old: weight = 1.0 (full signal)
    - decay_window_days / 2 old: weight = 0.5
    - decay_window_days old: weight = 0.0 floored at 0.1
    - older than decay_window_days: weight = 0.1 (never fully zero)

    The weight is computed at query / index-update time, NEVER stored on
    the record itself (CONTEXT.md specifics line 111 — keeps weights fresh
    and decay-window tuning cheap).

    Args:
        ts: timezone-aware timestamp of the record.
        now: optional timezone-aware "as-of" timestamp; defaults to
            ``datetime.now(timezone.utc)``.
        decay_window_days: decay window (default 180).

    Returns:
        Float weight in ``[0.1, 1.0]``.

    Raises:
        TypeError: if ``ts`` (or ``now``) is timezone-naive. The check is
            defensive even though ``FeedbackRecord._ts_has_tz`` already
            rejects naive datetimes at schema time — internal computations
            must also use tz-aware UTC (RESEARCH Pitfall #7).
    """
    if ts.tzinfo is None:
        raise TypeError(
            "compute_weight(ts=...) requires a timezone-aware datetime; "
            "got a naive datetime."
        )
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        raise TypeError(
            "compute_weight(now=...) requires a timezone-aware datetime; "
            "got a naive datetime."
        )

    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
    raw_weight = 1.0 - (age_days / float(decay_window_days))
    return max(_WEIGHT_FLOOR, raw_weight)


def recompute_bucket_weighted_count(
    records: list[FeedbackRecord],
    *,
    now: datetime | None = None,
    decay_window_days: int = DEFAULT_DECAY_WINDOW_DAYS,
) -> float:
    """Sum of per-record weights for active records in a bucket.

    Superseded records contribute weight 0 (their effective status is
    ``"superseded"``). Since ``FeedbackRecord`` has no ``status`` field
    (Plan 02 tracks status in ``index.by_sha256``, not on the record),
    the caller is responsible for pre-filtering superseded records OR
    attaching a synthetic ``status`` attribute. This function uses
    ``getattr(r, "status", "active")`` so callers can pass either a
    pre-filtered list OR an annotated list.

    Args:
        records: list of FeedbackRecord instances in the bucket.
        now: optional "as-of" timestamp.
        decay_window_days: decay window.

    Returns:
        Sum of per-record weights, rounded to 2 decimals for clean
        ``index.json`` reads.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    total = sum(
        compute_weight(r.ts, now=now, decay_window_days=decay_window_days)
        for r in records
        if getattr(r, "status", "active") == "active"
    )
    return round(total, 2)


def _load_decay_window_days_from_config() -> int:
    """Read ``feedback.decay_window_days`` from config.yaml.

    Tolerates missing config file, missing ``feedback`` section, and
    non-integer values (all logged at debug and fall back to the default).
    Never raises — ``FeedbackStore.__init__`` must not crash on a
    misconfigured operator environment.

    Pattern: derived from ``agent/curator._load_config`` (curator.py:124).
    """
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
    except Exception as exc:  # noqa: BLE001 — config load must never crash
        logger.warning(
            "failed to load cli-config.yaml for feedback.decay_window_days; "
            "using default %d: %s",
            DEFAULT_DECAY_WINDOW_DAYS,
            exc,
        )
        return DEFAULT_DECAY_WINDOW_DAYS
    if not isinstance(cfg, dict):
        return DEFAULT_DECAY_WINDOW_DAYS
    fb = cfg.get("feedback") or {}
    if not isinstance(fb, dict):
        return DEFAULT_DECAY_WINDOW_DAYS
    try:
        return int(fb.get("decay_window_days", DEFAULT_DECAY_WINDOW_DAYS))
    except (TypeError, ValueError) as exc:
        logger.debug(
            "invalid feedback.decay_window_days value; using default %d: %s",
            DEFAULT_DECAY_WINDOW_DAYS,
            exc,
        )
        return DEFAULT_DECAY_WINDOW_DAYS


# ── FeedbackStore (STORE-01 / STORE-02) ──────────────────────────────────────


class FeedbackStore:
    """Single owner of feedback persistence under ``skills/.feedback/``.

    Every write goes through :meth:`record_feedback`. Every read goes
    through :meth:`query` / :meth:`summary` / :meth:`get_record`. The
    store maintains an in-memory ``_index: dict`` mirroring ``index.json``
    and a ``_sha256_index: dict[str, dict]`` cache loaded from the dedup
    registry (Plan 02 writes here; Plan 01 leaves the registry empty).

    Per CONTEXT.md storage layout decision: bucket layout is
    ``buckets/<skill_id>/<source>.jsonl`` (one file per source — verdict
    is a record attribute, not a file split, so ``query(verdict=...)``
    scans one file not three).
    """

    def __init__(
        self,
        *,
        hermes_home: Path | None = None,
        decay_window_days: int | None = None,
    ) -> None:
        """Initialize the store.

        Args:
            hermes_home: optional explicit ``HERMES_HOME`` path (tests use
                this to inject an isolated tmp_path). Defaults to
                :func:`hermes_constants.get_hermes_home`.
            decay_window_days: optional override for the decay window.
                Defaults to reading ``feedback.decay_window_days`` from
                config.yaml, falling back to 180.
        """
        self._root: Path = (hermes_home or get_hermes_home()) / "skills" / ".feedback"
        self._buckets_root: Path = self._root / "buckets"
        self._index_path: Path = self._root / "index.json"
        self._dedup_dir: Path = self._root / "dedup"
        self._dedup_registry_path: Path = self._dedup_dir / "sha256-registry.jsonl"
        self._archive_root: Path = self._root / "archive"
        self._incoming_dir: Path = self._root / "incoming"

        self._decay_window_days: int = (
            decay_window_days
            if decay_window_days is not None
            else _load_decay_window_days_from_config()
        )

        # Create directory layout lazily.
        self._buckets_root.mkdir(parents=True, exist_ok=True)
        self._dedup_dir.mkdir(parents=True, exist_ok=True)
        self._archive_root.mkdir(parents=True, exist_ok=True)

        # Migration state — gated by _migrated so re-init is a no-op.
        self._migrated: bool = False

        # In-memory dedup registry cache. Plan 01 leaves this empty
        # (no dedup branch yet); Plan 02 writes here on every record.
        self._sha256_index: dict[str, dict[str, Any]] = {}
        # Set of record_ids that have been superseded by a newer correction.
        # Populated from supersession events in dedup/sha256-registry.jsonl
        # (Plan 02). Used by query() filtering + weighted_count recomputation.
        self._superseded_record_ids: set[str] = set()
        self._load_sha256_index()

        # In-memory mirror of index.json — MUST be loaded BEFORE migration
        # so record_feedback calls during migration have self._index.
        self._index: dict[str, Any] = {}
        self._load_or_init_index()

        # Lazy migration from Phase 28 flat incoming/ layout. Runs AFTER
        # the index is loaded so record_feedback (which it calls) can
        # update the index safely.
        self._maybe_migrate_phase28_incoming()

    # ── record_id + paths ────────────────────────────────────────────────

    def _make_record_id(self, record: FeedbackRecord) -> str:
        """Generate a sortable, collision-resistant record_id.

        Format: ``f"{ts_unix_micro}_{sha256[:8]}"``.
        Microsecond precision + 8 hex chars from the output sha256 makes
        collision astronomically unlikely (RESEARCH A4).
        """
        ts_unix_micro = int(record.ts.timestamp() * 1_000_000)
        sha_prefix = record.output_snapshot.sha256[:8]
        return f"{ts_unix_micro}_{sha_prefix}"

    def bucket_path_for(self, record: FeedbackRecord) -> Path:
        """Return the bucket file path a record lands in.

        Public helper so Plan 02's ``write_feedback_record`` wrapper can
        return the path to Phase 28 callers that print it.
        """
        return self._buckets_root / record.skill_id / f"{record.source}.jsonl"

    # ── record_feedback (Plan 02: dedup / correction branch active) ─────

    def record_feedback(self, record: FeedbackRecord) -> str:
        """Persist a record + update the index atomically.

        Plan 02 inserts the :meth:`_handle_dedup` check between
        ``_make_record_id`` and the bucket append (STORE-04):

        - **New sha256** — proceeds with normal write.
        - **Same sha256 + same verdict (DUPLICATE)** — REJECTED. Returns
          the existing record_id; no bucket append, no registry append,
          no index change.
        - **Same sha256 + different verdict (CORRECTION)** — appends a
          supersession event to the registry marking the older record as
          superseded (weight=0 going forward), then proceeds with the
          normal write of the newer record.

        Args:
            record: a validated FeedbackRecord (Pydantic validation has
                already rejected malformed payloads before this method is
                called).

        Returns:
            The record_id (sortable + collision-resistant). For DUPLICATE
            writes, this is the EXISTING record_id, not a new one.
        """
        record_id = self._make_record_id(record)

        # ── 0. Dedup / correction check (STORE-04) ────────────────────
        # Must happen BEFORE any write. If the returned id differs from the
        # computed id, this is a DUPLICATE — return the existing id without
        # writing anything.
        dedup_result = self._handle_dedup(record, record_id)
        if dedup_result != record_id:
            # DUPLICATE — existing record_id returned. Skip all writes.
            return dedup_result

        bucket_key = f"{record.skill_id}:{record.source}:{record.verdict}"
        bucket_file = self.bucket_path_for(record)
        bucket_file.parent.mkdir(parents=True, exist_ok=True)

        # ── 1. Append record to bucket file (O(1) per write) ──────────
        # encoding="utf-8" MANDATORY (CLAUDE.md + Ruff PLW1514 + Pitfall #1).
        line = record.model_dump_json()
        with open(bucket_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

        # ── 2. Append record entry to dedup registry (audit log).
        # Supersession events are appended separately in _mark_superseded
        # when a correction happens (BEFORE this point in the flow).
        dedup_entry = {
            "sha256": record.output_snapshot.sha256,
            "verdict": record.verdict,
            "record_id": record_id,
            "ts": record.ts.isoformat(),
            "status": "active",
        }
        self._dedup_registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._dedup_registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(dedup_entry, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

        # ── 3. Update in-memory dedup cache + index ───────────────────
        self._sha256_index[record.output_snapshot.sha256] = dict(dedup_entry)

        # The bucket FILE holds all verdicts for (skill_id, source), but the
        # index bucket KEY includes verdict. So we filter records to the
        # matching verdict when computing count / weighted_count / ts range.
        # Superseded records are excluded from weighted_count (weight=0 by
        # STORE-04 contract); raw count still includes them (audit).
        all_records = self._read_bucket_records(bucket_file)
        verdict_records = [r for r in all_records if r.verdict == record.verdict]
        active_records = [
            r
            for r in verdict_records
            if self._make_record_id(r) not in self._superseded_record_ids
        ]
        weighted_count = self._recompute_bucket_weighted_count(active_records)

        ts_list = [r.ts for r in verdict_records]
        self._index["buckets"][bucket_key] = {
            "count": len(verdict_records),
            "weighted_count": weighted_count,
            "first_ts": min(ts_list).isoformat() if ts_list else record.ts.isoformat(),
            "last_ts": max(ts_list).isoformat() if ts_list else record.ts.isoformat(),
        }
        self._index["by_sha256"][record.output_snapshot.sha256] = dict(dedup_entry)
        self._index["updated_ts"] = datetime.now(timezone.utc).isoformat()
        self._index["decay_window_days"] = self._decay_window_days

        # ── 4. Atomic index.json rewrite (temp + fsync + os.replace) ──
        self._write_index()

        logger.debug(
            "recorded feedback: skill_id=%s source=%s verdict=%s record_id=%s",
            record.skill_id,
            record.source,
            record.verdict,
            record_id,
        )
        return record_id

    # ── Dedup / Correction (STORE-04) ───────────────────────────────────

    def _handle_dedup(
        self, record: FeedbackRecord, record_id: str
    ) -> str:
        """Consult the sha256 registry and decide whether to write.

        Args:
            record: the incoming FeedbackRecord.
            record_id: the computed record_id for the incoming record.

        Returns:
            - The SAME ``record_id`` if the write should proceed (new sha256
              or CORRECTION case).
            - The EXISTING ``record_id`` if the write is a DUPLICATE and
              must be skipped. The caller checks: if the returned id differs
              from the computed id, return early without writing.
        """
        sha = record.output_snapshot.sha256
        existing = self._sha256_index.get(sha)

        if existing is None:
            # New sha256 — no dedup action needed.
            return record_id

        if existing["verdict"] == record.verdict:
            # DUPLICATE: identical sha256 + identical verdict. Do NOT
            # double-count. Return the existing record_id; caller skips write.
            logger.info(
                "feedback duplicate detected: sha256=%s verdict=%s existing_record_id=%s",
                sha[:8],
                record.verdict,
                existing["record_id"],
            )
            return existing["record_id"]

        # CORRECTION: same sha256, different verdict. Mark the older record
        # superseded (weight=0 going forward) and proceed with the write of
        # the newer record. Order matters: _mark_superseded appends the
        # supersession event to the registry BEFORE the new record's entry
        # is appended in step 2 of record_feedback (T-29-11 mitigation).
        older_verdict = existing["verdict"]
        self._mark_superseded(
            sha=sha,
            older_record_id=existing["record_id"],
            older_verdict=older_verdict,
            newer_record_id=record_id,
            newer_verdict=record.verdict,
            newer_ts=record.ts,
        )
        logger.info(
            "feedback correction: sha256=%s older_verdict=%s -> newer_verdict=%s "
            "(older_record_id=%s weight zeroed)",
            sha[:8],
            older_verdict,
            record.verdict,
            existing["record_id"],
        )
        # After the older record is marked superseded, its bucket's
        # weighted_count is now stale (the superseded record no longer
        # contributes weight). Recompute the older verdict bucket so the
        # index reflects the correction immediately. The newer verdict's
        # bucket is recomputed in step 3 of record_feedback below.
        older_bucket_key = (
            f"{record.skill_id}:{record.source}:{older_verdict}"
        )
        self._recompute_single_bucket(older_bucket_key)
        return record_id

    def _recompute_single_bucket(self, bucket_key: str) -> None:
        """Recompute one bucket's count/weighted_count/ts range from disk.

        Helper for the correction path: when a record is marked superseded,
        its original bucket's weighted_count must be refreshed. Reads the
        bucket file for the (skill_id, source) pair, filters to the
        bucket_key's verdict, excludes superseded records from
        weighted_count, and updates ``self._index["buckets"][bucket_key]``.

        If the bucket has no active records left, ``weighted_count`` drops
        to 0.0 while ``count`` retains the raw line count (audit).

        No-op if the bucket file does not exist (nothing to recompute).
        """
        parts = bucket_key.split(":")
        if len(parts) != 3:
            return
        b_skill, b_source, b_verdict = parts
        bucket_file = self._buckets_root / b_skill / f"{b_source}.jsonl"
        if not bucket_file.is_file():
            return
        all_records = self._read_bucket_records(bucket_file)
        verdict_records = [r for r in all_records if r.verdict == b_verdict]
        active_records = [
            r
            for r in verdict_records
            if self._make_record_id(r) not in self._superseded_record_ids
        ]
        if verdict_records:
            ts_list = [r.ts for r in verdict_records]
            self._index["buckets"][bucket_key] = {
                "count": len(verdict_records),
                "weighted_count": self._recompute_bucket_weighted_count(
                    active_records
                ),
                "first_ts": min(ts_list).isoformat(),
                "last_ts": max(ts_list).isoformat(),
            }
        else:
            # No records of this verdict remain in the bucket file.
            self._index["buckets"].pop(bucket_key, None)

    def _mark_superseded(
        self,
        *,
        sha: str,
        older_record_id: str,
        older_verdict: str,
        newer_record_id: str,
        newer_verdict: str,
        newer_ts: datetime,
    ) -> None:
        """Mark an older record as superseded by a newer correction.

        Three mutations happen atomically (T-29-10 / T-29-11 mitigations):

        1. **Append supersession event** to ``dedup/sha256-registry.jsonl``
           (append-only audit log). Records older_record_id + older_verdict
           + newer_record_id + newer_verdict + ts. This is the audit trail
           and the source of truth for ``_superseded_record_ids`` on reload.
        2. **Update in-memory ``_sha256_index[sha]``** to point at the
           newer record (status=active, supersedes=older_record_id). The
           older record's status is implicitly superseded (the sha's active
           pointer no longer references it).
        3. **Add older_record_id to ``_superseded_record_ids``** so query()
           filtering and weighted_count recomputation skip it.

        NOTE: The older record's bytes are still in its bucket file (we do
        NOT rewrite bucket files — they are append-only). The status is
        reflected only in the index + registry. Bucket files remain the
        raw audit trail (T-29-12).

        Args:
            sha: the shared sha256.
            older_record_id: the record_id of the superseded record.
            older_verdict: the verdict of the superseded record.
            newer_record_id: the record_id of the newer (active) record.
            newer_verdict: the verdict of the newer (active) record.
            newer_ts: the timestamp of the newer record (used for the
                registry event ts and the active pointer ts).
        """
        ts_iso = newer_ts.isoformat()
        event = {
            "sha256": sha,
            "event": "superseded",
            "older_record_id": older_record_id,
            "older_verdict": older_verdict,
            "newer_record_id": newer_record_id,
            "newer_verdict": newer_verdict,
            "ts": ts_iso,
        }
        self._dedup_registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._dedup_registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

        # Update in-memory active pointer for this sha.
        self._sha256_index[sha] = {
            "record_id": newer_record_id,
            "verdict": newer_verdict,
            "ts": ts_iso,
            "status": "active",
            "supersedes": older_record_id,
        }

        # Track the older record_id as superseded for query() filtering +
        # weighted_count recomputation.
        self._superseded_record_ids.add(older_record_id)

    def _recompute_bucket_weighted_count(
        self, records: list[FeedbackRecord]
    ) -> float:
        """Inject ``self._decay_window_days`` into the module-level helper."""
        return recompute_bucket_weighted_count(
            records, decay_window_days=self._decay_window_days
        )

    # ── Bucket file I/O ─────────────────────────────────────────────────

    def _read_bucket_records(self, bucket_file: Path) -> list[FeedbackRecord]:
        """Read all records from a bucket jsonl file.

        Tolerates missing file (returns []). Skips blank lines. Logs and
        skips malformed lines (does not crash — operator can repair via
        Plan 02's ``rebuild-index`` command).
        """
        if not bucket_file.exists():
            return []
        records: list[FeedbackRecord] = []
        with open(bucket_file, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(FeedbackRecord.model_validate_json(stripped))
                except Exception as exc:  # noqa: BLE001 — skip bad line, keep going
                    logger.warning(
                        "malformed feedback record at %s:%d: %s",
                        bucket_file,
                        lineno,
                        exc,
                    )
        return records

    # ── Index load / write ──────────────────────────────────────────────

    def _write_index(self) -> None:
        """Atomically rewrite index.json (temp + fsync + os.replace)."""
        # DO NOT pass ensure_ascii= — atomic_json_write hardcodes it (Bug #1
        # in 28-01-SUMMARY).
        atomic_json_write(
            self._index_path,
            self._index,
            indent=2,
            sort_keys=True,
        )

    def _load_or_init_index(self) -> None:
        """Populate ``self._index`` from index.json, or write a default.

        Tolerates missing file (writes default). Tolerates corrupt JSON
        with warning + default (operator can ``rebuild-index`` in Plan 02).
        """
        default = {
            "version": _INDEX_VERSION,
            "decay_window_days": self._decay_window_days,
            "updated_ts": datetime.now(timezone.utc).isoformat(),
            "buckets": {},
            "by_sha256": {},
        }
        if not self._index_path.exists():
            self._index = default
            self._write_index()
            return
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "index.json corrupt; rewriting with default: %s", exc
            )
            self._index = default
            self._write_index()
            return
        if isinstance(data, dict) and data.get("version") == _INDEX_VERSION:
            self._index = data
        else:
            logger.warning(
                "index.json version mismatch or non-dict; rewriting with default"
            )
            self._index = default
            self._write_index()

    def _load_sha256_index(self) -> None:
        """Populate ``self._sha256_index`` + ``self._superseded_record_ids``.

        Reads ``dedup/sha256-registry.jsonl`` line-by-line in file order.
        Two line shapes are supported (append-only audit log):

        - **Record entry** (no ``event`` key or ``event == "active"``):
          ``{"sha256", "verdict", "record_id", "ts", "status"}``. Sets the
          current active pointer for the sha — a later active entry for the
          same sha replaces the earlier one.
        - **Supersession event** (``event == "superseded"``):
          ``{"sha256", "event", "older_record_id", "older_verdict",
             "newer_record_id", "newer_verdict", "ts"}``. Adds
          ``older_record_id`` to ``self._superseded_record_ids`` and updates
          ``self._sha256_index[sha]`` to point at the newer record.

        Tolerates missing file (empty dict + empty set). Skips blank lines.
        Logs and skips malformed lines.
        """
        if not self._dedup_registry_path.exists():
            return
        with open(self._dedup_registry_path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except (OSError, json.JSONDecodeError) as exc:
                    logger.warning(
                        "malformed dedup entry at %s:%d: %s",
                        self._dedup_registry_path,
                        lineno,
                        exc,
                    )
                    continue
                try:
                    event = entry.get("event")
                    if event == "superseded":
                        # Supersession event — mark older_record_id superseded
                        # and update active pointer to newer.
                        older_id = entry["older_record_id"]
                        sha = entry["sha256"]
                        self._superseded_record_ids.add(older_id)
                        self._sha256_index[sha] = {
                            "record_id": entry["newer_record_id"],
                            "verdict": entry["newer_verdict"],
                            "ts": entry["ts"],
                            "status": "active",
                            "supersedes": older_id,
                        }
                    else:
                        # Regular record entry — set active pointer.
                        sha = entry["sha256"]
                        self._sha256_index[sha] = {
                            "record_id": entry["record_id"],
                            "verdict": entry["verdict"],
                            "ts": entry["ts"],
                            "status": entry.get("status", "active"),
                        }
                except (KeyError, TypeError) as exc:
                    logger.warning(
                        "malformed dedup entry at %s:%d: %s",
                        self._dedup_registry_path,
                        lineno,
                        exc,
                    )

    # ── rebuild_index (operator repair tool) ────────────────────────────

    def rebuild_index(self) -> None:
        """Regenerate ``index.json`` from ``buckets/*.jsonl`` + dedup registry.

        Idempotent operator repair tool (STORE-02 / SC-2). Clears the
        in-memory index + sha256 cache + superseded record_id set, then
        rebuilds them from the two immutable on-disk sources of truth:

        1. ``dedup/sha256-registry.jsonl`` — append-only audit log. Replayed
           in file order to restore ``_sha256_index`` + superseded state
           (same logic as :meth:`_load_sha256_index`).
        2. ``buckets/<skill_id>/<source>.jsonl`` — append-only record files.
           Each record's effective status (active vs superseded) is derived
           from ``_superseded_record_ids`` after the registry replay. Active
           records contribute to ``weighted_count``; superseded records
           remain in raw ``count`` (audit) but contribute weight 0.

        After rebuilding in-memory state, atomically rewrites ``index.json``
        via :func:`utils.atomic_json_write`.

        Use cases:
          - ``index.json`` corrupted or lost (Pitfall #5).
          - Decay window retuned (refresh all weighted_counts in one shot).
          - Operator manually edited a bucket file (manual prune / merge).

        This method is exposed via the ``hermes feedback rebuild-index`` CLI.
        """
        # Reset in-memory state.
        self._index = {
            "version": _INDEX_VERSION,
            "decay_window_days": self._decay_window_days,
            "updated_ts": datetime.now(timezone.utc).isoformat(),
            "buckets": {},
            "by_sha256": {},
        }
        self._sha256_index = {}
        self._superseded_record_ids = set()

        # Replay the registry FIRST so supersession state is known before
        # we read bucket files (determines which records contribute weight).
        self._load_sha256_index()

        # Walk every bucket file. Path shape: buckets/<skill_id>/<source>.jsonl
        bucket_aggregates: dict[str, dict[str, Any]] = {}
        for bucket_file in sorted(self._buckets_root.glob("*/*.jsonl")):
            skill_id = bucket_file.parent.name
            source = bucket_file.stem
            records = self._read_bucket_records(bucket_file)
            for r in records:
                # Skip records that don't match the bucket's (skill_id, source)
                # pair (defensive — bucket file should only contain matching
                # records, but malformed writes are tolerated).
                if r.skill_id != skill_id or r.source != source:
                    continue
                bucket_key = f"{skill_id}:{source}:{r.verdict}"
                rid = self._make_record_id(r)
                is_superseded = rid in self._superseded_record_ids

                agg = bucket_aggregates.get(bucket_key)
                if agg is None:
                    agg = {
                        "count": 0,
                        "weighted_count": 0.0,
                        "first_ts": r.ts.isoformat(),
                        "last_ts": r.ts.isoformat(),
                        "_active_records": [],
                        "_ts_list": [],
                    }
                    bucket_aggregates[bucket_key] = agg
                agg["count"] += 1
                agg["_ts_list"].append(r.ts)
                if r.ts.isoformat() < agg["first_ts"]:
                    agg["first_ts"] = r.ts.isoformat()
                if r.ts.isoformat() > agg["last_ts"]:
                    agg["last_ts"] = r.ts.isoformat()
                if not is_superseded:
                    agg["_active_records"].append(r)

        # Compute weighted_count per bucket + finalize the index dict.
        for bucket_key, agg in bucket_aggregates.items():
            weighted = self._recompute_bucket_weighted_count(
                agg["_active_records"]
            )
            self._index["buckets"][bucket_key] = {
                "count": agg["count"],
                "weighted_count": weighted,
                "first_ts": agg["first_ts"],
                "last_ts": agg["last_ts"],
            }

        # Mirror sha256 state into the persisted index.
        self._index["by_sha256"] = {
            sha: dict(entry) for sha, entry in self._sha256_index.items()
        }
        self._index["updated_ts"] = datetime.now(timezone.utc).isoformat()
        self._index["decay_window_days"] = self._decay_window_days

        # Atomic index.json rewrite.
        self._write_index()

        logger.info(
            "feedback index rebuilt: %d buckets, %d superseded record_ids",
            len(self._index["buckets"]),
            len(self._superseded_record_ids),
        )

    # ── query / summary / get_record (STORE-02 Query API) ──────────────

    def query(
        self,
        *,
        skill_id: str | None = None,
        source: str | None = None,
        verdict: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        include_superseded: bool = False,
    ) -> list[FeedbackRecord]:
        """Return records matching all supplied filters.

        Filters compose by AND. Records are returned sorted by ``ts``
        ascending (stable for downstream consumers like the P32 review
        queue).

        The ``include_superseded`` flag controls whether records whose
        ``by_sha256`` entry has ``status="superseded"`` are returned.
        Plan 01 has no superseded records (no dedup branch yet) so this
        flag is a no-op today; Plan 02 activates it.

        Args:
            skill_id: optional skill filter.
            source: optional source filter.
            verdict: optional verdict filter.
            since: optional inclusive lower-bound on ``ts``.
            until: optional inclusive upper-bound on ``ts``.
            include_superseded: include superseded records (default False).

        Returns:
            List of :class:`FeedbackRecord` instances, ``ts``-ascending.
        """
        # Determine which bucket files to scan.
        if skill_id is not None and source is not None:
            candidates = [self._buckets_root / skill_id / f"{source}.jsonl"]
        elif skill_id is not None:
            skill_dir = self._buckets_root / skill_id
            candidates = (
                sorted(skill_dir.glob("*.jsonl")) if skill_dir.is_dir() else []
            )
        elif source is not None:
            candidates = sorted(self._buckets_root.glob(f"*/{source}.jsonl"))
        else:
            candidates = sorted(self._buckets_root.glob("*/*.jsonl"))

        results: list[FeedbackRecord] = []
        for path in candidates:
            for r in self._read_bucket_records(path):
                if skill_id is not None and r.skill_id != skill_id:
                    continue
                if source is not None and r.source != source:
                    continue
                if verdict is not None and r.verdict != verdict:
                    continue
                if since is not None and r.ts < since:
                    continue
                if until is not None and r.ts > until:
                    continue
                # Supersession filter (Plan 02). The bucket file holds both
                # active and superseded records (immutable); query excludes
                # superseded ones unless include_superseded=True. Record_id
                # membership in _superseded_record_ids is the authoritative
                # check (sha256 alone is ambiguous when corrections chain).
                if not include_superseded:
                    if self._make_record_id(r) in self._superseded_record_ids:
                        continue
                results.append(r)

        results.sort(key=lambda r: r.ts)
        return results

    def summary(
        self,
        *,
        skill_id: str | None = None,
        source: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Return per-bucket summary dicts from ``index.json``.

        Each value is ``{"count", "weighted_count", "first_ts", "last_ts"}``
        computed at the last :meth:`record_feedback` call. Decay-weighted
        values are "as of last write" not "as of now"; Plan 02's
        ``rebuild-index`` command refreshes them.

        Args:
            skill_id: optional skill filter (parsed from bucket key prefix).
            source: optional source filter (parsed from bucket key middle).

        Returns:
            Dict mapping bucket key (``"<skill_id>:<source>:<verdict>"``)
            to its summary dict.
        """
        out: dict[str, dict[str, Any]] = {}
        for key, bucket in self._index.get("buckets", {}).items():
            parts = key.split(":")
            if len(parts) != 3:
                continue
            b_skill, b_source, b_verdict = parts
            if skill_id is not None and b_skill != skill_id:
                continue
            if source is not None and b_source != source:
                continue
            out[key] = dict(bucket)
        return out

    def get_record(self, record_id: str) -> FeedbackRecord | None:
        """Return the record with the given record_id, or ``None``.

        Linear scan over all bucket files. At v6 scale (~thousands of
        records) this is acceptable (CONTEXT.md A4). For >100K records a
        future phase can add a dedicated record_id index.
        """
        for bucket_file in sorted(self._buckets_root.glob("*/*.jsonl")):
            for r in self._read_bucket_records(bucket_file):
                if self._make_record_id(r) == record_id:
                    return r
        return None

    # ── Phase 28 migration (lazy, idempotent) ───────────────────────────

    def _maybe_migrate_phase28_incoming(self) -> None:
        """Migrate Phase 28's flat ``incoming/`` layout to buckets/.

        Triggered once per process on :meth:`__init__`. Idempotent via
        the ``_migrated`` flag + ``.migration-in-progress`` sentinel
        file. The algorithm is naturally crash-safe (RESEARCH Pitfall #4):

          1. List ``incoming/*.json``. If empty, no-op.
          2. Touch the sentinel (crash-recovery marker).
          3. For each file: parse + validate as FeedbackRecord, call
             :meth:`record_feedback` (which routes to the correct
             ``buckets/<skill_id>/<source>.jsonl``), then move the
             original to ``archive/phase-28-migration/`` for audit.
          4. Remove the sentinel.

        ORDER MATTERS: append-first, then move. If append succeeds but
        the move fails, the next :meth:`__init__` re-appends (a harmless
        duplicate that Plan 02's dedup catches) and retries the move.

        Malformed files are logged at WARNING and left in ``incoming/``
        for retry (RESEARCH Pitfall #4 — never crash init).
        """
        if self._migrated:
            return
        self._migrated = True

        if not self._incoming_dir.is_dir():
            return
        pending = sorted(self._incoming_dir.glob("*.json"))
        if not pending:
            return

        archive_dir = self._archive_root / "phase-28-migration"
        archive_dir.mkdir(parents=True, exist_ok=True)
        sentinel = self._root / ".migration-in-progress"
        sentinel.touch(exist_ok=True)

        migrated = 0
        for src_path in pending:
            try:
                raw = json.loads(src_path.read_text(encoding="utf-8"))
                record = FeedbackRecord(**raw)
                # Append-first (RESEARCH Pitfall #4). record_feedback is
                # idempotent on partial retries only via Plan 02's dedup;
                # for Plan 01 a duplicate line is harmless (operator can
                # dedup-repair later).
                self.record_feedback(record)
                # Move original to archive for audit (do NOT delete).
                target = archive_dir / src_path.name
                src_path.rename(target)
                migrated += 1
            except Exception as exc:  # noqa: BLE001 — migration must not crash init
                logger.warning(
                    "phase-28 feedback migration skipped %s: %s "
                    "(left in incoming/ for retry)",
                    src_path.name,
                    exc,
                )

        try:
            sentinel.unlink(missing_ok=True)
        except OSError as exc:
            logger.debug("failed to remove migration sentinel: %s", exc)

        if migrated > 0:
            logger.info(
                "phase-28 feedback migration: moved %d records from incoming/ to buckets/",
                migrated,
            )
