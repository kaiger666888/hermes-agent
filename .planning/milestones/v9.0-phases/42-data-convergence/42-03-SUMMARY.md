---
phase: 42-data-convergence
plan: 03
subsystem: plugins/platform_metrics
tags: [tuning-loop, jsonl-queue, formula-writeback, evol02-pattern, hil-invariant, tdd, scope-discipline]
requires:
  - "42-01 (PlatformMetrics + FeedbackRecordExtension + TuningSuggestion + MetricTrigger schemas)"
  - "42-02 (adapter stubs — not directly consumed, but completes the DATA-01 contract)"
  - "39-FORM (plugins/formula_library/library/*.json — write-back target)"
  - "28-INGEST v6.0 (agent/evolution/queue.py EVOL-02 pattern — mirrored, not imported)"
provides:
  - "JSONL review queue (plugins/platform_metrics/queue.py): append_suggestion / move_suggestion / read_queue"
  - "formula tuning loop (plugins/platform_metrics/tuning_loop.py): run_tuning_loop + classify_metrics + TuningThresholds"
  - "atomic library write-back (plugins/platform_metrics/library_writer.py): apply_suggestion + SuggestionNotApprovedError HIL gate"
  - "DATA-03 complete: metrics → suggestions → JSONL queue → operator approve → formula_library eval_score write-back"
affects:
  - "Plan 42-04 (CLI consumes read_queue for stats dashboard display)"
  - "Phase 43 VALIDATE (SC#3 cross-phase integration check)"
tech-stack:
  added: []
  patterns:
    - "JSONL queue mirror of v6.0 EVOL-02 (queue/applied/rejected.jsonl + atomic rewrite + WR-02/WR-03 ordering)"
    - "Protocol-based decoupling from v6.0 FeedbackStore (FeedbackStoreLike + ExtensionStore — no concrete class import)"
    - "HIL invariant via single-caller AST-walk + status-pending gate (apply_suggestion is sole library writer)"
    - "TDD: RED test commit → GREEN implementation commit × 3 (queue, tuning_loop, library_writer)"
    - "Post-write integrity assertion (reload + deep-compare non-eval_score keys — T-42-09 mitigation)"
    - "Atomic write: temp + os.replace + fsync + cleanup-in-except (T-42-13 mitigation)"
key-files:
  created:
    - path: plugins/platform_metrics/queue.py
      lines: 310
      exports: ["append_suggestion", "move_suggestion", "read_queue", "QUEUE_FILENAME", "APPLIED_FILENAME", "REJECTED_FILENAME"]
    - path: plugins/platform_metrics/tuning_loop.py
      lines: 285
      exports: ["TuningThresholds", "classify_metrics", "run_tuning_loop", "FeedbackStoreLike", "ExtensionStore"]
    - path: plugins/platform_metrics/library_writer.py
      lines: 256
      exports: ["SuggestionNotApprovedError", "load_formula_file", "write_formula_file", "apply_suggestion"]
    - path: plugins/platform_metrics/tests/test_queue.py
      lines: 362
      tests: 12
    - path: plugins/platform_metrics/tests/test_tuning_loop.py
      lines: 322
      tests: 13
    - path: plugins/platform_metrics/tests/test_library_writer.py
      lines: 392
      tests: 10
  modified: []
decisions:
  - "HIL invariant reframed to match schema: TuningSuggestion.status Literal is pending/applied/rejected (no 'approved' value). The plan brief's `status == 'approved'` gate was impossible. Reframed: the operator's 'approval' IS the act of calling apply_suggestion; the function requires status='pending' and refuses applied/rejected (double-apply guard)."
  - "Protocol-based decoupling (FeedbackStoreLike + ExtensionStore) instead of importing agent.feedback_store.FeedbackStore. Keeps tuning_loop.py free of v6.0 concrete-class imports (grep-enforced), testable with MagicMock, and forward-compatible if v6.0 classes evolve."
  - "Single-caller invariant AST-walk test (test_library_writer_is_only_caller_to_formula_library) — write_formula_file may only be called from apply_suggestion. Mirrors the v6.0 EVOL pattern that guards the gate-then-apply path."
  - "model_dump(mode='json') used in append_suggestion so MetricTrigger enum serializes to its string value (Pydantic v2 default is python mode which yields the enum object, not JSON-serializable)."
  - "Post-write integrity assertion in apply_suggestion reloads the file and deep-compares every non-eval_score key against the pre-write snapshot. Catches T-42-09 (tampering with non-eval_score fields) at runtime, not just via test."
  - "commit_sha = sha256(json.dumps(updated, ensure_ascii=False, sort_keys=True)). 64 hex chars. Deterministic regardless of dict insertion order. Simpler than git-style (no git dependency)."
metrics:
  duration: "~8min (506s)"
  completed: 2026-06-27T01:24:00Z
  tasks_completed: 3
  tasks_total: 3
  files_created: 6
  files_modified: 0
  tests_added: 35
  commits: 6
---

# Phase 42 Plan 03: formula_tuning_loop + JSONL Queue + library_writer Summary

**One-liner:** Plan 42-03 ships the DATA-03 feedback loop: `tuning_loop.py` classifies convergent PlatformMetrics via 4 MetricTrigger rules (HIGH_HOOK_DROPOFF / HIGH_COMPLETION_LOW_ENGAGEMENT / LOW_COMPLETION / LOW_SAVE_RATE) into TuningSuggestion records; `queue.py` persists them to a JSONL review queue mirroring v6.0 EVOL-02 (queue/applied/rejected with WR-02 atomic ordering + WR-03 audit-strict reads); `library_writer.py` performs the non-bypassable HIL-gated atomic eval_score write-back to `plugins/formula_library/library/*.json` — the only code path that touches formula files.

---

## Goal Achieved

DATA-03 fully closed. With Plan 42-01 (schema) + Plan 42-02 (adapter stubs) + this plan (tuning loop + queue + writer), the data-convergence chain is wired:

1. Platform adapter stubs (Plan 42-02) yield `PlatformMetrics` (Plan 42-01 schema).
2. `FeedbackRecordExtension` (Plan 42-01) composes the metrics per-variant.
3. **`run_tuning_loop`** (this plan) scans extensions → classifies via 4 trigger rules → emits `TuningSuggestion` records to `queue.jsonl`.
4. Operator reviews via `hermes formula stats` CLI (Plan 42-04, shipped in parallel).
5. **`apply_suggestion`** (this plan) is the HIL gate: requires `status="pending"`, locates the formula file via slugify convention, atomically writes ONLY `eval_score` (sha256 commit_sha + post-write integrity assertion), then moves the suggestion pending → applied.

**Non-bypassable HIL invariant** (load-bearing per execution_protocol): `apply_suggestion` is the sole entry point to formula file writes. An AST-walk test (`test_library_writer_is_only_caller_to_formula_library`) grep-enforces that `write_formula_file` is called only from `apply_suggestion`. Combined with the `SuggestionNotApprovedError` status gate, no auto-apply path exists.

---

## Tasks Completed

| Task | Name | RED commit | GREEN commit | Tests |
|------|------|------------|--------------|-------|
| 1 | queue.py — JSONL queue helpers | `3579ec2c3` | `f2c84684f` | 12 |
| 2 | tuning_loop.py — classify_metrics + run_tuning_loop + TuningThresholds | `e00d0f618` | `531a7bc11` | 13 |
| 3 | library_writer.py — apply_suggestion atomic eval_score write-back | `66597a1f3` | `b1ab8c7ed` | 10 |

**TDD cycle:** All 3 tasks followed strict RED → GREEN. Each RED commit ships the failing test file; each GREEN commit ships the implementation that flips them to passing. No REFACTOR pass needed — modules are 256-310 lines, single-responsibility.

**Total: 35/35 tests GREEN across 3 test files.**

---

## Tuning Rules (MetricTrigger — 4 rules)

| Trigger | Condition (default threshold) | observed_metric field | Action (中文) |
|---------|-------------------------------|------------------------|---------------|
| HIGH_HOOK_DROPOFF | `hook_dropoff_rate > 0.20` | `hook_dropoff_rate` | 加 hook 强度 (upgrade hook_pattern to emotional_peak / suspense) |
| HIGH_COMPLETION_LOW_ENGAGEMENT | `completion_rate >= 0.70 AND engagement_rate < 0.05` | `engagement_rate` | 加 CTA + 情绪爆点 (viewers finished but didn't interact) |
| LOW_COMPLETION | `completion_rate < 0.30` | `completion_rate` | 前置冲突 (front-load climax — video failed to retain) |
| LOW_SAVE_RATE | `save_rate < 0.01` | `save_rate` | 加 collectible 内容钩子 (add save-worthy content hooks) |

All thresholds parameterized via `TuningThresholds(high_hook_dropoff=..., high_completion=..., low_engagement=..., low_completion=..., low_save_rate=...)`. Operator can override any subset; defaults mirror plan spec.

---

## JSONL Queue Discipline (mirror v6.0 EVOL-02)

| File | Purpose | strict read? |
|------|---------|--------------|
| `queue.jsonl` | pending suggestions (one TuningSuggestion per line) | No (skip + log malformed) |
| `applied.jsonl` | approved + applied (with commit_sha + ts_applied) | Yes (raise on malformed — WR-03 audit) |
| `rejected.jsonl` | rejected (with reason + ts_rejected) | Yes (raise on malformed — WR-03 audit) |

- **append_suggestion**: rejects `status != "pending"` (ValueError)
- **move_suggestion**: WR-02 ordering — remove from queue.jsonl FIRST, then append to destination. Validates `commit_sha` for applied, `reason` for rejected.
- **read_queue**: deterministic sort by `ts_queued`; `formula_id` filter optional
- **_atomic_rewrite_jsonl**: temp + os.replace (POSIX atomic) + cleanup-in-except

Queue directory: `<HERMES_HOME>/skills/.feedback/tuning/` — does NOT collide with v6.0 `evolution/` dir.

---

## HIL Invariant (load-bearing)

**Schema constraint discovered:** `TuningSuggestion.status` is a 3-value Literal: `pending` / `applied` / `rejected`. There is NO `"approved"` value. The plan brief's HIL spec (`status == "approved"`) was impossible.

**Reframed HIL:** The operator's "approval" IS the act of calling `apply_suggestion`. The function:

1. **Status gate**: requires `status == "pending"`. Raises `SuggestionNotApprovedError` on `applied` / `rejected` (double-apply guard). [Check runs BEFORE any file mutation.]
2. **Single-caller invariant**: `write_formula_file` is called only from `apply_suggestion` (AST-walk-enforced). No other code path can touch `library/*.json`.
3. **Field-restrictive write**: only `eval_score` mutated. Post-write integrity assertion reloads + deep-compares all non-eval_score keys (T-42-09 mitigation).
4. **Atomic write**: temp + os.replace + fsync + cleanup-in-except (T-42-13 mitigation).

This satisfies the execution_protocol's "non-bypassable HIL" requirement: there is no auto-apply path. The tuning loop only emits; the operator must invoke `apply_suggestion` (via Plan 42-04 CLI) to complete the loop.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] model_dump(mode="json") for MetricTrigger serialization**
- **Found during:** Task 1 GREEN
- **Issue:** `TuningSuggestion.model_dump()` returns the `MetricTrigger` enum object in the dict (Pydantic v2 default is python mode), which is not JSON-serializable. `json.dumps()` raised `TypeError: Object of type MetricTrigger is not JSON serializable`.
- **Fix:** Use `record.model_dump(mode="json")` in `append_suggestion`. Enum serializes to its `.value` string.
- **Files modified:** `plugins/platform_metrics/queue.py`
- **Commit:** `f2c84684f`

**2. [Rule 1 — Bug] Plan verification grep too strict (`record_feedback` appears in docstrings)**
- **Found during:** Task 2 GREEN
- **Issue:** Plan's `<verification>` said `grep -c "record_feedback" plugins/platform_metrics/tuning_loop.py returns 0`. The forbidden identifier legitimately appears in docstrings/comments explaining the invariant (3 times). A bare-identifier grep is too broad.
- **Fix:** Test `test_run_tuning_loop_no_v6_write` greps for invocation patterns (`.record_feedback(`) and import statements (`from agent.feedback_store import`) — both are 0. The bare-identifier count is non-zero but only in documentation.
- **Files modified:** `plugins/platform_metrics/tests/test_tuning_loop.py`
- **Commit:** `531a7bc11`

**3. [Rule 1 — Bug] Plan brief / schema mismatch on HIL status value**
- **Found during:** Task 3 GREEN
- **Issue:** Plan brief (execution_protocol) said `apply_suggestion` refuses unless `suggestion.status == "approved"`. But `schema.py:TuningSuggestion.status` (shipped Plan 42-01) is `Literal["pending", "applied", "rejected"]` — no `"approved"` value. Plan 42-04 (parallel executor) independently discovered the same mismatch and logged it in `deferred-items.md`.
- **Fix:** Reframed the HIL semantics. The operator's "approval" IS the act of calling `apply_suggestion`. The function requires `status == "pending"` (so it can transition to applied via move_suggestion) and refuses `applied` / `rejected` (double-apply guard). `SuggestionNotApprovedError` raised on any non-pending status.
- **Files modified:** `plugins/platform_metrics/library_writer.py`, `plugins/platform_metrics/tests/test_library_writer.py`
- **Commit:** `b1ab8c7ed`

**4. [Rule 1 — Bug] `_seed_queue_with_pending` test helper needed for full-path tests**
- **Found during:** Task 3 GREEN
- **Issue:** Tests that exercise apply_suggestion's full path (no `move_suggestion` patch) reached the post-write `move_suggestion` call, which raised `KeyError` because the suggestion wasn't in `queue.jsonl`.
- **Fix:** Added `_seed_queue_with_pending(tuning_dir, suggestion)` helper that appends a pending clone of the suggestion to `queue.jsonl` before apply_suggestion is invoked. Mirrors real lifecycle: tuning_loop emits pending → operator apply transitions to applied.
- **Files modified:** `plugins/platform_metrics/tests/test_library_writer.py`
- **Commit:** `b1ab8c7ed`

---

**Total deviations:** 4 auto-fixed (all Rule 1 bugs — schema/serialization/test-strictness issues discovered during GREEN implementation). Zero scope creep. Zero architectural changes (Rule 4 would have applied if the schema needed a new status value; it didn't — the reframing fits the existing 3-value Literal).

---

## Threat Model Compliance

| Threat ID | Category | Status | Verification |
|-----------|----------|--------|--------------|
| T-42-09 | Tampering (non-eval_score fields) | mitigated | Runtime post-write integrity assertion in `apply_suggestion` reloads + deep-compares all non-eval_score keys. `test_apply_suggestion_preserves_other_fields` covers field-level equality; runtime raises `RuntimeError` on drift. |
| T-42-10 | Repudiation (JSONL audit trail) | mitigated | `read_queue` strict mode for applied/rejected (WR-03 mirror). `test_strict_mode_on_applied` covers malformed-line rejection. WR-02 remove-then-append ordering in `move_suggestion`. |
| T-42-11 | Elevation of Privilege (auto-apply) | mitigated | `SuggestionNotApprovedError` on non-pending status + AST-walk single-caller invariant. No auto-invocation path. |
| T-42-12 | Information Disclosure (FeedbackStore query) | accept | tuning_loop uses `feedback_store.query` parameter (kept for future use); current implementation iterates extensions directly. No content logging. |
| T-42-13 | Tampering (atomic write failure) | mitigated | `write_formula_file` uses temp + os.replace + cleanup-in-except. `test_apply_suggestion_atomic_temp_cleanup_on_failure` monkeypatches os.replace to raise OSError and asserts no `.formula.*.tmp` leftover. |
| T-42-SC | Tampering (package install) | accept | N/A — pure stdlib (json, hashlib, logging, os, tempfile, dataclasses, typing, pathlib, datetime). No pip installs. |

---

## Scope Discipline Verification

| Check | Result |
|-------|--------|
| `grep -cE "from agent\\.(feedback_schema\\|feedback_store\\|evolution)" plugins/platform_metrics/queue.py` | 0 ✓ |
| `grep -cE "from agent\\.(feedback_schema\\|feedback_store\\|evolution)" plugins/platform_metrics/tuning_loop.py` | 0 ✓ |
| `grep -cE "from agent\\.(feedback_schema\\|feedback_store\\|evolution)" plugins/platform_metrics/library_writer.py` | 0 ✓ |
| `grep -cE "\\.record_feedback\\s*\\(" plugins/platform_metrics/tuning_loop.py` | 0 ✓ (invocation pattern; bare identifier appears 3× in docstrings only) |
| Files modified under `agent/` | 0 ✓ |
| Files modified under `hermes_cli/` | 0 ✓ |
| Files modified under `skills/` | 0 ✓ |
| Files modified under `plugins/formula_library/` | 0 ✓ (library files are write TARGETS at runtime, not source-modified) |
| Files modified outside `plugins/platform_metrics/` | 0 ✓ |
| Sibling files leaked into Plan 42-03 commits (git race) | 0 ✓ (verified via `git show --stat` after each commit) |

---

## Self-Check: PASSED

**Files verified to exist:**
- [x] `plugins/platform_metrics/queue.py` — FOUND (310 lines, exports `append_suggestion` / `move_suggestion` / `read_queue`)
- [x] `plugins/platform_metrics/tuning_loop.py` — FOUND (285 lines, exports `TuningThresholds` / `classify_metrics` / `run_tuning_loop`)
- [x] `plugins/platform_metrics/library_writer.py` — FOUND (256 lines, exports `SuggestionNotApprovedError` / `load_formula_file` / `write_formula_file` / `apply_suggestion`)
- [x] `plugins/platform_metrics/tests/test_queue.py` — FOUND (362 lines, 12 tests)
- [x] `plugins/platform_metrics/tests/test_tuning_loop.py` — FOUND (322 lines, 13 tests)
- [x] `plugins/platform_metrics/tests/test_library_writer.py` — FOUND (392 lines, 10 tests)

**Commits verified:**
- [x] `3579ec2c3` — FOUND (`test(42-03): add failing tests for JSONL tuning queue (RED)`)
- [x] `f2c84684f` — FOUND (`feat(42-03): JSONL queue for formula tuning suggestions (GREEN)`)
- [x] `e00d0f618` — FOUND (`test(42-03): add failing tests for tuning_loop + classify_metrics (RED)`)
- [x] `531a7bc11` — FOUND (`feat(42-03): formula tuning loop with classify_metrics + run_tuning_loop (GREEN)`)
- [x] `66597a1f3` — FOUND (`test(42-03): add failing tests for library_writer atomic write-back (RED)`)
- [x] `b1ab8c7ed` — FOUND (`feat(42-03): atomic library_writer with HIL-gated apply_suggestion (GREEN)`)

**Test suite verified:**
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_queue.py` — 12 passed in 0.11s
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_tuning_loop.py` — 13 passed in 0.12s
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_library_writer.py` — 10 passed in 0.14s
- [x] Combined: 35/35 passed in 0.15s
- [x] Plan 42-01/42-02 regression: 94/94 passed (queue + tuning_loop + library_writer + schema + adapter_base + adapters)

**Verification commands (from plan `<verification>` section):**
- [x] All 3 test files pass — 35 passed
- [x] `.record_feedback(` invocation pattern in tuning_loop.py — 0 matches (bare identifier appears 3× in docstrings only — explained in Deviation #2)
- [x] `updated["eval_score"]` is the ONLY dict-mutation in library_writer.py — verified via grep
- [x] JSONL queue path `tuning/` does NOT collide with v6.0 `evolution/` — verified (different dir name constant)

---

## Cross-Plan Coordination

**Plan 42-04 (parallel executor)** independently discovered the HIL/schema mismatch (Deviation #3 above) and logged it in `.planning/phases/42-data-convergence/deferred-items.md`. Their root-cause analysis matches mine exactly. Plan 42-03's GREEN implementation (commit `b1ab8c7ed`) resolves all 6 failures Plan 42-04 flagged. The `deferred-items.md` entry can be marked resolved once Plan 42-03 merges.

---

*Plan 42-03 executed: 2026-06-27 — 3/3 tasks complete, 35/35 tests GREEN, 6 commits (3 RED + 3 GREEN), DATA-03 closed.*
