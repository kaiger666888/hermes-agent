# v11.0 Vertical Slice Smoke Test Report

**Milestone:** v11.0 — Hermes-Native Expert Agents PoC Implementation
**Authored:** 2026-07-07 (Phase 56 Task 3)
**Audience:** Operator (Kai) + future v12.0 milestone author
**Source:** `VALIDATE-01` deliverable per `.planning/REQUIREMENTS.md` line 176 + `.planning/phases/56-validate/56-01-PLAN.md` Task 3

---

## §1 — Purpose + Scope

### What this report is

End-of-milestone smoke test aggregation for v11.0 PoC. Two layers:

1. **Automated baseline results** (§2) — test counts + spot-check outcomes already produced by Phase 52-55 automated verification. Populated now, NOT operator-action.
2. **Operator-action runtime validations** (§3) — 5 handoffs requiring real GLM_API_KEY / MEM0_API_KEY + live mem0 backend. Each marked `Status: human_needed`; operator fills `Timestamp when run` + `Result` after execution.

### Scope

- **In scope:** automated evidence aggregation + operator runbook for the 5 `human_verification` items from Phase 53/54/55 VERIFICATION.md frontmatter.
- **Out of scope:** live production traffic (v12+ per REQUIREMENTS.md `Out of Scope`); 15-expert full transform (v12.0); per-agent memory benchmark full (v12.0); 物理分区 migration (v12+ gated on EVAL-02 live p95).

### Operator-action convention (re-stated)

Per autonomous workflow convention (carried from v9.0 close-out), an item
marked `human_needed` is NOT a blocking design gap. It is a runtime
validation of code that is fully implemented and automated-test-verified.
The operator runs them with real credentials to capture production-grade
numbers (latency, accuracy). They count as `passed-with-operator-deferral`
per `scripts/run_milestone_audit.py` verdict logic.

---

## §2 — Automated Baseline Results (populated NOW)

These are the test counts and CLI spot-check outcomes already produced by
Phase 52-55 automated verification. No operator action required — these
are committed evidence.

### §2.1 Test-suite aggregate

| Dimension | Source phase | Test count | Result | Evidence pointer |
|-----------|-------------|-----------|--------|------------------|
| Phase 52 INFRA foundation | 52 | **71 passed** in 2.13s | ✅ PASS | `.planning/phases/52-infra-foundation/52-VERIFICATION.md` Behavioral Spot-Checks row 1 |
| Phase 53 CREATIVE (mocked GLM) | 53 | **53 passed** in 2.66s | ✅ PASS | `.planning/phases/53-creative-slice/53-VERIFICATION.md` Behavioral Spot-Checks row 12 |
| Phase 54 EVAL-HARNESS-1 | 54 | **50 passed** in 2.13s | ✅ PASS | `.planning/phases/54-eval-harness-1/54-VERIFICATION.md` Behavioral Spot-Checks row 6 |
| Phase 55 EVAL-HARNESS-2 | 55 | **165 passed** in 7.83s | ✅ PASS | `.planning/phases/55-eval-harness-2/55-VERIFICATION.md` Behavioral Spot-Checks row 1 |
| Migration dry-run probe | 55 | exit 0, 30 records mapped, 0 dropped | ✅ PASS | `.planning/phases/55-eval-harness-2/55-VERIFICATION.md` Probe Execution row 1 |
| **Total automated** | **52-55** | **339+ tests green** | ✅ PASS | aggregate |

### §2.2 Foundational artifacts (existence + wiring verified)

| Artifact | Expected | Status | Evidence |
|----------|----------|--------|----------|
| HOOK-09 schema fixture | `tests/fixtures/screenplay-step3-schema.json` with 6 required top-level fields | ✅ PASS | `53-VERIFICATION.md` Required Artifacts row 9 + `test_screenplay_step3_schema_fixture_loads` confirms 6 fields (logline, scene_breakdown, hooks, payoffs, cliffhangers, emotion_curve) |
| 9 agent YAMLs at `~/.hermes/agents/*.agent.yaml` | All validate against Phase 45 `agents-schema.yaml` (18 fields, lineage populated) | ✅ PASS | `53-VERIFICATION.md` SC#1 row + `test_all_9_yamls_pass_schema` (all 9 carry `derived_from_skill_id` + `skill_sha256`) |
| Round table lifecycle atomic | `test_lifecycle_round_trip` exercises `round_table_open` → `get_agent_opinion` → `submit_round_table_result`; final state file `status == "completed"` | ✅ PASS | `52-VERIFICATION.md` SC#2 row + Key Link Verification row 4 |
| Serial-execution 429 rejection | Concurrent `get_agent_opinion` for same `roundId` rejected; 429 message cites `feedback-glm-overload-reduce-concurrency.md` substring | ✅ PASS | `52-VERIFICATION.md` SC#4 row + `test_429_message_cites_memory_md` |
| Memory arbitration 5-mechanism | comparator LLM + scope precedence `session > project > global` + confidence voting + tie-break (`_TIE_THRESHOLD=0.05`) + conflicts.jsonl writer | ✅ PASS | `53-VERIFICATION.md` SC#3 row + `TestTwoConflictScenario` 2-conflict test |
| Curator dry-run-first default | `agent/curator.py:1942 dry_run: bool = True` + line 1986 None-check + AST-walk non-bypassable test | ✅ PASS | `55-VERIFICATION.md` SC#3 row + `tests/v11-dry-run-first/test_ast_walk_non_bypass.py` (4 AST-walk + 5 behavior + 2 sanity) |
| Migration dry-run zero-writes | Pre/post md5sum of `$HERMES_HOME/skills/.audit/log.jsonl` identical after dry-run | ✅ PASS | `55-VERIFICATION.md` Behavioral Spot-Checks row 4 (md5 identical) |
| Bias canary false-positive guard | `good_record_multi_operator.json` correctly NOT flagged | ✅ PASS | `54-VERIFICATION.md` Behavioral Spot-Checks row 4 (JSON inspection) |

### §2.3 Code coverage (production modules shipped)

| Module | Lines | Tests | Source phase |
|--------|-------|-------|--------------|
| `agent/registry_loader.py` | 325 | 15 (test_registry_loader.py) | 52 / INFRA-01 |
| `agent/round_table_state.py` | 617 | 17 (test_round_table_state.py) | 52 / INFRA-03 |
| `agent/round_table_executor.py` | 181 | 6 (test_round_table_executor.py) | 52 / INFRA-04 |
| `agent/memory_arbitration.py` | 360+ | 10 (test_memory_arbitration.py + test_conflict_log_writer.py) | 52 stub → 53 / CREATIVE-02 full |
| `mcp_serve.py` (7 new closures) | 887-1455 (~570 lines additive) | 21 (test_mcp_serve_round_table.py) | 52 / INFRA-02 |
| `agent/memory_compaction.py` | 702 | 13 (tests/v11-compaction/) | 55 / EVAL-04 |
| `agent/curator_bias_canary.py` | 504 | 6 fixtures (tests/v11-bias-canary/) | 54 / EVAL-03 |
| `agent/fitness_battery.py` | 423 | 8 scenarios (tests/v11-fitness-battery/) | 54 / EVAL-01 |
| `agent/memory_scoped_retrieval.py` | exports LatencySample + timed_retrieval + compute_percentiles | 3 fixtures (tests/v11-latency-bench/) | 54 / EVAL-02 |
| `scripts/migrate_v6_feedback_to_memory_schema.py` | 952 | 52 (tests/v11-schema-migration/) | 55 / EVAL-07 |
| `agent/curator.py` (modified) | +2 lines (line 1942 default flip + 1986 None-check) | 11 (tests/v11-dry-run-first/) | 55 / EVAL-06 |

**Total v11.0 production code shipped:** ~4900 lines Python + 9 agent YAMLs.

### §2.4 Schema extensions (additive)

| Schema | Extension | Phase | Status |
|--------|-----------|-------|--------|
| `agents-schema.yaml` | §2.6.1 `memory.thresholds` block (3 properties: `max_records=500`, `confidence_threshold_for_promotion=0.7`, `evidence_chain_min_for_acceptance=3`, `additionalProperties: false`) | 55 / EVAL-05 | ✅ PASS — additive, memory_scope §2.6 + lineage §2.7 untouched |

---

## §3 — Operator-Action Smoke Tests (5 handoffs, human_needed)

The runbook. Each handoff has 7 fields: Status, Command, Pre-conditions, Expected, Why human, Timestamp when run, Result. Operator fills the last two.

### §3.1 — Real-GLM Screenplay Step 3 Round Table Smoke (Phase 53 SC#2 / CREATIVE-01)

- **Status:** `human_needed`
- **Command:** `time python scripts/run_screenplay_step3_roundtable.py --storykernel tests/fixtures/storykernel-sample.json --output build/screenplay-step3-output.json --smoke`
- **Pre-conditions:**
  1. `~/.hermes/.env` has `GLM_API_KEY` (or `ZAI_API_KEY`) for 4-key rotation
  2. `cli-config.yaml` auxiliary block has `round_table_opinion.provider: glm` + `memory_comparator.provider: glm` (template at `cli-config.yaml.example` lines 487-501)
  3. 9 agent YAMLs at `~/.hermes/agents/*.agent.yaml` (already present — verified in §2.2)
  4. Use main repo `.venv/bin/python` (NOT system python3 — needs `openai` SDK)
  5. Run from `/data/workspace/hermes-agent` (the parent repo, NOT a worktree)
- **Expected:**
  - Exit code 0
  - Total wall-clock < 30 seconds (10 LLM calls × ~2s each + overhead)
  - `build/screenplay-step3-output.json` exists with all 6 HOOK-09 fields:
    - `logline` (string)
    - `scene_breakdown` (array, each entry has `emotion_curve` sub-array)
    - `hooks` (array, at least 1 entry with `type` ∈ `[cold_open, curiosity, shock, cliffhanger, paywall]`)
    - `payoffs` (array)
    - `cliffhangers` (array)
    - top-level `emotion_curve` (array, at least 1 entry with `arousal` ∈ `[0,1]` + `valence` ∈ `[-1,1]`)
  - State file at `~/.hermes/agents/.runtime/screenplay-step3-poc/round_tables/{round_id}.json` has `status: "completed"` + `turns` array length 9
- **Why human:** 10 sequential real-GLM API calls require operator's live GLM_API_KEY + 4-key rotation budget + main repo venv (executor sandbox lacks `openai` package + rate-limit budget). Mocked-GLM tests (12/12 PASS per `53-VERIFICATION.md` Behavioral Spot-Checks row 12) prove the lifecycle wiring but cannot prove real-GLM latency.
- **Timestamp when run:** _(operator fills in)_
- **Result:** _(operator fills in: PASS / FAIL / partial with details)_

### §3.2 — Live GLM Fitness Battery Baseline (Phase 54 EVAL-01)

- **Status:** `human_needed`
- **Command:** `python scripts/run_fitness_battery.py --battery tests/v11-fitness-battery/scenarios --persona-sha256 <real-persona-sha256>`
- **Pre-conditions:**
  1. `GLM_API_KEY` set (or `ZAI_API_KEY` for GLM provider)
  2. 8 scenario YAMLs in place (verified in §2.2)
  3. `screenplay.agent.yaml` `persona_sha256` referenced — operator can read from `~/.hermes/agents/screenplay.agent.yaml` `lineage.skill_sha256` field
- **Expected:**
  - Per-scenario scores in [0,1]
  - Persona-aligned screenplay agent scores 0.7+ vs generic LLM 0.4-0.5 (discrimination criterion per `.planning/research/v11-poc-eval/fitness-battery-spec.md §5`)
  - `fitness_trend.jsonl` entry appended at `~/.hermes/eval/fitness_trend.jsonl` as PoC baseline
- **Why human:** Live GLM dispatch via `auxiliary_client.call_llm` requires valid credentials. CI uses mocked judge returning 0.0 fallback per T-54-03 mitigation. Phase 56 VALIDATE will run this.
- **Timestamp when run:** _(operator fills in)_
- **Result:** _(operator fills in)_

### §3.3 — Live mem0 Latency p95 Benchmark (Phase 54 EVAL-02)

- **Status:** `human_needed`
- **Command:** `python scripts/run_latency_benchmark.py --fixture 500 --out /tmp/v11-latency-live.json`
- **Pre-conditions:**
  1. `MEM0_API_KEY` set
  2. Live mem0 backend reachable
  3. 500-record store seeded (per `tests/v11-latency-bench/fixtures/seed_500_records.py` pattern, but against real mem0)
- **Expected:**
  - p95 < 500ms SLO met on 100 sequential `memory_retrieve_scoped` retrievals (excluding LLM call)
  - Baseline numbers populate `.planning/research/v11-poc-eval/latency-baseline.md §2.2` live-backend row
  - If p95 > 500ms, document 物理分区 trigger conditions per Phase 48 §3 + `06-CROSS-REPO-IMPACT.md §2`
- **Why human:** Fixture-only benchmark is structurally sub-ms (in-memory list scan); authoritative SLO verdict requires live mem0 backend per Phase 54 SUMMARY §Next Phase Readiness.
- **Timestamp when run:** _(operator fills in)_
- **Result:** _(operator fills in)_

### §3.4 — Live GLM Bias Canary Smoke (Phase 54 EVAL-03)

- **Status:** `human_needed`
- **Command:** `python scripts/run_bias_canary.py --fixtures tests/v11-bias-canary/fixtures/ --out /tmp/v11-canary-live.json --smoke`
- **Pre-conditions:**
  1. `GLM_API_KEY` set
  2. `auxiliary.bias_canary_claim_check.provider: glm` in `cli-config.yaml` (template at `cli-config.yaml.example`)
- **Expected:**
  - LLM claim-support pass flags `bad_record_unsupported_claim.json` fixture (the 4th non-deterministic check)
  - Acceptance verdict remains pass (4-5 of 5 bad caught)
  - Audit chain entry appended
- **Why human:** Real GLM dispatch requires credentials. CI uses mocked LLM (returns `supported=True`); `--smoke` operator-action documented in CLI --help + `cli-config.yaml.example`.
- **Timestamp when run:** _(operator fills in)_
- **Result:** _(operator fills in)_

### §3.5 — Real-GLM Compaction Summary (Phase 55 EVAL-04)

- **Status:** `human_needed`
- **Command:** Use the `scripts/run_with_real_glm.py` pattern OR invoke `compact_memory(agent_id="screenplay", dry_run=False, backend=<real mem0 backend>)` directly via a one-shot Python session against a 600+ record real memory store.
- **Pre-conditions:**
  1. `GLM_API_KEY` set
  2. Live mem0 backend with 600+ records for `screenplay` agent
  3. `auxiliary.memory_compaction.provider: glm` + `task: memory_compaction` in `cli-config.yaml`
- **Expected:**
  - GLM call succeeds (not the deterministic fallback)
  - Single summary record in working-tier
  - All working-tier originals flipped to `status="superseded"`
  - All archival-tier originals flipped to `status="archived"`
  - `source_record_ids` chain populated with every original record_id
  - Audit log entry appended with real `eval_score` payload
  - 3-tier post-state satisfies core ≤10 / working ≤100 / archival ≤10000
- **Why human:** 13 tests in `tests/v11-compaction/` use `mock_claim_check_llm` (canned responder). Live GLM behavior depends on `GLM_API_KEY` availability and `auxiliary.memory_compaction` task routing in `cli-config.yaml`.
- **Timestamp when run:** _(operator fills in)_
- **Result:** _(operator fills in)_

---

## §4 — Verdict Triage Table (operator decision matrix)

After running the 5 §3 handoffs, the operator decides whether to tag v11.0 or defer.

| Operator-action result | Impact on verdict | Next step |
|------------------------|-------------------|-----------|
| All 5 PASS | `passed` — v11.0 fully validated end-to-end | `git tag v11.0` |
| 4/5 PASS, 1 documented partial (e.g. latency slightly above 500ms but within 2× SLO) | `passed` with note (operator-action items are runtime validations, not design gates — VALIDATE-01 deliverable spec explicitly allows documenting handoffs) | `git tag v11.0` + note partial in this report |
| 3/5 or fewer PASS, OR any FAILS fundamentally (e.g. round table cannot complete on real GLM) | Re-classify as `tech_debt` or `gaps_found`; document remediation plan | Defer v11.0 tag; consult `.planning/milestones/v11.0-MILESTONE-AUDIT.md §7 Tech Debt` for guidance; consider v11.1 hotfix milestone |

**Note:** per autonomous workflow convention, `passed` is achievable WITHOUT running any operator-action items — they are runtime validations of code already verified by 339+ automated tests. The default verdict from `scripts/run_milestone_audit.py` is `passed` regardless of operator-action status (because the operator-action layer is `human_needed` not `failed`).

---

## §5 — References

- `.planning/milestones/v11.0-MILESTONE-AUDIT.md §3` — canonical operator-action runbook (mirror of this §3)
- `.planning/phases/53-creative-slice/53-VERIFICATION.md` `human_verification` frontmatter — source of truth for §3.1 (P53 SC#2 handoff)
- `.planning/phases/54-eval-harness-1/54-VERIFICATION.md` `human_verification` frontmatter — source of truth for §3.2-§3.4 (P54 EVAL-01/02/03 handoffs)
- `.planning/phases/55-eval-harness-2/55-VERIFICATION.md` `human_verification` frontmatter — source of truth for §3.5 (P55 EVAL-04 handoff)
- `.planning/REQUIREMENTS.md` VALIDATE-01 deliverable spec
- `.planning/phases/56-validate/56-01-PLAN.md` Task 3 — authoring contract for this report
- `scripts/run_milestone_audit.py` — audit matrix producer; emits JSON with `operator_action_count` + `verdict_logic.recommended_verdict`

---

*v11.0 smoke test report authored 2026-07-07 (Phase 56 Task 3). Automated baselines (§2) are committed evidence. Operator-action sections (§3) await operator runs — fill `Timestamp when run` + `Result` fields per handoff.*
