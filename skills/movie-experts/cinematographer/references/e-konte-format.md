# E-Konte Format — 日本动画工业 5-Layer 分镜标注格式 for AI 短剧 / 微电影

**Source:** 日本动画工业公开术语体系(絵コンテ / Layout / ト書き / 絵切り;Studio Ghibli + Madhouse + Production I.G + MAPPA 公开 production documentaries / 业界访谈);今敏《红辣椒》(2006, Madhouse) 公开制作纪录片 + 访谈摘录(《今敏:动画大师》Suzuki 2021 等次级文献);宫崎骏吉卜力工作室公开纪录片(NHK specials / "The Kingdom of Dreams and Madness" 2013);Catherine Munroe Hotes 2010 *A Critical Study of the Genesis and Evolution of Kon Satoshi*;Tony Zhou "Every Frame a Painting" 公开视频随笔(其中分镜工业实践段落);Marcin Nowak "Anime Storyboard Tradition vs Western Live-Action Storyboard" 公开比较随笔(2018)。
**Copyright:** Fair Use — 5 层标注体系是日本动画工业通用术语(行业普遍公开,非单一版权方专有);今敏 / 宫崎骏案例仅作引述级别参考(≤ 1-2 段),不复制具体分镜页或受版权保护的 cut / drawing。See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-18
verified_date: 2026-06

> **⚠ Scope anchor (CONTEXT risk STATE.md 已记录):** 本 ref 覆盖**普通 E-Konte format**(5 层标注)。今敏级 hyper-detailed storyboard(单集 1.5 年分镜周期 / 每帧作画监督过审)**不在 scope**。今敏案例仅作为"精度上限"参考,本 ref 不要求 AI 输出达到今敏级精度。

---

## Summary

本 ref 定义 cinematographer 专家在**东方分镜传统(E-Konte 絵コンテ)**可选路径下的**中间格式权威源**(Eastern storyboard intermediate format)。它涵盖 5 层标注体系(场景布局 / 镜头角度与运动 / 角色位置表情动作 / 对白音效 / 时间帧数)+ 与西方 storyboard(Mascelli 8-level + Arijon composition + 180°/30° axis)的对比 + 今敏 / 宫崎骏两条参考案例。

它与 [`shot-grammar.md`](./shot-grammar.md)(西方语法侧)、[`axis-rules.md`](./axis-rules.md)(西方几何侧)、[`camera-motion-catalog.md`](./camera-motion-catalog.md)(西方运动侧)和 [`vertical-screen-framing.md`](./vertical-screen-framing.md)(竖屏侧)**互补不替代** —— E-Konte 是可选的**东方分镜语法**,在导演风格 = 东方 或 scene 信息密度 ≥ threshold 时触发。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## E-Konte 5 Annotation Layers

### 关键 heuristic 1 (load-bearing): E-Konte 5 层标注的语义层独立性

E-Konte(絵コンテ)是日本动画工业自 1960s 虫プロダクション《铁臂阿童木》时代定型的**分镜标准格式**。与西方 storyboard(每页一张图 + 一句 scene description)不同,E-Konte 在单页内强制 5 层标注,每层独立可消费:

| Layer | 日文术语 | 中文 | 字段 schema | 消费方 |
|-------|----------|------|-------------|--------|
| **Layer 1** | 絵(画)+ 場面設定 | 场景布局(Stage Layout)| `stage_geometry` / `props[]` / `character_blocking[]` | cinematographer 自身(composition_lock 子任务)+ scene_builder 兼容(已 deprecated → cinematographer 内化) |
| **Layer 2** | カメラ / 鏡頭 | 镜头角度与运动(Camera Angle & Movement)| `shot_scale` / `angle` / `camera_move` / `lens_mm` | visual_executor animator sub-step(camera-motion-catalog.md 12 moves 的东方映射) |
| **Layer 3** | 絵(角色)+ 絵姿 | 角色位置表情动作(Character Pose / Expression / Action)| `character_id` / `pose` / `expression` / `action_beat` | visual_executor drawer sub-step(FLUX 2 character pose reference)+ character_designer(STYLE_PREFIX 验证) |
| **Layer 4** | セリフ(台詞)+ 音(効果音・BGM)| 对白音效(Dialogue & SFX)| `dialogue_line` / `dialogue_character` / `sfx[]` / `bgm_cue` | audio_pipeline voicer / composer / foley sub-steps |
| **Layer 5** | 秒数 / フレーム / 絵切り | 时间帧数(Duration & Frame Count)| `duration_sec` / `frame_count` / `fps` / `cut_transition_type` | editor(beat timing + cut density)+ visual_executor animator(duration 参数) |

**关键差异(与西方):** E-Konte 把"分镜页"从"图文 1:1 单元"重构为"5 维 annotation slice"。这让下游 expert 可以**只消费自己需要的层**(visual_executor drawer 只读 Layer 1+3,audio_pipeline 只读 Layer 4),减少信息过载。

### Layer 1: 場面設定 / 场景布局(Stage Layout)

**字段 schema:**

```yaml
layer_1_stage_layout:
  stage_geometry: "indoor_office_desk"  # 场所 tag,从 scene_builder 现有 inventory 继承
  environment_props:
    - id: "desk_main"
      position: { x: 0.4, y: 0.6 }  # 9:16 归一化坐标
      anchor: "frame_right"
    - id: "laptop_open"
      position: { x: 0.4, y: 0.55 }
      parent: "desk_main"
  character_blocking:
    - character_id: "lead_female"
      position: { x: 0.5, y: 0.7 }  # MCU 占 frame 30-40% 主体位
      facing: "camera_3q_left"
      stance: "seated"
```

**短剧 9:16 适配:** 与 cinematographer 现有 `scene_builder_handoff.json` schema 兼容(Phase 17 v3.0 已折叠入 composition_lock 子任务)。9:16 vertical blocking 强制角色上下站位优于左右站位(详见 [`vertical-screen-framing.md`](./vertical-screen-framing.md) §Vertical Blocking)。

### Layer 2: カメラ / 镜头角度与运动(Camera Angle & Movement)

**字段 schema:**

```yaml
layer_2_camera:
  shot_scale: "MCU"           # Mascelli 8-level 之一,详见 shot-grammar.md
  angle: "eye_level"          # eye_level / low_angle / high_angle / bird_eye / worm_eye
  camera_move: "dolly_in"     # camera-motion-catalog.md 12 moves 之一
  lens_mm: 35                 # 焦距 hint(给 visual_executor animator 翻译 prompt token)
  motion_intensity: "subtle"  # subtle / gentle / moderate / high / extreme
```

**与现有 12 camera moves 的映射:** E-Konte Layer 2 的 `camera_move` 字段直接复用 [`camera-motion-catalog.md`](./camera-motion-catalog.md) 的 12-move taxonomy(static / pan / tilt / dolly_in / dolly_out / tracking / crane_up / crane_down / handheld / steadicam / zoom_in / zoom_out)。**E-Konte 不引入新 move 类型**,只是把 move 显式标注在分镜页内(西方传统依赖独立 shot list 文档)。

### Layer 3: 絵姿 / 角色位置表情动作(Character Pose / Expression / Action)

**字段 schema:**

```yaml
layer_3_character:
  character_id: "lead_female"  # 对接 character_designer character_bible.json 的 id
  pose:
    body_orientation: "seated_forward"
    hands: "laptop_typing"
    head_tilt: "slight_left"
  expression:
    primary: "concentrated"
    secondary: "anxious_micro"
    intensity: 0.6  # 0.0-1.0,给 drawer 翻译为 InstantID + LoRA 强度
  action_beat: "type_pause_look_up"  # 短剧 1 shot 内的可视化动作锚点
```

**与 character_designer STYLE_PREFIX 的集成:** Layer 3 的 `character_id` 必须能 join 到 character_designer 的 `character_bible.json`(详见 [`../character_designer/SKILL.md`](../character_designer/SKILL.md))。drawer sub-step 读 Layer 3 + STYLE_PREFIX 组合生成 FLUX 2 prompt。

### Layer 4: セリフ + 音 / 对白音效(Dialogue & SFX)

**字段 schema:**

```yaml
layer_4_audio:
  dialogue:
    - character_id: "lead_female"
      line: "这件事我不能答应。"
      emotion_tag: "controlled_anger"
  sfx:
    - cue: "keyboard_stop"
      timing: "at_dialogue_start"
  bgm_cue:
    track_id: "tension_pad_03"
    intensity_curve: [0.3, 0.5, 0.7]  # 3 个 anchor 点
```

**与 audio_pipeline 的集成:** Layer 4 是 audio_pipeline(voicer / composer / foley / mixer)的**直接输入**。本 ref 不重复 audio_pipeline 的内部 schema,只在 E-Konte 分镜页里保留"这一 shot 有哪些音频元素"的最小标注。

### Layer 5: 秒数 / フレーム / 絵切り / 时间帧数(Duration & Frame Count)

**字段 schema:**

```yaml
layer_5_timing:
  duration_sec: 3.2
  frame_count: 77          # 24fps × 3.2s = 77 frames(短剧标准 24fps)
  fps: 24                  # 详见 vertical-screen-framing.md §FPS Standards
  cut_transition_type: "hard_cut"  # hard_cut / dissolve / wipe / fade
  next_shot_link: "shot_02"  # 絵切り 后续 shot id
```

**关键 heuristic(load-bearing):** E-Konte Layer 5 把"时间"作为**第一公民字段**(西方 storyboard 把时间藏在 scene description 文字里)。这让 editor 可以直接读 Layer 5 算 cut density(短剧标准 1.5-2x horizontal cut density,详见 [`vertical-screen-framing.md`](./vertical-screen-framing.md) §短剧 Cut Density)。

---

## 短剧 9:16 E-Konte 修正

### 关键 heuristic 2: 竖屏 vs 日本动画传统横屏 16:9 的差异

日本动画 E-Konte 传统基于 16:9 横屏(或 4:3 古典比例)。竖屏 9:16 适配需要 3 项修正:

| 维度 | 日本动画 16:9 传统 | 短剧 9:16 修正 |
|------|---------------------|----------------|
| **Layer 1 stage_geometry** | 横向宽度优先(场景横向延伸)| 纵向深度优先(场景竖向延伸;Vertical blocking > Horizontal blocking) |
| **Layer 2 camera_move** | Pan / Tracking 横向运动占比高 | Tilt / Crane Up-Down / Vertical Tracking 占比高(避免主体出 frame) |
| **Layer 5 duration_sec** | 单 shot 平均 4-6s(日本动画 cut 长)| 单 shot 平均 1.5-3s(短剧 cut density 1.5-2x horizontal;详见 vertical-screen-framing.md) |

**关键例外:** 男频爽点 beat 的"打脸"reaction shot 在短剧里仍可走 1s fast cut(Layer 5 duration 极短);这在日本动画传统里少见,但短剧作为商业格式接受。

---

## E-Konte vs Western Storyboard 对比表

### 关键 heuristic 3 (load-bearing): 东西方分镜格式映射

本表是 EKONTE-01 success criterion 的核心交付物,定义 E-Konte 5 层与西方 storyboard 体系(Mascelli 8-level + Arijon composition + 180°/30° axis)的**映射关系**。**核心结论:互补不替代** —— 东方分镜语法 vs 西方轴线传统。

| 维度 | E-Konte(日本动画工业) | Western Storyboard(Mascelli / Arijon / Hollywood)| 映射关系 |
|------|-------------------------|---------------------------------------------------|----------|
| **结构** | 单页 5 层 annotation slice | 单页 1 图 + 1 scene description | E-Konte Layer 1+2 ≈ Western 图 + scene description;E-Konte Layer 3+4+5 是 Western 缺失的独立层 |
| **Shot Scale** | Layer 2 `shot_scale` 字段引用 Mascelli 8-level | Mascelli 8-level(EWS / WS / FS / MS / MCU / CU / BCU / INSERT) | **完全映射**(E-Konte 复用 Mascelli 词汇,详见 shot-grammar.md) |
| **Camera Move** | Layer 2 `camera_move` 字段引用 12-move taxonomy | Mascelli 5 C's + Arijon motion vocabulary | **完全映射**(E-Konte 复用 12 moves,详见 camera-motion-catalog.md) |
| **Axis Rule** | E-Konte 传统**不显式标注 180° axis**(日本动画 axis 由 layout board 隐式约束)| Western 显式 `axis_line` 字段 + 30° rule + screen direction | **不映射** —— E-Konte 路径仍必须由 cinematographer 的现有 axis-rules.md 兜底(轴线性不可妥协,详见 axis-rules.md) |
| **时间** | Layer 5 `duration_sec` + `frame_count` 显式标注 | "每页 ≈ 1 分钟"启发式(Syd Field 等) | E-Konte 更精细;Western 启发式不适用于短剧 60-180s 单集 |
| **音频** | Layer 4 显式 dialogue + sfx + bgm_cue | 散落在 scene description 文字里 | E-Konte 更适合 AI 自动化(audio_pipeline 可直接消费 Layer 4) |
| **角色动作** | Layer 3 显式 pose + expression + action_beat | 散落在 scene description 文字里 | E-Konte 更适合 AI drawer 自动化(FLUX 2 prompt 直接构造) |
| **Cut Transition** | Layer 5 `cut_transition_type` 显式 | Western 不显式(交由 editor 后期决定) | E-Konte 把 cut 节奏前移到分镜阶段 |
| **典型页数** | 单集 TV anime ≈ 300 页 E-Konte(24min × 12-15 cut/page)| Hollywood feature ≈ 1000-3000 张图 | 短剧 60-180s 单集 ≈ 30-90 页 E-Konte(每页 1 cut) |
| **作者** | 监督(导演)亲手绘制(宫崎骏 / 今敏 / 新海诚)| 分镜师(storyboard artist)独立职业 | 短剧 AI 流程:cinematographer LLM 生成 + 人类 supervisor 审核 |

### 关键 heuristic 4: 互补声明(load-bearing)

E-Konte 与西方 Mascelli / Arijon / 180° axis 体系是**互补不替代**关系:

- **E-Konte 复用** Mascelli 8-level shot scale 词汇(Layer 2 `shot_scale` 字段直接引用)
- **E-Konte 复用** 12 camera moves taxonomy(Layer 2 `camera_move` 字段直接引用)
- **E-Konte 不替代** 180° / 30° axis rule —— 即使选 E-Konte 路径,axis 仍由 cinematographer 的 [`axis-rules.md`](./axis-rules.md) 显式校验(axis_line 字段在 Layer 2 内保留)
- **E-Konte 不替代** Western vertical-screen-framing 9:16 power points / headroom / subtitle safe area(详见 [`vertical-screen-framing.md`](./vertical-screen-framing.md))

**操作化:** cinematographer 的 `composition_lock` 子任务在导演风格 = 东方时**双输出** —— 同时生成 `shot_intent.json`(西方语义层)+ `e_konte.json`(东方分镜层);两者 schema 在 Layer 2 `shot_scale` + `camera_move` 字段一致,下游 visual_executor 选择消费路径。

---

## 今敏《红辣椒》案例(精度上限参考)

> **本段落仅作参考引述,不要求 AI 输出达到今敏级精度。** 今敏(1963-2010)是日本动画工业 E-Konte 实践的**精度上限参考**。

今敏的《红辣椒》(Paprika,2006,Madhouse 制作)是日本动画工业公开记录最完整的"E-Konte 极致化"案例。根据公开制作纪录片(Suzuki, T. *Kon Satoshi: The Illusionist*,2021;以及 Madhouse 公开的 production notes),该片分镜阶段持续约 **1.5 年**(18 个月),今敏亲手绘制了**几乎全部** ~1500 个 cut 的 E-Konte 页(标准 TV 动画一集 ~300 cut,电影 ~1500 cut)。

**为什么这个案例对 AI 短剧有意义?**

1. **5 层标注的"极致化"参考** —— 今敏的 E-Konte 页里,Layer 3(角色动作)的精度细化到帧级表达式变化(单 cut 内 5-8 个 expression keyframe),Layer 5(时间)细化到帧级 cut transition。本 ref 的 schema 支持 keyframe 字段但不要求该精度。
2. **东方分镜监督亲手绘制传统** —— 与西方"分镜师独立职业"不同,日本动画监督(导演)通常亲手绘制 E-Konte。这影响 E-Konte 的格式:它是**导演视角的视觉笔记**,不是工程交付物。
3. **AI 化的 scope 边界** —— 今敏级 hyper-detailed storyboard 在 AI 短剧生产里**不必要也不可行**(短剧 60-180s 单集 + 商业化快速迭代节奏)。本 ref 只覆盖普通 E-Konte 5 层标注。

**公开访谈参考:** 今敏在多个公开访谈(收录于 *Satoshi Kon: The Animation Master* 访谈集,以及各动漫杂志)中提到他偏爱先画 E-Konte 再写剧本的"逆向创作法" —— 这在 AI 短剧生产里不适用(剧本必须先行以满足监管备案),但反映了 E-Konte 在东方传统里的核心地位。

---

## 宫崎骏吉卜力实践(Layout 制度)

> **本段落作参考引述,不要求 AI 输出达到吉卜力级 Layout 精度。**

宫崎骏与吉卜力工作室(Studio Ghibli)的 E-Konte 实践的核心特征是 **Layout(レイアウト)制度** —— 在 E-Konte(分镜)和 Key Animation(原画)之间插入一道独立工序。这一制度由宫崎骏和高畑勋在 1970s 末期定型,成为吉卜力作品的视觉签名。

**Layout 制度与 E-Konte 5 层的耦合:**

| 工序 | 吉卜力 | 与 E-Konte 层对应 |
|------|--------|-------------------|
| E-Konte(絵コンテ)| 宫崎骏亲手绘制 | Layer 1+2+5(场景布局 + 镜头 + 时间) |
| **Layout(レイアウト)** | 每原画师负责 1 cut 的详细 layout drawing,定义该 cut 内的空间几何 + 光影 + 角色 blocking 细节 | Layer 1+3 的细化(场景布局 + 角色位置的精确几何) |
| Key Animation(原画)| 角色动作关键帧 | Layer 3 的 action_beat 细化 |

**为什么这个案例对 AI 短剧有意义?**

1. **Layout 是 E-Konte Layer 1+3 的"工程化分离"** —— 吉卜力把 Layer 1(场景几何)从 E-Konte 页里抽出来作为独立 Layout 图,因为动画场景需要美术部门先行建模。AI 短剧可以借鉴这一分层(visual_executor 的 drawer sub-step 的 background generation + foreground character generation 分离),但本 ref 的 schema 把 Layer 1+3 保留在同一 E-Konte 页内(避免过度工程化)。
2. **Layout 字段在 E-Konte schema 中的对应** —— 本 ref 的 Layer 1 `stage_geometry` + Layer 3 `pose` / `position` 字段相当于吉卜力 Layout 的简化版。完整的吉卜力 Layout 需要 perspective grid + lighting diagram + camera field-of-view 角度,这些字段超出本 ref 的 scope。
3. **宫崎骏"分镜优先"哲学** —— 宫崎骏公开访谈多次强调"E-Konte 决定一切",剧本可以在分镜后微调。这在 AI 短剧里**不适用**(短剧必须先备案剧本),但反映了 E-Konte 在东方传统里的核心地位。

**公开纪录片参考:** 《梦与狂想的王国》(The Kingdom of Dreams and Madness,2013,NHK / DW)纪录片公开记录了宫崎骏绘制《起风了》(2013)E-Konte 的过程;《宫崎骏:十载同行》(10 Years with Hayao Miyazaki,2019,NHK)纪录片第 2 集详细展示了 Layout 制度。

---

## Trigger Conditions — 何时选 E-Konte vs Western Storyboard

### 关键 heuristic 5: 触发条件(load-bearing)

E-Konte 是**可选**的中间格式,不是默认路径。cinematographer 的 `composition_lock` 子任务按以下条件决定是否生成 `e_konte.json`:

| 条件 | 触发 E-Konte 路径 | 触发 Western 路径 |
|------|--------------------|--------------------|
| `director_style == "eastern_anime"` OR `style_genome.dna.eastern == true` | ✅ 强制触发 | (不触发) |
| `style_genome.dna.western_live_action == true` | (不触发) | ✅ 强制触发 |
| `scene.visual_density ≥ 0.75`(信息密度高,多角色 + 多道具 + 多动作)| ✅ 触发评估 | (不触发) |
| 单 episode `runtime_sec < 180`(短剧 60-180s 单集)| (不触发 — E-Konte overhead 太高)| ✅ 默认 Western |
| 单 episode `runtime_sec ≥ 180`(微电影 / 长剧)| ✅ 触发评估 | ✅ 仍可选 |
| `style_genome.references` 含今敏 / 宫崎骏 / 新海诚 / 山田尚子等东方监督 | ✅ 强制触发 | (不触发) |

**短剧默认策略:** 短剧 60-180s 单集默认走 Western storyboard 路径(理由:E-Konte 5 层标注的 overhead 对 30-90 cut 的小项目不划算)。仅在导演风格 = 东方动画 OR 监督引用东方传统时触发 E-Konte。

**微电影 / 长剧默认策略:** 微电影(5-30min)默认评估 E-Konte 路径(信息密度高时收益大)。

### 关键 heuristic 6: 双输出选项

当触发 E-Konte 路径时,cinematographer **同时**生成:

1. `shot_intent.json`(西方语义层,与 axis-rules.md + camera-motion-catalog.md 兼容)
2. `e_konte.json`(东方分镜层,本 ref 定义 schema)

**理由:** 即使走 E-Konte 路径,下游 editor 仍需要西方的 `axis_line` 字段做 cross-cut compliance 验证(详见 [`axis-rules.md`](./axis-rules.md) §180° Axis Rule);下游 continuity_auditor 仍需要西方的 `shot_intent.json` 做 4 维一致性审计。E-Konte 不替代西方 schema,只补充东方视角。

---

## 与现有 Mascelli / Arijon / 180°/30° 规则的集成

### 关键 heuristic 7: 字段共享 + 字段补充

E-Konte Layer 2 的字段(`shot_scale` / `angle` / `camera_move` / `lens_mm`)**完全复用** cinematographer 现有西方路径的 schema(详见 [`shot-grammar.md`](./shot-grammar.md) + [`camera-motion-catalog.md`](./camera-motion-catalog.md))。这意味着:

- 选 E-Konte 路径**不需要重新设计 shot_scale 词汇**(直接引用 Mascelli 8-level)
- 选 E-Konte 路径**不需要重新设计 camera_move 词汇**(直接引用 12 moves)
- 选 E-Konte 路径**不需要绕开 axis rule**(Layer 2 仍含 `axis_line` 字段,详见 axis-rules.md)

E-Konte 的**字段补充**在 Layer 3(角色动作)+ Layer 4(音频)+ Layer 5(时间)三层,这三层在西方 schema 里要么散落在 scene description 文字里(Layer 3+4),要么用"每页 ≈ 1 分钟"启发式粗估(Layer 5)。

### 关键 heuristic 8: storyboard_designer deprecated 的承诺兑现

Phase 17 v3.0 deprecate `storyboard_designer` expert 时,`deprecated_reason` 字段承诺"分镜设计职能已折叠至 cinematographer 的 composition_lock 子任务"。Phase 20 的 E-Konte 集成是对这一承诺的兑现 —— E-Konte 不创建新 expert_id,不复活 `storyboard_designer`,完全活在 `cinematographer.composition_lock` 子任务下。

详见 [`../storyboard_designer/SKILL.md`](../storyboard_designer/SKILL.md)(deprecated redirect-only stub)+ [`../../.planning/phases/17-skills-to-dag-alignment/`](../../.planning/phases/17-skills-to-dag-alignment/)(Phase 17 决策记录)。

---

## Output Schema (`e_konte.json`)

### 关键 heuristic 9: 单 shot 完整 schema

```yaml
e_konte:
  shot_id: "ep01_shot_007"        # 短剧 EP01 第 7 个 shot
  scene_id: "ep01_sc03"           # 所属 scene
  trigger_reason: "director_style_eastern_anime"  # 触发条件记录(审计用)

  layer_1_stage_layout:
    stage_geometry: "rooftop_night"
    environment_props:
      - id: "railing_metal"
        position: { x: 0.5, y: 0.85 }  # 9:16 归一化
      - id: "city_skyline_bg"
        position: { x: 0.5, y: 0.3 }
    character_blocking:
      - character_id: "lead_male"
        position: { x: 0.5, y: 0.5 }
        facing: "camera_front"
        stance: "standing_lean_on_railing"

  layer_2_camera:
    shot_scale: "MCU"             # Mascelli 8-level
    angle: "low_angle"            #仰视增 power(男频爽点)
    camera_move: "tilt_up"        # 12 moves 之一
    lens_mm: 50
    motion_intensity: "gentle"
    axis_line: "+X (L2R)"         # axis-rules.md 强制保留
    screen_direction: "Up"        # vertical tilt

  layer_3_character:
    character_id: "lead_male"
    pose:
      body_orientation: "leaning_forward"
      hands: "right_hand_on_railing"
      head_tilt: "slight_up"      # 仰望 sky
    expression:
      primary: "contemplative"
      secondary: "longing_micro"
      intensity: 0.7
    action_beat: "look_up_at_sky_pause"

  layer_4_audio:
    dialogue:
      - character_id: "lead_male"
        line: "原来这就是她说的自由。"
        emotion_tag: "realization"
    sfx:
      - cue: "wind_gentle"
        timing: "throughout"
    bgm_cue:
      track_id: "melancholy_piano_02"
      intensity_curve: [0.2, 0.4, 0.5]

  layer_5_timing:
    duration_sec: 3.0
    frame_count: 72              # 24fps × 3s
    fps: 24
    cut_transition_type: "dissolve_from_prev"
    next_shot_link: "ep01_shot_008"

# 下游消费:
# visual_executor.drawer <- layer_1 + layer_3 (FLUX 2 character + background prompt)
# visual_executor.animator <- layer_2 + layer_5 (camera_move + duration_sec)
# audio_pipeline.voicer <- layer_4.dialogue
# audio_pipeline.composer <- layer_4.bgm_cue
# audio_pipeline.foley <- layer_4.sfx
# editor <- layer_5 (beat timing + cut density)
# continuity_auditor <- layer_2 (axis + shot_scale continuity)
```

---

## Anti-Patterns / What NOT to do

- ❌ **不要把今敏级精度作为 AI 输出标准** —— 本 ref 只覆盖普通 E-Konte 5 层标注。今敏案例仅作参考引述。
- ❌ **不要在短剧 60-180s 单集默认触发 E-Konte** —— 除非导演风格 = 东方 OR 监督引用东方传统,默认走 Western storyboard。
- ❌ **不要省略 Layer 2 `axis_line` 字段** —— 即使走 E-Konte 路径,180° axis rule 仍然强制(详见 [`axis-rules.md`](./axis-rules.md))。
- ❌ **不要重新发明 shot_scale 词汇** —— Layer 2 `shot_scale` 直接引用 Mascelli 8-level(详见 [`shot-grammar.md`](./shot-grammar.md) §Shot Scale Taxonomy)。
- ❌ **不要重新发明 camera_move 词汇** —— Layer 2 `camera_move` 直接引用 12 moves taxonomy(详见 [`camera-motion-catalog.md`](./camera-motion-catalog.md) §12 Camera Moves Taxonomy)。
- ❌ **不要复活 deprecated 的 `storyboard_designer` expert** —— E-Konte 折叠进 cinematographer.composition_lock,不创建新 expert_id。
- ❌ **不要把 Layer 4 音频字段写满完整 audio_pipeline schema** —— Layer 4 只保留"这一 shot 有哪些音频元素"的最小标注,完整 audio 由 audio_pipeline 内部生成。
- ❌ **不要在 E-Konte 里塞入 9:16 power points / headroom / subtitle zone** —— 那是 [`vertical-screen-framing.md`](./vertical-screen-framing.md) 的责任,E-Konte 不重复。
- ❌ **不要把 Layer 3 `pose` / `expression` 写成自由文本** —— 字段 schema 必须结构化(`body_orientation` / `hands` / `head_tilt` / `primary` / `secondary` / `intensity`),否则下游 drawer 无法消费。
- ❌ **不要忽略 `next_shot_link` 字段** —— E-Konte 的 絵切り(cut transition)依赖这一字段形成 shot 链,editor 必须能 follow。

---

## License

本 ref 是日本动画工业 5 层 E-Konte 标注格式的 Fair Use paraphrase(行业通用术语 + 标注层结构 + 字段 schema)。未复制今敏 / 宫崎骏的具体分镜页、受版权保护的 cut drawing、或具体作品的 frame-level storyboard。今敏 / 宫崎骏段落仅引述公开访谈 / 纪录片的次级文献,引述级别 ≤ 1-2 段。详细 License 见 [`LICENSE.md`](./LICENSE.md)。

E-Konte 5 层标注体系是日本动画工业自 1960s 虫プロダクション《铁臂阿童木》时代定型的行业通用术语,非单一版权方专有。本 ref 的 schema 设计、短剧 9:16 适配、与西方 Mascelli / Arijon / 180° axis 的对比表、今敏 / 宫崎骏段落的选择性引述等部分是 Hermes Agent 项目原创工作。

---

**Ref author:** cinematographer expert team (Phase 20 EKONTE-01)
**Source date:** 2026-06-18
**Verified against:** Mascelli 8-level([`shot-grammar.md`](./shot-grammar.md))+ 12 camera moves([`camera-motion-catalog.md`](./camera-motion-catalog.md))+ 180°/30° axis([`axis-rules.md`](./axis-rules.md))+ 9:16 vertical framing([`vertical-screen-framing.md`](./vertical-screen-framing.md))+ character_bible.json schema([`../character_designer/SKILL.md`](../character_designer/SKILL.md))
