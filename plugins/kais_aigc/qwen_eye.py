"""qwen_eye.py — qwen-eye: 本地 Qwen3.8-27B VL 视觉判定引擎 (:8125).

DEPRECATED for IMAGE verification/description since 2026-08-27 (Kai verdict):
use plugins.kais_aigc.vision_verify (default engine glm-5.3-flash hosted).
Retained ONLY for (a) the vision_verify LOCAL arm when explicitly configured,
and (b) video-analysis consumers (e.g. p11c video_qc).

Shared engine layer extracted from p11c_video_qc (2026-08-15 experiment:
``/home/kai/shared/qwen-eye-exp/EXPERIMENT.md`` — 28-task validated:
negative controls 8/8 intercepted, repeat judgements 7/7 identical). The
business prompts (OBS/JUDGE) stay in the phases; this module owns ONLY
the engine lifecycle + the HTTP call shape.

Lifecycle (按需 LLM 政策):
  1. KAP allocate: POST :10588/api/production/llm/allocate
     {"variantId": "q4", "caller": "<caller>"} (GpuScheduler lease).
  2. Fallback when KAP is down: ``/opt/qwen-llm/kap-llm.sh start q4``.
  3. Health poll :8125/health ≤120s.
  4. ``stop_if_owned()`` stops ONLY a server WE started — a pre-existing
     server belongs to whoever started it (e.g. the KAP scheduler's own
     lease) and is NEVER touched.

Fail-fast (2026-08-15 验收缺陷: 模型加载 OOM 时轮询盲转满 120s):
  - Guard 1 (allocate 前): GPU1 free VRAM < ``_VRAM_MIN_FREE_MIB`` →
    skip start entirely, ``(False, False)``. nvidia-smi 不可用时
    fail-open (视为满足, 不挡启动路径)。
  - Guard 2 (轮询中): server.log 自启动前 offset 起的新增内容出现
    load 失败字样 → 立即放弃, ``(False, True)``。

Observation-layer hard constraint (llama.cpp multi-image drop bug,
experiment 17:55): ONE user message PER image. A single user message
carrying N images silently drops all but ceil(N/2). Consecutive user
messages are legal. Each image message carries a "(帧i/N)" tail tag.

Thinking MUST be disabled (``chat_template_kwargs.enable_thinking=False``)
— otherwise thinking eats the entire max_tokens budget and the content
comes back empty.
"""

from __future__ import annotations

import base64
import fcntl
import json
import logging
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ENGINE_NAME = "qwen-eye"
"""Canonical engine name — written into every returned payload."""

# KAP allocate API (GpuScheduler front-end). Falls back to a direct
# kap-llm.sh start when KAP is down.
KAP_ALLOCATE_URL = "http://127.0.0.1:10588/api/production/llm/allocate"
# GPU 接力补全 (2026-08-23 钟馗 ep p11a 死循环修复): 渲染后 WAN 权重常驻
# GPU1 → llama-server VRAM 预检必败 → 裁决1 fail-closed 整段 REJECT。渲染与
# 审核按"串行独占"接力：起审前卸掉 ComfyUI 模型（下一镜渲染自动重载）。
COMFYUI_FREE_URL = "http://127.0.0.1:8188/free"


def _unload_comfyui_models() -> None:
    """POST /free (unload_models) — best-effort, never raises."""
    try:
        data = json.dumps({"unload_models": True, "free_memory": True}).encode()
        req = urllib.request.Request(
            COMFYUI_FREE_URL, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            resp.read()
    except Exception:  # noqa: BLE001 — relay is best-effort
        logger.warning("qwen-eye: ComfyUI /free failed", exc_info=True)


def _wait_vram_freed(
    need_mib: int | None = None,
    timeout_s: float = 45.0,
    poll_s: float = 3.0,
) -> None:
    """等 ComfyUI 异步卸载落地：VRAM 到阈值，或 2 个周期无增长即止。"""
    if need_mib is None:
        need_mib = _VRAM_MIN_FREE_MIB
    best = QwenEye._vram_free_mib()
    if best is None:
        return
    deadline = time.monotonic() + timeout_s
    last = -1
    while time.monotonic() < deadline and best < need_mib:
        if best <= last:  # 连续两次无增长 → 卸载已尽
            break
        last = best
        time.sleep(poll_s)
        now = QwenEye._vram_free_mib()
        if now is not None:
            best = now
LLM_API = "http://127.0.0.1:8125/v1/chat/completions"
LLM_HEALTH = "http://127.0.0.1:8125/health"
KAP_LLM_SH = "/opt/qwen-llm/kap-llm.sh"

LLM_START_TIMEOUT_S = 120
LLM_CALL_TIMEOUT_S = 3600  # CPU-mode fallback can take ~5.5min per call

# ── fail-fast guards (2026-08-15 验收缺陷) ─────────────────────────────
# ComfyUI 渲染占满 GPU1 时模型加载必 OOM — 盲拉起只会让 health 轮询空转
# 满 120s。两道闸: 启动前 VRAM 预检 + 轮询中 server.log 死因检测。
SERVER_LOG = "/opt/qwen-llm/server.log"
# 2026-08-23: q3 共存档已退役（kap-llm.sh q4-only, 17.9GB 独占 GPU1）——
# 阈值按 q4 校准。variantId 同步 q3→q4（原 q3 申请注定 allocate fail）。
_VRAM_MIN_FREE_MIB = 19000  # q4 = UD-Q4_K_XL 17.9GB, 留 buffer
_VRAM_GPU_INDEX = 1  # RTX 3090, CUDA_VISIBLE_DEVICES=1
_LOAD_FAIL_RE = re.compile(
    r"failed to load model|model loading error",
)


class QwenEye:
    """qwen-eye — local Qwen3.8-27B VL vision-judgement engine (:8125).

    One instance per caller identity (the ``caller`` string flows into
    the KAP allocate lease for GPU-scheduler attribution). Thread-unsafe
    by design — phases drive it sequentially.
    """

    def __init__(self, caller: str = "kap:qwen_eye"):
        self.caller = caller
        self._owned = False  # True iff WE brought the server up

    # ── HTTP plumbing (module-level so tests can patch one shared copy) ──

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
        status, _ = cls._http_json(LLM_HEALTH, timeout=timeout)
        return status == 200

    # ── Lifecycle ─────────────────────────────────────────────────────

    @staticmethod
    def _vram_free_mib() -> int | None:
        """Free VRAM (MiB) on the qwen-eye GPU, or None when nvidia-smi is
        unavailable/fails (fail-open: the check must never block startup)."""
        try:
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free",
                 "--format=csv,noheader,nounits",
                 "-i", str(_VRAM_GPU_INDEX)],
                capture_output=True, text=True, timeout=10,
            )
            return int(proc.stdout.strip().splitlines()[0])
        except (subprocess.SubprocessError, OSError, ValueError, IndexError):
            return None

    @staticmethod
    def _server_log_load_failed(offset: int) -> bool:
        """True when the server.log tail added since *offset* shows a fatal
        model-load failure (OOM'd llama-server exits repeatedly). Returns
        False when the log is unreadable — detection is best-effort."""
        try:
            with open(SERVER_LOG, "rb") as fh:
                fh.seek(offset)
                tail = fh.read(2_000_000)  # cap: only the recent window matters
        except OSError:
            return False
        return bool(_LOAD_FAIL_RE.search(tail.decode(errors="replace")))

    @staticmethod
    def _server_log_size() -> int:
        """Current server.log size — the offset from which Guard 2 reads.
        0 when the log doesn't exist yet (detection simply starts at the
        top of the fresh file the launch creates)."""
        try:
            return Path(SERVER_LOG).stat().st_size
        except OSError:
            return 0

    def ensure_ready(self, timeout_s: int = LLM_START_TIMEOUT_S) -> tuple[bool, bool]:
        """Bring the qwen-eye server up. Returns ``(healthy, started_by_us)``.

        ``started_by_us`` is False when the server was ALREADY healthy
        before allocate, in which case the caller must NOT stop it after
        the batch (用完即停 only applies to what we started). Never raises.

        Fail-fast (2026-08-15): a model-load OOM is a hard unavailability —
        pre-check VRAM before allocating, and abandon the health poll the
        moment the server log records a load failure, so the caller falls
        through to the next engine instead of idling out the full timeout.
        """
        if self._health_ok():
            return True, False

        # Guard 1 — VRAM pre-check. Must run AFTER the health check: an
        # already-running q4 leaves GPU1 below the threshold by itself.
        free_mib = self._vram_free_mib()
        if free_mib is not None and free_mib < _VRAM_MIN_FREE_MIB:
            # GPU 接力 (2026-08-23): 渲染权重常驻时先卸 ComfyUI 模型再复检
            # ——串行独占策略下起审前必须腾出 GPU1（下一镜渲染自动重载）。
            # /free 是异步的：卸 GB 级权重要数秒，轮询等到阈值或稳定。
            _unload_comfyui_models()
            _wait_vram_freed()
            free_mib = self._vram_free_mib()
        if free_mib is not None and free_mib < _VRAM_MIN_FREE_MIB:
            logger.warning(
                "qwen-eye: insufficient VRAM (free=%d MiB < %d), skipping start",
                free_mib, _VRAM_MIN_FREE_MIB,
            )
            return False, False

        log_offset = self._server_log_size()
        allocated = False
        kap_unreachable = False
        alloc_status = 0
        try:
            alloc_status, body = self._http_json(
                KAP_ALLOCATE_URL,
                payload={"variantId": "q4", "caller": self.caller},
                timeout=60.0,
            )
            allocated = alloc_status == 200 and isinstance(body, dict) and (
                (body.get("data") or {}).get("granted") is True
            )
        except Exception:  # noqa: BLE001 — allocate is best-effort
            kap_unreachable = True
            logger.warning("qwen-eye: KAP allocate failed", exc_info=True)
        # started_by_us:allocate 成功=经队列取得(用完即停,旧契约);KAP 宕机
        # 兜底=仅 lease 持有者 own;等到别人的服务=只用不停。
        started_by_us = allocated
        if not allocated:
            # 73-02 (v3.2 F21 / 08-23 接力死锁根治):分两种"allocate 没成"——
            #   a) 队列显式拒绝(200 granted=false / 4xx):GPU 队列说不行,
            #      绝不绕队直跑(旧代码这里裸 subprocess kap-llm.sh 抢 GPU,
            #      是 08-23 五层死锁的未根治项);
            #   b) KAP 不可达(status 0 / 网络异常 / 5xx 服务坏):lease 受控
            #      拉起(flock 防多 episode 并发双启),只有 lease 持有者 own。
            queue_refused = alloc_status == 200 or 400 <= alloc_status < 500
            if not kap_unreachable and queue_refused:
                logger.warning(
                    "qwen-eye: allocate refused by KAP queue (HTTP %s) — "
                    "no bypass start (GPU 队列优先级必须尊重)", alloc_status,
                )
                return False, False
            started = self._direct_start_with_lease(timeout_s)
            if started is None:
                # 另一进程持有 lease 正在拉起——本进程只等健康,不 own。
                started_by_us = False
            elif not started:
                return False, False
            else:
                started_by_us = True

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._health_ok():
                # 只有本进程经 lease 真正拉起的服务才 owned(用完即停);
                # 等到别人的服务 → 只用不停。
                self._owned = started_by_us
                return True, True
            # Guard 2 — launch attempt died on model load: stop waiting.
            if self._server_log_load_failed(log_offset):
                logger.warning(
                    "qwen-eye: model load failed (see %s), giving up on start",
                    SERVER_LOG,
                )
                return False, True
            time.sleep(3)
        return False, True

    def _direct_start_with_lease(self, timeout_s: int) -> bool | None:
        """KAP 宕机兜底的 lease 受控拉起(73-02 F21)。

        Returns:
            True  — 本进程取得 flock 并实际执行了 kap-llm.sh start;
            None  — 另一进程持有 lease 正在拉起(调用方只等健康);
            False — 拉起失败。
        """
        lock_path = "/tmp/qwen-eye-direct-start.lock"
        fh = None
        try:
            fh = open(lock_path, "w")
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            if fh is not None:
                fh.close()
            logger.info(
                "qwen-eye: direct-start lease held by another process — "
                "waiting on their health",
            )
            return None
        try:
            subprocess.run(
                ["bash", KAP_LLM_SH, "start", "q4"],
                capture_output=True, timeout=timeout_s,
            )
            return True
        except (subprocess.SubprocessError, OSError):
            logger.warning("qwen-eye: kap-llm.sh start failed", exc_info=True)
            return False
        finally:
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
                fh.close()
            except OSError:
                pass

    def stop_if_owned(self) -> None:
        """Stop the server ONLY when we started it (幂等). Never raises.

        A pre-existing server (whoever's lease) is never touched — see
        the lifecycle contract in the module docstring.
        """
        if not self._owned:
            return
        self._owned = False
        try:
            subprocess.run(
                ["bash", KAP_LLM_SH, "stop"],
                capture_output=True, timeout=30,
            )
        except (subprocess.SubprocessError, OSError):
            logger.warning("qwen-eye: kap-llm.sh stop failed", exc_info=True)

    # ── Chat calls ────────────────────────────────────────────────────

    def _call_llm(self, messages: list[dict], max_tokens: int) -> str:
        """One chat completion. One retry on transient failure (OOM'd
        server recovers between calls). Raises RuntimeError on failure —
        callers decide whether to degrade."""
        # 看图模型 id（2026-08-25 模型路由）：QWEN_EYE_MODEL 逃生门。注意这是
        # llama-server 请求参数——服务端（kap-llm.sh 启动的容器）加载什么权重
        # 才是什么；此 env 只在换部署后同步 id 用，默认 qwen3.8 = 既有部署。
        body = {
            "model": os.environ.get("QWEN_EYE_MODEL", "qwen3.8"),
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": messages,
        }
        last_err: str = ""
        for attempt in range(2):
            status, resp = self._http_json(
                LLM_API, payload=body, timeout=LLM_CALL_TIMEOUT_S,
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
        raise RuntimeError(f"qwen-eye LLM call failed: {last_err}")

    @staticmethod
    def _b64(path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode()

    # ── Observation layer (multi-image) ───────────────────────────────

    def observe(self, image_paths: list[Path]) -> str:
        """Observe N images → natural-language description.

        Hard constraint: ONE user message PER image (llama.cpp drops
        images when a single user message carries N of them). Each image
        message carries a ``(帧i/N)`` text tail; consecutive user
        messages are legal.
        """
        n = len(image_paths)
        messages: list[dict] = []
        for i, path in enumerate(image_paths):
            messages.append({"role": "user", "content": [
                {"type": "image_url",
                 "image_url": {"url": "data:image/jpeg;base64," + self._b64(path)}},
                {"type": "text", "text": f"(帧{i + 1}/{n})"},
            ]})
        return self._call_llm(messages, max_tokens=2000)

    def observe_single(self, image_path: Path, question: str,
                       max_tokens: int = 2000) -> str:
        """Observe ONE image + answer a question in a single call.

        Used by the vision_verify routing layer: the image rides its own
        user message (hard constraint) and the question follows as the
        text part of the SAME message (single-image calls are exempt from
        the multi-image drop bug — there is only one image to drop).
        """
        messages = [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": "data:image/jpeg;base64," + self._b64(image_path)}},
            {"type": "text", "text": question},
        ]}]
        return self._call_llm(messages, max_tokens=max_tokens)

    # ── Judgement / QA layer (text mode) ──────────────────────────────

    def ask(self, text_prompt: str, max_tokens: int = 800) -> str:
        """Text-mode question over :8125 (no images)."""
        return self._call_llm(
            [{"role": "user", "content": text_prompt}], max_tokens=max_tokens,
        )
