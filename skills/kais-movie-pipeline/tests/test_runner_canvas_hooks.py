"""test_runner_canvas_hooks.py — Phase 37-01 event hook tests.

Verifies the Phase 37 callback plumbing added to ``runner.py`` and
``runner_hooks.py``:

* ``RunnerConfig.on_phase_complete`` / ``on_gate_resolved`` default None
  (D-37-06 — Phase 35/36 regression preserved).
* ``run_episode`` invokes ``on_phase_complete`` AFTER ``store.save_checkpoint``,
  guarded so a buggy subscriber never crashes the episode (D-37-04).
* ``runner_hooks.set_gate_resolved_hook`` + ``_on_gate_resolved`` module-level
  hook fires in ``resume_from_callback`` AFTER the ``review-outcomes`` slot
  is written (D-37-07), also guarded.

All tests mock store / delegate / bus (same pattern as Phase 35
``test_runner.py``) — no real subagents, no real HTTP, no real filesystem
outside ``tmp_path``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirrors test_runner.py).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline import runner as runner_mod  # noqa: E402
from pipeline.runner import RunnerConfig, run_episode  # noqa: E402
from pipeline import phases as phases_mod  # noqa: E402

# Import runner_hooks from the plugins tree (already on sys.path via conftest
# in the hermes-agent root, but be explicit so this file is self-contained).
from plugins.review_gates import runner_hooks  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures (mirror test_runner.py's clean_registry + stub phase factory)
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_registry():
    """Save/restore PHASE_REGISTRY around each test (see test_runner.py)."""
    saved_runner_list = list(runner_mod.PHASE_REGISTRY)
    saved_phases_list = list(phases_mod.PHASE_REGISTRY)
    shared: list = []
    phases_mod.PHASE_REGISTRY = shared
    runner_mod.PHASE_REGISTRY = shared
    yield shared
    phases_mod.PHASE_REGISTRY = list(saved_phases_list)
    runner_mod.PHASE_REGISTRY = list(saved_runner_list)


@pytest.fixture(autouse=True)
def reset_gate_hook():
    """Clear the module-level ``_on_gate_resolved`` hook before AND after
    each test so state never leaks between tests (the hook is module-global
    by design per D-37-07)."""
    runner_hooks.set_gate_resolved_hook(None)
    yield
    runner_hooks.set_gate_resolved_hook(None)


def _make_stub_phase(phase_id: str):
    """Return a stub phase module with a ``run`` function recording its call."""
    calls: dict = {"count": 0}

    def run(episode_id, asset_bus_read, asset_bus_write, delegate_task,
            trigger_gate=None):
        calls["count"] += 1
        return {"phase": phase_id, "ok": True}

    class _StubModule:
        __name__ = f"stub_{phase_id}"

    _StubModule.run = staticmethod(run)  # type: ignore[attr-defined]
    _StubModule.calls = calls  # type: ignore[attr-defined]
    return _StubModule


class _SpyStore:
    """Records ``save_checkpoint`` calls in order (for call-order assertions)."""

    def __init__(self):
        self.saved: list[tuple[str, str]] = []
        self.events: list[str] = []  # multiplexed event log for ordering checks

    def load_latest_checkpoint(self, episode_id):
        return None

    def save_checkpoint(self, episode_id, phase, payload):
        self.saved.append((episode_id, phase))
        self.events.append(f"checkpoint:{phase}")


class _StubBus:
    def __init__(self):
        self.writes: list[tuple[str, dict]] = []

    def read(self, slot):
        return None

    def write(self, slot, entry, envelope=True):
        self.writes.append((slot, entry))


# ═══════════════════════════════════════════════════════════════════
# Test 1: RunnerConfig defaults — both hooks None (D-37-06 regression)
# ═══════════════════════════════════════════════════════════════════
class TestRunnerConfigHookDefaults:
    def test_on_phase_complete_defaults_none(self):
        cfg = RunnerConfig()
        assert cfg.on_phase_complete is None, (
            "D-37-06: on_phase_complete MUST default None so Phase 35/36 "
            "tests that construct RunnerConfig() observe zero behavior change"
        )

    def test_on_gate_resolved_defaults_none(self):
        cfg = RunnerConfig()
        assert cfg.on_gate_resolved is None

    def test_hooks_settable(self):
        def cb_phase(ep, ph, res): pass
        def cb_gate(ep, g, d, p): pass
        cfg = RunnerConfig(on_phase_complete=cb_phase, on_gate_resolved=cb_gate)
        assert cfg.on_phase_complete is cb_phase
        assert cfg.on_gate_resolved is cb_gate


# ═══════════════════════════════════════════════════════════════════
# Test 2: callback invoked AFTER checkpoint, twice for 2 phases
# ═══════════════════════════════════════════════════════════════════
class TestOnPhaseCompleteInvocation:
    def test_on_phase_complete_invoked_after_checkpoint(
        self, tmp_path, clean_registry,
    ):
        """D-37-01 / CF-37-02: hook fires after save_checkpoint with the
        right (episode_id, phase_id, result) tuple, twice for a 2-phase
        episode. Uses the shared event log to assert checkpoint is written
        BEFORE the callback."""
        p1 = _make_stub_phase("p01_a")
        p2 = _make_stub_phase("p02_b")
        clean_registry.extend([
            {"id": "p01_a", "module": p1, "depends_on": []},
            {"id": "p02_b", "module": p2, "depends_on": ["p01_a"]},
        ])

        store = _SpyStore()
        hook_calls: list[tuple[str, str, dict]] = []

        def hook(episode_id, phase_id, result):
            hook_calls.append((episode_id, phase_id, result))
            # Record into the SAME event log as the store so we can assert
            # ordering: checkpoint MUST precede hook for the same phase.
            store.events.append(f"hook:{phase_id}")

        cfg = RunnerConfig(
            workdir=str(tmp_path),
            on_phase_complete=hook,
        )
        result = run_episode(
            "ep-2phase-hook", cfg,
            inject={
                "store": store,
                "bus": _StubBus(),
                "delegate_task": lambda *a, **k: {"summary": "ok"},
                "trigger_gate": lambda g, e: {"ok": True},
            },
        )

        # Hook fired twice with right tuples
        assert len(hook_calls) == 2
        assert hook_calls[0][0] == "ep-2phase-hook"
        assert hook_calls[0][1] == "p01_a"
        assert hook_calls[1][1] == "p02_b"
        # Result payload is forwarded verbatim
        assert hook_calls[0][2] == {"phase": "p01_a", "ok": True}

        # Event-order check: for EACH phase, checkpoint precedes hook
        assert store.events == [
            "checkpoint:p01_a", "hook:p01_a",
            "checkpoint:p02_b", "hook:p02_b",
        ], (
            "D-37-04: checkpoint MUST precede on_phase_complete so a "
            "subscriber crash still leaves episode progress saved"
        )

        # Episode completed normally
        assert set(result["phases"].keys()) == {"p01_a", "p02_b"}


# ═══════════════════════════════════════════════════════════════════
# Test 3: RunnerConfig() with no callbacks runs cleanly (regression)
# ═══════════════════════════════════════════════════════════════════
class TestOnPhaseCompleteNoneIsNoop:
    def test_default_config_runs_cleanly(self, tmp_path, clean_registry):
        """D-37-06 regression: RunnerConfig() with no hooks runs a 2-phase
        episode without error. Phase 35/36 tests rely on this."""
        p1 = _make_stub_phase("p01_x")
        p2 = _make_stub_phase("p02_y")
        clean_registry.extend([
            {"id": "p01_x", "module": p1, "depends_on": []},
            {"id": "p02_y", "module": p2, "depends_on": ["p01_x"]},
        ])

        cfg = RunnerConfig(workdir=str(tmp_path))
        result = run_episode(
            "ep-noop", cfg,
            inject={
                "store": _SpyStore(),
                "bus": _StubBus(),
                "delegate_task": lambda *a, **k: {"summary": "ok"},
                "trigger_gate": lambda g, e: {"ok": True},
            },
        )
        assert p1.calls["count"] == 1
        assert p2.calls["count"] == 1
        assert set(result["phases"].keys()) == {"p01_x", "p02_y"}


# ═══════════════════════════════════════════════════════════════════
# Test 4: subscriber exception is swallowed, episode completes (D-37-04)
# ═══════════════════════════════════════════════════════════════════
class TestOnPhaseCompleteExceptionSwallowed:
    def test_callback_raise_does_not_crash_episode(
        self, tmp_path, clean_registry, caplog,
    ):
        p1 = _make_stub_phase("p01_boom")
        p2 = _make_stub_phase("p02_ok")
        clean_registry.extend([
            {"id": "p01_boom", "module": p1, "depends_on": []},
            {"id": "p02_ok", "module": p2, "depends_on": ["p01_boom"]},
        ])

        def bad_hook(episode_id, phase_id, result):
            raise RuntimeError("subscriber crash (phase=%s)" % phase_id)

        cfg = RunnerConfig(workdir=str(tmp_path), on_phase_complete=bad_hook)
        with caplog.at_level("WARNING"):
            result = run_episode(
                "ep-boom", cfg,
                inject={
                    "store": _SpyStore(),
                    "bus": _StubBus(),
                    "delegate_task": lambda *a, **k: {"summary": "ok"},
                    "trigger_gate": lambda g, e: {"ok": True},
                },
            )

        # Episode completes despite the crashing subscriber
        assert p1.calls["count"] == 1
        assert p2.calls["count"] == 1, (
            "Phase 2 must still execute — a crashing subscriber cannot abort "
            "the episode (D-37-04)"
        )
        # Return payload is intact
        assert set(result["phases"].keys()) == {"p01_boom", "p02_ok"}
        # Warning logged (defensive boundary contract)
        assert any("on_phase_complete callback raised" in rec.message
                   for rec in caplog.records), (
            "Subscriber exception MUST be logged at WARNING so operators "
            "can see the canvas sync degraded"
        )


# ═══════════════════════════════════════════════════════════════════
# Test 5: set_gate_resolved_hook setter
# ═══════════════════════════════════════════════════════════════════
class TestSetGateResolvedHookSetter:
    def test_set_and_clear(self):
        assert runner_hooks._on_gate_resolved is None

        def fn(ep, g, d, p): pass
        runner_hooks.set_gate_resolved_hook(fn)
        assert runner_hooks._on_gate_resolved is fn

        runner_hooks.set_gate_resolved_hook(None)
        assert runner_hooks._on_gate_resolved is None


# ═══════════════════════════════════════════════════════════════════
# Test 6 & 7: resume_from_callback invokes hook AFTER bus.write
# ═══════════════════════════════════════════════════════════════════
def _seed_pending_gate(gate_id="test-gate", episode_id="ep-1",
                       decision="approve"):
    """Seed ``_PENDING_GATES`` with a real Gate so resume_from_callback can
    resolve it. Uses the gate framework directly to avoid mocking internals."""
    from plugins.review_gates.gate import Gate, GateConfig, GateMode, GateStatus

    config = GateConfig(
        gate_id=gate_id,
        phase="p01_test",
        asset_bus_slots_to_lock=("topic-kernel",),
        reviewer_role="creative_source",
        callback_url=None,
        default_mode=GateMode.WEBHOOK,
        max_retries=3,
    )
    gate = Gate(config=config, episode_id=episode_id, mode=GateMode.WEBHOOK)
    # Mark as submitted so resolve() accepts the decision transition.
    gate.status = GateStatus.PENDING
    gate.attempt = 1
    gate.review_id = "rev-1"
    gate.submitted_at = "2026-06-26T00:00:00Z"
    runner_hooks._PENDING_GATES[gate_id] = gate
    return gate


class TestResumeFromCallbackInvokesHook:
    def setup_method(self):
        runner_hooks._PENDING_GATES.clear()

    def teardown_method(self):
        runner_hooks._PENDING_GATES.clear()

    def test_hook_fires_after_review_outcomes_write(
        self, monkeypatch, tmp_path,
    ):
        """D-37-07: hook fires after the ``review-outcomes`` slot write so
        subscribers observe the persisted outcome. Uses an event log shared
        between the bus and the hook to assert ordering."""
        gate = _seed_pending_gate(gate_id="g-order", episode_id="ep-order")

        # Bus records writes into the shared event log
        event_log: list[str] = []

        class _OrderBus:
            def read(self, slot):
                return None

            def write(self, slot, entry, envelope=True):
                event_log.append(f"bus_write:{slot}")

        monkeypatch.setattr(runner_hooks, "_asset_bus", lambda wd=None: _OrderBus())
        monkeypatch.setattr(runner_hooks, "_state_store",
                            lambda wd=None: type("S", (), {
                                "load": lambda s: type("St", (), {
                                    "episode": "ep-order",
                                    "phases": {},
                                    "current_phase_id": None,
                                })(),
                                "save": lambda s, st: None,
                            })())
        monkeypatch.setattr(
            runner_hooks, "_review_client",
            lambda: type("C", (), {
                "verify_callback": lambda self, b, s, t: True,
            })(),
        )

        hook_calls: list[tuple[str, str, str, dict]] = []

        def hook(episode_id, gate_id, decision, payload):
            hook_calls.append((episode_id, gate_id, decision, payload))
            event_log.append(f"hook:{gate_id}:{decision}")

        runner_hooks.set_gate_resolved_hook(hook)

        body = json.dumps({
            "gate_id": "g-order",
            "decision": "approve",
            "suggested_action": None,
        })
        outcome = runner_hooks.resume_from_callback(body, "sig", 1700000000)

        # Hook fired once with right args
        assert len(hook_calls) == 1
        assert hook_calls[0][0] == "ep-order"
        assert hook_calls[0][1] == "g-order"
        assert hook_calls[0][2] == "approve"
        # Outcome payload forwarded
        assert hook_calls[0][3]["decision"] == "approve"

        # Event order: bus write precedes hook
        bus_idx = event_log.index("bus_write:review-outcomes")
        hook_idx = event_log.index("hook:g-order:approve")
        assert bus_idx < hook_idx, (
            "D-37-07: review-outcomes write MUST precede on_gate_resolved so "
            "subscribers see the formal outcome already persisted"
        )

        # Return payload intact
        assert outcome["decision"] == "approve"

    def test_hook_exception_swallowed(
        self, monkeypatch, tmp_path, caplog,
    ):
        """D-37-04: hook raising does not crash resume; the normal outcome
        payload is still returned."""
        _seed_pending_gate(gate_id="g-boom", episode_id="ep-boom")

        monkeypatch.setattr(runner_hooks, "_asset_bus", lambda wd=None: type(
            "B", (), {
                "read": lambda s, slot: None,
                "write": lambda s, *a, **k: None,
            })())
        monkeypatch.setattr(runner_hooks, "_state_store",
                            lambda wd=None: type("S", (), {
                                "load": lambda s: type("St", (), {
                                    "episode": "ep-boom",
                                    "phases": {},
                                    "current_phase_id": None,
                                })(),
                                "save": lambda s, st: None,
                            })())
        monkeypatch.setattr(
            runner_hooks, "_review_client",
            lambda: type("C", (), {
                "verify_callback": lambda self, b, s, t: True,
            })(),
        )

        def bad_hook(episode_id, gate_id, decision, payload):
            raise RuntimeError("subscriber crashed")

        runner_hooks.set_gate_resolved_hook(bad_hook)

        body = json.dumps({
            "gate_id": "g-boom",
            "decision": "approve",
            "suggested_action": None,
        })
        with caplog.at_level("WARNING"):
            outcome = runner_hooks.resume_from_callback(body, "sig", 1700000000)

        # Outcome returned normally despite crashing hook
        assert outcome["decision"] == "approve"
        assert any("on_gate_resolved hook raised" in rec.message
                   for rec in caplog.records)


# ═══════════════════════════════════════════════════════════════════
# Test 8: Phase 35/36 regression — full DAG test file still imports & runs
# ═══════════════════════════════════════════════════════════════════
class TestPhase35Regression:
    def test_full_dag_test_module_imports(self):
        """Phase 35/36 regression guard: the full-DAG test module must still
        import cleanly with the new RunnerConfig fields. (Running the full
        test file inline is redundant — pytest collects it as part of the
        suite; this test just asserts importability, which catches accidental
        breaking changes to RunnerConfig's signature.)"""
        from tests import test_runner_full_dag  # noqa: F401  — import side-effect
        # Importing the module exercises RunnerConfig references at module
        # load time; if we broke the dataclass, this raises.
        assert hasattr(test_runner_full_dag, "__name__")
