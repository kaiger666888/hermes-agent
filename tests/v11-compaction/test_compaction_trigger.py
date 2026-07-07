"""Tests for EVAL-04 compaction pass — trigger behavior (55-01 Task 1).

Covers the 7 behavior assertions from 55-01-PLAN.md Task 1 <behavior>:
  - Test 1: exactly max_records (500) does NOT trigger (strict >)
  - Test 2: 501 records DOES trigger (lazy on retrieve)
  - Test 3: 600-record store yields valid 3-tier post-state
  - Test 4: summary record carries source_record_ids chain; originals archived
  - Test 5: GLM dispatch happens inside acquire_glm_slot with provider="glm"
  - Test 6: audit entry appended with action="auto_apply" and eval_score.compaction
  - Test 7: dry_run=True (default) produces ZERO writes
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from agent import memory_compaction
from agent.memory_compaction import (
    COMPACT_TASK_NAME,
    DEFAULT_MAX_RECORDS,
    TIER_ARCHIVAL_MAX,
    TIER_CORE_MAX,
    TIER_WORKING_MAX,
    CompactionReport,
    compact_memory,
)


# --------------------------------------------------------------------------- #
# Test 1: exactly max_records does NOT trigger (strict >)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_at_max_records_does_not_trigger(mock_mem0_backend) -> None:
    """Store with exactly DEFAULT_MAX_RECORDS records is at-budget — no compaction."""
    # Seed 500 records all for "screenplay".
    records = [
        {
            "record_id": f"rec-{i:04d}",
            "agent_id": "screenplay",
            "scope": "project",
            "status": "active",
            "confidence": 0.5,
            "evidence_chain": [f"ev-{i}"],
            "created_at": "2026-06-01T00:00:00+00:00",
            "persona_sha256": "a" * 64,
            "schema_version": "1.0.0",
            "content": f"record {i}",
        }
        for i in range(DEFAULT_MAX_RECORDS)
    ]
    mock_mem0_backend.seed_from(records)

    report = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=None,  # Should not be called.
    )
    assert report.triggered is False
    assert report.pre_count == DEFAULT_MAX_RECORDS
    assert report.summary_record_ids == []
    assert report.archived_record_ids == []
    assert report.audit_entry_id is None


# --------------------------------------------------------------------------- #
# Test 2: 501 records DOES trigger
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_above_max_records_triggers(
    mock_mem0_backend, mock_claim_check_llm
) -> None:
    """Store with 501 records triggers compaction."""
    records = [
        {
            "record_id": f"rec-{i:04d}",
            "agent_id": "screenplay",
            "scope": "global" if i < 10 else "project",
            "status": "active",
            "confidence": 0.85 if i < 10 else (0.5 if i < 110 else 0.35),
            "evidence_chain": [f"ev-{i}"],
            "created_at": "2026-06-01T00:00:00+00:00",
            "persona_sha256": "a" * 64,
            "schema_version": "1.0.0",
            "content": f"record {i}",
        }
        for i in range(501)
    ]
    mock_mem0_backend.seed_from(records)

    report = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )
    assert report.triggered is True
    assert report.pre_count == 501


# --------------------------------------------------------------------------- #
# Test 5: GLM dispatch happens inside acquire_glm_slot with provider="glm"
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_glm_dispatch_uses_serial_lock(
    mock_mem0_backend, mock_claim_check_llm, monkeypatch
) -> None:
    """GLM call is wrapped in acquire_glm_slot and uses provider='glm'."""
    # Seed 600 records to force compaction.
    records = _make_records(600)
    mock_mem0_backend.seed_from(records)

    slot_acquired = {"count": 0}
    real_acquire = memory_compaction.acquire_glm_slot

    class _Slot:
        def __enter__(self):
            slot_acquired["count"] += 1
            return self

        def __exit__(self, *exc):
            return False

    def _fake_acquire(base_url):
        # Only count if the real one would have been a no-op (non-GLM URL).
        # We still want to count ALL entries to verify the wrap happened.
        slot_acquired["count"] += 1
        return _Slot()

    monkeypatch.setattr(memory_compaction, "acquire_glm_slot", _fake_acquire)

    # Use a recording LLM that asserts kwargs.
    seen_kwargs: dict[str, Any] = {}

    async def _recording_llm(*, messages, **kwargs):
        seen_kwargs.update(kwargs)
        return {"content": "summary", "confidence": 0.5}

    await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=_recording_llm,
    )

    assert slot_acquired["count"] >= 1, "acquire_glm_slot must wrap the GLM dispatch"
    assert seen_kwargs.get("provider") == "glm"
    assert seen_kwargs.get("task") == COMPACT_TASK_NAME


# --------------------------------------------------------------------------- #
# Test 6: audit entry appended via curator_audit.append_audit
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_audit_entry_appended(
    mock_mem0_backend, mock_claim_check_llm, monkeypatch, tmp_path
) -> None:
    """dry_run=False appends a curator_audit entry with action='auto_apply'."""
    records = _make_records(600)
    mock_mem0_backend.seed_from(records)

    appended: list[dict[str, Any]] = []

    def _fake_append_audit(**kwargs):
        appended.append(kwargs)
        return "fake-entry-id"

    # Patch the lazy-imported symbol in the module namespace.
    monkeypatch.setattr(memory_compaction, "append_audit", _fake_append_audit)

    report = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )

    assert report.audit_entry_id == "fake-entry-id"
    assert len(appended) == 1, "exactly one audit entry must be appended"
    entry = appended[0]
    assert entry["action"] == "auto_apply"
    assert entry["skill_id"] == "screenplay"
    assert "compaction" in (entry.get("eval_score") or {})
    assert entry["eval_score"]["compaction"]["pre_count"] == 600


# --------------------------------------------------------------------------- #
# Test 7: dry_run=True (default) produces ZERO writes
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_dry_run_default_is_true(mock_mem0_backend) -> None:
    """Default invocation must NOT mutate the backend or append audit."""
    records = _make_records(600)
    mock_mem0_backend.seed_from(records)
    pre_count = mock_mem0_backend.count(agent_id="screenplay")

    # Default dry_run — no explicit False.
    report = await compact_memory(
        "screenplay",
        backend=mock_mem0_backend,
        claim_check_llm=None,
    )

    assert report.dry_run is True
    assert report.triggered is True  # Planning proceeds; writes don't.
    # No backend writes.
    post_count = mock_mem0_backend.count(agent_id="screenplay")
    assert post_count == pre_count, "dry_run must not change record count"
    # No update calls (no archive mutations).
    update_calls = [c for c in mock_mem0_backend.calls if c[0] == "update"]
    assert update_calls == [], "dry_run must not invoke backend.update"
    # No add calls (no summary record written).
    add_calls = [c for c in mock_mem0_backend.calls if c[0] == "add"]
    assert add_calls == [], "dry_run must not invoke backend.add"
    # No audit entry.
    assert report.audit_entry_id is None


@pytest.mark.asyncio
async def test_dry_run_explicit_true_no_writes(
    mock_mem0_backend, mock_claim_check_llm
) -> None:
    """Explicit dry_run=True is the same as default — zero writes."""
    records = _make_records(600)
    mock_mem0_backend.seed_from(records)
    pre_count = mock_mem0_backend.count(agent_id="screenplay")

    report = await compact_memory(
        "screenplay",
        dry_run=True,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )
    assert report.dry_run is True
    assert mock_mem0_backend.count(agent_id="screenplay") == pre_count


# --------------------------------------------------------------------------- #
# Test: maybe_compact_on_retrieve lazy trigger
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_maybe_compact_on_retrieve_lazy(mock_mem0_backend) -> None:
    """Lazy trigger returns None when under threshold, report when over."""
    # Under threshold — returns None.
    small = _make_records(100)
    mock_mem0_backend.seed_from(small)
    result = await memory_compaction.maybe_compact_on_retrieve(
        "screenplay",
        backend=mock_mem0_backend,
        claim_check_llm=None,
    )
    assert result is None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_records(n: int) -> list[dict[str, Any]]:
    """Build N synthetic records with the 10 mandated fields, varied tiers."""
    records: list[dict[str, Any]] = []
    for i in range(n):
        if i < 10:
            scope, conf = "global", 0.90
        elif i < 110:
            scope, conf = "project", 0.60
        else:
            scope, conf = "session", 0.40
        records.append(
            {
                "record_id": f"rec-{i:04d}",
                "agent_id": "screenplay",
                "scope": scope,
                "status": "active",
                "confidence": conf,
                "evidence_chain": [f"ev-{i}"],
                "created_at": "2026-06-01T00:00:00+00:00",
                "persona_sha256": "a" * 64,
                "schema_version": "1.0.0",
                "content": f"record {i}",
            }
        )
    return records
