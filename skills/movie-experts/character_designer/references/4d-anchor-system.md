# 4D Anchor System (4D 锚点协议)

**Source:** Character turnaround sheet convention (animation industry) + multi-view consistency literature + OpenClaw kais-character-designer reference framework.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

The 4D anchor system is the cornerstone of character identity preservation in AI 短剧 / 微电影 production. It defines 4 canonical view angles per character, each with a dedicated prompt template and a usage priority order. Without 4D anchors, downstream experts (drawer, animator, lip_sync) cannot maintain identity across the full range of shot types required by cinematic storytelling.

## Heuristics

### The 4 anchor views

| View | File name | Purpose | Yaw angle | Prompt keywords |
|---|---|---|---|---|
| **front** | `front-source.png` | Identity baseline; used for frontal shots, expression reference, lip_sync reference | 0° | `front view, eyes looking at camera, symmetrical composition, neutral expression` |
| **three_quarter** | `3q-source.png` | Most-used angle; default for majority of shots | 45° | `3/4 view, head turned 45 degrees, showing depth and volume, partial side visibility` |
| **side** | `side-source.png` | Silhouette anchor; used for profile shots, walking-away shots | 90° | `side profile, clean outline, nose bridge and jawline, full body visible` |
| **back** | `back-source.png` | Back composition; used for walking-away reveals | 180° | `back view, full body, hair and outfit back details, no face visible` |

### Why these 4 views (and not more or fewer)

- **3 views insufficient**: front + 3-quarter + side misses back-composition shots (frequently used in 短剧 for "character walks away from conflict" reveals).
- **5+ views overkill**: additional angles (e.g., top-down, worm's-eye) are shot-specific, not identity-defining. Generating them per-character adds cost without improving identity coverage.
- **4 = minimum complete set**: covers all standard cinematic shot angles without redundancy.

### View priority order (for downstream consumption)

When downstream experts must pick which anchor(s) to use as reference, follow this priority:

```
1. three_quarter (default for most shots — natural depth, partial face)
2. front (when shot requires full face: emotional close-ups, dialogue)
3. side (when shot is profile or walking-away)
4. back (when shot is back-composition only)
```

**For Seedance / video-gen dual reference**: use `[three_quarter, front]` as default character anchor pair, plus scene anchor as 3rd ref.

**For lip_sync**: use `front` as primary, `three_quarter` as fallback (lip_sync needs frontal mouth visibility).

**For continuity ArcFace baseline**: use `front` (ArcFace performs best on frontal faces).

### Backward compatibility

If a `CharacterBible` lacks the `references` / `anchors` field (legacy format, or 4D generation failed for some views):

- Downstream consumers fall back to `reference_images[0]` as the single reference.
- This is a degraded mode: cross-angle consistency will suffer.
- Always log a warning when running in fallback mode.

### Anchor generation prompt template

For each view, the generation prompt is constructed as:

```
{STYLE_CORE}, {STYLE_IDENTITY}, {VIEW_SPECIFIC_KEYWORDS},
character turnaround sheet, single character,
consistent character design, {anchor_resolution} resolution
```

Where:
- `STYLE_CORE` = global style layer (from [`style_genome`](../../style_genome/SKILL.md))
- `STYLE_IDENTITY` = per-character identity layer (locked)
- `VIEW_SPECIFIC_KEYWORDS` = the prompt keywords from the table above
- `anchor_resolution` = 2K (production) or 1K (preview)

### Anchor style consistency enforcement

**Hard rule:** all 4 anchors MUST be generated with identical STYLE_PREFIX. Any drift in CORE or IDENTITY layer across views = identity corruption.

**Verification protocol (per anchor set):**
1. Compute pairwise CLIP-I across all 4 views (6 pairs).
2. Compute pairwise DINO-I across all 4 views.
3. **Pass threshold:** all 6 CLIP-I pairs ≥ 0.80; all 6 DINO-I pairs ≥ 0.78.
4. **Failure mode:** any pair < threshold → regenerate the failing view.

### Cross-view variance budget

Even with strict STYLE_PREFIX, some natural variance is expected (different angles show different features). The variance budget defines acceptable drift:

| Metric | Within-view (regen same view) | Cross-view (different angles) |
|---|---|---|
| CLIP-I | ≥ 0.92 | 0.80-0.90 |
| DINO-I | ≥ 0.90 | 0.78-0.88 |
| ArcFace (front vs others) | N/A | front vs 3Q ≥ 0.85; front vs side ≥ 0.75 |

**Failure mode:** cross-view CLIP-I > 0.95 = suspiciously similar (may indicate model is collapsing to a single canonical view rather than generating true multi-angle).

### Anchor file naming convention

**Required** per character:
```
assets/characters/{character_id}/
├── front-source.png      # 0° yaw
├── 3q-source.png         # 45° yaw
├── side-source.png       # 90° yaw
└── back-source.png       # 180° yaw
```

**Reference library** (8 images derived from anchors):
```
assets/characters/{character_id}/
├── front-portrait.png
├── 3quarter-body.png
├── side-profile.png
├── back-view.png
├── expression-shock.png
├── expression-shy.png
├── expression-calm.png
└── action-typing.png
```

### Resolution and aspect

- **Anchor images**: 1:1 aspect ratio (square), 2K resolution for production
- **Reference library images**: scene-appropriate aspect (3:4 portrait, 9:16 for 短剧 vertical, 16:9 for 微电影 horizontal)
- **All images**: PNG (lossless) for production; JPEG acceptable for preview only

### Common pitfalls and fixes

| Pitfall | Cause | Fix |
|---|---|---|
| Side view shows face instead of profile | Model defaults to face-forward | Add `strict side profile, no face visible, ear prominent` to prompt |
| Back view turns head | Model reluctant to show back of head | Add `head facing away from camera, no face visible, full back of head` |
| 3Q view too close to front | Model collapses angle | Add `45 degrees head turn, both eyes not equally visible` |
| Different eye color across views | Identity drift | Add identity tokens (e.g., `red eyes`) to all view prompts explicitly |
| Outfit changes across views | Identity drift | Add outfit tokens (e.g., `black trench coat`) to all view prompts explicitly |

---

## Cross-references

- [`./layered-style-prefix.md`](./layered-style-prefix.md) — STYLE_PREFIX construction that feeds anchor generation
- [`./consistency-stress-test.md`](./consistency-stress-test.md) — verifies anchor-derived reference library
- [`./character-bible-schema.md`](./character-bible-schema.md) — schema for the `anchors` field
- [`../../drawer/references/character-consistency-lora.md`](../../drawer/references/character-consistency-lora.md) — drawer's character-consistency stack consumes 4D anchors
- [`../../lip_sync/references/identity-preservation.md`](../../lip_sync/references/identity-preservation.md) — lip_sync uses front anchor for ArcFace baseline
