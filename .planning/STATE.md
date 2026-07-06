---
gsd_state_version: 1.0
milestone: v10.0
milestone_name: Hermes-Agent 编排架构第一性原理推导(设计型)
status: planning
last_updated: "2026-07-06T12:58:57.186Z"
last_activity: 2026-07-06
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: Hermes Agent — Kai's Personal Agent Platform

## Project Reference

**Project code:** MESV2 (historical; v7.0 broadens scope beyond movie-experts)
**Name:** Hermes Agent — Kai's Personal Agent Platform
**Core value:** 让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备的代码委派、自动化集成、文档协作、个人身份与记忆能力(v7.0 迁移目标)。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** v9.0 — Phase 41 PREVIEW shipped (Plan 01); parallel-eligible wave {38,39,40,41} has 40+41 done, 38+39 still pending

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-07-06 — Milestone v10.0 started

### Progress

```
v1 movie-experts:               [██████████] 100% (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP design:               [██████████] 100% (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG:             [██████████] 100% (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:      [██████████] 100% (Phases 19-21, shipped 2026-06-18)
v5.0 V8.6 Adaptation:           [██████████] 100% (Phases 22-27, shipped 2026-06-19)
v6.0 Self-Evolution Feedback:   [██████████] 100% (Phases 28-33, shipped 2026-06-24)
v7.0 openclaw → hermes Migration:[██████████] 100% (Phases 34-37, shipped 2026-06-25)

v9.0 kais-movie-pipeline 闭环深化 (in planning):
  Phase 38 (SLICE — 平台母版切片)          [██████████] 100% Plan 01 SHIPPED 2026-06-27 (platform-master-slicing.md + SKILL.md Step 14 body; variants[] schema)
  Phase 39 (FORM — 配方库 v0)              [██████████] 100% Plans 01+02+03 SHIPPED 2026-06-27 (49 tests; plugin + 10 seed formulas + Step 0 + theory_critic formula_reference)
  Phase 40 (GATE — 3 新审核门)             [██████████] 100% Plans 01+02+03 SHIPPED 2026-06-26 (145 tests; 3 detectors + 8→11 registry + auto-detect wiring + docs)
  Phase 41 (PREVIEW — LTX2.3 Step 6.5)     [██████████] 100% Plan 01 SHIPPED 2026-06-27 (ltx2-preview-loop.md + SKILL.md Step 6.5 + pipeline-dag.md annotation; FOUND-08 preserved)
  Phase 42 (DATA — 数据收敛 Step 15)       [██████████] 100% Plans 01+02+03+04 SHIPPED 2026-06-27 (107 tests; schema+adapters+tuning_loop+queue+library_writer+CLI+data-convergence.md; HIL invariant enforced)
  Phase 43 (VALIDATE — 集成验证)            [██████████] 100% Plan 01 SHIPPED 2026-06-27 (3 integration flows verified + FOUND-08 byte-diff all match + v9.0-MILESTONE-AUDIT.md 10 sections)
```

**v9.0 milestone status:** COMPLETE — 6/6 phases shipped, 13/13 plans complete, 22/22 requirements satisfied. Audit: `.planning/milestones/v9.0-MILESTONE-AUDIT.md`. FOUND-08 preserved milestone-wide. Ready for `git tag v9.0` + `/gsd:complete-milestone v9.0` (operator actions).

### Phase Statuses (v9.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 38 | SLICE — 平台母版切片 (Step 14) | **Plan 01 SHIPPED (2026-06-27)** | SLICE-01..04 satisfied. platform-master-slicing.md (346 lines) + SKILL.md Step 14 body section + variants[] schema in asset-bus-schema.md. FOUND-08 byte-identical. |
| 39 | FORM — 配方库 v0 (new plugin) | **Plans 01+02+03 SHIPPED (2026-06-26 → 2026-06-27)** | FORM-01..04 satisfied. 49 tests GREEN. Plugin scaffold + 10 seed formulas + Step 0 + theory_critic formula_reference. theory_critic body-only patch (frontmatter byte-identical). |
| 40 | GATE — 3 新审核门 | **Plans 01+02+03 SHIPPED (2026-06-26)** | GATE-01..04 satisfied. 145 tests GREEN. 3 detectors + gates.yaml 8→11 additive + auto_detect_and_resolve + tools dispatch + review-gates.md docs. V8.6 8-gate preserved byte-for-byte; gate.py FROZEN. |
| 41 | PREVIEW — LTX2.3 Step 6.5 | **Plan 01 SHIPPED (2026-06-27)** | PREVIEW-01..03 satisfied. ltx2-preview-loop.md (321 lines) + SKILL.md Step 6.5 + pipeline-dag.md annotation. 4-state fallback policy rides existing BLOCKING-mode Gate. V9-FUTURE-02 operator-action-handoff. |
| 42 | DATA — 数据收敛 (Step 15) | **Plans 01+02+03+04 SHIPPED (2026-06-27)** | DATA-01..04 satisfied. 107 tests GREEN. PlatformMetrics schema + 5 adapter stubs + formula_tuning_loop + JSONL queue + HIL-gated library_writer + CLI + data-convergence.md. V9-FUTURE-01 operator-action-handoff. |
| 43 | VALIDATE — 集成验证 + close-out | **Plan 01 SHIPPED (2026-06-27)** | VALIDATE-01..03 satisfied. 3 integration flows verified (SLICE→DATA / FORM→GATE / PREVIEW→Step 6). FOUND-08 byte-diff: 30 SKILL.md frontmatter all match `a2a20d2be`. v9.0-MILESTONE-AUDIT.md (10 sections) authored. 301 tests GREEN final evidence. |

### Critical Path

```
            ┌── Phase 38 (SLICE)  ───────┐
            │                            ├──→ Phase 42 (DATA)  ──┐
            ├── Phase 39 (FORM)   ───────┤                      │
Parallel    │                            │                      │
wave  ──────┤── Phase 40 (GATE)   ───────┘                      ├──→ Phase 43 (VALIDATE)
(disjoint,  │                                                   │      strictly LAST
 can start  │                                                   │
concurrent) └── Phase 41 (PREVIEW)  ────────────────────────────┘
                  (independent — touches Step 6.5 only)
```

**Parallel-eligible wave:** Phase 38 + 39 + 40 + 41 touch disjoint paths (Step 14 SKILL body / new formula_library plugin / review_gates registration / Step 6.5 ref). All four may start concurrently after user approval.

**Hard dependencies:**

- Phase 42 (DATA) → needs variants[] from Phase 38 (SLICE) + formula_library from Phase 39 (FORM) as tuning-loop write-back target.
- Phase 43 (VALIDATE) → strictly last; runs integration-checker across all 5 prior phases.

**FOUND-08 frozen rule continues milestone-wide:** zero expert_id / frontmatter changes across all 16 active movie-experts. Byte-diff verified at Phase 43 against v9.0 start commit `a2a20d2be`.

## Performance Metrics (v9.0)

- v9.0 phases total: 6 (Phases 38-43, continuing from v7.0 phase 37; v8.0 was a quick-task batch, not formal milestone)
- v9.0 phases completed: 0
- v9.0 requirements total: 22 (SLICE×4 + FORM×4 + GATE×4 + PREVIEW×3 + DATA×4 + VALIDATE×3)
- v9.0 requirements mapped: 22 / 22 ✓
- v9.0 requirements orphaned: 0
- v9.0 plans completed: 0 / TBD (plan counts to be refined in plan-phase)
- Deliverable form: repo-commit only — skills/kais-movie-pipeline/ + skills/movie-experts/ body patches + new plugins/formula_library/ + plugins/review_gates/ additive registration. **Zero Hermes core Python/JS changes** (new plugin lives in plugins/ namespace; new gates register on existing Phase 34 state machine).
- Operator-action-handoffs (NOT gaps, per scoped-boundary design): (1) Phase 41 LTX2.3 live GPU generation testing; (2) Phase 42 5 平台 API key 配置 + live data ingestion. Both documented in v9.0-MILESTONE-AUDIT.md at close.

## Decisions (v9.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 6 phases continuing from v7.0 phase 37 (38, 39, 40, 41, 42, 43) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only. v7.0 ended at P37; v8.0 was a quick-task batch (not formal milestone) — label consumed to avoid version collision. | Applied 2026-06-26 — ROADMAP phase numbering 38-43 |
| Phases 38 + 39 + 40 + 41 are parallel-eligible (parallel-eligible wave) | Disjoint paths: P38 = kais-movie-pipeline SKILL.md Step 14 body + new ref; P39 = new `plugins/formula_library/` + Step 0 patch; P40 = `plugins/review_gates/gates.yaml` additive registration; P41 = Step 6.5 ref + wiring. Zero file overlap. | Applied 2026-06-26 — ROADMAP critical path annotated |
| Phase 42 (DATA) depends on Phase 38 + Phase 39 | DATA needs variants[] schema from SLICE to attach per-platform metrics AND formula_library from FORM as tuning-loop write-back target. GATE is NOT a hard dep (read-side lookup only). | Applied 2026-06-26 — ROADMAP critical path annotated |
| Phase 43 (VALIDATE) strictly LAST | Cross-5-phase integration-checker + FOUND-08 byte-diff audit + canonical v9.0-MILESTONE-AUDIT.md. Mirrors v5.0 P27 / v6.0 P33 / v7.0 P37 close-out pattern. | Applied 2026-06-26 — ROADMAP critical path annotated |
| FOUND-08 frozen rule continues (zero expert_id / frontmatter changes across 16 active movie-experts) | Carried from v3 onward. v9.0 patches SKILL.md body only on (at most) kais-movie-pipeline + theory_critic + compliance_gate + editor (per Out-of-Scope). Byte-diff verified at Phase 43 against start commit `a2a20d2be`. | Applied 2026-06-26 — ROADMAP Phase 43 SC#2 + each phase's FOUND-08 note |
| Scope discipline: no Hermes core Python/JS changes | User explicit choice — new plugin lives in `plugins/formula_library/` namespace (hermes-agent internal plugin, NOT core code); new gates register on existing Phase 34 review_gates state machine (additive, no replacement of 8 V8.6 gates). | Applied 2026-06-26 — ROADMAP overview + each phase's scope reminder |
| V8.6 13-step numbering preserved (Step 6.5 / 14 / 15 are additive) | V8.6 numbering stability prioritized over renumbering. New steps inserted additively; existing 13-step I/O contract unchanged (verified at Phase 43 SC#1). | Applied 2026-06-26 — ROADMAP PREVIEW/DATA/SLICE phases all mark additive |
| Skip per-phase research workflow | Source artifact (Notion "创作方向" page) is already analyzed; Tier A shipped as quick task 260626-vzl. Tier B+C requirements are well-defined; research would add latency without changing scope. | Applied 2026-06-26 — no `.planning/research/v9-*` directory created |
| Operator-action-handoffs (NOT gaps) for Phase 41 + Phase 42 | Live LTX2.3 GPU testing + 5 平台 API key configuration are operator-side by design. v9.0 ships adapter skeletons + schema + baseline docs. Mirrors v7.0 migration-milestone scoped-boundary pattern (4 operator smoke-tests there). | Applied 2026-06-26 — Phase 41 SC#4 + Phase 42 SC#5 + Phase 43 SC#4 enumerate handoffs |
| LTX2.3 selected as Step 6.5 default preview model ($0.10/clip) | 5s budget exact match + lowest cost + open weight. CausVid / Kling 1.6 fast documented as alternatives for extreme-motion or CN-native-prompt cases. Phase 41 P01. | Applied 2026-06-27 — ltx2-preview-loop.md §模型选型 |
| Step 6.5 escalation reuses existing Phase 34 BLOCKING-mode Gate (no new gate_id) | Preserves V8.6 8-gate structure byte-for-byte. `GateConfig.max_retries=2` default matches our 2-retry policy exactly — no override needed. `CONSISTENCY_BLOCKED` PIPE-GUARD-01 semantics ensure non-bypassable exhaustion path. | Applied 2026-06-27 — ltx2-preview-loop.md §Fallback Policy |

### Decisions (carried forward — relevant to v9.0)

| Decision | Rationale | Why relevant to v9.0 |
|----------|-----------|----------------------|
| Project scope broadened from movie-experts to personal hermes agent (v6→v7) | PROJECT.md `## What This Is` + `## Core Value` evolved at v7.0 start. | v9.0 returns to movie-experts deepening — operates back inside `skills/movie-experts/` + `skills/kais-movie-pipeline/`. v7.0 broadened scope is preserved; v9.0 is a movie-experts subsystem milestone. |
| FOUND-08 frozen rule (movie-experts expert_id integrity) | Carried from v3 onward. Protects the frozen v6.0 shipped state. | v9.0 patches SKILL.md body on up to 4 experts; zero frontmatter / expert_id changes. Phase 43 byte-diff verifies. |
| `.planning/milestones/` is canonical close-out archive location | v3-v7 all wrote milestone audit/report to `.planning/milestones/v{X}-MILESTONE-AUDIT.md`. | Phase 43 SC#3 specifies `.planning/milestones/v9.0-MILESTONE-AUDIT.md`. |
| Tier A → quick task 260626-vzl (2026-06-26); Tier B+C → v9.0 formal milestone | Tier A (3 refs + 3 SKILL.md patches) was small enough for quick-task flow; Tier B+C (4 new pipeline capabilities + 3 gates + plugin + data loop) needed milestone-level planning discipline. | v9.0 ROADMAP builds on Tier A's 3 refs (platform-specs.md / creative-redlines.md / genre-anchor-urban-fantasy.md) as load-bearing inputs. |

## Accumulated Context

### v7.0 Goal Restatement

把 openclaw 作为主 agent 时的关键能力迁移到 hermes-agent,让 hermes-agent 接管主 agent 角色时保持能力对等:

1. **Skills (SKILL)** ⭐ —— `coding-agent`(统一 tmux 委派 Codex/Claude Code/Pi/OpenCode)+ `tmux-agents`(后台 tmux agent 管理)迁到 `skills/autonomous-ai-agents/`
2. **Identity (SOUL)** —— openclaw `~/.openclaw/SOUL.md` 中的 AIGC 路由规则非破坏性整合进 `~/.hermes/SOUL.md`
3. **Memory (MEM)** —— `USER.md` + 133 个 openclaw memory `.md`(1.3MB)ingest 到 hermes mem0 backend
4. **Validation (VALIDATE)** —— benchmark 测试 + 迁移报告

**核心范式拓宽:** v1-v6 都聚焦 movie-experts;v7.0 是项目第一次触及非 movie-experts 范畴。PROJECT.md `## What This Is` 已对应演进。movie-experts 后续深化在另一 repo(kais-movie-agent)处理。

**Scope explicitly out (与 Kai 2026-06-25 对齐):** provider keys / models.json、feishu channel config、acp config 由 Kai 手动处理;feishu-* / acp-router skills、多 profile 机制延后到 v8.0+;workspace/ 下 GB 级 AIGC 产出留原处;sessions runtime state 不迁。

### Decisions (v7.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4 phases continuing from v6.0 phase 33 (34, 35, 36, 37) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only. v6.0 ended at P33; `--reset-phase-numbers` NOT passed. | Applied 2026-06-25 — ROADMAP.md phase numbering 34-37 |
| Phase 34 (Skills Migration) runs first | P34 unblocks P37 (skills must exist to benchmark). No strict deps otherwise but canonical ordering puts repo-commit work first. | Applied 2026-06-25 — ROADMAP critical path annotated |
| Phases 34 + 35 + 36 are parallel-eligible | Disjoint paths: P34 = repo skills/; P35 = operator ~/.hermes/SOUL.md; P36 = operator ~/.hermes/memories/ + mem0 backend. Zero file overlap. | Applied 2026-06-25 — ROADMAP critical path notes parallel wave |
| Phase 37 (Validation + Report) runs LAST | P37 benchmarks P34 skills + tests P35 SOUL routing + references P36 memories + writes canonical `.planning/milestones/v7.0-MIGRATION-REPORT.md`. Mirrors v5.0 Phase 27 + v6.0 Phase 33 close-out pattern. | Applied 2026-06-25 — ROADMAP critical path annotated |
| SOUL-02 routing rules adaptation is non-destructive | SOUL-01 explicit constraint: must NOT overwrite hermes original SOUL content. openclaw rules added additively, tagged with source + date. | Applied 2026-06-25 — Phase 35 SC #3 + non-destructive contract annotated |
| MEM-02 ingestion may need Phase 36.1 split if volume > 2 plans | 133 files / 1.3MB ingestion is the largest single-req workload in v7.0. If plan-phase reveals setup + ingest + verify needs >2 plans, insert decimal phase. Flagged for plan-phase attention. | Watch-item — not yet triggered |
| Coexistence decision for autonomous-ai-agents overlap deferred to plan-phase | Existing `skills/autonomous-ai-agents/{claude-code, codex, opencode, hermes-agent}` partially overlap with incoming coding-agent. Plan-phase must decide: merge / supplement / replace. ROADMAP SC #5 requires the decision be documented either way. | Watch-item — plan-phase must resolve |
| **Phase 34 P03: SUPPLEMENT coexistence decision documented** | `skills/autonomous-ai-agents/COEXISTENCE.md` is the canonical artifact. 2 new skills add capabilities the 4 existing do not provide; no replacement. Bidirectional `related_skills` graph wired across all 6 skills; latent codex↔opencode asymmetry also resolved. | Applied 2026-06-25 — Phase 34 SC #5 satisfied; phase complete |
| mem0 plugin exists at `plugins/memory/mem0/` — config-only changes acceptable | Plugin already deployed; batch-ingest CLI/config additions are NOT Hermes-core code changes. Stays within "config-only at most" scope. | Applied 2026-06-25 — Phase 36 Hermes-core touch annotated "Configuration-only at most" |
| Phase 34 P01 | 8m | 1 tasks | 1 files |
| Phase 34 P03 | ~2m | 2 tasks | 5 files |
| Phase 35 P01 | 3min | 3 tasks | 1 files |
| Phase 36 P01 | ~15min | 2 tasks | 3 files |
| Phase 37 P01 | ~7m | 3 tasks | 3 files |
| Phase 41 P01 | ~25m | 4 tasks | 3 files |

### Decisions (carried forward — relevant to v7.0)

| Decision | Rationale | Why relevant to v7.0 |
|----------|-----------|----------------------|
| Project scope broadened from movie-experts to personal hermes agent (v6→v7) | PROJECT.md `## What This Is` + `## Core Value` evolved at v7.0 start. v1-v6 history preserved as movie-experts subsystem archive. | All v7.0 phases operate outside `skills/movie-experts/` for the first time. Movie-experts frozen (v6.0 shipped state). |
| FOUND-08 frozen rule (movie-experts expert_id integrity) | Carried from v3 onward. v7.0 does NOT touch movie-experts, but the rule still protects the frozen v6.0 shipped state. | Phase 34 skill migration is into `skills/autonomous-ai-agents/`, NOT `skills/movie-experts/`. Zero movie-experts SKILL.md changes expected across v7.0. |
| `.planning/milestones/` is canonical close-out archive location | v3-v6 all wrote milestone audit/report to `.planning/milestones/v{X}-MILESTONE-AUDIT.md`. v7.0 migration report follows same pattern. | Phase 37 SC #3 specifies `.planning/milestones/v7.0-MIGRATION-REPORT.md`. |

### Blockers / Risks (v7.0 — new)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Coexistence conflict: coding-agent vs existing claude-code/codex/opencode skills** | MEDIUM | MEDIUM (skill discovery ambiguity) | Phase 34 SC #5 requires documented coexistence decision. Plan-phase must inspect existing 4 skills + decide merge/supplement/replace. |
| **mem0 batch-ingest needs new tooling not in existing plugin** | MEDIUM | MEDIUM (MEM-02 may need script work) | Phase 36 plan-phase probes `plugins/memory/mem0/` capabilities. If batch-ingest CLI absent, plan adds it (config-only scope). |
| **133-file ingestion overwhelms single Phase 36 plan** | LOW-MEDIUM | LOW (split via decimal phase) | Decision table above flags Phase 36.1 insertion if >2 plans needed. |
| **SOUL.md routing rules don't map cleanly from openclaw trigger modes to hermes** | MEDIUM | MEDIUM (SOUL-02 adaptation complexity) | Phase 35 SC #3 requires explicit source + adaptation-date tagging per rule. Rules that don't map are dropped with rationale in transformation note (SOUL-03). |
| **Operator-state changes (~/.hermes/SOUL.md, memories/) bypass repo review** | LOW | LOW (operator can self-review) | Phase plans explicitly annotate operator-state paths vs repo-commit paths. Transformation note (SOUL-03) is repo-committed for audit. |
| **Migration report omits a skipped item, causing scope-creep reversal later** | LOW | MEDIUM (re-litigating decisions in v8) | Phase 37 SC #3 enumerates required skipped items (feishu-* / acp-router / models.json / sessions / multi-profile). VALIDATE-03 explicit. |

### Blockers / Risks (carried from v1-v6)

**Inherited from v1 (still ongoing, low priority for v7.0):**

- ⚠ Platform guideline drift (movie-experts refs) — not in v7.0 scope but documented for continuity
- ⚠ 短剧 sample copyright (movie-experts refs) — not in v7.0 scope
- ⚠ LLM-as-judge invalidity — v6 eval gate reuses single-judge; not relevant to v7.0 (no eval gate in v7.0)

**Inherited from v3.0 audit (deferred items, NOT in v7.0 scope):**

- W-1 through W-4, VALIDATE-D1, FUTURE-09 — all movie-experts-scope; v7.0 does not touch

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260626-rq4 | flood-aware `_send_with_retry` (parse retry_after, clamp [3,60]s, default 5s) | 2026-06-26 | dda0e6c1a | [260626-rq4-flood-aware-send-retry](./quick/260626-rq4-flood-aware-send-retry/) |
| 260626-t0q | CJK error classification (port openclaw failover-matches + Zhipu 1305/1311/1113 codes) | 2026-06-26 | c9e1ca8d4 | [260626-t0q-cjk-error-classification](./quick/260626-t0q-cjk-error-classification/) |
| 260626-vzl | Encode Notion "创作方向" into kais-movie-pipeline refs (3 new refs: platform-specs / creative-redlines / genre-anchor-urban-fantasy + 3 SKILL.md References table patches: compliance_gate / theory_critic / kais-movie-pipeline) | 2026-06-26 | bd53bc387 | [260626-vzl-kmp-creative-direction-refs](./quick/260626-vzl-kmp-creative-direction-refs/) |
| 260702-ezx | GLM concurrency + retry hardening (A+B+C): host-keyed `threading.Semaphore` N=4 for `*.bigmodel.cn`, 30s/600s backoff preset for `FailoverReason.overloaded`, 3-strike consecutive-1305 early-abort | 2026-07-02 | 4b821c29b | [260702-ezx-glm-concurrency-hardening](./quick/260702-ezx-glm-concurrency-hardening/) |
| 260702-o1a | Credential-pool overloaded fix: new `CredentialPool.rotate_to_next()` (advances current_id without marking exhausted); overloaded branch switched from `mark_exhausted_and_rotate` → `rotate_to_next`; cycle-detection returns None on full rotation, hands off to ezx 3-strike abort | 2026-07-02 | 5839b5f78 | [260702-o1a-credential-pool-overloaded-fix](./quick/260702-o1a-credential-pool-overloaded-fix/) |

## Deferred Items

Items acknowledged and carried forward (NOT in v7.0 scope, explicitly deferred to v8.0+):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| FEISHU | feishu-doc / feishu-drive / feishu-perm / feishu-wiki migration (FEISHU-01) + merge-vs-keep-4 design decision (FEISHU-02) | Deferred to v8.0+ | v7.0 planning (2026-06-25) |
| AGENT | Multi hermes profile mechanism (AGT-01) | Deferred — v7.0 uses single SOUL.md | v7.0 planning (2026-06-25) |
| AGENT | acp-router alternative form in hermes (AGT-02) | Deferred evaluation | v7.0 planning (2026-06-25) |
| ACP | acp-router skill migration (ACP-01) | Deferred — likely no hermes analog | v7.0 planning (2026-06-25) |
| Operator manual | Provider keys / models.json migration | Kai handles manually (out of milestone flow) | v7.0 planning (2026-06-25) |
| Operator manual | Feishu channel config + ACP config | Kai handles manually | v7.0 planning (2026-06-25) |
| Storage | workspace/ GB-scale AIGC outputs | Stay in place (not agent capability) | v7.0 planning (2026-06-25) |
| Runtime state | agents/<name>/sessions/ + auth-profiles.json | No migration value | v7.0 planning (2026-06-25) |

Items acknowledged at v7.0 close (2026-06-25) — documented operator-action-handoffs (NOT gaps, per migration-milestone scoped boundary design):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Operator smoke-test | MEM0_API_KEY config + live mem0 ingestion (124 .md files) | Documented in v7.0-MIGRATION-REPORT.md §Operator Action Items | v7.0 close (2026-06-25) |
| Operator smoke-test | mem0 spot_check.py 5-query live run + idempotency re-test | Documented in v7.0-MIGRATION-REPORT.md §Operator Action Items | v7.0 close (2026-06-25) |
| Operator smoke-test | SOUL.md routing live observation (3 prompt classes from hermes conversation) | Documented in v7.0-MIGRATION-REPORT.md §Operator Action Items | v7.0 close (2026-06-25) |
| Operator smoke-test | coding-agent + tmux-agents skill invocation live test | Documented in v7.0-MIGRATION-REPORT.md §Operator Action Items | v7.0 close (2026-06-25) |
| Quick task (pre-existing) | 260617-wgz-write-gap-analysis-doc-comparing-creativ | Unrelated to v7.0 (carried from prior milestone) | Pre-v7.0 |

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v9.0" — milestone goal + Tier B/C scope discipline
2. `.planning/ROADMAP.md` — 6 phases (38-43), success criteria, coverage table, critical path (parallel-eligible wave 38+39+40+41; DATA waits on 38+39; VALIDATE strictly last)
3. `.planning/REQUIREMENTS.md` — 22 requirements with REQ-IDs + Traceability table (22/22 mapped, status Phase-assigned)
4. `skills/kais-movie-pipeline/SKILL.md` — existing 13-step V8.6 pipeline; v9.0 adds Step 6.5 / 14 / 15 additively (no renumbering)
5. `skills/kais-movie-pipeline/references/` — 7 existing refs (incl. 3 Tier A refs from quick task 260626-vzl: platform-specs.md / creative-redlines.md / genre-anchor-urban-fantasy.md)
6. `plugins/review_gates/` — Phase 34-shipped state machine (`gate.py` + `gates.yaml` 8 V8.6 gates) — Phase 40 registers gate 9/10/11 additively
7. v9.0 start commit `a2a20d2be` — FOUND-08 byte-diff anchor for Phase 43 VALIDATE-02

**Next action:** After user approval, plan any of the parallel-eligible wave (`/gsd:plan-phase 38` or `/gsd:plan-phase 39` or `/gsd:plan-phase 40` or `/gsd:plan-phase 41`).

**Resume from interrupted phase:** Not yet started — first v9.0 phase.

---

*Last updated: 2026-06-27 — v9.0 milestone COMPLETE. Phase 43 VALIDATE shipped (Plan 01); v9.0-MILESTONE-AUDIT.md authored (10 sections). 6/6 phases done, 13/13 plans done, 22/22 reqs satisfied, FOUND-08 preserved milestone-wide. Ready for `git tag v9.0` + `/gsd:complete-milestone v9.0`.*

## Operator Next Steps

**v9.0 milestone is COMPLETE and ready for close-out.** Operator actions:

1. Review `.planning/milestones/v9.0-MILESTONE-AUDIT.md` (10 sections, 22/22 reqs verified)
2. (Optional) Re-run the verification commands in audit §9 (operator next action)
3. `git tag v9.0` — tag the milestone
4. `/gsd:complete-milestone v9.0` — archive and transition to next milestone

**Operator-action-handoffs (post-tag, NOT gaps):**

- (a) Phase 41 LTX2.3 live GPU testing (V9-FUTURE-02)
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01)
