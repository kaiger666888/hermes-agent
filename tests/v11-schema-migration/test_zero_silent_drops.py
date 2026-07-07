"""P14 mitigation tests — zero silent drops (T-55-13).

Asserts that every source FeedbackRecord appears in the dry-run output.
The migration MUST NOT silently drop records — every line is either:
  - Migrated to a target record (counted in ``source_record_ids_accounted``), OR
  - Logged as a mapping warning (counted in ``metrics.malformed_lines``).

Per CLAUDE.md conventions:
  - ``encoding="utf-8"`` on every ``open()``.
  - ``@pytest.mark.asyncio`` NOT needed (all sync).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ── Every source record appears in summary ──────────────────────────────


class TestEverySourceRecordAppears:
    def test_30_records_all_accounted(self, run_migration) -> None:
        """Sample fixture has 30 records — all 30 must appear in summary."""
        result, summary = run_migration()
        assert summary["metrics"]["total_source_count"] == 30
        assert len(summary["source_record_ids_accounted"]) == 30

    def test_no_duplicate_record_ids(self, run_migration) -> None:
        """All record_ids must be unique (UUIDv5 from distinct content)."""
        _, summary = run_migration()
        ids = summary["source_record_ids_accounted"]
        assert len(set(ids)) == len(ids), "duplicate record_ids detected"

    def test_record_ids_are_valid_uuids(self, run_migration) -> None:
        """Each record_id must be a valid UUID string."""
        import uuid

        _, summary = run_migration()
        for rid in summary["source_record_ids_accounted"]:
            # uuid.UUID accepts both hyphenated and hex forms.
            uuid.UUID(rid)


# ── All 5 metrics fields present ─────────────────────────────────────────


class TestAllMetricsFieldsPresent:
    @pytest.mark.parametrize(
        "key",
        [
            "total_source_count",
            "per_field_default_fill_rate",
            "conflict_count",
            "estimated_target_storage_mb",
            "mapping_warnings",
        ],
    )
    def test_required_metric_key_present(
        self, run_migration, key: str
    ) -> None:
        """All 5 §4.5 metrics must be present in the JSON summary."""
        _, summary = run_migration()
        assert key in summary["metrics"], (
            f"missing required metric: {key}. "
            f"Present: {sorted(summary['metrics'].keys())}"
        )

    def test_per_field_default_fill_rate_is_dict(self, run_migration) -> None:
        _, summary = run_migration()
        rates = summary["metrics"]["per_field_default_fill_rate"]
        assert isinstance(rates, dict)
        # Spot-check a few fields are in the dict.
        for field in ("agent_id", "scope", "confidence", "status"):
            assert field in rates, f"missing field in fill rate: {field}"

    def test_conflict_count_has_expected_subkeys(self, run_migration) -> None:
        _, summary = run_migration()
        conflicts = summary["metrics"]["conflict_count"]
        # The bad-verdict count goes under "quarantined_verdict_bad".
        assert "quarantined_verdict_bad" in conflicts
        # The fixture has 9 bad records (4 cli + 2 kais_aigc + 3 cinematographer).
        assert conflicts["quarantined_verdict_bad"] == 9


# ── Migration-tracking bonus metrics ────────────────────────────────────


class TestMigrationTrackingMetrics:
    """05-POC-PLAN.md §4.7 requires migrated_active / migrated_quarantined /
    dropped_or_failed in addition to the original §4.5 five."""

    def test_migrated_active_count(self, run_migration) -> None:
        """good + needs_work records → migrated_active.

        Fixture breakdown: 10 good + 11 needs_work = 21 active.
        """
        _, summary = run_migration()
        assert summary["metrics"]["migrated_active"] == 21

    def test_migrated_quarantined_count(self, run_migration) -> None:
        """bad records → migrated_quarantined. Fixture has 9 bad."""
        _, summary = run_migration()
        assert summary["metrics"]["migrated_quarantined"] == 9

    def test_dropped_or_failed_is_zero(self, run_migration) -> None:
        """P14 mitigation — zero silent drops on valid fixture."""
        _, summary = run_migration()
        assert summary["metrics"]["dropped_or_failed"] == 0


# ── record_id UUIDv5 determinism ────────────────────────────────────────


class TestRecordIdDeterministic:
    def test_two_runs_produce_identical_record_ids(self, run_migration) -> None:
        """Re-running dry-run produces identical source_record_ids_accounted."""
        _, summary_1 = run_migration()
        _, summary_2 = run_migration()
        assert (
            summary_1["source_record_ids_accounted"]
            == summary_2["source_record_ids_accounted"]
        )


# ── Malformed lines logged not dropped ──────────────────────────────────


class TestMalformedLineHandling:
    def test_malformed_line_logged_not_dropped(
        self,
        sample_feedbackstore,
        run_migration,
        tmp_path: Path,
    ) -> None:
        """Add a deliberately malformed JSON line; verify it's logged.

        The malformed line must:
          - Be added to mapping_warnings (NOT silently dropped).
          - Increment metrics.malformed_lines counter.
          - NOT be added to source_record_ids_accounted (no record_id for
            unparseable line — but the warning preserves line+file).
        """
        # Append a malformed line to one bucket.
        target_bucket = sample_feedbackstore / "buckets" / "screenplay" / "cli.jsonl"
        original = target_bucket.read_text(encoding="utf-8")
        # Append a clearly malformed JSON line (missing closing brace).
        target_bucket.write_text(
            original + '{"skill_id": "screenplay", broken\n', encoding="utf-8"
        )
        # Run dry-run with explicit --source so it picks up the modified fixture.
        out_path = tmp_path / "report.json"
        result, summary = run_migration(
            "--source", str(sample_feedbackstore),
            "--out", str(out_path),
        )
        assert result.returncode == 0
        # Malformed lines counter incremented.
        assert summary["metrics"]["malformed_lines"] >= 1
        # At least one mapping warning references the malformed line.
        warnings = summary["metrics"]["mapping_warnings"]
        parse_warnings = [w for w in warnings if w.get("field") == "_parse"]
        assert len(parse_warnings) >= 1, (
            "expected ≥1 _parse mapping warning, "
            f"got {len(parse_warnings)} (all warnings: {warnings})"
        )
        # The warning should reference the file + line number.
        w = parse_warnings[0]
        assert "cli.jsonl" in w.get("source_file", "")
        assert isinstance(w.get("line"), int)
