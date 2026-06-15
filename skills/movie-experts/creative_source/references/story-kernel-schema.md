# Story Kernel Schema

**Source:** Hermes Agent project schema design + OpenClaw kais-soul-radar Story Kernel format + downstream consumer requirements.
**Copyright:** Fair Use — schema specification.
**Last-verified:** 2026-06-16

## Summary

Authoritative schema specification for the `StoryKernel` JSON artifact produced by creative_source. Each field is documented with type, mutability, downstream consumer expectations.

## Schema overview

```json
{
  "type": "StoryKernel",
  "version": "1.0.0",
  "kernel_id": "kernel_<hash>",
  "title_working": "<working_title>",
  "strata_layers": [ ... ],
  "structural_formula": "<single_sentence>",
  "strata_overlay_coefficient": 1.8,
  "overlay_amplification": "<explanation>",
  "unspeakability_score": 7,
  "unspeakability_breakdown": { ... },
  "platform_compliance_paths": { ... },
  "dramatic_potential": { ... },
  "target_audience_overlap": { ... },
  "downstream_consumers": [ ... ],
  "created_at": "<ISO8601>",
  "created_by": "creative_source",
  "evidence_strength_aggregate": "<level>"
}
```

## Field specifications

### `kernel_id`

- **Type:** string
- **Format:** `kernel_<8-char-hash>` (deterministic from structural_formula + created_at)
- **Mutability:** Frozen at creation
- **Downstream consumers:** all (join key)

### `title_working`

- **Type:** string
- **Mutability:** Editable
- **Length:** 5-30 chars
- **Purpose:** human-readable label, not final title

### `strata_layers` (array, REQUIRED)

- **Type:** array of objects
- **Length:** 1-3 (4+ discouraged, see multi-strata-resonance.md)
- **Each entry schema:**

```json
{
  "layer": "L1",
  "layer_name": "制度地层 / Institutional",
  "analysis": "<natural_language_analysis>",
  "evidence_sources": [
    {
      "source": "<title>",
      "url": "<url>",
      "accessed_date": "YYYY-MM-DD",
      "evidence_strength": "high|medium|low"
    }
  ],
  "structural_question": "<question_from_strata_guide>",
  "answer": "<answer_to_question>"
}
```

**Required sub-fields:** `layer`, `layer_name`, `analysis`, `evidence_sources[]`, `structural_question`, `answer`.

### `structural_formula` (REQUIRED)

- **Type:** string
- **Length:** 50-200 chars
- **Format:** single sentence
- **Content:** describes the irreducible structural conflict in concrete terms
- **Mutability:** Frozen once kernel is consumed downstream
- **Validation:** must contain at least 1 structural force (L1-L5) AND 1 human consequence

**Examples:**
- ✅ "灵活就业者获得了'选择自由'的承诺,但每个选择都通向更深的脆弱;他们的劳动结晶被'人才引进'政策重新分配给本就拥有更多资本的人。"
- ❌ "现代社会让人很焦虑" (too abstract)
- ❌ "灵活就业者的故事" (no structural conflict)

### `strata_overlay_coefficient`

- **Type:** float
- **Range:** 1.0-3.0
- **Default:** 1.0 (single layer)
- **Mutability:** Computed from layer combination, not directly editable
- **Source:** per [`./multi-strata-resonance.md`](./multi-strata-resonance.md)

### `overlay_amplification`

- **Type:** string
- **Length:** 30-150 chars
- **Purpose:** explains why the multi-layer overlay produces > 1+1 resonance

### `unspeakability_score`

- **Type:** integer
- **Range:** 1-10
- **Default:** computed from breakdown
- **Source:** per [`./unspeakability-protocol.md`](./unspeakability-protocol.md)

### `unspeakability_breakdown`

- **Type:** object
- **Required sub-fields:**
  - `political_sensitivity`: 1-10
  - `platform_algorithm_risk`: 1-10
  - `audience_discomfort`: 1-10
  - `regulatory_redline`: 1-10

**Aggregate score = weighted average:**
```
unspeakability_score = round(
  political_sensitivity * 0.20 +
  platform_algorithm_risk * 0.30 +
  audience_discomfort * 0.15 +
  regulatory_redline * 0.35
)
```

### `platform_compliance_paths`

- **Type:** object keyed by platform name
- **Each value:** string describing the compliance strategy for that platform
- **Required keys (CN platforms):** `douyin`, `kuaishou`, `xiaohongshu`, `wechat_mini`
- **Optional keys:** `bilibili`, `youtube_shorts`, `tiktok_us`

### `dramatic_potential`

- **Type:** object
- **Required sub-fields (each 0.0-1.0):**
  - `actionability` — how easily converts to specific scenes
  - `emotional_intensity` — how strong the audience emotional response
  - `narrative_compression_fit` — how well fits短剧 60-180s format
  - `overall` — weighted average

**Weights:**
```
overall = actionability * 0.40 +
          emotional_intensity * 0.35 +
          narrative_compression_fit * 0.25
```

### `target_audience_overlap`

- **Type:** object
- **Required sub-fields (each 0.0-1.0):**
  - `male_18_25`, `male_25_35`, `male_35_50`
  - `female_18_25`, `female_25_35`, `female_35_50`

### `downstream_consumers`

- **Type:** array of strings (expert_ids)
- **Default:** `["style_genome", "screenplay", "topic_curator", "compliance_marketing"]`

### `created_at`

- **Type:** string (ISO 8601 timestamp)

### `evidence_strength_aggregate`

- **Type:** string enum
- **Values:** `"high"` / `"medium-high"` / `"medium"` / `"low"` / `"none"`
- **Computation:** aggregate of `strata_layers[].evidence_sources[].evidence_strength`
  - All high → "high"
  - Mix of high + medium → "medium-high"
  - All medium → "medium"
  - Any low → "low"
  - Empty evidence_sources → "none" (degraded mode)

## Validation rules

A StoryKernel JSON is valid if:

- [ ] `kernel_id` matches `kernel_<8-char-hash>` format
- [ ] `strata_layers` has 1-3 entries
- [ ] Each strata_layers entry has `layer` matching L1-L6
- [ ] Each strata_layers entry has ≥ 1 evidence_sources entry
- [ ] `structural_formula` is 50-200 chars single sentence
- [ ] `strata_overlay_coefficient` matches layer combination (per [`./multi-strata-resonance.md`](./multi-strata-resonance.md))
- [ ] `unspeakability_score` is 1-10 integer
- [ ] `unspeakability_breakdown` has all 4 sub-fields populated
- [ ] `platform_compliance_paths` has all 4 required CN platforms
- [ ] `dramatic_potential.overall` matches weighted average computation
- [ ] `target_audience_overlap` has all 6 demographic segments
- [ ] `evidence_strength_aggregate` matches `strata_layers[].evidence_sources` aggregate

## VETO conditions

A StoryKernel is rejected (cannot be consumed downstream) if:

- ❌ `unspeakability_score ≥ 9` — cannot be made on any major CN platform
- ❌ `evidence_strength_aggregate = "none"` — no data sources, pure speculation
- ❌ `dramatic_potential.overall < 0.40` — too weak to dramatize
- ❌ `target_audience_overlap` max < 0.50 — no clear audience
- ❌ `strata_layers.length ≥ 4` — narrative overload

## Downstream consumption contracts

### style_genome consumption

1. Read `structural_formula` + `target_audience_overlap` to inform genre/mood
2. Read `unspeakability_score` to constrain tone (high score → more allegorical)
3. Output StyleGenome JSON

### screenplay consumption

1. Read `strata_layers[].analysis` to inform character motivations
2. Read `dramatic_potential.actionability` to set scene density
3. Read `structural_formula` as the unifying theme
4. Output script.json with explicit value-shifts aligned to structural_formula

### compliance_marketing consumption

1. Read `unspeakability_breakdown` to identify risk dimensions
2. Read `platform_compliance_paths` for distribution strategy
3. Output compliance report + per-platform reframing recommendations

## Backward compatibility

A legacy StoryKernel (pre-multi-strata) lacks:
- `strata_overlay_coefficient` — default to 1.0 (single layer)
- `unspeakability_breakdown` — default to flat scoring
- `platform_compliance_paths` — empty object, downstream must scan fresh
- `evidence_strength_aggregate` — default to "low"

**Migration path:** creative_source accepts legacy input, upgrades to v1.0.0 output.

---

## Cross-references

- [`./strata-guide.md`](./strata-guide.md) — `strata_layers[]` content source
- [`./multi-strata-resonance.md`](./multi-strata-resonance.md) — `strata_overlay_coefficient` source
- [`./unspeakability-protocol.md`](./unspeakability-protocol.md) — `unspeakability_*` source
