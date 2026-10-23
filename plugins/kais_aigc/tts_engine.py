"""tts_engine.py - TTSEngine in-process adapter for P10 voice (P1-3).

Mirrors the ``preview_engine.py`` engine-adapter pattern (Plan 40-02 /
``LTXVideoEngine``): instead of embedding ``curl`` one-liners in the P10
delegate goal (the v15.2 "soft command" anti-pattern — see
``kmc-soft-command-scriptability``), the two-phase Qwen3-TTS workflow runs
IN-PROCESS here, deterministically and mockably.

Two-phase workflow (validated 2026-07-29, verbatim from the retired P10 goal):

- **Phase 1 — ``design_voice``**: POST ``{mode:"voice_design", text, instruct,
  seed, unload_model_after_generate:true}`` to ``:10588/api/v1/tts/speak`` once
  per character. Downloads the ``audio_url`` result (NOT ``audio_path`` — that
  is container-internal) to a reference FLAC and publishes it into the ComfyUI
  input dir so Phase 2 can clone from it.
- **Phase 2 — ``clone_voice``**: POST ``{mode:"voice_clone", text, ref_audio,
  ref_text, seed}`` per dialogue line. Downloads the result, converts
  FLAC→WAV (24 kHz mono) via FFmpeg, and runs ``volumedetect`` to enforce the
  MUTE HARD GATE (mean_volume <= -80 dB → degrade envelope). This is the
  in-process enforcement of the mute-WAV ban that previously lived only as a
  goal-hint string (the soft path that produced mute videos).

Design invariants (mirror ``preview_engine.py``):
- D-04: ``transport`` (``httpx.BaseTransport``) + ``subprocess_runner`` ctor
  kwargs let tests inject ``httpx.MockTransport`` / a fake runner for hermetic
  testing. Every argv + every HTTP body is assertable without a GPU service.
- D-06: config is read at construction time (env vars), never at import.
- D-09: degrade-first contract. Connect / timeout / 5xx / 429 → degrade
  envelope ``{"degraded": True, ...}`` (never raise to the caller). 4xx and
  invalid-JSON 2xx raise ``TTSEngineError`` (caller / service bug).
  EXCEPTION (2026-08-16 P10 fix): HTTP 503 ``kind=vram_insufficient`` is
  retried with exponential backoff (60s/120s/300s) BEFORE degrading — the KAP
  GPU queue needs time to drain, not an instant batch collapse.
- INFO #10: ``generation_time_ms`` is LOCALLY-measured wall time
  (``time.monotonic()``), ignoring any service-reported timing.

Two-phase ASYNC mode (2026-08-16 P10 double-timeout fix): ``_post_async``
submits with ``{"async": true}`` → KAP returns 202 ``{prompt_id}`` after the
GPU-queue acquire + ComfyUI submit (no synthesis wait), then polls
``GET /api/v1/tts/status/{prompt_id}`` every 5s (30min budget). The client's
per-request HTTP timeout no longer bounds "queue wait + job" total time —
the 21:48 incident had 677s queue wait > 360s client timeout → ReadTimeout ×3
→ 24 clones 400 → engine_mute hard-gate collapse. Non-202 responses (older
KAP without the async route) fall back to the synchronous path transparently.

This module is pure library code — the p10 phase module (P1-3) composes it.
NO phase integration here.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mute gate threshold
# ---------------------------------------------------------------------------
# A WAV whose ``mean_volume`` (ffmpeg volumedetect) is at or below this is
# considered SILENT — almost certainly a TTS failure (the model produced a
# near-zero waveform). Such clips MUST NOT flow to P11/P12 (they waste a full
# render pass and produce mute master.mp4). The engine returns a degrade
# envelope instead. -80 dB matches the retired goal hint ("mean_volume should
# be > -80dB") — promoted from advisory text to an enforced hard gate.
SILENT_MEAN_VOLUME_DB = -80.0

# Degrade ``kind`` taxonomy (ep-demo-pixar P0, matrix #2): the mute hard-gate
# in p10_voice must distinguish "the engine is down" (HTTP 5xx / connect /
# timeout — retrying via delegate cannot help; fix the engine then resume)
# from "the engine produced a bad clip" (volume gate / conversion failure —
# the existing retry→drop semantics are correct). ``_degrade`` stamps this
# on every envelope; callers default missing ``kind`` to "quality" so
# legacy/foreign envelopes keep the historical behavior.
DEGRADE_KIND_ENGINE_UNAVAILABLE = "engine_unavailable"
DEGRADE_KIND_QUALITY = "quality"


def _degrade_kind(reason: str) -> str:
    """Classify a degrade ``reason`` string into the kind taxonomy.

    Engine-side failures (HTTP 5xx/429, ConnectError/ReadTimeout/other
    httpx transport errors) → ``engine_unavailable``. Everything else
    (silent clip, ffmpeg failure, missing fields, long-instruct OOM guard)
    → ``quality`` (the engine answered; the output was unusable).
    """
    r = str(reason)
    if r.startswith(("HTTP 5", "HTTP 429", "VoiceDesign HTTP 5",
                     "VoiceDesign HTTP 429", "ConnectError", "ConnectTimeout",
                     "ReadTimeout", "WriteTimeout", "PoolTimeout", "Timeout",
                     "NetworkError", "ProtocolError", "RemoteProtocolError",
                     "HTTPError")):
        return DEGRADE_KIND_ENGINE_UNAVAILABLE
    return DEGRADE_KIND_QUALITY

# Qwen3-TTS VoiceDesign ``instruct`` length limit (validated root cause of the
# CUDA OOM that plagued v15.1 per-clip design). Long instruct explodes the KV
# cache. The engine enforces this BEFORE the POST so a buggy upstream
# character-bible cannot OOM the GPU.
MAX_INSTRUCT_CHARS = 20

# FFmpeg flac→wav conversion target. Qwen3-TTS + the downstream 5stage audio
# pipeline expect 24 kHz mono PCM. Matches the retired goal one-liner
# ``ffmpeg -y -i <in>.flac -ar 24000 -ac 1 <out>.wav``.
TTS_SAMPLE_RATE = 24000

# KAP breezeTts voice-design compat layer hard-400s an empty ``instruct``
# ("Missing required field: instruct (voice description)"). Narrator-style
# characters legitimately have none (no voice-design line in the script), and
# that 400 degraded the narrator ref → every clone → 3 QA reject rounds on
# ep-mv-guangdexiaoxi (2026-10-13). ``IndexTTS25Engine.design_voice`` fills an
# empty/whitespace instruct with a deterministic per-character default BEFORE
# the POST; a non-empty instruct is forwarded byte-identical. Both defaults
# stay under MAX_INSTRUCT_CHARS — OOM-guard semantics preserved (default
# first, then the guard budget still holds).
DEFAULT_INSTRUCT_NARRATOR = "温柔清晰的旁白女声"
DEFAULT_INSTRUCT_GENERIC = "清晰自然的人声"
_NARRATOR_NAME_TAGS = ("narrator", "旁白", "voiceover")


def _default_instruct_for(char: str) -> str:
    """Deterministic empty-``instruct`` default for ``char`` (pure).

    Narrator-style names (contains ``narrator`` / ``旁白`` / ``voiceover``,
    case-insensitive) get a fixed narration voice; everything else a fixed
    neutral voice. Same input → same output, so voice identity is stable
    across resume runs.
    """
    lowered = char.lower()
    if any(tag in lowered for tag in _NARRATOR_NAME_TAGS):
        return DEFAULT_INSTRUCT_NARRATOR
    return DEFAULT_INSTRUCT_GENERIC


class TTSEngineError(Exception):
    """Raised for 4xx client errors from the TTS service (caller bug).

    Mirrors ``PreviewEngineError`` semantics: connection errors / timeouts /
    5xx / 429 do NOT raise — they degrade (return ``{"degraded": True, ...}``
    envelope to the caller). 4xx and invalid-JSON 2xx responses are caller /
    service bugs and raise this exception.
    """


def _is_vram_insufficient(text: str) -> bool:
    """True iff a KAP error body carries kind=vram_insufficient.

    KAP 返回形如 ``{"code":400,"data":{"error":{"kind":"vram_insufficient",
    ...}},"message":"vram_insufficient: ..."}`` 或 message 文本直接含
    ``vram_insufficient`` (gpuVramManager.VramInsufficientError.message)。
    两种形态都识别 — 不 parse JSON (body 可能被截断/非 JSON)。
    """
    return "vram_insufficient" in (text or "")


class TTSEngine:
    """In-process Qwen3-TTS two-phase voice engine (P1-3).

    POSTs to ``/api/v1/tts/speak`` on the aigc-platform (default
    ``http://localhost:10588``) and returns produced WAV paths. Mirrors
    ``LTXVideoEngine`` structure EXACTLY for the D-09 degrade-first contract.

    Phase methods:
    - ``design_voice(...)`` — Phase 1: one ref audio per character.
    - ``clone_voice(...)`` — Phase 2: per-line clone + flac→wav + mute gate.

    Lifecycle: use as a context manager (``with TTSEngine() as eng:``) so the
    underlying ``httpx.Client`` connection pool is released. Mirrors
    ``LTXVideoEngine.__enter__/__exit__``.
    """

    DEFAULT_BASE_URL = "http://localhost:10588"
    # 7200s (2h, 2026-08-16 P10 双重超时修复). 旧值 360s 的设计意图是
    # "client budget > KAP poll 300s", 但 withGpuQueue 上线后单请求生命周期变成
    # 「GPU 排队 (最长 30min) + 作业 (~35s)」, 且 P10 一批 design_voice + 24 条
    # clone 会连续排队多次 — 21:48 事故实测排队 677s > 360s, 3 个 design_voice
    # 全部 httpx ReadTimeout → clone 全 400 → engine_mute 硬门崩。
    # 7200s = 4× KAP_GPU_QUEUE_TIMEOUT (30min) 余量。
    DEFAULT_TIMEOUT = 7200.0

    # vram_insufficient (HTTP 503 kind=vram_insufficient) 重试退避 — 给 GPU
    # 队列时间消化, 而不是立刻 degrade (KAP 侧 30min 排队超时后才抛这个错,
    # 说明队列确实满了; 但短暂撞车 (qwen-eye 拉起瞬间) 也会触发)。3 次
    # 60s/120s/300s 共 8min, 仍失败才降级。
    VRAM_RETRY_BACKOFF_S = (60.0, 120.0, 300.0)

    # 两段式异步轮询 (async 202 模式): 每 5s 查一次 status, 总预算 30min。
    # 客户端单请求超时不再约束「排队 + 作业」总时长。
    ASYNC_POLL_INTERVAL_S = 5.0
    ASYNC_POLL_BUDGET_S = 1800.0

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
        comfyui_input_dir: str | None = None,
        comfyui_container: str | None = None,
        subprocess_runner: Callable[[list[str]], Any] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        """Construct the engine.

        Parameters (D-06 env-var config at construction time, never import):

        - ``base_url`` / ``KAIS_TTS_URL``: aigc-platform TTS service base URL.
        - ``timeout``: per-request timeout in seconds (default 7200).
        - ``transport``: hermetic test injection via ``httpx.MockTransport``.
          ``None`` (default) uses real networking.
        - ``comfyui_input_dir``: host-side path that maps to ComfyUI's
          ``/root/ComfyUI/input`` (shared volume) — when set, ref audios are
          written directly there. ``None`` falls back to ``docker cp``.
        - ``comfyui_container``: container name for the ``docker cp`` fallback
          (default ``comfyui-primary``).
        - ``subprocess_runner``: test seam for FFmpeg / docker (SlideshowEngine
          pattern). When given, called as ``runner(argv)`` returning a
          ``subprocess.CompletedProcess``-like object. ``None`` (production)
          uses the real ``subprocess.run`` + ``shutil.which`` validation.
        - ``sleep``: test seam for the vram_insufficient backoff retries
          (2026-08-16). ``None`` (production) uses real ``time.sleep`` — tests
          inject a no-op recorder so 60s/120s/300s backoffs don't wall-clock.
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_TTS_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        # transport=None -> real network; tests inject httpx.MockTransport.
        self._client = httpx.Client(timeout=self._timeout, transport=transport)
        self._comfyui_input = comfyui_input_dir
        self._comfyui_container = comfyui_container or "comfyui-primary"
        self._runner = subprocess_runner
        self._sleep = sleep or time.sleep

    # ------------------------------------------------------------------
    # D-09 degrade / raise helpers
    # ------------------------------------------------------------------

    def _degrade(self, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope and log a warning (D-09).

        Mirrors ``LTXVideoEngine._degrade`` shape (engine-tagged), plus a
        ``kind`` classification (engine_unavailable vs quality) so the p10
        mute hard-gate can fail-fast on engine outage instead of retrying.
        """
        logger.warning("tts_engine degraded: %s", reason)
        return {
            "degraded": True,
            "engine": "Qwen3-TTS-1.7B",
            "reason": reason,
            "kind": _degrade_kind(reason),
        }

    def _submit(self, body: dict, *, async_mode: bool = False) -> httpx.Response | dict:
        """Single-shot POST /speak with the vram_insufficient retry loop.

        Shared by ``_post`` (synchronous) and ``_post_async`` (202 mode) so
        the retry budget is spent exactly once per logical request — the async
        path must NOT re-POST after a failed submit (a duplicate POST would
        synthesize the same line twice).

        ``vram_insufficient`` (HTTP 503 kind=vram_insufficient) is retried
        with exponential backoff (60s/120s/300s, ``VRAM_RETRY_BACKOFF_S``) to
        give the KAP GPU queue time to drain (2026-08-16 P10 fix; previously
        any 503 collapsed the whole batch).

        Returns the terminal ``httpx.Response`` (any status — the caller
        classifies), or a degrade envelope dict on transport failure.
        """
        url = f"{self._base_url}/api/v1/tts/speak"
        payload = {**body, "async": True} if async_mode else body
        response: httpx.Response | None = None
        for attempt in range(len(self.VRAM_RETRY_BACKOFF_S) + 1):
            if attempt > 0:
                backoff = self.VRAM_RETRY_BACKOFF_S[attempt - 1]
                logger.info(
                    "tts_engine: vram_insufficient retry %d/%d in %.0fs",
                    attempt, len(self.VRAM_RETRY_BACKOFF_S), backoff,
                )
                self._sleep(backoff)
            try:
                response = self._client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                return self._degrade(f"{type(exc).__name__}: {exc}")
            except httpx.HTTPError as exc:
                return self._degrade(f"{type(exc).__name__}: {exc}")
            status = response.status_code
            is_vram = status == 503 and _is_vram_insufficient(response.text)
            if not (is_vram and attempt < len(self.VRAM_RETRY_BACKOFF_S)):
                break  # terminal — classify at the call site
        assert response is not None
        return response

    def _classify_response(self, response: httpx.Response) -> Any:
        """D-09 classification of a terminal submit response.

        - 503 vram_insufficient (loop already exhausted) → degrade envelope.
        - status >= 500 or 429 → degrade envelope.
        - status >= 400 → raise ``TTSEngineError`` (caller bug).
        - 2xx → parsed JSON; invalid JSON → raise (service-side bug).
        """
        status = response.status_code
        text = response.text
        if status == 503 and _is_vram_insufficient(text):
            # Retries already spent inside _submit — queue cannot drain.
            return self._degrade(f"HTTP 503 vram_insufficient: {text[:200]}")
        if status >= 500 or status == 429:
            # Keep the service's error body (first 200 chars, matching the
            # 4xx branch below) — "HTTP 500" alone hides the KAP-side cause
            # (e.g. "TTS failed: node not registered") from the operator.
            return self._degrade(f"HTTP {status}: {text[:200]}")
        if status >= 400:
            raise TTSEngineError(f"HTTP {status}: {text[:200]}")
        try:
            return response.json()
        except Exception:
            raise TTSEngineError(f"Invalid JSON response: {text[:200]}")

    def _post(self, body: dict) -> Any:
        """Synchronous POST /speak enforcing the D-09 degrade / raise contract.

        Mirrors ``LTXVideoEngine._request``:
        - ConnectError / TimeoutException / HTTPError -> degrade envelope.
        - status >= 500 or status == 429 -> degrade envelope.
        - status >= 400 -> raise ``TTSEngineError`` (caller bug).
        - 2xx -> parse JSON; invalid JSON -> raise (service-side bug).
        """
        response = self._submit(body)
        if isinstance(response, dict):
            return response  # transport-level degrade from _submit
        return self._classify_response(response)

    def _post_async(self, body: dict) -> Any:
        """Two-phase async submit (KAP 202 mode, 2026-08-16).

        POSTs ``body + {"async": true}``; KAP acquires the GPU queue, submits
        to ComfyUI and immediately returns 202 ``{prompt_id, queue_wait_ms}``.
        Then polls ``GET /api/v1/tts/status/{prompt_id}`` every 5s until
        success/error or the 30min budget — the per-request HTTP timeout no
        longer bounds "queue wait + job" total time (P10 root cause).

        Non-202 terminal responses are classified in place (never re-POSTed —
        a duplicate submit would synthesize the same line twice): 2xx = older
        KAP that ignored the async flag and answered synchronously → use that
        result directly; 4xx/5xx/429/vram-exhausted → the standard D-09
        contract (raise / degrade).
        """
        response = self._submit(body, async_mode=True)
        if isinstance(response, dict):
            return response  # transport-level degrade from _submit

        if response.status_code != 202:
            return self._classify_response(response)

        try:
            accepted = response.json().get("data") or {}
        except Exception:
            return self._degrade("invalid JSON from async speak response")

        prompt_id = accepted.get("prompt_id")
        if not prompt_id:
            return self._degrade("async speak response missing prompt_id")

        status_url = f"{self._base_url}/api/v1/tts/status/{prompt_id}"
        deadline = time.monotonic() + self.ASYNC_POLL_BUDGET_S
        while time.monotonic() < deadline:
            self._sleep(self.ASYNC_POLL_INTERVAL_S)
            try:
                resp = self._client.get(status_url)
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning(
                    "tts_engine: status poll hiccup (%s: %s) — retrying",
                    type(exc).__name__, exc,
                )
                continue
            if resp.status_code >= 500 or resp.status_code == 429:
                continue  # transient server-side; keep polling within budget
            if resp.status_code >= 400:
                raise TTSEngineError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            try:
                data = (resp.json() or {}).get("data") or {}
            except Exception:
                continue
            state = data.get("status")
            if state == "success":
                return data  # {prompt_id, status, audio_url, audio_path, ...}
            if state == "error":
                return self._degrade(f"TTS job failed: {data.get('error', 'unknown')}")
            # pending / running — keep polling
        return self._degrade(
            f"async status poll exceeded {self.ASYNC_POLL_BUDGET_S:.0f}s budget "
            f"for {prompt_id}"
        )

    def _download(self, url: str) -> bytes | None:
        """Download ``url`` (an ``audio_url``) and return raw bytes.

        Resolves relative URLs against ``_base_url``. Applies the D-09 contract
        (network / 5xx / 429 -> None; 4xx -> None+warn rather than raise, since
        a missing audio is a degrade condition, not a caller bug at this layer).
        """
        if not url:
            return None
        full = url if url.startswith(("http://", "https://")) else f"{self._base_url}/{url.lstrip('/')}"
        try:
            resp = self._client.get(full)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
            logger.warning("tts_engine download failed (%s): %s", type(exc).__name__, exc)
            return None
        if resp.status_code >= 400:
            logger.warning("tts_engine download HTTP %s for %s", resp.status_code, full)
            return None
        return resp.content

    # ------------------------------------------------------------------
    # subprocess seam (FFmpeg + docker cp)
    # ------------------------------------------------------------------

    def _run_subprocess(self, argv: list[str], *, timeout: int = 120) -> Any:
        """Run ``argv`` via the injected runner or real ``subprocess.run``.

        Returns the ``subprocess.CompletedProcess``-like result. Raises
        ``RuntimeError`` on missing binary / timeout so callers can convert to a
        degrade or fail-loud as appropriate.
        """
        runner = self._runner
        try:
            if runner is not None:
                return runner(argv)
            return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError as exc:
            raise RuntimeError(f"binary not found for {argv[0]!r}: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{argv[0]!r} timed out ({timeout}s)") from exc

    def _ffmpeg_available(self) -> bool:
        """True iff ffmpeg is usable (skipped when a test runner is injected)."""
        if self._runner is not None:
            return True
        return shutil.which("ffmpeg") is not None

    def _publish_ref_to_comfyui(self, local_path: str, name: str) -> bool:
        """Make ``local_path`` available to ComfyUI input as ``name``.

        Prefers a direct write into a shared ``comfyui_input_dir`` (no docker
        dependency); falls back to ``docker cp`` into the container. Returns
        True on success / skip, False on hard failure (caller degrades).

        Failures are non-fatal warnings in the shared-volume case — the local
        ref file still exists for any downstream that reads it directly.
        """
        # Shared-volume fast path: write directly.
        if self._comfyui_input:
            try:
                target = os.path.join(self._comfyui_input, name)
                # Copy (not move) so the local ref is preserved for P10 records.
                shutil.copyfile(local_path, target)
                return True
            except OSError as exc:
                logger.warning(
                    "tts_engine: cannot write ref to comfyui_input %s: %s — "
                    "trying docker cp fallback", self._comfyui_input, exc,
                )
        # docker cp fallback.
        argv = ["docker", "cp", local_path, f"{self._comfyui_container}:/root/ComfyUI/input/{name}"]
        try:
            result = self._run_subprocess(argv, timeout=60)
        except RuntimeError as exc:
            logger.warning("tts_engine: docker cp ref failed: %s", exc)
            return False
        if getattr(result, "returncode", 0) != 0:
            stderr = getattr(result, "stderr", "") or ""
            logger.warning("tts_engine: docker cp ref exited %s: %s",
                           getattr(result, "returncode", "?"), str(stderr)[:200])
            return False
        return True

    # ------------------------------------------------------------------
    # Phase 1 — VoiceDesign (one ref audio per character)
    # ------------------------------------------------------------------

    def design_voice(
        self,
        *,
        char: str,
        ref_line: str,
        instruct: str,
        seed: int,
        ref_dir: str | None = None,
    ) -> dict[str, Any]:
        """Phase 1: generate ONE reference audio for a character.

        POSTs ``{mode:"voice_design", text:ref_line, instruct, seed,
        unload_model_after_generate:true}``, downloads the ``audio_url`` to a
        FLAC, and publishes it into ComfyUI input for Phase 2 cloning.

        Args:
            char: Character identifier (used for the ref filename).
            ref_line: Short reference line spoken in the design voice.
            instruct: SHORT voice description (<=20 chars). Longer instruct
                causes CUDA OOM — enforced here as a degrade gate.
            seed: Fixed per-character seed for reproducible voice identity.
            ref_dir: Directory to write the local ref FLAC. ``None`` uses a
                temp dir.

        Returns:
            Success envelope ``{"ref_audio": <comfyui filename>, "ref_local":
            <host path>, "generation_time_ms": int, "engine": "Qwen3-TTS-1.7B"}``
            or a degrade envelope ``{"degraded": True, ...}``.
        """
        # OOM guard: long instruct explodes the KV cache (validated root cause).
        if instruct and len(instruct) > MAX_INSTRUCT_CHARS:
            return self._degrade(
                f"instruct too long ({len(instruct)}>{MAX_INSTRUCT_CHARS} chars) — "
                f"truncated to avoid CUDA OOM: {instruct!r}"
            )

        body = {
            "mode": "voice_design",
            "text": ref_line,
            "instruct": instruct,
            "seed": seed,
            "unload_model_after_generate": True,
        }
        start = time.monotonic()
        result = self._post_async(body)
        if isinstance(result, dict) and result.get("degraded"):
            return result

        if isinstance(result, dict) and "data" in result and isinstance(result["data"], dict):
            result = result["data"]
        audio_url = result.get("audio_url") if isinstance(result, dict) else None
        if not audio_url:
            # audio_path is container-internal (inaccessible) — only audio_url
            # is reachable from the host. Missing audio_url = unusable result.
            return self._degrade("missing audio_url in voice_design response")

        data = self._download(audio_url)
        if not data:
            return self._degrade(f"audio download failed for {audio_url}")

        # Persist the local ref FLAC.
        ref_dir = ref_dir or _default_ref_dir()
        try:
            os.makedirs(ref_dir, exist_ok=True)
            name = _ref_filename(char)
            local_path = os.path.join(ref_dir, name)
            with open(local_path, "wb") as fh:
                fh.write(data)
        except OSError as exc:
            return self._degrade(f"cannot persist ref flac: {exc}")

        # Make available to ComfyUI for voice_clone (shared volume or docker cp).
        # Non-fatal: a failure here means clone_voice will likely miss the ref,
        # but we still return the local path for record-keeping.
        if not self._publish_ref_to_comfyui(local_path, name):
            logger.warning(
                "tts_engine: ref for %s may be unavailable to ComfyUI "
                "(publish failed) — voice_clone may degrade.", char,
            )

        return {
            "ref_audio": name,
            "ref_local": local_path,
            "generation_time_ms": int((time.monotonic() - start) * 1000),
            "engine": "Qwen3-TTS-1.7B",
        }

    # ------------------------------------------------------------------
    # Phase 2 — VoiceClone (per-line clone + flac→wav + mute gate)
    # ------------------------------------------------------------------

    def clone_voice(
        self,
        *,
        text: str,
        ref_audio: str,
        ref_text: str,
        seed: int,
        out_wav: str,
    ) -> dict[str, Any]:
        """Phase 2: clone one dialogue line + convert + mute hard gate.

        POSTs ``{mode:"voice_clone", text, ref_audio, ref_text, seed}``,
        downloads the result, converts FLAC→WAV (24 kHz mono), and runs
        ``volumedetect``. A WAV whose ``mean_volume <= -80 dB`` is SILENT →
        degrade envelope (the in-process mute-WAV ban).

        Args:
            text: The dialogue/narration line to synthesize.
            ref_audio: ComfyUI input filename from ``design_voice``.
            ref_text: The reference line (matches the design ref_audio).
            seed: Fixed per-character seed.
            out_wav: Absolute output WAV path.

        Returns:
            Success envelope ``{"audio_path": out_wav, "mean_volume": float,
            "generation_time_ms": int, "engine": "Qwen3-TTS-1.7B"}`` or a
            degrade envelope ``{"degraded": True, ...}``.
        """
        if not out_wav:
            return self._degrade("missing out_wav output path")
        if not self._ffmpeg_available():
            return self._degrade("ffmpeg binary not found in PATH")

        body = {
            "mode": "voice_clone",
            "text": text,
            "ref_audio": ref_audio,
            "ref_text": ref_text,
            "seed": seed,
        }
        start = time.monotonic()
        result = self._post_async(body)
        if isinstance(result, dict) and result.get("degraded"):
            return result

        if isinstance(result, dict) and "data" in result and isinstance(result["data"], dict):
            result = result["data"]
        audio_url = result.get("audio_url") if isinstance(result, dict) else None
        if not audio_url:
            return self._degrade("missing audio_url in voice_clone response")

        data = self._download(audio_url)
        if not data:
            return self._degrade(f"audio download failed for {audio_url}")

        # Persist the downloaded FLAC next to the target WAV, then convert.
        flac_path = out_wav + ".flac"
        try:
            os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
            with open(flac_path, "wb") as fh:
                fh.write(data)
        except OSError as exc:
            return self._degrade(f"cannot persist clone flac: {exc}")

        # FLAC -> WAV (24 kHz mono PCM). Verbatim from the retired goal:
        #   ffmpeg -y -i <in>.flac -ar 24000 -ac 1 <out>.wav
        convert_argv = [
            "ffmpeg", "-y", "-i", flac_path,
            "-ar", str(TTS_SAMPLE_RATE), "-ac", "1", out_wav,
        ]
        try:
            conv = self._run_subprocess(convert_argv, timeout=120)
        except RuntimeError as exc:
            return self._degrade(f"ffmpeg flac→wav failed: {exc}")
        if getattr(conv, "returncode", 0) != 0:
            stderr = _stderr_text(conv)
            return self._degrade(f"ffmpeg flac→wav exited {conv.returncode}: {stderr[:200]}")

        # Mute hard gate: volumedetect -> mean_volume.
        mean = self._volumedetect(out_wav)
        if mean is None:
            # Probe failed — cannot prove non-silence. Fail-closed: degrade so
            # a potentially-mute clip never flows to P11/P12 silently.
            return self._degrade("volumedetect unreadable — cannot verify non-silence")
        if mean <= SILENT_MEAN_VOLUME_DB:
            return self._degrade(
                f"silent clip: mean_volume={mean:.1f}dB <= {SILENT_MEAN_VOLUME_DB}dB "
                f"(mute-WAV ban)"
            )

        return {
            "audio_path": out_wav,
            "mean_volume": mean,
            "generation_time_ms": int((time.monotonic() - start) * 1000),
            "engine": "Qwen3-TTS-1.7B",
        }

    def _volumedetect(self, wav_path: str) -> float | None:
        """Run ``ffmpeg -i wav -af volumedetect -f null /dev/null`` and parse
        ``mean_volume`` from stderr. Returns None if unreadable.

        ``volumedetect`` exits 0 and prints its analysis to stderr, e.g.::

            [Parsed_volumedetect_0 @ 0x...] mean_volume: -23.4 dB
        """
        argv = [
            "ffmpeg", "-i", wav_path, "-af", "volumedetect",
            "-f", "null", os.devnull,
        ]
        try:
            result = self._run_subprocess(argv, timeout=60)
        except RuntimeError as exc:
            logger.warning("tts_engine volumedetect failed: %s", exc)
            return None
        stderr = _stderr_text(result)
        match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", stderr)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Lifecycle (mirrors LTXVideoEngine)
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "TTSEngine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class IndexTTS25Engine:
    """IndexTTS 2.5 voice engine adapter via the KAP API (v15.3, 2026-08-16).

    Same surface as ``TTSEngine`` (``design_voice`` + ``clone_voice``) but the
    chain runs VoiceDesign → IndexTTS 2.5 **through the KAP HTTP API** — Kai's
    2026-08-16 decision: this is the DEFAULT (and only) creative-audio chain;
    ``qwen_tts`` becomes an explicit-legacy option. Routed via KAP so the GPU
    serial queue (``withGpuQueue`` on the KAP side) arbitrates VRAM against
    H3/music3/qwen_eye — the engine no longer bypasses it by hitting the
    container IP directly.

    KAP topology (single base URL ``KAIS_TTS_BASE_URL``, default
    ``http://localhost:10588``):
    - **design**: ``POST /api/production/indextts2/voice-design/voice-design``
      JSON ``{character_name, instruct, text, lang, language, emotion_mode,
      duration_factor, seed}``. KAP synthesizes the ref internally and returns
      a JSON envelope ``{code:200, data:{synthesis:{audio_path, audio_url},
      ...}}``.
    - **clone**: ``POST /api/production/indextts2/speak/speak`` multipart
      ``{text, lang, duration_factor, ref_audio(file), emo_text, emo_alpha,
      version:"2.5"}`` → JSON envelope ``{data:{audio_path, audio_url}}``
      (KAP writes the wav to its oss dir; the engine downloads ``audio_url``).
      Double ``/speak``: KAP mounts the router AT ``.../indextts2/speak`` and
      the route is ``router.post("/speak")`` — same shape as voice-design.

    v15.4 ENGINE SWAP (2026-09-04, feat/tts-breeze): the synthesis backend
    behind BOTH endpoints is now **Breeze TTS 2** (BreezeBlue, 24 kHz,
    bilingual zh/en, inline acoustic events like ``[笑]``). KAP keeps the
    legacy indextts2 URLs + request/response envelopes as an internal compat
    layer and translates: ``emo_text`` → Breeze natural-language emotion
    ``instruction`` (cfg_scale=4.0 — the 2026-09-03 blind-test-winning
    recipe); ``duration_factor`` accepted then IGNORED (Breeze has no speed
    factor — duration calibration flows through instruction text / the P10
    post-synthesis callbacks, which fall through to text-shortening when a
    speed-up resynth does not shrink the clip). ``ENGINE_NAME`` is retained
    as the CHAIN label — the p10 batch-mode detector and the indextts25 ref
    fallback both key on it, and the route key ``indextts25`` stays the
    ``tts_engine`` enum value; the actual model behind it is Breeze.
    License: Breeze code Apache-2.0; weights NON-COMMERCIAL (self-hosted
    output limited to research / non-commercial use — Kai approved the
    swap 2026-09-03).

    Direct-branch opt-in (default OFF): ``breeze_engine=True`` (ctor kwarg)
    or env ``KAIS_TTS_BREEZE_ENGINE=1`` routes ``clone_voice`` to the Breeze
    native proxy ``POST /api/production/breezeTts/speak`` (same KAP host;
    form carries ``instruction`` instead of ``emo_text``, no ``version``
    field, ``cfg_scale=4.0`` + ``seed`` forwarded). ``design_voice`` has no
    direct branch — it always goes through the voice-design endpoint, whose
    backend is Breeze either way.

    ⚠ ref_text is REQUIRED by the Breeze clone template (2026-09-04 smoke:
    empty ref_text → ``ValueError: missing template fields: ['ref_text']``
    → 500) despite the API advertising it optional. ``clone_voice`` therefore
    forwards ``ref_text`` on BOTH paths — additive on the compat endpoint
    (KAP ignores unknown form fields until its Breeze proxy forwards them),
    load-bearing on the direct branch. An empty ``ref_text`` degrades loudly
    at the backend (D-09) — callers (p10 clips) carry the character's
    reference line.

    ``design_voice`` strategies (unchanged semantics):
    - **Strategy A (primary)**: KAP voice-design endpoint synthesizes the ref
      wav; the engine downloads ``data.synthesis.audio_url`` and persists it.
    - **Strategy B (reuse)**: if a ref wav for this character already exists
      on disk (voice_bank / prior run), reuse it — skip the design call.

    Design invariants (mirror ``TTSEngine``):
    - D-04: ``transport`` + ``subprocess_runner`` ctor kwargs for hermetic
      testing.
    - D-06: config read at construction time.
    - D-09: degrade-first contract — ConnectError / timeout / 5xx / 429 →
      degrade envelope; 4xx + invalid-JSON 2xx raise ``TTSEngineError``.
    - The MUTE HARD GATE (``volumedetect`` mean_volume <= -80 dB) still
      applies to ``clone_voice``. KAP returns wavs via ``audio_url`` download
      — no flac→wav conversion needed, but a near-silent clip still degrades.
    - Synchronous wait (no async two-phase): the KAP speak proxy is a direct
      pass-through to the :5110 server (~3-5s/line). The 600s timeout covers
      GPU-queue contention; the KAP GPU queue itself waits up to 30min
      internally and only surfaces vram_insufficient after that.
    """

    DEFAULT_KAP_BASE_URL = "http://localhost:10588"
    # 600s: KAP proxy is a synchronous pass-through (IndexTTS2.5 was ~3-5s/
    # line; the Breeze backend since 2026-09-04 is ~8s/line for a 3s line —
    # 600s still has huge headroom), but the KAP GPU queue may hold the lock
    # for an in-flight H3 render before our turn. Generous but bounded —
    # NOT 7200 (that budget exists for the ComfyUI-poll engines; here a hang
    # means the KAP TTS proxy chain is stuck).
    DEFAULT_TIMEOUT = 600.0
    ENGINE_NAME = "IndexTTS-2.5"

    def __init__(
        self,
        *,
        kap_base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
        subprocess_runner: Callable[[list[str]], Any] | None = None,
        breeze_engine: bool = False,
    ) -> None:
        """Construct the engine.

        Parameters (D-06 env-var config at construction time, never import):

        - ``kap_base_url`` / ``KAIS_TTS_BASE_URL``: KAP base URL (default
          ``http://localhost:10588``).
        - ``timeout``: per-request timeout in seconds (default 600).
        - ``transport``: hermetic test injection via ``httpx.MockTransport``.
        - ``subprocess_runner``: test seam for FFmpeg (volumedetect).
        - ``breeze_engine``: opt-in direct branch (v15.4) — POST clone to the
          Breeze native proxy ``/api/production/breezeTts/speak`` instead of
          the indextts2 compat endpoint. Default OFF (the compat endpoint IS
          Breeze behind KAP since 2026-09-04; this branch only skips the
          translation hop). Env ``KAIS_TTS_BREEZE_ENGINE`` (``1/true/yes/on``)
          opts in when the kwarg is left at ``False``.
        """
        # Back-compat: 旧环境变量 INDEXTTS25_SERVER_URL / VOICEDESIGN_SERVER_URL
        # 曾指向容器 IP :5110/:5111 — 语义改为「KAP base」(容器重启 IP 会漂移,
        # 且直连绕过 KAP GPU 队列)。旧名若仍是端口直连形态则忽略, 取 KAP 默认。
        legacy = os.environ.get("INDEXTTS25_SERVER_URL") or os.environ.get(
            "VOICEDESIGN_SERVER_URL"
        )
        if legacy and ":5110" not in legacy and ":5111" not in legacy:
            legacy = legacy.rstrip("/")
        else:
            legacy = None
        self._kap_base = (
            kap_base_url
            or os.environ.get("KAIS_TTS_BASE_URL")
            or legacy
            or self.DEFAULT_KAP_BASE_URL
        ).rstrip("/")
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self._client = httpx.Client(timeout=self._timeout, transport=transport)
        self._runner = subprocess_runner
        if breeze_engine:
            self._breeze_engine = True
        else:
            self._breeze_engine = str(
                os.environ.get("KAIS_TTS_BREEZE_ENGINE", "")
            ).strip().lower() in ("1", "true", "yes", "on")
        # Back-compat: 旧环境变量 INDEXTTS25_SERVER_URL / VOICEDESIGN_SERVER_URL
        # 曾指向容器 IP :5110/:5111 — 语义改为「KAP base」(容器重启 IP 会漂移,
        # 且直连绕过 KAP GPU 队列)。旧名若仍是端口直连形态则忽略, 取 KAP 默认。
        legacy = os.environ.get("INDEXTTS25_SERVER_URL") or os.environ.get(
            "VOICEDESIGN_SERVER_URL"
        )
        if legacy and ":5110" not in legacy and ":5111" not in legacy:
            legacy = legacy.rstrip("/")
        else:
            legacy = None
        self._kap_base = (
            kap_base_url
            or os.environ.get("KAIS_TTS_BASE_URL")
            or legacy
            or self.DEFAULT_KAP_BASE_URL
        ).rstrip("/")
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self._client = httpx.Client(timeout=self._timeout, transport=transport)
        self._runner = subprocess_runner

    # ------------------------------------------------------------------
    # D-09 degrade / raise helpers (mirror TTSEngine)
    # ------------------------------------------------------------------

    def _degrade(self, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope and log a warning (D-09).

        Carries the ``kind`` classification (engine_unavailable vs quality)
        mirroring ``TTSEngine._degrade``.
        """
        logger.warning("indextts25_engine degraded: %s", reason)
        return {
            "degraded": True,
            "engine": self.ENGINE_NAME,
            "reason": reason,
            "kind": _degrade_kind(reason),
        }

    def _post_voicedesign(self, body: dict) -> Any:
        """POST JSON to KAP ``/voice-design/voice-design`` (D-09 contract).

        KAP synthesizes the design ref internally (Breeze TTS 2 since
        2026-09-04; previously the VoiceDesign :5111 → IndexTTS 2.5 :5110
        chain) and returns a JSON envelope
        ``{code, data:{synthesis:{audio_url,...}}}``.
        2xx -> parsed JSON dict. Network / 5xx / 429 -> degrade envelope.
        4xx / invalid-JSON 2xx -> raise ``TTSEngineError``.
        """
        url = f"{self._kap_base}/api/production/indextts2/voice-design/voice-design"
        try:
            response = self._client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=body,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            return self._degrade(f"{type(exc).__name__}: {exc}")
        except httpx.HTTPError as exc:
            return self._degrade(f"{type(exc).__name__}: {exc}")

        status = response.status_code
        text = response.text
        if status >= 500 or status == 429:
            # Keep the error body (first 200 chars) — mirrors TTSEngine._post.
            return self._degrade(f"VoiceDesign HTTP {status}: {text[:200]}")
        if status >= 400:
            raise TTSEngineError(f"VoiceDesign HTTP {status}: {text[:200]}")
        try:
            return response.json()
        except Exception:
            raise TTSEngineError(f"VoiceDesign invalid JSON: {text[:200]}")

    def _post_speak(
        self,
        *,
        text: str,
        ref_path: str,
        lang: str,
        duration_factor: float,
        emotion_text: str | None,
        seed: int | None = None,
        ref_text: str = "",
    ) -> bytes | dict[str, Any]:
        """POST multipart to the KAP clone endpoint (D-09).

        Default (compat) path: ``/api/production/indextts2/speak/speak`` with
        ``version="2.5"`` — KAP translates ``emo_text`` → Breeze emotion
        ``instruction`` (cfg_scale=4.0) and ignores ``duration_factor``.
        Direct branch (``_breeze_engine``): ``/api/production/breezeTts/speak``
        — Breeze-native form (``instruction`` instead of ``emo_text``, no
        ``version``, ``cfg_scale=4.0`` + ``seed`` forwarded so per-character
        seeds stay reproducible).

        ``ref_text`` is forwarded on BOTH paths: the Breeze clone template
        requires it (empty → 500 at the backend), and the compat endpoint
        ignores the extra field until KAP's Breeze proxy forwards it.

        Both endpoints write the wav to the KAP oss dir and return the same
        JSON envelope ``{code, data:{audio_url, audio_path}}``. This helper
        returns the DOWNLOADED wav bytes (via ``audio_url``), or a degrade
        envelope on network / 5xx / 429 / download failure. 4xx / invalid-JSON
        2xx raise ``TTSEngineError``.
        """
        if self._breeze_engine:
            url = f"{self._kap_base}/api/production/breezeTts/speak"
            form = {
                "text": text,
                "lang": lang,
                # Breeze accepts duration_factor but IGNORES it (no speed
                # factor) — sent for form parity with the compat endpoint.
                "duration_factor": str(duration_factor),
                "cfg_scale": "4.0",
                "ref_text": ref_text or "",
            }
            if emotion_text:
                form["instruction"] = emotion_text
            if seed is not None:
                form["seed"] = str(int(seed))
        else:
            url = f"{self._kap_base}/api/production/indextts2/speak/speak"
            form = {
                "text": text,
                "lang": lang,
                "duration_factor": str(duration_factor),
                "version": "2.5",
                # Additive (2026-09-04): Breeze clone template requires a
                # non-empty ref_text — forward it so KAP's Breeze proxy can
                # use it. The IndexTTS 2.5 server ignored it (zero-shot).
                "ref_text": ref_text or "",
            }
            if emotion_text:
                form["emo_text"] = emotion_text
        try:
            with open(ref_path, "rb") as fh:
                files = {"ref_audio": (os.path.basename(ref_path), fh, "audio/wav")}
                response = self._client.post(url, data=form, files=files)
        except OSError as exc:
            return self._degrade(f"cannot read ref_audio {ref_path}: {exc}")
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            return self._degrade(f"{type(exc).__name__}: {exc}")
        except httpx.HTTPError as exc:
            return self._degrade(f"{type(exc).__name__}: {exc}")

        status = response.status_code
        if status >= 500 or status == 429:
            return self._degrade(f"HTTP {status}: {response.text[:200]}")
        if status >= 400:
            raise TTSEngineError(f"HTTP {status}: {response.text[:200]}")
        # KAP returns a JSON envelope (v1/tts style) — unpack data.audio_url.
        try:
            payload = response.json()
        except Exception:
            raise TTSEngineError(
                f"Invalid JSON response: {response.text[:200]}"
            )
        data = payload.get("data") if isinstance(payload, dict) else None
        audio_url = data.get("audio_url") if isinstance(data, dict) else None
        if not audio_url:
            return self._degrade(
                f"missing audio_url in KAP speak response: {str(payload)[:200]}"
            )
        return self._download(audio_url)

    def _download(self, url: str) -> bytes | None:
        """Download ``url`` (a KAP-relative ``audio_url``) → raw bytes (D-09).

        Mirrors ``TTSEngine._download``: relative URLs resolve against the KAP
        base. Network / 4xx+ → None (caller converts to a degrade envelope).
        """
        if not url:
            return None
        full = url if url.startswith(("http://", "https://")) else f"{self._kap_base}/{url.lstrip('/')}"
        try:
            resp = self._client.get(full)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
            logger.warning("indextts25_engine download failed (%s): %s", type(exc).__name__, exc)
            return None
        if resp.status_code >= 400:
            logger.warning("indextts25_engine download HTTP %s for %s", resp.status_code, full)
            return None
        return resp.content

    # ------------------------------------------------------------------
    # subprocess seam (FFmpeg volumedetect) — mirror TTSEngine
    # ------------------------------------------------------------------

    def _run_subprocess(self, argv: list[str], *, timeout: int = 120) -> Any:
        runner = self._runner
        try:
            if runner is not None:
                return runner(argv)
            return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError as exc:
            raise RuntimeError(f"binary not found for {argv[0]!r}: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{argv[0]!r} timed out ({timeout}s)") from exc

    def _ffmpeg_available(self) -> bool:
        if self._runner is not None:
            return True
        return shutil.which("ffmpeg") is not None

    # ------------------------------------------------------------------
    # Phase 1 — design_voice (VoiceDesign-server ref, or reuse)
    # ------------------------------------------------------------------

    def design_voice(
        self,
        *,
        char: str,
        ref_line: str,
        instruct: str,
        seed: int,
        ref_dir: str | None = None,
    ) -> dict[str, Any]:
        """Phase 1: obtain ONE reference wav for a character.

        The ref audio is synthesized via the KAP voice-design endpoint
        (Strategy A — backend is Breeze TTS 2 since 2026-09-04; the GPU step
        is arbitrated by the KAP GPU queue) or reused from an
        existing ref (Strategy B). The returned ``ref_audio`` is a HOST path
        (not a ComfyUI filename) — ``clone_voice`` reads + uploads it.

        Args:
            char: Character identifier (used for the ref filename).
            ref_line: Short reference line spoken in the design voice.
            instruct: Voice description (forwarded to KAP → VoiceDesign).
                Empty/whitespace → filled with a deterministic per-character
                default BEFORE the POST (KAP hard-400s an empty instruct):
                narrator-style names get a fixed narration voice, others a
                fixed neutral voice. Non-empty values are forwarded as-is.
            seed: Per-character seed (forwarded to VoiceDesign /generate;
                kept fixed per character for reproducible voice identity).
            ref_dir: Directory to write the local ref wav.

        Returns:
            Success envelope ``{"ref_audio": <host path>, "ref_local":
            <host path>, "generation_time_ms": int, "engine": "IndexTTS-2.5"}``
            or a degrade envelope ``{"degraded": True, ...}``.
        """
        ref_dir = ref_dir or _default_ref_dir()
        try:
            os.makedirs(ref_dir, exist_ok=True)
        except OSError as exc:
            return self._degrade(f"cannot create ref_dir {ref_dir}: {exc}")

        name = _indextts_ref_filename(char)
        local_path = os.path.join(ref_dir, name)

        # Strategy B: reuse an existing ref wav (voice_bank / prior run). This
        # also covers the resume case where design already ran.
        if os.path.isfile(local_path):
            logger.info(
                "indextts25_engine: reusing existing ref for %r at %s", char, local_path,
            )
            return {
                "ref_audio": local_path,
                "ref_local": local_path,
                "generation_time_ms": 0,
                "engine": self.ENGINE_NAME,
            }

        # Strategy A: synthesize a ref via the KAP voice-design endpoint
        # (backend is Breeze zero-ref design since 2026-09-04; KAP keeps the
        # legacy URL + envelope and returns {data:{synthesis:{audio_url}}}).
        # We download that wav and persist it as the character's ref — the
        # SAME ref the clone below uploads, so the voice identity is the
        # designed one.
        start = time.monotonic()
        # FIX (2026-10-13): KAP 400s an empty instruct → design degrade → the
        # whole clone batch loses its ref (ep-mv-guangdexiaoxi narrator loop).
        # Narrator has no voice-design line by nature, so empty is a NORMAL
        # input form, not a caller bug — fill a deterministic default instead.
        if not instruct.strip():
            instruct = _default_instruct_for(char)
            logger.info(
                "indextts25_engine: empty instruct for %r — defaulted to %r",
                char, instruct,
            )
        vd_result = self._post_voicedesign({
            "character_name": char,
            "instruct": instruct,
            "text": ref_line or "你好，这是我的声音。",
            "lang": "ZH",
            "language": "Chinese",
            "emotion_mode": "none",
            "seed": seed,
        })
        if isinstance(vd_result, dict) and vd_result.get("degraded"):
            return vd_result

        data = vd_result.get("data") if isinstance(vd_result, dict) else None
        synthesis = data.get("synthesis") if isinstance(data, dict) else None
        audio_url = synthesis.get("audio_url") if isinstance(synthesis, dict) else None
        if not audio_url:
            return self._degrade(
                "missing audio_url in KAP voice-design response: "
                f"{str(vd_result)[:200]}"
            )
        raw = self._download(audio_url)
        if not raw:
            return self._degrade(f"audio download failed for {audio_url}")
        try:
            with open(local_path, "wb") as fh:
                fh.write(raw)
        except OSError as exc:
            return self._degrade(f"cannot persist ref wav: {exc}")

        return {
            "ref_audio": local_path,
            "ref_local": local_path,
            "generation_time_ms": int((time.monotonic() - start) * 1000),
            "engine": self.ENGINE_NAME,
        }

    # ------------------------------------------------------------------
    # Phase 2 — clone_voice (multipart /speak + mute hard gate)
    # ------------------------------------------------------------------

    def clone_voice(
        self,
        *,
        text: str,
        ref_audio: str,
        ref_text: str,
        seed: int,
        out_wav: str,
        emotion_text: str | None = None,
        duration_factor: float = 1.0,
        lang: str = "ZH",
    ) -> dict[str, Any]:
        """Phase 2: clone one line via KAP (Breeze backend) + mute hard gate.

        POSTs multipart to KAP ``/api/production/indextts2/speak/speak`` with
        ``version="2.5"`` (``text`` + ``ref_audio`` file upload). The backend
        behind this endpoint is Breeze TTS 2 since 2026-09-04 (KAP compat
        layer maps ``emo_text`` → Breeze emotion ``instruction``;
        ``duration_factor`` is accepted then ignored — Breeze has no speed
        factor, so a speed-up calibration resynth comes back at ~the same
        duration and the P10 budget loop falls through to text-shortening).
        KAP writes the wav and returns ``{data:{audio_url}}``; the engine
        downloads it to ``out_wav`` (no flac→wav conversion), then
        ``volumedetect`` enforces the MUTE HARD GATE. With
        ``breeze_engine=True`` the multipart goes straight to
        ``/api/production/breezeTts/speak`` instead (``instruction`` +
        ``cfg_scale`` + ``seed``, no ``version``).

        ``ref_text`` is now FORWARDED (not ignored): the Breeze clone
        template requires it (empty → 500), whereas IndexTTS 2.5 was
        zero-shot. p10 clips carry the character's reference line.

        Args:
            text: The dialogue/narration line to synthesize.
            ref_audio: HOST path to the reference wav (from ``design_voice``
                or voice_bank). NOT a ComfyUI filename.
            ref_text: Transcript of the reference audio — REQUIRED non-empty
                by the Breeze clone template (forwarded on both paths; an
                empty value degrades loudly at the backend).
            seed: Per-character seed — forwarded ONLY on the direct breeze
                branch (Breeze accepts ``seed``; the compat endpoint ignores
                it). Reproducible voice there.
            out_wav: Absolute output WAV path.
            emotion_text: Optional emotion description (maps to ``emo_text``
                on the compat endpoint / ``instruction`` on the direct branch)
                — the P10 ``emotion_hint`` field lands here.
            duration_factor: Speed factor 0.5–2.0 (default 1.0). Accepted for
                signature compat; the Breeze backend ignores it.
            lang: Language (default ``"ZH"``).

        Returns:
            Success envelope ``{"audio_path": out_wav, "mean_volume": float,
            "generation_time_ms": int, "engine": "IndexTTS-2.5"}`` (the
            ``engine`` value is the chain label — see ``ENGINE_NAME``) or a
            degrade envelope ``{"degraded": True, ...}``.
        """
        if not out_wav:
            return self._degrade("missing out_wav output path")
        if not self._ffmpeg_available():
            return self._degrade("ffmpeg binary not found in PATH")
        if not ref_audio:
            return self._degrade("missing ref_audio (reference wav path)")
        if not os.path.isfile(ref_audio):
            return self._degrade(f"ref_audio not found: {ref_audio}")

        start = time.monotonic()
        data = self._post_speak(
            text=text,
            ref_path=ref_audio,
            lang=lang,
            duration_factor=duration_factor,
            emotion_text=emotion_text,
            seed=seed,
            ref_text=ref_text,
        )
        # A degrade envelope is a dict; raw audio is bytes.
        if isinstance(data, dict):
            return data
        if not data:
            return self._degrade("empty audio response from /speak")

        try:
            os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
            with open(out_wav, "wb") as fh:
                fh.write(data)
        except OSError as exc:
            return self._degrade(f"cannot persist clone wav: {exc}")

        # IndexTTS 2.5 returns wav directly — no flac→wav conversion. But the
        # MUTE HARD GATE (mean_volume <= -80 dB) still applies.
        mean = self._volumedetect(out_wav)
        if mean is None:
            return self._degrade("volumedetect unreadable — cannot verify non-silence")
        if mean <= SILENT_MEAN_VOLUME_DB:
            return self._degrade(
                f"silent clip: mean_volume={mean:.1f}dB <= {SILENT_MEAN_VOLUME_DB}dB "
                f"(mute-WAV ban)"
            )

        return {
            "audio_path": out_wav,
            "mean_volume": mean,
            "generation_time_ms": int((time.monotonic() - start) * 1000),
            "engine": self.ENGINE_NAME,
        }

    def _volumedetect(self, wav_path: str) -> float | None:
        """Run ``ffmpeg -i wav -af volumedetect -f null /dev/null`` and parse
        ``mean_volume`` from stderr (mirror ``TTSEngine._volumedetect``).
        """
        argv = [
            "ffmpeg", "-i", wav_path, "-af", "volumedetect",
            "-f", "null", os.devnull,
        ]
        try:
            result = self._run_subprocess(argv, timeout=60)
        except RuntimeError as exc:
            logger.warning("indextts25_engine volumedetect failed: %s", exc)
            return None
        stderr = _stderr_text(result)
        match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", stderr)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Lifecycle (mirror TTSEngine)
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "IndexTTS25Engine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _ref_filename(char: str) -> str:
    """Stable ComfyUI ref filename for a character (sanitized).

    e.g. "阿毛" -> "ref_阿毛.flac". Non-path-safe characters are replaced so the
    name is usable both as a docker cp destination and a ComfyUI input key.
    """
    safe = re.sub(r"[^A-Za-z0-9_一-鿿-]", "_", str(char)) or "char"
    return f"ref_{safe}.flac"


def _indextts_ref_filename(char: str) -> str:
    """Stable host-side ref WAV filename for a character (IndexTTS 2.5).

    Same sanitization as ``_ref_filename`` but ``.wav`` (IndexTTS 2.5 clones
    from a wav host path, not a ComfyUI ``.flac`` input key) — e.g.
    "阿毛" -> "ref_阿毛.wav".
    """
    safe = re.sub(r"[^A-Za-z0-9_一-鿿-]", "_", str(char)) or "char"
    return f"ref_{safe}.wav"


def _default_ref_dir() -> str:
    """Default ref output dir (temp) when the caller passes no ``ref_dir``."""
    import tempfile
    return os.path.join(tempfile.gettempdir(), "kais_tts_refs")


def _stderr_text(result: Any) -> str:
    """Best-effort decode of a CompletedProcess-like ``.stderr``."""
    stderr = getattr(result, "stderr", "") or ""
    if isinstance(stderr, bytes):
        try:
            return stderr.decode("utf-8", "replace")
        except Exception:
            return repr(stderr)
    return str(stderr)


def select_tts_engine(env: str | None = None) -> TTSEngine | IndexTTS25Engine:
    """Factory returning a TTS engine (mirrors ``preview_engine.select_engine``).

    Resolution order (D-06: read at call time, not import time):
    1. Explicit ``env`` kwarg (tests + programmatic callers).
    2. ``os.environ.get("KAIS_TTS_ENGINE")`` (call-time read).
    3. Default ``"indextts25"`` (v15.3, 2026-08-16 Kai decision — the
       VoiceDesign→IndexTTS 2.5 chain via KAP is the sole creative-audio
       link; ``qwen_tts`` is LEGACY, selectable explicitly for old-project
       resume).

    v15.1 removed the multi-engine division (ltx_native). v15.2 (2026-08-13)
    added ``indextts25`` as an optional engine; v15.3 (2026-08-16) makes it
    the DEFAULT and reroutes it through the KAP API (GPU queue arbitration).
    v15.4 (2026-09-04) swaps the backend behind ``indextts25`` to Breeze TTS 2
    via the KAP compat layer — the route key and this factory are unchanged.
    ``cosyvoice`` / ``indextts2_fallback`` are deprecated aliases that still
    route to Qwen3-TTS (legacy). Unknown values fall back to the DEFAULT
    (``IndexTTS25Engine``) AND emit a WARN log (T-40-09 mitigation — no eval,
    no dynamic lookup; predictable fallback).
    """
    value = env if env is not None else os.environ.get("KAIS_TTS_ENGINE", "indextts25")
    if value == "indextts25":
        return IndexTTS25Engine()
    elif value in ("qwen_tts", "cosyvoice", "indextts2_fallback"):
        comfyui_input = os.environ.get("KAIS_COMFYUI_INPUT_DIR") or None
        return TTSEngine(comfyui_input_dir=comfyui_input)
    else:
        logger.warning(
            "unknown KAIS_TTS_ENGINE=%r, falling back to default indextts25", value,
        )
        return IndexTTS25Engine()
