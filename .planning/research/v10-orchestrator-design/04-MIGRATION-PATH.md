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

## §3 — `default_invocation: skill_fallback → mcp_tool` 切换机制 (SC#3 Deep-Dive)

### §3.0 Why a Full Section on a 3-Enum Field?

本节是 **ROADMAP SC#3 的完整论证**. ARCHITECTURE §1.1 field 18 已定义 `default_invocation` enum (`mcp_tool | skill_fallback | disabled`, default `mcp_tool`), ARCHITECTURE §6.4 已声明 "SKILLs remain as fallback per `default_invocation: skill_fallback`". 本节的贡献是把三态语义**细化到 failure-mode matrix + transition path + safe-default-on-unknown 的可执行粒度** —— 当 v11.0 PoC 实施者问:

- "MCP tool 失败时怎么办?"
- "没有 `default_invocation` field 时 default 是什么?"
- "15 个 expert 哪些先切 `mcp_tool`?"

本节回答. 12-cell failure-mode matrix + 5-step per-agent transition path + FOUND-08 backward-compat anchor (via `expert_id` field, ARCHITECTURE §1.1 field 10) 共同构成 SC#3 的完整实施规则.

### §3.1 三态语义定义 (CITE agents-schema.yaml Field 18)

**CITE `agents-schema.yaml` field 18 verbatim (do NOT redefine enum):**

- **`mcp_tool` (default):** Agent invoked via `get_agent_opinion(name, question, context?)` MCP tool (STACK §3.2 Tool 2). Persona injected as **system-prompt fragment** (not user message). Output captured via `submit_round_table_result`. Round-table eligible (per `round_table_eligible` field 17).
- **`skill_fallback`:** Fall through to underlying SKILL body injection (**v1-v9 behavior**). SKILL body injected as **user message** (not system prompt). Output captured via existing skill output channel. NOT round-table eligible (SKILL has no `round_table_eligible` flag, default `false` for safety).
- **`disabled`:** Agent exists in `~/.hermes/agents/` registry but dispatcher rejects invocation. Used for:
  - **transform-in-progress** (persona not finalized)
  - **operator-locked** (`compliance_gate` pending policy review per §3.6)

Round-table NOT eligible in `disabled` state.

### §3.2 12-Cell Failure-Mode Matrix (3 Modes × 4 States)

**3 failure modes:**

- **(a) MCP tool runtime unavailable:** `mcp_serve.py` down / tool dispatch error / network partition (rare for stdio transport per Phase 44 决策 1 T6 协议)
- **(b) Agent persona missing or malformed:** YAML parse error / `persona` field empty / `tools` whitelist references non-existent tool
- **(c) Agent not in registry:** no `~/.hermes/agents/{name}.agent.yaml` for requested name/expert_id

**4 transition states:**

- **(1) `mcp_tool` active** — agent fully transformed + operator-verified
- **(2) `skill_fallback` active** — agent YAML exists but operator hasn't switched yet (intentional fallback during transition)
- **(3) `disabled`** — agent YAML exists but invocation locked (transform-in-progress or operator-locked)
- **(4) unknown** — no `default_invocation` field in YAML (schema-violation; agents-schema.yaml says field is optional with default `mcp_tool`, so this means operator authored YAML without the field)

**12-cell matrix:**

| Failure mode ＼ State | (1) `mcp_tool` active | (2) `skill_fallback` active | (3) `disabled` | (4) unknown (no field) |
|---|---|---|---|---|
| **(a) MCP tool unavailable** | Retry per tenacity backoff (3 retries, exponential). If all fail: return error to CC. **DOES NOT auto-fall to `skill_fallback`** — would change output semantics (system-prompt vs user-message persona injection). | N/A — already on `skill_fallback` path (no MCP tool invocation). | N/A — disabled agents aren't invoked at all. | Treat as `mcp_tool` (per agents-schema.yaml default); retry per tenacity; fail-with-error if exhausted. |
| **(b) Persona missing/malformed** | Return dispatcher error "agent persona invalid"; do NOT auto-fall to `skill_fallback` (persona corruption may indicate deeper YAML issue). Log to `errors.log`. Operator must fix YAML. | N/A — already on `skill_fallback`, persona not consumed in this path. | N/A — disabled. | Treat as `mcp_tool`; same error path as (1). |
| **(c) Agent not in registry** | N/A — agent not found means `mcp_tool` state is impossible. | N/A — same. | N/A — same. | **Always fall to SKILL fallback if SKILL exists** (v1-v9 backward-compat). If SKILL also missing: error "unknown agent/skill {name}". |

**Key insights from matrix:**

1. **Failure (a) + state (1)** is the **only ambiguous case** — should dispatcher auto-fall to SKILL when MCP fails? Decision: **NO** — output semantics differ (system-prompt vs user-message persona injection), so silent fallback would produce inconsistent results. Explicit error + operator intervention is safer.
2. **Failure (c)** is the **only always-fallback case** — missing agent is normal pre-transform state; SKILL fallback preserves v1-v9 behavior.
3. **State (4) unknown** always defaults to `mcp_tool` semantics (per agents-schema.yaml) — forward-compat for v11.0+ agents authored without explicit field.

### §3.3 Safe-Default-on-Unknown (Two Rules)

**Two safe-default rules cover the ambiguous dispatch cases:**

**Rule 1: Agent YAML missing `default_invocation` field → default to `mcp_tool`**
- Rationale: forward-compat. v11.0+ agents are agent-first; agents-schema.yaml declares `mcp_tool` as the field default.
- Risk: if operator creates an agent YAML intending `skill_fallback` but forgets the field, dispatcher treats as `mcp_tool`. Mitigation: Phase 51 VALIDATE lint should warn on agent YAMLs missing explicit `default_invocation` field.

**Rule 2: SKILL missing agent sibling → default to `skill_fallback`**
- Rationale: backward-compat. v1-v9 SKILLs continue working without transform; dispatcher falls through to SKILL body injection.
- Risk: if operator renames an agent YAML but forgets to update the SKILL `metadata.hermes.expert_id`, dispatcher may find SKILL but not agent. Mitigation: §3.5 routing order resolves by `name` first, then `expert_id` fallback.

**Both-exist-but-ambiguous case:** Agent YAML + SKILL both exist for same name/expert_id → **agent wins** (agent registry is source of truth per ARCHITECTURE §4.1 Sibling Registry pattern). Operator can force SKILL fallback by setting agent's `default_invocation: skill_fallback` explicitly.

### §3.4 Per-Agent Transition Path (5 Steps, NOT All-At-Once)

**Transition is per-agent, not all-at-once.** Operator transforms one SKILL → creates `~/.hermes/agents/{name}.agent.yaml` → switches `default_invocation`. Other 14 SKILLs continue as `skill_fallback` (or no agent at all).

**5-step transition sequence (per agent):**

1. **Run §2.X transform rules** for this expert → produce agent YAML with `default_invocation: disabled` initially
2. **Verify persona output via smoke test** — manually invoke the agent with a test question; check that persona produces first-person expert voice (not generic assistant)
3. **Switch to `default_invocation: mcp_tool`** — agent now invocable via `get_agent_opinion` MCP tool
4. **Update `round_table_eligible` to `true`** if desired — agent can now join round tables (Phase 46 protocol)
5. **(Optional) Mark SKILL as transformed** — v12+ may add `agent_transform_notes` frontmatter to source SKILL per ARCHITECTURE §6.4 row 2; v10.0/v11.0 PoC skips this

**Cite ARCHITECTURE §6.4 v11.0 PoC deliverable:** "15 `*.agent.yaml` files created by manual transform" — transition is manual, one expert at a time, ~5-10 minutes per expert (read SKILL → compute sha256 → fill 5-field table → write YAML → smoke test).

**Per-agent switch order recommendation (for v11.0 PoC):**

1. **First:** `screenplay` (central narrative role, 9 related_agents, HOOK-09 contract load-bearing — high-value test case)
2. **Second:** `cinematographer` (9 related_agents, scene_builder absorption — tests FOUND-08 mapping)
3. **Third:** `theory_critic` (soft-gate, safe to switch directly — tests `mcp_tool` baseline)
4. **Last:** `compliance_gate` (hard-gate, recommend `disabled` initially — operator must verify gate logic before unlock per §3.6)

### §3.5 FOUND-08 Backward-Compat Anchor

**`expert_id` field (agents-schema.yaml field 10, CITE-ONLY) preserves v1-v9 caller convention.**

Legacy caller invoking `expert_id: screenplay` still resolves. **Dispatcher routing order:**

1. **Check agent registry by `name`** — `agent_registry.get_agent(name="screenplay")` (per ARCHITECTURE §4.1)
2. **If agent found + `default_invocation: mcp_tool`** → invoke agent via `get_agent_opinion` MCP tool
3. **If agent found + `default_invocation: skill_fallback`** → fall through to SKILL body injection (v1-v9 behavior preserved)
4. **If agent found + `default_invocation: disabled`** → return dispatcher error "agent disabled"
5. **If agent NOT found by `name`** → check by `expert_id` fallback (agent YAML `expert_id` field, which may differ from `name` in rare rename cases)
6. **If agent NOT found by name OR expert_id** → default to SKILL fallback (v1-v9 behavior) — §3.3 Rule 2

**Cite ARCHITECTURE §1.1 field 10 + §1.2 SKILL body disposition:** `expert_id` is the bridge between old (skill) and new (agent) worlds. SKILL body disposition says "NOT copied. Becomes input to persona rewrite." — but `expert_id` is COPIED verbatim, preserving the routing key.

### §3.6 13/15 Standard Transition + 2/15 Special Handling

**13/15 standard transition (`mcp_tool` default):**

`hook_retention`, `creative_source`, `screenplay`, `script_auditor`, `character_designer`, `cinematographer`, `style_genome`, `prompt_injector`, `visual_executor`, `continuity_auditor`, `audio_pipeline`, `editor`, `colorist`, `theory_critic` — wait, that's 14. Let me recount: 13 standard excludes `compliance_gate` (special) and `theory_critic`. But `theory_critic` is also special — soft-gate framing, but `default_invocation: mcp_tool` is safe (no blocking authority). So 14 standard + 1 special (`compliance_gate` only).

**Correction:** 14/15 standard transition. Only `compliance_gate` needs special handling.

Actually, re-reading §2.17 + §2.15 + §2.16: `theory_critic` was flagged in §2.17 as "2/15 special handling (compliance_gate + theory_critic)". The distinction is:

- **`compliance_gate` special:** recommend `disabled` initially (operator unlocks after policy review). Hard-gate authority — premature `mcp_tool` activation could block pipeline progression before operator verifies gate logic.
- **`theory_critic` "special":** actually defaults to `mcp_tool` directly (soft-gate, safe). The "special handling" is just **acknowledging** in documentation that theory_critic is soft-gate (vs compliance_gate hard-gate). No `disabled` intermediate state needed.

**Net special handling:**

| Expert | `default_invocation` initial | Rationale |
|--------|------------------------------|-----------|
| 14 of 15 | `mcp_tool` (standard) | All advisory/generative/hard-gate-on-specific-dim experts are safe to switch directly after smoke test per §3.4 step 2 |
| `compliance_gate` | **`disabled` initially** (operator unlocks to `mcp_tool` after policy review) | Hard-gate authority — premature activation could block pipeline. Operator must verify the 3 v9.0 red-lines (`redline_emotion_desensitize` / `redline_no_cold_open` / `redline_unfinished_ending`) before unlock. |

**Transition step for `compliance_gate`:**

1. Transform per §2.15 → `default_invocation: disabled`
2. Operator reviews policy (3 red-lines + gate logic)
3. Smoke test with non-blocking test cases
4. Operator unlocks: `default_invocation: mcp_tool`
5. Update `round_table_eligible: true` (compliance_gate joins round tables as hard-gate panelist)

**Count reconciliation (§2.17 vs §3.6):**

§2.17 declared "2/15 special handling" (compliance_gate + theory_critic). §3.6 declares "1/15 special + 14/15 standard". The reconciliation:

- **§2.17 view (persona-framing perspective):** 2 experts have **persona-level** special framing — compliance_gate (hard-gate) + theory_critic (soft-gate). Both need persona to declare their authority level explicitly.
- **§3.6 view (dispatch perspective):** 1 expert has **dispatch-level** special handling — only compliance_gate needs `disabled` initially. theory_critic's soft-gate is safe for direct `mcp_tool` (no blocking authority, no pipeline risk).

Both counts are correct from their respective perspectives. The dispatch perspective (§3.6) is the load-bearing one for `default_invocation` switching — 14/15 standard + 1/15 special.

### §3.7 Round Table 消费 `default_invocation`

**CITE Phase 46 `round_table_eligible` field (agents-schema.yaml field 17) — 协同:**

`get_agent_opinion` MCP tool (STACK §3.2 Tool 2) checks panelist agent's `default_invocation` BEFORE invoking. Only `mcp_tool` state agents can join round tables. `skill_fallback` + `disabled` cannot.

**Why (rationale):**

- Round table requires **system-prompt-fragment persona** (mcp_tool mode) for panelist identity consistency across turns
- `skill_fallback` mode injects SKILL body as **user message** — no stable panelist identity across multiple turns (each invocation is stateless)
- Output capture via `submit_round_table_result` (Phase 46 atomic close event) only works in `mcp_tool` mode (skill_fallback has no MCP tool binding)

**Enforcement:**

`round_table_open` MCP tool (Phase 46) validates all panelists at open time:

```python
# pseudo-code — actual implementation in v11.0 PoC
for panelist_name in panel:
    agent = agent_registry.get_agent(panelist_name)
    if not agent or agent.get("default_invocation") != "mcp_tool":
        return tool_error(
            f"Panelist {panelist_name} not invocable "
            f"(state={agent.get('default_invocation') if agent else 'missing'})"
        )
```

Round table cannot open if any panelist is in `skill_fallback` or `disabled` state. **Cite Phase 46 `PanelistSnapshot` schema** (round-table-state-schema.yaml lines 263-307) — captures `agentId` + `fitnessScore` + `tools` + `memoryScope` at open time; `default_invocation` check is a precondition for entry into the snapshot.

**Mid-round state change edge case:**

If an agent's `default_invocation` flips mid-round (operator edits YAML while round table is open), the round table state file's `PanelistSnapshot` (captured at open time per Phase 46 OQ-5 resolution) prevails. Subsequent turns for that panelist continue using the open-time snapshot identity. The flip applies only to **new** round table opens. This prevents mid-round persona inconsistency.

**Phase 51 VALIDATE lint cross-check:**

VALIDATE lint will verify that every agent YAML with `round_table_eligible: true` also has `default_invocation: mcp_tool`. The combination `round_table_eligible: true` + `default_invocation: skill_fallback|disabled` is a configuration error (round-table-ineligible state flagged as eligible) — lint rejects it.

---

## §4 — Memory Schema 迁移计划 (SC#4 Deep-Dive + PITFALLS §P14 Mitigation)

### §4.0 Why This Section — P14 Risk + Resolution Declaration

本节是 **ROADMAP SC#4 的完整论证 + PITFALLS §P14 的 mitigation 落实**. v6.0 ship 的 `FeedbackStore` (`agent/feedback_store.py`) 是 **source schema**; Phase 45 `memory-record-schema.yaml` 是 **target schema**. 本节给出:

- 字段映射 (17-row source → target table, §4.3)
- `schema_version` forward-compat 语义 (cite memory-record-schema.yaml line 353, §4.4)
- dry-run migration mode (`hermes agent memory migrate --dry-run`, P14 mitigation 3, §4.5)
- safe-default-on-unknown-field (P14 mitigation 2, §4.6)
- 6-step migration 执行计划 (§4.7)
- rollback path (§4.8)
- P14 RESOLVED declaration (§4.9)

全部是为了防止 P14 (Schema Migration Breaks Memory Store — silent drop 或 unsafe default 污染 memory store). P14 是 v11.0 PoC 硬风险 (per PITFALLS risk register: severity MEDIUM, mitigation cost MEDIUM, PoC-acceptable deferral = NO — must ship with v11).

### §4.1 迁移 Source Schema 引用 (v6.0 FeedbackStore Ground Truth)

**Cite `agent/feedback_store.py` ground truth** (do NOT redefine — read the module directly for verification):

**Persistence layout (filesystem):**

```
~/.hermes/feedback/
├── buckets/
│   └── <skill_id>/
│       └── <source>.jsonl       # append-only, one FeedbackRecord per line, encoding="utf-8"
├── dedup/
│   └── sha256-registry.jsonl    # audit log of supersession events
└── index.json                    # versioned via _INDEX_VERSION = 1
```

**FeedbackRecord fields (per v6.0 ship):**

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `skill_id` | string | `"screenplay"` | Identifies which skill received the feedback |
| `source` | string | `"operator"` / `"auto_eval"` | Provenance — human operator vs automated eval |
| `skill_sha256` | string | `<sha256 of SKILL.md at feedback time>` | Content hash of source SKILL when feedback was given |
| `feedback_text` | string | `"Volvo S1-1 scene 3 needs more tension..."` | The feedback content |
| `verdict` | enum: `positive` / `negative` / `neutral` | `positive` | Operator's qualitative judgment |
| `operator_id` | string | `"kai"` | Who gave the feedback |
| `created_at` | ISO-8601 timestamp | `"2026-06-28T14:32:00Z"` | When feedback was recorded |

**`_INDEX_VERSION = 1` is for `index.json` ONLY**, NOT for record schema. This is the migration gap P14 warns about — the index has versioning, but individual FeedbackRecord lines do not carry a schema version. When target schema adds `confidentiality`, existing FeedbackRecord lines have no way to declare their confidentiality, forcing the migration to default it.

### §4.2 迁移 Target Schema 引用 (Phase 45 memory-record-schema.yaml)

**Cite Phase 45 `memory-record-schema.yaml` verbatim** (do NOT redefine — see `memory-record-schema.yaml` lines 1-380 for authoritative definition):

- **Layer 2 schema** (independent of `agents-schema.yaml` per SUMMARY CC-2 mandate — see memory-record-schema.yaml header lines 1-32).
- **10 mandated fields** (PITFALLS §P1/§P2/§P4/§P5/§P6/§P10/§P14 mitigations encoded as fields):

| # | Target field | Type | Required | Pitfall mitigated |
|---|--------------|------|----------|-------------------|
| 1 | `record_id` | string (UUID v4) | YES | P5 (curator audit) |
| 2 | `agent_id` | string `^[a-z0-9_-]+$` | YES | P4 (cross-project leakage routing) |
| 3 | `scope` | enum: `global` / `project` / `session` | YES | P4 (cross-project visibility) |
| 4 | `status` | enum: `active` / `archived` / `quarantined` | YES | P5/P6 (lifecycle + incident response) |
| 5 | `confidence` | float 0.0-1.0 | YES | P2 (time-decay) + OQ-4 default 0.5 |
| 6 | `evidence_chain` | list | YES | P5 (evidence coverage ≥3) |
| 7 | `created_at` | ISO-8601 | YES | P2 (time-decay start point) |
| 8 | `persona_sha256` | string `^[a-f0-9]{64}$` | YES | P1 (persona drift detection) |
| 9 | `schema_version` | string `^[0-9]+\.[0-9]+\.[0-9]+$` | YES (default `"1.0.0"`) | P14 (schema migration) — cite line 353 |
| 10 | `content` | string | (mandated by usage) | The memory fact itself |

**Optional / defaultable fields** (memory-record-schema.yaml additionalProperties: false, but several fields have defaults):

`project_id`, `session_id`, `expires_at`, `verified_at`, `supersedes_memory_id`, `evidence_operator_ids`, `half_life_days`, `last_recalled_at`, `recall_count`, `confidentiality`.

**Target schema is richer than source** — many fields have no source-side equivalent and must be filled with safe defaults (§4.6).

### §4.3 字段映射表 (Source → Target)

17-row mapping table. Source FeedbackRecord → Target memory-record:

| Source FeedbackRecord field | Target memory-record field | Mapping rule |
|-----------------------------|----------------------------|--------------|
| `skill_id` | `agent_id` (namespace component) | `agent_id = "{skill_id}"` per ARCHITECTURE §3.2 Option B convention (e.g. `screenplay` → `agent_id: screenplay`). NOT prefixed — mem0 routes via `agent_id` filter directly. |
| `source` | `evidence_chain[0].source_type` | Preserve as evidence provenance ("operator" / "auto_eval"). |
| `skill_sha256` | `evidence_chain[0].evidence_sha256` | Content hash of source evidence (the SKILL.md content at feedback time). |
| `feedback_text` | `content` | **Verbatim copy** — feedback_text becomes the memory fact content. |
| `verdict` | `status` | `positive` → `active`; `negative` → `quarantined` (P14 mitigation — never auto-activate negative-feedback records); `neutral` → `active` (neutral is informational, not blocking). |
| `operator_id` | `evidence_operator_ids[0]` | Single-element list. (If multiple operators gave same feedback, expand list.) |
| `created_at` | `created_at` | **Verbatim copy** — ISO-8601 timestamp preserved. |
| *(no source)* | `record_id` | Generated UUID v4 at migration time. |
| *(no source)* | `scope` | Default `"project"` (P14 mitigation 2 — tightest scope; can promote to `global` later via curator). |
| *(no source)* | `project_id` | From bucket path if encoded; else default `"unknown"` (P14 mitigation — never null, always trackable). |
| *(no source)* | `session_id` | Default `null` (legacy records have no session context). |
| *(no source)* | `confidence` | Default `0.5` (OQ-4 neutral — until curator evaluates). |
| *(no source)* | `half_life_days` | Default `180` (conservative — expire sooner rather than later; PITFALLS §P2 mitigation). |
| *(no source)* | `expires_at` | Default `created_at + 180 days` (matches half_life_days). |
| *(no source)* | `verified_at` | Default `created_at` (legacy records treated as verified at creation; curator may downgrade). |
| *(no source)* | `supersedes_memory_id` | Default `null` (no prior record to supersede at migration time). |
| *(no source)* | `confidentiality` | Default `"confidential"` (P14 mitigation 2 — **safest not most permissive**; never `public` by default). |
| *(no source)* | `persona_sha256` | Computed from agent YAML persona at migration time (cross-layer invariant per PITFALLS §P1 mitigation 4). |
| *(no source)* | `schema_version` | Default `"1.0.0"` (v10.0 baseline per memory-record-schema.yaml line 356). |

**Mapping edge cases:**

- **Multiple sources for same feedback:** If `feedback_text` and `skill_sha256` match across multiple FeedbackRecord lines (same evidence, different `source`), they collapse into ONE memory-record with `evidence_chain[N]` (N entries, not 1).
- **Negative verdict aggregation:** Multiple `verdict: negative` records for same `skill_id` aggregate into ONE memory-record with `status: quarantined` + `evidence_chain[N]` + `confidence: 0.5 + 0.1 * N` (each additional negative evidence boosts confidence slightly, capped at 0.9).
- **Missing `skill_id` (rare, malformed record):** Skip the record + log to migration audit. Do NOT default — `agent_id` is required field, can't fabricate.

### §4.4 `schema_version` 字段引用 + Forward-Compat 语义

**Cite `memory-record-schema.yaml` line 353 verbatim (do NOT redefine):**

```yaml
schema_version:
  type: string
  pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$"
  default: "1.0.0"
  description: |
    Version of the memory-record schema this record conforms to.
    Source: PITFALLS §P14 mitigation 1.
```

**Forward-compat semantics (P14 mitigation 1):**

1. **Read path tolerates older versions:** v1.x records are readable by v2.x reader with fallback logic (reader detects `schema_version < current`, applies forward-compat shims for missing fields).
2. **Migration job backfills:** v1.x → v2.x transform with audit log (every backfill record logged to `dedup/sha256-registry.jsonl` per v6.0 pattern).
3. **v10.0 baseline:** `schema_version = "1.0.0"` (matches FeedbackStore `_INDEX_VERSION = 1` for alignment — humans can intuit the correspondence).

**Future bumps (post-v10.0):**

- **v11.0 PoC:** `schema_version = "1.0.0"` (baseline — migration target as specified here).
- **v11.1+:** If `model_id` field is added (per PITFALLS §P8 model isolation), bump to `schema_version = "1.1.0"` + migration job backfills `model_id: null` for existing records.
- **v12.0+:** If `round_table_id` field is added (per Phase 46 cross-round memory tracking), bump to `schema_version = "2.0.0"` + migration job.

**Bump policy:** Semver — patch/minor for backward-compatible field additions; major for breaking changes (field renames, enum value removals). All bumps require a new migration job + dry-run per §4.5 discipline.

### §4.5 Dry-Run Migration Mode (P14 Mitigation 3)

**Cite PITFALLS §P14 mitigation 3 verbatim:** "Migration script with dry-run: `hermes agent memory migrate --dry-run` shows what would change before applying."

**Command (v11.0 PoC target — NOT implemented in v10.0):**

```bash
hermes agent memory migrate --dry-run
# Optional flags (v11.1+):
#   --source ~/.hermes/feedback/  (default: HERMES_HOME/feedback)
#   --target mem0                  (default: mem0 backend configured in cli-config.yaml)
#   --agent-id-namespace "agent:"  (default: no prefix per §4.3)
```

**Dry-run output plan (5 metrics):**

```
Memory Migration Dry-Run Report
================================
Source: ~/.hermes/feedback/ (v6.0 FeedbackStore, _INDEX_VERSION=1)
Target: mem0 backend (memory-record-schema v1.0.0)

(a) Total source records: 1,247 FeedbackRecord lines across 15 buckets/
    Breakdown by skill_id:
      screenplay:    312 records (25.0%)
      cinematographer: 248 (19.9%)
      hook_retention: 156 (12.5%)
      ... (12 more)

(b) Per-target-field default fill rate:
      content:           100% source-derived (from feedback_text)
      agent_id:          100% source-derived (from skill_id)
      status:            96.2% source-derived (verdict→status), 3.8% quarantined (verdict=negative)
      evidence_chain:    100% constructed (source + skill_sha256)
      confidence:        100% default 0.5 (OQ-4 neutral — no source equivalent)
      half_life_days:    100% default 180
      expires_at:        100% default (created_at + 180d)
      confidentiality:   100% default "confidential" (P14 mitigation 2)
      schema_version:    100% default "1.0.0" (v10.0 baseline)
      scope:             100% default "project" (tightest scope)
      persona_sha256:    100% computed from agent YAML at migration time

(c) Conflict count: 47 records (3.8%) → status=quarantined
    Reason: source verdict=negative
    Action: P14 mitigation 2 — never auto-activate negative records

(d) Estimated target storage: ~2.4MB after migration
    Source size: 1.3MB (1,247 lines × ~1KB avg)
    Target size: ~2.4MB (1.8x source — added fields account for 80% of growth)
    mem0 backend may compress; actual footprint TBD.

(e) Mapping warnings:
    WARNING: 12 records have bucket path without project_id — defaulting to "unknown"
    WARNING: 3 records have verdict=neutral but feedback_text contains "block" —
             manual review recommended (may need verdict=negative)
    OK: No agent_id collisions detected (all 15 skill_ids map uniquely)

NO WRITE OCCURRED. To apply: hermes agent memory migrate (without --dry-run)
```

**NO write occurs in dry-run.** Output is human-readable (above) + machine-parseable (JSON summary to stdout for CI integration).

### §4.6 Safe-Default-on-Unknown-Field (P14 Mitigation 2)

**Cite PITFALLS §P14 mitigation 2 verbatim:** "default unknown fields to the SAFEST value, not the most permissive."

**Safe-default rules (6 fields with no source equivalent):**

| Unknown field | Safe default | Rationale |
|---------------|--------------|-----------|
| `confidentiality` | `"confidential"` | P14 mitigation 2 — never leak via default-`public`. Records can be promoted to `public` later via operator review, but never auto-leaked. |
| `scope` | `"project"` | Tightest scope among enum (`global` / `project` / `session`). Can be promoted to `global` later via curator cross-project promotion gate. |
| `status` (when `verdict` ambiguous) | `"quarantined"` | P14 mitigation 2 — never auto-activate unverified records. Quarantined records exist but aren't retrieved by default queries; curator can promote to `active` after review. |
| `confidence` | `0.5` (neutral) | OQ-4 resolution — neutral until curator evaluates with evidence. Half-decayed after 180 days regardless. |
| `half_life_days` | `180` | Conservative — expire sooner rather than later. Aggressive half-life (`90`) would lose memory too fast; lax (`365`) would let stale memory pollute. 180 = 6 months = operator review cadence alignment. |
| `expires_at` | `created_at + 180 days` | Matches `half_life_days`. After expiry, record is eligible for archival (per memory-record-schema `status: archived`). |

**Why "safest not most permissive":**

The risk of permissive defaults (e.g. `confidentiality: public`) is **silent data leakage** — operator doesn't know records are public until an incident. The risk of safe defaults (e.g. `confidentiality: confidential`) is **false-positive access denial** — operator sees "record exists but restricted" and can manually promote. The former is unrecoverable (data already leaked); the latter is recoverable (operator promotes). P14 mitigation 2 mandates the recoverable failure mode.

### §4.7 Migration 执行步骤 (6 Steps)

**Estimated effort:** ~2-3 person-days (dry-run script + migration script + shadow-run comparator).

**Step 1 — Backup source (filesystem snapshot):**
```bash
cp -r ~/.hermes/feedback/ ~/.hermes/feedback.pre-migration.bak/
# Verify backup integrity
diff -r ~/.hermes/feedback/ ~/.hermes/feedback.pre-migration.bak/ && echo "Backup OK"
```
Source FeedbackStore is **append-only** — backup is a point-in-time snapshot. Operator can always restore from backup if migration goes wrong.

**Step 2 — Dry-run migration:**
```bash
hermes agent memory migrate --dry-run > migration-dryrun-report.txt
# Review the 5-metric output plan (§4.5)
# Verify mapping warnings are acceptable
```

**Step 3 — Operator approval gate (human checkpoint):**
Operator reviews `migration-dryrun-report.txt`. Approval criteria:
- (a) Total source records count matches expectations (no surprise gaps)
- (b) Quarantine count (verdict=negative) is reasonable (<10% of total)
- (c) Mapping warnings have been investigated
- (d) Estimated target storage is acceptable

**Step 4 — Live migration (write target + retain source):**
```bash
hermes agent memory migrate
# Writes ~2.4MB to mem0 backend per memory-record-schema v1.0.0
# Source FeedbackStore (~/.hermes/feedback/) is RETAINED unchanged
# Migration audit log appended to ~/.hermes/feedback/dedup/sha256-registry.jsonl
```

**Step 5 — Shadow run (30-day dual-read):**
- Curator + dispatcher read from BOTH source (FeedbackStore) AND target (mem0) for 30 days
- Compare query results: same agent_id, same question → same top-K memory records?
- Log discrepancies to `~/.hermes/logs/memory-migration-shadow.log`
- **Acceptance threshold:** <1% retrieval discrepancy (per §4.9 P14 acceptance)

**Step 6 — Decommission source (after shadow passes):**
```bash
# Mark source as read-only (chmod -w) — do NOT delete
chmod -R a-w ~/.hermes/feedback/
# Mark v1 schema deprecated in index.json
echo '{"_INDEX_VERSION": 1, "deprecated_at": "2026-08-07T00:00:00Z", "superseded_by": "memory-record-schema v1.0.0"}' > ~/.hermes/feedback/index.json
```
Source is **never deleted** — only marked deprecated. Rollback is always possible by reverting Step 6 + restoring from backup.

### §4.8 Rollback Path

**If shadow run reveals >1% retrieval discrepancy:**

Operator rolls back. **Rollback steps:**

1. **Delete v2 target records from mem0** — `hermes agent memory purge --agent-namespace migrated` (or scoped purge per agent_id)
2. **Retain v1 source** (NEVER deleted during migration — Step 1 backup + Step 4 retain + Step 6 chmod -w all preserve it)
3. **Investigate mapping error** — most likely candidates:
   - `verdict → status` mapping edge case (e.g. `verdict: neutral` should have been `quarantined` not `active`)
   - `skill_id → agent_id` namespace collision (rare — skill_ids are unique among 15 experts)
   - `confidence: 0.5` default too neutral (curator post-migration may need different starting confidence)
4. **Re-run dry-run with corrected mapping** — fix the mapping rule in §4.3, re-run §4.7 Step 2 (dry-run), verify the fix, then re-run §4.7 Step 4 (live migration)

**Rollback safety:** Source FeedbackStore is append-only and never mutated by migration — rollback is always safe. The only state lost on rollback is the v2 target records (intentionally deleted in step 1).

### §4.9 P14 风险评估 + RESOLVED Declaration

**P14 (Schema Migration Breaks Memory Store) — risk assessment:**

| Mitigation | This doc section | Implementation status |
|------------|------------------|----------------------|
| Mitigation 1: `schema_version` on every record | §4.4 | CITE memory-record-schema.yaml line 353 — field spec locked, v10.0 baseline `"1.0.0"` |
| Mitigation 2: Safe-default-on-unknown-field | §4.6 | 6 safe-default rules documented (confidentiality/scope/status/confidence/half_life_days/expires_at) |
| Mitigation 3: Migration script with dry-run | §4.5 | 5-metric dry-run output plan documented; v11.0 PoC implements actual `hermes agent memory migrate --dry-run` CLI |

**v11.0 PoC acceptance criterion (Phase 50 consumer):**

- Dry-run migration must run **clean** on existing FeedbackStore (no mapping errors, no unresolvable conflicts)
- 30-day shadow-run window must show **<1% retrieval discrepancy** before source decommission (§4.7 Step 5 → Step 6 gate)

**Resolution declaration:**

> **P14 RESOLVED in §4.** Three-layer mitigation (`schema_version` §4.4 + dry-run §4.5 + safe-default §4.6) + 6-step backup-first migration (§4.7) + always-safe rollback path (§4.8) collectively prevent P14 (silent drop / unsafe default pollution of memory store). Cite PITFALLS §P14 risk register entry (severity MEDIUM, PoC-acceptable deferral = NO) — this doc satisfies the "must ship with v11" requirement. Phase 50 POC-PLAN consumes §4.5 dry-run + §4.9 acceptance criteria as PoC week-1 work items.

---

## §5 — Retained-Phases Allowlist + Legacy mem0 Policy (SC#5 Deep-Dive, OQ-3 + OQ-10 Resolution)

### §5.0 Why This Section — SC#5 + OQ-3 + OQ-10 Three-Resolution

本节是 **ROADMAP SC#5 的完整论证 + SUMMARY OQ-3 + OQ-10 的 resolution**. STACK §3.2 Tool 7 已给 `run_python_phase` boundary tool 签名 (`async def run_python_phase(phase, ...)`); §11.2 已给 allowlist location (`round-table-schema.yaml` = `round-table-state-schema.yaml`). 本节给出:

- 7 个 retained step 的显式声明 + per-step rationale (§5.2)
- allowlist location resolution + `retained_python_phases` schema field spec (§5.3)
- enforcement mechanism (dispatcher-layer validation, no silent fallback, §5.4)
- 旧 v7.0 mem0 `agent_id=hermes` memory 遗留策略 (§5.5)
- 30-day sunset window (§5.6)

### §5.1 `run_python_phase` Boundary Tool 引用 (CITE STACK §3.2 Tool 7)

**Cite STACK §3.2 Tool 7 verbatim:**

- **Signature:** `async def run_python_phase(phase: str, ...) -> PhaseResult`
- **Purpose:** B3a Python runner 增量迁移的 boundary tool (Phase 44 决策 2 直接落实). Allow CC to invoke specific Python pipeline phases (ComfyUI generation / script audit / continuity audit / etc.) during round-table turns **without leaving the MCP tool boundary**.
- **Boundary semantics:** `openWorldHint=True` per STACK §3.2 — ComfyUI / dreamina_cli call is open-world (may fail, may produce unexpected output). CC must treat results as best-effort, not authoritative.
- **Hermes-side tool:** `run_python_phase` is a Hermes-side MCP tool (per Phase 44 决策 1 T6 协议 layer + 决策 7 Hermes-owns-structure). CC invokes via MCP call; Hermes validates + executes Python pipeline phase.

### §5.2 Retained-Phases Allowlist — 7 个 Step 显式声明 + Rationale

**Allowlist (Steps eligible for `run_python_phase`):**

| Step | Phase name | Why retained (delegate-only) | Why CC needs it |
|------|------------|------------------------------|-----------------|
| **Step 0** | `project_init` / `setup` | Pure project initialization (mkdir, copy templates, write initial config). No creative decisions. | CC asks Hermes to scaffold a new project structure; CC cannot mkdir in `~/.hermes/projects/` directly (filesystem-locked). |
| **Step 6.5** | `storyboard_assembly` (pre-generation) | Mechanical assembly of storyboard frames from prior decisions (script_auditor pass + character_designer L1-L4 + cinematographer shot list). No creative decisions — just composition. | CC asks Hermes to assemble the storyboard from round-table outputs; assembly requires reading 4-5 JSON artifacts CC doesn't have direct access to. |
| **Step 7** | `visual_generation` (ComfyUI / dreamina) | Long-running exec task (text2image / image2image / multimodal2video). dreamina CLI execution. CC cannot run dreamina directly (Hermes-side exec tool). | CC asks Hermes to generate visuals from prompt_injector's prompts; takes 30s-5min per frame; CC's MCP tool boundary cannot hold long exec calls without `run_python_phase` indirection. |
| **Step 10** | `script_audit_gate` | Deterministic gate (script_auditor 5-dim check + completion % prediction). No creative decisions — output is pass/fail + 5 dimension scores. | CC asks Hermes to run the audit gate; gate result drives round-table decision (pass → proceed; fail <65% → re-screenplay). |
| **Step 11** | `continuity_audit` | Deterministic gate (continuity_auditor 4-dim check + axis compliance). No creative decisions — output is pass/fail per dimension. | CC asks Hermes to run continuity audit; gate result drives visual re-generation if any dimension fails. |
| **Step 12** | `color_grading` | Deterministic transform (apply LUT plan from colorist to visual renders). No creative decisions — input is LUT plan, output is graded frames. | CC asks Hermes to apply LUT; transform is a function call, not a generative act. |
| **Step 15** | `final_render_export` | Long-running exec task (final render pipeline: stitch frames + audio + color + spatial audio). CC cannot run final render directly. | CC asks Hermes to render final output; takes 5-30min; CC's MCP tool boundary cannot hold this without `run_python_phase`. |

**Why OTHER steps NOT in allowlist:**

| Step | Phase name | Why NOT retained (CC cannot delegate) |
|------|------------|---------------------------------------|
| **Step 1** | `creative_ideation` | Creative decision — must be round-table consensus (creative_source + screenplay + theory_critic), not delegated. Per Phase 44 决策 7 (CC owns content). |
| **Step 2** | `story_kernel_expansion` | Creative decision — Snowflake Method expansion is creative_source's job in round table, not delegated. |
| **Step 3** | `screenplay_first_draft` | Creative decision — screenplay's job in round table, not delegated. |
| **Step 4** | `character_design` | Creative decision — character_designer's job in round table, not delegated. |
| **Step 5** | `cinematography_plan` | Creative decision — cinematographer's job in round table, not delegated. |
| **Step 6** | `prompt_translation` | Creative-technical decision — prompt_injector's job in round table, not delegated. |
| **Step 8** | `audio_pipeline` | Hermes internal sub_step orchestration (6 sub-steps per §2.12), not single-phase delegate. Audio is invoked via `audio_pipeline` agent in round table, not `run_python_phase`. |
| **Step 9** | `editor_cut` | Creative decision — editor's job in round table, not delegated. |
| **Step 13** | `compliance_gate` | Operator policy — hard-gate authority requires operator unlock (per §3.6), not CC-dispatchable. |
| **Step 14** | `theory_critic` | Creative advisory — theory_critic's job in round table (soft-gate advisory), not delegated. |

**Cite `v86-pipeline-mapping.md` step semantics** — the 15-step pipeline maps each step to its owning expert + creative/delegate classification.

### §5.3 Allowlist Location Resolution (OQ-10 + 02-ROUND-TABLE-PROTOCOL.md §5.7 Ambiguity)

**Cite STACK §11.2 line 1120 verbatim:**

> "run_python_phase 的 retained-phases allowlist 在哪定义? —— `round-table-schema.yaml` (= `round-table-state-schema.yaml`)."

**Resolve 02-ROUND-TABLE-PROTOCOL.md §5.7 ambiguity:**

Phase 46 §5.7 line 1145 mentions `~/.hermes/agents/{slug}/retained_phases.yaml` (a per-project file). This doc **clarifies the canonical location** is the **schema-level field** `retained_python_phases` in `round-table-state-schema.yaml` (because it's a schema-level constraint valid across all projects, not per-project config).

**Decision:** Schema field first; per-project override (v12+ optional) second.

**Schema field spec (NEW field added by this doc):**

```yaml
# round-table-state-schema.yaml — additive field
retained_python_phases:
  type: array
  description: |
    Allowlist of step IDs eligible for run_python_phase boundary tool invocation.
    Source: 04-MIGRATION-PATH.md §5.3 (OQ-10 resolution).
    Enforcement: dispatcher-layer validation in mcp_serve.py run_python_phase handler
      (04-MIGRATION-PATH.md §5.4).
    v10.0 baseline: Steps 0/6.5/7/10/11/12/15 (7 steps per §5.2 rationale).
    Future bumps may add steps (e.g. Step 8 audio if sub-step orchestration is simplified).
  items:
    type: string
    enum:
      - "step_0"        # project_init
      - "step_6_5"      # storyboard_assembly
      - "step_7"        # visual_generation
      - "step_10"       # script_audit_gate
      - "step_11"       # continuity_audit
      - "step_12"       # color_grading
      - "step_15"       # final_render_export
  default:
    - "step_0"
    - "step_6_5"
    - "step_7"
    - "step_10"
    - "step_11"
    - "step_12"
    - "step_15"
  required: true  # v10.0 baseline; future bumps may add steps
```

**Per-project override (v12+ optional):**

`~/.hermes/agents/.runtime/{slug}/retained_phases_overrides.yaml` may add project-specific steps (e.g. experimental Step 8 audio for a specific project). But base allowlist always comes from the schema field — projects can only ADD to allowlist, never REMOVE (security invariant).

### §5.4 Enforcement Mechanism (Dispatcher-Layer Validation)

**`run_python_phase` MCP tool handler validation:**

```python
# pseudo-code — actual implementation in v11.0 PoC mcp_serve.py
@mcp.tool()
async def run_python_phase(phase: str, round_table_id: str | None = None, ...) -> str:
    # Load allowlist from round-table-state-schema.yaml retained_python_phases field
    allowlist = _load_retained_python_phases()  # cached at startup
    if phase not in allowlist:
        return tool_error(
            f"phase '{phase}' not in retained_python_phases allowlist; "
            f"allowed: {allowlist}. "
            f"See 04-MIGRATION-PATH.md §5.2 for rationale."
        )
    # ... proceed with Python pipeline phase execution
```

**Key enforcement properties:**

1. **Dispatcher-layer validation BEFORE invocation:** Allowlist check happens before any Python code runs. CC cannot bypass via argument tricks — the check is on the `phase` parameter value, validated against an enum.
2. **No silent fallback:** Rejected calls return **explicit error** listing allowed steps — never auto-fall to "execute anyway". This preserves Phase 44 决策 7 (Hermes-owns-structure invariant).
3. **CC cannot bypass:** `run_python_phase` is a Hermes-side MCP tool (per Phase 44 决策 1 T6 协议 layer). CC only invokes via MCP call; Hermes validates before executing.
4. **Error message is actionable:** Error includes allowed steps + doc reference (§5.2). CC can re-try with valid phase value.

### §5.5 旧 v7.0 mem0 `agent_id=hermes` Memory 遗留策略 (OQ-3 Resolution)

**Cite SUMMARY OQ-3 verbatim:**

> "mem0 agent_id 冲突. v7.0 默认 agent_id=hermes 的旧 memory 怎么处理? 倾向性结论: 遗留 (不迁移), 新 agent invocation 从 agent_id=screenplay 等开始."

**Resolution (this section):**

v7.0 ship 默认 `agent_id=hermes` 的旧 memory **不迁移, 不删除**. 新 agent invocation 从 `agent_id=screenplay` / `agent_id=cinematographer` 等 per-agent namespace 开始.

**Rationale (why not migrate):**

1. **v7.0 memory is cross-agent global** (no per-agent isolation — single `agent_id=hermes` namespace)
2. **v10.0+ requires per-agent isolation** (Phase 44 决策 6 — `agent_id` per agent for scoped recall)
3. **Migration would require partitioning global memory by `skill_id`** — but v7.0 records lack `skill_id` field reliably (v7.0 mem0 plugin didn't enforce per-skill tagging)
4. **Cleaner to start fresh per-agent** — v10.0+ agents build their own memory from scratch via curator `_memory_evolution_phase`; legacy global memory has unknown provenance

**Legacy read-only fallback:**

Curator can read `agent_id=hermes` records as **fallback context** (e.g. "what did the system learn pre-v10.0?") but **never writes new records** to this namespace. The `agent_id=hermes` namespace becomes a frozen historical snapshot.

**Operator can manually bridge (optional):**

If operator wants specific legacy memory promoted to a v10.0+ agent's namespace, they can run:

```bash
hermes memory promote --from agent_id=hermes --to agent_id=screenplay --record-id <uuid>
# Curator evaluates the record + writes a new v1.0.0 record in screenplay namespace
# Original agent_id=hermes record remains as provenance
```

This is manual, opt-in, per-record — NOT a bulk migration.

### §5.6 Legacy Memory 30-Day Sunset Window

**Sunset timeline:**

- **Day 0:** v11.0 PoC launch — per-agent namespace (`agent_id=screenplay` etc.) becomes default for new writes
- **Day 0-30:** Transition window — curator + dispatcher read from BOTH `agent_id=hermes` (legacy) + `agent_id={per-agent}` (new) for queries that span the transition
- **Day 30:** Sunset date — read-path removes legacy fallback. `agent_id=hermes` records remain in mem0 (never deleted) but are no longer queried by default.

**During transition window (Day 0-30):**

- **Read preference:** Prefer new namespace (`agent_id={per-agent}`); fall back to legacy (`agent_id=hermes`) if new is empty for this query
- **Write destination:** Always new namespace (`agent_id={per-agent}`). Never write to `agent_id=hermes`.
- **Logging:** All legacy fallback reads logged to `~/.hermes/logs/legacy-memory-fallback.log` for sunset audit

**After sunset (Day 30+):**

- **Read path:** Per-agent namespace only. Legacy namespace ignored by default.
- **Operator override:** `~/.hermes/config.yaml` can extend sunset:
  ```yaml
  legacy_memory_sunset_days: 60  # default 30; extend if transition needs more time
  ```
- **Manual legacy access:** Operator can still query `agent_id=hermes` via explicit `hermes memory search --agent-id hermes ...` command (read-only).

**Sunset audit criteria (Day 30 review):**

Before removing legacy fallback, operator verifies:
- (a) Per-agent namespace coverage: each of 15 agents has at least 10 records (curator has been running for 30 days)
- (b) Legacy fallback hit rate <5% of total queries (most queries hit per-agent namespace, not legacy)
- (c) No critical knowledge loss reported (operator spot-checks legacy records for facts not yet in per-agent namespace)

If criteria fail, extend sunset via config (above).

---

## §6 — Phase 44 7 决策 Cross-Validation Audit + OQ/P14 Resolution

### §6.0 Audit Purpose

本节 audit 本 doc 的 75-cell transform + skill_fallback + memory migration + allowlist 是否**一致支持 Phase 44 锁定的 7 决策**. 预期 = **7/7 一致** (本 doc 是迁移路径落实, 不是 re-derivation — should not contradict any locked decision). 同时声明 OQ-3 + OQ-10 + P14 三条 open question 的 resolution 位置.

### §6.1 7-Row 决策 Audit Table

| 决策 # | 决策 (一句话) | 本 doc 实现位置 | 一致? | Citation |
|--------|---------------|------------------|-------|----------|
| **决策 1** | T6 协议 (Hermes MCP server + tmux dispatch + CC native MCP client) | §3 `default_invocation` 路由 (`mcp_tool` mode uses MCP tool); §5.4 `run_python_phase` enforcement (Hermes-side MCP tool, validates allowlist before execution) | ✅ | STACK §3.2 + Phase 44 §2.1 (`00-FIRST-PRINCIPLES.md`) |
| **决策 2** | B3a Python runner 增量迁移 (delegate-only phase 迁 CC via `run_python_phase`) | §5.1-§5.4 `run_python_phase` boundary tool + retained-phases allowlist (7 steps: 0/6.5/7/10/11/12/15) — **直接落实** | ✅ | STACK §3.2 Tool 7 + Phase 44 §2.2 |
| **决策 3** | D2 storyboard-first-class | §5.2 Step 6.5 storyboard assembly in retained-phases allowlist (D2 storyboard is delegate-eligible: mechanical assembly, not creative) | ✅ | ARCHITECTURE §6 + Phase 44 §2.3 |
| **决策 4** | G2 通用编排框架 | §2 15-expert transform table is G2 runtime's agent registry basis; §3 `default_invocation` is G2 dispatch path (mcp_tool / skill_fallback / disabled tri-state) | ✅ | ARCHITECTURE §6 + Phase 44 §2.4 |
| **决策 5** | α agent form (YAML + persona + tools + refs + memory_scope + lineage) | §2 75-cell transform is α form's 15-expert instantiation (each cell follows 5-field mapping); §3 `default_invocation` is α form's invocation semantics | ✅ | Phase 45 `agents-schema.yaml` 18 fields + ARCHITECTURE §1 (`§1.1` + `§1.2` + `§1.3`) |
| **决策 6** | per-agent memory + curator-driven 自进化 | §4 memory schema migration (v6.0 FeedbackStore → per-agent memory-record-schema); §5.5 legacy mem0 policy (`agent_id=hermes` 不迁移, new `agent_id={per-agent}` namespace) | ✅ | Phase 45 `memory-record-schema.yaml` + ARCHITECTURE §3 (`§3.1` + `§3.2` + `§3.4`) + Phase 44 §2.6 |
| **决策 7** | 分层 CC 角色 (Hermes 控结构, CC 控内容) | §3.4 `default_invocation` transition (operator owns the switch, step 2 smoke test before mcp_tool); §5.4 `run_python_phase` enforcement (Hermes validates allowlist, CC only invokes) | ✅ | STACK §3.2 + Phase 44 §2.7 |

### §6.2 偏差分析 (Deviation Analysis)

**预期:** 7/7 一致 (本 doc 是迁移路径落实, 不是 re-derivation).

**实际:** 7/7 一致. 本 doc 未发现 Phase 44 决策需修正.

**特别声明 — 决策 2 (B3a Python runner) 是本 doc 的直接 root argument:**

§5 retained-phases allowlist 是 决策 2 的**可执行落实**. STACK §3.2 Tool 7 给签名, §11.2 给 location, 本 doc §5.2 给 7 个 step value + rationale, §5.3 给 schema field spec, §5.4 给 enforcement. 决策 2 → STACK Tool 7 → §5 allowlist 的引用链完整.

**Allowlist revisability:**

若 v11.0 PoC 实施中发现 allowlist 需调整 (例如加 Step 8 audio pipeline, 或去掉 Step 12 color grading):

1. **Add a step:** Update §5.2 table + `retained_python_phases` enum in `round-table-state-schema.yaml` + bump schema version. Document in `05-POC-PLAN.md` risk register.
2. **Remove a step:** More conservative — require Phase 51 audit + operator approval. Update §5.2 + schema + bump version.

Allowlist is a **starting point**, not immutable. Phase 51 VALIDATE audits real PoC usage + may propose adjustments.

### §6.3 OQ-3 + OQ-10 + P14 Resolution Declaration

**Three open questions/pitfalls resolved in this doc:**

| ID | Question/Pitfall | Resolution location | Resolution summary |
|----|------------------|---------------------|--------------------|
| **OQ-3** | mem0 `agent_id` 冲突 — v7.0 默认 `agent_id=hermes` 的旧 memory 怎么处理? | **§5.5-§5.6** | **Legacy memory 不迁移 + 30-day sunset window + read-only fallback during transition.** New agent invocation starts from `agent_id=screenplay` etc. Source never deleted. |
| **OQ-10** | `run_python_phase` 的 retained-phases allowlist 在哪定义? | **§5.3** | **Location = `round-table-state-schema.yaml` `retained_python_phases` field** (per STACK §11.2 + SUMMARY OQ-10). Schema-level constraint, not per-project config. |
| **P14** | Schema Migration Breaks Memory Store — v11.0 PoC adds `confidentiality` field; existing records have no value; read path fails or defaults to `public`. | **§4** (§4.4 + §4.5 + §4.6 + §4.7 + §4.8 + §4.9) | **Three-layer mitigation:** `schema_version` (§4.4) + dry-run mode (§4.5) + safe-default-on-unknown (§4.6). 6-step backup-first migration (§4.7). Rollback path (§4.8). P14 RESOLVED in §4.9. |

**Cite SUMMARY.md OQ table + PITFALLS §P14 as resolution audit source.**

---

## §7 — Downstream Citation Guide + Coherence 声明 + References

### §7.0 Downstream Citation Card Table

| Downstream doc | Cite from this doc | Do NOT re-derive | Should derive |
|----------------|---------------------|-------------------|---------------|
| **`05-POC-PLAN.md`** | §2 75-cell transform table (PoC 实施 15 `*.agent.yaml` must follow this) + §3.4 transition path (PoC per-agent switch sequence — screenplay first, compliance_gate last) + §4.5 dry-run (PoC acceptance: dry-run must run clean) + §4.7 6-step migration (PoC week-1 work) + §5.2 allowlist (PoC `run_python_phase` test scope = 7 steps) | 18-field schema, 5-field mapping framework, OQ-3/OQ-10/P14 resolutions | PoC fitness battery, vertical slice selection, acceptance timeline |
| **Phase 50 POC-PLAN** | §5.2 retained-phases 7 steps (PoC `run_python_phase` test scope) + §4.9 P14 PoC acceptance (<1% shadow discrepancy) + §3.6 compliance_gate special handling (PoC switch order — disabled initially) | entire doc | PoC implementation sequence + budget + resource allocation |
| **51 VALIDATE lint** | §6.1 7 决策 audit table + §6.3 OQ-3/OQ-10/P14 resolution declarations + §2.18 FOUND-08 invariant + §5.3 `retained_python_phases` schema field | entire doc | cross-doc consistency lint script (term/schema/decision/citation checks). Specific lint rules: (a) every `decision 决策 N` citation in 04 must resolve in `00-FIRST-PRINCIPLES.md §2.N`; (b) every `ARCHITECTURE §X` citation must resolve in `ARCHITECTURE.md`; (c) §2 15-expert table must match `ARCHITECTURE §2` row-by-row (FOUND-08 preservation); (d) `retained_python_phases` enum values must match §5.2 step list |

### §7.1 Coherence 声明 (Complete SC#1-5 Coverage)

**SC#1-5 coverage:**

- §2 15-expert 75-cell transform 规则表 → **SC#2**
- §3 `default_invocation: skill_fallback → mcp_tool` 切换机制 → **SC#3**
- §4 memory schema 迁移计划 → **SC#4**
- §5 retained-phases allowlist + legacy mem0 policy → **SC#5**
- (§1.3 SC mapping table → **SC#1** file existence + 1300+ lines + all required terms)

**+ Cross-validation:**

- §6 Phase 44 7 决策 cross-validation audit (7/7 一致)
- §6.3 OQ-3/OQ-10/P14 resolution declarations

**= 完整 ROADMAP SC#1-5 coverage.**

**v11.0 PoC implementer 一站式引用:**

v11.0 PoC implementer 引用本 doc 的 §2 75-cell + §3.4 transition path + §4.5 dry-run + §5.2 allowlist 即可 defending:

- "how do I transform this SKILL?" → §2 per-expert 5-field table
- "when do I switch to `mcp_tool`?" → §3.4 5-step transition + §3.6 compliance_gate special
- "how do I migrate memory safely?" → §4.5 dry-run + §4.7 6-step + §4.9 P14 acceptance
- "which Python phases can `run_python_phase` execute?" → §5.2 7 retained steps

不需重新推导 Phase 44 决策或 re-litigate P14.

### §7.2 References

**Phase 44 root-argument source:**
- `00-FIRST-PRINCIPLES.md §2.1` (决策 1 — T6 协议)
- `00-FIRST-PRINCIPLES.md §2.2` (决策 2 — B3a Python runner, LOAD-BEARING for SC#5)
- `00-FIRST-PRINCIPLES.md §2.3` (决策 3 — D2 storyboard-first-class)
- `00-FIRST-PRINCIPLES.md §2.4` (决策 4 — G2 通用编排框架)
- `00-FIRST-PRINCIPLES.md §2.5` (决策 5 — α agent form)
- `00-FIRST-PRINCIPLES.md §2.6` (决策 6 — per-agent memory + curator-driven 自进化)
- `00-FIRST-PRINCIPLES.md §2.7` (决策 7 — 分层 CC 角色)

**Phase 45 schema sources (CITE-ONLY):**
- `01-AGENT-REGISTRY-SCHEMA.md` (18-field schema narrative)
- `agents-schema.yaml` (18 fields authoritative definition — esp `default_invocation` enum field 18 + `lineage` field 7 + `memory_scope` field 6 + `round_table_eligible` field 17 + `expert_id` field 10)
- `memory-record-schema.yaml` (10 mandated fields + `schema_version` line 353 + `persona_sha256` + `agent_id` + `scope`)

**Phase 46 protocol source (CITE-ONLY + ADD `retained_python_phases` field):**
- `02-ROUND-TABLE-PROTOCOL.md §5.7` (`run_python_phase` round-table consumer — Phase 46 says "retained_phases.yaml"; this doc resolves location to `round-table-state-schema.yaml` `retained_python_phases` field per STACK §11.2)
- `round-table-state-schema.yaml` (existing required fields: `roundId` / `projectId` / `panelists` / `turnOrder` / `status` / `turns` / `roundTableOpen` / `createdAt`. NEW field added by this doc: `retained_python_phases` per §5.3)

**ARCHITECTURE sources (CITE-ONLY):**
- `ARCHITECTURE.md §1.1` (18-field schema source table)
- `ARCHITECTURE.md §1.2` (SKILL→YAML disposition — 5-field mapping skeleton)
- `ARCHITECTURE.md §1.3` (screenplay minimal example — concrete transform output reference)
- `ARCHITECTURE.md §2` (15-expert table — verbatim source for §2 75-cell elaboration, FOUND-08 preserved)
- `ARCHITECTURE.md §3.1` (Current Mem0 Backend Surface — `_read_filters()` returns `user_id` only; v7.0 default `agent_id=hermes` context)
- `ARCHITECTURE.md §3.4` (Curator-Driven Memory Evolution — `_memory_evolution_phase` writes records conforming to memory-record-schema)
- `ARCHITECTURE.md §6.1` (Transform Procedure 5 steps)
- `ARCHITECTURE.md §6.4` (Repo Impact Summary — Phase 49 v11.0 PoC deliverable = 15 `*.agent.yaml` via manual transform)

**STACK sources (CITE-ONLY):**
- `STACK.md §3.2 Tool 7` (`run_python_phase` signature + retained_phases allowlist pointer to round-table-schema.yaml)
- `STACK.md §11.2 line 1120` (OQ-10 resolution verbatim)

**PITFALLS source (CITE-ONLY):**
- `PITFALLS.md §P14` (Schema Migration Breaks Memory Store — 3 mitigations: `schema_version` + safe-default + dry-run)

**SUMMARY source (OQ resolutions):**
- `SUMMARY.md OQ-3` (line 69 — v7.0 mem0 `agent_id=hermes` legacy policy)
- `SUMMARY.md OQ-10` (line 76 — `run_python_phase` retained-phases allowlist location)

**Code-level source (v6.0 ground truth):**
- `agent/feedback_store.py` (v6.0 FeedbackStore: `buckets/<skill_id>/<source>.jsonl` + `dedup/sha256-registry.jsonl` + `index.json` versioned via `_INDEX_VERSION = 1`. FeedbackRecord fields: `skill_id` / `source` / `skill_sha256` / `feedback_text` / `verdict` / `operator_id` / `created_at`)

**Cross-repo complement:**
- `06-CROSS-REPO-IMPACT.md §3` (lineage chain — complement, do NOT re-derive; this doc focuses on per-expert transform rules, lineage is Phase 48's domain)

**MEMORY.md milestone context:**
- `v6-self-evolution-milestone.md` (v6.0 SHIPPED feedback-driven self-learning — FeedbackStore is the migration source)
- `kais-movie-agent-v5-hermes-native-migration.md` (2026-07-02 cross-repo migration moved skills/movie-experts + 4 plugins to kais-hermes-skills repo — SKILL.md there is transform source)
- `coding-agent-vs-mcp-shim.md` (v10.0 must contrast coding-agent vs Kimi MCP shim)
- `hermes-native-expert-agents.md` (Kai denies Kimi CC-Teammates, wants Hermes-side persistent agents — v10.0 design fulfills this)

**CLAUDE.md conventions:**
- HERMES_HOME (`~/.hermes/`) canonical state root
- Skill file conventions (`SKILL.md` uppercase, frontmatter parsed by `agent/skill_utils.parse_frontmatter`)
- Bilingual doc structure (EN headers + 中文 prose)
- Markdown tables for dimension comparison

**Phase commit references:**
- Phase 44 commit `314888271` (mark phase planned — 1 plan in 1 wave ready to execute)
- Phase 45 commit (agents-schema.yaml + memory-record-schema.yaml — see Phase 45 SUMMARY)
- Phase 46 commit (round-table-state-schema.yaml — see Phase 46 SUMMARY)
- Phase 48 commit (06-CROSS-REPO-IMPACT.md lineage chain)
- Phase 49 commit (this doc — 04-MIGRATION-PATH.md)

---

*End of 04-MIGRATION-PATH.md. Consumers: `05-POC-PLAN.md` consumes §2 + §3.4 + §4.5 + §4.7 + §5.2; Phase 50 POC-PLAN consumes §5.2 + §4.9 + §3.6; 51 VALIDATE consumes §6.1 + §6.3 + §2.18 + §5.3.*

