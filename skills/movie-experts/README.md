# Movie-Experts Suite v2 — 短剧/微电影创作专家增强

**Project:** RAG-augmented movie-expert skill suite for AI 短剧 / 微电影 production.
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Status:** v1 complete (17 experts: 14 original + 3 new — COMPLI / HOOK / CINE). v1.5 will add production expert (PROD) → 18 total.
**Last updated:** 2026-06-15

---

## Suite Overview

17 specialists covering the entire AI 短剧 / 微电影 creation pipeline, from style definition through final mix. Each expert is a self-contained Hermes skill (`SKILL.md` + `references/*.md`) that integrates with the others via declared `related_skills` edges.

### 14 Original Experts (Phase 0 baselined; 4 deep-refactored in Phase 3)

| Expert | Chinese Name | Role |
|--------|--------------|------|
| [`style_genome`](./style_genome/SKILL.md) | 风格基因专家 | 5D director/genre style encoding + blend protocol + cross-module alignment (root expert) |
| [`screenplay`](./screenplay/SKILL.md) | 剧本专家 | Scene-level script + dialogue + emotion_curve design (HOOK-09 marker schema integrated) |
| [`scene_builder`](./scene_builder/SKILL.md) | 三维场景建构专家 | FxSxA scene matrix + 3D previsualization + camera blocking |
| [`performer`](./performer/SKILL.md) | 表演专家 | Performance-4D matrix (ExBxSxP) for character action + emotion design |
| [`drawer`](./drawer/SKILL.md) | 绘图专家 | FLUX/LoRA parameter optimization for cinematic visual quality |
| [`animator`](./animator/SKILL.md) | 视频专家 | Current video gen model cinematic camera motion + temporal consistency |
| [`colorist`](./colorist/SKILL.md) | 色彩专家 | CxSxZ 28-combination color intent + LUT design (Phase 3 deep-refactored) |
| [`editor`](./editor/SKILL.md) | 剪辑专家 | FxRxT editing matrix + Murch Rule of Six + 180° axis compliance (Phase 3 deep-refactored) |
| [`composer`](./composer/SKILL.md) | 配乐专家 | BGM generation + sound effect design + music-video beat sync |
| [`foley`](./foley/SKILL.md) | 拟音专家 | 7D parametric sound effects (Material × Action × Force) |
| [`spatial_audio`](./spatial_audio/SKILL.md) | 空间音频专家 | 6D spatial encoding + immersive 3D sound field |
| [`mixer`](./mixer/SKILL.md) | 混音专家 | Multi-track mixing + dialogue ducking + mastering |
| [`voicer`](./voicer/SKILL.md) | 配音专家 | CosyVoice speech synthesis + emotion-adaptive delivery |
| [`continuity`](./continuity/SKILL.md) | 连续性专家 | Cross-shot consistency auditing (character / environment / color / style) |

### 3 New Experts (Phase 1-4)

| Expert | Chinese Name | Role | Phase Built |
|--------|--------------|------|-------------|
| [`compliance_marketing`](./compliance_marketing/SKILL.md) | 合规与宣发专家 | CN content-rules gate + AIGC labeling + per-platform distribution + 爆款 vs 红线 review | Phase 1 |
| [`hook_retention`](./hook_retention/SKILL.md) | 钩子与留存专家 | 3-second hook design + 付费卡点 placement + per-platform 爆款公式 + 钩子/爽点/卡点 marker schema | Phase 2 |
| [`cinematographer`](./cinematographer/SKILL.md) | 镜头专家 | Shot intent layer (shot scale + composition + axis + camera move) with vertical 9:16 framing + 2026 video gen model prompt-token mapping | Phase 4 |

### Phase 5 (v1.5) — DEFERRED

| Expert | Chinese Name | Role |
|--------|--------------|------|
| `production` (planned) | 制作管理专家 | AI-relevant subset: casting LoRA / wardrobe / lighting intent / GPU budget / asset reuse (NOT live-action crews) |

---

## Production DAG (Collaboration Graph)

```text
                                  ┌─────────────────────┐
                                  │   USER INTENT       │
                                  │ (director / genre)  │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │   style_genome      │   (root expert)
                                  │   风格基因 (5D)      │
                                  └──────────┬──────────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          │                  │                  │
                          ▼                  ▼                  ▼
                ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                │   screenplay    │  │ hook_retention  │  │ compliance_     │
                │   剧本           │  │ 钩子与留存       │  │ marketing 合规  │
                └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
                         │                    │                    │
                         ▼                    ▼                    ▼
                ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                │ cinematographer │  │   performer     │  │   scene_builder │
                │   镜头           │  │   表演           │  │   三维场景建构   │
                └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
                         │                    │                    │
                         └──────────┬─────────┴────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │     drawer      │   (FLUX / LoRA stills)
                          │     绘图         │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │    animator     │   (Runway / Kling / Veo / Sora 2)
                          │     视频         │
                          └────────┬────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
       ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
       │   colorist    │   │    editor     │   │  composer /   │
       │   色彩         │   │    剪辑       │   │  foley /      │
       └───────┬───────┘   └───────┬───────┘   │  spatial_audio│
               │                   │           │  / voicer     │
               └───────────────────┴───────────┴───────┬───────┘
                                   │                   │
                                   ▼                   ▼
                          ┌─────────────────┐ ┌───────────────┐
                          │     mixer       │ │  continuity   │
                          │     混音         │ │  连续性审计    │
                          └────────┬────────┘ └───────┬───────┘
                                   │                  │
                                   └──────────┬───────┘
                                              │
                                              ▼
                                   ┌─────────────────┐
                                   │   FINAL OUTPUT  │
                                   │  (短剧 / 微电影)  │
                                   └─────────────────┘
```

**Key DAG properties:**
- **Root:** `style_genome` (no upstream; defines 5D style vector)
- **Bottleneck nodes:** `screenplay` (after style) / `drawer` (after intent) / `mixer` (after all audio)
- **Audit nodes:** `continuity` (parallel to mixer) verifies cross-shot consistency
- **Compliance gate:** `compliance_marketing` runs early + late (pre-production + pre-distribution)
- **Bidirectional edges:** most experts declare both upstream + downstream related_skills

---

## RAG Usage Guide

Each v1 expert carries a `references/*.md` corpus that grounds its numeric thresholds + heuristics in cited sources. The 4 Phase-3 deep-refactored experts + the new Phase-1/2/4 experts have **provider-agnostic RAG invocation**:

### Static refs (default path)
Each `SKILL.md` body links to its `references/*.md` via a `## References` table. The static refs are the authoritative source — they are git-trackable, reviewable, and provider-agnostic.

### Memory plugin (optional optimization)
If the runtime has a memory / RAG tool (e.g., `<memory_plugin>` / `<rag_search>`), the `## Knowledge Retrieval` block documents the tag queries to use:
```
tags="expert:<expert_name>,domain:<ref_slug>"
```
This is an optimization path — the static refs remain the authoritative source.

### Provider-agnostic invocation (hard constraint)
All RAG invocation is provider-agnostic. The `references/*.md` files contain model names ONLY in `known-external-models.yaml` (allowlist) and `camera-motion-catalog.md` (Phase 4 cinematographer — model-specific prompt-token mapping requires explicit model names with `verified_date` stamp).

### Ref corpus summary (per expert)
| Expert | Refs | Total size | Last verified |
|--------|------|------------|---------------|
| screenplay | 5 | ~108 KB | 2026-06-15 |
| editor | 5 | ~95 KB | 2026-06-15 |
| colorist | 5 | ~100 KB | 2026-06-15 |
| style_genome | 5 | ~95 KB | 2026-06-15 |
| compliance_marketing | 5 | ~80 KB | 2026-06-15 |
| hook_retention | 4 | ~70 KB | 2026-06-15 |
| cinematographer | 4 | ~52 KB | 2026-06-15 |
| **Total** | **33** | **~600 KB** | — |

(Other 10 experts have placeholder refs pending Phase 5 v1.5 RAG uplift.)

---

## Evaluation Framework

### MT-Bench position-swap harness
The suite ships a position-bias-mitigated LLM-as-judge harness at [`_eval/runner.py`](./_eval/runner.py). Per MT-Bench protocol: every (prompt, condition-pair) comparison is judged in BOTH orderings (A,B) and (B,A); disagreement → "tie" (position-bias signal, not genuine quality difference).

### Phase 3 dry-run results (4 top experts)
See [`_eval/reports/phase3-ablation-dryrun.md`](./_eval/reports/phase3-ablation-dryrun.md) for the full report. Summary:
- 4 experts × 3 conditions × 3 prompts × 1 judge (stub) = 36 dry-run verdicts
- All verdicts = "tie" (expected `_StubJudgeClient` stub signature)
- Harness validated end-to-end: 3-condition ablation matrix runnable; per-expert reports in JSON + Markdown

### Phase 3 GO/NO-GO report
See [`_eval/reports/phase3-go-nogo.md`](./_eval/reports/phase3-go-nogo.md) for the full report. Status: **CONDITIONAL GO** — deferred to Phase 6 live run for statistical evidence.

### Phase 6 live run procedure
The Phase 6 live run is the statistically defensible evaluation. To execute:

1. **Configure API key:**
   ```bash
   export OPENROUTER_API_KEY=sk-or-v1-...
   # Add to ~/.hermes/.env for persistence
   ```

2. **Copy config template:**
   ```bash
   cp _eval/config.yaml.example _eval/config.yaml
   # (config.yaml is gitignored; edit if needed but don't commit)
   ```

3. **Expand prompt set:** Each expert's `_eval/prompts/<expert>_demo.yaml` currently has 3 prompts. Phase 6 expands to ≥20 per EVAL-05 statistical threshold.

4. **Run multi-judge ensemble:** The runner currently uses only `judges[0]` (qwen3-235b). Phase 6 invokes both judges (qwen3-235b + deepseek-v3) per EVAL-06.

5. **Execute per expert:**
   ```bash
   for EXP in screenplay editor colorist style_genome cinematographer compliance_marketing hook_retention; do
     python3 _eval/runner.py \
         --config _eval/config.yaml \
         --expert "$EXP" \
         --output-json _eval/reports/${EXP}_phase6.json \
         --output-md   _eval/reports/${EXP}_phase6.md
   done
   ```

6. **Aggregate + GO/NO-GO:** Aggregate per-expert reports into `_eval/reports/phase6-summary.md` and apply CONTEXT D-9 GO criteria:
   > GO if ≥2/3 prompts improve with new-with-refs vs new-no-refs across ≥3/4 experts

---

## Bilingual Consistency

### EN↔CN term dictionary
The [`_shared/glossary.md`](./_shared/glossary.md) defines canonical EN↔CN terms. Every expert's `SKILL.md` and `references/*.md` MUST use these terms consistently.

### Format convention
- **Frontmatter:** English (`name`, `description`, `metadata.hermes.*`, `expert_id`)
- **SKILL.md body:** English structure (H1/H2/H3 headers, bullets) + Chinese descriptive prose
- **Refs:** Primarily Chinese prose with English technical terms preserved (e.g., "MCU", "ΔE2000", "CxSxZ")
- **Cross-references:** Markdown links use English filenames; anchor text may be bilingual

### Consistency check
Manual review performed Phase 6:
- ✓ All 17 experts use canonical CN terms (钩子 / 爽点 / 卡点 / 完播率 / 男频 / 女频 / 爆款 / 运镜)
- ✓ Metric IDs preserved across experts (e.g., `emotion_curve` / `color_intent_match` / `style_consistency`)
- ✓ Frozen `expert_id` values (backward-compat HARD RULE per Phase 0 [CR-01])
- ✓ All refs carry `Last-verified` stamp + LICENSE fair-use attribution

---

## File Layout

```text
skills/movie-experts/
├── README.md                                    (this file)
├── animator/           SKILL.md + (refs pending v1.5)
├── cinematographer/    SKILL.md + references/{shot-grammar,axis-rules,vertical-screen-framing,camera-motion-catalog}.md + LICENSE.md
├── colorist/           SKILL.md + references/{bellantoni,hurkman,cross-cultural,cn-audience,digital-science}.md + LICENSE.md
├── compliance_marketing/ SKILL.md + references/{cn-content-rules,viral-element-catalog,platform-douyin,platform-kuaishou,platform-miniprogram}.md + LICENSE.md
├── composer/           SKILL.md + (refs pending v1.5)
├── continuity/         SKILL.md + (refs pending v1.5)
├── drawer/             SKILL.md + (refs pending v1.5)
├── editor/             SKILL.md + references/{murch,classical,montage,fxrxt,cn-cutting}.md + LICENSE.md
├── foley/              SKILL.md + (refs pending v1.5)
├── hook_retention/     SKILL.md + references/{three-second-hooks,conflict-escalation,paywall-design,vertical-pacing}.md + LICENSE.md
├── mixer/              SKILL.md + (refs pending v1.5)
├── performer/          SKILL.md + (refs pending v1.5)
├── scene_builder/      SKILL.md + (refs pending v1.5)
├── screenplay/         SKILL.md + references/{save-the-cat,mckee,cn-shortdrama,emotion-curve-academic,dialogue-craft}.md + LICENSE.md
├── spatial_audio/      SKILL.md + (refs pending v1.5)
├── style_genome/       SKILL.md + references/{director-dna-archive,genre-dna-taxonomy,auteur-theory,cross-cultural-style,cn-director-analysis}.md + LICENSE.md
├── voicer/             SKILL.md + (refs pending v1.5)
├── _eval/
│   ├── runner.py                                 (MT-Bench position-swap harness)
│   ├── config.yaml.example                       (3-condition ablation template)
│   ├── judge_prompt.md                           (4-dimension rubric)
│   ├── prompts/
│   │   ├── animator_demo.yaml
│   │   ├── cinematographer_demo.yaml
│   │   ├── colorist_demo.yaml
│   │   ├── compliance_marketing_demo.yaml
│   │   ├── editor_demo.yaml
│   │   ├── hook_retention_demo.yaml
│   │   ├── screenplay_demo.yaml
│   │   └── style_genome_demo.yaml
│   ├── baseline/                                 (Phase 0 pre-refactor snapshots × 14)
│   └── reports/                                  (dry-run + Phase 3 GO/NO-GO reports)
└── _shared/
    ├── glossary.md                               (EN↔CN term dictionary)
    ├── known-external-models.yaml                (model name allowlist)
    ├── platform-comparison.md
    ├── RAG-INVOCATION-PATTERN.md
    └── SKILL-LAYOUT.md                           (reference anatomy spec)
```

---

## Project Planning Artifacts

- [`.planning/PROJECT.md`](../../.planning/PROJECT.md) — project context + core value + constraints
- [`.planning/REQUIREMENTS.md`](../../.planning/REQUIREMENTS.md) — 46 v1 requirements (FOUND ×9, COMPLI ×9, HOOK ×9, REFACTOR ×8, CINE ×9, EVAL ×9, DOC ×4)
- [`.planning/ROADMAP.md`](../../.planning/ROADMAP.md) — 7-phase build order (Phases 0-4 + 6 = v1, Phase 5 = v1.5)
- [`.planning/STATE.md`](../../.planning/STATE.md) — current execution state

---

## License

Each expert's `references/LICENSE.md` documents the fair-use attribution for its ref corpus. The suite code (runner.py, etc.) is MIT.

## Citation

If you build on this suite, please cite:
- Phase 0 audit + eval skeleton: PROJECT.md §Core Value
- Phase 3 deep refactor approach: 03-CONTEXT.md §Decisions
- Phase 4 cinematographer: 04-CONTEXT.md §Phase Boundary

---

*Movie-Experts Suite v2 — built 2026-06-15 across 4 phases + this Phase 6 documentation pass.*
*v1 = 17 experts (14 refactored-or-baselined + 3 new). v1.5 adds production → 18.*
