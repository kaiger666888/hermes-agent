"""test_gate.py — Phase 34-01 TDD RED gate for plugins.review_gates.gate.

Covers the pure-stdlib HIL Gate state machine: enums, frozen GateConfig,
mutable Gate lifecycle (submit / wait / resolve) across the 3 switchable
modes (blocking / webhook / polling), GateMaxRetriesExceeded propagation,
and CF-04 outcome-record shape.

Anti-pattern checks assert:
- gate.py is pure stdlib (no httpx / jwt / yaml imports)
- gate.py is sync-only (no ``async def``)
- GateConfig is frozen + hashable; Gate is mutable
- GateMaxRetriesExceeded message carries the PIPE-GUARD-01 ``CONSISTENCY_BLOCKED:`` marker
"""

from __future__ import annotations

import ast
import threading
import time
from pathlib import Path

import pytest

from plugins.review_gates.gate import (
    Gate,
    GateConfig,
    GateError,
    GateMaxRetriesExceeded,
    GateMode,
    GateStatus,
)


# ---------------------------------------------------------------------------
# Module-level purity assertions (D-34-01, D-34-05)
# ---------------------------------------------------------------------------

_GATE_PY = Path(__file__).resolve().parent.parent / "gate.py"


def _gate_source() -> str:
    return _GATE_PY.read_text(encoding="utf-8")


def test_gate_py_is_pure_stdlib_no_http_jwt_yaml_imports():
    """D-34-01: gate.py must not import httpx / jwt / yaml."""
    src = _gate_source()
    tree = ast.parse(src)
    forbidden_top = {"httpx", "jwt", "yaml"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_top, (
                    f"forbidden import in gate.py: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            assert top not in forbidden_top, (
                f"forbidden from-import in gate.py: {node.module}"
            )


def test_gate_py_has_no_async_def():
    """D-34-05: gate.py is sync-only — no ``async def``."""
    src = _gate_source()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.AsyncFunctionDef,)), (
            "gate.py must not contain async def (D-34-05)"
        )


# ---------------------------------------------------------------------------
# TestGateEnums
# ---------------------------------------------------------------------------


class TestGateEnums:
    def test_gate_mode_values_exact(self):
        assert GateMode.BLOCKING.value == "blocking"
        assert GateMode.WEBHOOK.value == "webhook"
        assert GateMode.POLLING.value == "polling"
        # Exhaustive membership
        assert {m.value for m in GateMode} == {"blocking", "webhook", "polling"}

    def test_gate_status_six_values(self):
        expected = {
            "pending",
            "approved",
            "rejected",
            "contested",
            "timed_out",
            "failed",
        }
        assert {s.value for s in GateStatus} == expected


# ---------------------------------------------------------------------------
# TestGateConfig (frozen dataclass)
# ---------------------------------------------------------------------------


def _make_config(**overrides) -> GateConfig:
    base = dict(
        gate_id="topic-gate",
        phase="p01_hook_topic",
        asset_bus_slots_to_lock=("hook-topic", "outline"),
        reviewer_role="creative_source",
    )
    base.update(overrides)
    return GateConfig(**base)


class TestGateConfig:
    def test_required_fields_set_and_defaults_match_cf_02(self):
        cfg = _make_config()
        assert cfg.gate_id == "topic-gate"
        assert cfg.phase == "p01_hook_topic"
        assert cfg.asset_bus_slots_to_lock == ("hook-topic", "outline")
        assert cfg.reviewer_role == "creative_source"
        # Defaults per Plan 34-01 task 2 spec
        assert cfg.timeout_sec == 3600
        assert cfg.callback_url is None
        assert cfg.max_retries == 2
        assert cfg.backoff_sec == 300
        assert cfg.default_mode == GateMode.BLOCKING

    def test_frozen_dataclass_is_immutable_and_hashable(self):
        cfg = _make_config()
        # Hashable — hash() does not raise
        h = hash(cfg)
        assert isinstance(h, int)
        # Immutable — setattr raises FrozenInstanceError (dataclass frozen=True)
        with pytest.raises(Exception):  # FrozenInstanceError subclasses AttributeError
            cfg.gate_id = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TestGateConstruction
# ---------------------------------------------------------------------------


class TestGateConstruction:
    def test_gate_is_mutable_with_empty_initial_state(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        assert g.attempt == 0
        assert g.status == GateStatus.PENDING
        assert g.review_id is None
        assert g.submitted_at is None
        assert g.resolved_at is None
        assert g.decision is None
        assert g.suggested_action is None
        # Mutable: assignment works
        g.attempt = 5
        assert g.attempt == 5

    def test_gate_requires_config_episode_id_and_mode(self):
        cfg = _make_config()
        # All three required positional/keyword
        g = Gate(config=cfg, episode_id="EP02", mode=GateMode.WEBHOOK)
        assert g.episode_id == "EP02"
        assert g.mode == GateMode.WEBHOOK
        # Missing any required field raises TypeError
        with pytest.raises(TypeError):
            Gate(episode_id="EP03", mode=GateMode.BLOCKING)  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            Gate(config=cfg, mode=GateMode.BLOCKING)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TestSubmit
# ---------------------------------------------------------------------------


class TestSubmit:
    def test_submit_increments_attempt_sets_submitted_at_and_status_pending(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        assert g.attempt == 0
        rec = g.submit(payload={"artifact": "x"})
        assert g.attempt == 1
        assert g.submitted_at is not None and g.submitted_at.endswith((":00Z", "+00:00")) or "T" in (g.submitted_at or "")
        assert g.status == GateStatus.PENDING
        assert isinstance(rec, dict)

    def test_submit_returns_record_with_required_keys(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        rec = g.submit(payload={"artifact": "x"})
        assert rec["gate_id"] == "topic-gate"
        assert rec["episode_id"] == "EP01"
        assert rec["attempt"] == 1
        assert rec["submitted_at"] == g.submitted_at
        assert rec["status"] == "pending"

    def test_submit_beyond_max_retries_raises_and_sets_failed(self):
        cfg = _make_config(max_retries=2)
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        # attempt 1
        g.submit(payload={})
        # attempt 2
        g.submit(payload={})
        assert g.attempt == 2
        # attempt 3 — exceeds max_retries=2
        with pytest.raises(GateMaxRetriesExceeded) as excinfo:
            g.submit(payload={})
        # Status set to FAILED before raise propagates
        assert g.status == GateStatus.FAILED
        # PIPE-GUARD-01 marker present
        assert "CONSISTENCY_BLOCKED:" in str(excinfo.value)
        # Exception carries metadata
        assert excinfo.value.gate_id == "topic-gate"
        assert excinfo.value.attempts == 3
        assert excinfo.value.max_retries == 2


# ---------------------------------------------------------------------------
# TestWaitBlockingMode
# ---------------------------------------------------------------------------


class TestWaitBlockingMode:
    def test_blocking_wait_returns_immediately_when_already_resolved(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        g.submit(payload={})
        # Pre-resolve from another thread is equivalent to already-set Event
        g.resolve("approve")
        rec = g.wait(timeout_sec=1)
        assert rec["status"] == "approved"

    def test_blocking_wait_times_out_sets_timed_out(self):
        cfg = _make_config(timeout_sec=1)
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        g.submit(payload={})
        start = time.monotonic()
        rec = g.wait(timeout_sec=1)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.9  # actually waited ~1s
        assert g.status == GateStatus.TIMED_OUT
        assert rec["status"] == "timed_out"

    def test_concurrent_resolve_from_another_thread_wakes_waiter(self):
        cfg = _make_config(timeout_sec=5)
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        g.submit(payload={})

        result: dict = {}

        def resolver():
            # Brief delay so the main thread is inside Event.wait()
            time.sleep(0.15)
            outcome = g.resolve("approve", suggested_action=None)
            result["outcome"] = outcome

        t = threading.Thread(target=resolver)
        t.start()
        start = time.monotonic()
        rec = g.wait(timeout_sec=5)
        elapsed = time.monotonic() - start
        t.join(timeout=2)
        # Woken well under the 5s timeout
        assert elapsed < 2.0, f"wait blocked too long: {elapsed}s"
        assert g.status == GateStatus.APPROVED
        assert rec["status"] == "approved"
        assert result.get("outcome", {}).get("decision") == "approve"


# ---------------------------------------------------------------------------
# TestWaitWebhookMode
# ---------------------------------------------------------------------------


class TestWaitWebhookMode:
    def test_webhook_wait_returns_immediately_with_awaiting_callback(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.WEBHOOK)
        g.submit(payload={})
        g.review_id = "rev_abc"
        start = time.monotonic()
        rec = g.wait(timeout_sec=5)
        elapsed = time.monotonic() - start
        # Non-blocking — returns in well under 1s
        assert elapsed < 0.5
        assert rec["status"] == "awaiting_callback"
        assert rec["review_id"] == "rev_abc"
        # Gate status unchanged (still pending)
        assert g.status == GateStatus.PENDING


# ---------------------------------------------------------------------------
# TestWaitPollingMode
# ---------------------------------------------------------------------------


class TestWaitPollingMode:
    def test_polling_wait_raises_gate_error_directing_to_runner_hooks(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.POLLING)
        g.submit(payload={})
        with pytest.raises(GateError) as excinfo:
            g.wait(timeout_sec=1)
        msg = str(excinfo.value)
        # Directs caller to the runner_hooks adapter
        assert "poll_until_terminal" in msg or "poll_step" in msg


# ---------------------------------------------------------------------------
# TestResolve
# ---------------------------------------------------------------------------


class TestResolve:
    @pytest.mark.parametrize(
        "decision,expected_status",
        [
            ("approve", GateStatus.APPROVED),
            ("reject", GateStatus.REJECTED),
            ("contest", GateStatus.CONTESTED),
        ],
    )
    def test_resolve_sets_status_decision_and_signals_event(self, decision, expected_status):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        g.submit(payload={})
        # Event is currently unset (cleared by submit)
        assert not g._event.is_set()
        outcome = g.resolve(decision, suggested_action="rollback:p02_outline")
        assert g.status == expected_status
        assert g.decision == decision
        assert g.suggested_action == "rollback:p02_outline"
        assert g.resolved_at is not None
        # Event signaled — wakes any blocking waiter
        assert g._event.is_set()
        # Outcome record reflects the decision
        assert outcome["decision"] == decision
        assert outcome["status"] == expected_status.value

    def test_resolve_with_invalid_decision_raises_gate_error(self):
        cfg = _make_config()
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        g.submit(payload={})
        with pytest.raises(GateError):
            g.resolve("invalid_decision")

    def test_resolve_signals_blocking_waiter(self):
        """End-to-end: resolve from same thread wakes a blocked waiter in another."""
        cfg = _make_config(timeout_sec=10)
        g = Gate(config=cfg, episode_id="EP01", mode=GateMode.BLOCKING)
        g.submit(payload={})

        waiter_result: dict = {}

        def waiter():
            waiter_result["rec"] = g.wait(timeout_sec=10)

        t = threading.Thread(target=waiter)
        t.start()
        time.sleep(0.2)
        g.resolve("approve")
        t.join(timeout=2)
        assert t.is_alive() is False
        assert waiter_result["rec"]["status"] == "approved"


# ---------------------------------------------------------------------------
# TestOutcomeRecord (CF-04 shape)
# ---------------------------------------------------------------------------


class TestOutcomeRecord:
    def test_outcome_record_full_shape_per_cf_04(self):
        cfg = _make_config(reviewer_role="script_auditor")
        g = Gate(config=cfg, episode_id="EP42", mode=GateMode.BLOCKING)
        g.submit(payload={})
        g.resolve("reject", suggested_action="rollback:p02_outline")
        rec = g._outcome_record()
        # CF-04 keys (excluding payload_snapshot which lives in the asset-bus slot
        # envelope written by runner_hooks — gate.py emits the resolution record only)
        assert rec["gate_id"] == "topic-gate"
        assert rec["episode_id"] == "EP42"
        assert rec["decision"] == "reject"
        assert rec["suggested_action"] == "rollback:p02_outline"
        assert rec["reviewer_role"] == "script_auditor"
        assert rec["resolved_at"] == g.resolved_at
        assert rec["attempt"] == 1
        assert rec["status"] == "rejected"
