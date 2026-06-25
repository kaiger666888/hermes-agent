"""test_runner_hooks.py — unit tests for the Phase 35 runner adapter.

Phase 34-03 (SC#3/4/5, CF-03/04/05). Mirrors the Phase 32 ``MockTransport`` and
Phase 33 ``tmp_path + monkeypatch.chdir`` patterns. All review-platform calls
are funneled through a ``MagicMock`` injected via
``monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake_client)``.

Coverage target: 10-14 tests across 8 classes. Exercises:

- ``pause_for_review`` happy path + auto-resolve on degrade envelope.
- ``GateMaxRetriesExceeded`` propagation + ``mark_episode_failed`` writing the
  literal ``CONSISTENCY_BLOCKED:`` PIPE-GUARD-01 marker to ``.pipeline-state.json``.
- ``resume_from_callback`` approve / reject (rollback) / bad-HMAC paths.
- ``_write_review_outcome`` append-not-overwrite + CF-04 schema fields.
- ``poll_until_terminal`` resolved-on-poll + timeout.
- No ``async def`` (D-34-05) — verified via source grep, not here.

NOTE: these tests import ``runner_hooks`` which in turn imports
``plugins.review_gates.gate`` and ``plugins.review_gates.gate_config``. The
tests therefore only collect after Plans 34-01 (gate.py) and 34-02
(gate_config.py) have landed (Wave 1 sibling plans).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plugins.review_gates import runner_hooks
from plugins.review_gates.gate import (
    Gate,
    GateConfig,
    GateMaxRetriesExceeded,
    GateMode,
)
from plugins.review_gates.gate_config import to_gate_config


# ────────────────── Fixtures ──────────────────


@pytest.fixture
def fake_review_client():
    """MagicMock standing in for ReviewPlatformClient.

    Individual tests override the return values of ``submit_review`` /
    ``verify_callback`` / ``query_review_status`` to exercise each branch.
    """
    client = MagicMock()
    client.submit_review.return_value = {"review_id": "rev-123", "state": "pending"}
    client.verify_callback.return_value = True
    client.query_review_status.return_value = {
        "review_id": "rev-123",
        "state": "pending",
    }
    return client


@pytest.fixture
def patched_hooks(monkeypatch, tmp_path, fake_review_client):
    """Inject the mock review client + redirect factory helpers to tmp_path.

    Mirrors Phase 33-04 ``_state_store()`` / ``_asset_bus()`` pattern: the
    module-level factory helpers consult ``os.getcwd()``, so ``monkeypatch.chdir``
    routes every PipelineStateStore / AssetBus write under ``tmp_path``.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake_review_client)
    # Clear the in-process pending-gate cache between tests.
    runner_hooks._PENDING_GATES.clear()
    return fake_review_client


def _gate_config(
    gate_id: str = "topic-gate",
    phase: str = "p01_hook_topic",
    max_retries: int = 2,
    default_mode: GateMode = GateMode.BLOCKING,
    callback_url: str | None = None,
) -> GateConfig:
    """Construct a GateConfig directly (bypasses YAML registry).

    Plan 34-02 owns ``GATE_REGISTRY``; here we build a frozen dataclass
    instance so tests don't depend on the YAML loader.
    """
    return GateConfig(
        gate_id=gate_id,
        phase=phase,
        asset_bus_slots_to_lock=("hook-topic",),
        reviewer_role="creative_source",
        timeout_sec=3600,
        callback_url=callback_url,
        max_retries=max_retries,
        backoff_sec=300,
        default_mode=default_mode,
    )


@pytest.fixture
def patch_gate_config(monkeypatch):
    """Override ``to_gate_config`` so tests don't touch the real YAML registry."""
    cfg = _gate_config()

    def _fake_to_gate_config(gate_id: str) -> GateConfig:
        if gate_id == cfg.gate_id:
            return cfg
        # Fallback for unexpected gate ids.
        return GateConfig(
            gate_id=gate_id,
            phase="p99",
            asset_bus_slots_to_lock=(),
            reviewer_role="creative_source",
        )

    monkeypatch.setattr(runner_hooks, "to_gate_config", _fake_to_gate_config)
    return cfg


# ────────────────── TestPauseForReview ──────────────────


class TestPauseForReview:
    """SC#3: pause_for_review submits + writes awaiting_review state."""

    def test_submits_and_writes_awaiting_review(self, patched_hooks, patch_gate_config):
        """Happy path: review-platform returns review_id → gate.pending,
        PipelineState.phases[p01].status == "awaiting_review"."""
        result = runner_hooks.pause_for_review(
            "topic-gate", "EP01", {"hook": "a hook"}
        )

        # Submit recorded on the mock review client.
        assert patched_hooks.submit_review.called
        submit_kwargs = patched_hooks.submit_review.call_args.kwargs
        assert submit_kwargs["type"] == "topic-gate"
        assert submit_kwargs["content_ref"] == "EP01/p01_hook_topic"

        # Return shape (plan item 4).
        assert result["gate_id"] == "topic-gate"
        assert result["episode_id"] == "EP01"
        assert result["review_id"] == "rev-123"
        assert result["status"] == "pending"
        assert result["attempt"] == 1

        # State file written with awaiting_review.
        state_path = Path(".pipeline-state.json")
        assert state_path.exists(), "PipelineState file must be written"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["phases"]["p01_hook_topic"]["status"] == "awaiting_review"
        assert state["phases"]["p01_hook_topic"]["review_id"] == "rev-123"

    def test_degraded_envelope_auto_resolves_approve(
        self, patched_hooks, patch_gate_config
    ):
        """D-DEGRADE: review-platform degrade envelope → DEGRADED_AUTO disposition
        → gate auto-resolves "approve" (mirrors review_platform behavior)."""
        patched_hooks.submit_review.return_value = {
            "degraded": True,
            "state": "DEGRADED_AUTO",
            "disposition": "APPROVED",
        }

        result = runner_hooks.pause_for_review("topic-gate", "EP01", {})

        # Auto-approved: status is "approved", not "pending".
        assert result["status"] == "approved"
        # Gate was registered in pending cache (so callback path could resolve it).
        # For the auto-resolve branch the gate is already resolved; not pending.

    def test_callback_url_forwarded_when_configured(
        self, patched_hooks, monkeypatch
    ):
        """callback_url from GateConfig is forwarded to submit_review."""
        cfg = _gate_config(callback_url="https://example.com/cb")

        def _fake_to_gate_config(gate_id: str) -> GateConfig:
            return cfg

        monkeypatch.setattr(runner_hooks, "to_gate_config", _fake_to_gate_config)
        monkeypatch.chdir(Path("."))  # ensure cwd set
        # re-patch _review_client since this test skips patched_hooks fixture
        fake = MagicMock()
        fake.submit_review.return_value = {"review_id": "rev-cb"}
        monkeypatch.setattr(runner_hooks, "_review_client", lambda: fake)
        runner_hooks._PENDING_GATES.clear()

        runner_hooks.pause_for_review("topic-gate", "EP01", {})

        assert fake.submit_review.call_args.kwargs["callback_url"] == (
            "https://example.com/cb"
        )


# ────────────────── TestPauseForReviewMaxRetries ──────────────────


class TestPauseForReviewMaxRetries:
    """SC#5 / CF-05: max_retries exhaustion → GateMaxRetriesExceeded propagates,
    caller catches via mark_episode_failed → CONSISTENCY_BLOCKED marker written."""

    def test_max_retries_raises_and_propagates(
        self, patched_hooks, monkeypatch, tmp_path
    ):
        """attempt > max_retries → GateMaxRetriesExceeded; pause_for_review does
        NOT swallow it (PIPE-GUARD-01 anti-pattern check)."""
        # GateConfig with max_retries=0 → first submit attempt already exceeds.
        cfg = _gate_config(max_retries=0)

        def _fake_to_gate_config(gate_id: str) -> GateConfig:
            return cfg

        monkeypatch.setattr(runner_hooks, "to_gate_config", _fake_to_gate_config)

        with pytest.raises(GateMaxRetriesExceeded) as excinfo:
            runner_hooks.pause_for_review("topic-gate", "EP01", {})

        # Error message preserves PIPE-GUARD-01 marker.
        assert "CONSISTENCY_BLOCKED" in str(excinfo.value)

    def test_mark_episode_failed_writes_consistency_blocked(
        self, patched_hooks, patch_gate_config
    ):
        """mark_episode_failed writes PipelineState with status=failed + error
        starting with the literal 'CONSISTENCY_BLOCKED:' marker."""
        # Simulate the exception a caller would catch after retry exhaustion.
        # (Triggering it naturally is covered by
        # ``test_max_retries_raises_and_propagates`` above.)
        exc = GateMaxRetriesExceeded("topic-gate", attempts=3, max_retries=2)
        runner_hooks.mark_episode_failed("EP01", "topic-gate", exc)

        state = json.loads(
            Path(".pipeline-state.json").read_text(encoding="utf-8")
        )
        phase_state = state["phases"]["p01_hook_topic"]
        assert phase_state["status"] == "failed"
        assert phase_state["error"].startswith("CONSISTENCY_BLOCKED:")
        assert "topic-gate" in phase_state["error"]
        assert "failed_at" in phase_state
        # failed_at must be ISO-format-parseable.
        datetime.fromisoformat(phase_state["failed_at"])


# ────────────────── TestResumeFromCallbackApprove ──────────────────


class TestResumeFromCallbackApprove:
    """SC#3: webhook callback approve → resolve → write outcome + advance state."""

    def test_approve_callback_resolves_and_writes_outcome(
        self, patched_hooks, patch_gate_config
    ):
        """verify_callback True → gate.resolve("approve") → outcome appended to
        review-outcomes slot + PipelineState status advanced to "approved"."""
        # Pre-establish a pending gate (as if pause_for_review had run).
        cfg = patch_gate_config
        gate = Gate(config=cfg, episode_id="EP01", mode=GateMode.WEBHOOK)
        gate.attempt = 1
        gate.review_id = "rev-123"
        runner_hooks._PENDING_GATES["topic-gate"] = gate

        # Seed PipelineState with awaiting_review so we can assert it advances.
        from plugins.pipeline_state.store import PipelineState, PipelineStateStore

        store = PipelineStateStore(".")
        state = store.load()
        state.episode = "EP01"
        state.phases["p01_hook_topic"] = {
            "status": "awaiting_review",
            "review_id": "rev-123",
        }
        store.save(state)

        body = json.dumps(
            {
                "gate_id": "topic-gate",
                "decision": "approve",
                "review_id": "rev-123",
            }
        )
        result = runner_hooks.resume_from_callback(body, "sha256=valid", int(time.time()))

        assert result["decision"] == "approve"
        assert result["status"] == "approved"

        # Outcome written to asset bus.
        outcomes_path = Path(".pipeline-assets", "review-outcomes.json")
        assert outcomes_path.exists()
        outcomes_doc = json.loads(outcomes_path.read_text(encoding="utf-8"))
        # Account for v3.0 envelope wrapping.
        if "value" in outcomes_doc and outcomes_doc.get("schema_version") == "3.0":
            outcomes_doc = outcomes_doc["value"]
        assert outcomes_doc["version"] == 1
        assert any(
            o["gate_id"] == "topic-gate" and o["decision"] == "approve"
            for o in outcomes_doc["outcomes"]
        )

        # State advanced to approved.
        new_state = json.loads(
            Path(".pipeline-state.json").read_text(encoding="utf-8")
        )
        assert new_state["phases"]["p01_hook_topic"]["status"] == "approved"


# ────────────────── TestResumeFromCallbackReject ──────────────────


class TestResumeFromCallbackReject:
    """SC#4: reject with suggested_action → rollback marker recorded."""

    def test_reject_with_suggested_action_returns_rollback_target(
        self, patched_hooks, patch_gate_config
    ):
        """reject + suggested_action="rollback:p02_outline" → outcome written +
        returned dict carries rollback_to so Phase 35 runner can jump back."""
        cfg = patch_gate_config
        gate = Gate(config=cfg, episode_id="EP01", mode=GateMode.WEBHOOK)
        gate.attempt = 1
        gate.review_id = "rev-456"
        runner_hooks._PENDING_GATES["topic-gate"] = gate

        body = json.dumps(
            {
                "gate_id": "topic-gate",
                "decision": "reject",
                "suggested_action": "rollback:p02_outline",
                "review_id": "rev-456",
            }
        )
        result = runner_hooks.resume_from_callback(
            body, "sha256=valid", int(time.time())
        )

        assert result["decision"] == "reject"
        assert result["suggested_action"] == "rollback:p02_outline"
        # Rollback target surfaced for the runner.
        assert result.get("rollback_to") == "rollback:p02_outline"

        # Outcome written with suggested_action.
        outcomes_doc = json.loads(
            Path(".pipeline-assets", "review-outcomes.json").read_text("utf-8")
        )
        if outcomes_doc.get("schema_version") == "3.0":
            outcomes_doc = outcomes_doc["value"]
        assert any(
            o.get("suggested_action") == "rollback:p02_outline"
            for o in outcomes_doc["outcomes"]
        )


# ────────────────── TestResumeFromCallbackBadHMAC ──────────────────


class TestResumeFromCallbackBadHMAC:
    """SC#3: HMAC mismatch → PermissionError + NO state mutation."""

    def test_bad_hmac_raises_and_does_not_mutate(
        self, patched_hooks, patch_gate_config
    ):
        """verify_callback False → PermissionError("Invalid HMAC callback signature");
        no outcome written, no PipelineState change."""
        patched_hooks.verify_callback.return_value = False

        # Pre-populate state so we can detect mutation.
        from plugins.pipeline_state.store import PipelineStateStore

        store = PipelineStateStore(".")
        state = store.load()
        state.phases["p01_hook_topic"] = {"status": "awaiting_review"}
        store.save(state)
        state_before = json.loads(
            Path(".pipeline-state.json").read_text("utf-8")
        )

        body = json.dumps({"gate_id": "topic-gate", "decision": "approve"})
        with pytest.raises(PermissionError, match="Invalid HMAC callback signature"):
            runner_hooks.resume_from_callback(
                body, "sha256=bogus", int(time.time())
            )

        # No outcome file written.
        assert not Path(".pipeline-assets", "review-outcomes.json").exists()

        # State unchanged.
        state_after = json.loads(
            Path(".pipeline-state.json").read_text("utf-8")
        )
        assert state_after == state_before


# ────────────────── TestWriteReviewOutcome ──────────────────


class TestWriteReviewOutcome:
    """SC#4: outcome schema + append-not-overwrite semantics."""

    def test_appends_to_existing_outcomes(self, patched_hooks, patch_gate_config):
        """Second outcome appends; first outcome is preserved."""
        cfg = patch_gate_config
        gate1 = Gate(config=cfg, episode_id="EP01", mode=GateMode.WEBHOOK)
        gate1.attempt = 1
        outcome1 = gate1.resolve("approve")
        runner_hooks._write_review_outcome(gate1, outcome1)

        gate2 = Gate(config=cfg, episode_id="EP02", mode=GateMode.WEBHOOK)
        gate2.attempt = 1
        outcome2 = gate2.resolve("reject", suggested_action="rollback:p02_outline")
        runner_hooks._write_review_outcome(gate2, outcome2)

        doc = json.loads(
            Path(".pipeline-assets", "review-outcomes.json").read_text("utf-8")
        )
        if doc.get("schema_version") == "3.0":
            doc = doc["value"]
        assert len(doc["outcomes"]) == 2
        assert doc["outcomes"][0]["episode_id"] == "EP01"
        assert doc["outcomes"][1]["episode_id"] == "EP02"

    def test_outcome_record_matches_cf04_schema(self, patched_hooks, patch_gate_config):
        """Each outcome record carries the CF-04 schema fields."""
        cfg = patch_gate_config
        gate = Gate(config=cfg, episode_id="EP01", mode=GateMode.WEBHOOK)
        gate.attempt = 2
        outcome = gate.resolve("reject", suggested_action="rollback:p02_outline")

        runner_hooks._write_review_outcome(gate, outcome)

        doc = json.loads(
            Path(".pipeline-assets", "review-outcomes.json").read_text("utf-8")
        )
        if doc.get("schema_version") == "3.0":
            doc = doc["value"]
        assert doc["version"] == 1
        record = doc["outcomes"][-1]
        for required_field in (
            "gate_id",
            "episode_id",
            "decision",
            "suggested_action",
            "reviewer_role",
            "resolved_at",
            "attempt",
            "status",
        ):
            assert required_field in record, f"CF-04 field missing: {required_field}"
        assert record["attempt"] == 2
        assert record["reviewer_role"] == "creative_source"


# ────────────────── TestPollUntilTerminal ──────────────────


class TestPollUntilTerminal:
    """SC#1 polling mode: query loop + timeout."""

    def test_poll_returns_approved_when_platform_resolved(
        self, patched_hooks, patch_gate_config
    ):
        """query_review_status returns state="resolved", disposition="APPROVED"
        → poll_until_terminal returns the approved outcome."""
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-123",
            "state": "resolved",
            "disposition": "APPROVED",
        }

        result = runner_hooks.poll_until_terminal(
            "topic-gate", timeout_sec=5, interval_sec=1
        )

        assert result["decision"] == "approve"
        assert result["status"] == "approved"
        # Outcome written.
        assert Path(".pipeline-assets", "review-outcomes.json").exists()

    def test_poll_returns_timed_out_when_exceeds_timeout(
        self, patched_hooks, patch_gate_config
    ):
        """query_review_status never returns resolved → timeout_sec exceeded →
        returns timed_out outcome."""
        patched_hooks.query_review_status.return_value = {
            "review_id": "rev-123",
            "state": "pending",
        }

        start = time.monotonic()
        result = runner_hooks.poll_until_terminal(
            "topic-gate", timeout_sec=1, interval_sec=1
        )
        elapsed = time.monotonic() - start

        assert result["status"] == "timed_out"
        # Sanity: did not block longer than a reasonable upper bound.
        assert elapsed < 5


# ────────────────── TestMarkEpisodeFailed ──────────────────


class TestMarkEpisodeFailed:
    """CF-05 / PIPE-GUARD-01: episode-fail state write."""

    def test_writes_failed_status_with_error_marker(
        self, patched_hooks, patch_gate_config
    ):
        """mark_episode_failed writes status=failed + failed_at ISO + error field
        containing gate_id and attempt count."""
        exc = GateMaxRetriesExceeded(
            gate_id="topic-gate", attempts=3, max_retries=2
        )

        runner_hooks.mark_episode_failed("EP01", "topic-gate", exc)

        state = json.loads(
            Path(".pipeline-state.json").read_text("utf-8")
        )
        phase_state = state["phases"]["p01_hook_topic"]
        assert phase_state["status"] == "failed"
        assert "failed_at" in phase_state
        datetime.fromisoformat(phase_state["failed_at"])  # parseable ISO
        assert "topic-gate" in phase_state["error"]
        assert "3" in phase_state["error"]  # attempt count
