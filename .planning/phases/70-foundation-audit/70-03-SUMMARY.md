---
phase: 70-foundation-audit
plan: 03
subsystem: docs
tags: [validate-checklist, smoke-runner, phase-76-input, xcut-01, audit-traceability, canonical-field-names]

# Dependency graph
requires:
  - phase: 70-01 (LINEAGE-INVENTORY)
    provides: inventory file (XCUT-01a/b/c targets) + cross-repo pin SHAs referenced in checklist procedure
  - phase: 70-02 (curator-freeze)
    provides: STATE.md `v14.0 Freeze Flags` block (XCUT-01e target) + `curator.enabled: false` (XCUT-01d target)
provides:
  - "Phase 76 VALIDATE audit checklist (70-VALIDATE-CHECKLIST.md) — deterministic XCUT-01 + hard-constraint audit input"
  - "Bash smoke runner (70-smoke.sh) executing all 6 XCUT-01 assertions with set -euo pipefail hard-fail semantics"
  - "Canonical field-name discipline encoded (lineage.skill_sha256, NOT source_sha) — prevents Phase 76 false-green on empty grep"
  - "Cross-repo commit pin re-hash procedure (5-step) for Phase 76 VALIDATE"
affects: [Phase 76 (VALIDATE — consumes checklist as audit input + re-runs smoke.sh as sanity check)]

# Tech tracking
tech-stack:
  added: []  # zero new packages — pure markdown + bash
  patterns:
    - "Markdown checklist as deterministic audit-traceability input (hand-rolled from RESEARCH.md spec — no prior template in repo per PATTERNS.md No Analog Found section)"
    - "Bash smoke runner with set -euo pipefail + BASH_SOURCE REPO_ROOT resolution (scripts/run_tests.sh idiom)"
    - "grep-count || true guard to survive set -e on zero matches (kill_modal.sh idiom)"
    - "Canonical field-name discipline callout (block-quote) to prevent terminology drift between roadmap prose and actual agent.yaml schema"

key-files:
  created:
    - ".planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md (192 lines, 34 table rows)"
    - ".planning/phases/70-foundation-audit/70-smoke.sh (79 lines, 6 XCUT-01 assertions, 3.4KB)"
  modified: []

key-decisions:
  - "Checklist authored hand-rolled from RESEARCH.md Validation Architecture spec — no prior CHECKLIST template exists in the repo (PATTERNS.md No Analog Found). Structure: 6 XCUT-01 rows + 4 hard-constraint preservation sections (INFRA-04/EVAL-06/FOUND-08/L1-L6) + cross-repo pin procedure + META-RULE X-2 audit rows + canonical field-name callout"
  - "Status glyphs as literal text (pending/green/red/flaky) NOT emoji — per CLAUDE.md 'avoid emojis' rule + PATTERNS.md line 77"
  - "XCUT-01d smoke uses config.yaml grep (not `hermes curator status` CLI) so the assertion works without requiring the hermes CLI in the execution environment — config flag is the canonical freeze mechanism per RESEARCH Pattern 2"
  - "smoke.sh header trimmed to 2 lines before `set -euo pipefail` so the plan's acceptance criterion `head -3 | grep set -euo pipefail` passes (originally had a 10-line header comment block — Rule 3 auto-fix to unblock the acceptance gate)"
  - "REPO_ROOT resolved via `cd \"$SCRIPT_DIR/../../..\" && pwd` (3 levels up from .planning/phases/70-foundation-audit/) — plan suggested `../..` (2 levels) which would have pointed at `.planning/` not the repo root"
  - "source_sha appears ONLY inside the PITFALL 1 warning callout + the roadmap-shorthand mapping table (as the 'wrong name') — never as a field name in any assertion, per acceptance criterion"

patterns-established:
  - "Checklist-as-audit-input pattern: Phase N drafts the checklist, Phase N+M consumes it as deterministic verification input (avoids reverse-engineering assertions from research docs)"
  - "Canonical field-name callout as a block-quote in every cross-phase audit artifact — load-bearing defense against terminology drift"

requirements-completed: [XCUT-01]

# Metrics
duration: 5min
completed: 2026-07-09
---

# Phase 70 Plan 03: VALIDATE-CHECKLIST + smoke.sh Runner Summary

**Phase 76 VALIDATE-CHECKLIST authored (34 table rows, 6 XCUT-01 sub-claims + 4 hard-constraint preservation sections + cross-repo pin procedure + canonical field-name discipline callout) AND bash smoke runner shipped (6 assertions, `set -euo pipefail`, exits 0 when all 6 pass) — Phase 70 now complete (3/3 plans)**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-09T06:53Z
- **Completed:** 2026-07-09T06:58Z
- **Tasks:** 2 (Task 1: VALIDATE-CHECKLIST.md; Task 2: 70-smoke.sh)
- **Files created:** 2 (both in-repo documentation + bash)

## Accomplishments

- **Phase 76 audit-traceability input shipped:** `70-VALIDATE-CHECKLIST.md` is a deterministic checklist Phase 76 VALIDATE consumes as its audit input. Without this, Phase 76 would have had to reverse-engineer assertions from RESEARCH.md — risking the terminology drift (source_sha vs `lineage.skill_sha256`) that PITFALL 1 warns about
- **6 XCUT-01 sub-claim rows:** a (inventory exists) / b (6 SKILL.md entries) / c (cross-repo pins) / d (curator freeze) / e (STATE.md freeze block) / f (this checklist drafted) — each maps to an automated smoke command with expected result
- **4 hard-constraint preservation sections:** INFRA-04 (MAX_CONCURRENT_GL=1, no asyncio.gather on GLM paths), EVAL-06 (curator dry-run-first, freeze released post-Phase-75), FOUND-08 (15 expert_id frozen, zero new transition_designer), SKILL.md L1-L6 read-only exception破例 reconciliation
- **Cross-repo commit pin assertion procedure:** 5-step re-hash procedure from pinned `d9620369e48eec51c31ee72ac8827c288eaccf71` (kais-hermes-skills) + `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1` (hermes-agent) using the canonical algorithm from `scripts/transform_skill_to_agent.py:232-240`
- **Canonical field-name discipline callout:** block-quote warning that Phase 76 MUST grep for `lineage.skill_sha256` (NOT `source_sha`), `lineage.transform_notes` (NOT `transform_rule_id`), `lineage.transform_date` (NOT `transform_timestamp`). Grepping the roadmap shorthand finds nothing — the assertion silently passes on an empty set (false-green)
- **META-RULE X-2 audit rows:** XCUT-02 preparation — for each MUST/MUST NOT added to SKILL.md in Phases 71-74, Phase 76 verifies a matching `_INSTRUCTION` constant + test exists (CI gate `grep MUST SKILL.md | wc -l == count_constraints(goal)`)
- **Bash smoke runner shipped:** `70-smoke.sh` executes all 6 XCUT-01 assertions with `set -euo pipefail` hard-fail semantics, REPO_ROOT resolution via `BASH_SOURCE`, quoted variable expansions, and `grep -c ... || true` guards against `set -e` on zero matches. Exits 0 only if all 6 pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Write Phase 76 VALIDATE-CHECKLIST.md with 6 XCUT-01 rows + hard-constraint preservation rows** — `6e4cba4e4` (docs)
2. **Task 2: Write 70-smoke.sh bash runner executing all 6 XCUT-01 assertions** — `f665e98df` (feat)

## Files Created/Modified

### Created

- `.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` (192 lines, 34 table rows)
  - XCUT-01 sub-claim verification table (6 rows a-f)
  - INFRA-04 preservation section (3 rows: asyncio.gather audit, MAX_CONCURRENT_GL pin check, transition routing manual audit)
  - EVAL-06 preservation section (3 rows: config flag state, audit log inspection, is_enabled() post-release)
  - FOUND-08 preservation section (4 rows: agent.yaml count, expert_id count, skills/ directory audit, transition_designer grep)
  - SKILL.md L1-L6 exception破例 reconciliation section (3 rows: commit-scope audit, agent.yaml refresh count, byte-for-byte hash match)
  - Cross-repo commit pin assertion procedure (5 steps with bash snippets + expected SHA table)
  - META-RULE X-2 audit section (3 rows for XCUT-02: MUST count diff, _INJECTION verification, test assertion existence)
  - Canonical field-name discipline callout (PITFALL 1 warning block-quote)
  - Phase 76 audit summary template

- `.planning/phases/70-foundation-audit/70-smoke.sh` (79 lines, 3.4KB)
  - Shebang + `set -euo pipefail` at line 3 (passes `head -3 | grep` acceptance criterion)
  - REPO_ROOT resolution via `cd "$SCRIPT_DIR/../../.." && pwd` (3 levels up)
  - 6 assertion blocks (XCUT-01a through XCUT-01f)
  - `grep -c ... || true` guards (survives `set -e` on zero matches)
  - All variable expansions double-quoted (CLAUDE.md bash discipline)
  - Final summary line on all-pass

## Decisions Made

1. **Checklist structure hand-rolled from RESEARCH spec** — PATTERNS.md `No Analog Found` section explicitly notes no prior `.planning/**/CHECKLIST*.md` exists in the repo. Closest analog is the `Per-Task Verification Map` pattern in `55-VALIDATION.md` / `53-VALIDATION.md`, but those are validation STRATEGY docs (per-task test map), not downstream-phase audit CHECKLISTS. Hand-rolled from RESEARCH.md Validation Architecture > Phase Requirements → Test Map (lines 419-426)

2. **XCUT-01d uses config.yaml grep, not CLI** — the plan offered two options (config.yaml grep OR `hermes curator status` CLI). Chose config.yaml grep because: (a) works without requiring the hermes CLI in the execution environment, (b) the config flag is the canonical freeze mechanism per RESEARCH Pattern 2 (`agent/curator.py:is_enabled()` reads it fresh), (c) `hermes curator status` depends on prompt_toolkit which may not be in scope for Phase 76's CI runner

3. **Status glyphs as literal text** — per CLAUDE.md "avoid emojis" + PATTERNS.md line 77 which cites the `pending/green/red/flaky` convention. Chose literal text over emoji (`pending` not `⬜`) so the checklist renders cleanly in plain-text editors and CI logs

4. **`source_sha` references limited to PITFALL 1 warning** — the acceptance criterion requires `source_sha` to appear ONLY inside the PITFALL 1 warning callout (explaining it is the WRONG name). Verified post-write: 5 occurrences total, all in the callout block-quote or the roadmap-shorthand mapping table. Zero occurrences as a field name in any assertion

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] smoke.sh header comment block pushed `set -euo pipefail` past line 3**
- **Found during:** Task 2 verification
- **Issue:** Initial header was a 10-line comment block (usage + docstring). `set -euo pipefail` landed at line 13. The plan's acceptance criterion `head -3 70-smoke.sh | grep -q "set -euo pipefail"` failed
- **Fix:** Consolidated the header to 2 lines (shebang + one-line purpose comment with usage), pushing `set -euo pipefail` to line 3. Moved the longer docstring below `set -euo pipefail` as inline comments
- **Files modified:** `.planning/phases/70-foundation-audit/70-smoke.sh`
- **Commit:** `f665e98df`

**2. [Rule 3 - Blocking issue] REPO_ROOT path depth corrected from `../..` to `../../..`**
- **Found during:** Task 2 implementation
- **Issue:** The plan's `<action>` block suggested `REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"`. But the script lives at `.planning/phases/70-foundation-audit/70-smoke.sh` — 3 directories deep from repo root. `../..` resolves to `.planning/`, not the repo root
- **Fix:** Used `../../..` (3 levels up). Verified post-write: script prints `Repo root: /home/kai/workspace/hermes-agent` (correct)
- **Files modified:** `.planning/phases/70-foundation-audit/70-smoke.sh`
- **Commit:** `f665e98df`

## Issues Encountered

None beyond the two Rule 3 auto-fixes above.

## User Setup Required

None. Both deliverables are in-repo documentation + bash. No external services, no config changes, no secrets.

## Next Phase Readiness

- **Phase 70 (FOUNDATION-AUDIT)** — COMPLETE (3/3 plans shipped: 01 lineage inventory, 02 curator freeze + STATE.md, 03 VALIDATE-CHECKLIST + smoke.sh). XCUT-01 fully delivered
- **Phase 71 (FORM)** — ready to start. The curator freeze protects against accidental drift during FORM's SKILL.md edits. The VALIDATE-CHECKLIST is ready for Phase 76 consumption
- **Phase 75 (LINEAGE-BUMP)** — will use the cross-repo pin assertion procedure documented in VALIDATE-CHECKLIST.md Step 4 to verify post-bump `lineage.skill_sha256` values match the re-hashed SKILL.md
- **Phase 76 (VALIDATE)** — consumes `70-VALIDATE-CHECKLIST.md` as its deterministic audit input. Re-runs `70-smoke.sh` as a sanity check. Fills in the Phase 76 Audit Summary Template at the bottom of the checklist

**Blockers/concerns:** None. Both deliverables verified — checklist passes all 9 acceptance criteria, smoke.sh passes `bash -n` syntax check + full execution exits 0 with all 6 XCUT-01 assertions passing.

## Operator Action Verification

The operator can verify Phase 70 Plan 03 completion in one command:

```bash
bash .planning/phases/70-foundation-audit/70-smoke.sh
```

Expected output: 6 `OK:` lines + `Phase 70 smoke status: ALL 6 XCUT-01 ASSERTIONS PASSED` + exit 0.

---

*Phase: 70-foundation-audit*
*Plan: 03*
*Completed: 2026-07-09*

## Self-Check: PASSED

- 70-VALIDATE-CHECKLIST.md: FOUND
- 70-smoke.sh: FOUND
- Task 1 commit 6e4cba4e4: FOUND
- Task 2 commit f665e98df: FOUND
- Checklist row count >= 6: OK (34 rows)
- smoke.sh `set -euo pipefail` in head -3: OK
- smoke.sh `bash -n` syntax: OK
- smoke.sh full execution exits 0: OK
- Canonical field name `lineage.skill_sha256` used: OK
- `source_sha` limited to PITFALL 1 warning callout: OK
- Cross-repo pin `d9620369` referenced: OK
- All 4 hard constraints documented (INFRA-04/EVAL-06/FOUND-08/L1-L6): OK
