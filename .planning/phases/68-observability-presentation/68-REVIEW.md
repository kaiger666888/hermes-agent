# Phase 68 Code Review (Self-Review)

**Reviewed:** 2026-07-08
**Reviewer:** Inline executor (autonomous mode)
**Scope:** All Phase 68 commits (5 commits across plans 68-01 and 68-02)

## Methodology

Self-review against:
1. **CLAUDE.md** compliance (encoding, lazy logging, specific exceptions, no Path.home)
2. **Anti-patterns** (bare except, f-string in logger, innerHTML, new asyncio)
3. **Phase invariants** (INFRA-04 serial, parity SC#3, auth gate)
4. **Threat register** mitigations (T-68-01-drift/crash/cycle, T-68-02-public/noauth/xss/cycle)

## Findings

### BLOCKER: None

### CRITICAL: None

### MAJOR: None

### MINOR: None

### INFO (observations, no fix required)

**INFO-1: `except Exception` in `_build_snapshot` is CLAUDE.md-compliant.**
- Location: `hermes_cli/orchestrator.py:133`
- Pattern: `except Exception as exc: logger.warning("...: %s", exc)`
- CLAUDE.md explicitly allows `except Exception:` "for best-effort fallback paths where the goal is 'don't crash'. Always log the exception." This pattern matches exactly. The exception is bound to `exc`, logged via lazy `%s` formatting. No fix needed.

**INFO-2: Static HTML template intentionally avoids Jinja2.**
- Location: `hermes_cli/web_templates/orchestrator.html`
- CONTEXT.md spec says "minimal Jinja2 panel" but the implementation uses a plain HTML file served via `FileResponse`. This is documented in 68-RESEARCH.md GA3: no server-side data needs substitution (all data comes from client-side fetch). Jinja2Templates would add an unused dependency path. Future evolution to Jinja2 is trivial. No fix needed.

**INFO-3: Auth UX rough edge for loopback mode.**
- Location: `hermes_cli/web_templates/orchestrator.html` token resolver + `web_server.py` handler docstring.
- In loopback mode, direct browser visits to `/orchestrator` without `?token=xxx` will 401. The operator workflow is: open dashboard SPA → SPA's "Orchestrator" link opens `/orchestrator?token=<session_token>`. This is documented in the handler docstring + 68-02 SUMMARY. Deferred to v14 for polish.

## Compliance Verification

### CLAUDE.md Rules

| Rule | Status | Evidence |
|------|--------|----------|
| `encoding="utf-8"` on every `open()` | ✅ N/A | No `open()` calls in new code |
| Lazy `%s` logging | ✅ | `orchestrator.py:134` — `logger.warning("...: %s", exc)` |
| Specific exception types | ✅ | `except Exception as exc:` with logging (CLAUDE.md-sanctioned pattern) |
| No `Path.home() / ".hermes"` | ✅ | No `Path.home()` calls; data comes from in-memory collectors |
| No bare `except:` | ✅ | All excepts bind the exception |
| No `f"..."` in logger calls | ✅ | `%s` positional args only |
| Snake_case naming | ✅ | `_cmd_status`, `_build_snapshot`, `_render_tables` |
| `from __future__ import annotations` | ✅ | `orchestrator.py:46` |

### Phase Invariants

| Invariant | Status | Evidence |
|-----------|--------|----------|
| INFRA-04 serial (no new asyncio) | ✅ | CLI handler fully sync; dashboard route sync; template fetch is browser-side async (not server) |
| SC#3 no-drift (CLI == endpoint shape) | ✅ | `test_no_drift_between_cli_and_endpoint` passes; both call same getters |
| Auth gate on `/orchestrator` panel | ✅ | `_require_token(request)` in handler; `test_orchestrator_panel_requires_auth` passes |
| `/orchestrator` NOT in PUBLIC_API_PATHS | ✅ | `test_orchestrator_panel_not_in_public_paths` + `test_status_not_in_public_paths` (Phase 67) |

### Threat Register Mitigations

| Threat | Mitigation | Verified By |
|--------|------------|-------------|
| T-68-01-drift | `_build_snapshot()` single source; parity test | `test_no_drift_between_cli_and_endpoint` ✅ |
| T-68-01-crash | try/except → schema_ok=False, exit 0 | `test_registry_failure_graceful` ✅ |
| T-68-01-cycle | Lazy imports inside `_build_snapshot` body | (structural) ✅ |
| T-68-02-public | Not in PUBLIC_API_PATHS | `test_orchestrator_panel_not_in_public_paths` ✅ |
| T-68-02-noauth | `_require_token` in handler | `test_orchestrator_panel_requires_auth` ✅ |
| T-68-02-xss | `textContent`-only setters | grep: no `innerHTML` outside comments ✅ |
| T-68-02-cycle | `FileResponse` + `Path(__file__).parent` | (structural) ✅ |

## Test Coverage

| Plan | Test File | Tests | Status |
|------|-----------|-------|--------|
| 68-01 | `tests/hermes_cli/test_orchestrator_cli.py` | 7 | ✅ all pass |
| 68-02 | `tests/hermes_cli/test_web_server_orchestrator_panel.py` | 4 | ✅ all pass |
| 67 (regression) | `tests/hermes_cli/test_web_server_orchestrator_status.py` | 5 | ✅ all pass |
| **Total** | | **16** | **✅ all pass** |

## Ruff Check

```
$ uv run --with 'ruff==0.15.10' ruff check hermes_cli/orchestrator.py
All checks passed!
```

## Verdict

**Status: PASSED** — No BLOCKER, CRITICAL, MAJOR, or MINOR findings. All CLAUDE.md rules + phase invariants + threat mitigations verified. No fixes required.

3 INFO observations documented for future reference (v14 polish candidates).
