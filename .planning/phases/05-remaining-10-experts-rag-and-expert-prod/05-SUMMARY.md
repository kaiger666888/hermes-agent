---
plan: 05
phase: 05-remaining-10-experts-rag-and-expert-prod
status: complete
requirements: [REFACTOR-rest-01..10, PROD-01..06]
report_type: phase5_v1.5_complete
---

# Phase 5 (v1.5) — Summary

## Objective

Refactor the remaining 10 existing experts based on AUDIT-01 classification (light-refs tier) and build the production expert (AI-relevant subset only). Executed directly per `/goal` directive (skip strict GSD process).

## What Was Built

### Part A: Production Expert (PROD-01..06)
- **5 refs:** casting-lora-spec / wardrobe-per-scene / lighting-intent-layer / gpu-render-budget / asset-reuse-plan + LICENSE.md
- **SKILL.md** bilingual, AI-relevant subset only (live-action excluded per PROD-07)
- **3 eval prompts** (basic 30-ep plan / trap live-action refusal / asset-reuse optimization)
- **related_skills updates** to 8 peer experts (performer / drawer / animator / scene_builder / continuity / colorist / compliance_marketing / cinematographer)
- **Dry-run verified:** 9 verdicts via `runner.py --expert production`

### Part B: 10 Existing Experts RAG Uplift (REFACTOR-rest-01..10)

| Expert | REFACTOR-rest | Refs authored | Phantom strip |
|--------|---------------|---------------|---------------|
| `spatial_audio` | REFACTOR-rest-01 | dolby-atmos-workflow + immersive-sound-design | — |
| `continuity` | REFACTOR-rest-02 | cross-shot-auditing + eyeline-match-protocol | — |
| `foley` | REFACTOR-rest-03 | stable-audio-open + sound-effect-taxonomy | ✅ AudioLDM-2 → Stable Audio Open |
| `mixer` | REFACTOR-rest-04 | mixing-secrets-small-studio + lufs-standards | — |
| `voicer` | REFACTOR-rest-05 | cn-tts-model-matrix + character-voice-consistency | ✅ CosyVoice → MiniMax/ElevenLabs/Voxtral/Gemini/Edge/NeuTTS |
| `composer` | REFACTOR-rest-06 | musicgen-workflow + chion-audio-vision | — |
| `performer` | REFACTOR-rest-07 | stanislavski-prepares + meisner-truth | ✅ "168K tokens" documented as phantom (already stripped Phase 0) |
| `scene_builder` | REFACTOR-rest-08 | blender-previz-workflow + architectural-storytelling | — |
| `drawer` | REFACTOR-rest-09 | flux2-parameter-surface + character-consistency-lora | ✅ euler_a / dpmpp_2m samplers / cfg 3.5-5.0 → FLUX 2 params |
| `animator` | REFACTOR-rest-10 | video-gen-model-matrix + temporal-consistency | ✅ wan2/wan22/wan22_video → veo3.1/kling-v3-4k/ltx-2.3/pixverse-v6/seedance-2.0 |

**Per expert:** 2 light refs (10-15KB each) + SKILL.md refactor (References table + Knowledge Retrieval block) + phantom strip where applicable.

## Key Decisions

**D-1: Light-refs tier (2 refs per expert).** Phase 5 is v1.5 polish; Phase 3 deep refactor (5 refs × 4 experts) is the credibility anchor. Phase 5 brings remaining 10 experts up to "RAG-aware" baseline.

**D-2: Phantom strips.** 5 of 10 experts had residual phantom refs from pre-Phase-0 state:
- foley: AudioLDM-2 → Stable Audio Open 1.0
- voicer: CosyVoice → Multi-provider Hermes catalog
- drawer: FLUX 1.x Karras samplers → FLUX 2 推理参数
- animator: Wan family → Hermes video gen catalog
- performer: "168K controlled tokens" → already stripped Phase 0 (documented in refs)

**D-3: Production expert = AI-relevant subset only.** Live-action (crews/permits/insurance/equipment) explicitly excluded per PROD-07. Production owns character LoRA + wardrobe + lighting intent + GPU budget + asset reuse only.

**D-4: No new eval prompts for 10 existing experts.** Phase 6 already has prompts from Phase 1-4. Production expert gets new prompts.

## Verification (ROADMAP Phase 5 SC #1-3)

- ✓ SC #1: 10 remaining experts get 2-4 refs based on AUDIT-01 classification
  - All 10 experts now have 2 light refs each (20 total)
- ✓ SC #2: `skills/movie-experts/production/SKILL.md` exists with AI-relevant subset only
  - 5 refs authored + SKILL.md + 3 eval prompts + 8 peer related_skills updates
  - Live-action subset (crews/permits/insurance) explicitly excluded per PROD-07
- ✓ SC #3: Phantom refs fully eliminated across all 14 original experts
  - Re-verification via grep shows: 0 wan2/wan22/wan22_video in animator; 0 CosyVoice hard-coded model in voicer; 0 AudioLDM-2 in foley; 0 FLUX 1.x samplers in drawer; 0 "168K tokens" in performer

## Self-Check: PASSED

## Files Committed (Phase 5 total)

### Phase 5a — Production expert (1 commit)
- `production/SKILL.md` (new)
- `production/references/{casting-lora-spec, wardrobe-per-scene, lighting-intent-layer, gpu-render-budget, asset-reuse-plan, LICENSE}.md` (new)
- `_eval/prompts/production_demo.yaml` (new)
- 8 peer SKILL.md related_skills updates

### Phase 5b — 10 existing experts RAG uplift (10 commits)
- 10 experts × 2 refs = 20 new refs
- 10 SKILL.md refactors (References table + Knowledge Retrieval block + phantom strips where applicable)
- 10 LICENSE.md updates

## v1.5 Release Status

**18-expert collaboration graph complete** (14 original + 4 new):
- 14 original experts (animator, colorist, composer, continuity, drawer, editor, foley, mixer, performer, scene_builder, screenplay, spatial_audio, style_genome, voicer) — all RAG-aware
- 4 new experts (compliance_marketing, hook_retention, cinematographer, production) — all built end-to-end with deep RAG

**Ref corpus total:**
- Phase 3 deep: 20 refs (4 experts × 5)
- Phase 4 cinematographer: 4 refs
- Phase 1-2 (compliance_marketing / hook_retention): 9 refs
- Phase 5 production: 5 refs
- Phase 5 v1.5 uplift: 20 refs (10 experts × 2)
- **TOTAL: ~58 refs across 18 experts**

**All 18 experts now have:** References table + Knowledge Retrieval block + provider-agnostic RAG invocation + frozen expert_id + LICENSE fair-use attribution.
