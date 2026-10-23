"""dreamina_stats.py — MetricsBuffer JSONL ring buffer + SLA CLI (IMG-05).

Exact twin of plugins/platform_metrics/ pattern:
  - schema.py -> DreaminaTaskMetrics (Pydantic v2 BaseModel)
  - queue.py  -> record_metric + read_metrics (sync JSONL ring buffer)
  - cli.py    -> register_dreamina_cli + _dreamina_command + _emit_rich

INFRA-04 preservation (PITFALL I-5):
  This module is SYNC ONLY. No async runtime. Zero GLM calls per metric.
  The v13.0 P67 sync @contextmanager precedent is the model.

Storage: ~/.hermes/metrics/dreamina_stats.jsonl (HERMES_HOME convention).
Ring buffer: last 1000 entries (~1 week of operator data per CONTEXT.md).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home
from pydantic import BaseModel, ConfigDict, Field, field_validator
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

__all__ = [
    "register_dreamina_cli",
    "_dreamina_command",
    "record_metric",
    "read_metrics",
    "DreaminaTaskMetrics",
    "register_glm_cli",
    "_glm_command",
]

# ── Constants ──────────────────────────────────────────────────────────────

_BUFFER_SIZE = 1000  # ~1 week of operator data per CONTEXT.md specifics


def _metrics_file() -> Path:
    """Return the canonical MetricsBuffer JSONL path.

    Uses hermes_constants.get_hermes_home() (NOT Path.home() — CLAUDE.md
    anti-pattern). Lives at ~/.hermes/metrics/dreamina_stats.jsonl.
    """
    return Path(get_hermes_home()) / "metrics" / "dreamina_stats.jsonl"


# ── Pydantic schema (mirror platform_metrics/schema.py) ───────────────────


class DreaminaTaskMetrics(BaseModel):
    """Per-task dreamina generation metric record (IMG-05 schema).

    One record per dreamina batch_submit task. Written synchronously
    to the JSONL ring buffer via record_metric(). Read by
    ``hermes dreamina stats`` CLI for dashboard rendering.
    """

    model_config = ConfigDict(extra="forbid")

    submit_id: str = Field(description="Dreamina submit UUID")
    stratum: str = Field(description="1-ref | 3-ref | 5-ref | text2image")
    latency_ms: int = Field(ge=0, description="Total task latency in ms")
    success: bool = Field(description="True if task succeeded")
    retries: int = Field(ge=0, description="Number of retries before success/failure")
    vision_verified: bool = Field(description="True if vision-verify ran")
    vision_confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Vision judge confidence (0-1); see vision_verify engines"
    )
    # Phase 82 XCUT-04c-INSTRUMENT: vision-judge token spend tracking
    # (recorded through the glm-4.6v era; engine now via vision_verify).
    # Default to 0 so existing v14.0 entries (which lack these fields)
    # load cleanly when deserialized via read_metrics.
    input_tokens: int = Field(default=0, ge=0, description="Vision judge input tokens consumed")
    output_tokens: int = Field(default=0, ge=0, description="Vision judge output tokens consumed")
    estimated_cost_usd: float = Field(
        default=0.0, ge=0.0, description="Estimated USD cost for the vision judge call"
    )
    ts: str = Field(description="ISO 8601 UTC timestamp")

    @field_validator("stratum")
    @classmethod
    def _stratum_values(cls, v: str) -> str:
        valid = {"1-ref", "3-ref", "5-ref", "text2image"}
        if v not in valid:
            raise ValueError(
                f"invalid stratum: {v!r} — must be one of {sorted(valid)}"
            )
        return v


# ── JSONL ring buffer (mirror platform_metrics/queue.py:64-119) ───────────


def record_metric(path: Path, metric: dict[str, Any]) -> None:
    """Append one metric record to JSONL. Sync (INFRA-04 compliant).

    No async runtime. No GLM calls. Writes a single JSON line to *path*.

    WR-03: validates *metric* against the DreaminaTaskMetrics schema
    before write. Invalid metrics (unknown field, bad stratum, out-of-
    range confidence) raise Pydantic ValidationError — callers should
    wrap in try/except if they want best-effort skip.

    Args:
        path: JSONL file path (typically _metrics_file()).
        metric: dict matching DreaminaTaskMetrics schema.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    validated = DreaminaTaskMetrics(**metric)
    line = validated.model_dump_json()
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_metrics(path: Path, limit: int = _BUFFER_SIZE) -> list[dict[str, Any]]:
    """Read last N metrics from JSONL (ring buffer semantic).

    Mirrors platform_metrics/queue.py:75-119 _read_jsonl pattern.
    Malformed lines are logged and skipped (NOT crashed).

    Args:
        path: JSONL file path.
        limit: return at most this many entries (default 1000).

    Returns:
        list of metric dicts, last *limit* entries.
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
                logger.warning(
                    "malformed JSON at %s:%d (%s) — skipping line",
                    path, lineno, exc,
                )
                continue
            if isinstance(parsed, dict):
                out.append(parsed)
            else:
                logger.warning(
                    "non-object JSON at %s:%d — skipping line", path, lineno
                )
    return out[-limit:]


# ── CLI (mirror platform_metrics/cli.py) ──────────────────────────────────


_HELP_TEXT = (
    "hermes dreamina — dreamina batch generation SLA dashboard\n"
    "\n"
    "Subcommands:\n"
    "  stats          Show per-stratum latency / success rate / count.\n"
    "\n"
    "Flags:\n"
    "  --json         Emit counts-only JSON (no rich tables, no ANSI).\n"
    "                 Suitable for shell scripting / piping into jq.\n"
)


def register_dreamina_cli(subparser: argparse.ArgumentParser) -> None:
    """Build the ``hermes dreamina`` argparse tree.

    Called once at plugin-load time by hermes_cli/main.py via
    ctx.register_cli_command(name="dreamina", ...). Mirrors
    plugins/platform_metrics/cli.py:register_formula_cli.
    """
    subs = subparser.add_subparsers(dest="dreamina_command")

    stats_p = subs.add_parser(
        "stats",
        help=(
            "Show dreamina batch generation SLA dashboard "
            "(latency / success rate / cost per stratum)"
        ),
    )
    stats_p.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit counts-only JSON (no rich tables, no ANSI). "
            "Suitable for shell scripting / piping into jq."
        ),
    )


def _dreamina_command(args: argparse.Namespace) -> int:
    """Dispatch ``hermes dreamina`` subcommands."""
    sub = getattr(args, "dreamina_command", None)
    if not sub:
        print(_HELP_TEXT)
        return 0
    if sub == "stats":
        return _cmd_stats(args)
    print(f"unknown subcommand: {sub!r} — available: stats")
    return 2


def _cmd_stats(args: argparse.Namespace) -> int:
    """Handle ``hermes dreamina stats`` — read JSONL, render table or JSON."""
    metrics_file = _metrics_file()
    metrics = read_metrics(metrics_file)

    if getattr(args, "json", False):
        return _emit_json(metrics)
    return _emit_rich(metrics)


def _emit_json(metrics: list[dict[str, Any]]) -> int:
    """Emit machine-readable JSON."""
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


def _emit_rich(metrics: list[dict[str, Any]]) -> int:
    """Render rich-formatted table (mirror platform_metrics/cli.py:267-340)."""
    console = Console()
    t = Table(title="Dreamina SLA Dashboard", title_style="bold cyan")
    t.add_column("Stratum", style="cyan")
    t.add_column("Count", justify="right")
    t.add_column("p50 (ms)", justify="right")
    t.add_column("p95 (ms)", justify="right")
    t.add_column("Success %", justify="right")

    if not metrics:
        t.add_row("(no data)", "0", "-", "-", "-")
        console.print(t)
        console.print(
            f"\n[dim]Metrics file: {_metrics_file()}[/dim]\n"
            "[dim]Run dreamina batch_submit to populate.[/dim]"
        )
        return 0

    # Aggregate by stratum.
    by_stratum: dict[str, list[dict[str, Any]]] = {}
    for m in metrics:
        stratum = m.get("stratum", "unknown")
        by_stratum.setdefault(stratum, []).append(m)

    for stratum in sorted(by_stratum.keys()):
        entries = by_stratum[stratum]
        count = len(entries)
        latencies = sorted(e.get("latency_ms", 0) for e in entries)
        p50 = latencies[len(latencies) // 2] if latencies else 0
        p95_idx = int(len(latencies) * 0.95)
        p95 = latencies[min(p95_idx, len(latencies) - 1)] if latencies else 0
        success_count = sum(1 for e in entries if e.get("success"))
        success_pct = (success_count / count * 100) if count else 0
        t.add_row(
            stratum,
            str(count),
            str(p50),
            str(p95),
            f"{success_pct:.0f}%",
        )

    console.print(t)
    console.print(f"\n[dim]Metrics file: {_metrics_file()}[/dim]")
    return 0


# ── GLM cost CLI (Phase 82 XCUT-04c-CLI) ──────────────────────────────────
# Mirrors the dreamina CLI pattern above. Reads the same MetricsBuffer JSONL
# (single source of truth) but aggregates by month + stratum for the vision judge
# (see vision_verify engines — glm-4.6v rows are historical)
# token spend tracking.


_GLM_HELP_TEXT = (
    "hermes glm — vision-verify cost dashboard\n"
    "\n"
    "Subcommands:\n"
    "  stats          Show monthly + per-stratum vision-judge token spend + cost.\n"
    "\n"
    "Flags:\n"
    "  --json         Emit JSON (no rich tables).\n"
    "  --month YYYY-MM  Filter to a single month.\n"
)


def register_glm_cli(subparser: argparse.ArgumentParser) -> None:
    """Build the ``hermes glm`` argparse tree.

    Mirrors register_dreamina_cli pattern. Adds a "stats" subcommand
    with --json and --month flags.
    """
    subs = subparser.add_subparsers(dest="glm_command")

    stats_p = subs.add_parser(
        "stats",
        help=(
            "Show monthly + per-stratum vision-judge token spend + "
            "estimated cost dashboard"
        ),
    )
    stats_p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (no rich tables, no ANSI).",
    )
    stats_p.add_argument(
        "--month",
        type=str,
        default=None,
        help="Filter to YYYY-MM month (e.g. 2026-07).",
    )


def _glm_command(args: argparse.Namespace) -> int:
    """Dispatch ``hermes glm`` subcommands."""
    sub = getattr(args, "glm_command", None)
    if not sub:
        print(_GLM_HELP_TEXT)
        return 0
    if sub == "stats":
        return _cmd_glm_stats(args)
    print(f"unknown subcommand: {sub!r} — available: stats")
    return 2


def _cmd_glm_stats(args: argparse.Namespace) -> int:
    """Handle ``hermes glm stats`` — read JSONL, aggregate, render table or JSON."""
    metrics = read_metrics(_metrics_file())

    # --month filter: keep only entries matching YYYY-MM.
    month_filter = getattr(args, "month", None)
    if month_filter:
        metrics = [
            m for m in metrics
            if m.get("ts", "")[:7] == month_filter
        ]

    monthly_data, stratum_data, no_token_count = _aggregate_glm_metrics(metrics)

    if no_token_count > 0:
        print(
            f"Warning: {no_token_count} entries have no token data "
            f"(pre-v15.0) — excluded from cost totals",
            file=sys.stderr,
        )

    if getattr(args, "json", False):
        return _emit_glm_json(monthly_data, stratum_data)
    return _emit_glm_rich(monthly_data, stratum_data)


def _aggregate_glm_metrics(
    metrics: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Aggregate GLM token spend by month and by stratum.

    Args:
        metrics: list of raw metric dicts from read_metrics.

    Returns:
        Tuple of (monthly_agg, stratum_agg, no_token_count):
        - monthly_agg: dict keyed by "YYYY-MM" → {
            task_count, input_tokens, output_tokens, estimated_cost_usd}
        - stratum_agg: dict keyed by stratum string → {
            task_count, total_tokens, estimated_cost_usd}
        - no_token_count: count of entries lacking token data (pre-v15.0)
    """
    monthly_agg: dict[str, dict[str, Any]] = {}
    stratum_agg: dict[str, dict[str, Any]] = {}
    no_token_count = 0

    for m in metrics:
        month = m.get("ts", "")[:7] or "unknown"
        stratum = m.get("stratum", "unknown")

        has_tokens = "input_tokens" in m
        if not has_tokens:
            no_token_count += 1

        inp = m.get("input_tokens", 0)
        out = m.get("output_tokens", 0)
        cost = m.get("estimated_cost_usd", 0.0)
        total = inp + out

        # Monthly aggregation.
        if month not in monthly_agg:
            monthly_agg[month] = {
                "task_count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
            }
        monthly_agg[month]["task_count"] += 1
        monthly_agg[month]["input_tokens"] += inp
        monthly_agg[month]["output_tokens"] += out
        monthly_agg[month]["estimated_cost_usd"] += cost

        # Stratum aggregation.
        if stratum not in stratum_agg:
            stratum_agg[stratum] = {
                "task_count": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
            }
        stratum_agg[stratum]["task_count"] += 1
        stratum_agg[stratum]["total_tokens"] += total
        stratum_agg[stratum]["estimated_cost_usd"] += cost

    return monthly_agg, stratum_agg, no_token_count


def _emit_glm_rich(monthly_data: dict[str, Any], stratum_data: dict[str, Any]) -> int:
    """Render Rich tables: monthly + per-stratum GLM cost dashboard."""
    console = Console()

    # Monthly table.
    mt = Table(title="Vision Judge Monthly Cost Dashboard", title_style="bold cyan")
    mt.add_column("Month", style="cyan")
    mt.add_column("Task Count", justify="right")
    mt.add_column("Input Tokens", justify="right")
    mt.add_column("Output Tokens", justify="right")
    mt.add_column("Est. Cost (USD)", justify="right")

    if not monthly_data:
        mt.add_row("(no data)", "0", "0", "0", "0.00")
    else:
        for month in sorted(monthly_data.keys()):
            d = monthly_data[month]
            mt.add_row(
                month,
                str(d["task_count"]),
                str(d["input_tokens"]),
                str(d["output_tokens"]),
                f"{d['estimated_cost_usd']:.4f}",
            )
    console.print(mt)

    # Stratum table.
    st = Table(title="Vision Judge Per-Stratum Breakdown", title_style="bold cyan")
    st.add_column("Stratum", style="cyan")
    st.add_column("Task Count", justify="right")
    st.add_column("Total Tokens", justify="right")
    st.add_column("Est. Cost (USD)", justify="right")

    if not stratum_data:
        st.add_row("(no data)", "0", "0", "0.00")
    else:
        for stratum in sorted(stratum_data.keys()):
            d = stratum_data[stratum]
            st.add_row(
                stratum,
                str(d["task_count"]),
                str(d["total_tokens"]),
                f"{d['estimated_cost_usd']:.4f}",
            )
    console.print(st)

    console.print(f"\n[dim]Metrics file: {_metrics_file()}[/dim]")
    return 0


def _emit_glm_json(monthly_data: dict[str, Any], stratum_data: dict[str, Any]) -> int:
    """Emit machine-readable JSON with monthly + stratum aggregation."""
    print(json.dumps(
        {"monthly": monthly_data, "stratum": stratum_data},
        ensure_ascii=False, indent=2,
    ))
    return 0

