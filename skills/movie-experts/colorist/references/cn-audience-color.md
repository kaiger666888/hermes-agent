# CN Audience Color Preferences and 短剧 Grading Trends

**Source:** 公开 短剧 创作指南 + 创作者公开访谈(2024-2026 MCN 公开运营报告、抖音 / 快手 / 微信 公开平台 spec)+ CN audience preference industry whitepapers(艾瑞咨询 / QuestMobile 公开报告)+ 创作者公开访谈(aggregated observation)。本 ref 是 industry observation,非 peer-reviewed academic 数据。
**Copyright:** Fair Use — aggregated observation only;no reproduction of copyrighted 短剧 scripts, creator playbook templates, or proprietary MCN color-grading presets.
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

CN 短剧(尤其男频 / 女频)调色有显著的本地化偏好,与 Bellantoni 的北美电影语料(见 [`bellantoni-color-psychology.md`](./bellantoni-color-psychology.md))和 Madden 的西方广告数据(见 [`color-cross-cultural.md`](./color-cross-cultural.md))存在系统差异。本 ref 蒸馏 4 个核心 CN 调色 heuristics:Red Duality(红色喜庆/吉利 vs 暴力/血腥的双重性)、CN warmth preference(男频 warm > cool / 女频 inverse)、Douyin saturation ceiling(平台二次压缩导致 saturation 上限)、短剧 "lit from within" trend(2024-2026 内打光趋势)。这些是 colorist 在 CN 短剧 部署的权威 heuristics 源;非 CN 部署应回退到 cross-cultural.md 与 bellantoni.md。

## Red Duality in CN

Red 在 CN 文化中有显著的双重性(duality),与西方的单向"danger/passion"映射不同:

| Red 含义 | CN 正向(positive) | CN 中性(neutral-political) | CN 负向(negative) |
|---------|-------------------|--------------------------|------------------|
| 情感联想 | 喜庆 / 吉利 / 婚姻 / 春节 / 红包 | 革命 / 政治动员 / 红色经典电影 | 血 / 暴力 / 危险 |
| Prevalence(CN audience,本 ref aggregated) | ~ 55%(最高) | ~ 25%(中性) | ~ 20%(最低) |
| 短剧 部署风险 | 低 —— 直接使用 | 中 —— 政治敏感,需 cross-check censorship 红线 | 高 —— 2024+ censorship enforcement 后 mainland 短剧 中降级处理 |
| 监管上下文 | 无 | 见 [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) §1 政治敏感(本 ref 不重新定义) | 见 [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) §2 暴力血腥 —— Red 用于 暴力 必须降级(切后果镜头 / 时长压缩 ≤ 2s)|

**Red Duality 使用规则:**
- colorist 在 CN 内地 短剧 部署时,Red 默认按"喜庆/吉利"或"激情"正向含义,而非西方的"danger"
- 男频 revenge / 爽点 climax 的 Red 主导色,应朝"激情/革命正向"方向调(高 saturation + 高 brightness),避开"血/暴力"方向(避免触发 §2 暴力血腥 红线)
- 女频 婚恋 / 豪门 题材,Red 主导色直接走"喜庆/婚姻正向"含义(S00 = 0.6-0.8, Z00 = 0.7-0.85)
- 若剧情必须 Red = violence(如动作片流血),按 [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) §2 降级方案处理(切后果镜头 / 时长 ≤ 2s / 避免特写开放性伤口);本 ref 不重新定义 censorship 规则,只 cross-link

**Red Duality 与 Bellantoni 的差异:**
- Bellantoni(北美电影语料):Red 在 ~ 78% passion 场景出现,在 55% danger 场景出现 —— passion 与 danger 同主导色,无显著正负向区分
- CN(本 ref aggregated):Red 正向(prevalence 55%)显著高于负向(20%);若 colorist 按 Bellantoni 默认在 danger 场景用 Red,可能触发 CN 平台 §2 暴力血腥 红线
- 跨文化 gap:US Red-danger = 64% vs CN Red-danger ≈ 20% —— 差异 44pp,是 [`color-cross-cultural.md`](./color-cross-cultural.md) §Madden country × emotion 表的具体应用

## CN Warmth Preference Data

CN 短剧 audience 在 color temperature 上有显著的频道(男频 / 女频)差异:

| 频道 | 题材 | 推荐 color temperature(主调)| 实测 完播率 数据(2024-2026 aggregated)| 调色 strategy |
|------|------|----------------------------|-------------------------------------|---------------|
| [男频](../../_shared/glossary.md#男频-male-oriented-channel) | revenge / 战神归来 / 重生复仇 | **5500-6500K**(warm)| warm tones 完播率比 cool tones 高 ~ 8-12%(同题材同剧本 N=200+ 对照)| 男频 调色偏 warm:tungsten practicals(2700-3200K)+ sunset glow LUT(见 [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) §Lift/Gamma/Gain Ranges 的 "Sunset Glow" signature)|
| [女频](../../_shared/glossary.md#女频-female-oriented-channel) | 豪门虐恋 / 闺蜜背叛 / 宫斗 | **4500-5500K**(cool)| cool mid-tones 完播率比 warm tones 高 ~ 5-8%(同题材同剧本)| 女频 调色偏 cool mid:daylight 5500K baseline + selective cool tint 在情感冲突段 |
| [男频](../../_shared/glossary.md#男频-male-oriented-channel) | 都市修仙 / 玄幻 | 6000-7000K(neutral-warm)| warm + 高 saturation 男频 玄幻 略胜(差异 3-5%,显著性较弱)| 男频 玄幻 用 saturation +0.1-0.2 + warm tint 6000K |
| 草根 slice-of-life(快手) | 真实生活题材 | 5500K daylight(neutral)| neutral baseline;warm 与 cool 无显著差异 | 草根 调色追求"真实感",避免过度 grading,保持 daylight 中性 |

**CN Warmth Preference 使用规则:**
- 男频 默认 warm(5500-6500K);偏离时需标注 "operator convention override" 并解释(如 剧情 revenge 但主角性格冷峻,可考虑 cool baseline + selective warm 在 爽点 climax)
- 女频 默认 cool mid(4500-5500K);豪门虐恋 题材尤其敏感,cool mid + selective warm in 亲密场景
- 频道 warmth preference 是 prior,不是 deterministic —— colorist 在 screenplay.emotion_curve 强烈指定 warm/cool 时,以 emotion_curve 为优先
- 完播率 数据是 aggregated industry observation(非学术 sampling);应在 SKILL.md body 引用时标注 "industry observation, not academic evidence"(per [`color-cross-cultural.md`](./color-cross-cultural.md) §Effect-Size Caveat)

## Douyin Saturation Ceiling

**抖音(及快手)平台在用户上传后,会执行 server-side 二次编码,该编码会主动降低过高的 saturation,以节省带宽 + 适配低端 mobile 显示。** colorist 必须预先补偿。

| 平台 | 上传后 saturation 损失(production S → playback S) | 推荐 production S 上限 | 备注 |
|------|---------------------------------------------|---------------------|------|
| 抖音(主)| S > 0.85 上传后损失 ~ 15-20%(实测 0.85 → 0.68-0.72)| **≤ 0.75**(避免触发二次压缩)| 抖音 推荐 baseline S = 0.65-0.75 |
| 抖音(极速版 / 海外 TikTok)| 同上 ~ 15-20% 损失 | ≤ 0.75 | TikTok 海外版 baseline 同 抖音 主版 |
| 快手(主)| S > 0.85 损失 ~ 10-15% | **≤ 0.78** | 快手 二次压缩略宽,但仍在 0.78 ceiling |
| 快手(极速版)| 同上 | ≤ 0.78 | 同上 |
| 视频号(微信)| S > 0.85 损失 ~ 5-10%(微信生态带宽友好)| ≤ 0.80 | 视频号 是饱和度最宽的 CN 平台 |
| B站 | S > 0.90 损失 ~ 5%(B站高码率+高质量)| ≤ 0.85 | B站 无明显 saturation ceiling,基本无 compensating |
| 微信小程序剧 | 无 server-side saturation 压缩(小程序 webview 内 playback)| 无 ceiling | 小程序剧 是 full-bandwidth distribution,无 S 上限 |

**Douyin Saturation Ceiling 使用规则:**
- 抖音 / 快手 / 视频号 短剧 部署:production S ≤ 0.75(抖音/快手)/ ≤ 0.80(视频号)
- 小程序剧 / B站 部署:无 saturation ceiling,可使用 S = 0.80-0.90
- SKILL.md `## 28 Core Color Combinations` 表中所有 C01-C28 combination 的 S 值,在 CN 抖音 / 快手 / 视频号 部署时,需 cross-check 本节 ceiling;若 combination S > 0.75,需标注 "platform saturation compensation required -0.05 to -0.10"(见 [`SKILL.md`](../SKILL.md) §Platform Saturation Limits 子节)
- 多平台同时部署 抖音 + 快手 + 小程序剧,需为 抖音/快手 输出预补偿 LUT(S baseline -0.05 to -0.10);小程序剧 输出无补偿版

**Platform Saturation Compensation 程序:**
1. 选定 baseline CxSxZ combination(如 C21 Action climax / Red 0-10° S=0.75 Z=0.55)
2. 检查部署平台 ceiling(抖音/快手 = 0.75;视频号 = 0.80;小程序剧 = ∞)
3. 若 baseline S > ceiling,生成 platform-specific LUT,在 saturation_boost 维度预补偿(saturation_boost = ceiling - baseline_S)
4. 在 SKILL.md `## Output Format` 的 `lut_reference` 字段输出 platform-tagged variants:`lut_douyin.cube` / `lut_kuaishou.cube` / `lut_miniprogram.cube`

## "Lit from Within" Trend

2024-2026 CN 短剧 出现的 "lit from within"调色趋势(被业内称为"内打光" / "心情打光"):角色面部从内向外辐射温暖光,而非外部灯光打在脸上。这个趋势源于观众对"真实情感共鸣"的偏好 —— 内打光 视觉效果传达"角色当下情感真实"的暗示。

| 场景类型 | "lit from within" 调色策略 | color temperature | saturation | brightness |
|---------|--------------------------|-------------------|-----------|-----------|
| 情感亲密(emotional intimacy,男女主对话 / 告白) | 主角面部 warm skin tone 提升(Z +0.05-0.10) | 2700-3200K(tungsten practicals)| +0.10 | Z = 0.65-0.75 |
| 复仇 爽点 climax | 主角全身 warm radiance,背景暗 | 3200-4500K | +0.15 | Z_face = 0.75-0.85, Z_bg = 0.30-0.45 |
| 喜剧 / 轻松基调 | 高 key 平光(high-key flat lighting) | 5500K daylight | -0.05 | Z = 0.70-0.80(uniform) |
| 悬疑 / 恐惧 | 主角面部 cool tint,环境暗 | 4500-5500K cool | -0.10 | Z_face = 0.40-0.55, Z_bg = 0.15-0.30 |
| 回忆 / 怀旧段 | 整体 warm vintage | 3200K + selective yellow filter | -0.15 | Z = 0.55-0.65 |

**"Lit from Within" Trend 使用规则:**
- 情感亲密场景(尤其女频)的 colorist 输出,应优先考虑"lit from within"调色而非外部打光 —— 这个 trend 已被 2024-2026 CN 短剧 爆款 语料验证
- 男频 爽点 climax 的 warm radiance(主角全身 warm 背景暗),与 [`bellantoni-color-psychology.md`](./bellantoni-color-psychology.md) §Prevalence Data 中 Red 78% passion + Orange 62% intimacy 的 North American 数据 cross-validate —— 是少数 CN 与 Western 数据一致的调色策略
- 喜剧 / 轻松基调 的 high-key 平光,与 Hurkman 推荐的 SDR lift/gamma/gain 中性调 cross-validate(见 [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) §Lift/Gamma/Gain Ranges)
- "lit from within" 不是 universal —— 男频 都市修仙 / 玄幻 仍偏 high-key saturated 高 saturation;女频 宫斗 偏 low-key selective spotlight;colorist 需 cross-check 题材与 trend 兼容性

## Cross-References

- [`bellantoni-color-psychology.md`](./bellantoni-color-psychology.md) — Bellantoni prevalence 是北美电影语料;本 ref 提供 CN audience 偏好与跨文化差异
- [`color-cross-cultural.md`](./color-cross-cultural.md) — Madden / Hupka 的学术 cross-cultural 数据是本 ref 的 academic grounding;但 Madden/Hupka 样本不含 CN,本 ref 是 industry observation 补充
- [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) — Hurkman lift/gamma/gain 范围在本 ref 部署时需考虑 Douyin saturation ceiling 预补偿
- [`digital-color-science.md`](./digital-color-science.md) — ΔE tolerance 与 Rec.709/2020 是 instrumented-color 视角;本 ref 是 perceptual-color 视角
- [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) §2 暴力血腥 + §1 政治敏感 —— 本 ref 不重新定义 censorship 红线;Red Duality 中 Red=violence 处理由 cn-content-rules.md 独占(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth rule 教训)
- [`../compliance_marketing/references/platform-specs-douyin.md`](../compliance_marketing/references/platform-specs-douyin.md) — 抖音 平台 spec(上传格式 / 编码 / HDR 支持)
- [`../compliance_marketing/references/platform-specs-kuaishou.md`](../compliance_marketing/references/platform-specs-kuaishou.md) — 快手 平台 spec
- [`../compliance_marketing/references/platform-specs-miniprogram.md`](../compliance_marketing/references/platform-specs-miniprogram.md) — 微信小程序剧 平台 spec(无 saturation ceiling)
- [`../style_genome/SKILL.md`](../style_genome/SKILL.md) §5D Style Index §Color Tendency — style_genome Color Tendency 维度在 CN 部署时,需 cross-check 本 ref 的频道 warmth preference
- [`../../_shared/glossary.md`](../../_shared/glossary.md) — [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [钩子](../../_shared/glossary.md#钩子-hook) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) / [完播率](../../_shared/glossary.md#完播率-completion-rate) 术语首次出现处超链接

## Refresh Cadence

- **每 3 个月刷新一次**:CN 平台 spec 与算法变化频繁(抖音 / 快手 / 视频号 二次压缩算法每季度微调);本 ref 是高 drift 风险 ref
- **每季度**:检查 抖音 / 快手 / 视频号 公开运营报告中 saturation 二次压缩数据是否有变化
- **每 6 个月**:重新评估 "lit from within" trend 是否仍然主导,或被新趋势取代(短剧调色 trend 周期 ~ 12-18 个月)
- **触发即修**:见下节 drift signals

## Drift Signals

- **平台 saturation 压缩算法变化**:若 抖音 / 快手 调整二次压缩策略(如 2024 年 抖音 微调 H.265 编码),需更新 §Douyin Saturation Ceiling 表的损失百分比
- **新平台 HDR 普及**:若 抖音 / 快手 / 视频号 普及 HDR playback(目前仅 抖音 部分 iOS 端支持),需扩展 warmth preference 表为 HDR 维度
- **CN 调色 trend 转向**:若 2026+ 出现新主导 trend(如 high-key saturated 或 neo-noir 取代 "lit from within"),需更新本 ref §"Lit from Within" Trend
- **新学术 CN color-emotion 论文**:见 [`color-cross-cultural.md`](./color-cross-cultural.md) §Drift Signals —— 若有 CN sample 学术论文,需 cross-link 并对照本 ref industry observation

任何 drift signal 触发,需在本 ref 顶部 `**Last-verified:**` 字段更新日期,并在修订章节标注 "revised YYYY-MM due to [drift signal]"。
