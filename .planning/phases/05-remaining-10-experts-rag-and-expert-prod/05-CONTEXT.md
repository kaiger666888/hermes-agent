# Phase 5: Remaining 10 Experts RAG + EXPERT-PROD (v1.5) — Context

**Phase:** 5
**Goal:** Refactor the remaining 10 existing experts based on AUDIT-01 classification (needs-deep-refs / needs-light-refs / needs-no-refs) and build the production expert (AI-relevant subset only).
**Mode:** Direct execution per `/goal` directive (skip strict GSD process)
**Depends on:** Phase 4 (GO gate — but per /goal directive, we proceed without waiting for Phase 6 live-run evidence; operator can scrap Phase 5 outputs later if Phase 6 GO verdict is NO-GO)

## Phase Boundary

Phase 5 has two parts:

### Part A: Production Expert (PROD) — NEW EXPERT
Build `skills/movie-experts/production/` end-to-end:
- SKILL.md (bilingual, AI-relevant subset only — NO live-action crews/permits/insurance per PROD-07)
- 5 refs:
  - `casting-lora-spec.md` (character LoRA / reference image spec) — PROD-02
  - `wardrobe-per-scene.md` (per-scene wardrobe spec feeding continuity) — PROD-03
  - `lighting-intent-layer.md` (lighting intent handoff) — PROD-04
  - `gpu-render-budget.md` (character-LoRA cost estimation, render-farm heuristics) — PROD-05
  - `asset-reuse-plan.md` (cross-shot/episode asset batching) — PROD-06
- 3 eval prompts (`production_demo.yaml`)
- related_skills graph updates to: performer, drawer, animator, scene_builder, continuity, colorist, compliance_marketing

### Part B: 10 Existing Experts RAG Uplift
Per REFACTOR-rest-01..10. Each expert gets:
- **2-3 light refs** (10-15 KB each) based on GAP-REPORT §missing_refs_topics
- **SKILL.md refactor:** References table + Knowledge Retrieval block + inline citations
- **Phantom ref strips** where still present:
  - `drawer/SKILL.md`: strip residual FLUX 1.x sampler params
  - `foley/SKILL.md`: replace AudioLDM-2 → Stable Audio Open 1.0
  - `voicer/SKILL.md`: replace CosyVoice → MiniMax / ElevenLabs / Mistral Voxtral (provider-agnostic placeholder)

## Experts + Refs Plan

| Expert | Tier | Refs to author | Key sources |
|--------|------|----------------|-------------|
| `animator` | light-refs | 1. video-gen-model-matrix.md (Runway/Kling/Veo/Sora/LTX/Pixverse behavior matrix)<br>2. temporal-consistency.md (CLIP-T, LPIPS, character ID preservation) | Runway/Kling/Veo/Sora docs (2026-06), CLIP-T literature |
| `composer` | light-refs | 1. musicgen-workflow.md (MusicGen-large + AudioLDM-2 melody conditioning)<br>2. chion-audio-vision.md (Chion acousmatic + 5 audio-vision modes)<br>3. scoring-on-the-track.md (Hickman & Huckle scoring craft) | MusicGen docs, Chion *Audio-Vision* (1994), Hickman *On the Track* (4th ed) |
| `continuity` | light-refs | 1. cross-shot-auditing.md (face/color/style/object matching heuristics)<br>2. eyeline-match-protocol.md (Hitchcock rule + 180° continuity across cuts) | Reisz & Millar 1968, Dmytryk 1984 |
| `drawer` | light-refs | 1. flux2-parameter-surface.md (FLUX 2 klein 9B + step/guidance defaults)<br>2. character-consistency-lora.md (LoRA training + IP-Adapter + InstantID) | FLUX 2 docs (fal-ai), LoRA training guides |
| `foley` | light-refs | 1. stable-audio-open.md (Stable Audio Open 1.0 workflow + 7D parametric design)<br>2. sound-effect-taxonomy.md (BBC Sound Library + freesound.org taxonomy) | Stable Audio Open 1.0 docs, BBC SE taxonomy |
| `mixer` | light-refs | 1. mixing-secrets-small-studio.md (Mike Senior LUFS + dialogue ducking + EQ carving)<br>2. lufs-standards.md (ITU-R BS.1770 + platform targets) | Senior *Mixing Secrets for the Small Studio* (2nd ed), ITU-R BS.1770-4 |
| `performer` | light-refs | 1. stanislavski-prepares.md (Stanislavski ExBxSxP + Laban effort analysis)<br>2. meisner-truth.md (Meisner repetition + truth-of-moment) | Stanislavski *An Actor Prepares* (1936), Meisner *On Acting* (1987) |
| `scene_builder` | light-refs | 1. blender-previz-workflow.md (Blender 4.x previz + camera blocking)<br>2. architectural-storytelling.md (FxSxA scene matrix + space-as-character) | Blender 4.x docs, Bordwell *Film Art* §space |
| `spatial_audio` | light-refs | 1. dolby-atmos-workflow.md (Atmos renderer + 6D encoding + bed + objects)<br>2. immersive-sound-design.md (3D sound field + HRTF + binaural) | Dolby Atmos spec, AES papers on HRTF |
| `voicer` | light-refs | 1. cn-tts-model-matrix.md (MiniMax / ElevenLabs / Mistral Voxtral / Gemini / Edge / NeuTTS)<br>2. character-voice-consistency.md (speaker embedding + voice cloning protocol) | Provider docs (2026-06), speaker-verification literature |

**Total Phase 5 refs:** 22 (across 10 experts) + 5 (production) = **27 new refs**

## Implementation Decisions

### D-1: Ref depth
**Decision:** 2-3 refs per existing expert (10-15 KB each, lighter than Phase 3's 5 refs × 20-30 KB each).

**Reasoning:** Phase 5 is v1.5 polish. The Phase 3 deep refactor (5 refs × 4 experts) is the credibility anchor. Phase 5 brings the remaining 10 experts up to "RAG-aware" baseline without the depth investment of Phase 3. Operator can deepen specific experts later if Phase 6 live eval shows they underperform.

### D-2: Eval prompts
**Decision:** No new eval prompts for the 10 existing experts (Phase 6 already has prompts from Phase 1-4). Production expert gets 3 new prompts.

**Reasoning:** REFACTOR-rest-01..10 don't require eval prompts. The 10 existing experts already have placeholder prompts in `_eval/baseline/` (Phase 0 snapshot). Production expert is NEW and needs prompts per Phase 1-4 pattern.

### D-3: Phantom strip approach
**Decision:** Replace hard-coded model names with provider-agnostic placeholders OR allowlist references.

**Examples:**
- `AudioLDM-2 (primary)` → `Stable Audio Open 1.0 (primary)` (Hermes ships this)
- `CosyVoice-300M` → `<tts_primary>` placeholder + ref `cn-tts-model-matrix.md` lists actual Hermes-catalog TTS
- FLUX 1.x samplers → strip entirely (FLUX 2 doesn't use Karras samplers)

### D-4: Production expert boundary
**Decision:** Production expert owns **AI-relevant subset only** — character LoRA / wardrobe / lighting intent / GPU budget / asset reuse. Live-action subset (crews, permits, insurance) explicitly excluded per PROD-07 (deferred to v2).

## Threats / Risks

- **T-05-01:** Phase 6 live-run GO verdict may be NO-GO (Phase 3 RAG uplift statistically insignificant). If so, all 10 RAG uplifts in Phase 5 are wasted effort. **Mitigation:** Per /goal directive, proceed anyway; operator can scrap later. Production expert is shippable regardless (it's a NEW expert, not a refactor).
- **T-05-02:** GLM overload (Phase 0 PITFALLS #4 — 2/4 mapper failures). Phase 5 authors 22+ refs sequentially in main worktree, no parallel subagent dispatch. **Mitigation:** Already accounted for in /goal execution mode.
- **T-05-03:** Model drift for voicer/foley refs (TTS / audio gen models evolve fast). **Mitigation:** All refs carry `verified_date: 2026-06` stamp; quarterly refresh per Phase 0 convention.

## Next Action

1. Part A: Build production expert (5 refs + SKILL.md + 3 prompts)
2. Part B: For each of 10 experts → author 2-3 refs → refactor SKILL.md → strip phantom refs
3. Update README + STATE + ROADMAP
4. Phase 5 SUMMARY
