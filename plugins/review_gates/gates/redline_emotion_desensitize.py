"""redline_emotion_desensitize — Phase 40-01 R1 detector (RED stub).

Operationalizes creative-redlines.md §R1 (Emotion Desensitization):

    同类型情绪连续出现不得超过 2 次。具体:在任意 60 秒窗口内,
    连续同一 taxonomy 的情绪镜头 ≤ 2 个;第 3 个连续同类型即触发脱敏。

    English: "no more than 2 consecutive beats of the same emotion
    taxonomy within any 60s window; the 3rd consecutive same-emotion
    beat triggers desensitization."

Detection signal: walk the payload's ``beats`` list with a 3-element
sliding window; if all 3 beats in any window share the same ``emotion``
value (per-beat emotion taxonomy tag), emit ``("reject",
"formula:emotion-break-up")``. Else ``("approve", None)``.

suggested_action rationale: ``formula:emotion-break-up`` references the
Phase 39 formula_library entry that instructs the screenplay / editor
expert to break up the desensitizing run by inserting a contrasting
emotion beat (e.g. anger→anger→anger becomes anger→anger→shock).

D-34-01 extended: this module imports only stdlib (typing). No httpx /
jwt / yaml / plugins.* imports — the purity AST-walk guard in
``tests/test_redline_purity.py`` enforces this at CI time.
"""

from __future__ import annotations

from plugins.review_gates.gates.types import DetectorResult

GATE_ID = "redline_emotion_desensitize"
REDLINE_REF = "creative-redlines.md §R1"


def detect(payload: dict) -> DetectorResult:  # noqa: ARG001 - stub signature stable
    """RED stub — raises NotImplementedError until Task 2 GREEN phase."""
    raise NotImplementedError("RED — Task 2 implements R1 emotion-desensitize detect()")


__all__ = ["GATE_ID", "REDLINE_REF", "detect"]
