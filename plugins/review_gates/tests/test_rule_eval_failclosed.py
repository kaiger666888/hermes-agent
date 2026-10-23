"""test_rule_eval_failclosed.py — FIX-3 (2026-10-12) 规则求值异常 fail-closed.

历史行为：``evaluate_gate`` 单条规则求值异常 → fail-open 跳过（"该规则没投
票"）——OR 语义下一条异常规则可能把 would-be block 变 pass（infra/求值错误
静默变成放行）。与 image-gate 聚合层 fail-closed 方向相反，同根：没有第三态。

新行为：规则求值异常 ≠ 数据缺失（后者仍是 skip 语义）——异常规则视作
fired (blocking) 并记入返回结构新增的 ``rule_errors`` 列表（含 rule_index 与
异常文本）。宁可误 block（人工放行）不可静默放行。既有调用方零破坏：纯加键。

纯函数设计：测试不 mock 求值器，用真实可复现的异常路径（YAML 误配导致的
TypeError）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.review_gates.evaluate_gate import evaluate_gate  # noqa: E402


def _bp(rules: list[dict]) -> dict:
    return {
        "auto_evaluate": True,
        "rollback_target_default": "p11b_final_render",
        "rules": rules,
    }


class TestRuleEvalFailClosed:
    def test_raising_rule_blocks_with_rule_error(self):
        """规则求值抛 TypeError（threshold 误配为 str）→ verdict=block +
        rule_errors 非空。"""
        bp = _bp([
            # 50 > "3" → TypeError（真实数据驱动，非 mock）
            {"type": "critical_count", "field": "criticals",
             "operator": "gt", "threshold": "3"},
        ])
        result = evaluate_gate(bp, {"criticals": 50}, phase_id="p14_quality_audit")

        assert result["block"] is True, (
            "规则异常必须 fail-closed（视作 fired），不得静默跳过"
        )
        assert len(result["rule_errors"]) == 1
        err = result["rule_errors"][0]
        assert err["rule_index"] == 0
        assert err["rule_type"] == "critical_count"
        assert "TypeError" in err["error"] or "not supported" in err["error"]
        # 触发条目可辨识（fail-closed 原因写进 reason）
        assert result["triggered_rules"], "异常规则必须进 triggered_rules"
        assert "fail-closed" in result["triggered_rules"][0]["reason"]

    def test_raising_rule_beats_missing_data_semantics(self):
        """字段存在但 threshold 误配 → 比较处 TypeError → fail-closed block。
        （字段真缺失仍走 skip——见 test_missing_data_still_skips_not_blocks。）"""
        bp = _bp([
            {"type": "critical_count", "field": "criticals",
             "operator": "gt", "threshold": "oops-not-a-number"},
        ])
        result = evaluate_gate(bp, {"criticals": 2}, phase_id="pX")
        assert result["block"] is True
        assert result["rule_errors"]

    def test_mixed_rules_or_semantics_preserved(self):
        """一条异常 + 一条正常 pass → 仍 block（异常规则 fired）；正常规则
        照常计入 rules_evaluated。"""
        bp = _bp([
            {"type": "critical_count", "field": "criticals",
             "operator": "gt", "threshold": "bad"},
            {"type": "score_floor", "field": "score", "min": 60},
        ])
        result = evaluate_gate(bp, {"criticals": 0, "score": 88})

        assert result["block"] is True
        assert len(result["rule_errors"]) == 1
        assert result["rule_errors"][0]["rule_index"] == 0
        assert result["rules_evaluated"] == 1  # score_floor 正常求值
        assert result["rules_skipped"] == 1  # 异常规则计入 skipped（不变式）

    def test_healthy_run_has_empty_rule_errors(self):
        """无异常 → rule_errors == []（形状统一，调用方零破坏）。"""
        bp = _bp([
            {"type": "score_floor", "field": "score", "min": 60},
        ])
        result = evaluate_gate(bp, {"score": 88})
        assert result["block"] is False
        assert result["rule_errors"] == []

    def test_missing_data_still_skips_not_blocks(self):
        """FIX-3 边界不变式：数据缺失（fired=None）仍是 skip 语义，不误伤
        —— fail-closed 只针对「求值异常」，不针对「数据缺失」。"""
        bp = _bp([
            {"type": "score_floor", "field": "no_such_field", "min": 60},
        ])
        result = evaluate_gate(bp, {})
        assert result["block"] is False
        assert result["rules_skipped"] == 1
        assert result["rule_errors"] == []

    def test_non_dict_rule_entry_fail_closed(self):
        """rules 列表里混入非 dict 条目 → AttributeError → fail-closed。"""
        bp = _bp(["not-a-dict-rule"])  # type: ignore[list-item]
        result = evaluate_gate(bp, {})
        assert result["block"] is True
        assert result["rule_errors"][0]["rule_type"] == "non_dict_rule"

    @pytest.mark.parametrize("bad_policies", ["not a dict", None, 123])
    def test_non_dict_policies_shape_consistent(self, bad_policies):
        """non-dict blocking_policies 早退路径也带 rule_errors 键（形状统一）。"""
        result = evaluate_gate(bad_policies, {})  # type: ignore[arg-type]
        assert result["block"] is False
        assert result["rule_errors"] == []
