---
phase: 78-trans-07-ltx-flf-validation-runner
reviewed: 2026-07-10T12:30:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_update_ltx_flf_verdict.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/workflows/ltx-flf-iclora-validation.json
findings:
  critical: 2
  warning: 8
  info: 5
  total: 15
status: issues_found
---

# Phase 78: Code Review Report

**Reviewed:** 2026-07-10T12:30:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Phase 78 (TRANS-07 LTX-FLF Validation Runner) implements an async validation runner, a verdict update script, a ComfyUI workflow JSON template, and associated tests. The overall architecture is sound: serial awaits for GLM-coupled calls (INFRA-04 compliant), Pydantic v2 schema with `extra="forbid"`, atomic writes for the verdict markdown, and a 4-check validation gate that refuses to proceed without operator sign-off.

Two critical issues were found:

1. **`ref_image_path` is dead code** — the `verify_identity_continuity` function accepts a `ref_image_path` parameter but never passes it to `vision_verify_fn`. The "identity continuity" check is actually a text-prompt-based content verification, not an image-to-image identity comparison. This means the validation runner cannot actually detect identity drift against the reference images, which is the entire purpose of TRANS-07.

2. **`poll_comfyui` ignores ComfyUI execution errors** — the poll loop only checks for non-empty `outputs` but never inspects `status.status_str` or `status.completed`. If ComfyUI fails mid-generation (e.g., OOM, node error), the poll keeps retrying for the full 600s `max_wait` instead of failing fast. This wastes 10 minutes on a doomed generation.

Additional findings include URL-encoding gaps in the download endpoint, type validation gaps in the verdict script, test coverage holes for timeout/error paths, and minor docstring/log issues.

## Critical Issues

### CR-01: `ref_image_path` parameter is dead code — identity continuity check does not use the reference image

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:565-599`

**Issue:** The `verify_identity_continuity` function accepts `ref_image_path: Path` as a parameter (line 567) and its docstring describes it as "Path to the reference identity image (ref1.png)" (line 574). However, the parameter is **never used** in the function body. The `vision_verify_fn` is called with only `image_path` (the generated frame) and `expected_content` (a generic text prompt: "character matching the reference image identity (face, clothing, appearance)").

The `verify_image_content` function from `plugins.kais_aigc.vision_verify` (line 73-77) only accepts `image_path: str`, `expected_content: str`, and `directional_check: str | None`. It does not accept a reference image — it verifies that a single image contains expected content via a text description, not via image-to-image comparison.

This means the entire "identity continuity" check is a text-prompt-based content verification. The validation runner cannot actually compare a generated frame against `ref1.png` to detect identity drift. The `ref_image_path` parameter gives a false impression that reference-image-based identity comparison is happening.

This is the core purpose of TRANS-07 — testing whether identity continuity holds across FLF-conditioned transition generation. If the check doesn't actually compare against reference images, the validation results are misleading.

**Fix:** This requires a design decision. Two options:

Option A — If `verify_image_content` is the only available API, update the docstring and parameter name to reflect that it's a text-prompt-based check, not a reference-image comparison. Remove `ref_image_path` from the signature or mark it as unused:

```python
async def verify_identity_continuity(
    frame_path: Path,
    vision_verify_fn: Any,
) -> dict:
    """Call vision_verify to check identity continuity on a generated frame.

    NOTE: This is a TEXT-PROMPT-based check, NOT a reference-image comparison.
    verify_image_content only accepts a text description of expected content.
    True image-to-image identity comparison would require a different API
    (e.g., face embedding cosine similarity).

    Args:
        frame_path: Path to the extracted video frame.
        vision_verify_fn: The verify_image_content function.

    Returns:
        Result dict with keys: pass, confidence, description, cached.
    """
    try:
        result = await vision_verify_fn(
            image_path=str(frame_path),
            expected_content=(
                "character matching the reference image identity "
                "(face, clothing, appearance)"
            ),
        )
        return result
    except Exception as exc:
        logger.warning("vision_verify failed for %s: %s", frame_path, exc)
        return {
            "pass": None,
            "confidence": None,
            "description": None,
            "error": str(exc),
        }
```

Option B — If true reference-image comparison is needed (which TRANS-07's purpose suggests), implement a separate function that compares the frame against `ref1.png` using face embeddings or a vision model that accepts two images. This may be out of scope for v1 but should be documented as a known limitation.

### CR-02: `poll_comfyui` ignores ComfyUI execution errors — 600s wasted on failed generations

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:355-387`

**Issue:** The `poll_comfyui` function polls `/history/{prompt_id}` until `outputs` is non-empty. However, it never checks the `status` field of the ComfyUI history response. ComfyUI's `/history` endpoint returns a structure like:

```json
{
  "prompt_id": {
    "outputs": {...},
    "status": {
      "status_str": "success" | "error",
      "completed": true | false,
      "messages": [...]
    }
  }
}
```

If ComfyUI fails mid-generation (OOM, node execution error, model loading failure), the `status.status_str` would be `"error"` and `outputs` might be empty or partial. The poll loop would keep retrying every 5 seconds for the full 600s `max_wait`, wasting 10 minutes on a generation that already failed.

The current code at line 380-383 only checks `if prompt_id in data` and `if outputs:` — it never inspects whether the generation succeeded or failed. A failed generation with partial outputs might even be treated as success.

**Fix:** Check the `status` field in the history response to detect execution errors and fail fast:

```python
async def poll_comfyui(
    client: httpx.AsyncClient, url: str, prompt_id: str, max_wait: int = 600
) -> dict | None:
    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = await client.get(
                f"{url}/history/{prompt_id}", timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    prompt_data = data[prompt_id]
                    # Check for execution error BEFORE checking outputs.
                    status = prompt_data.get("status", {})
                    status_str = status.get("status_str", "")
                    if status_str == "error":
                        messages = status.get("messages", [])
                        logger.error(
                            "ComfyUI execution failed for prompt_id=%s: %s",
                            prompt_id, messages[:500] if messages else "no details"
                        )
                        # Return a sentinel that signals execution error.
                        # Caller should check for this.
                        return {"_execution_error": True, "messages": messages}
                    outputs = prompt_data.get("outputs", {})
                    if outputs:
                        return outputs
        except httpx.HTTPError as exc:
            logger.debug("poll_comfyui request failed (will retry): %s", exc)
        await asyncio.sleep(5)
    return None
```

Then in `run_validation`, check for the execution error sentinel before proceeding:

```python
outputs = await poll_comfyui(client, comfyui_url, prompt_id)

if outputs is None:
    gen_status = "timeout"
    error_msg = f"ComfyUI poll timed out for prompt_id={prompt_id}"
elif outputs.get("_execution_error"):
    gen_status = "failed"
    error_msg = f"ComfyUI execution error: {outputs.get('messages', [])[:200]}"
else:
    # Proceed with download...
```

## Warnings

### WR-01: `download_video` does not URL-encode filename/subfolder parameters

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:412-415`

**Issue:** The download URL is constructed by string interpolation without URL-encoding the `filename`, `subfolder`, or `file_type` values:

```python
download_url = (
    f"{url}/view?filename={filename}&subfolder={subfolder}&type={file_type}"
)
```

If `filename` contains spaces or special characters (e.g., a shot subdirectory named `shot 01` produces `shot 01_validation.mp4`), the URL would be malformed. While `httpx` may tolerate some malformed URLs, this is not guaranteed and could cause download failures or security issues (path traversal via `..` in filenames).

**Fix:** Use `urllib.parse.quote` to encode the parameters:

```python
from urllib.parse import quote

download_url = (
    f"{url}/view?filename={quote(filename)}"
    f"&subfolder={quote(subfolder)}"
    f"&type={quote(file_type)}"
)
```

Alternatively, use `httpx.Params`:

```python
params = {"filename": filename, "subfolder": subfolder, "type": file_type}
resp = await client.get(f"{url}/view", params=params, timeout=120)
```

### WR-02: `validate_verdict` does not type-check `rationale` — non-string types pass through

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py:218-224`

**Issue:** The `verdict` field has an explicit type check at line 197 (`isinstance(verdict, (str, type(None)))`), but `rationale` does not. If `rationale` is a JSON array, number, or boolean, the check at line 219 (`rationale is None or (isinstance(rationale, str) and rationale.strip() == "")`) would not catch it — both conditions are `False` for non-string, non-None types. The non-string rationale would pass through to `format_verdict_block`, which would interpolate it into the markdown as `**Rationale:** ['a', 'b']` (Python repr of a list), producing unexpected output.

**Fix:** Add an explicit type check for `rationale`, mirroring the `verdict` pattern:

```python
# Check 3: non-null rationale + type check.
rationale = op_decision.get("rationale")
if not isinstance(rationale, (str, type(None))):
    errors.append(
        f"operator_decision.rationale must be a string or null, "
        f"got {type(rationale).__name__}"
    )
    rationale = ""
elif rationale is None or rationale.strip() == "":
    errors.append(
        "operator_decision.rationale is null — operator must provide a "
        "rationale citing validation results"
    )
    rationale = rationale or ""
```

### WR-03: `build_validation_workflow` produces empty image names when `num_refs < 4`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:266-269`

**Issue:** The replacements map hardcodes `PLACEHOLDER_REF1` through `PLACEHOLDER_REF4`. If `num_refs` is less than 4 (e.g., `num_refs=3`), the guard `if len(ref_filenames) > 3` evaluates to `False`, and `PLACEHOLDER_REF4` is replaced with an empty string `""`. The workflow JSON's node 43 (`LoadImage`) would then have `"image": ""`, which ComfyUI would reject with a confusing error.

The workflow JSON template is also hardcoded for exactly 5 refs (4 REF nodes + 1 BACKGROUND node). If `num_refs` differs from 5, the template doesn't adapt, and no warning is logged.

**Fix:** Add a validation check at the top of `build_validation_workflow` that warns or errors when `num_refs` doesn't match the template's expected ref count:

```python
# The template hardcodes 4 REF nodes + 1 BACKGROUND node (5 total).
# Warn if num_refs doesn't match.
expected_refs = 4  # PLACEHOLDER_REF1 through PLACEHOLDER_REF4
if num_refs != 5:
    logger.warning(
        "Workflow template expects 5 refs (4 REF nodes + 1 BACKGROUND), "
        "but num_refs=%d. Placeholder REF nodes may get empty image names, "
        "which ComfyUI will reject. Use num_refs=5 or edit the template.",
        num_refs
    )
```

### WR-04: `latency_ms` discarded for failed/timeout shots — diagnostic value lost

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:742-748`

**Issue:** The latency is calculated as `int((time.time() - start_time) * 1000)` at line 742, but at line 748, it's set to `None` when `actual_video_path is None`:

```python
latency_ms=latency_ms if actual_video_path is not None else None,
```

For a shot that times out after 600s of polling, the latency (600,000ms) is discarded. This loses valuable diagnostic information — the operator can't see how long the timeout took, which would help distinguish between "ComfyUI was slow" and "ComfyUI hung immediately."

**Fix:** Always record the latency, and use `gen_status` to indicate success/failure:

```python
latency_ms=latency_ms,  # Always record, even for failed/timeout shots
```

The `ShotResult.latency_ms` field is `int | None`, so a non-None value for failed shots is type-safe. The Rich summary table already handles `None` latency with `"-"`, so showing a number for failed shots would be an improvement, not a regression.

### WR-05: `verify_identity_continuity` docstring says `passed` but return dict uses `pass`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:579-581`

**Issue:** The docstring at lines 579-581 states the return dict has keys `passed`, `confidence`, `description`, `cached`. But the actual return values use the key `pass` (not `passed`):

- Success path (line 591): returns `result` from `vision_verify_fn`, which returns `{"pass": bool, ...}` (confirmed at `vision_verify.py:87,269-272`)
- Error path (line 595): returns `{"pass": None, ...}`

The caller at line 731 correctly uses `result.get("pass")`, so this is a docstring-only issue. But it's misleading — a developer reading the docstring would expect `result["passed"]` and get a `KeyError`.

**Fix:** Update the docstring to match the actual return keys:

```python
    Returns:
        Result dict with keys: ``pass``, ``confidence``, ``description``,
        ``cached``. On error, returns ``{pass: None, confidence: None,
        description: None, error: str}``.
```

### WR-06: No test for `poll_comfyui` timeout (returns `None`) or execution error paths

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py`

**Issue:** The test suite has no direct test for `poll_comfyui`. It's only exercised indirectly through `run_validation`, and the mocked tests always return successful outputs. There's no test for:

1. `poll_comfyui` returning `None` (timeout) — the `run_validation` code path at line 674-678 (`gen_status = "timeout"`) is untested.
2. `poll_comfyui` receiving an HTTP error on every poll attempt.
3. ComfyUI returning a 200 with empty outputs repeatedly until timeout.

The partial failure test (line 316) tests a `submit_comfyui` failure (HTTP 500 on `/prompt`), not a `poll_comfyui` timeout.

**Fix:** Add a test that mocks `poll_comfyui` to return `None` (timeout) and verifies `gen_status` is set to `"timeout"`:

```python
@pytest.mark.asyncio
async def test_run_validation_poll_timeout(self, tmp_path):
    """run_validation records gen_status='timeout' when poll_comfyui returns None."""
    # ... setup shots + template ...
    mock_client = AsyncMock()
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {"prompt_id": "test-pid"}
    mock_client.post = AsyncMock(return_value=mock_post_response)
    # poll_comfyui always returns empty history -> timeout
    mock_history_response = MagicMock()
    mock_history_response.status_code = 200
    mock_history_response.json.return_value = {}
    mock_client.get = AsyncMock(return_value=mock_history_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        report = await run_validation(
            shots=shots,
            comfyui_url="http://127.0.0.1:8188",
            workflow_template_path=template_path,
            output_dir=output_dir,
            flf_model="ltx/fflf",
            num_refs=5,
            steps=8,
            vision_verify_fn=AsyncMock(),
        )

    assert report.shots[0].gen_status == "timeout"
    assert "timed out" in report.shots[0].error
```

Note: This test would need to mock `time.time` or use a very short `max_wait` to avoid a 600s test runtime.

### WR-07: No test for `download_video` HTTP error (`raise_for_status` raises)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py`

**Issue:** The tests mock `raise_for_status` as a no-op `MagicMock()`. There's no test for the case where `download_video` receives a non-200 response and `raise_for_status()` raises `httpx.HTTPStatusError`. This code path (line 416: `resp.raise_for_status()`) would propagate to the `except Exception` handler in `run_validation` (line 696-699), setting `gen_status = "failed"`.

**Fix:** Add a test where the video download returns a 404 or 500 and `raise_for_status` raises, verifying the shot is marked as failed.

### WR-08: `emit_rich_summary` shows "0%" for `passed=True, confidence=None` (misleading)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:794-799`

**Issue:** The confidence display logic:

```python
if frame.confidence is not None:
    pct = f"{frame.confidence * 100:.0f}%"
elif frame.passed is None:
    pct = "-"
else:
    pct = "0%"
```

When `confidence is None` and `passed is True`, the code falls through to the `else` branch and shows `"0%"`. This is misleading — a frame that passed (even without a confidence score) should not show "0%". In practice, this case is not reachable through the normal `verify_image_content` path (which always returns a confidence float), but it IS reachable through the error path of `verify_identity_continuity` (which returns `pass=None, confidence=None`). If a future change returns `pass=True` with `confidence=None`, this would display incorrectly.

**Fix:** Handle the `passed=True, confidence=None` case explicitly:

```python
if frame.confidence is not None:
    pct = f"{frame.confidence * 100:.0f}%"
elif frame.passed is None:
    pct = "-"
elif frame.passed:
    pct = "pass"
else:
    pct = "0%"
```

## Info

### IN-01: `metadata.reference_shots_dir` is empty in test — `shots_dir` not injected into shot dicts

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py:289-298`

**Issue:** The `test_run_validation_mocked_comfyui` test calls `run_validation` with shots from `load_reference_shots` but does not inject `shots_dir` into each shot dict (unlike `main_async` which does at line 919). The metadata at line 759 reads `shots[0].get("shots_dir", "")`, which returns `""` in the test. The test doesn't verify metadata fields, so this doesn't cause a test failure, but it means the metadata path is untested.

**Fix:** Either inject `shots_dir` in the test, or add a metadata verification assertion:

```python
for shot in shots:
    shot["shots_dir"] = str(tmp_path / "shots")
```

### IN-02: `_no_vision_verify` stub uses `"pass"` key while `FrameIdentityResult` field is `passed`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:942-949`

**Issue:** The no-op stub returns `{"pass": None, ...}`. The caller at line 731 does `result.get("pass")` which correctly maps to `FrameIdentityResult.passed`. This works but the key naming inconsistency (`pass` in the dict vs `passed` in the model) is a cognitive tax. This is a minor naming inconsistency, not a bug — the code is functionally correct.

**Fix:** No code change needed. Consider adding a comment at the stub noting the `pass` key convention comes from `verify_image_content`.

### IN-03: `poll_comfyui` actual wait can exceed `max_wait` by up to 15 seconds

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py:372-387`

**Issue:** The loop condition checks `time.time() - start < max_wait` at the top of each iteration, but each iteration can take up to 10s (HTTP timeout) + 5s (sleep) = 15s. So the actual wait can be up to `max_wait + 15` seconds. For `max_wait=600`, this is 615s — a minor overshoot that's unlikely to matter in practice but is technically imprecise.

**Fix:** No fix needed for this use case (600s timeout with 15s overshoot is negligible). If precision matters, check the time inside the loop after each HTTP call and break early.

### IN-04: Verdict doc `## Production-Readiness Verdict` section heading has no anchor for programmatic detection

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md:240`

**Issue:** The `write_verdict` function uses a regex to find the `## Production-Readiness Verdict` section heading. If someone renames the heading (e.g., `## Production Readiness Verdict` without the hyphen, or `## Verdict`), the regex would fail to match and `write_verdict` would raise `ValueError`. There's no test for the heading-not-found case.

**Fix:** Consider adding a more resilient section marker (e.g., an HTML comment `<!-- verdict-section-start -->`) or add a test for the heading-not-found error path.

### IN-05: Workflow JSON `_meta.flf_model_default` is not used by `build_validation_workflow`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/workflows/ltx-flf-iclora-validation.json:4`

**Issue:** The workflow JSON has a `_meta.flf_model_default` field set to `"ltx/fflf"`, but `build_validation_workflow` never reads this field. The `flf_model` parameter comes from the CLI argument, not from the template metadata. The `_meta` field is informational only and has no programmatic effect. This is not a bug — the `_meta` field serves as documentation — but it could be confusing if someone expects changing it to affect behavior.

**Fix:** No code change needed. Consider adding a comment in `build_validation_workflow` noting that `_meta` fields are informational only and the `flf_model` parameter comes from the CLI.

---

_Reviewed: 2026-07-10T12:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
