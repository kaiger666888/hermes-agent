# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

**Milestone v7.0 — openclaw → hermes-agent Primary Agent Migration** (Phases 34-37)

v7.0 transitions hermes-agent from "movie-experts subsystem owner" to "Kai's primary agent". The milestone migrates capabilities from openclaw: 2 skills (coding-agent + tmux-agents) into `skills/autonomous-ai-agents/`, SOUL.md routing rules integrated non-destructively, USER.md + 133 memory .md files ingested into mem0 backend, and a migration report documenting all transform decisions. This is a migration milestone — phases reflect migration workflow (read source → transform → write target → validate), not new feature development.

**Paradigm shift:** First milestone touching non-movie-experts scope. Project category broadens from "movie-experts subsystem" to "personal hermes agent platform" (PROJECT.md `## What This Is` already evolved).

**Scope confirmation (与 Kai 2026-06-25 对齐):**
- Skills IN: coding-agent + tmux-agents
- Identity: single SOUL.md enhancement (no multi-profile)
- Memory: USER.md migrate + 133 .md files ingest to mem0
- OUT: feishu-* / acp-router / models.json / sessions / multi-profile mechanism

---

## Milestones

- ✅ **v1 Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15)
- ✅ **v2.0 PRFP** — Phases 7-12 (shipped 2026-06-16)
- ✅ **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (shipped 2026-06-17)
- ✅ **v4.0 Methodology Backfill** — Phases 19-21 (shipped 2026-06-18)
- ✅ **v5.0 kais-movie-agent V8.6 Adaptation** — Phases 22-27 (shipped 2026-06-19)
- ✅ **v6.0 Self-Evolution & Feedback Loop** — Phases 28-33 (shipped 2026-06-24)
- 🚧 **v7.0 openclaw → hermes-agent Primary Agent Migration** — Phases 34-37 (in planning)

<details>
<summary>✅ v1 through v6.0 (Phases 0-33) — SHIPPED</summary>

For completed milestone phase details, see:
- `.planning/milestones/v1-ROADMAP.md`
- `.planning/milestones/v3.0-ROADMAP.md`
- `.planning/milestones/v4.0-ROADMAP.md`
- `.planning/milestones/v5.0-ROADMAP.md`
- `.planning/milestones/v6.0-ROADMAP.md` (most recent)

</details>

---

### 🚧 v7.0 — openclaw → hermes-agent Primary Agent Migration (In Planning)

**Milestone Goal:** Migrate openclaw's primary-agent capabilities (coding delegation skills + identity + memory) into hermes-agent so it can serve as Kai's main agent without capability regression.

## Phases

**Phase Numbering:**
- Integer phases (34, 35, 36, 37): Planned v7.0 milestone work
- Decimal phases (e.g., 36.1): Reserved for urgent insertions only

- [x] **Phase 34: Skills Migration (coding-agent + tmux-agents)** - Migrate 2 openclaw skills into `skills/autonomous-ai-agents/` with hermes schema adaptation (frontmatter + prerequisites), resolving coexistence with existing claude-code/codex/opencode skills. (completed 2026-06-25)
- [x] **Phase 35: SOUL.md Identity Enhancement** - Integrate openclaw AIGC routing rules into `~/.hermes/SOUL.md` non-destructively (preserve hermes defaults, mark openclaw origin, adapt trigger modes), with backup + transformation note. (completed 2026-06-25)
- [ ] **Phase 36: Memory Ingestion (USER.md + 133 .md → mem0)** - Migrate USER.md to `~/.hermes/memories/` and batch-ingest 133 openclaw memory .md files (1.3MB) into mem0 backend with idempotent dedup, then spot-check via 5 sample queries.
- [ ] **Phase 37: Validation & Migration Report** - Benchmark-test migrated skills + SOUL.md routing behavior, then produce canonical migration report documenting all transform decisions and explicitly skipped items.

## Phase Details

### Phase 34: Skills Migration (coding-agent + tmux-agents)
**Goal**: Users can invoke `coding-agent` and `tmux-agents` capabilities from hermes-agent with the same functionality as openclaw (4 delegation targets for coding-agent; spawn/list/attach/get-results for tmux-agents), with coexistence against existing autonomous-ai-agents skills resolved.
**Depends on**: Nothing (first v7.0 phase — source files in openclaw workspace are read-only inputs)
**Requirements**: SKILL-01, SKILL-02, SKILL-03, SKILL-04
**Success Criteria** (what must be TRUE):
  1. `coding-agent` skill is discoverable from hermes-agent (appears in skill list / triggerable via slash command) and documents 4 working delegation targets (Codex / Claude Code / Pi / OpenCode)
  2. `tmux-agents` skill is discoverable from hermes-agent and documents spawn / list / attach / get-results operations adapted to hermes invocation patterns
  3. Both migrated skills carry complete `metadata.hermes.*` frontmatter (tags[], related_skills[], expert_id/metrics where applicable) indistinguishable in schema compliance from native hermes skills
  4. Both migrated skills declare prerequisites in hermes format (`prerequisites: {tools, commands, credentials}`) with zero unresolved openclaw-format (`metadata.openclaw.requires.{anyBins,config}`) dependencies remaining
  5. Coexistence decision (merge with / supplement / replace existing `skills/autonomous-ai-agents/{claude-code,codex,opencode,hermes-agent}`) is documented and either way the migrated skills do not break discovery of the existing 4
**Plans**: 3 plans

Plans:
- [x] 34-01-PLAN.md — Migrate coding-agent SKILL.md (Wave 1)
- [x] 34-02-PLAN.md — Migrate tmux-agents SKILL.md (Wave 1, parallel with 34-01)
- [x] 34-03-PLAN.md — Wire bidirectional related_skills graph + write COEXISTENCE.md (Wave 2, depends on 34-01 + 34-02)

**Repo-commit paths:** `skills/autonomous-ai-agents/coding-agent/SKILL.md`, `skills/autonomous-ai-agents/tmux-agents/SKILL.md`, `skills/autonomous-ai-agents/COEXISTENCE.md`, 4 existing skill `related_skills` edits
**Operator-state paths:** None (skills are repo-tracked)
**Hermes-core touch:** No (pure skill content; no Python/JS code changes)
**UI hint**: yes

### Phase 35: SOUL.md Identity Enhancement
**Goal**: Hermes-agent's `~/.hermes/SOUL.md` carries openclaw's AIGC routing intelligence (immediate-execution / cognitive / expert-management / default routes), adapted to hermes trigger modes, while preserving the existing hermes default SOUL content byte-for-byte in its original section.
**Depends on**: Nothing (source `~/.openclaw/SOUL.md` is read-only input; target `~/.hermes/SOUL.md` already exists with hermes defaults)
**Requirements**: SOUL-01, SOUL-02, SOUL-03
**Success Criteria** (what must be TRUE):
  1. User issuing an AIGC immediate-execution command from hermes-agent sees it route to local execution per the integrated openclaw rules (not to LLM chat by default)
  2. User issuing a cognitive-class command sees it route to MCP per the integrated rules; default-class prompts still go to LLM — routing behavior is observable on test prompts
  3. `~/.hermes/SOUL.md` preserves the original hermes-default content (additive integration only — no overwrite); openclaw-origin rules are explicitly tagged with source ("openclaw 迁移") + adaptation date
  4. Original openclaw SOUL.md is preserved verbatim at `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` and a transformation note under `.planning/` records where each openclaw rule landed (integrated / adapted / dropped)
**Plans**: 1 plan

Plans:
- [x] 35-01-PLAN.md — Backup openclaw SOUL.md, integrate routing rules into ~/.hermes/SOUL.md (non-destructive + source-tagged), author transformation note (Wave 1, single plan covers SOUL-01..03)

**Repo-commit paths:** `.planning/phases/35-soul-enhancement/35-*-TRANSFORMATION-NOTE.md` (transformation note only)
**Operator-state paths:** `~/.hermes/SOUL.md` (modified additively), `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (new backup) — these are operator-home-dir changes, NOT repo commits
**Hermes-core touch:** No (SOUL.md is operator state, not core code)
**Non-destructive contract:** SOUL-01 explicit — must NOT overwrite hermes original SOUL content
**UI hint**: yes

### Phase 36: Memory Ingestion (USER.md + 133 .md → mem0)
**Goal**: Kai's personal identity (USER.md) and 133 openclaw memory notes (1.3MB total) are durable in hermes-agent's mem0 backend, queryable from any hermes conversation, with idempotent re-ingest.
**Depends on**: Nothing strictly (source files in openclaw workspace are inputs); soft dependency on Phase 35 since SOUL.md routing may reference memories — but ingestion can proceed independently
**Requirements**: MEM-01, MEM-02, MEM-03, MEM-04
**Success Criteria** (what must be TRUE):
  1. `~/.hermes/memories/USER.md` exists in hermes-compatible format with `openclaw-origin` + migration-date frontmatter annotations
  2. All 133 openclaw `workspace/memory/*.md` files are stored as entries in the mem0 backend (configurable via `plugins/memory/mem0/`); a count query returns 133 ingested entries (or operator-configured subset if partial-ingest decision is made and documented)
  3. From a hermes-agent conversation, 5 sample queries covering AIGC deployment / ComfyUI / Trellis / ACE-Step / CosyVoice topics return relevant ingested memory content (spot-check passes)
  4. Re-running the ingestion command produces zero duplicate entries (idempotent — dedup keyed on content hash or openclaw file path)
**Plans**: TBD

Plans:
- [ ] 36-01: TBD

**Repo-commit paths:** Possibly `plugins/memory/mem0/` config/script additions if batch-ingest tooling is needed (TBD at plan time)
**Operator-state paths:** `~/.hermes/memories/USER.md` (new), mem0 backend storage (operator state)
**Hermes-core touch:** Configuration-only at most (mem0 plugin already exists; may need batch-ingest CLI/config — no core code changes)
**Volume note:** 133 files / 1.3MB — if Phase 36 plan-phase reveals ingestion needs >2 plans (e.g., separate setup + ingest + verify), consider Phase 36.1 insertion. Flag for plan-phase attention.
**UI hint**: yes

### Phase 37: Validation & Migration Report
**Goal**: All migrated capabilities are benchmark-verified regression-free, and a canonical migration report exists documenting every transform decision + every explicitly skipped item with rationale, ready for v8.0 planning reference.
**Depends on**: Phase 34 (skills must exist to benchmark), Phase 35 (SOUL.md must be enhanced to test routing), Phase 36 (memories must be ingested to spot-check — though MEM-03 spot-check may also live here)
**Requirements**: VALIDATE-01, VALIDATE-02, VALIDATE-03
**Success Criteria** (what must be TRUE):
  1. Each migrated skill (coding-agent + tmux-agents) passes at least 1 benchmark prompt end-to-end (trigger fires + delegation chain executes with no regression vs openclaw baseline)
  2. Enhanced SOUL.md produces expected routing behavior on 3+ test prompts (immediate command → local; cognitive → MCP; default → LLM) — verifiable by observation
  3. `.planning/milestones/v7.0-MIGRATION-REPORT.md` exists documenting: all transform decisions (skill frontmatter / prerequisite mapping / SOUL rule adaptation / memory ingestion strategy) + explicitly skipped items (feishu-* / acp-router / models.json / sessions / multi-profile) each with one-line rationale
**Plans**: TBD

Plans:
- [ ] 37-01: TBD

**Repo-commit paths:** `.planning/milestones/v7.0-MIGRATION-REPORT.md` (canonical close-out artifact)
**Operator-state paths:** None (read-only validation against existing state)
**Hermes-core touch:** No
**UI hint**: yes

## Progress

**Execution Order:**
Phases 34 → 35 → 36 → 37. Phases 34, 35, 36 have no strict inter-dependencies (parallel-eligible in principle — disjoint paths: repo skills / operator SOUL / operator memories). Phase 37 MUST run last (validates all three + writes the canonical migration report).

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 34. Skills Migration (coding-agent + tmux-agents) | v7.0 | 3/3 | Complete   | 2026-06-25 |
| 35. SOUL.md Identity Enhancement | v7.0 | 1/1 | Complete   | 2026-06-25 |
| 36. Memory Ingestion (USER.md + 133 .md → mem0) | v7.0 | 0/TBD | Not started | - |
| 37. Validation & Migration Report | v7.0 | 0/TBD | Not started | - |

---

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| SKILL-01 | Phase 34 | Pending |
| SKILL-02 | Phase 34 | Pending |
| SKILL-03 | Phase 34 | Pending |
| SKILL-04 | Phase 34 | Pending |
| SOUL-01 | Phase 35 | Pending |
| SOUL-02 | Phase 35 | Pending |
| SOUL-03 | Phase 35 | Pending |
| MEM-01 | Phase 36 | Pending |
| MEM-02 | Phase 36 | Pending |
| MEM-03 | Phase 36 | Pending |
| MEM-04 | Phase 36 | Pending |
| VALIDATE-01 | Phase 37 | Pending |
| VALIDATE-02 | Phase 37 | Pending |
| VALIDATE-03 | Phase 37 | Pending |

**Coverage: 14 / 14 v7.0 requirements mapped ✓ (no orphans, no duplicates)**

---

*Last updated: 2026-06-25 — v7.0 ROADMAP created (4 phases, 14 reqs, granularity=standard). v6.0 milestone shipped 2026-06-24 (Phases 28-33).*
