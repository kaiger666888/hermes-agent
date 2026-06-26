# Phase 42 Deferred Items

Out-of-scope discoveries logged during phase execution. Not fixed by the
discovering plan per scope discipline.

---

## Plan 42-03 — test_library_writer.py failing (6 tests)

**Discovered by:** Plan 42-04 executor (during post-task verification)
**Date:** 2026-06-27
**Owner:** Plan 42-03 (tuning_loop + library_writer)

**Symptom:**
```
FAILED plugins/platform_metrics/tests/test_library_writer.py::test_apply_suggestion_updates_eval_score
FAILED plugins/platform_metrics/tests/test_library_writer.py::test_apply_suggestion_preserves_other_fields
FAILED plugins/platform_metrics/tests/test_library_writer.py::test_apply_suggestion_unknown_formula_id_raises
FAILED plugins/platform_metrics/tests/test_library_writer.py::test_apply_suggestion_atomic_temp_cleanup_on_failure
FAILED plugins/platform_metrics/tests/test_library_writer.py::test_apply_suggestion_returns_commit_sha
FAILED plugins/platform_metrics/tests/test_library_writer.py::test_apply_suggestion_triggers_move_to_applied
```

**Root cause (preliminary):** `test_library_writer.py` constructs
`TuningSuggestion(status='approved', ...)` but `schema.py:TuningSuggestion`
declares `status: Literal["pending", "applied", "rejected"]`. The
`'approved'` value fails Pydantic literal validation.

**Why Plan 42-04 did NOT fix:** `test_library_writer.py` is owned by Plan
42-03 (commit `66597a1f3` — RED test commit). The 6 failures are Plan
42-03's RED gate waiting for its GREEN implementation; they will resolve
when Plan 42-03 ships `library_writer.py` with the correct status handling
(either change tests to use `'applied'`, or change the schema Literal to
include `'approved'`). Either way, it is Plan 42-03's call.

**Impact on Plan 42-04:** None. `cli.py` does not import `library_writer`
and the CLI's `--json` mode does not surface `apply_suggestion` output.
All 9 `test_cli.py` tests GREEN; FOUND-08 preserved; all Plan 42-04
deliverables shipped.

---

*Last updated: 2026-06-27 by Plan 42-04 executor.*
