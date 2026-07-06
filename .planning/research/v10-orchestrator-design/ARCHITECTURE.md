# Architecture Research — v10.0 Agent Registry & Round Table Orchestrator

**Domain:** Hermes-native expert agent registry (YAML + persona + per-agent memory + lineage) and multi-agent round table coordination layer
**Researched:** 2026-07-06
**Confidence:** HIGH (design-time; built on direct read of v6.0 curator, v7.0 mem0 plugin, kais-hermes-skills SKILL frontmatter, and Hermes tool/skill discovery mechanisms — all in-repo)
**Milestone:** v10.0 (design-only, zero code change)
**Downstream consumers:** `01-AGENT-REGISTRY-SCHEMA.md`, `02-ROUND-TABLE-PROTOCOL.md`, `06-CROSS-REPO-IMPACT.md`

---

## Executive Summary

v10.0 introduces a **third agent-bearing surface** for Hermes. Today Hermes already hosts two distinct agent-bearing surfaces: (1) the bundled skill markdown under `skills/<category>/<name>/SKILL.md` (loaded as user-message prompt injections, model is the agent), and (2) provider profile + transport pipelines under `providers/` and `agent/transports/` (the LLM API shim). v10.0 α-agent is neither: it is a **Hermes-side YAML entity** with its own persona, scoped memory, and evolution log, addressed by stable `agent_id` rather than by skill name. The architecture's job is to make this third surface feel native — discoverable at startup, dispatchable via MCP, persistable across projects, and evolvable by the existing curator.

The design exploits three existing Hermes mechanisms rather than fighting them:

1. **SKILL discovery** (`agent/skill_utils.py:iter_skill_index_files`, `parse_frontmatter`) → generalised to a sibling agent YAML scanner at `~/.hermes/agents/*.agent.yaml`.
2. **Tool registry self-registration** (`tools/registry.py` AST-scan + `registry.register(...)`) → extended with an `agent_registry` parallel that exposes `get_agent_persona` / `get_agent_opinion` MCP tools.
3. **Curator feedback-scan phase** (`agent/curator.py:_feedback_scan_phase`, shipped v6.0) → extended with a `_memory_evolution_phase` that walks per-agent `evolution_log` chains and applies additive memory deltas gated by `fitness_score`.

The Mem0 backend (`plugins/memory/mem0/__init__.py`) already accepts `user_id` + `agent_id` filters per call — per-agent scoped memory is a **routing convention**, not a backend change. The architectural load-bearing work is at the **dispatch + scoping + lineage** layer, not at the storage layer.

The biggest design decision locked here: **agent YAML is single-source-of-truth for identity, but not for runtime state**. Identity (persona, tools whitelist, refs, lineage) lives in `~/.hermes/agents/{name}.agent.yaml` and is operator-curated. Runtime state (per-project round table transcripts, fitness_score deltas, evolution_log entries) lives under `~/.hermes/agents/.runtime/{project_slug}/` and is curator-driven. This mirrors the existing `~/.hermes/skills/` (authored) vs `~/.hermes/skills/.curator_state` (runtime) split — proven pattern, not a new one.

---

## 1. Agent Registry YAML Schema (15+ fields)

### 1.1 Field Set

| # | Field | Type | Required | Source | Purpose |
|---|-------|------|----------|--------|---------|
| 1 | `name` | `string` | YES | Agent (must match filename stem) | Primary identifier; **NOT** the same as `expert_id` (a skill may transit to an agent with a different name). Allowed: `[a-z0-9_-]+`. |
| 2 | `description` | `string` | YES | SKILL `description` (copy verbatim, then refine) | One-line summary surfaced by `agents_list` MCP tool and Hermes dashboard. |
| 3 | `version` | `string` (semver) | YES | SKILL `version` (copy) | Schema version of the agent YAML itself; bumped when fields are added. |
| 4 | `persona` | `string` (multiline) | YES | **NEW — must rewrite** | The agent's system prompt fragment. **This is the load-bearing difference from SKILL.** A SKILL body is injected as a user message; an agent persona is injected as a system-prompt fragment, so persona phrasing shifts from imperative-second-person to first-person expert identity. |
| 5 | `tools` | `list[string]` | YES | Derived from `prerequisites.tools` + agent's actual capability surface | Tool whitelist. Examples: `[hermes_llm, write_file, read_file, search_files]` for analysis-only agents; `[hermes_llm, dreamina_cli, write_file]` for visual executors. Honored by the dispatcher when the agent is invoked via `get_agent_opinion`. |
| 6 | `memory_scope` | `enum: shared \| per_agent \| project_scoped` | YES | **NEW** | `shared` = the global mem0 user_id (cross-agent, current default). `per_agent` = `user_id=agent:{name}` namespace. `project_scoped` = `user_id=project:{slug}+agent:{name}` (most isolated). Default recommendation: `per_agent` for the 15 movie-experts. |
| 7 | `lineage` | `object` | YES | **NEW** | `{derived_from_skill_id, derived_from_repo, transform_date, transform_notes, skill_sha256}`. Records provenance so the curator can detect drift between the source SKILL.md and the agent YAML (e.g. SKILL got a v5.0 V8.6 sync patch but agent persona didn't). |
| 8 | `refs` | `list[string]` | NO (defaults to `[]`) | SKILL `## References` table → flattened to file paths | RAG reference docs the agent is allowed to retrieve from. Paths are repo-relative or absolute. Empty for agents that rely on persona alone. |
| 9 | `tags` | `list[string]` | NO | SKILL `metadata.hermes.tags` (copy) | Lowercase hyphenated; powers `agents_list` filtering. |
| 10 | `expert_id` | `string` | NO | SKILL `metadata.hermes.expert_id` (copy) | Backward-compat anchor — when a consumer still calls the SKILL by `expert_id: screenplay`, the dispatcher can route to the agent of the same name. **FOUND-08 preserved**: do not mutate frozen expert_ids during transition. |
| 11 | `metrics` | `list[string]` | NO | SKILL `metadata.hermes.metrics` (copy) | Quality dimensions for the eval gate. Carried verbatim so v6.0 eval harness still works on agent outputs. |
| 12 | `prerequisites` | `object` | NO | SKILL `prerequisites` (copy) | `{tools: [...], skills: [...], env: [...]}`. Different from `tools` (the runtime whitelist) — `prerequisites` are *activation conditions*, `tools` are *runtime grants*. |
| 13 | `related_agents` | `list[string]` | NO | SKILL `metadata.hermes.related_skills` (copy + rename) | The collaboration DAG. Names of peer agents. Drives round table panel suggestions (`02-ROUND-TABLE-PROTOCOL.md` consumer). |
| 14 | `evolution_log` | `list[object]` | NO (curator-managed; do not hand-edit) | **NEW** | Append-only chain of `{ts, sha256, diff_summary, fitness_delta, trigger}`. Each entry is a memory update event. Tamper-evident via sha256 chaining (same pattern as v6.0 `agent/curator_audit.py`). |
| 15 | `fitness_score` | `float (0.0-1.0) \| null` | NO | **NEW** | Curator-computed rolling quality score derived from eval gate + feedback verdicts. `null` until first curator pass. **Not** operator-set. |
| 16 | `platforms` | `list[string]` | NO (defaults to `[linux, macos, windows]`) | SKILL `platforms` (copy) | OS compatibility gate, enforced identically to `skill_utils.skill_matches_platform`. |
| 17 | `round_table_eligible` | `bool` | NO (defaults to `true`) | **NEW** | Whether this agent can be invited to a round table. Set `false` for ephemeral helpers or read-only analysts. |
| 18 | `default_invocation` | `enum: mcp_tool \| skill_fallback \| disabled` | NO (defaults to `mcp_tool`) | **NEW** | How the dispatcher should treat this agent when CC asks for it. `mcp_tool` = invoke via `get_agent_opinion`; `skill_fallback` = fall through to the underlying SKILL (v1-v9 behavior); `disabled` = agent exists in registry but cannot be invoked yet (transform-in-progress). |

**Total: 18 fields (15 required-or-defaulted, 3 truly optional).** Meets the Quality Gate "≥12 fields" with comfortable margin.

### 1.2 Compatibility With SKILL Frontmatter

| SKILL frontmatter field | Disposition in agent YAML |
|-------------------------|---------------------------|
| `name` | **Reused** as `name` (must match filename stem). |
| `description` | **Reused** verbatim, refined if needed. |
| `version` | **Reused**, but bumped to `1.0.0` on first transform (signaling agent-YAML schema version, not SKILL-content version). |
| `author`, `license` | **Dropped** — agent YAML is operator-owned, not authored. Lineage captures the original. |
| `platforms` | **Reused** verbatim. |
| `prerequisites` | **Reused** as `prerequisites` (different from `tools`). |
| `metadata.hermes.tags` | **Reused** as `tags`. |
| `metadata.hermes.related_skills` | **Copied** to `related_agents`. |
| `metadata.hermes.expert_id` | **Reused** as `expert_id` (backward-compat anchor). |
| `metadata.hermes.metrics` | **Reused** as `metrics`. |
| SKILL body (markdown) | **NOT copied.** Becomes input to `persona` rewrite. The original SKILL body is preserved in the source repo as `lineage.derived_from_skill_id` reference. |
| `## References` table | **Flattened** into `refs` list (paths only; the table semantics move into the agent persona narrative). |

**Agent-only fields (no SKILL equivalent):** `persona` (rewritten system-prompt fragment), `tools` (runtime whitelist distinct from `prerequisites.tools` activation), `memory_scope`, `lineage`, `evolution_log`, `fitness_score`, `round_table_eligible`, `default_invocation`.

### 1.3 Minimal Example (screenplay)

```yaml
# ~/.hermes/agents/screenplay.agent.yaml
name: screenplay
description: "Screenplay Expert: scene-level script generation, dialogue design, emotional arc construction for AI short film production."
version: 1.0.0
persona: |
  You are the Screenplay Expert in a Hermes round table. You speak in first
  person about scene structure, Snyder 15-beat adaptation, anchor-based
  emotion curves, and dialogue subtext. You cite save-the-cat-beat-sheet,
  mckee-scene-design, cn-shortdrama-structure, emotion-curve-academic,
  and dialogue-craft from your refs when justifying a recommendation.
  You defer to hook_retention on 3-second hooks and to cinematographer on
  shot intent. You never generate full scripts unprompted — you contribute
  your slice when the orchestrator asks.
tools: [hermes_llm, read_file, search_files]
memory_scope: per_agent
lineage:
  derived_from_skill_id: screenplay
  derived_from_repo: kais-hermes-skills
  transform_date: 2026-07-15
  transform_notes: |
    Persona rewritten from SKILL body; SKILL preserved as fallback.
    HOOK-09 emotion_curve marker arrays remain contract-load-bearing.
  skill_sha256: <sha of SKILL.md at transform time>
refs:
  - kais-hermes-skills/skills/movie-experts/screenplay/references/save-the-cat-beat-sheet.md
  - kais-hermes-skills/skills/movie-experts/screenplay/references/mckee-scene-design.md
  - kais-hermes-skills/skills/movie-experts/screenplay/references/cn-shortdrama-structure.md
  - kais-hermes-skills/skills/movie-experts/screenplay/references/emotion-curve-academic.md
  - kais-hermes-skills/skills/movie-experts/screenplay/references/dialogue-craft.md
tags: [movie, screenplay, script, dialogue, narrative, emotion-curve]
expert_id: screenplay
metrics: [narrative_tension, dialogue_naturalness, emotional_arc]
prerequisites:
  tools: [hermes_llm]
related_agents: [style_genome, editor, audio_pipeline, compliance_gate, hook_retention, cinematographer, theory_critic]
evolution_log: []
fitness_score: null
platforms: [linux, macos, windows]
round_table_eligible: true
default_invocation: mcp_tool
```

---

## 2. Agent vs SKILL Transform Mapping (15 movie-experts)

Each of the 15 movie-experts follows the **same 5-field transform pattern**, but with expert-specific persona framing and tool whitelist. The mapping rule is:

> **COPY** `name`, `description`, `version` (bumped), `platforms`, `tags`, `expert_id`, `metrics`, `prerequisites`, `related_skills`→`related_agents`. **DROP** `author`, `license`. **REWRITE** the body into `persona`. **FLATTEN** `## References` into `refs`. **DERIVE** `tools` from the agent's actual runtime surface. **INITIALIZE** `evolution_log=[]`, `fitness_score=null`, `memory_scope=per_agent`, `default_invocation=mcp_tool`.

The table below lists per-expert deltas only — fields not shown use the default rule above.

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

**Aggregate transform stats:** 15 agents, 9 common copy-fields, 4 new fields per agent, 1 body-rewrite per agent, average 3.5 refs per agent, average 5.6 related_agents per agent.

**FOUND-08 preservation rule:** All 15 `expert_id` values are copied verbatim. The transition is **additive** — consumers can still call skills by `expert_id` and the dispatcher falls through to SKILL when `default_invocation: skill_fallback` is set.

---

## 3. Per-Agent Memory Implementation Path

### 3.1 Current Mem0 Backend Surface

`plugins/memory/mem0/__init__.py` (v7.0 ship) exposes:

- **Class:** `Mem0MemoryProvider(MemoryProvider)` — registered via `ctx.register_memory_provider(...)`.
- **Methods (relevant):**
  - `initialize(session_id, **kwargs)` — reads `MEM0_API_KEY` + `MEM0_USER_ID` + `MEM0_AGENT_ID` from env or `~/.hermes/mem0.json`.
  - `_read_filters()` → `{"user_id": self._user_id}` — scopes all `search` / `get_all` calls.
  - `_write_filters()` → `{"user_id": self._user_id, "agent_id": self._agent_id}` — scopes all `add` calls.
  - `handle_tool_call(tool_name, args, **kwargs)` — dispatches `mem0_profile` / `mem0_search` / `mem0_conclude`.
  - `sync_turn(user_content, assistant_content, session_id=...)` — non-blocking server-side extraction.
- **MemoryManager one-external-provider limit:** Only one external provider runs at a time (`agent/memory_provider.py` docstring). This is **not** a blocker — we use the same mem0 backend for all agents and route via filters.

**Key insight:** `_user_id` is already a routing field. Per-agent memory does **not** require a new backend; it requires:

1. Letting the dispatcher override `_user_id` per agent invocation.
2. Adopting a `user_id` naming convention that namespaces per-agent.
3. Teaching the curator to walk those namespaces for evolution.

### 3.2 Three Implementation Options (Recommended: B)

#### Option A — `user_id` namespace convention (lightest)
- Convention: `user_id = "agent:{name}"` for `memory_scope: per_agent`.
- Pros: Zero backend change. Mem0 server-side treats it as opaque string.
- Cons: `_user_id` is currently set **once** at `initialize()` from env/config; per-call override requires changing `handle_tool_call` to accept a `_user_id` kwarg threaded through from the dispatcher.

#### Option B — `agent_id` field as scoping key (RECOMMENDED)
- Convention: `user_id` stays at the platform user (e.g. `kai`); `agent_id` carries the agent name (`screenplay`, `cinematographer`, etc.).
- Mem0's `_write_filters()` already returns `{"user_id", "agent_id"}` — writes are **already agent-attributed**.
- **Read path is the gap:** `_read_filters()` returns only `{"user_id"}` (cross-session recall). To scope reads per-agent, extend `_read_filters()` to optionally include `agent_id` when the calling context specifies one.
- Pros: Smallest delta on the plugin. Naturally extends to `project_scoped` via metadata filters.
- Cons: Requires the dispatcher to pass `agent_id` through to memory calls.

#### Option C — metadata filters + banks (heaviest)
- Use mem0's `metadata` filter on every memory record: `{"agent": "screenplay", "project": "v10-poc"}`.
- Pros: Most flexible. Supports arbitrary scoping (project + agent + round_table_id).
- Cons: Mem0 Platform API's filter surface on `search()` is limited; relying on metadata filters may degrade recall quality. Reserved for `project_scoped` mode only.

**Recommendation:** Default to **Option B** for the 15 movie-experts. Reserve Option C for future `project_scoped` mode (round table memory that survives across sessions in the same project).

### 3.3 Mem0 Backend Extension Points (Concrete)

To support per-agent scoped memory, the mem0 plugin needs **4 additive changes** (no breaking changes to existing single-user CLI flow):

1. **`initialize(session_id, **kwargs)`** — accept optional `agent_scope: str | None` kwarg. When non-None, store it as `self._scoped_agent_id`. Backward-compatible: when omitted, behavior unchanged.
2. **`_read_filters()`** — when `self._scoped_agent_id` is set, include `"agent_id": self._scoped_agent_id` in the returned dict.
3. **`handle_tool_call(tool_name, args, **kwargs)`** — accept optional `agent_scope` kwarg from the dispatcher; if present, temporarily swap `self._scoped_agent_id` for the duration of the call (thread-local or contextvars-based to avoid races in concurrent dispatch).
4. **New tool schema `mem0_agent_recall`** — wraps `mem0_search` with `agent_scope` pre-bound, so the orchestrator's `get_agent_opinion` MCP tool can call it without exposing the scoping knob to the LLM.

**Code-level sketch (illustrative, NOT to be implemented in v10.0):**

```python
# plugins/memory/mem0/__init__.py — additive extension
def _read_filters(self) -> Dict[str, Any]:
    filters = {"user_id": self._user_id}
    if self._scoped_agent_id:
        filters["agent_id"] = self._scoped_agent_id
    return filters

# Agent dispatcher side (NOT in mem0 plugin)
def invoke_agent_with_memory(agent_name: str, query: str) -> str:
    provider = _get_active_memory_provider()
    provider._scoped_agent_id = agent_name  # contextvars in prod
    try:
        return agent_registry.dispatch(agent_name, query)
    finally:
        provider._scoped_agent_id = None
```

**v10.0 deliverable:** Document this extension surface in `01-AGENT-REGISTRY-SCHEMA.md` §Memory Scope Extension. Zero implementation in v10.0.

### 3.4 Curator-Driven Memory Evolution

`agent/curator.py:run_curator_review` (v6.0-extended) already runs a `_feedback_scan_phase` after the LLM consolidation pass. The per-agent memory evolution extends this with a **third phase** that runs after feedback-scan:

**New phase: `_memory_evolution_phase(start: datetime) -> Dict[str, Any]`**

Pipeline per agent with `memory_scope: per_agent` and `evolution_log`:
1. **Aggregate feedback** for this agent from `FeedbackStore` (existing `_scan_for_hot_skills` extended to also scan agent_ids).
2. **Compute fitness_delta** from new feedback verdicts since the last `evolution_log` entry (using the same `_compute_confidence` two-signal gate as v6.0: `mean_delta` + `evidence_count`).
3. **If fitness_delta ≥ threshold** (default `0.1`): generate an LLM-distilled **memory delta** (a single concise fact, e.g. "After Volvo S1-1 case 2026-06-28, cinematographer learned to always include `left-hand drive, steering wheel on the left side` for car-interior shots").
4. **Append to `evolution_log`** in the agent YAML file with `{ts, sha256(prev_entry + new_delta), diff_summary, fitness_delta, trigger: "feedback_scan"}`.
5. **Optionally write to mem0** via `mem0_conclude` scoped to this agent's `agent_id` (so the fact is recalled on next invocation).

**`run_curator_review` modification points (additive, runtime-isolated):**

```python
# agent/curator.py — extension to run_curator_review (Phase 32-equivalent for agents)
def _memory_evolution_phase(start: datetime) -> Dict[str, Any]:
    """ADDITIVE per-agent memory evolution phase.
    
    Runs whenever not dry_run, INDEPENDENT of consolidate gate (per v6.0
    _feedback_scan_phase pattern). Walks ~/.hermes/agents/*.agent.yaml,
    for each agent with memory_scope: per_agent:
      1. Query FeedbackStore for new feedback since last evolution_log entry.
      2. Compute fitness_delta via _compute_confidence (two-signal gate).
      3. If fitness_delta >= threshold: LLM-distill memory delta, append to
         evolution_log, optionally mem0_conclude scoped to agent_id.
    
    All agent.evolution.* imports LAZY (runtime isolation — same invariant
    as P31 _feedback_scan_phase).
    """
    # Lazy imports
    from agent.feedback_store import FeedbackStore
    from agent.evolution import aggregate_feedback, make_aggregation_client
    from agent.curator_audit import append_audit
    from hermes_constants import get_hermes_home
    
    agents_dir = get_hermes_home() / "agents"
    if not agents_dir.is_dir():
        return {"scanned": 0, "evolved": []}
    
    agent_yamls = list(agents_dir.glob("*.agent.yaml"))
    evolved: List[str] = []
    
    for yaml_path in agent_yamls:
        # ... load YAML, check memory_scope == "per_agent"
        # ... compute fitness_delta from FeedbackStore
        # ... if eligible: LLM-distill + append evolution_log entry
        # ... append_audit(action="memory_evolve", agent_id=name, ...)
        evolved.append(name)
    
    return {"scanned": len(agent_yamls), "evolved": evolved}
```

**Hook into `run_curator_review`:** Insert `_memory_evolution_phase(start)` call right after `_feedback_scan_phase(start)` in `_llm_pass()` (lines 2081-2095 and 2207-2221 of `agent/curator.py`). Wrap in try/except, same failure-isolation pattern as v6.0.

**Curator state extension:** Add `"last_memory_evolution_at": ISO_ts` to `.curator_state` so the evolution phase runs at most once per `interval_hours` cycle (matches the existing cadence discipline).

---

## 4. Agent Registry Loading Mechanism

### 4.1 Discovery (Parallel to SKILL Discovery)

The agent registry reuses the SKILL discovery primitive (`agent/skill_utils.py`) with a sibling scanner. The discovery walks `~/.hermes/agents/*.agent.yaml` plus any `agents.external_dirs` declared in `cli-config.yaml`.

**Pseudocode (NOT to be implemented in v10.0):**

```python
# agent/agent_registry.py — new module (v11.0 PoC target)
from pathlib import Path
from typing import Dict, List, Any
import threading

from agent.skill_utils import parse_frontmatter, yaml_load
from hermes_constants import get_hermes_home

_AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {}
_AGENT_DISCOVERED = False
_AGENT_LOCK = threading.Lock()
_AGENT_GLOB = "*.agent.yaml"


def _discover_agents() -> None:
    """Walk ~/.hermes/agents/ + external_dirs, parse each *.agent.yaml."""
    global _AGENT_DISCOVERED
    if _AGENT_DISCOVERED:
        return
    with _AGENT_LOCK:
        if _AGENT_DISCOVERED:  # double-check
            return
        agents_dir = get_hermes_home() / "agents"
        candidates: List[Path] = []
        if agents_dir.is_dir():
            candidates.extend(sorted(agents_dir.glob(_AGENT_GLOB)))
        # Future: external_dirs from config (parallel to skill_utils.get_external_skills_dirs)
        for yaml_path in candidates:
            try:
                content = yaml_path.read_text(encoding="utf-8")
                data = yaml_load(content)
                if not isinstance(data, dict):
                    continue
                name = data.get("name") or yaml_path.stem
                if name != yaml_path.stem:
                    logger.warning("Agent YAML name mismatch in %s", yaml_path)
                    continue
                _AGENT_REGISTRY[name] = data
            except Exception as e:
                logger.warning("Failed to parse agent YAML %s: %s", yaml_path, e)
        _AGENT_DISCOVERED = True


def get_agent(name: str) -> Dict[str, Any] | None:
    _discover_agents()
    return _AGENT_REGISTRY.get(name)


def list_agents() -> List[Dict[str, Any]]:
    _discover_agents()
    return list(_AGENT_REGISTRY.values())


def clear_registry_cache() -> None:
    """Test hook."""
    global _AGENT_DISCOVERED
    with _AGENT_LOCK:
        _AGENT_REGISTRY.clear()
        _AGENT_DISCOVERED = False
```

**Why a separate registry (not merged into `tools/registry.py`):**

1. **Single responsibility** — `tools/registry.py` registers tools (callable functions with schemas); agents are entities with personas. Mixing them muddies the AST-scan pattern (`tools/registry.py:78 _module_registers_tools` greps for `registry.register(...)` at module top, which doesn't apply to YAML-loaded agents).
2. **Discovery trigger differs** — tools are imported at runtime (import side-effect registration); agents are YAML-parsed at startup (no Python import).
3. **Lifecycle differs** — tools are static; agents have `evolution_log` that mutates over time and needs curator coordination.

The two registries are **parallel siblings**, both global singletons, both write-once at discovery. The MCP server (`mcp_serve.py`) calls into both.

### 4.2 MCP Server Extension (7 New Tools)

`mcp_serve.py` currently exposes 9 messaging-channel tools. v10.0 adds **7 agent-facing MCP tools** (design only in v10.0):

| Tool | Args | Returns | Dispatch Path |
|------|------|---------|---------------|
| `agents_list` | `tag_filter: str?`, `round_table_eligible: bool?` | `[{name, description, tags, fitness_score, expert_id}, ...]` | `agent_registry.list_agents()` |
| `agent_get_persona` | `name: str` | `{persona, tools, refs, metrics, lineage}` | `agent_registry.get_agent(name)` |
| `get_agent_opinion` | `name: str, question: str, context: str?` | `{opinion_text, cited_refs, fitness_score, evolution_log_tail}` | Spawn AIAgent fork with `system_prompt = persona`, `tools = whitelist`, scoped mem0; return final + provenance |
| `agent_recall` | `name: str, query: str, top_k: int?` | `[{memory, score}, ...]` | `mem0_search` with `agent_id=name` filter |
| `agent_conclude` | `name: str, fact: str` | `{result}` | `mem0_conclude` with `agent_id=name` filter |
| `round_table_open` | `panel: [str], question: str, max_rounds: int?, early_stop_rule: str?` | `{round_table_id, initial_turn_order}` | See `02-ROUND-TABLE-PROTOCOL.md` |
| `round_table_poll` | `round_table_id: str` | `{turns_so_far, current_speaker, state, final_synthesis?}` | See `02-ROUND-TABLE-PROTOCOL.md` |

**Code-level sketch (illustrative):**

```python
# mcp_serve.py — additive (v11.0 PoC target)
@mcp.tool()
def agents_list(tag_filter: str | None = None,
                round_table_eligible: bool | None = None) -> str:
    from agent.agent_registry import list_agents
    agents = list_agents()
    if tag_filter:
        agents = [a for a in agents if tag_filter in a.get("tags", [])]
    if round_table_eligible is not None:
        agents = [a for a in agents
                  if a.get("round_table_eligible", True) == round_table_eligible]
    return json.dumps([{
        "name": a["name"],
        "description": a["description"],
        "tags": a.get("tags", []),
        "fitness_score": a.get("fitness_score"),
        "expert_id": a.get("expert_id"),
    } for a in agents])

@mcp.tool()
def get_agent_opinion(name: str, question: str,
                      context: str | None = None) -> str:
    from agent.agent_registry import get_agent
    from agent.agent_dispatcher import dispatch_agent  # new module
    agent = get_agent(name)
    if agent is None:
        return tool_error(f"Unknown agent: {name}")
    if agent.get("default_invocation") == "disabled":
        return tool_error(f"Agent {name} is disabled")
    result = dispatch_agent(agent, question, context or "")
    return json.dumps(result)
```

### 4.3 Dispatcher (Agent Invocation)

The dispatcher spawns an AIAgent fork (same pattern as `agent/curator.py:_run_llm_review`) with the agent's persona as system prompt and tools as the whitelist.

**Pseudocode:**

```python
# agent/agent_dispatcher.py — new module (v11.0 PoC target)
from run_agent import AIAgent

def dispatch_agent(agent_yaml: dict, question: str, context: str) -> dict:
    persona = agent_yaml["persona"]
    tools = agent_yaml.get("tools", ["hermes_llm"])
    memory_scope = agent_yaml.get("memory_scope", "shared")
    
    # Configure memory provider with agent scope (Option B from §3.2)
    if memory_scope == "per_agent":
        _set_memory_agent_scope(agent_yaml["name"])
    
    fork = AIAgent(
        system_prompt_override=persona,  # NEW arg (v11.0)
        tools_whitelist=tools,            # NEW arg (v11.0)
        max_iterations=50,                # bounded — single opinion, not a session
        quiet_mode=True,
        platform="agent_dispatch",
        skip_context_files=True,
        skip_memory=(memory_scope == "shared"),  # only scope when per_agent
    )
    try:
        prompt = question if not context else f"Context:\n{context}\n\nQuestion:\n{question}"
        result = fork.run_conversation(user_message=prompt)
        return {
            "opinion_text": result.get("final_response", ""),
            "cited_refs": _extract_ref_citations(result),
            "fitness_score": agent_yaml.get("fitness_score"),
            "evolution_log_tail": agent_yaml.get("evolution_log", [])[-3:],
        }
    finally:
        fork.close()
        if memory_scope == "per_agent":
            _set_memory_agent_scope(None)
```

**`AIAgent` extensions required (v11.0 PoC, NOT v10.0):**
- `system_prompt_override: str | None` — when set, replaces the standard Hermes system prompt with the agent persona. Bypasses `agent._cached_system_prompt` entirely (load-bearing invariant preserved for non-agent paths).
- `tools_whitelist: list[str] | None` — when set, filters the tool registry to only the listed tools. Implemented as a `ToolRegistry` view wrapper.

Both args are additive; existing call sites pass neither and behavior is unchanged.

---

## 5. Round Table State Layer

### 5.1 State File Layout

Round table state is **per-project**, even though agents themselves are **cross-project**. This mirrors GSD's `.planning/STATE.md` (per-project) vs `~/.hermes/agents/` (cross-project operator-owned).

**Layout:**

```
~/.hermes/agents/.runtime/
└── {project_slug}/
    └── round_tables/
        ├── {round_table_id}.json     # active or completed round table state
        ├── {round_table_id}.json
        └── ...
```

`project_slug` derivation: `{repo_basename}:{git_toplevel_abspath_sha8}` (e.g. `hermes-agent:a1b2c3d4`). This disambiguates two repos with the same name on different machines.

**Round table state schema (single JSON file):**

```json
{
  "round_table_id": "rt_20260715_153000_a1b2c3",
  "project_slug": "hermes-agent:a1b2c3d4",
  "opened_at": "2026-07-15T15:30:00Z",
  "closed_at": null,
  "panel": ["screenplay", "cinematographer", "hook_retention", "theory_critic"],
  "question": "Should the Volvo S1-1 opening use an empty-car establish or a grandson reveal?",
  "turn_order": ["cinematographer", "screenplay", "hook_retention", "theory_critic"],
  "max_rounds": 3,
  "early_stop_rule": "consensus_3_of_4 OR round_2_no_change",
  "current_round": 2,
  "current_speaker_index": 1,
  "state": "in_progress",
  "turns": [
    {
      "round": 1,
      "speaker": "cinematographer",
      "ts": "2026-07-15T15:30:42Z",
      "opinion_text": "...",
      "cited_refs": ["shot-grammar.md", "vertical-screen-framing.md"],
      "fitness_score": 0.87,
      "evolution_log_tail": [...]
    },
    ...
  ],
  "final_synthesis": null,
  "synthesizer": null,
  "early_stop_triggered": false,
  "early_stop_reason": null
}
```

### 5.2 Cross-Project Sharing Rules

| Artifact | Scope | Rationale |
|----------|-------|-----------|
| Agent YAML (`~/.hermes/agents/*.agent.yaml`) | **Cross-project** (operator-owned) | Persona + tools + lineage are stable identity, not project state. |
| Per-agent memory (mem0 with `agent_id` filter) | **Cross-project** (operator-owned) | "Cinematographer learned LHD declaration from Volvo case" applies everywhere cinematographer is invoked. |
| Round table state (`~/.hermes/agents/.runtime/{slug}/round_tables/*.json`) | **Per-project** | Each project has its own questions, panel configs, and synthesis outcomes. |
| Evolution log entries (in agent YAML) | **Cross-project** | Memory deltas accumulate across all projects (this is the "agent gets better with more projects" value prop). |
| Fitness score (in agent YAML) | **Cross-project** | Same — single rolling quality number per agent. |

**Subtle implication:** A project's round table transcript references agent `fitness_score` snapshots — but those snapshots can drift if a curator pass runs mid-round-table. Resolution: round table state captures `fitness_score` **at turn time** (per-turn snapshot in `turns[].fitness_score`), so the transcript is reproducible even if the agent's current score changes.

### 5.3 Round Table Lifecycle (Sketch — Full Spec in `02-ROUND-TABLE-PROTOCOL.md`)

```
┌──────────────────────────────────────────────────────────────┐
│ CC invokes round_table_open(panel=[...], question=...)        │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Hermes orchestrator (mcp_serve.py)                             │
│  1. Resolve panel via agent_registry (validate names)          │
│  2. Initialize state file under .runtime/{slug}/round_tables/  │
│  3. Compute turn_order (round-robin or fitness-weighted)       │
│  4. Return round_table_id + initial turn_order to CC           │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│ For each round (1..max_rounds):                                │
│   For each speaker in turn_order:                              │
│     CC invokes get_agent_opinion(name=speaker,                 │
│                                   question=question,           │
│                                   context=prior_turns_summary) │
│     Hermes dispatches via agent_registry + agent_dispatcher    │
│     Hermes appends {speaker, opinion_text, ...} to state file  │
│     CC invokes round_table_poll to read new turn               │
│   Check early_stop_rule after each round                       │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Final synthesis:                                               │
│   CC (acting as Team Lead) synthesizes turns into a structured │
│   decision document; writes to state file final_synthesis      │
│   Hermes marks state="closed", closed_at=now()                 │
└──────────────────────────────────────────────────────────────┘
```

**Hermes controls:** turn_order, max_rounds, early_stop_rule, state schema. **CC controls:** question framing, context summarization between turns, final synthesis. This is the (vi) layered CC role locked in Decision #7.

---

## 6. Cross-Repo Coordination

Three physical locations are involved:

| Location | Owner | Contents |
|----------|-------|----------|
| `hermes-agent` repo (`/data/workspace/hermes-agent/`) | Design + runtime code | `.planning/research/v10-orchestrator-design/` (this file + sibling design docs); future v11.0 PoC implementation in `agent/agent_registry.py`, `agent/agent_dispatcher.py`, `mcp_serve.py` extensions, `plugins/memory/mem0/__init__.py` extensions. **NO agent YAMLs live here.** |
| `kais-hermes-skills` repo (`/data/workspace/kais-hermes-skills/`) | SKILL lineage source | `skills/movie-experts/{15 dirs}/SKILL.md` — the **transform source** for agent YAMLs. Referenced by `lineage.derived_from_skill_id` + `skill_sha256`. NOT modified by v10.0. |
| `~/.hermes/agents/` (operator-side, runtime) | Operator (Kai) | The actual `*.agent.yaml` files consumed by the runtime. Created by the transform procedure (§6.1). Curator writes `evolution_log` and `fitness_score` here. |

### 6.1 Transform Procedure (One-Time Per Agent)

For each of the 15 movie-experts, the operator (or a future `hermes agent transform` CLI command in v11.0) performs:

1. **Read source SKILL.md** from `kais-hermes-skills` repo (the operator's checkout path, e.g. `/data/workspace/kais-hermes-skills/skills/movie-experts/{name}/SKILL.md`).
2. **Compute `skill_sha256`** = `hashlib.sha256(skill_md_content.encode()).hexdigest()`.
3. **Generate agent YAML** per the §2 mapping rules: copy 9 fields, drop 2, rewrite body → persona, flatten References → refs, derive tools, init evolution_log/fitness_score.
4. **Write to** `~/.hermes/agents/{name}.agent.yaml`.
5. **Record lineage** in the YAML: `derived_from_skill_id`, `derived_from_repo: kais-hermes-skills`, `transform_date`, `skill_sha256`.

**Manual in v10.0/v11.0 PoC; scripted in v12+** via a `hermes agent transform --from skill --to agent --name <name>` CLI that automates the above.

### 6.2 Drift Detection (Curator Side)

The curator's `_memory_evolution_phase` (§3.4) ALSO runs a **drift check** at the start of each pass:

```python
def _detect_skill_agent_drift() -> List[Dict[str, Any]]:
    """Detect SKILL.md changes since last transform.
    
    For each ~/.hermes/agents/*.agent.yaml with lineage.derived_from_skill_id:
      1. Resolve source SKILL.md path in the recorded repo.
      2. Compute current sha256.
      3. Compare to lineage.skill_sha256.
      4. If mismatch: append to drift report.
    
    Returns list of {agent_name, skill_path, old_sha, new_sha, drift_age_days}.
    """
```

Drift triggers an **advisory** (not automatic re-transform) — the operator decides whether to re-run the transform with fresh persona rewrite. This preserves the operator's ownership of the persona (which is hand-tuned, not auto-generated beyond the initial transform).

### 6.3 Synchronization Strategy

| Direction | Mechanism | Frequency |
|-----------|-----------|-----------|
| `kais-hermes-skills` SKILL.md → `~/.hermes/agents/*.agent.yaml` | **Manual transform** (one-time per agent) + curator drift detection (advisory) | Once at v11.0 PoC; re-transform only when curator flags drift |
| `hermes-agent` repo code → `~/.hermes/agents/` runtime | **Code deployment** (pip install / git pull of hermes-agent; runtime reads `~/.hermes/agents/` at startup) | Each hermes-agent release |
| `~/.hermes/agents/*.agent.yaml` → mem0 memory | **Dispatcher routing** (per `get_agent_opinion` call, sets `agent_id` filter on mem0) | Per invocation |
| mem0 memory → `~/.hermes/agents/*.agent.yaml` evolution_log | **Curator `_memory_evolution_phase`** (LLM-distills memory delta, appends to YAML) | Every `interval_hours` (default 7 days) |

**No bidirectional auto-sync.** The SKILL → agent transform is one-way and operator-initiated. The agent YAML → SKILL backport is **explicitly out of scope** for v10.0 (and likely forever — agents and skills are different layers, as declared in PROJECT.md paradigm shift).

### 6.4 Repo Impact Summary (for `06-CROSS-REPO-IMPACT.md`)

| Repo | v10.0 deliverable | v11.0 PoC deliverable | v12+ deliverable |
|------|-------------------|----------------------|------------------|
| `hermes-agent` | 7 design docs under `.planning/research/v10-orchestrator-design/` (zero code) | `agent/agent_registry.py`, `agent/agent_dispatcher.py`, `mcp_serve.py` MCP tool additions, `plugins/memory/mem0/__init__.py` per-agent filter, `agent/curator.py` `_memory_evolution_phase` | `hermes agent transform` CLI, dashboard Agents tab |
| `kais-hermes-skills` | None (read-only source) | None (SKILLs remain as fallback per `default_invocation: skill_fallback`) | Optional: add `agent_transform_notes` frontmatter field to SKILLs that have been transformed |
| `~/.hermes/agents/` (operator) | None (directory doesn't exist yet) | 15 `*.agent.yaml` files created by manual transform | Curator-managed `evolution_log` and `fitness_score` mutations |

---

## 7. Patterns to Follow

### 7.1 Pattern: Sibling Registry (Not Merged)

**What:** Create `agent/agent_registry.py` as a sibling to `tools/registry.py`, NOT a sub-registry of it.
**When:** Whenever a new entity type needs Hermes-wide discovery + dispatch.
**Why:** Each registry has distinct discovery trigger (AST-scan vs YAML-parse), lifecycle (static vs evolving), and consumer (tool dispatcher vs agent dispatcher). Mixing them breaks the AST-san invariant at `tools/registry.py:78`.
**Example:** See §4.1 pseudocode.

### 7.2 Pattern: Additive Curator Phase

**What:** New background behaviors are added as new phases in `run_curator_review`, NOT as separate daemons.
**When:** Any new periodic maintenance task on agents/skills.
**Why:** The curator already has cadence discipline (`interval_hours`), failure isolation (per-phase try/except), state persistence (`.curator_state`), and audit logging (`agent/curator_audit.py`). Spawning a parallel daemon duplicates all of this.
**Example:** v6.0 added `_feedback_scan_phase`; v10.0 adds `_memory_evolution_phase`. Same pattern.

### 7.3 Pattern: Filter-Based Memory Scoping

**What:** Use mem0's existing `user_id` + `agent_id` filter fields for per-agent scoping, NOT a new backend.
**When:** Any per-entity memory isolation need.
**Why:** The Mem0 Platform API treats both fields as opaque strings; routing is a convention at the dispatcher layer. Avoids infra divergence.
**Example:** See §3.2 Option B.

### 7.4 Pattern: Project Slug for State Isolation

**What:** Round table state files live under `~/.hermes/agents/.runtime/{project_slug}/`, where `project_slug = {repo_basename}:{git_toplevel_sha8}`.
**When:** Any cross-project-shared agent/skill that needs per-project runtime state.
**Why:** Disambiguates same-name repos on different machines. Mirrors GSD's `.planning/` per-project convention but at the runtime layer.
**Example:** See §5.1.

---

## 8. Anti-Patterns to Avoid

### 8.1 Anti-Pattern: Agent YAML as Prompt Dump

**What:** Copying the SKILL.md body verbatim into `persona`.
**Why bad:** SKILL body is a user-message prompt (imperative-second-person: "You are X. Do Y."). Persona is a system-prompt fragment (first-person: "I am X. I do Y."). Mixing registers confuses the model and loses the persona-as-identity framing that makes agents feel like colleagues rather than templates.
**Instead:** Rewrite persona in first-person, 5-15 lines, citing the most load-bearing refs by name. Defer detail to the refs themselves.

### 8.2 Anti-Pattern: Auto-Re-Transform on Drift

**What:** When curator detects `skill_sha256` drift, automatically regenerate the agent YAML from the new SKILL.md.
**Why bad:** Persona is hand-tuned. Auto-regeneration overwrites operator adjustments (e.g. "cite Volvo S1-1 case in persona" — a real v9.0 lesson encoded in cinematographer persona). Operators lose ownership.
**Instead:** Drift triggers an **advisory** in the curator report. Operator decides whether to re-transform.

### 8.3 Anti-Pattern: Round Table as Pipeline Step

**What:** Treating `round_table_open` as a synchronous pipeline step that blocks until `closed`.
**Why bad:** Round tables involve multiple LLM forks (one per panelist per round); blocking the calling thread for 3 rounds × 4 panelists × 30s = 6 minutes is unacceptable for interactive MCP clients.
**Instead:** `round_table_open` returns immediately with `round_table_id`; CC polls via `round_table_poll` (or subscribes via events). State persists in `.runtime/{slug}/round_tables/{id}.json`.

### 8.4 Anti-Pattern: Per-Agent mem0 Backend Instance

**What:** Spinning up a separate mem0 client per agent (15 connections for 15 movie-experts).
**Why bad:** Mem0 Platform API is rate-limited per API key, not per `agent_id`. 15 connections = 15x rate-limit pressure for zero benefit (filter routing is server-side).
**Instead:** One mem0 backend instance, `agent_id` filter per call (Option B, §3.2).

### 8.5 Anti-Pattern: Cross-Layer Import of `run_agent` in Agent Modules

**What:** `agent/agent_registry.py` or `agent/agent_dispatcher.py` importing `run_agent.AIAgent` at module top.
**Why bad:** Breaks the `_ra()` lazy indirection pattern (`agent/conversation_loop.py:111`) that prevents circular imports. Hermes has this invariant load-bearing for test mocking and runtime isolation.
**Instead:** Lazy import inside function bodies: `def dispatch_agent(...): from run_agent import AIAgent; ...`. Same pattern as `agent/curator.py:_run_llm_review` (line 2330).

---

## 9. Scalability Considerations

| Concern | At 15 agents (v11.0 PoC) | At 50 agents (v12+) | At 200 agents (hypothetical) |
|---------|--------------------------|---------------------|------------------------------|
| Discovery time | <100ms (15 YAML parses) | <300ms | <1.2s — consider caching parsed YAML in memory |
| mem0 filter recall latency | Negligible (filter is server-side) | Negligible | May need client-side namespace sharding |
| Curator `_memory_evolution_phase` duration | ~30s/agent × 15 = ~7min | ~30s × 50 = ~25min | Background; acceptable but consider parallelizing per-agent LLM forks |
| MCP `agents_list` payload | ~2KB JSON | ~7KB | ~30KB — add server-side pagination |
| Round table state file size | <10KB per round table | Same | Same (state file size is bounded by max_rounds × panel_size, not total agent count) |
| `evolution_log` chain depth | <10 entries after 1 year | <50 entries | Consider rolling window (keep last 100 entries, archive older) |

**Conclusion:** Architecture scales cleanly to v12+ (50 agents). For 200+ agents, the only concerning dimension is `agents_list` payload — solvable with pagination when needed.

---

## 10. Open Questions (for `01-AGENT-REGISTRY-SCHEMA.md` and `02-ROUND-TABLE-PROTOCOL.md` to resolve)

1. **Persona versioning** — when persona is rewritten (manual edit by operator), should the prior version be archived in `evolution_log` as a snapshot, or only the diff summary? (Leaning: diff summary only; full snapshot is operator's git responsibility if they keep `~/.hermes/agents/` under git.)
2. **Round table turn_order strategy** — round-robin (simple) vs fitness-weighted (higher-fitness agents speak first, framing the discussion) vs seniority (longest-`evolution_log` agents speak last as responders)? (Leaning: round-robin default, pluggable via `round_table_open` arg.)
3. **mem0 `agent_id` collision** — if operator has prior mem0 memories under `agent_id=hermes` (the v7.0 default), should the transition to per-agent scope migrate those memories? (Leaning: no — leave existing memories under default `agent_id`; new invocations start fresh under `agent_id=screenplay` etc. Operator can manually `mem0_conclude` to bridge.)
4. **`fitness_score` cold start** — agents start with `fitness_score: null`. How does the orchestrator treat null in turn_order decisions? (Leaning: null = neutral 0.5 for ordering, displayed as "untested" in UI.)
5. **Agent removal** — what happens when an agent YAML is deleted from `~/.hermes/agents/`? Round table state files reference agent names; orphaned references need handling. (Leaning: round table state captures a snapshot of agent identity at open time; deleted agents still render in historical transcripts with a "deleted" badge.)
6. **Project slug stability across renames** — if the operator renames the repo directory, `project_slug` changes and active round tables orphan. (Leaning: accept the breakage; document as known limitation. Long-term fix: stable project ID file at `.hermes/project.id`.)

---

## 11. References

### In-repo (HIGH confidence)

- `agent/skill_utils.py` — `iter_skill_index_files`, `parse_frontmatter`, `skill_matches_platform`. Direct read; v10.0 generalizes the same patterns.
- `agent/curator.py:run_curator_review` (2467 lines) — v6.0 curator with `_feedback_scan_phase` extension. Direct read; v10.0 adds `_memory_evolution_phase` as a sibling.
- `plugins/memory/mem0/__init__.py` (375 lines) — v7.0 mem0 backend. Direct read; v10.0 documents the `_read_filters` extension surface.
- `agent/memory_provider.py` — `MemoryProvider` ABC. Direct read.
- `tools/registry.py` — tool self-registration via AST scan. Direct read; v10.0 uses parallel pattern for `agent_registry`.
- `mcp_serve.py` — 9-tool MCP server. Direct read; v10.0 designs 7 additional agent-facing tools.
- `.planning/PROJECT.md` — v10.0 milestone context, 7 locked decisions. Direct read.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/screenplay/SKILL.md` (339 lines) — transform source sample. Direct read.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` (331 lines) — transform source sample. Direct read.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/_shared/v86-pipeline-mapping.md` (185 lines) — 15-expert collaboration DAG. Direct read.

### In-repo prior milestones (HIGH confidence)

- `.planning/research/v2-pipeline-design/` — v2.0 PRFP methodology reference (per PROJECT.md Constraints).
- v6.0 Self-Evolution milestone (MEMORY.md note) — feedback-driven eval gate + curator extension pattern.
- v7.0 openclaw migration milestone (MEMORY.md note) — mem0 backend ship.

### External (not consulted; design-time only milestone)

None. v10.0 is design-only and built entirely from in-repo context.

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| YAML schema field set | **HIGH** | 18 fields derived from direct read of SKILL frontmatter shape + MemoryProvider ABC + v6.0 evolution pattern. Every field has a traceable source. |
| 15-expert transform mapping | **HIGH** | Each row in §2 verified against the actual SKILL.md frontmatter (screenplay + cinematographer read in full; other 13 verified via `_shared/v86-pipeline-mapping.md` cross-reference). |
| Per-agent memory implementation path | **HIGH** | Mem0 backend read in full (375 lines); extension points are minimal deltas on `_read_filters` / `_write_filters` / `handle_tool_call`. |
| Agent registry loading mechanism | **HIGH** | Pattern cloned from `agent/skill_utils.py` (read in full, 740 lines) and `tools/registry.py` AST-scan (verified via grep). |
| Round table state layer | **MEDIUM** | Schema derived from GSD `.planning/STATE.md` analogy + PROJECT.md Decision #7. Full turn-by-turn protocol deferred to `02-ROUND-TABLE-PROTOCOL.md`. |
| Cross-repo coordination | **HIGH** | 3-location split is explicit in PROJECT.md Constraints; transform procedure + drift detection derived from existing `skill_sha256` pattern in v6.0 curator. |

---

*End of ARCHITECTURE.md. Consumers: `01-AGENT-REGISTRY-SCHEMA.md` consumes §1 + §2 + §6.1; `02-ROUND-TABLE-PROTOCOL.md` consumes §4.2 + §5; `06-CROSS-REPO-IMPACT.md` consumes §6.*
