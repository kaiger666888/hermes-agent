"""test_kais_ear.py — KaisEar (kais-ear 双后端引擎) 单测.

更名批 (2026-09-27) 自 test_qwen_ear.py 改写:
  - Omni 听审后端 (:8126) 生命周期/形状 — 全部平移 (KAP ear allocate
    三态收编语义零变化): already-healthy / allocate granted / queue-refused
    no-bypass (73-02 F21 同款) / script-start fallback / stop_if_owned
    (pre-existing server NEVER stopped; owned 先 KAP release, 失败回落
    脚本 stop) / poll-time model-load-death detection (Guard 2)
  - hybrid 转写后端 (:8012 / KAP :10588) 新增面:
      transcribe 经 KAP 路由 (ensure 内嵌) → 200 envelope unwrap;
      503 = 队列拒绝不绕队 (零脚本/零直连); 400 = ValueError;
      KAP 宕机 → kap-hybrid-asr.sh start 兜底 → 直连重试 → owned;
      ensure_transcriber_ready 三态 (sidecar 活 / KAP 活 / 双挂);
      ensure-hardening 批 (0927): 分支1/3 补 model_loaded 门 — 三态活
      只证进程在, status=loading 下 worker 可半途 OOM 自毁 (8188 渲染
      22.4G 驻留竞态, 首打 3×503 白烧事故), 等真载完才放行;
      stop_if_owned 按后端归属 (hybrid 兜底拉起才停, KAP 管不停;
      Omni 沿收编批语义)
  - shim: qwen_ear.py deprecated 兼容面 (import * + QwenEar 别名)

All HTTP is mocked at the _http_json seam — no real :8012/:8126/:10588
calls. server.log is redirected to tmp_path via the SERVER_LOG module
constant. 全程禁真 GPU 服务 (工单红线)。
"""

from __future__ import annotations

import base64
import logging
import sys
from pathlib import Path
from unittest import mock

import pytest

_PLUGINS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGINS_DIR))

from plugins.kais_aigc import kais_ear as kais_ear_mod  # noqa: E402
from plugins.kais_aigc.kais_ear import (  # noqa: E402
    ENGINE_NAME,
    HYBRID_SCRIPT_TIMEOUT_S,
    HYBRID_TRANSCRIBE_TIMEOUT_S,
    KaisEar,
)


def _ok_response(content: str) -> tuple[int, dict]:
    return 200, {"choices": [{"message": {"content": content}}]}


def _kap_ok(data: dict) -> tuple[int, dict]:
    """KAP 路由成功 envelope {code, data, message}。"""
    return 200, {"code": 0, "data": data, "message": "ok"}


_HYBRID_PAYLOAD = {
    "draft": "草稿文本",
    "final": "终稿文本",
    "sent_windows": [],
    "fw_calls": 2,
    "first_text_s": 0.8,
    "per_sentence": [{"text": "终稿文本", "engine": "fw"}],
    "timings": {"load_s": 0.0, "draft_s": 1.2, "final_s": 0.8, "total_s": 2.0},
}


@pytest.fixture(autouse=True)
def _isolate_server_log(tmp_path, monkeypatch):
    """Point SERVER_LOG at an empty tmp file for every test."""
    fake = tmp_path / "server.log"
    fake.write_bytes(b"")
    monkeypatch.setattr(kais_ear_mod, "SERVER_LOG", str(fake))
    yield


@pytest.fixture()
def wav_file(tmp_path) -> Path:
    p = tmp_path / "S1_a01.wav"
    p.write_bytes(b"RIFF" + b"\x00" * 1000)
    return p


class TestEngineName:
    def test_engine_name(self):
        assert ENGINE_NAME == "kais-ear"


# ══ Omni 听审后端 (:8126) — 收编批语义平移 ═════════════════════════════


class TestOmniLifecycle:
    def test_ensure_ready_already_healthy_not_owned(self):
        """Server up before start → (True, False); stop_if_owned no-ops."""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok", return_value=True):
            ok, owned = ear.ensure_ready()
        assert (ok, owned) == (True, False)
        # stop must not touch a server we didn't start
        with mock.patch("subprocess.run") as run:
            ear.stop_if_owned()
            run.assert_not_called()

    def test_ensure_ready_start_ok(self, tmp_path):
        """Server down → script runs → health flips on → (True, True).

        收编后脚本路径只在 KAP 不可达时兜底 — mock allocate 为 status 0,
        其余断言与旧语义一致 (行为兼容锚)。"""
        ear = KaisEar(caller="kap:test")
        health = {"ok": False}
        with mock.patch.object(
            KaisEar, "_health_ok",
            side_effect=lambda *a, **k: health["ok"],
        ), mock.patch.object(KaisEar, "_http_json",
                             return_value=(0, "conn refused")), \
                mock.patch("subprocess.run") as run:
            def _flip(*a, **k):
                health["ok"] = True
                return mock.Mock(returncode=0)
            run.side_effect = _flip
            ok, owned = ear.ensure_ready(timeout_s=30)
        assert (ok, owned) == (True, True)
        assert ear._owned is True

    def test_ensure_ready_load_death_aborts(self, tmp_path):
        """server.log shows 'failed to load model' → give up fast."""
        log = tmp_path / "server.log"
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok", return_value=False), \
             mock.patch.object(KaisEar, "_http_json",
                               return_value=(0, "conn refused")), \
             mock.patch("subprocess.run"), \
             mock.patch.object(KaisEar, "_server_log_size", return_value=0):
            log.write_bytes(b"llama_model_load: failed to load model\n")
            ok, owned = ear.ensure_ready(timeout_s=30)
        assert ok is False

    def test_stop_if_owned_calls_script(self):
        """owned + release 失败 (KAP 不可达) → 旧脚本 stop 兜底 (兼容锚)。"""
        ear = KaisEar(caller="kap:test")
        ear._owned = True
        with mock.patch.object(KaisEar, "_http_json",
                               return_value=(0, "conn refused")), \
                mock.patch("subprocess.run") as run:
            ear.stop_if_owned()
            assert run.call_count == 1
            assert run.call_args.args[0][:3] == \
                ["bash", kais_ear_mod.KAP_EAR_SH, "stop"]


class TestOmniKapScheduling:
    """Omni 后端 2026-09-27 收编 KAP 中央调度 (Kai 0925 令) — 平移锚。

    契约实读 (kais-aigc-platform/src/routes/production/ear/index.ts):
    allocate body {caller} → 200 {code,data,message}, data.granted 为授权
    判据 (5xx = 服务坏, 非策略拒绝); release body {caller} → data {ok:true}。
    """

    def test_healthy_fast_path_zero_posts(self):
        """已健康 → (True, False), KAP allocate/release 零 POST。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok", return_value=True), \
                mock.patch.object(KaisEar, "_http_json") as http:
            assert ear.ensure_ready() == (True, False)
        http.assert_not_called()

    def test_allocate_granted_then_healthy_owned(self):
        """allocate 200 granted → 健康 → (True, True), 脚本零调用。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok",
                               side_effect=[False, True]), \
                mock.patch.object(KaisEar, "_http_json",
                                  return_value=(200, {"data": {"granted": True}})) as http, \
                mock.patch("subprocess.run") as run:
            assert ear.ensure_ready(timeout_s=30) == (True, True)
        assert http.call_args.args[0] == kais_ear_mod.KAP_ALLOCATE_URL
        assert http.call_args.kwargs["payload"] == {"caller": "kap:test"}
        assert http.call_args.kwargs["timeout"] == 30.0
        run.assert_not_called()  # 经队列取得 — kap-ear.sh start 零调用
        assert ear._owned is True

    def test_allocate_unreachable_falls_back_to_script(self):
        """KAP 不可达 (conn refused) → 回落脚本路径不抛 → (True, True)。"""
        ear = KaisEar(caller="kap:test")
        health = {"ok": False}

        def _flip(*a, **k):
            health["ok"] = True
            return mock.Mock(returncode=0)

        with mock.patch.object(
            KaisEar, "_health_ok",
            side_effect=lambda *a, **k: health["ok"],
        ), mock.patch.object(KaisEar, "_http_json",
                             return_value=(0, "conn refused")), \
                mock.patch("subprocess.run", side_effect=_flip) as run:
            assert ear.ensure_ready(timeout_s=30) == (True, True)
        assert [c for c in run.call_args_list if "start" in str(c.args[0])]
        assert ear._owned is True

    def test_allocate_500_falls_back_to_script(self):
        """KAP 5xx = 服务坏 (非策略拒绝) → 同样回落脚本兜底。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok",
                               side_effect=[False, True]), \
                mock.patch.object(KaisEar, "_http_json",
                                  return_value=(500, "kap down")), \
                mock.patch("subprocess.run") as run:
            assert ear.ensure_ready(timeout_s=10) == (True, True)
        assert [c for c in run.call_args_list if "start" in str(c.args[0])]

    def test_allocate_exception_falls_back_to_script(self):
        """allocate POST 自身抛异常 → 吞掉, 回落脚本路径不抛。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok",
                               side_effect=[False, True]), \
                mock.patch.object(KaisEar, "_http_json",
                                  side_effect=OSError("kap exploded")), \
                mock.patch("subprocess.run") as run:
            assert ear.ensure_ready(timeout_s=10) == (True, True)
        assert [c for c in run.call_args_list if "start" in str(c.args[0])]

    def test_queue_refused_no_bypass(self):
        """73-02 F21 同款: 200 granted=false = 队列说不行 → 不绕队直跑。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok", return_value=False), \
                mock.patch.object(
                    KaisEar, "_http_json",
                    return_value=(200, {"data": {"granted": False,
                                                 "reason": "GPU busy"}}),
                ), \
                mock.patch("subprocess.run") as run:
            assert ear.ensure_ready(timeout_s=5) == (False, False)
        assert not [c for c in run.call_args_list if "start" in str(c.args[0])]
        assert ear._owned is False

    def test_queue_4xx_no_bypass(self):
        """4xx 同为队列层拒绝 → 不绕队。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_health_ok", return_value=False), \
                mock.patch.object(KaisEar, "_http_json",
                                  return_value=(409, "conflict")), \
                mock.patch("subprocess.run") as run:
            assert ear.ensure_ready(timeout_s=5) == (False, False)
        assert not [c for c in run.call_args_list if "start" in str(c.args[0])]

    def test_release_only_when_owned(self):
        """未 own → stop 零 POST 零脚本 (预存服务绝不碰)。"""
        ear = KaisEar(caller="kap:test")
        ear._owned = False
        with mock.patch.object(KaisEar, "_http_json") as http, \
                mock.patch("subprocess.run") as run:
            ear.stop_if_owned()
        http.assert_not_called()
        run.assert_not_called()

    def test_release_via_kap_when_owned(self):
        """owned 停止先走 KAP release (payload 带 caller), 脚本零调用。"""
        ear = KaisEar(caller="kap:test")
        ear._owned = True
        with mock.patch.object(KaisEar, "_http_json",
                               return_value=(200, {"data": {"ok": True}})) as http, \
                mock.patch("subprocess.run") as run:
            ear.stop_if_owned()
        assert http.call_args.args[0] == kais_ear_mod.KAP_RELEASE_URL
        assert http.call_args.kwargs["payload"] == {"caller": "kap:test"}
        assert http.call_args.kwargs["timeout"] == 60.0
        run.assert_not_called()
        assert ear._owned is False

    def test_release_non_200_falls_back_to_script_once(self):
        """release 非 200 → 旧脚本 stop 兜底恰好一次。"""
        ear = KaisEar(caller="kap:test")
        ear._owned = True
        with mock.patch.object(KaisEar, "_http_json",
                               return_value=(500, "boom")), \
                mock.patch("subprocess.run") as run:
            ear.stop_if_owned()
        assert run.call_count == 1
        assert run.call_args.args[0][:3] == \
            ["bash", kais_ear_mod.KAP_EAR_SH, "stop"]

    def test_start_timeout_default_covers_kap_cold_start(self):
        """allocate 服务端 timeoutMs=600s → 客户端缺省 ≥900s。"""
        assert kais_ear_mod.EAR_START_TIMEOUT_S >= 900


class TestListenShape:
    def test_listen_wav_content_shape(self, wav_file):
        """input_audio part: base64 data + format=wav + text question."""
        ear = KaisEar(caller="kap:test")
        captured = {}

        def fake_http(url, payload=None, timeout=30.0):
            captured["payload"] = payload
            return _ok_response("答案")

        with mock.patch.object(KaisEar, "_http_json", side_effect=fake_http):
            out = ear.listen(wav_file, "这段音频什么情绪")
        assert out == "答案"
        body = captured["payload"]
        assert body["temperature"] == 0.1
        assert body["chat_template_kwargs"] == {"enable_thinking": False}
        content = body["messages"][0]["content"]
        types = [p["type"] for p in content]
        assert types == ["input_audio", "text"]
        audio_part = content[0]["input_audio"]
        assert audio_part["format"] == "wav"
        assert audio_part["data"] == base64.b64encode(
            wav_file.read_bytes()).decode()

    def test_listen_rejects_ogg(self, tmp_path):
        ear = KaisEar(caller="kap:test")
        p = tmp_path / "clip.ogg"
        p.write_bytes(b"OggS" + b"\x00" * 100)
        with pytest.raises(ValueError, match="wav"):
            ear.listen(p, "q")

    def test_listen_rejects_huge_file(self, tmp_path):
        ear = KaisEar(caller="kap:test")
        p = tmp_path / "big.wav"
        p.write_bytes(b"RIFF" + b"\x00" * (8 * 1024 * 1024 + 10))
        with mock.patch.object(Path, "stat") as st:
            st.return_value = mock.Mock(st_size=9 * 1024 * 1024)
            with pytest.raises(ValueError, match="too large"):
                ear.listen(p, "q")

    def test_listen_retry_on_transient_failure(self, wav_file):
        ear = KaisEar(caller="kap:test")
        responses = [(0, "conn refused"), _ok_response("第二次成功")]
        with mock.patch.object(KaisEar, "_http_json",
                               side_effect=responses), \
             mock.patch("time.sleep"):
            out = ear.listen(wav_file, "q")
        assert out == "第二次成功"


class TestAskShape:
    def test_ask_plain_text(self):
        ear = KaisEar(caller="kap:test")
        captured = {}

        def fake_http(url, payload=None, timeout=30.0):
            captured["payload"] = payload
            return _ok_response("答案")

        with mock.patch.object(KaisEar, "_http_json", side_effect=fake_http):
            assert ear.ask("问题?") == "答案"
        body = captured["payload"]
        assert body["messages"] == [{"role": "user", "content": "问题?"}]
        assert body["max_tokens"] == 800


# ══ hybrid 转写后端 (:8012 / KAP :10588) — 更名批新增面 ═══════════════


class TestTranscribeViaKap:
    def test_transcribe_ok_unwraps_envelope(self, wav_file):
        """经 KAP 路由成功 → envelope data 剥壳返回 (含 final/per_sentence)。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(
            KaisEar, "_http_json",
            return_value=_kap_ok(dict(_HYBRID_PAYLOAD)),
        ) as http, mock.patch("subprocess.run") as run:
            out = ear.transcribe(wav_file)
        assert out["final"] == "终稿文本"
        assert out["draft"] == "草稿文本"
        assert out["fw_calls"] == 2
        assert http.call_args.args[0] == kais_ear_mod.KAP_HYBRID_TRANSCRIBE_URL
        body = http.call_args.kwargs["payload"]
        assert body["audio_path"] == str(wav_file.resolve())
        assert body["language"] == "Chinese"
        run.assert_not_called()  # KAP 面 200 → 零脚本零直连

    def test_transcribe_timeout_floor_600s(self, wav_file):
        """超时底线 600s 对齐 KAP 路由 (转发底线) + 客户端余量。"""
        assert HYBRID_TRANSCRIBE_TIMEOUT_S >= 600
        assert HYBRID_SCRIPT_TIMEOUT_S >= 600 - 1  # 脚本内预算 420+180

    def test_transcribe_queue_refusal_never_bypasses(self, wav_file):
        """503 allocate-not-granted = GPU 队列拒绝 → RuntimeError, 绝不
        脚本直启/直连绕队 (Kai 0925 令)。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(
            KaisEar, "_http_json",
            return_value=(503, {"message": "allocate-not-granted"}),
        ) as http, mock.patch("subprocess.run") as run:
            with pytest.raises(RuntimeError, match="队列拒绝"):
                ear.transcribe(wav_file)
        # 只有一次 KAP POST, 零脚本零直连
        assert http.call_count == 1
        run.assert_not_called()
        assert ear._hybrid_owned is False

    def test_transcribe_400_raises_value_error(self, wav_file):
        """400 (sidecar 同语义本地镜像) → ValueError, 不走兜底路径。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(
            KaisEar, "_http_json",
            return_value=(400, "audio_path 不存在"),
        ), mock.patch("subprocess.run") as run:
            with pytest.raises(ValueError, match="400"):
                ear.transcribe(wav_file)
        run.assert_not_called()

    def test_transcribe_rejects_bad_suffix_and_missing_file(self, tmp_path):
        """本地 400 镜像 fail-fast: 后缀/存在性校验先于任何 HTTP。"""
        ear = KaisEar(caller="kap:test")
        ogg = tmp_path / "clip.ogg"
        ogg.write_bytes(b"OggS")
        missing = tmp_path / "ghost.wav"
        with mock.patch.object(KaisEar, "_http_json") as http:
            with pytest.raises(ValueError, match=r"\.wav/\.mp3"):
                ear.transcribe(ogg)
            with pytest.raises(ValueError, match="不存在"):
                ear.transcribe(missing)
        http.assert_not_called()

    def test_transcribe_kap_down_script_fallback_direct_retry(self, wav_file):
        """KAP 宕机 (status 0) → kap-hybrid-asr.sh start 兜底 → 直连
        :8012 重试成功 → hybrid owned → stop_if_owned 走脚本 stop。"""
        ear = KaisEar(caller="kap:test")
        alive = {"ok": False}

        def _http(url, payload=None, timeout=30.0):
            if url == kais_ear_mod.HYBRID_HEALTH_URL:
                return (200, {"status": "ok"}) if alive["ok"] \
                    else (0, "refused")
            if url == kais_ear_mod.KAP_HYBRID_TRANSCRIBE_URL:
                return (0, "kap refused")
            if url == kais_ear_mod.HYBRID_TRANSCRIBE_API:
                assert alive["ok"], "direct retry only after script start"
                return (200, dict(_HYBRID_PAYLOAD))
            raise AssertionError(f"unexpected url {url}")

        def _run(cmd, **kw):
            alive["ok"] = True  # 脚本拉起成功 (幂等: health 翻活)
            return mock.Mock(returncode=0)

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http), \
                mock.patch("subprocess.run", side_effect=_run) as run:
            out = ear.transcribe(wav_file)
        assert out["final"] == "终稿文本"
        assert [c.args[0][:3] for c in run.call_args_list][0] == \
            ["bash", kais_ear_mod.KAP_HYBRID_SH, "start"]
        assert ear._hybrid_owned is True
        # owned → stop_if_owned 脚本 stop 归还 VRAM
        with mock.patch("subprocess.run") as run2:
            ear.stop_if_owned()
        assert run2.call_args.args[0][:3] == \
            ["bash", kais_ear_mod.KAP_HYBRID_SH, "stop"]

    def test_transcribe_kap_5xx_falls_back_to_direct(self, wav_file):
        """KAP 病坏 (500 upstream) → sidecar 已活 → 免脚本直接连重试。"""
        ear = KaisEar(caller="kap:test")

        def _http(url, payload=None, timeout=30.0):
            if url == kais_ear_mod.HYBRID_HEALTH_URL:
                return 200, {"status": "ok"}
            if url == kais_ear_mod.KAP_HYBRID_TRANSCRIBE_URL:
                return (500, "sidecar returned 503")
            if url == kais_ear_mod.HYBRID_TRANSCRIBE_API:
                return (200, dict(_HYBRID_PAYLOAD))
            raise AssertionError(f"unexpected url {url}")

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http), \
                mock.patch("subprocess.run") as run:
            out = ear.transcribe(wav_file)
        assert out["final"] == "终稿文本"
        run.assert_not_called()  # sidecar 已活 → 免脚本
        assert ear._hybrid_owned is False  # 借用预存服务不 own

    def test_transcribe_all_paths_dead_raises(self, wav_file, monkeypatch):
        """KAP 宕机 + 脚本拉不起 (health 恒死) → RuntimeError。"""
        ear = KaisEar(caller="kap:test")
        # 轮询预算缩到 ~0 (否则 monotonic 死线 busy-loop 60s)
        monkeypatch.setattr(kais_ear_mod, "_HYBRID_POST_SCRIPT_POLL_S", 0.05)

        def _http(url, payload=None, timeout=30.0):
            if url == kais_ear_mod.HYBRID_HEALTH_URL:
                return 0, "refused"
            if url == kais_ear_mod.KAP_HYBRID_TRANSCRIBE_URL:
                return 0, "kap refused"
            raise AssertionError(f"unexpected url {url}")

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http), \
                mock.patch("subprocess.run") as run, \
                mock.patch.object(kais_ear_mod.time, "sleep"):
            run.return_value = mock.Mock(returncode=1)
            with pytest.raises(RuntimeError, match="transcribe failed"):
                ear.transcribe(wav_file)
        assert ear._hybrid_owned is False


class TestEnsureTranscriberReady:
    def test_sidecar_alive_fast_path(self):
        """三态活 + model_loaded=true → True 热路径零等待 (单次 fetch).

        ensure-hardening 批 (0927) 改写: 原断言「三态任一即 True」是首打
        事故的假阳性本体 (loading ≠ 可转写) — 分支1 现过 model_loaded 门,
        已载才放行; 本测锚定已载热路径 (语义不变的承诺面)。
        """
        for st in ("ok", "idle", "loading"):
            ear = KaisEar(caller="kap:test")
            with mock.patch.object(
                KaisEar, "_http_json",
                return_value=(200, {"status": st, "model_loaded": True}),
            ) as http, mock.patch.object(
                kais_ear_mod.time, "sleep") as slp:
                assert ear.ensure_transcriber_ready() is True
            assert http.call_count == 1  # 单次 /health, 无二次轮询
            slp.assert_not_called()      # 零等待
            assert ear._hybrid_owned is False

    def test_kap_reachable_defers_pullup_to_transcribe(self):
        """sidecar 死 + KAP 活 → True (拉起交 transcribe 内嵌 ensure,
        排队/拒绝由调度器裁决 — hybrid-asr 无独立 allocate 路由)。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_hybrid_alive", return_value=False), \
                mock.patch.object(
                    KaisEar, "_http_json",
                    return_value=(200, {"data": {"healthy": False}}),
                ) as http, mock.patch("subprocess.run") as run:
            assert ear.ensure_transcriber_ready() is True
        assert http.call_args.args[0] == kais_ear_mod.KAP_HYBRID_STATUS_URL
        run.assert_not_called()
        assert ear._hybrid_owned is False

    def test_kap_down_script_fallback_owned(self):
        """sidecar 死 + KAP 死 → 脚本直启 → health 翻活且载完 → True + owned.

        ensure-hardening 批 (0927) 改写: 分支3 末尾新过 model_loaded 门,
        原翻转体 ``{"status": "loading"}`` 无 model_loaded 会被门拦 False
        — 翻转体补 ``model_loaded=True`` 锚定「脚本就绪且模型已载」路径。
        """
        ear = KaisEar(caller="kap:test")
        alive = {"ok": False}

        def _http(url, payload=None, timeout=30.0):
            if url == kais_ear_mod.HYBRID_HEALTH_URL:
                return (200, {"status": "ok", "model_loaded": True}) \
                    if alive["ok"] else (0, "refused")
            return 0, "kap refused"

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http), \
                mock.patch("subprocess.run") as run:
            run.side_effect = lambda *a, **k: alive.__setitem__(
                "ok", True) or mock.Mock(returncode=0)
            assert ear.ensure_transcriber_ready(timeout_s=30) is True
        assert [c.args[0][:3] for c in run.call_args_list][0] == \
            ["bash", kais_ear_mod.KAP_HYBRID_SH, "start"]
        assert ear._hybrid_owned is True

    def test_all_dead_returns_false(self, monkeypatch):
        """sidecar 死 + KAP 死 + 脚本拉不起 → False (调用方 fail-closed)。"""
        ear = KaisEar(caller="kap:test")
        monkeypatch.setattr(kais_ear_mod, "_HYBRID_POST_SCRIPT_POLL_S", 0.05)
        with mock.patch.object(KaisEar, "_hybrid_alive", return_value=False), \
                mock.patch.object(KaisEar, "_http_json",
                                  return_value=(0, "refused")), \
                mock.patch("subprocess.run") as run, \
                mock.patch.object(kais_ear_mod.time, "sleep"):
            run.return_value = mock.Mock(returncode=1)
            assert ear.ensure_transcriber_ready(timeout_s=6) is False
        assert ear._hybrid_owned is False

    def test_kap_managed_hybrid_never_stopped_by_us(self):
        """KAP 管的 hybrid (未 own) → stop_if_owned 不碰 (idleTimeoutMs
        10min + TTL 900s 两层自卸载归调度器)。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(KaisEar, "_hybrid_alive", return_value=False), \
                mock.patch.object(KaisEar, "_http_json",
                                  return_value=(200, {"data": {}})), \
                mock.patch("subprocess.run") as run:
            assert ear.ensure_transcriber_ready() is True
        ear.stop_if_owned()
        run.assert_not_called()


class TestEnsureModelLoadedGate:
    """model_loaded 门 (ensure-hardening 批, 0927 首打事故硬化).

    事故链: ensure 分支1 按「三态活即 True」放行 status=loading →
    8188 渲染驻留 22.4G 挤爆 worker (torch OOM → WorkerGoneError 自毁
    :8012 ECONNREFUSED) → transcribe 3×503 → p10c all-clips error
    白烧一次回滚预算。本类锚定: 分支1/3 的 True 钉死在 model_loaded,
    fail-closed 绝不 raise。全部 mock _http_json /health 序列。
    """

    @pytest.fixture(autouse=True)
    def _fast_poll(self, monkeypatch):
        """轮询间隔 3s→0.05s: 预算测试走真实 monotonic 但不真睡 3s。"""
        monkeypatch.setattr(kais_ear_mod, "_HYBRID_POLL_INTERVAL_S", 0.05)

    def test_loaded_immediate_true_no_sleep(self):
        """分支1: model_loaded=true → 即刻 True (单 fetch 零等待)。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(
            KaisEar, "_http_json",
            return_value=(200, {"status": "ok", "model_loaded": True,
                                "engine": "hybrid-asr-v2c", "ttl_sec": 900,
                                "loading": False, "error": None}),
        ) as http, mock.patch.object(kais_ear_mod.time, "sleep") as slp:
            assert ear.ensure_transcriber_ready() is True
        slp.assert_not_called()
        assert http.call_count == 1

    def test_loading_then_loaded_true(self):
        """分支1: loading→loaded 两轮 → True。"""
        ear = KaisEar(caller="kap:test")
        health = [
            (200, {"status": "loading", "model_loaded": False,
                   "loading": True, "error": None}),
            (200, {"status": "ok", "model_loaded": True,
                   "loading": False, "error": None}),
        ]

        def _http(url, payload=None, timeout=30.0):
            assert url == kais_ear_mod.HYBRID_HEALTH_URL
            return health.pop(0)

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http):
            assert ear.ensure_transcriber_ready(model_loaded_wait_s=5) is True
        assert not health  # 两轮吃完

    def test_loading_forever_budget_exhausted_false(self, caplog):
        """分支1: loading 全程 → 预算耗尽 False + WARNING 带最后 health 摘要。"""
        ear = KaisEar(caller="kap:test")
        with mock.patch.object(
            KaisEar, "_http_json",
            return_value=(200, {"status": "loading", "model_loaded": False,
                                "error": None}),
        ), caplog.at_level(logging.WARNING):
            assert ear.ensure_transcriber_ready(model_loaded_wait_s=1) is False
        assert "model_loaded gate timed out" in caplog.text
        assert "model_loaded=False" in caplog.text  # 运维取证摘要在场

    def test_health_dies_mid_wait_false(self):
        """分支1: 门中等载时 sidecar 自毁 (拒连持续) → 预算耗尽 False.

        0927 事故形态复刻: worker OOM 自毁后 :8012 ECONNREFUSED。
        """
        ear = KaisEar(caller="kap:test")
        state = {"first": True}

        def _http(url, payload=None, timeout=30.0):
            assert url == kais_ear_mod.HYBRID_HEALTH_URL
            if state["first"]:
                state["first"] = False
                return 200, {"status": "loading", "model_loaded": False}
            return 0, "connection refused"

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http):
            assert ear.ensure_transcriber_ready(model_loaded_wait_s=1) is False

    def test_worker_error_false_early(self, caplog):
        """分支1: health 自报 worker error → 提前 False (不烧满预算)。"""
        ear = KaisEar(caller="kap:test")
        health = [
            (200, {"status": "loading", "model_loaded": False}),
            (200, {"status": "error", "model_loaded": False,
                   "error": "torch.OutOfMemoryError: Tried to allocate "
                            "24.00 MiB"}),
        ]

        def _http(url, payload=None, timeout=30.0):
            assert url == kais_ear_mod.HYBRID_HEALTH_URL
            return health.pop(0)

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http), \
                caplog.at_level(logging.WARNING):
            # 预算给 5s: 若无提前退路, 走满预算才 False 且日志是 timed out
            assert ear.ensure_transcriber_ready(model_loaded_wait_s=5) is False
        assert "worker error" in caplog.text

    def test_branch3_script_up_model_never_loaded_false(self):
        """分支3: 脚本拉活但模型恒未载 → 门拦 False (owned 仍 True 收尸)。"""
        ear = KaisEar(caller="kap:test")
        alive = {"ok": False}

        def _http(url, payload=None, timeout=30.0):
            if url == kais_ear_mod.HYBRID_HEALTH_URL:
                if not alive["ok"]:
                    return 0, "refused"
                # 脚本 wait_ready 已过 (进程活) 但模型仍在载/载不动
                return 200, {"status": "loading", "model_loaded": False}
            return 0, "kap refused"

        with mock.patch.object(KaisEar, "_http_json", side_effect=_http), \
                mock.patch("subprocess.run") as run:
            run.side_effect = lambda *a, **k: alive.__setitem__(
                "ok", True) or mock.Mock(returncode=0)
            assert ear.ensure_transcriber_ready(
                timeout_s=30, model_loaded_wait_s=1) is False
        # 兜底拉起即 own — 门失败也要 stop_if_owned 收尸还 VRAM
        assert ear._hybrid_owned is True

    def test_budget_constant_floor(self):
        """默认预算 660s 且 ≥600s (判定引擎教训: 重入冷启 ~8min)。"""
        assert kais_ear_mod.HYBRID_MODEL_LOADED_BUDGET_S == 660
        assert kais_ear_mod.HYBRID_MODEL_LOADED_BUDGET_S >= 600


# ══ deprecated shim (qwen_ear.py) ════════════════════════════════════


class TestDeprecatedShim:
    def test_shim_reexports(self):
        from plugins.kais_aigc import qwen_ear as shim

        # import * 面真源重导出; QwenEar 别名锚定同一类
        assert shim.QwenEar is KaisEar
        assert shim.ENGINE_NAME == "kais-ear"
        assert shim.KAP_EAR_SH == kais_ear_mod.KAP_EAR_SH
        assert shim.KAP_HYBRID_SH == kais_ear_mod.KAP_HYBRID_SH

    def test_legacy_import_path_still_works(self):
        """旧消费方 import 形态零破坏 (from …qwen_ear import QwenEar)。"""
        from plugins.kais_aigc.qwen_ear import QwenEar

        ear = QwenEar(caller="legacy:consumer")
        assert isinstance(ear, KaisEar)
        assert hasattr(ear, "transcribe")  # 双后端面随 shim 可达
