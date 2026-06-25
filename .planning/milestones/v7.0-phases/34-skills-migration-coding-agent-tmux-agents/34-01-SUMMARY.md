---
phase: 34-skills-migration-coding-agent-tmux-agents
plan: 01
subsystem: skills/autonomous-ai-agents
tags: [skill-migration, coding-agent, tmux, delegation, frontmatter, openclaw-port]
dependency_graph:
  requires: []
  provides:
    - "skills/autonomous-ai-agents/coding-agent/SKILL.md — unified tmux-backed delegation skill (Codex/Claude Code/Pi/OpenCode)"
  affects:
    - "Plan 34-03 — will wire bidirectional related_skills on the 4 existing autonomous-ai-agents skills to include coding-agent"
tech_stack:
  added: []
  patterns:
    - "Native hermes SKILL.md frontmatter schema (name/description/version/author/license/platforms/metadata.hermes.{tags,related_skills})"
    - "Prose ## Prerequisites section with **Install:** / **Auth:** labels (replaces openclaw metadata.openclaw.requires.* YAML)"
    - "terminal(command=\"...\", pty=true) native invocation pattern (replaces openclaw bash command:\"...\" wrapper)"
key_files:
  created:
    - "skills/autonomous-ai-agents/coding-agent/SKILL.md (160 lines, net-new)"
  modified: []
decisions:
  - "SUPPLEMENT coexistence: coding-agent supplements (does not replace) the 4 existing single-agent skills; they remain authoritative for single-agent deep-dives"
  - "Drop metadata.openclaw.requires.config (openclaw-internal key, no hermes equivalent); convert anyBins to prose ## Prerequisites"
  - "Genericize 'openclaw message send' to 'platform-appropriate gateway delivery channel' (no hermes CLI equivalent)"
  - "Rename oc-<task>-<rand4> to hermes-<task>-<rand4> for hermes-agent consistency"
  - "Drop ACP thread-bound work exclusion (ACP out of v7.0 scope)"
  - "Drop _meta.json (openclaw pattern; SKILL.md only)"
  - "Drop status.sh script reference (~/.openclaw path) — replaced with cross-reference to tmux-agents skill"
metrics:
  duration: "~8 minutes"
  completed: "2026-06-25"
  tasks: 1
  files_created: 1
  files_modified: 0
---

# Phase 34 Plan 01: coding-agent Skill Migration Summary

Migrated the unified tmux-backed coding-agent delegation skill from `~/.openclaw/skills/coding-agent/SKILL.md` into the hermes-agent repo at `skills/autonomous-ai-agents/coding-agent/SKILL.md`, adapting frontmatter to native hermes schema and rewriting all 7 openclaw-runtime tokens to hermes equivalents.

## What Was Built

**One new file:** `skills/autonomous-ai-agents/coding-agent/SKILL.md` (160 lines).

The skill documents the **unified delegation layer** for spawning background coding workers in tmux. It covers 4 working delegation targets:

| Target | Launch Pattern |
|--------|----------------|
| **Claude Code** | `claude --permission-mode bypassPermissions --print < "$PROMPT"` |
| **Codex** | `codex exec - < "$PROMPT"` |
| **OpenCode** | `opencode run < "$PROMPT"` |
| **Pi** | `pi -p "$(cat "$PROMPT")"` |

Each target runs inside a `tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo` invocation wrapped in the native hermes `terminal(command="...", pty=true)` pattern.

## Frontmatter Adaptation

| openclaw source | hermes target |
|-----------------|---------------|
| `metadata.openclaw.requires.anyBins: [claude, codex, opencode, pi]` | `## Prerequisites` prose listing the 4 CLIs with cross-refs to dedicated skills |
| `metadata.openclaw.requires.config: ["skills.entries.coding-agent.enabled"]` | DROPPED (openclaw-internal key, no hermes equivalent) |
| `metadata.openclaw.emoji` | DROPPED (no equivalent; hermes skills don't carry emoji in frontmatter) |
| (none) | `version: 1.0.0`, `author: "Hermes Agent + openclaw upstream"`, `license: MIT`, `platforms: [linux, macos, windows]` |
| (none) | `metadata.hermes.tags: [Coding-Agent, Delegation, tmux, Codex, Claude-Code, OpenCode, Pi, Background-Worker]` |
| (none) | `metadata.hermes.related_skills: [claude-code, codex, opencode, hermes-agent, tmux-agents]` |

## Openclaw-Runtime Token Rewrites (7 categories)

All 7 openclaw-specific tokens enumerated in the plan's `<interfaces>` section were rewritten:

1. `metadata.openclaw.*` YAML block → dropped entirely
2. `openclaw message send --channel ... --target ... --message ...` → "send exactly one completion or failure message via the active gateway delivery channel (Telegram / Discord / Slack / etc.)"
3. `oc-<short-task-name>-<random4>` session prefix → `hermes-<short-task-name>-<random4>`
4. `~/.openclaw` paths → dropped (replaced with cross-ref to `tmux-agents` skill)
5. `~/Projects/openclaw` exclusion → `~/Projects/hermes-agent` (or wherever the repo lives)
6. `ACP thread-bound work` exclusion clause → dropped (ACP out of v7.0 scope)
7. `openclaw-worker-prompt` mktemp template → `hermes-worker-prompt`
8. `OPENCLAW_STATE_DIR` → dropped

(Plus: `bash command:"..."` wrappers → `terminal(command="...", pty=true)` native hermes pattern.)

## Deviations from Plan

None — plan executed exactly as written. All 6 `<decisions_honored>` were applied verbatim. All verification checks passed on first run.

## Verification Results

All 5 automated verification checks from the plan's `<verify>` block PASSED:

| Check | Result |
|-------|--------|
| File exists + frontmatter parses as valid YAML | PASS — `FRONTMATTER_OK` |
| No `metadata.openclaw` / `openclaw message send` / `~/.openclaw` / `OPENCLAW_STATE_DIR` / `ACP thread` / `oc-scratch` / `oc-$` strings | PASS — 0 matches |
| At least one `hermes-worker-prompt` / `hermes-$(echo` / `hermes-scratch-` occurrence | PASS — 3 matches |
| All 4 required sections present (## Prerequisites / ## Hard rules / ## Launch forms / ## Coexistence) | PASS — 4/4 |
| All 4 delegation targets (Codex: / Claude Code: / OpenCode: / Pi:) appear | PASS — 6 matches (4 launch forms + 2 in other prose) |

## Success Criteria Addressed

- **SKILL-01** (migration + discoverability): file at `skills/autonomous-ai-agents/coding-agent/SKILL.md` is auto-discoverable via skill directory walk; no registry edit needed
- **SKILL-03** (frontmatter schema compliance): `metadata.hermes.tags[]` and `metadata.hermes.related_skills[]` present; schema-indistinguishable from claude-code/codex/opencode
- **SKILL-04** (prerequisites format mapping): `metadata.openclaw.requires.{anyBins,config}` fully converted to prose `## Prerequisites`; zero openclaw-format dependencies remaining

## Notes for Downstream Plans

- **Plan 34-02** (tmux-agents migration) runs in parallel (wave 1) — its work is already committed at `4c64890c6` and does not conflict with this plan.
- **Plan 34-03** will wire the bidirectional `related_skills` graph: the 4 existing skills (claude-code, codex, opencode, hermes-agent) currently do NOT list `coding-agent` in their `related_skills` arrays. This plan intentionally does not touch those files per the plan's `<action>` directive ("Do NOT modify any of the 4 existing skills in this plan").

## Self-Check: PASSED

- FOUND: `skills/autonomous-ai-agents/coding-agent/SKILL.md`
- FOUND: commit `87e046b0d` in git log
