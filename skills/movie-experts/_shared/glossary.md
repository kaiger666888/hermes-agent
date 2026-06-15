# Glossary — Movie-Experts Suite v2

**Purpose:** Canonical EN↔CN term dictionary for the Movie-Experts Suite. Every expert's SKILL.md and `references/*.md` MUST use these terms consistently. Drift in translation breaks downstream metric comparability and judge-prompt reliability.

**Last updated:** 2026-06-15 (Phase 0 skeleton — 24 entries)
**Refresh cadence:** Phase 1+ adds terms as each new expert requires them; Phase 6 does a full consistency pass.

---

## How to use this glossary

1. **Authoring SKILL.md / refs:** When you write 短剧-specific terms, look them up here first. If a term exists, use the canonical CN form. If not, add it here with a bilingual definition + context note.
2. **Cross-expert signals:** When one expert emits a term (e.g., screenplay emits `钩子`), downstream experts (editor, composer) MUST consume the same CN token, not an ad-hoc English translation.
3. **LLM-as-judge prompts:** Judge prompts reference these terms by their CN form for 短剧-specific evaluation anchors. Bilingual definitions prevent judge-model misreading.

---

## Core terms (SC #5 required + extended)

### 运镜 / cinematography / camera movement
**CN:** 运镜 — 摄影机移动方式的统称,包括推拉摇移升降跟。
**EN:** The collective term for camera movement techniques (dolly, pan, tilt, crane, tracking, handheld).
**Context:** Used by EXPERT-CINE (Phase 4) and references `animator.camera_type`. Distinguished from 景别 (shot size) and 视角 (angle).

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
**Context:** Distinct from 爽点 (satisfaction) — 击中点 can be sad / bitter / nostalgic / cathartic. composer aligns musical sting to 击中点.

### 镜头语言 / shot grammar / cinematic language
**CN:** 镜头语言 — 通过镜头选择(景别、视角、运动、构图)传递意义的系统化表达方式。
**EN:** Shot grammar — systematic expression of meaning through lens choices (shot size, angle, movement, composition).
**Context:** EXPERT-CINE (Phase 4) owns 镜头语言 semantics; scene_builder owns spatial geometry; animator owns motion execution.

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
**Context:** editor enforces 180° axis compliance (zero-tolerance metric). EXPERT-CINE documents the rule; scene_builder pre-computes axis data.

### 调度 / blocking / staging
**CN:** 调度 — 演员在场景空间中的位置安排与移动路径设计。
**EN:** Blocking / staging — arrangement and movement paths of actors within the scene space.
**Context:** performer outputs stage positions (S dimension); scene_builder validates spatial feasibility; EXPERT-CINE consumes for camera-blocking design.

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
**Context:** screenplay branches narrative POV by 男频/女频; performer adjusts body-language intensity accordingly.

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
