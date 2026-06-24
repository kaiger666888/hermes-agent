"""CLI subcommand: `hermes curator <subcommand>`.

Thin shell around agent/curator.py and tools/skill_usage.py. Renders a status
table, triggers a run, pauses/resumes, and pins/unpins skills.

This module intentionally has no side effects at import time — main.py wires
the argparse subparsers on demand.

Phase 32 Plan 02 (CURATE-04 + CURATE-05) appends 5 subcommands AFTER the
existing p_rollback block: ``queue``, ``approve``, ``reject``,
``audit-log``, ``auto-apply-eligible``. The first three are thin wrappers
around P31's ``_cmd_review_queue`` / ``_cmd_approve`` / ``_cmd_reject`` in
``hermes_cli.feedback`` — single source of truth. ``audit-log`` reads the
sha256-chained audit trail (CURATE-04). ``auto-apply-eligible`` (CURATE-05)
implements the semi-automatic apply path for agent-created skills, routing
through ``_cmd_approve`` per Architectural Constraint #1 Option A (never
calls ``apply_patch_transaction`` directly — P31 structural invariant
``TestNonBypassableHumanInLoop`` passes UNCHANGED).
"""

from __future__ import annotations

import argparse
import getpass
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _fmt_ts(ts: Optional[str]) -> str:
    if not ts:
        return "never"
    try:
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return str(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


def _cmd_status(args) -> int:
    from agent import curator
    from tools import skill_usage

    state = curator.load_state()
    enabled = curator.is_enabled()
    paused = state.get("paused", False)
    last_run = state.get("last_run_at")
    summary = state.get("last_run_summary") or "(none)"
    runs = state.get("run_count", 0)

    status_line = (
        "ENABLED" if enabled and not paused else
        "PAUSED" if paused else
        "DISABLED"
    )
    print(f"curator: {status_line}")
    print(f"  runs:           {runs}")
    print(f"  last run:       {_fmt_ts(last_run)}")
    # Summary may be multi-line when the curator archived skills (the rename
    # map gets appended as `name → umbrella` lines). Indent continuation
    # lines so the block reads as one logical field.
    if "\n" in summary:
        first, *rest = summary.splitlines()
        print(f"  last summary:   {first}")
        for line in rest:
            print(f"                  {line}")
    else:
        print(f"  last summary:   {summary}")
    _report = state.get("last_report_path")
    if _report:
        suffix = "" if Path(_report).exists() else " (missing)"
        print(f"  last report:    {_report}{suffix}")
    _ih = curator.get_interval_hours()
    _interval_label = (
        f"{_ih // 24}d" if _ih % 24 == 0 and _ih >= 24
        else f"{_ih}h"
    )
    print(f"  interval:       every {_interval_label}")
    print(f"  stale after:    {curator.get_stale_after_days()}d unused")
    print(f"  archive after:  {curator.get_archive_after_days()}d unused")
    print(
        f"  consolidate:    {'on' if curator.get_consolidate() else 'off'}"
        f"{'' if curator.get_consolidate() else ' (prune-only; LLM merge pass opt-in)'}"
    )

    rows = skill_usage.agent_created_report()
    if not rows:
        print("\nno agent-created skills")
        return 0

    by_state = {"active": [], "stale": [], "archived": []}
    pinned = []
    for r in rows:
        state_name = r.get("state", "active")
        by_state.setdefault(state_name, []).append(r)
        if r.get("pinned"):
            pinned.append(r["name"])

    print(f"\nagent-created skills: {len(rows)} total")
    for state_name in ("active", "stale", "archived"):
        bucket = by_state.get(state_name, [])
        print(f"  {state_name:10s} {len(bucket)}")

    if pinned:
        print(f"\npinned ({len(pinned)}): {', '.join(pinned)}")

    # Show top 5 least-recently-active skills. Views and edits are activity too:
    # curator should not report a skill as "never used" right after skill_view()
    # or skill_manage() touched it.
    active = sorted(
        by_state.get("active", []),
        key=lambda r: r.get("last_activity_at") or r.get("created_at") or "",
    )[:5]
    if active:
        print("\nleast recently active (top 5):")
        for r in active:
            last = _fmt_ts(r.get("last_activity_at"))
            print(
                f"  {r['name']:40s}  "
                f"activity={r.get('activity_count', 0):3d}  "
                f"use={r.get('use_count', 0):3d}  "
                f"view={r.get('view_count', 0):3d}  "
                f"patches={r.get('patch_count', 0):3d}  "
                f"last_activity={last}"
            )

    # Show top 5 most-active and least-active skills by activity_count
    # (use + view + patch). This is a different signal from
    # least-recently-active: activity_count reflects frequency,
    # last_activity_at reflects recency. A skill touched 30 times a year
    # ago is high-frequency but stale; a skill touched once yesterday is
    # recent but low-frequency. Both can matter.
    active_all = by_state.get("active", [])
    if active_all:
        most_active = sorted(
            active_all,
            key=lambda r: (r.get("activity_count") or 0, r.get("last_activity_at") or ""),
            reverse=True,
        )[:5]
        if most_active and (most_active[0].get("activity_count") or 0) > 0:
            print("\nmost active (top 5):")
            for r in most_active:
                last = _fmt_ts(r.get("last_activity_at"))
                print(
                    f"  {r['name']:40s}  "
                    f"activity={r.get('activity_count', 0):3d}  "
                    f"use={r.get('use_count', 0):3d}  "
                    f"view={r.get('view_count', 0):3d}  "
                    f"patches={r.get('patch_count', 0):3d}  "
                    f"last_activity={last}"
                )

        least_active = sorted(
            active_all,
            key=lambda r: (r.get("activity_count") or 0, r.get("last_activity_at") or ""),
        )[:5]
        if least_active:
            print("\nleast active (top 5):")
            for r in least_active:
                last = _fmt_ts(r.get("last_activity_at"))
                print(
                    f"  {r['name']:40s}  "
                    f"activity={r.get('activity_count', 0):3d}  "
                    f"use={r.get('use_count', 0):3d}  "
                    f"view={r.get('view_count', 0):3d}  "
                    f"patches={r.get('patch_count', 0):3d}  "
                    f"last_activity={last}"
                )

    return 0


def _cmd_run(args) -> int:
    from agent import curator
    if not curator.is_enabled():
        print("curator: disabled via config; enable with `curator.enabled: true`")
        return 1

    dry = bool(getattr(args, "dry_run", False))
    background = bool(getattr(args, "background", False))
    synchronous = bool(getattr(args, "synchronous", False)) or not background
    # --consolidate forces the LLM umbrella-building pass on for this run,
    # overriding the config default (off). When the flag is absent, pass None
    # so run_curator_review reads curator.consolidate from config.
    consolidate = True if bool(getattr(args, "consolidate", False)) else None
    if dry:
        print("curator: running DRY-RUN (report only, no mutations)...")
    else:
        print("curator: running review pass...")
    if consolidate is None and not curator.get_consolidate():
        print(
            "curator: consolidation is off — running prune-only "
            "(deterministic stale/archive). Pass --consolidate or set "
            "`curator.consolidate: true` to enable the LLM merge pass."
        )

    def _on_summary(msg: str) -> None:
        print(msg)

    result = curator.run_curator_review(
        on_summary=_on_summary,
        synchronous=synchronous,
        dry_run=dry,
        consolidate=consolidate,
    )
    auto = result.get("auto_transitions", {})
    if auto:
        if dry:
            print(
                f"auto (preview): {auto.get('checked', 0)} candidate skill(s) "
                "— no transitions applied in dry-run"
            )
        else:
            print(
                f"auto: checked={auto.get('checked', 0)} "
                f"stale={auto.get('marked_stale', 0)} "
                f"archived={auto.get('archived', 0)} "
                f"reactivated={auto.get('reactivated', 0)}"
            )
    if not synchronous:
        print("llm pass running in background — check `hermes curator status` later")
    if dry:
        if synchronous:
            print(
                "dry-run: no changes applied. Read the report with "
                "`hermes curator status` and run `hermes curator run` (no flag) to apply."
            )
        else:
            print(
                "dry-run: no changes applied. When the report lands, read it with "
                "`hermes curator status` and run `hermes curator run` (no flag) to apply."
            )
    return 0


def _cmd_pause(args) -> int:
    from agent import curator
    curator.set_paused(True)
    print("curator: paused")
    return 0


def _cmd_resume(args) -> int:
    from agent import curator
    curator.set_paused(False)
    print("curator: resumed")
    return 0


def _cmd_pin(args) -> int:
    from tools import skill_usage
    if not skill_usage.is_agent_created(args.skill):
        print(
            f"curator: '{args.skill}' is bundled or hub-installed — cannot pin "
            "(only agent-created skills participate in curation)"
        )
        return 1
    skill_usage.set_pinned(args.skill, True)
    print(f"curator: pinned '{args.skill}' (will bypass auto-transitions)")
    return 0


def _cmd_unpin(args) -> int:
    from tools import skill_usage
    if not skill_usage.is_agent_created(args.skill):
        print(
            f"curator: '{args.skill}' is bundled or hub-installed — "
            "there's nothing to unpin (curator only tracks agent-created skills)"
        )
        return 1
    skill_usage.set_pinned(args.skill, False)
    print(f"curator: unpinned '{args.skill}'")
    return 0


def _cmd_restore(args) -> int:
    from tools import skill_usage
    ok, msg = skill_usage.restore_skill(args.skill)
    print(f"curator: {msg}")
    return 0 if ok else 1


def _cmd_archive(args) -> int:
    """Manually archive an agent-created skill. Refuses if pinned.

    The auto-curator archives stale skills on its own schedule; this verb is
    for the user who wants to archive *now* without waiting for a run.
    """
    from tools import skill_usage
    if skill_usage.get_record(args.skill).get("pinned"):
        print(
            f"curator: '{args.skill}' is pinned — unpin first with "
            f"`hermes curator unpin {args.skill}`"
        )
        return 1
    ok, msg = skill_usage.archive_skill(args.skill)
    print(f"curator: {msg}")
    return 0 if ok else 1


def _idle_days(record: dict) -> Optional[int]:
    """Days since the skill's last activity (view / use / patch).

    Falls back to ``created_at`` so a skill that was authored but never used
    can still be pruned — otherwise never-touched skills would be immortal.
    Returns None only when both fields are missing or unparseable.
    """
    ts = record.get("last_activity_at") or record.get("created_at")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - dt).days)


def _cmd_prune(args) -> int:
    """Bulk-archive agent-created skills idle for >= N days.

    Pinned skills are exempt. Already-archived skills are skipped. Default
    ``--days 90`` matches a conservative read of the curator's own archive
    threshold; adjust with ``--days``. Use ``--dry-run`` to preview.
    """
    from tools import skill_usage
    days = getattr(args, "days", 90)
    if days < 1:
        print(f"curator: --days must be >= 1 (got {days})", file=sys.stderr)
        return 2

    dry_run = bool(getattr(args, "dry_run", False))
    skip_confirm = bool(getattr(args, "yes", False))

    candidates = []
    for r in skill_usage.agent_created_report():
        if r.get("pinned"):
            continue
        if r.get("state") == skill_usage.STATE_ARCHIVED:
            continue
        idle = _idle_days(r)
        if idle is None or idle < days:
            continue
        candidates.append((r["name"], idle))

    if not candidates:
        print(f"curator: nothing to prune (no unpinned skills idle >= {days}d)")
        return 0

    candidates.sort(key=lambda c: -c[1])
    print(f"curator: {len(candidates)} skill(s) idle >= {days}d:")
    for name, idle in candidates:
        print(f"  {name:40s} idle {idle}d")

    if dry_run:
        print("\n(dry run — no changes made)")
        return 0

    if not skip_confirm:
        try:
            reply = input(f"\nArchive {len(candidates)} skill(s)? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\ncurator: aborted")
            return 1
        if reply not in {"y", "yes"}:
            print("curator: aborted")
            return 1

    archived = 0
    failures = []
    for name, _ in candidates:
        ok, msg = skill_usage.archive_skill(name)
        if ok:
            archived += 1
        else:
            failures.append((name, msg))

    print(f"\ncurator: archived {archived}/{len(candidates)}")
    if failures:
        print("failures:")
        for name, msg in failures:
            print(f"  {name}: {msg}")
        return 1
    return 0


def _cmd_backup(args) -> int:
    """Take a manual snapshot of the skills tree. Same mechanism as the
    automatic pre-run snapshot, just user-initiated."""
    from agent import curator_backup
    if not curator_backup.is_enabled():
        print(
            "curator: backups are disabled via config "
            "(`curator.backup.enabled: false`); re-enable to snapshot"
        )
        return 1
    reason = getattr(args, "reason", None) or "manual"
    snap = curator_backup.snapshot_skills(reason=reason)
    if snap is None:
        print("curator: snapshot failed — check logs (backup disabled or IO error)")
        return 1
    print(f"curator: snapshot created at ~/.hermes/skills/.curator_backups/{snap.name}")
    return 0


def _cmd_rollback(args) -> int:
    """Restore the skills tree from a snapshot. Defaults to newest.

    ``--list`` prints available snapshots and exits. ``--id <stamp>`` picks
    a specific one. Without ``-y``, prompts for confirmation. A safety
    snapshot of the current tree is always taken first, so rollbacks are
    themselves undoable.
    """
    from agent import curator_backup

    if getattr(args, "list", False):
        print(curator_backup.summarize_backups())
        return 0

    backup_id = getattr(args, "backup_id", None)
    target_path = curator_backup._resolve_backup(backup_id)
    if target_path is None:
        rows = curator_backup.list_backups()
        if not rows:
            print(
                "curator: no snapshots exist yet. Take one with "
                "`hermes curator backup` or wait for the next curator run."
            )
        else:
            print(
                f"curator: no snapshot matching "
                f"{'id ' + repr(backup_id) if backup_id else 'your query'}."
            )
            print("Available:")
            print(curator_backup.summarize_backups())
        return 1

    manifest = curator_backup._read_manifest(target_path)
    print(f"Rollback target: {target_path.name}")
    if manifest:
        print(f"  reason:      {manifest.get('reason', '?')}")
        print(f"  created_at:  {manifest.get('created_at', '?')}")
        print(f"  skill files: {manifest.get('skill_files', '?')}")
        cron = manifest.get("cron_jobs") or {}
        if isinstance(cron, dict):
            if cron.get("backed_up"):
                print(
                    f"  cron jobs:   {cron.get('jobs_count', 0)} "
                    f"(will be restored for skill-link fields only)"
                )
            else:
                reason = cron.get("reason", "not captured")
                print(f"  cron jobs:   not in snapshot ({reason})")
    print(
        "\nThis will replace the current ~/.hermes/skills/ tree (a safety "
        "snapshot of the current state is taken first so this is undoable). "
        "Cron jobs that still exist will have their skills/skill fields "
        "restored from the snapshot; all other cron fields are left alone."
    )

    if not getattr(args, "yes", False):
        try:
            ans = input("Proceed? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\ncancelled")
            return 1
        if ans not in {"y", "yes"}:
            print("cancelled")
            return 1

    ok, msg, _ = curator_backup.rollback(backup_id=target_path.name)
    if ok:
        print(f"curator: {msg}")
        return 0
    print(f"curator: rollback failed — {msg}")
    return 1


def _cmd_list_archived(args) -> int:
    """List archived (recoverable) skills."""
    from tools import skill_usage
    names = skill_usage.list_archived_skill_names()
    if not names:
        print("curator: no archived skills")
        return 0
    for name in names:
        print(name)
    return 0


# ---------------------------------------------------------------------------
# v6 Curator Upgrade handlers (CURATE-04 + CURATE-05)
#
# These handlers are THIN WRAPPERS around P31 commands in
# hermes_cli.feedback (single source of truth for queue/approve/reject) plus
# a new audit-log reader and the CURATE-05 semi-automatic apply path.
#
# Architectural Constraint #1 (LOAD-BEARING):
#   ``_cmd_auto_apply_eligible`` DELEGATES to ``_cmd_approve`` — it does NOT
#   call ``apply_patch_transaction`` directly. This keeps the P31 structural
#   invariant ``TestNonBypassableHumanInLoop`` green UNCHANGED.
#
# All ``from agent.evolution import ...`` / ``from agent.curator_audit
# import ...`` calls are LAZY (inside handler bodies) so this module has
# ZERO module-level agent.evolution imports (runtime isolation preserved).
# ---------------------------------------------------------------------------


def _get_operator() -> str:
    """Resolve the operator username for audit-log entries.

    Tries ``getpass.getuser()``; falls back to ``"unknown"`` if the call
    fails (e.g., no controlling terminal, env stripped, import error).
    """
    try:
        return getpass.getuser()
    except Exception as exc:  # noqa: BLE001 — best-effort username
        logger.debug("getpass.getuser failed: %s", exc)
        return "unknown"


def _resolve_skill_from_patch(patch_id: str) -> str:
    """Best-effort resolve skill_id from a patch_id across all queue files.

    Scans pending/applied/rejected queue files. Returns ``"unknown"`` if
    the patch_id is not present in any status file (the audit entry is
    still recorded — losing the skill_id is preferable to losing the
    audit entry).
    """
    try:
        from agent.evolution import read_queue
        from hermes_cli.feedback import _resolve_evolution_dir
    except ImportError as exc:
        logger.debug("evolution queue not importable: %s", exc)
        return "unknown"
    try:
        evo_dir = _resolve_evolution_dir()
        for status in ("pending", "applied", "rejected"):
            try:
                records = read_queue(evolution_dir=evo_dir, status=status)
            except Exception:  # noqa: BLE001 — queue read is best-effort
                continue
            for r in records:
                if r.patch_id == patch_id:
                    return r.skill_id
    except Exception as exc:  # noqa: BLE001 — skill resolve is best-effort
        logger.debug("skill resolve failed for %s: %s", patch_id, exc)
    return "unknown"


def _cmd_queue(args) -> int:
    """``hermes curator queue [--skill X] [--status pending|applied|rejected]``.

    Thin wrapper — delegates to P31 ``_cmd_review_queue`` in
    :mod:`hermes_cli.feedback` (single source of truth for queue rendering).
    """
    from hermes_cli.feedback import _cmd_review_queue
    return _cmd_review_queue(args)


def _cmd_approve_curator(args) -> int:
    """``hermes curator approve <patch_id> [--yes]``.

    Thin wrapper — delegates to P31 ``_cmd_approve`` (the single source of
    truth for ``apply_patch_transaction`` invocation per the P31 structural
    invariant). The audit-log append is wired INSIDE ``_cmd_approve`` itself
    (extended in Plan 02) so EVERY approve caller (curator wrapper AND
    direct ``hermes feedback approve``) gets the audit entry — single source
    of truth per RESEARCH A4.

    This wrapper exists for operator UX (``hermes curator`` is the
    discoverable namespace for CURATE-04) and does not duplicate logic.
    """
    from hermes_cli.feedback import _cmd_approve
    return _cmd_approve(args)


def _cmd_reject_curator(args) -> int:
    """``hermes curator reject <patch_id> <reason>``.

    Thin wrapper — delegates to P31 ``_cmd_reject`` for the queue lifecycle.
    On success (rc == 0), appends an audit entry with ``action="reject"``.

    The audit append is best-effort (try/except WARNING) per RESEARCH A4 /
    T-32-12 — a failed audit write MUST NOT block the reject.

    WR-06: resolve the skill_id BEFORE _cmd_reject moves the patch from
    pending.jsonl to rejected.jsonl. The prior order called _resolve_skill
    AFTER the move, which scanned pending first (where the patch no longer
    was), then applied, then rejected — 3 JSONL parses for one lookup.
    Resolving before the move reads pending directly (1 parse) and avoids
    the cross-file scan. If _cmd_reject ever changes to move patches
    elsewhere (e.g. retracted.jsonl), this resolver still works because
    it reads the patch at its pre-reject location.
    """
    from hermes_cli.feedback import _cmd_reject
    # Resolve skill_id while the patch is still in pending.jsonl.
    skill_id = _resolve_skill_from_patch(args.patch_id)
    rc = _cmd_reject(args)
    if rc == 0:
        try:
            from agent.curator_audit import append_audit
            append_audit(
                action="reject",
                patch_id=args.patch_id,
                skill_id=skill_id,
                operator=_get_operator(),
            )
        except Exception as exc:  # noqa: BLE001 — audit is best-effort (T-32-12)
            logger.warning(
                "audit log append failed for reject %s: %s",
                args.patch_id, exc,
            )
    return rc


def _cmd_audit_log(args) -> int:
    """``hermes curator audit-log [--action X] [--since D] [--skill Y] [--verify]``.

    CURATE-04 — query and optionally verify the tamper-evident audit trail.

    ``--verify`` walks the sha256 chain via :func:`verify_chain` and reports
    any breaks (exit 1 on break, exit 0 on valid/empty). Without
    ``--verify``, prints matching entries as
    ``{ts} {action:10s} {patch_id} skill={skill_id}``.
    """
    from agent.curator_audit import read_audit, verify_chain

    if getattr(args, "verify", False):
        breaks = verify_chain()
        if breaks:
            print(f"audit chain: {len(breaks)} break(s) detected:")
            for b in breaks:
                print(f"  line {b.get('line', '?')}: {b.get('error', '?')}")
            return 1
        print("audit chain: OK (all entries verify)")
        return 0

    entries = read_audit(
        action=getattr(args, "action", None),
        since=getattr(args, "since", None),
        skill=getattr(args, "skill", None),
    )
    if not entries:
        print("(no audit entries match)")
        return 0
    for e in entries:
        ts = e.get("ts", "?")
        action = str(e.get("action", "?"))
        patch_id = e.get("patch_id", "?")
        skill_id = e.get("skill_id", "?")
        print(f"{ts} {action:10s} {patch_id} skill={skill_id}")
    return 0


def _cmd_auto_apply_eligible(args) -> int:
    """``hermes curator auto-apply-eligible [--dry-run]`` — CURATE-05.

    Semi-automatic apply path for agent-created skills ONLY. Default OFF
    (config gate). Two-signal confidence required (mean_delta >= threshold
    AND evidence_count >= threshold). Bundled skills NEVER auto-apply
    (defense-in-depth via :func:`is_agent_created` recheck even if the
    proposer incorrectly marked the patch eligible).

    Architectural Constraint #1 (Option A):
        This handler DELEGATES to ``_cmd_approve`` for each eligible patch.
        It does NOT call ``apply_patch_transaction`` directly. The P31
        structural invariant ``TestNonBypassableHumanInLoop`` therefore
        passes UNCHANGED — ``apply_patch_transaction`` is still called only
        from ``_cmd_approve``.

    The audit entry uses ``action="auto_apply"`` (distinct from
    ``action="apply"`` so operators can filter auto vs manual in the audit
    log).
    """
    # LAZY imports preserve runtime isolation.
    from agent.curator import (
        get_auto_apply_enabled,
        get_auto_apply_min_delta,
        get_auto_apply_min_evidence,
    )
    from agent.curator_audit import append_audit
    from agent.evolution import read_queue
    from hermes_cli.feedback import _cmd_approve, _resolve_evolution_dir
    from tools.skill_usage import is_agent_created

    # Step 1: config gate — default OFF (T-32-09).
    if not get_auto_apply_enabled():
        print(
            "auto-apply disabled in config "
            "(feedback.curator.auto_apply_enabled=false)"
        )
        return 0

    min_delta = get_auto_apply_min_delta()
    min_evidence = get_auto_apply_min_evidence()

    # Step 2: scan pending queue.
    evo_dir = _resolve_evolution_dir()
    pending = read_queue(evolution_dir=evo_dir, status="pending")

    # Step 3: filter — two-signal confidence + agent-created + marked eligible.
    eligible = []
    skipped = []
    for p in pending:
        if not p.auto_apply_eligible:
            skipped.append((p.patch_id, p.skill_id, "not marked eligible"))
            continue
        if not is_agent_created(p.skill_id):
            # T-32-05 defense-in-depth: bundled NEVER auto even if the
            # proposer incorrectly marked it eligible.
            skipped.append(
                (p.patch_id, p.skill_id, "bundled skill: auto-apply forbidden")
            )
            logger.info(
                "skipped bundled skill %s for auto-apply (forbidden)",
                p.skill_id,
            )
            continue
        score = p.confidence_score or {}
        mean_delta = float(score.get("mean_delta", 0))
        evidence_count = int(score.get("evidence_count", 0))
        if mean_delta < min_delta:
            skipped.append(
                (p.patch_id, p.skill_id,
                 f"low mean_delta ({mean_delta} < {min_delta})")
            )
            continue
        if evidence_count < min_evidence:
            skipped.append(
                (p.patch_id, p.skill_id,
                 f"low evidence_count ({evidence_count} < {min_evidence})")
            )
            continue
        eligible.append(p)

    # Step 4: --dry-run lists without applying.
    if getattr(args, "dry_run", False):
        print(f"eligible for auto-apply ({len(eligible)}):")
        for p in eligible:
            print(f"  {p.patch_id} skill={p.skill_id}")
        if skipped:
            print(f"\nskipped ({len(skipped)}):")
            for pid, sid, reason in skipped:
                print(f"  {pid} skill={sid}: {reason}")
        return 0

    # Log skipped at INFO so operators can trace why a patch was bypassed.
    for pid, sid, reason in skipped:
        logger.info("auto-apply skipped %s (%s): %s", pid, sid, reason)

    # Step 5: apply each eligible patch via _cmd_approve (Option A).
    applied = 0
    failures = 0
    for p in eligible:
        # Construct an argparse.Namespace with yes=True (the operator's
        # explicit opt-in is running the command). _cmd_approve is the
        # single legitimate caller of apply_patch_transaction.
        ns = argparse.Namespace(patch_id=p.patch_id, yes=True)
        rc = _cmd_approve(ns)
        if rc == 0:
            applied += 1
            # Audit entry with action="auto_apply" (distinct from "apply").
            try:
                append_audit(
                    action="auto_apply",
                    patch_id=p.patch_id,
                    skill_id=p.skill_id,
                    operator=_get_operator(),
                    eval_score=p.eval_gate_score,
                )
            except Exception as exc:  # noqa: BLE001 — best-effort (T-32-12)
                logger.warning(
                    "audit log append failed for auto_apply %s: %s",
                    p.patch_id, exc,
                )
        else:
            failures += 1
            logger.error(
                "auto-apply failed for %s: rc=%d", p.patch_id, rc,
            )
            # Best-effort — one failure does not abort the batch.

    # Step 6: summary.
    print(
        f"auto-applied {applied} patch(es), skipped {len(skipped)}, "
        f"failed {failures}"
    )
    return 0 if failures == 0 else 1


# ---------------------------------------------------------------------------
# Phase 33 Plan 01 — `hermes curator stats` (OBS-01/02/03, read-only)
# ---------------------------------------------------------------------------

# Sparkline glyphs (CONTEXT.md D-sparkline). Index 0=lowest → 7=highest.
_SPARK = "▁▂▃▄▅▆▇█"

# Verdict → rich color style (CONTEXT.md D-stats-format).
_VERDICT_STYLES = {
    "good": "green",
    "needs_work": "yellow",
    "bad": "red",
}

# Known sources (CONTEXT.md + RESEARCH §"Architecture Patterns").
_SOURCES = ("cli", "kais_aigc", "manual")


def _sparkline(values: list[float]) -> str:
    """Compact unicode-block sparkline for a series of floats.

    Maps min(values)..max(values) onto 8 buckets (``_SPARK``).
    Empty list -> empty string. All-identical -> middle-tier block (index 4).
    """
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        # All identical → middle-tier block per CONTEXT.md D-sparkline.
        return _SPARK[4] * len(values)
    span = hi - lo
    return "".join(
        _SPARK[min(7, max(0, int((v - lo) / span * 7.999)))]
        for v in values
    )


def _collapse_verdicts(
    summary: dict[str, dict],
) -> dict[str, dict[str, object]]:
    """Collapse a FeedbackStore.summary() dict to per-verdict totals.

    Input:  ``{"<skill>:<source>:<verdict>": {count, weighted_count, first_ts, last_ts}}``
    Output: ``{"good": {count, weighted, first_ts, last_ts}, "needs_work": {...}, "bad": {...}}``

    Sources are merged; per-verdict counts + weighted_counts summed; ts
    range is min(first_ts) .. max(last_ts).
    """
    out: dict[str, dict[str, object]] = {
        v: {"count": 0, "weighted": 0.0, "first_ts": None, "last_ts": None}
        for v in ("good", "needs_work", "bad")
    }
    for key, bucket in summary.items():
        parts = key.split(":")
        if len(parts) != 3:
            continue
        verdict = parts[2]
        if verdict not in out:
            continue
        out[verdict]["count"] = int(out[verdict]["count"]) + int(
            bucket.get("count", 0)
        )
        out[verdict]["weighted"] = float(out[verdict]["weighted"]) + float(
            bucket.get("weighted_count", 0.0)
        )
        f_ts = bucket.get("first_ts")
        l_ts = bucket.get("last_ts")
        if f_ts:
            cur = out[verdict]["first_ts"]
            out[verdict]["first_ts"] = f_ts if cur is None or f_ts < cur else cur
        if l_ts:
            cur = out[verdict]["last_ts"]
            out[verdict]["last_ts"] = l_ts if cur is None or l_ts > cur else cur
    return out


def _empty_store_message() -> str:
    """Friendly message for empty FeedbackStore (T-33-05, CONTEXT.md)."""
    return (
        "no feedback yet — run /feedback in a Hermes conversation or "
        "`hermes feedback import <jsonl>` to seed data"
    )


def _render_per_skill_dashboard(
    *,
    store,
    skill_id: str,
    runs: int,
    as_json: bool,
    read_audit_fn,
    read_queue_fn,
    evolution_dir,
) -> int:
    """OBS-01 — per-skill dashboard.

    Renders verdict buckets (collapsed across sources) + patch history +
    eval-score trend. ``as_json=True`` emits COUNTS ONLY (T-33-01).
    """
    summary = store.summary(skill_id=skill_id)
    verdicts = _collapse_verdicts(summary)

    # Patch history (P31 evolution queue, status=applied, filtered to skill).
    try:
        applied_patches = read_queue_fn(
            evolution_dir=evolution_dir, status="applied",
        )
    except Exception as exc:  # noqa: BLE001 — read-only best-effort
        logger.warning("read_queue(applied) failed in stats: %s", exc)
        applied_patches = []
    skill_patches = [
        p for p in applied_patches if getattr(p, "skill_id", None) == skill_id
    ]

    # Eval-score trend (P32 audit log, action=apply, last N entries).
    try:
        audit_entries = read_audit_fn(action="apply", skill=skill_id)
    except Exception as exc:  # noqa: BLE001 — read-only best-effort
        logger.warning("read_audit(apply) failed in stats: %s", exc)
        audit_entries = []
    trend_entries = [e for e in audit_entries if e.get("eval_score")]
    trend_entries = trend_entries[-runs:] if runs > 0 else trend_entries

    total_count = sum(int(v["count"]) for v in verdicts.values())

    # Empty-store branch (T-33-05): exit 0 with friendly message.
    if total_count == 0 and not skill_patches and not trend_entries:
        print(_empty_store_message())
        return 0

    # JSON path — counts ONLY (T-33-01: no correction/output_snapshot/feedback_ids).
    if as_json:
        # Serialize eval_trend_count + recent commit shas (no feedback_ids).
        recent_commits = [
            e.get("commit_sha") for e in trend_entries
            if e.get("commit_sha")
        ]
        payload = {
            "skill_id": skill_id,
            "verdict_buckets": {
                v: int(verdicts[v]["count"]) for v in ("good", "needs_work", "bad")
            },
            "patch_count": len(skill_patches),
            "eval_trend_count": len(trend_entries),
            "recent_commit_shas": recent_commits,
        }
        import json as _json
        print(_json.dumps(payload, ensure_ascii=False))
        return 0

    # Human path — rich.table.Table rendering.
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title=f"Feedback stats: {skill_id}", show_lines=False)
    table.add_column("Verdict", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Weighted", justify="right")
    table.add_column("First ts")
    table.add_column("Last ts")
    for v in ("good", "needs_work", "bad"):
        style = _VERDICT_STYLES[v]
        b = verdicts[v]
        table.add_row(
            f"[{style}]{v}[/{style}]",
            str(b["count"]),
            f"{float(b['weighted']):.1f}",
            str(b["first_ts"] or "—"),
            str(b["last_ts"] or "—"),
        )
    console.print(table)

    # Patch history summary.
    print(f"\nApplied patches for {skill_id}: {len(skill_patches)}")
    for p in skill_patches[-5:]:
        pid = getattr(p, "patch_id", "?")
        ts = getattr(p, "ts_applied", None) or getattr(p, "ts_queued", "?")
        print(f"  {pid}  {ts}")

    # Eval-score trend (sparkline + last-N entries).
    if trend_entries:
        # Pull mean_delta per entry where present.
        deltas: list[float] = []
        for e in trend_entries:
            score = e.get("eval_score") or {}
            md = score.get("mean_delta")
            try:
                if md is not None:
                    deltas.append(float(md))
            except (TypeError, ValueError):
                pass
        spark = _sparkline(deltas) if deltas else ""
        print(f"\nEval-score trend (last {len(trend_entries)} apply entries):")
        if spark:
            print(f"  mean_delta sparkline: {spark}")
        if len(trend_entries) < runs:
            print(
                f"  (need more data for full trend: have "
                f"{len(trend_entries)}, want {runs})"
            )
    return 0


def _render_cross_skill_view(
    *,
    store,
    top_n: int,
    as_json: bool,
    hermes_home,
) -> int:
    """OBS-02 — cross-skill view: top-N negative + zero-feedback list."""
    summary = store.summary()

    # Empty-store branch (T-33-05).
    if not summary:
        print(_empty_store_message())
        return 0

    # Parse bucket keys "<skill>:<source>:<verdict>" → per_skill tally.
    per_skill: dict[str, dict[str, int]] = {}
    for key, bucket in summary.items():
        parts = key.split(":")
        if len(parts) != 3:
            continue
        skill, _source, verdict = parts
        if verdict not in ("good", "needs_work", "bad"):
            continue
        skill_row = per_skill.setdefault(
            skill, {"good": 0, "needs_work": 0, "bad": 0}
        )
        skill_row[verdict] += int(bucket.get("count", 0))

    # Top-N by negative feedback (needs_work + bad).
    neg_counts = {
        s: c["needs_work"] + c["bad"] for s, c in per_skill.items()
    }
    top_negative = sorted(neg_counts.items(), key=lambda x: -x[1])[:top_n]

    # Zero-feedback skills — from bundled movie-experts/ scan.
    bundled: list[str] = []
    bundled_root = hermes_home / "skills" / "movie-experts"
    try:
        if bundled_root.is_dir():
            bundled = sorted(
                p.name for p in bundled_root.iterdir()
                if p.is_dir() and not p.name.startswith("_")
            )
    except OSError as exc:
        logger.warning(
            "failed to scan bundled movie-experts for zero-feedback list: %s",
            exc,
        )
    zero_feedback = [s for s in bundled if s not in per_skill]

    if as_json:
        import json as _json
        payload = {
            "top_negative": [
                {"skill_id": s, "neg_count": n} for s, n in top_negative
            ],
            "zero_feedback": zero_feedback,
            "total_skills_with_feedback": len(per_skill),
        }
        print(_json.dumps(payload, ensure_ascii=False))
        return 0

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(
        title=f"Top-{len(top_negative)} skills by negative feedback",
        show_lines=False,
    )
    table.add_column("Skill", style="bold")
    table.add_column("needs_work", justify="right")
    table.add_column("bad", justify="right")
    table.add_column("good", justify="right")
    for skill, _neg in top_negative:
        c = per_skill.get(skill, {"good": 0, "needs_work": 0, "bad": 0})
        table.add_row(
            skill,
            str(c["needs_work"]),
            str(c["bad"]),
            str(c["good"]),
        )
    console.print(table)

    if zero_feedback:
        print(f"\nZero-feedback bundled skills ({len(zero_feedback)}):")
        for s in zero_feedback[:20]:
            print(f"  {s}")
        if len(zero_feedback) > 20:
            print(f"  ... and {len(zero_feedback) - 20} more")
    else:
        print("\n(no zero-feedback bundled skills detected)")
    return 0


def _render_source_breakdown(
    *,
    store,
    skill_filter: str | None,
    as_json: bool,
) -> int:
    """OBS-03 — source breakdown: per-source verdict distribution."""
    per_source: dict[str, dict[str, int]] = {}
    any_data = False
    for source in _SOURCES:
        summary = store.summary(source=source, skill_id=skill_filter)
        verdicts = _collapse_verdicts(summary)
        per_source[source] = {
            v: int(verdicts[v]["count"]) for v in ("good", "needs_work", "bad")
        }
        if any(per_source[source].values()):
            any_data = True

    if not any_data:
        print(_empty_store_message())
        return 0

    if as_json:
        import json as _json
        payload = {"by_source": per_source}
        if skill_filter:
            payload["skill_filter"] = skill_filter
        print(_json.dumps(payload, ensure_ascii=False))
        return 0

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Verdict distribution by source", show_lines=False)
    table.add_column("Source", style="bold")
    table.add_column("good", justify="right")
    table.add_column("needs_work", justify="right")
    table.add_column("bad", justify="right")
    for source in _SOURCES:
        c = per_source[source]
        style_good = _VERDICT_STYLES["good"]
        style_nw = _VERDICT_STYLES["needs_work"]
        style_bad = _VERDICT_STYLES["bad"]
        table.add_row(
            source,
            f"[{style_good}]{c['good']}[/{style_good}]",
            f"[{style_nw}]{c['needs_work']}[/{style_nw}]",
            f"[{style_bad}]{c['bad']}[/{style_bad}]",
        )
    console.print(table)
    return 0


def _stats_hermes_home():
    """Resolve HERMES_HOME for the stats handlers (isolated for testability).

    Stats is read-only and never resolves paths from operator input —
    this helper exists only to keep ``_cmd_stats`` body readable.
    """
    from hermes_constants import get_hermes_home
    return get_hermes_home()


def _cmd_stats(args) -> int:
    """``hermes curator stats`` — read-only observability (OBS-01/02/03).

    Pure aggregation over FeedbackStore (P29) + audit log (P32) +
    evolution queue (P31). NEVER mutates state (T-33-02).

    Modes:
      - ``stats <skill_id>``             → per-skill dashboard (OBS-01)
      - ``stats --all [--top N]``        → cross-skill view (OBS-02)
      - ``stats --by-source [--skill X]`` → source breakdown (OBS-03)

    Flags:
      --runs N   trend depth (default 10; OBS-01)
      --top N    cross-skill top-N (default 10; OBS-02)
      --json     emit counts-only JSON (T-33-01: no correction text)
    """
    # LAZY imports — zero module-level agent.evolution imports
    # (P31 runtime-isolation invariant; T-33-06).
    from agent.feedback_store import FeedbackStore
    from agent.curator_audit import read_audit
    from agent.evolution import read_queue
    from hermes_cli.feedback import _resolve_evolution_dir

    hermes_home = _stats_hermes_home()
    evolution_dir = _resolve_evolution_dir()
    store = FeedbackStore()

    if getattr(args, "all_skills", False):
        return _render_cross_skill_view(
            store=store,
            top_n=int(getattr(args, "top", 10) or 10),
            as_json=bool(getattr(args, "as_json", False)),
            hermes_home=hermes_home,
        )
    if getattr(args, "by_source", False):
        return _render_source_breakdown(
            store=store,
            skill_filter=getattr(args, "skill_filter", None),
            as_json=bool(getattr(args, "as_json", False)),
        )
    skill_id = getattr(args, "skill_id", None)
    if skill_id:
        return _render_per_skill_dashboard(
            store=store,
            skill_id=skill_id,
            runs=int(getattr(args, "runs", 10) or 10),
            as_json=bool(getattr(args, "as_json", False)),
            read_audit_fn=read_audit,
            read_queue_fn=read_queue,
            evolution_dir=evolution_dir,
        )
    # No args — ambiguous; print usage hint and return 0.
    print(
        "usage: hermes curator stats [<skill_id>] [--all] [--by-source] "
        "[--runs N] [--top N] [--skill <id>] [--json]"
    )
    print(
        "Pick one of: a skill_id (per-skill view), --all (cross-skill), "
        "or --by-source (source breakdown)."
    )
    return 0


# ---------------------------------------------------------------------------
# argparse wiring (called from hermes_cli.main)
# ---------------------------------------------------------------------------

def register_cli(parent: argparse.ArgumentParser) -> None:
    """Attach `curator` subcommands to *parent*.

    main.py calls this with the ArgumentParser returned by
    ``subparsers.add_parser("curator", ...)``.
    """
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    subs = parent.add_subparsers(dest="curator_command")

    p_status = subs.add_parser("status", help="Show curator status and skill stats")
    p_status.set_defaults(func=_cmd_status)

    p_run = subs.add_parser("run", help="Trigger a curator review now")
    p_run.add_argument(
        "--sync", "--synchronous", dest="synchronous", action="store_true",
        help="Wait for the LLM review pass to finish (default for manual runs)",
    )
    p_run.add_argument(
        "--background", dest="background", action="store_true",
        help="Start the LLM review pass in a background thread and return immediately",
    )
    p_run.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="Report only — no state changes, no archives, no consolidation "
             "(use this to preview what curator would do)",
    )
    p_run.add_argument(
        "--consolidate", dest="consolidate", action="store_true",
        help="Force the LLM umbrella-building consolidation pass on for this "
             "run, overriding the config default (off). Without this flag the "
             "run is prune-only unless `curator.consolidate: true` is set.",
    )
    p_run.set_defaults(func=_cmd_run)

    p_pause = subs.add_parser("pause", help="Pause the curator until resumed")
    p_pause.set_defaults(func=_cmd_pause)

    p_resume = subs.add_parser("resume", help="Resume a paused curator")
    p_resume.set_defaults(func=_cmd_resume)

    p_pin = subs.add_parser("pin", help="Pin a skill so the curator never auto-transitions it")
    p_pin.add_argument("skill", help="Skill name")
    p_pin.set_defaults(func=_cmd_pin)

    p_unpin = subs.add_parser("unpin", help="Unpin a skill")
    p_unpin.add_argument("skill", help="Skill name")
    p_unpin.set_defaults(func=_cmd_unpin)

    p_restore = subs.add_parser("restore", help="Restore an archived skill")
    p_restore.add_argument("skill", help="Skill name")
    p_restore.set_defaults(func=_cmd_restore)

    subs.add_parser("list-archived", help="List archived skills") \
        .set_defaults(func=_cmd_list_archived)

    p_archive = subs.add_parser(
        "archive",
        help="Manually archive a skill (move to .archive/, excluded from prompt)",
    )
    p_archive.add_argument("skill", help="Skill name")
    p_archive.set_defaults(func=_cmd_archive)

    p_prune = subs.add_parser(
        "prune",
        help="Bulk-archive agent-created skills idle for >= N days (default 90)",
    )
    p_prune.add_argument(
        "--days", type=int, default=90,
        help="Archive skills idle for at least N days (default: 90)",
    )
    p_prune.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip the confirmation prompt",
    )
    p_prune.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="Show what would be archived without doing it",
    )
    p_prune.set_defaults(func=_cmd_prune)

    p_backup = subs.add_parser(
        "backup",
        help="Take a manual tar.gz snapshot of ~/.hermes/skills/ "
             "(curator also does this automatically before every real run)",
    )
    p_backup.add_argument(
        "--reason", default=None,
        help="Free-text label stored in manifest.json (default: 'manual')",
    )
    p_backup.set_defaults(func=_cmd_backup)

    p_rollback = subs.add_parser(
        "rollback",
        help="Restore ~/.hermes/skills/ from a curator snapshot "
             "(defaults to the newest)",
    )
    p_rollback.add_argument(
        "--list", action="store_true",
        help="List available snapshots and exit without restoring",
    )
    p_rollback.add_argument(
        "--id", dest="backup_id", default=None,
        help="Snapshot id to restore (see `--list`); default: newest",
    )
    p_rollback.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt",
    )
    p_rollback.set_defaults(func=_cmd_rollback)

    # ── v6 Curator Upgrade subcommands (CURATE-04 + CURATE-05) ──────────
    # All ``from agent.evolution import ...`` / ``from agent.curator_audit
    # import ...`` calls in the handlers below are LAZY (inside handler
    # bodies) — this module has zero module-level agent.evolution imports,
    # preserving the runtime-isolation invariant documented at the top of
    # ``agent/evolution/__init__.py``.

    p_queue = subs.add_parser(
        "queue",
        help="List pending evolution patches (delegates to "
        "`hermes feedback review-queue`)",
    )
    p_queue.add_argument(
        "--skill", dest="skill", default=None,
        help="Filter by skill_id",
    )
    p_queue.add_argument(
        "--status", dest="status", default="pending",
        choices=["pending", "applied", "rejected"],
        help="Patch status filter (default: pending)",
    )
    p_queue.set_defaults(func=_cmd_queue)

    p_approve = subs.add_parser(
        "approve",
        help="Approve + apply a pending patch (delegates to "
        "`hermes feedback approve`; logs apply to audit trail)",
    )
    p_approve.add_argument(
        "patch_id", help="Patch ID from `hermes curator queue`"
    )
    p_approve.add_argument(
        "-y", "--yes", action="store_true",
        help="Confirm apply (REQUIRED — no default-yes path; mirrors P31)",
    )
    p_approve.set_defaults(func=_cmd_approve_curator)

    p_reject = subs.add_parser(
        "reject",
        help="Reject a pending patch with a reason (delegates to "
        "`hermes feedback reject`; logs reject to audit trail)",
    )
    p_reject.add_argument("patch_id", help="Patch ID to reject")
    p_reject.add_argument(
        "reason", help="Rejection reason (recorded in audit log)",
    )
    p_reject.set_defaults(func=_cmd_reject_curator)

    p_audit = subs.add_parser(
        "audit-log",
        help="Inspect the patch audit trail "
        "(~/.hermes/skills/.audit/log.jsonl) — query or verify sha256 chain",
    )
    p_audit.add_argument(
        "--action", dest="action", default=None,
        choices=["propose", "approve", "reject", "apply",
                 "rollback", "auto_apply"],
        help="Filter by action",
    )
    p_audit.add_argument(
        "--since", dest="since", default=None,
        help="ISO date lower bound (e.g., 2026-06-01)",
    )
    p_audit.add_argument(
        "--skill", dest="skill", default=None,
        help="Filter by skill_id",
    )
    p_audit.add_argument(
        "--verify", dest="verify", action="store_true",
        help="Walk the sha256 chain and report breaks",
    )
    p_audit.set_defaults(func=_cmd_audit_log)

    p_auto = subs.add_parser(
        "auto-apply-eligible",
        help="Apply all agent-created patches meeting two-signal "
        "confidence (CURATE-05; default OFF; bundled NEVER auto). "
        "Routes through _cmd_approve — apply_patch_transaction is "
        "STILL called only from _cmd_approve per P31 invariant.",
    )
    p_auto.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="List eligible patches without applying",
    )
    p_auto.set_defaults(func=_cmd_auto_apply_eligible)

    # Phase 33 Plan 01 — `hermes curator stats` (OBS-01/02/03, read-only)
    p_stats = subs.add_parser(
        "stats",
        help="Per-skill / cross-skill / by-source feedback stats "
        "(read-only; OBS-01/02/03). Aggregates over FeedbackStore (P29) "
        "+ audit log (P32) + evolution queue (P31).",
    )
    p_stats.add_argument(
        "skill_id", nargs="?", default=None,
        help="Skill to show (omit with --all/--by-source for cross-skill view)",
    )
    p_stats.add_argument(
        "--all", dest="all_skills", action="store_true",
        help="Cross-skill view (top-N negative feedback, zero-feedback list)",
    )
    p_stats.add_argument(
        "--by-source", dest="by_source", action="store_true",
        help="Source breakdown (CLI / kais_aigc / manual verdict distribution)",
    )
    p_stats.add_argument(
        "--top", type=int, default=10,
        help="Top-N for --all view (default: 10)",
    )
    p_stats.add_argument(
        "--runs", type=int, default=10,
        help="Eval-score trend depth (default: 10; OBS-01)",
    )
    p_stats.add_argument(
        "--skill", dest="skill_filter", default=None,
        help="Skill filter for --by-source",
    )
    p_stats.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Emit machine-readable JSON (counts only — no correction text)",
    )
    p_stats.set_defaults(func=_cmd_stats)


def cli_main(argv=None) -> int:
    """Standalone entry (also usable by hermes_cli.main fallthrough)."""
    parser = argparse.ArgumentParser(prog="hermes curator")
    register_cli(parser)
    args = parser.parse_args(argv)
    fn = getattr(args, "func", None)
    if fn is None:
        parser.print_help()
        return 0
    return int(fn(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cli_main())
