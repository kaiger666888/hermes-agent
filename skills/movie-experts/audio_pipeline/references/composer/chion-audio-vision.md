# Chion Audio-Vision — Acousmatic + 5 Modes + Audio-Vision Analysis

**Source:** Michel Chion *Audio-Vision: Sound on Screen* (1994, Columbia UP, translated by Claudia Gorbman);Chion *The Voice in Cinema* (1999, Columbia UP);Hickman *Reel Music: Exploring 100 Years of Film Music* (2022 update);Mervic Cooke *A History of Film Music* (2008, Cambridge UP)。
**Copyright:** Fair Use — paraphrased theoretical framework + heuristics; no verbatim quotation beyond short technical phrases. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 composer 专家在 **audio-vision(声音与画面的关系)** 决策时的**理论侧权威源**。它涵盖 Chion acousmatic concept + 5 audio-vision modes + audio-vision 分析协议。

## Chion's 5 Audio-Vision Modes

### 关键 heuristic 1 (load-bearing): Chion 5 种 sound-image relationship

| Mode | 描述 | 典型用例 |
|------|------|----------|
| **1. Empirical sound** | 同步出现的 sound + image(脚步声 + 走路)| 标准 diegetic SFX |
| **2. Adding value** | Sound 赋予 image 新意义(沉默 + face = 内心独白)| Emotional amplification |
| **3. Rendered sound** | Sound 不是物体本身,而是印象(心跳声放大 = 紧张)| Symbolic representation |
| **4. Psycho-analytic** | Sound 暗示 character 心理状态(童年音乐 + 现实场景 = 闪回)| Psychological narrative |
| **5. Acousmatic** | Sound 来源未显示(画外音 / 隐藏 source)| Mystery / 悬疑 |

### 关键 heuristic 2: Acousmatic concept 详解

**Acousmatic**(Chion 借用自 Pierre Schaeffer):听到声音但看不到声源。

**Acousmatic 用例:**
- Mystery character 画外音(隐藏 boss 声音)
- Threat 声音(monster footsteps approaching but unseen)
- Power dynamic(老师画外训斥 + 学生 close-up reaction)
- Revelation build-up(钥匙开门声先于门开)

**Acousmatic 设计协议:**
- Sound 持续 2-5s 后再 reveal source(build tension)
- Sound 越具体(revealed source 越易猜),acousmatic 效果越弱
- Acousmatic + close-up reaction shot 是经典组合

---

## Audio-Vision Analysis Protocol

### 关键 heuristic 3: Per-scene audio-vision analysis

每个 scene 必须 specify audio-vision mode(per Chion):

```yaml
# Audio-vision analysis example
scene_id: S01E01_scene_003
audio_vision_modes:
  - mode: empirical
    sound: footstep on hardwood
    timing: 0:00-0:05
    purpose: 标准环境 grounding
  - mode: adding_value
    sound: clock ticking
    timing: 0:05-0:15
    purpose: tension amplification(character 焦虑)
  - mode: acousmatic
    sound: muffled voice from hallway
    timing: 0:15-0:20
    purpose: mystery setup(revealed in next scene)
```

### 关键 heuristic 4: 5 modes 与 emotion_curve 联动

| emotion | 推荐 audio-vision mode |
|---------|------------------------|
| Anticipation | Acousmatic(build-up)|
| Fear / Tension | Acousmatic + Psycho-analytic |
| Sadness / Loss | Adding value(silence + face)|
| Joy / Hope | Empirical + Rendered |
| Anger | Empirical + Adding value |
| Surprise | Acousmatic + Rendered |

---

## 与 foley / mixer 协作

### 关键 heuristic 5: Composer vs Foley vs Mixer 边界

- **composer:** Music(score / BGM)决策
- **foley:** Physical SFX(footstep / door / prop)决策
- **mixer:** Final levels / EQ / ducking

但 audio-vision mode 决策是 composer 的职责(决定 music vs SFX vs silence 在某 scene 的分配)。

### 关键 heuristic 6: Silence as design choice

Chion 强调 **silence** 是一种 audio-vision mode(不是 music / SFX 的缺席,而是设计选择):

- **Tension silence:** 重要 narrative beat 前的 1-2s 静默(build anticipation)
- **Emotional silence:** 角色失去 / 悲伤时的静默(adding value)
- **Diegetic silence:** 角色进入 vacuum / deafness 的场景(special effect)

**Silence 用法:**
- 短剧 silence 时长 ≤ 3s(避免观众上滑)
- Silence 后必须紧跟 强 hook / drop / climax
- Silence 不能连续出现(连续 silence = dead air,观众流失)

---

## Anti-Patterns

### 关键 heuristic 7: Audio-vision 5 大 anti-pattern(规避)

1. **Music-only anti-pattern:** 全 music 无 SFX,缺乏 grounding。**Mitigation:** 5 modes 平衡。
2. **No acousmatic anti-pattern:** 全 empirical sound,无 mystery。**Mitigation:** 关键 scene 用 acousmatic。
3. **No silence anti-pattern:** 全程 sound,无 breathing room。**Mitigation:** Silence as design。
4. **Music overpowering dialogue anti-pattern:** music 太响盖过 dialogue。**Mitigation:** Dialogue ducking per mixer。
5. **Mismatched audio-vision mode anti-pattern:** 错用 mode(e.g., joy scene 用 acousmatic)。**Mitigation:** per heuristic 4 协议。

---

## Glossary

- **Acousmatic:** 听到声音但看不到声源(Chion 借用 Schaeffer)。
- **Adding value:** Sound 赋予 image 新意义。
- **Rendered sound:** Sound 是物体印象,不是物体本身。
- **Empirical sound:** 同步 sound + image。
- **Diegetic:** 角色听得到的 sound(对话 / 环境 / SFX);non-diegetic = 角色听不到(score / VO)。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-06 (composer RAG uplift).*
*Source provenance: Chion 1994 Audio-Vision / Chion 1999 Voice in Cinema / Hickman 2022 Reel Music / Cooke 2008 History of Film Music — fair use paraphrase + short technical phrases only.*
