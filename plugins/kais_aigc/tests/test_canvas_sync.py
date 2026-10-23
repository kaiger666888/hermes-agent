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

from plugins.kais_aigc.canvas import CanvasClient, CanvasClientError
from plugins.kais_aigc.canvas_sync import (
    CanvasSyncSubscriber,
    CanvasSyncValidationError,
)


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

    def test_canvas_4xx_reraises(self):
        """4xx RE-RAISES per P0-3 runner 契约 ("同步失败就停，不掩盖问题").

        Decision (P0-3, 2026-08-08): CanvasClientError (4xx) is logged to
        canvas-sync-errors.jsonl AND re-raised so it propagates to
        runner._try_canvas_sync's exclusive re-raise, which halts the
        pipeline. A 4xx is a DATA problem (graph format/content violates
        canvas schema) that should surface immediately, not be masked.
        Network errors (ConnectError/TimeoutException) remain
        degrade-tolerant (see the connect-error test above).
        """
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls, save_status=400)
        sub = CanvasSyncSubscriber(client)
        # P0-3: 4xx must RE-RAISE — propagate to runner to halt the pipeline.
        with pytest.raises(CanvasClientError):
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


class TestSyncPhaseResultShapeGuard:
    """Regression: sync_phase_result must auto-unwrap the persisted
    wrapper shape ``{status, completed_at, result: {...}}`` (or
    ``{phase, result: {...}}``) before delegating to on_phase_complete.

    Without the guard, calling sync_phase_result with the wrapper shape
    extracts zero artifacts (no top-level ``outputs`` key), and the
    subsequent full-graph UPSERT silently DELETES previously-synced
    artifact nodes for that phase. Observed 2026-07-15 on ep-cat-heist.
    """

    @staticmethod
    def _make_handler(captured_bodies: list[dict]):
        def handler(request: httpx.Request) -> httpx.Response:
            content = json.loads(request.content.decode("utf-8"))
            if request.url.path.endswith("/load-v2"):
                return httpx.Response(200, json={
                    "code": 200,
                    "data": {
                        "meta": {"version": "2", "projectId": 1, "episodesId": 1,
                                 "createdAt": 1, "updatedAt": 1, "lastEventId": 0},
                        "nodes": [], "links": [], "branches": [],
                    },
                })
            if request.url.path.endswith("/save-v2"):
                captured_bodies.append(content)
                return httpx.Response(200, json={"code": 200, "data": None})
            return httpx.Response(404)
        return handler

    def _patch_client(self, monkeypatch, captured):
        from plugins.kais_aigc import canvas_sync as cs
        handler = self._make_handler(captured)
        orig_init = cs.CanvasClient.__init__
        def _patched_init(self, **kw):
            orig_init(self, **kw)
            self._client = httpx.Client(
                transport=httpx.MockTransport(handler),
                timeout=self._timeout,
            )
        monkeypatch.setattr(cs.CanvasClient, "__init__", _patched_init)

    def test_unwraps_pipeline_state_wrapper(self, monkeypatch):
        """Wrapper ``{status, completed_at, result: {...}}`` is unwrapped
        so on_phase_complete sees the real outputs."""
        from plugins.kais_aigc import canvas_sync as cs
        monkeypatch.setenv("KAIS_CANVAS_URL", "http://test.local")
        monkeypatch.setenv("KAIS_CANVAS_PROJECT_ID", "1")
        monkeypatch.setenv("KAIS_CANVAS_EPISODES_ID", "1")

        captured: list[dict] = []
        self._patch_client(monkeypatch, captured)

        outputs = {
            "topic_kernel": {"audience_pain": "x", "topic_nucleus": "y"},
            "hook_design": {"hook_type": "open", "candidates": [{"id": "h1"}]},
        }
        wrapper = {"status": "completed", "completed_at": "2026-07-15",
                   "result": {"phase": "p01_hook_topic", "outputs": outputs}}
        ok = cs.sync_phase_result(
            episode_id="ep-test", phase_id="p01_hook_topic", result=wrapper,
        )
        assert ok is True
        assert captured, "save-v2 was never called"
        saved_graph = captured[-1]["graph"]
        node_ids = [n["id"] for n in saved_graph["nodes"]]
        assert any(i.startswith("a-") for i in node_ids), \
            f"no artifact nodes saved — wrapper was not unwrapped. ids={node_ids}"

    def test_passthrough_live_shape_unchanged(self, monkeypatch):
        """Direct live shape ``{phase, outputs, gate}`` is NOT mutated —
        the guard must be a no-op for correctly-shaped input."""
        from plugins.kais_aigc import canvas_sync as cs
        monkeypatch.setenv("KAIS_CANVAS_URL", "http://test.local")
        monkeypatch.setenv("KAIS_CANVAS_PROJECT_ID", "1")
        monkeypatch.setenv("KAIS_CANVAS_EPISODES_ID", "1")

        captured: list[dict] = []
        self._patch_client(monkeypatch, captured)

        outputs = {"topic_kernel": {"x": 1}, "hook_design": {"y": 2}}
        live = {"phase": "p01_hook_topic", "outputs": outputs, "gate": None}
        ok = cs.sync_phase_result(
            episode_id="ep-test", phase_id="p01_hook_topic", result=live,
        )
        assert ok is True
        assert captured
        saved_graph = captured[-1]["graph"]
        node_ids = [n["id"] for n in saved_graph["nodes"]]
        assert any(i.startswith("a-") for i in node_ids), \
            f"live shape should produce artifacts. ids={node_ids}"


class TestNoLegacyReferences:
    def test_no_openclaw_references(self):
        """SC: zero openclaw / Toonflow references in either module.

        Strips docstrings and comments before scanning — the contract
        text in module docstrings legitimately mentions these names to
        declare they are absent; that's documentation, not a code
        reference. Only actual code (identifiers, imports, string
        literals outside docstrings) is checked.
        """
        import ast

        base = Path(__file__).resolve().parent.parent
        targets = [base / "canvas_sync.py", base / "canvas_graph.py"]
        pattern = re.compile(r"openclaw|Toonflow", re.IGNORECASE)
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


# ─── P2-2: post-sync validation (node-count A + round-trip C) ──────────


class TestPostSyncNodeCountAssertion:
    """P2-2 validator A — ``_assert_node_count`` (default-on, zero-cost)."""

    def test_passes_when_all_expected_nodes_present(self):
        """A graph that contains the phase summary + every artifact node passes."""
        client = make_mock_client([])
        sub = CanvasSyncSubscriber(client)
        graph = {
            "nodes": [
                {"id": "n-p01_topic"},
                {"id": "a-topic-kernel"},
                {"id": "a-hook"},
            ],
            "links": [],
        }
        art_node_ids = [("a-topic-kernel", {}), ("a-hook", {})]
        # Must not raise.
        sub._assert_node_count(graph, art_node_ids, "p01_topic")
        client.close()

    def test_raises_when_artifact_node_missing(self):
        """A missing artifact node → CanvasSyncValidationError (fail-loud)."""
        client = make_mock_client([])
        sub = CanvasSyncSubscriber(client)
        graph = {"nodes": [{"id": "n-p01_topic"}], "links": []}
        art_node_ids = [("a-topic-kernel", {}), ("a-hook", {})]
        with pytest.raises(CanvasSyncValidationError, match="node-count"):
            sub._assert_node_count(graph, art_node_ids, "p01_topic")
        client.close()

    def test_passes_with_no_artifacts(self):
        """Zero artifacts + only the phase summary node present → passes."""
        client = make_mock_client([])
        sub = CanvasSyncSubscriber(client)
        graph = {"nodes": [{"id": "n-p02_outline"}], "links": []}
        sub._assert_node_count(graph, [], "p02_outline")
        client.close()

    def test_assertion_runs_in_normal_flow(self):
        """A is default-on: a normal on_phase_complete (with artifacts) must
        not raise — the just-built nodes are present in the local graph."""
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls)
        sub = CanvasSyncSubscriber(client)
        # selectedTopic produces an artifact node under p01.
        sub.on_phase_complete(
            "ep-1", "p01_topic",
            {"summary": {"selectedTopic": "X"}, "stage_order": 0},
        )
        client.close()
        # A save happened (flow reached past the assertion).
        assert len(_save_calls(urls)) == 1


class TestPostSyncRoundtripProbe:
    """P2-2 validator C — ``_roundtrip_probe`` (env-gated)."""

    def test_probe_matches_when_counts_equal(self):
        """Reloaded node/link counts == saved → no raise."""
        client = make_mock_client(
            [],
            load_data={
                "nodes": [{"id": "a"}, {"id": "b"}],
                "links": [{"source": "a", "target": "b"}],
            },
        )
        sub = CanvasSyncSubscriber(client)
        sub._roundtrip_probe(
            "p01_topic", saved_counts={"nodes": 2, "links": 1},
        )
        client.close()

    def test_probe_raises_on_node_mismatch(self):
        """Reloaded node count < saved → silent partial persist → raise."""
        client = make_mock_client(
            [], load_data={"nodes": [{"id": "a"}], "links": []},
        )
        sub = CanvasSyncSubscriber(client)
        with pytest.raises(
            CanvasSyncValidationError, match="Round-trip probe failed",
        ):
            sub._roundtrip_probe(
                "p01_topic", saved_counts={"nodes": 5, "links": 2},
            )
        client.close()

    def test_probe_skips_when_load_degrades(self):
        """A degrade envelope (transient network/5xx) is NOT a partial persist
        — the probe must skip rather than false-positive a pipeline stop."""
        client = make_mock_client(
            [],
            load_data={"degraded": True, "reason": "connect error"},
        )
        sub = CanvasSyncSubscriber(client)
        # Must not raise even though counts would mismatch.
        sub._roundtrip_probe(
            "p01_topic", saved_counts={"nodes": 99, "links": 99},
        )
        client.close()

    def test_probe_disabled_by_default(self, monkeypatch):
        """Without KAIS_CANVAS_ROUNDTRIP, no extra load after save (1 load only)."""
        monkeypatch.delenv("KAIS_CANVAS_ROUNDTRIP", raising=False)
        urls: list[tuple[str, str]] = []
        client = make_mock_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()
        # Only the initial load-v2 (before save); the probe's load is gated off.
        assert len(_load_calls(urls)) == 1

    def test_probe_enabled_fires_second_load(self, monkeypatch):
        """With KAIS_CANVAS_ROUNDTRIP=1, the probe issues a second load-v2."""
        monkeypatch.setenv("KAIS_CANVAS_ROUNDTRIP", "1")
        urls: list[tuple[str, str]] = []
        # Stateful handler: persist the saved graph so the probe reload matches.
        persisted: dict = {"nodes": [], "links": []}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal persisted
            urls.append((request.method, str(request.url)))
            path = request.url.path
            if path.endswith("/load-v2"):
                return httpx.Response(
                    200, json={"code": 0, "msg": "ok", "data": persisted},
                )
            if path.endswith("/save-v2"):
                body = json.loads(request.content) if request.content else {}
                persisted = body.get("graph", persisted)
                return httpx.Response(
                    200, json={"code": 0, "msg": "ok", "data": {"ok": True}},
                )
            return httpx.Response(404)

        client = CanvasClient(
            base_url="http://test-canvas:10588",
            project_id=1, episodes_id=1,
            transport=httpx.MockTransport(handler),
        )
        sub = CanvasSyncSubscriber(client)
        # Must not raise — the stateful mock persists, so the round-trip matches.
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()
        # Initial load + probe load = 2.
        assert len(_load_calls(urls)) == 2

    def test_probe_enabled_propagates_validation_error(self, monkeypatch):
        """When enabled and the reload mismatches (static mock does not
        persist), on_phase_complete must RE-RAISE CanvasSyncValidationError —
        not swallow it via the degrade-tolerant ``except Exception``
        (the P0-3 anti-pattern)."""
        monkeypatch.setenv("KAIS_CANVAS_ROUNDTRIP", "1")
        urls: list[tuple[str, str]] = []
        # load_data=None → reload returns empty (0 nodes) while the saved graph
        # has the phase summary node → mismatch.
        client = make_mock_client(urls, load_data=None)
        sub = CanvasSyncSubscriber(client)
        with pytest.raises(CanvasSyncValidationError, match="Round-trip"):
            sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()


# ─── 71-01/71-02 (v3.2 F05/COX-01/02): 删建抢救画布编辑 + stale 生命周期 ──


class TestCoexistenceMerge:
    """裁决点2a(画布为配方真值):B-4 删建不蒸发用户 prompt;kmc 重同步清 stale。"""

    def test_b4_preserves_user_edited_prompt(self):
        """旧 a-* 节点 data.prompt != _kmc_prompt(用户改过)→ 删建后恢复。"""
        # 第一轮:同步 p03 带 artifacts(script-candidates 或 outputs)
        load_round1 = {
            "nodes": [], "links": [],
            "meta": {"version": "3", "projectId": 1, "episodesId": 1},
        }
        urls, bodies = [], []
        client = make_mock_client(urls, captured_bodies=bodies, load_data=load_round1)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete(
            "ep-1", "p03_script_audit",
            {"outputs": {"script": {"description": "第一版剧本",
                                    "logline": "雨夜遭遇"}},
             "stage_order": 0},
        )
        client.close()
        save1 = next(b for b in bodies if str(b).find("save-v2") < 0 and b.get("graph"))
        art1 = next(
            n for n in save1["graph"]["nodes"] if str(n.get("id", "")).startswith("a-")
        )
        # 用户画布编辑:prompt 改、_kmc_prompt 哨兵不动
        art1_edited = json.loads(json.dumps(art1))
        art1_edited["data"]["prompt"] = "用户改过的配方:改运镜为推近"
        art1_edited["data"]["stale"] = "prompt-edited"

        # 第二轮:kmc 重跑同 phase(B-4 删建路径)
        load_round2 = {
            "nodes": [art1_edited], "links": [],
            "meta": {"version": "3", "projectId": 1, "episodesId": 1},
        }
        urls2, bodies2 = [], []
        client2 = make_mock_client(urls2, captured_bodies=bodies2, load_data=load_round2)
        sub2 = CanvasSyncSubscriber(client2)
        sub2.on_phase_complete(
            "ep-1", "p03_script_audit",
            {"outputs": {"script": {"description": "第二版剧本",
                                    "logline": "雨夜遭遇"}},
             "stage_order": 0},
        )
        client2.close()
        save2 = next(b for b in bodies2 if b.get("graph"))
        same_id = next(
            (n for n in save2["graph"]["nodes"] if n.get("id") == art1_edited["id"]),
            None,
        )
        assert same_id is not None, "重建后同 id 节点应在场(或新产物节点)"
        if same_id is not None:
            assert same_id["data"].get("prompt") == "用户改过的配方:改运镜为推近", \
                "用户画布编辑必须存活 B-4 删建(裁决点2a)"

    def test_resync_clears_stale(self):
        """71-02:旧节点 data.stale 在 kmc 重同步后清除(不再永久残留)。"""
        import plugins.kais_aigc.canvas_graph as cg
        graph = {
            "nodes": [
                {"id": "n-p02_outline", "type": "script",
                 "data": {"label": "P02", "stale": "upstream-changed"}},
            ],
            "links": [],
        }
        cg.upsert_node(graph, "n-p02_outline", {
            "type": "script", "data": {"label": "P02", "description": "重跑完成"},
        })
        assert "stale" not in graph["nodes"][0]["data"], \
            "kmc 重同步 = 新真值,stale 应清除(deep-merge 残留是 F05 根因)"
