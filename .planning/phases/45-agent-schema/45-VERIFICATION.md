---
phase: 45-agent-schema
verified: 2026-07-06T23:55:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 7/8
  gaps_closed:
    - "Truth #2 — File agents-schema.yaml exists with 18-field JSON Schema definitions (snake_case → camelCase fix closed the keyword-spelling gap)"
  gaps_remaining: []
  regressions: []
---

# Phase 45: Agent Schema Verification Report

**Phase Goal:** 定义 18-field agent YAML schema + memory-record-schema,作为所有下游设计文档(02/04/05/06)字段引用的物理载体,把 7 个 load-bearing pitfall 的字段级缓解固化

**Verified:** 2026-07-06T23:55:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (commit `6167c4156`)

## Re-Verification Summary

Initial verification (2026-07-06T23:45:00Z) found 1 partial gap: 4 snake_case JSON Schema keywords (`min_length`, `min_items` ×3) that Draft 2020-12 validators silently ignore, leaving the P5 hallucination guard (`evidence_chain ≥3`) and the OQ-13 tools-non-empty guard unenforced.

**Gap closed by commit `6167c4156`** (`fix(45-01): rename snake_case JSON Schema keywords to camelCase`). The commit renames exactly 4 keyword occurrences across the 2 schema files:

| File | Line | Before | After |
| ---- | ---- | ------ | ----- |
| `agents-schema.yaml` | 61 | `min_length: 10` | `minLength: 10` |
| `agents-schema.yaml` | 112 | `min_items: 1` | `minItems: 1` |
| `memory-record-schema.yaml` | 227 | `min_items: 3` | `minItems: 3` |
| `memory-record-schema.yaml` | 269 | `min_items: 1` | `minItems: 1` |

**Validation evidence (python jsonschema 4.26.0, Draft202012Validator):**

| Sample | Expected | Actual | Status |
| ------ | -------- | ------ | ------ |
| `tools: []` against agents-schema | REJECTED | REJECTED: "[] should be non-empty" | ✓ PASS |
| `description: 'short'` (5 chars) against agents-schema | REJECTED | REJECTED: "'short' is too short" | ✓ PASS |
| `evidence_chain` 2-item array against memory-record-schema | REJECTED | REJECTED (minItems=3 violation) | ✓ PASS |
| `evidence_operator_ids: []` against memory-record-schema | REJECTED | REJECTED: "[] should be non-empty" | ✓ PASS |
| Valid full agent (1+ tools, long description) | ACCEPTED | ACCEPTED | ✓ PASS |
| Valid full memory record (3-item evidence_chain) | ACCEPTED | ACCEPTED | ✓ PASS |
| Both schemas meta-valid Draft 2020-12 | PASS | `Draft202012Validator.check_schema` PASSED | ✓ PASS |

**Residual snake_case keyword scan:** `grep -n -E '\b(min_length|min_items|max_length|max_items|...)\b'` across both schemas → exit 1 (no matches). All camelCase forms confirmed at the 4 documented line numbers.

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | File `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` exists | ✓ VERIFIED | 1289 lines (target ≥800); §0-§8 all present; bilingual EN+中文; §1 has 18-row table; §2 has 19 H3 subsections (§2.0 + §2.1-§2.18); §3 has 13 H3 subsections; §4 7 H3; §5 7 H3; §6 4 H3; §7 3 H3; §8 3 H3. Phase 44 决策 5/6 cited 12×; CC-2 cited 12×; 00-FIRST-PRINCIPLES 4×; ARCHITECTURE § 47×; PITFALLS §P 13×. |
| 2 | File `agents-schema.yaml` exists with 18-field JSON Schema definitions | ✓ VERIFIED | File exists, 408 lines, all 18 properties present (`name`/`description`/`version`/`persona`/`tools`/`memory_scope`/`lineage`/`refs`/`tags`/`expert_id`/`metrics`/`prerequisites`/`related_agents`/`evolution_log`/`fitness_score`/`platforms`/`round_table_eligible`/`default_invocation`), 7 required, `additionalProperties: false`, `$defs` for Lineage/Prerequisites/EvolutionLogEntry. JSON Schema Draft 2020-12 meta-valid. All constraints enforce under python jsonschema 4.26.0 (camelCase `minLength`/`minItems` verified firing on bad samples — see Re-Verification Summary table). |
| 3 | File `memory-record-schema.yaml` exists independently with all 10 mandated fields | ✓ VERIFIED | File exists, 380 lines, `$id` distinct from agents-schema (`https://hermes-agent.local/v10/memory-record-schema.yaml` vs `.../agents-schema.yaml`). All 10 mandated fields present in `properties`: `expires_at`, `verified_at`, `supersedes_memory_id`, `confidence`, `half_life_days`, `evidence_chain`, `evidence_operator_ids`, `status`, `confidentiality`, `scope`. Plus `persona_sha256` (OQ-1) + `schema_version` (P14) + audit fields. Independent top-level schema (not `$ref` to agents-schema). `minItems: 3` on evidence_chain and `minItems: 1` on evidence_operator_ids now enforce (was snake_case in initial verification; fixed in `6167c4156`). |
| 4 | Per-agent memory tier (core/working/archival) documented with `memory.max_records` cap + compaction trigger (resolves OQ-7) | ✓ VERIFIED | §4 has 7 H3 subsections (§4.0 declaration + §4.1-§4.6). §4.1-§4.3 define core (~50) / working (~200) / archival (~250) tiers. §4.4: "OQ-7 resolution: `memory.max_records` 默认 500 records per agent, 3-tier aggregate cap" with explicit breakdown table totaling 500. §4.5 compaction trigger table: 90% threshold → demote lowest-confidence; `expires_at < now` → archive; `confidence < 0.1` → archive; `status=superseded` → archive. §4.6 ASCII diagram. P3+P9 cited. |
| 5 | Curator `_memory_evolution_phase` field contract documented (modeled on v6.0 `_feedback_scan_phase`, dry-run-by-default + try/except + execution order, resolves OQ-16) | ✓ VERIFIED | §5 has 7 H3 subsections. §5.1: "runs IMMEDIATELY AFTER `_feedback_scan_phase(start)` in `_llm_pass()`" with pseudo-code; cites `agent/curator.py` lines 2081-2095 + 2207-2221. §5.2: dry-run-by-default via `HERMES_CURATOR_MEMORY_EVOLUTION_LIVE=1` env or `--live-memory-evolution` CLI flag; cites v6.0 FOUND-06 + PITFALLS §P5 mitigation 5. §5.3: try/except isolation; never crash curator. §5.4 per-agent iteration walks `~/.hermes/agents/*.agent.yaml` filter `memory_scope==per_agent`. §5.5 `_scoped_agent_id` contextvars for thread-safe mem0_conclude. §5.6 return shape `Dict[str, Any]` parallel to `_feedback_scan_phase`. |
| 6 | 15 expert transform mapping table copied from ARCHITECTURE §2 (SKILL frontmatter → agent YAML per-field deltas) | ✓ VERIFIED | §6 has 4 H3 subsections. §6.1 declares 5-field transform pattern (COPY/DROP/REWRITE/FLATTEN/DERIVE/INITIALIZE) verbatim from ARCHITECTURE §2 line 124. §6.2 contains 15-row markdown table; all 15 expert names present (verified by grep): `hook_retention`, `creative_source`, `screenplay`, `script_auditor`, `character_designer`, `cinematographer`, `style_genome`, `prompt_injector`, `visual_executor`, `continuity_auditor`, `audio_pipeline`, `editor`, `colorist`, `compliance_gate`, `theory_critic`. Spot-checked rows match ARCHITECTURE §2 verbatim. §6.3 FOUND-08 preservation rule + aggregate stats present. |
| 7 | 6 Open Questions (OQ-1 / OQ-4 / OQ-7 / OQ-13 / OQ-14 / OQ-16) explicitly resolved or explicitly deferred to v11.0 | ✓ VERIFIED | §7.1 audit table contains all 6 rows. OQ-1 (persona version control) → resolved §2.4 + §3.11 (`persona_sha256` snapshot). OQ-4 (fitness_score cold start) → resolved §2.15 (null=neutral 0.5). OQ-7 (memory.max_records) → resolved §4.4 (max_records=500); compaction algorithm/cadence PARTIAL-deferred to 05-POC-PLAN.md. OQ-13 (tools enum) → resolved §2.5 (YES, runtime whitelist) AND now schema-enforced via `minItems: 1`. OQ-14 (agents-schema.yaml JSON Schema) → resolved §1.2. OQ-16 (curator phase order) → resolved §5.1-§5.3 (AFTER _feedback_scan_phase, try/except isolated, dry-run-by-default). 5 fully resolved, 1 (OQ-7) partial-deferred — both acceptable per SC#5 wording "explicitly resolved or explicitly deferred". |
| 8 | 7 load-bearing pitfalls (P1 / P2 / P4 / P5 / P8 / P10 / P14) each have ≥1 schema field-level mitigation mapped | ✓ VERIFIED | §7.2 audit table contains all 7 rows with explicit field-level mitigations: P1 → `persona_sha256` in evolution_log (§2.14) + memory record (§3.11); P2 → 5 fields (§3.1-§3.5); P4 → `scope` + `project_id` (§3.9); P5 → `evidence_chain ≥3` + `evidence_operator_ids ≥1` + `status=archived` + dry-run + bias canary (§3.6+§3.7+§3.8+§5.2+§5.4) — **the `evidence_chain ≥3` constraint now ACTUALLY enforces** post-`6167c4156` (verified via jsonschema rejection of 2-item chain); P8 → `fitness_score` (§2.15) + fitness_battery deferred to PoC; P10 → `confidentiality` enum (§3.10) PARTIAL (restricted+PII vault → v11.1); P14 → `schema_version` (§3.12) + agent YAML `version` (§2.3). |

**Score:** 8/8 truths fully verified (was 7/8 in initial verification — Truth #2 promoted from PARTIAL to VERIFIED)

### Deferred Items

Items not yet met but explicitly documented in §7 audit table and addressed by later milestone phases — NOT gaps.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | OQ-7 compaction algorithm + cadence (N tick interval) | Phase 50 (POC-PLAN) | Phase 50 goal: "v11.0 PoC 验收条件清单 (fitness battery / latency SLO / bias canary / compaction / dry-run-first)"; §7.1 OQ-7 row marks "PARTIAL — 具体算法 defer 到 v11.0 PoC 实测" |
| 2 | P8 fitness_battery yaml + fitness_trend.jsonl format + model_id isolation | Phase 50 (POC-PLAN) | §7.2 P8 row marks "fitness_battery + trend.jsonl + model_id isolation defer 到 05-POC-PLAN.md"; Phase 50 goal includes "fitness battery" |
| 3 | P10 confidentiality `restricted` tier + PII vault | v11.1 (post-PoC) | §7.2 P10 row marks "PARTIAL — restricted tier + PII vault defer 到 v11.1"; §3.10 narrative notes "v11.0 PoC ships with public/internal/confidential; restricted tier + PII vault deferred to v11.1" |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` | design narrative ≥800 lines with §0-§8, bilingual, 18-field per-field deep dive + memory-record narrative + 3-tier memory + curator phase contract + 15-expert table + OQ/pitfall audit + downstream citation guide | ✓ VERIFIED | 1289 lines (target ≥800). All §0-§8 present. Bilingual EN structure + 中文 prose. Contains all required markers: 18 (×N), `memory-record-schema`, `core / working / archival`, `_memory_evolution_phase`, P1/P2/P4/P5/P8/P10/P14, OQ-1/4/7/13/14/16. |
| `.planning/research/v10-orchestrator-design/agents-schema.yaml` | Formal JSON Schema (Draft 2020-12) with all 18 fields, type/description/enum/required/defaults, `$defs` for Lineage/Prerequisites/EvolutionLogEntry | ✓ VERIFIED | 408 lines, valid YAML, all 18 properties present, JSON Schema Draft 2020-12 meta-valid. All constraints enforce correctly under python jsonschema 4.26.0: `additionalProperties: false` rejects unknown fields; enum/pattern/minimum/maximum all fire; `minLength: 10` on description and `minItems: 1` on tools verified firing on bad samples. `$defs` block present with Lineage/Prerequisites/EvolutionLogEntry. |
| `.planning/research/v10-orchestrator-design/memory-record-schema.yaml` | Formal INDEPENDENT JSON Schema (Draft 2020-12) with 10 mandated fields + persona_sha256 + schema_version + audit fields, enum on status/scope/confidentiality, range on confidence/half_life_days | ✓ VERIFIED | 380 lines, valid YAML, distinct `$id`, all 10 mandated fields present + persona_sha256 + schema_version + 4 audit fields. JSON Schema meta-valid. Enums + ranges enforce correctly. `minItems: 3` on `evidence_chain` (P5 hallucination guard) and `minItems: 1` on `evidence_operator_ids` (P5 bias guard) now verified firing — load-bearing P5 mitigation is machine-enforced, not just documented. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| 01-AGENT-REGISTRY-SCHEMA.md | 00-FIRST-PRINCIPLES.md | markdown §reference + 决策号 citation | ✓ WIRED | 4 citations of `00-FIRST-PRINCIPLES`, 12 citations of `决策 5` / `决策 6` / `root-arg-决策` |
| 01-AGENT-REGISTRY-SCHEMA.md | ARCHITECTURE.md §1+§2+§3 | markdown §reference | ✓ WIRED | 47 citations of `ARCHITECTURE §N`; §6 explicitly declares "ARCHITECTURE.md §2 line 120-148 的 verbatim copy" |
| 01-AGENT-REGISTRY-SCHEMA.md | PITFALLS.md §Pitfall 1/2/4/5/8/10/14 | markdown §reference for field-level mitigation | ✓ WIRED | 13 citations of `PITFALLS §P`; every §3.N field narrative cites its PITFALLS §P source |
| agents-schema.yaml | 01-AGENT-REGISTRY-SCHEMA.md §2 | field name alignment | ✓ WIRED | All 18 property names in schema map to §2.1-§2.18 narrative subsections |
| memory-record-schema.yaml | 01-AGENT-REGISTRY-SCHEMA.md §3 | field name alignment | ✓ WIRED | All 12 schema properties map to §3.1-§3.12 narrative subsections |

### Data-Flow Trace (Level 4)

Not applicable — design-only deliverable (markdown + YAML schemas), no runtime data flow.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| agents-schema.yaml meta-valid Draft 2020-12 | `Draft202012Validator.check_schema` | PASS | ✓ PASS |
| memory-record-schema.yaml meta-valid Draft 2020-12 | `Draft202012Validator.check_schema` | PASS | ✓ PASS |
| agents-schema.yaml validates a known-good sample agent | `validate(good_sample)` | ACCEPTED | ✓ PASS |
| agents-schema.yaml rejects unknown field | additionalProperties: false | 1 error on `unknown_field` | ✓ PASS |
| agents-schema.yaml enforces enum on memory_scope | wrong enum value | 1 error | ✓ PASS |
| agents-schema.yaml enforces pattern on `name` regex | UPPERCASE name | 1 error | ✓ PASS |
| agents-schema.yaml enforces fitness_score range | 1.5 value | 1 error | ✓ PASS |
| agents-schema.yaml enforces `tools minItems: 1` (OQ-13) | `tools: []` | REJECTED: "should be non-empty" | ✓ PASS (was FAIL pre-`6167c4156`) |
| agents-schema.yaml enforces `description minLength: 10` | `'short'` (5 chars) | REJECTED: "too short" | ✓ PASS (was FAIL pre-`6167c4156`) |
| memory-record-schema.yaml enforces `evidence_chain minItems: 3` (P5 guard) | 2-item chain | REJECTED | ✓ PASS (was FAIL pre-`6167c4156`) |
| memory-record-schema.yaml enforces `evidence_operator_ids minItems: 1` | `[]` | REJECTED: "should be non-empty" | ✓ PASS (was FAIL pre-`6167c4156`) |
| memory-record-schema.yaml good 3-item chain accepted | valid full record | ACCEPTED | ✓ PASS |

### Probe Execution

Step 7c SKIPPED — this phase is a DESIGN-ONLY deliverable producing markdown + YAML schemas. No migration / CLI / tooling probes declared in PLAN.md.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DESIGN-02 | 45-01-PLAN.md | Agent Registry Schema: 3 deliverable files (narrative + agents-schema.yaml + memory-record-schema.yaml) | ✓ SATISFIED | All 3 files exist with substantive content (1289 + 408 + 380 lines). All 18 agent fields + all 10 memory-record fields + 3-tier memory + curator phase contract + 15-expert table + 6 OQ resolutions + 7 pitfall mitigations all present. All 4 previously-hollow JSON Schema keywords now enforce correctly. Ready for Phase 51 VALIDATE-02 lint consumption. |

No ORPHANED requirements — only DESIGN-02 is mapped to Phase 45 in REQUIREMENTS.md.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `01-AGENT-REGISTRY-SCHEMA.md` | 3 | `superseded_by: TBD` in document header metadata | ℹ️ Info | Acceptable document metadata placeholder (no current supersedes); not a content debt marker |

(All 4 snake_case JSON Schema keyword warnings from initial verification resolved by `6167c4156`.)

### Human Verification Required

No human verification items required. Phase 45 is a design-only deliverable; all truths are programmatically verifiable.

### Gaps Summary

No gaps. All 8 observable truths verified. The single partial gap from initial verification (snake_case JSON Schema keyword spelling on Truth #2) is closed by commit `6167c4156`. Validation with python jsonschema 4.26.0 confirms all 4 constraints (description length, tools non-empty, evidence_chain ≥3, evidence_operator_ids ≥1) now fire correctly on bad samples, while good samples still pass. Load-bearing P5 hallucination guard is now machine-enforced.

---

_Verified: 2026-07-06T23:55:00Z_
_Verifier: Claude (gsd-verifier)_
