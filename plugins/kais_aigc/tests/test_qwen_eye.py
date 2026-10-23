"""test_qwen_eye.py — QwenEye (qwen-eye engine) 单测.

Covers the shared engine layer extracted from p11c:
  - lifecycle: ensure_ready already-healthy / allocate-fallback /
    stop_if_owned semantics (pre-existing lease NEVER stopped)
  - fail-fast guards: VRAM pre-check + poll-time model-load-death
    detection (2026-08-15 验收缺陷 — OOM'd launch must not blind-spin
    the full 120s health poll)
  - observation shape: ONE user message PER image + (帧i/N) tail +
    enable_thinking=False + temperature 0.1 (llama.cpp constraints)
  - ask() text-mode shape
  - engine field: ENGINE_NAME == "qwen-eye"

All HTTP is mocked at the _http_json seam — no real :8125/:10588 calls.
server.log is redirected to tmp_path via the SERVER_LOG module constant —
the real /opt/qwen-llm/server.log is never read (a crash-looping real
server would otherwise leak increment matches into the tests).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest import mock

import pytest

_PLUGINS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGINS_DIR))

from plugins.kais_aigc import qwen_eye as qwen_eye_mod  # noqa: E402
from plugins.kais_aigc.qwen_eye import ENGINE_NAME, QwenEye  # noqa: E402


def _ok_response(content: str) -> tuple[int, dict]:
    return 200, {"choices": [{"message": {"content": content}}]}


@pytest.fixture(autouse=True)
def _isolate_server_log(tmp_path, monkeypatch):
    """Point SERVER_LOG at an empty tmp file for every test — the poll-time
    death detector must never see the real machine's server.log."""
    fake = tmp_path / "server.log"
    fake.write_bytes(b"")
    monkeypatch.setattr(qwen_eye_mod, "SERVER_LOG", str(fake))
    yield


class TestEngineName:
    def test_engine_name(self):
        assert ENGINE_NAME == "qwen-eye"


class TestLifecycle:
    def test_ensure_ready_already_healthy_not_owned(self):
        """Server up before allocate → (True, False) and stop_if_owned no-ops."""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=True) as h:
            assert eye.ensure_ready() == (True, False)
        h.assert_called_once()
        with mock.patch("plugins.kais_aigc.qwen_eye.subprocess") as sub:
            eye.stop_if_owned()
        sub.run.assert_not_called()

    def test_ensure_ready_allocate_then_healthy_owned(self):
        """KAP allocate granted → healthy → (True, True); stop_if_owned stops."""
        eye = QwenEye(caller="kap:test")
        health = mock.patch.object(QwenEye, "_health_ok",
                                   side_effect=[False, True])
        alloc = mock.patch.object(
            QwenEye, "_http_json",
            return_value=(200, {"data": {"granted": True}}),
        )
        with health, alloc as http, \
                mock.patch.object(QwenEye, "_vram_free_mib", return_value=None):
            assert eye.ensure_ready(timeout_s=10) == (True, True)
        # allocate payload carries variantId + the caller identity
        payload = http.call_args_list[0].kwargs["payload"]
        assert payload["variantId"] == "q4"  # 2026-08-23 q3→q4
        assert payload["caller"] == "kap:test"
        with mock.patch("plugins.kais_aigc.qwen_eye.subprocess") as sub:
            eye.stop_if_owned()
        sub.run.assert_called_once()
        argv = sub.run.call_args.args[0]
        assert argv[:3] == ["bash", "/opt/qwen-llm/kap-llm.sh", "stop"]

    def test_ensure_ready_kap_down_falls_back_to_script(self):
        """KAP 500(服务坏,非策略拒绝)→ lease 兜底拉起 → health ok。"""
        eye = QwenEye(caller="kap:test")
        http = mock.patch.object(
            QwenEye, "_http_json",
            return_value=(500, "kap down"),
        )
        health = mock.patch.object(QwenEye, "_health_ok",
                                   side_effect=[False, True])
        with http, health, \
                mock.patch.object(QwenEye, "_vram_free_mib", return_value=None), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess") as sub:
            assert eye.ensure_ready(timeout_s=10) == (True, True)
        started = [c for c in sub.run.call_args_list
                   if "start" in str(c) and "q4" in str(c)]
        assert started, "fallback must invoke kap-llm.sh start q4"

    def test_ensure_ready_queue_refused_no_bypass(self):
        """73-02 F21:队列显式拒绝(200 granted=false)→ 不绕队直跑,
        (False, Fast) 返回,kap-llm.sh start 零调用。"""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(
                    QwenEye, "_http_json",
                    return_value=(200, {"data": {"granted": False,
                                                 "reason": "GPU busy"}}),
                ), \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=None), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess") as sub:
            assert eye.ensure_ready(timeout_s=5) == (False, False)
        started = [c for c in sub.run.call_args_list if "start" in str(c)]
        assert not started, "queue refusal must NOT bypass to kap-llm.sh"

    def test_ensure_ready_queue_4xx_no_bypass(self):
        """73-02 F21:4xx(如 400 bad variant)同样是队列层拒绝 → 不绕队。"""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(409, "conflict")), \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=None), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess") as sub:
            assert eye.ensure_ready(timeout_s=5) == (False, False)
        assert not [c for c in sub.run.call_args_list if "start" in str(c)]

    def test_ensure_ready_never_healthy(self):
        """No server ever comes up → (False, True); owned stop still fires."""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(0, "conn refused")), \
                mock.patch.object(QwenEye, "_vram_free_mib", return_value=None), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess"):
            assert eye.ensure_ready(timeout_s=1) == (False, True)


class TestFailFast:
    """2026-08-15 验收缺陷: 模型加载失败 = 硬性不可用, 快速失败进降级."""

    def test_vram_insufficient_skips_start_immediately(self):
        """GPU1 free < threshold → (False, False) fast: no allocate, no
        script, and no 120s poll (returns well under 2s).
        08-23 GPU 接力:卸载重检路径(_unload_comfyui_models/_wait_vram_freed)
        被 mock 掉——本测试只关心"腾不出来就 fast-skip"。"""
        eye = QwenEye(caller="kap:test")
        t0 = time.monotonic()
        with mock.patch.object(QwenEye, "_health_ok", return_value=False) as h, \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=4712) as vram, \
                mock.patch.object(qwen_eye_mod, "_unload_comfyui_models") as unl, \
                mock.patch.object(qwen_eye_mod, "_wait_vram_freed") as wf, \
                mock.patch.object(QwenEye, "_http_json") as http, \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess") as sub:
            assert eye.ensure_ready() == (False, False)
        elapsed = time.monotonic() - t0
        h.assert_called_once()      # initial health check still ran
        vram.assert_called()  # pre-check ran(含卸载后复检)
        unl.assert_called_once()    # GPU 接力卸载先尝试
        wf.assert_called_once()
        http.assert_not_called()   # KAP allocate NEVER touched
        sub.run.assert_not_called()  # no kap-llm.sh, and stop_if_owned no-ops
        assert elapsed < 2.0, f"must fail fast, took {elapsed:.2f}s"
        eye.stop_if_owned()  # not owned → still a no-op (no real script call)

    def test_vram_check_nvidia_smi_missing_fails_open(self):
        """_vram_free_mib None (no nvidia-smi / timeout) → fail-open, the
        original allocate+poll path runs untouched."""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=None), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(200, {"data": {"granted": True}})), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess"):
            assert eye.ensure_ready(timeout_s=1) == (False, True)  # polled out

    def test_vram_free_exact_threshold_passes_precheck(self):
        """Boundary: free == _VRAM_MIN_FREE_MIB passes the >= check."""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(
                    QwenEye, "_vram_free_mib",
                    return_value=qwen_eye_mod._VRAM_MIN_FREE_MIB,
                ), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(200, {"data": {"granted": True}})), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess"):
            assert eye.ensure_ready(timeout_s=1) == (False, True)

    def test_poll_breaks_on_model_load_failure(self, tmp_path):
        """Guard 2: server.log gains 'failed to load model' during the poll
        → immediate (False, True), long before the timeout."""
        log = Path(qwen_eye_mod.SERVER_LOG)
        eye = QwenEye(caller="kap:test")
        probe_count = [0]

        def health(timeout=5.0):
            # Call 1 is the INITIAL health check (before log_offset is
            # taken); poll probes start at call 2 — the launch attempt
            # dies right after the first poll probe.
            probe_count[0] += 1
            if probe_count[0] >= 2:
                with open(log, "ab") as fh:
                    fh.write(
                        b"0.02.587.888 E llama_model_load_from_file_impl: "
                        b"failed to load model\n"
                        b"0.02.588.487 E srv  llama_server: exiting due to "
                        b"model loading error\n"
                    )
            return False

        t0 = time.monotonic()
        with mock.patch.object(QwenEye, "_health_ok", side_effect=health), \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=20000), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(200, {"data": {"granted": True}})), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess"):
            assert eye.ensure_ready(timeout_s=60) == (False, True)
        elapsed = time.monotonic() - t0
        assert probe_count[0] <= 3, (
            f"poll must break after ~2 probes, ran {probe_count[0]}"
        )
        assert elapsed < 5.0, f"must break fast, took {elapsed:.2f}s"

    def test_poll_ignores_stale_load_failures_before_offset(self, tmp_path):
        """Only NEW log content counts: pre-existing OOM lines from an
        earlier crash (before our launch offset) must NOT abort the poll
        when the current launch is still loading fine."""
        stale = Path(qwen_eye_mod.SERVER_LOG)
        with open(stale, "ab") as fh:
            fh.write(b"OLD CRASH: failed to load model (yesterday)\n")
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=20000), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(0, "conn refused")), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess"), \
                mock.patch("plugins.kais_aigc.qwen_eye.time") as t:
            t.monotonic.side_effect = [0, 1, 2]  # 3 loop iterations then out
            t.sleep = lambda *_: None
            assert eye.ensure_ready(timeout_s=1) == (False, True)

    def test_missing_server_log_detection_noop(self, monkeypatch, tmp_path):
        """server.log absent → Guard 2 silently disabled, poll behaves as
        before (times out to (False, True))."""
        monkeypatch.setattr(qwen_eye_mod, "SERVER_LOG",
                            str(tmp_path / "does-not-exist.log"))
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_health_ok", return_value=False), \
                mock.patch.object(QwenEye, "_vram_free_mib",
                                  return_value=20000), \
                mock.patch.object(QwenEye, "_http_json",
                                  return_value=(0, "conn refused")), \
                mock.patch("plugins.kais_aigc.qwen_eye.subprocess"), \
                mock.patch("plugins.kais_aigc.qwen_eye.time") as t:
            t.monotonic.side_effect = [0, 1, 2]
            t.sleep = lambda *_: None
            assert eye.ensure_ready(timeout_s=1) == (False, True)


class TestObserveShape:
    def test_observe_one_user_message_per_image(self, tmp_path):
        """HARD CONSTRAINT: N images → N user messages, 1 image each, each
        with a (帧i/N) tail; the multi-image-drop bug forbids batching."""
        imgs = []
        for i in range(5):
            p = tmp_path / f"f{i}.jpg"
            p.write_bytes(b"fake-jpg")
            imgs.append(p)
        eye = QwenEye(caller="kap:test")
        calls: list[dict] = []

        def fake_http(url, payload=None, timeout=30.0):
            calls.append(payload)
            return _ok_response("观察描述")

        with mock.patch.object(QwenEye, "_http_json", side_effect=fake_http):
            text = eye.observe(imgs)
        assert text == "观察描述"
        messages = calls[0]["messages"]
        assert len(messages) == 5
        for i, msg in enumerate(messages):
            assert msg["role"] == "user"
            parts = msg["content"]
            assert len(parts) == 2
            assert parts[0]["type"] == "image_url"
            assert parts[0]["image_url"]["url"].startswith(
                "data:image/jpeg;base64,",
            )
            assert parts[1]["text"] == f"(帧{i + 1}/5)"

    def test_call_llm_body_constraints(self, tmp_path):
        """Body: model qwen3.8, temperature 0.1, thinking DISABLED."""
        eye = QwenEye(caller="kap:test")
        bodies: list[dict] = []

        def fake_http(url, payload=None, timeout=30.0):
            bodies.append(payload)
            return _ok_response("ok")

        with mock.patch.object(QwenEye, "_http_json", side_effect=fake_http):
            eye.ask("问题?", max_tokens=800)
        body = bodies[0]
        assert body["model"] == "qwen3.8"
        assert body["temperature"] == 0.1
        assert body["max_tokens"] == 800
        assert body["chat_template_kwargs"] == {"enable_thinking": False}
        assert body["messages"] == [{"role": "user", "content": "问题?"}]

    def test_call_llm_retries_once_then_raises(self):
        """Both attempts fail → RuntimeError (caller decides degrade)."""
        eye = QwenEye(caller="kap:test")
        with mock.patch.object(QwenEye, "_http_json",
                               return_value=(0, "conn refused")), \
                mock.patch("plugins.kais_aigc.qwen_eye.time") as t:
            t.sleep = lambda *_: None
            try:
                eye.ask("问题")
                raise AssertionError("must raise")
            except RuntimeError as exc:
                assert "qwen-eye LLM call failed" in str(exc)

    def test_call_llm_recovers_on_second_attempt(self):
        """First attempt HTTP 503 (OOM), second succeeds → no raise."""
        eye = QwenEye(caller="kap:test")
        responses = iter([(503, "OOM"), _ok_response("恢复后的回答")])
        with mock.patch.object(
            QwenEye, "_http_json", side_effect=lambda *a, **k: next(responses),
        ), mock.patch("plugins.kais_aigc.qwen_eye.time") as t:
            t.sleep = lambda *_: None
            assert eye.ask("问题") == "恢复后的回答"

    def test_observe_single_image_plus_question(self, tmp_path):
        """observe_single: 1 user message, image part + question text part."""
        img = tmp_path / "one.png"
        img.write_bytes(b"fake-png")
        eye = QwenEye(caller="kap:test")
        captured: dict = {}

        def fake_http(url, payload=None, timeout=30.0):
            captured["payload"] = payload
            return _ok_response("是，置信度0.9")

        with mock.patch.object(QwenEye, "_http_json", side_effect=fake_http):
            eye.observe_single(img, "这张图是猫吗？")
        msg = captured["payload"]["messages"][0]
        assert msg["role"] == "user"
        assert msg["content"][0]["type"] == "image_url"
        assert msg["content"][1]["text"] == "这张图是猫吗？"
