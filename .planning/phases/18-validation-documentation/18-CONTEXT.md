# Phase 18: Validation + Documentation + Collaboration Graph Update - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning
**Mode:** Auto-generated (validation + finalization phase)

<domain>
## Phase Boundary

Final validation phase for v3.0 milestone. Per ROADMAP §18 success criteria:

1. `grep -r 'expert_id:' skills/movie-experts/ | wc -l` returns 21 (16 active + 5 aliases from rename/merge); no orphan IDs
2. `skills-mapping.yaml` all entries have `sign_off_status: signed_off`
3. `skills/movie-experts/README.md` updated: 26-expert → 21-expert inventory; 18-expert collaboration DAG → v2.0 PRFP topology Mermaid (per `01-NODE-DAG.md` §1.5)
4. `_shared/glossary.md` updated with new terms (visual_executor, audio_pipeline, prompt_injector, continuity_auditor, compliance_gate)
5. `_shared/known-external-models.yaml` updated with Phase 8 §2.17 dated annex models
6. FOUND-08 frozen rule compliance verified: zero silent renames; all aliases explicit
7. Backward compat verified: old expert_id references still resolve via aliases

Operations:
1. **Inventory validation** — enumerate all `expert_id:` declarations; classify each as ACTIVE / ALIAS / DEPRECATED; verify final count = 21 active+aliases
2. **Sign-off verification** — all skills-mapping.yaml entries flipped to `signed_off`
3. **README final form** — 21-expert inventory table + v2.0 PRFP Mermaid DAG (per `01-NODE-DAG.md` §1.5)
4. **Glossary finalization** — verify all 5 new terms present
5. **known-external-models.yaml** — add dated annex models from Phase 8 §2.17
6. **FOUND-08 audit** — verify all aliases explicit, zero silent renames
7. **Backward compat test** — verify old expert_id references resolve via aliases (e.g., consumer referencing `continuity` still works via `continuity_auditor.aliases`)

Out-of-scope: anything beyond v3.0 ROADMAP §18.

</domain>

<decisions>
## Implementation Decisions

### Validation Pattern
- **Source-of-truth:** `.planning/research/v2-pipeline-design/01-NODE-DAG.md` §1.5 (canonical DAG topology)
- **Inventory classification:**
  - **ACTIVE (16):** The canonical 16 DAG pipeline-roles per nodes.yaml — screenplay, cinematographer, character_designer, creative_source, prompt_injector, visual_executor, audio_pipeline, colorist, editor, continuity_auditor, compliance_gate, hook_retention, theory_critic, script_auditor, style_genome, + 1 TBD (likely production or animation_studio depending on DAG)
  - **ALIASES (5):** From renames/merges — continuity (→continuity_auditor), compliance_marketing (→compliance_gate), drawer+animator (→visual_executor), voicer+lip_sync+composer+foley+mixer+spatial_audio (→audio_pipeline). ROADMAP target is 5 aliases; actual count after Phase 13-15 may be more — Phase 18 reconciles.
  - **DEPRECATED (3):** performer, scene_builder, storyboard_designer — NOT counted in 21-expert active inventory per ROADMAP §18 criterion #1
- **ROADMAP §18 criterion #1 explicitly says "21 (16 active + 5 aliases)"** — Phase 18 must reconcile to this target or document why the actual count differs (e.g., if audio_pipeline merge preserved 6 aliases instead of 5)

### README Final Form
- 21-expert inventory table (currently shows 26 → 18 → must become 21)
- Replace ASCII DAG with **Mermaid** DAG per `01-NODE-DAG.md §1.5`
- Footer count updated to "21 active expert inventory (16 DAG pipeline-roles + 5 aliases from rename/merge) + 3 deprecated experts preserved for backward compat"

### known-external-models.yaml Annex
- Per Phase 8 §2.17 (dated annex models) — add new entries with `verified_date: 2026-06-17` for current model versions:
  - FLUX 2 (visual_executor drawer sub-step)
  - Veo / Kling 2.0 (visual_executor animator sub-step)
  - CosyVoice 2 / ElevenLabs v3 (audio_pipeline voicer sub-step)
  - Suno V5 / Udio 2 (audio_pipeline composer sub-step)
  - Stable Audio Open (audio_pipeline foley sub-step)
  - Template + few-shot (prompt_injector)

### Claude's Discretion
- Exact 21-expert inventory classification (which 16 are DAG-active vs which are aliases) — let the canonical mapping in skills-mapping.yaml drive this
- Mermaid DAG syntax details (boxes, edges, styling)
- known-external-models.yaml exact entry format

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v2-pipeline-design/01-NODE-DAG.md` §1.5 — canonical Mermaid DAG
- `.planning/research/v2-pipeline-design/skills-mapping.yaml` — final mapping (lines 1-138)
- Phase 13-17 SUMMARYs — all changes documented
- `skills/movie-experts/_shared/known-external-models.yaml` — existing annex to update

### Established Patterns (cumulative from Phases 13-17)
- ROADMAP.md progress tracking + checkboxes
- STATE.md phase status updates
- REQUIREMENTS.md traceability table
- skills-mapping.yaml sign_off_status field
- README inventory + corpus tree + DAG diagram conventions
- _shared/glossary.md H3 entry pattern

### Integration Points
- 31 expert_id declarations currently exist (per pre-Phase-18 grep)
- Target is 21 (16 active + 5 aliases) per ROADMAP §18 criterion #1
- 3 deprecated IDs (performer, scene_builder, storyboard_designer) are preserved but NOT counted in 21
- The remaining 31 - 21 - 3 = 7 discrepancy is likely from redirect stubs preserving OLD expert_ids (continuity, compliance_marketing, drawer, animator, voicer, lip_sync, composer, foley, mixer, spatial_audio = 10 stubs, not 5 aliases). ROADMAP §18 may need clarification — Phase 18 documents the actual count and explains the discrepancy.
- README.md needs Mermaid DAG conversion
- Glossary needs verification of 5 new terms (continuity_auditor, compliance_gate, visual_executor, audio_pipeline, prompt_injector)

</code_context>

<specifics>
## Specific Ideas

- ROADMAP §18 criterion #1: 21 expert_id inventory (16 active + 5 aliases)
- ROADMAP §18 criterion #2: all skills-mapping.yaml entries sign_off_status: signed_off
- ROADMAP §18 criterion #3: README updated to 21-expert inventory + v2.0 PRFP Mermaid DAG
- ROADMAP §18 criterion #4: glossary has 5 new terms
- ROADMAP §18 criterion #5: known-external-models.yaml updated with Phase 8 §2.17 dated annex models
- ROADMAP §18 criterion #6: FOUND-08 frozen rule compliance verified (zero silent renames; all aliases explicit)
- ROADMAP §18 criterion #7: Backward compat verified (old expert_id references resolve via aliases)
- ROADMAP §18 is **integration gate** — validates all 13-17 work meets FOUND-08 + backward compat + collaboration graph coherence

</specifics>

<deferred>
## Deferred Ideas

None — final validation phase, scope tightly bounded by ROADMAP §18.

</deferred>
