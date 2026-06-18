# Milestones

## v5.0 kais-movie-agent V8.6 Adaptation (Shipped: 2026-06-19)

**Phases completed:** 6 phases (22-27) · **Requirements:** 30 / 30 ✓ · **Commits:** 17
**Tag:** `v5.0`
**Source artifact:** kais-movie-agent V8.4-V8.6 SKILL.md (commits `4fb57b4` + `c22867d` + `e41fa68`, all 2026-06-18)
**Audit:** [`v5.0-MILESTONE-AUDIT.md`](./milestones/v5.0-MILESTONE-AUDIT.md) — status: passed (30/30 reqs, 6/6 phases, FOUND-08 preserved milestone-wide)

**One sentence:** Sync hermes-agent's 16 active movie-experts to kais-movie-agent V8.4-V8.6 (13-step pipeline + dreamina CLI + V8.4 expert mapping) —— 纯知识层增量(2 新 `_shared/` refs + 18 expert SKILL.md body patches + 6 redirect-stub patches + 3 cross-cutting file updates),不引入新 expert_id、不动 DAG 节点、不重构核心架构,v4.0 方法论 refs 全部 PRESERVED 不替换。

**Key accomplishments:**

1. **Phase 22 — dreamina CLI 知识基线:** 新增 `_shared/dreamina-cli-baseline.md` (330 行) + `_shared/LICENSE.md`,文档化 V8.5 dreamina CLI 6 sub-commands + L1-L4 角色资产库策略 + async poll pattern + gold-team fallback + jimeng-client 废弃通知
2. **Phase 23 — 视觉系 V8.6 sync:** 6 expert SKILL.md body patches(visual_executor + prompt_injector + character_designer + cinematographer + colorist + style_genome)
3. **Phase 24 — 文学系 V8.6 sync:** 4 expert SKILL.md patches(hook_retention + creative_source + screenplay + script_auditor),覆盖 V8.6 atomic operations(Step 1 / 2 / 3 / 6)
4. **Phase 25 — 听觉系 V8.6 sync:** 1 主 patch(audio_pipeline)+ 6 redirect-stub patches,含 dreamina CLI `multimodal2video @Audio N` 绑定语法
5. **Phase 26 — 审核系 V8.6 sync:** 4 expert SKILL.md patches(continuity_auditor + compliance_gate + editor + theory_critic),文档化 V8.6 8-gate 审核门结构(down from 12)
6. **Phase 27 — 集成 close-out:** 新增 `_shared/v86-pipeline-mapping.md` (220 行) canonical 13-Step mapping + skills-mapping.yaml `v5_ref_signoffs:` section + README + glossary 3 new H3 entries

**Shipped artifacts:**

- **2 new `_shared/` refs** (~550 lines total): `dreamina-cli-baseline.md` (330) + `v86-pipeline-mapping.md` (220)
- **18 expert SKILL.md body patches** across 16 active experts(Phase 23-26)
- **6 redirect-stub SKILL.md patches**(Phase 25,所有 v3.0 merge/fold predecessors)
- **3 cross-cutting close-out updates**(Phase 27): README + skills-mapping.yaml + glossary
- **v5.0-MILESTONE-AUDIT.md** (status: passed, 30/30 reqs, FOUND-08 preserved)

**Cross-phase integration(verified by autonomous-orchestrator):**

- **V8.6 Pipeline Sync cross-reference network:** 15-row per-expert table in `v86-pipeline-mapping.md` bidirectionally links all active experts' V8.6 sections
- **FOUND-08 milestone-wide preservation:** zero new expert_id dirs, zero frontmatter changes across 24 patched files, v3.0/v4.0 byte-intact
- **License integrity:** both v5.0 refs `fair_use_paraphrase`, signed_off_by: phase-27-doc-02

**Known tech debt at close(non-blocking):**

- **FUTURE-10:** Live-run validation of dreamina CLI integration prompts against actual V8.6 pipeline run (deferred to operator — requires kais-movie-agent end-to-end execution)
- **FUTURE-11:** Cross-repo automated drift detection between kais-movie-agent V-number and hermes-agent internal knowledge (tooling not yet built)
- **FUTURE-12:** Vogler / Truby / 设计思维 / Story Grid / 起承转合 methodology expansion (defer to v6.0+ per v4.0 gap-analysis §6)
- **Quick task 260617-wgz:** status "missing" SUMMARY — pre-existing condition from v4.0 close(non-blocking,separate audit-open item)

See `.planning/milestones/v5.0-ROADMAP.md` for full phase details and `.planning/milestones/v5.0-REQUIREMENTS.md` for requirement outcomes.

---

## v4.0 — Methodology Backfill (Shipped: 2026-06-18)

**Phases completed:** 3 phases (19-21) · **Plans:** 3 · **Requirements:** 14 / 14 ✓
**Tag:** `v4.0`
**Source artifact:** [`.planning/research/methodology-gap-analysis-2026-06-17.md`](./research/methodology-gap-analysis-2026-06-17.md)(quick task 260617-wgz 产物)
**Audit:** [`v4.0-MILESTONE-AUDIT.md`](./milestones/v4.0-MILESTONE-AUDIT.md) — status: passed(14/14 reqs, 7/7 integration, 3/3 E2E flows, 4/4 FOUND-08)

**One sentence:** 把 2026-06-17 gap-analysis 识别的 3 个 ⭐⭐⭐⭐⭐ AI 化方法论缺口(Snowflake Method / E-Konte 絵コンテ / SCAMPER)增量挂载到 `creative_source+screenplay` / `cinematographer+visual_executor` / `style_genome+hook_retention` —— 不引入新 expert_id、不动 DAG 节点、不重构核心架构,纯知识层增量(1249 行新 refs + 8 SKILL.md patches + 16 glossary 词条)。

### Key accomplishments

- **Phase 19 — Snowflake Method Integration:** 新增 `creative_source/references/snowflake-method.md`(279 行)挂载 Ingermanson 10 步递进管线,填补 StoryKernel → Snyder 15-beat 之间的"展开塌陷"。Patched `creative_source/SKILL.md`(+45 行,新增 SnowflakeArtifacts output schema + Workflow steps 12-13)+ `screenplay/SKILL.md`(+20 行,Beat Planning 前新增 step 1.5 "Consume Snowflake-4 一页大纲" + 字段映射表)+ `_shared/glossary.md`(+52 行,4 词条)。StoryKernel→Snowflake→Snyder 全链路字段对齐。
- **Phase 20 — E-Konte Integration:** 新增 `cinematographer/references/e-konte-format.md`(371 行)挂载日本动画工业 5 层分镜格式(场景布局 / 镜头角度运动 / 角色位置表情动作 / 对白音效 / 时间帧数),与现有西方 Mascelli 8-level + 180°/30° 轴线**互补不替代**。Patched `cinematographer/SKILL.md`(+27 行,composition_lock 下新增 H2 "E-Konte as Intermediate Format")+ `visual_executor/SKILL.md`(+47 行,drawer 消费 Layer 1+3 / animator 消费 Layer 2+5)+ `_shared/glossary.md`(+41 行,4 词条)+ LICENSE.md attribution。兑现 Phase 17 storyboard_designer deprecated promise(E-Konte 折叠进 cinematographer,**不复活** storyboard_designer)。
- **Phase 21 — SCAMPER Variation Engine + DOC Close-out:** 新增 `style_genome/references/scamper-variations.md`(599 行)挂载 Bob Eberle SCAMPER 7 动词变体引擎,生成 35 个短剧变体配方(7 动词 × 5 genre×mood×pacing×cast×runtime 组合)。Patched `style_genome/SKILL.md`(+43 行,style_blend 上叠加 SCAMPER Variation Layer,显式声明**叠加不替代** auteur-theory)+ `hook_retention/SKILL.md`(+44 行,SCAMPER × 5 爆款公式 cross-table = 35 hook variant seeds)+ `_shared/glossary.md`(+67 行,8 词条)+ `README.md`(+35 行,corpus tree 列出 3 个新 refs)+ `.planning/research/v2-pipeline-design/skills-mapping.yaml`(+50 行,新增 v4_ref_signoffs section 3 entries)。

### Shipped artifacts

- **3 new methodology refs**(1249 lines total):`snowflake-method.md` (279) + `e-konte-format.md` (371) + `scamper-variations.md` (599)
- **8 SKILL.md body patches** across 6 experts(creative_source / screenplay / cinematographer / visual_executor / style_genome / hook_retention)
- **16 new glossary entries**(4 Snowflake + 4 E-Konte + 8 SCAMPER,中英对照 + 出处标注)
- **Updated corpus tree** in `skills/movie-experts/README.md`(Mermaid DAG 不变 —— 3 refs 都是已有 expert 内部 ref)
- **v4_ref_signoffs** section in `skills-mapping.yaml`(3 entries with verified_date / source / license_status: fair_use_paraphrase)
- **3 new refs LICENSE.md attribution rows**(creative_source / cinematographer / style_genome 各 +1)

### Cross-phase integration(verified by gsd-integration-checker)

- **Flow A — Snowflake narrative pipeline:** creative_source StoryKernel → Snowflake Step 1-4 → snowflake_artifacts.json → screenplay step 1.5 Consume → Snyder 15-beat validation(3 anchor points ±5%)→ Beat Planning。Fallback: 低质量 kernel 走 direct structural_formula → Beat Planning。
- **Flow B — E-Konte visual pipeline:** cinematographer composition_lock → 5-layer annotation → e_konte.json(dual-output with shot_intent.json)→ visual_executor drawer (L1+3) + animator (L2+5)→ editor 消费 shot_intent.json for axis compliance。Fallback: Western storyboard when e_konte absent。
- **Flow C — SCAMPER variation pipeline:** style_genome auteur + genre + cross-cultural → SCAMPER 7-verb expansion → scamper_variants.json(7 candidates with novelty/feasibility/alignment scores)→ hook_retention 7×5 cross-table(35 seeds)→ Hook Design Workflow。

### FOUND-08 backward-compat honored

- All 6 patched experts retain original `expert_id` + `related_skills`(byte-identical)
- No new expert directories created
- No deprecated experts revived(storyboard_designer / scene_builder / performer 仍 deprecated)
- E-Konte folded into existing cinematographer.composition_lock —— 兑现 Phase 17 promise

### Known tech debt at close(non-blocking)

- Snowflake trigger conditions expanded from 1 to 3 OR-conditions during execution(documented in 19-01-SUMMARY.md deviations)
- E-Konte trigger conditions expanded from 2 to 6-row table during execution(documented in 20-01-SUMMARY.md deviations)
- scamper-variations.md reached 599 lines vs 300-450 target —— 非阻塞 over-delivery,覆盖更彻底
- Live-run statistical validation of SCAMPER 7 候选 quality deferred to operator —— v4.0 close 不要求

See `.planning/milestones/v4.0-ROADMAP.md` for full phase details and `.planning/milestones/v4.0-REQUIREMENTS.md` for requirement outcomes.

---

## v1 — Movie-Experts Suite v2 (Shipped: 2026-06-15)

**Phases completed:** 7 phases (0-6) · **Plans:** 15 · **Tasks:** 25
**Tag:** `v1`
**Known deferred items at close:** 6 (see [STATE.md § Deferred Items](./STATE.md#deferred-items))

**One sentence:** RAG-augmented 18-expert movie-making skill suite (14 refactored + 4 new) covering 短剧 / 微电影 creation end-to-end, with MT-Bench position-swap eval harness and operator-deferred live statistical run.

### Key accomplishments

- **Phase 0 — Audit + Eval Skeleton:** Stripped 5 phantom refs (`wan22_video`, "168K controlled tokens", FLUX 1.x samplers, AudioLDM-2, CosyVoice) from existing 14 SKILL.md files. Built byte-exact snapshot tool (sha256 + git sha + ISO 8601) + MT-Bench position-swap eval harness (`runner.py` 616 lines, `judge_prompt.md` 4-dimension rubric, 3-condition ablation template). Captured 14 pre-refactor baselines as the eval anchor.
- **Phase 1 — EXPERT-COMPLI (Legal Gate):** Built `compliance_marketing` expert end-to-end — 5 refs (cn-content-rules covering 网信办 AI 标识办法 2025-09-01 + AI 漫剧 备案 regime 2026-04-01 + 3 platform specs 抖音/快手/小程序剧 + 8-category 红线 + 5-type 爆款 taxonomy) + bilingual SKILL.md + 5 eval prompts. Wired bidirectionally into 4 existing experts.
- **Phase 2 — EXPERT-HOOK (Commercial Engine):** Built `hook_retention` expert — 4 refs (`three-second-hooks`, `conflict-escalation`, `paywall-design` with 卡点 density + 3-tier 🟢🟡🔴 strength, `vertical-pacing` with multi-platform variation) + SKILL.md + 5 eval prompts.
- **Phase 3 — Top-4 RAG:** Deep-refactored screenplay / editor / colorist / style_genome with 5 curated refs each (20 total refs, ~400KB). Ran 36-verdict dry-run producing `_eval/reports/phase3-ablation-dryrun.md` + `_eval/reports/phase3-go-nogo.md` (CONDITIONAL GO — deferred to Phase 6 live run for statistical evidence).
- **Phase 4 — EXPERT-CINE (Camera Language):** Built `cinematographer` expert — boundary doc vs scene_builder / animator / editor authored BEFORE SKILL.md to prevent scope creep. 4 refs (shot-grammar, axis-rules, vertical-screen-framing, camera-motion-catalog) + SKILL.md + 3 prompts + 7 peer related_skills updates.
- **Phase 5 — Remaining 10 + EXPERT-PROD (v1.5):** Built `production` expert (AI-relevant subset only per PROD-07 — character LoRA spec, wardrobe, lighting intent, GPU budget, asset reuse; NOT live-action). 5 refs + SKILL.md + 3 prompts + 8 peer edges. Light-uplifted remaining 10 existing experts (2 refs each = 20 total). Carried forward all Phase 0 phantom strips.
- **Phase 6 — Full Eval + Bilingual + README:** Published top-level `skills/movie-experts/README.md` documenting 18-expert collaboration DAG + RAG usage guide (static refs / memory plugin / provider-agnostic) + Phase 6 live-run procedure (6-step operator runbook) + bilingual consistency section + file layout tree. Live run deferred to operator (requires `OPENROUTER_API_KEY` + budget).

### Shipped artifacts

- 18 expert directories under `skills/movie-experts/` (14 original refactored + 4 new)
- 58 markdown refs (~1.2MB cited fair-use content), all with LICENSE.md + `Last-verified: 2026-06-15` stamps
- `_eval/` harness: `runner.py`, `snapshot.py`, `judge_prompt.md`, `config.yaml.example`, 9 prompt files, `baseline/` × 14, `reports/` × 40+
- `_shared/`: `glossary.md` (EN↔CN), `known-external-models.yaml` (33-entry allowlist), `platform-comparison.md`, `RAG-INVOCATION-PATTERN.md`, `SKILL-LAYOUT.md`
- Top-level `README.md` (297 lines, 20KB)

### Known gaps at close

- Phase 6 UAT not executed (10 checkpoints paused at user redirect — see `06-UAT.md`)
- Phase 1 VERIFICATION `human_needed` — CN legal content + platform-spec thresholds + judge prompt quality + glossary completeness all require human/expert review
- Live-run statistical GO/NO-GO deferred to operator per CONTEXT D-11 (budget decision)

See `.planning/milestones/v1-ROADMAP.md` for full phase details and `.planning/milestones/v1-REQUIREMENTS.md` for requirement outcomes.

---

---

## v2.0 PRFP — Pipeline Redesign from First Principles (Shipped: 2026-06-16)

**Phases completed:** 6 phases (7-12) · **Plans:** N/A (design-only milestone)
**Tag:** `v2.0-prfp-design` (no code shipped — design suite only)
**Design artifacts:** `.planning/research/v2-pipeline-design/` (10 design docs + 4 YAML schemas + validation script)

**One sentence:** First-principles redesign of the movie-experts pipeline producing canonical DAG topology + per-node specs + corpus traceability + LLM-creative-distillation + cross-repo handoff plan + governance — design-only milestone, no skill code changes.

---

## v3.0 — Skills-to-DAG Alignment (Shipped: 2026-06-17)

**Phases completed:** 6 phases (13-18) · **Plans:** 16 · **Commits:** 67
**Tag:** `v3.0` (pending operator push)
**Stats:** 137 files changed · 19007 insertions · 2137 deletions · 1-day execution window
**Audit status:** tech_debt (12/12 requirements satisfied, 4 non-blocking WARNINGs) — see [v3.0-MILESTONE-AUDIT.md](./v3.0-MILESTONE-AUDIT.md)
**Known deferred items at close:** 6 (W-1, W-2, W-3, W-4, VALIDATE-D1, FUTURE-09) — see audit report

**One sentence:** Aligned v1 14-expert skill suite + v2 PRFP design to the canonical v2.0 PRFP DAG topology via 2 renames + 2 merges + 1 new + 3 deprecations — 13 legacy expert_id migrations preserved via FOUND-08 backward-compat aliases.

### Key accomplishments

- **Phase 13 — Expert Rename + Alias Scaffolding:** Renamed `continuity` → `continuity_auditor` and `compliance_marketing` → `compliance_gate` with `metadata.hermes.aliases` preservation (FOUND-08). 27 consumer related_skills rewired bidirectionally. skills-mapping.yaml sign_off_status flipped to signed_off for both renamed entries.
- **Phase 14 — Visual Executor Merge:** Merged `drawer` + `animator` into unified `visual_executor` with `sub_steps: [drawer, animator]` declaration. 15 consumer edges collapsed to single deduplicated entry. Refs organized under `references/{drawer,animator}/` sub-folders.
- **Phase 15 — Audio Pipeline Merge:** Merged 5 audio experts (`voicer` + `lip_sync` + `composer` + `foley` + `mixer` + `spatial_audio`) into unified `audio_pipeline` with `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]`. spatial_audio FOLDED as 6th sub-step (D-1 decision — preserves HRTF/Atmos content; uses `status: folded_into` distinct from `merged_into`). 11 consumer edges collapsed.
- **Phase 16 — New AI-Native Expert (prompt_injector):** Created brand-new `prompt_injector` expert (no v1 predecessor) per Phase 8 §2.7 + nodes.yaml. 4 refs (prompt-engineering-patterns, cross-call-consistency, token-budget-management, model-specific-prompt-templates). Bidirectional edges to creative_source + cinematographer + visual_executor + audio_pipeline.
- **Phase 17 — Deprecate 3 Experts:** Marked `performer` / `scene_builder` / `storyboard_designer` as `status: deprecated` with `inheritance_targets` and `deprecated_reason`. 9 consumer body annotations added. FOUND-08 preserved — original expert_id + body content intact for backward compatibility.
- **Phase 18 — Validation + Documentation:** Produced VALIDATION-REPORT.md reconciling 31 SKILL.md files into 4 buckets (15 active DAG + 3 active non-DAG + 3 deprecated + 10 redirect stubs). README.md ASCII DAG replaced with canonical Mermaid from 01-NODE-DAG.md §1.5. 5 glossary terms verified/added. known-external-models.yaml Phase 8 §2.17 dated annex (27 entries with verified_date: 2026-06-17). All 19 skills-mapping.yaml entries signed_off.

### Shipped artifacts

- 5 new expert directories: continuity_auditor, compliance_gate, visual_executor, audio_pipeline, prompt_injector
- 13 redirect/deprecated stubs preserving v1 expert_ids (10 redirect + 3 deprecated)
- 1 new prompt_injector expert with 4 refs + LICENSE + GAP-REPORT
- Updated README.md with Mermaid DAG + 4-bucket inventory classification
- Updated glossary.md (5 new H3 entries)
- Updated known-external-models.yaml (73 entries, 27 verified_date stamps, Phase 8 §2.17 annex)
- VALIDATION-REPORT.md (canonical milestone-close audit artifact)

### Known gaps at close

- **W-1:** creative_source → topic_curator dead reference (pre-existing v2.0, narrow phase scope)
- **W-2:** character_designer missing Phase 17 inheritance body annotation
- **W-3:** 32 pre-existing v2.0 bidirectional asymmetries (post-v3.0 normalization candidacy)
- **W-4:** Frontmatter `status:` field path inconsistency (documentation drift in per-phase verification reports)
- **VALIDATE-D1:** quality_gate gap — canonical 16th DAG node has no SKILL.md directory
- **FUTURE-09:** production expert (currently `disposition: deferred` in skills-mapping.yaml)

---

*Last updated: 2026-06-17 — v3.0 archived, awaiting next milestone decision*
