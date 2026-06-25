# Phase 35 Transformation Note — openclaw SOUL.md Migration

- **Migration date:** 2026-06-25
- **Source file:** `~/.openclaw/SOUL.md` (24 lines, 975 bytes, mtime `2026-05-12 14:15:12 +0800`)
- **Backup file:** `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (verbatim, mtime preserved via `cp -p`)
- **Target file:** `~/.hermes/SOUL.md` (integrated; 4519 bytes post-integration; original 513-byte Hermes identity preserved byte-for-byte in Section A; openclaw routing rules integrated into Section C under H2 `## openclaw 迁移规则 (Source: openclaw SOUL.md, migrated 2026-06-25)`)
- **Requirements closed:** SOUL-01, SOUL-02, SOUL-03
- **Repo-commit artifact:** This document is the **only** repo-commit artifact for Phase 35.

---

## Section 1 — Hermes-target baseline correction

`35-CONTEXT.md` described the hermes `SOUL.md` as "0 bytes (empty)". Pre-integration inspection at Task 1 revealed this was wrong: the file actually contained **513 bytes** of Nous Research identity content on a single line, beginning `You are Hermes Agent, an intelligent AI assistant created by Nous Research...` and ending `...targeted and efficient in your exploration and investigations.`

SC #3 ("preserve original hermes-default content byte-for-byte") was therefore treated as a **non-trivial** constraint, not trivially satisfied. The integration is strictly **additive**: the original 513-byte paragraph is reproduced verbatim as Section A (the opening paragraph of the integrated file), and all openclaw-origin content is appended below it under a clearly demarcated H2 header. No character of the original Hermes identity was altered.

Verify step (a) of Task 2 confirms this: `head -n 1 ~/.hermes/SOUL.md` matches the pre-integration baseline string `You are Hermes Agent, an intelligent AI assistant created by Nous Research`.

---

## Section 2 — Identity statement fate

**Source element (openclaw, line 4):**
> 你是 Kais AIGC 短剧生产管线的主控 Agent。你是"手"——负责执行，Hermes 是"脑"——负责思考。

**Fate: DROPPED** (from the integrated file body).

**Rationale:** The openclaw identity assumed a **two-agent topology** — openclaw = "手" (hand, executor), hermes = "脑" (brain, thinker). Hermes is a **single-agent** model; there is no "other agent" to be the brain. Carrying the "手/脑" framing into the integrated SOUL.md would contradict hermes' Section A identity ("You are Hermes Agent..."). The identity framing is therefore dropped from the integrated file with an explicit adaptation note under Section B of `~/.hermes/SOUL.md`:

> Adaptation note: openclaw's two-agent "手/脑" identity framing is dropped (no direct single-agent analog); hermes' Section A identity statement remains authoritative.

The original openclaw identity statement is preserved verbatim in the backup file at `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (operator-only, not repo-tracked — see Section 7).

---

## Section 3 — Immediate-execution rules (6 tokens)

openclaw source (lines 8-10): a single regex `^(?i)(draw|video|tts|run|status|queue)` routed to `local_skill`, bypassing the cognitive layer.

| Token | openclaw Target | Hermes Adaptation | Fate |
|-------|-----------------|-------------------|------|
| `draw` | `local_skill` | Local AIGC skill execution (`skills/autonomous-ai-agents/*` and `skills/movie-experts/*` as applicable); bypass deep cognitive routing. | **integrated + adapted** |
| `video` | `local_skill` | (same as `draw`) | **integrated + adapted** |
| `tts` | `local_skill` | (same as `draw`) | **integrated + adapted** |
| `run` | `local_skill` | (same as `draw`) | **integrated + adapted** |
| `status` | `local_skill` | (same as `draw`) | **integrated + adapted** |
| `queue` | `local_skill` | (same as `draw`) | **integrated + adapted** |

**Adaptation rationale:** All 6 tokens shared the same openclaw target (`local_skill`), so they share the same hermes adaptation. Hermes' equivalent of "local skill execution" is its skills tree (`skills/autonomous-ai-agents/`, `skills/movie-experts/`) invoked via natural-language skill discovery. The regex notation is rewritten as natural-language routing guidance in `### 即时执行命令 (Immediate Execution — Local Skill)` because hermes is a single-agent model with skill-discovery, not a regex-dispatch router.

All 6 tokens are listed in the integrated file's "Triggers:" line for that section.

---

## Section 4 — Cognitive MCP routes (5 routes)

openclaw assumed a different MCP server topology: `mcp:hermes_plan`, `mcp:hermes_memory_write`, `mcp:hermes_memory_read`, `mcp:hermes_reflect`, `mcp:hermes_learn`. Hermes' actual MCP server (`mcp_serve.py`, per `./CLAUDE.md` §"Architecture → mcp_serve.py") exposes tools like `conversations_list`, `messages_read`, `messages_send`, `events_poll`, `permissions_respond`, `channels_list` — these **do not match** openclaw's targets. Each route is adapted below to the closest hermes-native surface.

| Trigger Pattern | openclaw MCP Target | Hermes Equivalent | Fate |
|-----------------|---------------------|-------------------|------|
| `plan`, `规划`, `剧本`, `分镜`, `怎么拍`, `帮我设计` | `mcp:hermes_plan` | Skill discovery for planning/screenplay/scene-builder skills (e.g., `/skill screenplay`, `/skill scene_builder` in `skills/movie-experts/`). | **integrated + adapted** (no direct plan-MCP; hermes uses skill-discovery) |
| `记住`, `保存`, `这个角色`, `风格设定`, `更新设定` | `mcp:hermes_memory_write` | Memory write via mem0 backend (`plugins/memory/mem0/`). Operator-configurable; until Phase 36 ingestion completes, route to note-taking via terminal/file tools. | **integrated + adapted** (memory plugin surface) |
| `之前`, `上次`, `那个项目`, `角色设定`, `查一下` | `mcp:hermes_memory_read` | Memory query via mem0 backend; fallback to `AGENTS.md` / conversation history recall. | **integrated + adapted** |
| `复盘`, `总结`, `为什么不好`, `哪里有问题` | `mcp:hermes_reflect` | Structured reflection using terminal/file tools to capture lessons-learned; curator review (`agent/curator.py`) may also fire. | **integrated + adapted** (curator is hermes' built-in reflection) |
| `学习`, `进化`, `改进`, `提升` | `mcp:hermes_learn` | Self-improvement via curator + memory write-back; surface improvement as a concrete proposed edit to skills/refs. | **integrated + adapted** (no discrete `learn` MCP; curator + memory forms the loop) |

**Adaptation rationale (applies to all 5):** Hermes has no `mcp:hermes_*` topology — its MCP server speaks a different vocabulary. The closest hermes-native surfaces are: skill discovery (for the planning route), the mem0 memory plugin (for the two memory routes), and the curator (`agent/curator.py`) for reflection and learning loops. Each adaptation is expressed as **natural-language routing guidance** in the integrated file, not raw regex+MCP notation.

---

## Section 5 — Expert-management command (1 command)

| Command | openclaw Target | Hermes Adaptation | Fate |
|---------|-----------------|-------------------|------|
| `/expert` | `local_skill:expert_manager` (manages approve/reject/status/rollback) | Expert management via hermes slash commands (e.g., `/skill` discovery + skill pruning through `agent/curator.py`); manage approve/reject/status/rollback as applicable. | **integrated + adapted** |

**Adaptation rationale:** Hermes' `/skill` discovery + curator review (`agent/curator.py:1388` `run_curator_review`) covers the skill lifecycle that openclaw's `expert_manager` handled. The integrated file's `### 专家管理命令 (Expert Management)` section expresses this as natural-language routing guidance.

---

## Section 6 — Default route (1 rule)

| Trigger | openclaw Target | Hermes Adaptation | Fate |
|---------|-----------------|-------------------|------|
| Simple chat (no other category match) | Local LLM `GLM-4-flash` | Configured local LLM (per `cli-config.yaml` `model:`) | **integrated + adapted** (rule integrated; `GLM-4-flash` hard reference **DROPPED**) |

**Drop rationale:** openclaw hardcoded `GLM-4-flash` as the default chat model. Hermes supports arbitrary model/provider switching via `cli-config.yaml` `model:` and the `--model` / `--provider` CLI flags (per `./CLAUDE.md` §"Configuration"). Hardcoding a specific model in `SOUL.md` would constrain the operator and contradict hermes' model-agnostic design. The default-route **rule** is integrated (simple chat goes to the configured LLM), but the `GLM-4-flash` literal is **dropped** from the integrated file — verify step (g) enforces `! grep -q "GLM-4-flash"` on `~/.hermes/SOUL.md`.

(For audit completeness: the literal string `GLM-4-flash` appears in this transformation note — that is expected and correct. The drop applies to the operator-state `~/.hermes/SOUL.md`, not to this repo-commit audit document.)

---

## Section 7 — Operator-state vs repo-commit file split

The integrated `~/.hermes/SOUL.md` and the backup `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` are **operator-state files**. They live in `~/.hermes/` (operator home, outside the `hermes-agent` repo worktree) and are **NOT git-committed** by this plan. They will not appear in `git status` of the `hermes-agent` repo because they are outside the worktree.

This transformation note under `.planning/phases/35-soul-md-identity-enhancement/` is the **only repo-commit artifact** for Phase 35 and serves as the audit trail for the operator-state changes. This split follows ROADMAP §"Repo-commit paths" / "Operator-state paths".

The repo-commit (`docs(35):` — see Phase 35 plan `<output>` block) stages **only** this file:

```
git add .planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md
git commit -m "docs(35): SOUL.md identity enhancement — transformation note (SOUL-01..03)"
```

Operators can self-review the operator-state changes by diffing the integrated `~/.hermes/SOUL.md` against the verbatim backup `~/.hermes/SOUL.md.openclaw-backup-2026-06-25`.

---

## Section 8 — Success-criteria traceability

| SC | Requirement | Satisfied by |
|----|-------------|--------------|
| SC #1 | Immediate-execution routes locally | Section `### 即时执行命令 (Immediate Execution — Local Skill)` of integrated `~/.hermes/SOUL.md` — all 6 tokens (`draw`/`video`/`tts`/`run`/`status`/`queue`) routed to local AIGC skill execution |
| SC #2 | Cognitive routes to MCP/memory/skill; default routes to LLM | Sections `### 认知类命令` (5 sub-routes) + `### 默认 (Default)` of integrated `~/.hermes/SOUL.md` |
| SC #3 | Non-destructive + source-tagged | Section A of integrated `~/.hermes/SOUL.md` (513-byte Hermes identity preserved byte-for-byte) + H2 header `## openclaw 迁移规则 (Source: openclaw SOUL.md, migrated 2026-06-25)` + per-category `> **Source:** openclaw 迁移 (2026-06-25)` annotations (9 source-tag occurrences, 10 date occurrences — both ≥ 5) |
| SC #4 | Backup + transformation note | `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (Task 1, verbatim `cp -p`, mtime preserved) + this document (Task 3, repo-commit) |

All four SC verified by automated checks during execution (see plan `<verification>` block). Phase 35 is complete.
