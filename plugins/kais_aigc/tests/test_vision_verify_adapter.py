"""test_vision_verify_adapter.py — engine adapter registry tests.

2026-08-27 (fixbatch-004): vision_verify grew an engine ADAPTER REGISTRY
(local qwen-eye / hosted glm-5.3-flash arms).
2026-08-27 (fixbatch-007, Kai 终审): the DEFAULT flipped to
``["glm-5.3-flash"]`` — hosted wins outright; qwen-eye stays a KNOWN
engine for explicit config/per-call opt-in only.

  - A configured multi-arm order falls through arm-by-arm when an arm
    produces no result; when ALL configured arms fail, the fail-closed
    ``VisionEngineUnavailable`` semantics are unchanged.
  - The hosted arm talks to Zhipu's v4 OpenAI-compatible endpoint with
    stdlib urllib. These tests NEVER touch the network: ``_urlopen`` /
    ``_resolve_zhipu_api_key`` / ``_verify_via_zhipu`` are patched (the
    late-bound name registry makes those patches effective).

Companion to test_vision_verify.py (qwen-eye-arm hard-gate coverage,
pinned to explicit orders) and to the observe_image_content tests here.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

import plugins.kais_aigc.vision_verify as vv
from plugins.kais_aigc.vision_verify import (
    VisionEngineUnavailable,
    _cache,
)


# ---------------------------------------------------------------------------
# Isolation: never let a test reach qwen-eye OR the open.bigmodel.cn endpoint
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """Fresh registry state per test + kill every machine-wide credential
    source so an unnoticed code path can't slip past the per-test patches
    into a real HTTP call (this box carries live ZHIPU_* provider vars in
    its launcher environment)."""
    monkeypatch.setattr(vv, "_engine_order_cache", None)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: None)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_VISION_API_KEY", raising=False)
    _cache.clear()
    yield
    _cache.clear()


def _make_png(path) -> None:
    """Minimal valid 1x1 PNG (same recipe as test_vision_verify.py)."""
    import struct
    import zlib

    raw_data = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw_data)

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", compressed)
    png += _chunk(b"IEND", b"")
    path.write_bytes(png)


class _UnhealthyEye:
    """Fake QwenEye that never becomes healthy (local arm fails at engine
    level → VEU raised by _verify_via_qwen_eye → treated as no-result by
    the router and a fall-through to the next configured arm happens)."""

    def __init__(self):
        self.observe_calls = 0

    def ensure_ready(self, timeout_s: int = 120):
        return (False, False)

    def observe_single(self, path, question, max_tokens=2000):  # pragma: no cover
        self.observe_calls += 1
        raise AssertionError("observe_single must not run when unhealthy")

    def stop_if_owned(self):
        pass


class _FakeHTTPResponse:
    def __init__(self, status: int = 200, body: bytes = b""):
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _hosted_response(content: str, reasoning: str = "", prompt_tokens=123,
                     completion_tokens=45) -> bytes:
    """A constructed chat/completions body — INCLUDING the thinking-model
    ``reasoning_content`` noise field that the parser must ignore."""
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if reasoning:
        message["reasoning_content"] = reasoning
    return json.dumps({
        "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens,
                  "completion_tokens": completion_tokens},
    }).encode("utf-8")


def _install_urlopen(monkeypatch, *, response: _FakeHTTPResponse | None = None,
                     exc: Exception | None = None):
    """Swap ``vv._urlopen`` for a recorder. Returns (requests, responses)."""
    requests_seen: list[Any] = []

    def fake_urlopen(request, timeout=None):
        requests_seen.append({"request": request, "timeout": timeout})
        if exc is not None:
            raise exc
        assert response is not None
        return response

    monkeypatch.setattr(vv, "_urlopen", fake_urlopen)
    return requests_seen


_REAL_RESOLVER = vv._resolve_zhipu_api_key
"""Import-time capture of the true key resolver — the autouse fixture
patches ``vv._resolve_zhipu_api_key`` to a no-op for network safety; these
tests re-install the real one under that same patch umbrella."""


# ---------------------------------------------------------------------------
# Registry shape: default order unchanged, both arms known, tables 1:1
# ---------------------------------------------------------------------------


def test_default_order_flipped_and_both_arms_known():
    """fixbatch-007: hosted glm-5.3-flash is THE default; both arms stay
    known across all three dispatch tables (single/batch/observe)."""
    assert vv._ENGINE_ORDER_DEFAULT == ["glm-5.3-flash"]
    assert set(vv._KNOWN_ENGINES) == {"qwen-eye", "glm-5.3-flash"}
    # Registry covers every known engine by NAME (late-bound), single-image
    # AND batch tables in 1:1 correspondence — plus the observe twin table.
    assert set(vv._ENGINE_ARMS) == set(vv._KNOWN_ENGINES)
    assert set(vv._ENGINE_BATCH_ARMS) == set(vv._KNOWN_ENGINES)
    assert set(vv._OBSERVE_ARMS) == set(vv._KNOWN_ENGINES)


def test_get_engine_order_defaults_without_config(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    assert vv.get_engine_order() == ["glm-5.3-flash"]


def test_config_order_unknown_names_dropped(monkeypatch, tmp_path):
    """Partially-known config keeps only the known names, IN ORDER."""
    (tmp_path / "config.yaml").write_text(
        "vision_verify:\n  engines: [\"qwen-typo\", \"glm-5.3-flash\", \"qwen-eye\"]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    assert vv.get_engine_order() == ["glm-5.3-flash", "qwen-eye"]


def test_config_order_all_unknown_falls_back_to_default(monkeypatch, tmp_path):
    (tmp_path / "config.yaml").write_text(
        "vision_verify:\n  engines: [\"midjourney-vision\", \"glm-4.6v\"]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    # glm-4.6v is retired — an all-unknown config (including it) falls
    # back to the fixbatch-007 default.
    assert vv.get_engine_order() == ["glm-5.3-flash"]


def test_config_order_qwen_eye_is_explicit_opt_in(monkeypatch, tmp_path):
    """qwen-eye stays KNOWN: a config naming ONLY the local arm runs the
    local arm exactly as pre-flip deployments did."""
    (tmp_path / "config.yaml").write_text(
        "vision_verify:\n  engines: [\"qwen-eye\"]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    assert vv.get_engine_order() == ["qwen-eye"]


# ---------------------------------------------------------------------------
# Two-arm traversal (single image): local miss → hosted verdict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_local_arm_none_falls_through_to_hosted(monkeypatch, tmp_path):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())

    hosted_calls: list[Any] = []

    def fake_hosted(p, expected_content, directional_check, threshold):
        hosted_calls.append((p, expected_content, directional_check, threshold))
        return {"pass": True, "confidence": 0.88, "description": "hosted says yes",
                "usage": {"input_tokens": 7, "output_tokens": 9}}

    monkeypatch.setattr(vv, "_verify_via_zhipu", fake_hosted)

    result = await vv.verify_image_content(
        str(img), "a baby in a car seat",
        engine_order=["qwen-eye", "glm-5.3-flash"],
    )

    assert result["pass"] is True
    assert result["engine"] == "glm-5.3-flash"  # entry names the ACTUAL judge
    assert hosted_calls and hosted_calls[0][1] == "a baby in a car seat"


@pytest.mark.asyncio
async def test_cached_hit_keeps_producing_engine(monkeypatch, tmp_path):
    """The cached entry carries the engine that produced it, on hit too."""
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())
    monkeypatch.setattr(
        vv, "_verify_via_zhipu",
        lambda p, e, d, t: {
            "pass": True, "confidence": 0.9, "description": "ok",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    )

    first = await vv.verify_image_content(
        str(img), "content", engine_order=["qwen-eye", "glm-5.3-flash"]
    )
    assert first["engine"] == "glm-5.3-flash"
    second = await vv.verify_image_content(
        str(img), "content", engine_order=["qwen-eye", "glm-5.3-flash"]
    )
    assert second["cached"] is True
    assert second["engine"] == "glm-5.3-flash"


@pytest.mark.asyncio
async def test_all_arms_unavailable_fails_closed_with_current_type(
    monkeypatch, tmp_path,
):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())
    monkeypatch.setattr(vv, "_verify_via_zhipu", lambda *a: None)

    with pytest.raises(VisionEngineUnavailable):
        await vv.verify_image_content(
            str(img), "content", engine_order=["qwen-eye", "glm-5.3-flash"]
        )


# ---------------------------------------------------------------------------
# Hosted arm, pure unit tests (network fully faked)
# ---------------------------------------------------------------------------

_HOSTED_ORDER = ["glm-5.3-flash"]


@pytest.mark.asyncio
async def test_hosted_happy_path_parses_content_ignoring_reasoning(
    monkeypatch, tmp_path,
):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "test-key-123")
    seen = _install_urlopen(
        monkeypatch,
        response=_FakeHTTPResponse(
            status=200,
            body=_hosted_response(
                content="是，图中包含婴儿座椅。置信度0.87",
                # Decoy confidence in the ignored thinking channel:
                reasoning="让我想想……置信度0.11？不，再看看……",
            ),
        ),
    )

    result = await vv.verify_image_content(str(img), "content",
                                           engine_order=_HOSTED_ORDER)

    assert result["pass"] is True
    assert result["confidence"] == 0.87  # parsed from content, NOT reasoning
    assert result["engine"] == "glm-5.3-flash"

    req = seen[0]["request"]
    assert req.full_url == vv._ZHIPU_VISION_ENDPOINT
    assert seen[0]["timeout"] >= 120  # slow base64 uploads — mandated budget
    headers = {k.lower(): v for k, v in req.headers.items()}
    assert headers["authorization"] == "Bearer test-key-123"
    payload = json.loads(req.data.decode("utf-8"))
    assert payload["model"] == "glm-5.3-flash"
    assert payload["model"] == vv._ZHIPU_VISION_MODEL
    (msg,) = payload["messages"]
    types = [part["type"] for part in msg["content"]]
    assert types == ["image_url", "text"]
    assert msg["content"][0]["image_url"]["url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_hosted_metered_usage_reported(monkeypatch, tmp_path):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")
    _install_urlopen(
        monkeypatch,
        response=_FakeHTTPResponse(
            status=200,
            body=_hosted_response(content="否，置信度0.2",
                                  prompt_tokens=500, completion_tokens=60),
        ),
    )
    result = await vv.verify_image_content(str(img), "content",
                                           engine_order=_HOSTED_ORDER)
    assert result["pass"] is False
    assert result["usage"] == {"input_tokens": 500, "output_tokens": 60}


@pytest.mark.asyncio
async def test_hosted_network_exception_returns_none_then_fail_closed(
    monkeypatch, tmp_path,
):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")
    _install_urlopen(monkeypatch, exc=TimeoutError("simulated socket timeout"))

    # Arm contract: ANY network failure → None (never raises).
    assert vv._verify_via_zhipu(
        img, "content", None, vv._CONFIDENCE_THRESHOLD
    ) is None

    # Sole configured arm → the original fail-closed type surfaces.
    with pytest.raises(VisionEngineUnavailable):
        await vv.verify_image_content(str(img), "content",
                                      engine_order=_HOSTED_ORDER)


def test_hosted_non_200_returns_none(monkeypatch, tmp_path):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")
    _install_urlopen(
        monkeypatch, response=_FakeHTTPResponse(status=503, body=b"boom")
    )
    # _verify_via_zhipu directly (sync): None means "no result" for the router.
    assert vv._verify_via_zhipu(
        img, "content", None, vv._CONFIDENCE_THRESHOLD
    ) is None


def test_hosted_empty_or_malformed_content_returns_none(monkeypatch, tmp_path):
    img = tmp_path / "img.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")

    # Empty content string → None.
    _install_urlopen(monkeypatch,
                     response=_FakeHTTPResponse(body=_hosted_response(content="   ")))
    assert vv._verify_via_zhipu(img, "content", None, 0.7) is None

    # Malformed body (no choices) → None, never raises.
    _install_urlopen(monkeypatch,
                     response=_FakeHTTPResponse(body=b'{"error": {"code": "x"}}'))
    assert vv._verify_via_zhipu(img, "content", None, 0.7) is None


@pytest.mark.asyncio
async def test_hosted_without_api_key_skips_network(monkeypatch, tmp_path):
    """No env key AND no settings.json token under an empty HOME → the arm
    reports unavailable WITHOUT any network attempt."""
    img = tmp_path / "img.png"
    _make_png(img)
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: empty_home)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", _REAL_RESOLVER)
    seen = _install_urlopen(
        monkeypatch, response=_FakeHTTPResponse(body=b"{}"),
    )

    assert vv._resolve_zhipu_api_key() is None  # real resolver, empty home
    with pytest.raises(VisionEngineUnavailable):
        await vv.verify_image_content(str(img), "content",
                                      engine_order=_HOSTED_ORDER)
    assert seen == []  # zero network attempts


# ---------------------------------------------------------------------------
# API key resolution order (three sources, one shared key)
# ---------------------------------------------------------------------------


def _write_settings_home(home, token):
    glm_dir = home / ".claude-glm"
    glm_dir.mkdir(parents=True)
    (glm_dir / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_AUTH_TOKEN": token}}), encoding="utf-8",
    )


def test_key_resolution_zhipu_api_key_wins_over_everything(monkeypatch, tmp_path):
    """Source 1: plain ``ZHIPU_API_KEY`` beats the vision pin AND the
    launcher settings token (all three hold the same key on a standard
    deployment, but the first-listed var wins deterministically)."""
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", _REAL_RESOLVER)
    monkeypatch.setenv("ZHIPU_API_KEY", "  plain-key  ")
    monkeypatch.setenv("ZHIPU_VISION_API_KEY", "vision-key")
    _write_settings_home(tmp_path, "settings-key")
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    assert vv._resolve_zhipu_api_key() == "plain-key"  # winner, stripped


def test_key_resolution_vision_var_when_plain_absent(monkeypatch, tmp_path):
    """Source 2: ``ZHIPU_VISION_API_KEY`` applies once ``ZHIPU_API_KEY``
    is unset — an explicit vision-only operator pin."""
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", _REAL_RESOLVER)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.setenv("ZHIPU_VISION_API_KEY", "vision-key")
    _write_settings_home(tmp_path, "settings-key")
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    assert vv._resolve_zhipu_api_key() == "vision-key"


def test_key_resolution_falls_back_to_settings_json(monkeypatch, tmp_path):
    """Source 3: the Claude Code launcher credentials at
    ``~/.claude-glm/settings.json`` ``env.ANTHROPIC_AUTH_TOKEN`` (same
    Zhipu-issued token the GLM proxy channel uses)."""
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", _REAL_RESOLVER)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_VISION_API_KEY", raising=False)
    _write_settings_home(tmp_path, "settings-key")
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    assert vv._resolve_zhipu_api_key() == "settings-key"


def test_key_resolution_none_when_neither_source_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", _REAL_RESOLVER)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_VISION_API_KEY", raising=False)
    empty = tmp_path / "nothing-here"
    empty.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: empty)
    # A malformed settings.json must not raise — just resolve to None.
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / ".claude-glm").mkdir()
    (bad / ".claude-glm" / "settings.json").write_text("{not json", encoding="utf-8")

    monkeypatch.setattr("pathlib.Path.home", lambda: empty)
    assert vv._resolve_zhipu_api_key() is None
    monkeypatch.setattr("pathlib.Path.home", lambda: bad)
    assert vv._resolve_zhipu_api_key() is None


# ---------------------------------------------------------------------------
# Batch traversal
# ---------------------------------------------------------------------------


def _three_pngs(tmp_path, prefix="b"):
    paths = []
    for i in range(3):
        p = tmp_path / f"{prefix}_{i}.png"
        _make_png(p)
        paths.append(str(p))
    return paths


@pytest.mark.asyncio
async def test_batch_default_order_hosted_down_yields_error_rows(
    monkeypatch, tmp_path,
):
    """fixbatch-007 regression guard: with the DEFAULT hosted-only order
    (real get_engine_order against a configless home), hosted per-image
    failures land as ``engine_error`` rows — never silently-pass verdicts.
    (Batch contract: raise is reserved for ENGINE-level local-arm failures;
    the hosted batch arm isolates per-image misses.)"""
    paths = _three_pngs(tmp_path)
    empty_home = tmp_path / "configless-home"
    empty_home.mkdir()
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(empty_home),
    )
    monkeypatch.setattr(vv, "_new_qwen_eye",
                        lambda: _UnhealthyEye())
    monkeypatch.setattr(vv, "_verify_via_zhipu", lambda *a: None)

    results = await vv.verify_batch(paths, ["content"] * 3)
    assert len(results) == 3
    for r in results:
        assert r["pass"] is False
        assert r["engine_error"] is True
        assert r["engine"] == "glm-5.3-flash"
        assert r["cached"] is False


@pytest.mark.asyncio
async def test_batch_default_order_pinned_local_still_raises(monkeypatch, tmp_path):
    """Explicit qwen-eye-only order keeps the pre-flip fail-closed shape:
    local engine-level failure raises rather than producing rows."""
    paths = _three_pngs(tmp_path)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())
    monkeypatch.setattr(vv, "_verify_via_zhipu",
                        lambda *a: pytest.fail("hosted arm must not run"))

    with pytest.raises(VisionEngineUnavailable):
        await vv.verify_batch(paths, ["content"] * 3,
                              engine_order=["qwen-eye"])


@pytest.mark.asyncio
async def test_batch_local_engine_down_falls_through_to_hosted(
    monkeypatch, tmp_path,
):
    paths = _three_pngs(tmp_path)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())

    hosted_seen: list[str] = []

    def fake_hosted(p, expected_content, directional_check, threshold):
        hosted_seen.append(str(p))
        return {"pass": True, "confidence": 0.91,
                "description": f"hosted judged {p.name}",
                "usage": {"input_tokens": 10, "output_tokens": 5}}

    monkeypatch.setattr(vv, "_verify_via_zhipu", fake_hosted)

    results = await vv.verify_batch(
        paths, ["content"] * 3, engine_order=["qwen-eye", "glm-5.3-flash"],
    )

    assert sorted(hosted_seen) == sorted(paths)  # whole batch re-homed
    assert len(results) == 3
    for r in results:
        assert r["pass"] is True
        assert r["engine"] == "glm-5.3-flash"
        assert r["cached"] is False


@pytest.mark.asyncio
async def test_batch_hosted_per_image_failure_isolated(monkeypatch, tmp_path):
    """One hosted HTTP miss → engine_error row; siblings still judged."""
    paths = _three_pngs(tmp_path)

    def flaky_hosted(p, expected_content, directional_check, threshold):
        if str(p) == paths[1]:
            return None  # simulated per-image failure
        return {"pass": True, "confidence": 0.85, "description": "ok",
                "usage": {"input_tokens": 1, "output_tokens": 1}}

    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())
    monkeypatch.setattr(vv, "_verify_via_zhipu", flaky_hosted)

    results = await vv.verify_batch(
        paths, ["content"] * 3, engine_order=["qwen-eye", "glm-5.3-flash"],
    )

    assert results[0]["pass"] is True and results[0]["engine"] == "glm-5.3-flash"
    assert results[1]["engine_error"] is True
    assert results[1]["engine"] == "glm-5.3-flash"
    assert results[2]["pass"] is True


# ---------------------------------------------------------------------------
# observe_image_content (fixbatch-007): observation-layer twin — network
# fully faked via the same _install_urlopen手法 as the verify arm tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_observe_happy_path_hosted(monkeypatch, tmp_path):
    """Free-text question in verbatim; content returned unparsed with real
    metered usage and the engine that answered."""
    img = tmp_path / "obs.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "test-key")
    seen = _install_urlopen(
        monkeypatch,
        response=_FakeHTTPResponse(
            status=200,
            body=_hosted_response(content="开阔的沙漠绿洲，黄昏暖光。",
                                  reasoning="先看看构图……置信度0.11？（无关噪声）",
                                  prompt_tokens=321, completion_tokens=45),
        ),
    )

    result = await vv.observe_image_content(
        str(img), "用1-2句话客观描述这张场景图",
    )

    assert result == {
        "text": "开阔的沙漠绿洲，黄昏暖光。",
        "engine": "glm-5.3-flash",
        "cached": False,
        "usage": {"input_tokens": 321, "output_tokens": 45},
    }
    # Question rides the request VERBATIM (no yes/no template injected).
    payload = json.loads(seen[0]["request"].data.decode("utf-8"))
    (msg,) = payload["messages"]
    texts = [part["text"] for part in msg["content"] if part["type"] == "text"]
    assert texts == ["用1-2句话客观描述这张场景图"]
    assert msg["content"][0]["image_url"]["url"].startswith("data:image/png;base64,")
    headers = {k.lower(): v for k, v in seen[0]["request"].headers.items()}
    assert headers["authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_observe_ignores_reasoning_channel(monkeypatch, tmp_path):
    """Only ``message.content`` is surfaced; reasoning_content never leaks."""
    img = tmp_path / "r.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")
    _install_urlopen(
        monkeypatch,
        response=_FakeHTTPResponse(body=_hosted_response(content="第一句话。"))
    )
    result = await vv.observe_image_content(str(img), "q?")
    assert result["text"] == "第一句话。"


@pytest.mark.asyncio
async def test_observe_local_arm_wrapper(monkeypatch, tmp_path):
    """Explicit qwen-eye order → QwenEye.observe_single wrapper, usage 0/0."""
    img = tmp_path / "local.png"
    _make_png(img)

    class _Eye:
        def __init__(self):
            self.calls = []
            self.stopped = 0

        def ensure_ready(self, timeout_s=120):
            return True, False

        def observe_single(self, path, question, max_tokens=2000):
            self.calls.append((str(path), question))
            return "画面里有一只橘猫。"

        def stop_if_owned(self):
            self.stopped += 1

    eye = _Eye()
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: eye)
    result = await vv.observe_image_content(str(img), "描述图片",
                                            engine_order=["qwen-eye"])
    assert result["text"] == "画面里有一只橘猫。"
    assert result["engine"] == "qwen-eye"
    assert result["usage"] == {"input_tokens": 0, "output_tokens": 0}
    assert eye.stopped == 1  # lease hygiene mirrors the verify local arm


@pytest.mark.asyncio
async def test_observe_local_down_falls_through_to_hosted(monkeypatch, tmp_path):
    """Local arm raises VEU → hosted answers; entry names the executor."""
    img = tmp_path / "ft.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())
    monkeypatch.setattr(vv, "_observe_via_zhipu",
                        lambda p, q: {"text": "hosted 答案",
                                      "usage": {"input_tokens": 5,
                                                "output_tokens": 2}})
    result = await vv.observe_image_content(
        str(img), "q", engine_order=["qwen-eye", "glm-5.3-flash"])
    assert result["engine"] == "glm-5.3-flash"
    assert result["cached"] is False
    assert result["text"] == "hosted 答案"


@pytest.mark.asyncio
async def test_observe_all_arms_fail_fails_closed(monkeypatch, tmp_path):
    """Hosted None + local raise, no further arm → VisionEngineUnavailable."""
    img = tmp_path / "down.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())
    monkeypatch.setattr(vv, "_observe_via_zhipu", lambda *a: None)

    with pytest.raises(VisionEngineUnavailable):
        await vv.observe_image_content(
            str(img), "q", engine_order=["glm-5.3-flash", "qwen-eye"])


@pytest.mark.asyncio
async def test_observe_empty_text_is_engine_failure(monkeypatch, tmp_path):
    """Empty hosted content → treated as no-answer (fall-through /
    fail-closed), never an empty-text success."""
    img = tmp_path / "empty.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")
    _install_urlopen(
        monkeypatch,
        response=_FakeHTTPResponse(body=_hosted_response(content="   ")),
    )
    with pytest.raises(VisionEngineUnavailable):
        await vv.observe_image_content(str(img), "q")


@pytest.mark.asyncio
async def test_observe_cache_hit_reports_engine_and_zero_usage(monkeypatch, tmp_path):
    """Second identical ask hits the three-part key: cached=True, same
    engine echoed back, usage zeroed."""
    img = tmp_path / "c.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", lambda: "k")

    calls = {"n": 0}

    def counting_urlopen(request, timeout=None):
        calls["n"] += 1

        class _Resp(_FakeHTTPResponse):
            pass

        return _FakeHTTPResponse(status=200,
                                 body=_hosted_response(content=f"答案{calls['n']}"))

    monkeypatch.setattr(vv, "_urlopen", counting_urlopen)

    r1 = await vv.observe_image_content(str(img), "同一问题")
    assert r1["cached"] is False
    r2 = await vv.observe_image_content(str(img), "同一问题")
    assert r2["cached"] is True
    assert r2["engine"] == r1["engine"] == "glm-5.3-flash"
    assert r2["text"] == r1["text"]  # served from cache, not re-judged
    assert r2["usage"] == {"input_tokens": 0, "output_tokens": 0}
    assert calls["n"] == 1  # exactly one network call total


@pytest.mark.asyncio
async def test_observe_and_verify_do_not_cross_serve_cache(monkeypatch, tmp_path):
    """A verify-format question asked via observe gets a fresh judgement:
    shape guards stop verify's {pass,...} entries serving observation (and
    vice versa)."""
    img = tmp_path / "x.png"
    _make_png(img)
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: _UnhealthyEye())

    question = vv._build_question("内容", None)  # the EXACT verify text

    def fake_verify(p, expected_content, directional_check, threshold):
        return {"pass": True, "confidence": 0.99, "description": "是",
                "usage": {"input_tokens": 9, "output_tokens": 9}}

    monkeypatch.setattr(vv, "_verify_via_zhipu", fake_verify)

    # Prime the cache through verify.
    v = await vv.verify_image_content(str(img), "内容",
                                      engine_order=["glm-5.3-flash"])
    assert v["cached"] is False

    # Same image, SAME question text through observe — must NOT inherit
    # the verdict entry; observes freshly (hosted call faked to answer).
    observe_calls: list[str] = []

    def fake_observe(p, q):
        observe_calls.append(q)
        return {"text": "自由文本答案",
                "usage": {"input_tokens": 1, "output_tokens": 1}}

    monkeypatch.setattr(vv, "_observe_via_zhipu", fake_observe)
    o = await vv.observe_image_content(str(img), question,
                                       engine_order=["glm-5.3-flash"])
    assert o["cached"] is False
    assert "pass" not in o  # verdict dict was not served as an observation

    # And the reverse: the observe entry doesn't serve a verify call —
    # verify re-judges rather than returning a {text}-shaped dict.
    monkeypatch.setattr(vv, "_verify_via_zhipu", fake_verify)
    v2 = await vv.verify_image_content(str(img), "内容",
                                       engine_order=["glm-5.3-flash"])
    assert v2["cached"] is True or "confidence" in v2  # always verdict-shaped
    assert "text" not in v2


def test_observe_without_key_makes_no_network_call(monkeypatch, tmp_path):
    """No key under an empty HOME → fail-closed BEFORE any HTTP attempt."""
    import asyncio

    img = tmp_path / "nk.png"
    _make_png(img)
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: empty_home)
    monkeypatch.setattr(vv, "_resolve_zhipu_api_key", _REAL_RESOLVER)
    seen = _install_urlopen(monkeypatch,
                            response=_FakeHTTPResponse(body=b"{}"))

    with pytest.raises(VisionEngineUnavailable):
        asyncio.run(vv.observe_image_content(str(img), "q"))
    assert seen == []  # zero network attempts
