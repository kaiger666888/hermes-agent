# Roadmap: Movie-Experts Suite v2 — 短剧/微电影创作专家增强

**Project:** RAG-augmented movie-expert skill suite (MESV2)
**Current milestone:** v5.0 — kais-movie-agent V8.6 Adaptation (started 2026-06-19)
**Phase numbering:** Continues from v4.0 (ended at Phase 21). v5.0 phases: 22-27.

---

## Milestones

- ✅ **v1 — Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15) — [Full archive](./milestones/v1-ROADMAP.md)
- ✅ **v2.0 PRFP — Pipeline Redesign from First Principles** — Phases 7-12 (shipped 2026-06-16) — design suite at `.planning/research/v2-pipeline-design/`
- ✅ **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (shipped 2026-06-17) — [Full archive](./milestones/v3.0-ROADMAP.md) · [Audit](./milestones/v3.0-MILESTONE-AUDIT.md)
- ✅ **v4.0 Methodology Backfill** — Phases 19-21 (shipped 2026-06-18) — [Full archive](./milestones/v4.0-ROADMAP.md) · [Audit](./milestones/v4.0-MILESTONE-AUDIT.md)
- 🚧 **v5.0 — kais-movie-agent V8.6 Adaptation** — Phases 22-27 (started 2026-06-19)

---

## v5.0 Summary

**v5.0 — kais-movie-agent V8.6 Adaptation** syncs hermes-agent's 16 active movie-experts to kais-movie-agent V8.4-V8.6 (commits `4fb57b4` V8.4 + `c22867d` V8.5 + `e41fa68` V8.6, all 2026-06-18). The consumer-side kais-movie-agent pipeline underwent three same-day shifts: (1) V8.4 expert mapping full update (drawer+animator→visual_executor, audio N:1 merge, continuity→continuity_auditor, scene_builder/storyboard_designer→cinematographer, NEW prompt_injector); (2) V8.5 dreamina CLI replacing jimeng-client + Step 7 角色资产库完整化 (L1-L4); (3) V8.6 管线精简 25→13 步, 审核门 12→8 个, Expert 调用 15→10 次. The gap is internal knowledge layer — hermes-agent experts still emit pre-V8.4 assumptions.

6 phases, 30 requirements. Pure knowledge-layer increment (mirrors v4.0 scope discipline): no new expert_id, no DAG node change, no core architecture refactor. v4.0 methodology refs (snowflake-method.md / e-konte-format.md / scamper-variations.md) PRESERVED, not replaced — V8.6 knowledge ADDED alongside.

---

## Phases

- [ ] **Phase 22: dreamina CLI 知识基线** — Shared ref documenting dreamina CLI as sole image/video tool
- [ ] **Phase 23: 视觉系 V8.6 sync** — visual_executor + prompt_injector + character_designer + cinematographer + colorist + style_genome
- [ ] **Phase 24: 文学系 V8.6 sync** — hook_retention + creative_source + screenplay + script_auditor
- [ ] **Phase 25: 听觉系 V8.6 sync** — audio_pipeline + 6 sub-step stubs
- [ ] **Phase 26: 审核系 V8.6 sync** — continuity_auditor + compliance_gate + editor + theory_critic
- [ ] **Phase 27: 集成 (Integration close-out)** — _shared/v86-pipeline-mapping.md + skills-mapping.yaml v5 sign-off + README corpus tree + glossary

---

## Phase Details

### Phase 22: dreamina CLI 知识基线
**Goal**: Create the cross-expert shared reference documenting dreamina CLI as the canonical image/video generation tool per kais-movie-agent V8.5 — unblocking downstream expert V8.6 sync phases (P23 + P25 both reference this baseline).
**Depends on**: Nothing (first phase of v5.0; produces `_shared/dreamina-cli-baseline.md` referenced by P23 VISUAL-02 + P25 AUDIO-02)
**Requirements**: DREAMINA-01, DREAMINA-02, DREAMINA-03, DREAMINA-04, DREAMINA-05
**Success Criteria** (what must be TRUE):
  1. `skills/movie-experts/_shared/dreamina-cli-baseline.md` exists with `verified_date: 2026-06-19` documenting all 6 dreamina CLI sub-commands (text2image / image2image / multimodal2video / multiframe2video / frames2video / image_upscale) per kais-movie-agent V8.5 SKILL.md
  2. dreamina-cli-baseline.md documents the L1/L2/L3/L4 character asset library strategy (L1 面部锚点→角色参考 / L2 造型卡片→智能参考 / L3 姿势包 / L4 表情标定) per V8.5 角色资产库完整化
  3. dreamina-cli-baseline.md documents the async poll pattern (`--poll 0` submit + `dreamina query_result --submit_id` poll + `aria2c URL` download) per V8.5 integration
  4. dreamina-cli-baseline.md documents the gold-team fallback path (gold-team now video/TTS/3D only; image generation does NOT route through gold-team per V8.5)
  5. dreamina-cli-baseline.md documents explicit deprecation notice for jimeng-client.js (marked 废弃 in V8.5, retained in lib/ for compat reference only)
  6. dreamina-cli-baseline.md has LICENSE.md attribution row with license_status declared
  7. FOUND-08 preservation: no new expert_id directory created under `skills/movie-experts/`, no DAG node change, no rename — `_shared/` ref only
**Plans**: TBD

### Phase 23: 视觉系 V8.6 sync
**Goal**: Update the 6 visual系 experts (visual_executor / prompt_injector / character_designer / cinematographer / colorist / style_genome) to reference V8.6 Step positions (Step 4 角色资产 / Step 5 场景 / Step 6 运镜+终审 / Step 7 视觉种子+风格化) and document dreamina CLI integration parameters, so they stop emitting pre-V8.4 assumptions.
**Depends on**: Phase 22 (consumes `_shared/dreamina-cli-baseline.md` for VISUAL-02 + VISUAL-03 dreamina CLI parameters)
**Requirements**: VISUAL-01, VISUAL-02, VISUAL-03, VISUAL-04, VISUAL-05, VISUAL-06, VISUAL-07
**Success Criteria** (what must be TRUE):
  1. `visual_executor/SKILL.md` references V8.6 Step 4 (主角设计+资产库, alongside character_designer) AND Step 5 (场景设计, alongside cinematographer + style_genome) AND Step 7 (视觉种子+风格化, alongside prompt_injector + style_genome + colorist)
  2. `visual_executor/SKILL.md` documents dreamina CLI integration — drawer sub-step uses `image2image` with L1+L2 references; animator sub-step uses `multimodal2video` / `multiframe2video` / `frames2video` per V8.5 (links to `_shared/dreamina-cli-baseline.md`)
  3. `prompt_injector/SKILL.md` documents its V8.4-NEW role as Step 7 pre-node translating visual_intent + style_genome + character_assets into dreamina-compatible model_prompts (per V8.4 §2 of update notes)
  4. `character_designer/SKILL.md` references V8.6 Step 4 AND documents L1/L2/L3/L4 asset output format feeding downstream visual_executor + dreamina CLI
  5. `cinematographer/SKILL.md` references V8.6 Step 5 (场景设计) AND Step 6 (运镜+终审, alongside screenplay + script_auditor) AND Step 8 (运镜+节奏 alongside editor); explicitly preserves V8.4 folding of scene_builder + storyboard_designer (no resurrection)
  6. `colorist/SKILL.md` references V8.6 Step 7 (视觉种子+风格化) co-role with visual_executor + prompt_injector + style_genome
  7. `style_genome/SKILL.md` references V8.6 Step 2.5 (前置 style_genome after story framework per V8.4 §3) AND Step 5 (场景设计 alongside cinematographer + visual_executor) AND Step 7 (视觉种子+风格化)
  8. FOUND-08 preservation: no new expert_id directory created, no DAG node change, no rename — only body edits to existing SKILL.md files; v4.0 methodology refs (e-konte-format.md under cinematographer, scamper-variations.md under style_genome) PRESERVED not replaced
**Plans**: TBD
**UI hint**: yes

### Phase 24: 文学系 V8.6 sync
**Goal**: Update the 4 literary系 experts (hook_retention / creative_source / screenplay / script_auditor) to reference V8.6 Step positions (Step 1 hook+主题 atomic / Step 2 框架+大纲 atomic / Step 3 剧本+审计 atomic), aligning I/O contracts for the new atomic operations.
**Depends on**: Phase 22 (soft dep — uses dreamina-cli-baseline.md terminology; can run parallel to P23/P25/P26)
**Requirements**: LITERARY-01, LITERARY-02, LITERARY-03, LITERARY-04
**Success Criteria** (what must be TRUE):
  1. `hook_retention/SKILL.md` references V8.6 Step 1 merged role (爆款选题雷达 + 主题生成 in one atomic step, originally Step 1+2 per V8.6 §1) AND preserves V8.4 pre-fronting of style_genome as input
  2. `creative_source/SKILL.md` references V8.6 Step 2 merged role (故事框架+大纲 in one atomic step alongside screenplay, originally Step 2.5+3 per V8.6 §2)
  3. `screenplay/SKILL.md` references V8.6 Step 2 (框架+大纲 alongside creative_source) AND Step 3 (剧本+审计 atomic op alongside script_auditor, originally Step 5+5B+6 per V8.6 §3) AND Step 6 (时空剧本+终审 alongside cinematographer + script_auditor)
  4. `script_auditor/SKILL.md` references V8.6 Step 3 (剧本+审计 atomic op) AND Step 6 (终审) — documents its V8.4 §4 pre-fronting role (Step 5 后 5维定量审计 drives Step 6 选剧本)
  5. FOUND-08 preservation: no new expert_id directory created, no DAG node change — only body edits to existing SKILL.md files; v4.0 methodology ref (snowflake-method.md under creative_source) PRESERVED not replaced
**Plans**: TBD
**UI hint**: yes

### Phase 25: 听觉系 V8.6 sync
**Goal**: Update `audio_pipeline` + 6 sub-step stubs (voicer / composer / foley / mixer / spatial_audio / lip_sync) to reference V8.6 Step positions (Step 7B 声音骨架 / Step 11 BGM+音效+口型统一) and document dreamina CLI `multimodal2video` audio binding, so audio experts align with the V8.6 atomic Step 11 merge.
**Depends on**: Phase 22 (consumes `_shared/dreamina-cli-baseline.md` for AUDIO-02 multimodal2video audio binding)
**Requirements**: AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04
**Success Criteria** (what must be TRUE):
  1. `audio_pipeline/SKILL.md` references V8.6 Step 7B (声音骨架: voicer + composer + foley sub-steps) AND Step 11 merged role (BGM+音效+口型统一 in one atomic step, originally Step 18+17B per V8.6 §6)
  2. `audio_pipeline/SKILL.md` documents dreamina CLI `multimodal2video` audio binding (@Audio N reference syntax per V8.3) when audio assets feed video generation (links to `_shared/dreamina-cli-baseline.md`)
  3. Sub-step stubs (voicer / composer / foley / mixer / spatial_audio / lip_sync) under `audio_pipeline/references/` updated with V8.6 Step position annotations (Step 7B for skeleton, Step 11 for final mix)
  4. `audio_pipeline/SKILL.md` clarifies V8.4 merge boundary — 6 audio experts merged into N:1 audio_pipeline with `sub_steps` preservation per skills-mapping.yaml revisit_resolution Phase 18 v3.0
  5. FOUND-08 preservation: no new expert_id directory created, no DAG node change, no merge re-opening — audio_pipeline N:1 merge boundary from Phase 15 v3.0 preserved
**Plans**: TBD
**UI hint**: yes

### Phase 26: 审核系 V8.6 sync
**Goal**: Update the 4 audit系 experts (continuity_auditor / compliance_gate / editor / theory_critic) to reference V8.6 8-gate structure (down from 12) and document their canonical atomic roles per V8.6 SKILL.md mapping table.
**Depends on**: Phase 22 (soft dep — uses dreamina-cli-baseline.md terminology; can run parallel to P23/P24/P25)
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04
**Success Criteria** (what must be TRUE):
  1. `continuity_auditor/SKILL.md` references V8.6 Step 9 (一致性检查 atomic role) AND documents V8.6 8-gate structure (down from 12) with which gate continuity lives at
  2. `compliance_gate/SKILL.md` documents V8.6 8-gate structure AND which gate compliance review fires at (typically pre-publish gate)
  3. `editor/SKILL.md` references V8.6 Step 8 (运镜+节奏 alongside cinematographer) AND documents V8.4 §6 pre-fronting role (剪辑节奏前置决定镜头数/时长/转场)
  4. `theory_critic/SKILL.md` references V8.6 "按需补充调用" consultative role per kais-movie-agent V8.6 SKILL.md canonical mapping table
  5. FOUND-08 preservation: no new expert_id directory created, no DAG node change — only body edits to existing SKILL.md files; Phase 13 v3.0 rename continuity→continuity_auditor + compliance_marketing→compliance_gate alias chains intact
**Plans**: TBD
**UI hint**: yes

### Phase 27: 集成 (Integration close-out)
**Goal**: Produce the canonical V8.6 13-step → expert_id mapping reference, update README corpus tree, sign off the 2 new `_shared/` refs in skills-mapping.yaml, and add bilingual glossary entries — closing out v5.0 with audit-ready traceability.
**Depends on**: Phase 22 (references `_shared/dreamina-cli-baseline.md`) + Phases 23/24/25/26 (verifies their SKILL.md updates against canonical mapping)
**Requirements**: INTEGRATION-01, INTEGRATION-02, INTEGRATION-03, INTEGRATION-04, INTEGRATION-05, INTEGRATION-06
**Success Criteria** (what must be TRUE):
  1. `skills/movie-experts/_shared/v86-pipeline-mapping.md` exists with `verified_date: 2026-06-19` documenting the canonical 13-step → expert_id mapping per kais-movie-agent V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查"
  2. v86-pipeline-mapping.md documents the 8 review gates (down from 12) per V8.6 §2 — which gate each expert's output passes through
  3. `skills/movie-experts/README.md` corpus tree updated to list the 2 new `_shared/` refs (dreamina-cli-baseline.md + v86-pipeline-mapping.md) with `verified_date: 2026-06-19`
  4. `.planning/research/v2-pipeline-design/skills-mapping.yaml` adds `v5_ref_signoffs` section with 2 entries (dreamina-cli-baseline.md + v86-pipeline-mapping.md) including `verified_date`, `source`, `license_status: fair_use_paraphrase` (mirrors v4.0 Phase 21 DOC-02 pattern)
  5. `_shared/glossary.md` adds new H3 bilingual entries for V8.6 terms — minimum 3 entries including at least: `### Atomic Step / 原子步骤`, `### Review Gate / 审核门`, `### L1 Identity Anchor / L1 身份锚点`
  6. FOUND-08 final preservation check at v5.0 close: zero new expert_id directories created across Phases 22-27, zero DAG node changes, zero renames, v4.0 methodology refs (snowflake-method.md / e-konte-format.md / scamper-variations.md) byte-intact
  7. v86-pipeline-mapping.md has LICENSE.md attribution row with license_status declared
**Plans**: TBD
**UI hint**: yes

---

## Critical Path

```
Phase 22 (dreamina CLI baseline)  ──┐
                                    ├─→  Phase 27 (Integration close-out)  ← MUST run last
Phase 23 (视觉系)        ─┐          │       (references _shared/dreamina-cli-baseline.md
Phase 24 (文学系)        ├─→ parallel │        from P22; verifies P23-26 SKILL.md updates
Phase 25 (听觉系)        │   wave     │        against canonical mapping)
Phase 26 (审核系)        ─┘          │
                                    ─┘
```

**Phase 22 MUST run first** — produces `_shared/dreamina-cli-baseline.md` referenced by Phase 23 (VISUAL-02) and Phase 25 (AUDIO-02).

**Phases 23, 24, 25, 26 are independent** — touch disjoint expert directories (P23: visual_executor / prompt_injector / character_designer / cinematographer / colorist / style_genome; P24: hook_retention / creative_source / screenplay / script_auditor; P25: audio_pipeline + sub-steps; P26: continuity_auditor / compliance_gate / editor / theory_critic). Can run in parallel waves if `/gsd:execute-phase` supports it.

**Phase 27 MUST run last** — close-out: references `_shared/dreamina-cli-baseline.md` from P22, writes canonical v86-pipeline-mapping.md verifying P23-26 SKILL.md Step references, and touches cross-cutting skills-mapping.yaml.

---

## Coverage Validation

**Total v5.0 requirements:** 30 (all mapped, zero orphans)

| Phase | Requirements | Count |
|-------|--------------|-------|
| 22 — dreamina CLI 知识基线 | DREAMINA-01..05 | 5 |
| 23 — 视觉系 V8.6 sync | VISUAL-01..07 | 7 |
| 24 — 文学系 V8.6 sync | LITERARY-01..04 | 4 |
| 25 — 听觉系 V8.6 sync | AUDIO-01..04 | 4 |
| 26 — 审核系 V8.6 sync | AUDIT-01..04 | 4 |
| 27 — 集成 close-out | INTEGRATION-01..06 | 6 |
| **Total** | | **30 / 30 ✓** |

**Coverage check:**
- ✓ Every v5.0 requirement mapped to exactly one phase (no orphans)
- ✓ Every phase has 4-7 requirements (standard granularity, no over-split, no over-merge)
- ✓ Critical path documented (P22 first, P23-26 parallel-eligible, P27 last)
- ✓ FOUND-08 preservation criterion explicit in every phase
- ✓ verified_date criterion explicit for every new ref
- ✓ v4.0 methodology refs explicitly PRESERVED (not replaced) — V8.6 knowledge ADDED alongside

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 22. dreamina CLI 知识基线 | 0/? | Not started | - |
| 23. 视觉系 V8.6 sync | 0/? | Not started | - |
| 24. 文学系 V8.6 sync | 0/? | Not started | - |
| 25. 听觉系 V8.6 sync | 0/? | Not started | - |
| 26. 审核系 V8.6 sync | 0/? | Not started | - |
| 27. 集成 close-out | 0/? | Not started | - |

---

*Last updated: 2026-06-19 — v5.0 kais-movie-agent V8.6 Adaptation roadmap created (6 phases, 30 reqs mapped). Phase 22 ready for planning.*
