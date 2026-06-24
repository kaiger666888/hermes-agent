"""CLI subcommand: ``hermes feedback <import|watch|submit>``.

Thin shell around :mod:`agent.feedback_ingest`. Built via the
:func:`register_cli` pattern that mirrors :mod:`hermes_cli.curator` —
``main.py`` calls this with the ``ArgumentParser`` returned by
``subparsers.add_parser("feedback", ...)``.

This module has no side effects at import time; main.py wires the
argparse subparsers on demand.

Subcommands:
  - ``import``: atomic batch import of feedback records from a JSONL file
    (INGEST-03/05). All-or-nothing: parses + validates ALL lines before
    writing ANY. Lists every validation error with line numbers on failure.
  - ``watch``: foreground polling watcher for the kais-aigc file-exchange
    inbox (INGEST-02). Polls ``~/.hermes/skills/.feedback/inbox-kais/``
    at a configurable interval. Ctrl+C exits cleanly.
  - ``submit``: scripting-friendly single-record ingest (INGEST-05).
    Constructs a :class:`FeedbackRecord` with ``source="manual"`` from
    explicit args (no live conversation state required).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - Double-quoted strings.
  - Specific exceptions bound with ``as exc``.
  - No bare ``except:``.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


def register_cli(parent: argparse.ArgumentParser) -> None:
    """Attach ``feedback`` subcommands to *parent*.

    main.py calls this with the ArgumentParser returned by
    ``subparsers.add_parser("feedback", ...)``. Mirrors the
    :func:`hermes_cli.curator.register_cli` pattern line-for-line in style.
    """
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    subs = parent.add_subparsers(dest="feedback_command")

    # ── import ────────────────────────────────────────────────────────
    p_import = subs.add_parser(
        "import",
        help="Batch-import feedback records from a JSONL file (atomic)",
    )
    p_import.add_argument(
        "file",
        help="Path to .jsonl file (one FeedbackRecord per line; blank lines "
        "and lines starting with # are skipped)",
    )
    p_import.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate every record without writing anything",
    )
    p_import.set_defaults(func=_cmd_import)

    # ── watch ────────────────────────────────────────────────────────
    p_watch = subs.add_parser(
        "watch",
        help="Watch inbox-kais/ for new kais-aigc feedback files "
        "(foreground; Ctrl+C to stop)",
    )
    p_watch.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Poll interval in seconds (default: 1.0)",
    )
    p_watch.set_defaults(func=_cmd_watch)

    # ── submit ───────────────────────────────────────────────────────
    p_submit = subs.add_parser(
        "submit",
        help="Submit a single feedback record (scripting-friendly)",
    )
    p_submit.add_argument("skill_id", help="Target skill (e.g. 'screenplay')")
    p_submit.add_argument(
        "verdict",
        choices=["good", "needs_work", "bad"],
        help="Operator verdict on the output",
    )
    p_submit.add_argument(
        "--correction", default="", help="Free-text correction / explanation"
    )
    p_submit.add_argument(
        "--revised",
        default=None,
        help="Optional full revised output text",
    )
    p_submit.add_argument(
        "--output-text",
        required=True,
        help="The original output text being reviewed (required — the submit "
        "path has no live conversation state to capture from)",
    )
    p_submit.add_argument(
        "--prompt-text", default="", help="Optional prompt that produced the output"
    )
    p_submit.add_argument(
        "--model", default="", help="Model name (default: empty)"
    )
    p_submit.add_argument(
        "--provider", default="", help="Provider name (default: empty)"
    )
    p_submit.set_defaults(func=_cmd_submit)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _cmd_import(args) -> int:
    """``hermes feedback import <file.jsonl> [--dry-run]``."""
    from agent.feedback_ingest import import_jsonl

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        return 2

    try:
        count, errors = import_jsonl(file_path, dry_run=getattr(args, "dry_run", False))
    except Exception as exc:  # noqa: BLE001 — surface any unexpected failure to the operator
        print(f"Error: import failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        # Print every error so the operator can fix the file.
        print(f"Import rejected ({len(errors)} error(s)):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    if getattr(args, "dry_run", False):
        print(f"Validated {count} records (dry-run; nothing written).")
    else:
        print(f"Imported {count} record(s).")
    return 0


def _cmd_watch(args) -> int:
    """``hermes feedback watch [--interval N]``."""
    from agent.feedback_ingest import watch_inbox_kais

    stop_event = threading.Event()
    # The watcher installs its own SIGINT/SIGTERM handlers when given a
    # fresh stop_event. We pass ours so test mocks can set it.
    try:
        watch_inbox_kais(
            interval=args.interval,
            stop_event=stop_event,
        )
    except KeyboardInterrupt:
        stop_event.set()
    return 0


def _cmd_submit(args) -> int:
    """``hermes feedback submit <skill_id> <verdict> [--correction ...] ...``.

    Constructs a :class:`FeedbackRecord` with ``source="manual"`` and writes
    it via :func:`agent.feedback_ingest.write_feedback_record`. The
    scripting path does not have a live conversation, so the caller MUST
    supply ``--output-text`` (the original output being reviewed).
    """
    from agent.feedback_schema import FeedbackRecord, OutputSnapshot
    from agent.feedback_ingest import write_feedback_record
    from pydantic import ValidationError

    output_text = args.output_text
    sha = hashlib.sha256(
        output_text.encode("utf-8", errors="surrogatepass")
    ).hexdigest()
    snapshot = OutputSnapshot(
        sha256=sha,
        output_text=output_text,
        prompt=args.prompt_text,
        model=args.model,
        provider=args.provider,
        api_mode="",
        params={},
        captured_at=datetime.now(timezone.utc),
    )
    try:
        record = FeedbackRecord(
            skill_id=args.skill_id,
            expert_id=args.skill_id,
            source="manual",
            verdict=args.verdict,
            correction=args.correction,
            revised_output=args.revised,
            output_snapshot=snapshot,
            ts=datetime.now(timezone.utc),
        )
    except ValidationError as exc:
        print(f"Validation failed:", file=sys.stderr)
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()))
            print(f"  {loc}: {err.get('msg', '?')}", file=sys.stderr)
        return 1

    try:
        target = write_feedback_record(record)
    except Exception as exc:  # noqa: BLE001 — surface write failures to the operator
        print(f"Error writing record: {exc}", file=sys.stderr)
        return 1

    print(f"Feedback saved: {target}")
    return 0


def cli_main(argv=None) -> int:
    """Standalone entry (also usable by hermes_cli.main fallthrough)."""
    parser = argparse.ArgumentParser(prog="hermes feedback")
    register_cli(parser)
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)
