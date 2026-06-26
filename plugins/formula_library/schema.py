"""schema.py — Pydantic v2 schema for formula_library (Plan 39-01, FORM-02).

Single contract that every ``library/*.json`` file validates against.
Downstream (Plan 39-02) authors 10 seed formulas conforming to this schema;
Plan 39-03 wires it into ``kais-movie-pipeline`` Step 0 + ``theory_critic``
optional ``formula_reference`` input.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - Double-quoted strings throughout.
  - Pydantic v2 syntax (``field_validator``, ``model_config``).
  - ``encoding="utf-8"`` on every ``read_text`` (Ruff PLW1514).
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations (Literal types — kept as module-level aliases for reuse in
# tools.py JSON-schema generation and tests)
# ---------------------------------------------------------------------------

GENRES = ("都市奇幻", "悬疑反转", "家庭情感", "校园青春", "职场商战")
"""5-genre matrix axis (FORM-02)."""

MOODS = ("轻喜剧", "虐心")
"""2-mood matrix axis (FORM-02)."""

PLATFORMS = ("抖音", "快手", "B站", "小红书", "视频号", "红果")
"""6 supported platforms (FORM-02 platform_fit axis)."""

HOOK_PATTERNS = ("emotional", "suspense", "conflict", "contrast", "emotional_peak")
"""5 hook types from ``hook_retention/references/three-second-hooks.md``."""

SOURCE_TYPES = ("notion", "public-book", "kais-benchmark")
"""3 citation source categories (FORM-02)."""

FAIR_USE_STATUSES = ("verbatim-spec", "paraphrased", "derived-analysis")
"""3 fair-use disposition categories (FORM-02)."""

Genre = Literal["都市奇幻", "悬疑反转", "家庭情感", "校园青春", "职场商战"]
Mood = Literal["轻喜剧", "虐心"]
Platform = Literal["抖音", "快手", "B站", "小红书", "视频号", "红果"]
HookPattern = Literal["emotional", "suspense", "conflict", "contrast", "emotional_peak"]
SourceType = Literal["notion", "public-book", "kais-benchmark"]
FairUseStatus = Literal["verbatim-spec", "paraphrased", "derived-analysis"]


# ---------------------------------------------------------------------------
# Nested models
# ---------------------------------------------------------------------------


class PlatformFit(BaseModel):
    """Per-platform fit score for a Formula.

    ``platform`` is constrained to the 6 short-drama platforms (FORM-02).
    ``fit_score`` is a float in [0.0, 1.0] — higher is better.
    """

    model_config = ConfigDict(extra="forbid")

    platform: Platform
    fit_score: float

    @field_validator("fit_score")
    @classmethod
    def _fit_score_in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(
                f"fit_score must be in [0.0, 1.0]; got {v}"
            )
        return v


class Citation(BaseModel):
    """Fair-use attribution for a Formula (FORM-02).

    Every formula MUST carry a citation — uncited formulas fail validation.
    This is a CLAUDE.md copyright hard-constraint.
    """

    model_config = ConfigDict(extra="forbid")

    source: str
    source_type: SourceType
    fair_use_status: FairUseStatus
    verified_date: date


# ---------------------------------------------------------------------------
# Formula — top-level model
# ---------------------------------------------------------------------------


class Formula(BaseModel):
    """A single short-drama formula entry (FORM-02).

    Schema fields:
      formula_id: unique kebab-case identifier (e.g. ``urban-fantasy-light-01``).
      genre: one of 5 genres (都市奇幻 / 悬疑反转 / 家庭情感 / 校园青春 / 职场商战).
      mood: one of 2 moods (轻喜剧 / 虐心).
      pacing: short descriptor (``fast-cut`` / ``slow-burn`` / ``mid-tempo``).
      hook_pattern: one of 5 hook types from ``three-second-hooks.md``.
      characters: archetype list (e.g. ``["hidden-boss", "everyman-sidekick"]``).
      runtime_sec: episode length in seconds, clamped to [60, 600].
      platform_fit: per-platform fit scores; 2-6 entries.
      citation: fair-use attribution (required).
      verified_date: top-level ISO date (when the formula was last verified).
      eval_score: optional float populated by v6.0 eval gate; None until then.
    """

    model_config = ConfigDict(extra="forbid")

    formula_id: str
    genre: Genre
    mood: Mood
    pacing: str
    hook_pattern: HookPattern
    characters: list[str]
    runtime_sec: int
    platform_fit: list[PlatformFit]
    citation: Citation
    verified_date: date
    eval_score: Optional[float] = None

    @field_validator("runtime_sec")
    @classmethod
    def _runtime_sec_in_range(cls, v: int) -> int:
        if v < 60 or v > 600:
            raise ValueError(
                f"runtime_sec must be in [60, 600]; got {v}"
            )
        return v

    @field_validator("characters")
    @classmethod
    def _characters_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("characters must be a non-empty list")
        return v

    @field_validator("platform_fit")
    @classmethod
    def _platform_fit_non_empty(cls, v: list[PlatformFit]) -> list[PlatformFit]:
        if not v:
            raise ValueError("platform_fit must be a non-empty list")
        return v


# ---------------------------------------------------------------------------
# FormulaLibrary — collection wrapper + helpers
# ---------------------------------------------------------------------------


class FormulaLibrary(BaseModel):
    """Collection of Formula objects with lookup helpers.

    ``load_from_dir`` is the canonical entrypoint for Plan 39-02 seed data:
    it globs ``library/*.json``, validates each against ``Formula``, and
    degrades gracefully on per-file failures (mirrors the
    ``_discover_expert_ids`` pattern in ``agent/feedback_schema.py:117``).
    """

    model_config = ConfigDict(extra="forbid")

    formulas: list[Formula] = []

    # ----------------------- helpers -----------------------

    _GENRE_MOOD_KEY_SEPARATOR: ClassVar[str] = "\x1f"  # ASCII unit separator

    def by_id(self, formula_id: str) -> Optional[Formula]:
        """Return the Formula with ``formula_id`` or None."""
        for f in self.formulas:
            if f.formula_id == formula_id:
                return f
        return None

    def filter(self, *, genre: str, mood: str) -> list[Formula]:
        """Strict genre+mood filter.

        Both ``genre`` and ``mood`` must match exactly. Literal types enforce
        valid values upstream in Pydantic validation, but this method accepts
        plain strings so callers don't have to construct Literal-typed args.
        """
        return [
            f for f in self.formulas
            if f.genre == genre and f.mood == mood
        ]

    # ----------------------- classmethod loaders -----------------------

    @classmethod
    def load_from_dir(cls, library_dir: Path) -> "FormulaLibrary":
        """Load every ``library/*.json`` file from ``library_dir``.

        Degrade-gracefully: if the dir is missing, return an empty library.
        On per-file JSON parse / Pydantic validation failure, log a warning
        and skip that file (do NOT abort the whole load — operator can fix
        the bad file without losing the good ones).

        Args:
            library_dir: directory containing ``formula_*.json`` files.

        Returns:
            FormulaLibrary with all valid formulas. Empty if dir missing or
            all files invalid.
        """
        if not library_dir.is_dir():
            logger.debug(
                "formula library dir %s does not exist; returning empty library",
                library_dir,
            )
            return cls(formulas=[])

        loaded: list[Formula] = []
        # Sort for deterministic load order across platforms.
        for json_path in sorted(library_dir.glob("*.json")):
            try:
                raw = json_path.read_text(encoding="utf-8")
                obj = json.loads(raw)
                formula = Formula.model_validate(obj)
                loaded.append(formula)
            except Exception as exc:  # noqa: BLE001 — per-file failure must not abort load
                logger.warning(
                    "skipped invalid formula file %s: %s",
                    json_path, exc,
                )
        logger.debug(
            "loaded %d formula(s) from %s", len(loaded), library_dir,
        )
        return cls(formulas=loaded)


__all__ = [
    "Citation",
    "FAIR_USE_STATUSES",
    "Formula",
    "FormulaLibrary",
    "GENRES",
    "HOOK_PATTERNS",
    "MOODS",
    "PLATFORMS",
    "PlatformFit",
    "SOURCE_TYPES",
]
