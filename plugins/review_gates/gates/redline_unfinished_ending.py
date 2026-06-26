"""redline_unfinished_ending — Phase 40-01 R4 detector (RED stub).

Operationalizes creative-redlines.md §R4 (Unresolved Ending):

    最后 3 秒(竖屏)/ 最后 10 秒(横屏)必须释放新钩子,禁止
    大团圆。具体:最后窗口必须引入一个新的 open question(悬念 /
    反转 / 新信息),不可出现冲突闭合 / 情绪舒缓 / "未完待续"
    静止字幕。

    English: "the final beat must release a new hook, not a tidy
    closure. The last beat must NOT be labeled resolution / closure /
    epilogue — it must seed an open question (cliffhanger / twist /
    new information) to drive the next-episode play."

Detection signal: read ``beats[-1].label``; if it is one of
``{"resolution", "closure", "epilogue"}``, emit ``("reject",
"formula:open-question-cliffhanger")``. Else ``("approve", None)``.

suggested_action rationale: ``formula:open-question-cliffhanger``
references the Phase 39 formula_library entry that instructs the
screenplay + editor + hook_retention experts to replace any closing
beat with an open-question seed (e.g. phone rings mid-hug, new
character name on screen, unanswered visual cue).

D-34-01 extended: pure stdlib only (typing).
"""

from __future__ import annotations

from plugins.review_gates.gates.types import DetectorResult

GATE_ID = "redline_unfinished_ending"
REDLINE_REF = "creative-redlines.md §R4"


def detect(payload: dict) -> DetectorResult:  # noqa: ARG001 - stub signature stable
    """RED stub — raises NotImplementedError until Task 2 GREEN phase."""
    raise NotImplementedError("RED — Task 2 implements R4 unfinished-ending detect()")


__all__ = ["GATE_ID", "REDLINE_REF", "detect"]
