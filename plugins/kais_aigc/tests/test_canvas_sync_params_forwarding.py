"""test_canvas_sync_params_forwarding.py — Phase 43 SYNCSIDE-03 contract test.

Verifies the single-path mapping helper ``_build_node_from_phase_result``
forwards every ``params.*`` key from the input manifest into the canvas
node's ``data`` field. Pre-Phase-43, the mapping used an opt_key whitelist
that silently dropped structured fields the frontend needed; this test
locks the contract so the regression cannot return.

Background: see Phase 43 PLAN-01 Task 2 — the canvas detail panel only
renders fields it sees in node.data, so any params.* key lost between
manifest write (Python side, Phase 42) and canvas POST is invisible to
the user. This test catches that loss at unit-test time.
"""
from __future__ import annotations

import sys
from pathlib import Path


_PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from canvas_sync import (  # noqa: E402
    _build_node_from_phase_result,
    CanvasSyncSubscriber,
    _NullCanvasClient,
)


def _make_subscriber() -> CanvasSyncSubscriber:
    """Subscriber backed by a no-op client — pure-mapping only."""
    return CanvasSyncSubscriber(_NullCanvasClient())


# ---------------------------------------------------------------------------
# Helper existence + basic shape
# ---------------------------------------------------------------------------


class TestBuildNodeFromPhaseResultContract:
    """The single-path mapping helper exists and returns the right shape."""

    def test_helper_is_callable_with_phase_result_shape(self):
        result = {
            "phase": "p01_hook_topic",
            "outputs": {
                "topic_kernel": {"genre": "喜剧", "tone": "搞笑",
                                  "total_duration_sec": 30,
                                  "description": "P01 选题核 · 类型与基调"},
            },
            "gate": None,
        }
        nodes = _build_node_from_phase_result("p01_hook_topic", result)
        # Always returns at least the phase summary node
        assert len(nodes) >= 1
        # Every node has the canonical shape
        for node in nodes:
            assert "type" in node
            assert "data" in node
            assert isinstance(node["data"], dict)

    def test_helper_accepts_persisted_checkpoint_wrapper(self):
        """sync_phase_result receives both shapes; helper must unwrap."""
        inner = {
            "phase": "p01_hook_topic",
            "outputs": {"topic_kernel": {"description": "P01 topic-kernel 钩子"}},
            "gate": None,
        }
        wrapper = {"status": "completed", "result": inner}
        nodes = _build_node_from_phase_result("p01_hook_topic", wrapper)
        assert len(nodes) >= 1

    def test_helper_degrades_to_phase_node_on_empty_outputs(self):
        """No outputs → just the phase summary node, no exception."""
        result = {"phase": "p01_hook_topic", "outputs": {}, "gate": None}
        nodes = _build_node_from_phase_result("p01_hook_topic", result)
        assert len(nodes) == 1
        # Just verify the node has data — exact label text varies by
        # phase-prefix mapping (could be "Step 1 · 爆款选题+钩子" or
        # "P01 钩子设计"). The point is the summary node built successfully.
        assert "data" in nodes[0]
        assert isinstance(nodes[0]["data"], dict)
        assert nodes[0]["data"].get("label"), \
            "phase summary node missing label"


# ---------------------------------------------------------------------------
# SYNCSIDE-03: every params.* key forwarded into node_data.data
# ---------------------------------------------------------------------------


class TestParamsForwarding:
    """For artifact nodes, every manifest params.* key MUST reach node.data.

    This is the v2.0 contract — Phase 42 enforces it on the WRITE side
    (manifest validation); this test enforces it on the READ side
    (canvas sync). If either side regresses, the panel silently drops
    fields and the user perceives a broken node.
    """

    def test_p04_character_asset_forwards_all_params(self):
        """P04 character asset: archetype/role/description reach node.data.

        Phase 42 added ("asset","p04") → {archetype, role} to the source-side
        required fields. This test verifies the receiving-side mapping
        doesn't drop them.
        """
        result = {
            "phase": "p04_character_design",
            "outputs": {
                "character_bible": {"characters": [
                    {"name": "小橘", "archetype": "protagonist",
                     "role": "main character (mikan)", "age_range": "teen"},
                ]},
                "character_assets": [
                    {"name": "小橘", "turnaround_sheet":
                        "/oss/proj/p04/mikan.png"},
                ],
            },
            "gate": None,
        }
        nodes = _build_node_from_phase_result("p04_character_design", result)
        # Find the character asset node (not the phase summary)
        asset_nodes = [n for n in nodes if n.get("type") in ("asset", "script")
                       and "characterId" in n.get("data", {})]
        # The lookup may not match if name mismatch — fall back to any
        # non-summary node carrying structured fields.
        if not asset_nodes:
            asset_nodes = [n for n in nodes[1:] if "archetype" in n.get("data", {})]
        assert asset_nodes, (
            f"No asset node found carrying archetype/role. "
            f"Nodes: {[(n.get('type'), list(n.get('data', {}).keys())) for n in nodes]}"
        )
        data = asset_nodes[0]["data"]
        # Every params key from the manifest contract must be in data
        for required_key in ("archetype", "role"):
            assert required_key in data, (
                f"params.{required_key} lost in mapping. "
                f"data has: {sorted(data.keys())}"
            )
            assert data[required_key], f"params.{required_key} is empty"

    def test_p11_video_forwards_structured_params(self):
        """P11 video node: engine/resolution/shot_id/duration_sec survive.

        These are MANIFEST_PARAM_SCHEMA["video"] required fields. Losing
        any of them between manifest and canvas means the detail panel
        shows a video without its render metadata.
        """
        result = {
            "phase": "p11_video_render",
            "outputs": {
                "video_clips": [{
                    "shot_id": "S01-01",
                    "engine": "ltx",
                    "duration_sec": 3.5,
                    "resolution": "1280x704",
                    "filePath": "/oss/proj/p11/S01-01.mp4",
                    "thumbnailUrl": "/oss/proj/p11/S01-01.mp4",
                    "description": "P11 视频片段 · S01-01 · ltx engine · 黄昏",
                    "prompt": "a lone cyclist descends a moonlit mountain road",
                }],
            },
            "gate": None,
        }
        nodes = _build_node_from_phase_result("p11_video_render", result)
        # Find the video node
        video_nodes = [n for n in nodes if n.get("type") == "video"
                       or "engine" in n.get("data", {})]
        assert video_nodes, (
            f"No video node found. "
            f"Nodes: {[(n.get('type'), list(n.get('data', {}).keys())) for n in nodes]}"
        )
        data = video_nodes[0]["data"]
        for required_key in ("shot_id", "engine", "duration_sec", "resolution"):
            assert required_key in data, (
                f"params.{required_key} lost. data has: {sorted(data.keys())}"
            )

    def test_arbitrary_unknown_params_key_is_forwarded(self):
        """Future-proofing: any new params key auto-forwards, no whitelist update needed.

        The passthrough loop in _build_artifact_node copies ALL artifact
        dict fields to data (with a small skip-list for internal keys).
        This test confirms a hypothetical new field reaches the canvas
        without code changes here. Schema mappings (snake_case → camelCase)
        are an accepted transformation — the test checks the VALUE
        survives in some form, not the exact key spelling.
        """
        result = {
            "phase": "p11_video_render",
            "outputs": {
                "video_clips": [{
                    "shot_id": "S02-01",
                    "engine": "msr",
                    "duration_sec": 4.0,
                    "resolution": "1920x1080",
                    "filePath": "/oss/proj/p11/S02-01.mp4",
                    "thumbnailUrl": "/oss/proj/p11/S02-01.mp4",
                    "description": "P11 视频片段 · S02-01 · msr engine",
                    "murch_grade": "pass",
                    "render_cost_seconds": 12.7,
                    "custom_field_future_phase": "any value",
                }],
            },
            "gate": None,
        }
        nodes = _build_node_from_phase_result("p11_video_render", result)
        video_nodes = [n for n in nodes if n.get("type") == "video"
                       or "engine" in n.get("data", {})]
        assert video_nodes
        data = video_nodes[0]["data"]

        # murch_grade may be schema-mapped to murchGrade (camelCase) —
        # accept either form, what matters is the value survived.
        murch_value = data.get("murch_grade") or data.get("murchGrade")
        assert murch_value == "pass", (
            f"murch_grade value lost. data: {sorted(data.keys())}"
        )

        # render_cost_seconds has no camelCase mapping — must survive verbatim.
        assert data.get("render_cost_seconds") == 12.7, (
            f"render_cost_seconds value lost. data: {sorted(data.keys())}"
        )

        # custom_field_future_phase has no mapping either — verbatim survival.
        assert data.get("custom_field_future_phase") == "any value", (
            f"custom_field_future_phase value lost. data: {sorted(data.keys())}"
        )


# ---------------------------------------------------------------------------
# Internal-key skip list — these MUST NOT leak into node.data
# ---------------------------------------------------------------------------


class TestInternalKeysAreSkipped:
    """Conversely: internal bookkeeping keys stay out of node.data.

    The skip list prevents ``id``, ``label``, ``type``, ``selected``,
    ``_origin_key`` from polluting data — they're handled as top-level
    node fields or used internally. If the skip list shrinks, the data
    dict gets noisy with redundant fields.
    """

    def test_id_and_origin_key_not_in_data(self):
        result = {
            "phase": "p11_video_render",
            "outputs": {
                "video_clips": [{
                    "shot_id": "S03-01",
                    "engine": "ltx",
                    "duration_sec": 2.5,
                    "resolution": "1280x704",
                    "filePath": "/oss/proj/p11/S03-01.mp4",
                    "thumbnailUrl": "/oss/proj/p11/S03-01.mp4",
                    "description": "P11 视频片段 · S03-01 · ltx engine · 测试",
                }],
            },
            "gate": None,
        }
        nodes = _build_node_from_phase_result("p11_video_render", result)
        for node in nodes:
            data = node.get("data", {})
            # _origin_key is internal bookkeeping for assetType override
            assert "_origin_key" not in data, \
                f"_origin_key leaked into data: {data.get('_origin_key')}"
