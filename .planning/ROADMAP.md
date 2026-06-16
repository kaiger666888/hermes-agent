# Roadmap: Movie-Experts Suite v2 — Milestone **v3.0 Skills-to-DAG Alignment**

**Milestone:** v3.0 Skills-to-DAG Alignment
**Defined:** 2026-06-16
**Granularity:** standard
**Phase numbering:** continues from v2.0 (v2.0 ended at Phase 12; v3.0 starts at **Phase 13**)
**Coverage:** 12/12 v3.0 requirements mapped ✓ (0 orphaned)
**Deliverable form:** `skills/movie-experts/` 重构 — rename + merge + new + deprecate experts to align with v2.0 PRFP DAG. ZERO edits to kais-movie-agent/(parallel milestone).

---

## Milestones

- ✅ **v1 — Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15) — [Full archive](./milestones/v1-ROADMAP.md)
- ✅ **v2.0 PRFP — Pipeline Redesign from First Principles** — Phases 7-12 (shipped 2026-06-16) — design suite at `.planning/research/v2-pipeline-design/`
- 🚧 **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (in planning)

---

## v3.0 PRFP Coverage Map (12 requirements mapped)

| Phase | Requirements | Count |
|---|---|---|
| 13 | RENAME-01, RENAME-02 | 2 |
| 14 | MERGE-01 | 1 |
| 15 | MERGE-02 | 1 |
| 16 | NEW-01 | 1 |
| 17 | DEPRECATE-01, DEPRECATE-02, DEPRECATE-03 | 3 |
| 18 | VALIDATE-01, VALIDATE-02, DOC-01, DOC-02 | 4 |
| **Total** | | **12** |

---

## v3.0 Phases

### Phase 13: Expert Rename + Alias Scaffolding

**Goal:** A reader can read `skills/movie-experts/continuity_auditor/SKILL.md` and `skills/movie-experts/compliance_gate/SKILL.md` and find fully renamed experts with backward-compat aliases — old `continuity` and `compliance_marketing` references still resolve (FOUND-08 frozen rule preserved).

**Depends on:** Phase 12 (v2.0 PRFP design shipped; `skills-mapping.yaml` is the canonical source)

**Requirements:** RENAME-01, RENAME-02

**Success Criteria** (what must be TRUE):
1. `skills/movie-experts/continuity_auditor/SKILL.md` exists with `name: continuity_auditor` + `expert_id: continuity_auditor` + `metadata.hermes.aliases: [continuity]`
2. `skills/movie-experts/compliance_gate/SKILL.md` exists with `name: compliance_gate` + `expert_id: compliance_gate` + `metadata.hermes.aliases: [compliance_marketing]`
3. All experts that previously listed `continuity` or `compliance_marketing` in `metadata.hermes.related_skills` have updated to new IDs (bidirectional edge sync)
4. Old directory paths (`continuity/`, `compliance_marketing/`) preserved with redirect SKILL.md (backward compat)
5. `skills-mapping.yaml` `sign_off_status` updated: `pending` → `signed_off` for both renamed entries

**Plans:** 3/3 plans complete

Plans:
- [x] 13-01-PLAN.md — Rename continuity → continuity_auditor (new dir + redirect stub + 17-consumer edge sync)
- [x] 13-02-PLAN.md — Rename compliance_marketing → compliance_gate (new dir + redirect stub + 11-consumer edge sync, depends on 13-01)
- [x] 13-03-PLAN.md — Close-out: skills-mapping.yaml sign_off + README + _shared/glossary.md updates (depends on 13-01 + 13-02)

---

### Phase 14: Visual Executor Merge (drawer + animator)

**Goal:** A reader can read `skills/movie-experts/visual_executor/SKILL.md` and find a unified expert that declares `sub_steps: [drawer, animator]`, with `related_skills` edges inherited from both predecessors, and the old drawer + animator expert_ids preserved as aliases for backward compatibility.

**Depends on:** Phase 13 (rename pattern established + alias scaffolding reusable)

**Requirements:** MERGE-01

**Success Criteria:**
1. `skills/movie-experts/visual_executor/SKILL.md` exists with `sub_steps: [drawer, animator]` declared
2. `metadata.hermes.related_skills` includes union of drawer + animator edges (cinematographer, prompt_injector, continuity_auditor, editor, etc.)
3. Old `drawer/SKILL.md` + `animator/SKILL.md` preserved with `status: merged_into` + `merged_into: visual_executor` + redirect
4. All consumers (other experts' related_skills, README, _eval/, _shared/) updated to reference `visual_executor` instead of drawer/animator
5. Drawer + animator refs (if any in `_shared/project-corpus/`) consolidated or cross-referenced under visual_executor

**Plans:** 3/3 plans

Plans:
- [x] 14-01-PLAN.md — Create visual_executor/ with merged SKILL.md (sub_steps + aliases + unioned related_skills) + refs sub-folders + redirect stubs for drawer/animator (Wave 1)
- [ ] 14-02-PLAN.md — Consumer edge sync: 15 consumer SKILL.md files updated (related_skills dedup + body prose reference sync) (Wave 2, depends on 14-01)
- [ ] 14-03-PLAN.md — Close-out: README inventory + corpus tree + DAG diagram + _shared/ glossary + quality-rubric + RAG-INVOCATION-PATTERN + project-corpus updates (Wave 3, depends on 14-01 + 14-02)

---

### Phase 15: Audio Pipeline Merge (5 audio experts)

**Goal:** A reader can read `skills/movie-experts/audio_pipeline/SKILL.md` and find a unified expert declaring `sub_steps: [voicer, lip_sync, composer, foley, mixer]`, with `spatial_audio` explicitly addressed (folded or deprecated with rationale), and old expert_ids preserved as aliases.

**Depends on:** Phase 14 (merge pattern established)

**Requirements:** MERGE-02

**Success Criteria:**
1. `skills/movie-experts/audio_pipeline/SKILL.md` exists with `sub_steps: [voicer, lip_sync, composer, foley, mixer]`
2. `spatial_audio` expert disposition documented (fold into audio_pipeline mixer sub-step OR deprecate with rationale) — decision recorded in SKILL.md
3. `metadata.hermes.related_skills` includes union of 5 audio experts' edges
4. Old 5 audio expert directories preserved with `status: merged_into` + redirect
5. lip_sync explicitly added as sub-step (was implicit in v1; new DAG makes it explicit per Phase 8 §2.9 NODE-09 critic pairing)

**Plans:** TBD

---

### Phase 16: New AI-Native Expert (prompt_injector)

**Goal:** A reader can read `skills/movie-experts/prompt_injector/SKILL.md` and find a complete new expert with 4 refs (prompt engineering patterns + cross-call consistency), frontmatter metadata.hermes aligned to v2.0 PRFP DAG (expert_id, related_skills, metrics), and integration into the collaboration graph.

**Depends on:** Phase 15 (merge pattern + collaboration graph topology stable)

**Requirements:** NEW-01

**Success Criteria:**
1. `skills/movie-experts/prompt_injector/SKILL.md` exists with full content (EN structure + CN prose per META-03)
2. `metadata.hermes.expert_id: prompt_injector`
3. `metadata.hermes.related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]` (per Phase 8 §2.7)
4. `metadata.hermes.metrics: [cross_call_consistency, prompt_token_efficiency]` (per nodes.yaml)
5. 4 refs in `prompt_injector/references/` (prompt engineering patterns + cross-call consistency literature)
6. README 21-expert inventory lists prompt_injector as NEW (Phase 16 entry)

**Plans:** TBD

---

### Phase 17: Deprecate 3 Candidates (performer / scene_builder / storyboard_designer)

**Goal:** A reader can find 3 deprecated experts (`performer`, `scene_builder`, `storyboard_designer`) each marked `status: deprecated` with redirect annotations pointing to their inheritance targets (character_designer + screenplay / cinematographer + style_genome / cinematographer composition_lock respectively), and old expert_ids preserved for backward compatibility.

**Depends on:** Phase 14-16 (inheritance targets exist as renamed/merged/new experts)

**Requirements:** DEPRECATE-01, DEPRECATE-02, DEPRECATE-03

**Success Criteria:**
1. `skills/movie-experts/performer/SKILL.md` marked `status: deprecated` + redirect to `character_designer` + `screenplay`
2. `skills/movie-experts/scene_builder/SKILL.md` marked `status: deprecated` + redirect to `cinematographer` + `style_genome`
3. `skills/movie-experts/storyboard_designer/SKILL.md` marked `status: deprecated` + redirect to `cinematographer` (composition_lock sub-task per Phase 7 §3.4 D3.4)
4. Each deprecated SKILL.md retains original expert_id + content (FOUND-08 backward compat)
5. `metadata.hermes.deprecated: true` + `metadata.hermes.deprecated_reason: <CN prose>` per deprecation rationale

**Plans:** TBD

---

### Phase 18: Validation + Documentation + Collaboration Graph Update

**Goal:** A reader can verify (a) 21 active expert_id inventory (16 DAG pipeline-roles + 5 aliases from rename/merge), (b) updated 21-expert collaboration DAG matching v2.0 PRFP topology, (c) updated README + glossary + known-external-models.yaml reflecting Phase 13-17 changes, and (d) `skills-mapping.yaml` sign_off_status: signed_off across all entries.

**Depends on:** Phase 13-17 (all rename/merge/new/deprecate operations complete)

**Requirements:** VALIDATE-01, VALIDATE-02, DOC-01, DOC-02

**Success Criteria:**
1. `grep -r 'expert_id:' skills/movie-experts/ | wc -l` returns 21 (16 active + 5 aliases); no orphan IDs
2. `skills-mapping.yaml` all entries have `sign_off_status: signed_off`
3. `skills/movie-experts/README.md` updated: 26-expert → 21-expert inventory; 18-expert collaboration DAG → v2.0 PRFP topology Mermaid (per `01-NODE-DAG.md` §1.5)
4. `_shared/glossary.md` updated with new terms (visual_executor, audio_pipeline, prompt_injector, continuity_auditor, compliance_gate)
5. `_shared/known-external-models.yaml` updated with Phase 8 §2.17 dated annex models
6. FOUND-08 frozen rule compliance verified: zero silent renames; all aliases explicit
7. Backward compat verified: old expert_id references still resolve via aliases

**Plans:** TBD

---

## Critical Path

```
13 (rename) → 14 (visual merge) → 15 (audio merge) → 16 (prompt_injector NEW) → 17 (deprecate 3) → 18 (validate + docs)
```

Strict sequential — each phase establishes pattern for next. No parallelism within v3.0 (skills work is single-track).

**Phase 13 is bottleneck** — establishes rename + alias pattern reused by 14-17.

**Phase 18 is integration gate** — validates all 13-17 work meets FOUND-08 + backward compat + collaboration graph coherence.

---

## v2.0 PRFP Cross-References

- **Design source-of-truth:** `.planning/research/v2-pipeline-design/`
- **Canonical mapping:** `.planning/research/v2-pipeline-design/skills-mapping.yaml`
- **Comparison rationale:** `.planning/research/v2-pipeline-design/06-COMPARISON-VS-26-SKILLS.md`
- **Per-node specs:** `.planning/research/v2-pipeline-design/02-NODE-SPECS.md` + `nodes.yaml`
- **DAG topology:** `.planning/research/v2-pipeline-design/01-NODE-DAG.md` (Mermaid in §1.5)

---

## Coordination with kais-movie-agent parallel milestone

Per HANDOFF-05 ownership matrix:
- **hermes-agent (this milestone v3.0):** owns design-intent layer (skills)
- **kais-movie-agent (parallel milestone):** owns implementation layer (lib/)
- **Co-owned DAG:** structural changes require cross-repo sign-off (cross-repo ADR)

v3.0 does NOT change DAG structure — it only renames/merges/deprecates experts to align with already-frozen v2.0 PRFP DAG. So no cross-repo sign-off needed for v3.0 individual phases; only final VALIDATE-01 may surface coordination items for kais team.

---

## Notes

- **Phase 17 (deprecate) is reversible** — if kais team or live run shows a deprecated expert is still needed, the `status: deprecated` flag can be removed without structural DAG change.
- **Phase 18 (validation) may trigger small revisions to 13-17** — if FOUND-08 violations found, the relevant phase revisits before milestone complete.
- **v3.0 is preparatory for FUTURE-08 live run** — once v3.0 + kais parallel milestone both complete, FUTURE-08 (live statistical GO/NO-GO) becomes possible.

---

*Roadmap defined: 2026-06-16 — v3.0 Skills-to-DAG Alignment, 6 phases (13-18), 12 requirements*
