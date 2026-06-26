"""redline_no_cold_open — Phase 40-01 R3 detector (RED stub).

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

D-34-01 extended: pure stdlib only (typing).
"""

from __future__ import annotations

from plugins.review_gates.gates.types import DetectorResult

GATE_ID = "redline_no_cold_open"
REDLINE_REF = "creative-redlines.md §R3"


def detect(payload: dict) -> DetectorResult:  # noqa: ARG001 - stub signature stable
    """RED stub — raises NotImplementedError until Task 2 GREEN phase."""
    raise NotImplementedError("RED — Task 2 implements R3 no-cold-open detect()")


__all__ = ["GATE_ID", "REDLINE_REF", "detect"]
