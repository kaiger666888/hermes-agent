"""preview_engine.py - PreviewEngine strategy pattern (Plan 40-02).

The Phase 40 rapid-preview tier produces 3 low-quality variants per shot by
varying exactly ONE structure parameter from baseline (Notion 红线 #6 — control
variable). The actual rendering can happen via one of two engines:

- ``SlideshowEngine``: assembles a keyframe image + TTS voice clip into an
  MP4 via the FFmpeg subprocess. Native, no external API dependency.
  (Implemented in Plan 40-02 Task 2.)
- ``LTXVideoEngine``: POSTs to a (mocked in v6.0) LTX-Video GPU service at
  ``:9001/api/v1/ltx`` and returns the produced clip path. Mirrors the
  ``GoldTeamClient`` D-09 degrade-first contract.
  (Implemented in Plan 40-02 Task 3.)

This module is pure library code — the p10b phase module (Plan 40-03) composes
these engines into the rapid-preview fan-out. NO phase integration here.

Design invariants (per CONTEXT.md Phase 40 decisions):
- D-04: ``transport`` constructor kwarg on ``LTXVideoEngine`` lets tests inject
  ``httpx.MockTransport`` for hermetic HTTP mocking. ``SlideshowEngine`` accepts
  a ``subprocess_runner`` kwarg for the same purpose.
- D-06: All configuration is read from env vars at construction / call time
  (never at module import).
- D-09: Degrade-first contract. Connection errors / timeouts / 5xx / 429 return
  ``{"degraded": True, ...}``; they never raise to the caller. 4xx raises
  ``PreviewEngineError`` (caller bug).
- Strategy selection: ``select_engine()`` reads ``KAIS_PREVIEW_ENGINE`` at
  call time (not import time). Default is ``"slideshow"`` (safer fallback; no
  external API dep; honors 降级容忍 红线 #1). Unknown values fall back to
  slideshow + WARN log (T-40-09 mitigation: no eval(), no dynamic lookup).

WARNING #7 stub strategy: Task 1 of Plan 40-02 leaves ``SlideshowEngine`` and
``LTXVideoEngine`` as stubs whose ``generate()`` raises ``NotImplementedError``.
A dedicated test (TestPreviewEngineABC.test_stub_subclasses_raise_not_implemented_at_task_1_boundary)
asserts this at the Task 1 -> 2/3 boundary, proving the stub strategy is in
place and Tasks 2/3 will expand them rather than accidentally re-using a no-op.
"""

from __future__ import annotations

import abc
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)


class PreviewEngineError(Exception):
    """Raised for 4xx client errors from LTX-Video (caller bug).

    Mirrors ``GoldTeamError`` semantics: connection errors / timeouts / 5xx /
    429 do NOT raise — they degrade (return ``{"degraded": True, ...}`` envelope
    to the caller). 4xx and invalid-JSON 2xx responses are caller / service
    bugs and raise this exception.
    """


class PreviewEngine(abc.ABC):
    """Abstract base class for the rapid-preview dual-engine strategy.

    Concrete subclasses implement ``generate()`` to produce one preview clip
    variant. Both engines return a uniform envelope:

    - Success: ``{"clip_path": str, "generation_time_ms": int, "engine": str}``
    - Degrade: ``{"degraded": True, "engine": str, "reason": str}``

    ``generation_time_ms`` is LOCALLY-measured wall time via
    ``time.monotonic()`` (INFO #10) — the response body's reported timing is
    IGNORED. Local wall time is always available and comparable across engines;
    service-reported timing may be unreliable, missing, or inconsistent.
    """

    @abc.abstractmethod
    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,
        voice_clip_path: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        """Produce one rapid-preview variant. Subclasses MUST implement.

        Returns a success envelope (``clip_path`` / ``generation_time_ms`` /
        ``engine``) or a degrade envelope (``degraded: True``).
        """
        raise NotImplementedError

    @staticmethod
    def _record_time(start: float) -> int:
        """Return wall-clock ms since ``start`` (monotonic delta, INFO #10)."""
        return int((time.monotonic() - start) * 1000)

    # ------------------------------------------------------------------
    # Lifecycle (Phase 40 CR-02 fix — context-manager protocol on the ABC)
    # ------------------------------------------------------------------
    # The ABC provides no-op defaults so callers can unconditionally use
    # ``with select_engine() as engine:`` regardless of which concrete
    # engine is selected. ``LTXVideoEngine`` overrides these to close its
    # ``httpx.Client`` connection pool; ``SlideshowEngine`` inherits the
    # no-ops (no resources to clean up — each ``subprocess.run`` spawns its
    # own process).
    #
    # Before this change, ``LTXVideoEngine`` defined ``close`` /
    # ``__enter__`` / ``__exit__`` but p10b's ``_run_body`` never entered
    # the context manager — leaking one ``httpx.Client`` connection pool
    # per episode in long-running daemons (gateway / cron).

    def close(self) -> None:
        """Release engine-held resources. No-op default; subclasses override."""
        # SlideshowEngine has no resources to release. LTXVideoEngine
        # overrides this to close its ``httpx.Client``.
        return

    def __enter__(self) -> "PreviewEngine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def select_engine(env: str | None = None) -> PreviewEngine:
    """Factory returning a concrete engine based on env-var dispatch.

    Resolution order (D-06: read at call time, not import time):
    1. Explicit ``env`` kwarg (tests + programmatic callers).
    2. ``os.environ.get("KAIS_PREVIEW_ENGINE")`` (call-time read).
    3. Default ``"slideshow"`` (safer fallback; no external API dep).

    Unknown values fall back to ``SlideshowEngine`` AND emit a WARN log
    mentioning the unknown value (T-40-09 mitigation — no eval(), no
    dynamic class lookup; predictable fallback).
    """
    value = env if env is not None else os.environ.get("KAIS_PREVIEW_ENGINE", "slideshow")
    if value == "ltx":
        return LTXVideoEngine()
    if value == "slideshow":
        return SlideshowEngine()
    logger.warning(
        "unknown KAIS_PREVIEW_ENGINE=%r, falling back to slideshow",
        value,
    )
    return SlideshowEngine()


# ----------------------------------------------------------------------
# Stub subclasses (Task 1 WARNING #7 boundary — expanded by Tasks 2 / 3).
#
# At this point both engines raise NotImplementedError on generate(). Task 2
# expands SlideshowEngine (FFmpeg subprocess). Task 3 expands LTXVideoEngine
# (httpx POST). The TestPreviewEngineABC.test_stub_subclasses_raise_not_implemented_at_task_1_boundary
# test pins this boundary.
# ----------------------------------------------------------------------


class SlideshowEngine(PreviewEngine):
    """FFmpeg-subprocess engine.

    Assembles one preview variant from a keyframe image + TTS voice clip via
    the FFmpeg subprocess. ``generate()`` builds the argv as a Python list
    (T-40-06: no shell=True; argument injection impossible) and degrades
    gracefully on missing inputs, missing FFmpeg binary, or non-zero exit.

    Generation target: < 10s per variant (per CONTEXT.md specifics).
    """

    def __init__(
        self,
        *,
        subprocess_runner: Callable[[list[str]], "subprocess.CompletedProcess"] | None = None,
    ) -> None:
        """Construct the engine.

        ``subprocess_runner`` exists for hermetic test injection: pass a
        callable returning a ``subprocess.CompletedProcess``-like object
        (with ``.returncode`` and ``.stderr``). ``None`` (default) uses the
        real ``subprocess.run`` and validates the FFmpeg binary via
        ``shutil.which`` first.
        """
        self._subprocess_runner = subprocess_runner

    def _degrade(self, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope and log a warning (D-09)."""
        logger.warning("slideshow_engine degraded: %s", reason)
        return {"degraded": True, "engine": "slideshow", "reason": reason}

    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,
        voice_clip_path: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        """Render one variant via FFmpeg subprocess.

        Validation order (input validation before binary lookup before
        invocation): missing inputs short-circuit to degrade envelopes so
        we never spawn FFmpeg on bad data.
        """
        # Input validation.
        if not keyframe_image_path:
            return self._degrade("missing keyframe_image_path")
        if not voice_clip_path:
            return self._degrade("missing voice_clip_path")
        if not output_path:
            return self._degrade("missing output_path")

        # Binary lookup (only when using the real subprocess).
        runner = self._subprocess_runner
        if runner is None:
            if shutil.which("ffmpeg") is None:
                return self._degrade("ffmpeg binary not found in PATH")
            runner = subprocess.run  # type: ignore[assignment]

        # T-40-06: argv as Python list — no shell=True, no string concat.
        argv = [
            "ffmpeg", "-y", "-loop", "1",
            "-i", keyframe_image_path,
            "-i", voice_clip_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        start = time.monotonic()
        try:
            result = runner(argv)
        except OSError as exc:
            # Unexpected OS-level error (permission denied, etc.) — degrade.
            return self._degrade(f"{type(exc).__name__}: {exc}")

        elapsed_ms = self._record_time(start)
        returncode = getattr(result, "returncode", 0)
        if returncode != 0:
            stderr = getattr(result, "stderr", b"") or b""
            if isinstance(stderr, bytes):
                try:
                    stderr_text = stderr.decode("utf-8", errors="replace")
                except Exception:
                    stderr_text = repr(stderr)
            else:
                stderr_text = str(stderr)
            return self._degrade(
                f"ffmpeg exited {returncode}: {stderr_text[:200]}"
            )

        return {
            "clip_path": output_path,
            "generation_time_ms": elapsed_ms,
            "engine": "slideshow",
        }


class LTXVideoEngine(PreviewEngine):
    """LTX-Video HTTP engine (mocked in v6.0; real GPU deferred to operator).

    POSTs to ``/api/v1/ltx`` with ``{shot_id, prompt, structure_delta}`` and
    returns the produced clip path. Mirrors ``GoldTeamClient`` structure
    EXACTLY for the D-09 degrade-first contract:

    - ConnectError / TimeoutException / HTTPError -> degrade envelope.
    - status >= 500 or status == 429 -> degrade envelope.
    - status >= 400 -> raise ``PreviewEngineError`` (caller bug).
    - 2xx -> parse JSON; invalid JSON -> raise (service bug).

    INFO #10: ``generation_time_ms`` in the SUCCESS envelope is the
    LOCALLY-measured wall time, NOT the value reported in the response body.
    """

    DEFAULT_BASE_URL = "http://localhost:9001"
    DEFAULT_TIMEOUT = 30.0  # LTX-Video is second-scale; allow generous timeout.

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Construct the engine.

        Parameters mirror ``GoldTeamClient`` (D-06 env-var configuration at
        construction time, never at module import):

        - ``base_url`` / ``KAIS_LTX_URL``: LTX-Video service base URL.
        - ``timeout``: per-request timeout in seconds.
        - ``transport``: hermetic test injection via ``httpx.MockTransport``.
          ``None`` (default) uses real networking.
        """
        self._base_url = (
            base_url
            or os.environ.get("KAIS_LTX_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        # transport=None -> real network; tests inject httpx.MockTransport.
        self._client = httpx.Client(timeout=self._timeout, transport=transport)

    def _degrade(self, reason: str) -> dict[str, Any]:
        """Return the uniform degrade envelope and log a warning (D-09).

        Mirrors ``GoldTeamClient._degrade`` shape (with ``engine`` instead
        of ``client`` / ``operation`` since the engine is single-purpose).
        """
        logger.warning("ltx_engine degraded: %s", reason)
        return {"degraded": True, "engine": "ltx", "reason": reason}

    def _request(self, body: dict) -> Any:
        """Central HTTP wrapper enforcing D-09 degrade / raise contract.

        Mirrors ``GoldTeamClient._request`` (lines 170-221 of gold_team.py):
        - ConnectError / TimeoutException / HTTPError -> degrade envelope.
        - status >= 500 or status == 429 -> degrade envelope.
        - status >= 400 -> raise ``PreviewEngineError`` (caller bug).
        - 2xx -> parse JSON; invalid JSON -> raise (service-side bug).
        """
        url = f"{self._base_url}/api/v1/ltx"
        try:
            response = self._client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=body,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            # D-09: degrade on connect / timeout (server-side problem).
            return self._degrade(f"{type(exc).__name__}: {exc}")
        except httpx.HTTPError as exc:
            # Catch-all for other httpx transport errors (also degrade).
            return self._degrade(f"{type(exc).__name__}: {exc}")

        status = response.status_code
        text = response.text

        if status >= 500 or status == 429:
            # D-09: degrade on server errors and rate limiting.
            return self._degrade(f"HTTP {status}")

        if status >= 400:
            # 4xx is a caller bug - raise, do not degrade.
            raise PreviewEngineError(f"HTTP {status}: {text[:200]}")

        # 2xx - parse JSON. Invalid JSON is a service-side bug, so raise.
        try:
            return response.json()
        except Exception:
            raise PreviewEngineError(f"Invalid JSON response: {text[:200]}")

    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,
        voice_clip_path: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        """POST one variant request to LTX-Video and return the envelope.

        INFO #10: ``generation_time_ms`` is LOCALLY-measured wall time; the
        response body's reported timing is IGNORED. Local wall time is
        always available and comparable across engines.
        """
        body = {
            "shot_id": shot_id,
            "prompt": prompt,
            "structure_delta": structure_delta,
        }
        start = time.monotonic()
        result = self._request(body)
        # Pass-through degrade envelope (already shaped by _degrade).
        if isinstance(result, dict) and result.get("degraded"):
            return result
        # Validate response shape: must have clip_path.
        if not isinstance(result, dict) or "clip_path" not in result:
            return self._degrade("missing clip_path in ltx response")
        return {
            "clip_path": result["clip_path"],
            "generation_time_ms": self._record_time(start),
            "engine": "ltx",
        }

    # ------------------------------------------------------------------
    # Lifecycle (mirrors GoldTeamClient)
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "LTXVideoEngine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
