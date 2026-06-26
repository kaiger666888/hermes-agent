"""Tests for plugins.platform_metrics.adapters.base (Task 3).

Phase 42 Plan 01 Task 3 — exercises the BasePlatformAdapter ABC +
AdapterNotActivatedError + get_adapter factory. These tests assert the
contract that Plan 42-02's 5 adapter stubs (douyin / kuaishou /
weixin_video / xiaohongshu / bilibili) will rely on.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, async tests run via ``asyncio.run`` (simpler than pytest_asyncio
fixtures per the v6.0 evolution queue test pattern).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest


# ──────────────────────────────────────────────────────────────────────────
# Test 1: AdapterNotActivatedError preserves env_key in message
# ──────────────────────────────────────────────────────────────────────────


def test_adapter_not_activated_error() -> None:
    """AdapterNotActivatedError inherits RuntimeError + names env_key."""
    from plugins.platform_metrics.adapters.base import AdapterNotActivatedError

    err = AdapterNotActivatedError("DOUYIN_API_KEY", platform="douyin")
    assert isinstance(err, RuntimeError)
    assert "DOUYIN_API_KEY" in str(err)
    assert "douyin" in str(err)
    # env_key attribute preserved for programmatic access.
    assert err.env_key == "DOUYIN_API_KEY"
    assert err.platform == "douyin"


# ──────────────────────────────────────────────────────────────────────────
# Test 2: BasePlatformAdapter cannot be instantiated directly (ABC)
# ──────────────────────────────────────────────────────────────────────────


def test_base_cannot_instantiate() -> None:
    """BasePlatformAdapter is abstract — direct instantiation fails."""
    from plugins.platform_metrics.adapters.base import BasePlatformAdapter

    with pytest.raises(TypeError):
        BasePlatformAdapter()  # type: ignore[abstract]


# ──────────────────────────────────────────────────────────────────────────
# Test 3: Subclass must override name + env_key + implement fetch
# ──────────────────────────────────────────────────────────────────────────


def test_subclass_must_override_name_and_env_key() -> None:
    """Subclass without name/env_key ClassVars + fetch impl fails to instantiate.

    A subclass that implements fetch() but leaves name="" / env_key=""
    should instantiate (these are ClassVar defaults), but its
    is_activated() / _require_activated() will fail to find the env var
    correctly. Pin the contract: subclasses MUST set non-empty name +
    env_key, and MUST implement async fetch.
    """
    from plugins.platform_metrics.adapters.base import BasePlatformAdapter

    # Subclass that only implements fetch() — leaves name/env_key as "".
    class HalfBakedAdapter(BasePlatformAdapter):
        async def fetch(self, variant_id: str):  # type: ignore[override]
            self._require_activated()
            return None

    # It can be instantiated (ABC only enforces abstractmethod).
    instance = HalfBakedAdapter()
    # But its is_activated() reads os.environ.get("") which is always
    # falsy → never activated. This is the contract signal: subclasses
    # that don't override env_key are permanently unactivated.
    assert instance.is_activated() is False
    assert instance.name == ""
    assert instance.env_key == ""

    # Subclass that does NOT implement fetch() cannot instantiate.
    class MissingFetchAdapter(BasePlatformAdapter):
        pass

    with pytest.raises(TypeError):
        MissingFetchAdapter()  # type: ignore[abstract]


# ──────────────────────────────────────────────────────────────────────────
# Test 4 + 5: Concrete TestAdapter activates via env var
# ──────────────────────────────────────────────────────────────────────────


# Inline fixture class for the activation tests. Module-level (not
# nested in a test function) so the registry test below can reuse it.
class _TestAdapter:
    """Placeholder — re-imported in each test to keep pytest isolation clean."""

    pass


def _make_test_adapter_class():
    """Factory: build a fresh TestAdapter subclass bound to TEST_API_KEY.

    Avoids module-level class-attr leakage between tests (env_key on a
    ClassVar is shared across instances of the same class — creating a
    fresh subclass per test sidesteps this).
    """
    from plugins.platform_metrics.adapters.base import BasePlatformAdapter
    from plugins.platform_metrics.schema import PlatformMetrics

    class TestAdapter(BasePlatformAdapter):
        name = "test"
        env_key = "TEST_API_KEY"

        async def fetch(self, variant_id: str) -> PlatformMetrics:  # type: ignore[override]
            self._require_activated()
            return PlatformMetrics(
                platform="douyin",
                variant_id=variant_id,
                completion_rate=0.5,
                hook_dropoff_rate=0.5,
                engagement_rate=0.05,
                save_rate=0.02,
                comment_rate=0.01,
                fetched_at=datetime(2026, 6, 27, tzinfo=timezone.utc),
            )

    return TestAdapter


def test_concrete_subclass_activates_with_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With env var set, is_activated() is True + fetch() returns metrics."""
    TestAdapter = _make_test_adapter_class()
    monkeypatch.setenv("TEST_API_KEY", "fake-token-abc")

    instance = TestAdapter()
    assert instance.is_activated() is True
    assert instance.name == "test"
    assert instance.env_key == "TEST_API_KEY"

    pm = asyncio.run(instance.fetch("v1"))
    assert pm.platform == "douyin"
    assert pm.variant_id == "v1"


def test_concrete_subclass_without_env_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without env var, fetch() raises AdapterNotActivatedError."""
    from plugins.platform_metrics.adapters.base import AdapterNotActivatedError

    TestAdapter = _make_test_adapter_class()
    monkeypatch.delenv("TEST_API_KEY", raising=False)

    instance = TestAdapter()
    assert instance.is_activated() is False

    with pytest.raises(AdapterNotActivatedError) as exc_info:
        asyncio.run(instance.fetch("v1"))
    # env_key preserved in exception.
    assert exc_info.value.env_key == "TEST_API_KEY"
    assert "TEST_API_KEY" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────────────
# Test 6: get_adapter factory reads from ADAPTER_REGISTRY
# ──────────────────────────────────────────────────────────────────────────


def test_get_adapter_factory() -> None:
    """get_adapter(name) returns an instance registered under that name."""
    from plugins.platform_metrics.adapters import ADAPTER_REGISTRY, register_adapter
    from plugins.platform_metrics.adapters.base import BasePlatformAdapter, get_adapter

    TestAdapter = _make_test_adapter_class()
    # Register + clean up after (avoid registry pollution across tests).
    register_adapter("test", TestAdapter)
    try:
        adapter = get_adapter("test")
        assert isinstance(adapter, BasePlatformAdapter)
        assert isinstance(adapter, TestAdapter)
        assert adapter.name == "test"
    finally:
        del ADAPTER_REGISTRY["test"]


# ──────────────────────────────────────────────────────────────────────────
# Test 7: get_adapter raises KeyError on unknown name
# ──────────────────────────────────────────────────────────────────────────


def test_get_adapter_unknown_raises() -> None:
    """get_adapter(name) raises KeyError for unregistered names.

    Message includes the registered names so the operator sees what's
    available.
    """
    from plugins.platform_metrics.adapters.base import get_adapter

    with pytest.raises(KeyError) as exc_info:
        get_adapter("nonexistent_platform")
    # Message includes context (registered adapters list).
    assert "nonexistent_platform" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────────────
# Test 8: SCOPE DISCIPLINE — base.py does not import agent.feedback_*
# ──────────────────────────────────────────────────────────────────────────


def test_base_does_not_import_feedback_core() -> None:
    """adapters/base.py MUST NOT import agent.feedback_schema or agent.feedback_store.

    The adapter contract is independent of v6.0 core. Composition with
    FeedbackRecord happens at the schema layer (FeedbackRecordExtension),
    not the adapter layer.
    """
    import subprocess
    from pathlib import Path

    base_path = (
        Path(__file__).resolve().parent.parent / "adapters" / "base.py"
    )
    for forbidden in ("agent.feedback_schema", "agent.feedback_store"):
        result = subprocess.run(
            ["grep", "-c", f"from {forbidden}", str(base_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        count = int(result.stdout.strip()) if result.stdout.strip() else 0
        assert count == 0, (
            f"Scope discipline violated: adapters/base.py imports "
            f"{forbidden} {count} time(s). Adapters must be independent "
            f"of v6.0 core."
        )
