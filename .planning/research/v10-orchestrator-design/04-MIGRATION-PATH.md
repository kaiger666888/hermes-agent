# 04 — Migration Path (15-Expert Transform + Memory Schema Migration + Retained-Phases Allowlist)

**Status:** Design-locked (v10.0 design-only milestone — zero code, zero SKILL.md edits, zero plugin edits)
**Phase:** 49-migration-path (single deliverable)
**Audience:** Kai (reviewer) · v11.0 PoC implementer (primary consumer) · v12+ transform-CLI implementer (secondary consumer)
**Reading time:** ~45 min (1,300+ lines bilingual)
**Stability markers:**
- **LOCKED-CITE:** Phase 44 决策 1-7 (`00-FIRST-PRINCIPLES.md §2.1-§2.7`)
- **LOCKED-CITE:** Phase 45 schemas (`agents-schema.yaml` 18 fields + `memory-record-schema.yaml` 10 mandated fields)
- **LOCKED-CITE:** Phase 46 protocol (`round-table-state-schema.yaml`)
- **LOCKED-CITE:** ARCHITECTURE §1.1 + §1.2 + §2 + §6 (5-field mapping skeleton + 15-expert table + transform procedure + repo impact)
- **LOCKED-CITE:** STACK §3.2 Tool 7 (`run_python_phase` boundary-tool signature)
- **LOCKED-CITE:** PITFALLS §P14 (3 schema-migration mitigations — `schema_version` + safe-default + dry-run)
- **ELABORATES:** ARCHITECTURE §1.2 + §2 (5-field mapping → 75-cell granularity)
- **NET-NEW:** 75-cell per-expert edge cases · `default_invocation` failure-mode matrix · v6.0 FeedbackStore → memory-record-schema migration plan · `retained_python_phases` allowlist value (Steps 0/6.5/7/10/11/12/15) · legacy `agent_id=hermes` sunset policy
**Confidence:** HIGH — built entirely from in-repo design docs + v6.0 `agent/feedback_store.py` ground truth + MEMORY.md milestone notes

---

## §0 阅读指南 (Reading Guide)

### 0.1 Chapter Map

| § | Title | Lines (approx) | Audience | Stability |
|---|-------|-----------------|----------|-----------|
| §0 | 阅读指南 + chapter map + 3-audience guide + consumption preamble | ~70 | all | — |
| §1 | Framing + scope + SC mapping + roadmap placement + 4 deliverables + 15-expert quick-glance + out-of-scope | ~300 | all | LOCKED-CITE |
| §2 | **15-Expert × 5-Field Transform 规则表 (SC#2 75-Cell Deep-Dive)** | ~430 | PoC implementer | ELABORATES §1.2 + §2 |
| §3 | **`default_invocation: skill_fallback → mcp_tool` 切换机制 (SC#3 Deep-Dive)** | ~220 | PoC implementer | NET-NEW |
| §4 | **Memory Schema 迁移计划 (SC#4 + P14 Mitigation Deep-Dive)** | ~280 | PoC implementer + operator | NET-NEW |
| §5 | **Retained-Phases Allowlist + Legacy mem0 Policy (SC#5 + OQ-3 + OQ-10 Resolution)** | ~200 | PoC implementer | NET-NEW |
| §6 | Phase 44 7 决策 Cross-Validation Audit + OQ/P14 Resolution | ~150 | reviewer + 51 VALIDATE | — |
| §7 | Downstream Citation Guide + Coherence 声明 + References | ~100 | downstream doc authors | — |

### 0.2 Three-Audience Guide

- **Kai (reviewer):** Read §1 (framing), §6 (7 决策 audit + OQ/P14 resolution), §7.1 (coherence 声明). Skim §2-§5 headers + §2.18 (FOUND-08 invariant) + §4.9 (P14 RESOLVED). Use §1.3 SC mapping as the verification checklist.
- **v11.0 PoC implementer (primary consumer):** Read §2 (75-cell transform table) end-to-end before starting any `*.agent.yaml`. Read §3.4 (transition path) before any `default_invocation` switch. Read §4.5 + §4.7 (dry-run + 6-step migration) before touching v6.0 FeedbackStore. Read §5.2 (retained-phases 7 steps) before any `run_python_phase` invocation. §7.0 downstream citation card tells you which sections to copy into PoC tickets.
- **v12+ transform-CLI implementer (secondary consumer):** §2.1 5-field default + edge case pattern is the CLI's rule engine. §2.2-§2.16 per-expert persona excerpts are the CLI's regression fixtures. §4.3 source→target field mapping table is the CLI's dry-run core. §6.1 audit row 5 (决策 5 α agent form) reaffirms operator ownership — CLI must NOT auto-overwrite hand-tuned persona (see §2.18 additive invariant).

### 0.3 Consumption Preamble (What This Doc CITEs vs NET-NEWs)

**CITE-ONLY (do NOT re-derive — re-derivation causes cross-doc drift):**

| Source | What this doc cites | Where cited |
|--------|---------------------|-------------|
| Phase 44 `00-FIRST-PRINCIPLES.md §2.1` | 决策 1 — T6 协议 (Hermes owns `run_python_phase` MCP tool surface) | §1.1, §3.1, §5.1, §6.1 row 1 |
| Phase 44 `00-FIRST-PRINCIPLES.md §2.2` | 决策 2 — B3a Python runner 增量迁移 (LOAD-BEARING root for SC#5) | §1.1, §5.0-§5.4, §6.1 row 2 |
| Phase 44 `00-FIRST-PRINCIPLES.md §2.5` | 决策 5 — α agent form (YAML + persona + tools + refs + memory_scope + lineage) | §1.1, §2.0, §6.1 row 5 |
| Phase 44 `00-FIRST-PRINCIPLES.md §2.6` | 决策 6 — per-agent memory + curator-driven 自进化 | §1.1, §4.0, §6.1 row 6 |
| Phase 44 `00-FIRST-PRINCIPLES.md §2.7` | 决策 7 — Hermes controls structure, CC controls content | §1.1, §3.0, §5.4, §6.1 row 7 |
| Phase 45 `agents-schema.yaml` | 18-field schema (esp #6 `memory_scope`, #7 `lineage`, #18 `default_invocation`) | §2.0, §3.1 |
| Phase 45 `memory-record-schema.yaml` | 10 mandated fields + `schema_version` (line 353) + Layer-2 independence | §4.2, §4.4 |
| Phase 46 `round-table-state-schema.yaml` | required fields + `retained_python_phases` field (NEW, this doc adds) | §5.3 |
| ARCHITECTURE §1.1 | 18-field schema source table | §2.0, §3.5, §6.1 row 5 |
| ARCHITECTURE §1.2 | SKILL→YAML disposition (9 copy / 2 drop / 1 rewrite / 1 flatten / 1 derive / 8 new) | §1.2, §2.0, §2.18, §3.1 |
| ARCHITECTURE §2 | 15-expert table (verbatim source for §2 75-cell elaboration — FOUND-08 preserved) | §1.6, §2.0, §2.2-§2.16, §2.18 |
| ARCHITECTURE §6.1 | Transform procedure 5 steps (read → sha256 → generate → write → record lineage) | §2.1, §2.18 |
| ARCHITECTURE §6.4 | Repo impact summary (Phase 49 v11.0 PoC deliverable = 15 `*.agent.yaml`) | §1.4, §3.4 |
| STACK §3.2 Tool 7 | `run_python_phase` signature + `openWorldHint=True` | §5.1, §5.4 |
| STACK §11.2 line 1120 | OQ-10 resolution (allowlist location = round-table-schema.yaml) | §5.3 |
| PITFALLS §P14 | 3 mitigations (`schema_version` + safe-default + dry-run) | §4.0, §4.4-§4.6, §4.9 |
| SUMMARY OQ-3 + OQ-10 | Two open questions this doc resolves | §5.0, §5.5, §5.6, §6.3 |

**NET-NEW (this doc's contribution):**

1. **75-cell per-expert edge cases** (§2.2-§2.16 + §2.19) — ARCHITECTURE §2 gives the 5-field skeleton; this doc elaborates each of 15 experts × 5 fields with `default + edge case` granularity. Per §1.2, the 5-field framework itself is CITE-ONLY.
2. **`default_invocation` failure-mode matrix** (§3.2) — 3 failure modes × 4 transition states = 12-cell matrix. ARCHITECTURE §1.1 field 18 gives the enum; this doc gives dispatcher semantics.
3. **v6.0 FeedbackStore → memory-record-schema migration plan** (§4) — agent/feedback_store.py gives the source schema; Phase 45 memory-record-schema.yaml gives the target; this doc gives the field mapping + 6-step execution + rollback path.
4. **`retained_python_phases` allowlist value** (§5.2-§5.3) — STACK §3.2 Tool 7 gives the signature; §11.2 gives the location; this doc gives the 7 step values (Steps 0/6.5/7/10/11/12/15) + per-step rationale.
5. **Legacy `agent_id=hermes` sunset policy** (§5.5-§5.6) — SUMMARY OQ-3 gives the leaning; this doc gives the 30-day sunset window + read-only fallback rules.

### 0.4 Stability Discipline

Re-deriving any LOCKED-CITE source in this doc is a **scope violation**. If a contradiction surfaces (e.g. ARCHITECTURE §2 row for `cinematographer` lists 7 refs but §2.7 of this doc counts 6), this doc is wrong — fix this doc, not the source. The single exception: ARCHITECTURE §1.2 dispositions are a *skeleton* — §2 *elaborates* that skeleton to 75-cell granularity, which is the doc's mandate per ROADMAP SC#2.

---

## §1 Framing + Scope + SC Mapping

### §1.1 Framing — 本文是 决策 2/5/6 + ARCHITECTURE §1.2/§2 的迁移路径落实

本文档定义 Phase 44 **决策 2** (B3a Python runner 增量迁移 — delegate-only phase 通过 `run_python_phase` boundary tool 迁移到 CC) + **决策 5** (α agent form: YAML + persona + tools + refs + memory_scope + lineage) + **决策 6** (per-agent memory + curator-driven 自进化) 的**可执行迁移路径**。

具体而言,本 doc 把:

- ARCHITECTURE §1.2 已有的 SKILL→YAML 5-field mapping 骨架 (9 copy / 2 drop / 1 rewrite / 1 flatten / 1 derive / 8 new)
- ARCHITECTURE §2 已有的 15-expert 表 (per-expert deltas for tools / persona / refs / related_agents)

**细化到 75-cell (15 expert × 5 field) 可执行粒度** —— 当 v11.0 PoC 实施者问 "screenplay 的 transform 规则是什么? edge case 有哪些?", §2 直接回答. 同时本 doc **锁定 4 件套 net-new 贡献**:

1. **(a) Memory schema 迁移计划** (§4) — v6.0 FeedbackStore JSONL → Phase 45 memory-record-schema, 含 `schema_version` + dry-run mode per PITFALLS §P14 mitigation 3 (防止 P14 silent drops / unsafe defaults)
2. **(b) Retained-phases allowlist** (§5) — `run_python_phase` 仅接受 Steps 0/6.5/7/10/11/12/15, location = `round-table-state-schema.yaml` `retained_python_phases` field per STACK §11.2 (resolves OQ-10)
3. **(c) `default_invocation: skill_fallback → mcp_tool` 切换机制** (§3) — agent 优先 MCP tool, 失败回退 SKILL form, 保留 FOUND-08 backward-compat anchor
4. **(d) 旧 v7.0 mem0 `agent_id=hermes` memory 遗留策略** (§5.5-§5.6) — 遗留/不迁移 + 30-day sunset window + read-only fallback (resolves OQ-3)

**Phase 44 决策引用:**

- **决策 1** (T6 协议: Hermes MCP server + tmux dispatch + CC native MCP client, §2.1) — sets Hermes as runtime owner of MCP tool surface. `run_python_phase` is one of 7 Hermes-side MCP tools (§3 + §5.4 dispatch on this layer).
- **决策 2** (B3a Python runner 增量迁移, §2.2) — **LOAD-BEARING root for SC#5**. Delegate-only phases migrate to CC via `run_python_phase` boundary tool. §5 retained-phases allowlist is the direct fulfillment of 决策 2.
- **决策 5** (α agent form, §2.5) — transform target schema. §2 75-cell transform is the per-expert instantiation of α form.
- **决策 6** (per-agent memory + curator-driven 自进化, §2.6) — **LOAD-BEARING root for SC#4**. §4 memory migration is the source→target path; §5.5-§5.6 legacy policy handles v7.0 mem0 transition.
- **决策 7** (分层 CC 角色: Hermes 控结构, CC 控内容, §2.7) — `run_python_phase` is Hermes-side boundary tool; CC invokes via MCP. §3.4 default_invocation transition is operator-owned (Hermes exposes the switch, operator flips it).

**Consumed vs NET-NEW 显式声明:**

| Category | Items | Source |
|----------|-------|--------|
| **Consumed (CITE-ONLY)** | 5-field mapping skeleton (tools/persona/refs/related_agents/lineage.skill_sha256) | ARCHITECTURE §1.2 + §2 |
| **Consumed (CITE-ONLY)** | 18-field agent YAML schema | Phase 45 `agents-schema.yaml` |
| **Consumed (CITE-ONLY)** | 10-field memory record schema + `schema_version` line 353 | Phase 45 `memory-record-schema.yaml` |
| **Consumed (CITE-ONLY)** | Round-table state schema | Phase 46 `round-table-state-schema.yaml` |
| **Consumed (CITE-ONLY)** | `run_python_phase` boundary tool signature | STACK §3.2 Tool 7 |
| **Consumed (CITE-ONLY)** | 3 P14 mitigations | PITFALLS §P14 |
| **NET-NEW** | 75-cell per-expert edge cases | §2.2-§2.16 + §2.19 |
| **NET-NEW** | `default_invocation` 12-cell failure-mode matrix + transition path | §3.2 + §3.4 |
| **NET-NEW** | v6.0 FeedbackStore → memory-record-schema migration plan | §4.3-§4.8 |
| **NET-NEW** | `retained_python_phases` allowlist value (Steps 0/6.5/7/10/11/12/15) | §5.2-§5.3 |
| **NET-NEW** | Legacy `agent_id=hermes` 30-day sunset policy | §5.5-§5.6 |

### §1.2 Scope Rules — CITE-ONLY 策略 + 4 项 OUT-OF-SCOPE

本 doc **细化** ARCHITECTURE §1.2 + §2 已有 mapping 到 75-cell 可执行粒度, **不重定义** 5-field mapping 框架本身.

**CITE-ONLY 策略 (不重定义):**

引用 Phase 44 决策 1-7 + Phase 45 `agents-schema.yaml` 18 fields + `memory-record-schema.yaml` 10 fields + Phase 46 `round-table-state-schema.yaml` + ARCHITECTURE §1/§2/§6 + STACK §3.2 + PITFALLS §P14 时, **一律 cite by 决策号/字段名/section号**, 不在本文重述字段定义或重新推导决策论据. 任何字段细节去 source 文档查; 本 doc 仅给出 "source 字段 → target 字段 + default + edge case" 的迁移语义.

**4 项 OUT-OF-SCOPE (本 doc 不讨论):**

1. **(a) Agent YAML schema 字段定义本身** — 留给 Phase 45 `agents-schema.yaml`. 本 doc 引用 `default_invocation` enum 时不重述 enum 值; 引用 `lineage.skill_sha256` 时不重述 sub-fields.
2. **(b) Round table protocol 字段细节** — 留给 Phase 46 (`02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml`). 本 doc 引用 `retained_python_phases` field 时仅声明它在本 doc 中新增, 不重述 round-table state schema 其他字段.
3. **(c) Live transform CLI 实现** — deferred to v12+ `hermes agent transform` CLI. 本 doc §2 75-cell 是 v11.0 PoC **manual transform** 的规则; CLI 自动化是 v12+ 的事.
4. **(d) mem0 backend 部署拓扑** (Option B 单 backend vs 物理分区) — 留给 Phase 48 `06-CROSS-REPO-IMPACT.md`. 本 doc §4 memory migration 假设 Option B (单 mem0 backend + `agent_id` filter); 物理分区触发条件不在本 doc scope.

### §1.3 ROADMAP SC#1-5 Mapping Table

| SC# | 描述 (ROADMAP §Phase 49) | 本 doc 解决章节 | 验证脚本 (Phase 51 VALIDATE lint) |
|-----|--------------------------|-----------------|-----------------------------------|
| **SC#1** | File `04-MIGRATION-PATH.md` exists at `.planning/research/v10-orchestrator-design/` | (entire doc) | `test -f .../04-MIGRATION-PATH.md && wc -l >= 1300` |
| **SC#2** | 15 expert × 5-field transform 规则表完整 (75 cells, FOUND-08 preserved) | §2.0-§2.19 | count `^### §2\.` >= 18 + each of 15 expert_ids appears in own section + `grep FOUND-08` >= 3 |
| **SC#3** | `default_invocation: skill_fallback → mcp_tool` 切换机制文档化 (failure modes + transition + safe-default) | §3.0-§3.7 | `grep default_invocation` + `grep "12-cell"` + check failure-mode matrix presence |
| **SC#4** | Memory schema 迁移计划 (v6.0 FeedbackStore → memory-record-schema, 含 `schema_version` + dry-run per P14) | §4.0-§4.9 | `grep FeedbackStore` + `grep "schema_version"` + `grep "dry-run"` + `grep "P14 RESOLVED"` |
| **SC#5** | Retained-phases allowlist (Steps 0/6.5/7/10/11/12/15) + legacy `agent_id=hermes` policy | §5.0-§5.6 | `grep run_python_phase` + each of 7 step values appears + `grep agent_id=hermes` + `grep sunset` |

### §1.4 Roadmap Placement — Phase 49 在 v10.0 设计图里的位置

**上游依赖 (consumed):**

- Phase 44 决策 1-7 (`00-FIRST-PRINCIPLES.md §2.1-§2.7`) — 7 locked root arguments
- Phase 45 schemas (`agents-schema.yaml` 18 fields + `memory-record-schema.yaml` 10 fields) — field-level citation source
- Phase 46 protocol (`round-table-state-schema.yaml`) — allowlist location
- ARCHITECTURE §1.1 + §1.2 + §2 + §6 — 5-field mapping skeleton + 15-expert table + transform procedure + repo impact
- STACK §3.2 Tool 7 + §11.2 — `run_python_phase` signature + allowlist location resolution
- PITFALLS §P14 — 3 migration mitigations

**下游 consumer (produces for):**

- **`05-POC-PLAN.md`** (Phase 49's immediate successor) — consumes §2 75-cell transform table (PoC 实施 15 `*.agent.yaml` must follow this) + §3.4 transition path (per-agent switch sequence) + §4.5 dry-run (PoC acceptance: dry-run must run clean) + §4.7 migration 6 steps (PoC week-1 work) + §5.2 retained-phases 7 steps (PoC `run_python_phase` test scope)
- **Phase 50 POC-PLAN** — consumes §5.2 retained-phases 7 steps (PoC `run_python_phase` test scope) + §4.9 P14 PoC acceptance (<1% shadow discrepancy) + §3.6 compliance_gate/theory_critic special handling (PoC switch order)
- **51 VALIDATE lint** — consumes §6.1 7 决策 audit table + §6.3 OQ-3/OQ-10/P14 resolution declarations + §2.18 FOUND-08 invariant + §5.3 `retained_python_phases` schema field. VALIDATE cross-doc lint will cross-check this doc's 15-expert transform 规则 against ARCHITECTURE §2 (consistency) + check all `decision 决策 N` citations resolve.

**LOCKED declarations:**

Phase 44 决策 1-7 LOCKED · Phase 45 schemas LOCKED · Phase 46 protocol LOCKED · ARCHITECTURE §1.2 + §2 mapping skeleton LOCKED — **this doc only elaborates + adds 4 net-new pieces**. If v11.0 PoC 实施中发现 any locked source needs revision, that's a Phase 51 audit finding, NOT a Phase 49 doc edit.

### §1.5 Four Deliverables Declared Upfront

This doc provides **four load-bearing deliverables** beyond the cited sources:

#### §1.5.1 15-Expert × 5-Field Transform 规则表 (§2)

- **CITEs:** ARCHITECTURE §1.1 18-field schema + §1.2 dispositions (9 copy / 2 drop / 1 rewrite / 1 flatten / 1 derive / 8 new) + §2 15-expert table verbatim.
- **NET-NEW contribution:** Each of 15 experts × 5 fields (tools / persona / refs / related_agents / lineage.skill_sha256) elaborated to `default + edge case` granularity. Per-cell edge case is new (ARCHITECTURE §2 gives only the default value per expert). Lineage derivation (sha256 computation + LF normalization edge case) is made explicit.
- **PoC consumer:** v11.0 PoC manual transform uses §2.2-§2.16 as the rule table — when implementer asks "screenplay 的 tools 字段填什么?", §2.4 answers with default `[hermes_llm, read_file, search_files, write_file, patch]` + edge case "write_file/patch for script revision per HOOK-09 contract".

#### §1.5.2 `default_invocation: skill_fallback → mcp_tool` 切换机制 (§3)

- **CITEs:** ARCHITECTURE §1.1 field 18 (`default_invocation` enum) + §1.2 SKILL body disposition ("NOT copied. Becomes input to persona rewrite. Original SKILL body preserved in source repo as lineage.derived_from_skill_id reference.")
- **NET-NEW contribution:** 12-cell failure-mode matrix (3 failure modes × 4 transition states) + safe-default-on-unknown rules (missing field → `mcp_tool`; missing agent sibling → `skill_fallback`) + per-agent transition path (5 steps: transform → disabled → verify → mcp_tool → round_table_eligible).
- **FOUND-08 backward-compat preserved via `expert_id` anchor** (§3.5).

#### §1.5.3 Memory Schema 迁移计划 (§4)

- **CITEs:** agent/feedback_store.py (v6.0 source schema ground truth) + Phase 45 memory-record-schema.yaml (target schema, 10 mandated fields) + PITFALLS §P14 (3 mitigations).
- **NET-NEW contribution:** 17-row source→target field mapping table + `schema_version` forward-compat semantics (cite line 353) + dry-run migration mode (`hermes agent memory migrate --dry-run`, 5-metric output plan) + safe-default-on-unknown-field table (6 rules per P14 mitigation 2) + 6-step migration execution (backup → dry-run → approval → live → shadow 30d → decommission) + rollback path + P14 RESOLVED declaration.
- **PoC acceptance (§4.9):** dry-run migration must run clean + 30-day shadow-run window must show <1% retrieval discrepancy before source decommission.

#### §1.5.4 Retained-Phases Allowlist + Legacy mem0 Policy (§5)

- **CITEs:** STACK §3.2 Tool 7 (`run_python_phase` signature) + §11.2 (allowlist location resolution) + SUMMARY OQ-3 + OQ-10 + ARCHITECTURE §3.1 (current mem0 surface).
- **NET-NEW contribution:** 7-step retained-phases allowlist (Steps 0/6.5/7/10/11/12/15) with per-step rationale + `retained_python_phases` schema field (NEW in round-table-state-schema.yaml, this doc adds it) + dispatcher enforcement mechanism (no silent fallback) + legacy `agent_id=hermes` 遗留/不迁移 policy + 30-day sunset window (operator-extendable via config).

### §1.6 15-Expert Quick-Glance Table (ARCHITECTURE §2 Verbatim — FOUND-08 Preserved)

The following table is **copied verbatim from ARCHITECTURE §2** (lines 128-144). All 15 `expert_id` values are unchanged — FOUND-08 preserved. §2 full deep-dive adds `default + edge case` per cell.

| Expert | `tools` | `persona` framing | Notable `refs` (count) | `related_agents` (count) |
|--------|---------|-------------------|------------------------|--------------------------|
| **hook_retention** | `[hermes_llm, read_file, search_files]` | First-person commercial留存引擎; cites 5 hook types + 5 爆款公式; defers to screenplay on dialogue | 4 refs (three-second-hooks, conflict-escalation, paywall-design, viral-formulas) | 5 |
| **creative_source** | `[hermes_llm, read_file, search_files]` | First-person creative ideation; cites Snowflake Method 10-step + SCAMPER 7-verb; outputs StoryKernel JSON scaffold | 3 refs (snowflake-method, scamper-variations, project-corpus) | 4 |
| **screenplay** | `[hermes_llm, read_file, search_files, write_file, patch]` | First-person scene architect; cites Snyder 15-beat + McKee value-shift + Tan interest formula; HOOK-09 marker contract is load-bearing | 5 refs (save-the-cat, mckee, cn-shortdrama, emotion-curve, dialogue-craft) | 9 |
| **script_auditor** | `[hermes_llm, read_file, search_files]` | First-person 5-dim critic (NOT creative writer); predicts completion %, flags exposition dumps; hard-gates on `< 65% predicted_completion` | 5 refs (5-dim audit) | 4 |
| **character_designer** | `[hermes_llm, read_file, search_files, write_file]` | First-person character psychologist; produces L1-L4 asset library specs; defers to visual_executor on turnaround sheets | 4 refs | 5 |
| **cinematographer** | `[hermes_llm, read_file, search_files]` | First-person shot-intent owner; cites Mascelli 8-level + 180°/30° axis + 9:16 power points + 12 camera moves; does NOT execute motion (visual_executor's job); Phase 17 absorbed scene_builder | 7 refs (shot-grammar, axis-rules, vertical-screen-framing, camera-motion-catalog, e-konte-format, duration-decision-framework, ltx-video-workflows cross-ref) | 9 |
| **style_genome** | `[hermes_llm, read_file, search_files]` | First-person 5D style vector architect; cites SCAMPER for style_blend variants; Cross-Module Alignment metric | 3 refs | 8 |
| **prompt_injector** | `[hermes_llm, read_file, search_files, write_file]` | First-person bilingual prompt translator (camera-move intent → dreamina/Runway/Kling/Veo/Sora prompt tokens); NEW AI-native (no SKILL precedent pre-v3.0) | 2 refs | 5 |
| **visual_executor** | `[hermes_llm, dreamina_cli, read_file, write_file, patch]` | First-person dreamina CLI executor (text2image / image2image / multimodal2video); sub_steps: [drawer, animator]; does NOT decide intent | 2 refs (dreamina-cli-baseline, scene-multi-angle-references) | 6 |
| **continuity_auditor** | `[hermes_llm, read_file, search_files]` | First-person 4-dim continuity critic (face_identity / wardrobe_figure / color_temperature / scene_environment) + axis compliance; hard-gate on 4-dim fail | 3 refs | 5 |
| **audio_pipeline** | `[hermes_llm, dreamina_cli (TTS path), read_file, write_file]` | First-person audio master; sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]; 6 sub-step atomic operation per V8.6 §6 | 6 refs (one per sub-step) | 4 |
| **editor** | `[hermes_llm, read_file, search_files]` | First-person rhythm + axis compliance owner; cut_density metric; defers to cinematographer on intent | 3 refs | 5 |
| **colorist** | `[hermes_llm, read_file, search_files, write_file]` | First-person CxSxZ color narrative + LUT plan; integrates with visual_executor at Step 7 | 2 refs | 4 |
| **compliance_gate** | `[hermes_llm, read_file, search_files]` | First-person red-line gate (redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending per v9.0); **hard-gate authority** — can block pipeline progression | 5 refs | 4 |
| **theory_critic** | `[hermes_llm, read_file, search_files]` | First-person artistic critic; **soft-gate only** (advisory); cites McKee + Tan + classical film theory | 4 refs | 6 |

**Aggregate (per ARCHITECTURE §2 closing):** 15 agents, 9 common copy-fields, 4 new fields per agent, 1 body-rewrite per agent, average 3.5 refs per agent, average 5.6 related_agents per agent.

**FOUND-08 preservation rule (ARCHITECTURE §2 verbatim):** All 15 `expert_id` values are copied verbatim. The transition is **additive** — consumers can still call skills by `expert_id` and the dispatcher falls through to SKILL when `default_invocation: skill_fallback` is set.

### §1.7 Explicit OUT-OF-SCOPE Declaration

This doc does NOT cover (per §1.2 scope rules):

- **(a) Agent YAML schema 字段定义本身** — Phase 45 `agents-schema.yaml` authoritative. This doc cites field names (`default_invocation`, `lineage.skill_sha256`, `memory_scope`, etc.) without redefining.
- **(b) Round table protocol 字段细节** — Phase 46 (`02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml`) authoritative. This doc only adds the `retained_python_phases` field.
- **(c) Live transform CLI 实现** — deferred to v12+ `hermes agent transform` CLI. §2 75-cell is the v11.0 PoC **manual transform** rule table; CLI automation is v12+.
- **(d) mem0 backend 部署拓扑** — Phase 48 `06-CROSS-REPO-IMPACT.md` Option B vs 物理分区. This doc §4 assumes Option B (单 mem0 backend + `agent_id` filter).
- **(e) Live `run_python_phase` execution** — v11.0 PoC deferred. This doc §5 specifies the allowlist + enforcement mechanism; live execution semantics are PoC scope.
- **(f) A2A protocol** — post-v12+. Round table is MCP-only (per Phase 44 决策 1 T6 协议 layer); A2A cross-platform interop is later milestone.

---

## §2 — 15-Expert × 5-Field Transform 规则表 (SC#2 75-Cell Deep-Dive)

### §2.0 Selection Rationale — 为什么 5 fields × 15 experts = 75 cells?

本节是 **ROADMAP SC#2 的完整论证**. ARCHITECTURE §1.2 已给 SKILL→YAML 5-field mapping 通则 (9 copy / 2 drop / 1 rewrite / 1 flatten / 1 derive / 8 new) + §2 已给 15-expert 表 (per-expert deltas for tools / persona / refs / related_agents). 本节把这两张表**合并 + 细化到 75-cell (15 expert × 5 field) 可执行粒度** —— 当 v11.0 PoC 实施者问 "screenplay 的 transform 规则是什么? edge case 有哪些?", 本节回答.

**5 fields 选择 (从 18-field schema 中筛出):**

| Field | ARCHITECTURE §1.2 disposition class | Why per-expert rule needed? |
|-------|-------------------------------------|------------------------------|
| **(1) `tools`** | DERIVE (from SKILL `prerequisites.tools` + agent actual surface) | 15 experts have 4 distinct tool patterns (analysis-only / dreamina / write_file / write+patch); can't be a single default |
| **(2) `persona`** | REWRITE (from SKILL body markdown) | 15 experts have 15 distinct first-person framings; SKILL body imperative-second-person → persona first-person requires per-expert rewriting |
| **(3) `refs`** | FLATTEN (from SKILL `## References` table) | 15 experts have refs count ranging 2-7; per-expert list with notable anchors needed |
| **(4) `related_agents`** | COPY-with-rename (from `metadata.hermes.related_skills` → `related_agents`) | 15 experts have related-count 4-9; per-expert DAG differs (screenplay has 9 peers per v86-pipeline-mapping.md; theory_critic has 6) |
| **(5) `lineage.skill_sha256`** | NEW (computed at transform time) | Per-expert `transform_notes` differ — e.g. screenplay's HOOK-09 contract is load-bearing and must surface |

**其他 9 fields 是简单 COPY 或统一 default, 无需 per-expert 规则:**

| Field | Default (no per-expert variation) |
|-------|-----------------------------------|
| `name` | Copy from SKILL `name` (must match filename stem) |
| `description` | Copy verbatim from SKILL `description`, refine if needed |
| `version` | Bumped to `1.0.0` on first transform |
| `platforms` | Copy verbatim (default `[linux, macos, windows]`) |
| `tags` | Copy verbatim from `metadata.hermes.tags` |
| `expert_id` | Copy verbatim from `metadata.hermes.expert_id` (FOUND-08 preserved) |
| `metrics` | Copy verbatim from `metadata.hermes.metrics` |
| `prerequisites` | Copy verbatim from SKILL `prerequisites` (different from runtime `tools`) |
| `memory_scope` | Default `per_agent` for all 15 movie-experts (uniform) |
| `default_invocation` | Default `mcp_tool` for 13/15; `disabled` initially for `compliance_gate` (special handling per §3.6) |
| `evolution_log` | Init `[]` for all 15 (curator-managed) |
| `fitness_score` | Init `null` for all 15 (curator-managed) |
| `round_table_eligible` | Default `true` for all 15 (set `false` only for ephemeral helpers; none of the 15 are ephemeral) |

### §2.1 5-Field Mapping 通则 (Default Rule + Edge Case Pattern Template)

The following table gives the **default rule + edge case pattern template** that §2.2-§2.16 instantiate per-expert.

| Field | Default rule (applies to all 15) | Edge case pattern (per-expert override criteria) |
|-------|----------------------------------|--------------------------------------------------|
| **tools** | `[hermes_llm, read_file, search_files]` + expert-specific write/exec tools per ARCHITECTURE §2 row | If SKILL `prerequisites.tools` lists `dreamina_cli` or `comfyui`, include in agent tools; else analysis-only. If SKILL body emits structured artifacts (e.g. StoryKernel JSON), add `write_file`. If SKILL body patches existing files (e.g. screenplay script revision), add `patch`. |
| **persona** | First-person expert identity; cite 1-2 anchor refs by name; defer to peers on their domains; NEVER generate full output unprompted (contribute slice when orchestrator asks) | If SKILL body has load-bearing marker contract (e.g. screenplay HOOK-09 emotion_curve arrays, hook_retention 3-second contract), surface in persona + record in `lineage.transform_notes`. If SKILL absorbed a prior skill (e.g. cinematographer absorbed scene_builder Phase 17), surface in persona framing. |
| **refs** | SKILL `## References` table → repo-relative path list. Default 2-7 refs per expert. | If SKILL has 0 refs (rare), agent is persona-only. If >7 refs (cinematographer 7), dedupe by topic or mark as "extension refs" with retrieval priority. If cross-module refs (style_genome, prompt_injector), cite the cross-module anchor explicitly. |
| **related_agents** | SKILL `metadata.hermes.related_skills` → `related_agents` verbatim (COPY-with-rename). Default 4-9 agents per expert. | If SKILL has 0 `related_skills`, agent is solo (no round table peers — rare). If SKILL references deprecated name, map via FOUND-08 (e.g. pre-v3.0 `scene_builder` → `cinematographer`). If DAG includes hard-gate agent (`compliance_gate`), keep it in `related_agents` even though invocation is via MCP not direct call. |
| **lineage.skill_sha256** | `hashlib.sha256(source_skill_md_content.encode("utf-8")).hexdigest()` (encoding explicit per CLAUDE.md PLW1514 — Ruff will block merge without it) | If source SKILL.md has CRLF line endings (Windows checkout), normalize to LF before hashing AND document normalization in `transform_notes`. If source SKILL.md has BOM, strip before hashing. If SKILL undergoes v5.0 V8.6 sync patch mid-transform, recompute hash + bump `transform_date`. |

### §2.2 `hook_retention` — Commercial 留存引擎

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None — hook_retention is advisory, no write/exec tools. Differs from screenplay (which adds `write_file, patch`). |
| `persona` | First-person commercial 留存引擎. Cites 5 hook types (cold-open / mystery-box / conflict-front / curiosity-gap / shock-frame) + 5 爆款公式 (3-second rule / 7-second rule / paywall-design / viral-formulas / conflict-escalation). Defers to screenplay on dialogue subtext, to cinematographer on shot intent. | **Contract-load-bearing:** 3-second hook contract must surface in persona as first-class content (not buried in refs). Persona should explicitly invoke "3 秒原则" + cite the 5 hook types by name. |
| `refs` | 4 refs: `three-second-hooks.md`, `conflict-escalation.md`, `paywall-design.md`, `viral-formulas.md` | None — all 4 refs are core to persona. No dedup needed. |
| `related_agents` | 5 agents: `screenplay`, `creative_source`, `cinematographer`, `editor`, `theory_critic` | None — DAG is standard advisory ring. |
| `lineage.skill_sha256` | SHA256 of `kais-hermes-skills/skills/movie-experts/hook_retention/SKILL.md` content (UTF-8 / LF-normalized) | `transform_notes`: "5 hook types + 5 爆款公式 enumerated in persona verbatim per SKILL body — contract-load-bearing". |

**Expert-specific edge case:** hook_retention is the **only** expert where persona content must enumerate specific commercial formulas (5×5 = 25 hooks) verbatim. Other experts cite refs by name; hook_retention inlines the formulas because they are the entire value-add.

**Persona excerpt (first-person, bilingual):**
```
我是 Hook & Retention Expert (商业留存引擎). 我负责短剧 0-3 秒的 hook 设计
与全片 retention curve. 我精通 5 类 hook (cold-open / mystery-box / conflict-front /
curiosity-gap / shock-frame) 与 5 条 爆款公式 (3-second rule / 7-second rule /
paywall-design / viral-formulas / conflict-escalation). 我不会替 screenplay 写台词,
也不会替 cinematographer 设计镜头 — 我只在编排者问我"这片子开头如何 hook 观众?"
时贡献我的切片.
```

### §2.3 `creative_source` — Creative Ideation + StoryKernel Scaffold

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files, write_file]` | **+`write_file`** vs default analysis-only. Rationale: outputs StoryKernel JSON scaffold — `write_file` needed to persist artifact to `~/.hermes/projects/<slug>/story_kernel.json`. |
| `persona` | First-person creative ideation engine. Cites Snowflake Method 10-step + SCAMPER 7-verb + project-corpus. Outputs StoryKernel JSON scaffold (per `.planning/research/methodology-gap-analysis.md` gap #1 — Snowflake/SCAMPER were unfilled pre-v10.0). Defers to screenplay on dialogue, to style_genome on visual DNA. | **Edge case:** persona must declare output format (StoryKernel JSON) explicitly so dispatcher knows `write_file` is load-bearing, not optional. |
| `refs` | 3 refs: `snowflake-method.md`, `scamper-variations.md`, `project-corpus.md` | None — 3 refs is lean. |
| `related_agents` | 4 agents: `screenplay`, `style_genome`, `character_designer`, `theory_critic` | None — DAG is small (creative_source is upstream of all narrative experts). |
| `lineage.skill_sha256` | SHA256 of `creative_source/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "StoryKernel JSON output format declared in persona — `write_file` tool load-bearing for scaffold persistence". |

**Expert-specific edge case:** creative_source is **newly added in v10.0** (filled the gap methodology-gap-analysis identified). Persona must surface "Snowflake Method 10-step + SCAMPER 7-verb" as the creative engine — not just cite refs.

**Persona excerpt:**
```
I am the Creative Source Expert (创意源头架构师). I generate the seed of every
project via Snowflake Method 10-step (one-line → one-paragraph → character
synopses → ...) cross-pollinated with SCAMPER 7-verb operators (Substitute /
Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse). My output
is a StoryKernel JSON scaffold (logline + kernel + character_seeds + theme)
consumed by screenplay, character_designer, and style_genome. I defer on
dialogue to screenplay, on visual DNA to style_genome.
```

### §2.4 `screenplay` — Scene Architect + HOOK-09 Contract

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files, write_file, patch]` | **+`write_file, patch`** vs default. Rationale: screenplay writes the initial script (`write_file`) AND revises it based on script_auditor feedback (`patch`). |
| `persona` | First-person scene architect. Cites Snyder 15-beat + McKee value-shift + Tan interest formula + cn-shortdrama-structure + emotion-curve-academic. HOOK-09 emotion_curve marker contract is **load-bearing** (must surface). Defers to hook_retention on 3-second hooks, to cinematographer on shot intent. | **HOOK-09 contract:** Persona must explicitly mention `emotion_curve marker arrays remain contract-load-bearing` — these arrays drive downstream hook_retention analysis + script_auditor 5-dim audit. Losing this in transform breaks the v9.0→v10.0 pipeline. |
| `refs` | 5 refs: `save-the-cat-beat-sheet.md`, `mckee-scene-design.md`, `cn-shortdrama-structure.md`, `emotion-curve-academic.md`, `dialogue-craft.md` | None — 5 refs is core. |
| `related_agents` | **9 agents** (highest among 15): `style_genome`, `editor`, `audio_pipeline`, `compliance_gate`, `hook_retention`, `cinematographer`, `theory_critic`, `creative_source`, `script_auditor` | None — 9-agent DAG per v86-pipeline-mapping.md reflects screenplay's central narrative role. |
| `lineage.skill_sha256` | SHA256 of `screenplay/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "Persona rewritten from SKILL body; SKILL preserved as fallback. HOOK-09 emotion_curve marker arrays remain contract-load-bearing — do NOT lose in transform." |

**Expert-specific edge case:** screenplay is the **only** expert with explicit `transform_notes` warning about contract preservation. The HOOK-09 emotion_curve arrays are downstream-consumed by hook_retention (for hook-vs-emotion alignment) and script_auditor (for emotional_arc dimension).

**Persona excerpt:**
```
You are the Screenplay Expert in a Hermes round table. You speak in first
person about scene structure, Snyder 15-beat adaptation, anchor-based
emotion curves, and dialogue subtext. You cite save-the-cat-beat-sheet,
mckee-scene-design, cn-shortdrama-structure, emotion-curve-academic,
and dialogue-craft from your refs when justifying a recommendation.
You defer to hook_retention on 3-second hooks and to cinematographer on
shot intent. You never generate full scripts unprompted — you contribute
your slice when the orchestrator asks. HOOK-09 emotion_curve marker arrays
remain contract-load-bearing.
```
*(Cited verbatim from ARCHITECTURE §1.3 screenplay minimal example.)*

### §2.5 `script_auditor` — 5-Dimension Critic (NOT Creative Writer)

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None — script_auditor reads screenplay outputs but never writes. Differs from screenplay's `write_file, patch`. |
| `persona` | First-person 5-dim critic. Cites 5-dim audit framework (narrative_tension / dialogue_naturalness / pacing / emotional_arc / hook_strength). Predicts completion %, flags exposition dumps. Hard-gates on `< 65% predicted_completion`. **Critical framing: NOT a creative writer — advisory + gate, never rewrites.** | **Framing contract:** Persona must explicitly say "I am NOT a creative writer; I critique, I do not generate." This prevents the model from drifting into rewriting screenplay's work (which would create circular feedback). |
| `refs` | 5 refs (5-dim audit framework docs) | None. |
| `related_agents` | 4 agents: `screenplay`, `theory_critic`, `continuity_auditor`, `compliance_gate` | None — DAG is the audit ring. |
| `lineage.skill_sha256` | SHA256 of `script_auditor/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "Critical-not-generative framing explicit in persona — prevents model drift to creative rewriting." |

**Expert-specific edge case:** script_auditor's persona must establish the **critic-not-writer** framing as a first-class invariant. Without it, the model tends to suggest rewrites (which is screenplay's job), creating role confusion.

**Persona excerpt:**
```
我是 Script Auditor (剧本审计员). 我用 5 维框架 (narrative_tension /
dialogue_naturalness / pacing / emotional_arc / hook_strength) 评估剧本.
我预测 completion %, 标记 exposition dump. 当 predicted_completion < 65%
我 hard-gate 拒绝. 我不是 creative writer — 我不重写剧本, 我只 critique.
我的 4 位同事是 screenplay (被审计方), theory_critic (软评估搭档),
continuity_auditor (4-dim 连续性审计), compliance_gate (合规 hard-gate).
```

### §2.6 `character_designer` — Character Psychologist + L1-L4 Asset Specs

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files, write_file]` | **+`write_file`** vs default. Rationale: produces L1-L4 asset library specs (JSON / YAML) that downstream visual_executor consumes. |
| `persona` | First-person character psychologist. Produces L1 (backstory) / L2 (psychology) / L3 (visual spec) / L4 (turnaround sheet) asset library specs. Defers to visual_executor on actual visual rendering. | **L4 handoff contract:** Persona must declare "L4 turnaround sheets are consumed by visual_executor" so dispatcher knows cross-agent data flow. |
| `refs` | 4 refs (character psych + L1-L4 spec framework) | None. |
| `related_agents` | 5 agents: `screenplay`, `creative_source`, `visual_executor`, `style_genome`, `continuity_auditor` | None. |
| `lineage.skill_sha256` | SHA256 of `character_designer/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "L4 turnaround sheet handoff to visual_executor declared in persona — `write_file` load-bearing". |

**Expert-specific edge case:** character_designer is the **only** expert where `write_file` is justified by structured handoff to another agent (visual_executor). screenplay also has `write_file` but for script artifact; character_designer for L1-L4 JSON.

**Persona excerpt:**
```
I am the Character Designer Expert (角色设计师). I produce the L1-L4 asset
library for every character: L1 backstory, L2 psychology profile, L3 visual
spec (silhouette / color palette / material), L4 turnaround sheet (8-view
reference for visual_executor). I defer to screenplay on dialogue, to
style_genome on visual DNA. L4 turnaround sheets are consumed by
visual_executor — I produce them as JSON, not rendered images.
```

### §2.7 `cinematographer` — Shot-Intent Owner (Phase 17 Absorbed scene_builder)

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | **Important:** does NOT execute motion (that's visual_executor's job). `tools` stays analysis-only even though cinematographer designs shots — intent vs execution split. |
| `persona` | First-person shot-intent owner. Cites Mascelli 8-level + 180°/30° axis rule + 9:16 power points + 12 camera moves + e-konte-format + duration-decision-framework + ltx-video-workflows. **Phase 17 absorbed `scene_builder`** — persona must surface this absorbed domain explicitly so consumers know cinematographer owns scene composition (not a separate scene_builder). | **Absorption contract:** Persona must declare "I absorbed scene_builder per Phase 17 — scene composition is mine, not a separate expert." Without this, consumers may look for non-existent `scene_builder` agent. |
| `refs` | **7 refs** (highest among 15): `shot-grammar.md`, `axis-rules.md`, `vertical-screen-framing.md`, `camera-motion-catalog.md`, `e-konte-format.md`, `duration-decision-framework.md`, `ltx-video-workflows.md` (cross-ref) | **7 refs edge case:** mark `ltx-video-workflows.md` as "extension ref — retrieve when prompt_injector or visual_executor needs LTX context". |
| `related_agents` | **9 agents** (tied with screenplay for highest): `screenplay`, `character_designer`, `visual_executor`, `continuity_auditor`, `editor`, `prompt_injector`, `style_genome`, `theory_critic`, `compliance_gate` | None — 9-agent DAG reflects cinematographer's central role in visual pipeline. |
| `lineage.skill_sha256` | SHA256 of `cinematographer/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "Phase 17 absorbed scene_builder — persona explicitly declares ownership of scene composition. 7 refs include ltx-video-workflows cross-ref." |

**Expert-specific edge case:** cinematographer has the **highest ref count (7)** tied with the highest related_agents count (9) — it's the most cross-referenced expert. Persona must declare the scene_builder absorption explicitly to prevent consumers looking for non-existent separate agents (FOUND-08 risk: pre-v3.0 callers may still invoke `expert_id=scene_builder`; per additive invariant §2.18, this should route to cinematographer via expert_id map).

**Persona excerpt:**
```
我是 Cinematographer Expert (摄影指导). 我负责所有 shot intent — 镜头语法
(Mascelli 8-level), 轴线规则 (180°/30°), 竖屏 power points (9:16), 12 摄影机
运动, e-konte 分镜格式, 镜头时长决策框架. 我吸收了 Phase 17 的 scene_builder
— 场景调度是我的领域, 不是独立 expert. 我不执行 motion (那是 visual_executor
的工作); 我只设计 intent. 我与 9 位同事协作: screenplay (剧本), character_designer
(角色), visual_executor (执行), continuity_auditor (4-dim 连续性审计), editor
(节奏), prompt_injector (AI prompt 翻译), style_genome (5D 风格), theory_critic
(艺术评估), compliance_gate (合规).
```

### §2.8 `style_genome` — 5D Style Vector Architect

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None — style_genome outputs style vectors as data, no file writes needed (vectors live in agent's recall context). |
| `persona` | First-person 5D style vector architect. Cites SCAMPER for `style_blend` variants. **Cross-Module Alignment metric** is load-bearing (per `metadata.hermes.metrics`). | **Metric preservation:** Persona must declare "Cross-Module Alignment metric preserved" — this metric is evaluated by v6.0 eval harness and must continue working post-transform. |
| `refs` | 3 refs: `scamper-variations.md` (cross-ref from creative_source), `style-dna-framework.md`, `cross-module-alignment.md` | None. |
| `related_agents` | **8 agents**: `screenplay`, `cinematographer`, `colorist`, `editor`, `audio_pipeline`, `prompt_injector`, `character_designer`, `theory_critic` | None — 8-agent DAG reflects style_genome's cross-module role (style touches every visual/audio output). |
| `lineage.skill_sha256` | SHA256 of `style_genome/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "5D style vector + Cross-Module Alignment metric preserved — v6.0 eval harness continues to work." |

**Expert-specific edge case:** style_genome's `Cross-Module Alignment` metric is **evaluated by external harness** (v6.0 eval gate per CLAUDE.md). Transform must preserve this metric name verbatim in `metrics` field, not rename.

**Persona excerpt:**
```
I am the Style Genome Expert (风格基因组架构师). I encode every project's
visual + audio + narrative DNA as a 5D style vector (color / composition /
rhythm / texture / tone). I cite SCAMPER for style_blend variants when
blending two reference styles. Cross-Module Alignment metric is load-bearing
— my style vectors must be retrievable by every downstream expert
(cinematographer, colorist, editor, audio_pipeline, prompt_injector). I
defer to theory_critic on aesthetic judgment.
```

### §2.9 `prompt_injector` — Bilingual Prompt Translator (NEW AI-Native)

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files, write_file]` | **+`write_file`** vs default. Rationale: writes translated prompts to project artifacts (dreamina prompt JSON, Runway prompt YAML). |
| `persona` | First-person bilingual prompt translator. Translates camera-move intent (from cinematographer) → dreamina/Runway/Kling/Veo/Sora prompt tokens. **NEW AI-native expert** — no SKILL precedent pre-v3.0; lineage may have null `derived_from_skill_id` or special "AI-native" marker. | **AI-native marker:** If pre-v3.0 SKILL.md doesn't exist for prompt_injector, set `lineage.derived_from_skill_id: null` and `transform_notes: "AI-native expert — no SKILL precedent; persona authored fresh in v3.0+"`. |
| `refs` | 2 refs: `dreamina-prompt-baseline.md`, `multi-platform-prompt-syntax.md` | None — 2 refs is lean (prompt syntax is fast-moving, refs are baseline only). |
| `related_agents` | 5 agents: `cinematographer`, `visual_executor`, `style_genome`, `colorist`, `theory_critic` | None. |
| `lineage.skill_sha256` | If SKILL.md exists: SHA256 of `prompt_injector/SKILL.md`. If not (AI-native): hash of `persona` field at transform time, `derived_from_skill_id: null`. | `transform_notes`: "AI-native expert — persona may predate SKILL.md. If SKILL.md exists post-v3.0, use its sha256; else hash persona." |

**Expert-specific edge case:** prompt_injector is the **only** expert where `lineage.derived_from_skill_id` may be `null`. All other 14 experts derive from kais-hermes-skills SKILL.md. This is the AI-native exception.

**Persona excerpt:**
```
我是 Prompt Injector Expert (双语 prompt 翻译官). 我把 cinematographer 的
镜头 intent (e.g. "low-angle tracking shot, 9:16, 30° axis") 翻译成
dreamina / Runway / Kling / Veo / Sora 的 prompt token 序列. 我是 AI-native
expert — 我在 v3.0 诞生, 没有更早的 SKILL precedent. 我与 cinematographer
(intent 来源), visual_executor (执行方), style_genome (风格约束),
colorist (色彩 prompt 协同), theory_critic (美学评估) 协作.
```

### §2.10 `visual_executor` — Dreamina CLI Executor (Sub-Steps: drawer + animator)

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, dreamina_cli, read_file, write_file, patch]` | **+`dreamina_cli, write_file, patch`** vs default. Rationale: visual_executor is the **only** expert that executes dreamina CLI calls; `patch` for sub-step iteration (drawer produces sketches, animator refines them). |
| `persona` | First-person dreamina CLI executor. Sub-steps: `[drawer, animator]` (per V8.6 pipeline). Does NOT decide intent (cinematographer's job) — only executes given intent. Modes: text2image / image2image / multimodal2video. | **Intent-vs-execution split:** Persona must declare "I do NOT decide intent" explicitly to prevent role drift into cinematographer's domain. |
| `refs` | 2 refs: `dreamina-cli-baseline.md`, `scene-multi-angle-references.md` | None. |
| `related_agents` | 6 agents: `cinematographer`, `prompt_injector`, `character_designer`, `colorist`, `continuity_auditor`, `editor` | None. |
| `lineage.skill_sha256` | SHA256 of `visual_executor/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "dreamina_cli + patch in tools load-bearing — drawer→animator sub-step iteration requires patch". |

**Expert-specific edge case:** visual_executor is the **only** expert with `dreamina_cli` in tools EXCEPT audio_pipeline (which uses dreamina for TTS). Intent-vs-execution split is the load-bearing persona invariant.

**Persona excerpt:**
```
I am the Visual Executor Expert (视觉执行者). I run dreamina CLI in three
modes: text2image, image2image, multimodal2video. My sub_steps are
[drawer, animator] — drawer produces initial sketches from prompt_injector's
prompts; animator refines them with motion. I do NOT decide intent
(cinematographer's job); I only execute given intent. I patch my outputs
across sub-step iterations.
```

### §2.11 `continuity_auditor` — 4-Dim Hard-Gate Critic

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None — continuity_auditor reads visual outputs but never writes. |
| `persona` | First-person 4-dim continuity critic. 4 dimensions: `face_identity` / `wardrobe_figure` / `color_temperature` / `scene_environment`. Plus axis compliance (cross-reference cinematographer's 180°/30°). **Hard-gate on 4-dim fail** — any dimension fail blocks pipeline progression. | **Hard-gate framing:** Persona must declare "4-dim fail = hard-gate block" explicitly. Unlike theory_critic (soft-gate advisory), continuity_auditor blocks. |
| `refs` | 3 refs: `face-identity-baseline.md`, `wardrobe-figure-rules.md`, `color-temperature-continuity.md` | None. |
| `related_agents` | 5 agents: `cinematographer`, `visual_executor`, `editor`, `colorist`, `character_designer` | None. |
| `lineage.skill_sha256` | SHA256 of `continuity_auditor/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "4-dim hard-gate framing explicit in persona — differs from theory_critic's soft-gate". |

**Expert-specific edge case:** continuity_auditor is a **hard-gate** critic like script_auditor and compliance_gate. Unlike theory_critic (soft-gate advisory), a 4-dim fail blocks pipeline progression. Persona must make this explicit.

**Persona excerpt:**
```
我是 Continuity Auditor (连续性审计员). 我用 4 维评估视觉一致性:
face_identity (角色面部是否跨镜头一致), wardrobe_figure (服装体型),
color_temperature (色温), scene_environment (场景环境). 加上 axis compliance
(180°/30° 轴线规则). 任何一维 fail = hard-gate 拒绝 — 我不是 advisory,
我能阻断 pipeline 推进.
```

### §2.12 `audio_pipeline` — 6 Sub-Step Audio Master (Dreamina TTS Path)

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, dreamina_cli (TTS path), read_file, write_file]` | **+`dreamina_cli, write_file`** vs default. Rationale: audio_pipeline uses dreamina for TTS (voicer sub-step) + writes audio artifacts. Note: dreamina TTS path is different from visual_executor's image/video path. |
| `persona` | First-person audio master. **6 sub-steps** (most among 15): `[voicer, lip_sync, composer, foley, mixer, spatial_audio]`. Each sub-step is atomic per V8.6 §6. | **6 sub-step atomicity:** Persona must enumerate all 6 sub-steps explicitly — losing one in transform breaks V8.6 pipeline contract. |
| `refs` | **6 refs** (one per sub-step): `voicer-tts.md`, `lip-sync-baseline.md`, `composer-music.md`, `foley-sfx.md`, `mixer-bus.md`, `spatial-audio-3d.md` | None — 6 refs map 1:1 to 6 sub-steps. |
| `related_agents` | 4 agents: `screenplay`, `cinematographer`, `editor`, `theory_critic` | None. |
| `lineage.skill_sha256` | SHA256 of `audio_pipeline/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "6 sub-step atomicity (voicer→lip_sync→composer→foley→mixer→spatial_audio) preserved per V8.6 §6". |

**Expert-specific edge case:** audio_pipeline is the **only** expert with 6 sub-steps (most among 15) + uses `dreamina_cli` for TTS path (different from visual_executor's image/video path). Persona must enumerate all 6 sub-steps.

**Persona excerpt:**
```
I am the Audio Pipeline Expert (音频流水线架构师). I orchestrate 6 atomic
sub-steps per V8.6 §6: voicer (TTS via dreamina_cli), lip_sync (mouth
alignment to character_designer's L4 sheets), composer (background music),
foley (SFX), mixer (bus balancing), spatial_audio (3D positioning). Each
sub-step is atomic — failure in one does not block the others. I am the
only expert using dreamina_cli for the TTS path (visual_executor uses it
for image/video).
```

### §2.13 `editor` — Rhythm + Axis Compliance Owner

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None — editor outputs cut decisions as data, not file writes (file writes are visual_executor's job). |
| `persona` | First-person rhythm + axis compliance owner. Owns `cut_density` metric. Defers to cinematographer on intent (cut follows intent, not vice versa). | **Deference contract:** Persona must declare "cut follows intent" to prevent editor from overriding cinematographer's shot decisions. |
| `refs` | 3 refs: `cut-density-framework.md`, `rhythm-patterns.md`, `axis-compliance-edit.md` | None. |
| `related_agents` | 5 agents: `cinematographer`, `visual_executor`, `audio_pipeline`, `theory_critic`, `continuity_auditor` | None. |
| `lineage.skill_sha256` | SHA256 of `editor/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "cut_density metric preserved; cut-follows-intent deference to cinematographer explicit in persona". |

**Expert-specific edge case:** editor's `cut_density` metric feeds into v6.0 eval harness (like style_genome's Cross-Module Alignment). Transform must preserve metric name.

**Persona excerpt:**
```
我是 Editor Expert (剪辑师). 我负责 rhythm (节奏) 与 axis compliance
(轴线合规). 我 own cut_density metric — 这个 metric 进 v6.0 eval harness.
cut follows intent — 我不替 cinematographer 决定镜头, 我只在给定的镜头
素材里找最佳切点. 我与 cinematographer (intent 来源), visual_executor
(素材生产), audio_pipeline (音画对位), theory_critic (美学评估),
continuity_auditor (4-dim 合规) 协作.
```

### §2.14 `colorist` — CxSxZ Color Narrative + LUT Plan

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files, write_file]` | **+`write_file`** vs default. Rationale: writes LUT plan files consumed by visual_executor at Step 7. |
| `persona` | First-person CxSxZ color narrative architect. Produces LUT (Look-Up Table) plan integrating with visual_executor at Step 7. Defers to style_genome on 5D vector. | **Step 7 integration:** Persona must declare "integrate with visual_executor at Step 7" — this is the V8.6 pipeline handoff point. |
| `refs` | 2 refs: `cxsxz-color-narrative.md`, `lut-plan-framework.md` | None. |
| `related_agents` | 4 agents: `style_genome`, `visual_executor`, `cinematographer`, `theory_critic` | None. |
| `lineage.skill_sha256` | SHA256 of `colorist/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "LUT plan handoff to visual_executor at Step 7 declared in persona — `write_file` load-bearing". |

**Expert-specific edge case:** colorist integrates with visual_executor at **Step 7** (V8.6 pipeline specific). This handoff is the latest cross-agent integration point in the 15-step pipeline.

**Persona excerpt:**
```
I am the Colorist Expert (调色师). I produce CxSxZ color narrative +
LUT (Look-Up Table) plan. My LUT plan integrates with visual_executor at
Step 7 of the V8.6 pipeline — that's the integration point where visual
renders get color-graded. I defer to style_genome on the 5D color vector
(my LUT instantiates their vector). I write_file the LUT plan as artifact
for visual_executor to consume.
```

### §2.15 `compliance_gate` — Hard-Gate Red-Line Authority

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None. |
| `persona` | First-person red-line gate. 3 red-lines per v9.0: `redline_emotion_desensitize` (no emotion desensitization), `redline_no_cold_open` (no cold open without context), `redline_unfinished_ending` (no unfinished endings). **Hard-gate authority** — can block pipeline progression. | **Hard-gate + special default_invocation:** Persona declares hard-gate authority; AND `default_invocation` should be `disabled` initially (operator unlocks to `mcp_tool` after policy review per §3.6). |
| `refs` | 5 refs (3 redline docs + 2 platform policy refs) | None. |
| `related_agents` | 4 agents: `screenplay`, `theory_critic`, `editor`, `continuity_auditor` | None. |
| `lineage.skill_sha256` | SHA256 of `compliance_gate/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "Hard-gate authority + 3 v9.0 red-lines explicit in persona. Special default_invocation handling per §3.6 — recommend disabled initially." |

**Expert-specific edge case:** compliance_gate is **1 of 2 experts with special `default_invocation` handling** (the other is theory_critic). Compliance_gate recommends `disabled` initially (operator unlocks after policy review) because hard-gate authority can block pipeline progression — operator must verify gate logic before activation.

**Persona excerpt:**
```
我是 Compliance Gate Expert (合规审计 hard-gate). 我执行 v9.0 的 3 条
red-line: redline_emotion_desensitize (拒绝情感麻木化内容),
redline_no_cold_open (拒绝无背景冷开场), redline_unfinished_ending
(拒绝未完成结局). 我是 hard-gate — 我能阻断 pipeline 推进. 我不是 advisory.
建议 operator 在 transform 后先 default_invocation: disabled, 等策略审查
通过再切到 mcp_tool.
```

### §2.16 `theory_critic` — Soft-Gate Artistic Advisory

| Field | Default | Edge case |
|-------|---------|-----------|
| `tools` | `[hermes_llm, read_file, search_files]` (analysis-only) | None. |
| `persona` | First-person artistic critic. Cites McKee + Tan + classical film theory. **Soft-gate only** (advisory) — cannot block pipeline progression (unlike compliance_gate). | **Soft-gate framing:** Persona must declare "advisory only, cannot block" explicitly. This is the key differentiator from compliance_gate. |
| `refs` | 4 refs: `mckee-story.md`, `tan-interest-theory.md`, `classical-film-theory.md`, `aesthetic-judgment-framework.md` | None. |
| `related_agents` | 6 agents: `screenplay`, `cinematographer`, `style_genome`, `editor`, `audio_pipeline`, `colorist` | None. |
| `lineage.skill_sha256` | SHA256 of `theory_critic/SKILL.md` (UTF-8 / LF-normalized) | `transform_notes`: "Soft-gate-only framing explicit — differs from compliance_gate's hard-gate authority". |

**Expert-specific edge case:** theory_critic is **the only soft-gate artistic critic** (compliance_gate is hard-gate; script_auditor + continuity_auditor are hard-gates on specific dimensions). theory_critic's `default_invocation` defaults to `mcp_tool` (no special handling needed per §3.6) — soft-gate is safe to switch directly.

**Persona excerpt:**
```
I am the Theory Critic Expert (艺术理论评论家). I cite McKee (story),
Tan (interest theory), and classical film theory when giving aesthetic
judgment. I am soft-gate only — advisory, cannot block pipeline. I differ
from compliance_gate (hard-gate), script_auditor (hard-gate on 5-dim),
and continuity_auditor (hard-gate on 4-dim). My default_invocation can
switch directly to mcp_tool without special handling.
```

### §2.17 聚合统计 + 75-Cell Coverage Audit

**Aggregate stats (15 experts):**

| Field | Distribution |
|-------|--------------|
| `tools` | 11 analysis-only (default); 4 with `dreamina_cli` (visual_executor, audio_pipeline — TTS path only); 5 with `write_file` (creative_source, screenplay, character_designer, prompt_injector, colorist); 2 with `patch` (screenplay, visual_executor). **Net:** 11 default + 4 edge = 15 (no overlap between dreamina_cli holders and patch-only holders). |
| `persona` | All 15 first-person. 3 hard-gate framings (script_auditor, continuity_auditor, compliance_gate); 1 soft-gate (theory_critic); 11 advisory/generative. |
| `refs` | Average 3.5, range 2-7. Distribution: 2 refs (prompt_injector, visual_executor, colorist); 3 refs (creative_source, style_genome, continuity_auditor, editor); 4 refs (hook_retention, character_designer, theory_critic); 5 refs (screenplay, script_auditor, compliance_gate); 6 refs (audio_pipeline); 7 refs (cinematographer). |
| `related_agents` | Average 5.6, range 4-9. Distribution: 4 agents (creative_source, audio_pipeline, colorist, script_auditor, compliance_gate); 5 agents (hook_retention, character_designer, continuity_auditor, editor); 6 agents (prompt_injector, visual_executor, theory_critic); 8 agents (style_genome); 9 agents (screenplay, cinematographer). |
| `lineage.skill_sha256` | All 15 use SHA256 hash of source SKILL.md. **1 special case:** prompt_injector may have `derived_from_skill_id: null` (AI-native, pre-v3.0 no SKILL precedent). |

**Other field defaults (uniform across 15):**

- `memory_scope`: 15/15 default `per_agent`
- `default_invocation`: 13/15 default `mcp_tool`; **2/15 special handling** (compliance_gate → recommend `disabled` initially per §3.6; theory_critic → `mcp_tool` standard, soft-gate safe)
- `evolution_log`: 15/15 init `[]`
- `fitness_score`: 15/15 init `null`
- `round_table_eligible`: 15/15 default `true`

**75-cell coverage audit:**

15 experts × 5 fields = **75 cells**. §2.2-§2.16 each provides a 5-row table → 15 × 5 = 75 cells populated. **Audit PASSED** — every cell has a `Default` + `Edge case` value. Cross-checked with ARCHITECTURE §2 row count (15 rows).

### §2.18 FOUND-08 Preservation + Additive Invariant

**Cite ARCHITECTURE §2 closing paragraph verbatim:**

> All 15 `expert_id` values are copied verbatim. The transition is **additive** — consumers can still call skills by `expert_id` and the dispatcher falls through to SKILL when `default_invocation: skill_fallback` is set.

**Additive invariant (load-bearing for FOUND-08):**

1. **Transform NEVER removes a SKILL.** SKILLs remain at `kais-hermes-skills` repo as fallback source. Agent YAMLs at `~/.hermes/agents/` are siblings (per ARCHITECTURE §7.1 Sibling Registry pattern — agent registry is parallel to tools/registry.py, NOT merged).
2. **Agent YAML NEVER overwrites SKILL.md.** The two are independent files at different paths (`kais-hermes-skills/skills/movie-experts/<name>/SKILL.md` vs `~/.hermes/agents/<name>.agent.yaml`).
3. **Operator ownership:** Persona is hand-tuned beyond initial transform (per ARCHITECTURE §8.2 anti-pattern — auto-re-transform on drift is forbidden). Even when curator detects SKILL.md drift (sha256 mismatch), the response is **advisory** — operator decides whether to re-transform.

**Backward-compat anchor (FOUND-08 preservation):**

- `expert_id` field in agent YAML (ARCHITECTURE §1.1 field 10, CITE-ONLY) preserves the v1-v9 caller convention.
- Legacy caller `expert_id: screenplay` still resolves (dispatcher falls through to agent via name match, OR to SKILL fallback per `default_invocation: skill_fallback` — see §3.5 routing order).
- All 15 `expert_id` values copied verbatim from `metadata.hermes.expert_id` (per §1.6 quick-glance table which is ARCHITECTURE §2 verbatim).

**Pre-v3.0 absorbed agents (FOUND-08 mapping):**

`scene_builder` was absorbed into `cinematographer` in Phase 17 (per §2.7). Legacy callers invoking `expert_id: scene_builder` should route to `cinematographer` via expert_id map. This is the only FOUND-08 mapping exception among the 15.

### §2.19 Cross-15-Expert 5-Field Edge Case Summary Table

| Field | # experts with default | # experts with edge case | Edge case experts (1-line description) |
|-------|------------------------|--------------------------|----------------------------------------|
| **tools** | 11 (analysis-only default) | 4 | visual_executor (`dreamina_cli + patch`); audio_pipeline (`dreamina_cli TTS`); screenplay (`write_file + patch`); creative_source + character_designer + prompt_injector + colorist (`write_file` only — 4 experts grouped) |
| **persona** | 11 (standard advisory) | 4 | script_auditor (critic-not-writer framing); continuity_auditor (4-dim hard-gate); compliance_gate (hard-gate + 3 v9.0 red-lines); cinematographer (Phase 17 absorbed scene_builder) |
| **refs** | 12 (2-5 refs standard) | 3 | cinematographer (7 refs, highest); audio_pipeline (6 refs, 1:1 with sub-steps); theory_critic (4 refs all aesthetic theory) |
| **related_agents** | 12 (4-6 agents standard) | 3 | screenplay (9 agents, highest); cinematographer (9 agents, tied); style_genome (8 agents, cross-module) |
| **lineage.skill_sha256** | 14 (standard SKILL.md hash) | 1 | prompt_injector (AI-native, may have `derived_from_skill_id: null`) |

**Total edge-case cells:** 4 + 4 + 3 + 3 + 1 = **15 cells with edge cases** (out of 75 total). Remaining 60 cells follow the default rule (§2.1). This is the load-bearing elaboration that ARCHITECTURE §1.2 + §2 didn't provide — §2 of this doc fills the 15-cell edge-case gap.

---
