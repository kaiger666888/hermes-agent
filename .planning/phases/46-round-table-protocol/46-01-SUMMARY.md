---
phase: 46-round-table-protocol
plan: 01
subsystem: v10-orchestrator-design
tags: [design, round-table-protocol, mcp, memory-conflict, serial-execution]
requires:
  - .planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md (Phase 44 decisions 5/6/7 LOCKED)
  - .planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md (Phase 45 schemas LOCKED)
  - .planning/research/v10-orchestrator-design/agents-schema.yaml (18-field agent schema)
  - .planning/research/v10-orchestrator-design/memory-record-schema.yaml (10-field memory record)
  - .planning/research/v10-orchestrator-design/STACK.md (§3.2 7-tool schema — canonical naming)
  - .planning/research/v10-orchestrator-design/ARCHITECTURE.md (§5.1 state file layout + §8 anti-patterns)
  - .planning/research/v10-orchestrator-design/PITFALLS.md (§Pitfall 7 memory conflict)
  - .planning/research/v10-orchestrator-design/FEATURES.md (§10 7 borrowable points)
  - .planning/research/v10-orchestrator-design/SUMMARY.md (CC-1 + CC-6 + 6 OQ resolutions)
  - ~/.claude/projects/-data-workspace-hermes-agent/memory/feedback-glm-overload-reduce-concurrency.md (serial root cause)
provides:
  - .planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md (design narrative)
  - .planning/research/v10-orchestrator-design/round-table-state-schema.yaml (JSON Schema draft 2020-12)
affects:
  - 04-MIGRATION-PATH.md (will cite §2 lifecycle + §4.2 MCP names)
  - 05-POC-PLAN.md (will cite §3 conflict arbitration + §4.1 serial + §4.3/§4.4 audit tables)
  - 03-COMPARISON-VS-KIMI-MCP-SHIM.md (will cite §4.2 MCP naming reconciliation)
  - 06-CROSS-REPO-IMPACT.md (will cite §2.4 state file path)
  - 51 VALIDATE lint script (cross-doc consistency check)
tech-stack:
  added: []
  patterns:
    - "JSON Schema Draft 2020-12 with camelCase keywords (Phase 45 lesson applied)"
    - "Bilingual design doc: EN structure (headers, schemas, field names) + 中文 prose (rationale, examples)"
    - "Three hard constraints declared upfront (serial / STACK naming / atomic lifecycle)"
    - "CITE-ONLY schema field consumption pattern (no redefinition of Phase 45 fields)"
    - "Comparator LLM prompt template (v11.0 PoC-ready, ~2K tokens/call)"
key-files:
  created:
    - .planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md (1287 lines)
    - .planning/research/v10-orchestrator-design/round-table-state-schema.yaml (572 lines)
  modified: []
decisions:
  - "Turn lifecycle is 3 atomic ops: round_table_open (immediate return) → turn N (sequential await) → submit_round_table_result (idempotent 409 guard)"
  - "5 turn_order strategies (round-robin default + fixed/llm/matrix; fitness-weighted deferred to v11.1+)"
  - "Memory conflict arbitration = 5 sub-mechanisms aligned with PITFALLS §P7 mitigation 1-5"
  - "Scope precedence rule: session > project > global (applied in-context by comparator LLM)"
  - "Confidence-weighted voting tiebreak: Δconfidence ≤ 0.05 → deferred-to-operator (deterministic)"
  - "Serial execution is non-negotiable: 1 panelist 1 turn await, MEMORY.md global concurrency==1 BY DESIGN"
  - "MCP tool naming adopts STACK §3.2 form (no agent_ prefix, aligns with 9 existing messaging tools)"
metrics:
  duration: ~25 min (design-only, no code)
  completed: 2026-07-07
  tasks: 5/5
  files-created: 2
  lines-written: 1859 (1287 narrative + 572 schema)
---

# Phase 46 Plan 01: Round Table Protocol Summary

**One-liner:** v10.0 round table protocol — 3 atomic lifecycle ops (round_table_open → turn N → submit_round_table_result) over serial panelist turns, with 5-mechanism memory conflict arbitration (P7 mitigations) and STACK-form MCP tool naming.

## Deliverables

### 1. `02-ROUND-TABLE-PROTOCOL.md` (1287 lines)

v10.0 design doc #02 — comprehensive round table protocol narrative covering:

- **§0 阅读指南** — chapter map, 3-audience guide (Kai reviewer / Kimi Notion 续聊 / v11.0 PoC implementer), Phase 44/45 consumption preamble
- **§1 Protocol Overview** — design philosophy (root-arg-决策-5/6/7 anchors), turn lifecycle ASCII diagram, SC#1-5 mapping table, roadmap placement, **3 hard constraints declared upfront** (serial / STACK-form naming / atomic lifecycle)
- **§2 Turn Lifecycle** — 8 subsections: §2.1 round_table_open (with full worked example) / §2.2 turn N (serial invariant) / §2.3 submit_round_table_result (with idempotency replay scenario) / §2.4 state file persistence (ARCHITECTURE §5.1 verbatim path + crash recovery) / §2.5 5 turn_order strategies + decision tree / §2.6 agent deletion semantics (OQ-5 worked example with drift detection) / §2.7 early-stop conditions / §2.8 serial invariant restatement
- **§3 Memory Conflict Arbitration** — 8 subsections aligned with PITFALLS §P7 mitigation 1-5: §3.1 memory annotation / §3.2 comparator LLM pass (v11.0 PoC-ready prompt template) / §3.3 scope precedence (session > project > global) / §3.4 confidence-weighted voting / §3.5 conflict log for curator review / §3.6 decision tree / §3.7 edge cases
- **§4 Hard Constraints + Audit** — §4.1 serial root cause (MEMORY.md verbatim + token math + 3 implementation invariants) / §4.2 STACK-form MCP naming (9-tool reconciliation table) / §4.3 6 OQ resolution audit table / §4.4 7 borrowable points coverage audit table
- **§5 MCP Tool Contract** — 7 tools in STACK §3.2 form (get_agent_persona / get_agent_opinion / get_agent_memory / submit_round_table_result / submit_artifact / query_memory / run_python_phase)
- **§6 Advanced Features** — 4 features deferred to v11.1+ (subpanel / hooks / panelist_role / asset_locks)
- **§7 Downstream Citation Guide** — citation card table for 04/05/03/06/51 consumers + coherence declaration + references

### 2. `round-table-state-schema.yaml` (572 lines)

JSON Schema Draft 2020-12 for `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json` state file:

- **9 required top-level fields:** roundId / projectId / question / panelists / turnOrder / status / turns / roundTableOpen / createdAt
- **7 optional top-level fields:** submitRoundTableResult / earlyStopRule / maxRounds / conflicts / personaSnapshots / schemaVersion / lastUpdatedAt
- **7 `$defs` reusable shapes:** PanelistSnapshot / TurnOrder / Turn / ConflictRecord / EarlyStopRule / RoundTableOpen / SubmitRoundTableResult
- **camelCase keywords throughout** (Phase 45 verification lesson applied)
- Each load-bearing field has YAML comment citing OQ / PITFALLS §P1/P7/P14 mitigation / FEATURES B2.1/B8.2 borrowable point

## Turn Lifecycle 3-Step Lock

```
1. round_table_open(roundId, panel, question, maxRounds, turnOrderStrategy, projectId)
   └─→ atomic start, returns immediately with {roundId, initialTurnOrder}
       (ARCHITECTURE §8.3 anti-pattern: NOT synchronous pipeline step)

2. For each turn i in 1..N (SERIAL await per OQ-8):
   └─→ CC selects panelist per turnOrder.strategy
   └─→ CC calls get_agent_opinion(panelist, topic, priorDiscussion)
   └─→ CC appends {turnIndex, panelistId, opinion, citedMemoryIds, submittedAt} to state file
   └─→ (optional) comparator LLM on conflicts → ConflictRecord appended

3. submit_round_table_result(roundId, conclusion, citedMemories, artifacts, conflicts)
   └─→ atomic commit, flips status: open → completed
   └─→ seals conflict log, emits event for curator
   └─→ returns {receiptId, sealedAt, finalConflictCount}
   └─→ idempotent: 409 Conflict on second submit for same roundId
```

## 5 Turn Order Strategies (OQ-2)

| Strategy | PoC scope | When to use |
|---|---|---|
| round-robin (default) | v11.0 ✅ | General discussions, no seniority |
| fixed | v11.0 ✅ | Compliance / audit (compliance_gate speaks last) |
| llm (progressive) | v11.0 ✅ | Dynamic — next speaker depends on current opinion |
| matrix (FSM) | v11.0 ✅ (simple 2-state); full editor → v11.1+ | Structured rebuttal / devil's advocate |
| fitness-weighted | v11.1+ deferred | Needs ≥10 fitness data points (won't exist at PoC start) |

## 6 OQ Resolutions

| OQ# | Resolution | Section |
|---|---|---|
| OQ-2 | default round-robin + 4 alternatives (fitness-weighted + matrix editor → v11.1+) | §2.5 + §4.3 |
| OQ-5 | open-time PanelistSnapshot + deleted flag (transcript integrity preserved) | §2.6 + §4.3 |
| OQ-8 | strict serial — 1 panelist 1 turn await (MEMORY.md global concurrency==1 BY DESIGN, non-negotiable) | §1.5.1 + §2.8 + §4.1 + §4.3 |
| OQ-9 | STACK §3.2 form (no agent_ prefix, aligns with 9 existing messaging tools) | §1.5.2 + §4.2 + §4.3 |
| OQ-11 | CC self-generates UUID v4 in round_table_open call | §2.1 + §4.3 |
| OQ-15 | comparator LLM + scope precedence + confidence voting + conflict log (5 mechanisms) | §3.0-§3.7 + §4.3 |

## 7 Borrowable Points Coverage (B1.4/B2.1/B2.3/B4.2/B6.1/B7.3/B8.2)

| BP# | Source | Where addressed | PoC scope |
|---|---|---|---|
| B1.4 | LangGraph hierarchical supervisor → nesting | §6.1 subpanel evaluation | v11.1+ deferred |
| B2.1 | AutoGen/MAF turn_order three-state | §2.5 5-strategy enum | v11.0 (4/5 strategies) |
| B2.3 | AutoGen nested chat → subpanel | §6.1 subpanel evaluation | v11.1+ deferred |
| B4.2 | Claude Agent SDK hooks → PreTurn/PostTurn | §6.2 audit hooks | v11.0 implicit via Turn schema; explicit event stream → v11.1+ |
| B6.1 | Camel-AI generator+critics → panelist_role | §6.3 role enum evaluation | v11.1+ additive field |
| B7.3 | Agent-MCP file-level lock → asset_locks | §6.4 evaluation | v11.0 trivially satisfied by serial; v11.1+ required if subpanels |
| B8.2 | A2A Task lifecycle FSM → turn state machine | §2.2 turn FSM + state schema status enum | v11.0 ✅ |

## Memory Conflict Arbitration 5-Mechanism Lock (P7 mitigation)

Aligned with PITFALLS §Pitfall 7 mitigation 1-5:

1. **Memory annotation in turns** — `Turn.citedMemoryIds` field, every citation carries record_id (mitigation 1)
2. **Comparator LLM pass** — Hermes coordinator extracts both memories, runs comparator LLM with v11.0 PoC-ready prompt template, broadcasts resolution (mitigation 2)
3. **Scope precedence** — `session > project > global` applied in-context by comparator LLM (mitigation 3)
4. **Confidence-weighted voting** — Phase 45 `confidence` field weighted; Δconfidence ≤ 0.05 → deferred-to-operator (deterministic tiebreak) (mitigation 4)
5. **Conflict log for curator review** — `state.conflicts` array sealed at submit; curator periodic pass reviews high-frequency conflicts for promote/quarantine (mitigation 5)

## Serial Constraint Lock (citing MEMORY.md verbatim)

> **MEMORY.md `feedback-glm-overload-reduce-concurrency.md` verbatim:**
> GLM 持续报 1305/overloaded 时...**演进历程**:**2026-07-03 从 5→3;2026-07-06 已是 1**。...**concurrency 到 1 之后再降不动了——上游模型容量本身就是瓶颈**...Telegram 用户会收到 115 字符的「暂停 10-15 分钟」消息,这是 by design,**不需要立刻做什么**。

**3 implementation invariants (load-bearing):**

1. v11.0 PoC `get_agent_opinion` MUST sequential `await` in for-loop, NEVER `Promise.all` or async-gather
2. Hermes dispatcher MUST reject concurrent `get_agent_opinion` calls for same `roundId` (return 429)
3. v11.0 PoC MUST NOT add "parallel round table" opt-in flag — structural constraint, not configurational

## MCP Tool Naming Lock (STACK §3.2 form, no agent_ prefix)

9-tool reconciliation table (ARCHITECTURE §4.2 deprecated → STACK §3.2 canonical):

| Deprecated | Canonical (ADOPTED) |
|---|---|
| `agent_get_persona` | `get_agent_persona` |
| `agent_recall` | `get_agent_memory` |
| `agent_opinion` | `get_agent_opinion` |
| `agent_conclude` | `submit_round_table_result` |
| (new) | `submit_artifact` / `query_memory` / `run_python_phase` / `agents_list` / `round_table_open` |

Aligns with existing `mcp_serve.py` 9 messaging tools (no prefix style).

## camelCase JSON Schema Keywords Confirmed

All property names in `round-table-state-schema.yaml` are camelCase (Phase 45 verification lesson applied):

- Top-level: roundId / projectId / turnOrder / roundTableOpen / submitRoundTableResult / earlyStopRule / maxRounds / personaSnapshots / schemaVersion / createdAt / lastUpdatedAt
- $defs: PanelistSnapshot.agentId / .personaSha256 / .fitnessScore / .memoryScope; Turn.citedMemoryIds / .conflictsDetected / .submittedAt; ConflictRecord.memoryIdA / .scopeA / .confidenceA / .resolvedAt; EarlyStopRule; RoundTableOpen.openedAt; SubmitRoundTableResult.citedMemories / .closedAt / .closedBy

No snake_case property names anywhere.

## Cross-Validation (every section cites traceable source)

- §1.1 cites Phase 44 决策 5/6/7 (root-arg anchors) + Phase 45 field consumption table
- §2 cites ARCHITECTURE §5.1 (state file path verbatim) + §5.3 (lifecycle sketch) + §8.3 (anti-pattern)
- §3 cites PITFALLS §Pitfall 7 mitigation 1-5 verbatim + Phase 45 memory-record-schema fields
- §4.1 cites MEMORY.md `feedback-glm-overload-reduce-concurrency.md` verbatim (5→3→1 evolution)
- §4.2 cites SUMMARY.md CC-1 + STACK §3.2 + ARCHITECTURE §4.2 (deprecated)
- §4.3 / §4.4 audit tables cite OQ + BP sources
- §5 cites STACK §3.2 Tool 1-7 for each MCP tool signature
- §6 cites FEATURES §10 B1.4 / B2.3 / B4.2 / B6.1 / B7.3 for each advanced feature

## Deviations from Plan

None — plan executed exactly as written. All 5 tasks completed in sequence with the prescribed deliverable structure.

## Self-Check

**Files created (verified to exist):**

- ✅ `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` (1287 lines, ≥ 800 target)
- ✅ `.planning/research/v10-orchestrator-design/round-table-state-schema.yaml` (572 lines, ≥ 200 target, JSON Schema draft 2020-12 valid)

**Commits verified (5 task commits + this SUMMARY commit):**

- ✅ `fbfbb5f3f` — Task 1: §0 + §1
- ✅ `15fb8aff1` — Task 2: round-table-state-schema.yaml
- ✅ `7c1fcbfd5` — Task 3: §2 turn lifecycle
- ✅ `116ba4614` — Task 4: §3 conflict arbitration + §4 hard constraints
- ✅ `aab9e5350` — Task 5: §5 MCP tools + §6 advanced + §7 citation

## Self-Check: PASSED
