---
phase: 00-audit-eval-skeleton-blocker-gate
fixed_at: 2026-06-15T00:00:00Z
review_path: .planning/phases/00-audit-eval-skeleton-blocker-gate/00-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 0: Code Review Fix Summary

**Fixed at:** 2026-06-15
**Source review:** `.planning/phases/00-audit-eval-skeleton-blocker-gate/00-REVIEW.md`
**Iteration:** 1
**Scope:** Critical + Warning (Info items excluded per default scope)

## Summary

- Findings in scope: 9 (2 Critical + 7 Warning; WR-06 was demoted to IN-03 in the REVIEW itself)
- Fixed: 9
- Skipped: 0
- Tests: 41 pass (28 baseline + 13 new)

## Fixed Issues

### CR-01: Phantom denylist (Critical)

**Files modified:** `scripts/verify_skill_references.py`, `scripts/tests/test_verify_skill_references.py`
**Commit:** `3e6ccccdc`
**Applied fix:** Added module-level `_PHANTOM_DENYLIST = frozenset({"wan22_video", "wan22_video_turbo", "wan22", "168k controlled tokens"})`. In `scan_skill_file`, denylist tokens are flagged unconditionally BEFORE the allowlist check, so no operator override can suppress them. Renamed `_VENDOR_TOKEN_RE` to `_VENDOR_CANDIDATE_RE` with a clarified docstring stating "Detection regex — yields candidate tokens that are then checked against the allowlist. Does NOT itself whitelist anything." Added 2 tests: `test_phantom_denylist_cannot_be_overridden`, `test_phantom_denylist_includes_bare_wan22`.

### CR-02: Untracked expert detection (Critical)

**Files modified:** `skills/movie-experts/_eval/snapshot.py`, `skills/movie-experts/_eval/tests/test_snapshot.py`
**Commit:** `c5a9f6d2c`
**Applied fix:** After the existing missing-expert check in `capture_baselines`, added a symmetric check that walks `skills_dir.iterdir()` for directories containing `SKILL.md` (excluding `_`-prefixed names). If any live expert dir is not in `EXPERT_DIRS`, raises `RuntimeError` listing the untracked dirs. Added 2 tests: `test_capture_fails_on_untracked_expert_dir`, `test_capture_ignores_underscore_prefixed_dirs`.

### WR-01: snapshot.py docstring clarity

**Files modified:** `skills/movie-experts/_eval/snapshot.py`
**Commit:** `c5ef342e7`
**Applied fix:** Changed "stdlib only (no new packages)" to "stdlib only (no third-party packages). Uses `subprocess` to invoke `git rev-parse` for provenance; degrades gracefully to the literal `\"uncommitted\"` if git is unavailable." This resolves both WR-01 and the demoted CR-03.

### WR-02: _StubJudgeClient refactor

**Files modified:** `skills/movie-experts/_eval/runner.py`, `skills/movie-experts/_eval/tests/test_runner.py`
**Commit:** `552b239b5`
**Applied fix:** Refactored `_StubJudgeClient` from nested-class-with-class-attrs to instance-based with `__init__` constructing `self.chat = self._Chat()`. Kept `_Completions.create` as `@staticmethod` (matches OpenAI client contract). Added 2 tests: `test_stub_returns_position_bias_pattern`, `test_stub_judge_client_instances_independent`.

### WR-03: Fail-fast on non-dry-run mode

**Files modified:** `skills/movie-experts/_eval/runner.py`, `skills/movie-experts/_eval/tests/test_runner.py`
**Commit:** `c639f1516` (combined with WR-04)
**Applied fix:** Merged the two separate `if args.dry_run` blocks in `main()` into one branch. The `else` branch now logs an error and `return 2` instead of silently falling through to `_stub_answers`. Added 1 test: `test_main_rejects_live_mode_without_dry_run`.

### WR-04: Fail-fast on empty OPENROUTER_API_KEY

**Files modified:** `skills/movie-experts/_eval/runner.py`, `skills/movie-experts/_eval/tests/test_runner.py`
**Commit:** `c639f1516` (combined with WR-03)
**Applied fix:** In `make_judge_client`, when `api_key == ""`, raises `RuntimeError("OPENROUTER_API_KEY is not set. Set it in ~/.hermes/.env or your shell, or use --dry-run.")` instead of constructing an OpenAI client with an empty key. Added 1 test: `test_make_judge_client_raises_on_missing_api_key`.

### WR-05: Verify tokenization test (resolved reviewer uncertainty)

**Files modified:** `scripts/verify_skill_references.py`, `scripts/tests/test_verify_skill_references.py`
**Commit:** `825f167d8`
**Applied fix:** Ran the test — it passes. The reviewer's trace was based on an assumption that the test asserts `"flux" in allowlist`, but the actual assertions check `"veo"` and `"kling"` (which come from a different plugin description that does split on whitespace/commas). The `"flux-2-pro"` description does contribute `flux-2-pro` as one hyphenated token. Added a docstring to `_tokenize_description` documenting hyphen behavior, and fixed the misleading test comment that claimed "we get: flux, pro, etc." Added an assertion that `flux-2-pro` (the actual token) is in the allowlist.

### WR-07: plugin.yml support

**Files modified:** `scripts/verify_skill_references.py`, `scripts/tests/test_verify_skill_references.py`
**Commit:** `17aeb7e60`
**Applied fix:** Modified `_walk_plugin_yamls` to check both `plugin.yaml` and `plugin.yml` (first found wins). Added 2 tests: `test_walk_plugin_yamls_accepts_plugin_yml`, `test_walk_plugin_yamls_prefers_yaml_when_both_exist`.

### WR-08: PROVENANCE.json schema validation

**Files modified:** `skills/movie-experts/_eval/snapshot.py`, `skills/movie-experts/_eval/tests/test_snapshot.py`
**Commit:** `16f27baf4`
**Applied fix:** In `verify_baselines`, after loading provenance JSON, checks that all `_REQUIRED_PROVENANCE_KEYS` are present and that `provenance.get("tag") == BASELINE_TAG`. On failure, appends a drift entry with a descriptive message. Added 2 tests: `test_verify_flags_missing_provenance_keys`, `test_verify_flags_wrong_tag`.

### WR-09: Markdown pipe escaping

**Files modified:** `skills/movie-experts/_eval/runner.py`, `skills/movie-experts/_eval/tests/test_runner.py`
**Commit:** `8c7c65a69`
**Applied fix:** Added `_md_escape(s)` helper that replaces `|` with `\|`. Applied to all interpolated values (`prompt_id`, `pair_str`, `winner`, `judge`) in the Markdown table row. Added 1 test: `test_format_results_escapes_pipes`.

## Skipped Issues

None — all in-scope findings were fixed.

WR-06 was demoted to IN-03 within the REVIEW.md itself (re-traced as correct). IN-01 through IN-04 are Info-tier items outside the default fix scope.

---

_Fixed: 2026-06-15_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
