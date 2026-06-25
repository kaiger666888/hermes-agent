---
phase: 34-review-gate-framework
plan: 01
subsystem: review-gates
tags: [hil, gate, state-machine, lifecycle, stdlib, threading]
requires:
  - Phase 31 review_gates plugin scaffold (tools.py stubs, __init__.py, plugin.yaml)
provides:
  - plugins.review_gates.gate.Gate (mutable runtime instance)
  - plugins.review_gates.gate.GateConfig (frozen, hashable static config)
  - plugins.review_gates.gate.GateMode (3-mode enum: blocking/webhook/polling)
  - plugins.review_gates.gate.GateStatus (6-state enum)
  - plugins.review_gates.gate.GateError (transient)
  - plugins.review_gates.gate.GateMaxRetriesExceeded (terminal, CONSISTENCY_BLOCKED marker)
affects:
  - Plan 34-03 (runner_hooks.py imports Gate / GateMaxRetriesExceeded / GateStatus)
  - Plan 34-04 (tools.py handlers swap to call runner_hooks which calls Gate)
  - Phase 35 runner (catches GateMaxRetriesExceeded -> episode fail path)
tech-stack:
  added: []
  patterns:
    - pure-stdlib leaf module (D-34-01) — no httpx/jwt/yaml/plugins.* imports
    - frozen + mutable dataclass split (D-34-04) — GateConfig hashable, Gate mutable
    - threading.Event for blocking-mode wait (D-34-05) — sync only, no asyncio
    - mode-dispatched wait() (CF-01) — BLOCKING/WEBHOOK/POLLING
    - terminal exception carries literal marker (PIPE-GUARD-01 CONSISTENCY_BLOCKED:)
key-files:
  created:
    - plugins/review_gates/gate.py
    - plugins/review_gates/tests/test_gate.py
  modified: []
decisions:
  - D-34-01 honored — gate.py imports only stdlib (enum/logging/threading/time/dataclasses/datetime/pathlib/typing); AST-verified by test_gate_py_is_pure_stdlib_no_http_jwt_yaml_imports
  - D-34-05 honored — no ast.AsyncFunctionDef nodes in gate.py (AST-verified by test_gate_py_has_no_async_def); the single grep "async def" hit is in docstring prose (line 33), not code
  - CF-05 / PIPE-GUARD-01 — GateMaxRetriesExceeded message format is "CONSISTENCY_BLOCKED: gate '<id>' exhausted retries (<n> > <m>)"; raised from submit() AFTER setting status=FAILED so callers observing state see the terminal condition even if they catch
  - CF-04 — _outcome_record() emits the 8-key shape; payload_snapshot envelope (bus-level concern) is intentionally NOT included — runner_hooks._write_review_outcome wraps it (separation of concerns: state machine vs persistence)
metrics:
  duration: ~3min
  completed: 2026-06-25T15:30:00Z
  tasks: 2
  files_created: 2
  tests_added: 22
  loc_gate_py: 378
  loc_test_gate_py: 388
---

# Phase 34 Plan 01: Gate Lifecycle State Machine Summary

Pure-stdlib HIL review-gate state machine with 3 switchable modes (blocking/webhook/polling), `GateMaxRetriesExceeded` terminal exception preserving v4.0 PIPE-GUARD-01 CONSISTENCY_BLOCKED semantics, and CF-04 outcome-record shape — the core abstraction the Phase 35 runner will call via Plan 34-03's runner_hooks adapter.

## What Was Built

### `plugins/review_gates/gate.py` (378 LOC)

A pure-stdlib leaf module implementing the gate lifecycle state machine.

**Enums:**
- `GateMode` — BLOCKING / WEBHOOK / POLLING (CF-01 three switchable modes).
- `GateStatus` — PENDING / APPROVED / REJECTED / CONTESTED / TIMED_OUT / FAILED.

**Exceptions:**
- `GateError` — transient (invalid decision, polling-mode wait misuse).
- `GateMaxRetriesExceeded` — terminal; constructor `(gate_id, attempts, max_retries)`; message always prefixed `"CONSISTENCY_BLOCKED: "` so the runner / log greps can identify the episode-fail path (PIPE-GUARD-01 / CF-05).

**Dataclasses:**
- `@dataclass(frozen=True) GateConfig` — static gate definition (gate_id, phase, asset_bus_slots_to_lock, reviewer_role required; timeout_sec=3600, callback_url=None, max_retries=2, backoff_sec=300, default_mode=BLOCKING defaults per CF-02). Frozen for hashability + immutability (D-34-04).
- `@dataclass Gate` — mutable runtime instance. Fields: config / episode_id / mode (required) + attempt / status / review_id / submitted_at / resolved_at / decision / suggested_action / `_event` (threading.Event, repr=False).

**Methods:**
- `submit(payload, *, review_client=None) -> dict` — increments `attempt`; BEFORE any other mutation, checks `attempt > config.max_retries` → sets status=FAILED + raises `GateMaxRetriesExceeded` (CF-05). On success: stamps submitted_at, sets status=PENDING, clears the Event (so a fresh blocking wait actually blocks), returns submission record. `review_client` accepted but unused — D-34-01 keeps gate.py pure; runner_hooks owns the actual HTTP call.
- `wait(timeout_sec=None) -> dict` — mode-dispatched (CF-01):
  - BLOCKING → `self._event.wait(timeout=effective_timeout)`; on False sets status=TIMED_OUT; returns outcome record.
  - WEBHOOK → returns immediately `{"status": "awaiting_callback", "review_id": self.review_id}` (non-blocking — caller persists awaiting_review state and exits).
  - POLLING → raises `GateError("POLLING mode wait requires runner_hooks.poll_until_terminal(); use Gate.poll_step() in a loop instead.")`.
- `resolve(decision, suggested_action=None) -> dict` — validates decision ∈ {approve, reject, contest}; sets status (APPROVED/REJECTED/CONTESTED), decision, suggested_action, resolved_at; signals `_event.set()` to wake blocking waiters; returns outcome record. Does NOT touch the asset bus — separation of concerns (CF-04 write is runner_hooks' job).
- `_outcome_record() -> dict` — CF-04 shape: gate_id / episode_id / decision / suggested_action / reviewer_role / resolved_at / attempt / status. (payload_snapshot envelope is added by the bus adapter, not by the state machine.)

### `plugins/review_gates/tests/test_gate.py` (388 LOC, 22 tests)

TDD test suite across 9 classes + 2 module-purity assertions:

| Class / Group | Tests | Coverage |
|---|---|---|
| module purity | 2 | AST-verified: no httpx/jwt/yaml imports (D-34-01); no `async def` nodes (D-34-05) |
| `TestGateEnums` | 2 | GateMode 3 values exact; GateStatus 6 values exact |
| `TestGateConfig` | 2 | CF-02 defaults; frozen + hashable + immutable (FrozenInstanceError on setattr) |
| `TestGateConstruction` | 2 | mutable empty initial state; TypeError when config/episode_id/mode missing |
| `TestSubmit` | 3 | attempt increment + submitted_at + PENDING; submission record shape; max_retries -> GateMaxRetriesExceeded + FAILED + CONSISTENCY_BLOCKED marker + exception metadata |
| `TestWaitBlockingMode` | 3 | immediate return when pre-resolved; timeout -> TIMED_OUT (~1s actual wait verified); concurrent-thread resolver wakes waiter in <2s (vs 5s timeout) |
| `TestWaitWebhookMode` | 1 | non-blocking return <0.5s with awaiting_callback + review_id; status stays PENDING |
| `TestWaitPollingMode` | 1 | raises GateError mentioning poll_until_terminal / poll_step |
| `TestResolve` | 3 + 1 | parametrized approve/reject/contest status+decision+Event signal; invalid decision raises GateError; end-to-end cross-thread wake |
| `TestOutcomeRecord` | 1 | CF-04 8-key shape (reviewer_role propagated from config; attempt counter reflected) |

## Commits

| Hash | Type | Message |
|---|---|---|
| `78a08b5c0` | test | `test(34-01): add failing tests for Gate state machine` (RED gate — 22 tests fail on `ModuleNotFoundError: plugins.review_gates.gate`) |
| `6d6c29029` | feat | `feat(review_gates): port Gate state machine (Phase 34-01)` (GREEN gate — 22/22 pass) |

## Verification

All plan verification gates met:

| Gate | Required | Actual | Status |
|---|---|---|---|
| gate.py exists at plugins/review_gates/gate.py, ≥180 LOC | yes | 378 LOC | PASS |
| test_gate.py exists, ≥250 LOC, 12-15 tests | yes | 388 LOC, 22 tests | PASS (superset) |
| `pytest plugins/review_gates/tests/test_gate.py -v` all pass | yes | 22 passed in 1.40s | PASS |
| No `async def` (AST) in gate.py | yes | 0 AsyncFunctionDef nodes | PASS |
| No httpx/jwt/yaml imports in gate.py | yes | 0 (AST-verified) | PASS |
| `GateMaxRetriesExceeded` message starts with `CONSISTENCY_BLOCKED:` | yes | format `"CONSISTENCY_BLOCKED: gate '<id>' exhausted retries (<n> > <m>)"` | PASS |
| Both RED + GREEN commits in git log | yes | `78a08b5c0` + `6d6c29029` | PASS |
| Import smoke test | yes | `python3 -c "from plugins.review_gates.gate import Gate, GateConfig, GateMode, GateStatus, GateError, GateMaxRetriesExceeded; print('OK')"` exits 0 | PASS |

## Deviations from Plan

None. Plan executed exactly as written — PATTERNS.md skeleton followed, all CF-01 (3 modes) / CF-04 (outcome shape) / CF-05 (max_retries terminal) requirements covered, all D-34-01 (pure stdlib) / D-34-04 (frozen+mutable split) / D-34-05 (sync only) decisions honored.

**Note on the plan's grep-based async check:** The plan's verification step `grep -c "async def" plugins/review_gates/gate.py` returns 1 — but the single hit is the docstring prose on line 33 describing the constraint ("No ``async def`` anywhere in this module"). The authoritative check is the AST-based `test_gate_py_has_no_async_def` test which walks `ast.AsyncFunctionDef` nodes (not strings) and passes. No actual async code exists in gate.py. This is a known imprecision in the grep proxy, not a deviation in implementation.

## Known Stubs

None. gate.py is a complete, self-contained state machine. The HTTP-calling adapters (webhook HMAC verify, polling query loop, asset-bus write-back) are explicitly out of scope for Plan 34-01 — they live in Plan 34-03 (runner_hooks.py) per D-34-01.

## Threat Flags

None. gate.py is a pure in-process state machine with no network surface, no file system access, no auth boundary. The only externally-visible behavior is the `GateMaxRetriesExceeded` exception which is intentionally terminal and labeled with the `CONSISTENCY_BLOCKED:` marker for grep-based triage (this is a safety feature preserving PIPE-GUARD-01, not a threat surface).

## Self-Check: PASSED

- FOUND: plugins/review_gates/gate.py
- FOUND: plugins/review_gates/tests/test_gate.py
- FOUND: 78a08b5c0 (test RED)
- FOUND: 6d6c29029 (feat GREEN)
