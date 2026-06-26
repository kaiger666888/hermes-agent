# Platform Master Slicing — 7-Variant Algorithm (Step 14)

**Source:** Notion page `32811082-af8e-8009-b097-d19a5027b46f` (anchor block `38211082-af8e-800e-b464-c65441cf8e6e`, "心流♥ → aigc开发 → 创作方向" §平台策略). Tier A ref `platform-specs.md` is the canonical 7-row matrix source; this ref encodes the slicing algorithm that consumes it.
**Copyright:** Fair Use — factual algorithm structure + brief operational definitions reproduced with attribution; no copyrighted creative content.
**Last-verified:** 2026-06-26

---

## Summary

本 ref 是 **Step 14 平台母版切片算法**的权威源。它把 1 个 `master.mp4` (Step 13 交付)切成 **7 个平台 variants**,每个 variant 自动调整 aspect ratio / hook position / 中段卡点密度 / 结尾 3s 钩子,所有数值参数都来自 `platform-specs.md` 7-row 硬性规格矩阵 + 12-row 刚性约束。

**Phase 38 (v9.0) 引入**:Step 14 是 additive 扩展,不重排 V8.6 13-step 编号(`step_count: 13` 在 frontmatter 中保持不变),在 Step 13 delivery 完成后触发。

**Phase 42 (DATA) 消费契约**:variants[] metadata 作为数据契约,Phase 42 DATA adapter 会按 platform 分桶接入实际平台 API metrics(完播率 / 卡点跳出率 / 互动率 / 收藏率 / 评论率)。

**本 ref 不发明数值。** aspect_ratio / length / hook position 全部源自 `platform-specs.md` 硬性规格对照表 + ROADMAP Phase 38 SC#1 枚举;本 ref 仅做算法编排(7 variants × 4 决策点 = 28 个确定性变换)。

---

## 7-Variant Emission Matrix (SLICE-01)

下表是 Step 14 必须产出的 7 个 variant 矩阵。每个 platform enum 与其 `aspect_ratio` / `length_sec` / hook 位置**全部源自** `platform-specs.md` 硬性规格对照表 + ROADMAP Phase 38 SC#1 枚举。

### 矩阵读法

矩阵的每一行都是一个**硬性产出要求**:Step 14 必须为每个 platform enum 产出 1 个 variant 文件 + 1 条 variants[] 记录。不允许跳过某个 platform,也不允许合并(例如不允许把 抖音竖屏 与 快手竖屏 视为同一 variant —— 即使它们的 aspect_ratio / length / hook 位置完全相同,它们仍然是 2 个独立 variant,因为下游 Phase 42 DATA 需要按 platform 独立接入 API + 独立计算 metrics)。

### 矩阵 vs. 硬性规格对照表的差异说明

`platform-specs.md` 的硬性规格对照表只区分 2 种形态(竖屏滑动 vs. 横屏主动),共 10 行维度。但实际平台有 7 个(抖音有竖屏 + 横屏两种投放模式;B 站横屏长 vs. 横屏短的时长不同;小红书 / 视频号 / 红果/快手极短各自有独立的时长上限)。本 7-Variant Emission Matrix 是把 硬性规格对照表 的 2 种形态 × 7 个具体平台的时长差异化处理结果。

- 4 个 9:16 verticals(抖音竖屏 / 快手竖屏 / 小红书竖屏 / 红果/快手极短)共享 硬性规格对照表 竖屏滑动列的所有维度数值,差异仅在 `length_sec` 上限。
- 3 个 16:9 horizontals(抖音横屏 / B 站横屏长 / 视频号横屏)共享 硬性规格对照表 横屏主动列,差异仅在 `length_sec` 上限(B 站横屏长 放宽至 5-10min)。

| 平台 enum | 中文名 + 形态 | aspect_ratio | length_sec | hook_position | Source row in `platform-specs.md` |
|-----------|---------------|--------------|------------|---------------|------------------------------------|
| `douyin_vertical_916` | 抖音竖屏 9:16 (竖屏滑动) | 9:16 | 15-60 | 第 1-3 秒 | 硬性规格对照表 竖屏滑动列 |
| `douyin_horizontal_169` | 抖音横屏 16:9 (横屏主动, 抖音横屏短剧) | 16:9 | 90-300 | 第 5-10 秒 | 硬性规格对照表 横屏主动列 |
| `kuaishou_vertical` | 快手竖屏 (竖屏滑动) | 9:16 | 15-60 | 第 1-3 秒 | 硬性规格对照表 竖屏滑动列 (快手与抖音同形态) |
| `bilibili_horizontal_long` | B 站横屏长 (横屏主动, 5-10min) | 16:9 | 300-600 | 第 5-10 秒 + 30 秒信任死亡线 | 硬性规格对照表 横屏主动列 (上限放宽至 5-10min per ROADMAP SC#1) |
| `xiaohongshu_vertical_short` | 小红书竖屏短 (竖屏滑动, 3min) | 9:16 | 60-180 | 第 1-3 秒 | 硬性规格对照表 竖屏滑动列 (小红书 3min 上限 per ROADMAP SC#1) |
| `shipinhao_horizontal` | 视频号横屏 (横屏主动) | 16:9 | 90-300 | 第 5-10 秒 | 硬性规格对照表 横屏主动列 |
| `hongguo_kuaishou_micro` | 红果/快手极短 (竖屏滑动, 1-2min) | 9:16 | 60-120 | 第 1-3 秒 | 硬性规格对照表 竖屏滑动列 (红果/快手极短 1-2min per ROADMAP SC#1) |

**读法约束(本 ref 的最高优先级规则):**
- aspect_ratio 与 length_sec **全部源自** `platform-specs.md` 硬性规格对照表 + ROADMAP Phase 38 SC#1 枚举。本 ref 不发明数值;仅做算法编排。
- 9:16 verticals(抖音竖屏 / 快手竖屏 / 小红书竖屏 / 红果极短)共享 硬性规格对照表 竖屏滑动列 —— 用户契约 "被动投喂,随时划走" 决定下行所有约束。
- 16:9 horizontals(抖音横屏 / B 站横屏 / 视频号横屏)共享 硬性规格对照表 横屏主动列 —— 用户契约 "主动点击,预付耐心" 决定下行所有约束。
- B 站横屏长的 `length_sec` 上限放宽至 600 秒(5-10min)per ROADMAP Phase 38 SC#1 枚举(超过 `platform-specs.md` 默认 90s-5min 上限);红果/快手极短下限放宽至 60s。

**7 平台覆盖完整性:** 7 个 platform enum 值是 SLICE-01 的硬性产出要求 —— Step 14 必须为每个 enum 产出 1 个 variant 文件 + 1 条 variants[] 记录,缺一不可。

---

## Slicing Algorithm — 4 Key Decision Points (SLICE-02)

Step 14 切片算法对**每个 variant** 走 4 个决策点(7 variants × 4 decisions = 28 个确定性变换)。每个决策点的 source rule 都指向 `platform-specs.md` 的具体行,不允许凭主观调整。

### D1. Aspect-Ratio Adaptation (画幅适配)

**Input:** `master.mp4` native aspect(由 Step 13 `master-mp4` slot 的 metadata 字段给出)+ `scene-images` slot(p07 output,用于 reframe 决策)。

**Source rule:** 7-Variant Emission Matrix `aspect_ratio` 列(上方)+ `platform-specs.md` 硬性规格对照表 + 刚性约束 行为层 "划走手势触发区" 行(屏幕下三分之一为 swipe gesture zone,关键视觉信息不可只落在下三分之一)。

**Algorithm:**
- 从 `master.mp4` 提取 native aspect(典型 16:9 master 或 9:16 master,取决于 Step 12 composition 输出)。
- 对 9:16 vertical variants:若 master 是 16:9,执行 center-crop;safe-area = top 2/3 + bottom 1/3 的关键信息分布(swipe gesture zone avoidance);若 master 已是 9:16,直接 pass-through。
- 对 16:9 horizontal variants:若 master 是 9:16,执行 letterbox(上下黑边)或 reframe(从 9:16 vertical 重剪关键帧);若 master 已是 16:9,直接 pass-through。
- 输出 aspect-ratio-adapted intermediate mp4(D1 不写 metadata,只准备 D2/D3/D4 的 source 画面)。

**Safe-area 详解(竖屏 center-crop):**
- `platform-specs.md` 刚性约束 行为层 "划走手势触发区" 明确:屏幕下三分之一为 swipe gesture zone,关键视觉信息(角色脸 / 钩子物件)不可只落在下三分之一。
- 因此 16:9 → 9:16 center-crop 不能简单取 center-horizontal-slice;必须先做 saliency scan(消费 `scene-images` slot 的 keyframe saliency map),确保 crop 后的关键信息分布为 top 2/3 + bottom 1/3(bottom 1/3 允许次要信息 / 字幕 / 装饰,但不允许 primary 冲突帧)。
- 若 saliency scan 发现 primary 信息集中在底部,D1 触发 `cinematographer` 咨询(reframe 决策),不允许直接 crop 掉关键信息。

**Aspect-ratio consistency check(T-38-03 mitigation):**
- 输出 `aspect_ratio` 字段必须与 platform enum 的 7-Variant Emission Matrix 矩阵行严格匹配。
- 例如 `douyin_vertical_916` variant 的 `aspect_ratio` 必须是 `"9:16"`(string);若算法误输出 `"16:9"`,Phase 42 DATA 消费时会拒绝该 variant(T-38-03 spoofing mitigation)。
- 此 consistency check 在 Step 14 算法内部完成,不依赖外部 gate。

**Output field:** `variants[].aspect_ratio`(string "W:H")。

### D2. Opening Hook Repositioning (开头钩子重定位)

**Input:** `master.mp4` timeline + Step 1 `hook-design` slot(p01 output,含 `timestamp_sec` 字段标识 master 中的原始 hook 位置)。

**Source rule:** `platform-specs.md` 硬性规格对照表 "钩子位置" 行 —— 竖屏 第 1-3 秒 / 横屏 第 5-10 秒;刚性约束 平台层 "冷启动秒级审判"(抖音/快手 前 3 秒不可出现纯文字 / 静止画面,需动态冲突);`creative-redlines.md` R3 零背景铺垫(竖屏前 3s / 横屏前 10s 必须 active conflict)。

**Algorithm:**
- 从 `hook-design` slot 读取 master 原始 hook 的 `timestamp_sec`(典型为 0-5s 区间内的冲突峰值)。
- 对 vertical variants:force-hook at 0-3s。若 master 开场已是 0-3s 冲突 → pass-through。若 master 开场为 exposition(旁白 / 静止画面 / setup) → re-cut 把 master 中后段的 conflict peak 前移到 0-3s(从 `scene-images` B-roll 候选里选 1 个冲突帧作为新开场)。
- 对 horizontal variants:允许 5-10s ramp,但确保 30s 信任死亡线之前已完成首次情绪转折(`platform-specs.md` "首次情绪转折" 行:横屏 第 30-60 秒)。
- 输出 re-cut timeline(D2 改变 variant 的开场时间轴)。

**Re-cut 决策树:**

| Master 开场 pattern | Vertical variant 处理 | Horizontal variant 处理 |
|---------------------|------------------------|--------------------------|
| 0-3s active conflict(pass) | pass-through | pass-through(允许 0-3s 冲突,但 ramp 至 5-10s 也可) |
| 0-3s exposition(narration / static) | re-cut:从 B-roll 选 conflict peak 前移到 0-3s | 允许保留 exposition ≤ 5s,但 5-10s 必须有冲突 |
| 3-5s exposition 后才冲突 | re-cut:把 3-5s 的 conflict 前移到 0-3s | pass-through(符合横屏 5-10s 钩子线) |
| 全片无明确冲突(R3 + R4 双违反) | 触发 `hook_retention` 咨询;若仍无解 → 标记 variant 为 needs-operator-review | 同 vertical |

**Cold-start 审判(平台层刚性约束):**
- `platform-specs.md` 刚性约束 平台层 "冷启动秒级审判(抖音/快手)" 行明确:前 3 秒不可出现纯文字 / 静止画面,需动态冲突。
- 因此 `douyin_vertical_916` / `kuaishou_vertical` / `hongguo_kuaishou_micro` 三个 vertical variants 的 D2 是 **强制 re-cut**(不允许 exposition 开场)。
- 其他平台(B 站 / 视频号 / 小红书)虽然不在 "冷启动秒级审判" 约束内,但仍受 R3 零背景铺垫 creative-redline 约束 —— D2 仍然必须 force conflict 开场,只是允许略宽的时间窗(竖屏 ≤ 3s / 横屏 ≤ 10s)。

**Output field:** `variants[].hook_timestamps.opening_hook_{start,end}_sec`(float,秒)。

### D3. Mid-Segment 卡点 Density Adjustment (中段卡点密度调整)

**Input:** `master.mp4` 的 emotion-tagged beat sheet(从 `spatio-temporal-script` slot,p06 output,含 per-beat `script_emotion_tags`)。

**Source rule:** `platform-specs.md` 硬性规格对照表 "情绪单元间隔" 行 —— 竖屏 ≤ 8 秒 / 横屏 ≤ 60-90 秒;刚性约束 行为层 "重复观看触发条件"(每 15 秒竖屏 / 每 60 秒横屏至少 1 个差异点刺激重看);`creative-redlines.md` R1 情绪脱敏(连续同类型 ≤ 2 次)。

**Algorithm:**
- 从 `spatio-temporal-script` 计算每个相邻情绪单元的间隔(duration_ms)。
- 对 vertical variants:扫描间隔 > 8000ms 的 gap,从 `scene-images` B-roll 候选里选 1 个反差情绪帧插入卡点(re-cut 或 speed-ramp);同时确保每 15s 至少 1 个差异点。
- 对 horizontal variants:扫描间隔 > 90000ms 的 gap,同样处理;每 60s 至少 1 个差异点。
- 检查 R1 情绪脱敏:若任意 60s 窗口内出现连续 ≥ 3 个同 taxonomy 情绪标签,在中间插入 1 个反差标签镜头(从 B-roll 选)。
- 输出每插入点的 `cut_points[]` 条目,`reason: emotion_unit_gap_fill`。

**卡点密度计算示例(vertical variant, length_sec=60):**
- master 的 emotion-tagged beat sheet 假设为:`[angry@0-8s, angry@8-16s, neutral@16-30s, sad@30-45s, sad@45-60s]`
- 情绪单元间隔扫描:`angry→angry=0s`(同类型连续,触发 R1 风险)、`angry→neutral=14s`(> 8s gap,触发 D3 卡点)、`neutral→sad=15s`(> 8s gap,触发 D3 卡点)、`sad→sad=0s`(同类型连续,触发 R1 风险)。
- D3 处理:
  - 在 angry@8-16s 与 neutral@16-30s 之间(约 12s 处)插入 1 个反差情绪帧(例如 "shocked"),既填补 gap 又打散 R1 风险。cut_points 加 `{timestamp_sec: 12, reason: emotion_unit_gap_fill}`。
  - 在 neutral@16-30s 与 sad@30-45s 之间(约 23s 处)插入 1 个反差情绪帧(例如 "hopeful")。cut_points 加 `{timestamp_sec: 23, reason: emotion_unit_gap_fill}`。
  - 同时把 `first_emotional_turn` cut point 标记在 8s(首次情绪转折,符合 `platform-specs.md` 竖屏 第 8-15 秒)。`memory_closure` cut point 标记在 30s(`platform-specs.md` "记忆闭环" 行:竖屏 30 秒内微型闭环)。
- 处理后 variant 的 cut_points 应包含至少:`opening_hook_boundary` (D2) + `first_emotional_turn` (D3) + `memory_closure` (D3) + N 个 `emotion_unit_gap_fill` (D3) + `closing_hook_boundary` (D4)。

**B-roll 候选选择规则:**
- 从 `scene-images` slot 的 5-view per-scene keyframes 中,选 emotion-tag 与目标卡点反差最大的帧。
- 反差度量:emotion taxonomy 距离(例如 angry ↔ hopeful 距离大,angry ↔ furious 距离小)。
- 不允许重复使用同一 B-roll 帧(每帧只能在 1 个 variant 中作为 D3 卡点或 D4 closing hook 使用 1 次,避免视觉重复)。

**Output field:** `variants[].cut_points[]` 中所有 `reason: emotion_unit_gap_fill` / `reason: first_emotional_turn` 条目。

### D4. Closing Hook Injection (结尾新钩子注入)

**Input:** `master.mp4` ending timeline + `scene-images` B-roll slot。

**Source rule:** `creative-redlines.md` R4 结尾未完成(最后 3 秒竖屏 / 最后 10 秒横屏必须释放新钩子,禁止大团圆)+ `platform-specs.md` 刚性约束 行为层 "收藏/转发 决策窗口"(结尾前 3 秒竖屏 / 10 秒横屏)。

**Algorithm:**
- 检测 master 的 ending pattern:若末 beat 标记为 resolution / closure / epilogue(R4 违反风险),必须在最后窗口注入 new open question。
- 对 vertical variants:在 `length_sec - 3` 到 `length_sec` 区间注入 1 个 closing hook(从 `scene-images` B-roll 选 1 个未使用的新信息帧 —— 例:角色手机响起 / 新角色登场 / 道具特写)。
- 对 horizontal variants:在 `length_sec - 10` 到 `length_sec` 区间注入 1 个 closing hook。
- 输出 closing hook timestamps + 边界 cut_points 条目。

**Closing hook 候选类型(从 `genre-anchor-urban-fantasy.md` 都市奇幻题材库衍生):**
- **新角色登场型:** 最后窗口引入一个未出现过的角色(例:镜头扫过角色肩膀,背景出现一个神秘人剪影)。
- **道具揭示型:** 最后窗口特写一个之前未出现的道具(例:桌上突然出现一封未拆的信 / 一个未激活的法器)。
- **反转信息型:** 最后窗口引入一条与已建立剧情冲突的信息(例:主角手机响起,屏幕显示 "前妻" / ".unknown caller" / 一个不该存在的联系人)。
- **环境异常型:** 最后窗口出现一个视觉 / 听觉异常(例:窗外突然下起反向的雨 / 镜中的主角比主角慢半拍)。

候选帧必须**未在前面 variant 中使用过**(B-roll 不可重复,见 D3 规则),且必须构成 open question(不可在 3s/10s 窗口内闭合)。

**R4 compliance check:**
- D4 完成后,Step 14 内部自检 R4:末窗口是否引入 new open question。
- 若 D4 未找到合适 closing hook 候选(B-roll 耗尽 / 所有候选都已在前面用过),Step 14 标记该 variant 为 `needs-operator-review` 并不写入 variants[](variant 缺失会被 Phase 42 DATA 检测到 —— SLICE-01 要求 7 variant 全部存在)。
- 此 self-check 在 Phase 40 GATE-03 `redline_unfinished_ending` gate 之外,是 Step 14 算法内置的预检测。

**Output field:** `variants[].hook_timestamps.closing_hook_{start,end}_sec` + `variants[].cut_points[]` 中所有 `reason: closing_hook_boundary` 条目。

---

## variants[] Schema (SLICE-03)

`variants[]` 是 `pipeline_state.episode_id` 上的 **ADDITIVE 字段**(Phase 38 引入)。它不替换现有 13-step 任何 slot;在 `master-mp4` slot 写入后由 Step 14 追加。Schema enforcement 由 Phase 42 DATA 在消费侧做 Pydantic 校验;Phase 38 只产出 schema 文档,不写 Python 校验代码。

**完整 schema shape:**

```json
{
  "episode_id": "ep-001",
  "variants": [
    {
      "platform": "douyin_vertical_916",
      "aspect_ratio": "9:16",
      "length": 60,
      "hook_timestamps": {
        "opening_hook_start_sec": 0,
        "opening_hook_end_sec": 3,
        "closing_hook_start_sec": 57,
        "closing_hook_end_sec": 60
      },
      "cut_points": [
        { "timestamp_sec": 3, "reason": "opening_hook_boundary" },
        { "timestamp_sec": 8, "reason": "first_emotional_turn" },
        { "timestamp_sec": 30, "reason": "memory_closure" },
        { "timestamp_sec": 57, "reason": "closing_hook_boundary" }
      ],
      "source_master_hash": "sha256:<master-mp4 slot content_hash>"
    }
    // ... 6 more variant objects, one per platform row in 7-Variant Emission Matrix
  ]
}
```

**5 个必填字段(每个 variant object):**

| Field | Type | Source decision | Consumer |
|-------|------|-----------------|----------|
| `platform` | enum (7 values: `douyin_vertical_916` / `douyin_horizontal_169` / `kuaishou_vertical` / `bilibili_horizontal_long` / `xiaohongshu_vertical_short` / `shipinhao_horizontal` / `hongguo_kuaishou_micro`) | D1 (matrix row) | Phase 42 DATA bucketing |
| `aspect_ratio` | string "W:H"(e.g. `"9:16"` / `"16:9"`) | D1 | Phase 42 rendering validation |
| `length` | int (seconds,必须落在 7-Variant Emission Matrix `length_sec` 范围内) | D1 (matrix) | Phase 42 completion-rate denominator |
| `hook_timestamps` | `{opening_hook_start_sec, opening_hook_end_sec, closing_hook_start_sec, closing_hook_end_sec}` (all float seconds) | D2 (opening) + D4 (closing) | Phase 42 hook_dropoff_rate window |
| `cut_points` | `[{timestamp_sec: float, reason: enum}]` (reason ∈ `{opening_hook_boundary, first_emotional_turn, memory_closure, emotion_unit_gap_fill, closing_hook_boundary}`) | D2 + D3 + D4 | Phase 42 per-cut retention analysis |

**Optional 字段:**
- `source_master_hash` (string, `"sha256:<hash>"`) — 用于 T-38-01 mitigation:Phase 42 可拒绝 source hash 与 master-mp4 slot content_hash 不匹配的 variants。

**Schema 约束:**
- 7 个 variant object 必须**全部存在**(SLICE-01 硬性要求);不允许部分产出。
- 同一 `source_master_hash` 必须出现 7 次(每个 variant 共享一个 master.mp4 源)。
- `aspect_ratio` 必须与 platform enum 的 7-Variant Emission Matrix 矩阵行匹配(T-38-03 mitigation:防 platform enum spoofing)。例如 `douyin_vertical_916` 的 `aspect_ratio` 必须为 `"9:16"`,不允许 `"16:9"`。

**写入语义:** write-once per episode(Step 14 切片完成后一次性写入)。Atomic write per AssetBus V3 envelope 约定(见 `asset-bus-schema.md` §Envelope Schema)。Phase 42 DATA 消费时只读不写。

**`cut_points[].reason` enum 完整定义:**

| Reason | 触发决策 | 含义 |
|--------|----------|------|
| `opening_hook_boundary` | D2 | 开场钩子的结束边界(vertical 3s / horizontal 10s 之后);标记"钩子区"与"正片"的分界 |
| `first_emotional_turn` | D3 | 首次情绪转折点(`platform-specs.md` 硬性规格:竖屏 8-15s / 横屏 30-60s);用于 Phase 42 hook_dropoff_rate 分析 |
| `memory_closure` | D3 | 记忆闭环点(`platform-specs.md` "记忆闭环" 行:竖屏 30s 内微型闭环 / 横屏 60-90s 单元闭环);用于 Phase 42 重复观看触发分析 |
| `emotion_unit_gap_fill` | D3 | D3 算法主动插入的卡点(填补 > 8s/90s 情绪单元 gap 或打散 R1 情绪脱敏);用于 Phase 42 卡点跳出率分析 |
| `closing_hook_boundary` | D4 | 结尾钩子的起始边界(vertical 末 3s / horizontal 末 10s 之前);标记"正片"与"结尾钩子区"的分界 |

**Schema enforcement 边界:**
- Phase 38(本 phase)只产出 schema 文档 + 算法 spec;**不写 Python 校验代码**。
- Phase 42 DATA 在消费侧做 Pydantic 校验 —— 任何 field 缺失 / 类型不匹配 / aspect_ratio 与 platform enum 不一致 都会被 Phase 42 拒绝。
- 这种 "spec 在 Phase 38,enforcement 在 Phase 42" 的拆分遵循 CLAUDE.md `## Out of Scope` 规则:v9.0 Phase 38 是 docs-only,Python adapter 代码归 Phase 42。

---

## Slicing Pipeline I/O Contract

Step 14 切片算法的输入 / 输出契约。

**Inputs (READ from existing slots — Step 14 does NOT write to these):**
- `master-mp4` (p13 output, V8.6 Step 12-13) — 源 master render,Step 14 切片的唯一视频源。
- `hook-design` (p01 output) — master 原始 hook 的 `timestamp_sec`,供 D2 重定位使用。
- `spatio-temporal-script` (p06 output) — emotion-tagged beat sheet,供 D3 卡点密度分析使用。
- `scene-images` (p07 output) — B-roll 候选帧池,供 D2 / D4 re-cut injection 使用(D2 开场冲突帧 / D4 结尾新钩子帧)。

**Step 14 algorithm (4 decisions × 7 variants):**
```
master-mp4 ─┐
hook-design ┼─▶ D1 aspect-ratio adaptation ─▶ D2 opening hook repositioning
spatio-     ┤                                     │
temporal-   ┤                                     ▼
script      ┼─▶ D3 mid-segment 卡点 density ─▶ D4 closing hook injection
scene-images┘                                            │
                                                          ▼
                                              variants[] (7 records)
                                              + 7 per-platform mp4 paths
```

**Outputs (WRITE — additive):**
- `pipeline_state.episode_id.variants[]` — 7-element array,5 必填字段 per variant(schema 见上方 §variants[] Schema)。
- `delivery-package` slot extension — 7 per-platform mp4 paths(additive to 现有 p13 delivery-package manifest;每条 path 形如 `runs/<episode>/variant_<platform>.mp4`)。

**Step 14 不写:**
- 不修改 `master-mp4` slot(只读)。
- 不修改 `hook-design` / `spatio-temporal-script` / `scene-images` slot(只读)。
- 不新增 gate(现有 V8.6 8-gate review 结构不变;per-variant compliance sign-off 通过现有 Gate 8 final-delivery + per-variant AIGC 标识)。
- 不修改 V8.6 13-step 任何 phase 的 slot write contract。

**Operator-action-handoff:** 无。Step 14 是 deterministic algorithm extension,所有数值参数都来自 `platform-specs.md` 刚性约束;operator 不需要在 Step 14 期间做手工决策。Operator 仅在 Step 13 delivery (Gate 8) 时确认 master.mp4 通过合规审核,Step 14 自动启动。

**触发条件与前置依赖:**
- Step 14 仅在 Gate 8 `final-delivery` approve 后触发(Gate 8 reviewer:Operator + compliance_gate;mode:Sync)。
- 若 Gate 8 reject,master.mp4 回到 p13 重做,Step 14 不启动。
- 若 Step 13 delivery-package slot 已包含 operator 手工切片的 variants(legacy / pre-v9.0 工作流),Step 14 不覆盖;只在 variants[] 字段为空时执行。这是 v9.0 兼容性约束 —— 现有 V8.6 13-step 工作流不被 Step 14 打断。

**失败回退策略:**
- 若 D1-D4 任一决策点无法完成(例如 B-roll 候选耗尽 / re-cut 后的 variant 不符合 R4),Step 14 标记该 variant 为 `needs-operator-review` 并不写入 variants[]。
- 此时 variants[] 可能少于 7 条 —— Phase 42 DATA 消费时会检测到(SLICE-01 硬性要求 7 variant 全部存在),触发 operator 介入。
- Step 14 本身不抛异常 / 不阻断 pipeline;它尽力产出最多 variant,缺失的留给 operator 补。
- 这与 Phase 41 Step 6.5 的 fallback 不同 —— Step 6.5 失败会 BLOCKING(通过 review_gates);Step 14 失败是 degrade-tolerant(per GPU-DIRECT-05 pattern)。

---

## Per-Expert Consultation Guide

Step 14 主要由 `editor` 执行,辅以 3 个咨询专家。

- **`editor`** — 执行 D2 / D3 / D4 的实际 cut 决策。本 ref 是 editor 在 Step 14 期间的主要输入;editor 调用 delegate_task 时优先加载本 ref + `platform-specs.md`。
- **`hook_retention`** — 拥有 `hook-design` slot,D2 消费它。当 D2 必须 re-cut 一个非冲突开场时(原 master 开场为 exposition),hook_retention 被咨询以选择最佳 conflict peak 前移。
- **`cinematographer`** — 拥有 composition。当 D1 aspect-ratio adaptation 需要 reframe 决策(center-crop safe-area)时,cinematographer 被咨询以确保关键视觉信息(角色脸 / 钩子物件)不被 crop 掉。
- **`compliance_gate`** — 每个 variant 的 final sign-off。per `platform-specs.md` 刚性约束 平台层 "AIGC 标识显式要求(全平台)",每个 variant 文件必须带 AIGC 三件套标识(标识不可遮挡下方视觉信息)。

---

## Numeric Parameter Traceability

本 ref 的所有数值参数都必须可追溯到 `platform-specs.md` 或 ROADMAP Phase 38 SC#1 枚举。这是为了满足 "本 ref 不发明数值" 的核心约束。

| 本 ref 中的数值 | Source | Source 行 |
|------------------|--------|-----------|
| 竖屏 hook 0-3s | `platform-specs.md` | 硬性规格对照表 "钩子位置" 行 竖屏滑动列 |
| 横屏 hook 5-10s | `platform-specs.md` | 硬性规格对照表 "钩子位置" 行 横屏主动列 |
| 竖屏 length_sec 15-60s | `platform-specs.md` | 硬性规格对照表 "最优时长" 行 竖屏滑动列 |
| 横屏 length_sec 90-300s | `platform-specs.md` | 硬性规格对照表 "最优时长" 行 横屏主动列 |
| B 站横屏长 length_sec 300-600s | ROADMAP Phase 38 SC#1 | 上限放宽至 5-10min |
| 小红书竖屏短 length_sec 60-180s | ROADMAP Phase 38 SC#1 | 3min 上限 |
| 红果/快手极短 length_sec 60-120s | ROADMAP Phase 38 SC#1 | 1-2min |
| 竖屏 情绪单元间隔 ≤ 8s | `platform-specs.md` | 硬性规格对照表 "情绪单元间隔" 行 竖屏滑动列 |
| 横屏 情绪单元间隔 ≤ 60-90s | `platform-specs.md` | 硬性规格对照表 "情绪单元间隔" 行 横屏主动列 |
| 竖屏 首次情绪转折 8-15s | `platform-specs.md` | 硬性规格对照表 "首次情绪转折" 行 竖屏滑动列 |
| 横屏 首次情绪转折 30-60s | `platform-specs.md` | 硬性规格对照表 "首次情绪转折" 行 横屏主动列 |
| 竖屏 记忆闭环 30s 内 | `platform-specs.md` | 硬性规格对照表 "记忆闭环" 行 竖屏滑动列 |
| 横屏 记忆闭环 60-90s 单元 | `platform-specs.md` | 硬性规格对照表 "记忆闭环" 行 横屏主动列 |
| 竖屏 closing window 末 3s | `platform-specs.md` + `creative-redlines.md` | 刚性约束 行为层 "收藏/转发 决策窗口" + R4 |
| 横屏 closing window 末 10s | `platform-specs.md` + `creative-redlines.md` | 刚性约束 行为层 "收藏/转发 决策窗口" + R4 |
| 竖屏 差异点 每 15s ≥ 1 | `platform-specs.md` | 刚性约束 行为层 "重复观看触发条件" |
| 横屏 差异点 每 60s ≥ 1 | `platform-specs.md` | 刚性约束 行为层 "重复观看触发条件" |
| 情绪脱敏 连续 ≤ 2 次 | `creative-redlines.md` | R1 情绪脱敏 |
| R3 零背景铺垫 竖屏 ≤ 3s / 横屏 ≤ 10s | `creative-redlines.md` | R3 零背景铺垫 |
| 横屏 30s 信任死亡线 | `platform-specs.md` | 硬性规格对照表 "注意力窗口" 行 横屏主动列 |

**Operator 审查 checkpoint:** 在 Phase 38 merge 前,operator 应打开本表 + `platform-specs.md`,逐行核对本 ref 的数值是否与 source 一致。任何对不上的数值都应在 merge 前修正 —— 不允许 "大约一致" 的近似值。

---

## Threat Model Notes (T-38-01..T-38-04)

本 ref 编码的算法内置以下 mitigation(对应 Phase 38 threat register):

- **T-38-01 (Tampering — variants[] metadata integrity):** `source_master_hash` 字段(sha256 of master-mp4 slot content_hash)tie 每个 variant 到其 source master —— Phase 42 可拒绝 source hash 不匹配的 variants。
- **T-38-03 (Spoofing — Platform enum spoofing):** D1 算法从 7-Variant Emission Matrix 强制 aspect-ratio;`aspect_ratio` 字段必须与 platform enum 的矩阵行匹配(consistency check)。例如 `douyin_vertical_916` 不允许 `"16:9"` aspect_ratio。

---

## See Also

- [`platform-specs.md`](./platform-specs.md) — v1 平台硬性规格权威源(7-row 矩阵 + 12-row 刚性约束)。本 ref 的所有数值参数都源自此处。
- [`pipeline-dag.md`](./pipeline-dag.md) — V8.6 13-step DAG + Step 14 additive annotation(Step 13 → Step 14 → Phase 42 DATA 消费)。
- [`asset-bus-schema.md`](./asset-bus-schema.md) — variants[] slot schema 文档(§Phase 38 Slots);AssetBus V3 envelope + atomic write 约定。
- [`creative-redlines.md`](./creative-redlines.md) — R3 零背景铺垫(D2 强制)+ R4 结尾未完成(D4 强制)+ R1 情绪脱敏(D3 中段检测)。Step 14 算法的合规边界。
- [`genre-anchor-urban-fantasy.md`](./genre-anchor-urban-fantasy.md) — v1 题材锚定(都市奇幻·轻喜剧),8 平台内容形态对齐(7 variant 内容取舍参考)。
- [`ltx2-preview-loop.md`](./ltx2-preview-loop.md) — Phase 41 Step 6.5 LTX2.3 fast-preview。Step 6.5 在 Step 14 之前验证 composition / framing / pacing;Step 14 切片基于 Step 6.5 已通过的 storyboard。
