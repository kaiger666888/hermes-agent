"""test_p10b_degrade_warning.py — Phase 40-04 Task 3: WARN-level degrade + episode-meta.

RAPID-PREVIEW-05 + BLOCKER #1 strict verification. Extends the plan 03
TestP10bDegradePath unit tests with STRICTER WARN-level + episode-meta
slot-name assertions:

  - degrade level is exactly WARNING (NOT INFO, NOT ERROR)
  - WARN message contains "preview_skipped" (canonical monitoring token)
  - WARN message contains episode_id (operator correlation)
  - preview_skipped flag persisted to "episode-meta" slot (BLOCKER #1)
  - no WARN on partial degrade
  - no WARN on full success
  - WARN fires exactly once for multi-shot full degrade
  - return value on full degrade matches expected shape
  - BLOCKER #1 negative assertion: ZERO writes target "pipeline-state"

Uses pytest's built-in caplog fixture (not a custom handler) — the
canonical way to capture log records in pytest.

Monkeypatch target: p10b.select_engine (the module-level symbol imported
via ``from plugins.kais_aigc.preview_engine import select_engine``).
"""

from __future__ import annotations

import logging
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


class AlwaysDegradeEngine(PreviewEngine):
    """Engine that ALWAYS returns a degrade envelope (full-degrade scenario)."""

    def __init__(self) -> None:
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
        with self._lock:
            self.calls.append({"shot_id": shot_id})
        return {
            "degraded": True,
            "engine": "slideshow",
            "reason": "test forced degrade",
        }


class PartialDegradeEngine(PreviewEngine):
    """Engine that degrades ONLY when structure_delta matches a specific key.

    Used by Test 5 (no WARN on partial degrade) — only variants whose
    structure_delta matches ``degrade_key`` degrade; others succeed.
    Default ``degrade_key="emotion_sequence"``.
    """

    def __init__(self, *, degrade_key: str = "emotion_sequence") -> None:
        self._degrade_key = degrade_key

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
        if self._degrade_key in structure_delta:
            return {"degraded": True, "engine": "slideshow", "reason": "partial test"}
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 100,
            "engine": "slideshow",
        }


class _AlwaysSucceedEngine(PreviewEngine):
    """Engine that always returns a success envelope (full-success scenario)."""

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
            "generation_time_ms": 100,
            "engine": "slideshow",
        }


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


def _voice_clips(n_shots: int) -> list[dict]:
    return [
        {
            "shot_id": f"shot_{i:03d}",
            "clip_path": f"/voice/shot_{i:03d}.wav",
            "intent": f"shot {i} intent",
            "duration_ms": 3000,
        }
        for i in range(n_shots)
    ]


def _full_slots(n_shots: int = 1) -> dict:
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


@pytest.fixture
def patched_degrade_engine(monkeypatch):
    """Install AlwaysDegradeEngine via monkeypatch; return the engine."""
    engine = AlwaysDegradeEngine()
    monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)
    return engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestP10bDegradeWarning:
    """RAPID-PREVIEW-05 strict WARN-level + episode-meta slot assertions."""

    def test_degrade_warn_level_is_warning_not_info_not_error(
        self, monkeypatch, caplog
    ):
        """Test 1: on full-degrade, at least one log record has levelno == WARNING.

        NOT INFO (would be silent-swallow by default logging config).
        NOT ERROR (would crash monitoring / trip wrong alerts).
        Strict: caplog.at_level(WARNING) captures WARN+; we filter for ==WARNING.
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        with caplog.at_level(logging.WARNING, logger="pipeline.phases.p10b_rapid_preview"):
            p10b.run(
                episode_id="ep-level",
                asset_bus_read=recorder.read(_full_slots(n_shots=1)),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )

        # Filter to records emitted by p10b's logger only (caplog catches all).
        p10b_warns = [
            r for r in caplog.records
            if r.name == "pipeline.phases.p10b_rapid_preview"
            and r.levelno == logging.WARNING
        ]
        assert len(p10b_warns) >= 1, (
            f"expected >=1 WARN-level record from p10b; got levels: "
            f"{[(r.name, r.levelname) for r in caplog.records]}"
        )
        # STRICT: the degrade WARN must NOT be INFO and NOT ERROR.
        preview_warns = [r for r in p10b_warns if "preview_skipped" in r.getMessage()]
        assert len(preview_warns) >= 1, (
            f"no preview_skipped WARN found; messages: "
            f"{[r.getMessage() for r in p10b_warns]}"
        )
        for r in preview_warns:
            assert r.levelno == logging.WARNING, (
                f"degrade WARN level must be WARNING ({logging.WARNING}); "
                f"got {r.levelno}"
            )

    def test_warn_message_contains_preview_skipped_token(self, monkeypatch, caplog):
        """Test 2: the WARNING record's message contains the literal 'preview_skipped'.

        This is the canonical token monitoring/alerting will grep for.
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        with caplog.at_level(logging.WARNING, logger="pipeline.phases.p10b_rapid_preview"):
            p10b.run(
                episode_id="ep-token",
                asset_bus_read=recorder.read(_full_slots(n_shots=1)),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )

        messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("preview_skipped" in m for m in messages), (
            f"no WARN message contains 'preview_skipped'; got: {messages}"
        )

    def test_warn_message_contains_episode_id(self, monkeypatch, caplog):
        """Test 3: WARN message contains the actual episode_id argument value.

        Operators must be able to correlate which episode degraded.
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        episode_id = "ep-correlate-XYZ-12345"
        with caplog.at_level(logging.WARNING, logger="pipeline.phases.p10b_rapid_preview"):
            p10b.run(
                episode_id=episode_id,
                asset_bus_read=recorder.read(_full_slots(n_shots=1)),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )

        preview_warns = [
            r.getMessage() for r in caplog.records
            if r.levelno == logging.WARNING and "preview_skipped" in r.getMessage()
        ]
        assert len(preview_warns) >= 1
        assert any(episode_id in m for m in preview_warns), (
            f"episode_id {episode_id!r} not in any WARN message; got: {preview_warns}"
        )

    def test_preview_skipped_flag_persisted_to_episode_meta_slot(
        self, monkeypatch
    ):
        """Test 4 (BLOCKER #1): on full-degrade, asset_bus_write was called with
        ("episode-meta", {episode_id, preview_skipped: True, skip_reason}).

        The slot name MUST be exactly "episode-meta" — NOT "pipeline-state".
        The dict MUST contain exactly the 3 keys.
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        p10b.run(
            episode_id="ep-blocker1-flag",
            asset_bus_read=recorder.read(_full_slots(n_shots=1)),
            asset_bus_write=recorder.make_write(),
            delegate_task=lambda g, c, t: {},
            trigger_gate=None,
            parallel_shots=1,
        )

        # Exactly ONE write to "episode-meta" with the 3-key shape.
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1, (
            f"expected 1 episode-meta write; got {len(meta_writes)}"
        )
        meta = meta_writes[0]
        assert set(meta.keys()) == {"episode_id", "preview_skipped", "skip_reason"}, (
            f"episode-meta must have exactly 3 keys; got: {set(meta.keys())}"
        )
        assert meta["episode_id"] == "ep-blocker1-flag"
        assert meta["preview_skipped"] is True, (
            f"preview_skipped must be True; got {meta['preview_skipped']!r}"
        )
        assert isinstance(meta["skip_reason"], str) and meta["skip_reason"], (
            f"skip_reason must be non-empty str; got {meta['skip_reason']!r}"
        )

    def test_no_warn_on_partial_degrade(self, monkeypatch, caplog):
        """Test 5: partial degrade (1 of 3 variants degrades) does NOT emit a WARN.

        Per-variant degrade is silent (recoverable — successes still flow to
        rapid-preview-clips). Episode-level WARN triggers ONLY when ALL
        variants of ALL shots degrade.
        """
        # The cycling matrix picks params [hook_position_sec, emotion_sequence,
        # turning_points_sec] for shot 0. PartialDegradeEngine degrades only
        # when emotion_sequence is in structure_delta → exactly 1 of 3 variants
        # degrades, the other 2 succeed.
        engine = PartialDegradeEngine(degrade_key="emotion_sequence")
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        with caplog.at_level(logging.WARNING, logger="pipeline.phases.p10b_rapid_preview"):
            result = p10b.run(
                episode_id="ep-partial",
                asset_bus_read=recorder.read(_full_slots(n_shots=1)),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )

        # 2 variants succeeded; only 1 degraded.
        rapid_writes = recorder.writes.get("rapid-preview-clips", [])
        assert len(rapid_writes) == 2, (
            f"partial degrade: expected 2 successful writes; got {len(rapid_writes)}"
        )
        # ZERO WARN-level records.
        warn_records = [
            r for r in caplog.records
            if r.name == "pipeline.phases.p10b_rapid_preview"
            and r.levelno >= logging.WARNING
        ]
        assert len(warn_records) == 0, (
            f"partial degrade must NOT emit WARN; got: "
            f"{[(r.levelname, r.getMessage()) for r in warn_records]}"
        )
        # ZERO writes to episode-meta (no episode-level degrade).
        assert recorder.writes.get("episode-meta", []) == []
        # Result envelope reports the degrade count (per-variant accounting).
        assert result["outputs"]["variants_degraded"] == 1
        assert result["outputs"]["variants_generated"] == 2

    def test_no_warn_on_full_success(self, monkeypatch, caplog):
        """Test 6: all variants succeed → NO WARN, NO preview_skipped flag."""
        engine = _AlwaysSucceedEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        with caplog.at_level(logging.WARNING, logger="pipeline.phases.p10b_rapid_preview"):
            result = p10b.run(
                episode_id="ep-success",
                asset_bus_read=recorder.read(_full_slots(n_shots=1)),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=1,
            )

        warn_records = [
            r for r in caplog.records
            if r.name == "pipeline.phases.p10b_rapid_preview"
            and r.levelno >= logging.WARNING
        ]
        assert len(warn_records) == 0, (
            f"full success must NOT emit WARN; got {warn_records}"
        )
        # No episode-meta write (no degrade).
        assert recorder.writes.get("episode-meta", []) == []
        # All variants generated.
        assert result["outputs"]["variants_generated"] == 3
        assert result["outputs"]["variants_degraded"] == 0

    def test_warn_fires_exactly_once_for_multi_shot_full_degrade(
        self, monkeypatch, caplog
    ):
        """Test 7: 4 shots × 3 variants = 12 all-degrade → exactly 1 WARN.

        The WARN is episode-level (not per-shot). AND exactly 1 episode-meta
        write (not 12).
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        with caplog.at_level(logging.WARNING, logger="pipeline.phases.p10b_rapid_preview"):
            p10b.run(
                episode_id="ep-multishot-once",
                asset_bus_read=recorder.read(_full_slots(n_shots=4)),
                asset_bus_write=recorder.make_write(),
                delegate_task=lambda g, c, t: {},
                trigger_gate=None,
                parallel_shots=4,
            )

        preview_warns = [
            r for r in caplog.records
            if r.name == "pipeline.phases.p10b_rapid_preview"
            and r.levelno == logging.WARNING
            and "preview_skipped" in r.getMessage()
        ]
        assert len(preview_warns) == 1, (
            f"multi-shot full-degrade must emit exactly 1 episode-level WARN "
            f"(not 12); got {len(preview_warns)}"
        )
        # Exactly 1 episode-meta write (not 12).
        meta_writes = recorder.writes.get("episode-meta", [])
        assert len(meta_writes) == 1, (
            f"episode-meta must be written exactly once; got {len(meta_writes)}"
        )
        # rapid-preview-clips NEVER written on full-degrade.
        assert recorder.writes.get("rapid-preview-clips", []) == []

    def test_return_value_on_full_degrade(self, monkeypatch):
        """Test 8: full-degrade run() returns {phase, outputs{generated=0,
        degraded=total}, gate=None} — does NOT raise.
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        result = p10b.run(
            episode_id="ep-returnval",
            asset_bus_read=recorder.read(_full_slots(n_shots=4)),
            asset_bus_write=recorder.make_write(),
            delegate_task=lambda g, c, t: {},
            trigger_gate=None,
            parallel_shots=4,
        )

        assert result["phase"] == "p10b_rapid_preview"
        assert result["gate"] is None
        assert result["outputs"]["variants_generated"] == 0
        # 4 shots × 3 variants = 12 degraded.
        assert result["outputs"]["variants_degraded"] == 12, (
            f"expected 12 degraded; got {result['outputs']['variants_degraded']}"
        )

    def test_no_write_targets_pipeline_state_slot(self, monkeypatch):
        """Test 9 (BLOCKER #1 negative): ZERO asset_bus_write calls target
        the "pipeline-state" slot — proves the slot rename landed.

        Only "episode-meta" + "rapid-preview-clips" should appear; on
        full-degrade, "rapid-preview-clips" should have ZERO writes too (no
        successes), leaving "episode-meta" as the sole write target.
        """
        engine = AlwaysDegradeEngine()
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        recorder = _AssetBusRecorder()
        p10b.run(
            episode_id="ep-negassert",
            asset_bus_read=recorder.read(_full_slots(n_shots=1)),
            asset_bus_write=recorder.make_write(),
            delegate_task=lambda g, c, t: {},
            trigger_gate=None,
            parallel_shots=1,
        )

        # BLOCKER #1 negative assertion.
        assert "pipeline-state" not in recorder.writes, (
            f"BLOCKER #1 VIOLATION: writes to 'pipeline-state' detected: "
            f"{recorder.writes.get('pipeline-state')}"
        )
        # Sanity: only episode-meta was written on full-degrade (rapid-preview-clips empty).
        assert set(recorder.writes.keys()) == {"episode-meta"}, (
            f"unexpected slot writes: {list(recorder.writes.keys())}; "
            f"expected only 'episode-meta' on full-degrade"
        )
