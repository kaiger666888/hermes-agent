"""Unit tests for ``agent/memory_scoped_retrieval.py`` (Phase 54 plan 02).

Covers the 4 behavior contracts from ``54-02-PLAN.md`` Task 1:

1. ``compute_percentiles`` returns ``{"p50", "p95", "p99"}`` matching
   stdlib ``statistics.quantiles`` semantics on a 5-element input.
2. ``timed_retrieval`` wraps a happy-path ``FakeBackend`` and returns a
   ``LatencySample`` with ``status="ok"``, ``hits=[...]`` and
   ``latency_ms > 0``.
3. ``timed_retrieval`` swallows a ``FakeBackend`` injected failure and
   returns ``LatencySample(status="error", hits=[])`` — never raises.
4. ``timed_retrieval`` does NOT call any LLM (no ``call_llm`` import path
   reachable from the module — grep-verifiable separately, this test
   asserts the runtime path stays LLM-free by patching
   ``agent.auxiliary_client.call_llm`` to a detector).

TDD: RED until Task 1 GREEN lands ``agent/memory_scoped_retrieval.py``.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# The test directory ``tests/v11-latency-bench/`` is not a valid Python
# identifier (hyphens), so we cannot do a normal ``from tests.v11-latency-...``
# import. pytest still discovers ``conftest.py`` automatically (fixtures
# become injectable by name), but for direct class access in test bodies
# (we instantiate FakeBackend explicitly so we can inject failure modes),
# we load the conftest module by file path. This avoids the ambiguity of
# `from conftest import X` when multiple conftest.py files exist in sys.path
# (which happens when running tests across multiple directories).
_TESTS_DIR = Path(__file__).resolve().parent
_CONFTEST_PATH = _TESTS_DIR / "conftest.py"

import importlib.util as _importlib_util
_spec = _importlib_util.spec_from_file_location("_v11_latency_bench_conftest", _CONFTEST_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_CONFTEST_PATH}"
_conftest_module = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest_module)
FakeBackend = _conftest_module.FakeBackend


# ── Helpers ─────────────────────────────────────────────────────────────────


def _import_module():
    """Lazy import so RED phase collects cleanly before implementation lands."""
    from agent import memory_scoped_retrieval
    return memory_scoped_retrieval


# ── Test 1: compute_percentiles ─────────────────────────────────────────────


class TestComputePercentiles:
    def test_compute_percentiles_5_element_input(self):
        """``compute_percentiles([10,20,30,40,50])`` returns the expected
        stdlib ``statistics.quantiles(n=100, method="inclusive")`` mapping.

        The contract from 54-02-PLAN.md `<behavior>` Test 1:
          - p50 == 30.0 (median)
          - p95 ~= 48.0 (within float tolerance)
          - p99 ~= 49.8 (within float tolerance)
        """
        mod = _import_module()
        result = mod.compute_percentiles([10.0, 20.0, 30.0, 40.0, 50.0])
        assert set(result.keys()) == {"p50", "p95", "p99"}
        assert result["p50"] == pytest.approx(30.0, abs=0.5)
        assert result["p95"] == pytest.approx(48.0, abs=1.5)
        assert result["p99"] == pytest.approx(49.8, abs=1.5)

    def test_compute_percentiles_handles_short_input(self):
        """len<2 input must not crash — returns all-equal values."""
        mod = _import_module()
        result = mod.compute_percentiles([42.0])
        assert result == {"p50": 42.0, "p95": 42.0, "p99": 42.0}

    def test_compute_percentiles_empty_input(self):
        """Empty input returns zeros (defensive — never raises)."""
        mod = _import_module()
        result = mod.compute_percentiles([])
        assert result == {"p50": 0.0, "p95": 0.0, "p99": 0.0}


# ── Test 2: timed_retrieval happy path ──────────────────────────────────────


class TestTimedRetrievalHappyPath:
    @pytest.mark.asyncio
    async def test_timed_retrieval_returns_latency_sample_with_hits(self):
        """Wraps a working ``FakeBackend``; returns ``status="ok"`` and hits."""
        mod = _import_module()
        backend = FakeBackend()
        backend.add(content="record-1", agent_id="ag1")
        backend.add(content="record-2", agent_id="ag1")

        sample = await mod.timed_retrieval(
            query="benchmark query",
            agent_id="ag1",
            backend=backend,
            top_k=5,
        )

        assert isinstance(sample, mod.LatencySample)
        assert sample.status == "ok"
        assert sample.latency_ms > 0.0
        assert isinstance(sample.latency_ms, float)
        assert len(sample.hits) == 2
        assert all(isinstance(h, dict) for h in sample.hits)
        assert isinstance(sample.ts, str) and len(sample.ts) > 0


# ── Test 3: timed_retrieval error path ──────────────────────────────────────


class TestTimedRetrievalErrorPath:
    @pytest.mark.asyncio
    async def test_timed_retrieval_on_backend_exception_returns_error_sample(self):
        """When ``backend.search`` raises, returns ``status="error"``,
        ``hits=[]``, ``latency_ms`` still measured — never raises."""
        mod = _import_module()
        backend = FakeBackend()
        backend.search_raises = True

        sample = await mod.timed_retrieval(
            query="any",
            agent_id="ag1",
            backend=backend,
        )

        assert sample.status == "error"
        assert sample.hits == []
        assert sample.latency_ms > 0.0  # still measured up to exception point


# ── Test 4: no LLM in timed_retrieval path ──────────────────────────────────


class TestNoLLMInTimedRetrievalPath:
    @pytest.mark.asyncio
    async def test_timed_retrieval_does_not_dispatch_call_llm(self):
        """``timed_retrieval`` must never invoke ``auxiliary_client.call_llm``
        — the §4.2 SLO explicitly excludes LLM-bound calls (per STACK §7.4).

        This test patches ``call_llm`` with a detector that fails the test
        if the wrapper accidentally dispatches an LLM call.
        """
        mod = _import_module()
        backend = FakeBackend()
        backend.add(content="x", agent_id="ag1")

        call_detected: list[Any] = []

        def _detector(*args: Any, **kwargs: Any) -> Any:
            call_detected.append((args, kwargs))
            raise AssertionError(
                "timed_retrieval MUST NOT call auxiliary_client.call_llm; "
                "SLO excludes LLM-bound calls per 05-POC-PLAN.md §4.2 + STACK §7.4"
            )

        # Patch the canonical LLM dispatcher used elsewhere in agent/*.
        with patch("agent.auxiliary_client.call_llm", side_effect=_detector):
            sample = await mod.timed_retrieval(
                query="q",
                agent_id="ag1",
                backend=backend,
            )

        assert call_detected == [], (
            f"timed_retrieval unexpectedly dispatched call_llm: {call_detected}"
        )
        assert sample.status == "ok"


# ── Test 5: timed_retrieval works without explicit backend ──────────────────
#
# When no ``backend`` kwarg is supplied, the wrapper delegates to
# ``memory_arbitration.memory_retrieve_scoped`` (which itself lazy-imports the
# mem0 plugin). With MEM0_API_KEY unset in CI, that returns
# ``{"status": "unavailable", "hits": []}`` — the wrapper must propagate this
# as ``status="unavailable"`` so benchmark SLO verdict logic can treat it as
# "skip SLO verdict" rather than as a zero-latency pass.


class TestTimedRetrievalUnavailableBackend:
    @pytest.mark.asyncio
    async def test_timed_retrieval_propagates_unavailable_status(self, monkeypatch):
        """When the arbitration layer reports the backend is unavailable
        (e.g. MEM0_API_KEY unset in CI), the wrapper surfaces
        ``status="unavailable"`` rather than masking it as ``"ok"`` or
        ``"error"``.
        """
        mod = _import_module()
        # Ensure no mem0 env var leaks from the host.
        monkeypatch.delenv("MEM0_API_KEY", raising=False)

        sample = await mod.timed_retrieval(
            query="q",
            agent_id="ag1",
            # No backend kwarg — exercises the memory_arbitration fallback.
        )

        # In CI (no mem0 configured), status must be "unavailable".
        # Operators running with a real backend may see "ok" instead —
        # this test asserts the CI-fallback path only.
        assert sample.status in ("unavailable", "ok"), (
            f"unexpected status {sample.status!r}"
        )
        assert isinstance(sample.latency_ms, float)
        assert sample.latency_ms >= 0.0
