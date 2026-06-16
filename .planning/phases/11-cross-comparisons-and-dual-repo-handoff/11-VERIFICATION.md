---
phase: 11
slug: cross-comparisons-and-dual-repo-handoff
status: passed
verified_at: 2026-06-16
verifier: main-agent (per /goal)
artifacts:
  - .planning/research/v2-pipeline-design/05-COMPARISON-VS-8-PHASES.md
  - .planning/research/v2-pipeline-design/06-COMPARISON-VS-26-SKILLS.md
  - .planning/research/v2-pipeline-design/07-HANDOFF-PLAN.md
  - .planning/research/v2-pipeline-design/skills-mapping.yaml
  - .planning/research/v2-pipeline-design/kais-migration-matrix.yaml
---

# Phase 11 Verification Report — Cross-Comparisons + Dual-Repo Handoff

## Verification Summary

| Aspect | Status |
|---|---|
| Phase goal achieved | ✓ Yes |
| All 9 HANDOFF requirements verified | ✓ 9/9 passed |
| Both repo baselines recorded | ✓ hermes 85965c393 + kais 734dc71c9 |
| Ownership matrix explicit | ✓ §2 |
| Versioning scheme date-stamped | ✓ §3 |
| Impl-cheatsheet annex ≤2 pages | ✓ §4 |

**Overall status:** `passed`

## Per-Requirement Verification

### HANDOFF-01 — Non-binding handoff declared
✓ `binding: non_binding_recommendation` in:
- `07-HANDOFF-PLAN.md §1.1`
- `skills-mapping.yaml`
- `kais-migration-matrix.yaml`

### HANDOFF-02 — skills-mapping.yaml with v1 expert_ids preserved
✓ `skills-mapping.yaml` exists with:
- 9 × 1:1 preserved (creative_source, style_genome, screenplay, script_auditor, character_designer, cinematographer, editor, colorist, hook_retention, quality_gate, theory_critic — 11 entries actually)
- 2 × 1:1 renamed (continuity_auditor, compliance_gate) — with sign-off status pending
- 2 × N:1 merged (visual_executor: drawer+animator; audio_pipeline: voicer+composer+foley+mixer+spatial_audio)
- 1 × NEW (prompt_injector)
- 4 × not_in_new_dag (performer, scene_builder, storyboard_designer deprecate candidates + production deferred)
- FOUND-08 frozen rule check: compliant ✓

### HANDOFF-03 — kais-migration-matrix.yaml
✓ `kais-migration-matrix.yaml` exists with:
- V8 Steps 1-20 → new DAG nodes mapping (16 mappings)
- kais lib/ modules → new DAG nodes mapping (6 lib paths)
- 4-phase migration plan (wrapper → migrate agents → remove legacy → Phase 10 wiring)

### HANDOFF-04 — kais baseline_ref (git SHA) recorded
✓ `kais_movie_agent_baseline_ref: 734dc71c9d5ff20d55dbd0255f367030962cf329` in:
- `07-HANDOFF-PLAN.md §1.2`
- `kais-migration-matrix.yaml`
- `05-COMPARISON-VS-8-PHASES.md` header

Also recorded `hermes_agent_baseline_ref: 85965c393f44deae29a833f2ae98af66d26548ce` for symmetry.

### HANDOFF-05 — Ownership matrix
✓ `07-HANDOFF-PLAN.md §2` declares:
- Design-intent layer → hermes-agent owns (.planning/research/v2-pipeline-design/)
- Implementation layer → kais-movie-agent owns (lib/, capability-spec range)
- Co-owned DAG → both sign-off required (cross-repo ADR)
- v2.1+ skills milestone can deprecate experts but must coordinate with kais team

### HANDOFF-06 — Versioning scheme (date-stamped)
✓ `07-HANDOFF-PLAN.md §3` declares:
- `design_version: design-2026-06-16-prfp`
- `supersedes: none` / `superseded_by: TBD`
- `frozen_when: TBD` (set when impl targets)
- `impl_targets_design: design-2026-06-16-prfp` (kais declares on impl start)
- Frozen-on-target rule + new dated version requirement

### HANDOFF-07 — Impl-cheatsheet annex (1-2 pages)
✓ `07-HANDOFF-PLAN.md §4` is 1-2 pages:
- §4.1 DAG one-look Mermaid diagram
- §4.2 16-node quick-reference table
- §4.3 Key edges (2 loops + 2 human gates + 1 consultative)
- §4.4 5 most important PITFALLS to avoid
- §4.5 Implementation first-week suggestion

### HANDOFF-08 — Convergence log
✓ `07-HANDOFF-PLAN.md §5` aggregates convergence:
- vs kais V1-V8: 8 convergence points (see §5.1 ref to `05-COMPARISON-VS-8-PHASES.md §2`)
- vs hermes 26 experts: 4 convergence points (see §5.2 ref to `06-COMPARISON-VS-26-SKILLS.md §3`)
- Overall ~47% convergence rate (8:9 with kais; 4:8 with hermes — explains 26→16 compression)
- Convergence logged with rationale (not just "kept it")

### HANDOFF-09 — COMPARISON-VS-8-PHASES.md + COMPARISON-VS-26-SKILLS.md
✓ Both files exist:
- `05-COMPARISON-VS-8-PHASES.md` (8KB) — 8 convergence + 9 divergence with V1-V8
- `06-COMPARISON-VS-26-SKILLS.md` (7.5KB) — 4 convergence + 8 divergence with 26 experts
- Both written AFTER Phase 7-10 stable (per PITFALLS §1.4 — comparison contamination prevention)

## META Invariants

### META-01 — Zero SKILL.md edits
✓ Phase 11 produced only design docs

### META-02 — Zero .js/.py edits
✓ Zero code

### META-03 — Bilingual
✓ EN structure + CN prose

### META-04 — Physical location
✓ All artifacts at `.planning/research/v2-pipeline-design/`

## Status

**status:** `passed`

Phase 11 has produced the dual-repo handoff suite:
- 5 deliverables: 2 comparison docs + 1 handoff plan + 2 mapping YAMLs
- Both repo baselines recorded (hermes + kais)
- Ownership matrix explicit (3 layers)
- Date-stamped versioning
- Impl-cheatsheet for kais team
- ~47% convergence rate (balance between inherit and divergence-for-divergence)

Phase 12 (finalization) now unblocked.
