# Phase 13: Expert Rename + Alias Scaffolding - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — rename + alias scaffolding)

<domain>
## Phase Boundary

Rename 2 v1 movie-experts to align with v2.0 PRFP DAG node IDs:
1. `continuity` → `continuity_auditor` (per Phase 7 §4.10 — emphasize critic role)
2. `compliance_marketing` → `compliance_gate` (per Phase 7 §4.15 — separate pure compliance from marketing)

Each rename must:
- Create new directory `skills/movie-experts/{new_id}/` with full content (refs + SKILL.md + GAP-REPORT.md if exists)
- Update `name`, `expert_id` to new ID
- Add `metadata.hermes.aliases: [{old_id}]` for backward compat
- Preserve old directory paths (`continuity/`, `compliance_marketing/`) with redirect SKILL.md (backward compat per FOUND-08)
- Update all consumers' `related_skills` to use new IDs (bidirectional edge sync)
- Update `skills-mapping.yaml` `sign_off_status`: `pending` → `signed_off` for both entries

Out-of-scope: drawer/animator merge (Phase 14), audio merge (Phase 15), prompt_injector new (Phase 16), deprecations (Phase 17), validation/docs (Phase 18).

</domain>

<decisions>
## Implementation Decisions

### Rename Pattern (Established by ROADMAP + skills-mapping.yaml)
- **Source-of-truth:** `.planning/research/v2-pipeline-design/skills-mapping.yaml` lines 66-78 — `one_to_one_renamed` mapping entries
- **Directory strategy:** New dir `{new_id}/` holds full content; old dir `{old_id}/` retains a redirect-only SKILL.md (no refs)
- **Redirect SKILL.md format:** Single frontmatter block + one paragraph: "This expert has been renamed to `{new_id}`. See `../{new_id}/SKILL.md`. Backward-compat alias preserved in `metadata.hermes.aliases`."
- **Aliases metadata:** `metadata.hermes.aliases: [{old_id}]` array in new expert's SKILL.md frontmatter

### Consumer Updates (Bidirectional Edge Sync)
- All 17 SKILL.md files referencing `continuity` in `related_skills` must change to `continuity_auditor`
- All 11 SKILL.md files referencing `compliance_marketing` in `related_skills` must change to `compliance_gate`
- Files in `_eval/`, `_shared/`, `README.md` referencing old IDs must update similarly

### Claude's Discretion
- Order of operations (rename one then other, or both at once — both fine since independent)
- Exact redirect SKILL.md phrasing (as long as it conveys "renamed to X, see new path, aliases preserved")
- Whether to add a CHANGELOG note inside new SKILL.md describing the rename — recommended YES for traceability

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v2-pipeline-design/skills-mapping.yaml` — canonical mapping table with `sign_off_status` field
- Existing `continuity/SKILL.md` (6508 bytes, 1.1.0) + `references/` + `GAP-REPORT.md`
- Existing `compliance_marketing/SKILL.md` (18492 bytes, 1.0.0) + `references/`

### Established Patterns
- SKILL.md frontmatter uses YAML with `metadata.hermes.{tags, related_skills, expert_id, metrics}` schema (CLAUDE.md §Skill File Conventions)
- Bilingual: EN YAML structure + CN prose in body
- `related_skills` is bidirectional: A listing B implies B should list A (close edge loops explicitly)

### Integration Points
- `skills-mapping.yaml:71,78` — two `sign_off_status: pending` lines need updating
- 17 files reference `continuity` in `related_skills` (per grep)
- 11 files reference `compliance_marketing` in `related_skills`
- `skills/movie-experts/README.md` likely lists both old IDs in inventory

</code_context>

<specifics>
## Specific Ideas

- ROADMAP §13 success criterion #4: "Old directory paths preserved with redirect SKILL.md (backward compat)" — explicit hard requirement
- ROADMAP §13 success criterion #5: "`skills-mapping.yaml` `sign_off_status` updated: `pending` → `signed_off` for both renamed entries" — explicit hard requirement
- FOUND-08 frozen rule: zero silent renames; all aliases must be explicit in metadata

</specifics>

<deferred>
## Deferred Ideas

None — pure infrastructure phase, scope tightly bounded by ROADMAP §13.

</deferred>
