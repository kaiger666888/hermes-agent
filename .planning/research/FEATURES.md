# Features Research — AI Short-Drama Skill Suite

**Domain:** AI short-drama (短剧 / 竖屏短剧) and micro-film (微电影) creation suite
**Researched:** 2026-06-15
**Overall confidence:** MEDIUM — built on codebase evidence + China short-drama industry knowledge (2024-2026); regulatory items have HIGH confidence from official sources cited inline; some 2026 platform-specific cuts are LOW until verified per-platform.

## Summary

The current 14-expert suite covers the **craft layer** of traditional film production (writing, drawing, animating, editing, color, sound, performance) but is missing the **language layer** (cinematography / 运镜), the **retention layer** (hook design + paid cliffhangers, the actual economic engine of 短剧), the **production-management layer** (casting, wardrobe, lighting, scheduling), and the **distribution-and-compliance layer** (中国 监管 + 平台规则 + 海报/trailer). This file categorizes every candidate capability for the 4 new experts and lists concrete knowledge gaps + named references for the 14 existing experts. Bilingual authoring pattern recommendation: keep EN for the YAML/metadata/coding-matrix schema and for English-canonical technical terms (LUT, L-cut, foley, Mise-en-scène), use CN for all narrative/descriptive prose, examples, refs, and any 短剧 cultural context that has no good English equivalent (钩子 / 卡点 / 爆款 / 完播率).

## Capability Areas

### 1. Cinematography / 运镜 (NEW — EXPERT-CINE)

The existing `scene_builder` covers *camera blocking feasibility* (where the camera can physically go) and `editor` covers *axis rule compliance at cut time*, but no expert owns the **camera language itself** — shot grammar, lens choice as narrative device, and movement vocabulary. This is the gap.

**Table stakes (must have for v1):**
- Shot size vocabulary (景别): ECU/CU/MCU/MS/MLS/WS/EWS with narrative intent mapping (e.g., ECU = emotional disclosure, WS = powerlessness / scale)
- Angle vocabulary (视角): eye-level, low (power), high (vulnerability), dutch/tilt (unease), overhead/god's-eye (fate), POV
- Composition systems: rule of thirds, golden ratio, center framing (symmetry = Wes Anderson / control), leading lines, headroom, nose-room, 180° / 30° rules
- Lens language: wide (24mm, distortion + intimacy), normal (35-50mm), tele (85-135mm, compression + voyeurism), anamorphic cues, focal length as emotion
- Camera movement vocabulary: static / pan / tilt / dolly / truck / pedestal / crane / handheld / steadicam / gimbal / whip-pan / zoom-in-(slow push)/zoom-out
- Match cut design (graphic match, action match, idea match — Eisensteinian)
- Mise-en-scène checklist (blocking, depth staging, foreground framing)
- 180° axis ownership (currently duplicated in editor — needs handoff boundary documented)
- Vertical-format (9:16) composition rules: safe zones for 抖音/快手 UI overlays, top-thirds for titles, bottom for captions, center-screen subject priority

**Differentiators (set this expert apart):**
- AI-native lens constraints: what focal lengths render reliably in current diffusion/video models (e.g., 35-85mm are robust; extreme wide/tele often break), `scene_builder` feasibility handoff
- "Camera move → prompt token" mapping for video gen models (Runway / Kling / Sora / Veo): dolly-in ↔ "slow push-in", handheld ↔ "shaky cam, documentary feel"
- Movement-emotion dictionary (slow push = realization, pull-out = abandonment, whip-pan = energy cut, static = dread) — pairs with `screenplay.emotion_curve` and `editor.FxRxT`
- Match-cut pre-planning that emits shot pairs to `screenplay` for setup and `editor` for transition marker
- Vertical vs horizontal framing co-design (cross-post to both 抖音 9:16 and B站 16:9)
- Director lens signatures table (Deakins long takes, Lubezki natural light wide, Kubrick symmetric center + zoom) feeding back into `style_genome` director profile

**Anti-features (explicitly do NOT build):**
- Real-time camera tracking / motion-control hardware integration — out of scope (pure skill + refs)
- Physical camera spec sheet generator (sensor size, codec, bitrate) — irrelevant to AI pipeline, leave to live-action tools
- VR / 360° / volumetric cinematography — different domain, separate project
- Re-implementing the 180° axis check that `editor` already owns — declare the handoff boundary instead (CINE owns *intent*, EDITOR owns *compliance*)
- Auto-blocking in 3D — that stays in `scene_builder`; CINE emits *intent*, scene_builder emits *feasibility*

**AI-specific concerns to address:**
- **Negative space asymmetry**: diffusion models tend to center subjects; CINE must override with explicit composition tokens
- **Lens distortion reliability**: wide-angle distortion often fails or over-fisheyes in current models — flag as risk
- **Movement continuity across cuts**: video gen produces per-clip; camera moves that span cuts (e.g., continuous dolly through edit) need pre-negotiated prompts
- **Match-cut feasibility**: AI models cannot reliably produce a graphic match across two independently generated clips — CINE must flag when match cuts need budget for multiple takes

---

### 2. Hook & Retention / 钩子设计 (NEW — EXPERT-HOOK, 短剧-specific)

This is the **economic engine** of 小程序剧 / 竖屏短剧. The existing `screenplay` has a vague "opening hook within first 3 seconds" rule and an emotion curve, but no structured retention craft. Without this expert, the suite produces *cinematically correct but commercially dead* content for the China 短剧 market.

**Table stakes (must have for v1):**
- 3-second hook taxonomy (情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩) with prompt templates for each
- Escalation pacing curve (阶梯式升级): each 30-60s segment must raise stakes, escalate conflict, introduce a new reversal
- 击中点 / 爽点 design — the moment of emotional payoff (打脸 / 反转 / 复仇 / 真相揭露 / 双向奔赴) and its placement rule
- 付费卡点 / cliffhanger placement (typically at episode-end of mini-program drama, ~90 sec mark for 抖音 single-episode)
- 完播率 (completion rate) optimization: 1.5x pace rule, every 10s a micro-hook, no >3s dead air
- 转发 (share) triggers: emotional resonance + social currency — relatable conflicts, status reveals, "send this to a friend who..."
- 留存 (retention) design: 下集预告 hook at end, 角色陪伴感 building
- 竖屏节奏: faster cut density than horizontal (research suggests 1.5-2x editor's `cuts_per_second` default)
- BGM-driven hooks: 配乐 drop / lyric-synced moments — pairs with `composer.coupled_beat`
- 字幕 design language (大字标题党 / 关键词加粗 / emoji-flavored captions)

**Differentiators (set this expert apart):**
- 爆款公式 (hit formulas) by platform:
  - 抖音剧: 男频 = 赘婿逆袭 / 战神归来 / 重生复仇; 女频 = 豪门虐恋 / 闺蜜背叛 / 替身白月光
  - 快手剧: more 草根 / 接地气, emotional realism > fantasy
  - 小程序剧 (WeChat / 独立 App): longer (1-3 min episodes), 付费卡点 at min 3-5 of 10 ep, higher ARPU tolerance for 大尺度 / 强冲突
- 付费率 optimization: 付费卡点 selection (which emotional peak to cliffhang), 付费节奏 (free first 5-10 episodes → first cliffhanger → daily release cadence)
- 击中点 density meter: counting 爽点 per minute (typical hit 短剧: 1 爽点 per 30-45s)
- Emotional curve extensions beyond `screenplay.emotion_curve`: 爽点 spike detection, 虐点 trough detection, 卡点 cliffhanger markers — output format compatible with `screenplay.emotion_curve` schema
- Reverse-engineering: given a reference爆款 clip, decompose its 钩子 structure into a template
- A/B variant generation: produce 2-3 hook variants for the same setup (different 钩子 type)
- Predictive metrics estimation (LOW confidence, mark as v2): rough regression from script features → predicted 完播率 / 转发率 / 付费率 bands

**Anti-features (explicitly do NOT build):**
- Actual metric measurement / platform API integration — out of scope, no platform data access
- Real-time bidding / ad placement inside content — different problem
- Audience demographic targeting beyond broad 男频/女频/老年向 splits — needs platform data, out of scope
- Plagiarism / 直接抄爆款 — provide structural templates, not literal copying (also 合规 risk)
- Auto-translating 爆款 across platforms without cultural adaptation — each platform has distinct audience norms

**Metrics this expert owns:**
- `hook_strength` (predicted 3-second retention probability, 0-1)
- `escalation_density` (爽点/minute)
- `cliffhanger_strength` (predicted 付费转化, 0-1)
- `pacing_variance` (rhythm diversity — flat = boring)

---

### 3. Production Management / 制作管理 (NEW — EXPERT-PROD)

Existing 14 experts are all **production-execution** (how to make a shot). None covers **production-management** (how to plan and resource the work). This expert fills that.

**Table stakes:**
- 选角 (casting) — character breakdown → actor type spec (age range / 体型 / 气质 / 表演特长); feeds `performer` for character consistency
- 服化道 (costume / makeup / props) — per-character wardrobe, makeup design (gender/age/era/职业), key props list
- 灯光 design plan (key/fill/rim per scene) — currently scattered in `scene_builder`; PROD owns the *intent*, scene_builder owns *execution*
- 拍摄计划 (shooting schedule) — shot list grouped by setup, day breakdown for live-action, scene-package breakdown for AI
- 资源调度 (resource scheduling) — GPU/render budget allocation across drawer/animator/scene_builder, asset reuse plan
- 统筹 (production coordination) — dependencies between experts, handoff checkpoints, blocking issues

**AI-relevant table stakes (subset that applies to AI pipeline):**
- 选角 for AI = **character LoRA / reference image spec** — feeds `performer.style_genome` and `drawer` for character consistency
- 服化道 for AI = **per-scene character wardrobe spec** (consistency across shots, feeds `continuity`)
- 灯光 intent = currently in `colorist.lighting_mood` + `scene_builder`; PROD unifies the *intent layer*
- 资源调度 for AI = **GPU/render budget allocation** (the most scarce resource in this pipeline)
- Asset reuse plan (which props/scenes/characters can be reused across shots/episodes — major cost saver)

**Live-action-only table stakes (lower v1 priority, mark for v2):**
- Real-world location scouting
- Crew roles (DP, gaffer, grip, sound mixer, script supervisor)
- Equipment rental / camera package
- Per-day call sheets, talent schedules, weather contingencies
- Insurance, permits, union rules

**Differentiators (set this expert apart):**
- AI-budget-aware scheduling: optimize shot order to minimize `drawer` / `animator` re-renders (most expensive ops); batch shots sharing the same scene package
- Character-LoRA cost estimation: each new character = LoRA training time + storage; advise on reuse vs new
- Wardrobe-change optimization: minimize costume changes within a shoot day (each change = re-prompt + re-render)
- Cross-episode asset amortization (esp. for 小程序剧 with 10-100 episodes): when to invest in reusable assets vs one-shot
- Render-farm / GPU-pool allocation model — though this may belong in a separate infrastructure concern; mark as edge

**Anti-features:**
- Real-world crew management — leave for live-action production software
- Real budgeting in money terms — too dependent on local rates; stick to *relative* cost (LoRA hours, GPU-hours, render-hours)
- Permit / insurance / legal entity — out of scope, belongs to compliance + business layer
- Re-implementing `scene_builder` asset pipeline — PROD owns *plan*, scene_builder owns *execution*

---

### 4. Compliance & Distribution / 合规与宣发 (NEW — EXPERT-COMPLI, China-specific)

This is a **hard regulatory requirement** for any 短剧 distributed in China as of 2026-04-01. Without this expert, the suite produces content that cannot legally be distributed. HIGH confidence on regulatory items.

**Table stakes (regulatory — HIGH confidence):**
- **AI 漫剧 (AI-generated manga-style drama) regulatory compliance** — as of 2026-04-01, 国家广电总局 requires 网络微短剧 classification and content review for AI-generated content; 备案号 required for any paid / broadcast distribution (verify exact scope, but direction is HIGH confidence)
- **广电总局 网络微短剧 备案** — 备案号 acquisition workflow, 所需材料清单, 分类标识 (重点/普通/其他), 时长 (≤30分钟 for 微短剧 category) and episode structure rules
- **网信办 生成合成内容标识 (《人工智能生成合成内容标识办法》, effective 2025-09-01)** — mandatory visible + invisible watermarking / metadata labeling for AI-generated content
- **先审后播 (review-before-broadcast)** for 小程序剧 platforms
- **平台规则差异** by platform:
  - 抖音 短剧: 短剧类目准入, 内容审核标准, 流量分级
  - 快手 短剧: 类似但审核尺度略宽 (verify current)
  - 微信小程序剧: 备案要求更严, 付费机制限制
  - B站 / 小红书 / 微博: 各有规则
- **内容审核 红线** (universal): 涉政 / 涉黄 / 涉暴 / 涉赌 / 民族宗教 / 未成年人保护 / 虚假宣传 / 不良价值观 — concrete checklist
- **未成年人保护**: 不得诱导未成年消费, 适龄提示
- **付费合规**: 收费公示, 自动续费规则, 退款政策

**Table stakes (宣发 — distribution support):**
- 海报 (poster) generation spec — feeds `drawer` for static key-art output
- Trailer / 片花 generation spec — feeds `editor` for 15-30s cut
- 平台裁剪 (platform tailoring): 抖音版 / 快手版 / 小程序剧版 differences in length, hook placement, 卡点 position
- 标题党 / 副标题 / 封面文案 patterns
- 关键词 SEO for 平台 search

**Differentiators:**
- **AI 漫剧专项合规 checklist** — since AI 漫剧 is a newly regulated category (2026), few tools explicitly handle this; explicit compliance advisor is a real differentiator
- **平台差异化合规矩阵** — single source of truth for what's allowed on each platform
- **爆款元素识别 + 合规避险** dual analysis: which 爆款 elements are also 合规 risk (大尺度 / 强冲突 often overlaps with 审核风险)
- **付费卡点 + 付费合规 co-design** with `EXPERT-HOOK`: where the cliffhanger is legal to charge for
- **AI-content 标识 automation** — generate the required watermarking / metadata / visible labels spec
- **备案材料自动生成** — draft 备案 application docs from `script.json`
- **审核预检 (pre-review)** — LLM-based 预审 that flags potential 红线 issues before submission (HIGH value, reduces rejection rate)
- **降级方案** — if content is rejected, what to cut / modify to pass without losing core 爆款 value

**Anti-features:**
- **法律咨询 / 替代律师** — explicit disclaimer: this is a checklist tool, not legal advice; complex cases need actual lawyers
- **代备案服务** — out of scope, that's a service business
- **跨平台自动分发** (auto-upload) — out of scope (API complexity + 平台 TOS)
- **追踪平台规则变更的实时更新** — v1 uses manually curated knowledge base; real-time monitoring is v2+
- **规避监管** — explicitly support compliance, never *circumvent* (this is also a safety/ethical line)

**Critical risk note:** 2026 AI 漫剧 regulation is **new and evolving**. Rules may change quarterly. All refs MUST have a "verified as of YYYY-MM-DD" stamp and a refresh cadence (recommend quarterly audit).

---

### 5. Existing 14 Expert Enhancement Opportunities (RAG refs)

For each existing expert, the gap is the same: **prompt describes mechanism (how to do X) but lacks industry experience (what good X actually looks like)**. RAG refs should be hand-curated markdown distillations of authoritative sources.

| Expert | Knowledge Gaps (concrete) | Suggested Refs (named) | Priority |
|--------|---------------------------|------------------------|----------|
| **screenplay** | Currently cites "Hauge compression" without source; no Save the Cat / McKee / 短剧-specific beat sheet; no dialogue craft references | *Save the Cat!* (Snyder), *Story* (McKee), *The Foundations of Screenwriting* (Field), 短剧 beat sheet (3秒钩子 + 每30秒一击中点), 《故事》翻译版, 拆解 100 部爆款短剧 beat 模板 | **High** |
| **drawer** | Style references are abstract; no concrete cinematographer/illustrator reference library; no model-specific prompt patterns | Cinematographer reference set (Deakins / Lubezki / Khondji shot libraries), Studio Ghibli color scripts, 当前 diffusion 模型 prompt 工程实践 (Perlin noise / negative prompts / ControlNet refs), 短剧封面美学 (大字 / 高对比 / 强冲突) | High |
| **animator** | No animation principles reference; no Disney 12 principles; no motion-library; no current video-gen-model behavior notes | Disney 12 Principles of Animation (Johnston & Thomas), *The Animator's Survival Kit* (Williams), 当前 video gen models (Runway Gen-3 / Kling / Veo / Sora) behavior notes (运动幅度 / 一致性 / 多镜头), 12帧循环 vs 24帧 | High |
| **editor** | Cites 180° rule + L/J-cut but no montage theory; no Pudovkin / Eisenstein; no 短剧-specific cut rate data | *The Technique of Film Editing* (Reisz & Millar), Eisenstein montage essays, Pudovkin constructive editing, Walter Murch *In the Blink of an Eye* (Rule of Six), 短剧平均切镜频率 (1.5-2x 横屏剧), 抖音爆款平均镜头时长数据 | **High** |
| **colorist** | Has 28 color combos but no famous-film LUT case studies; no 色彩心理学 system; no 调色软件实操 | *If It's Purple, Someone's Gonna Die* (Bellantoni) — color-psychology classic, *Color Correction Look Book* (Hurkman), DaVinci Resolve 调色节点实践, 经典影片 LUT 案例库 (Blade Runner 2049 orange-cyan, Mad Max desert, Moonlight blue-night), 色彩心理学跨文化差异 (中国 vs 西方 颜色含义) | **High** |
| **composer** | Has coupled_beat concept but no film scoring theory; no theme/leitmotif craft; no genre score conventions | *On the Track* (Karlin & Wright), *The Complete Guide to Game Audio* (scope overlap), film composer case studies (Zimmer / Williams / Reznor), 短剧 BGM 公式 (情绪堆叠 / 静默-爆发 / 经典曲改编), 版权音乐 vs 原创 tradeoffs | Medium |
| **performer** | Has ExBxSxP matrix but no acting theory; no Meisner / Stanislavski; no 表演 in 短剧 context (夸张 vs 收敛) | *An Actor Prepares* (Stanislavski), Meisner technique, *Respect for Acting* (Hagen), 短剧表演特点 (情绪外放 / 微表情特写适配竖屏 / 配音 vs 同期), AI 数字人表演约束 (uncanny valley / 微表情生成限制) | Medium |
| **scene_builder** | Has FxSxA matrix but no Mise-en-scène theory; no real production design references | *Mise-en-scène* analyses (Gibbs), production design case studies (蛋头先生 / 韦斯·安德森对称美学), 3D 场景资产库 (SketchFab / Poly Haven 公开素材), Blender 场景搭建最佳实践 | Medium |
| **foley** | Has 7D system but no actual foley art reference; no sound design theory | *The Sound Effects Bible* (Viers), *Audio-Vision* (Chion), classic foley case studies (Star Wars lightsaber / Jurassic breath), 拟音师工作流 ( Foley vs hard effects vs design ), 公开音效素材库 (Freesound / BBC Sound Effects) | Medium |
| **spatial_audio** | No spatial audio theory; no Dolby Atmos case studies; no immersive audio reference | Dolby Atmos music/film guidelines, *Immersive Sound* (Rumsey), Ambisonics theory, VR/360 audio case studies, headphones-vs-speakers mixing tradeoffs | Low (specialized) |
| **mixer** | Has LUFS targets but no mixing craft theory; no genre mix conventions | *Mixing Secrets for the Small Studio* (Senior), *The Mixing Engineer's Handbook* (Owsinski), 平台 loudness 规范 (Spotify -14 LUFS / 抖音 / Apple Music), 对白混音清晰度优先级 (短剧对白 > BGM > 拟音) | Medium |
| **voicer** | No voice direction theory; no casting-for-voice principles; no TTS model-specific notes | *Voice-Over Voice Actor* (Yousefian & Crum), 配音导演工作流, 当前 TTS / voice cloning 模型 (ElevenLabs / CosyVoice / GPT-SoVITS) 行为与边界, 短剧配音特点 (情绪激烈 / 语速快 / 方言加成) | Medium |
| **continuity** | Has deviation detection but no script supervisor craft reference | *The Film Director's Team* (script supervisory chapter), script supervisor workflow ( lined script / facing pages / continuity report ), 短剧连续性挑战 (多集角色一致性 / 服装记忆 / 道具追踪) | Medium |
| **style_genome** | Has director archive (5 names) but tiny; no genre conventions library; no blending case studies | 扩充导演档案库 to 30-50 名 (东西方兼顾: 王家卫 / 张艺谋 / 是枝裕和 / 奉俊昊 + Nolan / Villeneuve / Fincher / Anderson), 类型片风格基因 (科幻 / 古装 / 都市 / 武侠 / 短剧特有的"爽剧风"), 跨导演混搭案例 (Blade Runner 2049 = Villeneuve × Deakins × sci-fi) | **High** |

**Cross-cutting gaps to address in multiple experts:**
- **短剧-specific data** is universally thin — most existing knowledge is feature-film-oriented. Need 短剧-pacing / 短剧-color / 短剧-cut-rate empirical data refs.
- **AI generation model behavior notes** are needed across drawer/animator/voicer — what current models do well/poorly, prompt patterns that work, failure modes.
- **Cross-cultural color/sound meaning** — current 28-color system and emotion mappings are Western-leaning; need Chinese audience variations (e.g., 红色 in China = 喜庆/吉利, in Western thriller = 危险/血腥).

---

### 6. Bilingual Authoring Patterns

**Recommendation:** **EN structure + CN descriptive prose + mixed-language technical vocabulary.** This is the pattern already emerging in existing SKILL.md files (e.g., "Screenplay Expert (剧本专家)" as title, EN description, but capable of CN operation).

**Table stakes for bilingual SKILL.md:**

| Layer | Language | Why |
|-------|----------|-----|
| YAML frontmatter (name, description, tags) | EN | Hermes ecosystem convention, English-only tooling parses it |
| `metadata.hermes.*` (expert_id, metrics, related_skills) | EN (snake_case identifiers) | Machine-readable keys |
| Coding matrix names (FxRxT, CxSxZ, ExBxSxP) | EN abbreviations + CN gloss in parenthesis once | Concise + accessible |
| Section headers (## Role, ## Workflow, ## What NOT to do) | EN | Consistency across suite, English-first community |
| Body prose (philosophy, explanations) | EN primary + CN where cultural context warrants | EN for global readability, CN for 短剧 cultural specifics |
| Examples | **CN primary** (target market is China) | Examples must reflect actual 短剧 language |
| `references/*.md` | **CN primary**, key terms in EN | Source material is mostly Chinese (短剧 industry, China regulatory docs) |
| Forbidden patterns / prohibitions | EN with CN-specific items in CN | EN base + local nuance |

**When EN makes sense (use English):**
- Technical terms with no good Chinese equivalent or where EN is canonical: LUT, foley, L-cut, J-cut, Mise-en-scène, key/fill/rim light, ControlNet, LoRA, HDRI, PBR
- Coding-matrix dimension names where abbreviation is standard: F (Frame), R (Rhythm), T (Transition), CxSxZ
- Tool / framework / model names: Blender, DaVinci Resolve, ElevenLabs, Runway, Kling
- Metadata, identifiers, machine-readable fields

**When CN makes sense (use Chinese):**
- 短剧 cultural concepts with no good EN equivalent: 钩子 (hook is a weak translation — 短剧钩子 is denser), 卡点 (literally "card point" — meaning paid cliffhanger, no EN term), 爆款, 击中点, 完播率, 转化率, 爽点, 虐点, 男频, 女频, 赘婿, 战神, 替身, 白月光, 复仇, 反转, 打脸
- Regulatory terms: 备案号, 先审后播, 网络微短剧, 网信办, 广电总局, 内容审核, 红线, 未成年人保护, 适龄提示
- All descriptive prose, narrative examples, refs sourced from Chinese-language material
- Cultural context where English translation loses meaning (e.g., explaining why 赘婿 genre works in China)

**Anti-pattern (do NOT do):**
- **Fully translating everything to EN** — loses 短剧 cultural specificity and reads unnaturally
- **Fully translating everything to CN** — breaks Hermes ecosystem compatibility, harder for English-only contributors
- **Mixing languages mid-sentence randomly** — apply consistent layer-based rules
- **Translating 短剧-specific terms to literal EN** ("赘婿" → "live-in son-in-law" loses the cultural resonance) — keep CN + parenthetical gloss on first use

**Layered template recommendation:**
```markdown
---
name: cinematographer  # EN
description: "..."  # EN
metadata:
  hermes:
    tags: [...]  # EN
    expert_id: cinematographer  # EN
---

# Cinematographer Expert (运镜专家 / 摄影指导)

[EN opening paragraph: what this expert does, why it exists]

## Role & Philosophy (角色与理念)

[CN paragraph: industry context — why 镜头语言 matters for 短剧 specifically]

## Core Capabilities (核心能力)

[EN bullets with CN examples inline]

## Example: 钩子镜头设计 (Hook Shot Design)

[CN example block, terms in CN, technical specs in EN notation]

## References

- [CN-language refs in CN]
- [EN-language refs in EN]
```

---

## Feature Dependencies

```
EXPERT-COMPLI (compliance gate, can reject script)
  ↓ blocks
EXPERT-HOOK (needs approved script)
  ↓ feeds
screenplay (gets 爽点 / 卡点 / 钩子 markers in emotion_curve)
  ↓
EXPERT-CINE (camera language for each shot, given emotional intent)
  ↓
scene_builder (camera feasibility check on CINE intent)
editor (axis check on CINE output)
  ↓
[drawer/animator/colorist/composer pipeline]

EXPERT-PROD (parallel, plans resources for all of above)
```

**Key handoffs to design:**
- `EXPERT-CINE` → `scene_builder`: CINE emits camera *intent* (lens, move, framing); scene_builder emits *feasibility* (can the 3D scene support this) → loopback if infeasible
- `EXPERT-CINE` → `editor`: CINE emits shot grammar; editor uses for cut decisions and axis check (the existing 180° check in editor must declare CINE as upstream owner of axis *intent*)
- `EXPERT-HOOK` → `screenplay`: HOOK emits 钩子/爽点/卡点 markers that screenplay must encode into `emotion_curve[]` (extend schema)
- `EXPERT-HOOK` ↔ `EXPERT-COMPLI`: cliffhanger placement must satisfy 付费合规 (some 卡点 cannot legally be paywalls)
- `EXPERT-PROD` ↔ all: bidirectional — PROD plans based on all experts' outputs, all experts may flag resource conflicts back to PROD
- `EXPERT-COMPLI` is the **gate** — runs first (preliminary) and last (final pre-distribution check)

## MVP Recommendation

**v1 priority (build first):**
1. `EXPERT-COMPLI` (regulatory blocker — without this, nothing ships legally)
2. `EXPERT-HOOK` (commercial engine — without this, 短剧 content is dead on arrival)
3. RAG enhancement for `screenplay`, `editor`, `colorist`, `style_genome` (4 highest-impact existing experts)
4. `EXPERT-CINE` (camera language — needed for craft quality but not a blocker)

**Defer to v1.5 / v2:**
- `EXPERT-PROD` (production management — more value for studios scaling output; for early v1 the user can hand-coordinate)
- RAG for low-priority existing experts (`spatial_audio`, `continuity`, `foley` — specialized, lower leverage)
- Predictive metric estimation in HOOK (needs platform data, mark as future)
- Live-action-only features in PROD

**Anti-feature for v1:**
- Automated 平台 API integration (TOS + complexity risk)
- Real-time regulatory monitoring (quarterly manual audit is sufficient)
- Cross-platform auto-distribution

## Open Questions

- **Q1 (HIGH priority)**: 2026-04-01 AI 漫剧 regulatory specifics — what exactly triggers 备案? Threshold (revenue / episode count / platform)? Need to verify against current 广电总局 notices.
- **Q2 (MEDIUM)**: 短剧 pacing data — is "1.5-2x horizontal cut rate" actually backed by empirical studies, or is it industry folklore? Need real benchmarks from 抖音 爆款.
- **Q3 (MEDIUM)**: Current video gen model behavior — what focal lengths / camera moves do Runway Gen-3 / Kling / Veo / Sora reliably support as of 2026-06? Affects what `EXPERT-CINE` can recommend.
- **Q4 (LOW)**: Cross-platform 合规 matrix accuracy — are 抖音 / 快手 / 微信小程序 rules stable enough to encode, or do they shift monthly?
- **Q5 (LOW)**: Should `EXPERT-HOOK` predict metrics or only *structure* hooks? Prediction needs validation data; structure is safer for v1.
- **Q6 (LOW)**: Bilingual refs copyright — Chinese 短剧 case studies are largely paywalled / proprietary; how much can be quoted under fair use vs needs original distillation?

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Cinematography capabilities | HIGH | Established film craft, stable knowledge |
| Hook & Retention capabilities | MEDIUM | 短剧 industry knowledge is real but fast-moving |
| Compliance (regulatory existence) | HIGH | Official Chinese government sources |
| Compliance (specific thresholds) | MEDIUM | New 2026 AI 漫剧 rules, details still emerging |
| Production Management | HIGH for craft / LOW for live-action specifics | Live-action is large domain, v1 focuses on AI-relevant subset |
| Existing expert enhancement | MEDIUM-HIGH | Gaps are clear; specific book refs are HIGH confidence |
| Bilingual pattern | HIGH | Pattern already emerging in codebase |

## Sources

- **Codebase evidence (HIGH)**: `/data/workspace/hermes-agent/skills/movie-experts/{screenplay,editor,colorist,scene_builder,style_genome}/SKILL.md`
- **Project requirements (HIGH)**: `/data/workspace/hermes-agent/.planning/PROJECT.md`
- **Chinese 短剧 industry knowledge (MEDIUM)**: General industry awareness 2024-2026 of 抖音剧 / 快手剧 / 小程序剧 ecosystem; 爆款公式 widely documented in industry media
- **Regulatory (HIGH for existence, MEDIUM for specifics)**: 国家广电总局 微短剧 备案 framework (well-established); 网信办 《人工智能生成合成内容标识办法》 effective 2025-09-01 (verifiable official source); 2026 AI 漫剧 regulation newly in force — verify exact provisions against current official notices during implementation
- **Film craft references (HIGH)**: All cited books (Save the Cat, Story, In the Blink of an Eye, Animator's Survival Kit, Sound Effects Bible, etc.) are well-known canonical works in their domains
- **Gaps**: No WebSearch performed (time-boxed). Some specific 2026 platform rule details and current video-gen-model behavior specs should be verified with WebSearch during phase-specific research.
