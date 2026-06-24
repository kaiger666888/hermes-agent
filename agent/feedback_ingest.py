"""Feedback ingestion — atomic persistence entrypoint (INGEST-01/02/03 foundation).

This module owns the single write path for feedback records. Plan 02's
``/feedback`` slash-command handler, the kais-aigc file watcher, and
the JSONL batch importer all converge here.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514 enforced).
  - ``get_hermes_home()`` for path resolution — never the raw home call.
  - Specific exceptions bound with ``as exc``, lazy %-logging.

Per RESEARCH.md Pattern 3 (atomic write): every persistence call goes
through ``utils.atomic_json_write`` (temp + fsync + os.replace). This
guarantees no partial files if the process crashes mid-write.

Plan 02 extends this module with ``watch_inbox_kais()`` (file watcher)
and ``import_jsonl()`` (batch importer). Plan 01 ships ONLY the write
path + the contract the other paths will call.
"""

from __future__ import annotations

import logging
from pathlib import Path

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
