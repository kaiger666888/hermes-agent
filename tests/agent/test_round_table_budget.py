"""Phase 58 THROTTLE-02 — token-budget tracking for the round-table state.

Tests the per-round-table TPM (Token-Per-Meeting) budget contract:

1. ``open_round_table`` accepts an optional ``token_budget`` parameter
   (default 100K) and persists it as ``tokenBudget`` alongside the
   ``tokensConsumed`` (zero-init) and ``events`` (empty list) fields.
2. ``record_token_usage`` performs an atomic read-modify-write to add
   consumed tokens to ``tokensConsumed``. Idempotent across threads.
3. ``append_event`` appends a structured event dict to the state file's
   ``events`` array (used by budget_warning + budget_exceeded events).
4. ``submit_round_table_result`` extends the receipt with
   ``tokensConsumed`` (int) + ``costUsdEstimate`` (float) at the TOP
   LEVEL of the state dict. Cost formula:
   ``(tokensConsumed / 1_000_000) * 0.5 / 7.2`` (GLM-5.2 pricing).

Cross-phase regression: Phase 52's tests in ``test_round_table_state.py``
+ Phase 52 INFRA-04's tests in ``test_round_table_executor.py`` MUST stay
GREEN after this file lands.
"""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent.round_table_state import (
    DEFAULT_TOKEN_BUDGET,
    GLM_5_2_CNY_PER_1M_TOKENS,
    USD_CNY_RATE,
    abort_round_table,
    append_event,
    append_turn,
    open_round_table,
    record_token_usage,
    submit_round_table_result,
)
from hermes_constants import get_hermes_home


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _state_dir(project_slug: str = "test-budget-slug") -> Path:
    """Canonical state dir under the autouse-redirected HERMES_HOME."""
    return (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / project_slug
        / "round_tables"
    )


def _make_round(round_id: str = "round-budget-1", token_budget: int | None = None) -> Path:
    """Open a round-table state file; return its path."""
    state_dir = _state_dir()
    kwargs: dict = dict(
        state_dir=state_dir,
        round_id=round_id,
        project_id="test-budget-slug",
        question="How many tokens?",
        panelist_agent_ids=["agent-a", "agent-b"],
        caller="cc-budget-test",
    )
    if token_budget is not None:
        kwargs["token_budget"] = token_budget
    open_round_table(**kwargs)
    return state_dir / f"{round_id}.json"


def _read_state(state_path: Path) -> dict:
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Task 1 — round_table_state token_budget + events + helpers
# --------------------------------------------------------------------------- #


class TestOpenWithTokenBudget:
    def test_open_with_default_budget(self):
        """No token_budget arg → tokenBudget=DEFAULT_TOKEN_BUDGET=100000."""
        state_path = _make_round("round-default-budget")
        state = _read_state(state_path)
        assert state["tokenBudget"] == DEFAULT_TOKEN_BUDGET == 100_000
        assert state["tokensConsumed"] == 0
        assert state["events"] == []

    def test_open_with_explicit_budget(self):
        """Explicit token_budget=50000 is persisted."""
        state_path = _make_round("round-explicit-budget", token_budget=50_000)
        state = _read_state(state_path)
        assert state["tokenBudget"] == 50_000
        assert state["tokensConsumed"] == 0
        assert state["events"] == []


class TestRecordTokenUsage:
    def test_single_record_adds_to_consumed(self):
        state_path = _make_round("round-record-1")
        record_token_usage(state_path, tokens=3500)
        state = _read_state(state_path)
        assert state["tokensConsumed"] == 3500

    def test_multiple_records_are_additive(self):
        state_path = _make_round("round-record-2")
        record_token_usage(state_path, tokens=3500)
        record_token_usage(state_path, tokens=2000)
        state = _read_state(state_path)
        assert state["tokensConsumed"] == 5500

    def test_record_zero_is_noop(self):
        """Recording 0 tokens MUST not raise; the guard in the driver
        skips when ``tokens > 0`` so this path is exercised only if
        the helper is called directly."""
        state_path = _make_round("round-record-zero")
        record_token_usage(state_path, tokens=0)
        state = _read_state(state_path)
        assert state["tokensConsumed"] == 0


class TestAppendEvent:
    def test_single_event_appended(self):
        state_path = _make_round("round-event-1")
        event = {
            "type": "budget_warning",
            "threshold": 0.5,
            "remaining_tokens": 25_000,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        append_event(state_path, event)
        state = _read_state(state_path)
        assert len(state["events"]) == 1
        assert state["events"][0]["type"] == "budget_warning"
        assert state["events"][0]["remaining_tokens"] == 25_000

    def test_multiple_events_preserve_order(self):
        state_path = _make_round("round-event-2")
        for i in range(3):
            append_event(state_path, {
                "type": "budget_warning" if i < 2 else "budget_exceeded",
                "threshold": 2.0 - float(i),
                "remaining_tokens": 30_000 - i * 10_000,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
        state = _read_state(state_path)
        assert len(state["events"]) == 3
        assert state["events"][0]["remaining_tokens"] == 30_000
        assert state["events"][1]["remaining_tokens"] == 20_000
        assert state["events"][2]["type"] == "budget_exceeded"
        assert state["events"][2]["remaining_tokens"] == 10_000


class TestRecordTokenUsageConcurrency:
    def test_concurrent_writes_preserve_total(self):
        """100 concurrent record_token_usage calls MUST sum exactly.

        atomic_json_write = temp + fsync + os.replace guarantees no
        partial body, but read-modify-write still requires serialization
        at the helper layer so concurrent writers don't lose updates
        (lost-update = read same state, both add N, both write same sum).

        The per-state-file threading.Lock in record_token_usage is the
        serialization mechanism.
        """
        state_path = _make_round("round-concurrent")
        N_THREADS = 100
        TOKENS_PER_CALL = 100

        def _add_one():
            record_token_usage(state_path, tokens=TOKENS_PER_CALL)

        with ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(lambda _: _add_one(), range(N_THREADS)))

        state = _read_state(state_path)
        assert state["tokensConsumed"] == N_THREADS * TOKENS_PER_CALL, (
            f"expected {N_THREADS * TOKENS_PER_CALL}, got {state['tokensConsumed']} "
            f"— lost updates in concurrent record_token_usage"
        )


class TestSubmitReceipt:
    def test_receipt_includes_token_and_cost_fields(self):
        """submit_round_table_result response has tokensConsumed + costUsdEstimate."""
        state_path = _make_round("round-receipt-1")
        record_token_usage(state_path, tokens=3500)
        result = submit_round_table_result(
            state_path=state_path,
            conclusion="done",
            cited_memories=[],
            closed_by="cc-1",
        )
        assert "tokensConsumed" in result
        assert "costUsdEstimate" in result
        assert result["tokensConsumed"] == 3500
        assert isinstance(result["costUsdEstimate"], float)
        assert result["costUsdEstimate"] > 0

    def test_cost_calculation_correctness(self):
        """costUsdEstimate = (tokensConsumed / 1M) * 0.5 / 7.2."""
        state_path = _make_round("round-receipt-2")
        # Push tokensConsumed to 100000 → cost should be approx 0.00694 USD.
        record_token_usage(state_path, tokens=100_000)
        result = submit_round_table_result(
            state_path=state_path,
            conclusion="done",
            cited_memories=[],
            closed_by="cc-1",
        )
        expected = (100_000 / 1_000_000) * 0.5 / 7.2
        assert abs(result["costUsdEstimate"] - round(expected, 6)) < 1e-9, (
            f"costUsdEstimate={result['costUsdEstimate']} expected~={expected}"
        )

    def test_cost_zero_when_no_tokens_consumed(self):
        """If no panelist calls happened, costUsdEstimate == 0.0."""
        state_path = _make_round("round-receipt-zero")
        result = submit_round_table_result(
            state_path=state_path,
            conclusion="nothing debated",
            cited_memories=[],
            closed_by="cc-1",
        )
        assert result["tokensConsumed"] == 0
        assert result["costUsdEstimate"] == 0.0


class TestBudgetExceededAbort:
    def test_abort_with_budget_exceeded_reason(self):
        """abort_round_table accepts arbitrary 'budget_exceeded' reason."""
        state_path = _make_round("round-abort-budget")
        # Push tokensConsumed above tokenBudget — record_token_usage
        # itself does NOT auto-abort (delegates to caller).
        record_token_usage(state_path, tokens=110_000)
        result = abort_round_table(
            state_path,
            reason="budget_exceeded",
            aborted_by="round_table_executor",
        )
        assert result["status"] == "aborted"
        assert result["abortRoundTable"]["reason"] == "budget_exceeded"
        # State persisted
        state = _read_state(state_path)
        assert state["status"] == "aborted"


class TestOpenIdempotenceWithBudget:
    def test_duplicate_open_preserves_existing_budget(self):
        """Re-open of existing round returns 409 WITHOUT overwriting token_budget."""
        state_path = _make_round("round-idem-budget", token_budget=42_000)
        # Second open call with different budget — should be 409, no overwrite.
        result = open_round_table(
            state_dir=_state_dir(),
            round_id="round-idem-budget",
            project_id="test-budget-slug",
            question="Q?",
            panelist_agent_ids=["a", "b"],
            caller="cc-2",
            token_budget=99_999,  # different — should NOT take effect
        )
        assert result["status"] == 409
        # Confirm the existing tokenBudget is unchanged.
        state = _read_state(state_path)
        assert state["tokenBudget"] == 42_000


class TestModuleConstants:
    """Pin the pricing constants — operators / receipt formula depend on them."""

    def test_default_token_budget_is_100k(self):
        assert DEFAULT_TOKEN_BUDGET == 100_000

    def test_glm_5_2_pricing_constant(self):
        """GLM-5.2 hardcoded at 0.5 CNY per 1M tokens."""
        assert GLM_5_2_CNY_PER_1M_TOKENS == 0.5

    def test_usd_cny_rate_constant(self):
        """Fixed USD/CNY conversion rate (configurable in v13+)."""
        assert USD_CNY_RATE == 7.2
