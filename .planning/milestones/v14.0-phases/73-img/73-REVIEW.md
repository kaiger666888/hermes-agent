---
phase: 73-img
reviewed: 2026-07-09T14:56:40Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/__init__.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_manager.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_vision_verify.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_stats.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_integration.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p07_unit.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md
findings:
  critical: 2
  warning: 7
  info: 4
  total: 13
status: issues_found
---

# Phase 73: Code Review Report

**Reviewed:** 2026-07-09T14:56:40Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed the IMG phase (73) source: `dreamina_manager.py` (asyncio batch orchestrator), `vision_verify.py` (GLM-4.6V gate), `dreamina_stats.py` (sync JSONL metrics), `__init__.py` (CLI registration), `p07_scene_generation.py` (vision-verify injection), 4 test files, 2 SKILL.md body patches, and 1 new ref. The core concurrency architecture (Semaphore + gather block-on-all + 3-attempt escalation) is sound, and the IMG-02 sync-queue invariant is correctly implemented. However, I found **2 blockers** (one Ruff-gating PLW1514 violation on all 3 `subprocess.run(text=True)` calls — per CLAUDE.md this blocks merge; one functional defect where IMG-05 metrics pipeline is entirely dead — no production caller writes to the JSONL the dashboard reads). The `task="vision"` routing (NOT `prefer_vision=True`) is correctly verified, the 3-attempt RHD/LHD escalation state machine traces correctly, and the XCUT-02 dual injection is present in both `.task(steps=)` and `.constraints()` with the constraint count (5) within the MAX_CONSTRAINTS=7 budget. Frontmatter on both SKILL.md files is byte-identical above the body patches.

The adversarial stance surfaced 7 warnings spanning: percentage-format confidence misparse, dead `_degrade` helper, missing `record_metric`/schema validation wiring, partial SSRF mitigation (scheme check only, no host allowlist), unguarded path components in `output_path`/`ref_image_path`, and an untested poll-timeout path.

## Critical Issues

### CR-01: `subprocess.run(text=True)` without `encoding=` violates CLAUDE.md PLW1514 — blocks CI merge

**File:** `plugins/kais_aigc/dreamina_manager.py:301, 334, 467`
**Issue:** All three `subprocess.run(...)` calls use `text=True` without `encoding="utf-8"`. Per CLAUDE.md: *"PLW1514 (`unspecified-encoding`) is the single load-bearing rule. It forces every `open()` / `read_text()` / `write_text()` to pass an explicit `encoding="utf-8"`."* PLW1514 also covers `subprocess.run(text=True)` (Ruff treats text-mode subprocess I/O the same as file text-mode). The CI workflow at `.github/workflows/lint.yml` makes `ruff check .` blocking. On Windows, the default cp1252 would silently corrupt the Chinese characters in dreamina prompts (`"左舵LHD"`, `"方向盘在左侧"`) and the Chinese-containing query_result JSON — exactly the corruption PLW1514 exists to prevent.

This is not hypothetical: the prompts embedded in `_escalate_prompt` (lines 428-431) contain Chinese characters that would be mojibake'd on a Windows runner.

**Fix:**
```python
# Line 301
result = await loop.run_in_executor(
    None,
    lambda: subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        timeout=15,
    ),
)
# Line 334 — same change
# Line 467 — same change (timeout=30 stays)
```

### CR-02: IMG-05 metrics pipeline is entirely dead — dashboard always shows "(no data)"

**File:** `plugins/kais_aigc/dreamina_manager.py` (missing call); `plugins/kais_aigc/dreamina_stats.py:91` (`record_metric`); `plugins/kais_aigc/dreamina_stats.py:56` (`DreaminaTaskMetrics`)
**Issue:** The IMG-05 acceptance criterion promises a MetricsBuffer JSONL ring buffer that `hermes dreamina stats` reads. `dreamina_stats.py` defines `record_metric(path, metric)` and the `DreaminaTaskMetrics` Pydantic schema. The CLI (`_cmd_stats` → `read_metrics`) reads from `~/.hermes/metrics/dreamina_stats.jsonl`. **But no production code ever calls `record_metric` or constructs a `DreaminaTaskMetrics`.** I grepped the entire plugin: `record_metric` is referenced only in `dreamina_stats.py` itself (definition + docstring) and `test_dreamina_stats.py` (test). `dreamina_manager.batch_submit()` — the one place that has access to per-task latency/success/retries/confidence — returns `DreaminaTaskResult` dicts and discards them to the caller without ever writing a metric record.

Consequence: the `hermes dreamina stats` dashboard will **always** render the "(no data)" empty-state branch (`_emit_rich` line 223-230). The IMG-05 feature is structurally non-functional. The ref `image2image-stratification.md:87-100` even documents the expected dashboard output with non-zero counts — that output is impossible to achieve with the shipped code.

**Fix:** Wire `record_metric` into `batch_submit` (or `_generate_one_with_verify`). After each task resolves, append a metrics record. Example insertion at the end of `_generate_one_with_verify` (before each `return`), or wrap the return at the `batch_submit` level:

```python
# In batch_submit, after gather resolves:
from plugins.kais_aigc.dreamina_stats import record_metric, _metrics_file
from datetime import datetime, timezone

mf = _metrics_file()
for item, result in zip(prompts, results):
    stratum = "text2image"  # or detect from item.get("stratum")
    try:
        record_metric(mf, {
            "submit_id": result["submit_id"] or "unknown",
            "stratum": stratum,
            "latency_ms": result["latency_ms"],
            "success": result["status"] == "ok",
            "retries": result["retries"],
            "vision_verified": result["vision_verified"],
            "vision_confidence": result["vision_confidence"],
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.warning("dreamina metric write failed", exc_info=True)
return list(results)
```

Note: this also requires the caller to pass `stratum` in the item dict, OR `batch_submit` must infer stratum from `directional`/`lhd_reference_path`. Currently the item schema has no `stratum` field — the stratification layer is unimplemented end-to-end.

## Warnings

### WR-01: Confidence regex misparses percentage-format confidence (87 → 87.0, not 0.87)

**File:** `plugins/kais_aigc/vision_verify.py:227-230`
**Issue:** `_parse_vision_response` uses `r"置信度.*?([0-9.]+)"` / `r"confidence.*?([0-9.]+)"`. The prompt at line 207-209 asks for "置信度(0-1)" but GLM-4.6V may respond with percentage forms like "置信度87%" or "confidence: 87/100". The regex would capture `87` → `float("87") == 87.0`, which is `>= 0.7` → `passed = True`. A 0.87-confidence image passes correctly, but an image the model rates "87% confident NO" (i.e., 13% yes) would also pass because the number 87 is captured regardless of polarity. Worse: any value ≥ 1.0 from a percentage response bypasses the 0.7 threshold entirely.

The `_build_question` prompt does request "0-1" but provides no enforcement; the parse is unconditional.

**Fix:** Either (a) clamp + sanity-check, or (b) parse the yes/no polarity alongside confidence:
```python
# Reject implausible values (>1.0 not in 0-1 range as requested):
confidence = float(m.group(1)) if m else 0.5
if confidence > 1.0:
    logger.warning("vision confidence out of 0-1 range: %s — clamping", confidence)
    confidence = min(confidence / 100.0, 1.0) if confidence > 1.5 else 1.0
# Also parse polarity — "否" / "no" should force pass=False regardless of confidence:
negative = re.search(r"否|not|no\b", text, re.I)
if negative:
    passed = False
```

### WR-02: Dead `_degrade` helper in dreamina_manager.py (defined, never called)

**File:** `plugins/kais_aigc/dreamina_manager.py:381-393`
**Issue:** The module-level `_degrade(operation, reason)` function is defined to "mirror jimeng.py:212-220" but is **never called anywhere in `dreamina_manager.py`**. All failure paths inline-construct `DreaminaTaskResult` dicts directly (lines 205-214, 264-273). Compare to the sibling modules where `_degrade` IS used: `jimeng.py:258,292,308,314`, `gold_team.py:193,196,203,338,340,386`, `canvas.py:197,207,219,249,308`, `feedback_client.py:138,140,144,218,220`, `review_platform.py:222,225,229`. This is dead code per CLAUDE.md anti-patterns.

**Fix:** Either delete the function (lines 378-393, ~16 lines) or refactor the inline `return {... "failed" ...}` blocks to call `_degrade(...)` for consistency with the sibling-module convention. Deleting is simpler and lower-risk.

### WR-03: `record_metric` accepts unvalidated dict — Pydantic schema is decorative

**File:** `plugins/kais_aigc/dreamina_stats.py:91-103` (`record_metric`); `:56-85` (`DreaminaTaskMetrics`)
**Issue:** `record_metric(path, metric)` writes `metric` straight to JSONL via `json.dumps` with **zero schema validation**. The `DreaminaTaskMetrics` Pydantic model (with `extra="forbid"`, `stratum` enum, `ge`/`le` bounds) is exercised only in `test_dreamina_task_metrics_schema`. Production writes (if/when CR-02 is fixed by wiring the call) would bypass validation entirely — a typo like `"vision_confidence": 1.2` or `"stratum": "1ref"` (missing hyphen) would land in the JSONL silently and surface only as a weird dashboard row.

**Fix:** Validate inside `record_metric`:
```python
def record_metric(path: Path, metric: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    validated = DreaminaTaskMetrics(**metric)  # raises on invalid
    line = validated.model_dump_json()
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
```

### WR-04: Partial SSRF mitigation — scheme check only, no host allowlist

**File:** `plugins/kais_aigc/dreamina_manager.py:349-359` (`_extract_image_url`); `:365-375` (`_download`)
**Issue:** T-73-02 (per the file docstring) calls for SSRF mitigation. The implementation checks `url.startswith("http://") or url.startswith("https://")` — this blocks `file://`, `gopher://`, `ftp://` schemes. **But it does NOT validate the host.** If a compromised or buggy dreamina response returns `http://169.254.169.254/latest/meta-data/iam/security-credentials/` (AWS IMDS), `http://localhost:6379/` (Redis), or an internal-only IP, `_download` will fetch it via httpx and write the response body to `output_path`. In a cloud deployment this leaks instance metadata.

The dreamina system is trusted and returns byteimg.com CDN URLs in practice, so exploitability is low — but the comment claims SSRF mitigation and the mitigation is incomplete.

**Fix:** Either (a) allowlist the known dreamina CDN hosts, or (b) block link-local/loopback:
```python
from urllib.parse import urlparse
import ipaddress

_ALLOWED_HOSTS = {"byteimg.com", "p3-byteimg.com", "*.byteimg.com"}  # dreamina CDN

def _is_safe_url(url: str) -> bool:
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    parsed = urlparse(url)
    host = parsed.hostname or ""
    # Block loopback / link-local / private (SSRF defense-in-depth):
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            logger.warning("dreamina image_url points to internal IP: %s", host)
            return False
    except ValueError:
        pass  # hostname, not IP — allowlist check below
    return any(host == h or host.endswith("." + h.lstrip("*.")) for h in _ALLOWED_HOSTS)
```

### WR-05: `output_path` and `ref_image_path` built from unguarded `item_id` — path traversal possible

**File:** `plugins/kais-aigc/plugins/kais_aigc/dreamina_manager.py:155` (`output_path`); `:178, 456` (`ref_image_path`)
**Issue:** `output_path = str(Path(output_dir) / f"{item_id}.png")`. If `item_id` (sourced from the item dict, ultimately from pipeline state / batch JSON) contains `..` or absolute-path components, the resulting path escapes `output_dir`. Example: `item_id = "../../etc/cron.d/evil"` → writes to `{repo_root}/etc/cron.d/evil.png` (or worse on a system that ignores extension). Similarly `ref_image_path` from `item.get("lhd_reference_path")` is passed verbatim into `--images={ref_image_path}` on the dreamina CLI subprocess — while the list form prevents shell injection, a malicious path could point at sensitive files for the CLI to read.

The pipeline-state provenance makes this low-exploitability in normal operation, but there is **no defensive check** at the trust boundary.

**Fix:** Sanitize `item_id` and validate `ref_image_path`:
```python
import re
_SAFE_ID = re.compile(r"^[A-Za-z0-9_\-]+$")

item_id = item.get("id", "unknown")
if not _SAFE_ID.match(item_id):
    raise ValueError(f"unsafe item_id rejected: {item_id!r}")
output_path = str(Path(output_dir) / f"{item_id}.png")

# For ref_image_path:
ref_path = item.get("lhd_reference_path", "")
if ref_path:
    rp = Path(ref_path).resolve()
    if not rp.exists():
        raise FileNotFoundError(f"lhd_reference_path missing: {ref_path}")
```

### WR-06: `_dreamina_poll` timeout (raw=None) and `gen_status="failed"` paths untested

**File:** `plugins/kais_aigc/tests/test_dreamina_manager.py` (missing); `plugins/kais_aigc/dreamina_manager.py:316-346`
**Issue:** The 5 unit tests + 2 integration tests mock `_dreamina_poll` to always return a success dict. None of the tests exercise: (a) `_dreamina_poll` returning `None` (180s timeout exceeded); (b) `gen_status` in `("failed", "error", "fail")` → returns None; (c) `_dreamina_submit` returning empty `submit_id`; (d) `result.stdout` being empty / non-JSON; (e) `_extract_image_url` returning None (no images array). These are all documented failure modes with explicit `raise RuntimeError(...)` handling (lines 191-195, 307-313, 344-346) that the submission claims is tested but isn't.

The poll-timeout path in particular is operationally important: a 180s poll timeout cascades into a wasted outer attempt (3-attempt budget consumed faster than expected), which changes the degraded-vs-failed outcome for the operator.

**Fix:** Add at minimum:
```python
@pytest.mark.asyncio
async def test_poll_timeout_returns_none_propagates(monkeypatch, tmp_path):
    """When _dreamina_poll returns None (timeout), the task fails cleanly."""
    _patch_verify(monkeypatch)
    async def _poll_none(submit_id, max_wait=180):
        return None
    # ... wire mocks, assert result["status"] in ("failed", "degraded")

@pytest.mark.asyncio
async def test_malformed_submit_json_raises(monkeypatch, tmp_path):
    """Empty / non-JSON stdout from dreamina submit → RuntimeError → retry."""
    # ... mock subprocess.run to return stdout=""
```

### WR-07: Cache dict mutation under concurrent batch tasks — no lock, possible double-GLM-call

**File:** `plugins/kais_aigc/vision_verify.py:38` (`_cache`); `:81-89, 113-116, 145-158`
**Issue:** `_cache` is a module-level dict mutated by both `verify_image_content` and `verify_batch` without any lock. In `batch_submit`, up to 10 concurrent `_generate_one_with_verify` tasks run; each may call `verify_image_content`. CPython's GIL makes individual dict get/set/del atomic (no corruption), but the check-then-insert pattern is racy: two tasks with the same `sha` (same image file submitted twice in a batch) will both miss the cache, both invoke GLM-4.6V (~2-5s each), and both write — wasting one API call.

This is a latent inefficiency, not a correctness bug (the dict never corrupts and both writes are idempotent). But the IMG-03 design intent ("cuts overhead 4-8x via batching") is undermined if the cache hands out duplicate work under concurrency.

**Fix:** Either (a) accept the race and document it (the dedup win is still real across iterative editing runs, the dominant case), or (b) use an in-flight marker:
```python
_cache: dict[str, dict[str, Any]] = {}
_inflight: dict[str, asyncio.Future] = {}

async def verify_image_content(...):
    ...
    if sha in _cache:  # fast path
        ...
    if sha in _inflight:  # another task is verifying this exact image
        return await _inflight[sha]
    fut = asyncio.get_event_loop().create_future()
    _inflight[sha] = fut
    try:
        result = await _actual_verify(...)
        _cache[sha] = {**result, "_ts": time.time()}
        result["cached"] = False
        fut.set_result(result)
        return result
    finally:
        _inflight.pop(sha, None)
```

## Info

### IN-01: `for attempt in range(3)` + `except Exception` swallows tenacity `RetryError` silently into outer retry — works but masks retry attribution

**File:** `plugins/kais_aigc/dreamina_manager.py:164-214`
**Issue:** When tenacity `AsyncRetrying` exhausts 4 attempts on a transient error, it raises `RetryError` (subclass of `Exception`). The broad `except Exception` catches it, formats `last_error = "RetryError: ..."`, and continues the outer attempt loop. This is functionally correct but conflates "transient error exhausted tenacity retries" (should maybe escalate faster) with "permanent error" (RuntimeError from missing lhd_reference_path). The `retries` field in the result dict counts outer attempts, not tenacity attempts — operators reading "retries: 2" can't tell whether that's 2 outer × 4 tenacity = 8 actual CLI calls or 2 outer × 1 = 2 CLI calls.

**Fix:** Either narrow the except to `(RetryError, TimeoutError, ConnectionError, subprocess.TimeoutExpired, RuntimeError)`, or log the tenacity attempt count:
```python
except Exception as exc:
    last_error = f"{type(exc).__name__}: {exc}"
    logger.warning("dreamina %s outer-attempt %d failed (%s) — retrying",
                   item_id, attempt + 1, last_error, exc_info=True)
```
Low priority — current code doesn't crash, just makes ops harder.

### IN-02: `_escalate_prompt` only handles `directional == "lhd"` — `"rhd"` falls through to plain base prompt

**File:** `plugins/kais_aigc/dreamina_manager.py:399-434`
**Issue:** The function's docstring says "RHD/LHD 3-attempt budget" but only `directional == "lhd"` gets the steering-wheel emphasis / negative-prompt escalation. For `directional == "rhd"`, attempt 0 returns `base_prompt`, attempt 1 returns `f"{base_prompt} (stronger emphasis)"`, attempt 2 returns None (image2image). The LHD-specific escalation strings never fire for RHD. The docstring at line 9-12 of the module acknowledges this: *"directional='lhd' is the first instantiation."* So this is known-incomplete, not a bug — but the public function name and SKILL.md references promise "RHD/LHD 3-attempt budget", which is misleading for the RHD case.

**Fix:** Either (a) implement RHD escalation symmetrically, or (b) rename + narrow the docstring to "LHD 3-attempt budget (RHD is a future instantiation)".

### IN-03: `MAX_CONSTRAINTS` budget check passes (5 ≤ 7) but `_VISION_VERIFY_INSTRUCTION` in `.task(steps=)` is duplicated info with the `.constraints()` rule

**File:** `skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py:125, 164`
**Issue:** The XCUT-02 dual-injection requirement is correctly satisfied: `_VISION_VERIFY_INSTRUCTION` (4 numbered points, ~600 chars) appears in `.task(steps=[...])` and "MUST vision-verify every image before ComfyUI upload (IMG-03 mandatory gate)" appears in `.constraints([...])`. Constraint count = 5 ≤ MAX_CONSTRAINTS=7 ✓. However, the `.task(steps=)` injection is a single string element inside a list that otherwise contains short imperative steps ("Load all four experts via skill_view", "style_genome constructs 5D style vector"). The ~600-char instruction is ~30× longer than its siblings and will dominate the task-segment token budget. Consider hoisting it to a dedicated segment or trimming to 2-3 lines + a pointer to the SKILL.md ref. Minor prompt-engineering concern, not a defect.

### IN-04: `read_metrics` does not enforce the documented "ring buffer" semantic — file grows unbounded

**File:** `plugins/kais_aigc/dreamina_stats.py:106-141`
**Issue:** The docstring says "ring buffer: last 1000 entries". `read_metrics(path, limit=1000)` returns `out[-limit:]` — so it returns the last 1000, but the **file itself is never truncated**. `record_metric` only ever appends. Over weeks of operation the JSONL file grows past 1000 lines indefinitely; `read_metrics` will read the entire file into memory (`out` list) then slice. For 10k+ lines this is O(n) memory + parse cost on every `hermes dreamina stats` invocation. The "ring buffer" name is a misnomer — it's a "read-side tail window" over an unbounded append log.

**Fix:** Either (a) rename to "tail buffer" / "last-N read window", or (b) implement actual ring-buffer rotation in `record_metric` (read-all, trim to 1000, rewrite — expensive) or via a separate compaction job. Given INFRA-04's sync-only constraint, option (a) is lower-risk.

---

_Reviewed: 2026-07-09T14:56:40Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
