"""Tests for the FeedbackRecord + OutputSnapshot Pydantic schema (INGEST-04).

Verifies field-level validation: bad verdict, unknown skill_id, naive
datetime, malformed sha256, source-enum cross-source parity, and
auto-discovered _KNOWN_EXPERT_IDS coverage.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pydantic
import pytest

from agent.feedback_schema import (
    FeedbackRecord,
    OutputSnapshot,
    _KNOWN_EXPERT_IDS,
)


def _valid_snapshot(**overrides) -> OutputSnapshot:
    """Build a valid OutputSnapshot for tests; override fields as needed."""
    base = {
        "sha256": "0" * 64,
        "output_text": "sample assistant output",
        "prompt": "user prompt",
        "model": "test-model",
        "provider": "openai",
        "api_mode": "chat_completions",
        "params": {"max_tokens": 1024},
        "captured_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return OutputSnapshot(**base)


def _valid_record(**overrides) -> FeedbackRecord:
    """Build a valid FeedbackRecord for tests; override fields as needed."""
    base = {
        "skill_id": "screenplay",
        "expert_id": "screenplay",
        "source": "cli",
        "verdict": "good",
        "correction": "x",
        "output_snapshot": _valid_snapshot(),
        "ts": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return FeedbackRecord(**base)


class TestFeedbackRecordSchema:
    """Pydantic field-level validation for FeedbackRecord + OutputSnapshot."""

    def test_accepts_valid_record(self):
        record = _valid_record()
        assert record.skill_id == "screenplay"
        assert record.source == "cli"
        assert record.verdict == "good"

    def test_rejects_bad_verdict(self):
        with pytest.raises(pydantic.ValidationError) as exc_info:
            _valid_record(verdict="excellent")
        errors = exc_info.value.errors()
        # at least one error must reference the verdict field
        verdict_errors = [e for e in errors if "verdict" in e.get("loc", ())]
        assert verdict_errors, f"expected verdict field error, got: {errors}"

    def test_rejects_unknown_skill_id(self):
        with pytest.raises(pydantic.ValidationError) as exc_info:
            _valid_record(skill_id="not_a_skill")
        errors = exc_info.value.errors()
        skill_errors = [e for e in errors if "skill_id" in e.get("loc", ())]
        assert skill_errors, f"expected skill_id field error, got: {errors}"
        # the error message should mention known skills so operators can fix it
        msg = str(skill_errors[0].get("msg", ""))
        assert "known" in msg.lower() or "movie-expert" in msg.lower(), (
            f"error message should list known skills, got: {msg}"
        )

    def test_rejects_unknown_expert_id(self):
        with pytest.raises(pydantic.ValidationError) as exc_info:
            _valid_record(expert_id="not_a_skill")
        errors = exc_info.value.errors()
        expert_errors = [e for e in errors if "expert_id" in e.get("loc", ())]
        assert expert_errors, f"expected expert_id field error, got: {errors}"

    def test_rejects_naive_datetime(self):
        with pytest.raises(pydantic.ValidationError) as exc_info:
            _valid_record(ts=datetime(2026, 1, 1))  # no tzinfo
        errors = exc_info.value.errors()
        ts_errors = [e for e in errors if "ts" in e.get("loc", ())]
        assert ts_errors, f"expected ts field error, got: {errors}"
        msg = str(ts_errors[0].get("msg", "")).lower()
        assert "timezone" in msg or "tz" in msg, (
            f"error should mention timezone requirement, got: {msg}"
        )

    def test_rejects_short_sha256(self):
        with pytest.raises(pydantic.ValidationError) as exc_info:
            _valid_snapshot(sha256="abc")
        errors = exc_info.value.errors()
        sha_errors = [e for e in errors if "sha256" in e.get("loc", ())]
        assert sha_errors, f"expected sha256 field error, got: {errors}"

    def test_normalizes_uppercase_sha256_to_lowercase(self):
        upper = "A" * 64
        snap = _valid_snapshot(sha256=upper)
        assert snap.sha256 == "a" * 64, "uppercase hex sha256 must normalize to lowercase"

    def test_rejects_non_hex_sha256(self):
        # 64 chars but contains non-hex chars
        bad = "z" * 64
        with pytest.raises(pydantic.ValidationError) as exc_info:
            _valid_snapshot(sha256=bad)
        errors = exc_info.value.errors()
        sha_errors = [e for e in errors if "sha256" in e.get("loc", ())]
        assert sha_errors, f"expected sha256 field error for non-hex, got: {errors}"

    def test_source_enum_same_schema(self):
        """All three sources produce identical JSON modulo the source field.

        This is the INGEST-04 cross-source schema parity guarantee: the
        ONLY difference between a CLI-submitted record, a kais-aigc-platform
        record, and a manually-imported record is the value of ``source``.
        """
        base_kwargs = {
            "skill_id": "screenplay",
            "expert_id": "screenplay",
            "verdict": "needs_work",
            "correction": "tighten the ending",
            "output_snapshot": _valid_snapshot(),
            "ts": datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc),
        }
        cli_record = FeedbackRecord(source="cli", **base_kwargs)
        kais_record = FeedbackRecord(source="kais_aigc", **base_kwargs)
        manual_record = FeedbackRecord(source="manual", **base_kwargs)

        cli_dump = cli_record.model_dump(mode="json")
        kais_dump = kais_record.model_dump(mode="json")
        manual_dump = manual_record.model_dump(mode="json")

        # Only the source value differs across the three dumps
        assert cli_dump["source"] == "cli"
        assert kais_dump["source"] == "kais_aigc"
        assert manual_dump["source"] == "manual"

        # Strip source and compare the rest — must be byte-identical
        for d in (cli_dump, kais_dump, manual_dump):
            d.pop("source")
        assert cli_dump == kais_dump == manual_dump, (
            "cross-source records must produce identical JSON modulo source"
        )

    def test_known_expert_ids_includes_v5_additions(self):
        """Auto-discovery must catch v3/v4/v5 additions, not just v1 frozen list.

        Guards against silently shipping with the stale 14-expert
        snapshot.py list.
        """
        required = {
            "hook_retention",       # v3 addition
            "compliance_gate",      # v3 addition
            "compliance_marketing", # v3 addition
            "lip_sync",             # v5 addition
            "cinematographer",      # v4 addition
            "screenplay",           # v1 original
        }
        missing = required - _KNOWN_EXPERT_IDS
        assert not missing, (
            f"_KNOWN_EXPERT_IDS missing expected experts: {sorted(missing)}"
        )

    def test_known_expert_ids_meets_minimum_count(self):
        """Sanity: the current expert count is at least 28."""
        assert len(_KNOWN_EXPERT_IDS) >= 28, (
            f"expected >= 28 auto-discovered experts, got {len(_KNOWN_EXPERT_IDS)}"
        )

    def test_optional_revised_output_defaults_none(self):
        record = _valid_record()
        assert record.revised_output is None
        record_with_revised = _valid_record(revised_output="improved version")
        assert record_with_revised.revised_output == "improved version"

    def test_correction_defaults_empty(self):
        """Omitting correction yields the default empty string."""
        record = FeedbackRecord(
            skill_id="screenplay",
            expert_id="screenplay",
            source="cli",
            verdict="good",
            output_snapshot=_valid_snapshot(),
            ts=datetime.now(timezone.utc),
        )
        assert record.correction == ""
