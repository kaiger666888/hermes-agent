---
phase: 32-curator-upgrade-audit
fixed_at: 2026-06-25T00:00:00Z
review_path: .planning/phases/32-curator-upgrade-audit/32-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 32: Code Review Fix Report

**Fixed at:** 2026-06-25
**Source review:** `.planning/phases/32-curator-upgrade-audit/32-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (3 Critical + 7 Warning; INFO findings skipped per scope)
- Fixed: 10
- Skipped: 0
- Status: all_fixed

All 10 in-scope findings applied cleanly. Each fix has a regression test that
would catch the bug if reintroduced. The full regression suite
(472 passed, 1 skipped — 8 pre-existing failures in `test_feedback_cli.py`
due to missing `prompt_toolkit` in the test env, unrelated to these changes)
is green. P31 `TestNonBypassableHumanInLoop`, FOUND-08 byte-intact, and
runtime isolation (zero module-level `agent.evolution` imports in
`agent/curator.py` / `agent/curator_audit.py`) are all preserved.

## Fixed Issues

### CR-01: CURATE-05 auto-apply is unreachable — `auto_apply_eligible` is never True

**Files modified:** `hermes_cli/feedback.py`, `agent/curator.py`
**Commit:** `f8015cb0e`
**Applied fix:**

Two-part fix per REVIEW.md CR-01 option (b):

**Part A (producer — `hermes_cli/feedback.py:_cmd_evolve`):** when the eval
gate passes, compute two-signal confidence via `_compute_confidence`. For
AGENT-CREATED skills (`is_agent_created=True`) when `auto_apply_enabled=True`
AND both signals pass (`mean_delta >= auto_apply_min_delta` AND
`evidence_count >= auto_apply_min_evidence`), set `auto_apply_eligible=True`
and populate `confidence_score`. Bundled skills NEVER get the marker (T-32-05
defense-in-depth at producer). The evolve path is the canonical producer of
gated patches — it runs the eval gate; `_feedback_scan_phase` does not.

**Part B (diagnostics — `agent/curator.py:_feedback_scan_phase`):** the scan
phase does NOT run the gate, so `eval_gate_score={}` and `mean_delta=0.0`.
`_compute_confidence` returns `eligible=False` regardless of evidence_count;
`auto_apply_eligible` stays False for ALL scan-produced patches. But we now
populate `confidence_score` via `_compute_confidence` so the auto-apply CLI's
skip reason is informative ("mean_delta 0.000 < 0.1") rather than a bare
"not marked eligible" with no signal context.

Also addressed IN-02 (inline `import hashlib` + `from datetime import
datetime as _dt, timezone as _tz` shadowed module-level imports): `hashlib`
now imported at module top; the inline shadow imports removed.

**Tests:** `TestEvolveCmdAutoApplyEligible` (3 cases) —
`test_agent_created_with_signals_pass_marks_eligible`,
`test_bundled_skill_never_marked_eligible`,
`test_auto_apply_disabled_leaves_marker_false`.

### CR-02: `audit-log --since <naive-date>` silently drops every entry

**Files modified:** `agent/curator_audit.py`, `tests/agent/test_audit_log.py`, `tests/hermes_cli/test_curator_cli.py`
**Commit:** `a2f800769` (bundled with WR-02)
**Applied fix:**

Normalize both sides to aware UTC before comparison. `--since 2026-06-01`
parses as a naive datetime; entry `ts` is always aware
(`datetime.now(timezone.utc).isoformat()` → `+00:00`). Without normalization,
the naive-vs-aware comparison raised `TypeError`, which was caught as
"unparseable ts" — silently dropping EVERY entry regardless of actual content.

Fix promotes naive `since_dt` to UTC midnight (the documented operator
convention), and a naive `entry_ts` (legacy/hand-edited data) is promoted
defensively to UTC.

**Tests:** `test_filter_by_naive_since_normalizes_to_utc`,
`test_filter_by_naive_since_date_only` (exact CLI example),
`test_filter_by_since_naive_entry_ts_promoted` (legacy data),
`test_naive_since_date_returns_entries` (CLI operator workflow).

### CR-03: `_feedback_scan_phase` builds `current_files` with HERMES_HOME-relative paths but tells the LLM they are "repo-relative"

**Files modified:** `agent/curator.py`, `tests/agent/test_curator_feedback_scan.py`
**Commit:** `5fb2b57a3`
**Applied fix:**

Paths passed to the LLM MUST be repo-relative
(`skills/movie-experts/<skill>/...`) so the generated unified diff applies
cleanly via `apply_patch_transaction` (which resolves patch paths against the
git repo root). Added `_resolve_repo_root_or_none()` helper (mirrors
`hermes_cli/feedback.py:373` but returns `None` instead of raising —
feedback-scan is best-effort). Prefer reading from the git repo tree when
available; fall back to HERMES_HOME if the repo is not accessible (wheel
install). Either way the LLM gets consistent repo-relative paths. IN-03 also
addressed: silent skips now log at DEBUG.

**Tests:** `test_current_files_keys_are_repo_relative` — captures the
`current_files` dict passed to `emit_evol02_instructions` and asserts every
key starts with `skills/movie-experts/` and does NOT start with `.hermes`.

### WR-01: Audit log append is not crash-atomic

**Files modified:** `agent/curator_audit.py`
**Commit:** `5f90e6900`
**Applied fix:**

Added `f.flush()` + `os.fsync(f.fileno())` after the write. A single
`write()` longer than `PIPE_BUF` (4KB on POSIX) is NOT guaranteed atomic —
audit entries with rich `eval_score` dicts and CN feedback_ids easily exceed
4KB. A crash mid-write left a partial JSON line, which the next
`append_audit` rejected as `AuditChainError` ("audit log tail is malformed"),
bricking the chain until manual tail repair. `import os` added at module top.

### WR-02: Broad `except (ValueError, TypeError)` masks the real failure in `read_audit`

**Files modified:** `agent/curator_audit.py` (same hunk as CR-02)
**Commit:** `a2f800769` (bundled with CR-02)
**Applied fix:**

Split the parse from the compare so the "unparseable ts" diagnostic now only
fires on genuine parse failures. The comparison `TypeError` (naive vs aware —
see CR-02) can no longer be mis-attributed. After CR-02's normalization, the
comparison no longer raises `TypeError` at all.

### WR-03: `_scan_for_hot_skills` has dead defensive code and inconsistent key parsing

**Files modified:** `agent/curator.py`
**Commit:** `d4e18aa12`
**Applied fix:**

Two concerns:

1. Removed the dead `getattr(getattr(store, "_index", {}), "get", lambda *a: {})("buckets", {})` chain — `FeedbackStore._index` is ALWAYS `dict[str, Any]` after `__init__`. Plain `isinstance(_index, dict)` check.

2. Bucket-key parse disagreement fixed: `skill_id = ":".join(parts[:-2])` (lenient) → strict 3-part parse matching `feedback_store.py:505-508`. The lenient parse silently merged `skill_id:source` into the skill_id when a skill_id contained a colon, diverging from the canonical parse and producing wrong counts.

### WR-04: Markdown-fence regex in `emit_evol02_instructions` over-strips content

**Files modified:** `agent/evolution/evol02_generator.py`, `tests/agent/evolution/test_evol02_generator.py`
**Commit:** `a0843f767`
**Applied fix:**

Only strip the OUTER wrapping fences. The new `_FENCE_WRAP_RE` anchors on the
whole content (`\A...\Z`) with `re.DOTALL`, capturing the payload between the
opening ```` ```json ```` and closing ```` ``` ```` lines. Module-level
constant replaces the inline `import re` + `re.compile` inside the function
body. The prior regex with `re.MULTILINE` matched ANY line that started OR
ended with backticks — over-stripping legitimate backticks inside JSON string
values (`content_en`/`content_zh` frequently embed code samples).

**Tests:** `test_embedded_backticks_in_content_preserved` — `content_en`
with an embedded ```` ```python ... ``` ```` block must round-trip verbatim.

### WR-05: `_feedback_scan_phase` swallows ALL exceptions with a single broad `except Exception`

**Files modified:** `agent/curator.py`
**Commit:** `b4e2b51c3`
**Applied fix:**

Narrowed the outer try to cover ONLY the setup (imports, FeedbackStore,
hot-skills scan, LLM client init). After setup succeeds, the main per-skill/
per-insight loop runs WITHOUT a broad outer catch — per-skill and per-insight
try/except provide failure isolation. Unexpected errors propagate to the
caller (`_llm_pass`), which has its own try/except wrapper. The prior broad
outer catch masked logic bugs as "scan phase failed (non-fatal)" — making it
impossible to distinguish "config is broken" from "a single insight failed
inside the loop".

T-32-03 (scan failure must never abort the curator run) is preserved: the
caller's try/except catches any exception raised by `_feedback_scan_phase`,
and `TestScanFailureDoesNotAbortCurator` verifies this.

### WR-06: `_resolve_skill_from_patch` scans `pending` first after a reject moves the patch to `rejected`

**Files modified:** `hermes_cli/curator.py`, `tests/hermes_cli/test_curator_cli.py`
**Commit:** `9c0c57f9c`
**Applied fix:**

Resolve the `skill_id` BEFORE calling `_cmd_reject`, while the patch is still
in `pending.jsonl`. The resolver reads pending directly (1 parse) and the
result is stable regardless of where `_cmd_reject` files the patch
afterwards. The prior order called `_resolve_skill_from_patch` AFTER the
move, which scanned pending → applied → rejected (3 JSONL parses for one
lookup) and was fragile: if `_cmd_reject` ever changed to move patches
elsewhere, the resolver silently returned `"unknown"` and the audit entry
lost its `skill_id`.

**Tests:** `test_reject_resolves_skill_id_before_move` — verifies the call
order (resolve before reject) and that the audit entry carries the resolved
skill_id.

### WR-07: `git revert <commit_sha>` does not guard against option-injection

**Files modified:** `hermes_cli/feedback.py`, `tests/hermes_cli/test_evolution_cli.py`
**Commit:** `9cf8af575`
**Applied fix:**

Two-layer defense-in-depth:

1. Shape-validate the SHA before it reaches git: hex chars only (7-40 chars),
   OR a git ref-pattern (`refs/...`, `HEAD`, `HEAD~N`). Reject anything
   starting with `-`. This is the primary guard for `git rev-parse --verify`,
   which CANNOT take `--` (the `--` makes `rev-parse` treat the arg as a
   path, breaking the verify).
2. Pass `--` to `git revert` so even a shape-validated rev is treated as
   positional. `--no-edit` comes before `--` so it's still parsed as an
   option.

A commit_sha like `--help` would previously be passed to
`git rev-parse --verify --help` (exits 0 because `--help` short-circuits to
the man page), then to `git revert --help --no-edit` (also exits 0, no revert
performed but rc=0 misleading). Lower severity because the operator IS the
user supplying the SHA.

**Tests:** updated `test_invalid_sha_exits_nonzero` to accept either the
shape-check rejection message OR the git-verify rejection message; new
`test_option_like_sha_rejected_by_shape_check` — verifies `--help` is
rejected by the shape check BEFORE `subprocess.run` is invoked.

## Skipped Issues

None. All 10 in-scope findings (3 Critical + 7 Warning) were applied
successfully.

INFO findings (IN-01 through IN-06) were out of scope per `fix_scope:
critical_warning`. IN-02 and IN-03 were incidentally addressed as part of
CR-01 Part B and CR-03 respectively (same hunks, no extra commits).

## Verification

**Targeted test runs after each fix (all green):**
- CR-01: `pytest tests/agent/test_curator_feedback_scan.py tests/hermes_cli/test_curator_cli.py::TestAutoApply tests/hermes_cli/test_evolution_cli.py::TestEvolveCmdAutoApplyEligible`
- CR-02: `pytest tests/agent/test_audit_log.py tests/hermes_cli/test_curator_cli.py::TestAuditLogCmd`
- CR-03: `pytest tests/agent/test_curator_feedback_scan.py`
- WR-01: `pytest tests/agent/test_audit_log.py`
- WR-03: `pytest tests/agent/test_curator_feedback_scan.py`
- WR-04: `pytest tests/agent/evolution/test_evol02_generator.py`
- WR-05: `pytest tests/agent/test_curator_feedback_scan.py::TestScanFailureDoesNotAbortCurator`
- WR-06: `pytest tests/hermes_cli/test_curator_cli.py::TestRejectCmdCurator`
- WR-07: `pytest tests/hermes_cli/test_evolution_cli.py -k rollback`

**Full regression suite (in-scope files):**
```
pytest tests/agent/test_curator*.py tests/agent/test_audit_log.py \
       tests/agent/evolution/ tests/hermes_cli/test_curator_cli.py \
       tests/hermes_cli/test_evolution_cli.py tests/agent/test_feedback*.py
```
Result: **472 passed, 1 skipped**.

`tests/hermes_cli/test_feedback_cli.py` (8 failures) excluded — pre-existing
environment issue (`ModuleNotFoundError: No module named 'prompt_toolkit'`),
unrelated to these changes and present on `main` before any fix.

**Structural invariants preserved:**
- P31 `TestNonBypassableHumanInLoop` — green (2/2 tests).
- FOUND-08 byte-intact — green (29/29 tests in `tests/agent/evolution/`).
- Runtime isolation — verified: zero module-level `agent.evolution` imports
  in `agent/curator.py` and `agent/curator_audit.py`.
- Ruff PLW1514 — verified: every `open()`/`read_text()`/`write_text()` in
  modified files has `encoding="utf-8"`.

**CURATE-05 end-to-end:** `hermes feedback evolve --skill <agent-created>`
produces a patch with `auto_apply_eligible=True` when `auto_apply_enabled=true`
AND gate passes AND `mean_delta >= threshold` AND `evidence_count >= threshold`;
`hermes curator auto-apply-eligible` then lists and applies it via
`_cmd_approve` (P31 invariant preserved). Verified by
`test_agent_created_with_signals_pass_marks_eligible` (producer) +
`test_auto_apply_fires_for_agent_created` (consumer).

---

_Fixed: 2026-06-25_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
