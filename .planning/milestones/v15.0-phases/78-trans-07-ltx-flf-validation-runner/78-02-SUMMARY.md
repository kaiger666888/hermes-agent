---
phase: 78-trans-07-ltx-flf-validation-runner
plan: 02
subsystem: kais-movie-pipeline/transition
tags: [ltx, flf, iclora, verdict, trans-07, operator-action-closure]
requires:
  - "Phase 78 Plan 01 (validation runner + report JSON schema)"
  - "Phase 77 lock pattern (two-script design: runner + lock/verdict script)"
provides:
  - "Verdict update script (update_ltx_flf_verdict.py) with 4-check validation + overwrite guard + atomic write"
  - "18 unit tests for verdict update script validation guards"
  - "Runner Usage section in ltx-flf-iclora-validation.md documenting 4-step operator workflow"
affects:
  - "TRANS-07 operator-action handoff closure (verdict recording mechanism)"
  - "TRANS-11 v16+ production rollout gate (verdict value: ready/deferred-to-v16+/partial)"
tech-stack:
  added: []
  patterns:
    - "Sync-only script (INFRA-04 compliant — no async, no GLM calls, stdlib only)"
    - "4-check validation mirroring Phase 77 lock pattern: lock_ready + non-null verdict + valid value + non-null rationale"
    - "Overwrite guard via HTML comment marker (verdict-locked) for programmatic detection"
    - "Atomic write via tempfile + os.replace (mirrors Phase 77 write_lock)"
    - "Regex-based section replacement: only ## Production-Readiness Verdict section modified"
key-files:
  created:
    - path: "skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py"
      repo: kais-hermes-skills
      commit: b83721d
    - path: "skills/kais-movie-pipeline/tests/test_update_ltx_flf_verdict.py"
      repo: kais-hermes-skills
      commit: 492ebb4
  modified:
    - path: "skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md"
      repo: kais-hermes-skills
      commit: e628620
decisions:
  - "Two-script design (runner + verdict updater) mirrors Phase 77 lock pattern — runner produces report with null operator_decision, operator edits JSON, verdict script writes to markdown"
  - "4-check validation: lock_ready guard + non-null verdict + valid verdict value + non-null rationale — prevents premature/incomplete verdict recording"
  - "Overwrite guard via HTML comment marker (<!-- verdict-locked: ... -->) — programmatic detection without parsing markdown prose"
  - "Verdict comes from operator_decision.verdict in report JSON, NOT from --verdict CLI flag — ensures verdict is always paired with rationale in the same source-of-truth"
  - "Script does NOT auto-recommend verdict based on vision_verify confidence — identity drift is qualitative (confidence != drift severity per D-03)"
  - "Regex section replacement: only ## Production-Readiness Verdict section content is replaced; all other sections (Reference Shots, Operator Signature, Cross-References) are untouched"
metrics:
  duration: 255s
  completed: "2026-07-10"
  tasks: 3
  files: 3
---

# Phase 78 Plan 02: LTX-FLF Verdict Update Script Summary

Verdict update script + 18 unit tests + Runner Usage documentation that closes the TRANS-07 operator-action handoff by providing the mechanism for operators to record their production-readiness verdict (ready / deferred-to-v16+ / partial) in the markdown reference after running validation.

## What Was Built

### 1. Verdict Update Script (Task 1, commit `b83721d`)

`scripts/update_ltx_flf_verdict.py` — sync-only Python script (INFRA-04 compliant):

- **4-check validation**: `validate_verdict()` runs 4 safety checks on `operator_decision` from the report JSON:
  - Check 0: `lock_ready` guard — operator must set `lock_ready: true`
  - Check 1: non-null verdict — verdict must be a non-null string (type check guards against malformed JSON arrays/dicts)
  - Check 2: valid verdict value — verdict must be in `VALID_VERDICTS` frozenset (`ready`, `deferred-to-v16+`, `partial`)
  - Check 3: non-null rationale — rationale must be non-null and non-empty (repudiation protection T-78-09)

- **Overwrite guard**: `check_overwrite_guard()` searches for the HTML comment marker `<!-- verdict-locked: ... -->` in the markdown. Refuses if found without `--force`.

- **Verdict block formatting**: `format_verdict_block()` builds markdown text with the verdict value, description from `VERDICT_DESCRIPTIONS`, operator rationale, UTC timestamp, per-shot validation summary (gen_status + latency + per-frame identity confidence), and the verdict-locked HTML comment marker.

- **Section-scoped write**: `write_verdict()` uses regex to replace only the content between `## Production-Readiness Verdict` and the next `##` heading or `---` separator. All other sections are untouched (T-78-07 mitigation).

- **Atomic write**: Uses `tempfile.NamedTemporaryFile` + `os.replace` pattern (mirrors Phase 77 `write_lock`).

- **CLI**: `--validation-report` (required, path to JSON report), `--verdict-doc` (default auto-resolved), `--force` (overwrite guard). No `--verdict` flag (verdict comes from report per D-03).

- **No auto-recommendation**: The script does NOT compute or suggest a verdict based on vision_verify confidence scores. Identity drift is qualitative (per D-03). The `test_no_auto_recommend_logic` test verifies absence of `recommend_verdict`, `auto_verdict`, `suggest_verdict` functions and confidence-threshold-based verdict assignment patterns.

### 2. Unit Tests (Task 2, commit `492ebb4`)

`tests/test_update_ltx_flf_verdict.py` — 18 tests in `TestUpdateLtxFlfVerdict` class:

1. `test_validate_verdict_refuses_null_verdict` — 3+ errors for all-null operator_decision
2. `test_validate_verdict_refuses_invalid_verdict_value` — error mentions "not valid"
3. `test_validate_verdict_refuses_lock_ready_false` — error mentions "lock_ready"
4. `test_validate_verdict_refuses_null_rationale` — error mentions "rationale"
5. `test_validate_verdict_passes_valid_ready` — 0 errors for valid "ready" verdict
6. `test_validate_verdict_passes_valid_deferred` — "deferred-to-v16+" accepted
7. `test_validate_verdict_passes_valid_partial` — "partial" accepted
8. `test_valid_verdicts_frozenset` — VALID_VERDICTS == frozenset({"ready", "deferred-to-v16+", "partial"})
9. `test_check_overwrite_guard_refuses_without_force` — error string when locked + force=False
10. `test_check_overwrite_guard_allows_with_force` — None when force=True
11. `test_check_overwrite_guard_allows_when_no_lock` — None when no marker
12. `test_write_verdict_updates_verdict_section` — only verdict section modified, other sections unchanged
13. `test_write_verdict_uses_atomic_write` — `os.replace` called
14. `test_format_verdict_block_contains_verdict_and_rationale` — verdict + rationale + marker in output
15. `test_format_verdict_block_includes_shot_summary` — shot_ids + gen_status in output
16. `test_load_validation_report_missing_file` — FileNotFoundError raised
17. `test_load_validation_report_missing_operator_decision` — ValueError with "operator_decision" match
18. `test_no_auto_recommend_logic` — no auto-recommendation patterns in source

All 18 tests pass. Tests use temp file fixtures (`tmp_path`) for write/overwrite tests and source-text inspection for the no-auto-recommend test.

### 3. Runner Usage Documentation (Task 3, commit `e628620`)

Extended `references/ltx-flf-iclora-validation.md` with a new `## Runner Usage` section (145 lines inserted) positioned after `## ComfyUI Node Graph Setup` and before `## Reference Shots (operator fills)`. The section documents the 4-step operator workflow:

- **Step 1: Prepare reference shots directory** — directory structure with `first_frame.png`, `last_frame.png`, `ref1.png`...`ref5.png` per shot. Notes ref1 ordering (scene/vehicle, NOT character portrait).
- **Step 2: Run the validation** — `run_ltx_flf_validation.py --reference-shots shots/` command with all CLI flags documented in a table. Notes INFRA-04 serial execution + vision_verify 3x per shot.
- **Step 3: Review results + fill operator_decision** — instructs operator to edit JSON report with verdict + rationale + lock_ready. Documents all 3 verdict values with meanings. Notes no-auto-recommendation (D-03).
- **Step 4: Record the verdict** — `update_ltx_flf_verdict.py --validation-report <path>` command. Documents 4 validation checks + overwrite guard + `--force` flag.
- **Report JSON Schema subsection** — shows the top-level `{metadata, shots[], operator_decision}` structure with field descriptions.

No existing sections were modified — only the new section was inserted.

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| `validate_verdict` returns 3+ errors for all-null operator_decision | PASS |
| `validate_verdict` returns error for invalid verdict value | PASS |
| `validate_verdict` returns 0 errors for valid "ready" + lock_ready=true | PASS |
| `validate_verdict` accepts all 3 valid verdict values (ready, deferred-to-v16+, partial) | PASS |
| `validate_verdict` rejects invalid verdict values | PASS |
| `check_overwrite_guard` returns error when locked without --force | PASS |
| `check_overwrite_guard` returns None when force=True | PASS |
| `check_overwrite_guard` returns None when no lock marker | PASS |
| `write_verdict` modifies only Production-Readiness Verdict section | PASS |
| `write_verdict` uses atomic write (os.replace called) | PASS |
| `write_verdict` inserts `<!-- verdict-locked: -->` marker | PASS |
| Script does NOT auto-recommend verdict (no confidence-threshold logic) | PASS |
| `--help` shows `--validation-report`, `--verdict-doc`, `--force` (no `--verdict`) | PASS |
| Script starts with `from __future__ import annotations` | PASS |
| No `async def` or `await` keywords (INFRA-04 sync-only) | PASS |
| All `open()` calls include `encoding="utf-8"` (Ruff PLW1514) | PASS |
| `VALID_VERDICTS` == `frozenset({"ready", "deferred-to-v16+", "partial"})` | PASS |
| `VERDICT_DESCRIPTIONS` has entries for all 3 verdict values | PASS |
| All 18 unit tests pass | PASS |
| `## Runner Usage` section exists (exactly 1) | PASS |
| Section positioned after ComfyUI Node Graph Setup, before Reference Shots | PASS |
| Section has 4 step subsections + Report JSON Schema subsection | PASS |
| Section documents all 3 verdict values | PASS |
| Section mentions INFRA-04 serial execution | PASS |
| Section mentions vision_verify 3x per shot | PASS |
| No existing sections modified or deleted | PASS |

## Commits

| Commit | Repo | Message |
|--------|------|---------|
| `b83721d` | kais-hermes-skills | feat(78-02): add verdict update script with 4-check validation + atomic write |
| `492ebb4` | kais-hermes-skills | test(78-02): add 18 unit tests for verdict update script validation guards |
| `e628620` | kais-hermes-skills | docs(78-02): extend ltx-flf-iclora-validation.md with Runner Usage section |

## Known Stubs

None. All functionality is fully wired:
- Verdict script reads real JSON reports and writes to real markdown files
- All 4 validation checks are fully implemented and tested
- Atomic write uses real tempfile + os.replace
- Runner Usage docs reference real CLI flags and real script paths

## Threat Flags

None. All threats from the plan's `<threat_model>` are mitigated as specified:
- T-78-07 (Tampering): `write_verdict()` uses regex to replace only the `## Production-Readiness Verdict` section content; `test_write_verdict_updates_verdict_section` verifies other sections are unchanged
- T-78-08 (Tampering): `check_overwrite_guard()` refuses if `<!-- verdict-locked: -->` marker found without `--force`; 3 tests cover all guard states
- T-78-09 (Repudiation): `validate_verdict()` check 3 requires non-null rationale; rationale is persisted in the markdown verdict block
- T-78-10 (Tampering): `validate_verdict()` check 2 verifies verdict is in `VALID_VERDICTS` frozenset; rejects unknown values
- T-78-11 (Elevation of Privilege): Script has NO auto-recommendation logic; `test_no_auto_recommend_logic` verifies absence of confidence-threshold patterns

## Self-Check: PASSED

- [x] `skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py` exists (FOUND)
- [x] `skills/kais-movie-pipeline/tests/test_update_ltx_flf_verdict.py` exists (FOUND)
- [x] `skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md` exists (FOUND, extended)
- [x] Commit `b83721d` exists in kais-hermes-skills repo (FOUND)
- [x] Commit `492ebb4` exists in kais-hermes-skills repo (FOUND)
- [x] Commit `e628620` exists in kais-hermes-skills repo (FOUND)
