"""vision_verify.py — vision-verify mandatory gate (IMG-03), engine registry.

2026-08-18 冗余审核体系 (KMC 视觉审核重构, 用户裁决 1「不要降级」): any
engine-level failure of the ONLY engine in effect raises
``VisionEngineUnavailable`` — the caller fail-closes instead of silently
degrading or skipping the verdict.

2026-08-27 (fixbatch-004, Kai 裁决「默认行为零变化」): the seam widened
into a configurable ENGINE ADAPTER REGISTRY with two arms:

  - ``qwen-eye``      local arm (Qwen3.8-27B VL on :8125 via qwen_eye.py,
                      KAP allocate → kap-llm.sh startup chain unchanged).
  - ``glm-5.3-flash`` hosted arm (Zhipu MAIN model direct on the v4
                      OpenAI-compatible endpoint, stdlib urllib call;
                      NOT glm-4.6v and NO resurrection of the removed
                      ``async_call_llm`` import — channel verified
                      natively-vision-capable on 2026-08-27).

2026-08-27 (fixbatch-007, Kai 三引擎盲测终审裁决):

  1. glm-5.3-flash (hosted) 完全胜出 → 成为 Hermes 所有 skill 与 KAP
     视觉方案的唯一默认引擎；
  2. glm-4.6v 全面废弃，残留引用清理替换；
  3. qwen-eye 收缩到纯视频分析需求（图像判定/描述域废弃）。

``_ENGINE_ORDER_DEFAULT`` therefore FLIPPED to ``["glm-5.3-flash"]``
(was ``["qwen-eye"]`` through fixbatch-006). Fail-closed semantics are
unchanged: an arm-level failure of the sole default arm still raises
``VisionEngineUnavailable``. ``qwen-eye`` stays a KNOWN engine — an
explicit ``~/.hermes/config.yaml`` ``vision_verify.engines`` order (or a
per-call ``engine_order``) can still run it, and a configured order
listing BOTH arms keeps the fall-through behavior. This flip also added
the observation-layer twin ``observe_image_content`` (free-text Q&A over
one image) so pipeline phases stop importing QwenEye directly for image
judgement/description (qwen-eye remains the video-analysis engine, e.g.
p11c video_qc).

2026-08-27 (fixbatch-005): the result cache is keyed per (image sha,
engine). The pre-registry key was the bare sha, so once the registry made
multiple engines coexist, a verdict cached by engine A kept being served
(``cached=True``) to calls reconfigured to judge with engine B for the
whole 24h TTL — cross-engine pollution of a fail-closed verdict. Entries
are now written only by the arm that actually judged (on an order
fall-through: the final executor), and reads consult only the engines in
the caller's resolved order.

2026-08-27 (fixbatch-006): the cache key gained its third dimension —
the JUDGING QUESTION (16-hex sha256 of the full ``_build_question``
text). The (sha, engine) key served a verdict for question A to a later
call asking question B about the SAME image for the whole 24h TTL: an
acceptance harness's negative controls (same image × another shot's
question) all echoed the positive controls' cached verdicts, and
production hits the same trap whenever an unchanged image is re-judged
against a changed expected_content / directional_check (P07 scene-edit
re-verify, P11 direction flips). Every cache read/write site composes
the same three-part key, so an old two-part entry can never mix in.

Gate semantic (PITFALL I-2, updated for the hard-gate era):
  "pass" = an arm ran and returned high-confidence match.
  Low-confidence -> pass=False (content fail — callers route it into the
  redundancy/regenerate/human-review pipeline, NOT silent acceptance).
  All-configured-arms-down -> VisionEngineUnavailable (fail-closed, never
  skipped). Each result entry carries ``engine`` naming the actual judge.
"""

from __future__ import annotations

import base64
import hashlib
import inspect
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.request import Request as _Request
from urllib.request import urlopen as _urlopen

from hermes_constants import get_hermes_home
from ruamel.yaml import YAML

from plugins.kais_aigc.qwen_eye import (
    LLM_START_TIMEOUT_S as QWEN_EYE_START_TIMEOUT_S,
    QwenEye,
)

logger = logging.getLogger(__name__)


class VisionEngineUnavailable(RuntimeError):
    """No configured vision judge arm could be brought up or answered.

    Raised by verify_image_content / verify_batch when EVERY configured
    engine failed at engine level (not ready after the startup budget,
    empty response, call exception).
    Content-level LOW confidence is NOT this — that's a normal
    ``{"pass": False}`` result. Callers must fail-closed (KMC phases
    convert this to a QualityGateRejection with category
    "engine_unavailable"; it must never be silently skipped).
    """

# ── Module-level cache ─────────────────────────────────────────────────────

_cache: dict[str, dict[str, Any]] = {}
"""Result cache. Key = f"{sha}:{engine}:{sha256(question)[:16]}"
(fixbatch-005: per-engine isolation — the old bare-sha key served engine
A's verdict to engine-B calls for the whole TTL; fixbatch-006: the
judging-question dimension — the (sha, engine) key served a verdict for
question A to calls asking question B about the same image). Value =
parsed result dict WITHOUT the "cached" key (added by verify_image_content
on return).

WR-07 concurrency note: this dict is mutated by both verify_image_content
and verify_batch without a lock. CPython's GIL makes individual dict
get/set/del atomic (no corruption risk), but the check-then-insert
pattern is racy: two concurrent batch tasks verifying the same image
(duplicate file in one batch) will both miss the cache, both invoke the
engine, and both write — wasting one call. This is an inefficiency,
not a correctness bug (both writes are idempotent). Deliberate decision:
the dominant dedup win is across iterative editing runs (a separate
batch_submit invocation re-verifying unchanged frames), where there is
NO concurrency. If a future caller invokes verify_image_content
concurrently from multiple async tasks with high image-duplicate rates,
revisit and add an in-flight Future dedup layer."""

_CACHE_TTL_SEC = 86400
"""24h TTL per CONTEXT.md specifics. Entries older than this are evicted
on next access (avoids re-verifying identical images across iterative
editing runs while eventually invalidating stale results)."""


def _cache_key(sha: str, engine: str, question: str) -> str:
    """Composite cache key: image digest + judging engine + question
    fingerprint (fixbatch-005 per-engine, fixbatch-006 per-question).

    ``engine`` is the arm that ACTUALLY executed the judgement — on an
    order fall-through the final executor, not the first-tried arm.
    ``question`` is the FULL judgement text sent to the engine (the
    ``_build_question`` output); a 16-hex sha256 keeps the key short
    while keeping verdicts that answered different questions about the
    same image in separate entries.
    """
    digest = hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]
    return f"{sha}:{engine}:{digest}"

# ── Confidence threshold ───────────────────────────────────────────────────

_CONFIDENCE_THRESHOLD = 0.7
"""High-confidence threshold. Above → pass=True (auto). Below → pass=False
(flagged for operator review, NOT auto-rejected per PITFALL I-2 #4)."""

# ── Per-stratum threshold override (IMG-09-APPLY) ──────────────────────────

_threshold_cache: dict[str, float] = {}
"""Process-lifetime cache of per-stratum thresholds read from config.yaml.
Key = stratum string (e.g. "1-ref"). Value = resolved threshold float.
Cache is process-lifetime — config changes require restart. This is
acceptable for CLI tools and batch_submit runs which are short-lived
processes. The cache avoids re-reading + parsing config.yaml on every
verify_image_content call within a single batch (4-8 images per batch)."""


def get_threshold(stratum: str | None = None) -> float:
    """Resolve the confidence threshold for a given stratum.

    IMG-09-APPLY: reads per-stratum thresholds from
    ``~/.hermes/config.yaml`` ``vision_verify.thresholds`` block. Falls
    back to ``_CONFIDENCE_THRESHOLD`` (0.7) if:

    - ``stratum`` is None (backward-compatible — existing callers without
      stratum param get the default 0.7).
    - Config file doesn't exist.
    - ``vision_verify`` block doesn't exist.
    - ``thresholds`` block doesn't exist.
    - Stratum key not in thresholds.
    - Value is invalid (not a float, or out of [0.0, 1.0] range).
    - Any error occurs during config read (T-79-04: config-read failures
      NEVER break vision-verify — it's a mandatory gate).

    Uses ``_threshold_cache`` to avoid re-reading config on every call
    within a process lifetime.

    Args:
        stratum: Stratum string ("1-ref" / "3-ref" / "5-ref" / "text2image")
            or None for default.

    Returns:
        Confidence threshold as a float (0.0-1.0).
    """
    if stratum is None:
        return _CONFIDENCE_THRESHOLD

    # Check cache first (process-lifetime).
    cached = _threshold_cache.get(stratum)
    if cached is not None:
        return cached

    threshold = _CONFIDENCE_THRESHOLD  # default fallback
    try:
        config_path = Path(get_hermes_home()) / "config.yaml"
        if config_path.exists():
            yaml = YAML()
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.load(f)
            if config is not None:
                vv_block = config.get("vision_verify")
                if vv_block is not None:
                    thresholds_block = vv_block.get("thresholds")
                    if thresholds_block is not None:
                        raw = thresholds_block.get(stratum)
                        if raw is not None:
                            val = float(raw)
                            if 0.0 <= val <= 1.0:
                                threshold = val
        # WR-04: Only cache successful config reads. Caching the fallback
        # 0.7 on config-read errors (e.g. file locked, permission issue)
        # would poison the cache for the entire process lifetime, even if
        # the config becomes readable later. For long-running gateway
        # processes, a transient startup failure would permanently lock
        # all thresholds to 0.7.
        _threshold_cache[stratum] = threshold
        return threshold
    except Exception as exc:
        logger.warning(
            "Failed to read vision_verify thresholds from config: %s", exc
        )
        # Don't cache — retry on next call so a transient error doesn't
        # poison the cache for the process lifetime.
        return _CONFIDENCE_THRESHOLD


# ── Engine routing (adapter registry — local/hosted arms, fixbatch-004) ───

_ENGINE_ORDER_DEFAULT = ["glm-5.3-flash"]
"""fixbatch-007 (2026-08-27 Kai 终审): hosted glm-5.3-flash is THE default.
``qwen-eye`` remains known — explicit config/per-call order only (and the
video-analysis consumers outside this seam)."""

_KNOWN_ENGINES = ("qwen-eye", "glm-5.3-flash")

_engine_order_cache: list[str] | None = None
"""Process-lifetime cache of the configured engine order (None = not yet
read). Mirrors ``_threshold_cache`` semantics: config-read failures never
break the gate — they fall back to the default order."""


def get_engine_order() -> list[str]:
    """Resolve the engine order for verify/observe image calls.

    Reads ``~/.hermes/config.yaml`` ``vision_verify.engines`` (a list) and
    keeps only names in ``_KNOWN_ENGINES``. Two arms are known —
    ``"glm-5.3-flash"`` (hosted, the fixbatch-007 DEFAULT) and
    ``"qwen-eye"`` (local, explicit opt-in only since 2026-08-27). Unknown
    names are dropped; a config yielding no known engines falls back to
    the default order (a typo or stale config can't leave the gate
    engineless).
    """
    global _engine_order_cache
    if _engine_order_cache is not None:
        return list(_engine_order_cache)

    order = list(_ENGINE_ORDER_DEFAULT)
    try:
        config_path = Path(get_hermes_home()) / "config.yaml"
        if config_path.exists():
            yaml = YAML()
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.load(f)
            if config is not None:
                raw = (config.get("vision_verify") or {}).get("engines")
                if isinstance(raw, list) and raw:
                    known = [e for e in raw if e in _KNOWN_ENGINES]
                    if known:
                        order = known
        _engine_order_cache = order
        return list(order)
    except Exception as exc:
        logger.warning(
            "Failed to read vision_verify engines from config: %s", exc
        )
        # Don't cache — retry on next call so a transient error doesn't
        # poison the order for the process lifetime.
        return list(_ENGINE_ORDER_DEFAULT)


def _new_qwen_eye() -> QwenEye:
    """Build the per-caller qwen-eye engine handle (caller identity is
    the KAP allocate lease attribution)."""
    return QwenEye(caller="kap:vision_verify")


# ── Public API ─────────────────────────────────────────────────────────────


def _extract_usage(response: Any) -> dict[str, int]:
    """Deprecated stub — retained ONLY for backward import compatibility.

    The GLM-4.6V path that consumed it was removed (2026-08-18 no-degrade
    policy); qwen-eye is a local engine with no metered tokens, so usage
    is always 0/0. Kept as a no-op so any external importer keeps working.
    """
    return {"input_tokens": 0, "output_tokens": 0}


async def verify_image_content(
    image_path: str,
    expected_content: str,
    directional_check: str | None = None,
    stratum: str | None = None,
    *,
    engine_order: list[str] | None = None,
    fresh: bool = False,
) -> dict[str, Any]:
    """Verify a dreamina-generated image matches expected content.

    Engines are tried in registry order (``engine_order`` override, else
    ``get_engine_order()``): an arm that produces no result falls through
    to the next configured arm. When EVERY configured arm fails to
    produce a result, raises ``VisionEngineUnavailable`` — callers
    fail-closed (never silently skip). Content-level low confidence
    returns ``pass=False`` as before.

    Args:
        image_path: Local path to the generated image (.png/.jpg).
        expected_content: What the image SHOULD contain (e.g. "baby in car seat").
        directional_check: Optional directional question.
            "lhd" → asks "方向盘在左侧（左舵LHD）还是右侧（右舵RHD）？".
        stratum: Optional IMG-05 stratum ("1-ref" / "3-ref" / "5-ref" /
            "text2image"). When provided, the confidence threshold is read
            from ``~/.hermes/config.yaml`` ``vision_verify.thresholds`` block
            via ``get_threshold(stratum)``. When None (default), uses
            ``_CONFIDENCE_THRESHOLD`` (0.7) — backward-compatible.
        engine_order: Optional per-call engine order override. Names not in
            ``_KNOWN_ENGINES`` are ignored.
        fresh: Skip the cache READ for this call (multi-sample
            independence). Purpose: when one image is judged MULTIPLE
            times within one protocol — e.g. the anatomy_limb checker's
            3-sample majority vote — the 24h-TTL result cache would serve
            the first sample's verdict to samples 2..N (same image bytes +
            same engine + same question ⇒ same three-part key), collapsing
            the vote to "1 ballot ×N" and defeating the independence the
            protocol paid N× engine calls for. ``fresh=True`` bypasses the
            read side ONLY; a successful arm call is still WRITTEN to the
            cache, so the ordinary "identical re-ask is free" economics
            survive for subsequent non-fresh callers. Default False is
            zero-behavior-change for every existing caller. This cannot
            break the earlier cache-isolation semantics: fixbatch-005
            (per-engine keys), fixbatch-006 (per-question keys) and
            fixbatch-007 (verdict-shaped entries only) all govern WHICH
            entries may SERVE a read — fresh merely opts THIS call out of
            reading; writes still go through the same three-part key.

    Returns:
        {"pass": bool, "confidence": float, "description": str, "cached": bool,
         "fresh": bool,
         "usage": {"input_tokens": int, "output_tokens": int},
         "engine": "<name of the arm that actually judged>"}

        ``fresh`` echoes the input flag (a cache hit is always
        ``fresh=False``; a fresh call reports ``cached=False`` for the
        round it just judged).

    Raises:
        VisionEngineUnavailable: every arm in the (non-empty known) order
            failed at engine level.
    """
    p = Path(image_path)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    order = list(engine_order or get_engine_order())
    # The question text actually sent to whichever arm judges (built here
    # so the cache key fingerprints the exact same text the arms send).
    question = _build_question(expected_content, directional_check)

    # Cache hit? (fixbatch-005: entries are keyed per (sha, engine) — only
    # engines in THIS call's resolved order are consulted, so a verdict
    # cached by engine A is never served to a call reconfigured to judge
    # with engine B. First engine in order with a fresh entry wins.
    # fixbatch-006: the key also fingerprints the judging question, so a
    # cached verdict is only served to calls asking the SAME question
    # about the image. ``fresh=True`` opts THIS call out of the read side
    # entirely — multi-sample independence — while writes below stay on.)
    if not fresh:
        for engine in order:
            key = _cache_key(sha, engine, question)
            cached_entry = _cache.get(key)
            if cached_entry is None or "pass" not in cached_entry:
                # fixbatch-007: only serve verdict-shaped entries — an
                # observe_image_content entry ({"text", ...}) can share this key
                # when a caller asks the verify question verbatim as an observe
                # question; serving it here would return a dict without
                # pass/confidence.
                continue
            age = time.time() - cached_entry.get("_ts", 0)
            if age < _CACHE_TTL_SEC:
                result = {k: v for k, v in cached_entry.items() if k != "_ts"}
                result["cached"] = True
                # Cache hit → no new API call → zero tokens.
                result["usage"] = {"input_tokens": 0, "output_tokens": 0}
                result["fresh"] = False  # a hit is never a fresh call (echo)
                return result
            del _cache[key]  # expired

    threshold = get_threshold(stratum)
    last_engine_error: VisionEngineUnavailable | None = None

    for pos, engine in enumerate(order):
        arm = _resolve_arm(engine)
        if arm is None:
            continue  # unknown engine name — ignored
        last_engine_error: VisionEngineUnavailable | None = None
        try:
            result = arm(p, expected_content, directional_check, threshold)
        except VisionEngineUnavailable as exc:
            # Engine-level failure of THIS arm (local arm raises; hosted
            # returns None instead). Both mean "no result from this arm".
            last_engine_error = exc
            result = None
        if result is None:
            remaining = [e for e in order[pos + 1:] if e in _ENGINE_ARMS]
            if remaining:
                logger.warning(
                    "vision-verify: %s arm produced no result for %s (%s) "
                    "— falling through to %s",
                    engine, image_path,
                    last_engine_error or "hosted call failed", remaining[0],
                )
                continue  # try the next configured arm
            break  # last known arm — fall out to fail-closed below
        result["engine"] = engine
        # Cache the result under the engine that ACTUALLY judged and the
        # question that was actually asked (fixbatch-005 per-engine,
        # fixbatch-006 per-question isolation) — on an order fall-through
        # this loop variable IS the final executor. A fresh call writes
        # too: later NON-fresh callers (identical re-ask) still hit.
        _cache[_cache_key(sha, engine, question)] = {**result, "_ts": time.time()}
        result["cached"] = False
        result["fresh"] = fresh
        return result

    # Reached when NO configured arm produced a result. When the last arm
    # failed at ENGINE level, re-raise its original exception so callers
    # keep the precise pre-registry diagnostics ("not healthy in Ns" etc.);
    # otherwise (order named no known engine at all) raise the generic.
    if last_engine_error is not None:
        raise last_engine_error
    raise VisionEngineUnavailable(
        f"vision-verify: no usable arm in engine order {order} for "
        f"{image_path} — known arms: {list(_KNOWN_ENGINES)}"
    )


async def observe_image_content(
    image_path: str,
    question: str,
    *,
    engine_order: list[str] | None = None,
) -> dict[str, Any]:
    """Free-text observation of ONE image through the engine registry.

    fixbatch-007 (2026-08-27 Kai 终审): the observation-layer twin of
    ``verify_image_content`` — same registry, same fall-through, same
    fail-closed semantics — so pipeline phases stop importing QwenEye
    directly for image description. The ``question`` is sent VERBATIM (no
    yes/no/confidence template, no verdict parsing); the caller owns
    whatever it does with ``text`` (embed it in a judge prompt, parse a
    JSON contract, or ship it as a description).

    Engines are tried in registry order (``engine_order`` override, else
    ``get_engine_order()`` — default glm-5.3-flash since the fixbatch-007
    flip): an arm that produces no result falls through to the next
    configured arm; when EVERY configured arm fails, raises
    ``VisionEngineUnavailable`` — callers fail-closed, exactly like the
    verify twin.

    Cache: same three-part key ``(image_sha : engine : question[:16])``
    and 24h TTL as the verify path (an identical re-ask is free). A cache
    hit reports usage 0/0.

    Args:
        image_path: Local path to the image (.png/.jpg).
        question: Free-text question/instruction sent verbatim as the
            text part of the single user message.
        engine_order: Optional per-call engine order override. Names not
            in ``_KNOWN_ENGINES`` are ignored.

    Returns:
        {"text": str, "engine": "<arm that actually answered>",
         "cached": bool, "usage": {"input_tokens": int, "output_tokens": int}}

    Raises:
        VisionEngineUnavailable: every arm in the (non-empty known) order
            failed at engine level.
    """
    p = Path(image_path)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    order = list(engine_order or get_engine_order())

    # Cache hit? Only observe-shaped entries ({"text", ...}) serve here —
    # a verify entry can share this key when someone asks a verify-format
    # question verbatim; its pass/confidence shape is not ours to serve.
    for engine in order:
        key = _cache_key(sha, engine, question)
        cached_entry = _cache.get(key)
        if cached_entry is None or "text" not in cached_entry:
            continue
        age = time.time() - cached_entry.get("_ts", 0)
        if age < _CACHE_TTL_SEC:
            result = {k: v for k, v in cached_entry.items() if k != "_ts"}
            result["cached"] = True
            # Cache hit → no new API call → zero tokens.
            result["usage"] = {"input_tokens": 0, "output_tokens": 0}
            return result
        del _cache[key]  # expired

    last_engine_error: VisionEngineUnavailable | None = None
    for pos, engine in enumerate(order):
        arm = _resolve_observe_arm(engine)
        if arm is None:
            continue  # unknown engine name — ignored
        last_engine_error = None
        try:
            out = arm(p, question)
        except VisionEngineUnavailable as exc:
            # Local arm raises on engine-level failure; hosted arm returns
            # None instead. Both mean "no answer from this arm".
            last_engine_error = exc
            out = None
        if out is None:
            remaining = [e for e in order[pos + 1:] if e in _OBSERVE_ARMS]
            if remaining:
                logger.warning(
                    "vision-observe: %s arm produced no answer for %s (%s) "
                    "— falling through to %s",
                    engine, image_path,
                    last_engine_error or "hosted call failed", remaining[0],
                )
                continue  # try the next configured arm
            break  # last known arm — fall out to fail-closed below
        result = {
            "text": out["text"],
            "engine": engine,
            "cached": False,
            "usage": out["usage"],
        }
        # Cache under the arm that ACTUALLY answered + the verbatim question.
        _cache[_cache_key(sha, engine, question)] = {
            "text": out["text"], "engine": engine,
            "usage": out["usage"], "_ts": time.time(),
        }
        return result

    if last_engine_error is not None:
        raise last_engine_error
    raise VisionEngineUnavailable(
        f"vision-observe: no usable arm in engine order {order} for "
        f"{image_path} — known arms: {list(_KNOWN_ENGINES)}"
    )


def _verify_via_qwen_eye(
    p: Path,
    expected_content: str,
    directional_check: str | None,
    threshold: float,
) -> dict[str, Any]:
    """Single-image verify through the local qwen-eye engine (LOCAL arm).

    Returns the parsed result dict (WITHOUT the engine/cached keys — the
    caller adds them). Raises ``VisionEngineUnavailable`` on engine-level
    failure (server won't come up / empty response / call exception) —
    2026-08-18 fail-closed hard-gate semantics. Under the 2026-08-27
    registry, that raise is how "this arm produced nothing" is reported:
    the router falls through to a next configured arm if one exists, or
    re-raises this same exception (unchanged diagnostics) when none does.
    The engine server is stopped after the call iff we started it
    (per-caller lease semantics).
    """
    eye = _new_qwen_eye()
    healthy, started_by_us = eye.ensure_ready()
    if not healthy:
        raise VisionEngineUnavailable(
            f"qwen-eye did not become healthy in {QWEN_EYE_START_TIMEOUT_S}s "
            f"(caller kap:vision_verify) — no fallback engine exists, failing closed"
        )
    try:
        question = _build_question(expected_content, directional_check)
        text = eye.observe_single(p, question)
    except VisionEngineUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 — normalized to the engine-down type
        raise VisionEngineUnavailable(
            f"qwen-eye observe_single failed for {p}: {exc}"
        ) from exc
    finally:
        eye.stop_if_owned()
    if not text.strip():
        raise VisionEngineUnavailable(
            f"qwen-eye returned empty response for {p}"
        )
    result = _parse_vision_response(
        text, expected_content, directional_check, threshold,
    )
    # Local engine — no metered tokens to report.
    result["usage"] = {"input_tokens": 0, "output_tokens": 0}
    return result


# ── Observation layer: free-text Q&A arms (fixbatch-007) ────────────────────


def _observe_via_qwen_eye(p: Path, question: str) -> dict[str, Any]:
    """Observation LOCAL arm — ``QwenEye.observe_single`` wrapper.

    Explicit-opt-in only since the fixbatch-007 default flip (qwen-eye's
    image-judgement/description role was deprecated by the Kai verdict;
    this arm keeps a configured local order working). Same lifecycle as
    the verify local arm: ensure_ready fail-closed, stop_if_owned in
    finally. Returns ``{"text", "usage"}``; raises
    ``VisionEngineUnavailable`` on engine-level failure (empty response
    included) so the router falls through / fails closed.
    """
    eye = _new_qwen_eye()
    healthy, _started = eye.ensure_ready()
    if not healthy:
        raise VisionEngineUnavailable(
            f"qwen-eye did not become healthy in {QWEN_EYE_START_TIMEOUT_S}s "
            f"(caller kap:vision_verify, observe) — no fallback engine "
            f"exists, failing closed"
        )
    try:
        text = eye.observe_single(p, question)
    except VisionEngineUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 — normalized to the engine-down type
        raise VisionEngineUnavailable(
            f"qwen-eye observe_single failed for {p}: {exc}"
        ) from exc
    finally:
        eye.stop_if_owned()
    if not text.strip():
        raise VisionEngineUnavailable(
            f"qwen-eye returned empty response for {p}"
        )
    return {"text": text, "usage": {"input_tokens": 0, "output_tokens": 0}}


def _observe_via_zhipu(p: Path, question: str) -> dict[str, Any] | None:
    """Observation HOSTED arm — glm-5.3-flash, question sent verbatim.

    Same HTTP shape as the verify arm via the shared ``_zhipu_vision_chat``
    core; the only difference is the question (raw caller text, no
    yes/no/confidence template) and that the content text is returned
    UNPARSED. Returns ``{"text", "usage"}`` with metered usage, or None
    on ANY failure — never raises (arm contract).
    """
    out = _zhipu_vision_chat(p, question)
    if out is None:
        return None
    text, usage_raw = out
    return {
        "text": text,
        "usage": {
            "input_tokens": _safe_token_count(usage_raw.get("prompt_tokens")),
            "output_tokens": _safe_token_count(usage_raw.get("completion_tokens")),
        },
    }


_OBSERVE_ARMS: dict[str, str] = {
    "qwen-eye": "_observe_via_qwen_eye",
    "glm-5.3-flash": "_observe_via_zhipu",
}


def _resolve_observe_arm(engine: str):
    """Late-bind an engine name to its OBSERVE arm callable, or None when
    unknown (same late-binding rationale as ``_resolve_arm`` — tests that
    monkeypatch ``vv._observe_via_zhipu`` always take effect)."""
    name = _OBSERVE_ARMS.get(engine)
    if name is None:
        return None
    return globals().get(name)


# ── Hosted arm: glm-5.3-flash via Zhipu v4 OpenAI-compatible endpoint ─────

_ZHIPU_VISION_ENDPOINT = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
_ZHIPU_VISION_MODEL = "glm-5.3-flash"
_ZHIPU_VISION_TIMEOUT_S = 180
"""urllib socket timeout in seconds (connect + read headroom). Base64
image uploads are slow; ≥120s total was mandated for the hosted arm."""


def _resolve_zhipu_api_key() -> str | None:
    """Resolve the hosted-arm API key (three sources, one shared key).

    Order: env ``ZHIPU_API_KEY`` first (the plain Zhipu channel var),
    then env ``ZHIPU_VISION_API_KEY`` (explicit vision-only operator
    pin), then the Claude Code launcher credentials at
    ``~/.claude-glm/settings.json`` ``env.ANTHROPIC_AUTH_TOKEN`` (same
    Zhipu-issued token the GLM proxy channel uses — all three hold the
    same key on a standard deployment; the two env vars exist so a
    deployment machine can override without touching the launcher
    settings). Returns None when no source yields a key or the settings
    file is unreadable — the caller then treats the whole hosted arm as
    unavailable (→ next arm / fail-closed).
    """
    key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if key:
        return key
    key = os.environ.get("ZHIPU_VISION_API_KEY", "").strip()
    if key:
        return key
    try:
        settings_path = Path.home() / ".claude-glm" / "settings.json"
        if settings_path.exists():
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            token = ((data.get("env") or {}).get("ANTHROPIC_AUTH_TOKEN") or "")
            token = token.strip()
            if token:
                return token
    except Exception as exc:  # noqa: BLE001 — key-read failure must not break the gate
        logger.warning("vision-verify: could not read ~/.claude-glm/settings.json: %s", exc)
    return None


def _detect_image_mime_type(image_path: Path) -> str | None:
    """Return a MIME type when the file looks like a supported image.

    Header-byte detection (mirrors tools/vision_tools.py:109-128) — never
    trusts the file extension.
    """
    with image_path.open("rb") as f:
        header = f.read(64)

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if header.startswith(b"BM"):
        return "image/bmp"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def _image_to_base64_data_url(image_path: Path, mime_type: str | None = None) -> str:
    """Convert an image file to a base64-encoded data URL.

    CRITICAL: do NOT use file:// URLs — base64 is the safe default (the
    cloud endpoint has no filesystem access)."""
    data = image_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    mime = mime_type or _detect_image_mime_type(image_path) or "image/png"
    return f"data:{mime};base64,{encoded}"


def _zhipu_vision_chat(p: Path, question: str) -> tuple[str, dict] | None:
    """Shared hosted-arm core (fixbatch-007): one image + one question →
    ``(content_text, usage_raw)`` on success, None on ANY failure (no key /
    encode error / network error / non-200 / malformed / empty content) —
    never raises (arm contract). Used by both the verify arm (question =
    ``_build_question`` output, verdict-parsed upstream) and the observe
    arm (raw free-text question). NOTE: glm-5.3-flash is BOTH natively
    vision-capable AND a thinking model (dual-protocol verified
    2026-08-27) — the answer lives in ``choices[0].message.content``;
    ``reasoning_content`` is ignored deliberately.
    """
    key = _resolve_zhipu_api_key()
    if not key:
        logger.warning(
            "vision-verify: glm-5.3-flash arm unavailable — none of "
            "ZHIPU_API_KEY / ZHIPU_VISION_API_KEY env vars nor "
            "~/.claude-glm/settings.json env.ANTHROPIC_AUTH_TOKEN "
            "yielded a key"
        )
        return None

    try:
        data_url = _image_to_base64_data_url(p)
    except Exception as exc:  # noqa: BLE001 — unreadable image → next arm
        logger.warning(
            "vision-verify: glm-5.3-flash arm could not encode %s: %s", p, exc,
        )
        return None

    payload = {
        "model": _ZHIPU_VISION_MODEL,
        "temperature": 0.1,
        # Thinking-model headroom: reasoning_content generation shares this
        # budget with the final answer on bigmodel v4, and a truncated CoT
        # can leave ``content`` empty → None. 4096 keeps the answer intact
        # even behind long CoT.
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": question},
                ],
            }
        ],
    }
    request = _urllib_request_with_key(_ZHIPU_VISION_ENDPOINT, payload, key)

    try:
        with _urlopen(request, timeout=_ZHIPU_VISION_TIMEOUT_S) as resp:
            status = getattr(resp, "status", None)
            if status != 200:
                logger.warning(
                    "vision-verify: glm-5.3-flash arm got HTTP %s — "
                    "treating as unavailable",
                    status,
                )
                return None
            body = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001 — network/HTTP/JSON failures all degrade
        logger.warning("vision-verify: glm-5.3-flash call failed: %s", exc)
        return None

    try:
        message = body["choices"][0]["message"]
        text = message.get("content") or ""
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        logger.warning("vision-verify: glm-5.3-flash response malformed: %s", exc)
        return None
    if not text.strip():
        logger.warning("vision-verify: glm-5.3-flash returned empty content")
        return None

    usage_raw = body.get("usage") or {}
    return text, usage_raw


def _verify_via_zhipu(
    p: Path,
    expected_content: str,
    directional_check: str | None,
    threshold: float,
) -> dict[str, Any] | None:
    """Hosted arm — single-image verify through Zhipu's glm-5.3-flash.

    Direct call to the v4 OpenAI-compatible chat/completions endpoint
    (stdlib urllib, synchronous — image batches here are serial by design
    anyway). Message shape mirrors the historical async_call_llm path:
    one user message with a single image_url data-url + the question from
    ``_build_question()``; parsing reuses ``_parse_vision_response()`` so
    both arms score confidence identically.

    Returns the parsed result dict (WITHOUT engine/cached keys), or None
    on ANY failure (no API key / network error / non-200 / missing
    content / parse failure) so the caller falls through to the next arm.
    Never raises.
    """
    question = _build_question(expected_content, directional_check)
    out = _zhipu_vision_chat(p, question)
    if out is None:
        return None
    text, usage_raw = out
    result = _parse_vision_response(text, expected_content, directional_check, threshold)
    result["usage"] = {
        "input_tokens": _safe_token_count(usage_raw.get("prompt_tokens")),
        "output_tokens": _safe_token_count(usage_raw.get("completion_tokens")),
    }
    return result


def _urllib_request_with_key(url: str, payload: dict, key: str):
    """Build the POST Request for the hosted arm (thin seam — tests can
    patch ``_verify_via_zhipu`` or ``_resolve_zhipu_api_key`` wholesale, but
    the request object itself is inspectable via ``_urlopen`` capture)."""
    return _Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )


def _safe_token_count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# ── Engine adapter registry ────────────────────────────────────────────────

_ENGINE_ARMS: dict[str, str] = {
    "qwen-eye": "_verify_via_qwen_eye",
    "glm-5.3-flash": "_verify_via_zhipu",
}


_ENGINE_BATCH_ARMS: dict[str, str] = {
    "qwen-eye": "_batch_via_qwen_eye",
    "glm-5.3-flash": "_batch_via_zhipu",
}
"""Batch twin of ``_ENGINE_ARMS``: engine name → module-level batch-arm
function NAME (late-bound through ``_resolve_batch_arm`` exactly like the
single-image table). Keys MUST stay in 1:1 correspondence with
``_ENGINE_ARMS``/``_KNOWN_ENGINES`` (a batch-capable entry without a
single-image counterpart would produce verdicts verify_image_content can't
reproduce). Batch-arm contract: ``(image_paths, expected_contents,
directional_checks, indices, threshold, results) -> list[int]`` of still-
unjudged indices — sync OR awaitable (the router awaits when needed)."""
"""Registry-driven dispatch: engine name → module-level arm-function NAME.
Names (not objects) so resolution is LATE-BOUND via ``_resolve_arm`` —
monkeypatching ``vv._verify_via_zhipu`` etc. always takes effect (an
import-time callable table would strand tests on stale references and
risk real network calls slipping past a patch). ``get_engine_order()``
supplies the ORDER; only names present here are dispatched. Adding a
future arm = add its function here + extend ``_KNOWN_ENGINES``. The
observation twin table is ``_OBSERVE_ARMS`` (fixbatch-007) — keys MUST
mirror this table so both layers route the same engine names."""


def _resolve_arm(engine: str):
    """Late-bind an engine name to its arm callable, or None when unknown.

    Arm contract: (p, expected_content, directional_check, threshold) ->
    parsed result dict WITHOUT engine/cached keys, or None on failure.
    An arm MAY also raise ``VisionEngineUnavailable`` for engine-level
    failure (the local arm does, for its precise diagnostics); routers
    treat that identically to a None return — fall through to the next
    configured arm, or fail closed when none remains.
    """
    name = _ENGINE_ARMS.get(engine)
    if name is None:
        return None
    return globals().get(name)


def _resolve_batch_arm(engine: str):
    """Late-bind an engine name to its BATCH arm callable, or None when
    unknown (same late-binding rationale as ``_resolve_arm``)."""
    name = _ENGINE_BATCH_ARMS.get(engine)
    if name is None:
        return None
    return globals().get(name)


async def verify_batch(
    image_paths: list[str],
    expected_contents: list[str],
    directional_checks: list[str | None] | None = None,
    stratum: str | None = None,
    *,
    engine_order: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Batch-verify images (PITFALL I-1 mitigation #1), registry-routed.

    The WHOLE batch runs on ONE arm at a time (judgement-style
    consistency): arms are tried in priority order over the still-unjudged
    images; an arm that fails AT ENGINE LEVEL falls through to the next
    configured arm when one exists, otherwise raises
    ``VisionEngineUnavailable`` (2026-08-18 fail-closed hard gate — the
    default qwen-eye-only order behaves exactly as before). Per-image
    failure (transient call error / empty response / HTTP miss on ONE
    image) is isolated: that image gets ``{"pass": False, "confidence":
    0.0, "engine_error": True}`` and the batch continues — callers
    distinguish engine errors from content fails via the ``engine_error``
    key.

    Both arms verify PER-IMAGE: qwen-eye because the llama.cpp
    multi-image drop constraint forbids batching locally; glm-5.3-flash to
    keep both arms' judgement granularity identical (one question, one
    verdict, one image).

    Args:
        image_paths: list of local image paths.
        expected_contents: parallel list of expected content strings.
        directional_checks: optional parallel list of directional checks.
        stratum: Optional IMG-05 stratum for per-stratum threshold override.
            When provided, the threshold is resolved via ``get_threshold(stratum)``
            and applied to all images in the batch. When None (default), uses
            ``_CONFIDENCE_THRESHOLD`` (0.7) — backward-compatible.
        engine_order: Optional per-call engine order override. Names not in
            ``_KNOWN_ENGINES`` are ignored.

    Returns:
        list of result dicts (one per input image), same shape as
        verify_image_content return (each carries ``engine``; engine-error
        rows additionally carry ``engine_error: True``). Local-engine rows
        report usage 0/0; hosted rows carry real metered token counts.

    Raises:
        VisionEngineUnavailable: an arm failed at engine level AND no
            further known arm remained in the order (or the whole batch
            loop crashed inside a lone arm).

    Cache-hit images report usage 0/0 (no new API call).
    """
    if directional_checks is None:
        directional_checks = [None] * len(image_paths)

    order = list(engine_order or get_engine_order())

    # Check cache for all images first (fixbatch-005: per-(sha, engine)
    # keys — only engines in this call's resolved order are consulted,
    # first engine in order with a fresh entry wins; fixbatch-006: the
    # key carries the per-image judging question too, composed by the
    # SAME three-part _cache_key as the single-image path).
    results: list[dict[str, Any] | None] = [None] * len(image_paths)
    uncached_indices: list[int] = []

    for i, img_path in enumerate(image_paths):
        p = Path(img_path)
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        question = _build_question(expected_contents[i], directional_checks[i])
        for engine in order:
            key = _cache_key(sha, engine, question)
            cached_entry = _cache.get(key)
            if cached_entry is None or "pass" not in cached_entry:
                continue  # wrong-shape entry never serves a verdict (fixbatch-007)
            age = time.time() - cached_entry.get("_ts", 0)
            if age < _CACHE_TTL_SEC:
                r = {k: v for k, v in cached_entry.items() if k != "_ts"}
                r["cached"] = True
                # Cache hit → no new API call → zero tokens.
                r["usage"] = {"input_tokens": 0, "output_tokens": 0}
                results[i] = r
                break
            del _cache[key]  # expired
        if results[i] is None:
            uncached_indices.append(i)

    threshold = get_threshold(stratum)
    pending = list(uncached_indices)

    for pos, engine in enumerate(order):
        if not pending:
            break
        batch_arm = _resolve_batch_arm(engine)
        if batch_arm is None:
            continue  # unknown engine name — ignored
        try:
            out = batch_arm(
                image_paths, expected_contents, directional_checks,
                pending, threshold, results,
            )
            if inspect.isawaitable(out):  # local arm is async, hosted sync
                out = await out
            pending = out
        except VisionEngineUnavailable as exc:
            # Engine-level failure of THIS arm. Registry semantics: fall
            # through to a remaining configured arm; when none remains
            # (the default qwen-eye-only order), re-raise — fail-closed.
            if not any(e in _ENGINE_BATCH_ARMS for e in order[pos + 1:]):
                raise
            logger.warning(
                "vision-verify: %s arm failed at engine level (%s) — "
                "falling through to next configured arm", engine, exc,
            )

    def _miss(i: int) -> dict[str, Any]:
        # Only reachable when engine_order named no known engine — an
        # engineless batch is an engine failure, not a content verdict.
        return {"pass": False, "confidence": 0.0,
                "description": "batch miss (no usable engine in order)",
                "cached": False, "engine": "qwen-eye",
                "engine_error": True,
                "usage": {"input_tokens": 0, "output_tokens": 0}}

    return [r if r is not None else _miss(i) for i, r in enumerate(results)]


async def _batch_via_qwen_eye(
    image_paths: list[str],
    expected_contents: list[str],
    directional_checks: list[str | None],
    indices: list[int],
    threshold: float,
    results: list[dict[str, Any] | None],
) -> list[int]:
    """Judge ``indices`` per-image through qwen-eye (the local arm).

    Returns the indices still un-judged (empty in practice — per-image
    failures become isolated engine_error rows). Engine-level failure
    raises ``VisionEngineUnavailable`` (fail-closed). Per-image failure is
    ISOLATED: the image gets an ``engine_error`` row and the batch
    continues.
    """
    try:
        eye = _new_qwen_eye()
    except Exception as exc:
        raise VisionEngineUnavailable(
            f"qwen-eye construction failed: {exc}"
        ) from exc
    try:
        healthy, _started = eye.ensure_ready()
        if not healthy:
            raise VisionEngineUnavailable(
                f"qwen-eye did not become healthy in "
                f"{QWEN_EYE_START_TIMEOUT_S}s (caller kap:vision_verify, "
                f"batch) — no fallback engine exists, failing closed"
            )
        for i in indices:
            try:
                question = _build_question(
                    expected_contents[i], directional_checks[i],
                )
                text = eye.observe_single(Path(image_paths[i]), question)
                if not text.strip():
                    results[i] = {
                        "pass": False, "confidence": 0.0,
                        "description": "engine error: empty response",
                        "cached": False, "engine": "qwen-eye",
                        "engine_error": True,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    }
                    continue
                r = _parse_vision_response(
                    text, expected_contents[i], directional_checks[i], threshold,
                )
            except Exception as exc:  # noqa: BLE001 — per-image isolation
                logger.warning(
                    "qwen-eye per-image failure at %s (%s) — engine_error row",
                    image_paths[i], exc,
                )
                results[i] = {
                    "pass": False, "confidence": 0.0,
                    "description": f"engine error: {exc}",
                    "cached": False, "engine": "qwen-eye",
                    "engine_error": True,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                }
                continue
            r["engine"] = "qwen-eye"
            r["cached"] = False
            r["usage"] = {"input_tokens": 0, "output_tokens": 0}
            sha = hashlib.sha256(Path(image_paths[i]).read_bytes()).hexdigest()
            _cache[_cache_key(sha, "qwen-eye", question)] = {**r, "_ts": time.time()}
            results[i] = r
        return [i for i in indices if results[i] is None]
    except VisionEngineUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 — normalized to the engine-down type
        raise VisionEngineUnavailable(
            f"qwen-eye batch loop failed: {exc}"
        ) from exc
    finally:
        eye.stop_if_owned()


def _batch_via_zhipu(
    image_paths: list[str],
    expected_contents: list[str],
    directional_checks: list[str | None],
    indices: list[int],
    threshold: float,
    results: list[dict[str, Any] | None],
) -> list[int]:
    """Judge ``indices`` per-image through the hosted glm-5.3-flash arm.

    One HTTP call per image, serial — same judgement granularity as the
    local arm (one question, one verdict, one image). Per-image failure
    (call returned None) is ISOLATED into an ``engine_error`` row so a
    single slow/failed call doesn't sink the batch. Returns the indices
    still un-judged (always [] today — kept for symmetric pending
    plumbing with the local arm). Never raises engine-level errors.
    """
    judged: set[int] = set()
    for i in indices:
        r = _verify_via_zhipu(
            Path(image_paths[i]), expected_contents[i], directional_checks[i],
            threshold,
        )
        if r is None:
            logger.warning(
                "glm-5.3-flash per-image failure at %s — engine_error row",
                image_paths[i],
            )
            results[i] = {
                "pass": False, "confidence": 0.0,
                "description": "engine error: glm-5.3-flash call produced no result",
                "cached": False, "engine": "glm-5.3-flash",
                "engine_error": True,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
            continue
        r["engine"] = "glm-5.3-flash"
        r["cached"] = False
        # Hosted rows carry real metered usage (set by _verify_via_zhipu).
        sha = hashlib.sha256(Path(image_paths[i]).read_bytes()).hexdigest()
        # fixbatch-006: the single-image arm builds the question
        # internally; recompute it here for the cache key (deterministic
        # _build_question → identical text to what was actually sent).
        question = _build_question(expected_contents[i], directional_checks[i])
        _cache[_cache_key(sha, "glm-5.3-flash", question)] = {**r, "_ts": time.time()}
        results[i] = r
        judged.add(i)
    return [i for i in indices if i not in judged]


# ── Question/parse helpers (shared by both arms) ───────────────────────────


def _build_question(expected_content: str, directional: str | None) -> str:
    """Build the Chinese yes/no + confidence question for the vision judge
    (Chinese-native per RESEARCH; qwen-eye handles it identically)."""
    q = (
        f"这张图片是否包含以下内容？请回答是或否并给出置信度(0-1)。"
        f"内容：{expected_content}"
    )
    if directional == "lhd":
        q += "\n另外：方向盘在左侧（左舵LHD）还是右侧（右舵RHD）？"
    return q


def _parse_vision_response(
    text: str,
    expected: str,
    directional: str | None,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Parse the vision judge's response text into a result dict.

    Extracts confidence via regex. Default 0.5 if no match (flags as
    low-confidence). passed = confidence >= effective_threshold.

    Args:
        text: Raw response text from the vision judge (qwen-eye).
        expected: Expected content string (unused in parsing, kept for
            interface stability).
        directional: Optional directional check ("lhd" / "rhd" / None).
        threshold: Optional confidence threshold override. When None,
            uses ``_CONFIDENCE_THRESHOLD`` (0.7) — backward-compatible.
    """
    m = (
        re.search(r"置信度.*?([0-9.]+)", text)
        or re.search(r"confidence.*?([0-9.]+)", text, re.I)
    )
    confidence = float(m.group(1)) if m else 0.5
    # WR-01: the judge occasionally returns percentage forms ("87%", "87/100")
    # despite the prompt asking for 0-1. Values > 1.0 are interpreted as
    # percentages and divided by 100. Values > 1.5 are clamped to 1.0
    # (defensive — avoids an implausible 87.0 from "87%" bypassing the
    # 0.7 threshold as a false-pass).
    if confidence > 1.0:
        if confidence <= 100.0:
            confidence = confidence / 100.0
        else:
            logger.warning(
                "vision confidence out of plausible range: %s — clamping to 1.0",
                confidence,
            )
            confidence = 1.0
    effective_threshold = threshold if threshold is not None else _CONFIDENCE_THRESHOLD
    passed = confidence >= effective_threshold

    # Directional check: LHD must be confirmed.
    if directional == "lhd":
        lhd_match = re.search(r"左舵|LHD|left.?hand", text, re.I)
        passed = passed and bool(lhd_match)

    return {
        "pass": passed,
        "confidence": confidence,
        "description": text[:200] if text else "",
    }
