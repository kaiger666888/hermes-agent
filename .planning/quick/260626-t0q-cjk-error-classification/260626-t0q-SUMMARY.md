---
phase: quick-260626-t0q
plan: 01
subsystem: agent-error-classification
tags: [error-classification, cjk, zhipu, failover, openclaw-port, retry-recovery]
requires:
  - "agent/error_classifier.py existing classifier pipeline"
  - "agent/conversation_loop.py response-shape validator (response_invalid block)"
provides:
  - "CJK + English error pattern library (4 openclaw categories) in error_classifier.py"
  - "Zhipu numeric code handlers (1305/1311/1113)"
  - "classify_response_body_error() public helper for HTTP-200-with-error-body classification"
  - "_SyntheticBodyError exception class for routing body errors through classify_api_error"
  - "conversation_loop pre-check that converts retryable body errors into synthetic exceptions"
affects:
  - "agent/error_classifier.py (added 289 lines: patterns, codes, helper, exception class)"
  - "agent/conversation_loop.py (added 43 lines: pre-check insertion only, retry loop unmodified)"
  - "tests/agent/test_error_classifier.py (added 326 lines: 3 new test classes)"
tech-stack:
  added: []
  patterns:
    - "openclaw failover-matches.ts port — CJK + English regex pattern library"
    - "Belt-and-suspenders numeric-code handling (structured code + body-JSON regex fallback)"
    - "Synthetic exception pattern — wraps non-exception error payload to reuse existing classifier pipeline"
key-files:
  created: []
  modified:
    - agent/error_classifier.py
    - agent/conversation_loop.py
    - tests/agent/test_error_classifier.py
decisions:
  - "Port openclaw patterns verbatim except for 2 deliberate omissions (internal_error, connection reset) that collide with hermes' SSL and transport-error classification paths"
  - "Deliberately do NOT set synth.status_code — HTTP was 200 (uninformative for routing); classifier falls through to error-code + message paths"
  - "conversation_loop pre-check uses local lazy import to avoid changing module-top imports"
metrics:
  duration: 8m
  completed: 2026-06-26T13:07:15Z
  tasks: 2
  files: 3
---

# Phase quick-260626-t0q Plan 01: CJK Error Classification (openclaw Port) Summary

Ported openclaw's `failover-matches.ts` CJK + English error pattern library and added a `classify_response_body_error()` helper so Zhipu's HTTP-200-with-error-body pattern (`{"code":"1305","message":"该模型当前访问量过大"}`) classifies as `FailoverReason.overloaded` and retries correctly instead of burning all retries as `InvalidAPIResponse`.

## What Was Built

### Task 1: openclaw pattern port + Zhipu code handlers (RED: 98d5d726c, GREEN: 78351d357)

**agent/error_classifier.py:**
- Added 4 openclaw failover pattern categories with regex + plain-string entries:
  - `_OPENCLAW_RATE_LIMIT_RES` / `_OPENCLAW_RATE_LIMIT_STRINGS` — 4 regexes + 14 plain strings (7 English, 7 CJK)
  - `_OPENCLAW_OVERLOADED_RES` / `_OPENCLAW_OVERLOADED_STRINGS` — 3 regexes + 5 plain strings (English + CJK + Zhipu signature "该模型当前访问量过大")
  - `_OPENCLAW_SERVER_ERROR_RES` / `_OPENCLAW_SERVER_ERROR_STRINGS` — 9 plain strings (English + 6 CJK; 2 English entries omitted as collisions)
  - `_OPENCLAW_TIMEOUT_RES` / `_OPENCLAW_TIMEOUT_STRINGS` — 22 regexes (libuv codes, stop-reason variants, Zhipu gRPC-status-as-JSON) + 17 plain strings (English + CJK)
- Added 3 Zhipu numeric-code body-JSON regexes: `ZHIPU_OVERLOADED_CODE_1305_RE`, `ZHIPU_BILLING_CODE_1311_RE`, `ZHIPU_AUTH_CODE_1113_RE`
- Extended `_classify_by_error_code` with explicit handlers for Zhipu numeric codes 1305/1311/1113 (placed BEFORE existing string-code matches)
- Extended `_classify_by_message` with an openclaw pattern fallback (`_matches_openclaw` helper) + Zhipu body-JSON regex fallbacks, both placed AFTER all existing message patterns but BEFORE `return None`
- Appended CJK billing ("余额不足", "账户余额不足", "欠费", "账户已欠费") to `_BILLING_PATTERNS`
- Appended CJK auth ("无权访问", "认证失败", "鉴权失败", "密钥无效", "apikey 无效") to `_AUTH_PATTERNS`
- Added `import re` (file did not previously import it)

**tests/agent/test_error_classifier.py** (3 new test classes, 73 new tests):
- `TestOpenclawCjkPatterns` — 38 parametrized cases covering all 4 categories in English + CJK
- `TestZhipuErrorCodes` — 7 cases covering structured-body, raw-JSON-string, and int-form code variants for 1305/1311/1113
- `TestCjkBillingAndAuthPatterns` — 9 parametrized cases for the appended CJK billing/auth entries

### Task 2: classify_response_body_error helper + conversation_loop hook (RED: 20c883584, GREEN: c9e1ca8d4)

**agent/error_classifier.py:**
- New public function `classify_response_body_error(response) -> Optional[ClassifiedError]` — extracts an error embedded in a successful-HTTP response by walking 3 shapes (response.error as dict/object, response.choices[0].message.error, response.body dict), wraps it in a `_SyntheticBodyError`, and routes through `classify_api_error`
- New `_SyntheticBodyError(Exception)` class — carries a `body` dict so `_extract_error_body` / `_extract_error_code` work unchanged; `.status_code` deliberately None (HTTP was 200)
- Defensive `isinstance()` checks throughout per threat model T-t0q-01

**agent/conversation_loop.py** (43-line insertion at line 1234):
- Pre-check inserted IMMEDIATELY BEFORE the `if response_invalid:` block
- When `classify_response_body_error` returns a retryable reason in {rate_limit, overloaded, server_error, timeout}, raises a `_SyntheticBodyError` so the existing `except Exception as api_error:` handler (line 1945+) — which already calls `classify_api_error` and routes to the correct retry/fallback — takes over
- Local lazy import (`from agent.error_classifier import ...`) — no module-top import changes
- **Retry/fallback/give-up loop (originally lines 1342+) is byte-identical** — verified by `git diff` showing a single hunk

**tests/agent/test_error_classifier.py** (1 new test class, 10 new tests):
- `TestClassifyResponseBodyError` — covers None response, no-error response, dict/object/nested/body-dict error shapes, Zhipu 1305/1311/1113 via helper, CJK message without structured code, unrecognized code excluded from retryable path

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two English openclaw serverError patterns collided with existing classifier paths**

- **Found during:** Task 1 GREEN phase
- **Issue:** The plan said to port openclaw serverError verbatim, which includes `"internal_error"` and `"connection reset"`. These caused two test regressions:
  - `"Connection reset by peer"` (a `ConnectionError`) was re-routed from `timeout` (correct, transport-error heuristic) to `server_error`
  - `"[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error"` was re-routed from `timeout` (correct, SSL transient path) to `server_error`
- **Root cause:** `_classify_by_message` (where the openclaw fallback lives) runs at step 4 of the `classify_api_error` pipeline, BEFORE the SSL transient check (step 5) and the transport-error heuristic (step 7). The two colliding strings preempted the correct later-stage classifications.
- **Fix:** Deliberately omitted `"internal_error"` and `"connection reset"` from `_OPENCLAW_SERVER_ERROR_STRINGS`. Documented the omission inline. Updated one parametrized test case to remove `"internal_error"` (it had no prior hermes classifier and was a net-new openclaw port).
- **Files modified:** agent/error_classifier.py, tests/agent/test_error_classifier.py
- **Commit:** 78351d357

All other openclaw English entries (e.g. "internal server error", "bad gateway", "gateway timeout", "service_unavailable") were kept — they have no collision with existing hermes paths and add net-new coverage.

## Threat Model Compliance

| Threat ID | Mitigation Status |
|-----------|-------------------|
| T-t0q-01 (Tampering — response.error parsing) | **Applied.** `classify_response_body_error` uses `isinstance()` checks before every dict/string access; no `eval()`, only defensive attribute walking. Message length capped via `_extract_message` (500 chars). |
| T-t0q-02 (Info Disclosure — CJK in logs) | **Accepted.** Pattern strings carry no PII; error messages flow through existing `_clean_error_message`. |
| T-t0q-03 (DoS — regex backtracking) | **Applied.** All ported patterns are linear-time. The two JS lookahead patterns (Zhipu gRPC-status-as-JSON) compile cleanly with Python's `re` and contain no nested quantifiers. |
| T-t0q-04 (Tampering — Zhipu code regex on raw body) | **Accepted.** Read-only regex; false-positive only triggers retry. |

No package installs in this plan — supply-chain gate N/A.

## Test Results

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total tests in `test_error_classifier.py` | 161 | 233 | +72 |
| Passing | 161 | 233 | +72 |
| Failing | 0 | 0 | 0 |

New test classes:
- `TestOpenclawCjkPatterns` — 37 tests (38 parametrized cases, 1 dropped as collision fix)
- `TestZhipuErrorCodes` — 7 tests
- `TestCjkBillingAndAuthPatterns` — 9 tests
- `TestClassifyResponseBodyError` — 10 tests
- Miscellaneous additions to existing classes — 9 tests

## TDD Gate Compliance

Both tasks followed strict RED/GREEN cycle:

| Task | RED commit (test fails) | GREEN commit (test passes) |
|------|-------------------------|----------------------------|
| Task 1 | `98d5d726c` — 61 tests failing | `78351d357` — all 223 passing |
| Task 2 | `20c883584` — import error (whole module uncollectable) | `c9e1ca8d4` — all 233 passing |

RED gate committed before GREEN for both tasks. No REFACTOR commits needed (code was clean on first GREEN pass).

## Verification (Sample Log Lines)

The original failing case — Zhipu HTTP 200 + `{"error":{"code":"1305","message":"该模型当前访问量过大"}}` — now classifies correctly:

```
# Direct helper call (the contract the conversation_loop relies on):
classify_response_body_error(SimpleNamespace(
    error={'code':'1305','message':'该模型当前访问量过大'},
    choices=[], model='glm-4.6'
))
→ ClassifiedError(reason=FailoverReason.overloaded, retryable=True, message='该模型当前访问量过大')

# Bare message classification (e.g. if the structured code is lost):
classify_api_error(Exception("该模型当前访问量过大"))
→ ClassifiedError(reason=FailoverReason.overloaded, retryable=True)

# Raw JSON body string (transport-flattened case):
classify_api_error(Exception('{"error":{"code":1305,"message":"该模型当前访问量过大"}}'))
→ ClassifiedError(reason=FailoverReason.overloaded, retryable=True)
```

In the conversation_loop, the new pre-check converts these into a `_SyntheticBodyError` raise, which the existing `except Exception as api_error:` handler catches and routes through the standard retry-with-backoff path (instead of the old behavior of burning all retries as "InvalidAPIResponse" and giving up).

## Commits

| Hash | Type | Message |
|------|------|---------|
| `98d5d726c` | test | RED — failing CJK + Zhipu code tests |
| `78351d357` | feat | GREEN — openclaw patterns + Zhipu codes ported |
| `20c883584` | test | RED — failing classify_response_body_error tests |
| `c9e1ca8d4` | feat | GREEN — helper + conversation_loop hook |

## Self-Check: PASSED

- agent/error_classifier.py — FOUND
- agent/conversation_loop.py — FOUND
- tests/agent/test_error_classifier.py — FOUND
- Commit `98d5d726c` — FOUND
- Commit `78351d357` — FOUND
- Commit `20c883584` — FOUND
- Commit `c9e1ca8d4` — FOUND
