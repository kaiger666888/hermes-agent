"""Regression tests for canvas cross-phase reference topology.

These lock in the 2026-07-27 canvas-topology fix: ``_link_asset_level_references``
+ ``_resolve_ref_to_node`` now draw ``dataType="reference"`` edges across
phases even when the upstream phase outputs use inconsistent field naming
and ids — the exact failure mode that left ep-xiaojianghu-ep01 with 0
reference edges.

The four edges asserted here mirror the task's success criteria:
  * P04 → P09  (character_ref : pinyin slug bridge)
  * P07 → P09  (scene_ref     : ordinal fallback from shot_id)
  * P04 → P10  (character voice: speaker parsed to canonical name)
  * P09 → P10  (shot align     : shot_id resolves to P09, not P06)

A persisting in-memory fake client is used so multiple phases can be synced
in sequence and the later phases find the earlier phases' nodes — the same
shape the live ``load-v2``/``save-v2`` round-trip provides.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from plugins.kais_aigc import canvas_graph
from plugins.kais_aigc.canvas_sync import CanvasSyncSubscriber


class _PersistingFakeClient:
    """CanvasClient stand-in that persists the graph across load/save."""

    def __init__(self) -> None:
        self._project_id = 1
        self._episodes_id = 1
        self._graph: dict[str, Any] | None = None

    def load_canvas(self) -> Any:
        if self._graph is None:
            self._graph = canvas_graph.empty_graph(
                self._project_id, self._episodes_id,
            )
        return copy.deepcopy(self._graph)

    def save_canvas(self, graph: dict[str, Any]) -> Any:
        self._graph = copy.deepcopy(graph)
        return {"ok": True}

    def raw_post(self, path: str, payload: dict | None = None) -> dict:
        # Asset-registry calls (assets-registry search/create) are not exercised
        # by this topology test — return an empty dict so the subscriber's
        # _register_pipeline_asset degrades to a no-op (returns None) instead
        # of raising AttributeError. Parity with the real CanvasClient surface.
        return {}

    def close(self) -> None:  # parity with CanvasClient for test ergonomics
        pass


def _reference_links(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        l for l in graph.get("links", [])
        if isinstance(l, dict) and l.get("dataType") == "reference"
    ]


def _phase_of(graph: dict[str, Any], node_id: str) -> str:
    for n in graph.get("nodes", []):
        if isinstance(n, dict) and n.get("id") == node_id:
            pn = n.get("phaseName") or ""
            if isinstance(pn, str) and pn:
                return pn.split("_", 1)[0]
    return "?"


# ── minimal but field-accurate phase results ──────────────────────────


def _p04_result() -> dict[str, Any]:
    return {
        "phase": "p04_character_design",
        "outputs": {
            "character_bible": {
                "characters": [
                    {"name": "阿毛", "role": "protagonist",
                     "archetype": "protagonist", "age_range": "child"},
                ],
            },
            "character_assets": {
                "l1_anchors": [
                    {"name": "amao",
                     "turnaround_sheet": "assets/P04/t_amao.png",
                     "crops": {"front": "assets/P04/amao_front.png"}},
                ],
            },
        },
        "gate": None,
    }


def _p07_result() -> dict[str, Any]:
    return {
        "phase": "p07_scene_generation",
        "outputs": {
            "scene_images": [
                {"scene_id": "S01",
                 "views": {"front": "S01_front"},
                 "path": "assets/S07/"},
            ],
        },
        "gate": None,
    }


def _p09_result() -> dict[str, Any]:
    # Real shape: scene_ref=null, character_refs[].name is the PINYIN slug.
    return {
        "phase": "p09_shot_breakdown",
        "outputs": {
            "shot_list": [
                {"shot_id": "S1-01", "scene_ref": None,
                 "scene_label": "S1·林间空地·清晨",
                 "shot_type": "WS", "duration_sec": 4.0,
                 "ltx_prompt": "forest clearing dawn",
                 "character_refs": [
                     {"name": "amao",
                      "turnaround_path": "assets/P04/t_amao.png",
                      "role": "protagonist"},
                 ]},
            ],
        },
        "gate": None,
    }


def _p10_result() -> dict[str, Any]:
    # Real shape: speaker carries a parenthetical qualifier; no characterId.
    return {
        "phase": "p10_voice",
        "outputs": {
            "voice_clips": [
                {"shot_id": "S1-01", "clip_type": "narration",
                 "text": "爸爸什么都会。", "audio_path": "assets/audio/p10_voice/S1-01.wav",
                 "duration_sec": 3.0, "audio_type": "人声",
                 "engine": "Qwen3-TTS-1.7B", "emotion": "温柔",
                 "speaker": "阿毛(旁白)"},
            ],
        },
        "gate": None,
    }


@pytest.fixture()
def synced_graph():
    client = _PersistingFakeClient()
    sub = CanvasSyncSubscriber(client)
    for pid, result in (
        ("p04_character_design", _p04_result()),
        ("p07_scene_generation", _p07_result()),
        ("p09_shot_breakdown", _p09_result()),
        ("p10_voice", _p10_result()),
    ):
        sub.on_phase_complete("ep-topo", pid, result)
    return client._graph  # type: ignore[attr-defined]


class TestCanvasTopologyReferenceEdges:
    def test_reference_edges_are_drawn(self, synced_graph):
        refs = _reference_links(synced_graph)
        assert refs, "expected dataType='reference' edges, got none"

    def test_p04_to_p09_character_edge_via_pinyin_slug(self, synced_graph):
        """P09 character_refs[].name='amao' resolves to the P04 node whose
        characterSlug='amao' (characterId is the Chinese name '阿毛')."""
        refs = _reference_links(synced_graph)
        assert any(
            _phase_of(synced_graph, l["source"]) == "p04"
            and _phase_of(synced_graph, l["target"]) == "p09"
            for l in refs
        ), "no P04→P09 character_ref edge"

    def test_p07_to_p09_scene_edge_from_null_scene_ref(self, synced_graph):
        """P09 shot has scene_ref=null; the scene token is derived from
        shot_id 'S1-01' → 'S1' → P07 ordinal 0 (scene_id 'S01')."""
        refs = _reference_links(synced_graph)
        assert any(
            _phase_of(synced_graph, l["source"]) == "p07"
            and _phase_of(synced_graph, l["target"]) == "p09"
            for l in refs
        ), "no P07→P09 scene_ref edge"

    def test_p04_to_p10_voice_character_edge(self, synced_graph):
        """P10 speaker='阿毛(旁白)' is parsed to '阿毛' and linked to the P04
        node whose characterId='阿毛'."""
        refs = _reference_links(synced_graph)
        assert any(
            _phase_of(synced_graph, l["source"]) == "p04"
            and _phase_of(synced_graph, l["target"]) == "p10"
            for l in refs
        ), "no P04→P10 character voice edge"

    def test_p09_to_p10_shot_edge_not_p06(self, synced_graph):
        """shot_id 'S1-01' resolves to the P09 storyboard node, not any
        same-id node from another phase."""
        refs = _reference_links(synced_graph)
        shot_edges = [
            l for l in refs
            if _phase_of(synced_graph, l["source"]) == "p09"
            and _phase_of(synced_graph, l["target"]) == "p10"
        ]
        assert shot_edges, "no P09→P10 shot_ref edge"
        # The link id encodes ref_type=shot_ref.
        assert any(
            l.get("id", "").startswith("ref-shot_ref-") for l in shot_edges
        ), f"expected ref_type=shot_ref, got ids={[l.get('id') for l in shot_edges]}"


class TestResolveRefToNodePhaseGuard:
    """The src_prefix phase guard prevents cross-phase id collisions."""

    def test_strategy2_respects_src_prefix(self):
        sub = CanvasSyncSubscriber.__new__(CanvasSyncSubscriber)
        # Two a- nodes with colliding short ids across phases.
        all_nodes = {
            "a-S1-01": {"phaseName": "p06_spatio_temporal_script"},
            "a-shot_list-S1-01": {"phaseName": "p09_shot_breakdown"},
        }
        # Asking for p09 must skip the bare a-S1-01 (p06) and find the p09 node.
        got = CanvasSyncSubscriber._resolve_ref_to_node(
            "S1-01", "p09", all_nodes,
        )
        assert got == "a-shot_list-S1-01", (
            f"expected p09 node, got {got!r} (phase guard failed)"
        )


class TestDeriveSceneRef:
    def test_derives_from_shot_id(self):
        d = CanvasSyncSubscriber._derive_scene_ref(
            {"shot_id": "S1-01", "scene_ref": None},
        )
        assert d == "S1"

    def test_derives_from_scene_label(self):
        d = CanvasSyncSubscriber._derive_scene_ref(
            {"shot_id": None, "scene_label": "S1·林间空地"},
        )
        assert d == "S1"

    def test_ignores_scene_ref_path(self):
        """A scene_ref PATH (contains '/') is skipped to avoid the S07 dir
        prefix corrupting ordinal matching downstream."""
        d = CanvasSyncSubscriber._derive_scene_ref(
            {"shot_id": "S1-01", "scene_ref": "assets/S07/S1_front.png"},
        )
        assert d == "S1"  # from shot_id, NOT the path

    def test_returns_none_when_nothing_derivable(self):
        assert CanvasSyncSubscriber._derive_scene_ref({"shot_id": None}) is None


class TestParseSpeakerCharacter:
    @pytest.mark.parametrize("speaker,expected", [
        ("阿毛(旁白)", "阿毛"),
        ("阿毛（画外音）", "阿毛"),
        ("阿毛", "阿毛"),
        ("", None),
        (None, None),
    ])
    def test_parse(self, speaker, expected):
        assert CanvasSyncSubscriber._parse_speaker_character(speaker) == expected
