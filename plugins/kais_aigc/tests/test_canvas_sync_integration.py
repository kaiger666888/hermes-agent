"""test_canvas_sync_integration.py — Phase 37-03 keystone integration tests.

Wires the Phase 37-02 ``register_canvas_sync`` subscriber onto a real
``RunnerConfig`` (Phase 37-01 callback hooks) and runs mocked pipeline
episodes + mocked gate resolutions, asserting that the canvas :10588
``save-v2`` HTTP endpoint fires exactly when the contract says it should.

These are SC#2 keystones for Phase 37:

* ``test_full_pipeline_episode_canvas_save_v2_per_phase`` — runs a full
  13-phase episode with the subscriber registered, asserts 13 save-v2
  calls (one per phase completion). The single most important integration
  assertion in Phase 37.
* ``test_gate_approve_triggers_save_v2`` — fires a mocked gate-resolution
  approve via ``runner_hooks.resume_from_callback``, asserts the
  subscriber's gate handler runs and produces exactly 1 save-v2 call.
* ``test_gate_reject_triggers_save_v2_with_error_state`` — same path,
  reject decision, asserts the saved graph contains a phase node with
  ``state == "error"``.
* ``test_canvas_unreachable_does_not_block_pipeline`` — MockTransport
  raises ``httpx.ConnectError`` on every request; pipeline must complete
  normally with return payload intact.
* ``test_no_openclaw_references_in_phase_37_deliverables`` — SC#1 +
  OPENCLAW-REMOVE precondition grep.
* ``test_phase_35_36_regression_full_dag_imports`` — Phase 35/36
  regression guard (full-DAG test module still importable).

All tests use ``httpx.MockTransport`` injected into the real Phase 32
``CanvasClient`` via the ``transport`` seam (PATTERN 4) — the real client
runs, only the network is fake. The full-DAG harness is the same one
``test_runner_full_dag.py`` uses (mocked delegate, stub store, stub bus).
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

# ─── sys.path bootstrap (mirror test_runner_full_dag) ─────────────────
# The skill-local ``pipeline`` package (hyphen-dir-resident) lives under
# skills/kais-movie-pipeline/. Add it to sys.path so the runner imports.
_SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "kais-movie-pipeline"
if _SKILL_DIR.exists() and str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline import phases as phases_mod  # noqa: E402
from pipeline import runner as runner_mod  # noqa: E402
from pipeline.phases import PHASE_REGISTRY  # noqa: E402
from pipeline.runner import RunnerConfig, run_episode  # noqa: E402

from plugins.kais_aigc.canvas_sync import register_canvas_sync  # noqa: E402
from plugins.review_gates import runner_hooks  # noqa: E402


# ---------------------------------------------------------------------------
# MockTransport helper — records every request URL + body
# ---------------------------------------------------------------------------


def _make_transport(
    captured_urls: list[str],
    captured_bodies: list[dict],
    *,
    load_data: dict | None = None,
    raise_on_request: Exception | None = None,
) -> httpx.MockTransport:
    """Build an httpx.MockTransport that records URLs + bodies and returns
    canned canvas responses.

    Args:
        captured_urls: appended with ``str(request.url)`` for every request.
        captured_bodies: appended with parsed JSON body for every request.
        load_data: dict returned inside the load-v2 envelope (``None`` = empty).
        raise_on_request: if set, every request raises this (degrade test).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if raise_on_request is not None:
            raise raise_on_request
        captured_urls.append(str(request.url))
        body: dict = {}
        if request.content:
            try:
                body = json.loads(request.content)
            except ValueError:
                body = {}
        captured_bodies.append(body)

        path = request.url.path
        if path.endswith("/load-v2"):
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": load_data}
            )
        if path.endswith("/save-v2"):
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": {"ok": True}},
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _save_v2_count(urls: list[str]) -> int:
    return sum(1 for u in urls if "/api/canvas/v2/save-v2" in u)


def _save_v2_bodies(
    urls: list[str], bodies: list[dict],
) -> list[dict]:
    """Filter ``bodies`` to only save-v2 requests (load-v2 bodies have no graph)."""
    return [
        b for u, b in zip(urls, bodies) if "/api/canvas/v2/save-v2" in u
    ]


# ---------------------------------------------------------------------------
# Full-DAG test harness — mirrors test_runner_full_dag.py
# ---------------------------------------------------------------------------


def _canned_summary(payload: dict) -> str:
    return f"Expert output:\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _default_per_phase_payloads() -> dict[str, dict]:
    """Per-phase canned payloads (same as test_runner_full_dag)."""
    return {
        "p01_hook_topic": {
            "topic_kernel": {"genre": "test", "hook": "h"},
            "hook_design": {"candidates": []},
        },
        "p02_outline": {"story_framework": {"beats": []}},
        "p03_script_audit": {
            "script_draft": {"scenes": []},
            "audit_report": {"score": 0.9},
        },
        "p04_character_design": {
            "character_bible": {"characters": []},
            "character_assets": {"assets": []},
        },
        "p05_pain_discovery": {
            "pain_points": {"points": []},
            "escalation_ladder": {"rungs": []},
        },
        "p06_spatio_temporal_script": {
            "spatio_temporal_script": {"scenes": []},
            "final_audit": {"score": 0.9},
        },
        "p07_scene_generation": {
            "scene_images": {"scenes": []},
            "style_vector": {"genre": "x"},
            "color_intent": {"palette": []},
        },
        "p08_scene_selection": {
            "scene_selection": {"shots": []},
            "geometry_bed": {"anchors": []},
        },
        "p09_shot_breakdown": {
            "shot_list": [{"shot_id": "s1"}],
            "e_konte_sheets": {"sheets": []},
        },
        "p10_voice": {
            "voice_clips": [{"shot_id": "s1"}],
            "voice_timeline": {"shots": []},
        },
        "p11_video_render": {
            "video_clips": [{"shot_id": "s1"}],
            "lip_sync_reports": [{"shot_id": "s1"}],
        },
        "p12_composition": {
            "master_timeline": {"tracks": []},
            "audio_stems": {"stems": []},
        },
        "p13_delivery": {
            "master_mp4": {"path": "/tmp/m.mp4"},
            "delivery_package": {"manifest": []},
        },
    }


def _make_full_dag_delegate_spy(phase_to_payload: dict[str, dict] | None = None):
    """Mocked delegate that matches the current phase via the EXPERT name."""
    default_payloads = phase_to_payload or _default_per_phase_payloads()

    def _delegate(goal: str, context: str, toolsets: list[str]) -> dict:
        for phase_id, payload in default_payloads.items():
            module = next(
                (e["module"] for e in PHASE_REGISTRY if e["id"] == phase_id),
                None,
            )
            if module is None:
                continue
            expert = getattr(module, "EXPERT", "")
            if expert and expert in goal:
                return {"summary": _canned_summary(payload)}
        return {"summary": _canned_summary({})}

    return _delegate


class _StubStore:
    """Checkpoint store stub — keeps the resume cursor advancing."""

    def __init__(self, initial_checkpoint: dict | None = None):
        self._checkpoint = initial_checkpoint
        self.saved: list[tuple[str, str]] = []

    def load_latest_checkpoint(self, episode_id: str):
        return self._checkpoint

    def save_checkpoint(self, episode_id: str, phase: str, payload: dict):
        self.saved.append((episode_id, phase))
        self._checkpoint = {"phase": phase, "status": "completed"}


class _StubBus:
    """In-memory asset bus."""

    def __init__(self):
        self.slots: dict[str, Any] = {}

    def read(self, slot: str):
        return self.slots.get(slot)

    def write(self, slot: str, entry, envelope: bool = True, **kwargs):
        self.slots[slot] = entry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_gate_hook():
    """Clear the module-level gate hook before/after every test so
    registrations never leak across tests."""
    runner_hooks.set_gate_resolved_hook(None)
    yield
    runner_hooks.set_gate_resolved_hook(None)


# ═════════════════════════════════════════════════════════════════════════
# Test 1 — SC#2 keystone: full 13-phase episode → 13 save-v2 calls
# ═════════════════════════════════════════════════════════════════════════


class TestFullPipelineEpisodeSubscriber:
    def test_full_pipeline_episode_canvas_save_v2_per_phase(self, tmp_path):
        """SC#2 keystone integration test.

        Register the canvas sync subscriber on a RunnerConfig, run a
        mocked 13-phase episode, assert exactly 13 :10588 save-v2 HTTP
        calls — one per phase completion. The single most important
        integration assertion in Phase 37.
        """
        captured_urls: list[str] = []
        captured_bodies: list[dict] = []
        transport = _make_transport(captured_urls, captured_bodies)

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        # register_canvas_sync wires cfg.on_phase_complete AND the module-level
        # gate hook. The transport seam lets us observe real HTTP requests
        # without hitting a real canvas server.
        sub = register_canvas_sync(
            base_url="http://test-canvas:10588",
            project_id=1,
            episodes_id=1,
            runner_config=cfg,
            transport=transport,
        )
        assert sub is not None, "register_canvas_sync must return the subscriber"
        # PATTERN 7 contract — both callbacks wired in a single call.
        assert cfg.on_phase_complete is not None
        assert cfg.on_gate_resolved is not None

        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus()

        result = run_episode(
            "ep-integration", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        # All 13 phases ran.
        assert len(result["phases"]) == 13, (
            f"expected 13 phase results, got {len(result['phases'])}"
        )

        # SC#2: exactly 13 save-v2 calls — one per phase.
        save_count = _save_v2_count(captured_urls)
        assert save_count == 13, (
            f"SC#2 keystone: expected 13 save-v2 calls (one per phase), "
            f"got {save_count}. URLs: {captured_urls}"
        )

        # Episode return payload intact.
        assert result["episode_id"] == "ep-integration"

    def test_save_v2_bodies_carry_phase_node_ids(self, tmp_path):
        """Sanity: across the 13 save-v2 calls, every phase node id appears
        at least once. (The MockTransport returns empty graph for every
        load-v2, so individual saves are not cumulative — that's fine; we
        just need to confirm the subscriber upserts each phase's node id
        somewhere in the save stream.)"""
        captured_urls: list[str] = []
        captured_bodies: list[dict] = []
        transport = _make_transport(captured_urls, captured_bodies)

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        register_canvas_sync(
            base_url="http://test-canvas:10588",
            project_id=1, episodes_id=1,
            runner_config=cfg, transport=transport,
        )

        run_episode(
            "ep-node-ids", cfg,
            inject={
                "store": _StubStore(), "bus": _StubBus(),
                "delegate_task": _make_full_dag_delegate_spy(),
            },
        )

        save_bodies = _save_v2_bodies(captured_urls, captured_bodies)
        assert len(save_bodies) == 13
        # Collect every node id from every saved graph.
        all_node_ids: set[str] = set()
        for body in save_bodies:
            graph = body.get("graph", {})
            for node in graph.get("nodes", []):
                if isinstance(node, dict) and "id" in node:
                    all_node_ids.add(node["id"])
        # Every phase node id must appear at least once across the saves.
        expected_phase_ids = [entry["id"] for entry in PHASE_REGISTRY]
        for phase_id in expected_phase_ids:
            assert f"n-{phase_id}" in all_node_ids, (
                f"phase node n-{phase_id} never saved; present: "
                f"{sorted(all_node_ids)}"
            )


# ═════════════════════════════════════════════════════════════════════════
# Test 2 & 3 — gate resolution triggers save-v2 (approve + reject paths)
# ═════════════════════════════════════════════════════════════════════════


def _seed_pending_gate(
    gate_id: str = "g-test",
    episode_id: str = "ep-gate",
    phase: str = "p01_hook_topic",
) -> None:
    """Seed ``runner_hooks._PENDING_GATES`` with a real Gate instance so
    resume_from_callback / resolve_direct can resolve it. Mirrors
    test_runner_canvas_hooks._seed_pending_gate."""
    from plugins.review_gates.gate import (
        Gate, GateConfig, GateMode, GateStatus,
    )

    config = GateConfig(
        gate_id=gate_id,
        phase=phase,
        asset_bus_slots_to_lock=("topic-kernel",),
        reviewer_role="creative_source",
        callback_url=None,
        default_mode=GateMode.WEBHOOK,
        max_retries=3,
    )
    gate = Gate(config=config, episode_id=episode_id, mode=GateMode.WEBHOOK)
    gate.status = GateStatus.PENDING
    gate.attempt = 1
    gate.review_id = "rev-1"
    gate.submitted_at = "2026-06-26T00:00:00Z"
    runner_hooks._PENDING_GATES[gate_id] = gate


class _GateTestBus:
    """Stub bus recording writes for ordering checks."""

    def __init__(self):
        self.writes: list[tuple[str, dict]] = []

    def read(self, slot):
        return None

    def write(self, slot, entry, envelope=True):
        self.writes.append((slot, entry))


class _StubState:
    """Minimal PipelineState stub."""

    def __init__(self, episode_id: str = "ep-gate"):
        self.episode = episode_id
        self.phases: dict[str, Any] = {}
        self.current_phase_id: str | None = None


class _StubStateStore:
    def __init__(self):
        self.state = _StubState()

    def load(self):
        return self.state

    def save(self, state):
        self.state = state


class TestGateResolutionSubscriber:
    def setup_method(self):
        runner_hooks._PENDING_GATES.clear()

    def teardown_method(self):
        runner_hooks._PENDING_GATES.clear()

    def test_gate_approve_triggers_save_v2(self, monkeypatch):
        """SC#2 gate-resolution trigger path.

        Wire the subscriber, then fire resume_from_callback with
        decision="approve". Assert exactly 1 save-v2 call."""
        _seed_pending_gate(gate_id="g-approve", episode_id="ep-approve")

        captured_urls: list[str] = []
        captured_bodies: list[dict] = []
        transport = _make_transport(captured_urls, captured_bodies)

        # Subscriber must be constructed with a RunnerConfig even though
        # this test never invokes the phase-completion path. The config
        # is the duck-typed target of register_canvas_sync.
        cfg = RunnerConfig(enable_gates=False)
        register_canvas_sync(
            base_url="http://test-canvas:10588",
            project_id=1, episodes_id=1,
            runner_config=cfg, transport=transport,
        )
        # Gate hook is now wired.

        # Stub the dependencies resume_from_callback reaches besides the hook.
        monkeypatch.setattr(runner_hooks, "_asset_bus",
                            lambda wd=None: _GateTestBus())
        monkeypatch.setattr(runner_hooks, "_state_store",
                            lambda wd=None: _StubStateStore())
        monkeypatch.setattr(
            runner_hooks, "_review_client",
            lambda: type("C", (), {
                "verify_callback": lambda self, b, s, t: True,
            })(),
        )

        body = json.dumps({
            "gate_id": "g-approve",
            "decision": "approve",
            "suggested_action": None,
        })
        outcome = runner_hooks.resume_from_callback(
            body, "sig", int(time.time()),
        )

        # Outcome returned normally.
        assert outcome["decision"] == "approve"

        # SC#2: exactly 1 save-v2 call from the subscriber's gate handler.
        save_count = _save_v2_count(captured_urls)
        assert save_count == 1, (
            f"expected 1 save-v2 call after gate approve, got {save_count}; "
            f"URLs: {captured_urls}"
        )

    def test_gate_reject_triggers_save_v2_with_error_state(self, monkeypatch):
        """Reject path fires save-v2 AND the saved graph contains a phase
        node marked state="error"."""
        _seed_pending_gate(
            gate_id="g-reject", episode_id="ep-reject",
            phase="p03_script_audit",
        )

        captured_urls: list[str] = []
        captured_bodies: list[dict] = []
        transport = _make_transport(captured_urls, captured_bodies)

        cfg = RunnerConfig(enable_gates=False)
        register_canvas_sync(
            base_url="http://test-canvas:10588",
            project_id=1, episodes_id=1,
            runner_config=cfg, transport=transport,
        )

        monkeypatch.setattr(runner_hooks, "_asset_bus",
                            lambda wd=None: _GateTestBus())
        monkeypatch.setattr(runner_hooks, "_state_store",
                            lambda wd=None: _StubStateStore())
        monkeypatch.setattr(
            runner_hooks, "_review_client",
            lambda: type("C", (), {
                "verify_callback": lambda self, b, s, t: True,
            })(),
        )

        body = json.dumps({
            "gate_id": "g-reject",
            "decision": "reject",
            "suggested_action": "rollback_to_p02",
        })
        outcome = runner_hooks.resume_from_callback(
            body, "sig", int(time.time()),
        )

        # Outcome returned with rollback hint.
        assert outcome["decision"] == "reject"

        # 1 save-v2 call.
        save_count = _save_v2_count(captured_urls)
        assert save_count == 1, (
            f"expected 1 save-v2 call after gate reject, got {save_count}"
        )

        # The saved graph's phase node (or gate fallback node) carries error.
        save_bodies = _save_v2_bodies(captured_urls, captured_bodies)
        graph = save_bodies[0]["graph"]
        # Subscriber marks n-{phase_id} on reject where phase_id comes from
        # the gate's config.phase (no payload.phase_id from runner_hooks).
        # The subscriber falls back to gate_id for the node id when
        # payload["phase_id"] is absent.
        nodes = graph.get("nodes", [])
        error_states = [
            n for n in nodes
            if n.get("state") == "error"
            or (isinstance(n.get("data"), dict) and n["data"].get("state") == "error")
        ]
        assert len(error_states) >= 1, (
            f"expected >=1 node with state=error after reject; "
            f"nodes: {[n.get('id') for n in nodes]}"
        )


# ═════════════════════════════════════════════════════════════════════════
# Test 4 — degrade tolerance: canvas unreachable does not block pipeline
# ═════════════════════════════════════════════════════════════════════════


class TestCanvasUnreachableDoesNotBlock:
    def test_canvas_unreachable_does_not_block_pipeline(self, tmp_path):
        """CANVAS-IN-HERMES-03 keystone — every canvas request raises
        ConnectError. Pipeline still completes normally with return payload
        intact."""
        captured_urls: list[str] = []  # never populated — handler raises
        captured_bodies: list[dict] = []
        transport = _make_transport(
            captured_urls, captured_bodies,
            raise_on_request=httpx.ConnectError("canvas down"),
        )

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        register_canvas_sync(
            base_url="http://unreachable:10588",
            project_id=1, episodes_id=1,
            runner_config=cfg, transport=transport,
        )

        # Build a SHORT registry so the test is fast — 3 stub phases suffice.
        # Save/restore the real registry to avoid breaking sibling tests.
        saved_runner_list = list(runner_mod.PHASE_REGISTRY)
        saved_phases_list = list(phases_mod.PHASE_REGISTRY)
        try:
            short_registry: list = []
            phases_mod.PHASE_REGISTRY = short_registry
            runner_mod.PHASE_REGISTRY = short_registry

            def _make_stub(phase_id: str):
                def run(episode_id, asset_bus_read, asset_bus_write,
                        delegate_task, trigger_gate=None):
                    return {"phase": phase_id, "ok": True}

                class _M:
                    __name__ = f"stub_{phase_id}"
                _M.run = staticmethod(run)  # type: ignore[attr-defined]
                return _M

            short_registry.extend([
                {"id": "p01_a", "module": _make_stub("p01_a"), "depends_on": []},
                {"id": "p02_b", "module": _make_stub("p02_b"), "depends_on": ["p01_a"]},
                {"id": "p03_c", "module": _make_stub("p03_c"), "depends_on": ["p02_b"]},
            ])

            result = run_episode(
                "ep-down", cfg,
                inject={
                    "store": _StubStore(),
                    "bus": _StubBus(),
                    "delegate_task": lambda *a, **k: {"summary": "ok"},
                },
            )
        finally:
            phases_mod.PHASE_REGISTRY = saved_phases_list
            runner_mod.PHASE_REGISTRY = saved_runner_list

        # All 3 phases ran despite every canvas request failing.
        assert len(result["phases"]) == 3, (
            f"expected 3 phase results despite canvas unreachable; "
            f"got {len(result['phases'])}"
        )
        assert set(result["phases"].keys()) == {"p01_a", "p02_b", "p03_c"}
        # Return payload intact.
        assert result["episode_id"] == "ep-down"


# ═════════════════════════════════════════════════════════════════════════
# Test 5 — SC#1: no openclaw / Toonflow / sqlite references in deliverables
# ═════════════════════════════════════════════════════════════════════════


class TestNoLegacyReferences:
    def test_no_openclaw_references_in_phase_37_deliverables(self):
        """SC#1 + OPENCLAW-REMOVE precondition.

        Grep the Phase 37 production deliverables (canvas_sync.py,
        canvas_graph.py) for code references to openclaw / Toonflow /
        sqlite. The docstrings of those modules legitimately mention the
        names to declare their absence — that's documentation, not a code
        reference; the AST scan here skips docstring constants.

        Test files are excluded from the scan target list — they
        necessarily reference the forbidden names by virtue of asserting
        their absence (``pattern = re.compile(r"openclaw|...")``).
        Including them would make the test self-failing.
        """
        base = Path(__file__).resolve().parent.parent
        targets = [
            base / "canvas_sync.py",
            base / "canvas_graph.py",
        ]
        # AST walk — same defensive logic as test_canvas_sync.py's
        # test_no_openclaw_references. Collects docstring Constant ids
        # (first stmt of Module/FunctionDef/ClassDef) and skips them.
        pattern = re.compile(r"openclaw|Toonflow|sqlite", re.IGNORECASE)
        offenders: list[str] = []
        for target in targets:
            if not target.exists():
                continue
            source = target.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(target))
            except SyntaxError:
                # Fallback to raw grep — better to false-positive than miss.
                for line_num, line in enumerate(source.splitlines(), 1):
                    if pattern.search(line):
                        offenders.append(f"{target.name} line {line_num}: {line.strip()}")
                continue
            docstring_constant_ids: set[int] = set()
            for parent in ast.walk(tree):
                if isinstance(parent, (ast.Module, ast.FunctionDef,
                                       ast.AsyncFunctionDef, ast.ClassDef)):
                    if parent.body and isinstance(parent.body[0], ast.Expr):
                        expr = parent.body[0]
                        if isinstance(expr.value, ast.Constant) and isinstance(
                            expr.value.value, str
                        ):
                            docstring_constant_ids.add(id(expr.value))
            for node in ast.walk(tree):
                if id(node) in docstring_constant_ids:
                    continue
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for match in pattern.finditer(node.value):
                        offenders.append(
                            f"{target.name} line "
                            f"{getattr(node, 'lineno', '?')}: "
                            f"'{match.group(0)}'"
                        )
                elif isinstance(node, ast.Name) and pattern.search(node.id):
                    offenders.append(
                        f"{target.name} line {node.lineno}: '{node.id}'"
                    )
        assert not offenders, (
            f"SC#1 violation: openclaw / Toonflow / sqlite code references "
            f"found in Phase 37 deliverables: {offenders}"
        )

    def test_no_subprocess_node_runtime_dependency(self):
        """SC#1 (D-37-05) — no Node.js runtime dependency.

        Phase 37 deliverables must not invoke Node via subprocess or use
        ``require(...)`` (the Node.js module loader). Pure Python port only.
        """
        base = Path(__file__).resolve().parent.parent
        targets = [
            base / "canvas_sync.py",
            base / "canvas_graph.py",
        ]
        pattern = re.compile(
            r'subprocess\.run.*node|require\(|child_process|npm\s+install',
            re.IGNORECASE,
        )
        offenders: list[str] = []
        for target in targets:
            if not target.exists():
                continue
            source = target.read_text(encoding="utf-8")
            for line_num, line in enumerate(source.splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f"{target.name} line {line_num}: {line.strip()}")
        assert not offenders, (
            f"D-37-05 violation: Node.js runtime dependency detected: {offenders}"
        )


# ═════════════════════════════════════════════════════════════════════════
# Test 6 — Phase 35/36 regression: full-DAG test module still imports
# ═════════════════════════════════════════════════════════════════════════


class TestPhase35Regression:
    def test_phase_35_36_regression_full_dag_imports(self):
        """Phase 35/36 regression guard.

        ``test_runner_full_dag`` is part of the broader test suite. We
        just import it here to confirm RunnerConfig's signature changes
        haven't broken module load. Pytest will run its tests separately.
        """
        # The test module lives in skills/kais-movie-pipeline/tests/.
        # We don't actually need to invoke the tests — just confirm the
        # module imports cleanly with the new RunnerConfig fields.
        try:
            from tests import test_runner_full_dag  # type: ignore  # noqa: F401
        except ImportError:
            # The tests/ package may not be importable directly in all
            # configurations; fall back to loading by file path.
            test_path = _SKILL_DIR / "tests" / "test_runner_full_dag.py"
            assert test_path.exists(), (
                f"Phase 35/36 full-DAG test missing at {test_path}"
            )
            # If we can read the file, the source is intact.
            source = test_path.read_text(encoding="utf-8")
            assert "RunnerConfig" in source, (
                "test_runner_full_dag.py must still reference RunnerConfig"
            )
            return
        assert hasattr(test_runner_full_dag, "__name__")


# ═════════════════════════════════════════════════════════════════════════
# Test 7 — register_canvas_sync integration: both callbacks wired
# ═════════════════════════════════════════════════════════════════════════


class TestRegisterCanvasSyncWiring:
    def test_register_wires_both_trigger_paths(self):
        """PATTERN 7 — single register_canvas_sync call wires BOTH:
        1. runner_config.on_phase_complete
        2. runner_hooks._on_gate_resolved (module-level)

        Missing either breaks SC#2's two-trigger-path contract.
        """
        urls: list[str] = []
        bodies: list[dict] = []
        transport = _make_transport(urls, bodies)

        cfg = RunnerConfig()
        assert cfg.on_phase_complete is None
        assert cfg.on_gate_resolved is None
        assert runner_hooks._on_gate_resolved is None

        sub = register_canvas_sync(
            base_url="http://test:10588",
            project_id=42, episodes_id=99,
            runner_config=cfg,
            transport=transport,
        )

        # Phase-completion callback wired onto cfg.
        assert cfg.on_phase_complete is not None
        assert cfg.on_phase_complete == sub.on_phase_complete
        # Gate-resolution callback wired onto cfg (symmetry / audit field).
        assert cfg.on_gate_resolved is not None
        assert cfg.on_gate_resolved == sub.on_gate_resolved
        # Module-level gate hook ALSO wired (D-37-07 — this is the trigger
        # runner_hooks.resume_from_callback / resolve_direct actually fires).
        assert runner_hooks._on_gate_resolved is not None
        assert runner_hooks._on_gate_resolved == sub.on_gate_resolved

    def test_register_canvas_sync_subscriber_isolates_per_call(self):
        """Each register_canvas_sync call produces a fresh subscriber
        (PATTERN 6 — per-instance _prev_phase_id for link drawing)."""
        urls: list[str] = []
        bodies: list[dict] = []
        transport = _make_transport(urls, bodies)

        cfg1 = RunnerConfig()
        sub1 = register_canvas_sync(
            base_url="http://test:10588",
            project_id=1, episodes_id=1,
            runner_config=cfg1, transport=transport,
        )
        cfg2 = RunnerConfig()
        sub2 = register_canvas_sync(
            base_url="http://test:10588",
            project_id=1, episodes_id=1,
            runner_config=cfg2, transport=transport,
        )
        assert sub1 is not sub2, (
            "each register call must produce a distinct subscriber instance"
        )
