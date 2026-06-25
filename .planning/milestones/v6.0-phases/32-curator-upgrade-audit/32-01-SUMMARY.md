---
phase: 32-curator-upgrade-audit
plan: 01
subsystem: curator-audit-evol02
tags: [curator, audit, evolution, evol02, regression, feedback-scan, runtime-isolation]
requires:
  - P29-FeedbackStore (FeedbackStore._index["buckets"] iteration, query API)
  - P31-evolution (aggregate_feedback, append_patch, apply_patch_transaction, InsightRecord)
  - P31-TestNonBypassableHumanInLoop (structural invariant preserved)
provides:
  - agent/curator_audit.py (sha256-chained JSONL audit log: append/verify/read)
  - agent/evolution/evol02_generator.py (multi-instruction bilingual diff generator)
  - agent/curator.py feedback-scan phase (additive CURATE-01/02/03 extension)
  - PatchRecord.auto_apply_eligible + confidence_score additive fields
  - SC-6 regression coverage (tests/agent/test_curator_regression.py)
affects:
  - agent/curator.py (run_curator_review + _llm_pass extended additively)
  - agent/evolution/queue.py (PatchRecord schema — backward-compat defaults)
  - agent/evolution/__init__.py (re-exports evol02 symbols)
  - cli-config.yaml.example (feedback.curator.* documented)
tech-stack:
  added:
    - "stdlib hashlib (sha256 chain)"
    - "stdlib difflib (unified_diff for EVOL-02 multi-instruction)"
    - "stdlib json + uuid (audit log entries)"
  patterns:
    - "Build-final-state-then-diff-once (EVOL-02 multi-instruction same-file)"
    - "Lazy imports inside function body (runtime isolation — agent.evolution forbidden at module level)"
    - "Additive-only extension (pre-v6 curator behavior byte-unchanged — SC-6)"
    - "Two-signal confidence gate (mean_delta + evidence_count — CURATE-05)"
    - "sha256 chain tamper detection (prev_sha256 prefix binds entries)"
key-files:
  created:
    - agent/curator_audit.py
    - agent/evolution/evol02_generator.py
    - tests/agent/test_curator_regression.py
    - tests/agent/test_audit_log.py
    - tests/agent/test_curator_feedback_scan.py
    - tests/agent/evolution/test_evol02_generator.py
    - tests/fixtures/curator/audit_chain_valid.jsonl
    - tests/fixtures/curator/audit_chain_tampered.jsonl
    - tests/fixtures/curator/feedback_scenarios.json
  modified:
    - agent/curator.py
    - agent/evolution/queue.py
    - agent/evolution/__init__.py
    - cli-config.yaml.example
decisions:
  - "Audit log at agent/curator_audit.py (NOT agent/evolution/audit.py) because agent/curator.py IS runtime and imports it; P31 invariant forbids agent/evolution/ imports by runtime"
  - "EVOL-02 build-final-state-then-diff-once approach handles multi-instruction same-file anchor offset shifts correctly"
  - "Idempotent guard strengthened to check block already present at insertion site (not just full-line-set equality)"
  - "FeedbackStore constructed via hermes_home kwarg (not root) — matches actual P29 __init__ signature"
  - "Lazy imports patched via agent.evolution package namespace (not underlying modules) because _feedback_scan_phase uses `from agent.evolution import X` which binds from __init__"
metrics:
  duration: 17m 6s
  completed: 2026-06-25
  tasks: 4
  tests_added: 55
  files_created: 9
  files_modified: 4
---

# Phase 32 Plan 01: Curator Upgrade + Audit Engine Summary

SC-6 pre-v6 curator regression coverage, tamper-evident sha256-chained audit log, EVOL-02 multi-instruction bilingual diff generator, and additive feedback-scan phase wired into run_curator_review — all preserving P31 structural invariants and runtime isolation.

## What Shipped

### Task 1: SC-6 Regression Test (written FIRST)
- **5 tests** in `tests/agent/test_curator_regression.py` locking in pre-v6 curator behavior
- Baseline counts documented in module docstring (`{"marked_stale": 0, "archived": 1, "reactivated": 0, "checked": 1, "seeded": 0}` for a 120-day-idle skill)
- `test_consolidate_false_skips_llm_and_scan` uses `hasattr` guard for the TDD contract — soft RED until Task 4, then GREEN
- `test_scan_phase_is_additive_append` verifies scan never mutates `auto_transitions`

### Task 2: Audit Log Module (`agent/curator_audit.py`)
- **GENESIS_PREV_SHA256** = `sha256(b"").hexdigest()` = `e3b0c44...b855` (documented literal)
- **`_serialize_entry_for_sha256`** central helper (Pitfall #2 mitigation) — `ensure_ascii=False` pinned in both append and verify paths (Pitfall #8)
- **`append_audit`** — uuid4 entry_id, ISO-8601 UTC ts, sha256 chain; raises `AuditChainError` on corrupt tail
- **`verify_chain`** — enumerates ALL breaks (prev_sha256 mismatch + entry_sha256 recompute mismatch); does NOT stop at first
- **`read_audit`** — filters by action/since/skill
- **2 fixtures**: `audit_chain_valid.jsonl` (3-entry propose→apply→rollback) and `audit_chain_tampered.jsonl` (middle entry action mutated)
- **21 tests** covering genesis, serialization, append/chaining, tamper detection (prev mismatch, interior deletion, action mutation), filtering, CN round-trip

### Task 3: EVOL-02 Generator (`agent/evolution/evol02_generator.py`)
- **`_compose_bilingual_block`** — EN heading + body, blank line, CN heading + body (CLAUDE.md convention)
- **`generate_patch_from_knowledge_point`** — build-final-state-then-diff-once approach for multi-instruction same-file patches; multi-file joins per-file diffs with `"\n"`
- **`_validate_anchor`** — reuses `_frontmatter_end_offset` from `diff_generator.py` (Pitfall #3 — frontmatter immutable); rejects missing/duplicate anchors
- **Idempotent guard** — detects block already present at insertion site (strengthened from P31's full-line-set equality check)
- **`emit_evol02_instructions`** — SEPARATE LLM pass (does NOT modify P31 `aggregate_feedback`); `response_format` retry; `AggregationError` on malformed JSON/missing keys
- **`__init__.py` re-exports**: `generate_patch_from_knowledge_point`, `emit_evol02_instructions`, `_compose_bilingual_block`, `EVOL02_SYSTEM_PROMPT`
- **16 tests** including integration with P31 `apply_patch_transaction` on a real git repo

### Task 4: Feedback-Scan Phase + Propose/Audit Wiring
- **`agent/evolution/queue.py` PatchRecord** extended additively: `auto_apply_eligible: bool = False`, `confidence_score: dict | None = None` (defaults preserve P31 behavior — 14 existing queue tests green)
- **`agent/curator.py` feedback config**: `_load_feedback_config` + 5 getters (`feedback_threshold_count=3`, `feedback_threshold_sessions=2`, `auto_apply_enabled=false`, `auto_apply_min_delta=0.1`, `auto_apply_min_evidence=3`)
- **`_scan_for_hot_skills`** — iterates `store._index["buckets"]` keys (Pitfall #4 — no `list_skill_ids`); sums neg counts across sources; distinct UTC days from `record.ts.date()` as session proxy (Open Q #1 RESOLVED — FeedbackRecord has no `session_id` field)
- **`_compute_confidence`** — two-signal gate (mean_delta + evidence_count)
- **`_feedback_scan_phase`** — ADDITIVE phase appended to `_llm_pass` after `save_state(state2)` in BOTH branches (consolidate=True and consolidate=False early-return); ALL `agent.evolution.*` imports LAZY inside the function body (runtime isolation preserved); try/except wraps the whole body (T-32-03: scan failure never aborts curator); bundled NEVER `auto_apply_eligible=True` (T-32-05); logs `append_audit(action="propose")` for every patch
- **`cli-config.yaml.example`** — documented `feedback.curator.*` block
- **13 tests**: threshold detection (count/sessions/good-verdict exclusion), propose wiring (aggregate→emit→generate→append_patch→append_audit), scan failure isolation, bundled-never-auto, confidence scoring, config getters

## Verification Results

All 8 plan verification commands pass:
1. `pytest tests/agent/test_curator_regression.py tests/agent/test_audit_log.py tests/agent/test_curator_feedback_scan.py tests/agent/evolution/test_evol02_generator.py` → **55 passed**
2. `pytest tests/agent/test_curator*.py tests/agent/evolution/` → **246 passed**
3. `pytest tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop` → **2 passed** (P31 structural invariant preserved)
4. `ruff check` on all 5 modified/new source files → **All checks passed**
5. `grep -c "^from agent.evolution\|^import agent.evolution" agent/curator.py` → **0** (runtime isolation — lazy imports inside function body only)
6. `grep -c "apply_patch_transaction" agent/curator.py agent/curator_audit.py agent/evolution/evol02_generator.py` → **0, 0, 1** (the 1 is a docstring `:func:` cross-reference, NOT a call)
7. FOUND-08 byte-intact: `git diff --name-only HEAD -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` → **0**
8. `grep -c "encoding=" agent/curator_audit.py agent/evolution/evol02_generator.py` matches open() count (PLW1514 clean)

**Full P28-P31 regression**: 387 passed, 1 skipped (pre-existing openai-missing skip). Zero regressions.

## Resolved Open Questions

**Open Question #1 (FeedbackRecord.session_id):** ABSENT from schema (verified in `agent/feedback_schema.py`). RESOLVED → use **distinct UTC calendar days** derived from `record.ts.date()` as the session-diversity proxy. Documented in `_scan_for_hot_skills` docstring. This is an approximation (two feedback records on the same day from different actual sessions count as one "session") — documented for reviewability.

**Open Question #2 (EVOL-02 LLM call):** SEPARATE pass (`emit_evol02_instructions` in `evol02_generator.py`) — does NOT modify P31's `aggregate_feedback`. Avoids P31 regression risk.

**Open Question #3 (propose action logging):** YES — `_feedback_scan_phase` logs every propose via `append_audit(action="propose", ...)`. Operator filters via `--action apply` in Plan 02.

## PatchRecord Additive Extension

`agent/evolution/queue.py:PatchRecord` extended with two optional fields AFTER `ts_rejected`:
- `auto_apply_eligible: bool = False` — CURATE-05 marker; Plan 02 CLI may flip for agent-created skills after confidence check; bundled NEVER
- `confidence_score: dict[str, Any] | None = None` — shape `{"mean_delta": float, "evidence_count": int, "reason": str}`

Defaults preserve P31 behavior — all 14 existing `test_queue.py` tests pass unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] EVOL-02 idempotent guard strengthened**
- **Found during:** Task 3
- **Issue:** The plan-specified idempotent guard (`working == original_lines`) only triggers when the full line set is unchanged. But the generator always adds lines, so the guard never fires when re-running the same instruction against an already-patched file.
- **Fix:** Added a check that compares the block lines to the existing lines immediately after the anchor — raises `ValueError` if the block is already present at the insertion site.
- **Files modified:** `agent/evolution/evol02_generator.py`
- **Commit:** a30095668

**2. [Rule 1 - Bug] FeedbackStore constructor kwarg corrected**
- **Found during:** Task 4
- **Found during:** Task 4
- **Issue:** Plan referenced `FeedbackStore(root=...)` but the actual P29 signature is `FeedbackStore(hermes_home=...)`.
- **Fix:** Used `hermes_home=get_hermes_home()` in `_feedback_scan_phase` and `hermes_home=home` in test helper.
- **Files modified:** `agent/curator.py`, `tests/agent/test_curator_feedback_scan.py`
- **Commit:** 395bf60d9

**3. [Rule 3 - Blocking] Test mock patch target corrected**
- **Found during:** Task 4
- **Issue:** Monkeypatching `evol_insights.make_aggregation_client` did not affect the lazy import `from agent.evolution import make_aggregation_client` inside `_feedback_scan_phase` (the symbol is bound from `__init__.py`'s namespace at import time).
- **Fix:** Patched `agent.evolution` package namespace directly (`monkeypatch.setattr(evol_pkg, "make_aggregation_client", ...)`).
- **Files modified:** `tests/agent/test_curator_feedback_scan.py`
- **Commit:** 395bf60d9

No authentication gates, no Rule 4 architectural changes, no deferred issues.

## Known Stubs

None. All functions are fully implemented — no placeholder values, no TODO markers, no unwired data paths.

## Threat Flags

None. All threats in the plan's `<threat_model>` are mitigated as specified:
- T-32-01 (audit tampering) → sha256 chain + verify_chain
- T-32-02 (LLM injection) → additive-only + frontmatter guard + FOUND-08 + human-in-loop
- T-32-03 (scan crashes abort curator) → try/except wrapper + test
- T-32-04 (FeedbackStore API misuse) → iterate `_index["buckets"]` directly
- T-32-05 (bundled auto-apply) → `auto_apply_eligible=False` always for bundled + test
- T-32-06 (sha256 serialization drift) → central `_serialize_entry_for_sha256` helper
- T-32-07 (LLM non-determinism) → idempotent propose (strengthened guard)
- T-32-08 (bilingual style violation) → `_compose_bilingual_block` enforces EN+CN format

## Self-Check: PASSED

**Files created (verified to exist):**
- FOUND: agent/curator_audit.py
- FOUND: agent/evolution/evol02_generator.py
- FOUND: tests/agent/test_curator_regression.py
- FOUND: tests/agent/test_audit_log.py
- FOUND: tests/agent/test_curator_feedback_scan.py
- FOUND: tests/agent/evolution/test_evol02_generator.py
- FOUND: tests/fixtures/curator/audit_chain_valid.jsonl
- FOUND: tests/fixtures/curator/audit_chain_tampered.jsonl
- FOUND: tests/fixtures/curator/feedback_scenarios.json

**Commits (verified in git log):**
- FOUND: add82e932 (test 32-01: SC-6 regression)
- FOUND: e957a634b (feat 32-01: audit log)
- FOUND: a30095668 (feat 32-01: EVOL-02 generator)
- FOUND: 395bf60d9 (feat 32-01: feedback-scan phase)

**Test counts:**
- Task 1: 5 tests (test_curator_regression.py)
- Task 2: 21 tests (test_audit_log.py)
- Task 3: 16 tests (test_evol02_generator.py)
- Task 4: 13 tests (test_curator_feedback_scan.py)
- **Total new: 55 tests, all green**
- **Regression: 387 passed, 1 skipped (P28-P31 full suite)**
