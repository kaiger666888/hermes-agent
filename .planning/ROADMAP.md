# Roadmap: Movie-Experts Suite v2 — 短剧/微电影创作专家增强

**Project:** RAG-augmented movie-expert skill suite (MESV2)
**Current milestone:** v4.0 — Methodology Backfill (Snowflake / E-Konte / SCAMPER)
**Phases:** 3 (Phases 19-21, continuing from v3.0)
**Started:** 2026-06-17

---

## Milestones

- ✅ **v1 — Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15) — [Full archive](./milestones/v1-ROADMAP.md)
- ✅ **v2.0 PRFP — Pipeline Redesign from First Principles** — Phases 7-12 (shipped 2026-06-16) — design suite at `.planning/research/v2-pipeline-design/`
- ✅ **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (shipped 2026-06-17) — [Full archive](./milestones/v3.0-ROADMAP.md) · [Audit](./v3.0-MILESTONE-AUDIT.md)
- 🚧 **v4.0 Methodology Backfill** — Phases 19-21 (in planning) — Source: [gap-analysis](./research/methodology-gap-analysis-2026-06-17.md)

---

## v4.0 Overview

**v4.0 Methodology Backfill** fills the three ⭐⭐⭐⭐⭐ AI-suitability methodology gaps identified in the 2026-06-17 gap-analysis: **Snowflake Method** (process — fills StoryKernel → beat-sheet expansion collapse), **E-Konte 絵コンテ** (visual intermediate format — fills the storyboard_designer-deprecated 东方分镜 vacuum), and **SCAMPER** (variation engine — fills the single-output style_blend gap with a 7-verb generator). Each phase is a self-contained methodology integration into existing active experts — **no new expert_id created, no DAG node added, no core architecture refactor**. 3 phases, 14 requirements, all visible as increments to `skills/movie-experts/` content.

---

## Phases

- [ ] **Phase 19: Snowflake Method Integration** — Randy Ingermanson 雪花法 10 步递进管线接入 creative_source + screenplay,填补 StoryKernel → Snyder 15-beat 的展开塌陷
- [ ] **Phase 20: E-Konte Integration** — 日本动画工业 E-Konte 分镜格式接入 cinematographer + visual_executor,填补 storyboard_designer deprecated 后的东方分镜真空
- [ ] **Phase 21: SCAMPER Variation Engine + DOC close-out** — Bob Eberle SCAMPER 7 动词变体引擎接入 style_genome + hook_retention,补全 v4.0 跨切文档(README + skills-mapping sign-off)

---

## Phase Details

### Phase 19: Snowflake Method Integration

**Goal:** Users of `creative_source` and `screenplay` experts see the StoryKernel → beat-sheet pipeline expanded through Ingermanson's 10-step Snowflake Method, with the kernel-to-beat "one-hop collapse" replaced by a structured 5-step展开 (steps 2-6) producing intermediate artifacts that screenplay can consume as scaffold.

**Depends on**: Nothing (first phase of v4.0; no cross-phase dependency — Phase 19/20/21 are independent methodology integrations but recommended in priority order per gap-analysis §5)

**Requirements**: SNOWFLAKE-01, SNOWFLAKE-02, SNOWFLAKE-03, SNOWFLAKE-04

**Success Criteria** (what must be TRUE):
  1. **File exists & is non-trivial:** `skills/movie-experts/creative_source/references/snowflake-method.md` exists, ≥ 200 lines, covers all 10 Ingermanson steps with short-drama (60-180s single ep) and 短剧 10-80 ep serialization step-scaling, and includes an explicit StoryKernel-to-Snowflake bridge protocol
  2. **creative_source SKILL.md references snowflake in body:** The body of `skills/movie-experts/creative_source/SKILL.md` calls out the Snowflake expansion chain (StoryKernel → Snowflake-3 [角色概要] → Snowflake-4 [一页大纲] → 交付 screenplay), with at least one explicit 调用点 annotation and an output schema declaration
  3. **screenplay SKILL.md consumes Snowflake output:** The body of `skills/movie-experts/screenplay/SKILL.md` has a new sub-step before Beat Planning that consumes Snowflake-4 一页大纲 as input scaffold, with an explicit field-mapping table (Snowflake 段落 ↔ Snyder beat 集; Snowflake 灾难节点 ↔ Catalyst + Midpoint + All Is Lost)
  4. **Glossary is extended:** `skills/movie-experts/_shared/glossary.md` contains 4 new H3 entries — `Snowflake Method`, `Story Spine`, `Premise Sentence`, `Scene List` — each with EN↔CN bilingual definitions and Ingermanson 2000s 出处标注
  5. **No architecture break:** No new expert_id directory created; FOUND-08 backward-compat rule honored (creative_source + screenplay expert_id unchanged); no `related_skills` edge removed

**Plans**: TBD

### Phase 20: E-Konte Integration

**Goal:** Users of `cinematographer` and `visual_executor` experts see E-Konte (絵コンテ) as a new intermediate-format option in the cinematography pipeline, with the 5-layer annotation system (场景布局 / 镜头角度运动 / 角色位置表情动作 / 对白音效 / 时间帧数) explicitly contrasted with the existing Western Mascelli 8-level + 180°/30° axis rules so AI can choose东方分镜 grammar without losing Western axis compatibility.

**Depends on**: Nothing (independent of Phase 19; recommended second to follow gap-analysis §5 priority order)

**Requirements**: EKONTE-01, EKONTE-02, EKONTE-03, EKONTE-04

**Success Criteria** (what must be TRUE):
  1. **File exists & is non-trivial:** `skills/movie-experts/cinematographer/references/e-konte-format.md` exists, ≥ 200 lines, covers the 5 E-Konte annotation layers, includes 今敏《红辣椒》一年半分镜 + 宫崎骏吉卜力 practice cases, and contains a comparison table E-Konte vs Western storyboard (Mascelli/Arijon)
  2. **cinematographer SKILL.md declares E-Konte under composition_lock:** The body of `skills/movie-experts/cinematographer/SKILL.md` adds a sub-step "E-Konte 作为中间格式输出" under `composition_lock`, with explicit declaration of E-Konte's relationship to existing Mascelli 8-level shot scale + 180°/30° axis rules (东方分镜语法 vs 西方轴线传统 — complementary, not substitutive)
  3. **visual_executor SKILL.md consumes E-Konte fields:** The body of `skills/movie-experts/visual_executor/SKILL.md` declares how it extracts fields from E-Konte's 5 layers (character pose / camera motion / duration) to feed the drawer/animator sub_steps, and the existing `related_skills` graph remains stable (no edges removed, FOUND-08 honored)
  4. **Glossary is extended:** `skills/movie-experts/_shared/glossary.md` contains 4 new H3 entries — `E-Konte / 絵コンテ`, `Layout`, `ト書き (stage direction)`, `絵切り (cut transition)` — each with EN↔CN bilingual definitions and 日本动画工业体系 出处标注
  5. **No architecture break:** No new expert_id directory created; cinematographer + visual_executor expert_id unchanged; `storyboard_designer` deprecation state preserved (E-Konte lives inside cinematographer.composition_lock, does NOT resurrect storyboard_designer)

**Plans**: TBD

### Phase 21: SCAMPER Variation Engine + DOC Close-out

**Goal:** Users of `style_genome` and `hook_retention` experts see SCAMPER as a systematic 7-verb variation engine producing 35 short-drama variation seeds (7 verbs × 5 genre×mood×pacing×cast×runtime combinations), and v4.0 closes with cross-cutting documentation (README corpus tree + skills-mapping.yaml sign-off) listing all three new refs with verified_date + License status.

**Depends on**: Nothing (independent of Phases 19+20; recommended last because DOC-01 + DOC-02 are cross-cutting — they touch all 3 new refs including snowflake-method.md and e-konte-format.md from prior phases)

**Requirements**: SCAMPER-01, SCAMPER-02, SCAMPER-03, SCAMPER-04, DOC-01, DOC-02

**Success Criteria** (what must be TRUE):
  1. **File exists & is non-trivial:** `skills/movie-experts/style_genome/references/scamper-variations.md` exists, ≥ 200 lines, covers Bob Eberle's 7 SCAMPER verbs, provides 35 short-drama variation recipes (7 verbs × 5 genre×mood×pacing×cast×runtime combinations), includes an LLM prompt template + output schema
  2. **style_genome SKILL.md layers SCAMPER on style_blend:** The body of `skills/movie-experts/style_genome/SKILL.md` declares SCAMPER as a variation engine stacked on top of `style_blend` (style_blend 输入 → SCAMPER 7 动词展开 → 7 候选 style_blend 输出 → 下游或用户选择), with explicit declaration of the relationship to auteur-theory and genre-dna
  3. **hook_retention SKILL.md consumes SCAMPER × 5 formula cross-table:** The body of `skills/movie-experts/hook_retention/SKILL.md` contains a new "SCAMPER × 5 爆款公式" cross-table (7 verbs × 5 short-drama爆款公式 = 35 hook 变体种子), enabling hook_retention to consume candidate variation seeds from style_genome's SCAMPER output
  4. **Glossary is extended:** `skills/movie-experts/_shared/glossary.md` contains 8 new H3 entries — `SCAMPER` + 7 verbs (Substitute / Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse) — each with EN↔CN bilingual definitions and Eberle 1971 / based on Osborn 出处标注
  5. **README corpus tree updated:** `skills/movie-experts/README.md` lists all 3 new refs (`snowflake-method.md` / `e-konte-format.md` / `scamper-variations.md`) in the corpus tree / inventory; Mermaid DAG remains unchanged (3 methodologies are internal refs of existing experts, no new DAG nodes added)
  6. **skills-mapping.yaml sign-off recorded:** `.planning/research/v2-pipeline-design/skills-mapping.yaml` (or equivalent sign-off file) has new entries for the 3 new refs with `verified_date: 2026-06-17` + 出处 source + License status

**Plans**: TBD

---

## Coverage Validation

**v4.0 requirements:** 14 total (SNOWFLAKE × 4 + EKONTE × 4 + SCAMPER × 4 + DOC × 2)
**Mapped to phases:** 14 / 14 ✓
**Unmapped:** 0
**Orphans:** 0
**Duplicates:** 0

| Requirement | Phase | Status |
|-------------|-------|--------|
| SNOWFLAKE-01 | 19 | Pending |
| SNOWFLAKE-02 | 19 | Pending |
| SNOWFLAKE-03 | 19 | Pending |
| SNOWFLAKE-04 | 19 | Pending |
| EKONTE-01 | 20 | Pending |
| EKONTE-02 | 20 | Pending |
| EKONTE-03 | 20 | Pending |
| EKONTE-04 | 20 | Pending |
| SCAMPER-01 | 21 | Pending |
| SCAMPER-02 | 21 | Pending |
| SCAMPER-03 | 21 | Pending |
| SCAMPER-04 | 21 | Pending |
| DOC-01 | 21 | Pending |
| DOC-02 | 21 | Pending |

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 19. Snowflake Method Integration | 0/TBD | Not started | - |
| 20. E-Konte Integration | 0/TBD | Not started | - |
| 21. SCAMPER Variation Engine + DOC close-out | 0/TBD | Not started | - |

---

## Critical Path

```
Phase 19 (Snowflake)  ─┐
                        ├─→  Phase 21 (SCAMPER + DOC)  ← DOC-01/02 cross-cutting, must run last
Phase 20 (E-Konte)    ─┘
```

**Note:** Phases 19 and 20 are independent (touch different expert directories). Phase 21 contains the cross-cutting DOC requirements (DOC-01/02) which reference all 3 new refs, so Phase 21 must execute after at least 19+20 have produced their ref files. Recommended execution order: **19 → 20 → 21** to match gap-analysis §5 priority ranking (Snowflake ⭐⭐⭐⭐⭐ LOW difficulty → E-Konte ⭐⭐⭐⭐⭐ MEDIUM difficulty → SCAMPER ⭐⭐⭐⭐⭐ LOW-MEDIUM difficulty).

---

*Last updated: 2026-06-17 — v4.0 Methodology Backfill roadmap created (3 phases, 14 requirements mapped, continuing from v3.0 phase 18)*
