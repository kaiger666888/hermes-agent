"""Phase registry — maps phase_id to module + depends_on graph.

Phase 35-03 registered p01_hook_topic, p02_outline, p03_script_audit — the
vertical slice. Phase 36-05 (this commit) appends p04..p13, completing the
full V8.6 13-phase DAG (linear chain — parallelism is intra-phase shot-level
in p11 only, plumbed via ``RunnerConfig.parallel_shots``).

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
# Phase 36 (36-01..36-04): p04..p13 — full V8.6 DAG.
from . import p04_character_design as p04  # noqa: F401
from . import p05_pain_discovery as p05  # noqa: F401
from . import p06_spatio_temporal_script as p06  # noqa: F401
from . import p07_scene_generation as p07  # noqa: F401
from . import p08_scene_selection as p08  # noqa: F401
from . import p09_shot_breakdown as p09  # noqa: F401
from . import p10_voice as p10  # noqa: F401
from . import p11_video_render as p11  # noqa: F401
from . import p12_composition as p12  # noqa: F401
from . import p13_delivery as p13  # noqa: F401

# Canonical aliases — expose the modules under their long names too, so
# callers can ``from pipeline.phases import p01_hook_topic``.
p01_hook_topic = p01
p02_outline = p02
p03_script_audit = p03
p04_character_design = p04
p05_pain_discovery = p05
p06_spatio_temporal_script = p06
p07_scene_generation = p07
p08_scene_selection = p08
p09_shot_breakdown = p09
p10_voice = p10
p11_video_render = p11
p12_composition = p12
p13_delivery = p13

# Linear DAG (no branching): each phase depends on the previous one.
# Intra-phase shot-level parallelism lives in p11 only (D-36-08).
PHASE_REGISTRY: list[dict] = [
    {"id": "p01_hook_topic",           "module": p01, "depends_on": []},
    {"id": "p02_outline",              "module": p02, "depends_on": ["p01_hook_topic"]},
    {"id": "p03_script_audit",         "module": p03, "depends_on": ["p02_outline"]},
    {"id": "p04_character_design",     "module": p04, "depends_on": ["p03_script_audit"]},
    {"id": "p05_pain_discovery",       "module": p05, "depends_on": ["p04_character_design"]},
    {"id": "p06_spatio_temporal_script", "module": p06, "depends_on": ["p05_pain_discovery"]},
    {"id": "p07_scene_generation",     "module": p07, "depends_on": ["p06_spatio_temporal_script"]},
    {"id": "p08_scene_selection",      "module": p08, "depends_on": ["p07_scene_generation"]},
    {"id": "p09_shot_breakdown",       "module": p09, "depends_on": ["p08_scene_selection"]},
    {"id": "p10_voice",                "module": p10, "depends_on": ["p09_shot_breakdown"]},
    {"id": "p11_video_render",         "module": p11, "depends_on": ["p10_voice"]},
    {"id": "p12_composition",          "module": p12, "depends_on": ["p11_video_render"]},
    {"id": "p13_delivery",             "module": p13, "depends_on": ["p12_composition"]},
]

__all__ = [
    "PHASE_REGISTRY",
    "p01_hook_topic",
    "p02_outline",
    "p03_script_audit",
    "p04_character_design",
    "p05_pain_discovery",
    "p06_spatio_temporal_script",
    "p07_scene_generation",
    "p08_scene_selection",
    "p09_shot_breakdown",
    "p10_voice",
    "p11_video_render",
    "p12_composition",
    "p13_delivery",
]
