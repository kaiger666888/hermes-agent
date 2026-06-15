# Movie-Experts Suite v2 — 短剧/微电影创作专家增强

**Project:** RAG-augmented movie-expert skill suite for AI 短剧 / 微电影 production.
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Status:** v2 complete — 23 experts (14 original + 4 Phase 1-5 + 5 Phase 7 — SCRIPT_AUDIT / LIP_SYNC / CHARACTER / STORYBOARD / CREATIVE). All RAG-aware. 5 new experts have independent validation protocols (no LLM-judge required).
**Last updated:** 2026-06-16

---

## Suite Overview

23 specialists covering the entire AI 短剧 / 微电影 creation pipeline, from creative-source mining through final mix + lip-sync. Each expert is a self-contained Hermes skill (`SKILL.md` + `references/*.md`) that integrates with the others via declared `related_skills` edges. Total ref corpus: ~80 files (~1.8MB cited fair-use content).

### 14 Original Experts (Phase 0 baselined; 4 deep-refactored Phase 3, 10 light-uplifted Phase 5)

| Expert | Chinese Name | Role | Refs |
|--------|--------------|------|------|
| [`style_genome`](./style_genome/SKILL.md) | 风格基因专家 | 5D director/genre style encoding + blend protocol + cross-module alignment (root expert) | 5 (Phase 3 deep) |
| [`screenplay`](./screenplay/SKILL.md) | 剧本专家 | Scene-level script + dialogue + emotion_curve design (HOOK-09 marker schema integrated) | 5 (Phase 3 deep) |
| [`scene_builder`](./scene_builder/SKILL.md) | 三维场景建构专家 | FxSxA scene matrix + Blender 4.x previz + Pallasmaa space-as-character doctrine | 2 (Phase 5 light) |
| [`performer`](./performer/SKILL.md) | 表演专家 | ExBxSxP matrix + Stanislavski + Laban Effort + Meisner truth-of-moment | 2 (Phase 5 light) |
| [`drawer`](./drawer/SKILL.md) | 绘图专家 | FLUX 2 Klein 9B + LoRA + IP-Adapter + InstantID character consistency | 2 (Phase 5 light) |
| [`animator`](./animator/SKILL.md) | 视频专家 | Hermes-catalog video gen (veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0) + temporal consistency | 2 (Phase 5 light) |
| [`colorist`](./colorist/SKILL.md) | 色彩专家 | CxSxZ 28-combination color intent + LUT design + Bellantoni color psychology | 5 (Phase 3 deep) |
| [`editor`](./editor/SKILL.md) | 剪辑专家 | FxRxT editing matrix + Murch Rule of Six + 180° axis compliance | 5 (Phase 3 deep) |
| [`composer`](./composer/SKILL.md) | 配乐专家 | MusicGen-Large 4 mode + Chion audio-vision 5 modes + emotion_curve sync | 2 (Phase 5 light) |
| [`foley`](./foley/SKILL.md) | 拟音专家 | Stable Audio Open 1.0 (replaces phantom AudioLDM-2) + 7D parametric + BBC 21-cat taxonomy | 2 (Phase 5 light) |
| [`spatial_audio`](./spatial_audio/SKILL.md) | 空间音频专家 | Dolby Atmos Bed+Objects + 6D encoding + HRTF binaural + 5 immersive patterns | 2 (Phase 5 light) |
| [`mixer`](./mixer/SKILL.md) | 混音专家 | Senior Mixing Secrets + LUFS per-platform + dialogue ducking + EQ carving | 2 (Phase 5 light) |
| [`voicer`](./voicer/SKILL.md) | 配音专家 | Multi-provider TTS (MiniMax/ElevenLabs/Voxtral/Gemini/Edge/NeuTTS, replaces phantom CosyVoice) + speaker embedding | 2 (Phase 5 light) |
| [`continuity`](./continuity/SKILL.md) | 连续性专家 | 4-dimension cross-shot audit (face/wardrobe/color/object) + eyeline match + 180° axis | 2 (Phase 5 light) |

### 4 New Experts (Phase 1-5)

| Expert | Chinese Name | Role | Phase Built | Refs |
|--------|--------------|------|-------------|------|
| [`compliance_marketing`](./compliance_marketing/SKILL.md) | 合规与宣发专家 | CN content-rules gate + AIGC labeling + per-platform distribution + 爆款 vs 红线 review | Phase 1 | 5 |
| [`hook_retention`](./hook_retention/SKILL.md) | 钩子与留存专家 | 3-second hook design + 付费卡点 placement + per-platform 爆款公式 + 钩子/爽点/卡点 marker schema | Phase 2 | 4 |
| [`cinematographer`](./cinematographer/SKILL.md) | 镜头专家 | Shot intent layer (shot scale + composition + axis + camera move) + vertical 9:16 framing + 2026 video gen model prompt-token mapping | Phase 4 | 4 |
| [`production`](./production/SKILL.md) | 制作管理专家 | AI-relevant subset: character LoRA spec / per-scene wardrobe / lighting intent / GPU budget / asset reuse (NOT live-action per PROD-07) | Phase 5 | 5 |

### 5 New Experts (Phase 7 — independent validation, no LLM-judge required)

| Expert | Chinese Name | Role | Validation Protocol | Refs |
|--------|--------------|------|---------------------|------|
| [`script_auditor`](./script_auditor/SKILL.md) | 剧本审计专家 | 5-dimension quantitative script audit (narrative / emotion / hook / character / completion-forecast) BEFORE production. Decoupled from screenplay (screenplay writes, script_auditor audits) | Pearson correlation between predicted & actual 完播率 ≥ 0.65 on 100-script labeled corpus | 5 |
| [`lip_sync`](./lip_sync/SKILL.md) | 唇形同步专家 | Audio-driven lip sync (LatentSync v1.5/v1.6) producing synced video from (footage + audio) pair. Decoupled from voicer (voicer synthesizes audio, lip_sync aligns audio to footage) | LSE / LSE-C / SyncNet confidence on **LRS2 / LRS3 international-standard benchmark** (SOTA target LSE ≤ 5.5) | 4 |
| [`character_designer`](./character_designer/SKILL.md) | 角色设计专家 | Character Bible 2.0 authoring with 4D-Anchor (front/3-quarter/side/back) + layered STYLE_PREFIX (CORE/IDENTITY/VARIANCE) + consistency stress test. Decoupled from drawer (drawer generates images, character_designer defines identity contract) | CLIP-I / DINO-I cross-scene similarity ≥ 0.80 on 30-character × 7-image corpus | 4 |
| [`storyboard_designer`](./storyboard_designer/SKILL.md) | 分镜设计专家 | Scene → per-shot Storyboard JSON decomposition with camera params + 4D anchoring (depth/identity/lighting/temporal) + extension-chain end_frames. Decoupled from cinematographer (cinematographer defines rules, storyboard_designer applies them) | Shot count accuracy / shot size distribution KL / rhythm curve DTW vs professional ground truth on 50-script corpus | 4 |
| [`creative_source`](./creative_source/SKILL.md) | 创意源头专家 | Story Kernel mining from 6 social strata (institutional / technological / demographic / spatial / intergenerational / psychosocial). DAG root — upstream of style_genome. Sources: Bourdieu / Foucault / Giddens + Lefebvre + Han Byung-Chul | Strata resonance Pearson / Bourdieu field accuracy / unspeakability AUC on 100-topic labeled corpus | 4 |

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
                │   剧本           │  │ 钩子与留存       │  │ marketing 合规  │
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
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
       ┌───────────────┐  ┌───────────────┐
       │   lip_sync    │  │  voicer       │
       │   唇形同步     │  │  配音 (TTS)    │
       │ (LSE/LSE-C)   │  │               │
       └───────┬───────┘  └───────┬───────┘
               │                  │
               └──────────┬───────┘
                          │
                          ▼
                ┌──────────────────┐
                │  colorist /      │
                │  editor /        │
                │  composer / foley│
                │  / spatial_audio │
                └────────┬─────────┘
                         │
                         ▼
                ┌─────────────────┐
                │     mixer       │ ◄──── continuity (parallel audit)
                │     混音         │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   FINAL OUTPUT  │
                │  (短剧 / 微电影)  │
                └─────────────────┘
```

**Key DAG properties (v2 with Phase 7):**
- **New root:** `creative_source` (no upstream; mines Story Kernel from social strata) — replaces style_genome as DAG root
- **Quality loop:** `screenplay` ↔ `script_auditor` iterate until target audit band
- **Identity contract:** `character_designer` emits CharacterBible 2.0 consumed by drawer / animator / lip_sync / continuity
- **Bridge nodes:** `storyboard_designer` fills cinematographer → drawer gap with concrete Storyboard JSON
- **Audio-visual lock:** `voicer` produces audio → `lip_sync` aligns to footage (decoupled, composable)
- **Bottleneck nodes:** `screenplay` (after style) / `drawer` (after intent) / `lip_sync` (after audio + footage) / `mixer` (after all audio)
- **Audit nodes:** `continuity` (parallel to mixer) + `script_auditor` (pre-production) verify consistency
- **Independent validation:** 5 Phase 7 experts all have non-LLM-judge validation protocols (Pearson / LSE / CLIP-I / DTW / Bourdieu-field-accuracy)

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
   for EXP in screenplay editor colorist style_genome cinematographer compliance_marketing hook_retention production; do
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
├── animator/           SKILL.md + references/{video-gen-model-matrix,temporal-consistency,camera-execution-and-degradation}.md + LICENSE.md (Phase 5 + Phase 7C increment)
├── cinematographer/    SKILL.md + references/{shot-grammar,axis-rules,vertical-screen-framing,camera-motion-catalog}.md + LICENSE.md (Phase 4)
├── colorist/           SKILL.md + references/{bellantoni,hurkman,cross-cultural,cn-audience,digital-science}.md + LICENSE.md (Phase 3 deep)
├── compliance_marketing/ SKILL.md + references/{cn-content-rules,viral-element-catalog,platform-douyin,platform-kuaishou,platform-miniprogram}.md + LICENSE.md (Phase 1)
├── composer/           SKILL.md + references/{musicgen-workflow,chion-audio-vision,bgm-and-song-creation}.md + LICENSE.md (Phase 5 + Phase 7C increment)
├── continuity/         SKILL.md + references/{cross-shot-auditing,eyeline-match-protocol}.md + LICENSE.md (Phase 5)
├── drawer/             SKILL.md + references/{flux2-parameter-surface,character-consistency-lora}.md + LICENSE.md (Phase 5)
├── editor/             SKILL.md + references/{murch,classical,montage,fxrxt,cn-cutting}.md + LICENSE.md (Phase 3 deep)
├── foley/              SKILL.md + references/{stable-audio-open,sound-effect-taxonomy,sound-effects-prompt-engineering}.md + LICENSE.md (Phase 5 + Phase 7C increment)
├── hook_retention/     SKILL.md + references/{three-second-hooks,conflict-escalation,paywall-design,vertical-pacing}.md + LICENSE.md (Phase 2)
├── mixer/              SKILL.md + references/{mixing-secrets-small-studio,lufs-standards}.md + LICENSE.md (Phase 5)
├── performer/          SKILL.md + references/{stanislavski-prepares,meisner-truth}.md + LICENSE.md (Phase 5)
├── production/         SKILL.md + references/{casting-lora-spec,wardrobe-per-scene,lighting-intent-layer,gpu-render-budget,asset-reuse-plan}.md + LICENSE.md (Phase 5)
├── scene_builder/      SKILL.md + references/{blender-previz-workflow,architectural-storytelling}.md + LICENSE.md (Phase 5)
├── screenplay/         SKILL.md + references/{save-the-cat,mckee,cn-shortdrama,emotion-curve-academic,dialogue-craft}.md + LICENSE.md (Phase 3 deep)
├── spatial_audio/      SKILL.md + references/{dolby-atmos-workflow,immersive-sound-design}.md + LICENSE.md (Phase 5)
├── style_genome/       SKILL.md + references/{director-dna-archive,genre-dna-taxonomy,auteur-theory,cross-cultural-style,cn-director-analysis,art-direction-methodology}.md + LICENSE.md (Phase 3 deep + Phase 7C increment)
├── voicer/             SKILL.md + references/{cn-tts-model-matrix,character-voice-consistency,tts-emotion-prosody-control}.md + LICENSE.md (Phase 5 + Phase 7C increment)
├── script_auditor/     SKILL.md + references/{narrative-structure-audit,emotion-arc-audit,hook-strength-audit,character-network-audit,completion-rate-forecast}.md + LICENSE.md (Phase 7A-1 NEW)
├── lip_sync/           SKILL.md + references/{sync-quality-metrics,latentsync-deployment,audio-video-input-spec,identity-preservation}.md + LICENSE.md (Phase 7A-2 NEW)
├── character_designer/ SKILL.md + references/{4d-anchor-system,layered-style-prefix,consistency-stress-test,character-bible-schema}.md + LICENSE.md (Phase 7B-1 NEW)
├── storyboard_designer/ SKILL.md + references/{shot-decomposition-rules,camera-params-dictionary,4d-anchoring-params,storyboard-schema}.md + LICENSE.md (Phase 7B-2 NEW)
├── creative_source/    SKILL.md + references/{strata-guide,story-kernel-schema,multi-strata-resonance,unspeakability-protocol}.md + LICENSE.md (Phase 7B-3 NEW)
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

*Movie-Experts Suite v2 — built 2026-06-15 (Phases 0-6) + 2026-06-16 (Phase 7).*
*v2 = 23 experts (14 original + 4 Phase 1-5 + 5 Phase 7), all RAG-aware, all phantom refs stripped.*
*Total ref corpus: ~80 files (~1.8MB cited fair-use content).*
*5 Phase 7 experts carry independent validation protocols (no LLM-judge required).*
*Live-run statistical GO/NO-GO evidence deferred to operator per CONTEXT D-11.*

---

## Phase 7 additions summary (2026-06-16)

**5 new experts** with independent validation protocols:
- `script_auditor` — 5-dim quantitative script audit (Pearson vs actual 完播率)
- `lip_sync` — audio-driven lip sync (LRS2/LRS3 international benchmark, LSE/LSE-C objective metrics)
- `character_designer` — CharacterBible 2.0 authoring (CLIP-I/DINO-I cross-scene consistency)
- `storyboard_designer` — Scene → Storyboard JSON decomposition (shot count accuracy / rhythm DTW)
- `creative_source` — Story Kernel mining from 6 social strata (Bourdieu field accuracy / unspeakability AUC)

**7 reference increments** in existing experts:
- `_shared/cognitive-resonance-metrics.md` (NEW) — 4-scale evaluation rubric from 1st-director doctrine
- `_shared/quality-rubric.md` (NEW) — 6-dim publish-gate rubric from movie-gate doctrine
- `style_genome/references/art-direction-methodology.md` (NEW) — from kais-art-direction
- `composer/references/bgm-and-song-creation.md` (NEW) — from kais-bgm + kais-song-agent
- `foley/references/sound-effects-prompt-engineering.md` (NEW) — from kais-sound-effects-agent
- `voicer/references/tts-emotion-prosody-control.md` (NEW) — from kais-TTS-agent
- `animator/references/camera-execution-and-degradation.md` (NEW) — from kais-camera + kais-shooting-script + kais-evolink

**Decoupling principle:** All Phase 7 experts are pure nodes (no orchestration). Each owns a vertical capability with clear I/O schema + benchmark + objective metrics. The 5 new experts follow the project constraint: "每个专家 skill 专精自己的方向,目标是在每个专精方向的产出做到可迭代进步,可独立评估,有数据集可验证自己是否有提升."
