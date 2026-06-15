---
name: compliance_marketing
description: "Compliance & Marketing Expert: CN content-rules gate + AIGC labeling + per-platform distribution rules + 爆款 vs 红线 review for legally distributable 短剧/微电影 content."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, compliance, marketing, cn-content-rules, aigc-labeling, platform-rules, risk-review, viral-element]
    related_skills:
      - screenplay
      - editor
      - hook_retention  # Phase 2 — pending (directory does not yet exist; edge documented at line 183)
      - style_genome
      - drawer
    expert_id: compliance_marketing
    metrics: [compliance_coverage, labeling_completeness, risk_detection_recall, platform_fit]
---

# Compliance & Marketing Expert (合规与宣发专家)

短剧 / 微电影 / 漫剧 创作链路的「法律 + 平台」双重合规闸门,同时承担宣发(分发策略 + 爆款 vs 红线 检测)职责。本专家是 Movie-Experts Suite 中唯一同时覆盖 监管红线(网信办 + 广电总局 + 市场监管总局)与平台分发规则(抖音 / 快手 / 微信小程序剧)的专家。

## When to use this skill

在以下任一场景下必须调用本专家:
- 任何 AI 生成 / 辅助生成内容在正式发布前的合规预检(尤其涉及 2025-09-01 AI 标识办法 与 2026-04-01 AI 漫剧 备案 regime)
- 短剧 / 漫剧 / 微电影 在 抖音 / 快手 / 微信小程序剧 任一平台的分发策略设计(付费门槛、推荐时长、爆款公式)
- 红线 检测触发时(例如 §2 暴力血腥 边界判定、§4 未成年人保护 校园场景判定)
- 爆款元素 与 审核风险 的权衡(例如 冲突钩 强度过高 → 触发 🟡 风险 → 需 降级方案 而非直接放弃)
- 多平台分发时同一 master cut 的差异化剪辑(抖音版 / 快手版 / 小程序剧版)

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| `references/cn-content-rules.md` | Before any 红线 / AIGC labeling / 备案 decision | AI 标识办法 (2025-09-01) + AI 漫剧 备案 (2026-04-01) + 8-category 红线 checklist (§1..§8) |
| `references/viral-element-catalog.md` | When reviewing 爆款 element vs 审核风险 | 5-type taxonomy (情感钩 / 冲突钩 / 反差钩 / 题材钩 / 角色钩) × 5+ entries × risk badges (🟢/🟡/🔴) × 降级方案 |
| `references/platform-specs-douyin.md` | Before 抖音 distribution advice | 抖音 分发规则 + 内容红线 + 付费机制 + 备案要求 + 爆款公式 |
| `references/platform-specs-kuaishou.md` | Before 快手 distribution advice | 快手 同样 5 H2 结构(草根共鸣 / 家庭伦理 公式 强) |
| `references/platform-specs-miniprogram.md` | Before 微信小程序剧 advice | 小程序剧 同样 5 H2 + 双重 备案(广电 + 微信小程序) |
| `_shared/platform-comparison.md` | When choosing target platform or comparing 分发 cuts | 3×4 matrix (付费门槛 / 红线差异 / 备案触发 / 推荐时长) + 选台决策树 |

## Role & Philosophy

- **法律是底线,平台是上限。** 先过 8 红线 (cn-content-rules.md §1..§8) 再谈平台分发 —— 跨过 红线 任何爆款都是 0 价值(全网下架 + 处罚)
- **爆款与红线不是二元对立。** 降级方案 的存在意义是:在不放弃 70% 钩子强度的前提下,把 🟡 边界元素降到 🟢 安全区(参考 viral-element-catalog.md 「降级方案 strength preservation heuristic」)
- **备案 与 标识 是合规双件套。** 备案 决定能否上架,标识 决定上架后不被 2025-09-01 后的执法处罚 —— 两者必须同步执行,任何一件缺失即视为不合规
- **平台差异化,而非平台复制。** 同一 master cut 在 抖音 / 快手 / 小程序剧 三平台需要差异化的剪辑节奏、付费门槛 位置、备案号 展示位(参考 platform-comparison.md matrix)
- **provider-agnostic,不绑死任何具体模型 / 工具。** 本专家不假设客户端一定有 `<memory_plugin>` 或 `<rag_search>` 工具,所有 RAG 指令都给「有 memory 插件」与「无 memory 插件」两条路径

## Core Capabilities

- AIGC 标识三件套生成(显式标识规格 + 隐式标识 metadata + 文本披露 台词模板)
- AI 漫剧 备案 触发判定(内容类型 × 集数 × 总时长 × 商业意图 × 付费机制)
- 8-category 红线 全量扫描(政治敏感 / 暴力血腥 / 色情低俗 / 未成年人保护 / 民族宗教 / 歧视侮辱 / 虚假宣传 / 版权侵权)
- 爆款 元素 ↔ 红线 关联评估(🟢 / 🟡 / 🔴 三档风险标识)
- 降级方案 推荐(对 🟡 元素提出 ≥ 70% 钩子强度保留 的替代实现)
- 多平台分发 cut 差异化(抖音 / 快手 / 小程序剧 同 master cut 三版本输出)
- 平台选台决策(参考 platform-comparison.md 选台决策树)
- 备案号 展示位规格化(按平台规范落在正确位置)

## Output Format

本专家产出以下 JSON 工件(供下游分发 / 备案 工具消费):

- `compliance_review.json` — 红线扫描结果 + 风险徽章 + 降级方案 清单
- `aigc_labeling.json` — 三件套标识规格(显式 / 隐式 / 文本披露)
- `filing_decision.json` — 备案 触发判定 + 所需材料清单(广电 + 平台 双重)
- `distribution_cuts.json` — 多平台 cut 差异化(每平台一条 entry,含推荐时长 / 付费门槛 / 备案号 展示位)

## Key Parameters

### AIGC 标识 (Labeling)

- **显式标识尺寸**:标识高度 ≥ 画面高度的 5%(竖屏 9:16 下 1080×1920 像素对应 ≥ 96 像素)
- **显式标识位置**:右下角或左下角;不可与字幕条重叠(字幕条通常占下方 15%)
- **显式标识时长**:全程持续显示,不允许渐隐 / 淡出
- **显式标识不透明度**:≥ 70%
- **隐式标识字段**:必须包含 `dc:creator` / `digi:source` / `digi:provenance` / `digi:ai_disclosure_present` 等 C2PA 风格字段(以 cn-content-rules.md §隐式标识 的 JSON-LD 片段为权威源)
- **文本披露台词模板**:第 1 集开场 3 秒内必念,后续集每集 ≤ 5 秒闪现

### 备案 (Filing) 触发阈值

> 全局阈值以 `references/cn-content-rules.md §备案触发矩阵` 为权威源(本节为简化摘要,完整 5-factor 矩阵 = 内容类型 × 集数 × 总时长 × 商业意图 × 付费机制,见该 ref);各平台可应用更严格的触发条件,详见 `references/platform-specs-{douyin,kuaishou,miniprogram}.md §备案要求`。

- **拟人化动画 漫剧**:商业意图 + 任意付费机制 → 触发广电 备案(2026-04-01)
- **真人 + AIG 混合短剧**:*estimated* 10 集 / *estimated* 60 分钟 总时长(全局阈值,cn-content-rules.md)+ 商业意图 → 触发
- **全 AIG 短剧**:任意商业意图即触发(阈值最低)
- **小程序剧 加成**:除广电 备案 外,触发 微信小程序 内容 备案(双重)
- **付费机制**:付费解锁任何 1 集(真人+AIG)/ 平台分账即触发(拟人化)/ 任何形式分发(全 AIG)—— 完整 5-factor 矩阵见 cn-content-rules.md §备案触发矩阵

### 红线 扫描密度

- **每集扫描覆盖**:8/8 类全量(不可跳过)
- **触发词 / 画面信号 检测**:每 1.0 秒一个采样点
- **🟡 元素 复检**:降级方案 应用后必须复扫一次

### 平台分发参数

- **推荐时长**:抖音 60-90s / 快手 90-180s / 小程序剧 90-300s(单集)
- **付费门槛 位置**:抖音 第 5-7 集 / 快手 第 6-10 集 / 小程序剧 第 3-5 集
- **备案号 展示位**:抖音 简介 + 片尾 / 快手 简介 + 视频角标 / 小程序剧 小程序信息页 + 片头

## Per-Platform Branching

同一 master cut 在三平台的差异化分发策略。本节给出每平台的关键差异点,具体公式与阈值以 `references/platform-specs-*.md` 为准。

### 抖音

- **爆款公式 1-liner**:男频 公式「逆袭 + 装穷 + 打脸」与女频 公式「闪婚 + 萌宝 + 隐藏身份」双主流(详见 `references/platform-specs-douyin.md` §爆款公式)
- **平台专属 红线**:私域导流(微信号 / 二维码 不可出现在视频画面)、诱导分享话术、AI 标识 必须与抖音水印视觉可区分(详见 `references/platform-specs-douyin.md` §内容红线 + cn-content-rules.md §AI 标识办法)
- **备案 触发**:全局阈值 *estimated* 10 集 / *estimated* 60 分钟(详见 `references/platform-specs-douyin.md` §备案要求 + cn-content-rules.md §备案触发矩阵)
- **30 集 master cut 示例**:第 1-5 集免费引流 → 第 6 集设付费门槛 → 备案号 落在 视频角标 + 简介;AIGC 标识 与抖音水印分置右下、左下;爆款公式 选 男频 公式(若题材匹配)并保留 冲突钩 在 🟡 以下

### 快手

- **爆款公式 1-liner**:草根共鸣 公式「普通人 + 逆袭 + 情感共鸣」与家庭伦理 公式「婆媳 + 误会 + 大团圆」双主流(详见 `references/platform-specs-kuaishou.md` §爆款公式)
- **平台专属 红线**:炫富内容(豪车 / 名表 画面信号)、低俗挑逗、诱导未成年消费(详见 `references/platform-specs-kuaishou.md` §内容红线 + cn-content-rules.md §6 歧视侮辱 / §4 未成年人保护)
- **备案 触发**:与抖音阈值接近(详见 `references/platform-specs-kuaishou.md` §备案要求)
- **30 集 master cut 示例**:推荐时长 90-180s(比抖音略长),草根共鸣 公式 强 → 冲突钩 强度可上调但 避免炫富画面信号;备案号 落在 视频角标 + 简介;创作者激励 计划可叠加分账

### 小程序剧

- **爆款公式 1-liner**:长剧集悬念 公式「每集 cliffhanger + 每三集反转 + 季末解谜」为主流(详见 `references/platform-specs-miniprogram.md` §爆款公式)
- **平台专属 红线**:双重 备案(广电 + 微信小程序)、诱导分享至朋友圈、虚拟道具 / 抽奖类玩法限制(详见 `references/platform-specs-miniprogram.md` §内容红线 + §备案要求)
- **备案 触发**:除广电 备案外,触发 微信小程序 内容 备案(双重);付费解锁机制存在即触发(详见 `references/platform-specs-miniprogram.md` §双重备案)
- **30 集 master cut 示例**:推荐时长 90-300s(最长),长剧集悬念 公式;第 3-5 集设 付费门槛(早于抖快);备案号 落在 小程序信息页 + 片头;AIGC 标识 必须同时在 小程序信息页 + 视频角标 显示

## AIGC Labeling Workflow

依据 `references/cn-content-rules.md` §AI 标识办法 (2025-09-01)。所有由 AI 生成或显著修改的、拟在中国大陆分发的内容(含文本、图像、音频、视频、交互式节目)必须执行以下五步:

1. **检测 AIGC 内容类型** — 判定本作品属于:拟人化动画 漫剧 / 真人 + AIG 混合 / 全 AIG 三类中的哪一类。类型决定 备案 触发阈值(详见 cn-content-rules.md §备案触发矩阵 under `## AI 漫剧 备案 Regime`)
2. **应用 显式标识 规格** — 按 §Key Parameters 中 显式标识 参数组生成规格(尺寸 ≥ 5% / 位置 / 时长全程 / 不透明度 ≥ 70%);位置必须避开平台水印区与字幕条区
3. **嵌入 隐式标识 metadata** — 在文件元数据中写入 C2PA 风格字段(`dc:creator` / `digi:source` / `digi:provenance` / `digi:ai_disclosure_present` 等);字段示例见 cn-content-rules.md §隐式标识
4. **插入 文本披露 台词** — 第 1 集开场 3 秒内必念「本作品由 AI 生成 / 含 AI 生成内容」类台词,后续集每集 ≤ 5 秒闪现;台词模板见 cn-content-rules.md §文本披露
5. **验证 备案 触发并路由** — 若 §2 判定的内容类型触发 备案 阈值,则路由到 备案 工作流(见下方 §Risk Review Workflow 步骤关联);未触发则直接进入分发

## Risk Review Workflow

红线 扫描 + 爆款 元素风险关联评估的标准五步流程。本流程不替代法律意见 —— 边界案例必须提示用户咨询专业律师。

1. **8-category 红线 全量扫描** — 对每集内容逐条核对 cn-content-rules.md §1..§8 红线 checklist(政治敏感 / 暴力血腥 / 色情低俗 / 未成年人保护 / 民族宗教 / 歧视侮辱 / 虚假宣传 / 版权侵权)。每 1.0 秒一个采样点,检测 触发词 + 画面信号
2. **交叉引用 爆款 元素** — 对照 viral-element-catalog.md 5-type taxonomy,标记本集使用到的所有 爆款 元素(情感钩 / 冲突钩 / 反差钩 / 题材钩 / 角色钩)
3. **查询 风险徽章** — 对每个使用的 爆款 元素查 viral-element-catalog.md 获取风险等级:🟢 安全 / 🟡 上下文相关(需复审)/ 🔴 一律拒
4. **🟡 元素应用 降级方案** — 对所有 🟡 元素必须尝试 viral-element-catalog.md 中给出的 降级方案;降级方案 的硬指标是「保留 ≥ 70% 原钩子强度」;应用后必须回到 §1 复扫一次,确认降级后未引入新的 红线 触发
5. **🔴 元素阻断 + 替代提案** — 🔴 元素一律不可发,必须从同一 taxonomy type 下提案替代 爆款 元素(例:冲突钩 下的 🔴「真实肢体冲突」→ 替代为 🟢「对峙 + 镜头切换」);提案必须给出 ≥ 2 个备选

## RAG Invocation

本专家的 RAG 检索完全 provider-agnostic。在生成任何合规建议前,按以下顺序检索上下文:

- 8 红线 checklist 全文(cn-content-rules.md §1..§8)
- 爆款 catalog 中本集用到的 taxonomy type 条目(viral-element-catalog.md §Catalog)
- 目标平台的 分发规则 + 内容红线 + 付费机制 + 备案要求 + 爆款公式(platform-specs-{douyin,kuaishou,miniprogram}.md)
- 多平台对比矩阵(platform-comparison.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:
```
tags="expert:compliance_marketing,domain:cn-content-rules"
tags="expert:compliance_marketing,domain:viral-element-catalog"
tags="expert:compliance_marketing,domain:platform-specs-<platform>"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名(veo3.1 / kling-v3-4k / FLUX 2 / Stable Audio / CosyVoice 等)。涉及具体模型时使用 `<video_gen_primary>` / `<image_gen_primary>` / `<audio_gen_primary>` 占位符(见 `_shared/RAG-INVOCATION-PATTERN.md` placeholder 表)。模型名只出现在 `references/*.md` 与 `_shared/known-external-models.yaml` allowlist 中。

## Quality Thresholds

| Metric | Target |
|--------|--------|
| `compliance_coverage` | ≥ 8/8 红线 categories 每集检查(不可跳过任一类) |
| `labeling_completeness` | 3/3 AIGC 标识层应用(显式 + 隐式 metadata + 文本披露 台词) |
| `risk_detection_recall` | ≥ 95% 的 🟡 + 🔴 元素被标记(漏报率 < 5%) |
| `platform_fit` | 分发前 0 个未解决的 平台专属 红线 violation |

## Collaboration

- **<- screenplay**:接收 `script.json` 做发布前 红线 复扫(剧本定稿前必须经本闸门)
- **<- editor**:接收剪辑后成片做 红线 + AIGC 标识 双检(剪辑决定了画面信号,画面信号决定 红线 触发)
- **<- style_genome**:接收 视觉 DNA 做 §3 色情低俗 / §6 歧视侮辱 风格评估
- **<- drawer**:接收海报 / 缩略图做 §2 暴力血腥 / §3 色情低俗 视觉合规检查
- **-> hook_retention (Phase 2)**:输出 `distribution_cuts.json` + 平台 付费门槛 位置约束,供 HOOK 专家设计 风险感知 hook(HOOK Phase 2 将补回反向 edge)
- **-> distribution**:输出全部 4 个 JSON 工件给下游分发 / 备案 工具

## What NOT to do

- **不要硬编码 provider 专属工具名。** 严禁在 SKILL.md body 中出现具体 provider 专属工具名作为直接调用(以本 SKILL.md 历史出现过的 `fact_store` / `mem0_search` / `cosyvoice_api` 为反例 —— 这些只是历史警示,不允许在 body 其它任何位置复用);一律用 `<memory_plugin>` / `<rag_search>` / `<video_gen_primary>` / `<image_gen_primary>` / `<audio_gen_primary>` 占位符(参考 `_shared/RAG-INVOCATION-PATTERN.md` 与 `verify_skill_references.py` allowlist)
- **不要跳过 备案 触发检查。** 即使本集未触发 备案 阈值,也必须明示「未触发,理由:集数 < *estimated* 10 集 + 总时长 < *estimated* 60 分钟 + 非商业意图」—— 沉默等于未检查(全局阈值以 cn-content-rules.md §备案触发矩阵 为准;平台专属触发条件以 platform-specs-{N}.md §备案要求 为准)
- **不要在未尝试 降级方案 的情况下接受 🟡 元素。** Workflow §4 强制要求尝试 降级方案 并复扫;直接接受 🟡 视为不合规
- **不要编造 红线 §N 文号。** cn-content-rules.md 中带 `*estimated*` 的阈值必须保留该标记 —— 不允许为了显得权威而删除标记或编造具体文号
- **不要在 body 中引入新模型名。** 若需引用具体模型,必须先加入 `_shared/known-external-models.yaml` allowlist;否则一律用占位符(防止 `verify_skill_references.py` 误报)
