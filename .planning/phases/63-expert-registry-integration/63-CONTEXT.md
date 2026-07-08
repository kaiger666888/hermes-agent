# Phase 63: EXPERT-REGISTRY-INTEGRATION - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — borderline infrastructure with one runtime SC)

<domain>
## Phase Boundary

Phase 62 shipped 12 new agent YAMLs at `~/.hermes/agents/` (21 total). Phase 63 verifies the v11.0 `agent.registry_loader` ingests all 21 without errors, adds missing-expert alarm logic (new code), and runs an end-to-end `open_round_table` smoke with `visual_executor` as panelist (the most complex agent — sub_steps [drawer, animator] expressed in persona text per Phase 62 Pitfall #2).

**In scope:**
1. Verify `load_agent_registry()` (agent/registry_loader.py:278) loads 21 agents with zero errors
2. NEW: Add missing-expert alarm — emits warning when a "required" expert_id is absent from `~/.hermes/agents/`
3. NEW: Canary test for missing-expert alarm (temporarily rename a YAML, observe warning emitted)
4. Run `open_round_table` MCP tool with `visual_executor` as panelist, verify non-empty synthesis output

**Strictly out of scope:**
- `hermes orchestrator status` CLI command (Phase 68)
- Round table metrics / observability (Phase 67)
- Agent YAML schema changes (Phase 62 locked schema)
- visual_executor persona rewrites (Phase 62 shipped)

</domain>

<decisions>
## Implementation Decisions

### Locked-from-prior-phases

- **Registry loader API:** `agent.registry_loader.load_agent_registry(*, force_reload: bool = False) -> list[dict[str, Any]]` (line 278) — existing v11.0 API, do not change signature
- **Validation pattern:** `yaml.safe_load` + `jsonschema.Draft202012Validator` (Phase 62 SC#2 enforcement)
- **`open_round_table` API:** exists at `agent/round_table_state.py:302` — Phase 63 reuses, does not modify
- **visual_executor agent:** sub_steps in persona text (Phase 62 Pitfall #2); agent loads as a single YAML entity (not multi-YAML composition)
- **Round table executor:** `agent/round_table_executor.py` (existing v11.0); serial execution invariant (INFRA-04 — NOT lifted in v13.0)
- **GLM endpoint:** Live available per MEMORY.md `feedback-glm-5-2-only.md` — visual_executor smoke can hit real GLM

### Claude's Discretion

The following grey areas are at Claude's discretion — plan-phase research + planner judgment should drive final decisions:

**G1: "Required" expert_id set definition**
SC#2 requires missing-expert alarm to fire when a "known-required" expert is absent. What defines "required"?
- **Option A:** Hard-coded list of 15 active DAG expert_ids (per v10.0 design assumption)
- **Option B:** Config-driven (e.g., `cli-config.yaml: required_experts: [...]`)
- **Option C:** Derive from `related_agents` graph closure (any agent referenced by another agent's `related_agents` is "required")
- Recommendation: Option A (simplest; matches v10.0 design literal text); revisit in Phase 68 if operator needs override

**G2: Alarm emission channel**
Where does the missing-expert warning surface?
- **Option A:** `logger.warning()` only (visible in `~/.hermes/logs/agent.log`)
- **Option B:** Return structured `(agents, warnings)` tuple from `load_agent_registry` (callers decide)
- **Option C:** Both — log + structured return for downstream observability (Phase 67)
- Recommendation: Option C (sets up Phase 67 OBSRV-01 collector without doing it now)

**G3: Smoke test depth for SC#3**
`visual_executor` is the most complex agent. How deep does the smoke go?
- **Option A (minimal):** 1-turn round table with visual_executor as sole panelist, synthesize a 1-paragraph response to "describe a scene"
- **Option B (sub_steps):** 2-turn round table — first turn invokes drawer sub_step, second invokes animator sub_step (exercises the sub_steps-in-persona pattern)
- **Option C (full):** Multi-turn round table with visual_executor + 2 other agents (cinematographer + scene_builder), simulate Step 7 of the pipeline
- Recommendation: Option A — minimal viable smoke; Phase 64+ does deeper integration. Matches "non-empty synthesis output" SC#3 literal text.

**G4: Canary test location**
SC#2 canary temporarily renames a YAML. Where does this test live?
- **Option A:** `tests/agent/test_registry_loader.py` — unit-level pytest fixture
- **Option B:** `tests/integration/test_missing_expert_alarm.py` — separate integration test file
- **Option C:** Inline bash script in 63-VALIDATION.md (no pytest)
- Recommendation: Option A — co-located with existing registry loader tests (if any) or creates new file

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`agent/registry_loader.py:278`** — `load_agent_registry()` existing function (Phase 52 v11.0). Phase 63 extends with missing-expert alarm; do NOT change signature.
- **`agent/registry_loader.py:209-269`** — validation function pattern (per 62-PATTERNS.md)
- **`agent/round_table_state.py:302`** — `open_round_table()` existing function. Phase 63 uses it, does not modify.
- **`agent/round_table_executor.py`** — round table execution engine (v11.0). Phase 63 invokes, does not modify.
- **`/home/kai/.hermes/agents/visual_executor.agent.yaml`** — Phase 62 deliverable, target agent for smoke
- **`/home/kai/.hermes/agents/{20 others}.agent.yaml`** — full 21-agent registry (Phase 62 deliverable)

### Established Patterns

- **Logger pattern:** `logger.warning("...: %s", exc)` lazy %-formatting (CLAUDE.md)
- **Specific exceptions:** `RegistryValidationError` (existing in registry_loader.py)
- **Test isolation:** conftest.py redirects `HERMES_HOME` per-test — Phase 63 tests must respect this (use `get_hermes_home()` not `Path.home() / ".hermes"`)
- **pytest discovery:** `tests/agent/test_*.py` (per CLAUDE.md "Test files" convention)

### Integration Points

- **MCP tool layer:** `open_round_table` is one of 7 MCP tools registered by v11.0. Phase 63 smoke invokes via direct Python call (`agent.round_table_state.open_round_table(...)`) rather than MCP layer (keeps smoke deterministic).
- **Round table state file:** JSON at `~/.hermes/round_tables/{session_id}.json` — smoke verifies "non-empty synthesis" field
- **GLM provider:** Live endpoint available; visual_executor's `tools: [hermes_llm, hermes_llm_vision, dreamina_cli, ...]` whitelist routes through GLM
- **Phase 67 future collector:** Missing-expert alarm structured return (G2 Option C) is the input Phase 67 OBSRV-01 will consume

</code_context>

<specifics>
## Specific Ideas

-visual_executor smoke may need a fixture prompt — suggested: `"Given the screenplay scene 'INT. COFFEE SHOP - DAY (first meeting)', describe how you would execute shot 1 visually."` — exercises persona-declared drawer + animator sub_steps + dreamina CLI capability declaration without requiring actual image generation (synthesis-only).

- Canary test for SC#2: use `pytest` fixture with `tmp_path` + `monkeypatch` HERMES_HOME; copy 21 YAMLs to tmp_path, rename one, verify warning fires. Do NOT touch real `~/.hermes/agents/` in test.

- Phase 63 should NOT touch the 21 shipped YAMLs (Phase 62 lineage invariants). All testing via fixtures or direct registry invocation.

</specifics>

<deferred>
## Deferred Ideas

- **Async round table concurrency (INFRA-04 lift)** — deferred to v14+ pending Phase 64 EVAL-03 data
- **`hermes orchestrator status` CLI** — Phase 68 (OBSRV-04)
- **Round table metrics collection** — Phase 67 (OBSRV-02)
- **Multi-agent round table smoke (curtain call)** — Phase 64+ integration scope
- **visual_executor + dreamina_cli live image generation** — out of scope (synthesis text only; real image gen is operator-action-handoff)

</deferred>
