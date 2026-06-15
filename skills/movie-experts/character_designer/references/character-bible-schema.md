# CharacterBible 2.0 Schema

**Source:** Hermes Agent project schema design + OpenClaw kais-character-designer CharacterBible 2.0 + downstream consumer requirements (drawer / animator / lip_sync / continuity).
**Copyright:** Fair Use — schema specification.
**Last-verified:** 2026-06-16

## Summary

The authoritative schema specification for the `CharacterBible 2.0` JSON artifact produced by character_designer. Every field is documented with: purpose, type, mutability rule, downstream consumers, and frozen-status. This file is the ground truth — any drift in downstream consumers' expectations must be resolved here first.

## Schema overview

```json
{
  "type": "CharacterBible",
  "version": "2.0.0",
  "character_id": "char_<short_id>",
  "name": "<display_name>",
  "appearance": "<natural_language_description>",
  "personality": "<natural_language_description>",
  "anchors": { ... },
  "reference_images": [ ... ],
  "reference_library": { ... },
  "style_layers": { ... },
  "style_prefix_locked": "<composed_string>",
  "negative_traits": [ ... ],
  "layers": { ... },
  "seedance_profile": { ... },
  "video_samples": [ ... ],
  "sample_strength_default": 0.35,
  "consistency_lock": { ... },
  "downstream_consumers": [ ... ]
}
```

## Field specifications

### `character_id`

- **Type:** string
- **Format:** `char_<short_id>` (lowercase, alphanumeric, ≤ 20 chars after prefix)
- **Mutability:** Frozen at creation; never changes
- **Downstream consumers:** all experts (this is the join key across the production DAG)
- **Example:** `char_wuji`

### `name`

- **Type:** string
- **Mutability:** Editable (display name can change)
- **Example:** `无极`

### `appearance`

- **Type:** string (natural language)
- **Mutability:** **FROZEN after lock** (in `consistency_lock.frozen_fields`)
- **Required sub-content:** age + gender + hair (color/length/style) + eyes (color/shape) + face (jawline/cheekbones/distinguishing marks) + outfit + accessories + height/build (if known)
- **Length:** 100-300 chars
- **Downstream consumers:** drawer (image generation), continuity (visual reference)

### `personality`

- **Type:** string (natural language)
- **Mutability:** Editable
- **Required sub-content:** temperament + motivation + interpersonal style
- **Downstream consumers:** screenplay (dialogue calibration), performer (body language baseline)

### `anchors`

- **Type:** object with 4 string fields
- **Fields:** `front`, `three_quarter`, `side`, `back`
- **Each field:** file path to the anchor source image
- **Mutability:** **FROZEN after lock** (regeneration requires lock_version bump)
- **Downstream consumers:** drawer, animator, lip_sync (front + 3Q), continuity (front for ArcFace)
- **Required:** all 4 fields populated for primary characters; `front` + `three_quarter` minimum for secondary

### `reference_images`

- **Type:** array of strings (file paths)
- **Length:** 6-8 images
- **Mutability:** Editable (library can be extended post-lock with new expression / action refs)
- **Required content (8 standard refs):**
  - `front-portrait.png` — face close-up
  - `3quarter-body.png` — default half-body
  - `side-profile.png` — side silhouette
  - `back-view.png` — back composition
  - `expression-shock.png` — shocked emotion
  - `expression-shy.png` — shy emotion
  - `expression-calm.png` — calm emotion
  - `action-typing.png` — low-lock action reference

### `reference_library`

- **Type:** object keyed by image name
- **Each entry:** `{ url, strength (0.30-0.55), angle, purpose }`
- **Mutability:** Editable
- **Downstream consumers:** drawer (selects ref per scene needs)

### `style_layers`

- **Type:** object with 3 string fields
- **Fields:** `core` (frozen), `identity` (frozen), `variance_template` (editable)
- **Mutability:** `core` + `identity` frozen after lock; `variance_template` editable
- **Downstream consumers:** drawer, animator (compose per-scene STYLE_PREFIX)

### `style_prefix_locked`

- **Type:** string
- **Format:** `{core}, {identity}, {VARIANCE}` (VARIANCE is literal placeholder)
- **Mutability:** Frozen after lock
- **Downstream consumers:** drawer, animator (every prompt uses this prefix)

### `negative_traits`

- **Type:** array of strings
- **Length:** ≥ 3 items (recommended 5-8)
- **Mutability:** **FROZEN after lock**
- **Required content:** must cover common drift vectors for this character's demographic (e.g., for a male character: `["blonde hair", "beard", "glasses", "short hair", "blue eyes", "smile (default)"]`)
- **Downstream consumers:** drawer, animator (appended to negative prompt)

### `layers`

- **Type:** object with face/outfit/accessories sub-objects
- **Each sub-object:** `{ locked: bool, features: string }`
- **Mutability:** face + outfit typically locked; accessories often editable
- **Downstream consumers:** drawer, continuity

### `seedance_profile`

- **Type:** object with `consistency_mode`, `default_strength`, `character_ref_priority`
- **Mutability:** Editable
- **Downstream consumers:** animator (Seedance / video-gen dual-reference setup)
- **`character_ref_priority`:** ordered list of view names (e.g., `["three_quarter", "front"]`)

### `video_samples`

- **Type:** array of objects (initially empty, populated by animator)
- **Mutability:** Editable
- **Downstream consumers:** animator (chain reference), continuity

### `sample_strength_default`

- **Type:** float
- **Range:** 0.20-0.50
- **Default:** 0.35
- **Mutability:** Editable
- **Downstream consumers:** drawer, animator

### `consistency_lock`

- **Type:** object
- **Required sub-fields:**
  - `locked: bool`
  - `lock_version: int` (starts at 1, bumps on each revision)
  - `anchor_mode: "reference_image"` (only supported mode currently)
  - `frozen_fields: array of strings` (e.g., `["appearance", "style_layers.core", "style_layers.identity", "negative_traits"]`)
  - `stress_test_results: object` (per [`./consistency-stress-test.md`](./consistency-stress-test.md))

**Lock state machine:**

```
unlocked → stress_testing → locked(passed) ↔ revision_pending
                       ↘
                         locked(failed) → [return to variant selection]
```

### `downstream_consumers`

- **Type:** array of strings (expert_ids)
- **Default:** `["drawer", "animator", "lip_sync", "continuity", "production"]`
- **Mutability:** Editable
- **Purpose:** documentation of which experts read this CharacterBible

## Frozen fields contract

Once `consistency_lock.locked = true` and `lock_version ≥ 1`, the following fields are **immutable** unless explicit `revision_pending` workflow is invoked:

- `character_id`
- `appearance`
- `style_layers.core`
- `style_layers.identity`
- `style_prefix_locked`
- `negative_traits`
- `anchors.front` / `anchors.three_quarter` / `anchors.side` / `anchors.back`
- `layers.face` (if `locked: true`)
- `layers.outfit` (if `locked: true`)

**Revision workflow:**
1. Set `consistency_lock.locked = false` (transitional state)
2. Set `consistency_lock.lock_version += 1`
3. Modify the frozen field
4. Re-run consistency stress test
5. If passed: `consistency_lock.locked = true`
6. Notify all `downstream_consumers` to re-consume (they should detect version bump)

## Backward compatibility

A `CharacterBible 1.0` (legacy) lacks:
- `anchors` field (downstream falls back to `reference_images[0]`)
- `style_layers` field (downstream infers from free-text `appearance`)
- `consistency_lock` field (treated as unlocked; stress test required before consumption)
- `negative_traits` field (drift risk; character_designer should be re-run)

**Migration path:** character_designer accepts 1.0 input, upgrades to 2.0 output. Downstream consumers must support both, but flag 1.0 with a deprecation warning.

## Validation checklist for CharacterBible 2.0

Before emitting, verify:

- [ ] All required top-level fields present (`type`, `version`, `character_id`, `name`, `appearance`, `personality`, `anchors`, `reference_images`, `style_layers`, `negative_traits`, `consistency_lock`)
- [ ] `character_id` matches `char_<short_id>` format
- [ ] `appearance` is 100-300 chars and covers physical + outfit
- [ ] `anchors` has at least `front` + `three_quarter`; recommended all 4
- [ ] `reference_images` has 6-8 entries
- [ ] `style_layers.core` matches upstream style_genome output
- [ ] `style_layers.identity` is specific (≥ 5 features)
- [ ] `negative_traits` has ≥ 3 items
- [ ] `consistency_lock.stress_test_results` populated
- [ ] If `locked = true`: all `frozen_fields` listed and match schema

---

## Cross-references

- [`./4d-anchor-system.md`](./4d-anchor-system.md) — `anchors` field source
- [`./layered-style-prefix.md`](./layered-style-prefix.md) — `style_layers` + `style_prefix_locked` source
- [`./consistency-stress-test.md`](./consistency-stress-test.md) — `consistency_lock.stress_test_results` source
- [`../../drawer/SKILL.md`](../../drawer/SKILL.md) — primary downstream consumer
- [`../../continuity/SKILL.md`](../../continuity/SKILL.md) — ArcFace baseline consumer
