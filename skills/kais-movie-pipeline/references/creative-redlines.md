# Creative Redlines — 7 Cross-Platform Invariants

**Source:** Notion page `32811082-af8e-8009-b097-d19a5027b46f` (anchor block `38211082-af8e-800e-b464-c65441cf8e6e`, "心流♥ → aigc开发 → 创作方向" §第一性原理分析 / §剧集策略). Kai's canonical v1 creative-strategy doc.
**Copyright:** Fair Use — factual strategy structure + brief operational definitions reproduced verbatim with attribution; no copyrighted creative content.
**Last-verified:** 2026-06-26

---

## Summary

本 ref 是 **v1 跨平台创作的 7 条不变量红线权威源**。其中:

- **5 条单集红线(R1-R5)** —— 在单集合规审核时检查(engagement / pacing / 结构维度);任何单集发布前都必须 5/5 通过。
- **2 条流程红线(R6-R7)** —— 在 A/B 收敛循环期间检查(实验流程 / 统计决策);与单集内容无关,但决定 v1 启动期是否能产出可信结论。

这些红线是 **CREATIVE-strategy invariants**(参与度 / 节奏 / 结构),与 `compliance_gate` 的 8 条 LEGAL 红线(政治敏感 / 暴力血腥 / 等)是**两层独立** —— 见底部 §与 compliance_gate 红线的关系。两层都必须通过,单集才可发布。

---

## Per-Episode Red Lines (1-5)

> 5 条红线在单集合规审核时检查,违反任一即单集视为结构失败 → 回到上游专家重做。

### R1. 情绪脱敏 (Emotion Desensitization)

**操作化定义 (Operational definition):** 同类型情绪连续出现不得超过 2 次。具体:在任意 60 秒窗口内,连续同一 taxonomy 的情绪镜头 ≤ 2 个;第 3 个连续同类型即触发脱敏。
**检测提示 (Detection signal for compliance_gate):** 解析 `script.json` 中 `script_emotion_tags`(per-beat 情绪标签);扫描连续 ≥ 3 个同标签 beat → 标记 R1 违反。
**违反示例 (Violation example):** 60 秒内 3 个连续"愤怒"特写 → 观众情绪疲劳,后续愤怒镜头情绪反应下降 ≥ 40%。
**合规示例 (Compliant example):** 60 秒内 2 个"愤怒"+ 1 个"震惊" → 异类型切换,情绪节奏不脱敏。
**关联专家 (Related expert):** screenplay(写时控制情绪 taxonomy 分布)+ editor(剪辑时跨镜头打断脱敏序列)。

### R2. 信息分层 (Information Layering)

**操作化定义 (Operational definition):** 每帧只承载一层主导信息。具体:每帧允许 ≤ 1 个 primary 信息层 + ≤ 1 个 secondary 信息层;primary 必须占据视觉注意力中心(≥ 60% 像素权重)。
**检测提示 (Detection signal for compliance_gate):** scene-level 视觉审计(消费 `scene-images` slot);用 saliency map 算 primary 区域像素权重 < 60% → 标记 R2 违反。
**违反示例 (Violation example):** 一帧同时呈现"角色对话 + 道具特写 + 字幕 + 背景动效" → primary 信息层 < 60%,观众注意力分散 → 信息处理失败。
**合规示例 (Compliant example):** 一帧 primary = 角色脸部特写(70%),secondary = 道具虚化(20%),字幕(10%) → primary 主导,信息可解析。
**关联专家 (Related expert):** cinematographer(构图保证 primary 主导)+ visual_executor(渲染时分层)。

### R3. 零背景铺垫 (Zero Backstory Preamble)

**操作化定义 (Operational definition):** 切入即冲突,禁止"从前有个…"。具体:竖屏前 3 秒 / 横屏前 10 秒必须包含 active conflict,不可出现纯 exposition(旁白叙述背景 / 字幕交代设定 / 静止画面)。
**检测提示 (Detection signal for compliance_gate):** 解析 `script-draft` 第一 beat;若第一 beat 标记为 exposition / narration / setup → 标记 R3 违反。
**违反示例 (Violation example):** 竖屏前 3 秒 = 旁白"她是一个普通上班族…"+ 角色走路静止画面 → 无冲突,观众划走。
**合规示例 (Compliant example):** 竖屏前 3 秒 = 角色突然撞到上司 + 上司发怒 → active conflict,锁定注意力。
**关联专家 (Related expert):** screenplay(写开场必须入冲突)+ hook_retention(钩子位置与开场冲突同源)。

### R4. 结尾未完成 (Unresolved Ending)

**操作化定义 (Operational definition):** 最后 3 秒(竖屏)/ 最后 10 秒(横屏)必须释放新钩子,禁止大团圆。具体:最后窗口必须引入一个新的 open question(悬念 / 反转 / 新信息),不可出现冲突闭合 / 情绪舒缓 / "未完待续"静止字幕。
**检测提示 (Detection signal for compliance_gate):** 解析 `script-draft` 末 beat;若末 beat 标记为 resolution / closure / epilogue → 标记 R4 违反。
**违反示例 (Violation example):** 末 3 秒 = "二人拥抱 + 字幕:他们从此过上了幸福生活" → 闭合,无追播理由。
**合规示例 (Compliant example):** 末 3 秒 = 拥抱时角色手机突然响起 + 屏幕显示"前妻" → 新 open question,触发追播。
**关联专家 (Related expert):** screenplay(写结尾埋钩子)+ editor(剪辑保留悬念节拍)+ hook_retention(结尾即下一集钩子设计)。

### R5. 差异化识别 (Differentiation Marker)

**操作化定义 (Operational definition):** 0.5 秒内存在一个可被识别的异常点。具体:任意镜头切换的前 0.5 秒内,必须出现 ≥ 1 个可被识别的视觉异常(非预期颜色 / 非预期运动 / 非预期对象)或音频异常(非预期音效 / 非预期停顿)。
**检测提示 (Detection signal for compliance_gate):** shot-boundary + visual saliency 审计;若切换后 500ms 内 saliency peak 未超 baseline +20% → 标记 R5 违反。
**违反示例 (Violation example):** 镜头切换后画面与前一镜同色调 / 同运动节奏 → 观众视觉系统判定"无新信息",注意力下滑。
**合规示例 (Compliant example):** 镜头切换后第一个画面出现一个红色道具(前一镜为冷色调)→ 异常点,saliency peak +35%,识别成功。
**关联专家 (Related expert):** cinematographer(运镜设计差异化点)+ visual_executor(渲染时插入异常元素)。

---

## Process Red Lines (6-7) — Apply During A/B Convergence Loop

> 2 条流程红线在 v1 启动期的 A/B 实验循环期间检查,与单集内容无关。它们决定 v1 能否基于实验数据做可信决策。

### R6. 控制变量 (Control Variable) (PROCESS RED LINE — not per-episode)

*这是一条流程红线,在 A/B 收敛循环期间触发,不在单集合规审核中检查。*

**操作化定义 (Operational definition):** 一次实验只改一个结构参数。A/B 测试 variant 与 baseline 必须 **恰好** 在一个结构参数上不同(节奏 / 钩子位置 / 题材子类 / 配色 / 配乐);variant diff log 必须在 gate-submit 时提交。
**检测提示 (Detection signal for theory_critic / kais-movie-pipeline):** 解析 convergence-loop variant diff;若 diff 中包含 ≥ 2 个变更参数 → 标记 R6 违反,实验结果不可作为决策依据。
**违反示例 (Violation example):** variant 同时改"钩子位置 + 配色 + 配乐节奏"→ 若完播率提升 15%,无法归因到任一参数 → 决策无意义。
**合规示例 (Compliant example):** variant 只改"钩子位置"(第 1s → 第 2s)→ 若完播率提升,可直接归因 → 决策有效。
**关联专家 (Related expert):** kais-movie-pipeline(编排 A/B loop)+ theory_critic(批评实验设计)。

### R7. 统计显著 (Statistical Significance) (PROCESS RED LINE — not per-episode)

*这是一条流程红线,在 A/B 收敛循环决策时触发,不在单集合规审核中检查。*

**操作化定义 (Operational definition):** 样本量 N≥10 或置信区间 < ±5% 才做决策。具体:variant 决策(采纳 / 拒绝 / 继续实验)必须满足以下任一:(1) 样本量 N ≥ 10(单 variant);(2) 95% CI half-width < 5%。
**检测提示 (Detection signal for kais-movie-pipeline):** 解析 convergence-loop 决策日志;若决策时 N < 10 且 CI half-width ≥ 5% → 标记 R7 违反,决策无效。
**违反示例 (Violation example):** N=3 时观察到 variant 完播率高 10% 即宣布采纳 → 样本量不足,极可能是噪声 → 后续 N=10 验证时反转。
**合规示例 (Compliant example):** N=10 variant 完播率 +12% ± 4% → CI half-width < 5%,可采纳。
**关联专家 (Related expert):** kais-movie-pipeline(决策门控)。

---

## 与 compliance_gate 红线的关系 (Relationship to compliance_gate §1..§8)

> **本节是关键澄清,避免两层红线混淆。**

本文档的 7 条红线是 **CREATIVE-strategy invariants**,关注 **engagement / pacing / 结构维度**(情绪脱敏 / 信息分层 / 开场冲突 / 结尾悬念 / 差异化 / 实验流程 / 统计决策)。

`compliance_gate` 的 8 条红线(`references/cn-content-rules.md` §1..§8)是 **LEGAL invariants**,关注 **法律合规维度**(政治敏感 / 暴力血腥 / 色情低俗 / 未成年人保护 / 民族宗教 / 歧视侮辱 / 虚假宣传 / 版权侵权)。

**两层关系:**

| 维度 | creative-redlines (本文) | compliance_gate §1..§8 |
|------|--------------------------|--------------------------|
| 关注层 | engagement / 结构 | 法律合规 |
| 触发时机 | **pre-publish 设计约束**(写剧本前 / 剪辑前 / 实验时) | **pre-distribution 合规闸门**(分发前硬门) |
| 违反后果 | 结构失败 → 回上游专家重做(creatively suboptimal) | 法律风险 → 全网下架 + 处罚(legally non-distributable) |
| 关联专家 | screenplay / editor / cinematographer / hook_retention / theory_critic | compliance_gate |

**两层必须都通过,单集才可发布。** creative redlines 是创作期设计约束(降低结构性失败概率);compliance redlines 是分发前合规闸门(消除法律风险)。**不可互相替代** —— 一集可能 creative-redlines 全过但 compliance-redlines fail(例:结构精良但触发 §3 色情低俗),反之亦然。

---

## See Also

- [`platform-specs.md`](./platform-specs.md) — v1 平台硬性规格(竖屏 vs 横屏对照表 + 4 层刚性约束)
- [`genre-anchor-urban-fantasy.md`](./genre-anchor-urban-fantasy.md) — v1 题材锚定
- [`../../movie-experts/compliance_gate/SKILL.md`](../../movie-experts/compliance_gate/SKILL.md) — LEGAL 红线闸门(§1..§8);本文的 creative redlines 与其是两层独立关系
