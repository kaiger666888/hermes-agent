# Phase 34: Skills Migration (coding-agent + tmux-agents) - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure-phase classification)

<domain>
## Phase Boundary

Migrate 2 skills from `~/.openclaw/skills/` to `skills/autonomous-ai-agents/` in hermes-agent repo, adapting their frontmatter to hermes schema (`metadata.hermes.*` + `prerequisites`), and resolving coexistence with the 4 existing autonomous-ai-agents skills (`claude-code`, `codex`, `opencode`, `hermes-agent`).

**Source files (read-only inputs):**
- `~/.openclaw/skills/coding-agent/SKILL.md` — unified tmux-backed delegation skill for Codex / Claude Code / Pi / OpenCode
- `~/.openclaw/skills/openclaw-skills-tmux-agents/` — full skill dir (SKILL.md + scripts/ + README.md + _meta.json) for background tmux agent session management

**Target outputs (repo-commit):**
- `skills/autonomous-ai-agents/coding-agent/SKILL.md`
- `skills/autonomous-ai-agents/tmux-agents/SKILL.md` (+ optionally `scripts/` if needed)

Out of scope: Python/JS code changes; modifying the existing 4 autonomous-ai-agents skills (only documenting coexistence decision).

</domain>

<decisions>
## Implementation Decisions

### Smart Discuss Auto-Accept (Infrastructure Classification)

Phase 34 was classified as **infrastructure-only** per autonomous-smart-discuss criteria:
1. Goal keywords match: "migration" ✓
2. All success criteria are technical (skill discoverability, frontmatter schema compliance, prerequisites format, coexistence decision documented)
3. No novel user-facing behavior — features already exist in openclaw, this is a port

All implementation choices at Claude's discretion within the constraints set by ROADMAP SC #1–#5 and existing hermes skill conventions. Plan-phase will resolve:
- **Coexistence decision**: coding-agent is a unified delegation layer (supplements the 4 single-agent skills, doesn't replace them — they remain authoritative for single-agent deep-dives); tmux-agents is session-lifecycle management (orthogonal — supplements)
- **Frontmatter adaptation**: map `metadata.openclaw.requires.anyBins` → `prerequisites.commands`; map `metadata.openclaw.requires.config` → `prerequisites.credentials` or drop (config keys are openclaw-internal)
- **Notification block**: openclaw's `openclaw message send` must be replaced with hermes equivalent (likely hermes gateway delivery — check during plan)
- **Session naming**: keep `oc-<task>-<rand4>` or rename to hermes convention (e.g. `hermes-<task>-<rand4>`)

### Claude's Discretion

All remaining implementation choices (exact wording, prerequisite mapping granularity, whether to migrate scripts/ for tmux-agents, how to phrase coexistence rationale) deferred to plan-phase research + planner judgment.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (target side — hermes-agent)

- `skills/autonomous-ai-agents/DESCRIPTION.md` — category-level description (1 line; states scope is "spawning and orchestrating autonomous AI coding agents")
- `skills/autonomous-ai-agents/claude-code/SKILL.md` — native hermes skill schema reference (frontmatter uses `metadata.hermes.{tags, related_skills}`, has `platforms: [linux, macos, windows]` field, has `license` + `author` + `version`)
- `skills/autonomous-ai-agents/codex/SKILL.md`, `opencode/SKILL.md`, `hermes-agent/SKILL.md` — 3 more reference examples for schema
- Each native skill documents installation + auth + invocation modes — coding-agent can cross-reference these instead of duplicating

### Established Patterns

- Hermes skills are markdown-only (`SKILL.md` uppercase). No `_meta.json` (openclaw pattern — drop during migration)
- Frontmatter required: `name`, `description`, optional `version`/`author`/`license`/`platforms`, then `metadata.hermes.{tags, related_skills, expert_id?, metrics?}`
- Prerequisites declared inline as prose under `## Prerequisites` heading (claude-code uses `**Install:**`, `**Auth:**` etc.) — openclaw used `metadata.openclaw.requires.{anyBins, config}` YAML which has no hermes equivalent
- `related_skills` graph is bidirectional — adding `coding-agent` to the category means updating existing skills' `related_skills` lists to include it

### Integration Points

- Skill discovery is via directory walk — placing `coding-agent/SKILL.md` and `tmux-agents/SKILL.md` under `skills/autonomous-ai-agents/` makes them auto-discoverable. No registry edit.
- Cross-references to existing 4 skills go in `metadata.hermes.related_skills` arrays.

</code_context>

<specifics>
## Specific Ideas

- Coexistence decision is the load-bearing design choice (SC #5). Plan-phase must produce explicit rationale. Working hypothesis (subject to plan validation): **SUPPLEMENT** — coding-agent and tmux-agents add capabilities (unified delegation + session lifecycle) that the existing 4 single-agent skills don't provide; no replacement.
- openclaw's notification block uses `openclaw message send` which is openclaw-specific. Plan-phase must either (a) rewrite to hermes equivalent, (b) genericize to "use platform-appropriate completion message", or (c) note as runtime-config the operator fills in.

</specifics>

<deferred>
## Deferred Ideas

- coding-agent's "ACP thread-bound work" exclusion references openclaw's ACP system — not migrated to hermes (per v7.0 scope out). Skill body should drop or genericize the reference.
- openclaw-skills-tmux-agents includes `scripts/` (spawn.sh, status.sh, check.sh) — whether to migrate scripts into hermes-agent repo or just document them in SKILL.md body is deferred to plan-phase (likely document-only, since scripts are operator-runtime tools not skill content).
- Multi-agent skills beyond coding-agent + tmux-agents (e.g. acp-router, feishu-*) — explicitly OUT of v7.0 scope per ROADMAP.

</deferred>
