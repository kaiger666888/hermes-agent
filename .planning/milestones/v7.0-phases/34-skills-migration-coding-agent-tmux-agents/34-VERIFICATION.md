---
phase: 34-skills-migration-coding-agent-tmux-agents
verified: 2026-06-25T22:48:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: N/A
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 34: Skills Migration (coding-agent + tmux-agents) Verification Report

**Phase Goal:** Users can invoke `coding-agent` and `tmux-agents` capabilities from hermes-agent with the same functionality as openclaw (4 delegation targets for coding-agent; spawn/list/attach/get-results for tmux-agents), with coexistence against existing autonomous-ai-agents skills resolved.
**Verified:** 2026-06-25T22:48:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                                                                                                                                                       | Status     | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `coding-agent` skill is discoverable from hermes-agent and documents 4 working delegation targets (Codex / Claude Code / Pi / OpenCode)                                                                                                     | VERIFIED   | File at `skills/autonomous-ai-agents/coding-agent/SKILL.md` (160 lines), discoverable via directory walk. All 4 targets documented with `**Claude Code:**` / `**Codex:**` / `**OpenCode:**` / `**Pi:**` launch blocks at L78/84/90/96, each with `terminal(command="tmux new-session ... '<agent-cmd>'")` invocation. tmux launch primitives match openclaw source exactly (verified by source diff).                                                                                      |
| 2   | `tmux-agents` skill is discoverable from hermes-agent and documents spawn / list / attach / get-results operations adapted to hermes invocation patterns                                                                                    | VERIFIED   | File at `skills/autonomous-ai-agents/tmux-agents/SKILL.md` (166 lines). All 4 operations present as H3 subsections: `### Spawn a new agent session` (L49), `### List running sessions` (L73), `### Check on a session (get results)` (L81), `### Attach to watch live` (L93). Each uses hermes-native `terminal(command="...", pty=true)` pattern (16 invocations). Bonus ops: send-keys, kill-session.                                                                                  |
| 3   | Both migrated skills carry complete `metadata.hermes.*` frontmatter (tags[], related_skills[], expert_id/metrics where applicable) indistinguishable in schema compliance from native hermes skills                                          | VERIFIED   | Both files parse as valid YAML. coding-agent: `tags: [Coding-Agent, Delegation, tmux, Codex, Claude-Code, OpenCode, Pi, Background-Worker]` (8), `related_skills: [claude-code, codex, opencode, hermes-agent, tmux-agents]` (5). tmux-agents: `tags: [Coding-Agent, tmux, Background-Worker, Session-Management, Delegation, Parallel, Ollama]` (7), `related_skills: [claude-code, codex, opencode, hermes-agent, coding-agent]` (5). Schema indistinguishable from claude-code/codex/opencode (which also omit expert_id/metrics — non-movie-expert category convention). |
| 4   | Both migrated skills declare prerequisites in hermes format with zero unresolved openclaw-format (`metadata.openclaw.requires.{anyBins,config}`) dependencies remaining                                                                       | VERIFIED   | Both files have prose `## Prerequisites` sections (coding-agent L52, tmux-agents L18). Grep for `metadata.openclaw\|metadata.clawdbot\|openclaw message send\|OPENCLAW_STATE_DIR\|ACP thread`: 0 hits in either file. The only `openclaw` mention is author attribution string `"Hermes Agent + openclaw upstream"` (coding-agent L5) — provenance, not runtime dependency.                                                                                                            |
| 5   | Coexistence decision (merge with / supplement / replace existing `skills/autonomous-ai-agents/{claude-code,codex,opencode,hermes-agent}`) is documented and either way the migrated skills do not break discovery of the existing 4          | VERIFIED   | `skills/autonomous-ai-agents/COEXISTENCE.md` (61 lines) contains explicit `## Decision: SUPPLEMENT (not replace)` with ROADMAP Phase 34 SC #5 traceability quote. Capability Matrix (6 skills × 4 dimensions) shows clean partition. All 4 existing skills remain valid YAML with discovery fields intact; git diff of commit `a62c1178d` confirms only +1 line each (additive `related_skills` entries: `coding-agent, tmux-agents` appended). No content removed from any existing skill. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact                                                | Expected                                                    | Status     | Details                                                                                                                                  |
| ------------------------------------------------------ | ----------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `skills/autonomous-ai-agents/coding-agent/SKILL.md`    | Migrated skill with 4 delegation targets + hermes frontmatter | VERIFIED   | 160 lines; source openclaw 153 lines (expansion from schema adaptation). All 4 launch patterns present with terminal(command=) form.    |
| `skills/autonomous-ai-agents/tmux-agents/SKILL.md`     | Migrated skill with spawn/list/attach/get-results + hermes frontmatter | VERIFIED   | 166 lines; source openclaw 143 lines. 4 H3 operation subsections; 16 terminal(command=) invocations.                                   |
| `skills/autonomous-ai-agents/COEXISTENCE.md`           | SUPPLEMENT decision artifact with capability matrix         | VERIFIED   | 61 lines; 6 H2 sections (Decision / Capability Matrix / When to use which / Migration Provenance / Bidirectional Graph / Out of Scope). |
| `skills/autonomous-ai-agents/claude-code/SKILL.md`     | +2 entries in related_skills (additive)                     | VERIFIED   | git diff confirms: `[codex, hermes-agent, opencode]` → `[codex, hermes-agent, opencode, coding-agent, tmux-agents]`                     |
| `skills/autonomous-ai-agents/codex/SKILL.md`           | +3 entries in related_skills (incl. asymmetry fix)          | VERIFIED   | git diff confirms additive edit including new `opencode` reference                                                                       |
| `skills/autonomous-ai-agents/opencode/SKILL.md`        | +2 entries in related_skills (additive)                     | VERIFIED   | git diff confirms additive edit                                                                                                          |
| `skills/autonomous-ai-agents/hermes-agent/SKILL.md`    | +2 entries in related_skills (additive)                     | VERIFIED   | git diff confirms additive edit                                                                                                          |

### Key Link Verification

| From                | To                          | Via                                  | Status   | Details                                                                                                              |
| ------------------- | --------------------------- | ------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------- |
| `coding-agent`      | `claude-code/codex/opencode` skill bodies | `## Prerequisites` cross-references  | WIRED    | coding-agent L57-59 says "see the `claude-code` skill for install + auth" (and codex/opencode)                       |
| `coding-agent`      | `tmux-agents`               | `metadata.hermes.related_skills`     | WIRED    | Bidirectional: coding-agent→tmux-agents (frontmatter) and tmux-agents→coding-agent (frontmatter) both present       |
| `tmux-agents`       | All 4 existing skills       | `metadata.hermes.related_skills`     | WIRED    | tmux-agents related_skills list includes claude-code, codex, opencode, hermes-agent                                  |
| `COEXISTENCE.md`    | ROADMAP Phase 34 SC #5      | Literal SC quote                     | WIRED    | L5 contains the verbatim SC #5 string ("Coexistence decision ... is documented and ... do not break discovery ...")  |
| All 6 skills        | Skill discovery walk        | `SKILL.md` filename + dir layout     | WIRED    | `find skills/autonomous-ai-agents -maxdepth 2 -name SKILL.md` returns all 6; each has `name` + `description` + `tags` |

### Data-Flow Trace (Level 4)

Not applicable — Phase 34 deliverables are declarative skill markdown content (no dynamic data rendering). There are no components consuming runtime data; the equivalent of "data flowing" is the operator invoking tmux commands from the documented patterns, which is verified by Step 7b (Behavioral Spot-Checks) below at the syntactic level.

### Behavioral Spot-Checks

| Behavior                                                | Command                                                                                                                  | Result                                                                                                          | Status |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ------ |
| All 6 skill frontmatters parse as valid YAML            | `python3 -c "import yaml; ..."` (see verification log)                                                                   | 6/6 parsed cleanly; each has `name`, `description`, non-empty `metadata.hermes.tags`                            | PASS   |
| Bidirectional related_skills graph is complete          | python3 graph traversal checking `b in graph[a] and a in graph[b]` for all 10 relevant pairs                             | `BIDIRECTIONAL_GRAPH: COMPLETE`                                                                                 | PASS   |
| coding-agent documents all 4 delegation targets         | `grep -E '^\*\*(Claude Code\|Codex\|OpenCode\|Pi):' coding-agent/SKILL.md`                                                | 4 hits at L78, L84, L90, L96                                                                                    | PASS   |
| tmux-agents documents all 4 core operations             | `grep -E '^### (Spawn\|List\|Attach\|Check)' tmux-agents/SKILL.md`                                                        | 4 hits at L49, L73, L81, L93                                                                                    | PASS   |
| No openclaw runtime tokens remain in migrated skills    | `grep -E 'metadata.openclaw\|metadata.clawdbot\|openclaw message send\|OPENCLAW_STATE_DIR\|ACP thread' <both files>`       | 0 hits                                                                                                          | PASS   |
| tmux launch commands are syntactically valid            | `grep -oE 'tmux new-session -d -s [^ ]+ -x [0-9]+ -y [0-9]+' coding-agent/SKILL.md \| sort -u`                            | `tmux new-session -d -s '$SESSION' -x 200 -y 50` (matches openclaw source pattern exactly)                      | PASS   |
| All 4 SUMMARY commit hashes exist in git history        | `git cat-file -e <hash>` for 87e046b0d, 4c64890c6, a62c1178d, 5cbe555cc                                                  | 4/4 EXISTS with matching commit messages                                                                        | PASS   |

Step 7b note: Phase 34 produces markdown skill content rather than runnable code. Spot-checks at the syntactic / structural level are complete; end-to-end invocation (actually spawning a tmux session with each CLI) is operator-runtime behavior and deferred to Phase 37 VALIDATE-01.

### Probe Execution

Not applicable — Phase 34 PLAN/SUMMARY documents do not declare or imply probe-based verification (no `scripts/*/tests/probe-*.sh` referenced). Verification is via structural / YAML / grep checks.

### Requirements Coverage

| Requirement | Source Plan  | Description                                                                                                                | Status    | Evidence                                                                                                                                                                                                |
| ----------- | ------------ | -------------------------------------------------------------------------------------------------------------------------- --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SKILL-01    | 34-01        | coding-agent skill migrated to canonical path, discoverable, 4 delegation targets all working                              | SATISFIED | File at `skills/autonomous-ai-agents/coding-agent/SKILL.md`; 4 launch blocks present; discoverable via directory walk. Note: "working" in the end-to-end sense is deferred to Phase 37 VALIDATE-01.     |
| SKILL-02    | 34-02        | tmux-agents skill migrated, spawn/list/attach/get-results documented + adapted to hermes invocation patterns              | SATISFIED | File at `skills/autonomous-ai-agents/tmux-agents/SKILL.md`; 4 operation subsections with `terminal(command="...")` hermes-native form.                                                                 |
| SKILL-03    | 34-01, 34-02 | Both skills' frontmatter fully adapted to hermes `metadata.hermes.*` schema (tags[], related_skills[], expert_id/metrics where applicable) | SATISFIED | Both frontmatters parse as YAML; both have tags[] and related_skills[] populated. No expert_id/metrics — consistent with existing claude-code/codex/opencode (these are non-expert skills).             |
| SKILL-04    | 34-01, 34-02 | Prerequisites mapped from openclaw format to hermes format, no open dependencies                                          | SATISFIED | Both have prose `## Prerequisites` sections; zero `metadata.openclaw.requires.*` or `metadata.clawdbot.requires.*` blocks remain; only "openclaw" mention is author attribution (provenance, not dep). |

No orphaned requirements — REQUIREMENTS.md maps exactly SKILL-01..04 to Phase 34 and all 4 are covered by plans.

### Anti-Patterns Found

| File                                                      | Line | Pattern                                           | Severity | Impact                                                                                                                                                                                              |
| -------------------------------------------------------- | ---- | ------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skills/autonomous-ai-agents/coding-agent/SKILL.md`      | 67   | `XXXXXX` matched `XXX` regex                      | Info     | False positive — this is the standard `mktemp -t hermes-worker-prompt.XXXXXX` template (POSIX mktemp placeholder syntax, not a debt marker). Two hits (L67, L142). Not actionable.                  |
| (none other)                                              | -    | No `TBD` / `FIXME` / `HACK` / `TODO` / `PLACEHOLDER` | -        | Clean.                                                                                                                                                                                              |

Debt marker gate: PASS — no genuine `TBD` / `FIXME` / `XXX` debt markers (the only match is the mktemp template pattern, which is a runtime string, not a debt marker).

### Human Verification Required

None for Phase 34 closure. End-to-end skill invocation (triggering the skill via slash command and observing a tmux session spawn + delegation chain complete) is explicitly the responsibility of Phase 37 VALIDATE-01 ("Each migrated skill passes at least 1 benchmark prompt end-to-end"), and Phase 37 is the canonical benchmarking phase per ROADMAP. Phase 34's SCs are all structural (discoverability + frontmatter + prerequisites + coexistence) and have been fully verified programmatically.

### Gaps Summary

No gaps. All 5 ROADMAP Phase 34 Success Criteria verified as TRUE in the codebase:

1. coding-agent is discoverable + documents all 4 delegation targets (Codex / Claude Code / Pi / OpenCode).
2. tmux-agents is discoverable + documents spawn / list / attach / get-results.
3. Both carry complete `metadata.hermes.*` frontmatter schema-compliant with the existing 4 native skills.
4. Both declare prerequisites in hermes prose format with zero openclaw-format dependencies remaining.
5. SUPPLEMENT coexistence decision is documented in `COEXISTENCE.md` with capability matrix; the 4 existing skills remain discoverable (1-line additive related_skills edit each, original content preserved).

All 4 claimed commits exist in git history with matching messages. Migration source line counts confirm substantive (not stub) migration — targets slightly exceed sources due to hermes schema expansion.

---

_Verified: 2026-06-25T22:48:00Z_
_Verifier: Claude (gsd-verifier)_
