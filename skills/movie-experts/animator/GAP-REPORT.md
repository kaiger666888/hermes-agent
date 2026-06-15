# GAP-REPORT: animator

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

<!-- Model/tool/sampler/concept names not in plugins/ inventory or known-external-models.yaml -->

- `wan2` at `skills/movie-experts/animator/SKILL.md:3` — description field references "Wan2.2 video generation". `wan2` not in `plugins/video_gen/{fal,xai}` catalog, not in `_shared/known-external-models.yaml`. **Disposition: STRIP** (phantom — Hermes ships `veo3.1`, `kling-v3-4k`, `pixverse-v6`, `ltx-2.3`, `seedance-2.0`, `happy-horse` via fal, not the Wan family).
- `wan22` at `skills/movie-experts/animator/SKILL.md:12` — frontmatter `tags: [..., wan22, ...]`. **Disposition: STRIP** → replace with `video-gen`.
- `wan2` at `skills/movie-experts/animator/SKILL.md:20` — H1 subtitle "Wan2.2 video generation specialist". **Disposition: STRIP** → rewrite to "current video generation models".
- `wan2` at `skills/movie-experts/animator/SKILL.md:46` — H3 header "### Wan2.2 Generation". **Disposition: STRIP** → rewrite to "### Video Generation".
- `wan22_video` at `skills/movie-experts/animator/SKILL.md:47` — `model: wan22_video (primary), wan22_video_turbo (preview only)`. **Disposition: STRIP** → replace with `<video_gen_primary>` / `<video_gen_preview>` placeholders (provider-agnostic per CONTEXT.md).

**Cleanup target:** replace all `wan2`, `wan22`, `wan22_video`, `wan22_video_turbo` tokens with provider-agnostic placeholders or generic descriptors. Hermes' real video gen catalog (veo3.1, kling-v3-4k for 9:16 短剧 vertical; ltx-2.3 / pixverse-v6 cheap tier) goes into `references/video-model-matrix.md` (Phase 5).

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Current video gen model behavior matrix.** Which models (veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3) reliably support 9:16 vertical for 短剧, which support camera motion text prompts (dolly-in, pan, whip), which preserve character consistency across clips. SKILL.md mentions none.
2. **短剧-specific pacing constraints.** Vertical 短剧 typically run 1.5-2x the cut density of horizontal cinema. No mention of this scaling factor.
3. **I-frame-to-clip weight calibration.** SKILL.md gives a single `weight: 0.7-0.9` range but no guidance on when to push toward 0.9 (preserve identity) vs 0.7 (allow motion freedom).
4. **Temporal flicker / morphing detection heuristics.** "No object morphing between frames" is stated as a rule but no detection method or fallback when morphing occurs.
5. **Frame interpolation for slow-motion.** `fps: 16 (slow-motion), 8 (timelapse)` is listed but no interpolation guidance (RIFE / FILM fallbacks when generation produces stuttering at non-native fps).
6. **Multi-clip concatenation artifacts.** SKILL says "concatenate instead" for >6s clips, but no seam-blending protocol to hide concatenation boundaries.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Motion must serve narrative, never distract"** — vague principle with no operational check. No threshold for what counts as "distracting" motion (e.g., angular velocity > X°/s without emotional trigger).
2. **`motion_complexity: 0.3-0.8 range`** — no measurement definition. How is complexity computed? Frame-to-frame optical flow variance? Scene-cut density? A model with no defined measurement cannot be evaluated.
3. **`generation_fidelity: >= 0.80`** — fidelity to what? The I-frame reference? The prompt? Undefined.
4. **"Use dolly-in/out instead of digital zoom"** — correct principle but no prompt-token mapping (which words in the video-gen prompt trigger dolly vs zoom).
5. **`camera_ease: linear, ease_in, ease_out, ease_in_out (default: ease_in_out)`** — no explanation of when linear or ease_in is preferred over the default.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `motion_smoothness` — production minimum >= 0.85. No measurement definition (optical flow jitter? PSNR between interpolated frames? CLIP-temporal?). Cannot be auto-evaluated.
- `motion_complexity` — listed as `0.3-0.8 range`. A "complexity" metric without an algorithmic definition is hand-wavy.
- `temporal_consistency` — >= 0.90. Reasonable target but no canonical metric (CLIP-T? LPIPS between frames? human-evaluated?).

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/video-model-matrix.md` — current (2026-06) video gen model capabilities: vertical support, camera motion support, character consistency, duration limits, VRAM costs. Refreshed quarterly per research PITFALLS.
2. `references/camera-motion-prompt-tokens.md` — mapping from cinematography terms (dolly, whip-pan, crane) to prompt tokens that current models actually understand.
3. `references/i-frame-weight-calibration.md` — heuristic table for I-frame weight selection by shot purpose (establishing, action, reaction, portrait).
4. `references/shortdrama-pacing.md` — vertical 短剧 cut density, shot duration floors (1.5-2x horizontal), no >3s dead air rule per research HOOK requirements.
