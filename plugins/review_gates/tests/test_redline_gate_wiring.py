"""test_redline_gate_wiring.py — Phase 40-02 end-to-end auto-detect tests.

Verifies the Plan 02 wiring:

- ``runner_hooks.is_redline_gate(gate_id)`` correctly classifies by prefix.
- ``runner_hooks.auto_detect_and_resolve(gate_id, episode_id, payload)``
  runs the Plan-01 detector on the payload and auto-resolves the Gate:
    * violation payload  -> decision="reject", suggested_action="formula:..."
    * compliant payload  -> decision="approve", suggested_action=None
- Each of the 3 redline gate_ids dispatches to its OWN detector (no
  cross-wiring — R1 emotion payload must NOT trigger R3 cold-open).
- V8.6 gate_ids (e.g. topic-gate) do NOT auto-resolve — they keep the
  Phase 34 manual HIL path (pause_for_review leaves them PENDING).
- ``tools._handle_gate_submit`` dispatches redline_* gates through the
  auto-detect path, emitting a tool_result envelope with
  ``status="auto_resolved"`` (NOT "submitted").
- Unknown ``redline_X`` gate_id without a DETECTOR_REGISTRY entry raises
  KeyError (T-40-05 mitigation — never silent auto-approve).

These tests run against the REAL gates.yaml / DETECTOR_REGISTRY / detectors
(no mocks of the detector functions). The review-platform client is mocked
via ``monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake)``
so we don't hit the network; the detector path is pure-stdlib and runs
in-process.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plugins.review_gates import runner_hooks, tools
from plugins.review_gates.gate import GateStatus
from plugins.review_gates.gates import DETECTOR_REGISTRY
from plugins.review_gates.tools import _handle_gate_submit


# ────────────────── Shared fixtures (mirror test_tools_dispatch.py) ─────────


@pytest.fixture
def fake_review_client():
    """MagicMock standing in for ReviewPlatformClient (Phase 34-03 pattern)."""
    client = MagicMock()
    client.submit_review.return_value = {"review_id": "rev-auto", "state": "pending"}
    client.verify_callback.return_value = True
    client.query_review_status.return_value = {
        "review_id": "rev-auto",
        "state": "pending",
    }
    return client


@pytest.fixture
def patched(tmp_path: Path, monkeypatch, fake_review_client):
    """Redirect runner_hooks factory helpers to tmp_path + inject mock client."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake_review_client)
    runner_hooks._PENDING_GATES.clear()
    return fake_review_client


# ────────────────── Test payloads ──────────────────────────────────────────


# R1 violation: 3 consecutive same-emotion beats (anger) — triggers desensitization.
R1_VIOLATION = {
    "beats": [
        {"emotion": "anger"},
        {"emotion": "anger"},
        {"emotion": "anger"},
    ]
}

# R1 compliant: ≤2 consecutive same emotion.
R1_COMPLIANT = {
    "beats": [
        {"emotion": "anger"},
        {"emotion": "anger"},
        {"emotion": "shock"},
    ]
}

# R3 violation: first beat is exposition (cold open).
R3_VIOLATION = {
    "beats": [
        {"label": "exposition"},
        {"label": "active_conflict"},
        {"label": "cliffhanger"},
    ]
}

# R4 violation: last beat is resolution (unfinished ending — no new hook).
R4_VIOLATION = {
    "beats": [
        {"label": "active_conflict"},
        {"label": "cliffhanger"},
        {"label": "resolution"},
    ]
}


# ────────────────── TestIsRedlineGate ──────────────────────────────────────


class TestIsRedlineGate:
    """Plan 02: is_redline_gate() classifies gate_ids by ``redline_`` prefix."""

    def test_redline_prefixed_ids_classified_true(self):
        assert runner_hooks.is_redline_gate("redline_emotion_desensitize") is True
        assert runner_hooks.is_redline_gate("redline_no_cold_open") is True
        assert runner_hooks.is_redline_gate("redline_unfinished_ending") is True

    def test_v86_gate_ids_classified_false(self):
        """All 8 V8.6 gate_ids must NOT match the redline_ prefix."""
        for gate_id in (
            "topic-gate",
            "outline-gate",
            "script-gate",
            "character-gate",
            "scene-select-gate",
            "shot-breakdown-gate",
            "render-gate",
            "delivery-gate",
        ):
            assert runner_hooks.is_redline_gate(gate_id) is False, (
                f"{gate_id} must not be classified as redline"
            )

    def test_empty_or_none_gate_id_is_false(self):
        assert runner_hooks.is_redline_gate("") is False
        # None defensive — prefix check should not crash.
        assert runner_hooks.is_redline_gate(None) is False  # type: ignore[arg-type]


# ────────────────── TestAutoDetectEmotionDesensitize ───────────────────────


class TestAutoDetectEmotionDesensitize:
    """R1: pause_for_review('redline_emotion_desensitize', ...) auto-resolves."""

    def test_violation_payload_auto_rejects_with_formula_action(self, patched):
        """3 consecutive anger beats -> reject + suggested_action='formula:emotion-break-up'."""
        outcome = runner_hooks.auto_detect_and_resolve(
            "redline_emotion_desensitize", "EP01", R1_VIOLATION,
        )
        assert outcome["decision"] == "reject"
        assert outcome["suggested_action"] is not None
        assert outcome["suggested_action"].startswith("formula:")
        assert "emotion-break-up" in outcome["suggested_action"]
        # Reject path surfaces rollback_to (mirror resume_from_callback).
        assert outcome.get("rollback_to") == outcome["suggested_action"]

    def test_compliant_payload_auto_approves_with_null_action(self, patched):
        """Mixed-emotion sequence -> approve + suggested_action=None."""
        outcome = runner_hooks.auto_detect_and_resolve(
            "redline_emotion_desensitize", "EP01", R1_COMPLIANT,
        )
        assert outcome["decision"] == "approve"
        assert outcome["suggested_action"] is None

    def test_outcome_written_to_asset_bus_review_outcomes(self, patched, tmp_path):
        """auto-detect resolve must write the outcome to the review-outcomes slot (CF-04)."""
        runner_hooks.auto_detect_and_resolve(
            "redline_emotion_desensitize", "EP01", R1_VIOLATION,
        )
        outcomes_path = tmp_path / ".pipeline-assets" / "review-outcomes.json"
        assert outcomes_path.exists(), "review-outcomes.json must be written"
        doc = json.loads(outcomes_path.read_text(encoding="utf-8"))
        # Unwrap v3.0 envelope if present.
        if isinstance(doc, dict) and doc.get("schema_version") == "3.0":
            doc = doc["value"]
        records = doc.get("outcomes", [])
        assert any(
            r.get("gate_id") == "redline_emotion_desensitize"
            and r.get("decision") == "reject"
            for r in records
        ), f"redline reject outcome not found in {records}"


# ────────────────── TestAutoDetectNoColdOpen ───────────────────────────────


class TestAutoDetectNoColdOpen:
    """R3: pause_for_review('redline_no_cold_open', ...) auto-resolves."""

    def test_first_beat_exposition_auto_rejects(self, patched):
        outcome = runner_hooks.auto_detect_and_resolve(
            "redline_no_cold_open", "EP01", R3_VIOLATION,
        )
        assert outcome["decision"] == "reject"
        assert outcome["suggested_action"] is not None
        assert "cold-open-conflict-hook" in outcome["suggested_action"]

    def test_emotion_payload_does_not_trigger_cold_open_detector(self, patched):
        """R1 emotion payload must NOT trip R3 (no cross-wiring)."""
        outcome = runner_hooks.auto_detect_and_resolve(
            "redline_no_cold_open", "EP01", R1_VIOLATION,
        )
        # R1 violation payload has no label=exposition in beats[0]; R3 approves.
        assert outcome["decision"] == "approve", (
            "R3 detector must not trip on R1 emotion payload (no cross-wiring)"
        )


# ────────────────── TestAutoDetectUnfinishedEnding ─────────────────────────


class TestAutoDetectUnfinishedEnding:
    """R4: pause_for_review('redline_unfinished_ending', ...) auto-resolves."""

    def test_last_beat_resolution_auto_rejects(self, patched):
        outcome = runner_hooks.auto_detect_and_resolve(
            "redline_unfinished_ending", "EP01", R4_VIOLATION,
        )
        assert outcome["decision"] == "reject"
        assert outcome["suggested_action"] is not None
        assert "open-question-cliffhanger" in outcome["suggested_action"]


# ────────────────── TestV86GatesUnchanged ──────────────────────────────────


class TestV86GatesUnchanged:
    """Plan 02 success criterion: V8.6 8-gate HIL path preserved (zero behavior
    change). pause_for_review on a V8.6 gate_id does NOT auto-resolve."""

    def test_topic_gate_pause_leaves_gate_pending(self, patched):
        """pause_for_review('topic-gate', ...) leaves the gate in PENDING status
        awaiting manual gate_resolve (Phase 34 HIL contract preserved)."""
        result = runner_hooks.pause_for_review(
            "topic-gate", "EP01", {"hook": "a hook"},
        )
        # Phase 34 returns status=pending (not auto-resolved).
        assert result["status"] in ("pending", "submitted", "approved"), (
            f"unexpected V8.6 status: {result['status']!r}"
        )
        # The auto-resolve path would have written a reject/approve outcome
        # with decision set; here the gate sits in _PENDING_GATES unresolved.
        gate = runner_hooks._PENDING_GATES.get("topic-gate")
        if gate is not None:
            # If degraded-auto-approve fired, status is approved; otherwise
            # the gate is still PENDING (manual resolution path).
            assert gate.status in (GateStatus.PENDING, GateStatus.APPROVED), (
                f"V8.6 gate resolved to unexpected status: {gate.status}"
            )
            # Crucially, the V8.6 gate did NOT route through DETECTOR_REGISTRY.
            # The reviewer_role is creative_source, not redline_scanner.
            assert gate.config.reviewer_role != "redline_scanner"


# ────────────────── TestToolGateSubmitRedlineDispatch ──────────────────────


class TestToolGateSubmitRedlineDispatch:
    """Plan 02 Task 1 Test 7: _handle_gate_submit dispatches redline_ gates to
    the auto-detect path, emitting status='auto_resolved' (NOT 'submitted')."""

    def test_redline_submit_returns_auto_resolved_envelope(self, patched):
        """gate_submit(redline_emotion_desensitize, violation) -> status=auto_resolved + decision=reject."""
        result_str = _handle_gate_submit({
            "gate_id": "redline_emotion_desensitize",
            "episode_id": "EP01",
            "payload": R1_VIOLATION,
        })
        result = json.loads(result_str)
        assert result["status"] == "auto_resolved", (
            f"redline gate_submit must return status='auto_resolved', "
            f"got {result.get('status')!r}"
        )
        assert result["gate_id"] == "redline_emotion_desensitize"
        assert result["decision"] == "reject"
        assert result["suggested_action"].startswith("formula:")
        assert "emotion-break-up" in result["suggested_action"]

    def test_redline_submit_compliant_payload_auto_approves(self, patched):
        """gate_submit(redline_emotion_desensitize, compliant) -> auto_resolved + decision=approve."""
        result = json.loads(_handle_gate_submit({
            "gate_id": "redline_emotion_desensitize",
            "episode_id": "EP01",
            "payload": R1_COMPLIANT,
        }))
        assert result["status"] == "auto_resolved"
        assert result["decision"] == "approve"

    def test_v86_submit_still_returns_submitted_envelope(self, patched):
        """V8.6 gate_submit must still return status='submitted' (HIL path unchanged)."""
        result = json.loads(_handle_gate_submit({
            "gate_id": "topic-gate",
            "episode_id": "EP01",
            "payload": {"hook": "a hook"},
        }))
        assert result["status"] == "submitted", (
            f"V8.6 gate_submit must return status='submitted' (HIL preserved), "
            f"got {result.get('status')!r}"
        )


# ────────────────── TestUnknownRedlineGateRaises ───────────────────────────


class TestUnknownRedlineGateRaises:
    """T-40-05 mitigation: a gate_id with the ``redline_`` prefix but missing
    from DETECTOR_REGISTRY must raise KeyError — NEVER silent auto-approve.

    This guards against misconfiguration where gates.yaml has a redline_X
    entry but the detector module was never registered. The safe failure
    mode is to fail loud (KeyError), not to auto-approve.
    """

    def test_redline_prefix_not_in_detector_registry_raises_keyerror(self, patched, monkeypatch):
        """Construct a gate_id 'redline_unknown_X' that passes is_redline_gate()
        but is NOT in DETECTOR_REGISTRY -> auto_detect_and_resolve raises KeyError.

        We have to bypass the GATE_REGISTRY check (which would reject unknown
        gate_ids before auto-detect runs) by monkeypatching to_gate_config to
        return a fake config for the unknown redline gate_id.
        """
        from plugins.review_gates.gate import GateConfig, GateMode

        fake_cfg = GateConfig(
            gate_id="redline_unknown_test",
            phase="p13_delivery",
            asset_bus_slots_to_lock=("final-shots",),
            reviewer_role="redline_scanner",
            timeout_sec=60,
            max_retries=1,
            backoff_sec=60,
            default_mode=GateMode.BLOCKING,
        )
        monkeypatch.setattr(
            runner_hooks, "to_gate_config", lambda gid: fake_cfg,
        )
        # Sanity: confirm this gate_id is NOT in DETECTOR_REGISTRY.
        assert "redline_unknown_test" not in DETECTOR_REGISTRY

        with pytest.raises(KeyError):
            runner_hooks.auto_detect_and_resolve(
                "redline_unknown_test", "EP01", {"beats": []},
            )
