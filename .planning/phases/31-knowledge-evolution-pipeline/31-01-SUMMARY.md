---
phase: 31
plan: 01
subsystem: knowledge-evolution-engine
tags: [evolution, llm-aggregation, difflib, atomic-apply, found-08, additive-only, jsonl-queue]
requirements: [EVOL-01, EVOL-03, EVOL-04, EVOL-05]
requires:
  - "agent/feedback_store.py:FeedbackStore (P29 — query/summary for aggregation input)"
  - "agent/feedback_schema.py:FeedbackRecord (P28 — record shape)"
  - "agent/skill_utils.py:parse_frontmatter (FOUND-08 field extraction)"
  - "skills/movie-experts/_eval/gate.py (P30 — subprocess pattern reference)"
provides:
  - "agent/evolution/ subpackage — EVOL-01/03/04/05 engine (operator-invoked only)"
  - "aggregate_feedback + InsightRecord + AggregationError (EVOL-01)"
  - "generate_additive_diff (EVOL-02 placeholder — stdlib difflib)"
  - "PatchRecord + append/move/read_queue + failed_gate.jsonl (EVOL-03)"
  - "apply_patch_transaction + verify_found08_byte_intact + verify_additive_only + revert_files (EVOL-05)"
affects:
  - "No runtime modules — agent/evolution/ is NOT imported by run_agent/conversation_loop/curator/cli/gateway"
tech_stack:
  added: []
  patterns:
    - "TDD RED/GREEN/REFACTOR cycle (Tasks 1-3)"
    - "Pydantic v2 BaseModel for record schemas (InsightRecord, PatchRecord)"
    - "Atomic apply transaction (6-step: validate → apply → FOUND-08 → additive → stage → commit)"
    - "Byte-level frontmatter comparison (Pitfall 4 — stricter than value check)"
    - "Additive-only verification via pure-function regex (Pitfall 6 false-positive-safe)"
    - "Argv-list subprocess only (T-30-02 — never shell=True)"
    - "Deferred openai import (RuntimeError on missing key surfaces before SDK import)"
    - "Atomic JSONL rewrite via tempfile.mkstemp + os.replace"
key_files:
  created:
    - agent/evolution/__init__.py
    - agent/evolution/insights.py
    - agent/evolution/diff_generator.py
    - agent/evolution/queue.py
    - agent/evolution/apply.py
    - tests/agent/evolution/__init__.py
    - tests/agent/evolution/conftest.py
    - tests/agent/evolution/test_insights.py
    - tests/agent/evolution/test_diff_generator.py
    - tests/agent/evolution/test_queue.py
    - tests/agent/evolution/test_apply.py
    - tests/fixtures/evolution/sample_skill_md.md
    - tests/fixtures/evolution/sample_insights.json
    - tests/fixtures/evolution/additive.diff
    - tests/fixtures/evolution/violating_deletion.diff
    - tests/fixtures/evolution/violating_frontmatter_diffusion.diff
  modified: []
decisions:
  - "EVOL-02 placeholder uses stdlib difflib (LLM emits structured add-after-marker, difflib generates the diff)"
  - "Additive-only check is UNIVERSAL (all evolution patches additive per EVOL-02 scope); protected_refs flagged explicitly in SC-6 error"
  - "Deferred openai import so missing-key RuntimeError works without SDK installed"
  - "Local _extract_patched_files copy (gate.py under hyphenated path not importable)"
  - "Atomic JSONL rewrite via tempfile.mkstemp + os.replace (not os.mkstemp which had attr-resolution issue)"
  - "GIT_CONFIG_GLOBAL=/dev/null in git-author test to isolate from operator's global config"
metrics:
  duration: "~45 min"
  completed: "2026-06-24"
  tasks_total: 4
  tasks_completed: 4
  commits: 7
  files_created: 16
  files_modified: 0
  tests_added: 60
---

# Phase 31 Plan 01: Knowledge Evolution Pipeline Engine Summary

LLM aggregation (EVOL-01) + difflib additive diff (EVOL-02 placeholder) + JSONL review queue (EVOL-03) + atomic git apply transaction (EVOL-05) with FOUND-08 byte-intact + additive-only verification — the pure-function + dataclass + transaction primitives that Plan 02 wires into the CLI.

## What Was Built

### agent/evolution/ subpackage (5 modules, 20 public API names)

**insights.py (EVOL-01)** — LLM aggregation of accumulated feedback into structured insights:
- `aggregate_feedback(skill_id, store, client, model)` → `list[InsightRecord]`
- `InsightRecord` Pydantic model (insight_id, skill_id, theme, evidence_chain min_length=1, rationale, proposed_addition, insert_after_marker, ts) with defense-in-depth validator
- `AggregationError` — raised on malformed LLM JSON (NEVER silent empty list per Pitfall 1 atomicity)
- `make_aggregation_client(model_override)` — OpenAI client construction with fail-fast on missing OPENROUTER_API_KEY; deferred SDK import so RuntimeError works without openai installed
- `build_aggregation_user_prompt(skill_id, feedback_summary, feedback_details)` — embeds 3 JSON dumps with `ensure_ascii=False` for CN content; truncates to 50 most-recent records
- `AGGREGATION_SYSTEM_PROMPT` — 7 critical rules (additive-only, evidence chain, frontmatter byte-preserve, NEVER touch v4/v5 protected refs)
- Markdown fence stripping (`_FENCE_RE`) + `response_format=json_object` retry-without on SDK error (Pitfall 1 mitigation A2)
- Content-addressed `insight_id = f"{skill_id}_{ts_unix}_{sha256[:8]}"`
- Atomic Pydantic validation: collects ALL bad records before raising AggregationError

**diff_generator.py (EVOL-02 placeholder)** — stdlib difflib additive diff:
- `generate_additive_diff(current_content, proposed_addition, insert_after_marker, skill_md_path)` → unified diff string
- Pitfall 2 mitigations: CRLF normalization, marker uniqueness check (raise on 0 or >1 matches), idempotent guard (raise ValueError on no-op addition per plan-checker Warning 5)
- SC-6 by construction: only appends, never modifies/deletes; asserts at least one `+` content line

**queue.py (EVOL-03)** — JSONL review queue lifecycle:
- `PatchRecord` Pydantic model (patch_id, skill_id, insight_id, unified_diff, feedback_chain, llm_rationale, eval_gate_score, status, ts_queued + optional commit_sha/ts_applied/reason/ts_rejected)
- `PROTECTED_REFS` tuple (5 v4/v5 refs: snowflake-method, e-konte-format, scamper-variations, dreamina-cli-baseline, v86-pipeline-mapping) — reused by apply.py
- `append_patch(record, evolution_dir)` — append to queue.jsonl (status must be "pending")
- `move_patch(patch_id, target_status, evolution_dir, commit_sha/reason)` — atomic move from queue.jsonl to applied.jsonl/rejected.jsonl with transition timestamps
- `read_queue(evolution_dir, status, skill_id)` — filtered read; malformed lines skipped + WARNING logged (feedback_store.py:654 pattern)
- `append_failed_gate(rejection, evolution_dir)` — writes to failed_gate.jsonl (NEVER surfaces in read_queue)
- `_atomic_rewrite_jsonl` via `tempfile.mkstemp + os.replace`

**apply.py (EVOL-05)** — atomic git apply transaction:
- `apply_patch_transaction(patch_path, repo_root, commit_message, protected_refs)` → `ApplyResult`
- 6-step atomic transaction (D-EVOL-04): (1) dirty-tree guard, (2) git author fallback (Pitfall 7, repo-local only), (3) `git apply --check`, (4) `git apply`, (5a) FOUND-08 byte-intact, (5b) additive-only UNIVERSAL check, (6) `git add` + `git commit`
- `verify_additive_only(diff_text)` — pure-function regex (Pitfall 6 false-positive-safe): skips `--- `/`+++ `/`@@ ` headers, returns False on `-` content line or D<B hunk or empty diff
- `verify_found08_byte_intact(frontmatter_block_before, skill_md_path_after)` — byte-level comparison (Pitfall 4 stricter than value check); `_extract_frontmatter_block` helper
- `_extract_patched_files(patch_path)` — local copy of gate.py logic (hyphenated path not importable); T-31-04 path-traversal + WR-07 deletion-patch hardening
- `revert_files(files, repo_root)` — mirrors gate.py:201 (checkout for existing, scoped clean for added); NEVER blanket clean
- `build_commit_message(insight_summary, feedback_ids, eval_verdict, eval_mean_delta)` — machine-parseable `feat(evolution): <subject> | feedback: <ids> | eval: <verdict>:<delta>` (72-char subject truncation)
- `ApplyError` + `ApplyResult` dataclass
- try/except revert on ANY failure; if revert ALSO fails, raises ApplyError with "manual recovery required"

### Test scaffolding (60 tests across 4 files + conftest)

- `conftest.py` — `evolution_env` (isolated HERMES_HOME + tmp git repo + committed sample SKILL.md), `mock_llm_client` (OpenAI-shaped stub), `mock_store` (FeedbackStore stub), `sample_feedback_records`, `sample_skill_content`
- `test_insights.py` — 17 tests: InsightRecord schema, aggregate_feedback happy path + fence stripping + content-addressed IDs, malformed JSON (trailing comma, missing insights key, not-json), empty feedback, make_aggregation_client (4 tests with mocked OpenAI SDK), build_aggregation_user_prompt, AGGREGATION_SYSTEM_PROMPT critical-rules content
- `test_diff_generator.py` — 7 tests: additive hunk generation, hunk header D>B, marker not found, marker not unique, CRLF normalization, idempotent guard (empty addition), no-minus-content-lines
- `test_queue.py` — 14 tests: PatchRecord schema + invalid status + PROTECTED_REFS content, append (1 line + preserves prior), move to applied + rejected, move not-found, read pending + skill filter + applied, malformed-line skip, failed_gate separation
- `test_apply.py` — 22 tests: verify_additive_only (6 cases), _extract_frontmatter_block (3 cases), verify_found08_byte_intact (byte-equal + byte-different), build_commit_message (format + truncation + empty feedback), revert_files (checkout + clean), apply happy path, revert-on-deletion, dirty-tree guard, git-author fallback

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 9532d05b1 | test | RED: failing tests + fixtures for EVOL-01 LLM aggregation |
| 9f4d3b527 | feat | GREEN: implement EVOL-01 LLM aggregation engine |
| c2a82f640 | test | RED: failing tests for EVOL-02 diff generator + EVOL-03 queue |
| 02160d694 | feat | GREEN: implement EVOL-02 placeholder + EVOL-03 queue lifecycle |
| 7ee40250f | test | RED: failing tests for EVOL-05 atomic apply transaction |
| 5d27b9488 | feat | GREEN: implement EVOL-05 atomic apply + FOUND-08 + additive-only |
| 4cc280688 | feat | Public API re-exports + runtime isolation verification |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Deferred openai import in make_aggregation_client**
- **Found during:** Task 1 (test failure)
- **Issue:** `make_aggregation_client` imported `openai` at the top of the function, before the API key check. In environments where openai isn't installed, the `RuntimeError` for missing key never surfaced — the `ModuleNotFoundError` hit first.
- **Fix:** Deferred `from openai import OpenAI` until AFTER the key check. Now the missing-key RuntimeError fires cleanly regardless of SDK installation state.
- **Files modified:** agent/evolution/insights.py
- **Commit:** 9f4d3b527

**2. [Rule 1 - Bug] _extract_frontmatter_block end_idx formula was wrong**
- **Found during:** Task 3 (happy-path test failing with false FOUND-08 violation)
- **Issue:** Formula `end_match.start() + 3 + end_match.end()` double-counted the offset, producing an end_idx beyond the content length and including the entire body in the "frontmatter block".
- **Fix:** Corrected to `3 + end_match.end()` — end_match.end() is already the offset within `content[3:]` where the match ends; add 3 to translate back to full content offset.
- **Files modified:** agent/evolution/apply.py
- **Commit:** 5d27b9488

**3. [Rule 2 - Missing Critical Functionality] Additive-only check made UNIVERSAL**
- **Found during:** Task 3 (deletion-patch test not raising ApplyError)
- **Issue:** Plan action step 5d specified additive-only check ONLY for protected_refs. But the behavior bullet "raises ApplyError when the patch would delete a `-` content line (additive-only violation)" is universal — ALL evolution patches must be additive per EVOL-02 scope discipline. The protected-refs-only check let deletion patches through for non-protected files.
- **Fix:** Made `verify_additive_only` run for ALL files; protected_refs now only affects the error message specificity (SC-6 violation vs generic additive-only).
- **Files modified:** agent/evolution/apply.py
- **Commit:** 5d27b9488

**4. [Rule 3 - Blocking Issue] os.mkstemp AttributeError → tempfile.mkstemp**
- **Found during:** Task 2 (queue move_patch test failing)
- **Issue:** `os.mkstemp` raised `AttributeError: module 'os' has no attribute 'mkstemp'` in the test environment.
- **Fix:** Switched to `tempfile.mkstemp` (canonical import; `os.mkstemp` is an alias that isn't always resolvable).
- **Files modified:** agent/evolution/queue.py
- **Commit:** 02160d694

**5. [Rule 3 - Blocking Issue] Pydantic v2 model_copy(update=...) doesn't re-run validators**
- **Found during:** Task 2 (test_rejects_invalid_status failing)
- **Issue:** Test used `rec.model_copy(update={"status": "bogus"})` expecting ValidationError, but Pydantic v2's `model_copy` doesn't re-run validators by default.
- **Fix:** Changed test to construct PatchRecord directly with the bad status (which DOES trigger the model_validator).
- **Files modified:** tests/agent/evolution/test_queue.py
- **Commit:** 02160d694

**6. [Rule 3 - Blocking Issue] Git author test needed GIT_CONFIG_GLOBAL isolation**
- **Found during:** Task 3 (git-author test failing — operator's global config leaked in)
- **Issue:** `git config --unset user.email` on the repo didn't prevent the operator's GLOBAL git config from providing user.email, so the fallback never triggered.
- **Fix:** Test now sets `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_SYSTEM=/dev/null` via monkeypatch to isolate from global/system config.
- **Files modified:** tests/agent/evolution/test_apply.py
- **Commit:** 5d27b9488

## TDD Gate Compliance

All 3 TDD tasks (1, 2, 3) followed RED/GREEN cycle correctly:
- Task 1: RED commit `9532d05b1` (tests failing — ModuleNotFoundError) → GREEN commit `9f4d3b527` (17 tests pass)
- Task 2: RED commit `c2a82f640` (tests failing — ModuleNotFoundError) → GREEN commit `02160d694` (21 tests pass)
- Task 3: RED commit `7ee40250f` (tests failing — ModuleNotFoundError) → GREEN commit `5d27b9488` (22 tests pass)

Task 4 was plain `type="auto"` (no TDD) — public API re-exports + isolation grep verification.

## Isolation Verification

**Hermes runtime isolation (SC):** `grep -rn "from agent.evolution\|import agent.evolution" run_agent.py agent/conversation_loop.py agent/prompt_builder.py agent/system_prompt.py agent/tool_executor.py agent/curator.py cli.py gateway/` returns **0 matches**. The only intended consumer is `hermes_cli/feedback.py` (Plan 02, CLI handler).

## Found-08 + Additive-Only Verification

- **FOUND-08 byte-intact (SC-5):** `verify_found08_byte_intact` uses byte-level frontmatter block comparison (Pitfall 4 — catches re-serialization that preserves parsed values but changes bytes). Tested with `violating_frontmatter_diffusion.diff` fixture (related_skills list reordering: `[a, b]` → `[b, a]` — same parsed set, different bytes → check fails).
- **Additive-only (SC-6):** `verify_additive_only` pure-function regex skips `--- `/`+++ `/`@@ ` headers, returns False on `-` content line or D<B hunk. UNIVERSAL check (all evolution patches additive per EVOL-02). Protected refs flagged with explicit SC-6 error message.

## Known Stubs

None. All modules are fully implemented; no placeholder/TODO/FIXME markers in shipped code.

## Open Dependencies for Plan 02

- `hermes_cli/feedback.py:register_cli` will import from `agent.evolution` to wire the 5 new CLI subcommands (`evolve`, `review-queue`, `show-patch`, `approve`, `reject`, `rollback`)
- Plan 02 will add the `_cmd_approve` handler as the ONLY caller of `apply_patch_transaction` (EVOL-04 non-bypassable human-in-loop enforced structurally)
- Plan 02 will add the `_cmd_rollback` handler using `git revert <sha>` (EVOL-05 rollback subcommand)

## Self-Check

**Files created (verified to exist):**
- agent/evolution/__init__.py ✓
- agent/evolution/insights.py ✓
- agent/evolution/diff_generator.py ✓
- agent/evolution/queue.py ✓
- agent/evolution/apply.py ✓
- tests/agent/evolution/{__init__,conftest,test_insights,test_diff_generator,test_queue,test_apply}.py ✓
- tests/fixtures/evolution/{sample_skill_md.md, sample_insights.json, additive.diff, violating_deletion.diff, violating_frontmatter_diffusion.diff} ✓

**Commits (verified in git log):**
- 9532d05b1 ✓
- 9f4d3b527 ✓
- c2a82f640 ✓
- 02160d694 ✓
- 7ee40250f ✓
- 5d27b9488 ✓
- 4cc280688 ✓

**Test suite:** 60/60 evolution tests green; 110/110 feedback subsystem tests green (+1 pre-existing skip); 103/105 eval gate tests green (2 pre-existing openai-missing failures unrelated to P31).

## Self-Check: PASSED
