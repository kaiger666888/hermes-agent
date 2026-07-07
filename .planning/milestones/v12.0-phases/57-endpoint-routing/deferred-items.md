# Phase 57 — Deferred Items (out-of-scope discoveries)

Out-of-scope issues encountered during 57-01 execution. Logged per the executor
SCOPE BOUNDARY rule — not fixed, not investigated further.

## Pre-existing test failures on v12.0-dev (environmental, not caused by 57-01)

The following tests in `tests/agent/test_auxiliary_client.py` were already
failing on the `v12.0-dev` branch BEFORE any Phase 57 changes. They are
environmental (`ModuleNotFoundError: No module named 'openai'` — the local
test environment at `/data/workspace/hermes-agent` does not have the `openai`
Python package installed). Verified via `git stash` + re-run.

| Test | Failure mode |
|------|--------------|
| `TestAuxiliaryPoolAwareness::test_async_call_llm_retries_nous_after_401` | `ModuleNotFoundError: No module named 'openai'` |
| `TestAuxiliaryPoolAwareness::test_async_call_llm_refreshes_nous_after_free_tier_block_when_account_paid` | Same |
| `TestStaleBaseUrlWarning::test_warns_when_openai_base_url_set_with_named_provider` | Same |
| `TestAuxiliaryTaskExtraBody::test_no_warning_when_openai_base_url_not_set` | Same |

**Action:** None. These pass in CI (which installs the `[dev]` extra with
`openai==2.24.0`). Local reproducer needs `pip install openai==2.24.0` or
running inside the project venv. Phase 57 SC#3 ("zero regressions") is
satisfied: my changes introduce zero new failures — the 4 pre-existing
failures pre-date this phase.
