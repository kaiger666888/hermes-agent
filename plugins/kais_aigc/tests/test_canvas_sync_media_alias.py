"""test_canvas_sync_media_alias.py — ``_normalize_media_fields`` alias coverage.

P11a (``pipeline/phases/p11a_preview_clips.py``) emits ``rapid_preview_clips``
records whose media field is named ``clip_path`` — a name the
``_normalize_media_fields`` alias table didn't include. Result: ``filePath``
stayed empty, ``_build_artifact_node`` degraded every preview-clip node to
``type='script'``, and the frontend StoryboardTimeline ``videoByShot`` lookup
(kind==='asset' && filePath ends .mp4) matched nothing — 31 nodes with playable
mp4 paths rendered as dead script nodes.

Regression guard: ``clip_path`` must resolve to ``filePath`` so preview clips
surface as video assets.
"""

from __future__ import annotations

from plugins.kais_aigc.canvas_sync import _normalize_media_fields


def test_normalize_media_fields_clip_path_alias(tmp_path):
    """clip_path（P11a rapid_preview_clips 字段名）必须映射到 filePath。"""
    item = {
        "shot_id": "S1_0000",
        "variant_id": "S1_0000__v1_hook_position_sec",
        "clip_path": str(tmp_path / "S1_0000__v1_hook_position_sec.mp4"),
        "engine": "h3",
    }
    out = _normalize_media_fields(dict(item))
    fp = out.get("filePath") or ""
    # 要么等于原绝对路径（已在 OSS 内），要么被转成 /oss/ URL
    assert fp == item["clip_path"] or fp.startswith("/oss/"), fp


def test_normalize_media_fields_alias_priority_unchanged(tmp_path):
    """既有 alias 优先级不受影响：显式 video_path 仍胜过后加入的 clip_path。"""
    video = tmp_path / "render.mp4"
    clip = tmp_path / "clip.mp4"
    item = {
        "video_path": str(video),
        "clip_path": str(clip),
    }
    out = _normalize_media_fields(dict(item))
    fp = out.get("filePath") or ""
    assert fp == str(video) or fp.startswith("/oss/"), fp
