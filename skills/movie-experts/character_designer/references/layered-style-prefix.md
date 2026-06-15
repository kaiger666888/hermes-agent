# Layered STYLE_PREFIX (分层风格前缀)

**Source:** Prompt engineering best practices + LoRA / IP-Adapter character consistency literature + OpenClaw kais-character-designer STYLE_PREFIX doctrine.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Authoritative methodology for constructing and locking the layered STYLE_PREFIX that controls character identity across all downstream image generations. The 3-layer architecture (CORE / IDENTITY / VARIANCE) is what enables per-character identity preservation while still allowing scene-specific variation.

## Heuristics

### The 3-layer architecture

| Layer | Scope | Mutability | Example |
|---|---|---|---|
| **STYLE_CORE** | Global (all characters in a project) | Frozen after style_genome output | `anime, cyberpunk era, cinematic lighting` |
| **STYLE_IDENTITY** | Per-character (one specific character) | Frozen after character_designer lock | `black long hair, red eyes, scar on left cheek, black trench coat` |
| **STYLE_VARIANCE** | Per-shot / per-scene | Mutable per scene context | `{lighting}, {weather}, {mood}` template |

**Composition formula (used in every downstream prompt):**

```
{STYLE_CORE}, {STYLE_IDENTITY}, {STYLE_VARIANCE}
```

### Layer 1: STYLE_CORE

**Source:** computed by [`style_genome`](../../style_genome/SKILL.md) expert.

**Required sub-fields:**
- **genre**: project genre (cyberpunk / wuxia / romance / horror / ...)
- **era**: time period (contemporary / medieval / future / ...)
- **mood**: global aesthetic (cinematic / anime / realistic / ...)
- **lighting style**: high-level lighting direction (high-key / low-key / mixed)

**Locking rule:** STYLE_CORE is locked when style_genome emits its StyleGenome JSON. Any subsequent change requires:
1. Re-running style_genome with new inputs
2. Bumping style_genome version
3. Cascade-triggering character_designer revision for ALL characters (STYLE_CORE changed)

**Pitfall:** if style_genome is skipped or vague, STYLE_CORE defaults drift toward drawer's training distribution (generic photorealism or generic anime) — every character ends up looking same-genre.

### Layer 2: STYLE_IDENTITY

**Source:** character_designer expert, derived from character spec + screenplay character list.

**Required sub-fields:**
- **physical**: hair (color, length, style), eyes (color, shape), face (jawline, cheekbones, distinguishing features like scars)
- **outfit**: primary clothing (color, garment type), secondary clothing, footwear
- **accessories**: default accessories (watches, earrings, glasses — only if always present)
- **distinguishing marks**: scars, tattoos, birthmarks

**Locking rule:** STYLE_IDENTITY is locked when character_designer passes consistency stress test. After lock:
- ✅ Editable: nothing in STYLE_IDENTITY
- ❌ Frozen: physical, outfit, accessories (if marked as locked), distinguishing marks
- ⚠️ Revision path: requires explicit `revision_pending` workflow + lock_version bump + re-running stress test

**Pitfall:** vague identity layer ("cool-looking guy with dark hair") = downstream drift; specific layer ("25yo male, shoulder-length black hair with slight wave, red eyes, 3cm scar on left cheek") = locked identity.

### Layer 3: STYLE_VARIANCE

**Source:** per-scene context, populated at downstream expert call time.

**Template form:**

```yaml
variance_template: "{lighting}, {weather}, {mood}"
```

**Per-shot substitution examples:**

| Shot context | Substituted VARIANCE |
|---|---|
| Street scene at night | `neon lighting, rainy, melancholic mood` |
| Indoor dialogue close-up | `soft window light, indoor, tense mood` |
| Action running scene | `dynamic motion blur, outdoor daylight, urgent mood` |
| Emotional breakdown scene | `dim lighting, indoor, grief mood` |

**Locking rule:** STYLE_VARIANCE is the ONLY mutable layer after character lock. Variance values must:
- Not contradict STYLE_IDENTITY (e.g., cannot put "blonde hair" in VARIANCE if IDENTITY locks "black hair")
- Not contradict STYLE_CORE (e.g., cannot put "watercolor style" in VARIANCE if CORE is "cinematic photorealism")
- Be consistent within a single scene (no mid-scene lighting changes)

### Final STYLE_PREFIX example (after lock)

```yaml
style_prefix_locked: "anime, cyberpunk era, cinematic lighting,
  black long hair (shoulder-length, slight wave), red eyes,
  scar on left cheek, black trench coat, gray turtleneck, black boots,
  {VARIANCE}"
```

**Every** downstream image generation for this character uses this exact prefix with `{VARIANCE}` substituted per scene.

### Regeneration trigger conditions

STYLE_PREFIX is generally immutable after lock. **Regeneration required when:**

| Trigger | What regenerates | Downstream impact |
|---|---|---|
| STYLE_CORE changed (via style_genome revision) | All 4 anchors + all 8 reference library images for ALL characters | Cascade: drawer / animator / lip_sync must re-consume |
| STYLE_IDENTITY changed (via character revision) | Affected character's 4 anchors + 8 reference images + stress test re-run | Cascade: drawer / animator / lip_sync must re-consume for affected character |
| STYLE_VARIANCE scope violation detected | Only affected scene's images | Drawer must re-generate scene images with corrected VARIANCE |
| Negative trait violation detected (post-gen audit) | Affected image only | Drawer must re-generate with strengthened negative prompt |

**Cost warning:** STYLE_CORE changes are catastrophic — they cascade to every character + every downstream expert. Only do this if the style_genome upstream is fundamentally broken.

### Cross-layer consistency rules

**Hard rules:**
- All 3 layers must use the same language register (don't mix English CORE with Chinese IDENTITY)
- All 3 layers must use the same level of specificity (don't mix vague CORE with hyper-specific IDENTITY)
- VARIANCE values must not include any token that appears in IDENTITY's `negative_traits`

**Soft rules:**
- IDENTITY length should be 50-150 tokens (too short = vague; too long = model loses plot)
- CORE length should be 20-50 tokens
- VARIANCE length should be 5-30 tokens per substitution

### STYLE_PREFIX vs negative prompt

STYLE_PREFIX defines what character IS. Negative prompt defines what character is NOT.

**For each character, both are required:**

```yaml
positive_prompt: "{STYLE_PREFIX}, {scene_specific_addons}"
negative_prompt: "{negative_traits}, {general_negatives}"
```

Where:
- `negative_traits` from CharacterBible (e.g., `blonde hair, beard, glasses, short hair, blue eyes`)
- `general_negatives` are drawer-wide (e.g., `low quality, blurry, deformed, multiple people`)

**Hard rule:** negative_traits must mirror every "default drift" the model tends toward for this character's demographic. Without negative_traits, the model reverts to training defaults.

### Audit protocol for STYLE_PREFIX

When auditing a character_designer output:

1. Extract STYLE_CORE, STYLE_IDENTITY, STYLE_VARIANCE template.
2. Verify STYLE_CORE matches style_genome output (no drift).
3. Verify STYLE_IDENTITY is specific enough (≥ 5 physical features described).
4. Verify STYLE_VARIANCE template has placeholders, not literal scene tokens.
5. Verify negative_traits list ≥ 3 items and covers common drift vectors.
6. Test prompt by substituting VARIANCE in 3 different scenes; verify output CLIP-I within thresholds.

---

## Cross-references

- [`./4d-anchor-system.md`](./4d-anchor-system.md) — anchor generation consumes STYLE_PREFIX
- [`./consistency-stress-test.md`](./consistency-stress-test.md) — verifies STYLE_PREFIX produces consistent identity across scenes
- [`./character-bible-schema.md`](./character-bible-schema.md) — schema for `style_layers` field
- [`../../style_genome/SKILL.md`](../../style_genome/SKILL.md) — upstream STYLE_CORE source
- [`../../drawer/references/flux2-parameter-surface.md`](../../drawer/references/flux2-parameter-surface.md) — drawer prompt engineering consumes STYLE_PREFIX
