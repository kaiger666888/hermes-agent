---
phase: 32-curator-upgrade-audit
verified: 2026-06-25T00:55:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 32: Curator Upgrade + Audit Verification Report

**Phase Goal:** The Curator (currently limited to archiving agent-created skills) gains the ability to scan accumulated feedback, produce candidate patches against bundled movie-expert skills via the EVOL-02 generator, log every action to a tamper-evident audit trail, and expose operator CLI commands for queue management — with a semi-automatic path for high-confidence agent-created skill patches.

**Verified:** 2026-06-25T00:55:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth (SC) | Status | Evidence |
|---|------------|--------|----------|
| SC-1 | `run_curator_review` extended — bundled skill crosses threshold (≥3 neg across ≥2 distinct UTC days) triggers EVOL pipeline, patches land in P31 queue | ✓ VERIFIED | `agent/curator.py:1681` `_feedback_scan_phase`; lazy imports at lines 1729-1739 (`from agent.evolution import …`, `from agent.evolution.queue import PatchRecord`, `from agent.curator_audit import append_audit`); `tests/agent/test_curator_feedback_scan.py` → **14 passed**; runtime isolation preserved (0 module-level `from agent.evolution` imports in `agent/curator.py`). |
| SC-2 | EVOL-02 candidate-patch generator (knowledge point → unified diff, bilingual EN+CN) | ✓ VERIFIED | `agent/evolution/evol02_generator.py:generate_patch_from_knowledge_point` + `_compose_bilingual_block` (EN heading+body / blank / CN heading+body) + `emit_evol02_instructions` (separate LLM pass). `__init__.py:33-35,67-69` re-exports all three symbols. `tests/agent/evolution/test_evol02_generator.py` → **17 passed** incl. `TestDiffAppliesClean` integration with `apply_patch_transaction`. |
| SC-3 | Audit trail at `~/.hermes/skills/.audit/log.jsonl` — sha256-chained, append-only, queryable, operator/ts/feedback IDs/eval score/commit sha | ✓ VERIFIED | `agent/curator_audit.py:97` `_audit_log_path()` returns `get_hermes_home() / "skills" / ".audit" / "log.jsonl"`; `GENESIS_PREV_SHA256 = hashlib.sha256(b"").hexdigest()` (verified = `e3b0c44...b855`); `append_audit`/`verify_chain`/`read_audit`/`AuditChainError` exported. `tests/agent/test_audit_log.py` + `tests/hermes_cli/test_curator_cli.py::TestAuditLogCmd` → **31 passed** incl. `test_tampered_fixture_detects_break`, `test_prev_sha256_mismatch_on_edit`, `test_interior_deletion_breaks_chain`. |
| SC-4 | `hermes curator queue\|approve\|reject` work end-to-end against audit-backed queue | ✓ VERIFIED | `hermes_cli/curator.py:register_cli` extended with 5 subparsers (queue/approve/reject/audit-log/auto-apply-eligible). `_cmd_queue`→`_cmd_review_queue`, `_cmd_approve_curator`→`_cmd_approve`, `_cmd_reject_curator`→`_cmd_reject` (delegation). `_cmd_approve` in `hermes_cli/feedback.py:975` calls `append_audit(action="apply", …)` after successful `move_patch`. `tests/hermes_cli/test_curator_cli.py` → **36 passed** incl. `TestDelegation`, `TestAuditAppendBestEffort`. |
| SC-5 | Agent-created skills semi-automatic path (gate AND confidence ≥ threshold); globally toggleable; bundled NEVER auto | ✓ VERIFIED | `hermes_cli/curator.py:671` `_cmd_auto_apply_eligible`: 4-gate filter — (1) `get_auto_apply_enabled()` config gate [default OFF in `cli-config.yaml.example:556`], (2) `p.auto_apply_eligible` flag, (3) `is_agent_created(p.skill_id)` recheck [defense-in-depth, bundled NEVER], (4) two-signal `mean_delta >= min_delta AND evidence_count >= min_evidence`. CR-01 fix wired producer at `hermes_cli/feedback.py:695-698` (only agent-created + gate-pass + signals-pass sets the flag). `tests/hermes_cli/test_curator_cli.py::TestAutoApplyCmd` + `tests/hermes_cli/test_evolution_cli.py::TestEvolveCmdAutoApplyEligible` → **11 passed**. |
| SC-6 | Pre-v6 deterministic inactivity transitions + consolidation pass unchanged (regression) | ✓ VERIFIED | `tests/agent/test_curator_regression.py` → **5 passed**: `test_inactivity_transitions_unchanged`, `test_consolidate_false_skips_llm_and_scan`, `test_dry_run_no_state_mutation`, `test_no_feedback_no_scan`, `test_scan_phase_is_additive_append`. Extension is ADDITIVE — scan phase appended in `_llm_pass` after `save_state(state2)`; pre-v6 counts preserved byte-for-byte. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent/curator_audit.py` | sha256-chained JSONL append/verify/read + AuditChainError + GENESIS_PREV_SHA256 | ✓ VERIFIED | 16 KB; 5 public symbols exported; both `open()` calls have `encoding="utf-8"` (lines 148, 231); `os.fsync` after write (WR-01 fix). |
| `agent/evolution/evol02_generator.py` | multi-instruction bilingual diff generator extending P31 placeholder | ✓ VERIFIED | 18 KB; `generate_patch_from_knowledge_point` + `emit_evol02_instructions` + `_compose_bilingual_block`; reuses `from agent.evolution.diff_generator import generate_additive_diff, _frontmatter_end_offset`; build-final-state-then-diff-once approach. |
| `agent/curator.py` (extended) | `_feedback_scan_phase` additive phase + config getters + `_compute_confidence` | ✓ VERIFIED | Function at line 1681; lazy imports inside body at 1729-1739; 5 config getters mirror existing pattern; wraps body in narrowed try/except (WR-05 fix). |
| `agent/evolution/queue.py` (PatchRecord extended) | `auto_apply_eligible: bool = False` + `confidence_score: dict \| None = None` additive | ✓ VERIFIED | Fields at lines 116, 120; defaults preserve P31 behavior (14 existing queue tests still pass). |
| `agent/evolution/__init__.py` (re-exports) | re-export evol02 symbols | ✓ VERIFIED | Lines 33-35 (import), 67-69 (`__all__`). |
| `hermes_cli/curator.py` (extended) | 5 new subparsers + handlers | ✓ VERIFIED | `register_cli` extended; `_cmd_queue`/`_cmd_approve_curator`/`_cmd_reject_curator`/`_cmd_audit_log`/`_cmd_auto_apply_eligible`; `_get_operator` + `_resolve_skill_from_patch` helpers. |
| `hermes_cli/feedback.py` (extended) | `_cmd_approve` calls `append_audit(action="apply")` + producer sets `auto_apply_eligible` (CR-01) | ✓ VERIFIED | Audit call at line 975 inside try/except WARNING (best-effort); producer wiring at lines 695-698. |
| `tests/agent/test_curator_regression.py` | SC-6 coverage (min 80 lines) | ✓ VERIFIED | 10 KB, 5 tests, baseline counts documented. |
| `tests/agent/test_audit_log.py` | audit log unit coverage | ✓ VERIFIED | 13 KB, 24 tests across TestAppendAudit/TestVerifyChain/TestReadAudit. |
| `tests/agent/evolution/test_evol02_generator.py` | EVOL-02 coverage incl. apply integration (min 150 lines) | ✓ VERIFIED | 20 KB, 17 tests incl. TestDiffAppliesClean. |
| `tests/agent/test_curator_feedback_scan.py` | threshold detection + propose/audit wiring (min 150 lines) | ✓ VERIFIED | 20 KB, 14 tests. |
| `tests/hermes_cli/test_curator_cli.py` | CLI smoke + auto-apply + delegation (min 200 lines) | ✓ VERIFIED | 35 KB, 36 tests across 8 classes. |
| `tests/fixtures/curator/audit_chain_valid.jsonl` | 3-entry valid chain (propose→apply→rollback) | ✓ VERIFIED | 1.2 KB; `test_valid_fixture_no_breaks` passes. |
| `tests/fixtures/curator/audit_chain_tampered.jsonl` | tampered middle entry | ✓ VERIFIED | 1.2 KB; `test_tampered_fixture_detects_break` passes. |
| `tests/fixtures/curator/feedback_scenarios.json` | 3 scenarios (below/above threshold + bundled) | ✓ VERIFIED | 2 KB. |
| `cli-config.yaml.example` (extended) | `feedback.curator.*` block documented | ✓ VERIFIED | Lines 528-562; `auto_apply_enabled: false` default explicit. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `agent/curator.py:_llm_pass` (after `save_state(state2)`) | `agent.curator_audit.append_audit(action="propose")` | lazy import inside `_feedback_scan_phase` try/except | ✓ WIRED | Confirmed at lines 1738 (`from agent.curator_audit import append_audit`), invoked in body; wrapped in caller try/except. |
| `agent/curator.py:_feedback_scan_phase` | `agent.evolution.aggregate_feedback` + `append_patch` | lazy imports inside function body only | ✓ WIRED | Lines 1730-1737 (`from agent.evolution import …`); 0 module-level imports (runtime isolation preserved). |
| `agent/evolution/evol02_generator.py:generate_patch_from_knowledge_point` | `agent.evolution.diff_generator.generate_additive_diff` | reuse via import | ✓ WIRED | `_frontmatter_end_offset` imported and used in `_validate_anchor`; build-final-state-then-diff-once approach emits `difflib.unified_diff`. |
| `hermes_cli/curator.py:_cmd_approve_curator` | `hermes_cli/feedback.py:_cmd_approve` | direct function call | ✓ WIRED | Thin-wrapper delegation; `TestDelegation::test_approve_delegates_to_p31` confirms. |
| `hermes_cli/feedback.py:_cmd_approve` (after `move_patch`) | `agent.curator_audit.append_audit(action="apply")` | lazy import + try/except WARNING | ✓ WIRED | Line 973 lazy import, line 975 call; `TestAuditAppendBestEffort` verifies failure does not block apply. |
| `hermes_cli/curator.py:_cmd_auto_apply_eligible` | `_cmd_approve` per patch (Option A) | argparse.Namespace patch with `yes=True` | ✓ WIRED | NEVER calls `apply_patch_transaction` directly; P31 `TestNonBypassableHumanInLoop` passes UNCHANGED. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|---|
| `_feedback_scan_phase` | hot skills list | `store._index["buckets"]` keys + `store.query()` for distinct UTC days | Real FeedbackStore data (not hardcoded) | ✓ FLOWING |
| `generate_patch_from_knowledge_point` | unified_diff string | `emit_evol02_instructions` LLM output + `current_files` | Real diff via `difflib.unified_diff` (integration test `TestDiffAppliesClean`) | ✓ FLOWING |
| `append_audit` | entry_sha256 | sha256 chain over real entry fields | Real hash computation (tamper detection verified) | ✓ FLOWING |
| `_cmd_auto_apply_eligible` | eligible patches | `read_queue(status="pending")` + flag/confidence filters | Real queue scan; CR-01 producer at `hermes_cli/feedback.py:695-698` sets `auto_apply_eligible=True` end-to-end | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| SC-1..SC-6 test suites green | `python3 -m pytest tests/agent/test_curator*.py tests/agent/test_audit_log.py tests/agent/evolution/test_evol02_generator.py tests/hermes_cli/test_curator_cli.py` | 98 passed | ✓ PASS |
| P31 structural invariant (Option A) | `python3 -m pytest tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop` | 2 passed UNCHANGED | ✓ PASS |
| P28-P31 regression (feedback/insights/queue/apply/evolution-cli) | `python3 -m pytest tests/agent/test_feedback_store.py tests/agent/test_feedback_schema.py tests/agent/evolution/ tests/hermes_cli/test_evolution_cli.py` | 176 passed | ✓ PASS |
| Combined Phase 32 + P31 regression | broad pytest invocation | 339 passed | ✓ PASS |
| CR-01 producer regression | `python3 -m pytest tests/hermes_cli/test_evolution_cli.py::TestEvolveCmdAutoApplyEligible` | 3 passed | ✓ PASS |
| Audit chain tamper detection | `python3 -m pytest tests/agent/test_audit_log.py -k "tampered or valid or chain"` | 11 passed | ✓ PASS |

### Probe Execution

Step 7c SKIPPED — Phase 32 declares no `scripts/*/tests/probe-*.sh` probes; verification is pytest-driven per the plan's `<verification>` blocks (all 8 verification commands per plan ran green, see Behavioral Spot-Checks).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CURATE-01 | 32-01 | Extend curator to propose bundled-skill patches (human-in-loop gate) | ✓ SATISFIED | `_feedback_scan_phase` proposes bundled patches via EVOL pipeline; bundled patches always `auto_apply_eligible=False` and require operator `_cmd_approve`; tests in `test_curator_feedback_scan.py::TestProposeHotBundledSkill`. |
| CURATE-02 | 32-01 | Auto-trigger EVOL on negative-feedback threshold (≥3 neg across ≥2 sessions) | ✓ SATISFIED | `_scan_for_hot_skills` implements threshold via `_index["buckets"]` iteration + distinct UTC days session proxy; `get_feedback_threshold_count=3`, `get_feedback_threshold_sessions=2` defaults; `TestThresholdDetection` tests. |
| CURATE-03 | 32-01 | `~/.hermes/skills/.audit/` tamper-evident log with operator/ts/feedback IDs/eval score/commit sha | ✓ SATISFIED | `agent/curator_audit.py` + path at line 97; sha256 chain; `append_audit` signature includes operator/feedback_ids/eval_score/commit_sha; `verify_chain` detects tampering. |
| CURATE-04 | 32-02 | `hermes curator queue/approve/reject` CLI | ✓ SATISFIED | 3 subparsers + audit-log wired via delegation to P31 handlers; `TestQueueCmd`/`TestApproveCmdCurator`/`TestRejectCmdCurator`/`TestDelegation` confirm. |
| CURATE-05 | 32-02 | Agent-created semi-automatic path (confidence ≥ threshold, toggleable, bundled NEVER) | ✓ SATISFIED | Two-signal confidence (mean_delta ≥ 0.1 AND evidence_count ≥ 3); `auto_apply_enabled` config default OFF; bundled NEVER via `is_agent_created` recheck; CR-01 fix wired producer at `hermes_cli/feedback.py:695-698`. NOTE: ROADMAP says "default 0.8" but CONTEXT.md + plan LOCKED two-signal definition (mean_delta=0.1, evidence_count=3); LOCKED definition implemented and tested — see Override Note below. |
| EVOL-02 | 32-01 | Unified-diff patch generator preserving bilingual structure | ✓ SATISFIED | `generate_patch_from_knowledge_point` + `_compose_bilingual_block` enforce EN+CN format; `__init__.py` re-exports; 17 tests incl. integration with `apply_patch_transaction`. |

**Override Note (CURATE-05 threshold):** ROADMAP.md line 112 states "confidence ≥ 0.8" but `.planning/phases/32-curator-upgrade-audit/32-CONTEXT.md` §"Confidence Score for Auto-Apply (CURATE-05)" LOCKED the operationalization as a two-signal gate (`mean_delta >= 0.1 AND evidence_count >= 3`), which is what 32-01-PLAN, 32-02-PLAN, the implementation, the tests, and cli-config.yaml.example all consistently implement. The LOCKED two-signal definition is the authoritative operationalization; the "0.8" in ROADMAP is pre-operationalization prose. Treating as VERIFIED (no override entry needed because the deviation is internal-derivation-from-locked-context, not a missed SC).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | No TBD/FIXME/XXX/PLACEHOLDER markers in any Phase 32 modified file | ℹ️ Info | Clean. |

`grep -nE "TBD|FIXME|XXX|PLACEHOLDER"` on `agent/curator_audit.py`, `agent/evolution/evol02_generator.py`, `agent/curator.py`, `hermes_cli/curator.py`, `hermes_cli/feedback.py` returned zero matches. No blocker debt markers.

### Structural Invariants Preserved

| Invariant | Verification | Result |
|-----------|--------------|--------|
| FOUND-08 byte-intact (no bundled SKILL.md changes vs v5.0) | `git diff --name-only HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` | **0** ✓ |
| Runtime isolation (no module-level `from agent.evolution` in `agent/curator.py`) | `grep -nE "^\s*from agent\.evolution\|^\s*import agent\.evolution" agent/curator.py` (column 0 only) | **0** ✓ (lazy imports at lines 1729-1739 inside `_feedback_scan_phase` body) |
| P31 `TestNonBypassableHumanInLoop` UNCHANGED (Option A) | `pytest tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop` | **2/2 passed** ✓ |
| `apply_patch_transaction` sole caller remains `_cmd_approve` | AST-walk test + grep | **1 Call node in `hermes_cli/feedback.py:945` inside `_cmd_approve`; 0 Call nodes in `agent/curator.py`, `agent/curator_audit.py`, `agent/evolution/evol02_generator.py`, `hermes_cli/curator.py`** ✓ |
| PLW1514 (encoding="utf-8" on every open) | manual grep (ruff unavailable in offline env; CI gate) | `agent/curator_audit.py`: 2 I/O calls (read_text line 148, open line 231) both have `encoding="utf-8"` ✓ |

### Code-Review Fix Commits Confirmed (10 findings / 9 commits)

| Finding | Severity | Commit | Subject |
|---------|----------|--------|---------|
| CR-01 | Critical | `f8015cb0e` | fix(32): CR-01 wire auto_apply_eligible producer + diagnostics in scan |
| CR-02 + WR-02 | Critical + Warning | `a2f800769` (bundled) | fix(32): CR-02 + WR-02 normalize naive --since to UTC in read_audit |
| CR-03 | Critical | `5fb2b57a3` | fix(32): CR-03 use repo-relative paths for EVOL-02 current_files |
| WR-01 | Warning | `5f90e6900` | fix(32): WR-01 fsync audit-log append for crash-atomicity |
| WR-03 | Warning | `d4e18aa12` | fix(32): WR-03 remove dead defensive code + use strict 3-part bucket parse |
| WR-04 | Warning | `a0843f767` | fix(32): WR-04 tighten markdown-fence regex to outer wrap only |
| WR-05 | Warning | `b4e2b51c3` | fix(32): WR-05 narrow outer try in _feedback_scan_phase to setup-only |
| WR-06 | Warning | `9c0c57f9c` | fix(32): WR-06 resolve skill_id before _cmd_reject moves the patch |
| WR-07 | Warning | `9cf8af575` | fix(32): WR-07 shape-validate + `--` guard git revert option-injection |

All 9 commits verified present in `git log`. REVIEW-FIX.md confirms 10 findings (CR-02 and WR-02 fixed in same hunk/commit). All 10 in-scope findings (3 Critical + 7 Warning) applied; 0 skipped. Targeted test runs after each fix all green; full in-scope regression **472 passed, 1 skipped**. INFO findings (IN-01..06) out of scope per `fix_scope: critical_warning`; IN-02 and IN-03 incidentally addressed via CR-01/CR-03 hunks.

### Human Verification Required

None. All Phase 32 success criteria are verifiable programmatically:
- Curator feedback-scan logic → unit tests with mocked LLM
- Audit chain tamper-evidence → deterministic sha256 verification on fixtures
- EVOL-02 diff generation → deterministic difflib output + integration test on real git repo
- CLI subcommands → argparse + delegation tests with monkeypatched P31 handlers
- CURATE-05 auto-apply → two-signal filter logic tested with controlled PatchRecord lists
- Pre-v6 regression → baseline counts hardcoded in test_curator_regression.py

Operator workflow ergonomics (e.g. readability of `hermes curator audit-log` output formatting) is a soft concern but covered by TestAuditLogCmd output-shape assertions. No external services, no UI, no real-time behavior, no LLM non-determinism in the test path (LLM mocked throughout).

### Gaps Summary

No gaps found. All 6 success criteria verified green via dedicated pytest invocations. All 6 requirement IDs (CURATE-01..05, EVOL-02) SATISFIED with code+test evidence. All structural invariants (FOUND-08, runtime isolation, P31 `TestNonBypassableHumanInLoop`, PLW1514) preserved. All 10 code-review findings fixed (9 commits). Full regression: 339 (Phase 32 + P31 CLI) + 176 (P28-P31) passed, zero regressions.

---

_Verified: 2026-06-25T00:55:00Z_
_Verifier: Claude (gsd-verifier)_
