# Stanislavski + ExBxSxP Matrix — An Actor Prepares + Laban Effort

**Source:** Stanislavski *An Actor Prepares* (1936, Theatre Arts Books, trans. Elizabeth Hapgood);Stanislavski *Building a Character* (1948, Theatre Arts);Stanislavski *Creating a Role* (1961, Theatre Arts);Laban & Lawrence *Effort* (1947, Macdonald & Evans);Hodge *Twentieth-Century Actor Training* (2010, Routledge)。
**Copyright:** Fair Use — paraphrased methodology; no verbatim chapter content. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

> **⚠ Phantom strip note:** 旧 performer SKILL.md 的 "168K controlled performance tokens" 是 phantom(per Phase 0 GAP-REPORT + research SUMMARY:无任何模型 / 数据集支撑此 claim)。已 strip。

## ExBxSxP Matrix

### 关键 heuristic 1 (load-bearing): ExBxSxP 4 维度 character performance encoding

per SKILL.md §Performance-4D Matrix:

| 维度 | 全名 | 范围 | 用途 |
|------|------|------|------|
| **E (Emotion)** | 情绪 | Ekman 7 basic + mixed | Character 内在情绪 |
| **B (Body)** | 身体 | Laban Effort(Weight × Flow × Space × Time)| Character 身体语言 |
| **S (Space)** | 空间 | Proxemics(Hall intimate/personal/social/public)| Character 与他者 / 环境距离 |
| **P (Prompt)** | Prompt | 文本 prompt token | TTS / animation generation prompt |

### 关键 heuristic 2: Ekman 7 basic emotions + intensity

per Ekman 1971:

| Emotion | Intensity 0.0-1.0 | Facial action |
|---------|-------------------|---------------|
| Neutral | 0.0 | Relax baseline |
| Happy | 0.3 / 0.6 / 1.0 | Smile, eye crinkle |
| Sad | 0.3 / 0.6 / 1.0 | Frown, eye droop |
| Angry | 0.3 / 0.6 / 1.0 | Brow furrow, jaw clench |
| Fearful | 0.3 / 0.6 / 1.0 | Eye wide, brow raise |
| Surprised | 0.3 / 0.6 / 1.0 | Eye wide, mouth open |
| Disgusted | 0.3 / 0.6 / 1.0 | Nose wrinkle, lip curl |
| Contempt | 0.3 / 0.6 / 1.0 | Lip corner asym |

---

## Laban Effort Analysis

### 关键 heuristic 3 (load-bearing): Laban Effort 4 因子

per Laban & Lawrence 1947:

| 因子 | 范围 | 描述 |
|------|------|------|
| **Weight** | Strong / Light | 力度感 |
| **Flow** | Bound / Free | 流动感(紧张 vs 自由)|
| **Space** | Direct / Indirect | 空间感(直接 vs 间接)|
| **Time** | Sudden / Sustained | 时间感(突发 vs 持续)|

8 种 Effort 组合:

| Weight | Flow | Space | Time | Character 示例 |
|--------|------|-------|------|----------------|
| Strong | Bound | Direct | Sudden | Punch(暴力)|
| Strong | Bound | Direct | Sustained | Press(坚定)|
| Strong | Free | Direct | Sudden | Slash(攻击)|
| Strong | Free | Indirect | Sustained | Wring(挣扎)|
| Light | Bound | Direct | Sustained | Glide(优雅)|
| Light | Bound | Indirect | Sustained | Float(飘逸)|
| Light | Free | Direct | Sudden | Dab(轻点)|
| Light | Free | Indirect | Sustained | Flick(轻拂)|

### 关键 heuristic 4: ExB (Emotion × Body) 联动协议

| Emotion | 推荐 Laban Effort |
|---------|-------------------|
| Happy | Light / Free / Direct or Indirect / Sustained |
| Sad | Light / Bound / Indirect / Sustained |
| Angry | Strong / Bound / Direct / Sudden |
| Fearful | Light / Bound / Indirect / Sudden |
| Surprised | Light / Free / Direct / Sudden |
| Disgusted | Strong / Bound / Indirect / Sudden |
| Contempt | Light / Bound / Direct / Sustained |

---

## Stanislavski 6 Questions

### 关键 heuristic 5: Stanislavski character analysis 6 questions

per *An Actor Prepares* 1936,每个 character 必须回答:

1. **Who am I?** — Character identity(background, age, gender, occupation)
2. **Where am I?** — Scene environment(physical + social)
3. **When is it?** — Time period + time of day + season
4. **What do I want?** — Super-objective + scene objective
5. **Why do I want it?** — Motivation root cause
6. **How will I get it?** — Action strategy(obstacle + tactic)

### 关键 heuristic 6: Super-objective + scene objective hierarchy

- **Super-objective:** 全剧 character 总目标(e.g., "复仇")
- **Act objective:** 每 act 子目标(e.g., "收集证据")
- **Scene objective:** 每 scene 子目标(e.g., "说服证人")
- **Beat objective:** 每 beat 子目标(e.g., "建立信任")

---

## Anti-Patterns

### 关键 heuristic 7: Performance 5 大 anti-pattern

1. **Phantom token claim anti-pattern:** "168K controlled performance tokens"。**Mitigation:** strip phantom。
2. **Wrong Laban Effort for emotion anti-pattern:** Angry 用 Light / Bound。**Mitigation:** per heuristic 4 协议。
3. **No scene objective anti-pattern:** Character 无明确 scene objective。**Mitigation:** Stanislavski 6 questions。
4. **Emotion intensity extreme anti-pattern:** 每场景 emotion intensity = 1.0。**Mitigation:** 大多场景 0.3-0.6。
5. **No cross-shot performance consistency anti-pattern:** 同 character 跨 shot 行为不一致。**Mitigation:** ExBxSxP matrix σ ≤ 0.10。

---

## Glossary

- **ExBxSxP:** Emotion × Body × Space × Prompt 4-dim matrix。
- **Ekman 7:** 7 basic emotions(per Ekman 1971)。
- **Laban Effort:** Weight × Flow × Space × Time movement analysis。
- **Super-objective:** Stanislavski character 全剧总目标。
- **Proxemics:** Edward T. Hall 4 个 social distance(intimate / personal / social / public)。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-07 (performer RAG uplift).*
*Source provenance: Stanislavski 1936/1948/1961 / Laban & Lawrence 1947 / Hodge 2010 — fair use paraphrase + short technical phrases only.*
*⚠ Phantom strip: 168K controlled tokens claim stripped per Phase 0 GAP-REPORT.*
