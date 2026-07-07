# Phase 55: EVAL-HARNESS-2 - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped per autonomous smart-discuss rule)

<domain>
## Phase Boundary

Build second wave of PoC acceptance criteria per `05-POC-PLAN.md §4.4-§4.7`:

1. **EVAL-04 — Compaction Pass (1d):** Trigger compaction when `memory.max_records` threshold hit. Compaction = archive oldest archival-tier records + summarize working-tier into core-tier. Test: trigger compaction at exactly `max_records=500`, verify post-compaction state machine. NEW module `agent/memory_compaction.py`.
2. **EVAL-05 — Threshold Tuning (1d):** Document initial defaults + tuning path. Thresholds: `memory.max_records`, `confidence_threshold_for_promotion`, `evidence_chain_min_for_acceptance`. Initial defaults from v10.0 schemas; tuning path documented for v12.0 operators at `.planning/research/v11-poc-eval/threshold-tuning.md`.
3. **EVAL-06 — Dry-Run-First Invariant (1d):** Curator default `dry_run: true`. Schema migration default `dry_run: true`. Test: invoke both without explicit `dry_run: false` flag, verify no state mutation. Default value enforcement in `agent/curator.py` + `scripts/migrate_v6_feedback_to_memory_schema.py`.
4. **EVAL-07 — Schema Migration Dry-Run (2d):** v6.0 FeedbackStore JSONL → memory-record-schema migration script with `--dry-run` mode. Dry-run produces diff report without writing. P14 mitigation: zero silent drops. NEW script `scripts/migrate_v6_feedback_to_memory_schema.py` + `tests/v11-schema-migration/` fixtures + dry-run format spec.

**Hard dependencies:** Phase 54 fitness battery as regression-detection foundation (per `05-POC-PLAN.md §6.1`: fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD — bias canary done in 54, this phase completes remaining items).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation at Claude's discretion — pure infrastructure/test-fixtures/scripts phase.

**Authoritative design sources:**
- `05-POC-PLAN.md §4.4` (compaction) + §4.5 (threshold tuning) + §4.6 (dry-run-first) + §4.7 (schema migration)
- `agents-schema.yaml §2.6 memory_scope` + `memory-record-schema.yaml §3.8 status` (active/archived/quarantined/superseded)
- `agent/curator.py` existing `_memory_evolution_phase` (EVAL-06 default enforcement)
- `v6.0 FeedbackStore` schema (EVAL-07 source format — at `.planning/milestones/v6.0-phases/` if archived, or in agent/feedback_store.py)
- `04-MIGRATION-PATH.md §4.5` (EVAL-07 migration dry-run spec)

### Implementation-level open questions (Claude's discretion)

1. **Compaction trigger point:** Lazy (on next `memory_retrieve_scoped` call after threshold) OR eager (at `memory_submit_record` time). Recommend lazy — avoids write-path latency, fits existing pattern.
2. **Compaction summary approach:** LLM-based summarization of working-tier into core-tier (per design), OR deterministic merge. Recommend LLM with `auxiliary_client.call_llm(task="memory_compaction", provider="glm")`.
3. **Migration source location:** Find v6.0 FeedbackStore JSONL fixtures OR generate synthetic. Recommend synthetic fixture based on documented v6.0 schema (avoids dependency on archived data).
4. **Dry-run diff format:** JSON diff (machine-readable) + Markdown summary (human-readable). Documented at `.planning/research/v11-poc-eval/migration-dry-run-format.md`.
5. **Default enforcement pattern:** Per `04-MIGRATION-PATH.md §4.6` — function signature uses `dry_run: bool = True` (Python default). Plus explicit runtime check: if `dry_run` arg is None or missing, treat as True (defense-in-depth).

### Established patterns

- `from __future__ import annotations` + `encoding="utf-8"` + snake_case + `get_hermes_home()`
- Pytest fixtures + `@pytest.mark.asyncio` explicit
- `auxiliary_client.call_llm(task=..., provider="glm")` for LLM dispatch
- `agent/glm_concurrency_guard.acquire_glm_slot` for serial lock
- `utils.atomic_json_write` for state mutations
- `jsonschema.Draft202012Validator` for schema validation

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `agent/curator.py::run_curator_review` — existing entry point. EVAL-06 adds default `dry_run=True` enforcement.
- `agent/curator_audit.py` — sha256-chained audit log (v6.0 ship). Migration script + compaction append here.
- `agent/feedback_store.py` (v6.0 ship) — source format reference for EVAL-07.
- `agent/fitness_battery.py` (Phase 54) — regression-detection foundation.
- `agent/memory_arbitration.py` (Phase 53) — compaction interacts with memory records.
- `agent/curator_bias_canary.py` (Phase 54) — sister safety module.
- `auxiliary_client.call_llm` — GLM dispatch.
- `agent/glm_concurrency_guard.py` — serial lock.

### Integration Points

- `agent/memory_compaction.py` — NEW module
- `scripts/migrate_v6_feedback_to_memory_schema.py` — NEW script
- `.planning/research/v11-poc-eval/threshold-tuning.md` — NEW doc
- `.planning/research/v11-poc-eval/migration-dry-run-format.md` — NEW doc
- `tests/v11-compaction/` — NEW test dir (EVAL-04)
- `tests/v11-schema-migration/` — NEW test dir (EVAL-07)
- `agent/curator.py` — modified (EVAL-06 dry_run=True default)
- `cli-config.yaml.example` — add `auxiliary.memory_compaction` task with `provider: glm`

</code_context>

<specifics>
## Specific Ideas

The 4 SCs (per ROADMAP §Phase 55) are the authoritative acceptance contract:

- **SC#1 (EVAL-04):** `agent/memory_compaction.py` exists. Test triggers compaction at exactly `max_records=500`, verifies post-compaction state (archival-tier archived, working-tier summarized into core-tier).
- **SC#2 (EVAL-05):** `.planning/research/v11-poc-eval/threshold-tuning.md` documents initial defaults + tuning methodology for the 3 thresholds.
- **SC#3 (EVAL-06):** Default invocation of `agent/curator.py::_memory_evolution_phase` AND `scripts/migrate_v6_feedback_to_memory_schema.py` without explicit `dry_run: false` produces zero state mutation.
- **SC#4 (EVAL-07):** `scripts/migrate_v6_feedback_to_memory_schema.py` exists with `--dry-run` flag. `tests/v11-schema-migration/` has fixtures. Dry-run output format spec at `.planning/research/v11-poc-eval/migration-dry-run-format.md`. P14 mitigation: zero silent drops (every source record accounted for).

</specifics>

<deferred>
## Deferred Ideas

- **Live production traffic** — v12+ per REQUIREMENTS.md.
- **Threshold tuning with production data** — v12+ (v11.0 documents defaults only).
- **Migration cutover execution** — v12+ (v11.0 ships dry-run mode only).
- **15-expert full transform** — v12+ (only 9 sample in v11.0).

</deferred>
