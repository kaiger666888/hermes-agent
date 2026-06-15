# Axis Rules — 180° Axis + 30° Rule + Screen Direction for 短剧

**Source:** Arijon *Grammar of the Film Language* (1976); Mascelli *The Five C's of Cinematography* (1965); Bordwell & Thompson *Film Art* (11th ed, 2020); Reisz & Millar *The Technique of Film Editing* (2nd ed, 1968); Dmytryk *On Film Editing* (1984).
**Copyright:** Fair Use — axis rules + screen direction doctrine paraphrased; no verbatim quotation beyond short technical phrases. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 cinematographer 专家在 **镜头轴系(axis)与画面方向(screen direction)** 决策时的**几何侧权威源**(geometric-side authoritative source)。它涵盖 180° axis rule + 30° rule + screen direction continuity + reverse-cut 协议 + cross-cutting 密度。

它与 [`shot-grammar.md`](./shot-grammar.md)(语法侧:shot scale + composition)、[`vertical-screen-framing.md`](./vertical-screen-framing.md)(竖屏侧:9:16 framing)和 [`camera-motion-catalog.md`](./camera-motion-catalog.md)(运动侧)互补。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## 180° Axis Rule

### 关键 heuristic 1 (load-bearing): 180° axis 维护 spatial consistency

**核心规则(Mascelli §Camera Angles):** 两个 character 之间的对话 / 互动建立了一条 **invisible axis line**(imaginary line connecting the two characters)。所有 subsequent shots 必须 keep camera on **同一侧** of this line。

**为什么?** 如果一个 shot 从 axis 的左侧拍(让 A 在画面左侧),下一个 shot 跨越 axis 到右侧(让 A 在画面右侧),audience 的 spatial understanding 会 break — 看起来 A 和 B 突然交换了位置。

**操作化:** cinematographer 必须 output `axis_line` 字段标识 axis 方向(e.g., "+X (L2R)" 表示 axis 沿 +X 方向,camera 在 axis 北侧)。下游 editor 在 cross-cut 时必须 verify axis 维持。

### 关键 heuristic 2: 180° axis 违反的 4 个合法例外

axis rule 不是绝对的;以下 4 种情况允许 crossing the line:

1. **Camera move during shot:** camera 在 shot 内部缓缓 move across the line,观众通过 motion 感知到方向变化。
2. **Establishing shot re-anchor:** 一个 EWS 重新 establish spatial relationship,新的 axis 在新 shot 中重新定义。
3. **Cut to insert / detail shot:** INSERT shot 没有 character 互动,axis rule 不适用。
4. **Trisection transition:** 通过一个中间 shot(三方对话场景的中立 angle)过渡到 axis 的另一侧。

** cinematographer output:** 当违反 axis 时,必须在 `shot_intent.json` 中标注 `axis_crossing: true` + `crossing_reason: <reason>`,以警告 editor 不要在 cross-cut 中混淆。

### 关键 heuristic 3: 竖屏 9:16 axis rule 修正

竖屏 framing 下,axis rule **依然适用**,但有 2 个修正:

1. **Vertical blocking 强化:** 9:16 frame 限制 horizontal blocking,axis 优先 vertical(角色上下站立,而非左右)。常见场景:楼梯对话 / 站立 vs 坐姿 / 阳台向下看。
2. **OTS axis swap 警告:** 9:16 OTS 的 foreground shoulder 占用画面 30-40%,axis crossing 比 16:9 更显眼。建议竖屏 OTS 严格保持 axis。

---

## 30° Rule

### 关键 heuristic 4 (load-bearing): 30° rule 防 jump cut

**核心规则:** 同一主体的两个 consecutive shot,camera angle 必须相差 **至少 30°**(或 focal length 相差至少 25mm,即"25mm / 30° rule")。

**为什么?** 两个 angle 太近的 shot 切在一起会看起来像画面"跳了一下"(jump cut)。观众感知到画面错位,但无法解释为什么。

**操作化:** cinematographer 必须确保同主体的连续 shots angle 差 ≥30°,或 shot scale 差至少一级(e.g., MCU → CU)。

### 关键 heuristic 5: 30° rule 在 close-up 中的强化

| Shot Scale | 推荐 angle 差 | 备注 |
|-----------|---------------|------|
| WS / FS | 30° | 标准 |
| MS | 30-45° | 强化 differentiation |
| MCU | 45-60° | close-up 范围 angle 差更显眼 |
| CU / BCU | 60-90° | 极端 close-up 需要大 angle 差 |

---

## Screen Direction Continuity

### 关键 heuristic 6 (load-bearing): Screen direction 4 种状态

character / vehicle / camera 的 screen direction 必须在 scene 内保持一致。4 种状态:

| Direction | 表示 | narrative 含义 |
|-----------|------|----------------|
| L2R (Left-to-Right) | 主体从画面左 → 右移动 | progress / forward / goal-seeking |
| R2L (Right-to-Left) | 主体从画面右 → 左移动 | return / backward / retreat |
| Up (vertical up) | 主体向上移动 | aspiration / rise / hope |
| Down (vertical down) | 主体向下移动 | fall / decline / despair |

**关键规则:** 同一 character 在同一 scene 内 direction 必须一致(除非 narrative 故意 shift — e.g., 角色从 progress 变成 retreat)。

### 关键 heuristic 7: Character A vs Character B 的 opposing direction

对话 / 对峙场景中,A 和 B 的 direction 必须 opposite:
- A 朝 L2R 看(向 B 的方向)
- B 朝 R2L 看(向 A 的方向)

如果两个 character 都朝同一方向看,audience 会感知不到他们在互动。这是最常见的 axis rule 违反衍生错误。

---

## Reverse Cut Protocol

### 关键 heuristic 8: Reverse cut 标准 coverage

对话场景的 reverse cut(切换到对面 character 的反应)标准协议:

1. **Setup:** MS two-shot establish axis + spatial relationship
2. **First OTS:** 从 A 肩后看 B(B 在画面右侧 speaking)
3. **Reverse OTS:** 从 B 肩后看 A(A 在画面左侧 speaking)— **必须保持 axis**
4. **Singles (可选):** MCU 单独 shot A 或 B(emphasis)
5. **Inserts (可选):** 关键 prop / 手势

**节奏标准(基于 Cinemetrics 短剧 ASL 1.2-2.0s):** 一个 30s 对话场景典型 15-25 个 shot,即每 shot 1.2-2.0s。

### 关键 heuristic 9: Reaction shot priority

短剧 观众 emotion-driven,反应 shot 比 speaking shot 更重要。Coverage protocol:

- **Speaking character on-screen:** ~40% screen time
- **Listening character reaction:** ~50% screen time(**reaction emphasis**)
- **Two-shot / inserts:** ~10% screen time

这个 distribution 与横屏 cinema 不同(横屏 speaking ~60% / reaction ~30%)。

---

## Cross-Cutting Density

### 关键 heuristic 10: Cross-cut 协议与密度

cross-cut(在两个 simultaneous 场景之间切换)标准协议:

1. **Establish both scenes first:** 观众必须先看到两个场景的 spatial relationship
2. **Cross-cut rhythm:** 4-8s per scene segment(让观众"跟踪"双方)
3. **Climax convergence:** cross-cut 节奏逐渐 accelerate,直到两个场景 converge(经典 case:英雄赶赴 + 反派行动 converge)

**短剧 cross-cut 密度:** 短剧 ASL 1.2-2.0s 意味着 cross-cut 节奏更快;典型 8-12s cycle(每个 scene segment 4-6s)。

### 关键 heuristic 11: Cross-cut 与 axis rule 的交互

cross-cut 两个 simultaneous 场景时,每个场景有自己的 axis。但两个场景的 screen direction **必须 consistent**(避免 audience 混淆):e.g., 英雄赶赴场景 L2R + 反派行动场景也 L2R,表示两个事件"向同一目标前进"。

---

## Editor Handoff Schema

cinematographer 输出 `editor_handoff` 字段(per `shot_intent.json`):

```json
{
  "editor_handoff": {
    "axis_line": "+X (L2R)",
    "axis_side": "north",
    "screen_direction": "L2R",
    "compliance_required": [
      "verify 180° axis on next cut",
      "verify 30° rule if same subject",
      "verify screen direction continuity"
    ],
    "axis_crossing": false,
    "crossing_reason": null
  }
}
```

editor 收到 shot_intent 后,在 cross-cut / sequence edit 时 verify axis + 30° rule + screen direction continuity。详见 [`../editor/references/fxrxt-axis-compliance.md`](../editor/references/fxrxt-axis-compliance.md)。

---

## Anti-Patterns

### 关键 heuristic 12: Axis rule 5 大 anti-pattern(规避)

1. **Crossing the line without motivation anti-pattern:** 随意跨 axis 导致 audience 混淆。**Mitigation:** 必须有合法例外(camera move / EWS re-anchor / insert / trisection)。
2. **<30° jump cut anti-pattern:** 连续 shot angle 差 <30°,导致 jump cut。**Mitigation:** 强制 ≥30° rule,close-up 范围强化到 60-90°。
3. **Both characters looking same direction anti-pattern:** A 和 B 都看 L2R,audience 不感知互动。**Mitigation:** opposing direction required for dialogue coverage。
4. **Screen direction flip mid-scene anti-pattern:** 角色在 scene 内突然 direction flip 无 narrative motivation。**Mitigation:** 必须有 narrative beat 触发 direction shift(e.g., 角色从 progress 变成 retreat)。
5. **Cross-cut axis mismatch anti-pattern:** cross-cut 两个场景 screen direction opposite,audience 混淆。**Mitigation:** cross-cut scenes 必须 direction consistent。

---

## Glossary

- **180° axis rule:** 同一 axis line 的 camera 必须保持同一侧。
- **30° rule:** 同主体连续 shot angle 差 ≥30°(或 25mm focal length 差)。
- **Screen direction:** character / vehicle / camera 移动方向;L2R / R2L / Up / Down。
- **Reverse cut:** 切换到对面 character 的反应 shot。
- **Cross-cut:** 在两个 simultaneous 场景之间切换。

---

*Generated: 2026-06-15 as part of Phase 4 EXPERT-CINE (cinematographer expert).*
*Source provenance: Arijon 1976 / Mascelli 1965 / Bordwell & Thompson 2020 / Reisz & Millar 1968 / Dmytryk 1984 — fair use paraphrase + short technical phrases only.*
