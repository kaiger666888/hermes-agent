"""TDD tests for the PreviewEngine strategy pattern (Plan 40-02).

Three test classes track the three plan tasks:

- ``TestPreviewEngineABC`` (Task 1): ABC shape, ``PreviewEngineError``,
  ``select_engine()`` factory dispatch, and the WARNING #7 stub-NotImplementedError
  boundary check at Task 1 -> Task 2/3.
- ``TestSlideshowEngine`` (Task 2): FFmpeg subprocess engine + degrade paths.
- ``TestLTXVideoEngine`` (Task 3): mocked httpx POST + D-09 degrade contract.

WARNING #7 lifecycle:
- Task 1 leaves ``SlideshowEngine`` + ``LTXVideoEngine`` as stubs whose
  ``generate()`` raises ``NotImplementedError``. Test 9 in
  ``TestPreviewEngineABC`` asserts this at the Task 1 -> 2/3 boundary.
- Task 2 expands ``SlideshowEngine``; Test 9 is adjusted to assert only
  ``LTXVideoEngine.generate()`` raises ``NotImplementedError``.
- Task 3 expands ``LTXVideoEngine``; Test 9 is removed (both stubs gone).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure hermes-agent root is importable so ``plugins.kais_aigc.*`` resolves.
HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.preview_engine import (  # noqa: E402
    LTXVideoEngine,
    PreviewEngine,
    PreviewEngineError,
    SlideshowEngine,
    select_engine,
)


class TestPreviewEngineABC:
    """Task 1: ABC shape, error class, factory dispatch, stub boundary."""

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

    def test_select_engine_default_returns_slideshow(self, monkeypatch):
        # Simulate KAIS_PREVIEW_ENGINE unset.
        monkeypatch.delenv("KAIS_PREVIEW_ENGINE", raising=False)
        engine = select_engine()
        assert isinstance(engine, SlideshowEngine)

    def test_select_engine_env_ltx_returns_ltx_video(self):
        engine = select_engine(env="ltx")
        assert isinstance(engine, LTXVideoEngine)

    def test_select_engine_env_slideshow_returns_slideshow(self):
        engine = select_engine(env="slideshow")
        assert isinstance(engine, SlideshowEngine)

    def test_select_engine_unknown_env_falls_back_to_slideshow_with_warn(
        self, caplog
    ):
        import logging

        with caplog.at_level(logging.WARNING, logger="plugins.kais_aigc.preview_engine"):
            engine = select_engine(env="totally-bogus-value")
        assert isinstance(engine, SlideshowEngine)
        # WARNING log must mention the unknown value (T-40-09 mitigation).
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "totally-bogus-value" in joined
        assert "slideshow" in joined.lower()

    def test_select_engine_reads_env_at_call_time_not_import_time(self, monkeypatch):
        # First call: env unset -> slideshow.
        monkeypatch.delenv("KAIS_PREVIEW_ENGINE", raising=False)
        first = select_engine()
        assert isinstance(first, SlideshowEngine)
        # Set env to ltx between calls; second call must reflect the new value.
        monkeypatch.setenv("KAIS_PREVIEW_ENGINE", "ltx")
        second = select_engine()
        assert isinstance(second, LTXVideoEngine)

    def test_stub_subclasses_raise_not_implemented_at_task_1_boundary(self):
        """WARNING #7 fix: validates that Task 1 SlideshowEngine +
        LTXVideoEngine stubs raise NotImplementedError on generate() before
        Tasks 2/3 expand them. This test is REMOVED after Task 3 (both
        stubs gone). Lifecycle documented in module docstring."""
        slideshow = select_engine(env="slideshow")
        with pytest.raises(NotImplementedError):
            slideshow.generate(
                shot_id="s1",
                prompt="x",
                structure_delta={},
                keyframe_image_path="/tmp/k.png",
                voice_clip_path="/tmp/v.wav",
                output_path="/tmp/o.mp4",
            )
        ltx = select_engine(env="ltx")
        with pytest.raises(NotImplementedError):
            ltx.generate(shot_id="s1", prompt="x", structure_delta={})
