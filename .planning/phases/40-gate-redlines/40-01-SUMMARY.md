---
phase: 40-gate-redlines
plan: 01
subsystem: review-gates
tags: [redline, detector, r1, r3, r4, emotion, cold-open, cliffhanger, stdlib, purity, tdd]
requires:
  - Phase 34 review_gates plugin (gate.py frozen state machine, tests/test_gate.py purity pattern)
  - skills/kais-movie-pipeline/references/creative-redlines.md (R1/R3/R4 source spec)
provides:
  - plugins.review_gates.gates.types.DetectorResult (typed alias)
  - plugins.review_gates.gates.types.DetectorFn (Protocol)
  - plugins.review_gates.gates.types.reject_action (formula: helper)
  - plugins.review_gates.gates.redline_emotion_desensitize.detect (R1)
  - plugins.review_gates.gates.redline_no_cold_open.detect (R3)
  - plugins.review_gates.gates.redline_unfinished_ending.detect (R4)
  - plugins.review_gates.gates.DETECTOR_REGISTRY (gate_id -> detect fn)
affects:
  - Plan 40-02 (runner_hooks imports DETECTOR_REGISTRY for auto-detect dispatch)
  - Plan 40-03 (review-gates.md SKILL ref documents the 3 redline gates)
  - Phase 39 formula_library (read-side consumer of formula: action strings)
tech-stack:
  added: []
  patterns:
    - pure-stdlib detector leaf (D-34-01 extended) — no httpx/jwt/yaml/external-plugins.* imports
    - intra-package typing allow-list (gates.types whitelisted; broader plugins.* reach-back blocked)
    - TDD RED/GREEN/REFACTOR cycle (NotImplementedError stub -> minimal impl -> registry wiring)
    - formula:-prefixed suggested_action convention (Phase 39 formula_library read-side lookup)
    - defensive .get() access on untrusted payload (T-40-01 mitigation — no KeyError ever raised)
    - AST-walk purity guard mirroring test_gate.py:45-60 (catches supply-chain drift at CI)
key-files:
  created:
    - plugins/review_gates/gates/__init__.py
    - plugins/review_gates/gates/types.py
    - plugins/review_gates/gates/redline_emotion_desensitize.py
    - plugins/review_gates/gates/redline_no_cold_open.py
    - plugins/review_gates/gates/redline_unfinished_ending.py
    - plugins/review_gates/tests/test_redline_emotion_desensitize.py
    - plugins/review_gates/tests/test_redline_no_cold_open.py
    - plugins/review_gates/tests/test_redline_unfinished_ending.py
    - plugins/review_gates/tests/test_redline_purity.py
  modified: []
decisions:
  - D-34-01 extended honored — detector modules import only stdlib (typing) + their own sibling gates.types (pure-typing); AST-verified by test_detector_modules_have_no_forbidden_imports across all 4 modules
  - D-34-05 honored — no ast.AsyncFunctionDef nodes in any detector module (AST-verified by test_detector_modules_have_no_async_def); detectors are sync pure functions
  - formula_id canonical strings — R1="emotion-break-up" / R3="cold-open-conflict-hook" / R4="open-question-cliffhanger"; all match ^formula:[a-z][a-z0-9-]*$ (Phase 39 read-side convention, GATE-04 #4)
  - reject_action() helper centralized in types.py — single source of truth for the formula: prefix; all 3 detectors call it instead of hardcoding f-strings (DRY)
  - T-40-01 mitigation — defensive .get() throughout; missing beats key, empty beats, non-dict beat entries, and missing label/emotion keys all fall through to ("approve", None). No KeyError ever raised.
  - R1 boundary pinned — <3 beats returns approve (cannot form a 3-window); exactly 2 consecutive same-emotion is OK (R1 spec: "第 3 个连续同类型即触发脱敏")
  - R1 None-emotion handling — all-None window (every beat missing emotion) conservatively rejects; flags malformed payload as the safe failure mode
metrics:
  duration: ~7min
  completed: 2026-06-26T15:59:39Z
  tasks: 3
  files_created: 9
  tests_added: 54
  total_review_gates_tests: 122
  loc_types_py: 83
  loc_init_py: 52
  loc_redline_emotion_desensitize_py: 78
  loc_redline_no_cold_open_py: 73
  loc_redline_unfinished_ending_py: 73
---

# Phase 40 Plan 01: 3 Redline Detectors (R1/R3/R4) Summary

3 pure-stdlib redline detector modules (R1 emotion-desensitization / R3 zero-backstory-preamble / R4 unresolved-ending) emitting `(decision, suggested_action)` tuples with `formula:`-prefixed action strings for Phase 39 formula_library read-side lookup, plus a 4-file TDD test suite (54 cases) with an AST-walk purity guard extending the D-34-01 discipline to the new detector leaf.

## What Was Built

### `plugins/review_gates/gates/types.py` (83 LOC)

Pure-typing module defining the detector public contract.

- `Decision = Literal["approve", "reject", "contest"]` — three-value decision type (the 3 redline detectors emit only approve/reject; "contest" is forward-compat for future hybrid detectors).
- `SuggestedAction = str | None` — None for approve, formula:-prefixed string for reject.
- `DetectorResult = tuple[Decision, SuggestedAction]` — canonical tuple shape.
- `reject_action(formula_id) -> str` — helper that emits `f"formula:{formula_id}"`. Centralizes the Phase 39 convention so all 3 detectors share a single source of truth (DRY); future formula_id regex changes touch one function.
- `DetectorFn` Protocol — declares `GATE_ID: str`, `REDLINE_REF: str`, `detect(payload) -> DetectorResult`. Documentation-only contract; detectors satisfy it structurally.

### `plugins/review_gates/gates/redline_emotion_desensitize.py` (78 LOC) — R1

Operationalizes creative-redlines.md §R1 (情绪脱敏 / Emotion Desensitization).

- `GATE_ID = "redline_emotion_desensitize"`, `REDLINE_REF = "creative-redlines.md §R1"`.
- `_FORMULA_ID = "emotion-break-up"`, `_RUN_LENGTH = 3` (the 3rd consecutive same-emotion beat triggers violation per spec).
- `detect(payload)`: walks `payload["beats"]` with a 3-element sliding window; if all 3 beats in any window share the same `emotion` value → `("reject", "formula:emotion-break-up")`. Else `("approve", None)`.
- Boundary: `<3` beats → approve (cannot form a violating window).
- Defensive: missing `beats` key, non-dict beat entries, and missing `emotion` keys all handled via `.get()` and `isinstance()` checks. All-None window (every beat missing emotion) conservatively rejects (flags malformed payload).

### `plugins/review_gates/gates/redline_no_cold_open.py` (73 LOC) — R3

Operationalizes creative-redlines.md §R3 (零背景铺垫 / Zero Backstory Preamble).

- `GATE_ID = "redline_no_cold_open"`, `REDLINE_REF = "creative-redlines.md §R3"`.
- `_FORMULA_ID = "cold-open-conflict-hook"`, `_VIOLATION_LABELS = frozenset({"exposition", "narration", "setup"})`.
- `detect(payload)`: reads `beats[0].get("label")`; if in `_VIOLATION_LABELS` → `("reject", "formula:cold-open-conflict-hook")`. Else `("approve", None)`.
- Defensive: missing `beats`, empty list, non-dict first beat, missing `label` key all fall through to approve.

### `plugins/review_gates/gates/redline_unfinished_ending.py` (73 LOC) — R4

Operationalizes creative-redlines.md §R4 (结尾未完成 / Unresolved Ending).

- `GATE_ID = "redline_unfinished_ending"`, `REDLINE_REF = "creative-redlines.md §R4"`.
- `_FORMULA_ID = "open-question-cliffhanger"`, `_VIOLATION_LABELS = frozenset({"resolution", "closure", "epilogue"})`.
- `detect(payload)`: reads `beats[-1].get("label")`; if in `_VIOLATION_LABELS` → `("reject", "formula:open-question-cliffhanger")`. Else `("approve", None)`.
- Defensive: same T-40-01 hardening as R3.

### `plugins/review_gates/gates/__init__.py` (52 LOC)

Subpackage marker + `DETECTOR_REGISTRY` surface.

- `DETECTOR_REGISTRY: Dict[str, DetectorFn]` — populated with all 3 detectors keyed by `GATE_ID`:
  ```
  {
    "redline_emotion_desensitize": redline_emotion_desensitize.detect,
    "redline_no_cold_open":        redline_no_cold_open.detect,
    "redline_unfinished_ending":   redline_unfinished_ending.detect,
  }
  ```
- Plan 02's `runner_hooks` imports this dict to dispatch the auto-detect path for `redline_`-prefixed gate_ids. The 8 V8.6 gates do NOT appear here (they use the manual HIL resolution path in `gate.py` / `tools.py`).

### `plugins/review_gates/tests/test_redline_*.py` (4 files, 54 cases)

TDD test suite across 4 files:

| File | Class / Group | Cases | Coverage |
|---|---|---|---|
| test_redline_emotion_desensitize.py | Identity | 2 | GATE_ID exact; REDLINE_REF cites §R1 |
| test_redline_emotion_desensitize.py | Positive | 3 | 3 consecutive same emotion (anger/sadness/anywhere-in-seq) → reject + formula: |
| test_redline_emotion_desensitize.py | Negative | 1 | 2 same + 1 different → approve |
| test_redline_emotion_desensitize.py | Edge | 4 | exactly-2 boundary; empty beats; missing beats key; missing emotion key (no crash) |
| test_redline_emotion_desensitize.py | Determinism | 2 | detect(p) == detect(p) positive + negative |
| test_redline_no_cold_open.py | Identity | 2 | GATE_ID; REDLINE_REF §R3 |
| test_redline_no_cold_open.py | Positive | 3 | parametrized exposition/narration/setup → reject |
| test_redline_no_cold_open.py | Negative | 3 | parametrized active_conflict/other/cliffhanger → approve |
| test_redline_no_cold_open.py | Edge | 4 | empty; missing beats; missing label key; single-beat preamble rejects |
| test_redline_no_cold_open.py | Determinism | 2 | positive + negative |
| test_redline_unfinished_ending.py | Identity | 2 | GATE_ID; REDLINE_REF §R4 |
| test_redline_unfinished_ending.py | Positive | 3 | parametrized resolution/closure/epilogue → reject |
| test_redline_unfinished_ending.py | Negative | 4 | parametrized open_question/cliffhanger/active_conflict/other → approve; mid-sequence closure OK |
| test_redline_unfinished_ending.py | Edge | 4 | empty; missing beats; missing label key; single-beat closure rejects |
| test_redline_unfinished_ending.py | Determinism | 2 | positive + negative |
| test_redline_purity.py | Forbidden imports | 4 | AST-walk all 4 modules — no httpx/jwt/yaml; no plugins.* reach-back except whitelisted sibling types.py |
| test_redline_purity.py | No async def | 4 | AST-walk all 4 modules — 0 AsyncFunctionDef nodes (D-34-05) |
| test_redline_purity.py | Formula convention | 3 | returned string literals match ^formula:[a-z][a-z0-9-]*$ |
| test_redline_purity.py | Subpackage import | 1 | gates/ importable without gate_config.py / gates.yaml |

## Commits

| Hash | Type | Message |
|---|---|---|
| `32605925b` | test | `test(phase-40-01): add failing tests + stubs for 3 redline detectors (RED)` — 36 behavior tests fail with NotImplementedError; 12 purity tests pass |
| `4b8b28a02` | feat | `feat(phase-40-01): implement 3 redline detectors (R1/R3/R4) — GREEN` — all 54 tests pass |
| `300f689ae` | refactor | `refactor(phase-40-01): populate DETECTOR_REGISTRY with 3 redline detectors` — registry wired; 122 total tests in plugins/review_gates/tests/ pass (no regression) |

## Verification

All plan verification gates met:

| Gate | Required | Actual | Status |
|---|---|---|---|
| 3 detector modules exist under plugins/review_gates/gates/ | yes | redline_emotion_desensitize.py + redline_no_cold_open.py + redline_unfinished_ending.py | PASS |
| All detector tests pass | yes | 54/54 pass in 0.21s | PASS |
| Phase 34 regression — zero edits to gate.py | yes | gate.py untouched; test_gate.py + test_gates_config.py + test_runner_hooks.py + test_tools_dispatch.py all pass (68 tests) | PASS |
| DETECTOR_REGISTRY importable with 3 keys | yes | `python3 -c "from plugins.review_gates.gates import DETECTOR_REGISTRY; ..."` exits 0; keys = {redline_emotion_desensitize, redline_no_cold_open, redline_unfinished_ending} | PASS |
| No forbidden imports (httpx/jwt/yaml) in gates/*.py | yes | grep returns nothing | PASS |
| No plugins.* reach-back (gate/gate_config/runner_hooks/tools) | yes | grep returns nothing (only intra-package gates.* imports, allow-listed) | PASS |
| All reject-branch suggested_action match ^formula:[a-z][a-z0-9-]*$ | yes | emotion-break-up / cold-open-conflict-hook / open-question-cliffhanger all match | PASS |
| No async def in detector modules | yes | 0 AsyncFunctionDef nodes (AST-verified) | PASS |
| TDD gates: RED + GREEN + REFACTOR commits present | yes | 32605925b + 4b8b28a02 + 300f689ae | PASS |
| Full plugins/review_gates/tests/ suite | yes | 122 passed, 1 warning (unrelated discord/audioop DeprecationWarning) in 3.73s | PASS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Purity test initially over-blocked intra-package typing import**

- **Found during:** Task 1 (RED phase)
- **Issue:** The first purity test draft forbade ALL `plugins.*` imports, which blocked the detectors' own sibling `from plugins.review_gates.gates.types import DetectorResult, reject_action`. This made the purity test fail on the stubs themselves before any behavior test could run.
- **Fix:** Split `_FORBIDDEN_TOP` (external: httpx/jwt/yaml) from `_FORBIDDEN_PLUGINS_REACHBACK` (broader plugins.* surface: gate.py/gate_config.py/runner_hooks.py/tools.py — Plan 02's wiring direction) with an `_ALLOWED_INTRA_PACKAGE` allow-list whitelisting `plugins.review_gates.gates` and `plugins.review_gates.gates.types`. The T-40-04 supply-chain intent (block external network/config surface) is preserved; intra-package pure-typing imports are permitted.
- **Files modified:** plugins/review_gates/tests/test_redline_purity.py
- **Commit:** 32605925b (RED)

**2. [Rule 3 - Blocking Issue] Parallel-executor commit collision during RED staging**

- **Found during:** Task 1 commit attempt
- **Issue:** A concurrent Phase 39-01 executor's `git add` captured my untracked Plan 40-01 files into their commit `651e248a8` ("feat(phase-39-01): plugin scaffold + Pydantic schema"). That commit was later orphaned (not reachable from any ref — the parallel executor did `git reset`/`rebase` that abandoned it), returning my files to untracked state. No content loss occurred, but the staging state was briefly confusing.
- **Fix:** Verified working-tree content was intact (latest edits including the purity allow-list fix were on disk), then re-staged only my 9 in-scope files and committed the RED gate cleanly. The orphaned `651e248a8` is left untouched (not my commit to rewrite; it's unreachable so it'll be GC'd naturally).
- **Files modified:** none (recovery only)
- **Commit:** 32605925b (RED, clean re-stage)

## Known Stubs

None. All 3 detectors are fully implemented per the R1/R3/R4 specs. The `formula:`-prefixed action strings (`emotion-break-up` / `cold-open-conflict-hook` / `open-question-cliffhanger`) are read-side lookup keys for the Phase 39 formula_library — the library entries themselves are owned by Plan 39-02 (already shipped per recent git log). The detectors emit the keys; Plan 02's runner_hooks will consume them to drive `Gate.resolve()`.

## Threat Flags

None. The 3 detector modules are pure in-process functions with no network surface, no file system access, no auth boundary. The only externally-visible behavior is the `(decision, suggested_action)` tuple emitted to the caller. The purity AST guard (`test_redline_purity.py`) is itself a safety feature — it catches supply-chain drift (T-40-04) at CI time before a forbidden dependency enters the detector leaf.

## TDD Gate Compliance

- RED gate commit present: `32605925b` (`test(phase-40-01): ...`) — 36 behavior tests fail with NotImplementedError.
- GREEN gate commit present after RED: `4b8b28a02` (`feat(phase-40-01): ...`) — all 54 tests pass.
- REFACTOR gate commit present after GREEN: `300f689ae` (`refactor(phase-40-01): ...`) — registry wired, 122 total tests pass (no regression).

All 3 gates satisfied. No gate skipped.

## Self-Check: PASSED

- FOUND: plugins/review_gates/gates/__init__.py
- FOUND: plugins/review_gates/gates/types.py
- FOUND: plugins/review_gates/gates/redline_emotion_desensitize.py
- FOUND: plugins/review_gates/gates/redline_no_cold_open.py
- FOUND: plugins/review_gates/gates/redline_unfinished_ending.py
- FOUND: plugins/review_gates/tests/test_redline_emotion_desensitize.py
- FOUND: plugins/review_gates/tests/test_redline_no_cold_open.py
- FOUND: plugins/review_gates/tests/test_redline_unfinished_ending.py
- FOUND: plugins/review_gates/tests/test_redline_purity.py
- FOUND: 32605925b (test RED)
- FOUND: 4b8b28a02 (feat GREEN)
- FOUND: 300f689ae (refactor REFACTOR)
