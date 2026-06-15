"""Generic ``skill_invoke`` ACP tool — dispatch an input to a movie-expert skill.

This module registers a Hermes tool (``skill_invoke``) that ACP clients can
call to invoke one of the bundled ``skills/movie-experts/`` experts directly
with an arbitrary input string. The tool:

1. Discovers every ``movie-experts/<name>/SKILL.md`` and extracts its
   ``metadata.hermes.expert_id`` to populate the ``expert_id`` enum.
2. Loads the requested skill body via the existing ``skill_view`` helper so
   refs / preprocessing / plugin fallback all behave identically to the
   ``/skill_view`` slash command.
3. Returns a JSON payload combining skill metadata, the loaded body, the
   caller's input, and the optional context — letting the ACP client model
   operate as the expert without first having to issue a separate
   ``skill_view`` round-trip.

The tool surfaces in ACP sessions because ``_expand_acp_enabled_toolsets``
in ``acp_adapter/session.py`` always includes the ``movie-experts``
toolset, which this module creates via ``create_custom_toolset`` at import
time.

Importing this module is intentionally side-effectful: registration runs
once when ``acp_adapter.server`` is first imported (which ``hermes-acp
--check`` exercises), so the tool is available to every ACP session.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.registry import registry

logger = logging.getLogger(__name__)


# Toolset that owns skill_invoke. Created at import time via
# ``create_custom_toolset`` so the rest of the Hermes tool resolver can
# treat it like any built-in toolset.
SKILL_INVOKE_TOOLSET = "movie-experts"

# Category directory under the bundled skills root that holds every
# movie-expert skill. Hardcoded so the enum stays narrow even when other
# skill categories live alongside it.
_MOVIE_EXPERTS_CATEGORY = "movie-experts"


def _candidate_skill_roots() -> List[Path]:
    """Return directories that may contain the bundled movie-experts skills.

    Mirrors the lookup order used by ``tools.skills_tool``: the canonical
    ``$HERMES_HOME/skills`` first, then ``skills.external_dirs`` from
    config.yaml, then the in-tree ``skills/`` directory at the project
    root (for dev runs where the bundled skills have not yet been
    installed into ``~/.hermes``).
    """
    roots: List[Path] = []
    seen: set = set()

    def _add(path: Path) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen:
            return
        seen.add(resolved)
        roots.append(path)

    try:
        from hermes_constants import get_hermes_home

        _add(get_hermes_home() / "skills")
    except Exception:
        logger.debug("Could not resolve HERMES_HOME skills dir", exc_info=True)

    try:
        from agent.skill_utils import get_external_skills_dirs

        for external in get_external_skills_dirs():
            _add(external)
    except Exception:
        logger.debug("Could not enumerate external skills dirs", exc_info=True)

    # Dev fallback: in-tree skills/ directory next to this package's parent.
    # Lets ``hermes-acp --check`` succeed in a fresh checkout before any
    # ``hermes postinstall`` has copied skills into ~/.hermes/skills.
    try:
        in_tree = Path(__file__).resolve().parent.parent / "skills"
        if in_tree.is_dir():
            _add(in_tree)
    except Exception:
        logger.debug("Could not resolve in-tree skills dir", exc_info=True)

    return roots


def _extract_expert_id(frontmatter: Dict[str, Any], fallback_name: str) -> str:
    """Pull ``metadata.hermes.expert_id`` out of parsed frontmatter, with a fallback."""
    metadata = frontmatter.get("metadata") if isinstance(frontmatter.get("metadata"), dict) else {}
    hermes = metadata.get("hermes") if isinstance(metadata.get("hermes"), dict) else {}
    raw = str(hermes.get("expert_id") or "").strip()
    if raw:
        return raw
    return str(frontmatter.get("name") or fallback_name).strip()


def _parse_skill_frontmatter(skill_md: Path) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter from a SKILL.md, returning None on any failure."""
    try:
        from agent.skill_utils import parse_frontmatter

        text = skill_md.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        return fm if isinstance(fm, dict) else None
    except Exception:
        logger.debug("Could not parse frontmatter from %s", skill_md, exc_info=True)
        return None


def discover_movie_experts() -> List[Dict[str, str]]:
    """Return ``[{expert_id, name, skill_dir}]`` for every movie-expert skill.

    Deduplicates by ``expert_id`` so the same skill discovered under both
    ``~/.hermes/skills/`` and the in-tree dev copy only surfaces once.
    The first occurrence wins (HERMES_HOME has priority, matching the
    skill loader's lookup order).
    """
    discovered: List[Dict[str, str]] = []
    seen_ids: set = set()

    for root in _candidate_skill_roots():
        category_dir = root / _MOVIE_EXPERTS_CATEGORY
        if not category_dir.is_dir():
            continue
        for skill_md in sorted(category_dir.glob("*/SKILL.md")):
            fm = _parse_skill_frontmatter(skill_md)
            if not fm:
                continue
            expert_id = _extract_expert_id(fm, fallback_name=skill_md.parent.name)
            if not expert_id or expert_id in seen_ids:
                continue
            seen_ids.add(expert_id)
            discovered.append(
                {
                    "expert_id": expert_id,
                    "name": str(fm.get("name") or skill_md.parent.name),
                    "skill_dir": str(skill_md.parent),
                    "description": str(fm.get("description") or "").strip(),
                }
            )

    return discovered


# Discovered at import time so the JSON schema enum is stable for the
# lifetime of the process. Adding a new expert requires a restart —
# consistent with how every other Hermes tool behaves (the tool catalog
# is built once at ACP server startup).
_EXPERTS: List[Dict[str, str]] = discover_movie_experts()
_EXPERT_BY_ID: Dict[str, Dict[str, str]] = {entry["expert_id"]: entry for entry in _EXPERTS}
_EXPERT_IDS: List[str] = sorted(_EXPERT_BY_ID.keys())


def _skill_invoke_handler(args: Dict[str, Any], **_kwargs: Any) -> str:
    """Tool entry point: load the requested expert skill and bundle the input.

    Returns a JSON string matching the convention used by ``skill_view``
    so the existing ACP completion formatter (``_format_generic_structured_result``
    in ``acp_adapter/tools.py``) renders it without a special case.
    """
    expert_id = str(args.get("expert_id") or "").strip()
    user_input = str(args.get("input") or "").strip()
    context = str(args.get("context") or "").strip()

    if not expert_id:
        return json.dumps(
            {
                "success": False,
                "error": "expert_id is required.",
                "available_experts": _EXPERT_IDS,
            },
            ensure_ascii=False,
        )

    entry = _EXPERT_BY_ID.get(expert_id)
    if entry is None:
        return json.dumps(
            {
                "success": False,
                "error": f"Unknown expert_id '{expert_id}'.",
                "available_experts": _EXPERT_IDS,
            },
            ensure_ascii=False,
        )

    if not user_input:
        return json.dumps(
            {
                "success": False,
                "error": "input is required (the prompt or task to hand to the expert).",
                "expert_id": expert_id,
            },
            ensure_ascii=False,
        )

    # Load the SKILL.md body straight from the discovered ``skill_dir``.
    # We can't use the public ``skill_view(name=...)`` resolver here because
    # name-based resolution deliberately refuses to disambiguate when two
    # categories ship a skill with the same name (e.g. ``movie-experts/
    # screenplay`` and ``movie-production/screenplay`` both exist). Discovery
    # already pinned the exact directory we want, so read it directly.
    skill_md_path = Path(entry["skill_dir"]) / "SKILL.md"
    try:
        raw_text = skill_md_path.read_text(encoding="utf-8")
    except OSError as exc:
        return json.dumps(
            {
                "success": False,
                "error": f"Could not read SKILL.md for expert '{expert_id}' at {skill_md_path}: {exc}",
            },
            ensure_ascii=False,
        )

    # Strip frontmatter so the model gets the skill body verbatim, matching
    # what ``skill_view`` injects into the conversation.
    try:
        from agent.skill_utils import parse_frontmatter

        _, skill_body = parse_frontmatter(raw_text)
    except Exception:
        # If frontmatter parsing fails for any reason, ship the whole file —
        # the model can still operate on it, just with metadata noise.
        skill_body = raw_text
    skill_body = skill_body.strip()

    skill_body = skill_body
    response: Dict[str, Any] = {
        "success": True,
        "expert_id": expert_id,
        "skill_name": entry["name"],
        "skill_description": entry.get("description") or "",
        "input": user_input,
        "context": context,
        "skill_body": skill_body,
        "message": (
            f"Skill '{entry['name']}' loaded for expert_id '{expert_id}'. "
            "Operate as this expert on the provided input."
        ),
    }
    return json.dumps(response, ensure_ascii=False)


def _build_schema() -> Dict[str, Any]:
    """Construct the OpenAI-style function schema, with the live expert enum."""
    return {
        "name": "skill_invoke",
        "description": (
            "Invoke a movie-expert skill by expert_id with an arbitrary input. "
            "Loads the expert's SKILL.md body and returns it together with the "
            "caller's input and (optional) context, so the agent can operate "
            "as that expert. Use this when a task clearly maps to one of the "
            "movie-experts (e.g. screenplay, colorist, hook_retention). For "
            "browsing skill catalogs or loading skills generically, prefer "
            "skill_view / skills_list."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expert_id": {
                    "type": "string",
                    "description": "Stable identifier of the movie-expert to invoke.",
                    "enum": list(_EXPERT_IDS),
                },
                "input": {
                    "type": "string",
                    "description": (
                        "The task or prompt to hand to the expert. The expert "
                        "operates on this verbatim."
                    ),
                },
                "context": {
                    "type": "string",
                    "description": (
                        "Optional supporting context (prior artifacts, "
                        "constraints, style notes) the expert should fold in. "
                        "Omit when not applicable."
                    ),
                },
            },
            "required": ["expert_id", "input"],
        },
    }


def _ensure_toolset_registered() -> None:
    """Create the ``movie-experts`` toolset at runtime so the tool resolver finds it.

    Idempotent: re-running overwrites the entry, which is what we want when
    this module is re-imported in a long-lived process (tests, etc.).
    """
    try:
        from toolsets import create_custom_toolset

        create_custom_toolset(
            name=SKILL_INVOKE_TOOLSET,
            description=(
                "Movie-expert dispatcher — exposes skill_invoke for routing "
                "tasks to a specific movie-expert skill via expert_id."
            ),
            tools=["skill_invoke"],
            includes=[],
        )
    except Exception:
        logger.debug(
            "Could not create '%s' toolset via create_custom_toolset",
            SKILL_INVOKE_TOOLSET,
            exc_info=True,
        )


def register_skill_invoke_tool() -> None:
    """Register ``skill_invoke`` with the global tool registry.

    Safe to call multiple times — subsequent calls just re-register the
    same entry (the registry allows same-toolset overwrites without
    ``override=True``).
    """
    schema = _build_schema()
    registry.register(
        name="skill_invoke",
        toolset=SKILL_INVOKE_TOOLSET,
        schema=schema,
        handler=_skill_invoke_handler,
        # No check_fn: skill_invoke depends only on the bundled skill
        # corpus, which the adapter ships with. Always available.
        check_fn=None,
        is_async=False,
        description=schema["description"],
        emoji="🎬",
    )


# Module-import side effect: register the toolset + tool. Doing this at
# import time (rather than requiring an explicit call) matches the
# pattern used by every ``tools/*_tool.py`` module and ensures the tool
# is available by the time ``hermes-acp --check`` finishes.
_ensure_toolset_registered()
register_skill_invoke_tool()

logger.debug(
    "skill_invoke registered with %d movie-experts: %s",
    len(_EXPERT_IDS),
    ", ".join(_EXPERT_IDS) or "(none discovered)",
)
