# Platform Specs — V1 Hard Constraints

**Source:** Notion page `32811082-af8e-8009-b097-d19a5027b46f` (anchor block `38211082-af8e-800e-b464-c65441cf8e6e`, "心流♥ → aigc开发 → 创作方向" §平台策略). Kai's canonical v1 platform-strategy doc.
**Copyright:** Fair Use — factual strategy specs reproduced verbatim with attribution; no copyrighted creative content.
**Last-verified:** 2026-06-26

---

## Summary

本 ref 是 **v1 平台策略的硬性规格权威源**。它给出竖屏滑动(抖音/快手/B站 Story Mode)与横屏主动(B站/优腾爱 短剧)两种内容形态的硬性对照,以及跨 4 层(生理 / 行为 / 平台 / 市场)的 12 条刚性约束。所有 v1 分发决策、节奏设计、钩子位置都必须先对照本表。

底部的 **使用指南** 给出每个 movie-expert 何时需要查阅本 ref。本 ref **不覆盖** 合规红线(那是 `creative-redlines.md` 与 `compliance_gate/references/cn-content-rules.md` 的范畴),只覆盖结构 / 节奏 / 注意力窗口 之类的硬性规格。

---

## 硬性规格对照表 (Hard-Spec Cross-Platform Matrix)

> Reproduced verbatim from Notion §平台策略 §硬性规格。两列对照 v1 两大平台形态;数值即硬约束,任何 v1 生产决策不可违反。

| 维度 | 竖屏滑动 (抖音 / 快手 / B站 Story Mode) | 横屏主动 (B站 / 优腾爱 短剧) |
|------|------------------------------------------|------------------------------|
| 用户契约 (user contract) | 被动投喂,随时划走 | 主动点击,预付耐心 |
| 注意力窗口 (attention window) | 0-3 秒(生死线) | 5-10 秒(钩子线)+ 30 秒(信任死亡线) |
| 最优时长 (optimal duration) | 15-60 秒 | 90 秒-5 分钟 |
| 钩子位置 (hook placement) | 第 1-3 秒 | 第 5-10 秒 |
| 身份锚定 (identity anchor) | 第 3-8 秒 | 第 5-15 秒 |
| 首次情绪转折 (first emotional turn) | 第 8-15 秒 | 第 30-60 秒 |
| 情绪单元间隔 (emotion-unit gap) | ≤ 8 秒 | ≤ 60-90 秒 |
| 记忆闭环 (memory closure) | 30 秒内微型闭环 | 60-90 秒单元闭环 |
| 切入点要求 (entry-point rule) | 任意秒切入必须自洽 | 前 30 秒允许轻度上下文依赖 |
| 算法逻辑 (algorithm logic) | 冷启动秒级审判,阶梯流量池 | 完播率+追播率+追番率 |

**读法提示:**
- 用户契约 (user contract) 行是第一性原理 —— 竖屏"被动投喂"决定了所有下行硬约束(生死线 0-3s / 任意秒切入自洽 / 情绪单元 ≤ 8s)。
- 注意力窗口 (attention window) 与 最优时长 (optimal duration) 的乘积决定了"一集能容纳几个情绪单元" —— 竖屏 60s / 8s ≈ 7 单元,横屏 5min / 90s ≈ 3-4 单元。

---

## 刚性约束 (Hard Constraints by Layer)

> Reproduced from Notion §平台策略 §刚性约束。4 层 × 各层约束 = 12 行;每行给出该约束对 AI 短剧 的直接要求。这些约束是 v1 的硬边界,不是建议。

### 生理层 (Physiological Layer)

| 约束 | AI 短剧 要求 |
|------|-------------|
| 人眼视觉停留极限 ≈ 200ms | 单镜头视觉信息密度需在 200ms 内可解析;复杂构图需拆分多镜 |
| 听觉-视觉同步窗口 ±80ms | 配音 / 音效 / 字幕 必须 ≤ 80ms 内对齐画面;超出即观众抽离 |
| 情绪反应延迟 ≈ 300ms | 钩子刺激与下一个画面切换之间需预留 ≥ 300ms 让情绪完成反射 |

### 行为层 (Behavioral Layer)

| 约束 | AI 短剧 要求 |
|------|-------------|
| 划走手势触发区(屏幕下三分之一) | 关键视觉信息(角色脸 / 钩子物件)不可只落在下三分之一;需上下分布 |
| 重复观看触发条件(≥ 1 个异常点) | 每 15 秒(竖屏)/ 每 60 秒(横屏)至少 1 个差异点刺激重看 |
| 收藏/转发 决策窗口(结尾前 3 秒) | 结尾未完成 (Unresolved Ending) 必须埋在最后 3s(竖屏)/ 10s(横屏)—— 见 `creative-redlines.md` R4 |

### 平台层 (Platform Layer)

| 约束 | AI 短剧 要求 |
|------|-------------|
| 冷启动秒级审判(抖音/快手) | 前 3 秒不可出现纯文字 / 静止画面;需动态冲突 |
| 完播率权重(B站/优腾爱) | 开头 / 中段 / 结尾 三处必须各有 1 个"留存拐点"避免跳流失 |
| AIGC 标识显式要求(全平台) | 见 `compliance_gate` 的 AIGC 三件套规格 —— 标识不可遮挡下方视觉信息 |

### 市场层 (Market Layer)

| 约束 | AI 短剧 要求 |
|------|-------------|
| 爆款公式迭代周期 ≈ 2-3 周 | v1 不可一次押注单公式;必须留 A/B 收敛空间(见 `creative-redlines.md` R6 控制变量) |
| 平台流量分配优先级(完播率 > 互动 > 转发) | 完播率是首要 KPI —— 节奏(情绪单元间隔)优先于信息量 |
| 同质化风险(N≥10 才判定趋势) | v1 启动期必须做 N≥10 样本验证(见 `creative-redlines.md` R7 统计显著) |

---

## 使用指南 (Per-Expert Consultation Guide)

下列是 v1 阶段 movie-experts 何时应查阅本 ref:

- **`hook_retention`** — 设计 0-3s / 5-10s 钩子前,必须先核对钩子位置 (hook placement) 与 注意力窗口 (attention window) 行;钩子若落在窗口外即结构失败。
- **`editor`** — 节奏调整情绪单元间隔时,必须对照 情绪单元间隔 (emotion-unit gap) 行:竖屏 ≤ 8s,横屏 ≤ 60-90s。任何单元超出即重剪。
- **`cinematographer`** — 决定单镜头时长与运镜时,需参照 最优时长 (optimal duration) 与 切入点要求 (entry-point rule) —— 竖屏任意秒切入自洽要求运镜不可依赖"上一秒"的累积。
- **`screenplay`** — 写切入台词 / 第一场冲突时,需参照 用户契约 (user contract) 与 首次情绪转折 (first emotional turn) —— 竖屏必须在 8-15s 完成首次情绪转折,横屏可放宽至 30-60s。
- **`theory_critic`** — 评估作品平台契合度时,本表是硬规格基线;任何"理论上好但违反硬规格"的建议应标注不可执行。

---

## See Also

- [`creative-redlines.md`](./creative-redlines.md) — 7 条跨平台创作红线(5 条单集 + 2 条流程),与本文"硬性规格"互补
- [`genre-anchor-urban-fantasy.md`](./genre-anchor-urban-fantasy.md) — v1 题材锚定(都市奇幻·轻喜剧)与 8 平台内容形态
- [`../movie-experts/compliance_gate/SKILL.md`](../../movie-experts/compliance_gate/SKILL.md) — 合规闸门专家(本 ref 不覆盖法律 / 平台红线,只覆盖结构 / 节奏规格)
