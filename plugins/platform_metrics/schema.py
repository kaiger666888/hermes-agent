"""schema.py — Pydantic v2 schemas for platform_metrics (Phase 42 DATA).

Plan 42-01 Task 2 — ships the three Pydantic schemas that anchor the
entire DATA-01..04 chain:

  - ``PlatformMetrics`` (DATA-01) — unified schema every platform adapter
    returns. 5 metric fields clamped to [0.0, 1.0].
  - ``FeedbackRecordExtension`` (DATA-02) — composes WITH v6.0
    ``FeedbackRecord`` via a ``feedback_id`` string FK. Does NOT import
    or extend ``agent.feedback_schema.FeedbackRecord`` (Option A scope
    discipline). v6.0 records remain untouched (backward-compat).
  - ``TuningSuggestion`` (DATA-03) — JSONL review queue record (mirror
    ``agent/evolution/queue.py:PatchRecord`` shape). Consumed by Plan
    42-03's ``tuning_loop.py`` + ``queue.py``.

Scope discipline (Option A — load-bearing):

  This module has ZERO imports of ``agent.feedback_schema`` or
  ``agent.feedback_store``. The composition with v6.0 records happens
  via the ``feedback_id`` STRING foreign key — the v6.0 FeedbackStore
  owns the original record, this extension is a sibling document. Test
  ``test_feedback_record_extension_does_not_import_v6`` grep-enforces
  this invariant.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - Double-quoted strings throughout.
  - Pydantic v2 syntax (``field_validator``, ``model_config``,
    ``model_validator``).
  - ``encoding="utf-8"`` on every ``open()`` / ``read_text()`` /
    ``write_text()`` (Ruff PLW1514 — no I/O in this module; kept for
    future additions).
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# ── Platform Literal ──────────────────────────────────────────────────────
#
# 7 supported platform identifiers. The first 5 (douyin / kuaishou /
# weixin_video / xiaohongshu / bilibili) are the DATA-01 platforms with
# API adapters shipped in Plan 42-02. The last 2 (红果 / 视频号) lack
# documented open APIs in v9.0 — they appear in variants[] (Phase 38
# SLICE) but adapters are deferred to V9-FUTURE-01.
#
# NOTE: these are the platform *identifiers* used in PlatformMetrics +
# adapter registry keys. They are DIFFERENT from the variants[]
# .platform slot strings ("抖音竖屏" / "B站横屏" / etc.) which carry
# aspect-ratio info. The adapter resolves a variant_id to its source
# platform identifier at fetch time.

Platform = Literal[
    "douyin",
    "kuaishou",
    "weixin_video",
    "xiaohongshu",
    "bilibili",
    "红果",
    "视频号",
]
"""7 supported platform identifiers (DATA-01 + variants[])."""


SUPPORTED_PLATFORMS_WITH_ADAPTERS: tuple[str, ...] = (
    "douyin",
    "kuaishou",
    "weixin_video",
    "xiaohongshu",
    "bilibili",
)
"""5 platforms with API adapters (Plan 42-02). Plan 42-02's integration
test asserts this matches the populated ADAPTER_REGISTRY keys exactly."""


# ──────────────────────────────────────────────────────────────────────────
# PlatformMetrics — DATA-01
# ──────────────────────────────────────────────────────────────────────────


def _in_unit_interval(v: float) -> float:
    """Range-clamp a float into [0.0, 1.0] or raise ValueError.

    Shared by all 5 metric fields on PlatformMetrics. Centralized so the
    error message is consistent across fields.
    """
    if v < 0.0 or v > 1.0:
        raise ValueError(
            f"value must be in [0.0, 1.0]; got {v}"
        )
    return v


class PlatformMetrics(BaseModel):
    """Per-variant platform performance metrics (DATA-01 schema).

    One instance per (variant_id, platform) — the 5 metric fields are
    fetched from the platform's API (or operator-pasted into the
    FeedbackRecordExtension for v9.0 stub usage). All 5 metrics are
    rates in [0.0, 1.0].

    Fields:
      platform: one of the 7 supported platforms (Platform Literal).
      variant_id: opaque identifier matching
        ``variants[].source_master_hash`` (Phase 38 SLICE) or a composite
        key resolved by the adapter at fetch time. FK target.
      completion_rate: 完播率 (fraction of viewers who watched to end).
      hook_dropoff_rate: 卡点跳出率 (fraction who left during the opening
        hook window — measured against
        ``variants[].hook_timestamps.opening_hook_end_sec``).
      engagement_rate: 互动率 ((likes + comments + shares) / views).
      save_rate: 收藏率 (saves / views).
      comment_rate: 评论率 (comments / views).
      fetched_at: timezone-aware ISO 8601 timestamp when the metric was
        fetched from the platform API (or operator-pasted).
    """

    model_config = ConfigDict(extra="forbid")

    platform: Platform
    variant_id: str = Field(min_length=1)
    completion_rate: float
    hook_dropoff_rate: float
    engagement_rate: float
    save_rate: float
    comment_rate: float
    fetched_at: datetime

    # ── Range clamps (5 metrics × [0.0, 1.0]) ───────────────────────────

    @field_validator("completion_rate")
    @classmethod
    def _completion_rate_in_range(cls, v: float) -> float:
        return _in_unit_interval(v)

    @field_validator("hook_dropoff_rate")
    @classmethod
    def _hook_dropoff_rate_in_range(cls, v: float) -> float:
        return _in_unit_interval(v)

    @field_validator("engagement_rate")
    @classmethod
    def _engagement_rate_in_range(cls, v: float) -> float:
        return _in_unit_interval(v)

    @field_validator("save_rate")
    @classmethod
    def _save_rate_in_range(cls, v: float) -> float:
        return _in_unit_interval(v)

    @field_validator("comment_rate")
    @classmethod
    def _comment_rate_in_range(cls, v: float) -> float:
        return _in_unit_interval(v)

    @field_validator("fetched_at")
    @classmethod
    def _fetched_at_has_tz(cls, v: datetime) -> datetime:
        """Mirror FeedbackRecord._ts_has_tz invariant (v6.0)."""
        if v.tzinfo is None:
            raise ValueError(
                "fetched_at must be timezone-aware (ISO 8601 with offset)"
            )
        return v


# ──────────────────────────────────────────────────────────────────────────
# FeedbackRecordExtension — DATA-02 (Option A composition)
# ──────────────────────────────────────────────────────────────────────────


class FeedbackRecordExtension(BaseModel):
    """Sidecar document extending a v6.0 FeedbackRecord (DATA-02).

    Option A scope discipline: composes WITH the v6.0 FeedbackRecord via
    a ``feedback_id`` STRING foreign key. Does NOT import or extend the
    ``FeedbackRecord`` class itself. The v6.0 FeedbackStore owns the
    original record; this extension is a sibling document stored in a
    separate path under ``<HERMES_HOME>/skills/.feedback/platform_metrics/``.

    Fields:
      feedback_id: STRING FK to v6.0 ``FeedbackStore.record_feedback``
        return value. Format: ``f"{ts_unix_micro}_{sha256[:8]}"``
        (sortable, collision-resistant — see FeedbackStore.record_feedback
        docstring). Required.
      platform_metrics: per-platform bucketed PlatformMetrics map. Keyed
        by platform identifier (Platform Literal). Default empty for
        DATA-02 backward-compat: a v6.0 record with no platform data has
        no extension; an extension with empty metrics is valid but unusual.
      ts_created: timezone-aware timestamp when this extension was
        created (separate from FeedbackRecord.ts to preserve v6.0
        immutability).
    """

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(min_length=1)
    platform_metrics: dict[str, PlatformMetrics] = Field(default_factory=dict)
    ts_created: datetime

    @field_validator("ts_created")
    @classmethod
    def _ts_created_has_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError(
                "ts_created must be timezone-aware (ISO 8601 with offset)"
            )
        return v

    @model_validator(mode="after")
    def _platform_keys_are_valid(self) -> "FeedbackRecordExtension":
        """Defensive: assert platform keys are valid Platform Literal values.

        Pydantic already enforces this at construction time via the
        ``dict[str, PlatformMetrics]`` type, but an explicit check
        surfaces a clearer error to operators who construct via raw JSON.
        """
        # Re-check the platform field on each PlatformMetrics entry.
        for key, pm in self.platform_metrics.items():
            if key != pm.platform:
                raise ValueError(
                    f"platform_metrics key {key!r} does not match "
                    f"PlatformMetrics.platform {pm.platform!r}"
                )
        return self


# ──────────────────────────────────────────────────────────────────────────
# MetricTrigger — DATA-03 enum
# ──────────────────────────────────────────────────────────────────────────


class MetricTrigger(Enum):
    """Trigger conditions that fire the formula tuning loop (DATA-03).

    Each enum value names a discrete metric-driven signal that
    ``tuning_loop.py`` (Plan 42-03) translates into a TuningSuggestion.
    The thresholds listed below are DEFAULTS — ``tuning_loop.py``
    parameterizes them so the operator can tune sensitivity.

    Members:
      HIGH_HOOK_DROPOFF: hook_dropoff_rate > threshold (default 0.20).
        Fires when the opening hook fails to retain viewers.
      HIGH_COMPLETION_LOW_ENGAGEMENT: completion_rate > 0.70 AND
        engagement_rate < 0.05. Fires when viewers finish but don't
        interact — suggests weak CTA / emotional payoff.
      LOW_COMPLETION: completion_rate < 0.30. Fires when the video
        fails to retain viewers past the midpoint.
      LOW_SAVE_RATE: save_rate < 0.01. Fires when the video fails
        to earn saves (the strongest engagement signal on most
        platforms).
    """

    HIGH_HOOK_DROPOFF = "high_hook_dropoff"
    HIGH_COMPLETION_LOW_ENGAGEMENT = "high_completion_low_engagement"
    LOW_COMPLETION = "low_completion"
    LOW_SAVE_RATE = "low_save_rate"


# ──────────────────────────────────────────────────────────────────────────
# TuningSuggestion — DATA-03 JSONL queue record
# ──────────────────────────────────────────────────────────────────────────


# Allowed lifecycle statuses (mirror agent/evolution/queue.py:PATCH_STATUSES
# shape — pending / applied / rejected). ``failed_gate`` from v6.0 is
# NOT used here (tuning suggestions don't go through an eval gate; they
# go directly to operator approval).
_TUNING_SUGGESTION_STATUSES: frozenset[str] = frozenset({
    "pending",
    "applied",
    "rejected",
})


class TuningSuggestion(BaseModel):
    """A candidate tuning suggestion pending operator review (DATA-03).

    Persistence shape (Plan 42-03 ships ``queue.py``): one JSON record
    per line in ``<HERMES_HOME>/skills/.feedback/tuning/queue.jsonl``.
    Lifecycle mirrors v6.0 EVOL-02 pattern (queue / applied / rejected
    JSONL files).

    Fields:
      suggestion_id: content-addressed ID. Convention:
        ``f"{formula_id}_{trigger}_{ts_unix}"``. Must be unique within
        the queue (content-addressing catches duplicates on read).
      formula_id: FK to ``plugins/formula_library/library/*.json:formula_id``.
      trigger: the MetricTrigger enum that fired.
      observed_metric: the metric value that crossed the threshold.
      threshold: the threshold it crossed (default threshold for the
        trigger; tuning_loop parameterizes).
      suggested_action: concrete change proposal (中文为主, e.g.
        "加 hook 强度 — 当前 hook_pattern=contrast 建议升级 emotional_peak").
      rationale: why this trigger fires for this formula.
      evidence: list of feedback_ids + variant_ids cited as evidence.
      status: lifecycle status (pending / applied / rejected).
      ts_queued: ISO 8601 UTC timestamp when the suggestion entered the queue.
      commit_sha: set when status == "applied" (the apply commit's SHA —
        populated by Plan 42-03 ``library_writer.py``).
      ts_applied: set when status == "applied".
      reason: set when status == "rejected" (operator's rejection reason).
      ts_rejected: set when status == "rejected".
    """

    model_config = ConfigDict(extra="forbid")

    suggestion_id: str = Field(min_length=1)
    formula_id: str = Field(min_length=1)
    trigger: MetricTrigger
    observed_metric: float
    threshold: float
    suggested_action: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    status: Literal["pending", "applied", "rejected"] = "pending"
    ts_queued: str = Field(min_length=1)
    # Optional status-transition metadata (mirror PatchRecord shape).
    commit_sha: str | None = None
    ts_applied: str | None = None
    reason: str | None = None
    ts_rejected: str | None = None

    @model_validator(mode="after")
    def _status_in_allowed_set(self) -> "TuningSuggestion":
        """Defensive: explicit error message if status drifts.

        Pydantic v2's Literal already enforces this at schema time; this
        validator surfaces a clearer error if constructed via a code path
        that bypasses Literal validation.
        """
        if self.status not in _TUNING_SUGGESTION_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_TUNING_SUGGESTION_STATUSES)}, "
                f"got {self.status!r}"
            )
        return self


# ──────────────────────────────────────────────────────────────────────────
# Exports
# ──────────────────────────────────────────────────────────────────────────


__all__ = [
    "Platform",
    "PlatformMetrics",
    "FeedbackRecordExtension",
    "MetricTrigger",
    "TuningSuggestion",
    "SUPPORTED_PLATFORMS_WITH_ADAPTERS",
]
