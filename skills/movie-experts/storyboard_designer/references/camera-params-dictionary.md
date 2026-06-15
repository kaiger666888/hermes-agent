# Camera Params Dictionary (镜头参数词典)

**Source:** Bordwell & Thompson *Film Art* + cinematography industry standard + 短剧 9:16 vertical framing practice.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

The authoritative dictionary of camera angle types, movement types, and lens focal lengths. Each entry maps the parameter choice to its emotional / informational effect. Use this dictionary when assigning `camera.angle`, `camera.movement`, and `camera.lens` to each shot.

## Heuristics

### 9 shot types (angle / framing)

| CN | EN | Use case | Emotional effect |
|---|---|---|---|
| 鸟瞰 | Bird's Eye (top-down) | 上帝视角 / map view / 万物渺小 | 超然 / 全知 / 抽离 |
| 俯拍 | High Angle | 弱化角色 / 展示全局 | 压抑 / 渺小 / 被支配 |
| 荷兰角 | Dutch Angle (tilted) | 不安 / 失衡 / 心理扭曲 | 焦虑 / 混乱 / 紧张 |
| 平视 | Eye-level (neutral) | 中性叙事 / 主体平等 | 自然 / 客观 |
| 仰拍 | Low Angle | 强化角色 / 威慑感 | 力量 / 威胁 / 英雄 |
| 虫瞰 | Worm's Eye (extreme low) | 极端强化 / 巨物感 | 极端力量 / 敬畏 |
| 过肩 | Over-the-shoulder (OTS) | 对话场景 / 视角切换 | 互动 / 代入 / 紧张 |
| 主观视角 | POV | 第一人称 / 沉浸 | 沉浸 / 同步 / 紧张 |
| 反转视角 | Reverse POV | 看向 POV 主体 | 揭示 / 反转 |

### Shot size (framing scale)

| CN | EN | Subject framing | Use case |
|---|---|---|---|
| 极远景 | Extreme Wide Shot (EWS) | 主体极小,环境主导 | 场景建立 / 史诗感 |
| 远景 | Wide Shot (WS) | 主体全身,环境明显 | 场景建立 / 角色关系 |
| 全景 | Full Shot (FS) | 主体全身,环境次要 | 动作展示 / 走位 |
| 中远景 | Medium Wide (MWS) | 膝盖以上 | 走动 / 半身动作 |
| 中景 | Medium Shot (MS) | 腰部以上 | 对话 / 日常动作 |
| 中近景 | Medium Close-up (MCU) | 胸部以上 | 对话 / 情绪 |
| 近景 | Close-up (CU) | 面部为主 | 情感 / 细节 |
| 大特写 | Extreme Close-up (ECU) | 局部特写 | 极端情绪 / 关键细节 |

### 7 movement types

| CN | EN | Effect | Best use |
|---|---|---|---|
| 推进 | Push-in (dolly-in) | 引导注意力,增加紧张感 | 情绪累积 / 揭示 |
| 拉远 | Pull-out (dolly-out) | 揭示全貌,释放情绪 | 揭示 / 情绪释放 |
| 横摇 | Pan (horizontal) | 展示环境,跟随运动 | 场景扫描 / 跟随 |
| 俯仰 | Tilt (vertical) | 展示高度,揭示信息 | 全身扫描 / 高低对比 |
| 跟拍 | Tracking (lateral) | 沉浸式,与角色同行 | 走动 / 追逐 |
| 手持 | Handheld | 纪实感,紧张不安 | 紧张场景 / 纪录感 |
| 固定 | Static | 观察,稳定,仪式感 | 仪式 / 静态情绪 |

### Advanced movements

| Movement | Description | Effect |
|---|---|---|
| Crane (升/降) | Camera moves vertically via crane / jib | 主题揭示 / 视角变化 |
| Steadicam | Smooth tracking via stabilizer | 平滑跟随 / 沉浸感 |
| Drone (无人机) | Aerial shots | 鸟瞰 / 场景规模 |
| Zoom (光学变焦) | Lens focal length change without camera move | 注意力引导 / 时空感 |
| Whip-pan | Fast pan creating motion blur | 能量 / 转场 |
| Vertigo effect (dolly zoom) | Dolly + zoom in opposite directions | 不安 / 心理冲击 |

### Lens focal length dictionary

| Lens | Focal length | Angle of view | Emotional effect | Best use |
|---|---|---|---|---|
| Ultra-wide | 14-24mm | 90°+ | 宏大 / 失真 / 不安 | 场景建立 / 心理扭曲 |
| Wide | 24-35mm | 60-90° | 宏大 / 孤寂 / 环境主导 | 远景 / 史诗感 |
| Normal-wide | 35mm | 55° | 自然略宽 | 街景 / 走动 |
| Natural | 50mm | 40° | 中性 / 自然 / 人眼近似 | 默认 / 日常 |
| Portrait | 85mm | 25° | 亲密 / 情绪聚焦 / 浅景深 | 人像 / 情绪 |
| Short telephoto | 100-135mm | 15-20° | 压迫 / 被注视 / 紧张 | 偷窥 / 压迫感 |
| Telephoto | 200mm+ | < 15° | 极度压迫 / 远观 | 体育 / 野生动物 / 监视 |

### Lens compression effect

**Longer focal length = more background compression** (background appears closer to subject).

| Subject-to-camera distance | Focal length needed | Compression |
|---|---|---|
| Same framing, close | 35mm | Low (background far) |
| Same framing, mid | 85mm | Medium |
| Same framing, far | 200mm | High (background close) |

**Use case:** to make background loom over subject (threatening), use long lens + far subject-to-camera distance.

### Vertical (9:16) 短剧 adaptations

**Vertical frame changes default lens + angle choices:**

| Parameter | Horizontal default | Vertical 短剧 default | Reason |
|---|---|---|---|
| Default shot size | Medium Shot | Medium Close-up | Vertical frame favors tighter framing |
| Default lens | 50mm | 50-85mm | Vertical allows tighter portrait lens |
| Wide shot frequency | Frequent | Rare | Wide shots waste vertical real estate |
| Close-up frequency | Occasional | Frequent | Close-ups fill vertical frame well |
| Caption strip | None | Bottom 10-15% reserved | Platform convention |

### Composition safe zones (9:16)

For 抖音 / 快手 / 视频号 vertical 短剧:

```
┌────────────────────┐
│   TOP SAFE ZONE    │  ← top 5%: UI elements (likes count)
├────────────────────┤
│                    │
│                    │
│   ACTION SAFE ZONE │  ← middle 80%: critical action here
│                    │
│                    │
├────────────────────┤
│   CAPTION STRIP    │  ← bottom 10-15%: caption overlay
└────────────────────┘
```

**Hard rule:** critical action + character faces must NOT be placed in the caption strip area.

### Color temperature by lens mood

| Mood | Color temp | Lens pairing |
|---|---|---|
| 冷峻 / 冷漠 / 科技 | 5500-6500K (cool daylight) | Wide + Natural |
| 温暖 / 亲密 / 怀旧 | 2700-3200K (warm tungsten) | Portrait |
| 戏剧 / 紧张 / 高对比 | mixed warm/cool | Short telephoto |
| 中性 / 客观 / 新闻 | 4500K (neutral) | Natural |

### Camera parameter assignment decision tree

```
What is the shot's primary purpose?
├── Establish setting → Wide Shot, 24-35mm, Static or Slow Pan
├── Show action → Full Shot or Medium Wide, 35-50mm, Tracking
├── Reveal emotion → Close-up, 85mm, Slow Push-in
├── Dialogue exchange → MCU or OTS, 50-85mm, Static
├── Build tension → MCU, 85-135mm, Slow Push-in
├── Disorient / disturb → Dutch Angle, varied lens, Handheld
├── Establish power dynamic → Low Angle (dominant) / High Angle (submissive)
└── Transition between scenes → Tracking OR Whip-pan OR Match-cut
```

### Common pitfalls

| Pitfall | Cause | Fix |
|---|---|---|
| Dutch Angle overuse | Treat DA as "cool" rather than meaningful | Reserve for genuine psychological effect |
| Too many wide shots in vertical | Defaulting to horizontal composition | Switch defaults per [`#vertical-adaptations`] |
| Wrong lens for emotion | Don't know lens-emotion mapping | Use [`#lens-focal-length-dictionary`] |
| Caption strip blocking action | Forgot vertical safe zones | Place action in middle 80% |
| Handheld overuse | "More cinematic" misconception | Reserve for tense / documentary scenes |
| Push-in too fast | Rush the emotion | Slow push-in: motion_speed 0.2-0.4 |
| Static when motion needed | Lazy camera choice | Add subtle push-in or tracking for energy |

---

## Cross-references

- [`./shot-decomposition-rules.md`](./shot-decomposition-rules.md) — when each shot type is chosen
- [`./4d-anchoring-params.md`](./4d-anchoring-params.md) — anchoring complements camera choice
- [`../../cinematographer/SKILL.md`](../../cinematographer/SKILL.md) — upstream cinematography doctrine
- [`../../_shared/glossary.md`](../../_shared/glossary.md) §运镜 / 景别 / 视角 — canonical CN↔EN terms
