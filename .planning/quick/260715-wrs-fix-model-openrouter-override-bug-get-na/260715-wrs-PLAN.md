---
phase: quick
plan: 260715-wrs
type: execute
wave: 1
depends_on: []
files_modified:
  - hermes_cli/runtime_provider.py
  - gateway/run.py
  - tests/hermes_cli/test_runtime_provider_resolution.py
  - tests/gateway/test_session_model_override_routing.py
autonomous: true
requirements: [BUGFIX-MODEL-OVERRIDE]
must_haves:
  truths:
    - "User with `providers.openrouter.api_key` in config.yaml can run `/model nvidia/...:free` and subsequent messages in that Telegram session route to OpenRouter using the config-defined key"
    - "Stale session override carrying `api_key=''` / `base_url=''` no longer clobbers valid config credentials in runtime_kwargs"
    - "Canonical built-in providers (nous/openrouter/etc.) WITHOUT a user `providers:` entry still resolve to the built-in (no regression)"
  artifacts:
    - path: "hermes_cli/runtime_provider.py"
      provides: "Bug 1 fix — config scan precedes canonical short-circuit in _get_named_custom_provider"
      contains: "_get_named_custom_provider"
    - path: "gateway/run.py"
      provides: "Bug 2 fix — truthy gate in _apply_session_model_override loop"
      contains: "_apply_session_model_override"
    - path: "tests/hermes_cli/test_runtime_provider_resolution.py"
      provides: "Regression tests for Bug 1 (config-defined canonical provider wins over short-circuit)"
      contains: "test_named_custom_provider"
    - path: "tests/gateway/test_session_model_override_routing.py"
      provides: "Regression tests for Bug 2 (empty-string override does not clobber)"
      contains: "_apply_session_model_override"
  key_links:
    - from: "gateway/run.py:_apply_session_model_override"
      to: "runtime_kwargs passed to _run_agent"
      via: "for-loop over provider/api_key/base_url/api_mode keys"
      pattern: "if val"
    - from: "hermes_cli/runtime_provider.py:_get_named_custom_provider"
      to: "config.yaml providers: dict scan"
      via: "load_config() before canonical return-None"
      pattern: "providers\\.get|config\\.get\\(\"providers\"\\)"
---

<objective>
Fix the "No LLM provider configured" regression that occurs after running `/model nvidia/...` (openrouter) in a Telegram session. Two coordinated one-line-ish fixes prevent bad /model overrides from being created AND prevent bad overrides (from any source) from clobbering valid config credentials.

Purpose: Restore Kai's ability to switch models via `/model` in Telegram without breaking subsequent messages in the same session.
Output: Two patched source files + regression tests in both existing test files, one atomic commit.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

# Exact code locations (do NOT re-investigate — diagnosis is complete)

## Bug 1 — hermes_cli/runtime_provider.py:_get_named_custom_provider (lines ~514-531)

Current (BUGGY) flow at lines 514-531:

```
514  if requested_norm == "auto":
515      return None
516  if requested_norm != "custom" and not requested_norm.startswith("custom:"):
517      try:
518          canonical = auth_mod.resolve_provider(requested_norm)
519      except AuthError:
520          pass
521      else:
522          # ... long comment ...
530          if (canonical or "").strip().lower() == requested_norm:
531              return None     # <-- BUG: bails BEFORE config scan
532
533  config = load_config()
534  # First check providers: dict (new-style user-defined providers) ...
```

For canonical provider names (openrouter/nous/etc.), line 531 returns None *before* the `config = load_config()` scan at line 533. A user who defines `providers.openrouter.api_key` inline is therefore ignored, and resolution falls through to the env-var-only path (which needs OPENROUTER_API_KEY — not set in this case).

**Fix:** Move the canonical-provider short-circuit (lines 530-531) to AFTER the config scan. Concretely: scan `providers:` (new-style dict) and `custom_providers:` (legacy list) first. If a user entry matches, return it (user's explicit config wins). If no entry matches AND the name is a canonical built-in, return None (defer to built-in, preserving existing test `test_named_custom_provider_skipped_for_canonical_built_in`).

This preserves the existing `test_named_custom_provider_does_not_shadow_builtin_provider` and `test_named_custom_provider_wins_over_builtin_alias` semantics: the user-defined entry wins when it matches; the built-in only wins when no user entry matches.

## Bug 2 — gateway/run.py:_apply_session_model_override (lines ~12933-12952)

Current (BUGGY) loop at lines 12948-12951:

```
12948  for key in ("provider", "api_key", "base_url", "api_mode"):
12949      val = override.get(key)
12950      if val is not None:
12951          runtime_kwargs[key] = val
```

`if val is not None` treats empty string as a valid override value. When /model resolution fails upstream, the override dict gets `api_key=""` / `base_url=""`. Empty string is `not None` → True, so the loop overwrites valid config credentials with empty strings → downstream "No LLM provider configured".

**Fix:** Change line 12950 from `if val is not None:` to `if val:` (truthy check). Empty strings, None, and other falsy values will not clobber existing runtime_kwargs entries. Non-empty legitimate values (e.g. "***" api_key, real base_url) still override correctly.

## Why NOT touch model_switch.py / agent_init.py

- Bug 1 PREVENTS bad overrides from being created in the first place (config-defined openrouter key is correctly resolved).
- Bug 2 PREVENTS any bad override (from any source, even pre-existing stale ones) from clobbering good config.
- Together they close the regression fully. Touching agent_init.py's fallback chain is unnecessary scope expansion.
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Fix Bug 1 (config scan precedence) + Bug 2 (truthy override gate) + regression tests</name>
  <files>
    hermes_cli/runtime_provider.py,
    gateway/run.py,
    tests/hermes_cli/test_runtime_provider_resolution.py,
    tests/gateway/test_session_model_override_routing.py
  </files>
  <behavior>
    Bug 1 regressions (in tests/hermes_cli/test_runtime_provider_resolution.py):
    - Test A (new): When config.yaml has `providers.openrouter.{api_key, base_url}` AND `OPENROUTER_API_KEY` env var is UNSET, calling `_get_named_custom_provider("openrouter")` returns a dict with the config's api_key (NOT None). This is the direct regression for the reported bug.
    - Test B (new): Same scenario but user entry name differs in case / uses underscore ("open_router") with `_normalize_custom_provider_name` — matches normalized form, returns config entry. (Defensive — verify normalization path still works post-move.)
    - Preserve existing `test_named_custom_provider_skipped_for_canonical_built_in`: when NO user `providers:` / `custom_providers:` entry matches a canonical name (e.g. "nous" with no config entry), `_get_named_custom_provider("nous")` still returns None. This test already exists — must still pass unchanged.
    - Preserve existing `test_named_custom_provider_does_not_shadow_builtin_provider` and `test_named_custom_provider_wins_over_builtin_alias` — must still pass unchanged.

    Bug 2 regressions (in tests/gateway/test_session_model_override_routing.py):
    - Test C (new): Build a runner via `_make_runner()`, seed `runner._session_model_overrides[session_key]` with a dict carrying `api_key=""` and `base_url=""` (and a real model/provider). Construct `runtime_kwargs = {"provider": "openai-codex", "api_key": "real-key", "base_url": "https://real.example.com/v1", "api_mode": "chat_completions"}`. Call `runner._apply_session_model_override(session_key, "gpt-5.5", dict(runtime_kwargs))`. Assert the returned runtime_kwargs STILL has `api_key == "real-key"` and `base_url == "https://real.example.com/v1"` — empty-string override did NOT clobber.
    - Test D (new): Same setup but override carries real non-empty values (`api_key="override-key"`, `base_url="https://override.example.com/v1"`). Assert those DO clobber (truthy values still override). This guards against over-tightening the gate.
  </behavior>
  <action>
    **WRITE TESTS FIRST (RED), then apply fixes (GREEN):**

    1. Add Test A and Test B to tests/hermes_cli/test_runtime_provider_resolution.py, following the monkeypatch + `rp._get_named_custom_provider(...)` call pattern used by the existing `test_named_custom_provider_uses_saved_credentials` (line 679) and `test_named_custom_provider_skipped_for_canonical_built_in` (line 1008). Each test should:
       - `monkeypatch.setattr(rp, "load_config", lambda: {...})` with a `providers: {openrouter: {api_key, api|base_url, ...}}` dict
       - Ensure `OPENROUTER_API_KEY` env var is explicitly `monkeypatch.delenv(..., raising=False)` so the test does not accidentally pass via env var
       - Call `rp._get_named_custom_provider("openrouter")`
       - Assert the returned dict's `api_key` equals the config-defined value (NOT None)
    2. Add Test C and Test D to tests/gateway/test_session_model_override_routing.py. Use the existing `_make_runner()` and `_codex_override()` helpers (lines 39-76). Call `runner._apply_session_model_override(session_key, model, runtime_kwargs)` directly — no asyncio needed, this is a sync method.
    3. Run the 4 new tests — confirm they FAIL (RED):
       `python -m pytest tests/hermes_cli/test_runtime_provider_resolution.py -k "test_named_custom_provider" -x --no-header -q`
       `python -m pytest tests/gateway/test_session_model_override_routing.py -x --no-header -q`
    4. Apply Bug 1 fix in hermes_cli/runtime_provider.py:
       - DELETE the `if (canonical or "").strip().lower() == requested_norm: return None` block at lines 530-531 from its current position (inside the `else:` branch of the `try: canonical = auth_mod.resolve_provider(...)`)
       - PRESERVE the rest of the `try/except/else` block (it computes `canonical` which we still need)
       - Keep a reference to `canonical` so it is still in scope after the config scan
       - The `config = load_config()` scan at line 533+ stays in place and runs for ALL non-auto, non-custom-prefixed names
       - AFTER the config scan's `providers:` (new-style dict) loop AND the `custom_providers:` (legacy list) loop complete without a match, insert the canonical-defer check at the very end of the function (just before its existing `return None`): `if (canonical or "").strip().lower() == requested_norm: return None`. This makes the built-in only win when no user entry matched.
       - Keep the variable `canonical` reachable at the end — declare it with `canonical = ""` before the `try` block (or reuse the existing flow — `canonical` is already bound in the `else:` branch, but it must be in scope at the end-of-function check). Simplest: initialize `canonical = ""` at the top of the branch, assign inside `else:`.
       - Preserve the comment block (lines 522-529) — move it with the relocated check or leave a pointer comment. Rationale: future readers need to understand WHY canonical names defer to the built-in.
    5. Apply Bug 2 fix in gateway/run.py line 12950: change `if val is not None:` to `if val:`. Update the method's docstring (lines 12937-12943) to reflect the new semantics: change "Fields with ``None`` values are skipped" to "Fields with falsy values (None, empty string) are skipped so failed-resolution overrides do not clobber valid config defaults; only truthy values override."
    6. Run the 4 new tests — confirm they PASS (GREEN).
    7. Run the FULL test files (not just new tests) to confirm no regression:
       `python -m pytest tests/hermes_cli/test_runtime_provider_resolution.py --no-header -q`
       `python -m pytest tests/gateway/test_session_model_override_routing.py --no-header -q`
    8. Run Ruff (CLAUDE.md says PLW1514 is the load-bearing rule — ensure no new `open()` without `encoding="utf-8"`):
       `ruff check hermes_cli/runtime_provider.py gateway/run.py tests/hermes_cli/test_runtime_provider_resolution.py tests/gateway/test_session_model_override_routing.py`
    9. Run ty (advisory per CLAUDE.md, non-blocking but verify no new errors):
       `ty check hermes_cli/runtime_provider.py gateway/run.py 2>&1 | tail -20`
    10. One atomic commit (see `<output>`).
  </action>
  <verify>
    <automated>python -m pytest tests/hermes_cli/test_runtime_provider_resolution.py tests/gateway/test_session_model_override_routing.py --no-header -q && ruff check hermes_cli/runtime_provider.py gateway/run.py tests/hermes_cli/test_runtime_provider_resolution.py tests/gateway/test_session_model_override_routing.py</automated>
  </verify>
  <done>
    - 4 new regression tests added (2 per file), all passing
    - All pre-existing tests in both files still pass (no regressions)
    - Bug 1 fixed: `_get_named_custom_provider("openrouter")` returns user's config-defined entry when `providers.openrouter.api_key` is set, even though `openrouter` is a canonical built-in name
    - Bug 2 fixed: `_apply_session_model_override` skips falsy override values (`""`, None) for provider/api_key/base_url/api_mode, preserving valid runtime_kwargs
    - Ruff PLW1514 clean on all 4 touched files
    - Single atomic commit
  </done>
</task>

</tasks>

<verification>
Direct regression checks (the two lines that broke Kai's session):

1. **Bug 1 integration check** (manual reasoning, not a test): With Kai's config (`providers.openrouter.api_key` set, no `OPENROUTER_API_KEY` env var), `rp._get_named_custom_provider("openrouter")` now returns `{"name": "openrouter", "base_url": <config url>, "api_key": <config key>, ...}` instead of None. Test A asserts this directly.

2. **Bug 2 integration check**: Even if a bad override sneaks through (e.g. stale session state, or a different code path that still creates empty-string overrides), `_apply_session_model_override` no longer clobbers the real `api_key` in runtime_kwargs with `""`. Test C asserts this directly.

3. **Full test sweep**: `python -m pytest tests/hermes_cli/test_runtime_provider_resolution.py tests/gateway/test_session_model_override_routing.py -q` — all green, no skips unaccounted for.

4. **Lint gate**: `ruff check` passes on all 4 touched files (PLW1514 — any new `open()` must have `encoding="utf-8"`).
</verification>

<success_criteria>
- Reported bug scenario (`/model nvidia/...:free` in Telegram → subsequent messages fail with "No LLM provider configured") is structurally impossible post-fix:
  - Bug 1 fix means /model resolution finds the config-defined openrouter key
  - Bug 2 fix means even a bad override cannot clobber valid runtime credentials
- 4 new regression tests (2 + 2) guard against reintroduction
- All pre-existing tests in both test files still pass
- Ruff clean, ty advisory-clean
- One atomic commit with clear message referencing both bugs
</success_criteria>

<output>
Create `.planning/quick/260715-wrs-fix-model-openrouter-override-bug-get-na/260715-wrs-SUMMARY.md` when done.

Commit message (single atomic commit):
```
fix(runtime): repair /model openrouter override regression (config-defined providers + truthy gate)

Bug 1 (hermes_cli/runtime_provider.py): _get_named_custom_provider returned
None for canonical provider names (openrouter/nous/etc.) BEFORE scanning the
user's `providers:` config section. A user with `providers.openrouter.api_key`
set in config.yaml was ignored — resolution fell through to OPENROUTER_API_KEY
env var. Fix: move the canonical short-circuit to AFTER the config scan so
user-defined entries win, and the built-in only wins when no entry matches.

Bug 2 (gateway/run.py): _apply_session_model_override used `if val is not None`
to gate runtime_kwargs clobbering, but /model override population stores
`api_key=""` / `base_url=""` on resolution failure — empty string is `not None`
so it overwrote valid config credentials. Fix: change to truthy `if val:` so
falsy values cannot clobber existing runtime_kwargs.

4 new regression tests (2 per file) + all pre-existing tests pass.
```
</output>
