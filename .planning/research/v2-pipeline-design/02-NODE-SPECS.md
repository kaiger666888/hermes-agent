# 02 — Node Specs: kais-movie-agent v2.0 Pipeline Per-Node Detail

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 8 of v2.0 PRFP · **Source:** rendered from `nodes.yaml` (canonical)
> **Stability:** evolving (per Phase 7 §1.7 — per-node specs are evolving)
> **Regeneration:** This Markdown is regenerable from `nodes.yaml` via lint script (Phase 12 GOV-02)

---

## §2.0 — 阅读指南

本文档从 `nodes.yaml` 渲染,提供 per-node 人类可读规格。每节点有 3 行 audit header:
- 🅰 **First principles** — Phase 7 derivation reference
- 📚 **Traditional anchor** — 传统工序对照
- ⚡ **AIGC transformation** — 转化类型

**Capability-spec 层(canonical,§2.1-§2.16)** vs **instantiation 层(dated annex,§2.17)** 视觉上明确分离。**模型名只在 §2.17 出现**,canonical spec 完全 model-agnostic。

---

## §2.1 — Node: `creative_source` (创意源)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.1` (D1.1+D1.2+D1.3+D1.5+D4.1)
> 📚 **Traditional anchor:** 传统编剧 personal-experience mining + 故事 kernel 设计
> ⚡ **AIGC transformation:** ai_bounded — AI 协助但不能替代人类 lived experience

**Layer:** 0 (Root) · **Role:** root · **v1 expert_id:** preserved
**C1-C7 verdict:** PASS (per `01-NODE-DAG.md §1.2`)

**Core task:** 从 6 个社会阶层的生活经验挖故事 kernel,产出整合元意图(logline + 主角欲望 + 中央冲突 + 转折点 + 解决立场 + 风格基因)

**I/O contract:**
- Inputs: `creator_anecdote` (text, external), `lived_experience_seed` (text, external)
- Outputs: `story_kernel` (structured_json, consumed by style_genome + screenplay + character_designer)

**Success criteria:** kernel_novelty_score ≥ 0.7 (trope-catalog embedding);creator_acceptance pass/fail

**Fail modes:** cliche_default / lived_experience_thin
**Fallback:** anti-trope prompt + structured-interview for specificity

**Dependencies:** none · **Complexity:** O(1)
**AI capability:** creative expansion stable_2026;novel creativity evolving
**Non-AI alt:** 纯人类编剧 — 10x 时间成本
**Rationale:** per §3.1 D1.1+D1.2+D1.3+D1.5 + §3.4 D4.1

**Budget:** ¥150/episode (human_time) · 600s latency (critical) · model_horizon: stable_2026

**Critic pairing:** N/A (root; downstream has critics)

---

## §2.2 — Node: `style_genome` (风格基因组)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.2` (D2.3+D2.4)
> 📚 **Traditional anchor:** 传统 art direction + production design
> ⚡ **AIGC transformation:** augmentation

**Layer:** 1 · **Role:** intent_parallel · **v1 expert_id:** preserved

**Core task:** 提取 + 编码 + 复用 5D style genome(色调 + 构图 + 节奏 + 材质 + 情感基调)作为下游 invariant 输入

**I/O:** in: story_kernel;out: style_genome_5d (consumed by 6 downstream nodes)

**Success criteria:** aesthetic_alignment ≥ 0.7;cross_node_consistency ≥ 0.85
**Fail modes:** genre_conflation / over_abstraction · **Fallback:** form_context 分桶 + reference images

**Rationale:** per §3.2 D2.3+D2.4 — coherence 主导 + invariant ownership

**Budget:** ¥300/episode (human_time) · 120s · stable_2026

---

## §2.3 — Node: `screenplay` (剧本)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.3` (D1.3+D2.1)
> 📚 **Traditional anchor:** 传统编剧 + Field 三幕 + McKee 转折点 (validated-invariant)
> ⚡ **AIGC transformation:** full_generation

**Layer:** 1 · **Role:** intent_parallel · **v1 expert_id:** preserved

**Core task:** 把元意图展开为可执行叙事结构(scene list + dialogue + form 适配)

**I/O:** in: story_kernel, form_context;out: screenplay_full (consumed by cinematographer + hook_retention + script_auditor)

**Success criteria:** script_auditor_score ≥ 0.75;three_act_compliance 100%
**Fail modes:** plot_hole / dialogue_flat / mid_act_2_sag
**Fallback:** loop with script_auditor (max 3) / subtext rewrite / midpoint reversal

**Rationale:** per §3.1 D1.3 + §3.2 D2.1 — 元意图展开层 + story owner

**Budget:** ¥400/episode (compute) · 300s · evolving

**Critic pairing:** script_auditor (loop_with_critic edge)

---

## §2.4 — Node: `script_auditor` (剧本审计)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.4` (D2.5+D3.1(c))
> 📚 **Traditional anchor:** 传统 script doctor + notes session;AIGC quantitative + decoupled
> ⚡ **AIGC transformation:** verification

**Layer:** 1 · **Role:** critic_paired · **v1 expert_id:** preserved

**Core task:** 5-dim quantitative audit,decide accept/regenerate/escalate

**I/O:** in: screenplay_full;out: audit_score_5dim + verdict

**Success criteria:** pearson_with_human ≥ 0.65;audit_completeness 100%
**Fail modes:** rubric_bias / false_positive · **Fallback:** explicit rubric + human override

**Rationale:** per §3.2 D2.5 + §3.3 D3.1(c)

**Budget:** ¥100/episode (compute) · 60s · stable_2026

---

## §2.5 — Node: `character_designer` (角色设计)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.6` (D2.4)
> 📚 **Traditional anchor:** 传统角色设计 + casting;AIGC 增加 voice profile + behavioral tics
> ⚡ **AIGC transformation:** full_generation

**Layer:** 1 · **Role:** intent_parallel · **v1 expert_id:** preserved

**Core task:** 定义 + 维护角色 identity asset(face, body, wardrobe, voice, tics)

**I/O:** in: story_kernel;out: character_assets (consumed by cinematographer + prompt_injector + visual_executor + continuity_auditor)

**Success criteria:** identity_match ≥ 0.85;voice_consistency ≥ 0.9
**Fail modes:** identity_drift / voice_profile_mismatch · **Fallback:** loop + tighten ControlNet / explicit prosody

**Rationale:** per §3.2 D2.4 — 身份一致性 invariant

**Budget:** ¥300/episode (compute) · 180s · evolving

**Cross-cutting invariant owner:** character identity (5 consumer nodes)

---

## §2.6 — Node: `cinematographer` (摄影指导)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.5` (D2.1+D2.2+D3.4)
> 📚 **Traditional anchor:** 传统摄影指导角色直接适用;AIGC 增加 composition_lock 显式化
> ⚡ **AIGC transformation:** augmentation

**Layer:** 2 · **Role:** visual_intent · **v1 expert_id:** preserved

**Core task:** 把 intent 翻译为视觉 intent(镜头列表 + 灯光 + 构图 + composition_lock)

**I/O:** in: screenplay + style_genome + character_assets;out: visual_intent (consumed by prompt_injector)

**Success criteria:** composition_lock_adherence ≥ 0.85;axis_compliance 100%
**Fail modes:** composition_under_specified / axis_violation · **Fallback:** explicit framing rule + 180° constraint

**Rationale:** per §3.2 D2.1+D2.2 + §3.3 D3.4 — Murch 视觉维度 + composition_lock user-value

**Budget:** ¥300/episode (compute) · 120s · evolving

---

## §2.7 — Node: `prompt_injector` (提示注入)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.7` (D3.5+D2.4)
> 📚 **Traditional anchor:** 无传统对应(AI-native)
> ⚡ **AIGC transformation:** ai_native

**Layer:** 2 · **Role:** visual_intent · **v1 expert_id:** NEW

**Core task:** 把 intent 翻译为 model-ready prompt + cross-call consistency context

**I/O:** in: visual_intent + style_genome + character_assets;out: model_prompts + consistency_context

**Success criteria:** cross_call_consistency ≥ 0.85;prompt_token_efficiency ≤ 4000 tokens/call
**Fail modes:** consistency_drift / prompt_overload · **Fallback:** carry context + split prompt

**Rationale:** per §3.3 D3.5 + §3.2 D2.4 — AI-native 必要 + invariant ownership

**Budget:** ¥50/episode (compute) · 30s · stable_2026

---

## §2.8 — Node: `visual_executor` (视觉执行)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.8` (D3.1(b)+D2.5)
> 📚 **Traditional anchor:** 传统摄影师 + 动画师;AIGC 压缩合并 (PITFALLS §2.1)
> ⚡ **AIGC transformation:** full_generation

**Layer:** 3 · **Role:** visual_exec · **v1 expert_id:** NEW_COMPOSITE (drawer + animator merged)

**Core task:** 执行视觉资产生成 — 静态图 + 动态视频

**I/O:** in: model_prompts + consistency_context;out: generated_visuals (consumed by audio_pipeline + editor + continuity_auditor)

**Success criteria:** identity_match ≥ 0.85;aesthetic_alignment ≥ 0.7;composition_lock_adherence ≥ 0.85
**Fail modes:** identity_drift / style_drift / temporal_flicker / composition_drift
**Fallback:** loop with continuity_auditor (max 2, ¥50/iter) / regenerate with stronger constraints / split clips

**Rationale:** per §3.3 D3.1(b) + §3.2 D2.5

**Budget:** ¥3500/episode (compute — most expensive) · 1800s · evolving

**Critic pairing:** continuity_auditor (loop_with_critic edge)

---

## §2.9 — Node: `audio_pipeline` (音频管线)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.9` (D3.1(a))
> 📚 **Traditional anchor:** 传统 5 个独立专家(voice + composer + foley + mixer + ADR);AIGC 压缩
> ⚡ **AIGC transformation:** full_generation

**Layer:** 4 · **Role:** audio_post · **v1 expert_id:** NEW_COMPOSITE (5 audio tasks merged)

**Core task:** 执行全部音频生成 + 对齐 + 混音(voicer + lip_sync + composer + foley + mixer)

**I/O:** in: screenplay + generated_visuals + character_assets;out: mixed_audio

**Success criteria:** lufs_compliance ±1 of platform spec;dialogue_intelligibility ≥ 0.9;lip_sync_offset ≤ 80ms
**Fail modes:** tts_pronunciation_degradation / music_emotion_mismatch / lufs_out_of_spec
**Fallback:** switch TTS provider for dialect / emotion tags / human mixer + DSP

**Rationale:** per §3.3 D3.1(a) — 高程序化后期是 AI 加速第一类

**Budget:** ¥1000/episode (compute) · 900s · evolving

---

## §2.10 — Node: `continuity_auditor` (连续性审计)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.10` (D2.4+D2.5+D3.1(c))
> 📚 **Traditional anchor:** 传统剧本监督(continuity supervisor);AIGC automated + loop
> ⚡ **AIGC transformation:** verification

**Layer:** 3 · **Role:** critic_paired · **v1 expert_id:** preserved (renamed from continuity)

**Core task:** 跨镜头 invariant 验证 — identity + wardrobe + 180° axis + spatial + plot continuity

**I/O:** in: generated_visuals + character_assets;out: continuity_score + verdict

**Success criteria:** identity_match ≥ 0.85;axis_compliance 100%;wardrobe_drift 0 scenes
**Fail modes:** identity_misclassification / axis_false_negative · **Fallback:** human review / ensemble voting

**Rationale:** per §3.2 D2.4+D2.5 + §3.3 D3.1(c)

**Budget:** ¥600/episode (compute) · 300s · stable_2026

**Critic pairing:** paired with visual_executor (loop_with_critic edge)

---

## §2.11 — Node: `editor` (剪辑)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.11` (D2.1+D1.2)
> 📚 **Traditional anchor:** 传统剪辑师角色直接适用;Murch Rule of Six 保留
> ⚡ **AIGC transformation:** augmentation

**Layer:** 4 · **Role:** audio_post · **v1 expert_id:** preserved

**Core task:** 把素材 + 音频 + screenplay 整合为最终 cut(节奏 + 场景过渡 + pacing)

**I/O:** in: generated_visuals + screenplay + style_genome;out: edited_sequence (consumed by colorist + human_review_gate_2)

**Success criteria:** murch_rhythm_score ≥ 0.7;pacing_compliance within form envelope
**Fail modes:** rhythm_flat / arc_break · **Fallback:** human override + reference rhythm + theory_critic escalation

**Rationale:** per §3.2 D2.1 + §3.1 D1.2 — Murch + 整合体验

**Budget:** ¥400/episode (human_time) · 600s · evolving

**In-node self-critic:** rhythm self-check (Murch 6-dim quick audit)

---

## §2.12 — Node: `colorist` (调色)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.12` (D2.1+D2.4)
> 📚 **Traditional anchor:** 传统调色师角色直接适用;color theory validated-invariant
> ⚡ **AIGC transformation:** augmentation

**Layer:** 4 · **Role:** audio_post · **v1 expert_id:** preserved

**Core task:** 调色 + color grading strategy — 色调一致性 + 情感色调 + 平台 color spec 适配

**I/O:** in: edited_sequence + style_genome;out: color_graded_sequence

**Success criteria:** style_alignment ≥ 0.8;cross_shot_consistency ≥ 0.9
**Fail modes:** emotion_mismatch / cross_shot_drift · **Fallback:** human override + unified LUT

**Rationale:** per §3.2 D2.1+D2.4 — Murch planarity + style 子维度

**Budget:** ¥300/episode (human_time) · 300s · stable_2026

---

## §2.13 — Node: `hook_retention` (钩子留存)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.13` (D2.6)
> 📚 **Traditional anchor:** 无传统对应(短剧是 AIGC + 平台算法催生的新形态)
> ⚡ **AIGC transformation:** verification

**Layer:** 5 · **Role:** form_specific · **form_scope:** short_drama only · **v1 expert_id:** preserved

**Core task:** 短剧特定 — 前 3 秒 hook + 完播率 + 付费卡点 pacing + 竖屏 framing

**I/O:** in: screenplay + form_context (short_drama only);out: hook_pacing_recommendations (feedback to screenplay)

**Success criteria:** hook_strength_score ≥ 0.75;retention_curve_fit ≥ 0.7
**Fail modes:** hook_too_slow / 付费卡点_misplaced · **Fallback:** feedback to screenplay + A/B test

**Rationale:** per §3.2 D2.6 — 短剧形态特定

**Budget:** ¥200/episode (compute) · 60s · evolving

---

## §2.14 — Node: `quality_gate` (质量门)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.14` (D2.1+D2.5+D3.1(c))
> 📚 **Traditional anchor:** 传统 test screening + final QC;AIGC automated multi-dim
> ⚡ **AIGC transformation:** verification

**Layer:** 6 · **Role:** final_gate · **v1 expert_id:** preserved

**Core task:** 最终 multi-dim scoring — Murch Rule of Six + form 权重 + 平台 spec 合规

**I/O:** in: color_graded_sequence + mixed_audio;out: quality_score_multidim + verdict

**Success criteria:** murch_six_dim_score ≥ 0.7;form_specific_compliance 100%
**Fail modes:** rubric_overweight / false_negative · **Fallback:** weights 可调 + human override

**Rationale:** per §3.2 D2.1+D2.5 + §3.3 D3.1(c)

**Budget:** ¥150/episode (compute) · 60s · stable_2026

---

## §2.15 — Node: `compliance_gate` (合规门)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.15` (D2.6)
> 📚 **Traditional anchor:** 无传统对应(CN 平台 + AIGC 是新形态)
> ⚡ **AIGC transformation:** verification

**Layer:** 6 · **Role:** final_gate · **v1 expert_id:** preserved (renamed from compliance_marketing)

**Core task:** CN 平台合规审核 — pre_check + final(合并)

**I/O:** in: quality_approved_sequence + form_context;out: compliance_verdict + rejection_reason

**Success criteria:** platform_spec_compliance 100%;cn_regulation_compliance 100%
**Fail modes:** false_negative / false_positive · **Fallback:** 90-day rule refresh + human legal review

**Rationale:** per §3.2 D2.6 + Phase 7 §4.15

**Budget:** ¥200/episode (compute) · 120s · stable_2026

---

## §2.16 — Node: `theory_critic` (理论批评)

> 🅰 **First principles:** per `00-FIRST-PRINCIPLES.md §4.16` (D4.2+D4.4)
> 📚 **Traditional anchor:** 传统 theory consultant(批评家 / 影评人咨询)
> ⚡ **AIGC transformation:** ai_bounded

**Layer:** vertical · **Location:** consultative · **Trigger:** creator_pulled (META-06) · **v1 expert_id:** preserved

**Core task:** 咨询式理论批判 — 创作者手动拉,艺术价值 vs 平台优化张力平衡

**I/O:** in: pipeline_state_snapshot + creator_consultation_question;out: theoretical_critique

**Success criteria:** consultation_invoked true/false;creator_usefulness_likert ≥ 4/5
**Fail modes:** theory_academic_disconnect / commercial_drift_ignored · **Fallback:** form_context + balanced perspective

**Rationale:** per §3.4 D4.2+D4.4 + META-06

**Budget:** ¥50/episode (only when invoked) · 120s · evolving

---

## §2.17 — Global Model Annex (dated, per NODE-08)

> ⚠ **This annex is the ONLY place model names appear in the spec suite.**
> The canonical capability-spec layer (§2.1-§2.16) is model-agnostic.
> Model names below are current instantiations as of `verified_date` and WILL change.
> Per PITFALLS §1.3 + §2.7: the DAG must remain valid even if every model below is swapped.

| Node | Model | Role in node | Verified | Stability | Swap alternatives |
|---|---|---|---|---|---|
| creative_source | Claude Sonnet 4.5 | Kernel expansion | 2026-06-16 | evolving | GPT-5, GLM-4.6 |
| style_genome | Claude Sonnet 4.5 | Style extraction | 2026-06-16 | stable_2026 | GPT-5, Gemini 3 Pro |
| screenplay | Claude Sonnet 4.5 | Screenplay gen | 2026-06-16 | evolving | GPT-5, GLM-4.6 |
| script_auditor | Claude Haiku 4.5 | 5-dim audit | 2026-06-16 | stable_2026 | GPT-5-mini |
| character_designer | FLUX 2 + IP-Adapter | Face/body gen | 2026-06-16 | evolving | SD4 + IP-Adapter |
| character_designer | CosyVoice 2 | Voice cloning | 2026-06-16 | stable_2026 | ElevenLabs VC |
| cinematographer | Claude Sonnet 4.5 | Visual intent | 2026-06-16 | evolving | GPT-5 |
| prompt_injector | Template + few-shot | Engineering | 2026-06-16 | stable_2026 | N/A |
| visual_executor (drawer) | FLUX 2 | Image gen | 2026-06-16 | evolving | SD4, Ideogram |
| visual_executor (animator) | Sora 2 / Kling 2.0 | Video gen | 2026-06-16 | evolving | Veo 4, Runway Gen-5 |
| audio_pipeline (voicer) | CosyVoice 2 / ElevenLabs v3 | TTS | 2026-06-16 | evolving | Azure TTS, OpenAI TTS-2 |
| audio_pipeline (composer) | Suno V5 / Udio 2 | Music gen | 2026-06-16 | evolving | MusicGen-Large |
| audio_pipeline (foley) | Stable Audio Open | Foley gen | 2026-06-16 | evolving | AudioLDM-3 |
| audio_pipeline (mixer) | DSP engineering (ffmpeg) | LUFS targeting | 2026-06-16 | stable_2026 | N/A |
| editor | Claude Sonnet 4.5 | Cut-point suggestions | 2026-06-16 | evolving | GPT-5 |
| colorist | DaVinci Resolve + AI LUT | Color grading | 2026-06-16 | stable_2026 | Baseline AI Color |
| hook_retention | Claude Sonnet 4.5 | Hook + retention | 2026-06-16 | evolving | GPT-5, GLM-4.6 |
| quality_gate | Claude Sonnet 4.5 + custom | Multi-dim verdict | 2026-06-16 | stable_2026 | GPT-5, ensemble |
| compliance_gate | Claude Sonnet 4.5 + rules | CN compliance | 2026-06-16 | stable_2026 | GLM-4.6, CN API |
| theory_critic | Claude Opus 4.7 | Theory consultation | 2026-06-16 | evolving | GPT-5, Gemini 3 Pro |

**Stability legend:** stable_2026 (≥2 year persistence) / evolving (quarterly updates) / research_bet (may fail)

---

## §2.18 — Regeneration Note

This Markdown is regenerable from `nodes.yaml`. Regeneration procedure:
1. Read `nodes.yaml` → emit §2.X per node with 3-line audit header + 15 spec fields
2. Aggregate `current_instantiation` entries into §2.17 table

Phase 12 GOV-02 lint (`scripts/validate_design.py`) will verify regenerability + check capability-spec layers contain NO model names.

---

*Document version: design-2026-06-16-prfp*
*Phase 8 of v2.0 PRFP milestone*
*Bilingual policy: EN structure + CN prose (META-03)*
