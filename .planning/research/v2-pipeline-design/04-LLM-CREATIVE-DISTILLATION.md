# 04 — LLM Creative Distillation Deep-Dive

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 10 of v2.0 PRFP · **Source:** derives from `00-FIRST-PRINCIPLES.md` §3.4 (Q4 answer) + §2.5 (forward-reference) + `02-NODE-SPECS.md` §2.1/§2.3/§2.4 (creative_source / screenplay / script_auditor)
> **Stability:** experimental (per Phase 7 §1.7 — creativity definition is the most fluid dimension)

---

## §0 — 阅读指南

本文档是 v2.0 PRFP 设计套件中的 **LLM 创意凝练专题**(PROJECT.md 里程碑上下文目标 #4)。它解决用户特别强调的洞察层:"大模型如何产出**有创意且逻辑自洽**的故事框架"。

**前置阅读:** `00-FIRST-PRINCIPLES.md` §3.4 D4.1(创意意图起源不可还原)+ §2.5(forward-reference to Phase 10)+ `02-NODE-SPECS.md` §2.1(creative_source 节点 spec)

**章节地图:**
- §1 创意的操作性定义(novelty within inviolable constraints)
- §2 自洽性检验机制(consistency-context + logic-critic)
- §3 LLM 凝练 prompt 策略(引用 STACK §5 ≥3 篇论文)
- §4 Fail modes(PITFALLS §4.1-4.7 全部走查)
- §5 平台 vs 艺术张力(无教条处理)
- §6 模板库(多模板,不单一 Save-the-Cat)
- §7 Novelty-pressure 机制(链接回 creative_source 节点)
- §8 Open questions(喂给 Phase 12 OPEN-QUESTIONS.md)
- References

---

## §1 — 创意的操作性定义

### §1.1 — 为什么需要操作性定义

"创意"在 AIGC 上下文中常常被默认为"不重复训练数据"或"高 temperature 采样" — 但这两个定义都会导向 **随机性**(randomness),不是创意。本节给出可机器化、可审计的创意定义。

### §1.2 — 核心定义

**创意 = 在不可侵犯约束内的 novelty。**

具体:
- **不可侵犯约束(inviolable constraints)** = 创意必须满足的硬约束,违反即失败(不是低分)
- **novelty(新颖性)** = 在所有满足约束的解空间中,选择"罕见但有效"的解(不是"任意但合规")

**关键区分(防 PITFALLS §4.5 creative-vs-random 混淆):**

| 维度 | Randomness | Creativity |
|---|---|---|
| 约束 | 忽略 | 必须满足 |
| 解空间 | 全空间 | 满足约束的子空间 |
| 评价 | 不可预测 | 可评价(约束满足 + novelty 分数) |
| 失败模式 | 输出无意义 | 输出 cliché(novelty 不足)或 约束违反 |

**经典案例:**
- **不是创意:** "让 LLM 高 temperature 自由发挥写短剧" → 输出可能是无意义的高方差 token 序列
- **是创意:** "在 [Field 三幕结构 + 角色动机一致 + 平台时长 ≤ 90s + 拒绝 Save-the-Cat 模板] 约束下,选择 5 个候选中 novelty 分数最高的"

### §1.3 — 不可侵犯约束(inviolable constraints)清单

per Phase 7 §3.4 D4.3,以下约束是 **validated-invariant**,创意不能违反:

1. **叙事闭合(setup-payoff closure)** — Field 三幕结构要求每个 setup 都有 payoff
2. **角色动机一致(character motivation consistency)** — 角色的行动必须从其欲望 + 信念可推导
3. **时间线一致(timeline consistency)** — 事件因果链不能矛盾
4. **场景内一致(scene-level consistency)** — 场景中的对象、空间、人物状态不能漂移
5. **形态约束(form constraints)** — 短剧 ≤ 90s/集 + 竖屏 + 单场景为主;微电影 5-30 分钟 + 横屏;长片 90+ 分钟
6. **平台合规(platform compliance)** — CN 平台审核规则(政治敏感词、涉黄涉暴阈值、广告法)

### §1.4 — novelty 的测量

novelty 必须可量化(防 PITFALLS §4.5 模糊定义):

```yaml
novelty_score:
  definition: "1 - max_similarity_to_known_patterns"
  measurement:
    known_patterns:  # trope-catalog embedding database
      - save_the_cat_beats:  # 15 个 Blake Snyder beats
      - hero_journey_stages:  # 12 个 Campbell 阶段
      - 短剧_爆款公式:  # 平台算法奖励的 pacing templates
      - kishotenketsu:  # 起承转合 4 段
      - anti_structure:  # 实验性无模板(允许,但标 experimental)
    similarity_metric: "cosine_similarity on structural embedding"
    threshold: "novelty_score >= 0.6 = pass;< 0.6 = cliché flag"
```

novelty_score ≥ 0.6 不是创意的"上限" — 它是创意的"下限"。≥ 0.6 进入围栏,低于 0.6 触发 regeneration。

### §1.5 — 创意的"开放维度"(open dimensions)

创意不能在所有维度都开放(否则随机),只能在 **特定维度** 开放:

- ✅ **开放维度(允许 novelty):** POV 选择、structural inversion、trope-subversion、thematic angle、character archetype 选择
- ❌ **关闭维度(必须遵守约束):** Field 三幕结构、角色动机、时间线、形态时长、平台合规

设计的 prompt 必须显式标记:开放维度允许 LLM explore;关闭维度必须 satisfy。

---

## §2 — 自洽性检验机制

per CREATIVE-03 + PITFALLS §4.1 + §4.3:每个创意生成节点必须有 **consistency-context input + logic-critic** 双重保障。

### §2.1 — Consistency-context input schema

`consistency-context` 是 **结构化的已建立事实表示**,生成节点必须尊重它(不能违反):

```yaml
consistency_context:
  character_knowledge_state:  # 每个角色在每个时间点知道什么
    - character_id: <id>
      at_scene: <scene_id>
      knows: [<fact_id>, ...]
      does_not_know: [<fact_id>, ...]
  
  timeline:  # 事件因果链
    events:
      - id: <event_id>
        occurs_at: <scene_id>
        causes: [<event_id>, ...]  # 显式因果
        effects: [<event_id>, ...]
  
  stakes:  # 已建立的赌注
    - stake_id: <id>
      established_at: <scene_id>
      payoff_expected_at: <scene_id | unresolved>
      payoff_type: <emotional | plot | thematic>
  
  spatial_layout:  # 场景的空间不变量
    - scene_id: <id>
      layout: <diagram or schema>
      character_positions: {<character_id>: <position>}
      invariant: <what cannot change during scene>
  
  emotional_arc:  # 已建立的情感轨迹
    - scene_id: <id>
      target_emotion: <emotion>
      transition_from: <previous_emotion>
      intensity: <0-1>
```

**生成节点(screenplay + creative_source)的 I/O 修订(per CREATIVE-07 wiring):**

```yaml
# 修订后的 screenplay 节点 io_contract
inputs:
  - name: story_kernel
    source: creative_source
    required: true
  - name: consistency_context  # ← NEW per CREATIVE-03
    source: carries_forward_from_previous_iterations
    required: true  # first iteration = empty; subsequent iterations = audit-feedback-updated
outputs:
  - name: screenplay_full
    consumers: [cinematographer, hook_retention, script_auditor]
    required: true
  - name: consistency_context_updated  # ← NEW: reflects facts established in this draft
    consumers: [script_auditor]
    required: true
```

### §2.2 — Logic-critic specification

`script_auditor` (Phase 8 §2.4) 扮演 logic-critic 角色,但扩展 5-dim rubric 显式检查 consistency_context 违反:

```yaml
script_auditor_dimensions_expanded:
  character_network:  # 已有
    checks: [relationship_consistency, motivation_traceability]
    threshold: 0.85
  plot_holes:  # 已有
    checks: [setup_payoff_closure, causal_chain_completeness]
    threshold: 0.75
  dialogue_naturalness:  # 已有
    threshold: 0.70
  narrative_arc:  # 已有
    threshold: 0.75
  setup_payoff:  # 已有
    threshold: 0.80
  consistency_context_violations:  # ← NEW per CREATIVE-03
    checks:
      - "no character knows fact they should not know"
      - "no event happens before its causal antecedent"
      - "no stake mentioned that was never established"
      - "no spatial-layout violation"
      - "no emotional-arc discontinuity"
    threshold: 0  # ZERO violations tolerated
    on_violation: "regenerate with explicit consistency_context reminder"
```

**Logic-critic 的 evidence base(STACK §5 ≥3 论文 — per CREATIVE-04):**

1. **Plot Hole Detection benchmark (arXiv 2504.11900)** — 提供 plot-hole 检测的 benchmark + LLM 推理评估框架。Logic-critic 的 plot_holes dim 直接采用其检测 schema。
2. **ConStory-Bench (arXiv 2603.05890)** — 长故事一致性 bug 检测,ConStory-Checker LLM-as-judge pipeline。Logic-critic 的 consistency_context_violations dim 采用其 methodology。
3. **CONFACTCHECK (ACL 2025 Findings)** — 无外部 KB 的幻觉检测。Logic-critic 在虚构内容(无 ground-truth KB)上的应用采用 CONFACTCHECK 的 self-consistency 检查思路。

**Logic-critic 输出:**

```yaml
logic_critic_verdict:
  verdict: accept | regenerate | escalate
  per_dim_scores: {...}
  violations:
    - type: <consistency_context_violation_type>
      at: <scene_id | character_id>
      description: <CN prose>
      suggested_fix: <CN prose>
```

---

## §3 — LLM 凝练 prompt 策略

per CREATIVE-04:引用 STACK §5 ≥3 篇 LLM-story-gen 论文 + 给出具体 prompt 模式。

### §3.1 — 论文 evidence base(8 papers from STACK §5)

1. **EMNLP 2025 Survey on LLMs for Story Generation** — 综述;关键 taxonomy:independent generation vs author-assistance paradigm
2. **Learning to Reason for Long-Form Story Generation (OpenReview)** — 长程 plot + character arc reasoning
3. **Awesome-Story-Generation (GitHub)** — 一站式文献索引
4. **Plot Hole Detection (arXiv 2504.11900)** — plot-hole benchmark
5. **ConStory-Bench (arXiv 2603.05890)** — 一致性 bug 检测
6. **CONFACTCHECK (ACL 2025)** — 幻觉检测(无外部 KB)
7. **ACM Creator-Centric Methods** — creator-side gaps
8. **IASDR Scaffolding the Story** — LLM-as-evaluator for writing assessment

### §3.2 — 6 个核心 prompt 模式

per evidence base,提取 6 个适用于 v2.0 凝练的 prompt 模式:

**Pattern 1: Independent vs Author-Assistance 选取(per EMNLP Survey)**

```yaml
# 在 creative_source 节点应用
pattern: "force_author_assistance_mode"
prompt_template: |
  你不是独立的剧本生成器,你是创作者的凝练助手。
  
  创作者提供的 anecdote:
  {creator_anecdote}
  
  你的任务:把 anecdote 凝练为 story kernel,而不是发明新的故事。
  禁止:引入 anecdote 中没有的人物、地点、事件。
  允许:补全 logline + 主角欲望 + 中央冲突 + 转折点 + 解决立场的结构。
```

**Pattern 2: Reasoning-then-Generate(per Learning to Reason)**

```yaml
# 在 screenplay 节点应用
pattern: "reason_before_write"
prompt_template: |
  在写场景 {scene_id} 之前,先输出 reasoning:
  - 这个场景的 setup(承接上文什么)
  - 这个场景的 payoff(为下文铺垫什么)
  - 角色动机:为什么 {character_id} 在这里这样做
  - consistency_context 影响:这个场景改变了什么 fact
  
  然后才输出场景本身。
```

**Pattern 3: Trope-Aware Anti-Cliché(per ConStory-Bench + CONFACTCHECK)**

```yaml
# 在 screenplay + creative_source 应用
pattern: "explicit_anti_trope"
prompt_template: |
  避免 trope-catalog 中的以下模板:
  - Save-the-Cat beat #4 (B-story romance): 禁用
  - 短剧"逆袭打脸"模板: 禁用
  - Hero's Journey 拒绝召唤: 禁用(本作不适用)
  
  你的输出会被 trope-catalog embedding 检查;novelty_score < 0.6 触发 regenerate。
```

**Pattern 4: Consistency-Context-Aware Generation**

```yaml
# 在 screenplay 应用
pattern: "respect_consistency_context"
prompt_template: |
  已建立的 consistency_context:
  {consistency_context_yaml}
  
  你写的场景不能违反上述任何 fact。具体:
  - {character_id} 在 {scene_id} 不能知道 {fact_id}(他/她在 {later_scene} 才知道)
  - {event_id} 必须发生在 {earlier_event} 之后
  - {stake_id} 在 {payoff_scene} 必须有 payoff
  
  违反任意一条 = 失败。
```

**Pattern 5: Template Library Selection(per CREATIVE-06)**

```yaml
# 在 creative_source 应用
pattern: "select_template_first"
prompt_template: |
  从模板库选择一个 narrative arc template:
  1. classical_3_act (Field)
  2. save_the_cat_15_beats (Blake Snyder)
  3. hero_journey_12 (Campbell)
  4. kishotenketsu_4 (起承转合)
  5. 短剧_爆款公式 (platform-tuned)
  6. anti_structure (experimental;requires novelty_score >= 0.8)
  
  选择理由(必须):
  - 为什么选这个模板而不是其他?
  - 这个模板如何 fit 创作者的 anecdote?
  
  选择后:按模板 structure 凝练 story kernel。
```

**Pattern 6: Critic-Loop Aware Generation**

```yaml
# 在 screenplay 应用
pattern: "regenerate_with_audit_feedback"
prompt_template: |
  上次输出被 script_auditor 拒绝。violations:
  {violations_list}
  
  regenerate 时:
  - 必须修复上述每个 violation
  - 不能引入新 violation(consistency_context 仍生效)
  - 保持 novelty_score >= 0.6
  - 保持模板 selection
  
  输出新版本 + 修复 changelog。
```

### §3.3 — Pattern 组合

实际凝练流程组合使用:

```
creative_source 节点:
  Pattern 1 (force_author_assistance_mode)
  + Pattern 3 (explicit_anti_trope)
  + Pattern 5 (select_template_first)

screenplay 节点:
  Pattern 2 (reason_before_write)
  + Pattern 3 (explicit_anti_trope)
  + Pattern 4 (respect_consistency_context)
  + Pattern 6 (regenerate_with_audit_feedback)  [仅在 regenerate iteration]

script_auditor 节点:
  ConStory-Bench 检测 schema + CONFACTCHECK consistency 检查
```

---

## §4 — Fail Modes(PITFALLS §4.1-4.7 全部走查)

per CREATIVE-01 dim 4(fail modes):本节走查 7 个 fail mode + 对应缓解。

### §4.1 — Hallucinated logic(plot 与 setup 矛盾)

- **Trigger:** LLM token-by-token 生成,缺全局一致性模型
- **Impact:** 场景内合理,跨场景矛盾(角色知道不该知道的、时间线不连续、stake 消失)
- **Mitigation:** consistency_context input(§2.1)+ logic-critic(§2.2)+ Pattern 4 prompt

### §4.2 — Shallow narrative(cliché from training data)

- **Trigger:** LLM 训练数据主导,无 novelty pressure
- **Impact:** 输出表面不同,结构相同(Save-the-Cat 翻版)
- **Mitigation:** Pattern 3 anti-trope prompt + novelty_score 阈值 + trope-catalog embedding 检查

### §4.3 — Lack of self-consistency verification

- **Trigger:** 信任 LLM 第一稿,无 critic
- **Impact:** 不一致到 storyboard / final video 才发现,修复成本 10-100x
- **Mitigation:** §2 完整机制(consistency_context + logic-critic + screenplay↔script_auditor loop)

### §4.4 — "More details" mistaken for "richer story"

- **Trigger:** prompt 要求 exhaustive detail(全 character bio + 全 prop 列表)
- **Impact:** prompt 膨胀,LLM 注意力稀释,故事密集但情感 flat
- **Mitigation:** minimal viable story structure(只 logline + 主角欲望 + 中央冲突 + 转折点 + 解决立场)+ 下游节点 on-demand 拉取更多 detail

### §4.5 — Creative confused with random

- **Trigger:** prompt 移除约束 "let LLM surprise us"
- **Impact:** 输出随机,不是创意
- **Mitigation:** §1 操作性定义(创意 = 在约束内的 novelty)+ 区分开放/关闭维度

### §4.6 — Template over-reliance(单一 Save-the-Cat)

- **Trigger:** 硬编码单一 template
- **Impact:** 输出多样性塌缩,每个短剧结构相同
- **Mitigation:** §6 template library(≥4 模板)+ Pattern 5 select_template_first

### §4.7 — 短剧 conventions vs artistic merit

- **Trigger:** 两个极端:完全忽视平台 convention,或过度 dogma 爆款公式
- **Impact:** 平台分发失败 或 艺术价值丧失
- **Mitigation:** §5 平台 vs 艺术张力的非教条处理

---

## §5 — 平台 vs 艺术张力(非教条处理)

per CREATIVE-05 + PITFALLS §4.7:平台优化 vs 艺术价值的张力必须 **显式处理**,不单方面选边。

### §5.1 — 两端的失败模式

| 极端 | 表现 | 失败 |
|---|---|---|
| 平台 dogma | 完全追逐完播率 + 付费卡点 + 爆款公式 | 输出 algorithmically-optimized 但 artistically-empty,短赢不长 |
| 艺术 dogma | 完全无视平台 convention,纯 auteur 风格 | 短剧平台不分发,观众看不到,艺术价值无载体 |

### §5.2 — 非教条的张力处理

设计的 `creative_source` 节点接受 **两个并行 input**:

```yaml
creative_source_inputs:
  - platform_context:  # 平台 convention(短剧/微电影/长片 + 平台 spec)
      type: enum + structured
      activates:
        - 短剧: { hook_timing: 3s, pacing: fast, framing: vertical, ... }
        - 微电影: { narrative_arc: full_3_act, framing: horizontal, ... }
        - 长片: { ... }
  
  - artistic_intent:  # 创作者艺术意图
      type: structured_text
      includes:
        - thematic_focus: <theme>
        - pov_choice: <pov>
        - reference_works: [<films>, ...]  # 创作者心中的 reference
        - anti_patterns: [<things to avoid>]  # 创作者拒绝的 trope
```

**当 platform_context 与 artistic_intent 冲突时:**

1. 优先 **artistic_intent** in open dimensions(POV、主题、trope-subversion)
2. 优先 **platform_context** in inviolable constraints(形态时长、平台合规)
3. **theory_critic** 作为仲裁:当冲突在灰色地带(如 pacing),creator-pulled theory_critic 提供 both 视角分析,creator 做最终判断

### §5.3 — 短剧 specific 处理

短剧形态下,张力最尖锐(完播率生死线 vs 艺术价值)。设计的 `hook_retention` 节点(Phase 8 §2.13)的角色是:

- **不是** 自动 chase 完播率(dogma)
- **不是** 忽略完播率(脱离平台)
- **而是** 评估当前 screenplay 的 hook 强度 + 给 screenplay 节点 feedback,让 screenplay 重写时显式权衡

这避免了平台 dogma 自动叠加,保留了 artistic_intent 的空间。

---

## §6 — 模板库(per CREATIVE-06)

per PITFALLS §4.6 + CREATIVE-06:template library 必须包含 **多个** 叙事弧模板,不是单一 Save-the-Cat。

### §6.1 — 模板库清单(6 模板)

| Template | 来源 | 适用形态 | novelty 默认 | 选择场景 |
|---|---|---|---|---|
| `classical_3_act` | Field《剧本》 | universal | 0.5 | 创作者要 classical 叙事 |
| `save_the_cat_15` | Blake Snyder | universal (长片强) | 0.4 | 商业类型片 |
| `hero_journey_12` | Campbell | universal | 0.4 | 神话结构题材 |
| `kishotenketsu_4` | 起承转合(东亚) | 短剧 + 微电影 | 0.7 | 东亚审美 + 短形态 |
| `短剧_爆款公式` | 平台算法驱动 | 短剧 only | 0.3 | 商业短剧 |
| `anti_structure` | Vogler + experimental | experimental only | 0.9 | 艺术片 / 实验 |

### §6.2 — 模板 schema

每个 template 是结构化的:

```yaml
template:
  id: kishotenketsu_4
  name: 起承转合
  origin: 东亚叙事传统
  applicable_forms: [short_drama, 微电影]
  stages:
    - id: ki  # 起
      function: "establish setting + characters"
      length_share: 0.20
    - id: sho  # 承
      function: "develop expected trajectory"
      length_share: 0.30
    - id: ten  # 转
      function: "introduce unexpected turn (the 'twist')"
      length_share: 0.30
    - id: ketsu  # 合
      function: "resolve with new understanding"
      length_share: 0.20
  novelty_default: 0.7  # 因为西方 LLM 训练数据中较少见,默认 novelty 高
  compatible_with: [creative_source, screenplay]
```

### §6.3 — Template 选择决策

`creative_source` 节点的 Pattern 5 prompt 强制创作者(或 AI 建议)在 6 个模板中选择 + 说明理由。这避免了"模板默认"导致的多样性塌缩。

### §6.4 — Anti-structure 特殊处理

`anti_structure` 模板的 novelty_default = 0.9,但需要 **extraordinary justification**:
- 创作者明确选择(experimental intent)
- novelty_score >= 0.8(强制高 novelty)
- theory_critic consultation 触发(因为 anti-structure 是 artistic intent 的强声明)

---

## §7 — Novelty-pressure 机制(链接回 creative_source)

per CREATIVE-07:novelty 不能浮空,必须 **链接回 `creative_source` 节点**。

### §7.1 — Novelty-pressure 在 DAG 中的位置

```
creative_source (root)
  ↓ 输出 story_kernel + novelty_constraint
screenplay
  ↓ 消费 novelty_constraint + consistency_context
script_auditor
  ↓ 检查 novelty_score + consistency_violations
  ↑ regenerate if novelty < 0.6 OR consistency violations
```

### §7.2 — `novelty_constraint` schema(creative_source 输出扩展)

```yaml
# 在 creative_source 的 outputs 中新增
outputs:
  - name: story_kernel
    ...
  - name: novelty_constraint  # ← NEW per CREATIVE-07
    type: structured
    consumers: [screenplay]
    required: true
    schema:
      avoid_tropes: [<trope_id>, ...]  # 创作者明确拒绝的
      require_novelty_in: [<open_dimension>, ...]  # 在哪些维度 explore novelty
      novelty_score_threshold: 0.6  # 默认 0.6;experimental 可调到 0.8
      selected_template: <template_id>  # 从 §6.1 选择
      template_choice_rationale: <CN prose>
```

### §7.3 — screenplay 节点的 novelty-aware I/O

screenplay 在生成时:
- 读 `novelty_constraint` 作为 prompt 的一部分(Pattern 3 + Pattern 5)
- 输出 `screenplay_full` + `novelty_self_score`(LLM 自评 + 后续 logic-critic 验证)

script_auditor 在审计时:
- 检查 `novelty_self_score` vs 实际 trope-catalog embedding 算分
- 若 self-score 与 catalog-score 差距 > 0.15 → flag 为 self-overestimate,触发 regenerate

### §7.4 — Novelty 失败的 regeneration 路径

```
novelty_score < threshold:
  1. Try Pattern 3 + Pattern 6 (anti-trope + regenerate-with-feedback)
  2. If still failing after 3 iter:
     a. Try different template (Pattern 5 select different)
     b. If still failing:
        - escalate to human creator
        - creator may revise anecdote OR accept cliché with explicit "commercial_mode" flag
```

`commercial_mode` 是显式 escape hatch — 创作者接受 cliché(为了商业),但必须在 `creative_source` 输出中标记 `commercial_mode: true`,让下游 theory_critic 知道这是商业妥协不是创意失败。

---

## §8 — Open Questions(喂给 Phase 12 GOV-04)

### §8.1 — 研究层面 gaps

1. **Trope-catalog embedding 数据库不存在** — §1.4 假设有一个 Save-the-Cat + 爆款公式 + Kishōtenketsu 的 embedding database。这需要单独构建(短剧爆款公式 codification + embedding 模型选择)。**推荐:** FUTURE milestone
2. **Novelty-score 阈值(0.6 / 0.8)实证依据不足** — 是初步值,需要创作者实际反馈校准。**推荐:** v2.0 PRFP 之后小规模 pilot
3. **Consistency-context schema 完整性** — §2.1 的 schema 是初步设计,实战中可能需要更多/更少字段。**推荐:** Phase 11 handoff 时 kais-movie-agent 团队 review

### §8.2 — 实施层面 gaps

4. **Template library 实际可用性** — 6 模板中部分(尤其 anti_structure)需要进一步 operational 定义。**推荐:** Phase 11 handoff + 后续 milestone
5. **Logic-critic 的 LLM 模型选择** — script_auditor 当前用 Haiku(cost-optimized)。是否够用?需要 live run 验证。**推荐:** FUTURE-04 live run

### §8.3 — 设计层面 gaps

6. **Commercial_mode flag 的滥用风险** — 创作者可能滥用 commercial_mode 作为 cliché 的借口。需要 governance(per Phase 12 GOV-01 G7)。**推荐:** Phase 12
7. **平台 convention drift 对 novelty_score 的影响** — 短剧爆款公式漂移时,novelty_score 阈值是否需要调整?**推荐:** 后续 milestone

---

## References

### LLM-story-gen 论文(STACK §5)
- Plot Hole Detection benchmark — arXiv 2504.11900 — https://arxiv.org/html/2504.11900v1
- ConStory-Bench — arXiv 2603.05890 — https://arxiv.org/html/2603.05890v1 + https://github.com/Picrew/ConStory-Bench
- CONFACTCHECK — ACL 2025 Findings — https://aclanthology.org/2025.findings-ijcnlp.129/
- Survey on LLMs for Story Generation — EMNLP 2025 Findings — https://aclanthology.org/2025.findings-emnlp.750.pdf
- Learning to Reason for Long-Form Story Generation — OpenReview — https://openreview.net/forum?id=dr3eg5ehR2
- Awesome-Story-Generation — GitHub — https://github.com/yingpengma/Awesome-Story-Generation
- Creator-Centric Methods for LLM-Assisted Interactive Narrative — ACM — https://dl.acm.org/doi/10.1145/3772318.3791362
- Scaffolding the Story: An LLM-Based Assessment — IASDR — https://dl.designresearchsociety.org/cgi/viewcontent.cgi?article=1644&context=iasdr

### v2.0 PRFP 设计套件(cross-references)
- `00-FIRST-PRINCIPLES.md` §3.4 D4.1 + §2.5
- `02-NODE-SPECS.md` §2.1 (creative_source) + §2.3 (screenplay) + §2.4 (script_auditor)
- `nodes.yaml` (canonical source)
- `edges.yaml` (DAG topology)

### Template library 来源
- Field, Syd. *Screenplay*. Delta Trade Paperbacks.
- Snyder, Blake. *Save the Cat! The Last Book on Screenwriting You'll Ever Need*. Studio City Productions.
- Campbell, Joseph. *The Hero with a Thousand Faces*. New World Library.
- 起承转合(Kishōtenketsu)— 东亚叙事传统,无单一 canonical 来源
- Vogler, Christopher. *The Writer's Journey*. Michael Wiese Productions.
- 短剧爆款公式 — 平台算法驱动,无 canonical codification(本研究 §8.1 flag)

### Philosophy of creativity(背景)
- Boden, Margaret. *The Creative Mind: Myths and Mechanisms*. Routledge.
- Kant, Immanuel. *Critique of Judgment*. (creative genius as original + exemplary)

---

*Document version: design-2026-06-16-prfp*
*Phase 10 of v2.0 PRFP milestone — LLM Creative Distillation Deep-Dive*
*Bilingual policy: EN structure + CN prose (META-03)*
