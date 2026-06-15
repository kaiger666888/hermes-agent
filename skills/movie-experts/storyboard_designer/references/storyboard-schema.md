# Storyboard JSON Schema

**Source:** Hermes Agent project schema design + OpenClaw kais-storyboard-designer Storyboard schema + downstream consumer requirements.
**Copyright:** Fair Use — schema specification.
**Last-verified:** 2026-06-16

## Summary

Authoritative schema specification for the `Storyboard` JSON artifact produced by storyboard_designer. Documents every field, its type, mutability, and downstream consumer expectations.

## Schema overview

```json
{
  "type": "Storyboard",
  "version": "1.0.0",
  "episode_ref": "S1E0X",
  "scene_refs": ["scene_001", "scene_002"],
  "metadata": { ... },
  "shots": [ ... ],
  "downstream_consumers": [ ... ]
}
```

## Field specifications

### Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | Yes | Always `"Storyboard"` |
| `version` | string | Yes | Schema version (semver) |
| `episode_ref` | string | Yes | Episode identifier from screenplay |
| `scene_refs` | array<string> | Yes | Scene IDs covered by this Storyboard |
| `metadata` | object | Yes | Aggregate metadata (see below) |
| `shots` | array<object> | Yes | The shot list (see below) |
| `downstream_consumers` | array<string> | Yes | Expert IDs that consume this Storyboard |

### `metadata` object

| Field | Type | Description |
|---|---|---|
| `total_shots` | int | Length of `shots` array |
| `total_duration_estimate_seconds` | float | Sum of all `shots[].duration` |
| `tier` | string | One of `Draft` / `Standard` / `Cinematic` / `Premium` |
| `axis_compliance_passed` | bool | Whether 180° + 30° rules passed audit |
| `rhythm_curve` | object | Rhythm curve specification |

### `rhythm_curve` object

| Field | Type | Description |
|---|---|---|
| `type` | string | One of `escalating` / `wave` / `constant` / `reverse-escalating` / `peak-valley` |
| `shot_duration_distribution` | array<float> | Durations in shot order |
| `peaks_at_shot_indices` | array<int> | Indices of high-intensity shots |

### `shots[]` object schema

Each shot in the `shots` array has:

```json
{
  "shot_id": "shot_001",
  "scene_ref": "scene_001",
  "character_refs": ["char_wuji"],
  "camera": { ... },
  "action": "...",
  "duration": 4.5,
  "reference_image": "...",
  "render_image": "...",
  "end_frame": "...",
  "anchoring": { ... },
  "intentional_axis_cross": false,
  "intentional_jump_cut": false
}
```

#### `shot_id`

- **Type:** string
- **Format:** `shot_<3-digit-zero-padded>` (e.g., `shot_001`, `shot_014`)
- **Mutability:** Frozen at creation
- **Downstream consumers:** all experts (this is the join key)

#### `scene_ref`

- **Type:** string
- **Required:** Yes
- **Format:** matches `scene_refs` entry in top-level

#### `character_refs`

- **Type:** array of strings
- **Required:** Yes (may be empty if no characters in shot)
- **Each entry:** matches `character_id` in some CharacterBible

#### `camera` object

| Field | Type | Description |
|---|---|---|
| `angle` | string | Shot type (e.g., `"中景 / Medium Shot"`) — bilingual format |
| `movement` | string | Movement type (e.g., `"缓慢推进 / Slow Push-in"`) — bilingual format |
| `lens` | string | Focal length (e.g., `"50mm"`) |
| `lens_purpose` | string | One-line justification of lens choice |

**Required:** `angle` + `movement` + `lens`. `lens_purpose` recommended.

#### `action`

- **Type:** string (natural language)
- **Required:** Yes
- **Length:** 50-300 chars
- **Content:** describes what happens in the shot (character action + camera action + setting)
- **Downstream consumers:** drawer (image prompt), animator (video prompt), editor (cut reference)

#### `duration`

- **Type:** float (seconds)
- **Required:** Yes
- **Range:** 1.0-30.0s typical for 短剧; up to 60s for 微电影
- **Constraint:** sum of all `shots[].duration` ≈ `metadata.total_duration_estimate_seconds`

#### `reference_image` vs `render_image` (dual-pointer)

| Field | Purpose | Source |
|---|---|---|
| `reference_image` | 构图蓝本 / composition sketch | SceneDesign `sketch_image` OR standalone sketch |
| `render_image` | 最终画面 / final rendered look | SceneDesign `render_image` OR drawer output |

**Hard rule:** both fields must be populated. They serve different purposes:
- `reference_image` (sketch) shows composition + spatial relationships, color-agnostic
- `render_image` (final) shows actual colors + lighting + style

Drawer reviews both before generating; animator uses `render_image` as visual anchor.

#### `end_frame` (extension-chain anchor)

- **Type:** string (file path)
- **Required:** Yes for shots 1..N-1 in any scene; optional for the last shot in a scene
- **Purpose:** visual anchor for the NEXT shot in the scene — the next shot's first frame should match this end_frame

**Extension-chain protocol:**
1. Animator generates shot 1 video.
2. Shot 1's `end_frame` is captured from the video's last frame.
3. Shot 2's animator uses shot 1's `end_frame` as input reference for visual continuity.

This is critical for cross-shot character + setting consistency in AI-generated video.

#### `anchoring` object

Per [`./4d-anchoring-params.md`](./4d-anchoring-params.md). Has 4 sub-objects: `depth`, `identity`, `lighting`, `temporal`.

#### `intentional_axis_cross` / `intentional_jump_cut`

- **Type:** bool
- **Default:** false
- **Purpose:** explicitly mark intentional violations of axis / 30° rules (for dream / disorientation effect)
- **Audit:** if true, the axis compliance audit passes the shot with a warning

## Validation rules

A Storyboard JSON is valid if:

- [ ] All top-level required fields present
- [ ] `shots[]` is non-empty
- [ ] Every `shot_id` is unique
- [ ] Every `scene_ref` matches an entry in `scene_refs`
- [ ] Every `character_refs[]` entry matches a CharacterBible ID
- [ ] Every shot has `camera.angle` + `camera.movement` + `camera.lens`
- [ ] Every shot has `action` (50-300 chars)
- [ ] Every shot has `duration` in valid range
- [ ] Sum of `shots[].duration` ≈ `metadata.total_duration_estimate_seconds` (±10%)
- [ ] Tier ≥ Cinematic: every shot has `anchoring.depth.enabled = true` AND `anchoring.identity.enabled = true` AND `anchoring.lighting.enabled = true`
- [ ] Tier = Premium: every shot additionally has `anchoring.temporal.enabled = true`
- [ ] For shots 1..N-1 in each scene: `end_frame` populated
- [ ] Axis compliance audit passed (or all violations marked `intentional_*`)

## Downstream consumption contracts

### Drawer consumption

For each shot:
1. Read `camera.angle` + `camera.movement` + `lens` to set generation prompt
2. Read `action` for scene description
3. Read `reference_image` for composition guidance
4. Read `anchoring.depth` to apply ControlNet Depth
5. Read `anchoring.identity` to apply IP-Adapter per character
6. Read `anchoring.lighting` to apply IC-Light
7. Generate `render_image` output

### Animator consumption

For each shot:
1. All drawer steps (image first)
2. Additionally read `anchoring.temporal` to apply AnimateDiff
3. Use prior shot's `end_frame` as visual continuity reference
4. Generate per-shot video segment

### Editor consumption

1. Read `shots[].duration` for cut timings
2. Read `metadata.rhythm_curve` for pacing intent
3. Assemble shots in order; apply transitions per `metadata.rhythm_curve.peaks`

### Continuity consumption

1. Read all `character_refs` per scene
2. Cross-check character identity across shots
3. Verify `end_frame` continuity (shot N end matches shot N+1 start)
4. Audit 180° / 30° compliance via `intentional_*` flags

## Backward compatibility

A legacy Storyboard (pre-4D-anchoring) lacks:
- `anchoring` field — drawer / animator fall back to default settings
- `end_frame` field — animator runs each shot independently (lower continuity)
- `tier` field — assume `Standard`

**Migration path:** storyboard_designer accepts legacy input, upgrades to v1.0.0 output with all fields populated.

---

## Cross-references

- [`./shot-decomposition-rules.md`](./shot-decomposition-rules.md) — how shots are decomposed
- [`./camera-params-dictionary.md`](./camera-params-dictionary.md) — `camera.*` field source
- [`./4d-anchoring-params.md`](./4d-anchoring-params.md) — `anchoring` field source
- [`../../character_designer/references/character-bible-schema.md`](../../character_designer/references/character-bible-schema.md) — `character_refs` join target
