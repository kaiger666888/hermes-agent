"""lookup.py — formula ranking engine (Plan 39-01, FORM-04 lookup half).

Given ``genre`` + ``mood`` + ``platform``, return top-k formulas ranked by
``platform_fit[platform].fit_score`` descending. Ties broken by ``formula_id``
ascending (deterministic for test stability).

Module-level cache (``_LIBRARY_CACHE``) avoids repeated disk walks for the
default library dir; explicit ``library_dir`` arg bypasses cache (for tests).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations``.
  - Keyword-only args (the ``*`` separator) on public functions.
  - Double-quoted strings.
  - ``encoding="utf-8"`` on any read_text (none directly here — delegated to
    ``FormulaLibrary.load_from_dir``).
  - ``logger = logging.getLogger(__name__)``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from plugins.formula_library.schema import Formula, FormulaLibrary

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level cache for the default library dir
# ---------------------------------------------------------------------------
#
# Keyed on the default dir only (``Path(__file__).resolve().parent / "library"``).
# Explicit ``library_dir`` arg bypasses the cache so tests can point at
# synthetic tmp_path libraries without polluting the cache.
#
# Reset by tests via ``_LIBRARY_CACHE = None`` (see test_lookup.py setup_method).
# The cache holds a single FormulaLibrary instance — repeated lookups in the
# same process reuse it. T-39-03 mitigation: avoids disk walk per lookup call
# (current library is 10 formulas; future 50+ formulas would still be cheap
# but the cache eliminates even that cost).
_LIBRARY_CACHE: FormulaLibrary | None = None


# ---------------------------------------------------------------------------
# load_library
# ---------------------------------------------------------------------------


def load_library(library_dir: Path | None = None) -> FormulaLibrary:
    """Load the FormulaLibrary from ``library_dir`` (default = plugin's library/).

    If ``library_dir`` is None, defaults to ``Path(__file__).resolve().parent
    / "library"`` and uses the module-level cache. Explicit ``library_dir``
    always bypasses the cache (loads fresh from disk).

    Args:
        library_dir: optional explicit path to a directory of ``formula_*.json``
            files. None = use default plugin library dir.

    Returns:
        FormulaLibrary. Empty if dir missing or all files invalid (degrade
        gracefully — never raises on disk / validation errors).
    """
    global _LIBRARY_CACHE

    if library_dir is not None:
        # Explicit dir bypasses cache — caller (typically a test) wants fresh.
        return FormulaLibrary.load_from_dir(Path(library_dir))

    if _LIBRARY_CACHE is not None:
        return _LIBRARY_CACHE

    default_dir = Path(__file__).resolve().parent / "library"
    _LIBRARY_CACHE = FormulaLibrary.load_from_dir(default_dir)
    logger.debug(
        "formula_library cache populated from %s with %d formulas",
        default_dir, len(_LIBRARY_CACHE.formulas),
    )
    return _LIBRARY_CACHE


# ---------------------------------------------------------------------------
# lookup_formulas
# ---------------------------------------------------------------------------


def lookup_formulas(
    *,
    genre: str,
    mood: str,
    platform: str,
    top_k: int = 3,
) -> list[Formula]:
    """Return top-k formulas matching ``genre`` + ``mood``, ranked by platform fit.

    Contract (FORM-04 lookup half):
      - Strict filter: both ``genre`` and ``mood`` must match exactly.
      - Rank by ``platform_fit[platform].fit_score`` descending.
      - Missing ``platform`` entry on a formula = fit_score 0.0 (treated as
        platform-agnostic unknown, NOT excluded).
      - Ties broken by ``formula_id`` ascending (deterministic for tests).
      - Empty library or no matches → empty list (NOT an exception).

    Args:
        genre: one of the 5 genres (Literal-enforced upstream by Pydantic).
        mood: one of the 2 moods.
        platform: one of the 6 platforms.
        top_k: maximum formulas to return. Default 3 per FORM-04 spec.

    Returns:
        list[Formula] — at most ``top_k`` Pydantic Formula objects, ranked.
    """
    library = load_library()
    candidates = library.filter(genre=genre, mood=mood)

    def _fit_score(formula: Formula) -> float:
        """Extract fit_score for ``platform`` from formula, 0.0 if no entry."""
        for pf in formula.platform_fit:
            if pf.platform == platform:
                return pf.fit_score
        return 0.0

    # Sort by (-fit_score, formula_id) — primary desc, tiebreak id asc.
    ranked = sorted(
        candidates,
        key=lambda f: (-_fit_score(f), f.formula_id),
    )
    return ranked[:top_k]


__all__ = ["load_library", "lookup_formulas"]
