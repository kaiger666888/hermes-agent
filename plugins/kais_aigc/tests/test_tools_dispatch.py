"""Integration tests for plugins/kais_aigc/tools.py dispatch (Phase 32-05).

These tests prove each ``_handle_kais_*`` routes args to the correct client
method and returns JSON via ``tool_result`` / ``tool_error``. Clients are
mocked by ``monkeypatch.setattr`` on the factory functions in ``tools``
(``_gold_team_client`` / ``_review_platform_client`` / ``_canvas_client`` /
``_jimeng_client``). HTTP-level behavior is covered by the per-client test
files in Wave 1 (``test_gold_team.py`` etc.) — these tests verify *routing*,
not HTTP, and never construct ``httpx.Client``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from plugins.kais_aigc import tools
from plugins.kais_aigc.canvas import CanvasClientError
from plugins.kais_aigc.gold_team import GoldTeamError
from plugins.kais_aigc.jimeng import JimengError
from plugins.kais_aigc.review_platform import ReviewClientError


# ---------------------------------------------------------------------------
# Fake client doubles — mimic the small slice of API used by tools.py
# ---------------------------------------------------------------------------

class _FakeGoldTeam:
    def __init__(self, *, result: dict | None = None, exc: Exception | None = None) -> None:
        self.result = result if result is not None else {"task_id": "t-1", "state": "queued"}
        self.exc = exc
        self.submit_calls: list[dict] = []
        self.wait_calls: list[str] = []

    def submit_task(self, **kw: Any) -> dict:
        self.submit_calls.append(kw)
        if self.exc:
            raise self.exc
        return self.result

    def wait_for_task(self, task_id: str) -> dict:
        self.wait_calls.append(task_id)
        return {"task_id": task_id, "state": "done"}

    def __enter__(self) -> "_FakeGoldTeam":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


class _FakeReview:
    def __init__(self, *, result: dict | None = None, exc: Exception | None = None) -> None:
        self.result = result if result is not None else {"review_id": "r-1", "state": "pending"}
        self.exc = exc
        self.submit_calls: list[dict] = []

    def submit_review(self, **kw: Any) -> dict:
        self.submit_calls.append(kw)
        if self.exc:
            raise self.exc
        return self.result

    def __enter__(self) -> "_FakeReview":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


class _FakeCanvas:
    def __init__(self, *, result: Any = None, exc: Exception | None = None) -> None:
        self.result = result if result is not None else {"ok": True}
        self.exc = exc
        self.save_calls: list[dict] = []

    def save_canvas_degraded(self, graph: dict) -> Any:
        self.save_calls.append(graph)
        if self.exc:
            raise self.exc
        return self.result

    def __enter__(self) -> "_FakeCanvas":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


class _FakeJimeng:
    def __init__(self, *, result: Any = None, exc: Exception | None = None) -> None:
        self.result = result if result is not None else {"images": ["x"]}
        self.exc = exc
        self.calls: list[tuple[str, dict]] = []

    def call(self, subcommand: str, payload: dict) -> Any:
        self.calls.append((subcommand, payload))
        if self.exc:
            raise self.exc
        return self.result

    def __enter__(self) -> "_FakeJimeng":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


def _install(monkeypatch, factory_name: str, fake: Any) -> None:
    """Replace ``tools.<factory_name>`` to return ``fake`` (as a context manager)."""

    class _Ctx:
        def __enter__(self_) -> Any:
            return fake

        def __exit__(self_, *exc: Any) -> bool:
            return False

    monkeypatch.setattr(tools, factory_name, lambda: _Ctx())


def _parse(s: str) -> dict:
    return json.loads(s)


# ---------------------------------------------------------------------------
# Gold team dispatch
# ---------------------------------------------------------------------------

class TestGoldTeamDispatch:
    def test_submit_returns_tool_result_json(self, monkeypatch):
        fake = _FakeGoldTeam()
        _install(monkeypatch, "_gold_team_client", fake)
        out = tools._handle_kais_gold_team_submit({"task_type": "image_draw", "payload": {"prompt": "cat"}})
        data = _parse(out)
        assert data["task_id"] == "t-1"
        assert fake.submit_calls == [{"task_type": "image_draw", "params": {"prompt": "cat"}}]

    def test_submit_with_wait_polls(self, monkeypatch):
        fake = _FakeGoldTeam()
        _install(monkeypatch, "_gold_team_client", fake)
        tools._handle_kais_gold_team_submit({"task_type": "video_final", "wait": True})
        assert fake.wait_calls == ["t-1"]

    def test_submit_missing_task_type_returns_tool_error(self, monkeypatch):
        out = tools._handle_kais_gold_team_submit({})
        data = _parse(out)
        assert "error" in data
        assert data["error"] == "task_type is required"

    def test_submit_client_exception_returns_tool_error(self, monkeypatch):
        fake = _FakeGoldTeam(exc=GoldTeamError("boom", status=500))
        _install(monkeypatch, "_gold_team_client", fake)
        out = tools._handle_kais_gold_team_submit({"task_type": "image_draw"})
        data = _parse(out)
        assert "error" in data
        assert "boom" in str(data)


# ---------------------------------------------------------------------------
# Review platform dispatch
# ---------------------------------------------------------------------------

class TestReviewPlatformDispatch:
    def test_submit_returns_tool_result_json(self, monkeypatch):
        fake = _FakeReview()
        _install(monkeypatch, "_review_platform_client", fake)
        out = tools._handle_kais_review_submit({
            "asset_type": "script",
            "asset_id": "s-1",
            "reviewer_role": "director",
            "callback_url": "http://cb",
        })
        data = _parse(out)
        assert data["review_id"] == "r-1"
        assert fake.submit_calls == [{
            "type": "script",
            "content_ref": "s-1",
            "metadata": {"reviewer_role": "director"},
            "callback_url": "http://cb",
        }]

    def test_submit_without_reviewer_role_passes_none_metadata(self, monkeypatch):
        fake = _FakeReview()
        _install(monkeypatch, "_review_platform_client", fake)
        tools._handle_kais_review_submit({"asset_type": "scene", "asset_id": "x"})
        assert fake.submit_calls[0]["metadata"] is None

    def test_submit_missing_required_returns_tool_error(self, monkeypatch):
        out = tools._handle_kais_review_submit({"asset_type": "script"})
        data = _parse(out)
        assert "error" in data

    def test_submit_client_exception_returns_tool_error(self, monkeypatch):
        fake = _FakeReview(exc=ReviewClientError("nope", status=503))
        _install(monkeypatch, "_review_platform_client", fake)
        out = tools._handle_kais_review_submit({"asset_type": "x", "asset_id": "y"})
        data = _parse(out)
        assert "error" in data
        assert "nope" in str(data)


# ---------------------------------------------------------------------------
# Canvas dispatch
# ---------------------------------------------------------------------------

class TestCanvasDispatch:
    def test_sync_returns_tool_result_json(self, monkeypatch):
        fake = _FakeCanvas()
        _install(monkeypatch, "_canvas_client", fake)
        out = tools._handle_kais_canvas_sync({
            "node_id": "n1",
            "node_type": "character",
            "payload": {"name": "Hero"},
        })
        data = _parse(out)
        assert data == {"ok": True}
        assert fake.save_calls == [{"nodes": [{"id": "n1", "type": "character", "data": {"name": "Hero"}}]}]

    def test_sync_missing_required_returns_tool_error(self, monkeypatch):
        out = tools._handle_kais_canvas_sync({"node_id": "n1"})
        data = _parse(out)
        assert "error" in data

    def test_sync_client_exception_returns_tool_error(self, monkeypatch):
        fake = _FakeCanvas(exc=CanvasClientError("down", status=500))
        _install(monkeypatch, "_canvas_client", fake)
        out = tools._handle_kais_canvas_sync({"node_id": "n1", "node_type": "scene"})
        data = _parse(out)
        assert "error" in data
        assert "down" in str(data)


# ---------------------------------------------------------------------------
# Jimeng dispatch
# ---------------------------------------------------------------------------

class TestJimengDispatch:
    def test_call_returns_tool_result_json(self, monkeypatch):
        fake = _FakeJimeng()
        _install(monkeypatch, "_jimeng_client", fake)
        out = tools._handle_kais_jimeng_call({"subcommand": "text2image", "payload": {"prompt": "dog"}})
        data = _parse(out)
        assert data == {"images": ["x"]}
        assert fake.calls == [("text2image", {"prompt": "dog"})]

    def test_call_missing_subcommand_returns_tool_error(self, monkeypatch):
        out = tools._handle_kais_jimeng_call({"payload": {}})
        data = _parse(out)
        assert "error" in data

    def test_call_client_exception_returns_tool_error(self, monkeypatch):
        fake = _FakeJimeng(exc=JimengError("rate", status=429))
        _install(monkeypatch, "_jimeng_client", fake)
        out = tools._handle_kais_jimeng_call({"subcommand": "text2image"})
        data = _parse(out)
        assert "error" in data
        assert "rate" in str(data)

    def test_call_does_not_mutate_caller_payload(self, monkeypatch):
        fake = _FakeJimeng()
        _install(monkeypatch, "_jimeng_client", fake)
        payload = {"prompt": "x"}
        tools._handle_kais_jimeng_call({"subcommand": "text2image", "payload": payload})
        assert payload == {"prompt": "x"}  # untouched (we copy before passing)


# ---------------------------------------------------------------------------
# Schema sanity
# ---------------------------------------------------------------------------

class TestSchema17Enums:
    def test_gold_team_task_type_enum_has_17(self):
        enum = tools.KAIS_GOLD_TEAM_SUBMIT_SCHEMA["parameters"]["properties"]["task_type"]["enum"]
        assert len(enum) == 17
        # Sanity: all 4 Node.js-derived additions present
        for extra in ("tts_generation", "image_composition", "video_generation", "seedance_video"):
            assert extra in enum, f"missing {extra}"
