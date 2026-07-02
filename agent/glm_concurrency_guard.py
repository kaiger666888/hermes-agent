"""Process-wide concurrency guard for Zhipu GLM (*.bigmodel.cn) endpoints.

Throttles in-flight requests to *.bigmodel.cn hosts at a configurable
process-wide cap (default ``N=4``), mitigating the 1305 overloaded_error /
"该模型当前访问量过大" storms observed 2026-07-02 10:05-10:25 CST
(~400 retry failures surfacing as "model provider failed after retries").

Design notes
------------
* **Why threading.Semaphore, not asyncio**: the OpenAI SDK call inside
  ``_perform_api_call`` blocks the calling thread even under the gateway's
  asyncio loop. ThreadPoolExecutor workers (``delegate_task`` subagents)
  and asyncio-thread callers all share this process-wide semaphore. Cross-
  process throttling is out of scope — the existing ``hermes-gateway.service``
  deployment is a single process.
* **Why host-keyed**: Zhipu may route via different *.bigmodel.cn subdomains
  in the future (open., api., alt., …). Keying by parsed hostname means each
  upstream host gets its own throttle without coupling to a hardcoded URL.
* **No-op for non-GLM providers**: ``acquire_glm_slot`` short-circuits
  internally when ``is_glm_endpoint`` returns False, so wrapping the
  ``_perform_api_call`` chokepoint unconditionally adds zero overhead to
  Anthropic / OpenAI / Bedrock / etc. paths.

Configuration precedence (highest first):
    1. ``HERMES_GLM_CONCURRENCY`` env var (operator escape hatch during
       incidents — no config reload needed beyond service restart).
    2. ``glm.global_concurrency`` in ``~/.hermes/config.yaml``.
    3. Default ``4``.

The resolved N is clamped to ``[1, 32]`` to reject absurd operator input
(threat T-GLM-01). N=1 is a valid choice (fully serialize GLM calls); the
guard logs the resolved value on first semaphore creation so operators can
see the throughput impact in ``agent.log``.
"""

from __future__ import annotations

import contextlib
import logging
import os
import threading
from typing import Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Module-level registries. Write-once per host under _LOCK; subsequent
# get_glm_semaphore() calls for the same host return the cached object.
_SEMAPHORES: Dict[str, threading.Semaphore] = {}
_LOCK = threading.Lock()

# Cached resolved N. None until first resolution; after that we hold the
# value for the process lifetime (config hot-reload is OUT OF SCOPE — the
# gateway service restart picks up new values, matching existing semantics).
_RESOLVED_N: Optional[int] = None

# Default cap. Tuned from the 2026-07-02 incident: 4 concurrent in-flight
# requests to open.bigmodel.cn is well under the observed overload threshold
# while still letting typical multi-expert / delegate_task fan-out proceed.
_DEFAULT_GLM_CONCURRENCY = 4

# Clamp bounds. Below 1 would deadlock (semaphore never releasable from 0);
# above 32 defeats the throttle's purpose on a single-process gateway.
_MIN_GLM_CONCURRENCY = 1
_MAX_GLM_CONCURRENCY = 32


def _load_config_for_glm() -> dict:
    """Load ~/.hermes/config.yaml, isolated for testability.

    Wrapped in a helper so tests can monkeypatch this single function
    instead of stubbing the full ``hermes_cli.config.load_config`` path
    (which has side effects on the global config cache).
    """
    # Local import to keep this module dependency-light at import time
    # (hermes_cli.config pulls in a lot of the agent stack transitively).
    from hermes_cli.config import load_config

    try:
        return load_config()  # type: ignore[no-any-return]
    except Exception as exc:  # noqa: BLE001 — best-effort config read.
        logger.warning("GLM guard: could not load config (%s); using default N=%s", exc, _DEFAULT_GLM_CONCURRENCY)
        return {}


def _resolve_glm_n() -> int:
    """Resolve the GLM concurrency cap, with operator escape hatch.

    Precedence: env > config > default. Clamped to [1, 32].
    """
    global _RESOLVED_N
    if _RESOLVED_N is not None:
        return _RESOLVED_N

    raw_env = os.environ.get("HERMES_GLM_CONCURRENCY")
    if raw_env is not None:
        try:
            n = int(raw_env)
        except (TypeError, ValueError):
            logger.warning(
                "GLM guard: HERMES_GLM_CONCURRENCY=%r is not an integer; "
                "falling back to config/default.",
                raw_env,
            )
            n = None
        else:
            _RESOLVED_N = max(_MIN_GLM_CONCURRENCY, min(_MAX_GLM_CONCURRENCY, n))
            return _RESOLVED_N

    # Config path. Local import keeps this module importable without the
    # full hermes_cli stack at module-load time (avoids cycles / heavy I/O
    # on import); cfg_get is a small pure helper.
    from hermes_cli.config import cfg_get

    cfg = _load_config_for_glm()
    cfg_n = cfg_get(cfg, "glm", "global_concurrency", default=None)
    if cfg_n is not None:
        try:
            n = int(cfg_n)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            logger.warning(
                "GLM guard: glm.global_concurrency=%r is not an integer (%s); "
                "falling back to default.",
                cfg_n, exc,
            )
        else:
            _RESOLVED_N = max(_MIN_GLM_CONCURRENCY, min(_MAX_GLM_CONCURRENCY, n))
            return _RESOLVED_N

    _RESOLVED_N = _DEFAULT_GLM_CONCURRENCY
    return _RESOLVED_N


def is_glm_endpoint(base_url: str | None) -> bool:
    """Return True iff ``base_url`` points at a *.bigmodel.cn host.

    Matches ``open.bigmodel.cn``, ``bigmodel.cn``, and any future
    ``*.bigmodel.cn`` subdomain Zhipu may route via. Returns False for
    None/empty and for lookalike hosts (``bigmodel.cn.evil.com``).
    """
    if not base_url:
        return False
    try:
        parsed = urlparse(base_url)
    except (ValueError, TypeError):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    # ``endswith("bigmodel.cn")`` matches both "bigmodel.cn" and
    # "open.bigmodel.cn" but NOT "bigmodel.cn.evil.com" (that hostname
    # ends with ".evil.com", not "bigmodel.cn").
    return hostname == "bigmodel.cn" or hostname.endswith(".bigmodel.cn")


def get_glm_semaphore(base_url: str | None) -> threading.Semaphore | None:
    """Get-or-create the host-keyed semaphore for a GLM endpoint.

    Returns ``None`` for non-GLM endpoints (caller should treat the
    throttle as a no-op). Lazily creates the semaphore on first request
    for a given hostname, logging the resolved N once per host.
    """
    if not is_glm_endpoint(base_url):
        return None
    try:
        hostname = (urlparse(base_url).hostname or "")  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None
    if not hostname:
        return None

    # Fast path: already created.
    sem = _SEMAPHORES.get(hostname)
    if sem is not None:
        return sem

    n = _resolve_glm_n()
    with _LOCK:
        sem = _SEMAPHORES.get(hostname)
        if sem is None:
            sem = threading.Semaphore(n)
            _SEMAPHORES[hostname] = sem
            logger.info(
                "GLM concurrency guard enabled for %s: N=%d",
                hostname, n,
            )
            if n <= 1:
                logger.warning(
                    "GLM guard N=%d for %s — requests to this host will be "
                    "fully serialized. This is valid but may impact throughput.",
                    n, hostname,
                )
    return sem


@contextlib.contextmanager
def acquire_glm_slot(base_url: str | None):
    """Context manager that acquires a GLM concurrency slot, or no-ops.

    For non-GLM endpoints (or None/empty URL) this yields immediately
    with zero overhead — no semaphore lookup, no lock acquisition. This
    is CRITICAL: the wrapper sits on the main API-call chokepoint and
    must not slow down Anthropic/OpenAI/Bedrock/etc. paths.

    For GLM endpoints, acquires the host's semaphore before yield and
    releases it in a ``finally`` block so exceptions propagate the slot
    back to the pool (threat T-GLM-04: semaphore deadlock on exception).
    """
    sem = get_glm_semaphore(base_url)
    if sem is None:
        # Non-GLM passthrough — zero overhead, no semaphore interaction.
        yield
        return

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("GLM guard: acquiring slot for %s", base_url)
    sem.acquire()
    try:
        yield
    finally:
        sem.release()
