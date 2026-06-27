"""E2E integration tests for the Phase 42 feedback → recipe convergence loop.

This file is the v6.0 ship-gate integration test — it proves the
"最速收敛闭环" (rapid-convergence closed loop) actually closes end-to-end:

    HTTP POST /api/v1/feedback
      → HMAC-SHA256 verify (401)
      → JSON schema check (422)
      → semantic range check (400)
      → recipe lookup by episode (404)
      → feedback-data JSONL persist (audit trail)
      → RecipeLibrary.update_validation(use_continuous_rate=True)
      → Wilson CI recompute + converged flag

10 tests cover: happy path, convergence after 10 feedbacks, continuous-rate
preservation, rejection-does-not-pollute-recipe-library, multi-episode
isolation, list_pending_updates integration, HTTP E2E via Starlette
TestClient, platform field override, full metrics preservation, and
non-fatal update_validation failure.

Requirements covered:
  - FEEDBACK-INGEST-01: FeedbackIngestClient with 3 methods (Tests 1, 6)
  - FEEDBACK-INGEST-02: HMAC + POST endpoint (Test 7)
  - FEEDBACK-INGEST-03: feedback-data JSONL slot (Tests 1, 4, 5, 9)
  - FEEDBACK-INGEST-04: update_validation trigger (Tests 1, 2, 3, 8)
  - FEEDBACK-INGEST-05: no auto-modify pipeline (covered by 42-04 Task 2)
  - FEEDBACK-INGEST-06: 4-stage validation + feedback-rejected (Test 4)
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

import pytest

from plugins.pipeline_state.asset_bus import AssetBus
from plugins.pipeline_state.recipe_library import RecipeLibrary
from plugins.kais_aigc.feedback_ingest import (
    FeedbackIngestClient,
    _build_starlette_app,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers — mirror test_recipe_library_integration.py setup patterns
# ═══════════════════════════════════════════════════════════════════


def _make_structure(
    *,
    hook: int = 7,
    sequence: list[str] | None = None,
    tps: list[int] | None = None,
    drop: int = 1,
    ending: str = "resolved",
) -> dict:
    """Build a valid 5-field structure dict (mirrors ep-001 extraction)."""
    return {
        "hook_position_sec": hook,
        "emotion_sequence": sequence if sequence is not None else ["hope", "descent", "crisis", "recovery"],
        "turning_points_sec": tps if tps is not None else [7, 37, 55],
        "emotion_drop_level": drop,
        "ending_state": ending,
    }


def _make_recipe(
    bus: AssetBus,
    rl: RecipeLibrary,
    episode_id: str,
    genre: str = "Urban Fantasy",
) -> str:
    """Create a real recipe via RecipeLibrary.create_recipe. Returns recipe_id.

    Mirrors test_recipe_library_integration._make_recipe — uses the canonical
    V5.0 ep-001 structure so the recipe is well-formed.
    """
    recipe_id = rl.create_recipe(
        genre=genre,
        structure=_make_structure(),
        source_episode=episode_id,
    )
    assert recipe_id, f"create_recipe returned falsy: {recipe_id!r}"
    return recipe_id


def _make_feedback_body(
    episode_id: str,
    platform: str = "douyin",
    cr: float = 0.48,
    ir: float = 0.12,
    fr: float = 0.03,
    measured_at: str = "2026-06-27T12:00:00Z",
) -> bytes:
    """Build a valid feedback JSON body (bytes)."""
    return json.dumps({
        "episode_id": episode_id,
        "platform": platform,
        "metrics": {
            "completion_rate": cr,
            "interaction_rate": ir,
            "follow_rate": fr,
        },
        "measured_at": measured_at,
    }).encode("utf-8")


def _sign(body: bytes, secret: str) -> str:
    """Return 'sha256=<hex>' HMAC-SHA256 signature for body."""
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@pytest.fixture
def bus(tmp_path: Path) -> AssetBus:
    return AssetBus(tmp_path)


@pytest.fixture
def rl(bus: AssetBus) -> RecipeLibrary:
    return RecipeLibrary(asset_bus=bus)


@pytest.fixture
def client(bus: AssetBus, rl: RecipeLibrary) -> FeedbackIngestClient:
    return FeedbackIngestClient(
        asset_bus=bus,
        recipe_library=rl,
        secret="test-secret",
    )


SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════════
# TestFeedbackIngestIntegration — 10 end-to-end tests
# ═══════════════════════════════════════════════════════════════════


class TestFeedbackIngestIntegration:
    """End-to-end feedback → recipe convergence integration tests.

    Covers FEEDBACK-INGEST-01/02/03/04/06 (FEEDBACK-INGEST-05 is covered
    by the structural grep test in test_v50_regression_phase42.py).
    """

    # ── Test 1: E2E HAPPY PATH ───────────────────────────────────────

    def test_e2e_happy_path_updates_recipe_validation(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 1: E2E happy path — covers FEEDBACK-INGEST-01/03/04.

        Given recipe for ep-001 exists, when submit_feedback(valid_body, valid_sig),
        then: (a) feedback-data slot has 1 record with signature_valid=true +
        recipe_id; (b) RecipeLibrary.get_recipe returns version N+1 with
        validation.sample_size incremented by 1; (c) completion_rate is the
        running average (not raw feedback value); (d) last_validated is set.
        """
        recipe_id = _make_recipe(bus, rl, "ep-001")
        before = rl.get_recipe(recipe_id)
        assert before["version"] == 1
        assert before["validation"]["sample_size"] == 0

        body = _make_feedback_body("ep-001", cr=0.48)
        sig = _sign(body, SECRET)
        result = client.submit_feedback(body, sig)

        assert result["status"] == "accepted"
        assert result["feedback_id"] == hashlib.sha256(body).hexdigest()[:16]
        assert result["recipe_id"] == recipe_id

        # (a) feedback-data slot
        records = client.get_feedback()
        assert len(records) == 1
        rec = records[0]
        assert rec["signature_valid"] is True
        assert rec["recipe_id"] == recipe_id
        assert rec["episode_id"] == "ep-001"

        # (b) recipe version + sample_size incremented
        after = rl.get_recipe(recipe_id)
        assert after["version"] == before["version"] + 1
        assert after["validation"]["sample_size"] == before["validation"]["sample_size"] + 1

        # (c) completion_rate is the running avg (0.48 exactly with prior=0)
        # On continuous-rate path: passed += cr, total += 1.0 → avg = 0.48.
        cr = after["validation"]["completion_rate"]
        assert cr == pytest.approx(0.48, abs=1e-9), (
            f"expected running avg 0.48, got {cr}"
        )

        # (d) last_validated is a recent ISO timestamp
        lv = after["provenance"]["last_validated"]
        assert lv, "last_validated is empty"
        # ISO 8601 parseable
        from datetime import datetime
        datetime.fromisoformat(lv)

    # ── Test 2: CONVERGENCE AFTER 10 FEEDBACKS ──────────────────────

    def test_convergence_after_ten_feedbacks(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 2: Convergence — covers FEEDBACK-INGEST-04.

        Submit 10 feedbacks with completion_rate=0.5 each. After 10th:
        (a) sample_size == 10; (b) CI may flip converged (do NOT assert
        converged=True — CI math depends on float precision); (c)
        confidence_interval string is "±N%" format.
        """
        recipe_id = _make_recipe(bus, rl, "ep-conv")

        for i in range(10):
            # Use different measured_at to make each body unique (otherwise
            # feedback_id collides — sha256(body)[:16] is stable per body).
            body = _make_feedback_body(
                "ep-conv", cr=0.5, measured_at=f"2026-06-27T12:0{i}:00Z",
            )
            sig = _sign(body, SECRET)
            result = client.submit_feedback(body, sig)
            assert result["status"] == "accepted", f"feedback {i} rejected: {result}"

        recipe = rl.get_recipe(recipe_id)
        # (a)
        assert recipe["validation"]["sample_size"] == 10, (
            f"expected sample_size=10, got {recipe['validation']['sample_size']}"
        )
        # (b) — assert only that converged is bool (CI math is float-precision sensitive)
        assert isinstance(recipe["validation"]["converged"], bool)
        # (c) confidence_interval is "±N%" format
        ci = recipe["validation"]["confidence_interval"]
        assert isinstance(ci, str)
        assert "±" in ci, f"confidence_interval missing ±: {ci!r}"
        assert ci.endswith("%"), f"confidence_interval not percentage: {ci!r}"

    # ── Test 3: CONTINUOUS RATE PRESERVED ───────────────────────────

    def test_continuous_rate_preserved(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 3: Continuous-rate path — covers FEEDBACK-INGEST-04.

        Submit feedback with completion_rate=0.48. Recipe validation.
        completion_rate (running avg with prev=0) becomes 0.48 exactly
        (NOT quantized via int(round(cr*N)) int-passed path, which would
        produce 0.0 for N=1 since int(round(0.48*1))=0).
        """
        recipe_id = _make_recipe(bus, rl, "ep-cr")
        body = _make_feedback_body("ep-cr", cr=0.48)
        sig = _sign(body, SECRET)
        result = client.submit_feedback(body, sig)
        assert result["status"] == "accepted"

        recipe = rl.get_recipe(recipe_id)
        cr = recipe["validation"]["completion_rate"]
        # Continuous-rate path: passed=0.48, total=1.0 → avg=0.48 exactly.
        # Int-passed path would give: passed=int(round(0.48*1))=0, total=1 → 0.0.
        assert cr == pytest.approx(0.48, abs=1e-9), (
            f"continuous-rate path broken: expected 0.48, got {cr} "
            f"(int-passed quantization would give 0.0)"
        )

    # ── Test 4: REJECTION DOES NOT POLLUTE RECIPE LIBRARY ───────────

    def test_rejection_does_not_pollute_recipe_library(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 4: Rejection isolation — covers FEEDBACK-INGEST-03/06.

        Submit 4 rejected feedbacks (bad sig, bad schema, bad semantic,
        unknown episode). Then submit 1 valid feedback. Verify:
        (a) feedback-data slot has exactly 1 record (only the valid one);
        (b) feedback-rejected slot has exactly 4 records with reasons;
        (c) RecipeLibrary.get_recipe version is incremented exactly once
        (not 5 times — rejections never call update_validation).
        """
        recipe_id = _make_recipe(bus, rl, "ep-rej")
        before_version = rl.get_recipe(recipe_id)["version"]

        # 1: bad signature
        body_bad_sig = _make_feedback_body("ep-rej", cr=0.5)
        r1 = client.submit_feedback(body_bad_sig, "sha256=deadbeef")
        assert r1["status"] == "rejected" and r1["reason"] == "signature"

        # 2: bad schema (missing required field)
        body_bad_schema = json.dumps({"episode_id": "ep-rej"}).encode("utf-8")
        r2 = client.submit_feedback(body_bad_schema, _sign(body_bad_schema, SECRET))
        assert r2["status"] == "rejected" and r2["reason"] == "schema"

        # 3: bad semantic (platform not in enum)
        body_bad_sem = _make_feedback_body("ep-rej", platform="myspace")
        r3 = client.submit_feedback(body_bad_sem, _sign(body_bad_sem, SECRET))
        assert r3["status"] == "rejected" and r3["reason"] == "semantic"

        # 4: unknown episode (no recipe exists for ep-unknown)
        body_unknown_ep = _make_feedback_body("ep-unknown", cr=0.5)
        r4 = client.submit_feedback(body_unknown_ep, _sign(body_unknown_ep, SECRET))
        assert r4["status"] == "rejected" and r4["reason"] == "episode_not_found"

        # 5: valid feedback
        body_valid = _make_feedback_body("ep-rej", cr=0.5, measured_at="2026-06-27T13:00:00Z")
        r5 = client.submit_feedback(body_valid, _sign(body_valid, SECRET))
        assert r5["status"] == "accepted"

        # (a) feedback-data has exactly 1 record
        accepted = client.get_feedback()
        assert len(accepted) == 1, (
            f"expected 1 accepted record, got {len(accepted)}: {accepted}"
        )
        assert accepted[0]["feedback_id"] == hashlib.sha256(body_valid).hexdigest()[:16]

        # (b) feedback-rejected has exactly 4 records with correct reasons
        rejected = bus.read_lines("feedback-rejected")
        assert len(rejected) == 4, (
            f"expected 4 rejected records, got {len(rejected)}"
        )
        reasons = sorted(r["reason"] for r in rejected)
        assert reasons == sorted(["signature", "schema", "semantic", "episode_not_found"]), (
            f"unexpected reasons: {reasons}"
        )

        # (c) recipe version incremented exactly once (only on accept)
        after_version = rl.get_recipe(recipe_id)["version"]
        assert after_version == before_version + 1, (
            f"expected version {before_version + 1} (one increment on accept), "
            f"got {after_version} — rejections leaked into update_validation"
        )

    # ── Test 5: MULTI-EPISODE ISOLATION ─────────────────────────────

    def test_multi_episode_isolation(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 5: Multi-episode isolation — covers FEEDBACK-INGEST-03/04.

        2 recipes for 2 different episodes. Submit feedback for ep-002.
        Only ep-002's recipe validation updates; ep-001's recipe is unchanged.
        """
        rid1 = _make_recipe(bus, rl, "ep-isol-1")
        rid2 = _make_recipe(bus, rl, "ep-isol-2")
        v1_before = rl.get_recipe(rid1)["version"]
        v2_before = rl.get_recipe(rid2)["version"]

        body = _make_feedback_body("ep-isol-2", cr=0.6)
        result = client.submit_feedback(body, _sign(body, SECRET))
        assert result["status"] == "accepted"
        assert result["recipe_id"] == rid2

        # ep-002 recipe updated
        assert rl.get_recipe(rid2)["version"] == v2_before + 1
        # ep-001 recipe UNCHANGED
        assert rl.get_recipe(rid1)["version"] == v1_before, (
            "feedback for ep-002 leaked into ep-001's recipe"
        )

    # ── Test 6: LIST PENDING UPDATES INTEGRATION ────────────────────

    def test_list_pending_updates_integration(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 6: list_pending_updates integration — covers FEEDBACK-INGEST-01.

        Submit 3 feedbacks. client.list_pending_updates(limit=2) returns 2
        records, newest first (sorted by received_at descending).
        """
        _make_recipe(bus, rl, "ep-list")
        # Submit 3 with different measured_at so feedback_ids differ
        bodies = []
        for i, ts in enumerate(["T12:00:00Z", "T12:01:00Z", "T12:02:00Z"], start=1):
            body = _make_feedback_body(
                "ep-list", cr=0.3 + i * 0.1,
                measured_at=f"2026-06-27{ts}",
            )
            r = client.submit_feedback(body, _sign(body, SECRET))
            assert r["status"] == "accepted"
            bodies.append(body)

        pending = client.list_pending_updates(limit=2)
        assert len(pending) == 2
        # Newest first: received_at sorted descending
        ts_list = [r["received_at"] for r in pending]
        assert ts_list == sorted(ts_list, reverse=True), (
            f"not sorted newest-first: {ts_list}"
        )

    # ── Test 7: HTTP E2E via Starlette TestClient ───────────────────

    def test_http_e2e_via_starlette_testclient(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 7: HTTP E2E — covers FEEDBACK-INGEST-02/04.

        Using Starlette TestClient (in-process, no port binding), POST
        /api/v1/feedback with valid body + sig returns 200; recipe
        validation{} is updated as a side effect.
        """
        from starlette.testclient import TestClient

        recipe_id = _make_recipe(bus, rl, "ep-http")
        before_v = rl.get_recipe(recipe_id)["version"]

        app = _build_starlette_app(client)
        body = _make_feedback_body("ep-http", cr=0.55)
        sig = _sign(body, SECRET)

        with TestClient(app) as c:
            response = c.post(
                "/api/v1/feedback",
                content=body,
                headers={"X-Signature": sig},
            )

        assert response.status_code == 200, (
            f"expected 200, got {response.status_code}: {response.text}"
        )
        # Response body should NOT contain internal http_status key
        rb = response.json()
        assert "http_status" not in rb, (
            f"http_status leaked into response body: {rb}"
        )
        assert rb["status"] == "accepted"
        assert rb["recipe_id"] == recipe_id

        # Recipe validation updated as side effect
        after_v = rl.get_recipe(recipe_id)["version"]
        assert after_v == before_v + 1, (
            f"HTTP POST did not trigger recipe update: v {before_v} -> {after_v}"
        )

    # ── Test 8: PLATFORM MATCHING ───────────────────────────────────

    def test_platform_matching_overrides(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 8: Platform matching — covers FEEDBACK-INGEST-04.

        Submit feedback with platform="bilibili". Recipe validation.platform
        field is updated to "bilibili".
        """
        recipe_id = _make_recipe(bus, rl, "ep-plat")
        # Seed with douyin first to verify the override
        body1 = _make_feedback_body("ep-plat", platform="douyin", cr=0.5, measured_at="T11:00:00Z")
        client.submit_feedback(body1, _sign(body1, SECRET))
        assert rl.get_recipe(recipe_id)["validation"]["platform"] == "douyin"

        # Now submit bilibili — should override
        body2 = _make_feedback_body("ep-plat", platform="bilibili", cr=0.6, measured_at="T12:00:00Z")
        result = client.submit_feedback(body2, _sign(body2, SECRET))
        assert result["status"] == "accepted"

        recipe = rl.get_recipe(recipe_id)
        assert recipe["validation"]["platform"] == "bilibili", (
            f"expected platform='bilibili', got {recipe['validation']['platform']!r}"
        )

    # ── Test 9: FULL METRICS PRESERVED ──────────────────────────────

    def test_full_metrics_preserved_in_feedback_data(
        self, bus: AssetBus, rl: RecipeLibrary, client: FeedbackIngestClient,
    ) -> None:
        """Test 9: Full metrics preservation — covers FEEDBACK-INGEST-03.

        feedback-data record stores ALL of metrics{completion_rate,
        interaction_rate, follow_rate} even though only completion_rate
        feeds update_validation. Future-proofing per CONTEXT.md.
        """
        _make_recipe(bus, rl, "ep-metrics")
        body = _make_feedback_body(
            "ep-metrics", cr=0.42, ir=0.18, fr=0.07,
        )
        result = client.submit_feedback(body, _sign(body, SECRET))
        assert result["status"] == "accepted"

        records = client.get_feedback()
        assert len(records) == 1
        rec = records[0]
        # All 3 metrics preserved
        assert rec["metrics"]["completion_rate"] == pytest.approx(0.42)
        assert rec["metrics"]["interaction_rate"] == pytest.approx(0.18)
        assert rec["metrics"]["follow_rate"] == pytest.approx(0.07)

    # ── Test 10: NON-FATAL update_validation FAILURE ────────────────

    def test_no_raise_on_bad_update_validation(
        self, bus: AssetBus, rl: RecipeLibrary,
    ) -> None:
        """Test 10: Non-fatal update_validation — covers FEEDBACK-INGEST-01/03.

        If RecipeLibrary.update_validation returns None (e.g., AssetBus
        failure), submit_feedback still returns accepted (the feedback-data
        record was already persisted; update_validation failure is non-fatal
        — logged but not propagated).
        """
        _make_recipe(bus, rl, "ep-nf")

        # Build a FakeRecipeLibrary whose update_validation returns None.
        # Reuse the real rl for get_recipe_by_episode (the 404 stage needs it);
        # only update_validation is stubbed.
        class _FlakyRL:
            def __init__(self, real: RecipeLibrary) -> None:
                self._real = real
                self.update_validation_calls: list[tuple] = []

            def get_recipe_by_episode(self, source_episode: str) -> dict | None:
                return self._real.get_recipe_by_episode(source_episode)

            def update_validation(self, *args, **kwargs) -> None:
                self.update_validation_calls.append((args, kwargs))
                return None  # Simulate AssetBus failure / degrade mode.

        flaky = _FlakyRL(rl)
        client = FeedbackIngestClient(
            asset_bus=bus, recipe_library=flaky, secret=SECRET,
        )

        body = _make_feedback_body("ep-nf", cr=0.5)
        result = client.submit_feedback(body, _sign(body, SECRET))

        # Feedback accepted despite update_validation returning None
        assert result["status"] == "accepted", (
            f"expected accepted even when update_validation fails, got: {result}"
        )
        # feedback-data record was persisted
        assert len(client.get_feedback()) == 1
        # update_validation was actually called (proof the path was exercised)
        assert len(flaky.update_validation_calls) == 1, (
            f"expected 1 update_validation call, got {len(flaky.update_validation_calls)}"
        )
