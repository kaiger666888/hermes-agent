"""Feedback ingestion — atomic persistence + watcher + JSONL batch importer.

This module owns the single write path for feedback records. The
``/feedback`` slash-command handler, the kais-aigc file watcher, and
the JSONL batch importer all converge on :func:`write_feedback_record`.

Plan 01 shipped the write path. Plan 02 adds:
  - :func:`import_jsonl` — atomic all-or-nothing batch import (INGEST-03/05)
  - :func:`watch_inbox_kais` — portable polling file watcher (INGEST-02)
  - :func:`_scan_once` — single-pass helper factored out of the watcher
    so tests can exercise it directly without sleeping through the loop.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every text ``open()`` / ``read_text`` /
    ``write_text`` call (Ruff PLW1514 enforced — Pitfall #1).
  - ``get_hermes_home()`` for path resolution — never the raw home call.
  - Specific exceptions bound with ``as exc``, lazy %-logging.

Per RESEARCH.md:
  - Pattern 3 (atomic write): every persistence call goes through
    ``utils.atomic_json_write`` (temp + fsync + os.replace).
  - Pattern 4 (portable polling watcher): stdlib ``os.scandir`` + 2-poll
    stability check (Pitfall #2 partial-write detection).
  - Pitfall #6 (watcher orphan): SIGINT/SIGTERM handlers + stop_event;
    PID printed on startup so the operator can kill the process.
  - Pitfall #7 (JSONL atomicity): parse + validate ALL lines BEFORE any
    write. If any line errors, return ``(0, errors)`` without writing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agent.feedback_schema import FeedbackRecord
from hermes_constants import get_hermes_home
from utils import atomic_json_write

logger = logging.getLogger(__name__)


def write_feedback_record(record: FeedbackRecord) -> Path:
    """Atomically persist a validated :class:`FeedbackRecord` to disk.

    Phase 29 delegation: this function is a thin wrapper around
    :class:`agent.feedback_store.FeedbackStore`. The signature is
    preserved exactly so every Phase 28 caller (CLI ``/feedback`` slash
    command, kais-aigc watcher, JSONL batch importer, ``hermes feedback
    submit``) continues to work unchanged.

    The returned :class:`Path` now points at the bucket file
    ``buckets/<skill_id>/<source>.jsonl`` (append-only, may contain
    multiple records after multiple writes) rather than the Phase 28
    per-record ``incoming/{skill_id}_{source}_{ts_compact}.json`` file.
    Phase 28 callers only use the path for display/logging (e.g.
    ``print(f"Feedback saved: {target}")``), never for re-reading the
    specific record, so this semantic change is safe. The record itself
    is retrievable via :meth:`FeedbackStore.get_record` using the
    record_id (returned by ``store.record_feedback`` internally).

    Delegation also activates STORE-04 dedup: a second write with the
    same ``output_snapshot.sha256`` and the same verdict is a no-op
    (returns the existing bucket path without appending). A second
    write with the same sha256 but a different verdict triggers the
    correction path (older record marked superseded, weight=0 going
    forward).

    Args:
        record: a validated FeedbackRecord (Pydantic validation has
            already rejected malformed payloads before this function
            is called).

    Returns:
        The :class:`Path` to the bucket file the record landed in
        (``buckets/<skill_id>/<source>.jsonl``).

    Raises:
        OSError: if the directory cannot be created or the write fails
            (propagated from the store). The caller is expected to handle
            this (the CLI prints a clear error; the watcher logs and
            moves the file to ``errors/``).

    Notes:
        - :class:`FeedbackStore` runs lazy migration from Phase 28's flat
          ``incoming/`` layout on first instantiation. If Phase 28 already
          wrote records to ``incoming/`` before this code path activates
          (e.g. a partial Phase 28 run before Phase 29 shipped), the
          migration picks them up. This is the intended zero-downtime
          cutover.
        - Resolves paths via :func:`hermes_constants.get_hermes_home` —
          respects the ``HERMES_HOME`` env var, never the raw home-dir call.
    """
    # Lazy import to avoid circular dependency: feedback_store imports
    # feedback_schema (not feedback_ingest), but the lazy pattern keeps
    # the modules decoupled for future refactors.
    from agent.feedback_store import FeedbackStore

    store = FeedbackStore()
    store.record_feedback(record)
    return store.bucket_path_for(record)


# ---------------------------------------------------------------------------
# JSONL batch importer (INGEST-03 / INGEST-05)
# ---------------------------------------------------------------------------


def import_jsonl(
    file_path: Path, *, dry_run: bool = False
) -> tuple[int, list[str]]:
    """Import feedback records from a JSONL file (atomic, all-or-nothing).

    Reads the file as UTF-8 (Pitfall #1 — explicit encoding), parses every
    non-blank, non-comment line as JSON, validates each as a
    :class:`FeedbackRecord`, and only writes ANY of them if every line
    validated. This is the CONTEXT.md D-INGEST-03 atomic batch contract.

    Args:
        file_path: path to a ``.jsonl`` file (one FeedbackRecord per line).
            Blank lines and lines starting with ``#`` are skipped.
        dry_run: when True, validate-only — no files written.

    Returns:
        ``(count, errors)`` where ``count`` is the number of records
        written (0 if any error) and ``errors`` is a list of
        ``"line N: <reason>"`` strings. When ``errors`` is non-empty,
        NOTHING was written (atomicity — Pitfall #7 / threat T-28-11).

    Notes:
        - Cold-start path (INGEST-05): an operator can seed a baseline
          store from a historical JSONL by running
          ``hermes feedback import history.jsonl``.
        - All writes flow through :func:`write_feedback_record`, so the
          directory chain under ``<HERMES_HOME>/skills/.feedback/incoming/``
          is created lazily on first write.
    """
    errors: list[str] = []
    records: list[FeedbackRecord] = []

    # Pitfall #1 — explicit encoding on every read_text.
    raw_text = file_path.read_text(encoding="utf-8")
    for i, line in enumerate(raw_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(f"line {i}: invalid JSON: {exc}")
            continue
        try:
            records.append(FeedbackRecord(**raw))
        except ValidationError as exc:
            errors.append(f"line {i}: validation failed: {exc}")
        except Exception as exc:  # noqa: BLE001 — defensive: surface any unexpected per-line failure
            errors.append(f"line {i}: unexpected error: {exc}")

    # Atomicity: if any error, return without writing anything.
    if errors:
        return (0, errors)
    if dry_run:
        return (len(records), [])

    for record in records:
        write_feedback_record(record)
    return (len(records), [])


# ---------------------------------------------------------------------------
# kais-aigc file-exchange polling watcher (INGEST-02)
# ---------------------------------------------------------------------------


def _resolve_kais_inbox() -> Path:
    """Resolve the kais-aigc inbox directory.

    Honors the ``HERMES_FEEDBACK_INBOX_KAIS`` env var (CONTEXT.md specifics)
    if set; otherwise defaults to
    ``<HERMES_HOME>/skills/.feedback/inbox-kais/``.
    """
    override = os.environ.get("HERMES_FEEDBACK_INBOX_KAIS")
    if override:
        return Path(override)
    return get_hermes_home() / "skills" / ".feedback" / "inbox-kais"


def _scan_once(
    inbox_dir: Path,
    processed_dir: Path,
    errors_dir: Path,
    seen: dict[str, tuple[float, int, str]],
    pending: dict[str, int],
) -> int:
    """Scan the inbox once and ingest any newly-stable files.

    Single-pass helper factored out of :func:`watch_inbox_kais` so tests
    can exercise it directly without sleeping through the polling loop.

    The 2-poll stability check (Pitfall #2) works as follows:
      - On first sighting, record the file size in ``pending`` and skip.
      - On the next scan, if the size is unchanged, ingest. Otherwise
        update ``pending`` to the new size and skip again.

    Anti-spoofing (threat T-28-07): regardless of what the JSON contents
    claim, the watcher FORCES ``source="kais_aigc"`` on the constructed
    :class:`FeedbackRecord`. This prevents a file claiming to be from
    ``cli`` from polluting the cli source.

    Path-traversal defense (threat T-28-06): the write target is ALWAYS
    derived from ``skill_id + source + ts`` inside
    :func:`write_feedback_record` — never from the inbox filename. When
    moving the source file to processed/, we use ``Path(entry.name).name``
    to strip any directory components.

    Args:
        inbox_dir: directory to scan for ``.json`` files.
        processed_dir: where successfully-ingested files are moved.
        errors_dir: where malformed / invalid files are moved (so the
            loop does not retry them forever).
        seen: mapping ``name -> (mtime, size, sha256)`` for files already
            processed or in stable-seen state. CR-03: the sha256 of file
            contents is included in the cache key so a sub-second rewrite
            with identical mtime+size but DIFFERENT content (e.g. a
            kais-aigc exporter emitting the same filename with a revised
            verdict of the same byte length) is still re-ingested.
            Backward-compat: legacy 2-tuple values are treated as a cache
            miss on the sha256 comparison (forcing a re-read + re-hash),
            which is the safe direction.
        pending: mapping ``name -> last observed size`` for files whose
            write is still in progress (waiting for stability).

    Returns:
        The number of files successfully ingested on this scan.
    """
    ingested = 0
    for entry in os.scandir(inbox_dir):
        # Symlink guard (RESEARCH review WR-03): reject symlinks before any
        # stat / read / rename call. ``DirEntry.is_dir()`` and ``.is_file()``
        # follow symlinks by default, so without this check a link pointing
        # outside the watcher tree would be ingested (and the rename would
        # move the link itself, orphaning the target). Also closes a
        # low-severity info-leak vector (adversary links a sensitive file
        # into inbox-kais/ named *.json).
        if entry.is_symlink():
            logger.warning(
                "kais inbox ignoring symlink %s (symlinks are not followed "
                "for safety)",
                entry.name,
            )
            continue
        if entry.is_dir():
            continue
        if not entry.name.endswith(".json"):
            continue
        try:
            stat = entry.stat()
        except OSError as exc:
            logger.warning(
                "kais inbox stat failed for %s: %s", entry.name, exc
            )
            continue
        key = entry.name
        # CR-03: first-tier fast check on (mtime, size). If these don't
        # match the cached values, the file definitely changed — proceed
        # to stability check. If they DO match, we still must verify the
        # content hash because a same-second rewrite with identical size
        # but different content (revised verdict of same byte length)
        # would otherwise be skipped. We defer the hash until after this
        # fast reject so the common case (genuinely unchanged file) only
        # pays a stat call, not a full read.
        cached = seen.get(key)
        if cached is not None and len(cached) == 3:
            cached_mtime, cached_size, _cached_sha = cached
            if cached_mtime == stat.st_mtime and cached_size == stat.st_size:
                # mtime + size match — verify content to defeat the
                # sub-second-same-size-rewrite attack (CR-03).
                try:
                    raw_bytes_for_hash = Path(entry.path).read_bytes()
                except OSError as exc:
                    logger.warning(
                        "kais inbox re-hash read failed for %s: %s",
                        entry.name,
                        exc,
                    )
                    # Treat as unstable — leave in pending, retry next scan.
                    pending[key] = stat.st_size
                    continue
                content_sha = hashlib.sha256(raw_bytes_for_hash).hexdigest()
                if content_sha == _cached_sha:
                    continue  # truly identical content — skip
                # Content differs but mtime+size matched — fall through to
                # re-ingestion. The stability check below uses pending[key]
                # which still holds the old size; force it to the current
                # size so the 2-poll gate doesn't block the re-ingest.
                logger.info(
                    "kais inbox %s: content changed with same mtime+size; "
                    "re-ingesting",
                    entry.name,
                )
            # else: mtime/size differ — proceed to normal stability check.
        # 2-poll stability check (Pitfall #2).
        if pending.get(key) != stat.st_size:
            pending[key] = stat.st_size
            continue
        # Size is stable across 2 polls — attempt ingest.
        # CR-03: content sha computed once on the successful read path;
        # on error paths we fall back to a stat-only signature (the file
        # is moving to errors/ anyway, so the seen cache just needs to
        # suppress re-scans of the now-gone file).
        content_sha_for_cache: str = f"stat-{stat.st_mtime_ns}-{stat.st_size}"
        try:
            raw_bytes = Path(entry.path).read_bytes()
            content_sha_for_cache = hashlib.sha256(raw_bytes).hexdigest()
            raw = json.loads(raw_bytes.decode("utf-8"))
            # Anti-spoofing: force source regardless of JSON content (T-28-07).
            raw["source"] = "kais_aigc"
            record = FeedbackRecord(**raw)
            write_feedback_record(record)
            ingested += 1
            # Move source file to processed/ — sanitized name strips dir components.
            safe_name = Path(entry.name).name
            target = processed_dir / safe_name
            try:
                Path(entry.path).rename(target)
            except OSError as exc:
                # rename can fail across filesystems or if target exists; fall
                # back to copy + delete so the loop still makes progress.
                logger.warning(
                    "kais inbox rename failed for %s: %s; falling back to copy+unlink",
                    entry.name,
                    exc,
                )
                target.write_bytes(raw_bytes)
                try:
                    Path(entry.path).unlink()
                except OSError as unlink_exc:
                    # WR-01: post-ingest unlink failed (file locked, permission
                    # revoked, NFS hiccup). The record WAS written to incoming/
                    # and the bytes ARE in processed/, but the source file is
                    # still in inbox/. Without intervention the next scan
                    # silently skips it (seen cache hit), confusing operators
                    # who expect "files in inbox/ are pending".
                    #
                    # Move the orphan to errors/ with a .unlink-failed suffix
                    # so it is visible to the operator and not re-ingested
                    # (the record already exists in incoming/). Best-effort:
                    # if even the rename fails, log loudly — the data is safe.
                    logger.warning(
                        "kais inbox post-ingest unlink failed for %s: %s "
                        "(record was written to incoming/ — relocating "
                        "source to errors/ for manual cleanup)",
                        entry.name,
                        unlink_exc,
                    )
                    orphan_target = errors_dir / (
                        Path(entry.name).name + ".unlink-failed"
                    )
                    try:
                        Path(entry.path).rename(orphan_target)
                    except OSError as rename_exc:
                        logger.warning(
                            "kais inbox could not relocate orphaned source "
                            "%s to errors/ (%s) — file remains in inbox/ "
                            "and will be skipped on subsequent scans "
                            "(seen cache); manual cleanup required",
                            entry.name,
                            rename_exc,
                        )
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning(
                "kais inbox ingest failed for %s: %s", entry.name, exc
            )
            _move_to_errors(entry.path, errors_dir)
        except UnicodeDecodeError as exc:
            # Encoding failure at raw_bytes.decode("utf-8") — surface the
            # actual encoding cause instead of letting it fall through to
            # the generic "unexpected failure" branch. Matters when the
            # kais-aigc exporter emits UTF-16 / GBK / Latin-1.
            logger.warning(
                "kais inbox ingest failed (encoding) for %s: %s "
                "(file is not valid UTF-8 — re-export as UTF-8)",
                entry.name,
                exc,
            )
            _move_to_errors(entry.path, errors_dir)
        except OSError as exc:
            logger.warning(
                "kais inbox ingest failed for %s: %s", entry.name, exc
            )
            _move_to_errors(entry.path, errors_dir)
        except Exception as exc:  # noqa: BLE001 — the watcher loop MUST NOT crash
            logger.warning(
                "kais inbox ingest unexpected failure for %s: %s",
                entry.name,
                exc,
            )
            _move_to_errors(entry.path, errors_dir)
        # Mark seen regardless of outcome — do not retry files that errored
        # (they are now in errors/, so the next scan won't see them anyway,
        # but if a rename failed we don't want to spin forever).
        # CR-03: cache (mtime, size, sha256) so a same-mtime+size rewrite
        # with different content is detected + re-ingested on the next scan.
        seen[key] = (stat.st_mtime, stat.st_size, content_sha_for_cache)
        pending.pop(key, None)
    return ingested


def _move_to_errors(src_path: str, errors_dir: Path) -> None:
    """Move a malformed file to the errors directory (sanitized name)."""
    src = Path(src_path)
    safe_name = Path(src.name).name
    target = errors_dir / safe_name
    try:
        src.rename(target)
    except OSError:
        # Best-effort: if rename fails (cross-fs, target exists), overwrite.
        try:
            target.write_bytes(src.read_bytes())
            src.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning(
                "kais inbox errors-move failed for %s: %s", src.name, exc
            )


def watch_inbox_kais(
    inbox_dir: Path | None = None,
    *,
    interval: float = 1.0,
    stop_event: threading.Event | None = None,
    max_iterations: int | None = None,
) -> None:
    """Polling file watcher for kais-aigc feedback files (INGEST-02).

    Polls ``inbox_dir`` at ``interval`` seconds using stdlib ``os.scandir``
    (portable across Linux/macOS/Windows/Termux — no ``watchdog`` dependency).
    For each new ``.json`` file, waits for size stability (2-poll check,
    Pitfall #2), then constructs a :class:`FeedbackRecord` with
    ``source="kais_aigc"`` OVERRIDE (anti-spoofing, T-28-07), writes it
    via :func:`write_feedback_record`, and moves the source file to
    ``processed-kais/``. Malformed or invalid files are moved to
    ``errors-kais/`` (T-28-08).

    Args:
        inbox_dir: inbox path. If None, resolves via :func:`_resolve_kais_inbox`
            (honors ``HERMES_FEEDBACK_INBOX_KAIS`` env var).
        interval: poll interval in seconds (default 1.0).
        stop_event: when set, the loop exits at the next check. If None,
            a fresh :class:`threading.Event` is created and SIGINT/SIGTERM
            are wired to set it (Pitfall #6 — watcher orphan prevention).
        max_iterations: if set, loop at most N times. Used by tests to
            avoid sleeping; production callers leave this as None.
    """
    if inbox_dir is None:
        inbox_dir = _resolve_kais_inbox()
    processed_dir = inbox_dir.parent / "processed-kais"
    errors_dir = inbox_dir.parent / "errors-kais"
    for d in (inbox_dir, processed_dir, errors_dir):
        d.mkdir(parents=True, exist_ok=True)

    if stop_event is None:
        stop_event = threading.Event()

        # Pitfall #6 — wire SIGINT/SIGTERM to the stop_event so Ctrl+C
        # kills the loop cleanly. Wrapped for Windows (SIGTERM missing).
        def _handler(signum: int, frame: Any) -> None:  # noqa: ARG001
            stop_event.set()

        for sig_name in ("SIGINT", "SIGTERM"):
            sig = getattr(signal, sig_name, None)
            if sig is not None:
                try:
                    signal.signal(sig, _handler)
                except (OSError, ValueError) as exc:
                    # Not in main thread (e.g. tests) — signal cannot be set.
                    logger.debug(
                        "could not install %s handler for feedback watcher: %s",
                        sig_name,
                        exc,
                    )

    # Print startup banner so the operator can locate + kill the process.
    print(
        f"[feedback-watch] PID {os.getpid()} polling {inbox_dir} "
        f"every {interval:.2f}s; processed -> {processed_dir}; "
        f"Ctrl+C to stop."
    )

    seen: dict[str, tuple[float, int, str]] = {}
    pending: dict[str, int] = {}
    iter_count = 0
    while max_iterations is None or iter_count < max_iterations:
        if stop_event.is_set():
            break
        try:
            _scan_once(inbox_dir, processed_dir, errors_dir, seen, pending)
        except Exception as exc:  # noqa: BLE001 — the watcher MUST survive
            logger.warning(
                "feedback watcher scan raised unexpectedly: %s", exc
            )
        iter_count += 1
        if max_iterations is not None and iter_count >= max_iterations:
            break
        # Sleep in small slices so stop_event responds quickly.
        slept = 0.0
        while slept < interval:
            if stop_event.is_set():
                return
            slice_sleep = min(0.1, interval - slept)
            time.sleep(slice_sleep)
            slept += slice_sleep
