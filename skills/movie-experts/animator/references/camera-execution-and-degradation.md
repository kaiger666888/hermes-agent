# Camera Execution and Degradation Strategy (运镜执行与降级策略)

**Source:** Adapted from OpenClaw kais-camera (Seedance async + 4-level degradation) + kais-shooting-script (storyboard → video params) + kais-evolink (Seedance 1.5 Pro integration).
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Operational methodology for executing Storyboard shots as video segments, including: prompt engineering for video-gen models, 4-level degradation strategy when primary engine fails, and async batch processing patterns. Complements [`./video-gen-model-matrix.md`](./video-gen-model-matrix.md) (engine specs) and [`./temporal-consistency.md`](./temporal-consistency.md) (cross-frame coherence).

## Heuristics

### Storyboard shot → video-gen prompt

For each shot in a Storyboard (per [`../../storyboard_designer/SKILL.md`](../../storyboard_designer/SKILL.md)):

**Prompt assembly:**
```
{STYLE_CORE} {STYLE_IDENTITY} {STYLE_VARIANCE},
{shot.action},
{shot.camera.angle} {shot.camera.movement},
{shot.camera.lens} lens,
{shot.anchoring.lighting.mood} lighting,
{shot.anchoring.temporal.motion_type} at {shot.anchoring.temporal.motion_speed} speed,
duration: {shot.duration}s, fps: {shot.anchoring.temporal.fps}
```

**Character identity injection:**
- For each character_ref in shot: prepend character anchor images (per [`../../character_designer/references/4d-anchor-system.md`](../../character_designer/references/4d-anchor-system.md))
- Priority order: three_quarter > front > side > back

**Reference image injection:**
- `reference_image` (sketch): used as ControlNet input (composition control)
- `render_image` (final still): used as IP-Adapter input (visual identity)
- `end_frame` (from prior shot): used for extension-chain continuity

### 4-level degradation strategy

When the primary video-gen engine fails or produces low-quality output, degrade through 4 levels:

#### Level 1: Primary engine, retry with adjusted parameters

**Trigger:** primary engine returns error OR quality score < threshold
**Action:**
- Increase `inference_steps` (+10)
- Adjust `guidance_scale` (±0.5)
- Re-attempt

#### Level 2: Primary engine, simplified prompt

**Trigger:** Level 1 retry fails
**Action:**
- Strip STYLE_VARIANCE tokens (keep only CORE + IDENTITY)
- Reduce prompt length by 30-50%
- Reduce shot duration by 25% (if allowed by editor)
- Re-attempt

#### Level 3: Fallback engine (different model family)

**Trigger:** Level 2 fails OR primary engine unavailable
**Action:**
- Switch to `<video_gen_fallback>` (per [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml))
- Typically a smaller / faster / more-reliable model
- Accept lower quality in exchange for completion

#### Level 4: Static image fallback

**Trigger:** Level 3 fails OR all video-gen unavailable
**Action:**
- Use drawer to generate a single high-quality still frame
- Display as static image for the shot's duration
- Add subtle Ken Burns effect (slow zoom/pan) for visual interest
- Mark shot as `static_fallback: true` in metadata

**Editor notification:** the editor must be notified when a shot uses static fallback, so they can plan around the lack of motion (e.g., shorter duration, paired with motion-rich adjacent shots).

### Async batch processing

For multi-shot scenes (typical 短剧 episode = 10-30 shots):

**Batch protocol:**
1. Group shots by scene_ref
2. Within each scene, process sequentially (extension-chain requires order)
3. Across scenes, process in parallel (no dependency)
4. Per shot, attempt Level 1 → 4 until success
5. Emit per-shot quality report + level used

**Cost tracking:**
- Level 1: 1× cost
- Level 2: 1.2× cost (extra inference steps)
- Level 3: 1.5× cost (different engine startup)
- Level 4: 0.3× cost (static image much cheaper)

**Budget alert:** if > 30% of shots require Level 3+, flag for human review (likely systematic prompt issue).

### Seedance-style async API pattern

For engines that support async generation (per kais-camera methodology):

```python
# Submit job
job_id = submit_video_gen(prompt, reference_images, duration)

# Poll status
while True:
    status = check_job_status(job_id)
    if status == "completed":
        video_url = get_job_result(job_id)
        break
    elif status == "failed":
        trigger_degradation_level_2()
        break
    sleep(poll_interval)  # 10-30s typical
```

**Best practice:** submit batches of 5-10 shots concurrently; poll all in parallel; collect results as they complete.

### Quality scoring per shot

After generation, score each shot:

```python
quality_score = (
    temporal_consistency * 0.30 +     # per temporal-consistency.md
    identity_preservation * 0.25 +    # character identity holds
    motion appropriateness * 0.20 +   # matches shot.camera.movement spec
    style_alignment * 0.15 +          # matches STYLE_PREFIX
    duration_accuracy * 0.10          # actual duration within ±5% of spec
)
```

**Per-shot quality grade:**
- A (≥ 0.85): production-ready
- B (0.70-0.85): acceptable, may need editor adjustment
- C (0.55-0.70): marginal, consider regeneration
- D (< 0.55): failed, apply degradation strategy

### Cross-shot extension chain

For shots 2..N in a scene (per [`../../storyboard_designer/references/storyboard-schema.md`](../../storyboard_designer/references/storyboard-schema.md) §end_frame):

**Protocol:**
1. Generate shot 1 with primary engine
2. Extract last frame of shot 1 as `end_frame_1`
3. Use `end_frame_1` as input reference for shot 2 generation
4. Repeat for shots 3..N

**Why this works:** the end_frame provides visual identity continuity (character appearance + scene state) without requiring complex cross-shot constraints.

**Failure mode:** if shot 2 generation drifts significantly from `end_frame_1`, downstream shots 3..N inherit the drift. Mitigation: check identity cosine similarity per shot; if < 0.85, regenerate from end_frame_1.

### Per-scene vs per-shot generation trade-off

| Approach | Pros | Cons |
|---|---|---|
| **Per-shot generation** (default) | Higher quality per shot; easier degradation | Cross-shot drift risk |
| **Per-scene generation** (one long video) | Perfect cross-shot consistency | Much higher cost; harder to iterate |

**Recommendation:** default to per-shot for 短剧 (cost-sensitive); consider per-scene for cinematic 微电影 with high consistency requirements.

### Common generation failures and fixes

| Failure | Cause | Fix |
|---|---|---|
| Character identity drift across shots | Insufficient anchor reference | Strengthen IP-Adapter weight (0.75 → 0.85) |
| Motion doesn't match camera.movement spec | Engine ignores motion keywords | Use stronger motion prompt OR switch engine |
| Video too short | Engine caps duration | Split into multiple shots OR use extension chain |
| Style inconsistent with STYLE_PREFIX | Style tokens too generic | Add more specific style tokens |
| Temporal jitter | Frame coherence too low | Increase frame_coherence_weight to 0.8+ |
| Generation timeout | Async poll timeout too short | Increase timeout OR reduce prompt complexity |

### Per the cognitive-resonance-metrics alignment

Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md):

- **Scale 1 (neural):** motion must respect 2.8-5s attribution window — don't introduce confusing motion mid-shot
- **Scale 1:** temporal jitter p95 ≤ 60ms (per [`../../lip_sync/references/identity-preservation.md`](../../lip_sync/references/identity-preservation.md))
- **Scale 2 (emotional):** motion type should match emotion (slow push-in for emotional peak, NOT fast pan)
- **Scale 1:** audio-visual drift < 120ms — video duration must match TTS audio duration within ±120ms

---

## Cross-references

- [`./video-gen-model-matrix.md`](./video-gen-model-matrix.md) — engine specs
- [`./temporal-consistency.md`](./temporal-consistency.md) — cross-frame coherence
- [`../../storyboard_designer/SKILL.md`](../../storyboard_designer/SKILL.md) — upstream Storyboard source
- [`../../character_designer/references/4d-anchor-system.md`](../../character_designer/references/4d-anchor-system.md) — character anchor source
- [`../../lip_sync/references/identity-preservation.md`](../../lip_sync/references/identity-preservation.md) — temporal jitter thresholds
- [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml) — `<video_gen_primary>` / `<video_gen_fallback>` placeholders
