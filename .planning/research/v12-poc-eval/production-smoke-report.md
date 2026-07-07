# v12.0 Production Smoke Report — Hardening Delta vs v11.0

**Milestone:** v12.0 Production Hardening
**Authored:** 2026-07-08 (Phase 61 Task 3)
**Verifier:** Claude (gsd-executor for plan 61-01)
**SC#2 status:** `human_needed` — real-GLM smoke deferred to operator per §3 row 1

**Scope statement:** v12.0 production smoke with hardening in place (Phase 57 endpoint
routing + Phase 58 RPM/TPM throttle + Phase 59 aux pool isolation + Phase 60 live-eval
infrastructure). Target: <240s round table latency + zero `RateLimitError` vs v11.0's
measured 490s + 5x retry storm. Source: ROADMAP Phase 61 SC#2 + REQUIREMENTS.md
VALIDATE-01.

**Real-GLM attempt policy (per 61-CONTEXT.md D-2 "Claude's Discretion"):** The executor
checked pre-conditions: `GLM_API_KEY` is NOT set in the verifier environment, AND
`systemctl --user is-active hermes-gateway.service` returns `active` (gateway is
consuming GLM quota). Per the plan's default behavior, SC#2 is marked `human_needed`
from the start — no live attempt was made. The 586+ automated tests + Phase 57 Test 13
proxy signal together satisfy the autonomous close-out bar; the live measurement is
operator-action work.

---

## §1 — Automated Test Aggregation

| Phase | Test scope | Count | Wall-clock | Source |
|-------|-----------|-------|------------|--------|
| **Phase 57** | `tests/agent/test_auxiliary_endpoint_routing.py` (13) + 6 `v11-*/` dirs (87) + 9 cross-cutting test files (159) | 259 PASS | 87.29s | `57-VERIFICATION.md` Behavioral Spot-Checks row "Phase 57 test gate (SC#3)" |
| **Phase 58** | `tests/agent/test_glm_throttle.py` (9) + `tests/agent/test_round_table_budget.py` (28) | 37 PASS | 2.07s | `58-VERIFICATION.md` Behavioral Spot-Checks row "Phase 58 test suite GREEN" |
| **Phase 58 cross-phase** | Regression sweep across `tests/agent/test_auxiliary_endpoint_routing.py` + `test_round_table_state.py` + `test_round_table_executor.py` + `test_auxiliary_client.py` | 264 PASS | 11.94s | `58-VERIFICATION.md` Behavioral Spot-Checks row "Cross-phase regression (Phase 52/57)" |
| **Phase 59** | `tests/agent/test_auxiliary_client_aux_pool.py` (6 incl. new freshest-pick integration) + `tests/agent/test_credential_pool_tpm_tracking.py` (9) | 15 PASS | 63.78s | `59-VERIFICATION.md` Behavioral Spot-Checks row "Regression: aux pool + TPM tracking test files green" (after gap closure re-verification) |
| **Phase 60** | `tests/scripts/test_seed_mem0_backend.py` (12) + `tests/scripts/test_run_latency_benchmark_backend_flag.py` (7) + `tests/v11-fitness-battery/test_baseline_mode_dispatch.py` (11) | 30 PASS | 1.45s | `60-VERIFICATION.md` Behavioral Spot-Checks row "Test gate green" |
| **TOTAL** | **all v12.0 + dependent agent tests** | **586+ PASS** | **~166s aggregate** | aggregate |

**Observations:**

- Phase 57 test gate is the largest single sweep (259 tests in 87.29s) — it
  incorporates the full v11.0 vertical-slice regression to prove that endpoint routing
  does not break any of the 9 agent YAMLs, the round table state machine, the MCP
  integration, or any of the 6 `v11-*/` test directories.
- Phase 58 includes the cross-phase regression sweep (264 tests) confirming that
  THROTTLE-01/02 wire-in does not break Phase 52 (round table state machine), Phase 57
  (endpoint routing), or the auxiliary client.
- Phase 59 was initially `gaps_found` (`select_freshest_tpm` orphaned) — the 15-test
  count reflects post-fix re-verification including the new integration test
  `test_aux_pool_picks_freshest_entry`.
- Phase 60 is the smallest test count (30) because most of the work is infrastructure
  wiring (adapter + seeder + flag + dispatch) — the actual production run is deferred
  to operator-action §3 rows 2+3.

---

## §2 — Production Smoke Targets (SC#2 result)

| # | Target | v11.0 baseline | v12.0 target | Status | Reference |
|---|--------|----------------|--------------|--------|-----------|
| **1** | Total wall-clock latency for screenplay Step 3 round table (9 panelists + 1 synthesis, real GLM, single-run) | 490s (5x retry storm on synthesis due to z.ai 30s cap) | <240s (50% reduction from Phase 57 routing + Phase 58 throttle + Phase 59 aux pool) | `human_needed` | §3 row 1 (deferred — requires `GLM_API_KEY` + paused gateway) |
| **2** | Zero `RateLimitError` exceptions during the 10-call round table | 5x retry storm (openai-SDK fallback chain exhausted) | 0 (Phase 58 throttle absorbs RPM pacing; Phase 59 aux pool isolates from gateway bursts) | `human_needed` | §3 row 1 (same run as Target 1) |

**Both targets are `human_needed` from the start** — per CONTEXT.md D-2, the executor
checked pre-conditions and found: (a) `GLM_API_KEY` not set in verifier environment,
(b) `hermes-gateway.service` is `active` and consuming quota. The default behavior per
the plan is to mark `human_needed` rather than attempt a quota-consuming run.

The 586+ automated tests + Phase 57 Test 13 proxy signal (routed path succeeds in 1
dispatch; unrouted raises after fallback chain exhausts — eliminating the ~250s
retry-storm component of the 490s wall-clock at the deterministic boundary) together
satisfy the autonomous close-out bar. The live 490s → <240s measurement is
operator-action work that requires real GLM budget.

---

## §3 — Operator-Action Runbook (3 handoffs)

Same 3 handoffs as `v12.0-MILESTONE-AUDIT.md §3`, but in smoke-report 7-field format
(per v11.0 `smoke-test-report.md §3` precedent: Status / Command / Pre-conditions /
Expected / Why human / Timestamp / Result).

### Row 1 — Phase 57 SC#2 / ENDPOINT-01 — Real-GLM v11.0 SC#2 round-table smoke (with v12.0 hardening)

| Field | Value |
|-------|-------|
| **Status** | `human_needed` — deferred to operator |
| **Command** | `python scripts/run_screenplay_step3_roundtable.py --smoke` (full form: `python scripts/run_screenplay_step3_roundtable.py --storykernel tests/fixtures/storykernel-sample.json --output build/screenplay-step3-output.json --smoke`). Requires `GLM_API_KEY` + 4-key rotation + aux pool configured in `~/.hermes/.env`. Recommend `systemctl --user stop hermes-gateway.service` before the run to free GLM quota; restart with `systemctl --user start hermes-gateway.service` after. |
| **Pre-conditions** | (a) Main repo venv at `/data/workspace/hermes-agent/.venv/bin/python`; (b) working directory `/data/workspace/hermes-agent`; (c) 9 agent YAMLs at `~/.hermes/agents/*.agent.yaml`; (d) `cli-config.yaml` has the `auxiliary.*` blocks configured per `cli-config.yaml.example` (Phase 57 endpoint_routing + Phase 58 rpm/cost_estimate + Phase 59 `GLM_AUX_API_KEY_1..4`); (e) MEMORY.md `feedback-glm-overload-reduce-concurrency.md` honored (global_concurrency==1); (f) MEMORY.md `hermes-gateway-systemd.md` — pause gateway during run. |
| **Expected** | Exit 0; total wall-clock latency <240s (vs v11.0's measured 490s — 50% reduction). Synthesis call routes directly to `open.bigmodel.cn/api/anthropic` (no z.ai 30s cap, no 5x openai-SDK retry storm). Zero `RateLimitError` exceptions. `build/screenplay-step3-output.json` exists with all 6 HOOK-09 fields populated (logline, scene_breakdown with per-scene emotion_curve, hooks with ≥1 type ∈ [cold_open, curiosity, shock, cliffhanger, paywall], payoffs, cliffhangers, top-level emotion_curve with arousal ∈ [0,1] + valence ∈ [-1,1]). State file `~/.hermes/agents/.runtime/screenplay-step3-poc/round_tables/{round_id}.json` has `status: "completed"` + `turns` array length 9 + top-level `tokensConsumed` + `costUsdEstimate` receipt fields (Phase 58 THROTTLE-02 deliverable). |
| **Why human** | Live `GLM_API_KEY` + 4-key rotation budget + paused gateway required. The verifier sandbox lacks the openai SDK + real-GLM rate-limit budget. Phase 57 Test 13 verifies the deterministic proxy signal (routing eliminates the retry storm at the mocked boundary); the end-to-end production latency measurement is operator-action work that ROADMAP Phase 57 SC#2 + PLAN `<success_criteria>` both explicitly defer to Phase 61 VALIDATE. The 586+ automated tests (§1) prove wiring; operator smoke proves production-grade latency + cost. |
| **Timestamp** | (operator fills in when run) |
| **Result** | (operator fills in — `pass` / `fail: <reason>` / `partial: <reason>`) |

### Row 2 — Phase 60 EVAL-01 — Live mem0 latency p95 benchmark

| Field | Value |
|-------|-------|
| **Status** | `human_needed` — deferred to operator (Plan 60-01 Task 3 is `checkpoint:human-verify gate=blocking`) |
| **Command** | `python scripts/seed_mem0_backend.py --agent-id screenplay --count 500` then `python scripts/run_latency_benchmark.py --backend mem0 --record-count 500 --runs 100 --out /tmp/v12-bench-live.json`. Requires `MEM0_API_KEY` in `~/.hermes/.env`. |
| **Pre-conditions** | (a) Main repo venv; (b) working directory `/data/workspace/hermes-agent`; (c) `MEM0_API_KEY` set in `~/.hermes/.env` (operator secret — Platform API token from mem0.ai); (d) `cli-config.yaml` mem0 provider block configured. |
| **Expected** | `latency-baseline.md §2.2` 500-record row filled with empirical p50/p95/p99 + Date + Operator (replaces `TBD` placeholders). If `slo_verdict == "fail"` (p95 ≥ 500ms), author `.planning/research/v12-poc-eval/物理分区-triggers.md` with 5 sections per Phase 48 §3 (physical partition trigger conditions). Fixture regression preserved (sub-ms). |
| **Why human** | Requires `MEM0_API_KEY` (operator secret). Fixture-only benchmark (in-memory list scan) is structurally sub-ms; authoritative SLO verdict requires live mem0 Platform API. Plan 60-01 Task 3 is explicitly `checkpoint:human-verify gate=blocking` — cannot run live mem0 Platform API calls from CI or verifier sandbox. |
| **Timestamp** | (operator fills in when run) |
| **Result** | (operator fills in — `pass: p95=X.Xms` / `fail: p95=Xms, 物理分区-triggers.md authored` / `deferred: <reason>`) |

### Row 3 — Phase 60 EVAL-02 — Real-mode fitness battery baseline

| Field | Value |
|-------|-------|
| **Status** | `human_needed` — deferred to operator (Plan 60-02 Task 3 is `checkpoint:human-verify gate=blocking`) |
| **Command** | `python scripts/compute_fitness_baseline.py --battery tests/v11-fitness-battery/scenarios --out /tmp/v12-fitness-baseline.json`. Requires `GLM_AUX_API_KEY_1..4` (or `GLM_API_KEY` fallback) in `~/.hermes/.env`. Recommend `systemctl --user stop hermes-gateway.service` during run to free GLM RPM quota; restart after. |
| **Pre-conditions** | (a) Main repo venv; (b) working directory `/data/workspace/hermes-agent`; (c) `GLM_AUX_API_KEY_1..4` set in `~/.hermes/.env` (4 keys for aux pool TPM spreading); (d) `cli-config.yaml` has `auxiliary.*` provider blocks + `auxiliary.tpm_warning_threshold: 0.1`; (e) MEMORY.md `feedback-glm-overload-reduce-concurrency.md` — global_concurrency==1; (f) MEMORY.md `hermes-gateway-systemd.md` — pause gateway during run. |
| **Expected** | 2 new entries appended to `~/.hermes/eval/fitness_trend.jsonl` with `mode: "persona_aligned"` + `mode: "generic_llm"`, `battery_version: "v1-screenplay-baseline-real"` (no shadow stub markers). Author `.planning/research/v12-poc-eval/fitness-battery-baseline.md` (NEW doc) with 7 sections (criterion / persona-aligned results / generic-LLM results / discrimination analysis / token cost / v12.0 implications verdict / references). Verdict recorded in §6: PASS if `delta ≥ 0.3 AND persona mean ≥ 0.7`; tech_debt if persona mean < 0.7 but delta ≥ 0.3; design_concern if delta < 0.3. Expected runtime: ~10-25 min wall-clock, ~400K tokens, ~0.20 CNY at glm-5.2 pricing. |
| **Why human** | Requires `GLM_AUX_API_KEY_1..4` (operator secret) + 10-25min wall-clock + ~0.20 CNY spend. Plan 60-02 Task 3 is explicitly `checkpoint:human-verify gate=blocking` — cannot run live GLM API calls from CI or verifier sandbox. Per MEMORY.md `feedback-glm-overload-reduce-concurrency.md`: global_concurrency==1; recommend pausing hermes-gateway during the run per MEMORY.md `hermes-gateway-systemd.md`. |
| **Timestamp** | (operator fills in when run) |
| **Result** | (operator fills in — `pass: persona=X.XX, generic=Y.YY, delta=D.DD` / `partial: <reason>` / `deferred: <reason>`) |

**Pre-conditions for all 3 (shared):** main repo venv at
`/data/workspace/hermes-agent/.venv/bin/python`; working directory
`/data/workspace/hermes-agent`; 9 agent YAMLs at `~/.hermes/agents/*.agent.yaml`;
`cli-config.yaml` has the `auxiliary.*` provider blocks per
`cli-config.yaml.example`; MEMORY.md `feedback-glm-overload-reduce-concurrency.md`
honored; MEMORY.md `hermes-gateway-systemd.md` honored for any GLM-consuming run.

---

## §4 — v11.0 vs v12.0 Hardening Delta

Before/after table showing what v12.0 changed at each layer of the round table
vertical slice. Each row corresponds to a hardening gap closed (cross-reference to
`v12.0-MILESTONE-AUDIT.md §4`).

| Layer | v11.0 baseline | v12.0 hardening | Phase / Req closed |
|-------|----------------|-----------------|---------------------|
| **Endpoint routing** | Hardcoded z.ai coding plan for all auxiliary calls; synthesis hits 30s cap on long prompts → openai-SDK 5x retry storm → ~250s wasted per round table | Prompt-length-aware routing: <4096 tokens (estimated) → `z.ai/api/coding/paas/v4` (lower cost); ≥4096 tokens → `open.bigmodel.cn/api/anthropic` (anthropic-compat, no 30s cap). Threshold configurable via `auxiliary.endpoint_routing.token_threshold`. | Phase 57 / ENDPOINT-01 |
| **RPM pacing** | Hardcoded `asyncio.sleep(2.5)` "Strategy A" in driver script; ineffective under real GLM rate-limit; bypasses aux_client layer; brittle to config changes | `TokenBucket` per task (`agent/glm_throttle.py`) with configurable RPM (default 30/task, well under single-key ceiling); `acquire_slot(task)` blocks until slot available; wired into `auxiliary_client.call_llm` BEFORE routing decision. Zero executable `asyncio.sleep` in driver (AST-walked). | Phase 58 / THROTTLE-01 |
| **TPM budget** | Unbounded (no per-round-table cost ceiling); synthesis overrun could exhaust daily quota silently | `round_table_open(token_budget=100_000)` (default covers 9 panelists × 5K + synthesis 10K + slack); `record_token_usage` atomic; `budget_warning` event at <2× expected; `budget_exceeded` event + abort at <1× expected; `submit_round_table_result` receipt with `tokensConsumed` + `costUsdEstimate` (GLM-5.2 pricing). | Phase 58 / THROTTLE-02 |
| **Credential pool** | Shared main pool for agent + gateway + auxiliary; gateway burst could exhaust keys for round table mid-synthesis; no per-key TPM awareness | Isolated aux pool: `load_named_pool("auxiliary")` + `GLM_AUX_API_KEY_1..4` env vars (fallback to `GLM_API_KEY`); per-key TPM sliding 60s window (`TpmWindow` + `record_usage` + `pool_tpm_status`); `select_freshest_tpm` wire-in picks key with most remaining TPM BEFORE each call; `tpm_warning` emission when all keys <10%. | Phase 59 / POOL-01 + POOL-02 |
| **Live eval infrastructure** | Fixture-only mem0 benchmark (in-memory list scan, sub-ms); fitness battery shadow-mode only (mocked judge returns 0.0 fallback); no live-backend path | `_BackendAdapter` singleton in `plugins/memory/mem0/__init__.py` (keyword-only `search`/`add`/`is_available`); idempotent `scripts/seed_mem0_backend.py` with `--dry-run`; `run_latency_benchmark.py --backend mem0` flag (mutually-exclusive with `--fixture`); `baseline_mode` kwarg on `fitness_battery._dispatch_agent` (`None` / `persona_aligned` / `generic_llm`); dual-mode orchestrator `scripts/compute_fitness_baseline.py`. | Phase 60 / EVAL-01 + EVAL-02 (infrastructure; live runs operator-action §3) |

**Expected operator-visible delta after §3 row 1 (SC#2 smoke):**

- Total round table latency: 490s → <240s (the ~250s retry-storm component is
  eliminated by endpoint routing; aux pool isolation eliminates the gateway-contention
  tail; throttle eliminates burst-rate 429s).
- `RateLimitError` count: 5x → 0 (Phase 58 throttle paces every call; Phase 59 aux
  pool avoids the shared-pool contention).
- Receipt: NEW `tokensConsumed` + `costUsdEstimate` fields in
  `~/.hermes/agents/.runtime/screenplay-step3-poc/round_tables/{round_id}.json` (per
  Phase 58 THROTTLE-02 deliverable).

---

## §5 — Verdict Triage

| Operator-action result | Impact on v12.0 verdict |
|------------------------|--------------------------|
| **All 3 PASS** | `passed` — v12.0 fully validated end-to-end. SC#2 smoke shows <240s latency + 0 RateLimitError; mem0 p95 < 500ms; fitness battery delta ≥ 0.3 + persona mean ≥ 0.7. Operator can `git tag v12.0` with full confidence. |
| **2/3 PASS, 1 documented partial** | `passed` with note. Operator-action items are runtime validations, not design gates — partial completion still satisfies VALIDATE-01 deliverable spec which explicitly allows documenting handoffs per v11.0 Phase 56 precedent. Tag v12.0 with note in tag message. |
| **Any FAILS fundamentally** (e.g. SC#2 round table cannot complete on real GLM; mem0 p95 > 1s with no 物理分区 path) | Re-classify as `tech_debt` or `gaps_found`; document remediation plan; v12.0 tag deferred until resolved. (Note: mem0 p95 between 500ms and 1s triggers `物理分区-triggers.md` documentation per Phase 48 §3 but does NOT block the verdict — that's the documented v13+ migration path. Fitness delta < 0.3 triggers design_concern documentation but the infrastructure remains valid.) |

**Default verdict (current state — all 3 handoffs pending):** `passed` per
`scripts/run_milestone_audit.py --milestone v12.0` output. The 586+ automated tests
satisfy the autonomous close-out bar; the 3 operator-action items are runtime
validations, NOT design gates.

---

## §6 — References

### Phase VERIFICATIONs (4 — evidence source)

- `.planning/phases/57-endpoint-routing/57-VERIFICATION.md`
- `.planning/phases/58-rpm-throttling/58-VERIFICATION.md`
- `.planning/phases/59-aux-pool-isolation/59-VERIFICATION.md`
- `.planning/phases/60-live-eval/60-VERIFICATION.md`

### Milestone audit (sibling doc)

- `.planning/milestones/v12.0-MILESTONE-AUDIT.md` (verdict = `passed`; 8/8 reqs walked
  in §2; 3 operator-action runbook entries in §3 — same content as this report's §3
  but in audit-doc table format vs smoke-report 7-field format)

### v11.0 smoke-test-report (precedent)

- `.planning/research/v11-poc-eval/smoke-test-report.md` (v11.0 close-out — same
  operator-action handoff convention; 5 handoffs vs v12.0's 3)

### v12.0 Operator-action scripts (5 — referenced by §3 runbook)

- `scripts/run_screenplay_step3_roundtable.py` (Phase 57 SC#2 / ENDPOINT-01 — hardened driver)
- `scripts/seed_mem0_backend.py` (Phase 60 EVAL-01 — NEW idempotent seeder)
- `scripts/run_latency_benchmark.py` (Phase 60 EVAL-01 — extended with `--backend mem0`)
- `scripts/compute_fitness_baseline.py` (Phase 60 EVAL-02 — NEW dual-mode orchestrator)
- `scripts/run_milestone_audit.py` (Phase 61 VALIDATE-01 — audit script, milestone-aware)

### Process Artifacts

- `.planning/REQUIREMENTS.md` (8 reqs — traceability table updated in Task 3 Part B)
- `.planning/ROADMAP.md` (Phase 57-61 critical path + SC#2 target)
- `.planning/phases/61-validate/61-CONTEXT.md` (verdict strategy + real-GLM discretion D-2)
- `./CLAUDE.md` (Python conventions, MEMORY.md constraints honored)

---

*v12.0 production smoke report authored 2026-07-08. SC#2 status: `human_needed` (3
operator-action handoffs in §3). Verifier default verdict: `passed` per
`scripts/run_milestone_audit.py --milestone v12.0` (8/8 reqs, 586+ automated tests
green). Operator next: run §3 handoffs in any order, then `git tag v12.0`.*

**Short-form copy-paste commands for operator:**

```bash
# Row 1 — SC#2 smoke (recommend: stop gateway first)
python scripts/run_screenplay_step3_roundtable.py --smoke

# Row 2 — EVAL-01 mem0 benchmark
python scripts/seed_mem0_backend.py --agent-id screenplay --count 500
python scripts/run_latency_benchmark.py --backend mem0 --record-count 500 --runs 100 --out /tmp/v12-bench-live.json

# Row 3 — EVAL-02 fitness battery (recommend: stop gateway first)
python scripts/compute_fitness_baseline.py --battery tests/v11-fitness-battery/scenarios --out /tmp/v12-fitness-baseline.json
```
