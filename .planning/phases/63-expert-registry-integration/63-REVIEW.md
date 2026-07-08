---
phase: 63-expert-registry-integration
reviewed: 2026-07-08T01:52:44Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - agent/registry_loader.py
  - tests/agent/test_registry_loader.py
  - tests/agent/test_phase63_round_table_smoke.py
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: fixed
---

# Phase 63: Code Review Report

**Reviewed:** 2026-07-08T01:52:44Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Phase 63 adds missing-expert alarm scaffolding to `agent/registry_loader.py`
(new `REQUIRED_DAG_EXPERTS` frozenset + `load_agent_registry_with_warnings`
sibling + `_check_required_experts` pure helper) plus 6 new canary/smoke tests
across two test files. All 22 collected tests pass in the current environment
(1 skipped opt-in live test), and the `load_agent_registry()` signature is
indeed unchanged.

The 15-expert `REQUIRED_DAG_EXPERTS` set matches the v10.0 design doc
`01-AGENT-REGISTRY-SCHEMA.md §6.2` verbatim (cross-validated row-by-row).
The pure helper `_check_required_experts` is correctly side-effect-free. The
schema-cache and registry-cache mechanics are sound. CLAUDE.md conventions
(encoding=utf-8, %-formatting in log calls, specific exception types,
`from __future__ import annotations`) are honored in the production module.

However, the review surfaced **1 blocker-level bug** (logger.warning emission
inconsistency between cache-hit and cache-miss paths — the structured return
is correct, but the operator-visible `agent.log` alarm silently disappears on
repeat calls, which defeats the OBSRV-01 observability goal for any consumer
that calls the loader more than once per process) and **6 warnings**:
hardcoded developer-specific fixture path (`/home/kai/.hermes/agents`) baked
into two test files, a latent `str.lstrip` misuse in the existing code touched
by this phase, a bare `except Exception: pass` violating CLAUDE.md swallow
policy, an unnecessary YAML-seed in the idempotency test, and a dead
`_capture_missing_warnings` test helper. Plus 4 informational items.

## Critical Issues

### CR-01: `logger.warning` alarm NOT re-emitted on cache-hit path (operator observability regression)

**File:** `agent/registry_loader.py:427-432` (and the duplicate at `:435-438`)
**Issue:**
`_load_with_warnings` has two return paths:

1. **Cache-miss path** (`:440-486`): emits one `logger.warning` per missing
   required expert AND returns the structured `missing` list. Operator sees
   the alarm in `~/.hermes/logs/agent.log`.
2. **Cache-hit path** (`:427-432`): returns the recomputed `missing` list
   via `_check_required_experts(loaded_names)` but **does NOT emit any
   `logger.warning`**.

This means the very first call to `load_agent_registry_with_warnings()`
after process start logs all missing experts at WARNING, but every
subsequent call from any other caller (Phase 67 OBSRV-01 collector, MCP
`agents_list` tool, dashboard health endpoint) silently returns the
warnings without ever writing them to `agent.log`. An operator tailing
`agent.log` to debug a missing-expert regression will see no new records
after the first invocation and may conclude the issue self-resolved.

The Phase 63 task brief explicitly says the alarm is the foundation for
"Phase 67 OBSRV-01 collector consumer" — a collector that polls the
registry on a cron will only see log records on its very first poll
(or after `force_reload=True`), making log-based alerting unreliable.

The existing Phase 63 canary tests do not catch this because they all use
`force_reload=True` (via `_capture_missing_warnings` and the explicit
`force_reload=True` argument), which forces the cache-miss path.

**Fix:**
Extract the warning-emission into a small helper and call it on both paths:

```python
def _emit_missing_expert_warnings(
    missing: list[str], *, agents_dir: Path, loaded_count: int
) -> None:
    """Emit one operator-visible logger.warning per missing required expert."""
    for name in missing:
        logger.warning(
            "registry_loader: required expert %r missing from %s "
            "(loaded %d agents, expected %d required DAG experts)",
            name,
            agents_dir,
            loaded_count,
            len(REQUIRED_DAG_EXPERTS),
        )

# Cache-hit path (lines 427-432):
if _REGISTRY_CACHE is not None and not force_reload:
    cached = _REGISTRY_CACHE
    loaded_names = {e["name"] for e in cached}
    missing = _check_required_experts(loaded_names)
    _emit_missing_expert_warnings(
        missing, agents_dir=get_hermes_home() / "agents", loaded_count=len(cached)
    )
    return cached, missing
```

Apply the same fix to the double-checked-locking path at `:435-438`. Add a
regression test that calls `load_agent_registry_with_warnings()` twice
without `force_reload` and asserts `caplog` captured the warning BOTH times.

## Warnings

### WR-01: Hardcoded developer-specific path `/home/kai/.hermes/agents` in two test files (portability defect)

**File:** `tests/agent/test_registry_loader.py:46` and `tests/agent/test_phase63_round_table_smoke.py:51`
**Issue:**
Both files hardcode the absolute fixture source path:
```python
_REAL_AGENTS_DIR = Path("/home/kai/.hermes/agents")  # test_registry_loader.py:46
REAL_AGENTS_DIR = Path("/home/kai/.hermes/agents")   # test_phase63_round_table_smoke.py:51
```

This path is correct ONLY on Kai's machine. On any other developer's
machine, in CI (GitHub Actions runners use `/home/runner`), in Docker
containers (root user → `/root/.hermes`), or when the operator username
differs, these paths will not exist. The Phase 63 canary uses
`pytest.skip(...)` defensively in `_stage_required_experts` (line 488) so
those 3 tests degrade to SKIPPED. But `_seed_visual_executor_yamls` (smoke
test, line 105) uses `pytest.fail(...)` — a HARD FAILURE — so
`test_round_table_produces_nonempty_opinion` and
`test_open_round_table_idempotent_on_duplicate` will HARD-FAIL on any
non-Kai machine or CI runner.

This violates the hermetic-test invariant documented in
`tests/conftest.py:8-12`. The tests are not actually hermetic — they depend
on Kai's production `~/.hermes/agents/` tree being present.

**Fix:**
Resolve the source dir dynamically via `Path.home() / ".hermes" / "agents"`
(wrapped in a `_real_agents_dir()` helper) OR ship the required fixture
YAMLs under `tests/agent/fixtures/agents/` and reference those instead.
The fixture approach is preferred — it makes the tests truly hermetic:

```python
# At top of both test files, replace the hardcoded path:
from pathlib import Path
_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "agents"
_REAL_AGENTS_DIR = Path.home() / ".hermes" / "agents"  # fallback for live-mode
```

Then copy `visual_executor.agent.yaml` and `cinematographer.agent.yaml`
into `tests/agent/fixtures/agents/` so the mock-mode tests are hermetic.
The live-mode test (`test_live_round_table`) can still reference
`_REAL_AGENTS_DIR` since it's already gated behind an opt-in env var.

### WR-02: `str.lstrip("$.")` misuse in existing `_format_json_path` touched by this phase

**File:** `agent/registry_loader.py:315`
**Issue:**
```python
invalid_field = path.lstrip("$.") if path.startswith("$.") else None
```
`str.lstrip(chars)` strips ANY combination of the individual characters in
`chars`, NOT the literal prefix. For paths like `$.style.genome` it happens
to work (result `style.genome`), but for any field name beginning with `$`
or `.` it will over-strip. For example, a hypothetical `$._internal` would
become `_internal` (correct by accident), but `$.session.id` where the
session segment started with a `.` would be mis-stripped.

This is a latent bug — the current agents-schema.yaml field patterns
(`^[a-z0-9_-]+$`) happen to never start with `$` or `.`, so today the
result is correct. But it's the wrong tool: `str.removeprefix("$.")`
(Python 3.9+) does exactly what's intended with no edge-case risk.

This is in pre-existing code but lives in the same module being modified
by this phase, so it should be fixed alongside the Phase 63 work.

**Fix:**
```python
invalid_field = path.removeprefix("$.") if path.startswith("$.") else None
```

### WR-03: Bare `except Exception: pass` in `_seed_visual_executor_yamls` swallows errors silently (CLAUDE.md violation)

**File:** `tests/agent/test_phase63_round_table_smoke.py:114-122`
**Issue:**
```python
try:
    from agent import registry_loader
    registry_loader._REGISTRY_CACHE = None
except Exception:
    # registry_loader may not be importable in some environments;
    # the smoke still works because get_agent_opinion reads the
    # persona directly from the YAML via _load_persona_for_agent.
    pass
```

CLAUDE.md "Error Handling" section explicitly states: "always bind the
exception to a name (`except X as exc:`) and include it in the log message
... Do not swallow silently." This `except Exception: pass` block violates
both rules.

The comment provides a rationale (graceful degradation if
`registry_loader` can't import), but the silent swallow makes debugging
harder: if `_REGISTRY_CACHE = None` fails for an unexpected reason (e.g.,
attribute renamed in a future refactor), the test will silently proceed
with a stale cache and potentially produce confusing failures downstream
that don't point back to this swallow.

The reference pattern in `test_mcp_serve_round_table.py:80-83` does the
same thing, but that doesn't make it correct — this just propagates the
anti-pattern.

**Fix:**
Bind the exception and at minimum emit a debug-level log:
```python
try:
    from agent import registry_loader
    registry_loader._REGISTRY_CACHE = None
except Exception as exc:
    # registry_loader may not be importable; smoke still works because
    # get_agent_opinion reads persona directly via _load_persona_for_agent.
    import logging
    logging.getLogger(__name__).debug(
        "registry_loader cache reset skipped: %s", exc
    )
```

### WR-04: `_capture_missing_warnings` test helper is dead code

**File:** `tests/agent/test_registry_loader.py:493-503`
**Issue:**
The module-level helper `_capture_missing_warnings()` is defined but
NEVER called by any test in `TestMissingExpertAlarm`. All three tests in
that class (`test_alarm_fires_when_screenplay_missing`,
`test_alarm_silent_when_all_15_present`,
`test_alarm_warnings_sorted_when_multiple_missing`) inline the cache-reset
+ load call directly:

```python
_reset_registry_cache()
from agent.registry_loader import load_agent_registry_with_warnings
_entries, warnings = load_agent_registry_with_warnings(force_reload=True)
```

The docstring on `_capture_missing_warnings` says "Pitfall #6 mitigation:
always resets the module-level cache before loading" — but since no test
actually uses it, Pitfall #6 is mitigated by the manual `_reset_registry_cache()`
call at the top of each test, not by this helper. This is dead code that
will rot.

**Fix:**
Either (a) delete the unused helper, or (b) refactor the three tests to
actually use it (preferred — DRYs up the cache-reset boilerplate):
```python
def test_alarm_fires_when_screenplay_missing(self, caplog):
    _stage_required_experts(exclude={"screenplay"})
    with caplog.at_level(logging.WARNING, logger="agent.registry_loader"):
        _entries, warnings = _capture_missing_warnings()
    assert "screenplay" in warnings
    ...
```

### WR-05: Idempotency test unnecessarily seeds persona YAMLs (test smell)

**File:** `tests/agent/test_phase63_round_table_smoke.py:396-406`
**Issue:**
`test_open_round_table_idempotent_on_duplicate` calls
`_seed_visual_executor_yamls(tmp_path)` at line 406, which copies two
real YAMLs (visual_executor + cinematographer) from Kai's home dir into
the redirected HERMES_HOME. But `open_round_table()` (the only function
under test) does NOT read persona YAMLs — it only writes the state file.
The persona seed is wasted I/O that also introduces a hard dependency on
Kai's home dir existing (per WR-01).

This makes the idempotency test coupled to the persona-seeding fixture
for no functional reason. If the YAMLs are ever missing, this test will
fail at the seed step before even reaching the actual idempotency
assertion.

**Fix:**
Drop the `_seed_visual_executor_yamls(tmp_path)` call — the test only
needs `open_round_table()`, which doesn't read any YAMLs. The state dir
is created on-demand by `open_round_table` itself (line 443 of
round_table_state.py: `state_dir.mkdir(parents=True, exist_ok=True)`).

```python
def test_open_round_table_idempotent_on_duplicate(self, tmp_path):
    from agent.round_table_state import open_round_table
    # No _seed_visual_executor_yamls — open_round_table doesn't read YAMLs.
    round_id = str(uuid.uuid4())
    state_dir = _compute_state_dir()
    ...
```

### WR-06: Missing regression test for CR-01 (cache-hit alarm silent path)

**File:** `tests/agent/test_registry_loader.py` (entire `TestMissingExpertAlarm` class)
**Issue:**
All three `TestMissingExpertAlarm` tests use `force_reload=True`, which
forces the cache-miss path. There is NO test that verifies the alarm
behavior on the cache-hit path (`load_agent_registry_with_warnings()`
called twice without `force_reload`). This is exactly the path where
CR-01 manifests — the structured warnings list is returned correctly, but
no `logger.warning` is emitted on the second call.

The Phase 63 brief lists "Phase 67 OBSRV-01 collector consumer" as the
downstream use case, and OBSRV-01 will almost certainly call the loader
on a poll loop (cache-hit path). Without a regression test, CR-01 will
re-emerge the moment someone refactors `_load_with_warnings`.

**Fix:**
Add a fourth test to `TestMissingExpertAlarm`:
```python
def test_alarm_re_emitted_on_cache_hit(self, caplog: pytest.LogCaptureFixture):
    """CR-01 regression: alarm MUST emit logger.warning on EVERY call,
    not just the first (cache-miss) one."""
    _reset_registry_cache()
    _stage_required_experts(exclude={"screenplay"})

    from agent.registry_loader import load_agent_registry_with_warnings

    # First call (cache miss) — should emit warning.
    with caplog.at_level(logging.WARNING, logger="agent.registry_loader"):
        load_agent_registry_with_warnings(force_reload=True)
    first_call_warnings = sum(
        1 for r in caplog.records
        if "screenplay" in r.getMessage() and "missing" in r.getMessage().lower()
    )

    # Second call (cache hit, no force_reload) — MUST also emit warning.
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="agent.registry_loader"):
        _entries2, warnings2 = load_agent_registry_with_warnings()  # no force_reload
    second_call_warnings = sum(
        1 for r in caplog.records
        if "screenplay" in r.getMessage() and "missing" in r.getMessage().lower()
    )

    assert "screenplay" in warnings2, "cache-hit path must still return warnings list"
    assert second_call_warnings >= 1, (
        f"cache-hit path must re-emit logger.warning; got {second_call_warnings} "
        f"(first call had {first_call_warnings})"
    )
```

This test will FAIL against the current implementation, demonstrating the
bug, and pass once CR-01 is fixed.

## Info

### IN-01: `_mock_call_llm` FakeResponse sets a top-level `.content` attribute that is never read

**File:** `tests/agent/test_phase63_round_table_smoke.py:153-172`
**Issue:**
The `FakeResponse` mock object defines both `content` (top-level) and
`choices[0].message.content` (nested). `mcp_serve.get_agent_opinion` at
line 885 reads ONLY `response.choices[0].message.content` — the top-level
`.content` is dead. It's harmless (the reference pattern in
`test_mcp_serve_round_table.py:88-117` has the same redundancy) but adds
noise. The top-level `.content` was probably intended for an older code
path that no longer exists.

**Fix:**
Drop the top-level `"content": content` key from the `FakeResponse` type
dict to match the actual consumption shape.

### IN-02: `test_alarm_silent_when_all_15_present` assertion is permissive (could mask future regressions)

**File:** `tests/agent/test_registry_loader.py:558-565`
**Issue:**
The "silent" assertion checks that NO record contains BOTH "required
expert" AND "missing". If a future refactor emits a warning with slightly
different wording (e.g., "DAG expert X is absent"), the test would still
pass even though an unwanted warning was logged. A stricter assertion
would check that `caplog.records` is empty at WARNING level for the
target logger, or at least that no record mentions any of the 15 required
expert IDs.

**Fix:** Tighten to assert no WARNING-level records at all from the target
logger when the registry is complete:
```python
warning_records = [
    r for r in caplog.records
    if r.levelno >= logging.WARNING
    and r.name == "agent.registry_loader"
]
assert warning_records == [], (
    f"expected zero warnings when all 15 staged, got: "
    f"{[r.getMessage() for r in warning_records]!r}"
)
```

### IN-03: Docstring on `_load_with_warnings` claims "warnings list is recomputed on every `force_reload=True` call" but is silent on cache-hit semantics

**File:** `agent/registry_loader.py:411-415`
**Issue:**
The docstring says:
> "The warnings list is recomputed on every `force_reload=True` call
> (cheap set difference on ≤21 names) so operators who temporarily rename
> a YAML see the alarm fire without needing to invalidate the entries
> cache separately."

This is accurate for the `force_reload=True` path but doesn't mention
that the cache-hit path ALSO recomputes warnings (via the same
`_check_required_experts` call at lines 431-432/437-438). Combined with
CR-01 (no logger.warning on cache-hit), the docstring creates the
impression that the cache-hit path is a fast no-op when it actually
recomputes AND returns structured warnings — just silently. Clarifying
the docstring would help future maintainers.

**Fix:**
Add a sentence to the cache-semantics paragraph: "On cache-hit calls
(`force_reload=False`), the entries list is returned from cache but the
warnings list is still recomputed via `_check_required_experts` on the
cached entries' `name` fields, so callers always see fresh warnings
without paying the YAML-parse cost."

### IN-04: `_REAL_AGENTS_DIR` constant naming is inconsistent across the two test files

**File:** `tests/agent/test_registry_loader.py:46` vs `tests/agent/test_phase63_round_table_smoke.py:51`
**Issue:**
One uses `_REAL_AGENTS_DIR` (leading underscore, module-private), the
other uses `REAL_AGENTS_DIR` (no underscore, public). Both are
module-level constants used only within their own file. The CLAUDE.md
"Module-private singletons are prefixed `_`" convention suggests both
should be `_REAL_AGENTS_DIR`. Trivial, but worth aligning if the files
are touched again.

**Fix:** Rename `REAL_AGENTS_DIR` to `_REAL_AGENTS_DIR` in
`test_phase63_round_table_smoke.py:51`.

---

_Reviewed: 2026-07-08T01:52:44Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
