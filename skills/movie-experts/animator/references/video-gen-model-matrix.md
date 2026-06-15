# Video Gen Model Matrix — 2026 Hermes-Catalog Models + Behavior

**Source:** fal-ai video gen API docs (fal.ai, 2026-06);Hermes plugins/video_gen/fal/xai catalog;Runway Gen-3 Alpha docs;Kling 1.6 docs;Veo 2 docs;Sora 2 system card;LTX Video 2.3 docs;PixVerse v6 docs。
**Copyright:** Fair Use — paraphrased capability matrix; no proprietary model internals verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

> **⚠ Phantom strip note:** 旧 animator SKILL.md 的 `wan2 / wan22 / wan22_video` 是 phantom(per Phase 0 GAP-REPORT + research SUMMARY:Hermes 不部署 Wan family)。Hermes 实际 video gen catalog:`veo3.1` / `kling-v3-4k` / `pixverse-v6` / `ltx-2.3` / `seedance-2.0` / `happy-horse`(via fal)。

## Hermes Video Gen Catalog (2026-06)

### 关键 heuristic 1 (load-bearing): 6 video gen models 能力矩阵

| Model | Provider | 最大时长 | Resolution | 9:16 vertical | Camera move prompt | Character consistency | Cost / 5s clip |
|-------|----------|----------|-----------|---------------|---------------------|----------------------|----------------|
| **veo3.1** | Google (via fal) | 8s | 1080p | ✅ | ✅ 强 | ✅ 强(reference image)| $0.40 |
| **kling-v3-4k** | Kuaishou (via fal) | 10s | 4K | ✅ | ✅ 中(bilingual)| ✅ 中 | $0.70 |
| **pixverse-v6** | PixVerse (via fal) | 8s | 1080p | ✅ | ✅ 中 | ✅ 中 | $0.35 |
| **ltx-2.3** | Lightricks (open weight)| 5s | 768p | ✅ | ✅ 弱 | ✅ 弱 | $0.10(便宜)|
| **seedance-2.0** | ByteDance | 10s | 1080p | ✅ | ✅ 强 | ✅ 强 | $0.50 |
| **happy-horse** | (open weight)| 4s | 720p | ✅ | ❌ 弱 | ❌ 弱 | $0.05(极便宜)|

### 关键 heuristic 2: Per-scene complexity → model 选择

| Scene complexity | 推荐 model | 理由 |
|------------------|-----------|------|
| Simple motion(static + 1 character + plain background)| ltx-2.3 / happy-horse | 成本最低 |
| Standard motion(walking + dialogue + interior)| pixverse-v6 / seedance-2.0 | 性价比 |
| Complex motion(action + multiple characters + dynamic camera)| veo3.1 / kling-v3-4k | quality 最高 |
| Close-up emotion + character ID-critical | veo3.1 | reference image 一致性最强 |
| CN 母语 audience | kling-v3-4k / seedance-2.0 | 中文 prompt 优势 |
| Global audience | veo3.1 / pixverse-v6 | 跨文化 |

### 关键 heuristic 3: Wan family phantom 替换

per research SUMMARY + Phase 0 GAP-REPORT:Hermes 不部署 Wan family。

**替换 mapping:**
- `wan22_video` → `<video_gen_primary>` placeholder + provider matrix reference
- `wan22_video_turbo` → `<video_gen_preview>` placeholder
- 推荐 primary: veo3.1(全球)或 kling-v3-4k(CN)
- 推荐 preview: ltx-2.3(快 + 便宜)

---

## 短剧 Vertical Generation 协议

### 关键 heuristic 4: 9:16 vertical config

```yaml
# 短剧 9:16 production config
aspect_ratio: "9:16"
resolution: "1080×1920"
duration_sec: 5  # 短剧 典型 clip 时长
model: <per-scene-complexity 选>  # per heuristic 2
prompt: |
  [shot scale] [character trigger] [wardrobe] [lighting] [environment]
  [camera move] [duration]
  # Example:
  # MCU skw1 man dark blazer soft window light office dolly_in 5s
seed: <per-scene baseline seed>
```

### 关键 heuristic 5: Multi-clip concatenation 协议

短剧 通常需要 concatenate 多个 5s clips 形成完整 episode。Concatenation 协议:

1. **Clip overlap:** 相邻 clips 0.5s overlap(用于 seam blending)
2. **Seam blending:** RIFE / FILM frame interpolation 隐藏 concatenation 边界
3. **Audio continuous:** audio 跨 seam 必须 continuous(无 audible click)
4. **Character ID re-verify:** 每个 clip 接口处 character ID 必须 ≥0.80 face embedding similarity

---

## Anti-Patterns

### 关键 heuristic 6: Video gen 5 大 anti-pattern(规避)

1. **Phantom Wan family reference anti-pattern:** 引用 wan2 / wan22。**Mitigation:** 用 veo3.1 / kling-v3-4k 等。
2. **Single-model lock-in anti-pattern:** 全用 veo3.1(贵)。**Mitigation:** per-scene complexity 选择。
3. **No I-frame reference anti-pattern:** 无 I-frame 输入,character ID 不稳定。**Mitigation:** drawer 提供 I-frame。
4. **Visible concatenation seam anti-pattern:** clips 直接 concat 无 blending。**Mitigation:** 0.5s overlap + RIFE / FILM。
5. **Wrong model for scene complexity anti-pattern:** happy-horse 用于复杂 action scene。**Mitigation:** per-scene 协议。

---

## Glossary

- **veo3.1:** Google DeepMind 视频 gen model。
- **kling-v3-4k:** Kuaishou 视频 gen model。
- **I-frame:** Initial frame,作为 video gen 输入(由 drawer 生成)。
- **Multi-clip concatenation:** 多个 short clips 拼接成完整 episode。
- **Seam blending:** 隐藏拼接边界的 frame interpolation。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-10 (animator RAG uplift).*
*Source provenance: fal-ai video gen docs (2026-06) / Hermes plugins/video_gen catalog / Runway / Kling / Veo / Sora / LTX / PixVerse docs — fair use paraphrase + short technical phrases only.*
*⚠ Phantom strip: wan2 / wan22 / wan22_video references replaced per Phase 0 GAP-REPORT.*
