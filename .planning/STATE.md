---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Methodology Backfill
status: planning
last_updated: "2026-06-17T16:00:00.000Z"
last_activity: 2026-06-17
progress:
  total_phases: 3
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
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`, `.planning/research/methodology-gap-analysis-2026-06-17.md`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** v4.0 Methodology Backfill — Phase 19 (Snowflake Method Integration) ready for planning

## Current Position

Phase: 19 (Snowflake Method Integration) — Not started (awaiting `/gsd:plan-phase 19`)
Plan: —
Status: Roadmap written 2026-06-17; ready for phase planning
Last activity: 2026-06-17 — v4.0 ROADMAP.md + STATE.md initialized by roadmapper

### Progress

```
v1 milestone:                  [██████████] 100% Complete (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP milestone:           [██████████] 100% Complete (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG Alignment:  [██████████] 100% Complete (Phases 13-18, shipped 2026-06-17)

v4.0 Methodology Backfill:
  Phase 19 (Snowflake Method Integration)  [          ] 0% Not started
  Phase 20 (E-Konte Integration)           [          ] 0% Not started
  Phase 21 (SCAMPER + DOC close-out)       [          ] 0% Not started
```

### Phase Statuses (v4.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 19 | Snowflake Method Integration | Not started | Covers SNOWFLAKE-01..04. Touches creative_source + screenplay + glossary. LOW difficulty per gap-analysis §5.1. |
| 20 | E-Konte Integration | Not started | Covers EKONTE-01..04. Touches cinematographer + visual_executor + glossary. MEDIUM difficulty per gap-analysis §5.2. |
| 21 | SCAMPER Variation Engine + DOC close-out | Not started | Covers SCAMPER-01..04 + DOC-01 + DOC-02. Touches style_genome + hook_retention + glossary + README + skills-mapping.yaml. LOW-MEDIUM difficulty per gap-analysis §5.3. Must run LAST (DOC-01/02 cross-cut all 3 new refs). |

### Critical Path

```
Phase 19 (Snowflake)  ─┐
                        ├─→  Phase 21 (SCAMPER + DOC)  ← DOC-01/02 cross-cutting, must run last
Phase 20 (E-Konte)    ─┘
```

Phases 19 + 20 are independent (touch disjoint expert directories). Phase 21 contains DOC-01/02 (cross-cutting, references all 3 new refs) so must execute after 19+20. Recommended: 19 → 20 → 21 in priority order from gap-analysis §5.

## Quick Tasks Completed

| Quick ID | Date | Slug | Description | Deliverable |
|----------|------|------|-------------|-------------|
| 260617-wgz | 2026-06-17 | write-gap-analysis-doc-comparing-creativ | Gap-analysis 对照调研报告 §7.2 6 阶段蓝图 vs movie-experts 实际覆盖;高 ROI 缺口排序(雪花法 / E-Konte / SCAMPER) | `.planning/research/methodology-gap-analysis-2026-06-17.md` |

## Performance Metrics (v4.0)

- v4.0 phases total: 3 (Phases 19-21, continuing from v3.0 phase 18)
- v4.0 phases completed: 0
- v4.0 requirements total: 14
- v4.0 requirements mapped: 14 / 14 ✓
- v4.0 requirements orphaned: 0
- v4.0 plans completed: 0 / TBD (per phase)
- Deliverable form: PURE SKILL CONTENT — zero code changes to Hermes core; all deliverables under `skills/movie-experts/` + cross-cutting doc updates to `skills-mapping.yaml`

## Accumulated Context

### v4.0 Goal Restatement

把 2026-06-17 gap-analysis 识别的 3 个 ⭐⭐⭐⭐⭐ AI 化方法论缺口补进 `skills/movie-experts/`:
1. **Snowflake Method** (过程) — 接入 creative_source + screenplay,填补 StoryKernel → beat-sheet 的展开塌陷
2. **E-Konte 絵コンテ** (视觉中间格式) — 接入 cinematographer + visual_executor,填补 storyboard_designer deprecated 后的东方分镜真空
3. **SCAMPER** (变体引擎) — 接入 style_genome + hook_retention,填补 style_blend 单一输出的变体生成缺口

三者互补不重叠,各自接入点独立。**不重构**核心架构,不创建新 expert_id,不触发 FOUND-08 alias 流程。

### Decisions (v4.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 3 phases continuing from v3.0 phase 18 (19, 20, 21) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only | Applied 2026-06-17 — ROADMAP.md phase numbering 19/20/21 |
| Each phase = 1 new ref + 1-2 SKILL.md body updates + glossary词条 + cross-cutting edges | Per PROJECT.md §"Current Milestone: v4.0" scope boundary: only incremental methodology mounting, no architecture refactor | Applied 2026-06-17 — per-phase requirement clusters validated against scope |
| DOC-01 + DOC-02 placed in Phase 21 (close-out), not Phase 19 | DOC requirements cross-cut all 3 new refs (snowflake-method.md from Phase 19 + e-konte-format.md from Phase 20 + scamper-variations.md from Phase 21); must run after all 3 refs exist | Applied 2026-06-17 — Phase 21 carries SCAMPER-01..04 + DOC-01 + DOC-02 (6 reqs total) |
| Phase 19/20/21 are independent methodology integrations (no hard cross-phase dep) | Each methodology mounts into a distinct expert directory: Snowflake→creative_source+screenplay, E-Konte→cinematographer+visual_executor, SCAMPER→style_genome+hook_retention. No file ownership overlap. | Applied 2026-06-17 — ROADMAP.md critical path notes independence |
| Recommended execution order 19 → 20 → 21 | Matches gap-analysis §5 priority ranking (Snowflake LOW → E-Konte MEDIUM → SCAMPER LOW-MEDIUM difficulty); also matches DOC-01/02 last-placement constraint naturally | Applied 2026-06-17 — ROADMAP.md critical path annotated |
| Phase 21 NOT split into SCAMPER-only + DOC-only phases | Granularity=standard; DOC reqs are 2-line inventory updates (corpus tree + skills-mapping.yaml sign-off), not substantial enough to warrant separate phase | Applied 2026-06-17 — Phase 21 groups SCAMPER-01..04 + DOC-01..02 |
| FOUND-08 alias flow NOT triggered | All 3 phases mount new refs into existing active expert_ids (creative_source, screenplay, cinematographer, visual_executor, style_genome, hook_retention); no new expert_id created, no rename, no merge | Applied 2026-06-17 — ROADMAP.md success criterion #5 per phase explicitly checks "no new expert_id directory created" |
| Glossary 词条 split: 4 (Snowflake) + 4 (E-Konte) + 8 (SCAMPER) = 16 new H3 entries total | Each phase's glossary 词条 are methodology-specific; no overlap | Applied 2026-06-17 — glossary counts per phase validated |
| Phase 21 success criterion #5 (README corpus tree updated) includes ALL 3 new refs | Even though snowflake-method.md + e-konte-format.md belong to Phase 19/20 respectively, the README corpus tree update is a single atomic edit that must list all 3 together for consistency | Applied 2026-06-17 — Phase 21 SC #5 lists all 3 refs explicitly |

### Decisions (v3.0 carry-forward — relevant to v4.0)

| Decision | Rationale | Why relevant to v4.0 |
|----------|-----------|----------------------|
| Self-registration via `metadata.hermes.related_skills` + `expert_id` + `metrics` | All v4.0 SKILL.md body updates must continue using this convention (PROJECT.md §"Skill File Conventions") | Each Phase 19/20/21 SKILL.md body edit must respect existing frontmatter conventions; no new fields invented |
| FOUND-08 frozen rule: expert_id cannot silently rename; aliases required for any rename | v4.0 does NOT rename or create expert_ids, but the rule still constrains: body edits must not break existing alias chains | ROADMAP per-phase criterion #5 verifies "no architecture break" |
| Glossary H3 bilingual header convention `### Term / 中文术语` | Established in Phase 14 (visual_executor / 视觉执行专家) + Phase 15 (audio_pipeline / 音频管线专家) | All 16 new v4.0 glossary 词条 must follow bilingual header convention |
| Mermaid DAG is canonical source-of-truth for topology (Phase 18) | v4.0 explicitly does NOT add DAG nodes — all 3 methodologies are internal refs of existing experts | Phase 21 SC #5 verifies "Mermaid DAG remains unchanged" |
| skills-mapping.yaml is canonical sign-off registry | DOC-02 requirement specifically targets this file for verified_date + License status annotations | Phase 21 SC #6 verifies skills-mapping.yaml has new entries with required fields |

### Blockers / Risks (v4.0 — new)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **E-Konte 今敏级 vs 普通 E-Konte scope confusion** | MEDIUM | HIGH (5-10×工作量差异 per gap-analysis §5.2.2) | EKONTE-01 success criterion explicitly anchors to "5 annotation layers + 今敏红辣椒 case + 宫崎骏吉卜力 practice" — NOT今敏级 hyper-detailed storyboard. SKILL.md body must declare scope = 普通 E-Konte format only. |
| **SCAMPER × style_blend boundary confusion** | MEDIUM | MEDIUM (用户可能误以为 SCAMPER replaces style_blend) | SCAMPER-02 success criterion explicitly declares "SCAMPER stacked ON TOP of style_blend" (变体引擎叠加, not replacement). Glossary SCAMPER 词条 must cross-reference style_blend. |
| **Snowflake step selection ambiguity (10 steps vs short-drama缩放后子集)** | LOW | MEDIUM (短剧 60-180s 单集可能容不下全部 10 步) | SNOWFLAKE-01 explicitly requires "短剧 60-180s 单集 + 10-80 集连续剧形态做 step 缩放" — ref must declare缩放规则, not skip steps silently. |
| **Cross-skill related_skills edge drift** | LOW | LOW | Each phase's SC #5 verifies "no edges removed"; FOUND-08 backward-compat honored. visual_executor + hook_retention consume new methodology outputs without needing edge rewires (SCAMPER output flows through style_genome → hook_retention existing edge). |
| **Ref LICENSE/copyright not stamped** | MEDIUM | HIGH (PROJECT.md §"Copyright" constraint) | Phase 21 SC #6 explicitly requires skills-mapping.yaml sign-off with License status; gap-analysis §5.2.1 case references must use fair-use quotations only. |
| **Storyboard_designer deprecation mistaken as "resurrected" via E-Konte** | LOW | MEDIUM | Phase 20 SC #5 explicitly verifies "storyboard_designer deprecation state preserved — E-Konte lives inside cinematographer.composition_lock, does NOT resurrect storyboard_designer". |

### Blockers / Risks (carried from v1-v3)

**Inherited from v1 (still ongoing):**

- ⚠ Platform guideline drift — refs use `verified_date` + 90-day refresh cadence
- ⚠ 短剧 sample copyright — fair-use + LICENSE.md per ref
- ⚠ LLM-as-judge invalidity — Phase 6 live run deferred to operator

**Inherited from v3.0 audit (deferred items, NOT in v4.0 scope):**

- W-1: creative_source → topic_curator dead ref (pre-existing v2.0)
- W-2: character_designer missing Phase 17 inheritance body annotation
- W-3: 32 pre-existing v2.0 bidirectional asymmetries
- W-4: Frontmatter `status:` field path inconsistency (documentation drift)
- VALIDATE-D1: quality_gate gap — canonical 16th DAG node has no SKILL.md
- FUTURE-09: production expert (disposition: deferred)

These are documented in `.planning/v3.0-MILESTONE-AUDIT.md` and explicitly excluded from v4.0 scope per REQUIREMENTS.md §"Future Requirements".

### v4.0 Source Artifact

**Canonical source:** `.planning/research/methodology-gap-analysis-2026-06-17.md` (quick task `260617-wgz`)

Key takeaways informing v4.0 ROADMAP:

- §3 coverage matrix: 6-stage blueprint has 1/6 partial (Snyder-only), 2/6 path-divergent (Bourdieu / visual identity), 3/6 vacuum (E-Konte / SCAMPER / meta-process)
- §5 high-ROI ranking: Snowflake ⭐⭐⭐⭐⭐ LOW → E-Konte ⭐⭐⭐⭐⭐ MEDIUM → SCAMPER ⭐⭐⭐⭐⭐ LOW-MEDIUM (matches Phase 19/20/21 order)
- §4 fact correction: McKee is NOT a planning baseline (already in-place); future planning must not assume "still need to introduce McKee"
- §7 独创方法论: 8 methodologies already in-place (Tan / McMahon / Smith / Bourdieu / Sarris-Truffaut-Bordwell / CN 短剧公式 / Plutchik / 疲劳曲线) — these are NOT to be re-introduced in v4.0
- §8 non-action decision: gap-analysis itself does NOT start a phase; v4.0 milestone was launched by operator decision after reading the analysis

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v4.0" — milestone goal + scope boundary
2. `.planning/ROADMAP.md` — 3 phases, success criteria, coverage table
3. `.planning/REQUIREMENTS.md` — 14 requirements with REQ-IDs + Traceability table
4. `.planning/research/methodology-gap-analysis-2026-06-17.md` — source artifact (§3 coverage matrix + §5 priority ranking + §7 独创方法论 in-place list)

**Next action:** `/gsd:plan-phase 19` to plan Snowflake Method Integration (creative_source + screenplay + glossary, 4 requirements).

**Resume from interrupted phase:** Read `.planning/phases/19-snowflake-method-integration/` once it exists (created by `/gsd:plan-phase 19`).

---

*Last updated: 2026-06-17 — v4.0 Methodology Backfill roadmap + state initialized (3 phases, 14 reqs mapped, Phase 19 ready for planning)*
