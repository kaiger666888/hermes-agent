"""Tests for plugin scaffold: plugin.yaml + register(ctx) + ADAPTER_REGISTRY.

Phase 42 Plan 01 Task 1 — TDD RED: these tests assert the contract that
the scaffold (plugin.yaml + __init__.py + adapters/__init__.py) must
satisfy. They fail until Task 1 GREEN lands the implementation.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml


# Resolve plugin dir relative to this test file (robust against cwd shifts).
_PLUGIN_DIR = Path(__file__).resolve().parent.parent
_PLUGIN_YAML = _PLUGIN_DIR / "plugin.yaml"


# ──────────────────────────────────────────────────────────────────────────
# Test 1: plugin.yaml validates with required fields
# ──────────────────────────────────────────────────────────────────────────


def test_plugin_yaml_loads() -> None:
    """plugin.yaml parses as YAML and has the 5 required manifest fields."""
    assert _PLUGIN_YAML.is_file(), f"plugin.yaml missing at {_PLUGIN_YAML}"
    raw = _PLUGIN_YAML.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    assert isinstance(data, dict), "plugin.yaml must parse to a dict"
    assert data["name"] == "platform_metrics"
    assert data["version"] == "0.1.0"
    assert data["kind"] == "standalone"
    assert data["provides_tools"] == [], (
        "Plan 01 ships no tools — provides_tools must be empty list "
        "(Plan 04 adds formula stats CLI hook, not a tool)"
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 2: register(ctx) callable + no-op in Plan 01
# ──────────────────────────────────────────────────────────────────────────


def test_register_callable() -> None:
    """plugins.platform_metrics.register is callable + no-op in Plan 01."""
    from plugins.platform_metrics import register

    assert callable(register), "register must be a callable entry point"
    ctx = Mock()
    # register() in Plan 01 registers nothing (provides_tools=[]). Calling
    # it must not raise; ctx.register_tool must NOT be invoked.
    register(ctx)
    ctx.register_tool.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────
# Test 3: ADAPTER_REGISTRY exists and contains the 5 v9.0 platforms
# ──────────────────────────────────────────────────────────────────────────


def test_adapter_registry_has_v9_platforms() -> None:
    """ADAPTER_REGISTRY is a dict containing the 5 v9.0 platforms.

    Plan 42-01 shipped the registry + register_adapter helper; Plan 42-02
    populated it with 5 platform adapter stubs (douyin/kuaishou/weixin_video/
    xiaohongshu/bilibili) via register_adapter at module import time.
    """
    from plugins.platform_metrics.adapters import ADAPTER_REGISTRY

    assert isinstance(ADAPTER_REGISTRY, dict), (
        "ADAPTER_REGISTRY must be a dict keyed by platform name"
    )
    expected = {"douyin", "kuaishou", "weixin_video", "xiaohongshu", "bilibili"}
    assert expected.issubset(ADAPTER_REGISTRY.keys()), (
        f"v9.0 requires adapters for {expected}; got {set(ADAPTER_REGISTRY.keys())}. "
        "Plan 42-02 populates these via register_adapter."
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 4: register_adapter rejects non-BasePlatformAdapter subclasses
# ──────────────────────────────────────────────────────────────────────────


def test_register_adapter_rejects_non_subclass() -> None:
    """register_adapter raises TypeError when given a non-subclass.

    Contract: only ``BasePlatformAdapter`` subclasses may register. This
    catches typos like registering a schema class instead of an adapter.
    """
    from plugins.platform_metrics.adapters import register_adapter

    class DummyClass:
        """NOT a BasePlatformAdapter subclass — must be rejected."""

    with pytest.raises(TypeError):
        register_adapter("foo", DummyClass)
