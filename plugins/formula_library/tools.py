"""tools.py — formula_lookup JSON-schema + dispatch handler (Plan 39-01, FORM-04).

Mirrors the ``plugins/review_gates/tools.py`` pattern:
- ``FORMULA_LOOKUP_SCHEMA`` is a JSON-schema dict declaring the tool's args.
- ``_handle_formula_lookup`` is the handler that the plugin loader registers.
- Handler delegates to ``lookup_formulas`` (Plan 39-01 Task 2) inside the
  function body so this module imports cleanly even before lookup.py exists.
- On invalid args (missing required field), returns a ``tool_error`` envelope.
- On success, returns a ``tool_result`` envelope with ``formulas`` (list of
  JSON-serialized Formula dicts via ``model_dump(mode="json")``) + ``count``.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations``.
  - Double-quoted strings.
  - ``encoding="utf-8"`` on any read_text (none in this module).
  - Lazy import of lookup.py to avoid circular imports + module-load ordering.
"""

from __future__ import annotations

import logging
from typing import Any

from plugins.formula_library.schema import (
    GENRES,
    MOODS,
    PLATFORMS,
)
from tools.registry import tool_error, tool_result

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema (interface — declared here, locked by Plan 39-01)
# ---------------------------------------------------------------------------


FORMULA_LOOKUP_SCHEMA = {
    "name": "formula_lookup",
    "description": (
        "Look up top-k short-drama formulas ranked by platform fit. "
        "Returns formulas matching the given genre + mood, ranked by "
        "platform_fit[platform].fit_score (descending). Default top_k=3. "
        "中文:检索 top-k 爆款公式,按 platform_fit 降序排列,作为 Step 0 创意起点。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "genre": {
                "type": "string",
                "enum": list(GENRES),
                "description": (
                    "Genre axis (5 values): 都市奇幻 / 悬疑反转 / 家庭情感 / "
                    "校园青春 / 职场商战."
                ),
            },
            "mood": {
                "type": "string",
                "enum": list(MOODS),
                "description": "Mood axis (2 values): 轻喜剧 / 虐心.",
            },
            "platform": {
                "type": "string",
                "enum": list(PLATFORMS),
                "description": (
                    "Target platform (6 values): 抖音 / 快手 / B站 / 小红书 / "
                    "视频号 / 红果."
                ),
            },
            "top_k": {
                "type": "integer",
                "default": 3,
                "minimum": 1,
                "maximum": 20,
                "description": "Maximum formulas to return (default 3).",
            },
        },
        "required": ["genre", "mood", "platform"],
    },
}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

_REQUIRED_ARGS = ("genre", "mood", "platform")


def _handle_formula_lookup(args: dict, **_kwargs: Any) -> str:
    """Dispatch ``formula_lookup`` to ``lookup_formulas``.

    Args:
        args: tool args dict from the agent. Must contain ``genre``, ``mood``,
            ``platform`` (all required). Optional ``top_k`` (default 3).

    Returns:
        JSON-serialized tool_result envelope on success::

            {"formulas": [<Formula.model_dump>, ...], "count": <int>}

        Or a tool_error envelope on missing/invalid args::

            {"error": "...", "received": {...}}
    """
    # Validate required args first — surface a helpful error before delegating.
    missing = [k for k in _REQUIRED_ARGS if not args.get(k)]
    if missing:
        return tool_error(
            f"formula_lookup requires {','.join(missing)}",
            missing=missing,
            received={k: args.get(k) for k in _REQUIRED_ARGS},
        )

    genre = args["genre"]
    mood = args["mood"]
    platform = args["platform"]
    top_k = args.get("top_k", 3)

    # Lazy import: lookup.py is created in Task 2 of this plan. Importing it
    # here (inside the function body) keeps this module importable even before
    # lookup.py exists, and avoids any circular-import risk at module load.
    from plugins.formula_library.lookup import lookup_formulas

    try:
        results = lookup_formulas(
            genre=genre, mood=mood, platform=platform, top_k=top_k,
        )
    except Exception as exc:  # noqa: BLE001 — degrade gracefully on any lookup failure
        logger.exception("formula_lookup failed: %s", exc)
        return tool_error(
            f"formula_lookup failed: {exc}",
            genre=genre, mood=mood, platform=platform,
        )

    # Convert Pydantic Formula objects to JSON-serializable dicts.
    # ``mode="json"`` ensures date objects serialize as ISO strings.
    serialized = [f.model_dump(mode="json") for f in results]
    return tool_result({
        "formulas": serialized,
        "count": len(serialized),
        "query": {"genre": genre, "mood": mood, "platform": platform, "top_k": top_k},
    })
