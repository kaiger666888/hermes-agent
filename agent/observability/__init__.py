"""Phase 67 observability package.

Wave 0 (Plan 67-01) ships the shared ring-buffer primitive and the OBSRV-01
agent-registry collector. Plans 67-02/67-03 add the round-table and
memory-backend collectors, which will append their re-exports here.

Re-export surface (Wave 0):
    get_agent_registry_metrics  -- from agent_registry_metrics.py

Re-export surface (future, Plans 02/03):
    get_round_table_metrics     -- from round_table_metrics.py
    get_memory_backend_metrics  -- from memory_backend_metrics.py
"""

from __future__ import annotations

# Wave 0 re-export. Relative import so the package works under editable
# installs and wheel installs alike. Consumers (Plan 67-04 FastAPI endpoint,
# Phase 68 CLI) do ``from agent.observability import get_agent_registry_metrics``.
from agent.observability.agent_registry_metrics import get_agent_registry_metrics

__all__ = ["get_agent_registry_metrics"]
