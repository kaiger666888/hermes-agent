"""test_feedback_server.py - Phase 42-03 Task 1 (TDD RED->GREEN).

HTTP server wiring for FeedbackIngestClient: list_pending_updates +
``_build_starlette_app`` factory + ``start_feedback_server`` context
manager + ``__main__`` CLI block.

Architecture (LOCKED in CONTEXT.md "HTTP Server Architecture & HMAC"):
- Framework: httpx + Starlette ASGI wrapper (V5.0 deps — NO new deps).
- Endpoint: POST /api/v1/feedback on KAIS_FEEDBACK_PORT (default 8091).
- Server lifecycle: ``start_feedback_server`` context manager starts
  uvicorn in a daemon thread; ``__exit__`` signals ``should_exit=True``
  + joins the thread (graceful shutdown).
- Single-process uvicorn (worker=1) — no horizontal scaling concerns.

Tests (16 total):
  TestListPendingUpdates (Tests 1-3): recent-record queue semantics.
  TestStarletteApp        (Tests 4-11): ASGI app via Starlette TestClient
    (httpx-based, no port binding) — covers all 5 HTTP status codes.
  TestServerLifecycle     (Tests 12-16): real uvicorn round-trip on an
    ephemeral port + ``__main__`` source inspection.
"""

from __future__ import annotations

import hashlib
import hmac
import inspect
import json
import os
import socket
import sys
import types
from typing import Any

import httpx
import pytest

from plugins.kais_aigc.feedback_ingest import (
    DEFAULT_FEEDBACK_PORT,
    FeedbackIngestClient,
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
    """Minimal RecipeLibrary stub (mirrors test_feedback_validation)."""

    def __init__(self, *, episode_to_recipe: dict[str, dict] | None = None) -> None:
        self._episode_to_recipe = episode_to_recipe or {}
        self.update_call_count = 0

    def get_recipe_by_episode(self, source_episode: str) -> dict | None:
        return self._episode_to_recipe.get(source_episode)

    def update_validation(self, *args: Any, **kwargs: Any) -> dict:
        self.update_call_count += 1
        return {"recipe_id": "r1", "version": 2}


@pytest.fixture
def bus(tmp_path) -> AssetBus:
    return AssetBus(tmp_path)


@pytest.fixture
def recipe_with_episode() -> _RecordingRecipeLibrary:
    return _RecordingRecipeLibrary(
        episode_to_recipe={"ep-001": {"recipe_id": "r1", "version": 1}},
    )


@pytest.fixture
def client(bus, recipe_with_episode) -> FeedbackIngestClient:
    return FeedbackIngestClient(
        asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
    )


def _free_port() -> int:
    """Pick a free TCP port for an ephemeral uvicorn bind."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ─── Tests 1-3: list_pending_updates ─────────────────────────────────


class TestListPendingUpdates:
    """Verify the pending-review queue reader on FeedbackIngestClient."""

    def test_1_returns_empty_list_when_no_feedback_data(self, client):
        # No records written yet -> empty list (NOT None, NOT error).
        result = client.list_pending_updates()
        assert result == []

    def test_2_returns_at_most_n_most_recent_first(self, bus, recipe_with_episode):
        # Pre-populate feedback-data with 8 records having distinct received_at.
        c = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        for i in range(8):
            bus.append_line("feedback-data", {
                "feedback_id": f"f{i}",
                "received_at": f"2026-01-{i + 1:02d}T00:00:00Z",
                "episode_id": "ep-001",
            })
        out = c.list_pending_updates(limit=5)
        assert len(out) == 5
        # newest first (lexicographic ISO sort, descending)
        assert out[0]["feedback_id"] == "f7"
        assert out[4]["feedback_id"] == "f3"

    def test_3_default_limit_is_10(self, bus, recipe_with_episode):
        c = FeedbackIngestClient(
            asset_bus=bus, recipe_library=recipe_with_episode, secret=SECRET,
        )
        for i in range(12):
            bus.append_line("feedback-data", {
                "feedback_id": f"f{i}",
                "received_at": f"2026-01-{i + 1:02d}T00:00:00Z",
            })
        out = c.list_pending_updates()
        assert len(out) == 10  # default cap
        assert out[0]["feedback_id"] == "f11"  # newest


# ─── Tests 4-11: _build_starlette_app (no port — Starlette TestClient) ──


class TestStarletteApp:
    """Exercise the ASGI app directly via Starlette's httpx TestClient.

    No real socket is opened — Starlette TestClient drives the ASGI
    surface in-process. Faster + more deterministic than uvicorn.
    """

    def _client_with_app(self, client: FeedbackIngestClient):
        from starlette.testclient import TestClient

        from plugins.kais_aigc.feedback_ingest import _build_starlette_app
        app = _build_starlette_app(client)
        return TestClient(app)

    def test_4_factory_returns_starlette_app_with_one_post_route(self, client):
        from starlette.applications import Starlette

        from plugins.kais_aigc.feedback_ingest import _build_starlette_app
        app = _build_starlette_app(client)
        assert isinstance(app, Starlette)
        # Inspect the router for the canonical POST /api/v1/feedback route.
        routes = [(r.path, tuple(getattr(r, "methods", ()) or ())) for r in app.routes]
        assert ("/api/v1/feedback", ("POST",)) in routes

    def test_5_post_with_valid_body_and_signature_returns_200(self, client):
        tc = self._client_with_app(client)
        body = _valid_body()
        resp = tc.post(
            "/api/v1/feedback",
            content=body,
            headers={"X-Signature": _sign(body), "Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"

    def test_6_post_with_invalid_signature_returns_401(self, client):
        tc = self._client_with_app(client)
        body = _valid_body()
        resp = tc.post(
            "/api/v1/feedback",
            content=body,
            headers={"X-Signature": "sha256=deadbeef", "Content-Type": "application/json"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "signature"

    def test_7_post_with_malformed_json_valid_sig_returns_422(self, client):
        tc = self._client_with_app(client)
        # Malformed JSON body, but signed with the SAME secret so we get
        # past stage 1 (signature) and trip stage 2 (schema).
        body = b"{not valid json"
        resp = tc.post(
            "/api/v1/feedback",
            content=body,
            headers={"X-Signature": _sign(body), "Content-Type": "application/json"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "schema"

    def test_8_post_with_semantic_violation_returns_400(self, client):
        tc = self._client_with_app(client)
        bad = dict(_VALID_PAYLOAD)
        bad["metrics"] = dict(_VALID_PAYLOAD["metrics"])
        bad["metrics"]["completion_rate"] = 1.5  # out of [0, 1]
        body = json.dumps(bad).encode("utf-8")
        resp = tc.post(
            "/api/v1/feedback",
            content=body,
            headers={"X-Signature": _sign(body), "Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "semantic"

    def test_9_post_with_unknown_episode_returns_404(self, bus):
        # RecipeLibrary stub that knows about NO episodes.
        empty_recipe = _RecordingRecipeLibrary(episode_to_recipe={})
        c = FeedbackIngestClient(
            asset_bus=bus, recipe_library=empty_recipe, secret=SECRET,
        )
        tc = self._client_with_app(c)
        body = _valid_body()
        resp = tc.post(
            "/api/v1/feedback",
            content=body,
            headers={"X-Signature": _sign(body), "Content-Type": "application/json"},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "episode_not_found"

    def test_10_get_returns_405_method_not_allowed(self, client):
        tc = self._client_with_app(client)
        resp = tc.get("/api/v1/feedback")
        # Starlette returns 405 when the path matches but the method does not.
        assert resp.status_code == 405

    def test_11_post_to_unknown_path_returns_404(self, client):
        tc = self._client_with_app(client)
        resp = tc.post("/unknown")
        assert resp.status_code == 404


# ─── Tests 12-16: start_feedback_server context manager ──────────────


class TestServerLifecycle:
    """Real uvicorn round-trip on an ephemeral port via httpx."""

    def test_12_context_manager_yields_handle_with_client_and_base_url(
        self, bus, recipe_with_episode,
    ):
        from plugins.kais_aigc.feedback_ingest import start_feedback_server

        port = _free_port()
        with start_feedback_server(
            host="127.0.0.1", port=port, secret=SECRET,
            recipe_library=recipe_with_episode, asset_bus=bus,
        ) as srv:
            assert srv.client is not None
            assert isinstance(srv.client, FeedbackIngestClient)
            assert srv.base_url == f"http://127.0.0.1:{port}"

    def test_13_real_http_round_trip_returns_200(self, bus, recipe_with_episode):
        from plugins.kais_aigc.feedback_ingest import start_feedback_server

        port = _free_port()
        with start_feedback_server(
            host="127.0.0.1", port=port, secret=SECRET,
            recipe_library=recipe_with_episode, asset_bus=bus,
        ) as srv:
            body = _valid_body()
            # Use a fresh httpx client with a slightly longer timeout to
            # absorb uvicorn daemon-thread startup latency.
            with httpx.Client(timeout=5.0) as hc:
                resp = hc.post(
                    srv.base_url + "/api/v1/feedback",
                    content=body,
                    headers={
                        "X-Signature": _sign(body),
                        "Content-Type": "application/json",
                    },
                )
            assert resp.status_code == 200
            assert resp.json()["status"] == "accepted"

    def test_14_port_released_after_context_exit(self, bus, recipe_with_episode):
        from plugins.kais_aigc.feedback_ingest import start_feedback_server

        port = _free_port()
        # First occupation.
        with start_feedback_server(
            host="127.0.0.1", port=port, secret=SECRET,
            recipe_library=recipe_with_episode, asset_bus=bus,
        ):
            pass
        # Port should be released now; a second context manager on the
        # SAME port must succeed without OSError/EADDRINUSE.
        with start_feedback_server(
            host="127.0.0.1", port=port, secret=SECRET,
            recipe_library=recipe_with_episode, asset_bus=bus,
        ) as srv2:
            assert srv2.base_url == f"http://127.0.0.1:{port}"

    def test_15_reads_kais_feedback_port_env_when_port_none(
        self, bus, recipe_with_episode, monkeypatch,
    ):
        from plugins.kais_aigc.feedback_ingest import start_feedback_server

        port = _free_port()
        monkeypatch.setenv("KAIS_FEEDBACK_PORT", str(port))
        with start_feedback_server(
            host="127.0.0.1", secret=SECRET,
            recipe_library=recipe_with_episode, asset_bus=bus,
            # port= deliberately omitted -> must read KAIS_FEEDBACK_PORT.
        ) as srv:
            assert str(port) in srv.base_url
        monkeypatch.delenv("KAIS_FEEDBACK_PORT", raising=False)

    def test_16_main_block_exists_in_module_source(self):
        # Source inspection: assert the module ships an ``if __name__ ==
        # "__main__"`` guard so ``python -m plugins.kais_aigc.feedback_ingest``
        # would start the server. Avoid actually exec'ing the block (it
        # would block forever).
        import plugins.kais_aigc.feedback_ingest as mod

        src = inspect.getsource(mod)
        assert 'if __name__ == "__main__"' in src or (
            "if __name__ == '__main__'" in src
        )
        # Also confirm the module references start_feedback_server inside
        # the __main__ block region (heuristic: name appears in source).
        assert "start_feedback_server" in src
