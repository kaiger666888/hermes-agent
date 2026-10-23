"""Degraded-envelope guards for the canvas sync entry points (review B-1/B-2).

``CanvasClient.load_canvas()`` / ``save_canvas()`` never raise on network
failures — they return a degrade envelope ``{degraded: True, reason, ...}``.
Before the B-1 fix, ``on_phase_complete`` / ``on_gate_resolved`` /
``sync_artifact_nodes`` fed that envelope into ``normalize_loaded_graph``
(which produces an EMPTY graph) and saved it — the server's delete-absent
semantics then irreversibly wiped every previously-synced node.

These tests mock the HTTP transport (PATTERN 4) so load-v2 fails at the
network layer (degrade envelope) while save-v2 would succeed, and assert:
  * no save-v2 is issued (the wipe never happens),
  * the failure is recorded via ``_log_sync_error`` (monkeypatched spy).
"""

from __future__ import annotations


import httpx
import pytest

from plugins.kais_aigc.canvas import CanvasClient
from plugins.kais_aigc import canvas_sync as cs
from plugins.kais_aigc.canvas_sync import CanvasSyncSubscriber


def make_degrading_client(
    urls: list[tuple[str, str]],
    *,
    degrade_load: bool = True,
    save_envelope_degraded: bool = False,
) -> CanvasClient:
    """Client whose load-v2 degrades at the transport layer.

    ``raise_on_request`` on load only — save-v2 answers 200 OK so a buggy
    implementation WOULD wipe the canvas (the exact B-1 scenario: load
    fails, the immediately-following save succeeds).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append((request.method, str(request.url)))
        if request.url.path.endswith("/load-v2") and degrade_load:
            raise httpx.ConnectError("simulated transient network failure")
        if request.url.path.endswith("/save-v2"):
            if save_envelope_degraded:
                # HTTP 500 → _request degrades to an envelope after retries.
                return httpx.Response(500, json={"error": "boom"})
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": {"ok": True}},
            )
        return httpx.Response(200, json={"code": 0, "msg": "ok", "data": {}})

    return CanvasClient(
        base_url="http://test-canvas:10588",
        project_id=1,
        episodes_id=1,
        transport=httpx.MockTransport(handler),
    )


def _save_calls(urls: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [u for u in urls if u[1].endswith("/api/canvas/v2/save-v2")]


@pytest.fixture
def error_spy(monkeypatch):
    """Spy on _log_sync_error — the failure must be VISIBLE, not silent."""
    calls: list[dict] = []

    def fake_log(phase_id, episode_id, error_type, detail, *, exc_info=None):
        calls.append({
            "phase_id": phase_id,
            "episode_id": episode_id,
            "error_type": error_type,
            "detail": detail,
        })

    monkeypatch.setattr(cs, "_log_sync_error", fake_log)
    return calls


# ─── B-1: load degrade envelope must not produce a save ────────────────


class TestOnPhaseCompleteLoadDegraded:
    def test_no_save_and_error_logged(self, error_spy):
        urls: list[tuple[str, str]] = []
        client = make_degrading_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete(
            "ep-1", "p12a_timeline_composition", {"stage_order": 0},
        )
        client.close()
        assert not _save_calls(urls), (
            "load degrade envelope MUST NOT be followed by a save — the "
            "empty graph would wipe the whole canvas (B-1)"
        )
        assert len(error_spy) == 1
        assert error_spy[0]["error_type"] == "CanvasLoadDegraded"
        assert "degrade envelope" in error_spy[0]["detail"]
        assert error_spy[0]["phase_id"] == "p12a_timeline_composition"


class TestOnGateResolvedLoadDegraded:
    def test_no_save_and_error_logged(self, error_spy):
        urls: list[tuple[str, str]] = []
        client = make_degrading_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.on_gate_resolved("ep-1", "gate-4", "approve", {"phase_id": "p09"})
        client.close()
        assert not _save_calls(urls), (
            "gate_resolved must not save after a degraded load (B-1)"
        )
        assert len(error_spy) == 1
        assert error_spy[0]["error_type"] == "CanvasLoadDegraded"
        assert "gate_resolved(approve)" in error_spy[0]["detail"]


class TestSyncArtifactNodesLoadDegraded:
    def test_no_save_and_error_logged(self, error_spy):
        urls: list[tuple[str, str]] = []
        client = make_degrading_client(urls)
        sub = CanvasSyncSubscriber(client)
        sub.sync_artifact_nodes(
            "ep-1", "p11b_final_render",
            [{"id": "clip-1", "type": "video", "label": "S01"}],
        )
        client.close()
        assert not _save_calls(urls), (
            "sync_artifact_nodes must not save after a degraded load (B-1)"
        )
        assert len(error_spy) == 1
        assert error_spy[0]["error_type"] == "CanvasLoadDegraded"
        assert "sync_artifact_nodes" in error_spy[0]["detail"]


class TestHealthyLoadStillSaves:
    def test_smoke_save_still_happens_on_healthy_load(self):
        """Guard the guard: a healthy load must still trigger exactly one save."""
        urls: list[tuple[str, str]] = []
        client = make_degrading_client(urls, degrade_load=False)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-1", "p01_topic", {"stage_order": 0})
        client.close()
        assert len(_save_calls(urls)) == 1


# ─── B-2: save degrade envelope must be visible + propagate False ──────


class TestOnPhaseCompleteSaveDegraded:
    def test_returns_false_and_logs_error(self, error_spy):
        """Healthy load + degraded save → on_phase_complete returns False."""
        urls: list[tuple[str, str]] = []
        client = make_degrading_client(
            urls, degrade_load=False, save_envelope_degraded=True,
        )
        sub = CanvasSyncSubscriber(client)
        ret = sub.on_phase_complete(
            "ep-1", "p01_topic", {"stage_order": 0},
        )
        client.close()
        # Save WAS attempted (the load succeeded, so we proceed to save).
        assert _save_calls(urls), "save-v2 should have been attempted"
        assert ret is False, (
            "on_phase_complete must return False when save degrades (B-2)"
        )
        assert any(e["error_type"] == "CanvasSaveDegraded" for e in error_spy)


class TestSyncPhaseResultSaveDegraded:
    def test_returns_false_on_save_envelope(self, error_spy, monkeypatch):
        """sync_phase_result must return False (not True) when save degrades.

        Before B-2 the function unconditionally returned True after
        on_phase_complete — an agent's manual re-sync tool would report
        success while nothing was persisted.
        """
        urls: list[tuple[str, str]] = []

        def make_client(**kwargs):
            return make_degrading_client(
                urls, degrade_load=False, save_envelope_degraded=True,
            )

        monkeypatch.setattr(cs, "CanvasClient", make_client)
        monkeypatch.setenv("KAIS_CANVAS_URL", "http://test-canvas:10588")
        monkeypatch.setenv("KAIS_CANVAS_PROJECT_ID", "1")
        monkeypatch.setenv("KAIS_CANVAS_EPISODES_ID", "1")
        ok = cs.sync_phase_result(
            episode_id="ep-1",
            phase_id="p01_topic",
            result={"phase": "p01_topic", "outputs": {}, "gate": None},
        )
        assert ok is False, (
            "sync_phase_result broke its 'returns False on any failure' "
            "contract when save degraded (B-2)"
        )

    def test_returns_true_on_healthy_path(self, error_spy, monkeypatch):
        """Guard the guard: healthy load+save still returns True."""
        urls: list[tuple[str, str]] = []

        def make_client(**kwargs):
            return make_degrading_client(urls, degrade_load=False)

        monkeypatch.setattr(cs, "CanvasClient", make_client)
        monkeypatch.setenv("KAIS_CANVAS_URL", "http://test-canvas:10588")
        monkeypatch.setenv("KAIS_CANVAS_PROJECT_ID", "1")
        monkeypatch.setenv("KAIS_CANVAS_EPISODES_ID", "1")
        ok = cs.sync_phase_result(
            episode_id="ep-1",
            phase_id="p01_topic",
            result={"phase": "p01_topic", "outputs": {}, "gate": None},
        )
        assert ok is True
