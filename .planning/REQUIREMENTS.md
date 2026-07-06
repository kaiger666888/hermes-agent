# Milestone v11.0 Requirements — Hermes-Native Expert Agents PoC Implementation

**Goal:** 按 v10.0 设计套件(`.planning/research/v10-orchestrator-design/00-` 到 `06-`)实施 vertical slice(1 creative + 1 infra)+ 7 项 PoC 验收(12 person-days),验证三层架构 runtime 可行性。**v11.0 是 v10.0 设计的实施 milestone** —— 把设计落地为 Python 代码 + agent YAML + mem0 extensions,产出可运行的最小 PoC。

**Scope:** 单 repo (hermes-agent) runtime 改动。15 expert 全量 transform + per-agent memory benchmark 留 v12.0。Round table 仅 PoC 范围跑通,生产化优化留 v12+。

**Predecessors:**
- v10.0 design docs (`.planning/research/v10-orchestrator-design/00-` through `06-`)
- v10.0 schemas (`agents-schema.yaml`, `memory-record-schema.yaml`, `round-table-state-schema.yaml`)
- v10.0 PoC plan (`.planning/research/v10-orchestrator-design/05-POC-PLAN.md` §3-§6)
- v6.0 FeedbackStore (memory migration source)
- v7.0 mem0 backend (per-agent scoped memory extension target)
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (serial constraint policy)

---

## INFRA Requirements — Agent Registry + 7 MCP Tools Wire-up (4 reqs)

### INFRA-01: Agent Registry YAML Loader

Load + validate `~/.hermes/agents/*.agent.yaml` per Phase 45 `agents-schema.yaml` (18 fields, JSON Schema Draft 2020-12, camelCase keywords). Rejected on schema violation; lineage fields (`derived_from_skill_id` / `skill_sha256`) populated for sample agents. Loader consumed by both PoC runtime + `agents_list` MCP tool.

**Deliverables:**
- `agent/registry_loader.py` (or extension to existing loader)
- Sample agent YAMLs at `~/.hermes/agents/` (1-2 files, MIGR-01 transform output)
- Unit tests covering schema validation + rejection cases

### INFRA-02: 7 MCP Tools Wire-up in mcp_serve.py

Extend `mcp_serve.py` with 7 MCP tools per Phase 46 `02-ROUND-TABLE-PROTOCOL.md` §5 contract (STACK §3.2 form, no prefix):
- `round_table_open` / `submit_round_table_result` (atomic lifecycle)
- `get_agent_opinion` (single panelist turn)
- `agents_list` / `agent_describe` (registry queries)
- `memory_retrieve_scoped` / `memory_submit_record` (per-agent scoped memory)

All tools consume Phase 45 schemas + Phase 46 state schema. CC native MCP client compatible.

**Deliverables:**
- `mcp_serve.py` extension with 7 new tool registrations
- Per-tool schema validation against `agents-schema.yaml` + `memory-record-schema.yaml`
- Integration test: 1 full round table invocation lifecycle

### INFRA-03: Round Table State Persistence + Crash Recovery

Per-project state path `.runtime/{slug}/round_tables/` (ARCHITECTURE §5.1). State machine: `open` → `in_progress` → `closed` (atomic transitions). Crash recovery for 3 failure modes (per `06-CROSS-REPO-IMPACT.md` §6): partial-write corruption, mid-turn crash, orphaned session. Cross-project reference forbidden.

**Deliverables:**
- `agent/round_table_state.py` (state machine + persistence)
- Crash recovery tests (3 failure modes)
- Lint: cross-project reference detection

### INFRA-04: Serial Execution Enforcement

Hard constraint: 1 panelist 1 turn sequential `await`. No parallel panelist execution. References MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (global concurrency==1 by design). GLM 4-key rotation compatible (no concurrent API calls within a round table).

**Deliverables:**
- Async lock primitive in `agent/round_table_executor.py`
- Test: parallel submission rejected with clear error
- Documentation: serial constraint rationale + GLM rotation compatibility analysis

---

## CREATIVE Requirements — Screenplay Step 3 Round Table (2 reqs)

### CREATIVE-01: 9-Agent Screenplay Step 3 Round Table End-to-End

Implement 1 vertical slice: screenplay Step 3 (HOOK-09 edge case) as 9-agent round table. Agents = (sample 9 from 15 expert transform, MIGR-01). End-to-end runnable: `round_table_open` → 9 sequential `get_agent_opinion` calls → 1 `submit_round_table_result`. Output JSON validates against screenplay Step 3 schema.

**Deliverables:**
- `~/.hermes/agents/` sample 9 agent YAMLs (transformed from SKILL.md, MIGR-01)
- Round table execution script: `scripts/run_screenplay_step3_roundtable.py`
- Smoke test: full lifecycle on real GLM API call, latency < 30s

### CREATIVE-02: Memory Conflict Arbitration Runtime

Implement memory conflict arbitration per Phase 46 `02-ROUND-TABLE-PROTOCOL.md` §3 contract:
- Comparator LLM pass (detect conflicting panelist statements)
- Scope precedence: `session > project > global`
- Confidence-weighted voting
- Conflict log persisted to `.runtime/{slug}/round_tables/{round_id}/conflicts.jsonl`

P7 mitigation: 5 sub-mechanisms active.

**Deliverables:**
- `agent/memory_arbitration.py` (comparator + scope precedence + voting)
- Conflict log writer
- Test: 2-conflict scenario produces correct arbitration + log entry

---

## EVAL Requirements — 7 Acceptance Criteria (7 reqs)

### EVAL-01: Fitness Battery Design (3d)

Per `05-POC-PLAN.md` §4.1 + PITFALLS §P8. Design fitness battery: a battery of test scenarios that score agent outputs on dimensions relevant to the vertical slice (e.g. screenplay Step 3 quality, conflict resolution correctness). Each scenario has expected-output + scoring rubric. Battery persisted as data files.

**Deliverables:**
- `.planning/research/v11-poc-eval/fitness-battery-spec.md`
- `tests/v11-fitness-battery/` with 5-10 scenario files
- Run script: `scripts/run_fitness_battery.py`

### EVAL-02: Latency SLO p95 < 500ms (2d)

Per `05-POC-PLAN.md` §4.2. Per-agent scoped mem0 retrieval p95 < 500ms. Measure: instrument `memory_retrieve_scoped` MCP tool with timing. Test: 100 sequential retrievals on populated memory store. Document baseline + bottlenecks.

**Deliverables:**
- Timing instrumentation in `agent/memory_scoped_retrieval.py`
- `tests/v11-latency-bench/` benchmark script + results JSON
- `.planning/research/v11-poc-eval/latency-baseline.md` (results + analysis)

### EVAL-03: Bias Canary (2d)

Per `05-POC-PLAN.md` §4.3 + Phase 45 curator contract. Curator `_memory_evolution_phase` hallucination detection: bias canary runs curator in dry-run + flags suspicious memory edits (low evidence_chain, low confidence, unsupported claims). Test: inject 5 known-bad memory records, expect 4/5 caught.

**Deliverables:**
- `agent/curator_bias_canary.py` (extension to `agent/curator.py`)
- `tests/v11-bias-canary/` with 5 synthetic bad-record fixtures
- Run script: `scripts/run_bias_canary.py`

### EVAL-04: Compaction Pass (1d)

Per `05-POC-PLAN.md` §4.4. Trigger compaction when `memory.max_records` threshold hit. Compaction = archive oldest archival-tier records + summarize working-tier into core-tier. Test: trigger compaction at exactly `max_records=500`, verify post-compaction state.

**Deliverables:**
- `agent/memory_compaction.py`
- Test: trigger + verify post-compaction state machine

### EVAL-05: Threshold Tuning (1d)

Per `05-POC-PLAN.md` §4.5. Document initial defaults + tuning path. Thresholds: `memory.max_records`, `confidence_threshold_for_promotion`, `evidence_chain_min_for_acceptance`. Initial defaults from v10.0 schemas; tuning path documented for v12.0 operators.

**Deliverables:**
- `.planning/research/v11-poc-eval/threshold-tuning.md` (defaults + tuning methodology)
- Config schema fields for each threshold in `agents-schema.yaml` (already present, verify)

### EVAL-06: Dry-Run-First Invariant (1d)

Per `05-POC-PLAN.md` §4.6 + Phase 45 curator contract. Curator default `dry_run: true`. Schema migration default `dry_run: true`. Test: invoke both without explicit `dry_run: false` flag, verify no state mutation.

**Deliverables:**
- Default value enforcement in `agent/curator.py` + `scripts/migrate_v6_feedback_to_memory_schema.py`
- Test: default invocation produces zero state mutation

### EVAL-07: Schema Migration Dry-Run (2d)

Per `05-POC-PLAN.md` §4.7 + Phase 49 `04-MIGRATION-PATH.md` §4. v6.0 FeedbackStore JSONL → memory-record-schema migration script with `--dry-run` mode. Dry-run produces diff report (what would change) without writing. P14 mitigation: zero silent drops (every source record accounted for in dry-run output).

**Deliverables:**
- `scripts/migrate_v6_feedback_to_memory_schema.py` (with `--dry-run` flag)
- `tests/v11-schema-migration/` fixtures (1 sample v6.0 FeedbackStore)
- Dry-run output format spec: `.planning/research/v11-poc-eval/migration-dry-run-format.md`

---

## MIGR Requirements — Sample Agent YAML Transform (1 req)

### MIGR-01: 9 Sample Agent YAMLs from SKILL.md Transform

Per Phase 49 `04-MIGRATION-PATH.md` §2 75-cell transform table. Transform 9 sample movie-expert SKILL.md → agent YAML (sufficient for CREATIVE-01 screenplay Step 3 round table). NOT all 15 experts (that's v12.0 scope). Each YAML validates against Phase 45 `agents-schema.yaml` (camelCase keywords, 18 fields, lineage populated).

**Deliverables:**
- 9 agent YAMLs at `~/.hermes/agents/*.agent.yaml`
- Transform log: which SKILL.md frontmatter fields mapped to which agent YAML fields (audit trail per Phase 49 §2 rules)
- Schema validation: all 9 YAMLs pass `jsonschema.Draft202012Validator.validate()`

---

## VALIDATE Requirements — Milestone Close-out (1 req)

### VALIDATE-01: Milestone Audit + Smoke Test

End-of-milestone audit: 15/15 reqs verified, vertical slice end-to-end smoke test (real GLM API call, no mocks), latency benchmark published, bias canary report published. Audit verdict: PASS / tech_debt / FAIL.

**Deliverables:**
- `.planning/milestones/v11.0-MILESTONE-AUDIT.md`
- `.planning/research/v11-poc-eval/smoke-test-report.md` (vertical slice end-to-end output)

---

## Traceability

| REQ-ID | Phase | Category | Person-days | Status |
|--------|-------|----------|-------------|--------|
| INFRA-01 | 52 | INFRA | (bundled with INFRA-02) | Pending |
| INFRA-02 | 52 | INFRA | 2 | Pending |
| INFRA-03 | 52 | INFRA | 1 | Pending |
| INFRA-04 | 52 | INFRA | 0.5 | Pending |
| MIGR-01 | 53 | MIGR | 1 | Pending |
| CREATIVE-01 | 53 | CREATIVE | 1 | Pending |
| CREATIVE-02 | 53 | CREATIVE | 1 | Pending |
| EVAL-01 | 54 | EVAL | 3 | Pending |
| EVAL-02 | 54 | EVAL | 2 | Pending |
| EVAL-03 | 54 | EVAL | 2 | Pending |
| EVAL-04 | 55 | EVAL | 1 | Pending |
| EVAL-05 | 55 | EVAL | 1 | Pending |
| EVAL-06 | 55 | EVAL | 1 | Pending |
| EVAL-07 | 55 | EVAL | 2 | Pending |
| VALIDATE-01 | 56 | VALIDATE | 1 | Pending |

**Total:** 15 reqs · 19.5 person-days (slightly above 12-day PoC budget due to MIGR-01 + close-out; MIGR-01 can shrink to 0.5d if transform rules from Phase 49 §2 are sufficiently tight)

**Coverage:** 15/15 mapped · Phases 52-56 (5 phases planned) · No orphans.

**Phase mapping rationale:**
- **Phase 52 (INFRA-FOUNDATION):** INFRA-01..04 — agent registry + 7 MCP tools + state machine + serial enforcement. First phase because 53-55 build on its runtime.
- **Phase 53 (CREATIVE-SLICE):** MIGR-01 + CREATIVE-01..02 — MIGR-01 bundled here because CREATIVE-01 needs the 9 sample agent YAMLs as precondition. Splitting would force a non-value-add dependency wall.
- **Phase 54 (EVAL-HARNESS-1):** EVAL-01..03 — fitness battery (FIRST per `05-POC-PLAN.md` §6.1) + latency SLO + bias canary (THIRD per §6.1).
- **Phase 55 (EVAL-HARNESS-2):** EVAL-04..07 — compaction + threshold tuning + dry-run-first + schema migration dry-run (SECOND per §6.1). Phase 54 ships before 55, preserving §6.1 sequencing rationale (fitness battery = regression-detection foundation).
- **Phase 56 (VALIDATE):** VALIDATE-01 — strictly LAST, analog to v10.0 Phase 51 / v5.0 Phase 27 close-out pattern.

---

## Out of Scope (deferred to v12.0+)

- **15-expert 全量 transform** —— 仅 9 sample (CREATIVE-01 用) 在 v11.0 实施;剩余 6 expert 留 v12.0
- **per-agent memory benchmark 全量** —— 仅 latency p95 测;memory throughput / concurrent-agent scaling 留 v12.0
- **Option B → 物理分区迁移** —— v11.0 仍用 mem0 单 backend + `agent_id` filter;物理分区触发条件留 v12+ 监测后决定
- **live production traffic** —— v11.0 PoC 仅 smoke test;production deployment 留 v12+
- **kais-hermes-skills repo 改动** —— 设计文档已锁定 lineage 不动 SKILL;v11.0 不改 SKILL.md,只读
- **new repo 创建(如 kais-orchestrator)** —— 单 repo 收敛决策保留;v11.0 全在 hermes-agent
- **deprecate SKILL.md form** —— v11.0 SKILL 作 fallback 保留(`default_invocation: skill_fallback` per Phase 49 §3)
- **threshold tuning production data** —— v11.0 仅文档化 initial defaults;tuning 用 prod data 留 v12+

---

*Last updated: 2026-07-07 — v11.0 ROADMAP created (5 phases 52-56, 15/15 reqs mapped, all status=Pending). Traceability table aligned with ROADMAP phase mapping. Next: plan Phase 52 (`/gsd:plan-phase 52`).*
