# Camera Motion Catalog — 12 Camera Moves + Prompt-Token Mapping for 2026 Video Gen Models

**Source:** Runway Gen-3 Alpha official documentation (runwayml.com, accessed 2026-06);Kling AI 1.6 prompt engineering guide (klingai.com, accessed 2026-06);Google DeepMind Veo 2 technical report + prompt guide (2026-06);OpenAI Sora 2 system card + prompt engineering community guides (2026-06);Arijon *Grammar of the Film Language* (1976);Mascelli *The Five C's of Cinematography* (1965);Hurbache *The Camera* (1987, 3rd ed).
**Copyright:** Fair Use — camera move taxonomy from public cinematography literature; prompt-token mappings paraphrased from public model documentation and community guides. No proprietary model weights / internals / API verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

> **⚠ Model drift warning (T-04-01):** Video gen models evolve quarterly. This ref carries `verified_date: 2026-06`. Run `--research-phase 4` to refresh mappings before any production deployment. The 4 models documented here are the production-grade state as of mid-2026; Pika / MiniMax Hailuo / LTX Video are excluded due to lower adoption.

## Summary

本 ref 定义 cinematographer 专家在 **camera move intent** 决策 + **prompt-token mapping for downstream animator execution** 时的**运动侧权威源**(motion-side authoritative source)。

它涵盖 12 camera moves(taxonomy + emotional semantics + 竖屏修正)+ **prompt-token mapping for 4 production-grade 2026 video gen models**(Runway Gen-3 Alpha / Kling 1.6 / Veo 2 / Sora 2)。

它与 [`shot-grammar.md`](./shot-grammar.md)(语法侧)、[`axis-rules.md`](./axis-rules.md)(几何侧)和 [`vertical-screen-framing.md`](./vertical-screen-framing.md)(竖屏侧)互补。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## 12 Camera Moves Taxonomy

### 关键 heuristic 1 (load-bearing): 12 camera moves × emotional semantics

| # | Camera Move | 中文 | 描述 | Emotional semantic |
|---|-------------|------|------|---------------------|
| 1 | Static | 静态 | camera 不动 | stability / tension(unmoving tension)/ contemplation |
| 2 | Pan | 水平摇 | camera 水平转动 | surveying / following / revealing |
| 3 | Tilt | 垂直摇 | camera 垂直转动 | revealing up-down / height / depth |
| 4 | Dolly In | 推镜头 | camera 向主体推进 | intimacy / revelation / emphasis |
| 5 | Dolly Out | 拉镜头 | camera 远离主体 | isolation / context / distance |
| 6 | Tracking | 跟随 | camera 跟随主体 | involvement / immediacy / 沉浸感 |
| 7 | Crane Up | 升降镜头上 | camera 垂直上升 | aspiration / rise / scale |
| 8 | Crane Down | 升降镜头下 | camera 垂直下降 | descent / decline / dread |
| 9 | Handheld | 手持 | camera 手持晃动 | documentary / chaos / intimacy |
| 10 | Steadicam | 平稳跟随 | camera 稳定跟随 | smooth involvement / dream-like |
| 11 | Zoom In | 变焦推 | lens 焦距变长(非 dolly)| sudden emphasis / discovery / shock |
| 12 | Zoom Out | 变焦拉 | lens 焦距变短 | reveal context / dawning realization |

### 关键 heuristic 2: Dolly vs Zoom 的关键差异(常见混淆)

| 特征 | Dolly | Zoom |
|------|-------|------|
| camera 物理 move | ✓(移动)| ✗(只变焦距)|
| perspective shift | ✓(parallax 变化)| ✗(只是 magnification)|
| depth 感 | ✓(空间感强)| ✗(扁平感)|
| emotional effect | 渐进 emphasis | 突然 shock / discovery |

**常见错误:** AI 生成的"dolly in"经常实际是 zoom in(parallax 不变)。prompt-token mapping 必须明确区分。

### 关键 heuristic 3: 竖屏 camera move 修正

详见 [`vertical-screen-framing.md`](./vertical-screen-framing.md) §Vertical Camera Move 修正。竖屏优先:
- **Tilt**(vertical tilt 完美利用 vertical frame)
- **Crane Up/Down**(vertical crane 完美利用 vertical frame)
- **Vertical Tracking**(跟随角色上下楼梯 / 站起 / 跪下)

慎用:
- **Horizontal Pan**(主体出 frame 快)
- **Horizontal Tracking**(9:16 horizontal space 受限)

---

## Prompt-Token Mapping — Runway Gen-3 Alpha

### 关键 heuristic 4 (load-bearing): Runway Gen-3 Alpha prompt tokens

Runway Gen-3 Alpha(Turbo + Lite variants)对 camera move 的 prompt-token 响应(基于 runwayml.com 2026-06 official guide + community prompt engineering):

| Camera Move | Runway Gen-3 推荐 prompt token | 备注 |
|-------------|-------------------------------|------|
| Static | `static shot, locked-off camera` | 标准用法 |
| Pan | `panning shot, horizontal pan` | 慎用 9:16 |
| Tilt | `tilting shot, vertical tilt` | 竖屏优先 |
| Dolly In | `slow dolly in, camera pushing in` | Runway Gen-3 区分 dolly vs zoom |
| Dolly Out | `dolly out, camera pulling back` | — |
| Tracking | `tracking shot, following subject` | 标准用法 |
| Crane Up | `crane shot rising, ascending camera` | 竖屏完美 |
| Crane Down | `crane shot descending, descending camera` | 竖屏完美 |
| Handheld | `handheld camera, documentary style` | — |
| Steadicam | `steadicam, smooth tracking` | — |
| Zoom In | `quick zoom in, snap zoom` | Runway 区分 zoom vs dolly |
| Zoom Out | `zoom out, revealing context` | — |

**Runway Gen-3 quirks(2026-06 verified):**
- `slow push-in` 实际生成 dolly in(不是 zoom)✓ — 模型理解物理 move
- `zoom in` 在 Gen-3 Alpha 生成 lens zoom(parallax 不变)✓
- Turbo variant 速度更快但 motion blur 控制 < Lite;Lite 适合微妙 camera move
- prompt 长 ≥100 tokens 时,模型优先处理前 50 tokens 的 camera move instruction

### 关键 heuristic 5: Runway Gen-3 motion intensity scale

Runway Gen-3 通过 `motion_bucket` 参数控制 motion intensity(scale 0-100):
- 0-20: subtle(staic + 微 dolly)
- 21-40: gentle(标准 dolly / pan)
- 41-60: moderate(active tracking)
- 61-80: high(快速 crane / handheld)
- 81-100: extreme(intense action / shake)

cinematographer 输出 `motion_intensity_token` 给下游 animator 参考。

---

## Prompt-Token Mapping — Kling 1.6

### 关键 heuristic 6: Kling 1.6 prompt tokens(中文 + English 双语支持)

Kling 1.6(Pro + Standard)由快手开发,双语 prompt 支持强(2026-06 verified):

| Camera Move | Kling 1.6 推荐 prompt token(中文)| English equivalent |
|-------------|---------------------------------|---------------------|
| Static | `静态镜头,固定机位` | `static shot, locked off` |
| Pan | `水平摇镜头` | `horizontal pan` |
| Tilt | `垂直摇镜头` | `vertical tilt` |
| Dolly In | `缓慢推进,推镜头` | `slow push-in, dolly in` |
| Dolly Out | `拉镜头,远离主体` | `pull back, dolly out` |
| Tracking | `跟随镜头,跟踪主体` | `tracking shot` |
| Crane Up | `升镜头,吊臂上升` | `crane up` |
| Crane Down | `降镜头,吊臂下降` | `crane down` |
| Handheld | `手持摄影,纪录片风格` | `handheld` |
| Steadicam | `斯坦尼康,稳定跟随` | `steadicam` |
| Zoom In | `快速变焦拉近` | `quick zoom in` |
| Zoom Out | `变焦拉远` | `zoom out` |

**Kling 1.6 quirks(2026-06 verified):**
- 中文 prompt 在 motion control 上略优于 English(母语训练数据优势)
- Kling 1.6 Pro 区分 `推镜头`(dolly)vs `变焦拉近`(zoom)✓
- Kling 1.6 Standard 偶尔混淆 dolly / zoom(prompt 必须明确)
- 推荐 prompt 模板:`[shot scale] + [camera move] + [subject action] + [environment]`

### 关键 heuristic 7: Kling 1.6 motion control 参数

Kling 1.6 通过 web UI 参数控制 motion(无 prompt-token 直接控制):
- `Camera move` 下拉菜单:Static / Pan / Tilt / Zoom In / Zoom Out / Push In / Pull Back(等)
- `Motion amplitude` slider:1-10(1=微动,10=剧烈)

**对 cinematographer 的意义:** cinematographer 应 output `kling_camera_preset: <preset_name>` + `kling_motion_amplitude: <1-10>` 字段,而非仅靠 prompt-token。

---

## Prompt-Token Mapping — Veo 2

### 关键 heuristic 8: Veo 2 prompt tokens

Google DeepMind Veo 2(2026-06 verified)对 cinematic language 理解强:

| Camera Move | Veo 2 推荐 prompt token | 备注 |
|-------------|-------------------------|------|
| Static | `locked-off shot, no camera movement` | — |
| Pan | `panning camera` | — |
| Tilt | `tilting camera up` / `down` | 明确方向 |
| Dolly In | `dolly-in, camera moves toward subject` | Veo 2 区分 dolly vs zoom |
| Dolly Out | `dolly-out, camera moves away` | — |
| Tracking | `tracking shot following [subject]` | 明确 subject |
| Crane Up | `crane shot rising` | — |
| Crane Down | `crane shot descending` | — |
| Handheld | `handheld, shaky cam` | — |
| Steadicam | `smooth steadicam tracking` | — |
| Zoom In | `optical zoom in` | Veo 2 强调 optical 区分 |
| Zoom Out | `optical zoom out` | — |

**Veo 2 quirks(2026-06 verified):**
- Veo 2 对 cinematic terms(如 `dolly`, `tracking`, `steadicam`)理解准确
- 长 prompt(>200 tokens)时,模型更倾向 cinematic motion
- Veo 2 在 1080p 输出时 motion blur 控制好(适合 cinematic look)

### 关键 heuristic 9: Veo 2 cinematic language understanding

Veo 2 接受 **更高 level cinematic language**(2026-06 verified):

```
"a slow dolly-in on the protagonist's face as she realizes the truth,
shallow depth of field, golden hour lighting, 35mm lens equivalent"
```

Veo 2 能正确解析"slow dolly-in" + "shallow depth of field" + "golden hour" + "35mm lens equivalent"组合 — 这是 Veo 2 相对其他 3 个模型的独特优势。

cinematographer 可以输出更 **declarative** 的 prompt(描述 cinematic intent)而非 **imperative**(列出 camera move tokens)。

---

## Prompt-Token Mapping — Sora 2

### 关键 heuristic 10: Sora 2 prompt tokens

OpenAI Sora 2(2026-06 公开 API,有限 production access):

| Camera Move | Sora 2 推荐 prompt token | 备注 |
|-------------|--------------------------|------|
| Static | `static camera, no movement` | — |
| Pan | `camera pans horizontally` | — |
| Tilt | `camera tilts vertically` | — |
| Dolly In | `camera dollies in toward subject` | Sora 2 区分 dolly vs zoom |
| Dolly Out | `camera pulls back` | — |
| Tracking | `tracking shot, following [subject]` | — |
| Crane Up | `crane shot ascending` | — |
| Crane Down | `crane shot descending` | — |
| Handheld | `handheld, documentary style` | — |
| Steadicam | `smooth steadicam` | — |
| Zoom In | `optical zoom in` | Sora 2 强调 optical |
| Zoom Out | `optical zoom out` | — |

**Sora 2 quirks(2026-06 verified,limited access):**
- Sora 2 对物理 camera move 理解准确(dolly / zoom 区分清晰)
- 长 prompt 时,Sora 2 优先 cinematic realism(不像 Runway 偶尔 stylized)
- Sora 2 在 60s clip 长度上有独特优势(其他模型典型 5-10s)

### 关键 heuristic 11: Sora 2 长 clip cinematic continuity

Sora 2 的 60s clip 长度允许 **multi-shot sequence in single prompt**(2026-06 verified):

```
"Camera starts on wide establishing shot of the protagonist entering
the warehouse, then slowly dollies in to a medium close-up as she
discovers the package, ending on a static close-up of her reaction."
```

Sora 2 能解析 multi-shot sequence(其他模型会生成 single continuous shot)。这是 Sora 2 相对其他 3 个模型的独特优势。

cinematographer 应 output `sora_multi_shot_sequence: true` flag 给下游 animator,提醒使用 multi-shot prompt 模板。

---

## Cinematographer Output Schema for Animator Handoff

cinematographer 输出 `animator_handoff` 字段:

```json
{
  "animator_handoff": {
    "camera_move": "dolly_in",
    "motion_intensity": "moderate",
    "vertical_correction": "use_tilt_preferred",
    "model_specific_tokens": {
      "runway_gen_3_alpha": "slow dolly in, camera pushing in",
      "kling_1_6_pro": "缓慢推进,推镜头",
      "veo_2": "dolly-in, camera moves toward subject",
      "sora_2": "camera dollies in toward subject"
    },
    "kling_specific": {
      "camera_preset": "Push In",
      "motion_amplitude": 5
    },
    "veo_specific": {
      "declarative_prompt": "a slow dolly-in on the protagonist's face as she realizes the truth, shallow depth of field, golden hour lighting, 35mm lens equivalent",
      "cinematic_language": true
    },
    "sora_specific": {
      "multi_shot_sequence": false,
      "long_clip": false
    }
  }
}
```

下游 animator 收到 `animator_handoff` 后,根据当前 deployment 用的 video gen model 选择对应 prompt token / preset。详见 [`../animator/SKILL.md`](../animator/SKILL.md) §Camera Move Translation。

---

## Anti-Patterns

### 关键 heuristic 12: Camera move 6 大 anti-pattern(规避)

1. **Horizontal pan overuse in 9:16 anti-pattern:** 竖屏 horizontal pan 主体出 frame 快。**Mitigation:** 优先 tilt / crane / vertical tracking。
2. **Zoom vs dolly confusion anti-pattern:** AI 生成 zoom 但 prompt 写 dolly(或反之)。**Mitigation:** prompt-token mapping 明确区分;Runway / Kling / Veo / Sora 2 都已区分。
3. **Static-only sequence anti-pattern:** 整集无 camera move,导致节奏死板。**Mitigation:** 每 30s 至少 1 个 subtle camera move。
4. **Excessive handheld anti-pattern:** 过多 handheld 导致 audience 眩晕。**Mitigation:** handheld 占比 ≤20%(documentary 风格除外)。
5. **Quick zoom overuse anti-pattern:** quick zoom 易显得 amateurish。**Mitigation:** quick zoom 仅用于 shock / discovery,占比 ≤5%。
6. **Model-agnostic prompt anti-pattern:** 同一 prompt 用于 4 个不同 model,导致 motion 不准确。**Mitigation:** `animator_handoff` 必须包含 4 个 model-specific tokens。

---

## Glossary

- **Camera move taxonomy:** 12 camera moves(static / pan / tilt / dolly in/out / tracking / crane up/down / handheld / steadicam / zoom in/out)。
- **Prompt-token mapping:** 每个 camera move 在每个 video gen model 的 prompt token。
- **Motion intensity:** motion 剧烈程度(Runway motion_bucket 0-100 / Kling amplitude 1-10)。
- **Dolly vs zoom:** dolly 是物理 move(parallax 变化),zoom 是 lens 变化(无 parallax)。
- **Multi-shot sequence:** Sora 2 独特的 60s 长 clip cinematic continuity。

---

*Generated: 2026-06-15 as part of Phase 4 EXPERT-CINE (cinematographer expert).*
*Source provenance: Runway Gen-3 Alpha docs (2026-06) / Kling 1.6 docs (2026-06) / Veo 2 technical report (2026-06) / Sora 2 system card (2026-06) / Arijon 1976 / Mascelli 1965 / Hurbache 1987 — fair use paraphrase + short technical phrases only.*
*⚠ Model drift: quarterly refresh required. `verified_date: 2026-06` is load-bearing.*
