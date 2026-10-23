"""preview_engine.py - PreviewEngine strategy pattern (single H3 preview engine).

The Phase 40 rapid-preview tier produces 3 low-quality variants per shot by
varying exactly ONE structure parameter from baseline (Notion 红线 #6 — control
variable). Rendering is delegated to a single engine:

- ``H3PreviewEngine``: composes an ``H3VideoEngine`` (from
  ``plugins.kais_aigc.video_engine``) and renders the preview variant through
  the KAP unified H3 pipeline using the ``preview-lock`` useCase
  (lightx2v-8-768p 9 步统一 — KAP ``H3_PREVIEW_MOTION_ROUTES`` 全档路由,
  2026-08-31; 原 turbo/native-sage 分档映射已退役). Mirrors the ``H3VideoEngine``
  D-09 degrade-first contract.

This module is pure library code — the p11a phase module composes this engine
into the rapid-preview fan-out. NO phase integration here.

Design invariants:
- D-04: ``transport`` + ``frame_validator`` constructor kwargs on
  ``H3PreviewEngine`` forward to ``H3VideoEngine`` so tests inject
  ``httpx.MockTransport`` / a fake validator for hermetic mocking.
- D-06: All configuration is read from env vars at construction / call time
  (never at module import).
- D-09: Degrade-first contract. Connection errors / timeouts / 5xx / 429 return
  ``{"degraded": True, ...}``; they never raise to the caller. 4xx raises
  ``PreviewEngineError`` (caller bug).
- Strategy selection: ``select_engine()`` reads ``KAIS_PREVIEW_ENGINE`` at
  call time (not import time). Default is ``"h3"``. Unknown values fall back
  to ``H3PreviewEngine`` + WARN log (T-40-09 mitigation: no eval(), no dynamic
  lookup; predictable fallback).

Engine unification (2026-08-10): the dual-engine strategy (slideshow FFmpeg +
LTX-Video HTTP) was retired when H3 became the single video engine across both
the preview tier (P11a, useCase=preview-lock) and the production tier (P11b,
useCase=final-shot).
``SlideshowEngine`` and ``LTXVideoEngine`` are gone; ``H3PreviewEngine`` is the
only concrete engine.
"""

from __future__ import annotations

import abc
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase 40 WR-05 fix — path-traversal validation helper
# ---------------------------------------------------------------------------
# ``keyframe_image_path`` and ``voice_clip_path`` are read from untrusted
# upstream slots (``e-konte-sheets`` / ``voice-clips``, both produced by
# LLM-driven phases per CONTEXT D-35-04). These strings flow directly into
# FFmpeg's ``-i`` argv. List-form argv (T-40-06) correctly prevents SHELL
# injection, but does NOT prevent PATH TRAVERSAL — a malicious or buggy
# upstream output like ``../../etc/passwd`` would still be a filesystem
# read by FFmpeg, and the path would be persisted in the JSONL record.
#
# ``_validate_path_under_root`` rejects paths that escape an allow-listed
# base directory. Default behavior (no roots configured) accepts all paths
# — preserves test behavior and lets production wire explicit allow-lists
# via the ``SlideshowEngine(allowed_path_roots=[...])`` constructor kwarg.


def _validate_path_under_root(
    path: str | None,
    allowed_roots: list[str] | None,
    *,
    field_name: str = "path",
) -> str | None:
    """Validate ``path`` is under one of ``allowed_roots`` (or accept all
    if ``allowed_roots`` is empty / None).

    Returns the original ``path`` if it passes validation. Returns ``None``
    if ``path`` is ``None`` (caller is responsible for the missing-input
    degrade path).

    Raises ``ValueError`` if:
      - ``path`` contains a ``..`` sequence that resolves outside all
        allowed roots.
      - ``path`` is absolute and not under any allowed root.

    Validation is conservative: a path is "under" a root iff
    ``Path(path).resolve()`` is equal to or a descendant of
    ``Path(root).resolve()`` (after symlink resolution). Both ``path``
    and ``root`` are resolved before comparison so symbolic links can't
    smuggle a traversal past the check.

    When ``allowed_roots`` is empty or ``None``, the function is a no-op
    pass-through — production callers MUST configure an explicit allow-list
    to get any protection.
    """
    if path is None:
        return None
    if not allowed_roots:
        return path
    resolved = Path(path).resolve()
    for root in allowed_roots:
        try:
            resolved_root = Path(root).resolve()
        except (OSError, ValueError):
            continue
        # ``is_relative_to`` is the canonical "is descendant" check on
        # Path; available since Python 3.9. Handles the equal-to-root
        # case too (a path is relative to itself).
        if resolved == resolved_root or resolved_root in resolved.parents:
            return path
    raise ValueError(
        f"{field_name} {path!r} resolves outside all allowed roots "
        f"({len(allowed_roots)} configured) — path traversal rejected"
    )


class PreviewEngineError(Exception):
    """Raised for 4xx client errors from the preview engine's backing API (caller bug).

    Mirrors ``GoldTeamError`` / ``VideoEngineError`` semantics: connection
    errors / timeouts / 5xx / 429 do NOT raise — they degrade (return a
    ``{"degraded": True, ...}`` envelope to the caller). 4xx and invalid-JSON
    2xx responses are caller / service bugs and raise this exception.
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
        form_factor: str | None = None,
    ) -> dict:
        """Produce one rapid-preview variant. Subclasses MUST implement.

        ``form_factor`` (episode-level "landscape"/"portrait"; ``None`` →
        engine default) lets the caller pin the preview's aspect ratio.

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
    # engine is selected. ``H3PreviewEngine`` overrides these to delegate to
    # its wrapped ``H3VideoEngine`` (which closes the underlying
    # ``httpx.Client`` connection pool).
    #
    # Before the CR-02 fix, a concrete engine defined ``close`` /
    # ``__enter__`` / ``__exit__`` but the phase body never entered the
    # context manager — leaking one ``httpx.Client`` connection pool per
    # episode in long-running daemons (gateway / cron).

    def close(self) -> None:
        """Release engine-held resources. No-op default; subclasses override."""
        # H3PreviewEngine overrides this to delegate to its wrapped
        # H3VideoEngine (closing the httpx.Client).
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
    3. Default ``"h3"`` (H3 preview — lightx2v-8-768p 9 步统一, the single
    preview engine).

    Unknown values fall back to ``H3PreviewEngine`` AND emit a WARN log
    mentioning the unknown value (T-40-09 mitigation — no eval(), no
    dynamic class lookup; predictable fallback).
    """
    value = env if env is not None else os.environ.get("KAIS_PREVIEW_ENGINE", "h3")
    if value == "h3":
        return H3PreviewEngine()
    logger.warning(
        "unknown KAIS_PREVIEW_ENGINE=%r, falling back to h3",
        value,
    )
    return H3PreviewEngine()


# ----------------------------------------------------------------------
# H3PreviewEngine — composes an H3VideoEngine (lightx2v-8-768p 9-step preview
# profile) for the
# preview tier. generate() bridges the PreviewEngine.generate signature to
# H3VideoEngine.render; the abstract PreviewEngine.generate() raises
# NotImplementedError (ABC pattern).
# ----------------------------------------------------------------------


class H3PreviewEngine(PreviewEngine):
    """H3 preview engine (composes ``H3VideoEngine``).

    The Phase 40 rapid-preview tier renders each variant through the KAP
    unified H3 pipeline using the ``preview-lock`` useCase (lightx2v-8-768p
    9 步统一 — KAP ``H3_PREVIEW_MOTION_ROUTES`` 全档路由, tts-only audio
    mixing — 2026-08-17 KAP API 精简, 2026-08-31 全档路由定案). This engine COMPOSES (does
    not subclass) an ``H3VideoEngine`` instance and bridges the
    ``PreviewEngine.generate`` signature to ``H3VideoEngine.render``.

    Why composition instead of subclassing: ``H3VideoEngine.render`` takes a
    ``shot`` dict (carrying ``h3_useCase`` / ``h3_motion`` / ``duration_sec``
    / ``shot_id`` / prompt) while ``PreviewEngine.generate`` takes those
    values as separate kwargs plus a ``structure_delta`` dict. The bridge
    builds the ``shot`` dict on each call so callers (p11a) keep the
    preview-tier contract while the production render code (H3VideoEngine)
    is reused verbatim.

    ``h3_useCase`` is hardcoded to ``"preview-lock"`` here — this IS the preview
    tier; production renders go through ``H3VideoEngine`` directly (p11b)
    with useCase=final-shot. ``h3_motion`` is sourced from ``structure_delta``
    (default ``"medium"``) so p11a's motion classification reaches the
    engine's motion-adaptive step selector. ``duration_sec`` is sourced
    from ``structure_delta`` (default 5.0s) when the variant carries one.

    D-09 degrade-first contract is inherited from ``H3VideoEngine.render``,
    which returns ``{"degraded": True, "engine": "h3", "reason": str}`` on
    any network / validation failure (no raise to the caller).
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
        frame_validator: Callable[[str, int], tuple[bool, str]] | None = None,
    ) -> None:
        """Construct the engine, forwarding kwargs to the wrapped H3VideoEngine.

        Parameters (D-06 env-var configuration at construction time):

        - ``base_url`` / ``KAIS_H3_URL``: KAP unified pipeline base URL.
        - ``timeout``: per-request timeout in seconds.
        - ``transport``: hermetic test injection via ``httpx.MockTransport``.
          ``None`` (default) uses real networking.
        - ``frame_validator``: P0-4 frame-gate injection point forwarded to
          H3VideoEngine. ``None`` (default) uses the built-in
          ``_default_frame_validator`` (ffprobe duration + frame-count check).
          Tests inject a fake to bypass ffprobe.
        """
        from plugins.kais_aigc.video_engine import H3VideoEngine

        self._h3 = H3VideoEngine(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            frame_validator=frame_validator,
        )

    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,  # deprecated — see docstring
        voice_clip_path: str | None = None,
        output_path: str | None = None,
        form_factor: str | None = None,
        turnaround_paths: list[str] | None = None,
        scene_ref_path: str | None = None,
        first_frame: str | None = None,
    ) -> dict:
        """Bridge ``PreviewEngine.generate`` to ``H3VideoEngine.render``.

        Builds a ``shot`` dict with ``h3_useCase="preview-lock"`` and the variant's
        ``h3_motion`` + ``duration_sec`` (read from ``structure_delta``),
        then delegates to ``H3VideoEngine.render``. The render envelope is
        returned VERBATIM — ``H3VideoEngine.render`` already returns the
        PreviewEngine-compatible shape:

        - Success: ``{clip_path, generation_time_ms, engine:"h3",
          frame_count, video_url}``
        - Degrade: ``{degraded: True, engine:"h3", reason}``

        ``form_factor`` (episode-level "landscape"/"portrait") is stamped on
        the synthesized shot so ``_resolve_resolution`` renders previews in
        the episode's aspect — without it every preview was portrait
        (review report 2026-08-14 行动建议#9).

        Character consistency (2026-08-16 fix): ``turnaround_paths`` /
        ``scene_ref_path`` carry the shot's character turnaround sheets +
        scene reference image into the H3 refImages[] multipart. When at
        least one resolves to an existing file the synthesized shot uses
        ``mode: "ref2va"`` (reference-anchored generation); when both are
        absent the shot stays ``mode: "t2va"`` (zero-reference graceful
        degrade — pre-fix behavior). Missing files are skipped by
        ``H3VideoEngine._build_multipart`` (engine-layer contract).

        ``keyframe_image_path`` is DEPRECATED: accepted for signature
        compatibility but never consumed (the t2va mode it fed never used
        it either — see the 2026-08-16 review confirming the parameter was
        dead since introduction).

        ``first_frame`` (2026-08-22 SPEC-firstframe): forwarded verbatim to
        ``H3VideoEngine.render`` → multipart ``image`` field (first-frame
        lock). ref2va 的图像先验会覆盖 prompt 景别/运镜文本指令，首帧锁
        把构图/机位控制挪到图像层。预览层接通后，镜头语言可在预览成本
        验证（p11c 打回前的廉价拦截）。None → 行为与接入前一致。
        """
        sd = structure_delta if isinstance(structure_delta, dict) else {}
        # ref2va eligibility: at least one turnaround OR a scene ref that
        # exists on disk. os.path.isfile (not just truthiness) so a stale
        # shot-list path degrades to t2va instead of sending H3 a refImages
        # part that resolves to nothing.
        _has_ref = (
            any(os.path.isfile(p) for p in (turnaround_paths or []) if isinstance(p, str))
            or (isinstance(scene_ref_path, str) and os.path.isfile(scene_ref_path))
        )
        shot = {
            "shot_id": shot_id,
            # 2026-08-17 KAP API 精简: useCase 入口 (KAP 侧 motion 跨拓扑路由;
            # 2026-08-31 起 H3_PREVIEW_MOTION_ROUTES 全档路由至
            # lightx2v-8-768p 9 步统一, tts-only 混音)。
            "h3_useCase": "preview-lock",
            # ref2va when reference images exist; t2va (text-only) otherwise.
            "mode": "ref2va" if _has_ref else "t2va",
            "h3_motion": sd.get("h3_motion", "medium"),
            "duration_sec": sd.get("duration_sec", 5.0),
            "intent": prompt,
            "prompt": prompt,
        }
        if form_factor:
            shot["form_factor"] = form_factor
        return self._h3.render(
            shot=shot,
            output_path=output_path,
            turnaround_paths=turnaround_paths,
            scene_ref_path=scene_ref_path,
            voice_clip_path=voice_clip_path,
            first_frame=first_frame,
            prompt=prompt,
        )

    # ------------------------------------------------------------------
    # Lifecycle — delegate to the wrapped H3VideoEngine so the httpx.Client
    # connection pool is released. The P11a ``with select_engine() as engine:``
    # block depends on this.
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Delegate to the wrapped H3VideoEngine (closes its httpx.Client)."""
        self._h3.close()

    def __enter__(self) -> "H3PreviewEngine":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
