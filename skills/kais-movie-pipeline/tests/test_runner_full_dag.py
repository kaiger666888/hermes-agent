"""test_runner_full_dag.py — Phase 36-05 Task 3: full 14-phase DAG integration.

End-to-end orchestration tests against the *real* PHASE_REGISTRY (14
phase modules p01..p13 + p10b). Per D-35-08 / D-36-05 these are
MOCKED-DELEGATE tests: ``delegate_task`` is replaced with a canned-JSON
spy so no real subagent spawns and no real HTTP/LLM is exercised. The
phase modules' *orchestration correctness* (slot reads, goal construction,
slot writes, gate triggering) is exercised for real.

Phase 40 (v6.0) updates: registry now has 14 entries (p10b_rapid_preview
inserted between p10 and p11). p10b is a stub whose run() raises
NotImplementedError; the full-DAG tests use a canned-delegate spy that
does NOT consult p10b's EXPERT (which is None), so the stub's run() is
never invoked — the spy returns an empty payload for unknown phases. See
``_make_full_dag_delegate_spy`` for the matching heuristic.

Test coverage:
1. Full DAG runs p01 → p13 sequentially with mocked delegate; all 14 phase
   results returned.
2. Checkpoint resume mid-pipeline: simulate checkpoint at p07 → restart
   runner → only p08..p13 results in the second run (7 phases including
   p10b), resumed_from=7.
3. enable_gates=False suppresses gate triggering across the whole DAG.
4. RunnerConfig.parallel_shots reaches p11 (D-36-08 contract — only p11
   reads the kwarg; runner forwards it via keyword-only injection).

This test file does NOT clear PHASE_REGISTRY — it asserts on the real
Phase 36-05 production registry (unlike test_runner.py's fake_registry
fixture which is for runner-mechanics unit tests).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_p01_unit).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline import phases as phases_mod  # noqa: E402
from pipeline import runner as runner_mod  # noqa: E402
from pipeline.phases import PHASE_REGISTRY  # noqa: E402
from pipeline.runner import RunnerConfig, run_episode  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _canned_summary(payload: dict) -> str:
    """Build a delegate_task summary containing a fenced JSON block."""
    return f"Expert output:\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _make_full_dag_delegate_spy(phase_to_payload: dict[str, dict] | None = None):
    """Return a delegate_task mock that returns canned JSON per phase.

    The mock inspects the ``goal`` string for the current phase id and
    returns the matching canned payload. When no phase id is matched, it
    returns a generic empty-object payload (phases that read empty slots
    still produce valid JSON parses).

    Records every invocation on ``.calls`` (list of (goal_snippet, toolsets)).
    """
    default_payloads: dict[str, dict] = phase_to_payload or _default_per_phase_payloads()
    calls: list[dict] = []

    def _delegate(goal: str, context: str, toolsets: list[str]) -> dict:
        calls.append({
            "goal": goal,
            "context": context,
            "toolsets": list(toolsets),
        })
        # Match the current phase by scanning the goal for the phase id.
        for phase_id, payload in default_payloads.items():
            # Goal always embeds episode_id; phase_id is detectable via
            # the skill_view names + step numbers. Use a simpler heuristic:
            # match by the phase's primary expert name (EXPERT constant).
            module = next(
                (e["module"] for e in PHASE_REGISTRY if e["id"] == phase_id),
                None,
            )
            if module is None:
                continue
            expert = getattr(module, "EXPERT", "")
            if expert and expert in goal:
                return {"summary": _canned_summary(payload)}
        # Fallback: empty dict payload (downstream phases tolerate empty).
        return {"summary": _canned_summary({})}

    _delegate.calls = calls  # type: ignore[attr-defined]
    return _delegate


def _default_per_phase_payloads() -> dict[str, dict]:
    """Per-phase canned payloads whose output slots satisfy downstream reads.

    Each payload matches the JSON shape the phase module parses from the
    delegate summary (per Wave 1 SUMMARYs).
    """
    return {
        "p01_hook_topic": {
            "topic_kernel": {"genre": "test", "hook": "h"},
            "hook_design": {"candidates": []},
        },
        "p02_outline": {
            "story_framework": {"beats": []},
        },
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


class _StubStore:
    """Checkpoint store stub — scriptable load_latest_checkpoint + recording
    save_checkpoint. Matches the production PipelineStateStore contract the
    runner depends on."""

    def __init__(self, initial_checkpoint: dict | None = None):
        self._checkpoint = initial_checkpoint
        self.saved: list[tuple[str, str]] = []

    def load_latest_checkpoint(self, episode_id: str):
        return self._checkpoint

    def save_checkpoint(self, episode_id: str, phase: str, payload: dict):
        self.saved.append((episode_id, phase))
        # Advance the cursor so subsequent loads see the latest phase.
        self._checkpoint = {"phase": phase, "status": "completed"}


class _StubBus:
    """In-memory asset bus — supports the read/write API surface runner uses."""

    def __init__(self):
        self.slots: dict[str, Any] = {}

    def read(self, slot: str):
        return self.slots.get(slot)

    def write(self, slot: str, entry, envelope: bool = True, **kwargs):
        self.slots[slot] = entry


# ---------------------------------------------------------------------------
# Phase 40 (v6.0) — p10b stub proxy for full-DAG tests
# ---------------------------------------------------------------------------
# The real p10b_rapid_preview.run() raises NotImplementedError (impl arrives
# in plan 40-03). Full-DAG tests iterate the real PHASE_REGISTRY, so the
# runner WILL call p10b.run() — which would crash every full-DAG test. The
# fix: swap p10b's module in BOTH phases_mod.PHASE_REGISTRY AND
# runner_mod.PHASE_REGISTRY with a no-op proxy that returns a canned result.
# Mirrors the existing _P11Proxy swap pattern in
# test_full_dag_parallel_shots_config_reaches_p11.

class _P10bStubProxy:
    """Module proxy: replaces p10b_rapid_preview.run() with a canned result.

    Returns the same shape the real p10b will return (per CONTEXT.md
    "AssetBus Integration"): ``{"phase": "p10b_rapid_preview", "outputs": {},
    "gate": None}``. The stub writes nothing to the asset bus here — the
    canned-delegate spy's empty payload is sufficient for downstream phases
    (p11 reads voice-clips/voice-timeline which p10 wrote; p10b's outputs
    are rapid-preview-clips/episode-meta which p11 doesn't read).
    """
    __name__ = "p10b_rapid_preview_stub_proxy"

    PHASE_ID = "p10b_rapid_preview"
    EXPERT = None  # mirrors the real stub — pure orchestration
    INPUT_SLOTS = ["voice-clips", "voice-timeline", "e-konte-sheets"]
    OUTPUT_SLOTS = ["rapid-preview-clips", "episode-meta"]
    GATE_ID = None

    @staticmethod
    def run(*args, **kwargs):
        return {
            "phase": "p10b_rapid_preview",
            "outputs": {},
            "gate": None,
        }


def _install_p10b_stub_proxy():
    """Swap p10b in BOTH registries with _P10bStubProxy. Returns (swap_phases,
    swap_runner) — pass to _restore_p10b_stub() to restore."""
    def _swap_in(registry_list: list) -> tuple[int, dict] | None:
        for i, e in enumerate(registry_list):
            if e.get("id") == "p10b_rapid_preview":
                saved = registry_list[i]
                registry_list[i] = {
                    "id": "p10b_rapid_preview",
                    "module": _P10bStubProxy,
                    "depends_on": saved.get("depends_on", ["p10_voice"]),
                }
                return i, saved
        return None

    swap_phases = _swap_in(phases_mod.PHASE_REGISTRY)
    swap_runner = _swap_in(runner_mod.PHASE_REGISTRY)
    return swap_phases, swap_runner


def _restore_p10b_stub(swap_phases, swap_runner):
    """Restore original p10b entries (raise-on-call stub) after a test."""
    if swap_phases is not None:
        idx, saved = swap_phases
        phases_mod.PHASE_REGISTRY[idx] = saved
    if swap_runner is not None:
        idx, saved = swap_runner
        runner_mod.PHASE_REGISTRY[idx] = saved


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFullDagRun:
    """All full-DAG tests need p10b's run() stubbed out — the real
    p10b_rapid_preview.run() raises NotImplementedError (impl arrives in
    plan 40-03). The autouse fixture swaps p10b in both PHASE_REGISTRY
    copies (phases_mod + runner_mod) with _P10bStubProxy for the duration
    of each test, then restores the raise-on-call stub."""

    @pytest.fixture(autouse=True)
    def _swap_p10b_with_stub_proxy(self):
        swap_phases, swap_runner = _install_p10b_stub_proxy()
        yield
        _restore_p10b_stub(swap_phases, swap_runner)

    def test_full_dag_runs_p01_through_p13(self, tmp_path):
        """Full DAG: runner iterates p01 → p13 with mocked delegate, returns
        13 phase results (one per registry entry)."""
        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus()

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        result = run_episode(
            "ep-fulldag", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        # All 14 phases ran (none skipped — no checkpoint).
        # Phase 40 (v6.0) inserts p10b_rapid_preview between p10 and p11.
        assert len(result["phases"]) == 14, (
            f"expected 14 phase results, got {len(result['phases'])}; "
            f"phases: {sorted(result['phases'].keys())}"
        )
        # Phase ids exactly match the registry ids.
        assert set(result["phases"].keys()) == {
            entry["id"] for entry in PHASE_REGISTRY
        }
        # Runner reported fresh start.
        assert result["resumed_from"] == 0
        # Each phase returned a dict carrying its phase id.
        for phase_id, phase_result in result["phases"].items():
            assert isinstance(phase_result, dict)
            assert phase_result.get("phase") == phase_id, (
                f"phase {phase_id} result missing/wrong 'phase' key: {phase_result}"
            )

    def test_checkpoint_resume_mid_pipeline(self, tmp_path):
        """Checkpoint at p07 → restart runner → resumes at p08, only p08..p13
        results returned (7 phases, includes p10b at index 10). resumed_from
        == 7 (index of p08).

        Phase 40 (v6.0) BLOCKER #3 safety: p10b inserts at registry index 10
        (between p10@9 and p11@was-10-now-11), which is AFTER p08@7. The
        resume cursor is keyed on phase ID strings (not numeric index), so
        resumed_from=7 still resolves to p08_scene_selection correctly. The
        resumed slice now includes p10b between p10 and p11, expanding the
        phase count from 6 to 7.
        """
        delegate = _make_full_dag_delegate_spy()
        # Checkpoint says "p07 just completed" → resume at idx 7 (p08).
        store = _StubStore(initial_checkpoint={"phase": "p07_scene_generation"})
        bus = _StubBus()

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        result = run_episode(
            "ep-resume", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        # Resumed at index 7 (p08_scene_selection is index 7 in 0-based).
        assert result["resumed_from"] == 7, (
            f"expected resumed_from=7 (p08 index), got {result['resumed_from']}"
        )
        # Only p08..p13 should have run (7 phases, includes p10b at index 10).
        # p10b inserts at index 10 (between p10@9 and p11@was-10-now-11) —
        # within the resumed_from=7 slice.
        assert len(result["phases"]) == 7, (
            f"expected 7 phases (p08..p13, includes p10b), "
            f"got {len(result['phases'])}; "
            f"phases: {sorted(result['phases'].keys())}"
        )
        # p01..p07 should NOT be in the second-run results.
        for early_phase in ("p01_hook_topic", "p07_scene_generation"):
            assert early_phase not in result["phases"], (
                f"{early_phase} should have been skipped on resume"
            )
        # p08..p13 should all be present, INCLUDING p10b_rapid_preview
        # (inserted between p10_voice and p11_video_render by Phase 40).
        for late_phase in (
            "p08_scene_selection",
            "p09_shot_breakdown",
            "p10_voice",
            "p10b_rapid_preview",
            "p11_video_render",
            "p12_composition",
            "p13_delivery",
        ):
            assert late_phase in result["phases"], (
                f"{late_phase} should have run after resume at p08"
            )

    def test_p10b_insertion_preserves_p08_resume_cursor(self):
        """BLOCKER #3 safety: p10b inserts at index 10 (between p10@9 and
        p11), which is AFTER p08@7. resumed_from=7 must still work, and p10b
        runs as part of the resumed slice (now 7 phases: p08..p13 inclusive).

        This test pins the index invariant directly so future registry
        edits that shift p08 or p10b indices surface immediately.
        """
        ids = [entry["id"] for entry in PHASE_REGISTRY]
        assert ids.index("p08_scene_selection") == 7, (
            f"p08_scene_selection must remain at index 7 "
            f"(resume cursor invariant); got {ids.index('p08_scene_selection')}"
        )
        assert ids.index("p10b_rapid_preview") == 10, (
            f"p10b_rapid_preview must be at index 10 (between p10@9 and "
            f"p11@11); got {ids.index('p10b_rapid_preview')}"
        )
        assert ids.index("p11_video_render") == 11, (
            f"p11_video_render must be at index 11 (was 10 pre-p10b); "
            f"got {ids.index('p11_video_render')}"
        )

    def test_full_dag_with_gates_disabled(self, tmp_path):
        """enable_gates=False → phase modules receive trigger_gate=None across
        the whole DAG; even phases with GATE_ID set must report gate=None."""
        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus()

        gate_calls: list[tuple[str, str]] = []

        def gate_spy(gate_id, episode_id):
            gate_calls.append((gate_id, episode_id))
            return {"status": "paused"}

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        result = run_episode(
            "ep-nogate", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
                # Injected on purpose — enable_gates=False must override it.
                "trigger_gate": gate_spy,
            },
        )

        # Gate spy must NEVER have been forwarded to any phase.
        assert gate_calls == [], (
            f"enable_gates=False must suppress gate calls; got {gate_calls}"
        )
        # Phases with GATE_ID set (p01..p03, p05..p07, p11, p13) must report
        # gate=None because they received trigger_gate=None.
        gating_phases = [
            e["id"] for e in PHASE_REGISTRY
            if getattr(e["module"], "GATE_ID", None) is not None
        ]
        assert len(gating_phases) > 0, "test expects at least one gating phase"
        for phase_id in gating_phases:
            phase_result = result["phases"][phase_id]
            assert phase_result.get("gate") is None, (
                f"{phase_id} gate must be None when gates disabled; "
                f"got {phase_result.get('gate')}"
            )

    def test_full_dag_with_gates_enabled_fires_for_all_gating_phases(self, tmp_path):
        """enable_gates=True → every phase with GATE_ID set triggers the gate.
        Sanity check that the runner forwards trigger_gate correctly."""
        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus()

        gate_calls: list[tuple[str, str]] = []

        def gate_spy(gate_id, episode_id):
            gate_calls.append((gate_id, episode_id))
            return {"status": "paused"}

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=True)
        run_episode(
            "ep-gateyes", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
                "trigger_gate": gate_spy,
            },
        )

        # Every gating phase must have fired exactly once.
        expected_gate_ids = [
            getattr(e["module"], "GATE_ID")
            for e in PHASE_REGISTRY
            if getattr(e["module"], "GATE_ID", None) is not None
        ]
        fired_gate_ids = [call[0] for call in gate_calls]
        assert fired_gate_ids == expected_gate_ids, (
            f"gate fire order mismatch;\n  expected: {expected_gate_ids}\n"
            f"  got:      {fired_gate_ids}"
        )

    def test_full_dag_parallel_shots_config_reaches_p11(self, tmp_path):
        """RunnerConfig.parallel_shots=7 reaches p11 (D-36-08 contract).

        p11_video_render is the ONLY phase reading parallel_shots. The runner
        must forward cfg.parallel_shots to p11 via keyword-only injection.

        We wrap the p11 entry inside PHASE_REGISTRY (and runner.PHASE_REGISTRY,
        which may reference a DIFFERENT list object if a sibling test called
        ``importlib.reload(phases_mod)``) with a proxy module whose run()
        captures the kwargs forwarded by the runner. try/finally restores the
        original entry on teardown.
        """
        original_p11 = phases_mod.p11_video_render
        captured_kwargs: dict = {}

        class _P11Proxy:
            """Module proxy: forwards run() to real p11 but spies on kwargs."""
            __name__ = "p11_video_render_proxy"

            PHASE_ID = original_p11.PHASE_ID
            EXPERT = original_p11.EXPERT
            INPUT_SLOTS = original_p11.INPUT_SLOTS
            OUTPUT_SLOTS = original_p11.OUTPUT_SLOTS
            GATE_ID = original_p11.GATE_ID

            @staticmethod
            def run(*args, parallel_shots: int = 4, **kwargs):
                captured_kwargs["parallel_shots"] = parallel_shots
                captured_kwargs["got_kwargs"] = sorted(kwargs.keys())
                captured_kwargs["got_all_kwargs"] = sorted(
                    list(kwargs.keys()) + ["parallel_shots"]
                )
                return original_p11.run(*args, parallel_shots=parallel_shots, **kwargs)

        # Swap the p11 entry IN PLACE in BOTH registries. After Phase 35-05's
        # binding fix both modules normally reference the SAME list, but a
        # sibling test (test_p03_unit::test_registry_has_three_entries) calls
        # ``importlib.reload(phases_mod)`` which RE-BINDS phases_mod's list
        # to a fresh object — leaving runner_mod holding the OLD list. To be
        # robust to that, swap in whichever list actually contains p11.
        def _swap_in(registry_list: list) -> tuple[int, dict] | None:
            for i, e in enumerate(registry_list):
                if e.get("id") == "p11_video_render":
                    saved = registry_list[i]
                    registry_list[i] = {
                        "id": "p11_video_render",
                        "module": _P11Proxy,
                        "depends_on": saved.get("depends_on", []),
                    }
                    return i, saved
            return None

        swap_phases = _swap_in(phases_mod.PHASE_REGISTRY)
        swap_runner = _swap_in(runner_mod.PHASE_REGISTRY)
        try:
            delegate = _make_full_dag_delegate_spy()
            store = _StubStore(initial_checkpoint=None)
            bus = _StubBus()

            cfg = RunnerConfig(
                workdir=str(tmp_path),
                enable_gates=False,
                parallel_shots=7,  # D-36-08 — non-default to catch wiring bugs
            )
            run_episode(
                "ep-parallel", cfg,
                inject={
                    "store": store,
                    "bus": bus,
                    "delegate_task": delegate,
                },
            )
        finally:
            if swap_phases is not None:
                idx, saved = swap_phases
                phases_mod.PHASE_REGISTRY[idx] = saved
            if swap_runner is not None:
                idx, saved = swap_runner
                runner_mod.PHASE_REGISTRY[idx] = saved

        # p11 must have received parallel_shots=7 forwarded by the runner.
        assert captured_kwargs.get("parallel_shots") == 7, (
            "RunnerConfig.parallel_shots=7 must reach p11 via keyword-only "
            f"kwarg; captured kwargs: {captured_kwargs}"
        )

    def test_full_dag_checkpoints_persisted_after_each_phase(self, tmp_path):
        """Every phase that runs must be followed by a checkpoint save."""
        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus()

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        run_episode(
            "ep-ckpt", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        # 14 phases × 1 save each == 14 saves, in registry order.
        # Phase 40 (v6.0) adds p10b_rapid_preview (now 14 phases total).
        assert len(store.saved) == 14, (
            f"expected 14 checkpoint saves, got {len(store.saved)}"
        )
        saved_phases = [phase for (_ep, phase) in store.saved]
        expected_phases = [entry["id"] for entry in PHASE_REGISTRY]
        assert saved_phases == expected_phases, (
            f"checkpoint save order mismatch;\n  expected: {expected_phases}\n"
            f"  got:      {saved_phases}"
        )
