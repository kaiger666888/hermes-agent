"""test_feedback_validation.py - Phase 42-02 Task 2 (TDD RED->GREEN).

HMAC-SHA256 verification + 4-stage validation pipeline + feedback-data /
feedback-rejected JSONL persistence.

Pipeline order (LOCKED in CONTEXT.md):
    1. Signature (401)  - HMAC BEFORE json.loads (DoS mitigation)
    2. Schema (422)     - json.loads + required fields
    3. Semantic (400)   - metrics in [0,1], platform in valid set
    4. Episode (404)    - recipe_library.get_recipe_by_episode lookup

Structural invariant: ``self._rl`` is NEVER touched on signature/schema/
semantic failures — only after stage 4 passes (verified by Test 17).

Tests (18 total):
  TestVerifySignature (Tests 1-4): HMAC primitive edge cases.
  TestValidateSchema (Tests 5-7): JSON parsing + required fields.
  TestValidateSemantic (Tests 8-10): platform enum + metrics range.
  TestSubmitFeedbackPipeline (Tests 11-18): end-to-end pipeline behavior.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest

from plugins.kais_aigc.feedback_ingest import (
    FeedbackIngestClient,
    FeedbackValidationError,
    _validate_schema,
    _validate_semantic,
    _verify_signature,
)
from plugins.pipeline_state.asset_bus import AssetBus


# ─── Shared fixtures ──────────────────────────────────────────────────

SECRET = "test-secret-abc123"

_VALID_PAYLOAD: dict[str, Any] = {
    "episode_id": "ep-001",
    "platform": "douyin",
    "metrics": {
        "completion_rate": 0.48,
        "interaction_rate": 0.12,
        "follow_rate": 0.03,
    },
    "measured_at": "2026-06-27T10:30:00Z",
}


def _valid_body() -> bytes:
    return json.dumps(_VALID_PAYLOAD).encode("utf-8")


def _sign(body: bytes, secret: str = SECRET) -> str:
    """Produce a valid X-Signature header value for the given body."""
    return "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256,
    ).hexdigest()


class _RecordingRecipeLibrary:
    """Minimal RecipeLibrary stub that records update_validation calls.

    Tracks call count + last args so Test 17 can assert 'NEVER touched on
    failure' and Test 12 can assert the exact call args.
    """

    def __init__(self, *, episode_to_recipe: dict[str, dict] | None = None) -> None:
        self._episode_to_recipe = episode_to_recipe or {}
        self.update_call_count = 0
        self.last_update_args: dict[str, Any] | None = None

    def get_recipe_by_episode(self, source_episode: str) -> dict | None:
        return self._episode_to_recipe.get(source_episode)

    def update_validation(self, *args: Any, **kwargs: Any) -> dict:
        self.update_call_count += 1
        self.last_update_args = {"args": args, "kwargs": kwargs}
        # Return a minimal plausible row.
        return {
            "recipe_id": kwargs.get("recipe_id") or (args[0] if args else "?"),
            "version": 2,
            "validation": {"platform": kwargs.get("platform"), "sample_size": 1},
        }


@pytest.fixture
def bus(tmp_path) -> AssetBus:
    return AssetBus(tmp_path)


@pytest.fixture
def recipe_with_episode() -> _RecordingRecipeLibrary:
    """RecipeLibrary stub that knows about episode 'ep-001'."""
    return _RecordingRecipeLibrary(
        episode_to_recipe={
            "ep-001": {"recipe_id": "test-001", "version": 1, "provenance": {"source_episode": "ep-001"}},
        },
    )


@pytest.fixture
def empty_recipe() -> _RecordingRecipeLibrary:
    """RecipeLibrary stub that knows about no episodes."""
    return _RecordingRecipeLibrary()


# ═══════════════════════════════════════════════════════════════════
# Tests 1-4: _verify_signature primitive
# ═══════════════════════════════════════════════════════════════════
class TestVerifySignature:
    # Test 1: valid signature -> True
    def test_valid_signature_returns_true(self):
        body = _valid_body()
        sig = _sign(body)
        assert _verify_signature(body, sig, SECRET) is True

    # Test 2: invalid signature -> False (NOT raise)
    def test_invalid_signature_returns_false(self):
        body = _valid_body()
        assert _verify_signature(body, "sha256=invalid", SECRET) is False

    # Test 3: None/empty secret -> False (NO dev-mode escape)
    def test_no_secret_returns_false(self):
        body = _valid_body()
        sig = _sign(body)
        # Phase 42 ALWAYS requires a secret — NO dev-mode escape.
        assert _verify_signature(body, sig, None) is False
        assert _verify_signature(body, sig, "") is False

    # Test 4: signature without sha256= prefix -> False
    def test_signature_without_prefix_returns_false(self):
        body = _valid_body()
        # Compute the hex without the prefix.
        raw_hex = hmac.new(
            SECRET.encode("utf-8"), body, hashlib.sha256,
        ).hexdigest()
        assert _verify_signature(body, raw_hex, SECRET) is False


# ═══════════════════════════════════════════════════════════════════
# Tests 5-7: _validate_schema
# ═══════════════════════════════════════════════════════════════════
class TestValidateSchema:
    # Test 5: valid body -> parsed dict
    def test_valid_body_returns_parsed_dict(self):
        body = _valid_body()
        result = _validate_schema(body)
        assert isinstance(result, dict)
        assert result["episode_id"] == "ep-001"
        assert result["platform"] == "douyin"
        assert "metrics" in result
        assert "measured_at" in result

    # Test 6: malformed JSON -> FeedbackValidationError(reason='schema', 422)
    def test_malformed_json_raises_schema_error(self):
        with pytest.raises(FeedbackValidationError) as exc_info:
            _validate_schema(b'malformed json{{{')
        assert exc_info.value.reason == "schema"
        assert exc_info.value.http_status == 422

    # Test 7: missing required fields -> FeedbackValidationError(reason='schema', 422)
    def test_missing_fields_raises_schema_error(self):
        # Only episode_id present, missing platform/metrics/measured_at.
        body = b'{"episode_id":"ep-001"}'
        with pytest.raises(FeedbackValidationError) as exc_info:
            _validate_schema(body)
        assert exc_info.value.reason == "schema"
        assert exc_info.value.http_status == 422

    # Additional check: missing required metric field
    def test_missing_metric_field_raises_schema_error(self):
        body = json.dumps({
            "episode_id": "ep-001",
            "platform": "douyin",
            "metrics": {"completion_rate": 0.5, "interaction_rate": 0.1},  # no follow_rate
            "measured_at": "2026-06-27T10:30:00Z",
        }).encode("utf-8")
        with pytest.raises(FeedbackValidationError) as exc_info:
            _validate_schema(body)
        assert exc_info.value.reason == "schema"


# ═══════════════════════════════════════════════════════════════════
# Tests 8-10: _validate_semantic
# ═══════════════════════════════════════════════════════════════════
class TestValidateSemantic:
    # Test 8: valid payload -> None (passes silently)
    def test_valid_payload_returns_none(self):
        _validate_semantic(_VALID_PAYLOAD)  # no exception

    # Test 9: unknown platform -> SemanticError (reason='semantic', 400)
    def test_unknown_platform_raises_semantic_error(self):
        bad = {**_VALID_PAYLOAD, "platform": "twitter"}
        with pytest.raises(FeedbackValidationError) as exc_info:
            _validate_semantic(bad)
        assert exc_info.value.reason == "semantic"
        assert exc_info.value.http_status == 400

    # Test 10: metric out of [0,1] -> SemanticError
    def test_out_of_range_metric_raises_semantic_error(self):
        bad = {
            **_VALID_PAYLOAD,
            "metrics": {
                "completion_rate": 1.5,  # > 1.0
                "interaction_rate": 0.12,
                "follow_rate": 0.03,
            },
        }
        with pytest.raises(FeedbackValidationError) as exc_info:
            _validate_semantic(bad)
        assert exc_info.value.reason == "semantic"
        assert exc_info.value.http_status == 400


# ═══════════════════════════════════════════════════════════════════
# Tests 11-18: submit_feedback pipeline end-to-end
# ═══════════════════════════════════════════════════════════════════
class TestSubmitFeedbackPipeline:
    # Test 11: valid submission -> writes 1 line to feedback-data slot,
    # returns status='accepted', recipe_id matches the looked-up recipe.
    def test_valid_submission_writes_feedback_data(
        self, bus, recipe_with_episode,
    ):
        body = _valid_body()
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        result = client.submit_feedback(body, sig)
        assert result["status"] == "accepted"
        assert result["recipe_id"] == "test-001"
        # feedback-data slot has exactly 1 record.
        rows = bus.read_lines("feedback-data")
        assert len(rows) == 1
        rec = rows[0]
        assert rec["episode_id"] == "ep-001"
        assert rec["platform"] == "douyin"
        assert rec["signature_valid"] is True
        assert rec["feedback_id"] == result["feedback_id"]

    # Test 12: valid submission calls recipe_library.update_validation with
    # use_continuous_rate=True and the completion_rate from the payload.
    def test_valid_submission_calls_update_validation_with_continuous_rate(
        self, bus, recipe_with_episode,
    ):
        body = _valid_body()
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        client.submit_feedback(body, sig)
        assert recipe_with_episode.update_call_count == 1
        args = recipe_with_episode.last_update_args["args"]
        kwargs = recipe_with_episode.last_update_args["kwargs"]
        # Positional: (recipe_id, platform, completion_rate)
        assert args[0] == "test-001"            # recipe_id from recipe_with_episode
        assert args[1] == "douyin"              # platform
        assert args[2] == pytest.approx(0.48)   # completion_rate
        # Keyword: sample_size_delta + use_continuous_rate
        assert kwargs["sample_size_delta"] == 1
        assert kwargs["use_continuous_rate"] is True

    # Test 13: invalid signature -> 401 rejected, writes to feedback-rejected
    def test_invalid_signature_returns_401_and_logs_rejection(
        self, bus, recipe_with_episode,
    ):
        body = _valid_body()
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        result = client.submit_feedback(body, "sha256=invalid")
        assert result["status"] == "rejected"
        assert result["reason"] == "signature"
        assert result["http_status"] == 401
        # feedback-rejected has exactly 1 line.
        rej = bus.read_lines("feedback-rejected")
        assert len(rej) == 1
        assert rej[0]["reason"] == "signature"
        assert "feedback_id" in rej[0]
        assert "payload_snippet" in rej[0]
        assert "timestamp" in rej[0]
        # feedback-data MUST be empty (no accepted record on rejection).
        assert bus.read_lines("feedback-data") == []

    # Test 14: malformed JSON -> 422 schema rejected
    def test_malformed_json_returns_422_and_logs_rejection(
        self, bus, recipe_with_episode,
    ):
        body = b'malformed json{{{'
        # Sign the malformed body — the signature must match what we send,
        # so we get past stage 1 and hit stage 2 (schema).
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        result = client.submit_feedback(body, sig)
        assert result["status"] == "rejected"
        assert result["reason"] == "schema"
        assert result["http_status"] == 422
        rej = bus.read_lines("feedback-rejected")
        assert len(rej) == 1
        assert rej[0]["reason"] == "schema"

    # Test 15: out-of-range metrics -> 400 semantic rejected
    def test_out_of_range_metrics_returns_400_and_logs_rejection(
        self, bus, recipe_with_episode,
    ):
        bad_payload = {
            **_VALID_PAYLOAD,
            "metrics": {
                "completion_rate": 1.5,
                "interaction_rate": 0.12,
                "follow_rate": 0.03,
            },
        }
        body = json.dumps(bad_payload).encode("utf-8")
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        result = client.submit_feedback(body, sig)
        assert result["status"] == "rejected"
        assert result["reason"] == "semantic"
        assert result["http_status"] == 400
        rej = bus.read_lines("feedback-rejected")
        assert len(rej) == 1
        assert rej[0]["reason"] == "semantic"

    # Test 16: unknown episode -> 404 episode_not_found rejected
    def test_unknown_episode_returns_404_and_logs_rejection(
        self, bus, empty_recipe,
    ):
        body = _valid_body()
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=empty_recipe, secret=SECRET,
        )
        result = client.submit_feedback(body, sig)
        assert result["status"] == "rejected"
        assert result["reason"] == "episode_not_found"
        assert result["http_status"] == 404
        rej = bus.read_lines("feedback-rejected")
        assert len(rej) == 1
        assert rej[0]["reason"] == "episode_not_found"

    # Test 17: RecipeLibrary.update_validation NEVER called on any rejection
    @pytest.mark.parametrize("bad_sig,body,expected_reason", [
        ("sha256=invalid", _valid_body(), "signature"),
        (_sign(b'malformed{'), b'malformed{', "schema"),
        # Semantic + episode_not_found tested separately above (calls counted).
    ])
    def test_recipe_library_never_touched_on_rejection(
        self, bus, recipe_with_episode, bad_sig, body, expected_reason,
    ):
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        client.submit_feedback(body, bad_sig)
        assert recipe_with_episode.update_call_count == 0, (
            f"recipe_library.update_validation was called {recipe_with_episode.update_call_count} "
            f"times on a '{expected_reason}' rejection — structural invariant violated "
            "(self._rl must NEVER be touched on signature/schema/semantic failures)."
        )

    # Test 17b: explicit check for semantic + episode_not_found call counts
    def test_recipe_library_never_touched_on_semantic_or_episode_rejection(
        self, bus, recipe_with_episode, empty_recipe,
    ):
        # Semantic rejection (recipe_with_episode so we get past stages 1-3
        # but stage 3 semantic fails — recipe_library untouched).
        bad_payload = {
            **_VALID_PAYLOAD,
            "platform": "twitter",
        }
        body = json.dumps(bad_payload).encode("utf-8")
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        client.submit_feedback(body, sig)
        assert recipe_with_episode.update_call_count == 0

        # Episode_not_found rejection (stages 1-3 pass, stage 4 fails —
        # recipe_library.get_recipe_by_episode IS called, but update_validation
        # is NOT).
        body_ok = _valid_body()
        sig_ok = _sign(body_ok)
        client2 = FeedbackIngestClient(
            asset_bus=bus, recipe_library=empty_recipe, secret=SECRET,
        )
        client2.submit_feedback(body_ok, sig_ok)
        assert empty_recipe.update_call_count == 0

    # Test 18: feedback_id is a stable sha256[:16] hash of the body
    def test_feedback_id_is_stable_sha256_hash(self, bus, recipe_with_episode):
        body = _valid_body()
        sig = _sign(body)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        result = client.submit_feedback(body, sig)
        expected_id = hashlib.sha256(body).hexdigest()[:16]
        assert result["feedback_id"] == expected_id
        # Re-submitting the same body produces the same feedback_id.
        result2 = client.submit_feedback(body, sig)
        assert result2["feedback_id"] == expected_id
