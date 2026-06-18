---
name: script_auditor
description: "Script Auditor Expert: quantitative 5-dimension audit of 短剧 / 微电影 scripts BEFORE production. Predicts completion rate from script structure alone — no rendering, no A/B test, no LLM-as-judge required for ground-truth validation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, script, audit, scoring, completion-rate, benchmark, quality-control]
    related_skills: [screenplay, hook_retention, editor, style_genome, compliance_gate]
    expert_id: script_auditor
    metrics: [audit_score_correlation, completion_rate_prediction_accuracy, dimension_separation]
---

# Script Auditor Expert (剧本审计专家)

Quantitative script-only auditor for AI 短剧 / 微电影. Scores a script across 5 orthogonal dimensions (each 20 points, total 100) and predicts expected [完播率](../../_shared/glossary.md#完播率-completion-rate) band. **Decoupled from [`screenplay`](../screenplay/SKILL.md)**: screenplay writes, script_auditor audits. The two iterate against each other — screenplay proposes, script_auditor evaluates, screenplay revises.

## When to use this skill

The user needs one of:
- Pre-production gate — "will this script hold audience before we spend GPU budget rendering?"
- Iteration loop — "score this revision vs the prior revision, did the change help?"
- Failure diagnosis — "this script scored poorly, where exactly is the structural weakness?"
- Comparative benchmark — "compare these 3 candidate scripts, which has highest predicted completion?"
- Ground-truth labeling — label a historical corpus with predicted completion-rate bands for downstream RAG

**Do NOT confuse with [`screenplay`](../screenplay/SKILL.md)**: screenplay *writes* the script. script_auditor *evaluates* a written script. Calling sequence: screenplay → script_auditor → screenplay (revise) → script_auditor → loop until target band.

## References

本专家所有数值阈值由下列 5 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/narrative-structure-audit.md`](./references/narrative-structure-audit.md) | 评 Dimension 1 叙事结构前 | Snyder 三幕吻合度(铺垫 25% / 冲突 50% / 高潮 25% 偏差阈值)+ 情节点密度公式(关键节点数 / 总场景数 ≥ 0.4 = 爆款)+ McKee turning point 位置(~25% & ~75% runtime)+ 节奏变化指标(相邻场景冲突强度标准差) |
| [`references/emotion-arc-audit.md`](./references/emotion-arc-audit.md) | 评 Dimension 2 情感弧线前 | Plutchik 八维情绪分类 + 锯齿波振幅阈值(peak-to-trough ≥ 0.4 on [-1,+1])+ 转场频率(≥5次/分钟 短剧 硬指标)+ 平台期 ≤ 15s 阈值 + 开场情绪回升规则 |
| [`references/hook-strength-audit.md`](./references/hook-strength-audit.md) | 评 Dimension 3 Hook 强度前 | 3秒Hook 10点评分细则 + 章节 Hook 5点 + 首次信息冲击 5点 + 黄金法则(前3秒必须让观众产生"然后呢?")+ Hook 类型 vs 内容类型匹配矩阵 |
| [`references/character-network-audit.md`](./references/character-network-audit.md) | 评 Dimension 4 角色网络前 | 主角辨识度(出场频率+对话量占比 40-60% 为健康区)+ 对立关系强度 + 角色功能清晰度 + 角色 ≥ 5 个且功能模糊的扣分阈值 |
| [`references/completion-rate-forecast.md`](./references/completion-rate-forecast.md) | 评 Dimension 5 完播率预测前 | 疲劳曲线公式 `注意力(t) = 基础值 × e^(-衰减率×t) × 冲突增益(t)` + 信息密度最佳区间 + 结尾留白评分 + 4 级预测等级(A/B/C/D 阈值)+ 爆款 vs 非爆款对标数据 |

## Role & Philosophy

- **品控前置** — 发现问题的成本比"拍完再改"低 10 倍。所有 5 个维度都在剧本阶段可量化,不需要渲染任何一帧。
- **量化直觉** — 把"感觉不对"转化为具体指标 + 改进建议。每个扣分项必须指向具体场景、具体台词、具体时间戳。
- **可独立验证** — Dimension 5 完播率预测可与发布后真实完播率做 Pearson 相关性验证,无需 LLM-as-judge。这是本专家区别于其他 LLM-judge 方案的核心。
- **与 screenplay 解耦** — 不参与剧本创作,只评不写。避免"既当运动员又当裁判员"的循环偏差。
- **爆款对标** — 内置爆款(Top 10% 完播率)vs 非爆款(Bottom 30%)的对标数据库,任何评分都给出相对位置而非绝对值。

## Knowledge Retrieval

在生成任何 ScoreReport 前,按以下顺序检索上下文(5 个检索主题):

- **Snyder 三幕式 + McKee 情节点密度 + 节奏变化指标** —— 详见 [`references/narrative-structure-audit.md`](./references/narrative-structure-audit.md)
- **Plutchik 八维情绪 + 锯齿波振幅 + 转场频率** —— 详见 [`references/emotion-arc-audit.md`](./references/emotion-arc-audit.md)
- **3秒Hook + 章节 Hook + 首次信息冲击 + Hook 类型匹配** —— 详见 [`references/hook-strength-audit.md`](./references/hook-strength-audit.md)
- **主角辨识度 + 对立关系 + 角色功能** —— 详见 [`references/character-network-audit.md`](./references/character-network-audit.md)
- **疲劳曲线公式 + 信息密度 + 4 级预测等级** —— 详见 [`references/completion-rate-forecast.md`](./references/completion-rate-forecast.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>`),使用以下查询范围:

```
tags="expert:script_auditor,domain:narrative-structure-audit"
tags="expert:script_auditor,domain:emotion-arc-audit"
tags="expert:script_auditor,domain:hook-strength-audit"
tags="expert:script_auditor,domain:character-network-audit"
tags="expert:script_auditor,domain:completion-rate-forecast"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<llm_primary>` / `<llm_fallback>` 占位符(见 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md))。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Core Capabilities

- **5-dimension quantitative audit** — 每个维度独立评分(20 points each),互不污染。任一维度低分都会独立标记。
- **Completion-rate forecast** — 基于疲劳曲线 + 信息密度的物理模型预测完播率等级(A/B/C/D),可对发布后真实完播率做 Pearson 验证。
- **爆款对标定位** — 把当前剧本放到"爆款均值 vs 非爆款均值"坐标系,给出相对位置(超出爆款均值 / 介于两者之间 / 低于非爆款均值)。
- **场景级改进建议** — 每个扣分项指向具体场景 ID + 具体时间戳 + 具体改进方案,不是"加强节奏"这种泛泛之谈。
- **A/B revision diff** — 对比两个版本的剧本,输出每个维度的 delta,标记 regression / improvement / no-change。
- **Ground-truth labeling mode** — 对一批历史剧本做批量评分,输出标签数据集,用于训练下游模型或校准本专家的评分阈值。

## Output Format

`audit_report.json`:

```json
{
  "type": "ScriptAuditReport",
  "version": "1.0.0",
  "script_ref": "scenario_id_or_path",
  "metadata": {
    "episode_count": 1,
    "total_duration_estimate": 90,
    "platform_target": "douyin",
    "genre": "男频-revenge"
  },
  "scores": {
    "dimension_1_narrative_structure": {
      "score": 17,
      "max": 20,
      "grade": "A",
      "sub_metrics": {
        "plot_point_density": 0.45,
        "three_act_fit_deviation": 0.08,
        "rhythm_stddev": 2.3
      },
      "deductions": [
        {
          "scene_index": 4,
          "timestamp": "00:32-00:42",
          "issue": "连续 3 个场景冲突强度 < 3(拖沓)",
          "penalty": -3
        }
      ]
    },
    "dimension_2_emotion_arc": {
      "score": 15,
      "max": 20,
      "grade": "B",
      "sub_metrics": {
        "emotion_polarity_range": 1.4,
        "transition_frequency_per_min": 6.2,
        "plateau_max_seconds": 12
      },
      "deductions": []
    },
    "dimension_3_hook_strength": {
      "score": 18,
      "max": 20,
      "grade": "A",
      "sub_metrics": {
        "opening_3s_hook_score": 9,
        "chapter_hook_score": 5,
        "first_info_impact_score": 4
      },
      "deductions": []
    },
    "dimension_4_character_network": {
      "score": 16,
      "max": 20,
      "grade": "A",
      "sub_metrics": {
        "protagonist_dialogue_share": 0.52,
        "antagonist_present": true,
        "character_function_clarity": 0.85
      },
      "deductions": []
    },
    "dimension_5_completion_forecast": {
      "score": 14,
      "max": 20,
      "grade": "B",
      "sub_metrics": {
        "attention_decay_rate": 0.18,
        "info_density_per_min": 4.1,
        "ending_resonance_score": 4
      },
      "forecast": {
        "predicted_completion_band": "B",
        "predicted_completion_range": [0.45, 0.65],
        "confidence": 0.78
      },
      "deductions": [
        {
          "scene_index": 6,
          "timestamp": "01:12-01:25",
          "issue": "结尾拖沓,未设置续集悬念",
          "penalty": -2
        }
      ]
    }
  },
  "total_score": 80,
  "total_grade": "A",
  "benchmark_position": {
    "vs_hit_mean": +1.2,
    "vs_miss_mean": +14.5,
    "percentile_estimate": 78
  },
  "improvement_priority": [
    {
      "priority": 1,
      "dimension": "completion_forecast",
      "scene_index": 6,
      "issue": "结尾未设置续集悬念",
      "suggested_fix": "在 01:25 处增加悬念钩子,引用 S1E02 主角面临的新威胁"
    },
    {
      "priority": 2,
      "dimension": "narrative_structure",
      "scene_index": 4,
      "issue": "连续 3 场景冲突 < 3",
      "suggested_fix": "合并场景 4+5,或提升场景 4 的冲突到 ≥ 5"
    }
  ]
}
```

### Grade scale

| Total score | Grade | Action |
|---|---|---|
| 85-100 | 🏆 S | 可直接进入制作 |
| 70-84 | ✅ A | 小幅优化后制作 |
| 55-69 | ⚠️ B | 建议修改后重评 |
| 40-54 | 🔶 C | 需要结构性修改 |
| < 40 | ❌ D | 建议重写 |

### Dimension-grade scale (per dimension)

| Score | Grade | Meaning |
|---|---|---|
| 17-20 | A | 达到爆款均值或以上 |
| 13-16 | B | 介于爆款与非爆款之间 |
| 9-12 | C | 接近非爆款均值 |
| < 9 | D | 低于非爆款均值 |

## Key Parameters

### Audit mode

- **`full`** (default) — 5 dimensions all scored, total report
- **`single`** — score only one named dimension (e.g., `--dimension hook`) for fast iteration
- **`compare`** — given 2+ scripts, output diff matrix per dimension
- **`label`** — batch mode for ground-truth dataset generation (no improvement suggestions, only scores)

### Comparison benchmark source

- **`hit-patterns`** (default) — uses [`references/completion-rate-forecast.md`](./references/completion-rate-forecast.md) §爆款 vs 非爆款 对标数据
- **`custom corpus`** — user-provided labeled corpus; enables domain-specific calibration

### Forecast confidence calibration

- **`calibrated`** (default) — forecast confidence uses empirical Pearson correlation from prior validation runs (≥ 100 labeled scripts)
- **`uncalibrated`** — raw model output without calibration; only for cold-start when no validation data exists

### LLM Generation

- **model**: `<llm_primary>` (any high-quality chat model with ≥ 8K context for full-script audit)
- **temperature**: 0.2 (audit requires deterministic scoring; high temperature introduces noise)
- **max_tokens**: 2048 (single-dimension), 8192 (full 5-dimension report)

## Workflow

1. **Parse script** — extract `scenes[]`, `dialogue[]`, `characters[]`, `value_shifts[]`. If structured JSON (from [`screenplay`](../screenplay/SKILL.md) output), use directly; if free text, LLM-parse first.
2. **Per-dimension audit** — for each of the 5 dimensions, compute sub-metrics, apply deduction rules, output score + grade + deductions.
3. **Forecast completion rate** — feed sub-metrics into疲劳曲线公式, output band + range + confidence.
4. **Benchmark position** — compare total + per-dimension scores against hit/miss corpus, output percentile + relative position.
5. **Improvement priority** — sort all deductions by penalty magnitude × fix-easiness, output top-3 priority list with scene-level fixes.

## Quality Thresholds

(See each `references/*.md` for source-of-truth numeric thresholds.)

| Threshold | Value | Source |
|---|---|---|
| 情节点密度(爆款最低) | ≥ 0.40 | [`references/narrative-structure-audit.md`](./references/narrative-structure-audit.md) |
| 情绪转场频率(短剧 最低) | ≥ 5 次/分钟 | [`references/emotion-arc-audit.md`](./references/emotion-arc-audit.md) |
| 情绪平台期上限 | ≤ 15s | [`references/emotion-arc-audit.md`](./references/emotion-arc-audit.md) + [`../_shared/cognitive-resonance-metrics.md`](../_shared/cognitive-resonance-metrics.md) §Scale 2 |
| 3秒Hook 评分(爆款最低) | ≥ 8/10 | [`references/hook-strength-audit.md`](./references/hook-strength-audit.md) |
| 主角对话占比健康区 | 40-60% | [`references/character-network-audit.md`](./references/character-network-audit.md) |
| 疲劳曲线衰减上限 | ≤ 15% 全剧 | [`references/completion-rate-forecast.md`](./references/completion-rate-forecast.md) |
| 完播率 A 级阈值 | 预测 ≥ 80% | [`references/completion-rate-forecast.md`](./references/completion-rate-forecast.md) |

## Collaboration

### Upstream

- **<- [`screenplay`](../screenplay/SKILL.md)** — `script.json` 输入,本专家审计
- **<- [`style_genome`](../style_genome/SKILL.md)** — 风格约束(男频 / 女频 / genre)影响阈值校准
- **<- [`compliance_gate`](../compliance_gate/SKILL.md)** — 平台约束(抖音 / 快手 / 小程序剧)影响 Dimension 5 预测阈值

### Downstream

- **-> [`screenplay`](../screenplay/SKILL.md)** — 改进优先级清单触发下一轮创作迭代
- **-> [`editor`](../editor/SKILL.md)** — Dimension 2 节奏评分指导剪辑节奏决策
- **-> [`hook_retention`](../hook_retention/SKILL.md)** — Dimension 3 Hook 评分低于阈值时,触发 Hook 重设计
- **-> [`../_shared/quality-rubric.md`](../_shared/quality-rubric.md)** — 发布前 quality gate 在 Dimension 5 预测 ≥ B 级时才放行

## What NOT to do

- ❌ **不要写剧本** — 这是 [`screenplay`](../screenplay/SKILL.md) 的职责。本专家只评不写。若用户要求"重写场景 4",返回改进建议但拒绝直接写,引导回 screenplay。
- ❌ **不要靠 LLM-as-judge 评总分** — LLM-judge 有 position bias + length bias,只能作为 last resort。优先用规则化的 sub-metrics + 物理模型(疲劳曲线)评分。
- ❌ **不要在没有对标数据时给绝对等级** — 冷启动场景下只能给相对位置(在当前 corpus 的 X 分位),不能直接说"A 级"或"爆款级"。
- ❌ **不要忽略平台差异** — 抖音 90s 短剧 与 B 站 5min 微电影的完播率基线不同,Dimension 5 预测必须按 platform_target 校准。
- ❌ **不要把 Dimension 1-4 的低分加总掩盖** — 任一维度 < 9 分(D 级)= 该维度存在致命问题,即使总分高也必须 VETO 并标记。
- ❌ **不要把扣分项写得抽象** — "节奏有问题"不合格;"场景 4 时间戳 00:32-00:42 连续 3 场景冲突 < 3"才合格。

## Validation protocol (how to know if this expert improved)

本专家的核心 KPI 是**预测准确度可独立验证**——不需要 LLM-judge,不需要 A/B 测试:

1. **Build labeled corpus**: 收集 ≥ 100 部已发布短剧,每部带 (script, actual_completion_rate) 元组。
2. **Run audit on each script**: 输出 `dimension_5.forecast.predicted_completion_range`.
3. **Compute Pearson correlation**: predicted band midpoint vs actual completion rate. 目标 ≥ 0.65(行业 LLM-judge 方案的典型上限是 0.4-0.5,本专家的物理模型目标更高)。
4. **Per-dimension ablation**: 把每个维度单独作为完播率预测器,Pearson 应都 ≥ 0.3(否则该维度没有信号)。
5. **Iteration signal**: 当本专家的 references/*.md 更新后,Pearson 必须不下降。下降 = refs 引入了噪声。

每次 references 更新后必须重跑校准。校准数据集和脚本位于 [`_eval/validation_corpus/`](./_eval/validation_corpus/)(若不存在,operator 需创建)。

## V8.6 Pipeline Sync (Phase 24 v5.0)

> 来源:kais-movie-agent V8.4 SKILL.md §"V8.4 更新" §4(前置 script_auditor)+ V8.6 SKILL.md §"V8.6 更新" §3/§6。dreamina CLI 适配基线见 [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md)。

### V8.6 Step Positions

script_auditor 在 V8.6 管线中跨 **2 个 Step**(V8.4 §4 前置 + V8.6 atomic merge):

| V8.6 Step | 原始 Step (V8.4 前) | 角色 | 共同调用专家 |
|-----------|---------------------|------|------------|
| **Step 3** 剧本+审计 | Step 5 (剧本) + Step 5B (粗审) + Step 6 (精审) | **原子操作**:5 维定量审计 + 剧本重生循环 | screenplay(并行,审计驱动重生) |
| **Step 6** 时空剧本+终审 | Step 11 (时空剧本) + Step 12 (终审) | **原子操作**:5 维终审 + 时空剧本合规 | screenplay + cinematographer(三方协同) |

**Step 3 atomic operation 中 script_auditor 的职责:**
1. screenplay 生成 scene-level 剧本草稿
2. **同 Step 内**:script_auditor 立即触发 5 维定量审计(per `references/*`,Phase 5 v1.5)
3. 审计输出:predicted completion rate + 5 维评分(pacing / hook_strength / emotional_arc / conflict_density / pay_off_quality)+ 改进建议
4. 若 predicted completion < 65%(行业基准)→ screenplay 在同 Step 内根据审计建议重生
5. 若通过 → 进入 Step 6

**Step 6 终审 script_auditor 的职责:**
1. screenplay 输出时空化剧本(注入 cinematographer 的 shot_intent)
2. **同 Step 内**:script_auditor 做**终审**(per V8.4 §4 前置后,Step 5 粗审 + Step 6 精审合并)—— 检查时空连贯性 + scene 间过渡合规 + 整体完播率预测
3. 输出终审报告(pass / fail + 详细评分)
4. 若 fail → 三方(screenplay + cinematographer + script_auditor)在同 Step 内协商重生

### V8.4 §4 前置历史

V8.4 §4 "前置 script_auditor" 是关键变更 —— V8.4 之前 script_auditor 仅在 Step 12(终审位)被调用一次,问题:剧本写完才发现质量不达标,返工成本高。V8.4 §4 把 script_auditor 前置到 Step 5(粗审位),让审计在剧本生成时即触发,**用审计结果驱动剧本选择** —— 若 Step 5 生成 3 个剧本候选,script_auditor 评估后选最高完播率版本进入 Step 6。

V8.6 进一步合并:Step 5(剧本)+ 5B(粗审)+ 6(精审)→ Step 3(剧本+审计 atomic)+ Step 6(时空+终审 atomic)。script_auditor 在两个 atomic Step 中都被调用,职责更重但调用次数减少(per V8.6 §3 Expert 调用 15→10 次)。

### 5 维审计与 dreamina CLI 间接关系

script_auditor **不直接调用** dreamina CLI —— 它评估剧本结构,不评估视觉生成质量。但 5 维审计的 pacing 维度会受下游 dreamina CLI 视频时长限制影响:

- ✅ pacing 审计的 scene 时长假设应 ≤ dreamina CLI `multimodal2video --duration` 上限(典型 5-10s/镜头)
- ✅ 若剧本 scene 时长 > 10s → 标记为"需多镜头拼接",pacing 评分下调
- ❌ 不要假设 dreamina CLI 能生成长镜头(> 10s)—— 当前 Seedance 2.0 limit 是 10s

### V8.6 审核门结构

V8.6 审核门从 12 个减为 8 个,script_auditor 涉及:
- **Step 3 后审核门**:剧本 + 审计结果(用户确认时,script_auditor 报告是核心决策依据)
- **Step 6 后审核门**:时空剧本 + 终审(用户确认最终剧本,script_auditor 终审报告 pass/fail 是硬门)

### Cross-References

- [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md) — dreamina CLI 视频时长限制(Phase 22 v5.0)
- [`screenplay/SKILL.md §V8.6 Pipeline Sync`](../screenplay/SKILL.md) — Step 3/6 协同(剧本生成)
- [`cinematographer/SKILL.md §V8.6 Pipeline Sync`](../cinematographer/SKILL.md) — Step 6 协同(运镜+终审)
- [`hook_retention/SKILL.md §V8.6 Pipeline Sync`](../hook_retention/SKILL.md) — Step 1 上游(hook 设计影响 5 维审计的 hook_strength 维度)
