"""test_p10b_unit.py — Phase 40-03 unit tests for p10b_rapid_preview.

Mirrors the test_p11_unit.py patterns (mocked delegate_task / asset_bus /
ThreadPoolExecutor — no real subagents, no real network, no real LLM per
D-35-08). Verifies ORCHESTRATION CORRECTNESS only:

  - module constants match the p10b contract (PHASE_ID / EXPERT=None /
    INPUT_SLOTS / OUTPUT_SLOTS includes BOTH rapid-preview-clips AND
    episode-meta / GATE_ID=None)
  - _build_variants() returns exactly 3 single-delta variants per shot
  - BLOCKER #4: cycling matrix covers all 4 structure params across a
    multi-shot episode (union of all variant structure_delta keys == 4 params;
    turning_points_sec MUST appear in >=1 variant across shots 0..3)
  - single-delta rule enforced via _validate_structure_delta (Notion 红线 #6)
  - happy path: engine.generate() called 3x per shot; rapid-preview-clips
    written 3x with all 6 required fields
  - parallel fan-out: 4 shots × 3 variants = 12 engine calls
  - run() return shape includes phase / outputs / gate=None

Task 1 (skeleton + variant builder + JSONL write). Task 2 adds the degrade
WARN path tests (TestP10bDegradePath class).
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_p11_unit).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p10b_rapid_preview as p10b  # noqa: E402
from plugins.kais_aigc.preview_engine import PreviewEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeEngine(PreviewEngine):
    """Test double for PreviewEngine — always returns a fixed success envelope.

    Records every generate() call on ``self.calls`` (list of dicts) so tests
    can assert on call count, shot_ids, and structure_delta values. Thread-safe
    via an internal lock (ThreadPoolExecutor fan-out exercises this).
    """

    def __init__(self, *, clip_path_template: str = "/preview/{variant_id}.mp4"):
        # NOTE: deliberately does NOT call super().__init__ — PreviewEngine is
        # an ABC with no __init__ state; we only need generate() overridden.
        self._clip_path_template = clip_path_template
        self.calls: list[dict] = []
        self._lock = threading.Lock()

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
        record = {
            "shot_id": shot_id,
            "prompt": prompt,
            "structure_delta": dict(structure_delta),
            "keyframe_image_path": keyframe_image_path,
            "voice_clip_path": voice_clip_path,
            "output_path": output_path,
        }
        with self._lock:
            self.calls.append(record)
        # Derive a stable clip path from output_path (or fall back to template).
        clip = output_path or self._clip_path_template.format(variant_id=shot_id)
        return {
            "clip_path": clip,
            "generation_time_ms": 100,
            "engine": "slideshow",
        }


class _AssetBusRecorder:
    """In-memory asset_bus_write recorder.

    Captures every (slot, entry) write into ``self.writes[slot] = [entry, ...]``
    so tests can assert on call count, slot names, and record contents.
    """

    def __init__(self):
        self.writes: dict[str, list] = {}
        self._lock = threading.Lock()

    def read(self, slots: dict):
        """Return a read callable backed by the given slots dict."""
        return lambda slot: slots.get(slot)

    def make_write(self):
        def _write(slot: str, entry) -> None:
            with self._lock:
                self.writes.setdefault(slot, []).append(entry)
        return _write


_BASELINE_STRUCTURE = {
    "hook_position_sec": 3,
    "emotion_sequence": ["suppress", "thrill"],
    "turning_points_sec": [3, 15],
    "ending_state": "new_suspense",
}


def _voice_clips(n_shots: int) -> list[dict]:
    """Return a fixture shot list of n_shots voice clips."""
    return [
        {
            "shot_id": f"shot_{i:03d}",
            "clip_path": f"/voice/shot_{i:03d}.wav",
            "intent": f"shot {i} intent text",
            "duration_ms": 3000,
        }
        for i in range(n_shots)
    ]


def _full_slots(n_shots: int = 1) -> dict:
    """Return asset bus slots fixture with voice-clips + voice-timeline + e-konte."""
    return {
        "voice-clips": _voice_clips(n_shots),
        "voice-timeline": {"shots": [{"shot_id": f"shot_{i:03d}"} for i in range(n_shots)]},
        "e-konte-sheets": {"shots": [{"shot_id": f"shot_{i:03d}", "keyframe": f"/kf/{i}.png"} for i in range(n_shots)]},
    }


# ---------------------------------------------------------------------------
# Tests — module constants (Test 1)
# ---------------------------------------------------------------------------


class TestP10bRapidPreview:
    """Task 1 tests: skeleton + variant builder + JSONL write + ThreadPoolExecutor."""

    def test_module_constants_match_contract(self):
        """Test 1: PHASE_ID / EXPERT=None / INPUT/OUTPUT_SLOTS / GATE_ID=None."""
        assert p10b.PHASE_ID == "p10b_rapid_preview"
        assert p10b.EXPERT is None
        assert p10b.INPUT_SLOTS == ["voice-clips", "voice-timeline", "e-konte-sheets"]
        # BOTH slots per BLOCKER #1 (episode-meta is the AssetBus slot for
        # preview_skipped — NOT pipeline-state.json).
        assert p10b.OUTPUT_SLOTS == ["rapid-preview-clips", "episode-meta"]
        assert p10b.GATE_ID is None

    # -------------------------------------------------------------------
    # Tests — variant builder (Tests 2-5)
    # -------------------------------------------------------------------

    def test_build_variants_returns_three_single_delta_variants_for_shot_0(self):
        """Test 2: _build_variants(shot_index=0) returns 3 dicts, each single-key.

        For shot_index=0, the cycling matrix picks params at indices
        [0, 1, 2] = [hook_position_sec, emotion_sequence, turning_points_sec].
        """
        variants = p10b._build_variants(
            shot_id="shot_001",
            shot_index=0,
            baseline_structure=_BASELINE_STRUCTURE,
        )
        assert len(variants) == 3, f"expected 3 variants, got {len(variants)}"
        expected_params = [
            "hook_position_sec",
            "emotion_sequence",
            "turning_points_sec",
        ]
        for i, v in enumerate(variants):
            assert "variant_id" in v, f"variant {i} missing variant_id"
            assert "structure_delta" in v, f"variant {i} missing structure_delta"
            delta = v["structure_delta"]
            assert isinstance(delta, dict), f"variant {i} structure_delta not dict"
            assert len(delta) == 1, (
                f"variant {i} structure_delta must have exactly one key "
                f"(Notion 红线 #6); got {len(delta)}: {list(delta.keys())}"
            )
            only_key = next(iter(delta.keys()))
            assert only_key == expected_params[i], (
                f"variant {i} param mismatch: expected {expected_params[i]!r}, "
                f"got {only_key!r}"
            )

    def test_cycling_matrix_covers_all_four_params_across_multi_shot_episode(self):
        """Test 3 (BLOCKER #4): 4 consecutive shots cover all 4 params.

        Shot N uses params [STRUCTURE_PARAMS[N%4], [(N+1)%4], [(N+2)%4]].
        Across shots 0..3, the union of all variant structure_delta keys MUST
        be all 4 params. AND turning_points_sec MUST appear in >=1 variant
        (the explicit BLOCKER #4 assertion).
        """
        all_keys: set[str] = set()
        for shot_index in range(4):
            variants = p10b._build_variants(
                shot_id=f"shot_{shot_index:03d}",
                shot_index=shot_index,
                baseline_structure=_BASELINE_STRUCTURE,
            )
            for v in variants:
                all_keys.update(v["structure_delta"].keys())
        assert all_keys == {
            "hook_position_sec",
            "emotion_sequence",
            "turning_points_sec",
            "ending_state",
        }, f"cycling matrix union mismatch: got {all_keys}"
        # Explicit BLOCKER #4 assertion.
        assert "turning_points_sec" in all_keys, (
            "BLOCKER #4: turning_points_sec MUST appear in >=1 variant across "
            "a multi-shot episode (cycling matrix coverage)"
        )

    def test_multi_key_delta_rejected_at_validation(self):
        """Test 4: _validate_structure_delta raises on multi-key dict (Notion 红线 #6)."""
        bad_delta = {"hook_position_sec": 5, "emotion_sequence": ["x"]}
        with pytest.raises(ValueError) as exc_info:
            p10b._validate_structure_delta(bad_delta)
        msg = str(exc_info.value)
        assert "single-delta" in msg or "Notion 红线 #6" in msg, (
            f"ValueError message must mention 'single-delta' or 'Notion 红线 #6'; got: {msg!r}"
        )

    def test_invalid_param_name_rejected_at_validation(self):
        """Test 5: _validate_structure_delta raises on unknown param name."""
        bad_delta = {"unknown_param": 5}
        with pytest.raises(ValueError) as exc_info:
            p10b._validate_structure_delta(bad_delta)
        assert "invalid" in str(exc_info.value).lower() or "unknown_param" in str(exc_info.value), (
            f"ValueError must mention invalid param; got: {exc_info.value!r}"
        )

    # -------------------------------------------------------------------
    # Tests — run() happy path (Tests 6-9)
    # -------------------------------------------------------------------

    def _run_single_shot_happy_path(self):
        """Helper: run() with 1 shot + FakeEngine + parallel_shots=1.

        Returns (engine, result, rapid_writes). Used by Tests 6/7/9 to avoid
        duplicating the engine-injection boilerplate.
        """
        engine = FakeEngine()
        # Inject the engine via monkeypatch on p10b.select_engine.
        original_select = p10b.select_engine
        p10b.select_engine = lambda *a, **kw: engine
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            result = p10b.run(
                episode_id="ep-001",
                asset_bus_read=recorder.read(slots),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )
        finally:
            p10b.select_engine = original_select
        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        return engine, result, rapid_writes

    def test_run_single_shot_calls_engine_three_times_and_writes_three_records(self):
        """Test 6: happy path, 1 shot, parallel_shots=1 → 3 engine calls + 3 writes."""
        engine, result, rapid_writes = self._run_single_shot_happy_path()
        assert len(engine.calls) == 3, (
            f"expected 3 engine.generate() calls (1 shot × 3 variants); "
            f"got {len(engine.calls)}"
        )
        assert len(rapid_writes) == 3, (
            f"expected 3 rapid-preview-clips writes; got {len(rapid_writes)}"
        )

    def test_rapid_preview_clips_records_have_all_six_required_fields(self):
        """Test 7: each JSONL record has shot_id/variant_id/structure_delta/clip_path/generation_time_ms/engine."""
        _, _, rapid_writes = self._run_single_shot_happy_path()
        required_fields = {
            "shot_id", "variant_id", "structure_delta",
            "clip_path", "generation_time_ms", "engine",
        }
        for i, rec in enumerate(rapid_writes):
            missing = required_fields - set(rec.keys())
            assert not missing, (
                f"record {i} missing fields: {missing}; got keys: {list(rec.keys())}"
            )
            for field in required_fields:
                assert rec[field] is not None, (
                    f"record {i} field {field!r} is None"
                )

    def test_parallel_fan_out_four_shots_twelve_engine_calls(self):
        """Test 8: 4 shots × 3 variants = 12 engine calls under parallel_shots=4."""
        engine = FakeEngine()
        original_select = p10b.select_engine
        p10b.select_engine = lambda *a, **kw: engine
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=4)
            p10b.run(
                episode_id="ep-001",
                asset_bus_read=recorder.read(slots),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=4,
            )
        finally:
            p10b.select_engine = original_select

        assert len(engine.calls) == 12, (
            f"expected 12 engine calls (4 shots × 3 variants); got {len(engine.calls)}"
        )
        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 12, (
            f"expected 12 rapid-preview-clips writes; got {len(rapid_writes)}"
        )

    def test_run_returns_standard_envelope_with_gate_none(self):
        """Test 9: run() returns {phase, outputs, gate=None}."""
        _, result, _ = self._run_single_shot_happy_path()
        assert result["phase"] == "p10b_rapid_preview"
        assert result["gate"] is None  # GATE_ID is None — CF-36-04 conditional skip
        assert "outputs" in result
        # Outputs include variants_generated count (success path).
        assert result["outputs"].get("variants_generated", 0) == 3
