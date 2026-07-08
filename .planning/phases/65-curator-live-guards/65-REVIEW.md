---
phase: 65-curator-live-guards
reviewed: 2026-07-08T04:15:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - agent/curator.py
  - agent/curator_audit.py
  - hermes_cli/curator.py
  - tests/fixtures/curator_bias_canary/known_bad_records.jsonl
  - tests/agent/test_curator_live_guards.py
  - tests/hermes_cli/test_curator_evolve_cli.py
  - tests/hermes_cli/test_curator_cli.py
findings:
  critical: 2
  warning: 5
  info: 3
  total: 10
status: fixed
---

# Phase 65: Code Review Report

**Reviewed:** 2026-07-08T04:15:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** fixed

## Summary

Phase 65 (CURATOR-LIVE-GUARDS) adds the `hermes curator evolve [--live] [--skip-canary]` operator surface plus its deterministic bias canary gate (`run_bias_canary_pre_check`) and extends `append_audit` with four optional Phase 65 kwargs (`tick_mode`, `canary_pass`, `caught_count`, `mutation_summary`).

Empirical verification confirms the contract-level happy paths work as designed: the 5 fixture records produce 4 deterministic catches + 1 LLM-only miss (`bad-unsupported-claim`), `append_audit` round-trips through `verify_chain` cleanly for both legacy and extended schemas, and the `--skip-canary` audit entry correctly omits `canary_pass`/`caught_count` (records as None).

However, the review surfaced **2 BLOCKER-severity defects** and several warnings:

1. **CR-01 (BLOCKER):** `run_bias_canary_pre_check` violates its own documented fail-safe contract. The docstring promises "never raises" and lists `(False, 0, ["<read-error>"])` as the fail-safe return, but `check_record(record)` on line 2040 is NOT wrapped in any try/except. Empirically, malformed records (e.g. `{"text": 123}`, `{"confidence": []}`) raise `AttributeError`/`TypeError` from inside `check_record`, which escape the function entirely. A single corrupted line in the bundled fixture JSONL would crash the CLI instead of failing safe.

2. **CR-02 (BLOCKER):** The post-tick audit append in `_cmd_evolve` claims to be "best-effort" but does not catch `AuditChainError`. When the audit log tail is corrupt (truncated final line, disk-write interruption), `append_audit` raises `AuditChainError` (a direct `Exception` subclass, NOT `OSError` or `ValueError`). The handler's `except (OSError, ValueError)` on line 370 lets the exception propagate, crashing the CLI AFTER the live memory writes have already succeeded — the exact opposite of the documented "failed audit append MUST NOT mask a successful tick" guarantee.

Both blockers are reachable in production. CR-02 is the more severe of the two because it directly inverts the documented safety property after irreversible memory mutations.

## Critical Issues

### CR-01: `run_bias_canary_pre_check` does not honor its "never raises" contract

**File:** `agent/curator.py:2023-2047`
**Issue:** The docstring (lines 2006-2009) explicitly states:

> Fail-safe behavior: when `fixtures_path` does not exist or cannot be read, returns `(False, 0, ["<fixtures-missing>"])` (or `["<read-error>"]`) — **never raises**.

But the `try` block only wraps file I/O (`path.open(...)` iteration). The per-record call `check_record(record)` at line 2040 is INSIDE the try block, but the only `except` clause catches `OSError` — not exceptions thrown by `check_record`. Empirically verified:

```python
>>> from agent.curator_bias_canary import check_record
>>> check_record({"record_id": "x", "text": 123, "evidence_records": [],
...               "evidence_operator_ids": [], "confidence": 0.8})
AttributeError: 'int' object has no attribute 'lower'
>>> check_record({"record_id": "x", "text": "ok", "evidence_records": [],
...               "evidence_operator_ids": [], "confidence": []})
TypeError: float() argument must be a string or a real number, not a 'list'
```

A single JSON line with the wrong field type (e.g. a future editor commits `confidence: "0.8"` as a string, then later code strips the quotes and leaves it numeric-typed-but-wrong) will crash the CLI at `hermes curator evolve` invocation rather than failing safe.

**Severity rationale:** The docstring's "never raises" promise is load-bearing for operators — they rely on the canary gate returning a deterministic verdict. An unexpected exception during the pre-check aborts the live tick in a way that looks like an audit/IO failure, not a clean "canary blocked you" decision. Worse, the operator sees a Python traceback rather than the structured `BIAS_CANARY_FAILED` message the G4 spec mandates.

**Fix:** Wrap the per-record `check_record` call in a narrow `try/except` that treats any check-time exception as "this record was not flagged" (the conservative interpretation — never let a buggy fixture line grant a false PASS by reducing the denominator):

```python
total += 1
try:
    report = check_record(record)
except Exception as exc:  # noqa: BLE001 — defensive per "never raises" contract
    logger.warning(
        "bias canary check_record crashed on line %d (record_id=%s), "
        "treating as not-flagged: %s",
        total, record.get("record_id", "<missing>"), exc,
    )
    not_caught.append(record.get("record_id", "<crashed>"))
    continue
if report.flagged:
    caught += 1
else:
    not_caught.append(report.record_id)
```

Alternative: also fail-safe by incrementing `not_caught` (which keeps `caught` honest) and optionally count crashed records against the threshold by reducing the effective denominator — but the conservative interpretation (crash = not flagged, denominator unchanged) is the minimal contract-honoring fix.

### CR-02: Post-tick audit append does not catch `AuditChainError` — breaks "best-effort" guarantee

**File:** `hermes_cli/curator.py:338-375`
**Issue:** The handler's post-tick audit block is documented as:

> Best-effort: a failed audit append MUST NOT mask a successful tick.

But the `except` clause on line 370 only catches `(OSError, ValueError)`:

```python
try:
    from agent.curator_audit import append_audit
    ...
    append_audit(...)
except (OSError, ValueError) as exc:
    logger.warning("post-tick audit append failed (tick succeeded): %s", exc)
```

`append_audit` raises `AuditChainError` when the existing log tail is malformed JSON (see `agent/curator_audit.py:79-87` and `:255-260`). Empirically verified:

```python
>>> from agent.curator_audit import AuditChainError
>>> AuditChainError.__mro__
(AuditChainError, Exception, BaseException, object)
>>> issubclass(AuditChainError, OSError)
False
>>> issubclass(AuditChainError, ValueError)
False
```

So if the audit log's final line is corrupt (e.g. a previous tick was interrupted mid-write before `f.flush()` / `os.fsync()` completed — the very scenario the WR-01 durability comment at `agent/curator_audit.py:293-303` warns about), the next `hermes curator evolve --live` invocation will:

1. Run the live tick successfully (`run_curator_review` writes memory mutations).
2. Call `append_audit`, which detects the corrupt tail and raises `AuditChainError`.
3. The `except (OSError, ValueError)` clause does NOT catch it.
4. The unhandled exception propagates out of `_cmd_evolve`, killing the CLI process with a traceback.
5. The operator sees a crash, has no clear signal whether the tick succeeded, but the memory mutations are already committed and cannot be rolled back from the CLI.

This is the exact inversion of the documented guarantee. The test `test_audit_failure_does_not_crash_tick` covers `OSError("disk full")` but does NOT cover `AuditChainError`, leaving the regression undetected.

**Severity rationale:** The live path performs IRREVERSIBLE memory writes. A crash AFTER success but BEFORE the operator sees confirmation forces a forensic recovery operation (check logs, replay state, possibly file manual audit repair via `hermes curator audit-log --verify`). On a busy production deployment this is a real outage path.

**Fix:** Either broaden the `except` to `Exception` (matching the pattern at `hermes_cli/curator.py:754` for `_cmd_reject_curator`'s audit append) or explicitly include `AuditChainError`:

```python
from agent.curator_audit import AuditChainError
...
try:
    from agent.curator_audit import append_audit
    ...
    append_audit(...)
except (OSError, ValueError, AuditChainError) as exc:
    logger.warning(
        "post-tick audit append failed (tick succeeded): %s", exc,
    )
# Or the broader pattern already used in the codebase:
# except Exception as exc:  # noqa: BLE001 — best-effort audit per T-65-09
```

Prefer the explicit form because the broader `except Exception` would also swallow programming bugs (e.g. `KeyError` from a missing dict key inside `append_audit`).

**Also add a regression test** that monkeypatches `append_audit` to raise `AuditChainError` and asserts `_cmd_evolve` returns 0 (matching the existing `test_audit_failure_does_not_crash_tick` shape but covering the actually-vulnerable code path).

## Warnings

### WR-01: Hardcoded "5" and "threshold: 4" literals in `BIAS_CANARY_FAILED` message

**File:** `hermes_cli/curator.py:306`
**Issue:** The G4-locked structured message uses string literals for the fixture count (`/5`) and threshold (`threshold: 4`):

```python
f"BIAS_CANARY_FAILED: caught {caught}/5 (threshold: 4); "
```

Both literals duplicate module-level facts: `_BIAS_CANARY_THRESHOLD = 4` (in `agent/curator.py:1949`) and the implicit 5-record count baked into the fixture file. If Phase 66 adds a sixth fixture record, or someone bumps the threshold, the CLI message silently drifts out of sync with reality. The `--help` text on line 1416 ("aborts on <4/5 catch rate") has the same problem.

**Fix:** Import the threshold constant and compute the denominator from the fixture count, or at minimum add a `# noqa: keep literal in sync with _BIAS_CANARY_THRESHOLD` comment cross-referencing the constant. The test `test_canary_failure_message_format` pins the exact regex so any change will be visible.

### WR-02: `_cmd_evolve` outer `try` block misses `ImportError` on lazy `append_audit` import

**File:** `hermes_cli/curator.py:338-375`
**Issue:** The lazy import `from agent.curator_audit import append_audit` (line 339) sits inside the `try` block whose `except` only catches `(OSError, ValueError)`. An `ImportError` (e.g. circular import regression, partially-broken wheel install) would propagate and crash the handler. The existing `_resolve_skill_from_patch` helper at `hermes_cli/curator.py:675-680` explicitly catches `ImportError` from a similar lazy import — the new code should match that defensive pattern for consistency.

Lower severity than CR-02 because the module is bundled and import failure is unlikely in normal operation, but the inconsistency with the neighboring helper is a real maintainability defect.

**Fix:** Move the lazy import ABOVE the `try` block (so `ImportError` is reported distinctly), OR add `ImportError` to the `except` tuple:

```python
try:
    from agent.curator_audit import append_audit
    ...
except (OSError, ValueError, ImportError, AuditChainError) as exc:
    logger.warning("post-tick audit append failed (tick succeeded): %s", exc)
```

### WR-03: `test_audit_failure_does_not_crash_tick` does not cover `AuditChainError` path

**File:** `tests/hermes_cli/test_curator_evolve_cli.py:267-295`
**Issue:** This regression test only monkeypatches `append_audit` to raise `OSError("disk full")`. As shown in CR-02, the actually-vulnerable production failure mode (`AuditChainError` from a corrupt tail) is not exercised. The test passes despite the bug existing in production.

**Fix:** Add a parallel test (e.g. `test_audit_chain_corruption_does_not_crash_tick`) that monkeypatches `append_audit` with `side_effect=AuditChainError("audit log tail is malformed ...")` and asserts `rc == 0`. This is the test that would have caught CR-02.

### WR-04: Wheel-install blind spot in fixture path resolution

**File:** `agent/curator.py:1952-1966`
**Issue:** `_bias_canary_fixtures_path()` resolves to `<repo-root>/tests/fixtures/curator_bias_canary/known_bad_records.jsonl` via `Path(__file__).resolve().parents[1] / "tests" / ...`. But `[tool.setuptools.packages.find]` in `pyproject.toml:345-346` does NOT include `tests` in the wheel — only `agent`, `tools`, `hermes_cli`, `gateway`, etc. So when `hermes` is installed via `pip install hermes-agent`, the fixture file is absent, and `run_bias_canary_pre_check` always returns `(False, 0, ["<fixtures-missing>"])`, silently making `--live` UNUSABLE for wheel users.

The fail-safe behavior is correct (the canary denies rather than grants), and the docstring acknowledges Phase 66 will bundle fixtures as package data — but until Phase 66 ships, wheel users have NO live curator path at all, with no operator-visible signal that the issue is the install method rather than a misconfiguration. The CLI will print `BIAS_CANARY_FAILED: caught 0/5 (threshold: 4)` which reads like "the canary ran and found nothing," not "the canary file is missing because you're on a wheel install."

**Fix:** Either (a) escalate the Phase 66 fixture-bundling work to ship in this phase, or (b) emit a distinct `BIAS_CANARY_FIXTURES_MISSING` stderr message when `failed_ids == ["<fixtures-missing>"]` so operators can distinguish "canary ran and underperformed" from "canary couldn't run."

### WR-05: `result.get("auto_transitions", {})` in nested `try` shadows outer `try` semantics

**File:** `hermes_cli/curator.py:344-356`
**Issue:** The inner `try/except (AttributeError, TypeError)` block wraps a `dict.get()` chain that cannot actually raise either exception type in normal operation — `result.get(...)` returns `{}` (or the default) on any input, and `{}.get("checked", 0)` returns `0`. The `or {}` defensive coalescing on line 345 already handles `result` being `None`. The only realistic way to reach the `except` is if `result` is not a dict-like object (e.g. `result = "string"`), in which case `result.get` raises `AttributeError`. The comment "Wrap in try/except KeyError for forward-compat" is inaccurate — the caught types are `AttributeError, TypeError`, not `KeyError`.

This is a minor defect (the try/except is dead-code-ish but harmless), but the misleading comment + wrong-exception-types combo suggests the defensive envelope was written without tracing what actually raises. It also masks the case where `result` is genuinely malformed (a real bug in `run_curator_review` would be silently swallowed and `mutation_summary={}` would be written to the audit log, hiding the upstream defect).

**Fix:** Remove the inner `try/except` entirely — the `result.get("auto_transitions", {}) or {}` and per-key `.get(..., 0)` pattern already handles all reasonable inputs. Or if defensive coverage is desired, change the comment to match the caught types and let unexpected `result` shapes surface as a warning rather than silently producing an empty `mutation_summary`.

## Info

### IN-01: Fixture file uses leading `#` comment lines, parser correctly skips them

**File:** `tests/fixtures/curator_bias_canary/known_bad_records.jsonl:1-10`
**Issue:** The 10-line header comment documents the design intent (records #1-4 deterministic, #5 LLM-only, do-not-redesign caveat). Empirically verified the parser at `agent/curator.py:2029` correctly skips these via `line.startswith("#")`. No defect — flagging only to confirm the comment-skipping code path is exercised by the bundled fixture.

**No fix needed.** Comment is high-quality documentation that prevents well-meaning future contributors from "fixing" record #5 to fail deterministically.

### IN-02: `from datetime import datetime as _dt` alias inside `_cmd_evolve` is redundant

**File:** `hermes_cli/curator.py:358`
**Issue:** The handler already imports `from datetime import datetime, timezone` at module level (`hermes_cli/curator.py:27`). The local `from datetime import datetime as _dt` at line 358 aliases the same symbol unnecessarily. This appears to be leftover from an earlier draft where the timestamp formatting was inline before being refactored.

**Fix:** Replace `_dt.now(timezone.utc)` with `datetime.now(timezone.utc)` and delete the redundant local import.

### IN-03: `_bias_canary_fixtures_path()` uses `parents[1]` indexing — fragile to file relocations

**File:** `agent/curator.py:1960-1966`
**Issue:** `Path(__file__).resolve().parents[1]` assumes `agent/curator.py` lives exactly two levels below the repo root. If the module is ever moved into a subpackage (e.g. `agent/curation/orchestrator.py`), `parents[1]` would resolve to `agent/`, and `/ "tests" / ...` would silently point to a non-existent path. The fail-safe catches this (returns `<fixtures-missing>`), but the silent failure mode is hostile to refactoring.

**Fix:** Consider an explicit path marker (e.g. walk up looking for a `pyproject.toml` sentinel) or move the fixture to a packaged location under `agent/` so the path resolution is co-located with the code. Low priority — the current structure has been stable and the fail-safe behavior is correct.

---

_Reviewed: 2026-07-08T04:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
