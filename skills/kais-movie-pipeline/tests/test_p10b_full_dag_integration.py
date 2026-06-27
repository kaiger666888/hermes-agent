"""test_p10b_full_dag_integration.py — Phase 40-04 Task 4: full-DAG WARNING #9.

Dedicated E2E integration test verifying that the runner correctly iterates
PHASE_REGISTRY to p10b and that ``result["phases"]["p10b_rapid_preview"]``
exists with the expected output shape after a full DAG run with mocked
engines (WARNING #9 fix).

Mirrors the test_runner_full_dag.py patterns:
- _make_full_dag_delegate_spy (canned JSON payloads per phase)
- _StubStore + _StubBus (in-memory store + bus for runner injection)
- RunnerConfig(workdir=..., enable_gates=False) + run_episode(episode_id, cfg, inject={...})

CRITICAL: Unlike test_runner_full_dag.py's TestFullDagRun class, which uses
the _P10bStubProxy to swap in a no-op (because the real p10b was a stub at
plan 01 boundary), THIS test runs the REAL p10b module (plan 03
implementation) with mocked engines. The engines are mocked via
monkeypatch on ``p10b.select_engine`` (the module-level symbol imported
via ``from plugins.kais_aigc.preview_engine import select_engine``).
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
from pipeline.phases import p10b_rapid_preview as p10b  # noqa: E402
from pipeline.runner import RunnerConfig, run_episode  # noqa: E402
from plugins.kais_aigc.preview_engine import PreviewEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles — mirror test_runner_full_dag.py
# ---------------------------------------------------------------------------


def _canned_summary(payload: dict) -> str:
    """Build a delegate_task summary containing a fenced JSON block."""
    return f"Expert output:\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```\nDone."


def _default_per_phase_payloads() -> dict[str, dict]:
    """Per-phase canned payloads whose output slots satisfy downstream reads.

    Voice-clips carries 1 shot so p10b runs its fan-out (1 × 3 = 3 variants).
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
        # p10_voice payload populates voice-clips with 1 shot → p10b fan-out.
        "p10_voice": {
            "voice_clips": [
                {
                    "shot_id": "s1",
                    "clip_path": "/voice/s1.wav",
                    "intent": "shot 1 intent",
                    "duration_ms": 3000,
                }
            ],
            "voice_timeline": {"shots": [{"shot_id": "s1"}]},
        },
        # e-konte-sheets is read by p10b too; populate it via the bus's
        # initial state (set in the test fixture, NOT via p10 delegate).
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
    """Return a delegate_task mock that returns canned JSON per phase.

    Records every invocation on ``.calls`` (list of dicts).
    """
    default_payloads = phase_to_payload or _default_per_phase_payloads()
    calls: list[dict] = []

    def _delegate(goal: str, context: str, toolsets: list[str]) -> dict:
        calls.append({
            "goal": goal,
            "context": context,
            "toolsets": list(toolsets),
        })
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

    _delegate.calls = calls  # type: ignore[attr-defined]
    return _delegate


class _StubStore:
    """Checkpoint store stub — scriptable load_latest_checkpoint + recording save."""

    def __init__(self, initial_checkpoint: dict | None = None):
        self._checkpoint = initial_checkpoint
        self.saved: list[tuple[str, str]] = []

    def load_latest_checkpoint(self, episode_id: str):
        return self._checkpoint

    def save_checkpoint(self, episode_id: str, phase: str, payload: dict):
        self.saved.append((episode_id, phase))
        self._checkpoint = {"phase": phase, "status": "completed"}


class _StubBus:
    """In-memory asset bus — captures ALL writes (JSON or JSONL) without
    enforcing the JSONL format check (so p10b's rapid-preview-clips writes
    land here cleanly under full-DAG runner integration).

    Mirrors test_runner_full_dag.py's _StubBus but adds a ``writes`` recorder
    so we can assert p10b wrote rapid-preview-clips entries.
    """

    def __init__(self, initial_slots: dict[str, Any] | None = None):
        self.slots: dict[str, Any] = dict(initial_slots) if initial_slots else {}
        # Recording side-channel — captures every (slot, entry) pair for assertions.
        self.writes: list[tuple[str, Any]] = []

    def read(self, slot: str):
        return self.slots.get(slot)

    def write(self, slot: str, entry, envelope: bool = True, **kwargs):
        # JSON slots overwrite; JSONL slots append (we honor the format hint
        # by checking ASSET_SCHEMA — but the V5.0 _StubBus unconditionally
        # overwrites; to keep rapid-preview-clips as a list of records we
        # append when slot is jsonl-format).
        from plugins.pipeline_state.asset_bus import ASSET_SCHEMA
        schema = ASSET_SCHEMA.get(slot, {})
        if schema.get("format") == "jsonl":
            self.slots.setdefault(slot, []).append(entry)
        else:
            self.slots[slot] = entry
        self.writes.append((slot, entry))


# ---------------------------------------------------------------------------
# Engine doubles
# ---------------------------------------------------------------------------


class _FakeSuccessEngine(PreviewEngine):
    """Always-succeed engine; tagged 'slideshow'."""

    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,
        voice_clip_path: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 9500,
            "engine": "slideshow",
        }


class _AlwaysDegradeEngine(PreviewEngine):
    """Always-degrade engine; returns degrade envelope."""

    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,
        voice_clip_path: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        return {"degraded": True, "engine": "slideshow", "reason": "dag test"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestP10bFullDagIntegration:
    """WARNING #9 fix: runner iterates PHASE_REGISTRY to p10b in a full DAG run."""

    def test_p10b_appears_in_result_phases_after_full_dag(self, tmp_path, monkeypatch):
        """Test 1: after a full DAG run with mocked engines,
        result["phases"]["p10b_rapid_preview"] exists as a dict.
        """
        # Mock the engine BEFORE running.
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: _FakeSuccessEngine())

        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        # Pre-populate e-konte-sheets (p10b reads it; not produced by p10 delegate).
        bus = _StubBus(initial_slots={
            "e-konte-sheets": {"shots": [{"shot_id": "s1", "keyframe": "/kf/1.png"}]},
        })

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        result = run_episode(
            "ep-fulldag-p10b", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        assert "p10b_rapid_preview" in result["phases"], (
            f"p10b_rapid_preview missing from result['phases']; "
            f"got keys: {sorted(result['phases'].keys())}"
        )
        assert isinstance(result["phases"]["p10b_rapid_preview"], dict)

    def test_p10b_output_shape_in_result_phases(self, tmp_path, monkeypatch):
        """Test 2: result["phases"]["p10b_rapid_preview"] has phase / outputs /
        gate=None shape. outputs has variants_generated (int) + variants_degraded (int).
        """
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: _FakeSuccessEngine())

        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus(initial_slots={
            "e-konte-sheets": {"shots": [{"shot_id": "s1", "keyframe": "/kf/1.png"}]},
        })

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        result = run_episode(
            "ep-shape-p10b", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        p10b_result = result["phases"]["p10b_rapid_preview"]
        assert p10b_result["phase"] == "p10b_rapid_preview"
        assert p10b_result["gate"] is None
        outputs = p10b_result["outputs"]
        assert "variants_generated" in outputs
        assert "variants_degraded" in outputs
        assert isinstance(outputs["variants_generated"], int)
        assert isinstance(outputs["variants_degraded"], int)
        # 1 shot × 3 variants = 3 generated, 0 degraded (FakeSuccessEngine).
        assert outputs["variants_generated"] == 3, (
            f"expected 3 generated; got {outputs['variants_generated']}"
        )
        assert outputs["variants_degraded"] == 0

    def test_p10b_runs_between_p10_and_p11(self, tmp_path, monkeypatch):
        """Test 3: p10_voice runs before p10b_rapid_preview which runs before
        p11_video_render. Verified via the checkpoint save order recorded by
        _StubStore.saved (a list of (episode_id, phase_id) tuples in execution order).
        """
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: _FakeSuccessEngine())

        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus(initial_slots={
            "e-konte-sheets": {"shots": [{"shot_id": "s1", "keyframe": "/kf/1.png"}]},
        })

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        run_episode(
            "ep-order", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        saved_phases = [phase for (_ep, phase) in store.saved]
        # Relative order check (not necessarily adjacent — runner may insert
        # non-checkpointed ops between, but the SEQUENCE in saved must match).
        idx_p10 = saved_phases.index("p10_voice")
        idx_p10b = saved_phases.index("p10b_rapid_preview")
        idx_p11 = saved_phases.index("p11_video_render")
        assert idx_p10 < idx_p10b < idx_p11, (
            f"p10({idx_p10}) < p10b({idx_p10b}) < p11({idx_p11}) violated; "
            f"saved order: {saved_phases}"
        )

    def test_runner_handles_p10b_degrade_gracefully_in_dag(self, tmp_path, monkeypatch):
        """Test 4: with AlwaysDegradeEngine, the full DAG still completes —
        p10b returns its degrade envelope, runner proceeds to p11.

        result["phases"]["p10b_rapid_preview"] exists with
        outputs.variants_degraded == total_variants AND variants_generated == 0.
        The runner does NOT raise.
        """
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: _AlwaysDegradeEngine())

        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus(initial_slots={
            "e-konte-sheets": {"shots": [{"shot_id": "s1", "keyframe": "/kf/1.png"}]},
        })

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        # run_episode must NOT raise — the degrade path is graceful.
        result = run_episode(
            "ep-degrade-dag", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        p10b_result = result["phases"]["p10b_rapid_preview"]
        assert p10b_result["outputs"]["variants_generated"] == 0, (
            f"degrade path: variants_generated must be 0; "
            f"got {p10b_result['outputs']['variants_generated']}"
        )
        assert p10b_result["outputs"]["variants_degraded"] == 3, (
            f"degrade path: expected 3 degraded (1 shot × 3 variants); "
            f"got {p10b_result['outputs']['variants_degraded']}"
        )
        # Runner proceeded past p10b to p11 — p11 in result["phases"].
        assert "p11_video_render" in result["phases"], (
            f"runner should proceed to p11 after p10b degrade; "
            f"phases: {sorted(result['phases'].keys())}"
        )

    def test_rapid_preview_clips_slot_populated_after_successful_dag(
        self, tmp_path, monkeypatch
    ):
        """Test 5: after a successful DAG run, the AssetBus's rapid-preview-clips
        slot has >=1 record. Each record has all 6 required fields per the format
        contract (verified by Task 2's JSONL tests; here we just check the slot
        was populated with N records where N == total expected variants).
        """
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: _FakeSuccessEngine())

        delegate = _make_full_dag_delegate_spy()
        store = _StubStore(initial_checkpoint=None)
        bus = _StubBus(initial_slots={
            "e-konte-sheets": {"shots": [{"shot_id": "s1", "keyframe": "/kf/1.png"}]},
        })

        cfg = RunnerConfig(workdir=str(tmp_path), enable_gates=False)
        run_episode(
            "ep-populated", cfg,
            inject={
                "store": store,
                "bus": bus,
                "delegate_task": delegate,
            },
        )

        # The bus's rapid-preview-clips slot has 3 records (1 shot × 3 variants).
        rapid_records = bus.slots.get("rapid-preview-clips", [])
        assert len(rapid_records) >= 1, (
            f"rapid-preview-clips must be populated; got {rapid_records}"
        )
        assert len(rapid_records) == 3, (
            f"expected 3 records; got {len(rapid_records)}"
        )
        # Each record has all 6 required fields.
        required_fields = {
            "shot_id", "variant_id", "structure_delta",
            "clip_path", "generation_time_ms", "engine",
        }
        for i, rec in enumerate(rapid_records):
            missing = required_fields - set(rec.keys())
            assert not missing, f"record {i} missing fields: {missing}"

    def test_phase_registry_index_p10b_at_eleven(self):
        """Test 6: PHASE_REGISTRY index sanity — p10b_rapid_preview at index 10
        (between p10_voice at 9 and p11_video_render at 11).

        Verifies the plan 01 insertion landed and survived through plan 03.
        """
        ids = [entry["id"] for entry in PHASE_REGISTRY]
        assert ids.index("p10b_rapid_preview") == 10, (
            f"p10b_rapid_preview must be at index 10 (between p10@9 and p11@11); "
            f"got index {ids.index('p10b_rapid_preview')}; full order: {ids}"
        )
        # Sanity: relative ordering.
        assert ids.index("p10_voice") < ids.index("p10b_rapid_preview") < ids.index("p11_video_render"), (
            f"p10 < p10b < p11 violated; order: {ids}"
        )
