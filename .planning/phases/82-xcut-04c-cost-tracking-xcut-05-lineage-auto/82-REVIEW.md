---
phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto
reviewed: 2026-07-10T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py
  - /data/workspace/hermes-agent/scripts/bump_all_agent_lineage.py
findings:
  critical: 1
  warning: 4
  info: 5
  total: 10
status: issues_found
---

# Phase 82: Code Review Report

**Reviewed:** 2026-07-10
**Depth:** standard
**Files Reviewed:** 4 (cross-repo: kais-hermes-skills + hermes-agent)
**Status:** issues_found

## Summary

Phase 82 delivers two tracks: (1) XCUT-04c GLM-4.6V cost tracking via `dreamina_stats.py` + `vision_verify.py` + `dreamina_manager.py`, and (2) XCUT-05-AUTO agent lineage automation via `bump_all_agent_lineage.py`. The implementation is mostly solid — backward compatibility for legacy entries is handled, the CLI mirrors the existing `dreamina stats` pattern, the bump script correctly splits Track A (9 experts via `transform_one`) and Track B (6 experts via `transform_track_b_one`), and Phase 79 changes (per-stratum threshold + asyncio.gather + tenacity) are preserved.

However, one BLOCKER was found: the cost tracking pipeline **undercounts GLM-4.6V token usage by ~67% for 3-attempt items** because only the last vision-verify attempt's usage is captured. Several Warnings include TypedDict schema drift, batched-verify usage inflation for future callers, and an exception-path `vr` dict missing the `usage` key. Info-level items cover dead complexity, missing `--month` validation, and a pre-existing `Path.home()` anti-pattern.

## Structural Findings (fallow)

No structural findings block was provided for this review.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Cost tracking undercounts tokens for multi-attempt vision-verify (only last attempt's usage captured)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py:397-460`
**Issue:**

The `_generate_one_with_verify` function runs a 3-attempt loop (IMG-04). On each attempt where vision-verify runs and returns low-confidence, the code does `continue` (line 424) to retry with an escalated prompt. Each attempt consumes GLM-4.6V tokens, but only the LAST attempt's `usage` is captured:

```python
# Attempt 0: vr = await verify_image_content(...)  → vr["usage"] = {input: 200, output: 80}
# vr.get("pass") is False, attempt < 2 → continue (usage from attempt 0 LOST)

# Attempt 1: vr = await verify_image_content(...)  → vr["usage"] = {input: 180, output: 75}
# vr.get("pass") is False, attempt < 2 → continue (usage from attempt 1 LOST)

# Attempt 2: vr = await verify_image_content(...)  → vr["usage"] = {input: 190, output: 70}
# Falls through to degraded path:
final_usage = (vr or {}).get("usage", ...)  # only attempt 2's {190, 70}
final_cost = _compute_cost_usd(190, 70)     # cost for 1 call, not 3
```

For a 3-attempt item, the reported cost is approximately **1/3 of the actual cost**. This defeats the entire purpose of the XCUT-04c cost tracking dashboard — operators looking at `hermes glm stats` would see systematically understated spend, making budget decisions on bad data. The bug is silent (no crash, no warning) and proportional to the retry rate.

**Fix:**

Accumulate usage across all attempts. Add a running total before the retry `continue`:

```python
# Before the for loop (line 325):
total_input_tokens = 0
total_output_tokens = 0

# After each vision-verify call (after line 394, inside the `if expected:` block):
attempt_usage = (vr or {}).get("usage", {"input_tokens": 0, "output_tokens": 0})
total_input_tokens += attempt_usage.get("input_tokens", 0)
total_output_tokens += attempt_usage.get("output_tokens", 0)

# Then on ALL return paths (ok at line 405, degraded at line 449, no-expected at line 427):
cumulative_usage = {"input_tokens": total_input_tokens, "output_tokens": total_output_tokens}
cumulative_cost = _compute_cost_usd(total_input_tokens, total_output_tokens)
# Use cumulative_usage + cumulative_cost instead of single-attempt values.
```

This ensures every GLM-4.6V token consumed by the task is accounted for, regardless of how many attempts it took.

## Warnings

### WR-01: DreaminaTaskResult TypedDict missing `usage` + `estimated_cost_usd` fields (schema drift)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py:163-180`
**Issue:**

The `DreaminaTaskResult` TypedDict declares 9 fields (`submit_id`, `status`, `image_path`, `latency_ms`, `retries`, `vision_verified`, `vision_confidence`, `error`). But every return dict from `_generate_one_with_verify` now also includes `"usage"` (dict) and `"estimated_cost_usd"` (float) — 11 fields total. The TypedDict type annotation is stale and doesn't document the Phase 82 additions.

This is a maintenance hazard: a future developer reading the TypedDict would not know these fields exist, and type checkers (ty/mypy) cannot catch missing keys in consumers like `batch_submit` line 246-248 (`result.get("usage", {})`).

**Fix:**

Add the two fields to the TypedDict:

```python
class DreaminaTaskResult(TypedDict):
    submit_id: str
    status: str
    image_path: str | None
    latency_ms: int
    retries: int
    vision_verified: bool
    vision_confidence: float | None
    error: str | None
    # Phase 82 XCUT-04c-INSTRUMENT
    usage: dict[str, int]
    estimated_cost_usd: float
```

### WR-02: Exception-path `vr` fallback dict missing `usage` key (inconsistent shape)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py:389-394`
**Issue:**

When `verify_image_content` raises an exception, the except block sets:
```python
vr = {"pass": False, "confidence": 0.0}
```

This dict has no `"usage"` key. Downstream at line 397-399:
```python
usage = (vr or {}).get("usage", {"input_tokens": 0, "output_tokens": 0})
```
The `.get()` default handles this gracefully (returns zeros), so it doesn't crash. But the shape is inconsistent — successful vision-verify returns `vr` with 5 keys including `"usage"`, while the exception fallback has only 2 keys. This makes defensive `.get()` calls mandatory everywhere `vr` is consumed, and a future code change that drops the `.get()` default would crash on the exception path.

**Fix:**

Include `"usage"` in the exception fallback:
```python
except Exception as exc:
    logger.warning(
        "vision-verify %s failed: %s — treating as not-verified",
        item_id, exc,
    )
    vr = {
        "pass": False,
        "confidence": 0.0,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }
```

### WR-03: verify_batch attributes full batch-level usage to each image (cost inflation for future callers)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py:357-371`
**Issue:**

In `verify_batch`, line 357 extracts the batch-level usage from the response, then line 371 assigns the SAME `batch_usage` to each image's result dict:
```python
batch_usage = _extract_usage(response)  # e.g. {input: 600, output: 200}
for j, i in enumerate(batch_idx):
    ...
    r["usage"] = batch_usage  # each of 6 images gets {input: 600, output: 200}
```

If a future caller aggregates usage from `verify_batch` results (e.g. summing `input_tokens` across images), it would count 600×6 = 3600 instead of the actual 600 — a 6x inflation.

`dreamina_manager.py` currently only calls `verify_image_content` (not `verify_batch`), so the cost dashboard is NOT affected today. But the `usage` field on `verify_batch` results is misleading as-is — the docstring says "attributed to each image in the batch (approximate)" but doesn't warn that downstream summation would double-count.

**Fix:**

Either (a) divide the batch usage by the number of images in the batch and assign per-image shares:
```python
per_image_input = batch_usage["input_tokens"] // len(batch_idx)
per_image_output = batch_usage["output_tokens"] // len(batch_idx)
r["usage"] = {"input_tokens": per_image_input, "output_tokens": per_image_output}
```
Or (b) document that `usage` on batch results represents the batch total (not per-image) and callers must NOT sum across images:
```python
# Add to r a flag: r["usage_is_batch_total"] = True
```
Option (a) is safer for aggregation.

### WR-04: `_extract_usage` uses `or` fallback which treats legitimate `0` as falsy

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py:186-191`
**Issue:**

```python
input_tokens = _get(usage, "prompt_tokens", "prompt_tokens") or _get(
    usage, "input_tokens", "input_tokens"
)
```

If `prompt_tokens` is `0` (a valid value — e.g. an empty prompt), the `or` evaluates `0 or _get(...)` and skips to the fallback `_get(usage, "input_tokens", ...)`. If the usage object has both `prompt_tokens=0` AND `input_tokens=50` (unlikely but possible with some provider response shapes), the result would be `50` instead of `0`. More concerningly, if `prompt_tokens=0` and there's no `input_tokens` attribute, the result is `0` (correct by accident).

This is a minor correctness risk for edge cases with zero-token responses. The `output_tokens` line (189-190) has the same pattern.

**Fix:**

Use explicit `None` checks instead of truthiness:
```python
input_val = _get(usage, "prompt_tokens", "prompt_tokens")
if input_val == 0:
    input_tokens = 0
elif input_val > 0:
    input_tokens = input_val
else:
    input_tokens = _get(usage, "input_tokens", "input_tokens")
```
Or more concisely, check `is not None and > 0`:
```python
input_tokens = _get(usage, "prompt_tokens", "prompt_tokens")
if input_tokens <= 0:
    input_tokens = _get(usage, "input_tokens", "input_tokens")
```

## Info

### IN-01: `_get` helper in `_extract_usage` has dead complexity (obj_key and dict_key are always identical)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py:177-184`
**Issue:**

The inner `_get` function takes `obj_key` and `dict_key` as separate parameters, but at all 4 call sites (lines 186-191) they are passed the same string (e.g. `_get(usage, "prompt_tokens", "prompt_tokens")`). The two-parameter design suggests they were meant to differ (e.g. object attribute name vs dict key name), but in practice they never do. This is dead complexity — the function could take a single `key` parameter.

**Fix:**

Simplify to a single key parameter, or document why the split exists (if there's a future plan for attribute/dict name divergence).

### IN-02: `--month` flag accepts any string without validation (no format check)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py:315-320`
**Issue:**

The `--month` argument has `type=str` with no validation. Passing `--month foo` or `--month 2026-7` (missing zero-pad) silently produces empty results (no match against ISO timestamps like `2026-07-10T...`). The user gets no feedback that their input was malformed.

**Fix:**

Add a simple format check or use a custom type function:
```python
def _validate_month(val: str) -> str:
    import re
    if not re.match(r"^\d{4}-\d{2}$", val):
        raise argparse.ArgumentTypeError(
            f"--month must be YYYY-MM format (e.g. 2026-07), got: {val!r}"
        )
    return val

stats_p.add_argument("--month", type=_validate_month, ...)
```

### IN-03: DREAMINA_CLI uses `Path.home()` (pre-existing, not Phase 82 introduced)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py:67`
**Issue:**

```python
DREAMINA_CLI = Path.home() / ".local" / "bin" / "dreamina"
```

CLAUDE.md flags `Path.home()` as an anti-pattern (breaks test hermetic isolation via HERMES_HOME redirect). This is a pre-existing line (not introduced by Phase 82 — it was there in P73), and the dreamina binary path is NOT a HERMES_HOME-managed path (it's a system-level CLI install location). Still, for environments where `HOME` differs from the operator's expected path (e.g. Docker with a different user), this could fail silently. Worth making configurable via `config.yaml` or an env var in a future phase.

### IN-04: `_pricing_cache` typed as `dict[str, float] | None` but becomes `dict[str, float]` after first call (never re-None'd)

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py:75`
**Issue:**

The module-level `_pricing_cache: dict[str, float] | None = None` is set to `{}` on first call (line 112) and never reset to `None`. The `| None` in the type annotation only applies to the initial state. After the first `_compute_cost_usd` call, the type is effectively `dict[str, float]`. This is not a bug, but the type annotation is slightly misleading — a reader might think the cache can become `None` again (it can't). Minor.

### IN-05: TRACK_B_PANEL comment says "3 non-expert agent peers" but includes 4 entries

**File:** `/data/workspace/hermes-agent/scripts/bump_all_agent_lineage.py:146-153`
**Issue:**

The docstring/comment says:
> "the existing v13.0 P62 Track B YAMLs reference 3 non-expert agent peers (compliance_gate, production, prompt_injector)"

But `TRACK_B_PANEL` at line 150-153 adds 4 entries:
```python
TRACK_B_PANEL: frozenset[str] = frozenset(
    ACTIVE_EXPERTS_15
    + ["compliance_gate", "production", "prompt_injector", "scene_builder"]
)
```

`scene_builder` is the 4th. The comment at line 149 does mention "legacy ``scene_builder`` name" separately, but the "3 non-expert agent peers" count in the preceding comment block (line 146) is off by one. The test at `test_bump_all_agent_lineage.py:256` correctly checks for all 4 (`compliance_gate`, `production`, `prompt_injector`, `scene_builder`). This is a documentation inconsistency, not a code bug — the set itself is correct (verified: `performer` and `storyboard_designer` SKILL.md files both reference `scene_builder` in their `related_skills`).

**Fix:**

Update the comment from "3 non-expert agent peers" to "3 non-expert agent peers + the legacy scene_builder name" or "4 entries (3 non-expert agent peers + 1 legacy name)".

---

_Reviewed: 2026-07-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
