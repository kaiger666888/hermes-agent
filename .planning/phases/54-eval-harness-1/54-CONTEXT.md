# Phase 54: EVAL-HARNESS-1 - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped per autonomous smart-discuss rule)

<domain>
## Phase Boundary

Build first wave of PoC acceptance criteria per `05-POC-PLAN.md §4.1-§4.3`:

1. **EVAL-01 — Fitness Battery Design (3d):** Battery of test scenarios scoring agent outputs on dimensions relevant to vertical slice (screenplay Step 3 quality, conflict resolution correctness). Each scenario has expected-output + scoring rubric. Battery persisted as data files at `.planning/research/v11-poc-eval/fitness-battery-spec.md` + `tests/v11-fitness-battery/` (5-10 scenarios).
2. **EVAL-02 — Latency SLO p95 < 500ms (2d):** Per-agent scoped mem0 retrieval p95 < 500ms. Instrument `memory_retrieve_scoped` MCP tool with timing. Test: 100 sequential retrievals on populated memory store. Document baseline + bottlenecks at `.planning/research/v11-poc-eval/latency-baseline.md`.
3. **EVAL-03 — Bias Canary (2d):** Curator `_memory_evolution_phase` hallucination detection. Bias canary runs curator in dry-run + flags suspicious memory edits (low evidence_chain, low confidence, unsupported claims). Test: inject 5 known-bad memory records, expect 4/5 caught. Extend `agent/curator.py` + new `agent/curator_bias_canary.py`.

**Hard dependencies (consumed from Phase 53):** vertical slice runtime (agent registry + 9-agent round table + memory arbitration), curator extension hook points.

**Downstream:** Phase 55 EVAL-HARNESS-2 builds compaction + threshold tuning + dry-run-first + schema migration on this foundation. Phase 56 VALIDATE runs the full eval battery + publishes reports.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation choices at Claude's discretion — pure infrastructure/test-fixtures phase. The v10.0 design suite + 05-POC-PLAN.md §4 lock the contracts; implementation-level choices follow codebase patterns.

**Authoritative design sources:**
- `05-POC-PLAN.md §4.1` (fitness battery) + §4.2 (latency SLO) + §4.3 (bias canary) + §6.1 (sequence: fitness FIRST → schema migration SECOND → bias canary THIRD — bias canary ships in this phase per PoC plan)
- `02-ROUND-TABLE-PROTOCOL.md §3` (conflict arbitration — fitness battery tests this)
- `agent/curator.py` existing `_memory_evolution_phase` contract (Phase 54 extends)
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (serial invariant — bias canary must not violate)

### Implementation-level open questions (Claude's discretion)

1. **Fitness battery scenario format:** YAML or JSON? Recommend YAML (human-editable, matches SKILL.md refs convention). Each scenario has: `id`, `description`, `input` (StoryKernel JSON or conflict pair), `expected_output`, `scoring_rubric` (criteria + weights).
2. **Latency benchmark fixture store:** 100 memory records seeded via `memory_submit_record` against mem0 backend, OR a fixture-only store? Recommend fixture-only (deterministic, no mem0 backend dependency in CI).
3. **Bias canary integration approach:** Extend `agent/curator.py::_memory_evolution_phase` directly, OR separate `agent/curator_bias_canary.py` that reads curator output? Recommend separate module + thin integration hook in curator (keeps single-responsibility).
4. **Bias canary LLM pass:** Use existing `auxiliary_client.call_llm` with `task="bias_canary"`, provider="glm". Register in `cli-config.yaml.example`.
5. **Test directory layout:** `tests/v11-fitness-battery/` + `tests/v11-latency-bench/` + `tests/v11-bias-canary/` (new top-level test dirs per REQUIREMENTS.md deliverables) OR `tests/agent/v11_*`? Recommend new top-level dirs per REQUIREMENTS.md spec (matches `.planning/research/v11-poc-eval/` doc location).
6. **Run scripts:** `scripts/run_fitness_battery.py`, `scripts/run_latency_benchmark.py`, `scripts/run_bias_canary.py` — one per acceptance criterion per REQUIREMENTS.md.

### Established patterns to follow

- `from __future__ import annotations` + `encoding="utf-8"` + snake_case + `get_hermes_home()`
- Pytest fixtures for filesystem isolation (HERMES_HOME redirection)
- `@pytest.mark.asyncio` explicit (strict mode)
- `agent/auxiliary_client.call_llm(task=..., provider="glm")` for any LLM dispatch
- `jsonschema.Draft202012Validator` for any output schema validation
- `utils.atomic_json_write` for any persisted benchmark results

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `agent/curator.py::run_curator_review` — existing background-review entry point. Phase 54 adds bias canary hook.
- `agent/curator_audit.py` — sha256-chained audit log (existing v6.0 ship). Bias canary can append to this.
- `agent/memory_arbitration.py::arbitrate_two_memories` (Phase 53) — fitness battery tests this for conflict resolution correctness.
- `agent/auxiliary_client.call_llm` — GLM dispatch with 4-key rotation.
- `agent/glm_concurrency_guard.py` — serial lock (bias canary must respect).
- `agent/registry_loader.py` + `agent/round_table_state.py` + `scripts/run_screenplay_step3_roundtable.py` (Phase 52 + 53 outputs) — fitness battery exercises these end-to-end.
- `plugins/memory/mem0/` — mem0 backend plugin (latency benchmark target).
- `tests/fixtures/memory-conflict-2conflict.json` (Phase 53) — fitness battery can reuse this fixture format.

### Integration Points

- `.planning/research/v11-poc-eval/` — NEW directory for spec docs + baseline reports
- `tests/v11-fitness-battery/` + `tests/v11-latency-bench/` + `tests/v11-bias-canary/` — NEW test directories
- `scripts/run_fitness_battery.py` + `scripts/run_latency_benchmark.py` + `scripts/run_bias_canary.py` — NEW run scripts
- `agent/curator_bias_canary.py` — NEW module (extends curator)
- `agent/memory_scoped_retrieval.py` — NEW module (timing instrumentation wrapper) OR inline in mcp_serve.py
- `cli-config.yaml.example` — add `auxiliary.bias_canary` entry with `provider: glm`

</code_context>

<specifics>
## Specific Ideas

The 3 SCs (per ROADMAP §Phase 54) are the authoritative acceptance contract:

- **SC#1 (EVAL-01):** `.planning/research/v11-poc-eval/fitness-battery-spec.md` exists + `tests/v11-fitness-battery/` has 5-10 scenario files + `scripts/run_fitness_battery.py` runs battery and produces scored report.
- **SC#2 (EVAL-02):** Timing instrumentation in `agent/memory_scoped_retrieval.py` (or inline) + `tests/v11-latency-bench/` benchmark script + results JSON + `.planning/research/v11-poc-eval/latency-baseline.md` (results + analysis).
- **SC#3 (EVAL-03):** `agent/curator_bias_canary.py` extends `agent/curator.py` + `tests/v11-bias-canary/` with 5 synthetic bad-record fixtures + `scripts/run_bias_canary.py` run script. Test: 4/5 known-bad records caught.

</specifics>

<deferred>
## Deferred Ideas

- **Compaction pass** — EVAL-04 deferred to Phase 55.
- **Threshold tuning** — EVAL-05 deferred to Phase 55.
- **Dry-run-first invariant** — EVAL-06 deferred to Phase 55.
- **Schema migration dry-run** — EVAL-07 deferred to Phase 55.
- **Live production traffic** — v12+ per REQUIREMENTS.md.
- **Multi-judge ensemble** — v12+ (single LLM judge in v11.0 PoC).
- **Statistical GO/NO-GO verdicts** — v12+ (require N≥20 prompts per scenario).

</deferred>
