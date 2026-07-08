"""Agent registry YAML loader (INFRA-01).

Loads + validates ``~/.hermes/agents/*.agent.yaml`` against the locked v10.0
``agents-schema.yaml`` (Draft 2020-12). The loader is the foundation for
INFRA-02's ``agents_list`` / ``agent_describe`` MCP tools and Phase 53's
9-sample-agent transform.

Public exports
--------------
- ``load_agent_registry(*, force_reload=False) -> list[dict]``
    Walk ``~/.hermes/agents/`` (FLAT glob — no subdirs, see Pitfall #8 in
    52-RESEARCH.md), parse + validate each YAML, return the list. Cached at
    module level for cheap repeat access; ``force_reload=True`` bypasses.
    An empty/missing agents dir returns ``[]``. Return type is preserved
    as ``list[dict]`` for backward compatibility with all v11.0 callers
    (e.g. ``mcp_serve.agents_list`` at line 1541); callers needing the
    missing-expert warnings use ``load_agent_registry_with_warnings``.
- ``load_agent_registry_with_warnings(*, force_reload=False) -> tuple[list[dict], list[str]]``
    NEW sibling (Phase 63). Returns ``(entries, missing_expert_warnings)``
    where ``missing_expert_warnings`` is the list of required DAG expert
    IDs absent from the loaded registry. Phase 67 OBSRV-01 collector
    consumer. Does NOT change ``load_agent_registry`` return type.
- ``load_one_agent_yaml(yaml_path: Path) -> dict``
    Parse + validate a single agent YAML. Raises ``RegistryValidationError``
    with a specific JSON path on schema violation, or with the filename-stem
    invariant text on a name mismatch.
- ``REQUIRED_DAG_EXPERTS``
    Module-level ``frozenset[str]`` of 15 active DAG expert IDs that MUST
    be present in the registry (v10.0 §6.2 verbatim). Source of the
    missing-expert alarm set.
- ``RegistryValidationError``
    Raised when an agent YAML fails schema validation or the filename
    invariant (``name`` field must match filename stem).

Design sources (cite, do not re-derive)
---------------------------------------
- ``.planning/research/v10-orchestrator-design/agents-schema.yaml`` —
  18-field Draft 2020-12 schema, ``additionalProperties: false``, 7
  required fields, ``memory_scope`` enum, ``skill_sha256`` pattern
- ``.planning/phases/52-infra-foundation/52-RESEARCH.md`` §"Code Examples
  §YAML Loader Pattern" — canonical implementation skeleton
- ``tests/conftest.py:_hermetic_environment`` — confirms HERMES_HOME is
  env-var-redirected per-test, so ``get_hermes_home()`` returns the
  redirected path automatically

Threat model mitigations (per 52-01-PLAN.md)
--------------------------------------------
- T-52-01 (Tampering / YAML tags): ``yaml.safe_load`` refuses arbitrary
  tags by default.
- T-52-03 (Spoofing / filename-name mismatch): ``load_one_agent_yaml``
  explicitly verifies ``data["name"] == filename.stem`` and raises
  ``RegistryValidationError`` on mismatch (SC#1 acceptance).
- T-52-04 (Tampering / undeclared fields): ``additionalProperties: false``
  in agents-schema.yaml rejects unknown fields.

CLAUDE.md compliance
--------------------
- ``from __future__ import annotations`` at top (PEP 604 unions)
- ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514)
- ``get_hermes_home()`` instead of ``Path.home() / ".hermes"``
- Lazy %-formatting in log calls
- ``except X as exc:`` with bound name; preserve chains via ``raise ... from exc``
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Required DAG expert set (Phase 63 — missing-expert alarm foundation)
# --------------------------------------------------------------------------- #
# Source: v10.0 design doc 01-AGENT-REGISTRY-SCHEMA.md §6.2 (verbatim from
# ARCHITECTURE §2 lines 128-144). The 15 active DAG experts — load-bearing
# for the collaboration graph (related_agents closure). The other 6 agents
# in the 21-agent registry (animation_studio, documentary_maker, performer,
# production, scene_builder, storyboard_designer) are supporting/non-DAG
# and are NOT required — their absence is not an alarm condition.
# Hard-coded (G1 Option A) rather than config-driven or graph-closure-
# derived: the set is stable since v10.0 (2026-07-06) and auditable as a
# module-level constant with this docstring citing §6.2.
REQUIRED_DAG_EXPERTS: frozenset[str] = frozenset({
    "hook_retention",
    "creative_source",
    "screenplay",
    "script_auditor",
    "character_designer",
    "cinematographer",
    "style_genome",
    "prompt_injector",
    "visual_executor",
    "continuity_auditor",
    "audio_pipeline",
    "editor",
    "colorist",
    "compliance_gate",
    "theory_critic",
})


def _check_required_experts(loaded_names: set[str]) -> list[str]:
    """Return the sorted list of required DAG experts missing from ``loaded_names``.

    Pure function — no side effects, no I/O, no logging. The caller decides
    whether to log, raise, or surface via structured return. Keeping this
    isolated makes it trivially testable (the Phase 63 canary test calls
    this directly with a controlled input set).

    Args:
        loaded_names: the set of ``name`` fields from the loaded agent
            YAMLs (any subset of the 21-agent registry).

    Returns:
        Sorted list (deterministic ordering) of required expert IDs that
        are NOT in ``loaded_names``. Empty list when all 15 required
        experts are present.
    """
    return sorted(REQUIRED_DAG_EXPERTS - loaded_names)


def _emit_missing_expert_warnings(
    missing: list[str], *, agents_dir: Path, loaded_count: int
) -> None:
    """Emit one operator-visible ``logger.warning`` per missing required expert.

    CR-01 fix: this helper is invoked on BOTH the cache-miss AND cache-hit
    paths of ``_load_with_warnings``. Without it, the very first call to
    ``load_agent_registry_with_warnings()`` after process start logs every
    missing expert, but every subsequent call (Phase 67 OBSRV-01 collector
    poll, MCP ``agents_list`` tool, dashboard health endpoint) silently
    returns the structured warnings list without writing to ``agent.log``,
    defeating log-based alerting for any consumer that calls the loader
    more than once per process.

    Args:
        missing: sorted list of required DAG expert IDs absent from the
            registry (the return value of ``_check_required_experts``).
        agents_dir: the agents directory inspected (for the log message).
        loaded_count: number of entries in the loaded registry (0 when
            the agents dir is missing/empty).
    """
    for name in missing:
        logger.warning(
            "registry_loader: required expert %r missing from %s "
            "(loaded %d agents, expected %d required DAG experts)",
            name,
            agents_dir,
            loaded_count,
            len(REQUIRED_DAG_EXPERTS),
        )


# --------------------------------------------------------------------------- #
# Public exceptions
# --------------------------------------------------------------------------- #


class RegistryValidationError(Exception):
    """Raised when an agent YAML fails schema validation or filename invariant.

    WR-02 fix: optional structured fields ``json_path`` and ``invalid_field``
    let MCP closures return typed 400 responses that preserve the
    schema-violation specifics instead of collapsing them into a generic
    ``open_failed`` string. Callers (e.g. ``mcp_serve.round_table_open``)
    can read these attributes to surface the field-level error to the MCP
    client; older callers that just stringify the exception still work.
    """

    def __init__(
        self,
        message: str,
        *,
        json_path: str | None = None,
        invalid_field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.json_path = json_path
        self.invalid_field = invalid_field


# --------------------------------------------------------------------------- #
# Schema loader (cached at module level)
# --------------------------------------------------------------------------- #

_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / ".planning"
    / "research"
    / "v10-orchestrator-design"
    / "agents-schema.yaml"
)

_SCHEMA_CACHE: dict[str, Any] | None = None
_SCHEMA_CACHE_LOCK = threading.Lock()


def _load_schema() -> dict[str, Any]:
    """Load agents-schema.yaml from the v10.0 research directory.

    The schema is the authoritative 18-field Draft 2020-12 contract
    (``additionalProperties: false``, 7 required fields).

    WR-04 fix: validate the loaded value is a dict with the expected
    top-level keys (``type`` or ``$schema``). Without this, an empty or
    YAML-null file would cache as ``None`` and silently poison every
    subsequent ``load_agent_registry`` call — ``Draft202012Validator(None)``
    raises a confusing SchemaError that doesn't mention the actual root
    cause (empty schema file). The validator here raises a specific
    ``RegistryValidationError`` so the operator can triage.
    """
    try:
        with open(_SCHEMA_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as exc:
        # Wrap in RegistryValidationError so callers have a single
        # exception type to catch. This is unrecoverable — without the
        # schema the loader cannot validate any agent YAML.
        logger.error("registry_loader: cannot load agents-schema.yaml at %s: %s", _SCHEMA_PATH, exc)
        raise RegistryValidationError(
            f"cannot load agents-schema.yaml at {_SCHEMA_PATH}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise RegistryValidationError(
            f"agents-schema.yaml at {_SCHEMA_PATH} is not a valid object "
            f"(got {type(data).__name__}); expected a Draft 2020-12 JSON Schema dict"
        )
    if "type" not in data and "$schema" not in data:
        raise RegistryValidationError(
            f"agents-schema.yaml at {_SCHEMA_PATH} is missing both 'type' and "
            f"'$schema' keys; not a valid JSON Schema document"
        )
    return data


def _get_schema() -> dict[str, Any]:
    """Return the cached schema dict, loading on first access (thread-safe)."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE
    with _SCHEMA_CACHE_LOCK:
        if _SCHEMA_CACHE is None:
            _SCHEMA_CACHE = _load_schema()
        return _SCHEMA_CACHE


# --------------------------------------------------------------------------- #
# JSON path formatting helper
# --------------------------------------------------------------------------- #


def _format_json_path(err: jsonschema.ValidationError) -> str:
    """Format a jsonschema error's JSON path.

    WR-06 fix: use ``err.absolute_path`` + ``err.validator_value`` /
    ``err.instance`` directly instead of regex-parsing the human-readable
    ``err.message`` (which is locale- and version-fragile).

    For ``required`` errors (validator == "required"):
        ``err.absolute_path`` is empty (the violation lives at the object
        root), and ``err.validator_value`` is the required-field list. We
        find the missing field via set difference on the instance's keys
        and synthesize ``$.<missing_field>`` so callers see a specific
        path instead of the bare ``$``.

    For other errors: ``err.json_path`` (computed by jsonschema from
        ``absolute_path``) is already specific (e.g. ``$.version``); use
        it directly.
    """
    if err.validator == "required":
        # validator_value is the required-field list — find which one(s)
        # are actually missing from the instance (jsonschema reports the
        # FIRST missing one in its sorted order, but err.instance is the
        # actual object so set difference is reliable).
        required = err.validator_value or []
        instance_keys = (
            list(err.instance.keys()) if isinstance(err.instance, dict) else []
        )
        missing = [r for r in required if r not in instance_keys]
        if missing:
            # Sort for determinism (matches jsonschema's default ordering)
            missing.sort()
            return f"$.{missing[0]}"
        # Fallback if set-difference found nothing (shouldn't happen, but
        # defensive): use the bare json_path.
    return err.json_path


# --------------------------------------------------------------------------- #
# Public loaders
# --------------------------------------------------------------------------- #


def load_one_agent_yaml(yaml_path: Path) -> dict[str, Any]:
    """Parse + validate a single agent YAML file.

    Args:
        yaml_path: path to a ``*.agent.yaml`` file.

    Returns:
        The parsed YAML as a dict.

    Raises:
        RegistryValidationError: if the YAML has invalid syntax, fails
            schema validation (cites a specific JSON path like
            ``$.persona`` or ``$.version``), or has a ``name`` field
            that does not match the filename stem.
    """
    # 1. Parse (yaml.safe_load refuses arbitrary tags — T-52-01 mitigation)
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise RegistryValidationError(
            f"{yaml_path}: invalid YAML syntax: {exc}"
        ) from exc

    if data is None:
        raise RegistryValidationError(
            f"{yaml_path}: empty YAML file — expected an object with required fields"
        )
    if not isinstance(data, dict):
        raise RegistryValidationError(
            f"{yaml_path}: top-level YAML node is {type(data).__name__}, expected object"
        )

    # 2. Schema-validate (additionalProperties:false catches undeclared
    #    fields — T-52-04 mitigation)
    schema = _get_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = _format_json_path(first)
        # WR-02: surface structured json_path + invalid_field so MCP closures
        # can return typed 400 responses preserving schema-violation specifics.
        # WR-02 fix (review): use str.removeprefix("$.") instead of
        # str.lstrip("$."). The lstrip version strips ANY combination of
        # '$' and '.' chars from the left (over-strips edge cases like a
        # hypothetical '$._internal' field that happens to start with '.');
        # removeprefix strips the literal '$.' prefix only. For the bare
        # root path '$', invalid_field stays None (no specific field).
        if path.startswith("$."):
            invalid_field = path.removeprefix("$.")
        else:
            invalid_field = None
        raise RegistryValidationError(
            f"{yaml_path}: schema violation at {path}: {first.message}",
            json_path=path,
            invalid_field=invalid_field,
        )

    # 3. Filename invariant (T-52-03 spoofing mitigation): the YAML's
    #    `name` field MUST match the filename stem.
    expected_stem = yaml_path.name.removesuffix(".agent.yaml")
    actual_name = data.get("name", "")
    if actual_name != expected_stem:
        raise RegistryValidationError(
            f"{yaml_path}: name field {actual_name!r} does not match "
            f"filename stem {expected_stem!r}"
        )

    return data


# Module-level cache for load_agent_registry. Pattern: double-checked
# locking (mirrors providers/__init__.py:140 _discover_providers).
_REGISTRY_CACHE: list[dict[str, Any]] | None = None
_REGISTRY_CACHE_LOCK = threading.Lock()


def load_agent_registry(*, force_reload: bool = False) -> list[dict[str, Any]]:
    """Discover + validate every ``~/.hermes/agents/*.agent.yaml``.

    FLAT glob — only files matching ``*.agent.yaml`` at the TOP level of
    ``~/.hermes/agents/`` are discovered. Files in subdirectories are NOT
    discovered (Pitfall #8 in 52-RESEARCH.md).

    Args:
        force_reload: bypass the cache and re-walk the directory.

    Returns:
        List of validated agent dicts (one per discovered YAML). Empty
        list if ``~/.hermes/agents/`` does not exist or is empty.
        Return type is ``list[dict]`` (NOT a tuple) — preserved for
        backward compatibility with all v11.0 callers. Callers needing
        the missing-expert warnings should use
        ``load_agent_registry_with_warnings`` instead.

    Raises:
        RegistryValidationError: if any YAML in the directory fails schema
            validation or the filename invariant. The error propagates
            (the caller — typically an MCP tool — handles it).

    Note:
        Missing-expert warnings are emitted via ``logger.warning`` inside
        the shared implementation (``_load_with_warnings``) but NOT
        returned by this function. Use ``load_agent_registry_with_warnings``
        to obtain the structured warnings list (Phase 67 OBSRV-01 path).
    """
    entries, _warnings = _load_with_warnings(force_reload=force_reload)
    return entries


def load_agent_registry_with_warnings(
    *, force_reload: bool = False
) -> tuple[list[dict[str, Any]], list[str]]:
    """Discover + validate agents AND return missing-expert warnings.

    NEW sibling (Phase 63) — same discovery + validation behavior as
    ``load_agent_registry``, but returns the structured warnings list so
    downstream consumers (Phase 67 OBSRV-01 collector) don't need to
    scrape ``logger.warning`` records.

    Args:
        force_reload: bypass the cache and re-walk the directory.

    Returns:
        Tuple of ``(entries, missing_expert_warnings)`` where
        ``missing_expert_warnings`` is the sorted list of required DAG
        expert IDs absent from the loaded registry (empty when all 15
        required experts are present). The entries list is the same
        cached object ``load_agent_registry`` would return.

    Raises:
        RegistryValidationError: if any YAML in the directory fails schema
            validation or the filename invariant.
    """
    return _load_with_warnings(force_reload=force_reload)


def _load_with_warnings(
    *, force_reload: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """Shared implementation for both public loader entry points.

    Does the existing FLAT-glob + ``yaml.safe_load`` + ``Draft202012Validator``
    + filename-invariant work, THEN computes the missing-expert warnings
    via ``_check_required_experts`` and emits one ``logger.warning`` per
    missing required DAG expert.

    Cache semantics: the ``entries`` list is cached in ``_REGISTRY_CACHE``
    (list only — NOT the tuple). The warnings list is recomputed on every
    call — both cache-hit (``force_reload=False``) and cache-miss
    (``force_reload=True``) paths invoke ``_check_required_experts`` and
    ``_emit_missing_expert_warnings`` so callers always see fresh warnings
    AND the operator-visible ``logger.warning`` alarm fires on EVERY call
    (CR-01 regression: previously the cache-hit path returned the structured
    list silently, breaking log-based alerting for any consumer that polls
    the loader more than once per process). The entries list alone is
    cached; re-walking the YAML directory (the expensive part) only happens
    on cache miss or ``force_reload=True``.

    Args:
        force_reload: bypass the entries cache.

    Returns:
        Tuple of ``(entries, missing_expert_warnings)``.

    Raises:
        RegistryValidationError: propagated from ``load_one_agent_yaml``.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and not force_reload:
        # Entries cached; recompute warnings from the cache for the
        # structured-return path AND re-emit logger.warning (CR-01 fix).
        cached = _REGISTRY_CACHE
        loaded_names = {e["name"] for e in cached}
        missing = _check_required_experts(loaded_names)
        _emit_missing_expert_warnings(
            missing,
            agents_dir=get_hermes_home() / "agents",
            loaded_count=len(cached),
        )
        return cached, missing

    with _REGISTRY_CACHE_LOCK:
        if _REGISTRY_CACHE is not None and not force_reload:
            # Double-checked-locking cache-hit path — same CR-01 fix.
            cached = _REGISTRY_CACHE
            loaded_names = {e["name"] for e in cached}
            missing = _check_required_experts(loaded_names)
            _emit_missing_expert_warnings(
                missing,
                agents_dir=get_hermes_home() / "agents",
                loaded_count=len(cached),
            )
            return cached, missing

        agents_dir = get_hermes_home() / "agents"
        if not agents_dir.is_dir():
            # Missing agents dir is not an error — treat as "no agents".
            _REGISTRY_CACHE = []
            logger.debug("registry_loader: agents dir %s does not exist", agents_dir)
            # All 15 required experts are missing — surface the warning.
            missing = _check_required_experts(set())
            _emit_missing_expert_warnings(
                missing, agents_dir=agents_dir, loaded_count=0
            )
            return [], missing

        entries: list[dict[str, Any]] = []
        # FLAT glob — no recursion (Pitfall #8). sorted() for deterministic
        # ordering across filesystems (helps tests + operator triage).
        for yaml_path in sorted(agents_dir.glob("*.agent.yaml")):
            entries.append(load_one_agent_yaml(yaml_path))

        _REGISTRY_CACHE = entries
        logger.debug(
            "registry_loader: loaded %d agent YAML(s) from %s",
            len(entries),
            agents_dir,
        )

        # Phase 63: missing-expert alarm — required DAG expert set
        # difference. Pure helper computes the list; we emit one
        # logger.warning per missing expert (operator-visible in
        # ~/.hermes/logs/agent.log) AND surface the structured list
        # for the Phase 67 OBSRV-01 collector.
        loaded_names = {e["name"] for e in entries}
        missing = _check_required_experts(loaded_names)
        _emit_missing_expert_warnings(
            missing, agents_dir=agents_dir, loaded_count=len(entries)
        )
        return entries, missing
