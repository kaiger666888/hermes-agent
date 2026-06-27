"""test_feedback_ingest_skeleton.py - Phase 42-01 Task 2 (TDD RED->GREEN).

Verifies the FeedbackIngestClient skeleton created in
plugins/kais_aigc/feedback_ingest.py per plan 42-01. The skeleton ships
``__init__`` + ``get_feedback`` + ``submit_feedback`` stub; full impl
arrives in 42-02 (HMAC + validation) and 42-03 (HTTP server wiring).

Tests (10 total):
  1.  Constructor with asset_bus + recipe_library succeeds
  2.  Constructor without asset_bus raises ValueError
  3.  Constructor without recipe_library raises ValueError
  4.  get_feedback() returns list (empty when slot empty)
  5.  get_feedback() returns appended records
  6.  get_feedback(episode_id=...) filters by episode_id
  7.  submit_feedback(body, signature) returns stub not_implemented envelope
  8.  Context-manager protocol (__enter__ / __exit__ -> close)
  9.  KAIS_FEEDBACK_PORT env var honored (default 8091)
  10. KAIS_FEEDBACK_SECRET env var honored (None if unset - dev mode)
"""

from __future__ import annotations

import os

import pytest

from plugins.kais_aigc.feedback_ingest import FeedbackIngestClient
from plugins.pipeline_state.asset_bus import AssetBus


# ===================================================================
# Fakes
# ===================================================================

class _FakeRecipeLibrary:
    """Minimal RecipeLibrary stub.

    Phase 42-01 skeleton does NOT call any RecipeLibrary methods - the
    real integration (update_validation) lands in 42-02. The stub exists
    purely so the constructor's recipe_library requirement can be
    exercised.
    """
    pass


@pytest.fixture
def bus(tmp_path) -> AssetBus:
    return AssetBus(tmp_path)


@pytest.fixture
def recipe_library() -> _FakeRecipeLibrary:
    return _FakeRecipeLibrary()


# ===================================================================
# Tests 1-3: Constructor validation
# ===================================================================
class TestConstructor:
    def test_constructs_with_required_args(self, bus, recipe_library):
        """Test 1: FeedbackIngestClient(asset_bus=bus, recipe_library=rl)
        constructs without error."""
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        assert client is not None

    def test_raises_on_missing_asset_bus(self, recipe_library):
        """Test 2: asset_bus=None raises ValueError (required constructor arg)."""
        with pytest.raises(ValueError, match="asset_bus required"):
            FeedbackIngestClient(asset_bus=None, recipe_library=recipe_library)

    def test_raises_on_missing_recipe_library(self, bus):
        """Test 3: recipe_library=None raises ValueError (required constructor arg)."""
        with pytest.raises(ValueError, match="recipe_library required"):
            FeedbackIngestClient(asset_bus=bus, recipe_library=None)


# ===================================================================
# Tests 4-6: get_feedback
# ===================================================================
class TestGetFeedback:
    def test_returns_empty_list_when_slot_empty(self, bus, recipe_library):
        """Test 4: get_feedback() returns [] when feedback-data slot is empty."""
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        assert client.get_feedback() == []

    def test_returns_appended_records(self, bus, recipe_library):
        """Test 5: After bus.append_line('feedback-data', {...}),
        client.get_feedback() returns [that dict]."""
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        bus.append_line(
            "feedback-data",
            {"feedback_id": "fb-001", "episode_id": "ep-001"},
        )
        rows = client.get_feedback()
        assert len(rows) == 1
        assert rows[0]["feedback_id"] == "fb-001"
        assert rows[0]["episode_id"] == "ep-001"

    def test_filters_by_episode_id(self, bus, recipe_library):
        """Test 6: get_feedback(episode_id='ep-001') filters to matching records."""
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        bus.append_line(
            "feedback-data",
            {"feedback_id": "fb-001", "episode_id": "ep-001"},
        )
        bus.append_line(
            "feedback-data",
            {"feedback_id": "fb-002", "episode_id": "ep-002"},
        )
        bus.append_line(
            "feedback-data",
            {"feedback_id": "fb-003", "episode_id": "ep-001"},
        )

        rows = client.get_feedback(episode_id="ep-001")
        assert len(rows) == 2
        assert {r["feedback_id"] for r in rows} == {"fb-001", "fb-003"}


# ===================================================================
# Test 7: submit_feedback stub
# ===================================================================
class TestSubmitFeedbackStub:
    def test_submit_feedback_returns_not_implemented_envelope(
        self, bus, recipe_library,
    ):
        """Test 7: submit_feedback(body, signature) exists and returns the
        documented stub envelope (full impl arrives in 42-02/03)."""
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        result = client.submit_feedback(b'{"x": 1}', "sha256=abc")
        assert isinstance(result, dict)
        assert result.get("status") == "not_implemented"
        assert "reason" in result
        # The stub reason should mention 42-02 / 42-03 so future plans can
        # grep for the deferred-impl marker.
        assert "42-02" in result["reason"] or "42-03" in result["reason"], (
            f"stub reason should reference 42-02/42-03; got {result['reason']!r}"
        )


# ===================================================================
# Test 8: Context-manager protocol
# ===================================================================
class TestContextManager:
    def test_context_manager_protocol(self, bus, recipe_library):
        """Test 8: FeedbackIngestClient supports __enter__/__exit__ and
        __exit__ calls close() without error."""
        with FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        ) as client:
            assert client is not None
            # close() should be idempotent - safe to call within the block
            client.close()


# ===================================================================
# Tests 9-10: Env var configuration (D-06: read at construction time)
# ===================================================================
class TestEnvVarConfig:
    def test_reads_kais_feedback_port_from_env(
        self, bus, recipe_library, monkeypatch,
    ):
        """Test 9: KAIS_FEEDBACK_PORT env var honored at construction.
        Default 8091 if unset (CONTEXT.md decision: sibling to gold-team
        :8002 and review :8090)."""
        monkeypatch.setenv("KAIS_FEEDBACK_PORT", "9999")
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        assert client._port == 9999

        monkeypatch.delenv("KAIS_FEEDBACK_PORT", raising=False)
        client2 = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        assert client2._port == 8091, (
            "KAIS_FEEDBACK_PORT unset should fall back to default 8091"
        )

    def test_reads_kais_feedback_secret_from_env(
        self, bus, recipe_library, monkeypatch,
    ):
        """Test 10: KAIS_FEEDBACK_SECRET env var honored at construction.
        None if unset (dev mode)."""
        monkeypatch.setenv("KAIS_FEEDBACK_SECRET", "topsecret")
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        assert client._secret == "topsecret"

        monkeypatch.delenv("KAIS_FEEDBACK_SECRET", raising=False)
        client2 = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_library,
        )
        assert client2._secret is None, (
            "KAIS_FEEDBACK_SECRET unset should be None (dev mode)"
        )
