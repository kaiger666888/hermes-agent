"""redline_unfinished_ending — Phase 40-01 R4 detector.

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

D-34-01 extended: pure stdlib only (typing + sibling gates.types).
"""

from __future__ import annotations

from plugins.review_gates.gates.types import DetectorResult, reject_action

GATE_ID = "redline_unfinished_ending"
REDLINE_REF = "creative-redlines.md §R4"

# R4 formula_id — Phase 39 formula_library read-side lookup key.
# Instructs screenplay + editor + hook_retention to replace the closing
# beat with an open-question seed (cliffhanger / twist / new info).
_FORMULA_ID = "open-question-cliffhanger"

# R4 violation set: last-beat labels that constitute tidy closure
# (no open question). Any other label (open_question / cliffhanger /
# active_conflict / ...) is R4-compliant.
_VIOLATION_LABELS = frozenset({"resolution", "closure", "epilogue"})


def detect(payload: dict) -> DetectorResult:
    """R4 unresolved-ending detector.

    Reads ``payload["beats"][-1]["label"]``; if it is in
    ``_VIOLATION_LABELS``, returns ``("reject",
    "formula:open-question-cliffhanger")``. Otherwise ``("approve",
    None)``.

    T-40-01 mitigation: defensive ``.get()`` access — missing ``beats``
    key, empty beats list, or a last beat missing ``label`` all fall
    through to ``("approve", None)``. No KeyError ever raised.
    """
    beats = payload.get("beats") or []
    if not beats:
        return ("approve", None)

    last_beat = beats[-1]
    if not isinstance(last_beat, dict):
        return ("approve", None)

    last_label = last_beat.get("label")
    if last_label in _VIOLATION_LABELS:
        return ("reject", reject_action(_FORMULA_ID))

    return ("approve", None)


__all__ = ["GATE_ID", "REDLINE_REF", "detect"]
