"""dreamina_manager.py — production-grade dreamina batch orchestrator.

IMG-01: asyncio.Semaphore(10) concurrency cap + tenacity AsyncRetrying retry.
IMG-02: asyncio.gather block-on-all (sync queue — pipeline_state writes ONLY
        after all tasks resolve, NOT incrementally via as_completed).
IMG-04: 3-attempt RHD/LHD budget with image2image fallback on attempt 3.

Pattern generalization (CONTEXT.md specifics #4):
  The prompt + vision-verify + image2image retry pattern generalizes to
  other dreamina unreliability cases (gender, age, scene type). The
  _escalate_prompt function + _generate_one_with_verify loop is the
  generic scaffold; directional="lhd" is the first instantiation.

Architecture (RESEARCH-verified):

  batch_submit(prompts, output_dir, concurrency=10, deadline_sec=600)
    ├── asyncio.Semaphore(concurrency)  — caps at 10 validated sweet spot
    ├── per-item _generate_one_with_verify:
    │     3-attempt loop (IMG-04 scaffolding):
    │       ├── _escalate_prompt(item, attempt, directional)
    │       ├── tenacity AsyncRetrying:
    │       │     stop_after_attempt(4) + wait_exponential(1,1,8)
    │       │     retry_if_exception_type(Timeout, Connection, subprocess.TimeoutExpired)
    │       │     ├── _dreamina_submit (subprocess text2image --poll=0)
    │       │     ├── _dreamina_poll   (subprocess query_result, gen_status field)
    │       │     └── _download        (httpx.AsyncClient single-conn — NOT aria2c)
    │       └── verify_image_content (lazy import vision_verify)
    └── asyncio.wait_for(asyncio.gather(*tasks), timeout=deadline_sec)

Critical invariants (PATTERNS.md verified):
  1. gen_status field (NOT status) — dreamina query_result JSON schema.
  2. FULL UUID for query_result (NOT 8-char prefix).
  3. httpx download (NOT aria2c — broken data stream on byteimg.com CDN).
  4. subprocess.run([list]) form (NOT shell=True — T-73-01 injection mitigation).
  5. DREAMINA_CLI path hardcoded (NOT user-controllable — T-73-01 tampering).
  6. asyncio.gather (NOT as_completed) — IMG-02 sync-queue block-on-all.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

import httpx
from hermes_constants import get_hermes_home
from ruamel.yaml import YAML
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

DEFAULT_CONCURRENCY = 10  # IMG-01 lock — 10-parallel validated sweet spot
DEFAULT_DEADLINE_SEC = 600  # 10 min for 39-image batch per CONTEXT.md
DREAMINA_CLI = Path.home() / ".local" / "bin" / "dreamina"  # T-73-01 hardcoded path

# Import-guarded prompt standardizer (Phase 4 integration).
# On import failure or runtime error, falls back to raw prompt (hard-fail-safe).
try:
    from plugins.kais_aigc.prompt_standardizer import (
        standardize_prompt as _standardize_prompt,
        DREAMINA_DEFAULT_MAX_LENGTH,
    )
except ImportError:
    _standardize_prompt = None  # type: ignore[assignment]
    DREAMINA_DEFAULT_MAX_LENGTH = 4000


def _standardize_for_cli(prompt: str, mode: str = "text2image") -> str:
    """Standardize prompt before passing to dreamina CLI.

    Hard-fail-safe: on any error returns the raw prompt unchanged.
    Uses DREAMINA_DEFAULT_MAX_LENGTH (4000) so real prompts (≤2500 chars)
    are a no-op — only cleaning + dedup, zero behavior change.
    """
    if _standardize_prompt is None:
        return prompt
    try:
        return _standardize_prompt(
            prompt,
            mode=mode,
            max_length=DREAMINA_DEFAULT_MAX_LENGTH,
        )
    except Exception:
        return prompt

# Phase 82 XCUT-04c-INSTRUMENT: vision-judge pricing defaults
# (approximate; recorded through the glm-4.6v era — ARCHIVED pricing: the
# hosted verify arm moved to glm-5.3-flash via vision_verify, the keys and
# constants stay so historical records keep costing consistently).
# Operator can override via ~/.hermes/config.yaml glm_46v.pricing block.
_DEFAULT_INPUT_USD_PER_1M = 3.0
_DEFAULT_OUTPUT_USD_PER_1M = 8.0

# Process-lifetime pricing cache (avoids re-reading config per call).
_pricing_cache: dict[str, float] | None = None

# WR-05: item_id is used to derive output_path (f"{item_id}.png") and
# flows into --images={ref_image_path} on the dreamina CLI. Reject any
# item_id containing path separators / traversal sequences to prevent
# output_path escaping output_dir or pointing at sensitive files.
_SAFE_ITEM_ID = re.compile(r"^[A-Za-z0-9_\-]+$")


# ── Cost computation (Phase 82 XCUT-04c-INSTRUMENT) ────────────────────────


def _compute_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Compute estimated USD cost for a vision-verify call.

    Reads pricing from ``~/.hermes/config.yaml`` ``glm_46v.pricing`` block
    (``input_usd_per_1m_tokens`` + ``output_usd_per_1m_tokens``). Falls back
    to hardcoded defaults ($3 input / $8 output per 1M tokens — approximate
    glm-4.6v-era archived pricing, operator verifies + updates via config).

    If config has invalid pricing (negative, non-numeric): logs warning +
    uses defaults.

    Uses ``_pricing_cache`` (process-lifetime) to avoid re-reading config
    per call. Uses ``hermes_constants.get_hermes_home()`` for the config
    path (NOT ``Path.home()`` — CLAUDE.md anti-pattern).

    Args:
        input_tokens: Vision judge input token count.
        output_tokens: Vision judge output token count.

    Returns:
        Estimated USD cost as a non-negative float.
    """
    global _pricing_cache

    if _pricing_cache is None:
        _pricing_cache = {}
        try:
            config_path = Path(get_hermes_home()) / "config.yaml"
            if config_path.exists():
                yaml = YAML()
                with config_path.open("r", encoding="utf-8") as f:
                    config = yaml.load(f)
                if config is not None:
                    glm_block = config.get("glm_46v")
                    if glm_block is not None:
                        pricing = glm_block.get("pricing")
                        if pricing is not None:
                            raw_in = pricing.get("input_usd_per_1m_tokens")
                            raw_out = pricing.get("output_usd_per_1m_tokens")
                            if raw_in is not None:
                                val_in = float(raw_in)
                                if val_in >= 0:
                                    _pricing_cache["input"] = val_in
                                else:
                                    logger.warning(
                                        "invalid glm_46v.pricing."
                                        "input_usd_per_1m_tokens (%s) — "
                                        "using default %s",
                                        raw_in, _DEFAULT_INPUT_USD_PER_1M,
                                    )
                            if raw_out is not None:
                                val_out = float(raw_out)
                                if val_out >= 0:
                                    _pricing_cache["output"] = val_out
                                else:
                                    logger.warning(
                                        "invalid glm_46v.pricing."
                                        "output_usd_per_1m_tokens (%s) — "
                                        "using default %s",
                                        raw_out, _DEFAULT_OUTPUT_USD_PER_1M,
                                    )
        except Exception as exc:
            logger.warning(
                "failed to read glm_46v.pricing from config: %s — "
                "using defaults", exc,
            )

    input_rate = _pricing_cache.get("input", _DEFAULT_INPUT_USD_PER_1M)
    output_rate = _pricing_cache.get("output", _DEFAULT_OUTPUT_USD_PER_1M)
    return (input_tokens / 1_000_000 * input_rate) + \
           (output_tokens / 1_000_000 * output_rate)


# ── Result type ────────────────────────────────────────────────────────────


class DreaminaTaskResult(TypedDict):
    """Per-task result returned by batch_submit.

    status:
      "ok" — generated + (optionally) vision-verified pass
      "failed" — exhausted retries or unrecoverable error
      "degraded" — generated but vision-verify low-confidence (operator review)
    """

    submit_id: str
    # FIX-4 (2026-09-03): "5.0->4.6" when the i2i deadlock rescue fired,
    # "" otherwise.
    model_fallback: str
    status: str  # "ok" | "failed" | "degraded"
    image_path: str | None
    latency_ms: int
    retries: int
    vision_verified: bool
    vision_confidence: float | None
    error: str | None
    # Phase 82 XCUT-04c-INSTRUMENT: token spend + cost tracking.
    usage: dict[str, int]
    estimated_cost_usd: float


# ── Public API ─────────────────────────────────────────────────────────────


async def batch_submit(
    prompts: list[dict[str, str]],
    output_dir: str,
    *,
    concurrency: int = DEFAULT_CONCURRENCY,
    deadline_sec: int = DEFAULT_DEADLINE_SEC,
    ratio: str = "16:9",
    model_version: str = "5.0",
) -> list[DreaminaTaskResult]:
    """Submit a batch of dreamina image generation tasks.

    IMG-01: caps concurrency at ``concurrency`` via asyncio.Semaphore.
    IMG-02: returns ONLY after ALL tasks resolve (sync queue semantic).

    Args:
        prompts: list of item dicts. Each item MUST have "id" and "prompt";
            MAY have "expected" (vision-verify content) and "directional"
            ("lhd" / "rhd" / None).
        output_dir: directory for generated .png files.
        concurrency: max parallel tasks (default 10).
        deadline_sec: overall batch timeout (default 600s).
        ratio: aspect ratio for dreamina (default "16:9").
        model_version: dreamina model version (default "5.0").

    Returns:
        list of DreaminaTaskResult, one per input item. Pipeline state
        write should happen AFTER this returns (IMG-02).
    """
    sem = asyncio.Semaphore(concurrency)

    async def _one(item: dict[str, Any]) -> DreaminaTaskResult:
        async with sem:
            return await _generate_one_with_verify(
                item, output_dir, ratio, model_version
            )

    # IMG-02: asyncio.gather blocks until ALL resolve (NOT as_completed).
    results = await asyncio.wait_for(
        asyncio.gather(*[_one(item) for item in prompts]),
        timeout=deadline_sec,
    )

    # IMG-05 metrics: write one record per task to the JSONL ring buffer.
    # Lazy import to avoid pulling pydantic/rich at module-import time
    # (dreamina_stats pulls in rich.Console for the CLI path).
    try:
        from plugins.kais_aigc.dreamina_stats import _metrics_file, record_metric
        mf = _metrics_file()
        for item, result in zip(prompts, results):
            stratum = _infer_stratum(item)
            try:
                record_metric(mf, {
                    "submit_id": result.get("submit_id") or "unknown",
                    "stratum": stratum,
                    "latency_ms": result.get("latency_ms", 0),
                    "success": result.get("status") == "ok",
                    "retries": result.get("retries", 0),
                    "vision_verified": result.get("vision_verified", False),
                    "vision_confidence": result.get("vision_confidence"),
                    "ts": datetime.now(timezone.utc).isoformat(),
                    # Phase 82 XCUT-04c-INSTRUMENT: token spend + cost.
                    "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": result.get("usage", {}).get("output_tokens", 0),
                    "estimated_cost_usd": result.get("estimated_cost_usd", 0.0),
                })
            except Exception as exc:
                logger.warning(
                    "dreamina metric write failed for %s: %s",
                    item.get("id", "unknown"), exc,
                )
    except Exception as exc:
        logger.warning(
            "dreamina metrics pipeline unavailable: %s", exc,
        )

    return list(results)


def _infer_stratum(item: dict[str, Any]) -> str:
    """Infer the IMG-05 stratum from an item dict.

    Maps the item's reference-count / directional hint to one of the
    strata defined in DreaminaTaskMetrics ("1-ref" | "3-ref" |
    "5-ref" | "text2image"). Defaults to "text2image" when no
    reference-image signal is present.
    """
    # Explicit ref_count wins if the caller provides it.
    ref_count = item.get("ref_count")
    if isinstance(ref_count, int):
        if ref_count >= 5:
            return "5-ref"
        if ref_count >= 3:
            return "3-ref"
        if ref_count >= 1:
            return "1-ref"
        return "text2image"
    # Fall back to structural signals: lhd_reference_path implies a
    # single reference image (1-ref).
    if item.get("lhd_reference_path") or item.get("directional"):
        return "1-ref"
    return "text2image"


# ── Per-item pipeline ──────────────────────────────────────────────────────


async def _generate_one_with_verify(
    item: dict[str, Any],
    output_dir: str,
    ratio: str,
    model_version: str,
) -> DreaminaTaskResult:
    """Single-image pipeline: submit → poll → download → vision-verify.

    IMG-04 scaffolding: 3-attempt loop with prompt escalation. Full
    image2image fallback lands in Plan 73-02.
    """
    # Lazy import to avoid circular dependency (vision_verify imports
    # from agent.auxiliary_client which is heavy).
    from plugins.kais_aigc.vision_verify import (
        VisionEngineUnavailable,
        verify_image_content,
    )

    start = time.monotonic()
    item_id = item.get("id", "unknown")
    # WR-05: sanitize item_id at the trust boundary. item_id derives
    # output_path and flows into ref_image_path on the dreamina CLI;
    # reject any value containing path separators / traversal sequences.
    if not _SAFE_ITEM_ID.match(str(item_id)):
        raise ValueError(
            f"unsafe item_id rejected (must match {_SAFE_ITEM_ID.pattern}): "
            f"{item_id!r}"
        )
    output_path = str(Path(output_dir) / f"{item_id}.png")
    expected = item.get("expected", "")
    directional = item.get("directional")  # "lhd" | "rhd" | None
    base_prompt = item["prompt"]

    sid = ""
    last_error = ""
    # FIX-4 (2026-09-03): set to "5.0->4.6" when the i2i deadlock rescue
    # downgrades the model; surfaced on the result for provenance.
    model_fallback = ""
    vr: dict[str, Any] | None = None
    # CR-01: accumulate vision-judge token usage across ALL vision-verify
    # attempts. Previously only the LAST attempt's usage was captured,
    # undercounting cost by ~67% for 3-attempt items. Each attempt that
    # invokes vision-verify adds its tokens here; return paths use the
    # cumulative total.
    total_input_tokens = 0
    total_output_tokens = 0

    for attempt in range(3):  # IMG-04 RHD/LHD 3-attempt budget
        prompt = _escalate_prompt(base_prompt, attempt, directional)
        try:
            async for attempt_info in AsyncRetrying(
                stop=stop_after_attempt(4),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                # RuntimeError included for the 2026-09-03 i2i deadlock
                # signal raised by _dreamina_poll (drives fast fallback).
                retry=retry_if_exception_type(
                    (TimeoutError, ConnectionError, subprocess.TimeoutExpired,
                     RuntimeError)
                ),
            ):
                with attempt_info:
                    # IMG-04: attempt 2 (None from _escalate_prompt) →
                    # image2image fallback from confirmed LHD reference.
                    if prompt is None:
                        ref_path = item.get("lhd_reference_path", "")
                        if not ref_path:
                            raise RuntimeError(
                                "image2image fallback requires lhd_reference_path"
                            )
                        sid = await _dreamina_image2image(
                            ref_path, base_prompt, ratio, model_version
                        )
                    else:
                        sid = await _dreamina_submit(
                            prompt, ratio, model_version
                        )
                    try:
                        raw = await _dreamina_poll(sid)
                    except RuntimeError as exc:
                        # FIX-4 (2026-09-03 probe matrix): 5.x i2i server-side
                        # deadlock — retry ONCE with model 4.6 (4.6 immune).
                        # No prompt escalation: the deadlock is not prompt-
                        # length driven. A second deadlock (4.6) takes the
                        # normal failure path.
                        if ("dreamina deadlock" not in str(exc)
                                or prompt is not None
                                or not str(model_version).startswith("5")):
                            raise
                        logger.warning(
                            "dreamina %s: 5.x i2i deadlock — retrying once "
                            "with model 4.6", item_id,
                        )
                        model_fallback = "5.0->4.6"
                        sid = await _dreamina_image2image(
                            ref_path, base_prompt, ratio, "4.6"
                        )
                        raw = await _dreamina_poll(sid)
                    if raw is None:
                        raise RuntimeError("dreamina poll returned None")
                    url = _extract_image_url(raw)
                    if not url:
                        raise RuntimeError("no image_url in dreamina response")
                    await _download(url, output_path)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 2:
                logger.warning(
                    "dreamina %s attempt %d failed: %s — retrying",
                    item_id, attempt + 1, last_error,
                )
                continue
            return {
                "submit_id": sid,
                "model_fallback": model_fallback,
                "status": "failed",
                "image_path": None,
                "latency_ms": int((time.monotonic() - start) * 1000),
                "retries": attempt,
                "vision_verified": False,
                "vision_confidence": None,
                "error": last_error,
                # Phase 82: failed before vision-verify → zero usage/cost.
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "estimated_cost_usd": 0.0,
            }

        # Vision-verify gate (IMG-03).
        if expected:
            try:
                vr = await verify_image_content(
                    output_path,
                    expected,
                    directional_check=directional,
                    stratum=_infer_stratum(item),
                )
            except VisionEngineUnavailable:
                # 2026-08-18 no-degrade policy: qwen-eye is the ONLY vision
                # judge. Engine down = fail-closed — a prompt-escalation
                # retry cannot revive a dead engine, so DON'T burn attempts;
                # mark the item failed so the caller (KMC phase) converts
                # this into an engine_unavailable rejection.
                logger.error(
                    "dreamina %s: vision engine unavailable (qwen-eye down) "
                    "— failing item without retry (no fallback engine)",
                    item_id,
                )
                return {
                    "submit_id": sid,
                    "model_fallback": model_fallback,
                    "status": "failed",
                    "image_path": output_path,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "retries": attempt,
                    "vision_verified": False,
                    "vision_confidence": None,
                    "error": "vision engine unavailable (qwen-eye down, "
                             "no fallback) — fail-closed",
                    "engine_error": True,
                    "usage": {"input_tokens": total_input_tokens,
                              "output_tokens": total_output_tokens},
                    "estimated_cost_usd": _compute_cost_usd(
                        total_input_tokens, total_output_tokens,
                    ),
                }
            except Exception as exc:
                logger.warning(
                    "vision-verify %s failed: %s — treating as not-verified",
                    item_id, exc,
                )
                # WR-02: include usage key for shape consistency with
                # successful verify_image_content returns. Exception path
                # consumed no engine tokens → zero usage + zero cost.
                vr = {
                    "pass": False,
                    "confidence": 0.0,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                }

            # Phase 82 XCUT-04c-INSTRUMENT: extract usage from vision_verify.
            attempt_usage = (vr or {}).get(
                "usage", {"input_tokens": 0, "output_tokens": 0}
            )
            # CR-01: accumulate this attempt's tokens into the running total.
            total_input_tokens += attempt_usage.get("input_tokens", 0)
            total_output_tokens += attempt_usage.get("output_tokens", 0)
            cumulative_usage = {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
            }
            cumulative_cost = _compute_cost_usd(
                total_input_tokens, total_output_tokens
            )

            if vr.get("pass"):
                return {
                    "submit_id": sid,
                    "model_fallback": model_fallback,
                    "status": "ok",
                    "image_path": output_path,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "retries": attempt,
                    "vision_verified": True,
                    "vision_confidence": vr.get("confidence"),
                    "error": None,
                    "usage": cumulative_usage,
                    "estimated_cost_usd": cumulative_cost,
                }
            # Low-confidence: retry with escalated prompt (if budget allows).
            if attempt < 2:
                logger.info(
                    "dreamina %s vision-verify low-confidence (%.2f) — "
                    "retrying with escalated prompt",
                    item_id, vr.get("confidence", 0.0),
                )
                continue
        else:
            # No expected content → skip vision-verify, return ok.
            return {
                "submit_id": sid,
                "model_fallback": model_fallback,
                "status": "ok",
                "image_path": output_path,
                "latency_ms": int((time.monotonic() - start) * 1000),
                "retries": attempt,
                "vision_verified": False,
                "vision_confidence": None,
                "error": None,
                # Phase 82: no vision-verify → zero usage/cost.
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "estimated_cost_usd": 0.0,
            }

    # Attempt 3 exhausted: degraded (Plan 73-02 adds image2image fallback).
    # CR-01: use accumulated usage across ALL attempts (total_input_tokens
    # and total_output_tokens already include attempt 2's contribution from
    # the loop body above).
    final_usage = {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }
    final_cost = _compute_cost_usd(
        total_input_tokens, total_output_tokens,
    )
    return {
        "submit_id": sid,
        "model_fallback": model_fallback,
        "status": "degraded",
        "image_path": output_path,
        "latency_ms": int((time.monotonic() - start) * 1000),
        "retries": 3,
        "vision_verified": vr is not None,
        "vision_confidence": vr.get("confidence") if vr else None,
        "error": "vision-verify failed 3 attempts",
        "usage": final_usage,
        "estimated_cost_usd": final_cost,
    }


# ── Dreamina CLI subprocess wrappers ───────────────────────────────────────


async def _dreamina_submit(
    prompt: str,
    ratio: str,
    model_version: str,
) -> str:
    """Submit text2image non-blocking (--poll=0). Returns submit_id.

    T-73-01: subprocess.run([list]) form — NOT shell=True.
    """
    prompt = _standardize_for_cli(prompt, "text2image")
    cmd = [
        str(DREAMINA_CLI),
        "text2image",
        f"--prompt={prompt}",
        f"--ratio={ratio}",
        f"--model_version={model_version}",
        "--resolution_type=2k",
        "--poll=0",
    ]
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            timeout=15,
        ),
    )
    try:
        data = json.loads(result.stdout or "")
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(
            f"dreamina submit returned invalid JSON: {exc}"
        ) from exc
    sid = data.get("submit_id", "")
    if not sid:
        raise RuntimeError("dreamina submit returned empty submit_id")
    return str(sid)


async def _dreamina_poll(submit_id: str, max_wait: int = 180) -> dict | None:
    """Poll query_result until success/failed or timeout.

    NOTE: submit_id must be FULL UUID (NOT 8-char prefix).
    NOTE: response uses gen_status field (NOT status).
    """
    cmd = [
        str(DREAMINA_CLI),
        "query_result",
        f"--submit_id={submit_id}",
    ]
    loop = asyncio.get_event_loop()
    start = time.monotonic()
    while time.monotonic() - start < max_wait:
        await asyncio.sleep(5)
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                timeout=15,
            ),
        )
        try:
            data = json.loads(result.stdout or "")
        except (json.JSONDecodeError, TypeError):
            continue
        status = data.get("gen_status", "unknown")
        if status == "success":
            return data
        if status in ("failed", "error", "fail"):
            return None
        # Deadlock detection (2026-09-03 probe matrix: 5.0 i2i server-side
        # bug — queue finishes but result_json never returns). Raise so the
        # tenacity retry can fall back to a working arm fast.
        queue_status = (data.get("queue_info") or {}).get("queue_status", "")
        has_result = bool(data.get("result_json"))
        if queue_status == "Finish" and not has_result:
            raise RuntimeError(
                f"dreamina deadlock: queue=Finish without result_json "
                f"(submit={submit_id[:8]})"
            )
    return None


def _extract_image_url(data: dict) -> str | None:
    """Extract the first image URL from dreamina query_result response."""
    images = data.get("result_json", {}).get("images", [])
    if not images:
        return None
    url = images[0].get("image_url", "")
    # T-73-02: basic scheme check (partial SSRF mitigation).
    #
    # WR-04 limitation: this check ONLY validates the URL scheme
    # (http/https). It does NOT enforce a host allowlist and does NOT
    # block private/loopback/link-local hosts. A malicious or buggy
    # dreamina response returning an internal-IP URL (AWS IMDS, Redis
    # on localhost, etc.) would pass this check and be fetched by
    # _download via httpx. Deliberate decision: the dreamina system is
    # trusted and returns byteimg.com CDN URLs in practice, and the
    # byteimg.com CDN has many regional host variants (p3-byteimg.com,
    # p6-byteimg.com, p9-byteimg.com, ...) that make an exhaustive
    # allowlist brittle. Full SSRF defense-in-depth (host allowlist /
    # ipaddress-based loopback filtering) is a future hardening task
    # if dreamina is ever run against an untrusted response source.
    if url and not (url.startswith("http://") or url.startswith("https://")):
        logger.warning("dreamina image_url not HTTP(S): %s", url[:80])
        return None
    return url or None


# ── Download (httpx, NOT aria2c) ───────────────────────────────────────────


async def _download(url: str, output_path: str) -> None:
    """Download dreamina-generated image via httpx single-connection.

    NOT aria2c — multi-connection produces broken data stream on
    byteimg.com CDN (SKILL.md pitfall).
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(resp.content)


# ── IMG-04 prompt escalation (3-attempt budget with image2image fallback) ──


def _escalate_prompt(
    base_prompt: str,
    attempt: int,
    directional: str | None,
) -> str | None:
    """Escalate prompt intensity per RHD/LHD 3-attempt budget (IMG-04).

    Returns None on attempt 2 to signal image2image fallback (NOT a
    text2image prompt). The caller checks for None and switches to
    _dreamina_image2image with a confirmed LHD reference image.

    attempt 0: base prompt with mild LHD emphasis
    attempt 1: stronger LHD emphasis + negative RHD prompt
    attempt 2: None (signals image2image fallback)
    """
    if attempt == 0:
        if directional == "lhd":
            return (
                f"{base_prompt} "
                "left-hand drive car, steering wheel on the left, "
                "driver sits on the left side"
            )
        return base_prompt
    if attempt == 1:
        if directional == "lhd":
            return (
                f"{base_prompt} "
                "left-hand drive car, steering wheel on the left, "
                "driver sits on the left side, "
                "强调：左舵LHD，方向盘在左侧。"
                "NOT right-hand drive, NOT RHD, "
                "steering wheel is NOT on the right"
            )
        return f"{base_prompt} (stronger emphasis)"
    # attempt 2: signal image2image fallback.
    return None


async def _dreamina_image2image(
    ref_image_path: str,
    prompt: str,
    ratio: str,
    model_version: str,
) -> str:
    """Submit image2image (1-10 ref images). Returns submit_id.

    Per RESEARCH dreamina CLI image2image supports 1-10 images via
    --images comma-separated paths. Resolution type is 2k (image2image
    does NOT support 1k per RESEARCH).

    T-73-05: subprocess.run([list]) form — hardcoded escalation strings,
    NOT user input (no shell injection surface).
    """
    fallback_prompt = f"match the layout of the reference image: {prompt}"
    fallback_prompt = _standardize_for_cli(fallback_prompt, "image2image")
    cmd = [
        str(DREAMINA_CLI),
        "image2image",
        f"--images={ref_image_path}",
        f"--prompt={fallback_prompt}",
        f"--ratio={ratio}",
        f"--model_version={model_version}",
        "--resolution_type=2k",
        "--poll=0",
    ]
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            timeout=30,
        ),
    )
    try:
        data = json.loads(result.stdout or "")
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(
            f"dreamina image2image returned invalid JSON: {exc}"
        ) from exc
    sid = data.get("submit_id", "")
    if not sid:
        raise RuntimeError("dreamina image2image returned empty submit_id")
    return str(sid)
