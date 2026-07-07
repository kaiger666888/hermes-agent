# Phase 52: INFRA-FOUNDATION - Pattern Map

**Mapped:** 2026-07-07
**Files analyzed:** 11 new/modified files
**Analogs found:** 9 / 11 (2 partial — async lock primitive + memory arbitration stub are genuinely new)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `agent/registry_loader.py` | service | file-I/O + transform | `agent/skill_utils.py` (frontmatter parse) + `agent/plugin_llm.py` (jsonschema) | exact (role + flow) |
| `agent/round_table_state.py` | model + service | file-I/O (atomic) + state machine | `agent/turn_retry_state.py` (dataclass state) + `utils.py:atomic_json_write` (persistence) | exact (both halves) |
| `agent/round_table_executor.py` | service | request-response + concurrency control | `gateway/session_context.py` (contextvars) + `agent/glm_concurrency_guard.py` (negative — wrong primitive) | partial (new asyncio.Lock idiom; glm guard is the negative example) |
| `agent/memory_arbitration.py` | service (stub) | request-response | `gateway/session_context.py` (contextvars primitive) | partial (stub-only; real mem0 routing is Phase 53) |
| `mcp_serve.py` (modified) | controller | request-response | `mcp_serve.py:471-831` (9 existing `@mcp.tool()` tools) | exact (extending same file) |
| `tests/agent/test_registry_loader.py` | test | unit | `tests/agent/test_audit_log.py` (tmp_path + monkeypatch + HERMES_HOME) | exact |
| `tests/agent/test_round_table_state.py` | test | unit (incl. crash recovery) | `tests/agent/test_audit_log.py` (atomic + chain recovery) | exact |
| `tests/agent/test_round_table_executor.py` | test | async unit (concurrency) | `tests/test_trajectory_compressor.py:495` (`@pytest.mark.asyncio`) | role-match |
| `tests/agent/test_mcp_serve_round_table.py` | test | integration | `tests/agent/test_audit_log.py` (module boundary) | role-match |
| `tests/agent/fixtures/agents/*.agent.yaml` | fixture | declarative | `.planning/research/v10-orchestrator-design/agents-schema.yaml` (consumed schema) | exact |
| `tests/agent/fixtures/agents/malformed.agent.yaml` | fixture | declarative (negative) | `tests/fixtures/curator/audit_chain_tampered.jsonl` (negative fixture) | role-match |

## Pattern Assignments

### `agent/registry_loader.py` (service, file-I/O + schema validation)

**Analogs:** `agent/skill_utils.py` (YAML loading) + `agent/curator_audit.py` (schema-validated module) + `agent/plugin_llm.py:474` (jsonschema usage — referenced from RESEARCH.md)

**Imports pattern** — mirror `agent/curator_audit.py:42-55` (canonical "registry-style" module header):
```python
# Source: agent/curator_audit.py:42-55
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)
```
- `from __future__ import annotations` — required per CLAUDE.md for PEP 604 syntax on Python 3.11.
- `from hermes_constants import get_hermes_home` — **NEVER** `Path.home() / ".hermes"`.
- Add `import jsonschema`, `import yaml` (both already pinned in pyproject.toml).

**YAML parsing pattern** — copy structure from `agent/skill_utils.py:100-117` (lazy CSafeLoader):
```python
# Source: agent/skill_utils.py:100-117
_yaml_load_fn = None

def yaml_load(content: str):
    """Parse YAML with lazy import and CSafeLoader preference."""
    global _yaml_load_fn
    if _yaml_load_fn is None:
        import yaml
        loader = getattr(yaml, "CSafeLoader", None) or yaml.SafeLoader
        def _load(value: str):
            return yaml.load(value, Loader=loader)
        _yaml_load_fn = _load
    return _yaml_load_fn(content)
```
**What to copy:** lazy-import + CSafeLoader-preference idiom. **What to adapt:** agent YAMLs are flat (not frontmatter+body), so just `yaml.safe_load(open(path))` is sufficient — no need for the `---\n---` splitter in `parse_frontmatter`.

**Schema validation pattern** — from RESEARCH.md §"YAML Loader Pattern" (concrete excerpt, sources `agent/plugin_llm.py:474` + jsonschema docs):
```python
# Adapted from RESEARCH.md §Code Examples (lines 524-560)
_SCHEMA_CACHE: dict[str, Any] | None = None

def _get_validator() -> jsonschema.Draft202012Validator:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = _load_schema()  # reads agents-schema.yaml from .planning/research/v10-orchestrator-design/
    return jsonschema.Draft202012Validator(_SCHEMA_CACHE)

def load_one_agent_yaml(yaml_path: Path) -> dict[str, Any]:
    """Load + validate a single agent YAML. Raises RegistryValidationError."""
    with open(yaml_path, encoding="utf-8") as f:  # encoding= is Ruff PLW1514
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise RegistryValidationError(
                f"{yaml_path}: invalid YAML syntax: {exc}"
            ) from exc

    validator = _get_validator()
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        first = errors[0]
        path = "$" + "".join(f"[{repr(p)}]" for p in first.absolute_path)
        raise RegistryValidationError(
            f"{yaml_path}: schema violation at {path}: {first.message}"
        )

    # SC#1: verify name matches filename stem (agents-schema.yaml §2.1)
    expected_stem = yaml_path.name.removesuffix(".agent.yaml")
    if data.get("name", "") != expected_stem:
        raise RegistryValidationError(
            f"{yaml_path}: name field {data.get('name')!r} does not match "
            f"filename stem {expected_stem!r}"
        )
    return data
```

**Lazy cache pattern** — mirror `agent/i18n.py:83-84` + `agent/skill_utils.py:_EXTERNAL_DIRS_CACHE`:
```python
# Adapted from RESEARCH.md §Pattern 3 (lines 308-330)
_REGISTRY_CACHE: list[dict[str, Any]] | None = None
_REGISTRY_CACHE_LOCK = threading.Lock()  # stdlib, no extra dep

def load_agent_registry(*, force_reload: bool = False) -> list[dict[str, Any]]:
    """Lazy-load + validate ~/.hermes/agents/*.agent.yaml. Cached process-wide."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and not force_reload:
        return _REGISTRY_CACHE
    with _REGISTRY_CACHE_LOCK:
        if _REGISTRY_CACHE is not None and not force_reload:
            return _REGISTRY_CACHE
        agents_dir = get_hermes_home() / "agents"
        entries = []
        if agents_dir.is_dir():
            # FLAT layout — NOT nested like skills/ (Pitfall #8)
            for yaml_path in sorted(agents_dir.glob("*.agent.yaml")):
                entries.append(load_one_agent_yaml(yaml_path))
        _REGISTRY_CACHE = entries
        return entries
```

**File iteration pattern** — mirror `agent/skill_utils.py:696-717` (`iter_skill_index_files`) but simplified for flat layout:
```python
# Source: agent/skill_utils.py:696-717 (nested walk) — Phase 52 uses flat glob instead
# DO NOT walk recursively; agents live flat at ~/.hermes/agents/{name}.agent.yaml
for yaml_path in sorted(agents_dir.glob("*.agent.yaml")):
    ...
```

---

### `agent/round_table_state.py` (model + service, file-I/O + state machine)

**Analogs:** `agent/turn_retry_state.py` (dataclass-as-state) + `utils.py:atomic_json_write` (persistence) + `agent/curator_audit.py` (sha256 chain reference)

**Dataclass state pattern** — copy `agent/turn_retry_state.py:32-79`:
```python
# Source: agent/turn_retry_state.py:27-33, 76-79
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum

@dataclass
class TurnRetryState:
    """One-shot recovery guards for a single API-call attempt."""
    codex_auth_retry_attempted: bool = False
    # ... fields ...
    consecutive_overloaded: int = 0

    def __iter__(self):
        # Convenience for debugging / tests: iterate (name, value) pairs.
        for f in fields(self):
            yield f.name, getattr(self, f.name)
```
**What to copy:** `from __future__ import annotations` + `@dataclass` + default factory for mutable fields + `__iter__` test helper. **What to adapt:** add `RoundTableStatus(str, Enum)` per `round-table-state-schema.yaml:127-141`.

**State enum pattern** — values locked by `round-table-state-schema.yaml:127-141`:
```python
# Authority: .planning/research/v10-orchestrator-design/round-table-state-schema.yaml:127-141
class RoundTableStatus(str, Enum):
    # DO NOT add in_progress or closed — those are CONTEXT.md shorthand;
    # round-table-state-schema.yaml is authoritative (CONTEXT.md "Resolved by Kai" point 2).
    OPEN = "open"
    COMPLETED = "completed"
    ABORTED = "aborted"
    STALLED = "stalled"
```

**Atomic persistence pattern** — direct call to `utils.py:111-177`:
```python
# Source: utils.py:111-177 atomic_json_write — DO NOT reinvent
from utils import atomic_json_write

def _persist_state(state_path: Path, state_dict: dict[str, Any]) -> None:
    """Crash-safe write: temp + fsync + os.replace.
    If process crashes mid-write, the previous file remains intact.
    """
    atomic_json_write(state_path, state_dict, indent=2)
```
**Why this is the recovery:** `atomic_json_write`'s temp+fsync+rename contract handles failure mode (a) partial-write corruption by construction (see `utils.py:121-123` docstring). Only failure modes (b) mid-turn crash + (c) orphaned session need active recovery (stall detection on read).

**Crash recovery read-time pattern** — from RESEARCH.md §"Crash Recovery Read-Time Pattern" (lines 691-733):
```python
# Adapted from RESEARCH.md (lines 694-733) + atomic_json_write guarantee
def read_and_recover_state(state_path: Path, *, stall_threshold_minutes: int = 30) -> dict[str, Any]:
    """Read state file + apply 3 failure-mode recovery (06-CROSS-REPO-IMPACT.md §6.4)."""
    if not state_path.exists():
        raise FileNotFoundError(state_path)

    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except json.JSONDecodeError as exc:
        # Failure (a) defense-in-depth: archive corrupt file, raise
        archive = state_path.with_suffix(".json.corrupt")
        state_path.rename(archive)
        logger.error("round_table_state corrupt, archived to %s: %s", archive, exc)
        raise

    # Failure (b)/(c): stall detection
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

**sha256 chain pattern** (for `personaSnapshots` and any evolution_log carried forward) — mirror `agent/curator_audit.py:102-132`:
```python
# Source: agent/curator_audit.py:102-132
def _serialize_entry_for_sha256(entry: dict[str, Any]) -> str:
    """Canonical JSON for sha256 — sort_keys + compact + ensure_ascii=False."""
    payload = {k: v for k, v in entry.items() if k != "entry_sha256"}
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )

def _compute_entry_sha256(prev_sha256: str, entry: dict[str, Any]) -> str:
    payload = _serialize_entry_for_sha256(entry)
    return hashlib.sha256((prev_sha256 + payload).encode("utf-8")).hexdigest()
```
**What to copy verbatim:** both helpers + the `ensure_ascii=False` invariant (Pitfall #8 in `curator_audit.py`). Drift detection / persona drift uses the same canonicalization.

---

### `agent/round_table_executor.py` (service, concurrency control)

**Analogs:** `gateway/session_context.py:39` (contextvars) + `agent/glm_concurrency_guard.py` (NEGATIVE example — wrong primitive for this layer)

**Per-`roundId` asyncio.Lock pattern** — new idiom, RESEARCH.md §Pattern 2 (lines 266-301):
```python
# Adapted from RESEARCH.md §Pattern 2 + gateway/session_context.py contextvars idiom
import asyncio
import json
from contextvars import ContextVar
from typing import Optional

# Module-level registry of per-roundId locks.
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
    """Try to acquire per-roundId lock; return None if contended.
    SC#4 mandates REJECTION (not queueing) of concurrent calls.
    """
    lock = await _get_or_create_round_lock(round_id)
    # Check-then-acquire. Under asyncio cooperative scheduling, no other task
    # runs between this point and `await lock.acquire()` because there's no
    # await in between (Pitfall #2 in RESEARCH.md).
    if lock.locked():
        return None
    await lock.acquire()
    return lock
```

**NEGATIVE example — do NOT copy** from `agent/glm_concurrency_guard.py:196-221`. This module's docstring (lines 11-15) explicitly states the distinction:
```python
# Source: agent/glm_concurrency_guard.py:11-15 (the design note explaining WHY it uses threading.Semaphore)
# * **Why threading.Semaphore, not asyncio**: the OpenAI SDK call inside
#   ``_perform_api_call`` blocks the calling thread even under the gateway's
#   asyncio loop. ThreadPoolExecutor workers (``delegate_task`` subagents)
#   and asyncio-thread callers all share this process-wide semaphore.
```
**The distinction (load-bearing):** `glm_concurrency_guard` throttles *blocking SDK calls* (thread-layer). Phase 52's `round_table_executor` serializes *async MCP tool entry* (event-loop layer). They compose — `get_agent_opinion` acquires the asyncio.Lock first, then the LLM call inside goes through `acquire_glm_slot`. Do NOT collapse them.

**Contextvars primitive** — `_scoped_agent_id` per ARCHITECTURE §3.3, mirror `gateway/session_context.py:39-83`:
```python
# Source: gateway/session_context.py:39-62, 86-98
from contextvars import ContextVar
_UNSET: Any = object()  # sentinel

_SCOPED_AGENT_ID: ContextVar = ContextVar("HERMES_SCOPED_AGENT_ID", default=_UNSET)

def set_scoped_agent_id(agent_id: str) -> None:
    """Set the current task's scoped agent_id for memory routing."""
    _SCOPED_AGENT_ID.set(agent_id)

def get_scoped_agent_id() -> str | None:
    """Read the current task's scoped agent_id; None if unset."""
    val = _SCOPED_AGENT_ID.get()
    return None if val is _UNSET else str(val)
```
**Why contextvars, not threading.local:** ThreadPoolExecutor worker reuse makes `threading.local` leak scope across tasks; `contextvars` is asyncio-correct. (Per RESEARCH.md "Don't Hand-Roll" + ARCHITECTURE §3.3.)

---

### `agent/memory_arbitration.py` (service — Phase 52 ships STUB)

**Analog:** `gateway/session_context.py` (contextvars primitive) + `plugins/memory/mem0/__init__.py` (Phase 53 target — DO NOT import in Phase 52)

**Module purpose:** (1) Expose `_scoped_agent_id` contextvar wrappers (lives here, not in `round_table_executor.py`, because memory routing is cross-cutting); (2) provide the two MCP-tool-callable functions as **stubs** that return `phase53_not_implemented` status.

**Stub return contract** — from CONTEXT.md "Resolved by Kai" point 3:
```python
# Locked by CONTEXT.md "Resolved by Kai" point 3 (2026-07-07)
# Phase 53 (CREATIVE-SLICE) fills in real mem0 backend routing.

async def memory_retrieve_scoped(query: str, agent_id: str, *, top_k: int = 5) -> dict[str, Any]:
    """STUB. Returns phase53_not_implemented. Phase 53 wires mem0 routing."""
    return {"status": "phase53_not_implemented", "hits": []}

async def memory_submit_record(
    agent_id: str, content: str, *, scope: str = "per_agent", confidence: float = 0.5,
) -> dict[str, Any]:
    """STUB. Returns phase53_not_implemented with null record_id."""
    return {"status": "phase53_not_implemented", "record_id": None}
```

**What NOT to do:** Do NOT import `plugins.memory.mem0` at module top. Per RESEARCH.md Pitfall #5 — that path's `is_available()` returns False without `MEM0_API_KEY`, but eager import still couples Phase 52 to a Phase 53 backend.

---

### `mcp_serve.py` (modified — controller)

**Analog:** `mcp_serve.py:450-465` (`create_mcp_server` factory) + `mcp_serve.py:471-524` (`conversations_list` — first tool) + `mcp_serve.py:775-827` (`channels_list` — registry-style browse tool)

**Factory pattern** — extend inside `create_mcp_server()`:
```python
# Source: mcp_serve.py:450-465
def create_mcp_server(event_bridge: Optional[EventBridge] = None) -> "FastMCP":
    """Create and return the Hermes MCP server with all tools registered."""
    if not _MCP_SERVER_AVAILABLE:
        raise ImportError(...)

    mcp = FastMCP(
        "hermes",
        instructions=(...),
    )
    bridge = event_bridge or EventBridge()

    # ... 9 existing tools (lines 471-831) ...

    # ── v11.0 round-table tools (Phase 52 INFRA-02) ───────────────────────
    # ADD 7 new @mcp.tool() closures here, following the same form.
```

**`@mcp.tool()` decorator form** — copy from `mcp_serve.py:471-524`:
```python
# Source: mcp_serve.py:471-524 (canonical tool form)
@mcp.tool()
def conversations_list(
    platform: Optional[str] = None,
    limit: int = 50,
    search: Optional[str] = None,
) -> str:
    """List active messaging conversations across connected platforms.

    Returns conversations with their session keys (needed for messages_read),
    platform, chat type, display name, and last activity time.

    Args:
        platform: Filter by platform name (telegram, discord, slack, etc.)
        limit: Maximum number of conversations to return (default 50)
        search: Optional text to filter conversations by name
    """
    limit = _coerce_int(limit, default=50, minimum=1, maximum=200)
    entries = _load_sessions_index()
    # ... business logic ...
    return json.dumps({
        "count": len(conversations),
        "conversations": conversations,
    }, indent=2)
```

**What to copy verbatim:**
1. `@mcp.tool()` decorator on a closure defined inside `create_mcp_server`.
2. Synchronous `def` (not `async def`) for state-mutation-free tools like `agents_list` / `agent_describe` — they delegate to `registry_loader` (sync).
3. **`async def` for `round_table_open` / `submit_round_table_result` / `get_agent_opinion`** — these touch `asyncio.Lock` in `round_table_executor`. FastMCP supports both forms.
4. Docstring with `Args:` section (MCP uses this for tool description surface).
5. Always return `str` (JSON-serialized). Errors as `json.dumps({"error": "...", "detail": str(exc)})`.
6. Lazy-import `agent.*` modules inside the closure body to avoid import cycles at `mcp_serve` startup (mirrors `mcp_serve.py:765` `from tools.send_message_tool import send_message_tool` pattern).

**Concrete new tool skeleton — `agents_list`** (registry-browse, mirrors `channels_list` at `mcp_serve.py:775-827`):
```python
# Adapted from mcp_serve.py:775-827 channels_list + RESEARCH.md §"MCP Tool Registration Pattern"
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

**Concrete new tool skeleton — `get_agent_opinion` (async, lock-guarded):**
```python
# Adapted from RESEARCH.md §Pattern 2 + mcp_serve.py async-tool idiom
@mcp.tool()
async def get_agent_opinion(
    round_id: str, agent_id: str, topic: str, panel_context: Optional[str] = None,
) -> str:
    """Get one panelist's opinion on a topic within an open round table.

    Serial invariant: concurrent calls against the same roundId are rejected
    with 429 + MEMORY.md citation.

    Args:
        round_id: The roundId from round_table_open
        agent_id: The panelist's agent name (~/.hermes/agents/{name}.agent.yaml)
        topic: Topic/question this turn addresses
        panel_context: Optional prior-turn context for the panelist
    """
    from agent.round_table_executor import acquire_round_or_reject, _serial_violation_response
    lock = await acquire_round_or_reject(round_id)
    if lock is None:
        return _serial_violation_response(round_id)
    try:
        # ... actual opinion dispatch (Phase 53 fills in LLM call) ...
        # Phase 52: return placeholder + append turn to state file
        return json.dumps({
            "round_id": round_id, "agent_id": agent_id,
            "opinion": "[phase52_placeholder]",
            "status": "ok",
        }, indent=2)
    finally:
        lock.release()
```

**Tool name list — CONTEXT.md `agents_list / agent_describe / round_table_open / submit_round_table_result / get_agent_opinion / memory_retrieve_scoped / memory_submit_record` is authoritative for v11.0 PoC** (CONTEXT.md "Resolved by Kai" point 1 supersedes `02-ROUND-TABLE-PROTOCOL.md §5`).

---

### `tests/agent/test_registry_loader.py` (test, unit)

**Analog:** `tests/agent/test_audit_log.py:34-90` (canonical agent-module test header)

**Test file pattern** — copy header + fixture style:
```python
# Source: tests/agent/test_audit_log.py:14-37, 78-90
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agent.registry_loader import (
    load_agent_registry,
    load_one_agent_yaml,
    RegistryValidationError,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"
VALID_FIXTURE = FIXTURES_DIR / "test-coordinator.agent.yaml"
MALFORMED_FIXTURE = FIXTURES_DIR / "malformed.agent.yaml"


class TestValidYamlLoading:
    def test_valid_yaml_loads_and_validates(self, tmp_path, monkeypatch):
        # _hermetic_environment (autouse) already redirects HERMES_HOME.
        # Drop fixture into the redirected ~/.hermes/agents/ and call loader.
        agents_dir = tmp_path / "hermes_test" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "test-coordinator.agent.yaml").write_text(
            VALID_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8",
        )
        entries = load_agent_registry()
        assert len(entries) == 1
        assert entries[0]["name"] == "test-coordinator"


class TestMalformedYamlRejection:
    def test_malformed_yaml_rejected_with_field_path(self, tmp_path):
        # SC#1: schema-violation error must include specific field path.
        ...
```

**What to copy verbatim:**
- `from __future__ import annotations`
- `import pytest`
- `FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"` — fixture layout convention.
- Class-based test grouping (`class TestXxx:`) per CLAUDE.md.
- `_hermetic_environment` autouse fixture (in `tests/conftest.py:327`) already redirects `HERMES_HOME` to `tmp_path / "hermes_test"` — **no manual env var manipulation needed**; just create files under the redirected home via `tmp_path`-relative paths.

---

### `tests/agent/test_round_table_state.py` (test, unit + crash recovery)

**Analog:** `tests/agent/test_audit_log.py` (atomic write + chain-recovery test idiom)

**Crash recovery test skeletons (3 failure modes per RESEARCH.md SC#3a/b/c):**
```python
class TestCrashRecovery:
    def test_partial_write_recovery_defense_in_depth(self, tmp_path):
        # SC#3a: corrupt file → archived, raises, doesn't crash loader.
        state_path = tmp_path / "round.json"
        state_path.write_text("{ broken json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            read_and_recover_state(state_path)
        assert state_path.with_suffix(".json.corrupt").exists()

    def test_mid_turn_crash_recovers_via_stall(self, tmp_path, monkeypatch):
        # SC#3b: status=open + lastUpdatedAt old → status=stalled on read.
        ...

    def test_orphaned_session_recovers_on_next_read(self, tmp_path):
        # SC#3c: same recovery path as (b).
        ...

    def test_interrupted_submit_no_in_progress(self, tmp_path):
        # SC#2 contract: NEVER serialize status=in_progress — that value
        # isn't in round-table-state-schema.yaml enum (CONTEXT.md point 2).
        ...
```

---

### `tests/agent/test_round_table_executor.py` (test, async unit)

**Analog:** `tests/test_trajectory_compressor.py:495` (`@pytest.mark.asyncio` pattern)

**Async test pattern:**
```python
# Source: tests/test_trajectory_compressor.py:495-499 (canonical async test marker)
import pytest

class TestSerialEnforcement:
    @pytest.mark.asyncio
    async def test_concurrent_submission_rejected(self):
        """SC#4: concurrent get_agent_opinion for same roundId → 429 + MEMORY.md citation."""
        from agent.round_table_executor import acquire_round_or_reject, _serial_violation_response
        # Acquire the lock first
        lock1 = await acquire_round_or_reject("round-1")
        assert lock1 is not None
        # Second attempt must be rejected
        lock2 = await acquire_round_or_reject("round-1")
        assert lock2 is None
        lock1.release()

    @pytest.mark.asyncio
    async def test_429_message_cites_memory_md(self):
        """SC#4 substring check."""
        from agent.round_table_executor import _serial_violation_response
        msg = _serial_violation_response("round-x")
        assert "feedback-glm-overload-reduce-concurrency.md" in msg
        assert "429" in msg
```

**Note:** pytest-asyncio mode is **not** `auto` (no `asyncio_mode` setting found in `pyproject.toml`); **explicit `@pytest.mark.asyncio` is required** on every async test (verified via grep — every existing async test uses the marker).

---

### `tests/agent/test_mcp_serve_round_table.py` (test, integration)

**Analog:** `tests/agent/test_audit_log.py` (module boundary) + `mcp_serve.py` factory call pattern

**Integration test pattern:**
```python
# Pattern: call create_mcp_server() with a fake EventBridge, invoke tool closures via FastMCP's test client.
class TestMcpRoundTableIntegration:
    def test_agents_list_returns_json(self, tmp_path):
        # Setup: drop fixture agent YAML into redirected HERMES_HOME
        ...
        # Invoke: create_mcp_server(fake_bridge) returns FastMCP; call .tools dict
        # OR: import the inner closure directly via test inspection.
        ...
```

**Live-system guard warning (Pitfall #7):** the autouse `_live_system_guard` fixture (`tests/conftest.py:539`) AST-inspects test functions for `os.kill` / `subprocess.run`. Mock at the test boundary — inject a fake `EventBridge` — or mark genuinely-needed integration tests with `@pytest.mark.live_system_guard_bypass`.

---

### `tests/agent/fixtures/agents/*.agent.yaml` (fixtures)

**Analog:** `.planning/research/v10-orchestrator-design/agents-schema.yaml` (consumed schema)

**Minimal valid fixture** — derive from schema required-fields list (`agents-schema.yaml:41`):
```yaml
# tests/agent/fixtures/agents/test-coordinator.agent.yaml
# Schema: .planning/research/v10-orchestrator-design/agents-schema.yaml
name: test-coordinator            # required, must match filename stem
description: "Test coordinator agent for unit tests."   # minLength: 10
version: "1.0.0"                  # semver pattern
persona: "I am a test coordinator. I orchestrate unit-test fixtures."
tools: [read_file]                # minItems: 1
memory_scope: per_agent           # enum: shared | per_agent | project_scoped
lineage:
  derived_from_skill_id: test-coordinator-skill
  derived_from_repo: tests
  transform_date: 2026-07-07
  skill_sha256: "0000000000000000000000000000000000000000000000000000000000000000"
tags: [test-fixture]
```

**Malformed fixture** — for SC#1 negative test:
```yaml
# tests/agent/fixtures/agents/malformed.agent.yaml
# Deliberately missing required `persona` field + wrong type on `tools`.
name: malformed
description: "Has schema violations"
version: "not-semver"             # violates ^[0-9]+\.[0-9]+\.[0-9]+$
tools: "should-be-array"          # wrong type
memory_scope: invalid_scope       # not in enum
lineage:
  derived_from_skill_id: x
  derived_from_repo: x
  transform_date: "2026-07-07"
  skill_sha256: "short"           # violates ^[a-f0-9]{64}$
```

---

## Shared Patterns

### Atomic File Writes
**Source:** `utils.py:111-177` (`atomic_json_write`) + `utils.py:180-229` (`atomic_yaml_write`)
**Apply to:** All write paths in `agent/round_table_state.py` (every state mutation: open / turn-append / submit / stall-flip).
```python
# utils.py:111-134 (the contract)
def atomic_json_write(path, data, *, indent=2, mode=None, **dump_kwargs):
    """Write JSON data to a file atomically.
    Uses temp file + fsync + os.replace to ensure the target file is never
    left in a partially-written state. If the process crashes mid-write,
    the previous version of the file remains intact.
    """
```
**Rule:** NEVER call `open(path, "w")` directly for state writes. ALWAYS go through `atomic_json_write`. This is the entire defense for SC#3a (partial-write recovery).

### HERMES_HOME Resolution
**Source:** `hermes_constants.get_hermes_home()` + `tests/conftest.py:327-394`
**Apply to:** `agent/registry_loader.py` (read `~/.hermes/agents/`), `agent/round_table_state.py` (read/write `.runtime/{slug}/round_tables/`).
```python
# CORRECT — from agent/curator_audit.py:54 + 95-99
from hermes_constants import get_hermes_home

def _audit_log_path() -> Path:
    path = get_hermes_home() / "skills" / ".audit" / "log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
```
**FORBIDDEN:** `Path.home() / ".hermes"` — bypasses the conftest fixture redirect and leaks into real `~/.hermes` (per CLAUDE.md anti-pattern + RESEARCH.md Pitfall).

### Error Handling (specific exceptions + bound name)
**Source:** CLAUDE.md "Error Handling" + `agent/i18n.py:143-147` + `utils.py:277-280`
**Apply to:** Every `except` in every new file.
```python
# Pattern: bind with `as exc`, log with lazy %-formatting, re-raise with `from`
try:
    data = yaml.safe_load(f)
except yaml.YAMLError as exc:
    raise RegistryValidationError(f"{path}: invalid YAML: {exc}") from exc
```
**FORBIDDEN:** bare `except:`, swallowing without `as exc`, f-strings in `logger.x(...)` calls.

### Lazy %-Formatting in Logging
**Source:** CLAUDE.md "Logging" + pervasive codebase pattern
**Apply to:** Every `logger.x(...)` call in new modules.
```python
# CORRECT — args positional
logger.warning("agents_list: registry load failed: %s", exc)
# FORBIDDEN — f-string in log call
logger.warning(f"agents_list: registry load failed: {exc}")  # Ruff will not catch this; PR review must.
```

### Live-System Guard (test-only)
**Source:** `tests/conftest.py:539` (`_live_system_guard`) + CLAUDE.md anti-patterns
**Apply to:** `tests/agent/test_mcp_serve_round_table.py` (any test calling `create_mcp_server`).
- Mock at the test boundary (fake `EventBridge`, mock `hermes_state.SessionDB`).
- If a test legitimately needs live `os.kill` / `subprocess.run(["systemctl", ...])`, mark it `@pytest.mark.live_system_guard_bypass`.

### utf-8 Encoding on Every `open()`
**Source:** CLAUDE.md "Code Style" (Ruff PLW1514) + every codebase example
**Apply to:** Every `open()` in new modules AND test fixtures.
```python
# CORRECT
with open(path, encoding="utf-8") as f:
    ...
# FORBIDDEN — Ruff PLW1514 blocks the merge
with open(path, "w") as f:
    ...
```
`atomic_json_write` / `atomic_yaml_write` handle encoding correctly internally — prefer those over raw `open()` whenever the payload is JSON/YAML.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `agent/round_table_executor.py` (asyncio.Lock primitive) | service | concurrency control | Codebase has `threading.Semaphore` (`agent/glm_concurrency_guard.py`) for blocking SDK calls, but NO existing `asyncio.Lock` pattern for in-event-loop serialization. RESEARCH.md Pattern 2 (lines 266-301) provides the idiom; this is genuinely new code. |
| `agent/memory_arbitration.py` (mem0 backend routing) | service (stub) | request-response | No existing per-agent memory backend exists; mem0 plugin (`plugins/memory/mem0/__init__.py`) is global-`user_id`-only. Phase 52 ships STUB returning `phase53_not_implemented`; Phase 53 fills in routing per CONTEXT.md "Resolved by Kai" point 3. |

## Metadata

**Analog search scope:**
- `agent/*.py` (full scan — `curator_audit.py`, `turn_retry_state.py`, `skill_utils.py`, `glm_concurrency_guard.py`, `i18n.py`, `plugin_llm.py` referenced)
- `gateway/session_context.py` (contextvars pattern)
- `mcp_serve.py` (MCP factory + 9 existing tools)
- `utils.py` (atomic_*_write helpers)
- `tests/conftest.py` (autouse fixtures — `_hermetic_environment`, `_live_system_guard`)
- `tests/agent/test_audit_log.py` (canonical agent-module test header)
- `tests/test_trajectory_compressor.py` (async test marker)
- `.planning/research/v10-orchestrator-design/{agents-schema,round-table-state-schema}.yaml` (consumed schemas)

**Files scanned:** 11
**Pattern extraction date:** 2026-07-07

**Key design authorities (cite, do not re-derive):**
- `agents-schema.yaml` — 18 fields, camelCase keywords, `additionalProperties: false`.
- `round-table-state-schema.yaml` — state enum `open | completed | aborted | stalled` (NOT `in_progress | closed`).
- CONTEXT.md "Resolved by Kai" points 1-3 — overrides stale parts of `02-ROUND-TABLE-PROTOCOL.md §5`.
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` — serial-constraint policy citation (must appear verbatim in `_serial_violation_response`).

## PATTERN MAPPING COMPLETE

**Phase:** 52 - INFRA-FOUNDATION
**Files classified:** 11
**Analogs found:** 9 / 11 (2 partial — asyncio.Lock primitive + memory_arbitration stub)

### Coverage
- Files with exact analog: 7 (registry_loader, round_table_state, mcp_serve modification, 4 test files, 2 fixture families)
- Files with role-match analog: 2 (test_round_table_executor async pattern via test_trajectory_compressor; fixture from schema)
- Files with no analog: 2 (asyncio.Lock idiom is genuinely new; memory_arbitration is intentional Phase 53 stub)

### Key Patterns Identified
- **Atomic write via `utils.atomic_json_write`** — single reuse, covers SC#3a partial-write recovery by construction.
- **Lazy-cache registry pattern** — `_REGISTRY_CACHE + threading.Lock` double-checked idiom (mirrors `agent/i18n.py` + `agent/skill_utils.py:_EXTERNAL_DIRS_CACHE`).
- **`@mcp.tool()` decorator inside `create_mcp_server()`** — 7 new closures extend the 9 existing tools; lazy-import `agent.*` inside closure body.
- **`asyncio.Lock` per-roundId (NEW primitive)** — distinct from `agent/glm_concurrency_guard.py`'s `threading.Semaphore`; the two layers compose. Check-then-acquire idiom avoids Pitfall #2 TOCTOU under asyncio cooperative scheduling.
- **Dataclass state + Enum** — `RoundTableStatus(str, Enum)` mirrors `agent/turn_retry_state.py` + `agent/error_classifier.py:FailoverReason` patterns; values locked by `round-table-state-schema.yaml`.
- **HERMES_HOME via `get_hermes_home()`** — never `Path.home() / ".hermes"`; conftest fixture handles per-test redirection.
- **`@pytest.mark.asyncio` explicit** — pytest-asyncio mode is NOT `auto`; every async test needs the marker.

### File Created
`/data/workspace/hermes-agent/.planning/phases/52-infra-foundation/52-PATTERNS.md`

### Ready for Planning
Pattern mapping complete. Planner can reference concrete analog file paths + line ranges + code excerpts in PLAN.md action sections. Two genuine novelties (asyncio.Lock idiom, memory stub) are flagged with RESEARCH.md idiom references for the planner to fall back on.
