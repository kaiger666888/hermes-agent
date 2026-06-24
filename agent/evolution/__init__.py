"""Phase 31 Knowledge Evolution Pipeline (EVOL-01/03/04/05).

Operator-invoked only — NOT imported by Hermes runtime (run_agent.py,
agent/conversation_loop.py, agent/curator.py, cli.py, gateway/). The only
intended consumer is the CLI handler in hermes_cli/feedback.py (Plan 02),
which the operator invokes via ``hermes feedback evolve / approve / reject``.

Single-process assumption (see RESEARCH Pitfall 5): JSONL queue writes
are not cross-process atomic. v6 is single-operator; concurrent patch
application is out of scope.

Modules:
  - insights: LLM aggregation of feedback into structured insights (EVOL-01)
  - diff_generator: stdlib difflib additive diff (EVOL-02 placeholder)
  - queue: JSONL patch review queue lifecycle (EVOL-03)
  - apply: atomic git apply + commit + revert transaction (EVOL-05)
"""

from __future__ import annotations

from agent.evolution.apply import (
    ApplyError,
    ApplyResult,
    apply_patch_transaction,
    build_commit_message,
    revert_files,
    verify_additive_only,
    verify_found08_byte_intact,
)
from agent.evolution.diff_generator import generate_additive_diff
from agent.evolution.insights import (
    AGGREGATION_SYSTEM_PROMPT,
    AggregationError,
    InsightRecord,
    aggregate_feedback,
    build_aggregation_user_prompt,
    make_aggregation_client,
)
from agent.evolution.queue import (
    FAILED_GATE_FILENAME,
    PROTECTED_REFS,
    PatchRecord,
    append_failed_gate,
    append_patch,
    move_patch,
    read_queue,
)

__all__ = [
    # insights (EVOL-01)
    "AGGREGATION_SYSTEM_PROMPT",
    "AggregationError",
    "InsightRecord",
    "aggregate_feedback",
    "build_aggregation_user_prompt",
    "make_aggregation_client",
    # diff_generator (EVOL-02 placeholder)
    "generate_additive_diff",
    # queue (EVOL-03)
    "FAILED_GATE_FILENAME",
    "PROTECTED_REFS",
    "PatchRecord",
    "append_failed_gate",
    "append_patch",
    "move_patch",
    "read_queue",
    # apply (EVOL-05)
    "ApplyError",
    "ApplyResult",
    "apply_patch_transaction",
    "build_commit_message",
    "revert_files",
    "verify_additive_only",
    "verify_found08_byte_intact",
]
