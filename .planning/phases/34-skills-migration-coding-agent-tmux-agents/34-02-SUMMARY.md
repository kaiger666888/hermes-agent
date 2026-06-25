---
phase: 34-skills-migration-coding-agent-tmux-agents
plan: 02
subsystem: skills/autonomous-ai-agents
tags: [skills-migration, tmux, coding-agent, session-lifecycle, frontmatter]
requires: [34-01]
provides: [skills/autonomous-ai-agents/tmux-agents/SKILL.md]
affects: []
tech-stack:
  added: []
  patterns: [hermes-native SKILL.md schema, terminal(command=...) invocation wrapping]
key-files:
  created:
    - skills/autonomous-ai-agents/tmux-agents/SKILL.md
  modified: []
decisions:
  - "SUPPLEMENT coexistence — tmux-agents is session-lifecycle layer, orthogonal to coding-agent delegation + single-agent deep-dives"
  - "scripts/ NOT migrated — documented in body footnotes as upstream artifacts"
  - "Session naming uses hermes-<task>-<rand4> prefix for cross-skill consistency"
  - "metadata.clawdbot.requires.bins:[tmux] -> prose Prerequisites section"
  - "Dropped triggers:, homepage:, metadata.clawdbot.* entirely"
metrics:
  duration: ~1m
  completed: 2026-06-25
---

# Phase 34 Plan 02: tmux-agents Skill Migration Summary

Migrated the openclaw `tmux-agents` skill to `skills/autonomous-ai-agents/tmux-agents/SKILL.md` with hermes-native frontmatter, 4 operations (spawn/list/attach/get-results) documented via `terminal(command="...")` invocation patterns, and operator-runtime scripts referenced as upstream-only.

## What Was Built

### File Created

- **`skills/autonomous-ai-agents/tmux-agents/SKILL.md`** (166 lines) — the migrated tmux session-lifecycle skill.

### Frontmatter Adaptation

Source openclaw frontmatter → hermes native:

| Source (openclaw) | Hermes equivalent |
|---|---|
| `metadata.clawdbot.requires.bins: [tmux]` | Prose under `## Prerequisites` ("**tmux:** installed (`apt install tmux` / `brew install tmux`)") |
| `metadata.clawdbot.install` (brew formula spec) | DROPPED (openclaw-internal automation) |
| `metadata.clawdbot.emoji` | DROPPED |
| `triggers:` top-level list (8 entries) | DROPPED (hermes uses description + tags for discovery) |
| `homepage: https://clawdhub.com/skills/tmux-agents` | DROPPED (clawdhub hub URL not relevant) |
| `author: Jose Munoz` | `author: "Hermes Agent + clawdhub upstream"` (credit both) |
| (none) | `metadata.hermes.tags: [Coding-Agent, tmux, Background-Worker, Session-Management, Delegation, Parallel, Ollama]` |
| (none) | `metadata.hermes.related_skills: [claude-code, codex, opencode, hermes-agent, coding-agent]` |

### Body Structure

1. **Prerequisites** (NEW prose section) — tmux, coding-agent CLI, optional Ollama
2. **Available Agents** — 2 tables (Cloud / Local) preserved verbatim from source with cross-reference note
3. **Operations** — 4 subsections (spawn / list / check-get-results / attach) + "Other operations" (send-instruction, kill). Each uses hermes-native `terminal(command="tmux ...", pty=true/false)` pattern.
4. **When to Use Local vs Cloud** — decision table preserved
5. **Parallel Agents** — 4 parallel spawns using `hermes-{backend,frontend,docs,tests}` session names
6. **Ollama Setup** — preserved verbatim
7. **Tips** — "Clawdbot restarts" rewritten to "hermes-agent restarts (tmux is the process owner)"
8. **Coexistence** (NEW closing section) — distinguishes session-lifecycle (this skill) vs delegation layer (`coding-agent`) vs single-agent deep-dives (`claude-code`, `codex`, `opencode`, `hermes-agent`)

### Scripts Not Migrated

Per CONTEXT.md deferred decision: `scripts/spawn.sh`, `scripts/check.sh`, `scripts/status.sh` are operator-runtime helpers upstream. They are:
- **Mentioned in body footnotes** (4 grep hits) as upstream artifacts
- **NOT created as files** in the hermes-agent repo (negative existence check passes)

Inline tmux equivalents are provided instead, wrapped in `terminal(command="...")`.

## Deviations from Plan

None — plan executed exactly as written. All `<decisions_honored>` from CONTEXT.md and 34-02-PLAN.md applied:
- D (Coexistence: SUPPLEMENT) ✓
- D (Frontmatter mapping: bins→prose) ✓
- D (Drop `triggers:`) ✓
- D (Scripts NOT migrated) ✓
- D (Drop `_meta.json`) ✓ (not applicable — none in source)
- D (Session naming: `hermes-<task>-<rand4>`) ✓

## Verification Results

All 9 automated verification checks from the plan PASS:

| Check | Result |
|---|---|
| 1. File exists at target path | OK |
| 2. Frontmatter YAML parses; name/license/related_skills/tags valid; no triggers/clawdbot/homepage | FRONTMATTER_OK |
| 3. No `metadata.clawdbot\|openclaw\|clawdhub.com\|clawdhub install\|Clawdbot restarts\|^triggers:` strings | NO_OPENCLAW_STRINGS_OK |
| 4. `scripts/spawn.sh` does NOT exist in repo | NO_SPAWN_SH_OK |
| 5. 4 operation H3 subsections (spawn/list/attach/check) | 4_OPS_OK |
| 6. At least one `terminal(command=` invocation | TERMINAL_PATTERN_OK (count=16) |
| 7. `hermes-` session naming examples present | HERMES_NAMING_OK (count=6) |
| 8. Upstream `scripts/*.sh` mentioned in body | SCRIPTS_MENTIONED_OK (count=4) |
| 9. UTF-8 encoding + single trailing newline | TRAILING_NEWLINE_OK |

## Acceptance Criteria

All acceptance criteria from 34-02-PLAN.md met:
- [x] File exists at `skills/autonomous-ai-agents/tmux-agents/SKILL.md`
- [x] Frontmatter parses as valid YAML
- [x] Frontmatter contains name=tmux-agents, description, version, author, license=MIT, platforms, tags (non-empty), related_skills (all 5)
- [x] NO top-level `triggers:` field
- [x] NO `metadata.clawdbot.*` or `metadata.openclaw.*` block
- [x] NO `clawdhub.com` URL, `clawdhub install` command, or "Clawdbot restarts" reference
- [x] Body has 4 operation subsections (spawn/list/attach/check+get-results) verified by H3 grep
- [x] At least one `terminal(command="...")` invocation pattern
- [x] Scripts mentioned in body footnotes but NOT present as files (negative existence check)
- [x] Session naming uses `hermes-` prefix
- [x] UTF-8 with single trailing newline

## Success Criteria

- **SKILL-02 (tmux-agents migration + 4 ops documented):** file in correct directory; spawn/list/attach/get-results all present with hermes invocation patterns ✓
- **SKILL-03 (frontmatter schema compliance):** tags[], related_skills[] present ✓
- **SKILL-04 (prerequisites mapping):** `metadata.clawdbot.requires.bins` → prose `## Prerequisites` ✓

## Known Stubs

None — no hardcoded empty values, placeholder text, or unwired data sources.

## Threat Flags

None. The threat model in 34-02-PLAN.md assigned:
- T-34-04 (Tampering / frontmatter YAML): mitigated via `yaml.safe_load` verify gate (Check 2 PASSED)
- T-34-05 (EoP / tmux spawn commands): accepted — analogous to existing claude-code/codex/opencode skill content, no new privilege surface
- T-34-06 (Info Disclosure / Ollama section): accepted — only public install commands

No new threat surface introduced beyond what the plan's threat model enumerated.

## Self-Check: PASSED

- [x] `skills/autonomous-ai-agents/tmux-agents/SKILL.md` — FOUND
- [x] Commit `4c64890c6` — FOUND (`feat(34-02): migrate tmux-agents skill to hermes schema`)
