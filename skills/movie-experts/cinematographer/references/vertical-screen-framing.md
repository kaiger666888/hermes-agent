# Vertical Screen Framing — 9:16 短剧 Framing Rules + Per-Platform Divergence

**Source:** CN 平台 公开 framing 统计(抖音 / 快手 / 小程序剧 / 视频号 2024-2026 user behavior studies);TikTok Creator Academy public guides;YouTube Shorts Creator Academy;Instagram Reels Creative Guidelines;Bordwell & Thompson *Film Art* (11th ed, 2020) for general framing principles adapted to vertical.
**Copyright:** Fair Use — framing rules paraphrased from public creator guides + user behavior studies; no platform-internal documentation verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 cinematographer 专家在 **9:16 vertical 短剧 framing** 决策时的**竖屏侧权威源**(vertical-specific authoritative source)。它涵盖 power points 修正 + headroom 标准 + 字幕 safe area + per-platform divergence(抖音 / 快手 / 小程序剧 / TikTok / YouTube Shorts / Reels)。

它与 [`shot-grammar.md`](./shot-grammar.md)(通用 shot scale + composition)、[`axis-rules.md`](./axis-rules.md)(通用 axis rule)和 [`camera-motion-catalog.md`](./camera-motion-catalog.md)(运动侧)互补,共同构成 cinematographer 决策的四层 grounding — 但本 ref 是 **vertical-only**,不适用于横屏 cinema。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## 9:16 Power Points 修正

### 关键 heuristic 1 (load-bearing): 竖屏 power points 与横屏显著不同

横屏 16:9 power points(标准 rule of thirds):
- (1/3, 1/3) / (2/3, 1/3)
- (1/3, 2/3) / (2/3, 2/3)

竖屏 9:16 power points(基于 mobile viewing distance + 人脸 attention bias):
- **(1/3, 1/4) / (2/3, 1/4)** — **higher eye-line** (主体 eye-line 放在画面 vertical 1/4 位置,不是 1/3)
- **(1/3, 3/4) / (2/3, 3/4)** — **lower body / prop** (主体 body lower 或 关键 prop)

**理由:**
1. **Mobile viewing distance:** 手机观看距离 ~25-30cm(vs 横屏 cinema / TV 3-5m)。近距离观看时,人眼 attention bias 偏向画面中心略偏上。
2. **Vertical center bias:** 9:16 framing 的 vertical center 是 mobile UI safe zone(notification bar / bottom nav),主体必须偏上或偏下避开 safe zone。
3. **Eye contact intimacy:** 竖屏 close-up 模拟"face-to-face 对话"距离,eye-line 偏上模拟"对方眼睛略高于我"的社交 distance。

### 关键 heuristic 2: Per-shot-scale power point 推荐

| Shot Scale | 推荐 power point | 备注 |
|-----------|------------------|------|
| EWS | (1/2, 1/2) center | vertical EWS 主体居中 |
| WS | (1/2, 1/3) upper-center | 站立全身,head 在 1/3 |
| FS | (1/2, 1/3) upper-center | 同 WS,但主体更大 |
| MS | (1/3, 1/4) 或 (2/3, 1/4) | 偏左 / 偏右 eye-line |
| MCU | (1/3, 1/4) 或 (2/3, 1/4) | 偏左 / 偏右(对话场景)|
| CU | (1/2, 1/4) center-upper | 单主体居中 |
| BCU | (1/2, 1/3) | eye 居中 |
| INSERT | (1/2, 1/2) 或 (1/2, 2/3) | 物件居中 |

---

## Headroom 标准

### 关键 heuristic 3: 竖屏 headroom 与横屏显著不同

详见 [`shot-grammar.md`](./shot-grammar.md) §Headroom 标准。竖屏 headroom 普遍小于横屏(5-10% vs 8-15%),原因是 vertical space 受限 + face proximity priority。

### 关键 heuristic 4: 竖屏"haircut" anti-pattern 警告

竖屏 CU / BCU 容易出现"haircut"(主体头顶贴 top edge,看起来像被剪掉头发)。Mitigation:
- CU headroom 至少 2-3%
- BCU headroom 至少 1-2%(除非 narrative 故意 extreme emotion)
- 若 haircut 不可避免(emotion priority),output `haircut_intentional: true` 警告 editor

---

## 字幕 Safe Area

### 关键 heuristic 5 (load-bearing): 9:16 字幕 safe area 5 个区

竖屏 短剧 字幕安全区(基于 mobile UI 研究 + 平台 guideline):

| 区域 | Vertical 位置 | Horizontal 位置 | 用途 | 禁用 |
|------|---------------|-----------------|------|------|
| **Top zone** | 0-15% | 全宽 | 平台 logo / 标题 | 字幕(被 notification bar 遮挡)|
| **Upper-center** | 15-35% | 全宽 | **推荐字幕区 1** | — |
| **Center zone** | 35-65% | 全宽 | 主体 face 区 | 字幕(遮挡 face)|
| **Lower-center** | 65-85% | 全宽 | **推荐字幕区 2** | — |
| **Bottom zone** | 85-100% | 全宽 | 平台 nav / CTA 按钮 | 字幕(被 nav 遮挡)|

**字幕放置标准:** 竖屏字幕优先 **Lower-center zone**(65-85%),避开 face 区(35-65%)。若 face 区有空白(e.g., 上半身 shot),可用 **Upper-center zone**(15-35%)。

### 关键 heuristic 6: Per-platform 字幕 divergence

| 平台 | 字幕默认位置 | 字号(px on 1080×1920)| 字体偏好 | 颜色偏好 |
|------|---------------|----------------------|----------|----------|
| 抖音 | Lower-center (75%)| 24-32 | 思源黑体 Bold | 白 + 黑描边 |
| 快手 | Lower-center (70%)| 22-28 | 思源宋体 | 白 + 红色 highlight |
| 小程序剧 | Lower-center (78%)| 28-36 | 思源黑体 Heavy | 黄色 + 黑描边 |
| 视频号 | Upper-center (25%)| 24-30 | 思源黑体 | 白 + 黑描边 |
| TikTok | Lower-center (75%)| 28-36 | SF Pro / Helvetica Bold | 白 + 黑描边 |
| YouTube Shorts | Lower-center (75%)| 26-32 | Roboto | 白 + 黑描边 |
| Reels | Lower-center (75%)| 28-32 | San Francisco | 白 + 黑描边 |

**关键差异:** 视频号字幕优先 Upper-center(避开视频号 nav bar 在底部);其余平台优先 Lower-center。

---

## Per-Platform Framing Divergence

### 关键 heuristic 7 (load-bearing): 4 大 platform framing divergence

| Platform | 推荐 framing | 避免 | 备注 |
|----------|--------------|------|------|
| **抖音 短剧** | 高 contrast + 高 saturation + close-up emphasis | 长镜头 / dark scenes | 用户 scroll 节奏极快(平均 1.5s 决定是否继续看)|
| **快手 短剧** | 自然光 + 中 close-up + real-feel | 过度 production value | 草根 观众偏好 authentic 感 |
| **小程序剧** | 极快 cut + 高 saturation + cliffhanger emphasis | slow burn | 用户付费观看,要求 emotion density 高 |
| **视频号** | 标准 cinematic + 中 close-up + 文艺偏多 | 网感 overdone | 受众偏 older(35+),偏好 narrative depth |
| **TikTok** | high energy + close-up + 趋势 driven | 文化特定 joke | 全球受众,跨文化 framing |
| **YouTube Shorts** | YouTube-creator 风格 + medium shot | 过度 cinematic | 受众偏 younger YouTube 生态 |
| **Reels** | Instagram aesthetic + soft + curated | raw / unpolished | Instagram aesthetic priority |

### 关键 heuristic 8: 抖音 短剧 framing 3 大铁律

抖音 短剧 因 scroll behavior(用户在 1.5s 内决定是否继续看),framing 必须:

1. **First-frame hook:** 第一帧必须有 high-contrast / high-emotion visual(避免 fade-in / slow establishing)
2. **Face priority:** 主体 face 必须在前 0.5s 出现在画面中(audience attention anchor)
3. **No dead space:** 竖屏 vertical space 紧张,避免 EWS / WS dead space

### 关键 heuristic 9: 小程序剧 framing 3 大铁律

小程序剧 因付费观看(用户已经 commit ¥1-3 / episode),framing 必须:

1. **Cliffhanger framing:** episode 最后 2-3s 必须 close-up + extreme emotion(强制 hook 下一集)
2. **Single-subject priority:** 单主体 shot 占比 ≥70%(避免 wide two-shot 分散 attention)
3. **Insert density:** 关键 prop / 信息 必须 INSERT shot(用户付费想看到 detail)

---

## Vertical Camera Move 修正

### 关键 heuristic 10: 竖屏 camera move 修正

详见 [`camera-motion-catalog.md`](./camera-motion-catalog.md)。竖屏修正:

| Camera Move | 横屏 16:9 适用 | 竖屏 9:16 适用 | 竖屏修正 |
|-------------|----------------|----------------|----------|
| Pan(水平摇)| ✓ | 受限 | 9:16 horizontal pan 主体出 frame 快;慎用 |
| Tilt(垂直摇)| ✓ | ✓✓(优先)| 9:16 vertical tilt 完美利用 vertical frame |
| Dolly(推拉)| ✓ | ✓ | 标准 |
| Tracking(跟随)| ✓ horizontal | ✓ vertical 优先 | 9:16 tracking 优先 vertical(跟随角色上下楼梯)|
| Crane(升降)| ✓ | ✓✓(优先)| 9:16 crane 完美利用 vertical frame |
| Handheld | ✓ | ✓ | 标准 |

**竖屏建议:** 优先 tilt + crane + vertical tracking;慎用 horizontal pan(主体出 frame 太快)。

---

## Vertical Framing JSON Schema

cinematographer 输出 `vertical_framing_intent` 字段:

```json
{
  "vertical_framing_intent": {
    "aspect_ratio": "9:16",
    "power_point": "(1/3, 1/4)",
    "headroom_pct": 5,
    "subtitle_zone": "lower-center",
    "platform_target": "douyin",
    "platform_specific_adjustments": {
      "douyin": {
        "first_frame_hook": true,
        "face_priority_0_5s": true,
        "no_dead_space": true
      }
    },
    "vertical_camera_move_priority": ["tilt", "crane", "vertical_tracking"]
  }
}
```

---

## Anti-Patterns

### 关键 heuristic 11: Vertical framing 6 大 anti-pattern(规避)

1. **Horizontal rule-of-thirds anti-pattern:** 直接套 16:9 power points。**Mitigation:** 强制 vertical power point (1/3, 1/4)。
2. **Haircut BCU anti-pattern:** BCU 主体头顶贴 top edge。**Mitigation:** headroom ≥1-2% 或标注 `haircut_intentional: true`。
3. **Subtitle over face anti-pattern:** 字幕放在 face 区。**Mitigation:** 优先 lower-center zone。
4. **Horizontal pan overuse anti-pattern:** 竖屏 horizontal pan 主体出 frame 快。**Mitigation:** 优先 tilt / crane / vertical tracking。
5. **EWS dead space anti-pattern:** 竖屏 EWS 主体过小,空间 dead。**Mitigation:** EWS 占比 ≤3%。
6. **Platform-agnostic framing anti-pattern:** 同一 framing 直接发布到所有平台。**Mitigation:** per-platform divergence 必须考虑(e.g., 抖音 高饱和 vs 快手 低饱和)。

---

## Glossary

- **Vertical power points:** 9:16 framing 的 power points(1/4 vertical 而非 1/3)。
- **Subtitle safe area:** 字幕可放置区(upper-center 15-35% / lower-center 65-85%)。
- **Haircut:** BCU 主体头顶贴 top edge。
- **Per-platform divergence:** 抖音 / 快手 / 小程序剧 / 视频号 / TikTok / YouTube Shorts / Reels 各自 framing preference。
- **Vertical camera move priority:** tilt / crane / vertical tracking 优先于 horizontal pan。

---

*Generated: 2026-06-15 as part of Phase 4 EXPERT-CINE (cinematographer expert).*
*Source provenance: CN 平台 公开 framing 统计 (2024-2026) / TikTok Creator Academy / YouTube Shorts Creator Academy / Instagram Reels Creative Guidelines / Bordwell & Thompson 2020 — fair use paraphrase + short technical phrases only.*
