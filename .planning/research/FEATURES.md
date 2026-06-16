# Feature Research — v2.0 PRFP Pipeline Node Set

**Domain:** AIGC-native 短剧 / 微电影 production pipeline — node-set DESIGN DOCS only (no implementation)
**Researched:** 2026-06-16
**Overall confidence:** MEDIUM-HIGH — traditional film workflow grounded in 102-book corpus (HIGH); AIGC-native pattern claims drawn from ComfyUI/LangGraph ecosystem knowledge + general industry awareness, not project-specific benchmarks (MEDIUM).

> **Scope clarification.** This is NOT user-facing product feature research. It answers: *which nodes should appear in a from-scratch AIGC film pipeline DAG, what should each node be accountable for, and what node-design temptations are wrong?*
> Mapping per milestone context:
> - **Table stakes** = nodes every AIGC film pipeline must contain
> - **Differentiators** = nodes that distinguish a first-principles-derived pipeline from a copy-of-traditional-workflow pipeline
> - **Anti-features** = node-design temptations that are wrong (over-decomposition, AI-as-drop-in, redundant gates)

---

## Executive Framing

Two design philosophies are in tension:

1. **Imitation of traditional** = take the pre-prod / prod / post-prod workflow and replace each human role with an LLM call. Produces a 30-node pipeline that mirrors the 102-book corpus's工序 but doesn't exploit what AIGC changes structurally.
2. **First-principles derivation (Musk-style)** = start from "what does the viewer need to receive", "where does 短剧 live-or-die (3 seconds)", "what can AI actually compress", "what can AI not replace". Derive minimal necessary node set.

The research below enumerates candidates under BOTH philosophies so the roadmapper can pick. The selection criteria in §5 and the anti-features in §6 push toward (2).

---

## 1. Traditional Film Workflow — Canonical Stages (from 102-book corpus)

This is the raw material any first-principles derivation must either justify keeping, justify eliminating, or justify merging.

### 1.1 Universal stages (every film, every format, every era)

Drawn from the corpus index at `skills/movie-experts/_shared/project-corpus/README.md`. Each stage has a cited source.

| Stage (CN/EN) | Corpus Source (Project ID / Title) | Universal? |
|---|---|---|
| **创意/选题 (Idea mining)** | 《创意制片完全手册》(070);芦苇《白鹿原》七易其稿笔记 (【白鹿原】) | YES — every film starts from "what story" |
| **剧本 (Screenplay)** | 菲尔德《电影剧本写作基础》(-017);麦基《故事》(-026);奥班农《剧本结构设计》(069);维基·金《21天搞定电影剧本》(009);芦苇/刘天赐 | YES — even 无情节 (Antonioni, -004) is a script decision |
| **角色 (Character)** | 斯坦尼《演员的自我修养》(-058);斯特拉·阿德勒《表演的艺术》(062);乌塔·哈根《尊重表演艺术》(048) | YES — every film has кто (who) |
| **分镜/导演 (Storyboard / Directing)** | 阿里洪《电影语言的语法》(-025/037);卡茨《电影镜头设计》(006);《场面调度》(012);马梅《导演功课》(-008);van Sijll《电影化叙事100手法》(-035) | YES — even improv documentary has framing decisions |
| **摄影/光线 (Cinematography / Lighting)** | 《影视光线艺术》(-063);《电影照明器材与操作》(044);《光影创作课》(076);《镜头在说话》(007) | YES — every film encodes space visually |
| **美术/场景 (Production design)** | 《狼图腾:视觉设计与叙事语言》(【狼图腾】);《电影特技模型制作》(061) | YES — even a blank-wall film has production design (= "blank wall" was designed) |
| **表演 (Performance)** | 同 4 | YES for live-action/animation; NO for pure 漫剧/AI-still formats |
| **剪辑 (Editing)** | 默奇《剪辑之道》(071);傅正义《电影电视剪辑学》(-010);《魅力·剪辑》 | YES — assembly is universal |
| **声音 (Sound design / mix)** | 《音效圣经》(032);希翁《视听:幻觉的构建》(060) | YES — even silent film has sound (= silence is mixed) |
| **音乐 (Music)** | (no dedicated book in corpus — covered in editing-sound-post.md ref) | YES — even no-music is a music decision |
| **色彩 (Color)** | 《光影创作课》(076) part 2;第五代摄影 color theory per `lighting-equipment-and-design.md` | YES for color film; NO for monochrome |
| **理论/批评 (Theory / Critique)** | 巴赞《电影是什么》(-019/-020);塔可夫斯基《雕刻时光》(-022);Andrew《经典电影理论导论》(-045);戴锦华《电影批评》(-024) | NO — only for "serious" work; 短剧 often skips |

### 1.2 Genre/format-specific stages (NOT universal)

| Stage | Applies to | Corpus Source |
|---|---|---|
| **拟音 (Foley)** | Live-action + animation with hard effects | 《音效圣经》 |
| **空间音频 (Spatial audio)** | Dolby Atmos / VR / immersive | (corpus does not cover) |
| **配音/配音导演 (Voice direction)** | Animation / dubbed / 短剧 with TTS | (not in corpus as standalone) |
| **唇形同步 (Lip sync)** | Live-action with re-dubbing; AI-driven characters | (post-corpus practice) |
| **连续性 (Script supervisory)** | Multi-shot / multi-episode live-action | 《导演创作完全手册》(053) |
| **制片管理 (Production management)** | Any non-trivial production (>1 person) | 《电影制片手册》(-029);《好莱坞模式》(057);《影视预算手册》(074) |
| **合规 (Compliance)** | China 短剧 as of 2026-04-01;broadcast anywhere | (regulatory, not in corpus) |
| **宣发 (Distribution / marketing)** | Anything that needs an audience | 《创意制片完全手册》(070) part 3 |
| **运镜/摄影机运动 (Camera movement)** | 竖屏短剧 (essential for 完播率); feature film | 《场面调度》(012);cinematographer refs |
| **钩子/留存 (Hook & retention)** | 短剧 / 小程序剧 / 任何平台分发内容 | (post-corpus practice) |

### 1.3 Format-specific observations

- **微电影 (micro-film, 5-30 min):** follows traditional feature workflow compressed in time. McKee three-act applies. Theory-critic matters more than for 短剧.
- **竖屏短剧 (vertical 短剧, 60-90s/ep, 10-100 eps):** 钩子 + 卡点 + 爽点 drive survival; traditional 剧本 structure collapses. *Hook & retention is the structural equivalent of 剧本 for this format.*
- **AI 漫剧 (manga-style AI drama):** 表演 collapses into 角色设计 (no live actor); 唇形同步 becomes load-bearing; 拟音 becomes optional.

---

## 2. AIGC-Native Pipeline Patterns

What changes structurally when AI does the work? Distinguish from traditional workflow patterns.

### 2.1 Where AI COMPRESSES traditional multi-stage work into single nodes

| Traditional multi-stage | Compressed AIGC node | Mechanism | Risk |
|---|---|---|---|
| 故事构思 + 大纲 + 剧本 + 剧本医生 | **story-kernel generator** | LLM one-shot from idea + structural formula | Logic self-consistency may be lost (creative_source validation protocol addresses this) |
| 角色设计 + 试妆 + 选角 + 化妆 | **character-bible author** | 4D-anchor reference image + LoRA spec | Identity consistency becomes a separate verification node (cannot be folded) |
| 分镜 + 场面调度 + 镜头语言 + 拍摄 | **shot-intent + storyboard-JSON** | LLM emits structured JSON with shot_size / movement / lens / angle | "Camera move → prompt token" mapping must be a separate node (gen-model-dependent) |
| 摄影指导 + 摄影师 + 灯光师 + 美术 | **visual-generation node** | Diffusion model ingests prompt + reference | Style/identity lock requires separate consistency nodes (cannot be folded) |
| 剪辑 + 调色 + 混音 + 拟音 | **post-farm** (parallel) | Each is a distinct capability; may run in parallel | Audio-video lock becomes explicit handoff (not implicit) |
| 海报 + 预告片 + SEO 标题 | **distribution-cut generator** | LLM variants + editor clip extraction | 平台 compliance tailoring becomes per-platform fork |

### 2.2 Where AI EXPANDS traditional single-stage into multi-node loops

These are the structural reasons a first-principles pipeline may have MORE nodes than traditional at certain stages:

| Traditional single stage | Expanded AIGC sub-nodes | Why expansion is necessary |
|---|---|---|
| **角色一致性** (continuity of one character) | (a) character-bible (b) LoRA training (c) reference-image injection (d) cross-scene similarity verification (e) re-prompt loop | Diffusion models are stochastic; without explicit lock + verify loop, character drifts across cuts. Cannot collapse. |
| **剧本质量** (script quality) | (a) screenplay writer (b) script-auditor (5-dim quantitative) (c) revision loop | LLM writing is inconsistent; quantitative audit gates catch what human script-doctors would. Decoupling writer from auditor removes self-grading bias. |
| **镜头意图→视频** (camera intent → video) | (a) cinematographer (intent) (b) storyboard-designer (structured shot list) (c) prompt-injector (translate intent → model tokens) (d) video-gen executor (e) preview (f) final | Each translation loses information; explicit nodes preserve traceability + early failure detection. The camera-preview / camera-final split is the AIGC-native equivalent of "rough cut / final cut". |
| **音频-视频对齐** (audio-video lock) | (a) voicer (b) lip-sync (c) audio-video alignment verifier | TTS audio and generated video are independent streams; alignment is now an explicit node, not an implicit production step. |
| **风格一致性** (style consistency) | (a) style-genome (definition) (b) art-direction (asset) (c) per-shot prompt injection (enforcement) (d) style drift verifier | Diffusion model prompts drift; a style must be defined once, encoded as a reusable asset, and verified per shot. |

### 2.3 Agent-orchestration patterns observed in AIGC tooling

From research on ComfyUI workflows + LangGraph + plan-and-execute agents:

| Pattern | Source | When it applies | Caution |
|---|---|---|---|
| **Node graph (DAG)** | ComfyUI; Blender shader graph | Visual asset pipelines; deterministic data flow | Tempting to over-decompose into 100 micro-nodes; resist |
| **Planner-Executor-Critic** | LangGraph plan-and-execute; Reflexion pattern | Creative generation tasks where output quality varies | The critic must be measurable, not vibes — otherwise just noise |
| **Human-in-the-loop gate** | LangGraph HITL; review-platform in kais-movie-agent | High-stakes irreversible decisions (character lock, final delivery) | Each gate multiplies latency; only where cost-of-error > cost-of-delay |
| **Stateful workflow with checkpointing** | LangGraph checkpointing; kais-movie-agent `.pipeline-state.json` | Long-running pipelines that may fail mid-run | Essential for resume; not a creative decision, an infra decision |
| **Tool dispatch** | MCP; Hermes tool registry | Nodes that need to call external models | Should be invisible at the design-doc layer |

**Key distinction from traditional workflow patterns:** AIGC pipelines are **stateful graphs with feedback loops**, whereas traditional film workflows are **linear with implicit feedback** (e.g., editor tells DP to reshoot). The DAG formalism is correct; what must be designed carefully is *where the loops live*.

### 2.4 Video-gen chain variants

Two distinct AIGC-native patterns for visual generation, with different node implications:

| Pattern | Examples | Node implication |
|---|---|---|
| **Shot-by-shot (Runway/Pika/Sora-style)** | Generate per-shot from prompt + reference; stitch in editor | Requires shot-decomposition node, character-lock node, per-shot prompt-injector node |
| **Direct long-form (Wan/LTX-style)** | Generate longer continuous clip from one prompt | Reduces shot-decomposition overhead but introduces temporal-consistency node (currently unreliable) |

For 短剧/微电影 in 2026, **shot-by-shot is the mature pattern**. Direct long-form is a research bet.

---

## 3. Node Candidates Enumeration

Grouped by phase. ≥30 candidates listed. For each: traditional工序 mapping / AIGC enabler / merge-split-eliminate candidacy.

**Legend:** ⭐=table-stakes (universal) / 🔷=differentiator (first-principles-derived) / 🚫=anti-feature candidate (likely wrong)

### 3.1 Pre-Production (idea → script → character → shot-plan)

| # | Node candidate | Maps to traditional | AIGC enabler | Merge / Split / Eliminate |
|---|---|---|---|---|
| 1 ⭐ | **creative-source / story-kernel** | 选题 + 创意制片 (070) | LLM compresses social-strata analysis to single structural_formula (see creative_source SKILL.md) | KEEP — DAG root |
| 2 ⭐ | **style-genome / art-direction** | 风格定位 + 美术指导 (【狼图腾】) | 5D style vector + LUT-able color anchor | KEEP — defines reusable asset |
| 3 ⭐ | **screenplay** | 剧本 (菲尔德/麦基/芦苇) | LLM scene-level generation | KEEP — but see split candidates |
| 4 🔷 | **script-auditor (5-dim quantitative)** | 剧本医生 (informal) | LLM-as-judge with Pearson-validated metric | SPLIT from screenplay — self-grading bias removed |
| 5 ⭐ | **character-bible / character-designer** | 角色设计 + 选角 + 服化道 (斯坦尼/阿德勒) | 4D-anchor + LoRA spec + consistency stress test | KEEP — identity contract for all downstream |
| 6 🔷 | **hook-retention / commercial engine** | (none traditional; 短剧-specific) | Marker schema for 钩子/爽点/卡点 mechanically consumed by editor/screenplay | KEEP — for 竖屏短剧 this REPLACES part of screenplay's role |
| 7 ⭐ | **cinematographer (shot intent)** | 摄影指导 + 场面调度 (012/006) | Movement-emotion dictionary + lens-as-narrative | KEEP — defines intent |
| 8 🔷 | **storyboard-designer (structured JSON)** | 分镜师 (《电影语言的语法》) | LLM emits shot_size/movement/lens/angle JSON | KEEP — bridge between intent and execution |
| 9 🔷 | **theory-critic (consultative)** | 理论批评 (巴赞/塔可夫斯基/戴锦华) | LLM applies theoretical framework as diagnostic | OPTIONAL — vertical, not in linear pipeline |
| 10 🔷 | **compliance-pre-check** | (none traditional; regulatory new) | LLM 红线 scan before production | KEEP — must gate before costly generation |
| 11 🚫 | *outline-writer as separate node* | 大纲 | LLM can produce scene-level directly | ELIMINATE — fold into screenplay |
| 12 🚫 | *episode-breakdown as separate node* | 分集 | For 短剧 this is part of screenplay/hook-retention | ELIMINATE — fold into hook-retention |
| 13 🚫 | *audience-analysis as separate node* | 受众研究 | LLM can be a sub-routine of screenplay | MERGE into screenplay input |
| 14 🔷 | **topic-curatorial scan** (creative_source daily-scan mode) | (none) | Cron-triggered LLM scan of social data | OPTIONAL — for high-volume production studios |

### 3.2 Production (shot-plan → visual → motion)

| # | Node candidate | Maps to traditional | AIGC enabler | Merge / Split / Eliminate |
|---|---|---|---|---|
| 15 ⭐ | **scene-builder (3D previz / feasibility)** | 美术 + 场景搭建 (scene_builder) | Blender + architectural storytelling | KEEP — feasibility check |
| 16 ⭐ | **drawer (still keyframe)** | 摄影 + 灯光 + 美术 (combined) | Diffusion model with reference + LoRA | KEEP — bottleneck node |
| 17 ⭐ | **animator (video gen)** | 摄影机 + 表演 + 剪辑 (combined) | Video diffusion (Runway/Kling/Sora/Veo) | KEEP — bottleneck node |
| 18 🔷 | **prompt-injector (intent → model tokens)** | (none traditional) | Auto-prefix art-bible + character + scene refs | KEEP — load-bearing for consistency |
| 19 🔷 | **camera-preview (low-param verifier)** | 试拍 / dailies | video_preview_fast mode | KEEP — cheap-fail loop |
| 20 🔷 | **performer (acting intent)** | 表演 (斯坦尼) | Emotion intent for character animation | CONDITIONAL — only if live-action/animation; not for 漫剧 |
| 21 🔷 | **production (resource scheduling)** | 制片管理 (057/074) | GPU budget + LoRA reuse + wardrobe-consistency plan | KEEP — AI-specific PROD subset |
| 22 🚫 | *colorist as separate node at this stage* | 调色 (post) | LUT applied at drawer/animator prompt | DEFER color to post — applying mid-gen causes rework |
| 23 🚫 | *asset-reuse as separate node* | Asset management | Part of production node | MERGE into production |
| 24 🔷 | **wardrobe-consistency-verifier** | 服化道连续性 | CLIP-I/DINO-I check per shot | KEEP — AIGC-specific consistency loop |

### 3.3 Post-Production (audio + visual + composite)

| # | Node candidate | Maps to traditional | AIGC enabler | Merge / Split / Eliminate |
|---|---|---|---|---|
| 25 ⭐ | **voicer (TTS)** | 配音 | Multi-provider TTS (MiniMax/ElevenLabs/etc.) | KEEP |
| 26 🔷 | **lip-sync (audio→video alignment)** | (none traditional; re-dub only) | LatentSync; LSE/LSE-C benchmarked | KEEP — AIGC-native node |
| 27 ⭐ | **editor** | 剪辑 (默奇/傅正义) | LLM cut-decision + ffmpeg | KEEP |
| 28 ⭐ | **colorist** | 调色 (076 part 2) | LUT design + Bellantoni color psychology | KEEP |
| 29 ⭐ | **composer (BGM)** | 配乐 | MusicGen / Suno / licensed library | KEEP |
| 30 ⭐ | **foley** | 拟音 (《音效圣经》) | Stable Audio Open; BBC 21-cat taxonomy | KEEP |
| 31 🔷 | **spatial-audio (immersive)** | 空间音频 | Dolby Atmos bed+objects | OPTIONAL — only if target platform is Atmos |
| 32 ⭐ | **mixer** | 混音 | LUFS per-platform + ducking | KEEP — final audio node |
| 33 🔷 | **continuity-auditor (cross-shot)** | 场记 + 连续性 | 4-dim CLIP/DINO verifier | KEEP — runs parallel to mixer |
| 34 🚫 | *separate dialogue-mixer vs music-mixer* | Mix roles | Single mixer node handles both | MERGE into mixer |

### 3.4 Delivery (composite + compliance + distribute)

| # | Node candidate | Maps to traditional | AIGC enabler | Merge / Split / Eliminate |
|---|---|---|---|---|
| 35 ⭐ | **compositor (ffmpeg final)** | 后期合成 | ffmpeg concat + transition | KEEP |
| 36 🔷 | **quality-gate (multi-dim scorer)** | (none; v1 invention) | LLM-judge + objective metrics (LSE, CLIP-I, Pearson) | KEEP — must be quantitative, not vibes |
| 37 ⭐ | **compliance-final (备案 + 标识)** | 合规 (regulatory new) | AI-generated-content labeling automation | KEEP — legal blocker for CN distribution |
| 38 🔷 | **distribution-cut variants** | 平台裁剪 | Per-platform fork: 抖音/快手/小程序剧/B站 | KEEP — multi-platform fork |
| 39 🔷 | **poster + trailer generator** | 海报 + 片花 | Drawer for poster; editor for trailer | KEEP |
| 40 🚫 | *auto-upload as a node* | 分发 | API integration | ANTI-FEATURE — TOS risk, out of scope |
| 41 🚫 | *real-time metrics ingest as a node* | 数据回流 | Platform API | ANTI-FEATURE — out of scope, not creative |

### 3.5 Count check

**41 candidates enumerated across 4 phases** (≥30 quality gate met). Of these:
- ⭐ table-stakes: ~22 (universal must-haves)
- 🔷 differentiators: ~14 (first-principles-derived)
- 🚫 anti-feature: ~5 (eliminate/merge candidates)

---

## 4. Per-Node Declaration Contract — Schema Proposal

User specified: 核心任务 + I/O + AIGC 转化点 + 传统经验锚点. Additional fields proposed below, each with rationale.

```yaml
node_id: <stable_snake_case>            # e.g., screenplay, hook_retention
node_name_cn: <中文名>
node_name_en: <English name>
phase: pre_production | production | post_production | delivery

# === User-specified fields (mandatory) ===
core_task: |
  # 核心任务 — One sentence: what this node single-handedly owns.
  # If two nodes could plausibly own it, the boundary is wrong.
inputs:                                  # I/O contract — input side
  - name: <artifact_name>
    schema_ref: <path or schema_id>
    required: true | false
    from_node: <node_id> | "user" | "external"
outputs:                                 # I/O contract — output side
  - name: <artifact_name>
    schema_ref: <path or schema_id>
    consumed_by: [<node_id>, ...]
aigc_transformation_point: |
  # AIGC 转化点 — Where exactly does AI add value vs the traditional approach?
  # Must answer: what marginal value does AI contribute here?
  # If the answer is "AI just does what a human did faster", this node is suspect.
traditional_experience_anchor: |
  # 传统经验锚点 — Cite specific book/章节/技法 from 102-book corpus or
  # industry practice. Format: 《书名》(Project ID) §章节 → 传统工序.
  # If no anchor exists (e.g., compliance-pre-check), say so explicitly.

# === Proposed additional fields ===
success_criteria:                        # How to know this node succeeded
  - metric: <metric_name>
    target: <value>
    validation: quantitative | qualitative | human_review
    source_ref: <benchmark or rubric>
fail_modes:                              # Known failure patterns
  - mode: <name>
    detection: <signal>
    fallback: <strategy>
fallback_strategy: |                     # What to do if node fails entirely
  # e.g., degrade to placeholder, retry with different model, escalate to human
dependencies:                            # Hard dependencies on other nodes
  requires: [<node_id>, ...]             # Must complete before this node starts
  enhances: [<node_id>, ...]             # Improves quality of those nodes if present
  conflicts: [<node_id>, ...]            # Mutually exclusive or ordering-constrained
complexity_class: trivial | prompt_only | multi_step | loop_with_critic | external_call
iteration_protocol: |                    # For loop_with_critic nodes
  # How many retries, what triggers a retry, what is the exit condition
ai_capability_assumption: |
  # What AI capability does this node assume? Mark stability:
  #   stable_2026 — reliable across providers (e.g., LLM scene-writing)
  #   evolving — capability is real but model-dependent (e.g., long-form video gen)
  #   research_bet — not production-ready (e.g., autonomous theory-critic)
non_ai_alternative: |                    # What if AI is unavailable?
  # Manual fallback or simplified version; reveals whether node is truly necessary
rationale_for_existence: |               # The first-principles justification
  # Why this node and not another arrangement?
  # Must reference user value or AIGC marginal contribution, not historical precedent
provenance:                              # Audit trail
  source_book_refs: [<Project ID>, ...]
  related_skill: <hermes skill name> | none  # Existing 26-expert mapping
  kais_phase_equivalent: <phase id> | none    # Existing 11-phase mapping
```

### 4.1 Field rationale

| Field | Why mandatory | Why not optional |
|---|---|---|
| `core_task` (user-spec) | Without single-sentence ownership, nodes overlap | Defining ownership forces first-principles thinking |
| `inputs` / `outputs` (user-spec) | Without I/O contract, DAG composition fails silently | Pipeline reliability depends on this |
| `aigc_transformation_point` (user-spec) | Without this, node is just "AI does what human did" — anti-feature territory | Forces honest accounting of AI's marginal value |
| `traditional_experience_anchor` (user-spec) | Without anchor, the node floats free of domain knowledge | Ensures RAG corpus integration |
| `success_criteria` (NEW) | Without measurable success, the node cannot be improved iteratively | Per project constraint: "可迭代进步,可独立评估" |
| `fail_modes` (NEW) | AIGC pipelines fail in characteristic ways; documenting prevents silent degradation | Per kais-movie-agent degraded-mode design |
| `fallback_strategy` (NEW) | Required by kais-movie-agent's 降级-first principle | Without fallback, node is brittle |
| `dependencies` (NEW) | Required for DAG ordering | Roadmapper needs this |
| `complexity_class` (NEW) | Different node classes need different phase treatments | Trivial nodes can be batched; loop_with_critic needs own phase |
| `ai_capability_assumption` (NEW) | Some capabilities are research bets; flagging prevents over-engineering | Project risk management |
| `non_ai_alternative` (NEW) | If no fallback, node is essential; if trivial fallback, node is suspect | Anti-feature filter |
| `rationale_for_existence` (NEW) | The Musk first-principles gut-check | Without this, the node set drifts toward imitation-of-traditional |

---

## 5. First-Principles Node-Set Selection Criteria

A node set is "first-principles-derived" (not "imitation-of-traditional") iff it satisfies all 7 criteria. Each is testable.

| # | Criterion | Test | Failure mode |
|---|---|---|---|
| **C1** | **User-value-anchored existence** | Each node's `rationale_for_existence` references *user value or AIGC marginal contribution*, not "this is a traditional film工序". | Imitation pipeline fails C1 — its nodes cite McKee/Field as justification, not user need. |
| **C2** | **AIGC transformation measurability** | Each node's `aigc_transformation_point` names a *measurable* delta (cost reduction, latency reduction, quality lift, capability not previously possible). | Vague transformations ("AI makes it better") fail C2. |
| **C3** | **Compression-justified or expansion-justified** | For each node, explicitly state whether it COMPRESSES traditional multi-stage into one (§2.1) or EXPANDS traditional single-stage into multi (§2.2). If neither, justify why. | Inherited-from-traditional nodes with no transformation fail C3. |
| **C4** | **Independent evaluability** | Each node has at least one `success_criteria` metric that can be computed without subjective judgment (Pearson, LSE, CLIP-I, KL divergence, DTW, etc.). Per project constraint. | "Vibes-only" nodes fail C4. |
| **C5** | **Single ownership (non-overlapping)** | No two nodes own the same `core_task`. If they appear to, the boundary must be intent-vs-execution or definition-vs-verification (decoupling principle from Phase 7 README). | Overlapping nodes (e.g., cinematographer + storyboard_designer both "design shots") must declare boundary or merge. |
| **C6** | **Decoupled I/O contract** | Each node's `inputs` and `outputs` are machine-readable schemas, not free-form text. The DAG can be statically type-checked. | Implicit handoffs ("editor reads director's mind") fail C6. |
| **C7** | **Loop placement explicit** | Every feedback loop is documented (which node feeds back to which, what triggers the loop, what exits it). No implicit loops. | "Editor tells DP to reshoot" as an informal channel fails C7. |

**Quality gate for the node set:** All 7 must hold. A node failing one criterion is not necessarily wrong — it must be either fixed or explicitly justified as exception with documented reason.

---

## 6. Anti-Features Catalog — AIGC Pipeline Design Wrong-Turns

Concrete wrong-turns observed in AIGC pipeline design practice. ≥8 entries per quality gate.

| # | Anti-feature | What goes wrong | Why it's tempting | What to do instead |
|---|---|---|---|---|
| **AF-1** | **Over-decomposition: 100+ micro-nodes** | DAG becomes unmaintainable; latency multiplies; each node adds friction; debugging impossible | ComfyUI/Blender-graph aesthetic; "more nodes = more sophisticated" belief | Apply C1 + C5: each node must own a distinct user-value unit. Aim for 20-30 nodes, not 100. |
| **AF-2** | **AI as drop-in replacement for human role** | Loses AIGC structural advantages; produces "traditional workflow but slower and dumber" | "Screenwriter → AI Screenwriter" feels safe and intuitive | Apply C3: explicitly compress or expand. E.g., AI screenplay + AI script-auditor as decoupled pair (not "AI script-doctor"). |
| **AF-3** | **Missing critic/reviewer in creative loops** | LLM self-grading bias; quality drift undetected; no iteration signal | "Trust the model" assumption; saves a node | Per C4: every creative generation node needs a paired verification node with quantitative metric. |
| **AF-4** | **Conflating "more nodes = more sophisticated"** | Pipeline grows cargo-cult complexity without user value | Engineer aesthetics; "we have 26 skills, must be 30 nodes" | Apply C1 ruthlessly. Each node must earn its place. |
| **AF-5** | **Premature optimization for specific gen models** | Locks pipeline to one provider; becomes obsolete when model updates | "Runway works best with X prompt format" hard-coded | Use provider-agnostic placeholders (see `_shared/RAG-INVOCATION-PATTERN.md`); isolate model-specific knowledge in refs/. |
| **AF-6** | **Redundant gates (multiple quality-bars of the same kind)** | Latency multiplies; gates disagree; user confusion | "More quality checks = safer" intuition | One quality-gate per artifact, with multi-dim scoring inside, not multiple gates in series. |
| **AF-7** | **Treating consistency as an afterthought** | Character/style/wardrobe drift across shots; viewer perceives "wrong"; costly rework | Consistency is implicit in human production; easy to forget | Per §2.2: consistency is a first-class node set (character-bible + LoRA + verifier loop). |
| **AF-8** | **Ignoring audio-video lock until late** | Lip-sync failure becomes visible only at final composite; expensive to fix | Audio and video are generated by different models; easy to silo | Per Phase 7 lip_sync decoupling: voicer + lip_sync + alignment-verifier as explicit node cluster. |
| **AF-9** | **Auto-distribution / auto-upload nodes** | TOS violations; brittle to platform API changes; legal risk | "End-to-end automation" feels like the goal | Distribution node produces artifacts + specs; upload is operator action (out of scope per v1 PROJECT.md). |
| **AF-10** | **Real-time metrics ingest as a creative-loop input** | Latency feedback is wrong timescale for content iteration; introduces noise | "Data-driven creativity" buzzword | Per-作品 metrics inform NEXT project's creative-source node, not current loop. |
| **AF-11** | **Live-action-only nodes in an AI pipeline** | Wastes design surface on irrelevant工序 (location scouting, crew scheduling, permits) | Inheritance from traditional production-management books (057/074) | Per PROD-07 from v1: production node covers only AI-relevant subset. |
| **AF-12** | **Theory-critic as a blocking gate in the linear pipeline** | Kills 短剧 throughput; theory is for serious film, not 短剧 | "All films deserve theoretical rigor" stance | Theory-critic is a consultative vertical (Phase 8 design), invoked on demand, not in linear DAG. |

---

## Feature Dependencies (Node-Candidate DAG)

```
                USER INTENT
                    │
                    ▼
        ┌──────────────────────┐
        │  creative_source     │ ◄──── (daily-scan mode: topic_curatorial)
        │  (story-kernel)      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  style_genome         │ ◄──── theory_critic (consultative, optional)
        │  (5D style vector)    │
        └──────────┬───────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   screenplay  hook_retention  compliance_pre_check
   (剧本)     (商业引擎)       (红线预扫)
        │          │          │
        └──────────┼──────────┘
                   │
                   ▼
            script_auditor ◄── (loops back to screenplay if < threshold)
                   │
                   ▼
        ┌──────────────────────┐
        │  character_designer   │
        │  (CharacterBible 2.0) │
        └──────────┬───────────┘
                   │
                   ▼
            cinematographer
                   │
                   ▼
            storyboard_designer
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   scene_builder performer  production
       │           │       (resource plan)
       └─────┬─────┘
             │
             ▼
         drawer  ◄──── (prompt-injector feeds)
             │
             ▼
         animator ◄──── camera-preview (loops back on fail)
             │
       ┌─────┴─────┐
       ▼           ▼
    voicer      lip_sync ◄── (audio-video alignment)
       │           │
       └─────┬─────┘
             │
             ▼
   ┌─────────────────────────────┐
   │ colorist / editor / composer │
   │   foley / spatial_audio      │ ◄──── continuity_auditor (parallel)
   └──────────┬──────────────────┘
              │
              ▼
           mixer
              │
              ▼
          compositor
              │
              ▼
        quality_gate ◄── (multi-dim scorer; loops back on fail)
              │
              ▼
   ┌──────────────────────────┐
   │ compliance_final          │
   │ distribution_cut_variants │
   │ poster + trailer          │
   └──────────────────────────┘
```

### Dependency notes

- **`screenplay` requires `creative_source` + `style_genome`:** Without story-kernel and style, screenplay writes into a vacuum.
- **`script_auditor` enhances `screenplay`:** Decoupled writer/auditor per Phase 7A-1 (self-grading bias removed).
- **`hook_retention` requires `compliance_pre_check`:** 卡点 placement must satisfy 付费合规 (some 卡点 cannot be paywalls).
- **`character_designer` requires `screenplay`:** Character identity derives from story.
- **`storyboard_designer` requires `cinematographer`:** Cinematographer defines rules; storyboard_designer applies them per Phase 7B-2.
- **`drawer` + `animator` require `character_designer` + `scene_builder`:** Identity contract + scene feasibility.
- **`lip_sync` requires `voicer` + `animator`:** Audio and video must both exist before alignment.
- **`quality_gate` loops back to multiple upstream nodes:** Failure routes depend on which dimension failed (story → screenplay; visual → drawer; audio → mixer).
- **`theory_critic` is consultative:** Not in linear DAG; invoked when pipeline encounters its domain (per Phase 8 design).
- **`compliance_final` is a hard gate:** Cannot bypass for CN distribution.

---

## MVP Node Set Definition (For the Design-Docs Milestone)

The v2.0 PRFP milestone produces DESIGN DOCS ONLY — not implementation. The "MVP" here is the *minimum complete node set that the design docs must cover*.

### Must-document nodes (P1) — table stakes + critical differentiators

- [ ] **creative_source** — DAG root; first-principles test case 1
- [ ] **style_genome** — defines reusable asset
- [ ] **screenplay** — must own 剧本 task
- [ ] **script_auditor** — differentiator (decoupled critic)
- [ ] **character_designer** — identity contract
- [ ] **hook_retention** — first-principles test case 2 (商业引擎)
- [ ] **cinematographer** — shot intent
- [ ] **storyboard_designer** — structured bridge
- [ ] **drawer** — visual bottleneck
- [ ] **animator** — motion bottleneck
- [ ] **prompt_injector** — AIGC-native consistency mechanism
- [ ] **voicer** + **lip_sync** — audio-video lock
- [ ] **editor** + **colorist** + **composer** + **foley** + **mixer** — post cluster
- [ ] **continuity_auditor** — consistency verifier
- [ ] **quality_gate** — quantitative gate
- [ ] **compliance_pre_check** + **compliance_final** — regulatory gates
- [ ] **distribution_cut_variants** + **poster** + **trailer** — delivery

### Should-document nodes (P2) — when present, enrich design

- [ ] **scene_builder** — may be folded into storyboard_designer for AI-only pipelines
- [ ] **performer** — only if animation/live-action; skip for 漫剧
- [ ] **production** — AI-relevant subset (resource plan)
- [ ] **camera_preview** — AIGC-native cheap-fail loop
- [ ] **theory_critic** — consultative vertical

### Defer or eliminate (P3)

- [ ] **topic_curatorial scan** — for high-volume studios; v1 creative_source manual mode is enough
- [ ] **spatial_audio** — only if Atmos target
- [ ] **auto-upload / metrics ingest** — anti-features AF-9, AF-10

---

## Competitor / Reference Approach Analysis

| Approach | How they organize | Our approach |
|---|---|---|
| **ComfyUI node graph** | Visual DAG, dozens of micro-nodes per workflow; user-assembled | We aim for ~25 nodes, not user-assembled; pre-defined for 短剧/微电影 domain |
| **LangGraph plan-and-execute** | Planner agent + executor agents + critic loop | We adopt the pattern at the *pipeline* level, not within each node |
| **Runway/Pika/Sora shot-by-shot** | Per-shot prompt + reference | We adopt this as the production pattern; storyboard_designer emits the shot list |
| **Wan/LTX direct long-form** | One prompt → long video | Research bet; not MVP; flagged in `ai_capability_assumption` |
| **Traditional 102-book workflow** | Pre-prod → prod → post, human roles | Source of `traditional_experience_anchor` per node; not the structural template |
| **kais-movie-agent v1 (11 phases)** | Linear pipeline with review gates | Audit comparison; first-principles derivation should produce something different — the v1 phases are inherited, not derived |
| **Hermes movie-experts v2 (26 skills)** | Collaborative DAG with consultative verticals | Audit comparison; skills are not nodes (skills are capability surfaces; nodes are DAG positions with I/O contracts) |

**Critical distinction for the design docs:** A Hermes *skill* (e.g., `screenplay`) is a capability surface with refs and prompts. A pipeline *node* is a DAG position with an I/O contract. The 26 skills are candidate implementations for nodes — the node set is what gets designed first, the skill-to-node mapping comes after.

---

## Sources

### Project-internal (HIGH confidence)

- **102-book corpus index:** `/data/workspace/hermes-agent/skills/movie-experts/_shared/project-corpus/README.md`
- **26-expert inventory:** `/data/workspace/hermes-agent/skills/movie-experts/README.md`
- **Existing 11-phase pipeline:** `/data/workspace/kais-movie-agent/docs/WORKFLOW.md` + `/data/workspace/kais-movie-agent/docs/ARCHITECTURE_AND_WORKFLOW.md`
- **First-principles test case 1 (creative_source):** `/data/workspace/hermes-agent/skills/movie-experts/creative_source/SKILL.md`
- **First-principles test case 2 (hook_retention):** `/data/workspace/hermes-agent/skills/movie-experts/hook_retention/SKILL.md`
- **Theory-critic vertical:** `/data/workspace/hermes-agent/skills/movie-experts/theory_critic/SKILL.md`
- **Project context v2.0 PRFP:** `/data/workspace/hermes-agent/.planning/PROJECT.md` (Current Milestone section)
- **v1 FEATURES.md (audit carryover):** `/data/workspace/hermes-agent/.planning/research/FEATURES.md`

### External (MEDIUM confidence — general ecosystem awareness)

- [LangGraph: Agent Orchestration Framework for Reliable AI Agents](https://www.langchain.com/langgraph) — graph-based agent orchestration
- [ComfyUI Video Generation Pipeline: Features, Models & Optimization](https://comfyui.org/en/video-generation-pipeline-features-models-optimization) — multi-functional video gen workflow
- [How to Build, Run, and Scale High-Quality Creator Workflows in ComfyUI (NVIDIA)](https://developer.nvidia.com/blog/how-to-build-run-and-scale-high-quality-creator-workflows-in-comfyui/) — production-ready ComfyUI patterns
- [ComfyUI-R1: Exploring Reasoning Models for Workflow Generation](https://arxiv.org/html/2506.09790v1) — automated workflow composition via reasoning
- [Shot-by-Shot Timeline for AI Filmmaking (r/comfyui)](https://www.reddit.com/r/comfyui/comments/1u30hf0/im_building_a_shotbyshot_timeline_for_ai/) — practitioner building exactly the shot-by-shot pattern we describe

### Confidence assessment

| Area | Confidence | Why |
|------|------------|-----|
| Traditional workflow stages (from corpus) | HIGH | Cited directly from 102-book index |
| Node candidate enumeration | MEDIUM-HIGH | Synthesized from corpus + existing 26-expert + 11-phase + AIGC ecosystem knowledge |
| AIGC-native compression/expansion patterns | MEDIUM | Drawn from industry practice; not project-benchmarked |
| First-principles selection criteria (C1-C7) | MEDIUM | Derived from project constraints + Musk-style reduction; not externally validated |
| Anti-features catalog | HIGH | Each grounded in observed AIGC practice; specific examples given |
| Per-node declaration schema | MEDIUM | Proposal; needs roadmapper + executor validation before adoption |

### Gaps to address in later phases

- **Node-count target validation:** Is ~25 the right count, or should it be 15 / 35? Phase-specific research needed.
- **AIGC transformation measurability (C2):** Specific metrics per node need definition during node-design phases.
- **AI capability stability (2026 snapshot):** Which `ai_capability_assumption` entries are `stable_2026` vs `evolving` vs `research_bet`? Needs current model survey.
- **Theory-critic integration point:** Confirmed consultative (per Phase 8), but the trigger condition for invocation needs design.
- **Loop exit conditions:** Every `loop_with_critic` node needs explicit max-iterations + exit signal; defer to per-node design phase.

---
*Feature research for: v2.0 PRFP pipeline node-set design (AIGC-native 短剧 / 微电影 production).*
*Researched: 2026-06-16.*
