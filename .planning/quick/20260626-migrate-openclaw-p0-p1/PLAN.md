---
slug: migrate-openclaw-p0-p1
title: Migrate 5 openclaw skills to hermes-agent (v8.0 P0+P1)
created: 2026-06-26
status: complete
---

# Plan: Migrate 5 openclaw skills to hermes-agent (v8.0 P0+P1)

## Goal

P0 (deep-research, multi-search-engine, auto-dev) + P1 (thinking-partner, pre-mortem-analyst) skill migration from `~/.openclaw/workspace/skills/` into `skills/<category>/` of hermes-agent, with hermes-native frontmatter and bidirectional `related_skills` graph wiring.

Driven by gap analysis: v7.0 only migrated coding-agent + tmux-agents + SOUL.md + mem0 tooling. The 5 highest-leverage general/research skills were untouched.

## Scope

### In scope (5 skills)
1. `deep-research` → `skills/research/deep-research/` (P0)
2. `multi-search-engine` → `skills/research/multi-search-engine/` (P0)
3. `auto-dev` → `skills/software-development/auto-dev/` (P0, heavy ACPX→hermes rewrite)
4. `thinking-partner` → `skills/productivity/thinking-partner/` (P1)
5. `pre-mortem-analyst` → `skills/software-development/pre-mortem-analyst/` (P1)

### Out of scope (deferred to later v8.0+ work)
- feishu-doc/drive/perm/wiki (FEISHU-01/02 design decision pending)
- acp-router (ACP-01 — hermes likely has no analog)
- bgm, chart-image, knowledge-visualizer, soul-guide, etc. (P2 priority — evaluate later)
- All `kais-*` skills (frozen per v5.0 FOUND-08 invariant — belong to sibling kais-movie-agent repo)

## Frontmatter adaptation pattern (applied uniformly)

Source (openclaw):
```yaml
---
name: <skill>
description: "..."
metadata:
  clawdbot: {...}  # DROP
  openclaw: {...}  # DROP
triggers: [...]    # DROP
provides: [...]    # DROP
compatibility: ... # DROP
---
```

Target (hermes):
```yaml
---
name: <skill>
description: "..."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [...]
    category: <category>
    related_skills: [...]
---
```

## Tool name mapping

| openclaw | hermes |
|---|---|
| `web_search(query)` | `web_search(query)` (same) |
| `web_fetch({"url": X})` | `web_extract(urls=[X])` |
| `sessions_spawn(runtime="acp")` | `coding-agent` skill spawn (tmux + Claude Code/Codex/OpenCode/Pi) |
| `sessions_send(sessionKey=...)` | `tmux send-keys -t <session> -l -- '...'` |
| `subagents(action="list")` | `tmux ls` |
| `openclaw message send` | hermes gateway delivery channel block (Telegram/Discord/Slack) |

## Atomic commit plan

1. `feat(skills/research/deep-research): migrate deep-research ...`
2. `feat(skills/research/multi-search-engine): migrate multi-search-engine ...`
3. `feat(skills/software-development/auto-dev): migrate auto-dev ...`
4. `feat(skills/productivity/thinking-partner): migrate thinking-partner ...`
5. `feat(skills/software-development/pre-mortem-analyst): migrate pre-mortem-analyst ...`
6. `feat(skills): wire bidirectional related_skills graph for v8.0 P0/P1 migrations`

## Verification

- All 5 SKILL.md files parse (hermes-style YAML frontmatter, valid `metadata.hermes.*`)
- No remaining `web_fetch` / `sessions_spawn` / `metadata.clawdbot` / `metadata.openclaw` references in migrated skills
- Bidirectional `related_skills` graph: traversing from any new skill → existing peer, and from any touched existing skill → new peer
- `git log --oneline` shows 6 atomic commits with clear scope
