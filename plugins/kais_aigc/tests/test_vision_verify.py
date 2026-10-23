"""test_vision_verify.py — IMG-03 vision-verify gate.

2026-08-18 冗余审核体系 (user directive: 不要降级): the GLM-4.6V fallback
was REMOVED and the qwen-eye hard-gate semantics pinned here:

  - Engine-level failure (not ready / empty response / call exception)
    of the only arm in effect RAISES ``VisionEngineUnavailable`` —
    fail-closed, never skipped.
  - Content-level low confidence returns ``pass=False`` (unchanged).
  - An unresolvable ``engine_order`` pin fails closed (no arm ran).
  - verify_batch: per-image isolation with ``engine_error: True`` rows;
    engine-level failure raises.
  - sha256 cache + stratum thresholds (unchanged behaviors).

2026-08-27 (fixbatch-004): the seam widened into an engine ADAPTER
REGISTRY (local/hosted arms). 2026-08-27 (fixbatch-007, Kai 终审): the
DEFAULT flipped to ["glm-5.3-flash"]; this file's qwen-eye hard-gate
coverage pins EXPLICIT ``engine_order=["qwen-eye"]`` (or the module
fixture's explicit cache pin) so every assertion here still holds;
hosted-arm/fall-through/observe coverage lives in
test_vision_verify_adapter.py.

2026-08-27 (fixbatch-005): result-cache entries are keyed per
(sha, engine) — cross-engine isolation is pinned by
test_cache_isolated_per_engine (a bare-sha key served engine A's cached
verdict to engine-B calls for the whole 24h TTL).

2026-08-27 (fixbatch-006): the key also fingerprints the judging
question — cross-question isolation is pinned by
test_cache_isolated_per_question (an acceptance harness's negative
controls re-verifying the same image against another shot's spec
received the positive controls' cached echoes for the whole 24h TTL),
with test_cache_hit_same_question_regression guarding the dedup win and
test_batch_cache_isolated_per_question pinning the batch read/write
paths to the same three-part key.

The qwen-eye lifecycle is faked via the ``_new_qwen_eye`` seam — no real
KAP allocate / :8125 polling in unit tests (that has dedicated coverage in
test_qwen_eye.py).
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any

import pytest

import plugins.kais_aigc.vision_verify as vv
from plugins.kais_aigc.vision_verify import (
    VisionEngineUnavailable,
    _cache,
    _threshold_cache,
    get_threshold,
    verify_batch,
    verify_image_content,
)


# ---------------------------------------------------------------------------
# Engine-order isolation: pin to qwen-eye EXPLICITLY (fixbatch-007 made the
# default hosted) + cache resets
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _pin_qwen_engine(monkeypatch):
    # Explicit local-arm pin — NOT the post-flip default; keeps every
    # engineless-order call in this file judging through qwen-eye.
    monkeypatch.setattr(vv, "_engine_order_cache", ["qwen-eye"])
    _cache.clear()
    yield
    _cache.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_png(path: Path) -> None:
    """Write a minimal valid 1x1 PNG file to *path*."""
    width, height = 1, 1
    raw_data = b"\x00\xff\xff\xff"  # filter byte + white pixel
    compressed = zlib.compress(raw_data)

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", compressed)
    png += _chunk(b"IEND", b"")
    path.write_bytes(png)


class _FakeEye:
    """Fake QwenEye — records calls, returns scripted observe_single text.

    ``script`` maps image-path str → response text; ``default`` is used for
    unmapped paths. An Exception instance in place of text raises instead.
    ``observe_calls`` counts observe_single invocations; ``stopped`` records
    stop_if_owned() invocations.
    """

    def __init__(self, default: Any = "是，置信度0.92", script: dict | None = None,
                 healthy: bool = True):
        self.default = default
        self.script = script or {}
        self.healthy = healthy
        self.observe_calls = 0
        self.stopped = 0

    def ensure_ready(self, timeout_s: int = 120):
        return (self.healthy, False)

    def observe_single(self, path, question: str, max_tokens: int = 2000) -> str:
        self.observe_calls += 1
        val = self.script.get(str(path), self.default)
        if isinstance(val, Exception):
            raise val
        return val

    def stop_if_owned(self):
        self.stopped += 1


def _patch_eye(monkeypatch, eye: _FakeEye) -> _FakeEye:
    monkeypatch.setattr(vv, "_new_qwen_eye", lambda: eye)
    return eye


# ---------------------------------------------------------------------------
# Single-image verify: happy paths (converted from the GLM-era tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_high_confidence_passes(monkeypatch, tmp_path):
    img = tmp_path / "test.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.92"))

    result = await verify_image_content(str(img), "a baby in a car seat")

    assert result["pass"] is True
    assert result["confidence"] == 0.92
    assert result["engine"] == "qwen-eye"
    assert result["usage"] == {"input_tokens": 0, "output_tokens": 0}
    assert eye.observe_calls == 1
    assert eye.stopped == 1  # lease hygiene: stop after the call


@pytest.mark.asyncio
async def test_cache_hits(monkeypatch, tmp_path):
    """sha256 cache — second call with same image returns cached=True and
    does NOT re-invoke the engine."""
    img = tmp_path / "cached.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.92"))

    result1 = await verify_image_content(str(img), "test content")
    assert result1["cached"] is False
    assert eye.observe_calls == 1

    result2 = await verify_image_content(str(img), "test content")
    assert result2["cached"] is True
    assert eye.observe_calls == 1  # NOT called again
    assert result2["usage"] == {"input_tokens": 0, "output_tokens": 0}


@pytest.mark.asyncio
async def test_fresh_skips_cache_read_but_still_writes(monkeypatch, tmp_path):
    """fresh=True — multi-sample independence: the cache READ side is
    skipped (same image + same engine + same question would otherwise
    serve sample 1's verdict to samples 2..N, collapsing the anatomy
    checker's 3-sample majority vote to "1 ballot ×N"), while the WRITE
    side stays on so later non-fresh callers keep the identical-re-ask
    dedup win. fixbatch-005/006/007 govern which entries may SERVE a
    read — fresh merely opts this call out of reading."""
    img = tmp_path / "fresh.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.92"))

    r1 = await verify_image_content(str(img), "content", fresh=True)
    assert r1["cached"] is False
    assert r1["fresh"] is True  # 回显输入
    r2 = await verify_image_content(str(img), "content", fresh=True)
    assert r2["cached"] is False and r2["fresh"] is True
    assert eye.observe_calls == 2  # 第 2 采样不吃第 1 采样的缓存

    # 写缓存照常：后续普通（非 fresh）调用命中
    r3 = await verify_image_content(str(img), "content")
    assert r3["cached"] is True and r3["fresh"] is False
    assert eye.observe_calls == 2  # 无第 3 次引擎调用

    # 交叉隔离不破坏：fresh 写下的条目对 fixbatch-006 的同键普通读有效，
    # 但换问法（不同 question）仍不得互相服务
    r4 = await verify_image_content(str(img), "another question")
    assert r4["cached"] is False
    assert eye.observe_calls == 3


@pytest.mark.asyncio
async def test_fresh_false_is_zero_behavior_change(monkeypatch, tmp_path):
    """缺省 fresh=False：既有缓存行为逐位一致，返回 dict 仅新增
    "fresh": False 回显（缓存命中路径同样回显）。"""
    img = tmp_path / "plain.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.92"))

    r1 = await verify_image_content(str(img), "content")
    assert r1["cached"] is False and r1["fresh"] is False
    r2 = await verify_image_content(str(img), "content")
    assert r2["cached"] is True and r2["fresh"] is False
    assert eye.observe_calls == 1  # dedup 收益原样


@pytest.mark.asyncio
async def test_cache_isolated_per_engine(monkeypatch, tmp_path):
    """fixbatch-005: cache entries are keyed per (sha, engine) — a verdict
    cached by one engine must NOT be served to a call judging with the
    other. The bare-sha key cross-polluted verdicts across engine switches
    for the whole 24h TTL, violating fail-closed judgement semantics."""
    img = tmp_path / "engine_switch.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.92"))
    hosted_calls = {"n": 0}

    def fake_hosted(p, expected_content, directional_check, threshold):
        hosted_calls["n"] += 1
        return {"pass": False, "confidence": 0.3,
                "description": "hosted disagrees",
                "usage": {"input_tokens": 11, "output_tokens": 7}}

    monkeypatch.setattr(vv, "_verify_via_zhipu", fake_hosted)

    # qwen-eye judges first: fresh verdict, cached under the qwen-eye key.
    r1 = await verify_image_content(str(img), "content",
                                    engine_order=["qwen-eye"])
    assert r1["cached"] is False
    assert r1["engine"] == "qwen-eye"
    assert r1["confidence"] == 0.92 and r1["pass"] is True

    # Same image through glm-5.3-flash: must NOT hit qwen-eye's entry —
    # fresh hosted judgement carrying the hosted arm's own numbers.
    r2 = await verify_image_content(str(img), "content",
                                    engine_order=["glm-5.3-flash"])
    assert r2["cached"] is False
    assert r2["engine"] == "glm-5.3-flash"
    assert r2["confidence"] == 0.3 and r2["pass"] is False
    assert r2["usage"] == {"input_tokens": 11, "output_tokens": 7}
    assert hosted_calls["n"] == 1

    # Reverse direction: clear cache, hosted judges first, then qwen-eye
    # must re-judge fresh (not inherit the hosted verdict).
    _cache.clear()
    r3 = await verify_image_content(str(img), "content",
                                    engine_order=["glm-5.3-flash"])
    assert r3["cached"] is False and r3["engine"] == "glm-5.3-flash"
    r4 = await verify_image_content(str(img), "content",
                                    engine_order=["qwen-eye"])
    assert r4["cached"] is False
    assert r4["engine"] == "qwen-eye"
    assert r4["confidence"] == 0.92
    assert eye.observe_calls == 2  # r1 + r4 both really ran the local arm

    # Same-engine repeat still hits the cache (regression guard for the
    # isolation change — the dedup win itself must not regress).
    r5 = await verify_image_content(str(img), "content",
                                    engine_order=["qwen-eye"])
    assert r5["cached"] is True
    assert r5["engine"] == "qwen-eye"
    assert r5["usage"] == {"input_tokens": 0, "output_tokens": 0}
    assert eye.observe_calls == 2
    assert hosted_calls["n"] == 2


@pytest.mark.asyncio
async def test_cache_isolated_per_question(monkeypatch, tmp_path):
    """fixbatch-006: the cache key carries the judging-question dimension
    — same image + same engine + DIFFERENT question must re-judge instead
    of echoing the first verdict for the whole 24h TTL (the acceptance-
    harness trap: negative controls re-verifying the same image against
    another shot's spec received the positive controls' cached echoes)."""
    img = tmp_path / "per_question.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.92"))

    # Question A judged fresh.
    r1 = await verify_image_content(str(img), "镜头spec甲：主角坐在驾驶位")
    assert r1["cached"] is False
    assert eye.observe_calls == 1

    # Same image, different expected_content → different question →
    # independent judgement, NOT the entry cached for question A.
    r2 = await verify_image_content(str(img), "镜头spec乙：主角站在车外")
    assert r2["cached"] is False
    assert eye.observe_calls == 2

    # directional_check alone changing the question re-judges too (the
    # "lhd" suffix extends the text actually sent to the engine).
    r3 = await verify_image_content(str(img), "镜头spec乙：主角站在车外",
                                    directional_check="lhd")
    assert r3["cached"] is False
    assert eye.observe_calls == 3

    # Each distinct question now owns its entry: repeating question A
    # hits A's cache without touching the engine again.
    r4 = await verify_image_content(str(img), "镜头spec甲：主角坐在驾驶位")
    assert r4["cached"] is True
    assert eye.observe_calls == 3


@pytest.mark.asyncio
async def test_cache_hit_same_question_regression(monkeypatch, tmp_path):
    """Identical (image, engine, expected_content, directional_check) on
    the second call still hits the cache — the dedup win must survive the
    key widening (extends test_cache_hits with a directional_check
    present, pinning the new three-part key shape)."""
    img = tmp_path / "same_question.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.95，左舵LHD"))

    r1 = await verify_image_content(str(img), "city street at dusk",
                                    directional_check="lhd")
    assert r1["cached"] is False
    r2 = await verify_image_content(str(img), "city street at dusk",
                                    directional_check="lhd")
    assert r2["cached"] is True
    assert eye.observe_calls == 1  # NOT called again
    assert r2["usage"] == {"input_tokens": 0, "output_tokens": 0}


@pytest.mark.asyncio
async def test_batch_cache_isolated_per_question(monkeypatch, tmp_path):
    """Batch read/write paths compose the SAME three-part key as the
    single-image path: a single-path entry for question A is served to a
    batch row repeating question A, while a batch row asking question B
    over the same image re-judges (no old-key-shape mixing)."""
    img = tmp_path / "batch_q.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.9"))

    r_single = await verify_image_content(str(img), "spec A")
    assert r_single["cached"] is False
    assert eye.observe_calls == 1

    (r_b,) = await verify_batch([str(img)], ["spec B"])
    assert r_b["cached"] is False
    assert eye.observe_calls == 2

    (r_a,) = await verify_batch([str(img)], ["spec A"])
    assert r_a["cached"] is True
    assert eye.observe_calls == 2


@pytest.mark.asyncio
async def test_confidence_gating(monkeypatch, tmp_path):
    """High passes, low flags for review (pass=False, NOT an exception)."""
    img_hi = tmp_path / "hi.png"
    _make_png(img_hi)
    img_lo = tmp_path / "lo.png"
    _make_png(img_lo)

    _patch_eye(monkeypatch, _FakeEye(script={str(img_hi): "是，置信度0.92",
                                             str(img_lo): "置信度0.4"}))
    result_hi = await verify_image_content(str(img_hi), "content")
    assert result_hi["pass"] is True
    assert result_hi["confidence"] == 0.92

    # NOTE: both PNGs are byte-identical (same sha) — clear the cache so
    # the low-confidence verify actually hits the engine, not the hi cache.
    _cache.clear()
    result_lo = await verify_image_content(str(img_lo), "content")
    assert result_lo["pass"] is False
    assert result_lo["confidence"] == 0.4
    # Still a valid result dict (content fail ≠ engine fail).
    assert "description" in result_lo


@pytest.mark.asyncio
async def test_percentage_confidence_normalized(monkeypatch, tmp_path):
    """WR-01: "87%" → 0.87, not a false-pass 87.0."""
    img = tmp_path / "pct.png"
    _make_png(img)
    _patch_eye(monkeypatch, _FakeEye(default="是，置信度87%"))
    result = await verify_image_content(str(img), "content")
    assert result["confidence"] == 0.87
    assert result["pass"] is True  # 0.87 >= 0.7


# ---------------------------------------------------------------------------
# Engine-down: fail-closed (the 2026-08-18 core semantic change)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_engine_not_ready_raises(monkeypatch, tmp_path):
    """qwen-eye won't come up → VisionEngineUnavailable. NO fallback,
    NO silent skip."""
    img = tmp_path / "down.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(healthy=False))

    with pytest.raises(VisionEngineUnavailable):
        await verify_image_content(str(img), "content")
    assert eye.observe_calls == 0


@pytest.mark.asyncio
async def test_empty_response_raises(monkeypatch, tmp_path):
    img = tmp_path / "empty.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default="   "))

    with pytest.raises(VisionEngineUnavailable):
        await verify_image_content(str(img), "content")
    assert eye.stopped == 1  # stop_if_owned still runs (lease hygiene)


@pytest.mark.asyncio
async def test_observe_exception_raises(monkeypatch, tmp_path):
    img = tmp_path / "boom.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye(default=RuntimeError("LLM call failed")))

    with pytest.raises(VisionEngineUnavailable):
        await verify_image_content(str(img), "content")


@pytest.mark.asyncio
async def test_unknown_engine_order_fails_closed(monkeypatch, tmp_path):
    """An engine_order naming only UNKNOWN engines runs NO arm and fails
    closed (the fail-closed contract guards against unresolvable orders;
    "glm-5.3-flash" names the hosted arm when opt-in, but any unknown
    pin still runs nothing)."""
    img = tmp_path / "stale.png"
    _make_png(img)
    eye = _patch_eye(monkeypatch, _FakeEye())

    with pytest.raises(VisionEngineUnavailable):
        await verify_image_content(
            str(img), "content", engine_order=["totally-unknown-engine"]
        )
    assert eye.observe_calls == 0


def test_default_engine_order_flipped_to_hosted():
    """fixbatch-007 (2026-08-27 Kai 终审): hosted glm-5.3-flash IS the
    default order; the KNOWN set still has both arms (qwen-eye explicit
    opt-in only — and video-analysis consumers outside this seam)."""
    assert vv._ENGINE_ORDER_DEFAULT == ["glm-5.3-flash"]
    assert vv._KNOWN_ENGINES == ("qwen-eye", "glm-5.3-flash")


# ---------------------------------------------------------------------------
# verify_batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_per_image_calls(monkeypatch, tmp_path):
    """qwen-eye verifies per-image (llama.cpp multi-image constraint)."""
    paths = []
    for i in range(6):
        p = tmp_path / f"img_{i}.png"
        _make_png(p)
        paths.append(str(p))
    eye = _patch_eye(monkeypatch, _FakeEye(default="是，置信度0.9"))

    results = await verify_batch(paths, ["content"] * 6)

    assert eye.observe_calls == 6
    assert len(results) == 6
    for r in results:
        assert r["pass"] is True
        assert r["engine"] == "qwen-eye"
        assert r["usage"] == {"input_tokens": 0, "output_tokens": 0}


@pytest.mark.asyncio
async def test_batch_engine_down_raises(monkeypatch, tmp_path):
    paths = []
    for i in range(3):
        p = tmp_path / f"down_{i}.png"
        _make_png(p)
        paths.append(str(p))
    _patch_eye(monkeypatch, _FakeEye(healthy=False))

    with pytest.raises(VisionEngineUnavailable):
        await verify_batch(paths, ["content"] * 3)


@pytest.mark.asyncio
async def test_batch_per_image_failure_isolated(monkeypatch, tmp_path):
    """One image's observe error → engine_error row, batch continues."""
    paths = []
    for i in range(3):
        p = tmp_path / f"mix_{i}.png"
        _make_png(p)
        paths.append(str(p))
    script = {
        str(paths[0]): "是，置信度0.9",
        str(paths[1]): RuntimeError("transient"),
        str(paths[2]): "是，置信度0.85",
    }
    eye = _patch_eye(monkeypatch, _FakeEye(script=script))

    results = await verify_batch(paths, ["content"] * 3)

    assert eye.observe_calls == 3
    assert results[0]["pass"] is True
    assert results[1]["pass"] is False
    assert results[1]["engine_error"] is True
    assert "engine error" in results[1]["description"]
    assert results[2]["pass"] is True


# ---------------------------------------------------------------------------
# Phase 79-02: get_threshold + stratum param tests (IMG-09-APPLY, unchanged)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backward_compat_no_stratum_param(monkeypatch, tmp_path):
    """Existing callers without stratum param use the 0.7 default."""
    _threshold_cache.clear()
    img = tmp_path / "compat.png"
    _make_png(img)

    _patch_eye(monkeypatch, _FakeEye(script={str(img): "是，置信度0.92"}))
    result_hi = await verify_image_content(str(img), "content")
    assert result_hi["pass"] is True

    _cache.clear()
    _patch_eye(monkeypatch, _FakeEye(script={str(img): "置信度0.4"}))
    result_lo = await verify_image_content(str(img), "content")
    assert result_lo["pass"] is False


def test_get_threshold_fallback_no_config(monkeypatch, tmp_path):
    _threshold_cache.clear()
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    assert get_threshold("1-ref") == 0.7
    assert get_threshold(None) == 0.7
    assert get_threshold("3-ref") == 0.7
    assert get_threshold("text2image") == 0.7


def test_get_threshold_reads_config(monkeypatch, tmp_path):
    _threshold_cache.clear()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "vision_verify:\n  thresholds:\n    1-ref: 0.75\n  default: 0.7\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    assert get_threshold("1-ref") == 0.75
    assert get_threshold("3-ref") == 0.7
    assert get_threshold(None) == 0.7


def test_get_threshold_caches_result(monkeypatch, tmp_path):
    _threshold_cache.clear()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "vision_verify:\n  thresholds:\n    1-ref: 0.75\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    assert get_threshold("1-ref") == 0.75
    config_path.write_text(
        "vision_verify:\n  thresholds:\n    1-ref: 0.85\n",
        encoding="utf-8",
    )
    assert get_threshold("1-ref") == 0.75  # cached
    _threshold_cache.clear()
    assert get_threshold("1-ref") == 0.85  # re-read


def test_get_threshold_does_not_cache_on_error(monkeypatch, tmp_path):
    """WR-04: transient config-read errors never poison the cache."""
    _threshold_cache.clear()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "vision_verify:\n  thresholds:\n    1-ref: 0.85\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )

    from ruamel.yaml import YAML as _RealYAML

    call_count = {"n": 0}
    real_load = _RealYAML.load

    def flaky_load(self, stream):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise OSError("simulated transient config-read error")
        return real_load(self, stream)

    monkeypatch.setattr(_RealYAML, "load", flaky_load)

    assert get_threshold("1-ref") == 0.7
    assert "1-ref" not in _threshold_cache
    assert get_threshold("1-ref") == 0.85
    assert _threshold_cache.get("1-ref") == 0.85


@pytest.mark.asyncio
async def test_verify_with_stratum_uses_configured_threshold(monkeypatch, tmp_path):
    """stratum param actually changes the threshold used."""
    _threshold_cache.clear()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "vision_verify:\n  thresholds:\n    1-ref: 0.85\n  default: 0.7\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "plugins.kais_aigc.vision_verify.get_hermes_home",
        lambda: str(tmp_path),
    )
    img = tmp_path / "stratum_test.png"
    _make_png(img)

    _patch_eye(monkeypatch, _FakeEye(script={str(img): "置信度0.75"}))
    result_no_stratum = await verify_image_content(str(img), "content")
    assert result_no_stratum["pass"] is True  # 0.75 >= 0.7

    _cache.clear()
    _patch_eye(monkeypatch, _FakeEye(script={str(img): "置信度0.75"}))
    result_with_stratum = await verify_image_content(
        str(img), "content", stratum="1-ref"
    )
    assert result_with_stratum["pass"] is False  # 0.75 < 0.85
