# Phase 17: Deprecate 3 Experts - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning
**Mode:** Auto-generated (deprecation phase — pattern from Phase 13-15)

<domain>
## Phase Boundary

Mark 3 v1 movie-experts as `status: deprecated` with redirect annotations pointing to their inheritance targets. Per `.planning/research/v2-pipeline-design/skills-mapping.yaml` `not_in_new_dag:` section:

| v1 expert | Disposition | Inheritance target | Rationale |
|---|---|---|---|
| `performer` | deprecate_candidate | `character_designer` + `screenplay` | Performance truth folded into character_designer (voice + behavioral tics) + screenplay (dialogue subtext); no standalone node necessary |
| `scene_builder` | deprecate_candidate | `cinematographer` + `style_genome` | Scene design folded into cinematographer (mise-en-scène as composition_lock sub-task) + style_genome |
| `storyboard_designer` | deprecate_candidate | `cinematographer` (composition_lock sub-task) | Phase 7 §3.4 D3.4: storyboard folded into cinematographer composition_lock |

Per ROADMAP §17 success criteria:
1. `skills/movie-experts/performer/SKILL.md` marked `status: deprecated` + redirect to `character_designer` + `screenplay`
2. `skills/movie-experts/scene_builder/SKILL.md` marked `status: deprecated` + redirect to `cinematographer` + `style_genome`
3. `skills/movie-experts/storyboard_designer/SKILL.md` marked `status: deprecated` + redirect to `cinematographer` (composition_lock sub-task per Phase 7 §3.4 D3.4)
4. Each deprecated SKILL.md retains original expert_id + content (FOUND-08 backward compat)
5. `metadata.hermes.deprecated: true` + `metadata.hermes.deprecated_reason: <CN prose>` per deprecation rationale

Operations:
1. **DO NOT delete or rename** the 3 directories — they remain as deprecated stubs
2. Add `status: deprecated` + `deprecated: true` + `deprecated_reason:` + `redirect_to:` (or `inheritance_targets:`) to each SKILL.md frontmatter
3. Keep body content intact (FOUND-08) — readers can still read the v1 expertise
4. Add prominent deprecation notice at top of body: `> ⚠️ DEPRECATED (Phase 17): This expert is folded into [target(s)]. See [paths].`
5. Update all consumers referencing these 3 experts in `related_skills`:
   - For `performer`: Update consumers to reference `character_designer` or `screenplay` instead
   - For `scene_builder`: Update consumers to reference `cinematographer` or `style_genome` instead
   - For `storyboard_designer`: Update consumers to reference `cinematographer` instead
6. README inventory marks these 3 as DEPRECATED
7. Glossary entries updated with deprecation notices

Out-of-scope: validation/docs (Phase 18).

</domain>

<decisions>
## Implementation Decisions

### Deprecation Pattern (Established by ROADMAP + skills-mapping.yaml)
- **Source-of-truth:** `.planning/research/v2-pipeline-design/skills-mapping.yaml` lines 104-119 — `not_in_new_dag:` section
- **Directory strategy:** Keep old dir intact; just modify SKILL.md frontmatter + add deprecation notice at top of body
- **Backward compat:** FOUND-08 — original expert_id + content preserved. NO redirect stub replacement (different from rename/merge). The expert body remains readable; it's just marked deprecated.
- **Frontmatter additions:**
  ```yaml
  status: deprecated
  metadata:
    hermes:
      deprecated: true
      deprecated_reason: "<CN prose — why deprecated>"
      inheritance_targets: [<target1>, <target2>]  # or single target
  ```

### Body Deprecation Notice
Insert at top of body (after `# <Name> Expert (<CN>)` H1, before existing content):
```markdown
> ⚠️ **DEPRECATED (Phase 17 v3.0)**: This expert is deprecated. Its functionality has been folded into:
> - `<target1>` — `<what target1 absorbed>`
> - `<target2>` — `<what target2 absorbed>`
>
> **Original v1 content preserved below for backward compatibility (FOUND-08 frozen rule).**
```

### Consumer Updates (Edge Rewiring)
For each consumer of the 3 deprecated experts:
- `performer` → consumers should switch related_skills entry to `character_designer` OR `screenplay` (depending on what aspect of performance they need)
- `scene_builder` → consumers should switch to `cinematographer` OR `style_genome`
- `storyboard_designer` → consumers should switch to `cinematographer`

### Claude's Discretion
- Whether to add a CHANGELOG note inside each deprecated SKILL.md
- Exact deprecation notice phrasing (as long as it conveys the inheritance)
- For consumers with multiple valid targets (e.g., a consumer using `performer` for both voice and dialogue subtext), pick one or list both

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 3 existing expert dirs (performer, scene_builder, storyboard_designer) — each with SKILL.md + references/ + GAP-REPORT.md
- Phase 13-15 redirect stub patterns (for inspiration, though deprecation is NOT a redirect stub — body content stays)
- `.planning/research/v2-pipeline-design/skills-mapping.yaml:104-119` — `not_in_new_dag:` rationale entries

### Established Patterns (cumulative from Phases 13-16)
- SKILL.md frontmatter schema with `metadata.hermes.{tags, related_skills, expert_id, metrics}` — extended with `deprecated`, `deprecated_reason`, `inheritance_targets`
- FOUND-08 frozen rule: original expert_id + content preserved
- Bidirectional edge sync — but for deprecation, edges are REWIRED (not deleted) to inheritance targets

### Integration Points
- 8+ consumer SKILL.md files reference `performer` in `related_skills`
- 10+ consumers reference `scene_builder`
- 7+ consumers reference `storyboard_designer`
- README inventory marks 3 experts as DEPRECATED (final expert count: 18 → 15 active post-deprecation, or 18-3=15 then Phase 16 added 1 = back to 16... actual math: 18 (after Phase 16) - 3 deprecated = 15 active + 3 deprecated = 18 total expert_ids in the codebase; the 21-expert target counts active+aliases, so deprecation brings active count down)
- Phase 18 will validate the final 21-expert inventory (16 DAG pipeline-roles + 5 aliases from renames/merges per ROADMAP §18)

</code_context>

<specifics>
## Specific Ideas

- ROADMAP §17 success criterion #1: performer → character_designer + screenplay
- ROADMAP §17 success criterion #2: scene_builder → cinematographer + style_genome
- ROADMAP §17 success criterion #3: storyboard_designer → cinematographer (composition_lock sub-task per Phase 7 §3.4 D3.4)
- ROADMAP §17 success criterion #4: Each deprecated SKILL.md retains original expert_id + content (FOUND-08)
- ROADMAP §17 success criterion #5: `metadata.hermes.deprecated: true` + `metadata.hermes.deprecated_reason: <CN prose>` per deprecation rationale
- **Phase 17 is reversible** per ROADMAP §Notes — if kais team or live run shows a deprecated expert is still needed, the `status: deprecated` flag can be removed without structural DAG change

</specifics>

<deferred>
## Deferred Ideas

None — deprecation phase, scope tightly bounded by ROADMAP §17.

</deferred>
