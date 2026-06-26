---
name: deep-research
description: "Multi-round deep research with configurable search iterations and thinking depth (quick/medium/deep). Generates structured reports with citations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Deep-Research, Multi-Round, Citations, Web-Search, Reports]
    category: research
    related_skills: [arxiv, llm-wiki, multi-search-engine, blogwatcher]
---

# Deep Research Skill

深度研究 — 自动搜索、分析、生成带引用的结构化报告。

## 参数

| 参数 | 选项 | 默认 | 说明 |
|------|------|------|------|
| `search_rounds` | 1-5 | 3 | 搜索迭代轮数 |
| `thinking_depth` | quick / medium / deep | medium | 分析深度 |
| `focus` | 自由文本 | — | 聚焦维度（可选） |

## 快速使用

```
研究主题：2026年 AI Agent 发展趋势
搜索轮次：3
思考深度：deep
聚焦维度：技术、市场、竞争
```

## 工作流程（必须严格遵循）

### Step 1: 问题分解
根据主题和轮次生成子问题列表：
- 1 轮 → 2 个核心问题
- 2 轮 → 4 个问题
- 3 轮 → 6 个问题
- 4-5 轮 → 8-10 个问题

问题应覆盖不同维度（技术/市场/用户/竞争），第 1 轮搜基础，后续轮次基于发现生成新问题。

### Step 2: 搜索（每轮）
每轮选 2-3 个问题，使用 `web_search`（英文关键词优先，中文用 `search_lang="zh-hans"`）。

**降级策略**（当 web_search 失败时）：
1. `web_search` — 首选
2. `web_extract(urls=["https://www.bing.com/search?q=关键词"])` — Bing
3. `web_extract(urls=["https://metaso.cn/search/关键词"])` — 秘塔（中文好用）
4. 如果全部失败 → 报告末尾标注"⚠️ 搜索服务不可用，内容基于模型知识"

**关键规则**：
- 每轮搜索之间不要连续快速调用（避免 rate limit）
- 优先近期内容（Brave 用 `freshness="month"`）
- 搜索关键词要具体，避免太宽泛

### Step 3: 内容抓取
每轮搜索后，用 `web_extract` 抓取 top 3-5 个最相关的页面，提取关键信息、数据、观点。

优先级：官方文档 > 学术论文 > 技术博客 > 新闻媒体

### Step 4: 分析与输出
根据 thinking_depth 按对应格式输出报告（见下方）。

---

## 输出格式

### ⚡ Quick 模式（目标：300-500 字）

```markdown
# [主题] 快速总结

## 一句话定义
[一句话概括核心概念]

## 核心要点
- 要点 1
- 要点 2
- 要点 3

## 关键数据
- 数据 1
- 数据 2

## 核心挑战
- 挑战 1
- 挑战 2

## 来源
1. [标题](URL)
2. [标题](URL)
```

**禁止**：不要写长段落、不要写对比表格、不要写建议。

### 📊 Medium 模式（目标：800-1500 字）

```markdown
# [主题] 研究报告

## 摘要
[2-3 句总结核心发现]

## 主要发现

### [方面 A]
- 发现 1（附数据支撑）
- 发现 2

### [方面 B]
- 发现 1
- 发现 2

## 对比分析
| 维度 | 选项 1 | 选项 2 |
|------|--------|--------|
| 优点 | ... | ... |
| 缺点 | ... | ... |

## 结论
[总结性结论 + 简要建议]

## 来源
1. [标题](URL) — 关键观点
2. [标题](URL) — 数据来源
```

**禁止**：不要写"批判性评估"、不要写"方法论说明"、不要写"未来展望"。保持简洁实用。

### 🔬 Deep 模式（目标：2000-4000 字）

```markdown
# [主题] 深度研究报告

## 执行摘要
- 核心结论（3-5 条）
- 关键数据
- 主要建议

## 背景与上下文
[研究背景，1-2 段]

## 主要发现

### 发现 1: [标题]
- 证据/数据支撑
- 来源与可信度

### 发现 2: [标题]
...

## 多维度分析

### [维度 A：如技术]
- 现状 → 趋势 → 挑战

### [维度 B：如市场]
- 规模 → 增长 → 竞争格局

### [维度 C：如用户]
- 需求 → 痛点 → 机会

## 批判性评估
- 主流观点 vs 反对观点
- 数据局限性
- 潜在偏见

## 行动建议
- 短期（0-3 个月）
- 中期（3-12 个月）
- 长期（1 年以上）

## 未来展望
[预测 + 不确定性分析]

## 来源
1. [标题](URL) - 日期 - 可信度: 高/中/低
2. ...

## 方法论说明
- 搜索策略
- 数据收集范围
- 分析局限性
```

---

## 使用场景速查

| 场景 | 推荐配置 | 预计时间 |
|------|----------|----------|
| 快速了解概念 | rounds=1, depth=quick | 1-2 分钟 |
| 技术选型 | rounds=2, depth=medium | 3-5 分钟 |
| 行业趋势 | rounds=3, depth=medium | 5-7 分钟 |
| 深度技术研究 | rounds=4, depth=deep | 8-15 分钟 |
| 竞品分析 | rounds=5, depth=deep | 10-15 分钟 |

## 触发词

"研究 [主题]" / "深度调研 [主题]" / "帮我分析 [主题]" / "对比 [A] 和 [B]"

## 实现说明

此 Skill 使用 Hermes 内置能力：
- `web_search` — 网络搜索
- `web_extract` — 网页抓取（也是降级搜索工具）
- `pdf` — PDF 分析（如需）
- LLM — 内容分析与报告生成

无需额外安装。

## 使用示例

参见 `references/examples.md` 了解 Quick / Medium / Deep 三种模式下的完整输入输出示例。
