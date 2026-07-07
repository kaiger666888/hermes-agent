"""v6.0 FeedbackStore → v10.0 memory-record schema migration script (EVAL-07).

Per Phase 55 Plan 04 / Phase 49 ``04-MIGRATION-PATH.md`` §4 + Phase 49
``05-POC-PLAN.md`` §4.7. P14 mitigation: zero silent drops + safe defaults.

Default mode is **dry-run** (EVAL-06 invariant — pattern from Phase 55 Plan 03).
Dry-run produces a 5-metric diff report (Markdown + JSON summary) without
writing to mem0. Live migration (``--apply``) is gated by a confirmation
prompt and is OUT OF SCOPE for v11.0 PoC operators (deferred to v12+ per
``04-MIGRATION-PATH.md`` §4.7 Step 4).

This script performs **deterministic field mapping only** — NO LLM dispatch.
(The curator compaction path in 55-01 uses GLM dispatch; this path does not.)

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - ``get_hermes_home()`` from :mod:`hermes_constants` (NEVER Path.home()).
  - ``argparse`` CLI with explicit mutually-exclusive group.
  - Lazy %-logging; specific exceptions bound with ``as exc``.

Read-only enforcement (T-55-11):
  Script opens all source files in ``"r"`` mode. Never ``"w"`` / ``"a"`` /
  ``"r+"`` on source. The source ``dedup/sha256-registry.jsonl`` audit log
  is NEVER appended to in dry-run mode.

Audit log entries (T-55-15):
  ``curator_audit.append_audit(action="auto_apply", ...)`` is called ONLY
  in :func:`run_live_migration`. Dry-run MUST NOT call ``append_audit``
  (T-55-14 mitigation).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Lazy imports — keep the script's startup fast (esp. for --help).
# We import FeedbackRecord lazily inside map_record / run_dry_run so that
# test_field_mapping.py can import this module without triggering Pydantic
# validation at import time (Pydantic V2 is heavy).

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────

DEFAULT_SCHEMA_VERSION: str = "1.0.0"
"""Target memory-record schema version (per memory-record-schema.yaml §3.12)."""

DEFAULT_CONFIDENCE: float = 0.5
"""OQ-4 neutral baseline (per spec §5 row 4)."""

DEFAULT_HALF_LIFE_DAYS: int = 180
"""Conservative expiry window (mirrors feedback_store.DEFAULT_DECAY_WINDOW_DAYS)."""

DEFAULT_OUT_PATH: str = "migration-dryrun-report.json"
"""Default --out path for the JSON summary."""

CONFIRMATION_TOKEN: str = "apply"
"""Token the user must type to confirm ``--apply`` (defense-in-depth)."""

_PERSONA_ZERO_HASH: str = "0" * 64
"""Sentinel persona_sha256 when agent YAML persona not found (per spec §5)."""

_VERDICT_TO_STATUS: dict[str, str] = {
    "good": "active",
    "needs_work": "active",  # informational, not blocking
    "bad": "quarantined",    # P14 mitigation — never auto-activate
}
"""Per Phase 49 §4.3 table. CODE is authoritative (NOT doc which claims
positive/negative/neutral — see migration-dry-run-format.md §2)."""

_SOURCE_TO_EVIDENCE_TYPE: dict[str, str] = {
    "cli": "operator",
    "manual": "operator",
    "kais_aigc": "auto_eval",
}
"""Per spec §3.2 evidence_chain mapping."""


# ── record_id (deterministic UUIDv5) ─────────────────────────────────────


def compute_record_id(source_line: str) -> str:
    """Compute a deterministic ``record_id`` from a source JSONL line.

    Uses UUIDv5 with ``NAMESPACE_OID`` + ``sha256(source_line_bytes)`` so
    re-runs produce identical IDs (reproducible dry-run reports per spec §4.1).

    Args:
        source_line: The raw JSONL line as read from the bucket file (the
            exact bytes — including any trailing whitespace if present, but
            callers should ``strip()`` first for stability).

    Returns:
        UUID string (hyphenated form).
    """
    digest = hashlib.sha256(source_line.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_OID, digest))


# ── map_record (pure — unit test surface) ────────────────────────────────


def map_record(
    record: Any,
    *,
    agent_persona_sha256: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Map a v6.0 :class:`FeedbackRecord` → v10.0 memory-record dict.

    Pure function — no I/O, no logging, no side effects. The unit-test
    surface for the 17-row Phase 49 §4.3 mapping table.

    Args:
        record: A validated :class:`agent.feedback_schema.FeedbackRecord`
            instance. (Untyped to avoid importing Pydantic at module load —
            the call sites pass validated Pydantic instances.)
        agent_persona_sha256: Optional dict mapping ``agent_id`` →
            pre-computed persona sha256. If absent or no entry for this
            agent_id, falls back to :data:`_PERSONA_ZERO_HASH` (and the
            caller is expected to flag this as a mapping warning).

    Returns:
        Target memory-record dict conforming to memory-record-schema.yaml
        (10 mandated fields + selected optional fields with safe defaults).
    """
    persona_map = agent_persona_sha256 or {}
    target: dict[str, Any] = {}

    # ── Identity + routing (§3.1) ──────────────────────────────────────
    target["agent_id"] = record.skill_id  # verbatim per §4.3 row 1

    # ── Verdict → status (§3.8 + P14 mitigation) ──────────────────────
    target["status"] = _VERDICT_TO_STATUS.get(record.verdict, "archived")
    # ^ "archived" is the safe-default-on-unknown-field (P14 mitigation 2)
    # per spec §5 row 3. Should never fire in practice — verdict enum is
    # constrained — but if a future schema-drift case slips through we
    # fail-safe to non-active.

    # ── Scope (§3.9 + P14 mitigation 2) ───────────────────────────────
    target["scope"] = "project"  # tightest scope default
    target["project_id"] = "unknown"  # P14: never null, always trackable
    target["session_id"] = None

    # ── Confidence (§3.5 + OQ-4) ──────────────────────────────────────
    target["confidence"] = DEFAULT_CONFIDENCE

    # ── Evidence chain (§3.6) ─────────────────────────────────────────
    # Constructed from source FeedbackRecord. Length=1 (below P5 ≥3 threshold
    # — flagged as mapping warning at compute_metrics time, NOT here).
    evidence_entry = {
        "source_type": _SOURCE_TO_EVIDENCE_TYPE.get(record.source, "operator"),
        "source_id": record.output_snapshot.sha256,
        "timestamp": record.ts.isoformat(),
        "excerpt": record.output_snapshot.output_text[:200]
        if record.output_snapshot.output_text
        else "",
    }
    target["evidence_chain"] = [evidence_entry]
    target["evidence_operator_ids"] = ["unknown"]
    # ^ Divergence: FeedbackRecord has no operator_id field (MIGRATION-PATH
    # §4.1 doc lists operator_id, but actual code doesn't have it). Default
    # to ["unknown"] per spec §3.2 mapping table.

    # ── created_at (verbatim ts) ──────────────────────────────────────
    target["created_at"] = record.ts.isoformat()

    # ── persona_sha256 (OQ-1 + P1) ───────────────────────────────────
    target["persona_sha256"] = persona_map.get(record.skill_id, _PERSONA_ZERO_HASH)

    # ── schema_version (§3.12) ───────────────────────────────────────
    target["schema_version"] = DEFAULT_SCHEMA_VERSION

    # ── content (derived from correction + revised_output) ───────────
    content_parts: list[str] = []
    if record.correction:
        content_parts.append(record.correction)
    if record.revised_output:
        content_parts.append(f"Suggested revision: {record.revised_output}")
    if content_parts:
        target["content"] = "\n\n".join(content_parts)
    else:
        # Empty correction + no revised_output → placeholder (NOT empty string).
        # P14 mitigation — never silently blank. Generates a mapping warning
        # at compute_metrics time.
        target["content"] = "<no feedback text>"

    # ── Safe defaults (§4.6 / spec §5) ───────────────────────────────
    apply_safe_defaults(target, source_record=record)

    return target


def apply_safe_defaults(
    target_record: dict[str, Any],
    *,
    source_record: Any,
) -> dict[str, Any]:
    """Apply the 6 safe-default rules from Phase 49 §4.6 (mutates in place).

    Called by :func:`map_record`. Exposed as a separate function for
    unit-test surface.

    Args:
        target_record: The dict being built (mutated in place).
        source_record: The source FeedbackRecord (for derived defaults
            like ``expires_at = created_at + 180 days``).

    Returns:
        The same dict (for chaining).
    """
    # 1. confidentiality → "confidential" (safest not most permissive).
    target_record.setdefault("confidentiality", "confidential")
    # 2. scope → "project" (already set in map_record; idempotent here).
    target_record.setdefault("scope", "project")
    # 3. status safe-default-on-unknown-field is "archived" — already handled
    #    by map_record's .get(..., "archived") fallback.
    # 4. confidence → 0.5 (OQ-4).
    target_record.setdefault("confidence", DEFAULT_CONFIDENCE)
    # 5. half_life_days → 180.
    target_record.setdefault("half_life_days", DEFAULT_HALF_LIFE_DAYS)
    # 6. expires_at → created_at + 180 days.
    if "expires_at" not in target_record:
        created = datetime.fromisoformat(target_record["created_at"])
        target_record["expires_at"] = (
            created + timedelta(days=DEFAULT_HALF_LIFE_DAYS)
        ).isoformat()

    # Additional defaults (not in §4.6's six but required by target schema).
    target_record.setdefault("verified_at", target_record["created_at"])
    target_record.setdefault("supersedes_memory_id", None)
    target_record.setdefault("last_recalled_at", None)
    target_record.setdefault("recall_count", 0)

    return target_record


# ── Source reader (read-only) ────────────────────────────────────────────


def _read_source_records(
    source_path: Path,
) -> tuple[list[tuple[Any, str, str, int]], list[dict[str, Any]], dict[str, Any]]:
    """Walk ``buckets/<skill_id>/<source>.jsonl`` and parse each line.

    Read-only — opens all files in ``"r"`` mode. Never writes.

    Args:
        source_path: Root of the v6.0 FeedbackStore (the dir containing
            ``buckets/`` + ``index.json``).

    Returns:
        Tuple ``(records, warnings, source_meta)`` where:
          - ``records`` is a list of ``(FeedbackRecord, source_file_rel,
              raw_line, lineno)`` tuples. Malformed lines are excluded —
              they appear in ``warnings`` instead.
          - ``warnings`` is a list of mapping_warning dicts (already
              structured for direct insertion into the JSON summary).
          - ``source_meta`` is a dict with ``bucket_breakdown``,
              ``index_version``, etc.
    """
    # Lazy import — avoids Pydantic load at script startup.
    from agent.feedback_schema import FeedbackRecord

    buckets_root = source_path / "buckets"
    index_path = source_path / "index.json"

    if not buckets_root.is_dir():
        raise FileNotFoundError(
            f"source buckets dir not found: {buckets_root} "
            f"(expected layout: <source>/buckets/<skill_id>/<source>.jsonl)"
        )

    # Read index.json (tolerate missing — defensive).
    index_version = 1
    if index_path.is_file():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(index_data, dict):
                index_version = int(index_data.get("version", 1))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("source index.json unreadable: %s", exc)

    records: list[tuple[Any, str, str, int]] = []
    warnings: list[dict[str, Any]] = []
    bucket_breakdown: dict[str, dict[str, int]] = {}

    for bucket_file in sorted(buckets_root.glob("*/*.jsonl")):
        skill_id = bucket_file.parent.name
        source_name = bucket_file.stem
        rel = f"buckets/{skill_id}/{source_name}.jsonl"

        bucket_breakdown.setdefault(skill_id, {})
        bucket_breakdown[skill_id].setdefault(source_name, 0)

        with open(bucket_file, "r", encoding="utf-8") as f:
            for lineno, raw_line in enumerate(f, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue  # skip blank lines (not a warning)
                try:
                    record = FeedbackRecord.model_validate_json(stripped)
                except Exception as exc:  # noqa: BLE001 — log, don't crash
                    # P14 mitigation: log to mapping_warnings, do NOT silently drop.
                    warnings.append({
                        "record_id": None,
                        "source_file": rel,
                        "line": lineno,
                        "field": "_parse",
                        "warning": f"malformed FeedbackRecord: {type(exc).__name__}: {exc}",
                    })
                    continue
                records.append((record, rel, stripped, lineno))
                bucket_breakdown[skill_id][source_name] += 1

    source_meta = {
        "index_version": index_version,
        "bucket_breakdown": bucket_breakdown,
    }
    return records, warnings, source_meta


# ── compute_metrics (pure — unit test surface) ──────────────────────────


def compute_metrics(
    source_records: list[Any],
    target_records: list[dict[str, Any]],
    *,
    parse_warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute the 5-metric summary per spec §3.2.

    Pure function. Returns the metrics dict (does NOT include the outer
    summary envelope — that's :func:`build_summary`'s job).

    Args:
        source_records: List of parsed FeedbackRecord instances.
        target_records: List of mapped target dicts (same length +
            same order as ``source_records``).
        parse_warnings: Pre-computed parse warnings (from malformed lines).

    Returns:
        Dict with the 5 §4.5 keys + the 3 migration-tracking bonus keys.
    """
    parse_warnings = parse_warnings or []
    n = len(source_records)

    # (a) total_source_count
    total_source_count = n

    # (b) per_field_default_fill_rate — fraction of records where each
    #     target field was source-derived (vs default-backed).
    #     Heuristic: a field is "source-derived" if it varies across records
    #     (because defaults are constant). For constant fields the rate is 0.0.
    field_values: dict[str, set] = {}
    for tr in target_records:
        for k, v in tr.items():
            field_values.setdefault(k, set())
            # Use repr so unhashable values (lists/dicts) become hashable strings.
            field_values[k].add(json.dumps(v, sort_keys=True, ensure_ascii=False))
    # "Default-backed" fields are constant across all records. Heuristic per
    # spec §3.1 — a more rigorous check would tag each field individually.
    default_fill_rate: dict[str, float] = {}
    default_sentinels = {
        "scope": "project",
        "confidence": DEFAULT_CONFIDENCE,
        "confidentiality": "confidential",
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "half_life_days": DEFAULT_HALF_LIFE_DAYS,
        "persona_sha256": _PERSONA_ZERO_HASH,
        "project_id": "unknown",
        "evidence_operator_ids": ["unknown"],
        "supersedes_memory_id": None,
        "session_id": None,
        "recall_count": 0,
        "last_recalled_at": None,
    }
    source_derived_fields = {
        "agent_id",  # skill_id verbatim
        "status",    # verdict mapping
        "created_at",  # ts verbatim
        "record_id",   # UUIDv5 from content (generated, not default)
        "evidence_chain",  # constructed from source
        "content",  # from correction/revised_output
    }
    for field in (
        "record_id", "agent_id", "status", "scope", "confidence",
        "evidence_chain", "created_at", "persona_sha256", "schema_version",
        "content", "confidentiality", "half_life_days",
    ):
        if field in source_derived_fields:
            default_fill_rate[field] = 1.0 if field != "content" else (
                # Content is source-derived unless it's the placeholder.
                sum(
                    1 for tr in target_records
                    if tr.get("content") != "<no feedback text>"
                ) / n if n else 0.0
            )
            if field == "record_id":
                default_fill_rate[field] = 0.0  # generated, never source-derived
            if field == "evidence_chain":
                default_fill_rate[field] = 1.0  # constructed from source
        else:
            # Default-backed — count fraction that exactly equals the default.
            default_val = default_sentinels.get(field)
            if n == 0:
                default_fill_rate[field] = 0.0
            else:
                matching_default = sum(
                    1 for tr in target_records if tr.get(field) == default_val
                )
                # fill rate is fraction DEFAULT-backed (not source-derived).
                default_fill_rate[field] = 1.0 - (matching_default / n)

    # Re-express per_field_default_fill_rate as "fraction source-derived"
    # per spec §3.1 example (status: 96.2% source-derived, ...).
    # The keys in default_fill_rate already represent source-derived fraction.

    # (c) conflict_count
    quarantined_count = sum(
        1 for tr in target_records if tr.get("status") == "quarantined"
    )
    # evidence_chain length always 1 (single-source migration) — all below P5 ≥3.
    below_min = sum(
        1 for tr in target_records if len(tr.get("evidence_chain", [])) < 3
    )
    # Per-record mapping warnings (other than _parse warnings).
    field_warnings: list[dict[str, Any]] = []
    for tr in target_records:
        if tr.get("content") == "<no feedback text>":
            field_warnings.append({
                "record_id": tr.get("record_id"),
                "field": "content",
                "warning": "empty correction with no revised_output — content defaulted to '<no feedback text>'",
            })
        if tr.get("persona_sha256") == _PERSONA_ZERO_HASH:
            field_warnings.append({
                "record_id": tr.get("record_id"),
                "field": "persona_sha256",
                "warning": f"agent YAML persona not found for agent_id={tr.get('agent_id')} — defaulted to zero-hash",
            })

    all_warnings = list(parse_warnings) + field_warnings
    conflict_count = {
        "quarantined_verdict_bad": quarantined_count,
        "evidence_chain_below_min": below_min,
        "mapping_warnings_count": len(all_warnings),
    }

    # (d) estimated_target_storage_mb — sum of record JSON sizes.
    total_bytes = sum(
        len(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
        for tr in target_records
    )
    estimated_mb = round(total_bytes / (1024 * 1024), 6)

    # Migration-tracking bonus metrics (05-POC-PLAN.md §4.7).
    migrated_active = sum(1 for tr in target_records if tr.get("status") == "active")
    migrated_quarantined = sum(
        1 for tr in target_records if tr.get("status") == "quarantined"
    )
    dropped_or_failed = 0  # always 0 — P14 mitigation: zero silent drops

    return {
        "total_source_count": total_source_count,
        "migrated_active": migrated_active,
        "migrated_quarantined": migrated_quarantined,
        "dropped_or_failed": dropped_or_failed,
        "malformed_lines": len(parse_warnings),
        "per_field_default_fill_rate": default_fill_rate,
        "conflict_count": conflict_count,
        "estimated_target_storage_mb": estimated_mb,
        "mapping_warnings": all_warnings,
    }


# ── render_markdown_report (pure) ────────────────────────────────────────


def render_markdown_report(
    summary: dict[str, Any],
    *,
    source_path: Path,
) -> str:
    """Render the §4.5 example Markdown report (human-readable).

    Pure function. Returns the report as a string (does NOT print).
    """
    m = summary["metrics"]
    lines: list[str] = []
    sep = "=" * 64
    lines.append(sep)
    lines.append("  v6.0 FeedbackStore → v10.0 memory-record Migration Dry-Run")
    lines.append(sep)
    lines.append(f"Source: {source_path}  (index_version={summary['source']['index_version']})")
    lines.append(f"Target schema: memory-record-schema.yaml v{DEFAULT_SCHEMA_VERSION}")
    mode = "DRY-RUN (no writes will occur)" if summary["dry_run"] else "LIVE (--apply)"
    lines.append(f"Mode: {mode}")
    lines.append(f"Timestamp: {summary['timestamp']}")
    lines.append("")

    # (a) total source count
    n = m["total_source_count"]
    bb = summary["source"]["bucket_breakdown"]
    lines.append(f"(a) Total source records: {n} FeedbackRecord lines across "
                 f"{sum(len(v) for v in bb.values())} bucket files")
    lines.append("    Breakdown by agent_id:")
    for skill_id, sources in sorted(bb.items()):
        total_skill = sum(sources.values())
        pct = (total_skill / n * 100) if n else 0
        lines.append(f"      {skill_id}: {total_skill} ({pct:.1f}%)")
        for source_name, count in sorted(sources.items()):
            lines.append(f"        └─ {source_name}: {count}")
    lines.append("")

    # (b) per-field fill rate
    rates = m["per_field_default_fill_rate"]
    lines.append("(b) Per-target-field default fill rate:")
    for field, rate in sorted(rates.items()):
        pct = rate * 100
        if rate >= 0.999:
            label = f"{pct:.1f}% source-derived"
        elif rate <= 0.001:
            label = f"{100 - pct:.1f}% default-backed"
        else:
            label = f"{pct:.1f}% source-derived / {100 - pct:.1f}% default"
        lines.append(f"    {field:<20} {label}")
    lines.append("")

    # (c) conflict count
    cc = m["conflict_count"]
    lines.append("(c) Conflict count:")
    lines.append(f"    quarantined (verdict=bad → status=quarantined): "
                 f"{cc['quarantined_verdict_bad']} records")
    lines.append(f"    evidence_chain below P5 ≥3 threshold: "
                 f"{cc['evidence_chain_below_min']} records")
    lines.append(f"    mapping warnings: {cc['mapping_warnings_count']}")
    lines.append("")

    # (d) estimated target storage
    lines.append(f"(d) Estimated target storage: "
                 f"{m['estimated_target_storage_mb'] * 1024:.1f} KB after migration")
    lines.append("")

    # (e) mapping warnings
    warnings = m["mapping_warnings"]
    lines.append("(e) Mapping warnings:")
    if not warnings:
        lines.append("    OK: no mapping warnings")
    else:
        for w in warnings[:20]:  # cap to keep report readable
            loc = f"{w.get('source_file', '?')}:{w.get('line', '?')}"
            field = w.get("field", "?")
            msg = w.get("warning", "?")
            lines.append(f"    WARNING: {loc} — {field}: {msg}")
        if len(warnings) > 20:
            lines.append(f"    ... ({len(warnings) - 20} more warnings — see JSON summary)")
    lines.append("")

    # Footer
    lines.append(sep)
    if summary["dry_run"]:
        lines.append(
            "  NO WRITE OCCURRED. To apply: "
            "python scripts/migrate_v6_feedback_to_memory_schema.py --apply"
        )
        lines.append(
            "  (Live migration is OUT OF SCOPE for v11.0 PoC — "
            "see 04-MIGRATION-PATH.md §4.7 Step 4)"
        )
    else:
        lines.append(f"  LIVE MIGRATION COMPLETE. "
                     f"{m['migrated_active']} active + {m['migrated_quarantined']} quarantined.")
    lines.append(sep)

    return "\n".join(lines)


# ── build_summary (assembles JSON summary envelope) ─────────────────────


def build_summary(
    *,
    source_records: list[Any],
    target_records: list[dict[str, Any]],
    source_meta: dict[str, Any],
    parse_warnings: list[dict[str, Any]],
    source_path: Path,
    dry_run: bool,
    timestamp: str,
) -> dict[str, Any]:
    """Assemble the full JSON summary envelope per spec §3.2.

    Args:
        source_records: Parsed FeedbackRecord list.
        target_records: Mapped target dicts (same length + order).
        source_meta: Output of :func:`_read_source_records` source_meta slot.
        parse_warnings: Pre-computed parse warnings.
        source_path: Source root path (for the ``source.path`` field).
        dry_run: Whether this is a dry-run summary.
        timestamp: ISO-8601 timestamp string.

    Returns:
        The full summary dict ready for JSON serialization.
    """
    metrics = compute_metrics(
        source_records, target_records, parse_warnings=parse_warnings,
    )
    # Attach record_id to each target record (so source_record_ids_accounted
    # can list them). map_record doesn't set record_id because it's derived
    # from the source LINE (not the parsed record) — done at the read step.
    # The target_records list passed in should already have record_id set
    # by run_dry_run before calling build_summary.

    accounted_ids = [tr.get("record_id") for tr in target_records if tr.get("record_id")]

    return {
        "source": {
            "path": str(source_path),
            "index_version": source_meta["index_version"],
            "total_records": len(source_records),
            "bucket_breakdown": source_meta["bucket_breakdown"],
        },
        "target": {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "estimated_storage_bytes": int(
                metrics["estimated_target_storage_mb"] * 1024 * 1024
            ),
        },
        "metrics": metrics,
        "source_record_ids_accounted": accounted_ids,
        "dry_run": dry_run,
        "timestamp": timestamp,
    }


# ── run_dry_run (primary v11.0 PoC path) ─────────────────────────────────


def run_dry_run(source_path: Path, out_path: Path) -> dict[str, Any]:
    """Execute the dry-run migration (primary v11.0 PoC path).

    Read-only on source. Writes ONLY the JSON summary to ``out_path``.
    Zero ``append_audit`` calls.

    Args:
        source_path: Root of the v6.0 FeedbackStore.
        out_path: Where to write the JSON summary.

    Returns:
        The JSON summary dict.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"source path does not exist: {source_path}")

    (records_with_meta, parse_warnings, source_meta) = _read_source_records(source_path)

    # Build target records + attach deterministic record_id (from source line).
    target_records: list[dict[str, Any]] = []
    source_records: list[Any] = []
    for record, source_file, raw_line, lineno in records_with_meta:
        target = map_record(record)
        target["record_id"] = compute_record_id(raw_line)
        # Backfill record_id onto any field_warnings later.
        target_records.append(target)
        source_records.append(record)

    timestamp = datetime.now(timezone.utc).isoformat()

    summary = build_summary(
        source_records=source_records,
        target_records=target_records,
        source_meta=source_meta,
        parse_warnings=parse_warnings,
        source_path=source_path,
        dry_run=True,
        timestamp=timestamp,
    )

    # Render Markdown to stdout.
    md = render_markdown_report(summary, source_path=source_path)
    print(md)

    # Write JSON summary to out_path.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "dry-run complete: %d source records, %d migrated, %d quarantined, "
        "%d warnings → %s",
        summary["metrics"]["total_source_count"],
        summary["metrics"]["migrated_active"],
        summary["metrics"]["migrated_quarantined"],
        summary["metrics"]["conflict_count"]["mapping_warnings_count"],
        out_path,
    )
    return summary


# ── run_live_migration (v12+ path — gated) ──────────────────────────────


def run_live_migration(
    source_path: Path,
    out_path: Path,
    *,
    no_prompt: bool = False,
    stdin_input: Any = None,
) -> dict[str, Any]:
    """Execute live migration (writes to target + appends audit).

    v12+ operator workflow. For v11.0 PoC this path exists for test coverage
    but is NOT exercised by operators — see ``04-MIGRATION-PATH.md §4.7``.

    Confirmation prompt gates this path unless ``no_prompt=True``.

    Args:
        source_path: Source FeedbackStore root.
        out_path: Where to write the JSON summary.
        no_prompt: Skip confirmation prompt (for CI / scripting).
        stdin_input: Optional pre-filled stdin (testing only).

    Returns:
        The JSON summary dict.
    """
    # Confirmation gate (defense-in-depth).
    if not no_prompt:
        prompt = (
            f"Type '{CONFIRMATION_TOKEN}' to confirm live migration "
            f"(this will write to target + append audit): "
        )
        sys.stderr.write(prompt)
        sys.stderr.flush()
        if stdin_input is not None:
            response = stdin_input
        else:
            response = sys.stdin.readline().strip()
        if response != CONFIRMATION_TOKEN:
            sys.stderr.write(
                f"aborted: expected '{CONFIRMATION_TOKEN}', got {response!r}\n"
            )
            sys.exit(2)

    # Lazy import — avoid loading curator_audit at module load.
    from agent import curator_audit

    (records_with_meta, parse_warnings, source_meta) = _read_source_records(source_path)

    target_records: list[dict[str, Any]] = []
    source_records: list[Any] = []
    for record, source_file, raw_line, lineno in records_with_meta:
        target = map_record(record)
        target["record_id"] = compute_record_id(raw_line)
        target_records.append(target)
        source_records.append(record)

    timestamp = datetime.now(timezone.utc).isoformat()

    summary = build_summary(
        source_records=source_records,
        target_records=target_records,
        source_meta=source_meta,
        parse_warnings=parse_warnings,
        source_path=source_path,
        dry_run=False,
        timestamp=timestamp,
    )

    # Write target records (v11.0 PoC: JSON file target; v12+ writes to mem0).
    # NOTE: For v11.0 PoC, we write to a JSONL file under HERMES_HOME so the
    # test_apply_with_correct_confirmation_proceeds test can verify writes
    # happened. This is NOT mem0 — the real mem0 integration is v12+.
    from hermes_constants import get_hermes_home

    target_jsonl = get_hermes_home() / "memory" / "migrated_records.jsonl"
    target_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(target_jsonl, "a", encoding="utf-8") as f:
        for tr in target_records:
            f.write(json.dumps(tr, ensure_ascii=False) + "\n")

    # Append audit entry (T-55-15 mitigation).
    curator_audit.append_audit(
        action="auto_apply",
        patch_id=f"memory-migration-{timestamp}",
        skill_id="_migration",
        operator="system",
        eval_score={
            "migration": {
                "source_count": summary["metrics"]["total_source_count"],
                "target_count": len(target_records),
                "migrated_active": summary["metrics"]["migrated_active"],
                "migrated_quarantined": summary["metrics"]["migrated_quarantined"],
                "conflict_count": summary["metrics"]["conflict_count"],
            }
        },
    )

    # Render Markdown report.
    md = render_markdown_report(summary, source_path=source_path)
    print(md)

    # Write JSON summary.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


# ── argparse CLI ─────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser.

    Defaults to dry-run (EVAL-06 invariant). ``--dry-run`` and ``--apply``
    are mutually exclusive. ``--no-prompt`` only valid with ``--apply``.
    """
    parser = argparse.ArgumentParser(
        prog="migrate_v6_feedback_to_memory_schema",
        description=(
            "v6.0 FeedbackStore → v10.0 memory-record schema migration "
            "(EVAL-07 / P14 mitigation). Default mode is DRY-RUN (no writes)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/migrate_v6_feedback_to_memory_schema.py\n"
            "      (dry-run, default — produces report, zero writes)\n"
            "  python scripts/migrate_v6_feedback_to_memory_schema.py --dry-run\n"
            "      (explicit dry-run — identical to default)\n"
            "  python scripts/migrate_v6_feedback_to_memory_schema.py --apply\n"
            "      (live migration — prompts for confirmation; v12+ operator path)\n"
        ),
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help=(
            "Source FeedbackStore root (default: $HERMES_HOME/skills/.feedback). "
            "Must contain buckets/ + index.json."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(DEFAULT_OUT_PATH),
        help=f"JSON summary output path (default: {DEFAULT_OUT_PATH}).",
    )
    mode_group = parser.add_mutually_exclusive_group()
    # The default action when neither flag is present: dry-run.
    # argparse mutually-exclusive-group with no default = both absent is OK,
    # then main() decides. We use store_true on both and dispatch in main.
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        default=False,  # We don't use default=True because then --apply would
        # make both store_true and trigger the mutually-exclusive error.
        help="Dry-run mode (default). Produces report, zero writes.",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help=(
            "Live migration mode (gated by confirmation prompt; v12+ operator "
            "path). Writes to target + appends audit entry."
        ),
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        default=False,
        help=(
            "Skip confirmation prompt (only valid with --apply; use with care)."
        ),
    )
    return parser


def _resolve_source_path(cli_source: Path | None) -> Path:
    """Resolve the source FeedbackStore path.

    Args:
        cli_source: ``--source`` value, or None.

    Returns:
        Resolved Path. Defaults to ``$HERMES_HOME/skills/.feedback``.
    """
    if cli_source is not None:
        return cli_source.resolve()
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "skills" / ".feedback"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argv list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 success, non-zero error).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # EVAL-06 invariant: if NEITHER --dry-run NOR --apply is passed → dry-run.
    # If BOTH passed → argparse already errored (mutually exclusive group).
    if args.apply:
        mode = "apply"
    else:
        # Either --dry-run was explicit, or neither flag was passed.
        # Both cases → dry-run. (Default is dry-run-first.)
        mode = "dry-run"

    # --no-prompt validation.
    if args.no_prompt and mode != "apply":
        parser.error("--no-prompt requires --apply")

    source_path = _resolve_source_path(args.source)

    try:
        if mode == "dry-run":
            run_dry_run(source_path, args.out)
            return 0
        else:
            run_live_migration(source_path, args.out, no_prompt=args.no_prompt)
            return 0
    except FileNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\naborted by user\n")
        return 130


if __name__ == "__main__":
    sys.exit(main())
