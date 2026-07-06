---
phase: 40-gate-redlines
plan: 02
subsystem: review-gates
tags: [redline, gate-registration, auto-detect, runner_hooks, tools-dispatch, gates-yaml, tdd, gate-04]
requires:
  - Phase 34 review_gates plugin (gate.py FROZEN state machine, runner_hooks.pause_for_review HIL path)
  - Plan 40-01 DETECTOR_REGISTRY + 3 redline detector modules (R1/R3/R4)
  - Phase 39 formula_library read-side convention (formula:-prefixed suggested_action)
provides:
  - plugins.review_gates.runner_hooks.is_redline_gate (prefix classifier)
  - plugins.review_gates.runner_hooks.auto_detect_and_resolve (auto-detect entry point)
  - plugins.review_gates.gates.yaml 11-entry registry (8 V8.6 + 3 redline, additive)
  - plugins.review_gates.tools._handle_gate_submit redline-aware dispatch (status=auto_resolved)
  - plugins.review_gates.gate_config 11-count enforcement (GATE-04)
affects:
  - Plan 40-03 (review-gates.md SKILL ref documents the auto-detect path + 11-gate table)
  - Phase 35 runner (may call auto_detect_and_resolve directly for redline gates; tools.py already routes)
  - Phase 39 formula_library (read-side consumer of formula: suggested_action emitted on reject)
tech-stack:
  added: []
  patterns:
    - gate_id prefix dispatch (redline_ → auto path; else → V8.6 HIL path)
    - T-40-05 mitigation — unknown redline_X without DETECTOR_REGISTRY entry raises KeyError (never silent auto-approve)
    - T-40-07 mitigation — auto-resolved gate still writes review-outcomes slot for audit trail (CF-04 preserved)
    - T-40-09 mitigation — only DETECTOR_REGISTRY keys can auto-resolve; prefix check is necessary-but-not-sufficient
    - lazy import of DETECTOR_REGISTRY inside auto_detect_and_resolve (avoids module-load cycle, keeps V8.6-only path decoupled)
    - TDD RED/GREEN across 3 tasks (failing tests + stubs → yaml + loader bump → runner_hooks + tools wiring)
key-files:
  created:
    - plugins/review_gates/tests/test_redline_gate_wiring.py
  modified:
    - plugins/review_gates/gates.yaml
    - plugins/review_gates/gate_config.py
    - plugins/review_gates/runner_hooks.py
    - plugins/review_gates/tools.py
    - plugins/review_gates/__init__.py
    - plugins/review_gates/plugin.yaml
    - plugins/review_gates/tests/test_gates_config.py
    - plugins/review_gates/tests/test_tools_dispatch.py
decisions:
  - GATE-04 honored — additive bump 8 → 11; the 8 V8.6 entries are byte-preserved in gates.yaml (verified by test_load_gates_preserves_8_v86_gate_ids_byte_for_byte)
  - gate.py FROZEN — auto_detect_and_resolve consumes Phase 34's public Gate.resolve() API only; zero edits to gate.py
  - gate_id prefix dispatch — redline_-prefixed gate_ids route to auto_detect_and_resolve; all other gate_ids keep pause_for_review (V8.6 HIL). The prefix check is the single dispatch branch-point in _handle_gate_submit.
  - T-40-05 mitigation — unknown redline_X gate_id (prefix matches but DETECTOR_REGISTRY miss) raises KeyError. Caller (tools._handle_gate_submit) catches and emits status=detector_missing tool_error. NEVER silent auto-approve.
  - lazy DETECTOR_REGISTRY import — the import lives inside auto_detect_and_resolve, not at module top. V8.6-only callers can import runner_hooks without requiring the gates/ subpackage to be populated (forward-compat + avoids a load-time cycle if gates/__init__.py ever grows a runner_hooks reach-back).
  - All 3 redline gates share phase=p13_delivery — they fire AFTER gate 8 (delivery-gate) passes, as the final scan before master.mp4 release (per ROADMAP Phase 40 SC#3).
  - reviewer_role=redline_scanner — the auto-detect reviewer identity. Distinct from the V8.6 human reviewers (creative_source / script_auditor / editor / compliance_marketing) so audit trails distinguish auto vs manual resolution.
  - tool envelope shape — auto-resolved gates emit status=auto_resolved (distinct from status=submitted for V8.6 HIL and status=resolved for gate_resolve). Operators can tell at a glance whether a gate auto-resolved or went through HIL.
metrics:
  duration: ~6min
  completed: 2026-06-27T00:12:00Z
  tasks: 3
  files_created: 1
  files_modified: 8
  tests_added: 23
  total_review_gates_tests: 145
  loc_runner_hooks_added: 176
  loc_tools_dispatch_added: 63
  loc_gates_yaml_added: 54
---

# Phase 40 Plan 02: GATE — Wire Redline Detectors into V8.6 Gate Sequence Summary

Registered the 3 Phase 40-01 redline detectors (R1 emotion-desensitization / R3 no-cold-open / R4 unfinished-ending) on the Phase 34 state machine additively (gates.yaml 8→11) and wired them to auto-resolve via `runner_hooks.auto_detect_and_resolve()` — the 8 V8.6 gates keep their manual HIL `pause_for_review` path with zero behavior change, and the `redline_` prefix on a gate_id is the single dispatch branch-point in `tools._handle_gate_submit`.

## What Was Built

### `plugins/review_gates/gates.yaml` — 11-entry registry (additive)

Appended 3 new `GateConfig` entries (gates 9/10/11) below the 8 V8.6 entries, which are byte-preserved. Each redline gate:

- `gate_id`: `redline_emotion_desensitize` (R1) / `redline_no_cold_open` (R3) / `redline_unfinished_ending` (R4)
- `phase`: `p13_delivery` (fire AFTER gate 8 delivery-gate passes, as the final scan before master.mp4 release — ROADMAP Phase 40 SC#3)
- `reviewer_role`: `redline_scanner` (distinct from V8.6 human reviewers for audit clarity)
- `timeout_sec`: 60 (auto-detect is sub-second; short budget)
- `default_mode`: `blocking` (runner_hooks auto-resolves, no webhook needed)
- `retry_policy`: `max_retries: 1, backoff_sec: 60` (transient-error tolerance)
- `asset_bus_slots_to_lock`: `final-shots` (+ `master-mp4` for R1)

### `plugins/review_gates/gate_config.py` — count check bumped 8→11

Single semantic change: `if len(gate_list) != 8:` → `if len(gate_list) != 11:` with a Phase 40 GATE-04 rationale comment. The error message now says `exactly 11 gates`. Module docstring + `Raises:` section updated to mention the additive bump.

### `plugins/review_gates/runner_hooks.py` — auto-detect path (+176 LOC)

Two new public functions appended after `mark_episode_failed` (Phase 34 contracts `pause_for_review` / `resume_from_callback` / `resolve_direct` / `poll_until_terminal` / `mark_episode_failed` UNTOUCHED):

- **`is_redline_gate(gate_id) -> bool`** — True iff `gate_id` starts with `redline_`. Defensive against None/non-str input (returns False). Used by `tools._handle_gate_submit` as the dispatch branch-point.
- **`auto_detect_and_resolve(gate_id, episode_id, payload) -> dict`** — looks up the Plan-01 detector in `DETECTOR_REGISTRY`, runs it on the payload, and calls `Gate.resolve()` with the detector's verdict. Mirrors `pause_for_review`'s shape (build Gate → submit → resolve → write outcome → advance state) but skips the manual-resolution wait. Reject path surfaces `rollback_to` (mirrors `resume_from_callback`). Unknown `redline_X` gate_id without a registered detector raises `KeyError` (T-40-05 mitigation — never silent auto-approve).

Implementation highlights:
- Lazy import of `DETECTOR_REGISTRY` inside the function body (avoids module-load cycle; V8.6-only callers can import `runner_hooks` without requiring `gates/` subpackage).
- Fires the Phase 37 `_on_gate_resolved` hook (D-37-07) so canvas-sync subscribers observe auto-resolutions the same as HIL resolutions.
- Registers the resolved gate in `_PENDING_GATES` for audit visibility (Phase 34 `pause_for_review` does the same).

### `plugins/review_gates/tools.py` — `_handle_gate_submit` redline-aware dispatch (+63 LOC)

The existing V8.6 path is UNCHANGED (lines after the new branch). A new branch prepended right after the `GATE_REGISTRY` check routes `redline_`-prefixed gate_ids to `auto_detect_and_resolve`:

```python
if runner_hooks.is_redline_gate(gate_id):
    try:
        outcome = runner_hooks.auto_detect_and_resolve(gate_id, episode_id, payload)
    except GateMaxRetriesExceeded as exc:
        runner_hooks.mark_episode_failed(episode_id, gate_id, exc)
        return tool_error(str(exc), status="episode_failed", ...)
    except KeyError as exc:
        return tool_error(str(exc), status="detector_missing", ...)
    return tool_result({
        "status": "auto_resolved",           # distinct from "submitted" (V8.6 HIL)
        "decision": outcome.get("decision"),
        "suggested_action": outcome.get("suggested_action"),
        "rollback_to": outcome.get("rollback_to"),
        ...
    })
# else: existing V8.6 pause_for_review path (unchanged)
```

Operators can tell at a glance from the envelope `status` whether a gate auto-resolved (`auto_resolved`) vs went through HIL (`submitted`).

### `plugins/review_gates/__init__.py` — docstring update

Mentions Phase 40 redline auto-detect path + `runner_hooks.auto_detect_and_resolve` for operators reading the plugin source.

### `plugins/review_gates/plugin.yaml` — version bump 0.1.0 → 0.2.0

Description updated: `"review gate framework plugin — HIL gate lifecycle (submit/wait/resolve) + 11 gates (8 V8.6 + 3 Phase 40 redline)"`.

### `plugins/review_gates/tests/test_gates_config.py` — TestLoadGates + TestRedlineGates (+165 LOC)

- `TestLoadGates.EXPECTED_GATE_IDS` now includes the 3 redline IDs (11 total).
- `test_load_gates_returns_dict_with_exactly_8_entries` → `..._11_entries` (asserts `len == 11`).
- New tests: `test_load_gates_preserves_8_v86_gate_ids_byte_for_byte`, `test_load_gates_includes_3_redline_gate_ids`, `test_all_11_gate_ids_are_unique`.
- New `TestRedlineGates` class with 6 field-level spot-checks: default_mode==blocking, reviewer_role==redline_scanner, positive timeout ≤300s, retry_policy max_retries>0, phase==p13_delivery, final-shots slot locked.
- Bad-YAML tests now pad to 11 (was 8) to reach field-validation. New `test_wrong_count_raises_gateconfigerror` verifies 8 entries now fails with "exactly 11".

### `plugins/review_gates/tests/test_tools_dispatch.py` — TestGatesList expects 11

- `test_returns_all_8_gates` → `test_returns_all_11_gates` (asserts `count == 11`).
- `test_each_gate_has_required_fields` docstring updated to "all 11".

### `plugins/review_gates/tests/test_redline_gate_wiring.py` (NEW — 343 LOC, 7 classes, 14 cases)

End-to-end auto-detect wiring tests:

| Class | Cases | Coverage |
|---|---|---|
| TestIsRedlineGate | 3 | prefix classifier: redline_* → True; V8.6 → False; None/empty → False |
| TestAutoDetectEmotionDesensitize | 3 | R1 violation → reject+formula:emotion-break-up+rollback_to; compliant → approve+None; outcome written to review-outcomes.json |
| TestAutoDetectNoColdOpen | 2 | R3 first-beat-exposition → reject; R1 emotion payload does NOT trip R3 (no cross-wiring) |
| TestAutoDetectUnfinishedEnding | 1 | R4 last-beat-resolution → reject+formula:open-question-cliffhanger |
| TestV86GatesUnchanged | 1 | pause_for_review('topic-gate') leaves gate PENDING (Phase 34 HIL preserved) |
| TestToolGateSubmitRedlineDispatch | 3 | redline submit → status=auto_resolved+decision; compliant → auto_resolved+approve; V8.6 submit still returns status=submitted |
| TestUnknownRedlineGateRaises | 1 | redline_unknown_test (not in DETECTOR_REGISTRY) → KeyError (T-40-05 mitigation) |

## Commits

| Hash | Type | Message |
|---|---|---|
| `1f0e2fe3f` | test | `test(phase-40-02): add failing tests for 11 gates + redline auto-detect (RED)` — 27 tests RED (TestV86GatesUnchanged already GREEN — Phase 34 path unchanged) |
| `d1322404e` | feat | `feat(phase-40-02): append 3 redline gates to registry (8->11) — GREEN` — gates.yaml + gate_config count bump + plugin.yaml version |
| `e39a9585f` | feat | `feat(phase-40-02): wire redline auto-detect path into runner_hooks + tools — GREEN` — is_redline_gate + auto_detect_and_resolve + _handle_gate_submit dispatch |

## Verification

All plan verification gates met:

| Gate | Required | Actual | Status |
|---|---|---|---|
| gates.yaml holds 11 entries (8 byte-preserved + 3 appended) | yes | 11 entries; V86_GATE_IDS subset test passes | PASS |
| gate_config.py count check bumped 8 → 11 | yes | line 98 `!= 11`; error message says "exactly 11 gates" | PASS |
| auto_detect_and_resolve routes redline_ gates through DETECTOR_REGISTRY | yes | 7 classes / 14 cases in test_redline_gate_wiring.py pass | PASS |
| V8.6 8-gate HIL path preserved (zero behavior change) | yes | 24 tests in test_runner_hooks.py + test_tools_dispatch.py pass (Phase 34 regression-free) | PASS |
| Unknown redline_* gate_id without DETECTOR_REGISTRY entry raises KeyError | yes | TestUnknownRedlineGateRaises.test_redline_prefix_not_in_detector_registry_raises_keyerror | PASS |
| gates_list reports 11 gates | yes | test_returns_all_11_gates passes | PASS |
| tool envelope for redline auto-reject shows status="auto_resolved" | yes | TestToolGateSubmitRedlineDispatch.test_redline_submit_returns_auto_resolved_envelope | PASS |
| Zero edits to FROZEN plugins/review_gates/gate.py | yes | `git diff HEAD~3 HEAD -- plugins/review_gates/gate.py` is empty | PASS |
| Zero edits to Plan 40-01 / 40-03 owned files | yes | gates/__init__.py, gates/types.py, gates/redline_*.py, test_redline_*.py untouched; review-gates.md / README.md untouched (Plan 40-03 sibling) | PASS |
| Full review_gates test suite green | yes | 145 passed (122 Plan 40-01 + 23 Plan 40-02) in 3.91s | PASS |
| TDD gates: RED + GREEN + GREEN commits present | yes | 1f0e2fe3f (test RED) + d1322404e (feat GREEN) + e39a9585f (feat GREEN) | PASS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] KeyError catch in tools._handle_gate_submit added `status="detector_missing"` envelope**

- **Found during:** Task 3 GREEN phase
- **Issue:** The Plan's Task 3 action script for `_handle_gate_submit` shows the redline dispatch catching `GateMaxRetriesExceeded` but does NOT explicitly show a `KeyError` catch for the T-40-05 mitigation path. Without the catch, the unknown-redline KeyError would propagate as an unhandled exception, crashing the tool handler rather than returning a structured tool_error envelope.
- **Fix:** Added `except KeyError as exc:` clause returning `tool_error(str(exc), status="detector_missing", gate_id=..., episode_id=...)`. The KeyError message from `auto_detect_and_resolve` is rich (lists registered detectors + misconfiguration hint), so surfacing it verbatim gives operators an actionable error.
- **Files modified:** plugins/review_gates/tools.py
- **Commit:** e39a9585f

**2. [Rule 1 - Bug] V8.6 gate_id check happens before redline dispatch — preserves "unknown gate_id" error for unknown redline_X**

- **Found during:** Task 3 test design
- **Issue:** The T-40-05 test (`TestUnknownRedlineGateRaises`) needed to construct a fake `redline_unknown_test` gate_id. But `tools._handle_gate_submit` checks `gate_id not in GATE_REGISTRY` BEFORE the redline dispatch — an unknown redline_X gate_id would be rejected as "Unknown gate_id" by the GATE_REGISTRY check, never reaching `auto_detect_and_resolve`. This is actually the CORRECT behavior (T-40-05 mitigation: GATE_REGISTRY membership is necessary-but-not-sufficient; DETECTOR_REGISTRY membership is the second check).
- **Fix:** The test bypasses the GATE_REGISTRY check by monkeypatching `runner_hooks.to_gate_config` directly, then calls `auto_detect_and_resolve` directly (not through `_handle_gate_submit`). This correctly tests the T-40-05 mitigation at the layer where it lives (auto_detect_and_resolve's DETECTOR_REGISTRY lookup). No code change needed — the layering is correct as designed.
- **Files modified:** none (test-only)
- **Commit:** 1f0e2fe3f (RED)

### Parallel-executor observations

**3. [Observation] Plan 40-03 sibling executor landed between Task 2 and Task 3**

- **Found during:** Task 3 commit
- **Issue:** A concurrent Plan 40-03 executor's commit `b41502805` (`docs(phase-40-03): SUMMARY — review-gates.md 8→11 + plugin README bilingual`) landed between my Task 2 (`d1322404e`) and Task 3 (`e39a9585f`) commits. Plan 40-03 owns `skills/kais-movie-pipeline/references/review-gates.md` + `plugins/review_gates/README.md` — files I do NOT touch.
- **Resolution:** Verified my 3 commits' file stats show zero overlap with Plan 40-03's files (each commit contains only my in-scope files). The race-condition avoidance via explicit `git add <file1> <file2>` per the execution_protocol worked correctly.
- **Files modified:** none

## Known Stubs

None. The 3 redline gates are fully wired end-to-end:
- gates.yaml registration ✓
- gate_config.py count enforcement ✓
- runner_hooks.auto_detect_and_resolve dispatch ✓
- tools._handle_gate_submit redline-aware routing ✓
- Asset bus review-outcomes write (CF-04 audit trail) ✓
- PipelineState advancement (approved/rejected/contested) ✓
- Phase 37 on_gate_resolved hook fires (canvas-sync parity) ✓
- Rollback target surfaced on reject (Phase 35 runner signal) ✓

The `formula:`-prefixed suggested_action strings (`emotion-break-up` / `cold-open-conflict-hook` / `open-question-cliffhanger`) are emitted by Plan 40-01 detectors and carried through `auto_detect_and_resolve` → `Gate.resolve()` → asset bus → tool envelope unchanged. The formula_library entries themselves are owned by Phase 39 (already shipped).

## Threat Flags

None. The auto-detect path introduces no new network surface (detectors are pure stdlib — D-34-01 extended per Plan 40-01's purity AST guard). The only externally-visible behavior change is the `status="auto_resolved"` tool envelope (distinct from V8.6 `status="submitted"`), which is itself a safety feature: operators can audit which gates auto-resolved vs went through HIL.

The T-40-05 mitigation (KeyError on unknown redline_X) is itself a threat-control: it prevents a misconfigured `redline_X` gate_id from silently auto-approving. The purity AST guard (`test_redline_purity.py` from Plan 40-01) catches supply-chain drift at CI time.

## TDD Gate Compliance

- RED gate commit present: `1f0e2fe3f` (`test(phase-40-02): ...`) — 27 tests fail (count asserts + auto-detect AttributeError).
- GREEN gate commit present after RED: `d1322404e` (`feat(phase-40-02): append 3 redline gates ...`) — Tests 1-2 (gates_config + gates_list count) pass.
- GREEN gate commit present after GREEN: `e39a9585f` (`feat(phase-40-02): wire redline auto-detect path ...`) — Tests 3-8 (auto-detect wiring) pass; all 145 review_gates tests green.

All gates satisfied. No gate skipped. (Plan 40-02 is `type: tdd`; the plan was decomposed into 3 atomic tasks each with its own RED→GREEN cycle. The plan-level TDD gate is satisfied by the sequence: RED test commit precedes GREEN implementation commits.)

## Self-Check: PASSED

- FOUND: plugins/review_gates/gates.yaml
- FOUND: plugins/review_gates/gate_config.py
- FOUND: plugins/review_gates/runner_hooks.py
- FOUND: plugins/review_gates/tools.py
- FOUND: plugins/review_gates/__init__.py
- FOUND: plugins/review_gates/plugin.yaml
- FOUND: plugins/review_gates/tests/test_gates_config.py
- FOUND: plugins/review_gates/tests/test_tools_dispatch.py
- FOUND: plugins/review_gates/tests/test_redline_gate_wiring.py
- FOUND: 1f0e2fe3f (test RED)
- FOUND: d1322404e (feat GREEN — yaml + count)
- FOUND: e39a9585f (feat GREEN — wiring)
