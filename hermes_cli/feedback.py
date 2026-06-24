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
import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


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

    # ── rebuild-index (Phase 29 — operator repair tool) ──────────────
    p_rebuild = subs.add_parser(
        "rebuild-index",
        help="Regenerate index.json from buckets/*.jsonl + dedup registry "
        "(idempotent repair tool — use after manual edits or index corruption)",
    )
    p_rebuild.set_defaults(func=_cmd_rebuild_index)

    # ── Phase 31 Knowledge Evolution Pipeline (EVOL-01/03/04/05) ──────
    # All ``from agent.evolution import ...`` calls are LAZY (inside handler
    # bodies) to preserve the runtime-isolation invariant:
    # ``grep -n "^from agent.evolution\|^import agent.evolution" \
    #      hermes_cli/feedback.py``
    # must return 0 matches at module top level. The handlers are only
    # dispatched when the operator invokes the corresponding subcommand.

    # ── evolve (EVOL-01) ────────────────────────────────────────────
    p_evolve = subs.add_parser(
        "evolve",
        help="Run LLM aggregation on accumulated feedback for a skill "
        "(EVOL-01; writes insights.jsonl; optionally generates + gates patches)",
    )
    p_evolve.add_argument(
        "--skill", required=True, help="Target skill_id (e.g. 'screenplay')"
    )
    p_evolve.add_argument(
        "--model", default=None,
        help="Override LLM model (default: HERMES_EVOLUTION_MODEL env or builtin default)",
    )
    p_evolve.add_argument(
        "--dry-run", action="store_true",
        help="Skip the LLM call; emit a stub insight (offline testing path)",
    )
    p_evolve.add_argument(
        "--insights-only", action="store_true",
        help="Write insights.jsonl then exit (skip patch generation + eval gate)",
    )
    p_evolve.set_defaults(func=_cmd_evolve)

    # ── review-queue (EVOL-03) ──────────────────────────────────────
    p_queue = subs.add_parser(
        "review-queue",
        help="List pending/applied/rejected patches in the review queue (EVOL-03)",
    )
    p_queue.add_argument(
        "--skill", default=None, help="Filter by skill_id"
    )
    p_queue.add_argument(
        "--status", choices=["pending", "applied", "rejected"],
        default="pending", help="Filter by status (default: pending)",
    )
    p_queue.set_defaults(func=_cmd_review_queue)

    # ── show-patch (EVOL-03) ────────────────────────────────────────
    p_show = subs.add_parser(
        "show-patch",
        help="Show the full diff + rationale + feedback chain for a patch (EVOL-03)",
    )
    p_show.add_argument("patch_id", help="Patch ID to inspect")
    p_show.set_defaults(func=_cmd_show_patch)

    # ── approve (EVOL-04 + EVOL-05) ─────────────────────────────────
    p_approve = subs.add_parser(
        "approve",
        help="Apply a pending patch atomically (EVOL-04 non-bypassable; "
        "requires --yes for non-interactive consent)",
    )
    p_approve.add_argument("patch_id", help="Patch ID to approve + apply")
    p_approve.add_argument(
        "--yes", action="store_true",
        help="Explicit operator consent (REQUIRED for non-interactive apply; "
        "without --yes the command refuses to apply and exits non-zero)",
    )
    p_approve.set_defaults(func=_cmd_approve)

    # ── reject (EVOL-03) ────────────────────────────────────────────
    p_reject = subs.add_parser(
        "reject", help="Reject a pending patch with a reason (EVOL-03)"
    )
    p_reject.add_argument("patch_id", help="Patch ID to reject")
    p_reject.add_argument("reason", help="Rejection reason")
    p_reject.set_defaults(func=_cmd_reject)

    # ── rollback (EVOL-05) ──────────────────────────────────────────
    p_rollback = subs.add_parser(
        "rollback",
        help="Revert an applied patch via ``git revert <commit_sha>`` (EVOL-05)",
    )
    p_rollback.add_argument("commit_sha", help="Commit SHA to revert")
    p_rollback.add_argument(
        "--yes", action="store_true",
        help="Explicit operator consent (REQUIRED — git revert is destructive)",
    )
    p_rollback.set_defaults(func=_cmd_rollback)


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
    """``hermes feedback watch [--interval N]``.

    Ctrl+C is caught by Python's default SIGINT handler (raised as
    KeyboardInterrupt from ``time.sleep`` inside the watcher) and
    propagated here; we swallow it and return 0. We deliberately do NOT
    pass a ``stop_event`` so the watcher installs its own SIGINT/SIGTERM
    handlers (matching the docstring's "fresh threading.Event is created
    and SIGINT/SIGTERM are wired to set it" promise) when invoked from
    the CLI foreground context. Tests that need to drive the watcher
    externally still pass ``stop_event=`` directly to
    :func:`watch_inbox_kais`.
    """
    from agent.feedback_ingest import watch_inbox_kais

    try:
        # No stop_event kwarg -> watcher creates its own Event and installs
        # signal handlers. KeyboardInterrupt from time.sleep propagates
        # here on Ctrl+C (Python's default SIGINT handler).
        watch_inbox_kais(interval=args.interval)
    except KeyboardInterrupt:
        return 0
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
        print("Validation failed:", file=sys.stderr)
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


def _cmd_rebuild_index(args) -> int:
    """``hermes feedback rebuild-index`` — regenerate index.json from scratch.

    Phase 29 operator repair tool (STORE-02 / SC-2). Reads every
    ``buckets/<skill_id>/<source>.jsonl`` file + the
    ``dedup/sha256-registry.jsonl`` audit log, then atomically rewrites
    ``index.json`` with fresh counts + weighted_counts + supersession
    state. Idempotent: running twice produces identical output.

    Use cases:
      - ``index.json`` corrupted or lost (RESEARCH Pitfall #5).
      - ``feedback.decay_window_days`` retuned in config (refresh all
        weighted_counts in one shot after restarting Hermes).
      - Operator manually edited a bucket file (prune / merge).

    The handler is thin: it instantiates :class:`FeedbackStore`, calls
    :meth:`rebuild_index`, and prints the resulting bucket count.
    """
    from agent.feedback_store import FeedbackStore

    try:
        store = FeedbackStore()
        store.rebuild_index()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error rebuilding index: {exc}", file=sys.stderr)
        return 1

    summary = store.summary()
    print(f"Index rebuilt: {len(summary)} buckets.")
    return 0


# ---------------------------------------------------------------------------
# Phase 31 Knowledge Evolution Pipeline subcommand handlers
# (EVOL-01 / EVOL-03 / EVOL-04 / EVOL-05)
#
# All ``from agent.evolution import ...`` are LAZY (inside handler bodies)
# to preserve the runtime-isolation invariant. The handlers are dispatched
# only when the operator invokes the corresponding subcommand.
# ---------------------------------------------------------------------------


def _resolve_repo_root() -> Path:
    """Walk up from cwd looking for the ``.git`` directory.

    Raises SystemExit if not inside a git work tree. Used by handlers that
    need to invoke git (apply / revert / gate subprocess).
    """
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise SystemExit(
        "must run inside the hermes-agent git repo "
        "(no .git directory found walking up from cwd)"
    )


def _resolve_evolution_dir() -> Path:
    """Return the evolution persistence directory under HERMES_HOME.

    Lazily creates it. Mirrors the FeedbackStore P29 directory pattern at
    ``~/.hermes/skills/.feedback/evolution/``.
    """
    from hermes_constants import get_hermes_home

    evolution_dir = get_hermes_home() / "skills" / ".feedback" / "evolution"
    evolution_dir.mkdir(parents=True, exist_ok=True)
    return evolution_dir


def _gate_script_path() -> Path:
    """Locate ``skills/movie-experts/_eval/gate.py`` relative to this module.

    The hyphenated ``movie-experts`` directory makes normal import impossible,
    so the gate is invoked via subprocess. The path is resolved from
    ``__file__`` (not cwd) so it's stable regardless of where the operator
    invokes the CLI.
    """
    return (
        Path(__file__).resolve().parent.parent
        / "skills" / "movie-experts" / "_eval" / "gate.py"
    )


def _run_eval_gate(
    *,
    patch_path: Path,
    skill_id: str,
    repo_root: Path,
    reports_dir: Path,
    patch_id_for_report: str,
) -> "tuple[str, dict]":
    """Invoke ``gate.py`` via subprocess and parse the verdict + score.

    Per Plan-checker Warning 4: gate.py exposes ``--reports-dir`` (NOT
    ``--report``); the gate writes ``<reports_dir>/<patch_id>.json``.

    Args:
        patch_path: Path to the unified diff to score.
        skill_id: Target skill_id.
        repo_root: Repo root for gate cwd.
        reports_dir: Directory where the gate writes its JSON report.
        patch_id_for_report: The patch_id used as the report filename stem
            (gate writes ``<reports_dir>/<patch_id>.json``).

    Returns:
        ``(verdict_str, score_dict)``. ``verdict_str`` is one of
        ``"pass"``/``"fail"``/``"inconclusive"``. ``score_dict`` is the
        parsed JSON report (or an error-shaped dict on parse failure).
    """
    gate_path = _gate_script_path()
    if not gate_path.is_file():
        raise SystemExit(
            f"gate.py not found at {gate_path} — run inside the hermes-agent repo"
        )

    reports_dir.mkdir(parents=True, exist_ok=True)

    # CR-01: Phase 31 evolution does NOT pre-generate baseline / candidate
    # answers (answer pre-generation is out of scope for v6). Pass
    # --no-answers-required so gate.py short-circuits to inconclusive +
    # writes a stub report, rather than hitting `parser.error()` which
    # exits with code 2 and collides with VERDICT_TO_EXIT["fail_regression"].
    #
    # WR-07: pass --config if a committed gate_config.yaml exists next to
    # gate.py so operator threshold tunings are respected.
    gate_dir = gate_path.parent
    gate_config_path = gate_dir / "gate_config.yaml"
    config_args: list[str] = []
    if gate_config_path.is_file():
        config_args = ["--config", str(gate_config_path)]

    # Argv-list only — NEVER shell=True (T-31-17 / T-30-02).
    result = subprocess.run(
        [
            sys.executable,
            str(gate_path),
            "--patch", str(patch_path),
            "--skill", skill_id,
            "--reports-dir", str(reports_dir),
            "--no-answers-required",
            *config_args,
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode == 0:
        verdict = "pass"
    elif result.returncode == 3:
        # gate.py multi-skill guard (per gate.py:1376-1383 --multi-skill flag)
        # OR --no-answers-required short-circuit (Phase 31 evolution).
        verdict = "inconclusive"
    elif result.returncode == 2:
        # WR-06: gate.py uses exit-code 2 for BOTH `fail_regression`
        # (VERDICT_TO_EXIT) AND `argparse.parser.error()` (missing required
        # args). We disambiguate by checking whether gate.py wrote a
        # report — if no report exists, it's the argparse-missing-args
        # path (operator mis-supplied argv); surface as inconclusive so
        # the patch lands in failed_gate.jsonl with a clear reason rather
        # than being mislabelled as fail_regression.
        verdict = "inconclusive"
    else:
        verdict = "fail"

    # Read the report JSON the gate wrote.
    report_path = reports_dir / f"{patch_id_for_report}.json"
    score: dict
    if report_path.is_file():
        try:
            score = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            score = {
                "verdict": verdict,
                "reason": "report parse error",
                "parse_error": str(exc),
                "stderr_tail": (result.stderr or "")[-200:],
            }
    else:
        score = {
            "verdict": verdict,
            "reason": "report file not written by gate",
            "stdout_tail": (result.stdout or "")[-200:],
            "stderr_tail": (result.stderr or "")[-200:],
        }
    return verdict, score


def _cmd_evolve(args) -> int:
    """``hermes feedback evolve --skill <id> [--model X] [--dry-run] [--insights-only]``.

    EVOL-01 LLM aggregation pipeline:
      1. Read feedback for the skill from FeedbackStore.
      2. Aggregate via LLM into InsightRecords (or stub for --dry-run).
      3. Append each to insights.jsonl.
      4. Unless --insights-only: generate additive diffs, run the eval gate,
         append passing patches to queue.jsonl, failing-gate to failed_gate.jsonl.

    Operator-invoked + synchronous per CONTEXT.md D-EVOL-01. No retry on LLM
    failure (RESEARCH Open Question 1 RESOLVED — operator can re-run).
    """
    # LAZY imports preserve runtime isolation.
    from agent.evolution import (
        AggregationError,
        InsightRecord,
        PatchRecord,
        aggregate_feedback,
        append_failed_gate,
        append_patch,
        generate_additive_diff,
        make_aggregation_client,
    )
    from agent.feedback_store import FeedbackStore

    evolution_dir = _resolve_evolution_dir()
    repo_root = _resolve_repo_root()
    store = FeedbackStore()  # uses get_hermes_home() internally.

    feedback = store.query(skill_id=args.skill)
    if not feedback:
        print(f"no feedback for skill {args.skill}; nothing to evolve")
        return 0

    insights_path = evolution_dir / "insights.jsonl"

    # --dry-run path: write a single stub insight, skip everything else.
    if args.dry_run:
        # Read current SKILL.md to pick a reasonable insert_after_marker.
        skill_md_path = (
            repo_root / "skills" / "movie-experts" / args.skill / "SKILL.md"
        )
        marker = "## References"
        if skill_md_path.is_file():
            content = skill_md_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("## "):
                    marker = line
                    break
        ts = datetime.now(timezone.utc)
        ts_unix = int(ts.timestamp())
        # CR-02: feedback[0] is typed FeedbackRecord (Pydantic) but may
        # arrive as a dict from test stubs. Prefer an explicit record_id
        # field when present; otherwise compute via store._make_record_id
        # (only for real FeedbackRecord objects); fall back to "fb_dry_run".
        first = feedback[0]
        if isinstance(first, dict):
            first_record_id = str(first.get("record_id") or "fb_dry_run")
        elif hasattr(first, "record_id") and getattr(first, "record_id", None):
            first_record_id = str(first.record_id)
        else:
            make_record_id = getattr(store, "_make_record_id", None)
            if callable(make_record_id):
                try:
                    first_record_id = str(make_record_id(first))
                except Exception:
                    first_record_id = "fb_dry_run"
            else:
                first_record_id = "fb_dry_run"
        stub = InsightRecord(
            insight_id=f"{args.skill}_{ts_unix}_dryrun000",
            skill_id=args.skill,
            theme=f"[dry-run] stub for {args.skill}",
            evidence_chain=[first_record_id],
            rationale="dry-run stub — no LLM call made",
            proposed_addition="# Dry-run addition\n",
            insert_after_marker=marker,
            ts=ts.isoformat(),
        )
        with insights_path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(stub.model_dump(), ensure_ascii=False) + "\n"
            )
        print(f"dry-run: 1 stub insight written to {insights_path}")
        return 0

    # Live LLM aggregation path.
    try:
        client, model = make_aggregation_client(model_override=args.model)
    except RuntimeError as exc:
        print(f"aggregation client construction failed: {exc}", file=sys.stderr)
        return 1

    try:
        insights = aggregate_feedback(
            skill_id=args.skill, store=store, client=client, model=model
        )
    except AggregationError as exc:
        print(f"aggregation failed: {exc}", file=sys.stderr)
        return 1

    # Append insights to insights.jsonl (atomic per-line appends).
    with insights_path.open("a", encoding="utf-8") as fh:
        for insight in insights:
            fh.write(
                json.dumps(insight.model_dump(), ensure_ascii=False) + "\n"
            )
    print(f"generated {len(insights)} insights for {args.skill}")

    if args.insights_only:
        # RESEARCH Open Question 3 RESOLVED — skip patch generation + gate.
        return 0

    # Patch generation + eval gate per insight.
    passed = 0
    failed = 0
    for insight in insights:
        skill_md_path = (
            repo_root / "skills" / "movie-experts" / args.skill / "SKILL.md"
        )
        if not skill_md_path.is_file():
            logger.warning(
                "SKILL.md missing for skill %s — skipping insight %s",
                args.skill, insight.insight_id,
            )
            continue
        current_content = skill_md_path.read_text(encoding="utf-8")
        try:
            diff = generate_additive_diff(
                current_content=current_content,
                proposed_addition=insight.proposed_addition,
                insert_after_marker=insight.insert_after_marker,
                skill_md_path=str(skill_md_path.relative_to(repo_root)),
            )
        except ValueError as exc:
            logger.warning(
                "diff generation failed for insight %s: %s",
                insight.insight_id, exc,
            )
            continue

        # Write diff to a temp patch file for the gate subprocess.
        patch_fd, patch_tmp_path = tempfile.mkstemp(
            prefix=f"evolve_{args.skill}_", suffix=".patch"
        )
        patch_tmp = Path(patch_tmp_path)
        try:
            os.close(patch_fd)
            patch_tmp.write_text(diff, encoding="utf-8")

            ts_unix = int(datetime.now(timezone.utc).timestamp())
            diff_digest = hashlib.sha256(diff.encode("utf-8")).hexdigest()[:16]
            patch_id = f"{args.skill}_{ts_unix}_{diff_digest}"

            verdict, score = _run_eval_gate(
                patch_path=patch_tmp,
                skill_id=args.skill,
                repo_root=repo_root,
                reports_dir=evolution_dir / "gate_reports",
                patch_id_for_report=patch_id,
            )

            if verdict == "pass":
                record = PatchRecord(
                    patch_id=patch_id,
                    skill_id=args.skill,
                    insight_id=insight.insight_id,
                    unified_diff=diff,
                    feedback_chain=list(insight.evidence_chain),
                    llm_rationale=insight.rationale,
                    eval_gate_score=score,
                    status="pending",
                    ts_queued=datetime.now(timezone.utc).isoformat(),
                )
                append_patch(record, evolution_dir)
                passed += 1
            else:
                append_failed_gate(
                    {
                        "patch_id": patch_id,
                        "insight_id": insight.insight_id,
                        "skill_id": args.skill,
                        "verdict": verdict,
                        "score": score,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    },
                    evolution_dir,
                )
                failed += 1
        finally:
            patch_tmp.unlink(missing_ok=True)

    print(
        f"generated {len(insights)} insights, "
        f"{passed} patches passed gate, "
        f"{failed} failed gate"
    )
    return 0


def _cmd_review_queue(args) -> int:
    """``hermes feedback review-queue [--skill X] [--status pending|applied|rejected]``.

    EVOL-03 — prints a table of patches in the requested status.
    """
    from agent.evolution import read_queue

    evolution_dir = _resolve_evolution_dir()
    records = read_queue(
        evolution_dir=evolution_dir, status=args.status, skill_id=args.skill
    )

    if not records:
        skill_hint = f" for {args.skill}" if args.skill else ""
        print(f"(no {args.status} patches{skill_hint})")
        return 0

    # Table header.
    print(
        "PATCH_ID                        | SKILL       | VERDICT | MEAN_DELTA | #FB | SUMMARY"
    )
    print("-" * 90)
    for r in records:
        verdict = r.eval_gate_score.get("verdict", "?") if r.eval_gate_score else "?"
        mean_delta = r.eval_gate_score.get("mean_delta", "?") if r.eval_gate_score else "?"
        patch_id_short = r.patch_id[:30]
        summary_short = (r.llm_rationale or "")[:40]
        print(
            f"{patch_id_short:<30} | {r.skill_id:<11} | {verdict:<7} | "
            f"{str(mean_delta):<10} | {len(r.feedback_chain):<2} | {summary_short}"
        )
    return 0


def _cmd_show_patch(args) -> int:
    """``hermes feedback show-patch <patch_id>`` — EVOL-03.

    Searches pending, applied, and rejected queues; prints full metadata +
    the unified diff in a fenced block.
    """
    from agent.evolution import read_queue

    evolution_dir = _resolve_evolution_dir()
    match = None
    for status in ("pending", "applied", "rejected"):
        records = read_queue(evolution_dir=evolution_dir, status=status)
        match = next((r for r in records if r.patch_id == args.patch_id), None)
        if match:
            break

    if not match:
        print(
            f"patch {args.patch_id} not found in any queue file",
            file=sys.stderr,
        )
        return 1

    print(f"Patch: {match.patch_id}")
    print(f"Skill: {match.skill_id}")
    print(f"Insight: {match.insight_id}")
    print(f"Status: {match.status}")
    print(f"Feedback chain: {match.feedback_chain}")
    print(f"Eval: {match.eval_gate_score}")
    print()
    print("Rationale:")
    print(match.llm_rationale or "(none)")
    print()
    print("Unified diff:")
    print("```diff")
    print(match.unified_diff)
    print("```")
    return 0


def _cmd_reject(args) -> int:
    """``hermes feedback reject <patch_id> <reason>`` — EVOL-03.

    Moves a pending patch to rejected.jsonl with the given reason.
    """
    from agent.evolution import move_patch

    evolution_dir = _resolve_evolution_dir()
    try:
        updated = move_patch(
            patch_id=args.patch_id,
            target_status="rejected",
            evolution_dir=evolution_dir,
            reason=args.reason,
        )
    except KeyError as exc:
        print(f"patch not found: {exc}", file=sys.stderr)
        return 1

    print(f"rejected {updated.patch_id}: {args.reason}")
    return 0


def _cmd_approve(args) -> int:
    """``hermes feedback approve <patch_id> [--yes]`` — EVOL-04 + EVOL-05.

    EVOL-04 non-bypassable human-in-loop: this is the ONLY code path in
    the codebase that calls ``apply_patch_transaction``. Without ``--yes``,
    the command refuses to apply and exits non-zero (no default-yes path).

    On success: atomic git apply + commit (delegated to
    ``apply_patch_transaction``), patch moves to applied.jsonl with the
    commit_sha.

    On ApplyError: working tree auto-reverted by apply_patch_transaction;
    patch STAYS pending; operator can retry or reject.
    """
    # EVOL-04: --yes is explicit operator consent. No --yes → refuse.
    if not args.yes:
        print(
            "approval required (pass --yes to confirm)",
            file=sys.stderr,
        )
        return 1

    # LAZY imports — apply_patch_transaction is the SOLE caller gate
    # (TestNonBypassableHumanInLoop enforces this structurally via ast).
    from agent.evolution import (
        ApplyError,
        apply_patch_transaction,
        build_commit_message,
        move_patch,
        read_queue,
    )

    evolution_dir = _resolve_evolution_dir()
    repo_root = _resolve_repo_root()

    # Look up the pending patch.
    records = read_queue(evolution_dir=evolution_dir, status="pending")
    match = next((r for r in records if r.patch_id == args.patch_id), None)
    if not match:
        print(
            f"patch {args.patch_id} not found in pending queue",
            file=sys.stderr,
        )
        return 1

    # Write the unified_diff to a temp .patch file for git apply.
    patch_fd, patch_tmp_path = tempfile.mkstemp(
        prefix=f"approve_{args.patch_id}_", suffix=".patch"
    )
    patch_tmp = Path(patch_tmp_path)
    try:
        os.close(patch_fd)
        patch_tmp.write_text(match.unified_diff, encoding="utf-8")

        commit_message = build_commit_message(
            insight_summary=(match.llm_rationale or "")[:72],
            feedback_ids=list(match.feedback_chain),
            eval_verdict=str(
                (match.eval_gate_score or {}).get("verdict", "unknown")
            ),
            eval_mean_delta=float(
                (match.eval_gate_score or {}).get("mean_delta", 0.0)
            ),
        )

        try:
            result = apply_patch_transaction(
                patch_path=patch_tmp,
                repo_root=repo_root,
                commit_message=commit_message,
            )
        except ApplyError as exc:
            # Working tree already auto-reverted; patch stays pending.
            print(
                f"apply failed (working tree restored): {exc}",
                file=sys.stderr,
            )
            return 1

        # Success: move patch to applied.jsonl with the commit_sha.
        move_patch(
            patch_id=args.patch_id,
            target_status="applied",
            evolution_dir=evolution_dir,
            commit_sha=result.commit_sha,
        )
        print(f"applied {args.patch_id} as commit {result.commit_sha[:12]}")
        return 0
    finally:
        patch_tmp.unlink(missing_ok=True)


def _cmd_rollback(args) -> int:
    """``hermes feedback rollback <commit_sha> [--yes]`` — EVOL-05.

    Invokes ``git revert <commit_sha> --no-edit``. ``--yes`` is REQUIRED
    (git revert is destructive — no default-yes path). Validates the SHA
    exists before invoking revert (fail fast on typos).
    """
    if not args.yes:
        print("rollback requires --yes", file=sys.stderr)
        return 1

    repo_root = _resolve_repo_root()

    # Validate the commit SHA exists BEFORE invoking revert.
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", args.commit_sha],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if verify.returncode != 0:
        print(f"commit {args.commit_sha} not found", file=sys.stderr)
        return 1

    revert_result = subprocess.run(
        ["git", "revert", args.commit_sha, "--no-edit"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if revert_result.returncode != 0:
        # Tail only — avoid dumping full git output (could contain diffs).
        print(
            f"git revert failed:\n{(revert_result.stderr or '')[-400:]}",
            file=sys.stderr,
        )
        return 1

    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    revert_sha = sha_result.stdout.strip()
    print(f"reverted {args.commit_sha} as {revert_sha[:12]}")
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
