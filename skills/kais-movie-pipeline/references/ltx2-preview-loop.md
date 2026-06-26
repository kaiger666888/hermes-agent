# LTX2.3 Preview Loop — Step 6.5 Fast-Preview Baseline & Fallback Policy

**Source:** LTX Video 2.3 docs (Lightricks, 2026-06); CausVid docs (2026-06); Kling 1.6 fast docs (Kuaishou, 2026-06); existing `skills/movie-experts/visual_executor/references/animator/video-gen-model-matrix.md` (Phase 5 v1.5 — the in-repo canonical 6-model catalog); `plugins/review_gates/gate.py` (Phase 34 — BLOCKING-mode Gate state machine); `skills/movie-experts/cinematographer/references/e-konte-format.md` (Phase 20 — 5-layer storyboard format consumed by preview).
**Copyright:** Fair Use — paraphrased capability specs + threshold rationale; no proprietary model internals verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-27

---

## Summary

本 ref 是 **V8.6 管线 Step 6.5 fast-preview 的权威源**。它文档化:

1. **为什么 LTX2.3 是 Step 6.5 preview 默认模型** —— 5s 预算内成本最低($0.10/clip)+ 开源权重 + 768p vertical 原生支持
2. **3 维校验阈值(composition / framing / pacing)** —— 每维都带硬阈值(0.80 / 10% / 15%),不是启发式建议
3. **确定性失败回退策略** —— pacing 偏差 > 15% OR framing 偏差 > 10% 自动回退 Step 6 重新分镜;max 2 retries;耗尽 retries 走 **现有 `plugins/review_gates/` BLOCKING mode**(非新 gate,非 silent skip)
4. **Prompt 模板** —— 把 E-Konte 5-layer storyboard 翻译成 LTX2.3 生成调用的 YAML 模板

**v9.0 边界声明(load-bearing — SC#4 operator-action-handoff):** v9.0 只交付 baseline 文档 + Step 6.5 wiring(本 ref + `SKILL.md` Step 6.5 section + `pipeline-dag.md` 注解)。**真实 LTX2.3 GPU 生成验证(V9-FUTURE-02)显式 deferred 到 operator 侧**。本 ref 不要求 v9.0 提供运行时 GPU validation evidence —— 阈值数字基于 LTX2.3 公开 specs + 现有 visual_executor consistency stack 的设计目标,实际 production-grade calibration 待 V9-FUTURE-02 operator 跑通。

---

## 模型选型 (Model Selection)

Step 6.5 的 preview 模型必须满足 3 条硬约束:

- **生成预算 ≤ 5 秒** —— 足够检测 composition / framing / pacing(1-2 cuts detectable @ 24fps = 120 frames),足够短让 operator 等待 < 30s wall-clock(3-5 key shots 并行)
- **9:16 原生支持** —— 短剧默认 vertical;横向裁剪引入 framing 失真,preview 失效
- **成本 ≤ $0.20/clip** —— preview 是 disposable 的(每次 retry 都丢),不是 production asset;成本超过 $0.20/clip 与 Step 7 的 production render 成本差不到 5x,失去 preview 的成本优势

### 3 个候选模型对比

| 模型 | Provider | 最大时长 | 分辨率 | 9:16 vertical | 成本 per 5s | 推荐场景 |
|------|----------|----------|--------|---------------|-------------|----------|
| **LTX2.3** | Lightricks (open weight) | **5s** | 768p | ✅ 原生 | **$0.10** | **Step 6.5 默认** — 5s 预算 + 成本最低 + 开源 |
| CausVid | (causal video model) | 8s | 720p | ✅ | $0.18 | 替代选项 — 需要 causal generation speed(sub-frame motion coherence 优先) |
| Kling 1.6 fast | Kuaishou | 10s | 1080p | ✅ | $0.25 | 替代选项 — CN-native prompt fidelity 优先(中文 prompt 直接消费不翻译) |

### 默认 LTX2.3 的理由(load-bearing)

LTX2.3 是 Step 6.5 默认 preview 模型,理由是 3 维硬约束的**全满足 + 最低成本**:

1. **5s 上限精确匹配预算** —— CausVid / Kling 1.6 fast 允许更长但 Step 6.5 不需要;统一 cap 在 5s 强制 budget discipline(避免 "再生成 2s 就完美" 的 cost creep)
2. **$0.10/clip 是 3 模型里最低** —— preview 平均每 episode 跑 3-5 key shots × 2-3 retries = 6-15 次生成;LTX2.3 = $0.60-$1.50/episode preview 成本,CausVid = $1.08-$2.70,Kling 1.6 fast = $1.50-$3.75。preview 的 disposable 性质让 $0.10 vs $0.25 的差距 6x 放大
3. **开源权重** —— 与 hermes-agent "open-first" 原则一致;CausVid / Kling 1.6 fast 是闭源 API,operator 可锁但非默认

**替代触发条件:**
- **CausVid 替代** —— 当 storyboard 的 Layer 2 `motion_intensity == "extreme"` 且 storyboard 自检 flag 了 sub-frame motion coherence 风险时;causal generation 在 fast motion 下 artifacts 更少
- **Kling 1.6 fast 替代** —— 当 storyboard 的 E-Konte Layer 1+2 描述含不可翻译的中文文化符号(例:"古风园林 + 红楼梦式 blocking")时;CN-native model 直接消费中文 prompt 减少翻译 lossy

**完整 6-model matrix 见** [`skills/movie-experts/visual_executor/references/animator/video-gen-model-matrix.md`](../../movie-experts/visual_executor/references/animator/video-gen-model-matrix.md) —— 本 ref **不重复** 6-model 全表;Step 6.5 只关心 3 个 fast-preview 候选。Step 10/11 production render 走的是 veo3.1 / kling-v3-4k / dreamina CLI(production-grade,不在本 ref scope)。

---

## ~5s 生成预算 (Generation Budget)

### 为什么是 5s?

Step 6.5 preview 的 5s 窗口是**精度 vs 成本的 trade-off sweet spot**,基于 3 个量化考量:

1. **Composition + Framing 可检性** —— 单 shot 5s @ 24fps = 120 frames;CLIP-T scene composition + Object IoU prop position 校验在 30+ frames sample 上统计稳定。少于 3s (72 frames) 时 sample size 不足,假阴性率上升
2. **Pacing 可检性** —— 5s 内可容纳 1-2 cuts(短剧标准 1.5-3s/shot,详见 [`vertical-screen-framing.md`](../../movie-experts/cinematographer/references/vertical-screen-framing.md) §短剧 Cut Density);cut 数量 + interval 与 storyboard `next_shot_link` chain 对比可量化 pacing deviation。少于 3s 时最多 1 cut,pacing 校验退化成 binary
3. **Wall-clock 成本** —— LTX2.3 5s clip 生成 wall-clock 约 8-15s(GPU 推理 + post-process);3-5 key shots 并行 = 15-30s operator 等待。超过 5s 预算 → wall-clock > 30s,operator UX 退化;少于 3s → 校验信号不可靠

### 5s 不覆盖什么

5s preview **故意不覆盖** 以下维度 —— 这些是 Step 7+ production render 的责任:

- **音频 sync** —— 5s preview 无 audio track;voicer / composer / foley 在 Step 10-12 才进管线。Preview 不检查 lip sync / BGM 节奏
- **跨 shot continuity** —— 5s 内最多 1-2 cuts;cross-shot character consistency (face / wardrobe / color) 在 Step 7 scene_images 阶段由 continuity_auditor 4-dim 审计
- **Final color grade** —— LTX2.3 768p 输出未应用 colorist LUT(CxSxZ grade 在 Step 13 才进);preview 的色调与最终 master.mp4 不可比

---

## 3 维校验阈值 (3-Dimension Check Thresholds)

> **本节是 PREVIEW-01 的核心交付物。** 3 个硬阈值数字(0.80 / 10% / 15%)是 load-bearing —— SC#3 引用 "pacing > 15% OR framing > 10%" 作为自动 fallback trigger。

Step 6.5 preview 的 3 维校验基于 E-Konte 5-layer storyboard 的对应层:

| 维度 | 消费 E-Konte 层 | 硬阈值 | 失败触发 |
|------|----------------|--------|----------|
| **composition** | Layer 1 (stage_geometry) + Layer 2 (shot_scale / axis_line) | `composition_match_score ≥ 0.80` | < 0.80 → fallback |
| **framing** | Layer 2 (vertical-screen framing rules) | `framing_deviation ≤ 10%` | > 10% → fallback |
| **pacing** | Layer 5 (duration_sec / cut_transition_type / next_shot_link) | `pacing_deviation ≤ 15%` | > 15% → fallback |

### composition (构图)

校验 E-Konte **Layer 1**(stage_geometry / character_blocking / environment_props)+ **Layer 2**(shot_scale / axis_line)在 LTX2.3 生成的 preview 帧中得到尊重。

**阈值:** `composition_match_score ≥ 0.80`(vs storyboard intent)

**测量方法:**
- 对 preview 5s 内 sample 30 frames(每 4 frames 一帧)
- 用 CLIP-T 计算 sample frame 与 storyboard Layer 1 declared stage_geometry 的 composition similarity
- 用 Object IoU 校验 Layer 1 `environment_props` 的 position 是否落在 declared ±0.1 normalized coords 内
- 用 shot_scale classifier(Mascelli 8-level)校验 Layer 2 `shot_scale` 是否匹配
- `composition_match_score = mean(CLIP_T_score × 0.5 + Object_IoU_score × 0.3 + shot_scale_match × 0.2)`

**失败示例:**
- 道具缺失:storyboard Layer 1 declares `desk_main` at `{x: 0.4, y: 0.6}`,preview 帧里 desk 不存在 → Object IoU = 0 → composition_match_score ≤ 0.5 → fail
- shot_scale 错:storyboard Layer 2 declares `MCU`,preview 实际是 `WS`(远景)→ shot_scale_match = 0 → composition_match_score ≤ 0.6 → fail
- axis_line 违反:storyboard Layer 2 declares `+X (L2R)` axis,preview 出现 R2L motion → axis check fail → composition_match_score 直接归零(轴线性不可妥协,per [`axis-rules.md`](../../movie-experts/cinematographer/references/axis-rules.md))

### framing (取景)

校验 E-Konte **Layer 2** 的 vertical-screen framing rules —— 9:16 power points / headroom / subtitle safe area(详见 [`vertical-screen-framing.md`](../../movie-experts/cinematographer/references/vertical-screen-framing.md))。

**阈值:** `framing_deviation ≤ 10%`(per SC#3 hard number)

**测量方法:**
- 对 preview 5s 内 sample 30 frames
- 检测主体(character / prop)的 bounding box
- 校验 bounding box 中心 vs 9:16 power points(1/3 + 2/3 intersections)的距离偏差;> 10% normalized distance 即 frame_offset_violation
- 校验 headroom ratio(头顶到 frame 上沿 / 总高度)应在 0.05-0.15 范围;超出即 headroom_violation
- 校验 subtitle safe area(bottom 20% of 9:16 frame)是否被主体 bounding box 完全覆盖 → subtitle_obscured_violation
- `framing_deviation = max(frame_offset_pct, headroom_excess_pct, subtitle_obscured_pct)`

**失败示例:**
- headroom 过大:storyboard Layer 2 intent = MCU 占 frame 30-40%,preview 主体实际占 15%(头顶上方 25% 空白)→ headroom ratio 0.25 > 0.15 → framing_deviation ≥ 25% → fail
- 主体偏离 power point:storyboard intent = 主体在 frame 1/3 交叉点,preview 实际偏移到 frame 边缘 → frame_offset > 10% → fail
- subtitle safe area 被遮:preview 主体 bounding box 覆盖 bottom 25% → subtitle 字幕无法放置 → fail

### pacing (节奏)

校验 E-Konte **Layer 5**(duration_sec / frame_count / cut_transition_type / next_shot_link)在 preview 里得到尊重。

**阈值:** `pacing_deviation ≤ 15%`(per SC#3 hard number)

**测量方法:**
- 对 preview 5s 内 detect cut points(shot-boundary detection,PySceneVideo 或同等)
- 校验 detected cut count vs storyboard Layer 5 `next_shot_link` chain declared cut count
- 校验 detected cut intervals vs storyboard declared `duration_sec` per shot
- 校验 cut_transition_type(hard_cut / dissolve / wipe / fade)在 detected transition 帧上是否匹配(用 transition classifier)
- `pacing_deviation = max(cut_count_delta_pct, interval_delta_pct, transition_mismatch_pct)`

**失败示例:**
- cut 过少:storyboard Layer 5 declares 2 cuts in 5s(2.5s/shot avg),preview 实际 0 cut(单 shot 5s)→ cut_count_delta = 100% → pacing_deviation = 100% → fail
- cut 过密:storyboard declares 1 cut,preview 实际 4 cuts(1.25s/shot avg,cut density 太高,观众眼疲劳)→ cut_count_delta = 300% → fail
- transition 类型错:storyboard declares `dissolve`,preview 实际 `hard_cut` → transition_mismatch = 100% → fail

---

## Prompt 模板 (Preview Prompt Template)

Step 6.5 把 E-Konte 5-layer storyboard JSON(Step 6 输出)翻译成 LTX2.3 生成调用。模板结构镜像 [`video-gen-model-matrix.md`](../../movie-experts/visual_executor/references/animator/video-gen-model-matrix.md) §短剧 Vertical Generation 协议 heuristic 4。

```yaml
# Step 6.5 preview generation call — assembled from E-Konte Layer 1+2+3
preview_prompt:
  # --- LTX2.3 model call params ---
  model: ltx-2.3                        # default; "causvid" or "kling-1.6-fast" per Model Selection §alternatives
  aspect_ratio: "9:16"                  # 短剧 default vertical
  resolution: "768×1344"                # LTX2.3 768p vertical native
  duration_sec: 5                       # budget cap (load-bearing — see Generation Budget §)
  seed: ${per_scene_baseline_seed}      # deterministic per scene; from storyboard Layer 5
  num_inference_steps: 30               # LTX2.3 default; preview favors speed over detail

  # --- Prompt body — assembled from E-Konte layers (bilingual) ---
  prompt_body: |
    # 从 E-Konte Layer 1+2+3 装配 (中文 + 关键英文术语)
    [Layer 1 stage_geometry]: ${layer_1.stage_geometry}
    [Layer 1 environment_props]: ${layer_1.environment_props | map(attribute='id') | join(', ')}
    [Layer 1 character_blocking]: ${layer_1.character_blocking[0].character_id}
      at position ${layer_1.character_blocking[0].position}, facing ${layer_1.character_blocking[0].facing}
    [Layer 2 camera]: ${layer_2.shot_scale} / ${layer_2.angle} / ${layer_2.camera_move}
      lens ${layer_2.lens_mm}mm, motion_intensity ${layer_2.motion_intensity}
      axis_line ${layer_2.axis_line}, screen_direction ${layer_2.screen_direction}
    [Layer 3 character]: ${layer_3.character_id}
      pose: ${layer_3.pose.body_orientation}, hands ${layer_3.pose.hands}, head ${layer_3.pose.head_tilt}
      expression: ${layer_3.expression.primary} + ${layer_3.expression.secondary} (intensity ${layer_3.expression.intensity})
      action_beat: ${layer_3.action_beat}

    # 中文示例(填充后):
    # [场景] rooftop_night — 城市夜景天台
    # [道具] metal_railing (frame 下方), city_skyline_bg (frame 上方 1/3)
    # [角色 blocking] lead_male at (0.5, 0.5), facing camera_front, standing_lean_on_railing
    # [镜头] MCU / low_angle / tilt_up — 50mm lens, gentle motion
    #   axis +X (L2R), screen direction Up
    # [角色姿态] leaning_forward, right_hand_on_railing, head slight_up
    #   expression: contemplative + longing_micro (intensity 0.7)
    #   action: look_up_at_sky_pause

  # --- Negative prompt — storyboard-vs-preview common failure modes ---
  negative_prompt: |
    deformed, extra limbs, wrong aspect ratio, horizontal composition,
    text watermark, subtitle burned in, multiple scenes in one clip,
    abrupt cut within 5s without declared transition

  # --- Reference inputs (optional, for character consistency) ---
  reference_image: ${character_bible.assets[layer_3.character_id].L1_anchor}
    # from p04 character-bible slot; gives LTX2.3 a face anchor for consistency
```

**装配规则(load-bearing):**

1. **prompt_body 必须从 E-Konte Layer 1+2+3 装配**,不是自由文本 —— storyboard 的结构化字段必须 1:1 映射到 prompt token,避免 LLM "再创作"
2. **negative_prompt 必须包含 `wrong aspect ratio` + `horizontal composition`** —— 防止 LTX2.3 退化到默认 16:9 输出
3. **reference_image 是可选的** —— character_bible 的 L1 anchor(seed face)有助于 cross-clip consistency,但 preview 阶段不强制(Step 7 的 production render 才强制)
4. **seed 必须从 storyboard Layer 5 derive** —— `seed = hash(shot_id + storyboard_version)`;确保同 storyboard 多次 preview 生成可复现,retry 时 prompt 微调才能归因到 prompt diff 而非 random seed

---

## 失败回退策略 (Fallback Policy)

> **本节是 PREVIEW-03 的核心交付物。** 失败路径必须**确定性 + 非 silent skip**。max 2 retries;耗尽 retries 走 **现有 `plugins/review_gates/gate.py` BLOCKING mode** —— **不是新 gate,不是新基础设施**。

### 状态机(load-bearing)

| State | 触发条件 | 动作 |
|-------|----------|------|
| **preview_pass** | 所有 3 维 (composition / framing / pacing) 在阈值内 | 推进到 Step 7 (`p07_scene_generation`) |
| **preview_fail_retry_1** | 任一维 miss(composition < 0.80 OR framing > 10% OR pacing > 15%) | re-invoke Step 6 (`p06_spatio_temporal_script`) 带 audit feedback;re-render preview |
| **preview_fail_retry_2** | 第 2 次 miss(同 trigger) | re-invoke Step 6 带 **累积** feedback(累计 miss pattern,不是只看最近一次);re-render preview |
| **preview_fail_exhausted** | 第 3 次 failure(`attempt > max_retries=2`) | **route to operator review via 现有 `plugins/review_gates/gate.py` BLOCKING mode** |

### 现有 BLOCKING gate 复用(load-bearing — 非新 gate)

PREVIEW-03 的 exhausted path **不创建新 gate_id**。它复用 Phase 34 已交付的 `plugins/review_gates/gate.py` BLOCKING mode:

- **Gate state machine** —— `GateMode.BLOCKING = "blocking"`([`plugins/review_gates/gate.py:64`](../../../plugins/review_gates/gate.py))。BLOCKING mode = synchronous pause on `threading.Event`;caller thread block 直到 `resolve()` 被调用(local operator review)
- **`GateConfig.max_retries: int = 2`** —— 默认值([`plugins/review_gates/gate.py:137`](../../../plugins/review_gates/gate.py))。**Step 6.5 不 override** —— 我们 policy 的 max 2 retries 与 GateConfig 默认完全匹配
- **`GateMaxRetriesExceeded` exception** —— 第 3 次 failure 时 raise;message 携带 `CONSISTENCY_BLOCKED: gate '<gate_id>' exhausted retries (3 > 2)` 前缀([`plugins/review_gates/gate.py:93-112`](../../../plugins/review_gates/gate.py))。这是 **terminal**(非 transient),runner 必须捕获并 mark episode failed
- **PIPE-GUARD-01 semantics** —— `CONSISTENCY_BLOCKED` 前缀是 v4.0 PIPE-GUARD-01 的 marker。Runner 识别此 marker 后**必须** mark episode failed,**不可** 静默 swallow。Preserves "no silent skip" guarantee

### Operator review 决策语义

Step 6.5 exhausted gate 提交时携带:

```yaml
gate_submission:
  gate_id: "step6_5_preview_exhausted"   # logical label (NOT a new V8.6 gate slot)
  episode_id: ${episode_id}
  attempt: 3                              # > max_retries=2
  suggested_action: "rollback:p06_spatio_temporal_script"
  decision: "contest"                     # default for exhausted gate (needs human attention)
  payload:
    preview_clips: ${preview-clips}       # 第 3 次生成的 mp4 paths
    preview_audit: ${preview-audit}       # 3 维分数 + 历史 retry audit
    cumulative_miss_pattern: [...]        # 累积 miss 序列(给 operator 诊断根因)
    storyboard_snapshot: ${spatio-temporal-script}  # 当前 storyboard 状态
```

Operator 通过 BLOCKING gate 的 `resolve()` 选择:

- **`approve`** —— 接受当前 preview(尽管 miss 阈值),推进到 Step 7。Operator 承担 risk;audit 记录 "operator_override_preview_fail"
- **`reject`** —— 拒绝整个 episode;episode 标记 failed,return to creative_source / screenplay upstream
- **`contest`** —— Operator 手动 re-storyboard(不依赖 Step 6 自动 retry);手改 storyboard 后 re-submit preview

### 非 silent-skip 证明(load-bearing)

回退策略的 4 个 state **都不允许 silent skip**:

1. `preview_pass` → 正常推进,audit 记录 3 维分数
2. `preview_fail_retry_1/2` → re-invoke Step 6;audit 记录 miss pattern + retry counter
3. `preview_fail_exhausted` → **GateMaxRetriesExceeded raise + BLOCKING gate submit**;runner block 直到 operator resolve;`CONSISTENCY_BLOCKED` marker 写入 episode audit log

**不存在** "preview failed but pipeline proceeded anyway" 路径。这是 PIPE-GUARD-01 (v4.0) + CF-05 (Phase 34) 的复合保证。

---

## I/O 契约 (Step 6.5 Input/Output)

### Input slots (从 p06 + 跨阶段读)

| Slot | Producer | 用途 |
|------|----------|------|
| `spatio-temporal-script` | p06 → `p06_spatio_temporal_script` | **主输入** —— E-Konte 5-layer storyboard JSON,被翻译成 preview prompt |
| `final-audit` | p06 → `p06_spatio_temporal_script` | Gate 6 spatio-temporal 的审核结果(必须已通过才能进 Step 6.5) |
| `character-bible` | p04 → `p04_character_design` | **跨阶段读** —— 提供 character L1 anchor 作为 reference_image(可选,提升 cross-clip consistency) |

### Output slots (新增 — Phase 41)

| Slot | Format | Writer | Reader(s) | Lifecycle |
|------|--------|--------|-----------|-----------|
| `preview-clips` | JSON (paths to mp4) | p06.5 → `p06_5_ltx2_preview` | operator audit + review_gates escalation path | write-once per attempt (overwrite on retry) |
| `preview-audit` | JSON (3-dim scores + state) | p06.5 → `p06_5_ltx2_preview` | operator audit + review_gates escalation path | write-once per attempt (overwrite on retry) |

**AssetBus envelope wrapping:** `preview-clips` + `preview-audit` 都遵循 V3 envelope(content_hash + derived_from `spatio-temporal-script`)—— provenance chain 保留(preview 从哪个 storyboard 版本生成的可追溯)。Per Phase 33 AssetBus V3 pattern。

### Gate 关系(关键澄清 — 不新增 gate)

Step 6.5 **不添加 V8.6 第 9 号 gate**。Gate 结构仍是 V8.6 canonical 8-gate(详见 [`review-gates.md`](./review-gates.md)):

- **Gate 6 spatio-temporal** —— 仍在 Step 6 后触发(p06 → Gate 6),审核 storyboard 本身
- **Gate 5 scene-design** —— 仍在 Step 7 后触发(p07 → Gate 5),审核 production scene images
- **Step 6.5 exhausted escalation** —— 走 `GateMode.BLOCKING` 但**不是新 gate_id**;它是 retry-policy exhausted exception path,复用现有 framework 的 `GateMaxRetriesExceeded` semantics。Logical label `step6_5_preview_exhausted` 是 audit-log 标识,不进入 `gates.yaml` 注册表

**不要** 把 Step 6.5 escalation 误读为 "V8.6 9-gate"。8-gate 编号 byte-preserved。

---

## Anti-Patterns / What NOT to do

- ❌ **不要跳过 preview 即使 storyboard 自审通过** —— preview 检测的是静态 storyboard audit 检测不到的:运动一致性(motion coherence)、动态取景(framing in motion)、节奏感受(pacing felt-rate)。Gate 6 spatio-temporal 通过 ≠ preview 通过
- ❌ **不要用 veo3.1 / kling-v3-4k 做 preview** —— 它们是 Step 10/11 production-grade 模型;成本 4-7× LTX2.3 for 相同 preview 信号。preview 是 disposable 的,production 模型 overkill
- ❌ **不要 silent 超过 max_retries=2** —— exhausted path 走 BLOCKING gate 是 **non-bypassable**(preserves PIPE-GUARD-01)。不允许 "再试一次说不定过" 路径
- ❌ **不要发明新 gate_id** —— Step 6.5 escalation 复用 `plugins/review_gates/` framework 的 BLOCKING mode + `GateMaxRetriesExceeded` exception。**零新 gate 基础设施**
- ❌ **不要在 v9.0 验证真实 GPU 输出** —— V9-FUTURE-02 deferred;本 baseline doc + Step 6.5 wiring 是 v9.0 deliverable only。Live GPU validation 是 operator 侧责任
- ❌ **不要让 prompt_body 自由文本生成** —— 必须 1:1 从 E-Konte Layer 1+2+3 结构化字段装配;否则 LLM "再创作" 引入 preview-vs-storyboard diff,audit 失败无法归因
- ❌ **不要把 5s 预算 cap 提到 8s/10s** —— 5s 是 budget discipline 锚;提升 cap 会 cost creep($0.10 → $0.20+ per clip),且 wall-clock > 30s 退化 operator UX
- ❌ **不要用 preview 替代 Gate 6 spatio-temporal** —— Gate 6 审 storyboard 结构合法性(axis / scale / composition_lock);preview 审生成结果(动态呈现)。**两层独立,都必过**
- ❌ **不要把 preview-clips 写到 `master-mp4` slot** —— preview 是 disposable artifact;`master-mp4` 是 Step 13 交付物。混用破坏 AssetBus provenance

---

## See Also

- [`pipeline-dag.md`](./pipeline-dag.md) — Step 6.5 slot flow (p06 → p06.5 → p07)
- [`asset-bus-schema.md`](./asset-bus-schema.md) — `preview-clips` / `preview-audit` slot schema (envelope wrapping rules)
- [`review-gates.md`](./review-gates.md) — V8.6 8-gate structure (Step 6.5 escalation **不** 新增 9th gate)
- [`_shared/v86-pipeline-mapping.md`](../../movie-experts/_shared/v86-pipeline-mapping.md) — canonical V8.6 source ref
- [`video-gen-model-matrix.md`](../../movie-experts/visual_executor/references/animator/video-gen-model-matrix.md) — 完整 6-model matrix in movie-experts/visual_executor (本 ref 只覆盖 3 fast-preview 候选)
- [`e-konte-format.md`](../../movie-experts/cinematographer/references/e-konte-format.md) — 5-layer storyboard format(本 ref 的输入 schema)
- [`vertical-screen-framing.md`](../../movie-experts/cinematographer/references/vertical-screen-framing.md) — 9:16 framing rules(framing 维度阈值源)
- [`axis-rules.md`](../../movie-experts/cinematographer/references/axis-rules.md) — 180°/30° axis rule(composition 维度的 axis 校验源)

---

**Ref author:** kais-movie-pipeline team (Phase 41 PREVIEW-01)
**Source date:** 2026-06-27
**Verified against:** LTX Video 2.3 docs / [`video-gen-model-matrix.md`](../../movie-experts/visual_executor/references/animator/video-gen-model-matrix.md) (Phase 5) / [`e-konte-format.md`](../../movie-experts/cinematographer/references/e-konte-format.md) (Phase 20) / [`gate.py`](../../../plugins/review_gates/gate.py) (Phase 34)
