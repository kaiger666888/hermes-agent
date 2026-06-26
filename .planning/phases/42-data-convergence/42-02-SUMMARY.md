---
phase: 42-data-convergence
plan: 02
subsystem: plugins/platform_metrics
tags: [adapters, platform-api, httpx, operator-handoff, stubs, DATA-01]
requires:
  - "42-01 (BasePlatformAdapter ABC + ADAPTER_REGISTRY + PlatformMetrics schema)"
provides:
  - "DouyinOpenAdapter (douyin, DOUYIN_API_KEY, OAuth2)"
  - "KuaishouOpenAdapter (kuaishou, KUAISHOU_API_KEY, OAuth2)"
  - "WeixinVideoAdapter (weixin_video, WEIXIN_VIDEO_API_KEY, cookie-based)"
  - "XiaohongshuShutiaoAdapter (xiaohongshu, XIAOHONGSHU_API_KEY, cookie-based)"
  - "BilibiliCreatorAdapter (bilibili, BILIBILI_API_KEY, OAuth2)"
  - "5 platforms registered in ADAPTER_REGISTRY (SC#1 adapter half)"
affects:
  - "Plan 42-03 (tuning_loop consumes activated adapters for fetch triggers)"
  - "Plan 42-04 (CLI + .env.example document the 5 env_key names shipped here)"
tech-stack:
  added: []
  patterns:
    - "Self-registration via register_adapter() at module import (mirror tools/registry.py)"
    - "Env-key activation gate via BasePlatformAdapter._require_activated()"
    - "NotImplementedError with V9-FUTURE-01 deferral message (operator-action-handoff)"
    - "TDD: RED test commit (32 failing) → GREEN implementation commit (5 adapters) → tests pass"
key-files:
  created:
    - path: plugins/platform_metrics/adapters/douyin.py
      lines: 125
      class: DouyinOpenAdapter
    - path: plugins/platform_metrics/adapters/kuaishou.py
      lines: 114
      class: KuaishouOpenAdapter
    - path: plugins/platform_metrics/adapters/weixin_video.py
      lines: 112
      class: WeixinVideoAdapter
    - path: plugins/platform_metrics/adapters/xiaohongshu.py
      lines: 110
      class: XiaohongshuShutiaoAdapter
    - path: plugins/platform_metrics/adapters/bilibili.py
      lines: 116
      class: BilibiliCreatorAdapter
    - path: plugins/platform_metrics/tests/test_adapters.py
      lines: 347
      tests: 32
  modified: []
decisions:
  - "All 5 adapters raise NotImplementedError on live HTTP path (not just NotImplementedError stub). Message includes V9-FUTURE-01 + operator-handoff context + URL of planned endpoint."
  - "Cookie-based auth (weixin_video + xiaohongshu) documented in module docstring + cookie-rotation caveat called out for V9-FUTURE-01 implementer."
  - "Each adapter uses pure stdlib (logging + os). httpx referenced only in V9-FUTURE-01 pseudo-code comment block; no httpx import in v9.0 stubs."
  - "Module constants (OAUTH_TOKEN_URL, VIDEO_DATA_URL, CREATOR_BASE_URL) document planned V9-FUTURE-01 live targets — placeholders only, NOT called by v9.0."
metrics:
  duration: "~25min (incl. 5min wait for Plan 42-01 dependency)"
  completed: 2026-06-26T17:12:08Z
  tasks_completed: 3
  tasks_total: 3
  files_created: 6
  files_modified: 0
  tests_added: 32
  commits: 2
---

# Phase 42 Plan 02: 5 Platform Adapter Stubs Summary

**One-liner:** 5 platform adapter stubs (douyin / kuaishou / weixin_video / xiaohongshu / bilibili) subclass BasePlatformAdapter, activate via per-platform env_key, raise NotImplementedError with V9-FUTURE-01 operator-handoff message on live HTTP path, and self-register into ADAPTER_REGISTRY at module import — closes the DATA-01 adapter half.

---

## Goal Achieved

Plan 42-02 ships the concrete subclasses that Plan 42-01's `BasePlatformAdapter` ABC requires. With both plans landed, the contract holds:

- `ADAPTER_REGISTRY` keys exactly match `SUPPORTED_PLATFORMS_WITH_ADAPTERS` (`("douyin", "kuaishou", "weixin_video", "xiaohongshu", "bilibili")`).
- `get_adapter(name)` returns a fresh instance of the right subclass for any of the 5 platforms; raises `KeyError` for unknown names.
- Each adapter activates when its env var is non-empty; without it, `fetch()` raises `AdapterNotActivatedError` mentioning the exact env var name.
- Live HTTP path is deferred to V9-FUTURE-01: stubs raise `NotImplementedError` with the planned endpoint URL + operator-action-handoff message.
- Zero platform-specific SDK dependencies (pure stdlib + documented V9-FUTURE-01 httpx pseudo-code).

Operator-action-handoff (per Phase 42 CONTEXT): operators obtain platform API credentials and set the env keys; v9.0 ships the activation scaffold + schema validation only.

---

## Tasks Completed

| Task | Name | Commit | Tests |
|------|------|--------|-------|
| 1 | DouyinOpenAdapter + KuaishouOpenAdapter (OAuth2 platforms) | `0616c64b3` (RED) + `67405d7a6` (GREEN) | 10 per-adapter |
| 2 | WeixinVideoAdapter + XiaohongshuShutiaoAdapter (cookie-based) | `0616c64b3` + `67405d7a6` | 10 per-adapter + 2 cookie-doc |
| 3 | BilibiliCreatorAdapter + adapter registry integration tests | `0616c64b3` + `67405d7a6` | 5 per-adapter + 4 integration + 1 T-42-05 guard |

**TDD cycle:** Plan is `type: execute` with `tdd="true"` on all 3 tasks. RED commit (`0616c64b3`) ships the failing test file (32 tests, all ModuleNotFoundError on missing adapter modules). GREEN commit (`67405d7a6`) ships the 5 adapters; all 32 tests pass. No separate REFACTOR pass needed — adapters are ~110 lines each, single responsibility.

---

## Adapter Contract Verification

```
$ python3 -c "from plugins.platform_metrics.adapters import ADAPTER_REGISTRY; \
    import plugins.platform_metrics.adapters.douyin, \
    plugins.platform_metrics.adapters.kuaishou, \
    plugins.platform_metrics.adapters.weixin_video, \
    plugins.platform_metrics.adapters.xiaohongshu, \
    plugins.platform_metrics.adapters.bilibili; \
    print(sorted(ADAPTER_REGISTRY.keys()))"
['bilibili', 'douyin', 'kuaishou', 'weixin_video', 'xiaohongshu']
```

| Platform | Adapter Class | env_key | Auth Model | Endpoint Constants |
|----------|---------------|---------|------------|--------------------|
| douyin | DouyinOpenAdapter | DOUYIN_API_KEY | OAuth2 (client_credentials) | OAUTH_TOKEN_URL + VIDEO_DATA_URL (open.douyin.com) |
| kuaishou | KuaishouOpenAdapter | KUAISHOU_API_KEY | OAuth2 (access_token) | OAUTH_TOKEN_URL + VIDEO_DATA_URL (open.kuaishou.com) |
| weixin_video | WeixinVideoAdapter | WEIXIN_VIDEO_API_KEY | cookie-based | CREATOR_BASE_URL (channels.weixin.qq.com) |
| xiaohongshu | XiaohongshuShutiaoAdapter | XIAOHONGSHU_API_KEY | cookie-based | CREATOR_BASE_URL (creator.xiaohongshu.com) |
| bilibili | BilibiliCreatorAdapter | BILIBILI_API_KEY | OAuth2 (client_credentials) | OAUTH_TOKEN_URL + VIDEO_ANALYSIS_URL (member.bilibili.com) |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Fixed typo XIAOHONOSHU → XIAOHONGSHU in test_adapters.py**
- **Found during:** Task 1 (RED phase)
- **Issue:** Initial test file used misspelled env var `XIAOHONOSHU_API_KEY` in 6 places (Xiaohongshu has the "G" before "S"; common typo).
- **Fix:** `sed -i 's/XIAOHONOSHU_API_KEY/XIAOHONGSHU_API_KEY/g'` — all 6 instances corrected before commit.
- **Files modified:** `plugins/platform_metrics/tests/test_adapters.py` (pre-commit fix; never landed in repo).
- **Commit:** Fixed before RED commit (`0616c64b3`); not visible in git history.

### Deferred Cross-Plan Issues

**2. [Cross-plan — Plan 42-01 design] `test_adapter_registry_empty_at_import` fails after 42-02 ships (by design)**
- **Found during:** GREEN phase test-suite run.
- **Issue:** Plan 42-01's `tests/test_plugin_registration.py::test_adapter_registry_empty_at_import` asserts `len(ADAPTER_REGISTRY) == 0` after Plan 42-01 ships. Once Plan 42-02's `test_adapters.py` is co-collected (because it imports all 5 adapter modules at top-level, populating the singleton registry), this assertion fails.
- **Root cause:** Plan 42-01 plan text line 183 explicitly says `(Plan 42-02 populates it)` — the test was written as a one-shot invariant that is *expected* to break when 42-02 ships. It is not a regression; it is a forward-looking placeholder.
- **Why NOT auto-fixed:** Scope discipline forbids editing Plan 42-01's test files. The fix belongs to a phase-integration step (or Plan 42-04's full-plugin CLI test) — that step should either delete `test_adapter_registry_empty_at_import` or repurpose it to assert `len(ADAPTER_REGISTRY) >= 5`.
- **Impact:** Running the full `plugins/platform_metrics/tests/` suite yields 62 passed + 1 failed. Running `test_adapters.py` + `test_schema.py` in isolation yields 51 passed, 0 failed.
- **Files affected:** `plugins/platform_metrics/tests/test_plugin_registration.py` (Plan 42-01 owned — not modified by this plan).
- **Recommendation:** Phase 42 integration step (after Wave 2) should update or remove the brittle test.

---

## Threat Model Compliance

| Threat ID | Status | Verification |
|-----------|--------|--------------|
| T-42-05 (Info Disclosure — env var value in logs) | mitigated | `test_no_adapter_logs_env_value` (test_adapters.py:309) grep-asserts no adapter source contains forbidden `logger.*os.environ.get` or `logger.*key` patterns. Each adapter's `fetch()` reads `os.environ.get(self.env_key)` for a bool flag only; logs use `%s` with the bool, never the value. |
| T-42-06 (Spoofing — live HTTP response) | accept | Out of scope for v9.0 (stubs raise NotImplementedError before any HTTP call). V9-FUTURE-01 implementer owns TLS verification + response schema validation. Documented in stub messages. |
| T-42-07 (Tampering — variant_id → URL interpolation) | mitigate | v9.0 stubs raise NotImplementedError before any HTTP path. V9-FUTURE-01 messages document the urllib.parse.quote requirement. |
| T-42-08 (Repudiation — fetch audit trail) | accept | v9.0 stubs emit no side effects. V9-FUTURE-01 concern. |
| T-42-SC (Tampering — package install) | accept | N/A — pure stdlib; no pip installs introduced. |

---

## Known Stubs

All 5 adapters are intentional stubs by design (V9-FUTURE-01 operator-action-handoff). Each adapter's `fetch()`:
1. Calls `self._require_activated()` — real env-key check, works as intended.
2. Raises `NotImplementedError` with V9-FUTURE-01 message — intentional stub.
3. Below the raise (unreachable), documents the planned V9-FUTURE-01 live path as a pseudo-code comment block.

These stubs satisfy DATA-01 as scoped ("adapter stubs" — not "live API integration"). The plan-level deferral V9-FUTURE-01 is documented in the phase overview and is the operator-action-handoff contract for v9.0.

---

## Self-Check: PASSED

**Files verified to exist:**
- [x] `plugins/platform_metrics/adapters/douyin.py` — FOUND (125 lines, contains `class DouyinOpenAdapter`)
- [x] `plugins/platform_metrics/adapters/kuaishou.py` — FOUND (114 lines, contains `class KuaishouOpenAdapter`)
- [x] `plugins/platform_metrics/adapters/weixin_video.py` — FOUND (112 lines, contains `class WeixinVideoAdapter`)
- [x] `plugins/platform_metrics/adapters/xiaohongshu.py` — FOUND (110 lines, contains `class XiaohongshuShutiaoAdapter`)
- [x] `plugins/platform_metrics/adapters/bilibili.py` — FOUND (116 lines, contains `class BilibiliCreatorAdapter`)
- [x] `plugins/platform_metrics/tests/test_adapters.py` — FOUND (347 lines, 32 tests)

**Commits verified:**
- [x] `0616c64b3` — FOUND (`test(42-02): add failing tests for 5 platform adapters (RED)`)
- [x] `67405d7a6` — FOUND (`feat(42-02): add 5 platform adapter stubs registered into ADAPTER_REGISTRY`)

**Test suite verified:**
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_adapters.py` — 32 passed in 0.12s
- [x] `python3 -m pytest plugins/platform_metrics/tests/test_adapters.py plugins/platform_metrics/tests/test_schema.py` — 51 passed in 0.14s
- [x] Registry check: `len(ADAPTER_REGISTRY) == 5`, keys == `['bilibili', 'douyin', 'kuaishou', 'weixin_video', 'xiaohongshu']`

**Scope discipline verified:**
- [x] Zero edits to Hermes core (`agent/*`, `hermes_cli/*`)
- [x] Zero edits to Plan 42-01 owned files (`schema.py`, `adapters/base.py`, `adapters/__init__.py`, `plugin.yaml`, `__init__.py`, `README.md`, `tests/test_schema.py`, `tests/test_plugin_registration.py`)
- [x] Zero edits to Plan 42-03/42-04 owned files (`tuning_loop.py`, `library_writer.py`, `cli.py`, `skills/*`, `.env.example`)
- [x] Only 6 files touched: 5 NEW adapter files + 1 NEW test file

---

*Plan 42-02 executed: 2026-06-26 — 3/3 tasks complete, 32/32 tests GREEN, 5/5 adapters registered, 2 commits.*
