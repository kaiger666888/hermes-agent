---
name: prompt_injector
description: "Prompt Injector Expert: AI-native node translating upstream human intent (visual_intent + style_genome + character_assets) into model-ready prompts (model_prompts + consistency_context) with cross-call consistency context management. No traditional counterpart — prompt engineering IS the discipline."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, prompt-engineering, cross-call-consistency, model-prompts, ai-native, intent-translation, token-budget, few-shot, chain-of-thought, ip-adapter, lora-reference, identity-preservation, template-engineering, consistency-context]
    related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]
    expert_id: prompt_injector
    metrics: [cross_call_consistency, prompt_token_efficiency]
---

# Prompt Injector Expert (提示注入)

AI-native prompt engineering + cross-call consistency context specialist for AI 短剧 / 微电影 production. **No traditional counterpart exists** — this expert is an AI-native invention per the v2.0 PRFP derivation (Phase 7 §4.7 D3.5 + D2.4). Its role is not to "translate" intent into a different medium, but to *operate* the discipline that only exists because of generative models: assembling model-ready prompts + managing cross-call consistency context.

**I/O contract (canonical, per `02-NODE-SPECS.md §2.7` + `nodes.yaml` lines 448-523):**

- **Inputs (all required):**
  - `visual_intent` ← `cinematographer` (shot scale + composition + axis + camera move intent)
  - `style_genome_5d` ← `style_genome` (5-dimensional style vector: genre / mood / aesthetic / pace / color)
  - `character_assets` ← `character_designer` (character LoRA refs / IP-Adapter embeddings / InstantID face locks)

- **Outputs (all required):**
  - `model_prompts` → `visual_executor` (token-budgeted, model-ready prompts per shot/scene)
  - `consistency_context` → `visual_executor` (cross-call carry-context that preserves identity/style/composition across multiple gen-model invocations)

**Success criteria (canonical, hard constraints):**

- `cross_call_consistency ≥ 0.85` — measured by downstream visual outputs' style/identity consistency across calls
- `prompt_token_efficiency ≤ 4000 tokens per call` — hard ceiling; measured as token count vs the 4000-token ceiling

**Fail modes + fallback:** `consistency_drift` (carry context lost across calls → fallback: explicit carry + repeat key constraints); `prompt_overload` (token budget exceeded → fallback: split prompt into structured sections + use system prompt for stable constraints).

**Budget:** ¥50/episode (compute) · 30s latency · `stable_2026` maturity · O(1) complexity class.

**Model horizon:** `stable_2026` — prompt engineering is stable; cross-call context management is evolving.

> **AI-native identity.** Unlike 13 of the 14 v1 experts (which had traditional cinematography / editing / sound anchors), `prompt_injector` has no human-craft predecessor. It exists because generative models require a discipline that didn't exist in traditional filmmaking. Per `skills-mapping.yaml:99-103`, mapping_type = `new_ai_native`. No `metadata.hermes.aliases` (NEW expert, no v1 predecessor per FOUND-08 inapplicability). No redirect stub (no predecessor directory).

## When to use this skill

The user needs one of:

- **Intent-to-prompt translation** — upstream visual_intent + style_genome + character_assets must be assembled into a token-budgeted, model-ready prompt before visual_executor can be invoked
- **Cross-call consistency context construction** — a multi-shot sequence requires identity/style/composition preservation across multiple gen-model calls (the `consistency_context.json` artifact)
- **Token budget planning** — a complex visual scene is at risk of `prompt_overload` (token count > 4000/call ceiling) and needs structured-section decomposition
- **Model-specific template instantiation** — the prompt must be concretized against a 2026 model grammar (FLUX 2 / Veo / Kling per the model-specific-prompt-templates ref; literal model names live in refs only — SKILL.md body uses `<image_primary>` / `<video_primary>` placeholders)

## Role & Philosophy

- **Prompt engineering IS the discipline, not a translation layer.** This expert does not "translate" intent into a different language — it operates the engineering discipline of structuring prompts for stable, consistent, token-efficient generation. Treating it as a passive translator under-invests in the one craft skill that AI-native production uniquely requires.
- **Cross-call consistency context is first-class output, not a side effect.** The `consistency_context.json` artifact is a peer of `model_prompts.json` — both are required outputs per nodes.yaml. Losing consistency context between calls is a `consistency_drift` fail mode; treating it as implicit state is the root cause of most cross-shot character drift.
- **Token budget is a hard ceiling (≤ 4000/call), not a soft guideline.** Exceeding it triggers the `prompt_overload` fail mode → structured-section split + system-prompt-for-stable-constraints fallback. The ceiling exists because gen-model attention degrades with prompt length; 4000 tokens is the empirically validated stability threshold for `stable_2026` model horizons.
- **Provider-agnostic — no model names in SKILL.md body.** Use `<image_primary>` / `<video_primary>` placeholder convention (matches `visual_executor` pattern). Literal model names appear ONLY in the dated examples within `references/model-specific-prompt-templates.md`, each carrying a `verified_date:` stamp. Hard-coding model names as identifiers in the SKILL.md body would lock the expert to a 2026-Q2 model catalog and break at the next model swap.
- **AI-native means no traditional cinematography / editing precedent.** This expert is not constrained by Murch / Field / 180°-axis rules or any human-craft heritage. Its constraints come from the gen-model's prompt grammar + token-attention physics + cross-call consistency literature, not from film-school textbooks.

## Core Capabilities

- **Intent decomposition** — break a complex `visual_intent` into atomic prompt units (identity / composition / motion / lighting / mood), each addressable as an independent prompt section
- **Style genome vector injection** — embed `style_genome_5d` (genre / mood / aesthetic / pace / color) into the prompt's stable-constraints section so every call in a sequence carries the same style fingerprint
- **Character asset reference compilation** — assemble per-character LoRA refs / IP-Adapter embeddings / InstantID face locks into the prompt's identity section, with per-shot weight tuning
- **Cross-call consistency context assembly** — build the `consistency_context.json` artifact that carries identity / style / composition references across multiple gen-model calls, including the repeat-key-constraints list (the fallback for `consistency_drift`)
- **Prompt token budget management** — keep each call under the 4000-token ceiling via split-by-concern chunking + system-prompt-for-stable-constraints + redundancy elimination
- **Model-specific template instantiation** — concretize the abstract prompt against a 2026 model grammar (FLUX 2 / Veo / Kling) using the template library in `references/model-specific-prompt-templates.md`

## I/O Contract

> **Canonical source:** `02-NODE-SPECS.md §2.7` + `nodes.yaml` lines 448-523. This section quotes the canonical spec verbatim where possible.

| Direction | Artifact | Type | Source / Consumer | Required |
|-----------|----------|------|-------------------|----------|
| **Input** | `visual_intent` | structured JSON | from `cinematographer` (shot scale + composition + axis + camera move intent) | YES |
| **Input** | `style_genome_5d` | structured vector | from `style_genome` (5-dim: genre / mood / aesthetic / pace / color) | YES |
| **Input** | `character_assets` | structured set | from `character_designer` (per-character LoRA / IP-Adapter / InstantID refs) | YES |
| **Output** | `model_prompts` | structured set | to `visual_executor` (token-budgeted, model-ready per-shot prompts) | YES |
| **Output** | `consistency_context` | structured context | to `visual_executor` (cross-call carry: identity / style / composition) | YES |

**Success criteria (hard constraints):**

| Metric | Threshold | Measurement |
|--------|-----------|-------------|
| `cross_call_consistency` | `≥ 0.85` | downstream visual outputs' style / identity consistency across calls |
| `prompt_token_efficiency` | `≤ 4000 tokens per call` | token count vs the defined ceiling |

**Budget:** ¥50/episode (compute) · 30s latency · `stable_2026` maturity · O(1) complexity class.

**Dependencies (from `nodes.yaml`):**

- **Hard deps (data-flow predecessors):** `cinematographer`, `style_genome`, `character_designer` — these three produce the artifacts that prompt_injector consumes. They are NOT in `related_skills` because `related_skills` is the collaboration-graph peer set (bidirectional edges for skill recommendation + DAG traversal), while `hard deps` is the data-flow predecessor set. Both coexist; the data-flow deps appear in this I/O Contract section, the collaboration peers appear in the `## Collaboration` section.
- **Soft deps:** none.

> **`related_skills` vs `hard deps` distinction (per threat T-16-06):** `related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]` is the bidirectional peer set for DAG traversal. `nodes.yaml` `hard deps: [cinematographer, style_genome, character_designer]` is the data-flow predecessor set. The two overlap on `cinematographer` but diverge on the others — `creative_source` produces story_kernel (consumed upstream by screenplay, not directly by prompt_injector); `style_genome` and `character_designer` are upstream data sources but are not declared as collaboration-graph peers (their edges are reflected in body prose, not in related_skills). `visual_executor` and `audio_pipeline` are downstream consumers — they appear in related_skills (collaboration-graph) but not in hard deps (which is predecessors-only).

## Output Format

The expert emits two JSON artifacts per scene/shot:

### `model_prompts.json`

```json
{
  "type": "ModelPrompts",
  "version": "1.0.0",
  "scene_ref": "scene_03",
  "shot_ref": "shot_03_02",
  "model_target": "<image_primary>",
  "system_prompt": {
    "stable_constraints": [
      "genre: neo-noir thriller",
      "mood: oppressive heat, moral corrosion",
      "color: desaturated teal + amber practicals",
      "identity.char_wuji: LoRA 0.78, IP-Adapter 0.55, InstantID 0.60"
    ],
    "token_count": 412
  },
  "user_prompt": {
    "sections": [
      {"concern": "identity", "text": "char_wuji, male, 30s, gaunt cheekbones, rain-soaked coat...", "token_count": 89},
      {"concern": "composition", "text": "medium close-up, eye-line left-of-frame, shallow DoF...", "token_count": 64},
      {"concern": "motion", "text": "static held beat, micro-tremor in jaw...", "token_count": 38},
      {"concern": "lighting", "text": "key: amber sodium-vapor practical from frame-left...", "token_count": 52},
      {"concern": "mood", "text": "oppressive humidity, moral rot barely concealed...", "token_count": 41}
    ],
    "total_token_count": 284
  },
  "total_token_count": 696,
  "ceiling": 4000,
  "ceiling_compliance": "PASS",
  "negative_prompt": "cartoon, anime, oversaturated, HDR, plastic skin",
  "verified_date": "2026-06-17"
}
```

### `consistency_context.json`

```json
{
  "type": "ConsistencyContext",
  "version": "1.0.0",
  "scene_ref": "scene_03",
  "shot_sequence": ["shot_03_01", "shot_03_02", "shot_03_03"],
  "carry_blocks": [
    {
      "block": "identity",
      "scope": "per-character",
      "content": {"char_wuji": {"lora_ref": "wuji_v3.safetensors", "ip_adapter_ref": "wuji_embed_v2.pt", "instantid_ref": "wuji_face_v1.pt", "weight_tuning": {"lora": 0.78, "ip_adapter": 0.55, "instantid": 0.60}}}
    },
    {
      "block": "style",
      "scope": "scene-wide",
      "content": {"genome_5d": {"genre": "neo-noir", "mood": "oppressive", "aesthetic": "grain-35mm", "pace": "slow-burn", "color": "teal-amber"}}
    },
    {
      "block": "composition",
      "scope": "shot-pair",
      "content": {"axis_lock": "180° axis on char_wuji eye-line", "screen_direction": "left-of-frame"}
    }
  ],
  "repeat_key_constraints": [
    "char_wuji rain-soaked coat + gaunt cheekbones + amber key light",
    "180° axis: eye-line left-of-frame, never cross"
  ],
  "drift_watch": {
    "identity_cosine_sim_floor": 0.85,
    "style_consistency_floor": 0.85,
    "trigger_on_breach": "consistency_drift"
  },
  "verified_date": "2026-06-17"
}
```

## Key Parameters

### Prompt Structure

- **few-shot template selection** — choose 0-shot / 1-shot / 3-shot / 5-shot based on visual_intent complexity (0-shot for atomic single-concern shots; 5-shot for multi-character compositions requiring reference frames). See `references/prompt-engineering-patterns.md` §Few-Shot Template Structures.
- **chain-of-thought (CoT) chain depth** — for visual reasoning chains (e.g., "describe character → describe lighting → describe composition → compose final prompt"), CoT depth 2-4 is empirically stable for `stable_2026` models. CoT depth > 5 risks prompt_overload. See `references/prompt-engineering-patterns.md` §Chain-of-Thought Decomposition.
- **decomposition granularity** — split visual_intent by concern (identity / composition / motion / lighting / mood) into atomic prompt units. Granularity too fine → too many sections, hard to maintain consistency; granularity too coarse → single section over-stuffed, prompt_overload risk. Empirically: 4-6 sections per prompt is stable.
- **negative-prompt patterns** — always include a negative prompt (cartoon / anime / oversaturated / HDR / plastic skin) per `references/prompt-engineering-patterns.md` §Negative-Prompt Patterns.

### Cross-Call Consistency

- **consistency_context carry strategy** — `consistency_context.json` is the canonical carry artifact. Every gen-model call in a shot sequence receives the same `consistency_context` (or a sub-slice scoped to the shot-pair). Carrying by reference (filename) is preferred over carrying by value (inline) to stay under token ceiling.
- **identity reference selection** — per `references/cross-call-consistency.md` §Identity Reference Selection: prefer LoRA (stable, file-based, weight-tunable) for main characters; IP-Adapter for variable wardrobe / lighting; InstantID for face identity lock in close-ups. Multi-method stacking (LoRA + IP-Adapter + InstantID) is encouraged with total stack strength 1.0-2.0.
- **repeat-key-constraints list** — the fallback mechanism for `consistency_drift`. Each `consistency_context.json` carries a `repeat_key_constraints` array (2-4 entries) that must be repeated verbatim in every call's system prompt. Per fail-mode fallback: "consistency context 显式 carry across calls + repeat key constraints".

### Token Budget

- **≤ 4000 tokens per call — hard ceiling.** Exceeding it triggers `prompt_overload` fail mode → fallback: split prompt into structured sections + use system prompt for stable constraints.
- **system-prompt-for-stable-constraints strategy** — identity / style / composition constraints that don't change across calls belong in the system prompt (cached, doesn't count against per-call variance budget). Per-call variance (motion / lighting / mood deltas) belongs in the user prompt. See `references/token-budget-management.md` §Hierarchical Prompt Structures.
- **chunking thresholds** — single-section size > 200 tokens is a chunking candidate. Split by concern; never split a concern across two sections (breaks semantic coherence).
- **redundancy elimination** — don't repeat identity in every call's user prompt; carry it via `consistency_context` + system prompt. Per `references/token-budget-management.md` §Redundancy Elimination.

### Model-Specific Templates

> **CRITICAL:** SKILL.md body uses `<image_primary>` / `<video_primary>` placeholders. Literal model names (FLUX 2 / Veo / Kling) appear ONLY in `references/model-specific-prompt-templates.md` with `verified_date:` stamps per threat T-16-03.

- **`<image_primary>` template pattern** — structured-tags + natural-language blend (per `references/model-specific-prompt-templates.md` §`<image_primary>` Prompt Grammar). E.g., `[character: X] [composition: Y] [lighting: Z] + natural-language mood sentence`.
- **`<video_primary>` template pattern** — cinematographic descriptor prefixes (per `references/model-specific-prompt-templates.md` §`<video_primary>` Prompt Grammar). E.g., `Camera: dolly-in, slow. Subject: char_wuji, trembling. Mood: oppressive heat.`
- **cross-provider abstraction** — the abstract prompt structure (identity / composition / motion / lighting / mood sections) is provider-agnostic; the model-specific template instantiation is a thin adapter that maps abstract sections → model grammar. Swapping `<image_primary>` from one model to another should require only a template-adapter change, not a prompt rewrite. See `references/model-specific-prompt-templates.md` §Cross-Provider Abstraction Patterns.

## Fail Modes + Fallback

> **Canonical source:** `nodes.yaml` lines 489-500.

| Fail Mode | Trigger | Impact | Fallback Strategy |
|-----------|---------|--------|-------------------|
| `consistency_drift` | consistency context lost across multiple calls | `visual_executor` output drifts (character identity / style / composition breaks across shots) | **Carry context explicitly across calls + repeat key constraints** — `consistency_context.json` is mandatory carry; `repeat_key_constraints` array is repeated verbatim in every call's system prompt |
| `prompt_overload` | prompt token count > 4000 ceiling; model attention disperses | Critical constraints ignored by the model (identity / composition / lighting details dropped) | **Split prompt into structured sections + use system prompt for stable constraints** — identity / style / composition move to system prompt; user prompt keeps only per-call variance (motion / lighting deltas) |

## References

本专家所有 prompt engineering patterns + cross-call consistency literature + token budget strategies + model-specific templates 由下列 4 个 refs 独占定义:

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/prompt-engineering-patterns.md`](./references/prompt-engineering-patterns.md) | 设计 prompt 结构 / few-shot template / CoT chain / decomposition / negative prompt 前 | Few-shot template structures (0/1/3/5-shot) + chain-of-thought decomposition patterns + structured prompt anatomy (system/context/user segments) + task decomposition patterns + negative-prompt patterns |
| [`references/cross-call-consistency.md`](./references/cross-call-consistency.md) | 设计 cross-call consistency context / 选择 identity reference method / 验证 cross-call 一致性 前 | LoRA adapter references (character identity preservation) + IP-Adapter (image prompt conditioning) + InstantID (zero-shot identity) + identity-preserving prompting (seed locking + reference embedding + multi-shot consistency context) — ties to `cross_call_consistency ≥ 0.85` criterion |
| [`references/token-budget-management.md`](./references/token-budget-management.md) | 设计 token budget / 处理 prompt_overload / chunking strategy 前 | Prompt chunking (split-by-concern: identity / composition / motion / lighting) + hierarchical prompt structures (system-prompt for stable + user-prompt for variance) + context window management + token counting per provider + redundancy elimination |
| [`references/model-specific-prompt-templates.md`](./references/model-specific-prompt-templates.md) | 实例化 abstract prompt 到具体 model grammar / 替换 `<image_primary>` 或 `<video_primary>` 前 | FLUX 2 prompt grammar (structured tags + natural language) + Veo prompt grammar (cinematographic descriptor prefixes) + Kling prompt grammar (Chinese-friendly natural language) + cross-provider abstraction patterns |

## Knowledge Retrieval

在生成任何 model_prompts / consistency_context / token budget plan / model-specific template 输出前,按以下顺序检索上下文(4 个检索主题):

- **Few-shot / CoT / decomposition / negative-prompt patterns** —— 详见 [`references/prompt-engineering-patterns.md`](./references/prompt-engineering-patterns.md)
- **LoRA / IP-Adapter / InstantID identity preservation + cross-call consistency** —— 详见 [`references/cross-call-consistency.md`](./references/cross-call-consistency.md)
- **Token chunking + hierarchical prompts + redundancy elimination (≤ 4000/call)** —— 详见 [`references/token-budget-management.md`](./references/token-budget-management.md)
- **FLUX 2 / Veo / Kling template instantiation + cross-provider abstraction** —— 详见 [`references/model-specific-prompt-templates.md`](./references/model-specific-prompt-templates.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:prompt_injector,domain:prompt-engineering-patterns"
tags="expert:prompt_injector,domain:cross-call-consistency"
tags="expert:prompt_injector,domain:token-budget-management"
tags="expert:prompt_injector,domain:model-specific-prompt-templates"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Collaboration

> **Collaboration graph.** `related_skills` is the bidirectional peer set for DAG traversal: `[creative_source, cinematographer, visual_executor, audio_pipeline]`. The data-flow hard-dep predecessors from `nodes.yaml` (`cinematographer`, `style_genome`, `character_designer`) are listed below as inbound edges but are NOT all in `related_skills` — the distinction is documented in the `## I/O Contract` section above.

### Inbound (data-flow predecessors + collaboration peers)

- **<- [`cinematographer`](../cinematographer/SKILL.md)**: `visual_intent` (shot scale + composition + axis + camera move intent) — hard dependency per `nodes.yaml`
- **<- `style_genome`**: `style_genome_5d` (5-dim vector: genre / mood / aesthetic / pace / color) — hard dependency per `nodes.yaml`
- **<- `character_designer`**: `character_assets` (per-character LoRA / IP-Adapter / InstantID refs) — hard dependency per `nodes.yaml`
- **<- [`creative_source`](../creative_source/SKILL.md)**: story_kernel (indirect — grounds the intent chain at the DAG root; creative_source produces the narrative seed that flows through screenplay → cinematographer → prompt_injector)

### Outbound (downstream consumers + collaboration peers)

- **-> [`visual_executor`](../visual_executor/SKILL.md)**: `model_prompts` + `consistency_context` — primary consumer per `nodes.yaml` io_contract
- **-> [`audio_pipeline`](../audio_pipeline/SKILL.md)**: prompt assembly support for audio generation prompts (TTS voice-character prompts, music mood prompts) — secondary consumer; audio_pipeline may invoke prompt_injector to assemble audio-side prompts under the same consistency_context

## Changelog

- **2026-06-17** — Created `prompt_injector` expert (v1.0.0) per Phase 16 NEW-01. AI-native node (no v1 predecessor); `mapping_type: new_ai_native` per `skills-mapping.yaml:99-103`. Node spec source: `02-NODE-SPECS.md §2.7` + `nodes.yaml` lines 448-523. **No aliases** (NEW expert — FOUND-08 alias requirement does not apply). **No redirect stub** (no predecessor directory). **Refs:** 4 ref files (prompt-engineering-patterns + cross-call-consistency + token-budget-management + model-specific-prompt-templates) + LICENSE.md. **GAP-REPORT:** placeholder per CONTEXT.md D-04 (new expert — no v1 baseline to gap-analyze). **Frontmatter constraints satisfied:** `related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]` exactly (ROADMAP §16 criterion #3); `metrics: [cross_call_consistency, prompt_token_efficiency]` exactly (ROADMAP §16 criterion #4); no `aliases` field; no `sub_steps` field (single-node expert).
- **2026-06-19** — Phase 23 v5.0 patch: appended `## V8.6 Pipeline Sync (Phase 23 v5.0)` section documenting kais-movie-agent V8.4 NEW role (Step 7 pre-node) + V8.6 atomic Step 7 merge with visual_executor/style_genome/colorist. No frontmatter changes (FOUND-08 preserved).

## V8.6 Pipeline Sync (Phase 23 v5.0)

> 来源:kais-movie-agent V8.4 SKILL.md §"V8.4 更新" §2 + V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查"。dreamina CLI 适配基线见 [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md)。

### V8.6 Step Position

prompt_injector 在 V8.6 管线中位于 **Step 7 pre-node**(原 V8.4 §2 引入的新节点):

| V8.6 Step | 角色 | 共同调用专家(atomic op) |
|-----------|------|----------------------|
| **Step 7** 视觉种子+风格化 | **pre-node**(在 visual_executor 调用 dreamina CLI 之前) | visual_executor + style_genome + colorist |

**Step 7 atomic operation 流程:**
1. style_genome 输出 5D 风格向量 + style_blend 协议
2. cinematographer 输出 visual_intent(shot scale + composition + axis + camera move)
3. character_designer 输出 character_assets(L1 身份锚点 + L2 造型卡片 + LoRA / IP-Adapter refs)
4. **prompt_injector**(本专家)将上述 3 路输入翻译为 dreamina-compatible `model_prompts` + `consistency_context`
5. visual_executor 接收 `model_prompts`,调用 `dreamina text2image` / `image2image` 生成视觉种子

### V8.4 NEW Role(历史背景)

prompt_injector 是 kais-movie-agent V8.4 §2 引入的 **NEW 节点** —— V8.4 之前,visual_intent + style_genome + character_assets 直接堆叠到 visual_executor 的 prompt 中,导致 token 浪费 + cross-call 漂移。V8.4 引入 prompt_injector 作为**翻译层**,将多源异构 intent 压缩为 model-ready prompts。

**与 hermes-agent v3.0 Phase 16 的关系:** hermes-agent 在 Phase 16 创建了 prompt_injector expert_id(per skills-mapping.yaml `mapping_type: new_ai_native`),V8.4 是消费者侧(kais-movie-agent)确认并采用此 expert。

### dreamina CLI 适配要点

prompt_injector 输出的 `model_prompts` 必须是 dreamina CLI 兼容格式:

- **零面部描述** —— 面部特征由 L1 参考图传递,prompt 只写动作/场景/镜头(per `_shared/dreamina-cli-baseline.md` §"核心原则")
- **`@Image N` 绑定语法** —— 多模态视频生成时,prompt 中用 `@Image1 provides identity...` 显式绑定 L1 参考图
- **`@Audio N` 绑定语法** —— multimodal2video 音频绑定时使用(详见 audio_pipeline SKILL.md Phase 25 patch)
- **中文/英文双语 prompt** —— dreamina CLI 对双语 prompt 兼容,但关键身份/动作描述建议英文(参考图识别更稳定)
- **token budget** —— 单 prompt ≤ 500 tokens(dreamina CLI 最佳实践);超长 prompt 拆分为多次调用

### Cross-References

- [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md) — dreamina CLI prompt 格式约定(Phase 22 v5.0)
- [`visual_executor/SKILL.md §V8.6 Pipeline Sync`](../visual_executor/SKILL.md) — Step 7 downstream consumer
- [`style_genome/SKILL.md §V8.6 Pipeline Sync`](../style_genome/SKILL.md) — Step 2.5/5/7 上游 5D 向量
- [`cinematographer/SKILL.md §V8.6 Pipeline Sync`](../cinematographer/SKILL.md) — Step 5/6/8 上游 visual_intent
- [`character_designer/SKILL.md §V8.6 Pipeline Sync`](../character_designer/SKILL.md) — Step 4 上游 character_assets
- [`colorist/SKILL.md §V8.6 Pipeline Sync`](../colorist/SKILL.md) — Step 7 协同(color_intent 注入 model_prompts)
