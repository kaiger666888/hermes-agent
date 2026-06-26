"""Tests for plugins.platform_metrics.tuning_loop (DATA-03).

Phase 42 Plan 03 Task 2 — TDD RED: tests assert the classify_metrics +
run_tuning_loop contract. 13 tests cover threshold defaults, the 4
trigger rules (including multi-trigger + override), and the run loop's
emit + dedup + no-v6-write invariants.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


# ──────────────────────────────────────────────────────────────────────────
# Fixture helpers
# ──────────────────────────────────────────────────────────────────────────


def _make_metrics(**overrides: Any) -> "object":
    """Build a PlatformMetrics fixture with normal-range defaults.

    Defaults keep all metrics in the "no trigger" band so tests can
    override only the field(s) they want to push past a threshold.
    """
    from plugins.platform_metrics.schema import PlatformMetrics

    defaults: dict[str, Any] = {
        "platform": "douyin",
        "variant_id": "v1",
        "completion_rate": 0.50,
        "hook_dropoff_rate": 0.10,
        "engagement_rate": 0.10,
        "save_rate": 0.02,
        "comment_rate": 0.01,
        "fetched_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return PlatformMetrics(**defaults)


# ──────────────────────────────────────────────────────────────────────────
# Test 1: default thresholds
# ──────────────────────────────────────────────────────────────────────────


def test_default_thresholds() -> None:
    """TuningThresholds() has the 5 documented defaults."""
    from plugins.platform_metrics.tuning_loop import TuningThresholds

    t = TuningThresholds()
    assert t.high_hook_dropoff == pytest.approx(0.20)
    assert t.high_completion == pytest.approx(0.70)
    assert t.low_engagement == pytest.approx(0.05)
    assert t.low_completion == pytest.approx(0.30)
    assert t.low_save_rate == pytest.approx(0.01)


# ──────────────────────────────────────────────────────────────────────────
# Tests 2-8: classify_metrics trigger rules
# ──────────────────────────────────────────────────────────────────────────


def test_classify_high_hook_dropoff() -> None:
    """hook_dropoff_rate > 0.20 → HIGH_HOOK_DROPOFF."""
    from plugins.platform_metrics.tuning_loop import classify_metrics
    from plugins.platform_metrics.schema import MetricTrigger

    m = _make_metrics(hook_dropoff_rate=0.32)
    triggers = classify_metrics(m)
    assert MetricTrigger.HIGH_HOOK_DROPOFF in triggers


def test_classify_high_completion_low_engagement() -> None:
    """completion >= 0.70 AND engagement < 0.05 → HIGH_COMPLETION_LOW_ENGAGEMENT."""
    from plugins.platform_metrics.tuning_loop import classify_metrics
    from plugins.platform_metrics.schema import MetricTrigger

    m = _make_metrics(completion_rate=0.85, engagement_rate=0.02)
    triggers = classify_metrics(m)
    assert MetricTrigger.HIGH_COMPLETION_LOW_ENGAGEMENT in triggers


def test_classify_high_completion_high_engagement_no_trigger() -> None:
    """completion >= 0.70 AND engagement >= 0.05 → no HIGH_COMPLETION_LOW_ENGAGEMENT."""
    from plugins.platform_metrics.tuning_loop import classify_metrics
    from plugins.platform_metrics.schema import MetricTrigger

    m = _make_metrics(completion_rate=0.85, engagement_rate=0.10)
    triggers = classify_metrics(m)
    assert MetricTrigger.HIGH_COMPLETION_LOW_ENGAGEMENT not in triggers


def test_classify_low_completion() -> None:
    """completion < 0.30 → LOW_COMPLETION."""
    from plugins.platform_metrics.tuning_loop import classify_metrics
    from plugins.platform_metrics.schema import MetricTrigger

    m = _make_metrics(completion_rate=0.20)
    triggers = classify_metrics(m)
    assert MetricTrigger.LOW_COMPLETION in triggers


def test_classify_low_save_rate() -> None:
    """save_rate < 0.01 → LOW_SAVE_RATE."""
    from plugins.platform_metrics.tuning_loop import classify_metrics
    from plugins.platform_metrics.schema import MetricTrigger

    m = _make_metrics(save_rate=0.005)
    triggers = classify_metrics(m)
    assert MetricTrigger.LOW_SAVE_RATE in triggers


def test_classify_multiple_triggers() -> None:
    """Metrics hitting multiple thresholds return multiple triggers."""
    from plugins.platform_metrics.tuning_loop import classify_metrics
    from plugins.platform_metrics.schema import MetricTrigger

    # hook_dropoff > 0.20 AND completion < 0.30.
    m = _make_metrics(hook_dropoff_rate=0.40, completion_rate=0.20)
    triggers = classify_metrics(m)
    assert MetricTrigger.HIGH_HOOK_DROPOFF in triggers
    assert MetricTrigger.LOW_COMPLETION in triggers


def test_classify_no_triggers() -> None:
    """All metrics in normal range → empty trigger list."""
    from plugins.platform_metrics.tuning_loop import classify_metrics

    m = _make_metrics()  # defaults are all in normal range
    triggers = classify_metrics(m)
    assert triggers == []


def test_classify_threshold_override() -> None:
    """Custom thresholds change which metrics trigger."""
    from plugins.platform_metrics.tuning_loop import (
        TuningThresholds,
        classify_metrics,
    )
    from plugins.platform_metrics.schema import MetricTrigger

    # Default threshold 0.20 would fire on 0.32; raise it to 0.50.
    custom = TuningThresholds(high_hook_dropoff=0.50)
    m = _make_metrics(hook_dropoff_rate=0.32)
    triggers = classify_metrics(m, custom)
    assert MetricTrigger.HIGH_HOOK_DROPOFF not in triggers


# ──────────────────────────────────────────────────────────────────────────
# Tests 10-13: run_tuning_loop
# ──────────────────────────────────────────────────────────────────────────


class _StubExtensionStore:
    """Minimal ExtensionStore stub returning a fixed list of extensions."""

    def __init__(self, extensions: list[Any]) -> None:
        self._extensions = extensions

    def list_extensions(self) -> list[Any]:
        return list(self._extensions)


def _make_extension(
    *,
    feedback_id: str = "fb_1",
    platform_metrics: dict[str, Any] | None = None,
) -> "object":
    """Build a FeedbackRecordExtension fixture."""
    from plugins.platform_metrics.schema import FeedbackRecordExtension

    if platform_metrics is None:
        platform_metrics = {}
    return FeedbackRecordExtension(
        feedback_id=feedback_id,
        platform_metrics=platform_metrics,
        ts_created=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )


def test_run_tuning_loop_emits_suggestions(tmp_path: Path) -> None:
    """run_tuning_loop emits suggestions for metrics crossing thresholds."""
    from plugins.platform_metrics.tuning_loop import run_tuning_loop

    # Two extensions, each with one platform hitting HIGH_HOOK_DROPOFF.
    m1 = _make_metrics(variant_id="v1", hook_dropoff_rate=0.40)
    m2 = _make_metrics(variant_id="v2", hook_dropoff_rate=0.35)
    ext1 = _make_extension(
        feedback_id="fb_1",
        platform_metrics={"douyin": m1},
    )
    ext2 = _make_extension(
        feedback_id="fb_2",
        platform_metrics={"douyin": m2},
    )
    ext_store = _StubExtensionStore([ext1, ext2])
    fb_store = MagicMock()
    resolver_map = {"v1": "urban-fantasy-light-01", "v2": "mystery-twist-light-01"}
    resolver = lambda vid: resolver_map.get(vid)  # noqa: E731

    fixed_now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    emitted = run_tuning_loop(
        feedback_store=fb_store,
        extension_store=ext_store,
        tuning_dir=tmp_path,
        formula_resolver=resolver,
        now=fixed_now,
    )

    assert len(emitted) == 2
    ids = {e.formula_id for e in emitted}
    assert ids == {"urban-fantasy-light-01", "mystery-twist-light-01"}

    # Queue file has both suggestions.
    queue_path = tmp_path / "queue.jsonl"
    assert queue_path.exists()
    assert len(queue_path.read_text(encoding="utf-8").strip().splitlines()) == 2


def test_run_tuning_loop_skips_extensions_without_metrics(tmp_path: Path) -> None:
    """Extensions with empty platform_metrics produce no suggestions."""
    from plugins.platform_metrics.tuning_loop import run_tuning_loop

    ext_empty = _make_extension(feedback_id="fb_empty", platform_metrics={})
    # And one extension that DOES have metrics, to prove the loop didn't
    # just abort on the empty one.
    m = _make_metrics(variant_id="v1", hook_dropoff_rate=0.40)
    ext_with = _make_extension(
        feedback_id="fb_with", platform_metrics={"douyin": m}
    )
    ext_store = _StubExtensionStore([ext_empty, ext_with])
    fb_store = MagicMock()
    resolver = lambda vid: "urban-fantasy-light-01"  # noqa: E731

    fixed_now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    emitted = run_tuning_loop(
        feedback_store=fb_store,
        extension_store=ext_store,
        tuning_dir=tmp_path,
        formula_resolver=resolver,
        now=fixed_now,
    )

    assert len(emitted) == 1
    assert emitted[0].evidence[0] == "fb_with"


def test_run_tuning_loop_dedup_suggestion_ids(tmp_path: Path) -> None:
    """Same formula_id + trigger + timestamp bucket → one suggestion (dedup)."""
    from plugins.platform_metrics.tuning_loop import run_tuning_loop

    # Two extensions, both pointing at the SAME formula_id via resolver,
    # both with the SAME trigger (HIGH_HOOK_DROPOFF). Fixed now means
    # the suggestion_id bucket is identical → dedup should collapse them.
    m1 = _make_metrics(variant_id="v1", hook_dropoff_rate=0.40)
    m2 = _make_metrics(variant_id="v2", hook_dropoff_rate=0.50)
    ext1 = _make_extension(
        feedback_id="fb_1", platform_metrics={"douyin": m1}
    )
    ext2 = _make_extension(
        feedback_id="fb_2", platform_metrics={"douyin": m2}
    )
    ext_store = _StubExtensionStore([ext1, ext2])
    fb_store = MagicMock()
    # Both variants resolve to the same formula_id.
    resolver = lambda vid: "urban-fantasy-light-01"  # noqa: E731

    fixed_now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    emitted = run_tuning_loop(
        feedback_store=fb_store,
        extension_store=ext_store,
        tuning_dir=tmp_path,
        formula_resolver=resolver,
        now=fixed_now,
    )

    # Without dedup, this would be 2. With dedup on suggestion_id, it's 1.
    assert len(emitted) == 1
    assert emitted[0].formula_id == "urban-fantasy-light-01"


def test_run_tuning_loop_no_v6_write() -> None:
    """Scope-discipline grep: tuning_loop.py invokes no v6 write method.

    The loop must NEVER *call* v6.0 FeedbackStore write methods. We check
    for invocation patterns (``.record_feedback(``, ``feedback_store.<write>``)
    rather than bare identifiers — the forbidden names legitimately appear
    in docstrings explaining the invariant.
    """
    import re

    source = (
        Path(__file__).resolve().parent.parent / "tuning_loop.py"
    ).read_text(encoding="utf-8")
    # Match actual invocations: `.record_feedback(` or `.rebuild_index(`.
    # A bare mention in a docstring (no leading dot + paren) is allowed.
    forbidden_calls = [
        r"\.record_feedback\s*\(",
        r"\.rebuild_index\s*\(",
    ]
    for pattern in forbidden_calls:
        matches = re.findall(pattern, source)
        assert not matches, (
            f"scope discipline violation: tuning_loop.py invokes a v6.0 "
            f"write method via pattern {pattern!r} — only query / get_record "
            f"are permitted (found {len(matches)} call(s))"
        )
    # Also assert no import of v6 write modules (only the Protocol-based
    # read API is permitted). Mirror Plan 42-01's
    # test_feedback_record_extension_does_not_import_v6 pattern.
    assert "from agent.feedback_store import" not in source, (
        "scope discipline: tuning_loop.py imports agent.feedback_store "
        "directly — use the FeedbackStoreLike Protocol instead"
    )
    assert "from agent.feedback_schema import" not in source, (
        "scope discipline: tuning_loop.py imports agent.feedback_schema "
        "directly — FeedbackRecordExtension is the local schema"
    )
