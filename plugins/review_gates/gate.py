"""gate.py — HIL Gate lifecycle state machine (Phase 34-01, SC#1).

Pure-stdlib Human-In-The-Loop review gate state machine. Implements the
3 switchable resolution modes mandated by CF-01 / GATE-NATIVE-01:

  * **blocking** — synchronous pause on a ``threading.Event``. The caller
    thread blocks until ``resolve()`` is invoked (same process / another
    thread) or ``timeout_sec`` elapses. Use case: local operator review.
  * **webhook** — non-blocking. ``wait()`` returns immediately with an
    ``awaiting_callback`` sentinel carrying the ``review_id``. The runner
    persists ``awaiting_review`` state and exits; an HMAC-signed callback
    later resumes the gate via ``resolve()``. Use case: production async
    pipelines.
  * **polling** — ``wait()`` raises ``GateError`` directing the caller to
    ``runner_hooks.poll_until_terminal()`` (active pull loop). Use case:
    webhook-delivery fallback and integration tests.

This module is intentionally a *leaf*: it owns only the lifecycle state
machine. HTTP-calling adapters (webhook HMAC verify, polling query loop,
asset-bus write-back, PipelineState awaiting_review write) live in
``runner_hooks.py`` (Plan 34-03) and reuse
``plugins.kais_aigc.review_platform`` from Phase 32. Keeping gate.py pure
stdlib (D-34-01) makes it unit-testable without network mocks and mirrors
the Phase 33 "data layer is stdlib-only" pattern.

CF-05 / GATE-NATIVE-05: ``GateMaxRetriesExceeded`` is raised from
``submit()`` when ``attempt > config.max_retries``. This is terminal (not
transient like ``GateError``) and carries the literal
``CONSISTENCY_BLOCKED:`` prefix so callers / grep / the runner can
identify it. The runner (Phase 35) catches this and marks the episode
failed — this preserves v4.0 PIPE-GUARD-01 semantics (no silent swallow).

D-34-05: sync-only. No ``async def`` anywhere in this module. If the
hermes-agent runtime is async, the Phase 35 runner wraps the sync calls in
``asyncio.to_thread``.
"""

from __future__ import annotations

import enum
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GateMode(str, enum.Enum):
    """Resolution strategy for a Gate instance (CF-01).

    The same lifecycle methods (``submit`` / ``wait`` / ``resolve``) work for
    all three modes; only the ``wait()`` behavior differs.
    """

    BLOCKING = "blocking"
    WEBHOOK = "webhook"
    POLLING = "polling"


class GateStatus(str, enum.Enum):
    """6 lifecycle states for a Gate runtime instance."""

    PENDING = "pending"          # submitted, awaiting resolution
    APPROVED = "approved"        # resolve("approve")
    REJECTED = "rejected"        # resolve("reject")
    CONTESTED = "contested"      # resolve("contest") — needs human attention
    TIMED_OUT = "timed_out"      # blocking wait() exhausted timeout_sec
    FAILED = "failed"            # max_retries exceeded (PIPE-GUARD-01)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GateError(Exception):
    """Transient gate error (invalid decision, wrong mode for wait, etc.).

    Callers may retry or reroute. Distinct from ``GateMaxRetriesExceeded``
    which is terminal.
    """


class GateMaxRetriesExceeded(Exception):
    """Terminal: gate exhausted ``retry_policy.max_retries``.

    Preserves v4.0 PIPE-GUARD-01 CONSISTENCY_BLOCKED semantics — the episode
    is marked failed and the runner must stop. NOT silently swallowed.

    The message always starts with the literal ``"CONSISTENCY_BLOCKED: "`` so
    that callers, log greps, and the Phase 35 runner can identify this
    specific failure mode and route it to the episode-fail path rather than
    the generic-error path.
    """

    def __init__(self, gate_id: str, attempts: int, max_retries: int):
        super().__init__(
            f"CONSISTENCY_BLOCKED: gate '{gate_id}' exhausted retries "
            f"({attempts} > {max_retries})"
        )
        self.gate_id = gate_id
        self.attempts = attempts
        self.max_retries = max_retries


# ---------------------------------------------------------------------------
# Static config (frozen, hashable) — loaded from gates.yaml in Plan 34-02
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateConfig:
    """Static gate definition.

    One instance per gate_id, loaded once from ``gates.yaml`` at
    ``review_gates/__init__.py`` import time (D-34-02: hot-reload NOT
    supported). Frozen for hashability + immutability per D-34-04.

    Required fields mirror ROADMAP SC#2 + CF-02 8-gate table.
    """

    gate_id: str
    phase: str                                       # V8.6 phase after which this gate fires
    asset_bus_slots_to_lock: tuple[str, ...]         # slots frozen for the duration of review
    reviewer_role: str                               # e.g. creative_source, script_auditor, editor
    timeout_sec: int = 3600                          # default 1h; render-gate overrides to 14400
    callback_url: Optional[str] = None               # webhook-mode endpoint; None for blocking
    max_retries: int = 2                             # CF-05: episode fails when attempt > max_retries
    backoff_sec: int = 300                           # retry backoff (runner_hooks enforces)
    default_mode: GateMode = GateMode.BLOCKING       # CF-01 default; render-gate overrides to webhook


# ---------------------------------------------------------------------------
# Mutable runtime gate — carries state across submit/wait/resolve
# ---------------------------------------------------------------------------


@dataclass
class Gate:
    """Runtime gate instance — one per (gate_id, episode_id, submission cycle).

    Mutable: tracks ``attempt`` counter, current ``review_id``, lifecycle
    ``status``, and a private ``threading.Event`` used by blocking-mode
    ``wait()``. The Event is excluded from ``repr`` to keep logs readable.
    """

    config: GateConfig
    episode_id: str
    mode: GateMode
    # Mutable state — defaults represent "freshly constructed, not yet submitted"
    attempt: int = 0
    status: GateStatus = GateStatus.PENDING
    review_id: Optional[str] = None
    submitted_at: Optional[str] = None
    resolved_at: Optional[str] = None
    decision: Optional[str] = None           # "approve" | "reject" | "contest"
    suggested_action: Optional[str] = None   # e.g. "rollback:p02_outline"
    _event: threading.Event = field(default_factory=threading.Event, repr=False)

    # ----------------------- submit -----------------------

    def submit(self, payload: dict, *, review_client: Any = None) -> dict:
        """Submit gate for review. Increments ``attempt``.

        Per CF-05 / GATE-NATIVE-05: when ``attempt`` exceeds
        ``config.max_retries``, sets ``status = FAILED`` and raises
        ``GateMaxRetriesExceeded`` (which carries the
        ``CONSISTENCY_BLOCKED:`` PIPE-GUARD-01 marker). The runner catches
        this and marks the episode failed.

        ``review_client`` is accepted for forward-compat with Plan 34-03's
        ``runner_hooks.pause_for_review`` adapter (which will pass the
        Phase 32 ``ReviewPlatformClient``). gate.py itself does NOT call
        the client — D-34-01 keeps this module pure stdlib. The actual
        ``review_platform.submit_review`` call + ``awaiting_review`` state
        write happens in ``runner_hooks``.

        Args:
            payload: review payload (artifact refs, snapshot). Stored
                opaquely — gate.py does not introspect it.
            review_client: optional Phase 32 review client (ignored by
                gate.py; consumed by the runner_hooks adapter).

        Returns:
            Submission record dict with keys: ``gate_id``, ``episode_id``,
            ``attempt``, ``submitted_at``, ``status``.
        """
        self.attempt += 1
        # CF-05: check BEFORE mutating further — if we're past the limit,
        # the episode is terminal.
        if self.attempt > self.config.max_retries:
            self.status = GateStatus.FAILED
            logger.error(
                "gate '%s' episode '%s' exhausted retries: %d > %d",
                self.config.gate_id, self.episode_id, self.attempt, self.config.max_retries,
            )
            raise GateMaxRetriesExceeded(
                self.config.gate_id, self.attempt, self.config.max_retries
            )
        self.submitted_at = datetime.now(timezone.utc).isoformat()
        self.status = GateStatus.PENDING
        # Clear any stale signal from a previous attempt so a fresh
        # blocking-mode wait() actually blocks.
        self._event.clear()
        logger.info(
            "gate '%s' episode '%s' submitted (attempt %d/%d, mode=%s)",
            self.config.gate_id, self.episode_id,
            self.attempt, self.config.max_retries, self.mode.value,
        )
        return {
            "gate_id": self.config.gate_id,
            "episode_id": self.episode_id,
            "attempt": self.attempt,
            "submitted_at": self.submitted_at,
            "status": self.status.value,
        }

    # ----------------------- wait (mode-dispatched) -----------------------

    def wait(self, timeout_sec: Optional[int] = None) -> dict:
        """Block / return / raise depending on ``self.mode`` (CF-01).

        * **BLOCKING** — ``threading.Event.wait(timeout)``. Returns the
          outcome record (status=APPROVED/REJECTED/CONTESTED on resolve,
          TIMED_OUT on timeout).
        * **WEBHOOK** — non-blocking. Returns immediately with
          ``{"status": "awaiting_callback", "review_id": ...}``. Caller
          persists state and exits; resume happens via a later
          ``resolve()`` call driven by the HMAC callback.
        * **POLLING** — raises ``GateError``. The caller (runner_hooks)
          must use ``poll_until_terminal()`` which calls ``poll_step()``
          in a loop, because polling requires the Phase 32 review client
          (HTTP) which gate.py does not own (D-34-01).

        Args:
            timeout_sec: optional override for ``config.timeout_sec``
                (blocking mode only).

        Returns:
            Outcome record (blocking) or awaiting-callback sentinel
            (webhook). POLLING raises before returning.
        """
        effective_timeout = timeout_sec if timeout_sec is not None else self.config.timeout_sec
        if self.mode == GateMode.BLOCKING:
            # Event.wait returns True if the event was set (resolved), False on timeout.
            resolved = self._event.wait(timeout=effective_timeout)
            if not resolved:
                self.status = GateStatus.TIMED_OUT
                logger.warning(
                    "gate '%s' episode '%s' blocking wait timed out after %ds",
                    self.config.gate_id, self.episode_id, effective_timeout,
                )
            return self._outcome_record()
        elif self.mode == GateMode.WEBHOOK:
            # Non-blocking: caller persists awaiting_review state and exits.
            # Resume path = HMAC callback -> runner_hooks.resume_from_callback
            #   -> gate.resolve(decision, suggested_action).
            return {"status": "awaiting_callback", "review_id": self.review_id}
        elif self.mode == GateMode.POLLING:
            raise GateError(
                "POLLING mode wait requires runner_hooks.poll_until_terminal(); "
                "use Gate.poll_step() in a loop instead."
            )
        else:  # pragma: no cover — exhaustive enum, unreachable
            raise GateError(f"Unknown gate mode: {self.mode!r}")

    # ----------------------- resolve -----------------------

    def resolve(self, decision: str, suggested_action: Optional[str] = None) -> dict:
        """Resolve the gate with a reviewer decision.

        Sets ``status`` to APPROVED / REJECTED / CONTESTED per
        ``decision``, records ``suggested_action`` (e.g.
        ``"rollback:p02_outline"`` — the runner reads this to jump phases),
        stamps ``resolved_at``, and signals the internal Event so any
        blocking-mode waiter wakes.

        Does NOT write to the asset bus — separation of concerns: the state
        machine emits the outcome record; the runner_hooks adapter (or
        tools.py handler in Plan 34-04) writes it to the
        ``review-outcomes`` slot per CF-04.

        Args:
            decision: one of ``"approve"``, ``"reject"``, ``"contest"``.
                Any other value raises ``GateError``.
            suggested_action: optional action hint. For ``"reject"`` this
                is typically a rollback target (``"rollback:pXX_name"``).
                For ``"contest"`` it may carry a human-instruction string.

        Returns:
            Outcome record dict (CF-04 shape minus the
            ``payload_snapshot`` envelope which the bus adapter adds).
        """
        if decision not in {"approve", "reject", "contest"}:
            raise GateError(
                f"Invalid decision: {decision!r} (expected approve/reject/contest)"
            )
        self.decision = decision
        self.suggested_action = suggested_action
        self.resolved_at = datetime.now(timezone.utc).isoformat()
        self.status = {
            "approve": GateStatus.APPROVED,
            "reject": GateStatus.REJECTED,
            "contest": GateStatus.CONTESTED,
        }[decision]
        # Wake any blocking-mode waiter. No-op if nobody is waiting.
        self._event.set()
        logger.info(
            "gate '%s' episode '%s' resolved: decision=%s action=%s status=%s",
            self.config.gate_id, self.episode_id,
            decision, suggested_action, self.status.value,
        )
        return self._outcome_record()

    # ----------------------- outcome record -----------------------

    def _outcome_record(self) -> dict:
        """Return the CF-04 outcome record dict.

        Shape (excluding ``payload_snapshot`` which the asset-bus envelope
        in ``runner_hooks._write_review_outcome`` adds from the original
        submit payload — gate.py does not retain the payload to avoid
        holding large artifact refs in memory across the gate lifetime)::

            {
              "gate_id": str,
              "episode_id": str,
              "decision": str | None,
              "suggested_action": str | None,
              "reviewer_role": str,
              "resolved_at": str | None,
              "attempt": int,
              "status": str,
            }
        """
        return {
            "gate_id": self.config.gate_id,
            "episode_id": self.episode_id,
            "decision": self.decision,
            "suggested_action": self.suggested_action,
            "reviewer_role": self.config.reviewer_role,
            "resolved_at": self.resolved_at,
            "attempt": self.attempt,
            "status": self.status.value,
        }


# ---------------------------------------------------------------------------
# Module-level identity (used by tests as a sentinel that the module loaded)
# ---------------------------------------------------------------------------

_MODULE_PATH = Path(__file__).resolve()

# Re-exported names consumed by Plan 34-03 runner_hooks and Plan 34-04 tools.py.
__all__ = [
    "Gate",
    "GateConfig",
    "GateError",
    "GateMaxRetriesExceeded",
    "GateMode",
    "GateStatus",
]


# Silence unused-import warnings for stdlib modules reserved for future use
# (logging is wired above; time / pathlib are reserved for adapter-driven
# instrumentation that Plan 34-03 may backport into gate.py if a hot-path
# need arises — currently the adapters own those concerns per D-34-01).
_ = (time, _MODULE_PATH)
