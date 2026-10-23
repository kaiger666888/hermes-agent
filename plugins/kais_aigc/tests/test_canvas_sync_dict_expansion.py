"""test_canvas_sync_dict_expansion.py — dict 子节点展开 + content 全文双写回归。

Background (ep-ccport-test01, 2026-08-18):
    _extract_artifacts 的子键展开只有 list / str / 纯数值 dict 三个分支，
    嵌套结构化 dict 被静默丢弃——p01 丢了 emotion_spectrum /
    platform_fit / charlie_selection / reversal_blueprint /
    creative_constraints / frame_breakdown_3sec 等 10 个字段；str 分支的
    description[:200] 截断即永久丢失全文。落选 hook 候选的 desc 白名单
    只认 5 个键，核心差异字段（visual_concept / hook_strength /
    frame_breakdown_3sec）拼不进去。前端 script 结构化字段表读
    totalDuration 而生成映射表的 python_key 是 total_duration（identity
    占位），永远 miss。

四个修复的回归契约：
    1. dict 子键 → 1 个子节点（description 摘要 + data.content 全文 +
       标量叶子透传），节点数有上界（不随嵌套深度爆炸）。
    2. str 子键 → description 截断 200，data.content 保留全文。
    3. 候选变体 desc 白名单扩容 + extra_data 结构化透传。
    4. topic_kernel 摘要双写 camelCase totalDuration。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc import canvas_sync  # noqa: E402


class _ClientStub:
    def __init__(self, project_id=101, episodes_id=202):
        self._project_id = project_id
        self._episodes_id = episodes_id


def _make_subscriber():
    sub = canvas_sync.CanvasSyncSubscriber.__new__(
        canvas_sync.CanvasSyncSubscriber
    )
    sub._client = _ClientStub()
    return sub


def _arts_by_id(sub, outputs: dict, phase: str = "p01_hook_topic") -> dict:
    arts = sub._extract_artifacts(phase, {"outputs": outputs})
    return {a["id"]: a for a in arts}


# ─── Fix 1: dict 子节点展开 ────────────────────────────────────────────


class TestDictChildExpansion:
    def test_mixed_dict_expands_to_child_node(self):
        """emotion_spectrum（str+int+嵌套 dict 混合）不再被静默丢弃。"""
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "topic_nucleus": "咖啡机成精了",
            "emotion_spectrum": {
                "scan_dimensions": 10,
                "constraint_priority": "喜剧/荒诞轴优先",
                "scores": {"curiosity": 9, "frustration": 9, "joy": 8},
                "top_axes_rationale": {
                    "curiosity": "咖啡机为什么故意做错",
                    "frustration": "被机器拿捏的共鸣",
                },
            },
        }})
        art = arts.get("topic_kernel-emotion_spectrum")
        assert art is not None, f"emotion_spectrum child missing: {list(arts)}"
        assert "curiosity=9" in art["description"]
        assert "喜剧/荒诞轴优先" in art["description"]
        # 标量叶子透传 node data
        assert art.get("scan_dimensions") == 10
        assert art.get("constraint_priority") == "喜剧/荒诞轴优先"

    def test_nested_numeric_map_full_dump_in_content(self):
        """嵌套数值 dict：desc 取前 N 项，content 全量。"""
        sub = _make_subscriber()
        scores = {f"axis_{i}": i for i in range(10)}
        arts = _arts_by_id(sub, {"topic_kernel": {
            "emotion_spectrum": {"scores": scores},
        }})
        art = arts["topic_kernel-emotion_spectrum"]
        assert "…" in art["description"], "desc should mark truncation"
        assert "axis_9=9" in art["content"], "content carries full map"

    def test_str_map_desc_preview_content_full(self):
        """嵌套 str map（emotion_spectrum.top_axes_rationale）：desc 首条
        预览 + 条数，content 全量；顶层 dict-of-str 则每键直接成叶子。"""
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "emotion_spectrum": {
                "top_axes_rationale": {
                    "curiosity": "咖啡机为什么故意连做三次错 drink",
                    "frustration": "被机器拿捏只能认命",
                },
            },
            # 顶层 dict-of-str：每个键就是一个标量叶子
            "top_axes_rationale": {
                "curiosity": "咖啡机为什么故意连做三次错 drink",
                "frustration": "被机器拿捏只能认命",
            },
        }})
        nested = arts["topic_kernel-emotion_spectrum"]
        assert "top_axes_rationale(2条)" in nested["description"]
        assert (
            "frustration=被机器拿捏只能认命" in nested["content"]
        )
        top = arts["topic_kernel-top_axes_rationale"]
        assert "curiosity: 咖啡机为什么" in top["description"]
        assert top.get("frustration") == "被机器拿捏只能认命"

    def test_deep_structure_count_only_desc_json_content(self):
        """段结构（frame_breakdown_3sec，每段是 str dict）：desc 出每段
        mode 预览，content JSON 全量；真正的 dict-of-dict 才降级为计数。"""
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"hook_design": {
            "hook_type": "反差钩",
            "frame_breakdown_3sec": {
                "0-1s_attention_grab": {
                    "mode": "反常规切入", "content": "LED 眨眼特写",
                },
                "1-2s_rehook": {"mode": "信息差", "content": "加班概率 99%"},
            },
        }})
        art = arts["hook_design-frame_breakdown_3sec"]
        assert art is not None, f"frame_breakdown_3sec missing: {list(arts)}"
        assert "0-1s_attention_grab" in art["description"]
        assert "反常规切入" in art["description"]
        assert "LED 眨眼特写" in art["content"]
        assert "1-2s_rehook" in art["content"]
        # 真正的三层结构（段值不是纯 str dict）→ 每段计数 + JSON 全量
        arts2 = _arts_by_id(sub, {"hook_design": {
            "frame_breakdown_3sec": {
                "seg1": {"meta": {"deep": ["a", "b"]}},
                "seg2": {"meta": {"deep": ["c"]}},
            },
        }})
        art2 = arts2["hook_design-frame_breakdown_3sec"]
        assert "seg1: 1 段" in art2["description"]
        assert "seg1" in art2["content"]

    def test_node_count_bounded_by_keys_not_depth(self):
        """dict 节点数上界 = 输出 key 数：深嵌套/大段数不放大节点数
        （list 分支按既有契约为每 item 一节点，不在本上界内）。"""
        sub = _make_subscriber()
        big = {f"seg_{i}": {"mode": "x", "content": "y" * 50} for i in range(50)}
        arts = _arts_by_id(sub, {"topic_kernel": {
            "a": big,
            "c": {"deep": {"deeper": {"deepest": big}}},
        }})
        # 2 个 dict 子键 → 恰好 2 个子节点（外加 summary），不随内容量膨胀
        dict_children = [
            k for k in arts
            if k.startswith("topic_kernel-") and k != "topic_kernel-summary"
        ]
        assert len(dict_children) == 2, dict_children

    def test_metadata_keys_filtered_from_expansion(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "_agent_name": "hook_master",
            "payload": {"_seq": 3, "note": "有效字段"},
        }})
        art = arts["topic_kernel-payload"]
        assert art is not None
        assert "_seq" not in str(art.get("description"))
        assert "_seq" not in art  # 标量透传也过滤 metadata
        assert "有效字段" in art["description"]

    def test_empty_after_filter_skips_node(self):
        """全被过滤的 dict（纯 metadata）不产空节点。"""
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "junk": {"_seq": 1, "_error": None},
        }})
        assert "topic_kernel-junk" not in arts


# ─── Fix 2: 标量截断双写 content ───────────────────────────────────────


class TestScalarContentPassthrough:
    def test_long_scalar_keeps_full_text_in_content(self):
        long_text = " Audience pain " * 60  # ~780 chars
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "audience_pain": long_text,
        }})
        art = arts["topic_kernel-audience_pain"]
        assert art["description"] == long_text[:200]
        assert art["content"] == long_text, "content must carry full text"

    def test_short_scalar_still_works(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "thrill_tier": "belonging",
        }})
        art = arts["topic_kernel-thrill_tier"]
        assert art["description"] == "belonging"


# ─── Fix 4: totalDuration camelCase 双写 ───────────────────────────────


class TestTotalDurationCamelCase:
    def test_enrich_p01_summary_double_writes_total_duration(self):
        sub = _make_subscriber()
        desc, extra = sub._enrich_p01_summary("topic_kernel", {
            "creative_constraints": {
                "genre": "comedy",
                "tone": "deadpan",
                "total_duration_sec": 25,
            },
        })
        assert extra["total_duration_sec"] == "25"
        assert extra["totalDuration"] == "25", (
            "camelCase alias required — frontend NODE_SCHEMA.script reads "
            "totalDuration; the generated map's python_key (total_duration) "
            "never matches the pipeline's total_duration_sec"
        )


# ─── Fix 5: p03 概览节点结构化字段（_build_output_summary_description 同形化）


class TestP03SummaryStructuredFields:
    """P03 script/audit 概览节点此前 _sum_extra={}——mcmahon_arc /
    total_duration_sec / genre 产出了、映射表有条目，概览节点却一个
    结构化字段都不带（前端 script 6 字段面板永远空）。"""

    def _p03_result(self) -> dict:
        # 镜像 p03 blacksmith 真实产出键位（ep-ccport-test01 日志实证）
        # 注意：_arts_by_id 会自行包 {"outputs": …}，这里只给 outputs dict。
        return {
            "script": {
                "title": "咖啡机成精了",
                "genre": "comedy",
                "total_duration_sec": 25,
                "format": "vertical 9:16",
                "mcmahon_arc": "man_in_a_hole",
                "scenes": [{"scene": 1}, {"scene": 2}],
            },
            "audit_report": {
                "total_score": 0.82,
                "predicted_completion_band": "A",
                "scores": {"drama": 0.8, "rhythm": 0.7},
                "weaknesses": [{"w": 1}],
            },
        }

    def test_script_summary_carries_structured_fields(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, self._p03_result(), phase="p03_script_audit")
        summary = arts["script-summary"]
        assert summary["genre"] == "comedy"
        assert summary["mcmahon_arc"] == "man_in_a_hole"
        assert summary["total_duration_sec"] == "25"
        assert summary["totalDuration"] == "25"
        assert summary["title"] == "咖啡机成精了"

    def test_audit_summary_carries_score_fields(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, self._p03_result(), phase="p03_script_audit")
        summary = arts["audit_report-summary"]
        assert summary["total_score"] == 0.82
        assert summary["predicted_completion_band"] == "A"

    def test_summary_description_still_meaningful(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, self._p03_result(), phase="p03_script_audit")
        desc = arts["script-summary"]["description"]
        assert "类型: comedy" in desc
        assert "25s" in desc
        assert "弧线: man_in_a_hole" in desc





# ─── Fix 6/7: p04 子项标签合成 + 道具 assetType（资管首考）───────────────


class TestP04ChildLabelAndPropType:
    """ep-ccport-test01 p04 首考暴露：服装子项兜底标签
    「角色资产.scene_costume_turnarounds 1」进画布 label 与 o_assets.name；
    l4 道具 assetType=prop 的 setdefault 嵌在「if matched:」内——道具匹配
    不到角色 bible → 恒不执行 → 咖啡杯谱系表以 character 注册。"""

    def _p04_outputs(self) -> dict:
        return {
            "character_bible": {
                "characters": [
                    {"name": "小周", "role": "protagonist (xiaozhou)",
                     "archetype": "protagonist", "age_range": "young_adult"},
                    {"name": "AI咖啡机", "role": "antagonist (coffeemachine)",
                     "archetype": "antagonist", "age_range": "adult"},
                ],
            },
            "character_assets": {
                "l1_anchors": [
                    {"name": "xiaozhou", "path": "/x/base_turnaround_xiaozhou.png"},
                    {"name": "coffeemachine", "path": "/x/base_turnaround_coffeemachine.png"},
                ],
                "scene_costume_turnarounds": [
                    {"character": "xiaozhou",
                     "scene": "chashuijian_S1-S5（茶水间·单场景）",
                     "path": "/x/l2_xiaozhou_chashuijian.png"},
                ],
                "l4_props": [
                    {"name": "咖啡杯四态谱系表",
                     "path": "/x/l4_prop_coffee_cup_states.png"},
                ],
            },
        }

    def _arts(self):
        sub = _make_subscriber()
        arts = sub._extract_artifacts(
            "p04_character_design", {"outputs": self._p04_outputs()},
            workdir="",
        )
        return {a["id"]: a for a in arts}

    def test_costume_label_synthesized_from_character_and_scene(self):
        arts = self._arts()
        art = arts["character_assets-scene_costume_turnarounds-0"]
        assert art["label"] == "xiaozhou·chashuijian_S1-S5", art["label"]

    def test_costume_label_with_costume_key(self):
        sub = _make_subscriber()
        arts = _arts_by_id(
            sub,
            {"character_assets": {"l3_costumes": [
                {"character": "xiaozhou",
                 "costume": "周一工位装（全片唯一服装）：蓝灰格子衬衫",
                 "path": "/x/l2.png"},
            ]}},
            phase="p04_character_design",
        )
        art = arts["character_assets-l3_costumes-0"]
        assert art["label"].startswith("xiaozhou·周一工位装")

    def test_path_basename_fallback_when_no_semantic_keys(self):
        assert canvas_sync.CanvasSyncSubscriber._synthesize_child_label(
            {"path": "/data/x/amao_turnaround.png"}, "资产", "sub", 0,
        ) == "amao_turnaround"

    def test_index_fallback_unchanged(self):
        assert canvas_sync.CanvasSyncSubscriber._synthesize_child_label(
            {"foo": 1}, "资产", "sub", 2,
        ) == "资产.sub 3"

    def test_prop_gets_asset_type_prop_without_bible_match(self):
        """l4 道具不匹配角色 bible，assetType 仍必须是 prop。"""
        arts = self._arts()
        prop = arts["character_assets-l4_props-0"]
        assert prop.get("assetType") == "prop", (
            f"prop assetType must not depend on bible match; got {prop}"
        )

    def test_anchor_keeps_character_type(self):
        arts = self._arts()
        anchor = arts["character_assets-l1_anchors-0"]
        assert anchor.get("assetType") == "character"
        # bible merge 仍生效
        assert anchor.get("characterId") == "小周"
        assert anchor.get("characterSlug") == "xiaozhou"

    def test_costume_matches_bible_via_character_field(self):
        """服装子项无 name——匹配键退到 character，再经 l1_anchors 的
        pinyin 别名索引归属 bible 角色；绝不能空串子串匹配错挂第一个
        bible 角色（1660 coffeemachine 服装挂小周 的根因）。真实形状：
        role 是纯枚举（无括号拼音），拼音只在 l1_anchors[].name。"""
        sub = _make_subscriber()
        arts = _arts_by_id(
            sub,
            {"character_bible": {"characters": [
                {"name": "小周", "role": "protagonist",
                 "archetype": "protagonist", "age_range": "young_adult"},
                {"name": "AI咖啡机", "role": "antagonist",
                 "archetype": "antagonist", "age_range": "adult"},
            ]},
             "character_assets": {
                 "l1_anchors": [
                     {"name": "xiaozhou", "path": "/x/base_x.png"},
                     {"name": "coffeemachine", "path": "/x/base_c.png"},
                 ],
                 "scene_costume_turnarounds": [
                     {"character": "coffeemachine", "scene": "chashuijian",
                      "path": "/x/l2_coffeemachine.png"},
                 ],
             }},
            phase="p04_character_design",
        )
        art = arts["character_assets-scene_costume_turnarounds-0"]
        assert art.get("characterId") == "AI咖啡机", (
            f"costume must match bible via anchor pinyin alias; got {art}"
        )

    def test_unkeyed_item_never_matches_first_bible_character(self):
        """无 name 无 character 的子项：bible merge 必须整体跳过。"""
        sub = _make_subscriber()
        arts = _arts_by_id(
            sub,
            {"character_bible": {"characters": [
                {"name": "小周", "role": "p (xiaozhou)", "archetype": "protagonist"},
            ]},
             "character_assets": {"l4_props": [
                 {"path": "/x/prop.png"},
             ]}},
            phase="p04_character_design",
        )
        art = arts["character_assets-l4_props-0"]
        assert "characterId" not in art, art
        assert art.get("assetType") == "prop"


# ─── Fix 8: save-v2 schema 类型 coerce（p07 style_vector 400 修复）──────


class TestSchemaTypeCoercion:
    """p07 style_vector 5D 数值（composition=0.45 float）撞上 script 类型表
    composition:string → 整图 400、管线停止。coerce 必须通用：按 SSOT
    yaml 的 per-canvas_type zod_type 表对齐，不做单字段 if。"""

    def test_scalar_number_to_string(self):
        f = canvas_sync._coerce_scalar_to_schema
        assert f(0.45, "string") == "0.45"
        assert f(25, "string") == "25"
        assert f(True, "string") == "true"
        assert f("0.45", "string") == "0.45"  # 已对齐不动

    def test_scalar_numeric_string_to_number(self):
        f = canvas_sync._coerce_scalar_to_schema
        assert f("25", "number") == 25
        assert f("0.8", "number") == 0.8
        assert f(0.8, "number") == 0.8  # 已对齐不动
        assert f("abc", "number") == "abc"  # 非数字串不硬转
        assert f("", "number") == ""

    def test_objects_left_alone(self):
        f = canvas_sync._coerce_scalar_to_schema
        assert f({"a": 1}, "string") == {"a": 1}
        assert f([1, 2], "string") == [1, 2]

    def test_graph_coercion_p07_style_vector_shape(self):
        """script 节点带 5D 数值穿透 → 已声明字段（composition/pacing）
        save 前 string 化；未声明字段（rhythm/sound 等，zod strip 不报错）
        保持原样。"""
        graph = {"nodes": [
            {"id": "a-style_vector", "type": "script", "data": {
                "label": "风格设定", "description": "…",
                "composition": 0.45, "pacing": 0.72, "rhythm": 0.62,
                "undeclared_number": 0.99,
            }},
        ]}
        canvas_sync._coerce_graph_schema_types(graph)
        d = graph["nodes"][0]["data"]
        assert d["composition"] == "0.45"
        assert d["pacing"] == "0.72"
        # rhythm/undeclared_number 未声明 → 不动（服务端 strip，无 400）
        assert d["rhythm"] == 0.62
        assert d["undeclared_number"] == 0.99

    def test_graph_coercion_number_declared_fields(self):
        """asset style_* 声明 number：数字串 → number（反向 coerce）。"""
        graph = {"nodes": [
            {"id": "a-x", "type": "asset", "data": {
                "label": "x", "assetType": "scene",
                "style_composition": "0.8", "style_sound": "1",
            }},
            {"id": "a-sb", "type": "storyboard", "data": {
                "label": "s", "shot_id": "s01", "shot_type": "CU",
                "duration_sec": "25",
            }},
        ]}
        canvas_sync._coerce_graph_schema_types(graph)
        assert graph["nodes"][0]["data"]["style_composition"] == 0.8
        assert graph["nodes"][0]["data"]["style_sound"] == 1
        assert graph["nodes"][1]["data"]["duration_sec"] == 25

    def test_structural_types_skipped(self):
        graph = {"nodes": [
            {"id": "z-p07", "type": "zone", "data": {"composition": 0.45}},
            {"id": "c-p07-v1", "type": "variant", "data": {"pacing": 0.7}},
        ]}
        canvas_sync._coerce_graph_schema_types(graph)
        assert graph["nodes"][0]["data"]["composition"] == 0.45
        assert graph["nodes"][1]["data"]["pacing"] == 0.7

    def test_type_table_loaded_from_ssot(self):
        types = canvas_sync._load_schema_field_types()
        assert types["script"]["composition"] == "string"
        assert types["script"]["totalDuration"] == "string"
        assert types["asset"]["style_composition"] == "number"
        # 基座镜像也在
        assert types["video"]["duration_sec"] == "number"


class TestP07StyleVectorEndToEnd:
    """用 ep-ccport-test01 真实 p07 result 走 on_phase_complete → 断言
    发出的 save-v2 body 里 a-style_vector.data.composition 是 string。"""

    def test_real_p07_result_saves_with_string_composition(self):
        import httpx
        from plugins.kais_aigc.canvas import CanvasClient

        state_path = (
            "/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/"
            "episodes/ep-ccport-test01/.pipeline-state.json"
        )
        try:
            state = json.load(open(state_path))
            result = state["phases"]["p07_scene_generation"][
                "result"]["result"]
        except (OSError, KeyError):
            pytest.skip("ep-ccport-test01 p07 state not present")

        bodies: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/save-v2"):
                bodies.append(json.loads(request.content))
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": {"ok": True}},
            )

        client = CanvasClient(
            base_url="http://test-canvas:10588", project_id=1, episodes_id=1,
            transport=httpx.MockTransport(handler),
        )
        sub = canvas_sync.CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-t", "p07_scene_generation", result)
        client.close()

        graph = bodies[-1]["graph"]
        nodes = {n["id"]: n for n in graph["nodes"]}
        sv = nodes.get("a-style_vector")
        assert sv is not None, f"a-style_vector missing: {list(nodes)[:20]}"
        comp = sv["data"]["composition"]
        assert isinstance(comp, str), (
            f"composition must be str for save-v2 script schema; "
            f"got {type(comp).__name__}: {comp!r}"
        )
        # 服务端 zod 表逐字段模拟校验：所有已声明字段类型必须对齐
        table = canvas_sync._load_schema_field_types()["script"]
        for k, v in sv["data"].items():
            if k in table and isinstance(v, (int, float, bool, str)):
                expected = table[k]
                got = "number" if isinstance(v, (int, float, bool)) else "string"
                assert got == expected, f"a-style_vector.{k}: {got} ≠ {expected}"

    def test_pure_mapping_entry_emits_typed_data(self):
        """纯映射入口（coordinator 重建用的 _build_node_from_phase_result，
        无 HTTP）产出的 data 也必须已类型化——源头 coerce 的契约。"""
        state_path = (
            "/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/"
            "episodes/ep-ccport-test01/.pipeline-state.json"
        )
        try:
            state = json.load(open(state_path))
            result = state["phases"]["p07_scene_generation"][
                "result"]["result"]
        except (OSError, KeyError):
            pytest.skip("ep-ccport-test01 p07 state not present")

        nodes = canvas_sync._build_node_from_phase_result(
            "p07_scene_generation", result,
        )
        assert nodes, "mapping produced no nodes"
        table_all = canvas_sync._load_schema_field_types()
        checked = 0
        for node in nodes:
            t = table_all.get(node.get("type"))
            if not t:
                continue
            for k, v in (node.get("data") or {}).items():
                if k in t and isinstance(v, (int, float, bool, str)):
                    expected = t[k]
                    got = "number" if isinstance(v, (int, float, bool)) else "string"
                    assert got == expected, (
                        f"{node.get('id')}.{k}: {got} ≠ {expected} "
                        f"(pure-mapping output must be schema-typed)"
                    )
                    checked += 1
        assert checked > 0, "test must exercise at least one declared field"


def _write_hook_candidates(workdir: Path, chosen: str = "v1") -> str:
    """Write a hook-candidates.json matching the pipeline's SSOT wrapper."""
    variants = []
    for vid, strength, vc in (
        ("v1", 0.92, "暖光茶水间，LED 屏眨眼坏笑"),
        ("v2", 0.88, "超写实咖啡机占满竖屏上三分之二"),
    ):
        variants.append({
            "variant_id": vid,
            "candidate": {
                "hook_type": "反差钩",
                "hook_intensity": 5,
                "hook_strength": strength,
                "opening_line": f"候选 {vid} 开场台词",
                "visual_concept": vc,
                "frame_breakdown_3sec": {
                    "0-1s_attention_grab": {
                        "mode": "反常规切入",
                        "content": "LED 表情屏怼脸特写",
                    },
                },
            },
            "provenance": {"k": 3},
        })
    payload = {
        "type": "hook-candidates",
        "variants": variants,
        "k": 3,
        "chosen_variant_id": chosen,
    }
    assets_dir = workdir / ".pipeline-assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    path = assets_dir / "hook-candidates.json"
    path.write_text(
        json.dumps({"value": payload}, ensure_ascii=False), encoding="utf-8",
    )
    return str(workdir)


class TestCandidateVariantEnrichment:
    def test_desc_whitelist_includes_visual_concept_and_strength(self, tmp_path):
        workdir = _write_hook_candidates(tmp_path)
        sub = _make_subscriber()
        cands = sub._load_candidate_variants("p01_hook_topic", workdir)
        assert len(cands) == 2
        by_id = {c["id"]: c for c in cands}
        v1 = by_id["variant-v1"]
        assert "visual_concept: 暖光茶水间" in v1["description"]
        assert "hook_strength: 0.92" in v1["description"]
        assert v1["selected"] is True
        assert by_id["variant-v2"]["selected"] is False

    def test_desc_includes_frame_breakdown_segment_count(self, tmp_path):
        workdir = _write_hook_candidates(tmp_path)
        sub = _make_subscriber()
        cands = sub._load_candidate_variants("p01_hook_topic", workdir)
        assert "frame_breakdown_3sec: 1 段" in cands[0]["description"]

    def test_extra_data_carries_structured_fields(self, tmp_path):
        """候选标量字段 + frame_breakdown 拍平预览透传进 entry['data']。"""
        workdir = _write_hook_candidates(tmp_path)
        sub = _make_subscriber()
        cands = sub._load_candidate_variants("p01_hook_topic", workdir)
        data = cands[0].get("data") or {}
        assert data.get("hook_type") == "反差钩"
        assert data.get("hook_strength") == 0.92
        assert data.get("visual_concept") == "暖光茶水间，LED 屏眨眼坏笑"
        # frame_breakdown 拍平：段 key → mode/content 预览
        assert "0-1s_attention_grab" in data
        assert "LED 表情屏怼脸特写" in data["0-1s_attention_grab"]
        # 嵌套 dict 本体不透传（RawDataSection 不渲染对象）
        assert "frame_breakdown_3sec" not in data

    def test_add_candidate_node_merges_extra_data(self):
        graph = {"nodes": [], "links": [], "branches": [],
                 "variantGroups": [], "meta": {}}
        node_id = canvas_sync.canvas_graph.add_candidate_node(
            graph,
            phase_id="p01_hook_topic",
            candidate_id="variant-v2",
            label="候选 v2",
            selected=False,
            description="hook_type: 反差钩",
            extra_data={
                "hook_type": "反差钩",
                "hook_strength": 0.88,
                "empty": "",
                "nested": {"x": 1},
            },
        )
        node = next(n for n in graph["nodes"] if n["id"] == node_id)
        data = node["data"]
        assert data["hook_type"] == "反差钩"
        assert data["hook_strength"] == 0.88
        assert "empty" not in data, "empty strings must not pollute data"
        assert "nested" not in data, "objects must not pass through"
        # 既有字段（label/description/tags）不被 extra_data 覆盖
        assert data["label"] == "候选 v2"


# ─── 72-01 (v3.2 F26/QVR-01): 判定数组整块保留 ─────────────────────────


class TestVerdictArrayPassthrough:
    """p10c fidelity_check / p11c per_shot 整块挂概览节点 data。

    修复前:判定数组只经 sublist 展开打散成子节点,概览节点 data 无任何
    判定字段——kap qcVerdict join(眼/耳角标)恒零命中。
    """

    def test_fidelity_check_kept_intact_on_summary(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"voice-audit": {
            "phase": "p10c",
            "findings": [],
            "fidelity_check": {
                "check": "transcription_fidelity",
                "clips": [
                    {"id": "wav1", "shot_id": "S01", "verdict": "WARN",
                     "similarity": 0.42},
                    {"id": "wav2", "shot_id": "S02", "verdict": "PASS",
                     "similarity": 0.91},
                ],
            },
        }}, phase="p10c_voice_audit")
        summary = arts.get("voice-audit-summary")
        assert summary is not None, f"summary missing: {list(arts)}"
        fid = summary.get("fidelity_check")
        assert isinstance(fid, dict), "fidelity_check 必须整块挂在概览节点"
        clips = fid.get("clips")
        assert isinstance(clips, list) and len(clips) == 2
        assert clips[0]["shot_id"] == "S01" and clips[0]["verdict"] == "WARN"

    def test_per_shot_dict_kept_intact_on_summary(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"video-qc": {
            "phase": "p11c",
            "per_shot": {
                "S01": {"shot_id": "S01", "verdict": "pass"},
                "S02": {"shot_id": "S02", "verdict": "fail"},
            },
        }}, phase="p11c_video_qc")
        summary = arts.get("video-qc-summary")
        assert summary is not None
        per_shot = summary.get("per_shot")
        assert isinstance(per_shot, dict), "per_shot(dict 形)必须整块保留"
        assert per_shot["S02"]["verdict"] == "fail"


class TestAiScoreDerivation:
    """72-02 (F28/QVR-03):审计分数 → aiScore 顶层字段(雷达图生产者)。

    形状以 ep-zhongkui-ep01 真实落盘为锚(p03 scores 0..1 / p14
    quality_audit.dimensions {score:0..100})。
    """

    def test_p03_scores_shape(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"audit_report": {
            "scores": {"drama": 1.0, "rhythm": 0.9, "character": 0.8,
                       "logic": 0.9},
            "total_score": 0.85,
        }}, phase="p03_script_audit")
        summary = arts.get("audit_report-summary")
        assert summary is not None
        ai = summary.get("aiScore")
        assert ai == {"overall": 0.85,
                      "dimensions": {"drama": 1.0, "rhythm": 0.9,
                                     "character": 0.8, "logic": 0.9}}

    def test_p14_quality_audit_nested_shape(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"quality-audit": {
            "video_meta": {},
            "quality_audit": {
                "dimensions": {
                    "hook_quality": {"score": 94, "reasoning": "…"},
                    "narrative_design": {"score": 88, "reasoning": "…"},
                    "visual_rendering": {"score": 90, "reasoning": "…"},
                },
                "overall_score": 91,
            },
        }}, phase="p14_quality_audit")
        summary = arts.get("quality-audit-summary")
        assert summary is not None
        ai = summary.get("aiScore")
        assert ai is not None
        assert ai["overall"] == 0.91
        assert ai["dimensions"]["hook_quality"] == 0.94

    def test_non_audit_slot_no_fake_score(self):
        sub = _make_subscriber()
        arts = _arts_by_id(sub, {"topic_kernel": {
            "topic_nucleus": "x", "n_candidates": 3,
        }})
        summary = arts.get("topic_kernel-summary")
        assert summary is not None
        assert "aiScore" not in summary

    def test_build_artifact_node_hoists_ai_score_top_level(self):
        sub = _make_subscriber()
        sub._child_counters = {}  # __new__ stub 不跑 __init__
        node = sub._build_artifact_node(
            "p03_script_audit",
            {"id": "audit_report", "label": "审计报告", "type": "script",
             "aiScore": {"overall": 0.8, "dimensions": {"drama": 0.9}},
             "filePath": None},
        )
        assert node.get("aiScore") == {"overall": 0.8,
                                       "dimensions": {"drama": 0.9}}
        assert "aiScore" not in node.get("data", {})
