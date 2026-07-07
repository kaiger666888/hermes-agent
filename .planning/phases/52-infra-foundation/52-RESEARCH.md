# Phase 52: INFRA-FOUNDATION — Research

**Researched:** 2026-07-07
**Domain:** Hermes-side runtime layer for v11.0 PoC expert-agents system (agent registry YAML loader + 7 MCP tools + round-table state machine + serial-execution lock)
**Confidence:** MEDIUM (HIGH on codebase patterns; MEDIUM on v10.0 design suite interpretations due to naming discrepancies — see Open Questions #1 and #2)

## Summary

Phase 52 is a pure-infrastructure phase that builds 4 deliverables on top of the existing Hermes runtime: (1) an agent registry YAML loader that validates `~/.hermes/agents/*.agent.yaml` against Phase 45's `agents-schema.yaml`; (2) 7 MCP tools wired into `mcp_serve.py` following the existing `@mcp.tool()` decorator pattern; (3) a per-project `.runtime/{slug}/round_tables/{round_id}.json` state machine with atomic-write crash recovery; (4) a per-`roundId` async lock enforcing the hard serial-execution constraint.

The implementation is well-served by existing codebase patterns. `utils.atomic_json_write` (utils.py:111) provides crash-safe rename-on-write out of the box — no new persistence primitive is needed. `gateway/session_context.py` provides the canonical `contextvars.ContextVar` pattern for task-scoped state (referenced by ARCHITECTURE §3.3 `_scoped_agent_id`). `mcp_serve.py:450 create_mcp_server` is the single wire-up point — the 7 new tools follow the same `@mcp.tool()` form as the 9 existing messaging tools (lines 471-831). `agent/turn_retry_state.py` shows the dataclass-as-state-machine idiom that round-table state should follow. `tests/conftest.py:_hermetic_environment` already redirects `HERMES_HOME` per-test, so registry/state tests get filesystem isolation for free.

**Primary recommendation:** Build 4 new modules under `agent/` (`registry_loader.py`, `round_table_state.py`, `round_table_executor.py`, `memory_arbitration.py` — the latter two are minimal stubs consumed by Phase 53) and wire the 7 MCP tools into `mcp_serve.py` via thin closures that delegate to those modules. Before writing any tool code, **resolve the two naming discrepancies** documented in Open Questions #1 and #2 — they change which doc is authoritative for tool names and state values.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Claude's Discretion

1. **JSON file per round table vs append-only JSONL vs SQLite for state persistence** — design doc says "JSON file at `.runtime/{slug}/round_tables/{round_id}.json`" so this is locked; Claude's discretion is only on the temp-file + atomic-rename mechanics (use existing `atomic_json_write`).
2. **Crash recovery implementation strategy** — design doc enumerates 3 failure modes; Claude chooses between (a) write-ahead journal, (b) snapshot+atomic-rename, (c) SQLite WAL. Recommend (b) — minimal new code, leverages `atomic_json_write`, sufficient for 3 documented failure modes.
3. **Schema validation eager vs lazy** — Claude's discretion. Recommend eager (validate at registry load time) so invalid YAMLs fail fast.
4. **Async lock granularity** — Per-`roundId` lock (per design doc §5.2) is mandatory. Claude may add per-agent locks if needed for memory access serialization.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. Allotment of MIGR-01 (9 sample agent YAMLs) deferred to Phase 53 (creative slice precondition). Per-agent memory benchmark + production traffic deferred to v12.0+ per REQUIREMENTS.md "Out of Scope".
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | Agent Registry YAML Loader — load + validate `~/.hermes/agents/*.agent.yaml` per Phase 45 `agents-schema.yaml` (18 fields, JSON Schema Draft 2020-12, camelCase keywords). Rejected on schema violation; lineage fields populated for sample agents. | `## Don't Hand-Roll` (jsonschema Draft202012Validator); `## Code Examples §YAML Loader Pattern`; existing skill_utils.parse_frontmatter pattern (agent/skill_utils.py) |
| INFRA-02 | 7 MCP Tools Wire-up in mcp_serve.py — extend with 7 MCP tools per Phase 46 §5 contract (STACK §3.2 form, no prefix): `round_table_open` / `submit_round_table_result` / `get_agent_opinion` / `agents_list` / `agent_describe` / `memory_retrieve_scoped` / `memory_submit_record` | `## Code Examples §MCP Tool Registration Pattern` (mcp_serve.py:450 + 471-831); **Open Question #1** — tool-name list must be reconciled with v10.0 design suite before implementation |
| INFRA-03 | Round Table State Persistence + Crash Recovery — per-project state path `.runtime/{slug}/round_tables/` (ARCHITECTURE §5.1). State machine: `open` → `in_progress` → `closed` (atomic transitions). Crash recovery for 3 failure modes. Cross-project reference forbidden. | `## Code Examples §Atomic State Persistence Pattern`; `## Common Pitfalls §Partial-Write Detection`; existing `agent/turn_retry_state.py` dataclass state pattern; **Open Question #2** — state enum values must be reconciled with `round-table-state-schema.yaml` |
| INFRA-04 | Serial Execution Enforcement — hard constraint: 1 panelist 1 turn sequential `await`. References MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (global concurrency==1 by design). GLM 4-key rotation compatible. | `## Code Examples §Per-roundId Async Lock Pattern`; `agent/glm_concurrency_guard.py` (threading.Semaphore precedent); existing `gateway/session_context.py` (contextvars.ContextVar pattern) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Python 3.11+** (target `requires-python = ">=3.11"` in pyproject.toml). Use `from __future__ import annotations` at top of every new module for PEP 604 / PEP 585 support.
- **Ruff PLW1514** — every `open()` MUST pass `encoding="utf-8"` explicitly. This is the only load-bearing lint rule; CI blocks on it.
- **snake_case** naming for all modules (`registry_loader.py`), functions (`load_agent_registry`), locals, module-level constants (`_REGISTRY_CACHE`). `PascalCase` for classes (`AgentRegistryEntry`, `RoundTableState`). Module-private singletons prefixed `_`.
- **Circular import constraint** — `agent/*` modules MUST NOT top-level-import `run_agent`. Use the `_ra()` lazy indirection pattern (`agent/conversation_loop.py:111`) if a `run_agent` symbol is needed.
- **Type hints required** on public functions and `__init__` signatures.
- **No bare `except:`** — catch specific types or `except Exception:` with bound name (`except X as exc:`) and log the exception.
- **Lazy %-formatting** in log calls — `logger.warning("Failed: %s", exc)`, never f-strings.
- **`Path.home() / ".hermes"` is FORBIDDEN in production code** — use `hermes_constants.get_hermes_home()` instead. (tests/conftest.py fixture redirects HERMES_HOME per-test.)
- **Hermes-core scope** — this phase touches `agent/*`, `mcp_serve.py`, `tests/agent/*`. No gateway/platform changes.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agent YAML discovery + schema validation | API / Backend (Hermes runtime) | — | Loader runs in-process at MCP-server startup; no client-side concern |
| 7 MCP tool wire-up | API / Backend (`mcp_serve.py` FastMCP) | Browser/Client (CC consumes via stdio MCP) | Tools register server-side; CC invokes them via the MCP stdio transport |
| Round-table state persistence | Database / Storage (filesystem `.runtime/{slug}/`) | API / Backend (atomic_json_write helper) | State files are per-project on disk; atomic rename guarantees crash-safety |
| Crash recovery | Database / Storage | API / Backend | Detection + recovery runs at read time inside the state module (single-process) |
| Serial execution enforcement | API / Backend (asyncio.Lock per roundId) | — | Gateway runs single-process event loop; cross-process locking unnecessary |
| Per-agent memory scoping (Phase 53) | API / Backend (contextvars `_scoped_agent_id`) | Database / Storage (mem0 backend) | Phase 52 wires the contextvars primitive; mem0 routing comes in Phase 53 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `jsonschema` | 4.26.0 (uv.lock) [VERIFIED: uv.lock] | Validate agent YAML against Phase 45 `agents-schema.yaml` (Draft 2020-12) | Already a transitive dependency; `Draft202012Validator` is the draft-2020-12 entry point [CITED: json-schema.org/draft/2020-12/schema] |
| `PyYAML` | 6.0.3 (pyproject.toml) [VERIFIED: pyproject.toml] | Parse `.agent.yaml` frontmatter + body | Already pinned; same library `agent/skill_utils.parse_frontmatter` uses |
| `mcp` (FastMCP) | 1.26.0 (pyproject.toml) [VERIFIED: pyproject.toml] | `@mcp.tool()` decorator for 7 new tools | Already pinned; existing 9 messaging tools use this exact form |
| `pydantic` | 2.13.4 (pyproject.toml) [VERIFIED: pyproject.toml] | Optional — typed result models for tool return values | Already pinned; agents-schema and round-table-state-schema are JSON Schema (not Pydantic), but Pydantic models can wrap tool I/O |
| Python stdlib `asyncio` | 3.11+ | `asyncio.Lock` for per-`roundId` serial enforcement inside FastMCP's event loop | stdlib — no install; FastMCP tools can be `async def` |
| Python stdlib `contextvars` | 3.11+ | `_scoped_agent_id` for task-local memory scoping (Phase 53 prep, primitive built in Phase 52) | stdlib; canonical pattern at `gateway/session_context.py:39` [VERIFIED: codebase grep] |
| Python stdlib `hashlib` | 3.11+ | SHA-256 chaining for evolution_log + persona_sha256 | stdlib; existing pattern at `agent/curator_audit.py` [VERIFIED: codebase grep] |
| Python stdlib `uuid` | 3.11+ | UUID v4 generation for `roundId` (CC-supplied per OQ-11, but Hermes validates format) | stdlib |
| Python stdlib `pathlib` | 3.11+ | Path manipulation for `.runtime/{slug}/round_tables/` | stdlib |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ruamel.yaml` | 0.18.17 (pyproject.toml) [VERIFIED: pyproject.toml] | Round-trip-safe YAML if Phase 52 needs to mutate evolution_log entries | Only if registry_loader writes to agent YAML (curator does that — Phase 52 likely read-only) |
| `pytest` | 9.0.2 (pyproject.toml) [VERIFIED: pyproject.toml] | Test framework | All unit tests for the 4 deliverables |
| `pytest-asyncio` | 1.3.0 (pyproject.toml) [VERIFIED: pyproject.toml] | Async test support for `asyncio.Lock` concurrency tests (INFRA-04 SC#4) | SC#4 specifically requires testing concurrent `get_agent_opinion` rejection |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `jsonschema` for YAML validation | Pydantic models generated from JSON Schema | Pydantic gives better error messages but loses the `agents-schema.yaml` file as the single source of truth. Stick with `jsonschema` — design suite says "JSON Schema Draft 2020-12" explicitly. |
| `asyncio.Lock` per-roundId | `threading.Lock` per-roundId | FastMCP runs tools inside its asyncio event loop — `asyncio.Lock` is the correct primitive for in-event-loop serialization. `threading.Semaphore` is the right choice for blocking SDK calls (as `glm_concurrency_guard.py` does), but Phase 52 MCP tools are non-blocking state mutations. |
| Filesystem JSON for state | SQLite WAL | SQLite adds a binary dep + a connection-management lifecycle. Design doc locks "JSON file at `.runtime/{slug}/round_tables/{round_id}.json`" — switching to SQLite would re-litigate a locked decision. |
| Eager schema validation at load time | Lazy validation on first `agents_list` call | Eager gives faster failure feedback to operators editing YAML; trade-off is start-up cost (~ms per agent, negligible at PoC scale ≤ 20 agents). Recommend eager. |

**Installation:**
```bash
# No new packages required. All dependencies already pinned in pyproject.toml + uv.lock:
# - jsonschema 4.26.0 (transitive)
# - PyYAML 6.0.3
# - mcp 1.26.0
# - pydantic 2.13.4
# - pytest 9.0.2 + pytest-asyncio 1.3.0
```

**Version verification:**
```bash
# Verified at research time:
$ /data/workspace/hermes-agent/.venv/bin/python -c "import jsonschema; print(jsonschema.__version__)"
4.26.0
$ grep -E "^(jsonschema|PyYAML|ruamel\.yaml|mcp|pydantic|pytest|pytest-asyncio) " /data/workspace/hermes-agent/uv.lock
# All present, exact-pinned per pyproject.toml supply-chain policy
```

## Package Legitimacy Audit

> This phase installs **zero** new external packages. All required libraries (`jsonschema`, `PyYAML`, `mcp`, `pydantic`, `pytest`, `pytest-asyncio`) are already pinned in `pyproject.toml` + `uv.lock` and have been shipped in prior milestones. Slopcheck gate not triggered.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (no new packages) | — | — | — | — | — | N/A — phase reuses existing pinned deps |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                  ┌─────────────────────────────────────────┐
                  │  MCP Client (Claude Code / Cursor / etc) │
                  └────────────────┬────────────────────────┘
                                   │ stdio JSON-RPC (MCP transport)
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ mcp_serve.py — create_mcp_server()                                │
│ FastMCP("hermes") instance                                        │
│                                                                   │
│  Existing 9 messaging tools (lines 471-831)  ◄── pattern reference│
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 7 NEW v11.0 tools (Phase 52 INFRA-02)                      │  │
│  │  ┌────────────────┐  ┌────────────────┐                    │  │
│  │  │ round_table_   │  │ submit_round_  │  (lifecycle pair)   │  │
│  │  │ open           │  │ table_result   │                     │  │
│  │  └───────┬────────┘  └────────┬───────┘                     │  │
│  │          │                    │                             │  │
│  │          ▼                    ▼                             │  │
│  │  ┌────────────────┐  ┌────────────────┐                    │  │
│  │  │ get_agent_     │  │ agents_list /  │  (panelist/registry)│  │
│  │  │ opinion        │  │ agent_describe │                     │  │
│  │  └───────┬────────┘  └────────┬───────┘                     │  │
│  │          │ (serial)           │                             │  │
│  │          ▼                    ▼                             │  │
│  │  ┌────────────────┐  ┌────────────────┐                    │  │
│  │  │ memory_        │  │ memory_submit_ │  (Phase 53 prep,    │  │
│  │  │ retrieve_      │  │ record         │   primitive in 52)  │  │
│  │  │ scoped         │  │                │                     │  │
│  │  └────────────────┘  └────────────────┘                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────┬────────────┬─────────────────────────────┬──────────────┘
         │            │                             │
         ▼            ▼                             ▼
┌─────────────┐ ┌──────────────────┐  ┌──────────────────────────────┐
│ agent/      │ │ agent/           │  │ agent/                       │
│ registry_   │ │ round_table_     │  │ round_table_                 │
│ loader.py   │ │ state.py         │  │ executor.py                  │
│             │ │                  │  │ (per-roundId asyncio.Lock +  │
│ YAML walk + │ │ State machine    │  │  serial invariant + 429      │
│ jsonschema  │ │ open→...→closed  │  │  rejection w/ MEMORY.md      │
│ validation  │ │ Atomic write +   │  │  citation)                   │
│             │ │ crash recovery   │  │                              │
│ Returns:    │ │                  │  │ Uses: contextvars            │
│ AgentRegist │ │ Uses: utils.     │  │ _scoped_agent_id (Phase 53   │
│ ryEntry[]   │ │ atomic_json_write│  │ memory routing hook)         │
└──────┬──────┘ └────────┬─────────┘  └──────────────┬───────────────┘
       │                 │                           │
       ▼                 ▼                           ▼
┌────────────────────────────────────────────────────────────────────┐
│ Filesystem (~/.hermes/) — HERMES_HOME, redirected per-test by       │
│                              tests/conftest.py:_hermetic_environment│
│                                                                    │
│  agents/                      .runtime/{slug}/round_tables/         │
│  ├─ screenplay.agent.yaml     ├─ {roundId}.json                     │
│  ├─ cinematographer.agent.yaml│  (atomic-json-write + atomic-rename)│
│  └─ ...                       └─ ...                                │
│                                                                    │
│  (read by registry_loader)   (read+write by round_table_state)     │
└────────────────────────────────────────────────────────────────────┘
```

**Reading the diagram:** A round-table lifecycle flows (1) CC calls `round_table_open` → state.py writes a new `{roundId}.json` with `status: open`; (2) CC calls `get_agent_opinion` for each panelist serially → executor.py acquires per-roundId lock, state.py appends a `Turn` to the state file with atomic rename; (3) CC calls `submit_round_table_result` → state.py flips `status: completed` and seals the conflict log. A concurrent `get_agent_opinion` against an in-flight roundId hits the executor's lock and is rejected with 429 + MEMORY.md citation.

### Recommended Project Structure
```
agent/
├── registry_loader.py        # INFRA-01: YAML walk + jsonschema validation
├── round_table_state.py      # INFRA-03: state machine + atomic persistence + crash recovery
├── round_table_executor.py   # INFRA-02 + INFRA-04: per-roundId lock + tool dispatch helpers
├── memory_arbitration.py     # INFRA-02: contextvars primitive + memory_retrieve_scoped/_submit_record stubs
                                        (Phase 53 fills in real mem0 routing)
├── turn_retry_state.py       # EXISTING — pattern reference for dataclass state machine
├── curator_audit.py          # EXISTING — pattern reference for sha256 chain
├── glm_concurrency_guard.py  # EXISTING — pattern reference for threading.Semaphore
└── ...

mcp_serve.py                  # MODIFIED — add 7 @mcp.tool() closures inside create_mcp_server()

tests/agent/
├── test_registry_loader.py        # INFRA-01 unit tests
├── test_round_table_state.py      # INFRA-03 unit tests (incl. 3 crash recovery scenarios)
├── test_round_table_executor.py   # INFRA-04 unit tests (async concurrency, 429 rejection)
├── test_mcp_serve_round_table.py  # INFRA-02 integration test (lifecycle end-to-end)
└── fixtures/
    └── agents/
        ├─ test-coordinator.agent.yaml   # minimal valid synthetic agent
        └─ malformed.agent.yaml          # invalid YAML for SC#1 negative test

.planning/research/v10-orchestrator-design/
├── agents-schema.yaml             # CONSUMED (read-only) by registry_loader
└── round-table-state-schema.yaml  # CONSUMED (read-only) by round_table_state
```

### Pattern 1: Atomic State Persistence (REUSE — do not reinvent)
**What:** Round-table state files use temp-write + fsync + `os.replace` to guarantee no partial-write corruption.
**When to use:** Every state mutation (`round_table_open`, each turn append, `submit_round_table_result`).
**Example:**
```python
# Source: utils.py:111 atomic_json_write — verbatim pattern already shipped
from utils import atomic_json_write

def _persist_state(state_path: Path, state: RoundTableState) -> None:
    """Crash-safe persistence: temp + fsync + os.replace.

    If the process crashes mid-write, the previous version of {roundId}.json
    remains intact (the temp file is unlinked in the BaseException handler).
    """
    atomic_json_write(
        state_path,
        state.to_dict(),  # camelCase keys per round-table-state-schema.yaml
        indent=2,
    )
```

### Pattern 2: Per-roundId Async Lock (NEW — introduce asyncio.Lock)
**What:** FastMCP tools run inside an asyncio event loop. A per-`roundId` `asyncio.Lock` serializes `get_agent_opinion` calls so concurrent submissions are rejected with 429 + MEMORY.md citation.
**When to use:** Inside `get_agent_opinion` (and any other turn-mutating tool).
**Example:**
```python
# Source: asyncio.Lock pattern adapted from gateway/session_context.py contextvars idiom
import asyncio
from contextvars import ContextVar

# Module-level registry of per-roundId locks. Lazily created on first access.
_round_locks: dict[str, asyncio.Lock] = {}
_round_locks_guard = asyncio.Lock()  # guards the registry itself

async def _get_round_lock(round_id: str) -> asyncio.Lock:
    async with _round_locks_guard:
        if round_id not in _round_locks:
            _round_locks[round_id] = asyncio.Lock()
        return _round_locks[round_id]

async def get_agent_opinion(round_id: str, agent_id: str, topic: str, ...) -> str:
    lock = await _get_round_lock(round_id)
    if lock.locked():
        # SC#4 — reject concurrent submission with MEMORY.md citation
        return json.dumps({
            "error": "serial_violation",
            "status": 429,
            "message": (
                "Concurrent get_agent_opinion for the same roundId is rejected. "
                "Hermes enforces 1 panelist 1 turn sequential execution by design "
                "(global concurrency==1; GLM 4-key rotation compatible). "
                "See MEMORY.md feedback-glm-overload-reduce-concurrency.md."
            ),
            "round_id": round_id,
        })
    async with lock:
        # ... actual opinion dispatch ...
        pass
```

**Why `if lock.locked()` then `async with lock` rather than just `async with lock` (which would queue)?** SC#4 says concurrent calls are **rejected** (429), not queued. The check-then-acquire has a small TOCTOU window but is safe under asyncio's cooperative scheduling — no other task runs between the `await` resolution and the `async with` entry.

### Pattern 3: Lazy Plugin Discovery (mirror existing provider/platform pattern)
**What:** Agent registry loads on first `agents_list` call and caches. Avoids paying YAML-walk + schema-validation cost on every MCP startup if no round-table tools are invoked.
**When to use:** `registry_loader.load_agent_registry()` should be wrapped in a `functools.lru_cache` or module-level `_REGISTRY_CACHE` sentinel.
**Example:**
```python
# Source: providers/__init__.py:140 _discover_providers pattern + agent/i18n.py:83 _catalog_cache
_REGISTRY_CACHE: list[AgentRegistryEntry] | None = None
_REGISTRY_CACHE_LOCK = threading.Lock()

def load_agent_registry(*, force_reload: bool = False) -> list[AgentRegistryEntry]:
    """Lazy-load + validate ~/.hermes/agents/*.agent.yaml.

    Validates each YAML against agents-schema.yaml (Draft 2020-12).
    Raises RegistryValidationError on schema violation with field-specific message.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and not force_reload:
        return _REGISTRY_CACHE
    with _REGISTRY_CACHE_LOCK:
        if _REGISTRY_CACHE is not None and not force_reload:
            return _REGISTRY_CACHE
        agents_dir = get_hermes_home() / "agents"
        entries = []
        for yaml_path in sorted(agents_dir.glob("*.agent.yaml")):
            entries.append(_load_and_validate_one(yaml_path))
        _REGISTRY_CACHE = entries
        return entries
```

### Pattern 4: Dataclass State Machine (mirror agent/turn_retry_state.py)
**What:** Round-table state is a `@dataclass` with explicit status enum, mutated in place, serialized via `dataclasses.asdict` for `atomic_json_write`.
**When to use:** `round_table_state.py`.
**Example:**
```python
# Source: agent/turn_retry_state.py:33 (TurnRetryState dataclass pattern)
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum

class RoundTableStatus(str, Enum):
    # CITE: round-table-state-schema.yaml status enum
    # NOTE: see Open Question #2 — design suite has conflicting enums
    OPEN = "open"
    COMPLETED = "completed"
    ABORTED = "aborted"
    STALLED = "stalled"

@dataclass
class Turn:
    turn_index: int
    panelist_id: str
    opinion: str
    cited_memory_ids: list[str] = field(default_factory=list)
    submitted_at: str = ""  # ISO-8601 UTC

@dataclass
class RoundTableState:
    round_id: str
    project_id: str
    question: str
    status: RoundTableStatus = RoundTableStatus.OPEN
    turns: list[Turn] = field(default_factory=list)
    # ... other fields per round-table-state-schema.yaml ...

    def to_dict(self) -> dict:
        """Serialize for atomic_json_write. CamelCase keys per schema."""
        d = asdict(self)
        # Convert enum to value + rename snake_case → camelCase for JSON
        d["status"] = self.status.value
        return _snake_to_camel(d)  # helper
```

### Anti-Patterns to Avoid
- **Top-level `run_agent` import in `agent/registry_loader.py`** — circular import; use `_ra()` lazy indirection if absolutely needed (CLAUDE.md).
- **`Path.home() / ".hermes"`** — use `get_hermes_home()` from `hermes_constants`. The conftest fixture redirects `HERMES_HOME` per-test; `Path.home()` bypasses that and leaks into real `~/.hermes`.
- **`open(state_path, "w")` without `encoding="utf-8"`** — Ruff PLW1514 blocks the merge. (Use `atomic_json_write`, which handles encoding correctly.)
- **`os.kill`, `subprocess.run(["systemctl", ...])` in tests without mocking** — autouse `_live_system_guard` fixture (tests/conftest.py:539) raises `RuntimeError`. Mock or mark with `@pytest.mark.live_system_guard_bypass`.
- **f-string in `logger.x(...)`** — use `%s` positional args per CLAUDE.md logging convention.
- **Using `threading.Lock` for FastMCP tool serialization** — `threading.Lock` would block the entire asyncio event loop. Use `asyncio.Lock` for in-event-loop primitives.
- **State machine values `open → in_progress → closed` (CONTEXT.md wording)** vs `open | completed | aborted | stalled` (schema file) — see Open Question #2. Do NOT write code until resolved.
- **Cross-project reference in round-table state JSON** — `06-CROSS-REPO-IMPACT.md` §6.5 forbids this. State file `projectId` field gates the path; do not allow lookups across projects.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file write (crash-safe rename) | Custom `tempfile + os.replace` | `utils.atomic_json_write` (utils.py:111) | Already handles fsync, EXDEV/EBUSY cross-device fallback, symlink preservation (GitHub #16743), mode preservation, BaseException-safe cleanup. 8 years of edge cases baked in. |
| Atomic YAML write | Custom `tempfile + os.replace` for YAML | `utils.atomic_yaml_write` (utils.py:180) | Same fsync + rename pattern, PyYAML-aware |
| JSON Schema validation | Hand-rolled field-by-field checks | `jsonschema.Draft202012Validator` | Schema is already JSON Schema Draft 2020-12; the library gives you `$ref` resolution, custom error messages, format checkers for free |
| sha256 chain (evolution_log) | Custom sha256 chaining logic | Mirror `agent/curator_audit.py` `_compute_entry_sha256` + `_serialize_entry_for_sha256` | Same tamper-evident pattern already shipped in v6.0; copying the formula avoids subtle serialization-drift bugs |
| YAML frontmatter parsing | Custom regex splitter | `agent/skill_utils.parse_frontmatter` (or generalize it) | Already handles the `---\n---` boundary correctly |
| Per-task session scoping | `threading.local` | `contextvars.ContextVar` | ThreadPoolExecutor worker reuse makes `threading.local` leak scope across tasks; `contextvars` is asyncio-correct. Canonical pattern at `gateway/session_context.py:39` |
| GLM concurrency throttling (don't confuse with serial invariant) | Per-roundId lock for GLM throttle | `agent/glm_concurrency_guard.py` already handles GLM API throttling | INFRA-04's serial invariant is about *turn-level ordering* (1 panelist 1 turn sequential); GLM guard is about *API-call-level throttling* (N=1 concurrent in-flight requests). These are independent layers — do not collapse them. |

**Key insight:** The serial-execution invariant (INFRA-04) and the GLM concurrency guard are **two different layers**. The serial invariant says "no two `get_agent_opinion` calls for the same `roundId` may overlap." The GLM guard says "no more than N concurrent in-flight requests to `*.bigmodel.cn`." A correctly-serialized round table still goes through the GLM guard on every LLM call — they compose.

## Runtime State Inventory

> Phase 52 is **greenfield** for runtime state — it CREATES new state (`.runtime/{slug}/round_tables/`, `~/.hermes/agents/*.agent.yaml` directory convention) but does not rename or migrate any existing state. Skip the full rename/refactor inventory.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — Phase 52 introduces the `.runtime/{slug}/round_tables/` directory; no existing data store uses it | Create directory on first `round_table_open`; no migration |
| Live service config | None — no n8n workflows / external service configs reference agent registry or round-table state | None |
| OS-registered state | None — no Task Scheduler / launchd / systemd unit references the new modules | None |
| Secrets/env vars | None — Phase 52 reads no new env vars beyond `HERMES_HOME` (already canonical) | None |
| Build artifacts | None — pure Python source, no compiled artifacts | None |

**Nothing found in category:** This is a greenfield infrastructure phase — verified by codebase grep for `.runtime/` (zero matches in existing source) and `~/.hermes/agents/` (zero matches — the directory does not yet exist).

## Common Pitfalls

### Pitfall 1: asyncio.Lock vs threading.Lock confusion
**What goes wrong:** Using `threading.Lock` inside an async FastMCP tool blocks the entire event loop while waiting for the lock, freezing all concurrent MCP tool calls (including unrelated messaging tools).
**Why it happens:** Most of the codebase uses `threading.Semaphore` (e.g., `agent/glm_concurrency_guard.py`) because the SDK calls are blocking. Developers copy-paste the pattern into async context.
**How to avoid:** Use `asyncio.Lock` for any await-able serialization inside `async def` MCP tools. Reserve `threading.Semaphore`/`Lock` for blocking SDK calls inside `ThreadPoolExecutor` workers.
**Warning signs:** Test that exercises two concurrent `get_agent_opinion` calls times out instead of returning 429.

### Pitfall 2: TOCTOU race in check-then-acquire lock pattern
**What goes wrong:** `if lock.locked(): return 429; async with lock: ...` has a window between the check and the `async with` entry where another coroutine could acquire the lock. Under asyncio's cooperative scheduling this window only closes at an `await`, but if the code path between the check and `async with` contains an `await`, a race is possible.
**Why it happens:** SC#4 mandates *rejection* of concurrent submissions, not *queueing*. The naive implementation queues.
**How to avoid:** Make the check-then-acquire atomic by using `lock.acquire(block=False)` instead:
```python
acquired = lock.locked() is False and await _try_acquire(lock)
# or, simpler:
try:
    acquired = lock.locked() is False
    if acquired:
        await lock.acquire()
except RuntimeError:
    acquired = False
```
Actually, the cleanest pattern is to use a non-blocking acquire via `asyncio.Lock`'s coro: `acquired = lock.acquire_no_wait()` — but asyncio.Lock doesn't have that. Use this idiom instead:
```python
lock = await _get_round_lock(round_id)
if lock.locked():
    return _429_response(round_id)
# Between the check and the acquire, no other coroutine can run
# UNLESS we await something. Don't await anything here.
async with lock:
    ...
```
Test with `asyncio.gather` to verify the race window is empty.
**Warning signs:** Intermittent test flakiness in `test_concurrent_get_agent_opinion_second_call_rejected`.

### Pitfall 3: Schema validation eager vs lazy tradeoff
**What goes wrong:** Lazy validation (validate on first `agents_list` call) gives bad UX — operator edits YAML, restarts Hermes, gets no error, then an hour later hits the error mid-round-table.
**Why it happens:** Lazy feels faster to implement because you skip validation when the round-table feature isn't used.
**How to avoid:** Eager validation at registry load time. The cost is ~ms per agent (jsonschema validation is fast at ≤20 agents). Log validation errors to `agent.log` + `errors.log` with the specific schema-violation path (`$.persona: field is required`) so operators can fix YAMLs without grep'ing source.
**Warning signs:** Operator reports "round_table_open worked but get_agent_opinion failed with weird error" — that's lazy validation leaking.

### Pitfall 4: round-table-state-schema.yaml vs CONTEXT.md state-enum mismatch
**What goes wrong:** CONTEXT.md/INFRA-03 says `open → in_progress → closed`. `round-table-state-schema.yaml` says `open | completed | aborted | stalled`. If implementation uses one and tests check the other, you get spurious failures or worse, shipped code that doesn't match the schema file.
**Why it happens:** The design suite has internal inconsistencies between narrative docs (06-CROSS-REPO-IMPACT §6.1 uses yet a third enum: `in_progress | closed | abandoned`) and the schema YAML. The schema YAML is the most authoritative artifact (`$schema: draft 2020-12`, `additionalProperties: false`).
**How to avoid:** Resolve in Open Question #2 BEFORE writing code. Recommend using `round-table-state-schema.yaml` values verbatim (`open | completed | aborted | stalled`) and treating CONTEXT.md's `in_progress/closed` as informal shorthand.
**Warning signs:** Schema validation fails on a syntactically valid state file because the status field has the wrong enum value.

### Pitfall 5: mem0 backend integration assumed available
**What goes wrong:** Phase 52 builds `memory_arbitration.py` with `memory_retrieve_scoped` / `memory_submit_record` MCP tools. If those tools eagerly call into `plugins/memory/mem0/__init__.py`, the test suite fails when `MEM0_API_KEY` isn't set.
**Why it happens:** `plugins/memory/mem0/__init__.py:144 is_available()` returns False without an api_key, but the provider's `search()` will still raise.
**How to avoid:** Phase 52 ships the MCP tool **stubs** + the `_scoped_agent_id` contextvars primitive. The actual mem0 routing is Phase 53's job. Phase 52's `memory_retrieve_scoped` returns an empty list with a `"phase53_not_implemented"` status field.
**Warning signs:** Tests require a live mem0 backend to pass.

### Pitfall 6: 7 MCP tool naming — CONTEXT.md vs 02-ROUND-TABLE-PROTOCOL.md §5 conflict
**What goes wrong:** CONTEXT.md and INFRA-02 list: `round_table_open`, `submit_round_table_result`, `get_agent_opinion`, `agents_list`, `agent_describe`, `memory_retrieve_scoped`, `memory_submit_record`. The v10.0 design suite `02-ROUND-TABLE-PROTOCOL.md §5` lists: `get_agent_persona`, `get_agent_opinion`, `get_agent_memory`, `submit_round_table_result`, `submit_artifact`, `query_memory`, `run_python_phase`. Implementing one set when the v10.0 design locked the other breaks Phase 53/54/55 downstream.
**Why it happens:** The CONTEXT.md description was written based on an early reading of the design suite; the design suite §5 is the authoritative source ("Authoritative Pydantic schema in STACK §3.2").
**How to avoid:** Resolve in Open Question #1 BEFORE writing code. Recommend treating `02-ROUND-TABLE-PROTOCOL.md §5` as authoritative (it's the locked design doc) and treating CONTEXT.md's list as a phase-planner simplification.
**Warning signs:** Plan/executor implements a tool name that doesn't appear in the design suite.

### Pitfall 7: Live-system guard triggers in tests
**What goes wrong:** Any test that calls `mcp_serve.create_mcp_server()` may transitively trigger `os.kill` / `subprocess.run(["systemctl", ...])` lookups, hitting the autouse `_live_system_guard` fixture (tests/conftest.py:539) and raising `RuntimeError`.
**Why it happens:** conftest's guard AST-inspects test functions for live-system-call patterns.
**How to avoid:** Mock at the test boundary — inject a fake `EventBridge`, mock `hermes_state.SessionDB`, and mark genuinely needed integration tests with `@pytest.mark.live_system_guard_bypass`.
**Warning signs:** Test collection raises `RuntimeError("live system guard ...")`.

### Pitfall 8: `glob("*.agent.yaml")` vs SKILL.md discovery rule
**What goes wrong:** Existing `agent/skill_utils.py` walks `skills/<category>/<name>/SKILL.md` (capital). Developers assume agent YAMLs follow the same pattern and put them at `~/.hermes/agents/<category>/<name>/<name>.agent.yaml`. The design suite puts them flat at `~/.hermes/agents/{name}.agent.yaml`.
**Why it happens:** Pattern mismatch between SKILL discovery (nested) and agent discovery (flat).
**How to avoid:** Use flat `~/.hermes/agents/*.agent.yaml` per `agents-schema.yaml` description + CONTEXT.md. Add a test that explicitly verifies the flat layout is honored.
**Warning signs:** Operator reports their agent YAML "isn't being discovered" — they put it in a subdirectory.

## Code Examples

Verified patterns from the codebase. Each is referenced by file:line so the planner can lift the pattern verbatim.

### YAML Loader Pattern (INFRA-01)
```python
# Source: agent/skill_utils.py:88 parse_frontmatter + utils.py atomic_yaml_write
# + agent/plugin_llm.py:474 jsonschema usage
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
import yaml

logger = logging.getLogger(__name__)


class RegistryValidationError(Exception):
    """Raised when an agent YAML fails schema validation."""


def _load_schema() -> dict[str, Any]:
    """Load agents-schema.yaml from the v10.0 research dir."""
    schema_path = (
        Path(__file__).resolve().parent.parent
        / ".planning" / "research" / "v10-orchestrator-design"
        / "agents-schema.yaml"
    )
    with open(schema_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


_SCHEMA_CACHE: dict[str, Any] | None = None


def _get_validator() -> jsonschema.Draft202012Validator:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = _load_schema()
    return jsonschema.Draft202012Validator(_SCHEMA_CACHE)


def load_one_agent_yaml(yaml_path: Path) -> dict[str, Any]:
    """Load + validate a single agent YAML. Raises RegistryValidationError."""
    with open(yaml_path, encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise RegistryValidationError(
                f"{yaml_path}: invalid YAML syntax: {exc}"
            ) from exc

    validator = _get_validator()
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        # SC#1: specific schema-violation error message
        first = errors[0]
        path = "$" + "".join(f"[{repr(p)}]" for p in first.absolute_path)
        raise RegistryValidationError(
            f"{yaml_path}: schema violation at {path}: {first.message}"
        )

    # Verify name matches filename stem (agents-schema.yaml §2.1)
    expected_stem = yaml_path.name.removesuffix(".agent.yaml")
    actual_name = data.get("name", "")
    if actual_name != expected_stem:
        raise RegistryValidationError(
            f"{yaml_path}: name field {actual_name!r} does not match "
            f"filename stem {expected_stem!r}"
        )

    return data
```

### MCP Tool Registration Pattern (INFRA-02)
```python
# Source: mcp_serve.py:450 create_mcp_server + 471-525 conversations_list
# In mcp_serve.py create_mcp_server(), add inside the existing function body:

@mcp.tool()
def agents_list(category: Optional[str] = None, tag: Optional[str] = None) -> str:
    """List registered Hermes agents (~/.hermes/agents/*.agent.yaml).

    Returns each agent's name, description, version, tags, and fitness_score.
    Use agent_describe for full details on a specific agent.

    Args:
        category: Optional category filter (not yet implemented — Phase 53)
        tag: Optional tag filter (matches agents-schema.yaml §2.9 tags field)
    """
    from agent.registry_loader import load_agent_registry
    try:
        entries = load_agent_registry()
    except Exception as exc:
        logger.warning("agents_list: registry load failed: %s", exc)
        return json.dumps({"error": "registry_load_failed", "detail": str(exc)})

    filtered = entries
    if tag:
        filtered = [e for e in filtered if tag in e.get("tags", [])]

    return json.dumps({
        "count": len(filtered),
        "agents": [
            {
                "name": e["name"],
                "description": e["description"],
                "version": e["version"],
                "tags": e.get("tags", []),
                "fitness_score": e.get("fitness_score"),
                "memory_scope": e["memory_scope"],
            }
            for e in filtered
        ],
    }, indent=2)
```

### Atomic State Persistence Pattern (INFRA-03)
```python
# Source: utils.py:111 atomic_json_write + agent/turn_retry_state.py dataclass pattern
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from utils import atomic_json_write

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def open_round_table(
    state_dir: Path, round_id: str, project_id: str, question: str,
    panelist_agent_ids: list[str], caller: str,
) -> dict:
    """SC#2 step 1: create a new round-table state file atomically.

    Idempotent: if {round_id}.json already exists, return 409 Conflict.
    """
    state_path = state_dir / f"{round_id}.json"
    if state_path.exists():
        return {"error": "round_already_open", "status": 409, "round_id": round_id}

    state = {
        # CITE round-table-state-schema.yaml (resolve Open Question #2 first)
        "roundId": round_id,
        "projectId": project_id,
        "question": question,
        "panelists": [],  # populated by registry_loader snapshots
        "turnOrder": {"strategy": "round-robin", "currentIndex": 0, "seed": panelist_agent_ids},
        "status": "open",
        "turns": [],
        "conflicts": [],
        "roundTableOpen": {"caller": caller, "openedAt": _now_iso(), "project": project_id, "question": question},
        "personaSnapshots": {},
        "schemaVersion": "1.0.0",
        "createdAt": _now_iso(),
        "lastUpdatedAt": None,
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    # atomic_json_write = temp + fsync + os.replace — partial-write safe
    atomic_json_write(state_path, state, indent=2)
    return state


def append_turn(state_path: Path, turn: dict) -> dict:
    """SC#2 step 2: append a Turn atomically. Read-modify-write under lock."""
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    state["turns"].append(turn)
    state["lastUpdatedAt"] = _now_iso()
    atomic_json_write(state_path, state, indent=2)
    return state


def submit_round_table_result(state_path: Path, conclusion: str, ...) -> dict:
    """SC#2 step 3: terminal transition. Flips status to 'completed'.

    Idempotent: second submit returns 409 Conflict.
    """
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    if state["status"] != "open":
        return {"error": "round_not_open", "status": 409}
    state["status"] = "completed"
    state["submitRoundTableResult"] = {
        "conclusion": conclusion,
        "citedMemories": [],
        "closedAt": _now_iso(),
        "closedBy": "cc",
    }
    state["lastUpdatedAt"] = _now_iso()
    atomic_json_write(state_path, state, indent=2)
    return state
```

### Crash Recovery Read-Time Pattern (INFRA-03 — 3 failure modes)
```python
# Source: 06-CROSS-REPO-IMPACT.md §6.4 (3 failure modes) + atomic_json_write guarantee

def read_and_recover_state(state_path: Path, *, stall_threshold_minutes: int = 30) -> dict:
    """Read a round-table state file and apply crash recovery if needed.

    Three failure modes (per 06-CROSS-REPO-IMPACT.md §6.4):
      (a) Partial-write corruption — atomic_json_write guarantees this CANNOT
          happen to the file body. If the file exists, it's valid JSON.
          (Recovery: none needed; the guarantee is the recovery.)
      (b) Mid-turn crash — process died between turn append + status flip.
          State file shows status=open + lastUpdatedAt old.
          (Recovery: detect via stall_threshold; flip status to stalled.)
      (c) Orphaned session — state file exists but the calling process is gone.
          (Recovery: same as (b) — stall detection on read.)
    """
    if not state_path.exists():
        raise FileNotFoundError(state_path)

    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except json.JSONDecodeError as exc:
        # Failure mode (a) defense-in-depth: if somehow the file is corrupted
        # (e.g.EXT4-fsync race on ancient kernel), archive it and raise.
        archive = state_path.with_suffix(".json.corrupt")
        state_path.rename(archive)
        logger.error("round_table_state corrupt, archived to %s: %s", archive, exc)
        raise

    # Failure mode (b)/(c): stall detection
    if state.get("status") == "open" and state.get("lastUpdatedAt"):
        last = datetime.fromisoformat(state["lastUpdatedAt"])
        age = (datetime.now(timezone.utc) - last).total_seconds() / 60
        if age > stall_threshold_minutes:
            logger.warning(
                "round_table %s stalled (age=%dm > %dm); flipping status",
                state.get("roundId"), int(age), stall_threshold_minutes,
            )
            state["status"] = "stalled"
            atomic_json_write(state_path, state, indent=2)

    return state
```

### Per-roundId Async Lock Pattern (INFRA-04)
```python
# Source: gateway/session_context.py:39 contextvars pattern + new asyncio.Lock idiom
from __future__ import annotations

import asyncio
import json
from typing import Optional

# Module-level registry of per-roundId locks. Lives in the FastMCP event loop.
_ROUND_LOCKS: dict[str, asyncio.Lock] = {}
_ROUND_LOCKS_GUARD = asyncio.Lock()


async def _get_or_create_round_lock(round_id: str) -> asyncio.Lock:
    """Get-or-create the per-roundId asyncio.Lock."""
    async with _ROUND_LOCKS_GUARD:
        if round_id not in _ROUND_LOCKS:
            _ROUND_LOCKS[round_id] = asyncio.Lock()
        return _ROUND_LOCKS[round_id]


def _serial_violation_response(round_id: str) -> str:
    """SC#4: 429 with MEMORY.md citation."""
    return json.dumps({
        "error": "serial_violation",
        "status": 429,
        "round_id": round_id,
        "message": (
            "Concurrent get_agent_opinion for the same roundId is rejected. "
            "Hermes enforces 1 panelist 1 turn sequential execution by design "
            "(global concurrency==1; GLM 4-key rotation compatible). "
            "See MEMORY.md feedback-glm-overload-reduce-concurrency.md."
        ),
    }, indent=2)


async def acquire_round_or_reject(round_id: str) -> Optional[asyncio.Lock]:
    """Try to acquire the per-roundId lock. Return None if contended.

    SC#4 mandates REJECTION (not queueing) of concurrent submissions.
    """
    lock = await _get_or_create_round_lock(round_id)
    # Check-then-acquire. Under asyncio cooperative scheduling, no other task
    # runs between this point and `await lock.acquire()` because there is no
    # await in between.
    if lock.locked():
        return None
    await lock.acquire()
    return lock
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SKILL.md as user-message injection (v1-v9) | Agent YAML with persona as system-prompt fragment (v10/v11) | Phase 44 decision 5 (2026-07) | Agent persona is now first-person expert identity, not imperative-second-person template |
| Global mem0 user_id (v7.0 default) | Per-agent memory_scope namespace (v10.0) | Phase 44 decision 6 + 01-AGENT-REGISTRY-SCHEMA §2.6 | `user_id=agent:{name}` routes records per-agent; default `per_agent` |
| threading.Semaphore for GLM (2026-07-02) | asyncio.Lock for in-event-loop turn serialization (v11.0 Phase 52) | This phase | Different layer: GLM guard throttles API calls; Phase 52 lock serializes turn-level ordering. They compose. |
| `os.kill(pid, 0)` for liveness (pre-2026) | `psutil`-based process-tree walking (2026+) | pyproject.toml:62-66 comment | Phase 52 tests must mock `psutil` if process-liveness checks are added |

**Deprecated/outdated:**
- **`os.environ["HERMES_SESSION_*"]`** — replaced by `gateway/session_context.py` contextvars (2026). New code MUST use contextvars.
- **`Path.home() / ".hermes"`** in production code — replaced by `hermes_constants.get_hermes_home()`. Still appears in legacy paths; do not introduce in new code.
- **Lazy plugin discovery without cache** — providers/platforms now use `_discovered` flag. Agent registry should follow same idempotent-once pattern.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `asyncio.Lock` is the correct primitive for serializing FastMCP tool calls | Pattern 2, INFRA-04 | MEDIUM — if FastMCP actually runs tools in a ThreadPoolExecutor, `asyncio.Lock` would block. Mitigation: verify FastMCP dispatch model in Wave 0 with a 5-line probe test. |
| A2 | `jsonschema 4.26.0` supports `Draft202012Validator` | Standard Stack | LOW — jsonschema has shipped Draft202012Validator since 4.0 (2021). Verified by `import jsonschema; jsonschema.Draft202012Validator` succeeds at runtime. |
| A3 | `02-ROUND-TABLE-PROTOCOL.md §5` is the authoritative source for tool names over CONTEXT.md/INFRA-02 | Pitfall 6, Open Q#1 | HIGH — implementing the wrong tool names breaks Phase 53/54/55. The CONTEXT.md was auto-generated by smart-discuss; the design suite was locked in Phase 46. |
| A4 | `round-table-state-schema.yaml` is the authoritative source for state-enum values over CONTEXT.md/INFRA-03 | Pitfall 4, Open Q#2 | MEDIUM — same authoritative-source question. Schema YAML is machine-checkable; CONTEXT.md prose is informal. |
| A5 | Agent YAMLs live flat at `~/.hermes/agents/{name}.agent.yaml` (not nested like SKILLs) | Pitfall 8 | LOW — agents-schema.yaml description says so explicitly. Test verifies flat layout. |
| A6 | Phase 52 ships `memory_retrieve_scoped` / `memory_submit_record` as stubs (Phase 53 fills in mem0 routing) | Pitfall 5 | MEDIUM — if Phase 53 expects working tools, Phase 52 must do real mem0 integration. Confirm with planner. |
| A7 | `contextvars.ContextVar` is the correct primitive for `_scoped_agent_id` (not `threading.local`) | Don't Hand-Roll table | LOW — ARCHITECTURE §3.3 + 01-AGENT-REGISTRY-SCHEMA §5.5 explicitly mandate contextvars. |
| A8 | The `.planning/research/v10-orchestrator-design/` YAML files are stable inputs (won't change mid-phase) | All sections | LOW — they were committed in v10.0 design milestone (Phase 45-50, tag v10.0) and are LOCKED per stability markers. |

## Open Questions

1. **Tool names — which list is authoritative?**
   - What we know: CONTEXT.md/INFRA-02 lists 7 names (`round_table_open`, `submit_round_table_result`, `get_agent_opinion`, `agents_list`, `agent_describe`, `memory_retrieve_scoped`, `memory_submit_record`). `02-ROUND-TABLE-PROTOCOL.md §5` lists 7 different names (`get_agent_persona`, `get_agent_opinion`, `get_agent_memory`, `submit_round_table_result`, `submit_artifact`, `query_memory`, `run_python_phase`). Overlap is only 2 names (`get_agent_opinion`, `submit_round_table_result`).
   - What's unclear: whether CONTEXT.md was a deliberate simplification/renaming for v11.0 PoC scope, or an early-plan artifact that should defer to the locked design suite.
   - Recommendation: **Treat `02-ROUND-TABLE-PROTOCOL.md §5` as authoritative** for tool contracts (signatures, side effects). Use CONTEXT.md's `agents_list` / `agent_describe` as user-facing aliases for `get_agent_persona` if/when a registry-browsing surface is needed. Surface in discuss-phase or planner checkpoint before implementation.

2. **State-enum values — which doc is authoritative?**
   - What we know: CONTEXT.md/INFRA-03 says `open → in_progress → closed`. `round-table-state-schema.yaml` says `open | completed | aborted | stalled` (with `stalled → open` resume and `stalled → aborted` paths). `06-CROSS-REPO-IMPACT.md §6.1` uses a third enum: `in_progress | closed | abandoned`.
   - What's unclear: which doc the runtime should serialize into the state JSON.
   - Recommendation: **Treat `round-table-state-schema.yaml` as authoritative** for the wire format. It's the machine-checkable JSON Schema (`additionalProperties: false`, `$schema: draft 2020-12`). CONTEXT.md's `in_progress/closed` is informal shorthand for the open-but-active and completed states.

3. **Does `round_table_open` exist as an MCP tool in Phase 52, or is it deferred to v11.1+?**
   - What we know: `02-ROUND-TABLE-PROTOCOL.md §5.0` says: "lifecycle controller (`round_table_open` / `round_table_resume` / `round_table_abort` deferred to v11.1+), 构成 v10.0 round table 的 MCP 表面." But CONTEXT.md/INFRA-02 lists `round_table_open` as a Phase 52 deliverable, and SC#2/SC#3 require `round_table_open` to be callable.
   - What's unclear: whether the §5.0 deferral comment predates the v11.0 PoC plan (which DOES require `round_table_open`).
   - Recommendation: **Implement `round_table_open` in Phase 52** — SC#2/SC#3 cannot pass without it. The §5.0 deferral comment is stale (predates 05-POC-PLAN.md §3.3 which mandates `round_table_open`).

4. **Should `agent_describe` exist as a separate tool, or is it `get_agent_persona` renamed?**
   - What we know: CONTEXT.md lists `agent_describe`. Design suite has `get_agent_persona` (returns persona YAML block).
   - Recommendation: Implement `agents_list` (registry-browse, returns summary list) and `agent_describe` (returns full agent YAML for one agent — broader than just persona). Treat `get_agent_persona` as a v11.1+ narrow-scope variant.

5. **Does Phase 52 ship working `memory_retrieve_scoped` / `memory_submit_record`, or stubs?**
   - What we know: 01-AGENT-REGISTRY-SCHEMA §5.5 says Phase 52 builds the `_scoped_agent_id` contextvars primitive. Phase 53 does real mem0 routing.
   - Recommendation: **Ship stubs** that return `{"status": "phase53_not_implemented", "hits": []}`. Phase 52's job is the wire-up + primitive; Phase 53's job is the routing. Confirm with planner.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All Phase 52 modules | ✓ | 3.13 (per Dockerfile) / 3.11 minimum per pyproject | — |
| `jsonschema` | INFRA-01 schema validation | ✓ | 4.26.0 [VERIFIED: uv.lock + `python -c "import jsonschema"`] | — |
| `PyYAML` | INFRA-01 YAML parsing | ✓ | 6.0.3 [VERIFIED: pyproject.toml] | — |
| `mcp` (FastMCP) | INFRA-02 MCP tool wire-up | ✓ | 1.26.0 [VERIFIED: pyproject.toml] | — |
| `pydantic` | Optional tool I/O models | ✓ | 2.13.4 [VERIFIED: pyproject.toml] | Use plain dataclasses if you want zero deps |
| `pytest` + `pytest-asyncio` | INFRA-04 concurrency tests | ✓ | 9.0.2 + 1.3.0 [VERIFIED: pyproject.toml] | — |
| `~/.hermes/` writable | State file persistence | ✓ | Redirected per-test by conftest `_hermetic_environment` | — |
| mem0 backend (MEM0_API_KEY) | `memory_retrieve_scoped` / `memory_submit_record` (Phase 53) | ✗ | — | Ship as stubs in Phase 52; real mem0 in Phase 53 |
| GLM API key | `get_agent_opinion` LLM call (Phase 53) | Unknown (operator-side) | — | SC#2 says "single synthetic agent" — Phase 52 likely uses a mock LLM |

**Missing dependencies with no fallback:** none for Phase 52's scope.
**Missing dependencies with fallback:** mem0 backend — Phase 52 ships stubs (per Open Question #5).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml:261` (addopts includes `-ra --strict-markers --timeout=30`) |
| Quick run command | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/agent/test_registry_loader.py -x` |
| Full suite command | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/agent/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | Valid YAML loads + appears in `agents_list` | unit | `pytest tests/agent/test_registry_loader.py::test_valid_yaml_loads -x` | ❌ Wave 0 |
| INFRA-01 | Malformed YAML rejected with field-specific error | unit | `pytest tests/agent/test_registry_loader.py::test_malformed_yaml_rejected -x` | ❌ Wave 0 |
| INFRA-01 | `name` mismatch with filename stem rejected | unit | `pytest tests/agent/test_registry_loader.py::test_name_filename_mismatch -x` | ❌ Wave 0 |
| INFRA-02 | `agents_list` MCP tool returns JSON list | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_agents_list_returns_json -x` | ❌ Wave 0 |
| INFRA-02 | `agent_describe` returns full agent YAML | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_agent_describe_returns_yaml -x` | ❌ Wave 0 |
| INFRA-03 (SC#2) | `open → opinion → submit` round trip on synthetic agent | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_lifecycle_round_trip -x` | ❌ Wave 0 |
| INFRA-03 (SC#2) | Interrupted submit doesn't leave `status: in_progress` | unit | `pytest tests/agent/test_round_table_state.py::test_interrupted_submit_atomic -x` | ❌ Wave 0 |
| INFRA-03 (SC#3a) | Partial-write corruption recovered (defense-in-depth) | unit | `pytest tests/agent/test_round_table_state.py::test_partial_write_recovery -x` | ❌ Wave 0 |
| INFRA-03 (SC#3b) | Mid-turn crash recovered via stall detection | unit | `pytest tests/agent/test_round_table_state.py::test_mid_turn_crash_recovery -x` | ❌ Wave 0 |
| INFRA-03 (SC#3c) | Orphaned session recovered on next read | unit | `pytest tests/agent/test_round_table_state.py::test_orphaned_session_recovery -x` | ❌ Wave 0 |
| INFRA-04 (SC#4) | Concurrent second `get_agent_opinion` rejected with 429 + MEMORY.md citation | async unit | `pytest tests/agent/test_round_table_executor.py::test_concurrent_submission_rejected -x` | ❌ Wave 0 |
| INFRA-04 (SC#4) | Single sequential submission proceeds + returns opinion | async unit | `pytest tests/agent/test_round_table_executor.py::test_sequential_submission_succeeds -x` | ❌ Wave 0 |
| INFRA-04 (SC#4) | 429 message contains "feedback-glm-overload-reduce-concurrency.md" substring | async unit | `pytest tests/agent/test_round_table_executor.py::test_429_message_cites_memory_md -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/agent/test_registry_loader.py tests/agent/test_round_table_state.py tests/agent/test_round_table_executor.py -x`
- **Per wave merge:** `pytest tests/agent/ -x` (full agent test suite)
- **Phase gate:** Full suite green + 4 INFRA-* SC tests passing before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/agent/test_registry_loader.py` — covers INFRA-01 (3 tests min: valid/malformed/name-mismatch)
- [ ] `tests/agent/test_round_table_state.py` — covers INFRA-03 (5 tests min: lifecycle + 3 crash recovery + atomic)
- [ ] `tests/agent/test_round_table_executor.py` — covers INFRA-04 (3 tests min: concurrent reject + sequential success + MEMORY.md citation substring)
- [ ] `tests/agent/test_mcp_serve_round_table.py` — covers INFRA-02 integration (3+ tests: agents_list / agent_describe / lifecycle round trip)
- [ ] `tests/agent/fixtures/agents/test-coordinator.agent.yaml` — minimal valid synthetic agent fixture
- [ ] `tests/agent/fixtures/agents/malformed.agent.yaml` — invalid YAML fixture for SC#1 negative test
- [ ] Verify pytest-asyncio mode is `auto` (or mark async tests with `@pytest.mark.asyncio` explicitly)

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

## Security Domain

> `security_enforcement` is not explicitly set in `.planning/config.json` — treat as enabled per protocol default.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | MCP transport is stdio (local) — no auth in scope |
| V3 Session Management | no | Round-table state is filesystem-scoped, not session-scoped |
| V4 Access Control | yes | Per-project state isolation (`{slug}/round_tables/`) — cross-project reference forbidden (06-CROSS-REPO-IMPACT §6.5). Validate `project_id` field rejects cross-project references. |
| V5 Input Validation | yes | `jsonschema.Draft202012Validator` on agent YAML (INFRA-01). All MCP tool args typed (str regex `^[a-z0-9_-]+$` for agent IDs). |
| V6 Cryptography | yes (sha256 only) | SHA-256 for `persona_sha256` + evolution_log chain — use `hashlib.sha256` (stdlib), never hand-roll. Mirror `agent/curator_audit.py` formula verbatim. |
| V7 Error Handling and Logging | yes | Lazy %-formatting in all log calls. Specific exception types. Schema-violation errors include field path for operator triage. |
| V8 Data Protection | yes | `~/.hermes/agents/.runtime/{slug}/round_tables/` is operator-private. `atomic_json_write` uses mkstemp (0o600 default). Do not log opinion content (may contain operator IP). |

### Known Threat Patterns for Phase 52 stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in `project_slug` (e.g. `../../etc/passwd`) | Tampering | Regex-validate `project_id` format (e.g. `^[a-zA-Z0-9_.:-]+`); reject `..` components before constructing `.runtime/{slug}/round_tables/{round_id}.json` path |
| Cross-project reference in state JSON | Information disclosure | Schema validation rejects `cross_project_references` field; runtime check on every state read |
| Concurrent state mutation race | Tampering | Per-`roundId` `asyncio.Lock` (INFRA-04); atomic_json_write's temp+rename guarantees no partial writes |
| Schema-validation bypass | Tampering | `additionalProperties: false` in agents-schema.yaml + round-table-state-schema.yaml — reject undeclared fields |
| Resource exhaustion (orphaned round tables accumulating) | DoS | Stall detection (Pitfall 4) + GC pass on read (deferred per 06-CROSS-REPO-IMPACT §6.4 GC note) |
| `name` field mismatch with filename (symlink attack) | Spoofing | INFRA-01 validates `name == filename.stem` — agents-schema.yaml §2.1 |

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** (this session): `utils.py`, `mcp_serve.py`, `agent/turn_retry_state.py`, `agent/glm_concurrency_guard.py`, `agent/curator_audit.py`, `gateway/session_context.py`, `plugins/memory/mem0/__init__.py`, `tests/conftest.py`, `tests/agent/test_audit_log.py`, `tests/agent/test_curator_feedback_scan.py`
- **`pyproject.toml`** — pinned versions for jsonschema, PyYAML, mcp, pydantic, pytest, pytest-asyncio
- **`uv.lock`** — confirmed jsonschema 4.26.0 installed
- **`.planning/research/v10-orchestrator-design/agents-schema.yaml`** — 18-field agent YAML schema (Draft 2020-12, `additionalProperties: false`)
- **`.planning/research/v10-orchestrator-design/round-table-state-schema.yaml`** — state machine schema (Draft 2020-12)
- **`.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md`** — 2-layer schema narrative (read full)
- **`.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` §5** — 7 MCP tool narrative contracts (read §5.0-§5.7)
- **`.planning/research/v10-orchestrator-design/05-POC-PLAN.md` §3.3 + §3.5 + §3.6** — infra vertical slice definition
- **`.planning/research/v10-orchestrator-design/06-CROSS-REPO-IMPACT.md` §5.1 + §6.1-§6.6** — `.runtime/{slug}/round_tables/` path + 3 crash recovery failure modes
- **`MEMORY.md` feedback-glm-overload-reduce-concurrency.md** — serial constraint policy (referenced in user memory)

### Secondary (MEDIUM confidence)
- **`.planning/phases/52-infra-foundation/52-CONTEXT.md`** — auto-generated CONTEXT.md (high confidence on intent, MEDIUM on tool-name list due to conflict with design suite)
- **`.planning/REQUIREMENTS.md`** INFRA-01..04 (high confidence on acceptance contract)
- **`json-schema.org/draft/2020-12/schema`** [CITED: json-schema.org] — Draft 2020-12 dialect

### Tertiary (LOW confidence)
- None — all claims verified against codebase or design suite

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already pinned + verified in uv.lock; zero new installs
- Architecture: HIGH — codebase patterns (`atomic_json_write`, FastMCP `@mcp.tool()`, `contextvars.ContextVar`) directly applicable; design suite locks schemas + paths
- Pitfalls: HIGH — most pitfalls are concrete codebase anti-patterns (top-level run_agent import, `Path.home()` bypass, threading.Lock in async)
- Tool names (INFRA-02): MEDIUM — design suite §5 conflicts with CONTEXT.md; flagged as Open Question #1
- State enum values (INFRA-03): MEDIUM — design suite has three different enums; flagged as Open Question #2
- Async lock pattern (INFRA-04): MEDIUM — `asyncio.Lock` is the textbook-correct primitive but FastMCP's exact dispatch model (pure-asyncio vs ThreadPoolExecutor-hybrid) needs Wave 0 probe test (Assumption A1)

**Research date:** 2026-07-07
**Valid until:** 2026-08-07 (30 days; the design suite is LOCKED so the recommendations are stable indefinitely, but the Open Questions need resolution within ~7 days to keep Phase 52 on track)

## RESEARCH COMPLETE

**Phase:** 52 - INFRA-FOUNDATION
**Confidence:** MEDIUM (HIGH on patterns; MEDIUM on two design-suite discrepancies that need user resolution)

### Key Findings
- **Zero new dependencies** — jsonschema 4.26.0, PyYAML, mcp 1.26.0, pydantic 2.13.4 all already pinned in pyproject.toml + uv.lock. Slopcheck gate not triggered.
- **Direct reuse of 4 existing patterns**: `utils.atomic_json_write` (utils.py:111), FastMCP `@mcp.tool()` decorator (mcp_serve.py:471-831), `contextvars.ContextVar` (gateway/session_context.py:39), dataclass state machine (agent/turn_retry_state.py:33).
- **asyncio.Lock is the correct primitive for INFRA-04** (not threading.Semaphore — that's for blocking SDK calls like GLM guard). Distinct from `agent/glm_concurrency_guard.py`; they compose.
- **Three naming/enum discrepancies between CONTEXT.md and v10.0 design suite** — flagged as Open Questions #1 (tool names), #2 (state enum), #3 (round_table_open deferral). Recommend treating design suite as authoritative; planner should add a `checkpoint:human-verify` task to confirm before implementation.
- **Crash recovery is mostly free** — `atomic_json_write`'s temp+fsync+rename guarantees partial-write recovery by construction. Only mid-turn crash + orphaned session need active recovery (stall detection on read).

### File Created
`/data/workspace/hermes-agent/.planning/phases/52-infra-foundation/52-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | All packages verified in uv.lock + pyproject.toml; zero new installs |
| Architecture | HIGH | 4 existing codebase patterns directly applicable; design suite locks schemas + paths |
| Pitfalls | HIGH | 8 pitfalls identified, all concrete codebase anti-patterns with specific file:line citations |
| INFRA-02 tool names | MEDIUM | Open Question #1 — CONTEXT.md vs design suite §5 conflict; design suite more authoritative |
| INFRA-03 state enum | MEDIUM | Open Question #2 — three different enums across design docs; schema YAML most authoritative |
| INFRA-04 async lock | MEDIUM | asyncio.Lock textbook-correct for FastMCP, but Assumption A1 needs Wave 0 probe |

### Open Questions
1. **Tool names — CONTEXT.md list or 02-ROUND-TABLE-PROTOCOL.md §5 list?** (HIGH risk if wrong — breaks Phase 53-55)
2. **State enum — CONTEXT.md `in_progress/closed` or schema YAML `open/completed/aborted/stalled`?** (MEDIUM risk)
3. **`round_table_open` in Phase 52 or v11.1+?** — SC#2/SC#3 require it; §5.0 deferral comment is stale
4. **`agent_describe` separate tool or `get_agent_persona` alias?** (LOW risk)
5. **Memory tools as stubs or working?** — Recommend stubs; Phase 53 does real mem0 routing

### Ready for Planning
Research complete. Planner can now create PLAN.md files. **Strong recommendation:** planner inserts a `checkpoint:human-verify` task at the start of Wave 0 to resolve Open Questions #1, #2, #3 with Kai before any code is written — they are load-bearing for tool naming and state serialization.
