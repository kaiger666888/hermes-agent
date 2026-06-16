# MusicGen Workflow — MusicGen-Large + Melody Conditioning + AudioLDM-2

**Source:** Copeland et al. *MusicGen* (Meta, 2023 arXiv:2306.05284);Hermes plugins/audio_gen catalog(2026-06);Meta Audiocraft docs;Hugging Face MusicGen-Large model card;AudioLDM-2 docs (Liu et al. 2023)。
**Copyright:** Fair Use — paraphrased workflow + heuristics; no proprietary model weights verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 composer 专家在 **AI music generation workflow** 决策时的**权威源**。它涵盖 MusicGen-Large model + melody conditioning + 4 mode(text-to-music / melody-to-music / continuation / stereo)+ AudioLDM-2 melody 协议。

## MusicGen-Large 4 Mode

### 关键 heuristic 1 (load-bearing): MusicGen-Large 4 mode

| Mode | 输入 | 输出 | 用途 |
|------|------|------|------|
| **Text-to-music** | text prompt | 30s music | 新 music composition |
| **Melody conditioning** | text + melody audio | 30s music following melody | 现有 melody 改编 |
| **Continuation** | text + audio | extended music | 续写已有 music |
| **Stereo** | text | 30s stereo music | 立体声输出 |

### 关键 heuristic 2: MusicGen generation 参数

| 参数 | 范围 | 默认 | 备注 |
|------|------|------|------|
| model | `facebook/musicgen-large` / `musicgen-melody` | musicgen-large | Hermes 默认 |
| duration_sec | 5-180 | 30 | 短剧 typical 30s per theme |
| temperature | 0.5-1.5 | 1.0 | higher = more variation |
| top_k | 0-1000 | 250 | token sampling |
| top_p | 0.0-1.0 | 0.0 | nucleus sampling |
| guidance_scale | 1.0-5.0 | 3.0 | prompt adherence |
| sample_rate | 32000 Hz | 32000 | MusicGen native |

### 关键 heuristic 3: Melody conditioning 协议

Melody conditioning 允许输入一段 reference melody(典型 5-15s),MusicGen 生成 follow 该 melody 的新 music:

```yaml
# Melody conditioning config
model: facebook/musicgen-melody
melody: asset_library/music_themes/baseline_melody.wav
prompt: |
  cinematic orchestral, building tension, strings + brass + timpani,
  fast tempo 140 BPM, dramatic mood
duration_sec: 30
```

**Use case:**
- Episode theme:统一 melody 但每 episode 不同 arrangement
- Genre cover:existing melody 改编为新 genre
- Character theme:melody 与 character LoRA 同步(per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md))

---

## 与 screenplay / editor 的 handoff

### 关键 heuristic 4: Music tempo + emotion_curve sync

music tempo 必须与 screenplay emotion_curve sync:

| emotion_curve anchor | 推荐 tempo (BPM)| Music mood |
|----------------------|-----------------|------------|
| Hope / 升起 | 100-130 | Major key, uplifting |
| Tension / 紧张 | 130-160 | Minor key, building |
| Climax / 高潮 | 140-180 | Dissonance, intense |
| Sadness / 悲伤 | 60-80 | Minor key, slow |
| Romance / 甜蜜 | 80-110 | Major key, soft |
| Action / 战斗 | 140-180 | Percussion heavy, fast |

### 关键 heuristic 5: Editor cut-point sync

music 必须与 editor cut points sync:

- Music downbeat 与 visual cut 对齐(±1 frame tolerance)
- Music build-up 与 tension escalation scene 对齐
- Music drop / climax 与 爽点 / 卡点 对齐
- Music fade-out 与 scene 结束对齐

详见 [`../editor/references/cn-cutting-rhythm.md`](../editor/references/cn-cutting-rhythm.md) §BGM-driven cut points。

---

## Anti-Patterns

### 关键 heuristic 6: Music gen 5 大 anti-pattern(规避)

1. **No melody reference anti-pattern:** 全 text-to-music,跨 episode 不一致。**Mitigation:** melody conditioning for recurring themes。
2. **Wrong tempo for emotion anti-pattern:** 悲伤场景 160 BPM。**Mitigation:** per heuristic 4 协议。
3. **Music not synced with cuts anti-pattern:** music 与 visual cut 不同步。**Mitigation:** ±1 frame tolerance。
4. **Over-generated duration anti-pattern:** 生成 5min music 但只用 30s。**Mitigation:** per-scene duration。
5. **No emotional arc anti-pattern:** music 无 build-up / drop / climax 结构。**Mitigation:** 5-act structure(build / develop / climax / resolve / outro)。

---

## Glossary

- **MusicGen-Large:** Meta 2023 开源 music gen model。
- **Melody conditioning:** 用 reference melody 引导生成。
- **BPM:** Beats Per Minute,music tempo。
- **Downbeat:** Music 主拍(典型每 4 beat 一次)。
- **5-act structure:** Build / develop / climax / resolve / outro。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-06 (composer RAG uplift).*
*Source provenance: Copeland et al. 2023 MusicGen / Meta Audiocraft / Hugging Face MusicGen-Large / Liu et al. 2023 AudioLDM-2 — fair use paraphrase + short technical phrases only.*
