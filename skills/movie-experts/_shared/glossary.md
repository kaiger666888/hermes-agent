# Glossary — Movie-Experts Suite v2

**Purpose:** Canonical EN↔CN term dictionary for the Movie-Experts Suite. Every expert's SKILL.md and `references/*.md` MUST use these terms consistently. Drift in translation breaks downstream metric comparability and judge-prompt reliability.

**Last updated:** 2026-06-17 (Phase 18 — DOC-02 verification: 5 new-expert terms confirmed present, 2 added [continuity_auditor + compliance_gate], 0 inline-updated)
**Refresh cadence:** Phase 1+ adds terms as each new expert requires them; Phase 6 does a full consistency pass.

---

## How to use this glossary

1. **Authoring SKILL.md / refs:** When you write 短剧-specific terms, look them up here first. If a term exists, use the canonical CN form. If not, add it here with a bilingual definition + context note.
2. **Cross-expert signals:** When one expert emits a term (e.g., screenplay emits `钩子`), downstream experts (editor, audio_pipeline (composer sub-step)) MUST consume the same CN token, not an ad-hoc English translation.
3. **LLM-as-judge prompts:** Judge prompts reference these terms by their CN form for 短剧-specific evaluation anchors. Bilingual definitions prevent judge-model misreading.

---

## Core terms (SC #5 required + extended)

### 运镜 / cinematography / camera movement
**CN:** 运镜 — 摄影机移动方式的统称,包括推拉摇移升降跟。
**EN:** The collective term for camera movement techniques (dolly, pan, tilt, crane, tracking, handheld).
**Context:** Used by EXPERT-CINE (Phase 4) and references `visual_executor.animator.camera_type`. Distinguished from 景别 (shot size) and 视角 (angle).

### 钩子 / hook
**CN:** 钩子 — 短剧开场 3 秒内抓住观众注意力的设计。分为情感钩、悬念钩、冲突钩、反差钩、情绪爆点钩五类。
**EN:** Opening 3-second attention-grabber in 短剧. Five categories: emotional hook, suspense hook, conflict hook, contrast hook, emotional-peak hook.
**Context:** EXPERT-HOOK (Phase 2) owns the taxonomy. screenplay must integrate hook into opening beat; editor must pace for hook reveal.

### 卡点 / paywall cliffhanger / paywall moment
**CN:** 卡点 — 小程序剧中放置付费墙的剧情节点,通常在每集 60-80% 处,以悬念收尾强制付费解锁下一集。
**EN:** Paywall cliffhanger — narrative beat in 小程序剧 where a paywall is placed (typically at 60-80% of episode runtime), ending on a suspense hook to force paid unlock of the next episode.
**Context:** EXPERT-HOOK designs placement; EXPERT-COMPLI validates compliance with platform paywall rules (some platforms cap paywall frequency).

### 爆款 / viral formula / explosive hit
**CN:** 爆款 — 在特定平台算法下获得异常高完播率 / 转发率 / 付费率的短剧,通常具有可复制的元素组合。
**EN:** Viral formula — 短剧 that achieves abnormally high completion / share / paid-conversion rates under a specific platform's algorithm; usually has a reproducible element combination.
**Context:** EXPERT-HOOK + EXPERT-COMPLI jointly identify 爆款 elements vs 审核红线 overlap. Platform-specific (抖音 爆款 ≠ 快手 爆款).

### 男频 / male-oriented channel
**CN:** 男频 — 面向男性观众主体的短剧类型,常见题材:赘婿逆袭、战神归来、重生复仇、都市修仙。
**EN:** Male-oriented channel — 短剧 genre targeting male-primary audiences. Common themes: 慕强逆袭 (underdog-rise), 战神归来 (warrior-return), 重生复仇 (rebirth-revenge), 都市修仙 (urban-cultivation).
**Context:** 爆款公式 diverges sharply by 男频 vs 女频. screenplay and style_genome must branch.

### 女频 / female-oriented channel
**CN:** 女频 — 面向女性观众主体的短剧类型,常见题材:豪门虐恋、闺蜜背叛、替身白月光、宫斗宅斗。
**EN:** Female-oriented channel — 短剧 genre targeting female-primary audiences. Common themes: 豪门虐恋 (billionaire-romance), 闺蜜背叛 (best-friend-betrayal), 替身白月光 (substitute-first-love), 宫斗 (harem-intrigue).
**Context:** Pair with 男频; never assume a universal 爆款 formula.

### 完播率 / completion rate
**CN:** 完播率 — 观众从开场看到结尾(或看到卡点)的比例,是短剧平台算法的核心权重指标。
**EN:** Completion rate — fraction of viewers who watch from opening to ending (or to paywall); core algorithmic weight metric on 短剧 platforms.
**Context:** EXPERT-HOOK optimizes for 完播率; common rule: front-load conflict within first 5s (completion drops at 7s for romance genre).

### 付费卡点 / paid-conversion trigger
**CN:** 付费卡点 — 触发观众付费解锁下一集的剧情节点。与 卡点 (paywall placement) 相关但更强调转化率设计。
**EN:** Paid-conversion trigger — narrative beat designed to maximize the probability a viewer pays to unlock the next episode. Related to 卡点 (placement) but emphasizes conversion-rate design.
**Context:** 小程序剧 typically requires 付费卡点 at min 3-5 of 10 episodes (research SUMMARY). EXPERT-HOOK + EXPERT-COMPLI co-own.

### 钩子 / opening hook (alt form)
**CN:** 钩子 — (alt reading) 特指开场 3 秒钩子,与完整 hook taxonomy 中第一类同义。
**EN:** Opening hook (alt form) — specifically the 3-second opening hook; synonymous with category 1 of the full hook taxonomy.
**Context:** Use this reading when the surrounding context is "opening" rather than "taxonomy".

### 爽点 / satisfaction beat
**CN:** 爽点 — 让观众产生强烈情绪满足感的剧情节点,通常伴随主角逆袭、打脸反派、揭穿阴谋等桥段。
**EN:** Satisfaction beat — narrative moment that produces strong emotional satisfaction in the viewer; typically伴随 protagonist-rise, face-slap-of-antagonist, conspiracy-reveal tropes.
**Context:** 爽点 density is a core 爆款 driver in 男频 短剧. EXPERT-HOOK designs 爽点 placement; editor paces for 爽点 payoff.

### 击中点 / emotional-impact point
**CN:** 击中点 — 短剧中触发观众强烈共鸣的瞬间,可能是台词、镜头、配乐或三者合一。
**EN:** Emotional-impact point — instant in 短剧 that triggers strong audience resonance; may be a line of dialogue, a shot, a musical cue, or a combination.
**Context:** Distinct from 爽点 (satisfaction) — 击中点 can be sad / bitter / nostalgic / cathartic. audio_pipeline (composer sub-step) aligns musical sting to 击中点.

### 镜头语言 / shot grammar / cinematic language
**CN:** 镜头语言 — 通过镜头选择(景别、视角、运动、构图)传递意义的系统化表达方式。
**EN:** Shot grammar — systematic expression of meaning through lens choices (shot size, angle, movement, composition).
**Context:** EXPERT-CINE (Phase 4) owns 镜头语言 semantics; scene_builder (deprecated Phase 17 → cinematographer+style_genome) owns spatial geometry; visual_executor (animator sub-step) owns motion execution.

### 景别 / shot size / shot scale
**CN:** 景别 — 主体在画面中所占比例的分级。常见分:远景、全景、中景、近景、特写、大特写。
**EN:** Shot size — classification of subject-to-frame ratio. Standard tiers: extreme-wide, wide, medium, medium-close, close-up, extreme-close-up.
**Context:** EXPERT-CINE owns 景别 vocabulary; editor consumes for FxRxT matrix F (Frame) dimension.

### 视角 / angle / camera angle
**CN:** 视角 — 摄影机相对主体的拍摄角度。常见分:平视、仰视、俯视、鸟瞰、虫瞰。
**EN:** Camera angle — shooting angle of camera relative to subject. Standard tiers: eye-level, low-angle, high-angle, bird's-eye, worm's-eye.
**Context:** Pairs with 景别 to form the basic 镜头语言 vocabulary. Low-angle = power/dominance; high-angle = vulnerability.

### 轴线 / axis line / 180° rule line
**CN:** 轴线 — 场景中两个主体之间的连线,定义了 180° 拍摄半圆。越线拍摄会造成观众方向感混乱。
**EN:** Axis line — imaginary line between two subjects in a scene, defining the 180° shooting semicircle. Crossing the line disorients the viewer.
**Context:** editor enforces 180° axis compliance (zero-tolerance metric). EXPERT-CINE documents the rule; scene_builder (deprecated Phase 17 → cinematographer+style_genome) pre-computes axis data.

### 调度 / blocking / staging
**CN:** 调度 — 演员在场景空间中的位置安排与移动路径设计。
**EN:** Blocking / staging — arrangement and movement paths of actors within the scene space.
**Context:** performer (deprecated Phase 17 → character_designer+screenplay) outputs stage positions (S dimension); scene_builder (deprecated Phase 17 → cinematographer+style_genome) validates spatial feasibility; EXPERT-CINE consumes for camera-blocking design.

---

## Extended terms (added beyond SC #5 minimum)

### 转发率 / share rate
**CN:** 转发率 — 观众转发短剧的比例,平台算法权重仅次于完播率。
**EN:** Share rate — fraction of viewers who share the 短剧; second-highest algorithmic weight after 完播率.
**Context:** EXPERT-HOOK optimizes 转发率 triggers (usually 击中点 or 爽点 driven).

### 竖屏 / vertical screen / 9:16
**CN:** 竖屏 — 9:16 竖屏画幅,是 抖音 / 快手 / 视频号 短剧的标准画幅。
**EN:** Vertical screen — 9:16 aspect ratio, standard for 抖音 / 快手 / 视频号 短剧.
**Context:** Every expert must account for 竖屏 constraints (composition safe-zones, cut density 1.5-2x horizontal, caption strip overlay).

### 备案 / filing / regulatory filing
**CN:** 备案 — 网络微短剧 / AI 漫剧 在中国大陆分发前必须完成的广电总局备案流程。
**EN:** Regulatory filing — mandatory 广电总局 filing process for 网络微短剧 / AI 漫剧 before distribution in mainland China.
**Context:** EXPERT-COMPLI (Phase 1) owns 备案 workflow. AI 漫剧 备案 regime effective 2026-04-01.

### 标识 / labeling / AI-content label
**CN:** 标识 — 网信办《人工智能生成合成内容标识办法》要求 AI 生成内容必须携带的可见与不可见标识。
**EN:** AI-content label — visible and invisible labeling mandated by 网信办《人工智能生成合成内容标识办法》 for AI-generated content.
**Context:** EXPERT-COMPLI automates 标识 compliance; effective 2025-09-01.

### 男主 / 女主 / male lead / female lead
**CN:** 男主 / 女主 — 短剧的男主角 / 女主角。男频短剧以男主视角为主,女频反之。
**EN:** Male lead / female lead — protagonist of the 短剧. 男频 centers male lead POV; 女频 centers female lead POV.
**Context:** screenplay branches narrative POV by 男频/女频; performer (deprecated Phase 17 → character_designer+screenplay) adjusts body-language intensity accordingly.

### 小程序剧 / mini-program drama
**CN:** 小程序剧 — 在微信小程序 / 抖音小程序内分发的短剧,通常以 10-80 集连续剧形式付费解锁。
**EN:** Mini-program drama — 短剧 distributed via WeChat / 抖音 mini-programs, typically as 10-80 episode serialized paid-unlock format.
**Context:** 小程序剧 has the strictest 付费卡点 requirements (min 3-5 of 10 episodes) and longest narrative arc.

### 男频 / 女频 (simplified channel terms)
**CN:** 男频 / 女频 — (simplified form) 详见上方完整定义。
**EN:** See full entries above.
**Context:** Use these short forms when the surrounding sentence already disambiguates.

### 慕强 / power-fantasy
**CN:** 慕强 — 男频短剧的核心情绪驱动:主角从弱到强、碾压对手的爽感循环。
**EN:** Power-fantasy — core emotional driver of 男频 短剧: protagonist rises from weak to strong, crushing opponents in a 爽点 cycle.
**Context:** EXPERT-HOOK uses 慕强 as the primary 爽点 design pattern for 男频.

---

## Phase 7 additions (5 new experts — script_auditor / lip_sync / character_designer / storyboard_designer (deprecated Phase 17 → cinematographer) / creative_source)

### 故事核 / Story Kernel
**CN:** 故事核 — 从社会结构性冲突中提炼的不可逆戏剧前提,一句话能描述的核心矛盾。
**EN:** Story Kernel — irreducible dramatic premise distilled from social structural conflict, describable in a single sentence.
**Context:** creative_source expert's output artifact. Lives upstream of style_genome + screenplay. Multi-strata overlay produces resonance coefficient (1.0-3.0).

### 六层地层学 / Six-Strata
**CN:** 六层地层学 — 创意源头专家的分析框架,把社会分为 L1 制度 / L2 技术 / L3 人口 / L4 空间 / L5 代际契约 / L6 心灵 六个地层,逐层扫描结构性裂缝。
**EN:** Six-Strata — creative_source expert's analysis framework decomposing society into 6 layers (institutional / technological / demographic / spatial / intergenerational-contract / psychosocial).
**Context:** Theoretical basis: Bourdieu field theory + Giddens structuration + Barthes narrative analysis + Foucault power/knowledge.

### 不可言说性 / Unspeakability
**CN:** 不可言说性 — 故事核在 CN 平台制作的禁忌程度,10 分制评分(1=主流安全 / 10=绝对禁忌)。包含 4 子维度:政治敏感度 / 平台算法风险 / 观众不适度 / 监管红线。
**EN:** Unspeakability — 10-point score (1=mainstream-safe / 10=absolute-taboo) measuring how off-limits a story kernel is for CN platform production. 4 sub-dimensions: political sensitivity / platform algorithm risk / audience discomfort / regulatory redline.
**Context:** Scores ≥ 9 trigger VETO; 5-8 require per-platform reframing paths.

### 角色圣经 / Character Bible
**CN:** 角色圣经 — character_designer 输出的角色身份契约 JSON,包含 4D 锚点 + 分层 STYLE_PREFIX + 一致性压力测试结果 + negative_traits + consistency_lock。下游所有专家(visual_executor / audio_pipeline (lip_sync sub-step) / continuity_auditor)的 ground truth。
**EN:** Character Bible — character identity contract JSON output by character_designer. Contains 4D anchors + layered STYLE_PREFIX + consistency stress-test results + negative_traits + consistency_lock. Ground truth for all downstream consumers.
**Context:** Schema version 2.0.0; frozen after stress test pass.

### 4D 锚点 / 4D Anchor
**CN:** 4D 锚点 — 角色的 4 个标准视角源图(front 正面 / three_quarter 3/4 / side 侧面 / back 背面),构成角色身份的"4D 护照"。下游专家按 3Q > Front > Side > Back 优先级使用。
**EN:** 4D Anchor — 4 canonical view source images (front / three_quarter / side / back) defining a character's identity across all shot angles. Downstream consumers use 3Q > Front > Side > Back priority.
**Context:** character_designer output; audio_pipeline (lip_sync sub-step) prefers front + 3Q for identity reference.

### 分层 STYLE_PREFIX / Layered Style Prefix
**CN:** 分层 STYLE_PREFIX — character_designer 的核心方法论,把角色风格分为 CORE(全局不变)/ IDENTITY(严格锁定)/ VARIANCE(随镜头变化)三层。组合公式:`{CORE}, {IDENTITY}, {VARIANCE}`。
**EN:** Layered STYLE_PREFIX — character_designer's core methodology decomposing character style into 3 layers (CORE global-frozen / IDENTITY strict-locked / VARIANCE scene-mutable). Composition: `{CORE}, {IDENTITY}, {VARIANCE}`.
**Context:** Locked STYLE_PREFIX is used by every downstream image-gen prompt.

### 一致性压力测试 / Consistency Stress Test
**CN:** 一致性压力测试 — 在锁定角色前,把候选角色放入 3 个完全不同场景验证一致性的协议。3 场景:街头夜景(strength 0.40)/ 室内特写(0.55)/ 动作侧拍(0.35)。CLIP-I ≥ 0.80 + DINO-I ≥ 0.78 才 pass。
**EN:** Consistency Stress Test — protocol verifying candidate character identity survives 3 radically different scene contexts before lock. 3 scenes: street night neon (0.40) / indoor close-up (0.55) / running side view (0.35). CLIP-I ≥ 0.80 + DINO-I ≥ 0.78 to pass.
**Context:** Gate between variant selection and final character lock.

### 分镜 / Storyboard
**CN:** 分镜 — 把剧本场景拆解为可执行的 per-shot JSON 列表,每 shot 包含 shot_id / camera 参数 / action / duration / reference_image / end_frame / anchoring。
**EN:** Storyboard — executable per-shot JSON list decomposed from screenplay scenes. Each shot contains shot_id / camera params / action / duration / reference_image / end_frame / anchoring.
**Context:** storyboard_designer (deprecated Phase 17 → cinematographer composition_lock sub-task) output; downstream consumers are visual_executor / editor / continuity_auditor.

### 4D 锚定 / 4D Anchoring
**CN:** 4D 锚定 — 分镜 shot 的渲染层控制参数,4 维度:depth(ControlNet Depth)/ identity(IP-Adapter)/ lighting(IC-Light)/ temporal(AnimateDiff)。每维度可独立开关 + 调强度。4 级降级策略:Draft / Standard / Cinematic / Premium。
**EN:** 4D Anchoring — render-layer control parameters per storyboard shot. 4 dimensions: depth (ControlNet Depth) / identity (IP-Adapter) / lighting (IC-Light) / temporal (AnimateDiff). Each independently toggleable + strength-adjustable. 4-tier degradation: Draft / Standard / Cinematic / Premium.
**Context:** Cinematic tier = default for production; Premium required for final delivery.

### 延续锚点 / Extension-Chain End-Frame
**CN:** 延续锚点 — 多 shot 场景中,前一个 shot 的 end_frame 作为下一个 shot 的视觉延续参考。让 visual_executor 的 animator sub-step 在跨 shot 生成时保持角色 + 场景一致性。
**EN:** Extension-Chain End-Frame — in multi-shot scenes, prior shot's end_frame serves as next shot's visual continuity reference. Enables visual_executor's animator sub-step to maintain character + scene consistency across shot boundaries.
**Context:** Required for shots 1..N-1 in any scene per storyboard-schema.md.

### 唇形同步 / Lip Sync
**CN:** 唇形同步 — 把目标音频对齐到人物视频的嘴部运动,生成口型与音频精确匹配的视频。基于音频驱动的潜在扩散(LatentSync v1.5 / v1.6)。
**EN:** Lip Sync — aligning target audio to mouth motion in person footage, generating video where lip movement matches audio precisely. Based on audio-conditioned latent diffusion (LatentSync v1.5 / v1.6).
**Context:** audio_pipeline (lip_sync sub-step) domain. Intra-expert handoff from voicer sub-step (audio synthesis) — voicer sub-step produces WAV, lip_sync sub-step aligns WAV to footage.

### LSE / Lip Sync Error — Distance
**CN:** LSE — SyncNet 嵌入空间中音频嵌入与视频嵌入的平均欧氏距离,客观指标,越低越好。SOTA ≤ 6.5。
**EN:** LSE (Lip Sync Error — Distance) — average Euclidean distance between audio and video embeddings in SyncNet space. Objective metric; lower is better. SOTA ≤ 6.5.
**Context:** International-standard metric (no LLM-judge required). Computed on LRS2 / LRS3 benchmarks.

### LSE-C / Lip Sync Error — Confidence
**CN:** LSE-C — 错位音频 baseline 与同步输出的 LSE 差值,客观指标,越高越好。SOTA ≥ 7.0。
**EN:** LSE-C (Lip Sync Error — Confidence) — distance improvement between off-sync baseline and synced output. Objective metric; higher is better. SOTA ≥ 7.0.
**Context:** Paired with LSE; both must pass for Grade A.

### 剧本审计 / Script Audit
**CN:** 剧本审计 — 在制作前对剧本进行 5 维度量化评分(叙事结构 / 情感弧线 / Hook 强度 / 角色网络 / 完播率预测),输出 ScoreReport JSON。与 screenplay 解耦:screenplay 写,script_auditor 评。
**EN:** Script Audit — pre-production 5-dimension quantitative scoring of scripts (narrative structure / emotion arc / hook strength / character network / completion-rate forecast), outputting ScoreReport JSON. Decoupled from screenplay: screenplay writes, script_auditor audits.
**Context:** script_auditor expert's domain. Dimension 5 (completion-rate forecast) can be independently validated against actual completion rate via Pearson correlation.

### 完播率预测 / Completion Rate Forecast
**CN:** 完播率预测 — script_auditor Dimension 5,基于疲劳曲线 + 信息密度物理模型预测 A/B/C/D 级完播率区间。可独立验证(预测中点 vs 实际完播率 Pearson ≥ 0.65)。
**EN:** Completion Rate Forecast — script_auditor Dimension 5, predicting A/B/C/D completion-rate band based on fatigue-curve + information-density physics model. Independently validatable (predicted midpoint vs actual completion rate Pearson ≥ 0.65).
**Context:** The only script_auditor dimension not requiring LLM-judge for validation.

---

## Phase 14 additions (visual_executor merge)

### visual_executor / 视觉执行专家

**CN:** 视觉执行专家 — Phase 14 merge of `drawer` (FLUX 2 image gen) + `animator` (Hermes-catalog video gen)。声明 `sub_steps: [drawer, animator]`,unified visual + temporal consistency context per Phase 7 §4.8 + PITFALLS §2.1。Backward-compat aliases `[drawer, animator]` 保留 per FOUND-08。

**EN:** Visual Executor Expert — Phase 14 merge of `drawer` + `animator` experts per v2.0 PRFP DAG. Unified sub-steps handle image gen (FLUX 2 + LoRA + IP-Adapter + InstantID) and video gen (veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0).

**Context:** Replaces the v1 drawer → animator inter-expert collaboration edge with an intra-expert sub-step handoff (drawer generates first_frame I-frame → animator consumes it). Declared at `skills/movie-experts/visual_executor/SKILL.md`.

---

## Phase 15 additions (audio_pipeline merge)

### audio_pipeline / 音频管线专家

**CN:** 音频管线专家 — Phase 15 merge of 5 canonical audio experts (voicer, lip_sync, composer, foley, mixer) + spatial_audio (folded per disposition D-1)。声明 `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]`,unified audio consistency context per Phase 7 §4.9 + PITFALLS §2.6。spatial_audio folded (not deprecated) because spatial rendering is fundamentally a mixer/mastering concern (Atmos, HRTF, binaural)。Backward-compat aliases `[voicer, lip_sync, composer, foley, mixer, spatial_audio]` 保留 per FOUND-08。

**EN:** Audio Pipeline Expert — Phase 15 merge of 6 predecessors per v2.0 PRFP DAG §4.9. Unified sub-steps handle TTS (MiniMax / ElevenLabs / Voxtral / Gemini / Edge / NeuTTS), audio-driven lip sync (LatentSync, LRS2/LRS3 benchmark), music generation (MusicGen-Large, Chion audio-vision), SFX (Stable Audio Open, 7D parametric), mixing (Senior Mixing Secrets, LUFS mastering), and spatial audio (Dolby Atmos, HRTF binaural).

**Context:** Replaces the v1 inter-expert audio collaboration edges (voicer↔mixer, composer↔foley, etc.) with intra-expert sub-step handoffs. spatial_audio disposition D-1 (fold) documented in the merged SKILL.md `## Spatial Audio Disposition` H2 section per ROADMAP §15 criterion #2. Declared at `skills/movie-experts/audio_pipeline/SKILL.md`.

---

## Phase 16 additions (prompt_injector NEW AI-native expert)

### prompt_injector / 提示注入 / Prompt Injector

**CN:** 提示注入 — Phase 16 NEW AI-native node(无 v1 前身)。把上游人类意图 — `visual_intent`(来自 cinematographer)+ `style_genome_5d`(来自 style_genome)+ `character_assets`(来自 character_designer)— 翻译为 model-ready prompts(`model_prompts` + `consistency_context`)供 visual_executor 消费。owns 两项质量指标:`cross_call_consistency` ≥ 0.85(下游视觉输出在多次 gen-model 调用间保持风格/身份一致性)+ `prompt_token_efficiency` ≤ 4000 tokens/call(token 预算硬上限)。Fail modes:`consistency_drift`(跨调用一致性上下文丢失 → fallback:显式 carry + 重复关键约束)+ `prompt_overload`(token 超载 → fallback:拆分为结构化 sections + system prompt 承载稳定约束)。Per v2.0 PRFP Phase 7 §4.7 D3.5+D2.4 derivation。

**EN:** Prompt Injector — Phase 16 NEW AI-native node (no v1 predecessor) that translates upstream human intent — `visual_intent` (from cinematographer) + `style_genome_5d` (from style_genome) + `character_assets` (from character_designer) — into model-ready prompts (`model_prompts` + `consistency_context`) consumed by visual_executor. Owns two quality metrics: `cross_call_consistency` (≥0.85 — downstream visual outputs maintain style/identity across multiple gen-model calls) and `prompt_token_efficiency` (≤4000 tokens/call — token budget hard ceiling). Fail modes: `consistency_drift` (consistency context lost between calls → fallback: explicit carry + repeat key constraints) and `prompt_overload` (prompt token overload → fallback: split into structured sections + system prompt for stable constraints). Per v2.0 PRFP Phase 7 §4.7 D3.5+D2.4 derivation.

**Context:** Distinct from cinematographer (which owns shot intent / composition_lock) — prompt_injector owns the prompt-assembly layer that did not exist in traditional pre-AI cinematography. Provider-agnostic: uses `<image_primary>` / `<video_primary>` placeholders (no literal model names committed as identifiers in SKILL.md body). Related_skills peer set: [creative_source, cinematographer, visual_executor, audio_pipeline]. Mapping type in skills-mapping.yaml: `new_ai_native`. Declared at `skills/movie-experts/prompt_injector/SKILL.md`.

---

## Phase 18 canonical term reconciliation (DOC-02 verification)

### continuity_auditor / 连续性审计专家

**CN:** 连续性审计专家 — Phase 13 rename from `continuity`(per ROADMAP §13 + skills-mapping.yaml RENAME-01)。强调 "critic/audit" 角色 — 不是被动记录连续性,而是主动审计跨 shot 的一致性,在 L3 critic_paired with visual_executor。审计 4 个维度:face identity / wardrobe / color / object,加 eyeline match + 180° axis compliance(zero-tolerance metric)。输出 `continuity_audit.json`,与 visual_executor 形成显式 loop_with_critic(见 `01-NODE-DAG.md §1.4`):max 2 iter,exit 条件 `identity_match ≥ 0.85 AND axis_compliance = 100%`,cost ceiling ¥50/iter。Backward-compat alias `continuity` 保留 per FOUND-08(`skills/movie-experts/continuity/SKILL.md` 是 redirect stub,`metadata.hermes.aliases: [continuity]` 在新 SKILL.md frontmatter)。

**EN:** Continuity Auditor Expert — Phase 13 rename from `continuity` per v2.0 PRFP DAG. Emphasizes the active critic/audit role (not passive continuity recording) at L3 critic_paired with visual_executor. Audits 4 dimensions: face identity / wardrobe / color / object, plus eyeline match + 180° axis compliance (zero-tolerance). Outputs `continuity_audit.json`, forms an explicit loop_with_critic with visual_executor (per `01-NODE-DAG.md §1.4`): max 2 iterations, exit condition `identity_match ≥ 0.85 AND axis_compliance = 100%`, cost ceiling ¥50/iter. Backward-compat alias `continuity` preserved per FOUND-08.

**Context:** DAG layer L3 (Visual exec — critic_paired with visual_executor). Renamed to emphasize that this is an active audit role that pairs with visual_executor's generation loop, not a standalone continuity recorder. Mapping type in skills-mapping.yaml: `one_to_one_renamed`. Declared at `skills/movie-experts/continuity_auditor/SKILL.md`.

### compliance_gate / 合规门

**CN:** 合规门 — Phase 13 rename from `compliance_marketing`(per ROADMAP §13 + skills-mapping.yaml RENAME-02)。聚焦 pure compliance — 分离 marketing 到独立 ref 或 sub-skill,只保留 CN content-rules gate + AIGC labeling + per-platform distribution + 爆款 vs 红线 review。DAG 位置 L6 final_gate(与 quality_gate 配对,sequential:quality_gate → compliance_gate 是最终门)。Backward-compat alias `compliance_marketing` 保留 per FOUND-08。per v2.0 PRFP DAG §1.4 edges:`audio_pipeline → quality_gate` + `colorist → quality_gate` + `quality_gate → compliance_gate`。

**EN:** Compliance Gate Expert — Phase 13 rename from `compliance_marketing` per v2.0 PRFP DAG. Focuses on pure compliance — separates marketing concerns to independent refs/sub-skills, retaining CN content-rules gate + AIGC labeling + per-platform distribution + 爆款 vs 红线 review. DAG position L6 final_gate (paired with quality_gate, sequential: quality_gate → compliance_gate is the final gate). Backward-compat alias `compliance_marketing` preserved per FOUND-08.

**Context:** DAG layer L6 (Final gates — paired with quality_gate per v2.0 PRFP DAG §1.4 edges). The rename separates the pure-compliance role from the marketing/distribution role the v1 expert carried; compliance_gate owns the hard regulatory gate (备案 + 标识 + 红线), while marketing formulas now live as `references/viral-element-catalog.md` etc. Mapping type in skills-mapping.yaml: `one_to_one_renamed`. Declared at `skills/movie-experts/compliance_gate/SKILL.md`.

---

## Phase 18 DOC-02 verification matrix

Per REQUIREMENTS DOC-02, `_shared/glossary.md` must have entries for: `visual_executor`, `audio_pipeline`, `prompt_injector`, `continuity_auditor`, `compliance_gate`.

| Term | Line of entry (pre-Phase 18) | Phase 18 status |
|------|------------------------------|-----------------|
| `visual_executor` | line 227 (`### visual_executor / 视觉执行专家`) | PRESENT — no action needed (Phase 14 additions section) |
| `audio_pipeline` | line 239 (`### audio_pipeline / 音频管线专家`) | PRESENT — no action needed (Phase 15 additions section) |
| `prompt_injector` | line 251 (`### prompt_injector / 提示注入 / Prompt Injector`) | PRESENT — no action needed (Phase 16 additions section) |
| `continuity_auditor` | (none — only inline references at lines 164 + 186) | **ADDED in Phase 18 §Phase 18 canonical term reconciliation** (bilingual CN/EN/Context per DOC-02) |
| `compliance_gate` | (none — no entry; role-only references via EXPERT-COMPLI) | **ADDED in Phase 18 §Phase 18 canonical term reconciliation** (bilingual CN/EN/Context per DOC-02) |

**Verification verdict:** 5 / 5 terms present with dedicated H3 entries post-Phase 18. DOC-02 PASS.

---

## Phase 19 canonical terms (SNOWFLAKE-04)

Per REQUIREMENTS SNOWFLAKE-04, `_shared/glossary.md` must have 4 new H3 entries: `Snowflake Method`, `Story Spine`, `Premise Sentence`, `Scene List` — each with EN↔CN bilingual definitions and Ingermanson 2000s 出处.

### Snowflake Method / 雪花法

**CN:** 雪花法 — Randy Ingermanson 在 2002-2013 期间系统化的递进式展开创作法。从一句话 premise 出发,逐层放大到段落(Story Spine)→ 角色概要 → 一页大纲 → 角色传记 → 四页大纲 → 完整角色表 → 场景列表(Scene List)→ 场景描述 → 初稿。10 步严格递进,前一步是后一步的唯一输入。Phase 19 把雪花法挂载到 `creative_source` 的 StoryKernel 输出与 `screenplay` 的 Snyder 15-beat 消费之间,填补"一句话 → 段落 → 场景"的展开塌陷。雪花法不替代 StoryKernel(它消费 StoryKernel),也不替代 Snyder beat sheet(它产出可被 Snyder 消费的一页大纲 scaffold)。

**EN:** Snowflake Method — recursive expansion writing method systematized by Randy Ingermanson between 2002-2013. Starting from a one-sentence premise, it progressively expands through paragraph (Story Spine) → character synopses → one-page synopsis → character biographies → four-page synopsis → full character chart → scene list → scene descriptions → first draft. The 10 steps strictly recurse — each step's output is the sole input to the next step. Phase 19 mounts Snowflake between `creative_source`'s StoryKernel output and `screenplay`'s Snyder 15-beat consumption, filling the "one-hop collapse" between premise → paragraph → scene. Snowflake does NOT replace StoryKernel (it consumes it), nor Snyder beat sheet (it produces a scaffold Snyder then consumes).

**Context:** Source: Randy Ingermanson, *How to Write a Novel Using the Snowflake Method* (2013 10th-anniversary edition; method originally published on `advancedfictionwriting.com` 2002-2003 article series). Phase 19 (SNOWFLAKE-01..04) integrates this method into creative_source + screenplay experts. Canonical ref: [`creative_source/references/snowflake-method.md`](../creative_source/references/snowflake-method.md). Snowflake Step 1-4 (premise → paragraph → character synopses → one-page synopsis) is the forced minimum for 短剧 60-180s 单集; Step 5-6 optional; Step 7-10 deferred to screenplay internal Beat Planning. Trigger conditions: StoryKernel `unspeakability_score ≥ 7` OR `dramatic_potential.overall ≥ 0.75` OR `strata_overlay_coefficient ≥ 1.7`.

### Story Spine / 故事脊

**CN:** 故事脊 — 雪花法 Step 2 paragraph expansion 的结构模板,源自 Ingermanson 对 Kenn Adams 的 Story Spine improvisation 框架的改编(Adams 原始 8 段:Once upon a time... / Every day... / But one day... / Because of that... × 3 / Until finally... / And ever since then...)。雪花法把它压缩为 5 句话段落:开头(1 句)+ 三幕灾难(3 句,每句对应一幕的灾难转折)+ 结尾(1 句)。在 Phase 19 的短剧适配中,每句 ≤ 12 字 —— 5 句 = 60 字 ≈ 90s 单集开场 30s 的信息密度。Story Spine 是 Snowflake Step 2 的唯一结构模板。

**EN:** Story Spine — structural template for Snowflake Method Step 2 paragraph expansion, derived from Ingermanson's adaptation of Kenn Adams's Story Spine improvisation framework (Adams's original 8 segments: "Once upon a time... / Every day... / But one day... / Because of that..." × 3 / "Until finally... / And ever since then..."). Snowflake compresses it into a 5-sentence paragraph: opening (1 sentence) + three disasters (3 sentences, each corresponding to one act's disaster turning point) + ending (1 sentence). In Phase 19's 短剧 adaptation, each sentence ≤ 12 chars — 5 sentences = 60 chars ≈ information density of the opening 30s of a 90s single episode. Story Spine is the sole structural template for Snowflake Step 2.

**Context:** Source: Kenn Adams, improvisation framework (1990s, "How to Create a Story Spine"); adapted by Ingermanson for Snowflake Method Step 2 (2002-2013). Phase 19 (SNOWFLAKE-01) integrates Story Spine as the structural template for Snowflake Step 2 paragraph expansion in the creative_source → screenplay pipeline. Three "disaster" sentences map to Snyder Midpoint + All Is Lost + Finale anchors (详见 [`creative_source/references/snowflake-method.md`](../creative_source/references/snowflake-method.md) §Snowflake-4 → Snyder 15-Beat Field Mapping).

### Premise Sentence / 一句话前提

**CN:** 一句话前提 — 雪花法 Step 1 的输出 artifact,≤ 30 字单句,必须包含 4 要素:主人公(who)+ 冲突(conflict)+ 目标(goal)+ 障碍(obstacle)。是整个雪花法展开链的起点 —— Step 2 paragraph 必须从 Step 1 premise 严格扩展,跳过 Step 1 直接写段落会引入结构性塌陷。在 Phase 19 中,Premise Sentence 的输入来自 StoryKernel `structural_formula`(50-200 字单句)的压缩 + StoryKernel `strata_layers[0].answer`(主导地层的"谁被规训 / 谁被豁免")的角色化转译。

**EN:** Premise Sentence — output artifact of Snowflake Method Step 1, a single sentence ≤ 30 chars that must contain four elements: protagonist (who) + conflict + goal + obstacle. It is the starting point of the entire Snowflake expansion chain — Step 2 paragraph must be strictly expanded from Step 1 premise; skipping Step 1 to write the paragraph directly introduces structural collapse. In Phase 19, the Premise Sentence input is derived from compressing StoryKernel `structural_formula` (50-200 char single sentence) + character-level translation of StoryKernel `strata_layers[0].answer` ("who is disciplined / who is exempt" from the dominant stratum).

**Context:** Source: Randy Ingermanson, Snowflake Method Step 1 (2002-2013). Phase 19 (SNOWFLAKE-01) defines Premise Sentence as the starting artifact of the Snowflake expansion chain. Canonical spec: [`creative_source/references/snowflake-method.md`](../creative_source/references/snowflake-method.md) §StoryKernel → Snowflake Bridge Protocol. 4-element requirement (protagonist/conflict/goal/obstacle) is the strict rule; missing any element fails Snowflake Step 1.

### Scene List / 场景列表

**CN:** 场景列表 — 雪花法 Step 8 的输出 artifact,每行 1 场景,含 4 字段:视角(POV character)+ 目标(scene goal)+ 冲突(scene conflict)+ 灾难(scene disaster)。是雪花法从幕级展开到场景级的过渡 artifact —— Step 7 完整角色表 → Step 8 场景列表 → Step 9 场景描述。在 Phase 19 的短剧适配中,Step 8 **不在 creative_source 跑** —— 而是延后到 screenplay 内部 Beat Planning 阶段产出,与 Snyder 15-beat 同构合并(避免双重产出场景表)。详见 [`creative_source/references/snowflake-method.md`](../creative_source/references/snowflake-method.md) §短剧 Step Scaling 延后项。

**EN:** Scene List — output artifact of Snowflake Method Step 8, one row per scene, containing 4 fields: POV character + scene goal + scene conflict + scene disaster. It is the transitional artifact where Snowflake expands from act-level to scene-level — Step 7 full character chart → Step 8 scene list → Step 9 scene descriptions. In Phase 19's 短剧 adaptation, Step 8 is **NOT executed in creative_source** — it is deferred to screenplay's internal Beat Planning stage, merged with Snyder 15-beat (to avoid double-producing scene tables). See [`creative_source/references/snowflake-method.md`](../creative_source/references/snowflake-method.md) §短剧 Step Scaling deferred items.

**Context:** Source: Randy Ingermanson, Snowflake Method Step 8 (2002-2013). Phase 19 (SNOWFLAKE-01 + SNOWFLAKE-03) places Scene List generation in screenplay's Beat Planning stage (not creative_source), as the merger point between Snowflake and Snyder 15-beat. The 4-field structure (POV/goal/conflict/disaster) aligns with McKee's scene value-shift rule (详见 [`screenplay/references/mckee-scene-design.md`](../screenplay/references/mckee-scene-design.md) §Value-Shift Rule).

---

**Phase 19 SNOWFLAKE-04 verification:** 4 / 4 new H3 entries added (Snowflake Method / Story Spine / Premise Sentence / Scene List), each with CN/EN/Context + Ingermanson 出处. SNOWFLAKE-04 PASS.
