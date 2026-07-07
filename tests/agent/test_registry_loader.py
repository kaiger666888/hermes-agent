"""Agent registry YAML loader unit tests (INFRA-01 SC#1).

Covers the four acceptance behaviors of the registry loader:

1. **Valid YAML loads + validates** — a minimal fixture placed at
   ``~/.hermes/agents/test-coordinator.agent.yaml`` is discovered and
   returned by ``load_agent_registry()`` with the expected name.
2. **Malformed YAML is rejected with a specific JSON path** — schema
   violations surface as ``RegistryValidationError`` whose ``str()``
   contains a ``$.`` JSON-path marker (e.g. ``$.persona``) rather than a
   generic "schema validation failed" message.
3. **Filename stem == ``name`` field invariant** — schema-valid YAML
   whose ``name`` disagrees with the filename stem is rejected with a
   message that literally cites ``does not match filename stem``.
4. **Caching + flat discovery** — repeated calls return the SAME list
   object; ``force_reload=True`` returns a NEW list object; subdirectories
   of ``~/.hermes/agents/`` are NOT walked (flat glob only).

The ``_hermetic_environment`` autouse fixture from ``tests/conftest.py``
redirects ``HERMES_HOME`` to ``tmp_path / "hermes_test"`` per-test, so we
copy the fixture YAMLs into ``(redirected hermes_home) / "agents"`` and
let ``get_hermes_home()`` find them — no manual env-var manipulation.

TDD note: this file is RED until ``agent/registry_loader.py`` lands in
Task 2. The import is deferred into the ``registry`` fixture so
``pytest --collect-only`` succeeds without the module present; the first
test that runs raises a clear ``ModuleNotFoundError`` until Task 2 ships
the implementation.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from hermes_constants import get_hermes_home

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"
VALID_FIXTURE = FIXTURES_DIR / "test-coordinator.agent.yaml"
MALFORMED_FIXTURE = FIXTURES_DIR / "malformed.agent.yaml"
NAME_MISMATCH_FIXTURE = FIXTURES_DIR / "name-mismatch.agent.yaml"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


class _Registry:
    """Thin holder for the three public exports of agent.registry_loader.

    Importing agent.registry_loader is deferred to ``_Registry._load`` so
    the test file collects cleanly under TDD RED (module not yet shipped).
    Task 2 ships the module and the import succeeds.
    """

    @staticmethod
    def _load() -> tuple[Any, Any, Any]:
        from agent.registry_loader import (  # type: ignore[import-not-found]
            RegistryValidationError,
            load_agent_registry,
            load_one_agent_yaml,
        )

        return RegistryValidationError, load_agent_registry, load_one_agent_yaml

    @property
    def error_cls(self) -> Any:
        return self._load()[0]

    @property
    def load_registry(self) -> Any:
        return self._load()[1]

    @property
    def load_one(self) -> Any:
        return self._load()[2]


@pytest.fixture
def registry() -> _Registry:
    """Lazy accessor for agent.registry_loader public exports.

    Tests reference ``registry.load_registry`` / ``registry.error_cls`` /
    ``registry.load_one`` so the module is imported only when a test runs,
    not at collection time. This keeps ``pytest --collect-only`` clean
    under TDD RED while still failing each test with ModuleNotFoundError
    until Task 2 lands.
    """
    return _Registry()


# --------------------------------------------------------------------------- #
# Test helpers (module-level; do NOT import agent.registry_loader)
# --------------------------------------------------------------------------- #


def _agents_dir() -> Path:
    """Return the redirected ``~/.hermes/agents/`` directory.

    Relies on the ``_hermetic_environment`` autouse fixture from
    ``tests/conftest.py`` having set ``HERMES_HOME=tmp_path/"hermes_test"``.
    Creates the ``agents/`` subdir on demand so each test can drop fixture
    YAMLs into it.
    """
    agents_dir = get_hermes_home() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir


def _copy_fixture(fixture: Path, target_name: str | None = None) -> Path:
    """Copy a fixture YAML into the redirected ``~/.hermes/agents/`` dir.

    Args:
        fixture: source path under ``tests/agent/fixtures/agents/``.
        target_name: filename to write; defaults to the fixture's basename.
    """
    target_name = target_name or fixture.name
    dst = _agents_dir() / target_name
    shutil.copyfile(fixture, dst)
    return dst


def _reset_registry_cache() -> None:
    """Clear the module-level cache between tests.

    ``load_agent_registry`` caches its result; in tests we mutate the
    redirected HERMES_HOME between calls, so we must reset the cache to
    observe the mutation. Mirrors the ``force_reload=True`` code path
    but more explicit for unit tests.
    """
    import agent.registry_loader as mod  # type: ignore[import-not-found]

    mod._REGISTRY_CACHE = None  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# 1. Valid YAML loading + schema validation
# --------------------------------------------------------------------------- #


class TestValidYamlLoading:
    """A schema-valid YAML is discoverable and returned by the registry."""

    def test_valid_yaml_loads_and_validates(self, registry: _Registry):
        _reset_registry_cache()
        _copy_fixture(VALID_FIXTURE)

        entries = registry.load_registry()

        assert len(entries) == 1, f"expected 1 entry, got {len(entries)}"
        assert entries[0]["name"] == "test-coordinator"
        required_fields = (
            "name",
            "description",
            "version",
            "persona",
            "tools",
            "memory_scope",
            "lineage",
        )
        for required in required_fields:
            assert required in entries[0], f"missing required field {required!r}"

    def test_load_one_agent_yaml_returns_parsed_dict(self, registry: _Registry):
        data = registry.load_one(VALID_FIXTURE)
        assert isinstance(data, dict)
        assert data["name"] == "test-coordinator"
        assert isinstance(data["persona"], str)
        assert "test coordinator" in data["persona"].lower()


# --------------------------------------------------------------------------- #
# 2. Malformed YAML rejection with specific JSON path
# --------------------------------------------------------------------------- #


class TestMalformedYamlRejection:
    """Schema-violating YAML surfaces a specific JSON path, not a generic error."""

    def test_malformed_yaml_rejected_with_field_path(self, registry: _Registry):
        _reset_registry_cache()
        _copy_fixture(MALFORMED_FIXTURE)

        with pytest.raises(registry.error_cls) as exc_info:
            registry.load_registry()

        message = str(exc_info.value)
        # Plan SC#1 acceptance: the error message MUST cite a specific JSON
        # path ($ followed by . or [), not just "schema validation failed".
        assert "$." in message, (
            f"expected JSON path marker '$.' in error message, got: {message!r}"
        )
        # Per fixture design, the omitted required field `persona` is the
        # first sorted violation (root-level path sorts before nested paths).
        assert "$.persona" in message or "persona" in message.lower(), (
            f"expected persona in error (first sorted violation), got: {message!r}"
        )

    def test_load_one_agent_yaml_surfaces_path_on_malformed(self, registry: _Registry):
        with pytest.raises(registry.error_cls) as exc_info:
            registry.load_one(MALFORMED_FIXTURE)
        assert "$." in str(exc_info.value)


# --------------------------------------------------------------------------- #
# 3. name == filename-stem invariant
# --------------------------------------------------------------------------- #


class TestNameFilenameMismatch:
    """Schema-valid YAML with a mismatching ``name`` field is rejected."""

    def test_name_filename_mismatch_rejected(self, registry: _Registry):
        _reset_registry_cache()
        _copy_fixture(NAME_MISMATCH_FIXTURE)

        with pytest.raises(registry.error_cls) as exc_info:
            registry.load_registry()

        message = str(exc_info.value)
        # The error message MUST cite the filename-stem invariant verbatim.
        assert "does not match filename stem" in message, (
            f"expected 'does not match filename stem' substring, got: {message!r}"
        )
        # The fixture's name field is "wrong-name" and the stem is "name-mismatch".
        assert "wrong-name" in message
        assert "name-mismatch" in message

    def test_load_one_agent_yaml_rejects_name_mismatch(self, registry: _Registry):
        with pytest.raises(registry.error_cls) as exc_info:
            registry.load_one(NAME_MISMATCH_FIXTURE)
        assert "does not match filename stem" in str(exc_info.value)


# --------------------------------------------------------------------------- #
# 4. Caching + flat discovery
# --------------------------------------------------------------------------- #


class TestRegistryCaching:
    """Lazy cache: repeat calls return the same list; force_reload refreshes."""

    def test_force_reload_bypasses_cache(self, registry: _Registry):
        _reset_registry_cache()
        _copy_fixture(VALID_FIXTURE)

        first = registry.load_registry()
        second = registry.load_registry()
        assert first is second, "second call should return the cached list object"

        third = registry.load_registry(force_reload=True)
        assert third is not first, (
            "force_reload=True should return a NEW list object, not the cache"
        )
        assert [e["name"] for e in third] == [e["name"] for e in first]

    def test_empty_agents_dir_returns_empty_list(self, registry: _Registry):
        _reset_registry_cache()
        _agents_dir()  # ensure the dir exists but is empty
        entries = registry.load_registry()
        assert entries == []
        assert isinstance(entries, list)

    def test_missing_agents_dir_returns_empty_list(self, registry: _Registry):
        _reset_registry_cache()
        agents_dir = get_hermes_home() / "agents"
        if agents_dir.exists():
            shutil.rmtree(agents_dir)
        entries = registry.load_registry()
        assert entries == []
        assert isinstance(entries, list)

    def test_flat_glob_not_nested(self, registry: _Registry):
        _reset_registry_cache()
        # Drop a valid fixture at the top level — discovered.
        _copy_fixture(VALID_FIXTURE)
        # Drop ANOTHER copy inside a subdirectory — NOT discovered
        # (Pitfall #8 in 52-RESEARCH.md: flat *.agent.yaml glob, not rglob).
        nested_dir = _agents_dir() / "subdir"
        nested_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VALID_FIXTURE, nested_dir / "nested.agent.yaml")

        entries = registry.load_registry()
        names = [e["name"] for e in entries]
        assert names == ["test-coordinator"], (
            f"nested YAML leaked into registry; got names={names!r}"
        )


# --------------------------------------------------------------------------- #
# WR-04 fix: _load_schema validates its return value
# --------------------------------------------------------------------------- #


class TestSchemaLoadValidation:
    """WR-04: ``_load_schema`` MUST validate its return value before caching.

    Without this guard, an empty / YAML-null schema file caches as ``None``
    and silently poisons every subsequent load — ``Draft202012Validator(None)``
    raises a confusing SchemaError that doesn't mention the root cause
    (empty schema file). The fix raises a specific RegistryValidationError
    with the path + type info so the operator can triage immediately.
    """

    def test_empty_schema_file_raises_registry_validation_error(self, monkeypatch, tmp_path):
        """Empty file → yaml.safe_load returns None → loader rejects."""
        from agent import registry_loader as rl

        empty_schema = tmp_path / "empty.yaml"
        empty_schema.write_text("", encoding="utf-8")
        monkeypatch.setattr(rl, "_SCHEMA_PATH", empty_schema)
        # Reset cache so the next _get_schema() triggers _load_schema()
        monkeypatch.setattr(rl, "_SCHEMA_CACHE", None)

        with pytest.raises(rl.RegistryValidationError) as exc_info:
            rl._load_schema()
        assert "not a valid object" in str(exc_info.value)
        assert "NoneType" in str(exc_info.value)

    def test_non_dict_schema_raises_registry_validation_error(self, monkeypatch, tmp_path):
        """List-of-strings YAML → loader rejects with type info."""
        from agent import registry_loader as rl

        list_schema = tmp_path / "list.yaml"
        list_schema.write_text("- foo\n- bar\n", encoding="utf-8")
        monkeypatch.setattr(rl, "_SCHEMA_PATH", list_schema)
        monkeypatch.setattr(rl, "_SCHEMA_CACHE", None)

        with pytest.raises(rl.RegistryValidationError) as exc_info:
            rl._load_schema()
        assert "not a valid object" in str(exc_info.value)
        assert "list" in str(exc_info.value).lower()

    def test_schema_missing_type_and_dollar_schema_keys_raises(self, monkeypatch, tmp_path):
        """Dict YAML without type/$schema keys → loader rejects."""
        from agent import registry_loader as rl

        bad_schema = tmp_path / "bad.yaml"
        # Valid YAML object but missing both type and $schema — not a JSON Schema doc
        bad_schema.write_text("foo: bar\nbaz: qux\n", encoding="utf-8")
        monkeypatch.setattr(rl, "_SCHEMA_PATH", bad_schema)
        monkeypatch.setattr(rl, "_SCHEMA_CACHE", None)

        with pytest.raises(rl.RegistryValidationError) as exc_info:
            rl._load_schema()
        assert "missing both 'type' and '$schema'" in str(exc_info.value)
