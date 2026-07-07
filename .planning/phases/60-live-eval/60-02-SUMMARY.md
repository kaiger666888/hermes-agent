---
phase: 60-live-eval
plan: 02
subsystem: testing
tags: [fitness-battery, real-mode, discrimination, glm, aux-pool, baseline]

requires:
  - phase: 54-eval-fitness
    provides: agent/fitness_battery.py run_battery + 8 frozen scenario YAMLs
  - phase: 59-aux-pool-isolation
    provides: agent/auxiliary_client.call_llm with Phase 59 auxiliary pool (GLM_AUX_API_KEY_1..4)
  - phase: 53-creative
    provides: $HERMES_HOME/agents/screenplay.agent.yaml (persona source for persona_aligned mode)
provides:
  - agent/fitness_battery.py baseline_mode kwarg on _dispatch_agent + run_battery (3 dispatch paths: None | persona_aligned | generic_llm)
  - scripts/compute_fitness_baseline.py dual-mode orchestrator (runs both batteries sequentially + computes delta + writes JSON)
  - tests/v11-fitness-battery/test_baseline_mode_dispatch.py 11 hermetic dispatch tests
affects: [60-live-eval, 61-validate, v13-migration]

tech-stack:
  added: []  # no new dependencies — uses existing auxiliary_client + yaml
  patterns:
    - "baseline_mode kwarg pattern — orthogonal selector to existing shadow flag; persona_aligned vs generic_llm differ only in whether a system message is prepended"
    - "_extract_user_message canonical-user-payload helper — handles all 3 scenario input shapes (prompt / storykernel / question+mem_a/mem_b) with ordered key fallback"
    - "_load_persona_system_prompt hermetic loader — reads $HERMES_HOME/agents/<name>.agent.yaml via hermes_constants.get_hermes_home() (no Path.home())"
    - "graceful degradation on real-mode dispatch failure — returns JSON stub with real_mode_error marker so the battery can score (likely low) without crashing"

key-files:
  created:
    - scripts/compute_fitness_baseline.py
    - tests/v11-fitness-battery/test_baseline_mode_dispatch.py
  modified:
    - agent/fitness_battery.py
  deferred:
    - .planning/research/v12-poc-eval/fitness-battery-baseline.md  # Task 3 — operator GLM run

key-decisions:
  - "baseline_mode is orthogonal to the Phase 54 shadow flag — when baseline_mode is set, shadow is ignored. Avoids a confusing 4-state matrix."
  - "persona_aligned mode loads the persona from $HERMES_HOME/agents/screenplay.agent.yaml at dispatch time (not import time) so curator edits between runs are picked up without a restart. Falls back to a warning + persona-less dispatch on YAML load failure (graceful degradation, Rule 2)."
  - "generic_llm mode uses the SAME user message text as persona_aligned (apples-to-apples). Only the system message differs. This is the load-bearing control variable for the discrimination delta."
  - "BATTERY_VERSION bumped to 'v1-screenplay-baseline-real' to distinguish real-mode from shadow runs in fitness_trend.jsonl. The shadow run producing mean_score=0.0187 in the v11.0 smoke-test-report now has a different battery_version from future real-mode runs."
  - "compute_fitness_baseline.py runs sequentially (persona_aligned THEN generic_llm), NOT in parallel. Both modes share the Phase 59 auxiliary pool; sequential execution lets the RPM bucket settle between modes (per MEMORY.md global_concurrency==1)."
  - "Added 'mode' field to fitness_trend.jsonl entries — downstream analysis can filter persona_aligned vs generic_llm rows. Field is additive; existing trend rows without it are unaffected."

patterns-established:
  - "Real-mode dispatch helper pattern: _dispatch_real_mode encapsulates the new path so the original _dispatch_agent shadow/arbitration logic is preserved verbatim — Phase 54 contract intact."
  - "Recording-stub test pattern: _recording_stub(record) factory in test_baseline_mode_dispatch.py captures messages kwarg for assertion without monkey-patching internals."

metrics:
  duration: ~45min
  completed: 2026-07-08
  tasks_total: 3
  tasks_done: 2
  tasks_deferred: 1
  files_created: 2
  files_modified: 1
  tests_added: 11
  commits:
    - a988bd4e8  # feat(60-02): add baseline_mode real-mode dispatch to fitness_battery
    - 0361b6170  # feat(60-02): add compute_fitness_baseline.py dual-mode orchestrator
---

# Phase 60 Plan 02: Fitness Battery Real-Mode Baseline Summary

Built the dual-mode (persona-aligned + generic-LLM) real-mode dispatch infrastructure for the EVAL-02 fitness battery. Task 3 (live GLM run + authoring of `fitness-battery-baseline.md`) is DEFERRED — requires operator GLM aux pool keys + ~400K tokens + 10-25min wall-clock.

## What Shipped

### Task 1 — baseline_mode dispatch in agent/fitness_battery.py

`_dispatch_agent` + `run_battery` now accept a `baseline_mode: str | None = None` kwarg. Three mutually-exclusive dispatch paths:

| `baseline_mode` | Behavior | System message | Use case |
|---|---|---|---|
| `None` (default) | Phase 54 behavior preserved verbatim: shadow stub / conflict arbitration / screenplay stub | n/a | CI shadow runs + Phase 54 backward compat |
| `"persona_aligned"` | Load `screenplay.agent.yaml` persona + dispatch via `auxiliary_client.call_llm` | yes (persona YAML) | Real-mode battery — measures persona-equipped agent |
| `"generic_llm"` | Same user payload, NO system prompt | no | Discrimination baseline — generic GLM-5.2 |

Both real-mode paths route through `auxiliary_client.call_llm(task="fitness_battery_agent", provider="glm")` per MEMORY.md GLM-only rule, hitting the Phase 59 auxiliary pool (`GLM_AUX_API_KEY_1..4` or `GLM_API_KEY` fallback). Dispatch failure returns a JSON stub with a `real_mode_error` marker so the battery continues scoring (graceful degradation — never crashes).

Two new helpers:
- `_extract_user_message(scenario)` — ordered-key fallback (`prompt` → `user_message` → `user` → `question`) handles all 8 scenario shapes.
- `_load_persona_system_prompt(agent_name)` — reads `$HERMES_HOME/agents/<name>.agent.yaml` via `hermes_constants.get_hermes_home()` (CLAUDE.md anti-pattern compliant); returns `None` on any failure.

`BATTERY_VERSION` bumped `"v1-screenplay-baseline"` → `"v1-screenplay-baseline-real"` so real-mode trend entries are distinguishable from shadow stubs in `fitness_trend.jsonl`.

11 new tests in `tests/v11-fitness-battery/test_baseline_mode_dispatch.py` — all hermetic via `monkeypatch.setattr(fitness_battery, "_call_llm", stub)`:
- persona_aligned prepends system message + records `provider="glm"`
- generic_llm omits system message + returns raw content string (not stub dict)
- dispatch failure returns `real_mode_error` JSON stub
- `run_battery` threads `baseline_mode` to every dispatch call (spied)
- `run_battery` default `baseline_mode=None` (Phase 54 compat)
- `_extract_user_message` covers prompt / storykernel / question shapes
- `BATTERY_VERSION` is `"v1-screenplay-baseline-real"`

Full v11.0 fitness-battery suite: 20 tests pass (11 new + 9 existing — zero regression).

### Task 2 — scripts/compute_fitness_baseline.py

Single CLI that orchestrates both real-mode runs + computes discrimination delta + writes structured JSON summary.

```
python scripts/compute_fitness_baseline.py \
    --battery tests/v11-fitness-battery/scenarios \
    --out /tmp/fitness-baseline-phase60.json
```

Flags: `--battery`, `--persona-sha256` (auto-computed from `screenplay.agent.yaml` if omitted), `--out` (required), `--model-id` (locked `glm-5.2`), `--provider` (locked `zai`), `--skip-generic` (debugging), `--trend-path`.

Behavior:
1. Auto-compute persona SHA-256 from `$HERMES_HOME/agents/screenplay.agent.yaml` (overridable).
2. Run persona_aligned battery; append trend entry with `"mode": "persona_aligned"`.
3. Run generic_llm battery (unless `--skip-generic`); append trend entry with `"mode": "generic_llm"`.
4. Compute `delta = persona_mean - generic_mean`; verdict = `meaningful` if `delta >= 0.3` else `not_meaningful` (CONTEXT.md decision #4).
5. Stdout prints per-scenario breakdown + delta + verdict + token-cost estimate.
6. Write JSON summary to `--out` with both full run_battery dicts + delta + verdict + timestamp + token cost.

Sequential execution — both modes share the Phase 59 aux pool; running them back-to-back lets the RPM throttle (30/task) reset between modes (per MEMORY.md global_concurrency==1).

`scripts/run_fitness_battery.py` UNCHANGED — remains the single-mode CLI for shadow CI runs + operator spot-checks.

## Deviations from Plan

None — plan executed exactly as written for Tasks 1+2.

Minor scope clarifications (documented, not deviations):
- The plan's `--help` verification command counts 4 flag substrings; the actual output matches 7 lines because some flags appear in default-value descriptions too. Count ≥ 4 satisfies the done criterion.
- The plan's `<verify>` for Task 2 invokes the script end-to-end. Without GLM aux pool keys, a full end-to-end run is deferred to Task 3. Syntax check + `--help` + Task 1 unit tests cover the wiring verification for Task 2 in CI.

## Deferred: Task 3 — Live GLM Run + Baseline Doc Authoring

**Status:** DEFERRED per orchestrator instruction (autonomous tasks 1+2 only).

**What Task 3 requires (operator-run, blocking checkpoint:human-verify):**
1. `GLM_AUX_API_KEY_1..4` (or `GLM_API_KEY` fallback) set in `~/.hermes/.env`.
2. `~/.hermes/agents/screenplay.agent.yaml` exists (verified present at SUMMARY time).
3. Recommend pausing `hermes-gateway.service` during the run to free GLM RPM quota.
4. ~10-25min wall-clock, ~400K tokens, ~0.20 CNY.
5. Author `.planning/research/v12-poc-eval/fitness-battery-baseline.md` (7 sections, mirroring `latency-baseline.md` style).

**Resume signal:** Operator invokes Task 3 explicitly with GLM keys provisioned. Expected command:

```bash
python scripts/compute_fitness_baseline.py \
    --battery tests/v11-fitness-battery/scenarios \
    --out /tmp/fitness-baseline-phase60.json 2>&1 | tee /tmp/fitness-baseline-phase60.log
```

**Expected post-Task-3 state:**
- `~/.hermes/eval/fitness_trend.jsonl` has 2 new entries (one per mode).
- `.planning/research/v12-poc-eval/fitness-battery-baseline.md` exists with 7 sections + verdict (PASS if delta ≥ 0.3 AND persona mean ≥ 0.7).
- Single doc commit landed: `docs(60-02): ship EVAL-02 real-mode fitness baseline (persona=X.XX, generic=Y.YY, delta=D.DD, verdict=...)`.

## Known Stubs

None — no stub patterns in the shipped code paths. Real-mode dispatch genuinely invokes `auxiliary_client.call_llm`; the deferred-Task-3 status reflects missing live-GLM operator time, not a code stub.

## Threat Flags

None — no new security-relevant surface beyond what the plan's `<threat_model>` already documents. The two new dispatch paths (`persona_aligned` + `generic_llm`) reuse the existing `auxiliary_client.call_llm` (Phase 59 aux pool, TLS-protected, no new endpoints). Threat register entries T-60-02-PI / -DO / -CO / -IZ / -RE all remain adequately mitigated.

## Verification

| Check | Status |
|---|---|
| `python3 -m pytest tests/v11-fitness-battery/test_baseline_mode_dispatch.py -x` | PASS (11 tests) |
| `python3 -m pytest tests/v11-fitness-battery/ -q` (no regression) | PASS (20 tests: 11 new + 9 existing) |
| `python3 -c "import ast; ast.parse(open('scripts/compute_fitness_baseline.py').read())"` | PASS |
| `python3 scripts/compute_fitness_baseline.py --help` lists 4 documented flags | PASS (7 lines, ≥ 4) |
| `ruff check` on all 3 modified/created files | PASS |
| `git log --oneline` shows both task commits | PASS (a988bd4e8, 0361b6170) |

## Self-Check: PASSED

Files verified to exist:
- FOUND: /data/workspace/hermes-agent/agent/fitness_battery.py
- FOUND: /data/workspace/hermes-agent/scripts/compute_fitness_baseline.py
- FOUND: /data/workspace/hermes-agent/tests/v11-fitness-battery/test_baseline_mode_dispatch.py
- FOUND: /data/workspace/hermes-agent/.planning/phases/60-live-eval/60-02-SUMMARY.md

Commits verified:
- FOUND: a988bd4e8 (feat(60-02): add baseline_mode real-mode dispatch to fitness_battery)
- FOUND: 0361b6170 (feat(60-02): add compute_fitness_baseline.py dual-mode orchestrator)
