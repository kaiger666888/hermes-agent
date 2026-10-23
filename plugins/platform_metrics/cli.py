"""cli.py — ``hermes formula`` CLI subcommand (Phase 42 DATA, Plan 42-04).

Registers the ``formula`` CLI namespace via the plugin CLI hook
(``ctx.register_cli_command``), auto-discovered at
``hermes_cli/main.py:11942``. Zero edits to ``hermes_cli/main.py``.

Subcommands:
  stats           Show rich tables of per-formula library contents + the
                  tuning suggestion queue depth (pending / applied /
                  rejected). The ``--json`` flag emits counts-only JSON
                  for scripting (no rich tables, no ANSI codes).

DATA-04 dashboard. The stats subcommand reads:

  - ``plugins/formula_library/lookup.py:load_library()`` for formula
    metadata (10 formulas by default).
  - ``plugins/platform_metrics/queue.py:read_queue()`` for tuning
    suggestion counts. Plan 42-03 ships ``queue.py`` in parallel with
    this plan — this module uses a DEFENSIVE LAZY IMPORT so it works
    whether or not ``queue.py`` has landed yet (the v9.0 stub scenario:
    no metrics collected, queue files absent → all counts surface as 0).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - Double-quoted strings throughout.
  - Lazy %-logging (no f-strings in logger calls).
  - Specific exceptions bound with ``as exc``.
  - ``encoding="utf-8"`` on every ``open()`` (none directly here —
    JSONL I/O is delegated to ``queue.py``).
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from hermes_constants import get_hermes_home
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


__all__ = ["register_formula_cli", "_formula_command"]


# ---------------------------------------------------------------------------
# Help text (top-level — printed when no subcommand given)
# ---------------------------------------------------------------------------


_HELP_TEXT = (
    "hermes formula — formula library + platform metrics observability\n"
    "\n"
    "Subcommands:\n"
    "  stats          Show per-formula library overview + tuning queue\n"
    "                 depth (pending / applied / rejected).\n"
    "\n"
    "Flags:\n"
    "  --json         Emit counts-only JSON (no rich tables, no ANSI).\n"
    "                 Suitable for shell scripting / piping into jq.\n"
    "\n"
    "Examples:\n"
    "  hermes formula stats\n"
    "  hermes formula stats --json\n"
    "\n"
    "V9-FUTURE: a ``hermes formula approve <suggestion_id>`` subcommand is\n"
    "reserved. v9.0 ships stats only — approve happens via the Python API\n"
    "(plugins.platform_metrics.library_writer.apply_suggestion, Plan 42-03).\n"
)


# ---------------------------------------------------------------------------
# Defensive queue reader — survives the Plan 42-03 parallel-race window
# ---------------------------------------------------------------------------


def _queue_counts(tuning_dir) -> dict[str, int]:
    """Read pending / applied / rejected counts from the JSONL queue.

    Returns a 3-key dict (``pending`` / ``applied`` / ``rejected``) with
    integer counts. Degrades gracefully:

      - If ``plugins.platform_metrics.queue`` is not importable (Plan
        42-03 has not landed yet, or the plugin is partially installed),
        returns ``{pending: 0, applied: 0, rejected: 0}``.
      - If the tuning dir or its JSONL files are missing, returns zeros.
      - Any I/O or validation error on a single file is logged at
        warning level + counted as 0 for that status.
    """
    zeros = {"pending": 0, "applied": 0, "rejected": 0}
    try:
        from plugins.platform_metrics.queue import read_queue  # type: ignore[import-not-found]
    except ImportError as exc:
        logger.debug(
            "plugins.platform_metrics.queue not importable yet (%s); "
            "returning zero counts",
            exc,
        )
        return zeros

    counts: dict[str, int] = dict(zeros)
    for status in ("pending", "applied", "rejected"):
        try:
            records = read_queue(tuning_dir=tuning_dir, status=status)
            counts[status] = len(records)
        except Exception as exc:  # noqa: BLE001 — best-effort counts
            logger.warning(
                "read_queue(status=%s) failed: %s — counting as 0",
                status,
                exc,
            )
            counts[status] = 0
    return counts


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------


def register_formula_cli(subparser: argparse.ArgumentParser) -> None:
    """Build the ``hermes formula`` argparse tree.

    Called once at plugin-load time by ``hermes_cli/main.py:11942`` via
    ``ctx.register_cli_command(name="formula", setup_fn=...)``. Mirrors
    the pattern in ``plugins/google_meet/cli.py:register_cli``.

    Args:
        subparser: the argparse subparser allocated for the ``formula``
            namespace. This function attaches the ``stats`` sub-subparser
            + its ``--json`` flag.
    """
    subs = subparser.add_subparsers(dest="formula_command")

    stats_p = subs.add_parser(
        "stats",
        help=(
            "Show per-formula / per-platform library overview + tuning "
            "suggestion queue depth"
        ),
    )
    stats_p.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit counts-only JSON (no rich tables, no ANSI). Suitable "
            "for shell scripting / piping into jq."
        ),
    )

    # Reserved for V9-FUTURE: per-formula + per-platform filter flags.
    # v9.0 ships stats-only; argparse tree does NOT reserve these slots
    # yet (keeping the help output clean). Add when approve subcommand
    # ships.


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def _formula_command(args: argparse.Namespace) -> int:
    """Dispatch the ``hermes formula <subcommand>`` invocation.

    Args:
        args: argparse Namespace. Must have ``formula_command`` (or
            None) and ``json`` (bool, default False).

    Returns:
        int exit code. 0 = success, 2 = unknown subcommand.
    """
    sub = getattr(args, "formula_command", None)
    if not sub:
        print(_HELP_TEXT)
        return 0
    if sub == "stats":
        return _cmd_stats(args)
    print(
        f"unknown subcommand: {sub!r} — available: stats "
        "(see `hermes formula` for help)"
    )
    return 2


# ---------------------------------------------------------------------------
# stats implementation
# ---------------------------------------------------------------------------


def _cmd_stats(args: argparse.Namespace) -> int:
    """Show formula library overview + tuning queue depth.

    In rich mode (default): prints two tables to stdout.

      Table 1 — "Formula Library Overview": per-formula row with
      formula_id / genre / mood / pacing / eval_score / # pending
      suggestions (best-effort count — currently 0 in v9.0 since
      tuning_loop has not produced suggestions yet).

      Table 2 — "Tuning Queue Summary": pending / applied / rejected
      counts + a Notes column documenting the approve workflow.

    In JSON mode (``--json``): prints a single JSON object to stdout
    with shape::

        {
          "formulas": [
            {"formula_id": "...", "genre": "...", "mood": "...",
             "pacing": "...", "eval_score": 0.0},
            ...
          ],
          "queue": {"pending": N, "applied": N, "rejected": N}
        }

    No ANSI escape codes in JSON mode (rich is bypassed).
    """
    hermes_home_str = get_hermes_home()
    from pathlib import Path

    hermes_home = Path(hermes_home_str)
    tuning_dir = hermes_home / "skills" / ".feedback" / "tuning"

    # Read formula library (always present — Phase 39 shipped it).
    try:
        from plugins.formula_library.lookup import load_library
        library = load_library()
        formulas = list(library.formulas)
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        logger.warning("load_library() failed: %s — showing empty list", exc)
        formulas = []

    # Read queue counts (defensive against missing queue.py).
    counts = _queue_counts(tuning_dir)

    if getattr(args, "json", False):
        return _emit_json(formulas, counts)

    return _emit_rich(formulas, counts)


def _emit_json(formulas: list, counts: dict[str, int]) -> int:
    """Emit counts-only JSON. No ANSI, no rich formatting."""
    payload: dict[str, Any] = {
        "formulas": [
            {
                "formula_id": getattr(f, "formula_id", ""),
                "genre": str(getattr(f, "genre", "")),
                "mood": str(getattr(f, "mood", "")),
                "pacing": getattr(f, "pacing", ""),
                "eval_score": getattr(f, "eval_score", None),
            }
            for f in formulas
        ],
        "queue": {
            "pending": int(counts.get("pending", 0)),
            "applied": int(counts.get("applied", 0)),
            "rejected": int(counts.get("rejected", 0)),
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _emit_rich(formulas: list, counts: dict[str, int]) -> int:
    """Emit two rich tables to stdout."""
    console = Console()

    # Table 1 — Formula Library Overview
    t1 = Table(
        title="Formula Library Overview",
        show_lines=False,
        title_style="bold cyan",
    )
    t1.add_column("Formula ID", style="cyan", no_wrap=True)
    t1.add_column("Genre", style="magenta")
    t1.add_column("Mood", style="yellow")
    t1.add_column("Pacing")
    t1.add_column("Eval", justify="right")
    t1.add_column("# Pending", justify="right")

    # Pre-compute pending-suggestion counts per formula_id (v9.0: all 0
    # since tuning_loop is V9-FUTURE-01 deferred; the column exists for
    # forward-compat so operators see where suggestions will land).
    for f in formulas:
        eval_score = getattr(f, "eval_score", None)
        eval_str = f"{eval_score:.2f}" if eval_score is not None else "—"
        t1.add_row(
            str(getattr(f, "formula_id", "")),
            str(getattr(f, "genre", "")),
            str(getattr(f, "mood", "")),
            str(getattr(f, "pacing", "")),
            eval_str,
            "0",  # v9.0: tuning_loop not yet producing suggestions
        )

    console.print(t1)
    console.print()

    # Table 2 — Tuning Queue Summary
    t2 = Table(
        title="Tuning Queue Summary",
        show_lines=False,
        title_style="bold cyan",
    )
    t2.add_column("Status", style="cyan")
    t2.add_column("Count", justify="right")
    t2.add_column("Notes")

    t2.add_row(
        "pending",
        str(counts.get("pending", 0)),
        "awaiting operator review",
    )
    t2.add_row(
        "applied",
        str(counts.get("applied", 0)),
        (
            "eval_score written back to formula_library "
            "(via library_writer.apply_suggestion)"
        ),
    )
    t2.add_row(
        "rejected",
        str(counts.get("rejected", 0)),
        "operator declined with reason",
    )

    console.print(t2)
    console.print()
    console.print(
        "[dim]Approve pending suggestions via the Python API:[/dim]\n"
        "[dim]  from plugins.platform_metrics.library_writer "
        "import apply_suggestion[/dim]\n"
        "[dim]V9-FUTURE: `hermes formula approve <suggestion_id>` "
        "CLI subcommand.[/dim]"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="hermes formula")
    register_formula_cli(parser)
    ns = parser.parse_args()
    import sys as _sys
    _sys.exit(_formula_command(ns))
