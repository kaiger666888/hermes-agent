---
phase: 53-creative-slice
plan: 02
subsystem: agent-memory-arbitration
tags: [memory, arbitration, round-table, comparator-llm, conflict-log]
requires:
  - "Phase 52: agent/memory_arbitration.py _scoped_agent_id primitive"
  - "Phase 52: agent/auxiliary_client.call_llm"
  - "Phase 45: memory-record-schema.yaml (scope/confidence/evidence_chain fields)"
  - "02-ROUND-TABLE-PROTOCOL.md §3 (5-mechanism contract)"
provides:
  - "agent/memory_arbitration.py::COMPARATOR_PROMPT_TEMPLATE (verbatim §3.2)"
  - "agent/memory_arbitration.py::arbitrate_two_memories (GLM comparator LLM pass)"
  - "agent/memory_arbitration.py::apply_tie_break (Δconfidence<0.05 → deferred-to-operator)"
  - "agent/memory_arbitration.py::append_conflict_record (JSONL + fsync)"
  - "agent/memory_arbitration.py::memory_retrieve_scoped (Phase 53 mem0 routing, replaces Phase 52 stub)"
  - "agent/memory_arbitration.py::memory_submit_record (Phase 53 mem0 routing, replaces Phase 52 stub)"
affects:
  - "tests/agent/test_memory_arbitration_stub.py (Phase 52 stub-contract tests updated to Phase 53 routing-contract tests)"
  - "Phase 53-03: screenplay Step 3 round-table driver invokes arbitrate_two_memories when conflicts detected"
  - "Phase 54: curator periodic pass reads conflicts.jsonl for high-frequency-conflict detection"
tech-stack:
  added: []
  patterns:
    - "Python contextvars primitive (preserved verbatim from Phase 52)"
    - "Function-level lazy import for mem0 backend (RESEARCH Pitfall 5)"
    - "Python str.format() template with doubled-brace JSON example block"
    - "JSONL append + fsync per-line atomicity (RESEARCH Pattern 3)"
    - "Deterministic Python tie-break layer on top of LLM arbitration"
    - "Defensive json.loads with deferred-to-operator fallback (RESEARCH Pitfall 4)"
key-files:
  created:
    - agent/memory_arbitration.py
    - tests/agent/test_memory_arbitration.py
    - tests/agent/test_conflict_log_writer.py
    - tests/fixtures/memory-conflict-2conflict.json
  modified:
    - tests/agent/test_memory_arbitration_stub.py
decisions:
  - "Phase 52 stub return contract REPLACED per CONTEXT.md decision #3 (status='unavailable' when MEM0_API_KEY unset, NOT 'phase53_not_implemented')"
  - "comparator LLM uses provider='glm' explicit (MEMORY.md feedback-glm-5-2-only.md); never auto-chain to OpenRouter (RESEARCH Pitfall 6)"
  - "Tie-break is a Python deterministic layer on top of the LLM (the LLM is told the rule in prompt; Python enforces it authoritatively)"
  - "JSONL writer takes a fully-qualified Path; path-traversal defense lives at the caller (Phase 52 validate_project_slug/validate_round_id) per threat T-53-08 accept"
metrics:
  duration: 274s
  completed: 2026-07-07
  tasks: 2
  files-created: 4
  files-modified: 1
  tests-added: 14
  tests-passing: 14
---

# Phase 53 Plan 02: Memory Conflict Arbitration Runtime Summary

5-mechanism conflict arbitration runtime per `02-ROUND-TABLE-PROTOCOL.md §3` — memory annotation enrichment (via mem0 routing), GLM comparator LLM pass (verbatim §3.2 prompt), scope-precedence-aware tie-break, JSONL conflict log writer. Preserves the Phase 52 `_scoped_agent_id` ContextVar primitive verbatim.

## What Was Built

**`agent/memory_arbitration.py`** (514 lines, replaces Phase 52 stub module):

- `COMPARATOR_PROMPT_TEMPLATE` — verbatim copy of the §3.2 prompt template (lines 627-663 of `02-ROUND-TABLE-PROTOCOL.md`). Contains the 5 required substrings: opening line `"You are arbitrating a memory conflict in a Hermes round table."`, scope-precedence rule `"Apply scope precedence: session > project > global"`, Δconfidence threshold `"confidence within 0.05"`, `"evidence_operator_ids"` field name, and the full 5-value resolution enum line. Implemented as a `str.format()` template with 16 substitution fields + doubled-brace JSON example block.
- `arbitrate_two_memories(...)` — formats the prompt with the two memory records + panelist IDs + project/question, dispatches to `auxiliary_client.call_llm(task="memory_comparator", provider="glm", temperature=0.0, max_tokens=200)`, defensively `json.loads` the response (RESEARCH Pitfall 4 — malformed JSON falls back to `deferred-to-operator`, never raises), then passes through `apply_tie_break` for the deterministic Python layer.
- `apply_tie_break(...)` — when LLM returned `A-wins`/`B-wins` AND both memories are at the same scope AND Δconfidence < 0.05, overrides to `deferred-to-operator`. Different scopes pass through (scope-precedence handled by the LLM in-prompt).
- `append_conflict_record(path, record)` — JSONL append + `flush()` + `os.fsync()` + explicit `encoding="utf-8"` (CLAUDE.md PLW1514). Parent dirs created with `mkdir(parents=True, exist_ok=True)`.
- `memory_retrieve_scoped(...)` / `memory_submit_record(...)` — Phase 52 stubs REPLACED with lazy mem0 backend routing (function-level import per RESEARCH Pitfall 5). When `MEM0_API_KEY` unset or backend `is_available()` returns False, return `{"status": "unavailable", ...}` (graceful degradation, never raise). Honor `_scoped_agent_id` ContextVar for namespace routing when set; fall back to explicit `agent_id` parameter otherwise. Layered defense on the read path (T-53-06): re-filter `agent_id` matches after mem0 returns hits.
- `_default_comparator_llm(...)` — thin wrapper that calls `auxiliary_client.call_llm` with the locked GLM-only config. Test-injectable via `comparator_llm=` parameter on `arbitrate_two_memories`.
- `_UNSET` / `_SCOPED_AGENT_ID` / `set_scoped_agent_id` / `get_scoped_agent_id` — **Phase 52 contract preserved verbatim** (no character changes; docstring updated to remove "Phase 53 fills in" phrasing since Phase 53 has now landed).

**`tests/agent/test_memory_arbitration.py`** (252 lines, 8 tests):

1. `test_comparator_prompt_template_verbatim` — asserts all 5 §3.2 substrings present.
2. `test_arbitrate_two_memories_session_over_global` — injected mock LLM; assert spy called once with formatted prompt; result is LLM-driven.
3. `test_call_llm_uses_memory_comparator_task` — spies on `auxiliary_client.call_llm`; asserts `task="memory_comparator"`, `provider="glm"`, `temperature=0.0`, `max_tokens=200`.
4. `test_arbitrate_handles_malformed_llm_json` — mock returns `"I think A wins..."` (not JSON); assert fallback to `deferred-to-operator` with `"malformed JSON"` rationale; never raises.
5. `test_apply_tie_break_forces_deferral` — same-scope (project/project) with Δconfidence=0.03; assert override to `deferred-to-operator` with `Δconfidence` and `< 0.05` in rationale.
6. `test_apply_tie_break_no_tie_passes_through` — same-scope with Δconfidence=0.3; assert LLM resolution preserved unchanged.
7. `test_2conflict_scenario_end_to_end` — loads `memory-conflict-2conflict.json` fixture; both pairs arbitrate; both records appended to temp JSONL; both lines `json.loads` cleanly; expected resolutions match.
8. `test_phase52_scoped_agent_id_primitive_unchanged` — set/get round-trip + None clear + `_SCOPED_AGENT_ID` / `_UNSET` symbols present.

**`tests/agent/test_conflict_log_writer.py`** (112 lines, 6 tests):

1. `test_append_creates_file_with_parents` — deep path `/x/y/z/round_abc/conflicts.jsonl`; file + parent dirs created.
2. `test_append_writes_one_jsonl_line_per_record` — append 3 records; verify exactly 3 lines, each parses.
3. `test_append_is_atomic_per_line` — 2 appends back-to-back; both lines self-contained JSON.
4. `test_record_preserves_unicode_and_non_ascii` — record with `"中文字符 — Δconfidence < 0.05"`; verify raw file bytes contain the literal characters (no `\uXXXX` escape corruption).
5. `test_path_convention_under_hermes_home` — redirect `HERMES_HOME`; caller constructs `get_hermes_home() / "agents" / ".runtime" / "volvo-2026" / "round_tables" / "round-xyz" / "conflicts.jsonl"`; file lands at that path.
6. `test_fsync_called` — `monkeypatch.setattr` `os.fsync`; assert called exactly once per append.

**`tests/fixtures/memory-conflict-2conflict.json`** (63 lines): 2-conflict scenario — `session_vs_global` (expected `A-wins`) and `same_scope_tie` (expected `deferred-to-operator`). Both memory records include all required schema fields (`record_id`, `content`, `scope`, `confidence`, `evidence_chain`, `evidence_operator_ids`, `agent_id`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking test inconsistency] Updated Phase 52 stub-contract tests to match Phase 53 routing-contract**
- **Found during:** Task 1 GREEN phase
- **Issue:** `tests/agent/test_memory_arbitration_stub.py::TestMemoryStubReturnContract` asserted the OLD `{"status": "phase53_not_implemented", ...}` payload. Plan 53-02's success criteria #3 explicitly REPLACES that contract — the new code returns `{"status": "unavailable", ...}` when `MEM0_API_KEY` is unset (the hermetic-test invariant). Tests could not pass without updates.
- **Fix:** Updated `TestMemoryStubReturnContract` → `TestMemoryRoutingReturnContract`. New assertions check `status in ("ok", "unavailable")` and the dict shape. Updated the file docstring to reflect the Phase 53 contract replacement per CONTEXT.md decision #3.
- **Files modified:** `tests/agent/test_memory_arbitration_stub.py`
- **Commit:** dcc24b391

**2. [Rule 3 - Blocking test invariant conflict] Updated `TestNoEagerMem0Import` AST guard for Phase 53 lazy-import design**
- **Found during:** Task 1 GREEN phase
- **Issue:** The Phase 52 AST guard walked the entire module tree and flagged ANY `plugins.memory.mem0` import. Phase 53 intentionally adds a **function-level** lazy import inside `_get_mem0_backend` per the plan's explicit instruction ("real routing attempts to import `plugins.memory.mem0` lazily inside the function body (NOT at module top — RESEARCH.md 'Don't Hand-Roll' warning)"). The original test failed.
- **Fix:** Updated the AST guard to inspect only `tree.body` (top-level statements) rather than `ast.walk(tree)`. Imports nested inside `FunctionDef` / `AsyncFunctionDef` are now correctly permitted. Preserved the original RESEARCH Pitfall 5 guarantee — no top-level eager import.
- **Files modified:** `tests/agent/test_memory_arbitration_stub.py`
- **Commit:** dcc24b391

### Deferred Issues

None.

## Verification

```
$ python3 -m pytest tests/agent/test_memory_arbitration.py tests/agent/test_conflict_log_writer.py -v
============================== 14 passed in 0.44s ==============================

$ python3 -c "from agent.memory_arbitration import COMPARATOR_PROMPT_TEMPLATE as P; assert 'session > project > global' in P and 'deferred-to-operator' in P and 'evidence_operator_ids' in P; print('comparator prompt OK')"
comparator prompt OK

$ python3 -c "from agent.memory_arbitration import _SCOPED_AGENT_ID, set_scoped_agent_id, get_scoped_agent_id; set_scoped_agent_id('test'); assert get_scoped_agent_id() == 'test'; set_scoped_agent_id(None); assert get_scoped_agent_id() is None; print('Phase 52 primitive intact')"
Phase 52 primitive intact
```

## Phase 52 Contract Preservation

Verified: `_UNSET` sentinel, `_SCOPED_AGENT_ID` `ContextVar`, `set_scoped_agent_id`, `get_scoped_agent_id` are byte-identical to the Phase 52 implementation (only the docstring at the top of the primitive block was updated to remove "Phase 53 fills in" language now that Phase 53 has landed). `tests/agent/test_memory_arbitration_stub.py::TestScopedAgentId` (5 tests including asyncio task-isolation) all pass unchanged.

## Threat Model Mitigation Coverage

| Threat | Mitigation Status |
|--------|-------------------|
| T-53-05 (Tampering via malformed JSON) | Implemented: `_parse_llm_json` falls back to `deferred-to-operator` on `JSONDecodeError` (Test 4). |
| T-53-06 (Info Disclosure via wrong-namespace records) | Implemented: `memory_retrieve_scoped` re-filters hits by `agent_id` after mem0 returns (layered defense). |
| T-53-07 (DoS via comparator timeout) | Implemented: outer `try/except Exception` in `arbitrate_two_memories` catches dispatch failures, falls back to `deferred-to-operator`. |
| T-53-08 (Path traversal via manipulated path) | Accepted per plan: writer trusts caller-constructed path; defense at the boundary in Phase 52 `validate_project_slug`/`validate_round_id`. |
| T-53-09 (Spoofing via non-GLM provider) | Implemented: `_default_comparator_llm` passes `provider="glm"` explicitly (MEMORY.md feedback-glm-5-2-only.md). |
| T-53-SC (supply chain) | N/A — no new packages installed. |

## Self-Check: PASSED

- [x] `agent/memory_arbitration.py` exists (514 lines ≥ 350 minimum)
- [x] `tests/agent/test_memory_arbitration.py` exists (252 lines ≥ 200 minimum)
- [x] `tests/agent/test_conflict_log_writer.py` exists (112 lines ≥ 80 minimum)
- [x] `tests/fixtures/memory-conflict-2conflict.json` exists (2 scenarios)
- [x] Commit `dcc24b391` exists in `git log`
- [x] Commit `6bd0e4b01` exists in `git log`
- [x] All 14 plan-specified tests pass
- [x] `COMPARATOR_PROMPT_TEMPLATE` contains all 5 required §3.2 substrings
- [x] `_scoped_agent_id` / `set_scoped_agent_id` / `get_scoped_agent_id` preserved verbatim

## Known Stubs

None. All functions have real implementations per the plan spec; the mem0 routing functions degrade gracefully to `{"status": "unavailable", ...}` when `MEM0_API_KEY` is unset, which is the documented Phase 53 behavior (CONTEXT.md decision #3 — graceful degradation, NOT a stub).
