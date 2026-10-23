"""test_dreamina_deadlock.py — deadlock detection + download hardening tests.

2026-09-03 fix batch (probe matrix: dreamina 5.0 × image2image server-side
deadlock — gen_status=querying + queue_info.queue_status=Finish + result_json
never returns).

Covers:
  - _dreamina_poll: deadlock fingerprint raises RuntimeError("dreamina deadlock...")
  - _dreamina_poll: normal success still returns the payload
  - gen_image template poll_until_done: same fingerprint → returns None (fast bail)
  - template download(): curl-first (aria2c only as fallback)
  - FIX-4 rescue: 5.x i2i deadlock downgrades to 4.6 exactly once, result
    carries model_fallback="5.0->4.6"

All tests monkeypatch subprocess (no real dreamina CLI) — no network. Each
test < 1s.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

import plugins.kais_aigc.dreamina_manager as dm
from plugins.kais_aigc.dreamina_manager import batch_submit

# Repo root (tests live at plugins/kais_aigc/tests/).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATE_PATH = (
    _REPO_ROOT / "skills" / "kais-movie-pipeline" / "templates"
    / "dreamina_gen_image.py"
)

# Deadlock fingerprint: queue finished but result_json absent (2026-09-03).
_DEADLOCK_PAYLOAD = json.dumps({
    "gen_status": "querying",
    "queue_info": {"queue_status": "Finish"},
})
_SUCCESS_PAYLOAD = json.dumps({
    "gen_status": "success",
    "result_json": {"images": [{"image_url": "https://byteimg.com/ok.png"}]},
})


class _MockResult:
    """Minimal CompletedProcess stand-in for subprocess.run mocks."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _load_template():
    """Load skills/kais-movie-pipeline/templates/dreamina_gen_image.py by path."""
    spec = importlib.util.spec_from_file_location(
        "dreamina_gen_image_template", _TEMPLATE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


async def _no_sleep(delay):
    """Async no-op standing in for asyncio.sleep (keeps tests < 1s)."""
    return None


# ---------------------------------------------------------------------------
# _dreamina_poll deadlock detection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_deadlock_raises_runtime_error(monkeypatch):
    """querying + queue_status=Finish + no result_json → RuntimeError."""
    def _fake_run(cmd, capture_output=True, text=True, encoding=None, timeout=None):
        return _MockResult(returncode=0, stdout=_DEADLOCK_PAYLOAD)

    monkeypatch.setattr(dm.subprocess, "run", _fake_run)
    monkeypatch.setattr(dm.asyncio, "sleep", _no_sleep)

    with pytest.raises(RuntimeError, match="dreamina deadlock"):
        await dm._dreamina_poll(
            "deadlock-0000-0000-0000-000000000000", max_wait=30
        )


@pytest.mark.asyncio
async def test_poll_success_still_returns_data(monkeypatch):
    """Normal success payload is returned unchanged (no false positive)."""
    def _fake_run(cmd, capture_output=True, text=True, encoding=None, timeout=None):
        return _MockResult(returncode=0, stdout=_SUCCESS_PAYLOAD)

    monkeypatch.setattr(dm.subprocess, "run", _fake_run)
    monkeypatch.setattr(dm.asyncio, "sleep", _no_sleep)

    data = await dm._dreamina_poll(
        "success0-0000-0000-0000-000000000000", max_wait=30
    )
    assert data is not None
    assert data["gen_status"] == "success"
    assert data["result_json"]["images"][0]["image_url"] == \
        "https://byteimg.com/ok.png"


@pytest.mark.asyncio
async def test_poll_querying_with_result_not_deadlock(monkeypatch):
    """querying WITH result_json (or queue not Finish) must NOT raise."""
    payload = json.dumps({
        "gen_status": "querying",
        "queue_info": {"queue_status": "Generated"},
        "result_json": {"images": [{"image_url": "https://x/y.png"}]},
    })

    def _fake_run(cmd, capture_output=True, text=True, encoding=None, timeout=None):
        return _MockResult(returncode=0, stdout=payload)

    monkeypatch.setattr(dm.subprocess, "run", _fake_run)
    monkeypatch.setattr(dm.asyncio, "sleep", _no_sleep)

    # One loop iteration (max_wait=6 with patched sleep) then clean timeout —
    # no deadlock raise despite gen_status=querying.
    result = await dm._dreamina_poll(
        "stillgen-0000-0000-0000-000000000000", max_wait=6
    )
    assert result is None


# ---------------------------------------------------------------------------
# gen_image template: poll_until_done + download hardening
# ---------------------------------------------------------------------------


def test_template_poll_deadlock_returns_none(monkeypatch):
    """Template poll_until_done: deadlock fingerprint → None (fast bail)."""
    mod = _load_template()

    def _fake_run_cmd(cmd, timeout=30):
        return (0, _DEADLOCK_PAYLOAD)

    monkeypatch.setattr(mod, "run_cmd", _fake_run_cmd)
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)

    result = mod.poll_until_done(
        "aaaaaaaa-0000-0000-0000-000000000000", max_wait=30
    )
    assert result is None


def test_template_poll_success_returns_data(monkeypatch):
    """Template poll_until_done: success payload passes through untouched."""
    mod = _load_template()

    def _fake_run_cmd(cmd, timeout=30):
        return (0, _SUCCESS_PAYLOAD)

    monkeypatch.setattr(mod, "run_cmd", _fake_run_cmd)
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)

    result = mod.poll_until_done(
        "bbbbbbbb-0000-0000-0000-000000000000", max_wait=30
    )
    assert result is not None
    assert result["gen_status"] == "success"


def test_template_download_uses_curl_first(monkeypatch, tmp_path):
    """download() prefers curl; aria2c is only a fallback (not called here)."""
    mod = _load_template()
    calls: list[list[str]] = []

    def _fake_run_cmd(cmd, timeout=30):
        calls.append(cmd)
        if cmd[0] == "curl":
            Path(cmd[cmd.index("-o") + 1]).write_bytes(b"\x89PNG\r\n\x1a\n")
        return (0, "")

    monkeypatch.setattr(mod, "run_cmd", _fake_run_cmd)

    out = tmp_path / "x.png"
    ok = mod.download({"_url": "https://byteimg.com/x.png"}, str(out))

    assert ok is True
    assert calls[0][0] == "curl"
    # curl succeeded → aria2c fallback never invoked.
    assert len(calls) == 1


def test_template_download_falls_back_to_aria2c(monkeypatch, tmp_path):
    """curl unavailable/failed → aria2c fallback still downloads."""
    mod = _load_template()
    calls: list[list[str]] = []

    def _fake_run_cmd(cmd, timeout=30):
        calls.append(cmd)
        if cmd[0] == "aria2c":
            # aria2c takes -d <dir> -o <basename>.
            d = Path(cmd[cmd.index("-d") + 1])
            (d / cmd[cmd.index("-o") + 1]).write_bytes(b"\x89PNG\r\n\x1a\n")
        return (1, "")

    monkeypatch.setattr(mod, "run_cmd", _fake_run_cmd)

    out = tmp_path / "y.png"
    ok = mod.download({"_url": "https://byteimg.com/y.png"}, str(out))

    assert ok is True
    assert calls[0][0] == "curl"
    assert calls[1][0] == "aria2c"


# ---------------------------------------------------------------------------
# FIX-4: i2i deadlock rescue — one-shot 5.x → 4.6 downgrade
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_i2i_deadlock_rescue_downgrades_to_4_6(monkeypatch, tmp_path):
    """5.x i2i deadlock → single retry with 4.6 → ok + model_fallback marker.

    Attempts 0+1 (t2i) fail vision-verify so attempt 2 switches to the
    image2image fallback with the batch model 5.0; its poll raises the
    deadlock RuntimeError, the rescue downgrades to 4.6 once, and the
    retried image passes vision-verify.
    """
    i2i_models: list[str] = []

    async def _fake_submit(prompt, ratio, model_version):
        return "t2i00000-0000-0000-0000-000000000000"

    async def _fake_image2image(ref_image_path, prompt, ratio, model_version):
        i2i_models.append(model_version)
        return f"i2i{len(i2i_models):04d}-0000-0000-0000-000000000000"

    async def _fake_poll(submit_id, max_wait=180):
        if submit_id.startswith("i2i0001"):
            raise RuntimeError(
                "dreamina deadlock: queue=Finish without result_json"
            )
        return {
            "gen_status": "success",
            "result_json": {"images": [{"image_url": "https://x/y.png"}]},
        }

    verify_calls = {"count": 0}

    async def _fail_fail_pass_verify(image_path, expected_content,
                                     directional_check=None, stratum=None):
        verify_calls["count"] += 1
        if verify_calls["count"] < 3:
            return {"pass": False, "confidence": 0.3,
                    "description": "RHD", "cached": False}
        return {"pass": True, "confidence": 0.95,
                "description": "LHD ok", "cached": False}

    async def _fake_download(url, output_path):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"\x89PNG\r\n\x1a\n")

    import plugins.kais_aigc.vision_verify as vv
    monkeypatch.setattr(vv, "verify_image_content", _fail_fail_pass_verify)
    monkeypatch.setattr(dm, "_dreamina_submit", _fake_submit)
    monkeypatch.setattr(dm, "_dreamina_image2image", _fake_image2image)
    monkeypatch.setattr(dm, "_dreamina_poll", _fake_poll)
    monkeypatch.setattr(dm, "_download", _fake_download)
    # Speed up tenacity wait.
    monkeypatch.setattr(dm, "wait_exponential", lambda **kw: (lambda *a, **k: 0))

    item = {
        "id": "S_dlock",
        "prompt": "car interior scene",
        "expected": "driver in car",
        "directional": "lhd",
        "lhd_reference_path": "/fake/lhd_ref.png",
    }
    results = await batch_submit([item], str(tmp_path), deadline_sec=30)

    assert len(results) == 1
    assert results[0]["status"] == "ok"
    # Exactly one downgrade: first i2i on 5.0 (deadlock), retry on 4.6.
    assert i2i_models == ["5.0", "4.6"]
    assert results[0]["model_fallback"] == "5.0->4.6"
