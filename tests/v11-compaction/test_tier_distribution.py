"""Tests for EVAL-04 compaction pass — 3-tier post-state validation (55-01 Task 1).

Covers:
  - Test 3 (post-state tier distribution): 600-record store yields
    core <=10 / working <=100 / archival <=10000 post-compaction.
  - Test 4 (source_record_ids chain): summary record carries source_record_ids
    populated with the original record_ids it summarizes; originals are
    archived (status="archived" or "superseded"), NOT deleted.
  - Full end-to-end fixture integration test using 600_record_store.json.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from agent import memory_compaction
from agent.memory_compaction import (
    DEFAULT_MAX_RECORDS,
    TIER_ARCHIVAL_MAX,
    TIER_CORE_MAX,
    TIER_WORKING_MAX,
    CompactionReport,
    compact_memory,
)


# --------------------------------------------------------------------------- #
# Test 3: 600-record fixture yields valid 3-tier post-state
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_600_record_fixture_3tier_post_state(
    mock_mem0_backend, fixture_600_records, mock_claim_check_llm
) -> None:
    """End-to-end: 600-record store → compact → valid 3-tier distribution."""
    mock_mem0_backend.seed_from(fixture_600_records)

    report = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )

    assert report.triggered is True
    assert report.pre_count == 600
    # No data loss — compaction reorganizes originals (archived, not deleted).
    # Adding summary records may grow the total by the number of summaries
    # produced (typically +1); originals are preserved as status="archived".
    # Per §4.4 the invariant is "no DELETIONS" — post_count >= pre_count.
    assert report.post_count >= report.pre_count, (
        f"post_count ({report.post_count}) must not drop below pre_count "
        f"({report.pre_count}) — compaction archives, never deletes"
    )
    # Tier distribution within budget (ACTIVE records per tier).
    tiers = report.tiers
    assert tiers["core"] <= TIER_CORE_MAX, f"core tier overflow: {tiers['core']}"
    assert tiers["working"] <= TIER_WORKING_MAX, f"working tier overflow: {tiers['working']}"
    assert tiers["archival"] <= TIER_ARCHIVAL_MAX, f"archival tier overflow: {tiers['archival']}"


# --------------------------------------------------------------------------- #
# Test 4: source_record_ids chain + originals archived
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_summary_record_carries_source_chain(
    mock_mem0_backend, fixture_600_records, mock_claim_check_llm
) -> None:
    """Summary record's source_record_ids lists every original it summarizes."""
    mock_mem0_backend.seed_from(fixture_600_records)
    pre_record_ids = {r["record_id"] for r in fixture_600_records}

    report = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )

    # At least one summary record was produced.
    assert len(report.summary_record_ids) >= 1, "must produce >=1 summary record"

    # Fetch the summary records from the backend.
    summaries = [
        r for r in mock_mem0_backend.get_all(agent_id="screenplay")
        if r["record_id"] in set(report.summary_record_ids)
    ]
    assert len(summaries) == len(report.summary_record_ids)

    # Every summary record must carry source_record_ids referencing originals.
    all_source_ids: set[str] = set()
    for s in summaries:
        assert "source_record_ids" in s, "summary must carry source_record_ids field"
        src_ids = s["source_record_ids"]
        assert isinstance(src_ids, list) and len(src_ids) > 0
        # Every source id must be one of the originals.
        for sid in src_ids:
            assert sid in pre_record_ids, f"source_record_id {sid!r} not in originals"
        all_source_ids.update(src_ids)

    # Every archived original must still be present in the backend (not deleted).
    for archived_id in report.archived_record_ids:
        match = [r for r in mock_mem0_backend.get_all() if r["record_id"] == archived_id]
        assert len(match) == 1, f"archived original {archived_id} must still exist"
        assert match[0]["status"] in ("archived", "superseded"), (
            f"original {archived_id} status must be archived/superseded, "
            f"got {match[0]['status']!r}"
        )


@pytest.mark.asyncio
async def test_no_data_loss_post_compaction(
    mock_mem0_backend, fixture_600_records, mock_claim_check_llm
) -> None:
    """Compaction never deletes — total record count does not decrease."""
    mock_mem0_backend.seed_from(fixture_600_records)
    pre_count = mock_mem0_backend.count()

    await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )
    post_count = mock_mem0_backend.count()
    # Total record count must not decrease (originals archived, not deleted).
    # May increase by the number of summary records added (typically +1).
    assert post_count >= pre_count, (
        f"record count must not decrease: pre={pre_count} post={post_count}"
    )


# --------------------------------------------------------------------------- #
# Idempotency: running compaction twice yields same tier counts
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_compaction_idempotent(
    mock_mem0_backend, fixture_600_records, mock_claim_check_llm
) -> None:
    """Second compaction pass is a no-op (already compacted)."""
    mock_mem0_backend.seed_from(fixture_600_records)

    report1 = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )
    assert report1.triggered is True

    # Second pass — store now has summary records + archived originals but
    # still > 500 raw rows. However the active (non-archived) count should
    # be under threshold, so triggered=False.
    report2 = await compact_memory(
        "screenplay",
        dry_run=False,
        backend=mock_mem0_backend,
        claim_check_llm=mock_claim_check_llm,
    )
    # Either not triggered (active count <= max) OR triggered but yields
    # same tier distribution (idempotent reorganization).
    if report2.triggered:
        assert report2.tiers == report1.tiers, (
            "idempotent re-compaction must produce same tier distribution"
        )


# --------------------------------------------------------------------------- #
# Boundary: tier budget enforcement via constants
# --------------------------------------------------------------------------- #


def test_tier_constants_match_plan() -> None:
    """Tier constants match the §4.4 contract."""
    assert DEFAULT_MAX_RECORDS == 500
    assert TIER_CORE_MAX == 10
    assert TIER_WORKING_MAX == 100
    assert TIER_ARCHIVAL_MAX == 10000


def test_compact_task_name_is_memory_compaction() -> None:
    """Auxiliary task name is exactly 'memory_compaction'."""
    assert memory_compaction.COMPACT_TASK_NAME == "memory_compaction"
