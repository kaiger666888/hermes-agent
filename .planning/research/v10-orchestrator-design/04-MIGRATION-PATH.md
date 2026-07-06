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
