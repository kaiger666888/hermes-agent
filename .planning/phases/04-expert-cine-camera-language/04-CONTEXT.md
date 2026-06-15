# Phase 4: EXPERT-CINE (Camera Language) — Context

**Phase:** 4
**Goal:** Build the cinematographer expert end-to-end so the suite has a unified 镜头语言 expression layer integrating with scene_builder (feasibility), animator (execution), and editor (180° axis compliance).
**Mode:** Direct execution per `/goal` directive (skip strict GSD process)
**Depends on:** Phase 3 (stable contracts for colorist + editor; screenplay emotion_curve schema in place)

## Phase Boundary

This phase produces ONE new expert: **cinematographer**. The handoff boundaries with adjacent experts MUST be documented BEFORE writing SKILL.md (per ROADMAP Phase 4 success criterion #4 + Phase 0 PITFALLS warning):

| Expert | Role | Handoff with cinematographer |
|--------|------|------------------------------|
| **cinematographer** | INTENT | What shot do we want + why? Shot type / framing / angle / camera move / motivation. **Owns the "shot list" semantic layer.** |
| **scene_builder** | FEASIBILITY | Can this shot exist in the 3D scene? Camera blocking / sight lines / asset availability / spatial constraints. **CINE outputs intent → scene_builder validates feasibility.** |
| **animator** | EXECUTION | How does the video gen model produce this motion? Prompt token mapping / model-specific quirks / temporal consistency. **CINE outputs camera-move intent → animator translates to model-specific prompt tokens.** |
| **editor** | COMPLIANCE | Does this shot break 180° axis across cuts? Continuity verification / reaction-shot pacing / cut-density compliance. **CINE outputs axis + screen-direction markers → editor verifies across-cut compliance.** |

**Hard boundary rule:** cinematographer does NOT decide feasibility (scene_builder's job), does NOT execute motion (animator's job), does NOT verify across-cut continuity (editor's job). CINema owns the **semantic shot intent** layer only.

## Deliverables

- `skills/movie-experts/cinematographer/SKILL.md` — bilingual content (EN YAML + CN prose)
- `skills/movie-experts/cinematographer/references/shot-grammar.md` — shot types + composition rules
- `skills/movie-experts/cinematographer/references/axis-rules.md` — 180° axis + 30° rule + screen direction
- `skills/movie-experts/cinematographer/references/vertical-screen-framing.md` — 9:16 vertical 短剧 framing rules
- `skills/movie-experts/cinematographer/references/camera-motion-catalog.md` — camera moves + prompt-token mapping for current video gen models
- `skills/movie-experts/cinematographer/references/LICENSE.md` — fair-use attribution
- `skills/movie-experts/_eval/prompts/cinematographer_demo.yaml` — 3 eval prompts
- related_skills graph updates to 7 experts: scene_builder, animator, editor, screenplay, continuity, drawer, hook_retention

## Success Criteria (per ROADMAP)

1. SKILL.md exists with bilingual content ✓
2. 4 reference files exist (shot-grammar / axis-rules / vertical-screen-framing / camera-motion-catalog) ✓
3. Camera-move → prompt-token mapping documented for current video gen models (Runway / Kling / Veo / Sora) ✓
4. Handoff boundary vs scene_builder/animator/editor documented BEFORE writing SKILL.md ✓ (this file)
5. Edges in related_skills graph to 7 experts ✓

## Implementation Decisions

### D-1: Camera-move prompt-token mapping scope
**Decision:** Document prompt-token mappings for **4 production-grade models** as of 2026-06:
- **Runway Gen-3 Alpha** (Turbo + Lite variants)
- **Kling 1.6** (Pro + Standard)
- **Veo 2** (Google DeepMind)
- **Sora 2** (OpenAI — limited public API as of 2026-06)

**Reasoning:** These 4 are the production-grade models cited most frequently in 2026 短剧 / 微电影 workflows. Excluded: Pika 2.x (lower adoption), MiniMax Hailuo (CN-only), LTX Video (open-weight but lower quality), Haiper (early access).

**Refresh cadence:** `verified_date: 2026-06` stamp; quarterly refresh per Phase 0 PITFALLS warning.

### D-2: Bilingual format
**Decision:** Same as Phase 3 — EN YAML structure + EN metadata + CN descriptive prose. Hermes community compat preserved.

### D-3: expert_id and metrics
**Decision:**
- `expert_id: cinematographer` (frozen; this is a new expert so no backward-compat constraint)
- `metrics: [shot_intent_clarity, axis_compliance, vertical_framing_quality, motion_narrative_fit]`

### D-4: Provider-agnostic RAG invocation
**Decision:** Same Knowledge Retrieval block pattern as Phase 3 experts. Tag queries:
```
tags="expert:cinematographer,domain:shot-grammar"
tags="expert:cinematographer,domain:axis-rules"
tags="expert:cinematographer,domain:vertical-screen-framing"
tags="expert:cinematographer,domain:camera-motion-catalog"
```

## Threats / Risks

- **T-04-01:** Model name drift — Runway/Kling/Veo/Sora versions change quarterly; refs must carry `verified_date` + refresh cadence per Phase 0 PITFALLS.
- **T-04-02:** Boundary bleed — cinematographer attempting feasibility (scene_builder scope) or execution (animator scope). Mitigation: SKILL.md `## What NOT to do` section + explicit handoff protocol.
- **T-04-03:** Vertical-screen framing anti-patterns — applying horizontal 16:9 framing rules to 9:16 短剧 shots. Mitigation: separate ref `vertical-screen-framing.md` with 9:16-specific rules.

## Next Action

Author the 4 refs first → then SKILL.md → then eval prompts → then related_skills graph updates → commit + Phase 4 SUMMARY.
