# Phase 71: FORM - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning
**Mode:** Smart Discuss (autonomous)

<domain>
## Phase Boundary

Users can author a kais-movie-pipeline project in either landscape 16:9 or portrait 9:16 form factor, with the pipeline reading `form_factor` as a first-class project meta and each expert emitting form-aware creative rules instead of hardcoded `9:16` assumptions.

This is the foundational track of v14.0 — every other track (DUB, IMG, TRANSITION) consumes `form_factor` for render resolution, framing rules, and transition composition. Cross-repo: code lives in `kais-hermes-skills`, only lineage bump (Phase 75) touches `hermes-agent`.

Requirements covered: FORM-01 (PipelineState.form_factor), FORM-02 (15 SKILL.md `## Form Factor Adaptation`), FORM-03 (`horizontal-screen-framing.md` ref), FORM-04 (Step 14 4-cell reframe matrix), FORM-05 (stale MSR_FC=17→41 fix).

**Out of scope (v15+ per REQUIREMENTS):** FORM-06 per-shot form_factor override; FORM-07 auto-form_factor inference from screenplay.

</domain>

<decisions>
## Implementation Decisions

### Schema Field Naming & Values (FORM-01)
- **Field name:** `form_factor` on `PipelineState` dataclass in `kais-hermes-skills/plugins/pipeline_state/store.py`. Matches REQUIREMENTS / ROADMAP prose. Reject alternatives (`aspect_ratio`, `frame_orientation`).
- **Enum values:** `Literal["landscape", "portrait"]` — semantic-clean, dimensions derived downstream (LTX-MSR template resolves `landscape → width=1280 height=704` / `portrait → width=704 height=1280`). REJECT REQUIREMENTS literal `"landscape_16_9"` / `"portrait_9:16"` — too verbose, the form IS the semantic, ratio is a derived rendering concern. (REQUIREMENTS prose at FORM-01 line uses the verbose form as illustration; ARCHITECTURE research and downstream consumers all use the short form. Plan-phase researcher must reconcile REQUIREMENTS wording with this decision: the verbose strings remain valid documentation aliases but the canonical schema field uses short strings.)
- **Default:** `"portrait"` — backwards-compatible with all existing 短剧 projects (v1-v13 all 9:16). REJECT ARCHITECTURE research slip-up suggesting `"landscape"` default — that would silently flip form on every existing episode.
- **Validation:** Pydantic `Literal["landscape", "portrait"]` strict enum. Unknown values raise `ValidationError` at parse time. No fuzzy matching, no warnings-and-continue.

### 15-Expert Rollout Decomposition (FORM-02)
- **Plan shape:** 3 plans, NOT 1 mega-plan and NOT 5+ micro-plans.
  - **Plan A (Foundation):** `PipelineState.form_factor` dataclass migration + `references/horizontal-screen-framing.md` authoring + LTX-MSR template `form_factor → resolution` switch + incidental MSR_FC=17→41 fix at `kais-movie-pipeline/SKILL.md:446`. (FORM-01, FORM-03, FORM-05, partial FORM-02 infrastructure)
  - **Plan B (15 SKILL.md patches):** `## Form Factor Adaptation` section added to 15 active movie-expert SKILL.md files, tiered by form-criticality. (FORM-02)
  - **Plan C (Step 14 matrix):** 4-cell reframe matrix in `references/platform-master-slicing.md` + cinematographer Step 3 dispatch + unit tests. (FORM-04)
- **Tiering inside Plan B (per PITFALL F-3 — forcing form_factor into form-agnostic experts is scope creep):**
  - **Tier 1 (form-critical, substantive dual-branch ~15-30 lines):** cinematographer, drawer, visual_executor, scene_builder, editor (5 experts — those that directly produce framing/scale/axis decisions)
  - **Tier 2 (form-aware, short dual-branch ~5-10 lines):** continuity_auditor, continuity, storyboard_designer, hook_retention, compliance_gate, physics_precheck, production_designer (7 experts — those whose rules shift slightly between forms)
  - **Tier 3 (form-agnostic, explicit stub ~3 lines):** the remaining 3 of 15 active experts (audio_pipeline, composer, colorist, etc. — pure sound/color work that doesn't read frame geometry) — stub says `## Form Factor Adaptation\n\nThis expert is form-agnostic; no form-specific rules required.`
- **FORM-02 success criteria interpretation:** Stub section counts as "has section" for Tier 3 experts. Substantive dual-branch content required for Tier 1 + Tier 2.
- **Atomic commit granularity:** Per-tier commit in Plan B (3 commits — `feat(71-B): form-critical tier dual-branch` / `feat(71-B): form-aware tier dual-branch` / `feat(71-B): form-agnostic tier stub section`).

### `horizontal-screen-framing.md` Authoring (FORM-03)
- **Document structure:** Mirror `vertical-screen-framing.md` 5-section structure (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region) — required by FORM-03 literal success criteria.
- **Cinematographer SKILL.md dispatch:** Step 3 (Composition per Shot) branches on `form_factor` and loads either `vertical-screen-framing.md` or `horizontal-screen-framing.md` — per PITFALL F-1 mitigation #3.
- **Content depth:** Full 5-dim treatment with real film citations (e.g., "1917" long-take horizontal track for eye-trace region; "Revenant" wide landscape for shot-scale distribution; "Grand Budapest Hotel" symmetry for power points). Consistent with v1-v5 methodology of citing real films.
- **Citation / copyright:** Cite professional cinematography books (Blain Brown "Cinematography: Theory and Practice", Gustavo Mercado "The Filmmaker's Eye") under fair-use with full source attribution per CLAUDE.md copyright constraint.

### Step 14 4-Cell Reframe Matrix (FORM-04)
- **Coverage:** Add explicit 4-cell matrix section to `kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md`. Per-cell rules:
  - **portrait → portrait:** pass-through (lossless)
  - **landscape → landscape:** pass-through (lossless)
  - **portrait → landscape:** letterbox OR reframe from 9:16 vertical keyframe (operator config)
  - **landscape → portrait:** center-crop + saliency scan (preserve top-2/3 primary info per existing ref line 74 — swipe gesture zone avoidance)
- **Verification:** Unit test on reframe math (crop coordinates) per cell + 1 sample-frame per cell committed under `_eval/form_factor_step14/` (4 cells × before/after = 8 frames total).
- **Regression coverage:** Existing vertical-master behavior = cell [portrait → portrait] now made explicit. Existing tests preserved (do NOT rewrite as part of matrix abstraction — high regression risk for low abstraction value).

### MSR_FC=17→41 Incidental Fix (FORM-05)
- **Scope:** Single-line fix at `kais-movie-pipeline/SKILL.md:446` — change `MSR_FC=17` to `MSR_FC=41` per 2026-07-01 A/B test (per SUMMARY research reconciliation #5, this is canonical value).
- **Propagation:** Audit other refs that may cite MSR_FC=17 — if found, fix together in same commit. (Plan A executor verifies with `grep -rn "MSR_FC=17" /data/workspace/kais-hermes-skills/`.)
- **Commit message:** `fix(71-A): correct stale MSR_FC=17 → 41 per 2026-07-01 A/B test (FORM-05)`

### Claude's Discretion
- Exact wording of each SKILL.md `## Form Factor Adaptation` section body (within tier depth guidelines above).
- Choice of which 3 of the 15 active experts land in Tier 3 (form-agnostic) — default: any expert whose entire output is sound (audio_pipeline, composer, voicer, foley, mixer, spatial_audio, lip_sync) or pure color (colorist). Plan B researcher verifies each expert's output has zero frame-geometry dependence before classifying as Tier 3.
- Exact 8 sample-frame fixtures for Step 14 matrix verification (use existing project assets where possible).
- Test framework (pytest vs standalone script) — match existing `_eval/` conventions.
- Whether to add an integration test that runs one shot landscape + one portrait through cinematographer and checks different `power_point` values — RECOMMENDED per PITFALL F-1 mitigation #4 detection guidance.

</decisions>

<canonical_refs>
## Canonical Refs (Phase 71 downstream agents MUST read)

All paths are relative to repo roots (`/data/workspace/hermes-agent/` for GSD planning; `/data/workspace/kais-hermes-skills/` for code + refs).

**Hermes-agent repo (GSD planning context):**
- `.planning/ROADMAP.md` — Phase 71 section (lines 44-58)
- `.planning/REQUIREMENTS.md` — FORM-01..05 (lines 18-26)
- `.planning/research/v14-4track-upgrade/SUMMARY.md` — reconciliation #5 (MSR_FC value), phase ordering rationale
- `.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — Pattern 1 (Schema Migration with Defaults), Anti-Pattern 1 (Per-Shot form_factor), FORM track touch points table
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — F-1 (vertical-only ref), F-2 (Step 14 matrix), F-3 (form-agnostic experts), X-1 (lineage cascade), X-2 (META-RULE _INSTRUCTION)
- `.planning/research/v14-4track-upgrade/FEATURES.md` — FORM feature landscape, anti-features (per-shot mixing, auto-inference)
- `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` — baseline sha256 for 6 SKILL.md files (Phase 75 delta anchor)

**Kais-hermes-skills repo (code + refs — READ before editing):**
- `plugins/pipeline_state/store.py` — `PipelineState` dataclass, `_STATE_FIELDS` auto-derivation (form_factor field auto-whitelists)
- `skills/kais-movie-pipeline/SKILL.md` — line 40 ("vertical 9:16" hardcoded), line 268 (framing 9:16), line 283 (Step 14 contract), line 446 (MSR_FC=17 STALE — fix to 41)
- `skills/kais-movie-pipeline/references/platform-master-slicing.md` — Step 14 4-cell matrix insertion point (lines 33-74 document current 7-variant / 3-aspect-ratio behavior)
- `skills/movie-experts/cinematographer/SKILL.md` — 28 vertical/9:16 refs; Step 3 (Composition per Shot) dispatch insertion point
- `skills/movie-experts/cinematographer/references/vertical-screen-framing.md` — 5-section structure to mirror (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region)
- 15 active movie-expert SKILL.md files — list maintained in `_shared/active-experts.md` (Plan B researcher enumerates exact paths)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PipelineState` dataclass + `_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())` auto-derivation pattern — adding a field with default value is safe; existing episode JSON loads cleanly (ARCHITECTURE Pattern 1).
- `references/platform-master-slicing.md` already documents 7 platform variants with 3 aspect ratios (lines 33-50) — Step 14 4-cell matrix extends this, does NOT replace it.
- `references/vertical-screen-framing.md` 5-section structure is the template for `horizontal-screen-framing.md` (FORM-03 success criteria literal).
- LTX-MSR template (`ltx_msr_batch_render.py`) already accepts `--width` / `--height` — form_factor → resolution mapping is a thin switch.
- Pydantic `Literal[a, b]` strict enum pattern — already used elsewhere in pipeline_state (per ARCHITECTURE research).

### Established Patterns
- **Schema migration with defaults:** Adding fields to `PipelineState` defaults to current behavior — pattern established in v9.0 P38 (Step 14 platform variants).
- **SKILL.md `## Form Factor Adaptation` section convention:** New convention established by this phase. Mirrors `## When to use this skill` / `## Role & Philosophy` style — top-level H2 section.
- **Cross-repo split:** Code + refs in `kais-hermes-skills`, GSD planning in `hermes-agent`. Hermes-agent touches NOTHING in Phase 71 except `.planning/` (lineage bump is Phase 75).
- **Per-tier commit granularity:** Matches v13.0 P62 transform flow pattern (commits grouped by logical tier, not per-file).

### Integration Points
- `PipelineState.form_factor` propagates to:
  - Each expert invocation context (delegated via `delegate_task` — Plan A adds the field to the context dict)
  - LTX-MSR render params (Plan A: template resolution switch)
  - Step 14 platform slicing (Plan C: 4-cell matrix consumer)
  - Drawer image dimensions (Plan B Tier 1: drawer SKILL.md dual-branch)
- `references/horizontal-screen-framing.md` loaded by cinematographer Step 3 when `form_factor == "landscape"` (Plan A: dispatch logic; Plan B Tier 1: cinematographer SKILL.md edit).

</code_context>

<specifics>
## Specific Ideas

- **MSR_FC fix scope:** Single-line at `kais-movie-pipeline/SKILL.md:446` is the floor. Plan A executor should grep for other MSR_FC=17 occurrences and fix together if found (likely candidates: `ltx_msr_batch_render.py` template, any `_eval/` fixtures, any `references/*.md` citing the stale value).
- **Citation discipline for `horizontal-screen-framing.md`:** Per CLAUDE.md copyright constraint, every citation needs source + copyright status. Use real films under fair-use (analysis/discussion context) and professional cinematography books with full bibliographic attribution.
- **Form-factor-as-episode-invariant enforcement:** Per ARCHITECTURE Anti-Pattern 1 — pipeline boot validates the invariant (no per-shot mixing). Plan A should include a validator that rejects episode JSON with per-shot `form_factor` overrides. Detection: scan shot list for field; reject if any shot has it.
- **Pipeline orchestrator (`kais-movie-pipeline/SKILL.md`) propagation:** Line 40 "Pipeline form" section must be updated to read `form_factor` from PipelineState, drop the "All 15 movie-experts assume this form" claim. Plan A includes this line edit (not deferred to Plan B — Plan A owns the schema + propagation contract).

</specifics>

<deferred>
## Deferred Ideas

- **FORM-06 (per-shot form_factor override):** Explicitly out-of-scope per REQUIREMENTS (anti-pattern — cross-shot consistency collapse risk). Deferred to v15+ if real use case emerges.
- **FORM-07 (auto-form_factor inference from screenplay):** Out-of-scope — unreliable (~40% wrong per FEATURES research). Operator declares at project creation.
- **LTX-MSR landscape-template evaluation:** Whether landscape_16_9 needs different sigmas / sampler / cfg values than portrait is a v15+ tuning concern. v14.0 reuses current LTX params with only `width`/`height` swapped.
- **Step 14 saliency-scan implementation details:** The center-crop + saliency scan algorithm for landscape→portrait cell is documented at the contract level in `platform-master-slicing.md`; the actual saliency detector (GLM-4.6V vs OpenCV vs simple histogram) is plan-phase researcher's call. Not a gray area for this discuss.
- **15-expert production tuning post-rollout:** Real-world production data on which Tier 2/3 experts need promotion to Tier 1 (or vice versa) — defer to v15+ operator feedback loop per EVAL-06.

</deferred>
