---
phase: 55-eval-harness-2
plan: 04
subsystem: eval-harness
tags: [eval, schema-migration, p14-mitigation, dry-run, feedbackstore, memory-record-schema]
requires:
  - 55-03 (dry-run-first invariant pattern)
  - agent/feedback_schema.py (source schema — FeedbackRecord)
  - agent/feedback_store.py (v6.0 FeedbackStore filesystem layout)
  - agent/curator_audit.py (sha256-chained audit log for --apply mode)
  - .planning/research/v10-orchestrator-design/memory-record-schema.yaml (target schema)
provides:
  - scripts/migrate_v6_feedback_to_memory_schema.py (CLI with --dry-run default)
  - tests/v11-schema-migration/ (52 tests, 30-record fixture, 3 test files)
  - .planning/research/v11-poc-eval/migration-dry-run-format.md (format spec)
affects:
  - P14 mitigation satisfied (zero silent drops + safe defaults)
  - EVAL-07 acceptance (dry-run output plan correct on synthetic input)
  - EVAL-06 invariant extends to migration script (dry_run=True default)
tech-stack:
  added: []
  patterns:
    - dry-run-first invariant (pattern from 55-03, applied to migration script)
    - deterministic UUIDv5 record_id (reproducible dry-run reports)
    - subprocess test invocation (matches operator CLI pattern)
    - filesystem-based audit verification (subprocess can't be monkeypatched)
key-files:
  created:
    - scripts/migrate_v6_feedback_to_memory_schema.py
    - tests/v11-schema-migration/__init__.py
    - tests/v11-schema-migration/conftest.py
    - tests/v11-schema-migration/test_field_mapping.py
    - tests/v11-schema-migration/test_dry_run_zero_writes.py
    - tests/v11-schema-migration/test_zero_silent_drops.py
    - tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/buckets/screenplay/cli.jsonl
    - tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/buckets/screenplay/kais_aigc.jsonl
    - tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/buckets/cinematographer/manual.jsonl
    - tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/index.json
    - .planning/research/v11-poc-eval/migration-dry-run-format.md
  modified: []
decisions:
  - "Verdict mapping follows CODE (good/needs_work/bad), NOT doc (positive/negative/neutral). Divergence documented in migration-dry-run-format.md §2."
  - "record_id = uuid.uuid5(NAMESPACE_OID, sha256(source_line)) — deterministic UUIDv5 for reproducible dry-run reports (NOT random UUIDv4)."
  - "Subprocess test invocation pattern (not direct Python import) — matches operator CLI pattern and catches sys.exit / stdout buffering correctly. Requires filesystem-based audit verification (subprocess can't be monkeypatched)."
  - "Content defaults to '<no feedback text>' placeholder (NOT empty string) when correction is empty + no revised_output. Generates mapping warning."
  - "persona_sha256 defaults to '0'×64 zero-hash when agent YAML persona not found (every record in fixture triggers this — no agent YAMLs present in test env). Generates mapping warning."
  - "Live migration (--apply) writes to JSONL file target under HERMES_HOME/memory/migrated_records.jsonl (NOT mem0 directly — that's v12+)."
metrics:
  duration: 641s (~11 min)
  completed: 2026-07-07T10:48:00Z
  tasks_total: 3
  tasks_completed: 3
  files_created: 11
  files_modified: 0
  tests_added: 52
  tests_passing: 52
  lines_added: 2229
---

# Phase 55 Plan 04: EVAL-07 Schema Migration Dry-Run Summary

Built the v6.0 FeedbackStore → v10.0 memory-record schema migration script with `--dry-run` default mode (EVAL-06 invariant). Dry-run produces a 5-metric diff report without writing to mem0. Every source FeedbackRecord appears in dry-run output (zero silent drops — P14 mitigation). Deterministic UUIDv5 record_ids make reports reproducible across runs.

## What Was Built

**Migration script (`scripts/migrate_v6_feedback_to_memory_schema.py`, 952 lines):**
- CLI with `--dry-run` (default), `--apply`, `--source`, `--out`, `--no-prompt` flags.
- Mutually exclusive `--dry-run` / `--apply` group; if neither passed → dry-run (EVAL-06 invariant).
- `run_dry_run()` — primary v11.0 PoC path. Read-only on source. Writes Markdown report to stdout + JSON summary to `--out` file. Zero `append_audit` calls.
- `run_live_migration()` — v12+ operator path. Gated by `Type 'apply' to confirm:` prompt (or `--no-prompt`). Writes target records to JSONL + appends `auto_apply` audit entry.
- `map_record()` — pure function implementing Phase 49 §4.3 17-row mapping table. Unit-test surface.
- `apply_safe_defaults()` — 6 safe-default rules from §4.6 (confidentiality=confidential, scope=project, confidence=0.5, half_life_days=180, expires_at=created_at+180d, verified_at=created_at).
- `compute_record_id()` — deterministic UUIDv5 from `sha256(source_line)` for reproducible reports.
- `compute_metrics()` — pure function producing 5 §4.5 metrics + 3 migration-tracking bonus metrics (migrated_active, migrated_quarantined, dropped_or_failed).

**Test suite (`tests/v11-schema-migration/`, 52 tests):**
- `test_field_mapping.py` (27 tests) — per-field mapping for §4.3 table: skill_id→agent_id, verdict→status (good/needs_work→active, bad→quarantined), ts→created_at, evidence_chain construction, content derivation, all safe defaults, record_id UUIDv5 determinism.
- `test_dry_run_zero_writes.py` (10 tests) — default mode is dry-run, explicit `--dry-run` identical to default, zero audit calls in dry-run (verified via filesystem), source unchanged (bytes + mtimes), `--apply` requires confirmation, `--apply --no-prompt` skips confirmation, mutually exclusive args error, unknown source path errors.
- `test_zero_silent_drops.py` (15 tests) — 30 records all accounted, no duplicate record_ids, valid UUIDs, all 5 metric keys present, migrated_active==21, migrated_quarantined==9, dropped_or_failed==0, deterministic across runs, malformed lines logged not dropped.

**Fixture (`tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/`, 30 records):**
- 3 buckets: `screenplay/cli.jsonl` (12 records), `screenplay/kais_aigc.jsonl` (8 records), `cinematographer/manual.jsonl` (10 records).
- Breakdown: 10 good + 11 needs_work + 9 bad.
- Edge cases: empty correction + verdict=bad (ambiguous → mapping warning), Chinese text in correction (UTF-8 round-trip), >1KB prompt (large record).
- `index.json` mirrors v6.0 layout.

**Format spec (`.planning/research/v11-poc-eval/migration-dry-run-format.md`, 346 lines):**
- §1 Purpose + Scope (P14 mitigation).
- §2 Source vs Target Schema Summary + **verdict divergence documented** (code good/needs_work/bad vs doc positive/negative/neutral — code is authoritative).
- §3 Dry-Run Output Format — Markdown report + JSON summary shapes.
- §4 Zero Silent Drops Guarantee (P14 mitigation).
- §5 Safe Defaults (6 rules from §4.6 + 6 additional).
- §6 v11.0 PoC Acceptance (4 checks).
- §7 Implementation Contract (CLI shape, read-only enforcement, no LLM dispatch, audit log gating).
- §8 Change Log.

## TDD Gate Compliance

Plan `type: execute` (not `type: tdd`), but Task 2 was marked `tdd="true"`. Gate sequence followed:

1. **RED** commit `8174e8edb` — fixture + 3 test files. Tests failed at module load (script not implemented).
2. **GREEN** commit `6faaeabdb` — script implementation + test fixes. All 52 tests pass.

Commit prefix convention followed (`test(...)` for RED, `feat(...)` for GREEN).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Test fixture sha256 values were not 64-hex**
- **Found during:** Task 3 (initial fixture authoring)
- **Issue:** Hand-crafted sha256 strings were not all exactly 64 hex characters, causing Pydantic validation failures.
- **Fix:** Regenerated the entire fixture programmatically using `hashlib.sha256(f"record-{idx:02d}-{skill_id}".encode()).hexdigest()` to guarantee valid 64-hex values.
- **Files modified:** 3 fixture `.jsonl` files + `index.json` (regenerated to match).
- **Commit:** `8174e8edb` (fixture committed in regenerated form).

**2. [Rule 3 - Blocking] mock_audit_chain fixture couldn't intercept subprocess calls**
- **Found during:** Task 2 (test execution)
- **Issue:** The `mock_audit_chain` fixture monkeypatches `agent.curator_audit.append_audit` in the parent test process, but the migration script runs in a subprocess — the monkeypatch doesn't apply across process boundaries.
- **Fix:** Rewrote `test_dry_run_zero_audit_calls`, `test_apply_with_correct_confirmation_proceeds`, and `test_apply_no_prompt_skips_confirmation` to verify audit log state via the filesystem (`$HERMES_HOME/skills/.audit/log.jsonl`).
- **Files modified:** `tests/v11-schema-migration/test_dry_run_zero_writes.py`.
- **Commit:** `6faaeabdb`.

### Not Deviations (Per-Plan Decisions Documented in Frontmatter)

These were per-plan decisions (Claude's discretion per 55-CONTEXT.md), not deviations:
- Verdict mapping uses CODE (`good/needs_work/bad`), NOT doc — explicitly required by plan critical_reminders + done criteria.
- record_id uses UUIDv5 (deterministic) — explicitly specified in plan §4.1 of doc.
- Live migration writes to JSONL file (not mem0) — per plan note "v11.0 PoC writes to a JSON file target, not mem0 directly" (format spec §6).

## Auth Gates

None — script performs deterministic field mapping, no LLM dispatch, no external API calls.

## Known Stubs

None. Allotment of "deferred to v12+" work is per-plan (live migration operator workflow, mem0 backend integration, 30-day shadow-run canary) — not stubs.

## Threat Flags

None. Threat register (T-55-11 through T-55-15, T-55-SC) from the plan is fully mitigated:

| Threat | Mitigation | Test |
|--------|------------|------|
| T-55-11 (Tampering — source mutation) | Script opens source read-only (`"r"` mode) | `test_source_files_unchanged_after_dry_run` + `test_source_files_mtimes_unchanged_after_dry_run` |
| T-55-12 (Info Disclosure — unsafe default) | 6 safe-default rules from §4.6 | `test_default_confidentiality_is_confidential` + 10 other safe-default tests |
| T-55-13 (DoS — silent drop) | `source_record_ids_accounted` array in JSON summary | `test_30_records_all_accounted` + `test_malformed_line_logged_not_dropped` |
| T-55-14 (EoP — dry-run bypass) | `dry_run: bool = True` default (EVAL-06 invariant) | `test_dry_run_zero_audit_calls` |
| T-55-15 (Repudiation — no audit) | `--apply` mode appends `auto_apply` audit entry | `test_apply_with_correct_confirmation_proceeds` |
| T-55-SC (Tampering — packages) | Zero packages installed | accept |

## Self-Check: PASSED

**Files created (verified to exist):**
- `scripts/migrate_v6_feedback_to_memory_schema.py` — FOUND
- `tests/v11-schema-migration/__init__.py` — FOUND
- `tests/v11-schema-migration/conftest.py` — FOUND
- `tests/v11-schema-migration/test_field_mapping.py` — FOUND
- `tests/v11-schema-migration/test_dry_run_zero_writes.py` — FOUND
- `tests/v11-schema-migration/test_zero_silent_drops.py` — FOUND
- `tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/buckets/screenplay/cli.jsonl` — FOUND
- `tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/buckets/screenplay/kais_aigc.jsonl` — FOUND
- `tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/buckets/cinematographer/manual.jsonl` — FOUND
- `tests/v11-schema-migration/fixtures/sample_v6_feedbackstore/index.json` — FOUND
- `.planning/research/v11-poc-eval/migration-dry-run-format.md` — FOUND

**Commits (verified in git log):**
- `f705f91d0` — `docs(55-04): migration dry-run format spec` — FOUND
- `8174e8edb` — `test(55-04): add failing EVAL-07 schema migration tests (RED)` — FOUND
- `6faaeabdb` — `feat(55-04): implement EVAL-07 schema migration script (GREEN)` — FOUND

**Test suite:** 52/52 passing (`pytest tests/v11-schema-migration/ -x`).

**Plan verification (5 checks):**
1. Script exists with `--dry-run` flag — PASS.
2. Fixtures exist (3 buckets × ~10 records = 30 records) — PASS.
3. Dry-run produces diff report without writing (exit 0 + JSON report + `dry_run: true` + zero audit log file) — PASS.
4. Zero silent drops (`len(source_record_ids_accounted) == total_source_count == 30`) — PASS.
5. Format spec exists with all 5 metrics + zero-silent-drops + safe defaults — PASS.
