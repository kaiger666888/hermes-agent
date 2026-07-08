# Phase 63: EXPERT-REGISTRY-INTEGRATION - Research

**Researched:** 2026-07-08
**Domain:** Agent registry validation + round-table lifecycle integration (Python, pytest, existing v11.0 runtime)
**Confidence:** HIGH

## Summary

Phase 63 is a **borderline infrastructure phase** with one pure-code SC (21-agent load + missing-expert alarm) and one runtime SC (visual_executor round-table smoke). The existing v11.0 runtime (`agent/registry_loader.py`, `agent/round_table_state.py`, `agent/round_table_executor.py`, `mcp_serve.py`) already implements 95% of the machinery — Phase 63's contribution is (a) adding a missing-expert alarm layer to `load_agent_registry`, (b) a canary test proving the alarm fires, and (c) a round-table smoke proving the most complex agent (visual_executor with sub_steps [drawer, animator] expressed in persona text) produces non-empty synthesis.

All 21 agent YAMLs are confirmed present at `/home/kai/.hermes/agents/*.agent.yaml` [VERIFIED: filesystem probe 2026-07-08]. The registry loader at `agent/registry_loader.py:278` (`load_agent_registry`) currently returns `list[dict]` with no alarm logic — it silently returns `[]` if the agents dir is missing, and raises `RegistryValidationError` only on per-YAML schema violations. There is **no existing "required expert" concept** [VERIFIED: `grep "missing.*expert\|required.*expert" agent/registry_loader.py` returns 0 hits] — Phase 63 introduces this.

The round-table smoke for SC#3 has a critical determinism decision: the existing `tests/agent/test_run_screenplay_step3.py` pattern **mocks `auxiliary_client.call_llm`** to keep tests hermetic (no `GLM_API_KEY` dependency). The hybrid recommendation (mock-by-default + opt-in live flag) preserves this discipline while still offering a real-GLM path for manual operator validation.

**Primary recommendation:** Implement G1=Option A (hard-coded 15-expert required set), G2=Option C (structured return + logger.warning), G3=Option A (minimal 1-turn smoke), G4=Option A (co-located pytest). Use mock-by-default for the smoke with an opt-in `HERMES_PHASE63_LIVE_SMOKE=1` env flag for real GLM validation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (from CONTEXT.md ## decisions / locked-from-prior-phases)

- **Registry loader API signature locked:** `agent.registry_loader.load_agent_registry(*, force_reload: bool = False) -> list[dict[str, Any]]` (line 278) — existing v11.0 API. Phase 63 extends with missing-expert alarm but **MUST NOT change the positional return signature** (callers like `mcp_serve.agents_list` at line 1541 expect a list). Structured warnings (G2 Option C) must be delivered via a NEW optional parameter or attribute, not by changing the return type to a tuple.
- **Validation pattern:** `yaml.safe_load` + `jsonschema.Draft202012Validator` (Phase 62 SC#2 enforcement — already in `load_one_agent_yaml` at line 209).
- **`open_round_table` API:** `agent/round_table_state.py:302` — Phase 63 reuses, does NOT modify. Signature: `open_round_table(state_dir, round_id, project_id, question, panelist_agent_ids, caller, *, token_budget=None) -> dict`.
- **visual_executor agent:** sub_steps `[drawer, animator]` are expressed **in persona text only** (Phase 62 Pitfall #2; schema `additionalProperties: false` forbids a top-level `sub_steps` field). Agent loads as a single YAML entity. Confirmed in `/home/kai/.hermes/agents/visual_executor.agent.yaml` lines 6-15.
- **Round table executor:** `agent/round_table_executor.py` — serial execution invariant (INFRA-04 NOT lifted in v13.0). Phase 63 MUST NOT introduce parallelism.
- **GLM endpoint:** Live available per MEMORY.md `feedback-glm-5-2-only.md`. visual_executor smoke CAN hit real GLM but does not HAVE to (determinism trade-off is a Claude discretion item — see G3 resolution below).
- **Phase 62 lineage invariants:** Phase 63 MUST NOT touch the 21 shipped YAMLs. All testing via fixtures or direct registry invocation on the real `~/.hermes/agents/`.

### Claude's Discretion (4 grey areas — G1-G4)

**G1: "Required" expert_id set definition** — see `## Recommended Grey-Area Resolutions` below.

**G2: Alarm emission channel** — see `## Recommended Grey-Area Resolutions` below.

**G3: Smoke test depth for SC#3** — see `## Recommended Grey-Area Resolutions` below.

**G4: Canary test location** — see `## Recommended Grey-Area Resolutions` below.

### Deferred Ideas (OUT OF SCOPE)

- **Async round table concurrency (INFRA-04 lift)** — deferred to v14+ pending Phase 64 EVAL-03 data.
- **`hermes orchestrator status` CLI** — Phase 68 (OBSRV-04).
- **Round table metrics collection** — Phase 67 (OBSRV-02).
- **Multi-agent round table smoke (curtain call)** — Phase 64+ integration scope.
- **visual_executor + dreamina_cli live image generation** — out of scope (synthesis text only; real image gen is operator-action-handoff).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXPERT-04 | Agent registry 启动时加载 21 agents(9 已 ship + 12 新增)无 schema/lifecycle 错误,missing-expert 告警逻辑就绪 | `load_agent_registry` (line 278) already loads + validates; SC#1 "21 agents loaded" verified via `agents_list` MCP tool `count` field. **NEW CODE:** missing-expert alarm layer + canary test (G1+G2+G4 resolutions). |
| EXPERT-05 | 至少 1 个新 agent(选 `visual_executor` —— 最复杂,带 sub_steps)通过 7 MCP tools 中的 `open_round_table` 实际调用并产生非空响应 | `open_round_table` (line 302) + `get_agent_opinion` (mcp_serve.py:688) + `submit_round_table_result` (round_table_state.py:553) form the 3-step lifecycle. **NEW TEST:** round-table smoke invoking visual_executor as panelist (G3 resolution for depth + determinism). |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Extracted actionable directives that Phase 63 MUST honor:

- **Encoding:** Every `open()` MUST pass `encoding="utf-8"` (Ruff `PLW1514` blocks merge). Existing `registry_loader.py` already compliant (lines 127, 226).
- **HERMES_HOME:** Use `get_hermes_home()` from `hermes_constants`, NEVER `Path.home() / ".hermes"`. Existing `registry_loader.py:305` + `round_table_state.py:239` compliant.
- **Logger pattern:** Lazy %-formatting — `logger.warning("...: %s", exc)`, NEVER f-strings in log calls. Existing code compliant.
- **Exception handling:** `except X as exc:` with bound name + `raise ... from exc` for chain preservation. Existing `registry_loader.py:136, 231` compliant.
- **Naming:** `snake_case` for functions/locals, `PascalCase` for classes. New alarm class (if any) follows this.
- **Test files:** `tests/agent/test_<module>.py` — canary test at `tests/agent/test_registry_loader.py` (G4 Option A) matches this convention.
- **from __future__ import annotations:** At top of new/modified modules for PEP 604 unions on Python 3.11+.
- **Test isolation:** `tests/conftest.py:_hermetic_environment` (autouse) redirects `HERMES_HOME` to `tmp_path / "hermes_test"` per-test (line 354). Phase 63 tests MUST stage fixtures into the redirected home, never touch real `~/.hermes/agents/`.
- **Live-system guard:** `tests/conftest.py:_live_system_guard` (autouse at line 538) AST-inspects tests for `os.kill` / `subprocess.run`. Round-table smoke that calls `open_round_table` directly (sync, no subprocess) is safe; if the guard trips, mark `@pytest.mark.live_system_guard_bypass`.
- **Credential env-var filter:** `conftest.py` unsets all `*_API_KEY` env vars per-test (line 57-73, including `GLM_API_KEY` at line 95). **This is why the round-table smoke MUST mock `auxiliary_client.call_llm`** — the live GLM key is stripped in test mode by design.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agent YAML discovery + schema validation | API / Backend (`agent/registry_loader.py`) | — | Pure-Python stdlib + `yaml` + `jsonschema`; no I/O beyond local filesystem under `HERMES_HOME`. |
| Missing-expert alarm (NEW) | API / Backend (`agent/registry_loader.py`) | Observability (Phase 67 collector) | Alarm is derived from registry content; structured return feeds Phase 67 `OBSRV-01` health collector. Logger surfaces to `~/.hermes/logs/agent.log` immediately. |
| Round-table state machine | API / Backend (`agent/round_table_state.py`) | Filesystem (`~/.hermes/agents/.runtime/`) | Atomic JSON writes via `utils.atomic_json_write`; state files are the crash-recovery substrate. |
| Round-table serial enforcement | API / Backend (`agent/round_table_executor.py`) | — | Per-`roundId` `asyncio.Lock` registry; INFRA-04 invariant. |
| Round-table MCP surface | API / Backend (`mcp_serve.py`) | — | 7 MCP tools (`round_table_open`, `get_agent_opinion`, `submit_round_table_result`, etc.) — the CC-facing protocol layer. |
| GLM LLM dispatch (smoke) | External (GLM endpoint) | API / Backend (`agent/auxiliary_client.py`) | `call_llm(task="round_table_opinion", provider="glm")`; mocked in hermetic tests, live in manual smoke. |
| Test fixtures + canary | Test tier (`tests/agent/`) | — | pytest + `tmp_path` + `monkeypatch` per `conftest.py` hermetic pattern. |

## Standard Stack

### Core (existing — Phase 63 reuses, does not install)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `jsonschema` | transitive (via v11.0 deps; `Draft202012Validator`) | Schema validation of agent YAMLs | [VERIFIED: `agent/registry_loader.py:60` import + `agents-schema.yaml` Draft 2020-12] Locked by Phase 45 schema + Phase 52 INFRA-01. |
| `PyYAML` | `6.0.3` (`pyproject.toml` pin) | `yaml.safe_load` for YAML parsing | [VERIFIED: `pyproject.toml` + `registry_loader.py:61`] Refuses arbitrary tags (T-52-01 mitigation). |
| `pytest` | `9.0.2` (`[dev]` extra) | Test framework for canary + smoke | [VERIFIED: `pyproject.toml` + existing `tests/agent/test_registry_loader.py`] Per-file subprocess parallelism via `scripts/run_tests_parallel.py`. |
| `pytest-asyncio` | `1.3.0` | `@pytest.mark.asyncio` for round-table smoke (async MCP tools) | [VERIFIED: `tests/agent/test_run_screenplay_step3.py:43-44` canonical pattern + strict mode] |

### Supporting (test-only, existing)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `monkeypatch` (pytest builtin) | — | Redirect `HERMES_HOME`, mock `auxiliary_client.call_llm`, reset `_REGISTRY_CACHE` | Every canary + smoke test (see `## Code Examples`). |
| `tmp_path` (pytest builtin) | — | Per-test temp dir for fixture YAML staging | Canary test copies real YAMLs into redirected home, renames one, verifies alarm. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hard-coded 15-expert required list (G1 Option A) | Config-driven (G1 Option B) | Config-driven is more flexible but adds a new config key to `cli-config.yaml` + parsing logic + doc overhead. For v13.0 the 15-expert set is stable (v10.0 design §6.2 locked). Defer config-driven to Phase 68 if operator needs override. **Use Option A.** |
| Tuple return from `load_agent_registry` (G2 Option B) | Structured attribute (G2 Option C) | Changing return type `list[dict]` → `tuple[list[dict], list[str]]` breaks ALL existing callers (`mcp_serve.agents_list` line 1541, `agent_describe` line 1608). Option C (structured attribute on a new param) preserves backward compat. **Use Option C.** |

**Installation:**
```bash
# No new packages — Phase 63 uses existing pinned deps.
# Verify jsonschema + PyYAML available:
python3 -c "import jsonschema, yaml; print('jsonschema:', jsonschema.__version__, 'PyYAML:', yaml.__version__)"
```

**Version verification:** All versions verified via `pyproject.toml` exact pins (`jsonschema` transitive, `PyYAML==6.0.3`, `pytest==9.0.2`, `pytest-asyncio==1.3.0`). No new packages installed in Phase 63.

## Package Legitimacy Audit

Phase 63 installs **zero** new packages. All dependencies are existing pinned stdlib + project deps reused from v11.0/v12.0.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none — no new packages) | — | — | — | — | — | — |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck not run because Phase 63 installs zero packages — the audit is trivially satisfied.*

## Architecture Patterns

### System Architecture Diagram

```
Phase 63 data flow — two independent verification paths:

PATH A: SC#1 + SC#2 (21-agent load + missing-expert alarm)
═══════════════════════════════════════════════════════════
                    ┌─────────────────────────┐
                    │ ~/.hermes/agents/       │
                    │   *.agent.yaml × 21     │
                    └────────────┬────────────┘
                                 │ flat glob *.agent.yaml
                                 ▼
              ┌──────────────────────────────────────┐
              │ load_agent_registry()                │
              │   (agent/registry_loader.py:278)     │
              │                                      │
              │   1. yaml.safe_load each YAML        │
              │   2. Draft202012Validator each       │
              │   3. filename==name invariant        │
              │   4. [NEW] check required set        │
              │      (15-expert hard-coded list)     │
              │      → logger.warning per missing    │
              │      → append to warnings list       │
              │   return list[dict] (+ warnings via  │
              │          new optional param)         │
              └──────────────┬───────────────────────┘
                             │
              ┌──────────────┴───────────────┐
              ▼                              ▼
   ┌────────────────────┐         ┌─────────────────────┐
   │ SC#1 verification  │         │ SC#2 canary test    │
   │ (agents_list MCP   │         │ (tests/agent/       │
   │  tool → count=21)  │         │  test_registry_     │
   │                    │         │  loader.py)         │
   │                    │         │                     │
   │  Assert:           │         │  1. Copy 15 YAMLs   │
   │  count == 21       │         │     to tmp_path     │
   │  zero errors       │         │  2. Rename 1 YAML   │
   │                    │         │     (e.g.            │
   │                    │         │     screenplay→     │
   │                    │         │     screenplay.bak) │
   │                    │         │  3. load_registry   │
   │                    │         │  4. Assert warning  │
   │                    │         │     lists           │
   │                    │         │     "screenplay"    │
   └────────────────────┘         └─────────────────────┘

PATH B: SC#3 (visual_executor round-table smoke)
════════════════════════════════════════════════
          ┌───────────────────────────┐
          │ Test fixture stages:      │
          │  - visual_executor.agent  │
          │    .yaml (real, from      │
          │    ~/.hermes/agents/)     │
          │  - cinematographer.agent  │
          │    .yaml (2nd panelist —  │
          │    minItems=2 required)   │
          └─────────────┬─────────────┘
                        │
                        ▼
   ┌─────────────────────────────────────────────┐
   │ Step 1: round_table_open(                   │
   │   round_id=<test UUID>,                     │
   │   project_slug="phase63-smoke",             │
   │   question="Describe shot 1 visually...",   │
   │   panelist_agent_ids=[                      │
   │     "visual_executor",                      │
   │     "cinematographer"                       │
   │   ])                                        │
   │ → state file created, status="open"         │
   └─────────────────┬───────────────────────────┘
                     │
                     ▼
   ┌─────────────────────────────────────────────┐
   │ Step 2: get_agent_opinion(                  │
   │   round_id, project_slug,                   │
   │   agent_id="visual_executor",               │
   │   topic="Describe shot 1 visually...")      │
   │                                             │
   │  [MOCK by default]:                         │
   │   auxiliary_client.call_llm → deterministic │
   │   "[TEST MOCK] visual_executor opinion..."  │
   │  [LIVE if HERMES_PHASE63_LIVE_SMOKE=1]:     │
   │   real GLM dispatch, persona as system      │
   │   prompt                                    │
   │ → Turn appended to state file               │
   └─────────────────┬───────────────────────────┘
                     │
                     ▼
   ┌─────────────────────────────────────────────┐
   │ Step 3: submit_round_table_result(          │
   │   round_id, conclusion=<synthesis>,         │
   │   cited_memories=[], closed_by="test")      │
   │ → status="completed", submitRoundTableResult│
   │   block sealed                              │
   └─────────────────┬───────────────────────────┘
                     │
                     ▼
   ┌─────────────────────────────────────────────┐
   │ SC#3 verification:                          │
   │  - Read state file from tmp_path            │
   │  - Assert state["status"] == "completed"    │
   │  - Assert state["turns"][-1]["opinion"]     │
   │    is non-empty                             │
   │  - Assert "drawer" or "animator" appears in │
   │    opinion (sub_steps persona exercised)    │
   │    [LIVE mode only — mock returns generic]  │
   └─────────────────────────────────────────────┘
```

### Recommended Project Structure

Phase 63 adds/modifies **no new directories**. Files touched:

```
agent/
├── registry_loader.py        # MODIFY: add missing-expert alarm (SC#2)
├── round_table_state.py      # READ ONLY (existing open_round_table)
└── round_table_executor.py   # READ ONLY (existing serial lock)

mcp_serve.py                  # READ ONLY (existing round_table_open MCP tool)

tests/agent/
├── test_registry_loader.py   # MODIFY: add TestMissingExpertAlarm class (SC#2 canary)
├── test_mcp_serve_round_table.py  # READ ONLY (existing lifecycle pattern reference)
└── test_phase63_round_table_smoke.py  # NEW: SC#3 visual_executor round-table smoke
```

### Pattern 1: Missing-Expert Alarm (SC#2 — new code in registry_loader.py)

**What:** After loading all YAMLs, compare the set of loaded `name`s against a hard-coded required set (15 active DAG experts from v10.0 §6.2). For each required expert absent from the registry, emit `logger.warning` + append to a structured warnings list.

**When to use:** Every `load_agent_registry()` call. The check is cheap (set difference on ≤21 names).

**Example:**
```python
# Source: v10.0 design 01-AGENT-REGISTRY-SCHEMA.md §6.2 + 02-ROUND-TABLE-PROTOCOL.md §1.5
# The 15 active DAG experts — verbatim from v10.0 §6.2 transform table.
REQUIRED_DAG_EXPERTS: frozenset[str] = frozenset({
    "hook_retention", "creative_source", "screenplay", "script_auditor",
    "character_designer", "cinematographer", "style_genome", "prompt_injector",
    "visual_executor", "continuity_auditor", "audio_pipeline", "editor",
    "colorist", "compliance_gate", "theory_critic",
})
"""15 active DAG expert IDs that MUST be present in the registry.

Source: v10.0 design doc 01-AGENT-REGISTRY-SCHEMA.md §6.2 (verbatim from
ARCHITECTURE §2 lines 128-144). The other 6 agents in the 21-agent
registry (animation_studio, documentary_maker, performer, production,
scene_builder, storyboard_designer) are supporting/non-DAG and are NOT
required — their absence is not an alarm condition.
"""


def _check_required_experts(
    loaded_names: set[str],
) -> list[str]:
    """Return the list of required experts missing from ``loaded_names``.

    Pure function — no side effects. Caller decides whether to log, raise,
    or surface via structured return. Keeping this isolated makes it
    trivially testable (canary test calls this directly with a controlled
    input set).
    """
    return sorted(REQUIRED_DAG_EXPERTS - loaded_names)
```

The integration into `load_agent_registry` preserves backward compat (return type stays `list[dict]`):

```python
# Inside load_agent_registry, after the for-loop populates `entries`:
loaded_names = {e["name"] for e in entries}
missing = _check_required_experts(loaded_names)
for name in missing:
    logger.warning(
        "registry_loader: required expert %r missing from %s "
        "(loaded %d agents, expected %d required DAG experts)",
        name,
        agents_dir,
        len(entries),
        len(REQUIRED_DAG_EXPERTS),
    )
# G2 Option C: structured warnings available via a new sibling function
# (does NOT change load_agent_registry return signature).
```

### Pattern 2: Round-Table Smoke via Direct Python Call (SC#3)

**What:** Invoke the 3-step round-table lifecycle (`open_round_table` → `get_agent_opinion` → `submit_round_table_result`) directly from Python, bypassing the MCP stdio layer. This keeps the smoke deterministic and debuggable.

**When to use:** SC#3 smoke test. The MCP layer adds JSON serialization + stdio transport overhead with no additional validation value — the closures in `mcp_serve.py` are thin wrappers around the same `agent.round_table_state` functions.

**Example:**
```python
# Source: tests/agent/test_run_screenplay_step3.py:108-119 (_open_round helper) +
# tests/agent/test_mcp_serve_round_table.py:55-121 (mcp_server fixture with mocked call_llm)
# Canonical pattern — Phase 63 smoke follows this exactly with visual_executor.

@pytest.mark.asyncio
async def test_visual_executor_round_table_smoke(monkeypatch, tmp_path):
    """SC#3: visual_executor produces non-empty opinion via round table."""
    # 1. Stage real visual_executor + cinematographer YAMLs into redirected HERMES_HOME
    _seed_agent_yamls(tmp_path)  # copies 2 real YAMLs

    # 2. Mock auxiliary_client.call_llm (hermetic — conftest strips GLM_API_KEY)
    _mock_call_llm(monkeypatch)

    # 3. Open round table (direct Python call, NOT MCP stdio)
    from agent.round_table_state import open_round_table, submit_round_table_result
    state_dir = get_hermes_home() / "agents" / ".runtime" / "phase63-smoke" / "round_tables"
    state = open_round_table(
        state_dir=state_dir,
        round_id=_test_uuid(),
        project_id="phase63-smoke",
        question="Describe how you would execute shot 1 visually.",
        panelist_agent_ids=["visual_executor", "cinematographer"],
        caller="test_phase63_smoke",
    )

    # 4. get_agent_opinion (async — MCP tool lifted to module level in Phase 53)
    from mcp_serve import get_agent_opinion
    raw = await get_agent_opinion(
        round_id=state["roundId"],
        project_slug="phase63-smoke",
        agent_id="visual_executor",
        topic="Describe how you would execute shot 1 visually.",
    )
    result = json.loads(raw)
    assert "error" not in result, f"opinion call failed: {result}"

    # 5. Submit + verify non-empty synthesis
    final = submit_round_table_result(
        state_path=state_dir / f"{state['roundId']}.json",
        conclusion="[TEST] visual_executor + cinematographer synthesis",
        cited_memories=[],
        closed_by="test_phase63_smoke",
    )
    assert final["status"] == "completed"

    # 6. Read state file, assert non-empty opinion in turns
    state_file = state_dir / f"{state['roundId']}.json"
    turns = json.loads(state_file.read_text(encoding="utf-8"))["turns"]
    assert len(turns) >= 1
    assert turns[-1]["opinion"], "opinion must be non-empty string"
```

### Anti-Patterns to Avoid

- **Changing `load_agent_registry` return type to a tuple** (G2 Option B). Breaks every caller. Use a sibling function or optional param instead.
- **Touching the 21 real YAMLs in canary test.** Canary MUST copy YAMLs to `tmp_path` first, then rename in the temp dir. The `_hermetic_environment` autouse fixture already redirects `HERMES_HOME` — leverage it.
- **Hitting live GLM in the default smoke test.** `conftest.py:95` strips `GLM_API_KEY` per-test. The smoke MUST mock `auxiliary_client.call_llm` by default; live mode is opt-in via `HERMES_PHASE63_LIVE_SMOKE=1` (set explicitly by operator, not in conftest).
- **Introducing parallelism in the round-table smoke.** INFRA-04 serial constraint NOT lifted. The smoke calls `get_agent_opinion` sequentially, never `asyncio.gather`.
- **Using `Path.home() / ".hermes"` in new code.** Use `get_hermes_home()` — conftest redirects it per-test; `Path.home()` bypasses the redirect and leaks into real `~/.hermes`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Round-table lifecycle (open → turn → submit) | Custom state machine | `agent.round_table_state.open_round_table` (line 302) + `append_turn` (line 417) + `submit_round_table_result` (line 553) | Already shipped in v11.0 with atomic writes, crash recovery, idempotency, schema-valid state files. Rebuilding would lose the `utils.atomic_json_write` partial-write safety. |
| Serial execution enforcement | Custom lock/semaphore | `agent.round_table_executor.acquire_round_or_reject` (line 110) | Per-`roundId` `asyncio.Lock` with CR-02 fix (check-and-acquire atomicity). Hand-rolling reintroduces the CR-02 race. |
| Agent YAML schema validation | Custom field checker | `jsonschema.Draft202012Validator` against `agents-schema.yaml` | Locked by Phase 45 schema (18 fields, `additionalProperties: false`). Already in `load_one_agent_yaml` (line 209). |
| GLM dispatch | Raw httpx call | `agent.auxiliary_client.call_llm(task="round_table_opinion", provider="glm")` | Routes through 4-key rotation + retry/backoff + error classification. Phase 53 already wired this into `get_agent_opinion` (mcp_serve.py:688). |
| Test fixture staging | Manual file copy in each test | `_seed_agent_yamls` helper + `tmp_path` + `_hermetic_environment` autouse | conftest already redirects HERMES_HOME; existing `tests/agent/test_registry_loader.py:114` (`_copy_fixture`) shows the pattern. |
| Test-isolated state-file cleanup | Manual `os.remove` | `tmp_path` auto-cleanup (pytest builtin) | conftest's `tmp_path` is destroyed after test; no cleanup code needed. |

**Key insight:** Phase 63 is a **thin integration layer** over existing v11.0 machinery. The hardest part (round-table state machine, serial locks, schema validation) is done. The new code is ~40 lines (alarm function + integration into `load_agent_registry`) + ~120 lines of tests. Do not rebuild what exists.

## Runtime State Inventory

> Phase 63 is an integration + test phase, not a rename/refactor/migration. However, it interacts with runtime state (agent YAMLs + round-table state files), so a targeted inventory applies.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | None — mem0 memories are NOT touched by Phase 63 (round-table smoke uses `cited_memories=[]`). | None |
| **Live service config** | 21 agent YAMLs at `/home/kai/.hermes/agents/*.agent.yaml` (Phase 62 deliverable, confirmed present 2026-07-08). | Canary test copies these to `tmp_path`; does NOT mutate the originals. |
| **OS-registered state** | None — no systemd units, cron jobs, or Task Scheduler entries touched. | None |
| **Secrets/env vars** | `GLM_API_KEY` — stripped by `conftest.py:95` in test mode. Live smoke (opt-in via `HERMES_PHASE63_LIVE_SMOKE=1`) requires operator to set `GLM_API_KEY` explicitly outside the test fixture. | None for default test path; document live-mode key requirement in VALIDATION.md. |
| **Build artifacts** | None — Phase 63 adds Python source + test files only; no compiled artifacts, no `egg-info` changes. | None |

**Nothing found requiring migration.** Phase 63 is additive (new alarm code + new tests) with zero mutation of existing shipped artifacts.

## Common Pitfalls

### Pitfall 1: Breaking `load_agent_registry` callers with a tuple return

**What goes wrong:** Implementing G2 as `return (entries, warnings)` changes the return type. Every `for agent in load_agent_registry():` loop now iterates the tuple, not the list. `mcp_serve.agents_list` (line 1541) silently returns wrong data; `agent_describe` (line 1608) breaks.
**Why it happens:** G2 Option B reads as "return structured tuple" which seems clean in isolation.
**How to avoid:** G2 Option C — keep `load_agent_registry` returning `list[dict]`; expose warnings via a NEW sibling function `load_agent_registry_with_warnings()` returning `tuple[list[dict], list[str]]`, OR add an optional `out_warnings: list[str] | None = None` parameter that callers can pass to collect warnings. The MCP `agents_list` tool stays unchanged; Phase 67 OBSRV-01 collector calls the new sibling function.
**Warning signs:** CI fails on `test_agents_list_returns_json` or `test_agent_describe` after the alarm lands.

### Pitfall 2: Canary test touching real `~/.hermes/agents/`

**What goes wrong:** The canary renames `screenplay.agent.yaml` to `screenplay.agent.yaml.bak` in the REAL home dir to trigger the alarm. If the test crashes before renaming back, the real registry is left with 20 agents — breaking subsequent phases and live runtime.
**Why it happens:** The test author forgets that `_hermetic_environment` already redirects HERMES_HOME, and writes to `Path.home() / ".hermes"` instead of `get_hermes_home() / "agents"`.
**How to avoid:** Canary copies the 15 required YAMLs into `get_hermes_home() / "agents"` (the redirected temp dir), then renames ONE in the temp dir. The real `/home/kai/.hermes/agents/` is never touched. Use the `_copy_fixture` helper pattern from `tests/agent/test_registry_loader.py:114`.
**Warning signs:** `ls /home/kai/.hermes/agents/*.agent.yaml | wc -l` returns 20 after running the canary test.

### Pitfall 3: Smoke test failing in CI due to missing `GLM_API_KEY`

**What goes wrong:** The smoke calls `auxiliary_client.call_llm` without mocking. In CI, `conftest.py:95` strips `GLM_API_KEY`. The call fails with auth error, SC#3 goes red, Phase 63 cannot verify.
**Why it happens:** Author copies the smoke from a live script that had the key set, without adding the mock.
**How to avoid:** Default smoke path mocks `auxiliary_client.call_llm` (pattern from `tests/agent/test_mcp_serve_round_table.py:88-117`). Add an opt-in live mode: `if os.environ.get("HERMES_PHASE63_LIVE_SMOKE"): skip mock`. Document the live mode in VALIDATION.md as operator-only.
**Warning signs:** CI log shows `GLM_API_KEY not set` or `401 Unauthorized` from `*.bigmodel.cn`.

### Pitfall 4: Round-table smoke requiring minItems=2 but only staging 1 agent

**What goes wrong:** SC#3 focuses on visual_executor, so the author stages only that one YAML. But `open_round_table` enforces `minItems=2` for `panelist_agent_ids` (mcp_serve.py:524, schema `$defs.PanelistSnapshot`). The open call returns `panelists_min_2_required` 400 error.
**Why it happens:** The schema constraint is in `round-table-state-schema.yaml`, not obvious from the `open_round_table` signature alone.
**How to avoid:** Stage 2 agent YAMLs (visual_executor + cinematographer — they're real collaborators per `related_agents`). Pass `panelist_agent_ids=["visual_executor", "cinematographer"]`. Only call `get_agent_opinion` for `visual_executor` (SC#3 only requires one agent's non-empty response).
**Warning signs:** `open_round_table` returns `{"error": "panelists_min_2_required", "status": 400}`.

### Pitfall 5: Alarm firing for the 6 non-DAG agents

**What goes wrong:** The required set is defined as "all 21 agents" instead of "15 active DAG experts". When animation_studio/documentary_maker/performer/production/scene_builder/storyboard_designer are (correctly) absent or renamed, the alarm fires — but these are NOT DAG-critical agents, so the alarm is noise.
**Why it happens:** Author conflates "21 agents loaded" (SC#1 count) with "15 required experts" (SC#2 alarm set). They're different concepts.
**How to avoid:** G1 Option A — hard-code the 15-expert set from v10.0 §6.2 (the `REQUIRED_DAG_EXPERTS` frozenset in Pattern 1 above). The other 6 are loaded-but-not-required. SC#1 verifies count==21 (all present); SC#2 verifies the 15 required subset is present (alarm fires if any of the 15 is missing).
**Warning signs:** Canary renames `storyboard_designer.agent.yaml` and the alarm does NOT fire (correct behavior) — but the test ASSERTS it should fire (wrong test expectation).

### Pitfall 6: Registry cache poisoning across canary + smoke tests

**What goes wrong:** `load_agent_registry` caches at module level (`_REGISTRY_CACHE`, line 274). Test A loads 15 YAMLs (canary setup). Test B (smoke) loads 2 YAMLs. Test B sees Test A's cached 15-entry list because the cache wasn't reset.
**Why it happens:** Within a single test file, ordering matters (per `conftest.py:39-49`). The cache survives across tests in the same file.
**How to avoid:** Call `_reset_registry_cache()` at the start of each test (pattern from `tests/agent/test_registry_loader.py:127-138`). The canary and smoke live in DIFFERENT test files (per-file process isolation), so cross-file leakage is impossible — but within-file ordering still requires explicit resets.
**Warning signs:** Test passes alone but fails when run with `pytest tests/agent/test_registry_loader.py` (file-level run).

## Code Examples

### Example 1: Canary test fixture (SC#2 — missing-expert alarm)

```python
# Source: tests/agent/test_registry_loader.py:114-138 (_copy_fixture + _reset_registry_cache)
# + tests/conftest.py:327-360 (_hermetic_environment HERMES_HOME redirection)
# Canonical pattern — Phase 63 canary follows this exactly.

class TestMissingExpertAlarm:
    """SC#2: missing-expert alarm fires when a required DAG expert is absent."""

    def test_alarm_fires_when_screenplay_missing(self):
        """Rename screenplay.agent.yaml → alarm lists 'screenplay' as missing."""
        _reset_registry_cache()
        # Stage all 15 required DAG experts EXCEPT screenplay
        _stage_required_experts(exclude={"screenplay"})

        from agent.registry_loader import load_agent_registry
        entries = load_agent_registry()

        # Verify the alarm pathway captured the missing expert
        # (via logger.warning capture or structured sibling function)
        assert "screenplay" in _captured_warnings()

    def test_alarm_silent_when_all_15_present(self):
        """With all 15 required experts loaded, no missing-expert warnings."""
        _reset_registry_cache()
        _stage_required_experts(exclude=set())  # all 15

        from agent.registry_loader import load_agent_registry
        load_agent_registry()

        assert _captured_warnings() == []
```

### Example 2: Capturing logger.warning in pytest (caplog fixture)

```python
# Source: pytest docs — caplog is the canonical log-capture fixture.
# Phase 63 uses this to assert the missing-expert warning was emitted.

import logging

def test_alarm_emits_logger_warning(caplog):
    """The missing-expert alarm surfaces via logger.warning (G2 Option C)."""
    _reset_registry_cache()
    _stage_required_experts(exclude={"visual_executor"})

    with caplog.at_level(logging.WARNING, logger="agent.registry_loader"):
        from agent.registry_loader import load_agent_registry
        load_agent_registry()

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("visual_executor" in msg and "missing" in msg.lower() for msg in warning_msgs), (
        f"expected missing-expert warning for visual_executor, got: {warning_msgs}"
    )
```

### Example 3: Mocking auxiliary_client.call_llm (SC#3 hermetic smoke)

```python
# Source: tests/agent/test_mcp_serve_round_table.py:88-117 (canonical mock pattern)
# Phase 63 smoke reuses this verbatim — conftest strips GLM_API_KEY so the mock
# is mandatory for hermetic test execution.

def _mock_call_llm(monkeypatch):
    """Replace auxiliary_client.call_llm with a deterministic stub."""
    from agent import auxiliary_client

    def _fake_call_llm(*args, **kwargs):
        agent_id = kwargs.get("agent_id", "unknown")
        return type(
            "FakeResponse",
            (),
            {
                "content": f"[TEST MOCK] {agent_id} opinion on shot 1: use drawer "
                           f"sub_step for FLUX 2 first_frame, then animator for veo3.1.",
                "choices": [
                    type("FakeChoice", (), {
                        "message": type("FakeMsg", (), {
                            "content": f"[TEST MOCK] {agent_id} opinion"
                        })(),
                        "finish_reason": "stop",
                    })
                ],
                "usage": {"total_tokens": 42},
            },
        )()

    monkeypatch.setattr(auxiliary_client, "call_llm", _fake_call_llm)
```

### Example 4: Opt-in live GLM mode (operator manual validation)

```python
# Source: MEMORY.md feedback-glm-5-2-only.md (GLM endpoint live)
# + conftest.py:95 (GLM_API_KEY stripped per-test)
# Operator sets HERMES_PHASE63_LIVE_SMOKE=1 + GLM_API_KEY manually outside pytest.

import os

@pytest.mark.asyncio
async def test_visual_executor_smoke(self, monkeypatch, tmp_path):
    """SC#3: visual_executor round-table smoke (mock by default, live opt-in)."""
    _seed_agent_yamls(tmp_path)

    # Default: mock (hermetic). Live: only if operator explicitly opts in.
    if not os.environ.get("HERMES_PHASE63_LIVE_SMOKE"):
        _mock_call_llm(monkeypatch)
    # else: real GLM dispatch — requires GLM_API_KEY set by operator.

    # ... rest of round-table lifecycle (open → opinion → submit → assert)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 52 `get_agent_opinion` returned `"[phase52_placeholder]"` | Phase 53 replaced with real `auxiliary_client.call_llm(task="round_table_opinion", provider="glm")` dispatch | Phase 53 (v11.0 PoC, shipped 2026-07-07) | Phase 63 smoke reuses the Phase 53 real-dispatch path (mocked in test, live in manual mode). No need to re-implement LLM dispatch. |
| Registry loader returned `list[dict]` with no alarm | Phase 63 adds `_check_required_experts` + logger.warning | This phase | First introduction of "required expert" concept. Phase 67 OBSRV-01 collector will consume the structured warnings. |
| Phase 62 VALIDATION.md used inline `python3 -c` (no pytest) | Phase 63 uses pytest (canary + smoke need fixtures + mocks) | This phase | Phase 62 was pure transform (YAML-only validation); Phase 63 is integration (needs Python runtime + mocked GLM). Different validation strategy justified by SC type. |

**Deprecated/outdated:**
- `ARCHITECTURE.md §4.2` old MCP tool naming (`agent_get_persona`, `agent_recall`, etc.) — superseded by STACK §3.2 no-prefix form (`get_agent_persona`, `get_agent_opinion`). Phase 63 smoke uses the current names (`round_table_open`, `get_agent_opinion`, `submit_round_table_result`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The 15-expert required set (G1 Option A) matches v10.0 design §6.2 verbatim. | G1 Resolution, Pattern 1 | If the 15-set is wrong (e.g., v10.0 was updated post-ship), the alarm fires for wrong agents. Mitigation: the set is `frozenset` in source code with a docstring citing §6.2 — trivially auditable. |
| A2 | `auxiliary_client.call_llm(task="round_table_opinion", provider="glm")` is the correct dispatch signature for `get_agent_opinion`. | Code Examples Example 3 | If Phase 53 changed the signature, the mock breaks. Verified via `mcp_serve.py:688-700` comment + `test_run_screenplay_step3.py` pattern (both cite this exact signature). |
| A3 | `tests/agent/test_mcp_serve_round_table.py` mock pattern (monkeypatch `auxiliary_client.call_llm`) is still valid in v13.0. | Code Examples Example 3 | If auxiliary_client was refactored, the mock target changes. Verified: `grep "auxiliary_client" agent/auxiliary_client.py` confirms module exists; `mcp_serve.py:688` imports it lazily. |
| A4 | The 6 non-DAG agents (animation_studio, documentary_maker, performer, production, scene_builder, storyboard_designer) are NOT in the required set. | G1 Resolution | If any of these 6 IS actually DAG-critical, the alarm silently misses its absence. Mitigation: v10.0 §6.2 explicitly lists 15 experts; the 6 extras are Phase 62 additions from the 12-expert transform that includes supporting roles. Low risk — operator can extend the set in Phase 68 if needed. |
| A5 | `conftest.py:95` strips `GLM_API_KEY` per-test, making live GLM impossible in default test path. | Pitfall 3, Code Examples Example 4 | If conftest was changed to NOT strip GLM_API_KEY, the default smoke could accidentally hit live GLM (flaky, costs money). Verified: `_CREDENTIAL_NAMES` frozenset at line 76 includes `GLM_API_KEY`. |

**All assumptions are LOW risk** — each is verified against current codebase state (2026-07-08) and carries a clear mitigation path.

## Open Questions

1. **Should the 6 non-DAG agents be in a "soft required" tier?**
   - What we know: They're loaded (SC#1 count=21 includes them) but not in the 15-expert DAG required set (G1 Option A).
   - What's unclear: If one of them is missing, should the alarm fire at a lower severity (INFO vs WARNING)?
   - Recommendation: v13.0 = no. The 15-expert set is the load-bearing DAG; the other 6 are supporting. If Phase 68 operator dashboard wants a softer "advisory" tier, it can derive from the same registry data. Keep Phase 63 alarm binary (required missing = WARNING; everything else = silent).

2. **Should the live smoke (HERMES_PHASE63_LIVE_SMOKE=1) be documented as an operator-action-handoff?**
   - What we know: The mock path is hermetic and deterministic. The live path requires `GLM_API_KEY` + real GLM endpoint.
   - What's unclear: Does this count as one of the "3 operator-action handoffs" tracked in milestone audit?
   - Recommendation: No — the live smoke is a developer/operator convenience, not a deferred verification. The mock path fully satisfies SC#3. Document in VALIDATION.md under "Manual-Only Verifications" but do not count as a handoff.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `~/.hermes/agents/*.agent.yaml` (21 files) | SC#1 (21-agent load), SC#2 (canary fixture source), SC#3 (visual_executor YAML) | ✓ | Phase 62 shipped 2026-07-08 | — |
| `.planning/research/v10-orchestrator-design/agents-schema.yaml` | SC#1 schema validation (already wired in `load_one_agent_yaml`) | ✓ | Phase 45 stable | — |
| Python 3.11+ | All code | ✓ | 3.13 (per `pyproject.toml` tool.ty pin) | — |
| `jsonschema` + `PyYAML` | YAML parsing + schema validation | ✓ | transitive via v11.0 deps | — |
| `pytest` + `pytest-asyncio` | Canary + smoke tests | ✓ | 9.0.2 / 1.3.0 (`[dev]` extra) | — |
| GLM endpoint (live) | SC#3 live-mode smoke (opt-in) | ✓ (per MEMORY.md `feedback-glm-5-2-only.md`) | — | Mock path (default) — no GLM needed |
| `GLM_API_KEY` | SC#3 live-mode smoke (opt-in) | ✗ in test (stripped by conftest:95); ✓ if operator sets explicitly | — | Mock path (default) |

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** `GLM_API_KEY` — stripped in test mode by design; mock path covers default SC#3 verification. Live mode is operator-opt-in for manual deeper validation.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest==9.0.2` + `pytest-asyncio==1.3.0` (`[dev]` extra) |
| Config file | `pyproject.toml` (existing — `addopts` at line 261, 30s per-test timeout) |
| Quick run command | `python -m pytest tests/agent/test_registry_loader.py -x` |
| Full suite command | `python -m pytest tests/agent/test_registry_loader.py tests/agent/test_phase63_round_table_smoke.py -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXPERT-04 (SC#1) | 21 agents load with zero schema/lifecycle errors | integration | `python3 -c "from agent.registry_loader import load_agent_registry; r=load_agent_registry(); assert len(r)==21, f'expected 21, got {len(r)}'"` | ✅ (inline command — no pytest file needed; uses real `~/.hermes/agents/`) |
| EXPERT-04 (SC#2 canary) | Missing-expert alarm fires when screenplay YAML renamed | unit | `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm::test_alarm_fires_when_screenplay_missing -x` | ❌ Wave 0 (new test class) |
| EXPERT-04 (SC#2 silent) | Alarm silent when all 15 required experts present | unit | `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm::test_alarm_silent_when_all_15_present -x` | ❌ Wave 0 |
| EXPERT-05 (SC#3 smoke) | visual_executor produces non-empty opinion via round table | integration | `python -m pytest tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_round_table_produces_nonempty_opinion -x` | ❌ Wave 0 (new test file) |
| EXPERT-05 (SC#3 live) | [OPTIONAL] visual_executor live GLM synthesis | manual-only | `HERMES_PHASE63_LIVE_SMOKE=1 GLM_API_KEY=... python -m pytest tests/agent/test_phase63_round_table_smoke.py -x` | ❌ Wave 0 (same file, opt-in via env) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/agent/test_registry_loader.py -x` (alarm tests are fast — <2s)
- **Per wave merge:** `python -m pytest tests/agent/test_registry_loader.py tests/agent/test_phase63_round_table_smoke.py -x` (full Phase 63 suite)
- **Phase gate:** Full suite green + inline SC#1 command (21-agent count against real `~/.hermes/agents/`) before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/agent/test_registry_loader.py` — add `TestMissingExpertAlarm` class (2 tests: fires + silent) + `_stage_required_experts` helper
- [ ] `tests/agent/test_phase63_round_table_smoke.py` — new file, `TestVisualExecutorSmoke` class (1 mock test + 1 opt-in live test)
- [ ] `agent/registry_loader.py` — add `REQUIRED_DAG_EXPERTS` frozenset + `_check_required_experts` function + integration into `load_agent_registry`
- [ ] No framework install needed — `pytest` + `pytest-asyncio` already in `[dev]` extra

## Security Domain

> `security_enforcement` is not explicitly set in `.planning/config.json` — treated as enabled per protocol default.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Phase 63 does not handle user auth. GLM API key auth is handled by `auxiliary_client` (existing). |
| V3 Session Management | no | Round-table state files are keyed by UUID `round_id` (CC-generated), not session tokens. |
| V4 Access Control | no | No new access boundaries; tests run under existing pytest process isolation. |
| V5 Input Validation | yes | Agent YAML validation via `jsonschema.Draft202012Validator` (`additionalProperties: false` — rejects undeclared fields). Already in `load_one_agent_yaml:245`. Canary test verifies this continues to work. |
| V6 Cryptography | no | No crypto operations in Phase 63. (`persona_sha256` exists in schema but is not computed/verified by Phase 63 code.) |

### Known Threat Patterns for Agent Registry + Round Table

| Pattern | STRIDE | Standard Mitigation (existing, Phase 63 preserves) |
|---------|--------|-----------------------------------------------------|
| YAML tag injection (arbitrary Python object instantiation) | Tampering | `yaml.safe_load` (not `yaml.load`) — refuses arbitrary tags (T-52-01, `registry_loader.py:227`). |
| Undeclared field injection in agent YAML | Tampering | `additionalProperties: false` in `agents-schema.yaml` + `Draft202012Validator` (T-52-04, `registry_loader.py:245-257`). |
| Filename ↔ name mismatch (spoofing) | Spoofing | `load_one_agent_yaml:261-267` verifies `data["name"] == filename.stem` (T-52-03). |
| Path traversal via `round_id` / `project_slug` | Tampering | `validate_round_id` + `validate_project_slug` reject `..` / separators (`round_table_state.py:145-177`, T-52-09). |
| Concurrent round-table turn (INFRA-04 DoS amplification) | Denial of Service | `acquire_round_or_reject` per-`roundId` `asyncio.Lock`, 429 on contention (`round_table_executor.py:110`, CR-02 fix). |
| Partial-write corruption of state file | Tampering | `utils.atomic_json_write` (temp + fsync + `os.replace`) + read-time recovery (`round_table_state.py:691-810`). |

**Phase 63 introduces NO new threat surface.** The missing-expert alarm is read-only (set difference on already-loaded data); the round-table smoke reuses the existing validated lifecycle.

## Recommended Grey-Area Resolutions (G1-G4)

### G1: "Required" expert_id set definition → **Option A (hard-coded 15-expert frozenset)**

**Rationale:**
- v10.0 design doc `01-AGENT-REGISTRY-SCHEMA.md §6.2` locks the 15 active DAG experts verbatim from ARCHITECTURE §2. This is the canonical "required" set — it's been reviewed, audited (SC#5 in Phase 45), and is stable since 2026-07-06.
- The 21-agent registry = 15 DAG experts + 6 supporting (animation_studio, documentary_maker, performer, production, scene_builder, storyboard_designer). Only the 15 are load-bearing for the collaboration DAG (`related_agents` graph closure).
- Option B (config-driven) adds a config key + parsing logic + doc overhead for no v13.0 benefit — the set hasn't changed since v10.0 design. Defer to Phase 68 if operator needs per-deployment override.
- Option C (graph closure from `related_agents`) is computationally elegant but fragile — a single typo in one YAML's `related_agents` list silently drops an expert from the required set. Hard-coded is auditable.

**Implementation:** See Pattern 1 above — `REQUIRED_DAG_EXPERTS` frozenset with docstring citing §6.2.

**Risk if wrong:** LOW. The set is a module-level constant with a docstring; changing it in Phase 68 is a one-line edit.

### G2: Alarm emission channel → **Option C (logger.warning + structured sibling function)**

**Rationale:**
- Option A alone (logger.warning only) is insufficient — Phase 67 OBSRV-01 collector needs structured data, not log scraping.
- Option B alone (tuple return) breaks every existing caller of `load_agent_registry` (`mcp_serve.agents_list` line 1541, `agent_describe` line 1608 — both do `for agent in load_agent_registry():` and would iterate the tuple).
- Option C gives both: logger.warning for immediate operator visibility (`~/.hermes/logs/agent.log`), AND a structured sibling function `load_agent_registry_with_warnings() -> tuple[list[dict], list[str]]` for Phase 67 to consume. The existing `load_agent_registry()` signature stays `list[dict]` — zero caller breakage.

**Implementation:**
```python
def load_agent_registry(*, force_reload: bool = False) -> list[dict[str, Any]]:
    """Existing signature — UNCHANGED. Still returns list[dict]."""
    entries, _warnings = _load_with_warnings(force_reload=force_reload)
    return entries

def load_agent_registry_with_warnings(*, force_reload: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
    """NEW sibling — returns (entries, missing_expert_warnings). Phase 67 consumer."""
    return _load_with_warnings(force_reload=force_reload)

def _load_with_warnings(*, force_reload: bool) -> tuple[list[dict[str, Any]], list[str]]:
    """Shared implementation — logs warnings + returns them."""
    # ... existing load logic ...
    missing = _check_required_experts(loaded_names)
    for name in missing:
        logger.warning("registry_loader: required expert %r missing ...", name, ...)
    return entries, missing
```

### G3: Smoke test depth for SC#3 → **Option A (minimal 1-turn smoke, mock-by-default)**

**Rationale:**
- SC#3 literal text: "通过 `open_round_table` 实际调用并产生非空响应" — the bar is "non-empty synthesis output", not "full sub_steps execution".
- Option B (2-turn drawer→animator sub_step) would require either (a) live GLM to actually parse the persona's sub_step semantics (flaky, costs money, stripped in CI) or (b) a sophisticated mock that pretends to understand sub_steps (low value — it's testing the mock, not the agent).
- Option C (multi-agent curtain call) is explicitly deferred to Phase 64+.
- The minimal smoke proves: (1) visual_executor YAML loads, (2) persona is non-empty, (3) `get_agent_opinion` dispatches and appends a turn, (4) `submit_round_table_result` seals the round. That's the full lifecycle integration — sufficient for SC#3.
- The `sub_steps [drawer, animator]` pattern is already verified structurally by Phase 62 SC#2 (schema validation) + the persona text contains both keywords (Phase 62 Pitfall #2 mitigation). Phase 63 doesn't need to re-verify persona content.

**Determinism strategy (live vs mock vs hybrid):** **Hybrid — mock by default, opt-in live via env var.**
- Mock path: `auxiliary_client.call_llm` returns deterministic string. Hermetic, fast, CI-safe. This is the default.
- Live path: `HERMES_PHASE63_LIVE_SMOKE=1` env var (set by operator outside pytest) skips the mock, hits real GLM. Used for manual deeper validation.
- Why not live-only: `conftest.py:95` strips `GLM_API_KEY` per-test by design. Live-only would make SC#3 untestable in CI.
- Why not mock-only: live GLM validation is valuable for catching persona-prompt issues that a mock can't surface (e.g., persona too long, GLM refuses, etc.). The opt-in flag keeps it available without making it the default.

### G4: Canary test location → **Option A (`tests/agent/test_registry_loader.py` — co-located)**

**Rationale:**
- The existing `tests/agent/test_registry_loader.py` already has 4 test classes covering `load_agent_registry` (valid load, malformed rejection, name mismatch, caching). The canary is a natural 5th class (`TestMissingExpertAlarm`).
- Co-location means the canary runs in the same pytest file subprocess as the other registry tests — sharing the `_reset_registry_cache` helper, `_copy_fixture` helper, and `_agents_dir` helper.
- Option B (separate integration test file) fragments the registry test coverage across two files for no benefit — the canary is a unit test (stages fixtures in tmp_path, checks a function return), not a true integration test.
- Option C (inline bash in VALIDATION.md) has no fixtures, no mocking, no HERMES_HOME redirection — it would touch the real `~/.hermes/agents/`, violating the test-isolation invariant.

**Implementation:** Add `TestMissingExpertAlarm` class to existing `tests/agent/test_registry_loader.py`, reusing the existing `_reset_registry_cache` + `_agents_dir` + `_copy_fixture` helpers. The canary stages 15 required YAMLs (copied from real `~/.hermes/agents/`), renames one, and asserts the warning fires.

## Sources

### Primary (HIGH confidence)

- **Codebase probes (2026-07-08):** `agent/registry_loader.py` (full read), `agent/round_table_state.py` (full read), `agent/round_table_executor.py` (full read), `mcp_serve.py:450-700` + `1500-1620`, `tests/agent/test_registry_loader.py` (full read), `tests/agent/test_mcp_serve_round_table.py:1-180`, `tests/agent/test_run_screenplay_step3.py:1-120`, `tests/conftest.py:1-120` + `327-426`, `/home/kai/.hermes/agents/visual_executor.agent.yaml` (full read), `/home/kai/.hermes/agents/screenplay.agent.yaml` (full read).
- **v10.0 design docs:** `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` §6.2 (15-expert transform table — verbatim source for G1 required set), `02-ROUND-TABLE-PROTOCOL.md` §1.2 + §1.5 (lifecycle + serial constraint).
- **MEMORY.md:** `feedback-glm-5-2-only.md` (GLM endpoint live), `feedback-glm-overload-reduce-concurrency.md` (INFRA-04 serial constraint root cause).
- **CLAUDE.md:** Project conventions (encoding, HERMES_HOME, logger pattern, test isolation, naming).

### Secondary (MEDIUM confidence)

- **Phase 62 VALIDATION.md:** `.planning/phases/62-expert-yaml-transform/62-VALIDATION.md` — inline `python3 -c` validation pattern (Phase 62 was transform-only; Phase 63 graduates to pytest because it needs mocks + fixtures).

### Tertiary (LOW confidence)

- None — all findings verified against codebase or official v10.0 design docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all deps verified via `pyproject.toml` exact pins + existing codebase imports.
- Architecture: HIGH — existing v11.0 runtime fully read; integration points (registry_loader, round_table_state, mcp_serve) understood at line level.
- Grey-area resolutions (G1-G4): HIGH — each grounded in v10.0 design doc + existing test patterns + clear trade-off analysis.
- Pitfalls: HIGH — all 6 pitfalls derived from existing codebase patterns (conftest HERMES_HOME redirection, cache reset, GLM_API_KEY stripping, minItems=2 schema constraint) or prior-phase lessons (Phase 62 Pitfall #2 sub_steps).
- Determinism strategy: HIGH — hybrid mock/live pattern directly mirrors `tests/agent/test_mcp_serve_round_table.py:88-117` canonical mock + `HERMES_PHASE63_LIVE_SMOKE` opt-in is a standard pytest env-var pattern.

**Research date:** 2026-07-08
**Valid until:** 2026-08-07 (30 days — stable infrastructure phase, existing code unlikely to churn; re-verify if v11.0 runtime is refactored)
