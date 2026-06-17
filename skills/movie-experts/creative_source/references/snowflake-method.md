# Snowflake Method — Ingermanson 10-Step Recursive Expansion Pipeline Adapted to 短剧 / 微电影

**Source:** *How to Write a Novel Using the Snowflake Method* (Randy Ingermanson, 2013 10th-anniversary edition; method originally published on `advancedfictionwriting.com` 2002-2003 series of articles). The method is widely referenced in creative-writing pedagogy; this ref paraphrases the 10-step skeleton (step names, inputs, outputs, recursion logic) only — no verbatim reproduction of Ingermanson's prose, examples, or chapter walkthroughs.
**Copyright:** Fair Use — paraphrased methodology skeleton + adaptation tables. No reproduction of Ingermanson's example prose, novel-plot walkthroughs, or chapter-level scaffolding. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-18
verified_date: 2026-06

---

## Summary

雪花法(Snowflake Method)是 Ingermanson 在 2002-2013 期间系统化的**递进式展开创作法** —— 从一句话 premise 出发,逐层放大到段落、角色概要、一页大纲、角色传记、四页大纲、完整角色表、场景列表、场景描述,最终抵达初稿。10 步的递进关系是严格的"前一步是后一步的输入":跳步展开会引入结构性塌陷。

本 ref 把雪花法挂载到 [`creative_source`](../SKILL.md) 的 StoryKernel 输出与 [`screenplay`](../../screenplay/SKILL.md) 的 Snyder 15-beat 消费之间,填补"一句话 → 段落 → 场景"的**展开塌陷** —— 此前 StoryKernel(structural_formula 一句话)直接被 screenplay 消费为 beat sheet 输入,中间缺失"角色如何承接冲突、四幕灾难如何分布"的过渡层,导致 screenplay 在 60-180s 单集 runtime 下经常出现 beat 分布失衡(典型症状:Catalyst 晚于 15% / Midpoint 缺失极性反转 / All Is Lost 不到位)。

雪花法不替代 StoryKernel(它消费 StoryKernel),也不替代 Snyder beat sheet(它产出可被 Snyder 消费的一页大纲 scaffold)。它是**展开中间层** —— 把"结构性冲突"递进式展开为"角色驱动的剧情骨架"。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md) 的 [Snowflake Method](../../_shared/glossary.md#snowflake-method-雪花法) / [Story Spine](../../_shared/glossary.md#story-spine-故事脊) / [Premise Sentence](../../_shared/glossary.md#premise-sentence-一句话前提) / [Scene List](../../_shared/glossary.md#scene-list-场景列表)。

---

## The 10 Ingermanson Steps

下表是 Ingermanson 原始 10 步的 paraphrased skeleton。每一步的输入 / 输出 / 与前一步的递进关系都已标注 —— 这是雪花法的**唯一权威表述**(避免 SKILL.md body 重述原理,Phase 1 CR-01 single-source-of-truth rule)。

| Step | 名称 | 输入 | 输出 artifact | 递进关系 |
|------|------|------|---------------|----------|
| 1 | **Premise Sentence**(一句话前提) | StoryKernel `structural_formula` (1-2 个最强冲突) | 1 句话 ≤ 30 字 | 把多层故事核压缩为"主人公 + 冲突 + 目标 + 障碍"四要素 |
| 2 | **Paragraph Expansion**(一段话扩展 / Story Spine) | Step 1 premise | 5 句话段落(灾难 × 3 + 结尾 × 1) | 用 Story Spine 的"开头 → 三幕灾难 → 结尾"结构扩展 premise |
| 3 | **Character Synopsis**(角色概要) | Step 2 paragraph + StoryKernel strata | 每主角 1 段(姓名 / 动机 / 目标 / 冲突 / 启示) | 把段落层面的冲突映射到具体角色 |
| 4 | **One-Page Synopsis**(一页大纲) | Step 2 paragraph | 4 段 1 页(开头 / 三幕灾难 / 结尾) | 把 5 句话段落扩展为 4 段,每段对应一幕 |
| 5 | **Character Biography**(角色传记) | Step 3 synopsis | 每主角 1 页(童年 / 当前 / 触发事件时) | 角色动机的内化深度 |
| 6 | **Four-Page Synopsis**(四页大纲) | Step 4 one-page | 4 页(每幕 1 页) | 把一页大纲展开为四页,引入支线 |
| 7 | **Full Character Chart**(完整角色表) | Step 5 bio | 完整角色字段表(年龄 / 外貌 / 习惯 / 秘密 / 弱点) | 角色细节冻结 |
| 8 | **Scene List**(场景列表) | Step 6 four-page | 场景表(每行 1 场景:视角 / 目标 / 冲突 / 灾难) | 从幕级展开到场景级 |
| 9 | **Scene Description**(场景描述) | Step 8 scene list | 每场景 1 段叙事性描述 | 场景级 narrative |
| 10 | **First Draft**(初稿) | Step 9 descriptions | 完整剧本 | 写作执行 |

**关键递进逻辑:** 每一步的输出是后一步的**唯一**输入。Step 4 one-page synopsis 不是凭空写,而是从 step 2 paragraph 严格扩展而来;step 8 scene list 不是凭空列,而是从 step 6 four-page synopsis 的每一段展开而来。这种严格递进保证了"展开过程中信息不丢失",也避免了从一句话直接跳到场景列表导致的"剧情塌陷"。

**与 McKee value-shift / Snyder beat 的关系:** 雪花法是**展开方法**(从抽象到具体的递进),McKee / Snyder 是**结构验证方法**(检查展开结果是否符合节奏)。两者互补不替代 —— 雪花法产出 step 4 one-page synopsis,然后被 screenplay 用 Snyder 15-beat 验证 beat 分布(见 §Snowflake-4 → Snyder 15-Beat Field Mapping)。

---

## 短剧 Step Scaling (60-180s 单集)

短剧 60-180s 单集 runtime 是长片(110 min)的 1/40 ~ 1/110。雪花法的 10 步原本是为长片设计 —— 完整跑 10 步对 60s 单集是过度工程。本节给出**强制 / 可选 / 延后**三档 step 选择规则。

### 强制 minimum(creative_source 必须产出,交付给 screenplay)

| Step | 强制产出 | 短剧适配 |
|------|----------|----------|
| Step 1 Premise Sentence | ✅ 必做 | 从 StoryKernel `structural_formula` 直接转写,通常 ≤ 15 字(短剧 premise 比长片更尖锐) |
| Step 2 Paragraph Expansion | ✅ 必做 | 5 句话段落,每句 ≤ 12 字 —— 短剧 5 句 = 60 字 = 90s 单集的开场 30s 信息密度 |
| Step 3 Character Synopsis | ✅ 必做 | 每主角 1 段(目标 / 动机 / 冲突 / 启示),4 项各 ≤ 10 字 —— 短剧 角色驱动需极简 |
| Step 4 One-Page Synopsis | ✅ 必做 | 4 段 1 页,每段 ≤ 30 字 —— 4 段对应 Snyder 的 Set-Up+Catalyst / Midpoint / All Is Lost / Finale |

**理由:** Step 1-4 是雪花法展开的**最小闭环** —— premise → paragraph → 角色 → 一页大纲。这 4 步产出的 `snowflake_artifacts.json` 是 screenplay 的强制消费输入(见 screenplay SKILL.md workflow step 1.5)。

### 可选(根据题材复杂度决定)

| Step | 触发条件 |
|------|----------|
| Step 5 Character Biography | 主角 ≥ 2 人(群像短剧)/ 题材为豪门虐恋 / 战神归来等需要角色背景层次时 |
| Step 6 Four-Page Synopsis | 单集 runtime ≥ 120s / 集数 ≥ 20 集(单集叙事容量够大) |

### 延后到 screenplay 内部(避免与 Snyder 重复)

| Step | 处理 |
|------|------|
| Step 7 Full Character Chart | screenplay 在 Dialogue Draft 阶段按需展开(避免重复 character_designer 工作) |
| Step 8 Scene List | screenplay 在 Beat Planning 阶段产出 —— 与 Snyder 15-beat 同构,合并 |
| Step 9 Scene Description | screenplay 在 Dialogue Draft 阶段产出 |
| Step 10 First Draft | screenplay 最终输出 script.json |

**架构边界:** Step 7-10 不在 creative_source 跑 —— 这是雪花法与 screenplay 内部 Snyder / McKee 流程的**协作边界**,避免双重产出场景表。

---

## 短剧 Step Scaling (10-80 集连续剧)

10-80 集短剧连续剧是雪花法的**天然适配场景** —— 雪花法递进式展开正好对应"主线 → 分集 → 分场"的连续剧展开逻辑。下表给出 series-level vs episode-level 的 step split:

| Step | Series Level(整剧) | Episode Level(单集) |
|------|---------------------|----------------------|
| 1 Premise | ✅ 整剧一句话 premise(锁定整剧核心冲突) | 不重复(每集消费整剧 premise 的子冲突) |
| 2 Paragraph | ✅ 整剧 5 句话段落(对应整剧的开头 / 发展 / 高潮 / 结尾) | ✅ 单集 5 句话段落(本集子冲突展开) |
| 3 Character Synopsis | ✅ 主要角色(2-4 人)的整剧角色弧线 | ✅ 单集角色状态(从整剧弧线中切出当前集快照) |
| 4 One-Page Synopsis | ✅ 整剧 4 段(对应整剧的 4 个 act) | ✅ 单集 4 段(对应单集的 Snyder 15-beat 压缩版) |
| 5 Character Bio | 仅主角 1 人(series-level 弧线追踪) | 不展开 |
| 6 Four-Page Synopsis | ❌ 不做(连续剧不做整剧 4 页大纲,改用 episode-level) | 仅对关键集(集 1 / 集末 / 中段转折集)做 |
| 7-10 | 移至 screenplay episode-level | screenplay 每集都跑 |

**关键 heuristic:** 整剧 Step 1-4 由 creative_source 一次性产出(series-level `snowflake_artifacts.json`),然后每集 screenplay 消费整剧 Step 4 one-page 的对应段落作为 episode-level premise,跑 episode-level Step 2-4。这种 series→episode 递进保证了**整剧主线一致 + 单集局部展开**。

---

## StoryKernel → Snowflake Bridge Protocol

本节是雪花法与 [`creative_source`](../SKILL.md) 的 StoryKernel 输出的**衔接协议**。决定一个 StoryKernel 是否值得走雪花法展开,以及如何从 StoryKernel 字段提取雪花法 step 1-2 的输入。

### 触发条件(决定是否走 Snowflake 展开路径)

满足以下任一条件,StoryKernel 必须走雪花法展开:

| 条件 | 阈值 | 字段 | 理由 |
|------|------|------|------|
| 高不可言说性 | `unspeakability_score ≥ 7` | StoryKernel `unspeakability_score` | 高敏感 kernel 需要更精细的角色 / 场景设计以承载合规降级(见 [`unspeakability-protocol.md`](./unspeakability-protocol.md)) |
| 高戏剧潜力 | `dramatic_potential.overall ≥ 0.75` | StoryKernel `dramatic_potential.overall` | 高潜力 kernel 值得展开为完整叙事 scaffold,而非直接交付 screenplay |
| 多层共振 | `strata_overlay_coefficient ≥ 1.7` | StoryKernel `strata_overlay_coefficient` | 多层叠加 kernel 需要角色层面承接多冲突维度 |

**默认:** 不满足上述任一条件的 StoryKernel 直接交付 screenplay(snowflake artifacts 字段为 null),避免对低质量 kernel 做无意义展开。

### Step 1 输入抽取(StoryKernel → Premise Sentence)

从 StoryKernel 提取 1-2 个最强冲突作为 Snowflake-1 (premise sentence) 的输入:

```
Step 1 输入:
  premise_seed_1 = StoryKernel.structural_formula  # 50-200 字单句
  premise_seed_2 = StoryKernel.strata_layers[0].answer  # 主导地层的"谁被规训 / 谁被豁免"
  
Step 1 输出 (Premise Sentence ≤ 30 字):
  "[主人公]面对[冲突],想要[目标],但被[障碍]阻挡"
```

**关键:** Step 1 premise 必须包含 4 要素(主人公 / 冲突 / 目标 / 障碍),这是 StoryKernel `structural_formula`(单句)到角色驱动 premise(4 要素)的**关键转译**。

### Step 2 输入抽取(Step 1 Premise → Paragraph Expansion)

Step 2 把 Step 1 premise 用 Story Spine 结构扩展为 5 句话段落。StoryKernel 提供的辅助字段:

| StoryKernel 字段 | Step 2 段落作用 |
|-------------------|------------------|
| `structural_formula` | 段落第 1 句(开头) |
| `strata_overlay_coefficient` | 决定段落第 2-3 句(三幕灾难)的密度 —— overlay ≥ 1.7 时灾难句应承载多冲突维度 |
| `unspeakability_breakdown.regulatory_redline` | 决定段落第 4 句(结尾)是否需要合规降级 |
| `target_audience_overlap` | 决定段落 polarity(男频 / 女频调整) |

---

## Snowflake-4 → Snyder 15-Beat Field Mapping

Snowflake step 4 的一页大纲(4 段)是 screenplay 消费的核心 artifact。下表是 4 段与 Snyder 15-beat 的字段映射 —— screenplay 在 Beat Planning 之前先消费 Snowflake-4 段落作为 scaffold,然后再用 Snyder 15-beat 验证 beat 分布。

| Snowflake-4 段落 | 对应 Snyder beat 集 | Snowflake 段落功能 | Snyder beat 目标 runtime 比例 |
|-------------------|---------------------|--------------------|------------------------------|
| **段落 1**(开头) | Opening Image + Theme Stated + Set-Up + Catalyst + Debate | 介绍主人公世界 + 触发事件 | 0-20% |
| **段落 2**(三幕灾难 第 1 幕) | Break into Two + B-Story + Fun & Games + Midpoint | 主角进入新世界 + 假胜利 / 假失败 | 20-50% |
| **段落 3**(三幕灾难 第 2 幕) | Bad Guys Close In + All Is Lost + Dark Night of the Soul | 外部对手反扑 + 最低点 | 50-77% |
| **段落 4**(结尾) | Break into Three + Finale + Final Image | 主角找到解决方案 + 执行 + 视觉对照 | 77-100% |

**关键映射 heuristic(双锚点):**
- Snowflake 段落第 1 段的**结尾**(Catalyst)必须对应 Snyder Catalyst(p.10 ± 3,~10% runtime)
- Snowflake 段落第 2 段的**结尾**(Midpoint)必须对应 Snyder Midpoint(p.55 ± 3,~50% runtime,且必须有极性反转)
- Snowflake 段落第 3 段的**结尾**(All Is Lost)必须对应 Snyder All Is Lost(p.75 ± 3,~68% runtime)

这三处是 Snowflake-4 段落与 Snyder 15-beat 的**强制对齐锚点** —— screenplay 消费 Snowflake-4 时,先校验这三处段落结尾是否落在 Snyder 目标 runtime 比例范围内(±5% 容差),若不在范围内则需要回到 creative_source 重写 Step 4 段落。

**反模式:** screenplay 不要在 Beat Planning 阶段把 Snowflake-4 段落拆细为 15-beat —— 雪花法的段落粒度已经足够作为 scaffold,Snyder 15-beat 是验证层而非展开层。强行拆细会导致雪花法展开的递进关系被破坏。

详细 Snyder 15-beat runtime 换算见 [`../../screenplay/references/save-the-cat-beat-sheet.md`](../../screenplay/references/save-the-cat-beat-sheet.md) §The 15 Beats。

---

## 与 McMahon 6 弧线的隐含耦合

Snowflake Step 2 paragraph expansion 应隐含呼应 McMahon 6 弧线之一(rags-to-riches / tragedy / man-in-a-hole / Icarus / Cinderella / Oedipus)。本 ref 不强制耦合,但建议在 Step 2 paragraph 写作时让作者选 1 个弧线作为 paragraph polarity 的隐含模板。

| McMahon 弧线 | Snowflake Step 2 段落 polarity | 典型短剧题材 |
|--------------|--------------------------------|--------------|
| Rags-to-riches | 段落 1 低 → 段落 4 高 | 男频 赘婿逆袭 / 都市修仙 |
| Tragedy | 段落 1 高 → 段落 4 低 | 悲剧向 / 虐恋 BE |
| Man-in-a-hole | 段落 1 高 → 段落 2-3 低 → 段落 4 高 | 战神归来 / 重生复仇(最常见男频弧线) |
| Icarus | 段落 1 中 → 段落 2-3 高 → 段落 4 低 | 警示向 / 反派主角 |
| Cinderella | 段落 1 低 → 段落 2-3 极低 → 段落 4 极高 | 女频 豪门虐恋 / 替身白月光 |
| Oedipus | 段落 1 中 → 段落 2-3 高 → 段落 4 低(自我诅咒) | 悬疑 / 反转剧 |

详细 McMahon 弧线定义见 [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md) §6 Core Emotional Arcs。

---

## Output Schema (`snowflake_artifacts.json`)

creative_source 在满足触发条件时,产出此 artifact 作为 StoryKernel 的展开补充,交付给 screenplay 消费。

```json
{
  "type": "SnowflakeArtifacts",
  "version": "1.0.0",
  "snowflake_id": "snowflake_<hash>",
  "kernel_id_ref": "kernel_<hash>",
  "trigger_reason": "unspeakability_score_ge_7 | dramatic_potential_ge_0_75 | strata_overlay_ge_1_7",
  "mcmahon_arc_selected": "man_in_a_hole",
  "step_1_premise_sentence": {
    "text": "灵活就业者李明面对社保断缴,想留在城市,但被高房价与制度陷阱阻挡。",
    "char_count": 28,
    "four_elements": {
      "protagonist": "灵活就业者李明",
      "conflict": "社保断缴",
      "goal": "留在城市",
      "obstacle": "高房价与制度陷阱"
    }
  },
  "step_2_paragraph_expansion": {
    "story_spine": [
      {"sentence": 1, "text": "李明是 35 岁外卖骑手,在一线城市奔波十年。", "role": "开头"},
      {"sentence": 2, "text": "社保断缴让他失去购房资格,女友提出分手。", "role": "灾难 1"},
      {"sentence": 3, "text": "他试图补缴,却遭遇平台政策调整,收入骤降。", "role": "灾难 2"},
      {"sentence": 4, "text": "返乡后,他发现家乡的灵活就业市场更不稳定。", "role": "灾难 3"},
      {"sentence": 5, "text": "他在城市边缘找到新的妥协,带着不完整的胜利继续。", "role": "结尾"}
    ]
  },
  "step_3_character_synopses": [
    {
      "name": "李明",
      "motivation": "想在城市立足证明自己",
      "goal": "保留购房资格",
      "conflict": "制度 vs 个人努力",
      "epiphany": "接受妥协不是失败"
    }
  ],
  "step_4_one_page_synopsis": {
    "paragraphs": [
      {"index": 1, "text": "...", "role": "开头", "mapped_snyder_beats": ["Opening Image", "Theme Stated", "Set-Up", "Catalyst", "Debate"]},
      {"index": 2, "text": "...", "role": "三幕灾难 第 1 幕", "mapped_snyder_beats": ["Break into Two", "B-Story", "Fun & Games", "Midpoint"]},
      {"index": 3, "text": "...", "role": "三幕灾难 第 2 幕", "mapped_snyder_beats": ["Bad Guys Close In", "All Is Lost", "Dark Night of the Soul"]},
      {"index": 4, "text": "...", "role": "结尾", "mapped_snyder_beats": ["Break into Three", "Finale", "Final Image"]}
    ]
  },
  "step_5_character_bios": null,
  "step_6_four_page_synopsis": null,
  "downstream_consumer": "screenplay",
  "created_at": "2026-06-18T10:00:00Z",
  "created_by": "creative_source.snowflake_expansion"
}
```

**字段冻结规则:**
- `trigger_reason` 必须三选一(对齐 §StoryKernel → Snowflake Bridge Protocol 触发条件)
- `mcmahon_arc_selected` 必须六选一(对齐 §与 McMahon 6 弧线的隐含耦合)
- `step_4_one_page_synopsis.paragraphs` 必须正好 4 段(对齐 §Snowflake-4 → Snyder 15-Beat Field Mapping)
- `step_5` / `step_6` 可为 null(对齐 §短剧 Step Scaling 可选项)

---

## Quality Thresholds

| Threshold | Value | Source |
|-----------|-------|--------|
| Step 1 premise char count | ≤ 30 chars | Ingermanson heuristic |
| Step 2 paragraph sentence count | exactly 5 | Story Spine rule |
| Step 4 paragraph count | exactly 4 | Ingermanson 4-act mapping |
| Step 4 段落 polarity 与 McMahon arc 一致性 | arc shape 必须匹配 | §与 McMahon 6 弧线 |
| Snowflake-4 锚点对齐 Snyder runtime 比例 | Catalyst ±5% / Midpoint ±5% / All Is Lost ±5% | §Snowflake-4 → Snyder Field Mapping |
| 触发条件覆盖 | 三选一,默认 null(不展开) | §触发条件 |

---

## Anti-Patterns to Avoid

- ❌ **不要跳步展开** —— Step 1 premise 必须先于 Step 2 paragraph,Step 2 必须先于 Step 4。从 StoryKernel 直接跳到 Step 4 会引入结构性塌陷。
- ❌ **不要在 Step 2 段落里塞入 Snyder beat 术语** —— Snowflake 是展开层,Snyder 是验证层。两者分层不混用。
- ❌ **不要把 Step 7-10 在 creative_source 跑** —— 这 4 步移至 screenplay 内部 Beat Planning 之后做(避免与 Snyder beat sheet 重复,见 §短剧 Step Scaling 延后项)。
- ❌ **不要忽略触发条件** —— 不满足触发条件的 StoryKernel 不展开,直接交付 screenplay(`snowflake_artifacts.json` 字段为 null)。
- ❌ **不要把 Snowflake-4 段落 polarity 与 McMahon arc 错配** —— 段落 polarity 必须与 `mcmahon_arc_selected` 一致(见 §与 McMahon 6 弧线)。
- ❌ **不要让 Snowflake-4 锚点偏离 Snyder runtime 比例超 ±5%** —— 偏离则需要重写 Step 4 段落,不要让 screenplay 强行适配。

---

## License

本 ref 是 Ingermanson 雪花法 10 步 skeleton 的 Fair Use paraphrase(方法论名称、步骤递进关系、输入/输出 artifact 类型)。未复制 Ingermanson 的原文 prose、example walkthroughs、或 chapter-level scaffolding。详细 License 见 [`LICENSE.md`](./LICENSE.md)。

雪花法 10 步的方法论所有权归 Randy Ingermanson(原创文章发布于 `advancedfictionwriting.com` 2002-2003;集结出版于 *How to Write a Novel Using the Snowflake Method*,2013)。本 ref 的短剧适配、StoryKernel 衔接协议、Snyder 字段映射、McMahon 弧线耦合等部分是 Hermes Agent 项目原创工作。

---

**Ref author:** creative_source expert team (Phase 19 SNOWFLAKE-01)
**Source date:** 2026-06-18
**Verified against:** StoryKernel schema ([`story-kernel-schema.md`](./story-kernel-schema.md)) + Snyder beat sheet ([`../../screenplay/references/save-the-cat-beat-sheet.md`](../../screenplay/references/save-the-cat-beat-sheet.md)) + McMahon arcs ([`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md))
