# Eyeline Match + 180° Continuity Protocol

**Source:** Reisz & Millar *Technique of Film Editing* (1968);Dmytryk *On Film Editing* (1984);Bordwell & Thompson *Film Art* (2020);Mascelli *Five C's of Cinematography* (1965);Arijon *Grammar of the Film Language* (1976)。
**Copyright:** Fair Use — paraphrased heuristics. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 continuity 专家在 **eyeline match + 180° axis continuity** 验证时的**权威源**。它涵盖 eyeline match protocol + screen direction continuity + axis verification across cuts。

## Eyeline Match Protocol

### 关键 heuristic 1 (load-bearing): Eyeline match 3 rule

1. **Look direction matches off-screen target:** Character 看 L2R → target 在画面右侧(off-screen)
2. **Eye height matches target height:** Character 看上方 → target 在画面上方(off-screen higher)
3. **Eye level vs target level:** Character MCU eye-level → target MCU eye-level(不可 mismatch CU vs EWS)

### 关键 heuristic 2: Eyeline mismatch 案例

| 错误 | 描述 | 修正 |
|------|------|------|
| Look direction wrong | Character 看 L2R 但 target 在画面左 | Reverse one shot |
| Eye height wrong | Character 看上方但 target 是 child | Adjust target to higher position |
| Shot scale mismatch | Character MCU + target EWS | Use matching shot scale |
| Angle mismatch | Character 30° angle + target 60° angle | Align angles |

---

## 180° Axis Continuity Across Cuts

### 关键 heuristic 3: Cross-cut axis verification

per [`../cinematographer/references/axis-rules.md`](../cinematographer/references/axis-rules.md):

每个 cut 必须 verify:
- `axis_line` 字段 consistent within scene
- `screen_direction` consistent(unless narrative motivation)
- `axis_crossing` flag = true if exception applies

### 关键 heuristic 4: Cross-scene axis reset protocol

跨场景时 axis 可以 reset:
- 用 EWS re-establish spatial relationship
- 新 scene 新 axis(无 obligation 跟上 scene axis)
- Cut to INSERT shot(axis 不适用)

---

## Screen Direction Continuity

### 关键 heuristic 5: Screen direction 4 状态 audit

| Direction | Within-scene 规则 | Cross-scene 规则 |
|-----------|------------------|------------------|
| L2R | 主体 direction consistent | 新 scene 可 reset |
| R2L | 主体 direction consistent | 新 scene 可 reset |
| Up | 同上 | 同上 |
| Down | 同上 | 同上 |

**Narrative motivation 例外:**
- 角色从 progress 变 retreat → direction shift 有 motivation
- Time cut 跨日夜 → direction 可 reset

---

## Audit Integration

### 关键 heuristic 6: 与 cross-shot-auditing.md 集成

eyeline + axis + screen direction audit 与 face/wardrobe/color/object audit 并行:

```json
{
  "continuity_audit": {
    "spatial": {
      "axis_compliance": true,
      "eyeline_match": true,
      "screen_direction": true
    },
    "visual": {
      "face_consistency": true,
      "wardrobe_consistency": true,
      "color_consistency": true,
      "object_consistency": true
    }
  }
}
```

---

## Anti-Patterns

### 关键 heuristic 7: Eyeline/axis 5 大 anti-pattern

1. **Eyeline mismatch anti-pattern:** Character 看错方向。**Mitigation:** eyeline match 3 rule。
2. **Axis crossing without exception anti-pattern:** 跨 axis 无合法例外。**Mitigation:** 4 legal exceptions。
3. **Screen direction flip mid-scene anti-pattern:** 同 scene 内 direction flip 无 motivation。**Mitigation:** consistency 规则。
4. **Shot scale mismatch anti-pattern:** Eyeline match 但 shot scale 不同。**Mitigation:** matching shot scale。
5. **No axis_line field anti-pattern:** shot_intent 无 axis_line 字段。**Mitigation:** cinematographer 协议。

---

## Glossary

- **Eyeline match:** Character 视线对应 off-screen target。
- **180° axis:** 同场景 camera 保持同一侧 of axis line。
- **Screen direction:** 主体移动方向(L2R / R2L / Up / Down)。
- **Axis crossing:** 跨 axis line(4 legal exceptions)。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-02 (continuity RAG uplift).*
*Source provenance: Reisz & Millar 1968 / Dmytryk 1984 / Bordwell 2020 / Mascelli 1965 / Arijon 1976 — fair use paraphrase + short technical phrases only.*
