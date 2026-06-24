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

    Writes under ``<HERMES_HOME>/skills/.feedback/incoming/`` using the
    filename pattern ``{skill_id}_{source}_{ts_compact}.json`` where
    ``ts_compact = record.ts.strftime("%Y%m%dT%H%M%S%fZ")``. Microsecond
    precision + source disambiguation makes the filename sortable and
    collision-resistant.

    Args:
        record: a validated FeedbackRecord (Pydantic validation has
            already rejected malformed payloads before this function
            is called).

    Returns:
        The :class:`Path` to the written file.

    Raises:
        OSError: if the directory cannot be created or the write fails
            (propagated from ``atomic_json_write`` / ``mkdir``). The
            caller is expected to handle this (the CLI prints a clear
            error; the watcher logs and moves the file to ``errors/``).

    Notes:
        - Uses :func:`utils.atomic_json_write` (temp + fsync +
          ``os.replace``) so the target file is never left partially
          written. If the process crashes mid-write, no file appears.
        - Resolves paths via :func:`hermes_constants.get_hermes_home` —
          respects the ``HERMES_HOME`` env var, never the raw home-dir call.
        - The directory chain is created lazily on first write.
    """
    target_dir = get_hermes_home() / "skills" / ".feedback" / "incoming"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Filename: {skill_id}_{source}_{ts_compact}.json
    # ts_compact is sortable ASCII (Y...m...d...T...H...M...S...micro...Z).
    ts_compact = record.ts.strftime("%Y%m%dT%H%M%S%fZ")
    target = target_dir / f"{record.skill_id}_{record.source}_{ts_compact}.json"

    atomic_json_write(
        target,
        record.model_dump(mode="json"),
        indent=2,
    )
    logger.debug(
        "wrote feedback record: skill_id=%s source=%s verdict=%s -> %s",
        record.skill_id,
        record.source,
        record.verdict,
        target,
    )
    return target


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
    seen: dict[str, tuple[float, int]],
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
        seen: mapping ``name -> (mtime, size)`` for files already
            processed or in stable-seen state (skip on subsequent scans).
        pending: mapping ``name -> last observed size`` for files whose
            write is still in progress (waiting for stability).

    Returns:
        The number of files successfully ingested on this scan.
    """
    ingested = 0
    for entry in os.scandir(inbox_dir):
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
        current = (stat.st_mtime, stat.st_size)
        if seen.get(key) == current:
            continue  # already processed and unchanged
        # 2-poll stability check (Pitfall #2).
        if pending.get(key) != stat.st_size:
            pending[key] = stat.st_size
            continue
        # Size is stable across 2 polls — attempt ingest.
        try:
            raw_bytes = Path(entry.path).read_bytes()
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
                    logger.warning(
                        "kais inbox unlink-after-copy failed for %s: %s",
                        entry.name,
                        unlink_exc,
                    )
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning(
                "kais inbox ingest failed for %s: %s", entry.name, exc
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
        seen[key] = current
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

    seen: dict[str, tuple[float, int]] = {}
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
