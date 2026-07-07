# Phase 60: LIVE-EVAL - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (eval + benchmark phase)

<domain>
## Phase Boundary

Run the 2 deferred v11.0 EVAL handoffs against live backends. v11.0 shipped these as `human_needed` operator-action items; v12.0 executes them and populates the live-baseline rows.

1. **EVAL-01 — Production mem0 Backend Latency p95 Benchmark:** Wire production mem0 backend (requires `MEM0_API_KEY`); seed 500-record store for `screenplay` agent; run 100 sequential `memory_retrieve_scoped` calls; measure p50/p95/p99; populate `.planning/research/v11-poc-eval/latency-baseline.md §2.2` live-backend row.

2. **EVAL-02 — Fitness Battery Real-Mode Baseline:** Run all 8 scenarios in real-mode (no `--shadow`); compute `mean_score` per scenario + overall; populate `fitness_trend.jsonl` with real baseline entry; document discrimination baseline (persona-aligned 0.7+ vs generic-LLM 0.4-0.5) in `.planning/research/v12-poc-eval/fitness-battery-baseline.md` (NEW).

</domain>

<decisions>
## Implementation Decisions

### Locked

1. **mem0 backend configuration:** Operator must set `MEM0_API_KEY` in `~/.hermes/.env`. Without it, this phase's EVAL-01 SC#1 is marked `human_needed`.
2. **mem0 fixture seeding:** Use `tests/v11-latency-bench/fixtures/seed_500_records.py` pattern but write to real mem0 backend. Each record: `{agent_id=screenplay, scope=per_agent, content, confidence=0.5, evidence_chain=[...]}`.
3. **Fitness battery real-mode:** 8 scenarios × ~3 prompts each = ~24 LLM calls per agent × 9 agents = ~216 LLM calls. **Use Phase 59 auxiliary pool** (`GLM_AUX_API_KEY_1..4`) to avoid exhausting main pool. Default RPM throttle (30/task) keeps it under cap.
4. **Discrimination baseline:** Compare persona-aligned screenplay agent scores vs generic-LLM baseline (same prompts, no persona). Delta ≥ 0.3 indicates meaningful discrimination.
5. **Token cost:** Estimate ~50K tokens per scenario × 8 = ~400K tokens for fitness battery real-mode. ≈ 0.20 CNY at glm-5.2 pricing.
6. **If MEM0_API_KEY missing:** EVAL-01 deferred, mark in `latency-baseline.md §2.2` as `human_needed`. EVAL-02 can still run (GLM only).

### Claude's Discretion

- Seeding script: NEW `scripts/seed_mem0_backend.py` OR extend `seed_500_records.py` with `--backend mem0` flag. Recommend new script (clean separation).
- Baseline computation: `scripts/compute_fitness_baseline.py` OR extend `run_fitness_battery.py` with `--baseline-mode`. Recommend new script.
- Generic-LLM baseline: use the same `auxiliary_client.call_llm` with empty persona (no system prompt). Save scores separately.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `scripts/run_fitness_battery.py` (Phase 54) — already has `--shadow` mode; this phase runs WITHOUT `--shadow` to invoke real LLM judge + agent dispatch.
- `scripts/run_latency_benchmark.py` (Phase 54) — currently fixture-only. This phase adds live mem0 backend support.
- `tests/v11-latency-bench/fixtures/seed_500_records.py` (Phase 54) — seeding pattern reference.
- `agent/memory_arbitration.py::memory_retrieve_scoped` (Phase 52/53) — the actual MCP tool we benchmark.
- `plugins/memory/mem0/` — mem0 backend plugin (currently stub).
- `agent/fitness_battery.py` (Phase 54) — runner; this phase drives real-mode.

### Integration Points

- `scripts/seed_mem0_backend.py` (NEW)
- `scripts/run_latency_benchmark.py` modification (`--backend mem0` flag)
- `scripts/run_fitness_battery.py` modification (real-mode is default; remove `--shadow` from operator docs)
- `scripts/compute_fitness_baseline.py` (NEW)
- `.planning/research/v11-poc-eval/latency-baseline.md` (UPDATE §2.2 with live numbers)
- `.planning/research/v12-poc-eval/fitness-battery-baseline.md` (NEW)
- `.planning/research/v12-poc-eval/`(NEW dir)

</code_context>

<specifics>
## Specific Ideas

3 SCs per ROADMAP §Phase 60:
1. Production mem0 backend wired; 100-call benchmark produces p50/p95/p99 in `latency-baseline.md §2.2` live-backend row.
2. If p95 > 500ms, `.planning/research/v12-poc-eval/物理分区-triggers.md` documents migration decision per Phase 48 §3.
3. Fitness battery 8 scenarios real-mode; discrimination baseline (persona-aligned 0.7+ vs generic 0.4-0.5) documented in `.planning/research/v12-poc-eval/fitness-battery-baseline.md`.

</specifics>

<deferred>
## Deferred Ideas

- Long-running mem0 backend benchmark (1000+ records) — keep at 500 for v12.0 PoC.
- Multi-judge ensemble for fitness battery — single LLM judge in v12.0; ensemble is v13+.
- Statistical GO/NO-GO verdicts on fitness battery — requires N≥20 per scenario; v13+ scope.

</deferred>
