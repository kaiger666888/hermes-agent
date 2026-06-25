"""test_jimeng.py — mocked-HTTP tests for JimengClient.

Mirrors the ``httpx.MockTransport`` test pattern established by
``tests/tools/test_microsoft_graph_client.py`` and the Phase 32 PATTERNS.md
"MockTransport Test Pattern" section.

Critical: NO real network calls (every JimengClient is constructed with
``transport=httpx.MockTransport(handler)``) and NO real sleeping
(``sleep_fn=lambda s: None`` is injected via the ``_client`` factory).
"""

from __future__ import annotations

import httpx
import pytest

from plugins.kais_aigc.jimeng import (
    SUBCOMMAND_ENDPOINTS,
    JimengClient,
    JimengError,
)


def _client(handler, **kw) -> JimengClient:
    """Build a JimengClient whose httpx calls are mocked by ``handler``.

    Two sessions are configured so rotation tests can exercise multi-session
    paths; the factory's ``sleep_fn`` is a no-op so the suite stays fast.
    Callers may override ``session_id`` / ``sleep_fn`` / ``max_retries`` etc.
    via ``kw``.
    """
    defaults = dict(
        base_url="http://test-jimeng",
        session_id="sess-1,sess-2",
        sleep_fn=lambda s: None,
    )
    defaults.update(kw)  # caller overrides win
    return JimengClient(
        transport=httpx.MockTransport(handler),
        **defaults,
    )


class TestJimengClient:
    """Happy-path + retry + rotation + degrade + raise coverage."""

    def test_call_text2image_happy_path(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                json={"data": [{"url": "http://img/1", "seed": 42}]},
            )

        with _client(handler) as c:
            result = c.call("text2image", {"prompt": "a cat"})

        # Result is the unwrapped ``data`` array (Node.js ref returns json.data).
        assert isinstance(result, list)
        assert result[0]["url"] == "http://img/1"
        assert result[0]["seed"] == 42

        # Exactly one HTTP call, on the right path/method/body/headers.
        assert len(captured) == 1
        req = captured[0]
        assert req.method == "POST"
        assert req.url.path == "/v1/images/generations"
        assert req.headers["Authorization"] == "Bearer sess-1"
        body = req.read()
        import json as _json
        parsed = _json.loads(body)
        assert parsed["model"] == "jimeng-5.0"  # default for text2image
        assert parsed["prompt"] == "a cat"

    def test_call_image2image_uses_compositions_endpoint(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": [{"url": "http://img/2"}]})

        with _client(handler) as c:
            result = c.call(
                "image2image",
                {"prompt": "cat", "images": ["http://ref"]},
            )

        assert result[0]["url"] == "http://img/2"
        assert captured[0].url.path == "/v1/images/compositions"

    def test_call_multimodal2video_passes_file_paths(self):
        """The client is subcommand-agnostic — caller sets functionMode."""
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": [{"url": "http://vid/1"}]})

        with _client(handler) as c:
            result = c.call(
                "multimodal2video",
                {
                    "prompt": "scene with @Image 1",
                    "file_paths": ["http://a", "http://b"],
                    "functionMode": "omni_reference",  # caller-injected, NOT auto
                },
            )

        assert result[0]["url"] == "http://vid/1"
        req = captured[0]
        assert req.url.path == "/v1/videos/generations"
        import json as _json
        parsed = _json.loads(req.read())
        assert parsed["file_paths"] == ["http://a", "http://b"]
        assert parsed["functionMode"] == "omni_reference"
        assert parsed["model"] == "jimeng-video-seedance-2.0"

    def test_call_frames2video_routes_to_video_generations(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": [{"url": "http://vid/2"}]})

        with _client(handler) as c:
            result = c.call(
                "frames2video",
                {"prompt": "interpolate", "file_paths": ["http://f1", "http://f2"]},
            )

        assert result[0]["url"] == "http://vid/2"
        assert captured[0].url.path == "/v1/videos/generations"

    def test_call_image_upscale_routes_to_upscales_endpoint(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": [{"url": "http://upscaled"}]})

        with _client(handler) as c:
            result = c.call(
                "image_upscale",
                {"prompt": "upscale", "images": ["http://src"]},
            )

        assert result[0]["url"] == "http://upscaled"
        assert captured[0].url.path == "/v1/images/upscales"

    def test_call_retries_on_429_then_succeeds(self):
        """429 → exponential backoff → retry → 200 succeeds on 2nd call."""
        call_count = {"n": 0}
        sleeps: list[float] = []

        def handler(request: httpx.Request) -> httpx.Response:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return httpx.Response(429)
            return httpx.Response(
                200,
                json={"data": [{"url": "http://after-retry"}]},
            )

        with _client(handler, sleep_fn=lambda s: sleeps.append(s)) as c:
            result = c.call("text2image", {"prompt": "x"})

        assert isinstance(result, list)
        assert result[0]["url"] == "http://after-retry"
        assert call_count["n"] == 2  # one 429, one 200
        # First sleep is the exponential backoff (2^0 = 1s) after the 429.
        # Second sleep is the 1-second inter-request spacing (RATE_LIMIT_SLEEP_SEC)
        # enforced before the retry attempt — both are part of the contract.
        assert len(sleeps) == 2
        assert sleeps[0] == pytest.approx(1.0)

    def test_call_rotates_session_after_3_strikes(self):
        """3 consecutive 429s on multi-session config → rotate session."""
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(429)  # always rate-limited

        # 3 sessions, max_retries=4: strikes 1,2,3 (all on sess-A),
        # rotation triggers after strike #3, attempt #4 uses sess-B.
        with _client(handler, session_id="sess-A,sess-B,sess-C", max_retries=4) as c:
            result = c.call("text2image", {"prompt": "x"})

        assert len(captured) == 4
        # First three requests use sess-A (strikes accumulate).
        assert captured[0].headers["Authorization"] == "Bearer sess-A"
        assert captured[1].headers["Authorization"] == "Bearer sess-A"
        assert captured[2].headers["Authorization"] == "Bearer sess-A"
        # Fourth request — after rotation — uses sess-B.
        assert captured[3].headers["Authorization"] == "Bearer sess-B"
        # All retries exhausted → degrade.
        assert isinstance(result, dict)
        assert result["degraded"] is True

    def test_call_degrades_when_max_retries_exhausted(self):
        """Continuous 429s with a single session → degrade envelope."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429)

        with _client(handler, session_id="only-sess", max_retries=3) as c:
            result = c.call("text2image", {"prompt": "x"})

        assert isinstance(result, dict)
        assert result["degraded"] is True
        assert result["client"] == "jimeng"
        assert "max_retries" in result["reason"]

    def test_call_degrades_on_503(self):
        """HTTP 5xx degrades immediately (no retry)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        with _client(handler) as c:
            result = c.call("text2image", {"prompt": "x"})

        assert isinstance(result, dict)
        assert result["degraded"] is True
        assert result["client"] == "jimeng"
        assert "503" in result["reason"]

    def test_call_raises_on_400(self):
        """HTTP 4xx (except 429) → JimengError (caller bug)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad request"})

        with _client(handler) as c:
            with pytest.raises(JimengError) as exc_info:
                c.call("text2image", {"prompt": "x"})

        assert exc_info.value.status == 400

    def test_call_raises_on_404(self):
        """Non-429 4xx variant also raises."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404)

        with _client(handler) as c:
            with pytest.raises(JimengError) as exc_info:
                c.call("text2image", {"prompt": "x"})

        assert exc_info.value.status == 404

    def test_call_unknown_subcommand_raises(self):
        def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
            raise AssertionError("should not make HTTP call")

        with _client(handler) as c:
            with pytest.raises(JimengError) as exc_info:
                c.call("bogus", {})

        assert "unknown subcommand" in str(exc_info.value)

    def test_call_degrades_on_connect_error(self):
        """Connection refused → retry once → degrade."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        # max_retries=1 → no second attempt, immediate degrade.
        with _client(handler, max_retries=1) as c:
            result = c.call("text2image", {"prompt": "x"})

        assert isinstance(result, dict)
        assert result["degraded"] is True
        assert "ConnectError" in result["reason"]

    def test_subcommand_endpoints_covers_all_six(self):
        """Sanity: SUBCOMMAND_ENDPOINTS has exactly the 6 GPU-DIRECT-04 commands."""
        expected = {
            "text2image",
            "image2image",
            "multimodal2video",
            "multiframe2video",
            "frames2video",
            "image_upscale",
        }
        assert set(SUBCOMMAND_ENDPOINTS.keys()) == expected
        # Each value is a (method, path, default_model) triple.
        for sub, (method, path, model) in SUBCOMMAND_ENDPOINTS.items():
            assert method == "POST", f"{sub}: expected POST, got {method}"
            assert path.startswith("/v1/"), f"{sub}: path not under /v1/"
            assert model, f"{sub}: missing default model"

    def test_payload_model_override_wins(self):
        """Caller-supplied ``model`` overrides the subcommand default."""
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": []})

        with _client(handler) as c:
            c.call("text2image", {"prompt": "x", "model": "custom-model"})

        import json as _json
        parsed = _json.loads(captured[0].read())
        assert parsed["model"] == "custom-model"

    def test_payload_not_mutated(self):
        """``call`` must not mutate the caller's payload dict."""
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"data": []})

        payload = {"prompt": "x"}
        with _client(handler) as c:
            c.call("text2image", payload)

        # Caller's dict should not have ``model`` injected into it.
        assert "model" not in payload
        assert payload == {"prompt": "x"}
