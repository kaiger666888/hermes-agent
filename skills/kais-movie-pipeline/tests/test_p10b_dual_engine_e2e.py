"""test_p10b_dual_engine_e2e.py — Phase 40-04 Task 1: dual-engine E2E (RAPID-PREVIEW-02).

Cross-engine integration verification of p10b_rapid_preview.run(). Plans 02
and 03 ship unit tests for the engines (test_preview_engine.py) and the
phase module (test_p10b_unit.py). This file EXTENDS that coverage with
integration scenarios that verify BOTH engines correctly flow through the
real p10b.run() fan-out:

  - slideshow path: KAIS_PREVIEW_ENGINE unset (default) + FakeSlideshowEngine
    injected → every record's engine=="slideshow"
  - ltx path: KAIS_PREVIEW_ENGINE=ltx + FakeLTXEngine injected → every
    record's engine=="ltx"
  - select_engine called exactly ONCE per phase run (not per variant)
  - parallel_shots=4 fans out 4 shots × 3 variants = 12 generate() calls
    (thread-safe counter verified)
  - Output envelope shape: {phase, outputs{variants_generated, variants_degraded}, gate=None}

Test-double pattern: mirror test_p10b_unit.py's FakeEngine + _AssetBusRecorder
helpers (separate from those to keep this file self-contained).

Monkeypatch target note: p10b_rapid_preview.py uses the import form
``from plugins.kais_aigc.preview_engine import PreviewEngine, select_engine``
(verified by reading plan 03 implementation). This binds ``select_engine``
into p10b's own module namespace, so the monkeypatch target is
``p10b.select_engine`` (i.e. ``pipeline.phases.p10b_rapid_preview.select_engine``).
"""

from __future__ import annotations

import os
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
# Test doubles — dual-engine variants
# ---------------------------------------------------------------------------


class _ThreadSafeCounter:
    """A thread-safe int counter — used to assert parallel fan-out counts."""

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def inc(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


class FakeSlideshowEngine(PreviewEngine):
    """Test double for the slideshow engine path.

    Always returns a slideshow-tagged success envelope. Accepts a thread-safe
    counter so tests can assert on the number of generate() calls under
    parallel fan-out (Test 4 — 4 shots × 3 variants == 12).
    """

    def __init__(self, counter: _ThreadSafeCounter | None = None) -> None:
        self._counter = counter or _ThreadSafeCounter()
        # Track call args too (used by Test 3 — select_engine call count is
        # asserted separately, but generate() call args are useful for
        # debugging).
        self.calls: list[dict] = []
        self._calls_lock = threading.Lock()

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
        self._counter.inc()
        with self._calls_lock:
            self.calls.append({
                "shot_id": shot_id,
                "structure_delta": dict(structure_delta),
            })
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 9500,
            "engine": "slideshow",
        }


class FakeLTXEngine(PreviewEngine):
    """Test double for the LTX engine path.

    Mirrors FakeSlideshowEngine but tags records with engine="ltx" (mirrors
    the real LTXVideoEngine's success envelope shape).
    """

    def __init__(self, counter: _ThreadSafeCounter | None = None) -> None:
        self._counter = counter or _ThreadSafeCounter()
        self.calls: list[dict] = []
        self._calls_lock = threading.Lock()

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
        self._counter.inc()
        with self._calls_lock:
            self.calls.append({
                "shot_id": shot_id,
                "structure_delta": dict(structure_delta),
            })
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 1200,
            "engine": "ltx",
        }


class _CountingSelectEngine:
    """Wraps an engine instance; records how many times select_engine was called.

    Plan 03's run() calls ``select_engine()`` exactly ONCE at the top of
    ``_run_body`` (not once per variant). This wrapper lets tests assert the
    call count by exposing ``self.select_call_count``.
    """

    def __init__(self, engine: PreviewEngine) -> None:
        self._engine = engine
        self.select_call_count = 0
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs) -> PreviewEngine:
        with self._lock:
            self.select_call_count += 1
        return self._engine


class _AssetBusRecorder:
    """In-memory asset_bus_write recorder (mirrors test_p10b_unit.py pattern)."""

    def __init__(self):
        self.writes: dict[str, list] = {}
        self._lock = threading.Lock()

    def read(self, slots: dict):
        return lambda slot: slots.get(slot)

    def make_write(self):
        def _write(slot: str, entry) -> None:
            with self._lock:
                self.writes.setdefault(slot, []).append(entry)
        return _write


def _fake_delegate_task(goal, context, toolsets):
    """p10b does not call delegate_task (EXPERT is None — pure orchestration).

    The callable exists only to satisfy the run() signature; p10b must never
    actually invoke it. If it ever does, this raises — surfaces the bug.
    """
    raise AssertionError(
        f"p10b should NOT call delegate_task (pure orchestration); "
        f"got called with goal={goal!r}"
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _voice_clips(n_shots: int) -> list[dict]:
    return [
        {
            "shot_id": f"shot_{i:03d}",
            "clip_path": f"/voice/shot_{i:03d}.wav",
            "intent": f"shot {i} intent text",
            "duration_ms": 3000,
        }
        for i in range(n_shots)
    ]


def _full_slots(n_shots: int = 2) -> dict:
    """Asset bus slots fixture: voice-clips + voice-timeline + e-konte-sheets."""
    return {
        "voice-clips": _voice_clips(n_shots),
        "voice-timeline": {
            "shots": [{"shot_id": f"shot_{i:03d}"} for i in range(n_shots)]
        },
        "e-konte-sheets": {
            "shots": [
                {"shot_id": f"shot_{i:03d}", "keyframe": f"/kf/{i}.png"}
                for i in range(n_shots)
            ]
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestP10bDualEngineE2E:
    """RAPID-PREVIEW-02 dual-engine end-to-end verification."""

    def test_slideshow_e2e_writes_rapid_preview_clips_with_slideshow_tag(self, monkeypatch):
        """Test 1: default engine → slideshow; 2 shots × 3 variants = 6 records,
        each tagged engine=="slideshow".
        """
        engine = FakeSlideshowEngine()
        counting = _CountingSelectEngine(engine)
        monkeypatch.setattr(p10b, "select_engine", counting)

        recorder = _AssetBusRecorder()
        slots = _full_slots(n_shots=2)
        result = p10b.run(
            episode_id="ep-slideshow",
            asset_bus_read=recorder.read(slots),
            asset_bus_write=recorder.make_write(),
            delegate_task=_fake_delegate_task,
            trigger_gate=None,
            parallel_shots=2,
        )

        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 6, (
            f"expected 6 records (2 shots × 3 variants); got {len(rapid_writes)}"
        )
        for i, rec in enumerate(rapid_writes):
            assert rec["engine"] == "slideshow", (
                f"record {i} engine mismatch: expected 'slideshow', got {rec['engine']!r}"
            )
        # Output envelope shape (Test 5 contract — early check here).
        assert result["phase"] == "p10b_rapid_preview"
        assert result["gate"] is None
        assert result["outputs"]["variants_generated"] == 6
        assert result["outputs"]["variants_degraded"] == 0

    def test_ltx_e2e_writes_rapid_preview_clips_with_ltx_tag(self, monkeypatch):
        """Test 2: KAIS_PREVIEW_ENGINE=ltx → ltx; 2 shots × 3 variants = 6 records,
        each tagged engine=="ltx".
        """
        monkeypatch.setenv("KAIS_PREVIEW_ENGINE", "ltx")
        engine = FakeLTXEngine()
        counting = _CountingSelectEngine(engine)
        monkeypatch.setattr(p10b, "select_engine", counting)

        recorder = _AssetBusRecorder()
        slots = _full_slots(n_shots=2)
        result = p10b.run(
            episode_id="ep-ltx",
            asset_bus_read=recorder.read(slots),
            asset_bus_write=recorder.make_write(),
            delegate_task=_fake_delegate_task,
            trigger_gate=None,
            parallel_shots=2,
        )

        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 6, (
            f"expected 6 ltx records; got {len(rapid_writes)}"
        )
        for i, rec in enumerate(rapid_writes):
            assert rec["engine"] == "ltx", (
                f"record {i} engine mismatch: expected 'ltx', got {rec['engine']!r}"
            )
        assert result["outputs"]["variants_generated"] == 6

    def test_select_engine_called_exactly_once_per_phase_run(self, monkeypatch):
        """Test 3: p10b.run() calls select_engine() ONCE per phase invocation,
        NOT once per variant. With 2 shots × 3 variants = 6 generate() calls,
        select_engine should still have been called exactly 1 time.

        This proves the engine is constructed once and reused across the
        ThreadPoolExecutor fan-out — not re-resolved per variant.
        """
        engine = FakeSlideshowEngine()
        counting = _CountingSelectEngine(engine)
        monkeypatch.setattr(p10b, "select_engine", counting)

        recorder = _AssetBusRecorder()
        slots = _full_slots(n_shots=2)
        p10b.run(
            episode_id="ep-once",
            asset_bus_read=recorder.read(slots),
            asset_bus_write=recorder.make_write(),
            delegate_task=_fake_delegate_task,
            trigger_gate=None,
            parallel_shots=2,
        )

        # 6 generate() calls happened (engine.calls records them).
        assert len(engine.calls) == 6, (
            f"expected 6 engine.generate() calls; got {len(engine.calls)}"
        )
        # select_engine called EXACTLY ONCE.
        assert counting.select_call_count == 1, (
            f"select_engine should be called exactly once per phase run "
            f"(not once per variant); got {counting.select_call_count}"
        )

    def test_parallel_shots_four_fans_out_twelve_generate_calls(self, monkeypatch):
        """Test 4: 4 shots × 3 variants = 12 generate() calls under parallel_shots=4.

        Thread-safe counter proves all 12 calls were dispatched (no race lost
        any of them). Mirrors the existing test_p10b_unit.py Test 8 contract
        but via a counter that lives on the engine instance (defensive
        against future engine replacement that doesn't expose .calls list).
        """
        counter = _ThreadSafeCounter()
        engine = FakeSlideshowEngine(counter=counter)
        counting = _CountingSelectEngine(engine)
        monkeypatch.setattr(p10b, "select_engine", counting)

        recorder = _AssetBusRecorder()
        slots = _full_slots(n_shots=4)
        p10b.run(
            episode_id="ep-parallel4",
            asset_bus_read=recorder.read(slots),
            asset_bus_write=recorder.make_write(),
            delegate_task=_fake_delegate_task,
            trigger_gate=None,
            parallel_shots=4,
        )

        assert counter.value == 12, (
            f"expected 12 generate() calls (4 shots × 3 variants); "
            f"counter={counter.value}"
        )

    def test_output_envelope_shape_both_engines(self, monkeypatch):
        """Test 5: both engines return {phase, outputs{variants_generated,
        variants_degraded}, gate=None}; sums match expected totals.
        """
        # Slideshow envelope.
        engine_slide = FakeSlideshowEngine()
        monkeypatch.setattr(p10b, "select_engine", _CountingSelectEngine(engine_slide))
        recorder = _AssetBusRecorder()
        result_slide = p10b.run(
            episode_id="ep-shape-slide",
            asset_bus_read=recorder.read(_full_slots(n_shots=2)),
            asset_bus_write=recorder.make_write(),
            delegate_task=_fake_delegate_task,
            trigger_gate=None,
            parallel_shots=2,
        )
        assert result_slide["phase"] == "p10b_rapid_preview"
        assert result_slide["gate"] is None
        gen = result_slide["outputs"]["variants_generated"]
        deg = result_slide["outputs"]["variants_degraded"]
        assert gen + deg == 6, (
            f"slideshow: variants_generated({gen}) + variants_degraded({deg}) "
            f"must equal 6 (total expected)"
        )

        # LTX envelope.
        engine_ltx = FakeLTXEngine()
        monkeypatch.setattr(p10b, "select_engine", _CountingSelectEngine(engine_ltx))
        recorder2 = _AssetBusRecorder()
        result_ltx = p10b.run(
            episode_id="ep-shape-ltx",
            asset_bus_read=recorder2.read(_full_slots(n_shots=2)),
            asset_bus_write=recorder2.make_write(),
            delegate_task=_fake_delegate_task,
            trigger_gate=None,
            parallel_shots=2,
        )
        assert result_ltx["phase"] == "p10b_rapid_preview"
        assert result_ltx["gate"] is None
        gen2 = result_ltx["outputs"]["variants_generated"]
        deg2 = result_ltx["outputs"]["variants_degraded"]
        assert gen2 + deg2 == 6, (
            f"ltx: variants_generated({gen2}) + variants_degraded({deg2}) "
            f"must equal 6 (total expected)"
        )
