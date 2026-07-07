"""Seed fixture: 100-record in-memory store (Phase 54 plan 02 Task 2).

Builds a ``FakeBackend`` pre-populated with 100 synthetic memory records
belonging to a single agent (``ag1``). Used by the latency benchmark
script as the "small, baseline" run per ``05-POC-PLAN.md §4.2`` task (c).

This module is a peer of ``seed_500_records.py`` / ``seed_1000_records.py``
— they share a deterministic generation contract (same content pattern,
same agent_id, only the count differs) so the 100→500→1000 progression
exposes pure scale effects on retrieval latency.

The record generator is deterministic: NO network, NO LLM, NO randomness.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Fixture dir is not a valid Python package name (parent ``v11-latency-bench``
# has hyphens). We sys.path-inject the parent test dir so we can import
# the FakeBackend from conftest.py.
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from conftest import FakeBackend  # noqa: E402

#: Total record count this fixture preloads.
RECORD_COUNT: int = 100

#: Agent ID the records belong to. Single-agent so the scoped filter
#: exercises the realistic "all hits match" path the latency SLO targets.
AGENT_ID: str = "ag1"


def build_fixture_backend() -> FakeBackend:
    """Return a ``FakeBackend`` pre-loaded with 100 synthetic records.

    Records follow the deterministic pattern:
        "memory record {i} for agent ag1: <deterministic content>"

    so the benchmark's query ("benchmark query") does not bias the
    result by matching some records but not others — all 100 are uniform.
    """
    backend = FakeBackend()
    for i in range(RECORD_COUNT):
        backend.add(
            content=f"memory record {i} for agent {AGENT_ID}: deterministic content #{i}",
            agent_id=AGENT_ID,
            scope="global",
            confidence=0.5,
        )
    assert len(backend) == RECORD_COUNT, (
        f"fixture seed_100_records expected {RECORD_COUNT} records, got {len(backend)}"
    )
    return backend
