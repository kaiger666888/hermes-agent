---
gsd_state_version: 1.0
milestone: v7.0
milestone_name: openclaw → hermes-agent Primary Agent Migration
status: milestone_complete
last_updated: "2026-06-25T15:45:00Z"
last_activity: 2026-06-25
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 7
  completed_plans: 7
  percent: 100
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
**Current focus:** v7.0 Phase 34 — Skills Migration (in progress: Plan 02 of 03 complete)

## Current Position

Phase: 37 of 37 (Validation & Migration Report) — COMPLETE (v7.0 milestone ready for `/gsd:complete-milestone v7.0`)
Plan: 01 of 01 in phase (01 complete — Phase 37 fully done; v7.0 milestone closed)
Status: Milestone complete — ready for v7.0 archive + v8.0 planning
Last activity: 2026-06-26 - Completed quick task 260626-vzl: Encode Notion "创作方向" into kais-movie-pipeline refs (3 new refs + 3 SKILL.md patches)

### Progress

```
v1 movie-experts:               [██████████] 100% (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP design:               [██████████] 100% (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG:             [██████████] 100% (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:      [██████████] 100% (Phases 19-21, shipped 2026-06-18)
v5.0 V8.6 Adaptation:           [██████████] 100% (Phases 22-27, shipped 2026-06-19)
v6.0 Self-Evolution Feedback:   [██████████] 100% (Phases 28-33, shipped 2026-06-24)

v7.0 openclaw → hermes Migration:
  Phase 34 (Skills Migration)              [██████████] 100% COMPLETE — 3/3 plans done (coding-agent + tmux-agents skills migrated; bidirectional related_skills wired; COEXISTENCE.md authored)
  Phase 35 (SOUL.md Enhancement)           [██████████] 100% COMPLETE — 1/1 plan done (SOUL.md non-destructive integration + transformation note)
  Phase 36 (Memory Ingestion)              [██████████] 100% COMPLETE — 2/2 plans done (batch_ingest.py + spot_check.py + USER.md migrated + INGESTION-NOTE)
  Phase 37 (Validation & Report)           [██████████] 100% COMPLETE — 1/1 plan done (BENCHMARK-RESULTS + v7.0-MIGRATION-REPORT.md + 37-VERIFICATION)
```

**v7.0 milestone status:** All 4 phases complete (34 + 35 + 36 + 37). 14/14 requirements structurally satisfied (SKILL×4 + SOUL×3 + MEM×4 + VALIDATE×3). Ready for `/gsd:complete-milestone v7.0` archive + tag. Operator next: run 4 Operator Action Items in v7.0-MIGRATION-REPORT.md to confirm runtime behavior, then begin v8.0 milestone planning.

### Phase Statuses (v7.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 34 | Skills Migration (coding-agent + tmux-agents) | **Complete** | SKILL-01..04. All 3 plans done: Plan 34-01 (coding-agent, 87e046b0d) + Plan 34-02 (tmux-agents, 4c64890c6) + Plan 34-03 (coexistence wiring + COEXISTENCE.md, a62c1178d + 5cbe555cc). Verification: passed 5/5. |
| 35 | SOUL.md Identity Enhancement | **Complete** | SOUL-01..03. 1/1 plan done (35-01: SOUL.md non-destructive integration + 35-01-TRANSFORMATION-NOTE.md, 0191f5589). Verification: human_needed (structural all-pass; 2 SC require runtime observation — deferred to operator). |
| 36 | Memory Ingestion (USER.md + 124 .md → mem0) | **Complete** | MEM-01..04. 2/2 plans done: 36-01 (batch_ingest.py + spot_check.py, d7aa2eb7c + 50ee1b8b2) + 36-02 (USER.md migrated + INGESTION-NOTE). Verification: human_needed (tooling-only; live ingest deferred pending MEM0_API_KEY). File count corrected: 124 files / 817KB (NOT 133 / 1.3MB). |
| 37 | Validation & Migration Report | **Complete** | VALIDATE-01..03. 1/1 plan done (37-01: BENCHMARK-RESULTS 9bcfcdecc + v7.0-MIGRATION-REPORT d1f6b9b33 + 37-VERIFICATION 2cb836c5c). Verification: human_needed (3/3 structural; runtime smoke-tests deferred per scoped boundary). **v7.0 milestone ready for `/gsd:complete-milestone v7.0`.** |

### Critical Path

```
Phase 34 (Skills)   ──┐
                      │
Phase 35 (SOUL.md)  ──┼──→  Phase 37 (Validation + Report)  ← MUST run last
                      │
Phase 36 (Memory)   ──┘
```

Phases 34, 35, 36 are parallel-eligible (disjoint paths: repo skills / operator SOUL / operator memories). Phase 37 strictly last — validates all three + writes the migration report.

## Performance Metrics (v7.0)

- v7.0 phases total: 4 (Phases 34-37, continuing from v6.0 phase 33)
- v7.0 phases completed: 0
- v7.0 requirements total: 14
- v7.0 requirements mapped: 14 / 14 ✓
- v7.0 requirements orphaned: 0
- v7.0 plans completed: 0 / TBD (plan counts to be refined in plan-phase)
- Deliverable form: MIXED — repo-commit (skills + migration report) + operator-state (SOUL.md + memories). No Hermes-core code changes (config-only at most for mem0 plugin).

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

1. `.planning/PROJECT.md` §"Current Milestone: v7.0" — milestone goal + scope broadening rationale
2. `.planning/ROADMAP.md` — 4 phases (34-37), success criteria, coverage table, critical path
3. `.planning/REQUIREMENTS.md` — 14 requirements with REQ-IDs + Traceability table (all mapped)
4. `~/.openclaw/` workspace — source files for migration (read-only inputs): `skills/coding-agent/`, `skills/openclaw-skills-tmux-agents/`, `SOUL.md`, `workspace/USER.md`, `workspace/memory/*.md` (133 files)
5. `skills/autonomous-ai-agents/` — existing 4 skills (claude-code, codex, opencode, hermes-agent) — coexistence decision input for Phase 34
6. `plugins/memory/mem0/` — existing mem0 plugin (Phase 36 may extend with batch-ingest config)
7. `~/.hermes/SOUL.md` — current hermes defaults (Phase 35 must preserve byte-for-byte in original section)

**Next action:** Plan Phase 34 (`/gsd:plan-phase 34` — Skills Migration: coding-agent + tmux-agents).

**Resume from interrupted phase:** Not yet started — first v7.0 phase.

---

*Last updated: 2026-06-25 — v7.0 ROADMAP + STATE created (4 phases, 14 reqs, granularity=standard, coverage 14/14). Phase 34 ready to plan. v6.0 milestone shipped 2026-06-24 (Phases 28-33).*

## Operator Next Steps

- `/gsd:plan-phase 34` — plan Skills Migration (coding-agent + tmux-agents)
- Coexistence decision for autonomous-ai-agents overlap will be resolved during Phase 34 planning
