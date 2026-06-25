"""test_runner.py — Phase 35-02 Task 2 (TDD RED→GREEN).

Mocked tests for ``runner.py``. Per CONTEXT D-35-08, all tests mock:
- ``delegate_task`` (no real subagent spawns)
- ``trigger_gate`` (no real review-platform HTTP)
- ``PipelineStateStore`` (real filesystem via ``tmp_path``, isolated per test)
- ``AssetBus`` (real filesystem via ``tmp_path``)

No network, no real LLM. Tests verify ORCHESTRATION CORRECTNESS only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable. ``skills/kais-movie-pipeline``
# uses hyphens (skill discovery convention) which isn't a valid Python identifier;
# we put the directory on sys.path so its ``pipeline/`` subpackage is importable
# as just ``pipeline``. This mirrors the production sys.path setup.
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))


# Import target (GREEN phase will create this).
from pipeline import runner  # noqa: E402
from pipeline.runner import RunnerConfig, run_episode, _compute_start_index  # noqa: E402
from pipeline import phases as phases_mod  # noqa: E402


@pytest.fixture
def clean_registry():
    """Save/restore PHASE_REGISTRY around each test (it's a module-level list)."""
    saved = list(phases_mod.PHASE_REGISTRY)
    phases_mod.PHASE_REGISTRY.clear()
    yield phases_mod.PHASE_REGISTRY
    phases_mod.PHASE_REGISTRY.clear()
    phases_mod.PHASE_REGISTRY.extend(saved)


def _make_stub_phase(phase_id: str, gate_id: str | None = None):
    """Return a stub phase module-like object with a ``run`` function that
    records its invocation."""
    calls: dict = {"count": 0, "args": None}

    def run(
        episode_id,
        asset_bus_read,
        asset_bus_write,
        delegate_task,
        trigger_gate=None,
    ):
        calls["count"] += 1
        calls["args"] = {
            "episode_id": episode_id,
            "has_read": callable(asset_bus_read),
            "has_write": callable(asset_bus_write),
            "has_delegate": callable(delegate_task),
            "trigger_gate": trigger_gate,
        }
        # If a gate is configured AND trigger_gate is wired, call it.
        gate_result = None
        if gate_id and trigger_gate:
            gate_result = trigger_gate(gate_id, episode_id)
        return {"phase": phase_id, "ok": True, "gate": gate_result}

    class _StubModule:
        __name__ = f"stub_{phase_id}"

    _StubModule.run = staticmethod(run)
    _StubModule.calls = calls  # type: ignore[attr-defined]
    return _StubModule


# ═══════════════════════════════════════════════════════════════════
# Test 1: RunnerConfig default parallel_shots == 4 (D-35-06 preserved)
# ═══════════════════════════════════════════════════════════════════
class TestRunnerConfigDefaults:
    def test_parallel_shots_defaults_to_4(self):
        cfg = RunnerConfig()
        assert cfg.parallel_shots == 4, (
            "D-35-06: parallel_shots MUST default to 4 to preserve v2.0 behavior"
        )

    def test_workdir_defaults_to_dot(self):
        assert RunnerConfig().workdir == "."

    def test_enable_gates_defaults_true(self):
        assert RunnerConfig().enable_gates is True

    def test_config_overridable(self):
        cfg = RunnerConfig(parallel_shots=8, workdir="/tmp/x", enable_gates=False)
        assert cfg.parallel_shots == 8
        assert cfg.workdir == "/tmp/x"
        assert cfg.enable_gates is False


# ═══════════════════════════════════════════════════════════════════
# Test 2: empty registry returns immediately with phases={} + config echoed
# ═══════════════════════════════════════════════════════════════════
class TestEmptyRegistry:
    def test_empty_registry_returns_immediately(self, tmp_path, clean_registry):
        assert clean_registry == []
        cfg = RunnerConfig(workdir=str(tmp_path))
        result = run_episode("ep-empty", cfg)
        assert result["episode_id"] == "ep-empty"
        assert result["phases"] == {}
        assert result["parallel_shots"] == 4

    def test_empty_registry_echoes_custom_parallel_shots(self, tmp_path, clean_registry):
        cfg = RunnerConfig(workdir=str(tmp_path), parallel_shots=7)
        result = run_episode("ep-ps7", cfg)
        assert result["parallel_shots"] == 7


# ═══════════════════════════════════════════════════════════════════
# Test 3: 2-entry stub registry executes both, saves checkpoint after each
# ═══════════════════════════════════════════════════════════════════
class TestTwoPhaseExecution:
    def test_both_phases_execute_in_order(self, tmp_path, clean_registry):
        p1 = _make_stub_phase("p01_x")
        p2 = _make_stub_phase("p02_y")
        clean_registry.extend([
            {"id": "p01_x", "module": p1, "depends_on": []},
            {"id": "p02_y", "module": p2, "depends_on": ["p01_x"]},
        ])

        # Inject mocks — track save_checkpoint calls
        ckpts: list[tuple[str, str]] = []

        class SpyStore:
            def load_latest_checkpoint(self, episode_id):
                return None

            def save_checkpoint(self, episode_id, phase, payload):
                ckpts.append((episode_id, phase))

        bus_reads = []
        bus_writes = []

        class SpyBus:
            def read(self, slot):
                bus_reads.append(slot)
                return None

            def write(self, slot, entry, envelope=True):
                bus_writes.append((slot, entry))

        def mock_delegate(goal, ctx, toolsets):
            return {"summary": "ok"}

        def mock_gate(gate_id, ep):
            return {"gate_id": gate_id, "outcome": "approved"}

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=True)
        result = run_episode(
            "ep-2phase", cfg,
            inject={
                "store": SpyStore(),
                "bus": SpyBus(),
                "delegate_task": mock_delegate,
                "trigger_gate": mock_gate,
            },
        )

        # Both phases executed
        assert p1.calls["count"] == 1
        assert p2.calls["count"] == 1
        # Checkpoint saved after EACH phase (order: p01 then p02)
        assert ckpts == [("ep-2phase", "p01_x"), ("ep-2phase", "p02_y")]
        # Result phases dict has both
        assert set(result["phases"].keys()) == {"p01_x", "p02_y"}
        assert result["phases"]["p01_x"]["ok"] is True

    def test_injected_callables_reach_phase_run(self, tmp_path, clean_registry):
        """Phase module receives the injected delegate / gate / read / write."""
        p1 = _make_stub_phase("p01_check")
        clean_registry.append({"id": "p01_check", "module": p1, "depends_on": []})

        def mock_delegate(goal, ctx, toolsets):
            return {"summary": "delegated"}

        def mock_gate(gate_id, ep):
            return {"g": gate_id}

        class _StubStore:
            def load_latest_checkpoint(self, ep):
                return None

            def save_checkpoint(self, *a, **kw):
                pass

        class _StubBus:
            def read(self, slot):
                return None

            def write(self, *a, **kw):
                pass

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=True)
        run_episode(
            "ep-callables", cfg,
            inject={
                "store": _StubStore(),
                "bus": _StubBus(),
                "delegate_task": mock_delegate,
                "trigger_gate": mock_gate,
            },
        )

        args = p1.calls["args"]
        assert args["has_read"] is True
        assert args["has_write"] is True
        assert args["has_delegate"] is True
        # When enable_gates=True and trigger_gate injected, phase receives it
        assert callable(args["trigger_gate"])


# ═══════════════════════════════════════════════════════════════════
# Test 4: resume — checkpoint exists for phase 1, re-run skips phase 1
# ═══════════════════════════════════════════════════════════════════
class TestCheckpointResume:
    def test_resume_skips_completed_phase(self, tmp_path, clean_registry):
        """After phase 1 is checkpointed, second run_episode resumes at phase 2."""
        p1 = _make_stub_phase("p01_skip")
        p2 = _make_stub_phase("p02_run")
        clean_registry.extend([
            {"id": "p01_skip", "module": p1, "depends_on": []},
            {"id": "p02_run", "module": p2, "depends_on": ["p01_skip"]},
        ])

        class StubStore:
            """Returns a checkpoint for p01_skip → runner should start at idx 1."""

            def __init__(self, episode_id, completed_phase):
                self.episode_id = episode_id
                self.completed_phase = completed_phase
                self.saved: list[tuple[str, str]] = []

            def load_latest_checkpoint(self, episode_id):
                if episode_id != self.episode_id:
                    return None
                if self.completed_phase is None:
                    return None
                # Match the shape store.load_latest_checkpoint actually
                # returns (a phase-state dict). Runner reads the phase id
                # via the envelope returned by store. Use the canonical
                # PipelineStateStore payload shape: {"status":..., "result":...}.
                # The runner derives the phase_id from the store's
                # ``current_phase_id`` — but to keep this test independent
                # of store internals, the runner's resume contract is:
                # ``load_latest_checkpoint`` returns a dict carrying the
                # completed phase id (key: "phase").
                return {"phase": self.completed_phase, "status": "completed"}

            def save_checkpoint(self, episode_id, phase, payload):
                self.saved.append((episode_id, phase))
                self.completed_phase = phase

        store = StubStore("ep-resume", completed_phase="p01_skip")

        cfg = RunnerConfig(workdir=str(tmp_path))
        result = run_episode(
            "ep-resume", cfg,
            inject={
                "store": store,
                "bus": type("B", (), {"read": lambda s, x: None, "write": lambda s, *a, **k: None})(),
                "delegate_task": lambda *a, **k: {"summary": "x"},
                "trigger_gate": lambda g, e: {"g": g},
            },
        )

        # p01_skip should NOT have run (skipped via checkpoint)
        assert p1.calls["count"] == 0, "phase 1 should be skipped on resume"
        # p02_run SHOULD have run
        assert p2.calls["count"] == 1
        # Result includes resumed_from metadata
        assert result.get("resumed_from") == 1, (
            "result must report resumed_from index so callers can audit"
        )

    def test_compute_start_index_no_checkpoint(self):
        """_compute_start_index(None) returns 0."""
        assert _compute_start_index(None) == 0

    def test_compute_start_index_unknown_phase(self, tmp_path, clean_registry):
        """Checkpoint phase id not in registry → start fresh (idx 0)."""
        clean_registry.append({"id": "p01_real", "module": _make_stub_phase("p01_real"), "depends_on": []})
        # checkpoint references a phase not in the registry
        assert _compute_start_index({"phase": "p99_nonexistent"}) == 0

    def test_compute_start_index_finds_phase(self, tmp_path, clean_registry):
        clean_registry.extend([
            {"id": "p01_a", "module": _make_stub_phase("p01_a"), "depends_on": []},
            {"id": "p02_b", "module": _make_stub_phase("p02_b"), "depends_on": ["p01_a"]},
            {"id": "p03_c", "module": _make_stub_phase("p03_c"), "depends_on": ["p02_b"]},
        ])
        # Checkpoint at p02_b → resume at idx 2 (p03_c)
        assert _compute_start_index({"phase": "p02_b"}) == 2
        # Checkpoint at p01_a → resume at idx 1 (p02_b)
        assert _compute_start_index({"phase": "p01_a"}) == 1


# ═══════════════════════════════════════════════════════════════════
# Test 5: enable_gates=False prevents trigger_gate from being called
# ═══════════════════════════════════════════════════════════════════
class TestGateConfigKnob:
    def test_gates_disabled_passes_none_to_phase(self, tmp_path, clean_registry):
        p1 = _make_stub_phase("p01_nogate", gate_id="selection-topic-hook")
        clean_registry.append({"id": "p01_nogate", "module": p1, "depends_on": []})

        gate_calls: list[tuple] = []

        def mock_gate(gate_id, ep):
            gate_calls.append((gate_id, ep))
            return {"approved": True}

        class _StubStore:
            def load_latest_checkpoint(self, ep):
                return None

            def save_checkpoint(self, *a, **kw):
                pass

        class _StubBus:
            def read(self, slot):
                return None

            def write(self, *a, **kw):
                pass

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        run_episode(
            "ep-nogate", cfg,
            inject={
                "store": _StubStore(),
                "bus": _StubBus(),
                "delegate_task": lambda *a, **k: {"summary": "x"},
                "trigger_gate": mock_gate,  # injected but should NOT be called
            },
        )

        # Phase module receives None for trigger_gate → no gate invocation
        assert p1.calls["args"]["trigger_gate"] is None, (
            "enable_gates=False MUST pass None to phase module, "
            "so phase skips gate logic"
        )
        assert gate_calls == [], (
            "with enable_gates=False, mock_gate must never be invoked"
        )

    def test_gates_enabled_passes_callable_to_phase(self, tmp_path, clean_registry):
        p1 = _make_stub_phase("p01_gate", gate_id="selection-topic-hook")
        clean_registry.append({"id": "p01_gate", "module": p1, "depends_on": []})

        def mock_gate(gate_id, ep):
            return {"approved": True}

        class _StubStore:
            def load_latest_checkpoint(self, ep):
                return None

            def save_checkpoint(self, *a, **kw):
                pass

        class _StubBus:
            def read(self, slot):
                return None

            def write(self, *a, **kw):
                pass

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=True)
        run_episode(
            "ep-gate", cfg,
            inject={
                "store": _StubStore(),
                "bus": _StubBus(),
                "delegate_task": lambda *a, **k: {"summary": "x"},
                "trigger_gate": mock_gate,
            },
        )

        assert callable(p1.calls["args"]["trigger_gate"])
        # Phase module should have called the gate (gate_id set + trigger_gate wired)
        gate_result = p1.calls["args"]["trigger_gate"]("selection-topic-hook", "ep-gate")
        assert gate_result == {"approved": True}


# ═══════════════════════════════════════════════════════════════════
# Phase 35-05 extensions — exercises the shared conftest.py fixtures.
# These complement the original 14 tests by driving run_episode through
# the production-shaped ``inject`` path with the shared mock factories.
# ═══════════════════════════════════════════════════════════════════


class TestRunnerWithConftestFixtures:
    """Smoke-test the shared fixtures (mock_delegate_factory, tmp_asset_bus,
    fake_registry, make_fake_phase) to prove they wire into run_episode."""

    def test_fake_registry_drives_run_episode(
        self, tmp_path, fake_registry, make_fake_phase, mock_delegate_factory,
    ):
        """Two fake phases appended to fake_registry both execute."""
        p1 = make_fake_phase("p01_alpha", {"k": "v1"})
        p2 = make_fake_phase("p02_beta", {"k": "v2"})
        fake_registry.extend([
            {"id": "p01_alpha", "module": p1, "depends_on": []},
            {"id": "p02_beta", "module": p2, "depends_on": ["p01_alpha"]},
        ])

        class _StubStore:
            def __init__(self):
                self.saved = []

            def load_latest_checkpoint(self, ep):
                return None

            def save_checkpoint(self, ep, phase, payload):
                self.saved.append(phase)

        class _StubBus:
            def read(self, slot):
                return None

            def write(self, *a, **kw):
                pass

        store = _StubStore()
        cfg = RunnerConfig(workdir=str(tmp_path))
        result = run_episode(
            "ep-fake-registry", cfg,
            inject={
                "store": store,
                "bus": _StubBus(),
                "delegate_task": mock_delegate_factory({"x": 1}),
                "trigger_gate": lambda g, e: {"ok": True},
            },
        )

        assert p1.calls["count"] == 1
        assert p2.calls["count"] == 1
        assert store.saved == ["p01_alpha", "p02_beta"]
        assert set(result["phases"].keys()) == {"p01_alpha", "p02_beta"}
        assert result["resumed_from"] == 0

    def test_tmp_asset_bus_round_trips(
        self, tmp_asset_bus, mock_delegate_factory,
    ):
        """tmp_asset_bus fixture gives a real AssetBus that round-trips slots."""
        bus, workdir = tmp_asset_bus
        bus.write("topic-kernel", {"title": "test-kernel"}, envelope=True)
        data = bus.read("topic-kernel")
        # AssetBus.read returns the payload directly (envelope unwrapped on read)
        assert data["title"] == "test-kernel"

    def test_mock_delegate_factory_emits_fenced_json(
        self, mock_delegate_factory,
    ):
        """mock_delegate_factory's return value embeds output as fenced JSON."""
        delegate = mock_delegate_factory({"topic_kernel": {"x": 1}})
        result = delegate("goal", "ctx", ["skills"])
        assert "```json" in result["summary"]
        assert "\"topic_kernel\"" in result["summary"]
        # Captures the invocation
        assert delegate.last_call["goal"] == "goal"
        assert delegate.last_call["toolsets"] == ["skills"]
