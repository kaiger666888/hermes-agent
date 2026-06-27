"""recipe_library.py — Emotion Recipe Library (Phase 41).

Converts V5.0 creative-history 5-dim script_auditor scores into reusable,
queryable emotion recipes. Pure stdlib, sync API throughout (D-07 — Phase
32 locked sync for state modules). No third-party deps, no async, no HTTP,
no subprocess (those concerns stay in kais_aigc/).

Sibling module to creative_history.py. RecipeLibrary mirrors the
CreativeHistoryTracker constructor pattern (*, asset_bus: AssetBus).

RECIPE-LIB-01: 5 core methods (this module ships 3 in plan 41-01:
                create_recipe / get_recipe / list_recipes;
                plan 41-02 ships update_validation;
                plan 41-03 ships query_by_structure).
RECIPE-LIB-02: JSONL schema strict (see _RECIPE_FIELDS — 16 fields total).
RECIPE-LIB-03: emotion-recipe AssetBus slot, append-only, multi-version.
RECIPE-LIB-05: list_recipes genre + converged filters (similarity in 41-03).
RECIPE-LIB-06: provenance chains recipe → source_episode; recipe_id
               follows <genre-slug>-<NNN> zero-padded pattern.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────

_VALID_ENDING_STATES = {"resolved", "new_suspense", "cliffhanger"}
_VALID_PLATFORMS = {"douyin", "bilibili", "youtube", ""}  # "" = unset on create

# Recipe JSONL schema field inventory (RECIPE-LIB-02 — 16 fields total).
# Used for documentation + future schema-strict assertions in 41-02.
_RECIPE_FIELDS = {
    "top_level": ("recipe_id", "version", "genre"),  # 3
    "structure": (
        "hook_position_sec",      # int seconds
        "emotion_sequence",       # list[str]
        "turning_points_sec",     # list[int] seconds
        "emotion_drop_level",     # int 1-5
        "ending_state",           # str enum
    ),  # 5
    "validation": (
        "platform",               # str enum: douyin|bilibili|youtube|"" (unset)
        "completion_rate",        # float 0-1
        "confidence_interval",    # str human-readable "±N%"
        "sample_size",            # int
        "converged",              # bool
    ),  # 5
    "provenance": (
        "source_episode",         # str — chains recipe → episode (RECIPE-LIB-06)
        "created",                # ISO 8601 UTC str
        "last_validated",         # None on create; ISO str after update_validation
    ),  # 3
}
# 3 + 5 + 5 + 3 = 16 fields total


# ─── Module-level helpers ─────────────────────────────────────────────


def _slugify(text: str) -> str:
    """Lowercase, whitespace → hyphen, strip non-[a-z0-9-], collapse hyphens.

    If the result is empty (e.g., all-Chinese input), fall back to the
    literal slug ``"recipe"`` so the recipe_id stays non-empty + ASCII-safe.

    Examples:
        _slugify("Urban Fantasy") → "urban-fantasy"
        _slugify("  A---B  ")     → "a-b"
        _slugify("都市奇幻")       → "recipe"  (Chinese chars stripped → fallback)
        _slugify("")              → "recipe"
    """
    s = text.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)  # Chinese chars become '' (acceptable)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s if s else "recipe"


def _now_iso() -> str:
    """Current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _validate_structure(structure: dict) -> None:
    """Raise ValueError if structure is missing required fields or has wrong types.

    RECIPE-LIB-02 schema strict — 5 fields:
        hook_position_sec (int, >= 0)
        emotion_sequence (list[str], len >= 1)
        turning_points_sec (list[int])
        emotion_drop_level (int, 1 <= x <= 5)
        ending_state (str, one of _VALID_ENDING_STATES)
    """
    if not isinstance(structure, dict):
        raise ValueError(f"structure must be dict, got {type(structure).__name__}")

    hook = structure.get("hook_position_sec")
    if not isinstance(hook, int) or isinstance(hook, bool) or hook < 0:
        raise ValueError(
            f"structure.hook_position_sec must be int >= 0, got {hook!r}"
        )

    seq = structure.get("emotion_sequence")
    if not isinstance(seq, list) or len(seq) < 1 or not all(isinstance(x, str) for x in seq):
        raise ValueError(
            f"structure.emotion_sequence must be non-empty list[str], got {seq!r}"
        )

    tps = structure.get("turning_points_sec")
    if not isinstance(tps, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in tps):
        raise ValueError(
            f"structure.turning_points_sec must be list[int], got {tps!r}"
        )

    drop = structure.get("emotion_drop_level")
    if not isinstance(drop, int) or isinstance(drop, bool) or drop < 1 or drop > 5:
        raise ValueError(
            f"structure.emotion_drop_level must be int in [1,5], got {drop!r}"
        )

    ending = structure.get("ending_state")
    if ending not in _VALID_ENDING_STATES:
        raise ValueError(
            f"structure.ending_state must be one of {_VALID_ENDING_STATES}, got {ending!r}"
        )


def _build_initial_recipe(
    recipe_id: str,
    genre: str,
    structure: dict,
    source_episode: str,
) -> dict:
    """Assemble the 16-field recipe dict with version=1 + initial validation{}.

    Initial validation{} values per CONTEXT.md "update_validation flow" —
    these get overwritten by 41-02 on first feedback.
    """
    return {
        "recipe_id": recipe_id,
        "version": 1,
        "genre": genre,
        "structure": {
            "hook_position_sec": structure["hook_position_sec"],
            "emotion_sequence": list(structure["emotion_sequence"]),
            "turning_points_sec": list(structure["turning_points_sec"]),
            "emotion_drop_level": structure["emotion_drop_level"],
            "ending_state": structure["ending_state"],
        },
        "validation": {
            "platform": "",             # unset until first update_validation
            "completion_rate": 0.0,
            "confidence_interval": "±0%",
            "sample_size": 0,
            "converged": False,
        },
        "provenance": {
            "source_episode": source_episode,
            "created": _now_iso(),
            "last_validated": None,     # None until first update_validation (41-02)
        },
    }


def _next_sequence(rows: list[dict], slug: str) -> int:
    """Return the next sequence number for the given slug.

    Reads all emotion-recipe rows, filters by recipe_id startswith
    ``f"{slug}-"``, parses trailing digits, returns max+1 (or 1 if none).
    """
    prefix = f"{slug}-"
    nums: list[int] = []
    for r in rows:
        rid = r.get("recipe_id", "")
        if not isinstance(rid, str) or not rid.startswith(prefix):
            continue
        suffix = rid[len(prefix):]
        if suffix.isdigit():
            nums.append(int(suffix))
    return (max(nums) + 1) if nums else 1


def _latest_version(rows: list[dict], recipe_id: str) -> dict | None:
    """Pick the max-version row for the given recipe_id, or None if absent."""
    matching = [r for r in rows if r.get("recipe_id") == recipe_id]
    if not matching:
        return None
    return max(matching, key=lambda r: r.get("version", 0))


# ─── RecipeLibrary ────────────────────────────────────────────────────


class RecipeLibrary:
    """Structured emotion-recipe library.

    Persists recipes to the ``emotion-recipe`` AssetBus JSONL slot
    (append-only; one line per recipe version). Sibling to
    CreativeHistoryTracker; mirrors its constructor signature.

    Plan 41-01 delivers create_recipe / get_recipe / list_recipes.
    Plan 41-02 will add update_validation; plan 41-03 query_by_structure.
    """

    SLOT = "emotion-recipe"

    def __init__(self, *, asset_bus: Any) -> None:
        if asset_bus is None:
            raise ValueError("RecipeLibrary: asset_bus required")
        self._bus = asset_bus

    # ── Core method 1: create_recipe ──────────────────────────────────

    def create_recipe(
        self,
        genre: str,
        structure: dict,
        source_episode: str,
    ) -> str | None:
        """Create a new recipe (version=1) and append it to the JSONL slot.

        Args:
            genre: Genre string (e.g. "Urban Fantasy" or "都市奇幻·轻喜剧").
            structure: Dict with the 5 required structure fields — see
                ``_validate_structure`` for the contract.
            source_episode: Episode ID for provenance tracking (RECIPE-LIB-06).

        Returns:
            recipe_id string (e.g. "urban-fantasy-001") on success, or
            None on AssetBus failure (degraded mode — logs warning, does
            not raise).

        Raises:
            ValueError: if structure fails validation (programmer error).
        """
        # Validate structure BEFORE slugifying/sequencing — fail fast on
        # bad input (programmer error, propagate per creative_history pattern).
        _validate_structure(structure)

        slug = _slugify(genre)
        try:
            rows = self._bus.read_lines(self.SLOT)
        except Exception as e:
            # If read fails we can still attempt to write at sequence 001
            # since a fresh slot is empty, but log the anomaly.
            logger.warning("RecipeLibrary create_recipe: read_lines degraded: %s", e)
            rows = []

        seq = _next_sequence(rows, slug)
        recipe_id = f"{slug}-{seq:03d}"
        recipe = _build_initial_recipe(recipe_id, genre, structure, source_episode)

        try:
            self._bus.append_line(self.SLOT, recipe)
        except Exception as e:
            logger.warning("RecipeLibrary create_recipe degraded: %s", e)
            return None

        logger.info(
            "RecipeLibrary create_recipe: %s (genre=%s, episode=%s)",
            recipe_id, genre, source_episode,
        )
        return recipe_id

    # ── Core method 2: get_recipe ────────────────────────────────────

    def get_recipe(self, recipe_id: str, *, version: int | None = None) -> dict:
        """Return a recipe by ID.

        Args:
            recipe_id: The recipe identifier (e.g. "urban-fantasy-001").
            version: If None (default), return the latest version row.
                If int, return that specific historical version.

        Returns:
            The recipe dict.

        Raises:
            KeyError: if recipe_id is unknown, or the specific version
                doesn't exist for a known recipe_id.
        """
        rows = self._bus.read_lines(self.SLOT)
        matching = [r for r in rows if r.get("recipe_id") == recipe_id]

        if not matching:
            raise KeyError(f"recipe_id not found: {recipe_id}")

        if version is not None:
            for r in matching:
                if r.get("version") == version:
                    return r
            raise KeyError(
                f"recipe_id not found: {recipe_id} (version={version})"
            )

        return max(matching, key=lambda r: r.get("version", 0))

    # ── Core method 3: list_recipes ──────────────────────────────────

    def list_recipes(
        self,
        *,
        genre: str | None = None,
        converged: bool | None = None,
    ) -> list[dict]:
        """List recipes with optional filtering.

        Args:
            genre: If provided, filter to recipes with this exact genre.
            converged: If provided, filter by validation.converged flag.

        Returns:
            List of recipe dicts — latest version per recipe_id only
            (older versions are not returned). Order is unspecified.
        """
        rows = self._bus.read_lines(self.SLOT)

        # Group by recipe_id, keep latest version per group
        by_id: dict[str, dict] = {}
        for r in rows:
            rid = r.get("recipe_id")
            if rid is None:
                continue
            if rid not in by_id or r.get("version", 0) > by_id[rid].get("version", 0):
                by_id[rid] = r

        results = list(by_id.values())

        if genre is not None:
            results = [r for r in results if r.get("genre") == genre]

        if converged is not None:
            results = [
                r for r in results
                if r.get("validation", {}).get("converged") == converged
            ]

        return results
