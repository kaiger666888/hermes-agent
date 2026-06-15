# 4D Anchoring Parameters (四维锚定参数)

**Source:** ControlNet (Zhang et al. 2023) + IP-Adapter (Ye et al. 2023) + IC-Light + AnimateDiff + OpenClaw kais-storyboard-designer 4D-anchoring design.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Authoritative specification for the 4D anchoring block in each Storyboard shot. The 4 dimensions (depth / identity / lighting / temporal) control how the Render Layer (drawer + animator) injects consistency cues into image / video generation. Without proper anchoring, downstream generation drifts freely and cross-shot consistency fails.

## Heuristics

### The 4 anchoring dimensions

| Dimension | Tool placeholder | Purpose | Effect when missing |
|---|---|---|---|
| **深度 / Depth** | `<controlnet_depth>` | Lock foreground / midground / background spatial hierarchy | Subject floats in undefined space; perspective drift |
| **身份 / Identity** | `<ip_adapter>` | Lock character identity across shots | Character's appearance drifts (face / outfit / hair) |
| **光影 / Lighting** | `<ic_light>` | Lock light direction / intensity / color temp / mood | Lighting inconsistent across shots; mood drift |
| **时序 / Temporal** | `<animatediff>` | Lock motion type / speed / frame-rate coherence | Video shots have inconsistent motion style; jitter |

### Depth anchoring parameters

```json
{
  "depth": {
    "enabled": true,
    "strength": 0.7,
    "foreground": "character sitting on bench",
    "midground": "park bench, trees",
    "background": "sunset city skyline",
    "depth_map_source": "auto"
  }
}
```

**Field specs:**
- `enabled`: bool — whether this dimension is active for the shot
- `strength`: float 0.5-0.9 — how strongly the depth map constrains generation
  - 0.5 = loose (allows some perspective interpretation)
  - 0.7 = default (balanced)
  - 0.9 = strict (locks exact depth)
- `foreground` / `midground` / `background`: natural-language descriptions of each depth layer
- `depth_map_source`: `"auto"` (computed from sketch) OR `"manual"` (user-provided depth map)

**Depth map generation:** derived from the scene sketch (`reference_image` field of the shot).

### Identity anchoring parameters

```json
{
  "identity": {
    "enabled": true,
    "characters": [
      {
        "ref": "char_wuji",
        "weight": 0.75,
        "anchor_priority": ["three_quarter", "front"]
      },
      {
        "ref": "char_mei",
        "weight": 0.70,
        "anchor_priority": ["front"]
      }
    ]
  }
}
```

**Field specs:**
- `characters`: array of character references (linked to CharacterBible IDs)
- `weight`: float 0.6-0.9 — how strongly each character's identity is enforced
  - 0.6 = loose (allows some appearance variation)
  - 0.75 = default
  - 0.9 = strict (locks exact appearance)
- `anchor_priority`: ordered list of which 4D anchors to try first (per CharacterBible.anchors)

**Multi-character handling:**
- Each character has independent weight
- Drawer must apply IP-Adapter per character
- Cross-character consistency NOT enforced by identity anchoring (that's continuity's job)

### Lighting anchoring parameters

```json
{
  "lighting": {
    "enabled": true,
    "direction": "upper-left",
    "intensity": 0.7,
    "color_temp": "4500K",
    "mood": "dramatic, rim-light",
    "reference_image": "lighting_refs/dramatic_rim_01.png"
  }
}
```

**Field specs:**
- `direction`: cardinal or inter-cardinal direction of primary light source
- `intensity`: float 0.0-1.0 — light strength
  - 0.3 = dim / atmospheric
  - 0.7 = default
  - 1.0 = harsh / bright
- `color_temp`: Kelvin scale
  - 2700-3200K = warm (tungsten / sunset / candle)
  - 4000-5000K = neutral (daylight / office)
  - 5500-6500K = cool (overcast / neon / tech)
- `mood`: natural-language mood descriptor for IC-Light conditioning
- `reference_image` (optional): explicit lighting reference for IC-Light

### Temporal anchoring parameters

```json
{
  "temporal": {
    "enabled": true,
    "motion_type": "slow-push-in",
    "motion_speed": 0.3,
    "motion_strength": 0.6,
    "fps": 24,
    "frame_coherence_weight": 0.7
  }
}
```

**Field specs:**
- `motion_type`: from the 7 standard types (push-in / pull-out / pan / tilt / tracking / handheld / static)
- `motion_speed`: float 0.0-1.0
  - 0.1-0.3 = slow (dramatic / contemplative)
  - 0.4-0.6 = medium (default)
  - 0.7-1.0 = fast (action / urgent)
- `motion_strength`: how strongly motion is enforced (vs static frames)
- `fps`: target frame rate (24 = cinematic, 30 = video standard, 60 = smooth)
- `frame_coherence_weight`: float 0.4-0.9 — temporal consistency between frames
  - 0.4 = loose (more motion freedom)
  - 0.7 = default
  - 0.9 = strict (may cause temporal jitter if too high)

### 4-tier progressive degradation strategy

| Tier | Anchoring enabled | Use case | Cost |
|---|---|---|---|
| **Draft** | none | 快速原型 / story reel / 早期 review | 最低 (1×) |
| **Standard** | identity only | 角色一致短片 / 测试生成 | 中 (2×) |
| **Cinematic** | depth + identity + lighting | 正式制作 (default) | 高 (4×) |
| **Premium** | all 4 dimensions | 电影级成片 / 最终交付 | 最高 (6×) |

**Cost multiplier rationale:** each anchoring dimension adds generation time:
- Draft: 1× baseline (no ControlNet / IP-Adapter calls)
- Standard: 2× (IP-Adapter inference per character)
- Cinematic: 4× (ControlNet Depth + IP-Adapter + IC-Light)
- Premium: 6× (all of the above + AnimateDiff temporal coherence)

### Tier selection logic

```
What is the production use case?
├── Early preview / story reel → Draft
├── Character test / consistency check → Standard
├── Production still (drawer output) → Cinematic
├── Production video (animator output) → Premium
└── Final delivery → Premium
```

### Anchoring completeness audit

For each shot, verify:

- [ ] If tier ≥ Standard: `identity.enabled = true` and `characters[]` populated
- [ ] If tier ≥ Cinematic: `depth.enabled = true` AND `lighting.enabled = true`
- [ ] If tier = Premium: `temporal.enabled = true` (only for animator, not drawer)
- [ ] All `strength` values within documented range
- [ ] All `weight` values within documented range
- [ ] All character refs exist in CharacterBible array

### Anchoring vs downstream expert responsibility

| Dimension | Drawer responsibility | Animator responsibility |
|---|---|---|
| Depth | Apply ControlNet Depth during image gen | N/A (depth implicit in video) |
| Identity | Apply IP-Adapter per character | Apply character anchor images in video gen |
| Lighting | Apply IC-Light conditioning | Apply consistent lighting across frames |
| Temporal | N/A (single image) | Apply AnimateDiff motion + coherence |

**Key insight:** drawer applies 3/4 dimensions (depth + identity + lighting). Animator applies all 4. This is why video is more expensive than stills.

### Common pitfalls

| Pitfall | Cause | Fix |
|---|---|---|
| Identity weight too low (0.5) | Trying to "allow variation" | Use 0.7+ for primary characters |
| Depth strength too high (0.95) | Over-constraining | Use 0.7 default; only go higher for architectural shots |
| Lighting direction inconsistent across shots | Each shot designed in isolation | Use scene-level lighting plan; copy across shots |
| Temporal frame_coherence_weight > 0.9 | Trying to eliminate jitter | Causes rigid motion; use 0.7 default |
| Wrong tier for use case | Defaulting to Premium everywhere | Use Draft for preview, Cinematic for production |
| Missing depth foreground description | Forgot to specify | Each depth layer needs description or depth_map_source |

### Vertical (9:16) anchoring adaptations

For 短剧 vertical format:
- **Depth**: background descriptions should account for vertical composition
- **Identity**: prefer `front` and `three_quarter` anchors (vertical frame is tighter)
- **Lighting**: account for caption strip (avoid placing key light there)
- **Temporal**: vertical 短剧 typical motion_speed range is 0.3-0.6 (medium pacing)

---

## Cross-references

- [`./shot-decomposition-rules.md`](./shot-decomposition-rules.md) — shot-level decisions before anchoring
- [`./camera-params-dictionary.md`](./camera-params-dictionary.md) — camera params complement anchoring
- [`./storyboard-schema.md`](./storyboard-schema.md) — schema for the `anchoring` field
- [`../../character_designer/references/4d-anchor-system.md`](../../character_designer/references/4d-anchor-system.md) — CharacterBible anchors consumed by identity dimension
- [`../../drawer/references/character-consistency-lora.md`](../../drawer/references/character-consistency-lora.md) — drawer's character consistency stack
- [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml) — placeholder resolution for ControlNet / IP-Adapter / IC-Light / AnimateDiff
