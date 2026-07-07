# Migration Dry-Run Output Format Spec (v11.0 PoC)

**Status:** AUTHORITATIVE — Task 2's `scripts/migrate_v6_feedback_to_memory_schema.py` implements this spec; Task 3's `tests/v11-schema-migration/` verifies against it.
**Scope:** v11.0 PoC (EVAL-07). Live migration (`--apply`) path is OUT OF SCOPE for v11.0 PoC operators per `04-MIGRATION-PATH.md §4.7 Step 4` (deferred to v12+).
**Authors:** Phase 55 Plan 04 (EVAL-07).
**Related:** `04-MIGRATION-PATH.md §4.3` (17-row mapping table), `§4.5` (5-metric plan), `§4.6` (6 safe defaults), `05-POC-PLAN.md §4.7` (acceptance contract).

---

## §1 — Purpose + Scope

**P14 mitigation:** "Schema Migration Breaks Memory Store — silent drop or unsafe default pollution of memory store" (per PITFALLS risk register: severity MEDIUM, PoC-acceptable deferral = NO — must ship with v11.0).

This spec defines the **dry-run output format** for `scripts/migrate_v6_feedback_to_memory_schema.py` — the operator-facing "preview before apply" report that proves the v6.0 → v10.0 schema migration is safe before any write touches the mem0 backend.

**In scope (v11.0 PoC):**
- Deterministic field mapping from v6.0 `FeedbackRecord` → v10.0 `memory-record` (no LLM dispatch).
- 5-metric diff report (Markdown human-readable + JSON machine-readable).
- Zero silent drops invariant — every source record appears in dry-run output.
- Safe-default-on-unknown-field (6 rules from `04-MIGRATION-PATH.md §4.6`).

**Out of scope (v12+):**
- Live migration (`--apply`) operator workflow.
- 30-day shadow-run discrepancy canary.
- Production traffic cutover.

---

## §2 — Source vs Target Schema Summary

### Source: v6.0 FeedbackRecord (`agent/feedback_schema.py:184`)

8 fields (Pydantic v2 model):

| Field | Type | Notes |
|-------|------|-------|
| `skill_id` | `str` | Validated against `_KNOWN_EXPERT_IDS` auto-discovered from `skills/movie-experts/*/SKILL.md`. |
| `expert_id` | `str` | Same as `skill_id` for movie-experts (kept separate for future-proofing). |
| `source` | `Literal["cli", "kais_aigc", "manual"]` | Provenance — cli slash cmd, kais_aigc inbox, manual JSONL. |
| `verdict` | `Literal["good", "needs_work", "bad"]` | Qualitative rating. **DIVERGENCE — see below.** |
| `correction` | `str = ""` | Free-text operator feedback. |
| `revised_output` | `str \| None = None` | Optional full replacement output. |
| `output_snapshot` | `OutputSnapshot` | Provenance of LLM output (sha256, output_text, prompt, model, provider, ...). |
| `ts` | `datetime` | Timezone-aware ISO-8601. |

**Filesystem layout** (`agent/feedback_store.py:199`):
```
~/.hermes/skills/.feedback/
├── buckets/<skill_id>/<source>.jsonl   # append-only, one FeedbackRecord per line
├── dedup/sha256-registry.jsonl          # audit log of supersession events
└── index.json                            # _INDEX_VERSION = 1
```

### Target: v10.0 memory-record (`memory-record-schema.yaml`)

10 mandated fields (`required`) + 10 optional fields:

| Field | Required | Type |
|-------|----------|------|
| `record_id` | YES | UUID string |
| `agent_id` | YES | `^[a-z0-9_-]+$` |
| `scope` | YES | `global \| project \| session` |
| `status` | YES | `active \| archived \| quarantined \| superseded` |
| `confidence` | YES | `float 0.0-1.0` |
| `evidence_chain` | YES | `list (≥3 per P5)` |
| `created_at` | YES | ISO-8601 |
| `persona_sha256` | YES | `^[a-f0-9]{64}$` |
| `schema_version` | YES (default) | `^[0-9]+\.[0-9]+\.[0-9]+$` |
| `content` | YES (default) | string |
| `project_id`, `session_id`, `expires_at`, `verified_at`, `supersedes_memory_id`, `evidence_operator_ids`, `half_life_days`, `last_recalled_at`, `recall_count`, `confidentiality` | optional | see schema |

### Verdict Divergence: Document vs Code

> **DIVERGENCE — documented for traceability.** The Phase 49 doc `04-MIGRATION-PATH.md §4.1` documents the source `FeedbackRecord.verdict` enum as `positive | negative | neutral`. The ACTUAL code in `agent/feedback_schema.py:206` defines the enum as `good | needs_work | bad`.
>
> **The CODE is authoritative.** This migration script follows the code. The mapping table below uses `good | needs_work | bad`.

| Doc says | Code says | Migration mapping |
|----------|-----------|-------------------|
| `positive` | `good` | `status="active"` |
| `negative` | `bad` | `status="quarantined"` (P14 mitigation — never auto-activate) |
| `neutral` | `needs_work` | `status="active"` (informational, not blocking) |

The `04-MIGRATION-PATH.md §4.1` doc must be updated to match code in a future doc-revision pass (out of scope for v11.0 PoC — flagged here for traceability).

---

## §3 — Dry-Run Output Format (5 metrics)

The script emits BOTH a human-readable Markdown report (stdout) AND a machine-readable JSON summary (file at `--out` path). The JSON summary is the contract tests verify against.

### 3.1 Markdown Report (stdout, human-readable)

```
═══════════════════════════════════════════════════════════════
  v6.0 FeedbackStore → v10.0 memory-record Migration Dry-Run
═══════════════════════════════════════════════════════════════
Source: ~/.hermes/skills/.feedback/  (index_version=1)
Target schema: memory-record-schema.yaml v1.0.0
Mode: DRY-RUN (no writes will occur)
Timestamp: 2026-07-07T...

(a) Total source records: 30 FeedbackRecord lines across 3 buckets
    Breakdown by agent_id:
      screenplay:      20 (66.7%)
        └─ cli:         12 (4 good, 4 needs_work, 4 bad)
        └─ kais_aigc:    8 (3 good, 3 needs_work, 2 bad)
      cinematographer: 10 (33.3%)
        └─ manual:      10 (3 good, 4 needs_work, 3 bad)

(b) Per-target-field default fill rate:
    record_id:         100% generated (UUIDv5 from source content hash)
    agent_id:          100% source-derived (skill_id verbatim)
    status:            100% source-derived (verdict→status mapping)
    scope:               0% source-derived — 100% default ("project")
    confidence:          0% source-derived — 100% default (0.5, OQ-4 neutral)
    evidence_chain:    100% constructed from source (length=1, below P5 ≥3 threshold)
    created_at:        100% source-derived (ts verbatim)
    persona_sha256:      0% source-derived — 100% default (0×64 zero-hash)
    schema_version:      0% source-derived — 100% default ("1.0.0")
    content:            96% source-derived (correction or revised_output) — 4% default ("<no feedback text>")
    confidentiality:     0% source-derived — 100% default ("confidential" P14 mitigation 2)
    half_life_days:      0% source-derived — 100% default (180)

(c) Conflict count:
    quarantined (verdict=bad → status=quarantined): 9 records
    evidence_chain below P5 ≥3 threshold:          30 records (all — single-source migration)
    mapping warnings:                               2 records

(d) Estimated target storage: ~48 KB after migration
    Source size: 27 KB (30 lines × ~900 B avg)
    Target size: ~48 KB (1.8× source — added fields account for 80% of growth)

(e) Mapping warnings:
    WARNING: line 7 in buckets/screenplay/cli.jsonl — empty correction with verdict=bad
             (ambiguous — content defaults to "<no feedback text>")
    WARNING: line 14 in buckets/cinematographer/manual.jsonl — output_snapshot.prompt > 1KB
             (large record — verify mem0 size limit before --apply)

═══════════════════════════════════════════════════════════════
  NO WRITE OCCURRED. To apply: python scripts/migrate_v6_feedback_to_memory_schema.py --apply
  (Live migration is OUT OF SCOPE for v11.0 PoC — see 04-MIGRATION-PATH.md §4.7 Step 4)
═══════════════════════════════════════════════════════════════
```

### 3.2 JSON Summary (file at `--out` path, machine-readable)

This is the contract tests verify against. Shape:

```json
{
  "source": {
    "path": "~/.hermes/skills/.feedback/",
    "index_version": 1,
    "total_records": 30,
    "bucket_breakdown": {
      "screenplay": {"cli": 12, "kais_aigc": 8},
      "cinematographer": {"manual": 10}
    }
  },
  "target": {
    "schema_version": "1.0.0",
    "estimated_storage_bytes": 49152
  },
  "metrics": {
    "total_source_count": 30,
    "migrated_active": 21,
    "migrated_quarantined": 9,
    "dropped_or_failed": 0,
    "malformed_lines": 0,
    "per_field_default_fill_rate": {
      "record_id": 0.0,
      "agent_id": 1.0,
      "status": 1.0,
      "scope": 0.0,
      "confidence": 0.0,
      "evidence_chain": 0.0,
      "created_at": 1.0,
      "persona_sha256": 0.0,
      "schema_version": 0.0,
      "content": 0.96,
      "confidentiality": 0.0,
      "half_life_days": 0.0
    },
    "conflict_count": {
      "quarantined_verdict_bad": 9,
      "evidence_chain_below_min": 30,
      "mapping_warnings_count": 2
    },
    "estimated_target_storage_mb": 0.048,
    "mapping_warnings": [
      {
        "record_id": "<uuid>",
        "source_file": "buckets/screenplay/cli.jsonl",
        "line": 7,
        "field": "content",
        "warning": "empty correction with verdict=bad — content defaults to '<no feedback text>'"
      }
    ]
  },
  "source_record_ids_accounted": [
    "<uuid>", "<uuid>", "... (one per source record — 30 total)"
  ],
  "dry_run": true,
  "timestamp": "2026-07-07T10:37:22Z"
}
```

### 3.3 Five Required Metrics Keys

Tests assert presence of these 5 keys under `metrics`:

1. `total_source_count` (int) — count of valid FeedbackRecord lines parsed.
2. `per_field_default_fill_rate` (dict[str, float]) — fraction of records where each target field was source-derived vs default-backed.
3. `conflict_count` (dict) — counts of records routed to `quarantined` + records with mapping warnings + records below evidence threshold.
4. `estimated_target_storage_mb` (float) — sum of target record sizes / 1MB.
5. `mapping_warnings` (list[dict]) — per-record warnings (record_id, source_file, line, field, warning).

**Bonus migration-tracking metrics** (not part of the original 5, but required by `05-POC-PLAN.md §4.7` acceptance check):

- `migrated_active` (int) — records mapped to `status="active"` (verdict=good or needs_work).
- `migrated_quarantined` (int) — records mapped to `status="quarantined"` (verdict=bad).
- `dropped_or_failed` (int) — records that could not be mapped at all (should ALWAYS be 0 for the dry-run on valid fixtures — P14 mitigation: zero silent drops means we account for every record, even malformed ones get logged to mapping_warnings not dropped).

---

## §4 — Zero Silent Drops Guarantee (P14 mitigation)

**Invariant:** Every source `FeedbackRecord` line (valid OR malformed) appears in the dry-run output.

### 4.1 Deterministic record_id (UUIDv5)

For each parsed source line, the migration script computes a deterministic `record_id`:

```python
import hashlib, uuid
record_id = str(uuid.uuid5(
    uuid.NAMESPACE_OID,
    hashlib.sha256(source_line_bytes).hexdigest(),
))
```

**Rationale:** UUIDv5 (namespace + name) is deterministic — re-running the dry-run on the same source produces identical `record_id`s, so the diff report is reproducible. This contrasts with UUIDv4 (random) which would change on every run.

**Property test:** `test_record_id_uuid5_deterministic` runs the dry-run twice on the same fixture and asserts `source_record_ids_accounted` arrays are byte-identical.

### 4.2 The `source_record_ids_accounted` array

The JSON summary MUST contain a top-level `source_record_ids_accounted: list[str]` with one entry per valid source record. Tests assert:

```python
assert len(summary["source_record_ids_accounted"]) == summary["metrics"]["total_source_count"]
```

### 4.3 Malformed lines — logged, not dropped

If a source JSONL line fails Pydantic validation (corrupt JSON, missing required field, etc.), the script:

1. Does NOT crash.
2. Appends an entry to `metrics.mapping_warnings` with `field="_parse"`, `warning=<error message>`, `source_file`, `line=<lineno>`.
3. Increments `metrics.malformed_lines` counter.
4. Does NOT add to `source_record_ids_accounted` (no record_id can be computed for an unparseable line — but the warning entry preserves the line number so the operator can find + repair it).

This means `total_source_count + malformed_lines == total lines read from source`. The P14 mitigation is satisfied: every source line is accounted for, either as a migrated record or as a logged warning.

---

## §5 — Safe Defaults (P14 mitigation 2)

Six safe-default-on-unknown-field rules from `04-MIGRATION-PATH.md §4.6`. Applied by `apply_safe_defaults()` for every target field with no source-side equivalent:

| # | Field | Default value | Rationale |
|---|-------|---------------|-----------|
| 1 | `confidentiality` | `"confidential"` | P14 mitigation 2 — **safest not most permissive**. Never `"public"` by default. |
| 2 | `scope` | `"project"` | P14 mitigation 2 — tightest scope. Can promote to `"global"` later via curator. |
| 3 | `status` (when verdict mapping fails) | `"archived"` | P14 mitigation 2 — fail-safe to non-active. Never `"active"` by default. (In practice the verdict enum is constrained so this branch only fires on schema drift.) |
| 4 | `confidence` | `0.5` | OQ-4 neutral baseline. (Note: 04-MIGRATION-PATH §4.6 mentions 0.3 for ambiguous cases — v11.0 PoC uses 0.5 uniformly per OQ-4; the 0.3 lower bound activates only for curator-flagged ambiguous post-migration records, not for migration-time defaults.) |
| 5 | `half_life_days` | `180` | Conservative — expire sooner rather than later (mirrors `DEFAULT_DECAY_WINDOW_DAYS` in `feedback_store.py:56`). |
| 6 | `expires_at` | `created_at + 180 days` | Matches `half_life_days`. Hard expiry forces re-verification. |

**Additional defaults** (not in §4.6's six but required by target schema):

| Field | Default | Notes |
|-------|---------|-------|
| `schema_version` | `"1.0.0"` | v10.0 baseline. |
| `persona_sha256` | `"0" × 64` (zero-hash) | Computed from agent YAML persona if available; zero-hash + mapping warning if YAML not found. |
| `verified_at` | `created_at` | Legacy records treated as verified at creation. |
| `supersedes_memory_id` | `null` | No prior record at migration time. |
| `project_id` | `"unknown"` | From bucket path if encoded; else default. Never null (P14 — always trackable). |
| `session_id` | `null` | No session context at feedback-record time. |

---

## §6 — v11.0 PoC Acceptance (cite `05-POC-PLAN.md §4.7`)

**Acceptance check** (operator + automated):

1. **Dry-run output plan correct on synthetic input.** Run `python scripts/migrate_v6_feedback_to_memory_schema.py --source tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/` — verify exit code 0 + JSON summary written + 5 metrics fields present + reasonable values.
2. **Zero silent drops.** `len(source_record_ids_accounted) == metrics.total_source_count == 30` for the 30-record fixture.
3. **Manual spot-check 5 random records.** Pick 5 `record_id`s from `source_record_ids_accounted`, inspect their mapped target records — does the mapping make sense? (verdict=bad → quarantined, content populated from correction, etc.)
4. **Default mode is dry-run.** Running with no args produces `"dry_run": true` in JSON summary + zero `append_audit` calls.

**Out of scope for v11.0 PoC** (deferred to v12+ per REQUIREMENTS.md):

- Live migration execution (`--apply` operator workflow).
- 30-day shadow-run discrepancy canary (< 1% drift acceptance).
- Production traffic cutover.
- mem0 backend integration (v11.0 PoC writes to a JSON file target, not mem0 directly).

---

## §7 — Implementation Contract (for Task 2 + Task 3)

This section is the binding contract between this spec (Task 1), the script (Task 2), and the tests (Task 3).

### 7.1 Script CLI

```
python scripts/migrate_v6_feedback_to_memory_schema.py [--source PATH] [--out PATH] [--dry-run | --apply] [--no-prompt]
```

- Default mode (no flags): **dry-run** (EVAL-06 invariant).
- `--dry-run`: explicit dry-run (identical to default).
- `--apply`: live migration (gated by confirmation prompt unless `--no-prompt`).
- `--source`: source FeedbackStore path (default: `$HERMES_HOME/skills/.feedback`).
- `--out`: JSON summary output path (default: `./migration-dryrun-report.json`).

### 7.2 Read-only enforcement (T-55-11)

Script opens all source files in `"r"` mode with `encoding="utf-8"`. Never `"w"`, `"a"`, or `"r+"` on source. The source `dedup/sha256-registry.jsonl` audit log is NEVER appended to in dry-run mode.

### 7.3 LLM dispatch — NONE

This script performs **deterministic field mapping only**. No `auxiliary_client.call_llm` calls. (The curator compaction path in 55-01 uses GLM dispatch; the schema migration path does not — divergence documented here for clarity.)

### 7.4 Audit log entries — ONLY in `--apply` mode

`curator_audit.append_audit(action="auto_apply", patch_id="memory-migration-{ts}", skill_id="_migration", eval_score={...})` is called ONLY in `run_live_migration()`. Dry-run mode MUST NOT call `append_audit` (T-55-14 mitigation).

---

## §8 — Change Log

| Date | Change |
|------|--------|
| 2026-07-07 | Initial authoring (Phase 55 Plan 04 / EVAL-07). |
