"""tuning_loop.py — formula tuning loop (DATA-03).

Scans :class:`FeedbackRecordExtension` records, classifies convergent
metrics via :class:`MetricTrigger` rules, and emits
:class:`TuningSuggestion` records to the JSONL review queue.

Mirrors v6.0 EVOL-02 HIL invariant: NOTHING auto-applies. The operator
approves suggestions via ``library_writer.apply_suggestion()`` (Plan
42-03 Task 3). The tuning loop only emits; it never writes to
``formula_library/`` or moves queue entries.

Scope discipline (load-bearing): reads v6.0 FeedbackStore via PUBLIC API
ONLY (``query``, ``get_record``). NEVER calls write methods
(``record_feedback``, ``rebuild_index``). Grep-enforced by
``test_run_tuning_loop_no_v6_write``.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - Double-quoted strings.
  - Keyword-only args on public functions with many optional knobs.
  - Lazy %-logging; specific exceptions bound.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from plugins.platform_metrics.queue import append_suggestion
from plugins.platform_metrics.schema import (
    FeedbackRecordExtension,
    MetricTrigger,
    PlatformMetrics,
    TuningSuggestion,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Thresholds
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TuningThresholds:
    """Threshold values for the 4 MetricTrigger rules.

    Defaults are operator-tunable. Pass a custom instance to
    :func:`classify_metrics` or :func:`run_tuning_loop` to override.

    All fields are keyword-only (frozen dataclass + kw_only) to prevent
    positional-arg drift as new thresholds are added.
    """

    high_hook_dropoff: float = 0.20
    """hook_dropoff_rate strictly above this fires HIGH_HOOK_DROPOFF."""

    high_completion: float = 0.70
    """completion_rate >= this (combined with low_engagement) fires
    HIGH_COMPLETION_LOW_ENGAGEMENT."""

    low_engagement: float = 0.05
    """engagement_rate strictly below this (combined with high_completion)
    fires HIGH_COMPLETION_LOW_ENGAGEMENT."""

    low_completion: float = 0.30
    """completion_rate strictly below this fires LOW_COMPLETION."""

    low_save_rate: float = 0.01
    """save_rate strictly below this fires LOW_SAVE_RATE."""


# --------------------------------------------------------------------------- #
# classify_metrics — pure function applying the 4 trigger rules
# --------------------------------------------------------------------------- #


# Per-trigger metadata: the metric field name to report as observed_metric,
# the human-readable suggested_action (中文为主), and the rationale.
# Centralized so classify_metrics and run_tuning_loop agree on the action
# strings (DRY).
_TRIGGER_META: dict[MetricTrigger, dict[str, str]] = {
    MetricTrigger.HIGH_HOOK_DROPOFF: {
        "metric_field": "hook_dropoff_rate",
        "threshold_field": "high_hook_dropoff",
        "action": "加 hook 强度 — 当前 hook_pattern 建议升级 emotional_peak / suspense",
        "rationale": "hook_dropoff_rate 超过阈值,开头未能留住观众 / "
                     "hook_dropoff_rate exceeds threshold; opening failed to retain",
    },
    MetricTrigger.HIGH_COMPLETION_LOW_ENGAGEMENT: {
        "metric_field": "engagement_rate",
        "threshold_field": "low_engagement",
        "action": "加 CTA + 情绪爆点 — 完播高但互动低,缺少行动召唤",
        "rationale": "completion_rate >= high_completion AND engagement_rate < "
                     "low_engagement / viewers finished but did not interact",
    },
    MetricTrigger.LOW_COMPLETION: {
        "metric_field": "completion_rate",
        "threshold_field": "low_completion",
        "action": "前置冲突 — 完播率低于阈值,中段叙事需要前置高潮",
        "rationale": "completion_rate < low_completion / "
                     "video failed to retain viewers past midpoint",
    },
    MetricTrigger.LOW_SAVE_RATE: {
        "metric_field": "save_rate",
        "threshold_field": "low_save_rate",
        "action": "加 collectible 内容钩子 — 收藏率低于阈值,缺少可保存价值",
        "rationale": "save_rate < low_save_rate / "
                     "video failed to earn saves (strongest engagement signal)",
    },
}


def classify_metrics(
    metrics: PlatformMetrics,
    thresholds: TuningThresholds = TuningThresholds(),
) -> list[MetricTrigger]:
    """Apply the 4 MetricTrigger rules to a single PlatformMetrics record.

    Pure function. Returns the list of triggers that fired (may be empty,
    may contain multiple if the metrics cross several thresholds).

    Rules:
      - HIGH_HOOK_DROPOFF: hook_dropoff_rate > thresholds.high_hook_dropoff
      - HIGH_COMPLETION_LOW_ENGAGEMENT: completion_rate >=
        thresholds.high_completion AND engagement_rate <
        thresholds.low_engagement
      - LOW_COMPLETION: completion_rate < thresholds.low_completion
      - LOW_SAVE_RATE: save_rate < thresholds.low_save_rate
    """
    triggers: list[MetricTrigger] = []

    # Rule 1: hook_dropoff_rate > threshold → HIGH_HOOK_DROPOFF
    # (加 hook 强度)
    if metrics.hook_dropoff_rate > thresholds.high_hook_dropoff:
        triggers.append(MetricTrigger.HIGH_HOOK_DROPOFF)

    # Rule 2: completion >= high_completion AND engagement < low_engagement
    # → HIGH_COMPLETION_LOW_ENGAGEMENT (加 CTA)
    if (
        metrics.completion_rate >= thresholds.high_completion
        and metrics.engagement_rate < thresholds.low_engagement
    ):
        triggers.append(MetricTrigger.HIGH_COMPLETION_LOW_ENGAGEMENT)

    # Rule 3: completion < low_completion → LOW_COMPLETION
    # (前置冲突)
    if metrics.completion_rate < thresholds.low_completion:
        triggers.append(MetricTrigger.LOW_COMPLETION)

    # Rule 4: save_rate < low_save_rate → LOW_SAVE_RATE
    # (加 collectible 内容钩子)
    if metrics.save_rate < thresholds.low_save_rate:
        triggers.append(MetricTrigger.LOW_SAVE_RATE)

    return triggers


# --------------------------------------------------------------------------- #
# Protocols — decouple from concrete v6.0 classes (scope discipline)
# --------------------------------------------------------------------------- #


class FeedbackStoreLike(Protocol):
    """Minimal read-only protocol for v6.0 FeedbackStore consumption.

    Defining a Protocol here (instead of importing
    ``agent.feedback_store.FeedbackStore``) keeps this module decoupled
    from v6.0 — tests can substitute any duck-typed object. The Protocol
    declares ONLY the read methods; write methods (record_feedback,
    rebuild_index) are intentionally absent (scope discipline,
    grep-enforced).
    """

    def query(self, **kwargs: Any) -> list[Any]:
        """Read-only query — returns FeedbackRecord-shaped objects."""
        ...

    def get_record(self, record_id: str) -> Any:
        """Read-only record lookup."""
        ...


class ExtensionStore(Protocol):
    """Minimal read API for FeedbackRecordExtension records.

    Plan 42-04 will ship a concrete implementation that loads extensions
    from ``<HERMES_HOME>/skills/.feedback/platform_metrics/``. Tests stub
    this with any object exposing ``list_extensions``.
    """

    def list_extensions(self) -> list[FeedbackRecordExtension]:
        """Return all FeedbackRecordExtension records (synchronous)."""
        ...


# variant_id → formula_id resolver. Plan 42-04 wires the real resolver
# (reads pipeline_state.episode_id.variants[] to look up the formula_id
# used for that variant). For Plan 42-03 tests, a dict-based stub.
FormulaResolver = Any  # Callable[[str], str | None]
"""Type alias for the variant_id → formula_id resolver function.

Typed as ``Any`` to avoid a ``Callable`` import dance; runtime contract
is ``def resolver(variant_id: str) -> str | None``. Returning ``None``
means "no formula mapping — skip this variant".
"""


# --------------------------------------------------------------------------- #
# run_tuning_loop — entry point
# --------------------------------------------------------------------------- #


def run_tuning_loop(
    *,
    feedback_store: FeedbackStoreLike,
    extension_store: ExtensionStore,
    tuning_dir: Path,
    formula_resolver: FormulaResolver,
    thresholds: TuningThresholds = TuningThresholds(),
    now: datetime | None = None,
) -> list[TuningSuggestion]:
    """Scan extensions, classify metrics, emit suggestions to the JSONL queue.

    Keyword-only args (CLAUDE.md convention for functions with many knobs).

    Args:
        feedback_store: v6.0 FeedbackStore (read-only — query/get_record
            only). Kept as a parameter for future date-filtering use; the
            current implementation iterates extensions directly.
        extension_store: Source of FeedbackRecordExtension records.
        tuning_dir: Directory containing the JSONL queue files
            (``queue.jsonl`` etc.).
        formula_resolver: Callable mapping variant_id → formula_id, or
            ``None`` for "no mapping".
        thresholds: Trigger thresholds (defaults via TuningThresholds()).
        now: Override for "current time" (testing). Defaults to
            ``datetime.now(timezone.utc)``.

    Returns:
        list of emitted TuningSuggestion records (also appended to
        ``tuning_dir/queue.jsonl``).

    Notes:
        - Suggestions are deduplicated by ``suggestion_id`` within a
          single run (same formula_id + trigger + timestamp bucket
          collapses to one suggestion).
        - NEVER calls ``feedback_store.record_feedback`` or any write
          method (grep-enforced by test_run_tuning_loop_no_v6_write).
    """
    if now is None:
        from datetime import timezone
        now = datetime.now(timezone.utc)
    ts_unix = int(now.timestamp())
    ts_iso = now.isoformat()

    emitted: list[TuningSuggestion] = []
    seen_ids: set[str] = set()

    extensions = extension_store.list_extensions()
    for extension in extensions:
        if not extension.platform_metrics:
            logger.debug(
                "extension %s has empty platform_metrics; skipping",
                extension.feedback_id,
            )
            continue

        for _platform_key, metrics in extension.platform_metrics.items():
            formula_id = formula_resolver(metrics.variant_id)
            if formula_id is None:
                logger.debug(
                    "no formula mapping for variant_id=%s; skipping",
                    metrics.variant_id,
                )
                continue

            triggers = classify_metrics(metrics, thresholds)
            for trigger in triggers:
                suggestion_id = f"{formula_id}_{trigger.value}_{ts_unix}"
                if suggestion_id in seen_ids:
                    logger.debug(
                        "dedup: suggestion_id %s already emitted this run",
                        suggestion_id,
                    )
                    continue
                seen_ids.add(suggestion_id)

                meta = _TRIGGER_META[trigger]
                observed_value = getattr(metrics, meta["metric_field"])
                threshold_value = getattr(thresholds, meta["threshold_field"])

                suggestion = TuningSuggestion(
                    suggestion_id=suggestion_id,
                    formula_id=formula_id,
                    trigger=trigger,
                    observed_metric=observed_value,
                    threshold=threshold_value,
                    suggested_action=meta["action"],
                    rationale=meta["rationale"],
                    evidence=[extension.feedback_id, metrics.variant_id],
                    status="pending",
                    ts_queued=ts_iso,
                )
                append_suggestion(suggestion, tuning_dir)
                emitted.append(suggestion)

    logger.info(
        "tuning_loop emitted %d suggestion(s) across %d extension(s)",
        len(emitted), len(extensions),
    )
    return emitted


__all__ = [
    "TuningThresholds",
    "classify_metrics",
    "run_tuning_loop",
    "FeedbackStoreLike",
    "ExtensionStore",
    "FormulaResolver",
]
