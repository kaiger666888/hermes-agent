"""test_blocking_gate.py — 2026-08-18 冗余审核体系: 真阻塞人工门.

Coverage for ``runner_hooks.pause_and_wait_for_review`` (+ the ``strict``
degrade semantics it adds to ``pause_for_review``):

- (a) in-process resolution: another thread ``resolve_direct`` → waiter
  returns the outcome (+ ``chosen_variant_id`` parsed from ``choose:<id>``).
- (b) cross-process resolution: ``query_review_status`` shows resolved →
  waiter mirrors the decision locally via ``resolve_direct`` (outcome +
  review-outcomes persisted), and surfaces a platform-supplied
  ``chosen_variant_id``.
- (c) timeout → ``HumanGateTimeout``; PipelineState keeps ``awaiting_review``
  (fail-closed, resumable).
- (d) strict submit + degrade envelope → ``ReviewPlatformUnavailable``
  (regardless of KAIS_GATE_STRICT — mandatory reviews never self-approve).
- (e) regression lock: legacy ``pause_for_review`` (strict=False) still
  auto-approves on a degrade envelope when KAIS_GATE_STRICT is unset.

Mirrors the test_runner_hooks.py conventions (MagicMock review client via
``monkeypatch.setattr(runner_hooks, "_review_client", ...)``, tmp_path chdir
for PipelineStateStore/AssetBus).
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from plugins.review_gates import runner_hooks
from plugins.review_gates.runner_hooks import (
    HumanGateTimeout,
    ReviewPlatformUnavailable,
)

# p13-gate (p13_delivery) — blocking mode, timeout 7200s in gates.yaml.
_GATE = "p13-gate"
_PHASE = "p13_delivery"


@pytest.fixture
def fake_review_client():
    client = MagicMock()
    client.submit_review.return_value = {"review_id": "rev-blk-1", "state": "pending"}
    client.query_review_status.return_value = {
        "review_id": "rev-blk-1",
        "state": "pending",
    }
    return client


@pytest.fixture
def patched_hooks(monkeypatch, tmp_path, fake_review_client):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake_review_client)
    monkeypatch.delenv("KAIS_GATE_STRICT", raising=False)
    runner_hooks._PENDING_GATES.clear()
    return fake_review_client


class TestInProcessResolution:
    def test_resolve_direct_approve_unblocks_waiter_with_chosen_variant(
        self, patched_hooks,
    ):
        """(a) resolve_direct in another thread wakes the blocking waiter;
        ``choose:<id>`` suggested_action surfaces as chosen_variant_id."""
        outcome_box: dict = {}

        def _waiter():
            outcome_box["result"] = runner_hooks.pause_and_wait_for_review(
                _GATE, "ep-blk",
                payload={"finalists": [{"id": "S01:first:2", "rank": 1}]},
                timeout_sec=10,
                poll_interval_sec=0.01,
            )

        t = threading.Thread(target=_waiter)
        t.start()
        # Wait until the gate is registered, then resolve as the operator
        # tool would (approve + explicit pick among the finalists).
        for _ in range(500):
            if _GATE in runner_hooks._PENDING_GATES:
                break
            time.sleep(0.01)
        runner_hooks.resolve_direct(
            _GATE, "approve", suggested_action="choose:S01:first:2",
        )
        t.join(timeout=5)
        assert not t.is_alive(), "waiter thread did not unblock"
        result = outcome_box["result"]
        assert result["status"] == "approved"
        assert result["decision"] == "approve"
        assert result["chosen_variant_id"] == "S01:first:2"
        # review-outcomes persisted by resolve_direct.
        bus = runner_hooks._asset_bus()
        outcomes = (bus.read("review-outcomes") or {}).get("outcomes", [])
        assert any(o.get("gate_id") == _GATE for o in outcomes)


class TestCrossProcessResolution:
    def test_platform_resolution_mirrors_decision_locally(self, patched_hooks):
        """(b) query_review_status resolved/APPROVED → local resolve_direct
        (outcome + PipelineState advanced) and status approved."""
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-blk-1",
            "state": "resolved",
            "disposition": "APPROVED",
        }
        result = runner_hooks.pause_and_wait_for_review(
            _GATE, "ep-blk", payload={}, timeout_sec=5, poll_interval_sec=0.01,
        )
        assert result["status"] == "approved"
        assert result["decision"] == "approve"
        state = runner_hooks._state_store().load()
        assert state.phases[_PHASE]["status"] == "approved"

    def test_platform_rejected_disposition_maps_to_reject(self, patched_hooks):
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-blk-1",
            "state": "closed",
            "disposition": "REJECTED",
        }
        result = runner_hooks.pause_and_wait_for_review(
            _GATE, "ep-blk", payload={}, timeout_sec=5, poll_interval_sec=0.01,
        )
        assert result["status"] == "rejected"
        assert result["decision"] == "reject"

    def test_platform_supplied_chosen_variant_id_passes_through(
        self, patched_hooks,
    ):
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-blk-1",
            "state": "resolved",
            "disposition": "APPROVED",
            "chosen_variant_id": "S02:last:1",
        }
        result = runner_hooks.pause_and_wait_for_review(
            _GATE, "ep-blk", payload={}, timeout_sec=5, poll_interval_sec=0.01,
        )
        assert result["chosen_variant_id"] == "S02:last:1"


class TestTimeoutAndStrict:
    def test_timeout_raises_and_preserves_awaiting_review(self, patched_hooks):
        """(c) No resolution within budget → HumanGateTimeout; PipelineState
        still awaiting_review (fail-closed, resumable)."""
        with pytest.raises(HumanGateTimeout) as exc_info:
            runner_hooks.pause_and_wait_for_review(
                _GATE, "ep-blk", payload={},
                timeout_sec=0.2, poll_interval_sec=0.05,
            )
        assert _GATE in str(exc_info.value)
        state = runner_hooks._state_store().load()
        assert state.phases[_PHASE]["status"] == "awaiting_review"

    def test_strict_degrade_raises_platform_unavailable(self, patched_hooks):
        """(d) strict submit + degrade envelope → ReviewPlatformUnavailable,
        no auto-approve, KAIS_GATE_STRICT unset."""
        patched_hooks.submit_review.return_value = {"degraded": True}
        with pytest.raises(ReviewPlatformUnavailable):
            runner_hooks.pause_and_wait_for_review(
                _GATE, "ep-blk", payload={},
                timeout_sec=5, poll_interval_sec=0.01,
            )
        # The gate must NOT have been self-approved.
        gate = runner_hooks._PENDING_GATES.get(_GATE)
        assert gate is None or gate.status.value not in {"approved"}

    def test_legacy_pause_for_review_degrade_still_auto_approves(
        self, patched_hooks,
    ):
        """(e) Regression lock: the async V8.6 gate path (strict=False)
        keeps the Phase-32 DEGRADED_AUTO disposition."""
        patched_hooks.submit_review.return_value = {"degraded": True}
        result = runner_hooks.pause_for_review(_GATE, "ep-blk", payload={})
        assert result["status"] == "approved"
