"""gates — Phase 40-01 redline detector subpackage.

Houses the 3 pure-stdlib redline detectors (R1 / R3 / R4) and the
``DETECTOR_REGISTRY`` mapping gate_id -> detector function.

The registry is the read-side surface that Plan 02's ``runner_hooks``
adapter imports to dispatch an auto-detect path for any gate_id
prefixed ``redline_``. This package is intentionally self-contained:
it does NOT import ``gate.py`` / ``gate_config.py`` / ``gates.yaml``
(frozen Phase 34 surface, owned by Plan 02). Detectors receive a
``payload: dict`` and emit ``(decision, suggested_action)`` — that is
the entire contract.

RED phase (Task 1): DETECTOR_REGISTRY is declared but EMPTY. The 3
detector modules ship as NotImplementedError stubs. Plan 02 Task 2 +
this plan's Task 3 populate the registry once detectors land.
"""

from __future__ import annotations

from typing import Dict

from plugins.review_gates.gates import types
from plugins.review_gates.gates.types import DetectorFn, DetectorResult

# RED phase: empty registry. Task 3 (REFACTOR) populates this with all 3
# detectors keyed by their GATE_ID. Declaring the empty surface here keeps
# the import path stable across phases — Plan 02 imports
# `from plugins.review_gates.gates import DETECTOR_REGISTRY` and can rely on
# the symbol existing today.
DETECTOR_REGISTRY: Dict[str, DetectorFn] = {}

__all__ = [
    "DETECTOR_REGISTRY",
    "DetectorFn",
    "DetectorResult",
    "types",
]
