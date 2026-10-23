"""Tests for the PreviewEngine strategy (single H3 preview engine).

Engine unification (2026-08-10): the dual-engine strategy (slideshow FFmpeg +
LTX-Video HTTP) was retired. ``H3PreviewEngine`` is the sole concrete engine,
composing an ``H3VideoEngine`` (profile=turbo) for the preview tier.

Test classes:

- ``TestPreviewEngineABC``: ABC shape, ``PreviewEngineError``,
  ``select_engine()`` factory dispatch (default h3 + unknown-env fallback).
- ``TestH3PreviewEngine``: ``H3PreviewEngine.generate`` bridge logic — builds a
  shot with ``h3_useCase="preview-lock"``, reads ``h3_motion`` from
  ``structure_delta``, delegates to ``H3VideoEngine.render``, and returns the
  render envelope verbatim. Uses a fake wrapped H3VideoEngine for bridge
  assertions + one MockTransport integration test for the full chain.
- ``TestPathTraversalValidation``: the standalone ``_validate_path_under_root``
  helper (kept for production opt-in path validation).
- ``TestPreviewEngineContextManager``: ``with`` protocol on H3PreviewEngine
  delegates close() to the wrapped H3VideoEngine.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

# Ensure hermes-agent root is importable so ``plugins.kais_aigc.*`` resolves.
HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.preview_engine import (  # noqa: E402
    H3PreviewEngine,
    PreviewEngine,
    PreviewEngineError,
    select_engine,
)


class TestPreviewEngineABC:
    """ABC shape, error class, factory dispatch (single H3 engine)."""

    def test_preview_engine_is_abc(self):
        from abc import ABC

        assert issubclass(PreviewEngine, ABC)

    def test_preview_engine_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            PreviewEngine()

    def test_generate_is_abstract_method(self):
        assert getattr(
            PreviewEngine.generate, "__isabstractmethod__", False
        ) is True

    def test_preview_engine_error_is_exception_subclass(self):
        assert issubclass(PreviewEngineError, Exception)

    def test_select_engine_default_returns_h3(self, monkeypatch):
        # Simulate KAIS_PREVIEW_ENGINE unset.
        monkeypatch.delenv("KAIS_PREVIEW_ENGINE", raising=False)
        engine = select_engine()
        assert isinstance(engine, H3PreviewEngine)

    def test_select_engine_env_h3_returns_h3(self):
        engine = select_engine(env="h3")
        assert isinstance(engine, H3PreviewEngine)

    def test_select_engine_unknown_env_falls_back_to_h3_with_warn(
        self, caplog
    ):
        import logging

        with caplog.at_level(logging.WARNING, logger="plugins.kais_aigc.preview_engine"):
            engine = select_engine(env="totally-bogus-value")
        assert isinstance(engine, H3PreviewEngine)
        # WARN log must mention the unknown value (T-40-09 mitigation).
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "totally-bogus-value" in joined
        assert "h3" in joined.lower()

    def test_select_engine_reads_env_at_call_time_not_import_time(self, monkeypatch):
        # First call: env unset -> h3.
        monkeypatch.delenv("KAIS_PREVIEW_ENGINE", raising=False)
        first = select_engine()
        assert isinstance(first, H3PreviewEngine)
        # Set env to h3 between calls; second call must reflect the resolved value.
        monkeypatch.setenv("KAIS_PREVIEW_ENGINE", "h3")
        second = select_engine()
        assert isinstance(second, H3PreviewEngine)
        # A distinct instance is returned per call (no shared mutable state).
        assert first is not second


class _FakeH3VideoEngine:
    """Test double for the wrapped H3VideoEngine.

    Records the ``render()`` call and returns a canned envelope. The bridge
    logic in H3PreviewEngine.generate is what we're verifying — the fake lets
    us assert exactly what shot dict + kwargs crossed the boundary.
    """

    def __init__(self, render_return=None, render_raises=None):
        self.render_calls: list[dict] = []
        self._render_return = render_return or {
            "clip_path": "/preview/ep1/v1.mp4",
            "generation_time_ms": 42,
            "engine": "h3",
            "frame_count": 124,
            "video_url": "http://h3/x.mp4",
        }
        self._render_raises = render_raises
        self.closed = False

    def render(self, **kwargs):
        self.render_calls.append(kwargs)
        if self._render_raises is not None:
            raise self._render_raises
        # Return a fresh copy so callers can't mutate our canned envelope.
        return dict(self._render_return)

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True


class TestH3PreviewEngineRef2va:
    """2026-08-16 character-consistency fix — ref2va branch of the bridge.

    ``turnaround_paths`` / ``scene_ref_path`` carry the shot's character
    turnarounds + scene reference into the H3 refImages[] multipart. At
    least one existing file → ``mode: "ref2va"`` + forwarded verbatim;
    both absent → ``mode: "t2va"`` (pre-fix behavior, byte-identical
    forwarding of the empty/None values).
    """

    def test_turnaround_paths_existing_file_switches_to_ref2va(self, tmp_path):
        """A turnaround that exists on disk → mode=ref2va + forwarded."""
        ta = tmp_path / "l2_amao_S1.png"
        ta.write_bytes(b"fake-png")
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        engine.generate(
            shot_id="S1_0000", prompt="x", structure_delta={},
            output_path="/o.mp4",
            turnaround_paths=[str(ta)],
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["mode"] == "ref2va"
        assert fake.render_calls[0]["turnaround_paths"] == [str(ta)]
        assert fake.render_calls[0]["scene_ref_path"] is None

    def test_scene_ref_existing_file_switches_to_ref2va(self, tmp_path):
        """Scene ref alone (no turnarounds) is enough for ref2va."""
        sr = tmp_path / "S01_front.png"
        sr.write_bytes(b"fake-png")
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        engine.generate(
            shot_id="S1_0000", prompt="x", structure_delta={},
            output_path="/o.mp4",
            scene_ref_path=str(sr),
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["mode"] == "ref2va"
        assert fake.render_calls[0]["scene_ref_path"] == str(sr)
        assert fake.render_calls[0]["turnaround_paths"] is None

    def test_no_refs_stays_t2va(self):
        """Both params absent → mode stays t2va (pre-fix default)."""
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["mode"] == "t2va"
        # None forwarded verbatim (engine layer skips empty refs).
        assert fake.render_calls[0]["turnaround_paths"] is None
        assert fake.render_calls[0]["scene_ref_path"] is None

    def test_stale_paths_degrade_to_t2va(self, tmp_path):
        """Declared-but-missing files (stale shot-list) → t2va, NOT a
        ref2va shot whose every refImages entry would resolve to nothing."""
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
            turnaround_paths=[str(tmp_path / "missing_amao.png")],
            scene_ref_path=str(tmp_path / "missing_front.png"),
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["mode"] == "t2va"
        # Paths still forwarded — engine-layer _build_multipart skips the
        # missing files itself (isfile check there).
        assert fake.render_calls[0]["turnaround_paths"] == [
            str(tmp_path / "missing_amao.png")
        ]

    def test_mixed_existing_and_missing_turnaround_uses_ref2va(self, tmp_path):
        """One existing turnaround among missing ones → ref2va (any() check)."""
        ta = tmp_path / "real.png"
        ta.write_bytes(b"png")
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
            turnaround_paths=[str(tmp_path / "gone.png"), str(ta)],
        )
        assert fake.render_calls[0]["shot"]["mode"] == "ref2va"

    def test_empty_turnaround_list_stays_t2va(self):
        """Empty list (no character_refs) + no scene ref → t2va."""
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
            turnaround_paths=[],
        )
        assert fake.render_calls[0]["shot"]["mode"] == "t2va"

    def test_keyframe_image_path_still_accepted_not_consumed(self, tmp_path):
        """Deprecated keyframe_image_path: accepted for signature compat,
        never consumed — even a real file must NOT flip the mode."""
        kf = tmp_path / "keyframe.png"
        kf.write_bytes(b"png")
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        result = engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
            keyframe_image_path=str(kf),
        )
        assert fake.render_calls[0]["shot"]["mode"] == "t2va"
        assert result["clip_path"] == "/preview/ep1/v1.mp4"  # envelope verbatim




    def _engine_with_fake(self, render_return=None, render_raises=None):
        """Build an H3PreviewEngine with its wrapped H3VideoEngine replaced."""
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        engine._h3 = _FakeH3VideoEngine(
            render_return=render_return, render_raises=render_raises,
        )
        return engine, engine._h3

    def test_generate_delegates_to_h3videoengine_render(self):
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="a prompt",
            structure_delta={"hook_position_sec": 5, "h3_motion": "high"},
            output_path="/preview/ep1/v1.mp4",
        )
        assert len(fake.render_calls) == 1
        # The bridge passes output_path, prompt, and voice_clip_path through.
        call = fake.render_calls[0]
        assert call["output_path"] == "/preview/ep1/v1.mp4"
        assert call["prompt"] == "a prompt"
        assert call["voice_clip_path"] is None

    def test_generate_forwards_first_frame_to_render(self):
        """2026-08-22 SPEC-firstframe: preview tier forwards first_frame
        verbatim into H3VideoEngine.render (multipart `image` first-frame
        lock); None default keeps pre-change call shape."""
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            output_path="/o.mp4",
            first_frame="/assets/P11/spec_firstframes/s1.png",
        )
        assert fake.render_calls[0]["first_frame"] == "/assets/P11/spec_firstframes/s1.png"
        # Default (no first_frame) → None, engine-side skips the image part.
        engine2, fake2 = self._engine_with_fake()
        engine2.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
        )
        assert fake2.render_calls[0]["first_frame"] is None

    def test_generate_builds_shot_with_h3_usecase_preview_lock(self):
        """h3_useCase is hardcoded 'preview-lock' — this IS the preview tier.

        2026-08-17 useCase 入口迁移: 预览档经 KAP preview-lock 动态路由
        (low→turbo4 / medium→turbo8 / high→native-sage15)。"""
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["h3_useCase"] == "preview-lock"

    def test_generate_reads_h3_motion_from_structure_delta(self):
        """h3_motion is sourced from structure_delta so p11a's classification
        reaches the engine's motion-adaptive step selector."""
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={"h3_motion": "low"},
            output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["h3_motion"] == "low"

    def test_generate_defaults_h3_motion_to_medium_when_absent(self):
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={"hook_position_sec": 5},  # no h3_motion
            output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["h3_motion"] == "medium"

    def test_generate_reads_duration_sec_from_structure_delta(self):
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={"duration_sec": 8.0},
            output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["duration_sec"] == 8.0

    def test_generate_defaults_duration_sec_to_5_when_absent(self):
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["duration_sec"] == 5.0

    def test_generate_carries_shot_id_and_prompt_into_shot(self):
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="S1_001",
            prompt="driver speaks",
            structure_delta={},
            output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["shot_id"] == "S1_001"
        assert shot["prompt"] == "driver speaks"
        assert shot["intent"] == "driver speaks"

    def test_generate_returns_render_envelope_verbatim(self):
        """The H3VideoEngine.render envelope is returned unchanged — no
        reshaping (H3VideoEngine already returns the PreviewEngine-compatible
        shape)."""
        canned = {
            "clip_path": "/x.mp4",
            "generation_time_ms": 99,
            "engine": "h3",
            "frame_count": 122,
            "video_url": "http://h3/x.mp4",
        }
        engine, _ = self._engine_with_fake(render_return=canned)
        result = engine.generate(
            shot_id="s1", prompt="x", structure_delta={}, output_path="/o.mp4",
        )
        assert result == canned
        assert "degraded" not in result

    def test_generate_returns_degrade_envelope_verbatim(self):
        """A degrade envelope from H3VideoEngine.render is also returned
        verbatim (D-09 contract — no raise to the caller)."""
        canned = {"degraded": True, "engine": "h3", "reason": "missing prompt"}
        engine, _ = self._engine_with_fake(render_return=canned)
        result = engine.generate(
            shot_id="s1", prompt="", structure_delta={}, output_path="/o.mp4",
        )
        assert result == canned

    def test_generate_forwards_voice_clip_path(self):
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            voice_clip_path="/voice/s1.wav",
            output_path="/o.mp4",
        )
        assert fake.render_calls[0]["voice_clip_path"] == "/voice/s1.wav"

    def test_generate_handles_none_structure_delta_gracefully(self):
        """A None structure_delta (defensive) doesn't crash the bridge."""
        engine, fake = self._engine_with_fake()
        engine.generate(
            shot_id="s1", prompt="x", structure_delta=None, output_path="/o.mp4",
        )
        shot = fake.render_calls[0]["shot"]
        assert shot["h3_motion"] == "medium"
        assert shot["duration_sec"] == 5.0

    def test_constructor_forwards_kwargs_to_wrapped_h3videoengine(self):
        """D-04/D-06: transport + frame_validator injection points forward to
        the wrapped H3VideoEngine."""
        called = {}
        captured_validator = lambda clip, expected: (True, "ok")

        # Patch H3VideoEngine in the video_engine module so we can capture
        # what H3PreviewEngine.__init__ passes through.
        import plugins.kais_aigc.video_engine as ve_mod

        real_h3 = ve_mod.H3VideoEngine

        class _CapturingH3(real_h3):
            def __init__(self, **kwargs):
                called.update(kwargs)
                # Don't call super().__init__ — avoid real httpx.Client setup.
                self._captured = kwargs

        ve_mod.H3VideoEngine = _CapturingH3
        try:
            H3PreviewEngine(
                base_url="http://h3-test",
                timeout=42.0,
                transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
                frame_validator=captured_validator,
            )
        finally:
            ve_mod.H3VideoEngine = real_h3
        assert called["base_url"] == "http://h3-test"
        assert called["timeout"] == 42.0
        assert called["frame_validator"] is captured_validator
        assert isinstance(called["transport"], httpx.MockTransport)


# ---------------------------------------------------------------------------
# Phase 40 WR-05 fix — path-traversal validation helper
# ---------------------------------------------------------------------------
# ``_validate_path_under_root`` is a standalone helper retained in
# preview_engine.py for production opt-in path validation. It is not used by
# H3PreviewEngine (which delegates path handling to H3VideoEngine), but the
# helper is kept for callers that wire explicit allow-lists. These tests pin
# its contract.


class TestPathTraversalValidation:
    """Phase 40 WR-05 — ``_validate_path_under_root`` rejects escaping paths."""

    def test_no_roots_configured_accepts_all_paths(self):
        """Default behavior (no allowed_path_roots) = pass-through."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        # Any path is accepted when no roots are configured.
        assert _validate_path_under_root("/etc/passwd", None) == "/etc/passwd"
        assert _validate_path_under_root("../../etc/passwd", []) == "../../etc/passwd"
        assert _validate_path_under_root("/anything", None) == "/anything"

    def test_none_path_returns_none(self):
        """``None`` input returns ``None`` (missing-input degrade path)."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        assert _validate_path_under_root(None, ["/workdir"]) is None

    def test_path_under_root_accepted(self):
        """A path resolving under an allowed root is accepted unchanged."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        # /tmp/kf/x.png is under /tmp/kf.
        result = _validate_path_under_root(
            "/tmp/kf/x.png", ["/tmp/kf"], field_name="kf",
        )
        assert result == "/tmp/kf/x.png"

    def test_path_under_one_of_multiple_roots_accepted(self):
        """Path can match any one of the configured roots."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        result = _validate_path_under_root(
            "/voice/s1.wav", ["/tmp/kf", "/voice"], field_name="vc",
        )
        assert result == "/voice/s1.wav"

    def test_path_outside_all_roots_rejected(self):
        """A path resolving outside all roots raises ValueError."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        with pytest.raises(ValueError, match="path traversal rejected"):
            _validate_path_under_root(
                "/etc/passwd", ["/tmp/kf", "/voice"], field_name="kf",
            )

    def test_dotdot_traversal_outside_root_rejected(self):
        """``../../etc/passwd`` from inside an allowed root escapes and is rejected."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        with pytest.raises(ValueError, match="path traversal rejected"):
            _validate_path_under_root(
                "/tmp/kf/../../etc/passwd", ["/tmp/kf"], field_name="kf",
            )

    def test_path_equal_to_root_accepted(self):
        """The root directory itself is "under" itself (boundary case)."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        result = _validate_path_under_root(
            "/tmp/kf", ["/tmp/kf"], field_name="kf",
        )
        assert result == "/tmp/kf"

    def test_error_message_mentions_field_name(self):
        """The ValueError message includes the field_name for debugging."""
        from plugins.kais_aigc.preview_engine import _validate_path_under_root

        with pytest.raises(ValueError, match="keyframe_image_path"):
            _validate_path_under_root(
                "/etc/passwd", ["/tmp/kf"], field_name="keyframe_image_path",
            )


# ---------------------------------------------------------------------------
# Phase 40 CR-02 fix — context-manager protocol on the ABC + H3 delegation
# ---------------------------------------------------------------------------
# H3PreviewEngine overrides close()/__enter__/__exit__ to delegate to its
# wrapped H3VideoEngine (closing the httpx.Client). The P11a
# ``with select_engine() as engine:`` block depends on this.


class TestPreviewEngineContextManager:
    """Every PreviewEngine supports ``with`` so p11a can unconditionally enter
    the context manager and release engine resources."""

    def test_abc_provides_noop_close_default(self):
        """``PreviewEngine.close`` is a no-op default overridable by subclasses.

        H3PreviewEngine overrides it to delegate; we verify the ABC default
        path via a minimal anonymous subclass.
        """

        class _NoopChild(PreviewEngine):
            def generate(self, **kwargs):
                return {}

        engine = _NoopChild()
        engine.close()  # inherited ABC no-op; should not raise

    def test_h3_engine_close_delegates_to_wrapped_h3videoengine(self):
        """H3PreviewEngine.close() closes the wrapped H3VideoEngine."""
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        assert fake.closed is False
        engine.close()
        assert fake.closed is True

    def test_h3_engine_context_manager_closes_on_normal_exit(self):
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        with engine as ctx:
            assert ctx is engine
            assert fake.closed is False
        assert fake.closed is True

    def test_h3_engine_context_manager_closes_on_exception(self):
        engine = H3PreviewEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        fake = _FakeH3VideoEngine()
        engine._h3 = fake
        with pytest.raises(RuntimeError, match="boom"):
            with engine:
                raise RuntimeError("boom")
        # __exit__ runs on exception too — wrapped engine must be closed.
        assert fake.closed is True
