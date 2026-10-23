"""types.py — Phase 40-01 detector result types and DetectorFn protocol.

Pure-typing module: defines the public contract that every redline detector
in ``plugins/review_gates/gates/`` must satisfy. Detectors emit a
``DetectorResult`` (decision + suggested_action) that Plan 02's
``runner_hooks`` adapter feeds into ``Gate.resolve()``.

Like ``gate.py`` (D-34-01), this module is intentionally pure stdlib —
no httpx / jwt / yaml / plugins.* imports. Detectors must remain
unit-testable in isolation without network or config coupling.
"""

from __future__ import annotations

from typing import Literal, Protocol

# Per Plan 40-01 <interfaces>: detectors emit one of three decisions.
# ("contest" is included for forward-compat with future hybrid detectors;
# the 3 redline detectors in this plan emit only approve/reject.)
Decision = Literal["approve", "reject", "contest"]

# suggested_action is either None (approve / no-op) or a string carrying
# a formula:-prefixed lookup id consumed by Phase 39 formula_library.
SuggestedAction = str | None

# DetectorResult is the canonical (decision, suggested_action) tuple shape.
DetectorResult = tuple[Decision, SuggestedAction]


def reject_action(formula_id: str) -> str:
    """Emit a formula:-prefixed suggested_action for a reject verdict.

    Centralizes the Phase 39 forward-compat convention: every reject
    action string MUST match ``^formula:[a-z][a-z0-9-]*$``. The runner
    reads the formula_id after the prefix and looks it up in the
    formula_library at runtime (read-side lookup — detectors do not
    import or invoke the library, preserving purity).

    Args:
        formula_id: lowercase hyphen-separated identifier (e.g.
            ``"emotion-break-up"``). MUST start with a lowercase ASCII
            letter and contain only ``[a-z0-9-]``.

    Returns:
        ``f"formula:{formula_id}"``.
    """
    return f"formula:{formula_id}"


class DetectorFn(Protocol):
    """Detector protocol — pure function over a clip beat-sequence payload.

    Every detector in ``plugins/review_gates/gates/`` exposes:

    - ``GATE_ID: str``       — the gates.yaml ``gate_id`` this detector
                              answers to (e.g. ``"redline_emotion_desensitize"``).
    - ``REDLINE_REF: str``   — citation of the creative-redlines.md §R<n>
                              section this detector operationalizes.
    - ``detect(payload)``    — pure function returning ``(decision,
                              suggested_action)``. MUST NOT raise on
                              malformed payloads (T-40-01 mitigation);
                              missing keys fall through to ``("approve",
                              None)``.

    Detectors MUST NOT import httpx / jwt / yaml / plugins.* (D-34-01
    extended to redline detectors). The AST-walk purity guard in
    ``tests/test_redline_purity.py`` enforces this at CI time.
    """

    GATE_ID: str
    REDLINE_REF: str

    def detect(self, payload: dict) -> DetectorResult:  # pragma: no cover - protocol
        ...


__all__ = [
    "Decision",
    "DetectorFn",
    "DetectorResult",
    "SuggestedAction",
    "reject_action",
]
