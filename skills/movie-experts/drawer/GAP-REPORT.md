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
