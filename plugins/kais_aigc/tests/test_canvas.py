"""Mocked-HTTP tests for plugins/kais_aigc/canvas.py.

Mirrors the httpx.MockTransport pattern in tests/tools/test_microsoft_graph_client.py.
Every CanvasClient(...) in this file is constructed with transport=httpx.MockTransport(handler)
— no real network calls are made (D-04). No DB-layer references (D-08).
"""

from __future__ import annotations

import httpx
import pytest

from plugins.kais_aigc.canvas import CanvasClient, CanvasClientError


def _client(handler, **kw) -> CanvasClient:
    """Build a CanvasClient whose httpx calls are mocked by ``handler``.

    Default project_id=123, episodes_id=456 — override via kw.
    """
    return CanvasClient(
        base_url="http://test-canvas",
        project_id=kw.pop("project_id", 123),
        episodes_id=kw.pop("episodes_id", 456),
        transport=httpx.MockTransport(handler),
        **kw,
    )


class TestCanvasClient:
    def test_save_canvas_happy_path(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert request.url.path == "/api/canvas/v2/save-v2"
            assert request.method == "POST"
            assert request.headers["Content-Type"] == "application/json"
            return httpx.Response(
                200,
                json={"code": 0, "msg": "ok", "data": {"id": "n1"}},
            )

        with _client(handler) as c:
            result = c.save_canvas({"nodes": [], "edges": []})

        # Envelope unwrapped (CRITICAL-FINDING-05).
        assert result == {"id": "n1"}
        assert len(captured) == 1
        # Body schema: projectId, episodesId, graph.
        import json as _json
        body = _json.loads(captured[0].content)
        assert body["projectId"] == 123
        assert body["episodesId"] == 456
        assert "graph" in body and isinstance(body["graph"], dict)

    def test_save_canvas_sets_updatedat(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": {"ok": True}}
            )

        with _client(handler) as c:
            c.save_canvas({"nodes": []})

        import json as _json
        body = _json.loads(captured[0].content)
        # Node.js canvas-content-sync.js line 53 stamps meta.updatedAt (ms epoch).
        assert "meta" in body["graph"], "meta dict must be created"
        updated_at = body["graph"]["meta"]["updatedAt"]
        assert isinstance(updated_at, int) and updated_at > 0

    def test_save_canvas_degrades_on_503(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        with _client(handler) as c:
            result = c.save_canvas({"nodes": []})

        # D-08 / D-09: 5xx degrades, never raises to caller.
        assert result["degraded"] is True
        assert result["client"] == "canvas"
        assert "HTTP 503" in result["reason"]

    def test_save_canvas_degrades_on_connect_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        with _client(handler) as c:
            result = c.save_canvas({"nodes": []})

        assert result["degraded"] is True
        assert result["client"] == "canvas"
        assert "ConnectError" in result["reason"]

    def test_save_canvas_degrades_on_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timed out", request=request)

        with _client(handler) as c:
            result = c.save_canvas({"nodes": []})

        # D-09: timeouts degrade (pipeline continues).
        assert result["degraded"] is True
        assert "Timeout" in result["reason"] or "timed out" in result["reason"]

    def test_save_canvas_raises_on_400(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad graph"})

        with _client(handler) as c:
            with pytest.raises(CanvasClientError) as ei:
                c.save_canvas({"nodes": []})

        # D-09: 4xx raises (caller bug). Status + url captured.
        assert ei.value.status == 400
        assert "/api/canvas/v2/save-v2" in (ei.value.url or "")

    def test_load_canvas_happy_path(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "msg": "ok",
                    "data": {"nodes": [{"id": "n1"}], "edges": []},
                },
            )

        with _client(handler) as c:
            result = c.load_canvas()

        assert isinstance(result, dict)
        assert isinstance(result["nodes"], list) and len(result["nodes"]) == 1
        assert captured[0].url.path == "/api/canvas/v2/load-v2"
        assert captured[0].method == "POST"

    def test_load_canvas_returns_none_when_no_graph(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": None}
            )

        with _client(handler) as c:
            result = c.load_canvas()

        # Unwraps data=null → None.
        assert result is None

    def test_require_context_raises_when_project_id_unset(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"code": 0, "data": {}})

        with _client(handler, project_id=None) as c:
            with pytest.raises(CanvasClientError) as ei:
                c.save_canvas({"nodes": []})
        assert "projectId" in str(ei.value)

    def test_require_context_raises_when_episodes_id_unset(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"code": 0, "data": {}})

        with _client(handler, episodes_id=None) as c:
            with pytest.raises(CanvasClientError) as ei:
                c.load_canvas()
        assert "episodesId" in str(ei.value)

    def test_save_canvas_rejects_non_dict_graph(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"code": 0, "data": {}})

        with _client(handler) as c:
            with pytest.raises(CanvasClientError) as ei:
                c.save_canvas(None)  # type: ignore[arg-type]
        assert "graph must be a dict" in str(ei.value)

    def test_save_canvas_degraded_swallows_4xx(self):
        """The convenience wrapper catches CanvasClientError → degrade envelope.

        Matches Node.js canvas-content-sync.js saveGraph pattern: HTTP failure
        degrades warn, never blocks the pipeline.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad graph"})

        with _client(handler) as c:
            # save_canvas() alone would raise; the wrapper must catch.
            result = c.save_canvas_degraded({"nodes": []})

        assert result["degraded"] is True
        assert result["client"] == "canvas"
        assert result["operation"] == "save"

    def test_set_context_updates_ids(self):
        def handler(request: httpx.Request) -> httpx.Response:
            import json as _json
            body = _json.loads(request.content)
            assert body["projectId"] == 999
            assert body["episodesId"] == 888
            return httpx.Response(200, json={"code": 0, "data": {"ok": True}})

        with _client(handler, project_id=None, episodes_id=None) as c:
            c.set_context(project_id=999, episodes_id=888)
            result = c.save_canvas({"nodes": []})
        assert result == {"ok": True}

    def test_env_var_fallback_used_when_base_url_unset(self, monkeypatch):
        """D-06: KAIS_CANVAS_URL env var supplies base_url when not passed."""
        monkeypatch.setenv("KAIS_CANVAS_URL", "http://env-canvas:9999")

        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"code": 0, "data": {"ok": True}})

        # base_url unset — must fall back to env var.
        c = CanvasClient(
            project_id=1,
            episodes_id=1,
            transport=httpx.MockTransport(handler),
        )
        try:
            c.save_canvas({"nodes": []})
        finally:
            c.close()
        assert captured[0].url.host == "env-canvas"
        assert captured[0].url.port == 9999
