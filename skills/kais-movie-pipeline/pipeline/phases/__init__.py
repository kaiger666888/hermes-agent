"""Phase registry — maps phase_id to run() function + metadata.

Phase 35-02 (this commit): stub registry ``[]`` so runner.py can import
``PHASE_REGISTRY`` for its iteration / checkpoint tests (35-02 tests inject
fakes via ``importlib.reload`` or direct list mutation, since the registry is
a mutable module-level list).

Phase 35-03 (Wave 2): appends p01_hook_topic, p02_outline, p03_script_audit
entries. Each entry shape::

    {
        "id":         "p01_hook_topic",
        "module":     <module with run()>,
        "depends_on": [...],
        "gate":       <gate_id or None>,
    }

Phase 36: appends p04..p13.
"""

from __future__ import annotations

# Empty stub — populated by Phase 35-03 (Wave 2). runner.py iterates this list;
# tests mutate it directly (``PHASE_REGISTRY.append({...})``) before calling
# ``run_episode``.
PHASE_REGISTRY: list[dict] = []

__all__ = ["PHASE_REGISTRY"]
