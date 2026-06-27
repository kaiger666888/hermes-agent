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
import time
from typing import Any, Callable

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

    Stub at Task 1 boundary. Task 2 implements:
    - Constructor ``subprocess_runner`` kwarg for hermetic test injection.
    - ``generate()`` builds the FFmpeg argv (list form — no shell=True per
      T-40-06 mitigation), validates inputs, measures wall time, returns
      success / degrade envelope.
    """

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
        raise NotImplementedError(
            "SlideshowEngine.generate() implemented in plan 40-02 Task 2"
        )


class LTXVideoEngine(PreviewEngine):
    """LTX-Video HTTP engine (mocked in v6.0).

    Stub at Task 1 boundary. Task 3 implements:
    - Constructor mirroring GoldTeamClient (transport / base_url / timeout).
    - ``_request()`` enforcing D-09 degrade-first contract.
    - ``generate()`` POSTing to ``/api/v1/ltx`` and returning the success /
      degrade envelope (INFO #10: locally-measured wall time).
    """

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
        raise NotImplementedError(
            "LTXVideoEngine.generate() implemented in plan 40-02 Task 3"
        )
