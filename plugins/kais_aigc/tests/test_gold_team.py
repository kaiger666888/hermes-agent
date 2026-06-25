"""Mocked-HTTP tests for ``GoldTeamClient`` (Plan 32-01).

Mirrors the ``httpx.MockTransport`` pattern from
``tests/tools/test_microsoft_graph_client.py`` and PATTERNS.md
"MockTransport Test Pattern". No real network calls - every
``GoldTeamClient`` instance is constructed with
``transport=httpx.MockTransport(handler)``.

Coverage matrix (D-09 degrade contract enforced for both paths):
- happy path submit / get / list / wait
- degrade on 5xx, connect error, timeout
- raise GoldTeamError on 4xx
- X-API-Key header conditional on env / api_key arg (CRITICAL-FINDING-02)
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

# Ensure hermes-agent root is importable so ``plugins.kais_aigc.*`` resolves.
HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.gold_team import GoldTeamClient, GoldTeamError  # noqa: E402


def _client(handler, **kw) -> GoldTeamClient:
    """Build a GoldTeamClient whose httpx calls are mocked by ``handler``.

    The handler is a ``(httpx.Request) -> httpx.Response`` callable.
    Caller uses ``with _client(handler) as c:`` so the httpx client closes
    cleanly even on assertion failure.
    """
    return GoldTeamClient(
        base_url="http://test-gold-team",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
        **kw,
    )


class TestGoldTeamClient:
    """Hermetic HTTP tests for ``GoldTeamClient``."""

    def test_submit_task_happy_path(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert request.url.path == "/api/v1/tasks"
            assert request.method == "POST"
            assert request.headers["X-API-Key"] == "test-key"
            return httpx.Response(
                200,
                json={
                    "data": {
                        "task_id": "t-1",
                        "state": "queued",
                        "created_at": "2026-06-25T00:00:00Z",
                    }
                },
            )

        with _client(handler) as c:
            result = c.submit_task(
                task_type="image_draw",
                params={"prompt": "cat"},
            )
        assert result["task_id"] == "t-1"
        assert result["state"] == "queued"
        assert result["created_at"] == "2026-06-25T00:00:00Z"
        assert len(captured) == 1
        # Body shape (task_type / params / callback wiring).
        body = httpx.QueryParams("")
        import json as _json
        parsed = _json.loads(captured[0].content.decode())
        assert parsed["task_type"] == "image_draw"
        assert parsed["params"] == {"prompt": "cat"}
        assert parsed["priority"] == 5
        assert parsed["callback_url"].endswith("/callback/gpu-task")

    def test_submit_task_degrades_on_503(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        with _client(handler) as c:
            result = c.submit_task(task_type="image_draw", params={})
        assert result["degraded"] is True
        assert result["client"] == "gold_team"
        assert "HTTP 503" in result["reason"]

    def test_submit_task_degrades_on_429(self):
        # 429 is rate-limiting - D-09 treats it as degrade (not raise).
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429)

        with _client(handler) as c:
            result = c.submit_task(task_type="image_draw", params={})
        assert result["degraded"] is True
        assert "HTTP 429" in result["reason"]

    def test_submit_task_degrades_on_connect_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        with _client(handler) as c:
            result = c.submit_task(task_type="image_draw", params={})
        assert result["degraded"] is True
        assert "refused" in result["reason"]

    def test_submit_task_degrades_on_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timed out", request=request)

        with _client(handler) as c:
            result = c.submit_task(task_type="image_draw", params={})
        assert result["degraded"] is True
        assert "Timeout" in result["reason"] or "timed out" in result["reason"]

    def test_submit_task_raises_on_400(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad task_type"})

        with _client(handler) as c:
            with pytest.raises(GoldTeamError) as ei:
                c.submit_task(task_type="invalid", params={})
        assert ei.value.status == 400
        assert "HTTP 400" in str(ei.value)

    def test_get_task_happy_path(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                json={
                    "data": {
                        "task_id": "t-1",
                        "state": "done",
                        "result": {"url": "s3://bucket/t-1.png"},
                    }
                },
            )

        with _client(handler) as c:
            result = c.get_task("t-1")
        assert result["state"] == "done"
        assert result["result"]["url"] == "s3://bucket/t-1.png"
        assert captured[0].url.path == "/api/v1/tasks/t-1"
        assert captured[0].method == "GET"

    def test_list_tasks_with_filters(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": [{"task_id": "t-1"}]})

        with _client(handler) as c:
            result = c.list_tasks(state="queued", task_type="image_draw", limit=5)
        assert result == [{"task_id": "t-1"}]
        url = str(captured[0].url)
        assert "state=queued" in url
        assert "task_type=image_draw" in url
        assert "limit=5" in url
        assert "offset=0" in url
        assert captured[0].method == "GET"

    def test_wait_for_task_completes_on_done(self):
        call_count = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            call_count["n"] += 1
            state = "running" if call_count["n"] == 1 else "done"
            return httpx.Response(
                200,
                json={"data": {"task_id": "t-1", "state": state}},
            )

        with _client(handler) as c:
            result = c.wait_for_task(
                "t-1",
                poll_interval=0.001,
                timeout=10,
            )
        assert result["state"] == "done"
        assert call_count["n"] == 2

    def test_wait_for_task_raises_on_failed(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "task_id": "t-1",
                        "state": "failed",
                        "error": "OOM on GPU 0",
                    }
                },
            )

        with _client(handler) as c:
            with pytest.raises(GoldTeamError) as ei:
                c.wait_for_task("t-1", poll_interval=0.001, timeout=10)
        assert "failed" in str(ei.value).lower()
        assert "OOM" in str(ei.value)

    def test_wait_for_task_times_out(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"data": {"task_id": "t-1", "state": "running"}},
            )

        with _client(handler) as c:
            with pytest.raises(GoldTeamError) as ei:
                c.wait_for_task("t-1", poll_interval=0.001, timeout=0.005)
        assert "timeout" in str(ei.value).lower()

    def test_no_api_key_header_when_unset(self, monkeypatch):
        # Ensure the env var is also unset so the constructor does not pick
        # it up (D-06: env read at construction time).
        monkeypatch.delenv("KAIS_GOLD_TEAM_API_KEY", raising=False)
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                json={"data": {"task_id": "t-1", "state": "queued"}},
            )

        c = GoldTeamClient(
            base_url="http://test-gold-team",
            api_key=None,
            transport=httpx.MockTransport(handler),
        )
        with c:
            c.submit_task(task_type="image_draw", params={})
        assert len(captured) == 1
        # X-API-Key MUST be absent when no key configured.
        assert "X-API-Key" not in captured[0].headers
        assert "x-api-key" not in captured[0].headers

    def test_submit_task_degraded_swallows_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad"})

        with _client(handler) as c:
            # submit_task_degraded wraps the 4xx raise -> degrade envelope.
            result = c.submit_task_degraded(
                task_type="invalid",
                params={},
            )
        assert result["degraded"] is True
        assert result["operation"] == "submit"

    def test_custom_callback_path_used(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                json={"data": {"task_id": "t-1", "state": "queued"}},
            )

        with _client(handler) as c:
            c.submit_task(
                task_type="image_draw",
                params={},
                callback_path="/custom/cb",
            )
        import json as _json
        parsed = _json.loads(captured[0].content.decode())
        assert parsed["callback_url"].endswith("/custom/cb")

    def test_subscribe_events_returns_documented_degrade(self):
        # SSE is a documented Phase 39 deferral.
        with _client(lambda r: httpx.Response(200)) as c:
            result = c.subscribe_events()
        assert result["degraded"] is True
        assert result["operation"] == "subscribe_events"
        assert "Phase 39" in result["reason"]
