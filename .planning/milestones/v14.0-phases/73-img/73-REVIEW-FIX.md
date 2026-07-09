---
phase: 73-img
fixed_at: 2026-07-09T15:10:00Z
review_path: .planning/phases/73-img/73-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 73: Code Review Fix Report

**Fixed at:** 2026-07-09T15:10:00Z
**Source review:** .planning/phases/73-img/73-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 9 (2 critical + 7 warnings; info findings excluded per default fix_scope=critical_warning)
- Fixed: 9
- Skipped: 0

**Cross-repo topology:** All fixes target the `kais-hermes-skills` repo (commit
landing in branch `gsd-reviewfix/73-2775331`, to be fast-forwarded into
`master`). This REVIEW-FIX.md itself is the hermes-agent phase artifact.

## Fixed Issues

### CR-01: `subprocess.run(text=True)` without `encoding=` violates CLAUDE.md PLW1514 — blocks CI merge

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`
**Commit:** bf03f15
**Applied fix:** Added `encoding="utf-8"` to all 3 `subprocess.run(...)` call
sites (`_dreamina_submit` line 301, `_dreamina_poll` line 335,
`_dreamina_image2image` line 469). Without this, Windows cp1252 default would
mojibake the Chinese characters in `_escalate_prompt` (`"左舵LHD"`,
`"方向盘在左侧"`) and the Chinese-containing query_result JSON — exactly the
corruption the PLW1514 Ruff rule exists to prevent, and which blocks CI merge.

### CR-02: IMG-05 metrics pipeline is entirely dead — dashboard always shows "(no data)"

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`
**Commit:** 524864e
**Applied fix:** Wired `record_metric()` into `batch_submit` — after
`asyncio.gather` resolves, iterate `(item, result)` pairs, infer stratum from
the item dict via a new `_infer_stratum()` helper (1-ref / 3-ref / 5-ref /
text2image based on `ref_count` field, falling back to structural signals like
`lhd_reference_path`/`directional`), and call `record_metric(metrics_path,
metric_dict)` per task. All writes wrapped in nested try/except so a single
metric failure never crashes the batch. The metrics_path is computed via the
imported `_metrics_file()` from `dreamina_stats`. The `hermes dreamina stats`
dashboard will now populate with real per-task latency / success / confidence
data instead of the "(no data)" empty-state branch. **Requires human
verification:** the stratum inference logic uses `ref_count` if provided by the
caller, else falls back to `1-ref` when `lhd_reference_path`/`directional` is
set, else `text2image` — confirm this matches the production item schema.

### WR-01: Confidence regex misparses percentage-format confidence (87 → 87.0, not 0.87)

**Files modified:** `plugins/kais_aigc/vision_verify.py`
**Commit:** 3c48533
**Applied fix:** In `_parse_vision_response`, after parsing the confidence
float, if `confidence > 1.0`: divide by 100 when in the `(1.0, 100.0]` range
(treat as percentage); clamp to 1.0 when above 100.0 (implausible value). A
warning is logged in the clamp branch. This prevents a percentage-form
response like "置信度87%" from bypassing the 0.7 threshold as a false-pass
(87.0 ≥ 0.7 → now correctly becomes 0.87).

### WR-02: Dead `_degrade` helper in dreamina_manager.py (defined, never called)

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`
**Commit:** e56901b
**Applied fix:** Deleted the `_degrade(operation, reason)` function (lines
381-393, ~18 lines including section header comment). All failure paths in
`_generate_one_with_verify` inline-construct `DreaminaTaskResult` dicts
directly and were never going to call `_degrade` (the sibling-module
convention it mirrored doesn't apply here — `dreamina_manager` has richer
per-failure context like `latency_ms`/`retries`/`vision_confidence`).

### WR-03: `record_metric` accepts unvalidated dict — Pydantic schema is decorative

**Files modified:** `plugins/kais_aigc/dreamina_stats.py`
**Commit:** 2ba021c
**Applied fix:** `record_metric` now validates `metric` via
`DreaminaTaskMetrics(**metric).model_dump_json()` before writing to the JSONL
file. Invalid metrics (unknown field, bad stratum, out-of-range confidence)
raise Pydantic `ValidationError` at write time — the CR-02 caller wraps this in
try/except per-task so one bad metric doesn't crash the batch, but typos like
`"stratum": "1ref"` (missing hyphen) or `"vision_confidence": 1.2` will be
caught at the source rather than silently corrupting the dashboard.

### WR-04: Partial SSRF mitigation — scheme check only, no host allowlist

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`
**Commit:** fb8adeb
**Applied fix:** Per fix guidance preference (comment-only), added a 14-line
docstring/comment block to `_extract_image_url` documenting: (a) the current
check only validates URL scheme, not host; (b) the known exploit paths (AWS
IMDS, internal Redis via localhost); (c) the deliberate-defer rationale —
byteimg.com CDN has many regional host variants (p3/p6/p9-byteimg.com) making
an allowlist brittle, dreamina is trusted, and full ipaddress-based loopback
filtering is a future hardening task if an untrusted response source is ever
introduced. No runtime behavior change.

### WR-05: `output_path` and `ref_image_path` built from unguarded `item_id` — path traversal possible

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`
**Commit:** 4159da3
**Applied fix:** Added module-level `_SAFE_ITEM_ID = re.compile(r"^[A-Za-z0-9_\-]+$")`
constant. At the top of `_generate_one_with_verify`, before deriving
`output_path`, the `item_id` is matched against this regex; any value
containing path separators / traversal sequences / non-safe chars raises
`ValueError` with a descriptive message. This blocks the
`item_id="../../etc/cron.d/evil"` → `output_dir/etc/cron.d/evil.png` escape
vector at the trust boundary. Added `import re` at module top.

### WR-06: `_dreamina_poll` timeout (raw=None) and malformed response paths untested

**Files modified:** `plugins/kais_aigc/tests/test_dreamina_manager.py`
**Commit:** 53bfc18
**Applied fix:** Added two new async test cases:
- `test_poll_timeout_returns_degraded`: mocks `_dreamina_poll` to always return
  `None` (simulating 180s timeout or `gen_status="failed"`). Asserts the task
  returns `status in ("failed", "degraded")` — never raises to the caller.
- `test_malformed_response_returns_failed`: mocks `_dreamina_submit` to always
  raise `RuntimeError("dreamina submit returned invalid JSON: ...")`. Asserts
  the task returns `status in ("failed", "degraded")` with a non-None `error`
  field containing "invalid JSON" or "RuntimeError". Both tests patch
  tenacity's `wait_exponential` to no-wait for speed.

### WR-07: Cache dict mutation under concurrent batch tasks — no lock, possible double-GLM-call

**Files modified:** `plugins/kais_aigc/vision_verify.py`
**Commit:** 7904bd0
**Applied fix:** Per fix guidance preference (verify-and-document), added an
18-line docstring block to `_cache` documenting: (a) CPython GIL makes
individual dict ops atomic (no corruption); (b) the check-then-insert race
under concurrent `verify_image_content` calls is an inefficiency (one wasted
GLM call), not a correctness bug; (c) the dominant dedup win is across
iterative editing runs (separate `batch_submit` invocations) where there is no
concurrency; (d) within a single batch, `verify_batch` is the correct dedup
unit; (e) explicit guidance to revisit with an in-flight Future marker if a
future caller invokes `verify_image_content` concurrently with high
image-duplicate rates. No runtime behavior change.

---

_Fixed: 2026-07-09T15:10:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
