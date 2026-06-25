"""Subscriber unit + integration tests for plugins.kais_aigc.canvas_sync.

Mocks HTTP via ``httpx.MockTransport`` injected into the real Phase 32
``CanvasClient`` (PATTERN 4 — never mock the client itself, only the
transport). This exercises the real request construction + envelope
unwrap + the subscriber's degrade boundary.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest

from plugins.kais_aigc.canvas import CanvasClient
from plugins.kais_aigc.canvas_sync import CanvasSyncSubscriber


# ─── helpers ───────────────────────────────────────────────────────────


def make_mock_client(
    captured_urls: list[tuple[str, str]],
    captured_bodies: list[dict] | None = None,
    load_data: dict | None = None,
    save_status: int = 200,
    save_payload: dict | None = None,
    *,
    raise_on_request: Exception | None = None,
) -> CanvasClient:
    """Build a CanvasClient with a MockTransport that records every request.

    Args:
        captured_urls: list that the handler appends ``(method, url)`` tuples to.
        captured_bodies: optional list to also record parsed JSON bodies.
        load_data: dict returned by load-v2 inside the ``{code, msg, data}``
            envelope (``None`` → empty canvas).
        save_status: HTTP status returned for save-v2.
        save_payload: data envelope returned for save-v2.
        raise_on_request: if set, the handler raises this on every request
            (used for the CANVAS-IN-HERMES-03 connect-error test).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if raise_on_request is not None:
            raise raise_on_request
        captured_urls.append((request.method, str(request.url)))
        body: dict = {}
        if request.content:
            try:
                body = json.loads(request.content)
            except ValueError:
                body = {}
        if captured_bodies is not None:
            captured_bodies.append(body)

        path = request.url.path
        if path.endswith("/load-v2"):
            return httpx.Response(
                200,
                json={"code": 0, "msg": "ok", "data": load_data},
            )
        if path.endswith("/save-v2"):
            if save_status >= 400:
                return httpx.Response(save_status, json={"error": "bad"})
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "msg": "ok",
                    "data": save_payload or {"ok": True},
                },
            )
        return httpx.Response(404)

    return CanvasClient(
        base_url="http://test-canvas:10588",
        project_id=1,
        episodes_id=1,
        transport=httpx.MockTransport(handler),
    )


def _save_calls(urls: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [u for u in urls if u[1].endswith("/api/canvas/v2/save-v2")]


def _load_calls(urls: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [u for u in urls if u[1].endswith("/api/canvas/v2/load-v2")]


# ─── on_phase_complete ─────────────────────────────────────────────────


class TestOnPhaseComplete:
    def test_phase_complete_triggers_save_v2(self):
        """SC#2 keystone — exactly one save-v2 POST per phase completion."""
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete(
            "ep-1",
            "p01_topic",
            {"summary": {"selectedTopic": "X"}, "stage_order": 0},
        )
        client.close()
        saves = _save_calls(urls)
        assert len(saves) == 1, f"expected 1 save-v2, got {len(saves)}: {urls}"
        assert saves[0][0] == "POST"

    def test_phase_complete_loads_then_saves(self):
        """Order: load-v2 must precede save-v2."""
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()
        # load-v2 happens at index 0, save-v2 at index 1.
        load_idx = next(
            i for i, u in enumerate(urls) if u[1].endswith("/load-v2")
        )
        save_idx = next(
            i for i, u in enumerate(urls) if u[1].endswith("/save-v2")
        )
        assert load_idx < save_idx

    def test_phase_complete_draws_link_to_prev(self):
        """Two consecutive phase completions — second save carries a link."""
        urls: list[tuple[str, str]] = []
        bodies: list[dict] = []
        client = make_mock_client(urls, captured_bodies=bodies)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        sub.on_phase_complete("ep-1", "p02_outline", {"stage_order": 1})
        client.close()

        saves = [b for u, b in zip(urls, bodies) if u[1].endswith("/save-v2")]
        assert len(saves) == 2
        second_graph = saves[1]["graph"]
        link_ids = [l.get("id") for l in second_graph.get("links", [])]
        assert "l-p01_topic-p02_outline" in link_ids, (
            f"expected link l-p01_topic-p02_outline, got {link_ids}"
        )

    def test_phase_complete_upserts_node_with_id(self):
        """The saved graph contains a node with id n-{phase_id}."""
        urls: list[tuple[str, str]] = []
        bodies: list[dict] = []
        client = make_mock_client(urls, captured_bodies=bodies)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete(
            "ep-1",
            "p01_topic",
            {"summary": {"description": "topic picked"}, "stage_order": 0},
        )
        client.close()
        # Filter to save-v2 bodies only (load-v2 bodies have no `graph` key).
        save_bodies = [
            b for u, b in zip(urls, bodies) if u[1].endswith("/save-v2")
        ]
        graph = save_bodies[0]["graph"]
        node_ids = [n.get("id") for n in graph["nodes"]]
        assert "n-p01_topic" in node_ids


# ─── on_gate_resolved ──────────────────────────────────────────────────


class TestOnGateResolved:
    def test_gate_approve_triggers_save_v2(self):
        """SC#2 keystone — gate approve hits save-v2."""
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.on_gate_resolved("ep-1", "g-p03", "approve", {"phase_id": "p03"})
        client.close()
        saves = _save_calls(urls)
        assert len(saves) == 1

    def test_gate_approve_writes_gate_node(self):
        """Approve writes a g-{gate_id} node with reviewStatus=approved."""
        urls: list[tuple[str, str]] = []
        bodies: list[dict] = []
        client = make_mock_client(urls, captured_bodies=bodies)
        sub = CanvasSyncSubscriber(client)
        sub.on_gate_resolved("ep-1", "g-p03", "approve", {"phase_id": "p03"})
        client.close()
        save_bodies = [
            b for u, b in zip(urls, bodies) if u[1].endswith("/save-v2")
        ]
        graph = save_bodies[0]["graph"]
        gate_nodes = [n for n in graph["nodes"] if n.get("id") == "g-g-p03"]
        assert len(gate_nodes) == 1
        assert gate_nodes[0]["data"]["reviewStatus"] == "approved"

    def test_gate_reject_marks_phase_error(self):
        """Reject marks the associated phase node with state=error."""
        urls: list[tuple[str, str]] = []
        bodies: list[dict] = []
        client = make_mock_client(urls, captured_bodies=bodies)
        sub = CanvasSyncSubscriber(client)
        sub.on_gate_resolved(
            "ep-1", "g-p03", "reject", {"phase_id": "p03_script"}
        )
        client.close()
        save_bodies = [
            b for u, b in zip(urls, bodies) if u[1].endswith("/save-v2")
        ]
        graph = save_bodies[0]["graph"]
        phase_nodes = [
            n for n in graph["nodes"] if n.get("id") == "n-p03_script"
        ]
        assert len(phase_nodes) == 1
        assert phase_nodes[0]["state"] == "error"
        assert phase_nodes[0]["data"]["state"] == "error"


# ─── empty canvas + degrade tolerance ──────────────────────────────────


class TestEmptyCanvasAndDegrade:
    def test_empty_canvas_handled(self):
        """load_canvas returns None — on_phase_complete still saves valid graph."""
        urls: list[tuple[str, str]] = []
        bodies: list[dict] = []
        # load_data=None → empty canvas.
        client = make_mock_client(urls, captured_bodies=bodies, load_data=None)
        sub = CanvasSyncSubscriber(client)
        # Must not raise.
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()
        # A save still happened.
        saves = _save_calls(urls)
        assert len(saves) == 1
        save_bodies = [
            b for u, b in zip(urls, bodies) if u[1].endswith("/save-v2")
        ]
        # The saved graph has the skeleton (branches, meta, etc.).
        graph = save_bodies[0]["graph"]
        assert "branches" in graph and len(graph["branches"]) == 1
        assert graph["meta"]["version"] == "2"
        # And the upserted node.
        node_ids = [n.get("id") for n in graph["nodes"]]
        assert "n-p01_topic" in node_ids

    def test_canvas_unreachable_does_not_block(self):
        """CANVAS-IN-HERMES-03 keystone — connect error swallowed, no raise."""
        urls: list[tuple[str, str]] = []
        client = make_mock_client(
            urls, raise_on_request=httpx.ConnectError("connection refused")
        )
        sub = CanvasSyncSubscriber(client)
        # Must NOT raise.
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        # Gate path also must not raise.
        sub.on_gate_resolved("ep-1", "g-x", "approve", {})
        client.close()

    def test_canvas_4xx_swallowed(self):
        """4xx raises CanvasClientError inside — subscriber must catch it."""
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls, save_status=400)
        sub = CanvasSyncSubscriber(client)
        # Must NOT raise even though save_canvas raises CanvasClientError.
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()


# ─── subscriber isolation ──────────────────────────────────────────────


class TestSubscriberIsolation:
    def test_prev_phase_id_resets_per_subscriber(self):
        """Two separate subscribers track their own prev_phase_id."""
        urls1: list[tuple[str, str]] = []
        bodies1: list[dict] = []
        c1 = make_mock_client(urls1, captured_bodies=bodies1)
        s1 = CanvasSyncSubscriber(c1)
        s1.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})

        urls2: list[tuple[str, str]] = []
        bodies2: list[dict] = []
        c2 = make_mock_client(urls2, captured_bodies=bodies2)
        s2 = CanvasSyncSubscriber(c2)
        # s2 starts fresh — no link should be drawn to s1's p01.
        s2.on_phase_complete("ep-2", "p02_outline", {"stage_order": 1})

        c1.close()
        c2.close()

        # s2's graph should NOT contain a link from p01_topic.
        save_bodies2 = [
            b for u, b in zip(urls2, bodies2) if u[1].endswith("/save-v2")
        ]
        graph2 = save_bodies2[0]["graph"]
        link_ids = [l.get("id") for l in graph2.get("links", [])]
        assert not any("p01_topic" in lid for lid in link_ids), (
            f"s2 leaked prev_phase_id from s1: {link_ids}"
        )


# ─── no-legacy-references static check ─────────────────────────────────


class TestNoLegacyReferences:
    def test_no_openclaw_references(self):
        """SC: zero openclaw / Toonflow / sqlite references in either module.

        Strips docstrings and comments before scanning — the contract
        text in module docstrings legitimately mentions these names to
        declare they are absent; that's documentation, not a code
        reference. Only actual code (identifiers, imports, string
        literals outside docstrings) is checked.
        """
        import ast

        base = Path(__file__).resolve().parent.parent
        targets = [base / "canvas_sync.py", base / "canvas_graph.py"]
        pattern = re.compile(r"openclaw|Toonflow|sqlite", re.IGNORECASE)
        offenders: list[str] = []

        for target in targets:
            source = target.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(target))
            # Walk only code string constants (not docstrings). A
            # docstring is an Expr(Constant) that is the first statement
            # of a Module / FunctionDef / ClassDef. We collect the ids
            # of those Constant nodes and skip them.
            docstring_constant_ids: set[int] = set()
            for parent in ast.walk(tree):
                if isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if parent.body and isinstance(parent.body[0], ast.Expr):
                        expr = parent.body[0]
                        if isinstance(expr.value, ast.Constant) and isinstance(expr.value.value, str):
                            docstring_constant_ids.add(id(expr.value))
            for node in ast.walk(tree):
                if id(node) in docstring_constant_ids:
                    continue
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for match in pattern.finditer(node.value):
                        offenders.append(
                            f"{target.name} line {getattr(node, 'lineno', '?')}: '{match.group(0)}'"
                        )
                elif isinstance(node, ast.Name) and pattern.search(node.id):
                    offenders.append(
                        f"{target.name} line {node.lineno}: '{node.id}'"
                    )
        assert not offenders, f"legacy code references found: {offenders}"
