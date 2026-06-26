"""runner_hooks.py — Phase 35 runner ↔ Phase 34 gate framework adapter.

Phase 34-03 (SC#3 / SC#4 / SC#5; CF-03 / CF-04 / CF-05). Three entry points
the Phase 35 orchestration runner calls plus one helper for PIPE-GUARD-01
episode-fail semantics:

* ``pause_for_review(gate_id, episode_id, payload, *, mode=None)`` — submit the
  gate to the review platform AND write ``awaiting_review`` to
  ``.pipeline-state.json``. Raises ``GateMaxRetriesExceeded`` on retry
  exhaustion (caller catches → ``mark_episode_failed``).
* ``resume_from_callback(body, signature, timestamp)`` — HMAC-verify an inbound
  review-platform callback (via Phase 32 ``ReviewPlatformClient.verify_callback``),
  resolve the matching pending gate, write the outcome to the asset bus
  ``review-outcomes`` slot (Phase 33 AssetBus, CF-04 schema), advance
  PipelineState, and surface a ``rollback_to`` target on reject.
* ``poll_until_terminal(gate_id, timeout_sec, *, interval_sec=30)`` — active
  query loop for polling-mode gates.
* ``mark_episode_failed(episode_id, gate_id, exc)`` — write ``status=failed``
  + the PIPE-GUARD-01 consistency-blocked marker (carried by the exception)
  to state.

Phase 40 Plan 02 added two new functions for the redline auto-detect path
(GATE-04 additive — the 8 V8.6 gates keep their HIL ``pause_for_review``
path with zero behavior change):

* ``is_redline_gate(gate_id)`` — True iff ``gate_id`` starts with ``redline_``.
* ``auto_detect_and_resolve(gate_id, episode_id, payload)`` — look up the
  Plan-01 detector in ``DETECTOR_REGISTRY``, run it on the payload, and call
  ``Gate.resolve()`` with the detector's verdict. Bypasses the manual HIL
  ``gate_resolve`` path: redline violations are structural / deterministic,
  so no human judgment is needed. Unknown ``redline_X`` gate_ids without a
  DETECTOR_REGISTRY entry raise ``KeyError`` (T-40-05 mitigation — never
  silent auto-approve).

Scope: adapters ONLY. The gate state machine lives in ``gate.py`` (Plan 34-01);
YAML config in ``gate_config.py`` (Plan 34-02). This module imports from both
plus reuses Phase 32 ``ReviewPlatformClient`` and Phase 33 ``PipelineStateStore``
+ ``AssetBus``. It does NOT reimplement any of those.

D-34-05: sync API throughout — no ``async`` syntax. Phase 35's async runner
wraps these calls in ``asyncio.to_thread`` if needed.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from plugins.kais_aigc.review_platform import ReviewPlatformClient
from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.store import PipelineStateStore
from plugins.review_gates.gate import (
    Gate,
    GateConfig,
    GateError,
    GateMaxRetriesExceeded,
    GateMode,
    GateStatus,
)
from plugins.review_gates.gate_config import to_gate_config

logger = logging.getLogger(__name__)


# ────────────────── Module-level factory helpers ──────────────────
# Mirrors the Phase 33-04 ``_state_store()`` / ``_asset_bus()`` pattern:
# factory helpers consult ``os.getcwd()`` so tests can redirect writes via
# ``monkeypatch.chdir(tmp_path)``. The review-client factory is also
# monkeypatched (``setattr(runner_hooks, "_review_client", lambda: fake)``)
# to inject a ``MagicMock`` for unit tests.


def _review_client() -> ReviewPlatformClient:
    """Construct or return a ReviewPlatformClient (Phase 32).

    Tests ``monkeypatch.setattr`` this to inject a ``MagicMock`` whose
    ``submit_review`` / ``verify_callback`` / ``query_review_status`` methods
    are pre-stubbed. The default construction reads env vars for JWT + HMAC
    secrets (Phase 32 CF-03 / CF-04).
    """
    return ReviewPlatformClient()


def _asset_bus(workdir: str | None = None) -> AssetBus:
    """Return an AssetBus rooted at ``workdir`` or ``os.getcwd()``."""
    return AssetBus(workdir or os.getcwd())


def _state_store(workdir: str | None = None) -> PipelineStateStore:
    """Return a PipelineStateStore rooted at ``workdir`` or ``os.getcwd()``."""
    return PipelineStateStore(workdir or os.getcwd())


# Module-level cache of gates awaiting callback resolution.
#
# Per Plan 34-03 item 5: for Phase 34 scope, a single in-memory dict is the
# adapter shim. Phase 35's runner will manage persistence properly (rebuild
# the Gate from PipelineState on resume). The cache key is ``gate_id`` — this
# means one in-flight gate per gate_id per process, which matches the V8.6
# serial-gate-per-phase model.
_PENDING_GATES: dict[str, Gate] = {}


# Phase 37 — optional gate resolution hook. None by default (Phase 34
# tests unchanged). Set via ``set_gate_resolved_hook()`` by the canvas sync
# subscriber (or any other gate-resolution observer). Invoked AFTER the
# ``review-outcomes`` slot is written in ``resume_from_callback`` /
# ``resolve_direct`` (D-37-07) so subscribers observe the formal outcome
# already persisted on the asset bus.
_on_gate_resolved: Callable[[str, str, str, dict], None] | None = None


def set_gate_resolved_hook(fn: Callable[[str, str, str, dict], None] | None) -> None:
    """Register (or clear with ``None``) a callback invoked after each gate
    resolution. Signature: ``(episode_id, gate_id, decision, outcome_payload)``.

    The ``outcome_payload`` is the dict written to the ``review-outcomes``
    slot — includes ``decision``, ``gate_id``, ``suggested_action``,
    ``reviewer``, etc. (plus ``rollback_to`` on reject).

    The callback is invoked from a ``try/except`` guard in
    ``resume_from_callback`` / ``resolve_direct`` (D-37-04) — subscriber
    exceptions are logged at WARNING and swallowed; the resume flow always
    returns its normal payload.
    """
    global _on_gate_resolved
    _on_gate_resolved = fn


# ────────────────── Helpers ──────────────────


def _now_iso() -> str:
    """UTC ISO-8601 timestamp (matches gate.py / store.py convention)."""
    return datetime.now(timezone.utc).isoformat()


def _build_gate(
    gate_id: str, episode_id: str, mode: Optional[GateMode] = None
) -> Gate:
    """Look up GateConfig via ``to_gate_config`` + construct a Gate instance.

    Pulled into a helper so ``pause_for_review`` and ``poll_until_terminal``
    share the same construction path. ``mode=None`` falls back to the config's
    ``default_mode`` (Plan 34-02).
    """
    config = to_gate_config(gate_id)
    return Gate(
        config=config,
        episode_id=episode_id,
        mode=mode or config.default_mode,
    )


def _write_awaiting_review_state(
    episode_id: str, phase: str, review_id: Optional[str], gate: Gate
) -> None:
    """Mark ``PipelineState.phases[phase]`` as ``awaiting_review``.

    Mirrors Node.js ``pipeline.js:295-379`` awaiting_review write. The Phase 35
    runner reads this status, emits its ``onProgress('awaiting_review')`` event,
    and exits the phase cleanly (a controlled pause, not a crash).
    """
    store = _state_store()
    state = store.load()
    if not state.episode:
        state.episode = episode_id
    state.phases[phase] = {
        "status": "awaiting_review",
        "review_id": review_id,
        "submitted_at": gate.submitted_at,
        "attempt": gate.attempt,
    }
    state.current_phase_id = phase
    store.save(state)


def _write_review_outcome(gate: Gate, outcome: dict) -> None:
    """Append the outcome to the asset bus ``review-outcomes`` slot (CF-04).

    Reads the current slot (or seeds ``{"outcomes": [], "version": 1}`` when
    absent), appends the new outcome record, and atomically writes it back via
    Phase 33's AssetBus. Idempotent at the slot level: two appends produce two
    outcomes (verified by ``TestWriteReviewOutcome.test_appends_to_existing``).
    """
    bus = _asset_bus()
    current = bus.read("review-outcomes") or {"outcomes": [], "version": 1}
    # Defensive: never trust on-disk shape — preserve a valid envelope.
    if "outcomes" not in current or not isinstance(current["outcomes"], list):
        current["outcomes"] = []
    if "version" not in current:
        current["version"] = 1
    current["outcomes"].append(outcome)
    bus.write("review-outcomes", current, envelope=True)


def _advance_state_after_resolution(
    phase: str, decision: str, gate: Gate
) -> None:
    """Update PipelineState after a gate resolves.

    approve  → ``status="approved"`` (Phase 35 runner advances).
    reject   → ``status="rejected"`` (Phase 35 runner jumps back, using the
               rollback_to hint returned from ``resume_from_callback``).
    contest  → ``status="contested"`` (terminal — human operator intervention).
    """
    store = _state_store()
    state = store.load()
    state.phases[phase] = {
        "status": {
            "approve": "approved",
            "reject": "rejected",
            "contest": "contested",
        }[decision],
        "resolved_at": gate.resolved_at,
        "decision": decision,
        "attempt": gate.attempt,
    }
    store.save(state)


# ────────────────── Public entry points ──────────────────


def pause_for_review(
    gate_id: str,
    episode_id: str,
    payload: dict,
    *,
    mode: Optional[GateMode] = None,
) -> dict:
    """Submit a gate to the review platform + write ``awaiting_review`` state.

    Sequence (Plan 34-03 Task 2 item 4):

    1. Build the Gate from ``to_gate_config`` + caller-supplied ``mode``.
    2. Call ``gate.submit(payload)`` — increments ``attempt``; raises
       ``GateMaxRetriesExceeded`` when ``attempt > config.max_retries``. The
       exception is NOT caught here (PIPE-GUARD-01 anti-pattern).
    3. Call ``ReviewPlatformClient.submit_review(...)`` with ``content_ref``
       of the form ``"<episode_id>/<phase>"`` and the config's ``callback_url``.
    4. If the platform returns a degrade envelope (``{"degraded": True, ...}``)
       auto-resolve the gate as "approve" (mirrors Phase 32 DEGRADED_AUTO).
       Otherwise persist the platform-issued ``review_id`` on the gate.
    5. Write ``PipelineState.phases[phase].status = "awaiting_review"``.
    6. Register the gate in ``_PENDING_GATES`` so a later webhook callback can
       resolve it in-process (Phase 35 runner rebuilds from state on resume).
    7. Return ``{gate_id, episode_id, review_id, status, attempt}``.

    Raises:
        GateMaxRetriesExceeded: when ``attempt > config.max_retries``.
            Callers (Phase 35 runner) catch this and invoke
            ``mark_episode_failed`` to preserve v4.0 PIPE-GUARD-01 semantics.
    """
    gate = _build_gate(gate_id, episode_id, mode)
    submission = gate.submit(payload)  # may raise GateMaxRetriesExceeded

    # Phase 32 client call. content_ref shape mirrors Node.js pipeline.js:323.
    result = _review_client().submit_review(
        type=gate_id,
        content_ref=f"{episode_id}/{gate.config.phase}",
        callback_url=gate.config.callback_url,
    )

    if isinstance(result, dict) and result.get("degraded"):
        # DEGRADED_AUTO → auto-approve (Phase 32 disposition). Pipeline
        # auto-advances rather than blocking on an unavailable review service.
        gate.resolve("approve")
    else:
        gate.review_id = (result or {}).get("review_id")

    # Write awaiting_review to PipelineState (CF-03 controlled-pause contract).
    _write_awaiting_review_state(episode_id, gate.config.phase, gate.review_id, gate)

    # Cache for in-process webhook resume (Plan 34-03 item 5 shim).
    _PENDING_GATES[gate_id] = gate

    return {
        "gate_id": gate_id,
        "episode_id": episode_id,
        "review_id": gate.review_id,
        "status": gate.status.value,
        "attempt": gate.attempt,
        "submitted_at": submission.get("submitted_at"),
    }


def resume_from_callback(body: str, signature: str, timestamp: int) -> dict:
    """Verify an HMAC callback → resolve the pending gate → write outcome.

    Sequence (Plan 34-03 Task 2 item 5):

    1. ``ReviewPlatformClient.verify_callback(body, signature, timestamp)``
       (Phase 32 — 5-min timestamp window + constant-time HMAC compare).
       Returns False → ``PermissionError("Invalid HMAC callback signature")``.
       No state mutation, no outcome write.
    2. Parse the callback JSON; extract ``gate_id``, ``decision``,
       ``suggested_action``.
    3. Look up the pending gate from ``_PENDING_GATES``. (Phase 35 will rebuild
       from PipelineState; this in-process cache is the adapter shim.)
    4. ``gate.resolve(decision, suggested_action)`` → outcome record.
    5. Write outcome to asset bus ``review-outcomes`` slot (CF-04).
    6. Advance PipelineState phase status (approved / rejected / contested).
    7. On reject with ``suggested_action``: include ``rollback_to`` in the
       returned dict so the Phase 35 runner can jump to the target phase.

    Raises:
        PermissionError: HMAC verification failed.
        KeyError: ``gate_id`` in the callback has no pending gate in this
            process (Phase 35 runner handles by rebuilding from state).
    """
    if not _review_client().verify_callback(body, signature, timestamp):
        # CRITICAL: no state mutation on auth failure.
        raise PermissionError("Invalid HMAC callback signature")

    callback_data = json.loads(body)
    gate_id = callback_data["gate_id"]
    decision = callback_data["decision"]
    suggested_action = callback_data.get("suggested_action")

    gate = _PENDING_GATES[gate_id]
    outcome = gate.resolve(decision, suggested_action)

    _write_review_outcome(gate, outcome)
    _advance_state_after_resolution(gate.config.phase, decision, gate)

    # Phase 37 — gate resolution event hook. Fire AFTER review-outcomes is
    # persisted (D-37-07) so subscribers see the formal outcome on the asset
    # bus before reacting. Guarded against subscriber exceptions (D-37-04):
    # the outcome + state advancement are already committed, so a buggy
    # subscriber never crashes the resume flow.
    if _on_gate_resolved is not None:
        try:
            _on_gate_resolved(gate.episode_id, gate_id, decision, outcome)
        except Exception:
            logger.warning(
                "resume_from_callback: on_gate_resolved hook raised "
                "(gate=%s decision=%s) — swallowed, resume continues",
                gate_id, decision,
                exc_info=True,
            )

    # Surface rollback target for the Phase 35 runner (CF-04 reject path).
    if decision == "reject" and suggested_action:
        outcome = {**outcome, "rollback_to": suggested_action}

    return outcome


def resolve_direct(
    gate_id: str,
    decision: str,
    suggested_action: Optional[str] = None,
) -> dict:
    """Direct operator-side gate resolution (Plan 34-04, Option (b)).

    Bypasses HMAC verification (which is reserved for external callbacks via
    ``resume_from_callback``). The operator invoking this path is already
    authenticated to hermes-agent, so the HMAC check is unnecessary and
    would reject empty signatures. Behavior is otherwise identical to
    ``resume_from_callback`` post-verification: look up the pending gate,
    resolve it, write the outcome to the asset bus, advance PipelineState,
    and surface ``rollback_to`` on reject.

    Used by the ``gate_resolve`` tool handler (Phase 34-04). The external
    webhook path (Phase 35 runner) continues to use ``resume_from_callback``
    which enforces HMAC on inbound POSTs.

    Raises:
        KeyError: ``gate_id`` has no pending gate in this process. Phase 35
            will rebuild from PipelineState; for the direct-operator flow the
            gate must have been submitted earlier in the same process.
        GateError: the gate rejected the decision (invalid state transition).
    """
    gate = _PENDING_GATES[gate_id]
    outcome = gate.resolve(decision, suggested_action)

    _write_review_outcome(gate, outcome)
    _advance_state_after_resolution(gate.config.phase, decision, gate)

    # Phase 37 — gate resolution event hook (mirrors resume_from_callback;
    # D-37-07). Operator-side resolution must notify subscribers too, so the
    # canvas reflects manual approvals/rejects the same as webhook-driven
    # ones.
    if _on_gate_resolved is not None:
        try:
            _on_gate_resolved(gate.episode_id, gate_id, decision, outcome)
        except Exception:
            logger.warning(
                "resolve_direct: on_gate_resolved hook raised "
                "(gate=%s decision=%s) — swallowed, resolve continues",
                gate_id, decision,
                exc_info=True,
            )

    if decision == "reject" and suggested_action:
        outcome = {**outcome, "rollback_to": suggested_action}

    return outcome


def poll_until_terminal(
    gate_id: str,
    timeout_sec: int,
    *,
    interval_sec: int = 30,
    episode_id: str = "",
) -> dict:
    """Polling-mode wait loop: actively query the review platform.

    Sequence (Plan 34-03 Task 2 item 7):

    1. Build the Gate + call ``submit({})`` to register the attempt (may raise
       ``GateMaxRetriesExceeded``).
    2. Track ``review_id`` from the submit response.
    3. Loop while ``elapsed < timeout_sec``:
       - ``ReviewPlatformClient.query_review_status(review_id)``.
       - If ``state in {"resolved", "closed"}``: map platform disposition to a
         gate decision and resolve. Break.
       - Else ``time.sleep(interval_sec)``.
    4. On timeout: set gate status to ``timed_out`` and return that outcome.
    5. Write outcome + advance PipelineState (same as ``resume_from_callback``
       for the resolved branch).

    Returns the outcome dict (resolved or timed_out).
    """
    gate = _build_gate(gate_id, episode_id or "_poll", GateMode.POLLING)
    gate.submit({})  # may raise GateMaxRetriesExceeded

    # Seed a submit so the platform assigns a review_id we can poll.
    submit_result = _review_client().submit_review(
        type=gate_id,
        content_ref=f"{episode_id or '_poll'}/{gate.config.phase}",
        callback_url=None,
    )
    if isinstance(submit_result, dict) and submit_result.get("degraded"):
        outcome = gate.resolve("approve")
        _write_review_outcome(gate, outcome)
        _advance_state_after_resolution(gate.config.phase, "approve", gate)
        return outcome
    gate.review_id = submit_result.get("review_id")

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        status = _review_client().query_review_status(gate.review_id)
        state = (status or {}).get("state")
        if state in {"resolved", "closed"}:
            disposition = (status or {}).get("disposition", "APPROVED")
            decision = "approve" if str(disposition).upper() == "APPROVED" else "reject"
            outcome = gate.resolve(decision)
            _write_review_outcome(gate, outcome)
            _advance_state_after_resolution(gate.config.phase, decision, gate)
            return outcome
        # Sleeps in polling mode are intentional (sync API, D-34-05). Phase 35
        # runner wraps this whole function in ``asyncio.to_thread``.
        time.sleep(max(0, interval_sec))

    # Timeout path — no resolution, but record the terminal state.
    gate.status = GateStatus.TIMED_OUT
    outcome = gate._outcome_record()
    _write_review_outcome(gate, outcome)
    return outcome


def mark_episode_failed(
    episode_id: str,
    gate_id: str,
    exc: GateMaxRetriesExceeded,
) -> None:
    """PIPE-GUARD-01: write ``status=failed`` + the consistency-blocked marker.

    Preserves v4.0 PIPE-GUARD-01 semantics: when a gate exhausts its
    ``retry_policy.max_retries``, the episode is marked failed with the
    consistency-blocked error prefix in the error field. The pipeline must NOT
    silently swallow the failure (silent swallow was the v4.0 bug PIPE-GUARD-01
    fixed).

    ``str(exc)`` already starts with the marker prefix (Plan 34-01
    ``GateMaxRetriesExceeded.__init__``), so we surface it verbatim rather than
    reconstructing the message here. Tests assert the prefix shows up in the
    on-disk state file (grep-able PIPE-GUARD-01 verification marker).
    """
    store = _state_store()
    state = store.load()
    if not state.episode:
        state.episode = episode_id
    phase = to_gate_config(gate_id).phase
    state.phases[phase] = {
        "status": "failed",
        "failed_at": _now_iso(),
        "error": str(exc),  # carries the marker prefix from Plan 34-01
        "gate_id": gate_id,
    }
    state.current_phase_id = phase
    store.save(state)
    logger.error(
        "PIPE-GUARD-01 episode_failed: episode=%s gate=%s phase=%s error=%s",
        episode_id,
        gate_id,
        phase,
        exc,
    )


# ────────────────── Phase 40 Plan 02: redline auto-detect path ──────────────
#
# GATE-04 additive: the 3 redline gates (R1/R3/R4) auto-resolve via the
# Plan-01 DETECTOR_REGISTRY. The 8 V8.6 gates keep their manual HIL path
# (``pause_for_review`` + ``gate_resolve``) with zero behavior change.
# ``tools._handle_gate_submit`` dispatches on the ``redline_`` prefix to
# route to ``auto_detect_and_resolve`` instead of ``pause_for_review``.


# The gate_id prefix that marks a gate as auto-detect (Phase 40 convention).
# Matches the 3 Plan-01 detector GATE_IDs:
#   redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending
_REDLINE_PREFIX = "redline_"


def is_redline_gate(gate_id: str) -> bool:
    """True if ``gate_id`` starts with ``redline_`` (Phase 40 Plan 02 convention).

    Used by ``tools._handle_gate_submit`` to route redline gates to the
    auto-detect path (``auto_detect_and_resolve``) instead of the V8.6
    HIL path (``pause_for_review``). Defensive against None / non-str input
    (returns False rather than raising) so callers can use it as a safe
    prefix check on untrusted args.
    """
    if not isinstance(gate_id, str):
        return False
    return gate_id.startswith(_REDLINE_PREFIX)


def auto_detect_and_resolve(gate_id: str, episode_id: str, payload: dict) -> dict:
    """Auto-resolve a redline gate by running its Plan-01 detector.

    Sequence (Plan 40-02 Task 3):

    1. Build the Gate via ``_build_gate(gate_id, episode_id, mode=None)`` —
       reuses the existing Phase 34 helper (loads GateConfig from gates.yaml).
    2. Call ``gate.submit(payload)`` — increments ``attempt``; may raise
       ``GateMaxRetriesExceeded`` (caller catches, same as pause_for_review).
    3. Import ``DETECTOR_REGISTRY`` from ``plugins.review_gates.gates`` (Plan 01).
       Look up ``gate_id``. If missing → raise ``KeyError`` (T-40-05 mitigation:
       a ``redline_``-prefixed gate_id without a registered detector is a
       misconfiguration — NEVER silent auto-approve).
    4. Run the detector: ``decision, suggested_action = DETECTOR_REGISTRY[
       gate_id](payload)``. Detectors are pure-stdlib functions (D-34-01
       extended); they return ``("approve"|"reject"|"contest", str|None)``.
    5. Call ``gate.resolve(decision, suggested_action)`` — uses Phase 34's
       public API (gate.py FROZEN, no edits).
    6. Write the outcome to the asset bus ``review-outcomes`` slot (CF-04)
       via ``_write_review_outcome`` — audit trail preserved.
    7. Advance PipelineState via ``_advance_state_after_resolution`` (approve
       → approved, reject → rejected, contest → contested).
    8. For reject with suggested_action: include ``rollback_to`` in the
       returned dict (mirror ``resume_from_callback``).
    9. Register the gate in ``_PENDING_GATES`` for audit visibility (the gate
       is already resolved; this just lets a later gates_list query find it).

    Args:
        gate_id: must start with ``redline_`` AND exist in DETECTOR_REGISTRY.
            Caller (``tools._handle_gate_submit``) is expected to have already
            verified ``gate_id`` is in ``GATE_REGISTRY`` (gates.yaml) — we do
            NOT re-check here.
        episode_id: episode under review.
        payload: gate submission payload — must match the detector's expected
            shape (e.g. ``{"beats": [{"emotion": ...}, ...}`` for R1).

    Returns:
        Outcome dict from ``gate.resolve()`` with ``rollback_to`` added on
        reject. Shape (CF-04 outcome record)::

            {
              "gate_id": str,
              "episode_id": str,
              "decision": "approve" | "reject" | "contest",
              "suggested_action": str | None,
              "reviewer_role": str,            # "redline_scanner"
              "resolved_at": str,              # ISO-8601
              "attempt": int,
              "status": str,                   # "approved"|"rejected"|"contested"
              "rollback_to": str | None,       # only on reject with action
            }

    Raises:
        GateMaxRetriesExceeded: when ``attempt > config.max_retries`` (same
            retry semantics as ``pause_for_review``). Caller catches and
            invokes ``mark_episode_failed``.
        KeyError: ``gate_id`` not in ``DETECTOR_REGISTRY`` — the prefix check
            passed but no detector was registered. T-40-05 mitigation: this
            is a misconfiguration (gates.yaml has a ``redline_X`` entry but
            the detector module was never registered). Fails loud rather
            than silent auto-approve.
    """
    # Lazy import to avoid a circular dependency at module load time
    # (plugins.review_gates.gates does not import runner_hooks, but keeping
    # the import local to this function makes the dependency direction
    # explicit and lets the V8.6-only path import runner_hooks without
    # requiring the gates/ subpackage to be populated).
    from plugins.review_gates.gates import DETECTOR_REGISTRY

    # Step 1-2: Build the Gate + submit (may raise GateMaxRetriesExceeded).
    gate = _build_gate(gate_id, episode_id, mode=None)
    submission = gate.submit(payload)  # may raise GateMaxRetriesExceeded

    # Step 3: T-40-05 mitigation — unknown redline_X without a detector raises
    # KeyError, NEVER silent auto-approve.
    if gate_id not in DETECTOR_REGISTRY:
        raise KeyError(
            f"auto_detect_and_resolve: gate_id {gate_id!r} has the "
            f"'redline_' prefix but is not in DETECTOR_REGISTRY. "
            f"This is a misconfiguration — register the detector in "
            f"plugins.review_gates.gates.__init__ or fix the gate_id in "
            f"gates.yaml. Registered detectors: {sorted(DETECTOR_REGISTRY.keys())}"
        )

    # Step 4: Run the Plan-01 detector on the payload. Detectors are pure
    # functions (D-34-01 extended) — no network, no state, no exceptions
    # on malformed payloads (T-40-01 mitigation in Plan 01).
    detect_fn = DETECTOR_REGISTRY[gate_id]
    decision, suggested_action = detect_fn(payload)

    # Step 5: Resolve via Phase 34's public API (gate.py FROZEN — no edits).
    outcome = gate.resolve(decision, suggested_action)

    # Step 6-7: Write outcome to asset bus + advance PipelineState. Mirrors
    # resume_from_callback / resolve_direct (Phase 34 HIL resolution path).
    _write_review_outcome(gate, outcome)
    _advance_state_after_resolution(gate.config.phase, decision, gate)

    # Phase 37 — gate resolution event hook. Fire AFTER review-outcomes is
    # persisted (D-37-07) so subscribers see the formal outcome on the asset
    # bus before reacting. Guarded against subscriber exceptions (D-37-04).
    if _on_gate_resolved is not None:
        try:
            _on_gate_resolved(gate.episode_id, gate_id, decision, outcome)
        except Exception:
            logger.warning(
                "auto_detect_and_resolve: on_gate_resolved hook raised "
                "(gate=%s decision=%s) — swallowed, auto-resolve continues",
                gate_id, decision,
                exc_info=True,
            )

    # Step 8: Surface rollback target for the Phase 35 runner (CF-04 reject
    # path) — mirrors resume_from_callback / resolve_direct.
    if decision == "reject" and suggested_action:
        outcome = {**outcome, "rollback_to": suggested_action}

    # Step 9: Register in _PENDING_GATES for audit visibility (the gate is
    # already resolved; this just lets a later gates_list / gate_wait query
    # find it by gate_id). Phase 34's pause_for_review does the same.
    _PENDING_GATES[gate_id] = gate

    logger.info(
        "auto_detect_and_resolve: gate=%s episode=%s decision=%s action=%s "
        "(attempt %d, detector=%s)",
        gate_id, episode_id, decision, suggested_action,
        gate.attempt, detect_fn.__module__ if hasattr(detect_fn, "__module__") else "?",
    )

    # Drop the submission field — callers care about the outcome shape.
    _ = submission  # silence unused-warning; kept for parity with pause_for_review
    return outcome
