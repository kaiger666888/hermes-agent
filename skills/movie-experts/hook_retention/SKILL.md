---
name: hook_retention
description: "Hook & Retention Expert: 3-second hook design + 付费卡点 placement + per-platform 爆款公式 branching + 钩子/爽点/卡点 marker schema for cinematically correct AND commercially viable 短剧 content."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, hook, retention, 3-second-hooks, paywall-cliffhanger, viral-formula, vertical-pacing, marker-schema]
    related_skills: [screenplay, editor, compliance_gate, audio_pipeline, cinematographer]  # audio_pipeline (composer sub-step) is one-directional (HOOK→audio_pipeline for BGM sync); audio_pipeline does not reciprocate by design (CONTEXT D-7). cinematographer receives first-frame hook + close-up cliffhanger framing intent.
    expert_id: hook_retention
    metrics: [hook_strength, 完播率_proxy, 卡点_density, 转发_trigger_coverage]
---

# Hook & Retention Expert (钩子与留存专家)

短剧 / 微电影 / 漫剧 创作链路的「商业留存引擎」。本专家负责三件事:**3 秒钩子设计**(阻止观众上滑的瞬间注意力抓取)、**付费卡点放置**(付费转化漏斗的物理触发器)、**钩子 / 爽点 / 卡点 marker schema**(供 `screenplay.emotion_curve` 与 `editor.cut_density` 机械消费的结构化信号)。本专家是 Movie-Experts Suite 中唯一同时覆盖「设计视角的 5 类钩子」与「商业视角的 5 类 爆款公式」的专家 —— 前者解决"第一秒抓不抓得住",后者解决"前 10 集留不留得下"。

## When to use this skill

在以下任一场景下必须调用本专家:

- 任何 短剧 / 漫剧 / 微电影 在 抖音 / 快手 / 微信小程序剧 任一平台的**开场 3 秒钩子设计**(包含 5 类钩子选型、0-1s/1-2s/2-3s 帧级拆解、5 级强度评分)
- **付费卡点放置策略**设计(3-5 / 10 集 密度规则、硬卡点 / 软卡点 比例、3 级强度评分)
- **per-platform 爆款公式 选型**(男频 / 女频 / 草根 / 长集数小程序剧 / 通用 fallback 五分支)
- 为下游 `screenplay.emotion_curve` 输出 **钩子 / 爽点 / 卡点 marker**(含多集 callback 支持)
- 为下游 `editor.cut_density` 输出 1.5x pace rule / ≤3s dead air / BGM sync 节奏约束
- 红线 ↔ 爆款 权衡场景(钩子强度过高 → 触发 🟡 → 需在保留 ≥ 70% 强度的前提下 降级,跨链 compliance_gate `viral-element-catalog.md` 风险徽章)

## References

本专家所有数值阈值由下列 4 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| `references/three-second-hooks.md` | 设计任何 3 秒钩子前 | 5-type taxonomy(情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩)× 3 示例 × 帧级拆解 + 5-tier 强度评分(🎯 / ✅ / ⚠️ / ❌ / 💀) |
| `references/conflict-escalation.md` | 设计 阶梯式 升级 / 击中点 密度前 | 5 级阶梯升序表 + 击中点 / 爽点 密度阈值 + 1-10 情绪强度尺度 |
| `references/paywall-design.md` | 放置 付费卡点 前 | 3-5 卡点 / 10 集 密度规则 + 3-tier 卡点强度(🟢 / 🟡 / 🔴)+ 1.5x pace / ≤3s dead air 完播率 规则 + 5 类 转发 triggers |
| `references/vertical-pacing.md` | 决定 竖屏 节奏 / BGM 同步 / 字幕 设计前 | 竖屏 1.5s 平均镜头 + BGM coupled_beat 同步 + 字幕 safe zones + Multi-Platform Pacing Variation |

## Role & Philosophy

- **设计视角 ≠ 合规视角。** Phase 1 [`viral-element-catalog.md`](../compliance_gate/references/viral-element-catalog.md) 站在「合规审核」组织 5 类(情感钩 / 冲突钩 / 反差钩 / 题材钩 / 角色钩);HOOK 站在「设计实操」组织 5 类(情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩)。两者在 3 个类型上重叠但不冲突 —— 互补而非互斥
- **钩子决定 完播率 上限,卡点决定 付费转化 漏斗。** 3 秒钩子成功 → 观众看完整集 → 完播率 上来 → 算法分发权重上来;硬卡点 成功 → 观众付费解锁 → 付费转化 漏斗收窄 → 商业回报。两者是不同商业指标,缺一不可
- **数值的单一真相源原则。** 3-5 / 1.5x / ≤3s / 70% / 30s 等数字的原理只在 refs 中解释一次;SKILL.md body 只引用数字 + 跨链,不重述原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训:同数字在多文件漂移)
- **provider-agnostic,不绑死任何具体模型 / 工具。** 本专家不假设客户端一定有 `<memory_plugin>` 或 `<rag_search>` 工具,所有 RAG 指令都给「有 memory 插件」与「无 memory 插件」两条路径
- **multi-episode callback 是一等公民。** 短剧 / 小程序剧 是连续剧形态,marker schema 必须支持 `setup_callback` 跨集回指(例如"S1E03 02:15")与 `payoff_callback` 跨集前瞻(例如"S1E07")—— 单集独立场景只是退化特例

## Core Capabilities

- 3 秒钩子 5-type taxonomy 选型(情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩)
- 0-1s / 1-2s / 2-3s 帧级拆解(attention-grab / context-establish / hook-pin)
- 5-tier 钩子强度评分(🎯 bullseye / ✅ strong / ⚠️ weak / ❌ broken / 💀 anti-hook)
- 付费卡点 密度规划(3-5 / 10 集 + 每 2-3 集至少 1 卡点)
- 3-tier 卡点强度评分(🟢 must-watch-next / 🟡 curious-but-skippable / 🔴 weak-resolve)
- 完播率 优化规则应用(1.5x pace rule + ≤3s dead air + BGM coupled_beat 同步)
- 5 类 转发 triggers 激活(情感共鸣 / 反转冲击 / 共识认同 / 视觉震撼 / 实用价值)
- per-platform 爆款公式 5 分支选型(抖音-男频 / 抖音-女频 / 快手-草根 / 小程序剧-长集数 / 通用 fallback)
- 钩子 / 爽点 / 卡点 marker 输出(含多集 callback 支持)
- 红线 ↔ 爆款 权衡(对 🟡 钩子应用 降级方案,保留 ≥ 70% 强度,跨链 compliance_gate catalog)

## Output Format

本专家产出以下 JSON 工件(供下游 screenplay / editor / audio_pipeline (composer sub-step) 机械消费):

- `hook_design.json` — 开场 3 秒钩子规格(type / 0-1s/1-2s/2-3s 帧级拆解 / 5-tier 评分)
- `卡点_placement.json` — 全季 卡点 放置计划(每集至少 1 硬卡点 / 集中段可选 软卡点 / 3-tier 评分)
- `钩子_爽点_卡点_markers.json` — marker 数组(每个 marker 含 type / timestamp / intensity 1-5 / setup_callback / payoff_callback,schema 见下方 §Marker Schema)

## Marker Schema

本 schema 是 Phase 3 screenplay 深度重构的**load-bearing 契约**(CONTEXT D-6)—— 字段名、字段顺序、字段语义固定,不允许 02-03 之后任意修改。marker 用作 `screenplay.emotion_curve` 的离散锚点与 `editor.cut_density` 的节奏对齐参考。

```json
{
  "type": "钩子" | "爽点" | "卡点",
  "timestamp": "MM:SS",
  "intensity": 1-5,
  "setup_callback": "what earlier scene set this up",
  "payoff_callback": "what later scene resolves this"
}
```

**字段语义:**

- **type** — 3 选 1:`钩子`(开场抓取,对应 5-type taxonomy 任一)/ `爽点`(情绪峰值兑现,对应 conflict-escalation.md §爽点 peak)/ `卡点`(未解悬念,对应 paywall-design.md §3-tier strength)
- **timestamp** — `MM:SS` 格式;跨集场景由 `setup_callback` / `payoff_callback` 中的 `S1E03 02:15` 形式承载,timestamp 字段本身仍只表示本集内时间
- **intensity** — 1-5 整数(对应 conflict-escalation.md 1-10 尺度折半;5 = 钩子 🎯 / 爽点 峰值 / 卡点 🟢)
- **setup_callback** — 自由字符串,**可跨集回指**(例如 `"S1E03 02:15 — 主角在病床前发誓复仇"`);对于开场 钩子 可填 `"none — cold open"`
- **payoff_callback** — 自由字符串,**可跨集前瞻**(例如 `"S1E07 — 反派真实身份揭露"`);对于未解 卡点 可填 `"S1E0N+1 opening"` 表示下集开场兑现

**3 个具体示例(每类 marker 各 1 个,均展示多集 callback 支持):**

```json
{
  "type": "钩子",
  "timestamp": "00:00",
  "intensity": 5,
  "setup_callback": "none — cold open (S1E01 opening hook)",
  "payoff_callback": "S1E01 01:30 — 主角身份首次被路人认出"
}
```

```json
{
  "type": "爽点",
  "timestamp": "01:12",
  "intensity": 5,
  "setup_callback": "S1E03 02:15 — 主角在病床前发誓复仇",
  "payoff_callback": "S1E05 00:45 — 反派在公司会议室被打脸"
}
```

```json
{
  "type": "卡点",
  "timestamp": "01:28",
  "intensity": 5,
  "setup_callback": "S1E04 — 主角发现养父遗书暗示真凶身份",
  "payoff_callback": "S1E06 opening — 真凶登门挑衅"
}
```

## Key Parameters

### hook_strength_target

- **opening hook(0-3s)**:目标 ≥ ✅ strong(4/5 tier);🎯 bullseye 是 stretch goal;⚠️ weak 必须迭代或前贴更强 hook
- **secondary hook(集中段)**:目标 ≥ ⚠️ weak 可接受;✅ strong 是理想
- **5-tier 评分阈值**:见 [`references/three-second-hooks.md`](./references/three-second-hooks.md) §5-Tier Strength Scoring

### 卡点_density

- **每 10 集 短剧 最少 卡点 数**:3-5 个(权威源:[`references/paywall-design.md`](./references/paywall-design.md) §付费卡点 Density Rules)
- **付费集 强制硬卡点**:每个付费集末必须有 1 个 🟢 hard 卡点
- **集中段 软卡点(可选)**:放置在 ~40-60% runtime
- **卡点 间隔**:每 2-3 集至少 1 个 卡点(避免连续 3+ 集无 卡点)

### 节奏_density

- **1.5x pace rule**:平均镜头 ≤ 1.5s(竖屏 9:16 硬约束;权威源:[`references/paywall-design.md`](./references/paywall-design.md) §1.5x Pace Rule + [`references/vertical-pacing.md`](./references/vertical-pacing.md) §竖屏 vs 横屏)
- **≤3s dead air**:不允许连续 ≥ 3s 静止 / 静默;BGM swell 与情绪 close-up 是仅有的例外(可延至 4-5s)
- **BGM coupled_beat 同步**:cut 必须落在 audio_pipeline.composer.coupled_beat 时间戳(详见 [`references/vertical-pacing.md`](./references/vertical-pacing.md) §BGM Sync Requirements)
- **字幕 safe zone**:避开上 1/3(状态栏)与下 1/3(评论 / 互动区),字幕占 frame ~15-20%

## Per-Platform 爆款公式 Branching

同一 master cut 在 5 种 平台 × 受众 组合下的差异化留存策略。本节给出每分支的关键差异点,具体公式 / 阈值 / 平台规则以 `references/paywall-design.md`、`references/vertical-pacing.md §Multi-Platform Pacing Variation` 与 Phase 1 [`platform-specs-{douyin,kuaishou,miniprogram}.md`](../compliance_gate/references/) 为准。

### 抖音-男频

- **核心动机:** 逆袭 / 复仇 / 装穷打脸 / 阶级碰撞 —— 男性受众追求"压抑 → 释放"的爽感曲线;复仇兑现的瞬时高潮是付费驱动力(跨链 [`../../compliance_gate/references/viral-element-catalog.md`](../compliance_gate/references/viral-element-catalog.md) 冲突钩 / 反差钩 类型条目 + 风险徽章)
- **情感曲线:** 阶梯式 上升(对应 [`references/conflict-escalation.md`](./references/conflict-escalation.md) §The 阶梯式 Escalation Ladder)—— 钩子 6/10 → 击中点 7/10 → 中段升级 8/10 → 爽点 9-10/10 → 卡点 悬而未决
- **节奏密度:** 最快 cut 密度(1.5s 平均镜头,见 [`references/vertical-pacing.md`](./references/vertical-pacing.md) §Multi-Platform Pacing Variation);抖音算法权重 完播率 ~35% *estimated*,快切是硬约束
- **付费卡点位置:** 第 5-7 集设 付费门槛(详见 [`../../compliance_gate/references/platform-specs-douyin.md`](../compliance_gate/references/platform-specs-douyin.md) §付费机制);硬卡点强度目标 🟢 must-watch-next(复仇将近但被打断)
- **典型案例:** (1)「战神归来」开场 3 秒 hook = 战神雨中独行 + 第一句台词"我回来了",30 集主线"复仇兑现阶梯";(2)「霸总装穷」反差钩,主角穿破西装被前任羞辱 → 第 6 集末 硬卡点"奶奶的遗嘱居然是…"

### 抖音-女频

- **核心动机:** 闪婚 / 萌宝 / 隐藏身份 / 婆媳冲突 / 替身的爱 —— 女性受众追求"误解 → 揭露 → 圆满"的共情曲线;情感兑现(和解 / 相认)是付费驱动力(跨链 viral-element-catalog.md 情感钩 类型 + 风险徽章 —— 替身 / 肢体接触 边界场景属 🟡)
- **情感曲线:** V 型反转(低谷误解 → 高谷揭露 → 圆满);阶梯式 在中段升级部分穿插
- **节奏密度:** 略慢于男频(1.5-2s 平均镜头);情绪 close-up 可破例延至 4-5s(BGM swell 例外,见 [`references/vertical-pacing.md`](./references/vertical-pacing.md) §BGM Swell Exceptions)
- **付费卡点位置:** 第 5-7 集设 付费门槛;硬卡点强度目标 🟢(情感即将揭穿但被打断,例如"她终于要说出真名了…")
- **典型案例:** (1)「替身的爱」开场 = 女主为姐姐代嫁 + 第一句"我不是她",🟡 风险:替身 暧昧 需 跨链 catalog 降级方案 保留 ≥ 70% 钩子强度;(2)「萌宝神助攻」隐藏身份钩,霸总意外救下的孩子其实是自己的骨肉

### 快手-草根

- **核心动机:** 普通人 / 家庭 / 逆袭 / 情感共鸣 —— 快手受众更重视"接地气"与"真实感",草根美学 是核心;避炫富画面信号(豪车 / 名表 是平台专属 红线,跨链 [`../../compliance_gate/references/platform-specs-kuaishou.md`](../compliance_gate/references/platform-specs-kuaishou.md) §内容红线)
- **情感曲线:** 线性上升(无陡峭反转);阶梯式 较缓(2-3 级而非 5 级);情感共鸣 触发器权重最高
- **节奏密度:** 较慢于抖音(1.5-2.5s 平均镜头);草根美学 避免过度快切显得"刻意"
- **付费卡点位置:** 第 6-10 集设 付费门槛(晚于抖音);硬卡点 较柔和(🟡 curious-but-skippable 可接受 —— 快手付费意愿较低,过强 卡点 反而劝退)
- **典型案例:** (1)「打工人的团圆」开场 = 工地直播 + 女儿视频"爸爸你什么时候回家",主转 转发 trigger = 情感共鸣 + 实用价值;(2)「婆媳误会」家庭伦理 公式,大团圆收尾;避炫富 → 主角逆袭后仍住老房子

### 小程序剧-长集数

- **核心动机:** 长剧集悬念 / 多集反转 / 季末解谜 —— 微信小程序剧 单集 3-5 min(最长形态),叙事容量远大于抖快;serial cliffhanger 是核心商业模式
- **情感曲线:** 多峰 阶梯式(每集 1 峰,跨集 callback 织成悬念网);多集 callback 是常态(setup_callback 跨集回指 S1E03,payoff_callback 跨集前瞻 S1E07)
- **节奏密度:** 单集内部慢(2-3s 平均镜头,因集长更长);但 卡点 密度最高(每集末硬卡点 + 集中段软卡点)
- **付费卡点位置:** 第 3-5 集设 付费门槛(最早);每集末必有 🟢 hard 卡点(详见 [`../../compliance_gate/references/platform-specs-miniprogram.md`](../compliance_gate/references/platform-specs-miniprogram.md) §付费机制);双重 备案 触发(广电 + 微信小程序)
- **典型案例:** (1)12 集 拟人化 漫剧「锁着的房间」每集末硬卡点,setup 跨集回指 S1E01 一封信,payoff 前瞻 S1E12;(2)30 集真人短剧「家族秘辛」,每三集一次反转,季末解谜

### 通用 fallback

- **核心动机:** 当平台未知 / 多平台分发时,采用最保守的"普适情感 + 通用悬念"组合;不依赖任何平台专属 爆款公式;🟡 / 🔴 风险元素一律按 catalog 降级,绝不存侥幸
- **情感曲线:** 阶梯式 上升(最普适形态);避免 V 型反转(反转在某些平台失效)与多峰(对短集数形态过载)
- **节奏密度:** 中等(1.5-2s 平均镜头);兼顾快平台(抖音)与慢平台(快手)
- **付费卡点位置:** 第 5-7 集设 付费门槛(中性区间);3-5 / 10 集 卡点 密度;硬卡点 强度目标 🟢
- **典型案例:** (1)未知平台的「母亲遗愿」开场,情感钩 + 悬念钩 双锚;主转 转发 trigger = 情感共鸣;(2)未知平台的「神秘来电」,悬念钩 驱动,通用 30s setup 后进入主线

## Hook Design Workflow

设计开场 3 秒钩子的标准 5 步流程。每步必跨链 [`references/three-second-hooks.md`](./references/three-second-hooks.md) 对应章节,不允许凭直觉跳过。

1. **选型 5-type taxonomy** — 根据 平台 × 受众 分支 + 题材,从 情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩 5 类中选 1 类(见 [`references/three-second-hooks.md`](./references/three-second-hooks.md) §Taxonomy);不允许凭空新增类别
2. **帧级拆解 0-1s / 1-2s / 2-3s** — 按 attention-grab / context-establish / hook-pin 三段式设计(见 [`references/three-second-hooks.md`](./references/three-second-hooks.md) §3-Second Frame Structure);不允许只写"感觉"
3. **5-tier 强度评分** — 用 🎯 / ✅ / ⚠️ / ❌ / 💀 评 current draft 强度(见 [`references/three-second-hooks.md`](./references/three-second-hooks.md) §5-Tier Strength Scoring);必须给出每 tier 的具体触发条件
4. **迭代或前贴** — 若评分 ≤ ⚠️,必须迭代改写或前贴更强 hook(直接接受 ⚠️ 视为不合格);每轮迭代后回到 §3 重新评分
5. **输出 钩子 marker** — 按 §Marker Schema 输出 `{type:"钩子", timestamp:"00:00", intensity:N, setup_callback:"none — cold open", payoff_callback:"S1E01 MM:SS — ..."}`;此 marker 将被 `screenplay.emotion_curve` 消费

## 卡点 Placement Workflow

设计全季 卡点 放置计划的标准 5 步流程。每步必跨链 [`references/paywall-design.md`](./references/paywall-design.md) + [`references/conflict-escalation.md`](./references/conflict-escalation.md)。

1. **判定 集数 + 平台分支** — 确认 master cut 集数(如 10 / 30 集)+ 目标平台分支(抖音-男频 / 抖音-女频 / 快手-草根 / 小程序剧-长集数 / 通用 fallback)
2. **应用密度规则** — 按 [`references/paywall-design.md`](./references/paywall-design.md) §付费卡点 Density Rules 放置:每 10 集 3-5 个 卡点;每 2-3 集至少 1 个;付费集末必有 1 个硬卡点
3. **放置 软卡点** — 集中段 ~40-60% runtime 可选放置 1 个软卡点(可选,非强制);软卡点 不强制付费但提升中段粘性
4. **3-tier 强度评分** — 对每个 卡点 用 🟢 must-watch-next / 🟡 curious-but-skippable / 🔴 weak-resolve 评分(见 [`references/paywall-design.md`](./references/paywall-design.md) §3-Tier Strength);硬卡点 目标 🟢,软卡点 🟡 可接受
5. **输出 卡点 marker** — 按 §Marker Schema 输出 `{type:"卡点", timestamp:"MM:SS(episode end)", intensity:N, setup_callback:"S1E0X — ...", payoff_callback:"S1E0Y — ..."}`;`payoff_callback` 必须指到具体的未来集 / 场景(不允许填 "next episode" 这种模糊表述)

## RAG Invocation

本专家的 RAG 检索完全 provider-agnostic。在生成任何 hook / 卡点 / marker 输出前,按以下顺序检索上下文:

- 当前 平台 × 受众 分支对应的 5-type taxonomy 条目([`references/three-second-hooks.md`](./references/three-second-hooks.md) §Taxonomy)
- 当前分支对应的 阶梯式 升级阶梯([`references/conflict-escalation.md`](./references/conflict-escalation.md) §The 阶梯式 Escalation Ladder)
- 当前平台 付费机制 + 付费门槛 位置([`../../compliance_gate/references/platform-specs-{douyin,kuaishou,miniprogram}.md`](../compliance_gate/references/) §付费机制)
- 竖屏 cut density + BGM sync 要求([`references/vertical-pacing.md`](./references/vertical-pacing.md) §Cut Density Rules + §BGM Sync Requirements)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:

```
tags="expert:hook_retention,domain:three-second-hooks"
tags="expert:hook_retention,domain:conflict-escalation"
tags="expert:hook_retention,domain:paywall-design"
tags="expert:hook_retention,domain:vertical-pacing"
tags="expert:hook_retention,domain:platform-<platform>"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)+ Phase 1 [`../../compliance_gate/references/`](../compliance_gate/references/) 跨链 catalog。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名(veo3.1 / kling-v3-4k / FLUX 2 / Stable Audio / CosyVoice 等)。涉及具体模型时使用 `<video_gen_primary>` / `<image_gen_primary>` / `<audio_gen_primary>` 占位符(见 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder 表)。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Quality Thresholds

| Metric | Target |
|--------|--------|
| `hook_strength` | opening hook ≥ ✅ strong(4/5 tier);secondary hook ≥ ⚠️ weak 可接受;🎯 bullseye 是 stretch |
| `完播率_proxy` | 1.5x pace rule 满足 + ≤3s dead air + BGM coupled_beat 同步(同步率目标见 [`references/paywall-design.md`](./references/paywall-design.md) §BGM-Driven Sync;degree of alignment is qualitative in v1, quantitative measurement deferred to Phase 6) |
| `卡点_density` | 每 10 集 3-5 个 + 每 2-3 集至少 1 个 + 100% 付费集末为 🟢 hard 卡点 |
| `转发_trigger_coverage` | 每集至少激活 5 类 转发 trigger 中的 ≥ 2 类(情感共鸣 / 反转冲击 / 共识认同 / 视觉震撼 / 实用价值) |

## Collaboration

- **<- screenplay**:接收 `script.json` + scene-list 做开场 hook 插入点推荐(剧本结构决定 hook 锚定位置)
- **<- compliance_gate**:接收 `distribution_cuts.json` + 平台 付费门槛 位置约束 + 红线 风险徽章(合规闸门决定 hook 强度上限)
- **<- editor**:接收 `cut_density` 反馈做 完播率 复检(剪辑决定 1.5x pace rule 是否真达成)
- **-> screenplay**:输出 `钩子_爽点_卡点_markers.json` 给 `emotion_curve` 离散锚点集成(Phase 3 screenplay 重构将原生消费)
- **-> editor**:输出 1.5x pace / ≤3s dead air / BGM coupled_beat 节奏约束(给 `cut_density` 决策输入)
- **-> audio_pipeline (composer sub-step)**:输出 BGM sync 时间戳要求(给 `coupled_beat` 对齐;**单向 edge** —— audio_pipeline 不需要回调 HOOK,只需把 cut 时间戳纳入 coupled_beat 设计,CONTEXT D-7)
- **-> compliance_gate**:输出 `hook_design.json` + `卡点_placement.json` 给 🟡 / 🔴 风险元素复审(关闭 Phase 1 单向 edge 合同)

## What NOT to do

- **不要硬编码 provider 专属工具名。** 严禁在 SKILL.md body 中出现具体 provider 专属工具名作为直接调用(以 `fact_store` / `mem0_search` / `cosyvoice_api` 为反例 —— 这些只是历史警示,不允许在 body 其它任何位置复用);一律用 `<memory_plugin>` / `<rag_search>` / `<video_gen_primary>` / `<image_gen_primary>` / `<audio_gen_primary>` 占位符(参考 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) 与 [`scripts/verify_skill_references.py`](../../../../../scripts/verify_skill_references.py) allowlist)
- **不要在付费集末放 🟡 或 🔴 卡点。** Workflow §4 强制要求硬卡点强度目标 🟢;🟡 只在集中段 软卡点 可接受;付费集末 🔴 weak-resolve 等于付费转化漏斗泄漏
- **不要把所有钩子评 🎯 不做诚实批判。** 5-tier 评分的存在意义是区分;若全部 🎯 等于未评分 —— 至少 1 个 secondary hook 应该是 ✅ 或 ⚠️
- **不要在 SKILL.md body 重复 Phase 1 付费机制 合规数字。** 备案 / 付费门槛 / 分账比例 / 退款规则 由 [`../../compliance_gate/references/platform-specs-*.md`](../compliance_gate/references/) 独占 —— HOOK body 只引用数字 + 跨链,不重述原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)
- **不要在 body 中引入新模型名。** 若需引用具体模型,必须先加入 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist;否则一律用 `<video_gen_primary>` / `<image_gen_primary>` / `<audio_gen_primary>` 占位符(防止 [`scripts/verify_skill_references.py`](../../../../../scripts/verify_skill_references.py) `--strict` 误报)
- **不要忽略 multi-episode callback。** marker schema 的 `setup_callback` / `payoff_callback` 字段对 小程序剧-长集数 分支是核心 —— 填 "next episode" 这种模糊值视为不合格,必须指到具体的 `S1E0X MM:SS`
