"""recipe_library.py — Emotion Recipe Library (Phase 41).

Converts V5.0 story-framework + final-audit slot data (structural data +
5-dim quality scores) into reusable, queryable emotion recipes. Pure stdlib,
sync API throughout (D-07 — Phase 32 locked sync for state modules). No
third-party deps, no async, no HTTP, no subprocess (those concerns stay in
kais_aigc/).

DATA SOURCE PIVOT (plan-checker BLOCKER #1, locked 2026-06-27): the original
blueprint assumed the 5-dim scores lived in the lineage slot. V5.0 verified
reality: structural data lives in story-framework (mcmahon_arc, anchor_
validation) and 5-dim quality scores live in final-audit (D1-D5). This
module reads ONLY those two slots.

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

import copy
import json
import logging
import math
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


# ─── Phase 41-02: structure extraction helpers (DATA SOURCE PIVOT) ────

# McMahon arc -> emotion_sequence lookup table (5-6 common arcs).
# CONTEXT.md "Updated structure{} extraction" mapping table.
# Unknown arc -> fallback ["setup", "rising", "climax", "resolution"] + WARNING log.
MCMAHON_ARC_EMOTIONS: dict[str, list[str]] = {
    "man_in_a_hole":     ["hope", "descent", "crisis", "recovery"],
    "rags_to_riches":    ["low", "rise", "peak", "fall"],
    "the_quest":         ["call", "trial", "ordeal", "boon"],
    "voyage_and_return": ["depart", "wonder", "terror", "return"],
    "rebirth":           ["sin", "realization", "redemption", "new_life"],
    "tragedy":           ["pride", "error", "catastrophe", "aftermath"],
}
_MCMAHON_FALLBACK_SEQUENCE = ["setup", "rising", "climax", "resolution"]

# Regexes for anchor_validation parsing.
# Format: "Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓"
_RE_CATALYST_HOOK = re.compile(r"Catalyst\s*~(\d+(?:\.\d+)?)s")
_RE_ALL_TIMESTAMPS = re.compile(r"~(\d+(?:\.\d+)?)s")
# Fallback when Catalyst absent in anchor_validation: parse first snyder_beats
# "(N-Ms)" range and take lower bound N as hook.
_RE_FIRST_BEAT_RANGE = re.compile(r"\((\d+)-\d+s\)")


def _parse_anchor_validation(anchor_str: str) -> tuple[int | None, list[int]]:
    """Parse a snowflake anchor_validation string into (hook, turning_points).

    Args:
        anchor_str: e.g. "Catalyst ~7.5s ✓ / Midpoint ~37s ✓ / All Is Lost ~55s ✓"

    Returns:
        (hook_position_sec, turning_points_sec_list):
          hook_position_sec — int(float("7.5")) == 7 (round-toward-zero).
            None if "Catalyst ~Ns" token absent (caller handles fallback).
          turning_points_sec_list — [int(float(x)) for x in all "~Ns" matches].
            Empty list if no matches.
    """
    if not anchor_str:
        return (None, [])

    hook_match = _RE_CATALYST_HOOK.search(anchor_str)
    hook = int(float(hook_match.group(1))) if hook_match else None

    all_matches = _RE_ALL_TIMESTAMPS.findall(anchor_str)
    turning_points = [int(float(x)) for x in all_matches]

    return (hook, turning_points)


def _map_d2_to_drop_level(d2_emotion: int) -> int:
    """Map D2_emotion (0-20 scale) to emotion_drop_level (1-5).

    Formula (CONTEXT.md): ``int((20 - D2) / 4) + 1`` clamped [1,5].
    Lower D2 -> bigger drop. WARNING #1 (CONTEXT.md): single-step computation
    from raw D2 scalar — no double quantization (D2 is already an int per slot
    schema; episode-level, not per-shot mean).

    Reference values:
        D2=20 -> 1 (int(0/4)+1 = 1)
        D2=17 -> 1 (int(3/4)+1 = int(0.75)+1 = 0+1 = 1)
        D2=16 -> 2 (int(4/4)+1 = 1+1 = 2)
        D2=12 -> 3 (int(8/4)+1 = 2+1 = 3)
        D2=8  -> 4 (int(12/4)+1 = 3+1 = 4)
        D2=4  -> 5 (int(16/4)+1 = 4+1 = 5)
        D2=0  -> 5 (int(20/4)+1 = 5+1 = 6 -> clamp 5)
    """
    raw = int((20 - d2_emotion) / 4) + 1
    return max(1, min(5, raw))


def _map_d5_to_ending_state(d5_completion: int) -> str:
    """Map D5_completion (0-20 scale) to ending_state enum.

    Thresholds (CONTEXT.md):
        D5 >= 16 -> "resolved"
        D5 >= 12 -> "new_suspense"
        else     -> "cliffhanger"
    """
    if d5_completion >= 16:
        return "resolved"
    if d5_completion >= 12:
        return "new_suspense"
    return "cliffhanger"


# ─── Phase 41-02: Wilson CI + converged flag (pure stdlib) ────────────

def _wilson_ci(passed: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval (pure stdlib — uses math.sqrt only).

    Returns ``(lower, upper)`` bounds at the given z-score (default 1.96 = 95% CI).
    Returns ``(0.0, 1.0)`` — the widest possible interval — when ``total <= 0``
    (CONTEXT.md: divide-by-zero mitigation, threat T-41-09).

    Formula (CONTEXT.md "Wilson confidence interval"):
        p_hat   = passed / total
        denom   = 1 + z^2 / total
        center  = (p_hat + z^2 / (2 * total)) / denom
        spread  = z * sqrt((p_hat * (1 - p_hat) + z^2 / (4 * total)) / total) / denom

    Pure stdlib verification (threat T-41-12): the function body uses
    ``math.sqrt`` only; no third-party scientific libraries are imported
    anywhere in this module. The corresponding unit test introspects this
    function's source via ``inspect.getsource`` and asserts the absence of
    forbidden third-party-library tokens.
    """
    if total <= 0:
        return (0.0, 1.0)
    p = passed / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return (center - spread, center + spread)


def _is_converged(
    sample_size: int,
    lower: float,
    upper: float,
    *,
    min_sample: int = 10,
    max_spread: float = 0.10,
) -> bool:
    """Converged iff ``sample_size >= min_sample`` AND ``(upper - lower) <= max_spread``.

    CONTEXT.md "Converged flag": ±5% half-width means total spread ≤ 10%.
    Both conditions required (sample sufficiency AND tightness).
    """
    return sample_size >= min_sample and (upper - lower) <= max_spread


# ─── Phase 41-03: similarity helpers (pure stdlib) ─────────────────────
# CONTEXT.md "Structure similarity algorithm" (LOCKED):
#   final score = 0.7 * cosine(numerical) + 0.3 * jaccard(emotion_sequence)
# - cosine over the 3-dim numerical vector
#   [hook_position_sec, mean(turning_points_sec), emotion_drop_level]
#   (turning_points_sec list is collapsed to its mean BEFORE cosine —
#    WARNING #4 refinement, keeps the vector a fixed-width comparable form)
# - jaccard over the emotion_sequence lists treated as sets
# Pure stdlib throughout (math.sqrt + set built-in — NO third-party
# scientific libraries, threat T-41-15 mitigation).


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity = dot(a, b) / (||a|| * ||b||).

    Returns ``0.0`` if either vector has zero magnitude (avoids divide-by-zero —
    threat T-41-14 mitigation; CONTEXT.md "Edge case" requires this degrade).
    Pure stdlib: uses ``sum`` + ``math.sqrt`` only (no third-party libs).

    Range: ``[-1.0, 1.0]``. ``1.0`` = identical direction; ``0.0`` = orthogonal
    or zero-vector input; ``-1.0`` = opposite direction.
    """
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _jaccard_similarity(list_a: list[str], list_b: list[str]) -> float:
    """Jaccard similarity = ``|A ∩ B| / |A ∪ B|`` over the two lists as sets.

    Returns ``0.0`` if both lists are empty (union has zero size — avoids
    divide-by-zero). Order-insensitive and duplicate-insensitive (set
    semantics — duplicates collapse, does not inflate the score).

    Range: ``[0.0, 1.0]``. ``1.0`` = identical sets; ``0.0`` = disjoint or empty.
    """
    set_a = set(list_a)
    set_b = set(list_b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _structure_to_numerical_vector(structure: dict) -> list[float]:
    """Extract the 3-dim numerical vector used for cosine similarity.

    Vector layout (CONTEXT.md "Cosine similarity over numerical fields"):
        [hook_position_sec, mean(turning_points_sec), emotion_drop_level]

    WARNING #4 refinement (CONTEXT.md): the ``turning_points_sec`` list is
    compressed to its scalar mean BEFORE cosine — the cosine vector must be a
    fixed-width comparable form, and the list-of-ints field cannot be fed
    directly into a dot product against another recipe's list (which may have
    a different length).

    Degrade rules:
        - Missing ``hook_position_sec`` -> ``0.0``
        - Missing or empty ``turning_points_sec`` -> mean ``0.0``
        - Missing ``emotion_drop_level`` -> ``0.0``
    """
    hook = float(structure.get("hook_position_sec", 0) or 0)
    tp_list = structure.get("turning_points_sec") or []
    tp_mean = float(sum(tp_list) / len(tp_list)) if tp_list else 0.0
    drop = float(structure.get("emotion_drop_level", 0) or 0)
    return [hook, tp_mean, drop]


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

    # ── Helper: extract_structure_from_episode (RECIPE-LIB-04) ────────
    # DATA SOURCE PIVOT (plan-checker BLOCKER #1, locked 2026-06-27):
    #   Reads `story-framework` + `final-audit` AssetBus slots (NOT the
    #   lineage hash-stamping slot — that contains only hashes, no creative
    #   content per V5.0 verified reality).
    #   - story-framework slot: story_kernel.mcmahon_arc, snowflake_artifacts.
    #     anchor_validation, snyder_beats_summary (structural data).
    #   - final-audit slot: scores.D2_emotion, scores.D5_completion (quality scores).
    #
    # This is a HELPER — best-effort. Missing/malformed slot -> None + WARNING log.
    # Operators can pass explicit structure{} to create_recipe to override.

    def extract_structure_from_episode(self, episode_id: str) -> dict | None:
        """Extract a structure{} dict from V5.0 story-framework + final-audit slots.

        Applies the CONTEXT.md mapping table:
            hook_position_sec     <- snowflake_artifacts.anchor_validation ("Catalyst ~Ns")
                                     with fallback to first snyder_beats range
            emotion_sequence      <- story_kernel.mcmahon_arc (lookup table)
            turning_points_sec    <- snowflake_artifacts.anchor_validation (all "~Ns")
            emotion_drop_level    <- scores.D2_emotion (int((20-D2)/4)+1 clamp [1,5])
            ending_state          <- scores.D5_completion (>=16 resolved /
                                     >=12 new_suspense / else cliffhanger)

        Args:
            episode_id: Episode identifier for traceability. The bus slots are
                per-workdir (one workdir per episode), so the method reads
                whatever story-framework + final-audit the bus currently holds.
                ``episode_id`` is recorded in WARNING logs for traceability
                but is NOT used to filter the bus — caller is responsible for
                pointing the bus at the correct workdir.

        Returns:
            structure dict with 5 fields, OR None if either slot is missing/
            malformed (best-effort helper — does NOT raise).
        """
        # 1. Read both slots (None if missing — bus.read returns None on
        #    FileNotFoundError / JSONDecodeError per asset_bus.py:512).
        sf = self._bus.read("story-framework")
        fa = self._bus.read("final-audit")

        if sf is None or fa is None:
            logger.warning(
                "extract_structure_from_episode: missing story-framework or "
                "final-audit slot for episode %s (sf=%s, fa=%s)",
                episode_id,
                "present" if sf is not None else "MISSING",
                "present" if fa is not None else "MISSING",
            )
            return None

        # 2. Validate slot shapes (defensive — V5.0 schema drift protection).
        if not isinstance(sf, dict) or "story_kernel" not in sf or "snowflake_artifacts" not in sf:
            logger.warning(
                "extract_structure_from_episode: malformed story-framework for "
                "episode %s (missing story_kernel or snowflake_artifacts)",
                episode_id,
            )
            return None
        if not isinstance(fa, dict) or "scores" not in fa:
            logger.warning(
                "extract_structure_from_episode: malformed final-audit for "
                "episode %s (missing scores)",
                episode_id,
            )
            return None

        # 3. emotion_sequence — mcmahon_arc lookup (fallback on unknown arc).
        arc = sf["story_kernel"].get("mcmahon_arc", "")
        emotion_sequence = MCMAHON_ARC_EMOTIONS.get(arc)
        if emotion_sequence is None:
            logger.warning(
                "extract_structure_from_episode: unknown mcmahon_arc %r for "
                "episode %s, using fallback sequence %s",
                arc, episode_id, _MCMAHON_FALLBACK_SEQUENCE,
            )
            emotion_sequence = list(_MCMAHON_FALLBACK_SEQUENCE)
        else:
            emotion_sequence = list(emotion_sequence)  # defensive copy

        # 4. hook_position_sec + turning_points_sec — anchor_validation parse.
        anchor_str = sf["snowflake_artifacts"].get("anchor_validation", "")
        hook_pos, turning_points = _parse_anchor_validation(anchor_str)

        # 4b. hook fallback: Catalyst absent -> first snyder_beats range lower bound.
        if hook_pos is None:
            beats = sf.get("snyder_beats_summary", []) or []
            for beat in beats:
                if not isinstance(beat, str):
                    continue
                m = _RE_FIRST_BEAT_RANGE.search(beat)
                if m:
                    hook_pos = int(m.group(1))
                    break
            if hook_pos is None:
                logger.warning(
                    "extract_structure_from_episode: no Catalyst timestamp and "
                    "no parseable snyder_beats range for episode %s, defaulting "
                    "hook_position_sec to 0",
                    episode_id,
                )
                hook_pos = 0

        # 5. D2_emotion -> emotion_drop_level (single-step, no double quantization).
        d2 = fa["scores"].get("D2_emotion")
        if not isinstance(d2, int) or isinstance(d2, bool):
            logger.warning(
                "extract_structure_from_episode: D2_emotion not int for episode "
                "%s (got %r), cannot extract",
                episode_id, d2,
            )
            return None
        emotion_drop_level = _map_d2_to_drop_level(d2)

        # 6. D5_completion -> ending_state.
        d5 = fa["scores"].get("D5_completion")
        if not isinstance(d5, int) or isinstance(d5, bool):
            logger.warning(
                "extract_structure_from_episode: D5_completion not int for "
                "episode %s (got %r), cannot extract",
                episode_id, d5,
            )
            return None
        ending_state = _map_d5_to_ending_state(d5)

        return {
            "hook_position_sec": hook_pos,
            "emotion_sequence": emotion_sequence,
            "turning_points_sec": turning_points,
            "emotion_drop_level": emotion_drop_level,
            "ending_state": ending_state,
        }

    # ── Core method 4: update_validation (RECIPE-LIB-01) ─────────────
    # Phase 42 contract — signature is LOCKED. feedback_ingest.py will call
    # this method after each feedback submission to close the convergence loop.

    def update_validation(
        self,
        recipe_id: str,
        platform: str,
        completion_rate: float,
        sample_size_delta: int = 1,
    ) -> dict | None:
        """Append a new validation{} version row to an existing recipe.

        This method is the **Phase 42 contract** — ``feedback_ingest.
        FeedbackIngestClient`` calls it after each feedback submission to
        close the convergence loop. Signature is LOCKED.

        Flow (CONTEXT.md "update_validation flow" — 4 steps):
          1. Read latest recipe version (KeyError propagates if unknown).
          2. Input validation: completion_rate in [0,1]; sample_size_delta >= 1;
             platform must be a non-empty real value (not the "" unset sentinel).
          3. Compute new validation{}: running-average completion_rate blend
             old + new, recompute Wilson CI + converged flag.
          4. Append a new row with version = latest + 1 (NEVER mutate latest);
             last_validated = now ISO 8601 UTC. Return the new row. On bus
             failure, log warning + return None (does NOT propagate).

        Args:
            recipe_id: Target recipe identifier.
            platform: Platform enum (douyin | bilibili | youtube). Must be a
                real value on update, NOT the empty "" unset sentinel used
                only on initial create_recipe.
            completion_rate: Float in [0.0, 1.0] for this batch of feedback.
            sample_size_delta: How many new samples this update represents
                (default 1; pass larger values for batch ingest).

        Returns:
            New version row dict, OR None if the AssetBus append failed
            (degraded mode — logs WARNING, does not raise).

        Raises:
            KeyError: if recipe_id is unknown (delegates to get_recipe).
            ValueError: if completion_rate is outside [0,1], sample_size_delta
                < 1, or platform is not a valid non-empty platform enum.
        """
        # Step 1: Read latest version (KeyError propagates if unknown — Test 9).
        latest = self.get_recipe(recipe_id)

        # Step 2: Input validation (threat T-41-10 — Elevation of Privilege).
        if not isinstance(completion_rate, (int, float)) or isinstance(completion_rate, bool):
            raise ValueError(
                f"completion_rate must be float in [0,1], got {completion_rate!r}"
            )
        if not (0.0 <= float(completion_rate) <= 1.0):
            raise ValueError(
                f"completion_rate must be in [0,1], got {completion_rate!r}"
            )
        if not isinstance(sample_size_delta, int) or isinstance(sample_size_delta, bool):
            raise ValueError(
                f"sample_size_delta must be int >= 1, got {sample_size_delta!r}"
            )
        if sample_size_delta < 1:
            raise ValueError(
                f"sample_size_delta must be >= 1, got {sample_size_delta!r}"
            )
        # Platform must be a real value on update (not the "" unset sentinel).
        valid_update_platforms = _VALID_PLATFORMS - {""}
        if platform not in valid_update_platforms:
            raise ValueError(
                f"platform must be one of {sorted(valid_update_platforms)}, "
                f"got {platform!r}"
            )

        # Step 3: Compute new validation{} fields.
        old_v = latest["validation"]
        old_sample = old_v.get("sample_size", 0)
        old_cr = old_v.get("completion_rate", 0.0)
        new_sample_size = old_sample + sample_size_delta

        # Running average: blend old completion_rate (weighted by old sample_size)
        # with the new batch (weighted by sample_size_delta). Single-step from
        # raw values (WARNING #1 — no double quantization).
        if new_sample_size > 0:
            cumulative_passed = old_cr * old_sample
            new_completion_rate = (
                cumulative_passed + float(completion_rate) * sample_size_delta
            ) / new_sample_size
        else:
            new_completion_rate = 0.0

        passed_int = int(round(new_completion_rate * new_sample_size))
        lower, upper = _wilson_ci(passed_int, new_sample_size)
        ci_str = f"±{int(round((upper - lower) / 2 * 100))}%"
        new_converged = _is_converged(new_sample_size, lower, upper)

        # Step 4: Build new row (NEVER mutate latest — append-only invariant).
        new_row = copy.deepcopy(latest)
        new_row["version"] = latest.get("version", 1) + 1
        new_row["validation"] = {
            "platform": platform,
            "completion_rate": new_completion_rate,
            "confidence_interval": ci_str,
            "sample_size": new_sample_size,
            "converged": new_converged,
        }
        new_row.setdefault("provenance", {})["last_validated"] = _now_iso()

        try:
            self._bus.append_line(self.SLOT, new_row)
        except Exception as e:
            # Threat T-41-11 (Repudiation): log warning, do NOT propagate.
            # Old version row is unaffected (no partial write — we deep-copied).
            logger.warning(
                "RecipeLibrary update_validation degraded for %s: %s",
                recipe_id, e,
            )
            return None

        logger.info(
            "RecipeLibrary update_validation: %s v%s (sample=%d, cr=%.3f, ci=%s, converged=%s)",
            recipe_id, new_row["version"], new_sample_size,
            new_completion_rate, ci_str, new_converged,
        )
        return new_row
