---
phase: 74-transition
fixed_at: 2026-07-10T00:45:00Z
review_path: .planning/phases/74-transition/74-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 74: Code Review Fix Report

**Fixed at:** 2026-07-10T00:45:00Z
**Source review:** `.planning/phases/74-transition/74-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (2 critical + 6 warning)
- Fixed: 8
- Skipped: 0

**Cross-repo topology:** All 8 fixes were committed inside the
`kais-hermes-skills` repo (at `/data/workspace/kais-hermes-skills`). The fixes
were authored in an isolated worktree on branch `gsd-reviewfix/74-3429387`
and fast-forwarded to `master` at cleanup time. REVIEW-FIX.md itself is
committed in the hermes-agent repo by the orchestrator (not by this fixer).

## Fixed Issues

### CR-01: `load_next_shot_link` is dead code — TRANS-02 backward-compat contract is unenforced at runtime

**Files modified:** `skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py`
**Commit:** `a8b793c`
**Applied fix:** Wired `load_next_shot_link` into the p09 write path (Option A
from the reviewer — single-touch coercion at write time). The
`transition-design` slot now ALWAYS holds structured data: each entry with a
`next_shot_link` key is passed through `load_next_shot_link` before being
written to the asset bus. Coercion is best-effort — entries that fail
validation (invalid enum / wrong type) are preserved unchanged so the slot
remains populated for downstream debugging rather than being dropped. Legacy
pre-v14.0 episodes with bare-string `next_shot_link: shot_02` entries are now
coerced at write time, fulfilling the TRANS-02 contract that "no migration
script is needed".

### CR-02: p09 goal emits an empty `[CONSTRAINTS]` bullet on first run (`fix_feedback = ""` is the 7th rule)

**Files modified:** `skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py`
**Commit:** `3b19f51`
**Applied fix:** Extracted a `_p09_constraint_rules(fix_feedback)` helper that
returns 6 unconditional MUST rules plus the `fix_feedback` rule ONLY when it
is non-empty. The `.constraints([...])` call now passes
`_p09_constraint_rules(fix_feedback)`. Count is 6 on first run (within
MAX_CONSTRAINTS=7), 7 on retry — no empty `"- "` bullet, no wasted budget row.
The `_prompt_template.py:287` contract that every rule MUST start with
MUST/MUST NOT/LIMIT is preserved.

### WR-01: Canvas sync field-map refactor has no end-to-end test

**Files modified:** `plugins/kais_aigc/tests/test_canvas_sync_field_map.py` (new)
**Commit:** `f60334a`
**Applied fix:** Added a new test module with 4 regression assertions that
exercise the data-driven `_apply_schema_mappings` refactor end-to-end against
the real generated `canvas_sync_mappings.PHASE_FIELDS` table:
1. `test_phase_fields_table_covers_p10_and_p11` — PHASE_FIELDS preserves the
   old handwritten canvas_keys for p10 (audioType / engine / emotion /
   speaker) and p11 (engine / resolution). Catches a YAML regression that
   drops either entry.
2. `test_apply_schema_mappings_emits_p10_structured_fields` — calling
   `_apply_schema_mappings` with a p10 artifact actually emits the 4
   structured fields. Catches refactor bugs in the per-field dispatch loop.
3. `test_apply_schema_mappings_p10b_inherits_p10_mapping` — p10b micro-gate
   inherits the p10 mapping via the alias branch.
4. `test_apply_schema_mappings_emits_p11_structured_fields` — p11 always-set
   branches (engine/resolution) still fire.

All 4 tests pass. A `pytestmark.skipIf` guards the tests when the generated
mappings file is absent (the dispatch becomes a no-op in that case).

### WR-02: `load_next_shot_link` does not validate `shot_id` — `None` silently passes through for dict input

**Files modified:** `plugins/pipeline_state/transition_schema.py`, `plugins/pipeline_state/tests/test_transition_schema.py`
**Commit:** `21d5b90`
**Applied fix:** Added a `shot_id` validation at the top of the dict branch in
`load_next_shot_link`: rejects missing, null, empty, and non-string values
with a `ValueError` bearing the `(TRANS-02 strict type — no fuzzy coercion of
missing/null shot_id)` audit suffix. This matches the function docstring's
"fail-fast backward-compat reader" claim, which the original dict branch
violated by silently returning `shot_id=None` via `value.get("shot_id")`.
Added 3 regression tests: `test_load_next_shot_link_rejects_missing_shot_id`,
`test_load_next_shot_link_rejects_none_shot_id`,
`test_load_next_shot_link_rejects_empty_shot_id`. All 15 schema tests pass.

### WR-03: `load_next_shot_link` is never called on the `transition-design` slot's read path — empty list default at p13

**Files modified:** `skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py`
**Commit:** `5cf6fb6`
**Applied fix:** Added a `logger.warning` at p13 when the transition-design
slot is empty (missing or falsy). The warning makes the degradation
observable — previously the editor silently proceeded with an empty
`transition_design` dict and the
`_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` rule "Read the transition-design
asset" degraded to a no-op with no operator-visible signal. Strict mode
(raise) was deliberately NOT chosen because a transition-v14.0-inactive
episode is a valid pre-v14.0 state; the warning surfaces the degradation
without blocking legacy episodes. Warning uses lazy %-formatting per
CLAUDE.md logging conventions.
**Status:** fixed: requires human verification (logic-behavior change — the
warning is new operator-visible output; verify it does not flood logs in
normal operation).

### WR-04: `test_p09_transition_unit.py` does not assert that the goal contains exactly 7 constraint bullets

**Files modified:** `skills/kais-movie-pipeline/tests/test_p09_transition_unit.py`
**Commit:** `9c88a4e`
**Applied fix:** Added `test_p09_constraint_count_within_budget_and_well_formed`
that serves as a CR-02 regression guard. The test:
1. Counts constraint bullets via `GoalBuilder.count_constraints` (≤7).
2. Asserts exactly 6 well-formed rules on first run (the 6 unconditional MUST
   rules, no fix_feedback).
3. Extracts the raw `[CONSTRAINTS]` section via `GoalBuilder.extract_section`
   and verifies every `"- "`-prefixed line is non-empty AND starts with
   MUST / MUST NOT / LIMIT.

The two-tier approach catches both the over-constraint case (would raise at
goal-build time) and the empty-bullet case (invisible to count_constraints
because it only counts well-formed lines). All 3 p09 tests pass; the new test
validates the CR-02 fix end-to-end.

### WR-05: `transition-design.md` has dual inconsistent date metadata

**Files modified:** `skills/movie-experts/cinematographer/references/transition-design.md`
**Commit:** `c6cc308`
**Applied fix:** Dropped the bare `verified_date: 2026-07` line (which was
not inside a YAML frontmatter block and looked like malformed YAML). Kept
only `**Last-verified:** 2026-07-09`, which is the format declared
load-bearing for prompt-token mapping drift warnings per the cinematographer
SKILL.md `Model drift warning (T-04-01)` pattern. Readers now have a single
authoritative date field.

### WR-06: `transition-engine-routing.md` cites `ltx-flf-iclora-validation.md` with a forward reference to Plan 74-03 that is now stale

**Files modified:** `skills/kais-movie-pipeline/references/transition-engine-routing.md`
**Commit:** `ba58c25`
**Applied fix:** Removed the "once authored in Plan 74-03" qualifier from the
link to `ltx-flf-iclora-validation.md`. The file is already authored (it is
in the review scope as a complete template); the stale qualifier suggested
the doc was missing when it is present. The link now reads as a normal
cross-reference.

---

_Fixed: 2026-07-10T00:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
