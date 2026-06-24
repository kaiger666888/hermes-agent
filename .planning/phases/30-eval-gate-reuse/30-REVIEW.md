---
phase: 30-eval-gate-reuse
reviewed: 2026-06-24T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - skills/movie-experts/_eval/gate.py
  - skills/movie-experts/_eval/runner.py
  - skills/movie-experts/_eval/gate_config.yaml.example
findings:
  critical: 5
  warning: 8
  info: 4
  total: 17
status: issues_found
---

# Phase 30: Code Review Report

**Reviewed:** 2026-06-24
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the Phase 30 eval-gate reuse implementation: `gate.py` (the gate orchestrator with paired-t statistics, patch mechanics, multi-skill detection, baseline cache), `runner.py` (the MT-Bench position-swap harness extended with numeric scoring), and `gate_config.yaml.example`. The implementation is generally well-structured with strong documentation of threat-model mitigations (T-30-01 through T-30-11) and good adherence to CLAUDE.md conventions (encoding="utf-8" everywhere, lazy %s logging, `from __future__ import annotations`, stdlib-only numerics).

However, the adversarial review surfaced **5 critical defects** that break documented invariants or produce incorrect verdicts, plus 8 quality/warning issues. The most severe: (1) the baseline cache is never wired into the CLI path, making the entire cache infrastructure dead code; (2) the `is_significant` fallback for unknown df values produces *more permissive* results, contradicting the docstring's "conservative round-down" claim; (3) the "first run populates baseline from candidate" path is dead code because `candidate_composites` is empty at the assignment site; (4) `--dry-run` produces uniformly `None` composites because `_StubJudgeClient` emits no dimension scores; (5) `decide_verdict` and `paired_t_stats` silently disagree on `min` alignment when baseline and candidate lists differ in length, producing misleading per-prompt reports.

Security posture is strong: subprocess calls use argv lists (no shell=True), path traversal is rejected at the `..` segment level, and the API key is never logged. The numerics edge cases are the main defect surface.

## Critical Issues

### CR-01: Baseline cache is never loaded in CLI runs (dead cache infrastructure)

**File:** `skills/movie-experts/_eval/gate.py:1318-1328`
**Issue:** The CLI `main()` calls `run_gate(...)` but does NOT pass the `baseline_scores_cache` parameter. It is not a CLI flag either. As a result, in every CLI invocation, `run_gate` runs with `baseline_scores_cache=None`, so the entire block at lines 887-914 (legacy list + Plan-02 scores.json + `load_cached_baseline` with staleness check) is skipped, and the gate always falls through to the line 930-931 path that treats the candidate as its own baseline (see CR-03). The whole `rebuild_baseline` / `load_cached_baseline` / `--rebuild-baseline` infrastructure produces files that the gate then never reads. The operator's `--rebuild-baseline` workflow is broken: they rebuild a baseline, then run the gate, and the gate ignores the rebuilt cache and passes every patch (mean_delta=0 vs self).

**Fix:** Add a `--baseline-cache` CLI flag (defaulting to `_eval/baseline/<skill>/scores.json`) and pass it through:

```python
parser.add_argument(
    "--baseline-cache",
    type=Path,
    default=None,
    help="Path to baseline scores.json cache (default: _eval/baseline/<skill>/scores.json).",
)
# ... after resolving skill:
baseline_cache = args.baseline_cache or (
    Path(__file__).resolve().parent / "baseline" / args.skill / "scores.json"
)
result = run_gate(
    ...
    baseline_scores_cache=baseline_cache,
)
```

### CR-02: `is_significant` fallback for unknown df is ANTI-conservative (contradicts docstring)

**File:** `skills/movie-experts/_eval/gate.py:337-377`
**Issue:** The docstring at line 350-352 claims: *"df < 30 not listed -> conservative round-down to the nearest listed df below (e.g. df=12 uses df=10's critical value 2.228)."* This is wrong in direction. Critical-t is a DECREASING function of df. Rounding df DOWN (e.g. df=12 -> df=10) picks a LARGER critical value (2.228 > the true ~2.201 for df=12), which is correctly conservative for that case. **But the asymptotic branch at line 369-370 has the opposite problem**: for any `df > 30`, it uses `1.960`, but the actual critical-t at df=31 is ~2.040, at df=40 is ~2.021, at df=60 is ~2.000. Using 1.960 makes the test systematically MORE permissive (more likely to declare significance) than the true value for every df in [31, ∞). The same anti-conservative direction occurs for the round-DOWN branch too, contradicting the docstring: smaller df -> larger crit-t -> HARDER to be significant, so "round-down df" is actually MORE conservative, not less — but the docstring says "conservative round-down" as if naming the rounding direction, not the effect, and the asymptotic branch is unambiguously permissive. Net effect: `significant_at_0.05` in the report can be `true` when the true paired-t would not reject H0, misleading operators into shipping patches that are not actually significant improvements (or, symmetrically, into trusting that a non-rejection was meaningful).

Also: line 367-376 `_CRITICAL_T_05_TWO_TAILED.get(df)` returns None for df=31..∞, then `crit = 1.960` unconditionally — even though a more accurate piecewise table (df=40, 60, 120) would be trivial to add and is the standard practice.

**Fix:** Either (a) fix the docstring to accurately describe the permissiveness direction and add operator-facing note in the report `paired_t.note`, OR (b) better, extend the table to cover df=40, 60, 120, and interpolate:

```python
_CRITICAL_T_05_TWO_TAILED: dict[int, float] = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042,
    40: 2.021, 60: 2.000, 120: 1.980,
}
# Fallback for >120 only:
crit = _CRITICAL_T_ASYMPTOTIC_05 if df > 120 else <interpolated value>
```
And make the rounding direction in the docstring unambiguous: "rounds df DOWN to the nearest listed df, which increases the critical value, making the test MORE conservative (harder to declare significance)."

### CR-03: "First-run populates baseline from candidate" path is dead code (always-empty candidate_composites)

**File:** `skills/movie-experts/_eval/gate.py:915-937`
**Issue:** The fallback at lines 930-931 reads:
```python
if not baseline_composites:
    baseline_composites = list(candidate_composites)
```
But `candidate_composites` is built INSIDE the loop at lines 916-919, which executes AFTER the `if baseline_scores_cache is not None and ...is_file()` block (lines 887-914) and BEFORE line 930. The loop populates `candidate_composites` correctly. **However**, the assignment `baseline_composites = list(candidate_composites)` at line 931 runs AFTER the loop, so `candidate_composites` IS populated at that point. Re-tracing: lines 915-927 build `candidate_composites` and fill `rec["baseline_composite"]`. Line 930 checks `if not baseline_composites`. So `baseline_composites` (still `[]`) is replaced with `candidate_composites`. So `decide_verdict(candidate_composites, candidate_composites, ...)` returns `pass` (mean_delta=0). This means: **the first run with no baseline cache ALWAYS passes every patch**, regardless of actual quality, because candidate is compared to itself. The docstring at line 929 ("If no baseline cache, treat candidate as its own baseline (first run) — mean_delta=0 -> pass. Cache for next time.") documents this as intentional, but it is a dangerous default: an operator running the gate for the first time on a regression-introducing patch will get a `pass` verdict and a false sense of safety, and the polluted cache then masks future regressions. Combined with CR-01 (cache never read by CLI), this is the actual runtime path for every CLI invocation.

**Fix:** Refuse to run without a baseline rather than silently passing:

```python
if not baseline_composites:
    logger.error(
        "no baseline cache found for skill %s; run --rebuild-baseline first. "
        "Refusing to score against self (would always pass).",
        skill_id,
    )
    return GateResult(
        verdict="inconclusive",
        exit_code=VERDICT_TO_EXIT["inconclusive"],
        evidence={"reason": "missing_baseline_cache", "skill_id": skill_id},
        patch_id=patch_id,
    )
```

### CR-04: `--dry-run` produces uniformly None composites (gate always returns inconclusive)

**File:** `skills/movie-experts/_eval/runner.py:543-588` interacting with `skills/movie-experts/_eval/gate.py:872-878`
**Issue:** `_StubJudgeClient._Completions.create` returns a response containing only `<reasoning>` and `<decision>` tags — NO `<dimension>: <score>` lines. So `parse_judge_scores` returns `{}` for every comparison, `composite_score({})` returns `None` per `runner.composite_score` (line 185-186), and `evaluate_candidate` produces records where `candidate_composite=None` for every prompt. Then in `run_gate` line 918 `if c is not None` filters them all out, so `candidate_composites=[]`. Then `decide_verdict([], [], min_prompts=5)` returns `inconclusive` (n=0 < 5). The gate's `--dry-run` flag is therefore non-functional for verifying the verdict logic — it always returns exit code 3. This defeats the documented purpose of `--dry-run` ("SC #3 fallback — no API key required"): operators cannot smoke-test the gate end-to-end without burning API quota.

**Fix:** Extend the stub to emit valid dimension scores so dry-run exercises the full pipeline:

```python
@staticmethod
def create(**kwargs: Any) -> dict:
    swap = bool(kwargs.get("extra_body", {}).get("swap", False))
    decision = "B" if swap else "A"
    # Emit deterministic scores so the gate's composite logic is exercised.
    scores_block = (
        "industry_accuracy: 4.0 — stub\n"
        "professional_depth: 4.0 — stub\n"
        "actionability: 4.0 — stub\n"
        "language_quality: 4.0 — stub\n"
    )
    return {
        "choices": [{
            "message": {
                "content": (
                    f"<reasoning>stub decision for swap={swap}</reasoning>\n"
                    f"{scores_block}"
                    f"<decision>{decision}</decision>"
                )
            }
        }]
    }
```

### CR-05: `decide_verdict` and `paired_t_stats` silently disagree with per_prompt report when list lengths differ

**File:** `skills/movie-experts/_eval/gate.py:407-413, 425-433, 993-1035`
**Issue:** `decide_verdict` uses `n = min(len(baseline_scores), len(candidate_scores))` and only inspects the first `n` deltas. So if `baseline_scores` has 5 entries and `candidate_scores` has 10, the verdict is decided on the first 5 prompts only. But `per_prompt` (the list returned by `evaluate_candidate`) has all 10 records, and these are written verbatim into the report at line 1052-1064. So the operator sees a report with 10 per-prompt rows, of which 5 have `baseline_composite` and 5 have `baseline_composite: null`, while the verdict was computed from only the first 5. The same `min`-truncation happens silently in `paired_t_stats` (line 305). There is no warning logged that lists were misaligned. This is a correctness defect: an operator reading the report cannot tell which rows were actually used in the verdict, and a regressing prompt at index 6 (with `baseline_composite=null`) is silently excluded from the per-prompt regression check.

Additionally, `run_gate` builds `candidate_composites` by filtering `if c is not None` (line 918) — so if some candidate records have None composite (e.g. judge returned no scores for one prompt), the candidate list SHRINKS below `len(per_prompt)`, further misaligning it from the baseline list (which has one entry per prompt at indices < len(baseline)). The `zip(..., strict=False)` then pairs baseline[0] with the first NON-None candidate, which may be a different prompt.

**Fix:** Validate alignment at the top of `decide_verdict` and log a warning:

```python
def decide_verdict(baseline_scores, candidate_scores, *, ...):
    if len(baseline_scores) != len(candidate_scores):
        logger.warning(
            "decide_verdict: baseline (%d) and candidate (%d) lengths differ; "
            "verdict computed on first %d only; per_prompt report may be misleading",
            len(baseline_scores), len(candidate_scores),
            min(len(baseline_scores), len(candidate_scores)),
        )
    ...
```
And in `run_gate`, build `candidate_composites` with explicit None placeholders so alignment is preserved:
```python
candidate_composites: list[float] = []
for rec in per_prompt:
    c = rec.get("candidate_composite")
    candidate_composites.append(float(c) if c is not None else float("nan"))
```
Then have `decide_verdict` skip NaN-aligned pairs explicitly rather than silently truncating.

## Warnings

### WR-01: Baseline cache write is not concurrency-safe (tmp file collision)

**File:** `skills/movie-experts/_eval/gate.py:631-637`
**Issue:** `rebuild_baseline` writes to a fixed path `<out_dir>/scores.json.tmp` then `os.replace`. If two `--rebuild-baseline` runs for the same skill execute concurrently (e.g. in CI matrix), they share the same `.tmp` path, causing one run's bytes to be partially overwritten by the other before `replace` is called. The atomic-rename guarantee only holds for a single writer.

**Fix:** Use `tempfile.NamedTemporaryFile(dir=out_dir, delete=False, suffix=".tmp")` to get a unique tmp name per run, then `os.replace(tmp_path, out_path)`.

### WR-02: First-run baseline cache write happens BEFORE verdict (mutates state on failed runs)

**File:** `skills/movie-experts/_eval/gate.py:930-937`
**Issue:** When no baseline cache exists, lines 932-937 write `baseline_composites` (which equals `candidate_composites` per CR-03) to `baseline_scores_cache` immediately, BEFORE `decide_verdict` runs. If the verdict is `fail_mean` or `fail_regression`, the cache is already polluted with the failing candidate's scores, and the next run will compare a new candidate against THIS failed candidate, masking the regression permanently. State mutation should not precede the decision.

**Fix:** Move the cache-write to AFTER `decide_verdict` and only on `verdict == "pass"` — OR, per CR-03, refuse to run without a baseline cache entirely.

### WR-03: `revert_patch` swallows errors silently in the `finally` block (only logs warning)

**File:** `skills/movie-experts/_eval/gate.py:947-953`
**Issue:** If `revert_patch` fails (e.g. `git checkout --` fails because of an untracked change conflict, or `git clean -f` refuses due to gitignored file), the failure is logged as a warning and execution continues to write a report claiming `verdict=pass/fail`. But the working tree is now in a CORRUPT state — the patch is still applied. Subsequent gate runs on the same repo will operate on patched files, producing wrong baselines. The T-30-04 mitigation docstring says "revert ALWAYS runs" — but a revert that silently fails is not a revert. The exit code returned to the operator does not reflect that the working tree was left dirty.

**Fix:** On revert failure, escalate the exit code to a distinct "internal_error" code (e.g. 4) and surface the corruption in the report:

```python
finally:
    if applied:
        try:
            revert_patch(files, repo_root)
        except Exception as exc:
            logger.error("revert_patch FAILED: %s — WORKING TREE LEFT DIRTY", exc)
            return GateResult(
                verdict="internal_error",
                exit_code=4,
                evidence={"reason": "revert_failed", "error": str(exc), **evidence},
                patch_id=patch_id,
            )
```

### WR-04: `generate_patch_id` is not collision-resistant for rapid re-runs

**File:** `skills/movie-experts/_eval/gate.py:448-457`
**Issue:** `patch_id = f"{skill_id}_{ts_unix}_{sha[:8]}"` uses Unix-second resolution. Two runs of the same patch within the same second produce the same id and overwrite the same report file at `reports_dir / f"{patch_id}.json"`. In CI or batch operator loops, sub-second re-runs are plausible.

**Fix:** Use `time.time_ns()` or append a short random suffix:
```python
import secrets
return f"{skill_id}_{ts_unix}_{sha[:8]}_{secrets.token_hex(2)}"
```

### WR-05: `parse_judge_scores` regex is fragile against markdown emphasis (silently drops scores)

**File:** `skills/movie-experts/_eval/runner.py:71-77, 163-175`
**Issue:** The regex `rf"{re.escape(dim)}:\s*([1-5](?:\.\d+)?)"` requires the literal `dimension:` immediately before the score. LLM judges commonly emit `**industry_accuracy:** 4.0` or `- **industry_accuracy:** 4.0` (markdown bold/italic + list markers). These would silently fail to match, producing an empty scores dict, which propagates to `composite_score=None` and ultimately an inconclusive verdict. The fail-safe is correct (don't crash), but the silent-drop leaves no audit trail for "the judge emitted scores in a slightly different format."

**Fix:** Strip markdown emphasis before matching, and log when a dimension is expected but not found:
```python
# Strip markdown bold/italic markers before matching.
stripped = re.sub(r"\*+", "", raw_text)
...
if m is None:
    logger.debug("dimension %s not found in judge response", dim)
    continue
```

### WR-06: `_load_answers_json` coerces non-string elements to "None"/"True" silently

**File:** `skills/movie-experts/_eval/gate.py:732-740`
**Issue:** `[str(x) for x in data]` converts `None` -> `"None"`, `True` -> `"True"`, `42` -> `"42"`. A malformed JSON file `[null, null, null]` becomes `["None", "None", "None"]` and is passed to the judge as if it were real answer text, producing meaningless verdicts with no error surfaced.

**Fix:** Validate element types and fail fast:
```python
for i, x in enumerate(data):
    if not isinstance(x, str):
        raise ValueError(
            f"answers file {path}[{i}] must be a string, got {type(x).__name__}"
        )
return data
```

### WR-07: `extract_patched_files` only inspects `+++ b/` headers, ignoring `/dev/null` deletions

**File:** `skills/movie-experts/_eval/gate.py:95, 103-136`
**Issue:** A unified diff for a file DELETION uses `+++ /dev/null`. The regex `^\+\+\+ b/(.+?)\s*$` won't match `/dev/null`, so deletion patches silently produce an empty `files` list. Then `run_gate` line 830-831 raises `ValueError("patch touches no files")` — confusing because the patch DOES touch a file (it deletes one). Worse, if a patch both modifies and deletes files, the deletion is silently ignored, the modified file is reverted by `revert_patch`, but the deleted file stays deleted in the working tree post-revert (because `revert_patch` only `checkout`s files in its list).

**Fix:** Also parse `--- a/<path>` headers for deletions, or document that deletion patches are out of scope and reject them explicitly at the top of `extract_patched_files`.

### WR-08: `paired_t_stats` n=2 case is silently allowed but statistically meaningless

**File:** `skills/movie-experts/_eval/gate.py:305-334`
**Issue:** With `n=2`, `df=1`, the critical-t is 12.706 — essentially unattainable in practice. So `is_significant` will always return False for n=2, but the report's `paired_t.note` will still emit a `|t_stat|` value that looks interpretable. An operator may read `significant_at_0.05: false` at face value without realizing the test had no statistical power. The `min_prompts` default is 5, so this only bites when operators lower `--min-prompts` to 2.

**Fix:** Log a warning when `n < 5` in `paired_t_stats` or in the report-generation block:
```python
if stats["n"] < 5:
    note += " (WARNING: n<5 — paired-t has low power; treat significant_at_0.05 with caution.)"
```

## Info

### IN-01: `_CRITICAL_T_05_TWO_TAILED` has non-uniform df spacing (10 -> 15 -> 20 -> 25 -> 30)

**File:** `skills/movie-experts/_eval/gate.py:82-86`
**Issue:** The table jumps 10, 15, 20, 25, 30. The standard statistical convention includes df=11, 12, 13, 14 (each distinct crit-t). The fallback interpolation (rounding down) loses precision in this range.

**Fix:** Fill in the missing df values, or accept the precision loss and update the docstring to note the table granularity.

### IN-02: `runner.py` live mode returns exit code 2 unconditionally (Phase 0 scope fence)

**File:** `skills/movie-experts/_eval/runner.py:690-696`
**Issue:** `runner.main` exits 2 with "Live answer generation is not implemented in Phase 0" for any non-dry-run invocation. This is a documented scope fence (Phase 31 work), but the message could mention the workaround (pre-generate answers and feed via gate.py's `--baseline-answers` / `--candidate-answers`).

**Fix:** Add the workaround hint to the error message.

### IN-03: `gate_config.yaml.example` does not document the `multi_skill` config key

**File:** `skills/movie-experts/_eval/gate_config.yaml.example`
**Issue:** The example documents `delta_threshold`, `per_prompt_threshold`, `min_prompts`, `ab_positions`, `judge_model` but omits `multi_skill` (which `gate.py:836` reads via `config.get("multi_skill", False)`). Operators wanting to bypass the multi-skill guard via config (not CLI) have no example.

**Fix:** Add a commented-out example line:
```yaml
# multi_skill: false  # Set true to allow patches touching multiple skills.
```

### IN-04: `is_significant` alpha != 0.05 silently returns False (no exception, just warning)

**File:** `skills/movie-experts/_eval/gate.py:357-363`
**Issue:** Only `alpha=0.05` is supported. Any other alpha logs a warning and returns False, which an operator may mistake for "not significant at the requested alpha" rather than "alpha unsupported, result is meaningless." Consider raising `ValueError` for unsupported alphas to fail-fast.

**Fix:** Either raise `ValueError(f"alpha={alpha} unsupported; only 0.05 is implemented")`, or document explicitly in the return-value contract that False means "indeterminate" not "not significant."

---

_Reviewed: 2026-06-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
