# Phase 15: Audio Pipeline Merge - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — multi-expert merge + alias scaffolding)

<domain>
## Phase Boundary

Merge 5 audio movie-experts into a unified `audio_pipeline` node per v2.0 PRFP DAG:

| Sub-step | v1 expert_id | Related skills (v1) |
|---|---|---|
| voicer | voicer | screenplay, performer, editor, mixer, spatial_audio, production |
| lip_sync | lip_sync | voicer, performer, editor, visual_executor, mixer, continuity_auditor |
| composer | composer | screenplay, editor, style_genome, mixer, foley, spatial_audio |
| foley | foley | visual_executor, performer, scene_builder, composer, mixer, spatial_audio, continuity_auditor |
| mixer | mixer | voicer, composer, foley, spatial_audio, editor, continuity_auditor |

Per `.planning/research/v2-pipeline-design/skills-mapping.yaml` lines 87-92:
- `sub_steps_preserved: [voicer, lip_sync, composer, foley, mixer]`
- `spatial_audio` expert disposition must be explicitly addressed (fold into audio_pipeline mixer sub-step OR deprecate with rationale) — decision recorded in SKILL.md
- `lip_sync` explicitly added as sub-step (was implicit in v1; new DAG makes it explicit per Phase 8 §2.9 NODE-09 critic pairing)

Operations:
1. Create `skills/movie-experts/audio_pipeline/` directory with merged SKILL.md + consolidated refs from all 5 predecessors
2. SKILL.md frontmatter declares `sub_steps: [voicer, lip_sync, composer, foley, mixer]` + `metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer]` (and possibly `spatial_audio` if folded)
3. `metadata.hermes.related_skills` = union of 5 predecessors' edges minus self-references and minus internal audio-pipeline edges
4. **spatial_audio decision:** Fold into audio_pipeline as a 6th sub-step (recommended) OR deprecate with explicit rationale. Document the choice in SKILL.md body.
5. Old 5 audio expert directories preserved with `status: merged_into` + `merged_into: audio_pipeline` + redirect (spatial_audio gets `status: folded_into` if folded)
6. Update all consumers referencing any of the 5 (or 6) audio expert_ids in `related_skills` to use `audio_pipeline`

Out-of-scope: prompt_injector new (Phase 16), deprecations (Phase 17), validation/docs (Phase 18).

</domain>

<decisions>
## Implementation Decisions

### Merge Pattern (Established by ROADMAP + skills-mapping.yaml)
- **Source-of-truth:** `.planning/research/v2-pipeline-design/skills-mapping.yaml:87-92` — `n_to_one_merged` mapping entry
- **Directory strategy:** New `audio_pipeline/` holds merged content; old 5 audio expert dirs preserved with `status: merged_into` redirect stubs
- **Sub-steps metadata:** `sub_steps: [voicer, lip_sync, composer, foley, mixer]` at top level of SKILL.md frontmatter
- **Aliases metadata:** `metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer]` (5 entries — plus spatial_audio if folded)

### spatial_audio Disposition (KEY DECISION)
Per ROADMAP §15 success criterion #2, this MUST be explicitly addressed:
- **Recommended:** Fold spatial_audio into audio_pipeline as a 6th sub-step (sub_steps array + aliases array both include `spatial_audio`). Spatial audio rendering is fundamentally a mixer/mastering concern — Dolby Atmos, HRTF, binaural panning all belong in the audio mastering stage. Old spatial_audio/SKILL.md becomes a redirect stub with `status: folded_into` (distinct from `merged_into`).
- **Alternative:** Deprecate spatial_audio with rationale. Less recommended because spatial_audio has unique technical content (HRTF, Atmos metadata) that should not be lost.
- **Claude's discretion** — pick one and document rationale in the SKILL.md body.

### Consumer Updates (Bidirectional Edge Sync)
- All experts listing ANY of {voicer, lip_sync, composer, foley, mixer, spatial_audio} in `related_skills` change to single `audio_pipeline` entry (deduplicated)
- The merged `audio_pipeline/SKILL.md` lists `union(5 predecessors.related_skills)` minus self-references and minus internal audio-pipeline edges (e.g., voicer→mixer is now intra-expert)

### Refs Strategy
- Each of 5 predecessors has its own `references/` subdir
- **Recommend sub-folders:** `audio_pipeline/references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/` for clean separation

### Sub-step Body Prose
- 5 (or 6) clearly-marked `## Sub-step: <Name>` H2 sections inside audio_pipeline/SKILL.md, each preserving the predecessor's body verbatim (or with light edits to convert inter-expert references to intra-expert sub-step references)

### Claude's Discretion
- Exact redirect SKILL.md phrasing
- spatial_audio disposition (fold vs deprecate) — pick one with rationale
- Refs organization (sub-folders vs prefixed files)
- Sub-step ordering in body (recommend pipeline order: voicer → lip_sync → composer → foley → mixer → spatial_audio if folded)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 6 existing audio expert dirs (voicer, lip_sync, composer, foley, mixer, spatial_audio) — each with SKILL.md + references/ + GAP-REPORT.md (except lip_sync which has `_eval/` subdir)
- Phase 13 + 14 patterns: redirect stub format, aliases metadata, sub_steps metadata, sub-folder refs organization, bidirectional edge sync, English-noun preservation

### Established Patterns (cumulative from Phases 13-14)
- Redirect stub: frontmatter with `status: <renamed|merged_into|folded_into>` + redirect target + 1-paragraph notice
- `metadata.hermes.aliases` array (FOUND-08)
- Bidirectional edge sync across all consumers
- README.md inventory + corpus tree + DAG diagram updated
- `_shared/glossary.md` updated with new expert terms
- `_shared/quality-rubric.md` + `_shared/RAG-INVOCATION-PATTERN.md` updated if they reference affected experts

### Integration Points
- 10+ consumer SKILL.md files reference at least one audio expert in `related_skills`
- Phase 14's `visual_executor` is referenced by `lip_sync` and `foley` — those edges must be preserved in `audio_pipeline.related_skills`
- Phase 13's `continuity_auditor` + `compliance_gate` are referenced by multiple audio experts — preserved in union
- `skills/movie-experts/README.md` inventory + DAG diagram needs major update (6→1 expert)
- `skills-mapping.yaml:87-92` already declares merge — no sign_off flip needed
- `hook_retention/SKILL.md` may have cross-chain refs

</code_context>

<specifics>
## Specific Ideas

- ROADMAP §15 success criterion #2: spatial_audio disposition MUST be documented in SKILL.md (fold or deprecate with rationale) — HARD REQUIREMENT
- ROADMAP §15 success criterion #5: lip_sync MUST be explicit sub-step (was implicit in v1; new DAG makes it explicit per Phase 8 §2.9 NODE-09 critic pairing)
- Phase 7 §4.9 + PITFALLS §2.6 rationale: "5-task compression; consistency context unified"
- `sub_steps_preserved: [voicer, lip_sync, composer, foley, mixer]` is the canonical 5-item list per skills-mapping.yaml line 91

</specifics>

<deferred>
## Deferred Ideas

None — pure infrastructure phase, scope tightly bounded by ROADMAP §15.

</deferred>
