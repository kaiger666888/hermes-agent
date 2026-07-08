"""Phase 67 observability package.

Wave 0 (Plan 67-01) ships the shared ring-buffer primitive and the OBSRV-01
agent-registry collector. Plans 67-02/67-03 add the round-table and
memory-backend collectors, which will append their re-exports here.

Re-export surface (Wave 0, added by Task 2):
    get_agent_registry_metrics  -- from agent_registry_metrics.py

Re-export surface (future, Plans 02/03):
    get_round_table_metrics     -- from round_table_metrics.py
    get_memory_backend_metrics  -- from memory_backend_metrics.py
"""

from __future__ import annotations

# Intentionally empty for Task 1. Task 2 of Plan 67-01 adds:
#     from agent.observability.agent_registry_metrics import get_agent_registry_metrics
# Plans 67-02/67-03 append their own re-exports without rewriting this block.
