---
phase: 34-skills-migration-coding-agent-tmux-agents
plan: 03
subsystem: skills/autonomous-ai-agents
tags: [skills-migration, related_skills, bidirectional-graph, coexistence, documentation]
requires: [34-01, 34-02]
provides:
  - skills/autonomous-ai-agents/COEXISTENCE.md
  - bidirectional related_skills graph (6 skills)
affects:
  - skills/autonomous-ai-agents/claude-code/SKILL.md
  - skills/autonomous-ai-agents/codex/SKILL.md
  - skills/autonomous-ai-agents/opencode/SKILL.md
  - skills/autonomous-ai-agents/hermes-agent/SKILL.md
tech-stack:
  added: []
  patterns: [YAML frontmatter surgical edit, bidirectional related_skills graph, SUPPLEMENT coexistence documentation]
key-files:
  created:
    - skills/autonomous-ai-agents/COEXISTENCE.md
  modified:
    - skills/autonomous-ai-agents/claude-code/SKILL.md
    - skills/autonomous-ai-agents/codex/SKILL.md
    - skills/autonomous-ai-agents/opencode/SKILL.md
    - skills/autonomous-ai-agents/hermes-agent/SKILL.md
decisions:
  - "SUPPLEMENT coexistence — 2 new skills add capabilities the existing 4 do not provide; no replacement"
  - "Opportunistic fix: latent codex->opencode asymmetry resolved while touching the file"
  - "related_skills graph is the discovery mechanism; bidirectional invariant enforced"
  - "COEXISTENCE.md is plain documentation (no YAML frontmatter) — not loaded as a skill"
  - "Phase 34 SC #5 traceability anchored via explicit ROADMAP reference in COEXISTENCE.md"
metrics:
  duration: ~2m
  completed: 2026-06-25
---

# Phase 34 Plan 03: Bidirectional related_skills Wiring + Coexistence Documentation Summary

Wired the bidirectional `related_skills` cross-reference graph across all 6 autonomous-ai-agents skills (4 existing + 2 new from Plans 34-01/34-02) and authored the canonical SUPPLEMENT coexistence decision artifact (`COEXISTENCE.md`) with a capability matrix, decision tree, migration provenance, and out-of-scope audit list.

## What Was Built

### Task 1 — Bidirectional related_skills Wiring

Applied 4 surgical Edit operations to the frontmatter `related_skills:` line in each of the 4 existing skills. Each file had exactly ONE line changed (additive edit, no removals):

- **`claude-code/SKILL.md`** — added `coding-agent`, `tmux-agents`
- **`codex/SKILL.md`** — added `opencode` (opportunistic asymmetry fix), `coding-agent`, `tmux-agents`
- **`opencode/SKILL.md`** — added `coding-agent`, `tmux-agents`
- **`hermes-agent/SKILL.md`** — added `coding-agent`, `tmux-agents`

The reverse links (coding-agent + tmux-agents → 4 existing skills) were already established by Plans 34-01 and 34-02. After Task 1, the bidirectional graph is complete: every relevant pair is linked both directions.

### Task 2 — COEXISTENCE.md Canonical Artifact

Created `skills/autonomous-ai-agents/COEXISTENCE.md` (61 lines) with 6 sections:

1. **Decision: SUPPLEMENT (not replace)** — explicit rationale + ROADMAP Phase 34 SC #5 traceability
2. **Capability Matrix** — 6 skills × 4 dimensions table (Authoritative / Supports / — partition is clean; no row owns >1 column authoritatively)
3. **When to use which** — 4-step operator-facing decision tree
4. **Migration Provenance (Phase 34, v7.0)** — openclaw source paths → hermes target paths with adaptation notes
5. **Bidirectional related_skills Graph** — describes the graph completion + the opportunistic codex↔opencode asymmetry fix
6. **Out of Scope** — explicit list of openclaw items NOT migrated (for Phase 37 VALIDATE-03 audit completeness)

The file is plain markdown (no YAML frontmatter) — it is documentation, not a skill, so it is not loaded by the skill discovery walk.

## Frontmatter Adaptation

N/A — this plan does not adapt openclaw frontmatter. The 4 existing skills already use the native hermes schema; Task 1 only appends two entries to the existing `related_skills:` YAML list per file.

## Verification

### Task 1 Verify Gate

- `yaml.safe_load` parses all 4 edited SKILL.md files cleanly (no syntax errors)
- `related_skills` in each of the 4 files contains both `coding-agent` and `tmux-agents`
- All pre-existing entries preserved (additive edit confirmed via `git diff --stat` showing 4 files × 1 line each)
- `BIDIRECTIONAL_GRAPH_OK` — automated graph-walk assertion confirms coding-agent ↔ {claude-code, codex, opencode, hermes-agent, tmux-agents}; tmux-agents ↔ same; each existing skill ↔ both new skills
- `codex` now references `opencode` (latent asymmetry resolved; matches opencode's pre-existing reverse link)

### Task 2 Verify Gate

- `COEXISTENCE.md` exists at the canonical path
- Literal token `SUPPLEMENT` present (decision explicit, not implicit)
- All 4 required H2 sections present: `## Capability Matrix`, `## When to use which`, `## Migration Provenance`, `## Bidirectional related_skills Graph`
- All 6 skill names appear in the file
- Capability matrix contains ≥7 table rows (header + separator + 6 skill rows)
- References Phase 34 / SC #5 for ROADMAP traceability
- UTF-8, single trailing newline, no emojis (per CLAUDE.md project conventions)

### Phase 34 Cross-Plan Verification (this plan completes the phase)

1. All 6 autonomous-ai-agents skills parse as valid YAML frontmatter — PASS
2. Bidirectional `related_skills` graph is complete (every relevant pair linked both directions) — PASS
3. `COEXISTENCE.md` exists with explicit SUPPLEMENT decision + capability matrix — PASS
4. No openclaw-runtime strings remain in migrated skills (the 3 `openclaw`/`clawdhub` mentions are author attribution + upstream-notes provenance, not runtime tokens; runtime tokens like `openclaw message send` and `metadata.openclaw.*` were already replaced by Plans 34-01/34-02) — PASS
5. The 4 existing skills remain discoverable (frontmatter schema unchanged except 2 added related_skills entries per file) — PASS
6. The 2 new skills are discoverable (files in expected paths, loaded via skill directory walk) — PASS

## Files

| File | Status | Purpose |
|------|--------|---------|
| `skills/autonomous-ai-agents/claude-code/SKILL.md` | modified | +2 entries in `related_skills` |
| `skills/autonomous-ai-agents/codex/SKILL.md` | modified | +3 entries in `related_skills` (incl. asymmetry fix) |
| `skills/autonomous-ai-agents/opencode/SKILL.md` | modified | +2 entries in `related_skills` |
| `skills/autonomous-ai-agents/hermes-agent/SKILL.md` | modified | +2 entries in `related_skills` |
| `skills/autonomous-ai-agents/COEXISTENCE.md` | created | SUPPLEMENT decision + capability matrix + provenance |

## Deviations from Plan

None — plan executed exactly as written. All 4 SKILL.md edits matched the planned `old_string` / `new_string` exactly. The opportunistic codex↔opencode asymmetry fix was anticipated by the plan (`<interfaces>` block lines 75-83 + `<decisions_honored>`), so it is not a deviation.

## Commits

| Hash | Type | Message |
|------|------|---------|
| `a62c1178d` | feat | wire bidirectional related_skills across autonomous-ai-agents skills (Task 1) |
| `5cbe555cc` | docs | document SUPPLEMENT coexistence decision + capability matrix (Task 2) |

## Phase 34 Closure

This plan completes Phase 34 of milestone v7.0. All 5 ROADMAP Phase 34 Success Criteria are now satisfiable:

- SC #1: `coding-agent/SKILL.md` exists at canonical path with valid frontmatter (Plan 34-01)
- SC #2: `tmux-agents/SKILL.md` exists at canonical path with valid frontmatter (Plan 34-02)
- SC #3: Both skills adapt openclaw frontmatter to hermes schema (Plans 34-01, 34-02)
- SC #4: Both skills cross-reference the 4 existing skills via `related_skills` (Plans 34-01, 34-02)
- SC #5: Coexistence decision documented + migrated skills do not break discovery of existing 4 (Plan 34-03 — this plan)

Phase 34 is ready for Phase 37 VALIDATE-03 validation benchmark.

## Self-Check: PASSED

- All 5 created/modified files exist on disk (4 SKILL.md + COEXISTENCE.md + this SUMMARY)
- Both per-task commits present in git log: `a62c1178d` (Task 1), `5cbe555cc` (Task 2)
