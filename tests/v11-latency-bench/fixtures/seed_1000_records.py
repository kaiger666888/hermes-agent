"""Seed fixture: 1000-record in-memory store (Phase 54 plan 02 Task 2).

Builds a ``FakeBackend`` pre-populated with 1000 synthetic memory records
belonging to a single agent (``ag1``). Used by the latency benchmark
script as the "large, stress test" run per ``05-POC-PLAN.md §4.2`` task
(c). The expected ceiling here is p95 < 1000ms; if p95 > 1000ms, P3
mitigation 1 (物理分区 evaluation) becomes mandatory even at PoC scale.

Threat T-54-05 mitigation: the 1000-record fixture is in-memory only
and capped at 1000 per the §4.2 protocol — no unbounded growth path.

Same deterministic contract as ``seed_100_records.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent


def _load_fake_backend():
    """Load FakeBackend from sibling conftest.py by file path.

    Avoids 'from conftest import X' ambiguity when multiple conftest.py
    files exist in sys.path (e.g., tests/v11-bias-canary/conftest.py
    being loaded first).
    """
    import importlib.util as _ilu
    fp = _PARENT / 'conftest.py'
    spec = _ilu.spec_from_file_location('_v11_latency_bench_conftest', fp)
    assert spec is not None and spec.loader is not None, f'cannot load {fp}'
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FakeBackend


FakeBackend = _load_fake_backend()

#: Total record count this fixture preloads.
RECORD_COUNT: int = 1000

#: Agent ID the records belong to (single-agent scoped retrieval).
AGENT_ID: str = "ag1"


def build_fixture_backend() -> FakeBackend:
    """Return a ``FakeBackend`` pre-loaded with 1000 synthetic records."""
    backend = FakeBackend()
    for i in range(RECORD_COUNT):
        backend.add(
            content=f"memory record {i} for agent {AGENT_ID}: deterministic content #{i}",
            agent_id=AGENT_ID,
            scope="global",
            confidence=0.5,
        )
    assert len(backend) == RECORD_COUNT, (
        f"fixture seed_1000_records expected {RECORD_COUNT} records, got {len(backend)}"
    )
    return backend
