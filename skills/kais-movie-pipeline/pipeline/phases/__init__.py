"""Phase registry — maps phase_id to module + depends_on graph.

Phase 35-03 (this commit): registers p01_hook_topic, p02_outline,
p03_script_audit — the vertical slice. Phase 36 appends p04..p13.

``runner.py`` iterates ``PHASE_REGISTRY`` in order; resume skips
already-checkpointed phases via ``_compute_start_index``.

Each entry shape::

    {
        "id":         "p01_hook_topic",
        "module":     <module with run()>,
        "depends_on": [...],
    }

(The phase module's ``GATE_ID`` constant documents its gate; the registry
does not duplicate it. ``runner.py`` looks up the gate via the module
attribute if needed in Phase 36.)
"""

from __future__ import annotations

# Import the PHASE MODULES themselves (not symbols inside them). Each
# ``p0X_<name>`` name below is bound to the module object so PHASE_REGISTRY
# can reference it via ``"module": p01`` and external callers can do
# ``from pipeline.phases import p01_hook_topic`` (the canonical module name).
from . import p01_hook_topic as p01  # noqa: F401  (re-exported below)
from . import p02_outline as p02  # noqa: F401
from . import p03_script_audit as p03  # noqa: F401

# Canonical aliases — expose the modules under their long names too, so
# callers can ``from pipeline.phases import p01_hook_topic``.
p01_hook_topic = p01
p02_outline = p02
p03_script_audit = p03

PHASE_REGISTRY: list[dict] = [
    {"id": "p01_hook_topic", "module": p01, "depends_on": []},
    {"id": "p02_outline", "module": p02, "depends_on": ["p01_hook_topic"]},
    {"id": "p03_script_audit", "module": p03, "depends_on": ["p02_outline"]},
    # Phase 36: p04..p13 with proper depends_on graph per references/pipeline-dag.md
]

__all__ = [
    "PHASE_REGISTRY",
    "p01_hook_topic",
    "p02_outline",
    "p03_script_audit",
]
