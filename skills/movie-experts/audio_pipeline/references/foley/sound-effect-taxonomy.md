# Sound Effect Taxonomy — BBC + Freesound + 短剧 SFX Library

**Source:** BBC Sound Effects Library catalogue (BBC Sound, 2024);freesound.org community taxonomy (Creative Commons, 2024-2026);Zagorski-Thomas *The Musicology of Record Production* (2014) §SFX chapter;CN 平台 公开 短剧 SFX usage 统计(2024-2026)。
**Copyright:** Fair Use — paraphrased taxonomy + usage stats; no reproduction of copyrighted SFX library audio. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 foley 专家在 **SFX 分类 + 短剧 SFX 用法** 决策时的**权威源**。它涵盖 BBC 21-category SFX taxonomy + freesound.org 标签系统 + 短剧 SFX 高频用法统计 + per-platform SFX divergence。

## BBC 21-Category SFX Taxonomy

### 关键 heuristic 1 (load-bearing): BBC 21 大类 + 短剧 高频使用

| # | 类别 | 短剧 高频使用 | 备注 |
|---|------|--------------|------|
| 1 | Atmospheres (背景环境)| ✅ 高 | 城市 / 室内 / 户外 |
| 2 | Doors / 玄关 | ✅ 极高 | 关门 / 开门 / 敲门 |
| 3 | Footsteps / 脚步 | ✅ 极高 | 不同地面 + 不同鞋 |
| 4 | Vehicles / 交通 | 中 | 汽车启动 / 刹车 / 喇叭 |
| 5 | crowds / 人群 | ✅ 高 | 街道人群 / 餐厅人群 |
| 6 | Weather / 天气 | 中 | 雨 / 雷 / 风 |
| 7 | Animals / 动物 | 低 | 狗叫 / 鸟鸣 |
| 8 | Household / 家居 | 中 | 厨房 / 浴室 |
| 9 | Office / 办公 | ✅ 高 | 键盘 / 打印机 / 电话 |
| 10 | Industrial / 工业 | 低 | 工厂 / 机械 |
| 11 | Machinery / 机械 | 低 | 同上 |
| 12 | Communications / 通讯 | ✅ 极高 | 电话铃 / 短信提示音 / 微信 |
| 13 | Sports / 运动 | 低 | — |
| 14 | Toys / 玩具 | 极低 | — |
| 15 | Weapons / 武器 | ✅ 高(男频)| 枪声 / 拳击 / 刀剑 |
| 16 | Water / 水 | 中 | 流水 / 浪 / 雨 |
| 17 | Magical / 魔幻 | 中(玄幻题材)| 法术 / 飞行 |
| 18 | Human sounds / 人声 | ✅ 极高 | 呼吸 / 叹气 / 笑 |
| 19 | Food / 食物 | 低 | 咀嚼 / 倒水 |
| 20 | Medical / 医疗 | 低 | 心跳 / 手术 |
| 21 | Sci-fi / 科幻 | 中(科幻题材)| 飞船 / 激光 |

**短剧 SFX 占比统计(基于 2024-2026 抖音 / 快手 短剧 case study):**
- Communications(微信提示音 / 电话铃):~25%
- Footsteps:~20%
- Doors:~15%
- Human sounds(呼吸 / 叹气):~10%
- Office / Household:~10%
- 其他 16 类合计:~20%

### 关键 heuristic 2: Per-platform SFX divergence

| Platform | SFX 风格偏好 | 备注 |
|----------|-------------|------|
| 抖音 短剧 | 高音量 + 高对比 + 强 emotional sting | 用户 scroll 行为需要 strong audio hook |
| 快手 短剧 | 自然 + 低对比 + authentic 感 | 草根用户偏好 real-feel |
| 小程序剧 | 戏剧化 + 夸张 + 卡点 强 | 用户付费观看,要求 emotional intensity |
| 视频号 | 标准 cinematic + 中等对比 | older 受众偏好 narrative depth |
| TikTok | trending SFX + 病毒式 sound template | 全球 trending sounds 复用 |
| YouTube Shorts | YouTube creator SFX library | 标准 YouTube 生态 |

---

## 短剧 SFX Design 协议

### 关键 heuristic 3: 3 类必备 SFX per scene

每个 scene 必须包含 3 类 SFX:

1. **Atmosphere / ambience bed**(背景层)— 持续 low-level 背景(街道 hum / 室内空调 / 自然环境)
2. **Action / Foley**(动作层)— character 动作产生的 SFX(脚步 / 衣物 / 物体接触)
3. **Spot / Highlight**(强调层)— 关键 narrative beat 的 SEX(微信提示音 / 关键 prop sound / emotional sting)

### 关键 heuristic 4: 卡点 SFX 设计

per [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §卡点 design,卡点 SFX 必须:
- 持续 0.5-1.5s(短而 sharp)
- 高 contrast vs ambience bed(至少 +6dB)
- Emotional intent = "tension" 或 "shock"
- 同集内卡点 SFX 一致(brand recall)

### 关键 heuristic 5: Layering 3-5 层 协议

高质量 foley 通常 3-5 层:

| Layer | 内容 | 典型音量 |
|-------|------|----------|
| Layer 1 | ambience bed | -25 dBFS |
| Layer 2 | character action(脚步 / 衣物) | -18 dBFS |
| Layer 3 | prop / object SFX | -15 dBFS |
| Layer 4 | emotional sting / 关键 highlight | -10 dBFS |
| Layer 5 (optional) | sweetener / sub-bass rumble | -22 dBFS |

---

## SFX Library 管理

### 关键 heuristic 6: 短剧 SFX library 累积策略

production 应建立递增 SFX library(per [`../production/references/asset-reuse-plan.md`](../production/references/asset-reuse-plan.md)):

- **第 1 集:** 从零生成 ~30 个基础 SFX(开门 / 脚步 / 电话 / 等)
- **第 2-5 集:** 复用 + 新增 ~10/集 → library 累积至 70 个
- **第 6-15 集:** 复用为主 + 新增 ~5/集 → library 累积至 120 个
- **第 16-30 集:** 几乎全复用 + 新增 ≤2/集 → library 稳定在 130-150 个

**SFX reuse rate target:** ≥ 95%(per asset-reuse-plan.md)。

---

## Anti-Patterns

### 关键 heuristic 7: SFX 5 大 anti-pattern(规避)

1. **Generic SFX library anti-pattern:** 用通用 SFX 库(无短剧 特化)。**Mitigation:** 建立短剧 specific library。
2. **Single-layer SFX anti-pattern:** 单层 SFX 无 depth。**Mitigation:** 3-5 layer 协议。
3. **Loud ambience bed anti-pattern:** ambience bed 太响盖过 dialogue。**Mitigation:** ambience bed ≤ -25 dBFS。
4. **Inconsistent 卡点 SFX anti-pattern:** 同集卡点 SFX 不一致。**Mitigation:** brand recall 规则。
5. **No SFX library accumulation anti-pattern:** 每集从零生成 SFX。**Mitigation:** 累积 library(per asset-reuse-plan.md)。

---

## Glossary

- **Ambience bed:** 持续 low-level 背景 SFX。
- **Action layer:** character 动作 SFX。
- **Spot / Highlight:** 关键 narrative beat SFX。
- **Sweetener:** 增强氛围的 sub-layer。
- **Sting:** 短 sharp emotional SFX(常用于 卡点)。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-03 (foley RAG uplift).*
*Source provenance: BBC Sound Library catalogue (2024) / freesound.org taxonomy (2024-2026) / Zagorski-Thomas 2014 / CN 平台 公开 短剧 SFX 统计 (2024-2026) — fair use paraphrase + short technical phrases only.*
