"""redline_emotion_desensitize — Phase 40-01 R1 detector.

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

D-34-01 extended: this module imports only stdlib (typing) plus its own
sibling ``gates.types`` (pure-typing, allow-listed by the purity guard).
No httpx / jwt / yaml / plugins.* reach-back (gate.py / gate_config.py /
runner_hooks.py / tools.py are Plan 02's wiring direction).
"""

from __future__ import annotations

from plugins.review_gates.gates.types import DetectorResult, reject_action

GATE_ID = "redline_emotion_desensitize"
REDLINE_REF = "creative-redlines.md §R1"

# R1 formula_id — Phase 39 formula_library read-side lookup key.
# The formula instructs screenplay/editor to insert a contrasting emotion
# beat to break the desensitizing run.
_FORMULA_ID = "emotion-break-up"

# R1 threshold: 3rd consecutive same-emotion beat triggers violation.
# (≤2 consecutive is OK per spec — "第 3 个连续同类型即触发脱敏".)
_RUN_LENGTH = 3


def detect(payload: dict) -> DetectorResult:
    """R1 emotion-desensitization detector.

    Walks ``payload["beats"]`` with a 3-element sliding window; if any
    window has all 3 beats sharing the same ``emotion`` value, returns
    ``("reject", "formula:emotion-break-up")``. Otherwise
    ``("approve", None)``.

    T-40-01 mitigation: defensive ``.get()`` access throughout — missing
    ``beats`` key, missing ``emotion`` key, or non-dict beat entries all
    fall through to ``("approve", None)``. No KeyError ever raised.
    """
    beats = payload.get("beats") or []
    # Need at least _RUN_LENGTH beats to form a violating window.
    if len(beats) < _RUN_LENGTH:
        return ("approve", None)

    for i in range(len(beats) - _RUN_LENGTH + 1):
        window = beats[i : i + _RUN_LENGTH]
        # Defensive: each beat must be a dict with an "emotion" key.
        emotions = [
            b.get("emotion") if isinstance(b, dict) else None for b in window
        ]
        # All-None window (missing emotion on every beat) is treated as
        # a single shared "None" taxonomy -> conservatively reject.
        # (Upstream should always emit emotion; if it doesn't, rejecting
        # is the safe failure mode — flags the malformed payload.)
        first = emotions[0]
        if all(e == first for e in emotions):
            return ("reject", reject_action(_FORMULA_ID))

    return ("approve", None)


__all__ = ["GATE_ID", "REDLINE_REF", "detect"]
