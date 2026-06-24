---
phase: 31-knowledge-evolution-pipeline
verified: 2026-06-24T23:59:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 31: Knowledge Evolution Pipeline Verification Report

**Phase Goal:** Accumulated feedback is transformed into candidate patches (unified diffs against SKILL.md / `references/*.md`) that an operator can review, approve, and apply with full rollback — closing the self-learning loop.
**Verified:** 2026-06-24T23:59:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth (Roadmap SC) | Status | Evidence |
| --- | --- | --- | --- |
| SC-1 | LLM aggregation reads feedback, identifies themes, emits structured insights with evidence chains | VERIFIED | `agent/evolution/insights.py:aggregate_feedback` (line 242) reads `store.query()` + `store.summary()`, calls LLM, validates via `InsightRecord` Pydantic (line 96) which enforces `evidence_chain: list[str] = Field(min_length=1)` (line 118) + defense-in-depth validator (line 124). `AGGREGATION_SYSTEM_PROMPT` (line 59) instructs the model to cite specific feedback record IDs. 17 tests pass in `tests/agent/evolution/test_insights.py`. |
| SC-2 | Patch review queue with feedback chain + LLM rationale + affected skills + eval-gate score | VERIFIED | `agent/evolution/queue.py:PatchRecord` (line 78) carries all four required fields: `feedback_chain`, `llm_rationale`, `skill_id`, `eval_gate_score`. `hermes_cli/feedback.py:_cmd_review_queue` (line 731) prints the table; `_cmd_show_patch` (line 765) prints full unified_diff + rationale + chain. 5 tests in `TestReviewQueueCmd` + 2 in `TestShowPatchCmd` pass. |
| SC-3 | Bundled skill patches require operator approval — NON-BYPASSABLE | VERIFIED | AST-walk of `hermes_cli/feedback.py` confirms ONLY `_cmd_approve` calls `apply_patch_transaction` (verifier re-ran the walk: 0 violators). `_cmd_approve` requires `--yes` (no default-yes). `TestNonBypassableHumanInLoop` (line 846 of test file) is a permanent structural guard. Runtime grep across `run_agent.py`, `agent/`, `cli.py`, `gateway/` returns 0 callers. |
| SC-4 | Patch apply = git-commit with feedback IDs + eval score; rollback subcommand | VERIFIED | `apply_patch_transaction` runs `git commit -m commit_message` (apply.py:497) using `build_commit_message` output (`feat(evolution): <subject> \| feedback: <ids> \| eval: <verdict>:<delta>`). `_cmd_rollback` runs `git revert <sha> --no-edit` (feedback.py:946). `TestRollbackCmdHappyPath` (test line 775) runs end-to-end against a real tmp git repo: real commit, real `git revert`, verifies revert commit appears in `git log`. |
| SC-5 | FOUND-08 byte-intact per patch (expert_id + related_skills byte-for-byte) | VERIFIED | `verify_found08_byte_intact` (apply.py:163) performs byte-level frontmatter block comparison (Pitfall 4 — stricter than value check). Runs inside `apply_patch_transaction` (apply.py:484) for every patched file. CR-03 fix correctly passes when no prior frontmatter exists (line 189). `TestVerifyFound08ByteIntact` (test line 125) includes `test_fails_on_byte_different_frontmatter` using the `violating_frontmatter_diffusion.diff` fixture — proves the byte-level check catches value-equal-but-byte-different YAML re-serialization. |
| SC-6 | v5/v4 refs additive-only (snowflake / e-konte / scamper / dreamina-cli-baseline / v86-pipeline-mapping) | VERIFIED | `PROTECTED_REFS` tuple in `queue.py:47` lists all 5 protected refs. `verify_additive_only` (apply.py:87) is a pure-function regex (Pitfall 6 false-positive-safe: skips `---`/`+++`/`@@`/`\ No newline` headers, returns False on `-` content line or D<B hunk). CR-04 fix runs the check BEFORE `git apply` mutates the working tree (apply.py:448 before apply.py:468) — eliminates the "applied then reverted" race. 8 tests in `TestVerifyAdditiveOnly` pass. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `agent/evolution/__init__.py` | Public API re-exports | VERIFIED | 75 lines; `__all__` lists 20 names; re-exports from all 4 submodules |
| `agent/evolution/insights.py` | EVOL-01 LLM aggregation | VERIFIED | 399 lines; aggregate_feedback, InsightRecord, AggregationError, make_aggregation_client, build_aggregation_user_prompt, AGGREGATION_SYSTEM_PROMPT all present |
| `agent/evolution/diff_generator.py` | EVOL-02 placeholder (difflib) | VERIFIED | 165 lines; generate_additive_diff with CRLF normalization + marker uniqueness + idempotent guard |
| `agent/evolution/queue.py` | EVOL-03 JSONL queue | VERIFIED | 375 lines; PatchRecord, append_patch, move_patch, read_queue, append_failed_gate, PROTECTED_REFS, atomic rewrite via tempfile.mkstemp+os.replace |
| `agent/evolution/apply.py` | EVOL-05 atomic transaction | VERIFIED | 568 lines; apply_patch_transaction, verify_additive_only, verify_found08_byte_intact, revert_files, build_commit_message, ApplyError, ApplyResult |
| `hermes_cli/feedback.py` | register_cli extended with 6 subcommands | VERIFIED | 6 new subparsers (evolve/review-queue/show-patch/approve/reject/rollback); 6 `_cmd_*` handlers; existing 4 subcommands preserved (TestRegisterCliPreservesExistingSubcommands) |
| `tests/agent/evolution/conftest.py` | Fixtures for evolution tests | VERIFIED | 8137 bytes; evolution_env, mock_llm_client, mock_store, sample_feedback_records, sample_skill_content |
| `tests/hermes_cli/test_evolution_cli.py` | CLI smoke tests for 6 subcommands | VERIFIED | 36571 bytes; 27 tests across 14 classes including TestNonBypassableHumanInLoop |
| `tests/fixtures/evolution/*` | 5 fixture files | VERIFIED | sample_skill_md.md, sample_insights.json, additive.diff, violating_deletion.diff, violating_frontmatter_diffusion.diff all exist |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `hermes_cli/feedback.py:_cmd_approve` | `agent.evolution.apply_patch_transaction` | LAZY `from agent.evolution import apply_patch_transaction` inside handler body | WIRED | feedback.py:854 (import), :894 (call); AST-walk confirms this is the ONLY caller |
| `hermes_cli/feedback.py:_cmd_evolve` | `agent.evolution.aggregate_feedback` | LAZY import inside handler | WIRED | feedback.py:_cmd_evolve imports aggregate_feedback, make_aggregation_client, generate_additive_diff, PatchRecord, append_patch, append_failed_gate |
| `agent/evolution/apply.py` | `subprocess git` | argv-list (no shell=True) | WIRED | All subprocess.run calls use list argv; grep for `shell=True` returns only doc-comment mentions |
| `hermes_cli/feedback.py:_run_eval_gate` | `skills/movie-experts/_eval/gate.py` (subprocess) | `subprocess.run([sys.executable, gate.py, ...])` | WIRED | CR-01 fix added `--no-answers-required` + `--config`; handles exit-code-2 collision (WR-06) |
| `agent/evolution/insights.py:aggregate_feedback` | `FeedbackStore.query/summary` | Dependency injection via `store` parameter | WIRED | CR-02 fix converts Pydantic FeedbackRecord objects to dicts before json.dumps; uses `store._make_record_id` for record_id consistency |
| `agent/evolution/apply.py` | `agent.skill_utils.parse_frontmatter` | (planned) | NOT IMPORTED | Apply.py uses its own `_extract_frontmatter_block` (byte-level) which is STRICTER than parse_frontmatter's value-level check — intentional, no gap |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `insights.py:aggregate_feedback` | `records` from `store.query()` | FeedbackStore (Phase 29) — reads `~/.hermes/skills/.feedback/<skill>/<source>/*.jsonl` | Yes — FeedbackStore returns Pydantic FeedbackRecord objects with record_id, verdict, correction, output_snapshot | FLOWING |
| `apply.py:apply_patch_transaction` | `patch_text` from `patch_path.read_text()` | Temp `.patch` file written by `_cmd_approve` from `PatchRecord.unified_diff` (LLM-generated + difflib-emitted) | Yes — unified diff is real (generated by `generate_additive_diff` in `_cmd_evolve`) | FLOWING |
| `feedback.py:_cmd_review_queue` | `records` from `read_queue(status, skill_id)` | `~/.hermes/skills/.feedback/evolution/queue.jsonl` | Yes — populated by `_cmd_evolve` after gate-pass | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full Phase 31 test suite green | `uv run python -m pytest tests/agent/evolution/ tests/hermes_cli/test_evolution_cli.py -x --timeout=60` | 94 passed in 3.92s | PASS |
| EVOL-04 non-bypassable AST invariant | `python -c "import ast; ... walk feedback.py for apply_patch_transaction calls outside _cmd_approve"` | violators: NONE | PASS |
| Runtime isolation grep (0 matches) | `grep -rn "from agent.evolution\|import agent.evolution" run_agent.py agent/conversation_loop.py agent/prompt_builder.py agent/system_prompt.py agent/tool_executor.py agent/curator.py cli.py gateway/` | 0 | PASS |
| Module-top isolation in feedback.py | `grep -n "^from agent.evolution\|^import agent.evolution" hermes_cli/feedback.py` | 0 | PASS |
| Ruff PLW1514 + lint | `uv run ruff check agent/evolution/ hermes_cli/feedback.py` | All checks passed | PASS |
| Phase 30 regression | `uv run python -m pytest skills/movie-experts/_eval/tests/` | 105 passed | PASS |
| Phase 28/29 regression | `uv run python -m pytest tests/agent/test_feedback_*.py tests/hermes_cli/test_feedback_cli.py` | 150 passed, 1 skipped | PASS |
| FOUND-08 baseline (no SKILL.md changes from Phase 31) | `git log --oneline -- 'skills/movie-experts/*/SKILL.md'` | All SKILL.md changes are from v5.0 (commits 23-26); Phase 31 commits only touch agent/evolution/, hermes_cli/feedback.py, planning/ | PASS |
| shell=True absence | `grep -rn "shell=True" agent/evolution/ hermes_cli/feedback.py` | 2 matches — both in doc comments documenting its absence | PASS |

### Probe Execution

SKIPPED — Phase 31 has no conventional `scripts/*/tests/probe-*.sh` probes. The phase's verification is test-driven (94 pytest tests) + structural (AST-walk, grep invariants).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| EVOL-01 | 31-01, 31-02 | 反馈→可执行知识点抽取 (LLM aggregation with evidence chains) | SATISFIED | `aggregate_feedback` + `InsightRecord.evidence_chain` (min_length=1) + 17 test_insights.py tests + CLI `_cmd_evolve` with --dry-run/--insights-only/no-feedback paths |
| EVOL-03 | 31-01, 31-02 | Patch review queue with feedback chain + LLM rationale + affected skills | SATISFIED | `PatchRecord` schema + queue.jsonl/applied.jsonl/rejected.jsonl lifecycle + CLI `_cmd_review_queue`/`_cmd_show_patch`/`_cmd_reject` |
| EVOL-04 | 31-01, 31-02 | Human-in-loop approve workflow — bundled skill patches NEVER auto-apply | SATISFIED | AST-verified: only `_cmd_approve` calls `apply_patch_transaction`. `--yes` required (no default-yes). `TestNonBypassableHumanInLoop` is a permanent structural guard. Runtime modules have zero callers. |
| EVOL-05 | 31-01, 31-02 | Patch apply + rollback — git-commit-on-apply + rollback subcommand | SATISFIED | `apply_patch_transaction` commits via `git commit -m` with machine-parseable message; `_cmd_rollback` invokes `git revert <sha> --no-edit` with SHA validation. End-to-end rollback test against real tmp git repo passes. |

**Orphaned requirements check:** REQUIREMENTS.md maps exactly EVOL-01, EVOL-03, EVOL-04, EVOL-05 to Phase 31. All 4 are claimed by the plans and SATISFIED. No orphans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| (none) | — | — | — | No TBD/FIXME/XXX/HACK markers in shipped code. No empty handlers. No console.log-only implementations. All `_cmd_*` handlers return int exit codes and call real logic. |

**Debt marker scan:** `grep -E "TBD|FIXME|XXX" agent/evolution/*.py hermes_cli/feedback.py` returns 0 matches in shipped code. Zero unreferenced debt markers.

**Stub scan:** No `return None`, `return []`, `=> {}`, or hardcoded-empty-data patterns in any rendering path. Temp patch files are cleaned via `try/finally unlink`. `apply_patch_transaction` reverts on ANY failure.

### Human Verification Required

**1. Live LLM Aggregation End-to-End**

**Test:** Run `hermes feedback evolve --skill <id>` against a populated FeedbackStore with a live OPENROUTER_API_KEY (or compatible provider key). Inspect the generated `~/.hermes/skills/.feedback/evolution/insights.jsonl` entries.
**Expected:** Each insight has a meaningful theme (not generic), a non-empty evidence_chain citing real feedback record IDs, a rationale that references the cited feedback, and a proposed_addition that is genuinely additive markdown.
**Why human:** The 17 test_insights.py tests use a mock LLM client. CR-02's correctness — whether `store._make_record_id` produces the same IDs the operator sees in `feedback.jsonl` — depends on the live FeedbackStore internal state. LLM output quality (theme coherence, evidence-chain accuracy) cannot be asserted programmatically. The aggregation prompt's 7 critical rules (additive-only, evidence chain, NEVER touch v4/v5 refs) are enforced by post-hoc Pydantic validation, but whether the LLM obeys them in practice needs one live run.

**2. Live Gate Integration End-to-End**

**Test:** Run `hermes feedback evolve --skill <id>` WITHOUT `--insights-only` so patches flow through `_run_eval_gate`. Inspect `queue.jsonl` (passing patches) and `failed_gate.jsonl` (failing patches).
**Expected:** Real eval gate runs via subprocess against `skills/movie-experts/_eval/gate.py` with the `--no-answers-required` flag (CR-01 fix); passing patches enter `queue.jsonl`, failing patches enter `failed_gate.jsonl`. CR-01's exit-code-2 ambiguity handling (WR-06) triggers correctly when gate.py emits it.
**Why human:** Tests mock the gate subprocess. Whether `gate.py --no-answers-required` correctly short-circuits to `inconclusive` verdict + stub report on a real run (vs hitting `parser.error()`) requires one live invocation. The CR-01 fix added a NEW flag to `gate.py` itself (`--no-answers-required`) — that flag's behavior in gate.py is outside Phase 31's test surface and should be sanity-checked once with a live gate run.

**3. Operator Approve Flow on a Real Repo**

**Test:** Against a clean working tree in the hermes-agent repo, queue a patch via `evolve`, then run `hermes feedback approve <patch_id> --yes`. Verify the commit appears in `git log` with the machine-parseable message format, then run `hermes feedback rollback <sha> --yes` and verify the revert appears.
**Expected:** Commit message matches `feat(evolution): <subject> | feedback: <ids> | eval: <verdict>:<delta>`. CR-05 sanitization prevents commit-message injection (stripped newlines/pipes, validated feedback_ids, coerced verdict). Rollback produces a revert commit.
**Why human:** The happy-path test for approve uses mocks for `apply_patch_transaction`. The end-to-end rollback test (TestRollbackCmdHappyPath) runs against a tmp git repo, not the actual hermes-agent repo. One live run on the real repo confirms the dirty-tree guard (D-EVOL-04 invariant) fires correctly when the operator has uncommitted changes.

### Gaps Summary

**No gaps found.** All 6 roadmap success criteria are verified with codebase evidence (not SUMMARY claims). All 4 requirements (EVOL-01, EVOL-03, EVOL-04, EVOL-05) are SATISFIED. All required artifacts exist, are substantive (1582 lines of evolution engine + 36KB of CLI tests), are wired (lazy imports preserve runtime isolation; AST confirms EVOL-04 non-bypassable), and have real data flowing (FeedbackStore → aggregate_feedback → PatchRecord → apply_patch_transaction → git commit).

**Code review closure:** All 12 review issues (5 CR- blockers + 7 WR- warnings) are fixed in 7 commits with status `all_fixed` (per `31-REVIEW-FIX.md`). Each fix has a targeted regression test (CR-03+CR-04 → 23 tests; WR-05 → regression test; etc.).

**Deferred items (NOT gaps — scheduled for later phases):**

| Item | Addressed In | Evidence |
| --- | --- | --- |
| EVOL-02 (unified-diff patch generator) | Phase 32 | REQUIREMENTS.md: "EVOL-02 \| Phase 32 \| Unified-diff patch generator (invoked by Curator proposal path)"; CONTEXT.md deferred section: "EVOL-02 diff generator — Mapped to Phase 32 (Curator invokes it). P31 uses a placeholder if EVOL-02 not yet shipped." Phase 31 shipped a difflib-based placeholder per plan. |
| CURATE-01..05 (Curator upgrade + audit log + semi-auto path) | Phase 32 | REQUIREMENTS.md Phase 32 coverage row |
| OBS-01..03 (Observability dashboard) | Phase 33 | REQUIREMENTS.md Phase 33 coverage row |
| Background daemon for evolve | Phase 32 | CONTEXT.md: "Background daemon — P32 Curator scope. P31 ships operator-invoked only." |
| Web dashboard for review queue | Phase 33 | CONTEXT.md: "Web dashboard for review queue — P33 Observability scope." |

These deferred items do NOT affect Phase 31's goal — the phase's scope is explicitly the operator-invoked pipeline mechanics, not automation or dashboards.

---

_Verified: 2026-06-24T23:59:00Z_
_Verifier: Claude (gsd-verifier)_
