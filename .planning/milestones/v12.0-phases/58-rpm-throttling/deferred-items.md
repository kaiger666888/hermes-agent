
## Pre-existing test_auxiliary_client.py failures (out of scope)

Discovered during Phase 58-01 Task 2 regression run. These 4 tests fail on the
base commit (fd43ec783 parent) WITHOUT any Phase 58 changes applied — confirmed
via `git stash` + re-run. They are unrelated to THROTTLE-01 wire-in:

- `TestAuxiliaryPoolAwareness::test_async_call_llm_retries_nous_after_401`
- `TestAuxiliaryPoolAwareness::test_async_call_llm_refreshes_nous_after_free_tier_block_when_account_paid`
- `TestStaleBaseUrlWarning::test_warns_when_openai_base_url_set_with_named_provider`
- `TestAuxiliaryTaskExtraBody::test_no_warning_when_openai_base_url_not_set`

Likely environment/ordering issues unrelated to RPM throttling. Deferred per
GSD Rule 3 scope boundary.
