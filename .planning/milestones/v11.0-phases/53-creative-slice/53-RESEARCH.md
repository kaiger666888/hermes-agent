# Phase 53: CREATIVE-SLICE - Research

**Researched:** 2026-07-07
**Domain:** Hermes-native expert agents — SKILL→agent YAML transform, 9-agent round table lifecycle, memory conflict arbitration
**Confidence:** HIGH

## Summary

Phase 53 is the **creative vertical slice** of v11.0: it transforms 9 sample movie-expert SKILL.md files into agent YAMLs, drives a real GLM-powered screenplay Step 3 round table end-to-end through 7 MCP tools shipped by Phase 52, and fills in the conflict-arbitration runtime (currently stubs). All design decisions are locked by v10.0 (Phase 44-51) and CONTEXT.md — Phase 53 implements, does not re-derive.

Three SCs frame the work: **(1)** 9 agent YAMLs validate against `agents-schema.yaml` with full lineage blocks (HOOK-09 invariant in `screenplay.agent.yaml`'s `transform_notes`); **(2)** `scripts/run_screenplay_step3_roundtable.py` drives `round_table_open → 9 sequential get_agent_opinion → submit_round_table_result` on real GLM, producing HOOK-09-valid Step 3 JSON in <30s; **(3)** 2-conflict scenario produces correct arbitration per `02-ROUND-TABLE-PROTOCOL.md §3` (comparator LLM + scope precedence + confidence voting + conflict log).

**Primary recommendation:** Implement Phase 53 as 3 sub-waves (MIGR-01 → CREATIVE-01 → CREATIVE-02), each decoupled by a file-based interface (transform script writes YAMLs; driver script consumes MCP tools; arbitration module is called by driver when conflicts detected). The Phase 52 contract surface is stable — `load_agent_registry`, `open_round_table`, `append_turn`, `submit_round_table_result`, `read_and_recover_state`, `acquire_round_or_reject`/`release_round_lock`, `_scoped_agent_id` ContextVar are all locked. Phase 53's net-new code surface is: (a) 9 YAMLs at `~/.hermes/agents/`, (b) 1 transform script, (c) 1 driver script, (d) arbitration logic in `agent/memory_arbitration.py` (replacing stubs), (e) conflicts.jsonl writer, (f) GLM opinion call wired into `mcp_serve.py:get_agent_opinion`.

**Critical success factors:** preserve HOOK-09 marker contract verbatim in screenplay transform; use `auxiliary_client.call_llm(task="round_table_opinion", ...)` for both panelist opinions and comparator LLM (NOT a new client); honor strict serial execution (no `asyncio.gather`); use HERMES_HOME redirection for test isolation (already in `tests/conftest.py:_hermetic_environment`); explicitly mark every async test with `@pytest.mark.asyncio` (pytest-asyncio strict mode).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SKILL.md read + SHA-256 compute | Transform script (`scripts/transform_skill_to_agent.py`) | `kais-hermes-skills` repo (read-only source) | One-shot offline transform; no runtime cost; per Phase 49 §2 lineage rules |
| Agent YAML validation | `agent/registry_loader.py` (Phase 52) | `agents-schema.yaml` (Draft 2020-12) | Already shipped; Phase 53 just produces YAMLs that pass it |
| Per-panelist LLM opinion call | `mcp_serve.py::get_agent_opinion` (Phase 53 fills real GLM call) | `agent/auxiliary_client.call_llm(task="round_table_opinion")` | MCP tool owns serial lock + state append; LLM client delegated to auxiliary layer |
| Round table state lifecycle | `agent/round_table_state.py` (Phase 52) | `agent/round_table_executor.py` (per-roundId Lock) | Already shipped; Phase 53 calls into it from driver script |
| Memory conflict detection | `agent/memory_arbitration.py` (Phase 53 fills real logic) | `agent/auxiliary_client.call_llm(task="memory_comparator")` | Phase 52 stub returns `phase53_not_implemented`; Phase 53 swaps in comparator LLM + scope precedence + voting |
| Conflict log persistence | NEW: `agent/memory_arbitration.py::append_conflict_record` | `utils.atomic_json_write` (for JSONL append) | Append-only JSONL per round_id; curator consumes in v12+ |
| Step 3 output schema validation | NEW: `tests/fixtures/screenplay-step3-schema.json` | `jsonschema.Draft202012Validator` | Validates HOOK-09 emotion_curve + hooks/payoffs/cliffhangers arrays in driver output |
| Test isolation | `tests/conftest.py::_hermetic_environment` (existing) | `HERMES_HOME` env-var redirection | Already autouse; Phase 53 test fixtures land in per-test tempdir automatically |

## Standard Stack

### Core (all [VERIFIED] — already pinned in pyproject.toml + shipped in Phase 52)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pyyaml` (PyYAML) | 6.0.3 | SKILL.md frontmatter parse + agent YAML emit | Already used by `agent/registry_loader.py` for schema-loaded YAML parse [CITED: pyproject.toml:34] |
| `jsonschema` | (core dep) | Draft 2020-12 validation of agent YAMLs + Step 3 output | Already used by `agent/registry_loader.py:Draft202012Validator`; required by agents-schema.yaml header [CITED: agents-schema.yaml:30] |
| `openai` (SDK) | 2.24.0 | Underlying client for `auxiliary_client.call_llm` GLM calls | Universal LLM client; every OpenAI-compatible provider routes through it [CITED: CLAUDE.md Technology Stack] |
| `mcp` (SDK) | 1.26.0 | FastMCP server (already wired in `mcp_serve.py`) | Phase 52 registered 7 tools on it; Phase 53 fills tool bodies [CITED: pyproject.toml] |
| `pytest` | 9.0.2 | Test framework | `[dev]` extra; per-test HERMES_HOME redirection already in conftest [CITED: pyproject.toml:157] |
| `pytest-asyncio` | 1.3.0 | Async test support | Strict mode (NOT auto) — every async test needs explicit `@pytest.mark.asyncio` [VERIFIED: tests/agent/test_round_table_executor.py:22-24] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hashlib` (stdlib) | — | SHA-256 of SKILL.md content + persona fragment | Lineage block in every agent YAML; persona_sha256 in evolution_log [CITED: agents-schema.yaml:316-323] |
| `contextvars` (stdlib) | — | `_scoped_agent_id` propagation | Already shipped by Phase 52; Phase 53 calls `set_scoped_agent_id` before memory retrieve/submit [VERIFIED: agent/memory_arbitration.py:71-103] |
| `pathlib` (stdlib) | — | Path manipulation | All file ops; consistent with codebase style |
| `tempfile` + `os.replace` via `utils.atomic_json_write` | — | Atomic JSONL append for conflicts log | Use existing helper for the per-line JSON encode then plain append (JSONL is line-delimited; full atomic_json_write rewrites whole file — see Pattern 3) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `auxiliary_client.call_llm` for comparator LLM | Direct `openai.OpenAI().chat.completions.create()` | REJECTED — `auxiliary_client` already handles GLM 4-key rotation + provider routing + retry/backoff (per its module docstring lines 5168-5257). Bypassing it breaks the GLM concurrency invariant [VERIFIED: agent/auxiliary_client.py:5168] |
| `mcp.client.stdio` for driver script | In-process direct function imports | REJECTED — driver is a *Python script* that calls the MCP tool *functions* (not the MCP transport). Importing `mcp_serve`'s tool closures directly is simpler; stdio client is only needed when an EXTERNAL MCP client (Claude Code, Cursor) drives the lifecycle [ASSUMED — verify in Wave 0] |
| `asyncio.gather` for 9 parallel opinions | Serial `for agent_id in panelists: await get_agent_opinion(...)` | REJECTED — INFRA-04 hard constraint (Phase 52 SC#4) mandates strict serial; `asyncio.gather` violates `feedback-glm-overload-reduce-concurrency.md` [VERIFIED: agent/round_table_executor.py:8-44] |
| `Path.home() / ".hermes"` in test fixtures | `get_hermes_home()` from `hermes_constants` | REJECTED — autouse conftest fixture redirects HERMES_HOME per-test; `Path.home()` bypasses the redirection and leaks into real `~/.hermes` [CITED: CLAUDE.md anti-patterns + tests/conftest.py:328-360] |

**Installation:** No new packages required. All dependencies already pinned in `pyproject.toml` and exercised by Phase 52.

**Version verification:** No version drift — Phase 53 installs nothing. `pyyaml`, `jsonschema`, `mcp`, `openai`, `pytest`, `pytest-asyncio` are all exact-pinned per CLAUDE.md.

## Package Legitimacy Audit

> Phase 53 installs **zero** external packages. All libraries listed in Standard Stack above are already pinned in `pyproject.toml` and shipped with Phase 52. The slopcheck gate is therefore satisfied vacuously — no new packages enter the project. Existing pins (e.g., `pyyaml==6.0.3`, `mcp==1.26.0`, `openai==2.24.0`) carry their own audit trail in `pyproject.toml:14-33` supply-chain pinning rationale and are not re-audited here.

**Packages removed due to slopcheck [SLOP] verdict:** none (none checked — nothing new)
**Packages flagged as suspicious [SUS]:** none

*If slopcheck was unavailable at research time, all packages above are tagged `[ASSUMED]` and the planner must gate each install behind a `checkpoint:human-verify` task.* — N/A: no installs.

## Architecture Patterns

### System Architecture Diagram

```text
                          ┌─────────────────────────────────────────┐
                          │  Phase 53 three deliverables (NEW)       │
                          └─────────────────────────────────────────┘

  ┌────────────────┐    transform_skill_to_agent.py    ┌──────────────────┐
  │ kais-hermes-   │ ────────────(MIGR-01)────────────▶│ ~/.hermes/agents/│
  │ skills/skills/ │   per Phase 49 §2 75-cell rules    │ *.agent.yaml (9) │
  │ movie-experts/ │   + SHA-256 + Phase 53 edge rules  │  (MIGR-01 out)   │
  │ {9}/SKILL.md   │                                    └────────┬─────────┘
  └────────────────┘                                             │
                       (read-only source per                    │ load_agent_registry
                        Phase 48 + 49 L1-L6)                     ▼
                                                          ┌──────────────────┐
                                                          │ agent/registry_  │
                                                          │ loader.py        │
                                                          │ (Phase 52)       │
                                                          └────────┬─────────┘
                                                                   │ validated agents

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  CREATIVE-01 driver script (scripts/run_screenplay_step3_roundtable.py) │
  │                                                                         │
  │  ┌──────────────┐   ┌─────────────────┐   ┌─────────────────────────┐  │
  │  │ StoryKernel  │──▶│ round_table_open│──▶│ for agent_id in 9:      │  │
  │  │ sample.json  │   │ (MCP tool)      │   │   await get_agent_opinion│  │
  │  │ (fixture)    │   └─────────────────┘   │   (MCP tool, serial)     │  │
  │  └──────────────┘                         └──────────┬──────────────┘  │
  │                                                       │                 │
  │                                            ┌──────────▼──────────────┐  │
  │                                            │ if conflicts detected:  │  │
  │                                            │   arbitrate_memories()  │  │
  │                                            │   (CREATIVE-02)         │  │
  │                                            │   → conflicts.jsonl     │  │
  │                                            └──────────┬──────────────┘  │
  │                                                       │                 │
  │                                            ┌──────────▼──────────────┐  │
  │                                            │ submit_round_table_     │  │
  │                                            │ result(MCP tool)        │  │
  │                                            └──────────┬──────────────┘  │
  │                                                       │                 │
  │                                            ┌──────────▼──────────────┐  │
  │                                            │ Validate output against │  │
  │                                            │ screenplay-step3-schema │  │
  │                                            │ .json (HOOK-09)         │  │
  │                                            └─────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────────┘

  Down-level calls (each get_agent_opinion inside mcp_serve.py):

    ┌──────────────────────────────────────────────────────────────────────┐
    │ mcp_serve.py::get_agent_opinion (Phase 53 fills real body)           │
    │                                                                      │
    │  1. validate_project_slug + validate_round_id                        │
    │  2. acquire_round_or_reject(round_id)  ◀── asyncio.Lock per round_id │
    │  3. read state, check status == "open"                               │
    │  4. set_scoped_agent_id(agent_id)  ◀── ContextVar for mem0 routing   │
    │  5. memory_retrieve_scoped(query, agent_id)  ◀── Phase 53 real impl  │
    │  6. auxiliary_client.call_llm(task="round_table_opinion", messages=) │
    │       ◀── GLM via 4-key rotation, retry/backoff handled here         │
    │  7. build Turn dict (opinion, citedMemoryIds, submittedAt)           │
    │  8. append_turn(state_path, turn)                                    │
    │  9. release_round_lock(round_id)  ◀── finally block                 │
    └──────────────────────────────────────────────────────────────────────┘
```

The reader can trace the primary use case (one panelist's opinion) from MCP call entry, through serial-lock acquisition, GLM dispatch, all the way to state-file append. The driver script orchestrates 9 of these sequentially before calling `submit_round_table_result` to seal the round.

### Recommended Project Structure

```
scripts/
├── transform_skill_to_agent.py        # NEW (MIGR-01): one-shot CLI, reads SKILL.md → writes agent YAML
└── run_screenplay_step3_roundtable.py # NEW (CREATIVE-01): driver, invokes MCP tool functions in-process
agent/
└── memory_arbitration.py              # EXTEND (CREATIVE-02): replace 2 stubs + add arbitrate_memories + append_conflict_record
mcp_serve.py                           # MODIFY (CREATIVE-01): swap placeholder opinion for real call_llm + memory_retrieve_scoped wiring
tests/
├── fixtures/
│   ├── screenplay-step3-schema.json   # NEW: JSON Schema for HOOK-09 emotion_curve + hooks/payoffs/cliffhangers
│   ├── storykernel-sample.json        # NEW: synthetic StoryKernel Step 1 output (driver input)
│   └── memory-conflict-2conflict.json # NEW: 2-conflict fixture for CREATIVE-02 SC#3
└── agent/
    ├── test_transform_skill_to_agent.py # NEW: per-expert transform correctness (9 sub-tests)
    ├── test_run_screenplay_step3.py      # NEW: driver smoke test (real GLM if available, skip otherwise)
    ├── test_memory_arbitration.py        # NEW: comparator LLM (mock) + scope precedence + voting
    └── test_conflict_log_writer.py       # NEW: JSONL append + atomic semantics
~/.hermes/agents/                        # PRODUCTION TARGET (test fixtures use HERMES_HOME redirection)
├── screenplay.agent.yaml                # 9 YAMLs land here
├── cinematographer.agent.yaml
├── hook_retention.agent.yaml
├── theory_critic.agent.yaml
├── editor.agent.yaml
├── character_designer.agent.yaml
├── continuity_auditor.agent.yaml
├── audio_pipeline.agent.yaml
└── style_genome.agent.yaml
```

### Pattern 1: SKILL.md → Agent YAML Transform (per Phase 49 §2)

**What:** 5-field per-expert transform (tools / persona / refs / related_agents / lineage.skill_sha256) with edge-case rules for 4 of the 9 selected agents.
**When to use:** Once per agent at MIGR-01 time; never at runtime (lineage is operator-owned, see ARCHITECTURE §8.2 anti-pattern).
**Example:**

```python
# Source: Phase 49 §2.1 (default rule) + §2.4 (screenplay edge case)
import hashlib
from pathlib import Path
import yaml

def transform_screenplay(skill_md_path: Path) -> dict:
    """Transform screenplay SKILL.md → agent YAML dict per Phase 49 §2.4."""
    content = skill_md_path.read_text(encoding="utf-8")
    # LF-normalize before hashing (Phase 49 §2.1 edge case: CRLF checkouts)
    content_lf = content.replace("\r\n", "\n")
    skill_sha = hashlib.sha256(content_lf.encode("utf-8")).hexdigest()

    frontmatter, body = parse_frontmatter(content)  # reuse agent/skill_utils.parse_frontmatter
    meta = frontmatter["metadata"]["hermes"]

    return {
        "name": "screenplay",  # MUST equal filename stem — registry_loader enforces
        "description": frontmatter["description"],
        "version": "1.0.0",  # Agent YAML version, NOT SKILL version (§2.0 §2.1)
        "persona": _build_persona_screenplay(body),  # first-person + HOOK-09 verbatim
        "tools": ["hermes_llm", "read_file", "search_files", "write_file", "patch"],
        "memory_scope": "per_agent",  # uniform default per §2.17
        "lineage": {
            "derived_from_skill_id": meta["expert_id"],  # = "screenplay"
            "derived_from_repo": "kais-hermes-skills",
            "transform_date": "2026-07-07",
            "transform_notes": (  # HOOK-09 invariant — load-bearing per §2.4
                "Persona rewritten from SKILL body; SKILL preserved as fallback. "
                "HOOK-09 emotion_curve marker arrays remain contract-load-bearing "
                "— do NOT lose in transform."
            ),
            "skill_sha256": skill_sha,
        },
        "refs": [
            "save-the-cat-beat-sheet.md",
            "mckee-scene-design.md",
            "cn-shortdrama-structure.md",
            "emotion-curve-academic.md",
            "dialogue-craft.md",
        ],
        "tags": meta["tags"],
        "expert_id": meta["expert_id"],  # FOUND-08 verbatim
        "metrics": meta["metrics"],
        "prerequisites": frontmatter.get("prerequisites", {}),
        "related_agents": _filter_related_agents(meta["related_skills"]),  # see Pattern 1b
        "evolution_log": [],
        "fitness_score": None,
        "platforms": frontmatter.get("platforms", ["linux", "macos", "windows"]),
        "round_table_eligible": True,
        "default_invocation": "mcp_tool",
    }

def _filter_related_agents(related_skills: list[str]) -> list[str]:
    """Map v3.0+ names + drop deprecated (FOUND-08). screenplay SKILL.md lists
    related_skills = [style_genome, editor, audio_pipeline, compliance_gate,
    hook_retention, cinematographer, theory_critic, animation_studio,
    documentary_maker]. Keep the 9-agent subset peers, drop non-panelists
    (animation_studio, documentary_maker are NOT in the 9-agent subset per
    CONTEXT.md decision #1)."""
    PANEL_9 = {"screenplay", "cinematographer", "hook_retention", "theory_critic",
               "editor", "character_designer", "continuity_auditor",
               "audio_pipeline", "style_genome"}
    return [r for r in related_skills if r in PANEL_9]
```

### Pattern 1b: Deprecated-name Mapping (FOUND-08 preservation)

Per Phase 49 §2.18 + §2.19, screenplay's source `related_skills` array may list `scene_builder` (pre-v3.0 name) — CONTEXT.md decision #1 picks the v3.0+ canonical name `cinematographer` (which absorbed scene_builder per Phase 17). The transform script MUST map legacy names:

```python
# Source: Phase 49 §2.7 + §2.18
LEGACY_NAME_MAP = {
    "scene_builder": "cinematographer",  # absorbed in Phase 17
    "continuity": "continuity_auditor",  # renamed in v3.0+
    "performer": "character_designer",   # CONTEXT.md decision #1 rename
    "composer": "audio_pipeline",        # CONTEXT.md decision #1 rename
}
def canonicalize(name: str) -> str:
    return LEGACY_NAME_MAP.get(name, name)
```

### Pattern 2: Real GLM Opinion Call Inside `get_agent_opinion`

**What:** Replace Phase 52's `"[phase52_placeholder]"` opinion with a real `auxiliary_client.call_llm` dispatch.
**When to use:** Every `get_agent_opinion` MCP tool call.
**Example:**

```python
# Source: agent/auxiliary_client.py:5168 (call_llm signature) + agent/memory_arbitration.py:116
from agent.auxiliary_client import call_llm
from agent.memory_arbitration import memory_retrieve_scoped, set_scoped_agent_id

# Inside mcp_serve.py::get_agent_opinion, after lock acquisition + state read:
set_scoped_agent_id(agent_id)  # for downstream memory routing ContextVar
try:
    # Phase 53: real memory retrieval (Phase 52 stub returned phase53_not_implemented)
    mem_result = await memory_retrieve_scoped(
        query=topic, agent_id=agent_id, top_k=5,
    )
    memory_context = _format_memory_context(mem_result.get("hits", []))

    messages = [
        {"role": "system", "content": _build_persona_prompt(agent_id)},
        {"role": "user", "content": _build_opinion_query(
            topic=topic,
            panel_context=panel_context,
            memory_context=memory_context,
            storykernel=storykernel_input,  # for screenplay step 3 driver
        )},
    ]
    # CRITICAL: synchronous call_llm in ThreadPoolExecutor via auxiliary_client.
    # auxiliary_client already handles GLM 4-key rotation + 3-strike early-abort
    # + retry/backoff. Do NOT add asyncio.gather or parallel calls here —
    # INFRA-04 hard constraint (Phase 52 SC#4 serial enforcement).
    response = call_llm(
        task="round_table_opinion",  # configure in config.yaml auxiliary section
        messages=messages,
        temperature=0.7,  # screenplay-specific; cinamatographer might want 0.5
        max_tokens=2048,
    )
    opinion_text = response.choices[0].message.content
finally:
    set_scoped_agent_id(None)  # always clear scope on exit

turn = {
    "turnIndex": len(state.get("turns", [])) + 1,
    "panelistId": agent_id,
    "opinion": opinion_text,
    "citedMemoryIds": _extract_cited_memory_ids(opinion_text, mem_result),
    "submittedAt": _state_now_iso(),
}
append_turn(state_path, turn)
```

### Pattern 3: Atomic JSONL Append for conflicts.jsonl

**What:** Append-only conflict-log writer. Distinct from `utils.atomic_json_write` (which rewrites the WHOLE file via temp+replace) — JSONL is line-delimited, so a plain append + fsync is atomic at the line level.
**When to use:** Every time the comparator LLM produces a ConflictRecord.
**Example:**

```python
# Source: Phase 53 CREATIVE-02 (NEW pattern, not in Phase 52)
import json
import os
from pathlib import Path
from typing import Any

def append_conflict_record(
    conflicts_jsonl_path: Path,
    record: dict[str, Any],
) -> None:
    """Append one ConflictRecord to the round's conflicts.jsonl.

    Path convention: .runtime/{slug}/round_tables/{round_id}/conflicts.jsonl
    (per CONTEXT.md decision #5; NEW subdirectory per round_id).

    Atomicity: JSONL line append is naturally atomic on POSIX for writes
    < 4096 bytes (PIPE_BUF). For larger records, use the standard
    temp-file-+os.replace dance per record (overkill for v11.0 PoC where
    records are ~500 bytes each).

    CLAUDE.md compliance: encoding="utf-8" mandatory (Ruff PLW1514).
    """
    conflicts_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(conflicts_jsonl_path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())  # durability for crash recovery
```

### Pattern 4: Conflict Arbitration Pipeline (CREATIVE-02)

**What:** 5-mechanism pipeline per `02-ROUND-TABLE-PROTOCOL.md §3`: memory annotation → comparator LLM → scope precedence → confidence voting → conflict log.
**When to use:** Driver detects conflicting `citedMemoryIds` across panelist turns OR explicit test scenario injects 2 conflicts.
**Example:**

```python
# Source: 02-ROUND-TABLE-PROTOCOL.md §3.2-§3.6 (verbatim prompt template + decision tree)
from agent.auxiliary_client import call_llm

COMPARATOR_PROMPT_TEMPLATE = """You are arbitrating a memory conflict in a Hermes round table.
Project context: {project_id}
Question under debate: {question}

Memory A (cited by panelist {panelistA}):
- content: {memoryA_content}
- scope: {memoryA_scope} (global | project | session)
- confidence: {memoryA_confidence}
- evidence_chain length: {memoryA_evidence_len}
- evidence_operator_ids: {memoryA_operator_ids}

Memory B (cited by panelist {panelistB}):
- content: {memoryB_content}
- scope: {memoryB_scope}
- confidence: {memoryB_confidence}
- evidence_chain length: {memoryB_evidence_len}
- evidence_operator_ids: {memoryB_operator_ids}

Apply scope precedence: session > project > global
  (a session-scoped memory overrides global for THIS session;
   a project-scoped memory overrides global for THIS project).

Apply confidence-weighting: at the same scope level, higher confidence wins.
  If both memories are at the same scope level AND confidence within 0.05 of
  each other, defer to operator (human review).

Apply evidence diversity check: prefer memory with more diverse
  evidence_operator_ids (>=2 distinct operators per Phase 45 §3.7).

Output JSON:
{{
  "resolution": "A-wins" | "B-wins" | "both-kept" | "both-quarantined" | "deferred-to-operator",
  "rationale": "<=200 chars human-readable",
  "confidence": 0.0-1.0
}}"""

async def arbitrate_two_memories(
    memory_a: dict, memory_b: dict, panelist_a: str, panelist_b: str,
    project_id: str, question: str,
) -> dict:
    """Run comparator LLM pass per §3.2 + tie-break rule per §3.4."""
    prompt = COMPARATOR_PROMPT_TEMPLATE.format(
        project_id=project_id, question=question,
        panelistA=panelist_a, panelistB=panelist_b,
        memoryA_content=memory_a["content"],
        memoryA_scope=memory_a["scope"],
        memoryA_confidence=memory_a["confidence"],
        memoryA_evidence_len=len(memory_a.get("evidence_chain", [])),
        memoryA_operator_ids=memory_a.get("evidence_operator_ids", []),
        memoryB_content=memory_b["content"],
        memoryB_scope=memory_b["scope"],
        memoryB_confidence=memory_b["confidence"],
        memoryB_evidence_len=len(memory_b.get("evidence_chain", [])),
        memoryB_operator_ids=memory_b.get("evidence_operator_ids", []),
    )
    response = call_llm(
        task="memory_comparator",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,  # deterministic arbitration
        max_tokens=200,
    )
    import json as _json
    return _json.loads(response.choices[0].message.content)

def apply_tie_break(
    memory_a: dict, memory_b: dict, llm_resolution: dict,
) -> dict:
    """§3.4 tie-break: if same scope AND |Δconfidence| <= 0.05 → deferred-to-operator."""
    if llm_resolution["resolution"] in ("A-wins", "B-wins"):
        if memory_a["scope"] == memory_b["scope"]:
            delta = abs(memory_a["confidence"] - memory_b["confidence"])
            if delta < 0.05:
                llm_resolution["resolution"] = "deferred-to-operator"
                llm_resolution["rationale"] = (
                    f"Tie at {memory_a['scope']} scope "
                    f"(Δconfidence={delta:.3f} < 0.05)"
                )
    return llm_resolution
```

### Anti-Patterns to Avoid

- **Auto-re-transform on SHA-256 drift:** ARCHITECTURE §8.2 explicitly forbids this. Curator's drift detection is ADVISORY only; operator decides whether to re-run transform. Phase 53 transform script is operator-invoked, not background-triggered. [CITED: agents-schema.yaml:320-323]
- **Parallel `asyncio.gather` for 9 opinions:** violates INFRA-04 hard constraint + `feedback-glm-overload-reduce-concurrency.md`. Must be `for agent_id in panelists: await get_agent_opinion(agent_id, ...)`. [VERIFIED: agent/round_table_executor.py:8-44]
- **Embedding GLM API key in driver script:** the driver uses `auxiliary_client.call_llm` which reads from `~/.hermes/.env` / `cli-config.yaml`. No key handling in Phase 53 code. [VERIFIED: agent/auxiliary_client.py:5168-5257]
- **Skipping `set_scoped_agent_id` before `memory_retrieve_scoped`:** the `_scoped_agent_id` ContextVar IS the routing key for mem0 namespace. Without it, memory calls hit the wrong namespace (or fail validation). [VERIFIED: agent/memory_arbitration.py:77-103]
- **Rewriting the WHOLE state file for conflict append:** the `state["conflicts"]` array inside `.runtime/{slug}/round_tables/{round_id}.json` IS sealed at submit time per `02-ROUND-TABLE-PROTOCOL.md §3.5` — Phase 53 must use the SEPARATE `conflicts.jsonl` (per CONTEXT.md decision #5) for runtime appends and only flush to `state["conflicts"]` at submit. (Two storage locations for the same logical data — see Open Questions OQ-2.)
- **Hand-rolling GLM retry/backoff:** `auxiliary_client.call_llm` already handles 4-key rotation + 3-strike early-abort. Adding tenacity decorators in Phase 53 code double-retries and breaks the global concurrency invariant. [VERIFIED: agent/auxiliary_client.py docstring]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML schema validation | Custom field-by-field checker | `jsonschema.Draft202012Validator` (already in registry_loader) | Schema has `$ref`, `additionalProperties: false`, regex patterns — jsonschema handles all; manual checker rots on schema drift |
| Atomic state file write | `open(path, "w") + json.dump` | `utils.atomic_json_write` (temp + fsync + os.replace) | Partial-write corruption on crash; Phase 52 already shipped this pattern |
| Per-roundId serial lock | threading.Lock / multiprocessing.Lock / Semaphore | `agent/round_table_executor.acquire_round_or_reject` (asyncio.Lock) | threading.Lock deadlocks under FastMCP's event loop; Semaphore allows N>1 concurrent (violates INFRA-04) |
| GLM API call + retry + 4-key rotation | Direct `openai.OpenAI().chat.completions.create` + custom retry | `agent/auxiliary_client.call_llm(task="round_table_opinion", ...)` | Layer already handles provider routing, key rotation, retry/backoff, timeout — bypassing breaks global concurrency invariant |
| SKILL.md frontmatter parse | Regex on raw markdown | `agent.skill_utils.parse_frontmatter` (already shipped) | Phase 5-era parser handles YAML frontmatter edge cases (BOM, CRLF, indentation) |
| Memory routing namespace | Manual `f"agent:{agent_id}"` string concat | `_scoped_agent_id` ContextVar + `set_scoped_agent_id` (Phase 52) | Async-correct propagation; manual strings leak across asyncio.create_task boundaries |
| HOOK-09 schema validation | Custom dict-shape checker | `jsonschema.Draft202012Validator` + `screenplay-step3-schema.json` fixture | Schema is the contract; custom checkers rot on emotion_curve marker evolution |

**Key insight:** Phase 53 is a **fill-in-the-blanks** phase, not a greenfield phase. Every primitive it needs (atomic write, serial lock, GLM call, schema validation, frontmatter parse, scoped agent context) was shipped by Phase 52 or earlier. Net-new code is narrow: transform script, driver script, arbitration logic, conflict log writer.

## Runtime State Inventory

> Phase 53 is partially a refactor/migration phase (SKILL.md → agent YAML transform introduces new state). All 5 categories answered explicitly.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None in v11.0 PoC scope. mem0 backend stores existing `agent_id=hermes` memories (per v7.0 carry-forward) but Phase 53 does NOT migrate them — Option B 物理分区 deferred to v12+. The 9 new agent YAMLs at `~/.hermes/agents/*.agent.yaml` are operator-owned config, not "stored data" in the runtime sense. | None — verify `memory_retrieve_scoped` honors `agent_id` filter and does NOT return v7.0 `agent_id=hermes` records (Phase 52 stub ignores this; Phase 53 routing must respect `memory_scope: per_agent`) |
| Live service config | None. No long-running service introduces new state in Phase 53 — the gateway runs Phase 52's MCP tools unchanged; Phase 53 fills in tool bodies that execute per-request and persist to filesystem. | None — `mcp_serve.py` is hot-patched in-place; no gateway restart needed for v11.0 PoC (operator-run driver script) |
| OS-registered state | None. No systemd units, cron jobs, or scheduled tasks created. Phase 53 deliverables are scripts + YAML files, not daemons. | None |
| Secrets/env vars | Phase 53 reads `GLM_API_KEY` (or whatever provider key the operator configured in `~/.hermes/.env` + `cli-config.yaml`). No new secrets introduced. Driver script gracefully skips SC#2 smoke test if GLM unavailable (mark `human_needed` in VERIFICATION.md). | None — driver script must check `auxiliary_client.call_llm(...)` raising `RuntimeError` and emit a clear "configure GLM_API_KEY in ~/.hermes/.env" message |
| Build artifacts | None in v11.0 PoC. The 9 agent YAMLs are checked into git (not build artifacts). `pyproject.toml` unchanged — no `egg-info` regeneration needed. | None |

**Nothing found requiring data migration.** Phase 53 is additive: it produces NEW files at NEW paths and fills in NEW logic in existing files. No rename, no in-place mutation of existing state.

## Common Pitfalls

### Pitfall 1: HOOK-09 marker contract loss in transform
**What goes wrong:** Transform script copies screenplay SKILL.md `description` field verbatim into `persona` (or rewrites persona without surfacing HOOK-09). Downstream Step 6.5 storyboard + Step 7 visual_executor cannot consume screenplay output (emotion_curve marker arrays missing).
**Why it happens:** Phase 49 §2.4 explicitly warns about this. The HOOK-09 contract is buried in the SKILL body (under `## Emotion Curve Hooks / Payoffs / Cliffhangers`), not in the frontmatter. Naive transform scripts that only read frontmatter lose it.
**How to avoid:** Per Phase 49 §2.4, `lineage.transform_notes` MUST contain literal string `"HOOK-09 emotion_curve marker arrays remain contract-load-bearing"`. The transform script writes this string verbatim into every screenplay agent YAML. SC#1 acceptance smoke-test grep-checks this substring.
**Warning signs:** Downstream storyboard step fails with `KeyError: 'hooks'` or `emotion_curve malformed`. The PoC's first "did the transform work?" smoke test (per `05-POC-PLAN.md §3.2`) catches this.

### Pitfall 2: asyncio.Lock acquired but never released on exception
**What goes wrong:** `get_agent_opinion` raises between `acquire_round_or_reject` and `release_round_lock` (e.g., GLM API timeout mid-call). The per-roundId lock stays held forever; subsequent panelists get 429 even after the crash.
**Why it happens:** Phase 52 already fixed this with `try/finally` (see `mcp_serve.py:1307-1312`). Phase 53 must preserve the finally block when filling in real GLM call.
**How to avoid:** Every `await acquire_round_or_reject(...)` MUST be paired with `await release_round_lock(...)` in a `finally:` block. Phase 52's T-52-15 (DoS) mitigation comment in `mcp_serve.py` calls this out.
**Warning signs:** Second `get_agent_opinion` for same `roundId` returns 429 immediately after a previous one crashed. Tests in `tests/agent/test_round_table_executor.py` cover this pattern; mirror them.

### Pitfall 3: pytest-asyncio strict mode (NOT auto)
**What goes wrong:** Async test silently skipped or fails with `RuntimeError: asyncio.run() cannot be called from a running event loop`.
**Why it happens:** `pyproject.toml` does NOT set `asyncio_mode=auto`, so the default is `strict`. Every async test MUST carry `@pytest.mark.asyncio` explicitly. Phase 52 hit this and documented it in `tests/agent/test_round_table_executor.py:22-24`.
**How to avoid:** Add `@pytest.mark.asyncio` to EVERY async test function. Do NOT rely on auto-detection.
**Warning signs:** Test collection reports `async def` functions as sync (no warning); they just don't run. Verify with `pytest --co -q` that async tests are collected.

### Pitfall 4: Comparator LLM returns malformed JSON
**What goes wrong:** Comparator LLM (via `auxiliary_client.call_llm`) returns prose instead of the `{"resolution": ..., "rationale": ..., "confidence": ...}` JSON the prompt requests. `json.loads` raises `JSONDecodeError`; arbitration crashes.
**Why it happens:** GLM occasionally wraps JSON in markdown fences (```` ```json ... ``` ````) or adds preamble text. Even with `temperature=0.0`, this is a known issue with chat models.
**How to avoid:** Wrap the parse in try/except; on failure, fall back to `deferred-to-operator` with rationale `"comparator LLM returned malformed JSON"`. Never crash the round table on arbitration failure — deferral is always safe per `02-ROUND-TABLE-PROTOCOL.md §3.6` decision tree.
**Warning signs:** `JSONDecodeError` in `tests/agent/test_memory_arbitration.py` when mocking comparator LLM.

### Pitfall 5: HERMES_HOME redirection bypassed by `Path.home()`
**What goes wrong:** Test writes 9 agent YAMLs to REAL `~/.hermes/agents/` instead of per-test tempdir. CI pollution; subsequent tests see stale fixtures.
**Why it happens:** Code uses `Path.home() / ".hermes" / "agents"` directly instead of `get_hermes_home() / "agents"`. The autouse `_hermetic_environment` fixture in `tests/conftest.py:328-360` only redirects via the `HERMES_HOME` env var.
**How to avoid:** All production code uses `from hermes_constants import get_hermes_home`. CLAUDE.md anti-patterns explicitly call this out. The Ruff/conftest guard catches it on test runs.
**Warning signs:** Real `~/.hermes/agents/` directory accumulates test fixtures between runs.

### Pitfall 6: Comparator LLM uses non-GLM provider by accident
**What goes wrong:** `call_llm(task="memory_comparator")` picks up OpenRouter or another provider because the operator didn't configure `auxiliary.memory_comparator.provider` in `cli-config.yaml`. Memory.md `feedback-glm-5-2-only.md` mandates GLM only.
**Why it happens:** `auxiliary_client.call_llm` has an auto-fallback chain (per its module docstring). Without explicit provider config, it falls back to whatever's available.
**How to avoid:** Driver script sets `provider="glm"` (or whatever the GLM provider ID is in `cli-config.yaml`) explicitly when calling `call_llm` for both opinion and comparator. Alternatively, add `auxiliary.round_table_opinion.provider: glm` + `auxiliary.memory_comparator.provider: glm` to `cli-config.yaml.example` and document in VERIFICATION.md.
**Warning signs:** `auxiliary_client` logs show "falling back to OpenRouter" warnings during SC#2 smoke test.

### Pitfall 7: SKILL.md CRLF line endings produce wrong SHA-256
**What goes wrong:** Operator checks out `kais-hermes-skills` on Windows; SKILL.md has CRLF endings. SHA-256 computed on raw bytes differs from CI's LF-normalized SHA-256. Curator's drift detection later flags a phantom mismatch.
**Why it happens:** Phase 49 §2.1 edge case explicitly documents this. `git config core.autocrlf=true` on Windows rewrites line endings on checkout.
**How to avoid:** Transform script normalizes content to LF before hashing: `content_lf = content.replace("\r\n", "\n")`. Document normalization in `transform_notes`.
**Warning signs:** Curator (Phase 54+ EVAL-03) reports `skill_sha256 mismatch` even though SKILL.md content semantically unchanged.

## Code Examples

### Example 1: Wave 0 — Verify Phase 52 contract surface compiles + imports

```python
# Source: Phase 52 actual outputs (read this verbatim before starting Phase 53)
# tests/agent/test_phase52_contract.py (NEW Wave 0 test — proves Phase 52 is consumable)
from __future__ import annotations
import pytest
from agent.registry_loader import (
    load_agent_registry, load_one_agent_yaml, RegistryValidationError,
)
from agent.round_table_state import (
    open_round_table, append_turn, submit_round_table_result,
    abort_round_table, read_and_recover_state,
    validate_round_id, validate_project_slug,
)
from agent.round_table_executor import (
    acquire_round_or_reject, release_round_lock, _serial_violation_response,
)
from agent.memory_arbitration import (
    memory_retrieve_scoped, memory_submit_record,
    set_scoped_agent_id, get_scoped_agent_id,
)
# If these imports fail, Phase 52 is not actually shipped — stop and investigate.

@pytest.mark.asyncio
async def test_phase52_stub_returns_phase53_marker(tmp_path, monkeypatch):
    """Phase 52 stub contract: returns phase53_not_implemented. Phase 53 will
    replace this with real routing — the stub return string is the gate."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    result = await memory_retrieve_scoped(query="test", agent_id="x", top_k=3)
    assert result == {"status": "phase53_not_implemented", "hits": []}
```

### Example 2: Driver script invoking MCP tools in-process

```python
# Source: scripts/run_screenplay_step3_roundtable.py (sketch — full impl in PLAN)
from __future__ import annotations
import asyncio
import json
import uuid
from pathlib import Path

# Import the closures registered in mcp_serve.py — they are regular async
# functions after @mcp.tool() decoration; we can call them directly without
# stdio MCP transport (the transport is for EXTERNAL clients like CC).
from mcp_serve import (
    round_table_open, get_agent_opinion, submit_round_table_result,
)
from agent.auxiliary_client import call_llm  # noqa: F401 — used by mcp_serve internally

PANEL_9 = [
    "screenplay", "cinematographer", "hook_retention", "theory_critic",
    "editor", "character_designer", "continuity_auditor",
    "audio_pipeline", "style_genome",
]

async def main(storykernel_path: Path, output_path: Path) -> None:
    storykernel = json.loads(storykernel_path.read_text(encoding="utf-8"))
    project_slug = "screenplay-step3-poc"
    round_id = uuid.uuid4().hex

    # 1. Open round table
    open_resp = await round_table_open(
        round_id=round_id,
        project_slug=project_slug,
        question=f"Generate screenplay Step 3 for: {storykernel['logline']}",
        panelist_agent_ids=PANEL_9,
        caller="run_screenplay_step3_roundtable.py",
    )
    assert '"status": "open"' in open_resp or '"roundId"' in open_resp

    # 2. 9 sequential opinions — STRICT SERIAL (no asyncio.gather)
    panel_context = None
    for agent_id in PANEL_9:
        resp = await get_agent_opinion(
            round_id=round_id,
            project_slug=project_slug,
            agent_id=agent_id,
            topic=f"Screenplay Step 3 scene design for {storykernel['logline']}",
            panel_context=panel_context,
        )
        opinion_data = json.loads(resp)
        panel_context = opinion_data.get("opinion")  # chain for next panelist

    # 3. Submit final result
    conclusion = await _synthesize_conclusion(round_id, project_slug)
    submit_resp = await submit_round_table_result(
        round_id=round_id,
        project_slug=project_slug,
        conclusion=conclusion,
        cited_memories=[],
        closed_by="run_screenplay_step3_roundtable.py",
    )

    # 4. Validate against HOOK-09 schema
    output = json.loads(conclusion)
    _validate_step3_schema(output, output_path)

async def _synthesize_conclusion(round_id: str, project_slug: str) -> str:
    """Optional: ask GLM to synthesize 9 opinions into final Step 3 JSON.
    For v11.0 PoC minimum scope, this can be the last panelist's opinion
    (screenplay's). For higher quality, do a separate synthesis LLM call."""
    # v11.0 PoC: simplest viable synthesis — screenplay re-emits structured
    # Step 3 JSON based on all 9 opinions. Implement as a 10th call_llm.
    ...

def _validate_step3_schema(output: dict, output_path: Path) -> None:
    import jsonschema
    schema_path = Path("tests/fixtures/screenplay-step3-schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(output)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(main(
        storykernel_path=Path("tests/fixtures/storykernel-sample.json"),
        output_path=Path("build/screenplay-step3-output.json"),
    ))
```

### Example 3: Unit-testing the transform without real GLM

```python
# Source: tests/agent/test_transform_skill_to_agent.py
from __future__ import annotations
import hashlib
from pathlib import Path
import pytest
from scripts.transform_skill_to_agent import transform_one, _build_persona_screenplay

KIAS_SKILLS = Path("/data/workspace/kais-hermes-skills/skills/movie-experts")

@pytest.mark.parametrize("expert_name,expected_tools", [
    ("screenplay", ["hermes_llm", "read_file", "search_files", "write_file", "patch"]),
    ("cinematographer", ["hermes_llm", "read_file", "search_files"]),  # analysis-only
    ("hook_retention", ["hermes_llm", "read_file", "search_files"]),  # advisory
    ("audio_pipeline", ["hermes_llm", "dreamina_cli", "read_file", "write_file"]),
])
def test_transform_tools_per_phase49_rules(expert_name, expected_tools):
    skill_path = KIAS_SKILLS / expert_name / "SKILL.md"
    if not skill_path.exists():
        pytest.skip(f"{skill_path} not available — run on operator machine")
    result = transform_one(expert_name, skill_path)
    assert result["tools"] == expected_tools

def test_screenplay_transform_preserves_HOOK_09():
    skill_path = KIAS_SKILLS / "screenplay" / "SKILL.md"
    if not skill_path.exists():
        pytest.skip("screenplay SKILL.md not available")
    result = transform_one("screenplay", skill_path)
    # HOOK-09 invariant — load-bearing
    assert "HOOK-09 emotion_curve marker arrays remain contract-load-bearing" in (
        result["lineage"]["transform_notes"]
    ), "Phase 49 §2.4 HOOK-09 invariant violated — downstream storyboard cannot consume"

def test_skill_sha256_lf_normalized():
    """Phase 49 §2.1 edge case: CRLF checkouts must normalize to LF before hash."""
    skill_path = KIAS_SKILLS / "screenplay" / "SKILL.md"
    if not skill_path.exists():
        pytest.skip()
    raw = skill_path.read_bytes()
    lf_content = raw.replace(b"\r\n", b"\n").decode("utf-8")
    expected_sha = hashlib.sha256(lf_content.encode("utf-8")).hexdigest()
    result = transform_one("screenplay", skill_path)
    assert result["lineage"]["skill_sha256"] == expected_sha
    assert len(result["lineage"]["skill_sha256"]) == 64
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SKILL.md as agent container | Agent YAML at `~/.hermes/agents/` (SKILL as fallback per `default_invocation: skill_fallback`) | v10.0 design (Phase 44-51) — v11.0 implements | Phase 53 transforms 9 SKILLs to YAMLs; SKILLs remain read-only in kais-hermes-skills |
| Phase 52 placeholder opinion (`[phase52_placeholder]`) | Real GLM call via `auxiliary_client.call_llm` | Phase 53 | Real LLM responses flow into round table state |
| Phase 52 stub arbitration (`phase53_not_implemented`) | 5-mechanism arbitration per `02-ROUND-TABLE-PROTOCOL.md §3` | Phase 53 | Conflicts detected + resolved + logged |
| `state["conflicts"]` array inside round-table-state-schema YAML (sealed at submit) | NEW: separate `conflicts.jsonl` per round (CONTEXT.md decision #5) | Phase 53 | Append-only runtime log + curator input |

**Deprecated/outdated:**
- Pre-v3.0 `expert_id` names (`scene_builder`, `continuity`, `performer`, `composer`) — map to v3.0+ canonical via `LEGACY_NAME_MAP` per Pattern 1b.
- `compliance_gate` and `script_auditor` are NOT in the 9-agent subset (CONTEXT.md decision #1); their absence is intentional, not a bug.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The 9 selected agent names (`screenplay`, `cinematographer`, `hook_retention`, `theory_critic`, `editor`, `character_designer`, `continuity_auditor`, `audio_pipeline`, `style_genome`) all exist at `/data/workspace/kais-hermes-skills/skills/movie-experts/` | Standard Stack, Pattern 1 | LOW — verified `ls` lists all 9. Some have alternate historical names (`continuity` vs `continuity_auditor`, `composer` vs `audio_pipeline`); transform script MUST handle both via `LEGACY_NAME_MAP`. |
| A2 | `auxiliary_client.call_llm(task="round_table_opinion", ...)` resolves to GLM via existing provider chain without new config | Pattern 2, Pitfall 6 | MEDIUM — if `auxiliary.round_table_opinion.provider` is not set in `cli-config.yaml`, call falls back to auto-chain (may pick OpenRouter). MEMORY.md `feedback-glm-5-2-only.md` mandates GLM only. **Planner must add `auxiliary.round_table_opinion.provider: glm` + `auxiliary.memory_comparator.provider: glm` to `cli-config.yaml.example` + VERIFICATION.md operator instructions.** |
| A3 | The driver script can import `mcp_serve.round_table_open` etc. as regular async functions (no stdio MCP transport needed) | Pattern 2 Example 2 | LOW-MEDIUM — `mcp_serve.py` registers tools with `@mcp.tool()` decorator. The decorated objects may be FastMCP wrappers, not raw coroutines. Wave 0 must verify with `inspect.iscoroutinefunction(mcp_serve.round_table_open)`. If wrapped, use `mcp_serve.round_table_open.fn` or call the underlying state-machine functions (`agent.round_table_state.open_round_table`) directly. |
| A4 | `tests/conftest.py::_hermetic_environment` (autouse) redirects HERMES_HOME for ALL tests including Phase 53 new tests | Pitfall 5 | LOW — verified: `monkeypatch.setenv("HERMES_HOME", str(fake_hermes_home))` at `tests/conftest.py:360`. Existing pattern; Phase 53 inherits automatically. |
| A5 | The 9 SKILL.md files all use the same YAML frontmatter schema (`metadata.hermes.{tags, related_skills, expert_id, metrics}`) | Pattern 1 | LOW — verified 4 of 9 (screenplay, hook_retention, cinematographer, theory_critic, editor) all share the schema per `05-POC-PLAN.md §1.6 quick-glance table`. The other 5 (character_designer, continuity_auditor, audio_pipeline, style_genome) follow per ARCHITECTURE §2 verbatim table. |
| A6 | `state["conflicts"]` (inside JSON state file) AND `conflicts.jsonl` (separate file per round) BOTH need to be written | Architecture Diagram, Pattern 3, Anti-Pattern 5 | MEDIUM — v10.0 design says conflicts live in `state["conflicts"]` (sealed at submit). CONTEXT.md decision #5 says runtime appends go to a SEPARATE `conflicts.jsonl`. **Interpretation:** runtime appends during round go to JSONL; at `submit_round_table_result` time, JSONL records are folded into `state["conflicts"]` (sealed). Or: JSONL is the canonical source, `state["conflicts"]` is a convenience snapshot. **Planner MUST clarify in PLAN.md by either (a) writing to both, or (b) treating JSONL as primary + state["conflicts"] as derived snapshot.** |
| A7 | `auxiliary_client.call_llm` is synchronous (returns response object directly, not coroutine) | Pattern 2, Pattern 4 | LOW — verified at `agent/auxiliary_client.py:5168` (`def call_llm`, not `async def`). For async alternative, see `async_call_llm` at line 5697. Driver script should use `call_llm` from within `asyncio.to_thread` or rely on the auxiliary_client's internal ThreadPoolExecutor. |
| A8 | `transform_skill_to_agent.py` lives in `scripts/` (per CONTEXT.md Claude's Discretion #2), not `agent/` | Project Structure | LOW — verified convention: existing `scripts/analyze_livetest.py`, `scripts/build_skills_index.py` etc. all live in `scripts/`. One-shot utilities, not runtime imports. |

## Open Questions (RESOLVED 2026-07-07 — addressed in PLAN.md files)

> All 4 OQs below were addressed during planning. Resolutions propagated to PLAN.md tasks.

1. **`mcp_serve.py` tool decoration: callable directly or wrapped?** ✅ RESOLVED: Wave 0 contract smoke test (53-01 Task 1, `test_phase52_contract.py`) probes all 7 MCP tool symbols. If wrapped, driver script falls back to calling `agent/round_table_state.py` + `agent/memory_arbitration.py` functions directly (documented in 53-03 Task 2 action).
   - What we know: 7 MCP tools were registered with `@mcp.tool()` decorator in Phase 52.
   - What's unclear: whether `mcp_serve.round_table_open(...)` (the decorated object) can be called directly as `await mcp_serve.round_table_open(round_id=..., ...)`, OR whether it's a FastMCP `Tool` wrapper requiring `.call()` / `.fn()`.
   - Recommendation: Wave 0 includes a smoke test (`test_phase52_contract.py`) that imports + awaits each tool with synthetic args. If wrapped, switch driver script to call the underlying `agent/round_table_state.py` functions directly (bypassing MCP tool layer — acceptable for v11.0 PoC since driver is a Python script, not an external MCP client).

2. **Dual conflict storage (state["conflicts"] + conflicts.jsonl)** ✅ RESOLVED: Per 53-02 Task 2 + 53-03 success_criteria — `conflicts.jsonl` is canonical append-only log; `state["conflicts"]` populated from JSONL read at `submit_round_table_result` time, then both sealed.
   - What we know: v10.0 schema says `state["conflicts"]` is sealed at submit. CONTEXT.md decision #5 says runtime appends go to `conflicts.jsonl`.
   - What's unclear: are these two copies of the same data, or distinct (one for runtime log, one for sealed snapshot)?
   - Recommendation: Treat `conflicts.jsonl` as canonical runtime append-only log (per CONTEXT.md decision #5); at `submit_round_table_result` time, read JSONL, write contents into `state["conflicts"]` array, seal both. Document in PLAN.md.

3. **Does driver script run real GLM in unit tests, or only in smoke test?** ✅ RESOLVED: Per 53-03 Task 1+2 — unit tests mock `auxiliary_client.call_llm` via `monkeypatch.setattr`; smoke test (`--smoke` flag) calls real GLM; SC#2 verification recorded in VERIFICATION.md as `human_needed` if GLM unavailable.
   - What we know: SC#2 mandates real GLM API call with <30s latency. Unit tests should not depend on GLM (slow, flaky).
   - What's unclear: where's the line?
   - Recommendation: Unit tests mock `auxiliary_client.call_llm` (via `monkeypatch.setattr`). Smoke test (`scripts/run_screenplay_step3_roundtable.py` invoked manually with `--smoke` flag) calls real GLM. SC#2 verification = manual smoke test result recorded in VERIFICATION.md.

4. **Comparator LLM task name registration** ✅ RESOLVED: Per 53-03 Task 2 — `cli-config.yaml.example` adds `auxiliary.round_table_opinion` + `auxiliary.memory_comparator` entries with `provider: glm`, `model: glm-5.2`, `timeout: 30`.
   - What we know: `auxiliary_client.call_llm(task="...")` reads `auxiliary.{task}.{provider,model}` from `cli-config.yaml`.
   - What's unclear: are `task="round_table_opinion"` and `task="memory_comparator"` already registered as valid task names, or do they need new entries in `cli-config.yaml.example`?
   - Recommendation: Add both to `cli-config.yaml.example` with `provider: glm`, `model: glm-5.2`, `timeout: 30`. Document in VERIFICATION.md.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All Python code | ✓ | 3.13 (per CLAUDE.md) | — |
| `pyyaml` | transform script YAML emit + parse | ✓ | 6.0.3 (pinned) | — |
| `jsonschema` | Schema validation | ✓ | (core dep) | — |
| `openai` SDK | Underlying GLM client | ✓ | 2.24.0 (pinned) | — |
| `mcp` SDK | FastMCP server (already wired) | ✓ | 1.26.0 (pinned) | — |
| GLM API key | SC#2 smoke test, comparator LLM | ✓/✗ (operator-config) | — | If unavailable: SC#2 marks `human_needed` in VERIFICATION.md per CONTEXT.md decision #6; unit tests mock `call_llm` |
| `/data/workspace/kais-hermes-skills/` | MIGR-01 transform source (read-only) | ✓ (verified) | v3.0+ | If unavailable: skip MIGR-01 transform tests with `pytest.skip()` (see Example 3) |
| `~/.hermes/agents/` write access | YAML output target | ✓ (operator-owned) | — | — |

**Missing dependencies with no fallback:** None identified. All Phase 53 work is doable on the current operator machine.

**Missing dependencies with fallback:** GLM API key — graceful skip per CONTEXT.md decision #6.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 (strict mode — NOT auto) |
| Config file | `pyproject.toml:261 addopts` (no separate `pytest.ini`) |
| Quick run command | `pytest tests/agent/test_transform_skill_to_agent.py tests/agent/test_memory_arbitration.py -x` |
| Full suite command | `pytest tests/agent/ -x --timeout=30` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MIGR-01 | 9 YAMLs validate against agents-schema.yaml | unit | `pytest tests/agent/test_transform_skill_to_agent.py -x` | ❌ Wave 0 |
| MIGR-01 | screenplay lineage.transform_notes contains HOOK-09 invariant | unit | `pytest tests/agent/test_transform_skill_to_agent.py::test_screenplay_transform_preserves_HOOK_09 -x` | ❌ Wave 0 |
| MIGR-01 | SHA-256 LF-normalized | unit | `pytest tests/agent/test_transform_skill_to_agent.py::test_skill_sha256_lf_normalized -x` | ❌ Wave 0 |
| CREATIVE-01 | round_table_open → 9 get_agent_opinion → submit (mocked GLM) | integration | `pytest tests/agent/test_run_screenplay_step3.py -x` | ❌ Wave 1 |
| CREATIVE-01 | HOOK-09 schema validation on output | integration | `pytest tests/agent/test_run_screenplay_step3.py::test_step3_output_validates -x` | ❌ Wave 1 |
| CREATIVE-01 | real GLM smoke test, <30s latency | manual-only (real GLM) | `python scripts/run_screenplay_step3_roundtable.py --smoke` | ❌ Wave 1 (script) / VERIFICATION.md (result) |
| CREATIVE-02 | 2-conflict scenario produces correct arbitration | unit (mocked comparator) | `pytest tests/agent/test_memory_arbitration.py::test_2conflict_arbitration -x` | ❌ Wave 2 |
| CREATIVE-02 | scope precedence session > project > global | unit | `pytest tests/agent/test_memory_arbitration.py::test_scope_precedence -x` | ❌ Wave 2 |
| CREATIVE-02 | confidence tie-break (<0.05 Δ → deferred-to-operator) | unit | `pytest tests/agent/test_memory_arbitration.py::test_confidence_tiebreak -x` | ❌ Wave 2 |
| CREATIVE-02 | conflicts.jsonl append + atomic semantics | unit | `pytest tests/agent/test_conflict_log_writer.py -x` | ❌ Wave 2 |

### Sampling Rate
- **Per task commit:** `pytest tests/agent/test_transform_skill_to_agent.py tests/agent/test_memory_arbitration.py tests/agent/test_conflict_log_writer.py -x` (quick, mocked GLM)
- **Per wave merge:** `pytest tests/agent/ -x --timeout=30` (full agent test suite)
- **Phase gate:** Full suite green + manual `python scripts/run_screenplay_step3_roundtable.py --smoke` succeeds with latency <30s on real GLM (or `human_needed` flag in VERIFICATION.md if GLM unavailable)

### Wave 0 Gaps
- [ ] `tests/agent/test_phase52_contract.py` — proves Phase 52 imports work (see Example 1)
- [ ] `tests/agent/test_transform_skill_to_agent.py` — 9 sub-tests for MIGR-01 (see Example 3)
- [ ] `tests/fixtures/screenplay-step3-schema.json` — JSON Schema for HOOK-09 emotion_curve marker contract
- [ ] `tests/fixtures/storykernel-sample.json` — synthetic Step 1 output (input to driver)
- [ ] `tests/fixtures/memory-conflict-2conflict.json` — 2-conflict scenario fixture
- [ ] Framework already installed (`pytest`, `pytest-asyncio`, `jsonschema`, `pyyaml`) — no install needed

*(All gaps are NEW test files; no framework installation gaps.)*

## Project Constraints (from CLAUDE.md)

Listed here for the planner's compliance verification:

1. **`from __future__ import annotations`** at the top of every new Python module (PEP 604 unions on Python 3.11+).
2. **`encoding="utf-8"`** on every `open()` / `read_text()` / `write_text()` — Ruff PLW1514 will block merge otherwise.
3. **snake_case** for functions, methods, variables; **PascalCase** for classes; **UPPER_SNAKE_CASE** for module constants.
4. **`get_hermes_home()`** from `hermes_constants` — NEVER `Path.home() / ".hermes"` (autouse conftest fixture redirects HERMES_HOME per-test; `Path.home()` bypasses).
5. **Lazy %-formatting** in log calls — `logger.warning("Failed: %s", exc)`, never f-strings.
6. **`except X as exc:`** with bound name + chain preservation via `raise ... from exc`.
7. **No top-level `run_agent` imports** in `agent/*` — use `_ra()` indirection pattern. `agent/memory_arbitration.py` extension must respect this.
8. **`@pytest.mark.asyncio` explicit on async tests** — pytest-asyncio strict mode (verified `tests/agent/test_round_table_executor.py:22-24`).
9. **No bare `except:`** — catch specific types or `except Exception:`.
10. **Avoid `Path.home()`** — anti-pattern documented in CLAUDE.md + tests/conftest.py live-system guard.
11. **MEMORY.md `feedback-glm-overload-reduce-concurrency.md`** citation mandatory in serial-violation error messages (Phase 52 contract; Phase 53 inherits when extending `round_table_executor`).

## Sources

### Primary (HIGH confidence)
- `.planning/research/v10-orchestrator-design/agents-schema.yaml` — 18-field Draft 2020-12 schema, $defs.Lineage / Prerequisites / EvolutionLogEntry
- `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md §2.0-§2.19` — 75-cell transform rules (5 fields × 15 experts; subset of 9 applies), screenplay §2.4 HOOK-09 invariant, cinematographer §2.7 scene_builder absorption, style_genome §2.8 Cross-Module Alignment metric preservation
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md §3.0-§3.7` — 5-mechanism arbitration: §3.1 memory annotation, §3.2 comparator LLM prompt template (verbatim, copied into `COMPARATOR_PROMPT_TEMPLATE`), §3.3 scope precedence, §3.4 confidence tie-break (<0.05 → deferred-to-operator), §3.5 conflict log for curator, §3.6 decision tree + 5 resolution values, §3.7 3+-way / no-confidence / all-quarantined edge cases
- `.planning/research/v10-orchestrator-design/05-POC-PLAN.md §3.2` — creative slice = screenplay Step 3, 9-agent subset, HOOK-09 edge case (first "did transform work?" smoke test)
- `.planning/phases/52-infra-foundation/52-CONTEXT.md`, `52-PATTERNS.md`, `52-RESEARCH.md` — Phase 52 contract surface
- `agent/registry_loader.py` (Phase 52 actual output) — `load_agent_registry`, `load_one_agent_yaml`, `RegistryValidationError` with `json_path` + `invalid_field`
- `agent/round_table_state.py` (Phase 52 actual output) — `open_round_table`, `append_turn`, `submit_round_table_result`, `abort_round_table`, `read_and_recover_state`, `validate_round_id`, `validate_project_slug`, `RoundTableStatus` enum, atomic_json_write usage
- `agent/round_table_executor.py` (Phase 52 actual output) — `acquire_round_or_reject`, `release_round_lock`, `_serial_violation_response` with MEMORY.md citation
- `agent/memory_arbitration.py` (Phase 52 actual stub) — `memory_retrieve_scoped`, `memory_submit_record` (both return `phase53_not_implemented`), `_scoped_agent_id` ContextVar, `set_scoped_agent_id` / `get_scoped_agent_id`
- `agent/auxiliary_client.py:5168-5257` — `call_llm(task, provider, model, messages, ...)` signature + GLM 4-key rotation handling
- `mcp_serve.py:875-1450` — 7 MCP tool closures (Phase 52 actual), `get_agent_opinion` body with INFRA-04 lock contract + try/finally pattern
- `tests/conftest.py:328-360` — `_hermetic_environment` autouse fixture, HERMES_HOME redirection
- `tests/agent/test_round_table_executor.py:22-24` — pytest-asyncio strict mode documentation
- `utils.py:111-155` — `atomic_json_write` (temp + fsync + os.replace)
- `CLAUDE.md` — Technology Stack, Conventions, Anti-Patterns (esp. `from __future__ import annotations`, `encoding="utf-8"`, `get_hermes_home()`)
- `MEMORY.md::feedback-glm-overload-reduce-concurrency.md` — global concurrency==1 policy root
- `MEMORY.md::feedback-glm-5-2-only.md` — GLM model-only constraint (no other models)

### Secondary (MEDIUM confidence)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/screenplay/SKILL.md` — frontmatter (verified) + body structure (HOOK-09 contract at line 114)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/{hook_retention,cinematographer,theory_critic,editor}/SKILL.md` — frontmatter verified (tags, related_skills, expert_id, metrics)
- `tests/agent/fixtures/agents/test-coordinator.agent.yaml` (Phase 52 fixture) — minimal valid agent YAML structure reference

### Tertiary (LOW confidence)
- None. All claims trace to either v10.0 design docs (Phase 44-51 shipped artifacts) or Phase 52 actual source code (both shipped and verified by reading the files).

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — all libraries already pinned in pyproject.toml and exercised by Phase 52; no new packages
- Architecture: **HIGH** — Phase 52 contract surface read directly from source files; v10.0 design docs §2 / §3 unambiguous
- Pitfalls: **HIGH** — 5 of 7 pitfalls directly inherited from Phase 52 documentation + CLAUDE.md anti-patterns; HOOK-09 + comparator-malformed-JSON are novel but well-documented in v10.0 design
- Transform rules: **HIGH** — Phase 49 §2 75-cell table is exhaustive; per-expert edge cases for screenplay / cinematographer / hook_retention explicitly cited

**Research date:** 2026-07-07
**Valid until:** 2026-08-07 (30 days; v11.0 implementation milestone — code surface evolves, but Phase 52 contract locked)

## RESEARCH COMPLETE
