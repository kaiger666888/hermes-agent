---
gsd_state_version: 1.0
milestone: v6.0
milestone_name: Self-Evolution & Feedback Loop
status: planning
last_updated: "2026-06-24T03:30:00.000Z"
last_activity: 2026-06-24
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: Movie-Experts Suite v2 (MESV2)

## Project Reference

**Project code:** MESV2
**Name:** Movie-Experts Suite v2 — 短剧/微电影创作专家增强
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`, `.planning/research/v2-pipeline-design/skills-mapping.yaml`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** v6.0 Self-Evolution & Feedback Loop — Phase 28 (Feedback Ingestion MVP) ready for planning

## Current Position

Phase: 28 (Feedback Ingestion MVP) — ready for planning
Plan: —
Status: Roadmap created; Phase 28 planning not yet started
Last activity: 2026-06-24 — v6.0 ROADMAP.md + REQUIREMENTS.md traceability + STATE.md initialized

### Progress

```
v1 milestone:                  [██████████] 100% Complete (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP milestone:           [██████████] 100% Complete (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG Alignment:  [██████████] 100% Complete (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:     [██████████] 100% Complete (Phases 19-21, shipped 2026-06-18)
v5.0 kais-movie-agent V8.6 Adaptation:
                               [██████████] 100% Complete (Phases 22-27, shipped 2026-06-19)

v6.0 Self-Evolution & Feedback Loop:
  Phase 28 (Feedback Ingestion MVP)        [          ] 0% Not started — MUST run first (core functional guarantee)
  Phase 29 (Feedback Store)                [          ] 0% Not started — depends on P28
  Phase 30 (Eval Gate Reuse)               [          ] 0% Not started — parallel-eligible with P31 after P29
  Phase 31 (Knowledge Evolution Pipeline)  [          ] 0% Not started — parallel-eligible with P30 after P29
  Phase 32 (Curator Upgrade + Audit)       [          ] 0% Not started — depends on P29 + P31
  Phase 33 (Observability + Close-out)     [          ] 0% Not started — MUST run last
```

### Phase Statuses (v6.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 28 | Feedback Ingestion MVP | Not started | Covers INGEST-01..05. MUST run first — core functional guarantee ships here. kais-aigc-platform接入 (INGEST-02) is must-have MVP; transport choice at plan-phase. Hermes-core touch (new ingest entrypoints). |
| 29 | Feedback Store | Not started | Covers STORE-01..04. Depends on P28 normalized schema. New persistence layer under `~/.hermes/skills/.feedback/`. |
| 30 | Eval Gate Reuse | Not started | Covers GATE-01..04. Parallel-eligible with P31 (disjoint files). Extends `_eval/runner.py` (offline dev tooling, no runtime touch). |
| 31 | Knowledge Evolution Pipeline | Not started | Covers EVOL-01, EVOL-03, EVOL-04, EVOL-05. Parallel-eligible with P30. Builds review queue + approve/apply mechanics. |
| 32 | Curator Upgrade + Audit | Not started | Covers CURATE-01..05 + EVOL-02. Directly modifies `agent/curator.py` (unavoidable scope expansion from v5). Implements EVOL-02 diff generator invoked by Curator proposal path. |
| 33 | Observability + Integration Close-out | Not started | Covers OBS-01..03 + integration deliverables. MUST run last. Writes `_shared/v6-feedback-loop-architecture.md` + skills-mapping.yaml `v6_ref_signoffs:` + README + glossary. Mirrors v5.0 Phase 27 pattern. |

### Critical Path

```
Phase 28 (Feedback Ingestion MVP)  ──→  Phase 29 (Feedback Store)  ──┐
                                                                      │
                                       ┌──────────────────────────────┤
                                       │                              │
                                       ▼                              ▼
                                   Phase 30                      Phase 31     ← parallel wave
                                   (Eval Gate)              (Evolution Pipeline)  (disjoint files,
                                       │                              │          share only P28 schema)
                                       └──────────┬───────────────────┘
                                                  ▼
                                         Phase 32 (Curator Upgrade + Audit)
                                                  │  (extends agent/curator.py +
                                                  │   implements EVOL-02 diff generator)
                                                  ▼
                                         Phase 33 (Observability + Close-out)  ← MUST run last
```

Phase 28 must run first (ships the core functional guarantee). Phase 29 depends on P28. Phases 30 + 31 are parallel-eligible (disjoint file ownership). Phase 32 consumes P29 + P31 review queue + implements EVOL-02. Phase 33 is strictly last (close-out + canonical doc).

## Quick Tasks Completed

| Quick ID | Date | Slug | Description | Deliverable |
|----------|------|------|-------------|-------------|
| 260617-wgz | 2026-06-17 | write-gap-analysis-doc-comparing-creativ | Gap-analysis 对照调研报告 §7.2 6 阶段蓝图 vs movie-experts 实际覆盖;高 ROI 缺口排序(雪花法 / E-Konte / SCAMPER) | `.planning/research/methodology-gap-analysis-2026-06-17.md` |

## Performance Metrics (v6.0)

- v6.0 phases total: 6 (Phases 28-33, continuing from v5.0 phase 27)
- v6.0 phases completed: 0
- v6.0 requirements total: 26
- v6.0 requirements mapped: 26 / 26 ✓
- v6.0 requirements orphaned: 0
- v6.0 plans completed: 0 / TBD (per phase)
- Deliverable form: MIXED — Hermes core touch (agent/curator.py extension + feedback ingestion infra in P28/P29/P32) + pure skill layer (additive SKILL.md / refs patches via P31 + canonical doc in P33). This is the v5→v6 scope expansion explicitly accepted in PROJECT.md.

## Accumulated Context

### v6.0 Goal Restatement

让 movie-experts skill suite 从「静态知识层」进化为「带反馈闭环的自学习系统」:

1. **反馈采集 (INGEST)** ⭐ MVP 核心 —— 多源接入:CLI 用户反馈 + kais-aigc-platform 审核反馈 + 手工标注;标准化 JSON schema `{skill_id, expert_id, source, verdict, correction, output_snapshot, ts}`
2. **反馈存储 (STORE)** —— `~/.hermes/skills/.feedback/` 持久化 + 时间衰减权重 + 按 skill 索引 + 去重
3. **eval 基线复用 (GATE)** —— 复用既有 `_eval/runner.py` MT-Bench position-swap harness 做 patch-vs-baseline gate,δ=0.3 平均阈值 + 1.0 单 prompt regression guard + A/B 双盲
4. **知识抽取 (EVOL)** —— LLM 抽取 candidate insights → unified-diff candidate patch → eval gate → review queue → human-in-loop approve → git-commit-on-apply + rollback
5. **Curator 升级 (CURATE)** —— `agent/curator.py` 从「只 archive agent-created」扩展为「能 propose patch 给 bundled skill」;audit log;operator CLI;agent-created skill 半自动路径
6. **可观测性 (OBS)** —— per-skill dashboard + cross-skill view + source breakdown

**核心范式跃迁:** 从 v1-v5 的「人工 curate 静态知识」转为「反馈驱动动态学习」。这是 movie-experts 第一次真正具备 self-improvement 能力。

**范围扩张 (v5→v6):** v6 不再是「纯 skill 内容交付」,需要触动 Hermes 核心 —— `agent/curator.py` 扩展、新增反馈接入 endpoint 或文件 watcher。这是用户在 PROJECT.md 中明确接受的 scope shift。

### Decisions (v6.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 6 phases continuing from v5.0 phase 27 (28, 29, 30, 31, 32, 33) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only. v5.0 ended at P27; `--reset-phase-numbers` NOT passed. | Applied 2026-06-24 — ROADMAP.md phase numbering 28-33 |
| Phase 28 (Feedback Ingestion MVP) runs FIRST | P28 ships the core functional guarantee (every expert can receive feedback after giving opinions). INGEST + STORE must ship before EVOL/CURATE can consume the feedback. MVP-first ordering per instructions. | Applied 2026-06-24 — ROADMAP critical path annotated |
| Phases 30 + 31 are parallel-eligible | Disjoint file ownership: P30 extends `skills/movie-experts/_eval/runner.py` (offline dev tooling, no runtime touch per its module docstring) + adds gate scripts; P31 builds patch-generation pipeline under `~/.hermes/skills/.feedback/` tooling + new modules. They share only the JSON schema contract from P28. Zero file overlap. | Applied 2026-06-24 — ROADMAP critical path notes parallel wave |
| Phase 33 (Integration Close-out) runs LAST | P33 references P28-32 + writes canonical `_shared/v6-feedback-loop-architecture.md` + skills-mapping.yaml `v6_ref_signoffs:` + README + glossary. Must close after all feedback-loop phases ship. Mirrors v5.0 Phase 27 pattern. | Applied 2026-06-24 — ROADMAP critical path annotated |
| EVOL-02 mapped to Phase 32 (not Phase 31) | The candidate-patch generator is invoked BY the Curator's proposal path in practice (CURATE-01 extends curator to propose patches, which uses EVOL-02's diff generator as its engine). Phase 31 builds the review queue + approve/apply mechanics; Phase 32 implements EVOL-02 as the engine Curator calls. Keeps dependency graph clean. | Applied 2026-06-24 — REQUIREMENTS.md traceability + ROADMAP.md coverage table reflect this |
| Hermes core touch accepted (v5→v6 scope expansion) | v6 (unlike v1-v5) modifies `agent/curator.py` (CURATE-01) + adds new ingestion endpoints/watchers (INGEST-02). This is explicitly accepted in PROJECT.md §"Current Milestone: v6.0" Key context. Pure-skill phases still occur but core touch is unavoidable. | Applied 2026-06-24 — P28 + P29 + P32 success criteria all annotate "Hermes-core touch: Yes" |
| FOUND-08 + scope discipline carried from v3.0 onward | Every phase verifies "no new expert_id, no DAG node change, no v5/v4 ref byte-change". P31 SC #5-6 + P33 SC #7-8 explicitly check. | Applied 2026-06-24 — every phase touching bundled SKILL.md has explicit preservation criterion |

### Decisions (carried forward — relevant to v6.0)

| Decision | Rationale | Why relevant to v6.0 |
|----------|-----------|----------------------|
| FOUND-08 frozen rule: expert_id cannot silently rename; aliases required for any rename | v6.0 does NOT rename or create expert_ids, but EVOL pipeline generates patches against bundled SKILL.md — patches must preserve expert_id + related_skills frontmatter byte-for-byte | P31 SC #5 + P33 SC #7 verify "no new expert_id directory created, no frontmatter edit" |
| skills-mapping.yaml is canonical sign-off registry | INTEGRATION-style requirement (P33) targets this file for `v6_ref_signoffs:` section with verified_date + license_status annotations — mirrors v4.0 `v4_ref_signoffs:` + v5.0 `v5_ref_signoffs:` | Phase 33 SC #5 verifies skills-mapping.yaml has new v6 entries with required fields |
| `_eval/runner.py` is offline developer tooling (per its module docstring) | GATE-01 explicitly reuses this harness for patch-vs-baseline; the docstring declares it is NOT imported by Hermes runtime and does NOT call `registry.register`. So extending it for the gate does not constitute Hermes-runtime touch. | Phase 30 is parallel-eligible with P31 on this basis; P30 "Hermes-core touch: No" annotation |
| Curator currently only touches agent-created skills (per `agent/curator.py` module docstring strict invariants) | CURATE-01 extends Curator scope to bundled skills — this breaks the pre-v6 strict invariant. Must be additive (existing agent-created behavior preserved per P32 SC #6 regression test). | Phase 32 SC #6 explicitly requires regression test against pre-v6 curator behavior |
| Glossary H3 bilingual header convention `### Term / 中文术语` | Established in Phase 14 + carried through v4.0 + v5.0. All new v6.0 glossary terms (P33 SC #6: Feedback Ingestion / Knowledge Evolution / Eval Gate / Curator Proposal) must follow bilingual header convention. | Phase 33 SC #6 explicit on convention |
| v4.0 + v5.0 methodology / V8.6 refs are additive knowledge, not replacement | snowflake-method.md / e-konte-format.md / scamper-variations.md (v4.0) + dreamina-cli-baseline.md / v86-pipeline-mapping.md (v5.0) byte-intact across v6.0. EVOL pipeline patches are ADDITIVE only (per EVOL-02 scope discipline). | P31 SC #6 + P33 SC #8 explicitly verify byte-intact preservation |

### Blockers / Risks (v6.0 — new)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **kais-aigc-platform接入方式选择 (file/HTTP/webhook) blocks INGEST-02** | MEDIUM | HIGH (INGEST-02 is must-have MVP) | Decision explicitly deferred to plan-phase per ROADMAP P28 scope note. P28 MUST ship a working ingest path regardless of transport choice. If plan-phase cannot decide, default to file-exchange (simplest). |
| **Curator scope expansion breaks pre-v6 agent-created skill behavior** | MEDIUM | HIGH (regression in shipped v1-v5 curator) | P32 SC #6 requires regression test against pre-v6 curator behavior. Extension is ADDITIVE — existing deterministic inactivity transitions + consolidation pass must continue unchanged. |
| **Eval gate false-rejects valid patches (threshold too tight)** | MEDIUM | MEDIUM (slows learning loop) | δ=0.3 + per-prompt 1.0 thresholds are defaults, configurable. P30 SC #2-4 require rejection logged with score delta so operator can tune. A/B double-blind (GATE-03) gives statistical signal beyond raw threshold. |
| **EVOL-02 unified-diff generation breaks bilingual EN+CN structure** | MEDIUM | HIGH (corrupts shipped SKILL.md style) | P32 SC #2 explicitly requires "preserving EN-structure + CN-prose bilingual style". Human-in-loop approve (EVOL-04, non-bypassable for bundled) catches style breaks before apply. |
| **Feedback PII / sensitive content in user-submitted corrections** | LOW | MEDIUM (v6 assumes trusted operator environment) | FUTURE-V6-06 (deferred to v7) — auto-redaction not in v6 scope. v6 assumes operator environment is trusted per PROJECT.md. |
| **Feedback store grows unbounded over time** | LOW | LOW (jsonl append-only) | Time-decay weighting (STORE-03) downweights old feedback but does not delete. Operator can manually prune `~/.hermes/skills/.feedback/`. Future auto-prune is FUTURE-V6 scope. |
| **v4.0/v5.0 refs accidentally overwritten by EVOL patches** | LOW | HIGH (would break v4.0 + v5.0 audit PASSED state) | P31 SC #6 + P33 SC #8 explicitly verify byte-intact preservation via sha256 snapshot diff. EVOL-02 patches are ADDITIVE only per scope discipline. |

### Blockers / Risks (carried from v1-v5)

**Inherited from v1 (still ongoing):**

- ⚠ Platform guideline drift — refs use `verified_date` + 90-day refresh cadence
- ⚠ 短剧 sample copyright — fair-use + LICENSE.md per ref
- ⚠ LLM-as-judge invalidity — single-judge bias; v6 reuses single-judge for eval gate (multi-judge ensemble deferred to FUTURE-V6-05)

**Inherited from v3.0 audit (deferred items, NOT in v6.0 scope):**

- W-1: creative_source → topic_curator dead ref (pre-existing v2.0)
- W-2: character_designer missing Phase 17 inheritance body annotation
- W-3: 32 pre-existing v2.0 bidirectional asymmetries
- W-4: Frontmatter `status:` field path inconsistency (documentation drift)
- VALIDATE-D1: quality_gate gap — canonical 16th DAG node has no SKILL.md
- FUTURE-09: production expert (disposition: deferred)

These are documented in `.planning/v3.0-MILESTONE-AUDIT.md` and explicitly excluded from v6.0 scope per REQUIREMENTS.md §"Future Requirements" + §"Out of Scope".

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v6.0" — milestone goal + scope expansion rationale
2. `.planning/ROADMAP.md` — 6 phases (28-33), success criteria, coverage table, critical path
3. `.planning/REQUIREMENTS.md` — 26 requirements with REQ-IDs + Traceability table (all mapped)
4. `agent/curator.py` (current implementation, lines 1-150 for invariants + lines 1428+ for `run_curator_review`) — v6 extends this
5. `skills/movie-experts/_eval/runner.py` (existing MT-Bench position-swap harness) — Phase 30 reuses this as eval gate
6. `.planning/research/v2-pipeline-design/skills-mapping.yaml` — canonical expert mapping baseline (v3.0 + v4.0 + v5.0 signoffs; v6 adds `v6_ref_signoffs:` in P33)

**Next action:** `/gsd:plan-phase 28` to plan Feedback Ingestion MVP (covers INGEST-01..05, ships core functional guarantee, unblocks P29 + P30 + P31).

**Resume from interrupted phase:** Read `.planning/phases/28-feedback-ingestion-mvp/` once it exists (created by `/gsd:plan-phase 28`).

---

*Last updated: 2026-06-24 — v6.0 Self-Evolution & Feedback Loop roadmap + state initialized (6 phases continuing from v5.0 Phase 27, 26/26 reqs mapped, Phase 28 ready for planning). Scope expansion from v5 accepted: touches Hermes core (agent/curator.py extension + feedback ingestion infra).*

## Operator Next Steps

- Plan Phase 28: `/gsd:plan-phase 28` (Feedback Ingestion MVP — covers INGEST-01..05, must-have)
- Review ROADMAP.md critical path to confirm Phase 30/31 parallel wave is acceptable
- Confirm EVOL-02 → Phase 32 mapping (Curator invokes diff generator) is acceptable before planning P31/P32
