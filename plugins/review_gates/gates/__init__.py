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

Task 3 (REFACTOR): DETECTOR_REGISTRY now populated with all 3 detectors
keyed by their GATE_ID. Plan 02's runner_hooks will read this to dispatch
the auto-detect path for redline_-prefixed gate_ids.
"""

from __future__ import annotations

from typing import Dict

from plugins.review_gates.gates import types
from plugins.review_gates.gates.redline_emotion_desensitize import (
    GATE_ID as _GATE_ID_R1,
    detect as _detect_r1,
)
from plugins.review_gates.gates.redline_no_cold_open import (
    GATE_ID as _GATE_ID_R3,
    detect as _detect_r3,
)
from plugins.review_gates.gates.redline_unfinished_ending import (
    GATE_ID as _GATE_ID_R4,
    detect as _detect_r4,
)
from plugins.review_gates.gates.types import DetectorFn, DetectorResult

# Populated registry — keyed by GATE_ID. Plan 02's runner_hooks reads
# this dict to dispatch the auto-detect path for redline_-prefixed
# gate_ids. The 8 V8.6 gates do NOT appear here (they use the manual
# HIL resolution path in gate.py / tools.py); only the 3 redline gates
# are auto-detected.
DETECTOR_REGISTRY: Dict[str, DetectorFn] = {
    _GATE_ID_R1: _detect_r1,  # "redline_emotion_desensitize"
    _GATE_ID_R3: _detect_r3,  # "redline_no_cold_open"
    _GATE_ID_R4: _detect_r4,  # "redline_unfinished_ending"
}

__all__ = [
    "DETECTOR_REGISTRY",
    "DetectorFn",
    "DetectorResult",
    "types",
]
