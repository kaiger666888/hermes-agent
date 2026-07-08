"""Phase 67 observability package — operator metrics collectors.

Re-exports the 3 getter functions consumed by the ``/orchestrator/agents/status``
FastAPI endpoint (Plan 67-04) and the Phase 68 CLI/dashboard.

Re-export surface:
    get_agent_registry_metrics   -- from agent_registry_metrics.py (Plan 01)
    get_round_table_metrics      -- from round_table_metrics.py (Plan 02)
    get_memory_backend_metrics   -- from memory_backend_metrics.py (Plan 03)

Plans 67-02 and 67-03 deliberately did NOT touch this file to avoid Wave 1
sibling-overlap; Plan 67-04 (Wave 2) consolidates all 3 re-exports here so
the endpoint can do a single ``from agent.observability import ...`` statement.
"""

from __future__ import annotations

from agent.observability.agent_registry_metrics import get_agent_registry_metrics
from agent.observability.memory_backend_metrics import get_memory_backend_metrics
from agent.observability.round_table_metrics import get_round_table_metrics

__all__ = [
    "get_agent_registry_metrics",
    "get_memory_backend_metrics",
    "get_round_table_metrics",
]
