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
    An empty/missing agents dir returns ``[]``.
- ``load_one_agent_yaml(yaml_path: Path) -> dict``
    Parse + validate a single agent YAML. Raises ``RegistryValidationError``
    with a specific JSON path on schema violation, or with the filename-stem
    invariant text on a name mismatch.
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
        invalid_field = path.lstrip("$.") if path.startswith("$.") else None
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

    Raises:
        RegistryValidationError: if any YAML in the directory fails schema
            validation or the filename invariant. The error propagates
            (the caller — typically an MCP tool — handles it).
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and not force_reload:
        return _REGISTRY_CACHE

    with _REGISTRY_CACHE_LOCK:
        if _REGISTRY_CACHE is not None and not force_reload:
            return _REGISTRY_CACHE

        agents_dir = get_hermes_home() / "agents"
        if not agents_dir.is_dir():
            # Missing agents dir is not an error — treat as "no agents".
            _REGISTRY_CACHE = []
            logger.debug("registry_loader: agents dir %s does not exist", agents_dir)
            return _REGISTRY_CACHE

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
        return _REGISTRY_CACHE
