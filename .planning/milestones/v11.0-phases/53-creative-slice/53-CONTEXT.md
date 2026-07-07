# Phase 53: CREATIVE-SLICE - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (smart discuss with grey-area acceptance)

<domain>
## Phase Boundary

Deliver the creative vertical slice end-to-end per `05-POC-PLAN.md §3.2`:

1. **MIGR-01 — 9 Sample Agent YAML Transform:** Transform 9 sample movie-expert SKILL.md → agent YAMLs at `~/.hermes/agents/*.agent.yaml`, sufficient for screenplay Step 3 round table. Each YAML validates against Phase 45 `agents-schema.yaml` (18 camelCase fields, lineage block populated).
2. **CREATIVE-01 — 9-Agent Screenplay Step 3 Round Table End-to-End:** `round_table_open` → 9 sequential `get_agent_opinion` calls → 1 `submit_round_table_result` lifecycle. Output JSON validates against screenplay Step 3 schema (HOOK-09 emotion_curve marker contract). Latency < 30s on real GLM API call (no mocks).
3. **CREATIVE-02 — Memory Conflict Arbitration Runtime:** Implement 5-mechanism arbitration per `02-ROUND-TABLE-PROTOCOL.md §3`: memory annotation enrichment, comparator LLM pass, scope precedence (`session > project > global`), confidence-weighted voting with tie-deferral, conflict log for curator review.

**Hard dependencies (consumed from Phase 52):** agent registry loader, 7 MCP tools, state machine with crash recovery, serial execution lock.

**Downstream:** Phase 54 (EVAL-HARNESS-1) consumes the running vertical slice for fitness battery + latency benchmark + bias canary hooks.

</domain>

<decisions>
## Implementation Decisions

### Resolved by Kai (2026-07-07, post-discuss grey-area acceptance)

1. **9-Agent Subset — Map to v3.0+ current names.** Use: `screenplay`, `cinematographer`, `hook_retention`, `theory_critic`, `editor`, `character_designer` (was `performer` per v3.0 absorption), `continuity_auditor` (was `continuity`), `audio_pipeline` (was `composer`), `style_genome` (replaces `scene_builder` visual-DNA role). All 9 are currently active in `/data/workspace/kais-hermes-skills/skills/movie-experts/`. This preserves the round-table density 9 from ARCHITECTURE §2 screenplay row while using living expert IDs — avoids FOUND-08 risk of resurrecting deprecated names. Phase 49 §2.4 transform rules apply to each.

2. **Conflict Arbitration — Full 5-mechanism per `02-ROUND-TABLE-PROTOCOL.md §3`.** Implement all 5 sub-mechanisms (P7 mitigation 1-5): memory annotation enrichment + comparator LLM pass + scope precedence + confidence-weighted voting + conflict log. Comparator LLM uses Hermes runtime (GLM via existing provider chain); token cost ~2K/call is acceptable per §3.2 estimate. Tie cases (Δconfidence < 0.05) → `deferred-to-operator`. No simplified rule-only fallback — CREATIVE-02 SC#3 requires "comparator LLM pass" verbatim.

3. **9 Agent YAMLs live at `~/.hermes/agents/*.agent.yaml` (production path).** Per INFRA-01 + `agents-schema.yaml` header. Real operators can drop YAMLs here and they're discoverable immediately via `agents_list` MCP tool. Test fixtures remain separate under `tests/agent/fixtures/agents/`. Hermetic test isolation via HERMES_HOME redirection (already in conftest.py `_hermetic_environment`).

### Claude's Discretion

1. **SKILL.md source files** at `/data/workspace/kais-hermes-skills/skills/movie-experts/{name}/SKILL.md` (read-only per Phase 48 + Phase 49 lineage invariants L1-L6). Compute SHA-256 with `hashlib.sha256(content.encode("utf-8")).hexdigest()` (UTF-8 / LF-normalized).
2. **Transform script:** `scripts/transform_skill_to_agent.py` — reads SKILL.md, applies Phase 49 §2 transform rules per expert, writes agent YAML at `~/.hermes/agents/{name}.agent.yaml`. Each transform produces an audit log entry mapping SKILL frontmatter → agent YAML fields.
3. **Screenplay Step 3 schema:** Define as `tests/fixtures/screenplay-step3-schema.json` — JSON Schema for the HOOK-09 emotion_curve marker contract. Output of `run_screenplay_step3_roundtable.py` must validate.
4. **Comparator LLM prompt template** from `02-ROUND-TABLE-PROTOCOL.md §3.2` — copy verbatim into `agent/memory_arbitration.py::COMPARATOR_PROMPT_TEMPLATE` constant.
5. **Conflict log path:** `.runtime/{project_slug}/round_tables/{round_id}/conflicts.jsonl` per `06-CROSS-REPO-IMPACT.md §5.1`. Append-only via `atomic_json_write`-style helper (or plain append with fsync, since JSONL is line-delimited).
6. **GLM API call for SC#2 smoke test:** Use existing `agent/glm_concurrency_guard.py` for 4-key rotation + 3-strike early-abort. Smoke test gracefully skips if `GLM_API_KEY` unavailable (mark as `human_needed` in VERIFICATION.md).
7. **9-agent round table driver script:** `scripts/run_screenplay_step3_roundtable.py` — orchestrates the 9 sequential `get_agent_opinion` MCP calls + 1 `submit_round_table_result`. Reads synthetic StoryKernel JSON input from `tests/fixtures/storykernel-sample.json`.

### Established patterns to follow (from Phase 52)

- `from __future__ import annotations` + `encoding="utf-8"` + snake_case + `get_hermes_home()`
- `utils.atomic_json_write` for state/conflict-log writes
- Pydantic or dataclasses for typed results
- `jsonschema.Draft202012Validator` for schema validation
- `@pytest.mark.asyncio` explicit on async tests
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` citation in serial-violation errors (Phase 52 contract)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 52)

- `agent/registry_loader.py::load_agent_registry` — validates YAMLs at `~/.hermes/agents/`. MIGR-01 outputs land here automatically.
- `agent/round_table_state.py::{open_round_table, append_turn, submit_round_table_result, abort_round_table, read_and_recover_state}` — full state machine with crash recovery.
- `agent/round_table_executor.py` — per-roundId asyncio.Lock + 429 + MEMORY.md citation. CREATIVE-01 round table inherits serial enforcement automatically.
- `agent/memory_arbitration.py` — Phase 52 stub. CREATIVE-02 fills in real arbitration logic here (comparator LLM + scope precedence + voting).
- `mcp_serve.py` — 7 v11.0 MCP tools registered. CREATIVE-01 driver script invokes them via the MCP client surface.
- `agent/glm_concurrency_guard.py` — 4-key rotation + 3-strike early-abort for GLM API calls.
- `agent/curator.py` — existing background-review module; Phase 54 EVAL-HARNESS-1 extends `_memory_evolution_phase` (CREATIVE-02's conflict log feeds this).

### Source Material (read-only)

- `/data/workspace/kais-hermes-skills/skills/movie-experts/{screenplay,cinematographer,hook_retention,theory_critic,editor,character_designer,continuity_auditor,audio_pipeline,style_genome}/SKILL.md` — 9 source SKILLs for MIGR-01 transform.
- `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md §2` — 75-cell transform table (5 fields × 15 experts; subset of 9 applies).
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md §3` — 5-mechanism conflict arbitration contract.
- `.planning/research/v10-orchestrator-design/agents-schema.yaml` — 18-field agent YAML schema.
- `.planning/research/v10-orchestrator-design/memory-record-schema.yaml` — memory record schema (consumed by Phase 52 stubs, Phase 53 fills in routing).

### Integration Points

- `~/.hermes/agents/*.agent.yaml` — 9 transformed YAMLs land here.
- `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json` — state files.
- `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}/conflicts.jsonl` — conflict log (NEW for CREATIVE-02).
- `scripts/run_screenplay_step3_roundtable.py` — driver script (NEW).
- `scripts/transform_skill_to_agent.py` — transform utility (NEW).

</code_context>

<specifics>
## Specific Ideas

The 3 SCs (per ROADMAP §Phase 53) are the authoritative acceptance contract:

- **SC#1:** 9 agent YAMLs at `~/.hermes/agents/*.agent.yaml` validate against `agents-schema.yaml`; transform log documents field mappings per Phase 49 §2 75-cell rules; lineage block has `derived_from_skill_id` + `skill_sha256`.
- **SC#2:** `scripts/run_screenplay_step3_roundtable.py` produces JSON artifact validating against screenplay Step 3 schema (HOOK-09 emotion_curve marker contract); latency < 30s on real GLM API call (no mocks); exercises full `round_table_open` → 9 sequential `get_agent_opinion` → 1 `submit_round_table_result` lifecycle.
- **SC#3:** 2-conflict test scenario produces correct arbitration per Phase 46 §3: comparator LLM detects conflict, `session > project > global` scope precedence honored, confidence-weighted voting picks winner, conflict entry appended to `conflicts.jsonl`.

**HOOK-09 invariant (per `05-POC-PLAN.md §3.2` edge case):** `screenplay.agent.yaml` `lineage.transform_notes` MUST contain `HOOK-09 emotion_curve marker arrays remain contract-load-bearing`. If absent, downstream Step 6.5 storyboard + Step 7 visual_executor cannot consume screenplay output. PoC's first "did the transform work?" smoke test verifies this string is present.

</specifics>

<deferred>
## Deferred Ideas

- **15-expert full transform** — only 9 sample agents in v11.0; remaining 6 experts deferred to v12.0 per REQUIREMENTS.md "Out of Scope".
- **Per-agent memory full benchmark** — only latency p95 measured (Phase 54 EVAL-02); memory throughput + concurrent-agent scaling deferred to v12.0.
- **Round table parallel optimization** — v11.0 strictly serial per INFRA-04 hard constraint; parallel round tables are explicitly forbidden by `02-ROUND-TABLE-PROTOCOL.md §4.1`.
- **subpanel / panelist_role / asset_locks** — `02-ROUND-TABLE-PROTOCOL.md §6` deferred all to v11.1+.
- **Operator-action GLM key configuration** — if GLM_API_KEY unavailable during SC#2 smoke test, mark as `human_needed` in VERIFICATION.md per autonomous workflow (operator runs smoke test manually after key config).

</deferred>
