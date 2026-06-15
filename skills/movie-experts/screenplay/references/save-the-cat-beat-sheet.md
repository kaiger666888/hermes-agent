# Save the Cat Beat Sheet — Snyder 15-Beat Structure Adapted to 60-180s 短剧

**Source:** *Save the Cat!* (Blake Snyder, 2005, Studio City Productions) + 短剧 创作者 公开 创作经验
**Copyright:** Fair Use — paraphrased beat-sheet heuristics (page-count targets, "double bump" rule) only; no reproduction of Snyder's scene walkthroughs or example loglines (see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 把 Blake Snyder 在 *Save the Cat!* (2005) 中提出的 15-beat 节拍表(原本为 110 页长片设计)适配到 短剧 的 60s / 90s / 180s 单集形态,以及 10-80 集连续剧形态。本 ref 是 Snyder 节拍数值(每拍的目标页数 / 目标 runtime 比例 / "Save the Cat" 时刻定义 / "double bump" 连续触发规则)的**唯一真相源** —— SKILL.md body 仅引用数字 + 跨链,不重述原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([钩子](../../_shared/glossary.md#钩子-hook) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel))。

Snyder 的 15-beat 模型之所以适配 短剧,是因为它把"观众情绪何时被驱动"这件事拆成了 15 个**可定位的剧情节点**,而不是"凭感觉写"。短剧 的 runtime 虽然只有长片的 1/60 ~ 1/20,但情绪驱动的结构同构 —— 只是把"每页 ≈ 1 分钟"换成"每 3-9 秒一个节拍"。本 ref 给出精确的 runtime 换算表。

---

## The 15 Beats

Snyder 的 15-beat 节拍表按 110 页长片规范化。每一拍都有**精确的目标页数**(对应 runtime 比例)。下表列出全部 15 拍的原始页数 + 对应 runtime 比例:

| # | Beat 名称 | 原始页数 (110 页长片) | Runtime 比例 | 功能 |
|---|-----------|----------------------|--------------|------|
| 1 | **Opening Image** | p.1 | 0-1% | 视觉化呈现主角的"起始状态"(通常是缺陷态) |
| 2 | **Theme Stated** | p.5 | ~5% | 某角色(常为次要角色)说出主题句 —— 主角此时尚未理解 |
| 3 | **Set-Up** | p.1-10 | 1-10% | 介绍主角的世界、缺陷、机会 |
| 4 | **Catalyst** | p.10 (±3) | ~10% | 触发事件 —— 打破主角的现状,通常是外部强加的 |
| 5 | **Debate** | p.10-20 | 10-20% | 主角对 Catalyst 的犹豫 / 恐惧 / 挣扎 |
| 6 | **Break into Two** | p.20 (±3) | ~20% | 主角做出决定,进入第二幕(新世界) |
| 7 | **B-Story** | p.30 (±5) | ~30% | 次要故事线启动(通常是爱情线 / 友情线) |
| 8 | **Fun & Games** | p.30-55 | 30-50% | "承诺的大前提"兑现 —— 观众来看这部片就是为了这一段 |
| 9 | **Midpoint** | p.55 (±3) | ~50% | **结构性转折** —— 假胜利 (false victory) 或假失败 (false defeat) |
| 10 | **Bad Guys Close In** | p.55-75 | 50-68% | 外部对手反扑 + 内部分裂 —— 局势恶化 |
| 11 | **All Is Lost** | p.75 (±3) | ~68% | **最低点** —— 主角失去关键资源 / 盟友 / 信念 |
| 12 | **Dark Night of the Soul** | p.75-85 | 68-77% | 主角的内省 / 绝望 / 觉醒前夜 |
| 13 | **Break into Three** | p.85 (±3) | ~77% | 主角找到解决方案(synthesis —— 融合 A 故事 + B 故事) |
| 14 | **Finale** | p.85-110 | 77-95% | 主角执行新方案,击败对手 / 解决问题 |
| 15 | **Final Image** | p.110 | 95-100% | 与 Opening Image 对照的视觉化呈现(主角的"完成态") |

**关键数字(heuristic 1):** Catalyst 必须在 **p.10 ± 3**(runtime 比例 ~10%)。对 90s 短剧 这意味着 Catalyst 在 **~9s**(精确范围 6-12s);对 180s 短剧 在 **~18s**。Catalyst 晚于 p.15(90s 的 13s / 180s 的 27s)会被 Snyder 判为"前戏过长",完播率 会受直接冲击 —— 因为观众在前 10% runtime 还没看到"为什么我要看下去"。

**关键数字(heuristic 2):** Midpoint 必须在 **p.55 ± 3**(runtime 比例 ~50%),且**必须发生极性反转**(假胜利 → 接下来会崩;假失败 → 接下来会触底反弹)。没有极性反转的 Midpoint 等同于没有 Midpoint —— 观众会觉得"中段平了"。这与 McKee 的 value-shift 规则同构(见 [`mckee-scene-design.md`](./mckee-scene-design.md) §Value-Shift Rule)。

**关键数字(heuristic 3):** All Is Lost + Dark Night of Soul 必须连续触发(见下方 §Double-Bump Rule)。

**关键数字(heuristic 4):** B-Story 必须在 **p.30 ± 5**(runtime 比例 ~27%)启动。B-Story 通常是爱情线 / 友情线,它的功能不是"第二条剧情线",而是**承载 Theme Stated 的主题**。主角在 A-Story(主线)中行动,在 B-Story 中学习主题。90s 短剧 的 B-Story 启动在 ~24s;180s 在 ~48s。短剧 常把 B-Story 与 Fun & Games 段重叠(因为 runtime 紧张,不允许独立的 B-Story 拍)。

**关键数字(heuristic 5):** Fun & Games 段(p.30-55,~30-50% runtime)是**观众留存的核心段** —— 这是"承诺的大前提"兑现的地方。如果观众是来看"装穷打脸"的,Fun & Games 就是打脸发生的地方;如果观众是来看"战神归来"的,Fun & Games 就是战神展示实力的地方。90s 短剧 的 Fun & Games 在 18-40s(22s 窗口);这段的 击中点 密度应 ≥ 3 个(见 [`cn-shortdrama-structure.md`](./cn-shortdrama-structure.md) §90s 短剧 Time Budget)。

### 15 Beats 之间的"松紧"节奏(heuristic)

Snyder 的 15-beat 模型不是均匀分布的 —— 有些 beat 是"紧拍"(runtime 短,情绪密度高),有些是"松拍"(runtime 长,情绪密度低)。这种松紧交替是节奏感的核心。

**关键 heuristic 6:** beat 的松紧分布:

| beat 区间 | 松紧 | runtime 占比 | 情绪密度 |
|-----------|------|--------------|----------|
| Opening Image → Catalyst (beat 1-4) | 紧 | ~10% | 高(钩子 + 触发) |
| Debate (beat 5) | 松 | ~10% | 低(主角犹豫) |
| Break into Two → Fun & Games (beat 6-8) | 紧 | ~20-30% | 高(行动 + 兑现) |
| Midpoint (beat 9) | 紧(单点) | ~1% | 极高(极性反转) |
| Bad Guys Close In (beat 10) | 松 | ~18% | 中(局势恶化) |
| All Is Lost → Dark Night (beat 11-12) | 紧(连续) | ~9% | 高(触底) |
| Break into Three → Finale (beat 13-14) | 紧 | ~18% | 高(反弹 + 解决) |
| Final Image (beat 15) | 紧(单点) | ~5% | 高(对照收尾) |

**关键 heuristic 7:** 松拍(Debate / Bad Guys Close In)的 runtime 不应超过紧拍的 1.5 倍。如果松拍过长,节奏感会变成"拖";如果完全没有松拍,节奏感会变成"喘不过气"。短剧 因 runtime 紧张,常把松拍压缩到极致 —— 90s 短剧 的 Debate 仅 6-9s(长片是 10 页 = ~10 分钟)。

---

## Save-the-Cat Moment Defined

"Save the Cat" 时刻是 Snyder 最知名的 heuristic:**主角在前 10 分钟(p.1-10)必须做一件让观众产生共情 / 同情 / 好感的事**。名字源于经典桥段"主角爬树救一只猫"。这个时刻的功能不是推动剧情,而是**让观众愿意跟随这个主角 90 / 120 / 180 分钟**。

### 为什么 短剧 尤其需要 Save the Cat 时刻

短剧 的 runtime 预算极紧(60-180s 单集),创作者常误以为"没时间做 Save the Cat"。这是致命误判:

1. **短剧观众决策更快。** 长片观众在前 10 分钟决定是否继续看;短剧观众在前 **3-5 秒**就决定(完播率 在 7s 后开始陡降,见 [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve)。Save the Cat 时刻必须**压缩到前 3-5 秒**。
2. **男频 逆袭 短剧 的特殊变体。** [男频](../../_shared/glossary.md#男频-male-oriented-channel) 短剧 常用"反向 Save the Cat" —— 主角在前 3 秒展示**极端弱势**(被羞辱 / 被背叛 / 装穷),而非"做好事"。共情机制从"我喜欢他"变为"我同情他 / 我期待他逆袭"。这与 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 兑现形成 setup-payoff 闭环(见 [`cn-shortdrama-structure.md`](./cn-shortdrama-structure.md) §90s 短剧 Time Budget)。
3. **女频 闪婚 / 萌宝 短剧 的特殊变体。** [女频](../../_shared/glossary.md#女频-female-oriented-channel) 短剧 常用"情感锚 Save the Cat" —— 主角在前 3 秒展示**强烈的情感脆弱**(为孩子 / 为家人 / 为爱人做出的牺牲),共情机制是"我理解她的痛"。

### 3 个具体的 短剧 Save the Cat 示例

1. **男频-反向 Save the Cat(90s, 战神归来):** 0-2s — 主角淋着雨,西装破旧,走过曾经属于自己的大楼;3s — 保安拦住他"先生,这里是私人区域"。**共情触发:** 观众同情弱势 + 好奇"他怎么会变成这样"。这与 [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §反差钩 类型同构。
2. **女频-情感锚 Save the Cat(120s, 萌宝神助攻):** 0-2s — 女主抱着发烧的孩子在医院走廊奔跑;3s — 前台"先交押金"。女主翻遍口袋,只有几张零钱。**共情触发:** 母性 + 经济焦虑的双共振。对应 [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §情感钩 类型。
3. **小程序剧-悬念 Save the Cat(180s, 家族秘辛):** 0-2s — 主角收到父亲死前寄出的信,信封上写着"等我死后再拆";3s — 主角拆信,镜头特写信纸,但内容被遮挡。**共情触发:** 悬念 + 丧亲之痛的复合。对应 [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §悬念钩 类型。

### Save the Cat 时刻的失败模式

以下是 短剧 创作者常犯的 Save the Cat 失败模式:

| 失败模式 | 描述 | 修复 |
|----------|------|------|
| **"无共情锚"** | 主角在前 3-5s 只是"出场",没有做任何让观众共情 / 同情 / 好感的事 | 插入一个具体的共情行动(救猫 / 展示脆弱 / 为他人牺牲) |
| **"共情过载"** | 前 3-5s 塞入过多共情元素(主角同时被羞辱 + 生病 + 失去亲人) | 只保留 1 个最强的共情锚;其余留到后续场景 |
| **"共情与主线脱节"** | Save the Cat 时刻与主线无关(主角救猫,但主线是复仇) | 让 Save the Cat 行动暗示主线主题(例如:主角救的不是猫,而是被欺负的孩子 —— 暗示主角的正义感) |
| **"反向 Save the Cat 过度"** | [男频](../../_shared/glossary.md#男频-male-oriented-channel) 主角在前 3s 展示极端弱势,但弱势程度过深(被 torture / 被虐待)导致观众不适 | 保持"共情弱势"而非"创伤弱势";目标是让观众同情,而非让观众难受 |

### Save the Cat 与 Theme Stated 的关系(heuristic)

**关键 heuristic 10:** Save the Cat 时刻与 Theme Stated(beat 2)应形成**主题闭环**。Save the Cat 展示主角的"起始美德 / 缺陷",Theme Stated 提出主角需要学习的"主题";到 Finale 段,主角通过 Save the Cat 美德的**升级版**解决主线问题。

- **男频 逆袭 示例:** Save the Cat = 主角默默捡起被踩的花(隐忍美德);Theme Stated = "真正的强者不需要证明自己"(次要角色台词);Finale = 主角用隐忍后的实力击败反派(隐忍美德的升级版)。
- **女频 闪婚 示例:** Save the Cat = 女主为孩子牺牲(母爱美德);Theme Stated = "爱是看见真实的对方"(次要角色台词);Finale = 女主用真实的自己赢得男主的爱(母爱美德的升级版 —— 从为孩子牺牲升级为为自己和爱人共同选择)。

这个主题闭环是 Snyder 模型的深层结构 —— Save the Cat 不只是"让观众喜欢主角",而是为 Finale 的主题兑现埋下种子。

---

## 短剧 Adaptation: 60s / 90s / 180s Beat Budgets

把 110 页长片的 15-beat 模型按 runtime 比例换算到 短剧 的 3 种典型集长。换算规则:**runtime 比例保持不变,但 beat 数量必须压缩**(15 拍 → 7-10 拍,因为 60-180s 不足以容纳 15 个独立节拍)。

### 90s 短剧(抖音 单集标准形态)Beat Budget

| Snyder Beat | Runtime 目标(90s) | 保留 / 合并 / 删除 | 说明 |
|-------------|---------------------|--------------------|------|
| Opening Image | 0-1s | 保留 | 与 Save the Cat 时刻合并 —— 0-3s 即是 Opening Image + Save the Cat + [钩子](../../_shared/glossary.md#钩子-hook) |
| Theme Stated | ~5s | 合并到 Catalyst | 短剧 不单独留 Theme Stated 拍;主题句融入 Catalyst 的台词 |
| Set-Up | 1-9s | 保留(压缩) | 与 Save the Cat / 钩子 重叠;1-9s 内交代主角处境 |
| **Catalyst** | **~9s (6-12s)** | **保留** | 触发事件 —— 在 9s 处发生(对应 Snyder p.10) |
| Debate | 9-18s | 保留(压缩) | 主角的犹豫必须 ≤ 9s,否则 完播率 崩 |
| Break into Two | ~18s | 合并到 Fun & Games | 短剧 不留独立 Break into Two 拍;主角直接进入行动 |
| B-Story | ~27s | 合并到 Fun & Games | 次要故事线(常为爱情线)在 Fun & Games 中穿插 |
| Fun & Games | 18-40s | 保留(压缩) | 22s 的"承诺兑现"段 |
| **Midpoint** | **~45s (42-48s)** | **保留** | 极性反转 —— 在 45s 处发生(对应 Snyder p.55) |
| Bad Guys Close In | 45-60s | 保留 | 局势恶化 15s |
| **All Is Lost** | **~67s (64-70s)** | **保留** | 最低点 —— 在 67s 处发生(对应 Snyder p.75) |
| Dark Night of Soul | 67-72s | 合并到 All Is Lost | 与 All Is Lost 连续触发(double bump) |
| Break into Three | ~72s | 合并到 Finale | 主角找到解决方案的瞬间融入 Finale 开头 |
| Finale | 72-80s | 保留(压缩) | 主角执行新方案 8s |
| Final Image + [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) | 80-90s | 保留 | 10s 的收尾 + 卡点 cliffhanger(对应 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §付费卡点 Density Rules) |

### 180s 短剧(小程序剧 单集形态)Beat Budget

180s 的集长允许保留更多 beat,但比例不变:

| Snyder Beat | Runtime 目标(180s) | 说明 |
|-------------|---------------------|------|
| Opening Image + Save the Cat + 钩子 | 0-3s | 与 90s 相同 —— 3 秒钩子规则不随集长变化 |
| Set-Up | 3-18s | 15s 的 setup(比 90s 的 8s 更从容) |
| **Catalyst** | **~18s (12-24s)** | 触发事件 |
| Debate | 18-36s | 主角犹豫 18s(允许更深的心理戏) |
| Break into Two | ~36s | 主角进入第二幕 |
| B-Story + Fun & Games | 36-90s | 54s 的承诺兑现段(可容纳 2 个 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point)) |
| **Midpoint** | **~90s (84-96s)** | 极性反转 |
| Bad Guys Close In | 90-122s | 局势恶化 32s |
| **All Is Lost + Dark Night of Soul** | **~122-138s** | double bump 16s |
| Break into Three + Finale | 138-162s | 主角找到方案 + 执行 24s |
| Final Image + 卡点 | 162-180s | 18s 收尾 + 卡点 |

### 60s 短剧(抖音 极短形态)Beat Budget

60s 是 短剧 的下限,beat 压缩到极致:

| Snyder Beat | Runtime 目标(60s) | 说明 |
|-------------|---------------------|------|
| Opening Image + Save the Cat + 钩子 | 0-3s | 3 秒钩子规则不变 |
| Set-Up + Catalyst | 3-6s | 3s 内完成 setup + 触发事件(高度压缩) |
| Debate + Break into Two | 6-12s | 主角犹豫 6s(几乎是一闪而过) |
| Fun & Games | 12-30s | 18s 的承诺兑现段(仅容纳 1 个 击中点) |
| **Midpoint** | **~30s (27-33s)** | 极性反转 |
| Bad Guys Close In + All Is Lost + Dark Night | 30-45s | 15s 的连续恶化(double bump) |
| Break into Three + Finale | 45-54s | 主角执行 9s |
| Final Image + 卡点 | 54-60s | 6s 收尾 + 卡点 |

**关键 heuristic:** 60s 短剧 的 Debate 只能 ≤ 6s,否则 完播率 在 12s 后崩。这与 [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve 的"8-12s 无 击中点 则 attention drops ≥ 15%"数据吻合。

### Beat Budget 跨集长形态(heuristic)

短剧 / 小程序剧 是连续剧形态,单集 beat budget 之上还有跨集的 beat 分布。关键 heuristic:

**关键 heuristic 8:** 跨集 season arc 中,每一集都应遵循单集 beat budget(90s / 180s / 60s 表),但不同集的 beat 重点不同:

| 集 类型 | beat 重点 | 说明 |
|---------|-----------|------|
| **opener 集 (ep 1)** | Opening Image + Save the Cat + 钩子 + Catalyst | opener 集的核心任务是"钩住观众",Catalyst 必须在前 10% runtime 发生 |
| **escalation 集 (ep 2-6)** | Fun & Games + Midpoint + 击中点 密度 | escalation 集的核心任务是"兑现大前提",Fun & Games 段应占最大 runtime 比例 |
| **卡点 集 (付费门槛集)** | All Is Lost + Dark Night + 卡点 cliffhanger | 卡点 集的核心任务是"触发付费",double-bump 必须完整,卡点 强度 🟢 |
| **finale 集 (ep 10)** | Break into Three + Finale + Final Image | finale 集的核心任务是"兑现终极 爽点",Finale 段应占最大 runtime 比例 |

**关键 heuristic 9:** finale 集的 Final Image 必须与 opener 集的 Opening Image 形成**视觉对照**。这是 Snyder 模型的核心收尾机制 —— Opening Image 展示主角的"起始缺陷态",Final Image 展示主角的"完成成长态"。短剧 中这种对照通常通过**同一场景 / 同一机位 / 同一角色的不同状态**实现。例如:opener 集主角淋雨走过大楼(弱);finale 集主角乘车驶向同一栋大楼(强)。

### Beat Budget 验证清单

每个 短剧 单集的 beat budget 应通过以下验证:

1. [ ] Catalyst 在前 ~10% runtime(90s: ~9s / 180s: ~18s / 60s: ~6s)
2. [ ] Midpoint 在 ~50% runtime 且发生极性反转
3. [ ] All Is Lost + Dark Night 连续触发(double-bump)
4. [ ] Finale 段占 ≥ 15% runtime(主角执行解决方案)
5. [ ] Final Image 与 Opening Image 形成视觉对照
6. [ ] 钩子 在 0-3s
7. [ ] [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger 在集末 2-5s

---

## Double-Bump Rule

Snyder 的 "double bump" 规则:**All Is Lost + Dark Night of Soul 必须连续触发,中间不允许有"喘息"或"虚假希望"。** 原始 110 页长片中,这两拍占据 p.75-85 的 10 页窗口(~9% runtime)。

### 短剧 中的 Double-Bump 适配

短剧 的 runtime 不允许 10 页(= 9% runtime)的 double bump 窗口。适配规则:

| 集长 | Double-Bump 窗口 | All Is Lost | Dark Night of Soul |
|------|------------------|-------------|---------------------|
| 90s | ~10s(67-77s,但 180s 的 10 页对应 ~16s;90s 按比例 ~8s) | 67s ± 3s | 70-77s(与 All Is Lost 连续) |
| 180s | ~16s(122-138s) | 122s ± 6s | 128-138s |
| 60s | ~6s(30-45s 中的后 6s) | 39s ± 3s | 42-45s |

**关键 heuristic:** Double-Bump 窗口内**不允许插入 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat)**。爽点 必须在 Break into Three 之后(Finale 段)才兑现。如果创作者在 Dark Night of Soul 中插入 爽点(例如主角突然获得外援),这破坏了 Snyder 的"触底反弹"结构 —— 观众感受不到 Finale 的 爽点 峰值,因为情绪曲线没有被压到最低。

### Double-Bump 失败模式(常见错误)

1. **"假触底":** All Is Lost 之后立刻给一个"虚假希望"(例如盟友突然出现救场),然后 Dark Night of Soul 被跳过。这违反 double-bump 规则 —— 观众会觉得"主角没真正经历绝望",Finale 的 爽点 缺乏对比。
2. **"触底过深":** Dark Night of Soul 持续过长(例如 90s 短剧 中占 > 10s),观众在最低点流失 —— 完播率 在 77s 后崩。正确做法:Dark Night of Soul ≤ 5s(90s)/ ≤ 8s(180s)/ ≤ 3s(60s)。
3. **"触底无内省":** All Is Lost + Dark Night 只是外部事件连续恶化,主角没有内省 / 觉醒 —— Break into Three 缺乏动机支撑。正确做法:Dark Night of Soul 中必须有 1 句内省台词或 1 个内省镜头(特写主角眼神 / 颤抖的手)。

### Double-Bump 在不同 题材 中的表现

不同题材的 double-bump 有不同的"触底"形式:

| 题材 | All Is Lost 的典型形式 | Dark Night 的典型内省 | Break into Three 的典型解决方案 |
|------|------------------------|----------------------|-------------------------------|
| **[男频](../../_shared/glossary.md#男频-male-oriented-channel) 复仇** | 主角被反派击败 / 关键盟友背叛 | 主角质疑"复仇是否值得" | 主角发现反派的弱点 / 获得新的力量来源 |
| **[女频](../../_shared/glossary.md#女频-female-oriented-channel) 闪婚** | 男主发现真相后冷暴力 / 驱逐女主 | 女主质疑"是否应该放弃这段感情" | 女主决定用真实的自己面对 / 萌宝助攻 |
| **小程序剧 悬疑** | 主角被嫁祸 / 关键证据被销毁 | 主角质疑"真相是否值得追求" | 主角发现新的证据渠道 / 盟友牺牲留下线索 |
| **男频 战神** | 主角的部队被歼灭 / 战神身份被剥夺 | 主角质疑"战争的意义" | 主角找到新的盟友 / 觉醒更高层级的力量 |

**关键 heuristic 11:** All Is Lost 的"失去"必须是**主角之前获得的**(否则没有"失去"的痛感)。例如:男频 复仇中,主角在 Midpoint 获得的盟友 → All Is Lost 中盟友背叛;女频 闪婚中,女主在 Fun & Games 获得的男主信任 → All Is Lost 中信任崩塌。这与 Snyder 的"假胜利"Midpoint 形成因果链 —— 假胜利让主角获得,All Is Lost 让主角失去,Break into Three 让主角以更深的层次重新获得。

---

## Cross-References

- [`mckee-scene-design.md`](./mckee-scene-design.md) §Value-Shift Rule —— Snyder 的 Midpoint 极性反转与 McKee 的 value-shift 同构;两 ref 互补(Snyder 给结构骨架,McKee 给场景内部机制)
- [`mckee-scene-design.md`](./mckee-scene-design.md) §Turning Point vs Plot Point —— Snyder 的 Catalyst / All Is Lost / Break into Three 是 McKee 的 plot point 的具体实例
- [`cn-shortdrama-structure.md`](./cn-shortdrama-structure.md) §90s 短剧 Time Budget —— 短剧 专属的 3-act 时间预算(钩子 / setup / escalation / 爽点 / 卡点)与 Snyder 的 beat 模型映射
- [`cn-shortdrama-structure.md`](./cn-shortdrama-structure.md) §10-Episode Season Arc —— 跨集 season arc 的 opener / escalation / 卡点 / finale 集分类依赖本 ref 的 beat 重点表
- [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve —— 8-12s 无 击中点 则 attention drops ≥ 15%;30-40s 无 value-shift 则 drops ≥ 30%。为 Snyder 的 Catalyst / Midpoint 位置提供实证支撑
- [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Anchor-Based Sampling Protocol —— Snyder beat 转换点是 emotion_curve anchor 采样的主要 anchor 类型之一
- [`dialogue-craft.md`](./dialogue-craft.md) §Density Thresholds by Genre —— Catalyst 时刻的台词密度(男频 0.4-0.6 lines/s / 女频 0.5-0.7)
- [`dialogue-craft.md`](./dialogue-craft.md) §"As You Know" CN Anti-Pattern —— Save the Cat 时刻的台词潜台词(避免 expository crutch)
- [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §Taxonomy —— Snyder 的 Save the Cat 时刻与 HOOK 的 5-type taxonomy 在前 3 秒重叠;两 ref 共同定义开场钩子
- [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §5-Tier Strength Scoring —— Save the Cat 时刻的钩子强度评分
- [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §付费卡点 Density Rules —— Final Image 段的 卡点 cliffhanger 放置
- [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) §The 阶梯式 Escalation Ladder —— Fun & Games 段的 击中点 升级序列
- [`../_shared/glossary.md`](../../_shared/glossary.md) —— 术语定义([钩子](../../_shared/glossary.md#钩子-hook) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel))

---

## Refresh Cadence

- **季度复核(每 90 天):** 重新验证 Snyder 页数比例是否仍为行业标准;检查是否有新的 短剧 节奏学研究修正 beat budget 表
- **平台算法变更触发:** 抖音 / 快手 / 微信小程序剧 推荐算法权重调整时,重新验证 Catalyst 位置(当前 ~9s for 90s)是否仍为 完播率 甜区
- **新集长形态触发:** 若出现 > 180s 或 < 60s 的新形态(例如 240s 超长集或 45s 极短集),补充对应 beat budget 表
- **新平台涌现触发:** 若出现新的主要 短剧 分发平台(例如 视频号 短剧 / B站 竖屏短剧),补充对应 per-platform beat budget 变体
- **A/B 测试结果触发:** 若 完播率 数据显示 Catalyst 位置的甜区漂移(例如从 ~9s 漂移到 ~7s),需更新所有 beat budget 表的 Catalyst 行
- **Save the Cat 变体失效触发:** 若 男频 反向 Save the Cat 在 A/B 测试中 完播率 不再优于正向 Save the Cat,需重写 §Save-the-Cat Moment Defined 的变体表
- **Double-Bump 窗口变化触发:** 若 短剧 观众对 Dark Night of Soul 的容忍度变化,需更新 §Double-Bump Rule 的时间窗口表
- **负责模块:** screenplay SKILL.md body 的 References 表必须同步更新本 ref 的 Last-verified 日期

### 复核协议(heuristic)

每次复核应遵循以下 4 步协议:

1. **数据采集:** 从各平台创作者中心收集最近 90 天的 完播率 曲线数据(若公开)
2. **甜区验证:** 对比当前 beat budget 表的 beat 位置(Catalyst ~9s / Midpoint ~45s / All Is Lost ~67s for 90s)与实测 完播率 拐点
3. **偏差判定:** 若偏差 > ±2s(90s 形态)/ ±4s(180s 形态),触发 beat budget 表更新
4. **文档更新:** 更新本 ref 的 Last-verified 日期 + 修订记录;同步更新 screenplay SKILL.md 的 References 表

---

## 修订记录

| 日期 | 版本 | 修订内容 | 修订人 |
|------|------|----------|--------|
| 2026-06-15 | v1.0 | 初版 — Snyder 15-beat 适配 短剧 60s/90s/180s 形态 + Save the Cat 定义 + Double-Bump 规则 | Phase 3 plan 03-01 |

---

## 使用说明

本 ref 是 screenplay 专家的 5 个 curated refs 之一(Phase 3 [CONTEXT D-1](../../../../../.planning/phases/03-top-4-existing-experts-rag/03-CONTEXT.md) source mix 第 1 项:Save the Cat)。screenplay SKILL.md 的 `## References` 表列出本 ref 的触发条件与核心内容摘要;`## Knowledge Retrieval` 块给出 provider-agnostic 的检索协议。

本 ref 的所有数值(beat 位置 / runtime 比例 / Save the Cat 变体阈值 / Double-Bump 窗口)是**唯一真相源** —— screenplay SKILL.md body 不重复定义这些数字,只引用 + 跨链。若数值需修订,修订本 ref,SKILL.md body 的引用自动同步。

---

## Drift Signals

以下信号提示本 ref 可能已过时,需要重新验证:

1. **Catalyst 位置漂移:** 若行业数据显示 90s 短剧 的 Catalyst 甜区从 ~9s 漂移到 ~6s 或 ~12s,需更新 beat budget 表
2. **新 beat 涌现:** 若 短剧 行业出现 Snyder 15-beat 模型之外的新节拍(例如"二次钩子"在 30s 处),需评估是否纳入模型
3. **Save the Cat 变体失效:** 若 男频 反向 Save the Cat(展示极端弱势)在 A/B 测试中 完播率 不再优于正向 Save the Cat,需重写 §Save-the-Cat Moment Defined
4. **Double-Bump 窗口变化:** 若 短剧 观众对 Dark Night of Soul 的容忍度变化(例如 90s 短剧 的 Dark Night 可延至 8s 而非 5s),需更新 §Double-Bump Rule 的时间窗口表
5. **跨平台差异涌现:** 若 抖音 / 快手 / 微信小程序剧 的 beat budget 出现显著分化(例如快手的 Catalyst 更晚),需拆分为 per-platform beat budget 表
6. **B-Story 位置失效:** 若 短剧 行业最佳实践显示 B-Story 不应在 p.30 启动(而应更早或更晚),需更新 §The 15 Beats 的 B-Story 行
7. **Fun & Games 段缩短:** 若 短剧 观众对"承诺兑现段"的耐心缩短(例如 90s 短剧 的 Fun & Games 从 22s 缩短到 15s),需更新 beat budget 表
8. **Final Image 对照机制失效:** 若 短剧 观众不再期待 Final Image 与 Opening Image 的视觉对照(例如 multi-season 形态中对照机制变化),需修订 §Beat Budget 验证清单
9. **松紧节奏漂移:** 若 短剧 观众对松拍(Debate / Bad Guys Close In)的容忍度变化,需更新 §15 Beats 之间的"松紧"节奏 表的 runtime 占比
10. **主题闭环失效:** 若 Save the Cat 与 Theme Stated 的主题闭环在某些题材下不再适用(例如纯动作题材不强调主题),需修订 §Save the Cat 与 Theme Stated 的关系
