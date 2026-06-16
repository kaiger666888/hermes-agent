# Visual Executor GAP-REPORT

**Consolidated from:** drawer (GAP-REPORT audited 2026-06-15) + animator (GAP-REPORT audited 2026-06-15)
**Merge date:** 2026-06-17 (Phase 14 MERGE-01)
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

> Both predecessor GAP-REPORTs are migrated verbatim below as historical provenance. The drawer + animator sub-steps under `visual_executor/` inherit these gap records; future audit runs against `visual_executor/SKILL.md` will supersede this consolidated file.

## Drawer GAP-REPORT (migrated)

# GAP-REPORT: drawer

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

<!-- Model/tool/sampler/concept names not in plugins/ inventory or known-external-models.yaml -->

- `flux` at `skills/movie-experts/drawer/SKILL.md:3` — description references "FLUX/LoRA parameter optimization". `flux` (bare family name) is not in `_shared/known-external-models.yaml` — only `flux2` and `flux_2` are. **Disposition: ALLOWLIST** — `flux` is the legitimate family name covering FLUX 1.x and FLUX 2; bare token is acceptable context reference. Add `flux` to allowlist.
- `flux` at `skills/movie-experts/drawer/SKILL.md:12` — frontmatter `tags: [..., flux, ...]`. **Disposition: ALLOWLIST** (same as above).
- `flux` at `skills/movie-experts/drawer/SKILL.md:20` — H1 subtitle "FLUX/LoRA parameter optimization specialist". **Disposition: ALLOWLIST**.
- `flux` at `skills/movie-experts/drawer/SKILL.md:34` — Core Capabilities bullet. **Disposition: ALLOWLIST**.
- `flux` at `skills/movie-experts/drawer/SKILL.md:48` — H3 "### FLUX Generation". **Disposition: ALLOWLIST**.
- `flux` at `skills/movie-experts/drawer/SKILL.md:84` — Workflow step. **Disposition: ALLOWLIST**.

**Cleanup target:** add `flux` to `_shared/known-external-models.yaml` as a legitimate family shorthand. Real cleanup needed for sampler names below.

**Additional stale-sampler issue (not detected by regex, surfaced manually):** SKILL.md `### FLUX Generation` lists `sampler: euler_a (default), dpmpp_2m (detail)` and `cfg: 3.5-5.0`. These are **FLUX 1.x / SDXL-era sampler parameters** superseded by FLUX 2 (research SUMMARY §"What NOT to use"). FLUX 2 (Hermes default `fal-ai/flux-2/klein/9b`) does not expose `euler_a` / `dpmpp_2m` / `cfg` — it uses guidance-distill parameters. The sampler block is stale and needs rewriting in Phase 5 to match FLUX 2's actual parameter surface.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **FLUX 2 actual parameter surface.** Hermes ships `fal-ai/flux-2/klein/9b` (FLUX 2 Klein 9B) and `fal-ai/flux-2-pro`. Parameter surface differs from FLUX 1.x (no `euler_a`, no `dpmpp_2m`, no LoRA workflow the same way). SKILL.md parameters are stale.
2. **Character consistency across multi-shot sequences.** "Character LoRA: weight 0.6-0.8" assumes a LoRA-per-character workflow. FLUX 2 / Z-Image / Nano Banana use reference-image conditioning, not LoRA. No reference-image guidance.
3. **短剧 vertical composition rules.** 9:16 aspect ratio with platform UI overlay safe-zones (抖音 caption strip, like-button zone, share-button zone). No safe-zone guidance.
4. **Image gen model selection matrix.** FLUX 2 vs Z-Image Turbo (fastest) vs Nano Banana Pro vs gpt-image-2 vs Recraft v3 — each has different strengths. No decision matrix.
5. **CN audience aesthetic preferences.** 短剧 audience aesthetic differs from Western cinema (smoother skin, brighter exposure, more saturated colors). No CN-tuned aesthetic guidance.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Real cinema aesthetic over stylized/2D looks"** — vague. No criteria for what counts as "real cinema" (film grain density? dynamic range? lens characteristics?).
2. **"Parameter precision over trial-and-error"** — principle stated but no parameter-decision tree provided.
3. **`aesthetic_score: >= 8.0`** — score on what scale? CLIP-aesthetic? LAION aesthetic predictor? Human-rated? Undefined.
4. **`film_realism: >= 8.0`** — same issue, undefined metric.
5. **`vram_efficiency: >= 0.7`** — efficiency measured how? Peak VRAM / available VRAM? Undefined.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `aesthetic_score` — >= 8.0. No measurement protocol.
- `character_consistency` — >= 0.85. Probably ArcFace/CLIP-based but not stated.
- `film_realism` — >= 8.0. No measurement protocol.
- `vram_efficiency` — >= 0.7. No formula.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/flux2-parameter-surface.md` — actual FLUX 2 / Klein 9B / FLUX 2 Pro parameters (replaces stale euler_a/dpmpp_2m/cfg block). Refreshed quarterly.
2. `references/image-model-matrix.md` — FLUX 2 vs Z-Image vs Nano Banana Pro vs gpt-image-2 vs Recraft v3 selection matrix with strengths, costs, vertical support.
3. `references/character-consistency-protocols.md` — reference-image conditioning workflow (FLUX 2), LoRA workflow (where still applicable), face-similarity feedback loop with continuity.
4. `references/vertical-safe-zones.md` — 9:16 platform UI overlay safe-zones for 抖音/快手/视频号/B站.

## Animator GAP-REPORT (migrated)

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
