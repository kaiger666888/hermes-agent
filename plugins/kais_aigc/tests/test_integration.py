"""test_integration.py — end-to-end integration tests for IMG chain.

Validates that dreamina_manager.batch_submit → vision_verify → result-chain
works end-to-end with mocked subprocess + vision judge. Covers:

  - VALIDATION 73-03-01 (IMG-01): 3-shot batch e2e — all 3 succeed,
    vision_verified=True on each, results list length == input length.
  - VALIDATION 73-03-02 (IMG-04): RHD/LHD failure injection e2e —
    vision-verify fails attempts 0+1, 3rd attempt uses image2image
    fallback; result status is "ok" (succeeded) or "degraded"
    (operator-actionable, NOT silent).

All tests mock at the async boundary (_dreamina_submit / _dreamina_poll /
_download / _dreamina_image2image) AND at the vision_verify boundary
(verify_image_content) — NO real subprocess, NO real vision API calls.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from plugins.kais_aigc import dreamina_manager as dm
from plugins.kais_aigc import vision_verify as vv
from plugins.kais_aigc.dreamina_manager import batch_submit


# ---------------------------------------------------------------------------
# Mock helpers (mock at async boundary — NOT subprocess.run, per Plan 73-01
# deviation #2: subprocess-level mocks track thread-pool concurrency, not
# asyncio.Semaphore concurrency).
# ---------------------------------------------------------------------------


def _patch_chain(
    monkeypatch,
    *,
    submit_side_effect=None,
    image2image_side_effect=None,
    poll_response=None,
    verify_side_effect=None,
):
    """Patch the full dreamina_manager → vision_verify chain at async boundaries.

    Args:
        submit_side_effect: async fn(prompt, ratio, model_version) -> submit_id.
            If None, a default always-succeed submit is used.
        image2image_side_effect: async fn(ref, prompt, ratio, mv) -> submit_id.
            If None, default always-succeed is used.
        poll_response: dict returned by _dreamina_poll. If None, default
            success response with a placeholder URL is used.
        verify_side_effect: async fn(image_path, expected, directional_check=None)
            -> dict. If None, default always-pass high-confidence is used.
    """
    if submit_side_effect is None:
        async def _default_submit(prompt, ratio, model_version):
            return "aaaaaaaa-0000-0000-0000-000000000000"
        submit_side_effect = _default_submit

    if image2image_side_effect is None:
        async def _default_i2i(ref_image_path, prompt, ratio, model_version):
            return "iiiiiiii-0000-0000-0000-000000000000"
        image2image_side_effect = _default_i2i

    if poll_response is None:
        poll_response = {
            "gen_status": "success",
            "result_json": {"images": [{"image_url": "https://byteimg.com/x.png"}]},
        }

    if verify_side_effect is None:
        async def _default_verify(image_path, expected_content, directional_check=None, stratum=None):
            return {
                "pass": True,
                "confidence": 0.92,
                "description": "fake-ok",
                "cached": False,
            }
        verify_side_effect = _default_verify

    async def _fake_poll(submit_id, max_wait=180):
        return poll_response

    async def _fake_download(url, output_path):
        # Write real bytes so vision_verify.read_bytes() (if invoked
        # unmocked) does not crash. Tests that exercise the chain via
        # mocked verify never touch the file contents.
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(dm, "_dreamina_submit", submit_side_effect)
    monkeypatch.setattr(dm, "_dreamina_image2image", image2image_side_effect)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)
    monkeypatch.setattr(vv, "verify_image_content", verify_side_effect)


# ---------------------------------------------------------------------------
# Test 73-03-01 (IMG-01): 3-shot batch e2e
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_e2e(monkeypatch, tmp_path):
    """VALIDATION 73-03-01 (IMG-01): 3-shot batch end-to-end.

    Mock the CLI + vision-verify chain. Submit a 3-item batch where each item
    has expected content + directional check. Assert:
      - batch_submit returns a list of length 3 (sync queue — block-on-all)
      - every result has status == "ok"
      - every result has vision_verified == True
      - every result has vision_confidence >= 0.7 (high-confidence pass)
      - batch_submit was called once per item (3 _dreamina_submit calls)
    """
    submit_calls: list[str] = []

    async def _tracking_submit(prompt, ratio, model_version):
        submit_calls.append(prompt)
        # Unique submit_id per call to simulate real CLI.
        return f"{0x10 + len(submit_calls):08x}-0000-0000-0000-000000000000"

    verify_calls: list[tuple[str, str, str | None]] = []

    async def _tracking_verify(image_path, expected_content, directional_check=None, stratum=None):
        verify_calls.append((image_path, expected_content, directional_check))
        return {
            "pass": True,
            "confidence": 0.88,
            "description": "fake-pass",
            "cached": False,
        }

    _patch_chain(
        monkeypatch,
        submit_side_effect=_tracking_submit,
        verify_side_effect=_tracking_verify,
    )

    prompts = [
        {
            "id": "S01",
            "prompt": "baby in car seat interior shot",
            "expected": "baby in car seat",
            "directional": "lhd",
        },
        {
            "id": "S02",
            "prompt": "mom driving car interior",
            "expected": "woman driving",
            "directional": "lhd",
        },
        {
            "id": "S03",
            "prompt": "dad in passenger seat",
            "expected": "man in passenger seat",
            "directional": "lhd",
        },
    ]
    results = await batch_submit(prompts, str(tmp_path), concurrency=3, deadline_sec=30)

    # IMG-01: results list length matches input (sync queue block-on-all).
    assert isinstance(results, list)
    assert len(results) == 3, (
        f"batch_submit must return one result per input item; got {len(results)}"
    )

    # IMG-01: every result succeeded + vision-verified pass.
    for i, r in enumerate(results):
        assert r["status"] == "ok", (
            f"result[{i}] status must be 'ok'; got {r['status']!r} (error: {r.get('error')})"
        )
        assert r["vision_verified"] is True, (
            f"result[{i}] must be vision_verified=True; got {r['vision_verified']}"
        )
        assert r["vision_confidence"] is not None and r["vision_confidence"] >= 0.7, (
            f"result[{i}] confidence must be >= 0.7; got {r['vision_confidence']}"
        )
        assert r["image_path"] is not None, (
            f"result[{i}] image_path must be populated on success"
        )

    # batch_submit was called once per item — each item submitted exactly
    # once on attempt 0 (happy path — verify passes first try).
    assert len(submit_calls) == 3, (
        f"expected 3 _dreamina_submit calls (happy path); got {len(submit_calls)}"
    )

    # Vision-verify ran once per item (3 calls).
    assert len(verify_calls) == 3, (
        f"expected 3 verify_image_content calls; got {len(verify_calls)}"
    )

    # Each verify call carried the expected directional_check.
    for _path, _expected, directional in verify_calls:
        assert directional == "lhd", (
            f"directional_check must propagate; got {directional!r}"
        )


# ---------------------------------------------------------------------------
# Test 73-03-02 (IMG-04): RHD/LHD failure injection e2e
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rhd_lhd_e2e(monkeypatch, tmp_path):
    """VALIDATION 73-03-02 (IMG-04): RHD/LHD failure injection end-to-end.

    Mock verify_image_content to FAIL on attempts 0+1 (low-confidence RHD
    detected), then SUCCEED on attempt 2 (image2image fallback produces a
    confirmed LHD image). Assert:
      - attempt 2 invokes _dreamina_image2image (NOT _dreamina_submit)
      - final status is "ok" (image2image succeeded) OR "degraded"
        (operator-actionable with explicit error message)
      - error is non-empty when status == "degraded" (NOT silent)
    """
    submit_calls = {"text2image": 0, "image2image": 0}
    verify_call_count = {"n": 0}

    async def _tracking_submit(prompt, ratio, model_version):
        submit_calls["text2image"] += 1
        return "aaaaaaaa-0000-0000-0000-000000000000"

    async def _tracking_image2image(ref_image_path, prompt, ratio, model_version):
        submit_calls["image2image"] += 1
        return "bbbbbbbb-0000-0000-0000-000000000000"

    async def _flaky_verify(image_path, expected_content, directional_check=None, stratum=None):
        verify_call_count["n"] += 1
        if verify_call_count["n"] < 3:
            # First two attempts: low-confidence RHD detection — fail.
            return {
                "pass": False,
                "confidence": 0.3,
                "description": "RHD detected",
                "cached": False,
            }
        # Attempt 3 (image2image fallback): high-confidence LHD — pass.
        return {
            "pass": True,
            "confidence": 0.85,
            "description": "LHD confirmed via image2image",
            "cached": False,
        }

    _patch_chain(
        monkeypatch,
        submit_side_effect=_tracking_submit,
        image2image_side_effect=_tracking_image2image,
        verify_side_effect=_flaky_verify,
    )

    item = {
        "id": "S_rhd_lhd",
        "prompt": "car interior scene",
        "expected": "driver in car",
        "directional": "lhd",
        "lhd_reference_path": "/fake/lhd_ref.png",
    }
    results = await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert len(results) == 1, f"expected 1 result; got {len(results)}"
    result = results[0]

    # Status is either ok (3rd attempt passed) or degraded (operator-actionable).
    assert result["status"] in ("ok", "degraded"), (
        f"status must be 'ok' or 'degraded' after failure injection; "
        f"got {result['status']!r}"
    )

    # IMG-04 invariant: attempt 2 MUST use image2image, NOT text2image.
    #   attempt 0 = text2image (fail-verify)
    #   attempt 1 = text2image (fail-verify)
    #   attempt 2 = image2image (fallback per _escalate_prompt returning None)
    assert submit_calls["text2image"] == 2, (
        f"expected 2 text2image calls (attempts 0+1); "
        f"got {submit_calls['text2image']}"
    )
    assert submit_calls["image2image"] == 1, (
        f"expected 1 image2image call (attempt 2 fallback); "
        f"got {submit_calls['image2image']}"
    )

    # Vision-verify was called once per attempt (3 attempts → 3 calls).
    assert verify_call_count["n"] == 3, (
        f"expected 3 verify calls (one per attempt); got {verify_call_count['n']}"
    )

    # If status is degraded, error MUST be non-empty (NOT silent).
    if result["status"] == "degraded":
        assert result["error"], (
            "degraded status MUST carry an explicit error message "
            "(operator-actionable, not silent)"
        )
        assert result["vision_confidence"] is not None, (
            "degraded status MUST record the last confidence for operator review"
        )
