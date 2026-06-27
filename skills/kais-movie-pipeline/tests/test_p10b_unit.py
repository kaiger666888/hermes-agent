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


# ===========================================================================
# Task 2 — Degrade WARN path + preview_skipped flag on episode-meta slot
# ===========================================================================


class FakeDegradeEngine(PreviewEngine):
    """Test double that ALWAYS returns a degrade envelope.

    Optionally degrades only specific variant indices (1-based position within
    a shot's 3 variants) for partial-degrade tests. Default: degrade all.
    """

    def __init__(self, *, degrade_positions: set[int] | None = None):
        # When None → degrade ALL variants. When a set, degrade only variants
        # whose position-in-shot (1, 2, or 3) is in the set.
        self._degrade_positions = degrade_positions
        self.calls: list[dict] = []
        self._lock = threading.Lock()
        self._position_counter = 0  # increments per call across all shots

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
        with self._lock:
            self._position_counter += 1
            position_in_shot = ((self._position_counter - 1) % 3) + 1
            self.calls.append({
                "shot_id": shot_id,
                "structure_delta": dict(structure_delta),
                "position_in_shot": position_in_shot,
            })
            should_degrade = (
                self._degrade_positions is None
                or position_in_shot in self._degrade_positions
            )
        if should_degrade:
            return {"degraded": True, "engine": "slideshow", "reason": "test"}
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 100,
            "engine": "slideshow",
        }


class _CapLogCapture:
    """Lightweight capture for logger.warning calls.

    The p10b module uses ``logging.getLogger(__name__)``; we attach a handler
    that records every LogRecord emitted at WARN level or above. Provides a
    ``.records`` list and ``.messages`` list for assertions.
    """

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.records: list = []
        self.messages: list[str] = []
        self._handler = None

    def __enter__(self):
        class _CaptureHandler(logging.Handler):
            def __init__(self, capture):
                super().__init__(level=logging.WARNING)
                self._capture = capture

            def emit(self, record):
                self._capture.records.append(record)
                self._capture.messages.append(record.getMessage())

        self._handler = _CaptureHandler(self)
        self.logger.addHandler(self._handler)
        return self

    def __exit__(self, *exc):
        if self._handler is not None:
            self.logger.removeHandler(self._handler)


import logging  # noqa: E402 — needed for _CapLogCapture (placed late to keep test doubles near use)


def _install_engine(engine):
    """Context-manager-free helper: monkeypatch p10b.select_engine to return engine.

    Returns (original_select,). Tests must restore via ``p10b.select_engine = original``
    in a try/finally block.
    """
    original = p10b.select_engine
    p10b.select_engine = lambda *a, **kw: engine
    return original


class TestP10bDegradePath:
    """Task 2 tests: episode-level full-degrade WARN + episode-meta flag (BLOCKER #1)."""

    def test_all_degrade_single_shot_emits_warn_and_writes_episode_meta(self):
        """Test 1: 1 shot × 3 variants all degrade → WARN + episode-meta flag."""
        engine = FakeDegradeEngine()  # degrade all
        original = _install_engine(engine)
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            with _CapLogCapture("pipeline.phases.p10b_rapid_preview") as cap:
                p10b.run(
                    episode_id="ep-degrade-1",
                    asset_bus_read=recorder.read(slots),
                    asset_bus_write=recorder.make_write(),
                    delegate_task=lambda g, c, t: {},
                    trigger_gate=None,
                    parallel_shots=1,
                )
        finally:
            p10b.select_engine = original

        # WARN log emitted (>=1 warning mentioning preview_skipped).
        preview_warns = [m for m in cap.messages if "preview_skipped" in m]
        assert len(preview_warns) >= 1, (
            f"expected >=1 WARN with 'preview_skipped'; got messages: {cap.messages}"
        )
        # episode-meta slot written with the 3-key shape.
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1, (
            f"expected 1 episode-meta write; got {len(meta_writes)}"
        )
        meta = meta_writes[0]
        assert meta["episode_id"] == "ep-degrade-1"
        assert meta["preview_skipped"] is True
        assert "skip_reason" in meta and isinstance(meta["skip_reason"], str)
        # NOTHING written to rapid-preview-clips (all degraded).
        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 0, (
            f"rapid-preview-clips must be empty on full-degrade; got {len(rapid_writes)}"
        )

    def test_partial_degrade_writes_successes_no_episode_meta(self):
        """Test 2: variant 2 degrades, variants 1 + 3 succeed → 2 writes, NO episode-meta.

        Partial degrade is recoverable — episode-level WARN triggers ONLY when
        ALL variants of ALL shots degrade.
        """
        # Degrade only position 2 of each shot's 3 variants.
        engine = FakeDegradeEngine(degrade_positions={2})
        original = _install_engine(engine)
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            with _CapLogCapture("pipeline.phases.p10b_rapid_preview") as cap:
                p10b.run(
                    episode_id="ep-partial",
                    asset_bus_read=recorder.read(slots),
                    asset_bus_write=recorder.make_write(),
                    delegate_task=lambda g, c, t: {},
                    trigger_gate=None,
                    parallel_shots=1,
                )
        finally:
            p10b.select_engine = original

        # 2 successful variants written (positions 1 + 3).
        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 2, (
            f"expected 2 rapid-preview-clips writes (variants 1 + 3); got {len(rapid_writes)}"
        )
        # NO episode-meta write (not all degraded).
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 0, (
            f"episode-meta must NOT be written on partial degrade; got {len(meta_writes)}"
        )
        # NO WARN log for partial degrade (per-variant degrade is silent).
        preview_warns = [m for m in cap.messages if "preview_skipped" in m]
        assert len(preview_warns) == 0, (
            f"partial degrade must NOT emit episode-level WARN; got: {preview_warns}"
        )

    def test_full_degrade_return_shape(self):
        """Test 3: full-degrade run() returns {phase, outputs{generated=0, degraded=3}, gate=None}."""
        engine = FakeDegradeEngine()
        original = _install_engine(engine)
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            result = p10b.run(
                episode_id="ep-shape",
                asset_bus_read=recorder.read(slots),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )
        finally:
            p10b.select_engine = original

        assert result["phase"] == "p10b_rapid_preview"
        assert result["gate"] is None
        assert result["outputs"]["variants_generated"] == 0
        assert result["outputs"]["variants_degraded"] == 3

    def test_warn_message_contains_preview_skipped_and_episode_id(self):
        """Test 4: WARN message contains 'preview_skipped' AND the episode_id."""
        engine = FakeDegradeEngine()
        original = _install_engine(engine)
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            with _CapLogCapture("pipeline.phases.p10b_rapid_preview") as cap:
                p10b.run(
                    episode_id="ep-warnmsg-XYZ",
                    asset_bus_read=recorder.read(slots),
                    asset_bus_write=recorder.make_write(),
                    delegate_task=lambda g, c, t: {},
                    trigger_gate=None,
                    parallel_shots=1,
                )
        finally:
            p10b.select_engine = original

        preview_warns = [m for m in cap.messages if "preview_skipped" in m]
        assert len(preview_warns) >= 1
        # Episode_id must appear in at least one preview_skipped message.
        assert any("ep-warnmsg-XYZ" in m for m in preview_warns), (
            f"episode_id must be in WARN message; got: {preview_warns}"
        )

    def test_episode_meta_slot_name_not_pipeline_state(self):
        """Test 5 (BLOCKER #1 explicit): asset_bus_write call uses 'episode-meta', not 'pipeline-state'.

        Asserts the slot name on the full-degrade write is exactly 'episode-meta'
        AND the written dict contains episode_id / preview_skipped / skip_reason.
        Captures ALL writes and verifies ONE matches this shape.
        """
        engine = FakeDegradeEngine()
        original = _install_engine(engine)
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            p10b.run(
                episode_id="ep-blocker1",
                asset_bus_read=recorder.read(slots),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )
        finally:
            p10b.select_engine = original

        # Verify NO write to 'pipeline-state' slot (BLOCKER #1 guard).
        assert "pipeline-state" not in recorder.writes, (
            f"BLOCKER #1 VIOLATION: writes to 'pipeline-state' detected: "
            f"{recorder.writes.get('pipeline-state')}"
        )
        # Verify the episode-meta write has the required 3-key shape.
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1
        meta = meta_writes[0]
        assert set(meta.keys()) == {"episode_id", "preview_skipped", "skip_reason"}, (
            f"episode-meta must have exactly 3 keys; got: {set(meta.keys())}"
        )
        assert meta["episode_id"] == "ep-blocker1"
        assert meta["preview_skipped"] is True
        assert isinstance(meta["skip_reason"], str) and meta["skip_reason"]

    def test_no_silent_path_for_engine_degrade(self):
        """Test 6: every degrade either increments a counter that triggers episode-level WARN.

        Verified by code inspection: the run() body's only ``result.get('degraded')``
        branch increments ``degraded_count``; if ``degraded_count == total_variants``
        the WARN fires. There is no code path where a degrade envelope is
        swallowed without either counting toward WARN or raising.
        """
        # Read the module source (run() delegates to _run_body for the
        # fan-out + degrade logic, so we inspect both).
        import inspect
        run_source = inspect.getsource(p10b.run)
        body_source = inspect.getsource(p10b._run_body)
        combined = run_source + "\n" + body_source
        # The degrade branch must increment degraded_count.
        assert "degraded_count" in combined, (
            "run()/_run_body must track degraded_count for episode-level WARN threshold"
        )
        # Must check degraded_count == total_variants for episode-level WARN.
        assert "degraded_count == total_variants" in combined, (
            "run()/_run_body must check degraded_count == total_variants to trigger WARN"
        )
        # Must NOT silently swallow without logger.warning or raise.
        assert "logger.warning" in combined, (
            "run()/_run_body must emit logger.warning on episode-level degrade"
        )

    def test_multi_shot_full_degrade_emits_exactly_one_warn(self):
        """Test 7: 4 shots × 3 variants = 12 degrades → exactly 1 episode-level WARN."""
        engine = FakeDegradeEngine()
        original = _install_engine(engine)
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=4)
            with _CapLogCapture("pipeline.phases.p10b_rapid_preview") as cap:
                p10b.run(
                    episode_id="ep-multishot",
                    asset_bus_read=recorder.read(slots),
                    asset_bus_write=recorder.make_write(),
                    delegate_task=lambda g, c, t: {},
                    trigger_gate=None,
                    parallel_shots=4,
                )
        finally:
            p10b.select_engine = original

        preview_warns = [m for m in cap.messages if "preview_skipped" in m]
        assert len(preview_warns) == 1, (
            f"multi-shot full-degrade must emit exactly 1 episode-level WARN "
            f"(not 12); got {len(preview_warns)}: {preview_warns}"
        )
        # episode-meta written exactly once.
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1, (
            f"episode-meta must be written exactly once; got {len(meta_writes)}"
        )
        # rapid-preview-clips NEVER written.
        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 0

    def test_engine_constructor_failure_caught_defensively(self):
        """Test 8: select_engine() raising → caught, WARN emitted, episode-meta flag written.

        Defensive: plan 02's select_engine should not raise in practice, but
        p10b must be robust. Verifies the try/except wraps the engine selection.
        """
        original = p10b.select_engine

        def _raising_select(*a, **kw):
            raise RuntimeError("simulated engine constructor failure")

        p10b.select_engine = _raising_select
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            with _CapLogCapture("pipeline.phases.p10b_rapid_preview") as cap:
                result = p10b.run(
                    episode_id="ep-engine-fail",
                    asset_bus_read=recorder.read(slots),
                    asset_bus_write=recorder.make_write(),
                    delegate_task=lambda g, c, t: {},
                    trigger_gate=None,
                    parallel_shots=1,
                )
        finally:
            p10b.select_engine = original

        # Did NOT raise — returned a standard envelope.
        assert result["phase"] == "p10b_rapid_preview"
        assert result["gate"] is None
        # WARN log emitted mentioning preview_skipped.
        preview_warns = [m for m in cap.messages if "preview_skipped" in m]
        assert len(preview_warns) >= 1, (
            f"engine constructor failure must emit WARN; got: {cap.messages}"
        )
        # episode-meta flag written.
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1
        assert meta_writes[0]["preview_skipped"] is True


# ---------------------------------------------------------------------------
# Phase 40 CR-02 fix — p10b must release engine resources via context manager
# ---------------------------------------------------------------------------
# Before the CR-02 fix, ``_run_body`` held the engine in a local variable
# and never entered its context manager. ``LTXVideoEngine`` defines
# ``close`` / ``__enter__`` / ``__exit__`` to release its ``httpx.Client``
# connection pool — but those went unused, leaking one client per episode
# in long-running daemons. These tests pin the contract that ``p10b.run``
# enters and exits the engine's context manager exactly once per call.


class _RecordingEngine(PreviewEngine):
    """Engine double that records ``close`` calls and context-manager events."""

    def __init__(self):
        # NOTE: no super().__init__ — PreviewEngine ABC has no init state.
        self.calls: list[str] = []  # ordered event log: "enter", "generate", "close"
        self._lock = threading.Lock()

    def __enter__(self) -> "_RecordingEngine":
        with self._lock:
            self.calls.append("enter")
        return self

    def __exit__(self, *exc) -> None:
        with self._lock:
            self.calls.append("exit")
        # No real resources — skip super().close() to avoid double-logging.

    def close(self) -> None:
        with self._lock:
            self.calls.append("close")

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
        with self._lock:
            self.calls.append("generate")
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 100,
            "engine": "recording",
        }


class TestP10bEngineLifecycle:
    """Phase 40 CR-02 — ``p10b.run`` must enter and exit the engine's context
    manager exactly once per call so engine-held resources (e.g.,
    ``LTXVideoEngine``'s ``httpx.Client``) are released."""

    def test_run_enters_and_exits_engine_context_manager_once(self):
        """After ``p10b.run`` returns, the engine's ``__enter__`` and
        ``__exit__`` must each have been called exactly once — proving
        resources are released.

        Pre-fix: this test FAILS — the engine's ``__enter__`` and
        ``__exit__`` are NEVER called (the engine was held in a local
        variable without ``with``).
        """
        engine = _RecordingEngine()
        original = p10b.select_engine
        p10b.select_engine = lambda *a, **kw: engine
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            p10b.run(
                episode_id="ep-lifecycle",
                asset_bus_read=recorder.read(slots),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )
        finally:
            p10b.select_engine = original

        # Exactly one enter / one exit — regardless of how many variants
        # ran. The fan-out (3 variants for 1 shot) all happen INSIDE the
        # context manager.
        enters = [c for c in engine.calls if c == "enter"]
        exits = [c for c in engine.calls if c == "exit"]
        assert len(enters) == 1, (
            f"engine __enter__ must be called exactly once; got {len(enters)} "
            f"(event log: {engine.calls})"
        )
        assert len(exits) == 1, (
            f"engine __exit__ must be called exactly once; got {len(exits)} "
            f"(event log: {engine.calls})"
        )
        # The enter happens BEFORE any generate call.
        first_generate_idx = engine.calls.index("generate")
        enter_idx = engine.calls.index("enter")
        assert enter_idx < first_generate_idx, (
            f"__enter__ must precede first generate(); log: {engine.calls}"
        )
        # The exit happens AFTER the last generate call.
        last_generate_idx = max(
            i for i, c in enumerate(engine.calls) if c == "generate"
        )
        exit_idx = engine.calls.index("exit")
        assert exit_idx > last_generate_idx, (
            f"__exit__ must follow last generate(); log: {engine.calls}"
        )

    def test_run_exits_engine_context_manager_on_engine_exception(self):
        """If ``engine.generate`` raises mid-fanout, ``__exit__`` MUST still
        run so resources are released even on the exception path.

        Pre-fix: the engine's context manager was never entered at all, so
        __exit__ was also never called — but more importantly, an exception
        from generate() would propagate out of ``_run_body`` and be caught
        by the broad ``except Exception`` in ``run()``, marking the episode
        ``preview_skipped``. Either way, no resources were released.
        """
        class _RaisingEngine(_RecordingEngine):
            def generate(self, **kwargs):
                with self._lock:
                    self.calls.append("generate")
                raise RuntimeError("simulated mid-fanout engine failure")

        engine = _RaisingEngine()
        original = p10b.select_engine
        p10b.select_engine = lambda *a, **kw: engine
        try:
            recorder = _AssetBusRecorder()
            slots = _full_slots(n_shots=1)
            # p10b.run should NOT raise — the broad except catches RuntimeError
            # and emits a preview_skipped envelope.
            result = p10b.run(
                episode_id="ep-lifecycle-exc",
                asset_bus_read=recorder.read(slots),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )
        finally:
            p10b.select_engine = original

        # Episode degraded cleanly.
        assert result["phase"] == "p10b_rapid_preview"
        # __enter__ and __exit__ both ran despite the exception — the with
        # block's __exit__ is called even when the body raises.
        enters = [c for c in engine.calls if c == "enter"]
        exits = [c for c in engine.calls if c == "exit"]
        assert len(enters) == 1, (
            f"engine __enter__ must run even on exception path; "
            f"log: {engine.calls}"
        )
        assert len(exits) == 1, (
            f"engine __exit__ MUST run on exception path (resource leak "
            f"otherwise); log: {engine.calls}"
        )


# ---------------------------------------------------------------------------
# Phase 40 WR-02 fix — episode-meta read-modify-write
# ---------------------------------------------------------------------------
# Before WR-02, both ``run()``'s outer except and ``_run_body``'s
# full-degrade check wrote ``episode-meta`` via the injected
# ``asset_bus_write`` directly. Because ``AssetBus.write`` is atomic-replace
# (tmp-file + ``os.replace``), a concurrent p10b invocation on the same
# workdir would clobber the prior run's ``preview_skipped=True`` flag with
# no trace — defeating the "no silent swallow" red line for the case where
# both runs landed on the full-degrade path.
#
# The fix: ``_merge_and_write_episode_meta`` reads the existing slot,
# merges ``updates`` into it, and writes the merged dict back. Prior
# ``skip_reason`` is preserved as ``previous_skip_reason`` for operator
# observability when both runs land on the skip path.


class TestEpisodeMetaMerge:
    """Phase 40 WR-02 — ``episode-meta`` writes use read-modify-write."""

    def test_merge_preserves_existing_keys(self):
        """Pre-existing keys NOT in ``updates`` survive the write."""
        from pipeline.phases.p10b_rapid_preview import (
            _merge_and_write_episode_meta,
        )

        class _Recorder:
            def __init__(self, initial):
                self.slots = dict(initial)
                self.writes = []

            def read(self, slot):
                return self.slots.get(slot)

            def make_write(self):
                def _w(slot, entry):
                    self.slots[slot] = entry
                    self.writes.append((slot, entry))
                return _w

        rec = _Recorder({"episode-meta": {"prior_flag": "abc"}})
        _merge_and_write_episode_meta(
            rec.read, rec.make_write(), "ep1",
            {"preview_skipped": True, "skip_reason": "test"},
        )
        merged = rec.slots["episode-meta"]
        # New keys present.
        assert merged["preview_skipped"] is True
        assert merged["skip_reason"] == "test"
        # Prior key preserved (NOT clobbered).
        assert merged.get("prior_flag") == "abc"

    def test_merge_preserves_prior_skip_reason_as_previous(self):
        """When both prior and new writes are ``preview_skipped=True`` with
        DIFFERENT skip_reasons, the prior reason is preserved as
        ``previous_skip_reason`` — operators can see both events."""
        from pipeline.phases.p10b_rapid_preview import (
            _merge_and_write_episode_meta,
        )

        class _Recorder:
            def __init__(self, initial):
                self.slots = dict(initial)

            def read(self, slot):
                return self.slots.get(slot)

            def make_write(self):
                def _w(slot, entry):
                    self.slots[slot] = entry
                return _w

        rec = _Recorder({"episode-meta": {
            "preview_skipped": True,
            "skip_reason": "prior_run_degrade",
        }})
        _merge_and_write_episode_meta(
            rec.read, rec.make_write(), "ep1",
            {"preview_skipped": True, "skip_reason": "this_run_degrade"},
        )
        merged = rec.slots["episode-meta"]
        # Latest reason wins on skip_reason.
        assert merged["skip_reason"] == "this_run_degrade"
        # Prior reason preserved as previous_skip_reason.
        assert merged.get("previous_skip_reason") == "prior_run_degrade"

    def test_merge_handles_missing_slot_cleanly(self):
        """When the slot is empty / never written, merge acts as a plain write."""
        from pipeline.phases.p10b_rapid_preview import (
            _merge_and_write_episode_meta,
        )

        class _Recorder:
            def __init__(self):
                self.slots = {}

            def read(self, slot):
                return self.slots.get(slot)

            def make_write(self):
                def _w(slot, entry):
                    self.slots[slot] = entry
                return _w

        rec = _Recorder()
        _merge_and_write_episode_meta(
            rec.read, rec.make_write(), "ep1",
            {"preview_skipped": True, "skip_reason": "first"},
        )
        merged = rec.slots["episode-meta"]
        assert merged == {"preview_skipped": True, "skip_reason": "first"}

    def test_merge_handles_non_dict_existing_slot(self):
        """If the slot somehow contains a non-dict (corruption / legacy),
        merge falls back to treating ``updates`` as the full new value
        rather than crashing."""
        from pipeline.phases.p10b_rapid_preview import (
            _merge_and_write_episode_meta,
        )

        class _Recorder:
            def __init__(self, initial):
                self.slots = dict(initial)

            def read(self, slot):
                return self.slots.get(slot)

            def make_write(self):
                def _w(slot, entry):
                    self.slots[slot] = entry
                return _w

        # Slot contains a list (corrupt state — shouldn't happen but be defensive).
        rec = _Recorder({"episode-meta": ["unexpected", "list"]})
        _merge_and_write_episode_meta(
            rec.read, rec.make_write(), "ep1",
            {"preview_skipped": True, "skip_reason": "post_corrupt"},
        )
        merged = rec.slots["episode-meta"]
        # Merge started from {} (non-dict discarded), so updates are the whole payload.
        assert merged == {"preview_skipped": True, "skip_reason": "post_corrupt"}

    def test_p10b_full_degrade_uses_merge(self):
        """End-to-end: when p10b's full-degrade path fires, the
        episode-meta write goes through the merge path. Verified by
        pre-populating episode-meta with a sentinel key and asserting it
        survives the full-degrade write."""
        engine = FakeDegradeEngine()
        original = p10b.select_engine
        p10b.select_engine = lambda *a, **kw: engine
        try:
            recorder = _AssetBusRecorder()
            # Pre-populate episode-meta with a sentinel key from a "prior run".
            recorder.slots = {
                "episode-meta": {"prior_run_id": "abc-123"},
                **_full_slots(n_shots=1),
            }
            with _CapLogCapture("pipeline.phases.p10b_rapid_preview") as cap:
                p10b.run(
                    episode_id="ep-merge",
                    asset_bus_read=recorder.read(recorder.slots),
                    asset_bus_write=recorder.make_write(),
                    delegate_task=lambda g, c, t: {},
                    trigger_gate=None,
                    parallel_shots=1,
                )
        finally:
            p10b.select_engine = original

        # episode-meta written once.
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1
        merged = meta_writes[0]
        # New keys from this run.
        assert merged["preview_skipped"] is True
        assert "skip_reason" in merged
        # Prior key from the "prior concurrent run" survived.
        assert merged.get("prior_run_id") == "abc-123"
