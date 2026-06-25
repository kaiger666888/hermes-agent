# Coexistence Decision: coding-agent + tmux-agents in autonomous-ai-agents

## Decision: SUPPLEMENT (not replace)

As of v7.0 Phase 34 (2026-06-25), `coding-agent` and `tmux-agents` are migrated from openclaw into `skills/autonomous-ai-agents/` as a **supplement** to the existing 4 skills (`claude-code`, `codex`, `opencode`, `hermes-agent`). The existing 4 remain authoritative for single-agent deep-dives (full CLI surface, install/auth/pitfall documentation per tool); the 2 new skills add unified delegation and session-lifecycle capabilities that none of the 4 individually provide. No replacement, no merge, no deprecation. This document is the auditable artifact for **ROADMAP Phase 34 Success Criterion #5**: "Coexistence decision ... is documented and ... the migrated skills do not break discovery of the existing 4".

## Capability Matrix

The 6 skills partition the autonomous-agent space along 4 capability dimensions. A skill marked "Authoritative" is the canonical choice for that capability; "Supports" means the capability is available but a different skill is the primary home; "—" means the skill does not provide this capability.

| Skill | Single-agent deep-dive (full CLI surface) | Unified delegation across multiple agents | Session lifecycle (spawn/list/attach/get-results) | Multi-agent parallel orchestration |
|-------|-------------------------------------------|-------------------------------------------|----------------------------------------------------|------------------------------------|
| `claude-code`   | Authoritative (Claude Code) | — | — | Supports (via tmux) |
| `codex`         | Authoritative (Codex)       | — | — | Supports (via worktrees) |
| `opencode`      | Authoritative (OpenCode)    | — | — | Supports (via workdirs) |
| `hermes-agent`  | Authoritative (Hermes itself) | — | — | Supports (spawning) |
| `coding-agent`  | — | Authoritative (Codex / Claude Code / Pi / OpenCode) | Supports | Supports |
| `tmux-agents`   | — | Supports | Authoritative | Authoritative |

Reading the matrix: the four single-agent skills own column 1 (each is the authoritative source for its named tool's full surface area). `coding-agent` owns column 2 (the unified delegation layer that picks between tools and emits a structured notification block on completion). `tmux-agents` owns columns 3 and 4 (the session-lifecycle primitives and the multi-agent parallel coordination layer). No row owns more than one column authoritatively by accident — the SUPPLEMENT partition is clean.

## When to use which

Operator-facing decision tree. Walk the questions in order; the first match wins.

1. **Need full surface-area docs for ONE agent** — install, auth, every CLI flag, every pitfall, every environment variable, every exit code for a specific tool? → invoke the dedicated skill: `claude-code` (Claude Code), `codex` (Codex), `opencode` (OpenCode), or `hermes-agent` (Hermes itself). These are the deep-dive authorities.
2. **Need to delegate a coding task to a background tmux worker and pick between Codex / Claude Code / Pi / OpenCode with a structured notification block** on completion? → use `coding-agent`. It wraps the spawn-decide-notify loop in one call and is the only skill that knows how to route between the four underlying CLIs.
3. **Need to manage the lifecycle of multiple background agent sessions** — spawn, list, attach, check-status, kill, get-results across many concurrent workers? → use `tmux-agents`. It is the canonical session-primitive layer.
4. **Need both — pick an agent AND manage the session?** → use `tmux-agents` for lifecycle primitives; cross-reference `coding-agent` for the spawn-with-notification pattern and the choose-agent decision block. The two are designed to compose: `coding-agent` for the per-task decision, `tmux-agents` for the multi-session control plane.

## Migration Provenance (Phase 34, v7.0)

Source openclaw paths → hermes-agent target paths. Frontmatter was adapted from the openclaw schema (`metadata.openclaw.*`, `requires.anyBins`, `requires.config`) to the hermes schema (`metadata.hermes.{tags, related_skills}`); openclaw-runtime tokens were rewritten; ACP references were dropped per v7.0 scope.

| openclaw source | hermes-agent target | Notes |
|-----------------|---------------------|-------|
| `~/.openclaw/skills/coding-agent/SKILL.md` | `skills/autonomous-ai-agents/coding-agent/SKILL.md` | frontmatter adapted; `openclaw message send` notification rewritten; ACP thread-bound work references dropped |
| `~/.openclaw/skills/openclaw-skills-tmux-agents/SKILL.md` | `skills/autonomous-ai-agents/tmux-agents/SKILL.md` | frontmatter adapted; `metadata.clawdbot.*` dropped; `scripts/` (spawn.sh / check.sh / status.sh) documented inline but not migrated as files |

## Bidirectional related_skills Graph

All 6 skills' `metadata.hermes.related_skills` lists were updated in Phase 34 Plan 03 to form a complete cross-reference graph:

- `claude-code`, `codex`, `opencode`, `hermes-agent` each had `coding-agent` and `tmux-agents` appended to their `related_skills` lists (additive edit, no removals).
- The reverse links — `coding-agent` and `tmux-agents` referencing the 4 existing skills — were established by Plans 34-01 and 34-02 when the new skills were created.
- A latent asymmetry was also resolved: `codex` now references `opencode` (matching the pre-existing reverse reference from `opencode` → `codex`). The category's discovery graph is now complete.

This bidirectional invariant is the discovery mechanism — an agent traversing the `related_skills` graph from any of the 6 skills can navigate to any relevant peer.

## Out of Scope

The following openclaw items were considered for migration in v7.0 Phase 34 and explicitly left out. Phase 37 VALIDATE-03 should audit this list against the migrated skills to confirm nothing load-bearing is missing.

- `_meta.json` files (openclaw-internal manifest — hermes uses directory-walk skill discovery, no equivalent)
- `scripts/spawn.sh` / `scripts/check.sh` / `scripts/status.sh` from openclaw-skills-tmux-agents (documented inline in the migrated SKILL.md; not committed as files — these are operator-runtime tools, not skill content)
- `README.md` files from openclaw source skills (content folded into the migrated SKILL.md body)
- ACP thread-bound work references (ACP not migrated to hermes per v7.0 scope decision)
- `clawdhub install` automation (clawdhub not migrated per v7.0 scope decision)
- `openclaw message send` notification delivery (rewritten to a generic hermes gateway delivery note in `coding-agent`; no automation shipped)

Cross-references REQUIREMENTS.md `## Out of Scope` table for the milestone-level scope boundary.
