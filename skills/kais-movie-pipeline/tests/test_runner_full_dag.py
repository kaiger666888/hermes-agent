"""test_runner_full_dag.py — Phase 36-05 Task 3: full 13-phase DAG integration.

End-to-end orchestration tests against the *real* PHASE_REGISTRY (all 13
phase modules p01..p13). Per D-35-08 / D-36-05 these are MOCKED-DELEGATE
tests: ``delegate_task`` is replaced with a canned-JSON spy so no real
subagent spawns and no real HTTP/LLM is exercised. The phase modules'
*orchestration correctness* (slot reads, goal construction, slot writes,
gate triggering) is exercised for real.

Test coverage:
1. Full DAG runs p01 → p13 sequentially with mocked delegate; all 13 phase
   results returned.
2. Checkpoint resume mid-pipeline: simulate checkpoint at p07 → restart
   runner → only p08..p13 results in the second run, resumed_from=7.
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
# Tests
# ---------------------------------------------------------------------------


class TestFullDagRun:
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

        # All 13 phases ran (none skipped — no checkpoint).
        assert len(result["phases"]) == 13, (
            f"expected 13 phase results, got {len(result['phases'])}; "
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
        results returned (6 phases). resumed_from == 7 (index of p08)."""
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
        # Only p08..p13 should have run (6 phases).
        assert len(result["phases"]) == 6, (
            f"expected 6 phases (p08..p13), got {len(result['phases'])}; "
            f"phases: {sorted(result['phases'].keys())}"
        )
        # p01..p07 should NOT be in the second-run results.
        for early_phase in ("p01_hook_topic", "p07_scene_generation"):
            assert early_phase not in result["phases"], (
                f"{early_phase} should have been skipped on resume"
            )
        # p08..p13 should all be present.
        for late_phase in (
            "p08_scene_selection",
            "p09_shot_breakdown",
            "p10_voice",
            "p11_video_render",
            "p12_composition",
            "p13_delivery",
        ):
            assert late_phase in result["phases"], (
                f"{late_phase} should have run after resume at p08"
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

        # 13 phases × 1 save each == 13 saves, in registry order.
        assert len(store.saved) == 13, (
            f"expected 13 checkpoint saves, got {len(store.saved)}"
        )
        saved_phases = [phase for (_ep, phase) in store.saved]
        expected_phases = [entry["id"] for entry in PHASE_REGISTRY]
        assert saved_phases == expected_phases, (
            f"checkpoint save order mismatch;\n  expected: {expected_phases}\n"
            f"  got:      {saved_phases}"
        )
