"""test_dreamina_manager.py — unit tests for IMG-01 + IMG-02.

Covers:
  - VALIDATION 73-01-01 (IMG-01): asyncio.Semaphore(10) concurrency cap
  - VALIDATION 73-01-02 (IMG-01): tenacity retry on subprocess.TimeoutExpired
  - VALIDATION 73-01-03 (IMG-02): batch_submit blocks until ALL tasks resolve

All tests mock subprocess.run (no real dreamina CLI) and async_call_llm
(no real vision API). Each test < 1s.
"""

from __future__ import annotations

import asyncio
import json
import subprocess

import pytest

from plugins.kais_aigc.dreamina_manager import (
    DEFAULT_CONCURRENCY,
    batch_submit,
)


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


class _MockResult:
    """Minimal CompletedProcess stand-in for subprocess.run mocks."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _ok_submit_result(submit_id: str = "aaaaaaaa-0000-0000-0000-000000000000") -> str:
    """JSON stdout for a successful dreamina text2image --poll=0 submit."""
    return json.dumps({"submit_id": submit_id, "gen_status": "submitting"})


def _ok_poll_result(image_url: str = "https://byteimg.com/test.png") -> str:
    """JSON stdout for a successful dreamina query_result poll."""
    return json.dumps({
        "gen_status": "success",
        "result_json": {"images": [{"image_url": image_url}]},
    })


async def _fake_verify_pass(image_path, expected_content, directional_check=None, stratum=None):
    """Fake verify_image_content returning a high-confidence pass."""
    return {"pass": True, "confidence": 0.92, "description": "fake", "cached": False}


def _patch_verify(monkeypatch):
    """Patch vision_verify at the dreamina_manager import boundary."""
    # dreamina_manager lazy-imports verify_image_content inside
    # _generate_one_with_verify; patch the module attribute so the
    # lazy import picks up our fake.
    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _fake_verify_pass)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_semaphore_cap_10(monkeypatch, tmp_path):
    """VALIDATION 73-01-01 (IMG-01): batch_submit uses asyncio.Semaphore(10).

    Submit 15 items; track peak concurrency via a counter incremented on
    entry to _dreamina_submit and decremented on exit. Assert peak == 10.
    """
    _patch_verify(monkeypatch)

    peak = {"value": 0}
    current = {"value": 0}

    async def _fake_submit(prompt, ratio, model_version):
        current["value"] += 1
        if current["value"] > peak["value"]:
            peak["value"] = current["value"]
        await asyncio.sleep(0.05)  # let other tasks overlap
        current["value"] -= 1
        return "aaaaaaaa-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._dreamina_submit", _fake_submit
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._dreamina_poll", _fake_poll
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._download", _fake_download
    )

    prompts = [{"id": f"S{i:02d}", "prompt": f"scene {i}"} for i in range(15)]
    results = await batch_submit(prompts, str(tmp_path), deadline_sec=30)

    assert len(results) == 15
    assert peak["value"] <= DEFAULT_CONCURRENCY  # MUST cap at 10
    assert peak["value"] == DEFAULT_CONCURRENCY   # AND should reach 10


@pytest.mark.asyncio
async def test_retry_strategy(monkeypatch, tmp_path):
    """VALIDATION 73-01-02 (IMG-01): tenacity retries on TimeoutError.

    Mock _dreamina_submit to raise subprocess.TimeoutExpired 3 times then
    succeed. Assert the result status == "ok" and retries reflect the
    recovery. tenacity wait is patched to zero for test speed.
    """
    _patch_verify(monkeypatch)

    call_count = {"value": 0}

    async def _fake_submit(prompt, ratio, model_version):
        call_count["value"] += 1
        if call_count["value"] <= 3:
            raise subprocess.TimeoutExpired(cmd=["dreamina"], timeout=15)
        return "bbbbbbbb-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._dreamina_submit", _fake_submit
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._dreamina_poll", _fake_poll
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._download", _fake_download
    )
    # Patch tenacity wait to zero for speed — tenacity calls the wait
    # callable with (retry_state) so accept and ignore positional args.
    def _no_wait(*args, **kwargs):
        return 0
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager.wait_exponential",
        lambda **kw: _no_wait,
    )

    prompts = [{"id": "S_retry", "prompt": "retry scene"}]
    results = await batch_submit(prompts, str(tmp_path), deadline_sec=30)

    assert len(results) == 1
    # The task recovered after retries.
    assert results[0]["status"] in ("ok", "degraded")
    assert call_count["value"] >= 4  # 3 failures + 1 success


@pytest.mark.asyncio
async def test_blocks_until_all_resolve(monkeypatch, tmp_path):
    """VALIDATION 73-01-03 (IMG-02): batch_submit blocks until ALL resolve.

    Mock items with staggered delays. Assert the return value length ==
    input length (no incremental/partial return as with as_completed).
    """
    _patch_verify(monkeypatch)

    # Stagger: items 0-2 fast (0.01s), items 3-5 slow (0.1s).
    delays = [0.01, 0.01, 0.01, 0.1, 0.1, 0.1]

    async def _fake_submit(prompt, ratio, model_version):
        # Extract delay from prompt text.
        idx = 0
        for i in range(6):
            if f"scene {i}" in prompt:
                idx = i
                break
        await asyncio.sleep(delays[idx])
        return f"id-{idx:08}-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._dreamina_submit", _fake_submit
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._dreamina_poll", _fake_poll
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.dreamina_manager._download", _fake_download
    )

    prompts = [{"id": f"S{i}", "prompt": f"scene {i}"} for i in range(6)]
    results = await batch_submit(prompts, str(tmp_path), deadline_sec=30)

    # IMG-02 proof: ALL 6 results returned (gather block-on-all, NOT
    # as_completed incremental).
    assert len(results) == 6
    # Every result has a status key (not a bare exception).
    for r in results:
        assert "status" in r
        assert r["status"] in ("ok", "failed", "degraded")


# ---------------------------------------------------------------------------
# IMG-04 RHD/LHD 3-attempt budget tests (Plan 73-02 Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rhd_lhd_3_attempt_budget(monkeypatch, tmp_path):
    """VALIDATION 73-02-01 (IMG-04): 3-attempt budget escalates prompt each attempt.

    Mock verify_image_content to fail on attempts 0+1, succeed on attempt 2
    (the image2image fallback attempt). Assert _escalate_prompt called 3
    times with escalating wording and final status == "ok".
    """
    escalate_calls: list[tuple[int, str | None]] = []

    from plugins.kais_aigc import dreamina_manager as dm

    original_escalate = dm._escalate_prompt

    def _tracking_escalate(base_prompt, attempt, directional):
        escalate_calls.append((attempt, directional))
        return original_escalate(base_prompt, attempt, directional)

    monkeypatch.setattr(dm, "_escalate_prompt", _tracking_escalate)

    # Vision-verify: fail-fail-succeed.
    verify_calls = {"count": 0}

    async def _flaky_verify(image_path, expected_content, directional_check=None, stratum=None):
        verify_calls["count"] += 1
        if verify_calls["count"] < 3:
            return {"pass": False, "confidence": 0.3, "description": "RHD", "cached": False}
        return {"pass": True, "confidence": 0.95, "description": "LHD ok", "cached": False}

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _flaky_verify)

    async def _fake_submit(prompt, ratio, model_version):
        return "cccccccc-0000-0000-0000-000000000000"

    async def _fake_image2image(ref_image_path, prompt, ratio, model_version):
        return "iiiiiiii-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_image2image", _fake_image2image)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)

    item = {
        "id": "S_lhd",
        "prompt": "car interior scene",
        "expected": "driver in car",
        "directional": "lhd",
        "lhd_reference_path": "/fake/lhd_ref.png",
    }
    results = await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert len(results) == 1
    assert results[0]["status"] == "ok"
    # _escalate_prompt called 3 times (attempts 0, 1, 2).
    assert len(escalate_calls) == 3
    # Each attempt uses directional "lhd".
    for attempt_num, directional in escalate_calls:
        assert directional == "lhd"
    # Verify was called 3 times.
    assert verify_calls["count"] == 3


@pytest.mark.asyncio
async def test_image2image_fallback_on_attempt_3(monkeypatch, tmp_path):
    """IMG-04: attempt 2 (3rd attempt) invokes image2image when prompt is None.

    Mock verify_image_content to fail all 3 attempts. Assert attempt 2
    invokes _dreamina_image2image (NOT _dreamina_submit text2image), and
    final status is "degraded".
    """
    from plugins.kais_aigc import dreamina_manager as dm

    submit_calls = {"text2image": 0, "image2image": 0}

    async def _tracking_submit(prompt, ratio, model_version):
        submit_calls["text2image"] += 1
        return "dddddddd-0000-0000-0000-000000000000"

    async def _tracking_image2image(ref_image_path, prompt, ratio, model_version):
        submit_calls["image2image"] += 1
        return "eeeeeeee-0000-0000-0000-000000000000"

    async def _always_fail_verify(image_path, expected_content, directional_check=None, stratum=None):
        return {"pass": False, "confidence": 0.2, "description": "still RHD", "cached": False}

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _always_fail_verify)

    monkeypatch.setattr(dm, "_dreamina_submit", _tracking_submit)
    monkeypatch.setattr(dm, "_dreamina_image2image", _tracking_image2image)

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)

    item = {
        "id": "S_i2i",
        "prompt": "car interior scene",
        "expected": "driver in car",
        "directional": "lhd",
        "lhd_reference_path": "/fake/lhd_ref.png",
    }
    results = await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert len(results) == 1
    # After 3 failed attempts, status is degraded.
    assert results[0]["status"] == "degraded"
    # text2image used for attempts 0+1; image2image used for attempt 2.
    assert submit_calls["text2image"] == 2
    assert submit_calls["image2image"] == 1


# ---------------------------------------------------------------------------
# WR-06: poll-timeout + malformed-response failure-path tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_timeout_returns_degraded(monkeypatch, tmp_path):
    """WR-06: when _dreamina_poll returns None (timeout), the task fails cleanly.

    A None return from _dreamina_poll signals poll-exhaustion (180s timeout
    or gen_status=failed). The outer 3-attempt loop should catch the
    RuntimeError, retry, and ultimately return a "failed" or "degraded"
    result — never raise to the caller.
    """
    _patch_verify(monkeypatch)

    async def _fake_submit(prompt, ratio, model_version):
        return "ffffffff-0000-0000-0000-000000000000"

    async def _poll_none(submit_id, max_wait=180):
        # Always return None — simulates 180s timeout / gen_status=failed.
        return None

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    from plugins.kais_aigc import dreamina_manager as dm
    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_poll", _poll_none)
    monkeypatch.setattr(dm, "_download", _fake_download)
    # Speed up tenacity wait.
    def _no_wait(*args, **kwargs):
        return 0
    monkeypatch.setattr(dm, "wait_exponential", lambda **kw: _no_wait)

    prompts = [{"id": "S_timeout", "prompt": "timeout scene"}]
    results = await batch_submit(prompts, str(tmp_path), deadline_sec=30)

    assert len(results) == 1
    # All 3 attempts failed → status is failed or degraded, NOT an exception.
    assert results[0]["status"] in ("failed", "degraded")
    # No image was produced.
    assert results[0]["image_path"] is None or results[0]["status"] == "degraded"


@pytest.mark.asyncio
async def test_malformed_response_returns_failed(monkeypatch, tmp_path):
    """WR-06: empty / non-JSON stdout from dreamina submit raises and retries.

    Mock _dreamina_submit to raise RuntimeError on invalid JSON. After 3
    outer attempts (each exhausting tenacity's 4 inner attempts) the task
    returns status="failed" — never propagates the RuntimeError to caller.
    """
    _patch_verify(monkeypatch)

    call_count = {"value": 0}

    async def _submit_always_invalid_json(prompt, ratio, model_version):
        # Mirror the real _dreamina_submit behavior: invalid JSON → RuntimeError.
        call_count["value"] += 1
        raise RuntimeError("dreamina submit returned invalid JSON: ...")

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success",
                "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    from plugins.kais_aigc import dreamina_manager as dm
    monkeypatch.setattr(dm, "_dreamina_submit", _submit_always_invalid_json)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)
    # Speed up tenacity wait.
    def _no_wait(*args, **kwargs):
        return 0
    monkeypatch.setattr(dm, "wait_exponential", lambda **kw: _no_wait)

    prompts = [{"id": "S_malformed", "prompt": "malformed scene"}]
    results = await batch_submit(prompts, str(tmp_path), deadline_sec=30)

    assert len(results) == 1
    # Invalid JSON on every attempt → status is failed or degraded.
    assert results[0]["status"] in ("failed", "degraded")
    # Error field records the failure reason.
    assert results[0]["error"] is not None
    assert "invalid JSON" in results[0]["error"] or "RuntimeError" in results[0]["error"]


# ---------------------------------------------------------------------------
# Phase 79-02: stratum param passing tests (IMG-09-APPLY Task 4)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stratum_passed_to_verify_ref_count_1(monkeypatch, tmp_path):
    """Phase 79 Task 4: dreamina_manager passes stratum='1-ref' when item has ref_count=1.

    Captures the stratum kwarg passed to verify_image_content and asserts
    it matches _infer_stratum(item) for an item with ref_count=1.
    """
    captured = {"stratum": None}

    async def _capturing_verify(image_path, expected_content, directional_check=None, stratum=None):
        captured["stratum"] = stratum
        return {"pass": True, "confidence": 0.92, "description": "fake", "cached": False}

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _capturing_verify)

    async def _fake_submit(prompt, ratio, model_version):
        return "stratum01-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    from plugins.kais_aigc import dreamina_manager as dm
    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)

    item = {
        "id": "S_1ref",
        "prompt": "scene with 1 ref",
        "expected": "content",
        "ref_count": 1,
    }
    await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert captured["stratum"] == "1-ref"


@pytest.mark.asyncio
async def test_stratum_passed_to_verify_ref_count_3(monkeypatch, tmp_path):
    """Phase 79 Task 4: stratum='3-ref' when item has ref_count=3."""
    captured = {"stratum": None}

    async def _capturing_verify(image_path, expected_content, directional_check=None, stratum=None):
        captured["stratum"] = stratum
        return {"pass": True, "confidence": 0.92, "description": "fake", "cached": False}

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _capturing_verify)

    async def _fake_submit(prompt, ratio, model_version):
        return "stratum03-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    from plugins.kais_aigc import dreamina_manager as dm
    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)

    item = {
        "id": "S_3ref",
        "prompt": "scene with 3 refs",
        "expected": "content",
        "ref_count": 3,
    }
    await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert captured["stratum"] == "3-ref"


@pytest.mark.asyncio
async def test_stratum_passed_to_verify_ref_count_5(monkeypatch, tmp_path):
    """Phase 79 Task 4: stratum='5-ref' when item has ref_count=5."""
    captured = {"stratum": None}

    async def _capturing_verify(image_path, expected_content, directional_check=None, stratum=None):
        captured["stratum"] = stratum
        return {"pass": True, "confidence": 0.92, "description": "fake", "cached": False}

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _capturing_verify)

    async def _fake_submit(prompt, ratio, model_version):
        return "stratum05-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    from plugins.kais_aigc import dreamina_manager as dm
    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)

    item = {
        "id": "S_5ref",
        "prompt": "scene with 5 refs",
        "expected": "content",
        "ref_count": 5,
    }
    await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert captured["stratum"] == "5-ref"


@pytest.mark.asyncio
async def test_stratum_passed_to_verify_text2image(monkeypatch, tmp_path):
    """Phase 79 Task 4: stratum='text2image' when item has no ref_count + no directional."""
    captured = {"stratum": None}

    async def _capturing_verify(image_path, expected_content, directional_check=None, stratum=None):
        captured["stratum"] = stratum
        return {"pass": True, "confidence": 0.92, "description": "fake", "cached": False}

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _capturing_verify)

    async def _fake_submit(prompt, ratio, model_version):
        return "stratumt2i-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        return {"gen_status": "success", "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

    async def _fake_download(url, output_path):
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    from plugins.kais_aigc import dreamina_manager as dm
    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)

    # No ref_count, no directional → text2image stratum.
    item = {
        "id": "S_t2i",
        "prompt": "text2image scene",
        "expected": "content",
    }
    await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert captured["stratum"] == "text2image"


# ---------------------------------------------------------------------------
# Phase 82-01: usage capture + cost computation (XCUT-04c-INSTRUMENT)
# ---------------------------------------------------------------------------


class TestUsageCapture:
    """Phase 82: _compute_cost_usd + usage capture in _generate_one_with_verify."""

    def test_dreamina_task_result_has_usage_fields(self):
        """WR-01: DreaminaTaskResult TypedDict declares usage + estimated_cost_usd.

        Schema drift check: both fields were added in Phase 82 but missing
        from the TypedDict annotation. Verify they're present now.
        """
        from plugins.kais_aigc.dreamina_manager import DreaminaTaskResult
        # __annotations__ includes all declared fields.
        annotations = DreaminaTaskResult.__annotations__
        assert "usage" in annotations
        assert "estimated_cost_usd" in annotations

    def test_compute_cost_usd_defaults(self, monkeypatch, tmp_path):
        """_compute_cost_usd uses $3/$8 per 1M tokens defaults when no config."""
        from plugins.kais_aigc import dreamina_manager as dm

        # Clear pricing cache + point hermes home at empty tmp.
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        # 1M input tokens → $3.0
        assert dm._compute_cost_usd(1_000_000, 0) == 3.0
        # 1M output tokens → $8.0
        assert dm._compute_cost_usd(0, 1_000_000) == 8.0
        # Mixed: 1M input + 1M output → $11.0
        assert dm._compute_cost_usd(1_000_000, 1_000_000) == 11.0

    def test_compute_cost_usd_config_pricing(self, monkeypatch, tmp_path):
        """_compute_cost_usd reads custom pricing from config.yaml."""
        from plugins.kais_aigc import dreamina_manager as dm

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "glm_46v:\n  pricing:\n    input_usd_per_1m_tokens: 5.0\n"
            "    output_usd_per_1m_tokens: 10.0\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        # Custom rates: 1M input → $5.0, 1M output → $10.0
        assert dm._compute_cost_usd(1_000_000, 0) == 5.0
        assert dm._compute_cost_usd(0, 1_000_000) == 10.0

    def test_compute_cost_usd_invalid_config(self, monkeypatch, tmp_path, caplog):
        """Invalid pricing (negative) falls back to defaults + warns."""
        import logging
        from plugins.kais_aigc import dreamina_manager as dm

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "glm_46v:\n  pricing:\n    input_usd_per_1m_tokens: -1.0\n"
            "    output_usd_per_1m_tokens: 8.0\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        with caplog.at_level(logging.WARNING):
            result = dm._compute_cost_usd(1_000_000, 0)
        # Negative input rate → fallback to default $3.0.
        assert result == 3.0
        # Warning was logged.
        assert any("invalid" in r.message.lower() or "pricing" in r.message.lower()
                   for r in caplog.records)

    @pytest.mark.asyncio
    async def test_generate_one_captures_usage(self, monkeypatch, tmp_path):
        """_generate_one_with_verify result includes usage + estimated_cost_usd."""
        from plugins.kais_aigc import dreamina_manager as dm

        async def _verify_with_usage(image_path, expected_content,
                                     directional_check=None, stratum=None):
            return {
                "pass": True, "confidence": 0.92, "description": "ok",
                "cached": False,
                "usage": {"input_tokens": 300, "output_tokens": 150},
            }

        import plugins.kais_aigc.vision_verify as vv
        monkeypatch.setattr(vv, "verify_image_content", _verify_with_usage)

        async def _fake_submit(prompt, ratio, model_version):
            return "usage-0000-0000-0000-000000000000"

        async def _fake_poll(submit_id, max_wait=180):
            return {"gen_status": "success",
                    "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

        async def _fake_download(url, output_path):
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

        monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
        monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
        monkeypatch.setattr(dm, "_download", _fake_download)
        # Clear pricing cache so defaults are used.
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        item = {
            "id": "S_usage",
            "prompt": "scene",
            "expected": "content",
        }
        results = await batch_submit([item], str(tmp_path), deadline_sec=30)

        assert len(results) == 1
        assert results[0]["status"] == "ok"
        assert "usage" in results[0]
        assert results[0]["usage"]["input_tokens"] == 300
        assert results[0]["usage"]["output_tokens"] == 150
        # 300/1M * 3.0 + 150/1M * 8.0 = 0.0009 + 0.0012 = 0.0021
        assert abs(results[0]["estimated_cost_usd"] - 0.0021) < 1e-9

    @pytest.mark.asyncio
    async def test_generate_one_no_expected_no_usage(self, monkeypatch, tmp_path):
        """When expected="" (no vision-verify), usage is 0/0 + cost is 0.0."""
        from plugins.kais_aigc import dreamina_manager as dm

        async def _fake_submit(prompt, ratio, model_version):
            return "noexp-0000-0000-0000-000000000000"

        async def _fake_poll(submit_id, max_wait=180):
            return {"gen_status": "success",
                    "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

        async def _fake_download(url, output_path):
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

        monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
        monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
        monkeypatch.setattr(dm, "_download", _fake_download)

        # No "expected" key → vision-verify is skipped.
        item = {"id": "S_noexp", "prompt": "scene"}
        results = await batch_submit([item], str(tmp_path), deadline_sec=30)

        assert len(results) == 1
        assert results[0]["status"] == "ok"
        assert results[0]["usage"]["input_tokens"] == 0
        assert results[0]["usage"]["output_tokens"] == 0
        assert results[0]["estimated_cost_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_vision_verify_exception_includes_usage(self, monkeypatch, tmp_path):
        """WR-02: exception-path vr fallback dict includes 'usage' key.

        When verify_image_content raises an exception, the fallback vr dict
        must include a 'usage' key (with zero tokens) for shape consistency
        with successful verify_image_content returns. Previously the
        fallback had only {'pass', 'confidence'} — 2 keys instead of 3+.
        """
        from plugins.kais_aigc import dreamina_manager as dm

        async def _raising_verify(image_path, expected_content,
                                  directional_check=None, stratum=None):
            raise RuntimeError("simulated vision-verify failure")

        import plugins.kais_aigc.vision_verify as vv
        monkeypatch.setattr(vv, "verify_image_content", _raising_verify)

        async def _fake_submit(prompt, ratio, model_version):
            return "vrexcp-0000-0000-0000-000000000000"

        async def _fake_image2image(ref_image_path, prompt, ratio, model_version):
            return "vrexcp-i2i-0000-0000-0000-000000000000"

        async def _fake_poll(submit_id, max_wait=180):
            return {"gen_status": "success",
                    "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

        async def _fake_download(url, output_path):
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

        monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
        monkeypatch.setattr(dm, "_dreamina_image2image", _fake_image2image)
        monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
        monkeypatch.setattr(dm, "_download", _fake_download)
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        # The item goes through 3 attempts; vision-verify raises each time.
        # Final status is "degraded" (all 3 attempts failed vision-verify).
        item = {
            "id": "S_vrexcp",
            "prompt": "scene",
            "expected": "content",
            "directional": "lhd",
            "lhd_reference_path": "/fake/lhd_ref.png",
        }
        results = await batch_submit([item], str(tmp_path), deadline_sec=30)

        assert len(results) == 1
        assert results[0]["status"] == "degraded"
        # WR-02: usage key present in result (exception path contributed
        # zero tokens — no vision-judge call succeeded).
        assert "usage" in results[0]
        assert results[0]["usage"]["input_tokens"] == 0
        assert results[0]["usage"]["output_tokens"] == 0
        assert results[0]["estimated_cost_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_batch_submit_writes_token_fields(self, monkeypatch, tmp_path):
        """batch_submit record_metric dict includes token/cost fields."""
        from plugins.kais_aigc import dreamina_manager as dm

        recorded_metrics: list[dict] = []

        async def _verify_with_usage(image_path, expected_content,
                                     directional_check=None, stratum=None):
            return {
                "pass": True, "confidence": 0.92, "description": "ok",
                "cached": False,
                "usage": {"input_tokens": 500, "output_tokens": 200},
            }

        import plugins.kais_aigc.vision_verify as vv
        monkeypatch.setattr(vv, "verify_image_content", _verify_with_usage)

        async def _fake_submit(prompt, ratio, model_version):
            return "writtok-0000-0000-0000-000000000000"

        async def _fake_poll(submit_id, max_wait=180):
            return {"gen_status": "success",
                    "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

        async def _fake_download(url, output_path):
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

        monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
        monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
        monkeypatch.setattr(dm, "_download", _fake_download)

        # Intercept record_metric to capture the metric dict.
        def _capturing_record(path, metric):
            recorded_metrics.append(metric)

        import plugins.kais_aigc.dreamina_stats as ds
        monkeypatch.setattr(ds, "record_metric", _capturing_record)

        item = {"id": "S_writtok", "prompt": "scene", "expected": "content"}
        await batch_submit([item], str(tmp_path), deadline_sec=30)

        assert len(recorded_metrics) == 1
        metric = recorded_metrics[0]
        assert metric["input_tokens"] == 500
        assert metric["output_tokens"] == 200
        # 500/1M * 3.0 + 200/1M * 8.0 = 0.0015 + 0.0016 = 0.0031
        assert abs(metric["estimated_cost_usd"] - 0.0031) < 1e-9


    @pytest.mark.asyncio
    async def test_multi_attempt_accumulates_usage(self, monkeypatch, tmp_path):
        """CR-01: multi-attempt items must accumulate usage across ALL attempts.

        Previously only the LAST attempt's usage was captured, undercounting
        cost by ~67% for 3-attempt items. This test verifies that a 3-attempt
        item (fail-fail-pass) reports the SUM of all 3 attempts' tokens.
        """
        from plugins.kais_aigc import dreamina_manager as dm

        # Vision-verify: fail-fail-succeed, each with distinct usage.
        verify_calls = {"count": 0}

        async def _multi_attempt_verify(image_path, expected_content,
                                        directional_check=None, stratum=None):
            verify_calls["count"] += 1
            if verify_calls["count"] == 1:
                return {
                    "pass": False, "confidence": 0.3, "description": "low",
                    "cached": False,
                    "usage": {"input_tokens": 100, "output_tokens": 40},
                }
            elif verify_calls["count"] == 2:
                return {
                    "pass": False, "confidence": 0.5, "description": "mid",
                    "cached": False,
                    "usage": {"input_tokens": 120, "output_tokens": 50},
                }
            return {
                "pass": True, "confidence": 0.95, "description": "pass",
                "cached": False,
                "usage": {"input_tokens": 110, "output_tokens": 45},
            }

        import plugins.kais_aigc.vision_verify as vv
        monkeypatch.setattr(vv, "verify_image_content", _multi_attempt_verify)

        async def _fake_submit(prompt, ratio, model_version):
            return "accum-0000-0000-0000-000000000000"

        async def _fake_image2image(ref_image_path, prompt, ratio, model_version):
            return "accum-i2i-0000-0000-0000-000000000000"

        async def _fake_poll(submit_id, max_wait=180):
            return {"gen_status": "success",
                    "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

        async def _fake_download(url, output_path):
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

        monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
        monkeypatch.setattr(dm, "_dreamina_image2image", _fake_image2image)
        monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
        monkeypatch.setattr(dm, "_download", _fake_download)
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        item = {
            "id": "S_accum",
            "prompt": "scene",
            "expected": "content",
            "directional": "lhd",
            "lhd_reference_path": "/fake/lhd_ref.png",
        }
        results = await batch_submit([item], str(tmp_path), deadline_sec=30)

        assert len(results) == 1
        assert results[0]["status"] == "ok"
        assert verify_calls["count"] == 3
        # CR-01: accumulated usage = 100+120+110 = 330 input, 40+50+45 = 135 output
        assert results[0]["usage"]["input_tokens"] == 330
        assert results[0]["usage"]["output_tokens"] == 135
        # 330/1M * 3.0 + 135/1M * 8.0 = 0.00099 + 0.00108 = 0.00207
        assert abs(results[0]["estimated_cost_usd"] - 0.00207) < 1e-9

    @pytest.mark.asyncio
    async def test_multi_attempt_degraded_accumulates_usage(self, monkeypatch, tmp_path):
        """CR-01: degraded (all 3 attempts fail) must also accumulate usage."""
        from plugins.kais_aigc import dreamina_manager as dm

        verify_calls = {"count": 0}

        async def _all_fail_verify(image_path, expected_content,
                                   directional_check=None, stratum=None):
            verify_calls["count"] += 1
            return {
                "pass": False, "confidence": 0.2, "description": "fail",
                "cached": False,
                "usage": {"input_tokens": 200, "output_tokens": 80},
            }

        import plugins.kais_aigc.vision_verify as vv
        monkeypatch.setattr(vv, "verify_image_content", _all_fail_verify)

        async def _fake_submit(prompt, ratio, model_version):
            return "deg-0000-0000-0000-000000000000"

        async def _fake_poll(submit_id, max_wait=180):
            return {"gen_status": "success",
                    "result_json": {"images": [{"image_url": "https://x/y.png"}]}}

        async def _fake_download(url, output_path):
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

        monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
        monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
        monkeypatch.setattr(dm, "_download", _fake_download)
        monkeypatch.setattr(
            "plugins.kais_aigc.dreamina_manager.get_hermes_home",
            lambda: str(tmp_path),
        )
        dm._pricing_cache = None

        item = {
            "id": "S_degv",
            "prompt": "scene",
            "expected": "content",
            "directional": "lhd",
            "lhd_reference_path": "/fake/lhd.png",
        }
        results = await batch_submit([item], str(tmp_path), deadline_sec=30)

        assert len(results) == 1
        assert results[0]["status"] == "degraded"
        assert verify_calls["count"] == 3
        # CR-01: 3 attempts × 200/80 = 600/240 accumulated
        assert results[0]["usage"]["input_tokens"] == 600
        assert results[0]["usage"]["output_tokens"] == 240
        # 600/1M * 3.0 + 240/1M * 8.0 = 0.0018 + 0.00192 = 0.00372
        assert abs(results[0]["estimated_cost_usd"] - 0.00372) < 1e-9

