# Phase 52: INFRA-FOUNDATION - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped per autonomous smart-discuss rule)

<domain>
## Phase Boundary

Build the Hermes-side runtime layer for v11.0 PoC expert-agents system:

1. **Agent registry YAML loader** — load + validate `~/.hermes/agents/*.agent.yaml` per Phase 45 `agents-schema.yaml` (18 fields, JSON Schema Draft 2020-12, camelCase keywords). Rejected on schema violation; lineage fields (`derived_from_skill_id` / `skill_sha256`) populated for sample agents.
2. **7 MCP tools wire-up in `mcp_serve.py`** — `round_table_open` / `submit_round_table_result` / `get_agent_opinion` / `agents_list` / `agent_describe` / `memory_retrieve_scoped` / `memory_submit_record`. STACK §3.2 form (no `agent_` prefix). All consume Phase 45 + Phase 46 schemas.
3. **Round table state persistence + crash recovery** — per-project `.runtime/{slug}/round_tables/` path. State machine `open` → `in_progress` → `closed` (atomic). Crash recovery for 3 failure modes: partial-write corruption, mid-turn crash, orphaned session. Cross-project reference forbidden.
4. **Serial execution enforcement** — 1 panelist 1 turn sequential `await`. No parallel panelist execution. References MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (global concurrency==1 by design). GLM 4-key rotation compatible.

**Hard dependencies (downstream):** Phase 53 (creative slice) needs the registry + 7 MCP tools + state machine as runtime. Phase 54-55 (eval) need state machine + memory layer for benchmark + curator hooks.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation choices are at Claude's discretion — pure infrastructure phase. The v10.0 design suite (`.planning/research/v10-orchestrator-design/`) locks protocol-level decisions (MCP tool names, schemas, state machine, lifecycle, conflict arbitration); implementation-level choices (module layout, persistence file format, async lock primitive, test fixtures) follow established codebase patterns.

**Authoritative design sources (cite, do not re-derive):**
- `01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml` (18 fields, camelCase)
- `02-ROUND-TABLE-PROTOCOL.md` §5 (7 MCP tool narrative contracts) + `round-table-state-schema.yaml`
- `05-POC-PLAN.md` §3 + §6.1 (implementation path)
- `06-CROSS-REPO-IMPACT.md` §5.1 (`.runtime/{slug}/round_tables/` path) + §6 (3 crash recovery failure modes)
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (serial constraint policy)

**Established codebase patterns to follow:**
- `utils.py` `atomic_replace` / `atomic_json_write` / `atomic_yaml_write` helpers (line 87, 121, 190) — use these for state file writes; guarantees crash-safe rename.
- `mcp_serve.py` `FastMCP` + `@mcp.tool()` decorator pattern (9 existing tools at lines 471-831) — extend with 7 new tools following same form.
- `agent/` flat module layout (e.g., `agent/curator.py`, `agent/context_compressor.py`) — new modules: `agent/registry_loader.py`, `agent/round_table_state.py`, `agent/round_table_executor.py`, `agent/memory_arbitration.py` (latter two consumed by Phase 53).
- `tests/agent/` subdirectory pattern (e.g., `tests/agent/test_curator.py`) — new tests follow `tests/agent/test_registry_loader.py` / `tests/agent/test_round_table_state.py` form.
- `jsonschema.Draft202012Validator` for schema validation (already pinned in pyproject.toml).
- `asyncio.Lock` for in-process serial enforcement; cross-process locking unnecessary (gateway runs single-process event loop per architecture constraint).

### Resolved by Kai (2026-07-07, post-research grey-area acceptance)

The v10.0 design suite has internal discrepancies between REQUIREMENTS.md (PoC scope, newer) and `02-ROUND-TABLE-PROTOCOL.md §5` (locked earlier). Kai resolved:

1. **7 MCP tool names — REQUIREMENTS.md list is authoritative for v11.0 PoC.** Implement exactly: `round_table_open`, `submit_round_table_result`, `get_agent_opinion`, `agents_list`, `agent_describe`, `memory_retrieve_scoped`, `memory_submit_record`. This list intentionally diverges from `02-ROUND-TABLE-PROTOCOL.md §5` (which lists `get_agent_persona` / `get_agent_memory` / `submit_artifact` / `query_memory` / `run_python_phase` and defers `round_table_open` to v11.1+). SC#2/SC#3 require `round_table_open` to be callable, so it MUST be implemented in Phase 52. The §5.0 deferral comment is stale (predates `05-POC-PLAN.md` §3.3 which mandates `round_table_open`).

2. **State machine enum — `round-table-state-schema.yaml` is authoritative for the wire format.** Use exactly: `open | completed | aborted | stalled` (with `stalled → open` resume and `stalled → aborted` paths). The informal `open → in_progress → closed` in INFRA-03 / CONTEXT.md / REQUIREMENTS.md is shorthand only; **DO NOT** serialize `in_progress` or `closed` to state JSON. SC#2 "interrupted submit doesn't leave status: in_progress" — that test must check that no state file has `status: in_progress` because that value is not in the schema enum.

3. **Memory tools ship as stubs in Phase 52.** `memory_retrieve_scoped` returns `{"status": "phase53_not_implemented", "hits": []}`. `memory_submit_record` returns `{"status": "phase53_not_implemented", "record_id": null}`. Phase 53 (CREATIVE-SLICE) fills in real mem0 backend routing. The `_scoped_agent_id` `contextvars.ContextVar` primitive is built in Phase 52 (per `01-AGENT-REGISTRY-SCHEMA.md` §5.5) and used by Phase 53.

### Implementation-level open questions (Claude's discretion)

1. **JSON file per round table vs append-only JSONL vs SQLite for state persistence** — design doc says "JSON file at `.runtime/{slug}/round_tables/{round_id}.json`" so this is locked; Claude's discretion is only on the temp-file + atomic-rename mechanics (use existing `atomic_json_write`).
2. **Crash recovery implementation strategy** — design doc enumerates 3 failure modes; Claude chooses between (a) write-ahead journal, (b) snapshot+atomic-rename, (c) SQLite WAL. Recommend (b) — minimal new code, leverages `atomic_json_write`, sufficient for 3 documented failure modes.
3. **Schema validation eager vs lazy** — Claude's discretion. Recommend eager (validate at registry load time) so invalid YAMLs fail fast.
4. **Async lock granularity** — Per-`roundId` lock (per design doc §5.2) is mandatory. Claude may add per-agent locks if needed for memory access serialization.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `utils.py:87` `atomic_replace(src, dst)` — atomic file swap, symlink-safe (resolves before rename).
- `utils.py:121` `atomic_json_write(path, data)` — temp+fsync+os.replace JSON writer; never leaves partial file.
- `utils.py:190` `atomic_yaml_write(path, data)` — same pattern for YAML.
- `mcp_serve.py:450` `create_mcp_server(event_bridge)` — entry point. Extends with `@mcp.tool()` decorators inside.
- `mcp_serve.py:471-831` 9 existing messaging tools — pattern reference for the 7 new round table tools.
- `agent/curator.py` — existing background-review module; Phase 45 §5 `_memory_evolution_phase` contract extends this. Phase 54 bias canary will extend further.
- `plugins/memory/mem0/` — mem0 backend plugin; per-agent memory extension target (Phase 53).
- `jsonschema` (pinned in pyproject.toml) — `Draft202012Validator` for Phase 45 schema validation.

### Established Patterns

- **Self-registration via decorator** — `tools/registry.py` `registry.register(...)` pattern at module import time. Round table tools register via `@mcp.tool()` decorator inside `create_mcp_server()`.
- **Atomic writes** — every persistence site uses `atomic_*_write` helpers. State machine MUST follow this for crash recovery.
- **Lazy plugin discovery** — providers/platforms discovered on first use. Agent registry can follow same pattern (load on first `agents_list` call, cache).
- **Pydantic for transport schemas** — used across agent/transports/*; MCP tool schemas can use simple dataclasses or Pydantic models.
- **`from __future__ import annotations`** — required at top of new modules per CLAUDE.md.
- **`encoding="utf-8"`** mandatory on every `open()` (Ruff PLW1514).
- **Tests in `tests/agent/test_*.py`** — pytest with `tmp_path` fixture for filesystem isolation.

### Integration Points

- `mcp_serve.py` — the 7 new MCP tools register here, following existing `@mcp.tool()` form. Output goes through `FastMCP` stdio transport to MCP clients (CC, Cursor, etc.).
- `agent/` package — new modules live alongside `curator.py`, `context_compressor.py`. No circular imports (avoid top-level `run_agent` imports per architecture constraint).
- `~/.hermes/agents/` — registry YAML source directory (read at registry load time).
- `~/.hermes/.runtime/{slug}/round_tables/` — per-project state file directory. Created on first `round_table_open`.
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` — serial constraint policy citation (must appear in serial-violation error message per SC#4).

</code_context>

<specifics>
## Specific Ideas

No specific requirements — pure infrastructure phase. Implementation choices deferred to Claude's discretion per design suite + codebase patterns.

The success criteria (SC#1-4 in ROADMAP) are the authoritative acceptance contract:

- **SC#1:** User places YAML at `~/.hermes/agents/{name}.agent.yaml` → `agents_list` MCP tool returns it. Malformed YAML → rejected by Phase 45 schema with specific schema-violation error.
- **SC#2:** Round trip `round_table_open` → 1 `get_agent_opinion` → `submit_round_table_result` against single synthetic agent completes end-to-end. Lifecycle is atomic (interrupted submit doesn't leave `status: in_progress`).
- **SC#3:** `round_table_open` invocation that crashes mid-turn (3 failure modes: partial-write, mid-turn crash, orphaned session) recovers on next access — state machine transitions cleanly to `closed` or `error` without operator hand-intervention.
- **SC#4:** Concurrent second `get_agent_opinion` submission against same `roundId` is **rejected** with clear serial-violation error (cites `feedback-glm-overload-reduce-concurrency.md`); single sequential submission proceeds and returns panelist opinion successfully.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Allotment of MIGR-01 (9 sample agent YAMLs) deferred to Phase 53 (creative slice precondition). Per-agent memory benchmark + production traffic deferred to v12.0+ per REQUIREMENTS.md "Out of Scope".

</deferred>
