---
phase: 59-aux-pool-isolation
plan: 01
subsystem: credential-pool
tags: [credential-pool, aux-isolation, glm, named-pool, env-vars]
requires:
  - 52-infra-foundation (CredentialPool + load_pool)
  - 57-endpoint-routing (anthropic-compat endpoint selection)
  - 58-rpm-throttling (glm_throttle.acquire_slot)
provides:
  - "agent.credential_pool.load_aux_pool — specialized aux-pool loader"
  - "agent.credential_pool.load_named_pool — generic named-pool extension point"
  - "agent.credential_pool._seed_aux_env — GLM_AUX_API_KEY_1..4 + GLM_API_KEY fallback seeding"
  - "agent.auxiliary_client._select_pool_entry/_peek_pool_entry pool_name kwarg"
  - "agent.glm_throttle.acquire_slot/try_acquire_slot pool_name kwarg"
affects:
  - "agent/auxiliary_client.py (call_llm wire-in: pool_name='auxiliary')"
  - "agent/glm_throttle.py (signature extension, behavior unchanged)"
  - "cli-config.yaml.example (operator docs)"
tech-stack:
  added: []
  patterns:
    - "Named-pool storage namespace (auxiliary:<provider> alongside <provider>)"
    - "Env-var fallback chain (GLM_AUX_API_KEY_* → GLM_API_KEY for single-key operators)"
    - "Backward-compatible kwarg default (pool_name='default' preserves Phase 58 callers)"
key-files:
  created:
    - tests/agent/test_credential_pool_aux_isolation.py
    - tests/agent/test_auxiliary_client_aux_pool.py
  modified:
    - agent/credential_pool.py
    - agent/auxiliary_client.py
    - agent/glm_throttle.py
    - cli-config.yaml.example
    - tests/agent/test_auxiliary_client.py
decisions:
  - "Named-pool storage key: 'auxiliary:<provider>' (e.g. 'auxiliary:zai') — isolation at the auth.json namespace level, not via in-memory filtering."
  - "GLM_AUX_API_KEY fallback is ADDITIVE — if GLM_API_KEY is set alongside GLM_AUX_*, both are seeded (operator-visible choice, not silent fallback). Plan Test 4 enforced this; differs slightly from CONTEXT.md decision #2 wording but matches the plan's load-bearing Test 4."
  - "pool_name kwarg in glm_throttle is metadata-only — glm_throttle stays a pure rate limiter; pool selection happens in auxiliary_client._select_pool_entry. Avoids awkward coupling between rate-limiting and credential-pool namespaces."
  - "load_named_pool is the generic extension point; load_aux_pool is a thin specialized wrapper. Future named pools (per-tenant, per-experiment) reuse load_named_pool without code changes."
metrics:
  duration: ~45min
  completed: 2026-07-08
  tasks: 2
  files_created: 2
  files_modified: 5
  tests_added: 13
---

# Phase 59 Plan 01: AUX-POOL-ISOLATION Summary

Named auxiliary credential pool that isolates auxiliary traffic (round table, memory compaction, fitness judge, etc.) from the main agent/gateway pool — eliminates the v11.0 smoke-test §3.1 failure mode where a gateway burst exhausts all 4 GLM keys and starves the round table halfway through a 9-panelist session.

## Outcome

- **POOL-01 satisfied**: two pools never share credentials at the storage-namespace level (`auxiliary:zai` vs `zai` in auth.json).
- **Load-bearing isolation test**: `test_aux_pool_isolation_from_default_exhaustion` proves that marking every default-pool entry exhausted (status_code=429) does NOT prevent the aux pool from selecting a usable key.
- **No breaking change**: single-`GLM_API_KEY` operators get a 1-entry aux pool via transparent fallback (source label `env:GLM_API_KEY`, NOT `env:GLM_AUX_API_KEY_1` — visible in `hermes auth list` audit trail).
- **Backward-compatible API**: all Phase 58 call sites that omit `pool_name` keep working; `acquire_slot(task)` is unchanged behavior, `acquire_slot(task, pool_name="auxiliary")` is now explicit at the wire-in point.

## What Was Built

### Task 1: Named-pool extension to credential_pool.py (RED → GREEN)

Extended `agent/credential_pool.py` with three new module-level helpers (additive — default `load_pool` is untouched):

- `AUX_POOL_PREFIX = "auxiliary:"` constant + `_AUX_ENV_VARS = ("GLM_AUX_API_KEY_1", ..., "GLM_AUX_API_KEY_4")` tuple.
- `_seed_aux_env(provider, entries) -> (changed, active_sources)` — structural twin of `_seed_from_env` but reads the dedicated aux env vars AND `GLM_API_KEY` (additive fallback, never suppresses the main key). Source labels are high-specificity (`env:GLM_AUX_API_KEY_1`, `env:GLM_API_KEY`) for audit-trail discipline (T-59-01-S, T-59-04-R mitigations).
- `load_named_pool(name, provider) -> CredentialPool` — generic named-pool loader. Storage key `<name>:<provider>`. For `name == "auxiliary"`, delegates env seeding to `_seed_aux_env`; for other names, no env seeding (operator-managed via `hermes auth add`). Always runs `_prune_stale_seeded_entries` for symmetric cleanup with default `load_pool` (T-59-06-E mitigation).
- `load_aux_pool(provider) -> CredentialPool` — specialized wrapper over `load_named_pool("auxiliary", provider)`.

8 TDD tests in `tests/agent/test_credential_pool_aux_isolation.py` cover: empty pool when no env vars, ordered seeding from GLM_AUX_*, GLM_API_KEY fallback with correct source label, mixed fallback semantics (Test 4 — additive, not either/or), named-pool storage key isolation in auth.json, no-breaking-change for default `load_pool`, and `load_named_pool` generic helper.

### Task 2: Throttle + auxiliary_client integration + isolation tests

- `agent/glm_throttle.py`: `acquire_slot(task, pool_name="auxiliary")` and `try_acquire_slot(task, pool_name="auxiliary")` — kwarg is metadata-only (propagated to downstream auxiliary_client logic via call-site convention). `glm_throttle` does NOT call into `credential_pool`; it stays a pure rate limiter.
- `agent/auxiliary_client.py`: `_select_pool_entry(provider, pool_name="default")` and `_peek_pool_entry(provider, pool_name="default")` — when `pool_name == "default"`, call `load_pool` (current behavior); otherwise dispatch to `load_named_pool(pool_name, provider)`. Existing acquire_slot wire-in at line ~5441 now passes `pool_name="auxiliary"` explicitly.
- `cli-config.yaml.example`: 25-line documentation block under `credential_pool:` section explaining `GLM_AUX_API_KEY_1..4` (dedicated aux pool) vs `GLM_API_KEY` (shared main+aux fallback for single-key operators).
- `tests/agent/test_auxiliary_client_aux_pool.py` (NEW): 5 tests including the **load-bearing** `test_aux_pool_isolation_from_default_exhaustion` — seeds default pool with 2 entries marked exhausted via `mark_exhausted_and_rotate(status_code=429)`, seeds aux pool with 2 separate entries, asserts `_select_pool_entry("zai", pool_name="default")` returns `(True, None)` (no available entries) while `_select_pool_entry("zai", pool_name="auxiliary")` returns `(True, <entry>)` with the entry's `access_token` in `{GLM_AUX_API_KEY_1, GLM_AUX_API_KEY_2}`. This is the v11.0 §3.1 failure-mode fix made executable.
- `tests/agent/test_auxiliary_client.py`: 3 mock lambdas updated to accept `**kw` so the new `pool_name` kwarg flows through the existing `TestGLMThrottleIntegration` tests.

## Commits

- `d64635255` — `test(59-01): add failing tests for aux pool named-pool extension` (RED)
- `732315d52` — `feat(59-01): implement load_aux_pool + load_named_pool + _seed_aux_env` (GREEN)
- `8ca95c9e7` — `feat(59-01): wire throttle.acquire_slot pool_name + auxiliary_client named-pool dispatch + isolation tests`

## Verification

| Check | Result |
|-------|--------|
| `pytest tests/agent/test_credential_pool_aux_isolation.py` | 8/8 pass |
| `pytest tests/agent/test_auxiliary_client_aux_pool.py` | 5/5 pass |
| `pytest tests/agent/test_credential_pool.py tests/agent/test_glm_throttle.py tests/agent/test_auxiliary_client.py` | 312 pass; 4 fail (pre-existing `ModuleNotFoundError: openai` — environmental, fails identically on prior commit) |
| `grep -c "pool_name" agent/{auxiliary_client,glm_throttle}.py` | 16, 5 — both files have the kwarg |
| `grep -c "load_aux_pool\|load_named_pool\|_seed_aux_env" agent/credential_pool.py` | 9 — helpers exist and are used |
| `grep -c "GLM_AUX_API_KEY" cli-config.yaml.example` | 5 — documentation block exists |
| Manual spot-check (only `GLM_API_KEY=test` set) | `load_aux_pool("zai").entries()[0].source == "env:GLM_API_KEY"` — no-breaking-change proof |

## Threat Model Coverage

All 7 threats in the plan's `<threat_model>` register mitigated or accepted as designed:

- **T-59-01-S** (Spoofing, env-var source labels): mitigated — Test 3 verifies `env:GLM_API_KEY` vs `env:GLM_AUX_API_KEY_1` label discipline.
- **T-59-02-T** (Tampering, named-pool storage key): mitigated — Test 5 verifies `credential_pool["auxiliary:zai"]` namespace isolation in auth.json.
- **T-59-03-I** (Info disclosure, debug logs): accepted — no new disclosure surface; matches Phase 52-58 pattern.
- **T-59-04-R** (Repudiation, fallback visibility): mitigated — Test 3 + Test 4 enforce distinct source labels.
- **T-59-05-D** (DoS via aux burst): accepted — Phase 59-02 adds per-key TPM tracking.
- **T-59-06-E** (Elevation via prune bypass): mitigated — `load_aux_pool` calls `_prune_stale_seeded_entries` symmetrically with `load_pool`; Test 6 guards against coupling.
- **T-59-SC** (Supply chain): N/A — pure stdlib extension.

## Deviations from Plan

None — plan executed exactly as written. All 7 Task 1 tests and 5 Task 2 tests match the plan's behavior/action specs verbatim. The only minor clarification is in the `decisions` frontmatter above: Test 4 of Task 1 specifies that GLM_AUX_API_KEY_1 + GLM_API_KEY both being set yields a 2-entry pool (additive), which differs slightly from CONTEXT.md decision #2's "fallback to GLM_API_KEY if unset" wording. The plan's Test 4 is authoritative (it is the load-bearing test), and the implementation matches the plan.

## Self-Check: PASSED

Files verified to exist:
- `agent/credential_pool.py` — FOUND
- `agent/auxiliary_client.py` — FOUND
- `agent/glm_throttle.py` — FOUND
- `tests/agent/test_credential_pool_aux_isolation.py` — FOUND
- `tests/agent/test_auxiliary_client_aux_pool.py` — FOUND
- `cli-config.yaml.example` — FOUND

Commits verified in `git log`:
- `d64635255` — FOUND
- `732315d52` — FOUND
- `8ca95c9e7` — FOUND
