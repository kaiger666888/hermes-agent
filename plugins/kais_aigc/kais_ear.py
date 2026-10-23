"""kais_ear.py — kais-ear: 统一语音引擎, 双后端 (hybrid 转写 + Omni 听审).

Kai 0927 架构令 (verbatim): 「fw（批量）+ hybrid :8012（流式）和 Omni 统一
放入 qwen-ear asr，要结合 whisper 和 R2T2 实现最准确的语音识别；Omni 还是
负责情感；并将 qwen-ear 更名为 kais-ear。」本文件即更名后的实现真源;
旧 ``qwen_ear.py`` 已 shim 化 (``from kais_ear import *``), 消费方零破坏。

双后端架构:
  - 转写后端 (fidelity/ASR) — hybrid-asr sidecar :8012: R2T2 流式草稿 +
    fw(whisper large-v3) 终稿, v2c 截断症状门选择 (macro CER 0.1155 定谳,
    Kai 人耳盲选 3:1 胜)。秒级懒加载/TTL 900s 自卸载, 替代旧「Omni 转写
    prompt 链」——后者 21.5GB 驻留 + 7min 冷启是 p10c/p11c「引擎窗抢不到
    烧预算」死因族 (定谳依据已 merged KAP main 5c2cebad)。
    入口 :meth:`KaisEar.transcribe`; 文本真源 = 响应 ``final`` 字段
    (``draft`` 兜底)。
  - 听审后端 (emotion/speaker/QA) — Qwen3-Omni-30B-A3B :8126: 只服务
    情绪/说话人等听审维度与文本问答, :meth:`listen` / :meth:`ask` 保留
    (自 qwen_ear.py 平移, 语义零变化)。

hybrid 生命周期 (sidecar 2026-09-25 已收编 KAP GpuScheduler, systemd 退役;
真源 /data/workspace/hybrid-asr-server/DELIVERY.md §8 — 本仓是消费方, 只读):
  1. ``transcribe()`` 经 KAP :10588 ``/api/production/hybridAsr/transcribe``
     —— 转发前 ensure 内嵌 (GpuScheduler allocate → 拉起/排队/互相驱逐),
     503 allocate-not-granted = GPU 队列拒绝 → 绝不绕队直跑 (Kai 0925 令,
     qwen-eye 73-02 F21 同款)。全程经 KAP 还刷新调度器空闲钟 (idleTimeoutMs
     10min 自卸载不被旁路饿死误杀)。
  2. KAP 宕机/病坏 (status 0 / 网络异常 / 5xx 非 503) → 回落
     ``kap-hybrid-asr.sh start`` 直启兜底 (VRAM 预检 NEED_MB=12000 + 420s
     等待窗在脚本内), 直连 :8012 重试一次。仅此路径 ``_hybrid_owned=True``
     (stop_if_owned 走脚本 stop 归还 VRAM)。
  3. ``/health`` 三态 ok/idle/loading 任一即活 (懒加载语义, 探针永不抛)。
     经 KAP 取得的 hybrid 归 GpuScheduler 管 (两层空闲卸载: 调度器 10min
     整服务退场 + sidecar 内 TTL 900s 杀 worker) —— 不 own 不停。
     (0927 ensure-hardening: 「三态活」只证进程在 — ``ensure_transcriber_ready``
     的就绪判定另过 model_loaded 门: status=loading 下 worker 可半途 OOM
     自毁, 不再据此放行; 详见该方法 docstring。)

Omni (:8126) 生命周期: 沿用 2026-09-27 收编批语义 (KAP ear allocate 租约
→ 宕机兜底 kap-ear.sh → server.log 死因检测; release 失败回落脚本 stop),
详见 :meth:`ensure_ready` / :meth:`stop_if_owned`。

GPU 关系: Omni ~19.9GB 与 qwen-eye (:8125) 单卡互斥 (KAP 队列裁决);
hybrid ~11.6GB 驻 QC_GEN2 卡 (gpu.conf hybrid_asr_role)。两后端各自走
中央调度, 本引擎不再有任何私有 GPU 旁路。

Failure modes:
  - hybrid KAP 队列拒绝 → RuntimeError (不绕队; 调用方 fail-closed)。
  - hybrid 双路皆不通 → RuntimeError; sidecar 503 (worker 死) 由 KAP
    ensureVram/懒复活自愈, 客户端重试即可。
  - Omni: ComfyUI 渲染期 VRAM 不足 → kap-ear.sh 条件等待 280s fail-fast;
    端口冲突 (8126 被占) → wait_ready 检测 server died → 报错。
"""

from __future__ import annotations

import base64
import json
import logging
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ENGINE_NAME = "kais-ear"
"""Canonical engine name — written into every returned payload.
(2026-09-27 更名批: qwen-ear → kais-ear; 旧名仅存于历史交付物。)"""

# ── 听审后端 (Omni :8126) — 自 qwen_ear.py 平移, 常量名保留 shim 兼容 ──

EAR_API = "http://127.0.0.1:8126/v1/chat/completions"
EAR_HEALTH = "http://127.0.0.1:8126/health"
KAP_EAR_SH = "/opt/qwen-ear/kap-ear.sh"
SERVER_LOG = "/opt/qwen-ear/server.log"

# KAP 中央调度 API (GpuScheduler front-end; 路由真源
# kais-aigc-platform/src/routes/production/ear/index.ts — 响应 {code,data,
# message} 包装, data.granted 为授权判据)。KAP 全宕机时回落 kap-ear.sh 直启。
KAP_ALLOCATE_URL = "http://127.0.0.1:10588/api/production/ear/allocate"
KAP_RELEASE_URL = "http://127.0.0.1:10588/api/production/ear/release"

EAR_START_TIMEOUT_S = 900   # allocate 冷启动含 NTFS 模型加载 (服务端 600s) + 兜底脚本冷读
EAR_CALL_TIMEOUT_S = 300    # 单条音频 ~10s → 推理几秒; 长音频留余量

# ── 转写后端 (hybrid-asr :8012 / KAP :10588) ────────────────────────────
# 契约真源: hybrid-asr-server/hybrid_server.py + KAP hybridAsr/{transcribe,
# status} 路由 (kais-aigc-platform/src/routes/production/hybridAsr/)。

HYBRID_TRANSCRIBE_API = "http://127.0.0.1:8012/transcribe"
HYBRID_HEALTH_URL = "http://127.0.0.1:8012/health"
KAP_HYBRID_TRANSCRIBE_URL = (
    "http://127.0.0.1:10588/api/production/hybridAsr/transcribe"
)
#: 纯探针路由 (不触调度器) — 仅用来判 KAP 进程是否活着 (拉起决策分支)。
KAP_HYBRID_STATUS_URL = "http://127.0.0.1:10588/api/production/hybridAsr/status"
KAP_HYBRID_SH = "/data/workspace/hybrid-asr-server/kap-hybrid-asr.sh"

#: 转写超时底线 600s 对齐 KAP 路由 forward 底线 (冷启 40-90s + 整段流式
#: 转写 + fw 逐窗重转写), 客户端再留 60s 余量防「KAP 刚答客户端先断」。
HYBRID_TRANSCRIBE_TIMEOUT_S = 660
#: 兜底脚本预算: 脚本内 DEADLINE_S=420 (VRAM 窗口等待+冷读) + WAIT_S=180
#: (wait_ready) — subprocess 上限给足 600s; 其后 health 轮询 60s 兜底。
HYBRID_SCRIPT_TIMEOUT_S = 600
_HYBRID_POLL_INTERVAL_S = 3
_HYBRID_POST_SCRIPT_POLL_S = 60

#: /health 三态任一即活 (DELIVERY §8.1: idle=待命/loading=冷启中都不是病)。
_HYBRID_ALIVE_STATES = frozenset({"ok", "idle", "loading"})

#: model_loaded 门预算 (0927 ensure-hardening 批): ensure 分支1/3 命中而
#: 模型未载时, 轮询 /health 至 model_loaded=true 的上限。判定引擎内存教训:
#: 重入冷启实测 ~8min, 240s 超时判死非质量 → 预算必须 ≥600s; 取 600s + 60s
#: 余量 = 660s (与 HYBRID_TRANSCRIBE_TIMEOUT_S 同刻度)。调小仅限测试。
HYBRID_MODEL_LOADED_BUDGET_S = 660

_LOAD_FAIL_RE = re.compile(
    r"failed to load model|model loading error",
)


def _summarize_hybrid_health(body: dict) -> str:
    """Compact /health forensics summary (运维取证用, 进 WARNING 日志)."""
    return (f"status={body.get('status')!r} "
            f"model_loaded={body.get('model_loaded')!r} "
            f"error={body.get('error')!r}")

# 音频大小软上限 (base64 前) — 超 8MB 的 wav 先截断/转码再送 (Omni 路径)
_AUDIO_MAX_BYTES = 8 * 1024 * 1024

__all__ = [
    "ENGINE_NAME", "KaisEar", "QwenEar",
    "EAR_API", "EAR_HEALTH", "KAP_EAR_SH", "SERVER_LOG",
    "KAP_ALLOCATE_URL", "KAP_RELEASE_URL",
    "EAR_START_TIMEOUT_S", "EAR_CALL_TIMEOUT_S",
    "HYBRID_TRANSCRIBE_API", "HYBRID_HEALTH_URL",
    "KAP_HYBRID_TRANSCRIBE_URL", "KAP_HYBRID_STATUS_URL", "KAP_HYBRID_SH",
    "HYBRID_TRANSCRIBE_TIMEOUT_S", "HYBRID_SCRIPT_TIMEOUT_S",
    "HYBRID_MODEL_LOADED_BUDGET_S",
]


class KaisEar:
    """kais-ear — 统一语音引擎: hybrid 转写 (:8012) + Omni 听审 (:8126).

    One instance per caller identity. The ``caller`` string flows into the
    KAP allocate/release lease for GPU-scheduler attribution (Omni 后端;
    hybrid 后端的 KAP 路由不透传 caller, 由路由侧固定归属)。
    Thread-unsafe by design — phases drive it sequentially (与 qwen-eye
    同约定)。
    """

    def __init__(self, caller: str = "pipeline:kais-ear"):
        self.caller = caller
        self._owned = False         # Omni: True iff WE brought :8126 up
        self._hybrid_owned = False  # hybrid: True iff 兜底脚本拉起 (KAP 管的不算)

    # ── HTTP plumbing (双后端共用) ────────────────────────────────────

    @staticmethod
    def _http_json(url: str, payload: dict | None = None,
                   timeout: float = 30.0) -> tuple[int, Any]:
        """Minimal JSON POST/GET. Returns (status, parsed-body-or-None)."""
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read().decode() or "null")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:300] if exc.fp else ""
            return exc.code, body
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return 0, str(exc)[:300]

    @classmethod
    def _health_ok(cls, timeout: float = 5.0) -> bool:
        status, _ = cls._http_json(EAR_HEALTH, timeout=timeout)
        return status == 200

    # ── 转写后端 (hybrid-asr :8012, 2026-09-27 更名批接入) ───────────

    @classmethod
    def _hybrid_health(cls, timeout: float = 5.0) -> dict | None:
        """/health body; None = 不可达/非200/畸形 (探针永不抛)."""
        status, body = cls._http_json(HYBRID_HEALTH_URL, timeout=timeout)
        if status == 200 and isinstance(body, dict):
            return body
        return None

    @classmethod
    def _hybrid_alive(cls, timeout: float = 5.0) -> bool:
        """:8012 三态判活 (ok/idle/loading 任一; 探针永不抛 → 200 即进程在)."""
        body = cls._hybrid_health(timeout=timeout)
        return body is not None and body.get("status") in _HYBRID_ALIVE_STATES

    def _wait_hybrid_alive(self, budget_s: float) -> bool:
        deadline = time.monotonic() + budget_s
        while time.monotonic() < deadline:
            if self._hybrid_alive():
                return True
            time.sleep(_HYBRID_POLL_INTERVAL_S)
        return False

    def _wait_model_loaded(self, budget_s: float, *, gate: str,
                           first_body: dict | None = None) -> bool:
        """model_loaded 门: sidecar 活 ≠ 可转写, 等模型真载完才放行.

        0927 13:10 首打实证: ensure 按「三态活即 True」放行时, sidecar 实处
        status=loading/model_loaded=false, 8188 渲染驻留 (22.4G) 挤爆 worker
        (torch.OutOfMemoryError → WorkerGoneError → 自毁 ECONNREFUSED) →
        transcribe 3×503 → p10c all-clips error 白烧一次回滚预算。本门把
        分支1/3 的 True 钉死在 ``model_loaded=true``; 耗尽/worker error →
        False (fail-closed)。Never raises。
        """
        deadline = time.monotonic() + budget_s
        started = time.monotonic()
        info_logged = False
        body = first_body
        last_summary = "health unreachable"
        while True:
            if body is None:
                body = self._hybrid_health()
            if body is not None:
                last_summary = _summarize_hybrid_health(body)
                if body.get("model_loaded") is True:
                    return True
                if body.get("error"):
                    logger.warning(
                        "kais-ear: hybrid worker error while waiting for "
                        "model_loaded (%.1fs elapsed, gate=%s): %s",
                        time.monotonic() - started, gate, last_summary,
                    )
                    return False
            now = time.monotonic()
            if now >= deadline:
                break
            if not info_logged:
                info_logged = True
                logger.info(
                    "kais-ear: hybrid sidecar up but model not loaded (%s) "
                    "— waiting up to %.0fs (gate=%s)",
                    last_summary, budget_s, gate,
                )
            time.sleep(min(_HYBRID_POLL_INTERVAL_S, deadline - now))
            body = None  # 下一轮重新实读
        logger.warning(
            "kais-ear: hybrid model_loaded gate timed out after %.1fs "
            "(budget=%.0fs, gate=%s) — last health: %s",
            time.monotonic() - started, budget_s, gate, last_summary,
        )
        return False

    def ensure_transcriber_ready(
        self, timeout_s: int = HYBRID_SCRIPT_TIMEOUT_S,
        model_loaded_wait_s: int | None = None,
    ) -> bool:
        """hybrid 转写后端就绪判定 (三态 + model_loaded 门).

        1. sidecar 三态活 → model_loaded 门 (0927 ensure-hardening 批):
           ``model_loaded=true`` → 立即 True (热路径零等待, 语义不变);
           否则轮询 /health 至 loaded (预算 ``model_loaded_wait_s``, 缺省
           :data:`HYBRID_MODEL_LOADED_BUDGET_S`), 预算耗尽 / health 持续
           不可达 / worker error → False。三态活只证「进程在」— 实证
           status=loading 下 worker 可半途 OOM 自毁, 「活」≠「可转写」。
           借用预存服务, 不 own — 后续 transcribe 经 KAP 刷新调度器空闲钟。
        2. KAP 进程可达 (hybridAsr/status 纯探针) → True: 拉起/排队/拒绝
           由 transcribe() 首打的内嵌 ensure 裁决 (503 拒绝如实上抛, 绝不
           绕队)。hybrid-asr 无独立 allocate 路由 — ensure 载体就是
           transcribe 转发本身 (DELIVERY §8.3 消费端契约)。
        3. KAP 宕机 → kap-hybrid-asr.sh start 直启兜底 (VRAM 预检+等待窗
           脚本内含) + health 轮询; 活 → ``_hybrid_owned=True`` (门失败也
           own — stop_if_owned 收尸还 VRAM) + 同过 model_loaded 门 (脚本
           wait_ready 返回时模型可能仍在载)。

        Never raises. 调用方 (p10c) 对 False 走 AudioEngineUnavailable
        fail-closed。
        """
        budget_s = float(
            HYBRID_MODEL_LOADED_BUDGET_S if model_loaded_wait_s is None
            else model_loaded_wait_s
        )
        body = self._hybrid_health()
        if body is not None and body.get("status") in _HYBRID_ALIVE_STATES:
            return self._wait_model_loaded(
                budget_s, gate="branch1:sidecar-alive", first_body=body,
            )
        kap_status, _ = self._http_json(KAP_HYBRID_STATUS_URL, timeout=5.0)
        if kap_status > 0:
            logger.info(
                "kais-ear: hybrid sidecar down, KAP reachable (HTTP %s) — "
                "拉起交 transcribe 内嵌 ensure (排队/拒绝由调度器裁决)",
                kap_status,
            )
            return True
        logger.info(
            "kais-ear: KAP unreachable (HTTP %s) — fallback to %s start",
            kap_status, KAP_HYBRID_SH,
        )
        try:
            subprocess.run(
                ["bash", KAP_HYBRID_SH, "start"],
                capture_output=True, timeout=float(timeout_s),
            )
        except (subprocess.SubprocessError, OSError):
            logger.warning("kais-ear: kap-hybrid-asr.sh start failed",
                           exc_info=True)
        if self._wait_hybrid_alive(_HYBRID_POST_SCRIPT_POLL_S):
            self._hybrid_owned = True
            return self._wait_model_loaded(
                budget_s, gate="branch3:script-fallback")
        return False

    def transcribe(self, audio_path: Path | str, *,
                   language: str = "Chinese",
                   timeout_s: int = HYBRID_TRANSCRIBE_TIMEOUT_S) -> dict:
        """转写一条音频 (hybrid v2c: R2T2 流式草稿 + fw 终稿).

        Args:
            audio_path: 绝对路径 (.wav/.mp3 — sidecar 400 校验的本地镜像,
                fail-fast 不发 HTTP)。
            language: 透传 sidecar (默认 Chinese)。
            timeout_s: ≥600s 底线对齐 KAP 路由转发超时。

        Returns:
            sidecar payload dict: ``{draft, final, sent_windows, fw_calls,
            first_text_s, per_sentence, timings}`` — 文本真源 = ``final``
            (空时 ``draft`` 兜底)。

        Raises:
            ValueError: 路径/后缀不合法 (400 同语义)。
            RuntimeError: KAP 队列拒绝 (503, 不绕队) 或双路皆不通。
        """
        path = Path(audio_path)
        if path.suffix.lower() not in (".wav", ".mp3"):
            raise ValueError(
                f"kais-ear transcribe only accepts .wav/.mp3, "
                f"got {path.suffix}")
        if not path.is_file():
            raise ValueError(f"kais-ear transcribe: audio_path 不存在: {path}")
        payload = {"audio_path": str(path.resolve()), "language": language}

        # 1) KAP 路由 — ensure(拉起/排队/驱逐)+转发+空闲钟刷新一体。
        status, body = self._http_json(
            KAP_HYBRID_TRANSCRIBE_URL, payload=payload,
            timeout=float(timeout_s),
        )
        if status == 200 and isinstance(body, dict):
            data = body.get("data") if isinstance(body.get("data"), dict) \
                else body
            if isinstance(data, dict) and data:
                return data
            last_err = f"KAP 200 malformed body: {str(body)[:200]}"
        elif status == 503:
            # allocate-not-granted = GPU 队列说不行 — 绝不绕队直跑
            # (Kai 0925 令; qwen-eye 73-02 F21 同款)。
            raise RuntimeError(
                f"kais-ear hybrid: KAP 队列拒绝 (不绕队): {str(body)[:180]}")
        elif status == 400:
            raise ValueError(f"kais-ear hybrid: 400 {str(body)[:180]}")
        else:
            last_err = f"KAP HTTP {status}: {str(body)[:200]}"

        # 2) KAP 宕机/病坏 (0/网络/5xx) → 脚本直启兜底 + 直连 :8012 一次。
        #    sidecar 已活 (KAP 单方面病坏) 则免脚本直接重试。
        if not self._hybrid_alive():
            try:
                subprocess.run(
                    ["bash", KAP_HYBRID_SH, "start"],
                    capture_output=True, timeout=float(HYBRID_SCRIPT_TIMEOUT_S),
                )
            except (subprocess.SubprocessError, OSError):
                logger.warning("kais-ear: kap-hybrid-asr.sh start failed",
                               exc_info=True)
            if not self._wait_hybrid_alive(_HYBRID_POST_SCRIPT_POLL_S):
                raise RuntimeError(
                    f"kais-ear hybrid transcribe failed: {last_err}")
            self._hybrid_owned = True  # 兜底拉起 → 我们 own, stop_if_owned 收
        status, body = self._http_json(
            HYBRID_TRANSCRIBE_API, payload=payload, timeout=float(timeout_s),
        )
        if status == 200 and isinstance(body, dict) and body:
            return body
        raise RuntimeError(
            f"kais-ear hybrid transcribe failed: HTTP {status}: "
            f"{str(body)[:200]}")

    # ── 听审后端 (Omni :8126) 生命周期 — 收编批语义平移 ───────────────

    @staticmethod
    def _server_log_load_failed(offset: int) -> bool:
        try:
            with open(SERVER_LOG, "rb") as fh:
                fh.seek(offset)
                tail = fh.read(2_000_000)
        except OSError:
            return False
        return bool(_LOAD_FAIL_RE.search(tail.decode(errors="replace")))

    @staticmethod
    def _server_log_size() -> int:
        try:
            return Path(SERVER_LOG).stat().st_size
        except OSError:
            return 0

    def ensure_ready(self, timeout_s: int = EAR_START_TIMEOUT_S) -> tuple[bool, bool]:
        """Bring the Omni (:8126) server up. Returns ``(healthy, started_by_us)``.

        Never raises. 先走 KAP 中央调度 (排队 + 互相驱逐 + 拉起), KAP 宕机
        才回落 kap-ear.sh 直启; 队列说不行绝不绕队 (qwen-eye 同款)。VRAM
        预检在 GpuScheduler/kap-ear.sh 内部, 这里只做 log 死因检测避免盲
        轮询 (Guard 2)。
        """
        if self._health_ok():
            return True, False

        log_offset = self._server_log_size()
        allocated = False
        kap_unreachable = False
        alloc_status = 0
        try:
            alloc_status, body = self._http_json(
                KAP_ALLOCATE_URL,
                payload={"caller": self.caller},
                timeout=float(timeout_s),
            )
            allocated = alloc_status == 200 and isinstance(body, dict) and (
                (body.get("data") or {}).get("granted") is True
            )
        except Exception:  # noqa: BLE001 — allocate is best-effort
            kap_unreachable = True
            logger.warning("kais-ear: KAP allocate failed", exc_info=True)
        if not allocated:
            # 分两种 "allocate 没成" (qwen-eye 73-02 F21 同款):
            #   a) 队列显式拒绝 (200 granted=false / 4xx): GPU 队列说不行,
            #      绝不绕队直跑 — 私有旁路禁再犯 (Kai 0925 令)。
            #   b) KAP 不可达 (status 0 / 网络异常 / 5xx): 旧脚本直启兜底。
            queue_refused = alloc_status == 200 or 400 <= alloc_status < 500
            if not kap_unreachable and queue_refused:
                logger.warning(
                    "kais-ear: allocate refused by KAP queue (HTTP %s) — "
                    "no bypass start (GPU 队列优先级必须尊重)", alloc_status,
                )
                return False, False
            logger.info(
                "kais-ear: KAP unreachable (HTTP %s) — fallback to %s start",
                alloc_status, KAP_EAR_SH,
            )
            try:
                subprocess.run(
                    ["bash", KAP_EAR_SH, "start"],
                    capture_output=True, timeout=timeout_s,
                )
            except (subprocess.SubprocessError, OSError):
                logger.warning("kais-ear: kap-ear.sh start failed",
                               exc_info=True)

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._health_ok():
                # 经队列取得或兜底拉起都算我们启动的 (用完即还/停);
                # 快路径 (服务已在跑) 在上方已提前返回, 不会到这里。
                self._owned = True
                return True, True
            if self._server_log_load_failed(log_offset):
                logger.warning(
                    "kais-ear: model load failed (see %s), giving up",
                    SERVER_LOG,
                )
                return False, True
            time.sleep(3)
        return False, True

    def stop_if_owned(self) -> None:
        """按后端归属收尾 (幂等). Never raises.

        hybrid: 仅兜底脚本拉起的才 stop (kap-hybrid-asr.sh stop 归还
        ~11.6G VRAM); 经 KAP GpuScheduler 取得的归调度器管 (idleTimeoutMs
        10min 整服务退场 + sidecar TTL 900s 两层自卸载) — 不 own 不停。
        Omni: 收编批语义 — owned 先 KAP release (解除服务级占用唤醒排队的
        重型引擎 + 停服务); release 失败回落 kap-ear.sh stop 兜底一次。快
        路径借用的预存服务不 own, 绝不碰。
        """
        if self._hybrid_owned:
            self._hybrid_owned = False
            try:
                subprocess.run(
                    ["bash", KAP_HYBRID_SH, "stop"],
                    capture_output=True, timeout=60,
                )
            except (subprocess.SubprocessError, OSError):
                logger.warning("kais-ear: kap-hybrid-asr.sh stop failed",
                               exc_info=True)
        if not self._owned:
            return
        self._owned = False
        try:
            status, _ = self._http_json(
                KAP_RELEASE_URL, payload={"caller": self.caller},
                timeout=60.0,
            )
            if status == 200:
                return
            logger.warning(
                "kais-ear: KAP release HTTP %s — falling back to script stop",
                status,
            )
        except Exception:  # noqa: BLE001 — release is best-effort
            logger.warning(
                "kais-ear: KAP release failed — falling back to script stop",
                exc_info=True,
            )
        try:
            subprocess.run(
                ["bash", KAP_EAR_SH, "stop"],
                capture_output=True, timeout=60,
            )
        except (subprocess.SubprocessError, OSError):
            logger.warning("kais-ear: kap-ear.sh stop failed", exc_info=True)

    # ── 听审后端 chat calls (Omni :8126) ─────────────────────────────

    def _call_llm(self, messages: list[dict], max_tokens: int) -> str:
        """One chat completion. One retry on transient failure."""
        body = {
            "model": "qwen3-omni",
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": messages,
        }
        last_err: str = ""
        for attempt in range(2):
            status, resp = self._http_json(
                EAR_API, payload=body, timeout=EAR_CALL_TIMEOUT_S,
            )
            if status == 200 and isinstance(resp, dict):
                txt = ((resp.get("choices") or [{}])[0]
                       .get("message", {}).get("content") or "").strip()
                if txt:
                    return txt
                last_err = f"empty content (status={status})"
            else:
                last_err = f"HTTP {status}: {str(resp)[:200]}"
            if attempt == 0:
                time.sleep(5)
        raise RuntimeError(f"kais-ear LLM call failed: {last_err}")

    @staticmethod
    def _b64(path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode()

    # ── 听审后端 audio layer (Omni :8126) ────────────────────────────

    def listen(self, audio_path: Path, question: str,
               max_tokens: int = 2000) -> str:
        """Listen to ONE audio clip + answer a question in a single call.

        format 硬约束 (server-common.cpp:1015): 只认 wav/mp3。
        其他格式 (ogg/flac/…) 必须先转 wav — 调用方负责。
        """
        if audio_path.suffix.lower() not in (".wav", ".mp3"):
            raise ValueError(
                f"kais-ear listen only accepts .wav/.mp3, "
                f"got {audio_path.suffix}")
        if audio_path.stat().st_size > _AUDIO_MAX_BYTES:
            raise ValueError(
                f"audio too large ({audio_path.stat().st_size} bytes > "
                f"{_AUDIO_MAX_BYTES}); trim or downsample first")
        messages = [{"role": "user", "content": [
            {"type": "input_audio", "input_audio": {
                "data": self._b64(audio_path),
                "format": "wav" if audio_path.suffix.lower() == ".wav" else "mp3",
            }},
            {"type": "text", "text": question},
        ]}]
        return self._call_llm(messages, max_tokens=max_tokens)

    # ── 听审后端 judgement / QA layer (text mode) ────────────────────

    def ask(self, text_prompt: str, max_tokens: int = 800) -> str:
        """Text-mode question over :8126 (no audio)."""
        return self._call_llm(
            [{"role": "user", "content": text_prompt}], max_tokens=max_tokens,
        )


#: Deprecated alias — qwen_ear.py shim 的消费方 (``from …qwen_ear import
#: QwenEar``) 经 ``import *`` 拿到本名; 新代码一律用 :class:`KaisEar`。
QwenEar = KaisEar
