"""OBSRV-02 unit tests for the round-table metrics collector (Plan 67-02 Task 1).

Verifies:
* ``_percentiles`` degrades gracefully on empty / single-element buffers
  (RESEARCH Pitfall 1 -- ``statistics.quantiles`` raises ``StatisticsError``
  on fewer than 2 data points).
* ``_percentiles`` returns interpolated p50/p95 on a 100-element list.
* ``record_round_table_entry`` appends to the module-level buffer and
  ``get_round_table_metrics().count`` reflects it.
* Buffer eviction: after 101 appends ``count == 100`` (deque maxlen).
* ``get_round_table_metrics()`` on an empty buffer returns a dict with
  ``count=0``, ``p50_latency_ms=0.0``, ``p95_latency_ms=0.0`` and an
  empty ``status_distribution``.
* ``_turn_capture`` happy path records an entry with ``status="ok"``.
* ``_turn_capture`` exception path records an entry with
  ``status="error"`` BEFORE re-raising (RESEARCH Pitfall 2 -- try/finally
  in the context manager).

These tests are pure-unit -- they do NOT exercise ``mcp_serve.get_agent_opinion``
(which would need an asyncio runtime + real locks). The MCP instrumentation
is verified by the manual smoke step in Task 2's ``<verify>`` block.
"""

from __future__ import annotations

import pytest

from agent.observability.round_table_metrics import (
    RoundTableMetricEntry,
    _percentiles,
    _reset_for_test,
    _submit_capture,
    _turn_capture,
    get_round_table_metrics,
    record_round_table_entry,
)


class TestPercentiles:
    """``_percentiles`` is the load-bearing helper for p50/p95 computation.

    Covers RESEARCH Pitfall 1: ``statistics.quantiles`` raises on empty
    or single-element inputs -- the helper MUST length-check first.
    """

    def test_empty_returns_zeros(self) -> None:
        # Pitfall 1: statistics.quantiles([]) raises StatisticsError.
        out = _percentiles([])
        assert out["p50"] == 0.0
        assert out["p95"] == 0.0
        assert out["count"] == 0

    def test_single_element_graceful(self) -> None:
        # Edge case: single sample returns the value as both p50 and p95.
        out = _percentiles([42.5])
        assert out["p50"] == 42.5
        assert out["p95"] == 42.5
        assert out["count"] == 1

    def test_hundred_element_list_interpolation(self) -> None:
        # 1..100 inclusive. statistics.quantiles(data, n=100) interpolates
        # so p50 ~ 50.5 and p95 ~ 95.05 (the boundary quantile).
        samples = [float(x) for x in range(1, 101)]
        out = _percentiles(samples)
        assert out["count"] == 100
        # Allow small float slack from the interpolation method.
        assert 49.5 < out["p50"] < 51.5, f"p50 off: {out['p50']}"
        assert 94.0 < out["p95"] < 96.0, f"p95 off: {out['p95']}"


class TestRoundTableMetricsBuffer:
    """``record_round_table_entry`` + ``get_round_table_metrics`` buffer ops."""

    @pytest.fixture(autouse=True)
    def _reset_buffer(self) -> None:
        # Cross-test isolation: the module-level buffer is shared. Clear
        # before every test so prior tests cannot leak state into later ones.
        _reset_for_test()
        yield
        _reset_for_test()

    def _entry(
        self,
        *,
        round_id: str = "round-1",
        duration_ms: float = 10.0,
        token_cost: int = 100,
        status: str = "ok",
        serial_lock_wait_ms: float = 1.0,
    ) -> RoundTableMetricEntry:
        return RoundTableMetricEntry(
            round_id=round_id,
            snapshot_at_iso="2026-07-08T00:00:00+00:00",
            duration_ms=duration_ms,
            token_cost=token_cost,
            cost_usd=0.0,
            turn_count=1,
            serial_lock_wait_ms=serial_lock_wait_ms,
            early_stop_triggered=False,
            status=status,
        )

    def test_record_appends_and_count_reflects(self) -> None:
        record_round_table_entry(self._entry(duration_ms=5.0))
        record_round_table_entry(self._entry(duration_ms=15.0))
        out = get_round_table_metrics()
        assert out["count"] == 2

    def test_buffer_evicts_at_maxlen(self) -> None:
        # 101 appends -> count clamps to 100 (deque maxlen).
        for i in range(101):
            record_round_table_entry(self._entry(duration_ms=float(i)))
        out = get_round_table_metrics()
        assert out["count"] == 100

    def test_empty_buffer_returns_zero_percentiles(self) -> None:
        # No entries -> p50/p95/avg all zero. No StatisticsError.
        out = get_round_table_metrics()
        assert out["count"] == 0
        assert out["p50_latency_ms"] == 0.0
        assert out["p95_latency_ms"] == 0.0
        assert out["avg_token_cost"] == 0.0
        assert out["total_token_cost"] == 0
        assert out["status_distribution"] == {}
        assert out["serial_lock_wait_p95_ms"] == 0.0
        assert out["early_stop_rate"] == 0.0

    def test_status_distribution_counts_statuses(self) -> None:
        record_round_table_entry(self._entry(status="ok"))
        record_round_table_entry(self._entry(status="ok"))
        record_round_table_entry(self._entry(status="serial_violation"))
        out = get_round_table_metrics()
        assert out["status_distribution"].get("ok") == 2
        assert out["status_distribution"].get("serial_violation") == 1

    def test_total_and_avg_token_cost(self) -> None:
        record_round_table_entry(self._entry(token_cost=100))
        record_round_table_entry(self._entry(token_cost=300))
        out = get_round_table_metrics()
        assert out["total_token_cost"] == 400
        assert out["avg_token_cost"] == 200.0


class TestTurnCapture:
    """``_turn_capture`` context manager -- happy + exception paths."""

    @pytest.fixture(autouse=True)
    def _reset_buffer(self) -> None:
        _reset_for_test()
        yield
        _reset_for_test()

    def test_capture_records_on_happy_path(self) -> None:
        with _turn_capture("round-1"):
            pass  # no-op body
        out = get_round_table_metrics()
        assert out["count"] == 1
        # The single recorded entry has status="ok" by default.
        # status_distribution tells us the status was recorded.
        assert out["status_distribution"].get("ok") == 1

    def test_capture_records_on_exception_path(self) -> None:
        # The context manager MUST record the entry BEFORE re-raising.
        with pytest.raises(ValueError, match="boom"):
            with _turn_capture("round-1"):
                raise ValueError("boom")
        out = get_round_table_metrics()
        assert out["count"] == 1
        assert out["status_distribution"].get("error") == 1

    def test_capture_status_can_be_overridden(self) -> None:
        # The caller (mcp_serve instrumentation) sets cap.status to a
        # specific value before the context exits.
        with _turn_capture("round-1") as cap:
            cap.status = "serial_violation"
        out = get_round_table_metrics()
        assert out["status_distribution"].get("serial_violation") == 1


class TestSubmitCapture:
    """``_submit_capture`` context manager -- happy + error paths."""

    @pytest.fixture(autouse=True)
    def _reset_buffer(self) -> None:
        _reset_for_test()
        yield
        _reset_for_test()

    def test_submit_happy_path_records_completed(self) -> None:
        with _submit_capture("round-1") as cap:
            cap.token_cost = 500
            cap.cost_usd = 0.012
            cap.turn_count = 3
            cap.early_stop_triggered = False
            cap.status = "completed"
        out = get_round_table_metrics()
        assert out["count"] == 1
        assert out["total_token_cost"] == 500
        assert out["status_distribution"].get("completed") == 1

    def test_submit_exception_path_records_error(self) -> None:
        with pytest.raises(RuntimeError, match="submit failed"):
            with _submit_capture("round-1"):
                raise RuntimeError("submit failed")
        out = get_round_table_metrics()
        assert out["count"] == 1
        assert out["status_distribution"].get("error") == 1
