"""video_engine.py - VideoEngine strategy pattern (P1-2 scriptability upgrade).

P11 (video render) historically delegated per-shot rendering to a subagent that
hand-wrote a ``render_S*.py`` wrapper around a bare ``curl`` POST to the KAP
unified H3 pipeline API (``:10588/api/production/minimax-h3/generate``). That
"freelancing" execution surface (which wrapper, whether to write one, whether
the trim is correct) is exactly what P1-2 retires: the deterministic render is
lifted into an in-process engine-adapter that mirrors ``preview_engine.py``.

Two engine roles mirror the ``PreviewEngine`` dual-engine split:

- ``H3VideoEngine``: multipart POST to the KAP H3 unified pipeline, stream-down
  the produced clip, then run the P0-4 frame-count hard gate inline. This is
  the ONLY video engine for P11 (``DEFAULT_VIDEO_ENGINE='h3'``).

This module is pure library code — ``pipeline/phases/p11_video_render.py`` (the
P1-2 integration) composes it into the per-shot fan-out. NO phase integration
here.

Design invariants (mirrors ``preview_engine.py``):
- D-04: ``transport`` constructor kwarg lets tests inject
  ``httpx.MockTransport`` for hermetic HTTP mocking. ``frame_validator`` is the
  P0-4 frame-gate injection point.
- D-06: All configuration is read from env vars at construction / call time
  (never at module import).
- D-09: Degrade-first contract. Connection errors / timeouts / 5xx / 429 return
  ``{"degraded": True, ...}``; they never raise to the caller. 4xx raises
  ``VideoEngineError`` (caller bug).
- WR-01: P11 fans out per-shot via ``ThreadPoolExecutor``. Since 2026-09-23
  (工单 B / C1) each worker thread owns ONE engine instance (constructed in
  the pool ``initializer=``), so workers no longer share a client and the
  per-instance lock does NOT serialize the fan-out. The ``threading.Lock``
  itself is RETAINED: it still serializes concurrent ``request()`` calls on
  the SAME instance (httpx connection-pool thread-safety is not part of its
  public contract — e.g. a main-thread selfheal redownload or any future
  same-instance hand-off). One instance per thread = the lock degenerates to
  uncontended; do NOT construct an engine and hand it to multiple threads
  expecting parallel renders. Lifecycle: owner thread's caller closes the
  instance after the pool joins (see ``close``).
- Strategy selection: ``select_video_engine()`` reads ``KAIS_VIDEO_ENGINE`` at
  call time (not import time). Default is ``"h3"`` (the only engine). Unknown
  values fall back to h3 + WARN log (no eval(), no dynamic lookup).

P1-1 (P12 ``_assemble_master``) is the deterministic-migration template this
module follows; P10b (``preview_engine``) is the engine-adapter template.
"""

from __future__ import annotations

import abc
import json
import logging
import math
import os
import re
import subprocess
import threading
import time
from typing import Any, Callable

import httpx

from plugins.kais_aigc.camera_move_intent import resolve_camera_move_trigger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# H3 frame-grid + ffprobe helpers (self-contained so this plugin module does
# NOT import from the ``pipeline`` package — plugins are below pipeline in the
# layering, see preview_engine.py). ``pipeline.engine_adapters`` is imported
# lazily when available (production, where the skill root is on sys.path); the
# inline n%17==5 snap is the always-available fallback so the module is correct
# even in the plugins-only test context.
# ---------------------------------------------------------------------------

# H3 sampler only accepts alignH3FrameCount-aligned frame counts (n%17==5).
_H3_FRAME_GRID = 17
_H3_FRAME_OFFSET = 5
_H3_FPS = 24
_H3_MIN_FRAMES = 5
_H3_MAX_FRAMES = 362
_H3_DEFAULT_FRAMES = 124  # 124 % 17 == 5 — used when the adapter is unavailable

# VDN engine arm (KAP profile="vdn-8", 2026-09-08 d3eb69e0 集成 — per-shot /
# episode 级显式选择, 不切默认). KAP 硬边界 H3_VDN.maxFrames=241 按对齐后
# (n%17==5) length 判; 网格在 (226, 241] 内无值 —— 226 之后下一格是 243 —
# 故 226f 是实际可请求的最大帧数。引擎侧预钳 (warn + 降档 226, 不 fail 整批)
# 避免超界 shot 撞 KAP 400 (0907 两次实测 OOM 定谳的边界)。消费链见
# _resolve_h3vdn / _cap_vdn_frames / docs/vdn-pipeline-integration.md。
VDN_PROFILE = "vdn-8"
_VDN_MAX_GRID_FRAMES = 226

# RH-V4 快速档臂 (KAP profile="rh-v4", 平台侧 2026-09-11 全注册: config.ts
# H3_EXPOSED_PROFILES 白名单 + H3_RH_V4 预射蓝图 —— 4 步恒定 + 14_lora LoRA
# 恒载; 本批引擎侧接入, KAP 零改动)。0911 盲测两轮定谳: LXV 17/21 > rh-v4
# 14/21, 但 rh-v4 在单人口型 (PK 轮 C03 优) 与非人物高速 (C05 优) 两轴反超
# 且渲染快 1.6-2.5× —— 引擎侧据此做场景路由 (_route_rh) + 显式 h3_rh 开关
# (_resolve_h3rh)。蓝图未声明帧网格约束 (0911 双批 229f/243f 均过 400 守卫),
# 故无 vdn 式 length 预钳, length 原值透传。
RH_V4_PROFILE = "rh-v4"

# Encoder padding tolerance; |actual - expected| > this is a trim_bypass.
_FRAME_TOLERANCE = 1

# Token-budget-aware resolution (KAP gate): a render is priced at
# width*height*length "tokens"; above safeLine KAP 400-rejects, and the
# crashLine beyond it is an RTX 3090 C++ abort that cannot be caught.
# Portrait 768×1344 × 362 frames (15s max-length shot) = 373,653,504 tokens
# → guaranteed 400 without the downgrade ladder below.
H3_TOKEN_SAFE_LINE = 300_000_000  # KAP safeLine with buffer (crashLine=340M)
H3_PORTRAIT_LADDER = [(768, 1344), (672, 1216), (640, 1152)]  # 32-multiples
H3_LANDSCAPE_LADDER = [(1344, 768), (1216, 672), (1152, 640)]

# H3 通用 LoRA 槽位 (KAP 0921 上线, /generate + /ref2va 收 lora/lora_strength/
# lora_steps 三字段): registry 唯一真源路径 + env 覆盖 (测试 fixture 注入)。
# 每调用重读不缓存 (与 KAP loadRegistry 同口径); 生产线只挂 status=production
# 条目 (trial 也拒)。链族守卫: preview-lock 臂落 lightx2v-8-768p (SigmaShift
# 族) —— 只收 chain=SigmaShift 条目; vdn-8/fasth3 无通用槽位, rh-v4 的
# 14_lora 是蓝图本体 LoRA, native-sage (final-shot) 无 LoRA loader 节点。
_H3_LORA_REGISTRY_PATH = (
    "/data/workspace/kais-aigc-platform/config/h3-lora-registry.json"
)
_H3_LORA_REGISTRY_ENV = "H3_KMC_LORA_REGISTRY_PATH"
_LORA_PREVIEW_LOCK_CHAIN = "SigmaShift"


def _compute_expected_frames(shot: dict) -> int:
    """shot.duration_sec → H3-legal frame count (n%17==5 snap, clamp [5,362]).

    Mirrors ``pipeline/phases/p11_video_render._expected_frame_count`` and the
    H3DurationAdapter snap logic. Prefers the authoritative adapter when the
    ``pipeline`` package is importable; otherwise falls back to the inline snap
    so this module is correct standalone.
    """
    try:
        from pipeline.engine_adapters import get_adapter as _get_adapter  # type: ignore[import-not-found]
        duration_sec = float((shot or {}).get("duration_sec", 5.0) or 5.0)
        return _get_adapter("h3").render_to_frame_count(duration_sec, _H3_FPS)
    except Exception:
        pass
    # Inline fallback — identical snap math to H3DurationAdapter.
    try:
        duration_sec = float((shot or {}).get("duration_sec", 5.0) or 5.0)
    except (TypeError, ValueError):
        return _H3_DEFAULT_FRAMES
    raw = round(duration_sec * _H3_FPS)
    grid, offset = _H3_FRAME_GRID, _H3_FRAME_OFFSET
    residue = raw % grid
    delta_up = (offset - residue) % grid
    delta_down = (residue - offset) % grid
    if delta_down <= delta_up and (raw - delta_down) >= _H3_MIN_FRAMES:
        snapped = raw - delta_down
    else:
        snapped = raw + delta_up
    return max(_H3_MIN_FRAMES, min(_H3_MAX_FRAMES, snapped))


def _cap_vdn_frames(frames: int, vdn: bool, shot: dict) -> int:
    """VDN length pre-clamp: warn + downgrade >226f shots to 226.

    KAP's vdn-8 guard (generate.ts 2026-09-08) 400-rejects aligned length
    >241f; 226 is the largest n%17==5 grid value under that boundary, so any
    larger grid value (≥243) would fail the whole request. Batch-tolerance
    principle (承管线容忍偏差原则): keep the shot renderable at 226 (~9.4s)
    instead of failing. Non-vdn shots pass through unchanged — legacy
    behavior byte-identical. Called from BOTH _build_multipart (request
    length) and render's P0-4 gate (expected frames) so a downgraded shot
    gates against the length actually requested, not its raw snap.
    """
    if not vdn or frames <= _VDN_MAX_GRID_FRAMES:
        return frames
    shot_id = (shot or {}).get("shot_id") or (shot or {}).get("id", "unknown")
    logger.warning(
        "h3_engine: %s h3_vdn length %df exceeds vdn-8 grid max %df "
        "(KAP hard boundary 241f, 0907 OOM verdict) — downgraded to %df",
        shot_id, frames, _VDN_MAX_GRID_FRAMES, _VDN_MAX_GRID_FRAMES,
    )
    return _VDN_MAX_GRID_FRAMES


def _load_lora_registry(shot_id: str = "unknown") -> dict[str, dict] | None:
    """H3 LoRA registry 真源 → ``{name: entry}``; 读盘失败 warning + None。

    真源读不了不禁渲染 (承 batch-tolerance 原则): 返回 None 后调用方
    ``_route_lora`` 放行不发 lora 字段, 渲染继续。路径 env
    ``H3_KMC_LORA_REGISTRY_PATH`` 覆盖 (测试 fixture 注入); 每调用重读不
    缓存 (与 KAP loadRegistry 同口径 —— 探针台帐 status 流转即时生效)。
    """
    path = os.environ.get(_H3_LORA_REGISTRY_ENV) or _H3_LORA_REGISTRY_PATH
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning(
            "h3_engine: %s lora registry 读盘失败 path=%s (%s) — "
            "h3_lora 本次不挂载, 渲染继续", shot_id, path, exc,
        )
        return None
    entries = data.get("loras") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        logger.warning(
            "h3_engine: %s lora registry 形态异常 path=%s (缺 loras 列表) "
            "— h3_lora 本次不挂载, 渲染继续", shot_id, path,
        )
        return None
    return {
        entry["name"]: entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _ffprobe_duration_valid(mp4_path: str) -> bool:
    """ffprobe duration > 0 check (mirrors p11 ``_ffprobe_mp4_valid`` fast path).

    Fail-closed (False) when ffprobe is missing / times out — production safety.
    """
    if not os.path.isfile(mp4_path) or os.path.getsize(mp4_path) == 0:
        return False
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", mp4_path],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return False
        dur = (r.stdout or "").strip()
        return bool(dur) and float(dur) > 0
    except (FileNotFoundError, OSError, ValueError, subprocess.TimeoutExpired):
        return False


def _ffprobe_frame_count(mp4_path: str) -> int | None:
    """Read mp4 frame count. Header ``nb_frames`` (fast) → ``count_frames`` (slow).

    Returns None on any failure (caller decides fail-closed vs skip).
    """
    if not os.path.isfile(mp4_path):
        return None
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=nb_frames",
             "-of", "default=noprint_wrappers=1:nokey=1", mp4_path],
            capture_output=True, text=True, timeout=10,
        )
        nb = (r.stdout or "").strip()
        if nb and nb != "N/A":
            return int(nb)
        r2 = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames",
             "-select_streams", "v:0",
             "-show_entries", "stream=nb_read_frames",
             "-of", "default=noprint_wrappers=1:nokey=1", mp4_path],
            capture_output=True, text=True, timeout=60,
        )
        nb2 = (r2.stdout or "").strip()
        return int(nb2) if nb2 and nb2 != "N/A" else None
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired, OSError):
        return None


def _default_frame_validator(clip_path: str, expected_frames: int) -> tuple[bool, str]:
    """P0-4 frame-count hard gate (built-in default for H3VideoEngine).

    Mirrors p11 ``_mp4_valid_with_frames``: duration probe THEN frame-count ==
    expected within ``_FRAME_TOLERANCE``. Fail-closed when frames are unreadable
    (production safety — a clip we can't probe is a clip we can't trust).
    """
    if not _ffprobe_duration_valid(clip_path):
        return False, "duration probe failed"
    actual = _ffprobe_frame_count(clip_path)
    if actual is None:
        return False, "frame count unreadable (fail-closed)"
    if abs(actual - expected_frames) > _FRAME_TOLERANCE:
        return False, f"trim_bypass: actual={actual} expected={expected_frames}"
    return True, f"ok (frames={actual})"


class VideoEngineError(Exception):
    """Raised for 4xx client errors from the H3 API (caller bug).

    Mirrors ``PreviewEngineError`` / ``GoldTeamError`` semantics: connection
    errors / timeouts / 5xx / 429 do NOT raise — they degrade (return a
    ``{"degraded": True, ...}`` envelope to the caller). 4xx and invalid-JSON
    2xx responses are caller / service bugs and raise this exception.
    """


class VideoEngine(abc.ABC):
    """Abstract base class for the P11 video-render engine strategy.

    Concrete subclasses implement ``render()`` to produce one video clip per
    shot. Both the success and degrade envelopes are uniform:

    - Success: ``{"clip_path": str, "generation_time_ms": int, "engine": str, ...}``
    - Degrade: ``{"degraded": True, "engine": str, "reason": str}``

    ``generation_time_ms`` is LOCALLY-measured wall time via
    ``time.monotonic()`` (INFO #10) — the response body's reported timing is
    IGNORED. Local wall time is always available and comparable across engines.
    """

    @abc.abstractmethod
    def render(
        self,
        *,
        shot: dict,
        output_path: str,
        turnaround_paths: list[str] | None = None,
        scene_ref_path: str | None = None,
        voice_clip_path: str | None = None,
        first_frame: str | None = None,
        prompt: str | None = None,
        episode_config: dict | None = None,
    ) -> dict:
        """Render one shot's video clip. Subclasses MUST implement.

        Returns a success envelope (``clip_path`` / ``generation_time_ms`` /
        ``engine`` / ``frame_count``) or a degrade envelope (``degraded: True``).
        """
        raise NotImplementedError

    @staticmethod
    def _record_time(start: float) -> int:
        """Return wall-clock ms since ``start`` (monotonic delta, INFO #10)."""
        return int((time.monotonic() - start) * 1000)

    # ------------------------------------------------------------------
    # Lifecycle (mirrors PreviewEngine — context-manager protocol on the ABC)
    # ------------------------------------------------------------------
    # The ABC provides no-op defaults so callers can unconditionally use
    # ``with select_video_engine() as engine:`` regardless of which concrete
    # engine is selected. ``H3VideoEngine`` overrides these to close its
    # ``httpx.Client`` connection pool.
    #
    # Per-worker lifecycle contract (2026-09-23 工单 B / C1): fan-out owners
    # construct one instance per worker thread and call ``close()`` exactly
    # once per instance AFTER the pool joins (worker threads have exited —
    # p11b closes its whole registry post-fan-out). Instances are NOT
    # thread-pooled or reused across run() invocations.

    def close(self) -> None:
        """Release engine-held resources. No-op default; subclasses override.

        Call once, from the owning orchestration thread, after that owner's
        concurrent work has joined (see the per-worker contract above).
        """
        return

    def __enter__(self) -> "VideoEngine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def select_video_engine(env: str | None = None) -> VideoEngine:
    """Factory returning a concrete engine based on env-var dispatch.

    Resolution order (D-06: read at call time, not import time):
    1. Explicit ``env`` kwarg (tests + programmatic callers).
    2. ``os.environ.get("KAIS_VIDEO_ENGINE")`` (call-time read).
    3. Default ``"h3"`` (the ONLY video engine for P11).

    Unknown values fall back to ``H3VideoEngine`` AND emit a WARN log
    mentioning the unknown value (T-40-09 mitigation — no eval(), no dynamic
    class lookup; predictable fallback).
    """
    value = env if env is not None else os.environ.get("KAIS_VIDEO_ENGINE", "h3")
    if value == "h3":
        return H3VideoEngine()
    logger.warning(
        "unknown KAIS_VIDEO_ENGINE=%r, falling back to h3", value,
    )
    return H3VideoEngine()


# ----------------------------------------------------------------------
# H3VideoEngine — httpx multipart POST to the KAP unified H3 pipeline.
# render() is the per-shot entry point; _post enforces the D-09 contract;
# _download streams the produced clip; the P0-4 frame gate runs inline.
# ----------------------------------------------------------------------


def _derive_caller_tag() -> str | None:
    """Best-effort caller identity for UGQ 排队任务归属 (2026-10-01).

    Derivation ladder (first hit wins):
      1. ``KAIS_H3_CALLER_TAG`` env override (explicit, wins over everything).
      2. cwd basename if it looks like a KMC episode dir (starts with ``ep-``)
         → ``kmc:<basename>``.
      3. None (external caller, no tag — KAP treats missing header as anonymous).

    Sent as ``X-KAP-Caller-Tag`` header; KAP side sanitizes/clamps to 120 chars.
    Pure best-effort: any failure here must never block a render.
    """
    try:
        tag = (os.environ.get("KAIS_H3_CALLER_TAG") or "").strip()
        if tag:
            return tag[:120]
        base = os.path.basename(os.getcwd().rstrip("/"))
        if base.startswith("ep-"):
            return f"kmc:{base}"[:120]
    except Exception:
        pass
    return None


class H3VideoEngine(VideoEngine):
    """H3 (MiniMax) video engine via the KAP unified pipeline API.

    POSTs a ``multipart/form-data`` request to
    ``/api/production/minimax-h3/generate`` (the same endpoint the retired
    per-shot ``curl`` hit), streams the produced clip to ``output_path``, then
    runs the P0-4 frame-count hard gate. Follows the D-09 degrade-first
    contract (``LTXVideoEngine`` retired 2026-09-02 — LTX fallback removed):

    - ConnectError / TimeoutException / HTTPError -> degrade envelope.
    - status >= 500 or status == 429 -> degrade envelope.
    - status >= 400 -> raise ``VideoEngineError`` (caller bug).
    - 2xx -> parse JSON; invalid JSON -> raise (service bug).

    The multipart field set is a 1:1 port of the retired curl template
    (``_form_factor_render_args_h3`` in p11), migrated 2026-08-17 to the KAP
    useCase entry: ``projectId``, ``prompt`` (the H3-enhanced prompt), ``mode``
    (ref2va/i2va/t2va), ``useCase`` (preview-lock/final-shot; preview-lock also
    sends ``motion``), ``width``/``height`` (32-multiple form-factor resolution),
    ``length`` (n%17==5 frame count), ``filenamePrefix`` (shot_id); files:
    ``refImages[]`` (character turnarounds + scene background, ≤9), ``ttsAudio``
    (TTS dialogue), ``image`` (first-frame lock for i2va). Optional
    ``blockCache``/``blockCacheThreshold`` (2026-08-27 MiniMaxH3BlockCacheT8
    passthrough, native-sage only) appear after ``useCase`` only when
    configured — unconfigured shots keep the legacy field sequence. VDN shots
    (``h3_vdn`` on, 2026-09-09) send ``profile=vdn-8`` INSTEAD of
    ``useCase``/``motion`` (profile-only wiring — a concurrent useCase would
    hijack KAP's steps/audio presets off the audited 8-step VDN blueprint) and
    are length-capped to 226f (KAP hard boundary 241f; grid has no legal value
    above 226). See docs/vdn-pipeline-integration.md. rh-v4 shots (``h3_rh``
    on or scene-routed, 2026-09-12) likewise send ``profile=rh-v4`` INSTEAD of
    ``useCase``/``motion`` (same profile-only wiring; the rh-v4 blueprint
    declares no frame-grid clause so ``length`` passes through uncapped) —
    scene routing picks rh-v4 only on its blind-test-winning axes
    (single-person lip-sync / non-person high-motion, ``_route_rh``), and
    ``h3_vdn`` wins when both arms are on (audited 8-step blueprint beats the
    fast tier). Since 2026-09-16 (0916 four-arm blind-verdict: vdn-8 top score
    72.2% at quality parity, 1.3-1.4× faster than lxv) final-shot detail
    closeups — single-person + any of dialogue / CU-scale / low-motion, ≤226f
    — are auto-routed to vdn-8 by ``_route_vdn_final`` when no explicit
    ``h3_vdn`` config exists; preview-lock never auto-vdns, explicit configs
    keep full-volume behavior, and the auto-overlap axis resolves vdn > rh
    (unchanged branch order).

    Generic LoRA slot (2026-09-22, KAP 0921 上线): explicit ``h3_lora`` config
    runs the ``_route_lora`` registry/arm preflight in ``render`` — fail-loud
    ``ValueError`` on nonexistent / non-production / forbidden-arm entries
    (preview-lock → lightx2v-8-768p, SigmaShift chain, is the ONLY attachable
    arm; the vdn/rh blueprint arms and the loaderless final-shot arm all
    reject) — then ``lora``/``lora_strength``/``lora_steps`` are appended
    after useCase/motion. Unconfigured shots keep the legacy field sequence
    byte-identical; an unreadable registry warns and renders without lora.

    WARNING WR-01: the underlying ``httpx.Client`` connection pool's
    thread-safety for CONCURRENT ``request()`` calls is not part of its public
    contract. A ``threading.Lock`` serializes the POST on THIS instance so
    concurrent callers sharing it can't corrupt connection state. Since
    2026-09-23 (工单 B / C1) p11b constructs ONE instance per fan-out worker
    (``ThreadPoolExecutor(initializer=...)``) instead of sharing one — the
    lock then degenerates to uncontended per worker and renders no longer
    serialize. Sharing one instance across threads is still SUPPORTED (the
    lock keeps it correct) but serializes renders — throughput callers
    should follow the per-worker pattern.
    """

    DEFAULT_BASE_URL = "http://localhost:10588"
    DEFAULT_TIMEOUT = 3600.0  # H3 ref2va 15-step render needs ~13min/shot on 3090
    H3_PATH = "/api/production/minimax-h3/generate"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
        frame_validator: Callable[[str, int], tuple[bool, str]] | None = None,
    ) -> None:
        """Construct the engine.

        Parameters (D-06 env-var configuration at construction time):

        - ``base_url`` / ``KAIS_H3_URL``: KAP unified pipeline base URL.
        - ``timeout``: per-request timeout in seconds (default 300s).
        - ``transport``: hermetic test injection via ``httpx.MockTransport``.
          ``None`` (default) uses real networking.
        - ``frame_validator``: P0-4 frame-gate injection point.
          ``Callable(clip_path, expected_frames) -> (ok, reason)``. ``None``
          (default) uses the built-in ``_default_frame_validator`` (ffprobe
          duration + frame-count check). Tests inject a fake to bypass ffprobe.
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_H3_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        # transport=None -> real network; tests inject httpx.MockTransport.
        self._client = httpx.Client(
            timeout=self._timeout, transport=transport, follow_redirects=True,
        )
        self._lock = threading.Lock()  # WR-01: serialize concurrent POST.
        self._frame_validator = frame_validator or _default_frame_validator
        # UGQ 排队任务归属: 构造时一次性推导 caller tag (进程身份), 每个 POST
        # 经 X-KAP-Caller-Tag header 旁路带给 KAP (D1-9 同款, 不碰 body schema)。
        self._caller_tag = _derive_caller_tag()
        # Last _download() failure cause (empty on success) — surfaces the
        # real error class in the degrade reason instead of "download failed".
        self._last_download_error = ""

    def _degrade(self, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope and log a warning (D-09)."""
        logger.warning("h3_engine degraded: %s", reason)
        return {"degraded": True, "engine": "h3", "reason": reason}

    # ------------------------------------------------------------------
    # Form-factor field resolution (port of _form_factor_render_args_h3,
    # minus the curl string — the engine builds multipart dict/files instead).
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_resolution(
        shot: dict,
        episode_config: dict | None,
        frames: int | None = None,
    ) -> tuple[int, int]:
        """Token-budget-aware 32-multiple form-factor resolution.

        Priority:
        1. Shot-level ``resolution_override`` ("672x1216") when both numbers
           are positive 32-multiples — the operator's manual knob, skips the
           ladder entirely.
        2. Form-factor ladder (landscape 1344×768 → …, portrait 768×1344 → …),
           from the top rung down to the first whose ``w*h*frames`` fits the
           KAP token safeLine. With ``frames<=0``/None (unknown length) the
           top rung stands — the pre-budget behavior.
        3. All rungs over budget → lowest rung (let KAP's 400 speak truth).

        A downgrade logs the rung transition + token count + shot_id.
        """
        shot_id = shot.get("shot_id") or shot.get("id", "unknown")
        # 1. Operator override — validated 32-multiple "WxH", else ignored.
        override = str(shot.get("resolution_override") or "").strip().lower()
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", override)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            if w > 0 and h > 0 and w % 32 == 0 and h % 32 == 0:
                return (w, h)
            logger.warning(
                "h3_engine: invalid resolution_override=%r for shot %s "
                "(need WxH, both 32-multiples); using ladder",
                override, shot_id,
            )

        ff = (episode_config or {}).get("form_factor") or shot.get("form_factor", "portrait")
        ladder = H3_LANDSCAPE_LADDER if ff == "landscape" else H3_PORTRAIT_LADDER
        top = ladder[0]
        if not frames or frames <= 0:
            return top  # unknown length — legacy top-rung behavior

        # 2. First rung whose token cost fits the safeLine.
        for w, h in ladder:
            if w * h * frames <= H3_TOKEN_SAFE_LINE:
                if (w, h) != top:
                    logger.info(
                        "h3_engine: %s resolution downgrade %dx%d -> %dx%d "
                        "(tokens=%d frames=%d safeLine=%d)",
                        shot_id, top[0], top[1], w, h,
                        top[0] * top[1] * frames, frames, H3_TOKEN_SAFE_LINE,
                    )
                return (w, h)

        # 3. Over budget at every rung — lowest, so KAP's 400 is honest.
        w, h = ladder[-1]
        logger.info(
            "h3_engine: %s all ladder rungs exceed token safeLine; using "
            "lowest %dx%d (tokens=%d frames=%d safeLine=%d)",
            shot_id, w, h, w * h * frames, frames, H3_TOKEN_SAFE_LINE,
        )
        return (w, h)

    # 2026-08-17 KAP API 精简迁移: H3 只暴露 useCase 白名单两档
    #   preview-lock —— P11a 预览, motion 跨拓扑路由 (low→turbo4 / medium→turbo8 /
    #                   high→native-sage15), 音频 tts-only (TTS+H3 原生音轨混音)。
    #   final-shot  —— P11b 成片, native-sage 36 步 @1344×768, 完整 Foley+TTS 混音。
    # KAP 侧 400 拒绝白名单外的 profile/useCase, 故旧 h3_profile 值必须映射到 useCase。
    _USECASE_BY_LEGACY_PROFILE = {
        "turbo": "preview-lock",
        "preview": "preview-lock",      # 旧 15 步 T8 预览 → 动态路由预览
        "native": "final-shot",          # 旧 P11b native→native-sage+15步 → final-shot(36步)
        "native-sage": "final-shot",
        "production": "final-shot",      # 旧 50 步完整管线 → 成片档
        # lightx2v-8-768p 已暴露(白名单)但仅作候选档; final-shot 预射 2026-08-28 回滚维持 native-sage 36 步
    }
    _USECASES = ("preview-lock", "final-shot")

    @staticmethod
    def _resolve_use_case(shot: dict, episode_config: dict | None) -> str:
        """H3 useCase (KAP 2026-08-17 白名单入口): preview-lock / final-shot.

        Priority: shot-level ``h3_useCase`` > episode_config ``h3_useCase`` >
        legacy ``h3_profile`` 映射 > default ``"final-shot"`` (旧引擎默认
        native 的语义等价物)。未知值回退 final-shot。
        """
        raw = shot.get("h3_useCase") or (episode_config or {}).get("h3_useCase")
        if raw:
            return raw if raw in H3VideoEngine._USECASES else "final-shot"
        legacy = shot.get("h3_profile") or (episode_config or {}).get("h3_profile")
        return H3VideoEngine._USECASE_BY_LEGACY_PROFILE.get(legacy or "", "final-shot")

    @staticmethod
    def _resolve_mode(shot: dict, episode_config: dict | None) -> str:
        """taskMode: shot.mode > episode_config.h3_mode > ref2va."""
        return shot.get("mode") or (episode_config or {}).get("h3_mode") or "ref2va"

    # 2026-09-09 VDN 通道 (KAP profile=vdn-8, d3eb69e0 集成): per-shot/episode
    # 级显式选择, 不走 preview-lock 动态路由 (vdn 是审定 8 步蓝图臂, 不是
    # motion 路由档)。接线形态 = profile-only —— 见 _build_multipart 内 C1
    # 实探结论与 docs/vdn-pipeline-integration.md §2。
    # 2026-09-16 扩展: 两层显式配置均缺时, final 档细节镜由 _route_vdn_final
    # 自动路由进 vdn-8 速度副档 (0916 四臂盲选定谳) —— 见 _resolve_h3vdn。
    # _resolve_vdn 本体原样保留为 legacy 显式-only 解析器 (既有 vdn 测试
    # 回归锚, 渲染消费点已换调 _resolve_h3vdn)。
    @staticmethod
    def _resolve_vdn(shot: dict, episode_config: dict | None) -> bool:
        """h3_vdn 开关 (legacy 显式-only): shot.h3_vdn > episode_config.h3_vdn
        > off。

        对齐 _resolve_block_cache 语义家族: shot 键存在即独占该决定权 ——
        显式 False/"off" 是对 episode 级 true 的 per-shot 抑制, 不回落。
        真值同构接受 bool True / "on"/"true"/"1" (大小写不敏感、去首尾空白)
        / 数字 1; 其余值 (0/None/垃圾串) 一律视为关。
        """
        if "h3_vdn" in shot:
            raw = shot["h3_vdn"]
        else:
            raw = (episode_config or {}).get("h3_vdn")
        if raw is True:
            return True
        if isinstance(raw, str):
            return raw.strip().lower() in {"on", "true", "1"}
        return raw == 1

    # 2026-09-16 vdn 解析重构 (0916 gpunoise 四臂盲选定谳落地): vdn-8 得分率
    # 72.2% 全场最高, 与 lxv 6 镜直接对拍 13:13 平 (质量平局), val 组同 case
    # 速度快 1.3-1.4× —— 故 final 档细节镜在无显式配置时自动路由 vdn-8 作
    # 速度副档 (quality-parity speed sub-tier); 预览档永不自动 vdn。
    @staticmethod
    def _resolve_h3vdn(
        shot: dict, episode_config: dict | None, use_case: str,
    ) -> bool:
        """h3_vdn 开关: shot.h3_vdn > episode_config.h3_vdn >
        _route_vdn_final 自动路由。

        语义家族同 _resolve_h3rh: 键存在即独占决定权 —— 显式 False/"off"
        是抑制 (不回落 episode 级 true, 也不回落自动路由)。真值同构接受
        bool True / "on"/"true"/"1" (大小写不敏感、去首尾空白) / 数字 1;
        其余值 (0/None/垃圾串) 一律视为关。

        语义变化 (2026-09-16, 向后兼容): 原 ``_resolve_vdn`` 无显式配置=
        永远 False; 本函数无显式配置=final 档细节镜自动路由判定。显式全量
        开 (episode 级 h3_vdn=true) 行为不变 —— preview 档也 vdn (自动路由
        被 use_case 门限制在 final 档, 显式配置不经此门)。

        渲染消费点 (_build_multipart profile 选择 + render() P0-4 帧门) 共用
        本解析; 生效判定打 INFO 日志注明三态来源 (source=shot/episode/auto)。
        """
        shot_id = (shot or {}).get("shot_id") or (shot or {}).get("id", "unknown")
        if "h3_vdn" in shot:
            source, raw = "shot", shot["h3_vdn"]
        elif episode_config and "h3_vdn" in episode_config:
            source, raw = "episode", episode_config["h3_vdn"]
        else:
            auto = H3VideoEngine._route_vdn_final(shot, episode_config, use_case)
            if auto:
                logger.info(
                    "h3_engine: %s h3_vdn=on (source=auto final 细节镜速度副档)",
                    shot_id,
                )
            return auto
        if raw is True:
            value = True
        elif isinstance(raw, str):
            value = raw.strip().lower() in {"on", "true", "1"}
        else:
            value = raw == 1
        if value:
            logger.info("h3_engine: %s h3_vdn=on (source=%s)", shot_id, source)
        return value

    # 特写景别词表 (P09 shot_grammar 真值 <MCU|CU|BCU|MS|FS|WS> + INSERT 无
    # 角色 shot): "CU" 子串同命中 MCU/BCU —— 大写化子串匹配, 同
    # p09_shot_breakdown 的 shot_scale 规整法 (strip().upper())。
    _VDN_FINAL_CLOSEUP_TOKENS = ("CU", "MCU", "INSERT")

    @staticmethod
    def _route_vdn_final(
        shot: dict, episode_config: dict | None, use_case: str,
    ) -> bool:
        """场景路由: final 档细节镜是否自动走 vdn-8 速度副档 (0916 定谳)。

        判据全部满足才路由 (细节敏感信号任一命中即算细节镜):
          1. final 档专属: ``use_case != "final-shot"`` 直接 False —— 预览档
             永不自动 vdn (preview-lock 动态路由有更快的 turbo 臂, 无副档
             收益; 显式 h3_vdn 配置不经此门, 全量开行为不变);
          2. 人物数 ≤1 (``character_refs`` 列表长度; 缺字段按 1 —— 抄
             _route_rh);
          3. 细节敏感信号任一命中: 对白镜 (``dialogue_text``/``dialogue_note``
             非空) ∨ 特写景别 (``shot_scale``/``shot_type`` 大写化后含
             CU/MCU/INSERT 之一) ∨ 低动 (``_classify_motion`` == "low" ——
             低动镜细节敏感且 vdn-8 速度收益最稳);
          4. 硬边界保护: ``_compute_expected_frames`` 长度经 _cap_vdn_frames
             钳制语义 (_VDN_MAX_GRID_FRAMES=226, KAP 241f 硬边界下网格最大
             值) 判仍超界 (即钳前 >226f) → False —— 超界细节镜留在 legacy
             链原长渲染, 不吃降档截断 (0907 两次 OOM 定谳边界, 防拒单打穿
             扇出)。
        无命中保守回退 False (同 _route_rh —— 默认零行为变化红线)。
        episode_config 不参与判定 (判据均为 shot 级信号 + use_case 档位;
        形参为 _resolve_* 家族签名对齐预留)。
        """
        shot_id = (shot or {}).get("shot_id") or (shot or {}).get("id", "unknown")
        if use_case != "final-shot":
            logger.info(
                "h3_engine: %s scene-route h3_vdn_final=False (use_case=%s "
                "— 非最终成片档, 不自动 vdn)", shot_id, use_case,
            )
            return False
        refs = shot.get("character_refs")
        character_count = len(refs) if isinstance(refs, list) else 1
        has_dialogue = bool(str(
            shot.get("dialogue_text") or shot.get("dialogue_note") or ""
        ).strip())
        scale = str(
            shot.get("shot_scale") or shot.get("shot_type") or ""
        ).strip().upper()
        closeup = any(
            tok in scale for tok in H3VideoEngine._VDN_FINAL_CLOSEUP_TOKENS
        )
        motion = H3VideoEngine._classify_motion(shot)
        detail_hit = has_dialogue or closeup or motion == "low"
        frames = _compute_expected_frames(shot)
        boundary_safe = frames <= _VDN_MAX_GRID_FRAMES
        routed = character_count <= 1 and detail_hit and boundary_safe
        logger.info(
            "h3_engine: %s scene-route h3_vdn_final=%s (use_case=%s "
            "characters=%d dialogue=%s closeup=%s motion=%s frames=%d%s)",
            shot_id, routed, use_case, character_count,
            has_dialogue, closeup, motion, frames,
            "" if boundary_safe else " — 超 226f 硬边界, 留 legacy 链原长渲染",
        )
        return routed

    # 2026-09-12 rh-v4 快速档通道 (KAP profile="rh-v4", 平台侧 0911 全注册):
    # 显式 h3_rh 开关 (h3_vdn 命名族语义) 优先; 两层显式配置均缺时由
    # _route_rh 按 0911 盲测定谳判据自动路由。接线形态同 vdn = profile-only
    # (useCase 在场会劫持步数/音频预射, 偏离 4 步 + 14_lora 蓝图)。
    @staticmethod
    def _resolve_h3rh(shot: dict, episode_config: dict | None) -> bool:
        """h3_rh 开关: shot.h3_rh > episode_config.h3_rh > _route_rh 自动路由。

        对齐 _resolve_vdn 语义家族: 键存在即独占决定权 —— 显式 False/"off"
        是抑制 (不回落 episode 级 true, 也不回落自动路由)。真值同构接受
        bool True / "on"/"true"/"1" (大小写不敏感、去首尾空白) / 数字 1;
        其余值 (0/None/垃圾串) 一律视为关。
        """
        if "h3_rh" in shot:
            raw = shot["h3_rh"]
        elif episode_config and "h3_rh" in episode_config:
            raw = episode_config["h3_rh"]
        else:
            return H3VideoEngine._route_rh(shot, episode_config)
        if raw is True:
            return True
        if isinstance(raw, str):
            return raw.strip().lower() in {"on", "true", "1"}
        return raw == 1

    # 场景分类信号源 (管线实测锚点): 人物数 = shot.character_refs 列表长度
    # (p11b _extract_character_names 同源消费, 元素可为 dict/str); 对白 =
    # dialogue_text / dialogue_note (P09 契约字段, p11b TTS 注入同源);
    # 运动档 = camera_movement (P09 真值字段, p09_shot_breakdown.py:1638)
    # 按 p11a _classify_motion 关键词集分级 (high 先查 → low → 默认 medium)。
    _ROUTE_LOW_MOTION_KEYWORDS = {
        "static", "locked", "locked_off", "tilt_up", "tilt_down",
        "slow_pan", "stationary",
    }
    _ROUTE_HIGH_MOTION_KEYWORDS = {
        "tracking", "dolly", "handheld", "crane", "whip_pan",
        "crash_zoom", "running", "chase",
    }

    @staticmethod
    def _classify_motion(shot: dict) -> str:
        """camera_movement → low/medium/high (判据同 p11a _classify_motion)。

        P09 真值字段 ``camera_movement`` 优先, 兼容旧拼写 ``camera_motion`` /
        ``camera_intent`` (全部小写化子串匹配): high 关键词先查、low 次之,
        无命中默认 medium (空/缺失同)。为 _route_rh 服务, 不上报 KAP。
        """
        camera_motion = (
            shot.get("camera_movement")
            or shot.get("camera_motion")
            or shot.get("camera_intent")
            or ""
        ).lower()
        for kw in H3VideoEngine._ROUTE_HIGH_MOTION_KEYWORDS:
            if kw in camera_motion:
                return "high"
        for kw in H3VideoEngine._ROUTE_LOW_MOTION_KEYWORDS:
            if kw in camera_motion:
                return "low"
        return "medium"

    @staticmethod
    def _route_rh(shot: dict, episode_config: dict | None = None) -> bool:
        """场景路由: 该 shot 是否走 rh-v4 快速档 (0911 盲测两轮定谳)。

        rh-v4 反超轴 = 单人口型 (PK 轮 C03 优) + 非人物高速 (C05 优), 渲染
        快 1.6-2.5×; LXV 保有多人对白/多人追逐 (LMH 轮 C02 优 / PK 轮
        C01+C07 优)。判据全部满足才路由:
          1. 人物数 ≤1 (``character_refs`` 长度; 缺字段按 1 算 —— 无明确
             多人证据不当多人排除, 但也不当非人物);
          2. 对白/口型镜头 (``dialogue_text``/``dialogue_note`` 非空) 或
             非人物 (``character_refs`` 为空列表);
          3. 运动档 medium/high (low 静止/极慢不路由 —— 极低动不缺速度且
             细节敏感)。
        路由信号缺失时保守回退 False。episode_config 不参与判定 (判据均为
        shot 级信号; 形参为 _resolve_* 家族签名对齐预留)。
        """
        refs = shot.get("character_refs")
        if isinstance(refs, list):
            character_count = len(refs)
            non_person = character_count == 0
        else:
            character_count = 1  # 缺字段按 1 算 (单人假设, 不触发非人物分支)
            non_person = False
        has_dialogue = bool(str(
            shot.get("dialogue_text") or shot.get("dialogue_note") or ""
        ).strip())
        motion = H3VideoEngine._classify_motion(shot)
        routed = (
            character_count <= 1
            and (has_dialogue or non_person)
            and motion in ("medium", "high")
        )
        shot_id = (shot or {}).get("shot_id") or (shot or {}).get("id", "unknown")
        logger.info(
            "h3_engine: %s scene-route h3_rh=%s (characters=%d dialogue=%s "
            "motion=%s)",
            shot_id, routed, character_count, has_dialogue, motion,
        )
        return routed

    # 2026-09-22 H3 通用 LoRA 槽位 (KAP 0921 上线): 需求侧预检路由器。显式
    # h3_lora 配置在发请求前过 registry/臂校验 —— 条目不存在 / status 非
    # production / 臂判定禁挂 一律 fail-loud ValueError (禁静默跳过 = 整批
    # 裸奔); 无配置或真源读不了返回 None (不发字段, 渲染继续)。
    @staticmethod
    def _route_lora(
        shot: dict, episode_config: dict | None = None,
    ) -> tuple[str, float | None, int | None, str] | None:
        """显式 h3_lora 配置预检 → (name, strength, steps, source) | None。

        返回元组时 ``_build_multipart`` 逐字段透传 (None 成员 = 不发该字段,
        KAP 落 registry 条目默认 —— 步数契约 r037 实锤: 风格/动作 LoRA 不
        显式 lora_steps=20 = 已知失效, 故显式配置走 h3_lora_steps; 缺省/
        "auto" 不做 auto→20 翻译, 让平台层 fall through 条目 steps)。
        None = 无配置 / 真源读不了, 不发任何 lora 字段。

        逐字段两级解析 (name/strength/steps 各自独立, shot 键存在即独占 ——
        _resolve_vdn 语义家族): 键级别混搭合法 (episode 名 + shot strength
        覆盖)。source 取 name 的层级 (per-shot|episode) —— name 是唯一锚,
        孤儿 strength/steps (无 name) 不发送不校验。

        fail-loud (raise ValueError, 信息含 lora 名 + 原因 + 修复提示):
          ① 条目不存在; ② status != production (trial/candidate/retired 也
          拒, 生产线只挂 production); ③ 臂判定禁挂 —— vdn-8/rh-v4 蓝图臂
          (profile-only: 前者无通用槽位, 后者 14_lora 是蓝图本体 LoRA)、
          final-shot 臂 (native-sage 无 LoRA loader 节点)、链族守卫
          (preview-lock 落 lightx2v-8-768p 属 SigmaShift 族, 只收
          chain=SigmaShift 条目)。唯一可挂臂 = preview-lock。判臂沿用
          _build_multipart 同源解析 (_resolve_use_case → _resolve_h3vdn →
          _resolve_h3rh; 纯函数双解析同结果, render() 帧门已有双解析先例)。
        解析结果只进返回值, 禁改 shot dict (多臂共享输入)。
        """
        shot = shot or {}
        ec = episode_config or {}

        def _pick(key: str) -> Any:
            # 两级解析: shot 键存在即独占 (显式空值是对 episode 级的抑制),
            # 否则 episode 值。
            return shot[key] if key in shot else ec.get(key)

        raw_name = _pick("h3_lora")
        name = str(raw_name).strip() if raw_name is not None else ""
        if not name:
            return None  # 无配置 (或孤儿 strength/steps) —— 不发任何 lora 字段
        shot_id = shot.get("shot_id") or shot.get("id", "unknown")
        source = "per-shot" if "h3_lora" in shot else "episode"

        # 数值解析: 缺省 / "auto" (steps) = None = 不发字段; 不可解析 = 跳过
        # 该字段 + warning (字段级容错降级, 不炸批)。
        strength: float | None = None
        raw_strength = _pick("h3_lora_strength")
        if raw_strength is not None:
            try:
                strength = float(raw_strength)
            except (TypeError, ValueError):
                logger.warning(
                    "h3_engine: %s h3_lora_strength=%r 不可解析为 float — "
                    "跳过该字段 (KAP 落 registry 条目默认)",
                    shot_id, raw_strength,
                )
            else:
                if not math.isfinite(strength):  # NaN/inf 同垃圾串处理
                    logger.warning(
                        "h3_engine: %s h3_lora_strength=%r 非有限数值 — "
                        "跳过该字段 (KAP 落 registry 条目默认)",
                        shot_id, raw_strength,
                    )
                    strength = None
        steps: int | None = None
        raw_steps = _pick("h3_lora_steps")
        if raw_steps is not None and str(raw_steps).strip().lower() != "auto":
            try:
                steps = int(raw_steps)
            except (TypeError, ValueError):
                logger.warning(
                    "h3_engine: %s h3_lora_steps=%r 不可解析为 int — "
                    "跳过该字段 (KAP fall through 条目 steps)",
                    shot_id, raw_steps,
                )
                steps = None

        # 臂判定 (③) 先于 registry 读盘: 配置与臂的矛盾不依赖真源内容,
        # 禁挂臂直接 fail-loud, 不吃读盘失败的放行通道。
        use_case = H3VideoEngine._resolve_use_case(shot, episode_config)
        if H3VideoEngine._resolve_h3vdn(shot, episode_config, use_case):
            raise ValueError(
                f"h3_lora={name!r} 无法挂载: vdn-8 蓝图臂无通用 LoRA 槽位 "
                f"(profile-only 蓝图臂禁 generic lora)。修复: 摘除或显式抑制 "
                f"(h3_vdn=False) 该臂, 或摘除 h3_lora"
            )
        if H3VideoEngine._resolve_h3rh(shot, episode_config):
            raise ValueError(
                f"h3_lora={name!r} 无法挂载: rh-v4 蓝图臂 14_lora 是蓝图本体 "
                f"LoRA, 禁 generic lora。修复: 摘除或显式抑制 (h3_rh=False) "
                f"该臂, 或摘除 h3_lora"
            )
        if use_case == "final-shot":
            raise ValueError(
                f"h3_lora={name!r} 无法挂载: final-shot 臂 (native-sage) 无 "
                f"LoRA loader 节点。修复: 该 shot 改 h3_useCase=preview-lock "
                f"(唯一可挂臂), 或摘除 h3_lora"
            )

        registry = _load_lora_registry(shot_id)
        if registry is None:
            return None  # 真源读不了不禁渲染 (warning 已在 loader 打)
        entry = registry.get(name)
        if entry is None:
            raise ValueError(
                f"h3_lora={name!r} 不在 registry ({_H3_LORA_REGISTRY_PATH}, "
                f"env {_H3_LORA_REGISTRY_ENV} 可覆盖)。修复: 核对 registry "
                f"条目名 (loras[].name)"
            )
        status = entry.get("status")
        if status != "production":
            raise ValueError(
                f"h3_lora={name!r} status={status!r} 非 production (trial/"
                f"candidate 也拒, 生产线只挂 production)。修复: 等评审晋 "
                f"production, 或改挂 production 条目"
            )
        chain = entry.get("chain")
        if chain != _LORA_PREVIEW_LOCK_CHAIN:
            raise ValueError(
                f"h3_lora={name!r} chain={chain!r} 与 preview-lock 臂链族不 "
                f"兼容 (lightx2v-8-768p 属 SigmaShift 族, 只收 "
                f"chain=SigmaShift 条目)。修复: 换 chain=SigmaShift 条目"
            )
        return (name, strength, steps, source)

    # 2026-08-27 blockCache (KAP feat/h3-blockcache): MiniMaxH3BlockCacheT8
    # 注入开关透传。物理背书: Case08 高动态 15s/362f A/B −52.5%
    # (5381s→2555s, 命中 23/41, SSIM 0.7145)。KAP 侧仅 native-sage 链路消费
    # (turbo/T8 静默忽略), 故引擎不做 useCase 门控, 按配置透传。
    @staticmethod
    def _resolve_block_cache(shot: dict, episode_config: dict | None) -> bool:
        """blockCache 开关: shot.h3_blockCache > episode_config.h3_blockCache
        > off。对齐 KAP 线缆侧解析语义 (round-5 勘误): 大小写不敏感、去首尾
        空白后比对 {"on","true","1"}, 数字 1 同义接受; bool True 直接通过。
        其余值一律视为关 (shot 键存在即独占该决定权 —— 显式 False/"off" 是
        对 episode 级 true 的 per-shot 抑制, 不回落)。
        """
        if "h3_blockCache" in shot:
            raw = shot["h3_blockCache"]
        else:
            raw = (episode_config or {}).get("h3_blockCache")
        if raw is True:
            return True
        if isinstance(raw, str):
            return raw.strip().lower() in {"on", "true", "1"}
        return raw == 1  # 数字 1 同义; False/None/0/垃圾值等一律关

    @staticmethod
    def _resolve_block_cache_threshold(
        shot: dict, episode_config: dict | None,
    ) -> float | None:
        """blockCacheThreshold 透传: shot.h3_blockCacheThreshold >
        episode_config.h3_blockCacheThreshold > 不发送。仅当可解析为 [0,1]
        浮点才返回数值; 垃圾值/越界/NaN 静默返回 None (容错不抛异常),
        不发送时 KAP 侧回落自身默认 (residual_diff_threshold=0.4)。
        """
        if "h3_blockCacheThreshold" in shot:
            raw = shot["h3_blockCacheThreshold"]
        else:
            raw = (episode_config or {}).get("h3_blockCacheThreshold")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        return value if 0.0 <= value <= 1.0 else None  # NaN 两比较均 False

    @staticmethod
    def _resolve_prompt(shot: dict, prompt: str | None) -> str:
        """Enhanced prompt (caller passes _h3_enhance_prompt output); fallback
        to the shot's raw ``video_prompt`` (``ltx_prompt`` legacy alias) /
        ``prompt``."""
        if prompt:
            return prompt
        return (shot.get("video_prompt") or shot.get("ltx_prompt")
                or shot.get("prompt") or "").strip()

    def _build_multipart(
        self,
        shot: dict,
        *,
        prompt: str | None,
        episode_config: dict | None,
        turnaround_paths: list[str] | None,
        scene_ref_path: str | None,
        voice_clip_path: str | None,
        first_frame: str | None,
        lora: tuple[str, float | None, int | None, str] | None = None,
    ) -> list | None:
        """Build the multipart ``files`` list (text fields + binary parts).

        Returns None (with the caller degrading) when the prompt is missing —
        H3 rejects empty prompts, so we short-circuit before the POST.

        Text fields are encoded as ``(name, (None, value))`` parts so httpx
        ALWAYS emits ``multipart/form-data`` (matching the retired curl ``-F``
        semantics) — even for t2va shots that carry no reference files. (Passing
        text fields via ``data`` with no ``files`` would downgrade to
        ``application/x-www-form-urlencoded``, which the H3 API does not expect.)

        File handles are opened here and returned OPEN; ``render`` closes them in
        a ``finally`` (httpx has read them by the time the POST returns).
        """
        shot_id = shot.get("shot_id") or shot.get("id", "unknown")
        resolved_prompt = self._resolve_prompt(shot, prompt)
        if not resolved_prompt:
            return None
        # use_case 先解析 (2026-09-16): vdn 解析升级三层 (显式 shot/episode >
        # final 细节镜自动路由), 自动层按档位门控 —— final 档才自动 vdn,
        # 预览档永不自动 (显式配置不受此门)。
        use_case = self._resolve_use_case(shot, episode_config)
        vdn = self._resolve_h3vdn(shot, episode_config, use_case)
        rh = self._resolve_h3rh(shot, episode_config)
        # vdn shot 预钳到 226f (>226 的网格值 ≥243 必撞 KAP 400 守卫);
        # 非 vdn shot 原值透传 —— 逐字节不变 (rh-v4 蓝图无网格条款, 同样不钳;
        # 自动路由层已在 _route_vdn_final 把 >226f 细节镜排除, 不吃降档截断)。
        frames = _cap_vdn_frames(_compute_expected_frames(shot), vdn, shot)
        width, height = self._resolve_resolution(shot, episode_config, frames)
        # Text fields as filename-less multipart parts (forces multipart encoding).
        files: list = [
            ("projectId", (None, "1")),
            ("prompt", (None, resolved_prompt)),
            ("mode", (None, self._resolve_mode(shot, episode_config))),
            ("width", (None, str(width))),
            ("height", (None, str(height))),
            ("length", (None, str(frames))),
            ("filenamePrefix", (None, str(shot_id))),
        ]
        # useCase 入口 (2026-08-17 KAP API 精简): 取代旧的 profile/turbo/native/
        # tespeed/steps 平铺参数。步数/拓扑/音频管线由 KAP 侧 useCase 预射:
        #   preview-lock → motion 路由 (low→turbo4 / medium→turbo8 / high→native-sage15),
        #                  音频 tts-only (TTS 对白与 H3 原生音轨混音)
        #   final-shot   → native-sage 36 步 @1344×768, 完整 LTX Foley + TTS 混音
        # (use_case 已在上方 vdn 解析前取定 —— 两臂 profile-only 形态不发该字段。)
        if vdn:
            if rh:
                # 两臂同开裁决 (工单 C1): h3_vdn 优先 —— vdn-8 是审定 8 步
                # 蓝图臂, rh-v4 是快速档。裁决与理由见
                # docs/h3rh-route-DELIVERY.md。
                logger.info(
                    "h3_engine: %s h3_vdn 与 h3_rh 同开 — h3_vdn 优先 "
                    "(vdn-8 审定蓝图臂 > rh-v4 快速档)", shot_id,
                )
            # VDN 臂 (2026-09-09): per-shot/episode 显式选择 → profile-only
            # 形态, 不发 useCase/motion。C1 实探 generate.ts (d3eb69e0):
            #   L1001-1006 显式 profile 一票优先 (useCase 只提供默认值), 但
            #   L1054-1058 useCase 在场时 motionRoute/useCasePreset.steps 会
            #   劫持步数, 偏离 vdn-8 审定 8 步蓝图 (H3_VDN.steps); L1073-1074
            #   useCasePreset.audio 会覆盖 profile.skipFoley。不发 useCase 是
            #   唯一保证 KAP 按 H3_PROFILES["vdn-8"] 预射渲染的形态 (8 步
            #   er_sde+beta, skipFoley=true 直出原生音频 —— ttsAudio 不混入,
            #   见交付文档 §2 注意事项)。
            files.append(("profile", (None, VDN_PROFILE)))
            logger.info(
                "h3_engine: %s profile=%s (h3_vdn on; useCase suppressed)",
                shot_id, VDN_PROFILE,
            )
        elif rh:
            # rh-v4 臂 (2026-09-12): 显式 h3_rh 开关或 _route_rh 场景路由命中
            # → profile-only 形态 (同 vdn 先例, C1 实探同源: useCase 在场时
            # useCasePreset.steps/audio 会劫持步数/音频预射, 偏离 H3_RH_V4
            # 4 步恒定 + 14_lora 恒载蓝图)。length 原值透传 —— 蓝图无帧网格
            # 约束 (0911 双批 229f/243f 均过 400 守卫), 不做 vdn 式预钳。
            files.append(("profile", (None, RH_V4_PROFILE)))
            logger.info(
                "h3_engine: %s profile=%s (h3_rh on; useCase suppressed)",
                shot_id, RH_V4_PROFILE,
            )
        else:
            files.append(("useCase", (None, use_case)))
            if use_case == "preview-lock":
                # motion 驱动 KAP 侧动态路由 (低4/中8/高15), 默认 medium。
                motion = shot.get("h3_motion") or (episode_config or {}).get("h3_motion", "medium")
                files.append(("motion", (None, motion)))
        # H3 通用 LoRA 槽位 (2026-09-22): lora/lora_strength/lora_steps 三字段
        # 透传, 追加在 useCase/motion/profile 分支之后、blockCache 之前 (仿
        # blockCache 先例)。禁挂臂/非法条目已在 render() 的 _route_lora 预检
        # fail-loud 拦下, 本层是纯透传; None 成员不发字段 (KAP 落 registry
        # 条目默认)。无 lora 配置的 shot 不追加任何字段 —— multipart 与改动
        # 前逐字节等价 (红线)。
        if lora is not None:
            lora_name, lora_strength, lora_steps, lora_source = lora
            if lora_name:
                files.append(("lora", (None, lora_name)))
            if lora_strength is not None:
                files.append(("lora_strength", (None, str(lora_strength))))
            if lora_steps is not None:
                files.append(("lora_steps", (None, str(lora_steps))))
            logger.info(
                "h3_engine: %s lora=%s strength=%s steps=%s (source=%s)",
                shot_id, lora_name, lora_strength, lora_steps, lora_source,
            )
        # 意图驱动 auto_attach (2026-09-28 批次2, KAP 8c794fcf 的 KMC 消费端):
        # 无显式 h3_lora 配置 (lora is None = _route_lora 未命中) 时解析中文
        # camera_move 意图, 命中白名单则透传 trigger 语义, 由 KAP 查 registry
        # ``auto_attach.trigger === "camera_move:<trigger>"`` 自动挂载。显式 >
        # 自动 (Kai 0927 设计律): lora 在场时跳过意图解析, 也省一次查表。
        # 未命中/空值不追加任何字段 —— multipart 与改动前逐字节等价 (红线);
        # 装配失败 (条目不在/overlay 条目/引擎不可见) 由 KAP 侧降级
        # prompt-only 继续渲染, 引擎侧绝不 fail-loud (增强不是依赖)。
        if lora is None:
            trigger = resolve_camera_move_trigger(shot)
            if trigger is not None:
                files.append(("camera_move", (None, trigger)))
                logger.info(
                    "h3_engine: %s camera_move=%s → auto_attach trigger"
                    "（装配失败由 KAP 侧降级）",
                    shot_id, trigger,
                )
        # blockCache (2026-08-27): 追加在 useCase/motion 文本字段之后、refImages
        # 之前。默认不发字段 —— 无配置 shot 的字段序列与改动前逐字节等价。
        block_cache = self._resolve_block_cache(shot, episode_config)
        block_cache_threshold = self._resolve_block_cache_threshold(shot, episode_config)
        if block_cache:
            files.append(("blockCache", (None, "true")))
            logger.info(
                "h3_engine: %s blockCache on (threshold=%s)",
                shot_id,
                block_cache_threshold if block_cache_threshold is not None else "default",
            )
        if block_cache_threshold is not None:
            files.append(("blockCacheThreshold", (None, str(block_cache_threshold))))
        # final-shot: 无附加参数 — profile/steps/audioMix 全部由 KAP useCase 预射。
        # refImages[]: character turnarounds + scene background (≤9 total).
        ref_paths: list[str] = []
        for p in (turnaround_paths or []):
            if isinstance(p, str) and p.strip():
                ref_paths.append(p.strip())
        if scene_ref_path and isinstance(scene_ref_path, str) and scene_ref_path.strip():
            ref_paths.append(scene_ref_path.strip())
        for p in ref_paths[:9]:
            if os.path.isfile(p):
                files.append(("refImages", (os.path.basename(p), open(p, "rb"), "image/png")))
            else:
                logger.debug("h3_engine: refImages skip missing file %s", p)
        # ttsAudio: TTS dialogue audio (optional).
        if voice_clip_path and os.path.isfile(voice_clip_path):
            files.append(("ttsAudio", (os.path.basename(voice_clip_path), open(voice_clip_path, "rb"), "audio/wav")))
        # image: first-frame lock for i2va (optional).
        if first_frame and os.path.isfile(first_frame):
            files.append(("image", (os.path.basename(first_frame), open(first_frame, "rb"), "image/png")))
        return files

    def _post(self, files: list) -> Any:
        """Central HTTP wrapper enforcing D-09 degrade / raise contract.

        D-09 degrade / raise contract (mirrors the retired
        ``LTXVideoEngine._request``, 2026-09-02):
        - ConnectError / TimeoutException / HTTPError -> degrade envelope.
        - status >= 500 or status == 429 -> degrade envelope.
        - status >= 400 -> raise ``VideoEngineError`` (caller bug).
        - 2xx -> parse JSON; invalid JSON -> raise (service bug).
        """
        url = f"{self._base_url}{self.H3_PATH}"
        headers = {"X-KAP-Caller-Tag": self._caller_tag} if self._caller_tag else None
        try:
            response = self._client.post(url, files=files, headers=headers)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            return self._degrade(f"{type(exc).__name__}: {exc}")
        except httpx.HTTPError as exc:
            return self._degrade(f"{type(exc).__name__}: {exc}")

        status = response.status_code
        text = response.text

        if status >= 500 or status == 429:
            return self._degrade(f"HTTP {status}")

        if status >= 400:
            # 4xx is a caller bug - raise, do not degrade.
            raise VideoEngineError(f"HTTP {status}: {text[:200]}")

        # 2xx - parse JSON. Invalid JSON is a service-side bug, so raise.
        try:
            return response.json()
        except Exception:
            raise VideoEngineError(f"Invalid JSON response: {text[:200]}")

    def _download(self, video_url: str, output_path: str) -> str | None:
        """Stream-download the produced clip to ``output_path``.

        ``video_url`` may be absolute or relative to ``base_url``. Returns the
        output_path on success, None on any download failure (caller degrades).
        On failure the specific cause is stored in ``self._last_download_error``
        so the caller's degrade reason can distinguish local-fs problems
        (e.g. PermissionError on makedirs) from HTTP errors instead of
        lumping both under a misleading "download failed".

        KAP returns ``/mnt/agents/output/xxx.mp4`` as the video URL, but that
        path requires auth (401). The ``/oss/`` route serves the same files
        without auth (fallback static mount). Rewrite the path accordingly.
        """
        self._last_download_error = ""
        if not video_url:
            self._last_download_error = "empty video_url"
            return None
        # Rewrite /mnt/agents/output/ → /oss/ (auth-free fallback route)
        if video_url.startswith("/mnt/agents/output/"):
            video_url = video_url.replace("/mnt/agents/output/", "/oss/", 1)
        if video_url.startswith("http://") or video_url.startswith("https://"):
            url = video_url
        else:
            url = f"{self._base_url}/{video_url.lstrip('/')}"
        try:
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with self._client.stream("GET", url) as resp:
                if resp.status_code >= 400:
                    self._last_download_error = f"http {resp.status_code} for {url}"
                    return None
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
            if os.path.isfile(output_path):
                return output_path
            self._last_download_error = f"missing output file {output_path!r}"
            return None
        except OSError as exc:
            # Local filesystem problem (unwritable dir, PermissionError on
            # makedirs, disk full...) — NOT a download/HTTP failure.
            self._last_download_error = f"local fs error for {output_path!r}: {exc}"
            return None
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
            self._last_download_error = f"{type(exc).__name__}: {exc} for {url}"
            return None

    def render(
        self,
        *,
        shot: dict,
        output_path: str,
        turnaround_paths: list[str] | None = None,
        scene_ref_path: str | None = None,
        voice_clip_path: str | None = None,
        first_frame: str | None = None,
        prompt: str | None = None,
        episode_config: dict | None = None,
    ) -> dict:
        """Render one shot via the H3 unified pipeline and frame-validate.

        Input validation (missing prompt / output) short-circuits to degrade
        envelopes before any network call. Explicit ``h3_lora`` config runs
        the ``_route_lora`` preflight first — a forbidden arm / invalid
        registry entry raises ``ValueError`` (fail-loud: never silently
        render without a configured LoRA). The POST is serialized under
        ``_lock`` (WR-01). After download the P0-4 frame gate runs inline — a
        clip that probes as duration-ok but frame-count-mismatched (trim_bypass)
        is rejected as a degrade rather than shipped.

        INFO #10: ``generation_time_ms`` is LOCALLY-measured wall time; the
        response body's reported timing is IGNORED.
        """
        if not output_path:
            return self._degrade("missing output_path")
        if not isinstance(shot, dict) or not shot:
            return self._degrade("missing shot")

        # T2 需求侧预检 (2026-09-22): 显式 h3_lora 配置先过 registry/臂校验,
        # 禁挂臂/非法条目 fail-loud ValueError (禁静默跳过 = 整批裸奔); 无
        # 配置/真源读不了 → None, multipart 保持改动前逐字节等价。解析结果只
        # 进局部变量, 禁改 shot dict (多臂共享输入)。
        lora = self._route_lora(shot, episode_config)
        built = self._build_multipart(
            shot,
            prompt=prompt,
            episode_config=episode_config,
            turnaround_paths=turnaround_paths,
            scene_ref_path=scene_ref_path,
            voice_clip_path=voice_clip_path,
            first_frame=first_frame,
            lora=lora,
        )
        if built is None:
            return self._degrade("missing prompt")
        files = built

        start = time.monotonic()
        try:
            with self._lock:  # WR-01: serialize POST across worker threads.
                result = self._post(files)
        finally:
            # Close all opened file handles (httpx has read them by now). Text
            # parts are (None, str) — no handle to close; binary parts are
            # (filename, fh, content_type) — close fh.
            for _field, payload in files:
                fh = payload[1] if isinstance(payload, tuple) and len(payload) >= 2 else None
                if hasattr(fh, "close"):
                    try:
                        fh.close()
                    except Exception:
                        pass

        # Pass-through degrade envelope (already shaped by _degrade).
        if isinstance(result, dict) and result.get("degraded"):
            return result

        # --- BUG FIX: KAP wraps responses in {"code":200,"data":{...}}.
        # Unwrap the data layer, then handle camelCase/snake_case mismatch
        # (KAP returns "videoUrl", engine expects "video_url").
        if isinstance(result, dict) and isinstance(result.get("data"), dict):
            result = result["data"]

        video_url = None
        if isinstance(result, dict):
            video_url = result.get("video_url") or result.get("videoUrl")

        # Validate response shape: must carry a video_url to download.
        if not video_url:
            return self._degrade("missing video_url in h3 response")

        clip_path = self._download(video_url, output_path)
        if not clip_path:
            detail = self._last_download_error or "download failed"
            return self._degrade(f"download failed ({detail}) for {video_url!r}")

        # P0-4 frame-count hard gate (inline). vdn shots gate against the
        # CAPPED length actually requested — gating on the raw snap would
        # false-fail every >226f downgraded shot as trim_bypass. vdn 判定与
        # _build_multipart 同源 (_resolve_h3vdn 三层解析, 同一 use_case 门)。
        expected = _cap_vdn_frames(
            _compute_expected_frames(shot),
            self._resolve_h3vdn(
                shot, episode_config, self._resolve_use_case(shot, episode_config),
            ),
            shot,
        )
        ok, reason = self._frame_validator(clip_path, expected)
        if not ok:
            # Remove the bad clip so a re-render isn't masked by a stale file.
            try:
                os.remove(clip_path)
            except OSError:
                pass
            return self._degrade(f"frame validation failed: {reason}")

        return {
            "clip_path": clip_path,
            "generation_time_ms": self._record_time(start),
            "engine": "h3",
            "frame_count": expected,
            "video_url": video_url,
        }

    # ------------------------------------------------------------------
    # Lifecycle (mirrors the retired LTXVideoEngine, 2026-09-02)
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying httpx client.

        Per-instance, single-owner semantics (WR-01 / C1): p11b constructs
        one H3VideoEngine per fan-out worker and closes each exactly once
        after the pool joins. Closing releases ONLY this instance's
        connection pool — sibling per-worker instances are unaffected.
        """
        self._client.close()

    def __enter__(self) -> "H3VideoEngine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
