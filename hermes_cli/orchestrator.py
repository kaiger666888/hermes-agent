"""Phase 68 OBSRV-04: ``hermes orchestrator status`` CLI.

Operator-facing observability for the v10.0 orchestrator. Surfaces the
3 dimensions shipped by Phase 67 (``agent.observability`` package):

* **Agent Registry** (OBSRV-01): loaded count, schema validation status,
  missing experts, lineage integrity, snapshot timestamp.
* **Round Table** (OBSRV-02): p50/p95 latency, total tokens, early-stop
  rate, status distribution.
* **Memory Backend** (OBSRV-03): p95 read/write latency, op counts,
  error rate, conflict count.

Two output modes:

* **Human (default):** 3 ``rich.table.Table`` objects printed to stdout.
* **Script (``--json``):** JSON document byte-identical in shape to the
  ``/orchestrator/agents/status`` FastAPI endpoint response (SC#3
  no-drift invariant). Consumable by ``jq`` and downstream automation.

Design notes
------------
* **Single source of truth.** Both this CLI and the dashboard endpoint
  call the same getters from ``agent.observability``. The shape is
  structurally identical — verified by
  ``test_no_drift_between_cli_and_endpoint``.
* **Lazy imports** for ``agent.observability`` inside the handler body
  (mirrors the endpoint pattern at ``web_server.py:2018`` — avoids any
  module-load cycle risk).
* **Graceful degradation.** Registry load failure (e.g. corrupt agent
  YAML) does NOT crash the CLI — the snapshot degrades to
  ``schema_validation_ok=False`` with empty ``agent_names``. Exit code
  stays 0 (this is observability data, not a CLI failure). Mirrors
  ``web_server.py:2029-2034``.
* **INFRA-04 compliance.** No new asyncio work — the handler is fully
  synchronous.
* **No new deps.** Uses ``rich==14.3.3`` (already in core) and stdlib
  ``json``.

Threat register
---------------
Mitigates:
* T-68-01-drift — ``_build_snapshot()`` is the single shared shape
  builder; the parity test asserts key-set equality with the endpoint.
* T-68-01-crash — try/except around ``load_agent_registry_with_warnings``.
* T-68-01-cycle — lazy import inside handler body.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["register_cli", "_cmd_status", "_build_snapshot"]


# ---------------------------------------------------------------------------
# CLI registration
# ---------------------------------------------------------------------------


def register_cli(parent: argparse.ArgumentParser) -> None:
    """Attach `orchestrator` subcommands to *parent*.

    main.py calls this with the ArgumentParser returned by
    ``subparsers.add_parser("orchestrator", ...)``.

    Currently exposes a single ``status`` subcommand. The namespace is
    reserved for future operator verbs (``inspect <agent>``,
    ``history``, etc.) per CONTEXT.md G1.
    """
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    subs = parent.add_subparsers(dest="orchestrator_command")

    p_status = subs.add_parser(
        "status",
        help="Show orchestrator observability snapshot (3 dimensions)",
        description=(
            "Operator visibility into the v10.0 orchestrator: agent "
            "registry health, round-table latency/token cost, and "
            "memory backend status. All metrics come from Phase 67 "
            "collectors (agent.observability)."
        ),
    )
    p_status.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit JSON (same shape as /orchestrator/agents/status endpoint) "
             "for script consumption. Pipe through `jq .` for pretty-printing.",
    )
    p_status.set_defaults(func=_cmd_status)


# ---------------------------------------------------------------------------
# Snapshot builder — shared shape (SC#3 no-drift)
# ---------------------------------------------------------------------------


def _build_snapshot() -> dict[str, Any]:
    """Build the orchestrator observability snapshot dict.

    This is the SINGLE source of truth for the snapshot shape. Both
    ``_cmd_status`` (CLI) and the parity test call this function. The
    endpoint at ``/orchestrator/agents/status`` builds the same shape
    inline (see ``web_server.py:2036-2041``) — the parity test asserts
    key-set equality.

    Lazy imports live INSIDE this function to avoid any module-load
    cycle between ``hermes_cli`` and ``agent.observability`` (threat
    T-68-01-cycle mitigation, mirrors endpoint pattern at
    ``web_server.py:2016-2024``).
    """
    from agent.observability import (
        get_agent_registry_metrics,
        get_round_table_metrics,
        get_memory_backend_metrics,
    )
    from agent.registry_loader import load_agent_registry_with_warnings
    from agent.round_table_state import _now_iso as _state_now_iso

    # OBSRV-01: live registry snapshot. The loader caches internally so
    # this is microseconds on cache hit. V7 error handling: never crash
    # the CLI on registry failure — degrade to schema_validation_ok=False.
    # (threat T-68-01-crash mitigation, mirrors endpoint at
    # web_server.py:2029-2034)
    try:
        entries, missing = load_agent_registry_with_warnings()
        schema_ok = True
    except Exception as exc:
        logger.warning("orchestrator status: registry load failed: %s", exc)
        entries, missing, schema_ok = [], [], False

    return {
        "agent_registry": get_agent_registry_metrics(entries, missing, schema_ok),
        "round_table": get_round_table_metrics(),
        "memory_backend": get_memory_backend_metrics(),
        "snapshot_at": _state_now_iso(),
    }


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


def _cmd_status(args: argparse.Namespace) -> int:
    """`hermes orchestrator status` handler.

    Args:
        args: argparse Namespace with ``as_json: bool`` attribute.

    Returns:
        0 on success (always — observability data, not a CLI error,
        even when the registry fails to load).
    """
    snapshot = _build_snapshot()

    as_json = bool(getattr(args, "as_json", False))
    if as_json:
        # JSON mode: byte-identical shape to /orchestrator/agents/status.
        # ensure_ascii=False so Chinese agent names / error strings survive.
        print(json.dumps(snapshot, ensure_ascii=False))
        return 0

    # Human mode: 3 rich tables.
    _render_tables(snapshot)
    return 0


# ---------------------------------------------------------------------------
# Rich table rendering
# ---------------------------------------------------------------------------


def _render_tables(snapshot: dict[str, Any]) -> None:
    """Print 3 rich tables (one per dimension) to stdout.

    Uses lazy imports for ``rich`` so the module is import-safe even in
    environments where the ``rich`` package is unavailable (defensive —
    rich is in core deps, but this mirrors the curator pattern).
    """
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # ── Dimension 1: Agent Registry ──────────────────────────────────
    ar = snapshot["agent_registry"]
    t1 = Table(title="Agent Registry (OBSRV-01)", show_lines=False)
    t1.add_column("Metric", style="bold")
    t1.add_column("Value", justify="left")
    t1.add_row("agents_loaded", str(ar["agents_loaded"]))
    t1.add_row(
        "schema_validation_ok",
        _bool_mark(ar["schema_validation_ok"]),
    )
    t1.add_row(
        "lineage_integrity_ok",
        _bool_mark(ar["lineage_integrity_ok"]),
    )
    t1.add_row("missing_experts", ", ".join(ar["missing_experts"]) or "(none)")
    t1.add_row("snapshot_at_iso", str(ar["snapshot_at_iso"]))
    console.print(t1)

    # ── Dimension 2: Round Table ─────────────────────────────────────
    rt = snapshot["round_table"]
    t2 = Table(title="Round Table (OBSRV-02)", show_lines=False)
    t2.add_column("Metric", style="bold")
    t2.add_column("Value", justify="right")
    t2.add_row("count", str(rt["count"]))
    t2.add_row("p50_latency_ms", _fmt_ms(rt["p50_latency_ms"]))
    t2.add_row("p95_latency_ms", _fmt_ms(rt["p95_latency_ms"]))
    t2.add_row("total_token_cost", str(rt["total_token_cost"]))
    t2.add_row("avg_token_cost", _fmt_float(rt["avg_token_cost"]))
    t2.add_row(
        "serial_lock_wait_p95_ms",
        _fmt_ms(rt["serial_lock_wait_p95_ms"]),
    )
    t2.add_row("early_stop_rate", _fmt_pct(rt["early_stop_rate"]))
    status_dist = rt.get("status_distribution") or {}
    t2.add_row(
        "status_distribution",
        ", ".join(f"{k}={v}" for k, v in sorted(status_dist.items())) or "(none)",
    )
    console.print(t2)

    # ── Dimension 3: Memory Backend ──────────────────────────────────
    mb = snapshot["memory_backend"]
    t3 = Table(title="Memory Backend (OBSRV-03)", show_lines=False)
    t3.add_column("Metric", style="bold")
    t3.add_column("Value", justify="right")
    t3.add_row("search_count", str(mb["search_count"]))
    t3.add_row("add_count", str(mb["add_count"]))
    t3.add_row("search_p95_ms", _fmt_ms(mb["search_p95_ms"]))
    t3.add_row("add_p95_ms", _fmt_ms(mb["add_p95_ms"]))
    t3.add_row("error_rate", _fmt_pct(mb["error_rate"]))
    t3.add_row("conflict_count", str(mb["conflict_count"]))
    t3.add_row("compaction_triggers", str(mb["compaction_triggers"]))
    t3.add_row("status", str(mb["status"]))
    console.print(t3)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _bool_mark(value: bool) -> str:
    """Render a boolean as a colored mark for human display.

    Uses rich markup so ``console.print`` colorizes it. JSON output is
    unaffected (raw bool in the snapshot dict).
    """
    return "[green]✓ yes[/green]" if value else "[red]✗ no[/red]"


def _fmt_ms(value: float) -> str:
    """Format a millisecond value with 2 decimal places."""
    return f"{float(value):.2f} ms"


def _fmt_float(value: float) -> str:
    """Format a generic float with 2 decimal places."""
    return f"{float(value):.2f}"


def _fmt_pct(value: float) -> str:
    """Format a 0..1 ratio as a percentage string."""
    return f"{float(value) * 100.0:.2f}%"
