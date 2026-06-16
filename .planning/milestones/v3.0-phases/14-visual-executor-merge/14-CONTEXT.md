# Phase 14: Visual Executor Merge - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — merge + alias scaffolding)

<domain>
## Phase Boundary

Merge 2 v1 movie-experts (`drawer` + `animator`) into a unified `visual_executor` node per v2.0 PRFP DAG. The merged expert declares `sub_steps: [drawer, animator]` and unifies the consistency context per Phase 7 §4.8 + PITFALLS §2.1.

Operations:
1. Create `skills/movie-experts/visual_executor/` directory with merged SKILL.md + consolidated refs from both predecessors
2. SKILL.md frontmatter declares `sub_steps: [drawer, animator]` + `metadata.hermes.aliases: [drawer, animator]`
3. `metadata.hermes.related_skills` = union of drawer + animator edges
4. Old `drawer/SKILL.md` and `animator/SKILL.md` preserved with `status: merged_into` + `merged_into: visual_executor` + redirect
5. Update all consumers referencing `drawer` or `animator` in `related_skills` to use `visual_executor`
6. Consolidate drawer + animator refs under `visual_executor/references/` (or cross-reference if duplication is undesirable)

Out-of-scope: audio pipeline merge (Phase 15), prompt_injector new (Phase 16), deprecations (Phase 17), validation/docs (Phase 18).

</domain>

<decisions>
## Implementation Decisions

### Merge Pattern (Established by ROADMAP + skills-mapping.yaml)
- **Source-of-truth:** `.planning/research/v2-pipeline-design/skills-mapping.yaml` lines 80-85 — `n_to_one_merged` mapping entry
- **Directory strategy:** New `visual_executor/` holds merged content; old `drawer/` + `animator/` dirs preserved with `status: merged_into` + `merged_into: visual_executor` + redirect-only SKILL.md
- **Sub-steps metadata:** `sub_steps: [drawer, animator]` declared at top level of SKILL.md frontmatter (new metadata field per v2.0 PRFP DAG convention)
- **Aliases metadata:** `metadata.hermes.aliases: [drawer, animator]` array

### Consumer Updates (Bidirectional Edge Sync)
- All experts listing `drawer` in `related_skills` change to `visual_executor`
- All experts listing `animator` in `related_skills` change to `visual_executor`
- The merged `visual_executor/SKILL.md` lists `union(drawer.related_skills, animator.related_skills)` minus self-references

### Refs Strategy
- Drawer has its own refs (FLUX, LoRA, IP-Adapter etc.); animator has its own (Veo, Kling, LTX, Pixverse etc.)
- **Decision:** Keep both ref sets side-by-side under `visual_executor/references/` with filename prefixes (e.g., `drawer-flux2-guide.md`, `animator-veo-guide.md`) OR keep sub-folders (e.g., `references/drawer/`, `references/animator/`). Claude's discretion — recommend sub-folders for cleanliness.

### Claude's Discretion
- Exact redirect SKILL.md phrasing for merged-into stub
- Refs organization (prefixed files vs sub-folders)
- Whether body prose from both SKILL.md files is merged into one body or kept as two clearly-marked sections
- Sub-step handoff contract documentation (how visual_executor decides when to call drawer vs animator sub-step)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing `drawer/SKILL.md` (FLUX 2 specialist, related_skills: screenplay/continuity_auditor/colorist/animator/style_genome/compliance_gate/cinematographer/production)
- Existing `animator/SKILL.md` (video gen specialist, related_skills: drawer/scene_builder/editor/performer/colorist/continuity_auditor/cinematographer/production)
- Both have `references/` subdirs + `GAP-REPORT.md`
- `.planning/research/v2-pipeline-design/skills-mapping.yaml:80-85` — canonical n_to_one_merged mapping

### Established Patterns (from Phase 13)
- Redirect stub format: frontmatter with `status: <renamed|merged_into>` + redirect target + 1-paragraph notice
- `metadata.hermes.aliases` array for backward compat (FOUND-08)
- Bidirectional edge sync: all consumers' `related_skills` arrays updated
- README.md inventory + corpus tree updated to reflect topology change
- `_shared/glossary.md` updated with new expert terms

### Integration Points
- 17+ consumer SKILL.md files reference `drawer` or `animator` in `related_skills`
- `skills/movie-experts/README.md` inventory needs update
- `skills-mapping.yaml` line 84 already declares merge — no sign_off flip needed (merge entries have no `sign_off_status` field by convention; that's only for renames)
- `hook_retention/SKILL.md` may have cross-chain refs to drawer/animator
- Drawer + animator already in `related_skills` of continuity_auditor + compliance_gate + others (Phase 13 just updated those edges)

</code_context>

<specifics>
## Specific Ideas

- ROADMAP §14 success criterion #1: `sub_steps: [drawer, animator]` MUST be declared in visual_executor SKILL.md
- ROADMAP §14 success criterion #2: `related_skills` MUST be union of drawer + animator edges
- ROADMAP §14 success criterion #3: Old `drawer/SKILL.md` + `animator/SKILL.md` preserved with `status: merged_into` + `merged_into: visual_executor` + redirect
- ROADMAP §14 success criterion #4: All consumers updated
- ROADMAP §14 success criterion #5: Drawer + animator refs (if any in `_shared/project-corpus/`) consolidated or cross-referenced under visual_executor
- Phase 7 §4.8 + PITFALLS §2.1 rationale: "consistency context unified; specialization loss acceptable"

</specifics>

<deferred>
## Deferred Ideas

None — pure infrastructure phase, scope tightly bounded by ROADMAP §14.

</deferred>
