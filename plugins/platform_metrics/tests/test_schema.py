"""Tests for plugins.platform_metrics.schema (DATA-01 + DATA-02 + DATA-03).

Phase 42 Plan 01 Task 2 — TDD RED: tests assert the contract that
schema.py must satisfy. All 10 fail until the GREEN step ships
PlatformMetrics + FeedbackRecordExtension + TuningSuggestion +
MetricTrigger.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError


_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.py"


# ──────────────────────────────────────────────────────────────────────────
# Test 1: PlatformMetrics builds with valid inputs
# ──────────────────────────────────────────────────────────────────────────


def test_platform_metrics_valid() -> None:
    """PlatformMetrics accepts valid inputs + preserves all fields."""
    from plugins.platform_metrics.schema import PlatformMetrics

    ts = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    pm = PlatformMetrics(
        platform="douyin",
        variant_id="v1",
        completion_rate=0.85,
        hook_dropoff_rate=0.12,
        engagement_rate=0.05,
        save_rate=0.03,
        comment_rate=0.01,
        fetched_at=ts,
    )
    assert pm.platform == "douyin"
    assert pm.variant_id == "v1"
    assert pm.completion_rate == pytest.approx(0.85)
    assert pm.hook_dropoff_rate == pytest.approx(0.12)
    assert pm.engagement_rate == pytest.approx(0.05)
    assert pm.save_rate == pytest.approx(0.03)
    assert pm.comment_rate == pytest.approx(0.01)
    assert pm.fetched_at == ts


# ──────────────────────────────────────────────────────────────────────────
# Test 2: 5 metric fields reject out-of-range values
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "field,value",
    [
        ("completion_rate", -0.01),
        ("completion_rate", 1.5),
        ("hook_dropoff_rate", -0.5),
        ("hook_dropoff_rate", 2.0),
        ("engagement_rate", -0.01),
        ("engagement_rate", 1.01),
        ("save_rate", -0.001),
        ("save_rate", 1.0001),
        ("comment_rate", -0.1),
        ("comment_rate", 1.5),
    ],
)
def test_platform_metrics_range_clamped(field: str, value: float) -> None:
    """Each of the 5 metric fields rejects values outside [0.0, 1.0]."""
    from plugins.platform_metrics.schema import PlatformMetrics

    base = {
        "platform": "douyin",
        "variant_id": "v1",
        "completion_rate": 0.5,
        "hook_dropoff_rate": 0.2,
        "engagement_rate": 0.05,
        "save_rate": 0.03,
        "comment_rate": 0.01,
        "fetched_at": datetime(2026, 6, 27, tzinfo=timezone.utc),
    }
    base[field] = value
    with pytest.raises(ValidationError):
        PlatformMetrics(**base)


# ──────────────────────────────────────────────────────────────────────────
# Test 3: platform Literal rejects unsupported platforms
# ──────────────────────────────────────────────────────────────────────────


def test_platform_metrics_invalid_platform() -> None:
    """platform must be one of the 7 supported values."""
    from plugins.platform_metrics.schema import PlatformMetrics

    with pytest.raises(ValidationError):
        PlatformMetrics(
            platform="Twitter",
            variant_id="v1",
            completion_rate=0.5,
            hook_dropoff_rate=0.2,
            engagement_rate=0.05,
            save_rate=0.03,
            comment_rate=0.01,
            fetched_at=datetime(2026, 6, 27, tzinfo=timezone.utc),
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 4: variant_id is required (FK to variants[].source_master_hash)
# ──────────────────────────────────────────────────────────────────────────


def test_platform_metrics_missing_variant_id() -> None:
    """variant_id is required — must raise ValidationError if absent."""
    from plugins.platform_metrics.schema import PlatformMetrics

    with pytest.raises(ValidationError):
        PlatformMetrics(
            platform="douyin",
            # variant_id intentionally omitted
            completion_rate=0.5,
            hook_dropoff_rate=0.2,
            engagement_rate=0.05,
            save_rate=0.03,
            comment_rate=0.01,
            fetched_at=datetime(2026, 6, 27, tzinfo=timezone.utc),
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 5: FeedbackRecordExtension composition with feedback_id FK
# ──────────────────────────────────────────────────────────────────────────


def test_feedback_record_extension_composition() -> None:
    """FeedbackRecordExtension composes via feedback_id string FK."""
    from plugins.platform_metrics.schema import (
        FeedbackRecordExtension,
        PlatformMetrics,
    )

    ts = datetime(2026, 6, 27, tzinfo=timezone.utc)
    douyin_pm = PlatformMetrics(
        platform="douyin",
        variant_id="v1",
        completion_rate=0.8,
        hook_dropoff_rate=0.15,
        engagement_rate=0.06,
        save_rate=0.04,
        comment_rate=0.02,
        fetched_at=ts,
    )
    kuaishou_pm = PlatformMetrics(
        platform="kuaishou",
        variant_id="v2",
        completion_rate=0.75,
        hook_dropoff_rate=0.18,
        engagement_rate=0.04,
        save_rate=0.03,
        comment_rate=0.01,
        fetched_at=ts,
    )

    ext = FeedbackRecordExtension(
        feedback_id="12345_abcdef",
        platform_metrics={"douyin": douyin_pm, "kuaishou": kuaishou_pm},
        ts_created=ts,
    )
    assert ext.feedback_id == "12345_abcdef"
    assert len(ext.platform_metrics) == 2
    assert isinstance(ext.platform_metrics["douyin"], PlatformMetrics)
    assert ext.platform_metrics["kuaishou"].completion_rate == pytest.approx(0.75)


# ──────────────────────────────────────────────────────────────────────────
# Test 6: SCOPE DISCIPLINE — zero imports of agent.feedback_schema
# ──────────────────────────────────────────────────────────────────────────


def test_feedback_record_extension_does_not_import_v6() -> None:
    """schema.py MUST NOT import agent.feedback_schema (Option A discipline).

    Composition via string FK only — never an import of the v6.0
    FeedbackRecord class. This is the load-bearing scope-discipline
    invariant for Phase 42 (DATA-02).
    """
    result = subprocess.run(
        ["grep", "-c", "from agent.feedback_schema", str(_SCHEMA_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    count = int(result.stdout.strip()) if result.stdout.strip() else 0
    assert count == 0, (
        f"Scope discipline violated: schema.py imports "
        f"agent.feedback_schema {count} time(s). Option A mandates "
        f"composition via feedback_id string FK, NOT class import."
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 7: FeedbackRecordExtension with empty metrics is valid
# ──────────────────────────────────────────────────────────────────────────


def test_feedback_record_extension_empty_metrics_ok() -> None:
    """Extension with empty platform_metrics dict is valid.

    DATA-02 backward-compat: a v6.0 record may have no platform data yet.
    The extension is a separate sibling document — empty metrics is valid
    (unusual but not erroneous).
    """
    from plugins.platform_metrics.schema import FeedbackRecordExtension

    ts = datetime(2026, 6, 27, tzinfo=timezone.utc)
    ext = FeedbackRecordExtension(
        feedback_id="abc",
        platform_metrics={},
        ts_created=ts,
    )
    assert ext.feedback_id == "abc"
    assert ext.platform_metrics == {}


# ──────────────────────────────────────────────────────────────────────────
# Test 8: TuningSuggestion round-trip via model_dump_json
# ──────────────────────────────────────────────────────────────────────────


def test_tuning_suggestion_schema() -> None:
    """TuningSuggestion builds + round-trips through JSON cleanly."""
    from plugins.platform_metrics.schema import MetricTrigger, TuningSuggestion

    suggestion = TuningSuggestion(
        suggestion_id="urban-fantasy-light-01_high_hook_dropoff_2026-06-27T12-00-00Z",
        formula_id="urban-fantasy-light-01",
        trigger=MetricTrigger.HIGH_HOOK_DROPOFF,
        observed_metric=0.32,
        threshold=0.20,
        suggested_action="加 hook 强度 — 当前 hook_pattern=contrast 建议升级 emotional_peak",
        rationale="hook_dropoff 0.32 > threshold 0.20: 开头 3s hook 强度不足",
        evidence=["fb_rec_001", "variant_v1"],
        status="pending",
        ts_queued="2026-06-27T12:00:00+00:00",
    )

    # Round-trip via JSON.
    dumped = suggestion.model_dump_json()
    restored = TuningSuggestion.model_validate_json(dumped)
    assert restored.suggestion_id == suggestion.suggestion_id
    assert restored.formula_id == "urban-fantasy-light-01"
    assert restored.trigger == MetricTrigger.HIGH_HOOK_DROPOFF
    assert restored.status == "pending"
    assert restored.observed_metric == pytest.approx(0.32)
    assert restored.threshold == pytest.approx(0.20)


# ──────────────────────────────────────────────────────────────────────────
# Test 9: TuningSuggestion status Literal validation
# ──────────────────────────────────────────────────────────────────────────


def test_tuning_suggestion_invalid_status() -> None:
    """status Literal must be pending / applied / rejected."""
    from plugins.platform_metrics.schema import MetricTrigger, TuningSuggestion

    with pytest.raises(ValidationError):
        TuningSuggestion(
            suggestion_id="x",
            formula_id="x",
            trigger=MetricTrigger.LOW_COMPLETION,
            observed_metric=0.2,
            threshold=0.3,
            suggested_action="bump completion",
            rationale="test",
            status="bogus",  # invalid
            ts_queued="2026-06-27T12:00:00+00:00",
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 10: MetricTrigger enum has the 4 documented values
# ──────────────────────────────────────────────────────────────────────────


def test_metric_trigger_enum() -> None:
    """MetricTrigger has 4 values, each matching its identifier."""
    from plugins.platform_metrics.schema import MetricTrigger

    members = {m.name: m.value for m in MetricTrigger}
    assert set(members.keys()) == {
        "HIGH_HOOK_DROPOFF",
        "HIGH_COMPLETION_LOW_ENGAGEMENT",
        "LOW_COMPLETION",
        "LOW_SAVE_RATE",
    }
    assert members["HIGH_HOOK_DROPOFF"] == "high_hook_dropoff"
    assert (
        members["HIGH_COMPLETION_LOW_ENGAGEMENT"]
        == "high_completion_low_engagement"
    )
    assert members["LOW_COMPLETION"] == "low_completion"
    assert members["LOW_SAVE_RATE"] == "low_save_rate"
