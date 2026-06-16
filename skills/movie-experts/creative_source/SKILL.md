---
name: creative_source
description: "Creative Source Expert: mines structural social narratives from 6 strata layers (institutional / technological / demographic / spatial / intergenerational-contract / psychosocial) producing Story Kernel JSON seeds for realistic 短剧 / 微电影 creation. Decoupled from style_genome — style_genome defines HOW to tell, creative_source defines WHAT to tell by grounding stories in social structural conflicts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, creative, story-kernel, social-narrative, realism, ideation, story-mining]
    related_skills: [style_genome, screenplay, hook_retention, compliance_gate, topic_curator]
    expert_id: creative_source
    metrics: [strata_resonance_depth, bourdieu_field_accuracy, kernel_actionability, unspeakability_calibration]
---

# Creative Source Expert (创意源头专家)

Social-structural story mining specialist for AI 短剧 / 微电影 production. Mines "structural tragedies" — conflicts driven by social forces rather than individual choices — from 6 stratified layers (L1 institutional / L2 technological / L3 demographic / L4 spatial / L5 intergenerational-contract / L6 psychosocial). Produces `StoryKernel` JSON that downstream experts consume as creative seeds. **Decoupled from [`style_genome`](../style_genome/SKILL.md)**: style_genome defines HOW to tell (genre / mood / aesthetic), creative_source defines WHAT to tell (which structural conflict the story embodies). Calling sequence: creative_source → style_genome → screenplay.

## When to use this skill

The user needs one of:
- **现实主义题材挖掘** — find a structural social conflict worth dramatizing
- **Story kernel creation** — produce a `StoryKernel` JSON that grounds a 短剧 / 微电影 in real social tension
- **Multi-strata overlay analysis** — combine 2+ strata to amplify narrative resonance
- **不可言说性 (unspeakability) scoring** — assess how "off-limits" a topic is for mainstream platforms
- **创意源头诊断** — diagnose why a proposed story feels "thin" or "generic" (likely no structural grounding)
- **Daily scanning** — automated daily scan of public data sources for emerging story kernels

**Do NOT confuse with [`screenplay`](../screenplay/SKILL.md)**: screenplay writes the script. creative_source provides the structural story seed (the "why this story matters" grounded in social reality). Without creative_source, screenplay output tends toward cliché / wish-fulfillment / generic tropes.

## References

本专家所有协议与数据源由下列 4 个 refs 独占定义。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/strata-guide.md`](./references/strata-guide.md) | 分析任何地层前 | 六层地层学完整定义(L1 制度/L2 技术/L3 人口/L4 空间/L5 代际契约/L6 心灵)+ 每层理论基础(Foucault / Bourdieu / Braverman / Lefebvre 等)+ 核心分析维度 + 推荐数据源 URL + 典型故事核示例 |
| [`references/story-kernel-schema.md`](./references/story-kernel-schema.md) | 输出 StoryKernel JSON 前 | 完整 schema(strata_layers[] / structural_formula / unspeakability_score / dramatic_potential / target_audience_overlap / downstream_consumers)+ 每字段冻结规则 + 多层叠加协议 |
| [`references/multi-strata-resonance.md`](./references/multi-strata-resonance.md) | 设计多层叠加分析 前 | 多层叠加规则(2 层叠加 = 1+1 > 2 / 3 层叠加 = 共振级跃迁)+ 6 层叠加系数矩阵 + 最佳叠加组合(L1+L4 制度-空间 / L2+L5 技术-代际 / L3+L6 人口-心灵)+ 共振度量化公式 |
| [`references/unspeakability-protocol.md`](./references/unspeakability-protocol.md) | 评估不可言说性 前 | 10 分制评分协议(1=主流安全 / 10=绝对禁忌)+ CN 平台审核红线映射(网信办 / 广电总局 / 抖音 / 快手 / 小红书)+ 不可言说性 vs 商业价值权衡矩阵 + 平台合规降级策略 |

## Role & Philosophy

- **结构性优于个人性** — 个人悲剧容易煽情但缺乏震撼;结构性悲剧(如灵活就业者的"每个选项都通向脆弱")才产生持续共鸣。
- **六层地层是分析框架,不是内容** — 地层提供"在哪里挖"的方向,不提供内容本身。每个地层都有公开数据源和理论支撑。
- **叠加共振 > 单层强度** — 单层故事核可能"尖锐";2-3 层叠加的故事核才有"震撼"。L1+L4 / L2+L5 / L3+L6 是已知最佳叠加组合。
- **不可言说性是必须评估的维度** — 不是所有故事核都能拍。10 分制评分 + 平台合规降级策略,避免创作后期被迫推翻。
- **数据源驱动** — 每个故事核必须可追溯到公开数据源(政策文件 / 人口普查 / 学术研究)。无来源的故事核 = 主观臆测 = 不可信。

## Knowledge Retrieval

在生成任何 StoryKernel 前,按以下顺序检索上下文(4 个检索主题):

- **六层地层定义 + 理论基础 + 数据源 + 示例** —— 详见 [`references/strata-guide.md`](./references/strata-guide.md)
- **StoryKernel schema + 字段冻结 + 多层叠加** —— 详见 [`references/story-kernel-schema.md`](./references/story-kernel-schema.md)
- **多层叠加规则 + 6 层系数矩阵 + 最佳组合** —— 详见 [`references/multi-strata-resonance.md`](./references/multi-strata-resonance.md)
- **不可言说性 10 分制 + 平台审核红线 + 降级策略** —— 详见 [`references/unspeakability-protocol.md`](./references/unspeakability-protocol.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:creative_source,domain:strata-guide"
tags="expert:creative_source,domain:story-kernel-schema"
tags="expert:creative_source,domain:multi-strata-resonance"
tags="expert:creative_source,domain:unspeakability-protocol"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

**数据采集建议:** 若 runtime 有搜索工具(`<web_search>` / `<kais_search>` / `<multi-search-engine>`),按地层推荐数据源(`references/strata-guide.md` 表)采集公开数据。无搜索工具时,基于 refs 中的示例公式构造 StoryKernel,但必须标注 `evidence_strength: low`。

## Core Capabilities

- **六层地层分析** — 对任一社会议题,可从 1-6 层中任意选取并独立分析
- **多层叠加共振** — 把 2-3 层叠加,产生 1+1 > 2 的共振效果(叠加系数矩阵见 [`references/multi-strata-resonance.md`](./references/multi-strata-resonance.md))
- **Story Kernel 提炼** — 把分析结果压缩为单一"结构性公式"(一句话描述不可逆转的结构性冲突)
- **不可言说性评估** — 10 分制评分 + 平台审核红线映射 + 合规降级路径
- **目标受众匹配** — 评估故事核与男频/女频/特定年龄段观众的重叠度
- **戏剧潜力评分** — 评估故事核转化为具体情节的可行性(actionability)+ 情感强度
- **数据源追溯** — 每个故事核必须可追溯到公开数据源,标注证据强度

## Output Format

```json
{
  "type": "StoryKernel",
  "version": "1.0.0",
  "kernel_id": "kernel_<hash>",
  "title_working": "灵活就业者的脆弱选择",
  "strata_layers": [
    {
      "layer": "L1",
      "layer_name": "制度地层 / Institutional",
      "analysis": "灵活就业政策将社保缴纳责任完全转移给个人,但平台经济的不稳定收入使得连续缴纳成为不可能,形成了'有选择权但每个选项都通向脆弱'的制度陷阱。",
      "evidence_sources": [
        {
          "source": "国务院办公厅《关于支持多渠道灵活就业的意见》",
          "url": "https://www.gov.cn/zhengce/...",
          "accessed_date": "2026-06-15",
          "evidence_strength": "high"
        }
      ],
      "structural_question": "谁被规训?谁被豁免?",
      "answer": "灵活就业者被规训为'独立承担社保';平台被豁免为'技术中介'不负雇佣责任。"
    },
    {
      "layer": "L4",
      "layer_name": "空间地层 / Spatial",
      "analysis": "高房价使灵活就业者无法在一线城市扎根,但'人才引进'政策又将有限住房资源优先分配给高学历年轻人,加剧了空间排斥。",
      "evidence_sources": [
        {
          "source": "贝壳研究院《2025 城市住房报告》",
          "url": "https://...",
          "accessed_date": "2026-06-15",
          "evidence_strength": "medium"
        }
      ],
      "structural_question": "谁拥有空间?谁被挤出?",
      "answer": "高学历人才通过政策获得空间准入;灵活就业者被系统性挤出核心城市。"
    }
  ],
  "structural_formula": "灵活就业者获得了'选择自由'的意识形态承诺,但每个选择(交社保/不交;留城/返乡;接单/不接)都通向更深的脆弱;与此同时,他们的劳动结晶(城市住房)被'人才引进'政策重新分配给本就拥有更多资本的人。",
  "strata_overlay_coefficient": 1.8,
  "overlay_amplification": "L1+L4 叠加使故事核从'制度悲剧'升级为'制度-空间双重锁定',共振强度 1+1=1.8(>2 的物理叠加)",
  "unspeakability_score": 7,
  "unspeakability_breakdown": {
    "political_sensitivity": 3,
    "platform_algorithm_risk": 6,
    "audience_discomfort": 5,
    "regulatory_redline": 8
  },
  "platform_compliance_paths": {
    "douyin": "降级为'奋斗故事':主角通过个人努力突破制度限制(去除结构性批判,改为个人英雄叙事)",
    "kuaishou": "可保留部分结构性批判,聚焦'小镇青年'视角",
    "xiaohongshu": "可保留,以女性视角切入,平台对结构性议题相对宽松",
    "wechat_mini": "可保留,小程序剧受众容忍度高"
  },
  "dramatic_potential": {
    "actionability": 0.85,
    "emotional_intensity": 0.80,
    "narrative_compression_fit": 0.75,
    "overall": 0.80
  },
  "target_audience_overlap": {
    "male_25_35": 0.85,
    "female_25_35": 0.70,
    "male_18_25": 0.60,
    "female_18_25": 0.55,
    "male_35_50": 0.80,
    "female_35_50": 0.65
  },
  "downstream_consumers": [
    "style_genome",
    "screenplay",
    "topic_curator",
    "compliance_gate"
  ],
  "created_at": "2026-06-16T14:30:00Z",
  "created_by": "creative_source",
  "evidence_strength_aggregate": "medium-high"
}
```

### Strata overlay scale

| Overlay | Coefficient | Effect |
|---|---|---|
| 1 layer | 1.0 | 单层强度(基础) |
| 2 layers (compatible) | 1.7-1.9 | 共振增强(1+1 > 2) |
| 2 layers (incompatible) | 1.2-1.4 | 简单叠加(接近 1+1 = 2) |
| 3 layers (rare) | 2.5-3.0 | 共振级跃迁(罕见,极强故事核) |
| 4+ layers | < 1.5 | 过载,叙事混乱(避免) |

## Key Parameters

### Strata selection

- **single layer**: user specifies one layer (e.g., "L1 only", "tech-only analysis")
- **multi-layer overlay**: user says "叠加" / "共振" / "综合" or doesn't specify
- **daily scan**: cron-triggered, scan Top N emerging kernels across all layers

### Search strategy (per layer)

| Layer | Recommended engine | Keyword direction |
|---|---|---|
| L1 | 微信搜一搜, 百度 | 政策文件名 + "解读/影响/争议" |
| L2 | Google, Bing INT | English report keywords ("future of jobs" / "automation impact") |
| L3 | 国家统计局, 百度 | "人口普查" + "老龄化/少子化/流动" + 年份 |
| L4 | 贝壳研究院, 百度 | "房价" + "住房/租房/城镇化" + 数据 |
| L5 | 小红书, 知乎, 百度 | "代际消费" + "年轻人 父母" + "囤积/断舍离" |
| L6 | 百度学术, 知乎, 微博 | "心理健康 报告" + "孤独 调查" + "年轻人 意义感" |

### Unspeakability evaluation

- **`<llm_primary>`**: used for unspeakability scoring; temperature 0.2 for consistency
- **scoring rubric**: 4 sub-dimensions (political / platform / audience / regulatory), each 1-10
- **overall**: weighted average, rounded to integer

## Workflow

1. **Determine analysis mode** — single layer, multi-layer overlay, or daily scan.
2. **Identify topic** — from user input OR scan emerging issues from data sources.
3. **Per-layer data collection** — for each layer in scope, search 3-5 keywords from recommended sources.
4. **Per-layer analysis** — apply the layer's core analysis dimensions to data, produce layer_analysis string.
5. **Compose structural formula** — compress multi-layer analysis into one sentence.
6. **Compute strata overlay coefficient** — based on which layers and their compatibility.
7. **Score unspeakability** — 4 sub-dimensions + aggregate.
8. **Generate platform compliance paths** — for each major CN platform, what降级 / reframing is needed.
9. **Score dramatic potential** — actionability + emotional intensity + narrative compression fit.
10. **Compute audience overlap** — for 6 standard demographic segments.
11. **Emit StoryKernel JSON** — full schema with all fields + downstream consumer pointers.

## Quality Thresholds

| Threshold | Value | Source |
|---|---|---|
| Evidence sources per layer | ≥ 1 (≥ 2 recommended) | [`references/strata-guide.md`](./references/strata-guide.md) |
| Structural formula length | 50-200 chars (single sentence) | [`references/story-kernel-schema.md`](./references/story-kernel-schema.md) |
| Multi-layer overlay coefficient (resonant) | ≥ 1.7 for 2-layer | [`references/multi-strata-resonance.md`](./references/multi-strata-resonance.md) |
| Unspeakability score range | 1-10 integer | [`references/unspeakability-protocol.md`](./references/unspeakability-protocol.md) |
| Unspeakability VETO threshold | ≥ 9 (cannot be made on any major platform) | [`references/unspeakability-protocol.md`](./references/unspeakability-protocol.md) |
| Dramatic potential overall | ≥ 0.65 for production-worthy | [`references/story-kernel-schema.md`](./references/story-kernel-schema.md) |
| Target audience max overlap | ≥ 0.70 for at least 1 demographic | [`references/story-kernel-schema.md`](./references/story-kernel-schema.md) |

## Collaboration

### Upstream

- **<- (none)** — creative_source is the DAG root; no upstream expert
- **<- `<web_search>` / `<kais_search>`** — runtime tools for data collection (optional but recommended)

### Downstream

- **-> [`style_genome`](../style_genome/SKILL.md)** — StoryKernel's `structural_formula` + `target_audience_overlap` inform genre / mood selection
- **-> [`screenplay`](../screenplay/SKILL.md)** — StoryKernel's `dramatic_potential` + `strata_layers` inform scene design + character motivation
- **-> `topic_curator` (future)** — multiple StoryKernels feed topic selection
- **-> [`compliance_gate`](../compliance_gate/SKILL.md)** — StoryKernel's `unspeakability_score` + `platform_compliance_paths` inform distribution strategy

## What NOT to do

- ❌ **不要在没有数据源的情况下生成故事核** — 每个故事核必须可追溯。evidence_strength 标注为 "low" 的故事核是 degraded 模式。
- ❌ **不要把 6 层全部叠加** — 4+ 层叠加 < 1.5,叙事混乱。最多 3 层(且 3 层是罕见情况)。
- ❌ **不要忽略不可言说性** — 不可言说性 ≥ 9 的故事核必须 VETO,即使戏剧潜力高。后期被迫推翻成本极大。
- ❌ **不要把 structural_formula 写成抽象社会学论文** — 50-200 字单句,描述具体的不可逆冲突,不是抽象分析。
- ❌ **不要把所有故事核都打成高戏剧潜力** — dramatic_potential.overall 应该有 variance;过高的平均分说明评分不严谨。
- ❌ **不要在 SKILL.md body 引用具体平台名** — `抖音` / `快手` 等具体平台名只在 references/unspeakability-protocol.md 中作为审核红线参考。SKILL.md 用 `<cn_platform_target>` 占位符。

## Validation protocol (how to know if this expert improved)

本专家的核心 KPI 用人工标注 + Bourdieu 场域客观指标量化:

1. **Build labeled corpus**: 收集 ≥ 100 个社会议题,每个由 3 位社会学/影视专业评估者独立标注故事核质量(0-1) + 多层共振度 + 不可言说性。
2. **Run creative_source** on each topic, output StoryKernel JSON。
3. **Compute strata resonance correlation**: 预测的 overlay_coefficient vs 评估者共振度评分的 Pearson 相关性。Target ≥ 0.55。
4. **Compute Bourdieu field accuracy**: 检查 L1 分析是否正确识别了"规训对象"与"豁免区域"(对照 Foucault/Bourdieu 标注)。Target ≥ 0.75。
5. **Compute unspeakability calibration**: 预测的 unspeakability_score vs 平台实际审核结果的 AUC。Target ≥ 0.80。
6. **Compute kernel actionability**: 故事核被下游 screenplay 成功转化为 ≥ 90s 短剧的比例。Target ≥ 60%。

**Iteration signal**: 当 references/*.md 更新后,所有指标必须不下降。

校准数据集和脚本位于 [`_eval/creative_source_benchmark/`](./_eval/creative_source_benchmark/)(若不存在,operator 需创建并标注 ≥ 100 个议题)。
