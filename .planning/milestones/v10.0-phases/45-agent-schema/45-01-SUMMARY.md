---
phase: 45-agent-schema
plan: 01
subsystem: v10-orchestrator-design
tags: [v10.0, design-doc, agent-schema, memory-record, json-schema, 2-layer, per-agent-memory, curator-evolution]
requires:
  - 00-FIRST-PRINCIPLES.md (Phase 44 root argument — 决策 5 + 决策 6 anchors)
  - ARCHITECTURE.md §1.1 (18-field source) + §2 (15-expert table) + §3.4 (curator phase source)
  - PITFALLS.md §P1/P2/P4/P5/P8/P10/P14 (load-bearing field-level mitigation source)
  - SUMMARY.md CC-2 (2-layer schema mandate) + OQ-1/4/7/13/14/16
provides:
  - 01-AGENT-REGISTRY-SCHEMA.md (design narrative, 1289 lines)
  - agents-schema.yaml (JSON Schema Draft 2020-12, 18 fields + $defs)
  - memory-record-schema.yaml (independent JSON Schema, 10 mandated fields + persona_sha256 + schema_version)
  - Physical carrier for 02/04/05/06 downstream design docs field references
affects:
  - 02-ROUND-TABLE-PROTOCOL.md (consumes memory_scope + scope + confidentiality + memory tier)
  - 04-MIGRATION-PATH.md (consumes lineage + default_invocation + transform table + schema_version)
  - 05-POC-PLAN.md (consumes compaction triggers + dry-run contract + pitfall audit)
  - 06-CROSS-REPO-IMPACT.md (consumes memory_scope + scope + schema_version + contextvars pattern)
  - 51 VALIDATE-02 lint (consumes entire schema as machine-checkable inputs)
tech-stack:
  added: []
  patterns:
    - JSON Schema Draft 2020-12 (machine-readable schema, additionalProperties: false)
    - 2-layer schema split (CC-2 mandate — agent-profile YAML vs memory-record schema)
    - Per-agent memory 3-tier (core/working/archival, max_records=500 aggregate)
    - Curator additive phase pattern (v6.0 _feedback_scan_phase → v10.0 _memory_evolution_phase)
    - persona_sha256 cross-layer invariant (agent YAML + evolution_log entry + memory record)
key-files:
  created:
    - .planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md
    - .planning/research/v10-orchestrator-design/agents-schema.yaml
    - .planning/research/v10-orchestrator-design/memory-record-schema.yaml
  modified: []
decisions:
  - 18-field agent YAML schema locked at ROADMAP level (SC#1); any field add/remove requires milestone-level decision
  - 2-layer schema split mandated by CC-2 (agent-profile 18f vs memory-record 10f) — cannot collapse to single layer
  - Per-agent memory 3-tier with max_records=500 aggregate (core 50 + working 200 + archival 250, resolves OQ-7)
  - Curator _memory_evolution_phase modeled on v6.0 _feedback_scan_phase (additive, AFTER, dry-run, try/except, resolves OQ-16)
  - persona_sha256 cross-layer invariant (3 locations: agent YAML registration + every evolution_log entry + every memory record) for P1 drift detection
  - P10 partial defer — confidentiality restricted tier + PII vault deferred to v11.1; public/internal/confidential ships in v11.0 PoC
metrics:
  duration: ~45min
  completed: 2026-07-06
  tasks_completed: 5
  tasks_total: 5
  files_created: 3
  files_modified: 0
  lines_written: 2300  # 1289 (narrative) + ~580 (agents-schema.yaml) + ~430 (memory-record-schema.yaml)
---

# Phase 45 Plan 01: Agent Registry Schema Summary

**One-liner:** Locked v10.0 2-layer schema — 18-field agent-profile YAML (JSON Schema Draft 2020-12) + independent 10-field memory-record schema — encoding 7 load-bearing pitfall mitigations at field level and resolving all 6 OQs, serving as the physical carrier for all 4 downstream v10.0 design docs.

## Deliverables

### 3 Files Created

| File | Lines | Role |
|------|-------|------|
| `01-AGENT-REGISTRY-SCHEMA.md` | 1289 | Design narrative (§0-§8): schema philosophy + 18-field per-field deep dive + memory-record narrative + 3-tier memory + curator phase contract + 15-expert table + OQ/pitfall audit + downstream citation |
| `agents-schema.yaml` | ~580 | JSON Schema Draft 2020-12, 18 fields + `$defs` (Lineage / Prerequisites / EvolutionLogEntry), `additionalProperties: false` enforces SC#1 lock |
| `memory-record-schema.yaml` | ~430 | INDEPENDENT JSON Schema Draft 2020-12 (not sub-schema), 10 mandated fields + `persona_sha256` (OQ-1) + `schema_version` (P14) + audit fields |

### 18-Field Agent YAML Schema Lock Status

All 18 fields locked (SC#1 ROADMAP-level). 7 required, 11 optional-with-default. Each field has traceable source: ARCHITECTURE §1.1 + PITFALLS §P-X + SUMMARY OQ-XX. `additionalProperties: false` in agents-schema.yaml rejects undeclared fields.

| # | Field | Required | Default | PITFALLS mitigation |
|---|-------|----------|---------|---------------------|
| 1 | `name` | YES | — | — |
| 2 | `description` | YES | — | — |
| 3 | `version` | YES | — | P14 (schema migration) |
| 4 | `persona` | YES | — | **P1** (persona_sha256 invariant) |
| 5 | `tools` | YES | — | OQ-13 (runtime whitelist) |
| 6 | `memory_scope` | YES | `per_agent` | **P4** (cross-project routing) |
| 7 | `lineage` | YES | — | — (skill_sha256 drift anchor) |
| 8 | `refs` | NO | `[]` | — |
| 9 | `tags` | NO | `[]` | — |
| 10 | `expert_id` | NO | — | — (FOUND-08 backward-compat) |
| 11 | `metrics` | NO | `[]` | — |
| 12 | `prerequisites` | NO | `{}` | — |
| 13 | `related_agents` | NO | `[]` | — |
| 14 | `evolution_log` | NO | `[]` | **P5** (tamper-evident sha256 chain) |
| 15 | `fitness_score` | NO | `null` | **P8** + OQ-4 (null→0.5) |
| 16 | `platforms` | NO | `[linux, macos, windows]` | — |
| 17 | `round_table_eligible` | NO | `true` | — |
| 18 | `default_invocation` | NO | `mcp_tool` | — (FOUND-08 additive) |

### 10-Field Memory-Record Schema Lock Status

All 10 mandated fields locked. INDEPENDENT from agents-schema (per CC-2 mandate). `additionalProperties: false`. Plus `persona_sha256` (OQ-1) + `schema_version` (P14) + audit fields (`record_id` / `agent_id` / `created_at` / `last_recalled_at` / `recall_count`) + `content`.

| Field | PITFALLS source |
|-------|-----------------|
| `expires_at` | P2 mitigation 1 (hard TTL) |
| `verified_at` | P2 mitigation 2 (periodic re-verification) |
| `supersedes_memory_id` | P2 mitigation 4 (supersession chain) |
| `confidence` | P2 mitigation 5 + OQ-4 (time-decay + neutral 0.5) |
| `half_life_days` | P2 mitigation 5 (decay rate) |
| `evidence_chain` | P5 mitigation 2 (hallucination guard, ≥3 sources) |
| `evidence_operator_ids` | P5 mitigation 3 (bias amplification guard) |
| `status` | P5 mitigation 1 + P6 mitigation 6 (never hard-delete + quarantine) |
| `confidentiality` | P10 mitigation 2 (privacy / data leakage) |
| `scope` | P4 mitigation 1 (finer than memory_scope; global/project/session) |
| `persona_sha256` (cross-layer) | P1 mitigation 4 + OQ-1 (drift detection) |
| `schema_version` (cross-layer) | P14 mitigation 1 (migration key) |

## 2-Layer Schema Split Declaration (CC-2 Resolved)

The 2-layer split is **explicit upfront** (§1.3 ASCII diagram). Layer 1 (agent-profile YAML, operator-owned) locks identity + runtime knobs + curator-managed metadata; Layer 2 (memory-record schema, curator + multi-source) locks time-decay + provenance + scope isolation + privacy + lifecycle invariants. They are linked via `agent_id` (memory record) = `name` (agent YAML) and `persona_sha256` (cross-layer drift detection). This resolves CC-2's mandate that the 18-field schema "not be misread as insufficient."

## 3-Tier Memory Declaration (OQ-7 Resolved)

Per-agent memory explicitly divided into 3 tiers (core / working / archival), not a single namespace. Aggregate cap = 500 records (core 50 in YAML persona + working 200 + archival 250 in mem0). Compaction pass triggers at 90% cap with never-hard-delete invariant. P3 + P9 mitigated at the tier-design level.

## Curator `_memory_evolution_phase` Contract Lock (OQ-16 Resolved)

Field contract modeled on v6.0 `_feedback_scan_phase`:
- **Execution order:** AFTER `_feedback_scan_phase` in `_llm_pass()`, never before, never parallel
- **Dry-run-by-default:** mutation requires explicit `HERMES_CURATOR_MEMORY_EVOLUTION_LIVE=1` env or `--live-memory-evolution` CLI flag
- **try/except isolation:** never crash `run_curator_review`; log to errors.log + curator_audit
- **Per-agent iteration:** walks `~/.hermes/agents/*.agent.yaml` with `memory_scope=per_agent`
- **mem0_conclude integration:** `_scoped_agent_id` contextvars pattern (ThreadPoolExecutor-safe)
- **Return shape:** `Dict[str, Any]` parallel to `_feedback_scan_phase`

## 6 OQ Resolutions

| OQ | Resolution | Section |
|----|------------|---------|
| OQ-1 | diff only for persona version control + persona_sha256 snapshot in every memory record | §2.4 + §3.11 |
| OQ-4 | null = neutral 0.5 for ordering; UI shows "untested" | §2.15 + agents-schema.yaml |
| OQ-7 | max_records=500 aggregate (core 50 + working 200 + archival 250); compaction algorithm partial-deferred to v11.0 PoC | §4.4 + §4.5 |
| OQ-13 | YES, `tools` is runtime whitelist enforced by dispatcher | §2.5 + agents-schema.yaml |
| OQ-14 | YES, `agents-schema.yaml` is the formal JSON Schema | §1.2 + Task 2 |
| OQ-16 | `_memory_evolution_phase` runs AFTER `_feedback_scan_phase`, try/except isolated, dry-run-by-default | §5.1-§5.3 |

## 7 Load-Bearing Pitfall Field-Level Mitigations

| Pitfall | Field-level mitigation | PoC must-fix? |
|---------|------------------------|---------------|
| P1 persona drift | persona_sha256 in evolution_log (§2.14) + memory record (§3.11) + cross-layer drift detection | YES |
| P2 stale memory | expires_at + verified_at + supersedes_memory_id + confidence + half_life_days (5 fields) | YES |
| P4 cross-project leakage | scope (global/project/session) + project_id required + promotion gate | YES |
| P5 curator failure modes | evidence_chain ≥3 + evidence_operator_ids + status=archived never-delete + dry-run + bias canary | YES |
| P8 no fitness signal | fitness_score (agent-YAML carrier) + fitness_battery deferred to PoC | YES (battery deferred) |
| P10 privacy / data leakage | confidentiality (public/internal/confidential/restricted) + propagation rule | PARTIAL (restricted + PII vault → v11.1) |
| P14 schema migration breaks | schema_version (memory-record) + version (agent YAML) + dry-run migration + safe defaults | YES |

## 15-Expert Transform Table (FOUND-08 Preserved)

All 15 expert rows copied verbatim from ARCHITECTURE §2 (§6.2 of design doc). 5-field transform pattern (COPY/DROP/REWRITE/FLATTEN/DERIVE/INITIALIZE). All 15 `expert_id` values frozen per FOUND-08 preservation rule; transition is additive (`default_invocation: skill_fallback → mcp_tool`).

## Cross-Validation

Every field narrative cites either ARCHITECTURE §1.1 source OR PITFALLS §P-X mitigation — no invented fields. Phase 44 决策 5 + 6 cited by 决策号 throughout, never re-derived. 2-layer schema split explicit upfront. All 7 load-bearing pitfalls appear in §7.2 audit table with field-level mitigation. All 6 OQs appear in §7.1 audit table with resolution status. Bilingual: EN structure (headers, schemas, field names) + 中文 prose (rationale, examples) per CLAUDE.md.

## Deviations from Plan

None — plan executed exactly as written. All 5 tasks committed individually with `docs(45-01):` prefix. All SC#1-SC#5 success criteria satisfied.

## Self-Check: PASSED

**Files created:**

- [x] FOUND: `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` (1289 lines)
- [x] FOUND: `\planning/research/v10-orchestrator-design/agents-schema.yaml` (~580 lines, 18 fields + $defs)
- [x] FOUND: `.planning/research/v10-orchestrator-design/memory-record-schema.yaml` (~430 lines, 10 mandated fields)

**Commits:**

- [x] FOUND: `d9ed981f7` — Task 1 (§0 + §1)
- [x] FOUND: `107499894` — Task 2 (agents-schema.yaml + memory-record-schema.yaml)
- [x] FOUND: `a8aff5e10` — Task 3 (§2 + §3)
- [x] FOUND: `971c78acf` — Task 4 (§4 + §5)
- [x] FOUND: `7c5406395` — Task 5 (§6 + §7 + §8)

**Success criteria:**

- [x] SC#1: 3 deliverable files exist with required field counts
- [x] SC#2: per-agent memory tier (core/working/archival) documented with max_records=500 + compaction trigger (resolves OQ-7)
- [x] SC#3: curator `_memory_evolution_phase` contract documented (resolves OQ-16)
- [x] SC#4: 15-expert transform table copied verbatim from ARCHITECTURE §2 (FOUND-08 preserved)
- [x] SC#5: 6 OQs + 7 load-bearing pitfalls each have field-level mitigation mapped
