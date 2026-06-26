"""redline_no_cold_open — Phase 40-01 R3 detector.

Operationalizes creative-redlines.md §R3 (Zero Backstory Preamble):

    切入即冲突,禁止"从前有个…"。具体:竖屏前 3 秒 / 横屏前 10 秒
    必须包含 active conflict,不可出现纯 exposition(旁白叙述背景 /
    字幕交代设定 / 静止画面)。

    English: "cold-open with conflict; no pure exposition. The first
    beat must NOT be labeled exposition / narration / setup — it must
    be an active-conflict beat to lock attention within the platform's
    skip window (3s vertical / 10s horizontal)."

Detection signal: read ``beats[0].label``; if it is one of
``{"exposition", "narration", "setup"}``, emit ``("reject",
"formula:cold-open-conflict-hook")``. Else ``("approve", None)``.

suggested_action rationale: ``formula:cold-open-conflict-hook``
references the Phase 39 formula_library entry that instructs the
screenplay + hook_retention experts to rewrite the cold open with an
in-frame active conflict (e.g. character collision, sudden noise,
visual rupture) replacing any pure-narration preamble.

D-34-01 extended: pure stdlib only (typing + sibling gates.types).
"""

from __future__ import annotations

from plugins.review_gates.gates.types import DetectorResult, reject_action

GATE_ID = "redline_no_cold_open"
REDLINE_REF = "creative-redlines.md §R3"

# R3 formula_id — Phase 39 formula_library read-side lookup key.
# Instructs screenplay + hook_retention to rewrite the cold open with
# an in-frame active conflict.
_FORMULA_ID = "cold-open-conflict-hook"

# R3 violation set: first-beat labels that constitute pure preamble
# (no active conflict). Any other label (active_conflict / cliffhanger /
# other / ...) is R3-compliant.
_VIOLATION_LABELS = frozenset({"exposition", "narration", "setup"})


def detect(payload: dict) -> DetectorResult:
    """R3 zero-backstory-preamble detector.

    Reads ``payload["beats"][0]["label"]``; if it is in
    ``_VIOLATION_LABELS``, returns ``("reject",
    "formula:cold-open-conflict-hook")``. Otherwise ``("approve",
    None)``.

    T-40-01 mitigation: defensive ``.get()`` access — missing ``beats``
    key, empty beats list, or a first beat missing ``label`` all fall
    through to ``("approve", None)``. No KeyError ever raised.
    """
    beats = payload.get("beats") or []
    if not beats:
        return ("approve", None)

    first_beat = beats[0]
    if not isinstance(first_beat, dict):
        return ("approve", None)

    first_label = first_beat.get("label")
    if first_label in _VIOLATION_LABELS:
        return ("reject", reject_action(_FORMULA_ID))

    return ("approve", None)


__all__ = ["GATE_ID", "REDLINE_REF", "detect"]
