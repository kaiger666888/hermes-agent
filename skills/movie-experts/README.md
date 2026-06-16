# Movie-Experts Suite v2 — 短剧/微电影创作专家增强

**Project:** RAG-augmented movie-expert skill suite for AI 短剧 / 微电影 production.
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Status:** v3.0 in progress — 18 active expert_ids (17 post-Phase-15 + 1 Phase 16 prompt_injector NEW). Phases 13-15 merged 4+6+1 predecessors into continuity_auditor / compliance_gate / visual_executor / audio_pipeline; Phase 16 added prompt_injector (the only NEW AI-native node, no v1 predecessor). All RAG-aware. 5 Phase-7 + 3 Phase-8 experts have independent validation protocols.
**Last updated:** 2026-06-17

---

## 🆕 Phase 8 Update — Project Corpus Integration (2026-06-16)

Integrated **102-book Chinese film production library** (`/home/kai/Downloads/100+本影视剪辑书/`) into the movie-experts suite as a unified RAG corpus. Total additions:

### 3 New Experts

| Expert | Chinese Name | Role | Source Books |
|---|---|---|---|
| [`theory_critic`](./theory_critic/SKILL.md) | 理论批评专家 | 电影理论(形式/写实/精神分析)+ 作者研究 + 电影史方法 + 学术批评方法 | 25+ 本理论批评书 |
| [`documentary_maker`](./documentary_maker/SKILL.md) | 纪录片创作专家 | 王竞六讲 + 6 种类型 + 4 大流派 + 民族志 + 纪录片风格 短剧 | 《纪录片创作六讲》《民族志纪录片创作》 |
| [`animation_studio`](./animation_studio/SKILL.md) | 动画制作专家 | 迪士尼 4 阶段 + 12 阶段流程 + 跨文化改编(花木兰)+ 歌舞叙事 | 《迪士尼的艺术》《影视动画经典剧本赏析》 |

### Shared Project Corpus (`_shared/project-corpus/`)

9 new ref files synthesizing the project's 102 books:

| Ref | Source Books | Used By |
|---|---|---|
| `README.md` | 102-book index | All experts (corpus navigation) |
| `theory-formalism-vs-realism.md` | Andrew / Agel / Balázs | theory_critic |
| `film-philosophy-bazin-tarkovsky.md` | Bazin / Tarkovsky / 七部半 | theory_critic |
| `psychoanalytic-film-theory.md` | 凝视的快感 / 好莱坞中的拉康 | theory_critic, compliance_gate |
| `auteur-director-biographies.md` | 7 本导演传记 | theory_critic, style_genome |
| `film-criticism-methodology.md` | 戴锦华 / 如何写影评 / 外国批评文选 | theory_critic |
| `film-history-methods.md` | Allen / Oxford / Sadoul | theory_critic |
| `narrative-revolution-and-modernism.md` | 郭小橹 / 本雅明 / 阿多诺 | theory_critic |
| `screenwriting-chinese-and-supplementary.md` | 芦苇 / 维基·金 / 刘天赐 / 编剧策略 / 奥班农 / 温斯顿 | screenplay |
| `cinematography-masterclass-and-grammar.md` | 阿里洪 / 100 手法 / 拉片子 / 拆解好电影 / 21 位大师 | cinematographer, editor |
| `lighting-equipment-and-design.md` | 照明器材 / 影视光线艺术 / 镜头在说话 / 狼图腾 | cinematographer, colorist |
| `editing-sound-post.md` | 剪辑之道 / 魅力剪辑 / 音效圣经 / 视听 / 王竞六讲 | editor, audio_pipeline, documentary_maker |
| `production-chinese-and-low-budget.md` | 拍电影 / 制片手册 / 创意制片 / 好莱坞模式 / 英国基础 / 预算手册 | production |
| `animation-disney-system.md` | 迪士尼的艺术 / 影视动画剧本赏析 | animation_studio |

### Existing Experts Enhanced

Cross-references to project corpus added for:

- `style_genome` — now cites auteur-director-biographies for 7-master research
- `screenplay` — now cites screenwriting-chinese-and-supplementary (芦苇 / 21-day / hook / O'Bannon)
- `cinematographer` — now cites masterclass-and-grammar + lighting-equipment
- `editor` — now cites editing-sound-post (Murch philosophy + 7 pioneers + sound bible)
- `colorist` — now cites lighting-equipment Part 2 (Fifth Generation color narrative)
- `production` — now cites production-chinese-and-low-budget

---

## Suite Overview

26 specialists covering the entire AI 短剧 / 微电影 creation pipeline, from creative-source mining through final mix + lip-sync, plus theory / documentary / animation verticals. Each expert is a self-contained Hermes skill (`SKILL.md` + `references/*.md`) that integrates with the others via declared `related_skills` edges. Total ref corpus: ~95 files (~3MB cited fair-use content) including 9 project-corpus refs.

### 14 Original Experts (Phase 0 baselined; 4 deep-refactored Phase 3, 10 light-uplifted Phase 5)

| Expert | Chinese Name | Role | Refs |
|--------|--------------|------|------|
| [`style_genome`](./style_genome/SKILL.md) | 风格基因专家 | 5D director/genre style encoding + blend protocol + cross-module alignment (root expert) | 5 (Phase 3 deep) |
| [`screenplay`](./screenplay/SKILL.md) | 剧本专家 | Scene-level script + dialogue + emotion_curve design (HOOK-09 marker schema integrated) | 5 (Phase 3 deep) |
| [`scene_builder`](./scene_builder/SKILL.md) | 三维场景建构专家 | FxSxA scene matrix + Blender 4.x previz + Pallasmaa space-as-character doctrine | 2 (Phase 5 light) |
| [`performer`](./performer/SKILL.md) | 表演专家 | ExBxSxP matrix + Stanislavski + Laban Effort + Meisner truth-of-moment | 2 (Phase 5 light) |
| [`visual_executor`](./visual_executor/SKILL.md) | 视觉执行专家 | Unified FLUX 2 image gen (drawer sub-step) + Hermes-catalog video gen (animator sub-step) — merged Phase 14 per v2.0 PRFP DAG §4.8 | 5 (Phase 5 light × 2 + Phase 14 merge) |
| [`colorist`](./colorist/SKILL.md) | 色彩专家 | CxSxZ 28-combination color intent + LUT design + Bellantoni color psychology | 5 (Phase 3 deep) |
| [`editor`](./editor/SKILL.md) | 剪辑专家 | FxRxT editing matrix + Murch Rule of Six + 180° axis compliance | 5 (Phase 3 deep) |
| [`audio_pipeline`](./audio_pipeline/SKILL.md) | 音频管线专家 | Unified 6-sub-step audio production: voicer (TTS) + lip_sync (audio-driven sync) + composer (music/score) + foley (SFX) + mixer (mastering) + spatial_audio (3D encoding). Merged Phase 15 per v2.0 PRFP DAG §4.9. | 2-4 (Phase 5 light × 5 + Phase 7A-2 lip_sync benchmark) |
| [`continuity_auditor`](./continuity_auditor/SKILL.md) | 连续性专家 | 4-dimension cross-shot audit (face/wardrobe/color/object) + eyeline match + 180° axis | 2 (Phase 5 light) |

### 4 New Experts (Phase 1-5)

| Expert | Chinese Name | Role | Phase Built | Refs |
|--------|--------------|------|-------------|------|
| [`compliance_gate`](./compliance_gate/SKILL.md) | 合规与宣发专家 | CN content-rules gate + AIGC labeling + per-platform distribution + 爆款 vs 红线 review | Phase 1 | 5 |
| [`hook_retention`](./hook_retention/SKILL.md) | 钩子与留存专家 | 3-second hook design + 付费卡点 placement + per-platform 爆款公式 + 钩子/爽点/卡点 marker schema | Phase 2 | 4 |
| [`cinematographer`](./cinematographer/SKILL.md) | 镜头专家 | Shot intent layer (shot scale + composition + axis + camera move) + vertical 9:16 framing + 2026 video gen model prompt-token mapping | Phase 4 | 4 |
| [`production`](./production/SKILL.md) | 制作管理专家 | AI-relevant subset: character LoRA spec / per-scene wardrobe / lighting intent / GPU budget / asset reuse (NOT live-action per PROD-07) | Phase 5 | 5 |

### 5 New Experts (Phase 7 — independent validation, no LLM-judge required)

| Expert | Chinese Name | Role | Validation Protocol | Refs |
|--------|--------------|------|---------------------|------|
| [`script_auditor`](./script_auditor/SKILL.md) | 剧本审计专家 | 5-dimension quantitative script audit (narrative / emotion / hook / character / completion-forecast) BEFORE production. Decoupled from screenplay (screenplay writes, script_auditor audits) | Pearson correlation between predicted & actual 完播率 ≥ 0.65 on 100-script labeled corpus | 5 |
| [`character_designer`](./character_designer/SKILL.md) | 角色设计专家 | Character Bible 2.0 authoring with 4D-Anchor (front/3-quarter/side/back) + layered STYLE_PREFIX (CORE/IDENTITY/VARIANCE) + consistency stress test. Decoupled from visual_executor (visual_executor generates images, character_designer defines identity contract) | CLIP-I / DINO-I cross-scene similarity ≥ 0.80 on 30-character × 7-image corpus | 4 |
| [`storyboard_designer`](./storyboard_designer/SKILL.md) | 分镜设计专家 | Scene → per-shot Storyboard JSON decomposition with camera params + 4D anchoring (depth/identity/lighting/temporal) + extension-chain end_frames. Decoupled from cinematographer (cinematographer defines rules, storyboard_designer applies them) | Shot count accuracy / shot size distribution KL / rhythm curve DTW vs professional ground truth on 50-script corpus | 4 |
| [`creative_source`](./creative_source/SKILL.md) | 创意源头专家 | Story Kernel mining from 6 social strata (institutional / technological / demographic / spatial / intergenerational / psychosocial). DAG root — upstream of style_genome. Sources: Bourdieu / Foucault / Giddens + Lefebvre + Han Byung-Chul | Strata resonance Pearson / Bourdieu field accuracy / unspeakability AUC on 100-topic labeled corpus | 4 |

### 3 New Experts (Phase 8 — Project Corpus Integration, 2026-06-16)

These 3 experts are the **primary consumers** of the integrated 102-book project corpus at `_shared/project-corpus/`. They cover verticals (theory / documentary / animation) that were not in the original 短剧-focused suite.

| Expert | Chinese Name | Role | Source | Refs |
|--------|--------------|------|--------|------|
| [`theory_critic`](./theory_critic/SKILL.md) | 理论批评专家 | 电影理论框架(形式 vs 写实 / 精神分析 / 巴赞 / 塔可夫斯基)+ 作者研究(7 位大师)+ 电影史方法(4 大路径)+ 学术批评(戴锦华 4 维度 + 自问十题) | Project corpus: Andrew / Bazin / Tarkovsky / Mulvey / Žižek / Dai Hua / 7 本导演传记 | 8 |
| [`documentary_maker`](./documentary_maker/SKILL.md) | 纪录片创作专家 | 王竞六讲法 + 6 种纪录片类型 + 4 大流派(Flaherty / Vertov / Grierson / Direct-Vérité)+ 民族志参与观察 + 纪录片风格 短剧 | Project corpus: 《纪录片创作六讲》《民族志纪录片创作》 | 5 |
| [`animation_studio`](./animation_studio/SKILL.md) | 动画制作专家 | 迪士尼 4 阶段体系 + 12 阶段制作流程 + 跨文化改编 5 法则(花木兰案例)+ 歌舞叙事 + 搭档喜剧 | Project corpus: 《迪士尼的艺术》《影视动画经典剧本赏析》 | 6 |


### 1 New Expert (Phase 16 — AI-Native prompt_injector, 2026-06-17)

The only NEW AI-native node in v3.0 (no v1 predecessor per `skills-mapping.yaml:99-103` `mapping_type: new_ai_native`). Translates upstream human intent into model-ready prompts with cross-call consistency context management — a discipline that only exists because of generative models.

| Expert | Chinese Name | Role | Source | Refs |
|--------|--------------|------|--------|------|
| [`prompt_injector`](./prompt_injector/SKILL.md) | 提示注入专家 | AI-native node translating visual_intent + style_genome + character_assets → model_prompts + consistency_context. Cross-call consistency context + token budget management (≤4000/call). No v1 predecessor (new_ai_native mapping) | 02-NODE-SPECS.md §2.7 + Phase 7 §4.7 D3.5+D2.4 | 4 |


---

## Production DAG (Collaboration Graph)

```text
                                  ┌─────────────────────┐
                                  │   USER INTENT       │
                                  │ (topic / social issue) │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │  creative_source    │   (Phase 7 root — mines Story Kernel)
                                  │  创意源头 (6 strata)  │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │   style_genome      │   (root — defines 5D style vector)
                                  │   风格基因 (5D)      │
                                  └──────────┬──────────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          │                  │                  │
                          ▼                  ▼                  ▼
                ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                │   screenplay    │  │ hook_retention  │  │ compliance_     │
                │   剧本           │  │ 钩子与留存       │  │ gate 合规       │
                └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
                         │                    │                    │
                         ▼                    │                    ▼
                ┌─────────────────┐            │           ┌─────────────────┐
                │ script_auditor  │ ◄──────────┴────────── │  character_     │
                │ 剧本审计 (5-dim) │            (loop)      │  designer       │
                └────────┬────────┘                        │  角色设计 (4D)   │
                         │                                 └────────┬────────┘
                         ▼                                          │
                ┌─────────────────┐                                 │
                │ cinematographer │                                 │
                │   镜头           │                                 │
                └────────┬────────┘                                 │
                         │                                          │
                         ▼                                          │
                ┌─────────────────┐                                 │
                │ storyboard_     │ ◄───────────────────────────────┘
                │ designer 分镜    │
                │ (Storyboard JSON)│
                └────────┬────────┘
                         │
                         ▼
                    ┌─────────────────┐   ◄── style_genome_5d
                    │ prompt_injector │       (parallel edge)
                    │  提示注入        │
                    └────────┬────────┘   ◄── character_assets
                             │               (parallel edge)
                             ▼
                ┌────────┴────────┬──────────────────┐
                │                 │                  │
                ▼                 ▼                  ▼
       ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
       │ scene_builder │  │   performer   │  │  production   │
       │ 三维场景建构   │  │   表演         │  │  制作管理      │
       └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
               │                  │                  │
               └──────────┬───────┴──────────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │  visual_        │   (FLUX stills + Runway/Kling/Veo video)
                │  executor 视觉  │   (Phase 14 merge: drawer + animator sub-steps)
                └────────┬────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
       ┌───────────────┐  ┌───────────────┐
       │  colorist /   │  │ audio_pipeline│ ◄──── continuity_auditor (parallel audit)
       │  editor       │  │ 音频管线      │
       │               │  │ (voicer/lip_ │
       │               │  │  sync/composer│
       │               │  │  /foley/mixer│
       │               │  │  /spatial)   │
       └───────┬───────┘  └───────┬───────┘
               │                  │
               └──────────┬───────┘
                          │
                          ▼
                ┌─────────────────┐
                │   FINAL OUTPUT  │
                │  (短剧 / 微电影)  │
                └─────────────────┘
```

**Key DAG properties (v2 with Phase 7 + 8):**
- **New root:** `creative_source` (no upstream; mines Story Kernel from social strata) — replaces style_genome as DAG root
- **Quality loop:** `screenplay` ↔ `script_auditor` iterate until target audit band
- **Identity contract:** `character_designer` emits CharacterBible 2.0 consumed by visual_executor / audio_pipeline (lip_sync sub-step) / continuity_auditor
- **Bridge nodes:** `storyboard_designer` fills cinematographer → visual_executor gap with concrete Storyboard JSON
- **Audio-visual lock:** `audio_pipeline` (voicer sub-step) produces audio → `audio_pipeline` (lip_sync sub-step) aligns to footage (now intra-expert handoff; still decoupled, composable)
- **Bottleneck nodes:** `screenplay` (after style) / `visual_executor` (after intent) / `audio_pipeline` (after all audio + footage) — single node now subsumes lip_sync + mixer bottleneck roles
- **Audit nodes:** `continuity_auditor` (parallel to audio_pipeline) + `script_auditor` (pre-production) verify consistency
- **AI-native prompt assembly:** `prompt_injector` (Phase 16) translates visual_intent + style_genome_5d + character_assets into model_prompts + consistency_context consumed by visual_executor. No traditional cinematography precedent — this node exists because AI generation requires explicit prompt engineering that human director tools did not. Indirect path from DAG root: creative_source → style_genome → cinematographer → storyboard_designer → prompt_injector.
- **Independent validation:** 5 Phase 7 experts all have non-LLM-judge validation protocols (Pearson / LSE / CLIP-I / DTW / Bourdieu-field-accuracy)
- **Phase 8 verticals (cross-cutting):** `theory_critic` / `documentary_maker` / `animation_studio` are NOT in the linear pipeline — they are **consultative experts** invoked when the pipeline encounters their domain (theory analysis, documentary-style, animation). They draw from `_shared/project-corpus/` (102-book library).

### Phase 8 Cross-Cutting Experts (consultative layer)

```text
                ┌──────────────────────────────────┐
                │  Project Corpus (102 books)       │
                │  _shared/project-corpus/          │
                │  ┌────────────────────────────┐  │
                │  │ theory-formalism-vs-realism │  │
                │  │ film-philosophy-bazin-tark  │  │
                │  │ psychoanalytic-film-theory  │  │
                │  │ auteur-biographies          │  │
                │  │ film-criticism-methodology  │  │
                │  │ film-history-methods        │  │
                │  │ narrative-revolution-modern  │  │
                │  │ cinematography-masterclass  │  │
                │  │ lighting-equipment-design   │  │
                │  │ editing-sound-post          │  │
                │  │ production-chinese-low      │  │
                │  │ animation-disney-system     │  │
                │  │ screenwriting-chinese       │  │
                │  └────────────────────────────┘  │
                └────┬─────────────┬───────────────┬┘
                     │             │               │
                     ▼             ▼               ▼
              ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
              │   theory_   │ │ documentary │ │ animation_  │
              │   critic    │ │   _maker    │ │   studio    │
              │  理论批评    │ │  纪录片创作  │ │  动画制作    │
              └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                     │               │               │
                     └───────────────┼───────────────┘
                                     │
                          (cross-cutting consultation)
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │  Existing Linear Pipeline         │
                  │  (creative_source → ... → mixer)  │
                  └──────────────────────────────────┘
```


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
| compliance_gate | 5 | ~80 KB | 2026-06-15 |
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
   for EXP in screenplay editor colorist style_genome cinematographer compliance_gate hook_retention production; do
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
├── animator/           SKILL.md (Phase 14 redirect stub) — references/ + GAP-REPORT.md preserved archival
├── visual_executor/   SKILL.md + references/{drawer/{flux2-parameter-surface,character-consistency-lora},animator/{video-gen-model-matrix,temporal-consistency,camera-execution-and-degradation}}.md + drawer/LICENSE.md + animator/LICENSE.md + GAP-REPORT.md (Phase 5 + Phase 14 merge)
├── cinematographer/    SKILL.md + references/{shot-grammar,axis-rules,vertical-screen-framing,camera-motion-catalog}.md + LICENSE.md (Phase 4)
├── colorist/           SKILL.md + references/{bellantoni,hurkman,cross-cultural,cn-audience,digital-science}.md + LICENSE.md (Phase 3 deep)
├── compliance_gate/     SKILL.md + references/{cn-content-rules,viral-element-catalog,platform-douyin,platform-kuaishou,platform-miniprogram}.md + LICENSE.md (Phase 1)
├── audio_pipeline/     SKILL.md + references/{voicer/{cn-tts-model-matrix,character-voice-consistency,tts-emotion-prosody-control},lip_sync/{sync-quality-metrics,latentsync-deployment,audio-video-input-spec,identity-preservation},composer/{musicgen-workflow,chion-audio-vision,bgm-and-song-creation},foley/{stable-audio-open,sound-effect-taxonomy,sound-effects-prompt-engineering},mixer/{mixing-secrets-small-studio,lufs-standards},spatial_audio/{dolby-atmos-workflow,immersive-sound-design}}.md + {voicer,lip_sync,composer,foley,mixer,spatial_audio}/LICENSE.md + GAP-REPORT.md (Phase 5 + Phase 7A-2 + Phase 15 merge)
├── composer/           SKILL.md (Phase 15 redirect stub — merged_into audio_pipeline) — references/ + GAP-REPORT.md preserved archival
├── continuity_auditor/ SKILL.md + references/{cross-shot-auditing,eyeline-match-protocol}.md + LICENSE.md (Phase 5)
├── drawer/             SKILL.md (Phase 14 redirect stub) — references/ + GAP-REPORT.md preserved archival
├── editor/             SKILL.md + references/{murch,classical,montage,fxrxt,cn-cutting}.md + LICENSE.md (Phase 3 deep)
├── foley/              SKILL.md (Phase 15 redirect stub — merged_into audio_pipeline) — references/ + GAP-REPORT.md preserved archival
├── hook_retention/     SKILL.md + references/{three-second-hooks,conflict-escalation,paywall-design,vertical-pacing}.md + LICENSE.md (Phase 2)
├── mixer/              SKILL.md (Phase 15 redirect stub — merged_into audio_pipeline) — references/ + GAP-REPORT.md preserved archival
├── performer/          SKILL.md + references/{stanislavski-prepares,meisner-truth}.md + LICENSE.md (Phase 5)
├── production/         SKILL.md + references/{casting-lora-spec,wardrobe-per-scene,lighting-intent-layer,gpu-render-budget,asset-reuse-plan}.md + LICENSE.md (Phase 5)
├── scene_builder/      SKILL.md + references/{blender-previz-workflow,architectural-storytelling}.md + LICENSE.md (Phase 5)
├── screenplay/         SKILL.md + references/{save-the-cat,mckee,cn-shortdrama,emotion-curve-academic,dialogue-craft}.md + LICENSE.md (Phase 3 deep)
├── spatial_audio/      SKILL.md (Phase 15 redirect stub — folded_into audio_pipeline) — references/ preserved archival
├── style_genome/       SKILL.md + references/{director-dna-archive,genre-dna-taxonomy,auteur-theory,cross-cultural-style,cn-director-analysis,art-direction-methodology}.md + LICENSE.md (Phase 3 deep + Phase 7C increment)
├── voicer/             SKILL.md (Phase 15 redirect stub — merged_into audio_pipeline) — references/ + GAP-REPORT.md preserved archival
├── script_auditor/     SKILL.md + references/{narrative-structure-audit,emotion-arc-audit,hook-strength-audit,character-network-audit,completion-rate-forecast}.md + LICENSE.md (Phase 7A-1 NEW)
├── lip_sync/           SKILL.md (Phase 15 redirect stub — merged_into audio_pipeline) — _eval/ regression suite preserved archival
├── character_designer/ SKILL.md + references/{4d-anchor-system,layered-style-prefix,consistency-stress-test,character-bible-schema}.md + LICENSE.md (Phase 7B-1 NEW)
├── storyboard_designer/ SKILL.md + references/{shot-decomposition-rules,camera-params-dictionary,4d-anchoring-params,storyboard-schema}.md + LICENSE.md (Phase 7B-2 NEW)
├── creative_source/    SKILL.md + references/{strata-guide,story-kernel-schema,multi-strata-resonance,unspeakability-protocol}.md + LICENSE.md (Phase 7B-3 NEW)
├── prompt_injector/                    # Phase 16 NEW (2026-06-17) — AI-native prompt engineering node
│   ├── SKILL.md                        # Prompt Injector Expert (提示注入)
│   ├── GAP-REPORT.md                   # placeholder per CONTEXT D-04 (NEW expert, no v1 baseline)
│   └── references/
│       ├── prompt-engineering-patterns.md     # few-shot / CoT / template / decomposition
│       ├── cross-call-consistency.md          # LoRA / IP-Adapter / identity-preserving
│       ├── token-budget-management.md         # ≤4000 tokens/call strategies
│       ├── model-specific-prompt-templates.md # FLUX 2 / Veo / Kling (provider-agnostic placeholders)
│       └── LICENSE.md                         # MIT + source attribution
├── _eval/
│   ├── runner.py                                 (MT-Bench position-swap harness)
│   ├── config.yaml.example                       (3-condition ablation template)
│   ├── judge_prompt.md                           (4-dimension rubric)
│   ├── prompts/
│   │   ├── animator_demo.yaml
│   │   ├── cinematographer_demo.yaml
│   │   ├── colorist_demo.yaml
│   │   ├── compliance_gate_demo.yaml
│   │   ├── editor_demo.yaml
│   │   ├── hook_retention_demo.yaml
│   │   ├── production_demo.yaml
│   │   ├── screenplay_demo.yaml
│   │   ├── style_genome_demo.yaml
│   │   ├── script_auditor_demo.yaml             (Phase 7A-1 NEW)
│   │   ├── lip_sync_demo.yaml                   (Phase 7A-2 NEW)
│   │   ├── character_designer_demo.yaml         (Phase 7B-1 NEW)
│   │   ├── storyboard_designer_demo.yaml        (Phase 7B-2 NEW)
│   │   └── creative_source_demo.yaml            (Phase 7B-3 NEW)
│   ├── baseline/                                 (Phase 0 pre-refactor snapshots × 14)
│   └── reports/                                  (dry-run + Phase 3 GO/NO-GO reports)
└── _shared/
    ├── glossary.md                               (EN↔CN term dictionary — Phase 7 expanded)
    ├── known-external-models.yaml                (model name allowlist — Phase 7 expanded)
    ├── platform-comparison.md
    ├── RAG-INVOCATION-PATTERN.md
    ├── SKILL-LAYOUT.md                           (reference anatomy spec)
    ├── cognitive-resonance-metrics.md            (Phase 7C-1 NEW — 4-scale evaluation rubric)
    └── quality-rubric.md                         (Phase 7C-2 NEW — 6-dim publish-gate rubric)
```

---

## Project Planning Artifacts

- [`.planning/PROJECT.md`](../../.planning/PROJECT.md) — project context + core value + constraints
- [`.planning/REQUIREMENTS.md`](../../.planning/REQUIREMENTS.md) — 62 v1.5 requirements (FOUND ×9, COMPLI ×9, HOOK ×9, REFACTOR ×8, REFACTOR-rest ×10, CINE ×9, PROD ×7, EVAL ×9, DOC ×4)
- [`.planning/ROADMAP.md`](../../.planning/ROADMAP.md) — 7-phase build order (all phases 0-6 complete)
- [`.planning/STATE.md`](../../.planning/STATE.md) — current execution state

---

## License

Each expert's `references/LICENSE.md` documents the fair-use attribution for its ref corpus. The suite code (runner.py, etc.) is MIT.

## Citation

If you build on this suite, please cite:
- Phase 0 audit + eval skeleton: PROJECT.md §Core Value
- Phase 3 deep refactor approach: 03-CONTEXT.md §Decisions
- Phase 4 cinematographer: 04-CONTEXT.md §Phase Boundary
- Phase 5 production + RAG uplift: 05-CONTEXT.md §Phase Boundary

---

*Movie-Experts Suite v2 — built 2026-06-15 (Phases 0-6) + 2026-06-16 (Phase 7) + 2026-06-17 (Phases 13-16).*
*v3.0 = 18 active expert_ids (17 post-Phase-15 + 1 Phase 16 prompt_injector NEW — AI-native, no v1 predecessor) — Phase 17 will deprecate 3 candidates (performer, scene_builder, storyboard_designer); Phase 18 will reconcile to canonical 21-expert topology (16 DAG pipeline-roles + 5 aliases). All RAG-aware, all phantom refs stripped.*
*Total ref corpus: ~85 files (~1.9MB cited fair-use content).*
*5 Phase 7 experts carry independent validation protocols (no LLM-judge required).*
*Live-run statistical GO/NO-GO evidence deferred to operator per CONTEXT D-11.*

---

## Phase 7 additions summary (2026-06-16)

**5 new experts** with independent validation protocols:
- `script_auditor` — 5-dim quantitative script audit (Pearson vs actual 完播率)
- `audio_pipeline` (lip_sync sub-step) — audio-driven lip sync (LRS2/LRS3 international benchmark, LSE/LSE-C objective metrics)
- `character_designer` — CharacterBible 2.0 authoring (CLIP-I/DINO-I cross-scene consistency)
- `storyboard_designer` — Scene → Storyboard JSON decomposition (shot count accuracy / rhythm DTW)
- `creative_source` — Story Kernel mining from 6 social strata (Bourdieu field accuracy / unspeakability AUC)

**7 reference increments** in existing experts:
- `_shared/cognitive-resonance-metrics.md` (NEW) — 4-scale evaluation rubric from 1st-director doctrine
- `_shared/quality-rubric.md` (NEW) — 6-dim publish-gate rubric from movie-gate doctrine
- `style_genome/references/art-direction-methodology.md` (NEW) — from kais-art-direction
- `audio_pipeline/references/composer/bgm-and-song-creation.md` (NEW) — from kais-bgm + kais-song-agent
- `audio_pipeline/references/foley/sound-effects-prompt-engineering.md` (NEW) — from kais-sound-effects-agent
- `audio_pipeline/references/voicer/tts-emotion-prosody-control.md` (NEW) — from kais-TTS-agent
- `visual_executor/references/animator/camera-execution-and-degradation.md` (NEW) — from kais-camera + kais-shooting-script + kais-evolink

**Decoupling principle:** All Phase 7 experts are pure nodes (no orchestration). Each owns a vertical capability with clear I/O schema + benchmark + objective metrics. The 5 new experts follow the project constraint: "每个专家 skill 专精自己的方向,目标是在每个专精方向的产出做到可迭代进步,可独立评估,有数据集可验证自己是否有提升."
