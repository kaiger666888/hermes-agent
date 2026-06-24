"""FeedbackRecord + OutputSnapshot Pydantic schema (INGEST-04 validation layer).

This module is the single contract that all three feedback sources
(``cli`` from ``/feedback``, ``kais_aigc`` from file-exchange inbox,
``manual`` from JSONL batch import) emit before persistence. Downstream
phases (P29 STORE, P30 GATE, P31 EVOL) all consume this shape.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - Double-quoted strings throughout.
  - Pydantic v2 syntax (``field_validator``, ``model_config``).
  - No ``open()`` in this module (Ruff PLW1514 n/a, but kept clean).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, field_validator

from agent.skill_utils import parse_frontmatter

logger = logging.getLogger(__name__)

# ── Auto-discovered expert ID registry ────────────────────────────────────
#
# Per CONTEXT.md D-04 + planner resolution of research open question #4:
# auto-discovery walks ``skills/movie-experts/*/SKILL.md`` at import time and
# collects the YAML frontmatter ``name`` field. This is the single source of
# truth — it catches v3/v4/v5 additions automatically, unlike the frozen
# ``EXPERT_DIRS`` list in ``_eval/snapshot.py`` which is stale.
#
# On ANY exception (missing dir, parse error, running outside repo) we fall
# back to a hardcoded list of every directory currently in
# ``skills/movie-experts/`` and log a warning so the operator notices.

# Hardcoded fallback: every directory in skills/movie-experts/ as of 2026-06-24.
# Must be kept in sync if a new expert ships — auto-discovery handles this
# automatically when the repo layout is available; this list only activates
# when discovery fails (e.g. running outside the repo).
_FALLBACK_EXPERT_IDS: frozenset[str] = frozenset(
    {
        "animation_studio",
        "animator",
        "audio_pipeline",
        "character_designer",
        "cinematographer",
        "colorist",
        "compliance_gate",
        "compliance_marketing",
        "composer",
        "continuity",
        "continuity_auditor",
        "creative_source",
        "documentary_maker",
        "drawer",
        "editor",
        "foley",
        "hook_retention",
        "lip_sync",
        "mixer",
        "performer",
        "production",
        "prompt_injector",
        "scene_builder",
        "screenplay",
        "script_auditor",
        "spatial_audio",
        "storyboard_designer",
        "style_genome",
        "theory_critic",
        "visual_executor",
        "voicer",
    }
)

# Module-level cache so repeated reads of the filesystem don't happen.
# Filled by ``_discover_expert_ids`` on first access.
_EXPERT_DISCOVERY_CACHE: frozenset[str] | None = None


def _discover_expert_ids() -> frozenset[str]:
    """Walk ``skills/movie-experts/*/SKILL.md`` and collect frontmatter ``name``.

    Returns a frozenset of the ``name`` field from each SKILL.md YAML
    frontmatter. Falls back to a hardcoded list on ANY exception (missing
    repo dir, parse error, running outside the repo) and emits a warning
    log so the operator notices the fallback.

    The result is cached in ``_EXPERT_DISCOVERY_CACHE`` so repeated calls
    are cheap.
    """
    global _EXPERT_DISCOVERY_CACHE
    if _EXPERT_DISCOVERY_CACHE is not None:
        return _EXPERT_DISCOVERY_CACHE

    discovered: set[str] = set()
    try:
        # Resolve relative to this file: agent/feedback_schema.py is at the
        # repo root + agent/, so skills/ is two parents up.
        repo_root = Path(__file__).resolve().parent.parent
        experts_dir = repo_root / "skills" / "movie-experts"
        if not experts_dir.is_dir():
            raise FileNotFoundError(f"movie-experts dir not found at {experts_dir}")

        for skill_md in experts_dir.glob("*/SKILL.md"):
            try:
                content = skill_md.read_text(encoding="utf-8")
                frontmatter, _body = parse_frontmatter(content)
                name = frontmatter.get("name")
                if isinstance(name, str) and name.strip():
                    discovered.add(name.strip())
            except Exception as exc:  # noqa: BLE001 — single-file parse must not abort discovery
                logger.debug(
                    "skipped expert frontmatter at %s: %s", skill_md, exc
                )

        if not discovered:
            raise RuntimeError(
                "auto-discovery walked the dir but found zero valid frontmatter names"
            )
    except Exception as exc:  # noqa: BLE001 — discovery must never crash import
        logger.warning(
            "expert ID auto-discovery failed: %s; using fallback list of %d experts",
            exc,
            len(_FALLBACK_EXPERT_IDS),
        )
        _EXPERT_DISCOVERY_CACHE = _FALLBACK_EXPERT_IDS
        return _EXPERT_DISCOVERY_CACHE

    _EXPERT_DISCOVERY_CACHE = frozenset(discovered)
    return _EXPERT_DISCOVERY_CACHE


# Populated at module load — every consumer imports this directly.
_KNOWN_EXPERT_IDS: frozenset[str] = _discover_expert_ids()


# ── OutputSnapshot ────────────────────────────────────────────────────────


_SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class OutputSnapshot(BaseModel):
    """Provenance for the LLM output being reviewed.

    The ``sha256`` field is the canonical dedup contract for P29 STORE and
    P30 GATE: it MUST be the sha256 of the exact ``output_text`` bytes
    encoded as UTF-8. Any sanitization (e.g. surrogate scrubbing) MUST
    happen BEFORE hashing so the hash is deterministic across runs.
    Document this at the hash call site in ``feedback_snapshot.py``.
    """

    sha256: str
    output_text: str
    prompt: str
    model: str
    provider: str
    api_mode: str = ""
    params: dict[str, Any]
    captured_at: datetime

    @field_validator("sha256")
    @classmethod
    def _sha256_is_64_hex(cls, v: str) -> str:
        if not isinstance(v, str) or not _SHA256_HEX_RE.match(v):
            raise ValueError("sha256 must be 64 lowercase hex characters")
        return v.lower()


# ── FeedbackRecord ────────────────────────────────────────────────────────


class FeedbackRecord(BaseModel):
    """Normalized feedback record — the single schema all three sources emit.

    Fields:
      skill_id: the movie-expert skill the feedback targets. Validated
        against ``_KNOWN_EXPERT_IDS`` (auto-discovered from
        ``skills/movie-experts/*/SKILL.md``).
      expert_id: same as skill_id for movie-experts (kept separate for
        future multi-expert-per-skill scenarios). Same validation.
      source: which ingestion path produced this record.
        ``cli`` = ``/feedback`` slash command; ``kais_aigc`` = file-exchange
        inbox; ``manual`` = JSONL batch import.
      verdict: operator's qualitative rating of the output.
      correction: free-text explanation of what was wrong or could improve.
      revised_output: optional full replacement output (for ablation in P30).
      output_snapshot: provenance of the LLM output being reviewed.
      ts: when the feedback was submitted. MUST be timezone-aware (ISO 8601).
    """

    skill_id: str
    expert_id: str
    source: Literal["cli", "kais_aigc", "manual"]
    verdict: Literal["good", "needs_work", "bad"]
    correction: str = ""
    revised_output: str | None = None
    output_snapshot: OutputSnapshot
    ts: datetime

    @field_validator("skill_id", "expert_id")
    @classmethod
    def _known_expert(cls, v: str) -> str:
        known = _KNOWN_EXPERT_IDS
        if v not in known:
            raise ValueError(
                f"skill_id '{v}' is not a known movie-expert. "
                f"Known: {sorted(known)}"
            )
        return v

    @field_validator("ts")
    @classmethod
    def _ts_has_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("ts must be timezone-aware (ISO 8601 with offset)")
        return v
