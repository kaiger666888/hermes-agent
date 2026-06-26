---
slug: migrate-openclaw-p0-p1
title: Migrate 5 openclaw skills to hermes-agent (v8.0 P0+P1)
created: 2026-06-26
completed: 2026-06-26
status: complete
commits: 6
---

# Summary: Migrate 5 openclaw skills to hermes-agent (v8.0 P0+P1)

**Status: COMPLETE.** All 5 skills migrated + bidirectional related_skills graph wired. 6 atomic commits.

## Commits

| # | Commit | Skill | Files |
|---|--------|-------|-------|
| 1 | `84e94c4ef` | deep-research → skills/research/deep-research/ | 2 (SKILL.md + references/examples.md) |
| 2 | `9bf8c8f3c` | multi-search-engine → skills/research/multi-search-engine/ | 3 (SKILL.md + 2 refs) |
| 3 | `7c77a9115` | auto-dev → skills/software-development/auto-dev/ | 3 (SKILL.md + 2 refs) |
| 4 | `2aadf0a0d` | thinking-partner → skills/productivity/thinking-partner/ | 1 (SKILL.md only) |
| 5 | `5da7ef1da` | pre-mortem-analyst → skills/software-development/pre-mortem-analyst/ | 3 (SKILL.md + 2 refs) |
| 6 | `eb2214004` | Bidirectional related_skills graph wiring | 5 (existing skills touched) |

Total: 17 files created + 5 files modified, 6 atomic commits.

## What was migrated

### P0 skills (3)
1. **deep-research** — Multi-round research skill with configurable iterations (1-5 rounds × quick/medium/deep depth). Generates structured reports with citations. Uses `web_search` + `web_extract`. Adapted from openclaw's clawdbot-flavored version; `EXAMPLES.md` moved to `references/examples.md`.
2. **multi-search-engine** — 16-engine web search integration (7 CN + 9 Global) with no API key requirement. Includes advanced operators, time filters, privacy engines, and WolframAlpha knowledge queries. References deep-dive guides for CN + international engines preserved verbatim.
3. **auto-dev** — Full-stack development pipeline orchestrator (Hermes as PM, coding-agent as Developer). Heavy adaptation: ACPX `sessions_spawn` → tmux-backed coding-agent spawn; openclaw-flavor message routing → hermes gateway delivery block; scripted `gsd-auto-init.cjs` (workaround for openclaw's ACPX-only AskUserQuestion limitation) → direct `/gsd:new-project` invocation since hermes IS the primary agent.

### P1 skills (2)
4. **thinking-partner** — Collaborative Socratic questioning skill for exploring complex problems without rushing to solutions. 5 core behaviors + workflow + 5 key prompts. Clean port.
5. **pre-mortem-analyst** — Project failure pre-imagination tool (30% more effective than risk assessment per Gary Klein research). 6-step process + 4-category failure matrix. References include framework methodology + 3 worked examples (GolfTab/TISA/TeddySnaps).

## Bidirectional related_skills graph

After commit 6, the discovery graph is complete. An agent traversing from any new skill can navigate to relevant peers, and vice versa:

- `arxiv` → `deep-research`, `multi-search-engine`
- `llm-wiki` → `deep-research`
- `blogwatcher` → `deep-research` (also gained its first `related_skills` field)
- `plan` → `auto-dev`, `pre-mortem-analyst`, `thinking-partner`
- `coding-agent` → `auto-dev`
- `deep-research` → `arxiv`, `llm-wiki`, `multi-search-engine`, `blogwatcher`
- `multi-search-engine` → `deep-research`, `arxiv`
- `auto-dev` → `coding-agent`, `tmux-agents`, `plan`, `hermes-agent-skill-authoring`
- `thinking-partner` → `pre-mortem-analyst`, `plan`
- `pre-mortem-analyst` → `plan`, `thinking-partner`, `requesting-code-review`

## Key adaptation decisions

| Decision | Rationale |
|---|---|
| Drop `scripts/gsd-auto-init.cjs` from auto-dev | The script was a workaround for openclaw's ACPX-only runtime not handling Claude Code's `AskUserQuestion`. Hermes IS the primary agent — it invokes `/gsd:new-project` natively with no intermediary. |
| Map `web_fetch({"url": X})` → `web_extract(urls=[X])` | Hermes web tool is named `web_extract` and takes a list, not a single url-keyed object. 57 occurrences across multi-search-engine SKILL.md + 2 refs. |
| Drop ALL `metadata.clawdbot.*` / `metadata.openclaw.*` / `triggers` / `provides` / `compatibility` | openclaw-runtime-specific fields with no hermes equivalent. Hermes uses `metadata.hermes.{tags, related_skills}` for discovery. |
| Copy `references/gsd-commands.md` verbatim into auto-dev | The file already documents hermes-native `/gsd:*` commands (52 subcommands). It was likely written by openclaw for delegating to Claude Code via ACPX but the content applies equally to hermes native. |
| Keep Artem-specific pre-mortem examples verbatim | They're illustrative; the methodology generalizes. Operator can swap in domain-specific examples later. |
| Place thinking-partner in `productivity/` not `software-development/` | Thinking-partner is a general cognitive tool, not software-specific. `productivity/` is hermes' catch-all for non-engineering tools. |
| Place pre-mortem-analyst in `software-development/` | Pre-mortem is typically applied to software projects; sits naturally next to `plan`, `systematic-debugging`, `spike`. |

## Operator action items

None — all structural work is committed. No runtime smoke-tests deferred (skills are static markdown; no live API calls or external services to verify).

If operator wants to validate at runtime, suggest:
- Invoke each new skill from a hermes conversation (e.g., `研究 2026 LLM 部署趋势` should surface `deep-research`)
- Verify `related_skills` graph traversal works in `/skill` discovery output

## Deferred to v8.0+ later work

The remaining openclaw skills not addressed in P0+P1:
- **P2 (evaluate later):** `bgm`, `chart-image`, `knowledge-visualizer`, `experiment-research`, `arxiv-watcher`, `habit-tracker`, `rssaurus`, `notion-skill`, `project-crew`, `smart-image-search`, `reverse-image-search`, `soul-guide`
- **Design decision pending:** `feishu-doc/drive/perm/wiki` (FEISHU-02 merge-vs-keep-4)
- **Likely no analog:** `acp-router` (openclaw-internal scheduler)
- **Out of scope (frozen):** All `kais-*` skills per v5.0 FOUND-08 invariant
- **Already covered:** `claude-code-via-openclaw` (replaced by `autonomous-ai-agents/coding-agent`), `chromadb-memory` (replaced by mem0 plugin)

## File count correction

| Metric | Value |
|--------|-------|
| Skills migrated | 5 (planned: 5) |
| Files created | 12 (SKILL.md ×5 + references ×7) |
| Files modified | 5 (existing skills touched for related_skills wiring) |
| Commits | 6 (planned: 6) |
| Net diff | 17 files, ~1962 insertions |

---

*Completed: 2026-06-26 — v8.0 P0+P1 skill migration batch.*
