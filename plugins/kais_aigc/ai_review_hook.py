"""ai_review_hook.py — Post-phase AI review hook.

Extracts quality scores from pipeline phase outputs and writes them to the Asset
Feedback API via FeedbackClient. Called after each phase completes, before or
after the review gate fires.

Design:
- Degrade-tolerant (never raises, never blocks pipeline)
- Configurable via env vars (KAIS_AI_REVIEW_ENABLED=1 to enable)
- Uses FeedbackClient.create_degraded() for each scored artifact
- Maps phase-specific quality metrics to feedback scores

Score extraction rules per phase:
- p03 (script_audit): extract audit-report 5-dim scores → 5 feedback entries
  (one per dimension: drama, rhythm, character, logic, theme).
  verdict = approve if score>=0.7, contest if 0.5-0.7, reject if <0.5
- p04 (character_design): no auto-score (human review only)
- p07 (scene_generation): no auto-score
- p10 (voice): extract lip-sync alignment scores → feedback per shot.
  verdict from alignment_score
- p10b (rapid_preview): extract per-shot quality scores if present
- p11 (video_render): extract lip-sync-reports → feedback per shot.
  alignment_score>=0.7=approve, 0.5-0.7=contest, <0.5=reject
- p12 (composition): no auto-score (final assembly, human review)

For phases without auto-score rules, the hook is a no-op.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# Phase-specific score extraction configs.
# Each entry maps an output slot to an extraction rule.
_PHASE_SCORE_CONFIG: dict[str, list[dict]] = {
    "p03_script_audit": [
        {
            "slot": "audit-report",
            "artifact_id_prefix": "n-p03",
            "type": "script_audit_5dim",
        },
    ],
    "p10_voice": [
        {
            "slot": "lip-sync-reports",
            "artifact_id_prefix": "a-p10",
            "score_field": "alignment_score",
            "id_field": "shot_id",
            "type": "lip_sync",
        },
    ],
    "p11_video_render": [
        {
            "slot": "lip-sync-reports",
            "artifact_id_prefix": "a-p11",
            "score_field": "alignment_score",
            "id_field": "shot_id",
            "type": "lip_sync",
        },
    ],
    "p10b_rapid_preview": [
        {
            "slot": "rapid-previews",
            "artifact_id_prefix": "a-p10b",
            "score_field": "quality_score",
            "id_field": "shot_id",
            "type": "rapid_preview",
        },
    ],
}

# Script audit 5 dimensions
_AUDIT_DIMS = ["drama", "rhythm", "character", "logic", "theme"]


def _score_to_verdict(score: float) -> str:
    """Map a 0-1 score to a verdict."""
    if score >= 0.7:
        return "approve"
    elif score >= 0.5:
        return "contest"
    else:
        return "reject"


def _import_feedback_client():
    """Import FeedbackClient — works both as package-relative and standalone."""
    try:
        from .feedback_client import FeedbackClient
    except ImportError:
        from feedback_client import FeedbackClient  # type: ignore[no-redef]
    return FeedbackClient


def extract_and_submit(
    phase_id: str,
    phase_result: dict[str, Any],
    project_id: int,
    *,
    base_url: str | None = None,
) -> int:
    """Extract quality scores from phase result and submit to feedback API.

    Returns the number of feedback entries created. Degrade-tolerant.
    """
    if os.environ.get("KAIS_AI_REVIEW_ENABLED", "0") != "1":
        return 0

    configs = _PHASE_SCORE_CONFIG.get(phase_id)
    if not configs:
        return 0

    outputs = phase_result.get("outputs", {})
    if not isinstance(outputs, dict):
        return 0

    try:
        FeedbackClient = _import_feedback_client()
        client = FeedbackClient(base_url=base_url)
    except Exception:
        logger.debug("ai_review_hook: FeedbackClient unavailable", exc_info=True)
        return 0

    count = 0

    for config in configs:
        slot = config["slot"]
        data = outputs.get(slot)
        if not data:
            continue

        # Handle script_audit 5-dim specially
        if config["type"] == "script_audit_5dim":
            # data could be {drama: 0.8, rhythm: 0.6, ...} or nested {scores: {...}}
            scores: dict = data if isinstance(data, dict) else {}
            if not scores:
                scores = {}
            # Support nested {scores: {...}} shape
            if not any(dim in scores for dim in _AUDIT_DIMS):
                nested = data.get("scores", {}) if isinstance(data, dict) else {}
                if isinstance(nested, dict):
                    scores = nested

            prefix = config["artifact_id_prefix"]
            for dim in _AUDIT_DIMS:
                score_val = scores.get(dim)
                if score_val is None:
                    continue
                if isinstance(score_val, dict):
                    try:
                        score_float = float(score_val.get("score", 0))
                    except (TypeError, ValueError):
                        continue
                else:
                    try:
                        score_float = float(score_val)
                    except (TypeError, ValueError):
                        continue

                asset_id = f"{prefix}-{dim}"
                verdict = _score_to_verdict(score_float)

                try:
                    result_resp = client.create_degraded(
                        asset_id=asset_id,
                        project_id=project_id,
                        score=score_float,
                        verdict=verdict,
                        content=f"Script audit [{dim}]: {score_float:.2f}",
                        source="ai_reviewer",
                        reviewer=f"script_auditor:{dim}",
                        context={"phase": phase_id, "dimension": dim},
                    )
                    # create_degraded swallows exceptions and returns a degrade
                    # envelope on failure — only count real successes.
                    if isinstance(result_resp, dict) and result_resp.get("degraded"):
                        continue
                    count += 1
                except Exception:
                    logger.debug(
                        "ai_review_hook: create_degraded failed (dim=%s)",
                        dim,
                        exc_info=True,
                    )

        elif config["type"] in ("lip_sync", "rapid_preview"):
            items = data if isinstance(data, list) else []
            id_field = config["id_field"]
            score_field = config["score_field"]
            prefix = config["artifact_id_prefix"]
            cfg_type = config["type"]

            for item in items:
                if not isinstance(item, dict):
                    continue
                shot_id = item.get(id_field) or "unknown"
                score_val = item.get(score_field)
                if score_val is None:
                    continue
                try:
                    score_float = float(score_val)
                except (TypeError, ValueError):
                    continue

                asset_id = f"{prefix}-{shot_id}"
                verdict = _score_to_verdict(score_float)

                issues = item.get("issues", [])
                content = f"{cfg_type} {shot_id}: score={score_float:.2f}"
                if issues:
                    joined = ", ".join(str(i) for i in issues[:3])
                    content += f" issues: {joined}"

                try:
                    result_resp = client.create_degraded(
                        asset_id=asset_id,
                        project_id=project_id,
                        score=score_float,
                        verdict=verdict,
                        content=content,
                        source="ai_reviewer",
                        reviewer=cfg_type,
                        context={"phase": phase_id, "shot_id": shot_id, **item},
                    )
                    if isinstance(result_resp, dict) and result_resp.get("degraded"):
                        continue
                    count += 1
                except Exception:
                    logger.debug(
                        "ai_review_hook: create_degraded failed (shot=%s)",
                        shot_id,
                        exc_info=True,
                    )

    if count > 0:
        logger.info("ai_review_hook: %s → %d feedback entries", phase_id, count)

    return count
