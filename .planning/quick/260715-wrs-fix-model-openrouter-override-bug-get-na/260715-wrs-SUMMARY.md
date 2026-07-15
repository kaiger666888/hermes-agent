---
phase: quick
plan: 260715-wrs
subsystem: runtime-provider-resolution
tags: [bugfix, model-override, openrouter, gateway, runtime-provider]
requires:
  - "config.yaml providers: dict support (v11 migration)"
provides:
  - "Config-defined canonical providers (providers.openrouter) resolve to user's inline api_key"
  - "Truthy gate on _apply_session_model_override prevents empty-string clobbering"
affects:
  - "gateway/run.py _apply_session_model_override"
  - "hermes_cli/runtime_provider.py _get_named_custom_provider"
tech-stack:
  added: []
  patterns:
    - "config-scan-before-canonical-short-circuit (providers: dict wins over built-in for canonical names)"
    - "truthy-override-gate (falsy values cannot clobber runtime_kwargs)"
key-files:
  created: []
  modified:
    - hermes_cli/runtime_provider.py
    - gateway/run.py
    - tests/hermes_cli/test_runtime_provider_resolution.py
    - tests/gateway/test_session_model_override_routing.py
decisions:
  - "providers: dict (new-style) scan moved BEFORE canonical short-circuit; custom_providers: (legacy list) stays AFTER — preserves does_not_shadow/skipped_for_canonical test semantics while fixing config-defined canonical provider resolution"
  - "Truthy `if val:` gate chosen over `if val is not None:` because empty-string is the documented failure payload from /model resolution"
metrics:
  duration: 521s
  completed: 2026-07-15
  tasks: 1
  files: 4
---

# Phase quick Plan 260715-wrs: /model openrouter override regression fix Summary

Fixed two coordinated bugs that caused "No LLM provider configured" after running `/model nvidia/...:free` in a Telegram session — Bug 1: canonical-provider short-circuit ignored user's `providers.openrouter` config entry; Bug 2: empty-string override values clobbered valid config credentials.

## What Was Built

### Bug 1 Fix (hermes_cli/runtime_provider.py)

**Root cause:** `_get_named_custom_provider` had the canonical-provider short-circuit (`resolve_provider('openrouter') == 'openrouter' → return None`) running BEFORE the `providers:` dict scan. A user with `providers.openrouter.api_key` set inline in config.yaml was silently ignored — resolution fell through to `OPENROUTER_API_KEY` env var (not set), producing `auth_unavailable`.

**Fix:** Moved the `providers:` dict (new-style) scan to BEFORE the canonical short-circuit. The `custom_providers:` list (legacy) scan stays AFTER the canonical check. This means:
- `providers.openrouter` (new-style dict) → dict scan finds it → user's inline key returned (BUG FIXED)
- `custom_providers: [{name: nous}]` (legacy list) → dict scan finds nothing → canonical check fires → None (EXISTING BEHAVIOR PRESERVED)
- `custom_providers: [{name: kimi}]` (legacy alias) → dict scan finds nothing → canonical check passes (kimi is alias not canonical) → list scan finds kimi → returned (EXISTING BEHAVIOR PRESERVED)

### Bug 2 Fix (gateway/run.py)

**Root cause:** `_apply_session_model_override` used `if val is not None:` to gate `runtime_kwargs` clobbering. When `/model` resolution failed upstream, the override dict carried `api_key=""` / `base_url=""`. Empty string is `not None` → True, so the loop overwrote valid config credentials with empty strings.

**Fix:** Changed `if val is not None:` to `if val:` (truthy check). Empty strings, None, and other falsy values no longer clobber existing `runtime_kwargs` entries. Non-empty legitimate values (`"***"` api_key, real base_url) still override correctly. Updated docstring to reflect the new semantics.

### Regression Tests (4 new)

- `test_named_custom_provider_openrouter_wins_via_providers_dict` — Bug 1 direct regression: `providers.openrouter` with inline `api_key`, `OPENROUTER_API_KEY` unset → returns config entry (NOT None)
- `test_named_custom_provider_normalized_name_matches_providers_dict` — Bug 1 defensive: normalized name `open_router` matches via `_normalize_custom_provider_name`
- `test_apply_session_model_override_empty_strings_do_not_clobber` — Bug 2 direct regression: empty-string override does NOT clobber valid `runtime_kwargs`
- `test_apply_session_model_override_truthy_values_still_clobber` — Bug 2 guard: non-empty override values DO clobber (prevents over-tightening the gate)

## Verification Results

- `tests/hermes_cli/test_runtime_provider_resolution.py`: 131 passed (129 pre-existing + 2 new), 0 failed
- `tests/gateway/test_session_model_override_routing.py`: 6 passed (4 pre-existing + 2 new), 0 failed
- Ruff PLW1514: All checks passed on all 4 touched files
- ty (advisory): No new diagnostics in modified line ranges (138 pre-existing diagnostics in untouched code)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Refined fix approach to preserve all existing tests**

- **Found during:** Task 1, RED phase analysis
- **Issue:** The plan's literal instruction ("move canonical short-circuit to AFTER both `providers:` dict AND `custom_providers:` list scans") would have broken two existing tests: `test_named_custom_provider_does_not_shadow_builtin_provider` and `test_named_custom_provider_skipped_for_canonical_built_in`. Both tests use the legacy `custom_providers:` list with canonical names ("nous") and expect None (built-in wins). Moving the canonical check past the legacy list scan would return the user's "nous" entry instead.
- **Fix:** Scoped the canonical-check relocation to the `providers:` dict (new-style) only. The `providers:` dict now scans before the canonical check; the `custom_providers:` list still scans after it. This satisfies all three must_have truths AND preserves all 131 pre-existing tests.
- **Files modified:** hermes_cli/runtime_provider.py
- **Commit:** 4e0a25bca

## Self-Check: PASSED

- [x] hermes_cli/runtime_provider.py — exists, modified (Bug 1 fix applied)
- [x] gateway/run.py — exists, modified (Bug 2 fix applied)
- [x] tests/hermes_cli/test_runtime_provider_resolution.py — exists, 2 new tests added
- [x] tests/gateway/test_session_model_override_routing.py — exists, 2 new tests added
- [x] Commit 4e0a25bca found in git log
- [x] All 137 tests pass (131 + 6)
- [x] Ruff PLW1514 clean
