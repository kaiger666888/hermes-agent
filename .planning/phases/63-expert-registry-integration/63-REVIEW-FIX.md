---
phase: 63-expert-registry-integration
fixed_at: 2026-07-08T02:03:26Z
review_path: .planning/phases/63-expert-registry-integration/63-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 63: Code Review Fix Report

**Fixed at:** 2026-07-08T02:03:26Z
**Source review:** `.planning/phases/63-expert-registry-integration/63-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (1 BLOCKER + 6 WARNING; 4 INFO deferred per `<files_to_modify>`)
- Fixed: 7
- Skipped: 0
- Test baseline before: 21 passed, 1 skipped
- Test baseline after: 22 passed, 1 skipped (+1 new WR-06 regression test)

## Fixed Issues

### CR-01: `logger.warning` alarm NOT re-emitted on cache-hit path (operator observability regression)

**Files modified:** `agent/registry_loader.py`
**Commit:** `3c039327e`
**Applied fix:** Extracted new `_emit_missing_expert_warnings(missing, *, agents_dir, loaded_count)` helper and invoked it on ALL four emission points — both cache-hit paths (uncontended fast path at the original `:427-432` and the double-checked-locking path at `:435-438`) and both cache-miss paths (missing-agents-dir at `:441-455` and successful-load at `:470-486`). Previously the cache-hit paths returned the recomputed structured warnings list silently, breaking log-based alerting for any consumer polling the loader more than once per process (Phase 67 OBSRV-01 collector, MCP `agents_list`, dashboard health endpoints). Also tightened the `_load_with_warnings` docstring (addresses IN-03) to clarify that warnings are recomputed on EVERY call, not just `force_reload=True`.

### WR-01: Hardcoded developer-specific path `/home/kai/.hermes/agents` in two test files (portability defect)

**Files modified:** `tests/agent/test_registry_loader.py`, `tests/agent/test_phase63_round_table_smoke.py`
**Commit:** `117e3853e`
**Applied fix:** Replaced `Path("/home/kai/.hermes/agents")` with `Path.home() / ".hermes" / "agents"` in both files. `conftest.py:347-353` explicitly documents that `_hermetic_environment` redirects `HERMES_HOME` but NOT `HOME`, so `Path.home()` still resolves to the real user's home — `/home/kai` on Kai's machine, `/home/runner` in CI, `/root` in Docker. For the smoke test, also changed `_seed_visual_executor_yamls` from `pytest.fail` to `pytest.skip` so tests degrade gracefully to SKIPPED on machines without Phase 62's 21 YAMLs, honoring the hermetic-test invariant (`conftest.py:8-12`). The canary test already used `pytest.skip`. Selected REVIEW's Option (b) over Option (a) (bundle fixtures) to keep blast radius minimal — Option (a) would add new fixture files outside Phase 63 scope.

### WR-02: `str.lstrip("$.")` misuse in existing `_format_json_path` touched by this phase

**Files modified:** `agent/registry_loader.py`
**Commit:** `74b6c6d86`
**Applied fix:** Replaced `path.lstrip("$.")` with `path.removeprefix("$.")` at the `invalid_field` computation (line 347 region). `str.lstrip(chars)` strips ANY combination of the individual characters in `chars`, NOT the literal prefix. For the current schema field regex (`^[a-z0-9_-]+$`) the result was correct by accident, but `lstrip` is the wrong tool. `str.removeprefix("$.")` (Python 3.9+) strips the literal `$.` prefix only, preserving the rest of the path verbatim. For the bare root path `$`, `invalid_field` stays `None`.

### WR-03: Bare `except Exception: pass` in `_seed_visual_executor_yamls` swallows errors silently (CLAUDE.md violation)

**Files modified:** `tests/agent/test_phase63_round_table_smoke.py`
**Commit:** `8d15dfad8`
**Applied fix:** Bound the exception (`except Exception as exc:`) and added a `logging.getLogger(__name__).debug("registry_loader cache reset skipped: %s", exc)` call so a future refactor that renames `_REGISTRY_CACHE` surfaces clearly in debug logs instead of silently proceeding with a stale cache. Used lazy %-formatting per CLAUDE.md "Lazy %-formatting" rule. Kept the `try/except` pattern (graceful degradation rationale is sound — `registry_loader` may not be importable in some environments, and `get_agent_opinion` reads persona directly via `_load_persona_for_agent`).

### WR-04: `_capture_missing_warnings` test helper is dead code

**Files modified:** `tests/agent/test_registry_loader.py`
**Commit:** `3d48ff2cf`
**Applied fix:** Deleted the unused module-level helper (lines 493-503). All three existing `TestMissingExpertAlarm` tests inline the cache-reset + load call directly; the helper's docstring claimed "Pitfall #6 mitigation: always resets the module-level cache" but no test actually called it. Selected REVIEW's Option (a) (delete) over Option (b) (refactor tests to use it) — deletion reduces maintenance surface and the new WR-06 test also inlines the call, matching the established pattern.

### WR-05: Idempotency test unnecessarily seeds persona YAMLs (test smell)

**Files modified:** `tests/agent/test_phase63_round_table_smoke.py`
**Commit:** `4b072a1c3`
**Applied fix:** Removed the `_seed_visual_executor_yamls(tmp_path)` call from `test_open_round_table_idempotent_on_duplicate`. The function under test (`open_round_table`) only WRITES the state file (`round_table_state.py:404` `state_dir.mkdir(parents=True, exist_ok=True)`) — it does NOT read persona YAMLs. The seed was wasted I/O that also introduced a hard dependency on Kai's home dir existing (per WR-01) for no functional reason. If YAMLs were ever missing, the test would fail at the seed step before reaching the actual idempotency assertion. The `tmp_path` parameter is retained (pytest fixture signature).

### WR-06: Missing regression test for CR-01 (cache-hit alarm silent path)

**Files modified:** `tests/agent/test_registry_loader.py`
**Commit:** `d9c0360c1`
**Applied fix:** Added 4th test `test_alarm_re_emitted_on_cache_hit` to `TestMissingExpertAlarm`. Calls `load_agent_registry_with_warnings(force_reload=True)` once (cache miss), then calls again WITHOUT `force_reload` (cache hit). Asserts `caplog` captured `logger.warning` citing `screenplay` + `missing` on BOTH calls, AND the structured `warnings2` list still contains `screenplay`. This test FAILS against the pre-CR-01 implementation (proving the bug exists) and PASSES after (proving the fix works). Verified manually during development. Verified post-commit that the test passes against the CR-01-fixed code.

---

_Fixed: 2026-07-08T02:03:26Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
