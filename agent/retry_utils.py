"""Retry utilities — jittered backoff for decorrelated retries.

Replaces fixed exponential backoff with jittered delays to prevent
thundering-herd retry spikes when multiple sessions hit the same
rate-limited provider concurrently.

The ``jittered_backoff_overloaded`` preset is tuned for Zhipu GLM 1305
("该模型当前访问量过大" / "model overloaded_error") recovery windows
observed during the 2026-07-02 10:05-10:25 CST incident: the default
0.5s-base / 32s-cap path exhausted all 10 retries in under 2 minutes,
well short of the provider's actual recovery window. The overloaded
preset uses a 30s floor and 600s cap so retries actually span the
typical 1305 micro-burst instead of churning uselessly.
"""

import random
import threading
import time

# Monotonic counter for jitter seed uniqueness within the same process.
# Protected by a lock to avoid race conditions in concurrent retry paths
# (e.g. multiple gateway sessions retrying simultaneously).
_jitter_counter = 0
_jitter_lock = threading.Lock()


def jittered_backoff(
    attempt: int,
    *,
    base_delay: float = 5.0,
    max_delay: float = 120.0,
    jitter_ratio: float = 0.5,
) -> float:
    """Compute a jittered exponential backoff delay.

    Args:
        attempt: 1-based retry attempt number.
        base_delay: Base delay in seconds for attempt 1.
        max_delay: Maximum delay cap in seconds.
        jitter_ratio: Fraction of computed delay to use as random jitter
            range.  0.5 means jitter is uniform in [0, 0.5 * delay].

    Returns:
        Delay in seconds: min(base * 2^(attempt-1), max_delay) + jitter.

    The jitter decorrelates concurrent retries so multiple sessions
    hitting the same provider don't all retry at the same instant.
    """
    global _jitter_counter
    with _jitter_lock:
        _jitter_counter += 1
        tick = _jitter_counter

    exponent = max(0, attempt - 1)
    if exponent >= 63 or base_delay <= 0:
        delay = max_delay
    else:
        delay = min(base_delay * (2 ** exponent), max_delay)

    # Seed from time + counter for decorrelation even with coarse clocks.
    seed = (time.time_ns() ^ (tick * 0x9E3779B9)) & 0xFFFFFFFF
    rng = random.Random(seed)
    jitter = rng.uniform(0, jitter_ratio * delay)

    return delay + jitter


def jittered_backoff_overloaded(attempt: int) -> float:
    """Backoff preset for provider-overloaded responses (HTTP 503/529, GLM 1305).

    Thin wrapper around :func:`jittered_backoff` with a 30-second floor and
    600-second cap, tuned for Zhipu GLM 1305 recovery windows. The default
    ``jittered_backoff`` path (0.5s/32s) exhausts a 10-retry budget in under
    two minutes — too fast to span a real provider recovery. This preset
    ensures the third retry lands at >= 30s + jitter, giving the upstream
    a real chance to recover before the early-abort counter fires.

    See ``agent/glm_concurrency_guard.py`` and the consecutive-overloaded
    early-abort logic in ``agent/conversation_loop.py`` for the companion
    mitigations shipped in the same commit.
    """
    return jittered_backoff(attempt, base_delay=30.0, max_delay=600.0, jitter_ratio=0.5)
