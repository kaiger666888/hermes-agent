"""test_poller_complete_state.py — 54-03 R2/R3: COMPLETE vocabulary + review_result extraction.

Phase 54-03 (GATE-03 legs R2+R3). Mirrors ``test_runner_hooks.py`` patterns:
``MagicMock`` review client injected via ``monkeypatch.setattr(runner_hooks,
"_review_client", ...)``, ``tmp_path + monkeypatch.chdir`` for state writes,
and a patched ``to_gate_config`` / ``gate_id_to_phase_id`` so tests never
touch the real YAML registry.

Coverage target (7 groups):

- Path 2 terminal vocabulary: platform ``COMPLETE`` is terminal (alongside
  legacy ``resolved`` / ``closed`` — union, no regression).
- Decision source priority: ``status.result.decision`` first
  (approve/reject/waive→approve, C.4); without ``result`` the legacy
  disposition fallback mapping still fires.
- ``chosen`` third channel: ``result.selected[0]`` → ``choose:v{N}`` →
  ``_chosen_from_suggested`` parser (parser itself unchanged).
- R2 extraction: ``query_review_status`` returns a fifth ``result`` key
  sourced from ``data.metadata.review_result`` with the legacy four keys
  intact; degrade envelopes pass through unchanged.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plugins.review_gates import runner_hooks
from plugins.review_gates.gate import GateConfig, GateMode


# ────────────────── Fixtures (mirrors test_runner_hooks) ──────────────────


@pytest.fixture
def fake_review_client():
    client = MagicMock()
    client.submit_review.return_value = {"review_id": "rev-54", "state": "pending"}
    client.query_review_status.return_value = {
        "review_id": "rev-54",
        "state": "PENDING",
    }
    return client


@pytest.fixture
def patched_hooks(monkeypatch, tmp_path, fake_review_client):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake_review_client)
    runner_hooks._PENDING_GATES.clear()

    cfg = GateConfig(
        gate_id="topic-gate",
        phase="p01_hook_topic",
        asset_bus_slots_to_lock=("hook-topic",),
        reviewer_role="creative_source",
        timeout_sec=3600,
        callback_url=None,
        max_retries=2,
        backoff_sec=300,
        default_mode=GateMode.BLOCKING,
    )

    def _fake_to_gate_config(key: str) -> GateConfig:
        if key in (cfg.gate_id, cfg.phase):
            return cfg
        return GateConfig(
            gate_id=key,
            phase="p99",
            asset_bus_slots_to_lock=(),
            reviewer_role="creative_source",
        )

    monkeypatch.setattr(runner_hooks, "to_gate_config", _fake_to_gate_config)
    if hasattr(runner_hooks, "gate_id_to_phase_id"):
        monkeypatch.setattr(
            runner_hooks,
            "gate_id_to_phase_id",
            lambda gid: cfg.phase if gid == cfg.gate_id else gid,
        )
    return fake_review_client


def _complete_status(**result_extra) -> dict:
    """Platform status payload post-R1: COMPLETE + metadata-sourced result."""
    result = {"decision": "approve"}
    result.update(result_extra)
    return {
        "review_id": "rev-54",
        "state": "COMPLETE",
        "disposition": "HUMAN",
        "version": 3,
        "result": result,
    }


# ────────────────── Path 2: COMPLETE vocabulary + decision mapping ────────


class TestPath2CompleteVocabulary:
    def test_complete_with_result_approve(self, patched_hooks):
        patched_hooks.query_review_status.return_value = _complete_status(
            decision="approve"
        )
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out["decision"] == "approve"
        assert out["status"] == "approved"

    def test_complete_with_result_reject(self, patched_hooks):
        patched_hooks.query_review_status.return_value = _complete_status(
            decision="reject"
        )
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out["decision"] == "reject"
        assert out["status"] == "rejected"

    def test_complete_with_result_waive_maps_to_approve(self, patched_hooks):
        """C.4 定案: waive 在 kmc 消费端读作 approve(豁免=放行)。"""
        patched_hooks.query_review_status.return_value = _complete_status(
            decision="waive"
        )
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out["decision"] == "approve"
        assert out["status"] == "approved"

    def test_complete_without_result_falls_back_to_disposition(self, patched_hooks):
        """无 result 键(旧记录/degrade 合成)→ 旧 disposition 兜底映射仍生效。"""
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-54",
            "state": "COMPLETE",
            "disposition": "APPROVED",
            "version": 2,
        }
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out["decision"] == "approve"

    def test_resolved_and_closed_still_terminal(self, patched_hooks):
        """并集兼容: legacy resolved/closed 词汇不回归。"""
        for legacy_state in ("resolved", "closed"):
            runner_hooks._PENDING_GATES.clear()
            patched_hooks.query_review_status.return_value = {
                "review_id": "rev-54",
                "state": legacy_state,
                "disposition": "APPROVED",
                "version": 2,
            }
            out = runner_hooks.pause_and_wait_for_review(
                "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
            )
            assert out["decision"] == "approve", legacy_state


class TestPath2ChosenThirdChannel:
    def test_chosen_from_result_selected(self, patched_hooks):
        """result.selected[0]=2 → choose:v2 → chosen_variant_id "v2"。

        第三通道排在 chosen_variant_id / suggested_action 之后(两者缺席时生效)。
        """
        patched_hooks.query_review_status.return_value = _complete_status(
            selected=[2]
        )
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out.get("chosen_variant_id") == "v2"

    def test_chosen_variant_id_still_wins(self, patched_hooks):
        """既有第一通道优先: 平台显式 chosen_variant_id 存在时不被 selected 覆盖。"""
        status = _complete_status(selected=[3])
        status["chosen_variant_id"] = "v1"
        patched_hooks.query_review_status.return_value = status
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out.get("chosen_variant_id") == "v1"


class TestPath2WaivedShotIds:
    """67-03 (v3.2 F15/WBX-02):waived_shot_ids 子集透传进 outcome。"""

    def test_waived_subset_injected_on_approve(self, patched_hooks):
        patched_hooks.query_review_status.return_value = _complete_status(
            waived_shot_ids=["S01", "S03"]
        )
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out["decision"] == "approve"
        assert out["waived_shot_ids"] == ["S01", "S03"]

    def test_no_waived_key_legacy_shape(self, patched_hooks):
        """无 waived_shot_ids(telegram 路径)→ outcome 不带该键,p10c/p11c
        落 legacy 全量豁免分支。"""
        patched_hooks.query_review_status.return_value = _complete_status()
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert "waived_shot_ids" not in out

    def test_reject_never_carries_waived(self, patched_hooks):
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-54",
            "state": "COMPLETE",
            "disposition": "HUMAN",
            "version": 3,
            "result": {
                "decision": "reject",
                "waived_shot_ids": ["S01"],
            },
        }
        out = runner_hooks.pause_and_wait_for_review(
            "topic-gate", "ep-54", {}, timeout_sec=2, poll_interval_sec=0.01
        )
        assert out["decision"] == "reject"
        assert "waived_shot_ids" not in out


class TestPollUntilTerminalComplete:
    def test_complete_maps_via_result(self, patched_hooks):
        """次要路径 poll_until_terminal: COMPLETE + result.decision 走同一映射。"""
        patched_hooks.query_review_status.return_value = _complete_status(
            decision="approve"
        )
        out = runner_hooks.poll_until_terminal(
            "topic-gate", timeout_sec=1, interval_sec=0, episode_id="ep-54"
        )
        assert out["decision"] == "approve"


# ────────────────── R2: query_review_status result key ────────────────────


class TestQueryReviewStatusResultKey:
    def _client_with(self, monkeypatch, response):
        from plugins.kais_aigc import review_platform

        client = review_platform.ReviewPlatformClient(
            base_url="http://review.invalid:8090"
        )
        monkeypatch.setattr(client, "_request", MagicMock(return_value=response))
        return client

    def test_fifth_key_result_extracted(self, monkeypatch):
        review_result = {"decision": "waive", "reason": "x"}
        client = self._client_with(
            monkeypatch,
            {
                "data": {
                    "id": 9,
                    "state": "COMPLETE",
                    "disposition": "HUMAN",
                    "version": 4,
                    "metadata": {"review_result": review_result},
                }
            },
        )
        status = client.query_review_status(9)
        assert status["result"] == review_result
        assert status["review_id"] == 9
        assert status["state"] == "COMPLETE"
        assert status["disposition"] == "HUMAN"
        assert status["version"] == 4

    def test_missing_metadata_yields_none_result(self, monkeypatch):
        client = self._client_with(
            monkeypatch,
            {"data": {"id": 10, "state": "APPROVING", "version": 1}},
        )
        status = client.query_review_status(10)
        assert status["result"] is None
        assert status["state"] == "APPROVING"

    def test_degrade_envelope_passthrough(self, monkeypatch):
        envelope = {
            "degraded": True,
            "client": "review_platform",
            "operation": "query",
            "state": "DEGRADED_AUTO",
            "disposition": "APPROVED",
        }
        client = self._client_with(monkeypatch, envelope)
        assert client.query_review_status(1) == envelope
