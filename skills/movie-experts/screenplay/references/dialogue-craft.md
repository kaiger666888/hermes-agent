# Dialogue Craft — Density Thresholds by Genre + Subtext Ratio + CN Anti-Patterns + Per-Platform Register

**Source:** 短剧 创作者 公开 创作经验 + modern CN screenplay craft books (公开) + 行业 创作指南 aggregated
**Copyright:** Fair Use — aggregated observation only; no reproduction of copyrighted example dialogue beyond ≤ 90s fair-use fragments (see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 CN 短剧 / 微电影 的台词设计工艺 —— 区别于西方电影的台词密度与潜台词规则,短剧 的台词有自己的密度阈值、潜台词比例、反模式、平台 register 差异与 economy 规则。本 ref 回答五个核心问题:**不同题材的台词密度阈值是多少?潜台词比例如何衡量?CN 特有的台词反模式有哪些?不同平台的台词 register 如何分化?不同集长形态的台词 economy 如何?**

本 ref 是 短剧 台词数值的**唯一真相源** —— screenplay SKILL.md body 的 dialogue_density threshold + dialogue_naturalness metric 定义依赖本 ref。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat))。

---

## Density Thresholds by Genre

台词密度(dialogue density)= 每秒台词行数(lines/second)。短剧 的台词密度因题材而有显著差异 —— 这不是"创作者风格选择",而是**观众认知负荷的物理约束**。

### 题材 × 台词密度阈值表(heuristic)

| 题材 | 台词密度(lines/sec) | 理由 | 典型平台 |
|------|----------------------|------|----------|
| **[男频](../../_shared/glossary.md#男频-male-oriented-channel) 复仇 / 逆袭** | **0.4-0.6** | 男频观众偏好"行动 > 语言";过密的台词会拖慢节奏,削弱 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 兑现的即时感 | 抖音 / 快手 |
| **[女频](../../_shared/glossary.md#女频-female-oriented-channel) 闪婚 / 豪门虐恋** | **0.5-0.7** | 女频观众偏好"情感表达";台词是情绪传递的主要载体;但 > 0.7 会显得"话痨" | 抖音 / 小程序剧 |
| **[女频](../../_shared/glossary.md#女频-female-oriented-channel) 萌宝 / 家庭** | **0.4-0.6** | 萌宝 / 家庭题材的台词需要留出"视觉萌点"时间;过密台词会淹没萌点 | 抖音 / 快手 |
| **小程序剧 悬疑 / 家族秘辛** | **0.3-0.5** | 悬疑题材的台词需要"留白"让观众推理;过密台词会破坏悬念 | 微信小程序剧 |
| **≥ 0.8(任何题材)** | **[旁白过度](../../_shared/glossary.md) anti-pattern** | ≥ 0.8 lines/sec 意味着几乎每秒都有台词,没有视觉叙事空间 —— 这是 CN 短剧 的典型 anti-pattern(见 §"As You Know" CN Anti-Pattern) | (所有平台) |

**关键 heuristic 1:** 男频 复仇的台词密度(0.4-0.6)低于 女频 闪婚(0.5-0.7)。原因是 男频 的 爽点 兑现依赖"行动"(打脸 / 逆袭 / 身份揭露),而非"语言";女频 的情感共鸣依赖"台词"(误解 / 揭露 / 和解的语言交换)。

**关键 heuristic 2:** ≥ 0.8 lines/sec 是 **[旁白过度](../../_shared/glossary.md) anti-pattern** 的阈值。短剧 是"竖屏视觉叙事" —— 观众的注意力分配给画面 + 字幕 + 台词三层。如果台词密度 ≥ 0.8,观众的认知负荷过载,无法处理画面信息,完播率 会崩。这与 [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve 的"8-12s 无 击中点 则 attention drops ≥ 15%"呼应 —— 过密台词本身不构成 击中点,反而消耗注意力。

### 台词密度的测量协议(heuristic)

**关键 heuristic 3:** 台词密度的测量不是简单地数行数除以秒数。协议:

1. **一行台词 = 一个角色的连续发言**(从开口到闭嘴,中间允许短暂停顿 ≤ 1s)。
2. **台词密度 = 总行数 / 场景 runtime(秒)**。例如:一个 12s 场景中有 6 行台词 → 密度 = 6/12 = 0.5 lines/sec。
3. **旁白 (voice-over narration) 计入台词密度**,但需单独标注(因为旁白是 anti-pattern 的高风险来源)。
4. **背景人声(嘈杂的宴会 / 街道)不计入台词密度**(它们是环境音,不是叙事台词)。

### 台词密度与 Snyder Beat 的关系(heuristic)

不同 Snyder beat 段的台词密度应有差异 —— 这不是随意分布,而是由 beat 的功能决定:

| Snyder Beat 段 | 推荐台词密度 | 理由 |
|----------------|-------------|------|
| **Opening Image + 钩子(0-3s)** | 0.3-0.5 lines/sec | 钩子段以视觉为主;台词只是 1-2 句 hook-pin |
| **Set-Up + Catalyst(3-15s)** | 0.4-0.6 lines/sec | setup 段需要台词交代背景,但不能话痨 |
| **Fun & Games(15-40s)** | 0.5-0.7 lines/sec | 兑现段允许更多台词(角色互动密集) |
| **Midpoint + Bad Guys Close In(40-70s)** | 0.4-0.6 lines/sec | 局势恶化段台词应稍降(视觉冲突为主) |
| **All Is Lost + Dark Night(67-77s)** | 0.2-0.4 lines/sec | 触底段台词最少(情绪靠视觉 + 音乐传递) |
| **Finale(77-90s)** | 0.3-0.5 lines/sec | Finale 段台词回升但不话痨(主角行动为主) |

**关键 heuristic 4(衍生):** All Is Lost + Dark Night 段的台词密度应最低(0.2-0.4 lines/sec)。这是因为触底段的情绪不应靠台词传递 —— 主角的绝望应通过视觉(特写眼神 / 颤抖的手)+ 音乐(BGM swell)传递,而非台词直述("我好绝望")。台词过密的触底段会变成"话痨式自怜",破坏情绪冲击。

### 台词密度的题材 × 段交叉验证

结合题材差异(§Density Thresholds by Genre)与段差异(§台词密度与 Snyder Beat):

- **男频 复仇 的 All Is Lost 段:** 台词密度 0.2-0.3 lines/sec(最低;男主沉默忍受)
- **女频 闪婚 的 All Is Lost 段:** 台词密度 0.3-0.4 lines/sec(略高;女主允许 1-2 句内省台词)
- **男频 复仇 的 Fun & Games 段:** 台词密度 0.4-0.5 lines/sec(男频整体偏低)
- **女频 闪婚 的 Fun & Games 段:** 台词密度 0.5-0.7 lines/sec(女频整体偏高)

---

## Subtext Ratio Rule

潜台词(subtext)= 台词字面意思之下的隐含意义。McKee 的"show don't tell"原则在台词上的体现:**好的台词不说出角色的真实想法,而是让观众通过语境推断。**

### 潜台词比例阈值(heuristic)

**关键 heuristic 4:** 每行台词的**潜台词比例 ≥ 60%**。即:每行台词至少 60% 的意义是隐含的(不在字面意思中),最多 40% 是字面直述。

- **高潜台词(≥ 80%):** 角色说的每句话几乎都是"反话"或"言外之意"。典型:[女频](../../_shared/glossary.md#女频-female-oriented-channel) 豪门虐恋中的"冷暴力台词" —— 男主说"你随便",潜台词是"我在乎但我不会说"。
- **中潜台词(60-80%):** 角色的台词有明确的字面意思,但情感层面有隐含。典型:[男频](../../_shared/glossary.md#男频-male-oriented-channel) 装穷打脸中的主角说"我没事",潜台词是"我忍着,但我会报复"。
- **低潜台词(< 60%):** 角色的台词几乎全是字面意思,没有隐含。这是 anti-pattern(见 §"As You Know" CN Anti-Pattern)。

**关键 heuristic 5:** 潜台词比例是**主观 LLM-judged 代理指标**,不是客观测量。判定协议:

1. 对每行台词,LLM 判断:"如果只看字面意思,观众能理解角色的真实意图吗?"
2. 如果"能完全理解" → 潜台词比例 < 40%(低)
3. 如果"能部分理解,但有隐含情感 / 动机" → 潜台词比例 40-80%(中-高)
4. 如果"字面意思与真实意图几乎相反" → 潜台词比例 ≥ 80%(高)
5. 场景的潜台词比例 = 所有台词的比例平均值

### 5 个高潜台词 vs 低潜台词 短剧 台词对比例(heuristic)

**示例 1:女频 豪门虐恋 —— 高潜台词(≥ 80%)**
- 场景:男主发现女主是替身,质问她。
- **高潜台词台词:** 男主:"你走吧。"(字面:驱逐。潜台词:我受伤了,但我不会求你留下)
- **低潜台词台词(anti-pattern):** 男主:"我现在很生气,因为你骗了我,我希望你离开。"(字面 = 潜台词,无隐含)

**示例 2:男频 装穷打脸 —— 中潜台词(60-80%)**
- 场景:主角被反派羞辱后,默默捡起地上的花。
- **高潜台词台词:** 主角(捡花时,不看反派):"花没坏。"(字面:评价花。潜台词:我不跟你计较,但我会记住)
- **低潜台词台词(anti-pattern):** 主角:"我虽然现在看起来穷,但我内心很强大,总有一天我会让你后悔。"(字面 = 潜台词,且是旁白式自我宣告)

**示例 3:女频 萌宝 —— 高潜台词(≥ 80%)**
- 场景:萌宝(主角的孩子)问女主关于爸爸的事。
- **高潜台词台词:** 萌宝:"妈妈,别人的爸爸也会很久不回家吗?"(字面:提问。潜台词:我想爸爸了,但我不想让你难过)
- **低潜台词台词(anti-pattern):** 萌宝:"妈妈,我很想念爸爸,他为什么不回家?是因为你不让他回来吗?"(字面 = 潜台词,且将孩子的情绪过度直述)

**示例 4:男频 战神归来 —— 中潜台词(60-80%)**
- 场景:战神(主角)回到曾经的部队,老部下认出他。
- **高潜台词台词:** 老部下(敬礼):"长官,好久不见。"(字面:问候。潜台词:我一直等你回来,我依然效忠你)
- **低潜台词台词(anti-pattern):** 老部下:"长官,你终于回来了!这些年我一直在等你,我依然效忠你,随时听你调遣!"(字面 = 潜台词,过度直述忠诚)

**示例 5:小程序剧 家族秘辛 —— 高潜台词(≥ 80%)**
- 场景:主角发现养父遗书,询问家族长辈。
- **高潜台词台词:** 长辈(沉默良久):"有些事,不知道比知道好。"(字面:建议。潜台词:我知道真相,但真相会伤害你,所以我不说)
- **低潜台词台词(anti-pattern):** 长辈:"你养父其实不是好人,他做过很多坏事,我怕你知道了会受不了,所以一直瞒着你。"(字面 = 潜台词,且是"as you know"式的信息倾倒)

---

## "As You Know" CN Anti-Pattern

西方编剧的反模式"As you know, Bob"(角色之间互相解释双方都已知道的信息,纯粹为观众服务)在 CN 短剧 中有对应的变体。

### CN 短剧 的 3 种"As You Know"变体

**变体 1:"你应该知道..." / "我们都知道..."式 expository crutch**

- **典型台词:** "你应该知道,我们家族三代都是从商的..." / "我们都知道,十年前那场大火改变了 everything..."
- **问题:** 角色之间不需要互相解释双方都知道的事;这是纯粹为观众服务的信息倾倒。
- **修复:** 把信息融入行动 / 视觉 / 潜台词。例如:不要让角色说"我们家族三代从商",而是让镜头扫过墙上的家族企业照片 + 角色随手整理西装(暗示商业背景)。

**变体 2:旁白过度(Voice-over Narration as Plot Crutch)**

- **典型形式:** 旁白连续解说主角的内心活动 / 背景故事 / 时间跳跃。
- **问题:** 短剧 是视觉叙事;旁白过度剥夺了观众的视觉参与,且暴露创作者"不会用画面讲故事"。
- **修复:** 旁白只在以下 3 种场景使用(且每集 ≤ 2 次):(1) 开场钩子段的 1-2 句旁白建立悬念;(2) 时间跳跃的 1 句旁白过渡(例如"三年后");(3) 集末 卡点 的 1 句旁白强化悬念。

**变体 3:角色自我宣告情绪("我很生气" / "我好难过")**

- **典型台词:** 主角:"我现在非常生气!" / 女主:"我真的很伤心..."
- **问题:** 好的表演 + 镜头 + 台词潜台词应该让观众"感受到"角色的情绪,而不是让角色"宣告"自己的情绪。
- **修复:** 用行动 / 视觉 / 潜台词替代。例如:不要让主角说"我很生气",而是让他默默握紧拳头(特写)+ 把杯子捏碎。

### 3-Strike 规则(heuristic)

**关键 heuristic 6:** **3-strike 规则** —— 一个场景中出现 ≥ 3 个上述"As You Know"变体,该场景必须重写。计数方式:

- 每个变体出现 1 次 = 1 strike
- 3 strikes = 重写触发
- 2 strikes = 警告(应修复但不强制重写)
- 1 strike = 可接受(偶发的 expository 台词是合理的)

### 3-Strike 规则的计数示例

以下是一个 90s 场景的 3-strike 计数示例(男频 装穷打脸 S1E03):

| 台词 | 变体类型 | Strike 计数 | 诊断 |
|------|----------|-------------|------|
| 主角:"你应该知道,我父亲生前是这家公司的创始人。" | 变体 1("你应该知道...") | 1 strike | 警告:expository crutch |
| 旁白:"三年前,主角被合伙人陷害,失去了一切..." (持续 5s) | 变体 2(旁白过度) | 2 strikes | 警告:旁白 > 2s |
| 主角:"我现在非常愤怒!我一定要让他们付出代价!" | 变体 3(自我宣告情绪) | **3 strikes** | **重写触发** |

**修复方案:**
- 台词 1 → 删除"你应该知道",改为视觉:镜头扫过墙上的老照片(暗示家族历史)
- 旁白 → 删除,改为 1s 的时间跳跃字幕"三年前"+ 1 个闪回画面(5s)
- 台词 3 → 删除,改为行动:主角默默握紧拳头(特写)+ 把手中的玻璃杯捏碎

修复后 strike 计数 = 0(全部通过视觉 / 行动 / 潜台词替代)。

---

## Per-Platform Register Divergence

不同平台的受众偏好导致台词 register(语域 / 语言风格)分化。

### 平台 × 台词 Register 表(heuristic)

| 平台 | 台词 Register 特征 | 典型句式 | 避免的 Register |
|------|---------------------|----------|-----------------|
| **抖音** | **punchy 一句话 + 反转** | 短句(8-15 字)/ 反转句式("你以为...其实...") | 长句 / 书面语 / 文艺腔 |
| **快手** | **口语化长句** | 口语化 / 方言元素 / 长 句(12-20 字)/ 接地气 | 文艺腔 / 过度修饰 / "精英感" |
| **微信小程序剧** | **戏剧化 elevated register** | 戏剧化 / 书面语元素 / 长 句(15-30 字)/ 文学性 | 过于口语 / 粗俗 / 草根 |

**关键 heuristic 7:** 抖音 偏好"一句话 + 反转"的台词风格。典型句式:"你以为我是乞丐?其实我是这家公司的老板。" 这种句式在 3-5 秒内完成"反转 gap"(见 [`mckee-scene-design.md`](./mckee-scene-design.md) §The Gap Definition),适合 抖音 的高密度快节奏。

**关键 heuristic 8:** 快手 偏好"口语化长句"的台词风格。快手受众重视"接地气"与"真实感" —— 台词应像普通人说话,允许方言元素(例如东北话 / 四川话)和口语化表达(例如"你说气不气人")。避免文艺腔(快手受众会觉得"装")。

**关键 heuristic 9:** 微信小程序剧 偏好"戏剧化 elevated register"。小程序剧 的集长更长(120-180s),叙事容量更大,允许更复杂的台词结构(例如家族秘辛中的"三姨太端着茶盘,缓步走到老太爷面前,轻声说:老爷,二房那边又有动静了"—— 这种文学性台词在 抖音 90s 形态中会显得拖沓,但在 小程序剧 180s 形态中恰到好处)。

---

## Dialogue Economy by Format

不同集长形态对台词 economy(经济性)的要求不同。

### 集长 × 平均台词长度表(heuristic)

| 集长形态 | 平均台词长度(CN 字符 / 行) | 理由 |
|----------|------------------------------|------|
| **抖音 90s** | **8-15 字** | 90s 形态要求每行台词快速传递信息;长句会拖慢节奏 |
| **快手 60-120s** | **12-20 字** | 快手 口语化 register 允许稍长的句子;但仍需控制 |
| **小程序剧 120-180s** | **15-30 字** | 小程序剧 集长更长,允许更复杂的句子结构 + elevated register |

**关键 heuristic 10:** 平均台词长度(字符 / 行)不是硬上限,而是**平均值**。单行台词可以超过这个范围(例如 小程序剧 中的一句 40 字独白),但场景内所有台词的平均值应落在对应集长的范围内。

### 台词 economy 的 3 条规则(heuristic)

**关键 heuristic 11:** 台词 economy 的 3 条硬规则:

1. **每行台词必须推进剧情 或 揭示角色(二选一或两者)。** 既不推进剧情也不揭示角色的台词 = 废话,应删除。验证方法:删掉这行台词后,观众是否还理解场景?如果"是",这行台词是废话。
2. **每行台词必须与上一行形成 gap(期望与结果的鸿沟)或 承接(补充信息)。** 既不形成 gap 也不承接的台词 = 游离台词,破坏场景节奏。
3. **台词与视觉的比例应平衡。** 经验值:台词占场景 runtime 的 40-60%(见 §Density Thresholds by Genre);视觉叙事(无台词段)占 40-60%。如果台词 > 70%,场景是"talking heads" anti-pattern;如果台词 < 30%,场景信息密度不足。

### 台词 Economy 的验证清单

每个 短剧 场景的台词应通过以下验证:

1. [ ] 每行台词推进剧情 或 揭示角色(废话检查)
2. [ ] 每行台词与上一行形成 gap 或 承接(游离检查)
3. [ ] 台词占场景 runtime 40-60%(talking heads 检查)
4. [ ] 3-strike 计数 ≤ 2(anti-pattern 检查)
5. [ ] 潜台词比例 ≥ 60%(subtext 检查)
6. [ ] 台词密度在题材范围内(男频 0.4-0.6 / 女频 0.5-0.7)
7. [ ] 平均台词长度在集长范围内(抖音 8-15 字 / 快手 12-20 字 / 小程序剧 15-30 字)

### 台词与 HOOK marker 的关系(heuristic)

台词设计不是孤立的 —— 它与 HOOK marker schema(见 [`../hook_retention/SKILL.md`](../hook_retention/SKILL.md) §Marker Schema)有精确对应:

| HOOK marker 类型 | 对应台词特征 | 台词密度 | 潜台词比例 |
|------------------|-------------|----------|-----------|
| **钩子 marker(0-3s)** | hook-pin 台词(1-2 句) | 0.3-0.5 lines/sec | ≥ 80%(高潜台词) |
| **爽点 marker(70-80s)** | 爽点 兑现台词(1 句关键台词) | 0.4-0.6 lines/sec | 60-80%(中-高潜台词) |
| **卡点 marker(88-90s)** | 卡点 悬念台词(1 句未解问题) | 0.2-0.4 lines/sec | ≥ 80%(高潜台词) |

**关键 heuristic 12(衍生):** 钩子 / 卡点 marker 的台词潜台词比例应 ≥ 80%(高于通用规则 60%)。这是因为钩子 / 卡点 的功能是"制造悬念" —— 悬念需要高潜台词(角色不说出真实意图,让观众猜测)。如果钩子 / 卡点 台词的潜台词比例 < 80%,悬念效果会大打折扣。

---

## Cross-References

- [`save-the-cat-beat-sheet.md`](./save-the-cat-beat-sheet.md) §Save-the-Cat Moment Defined —— Save the Cat 时刻的台词潜台词(本 ref 的 subtext ratio 规则适用)
- [`mckee-scene-design.md`](./mckee-scene-design.md) §The Gap Definition —— 台词 gap(角色期望与反应的鸿沟)与本 ref 的 subtext 同构
- [`cn-shortdrama-structure.md`](./cn-shortdrama-structure.md) §Per-Platform Divergence —— 平台节奏差异与本 ref 的台词 register 差异互补
- [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve —— 旁白过度 anti-pattern 的注意力衰减实证支撑
- [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §Taxonomy —— 钩子 5-type taxonomy 的台词风格(本 ref 的 register 规则适用)
- [`../_shared/glossary.md`](../../_shared/glossary.md) —— 术语定义([男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat))

---

## Refresh Cadence

- **季度复核:** 重新验证各题材的台词密度阈值(男频 0.4-0.6 / 女频 0.5-0.7)是否仍为当前观众认知负荷的甜区
- **平台算法变更触发:** 抖音 / 快手 / 微信小程序剧 受众偏好变化时,重新验证 per-platform register 差异
- **新题材涌现触发:** 若出现新的 短剧 题材(例如科幻短剧 / 悬疑推理短剧),补充对应台词密度阈值
- **A/B 测试结果触发:** 若 完播率 数据显示"高潜台词比例 ≥ 60%"在某些题材下不再优于"低潜台词",需修订 §Subtext Ratio Rule
- **新 anti-pattern 涌现触发:** 若 短剧 行业出现"As You Know"之外的新台词反模式,补充 §"As You Know" CN Anti-Pattern
- **集长形态变化触发:** 若出现新的集长标准,更新 §Dialogue Economy by Format 的平均台词长度表
- **3-strike 规则失效触发:** 若 A/B 测试显示 3-strike 阈值不再适用,修订 §3-Strike 规则
- **负责模块:** screenplay SKILL.md body 的 dialogue_density threshold + dialogue_naturalness metric 依赖本 ref

### 复核协议(heuristic)

每次复核应遵循以下 4 步协议:

1. **行业数据采集:** 从各平台创作者中心 + 创作者公开访谈收集最近 90 天的台词密度 / 潜台词比例观察
2. **阈值验证:** 对比当前阈值表(男频 0.4-0.6 / 女频 0.5-0.7 / 潜台词 ≥ 60%)与行业数据
3. **偏差判定:** 若偏差 > ±0.1(密度)/ ±10%(潜台词比例),触发更新
4. **文档更新:** 更新 Last-verified 日期 + 修订记录;同步 screenplay SKILL.md 的 References 表

---

## 修订记录

| 日期 | 版本 | 修订内容 | 修订人 |
|------|------|----------|--------|
| 2026-06-15 | v1.0 | 初版 — 密度阈值 + 潜台词比例 + CN anti-pattern + per-platform register + economy 规则 | Phase 3 plan 03-01 |

---

## 使用说明

本 ref 是 screenplay 专家的 5 个 curated refs 之一(Phase 3 [CONTEXT D-1](../../../../../.planning/phases/03-top-4-existing-experts-rag/03-CONTEXT.md) source mix 第 5 项:CN dialogue craft)。screenplay SKILL.md 的 `## References` 表列出本 ref 的触发条件与核心内容摘要。

本 ref 的所有数值(台词密度阈值 / 潜台词比例 60% / 3-strike 规则 / 平均台词长度 / per-platform register 表)是**唯一真相源** —— screenplay SKILL.md body 的 dialogue_density threshold + dialogue_naturalness metric 定义依赖这些数字。screenplay SKILL.md body 不重复定义,只引用 + 跨链。

---

## Drift Signals

以下信号提示本 ref 可能已过时,需要重新验证:

1. **密度阈值漂移:** 若 男频 复仇的台词密度甜区从 0.4-0.6 漂移到 0.5-0.8(更话痨的趋势),需更新 §Density Thresholds by Genre
2. **潜台词比例失效:** 若观众对"低潜台词直述"的容忍度提升(算法偏好更直白的表达),需修订 §Subtext Ratio Rule
3. **新 anti-pattern 涌现:** 若 短剧 行业出现"As You Know"之外的新的台词反模式(例如"AI 腔"——过度规范的 AI 生成台词),需补充 §"As You Know" CN Anti-Pattern
4. **per-platform register 趋同:** 若各平台的台词 register 差异逐渐缩小,需简化 §Per-Platform Register Divergence
5. **集长形态变化:** 若出现新的集长标准,需更新 §Dialogue Economy by Format 的平均台词长度表
6. **3-strike 阈值失效:** 若 A/B 测试显示 3-strike 阈值(重写触发)不再适用(例如 4-strike 才需重写),需修订 §3-Strike 规则
7. **段差异表漂移:** 若各 Snyder beat 段的台词密度差异发生变化(例如 All Is Lost 段允许更高密度),需更新 §台词密度与 Snyder Beat 的关系 表
8. **新题材涌现:** 若出现新的 短剧 题材(例如科幻 / 历史),需补充对应台词密度阈值
9. **潜台词判定协议变化:** 若 LLM-judged 潜台词比例判定协议需更新(例如引入新的判定维度),需修订 §潜台词比例阈值
10. **台词与 HOOK marker 关系变化:** 若 HOOK marker schema 发生变化(Phase 2 HOOK-09 合同修订),需更新 §台词与 HOOK marker 的关系 表
