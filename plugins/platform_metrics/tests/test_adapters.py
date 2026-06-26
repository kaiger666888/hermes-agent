"""test_adapters.py — tests for the 5 platform adapter stubs (Plan 42-02).

Per-adapter tests (Tasks 1+2):
  - Class attrs (name + env_key) set correctly.
  - is_activated() False without env var; True with it.
  - fetch(variant_id) raises AdapterNotActivatedError without env var.
  - fetch(variant_id) raises NotImplementedError mentioning "V9-FUTURE-01"
    when env var is set (live path deferred).
  - Adapter self-registers in ADAPTER_REGISTRY at module import.

Integration tests (Task 3):
  - All 5 adapters populate ADAPTER_REGISTRY.
  - get_adapter(name) returns the right class for each of the 5.
  - get_adapter("unknown") raises KeyError.
  - ADAPTER_REGISTRY keys exactly match SUPPORTED_PLATFORMS_WITH_ADAPTERS.

Cookie-based auth model documented in weixin_video + xiaohongshu module
docstrings (T-2 auth-documentation contract).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` at top.
  - ``asyncio.run(coro)`` inside sync test wrappers (project pattern —
    mirror v6.0 evolution queue tests; simpler than pytest_asyncio fixtures).
  - ``monkeypatch.delenv(..., raising=False)`` + ``monkeypatch.setenv(...)``
    for env-key activation; tests are order-independent.
"""

from __future__ import annotations

import asyncio
import re

import pytest

# Import all 5 adapter modules to trigger their self-registration.
# (Each ``register_adapter(name, cls)`` call at module bottom mutates
# ADAPTER_REGISTRY at import time — mirror tools/registry.py pattern.)
import plugins.platform_metrics.adapters.bilibili  # noqa: F401
import plugins.platform_metrics.adapters.douyin  # noqa: F401
import plugins.platform_metrics.adapters.kuaishou  # noqa: F401
import plugins.platform_metrics.adapters.weixin_video  # noqa: F401
import plugins.platform_metrics.adapters.xiaohongshu  # noqa: F401
from plugins.platform_metrics.adapters import ADAPTER_REGISTRY
from plugins.platform_metrics.adapters.base import (
    AdapterNotActivatedError,
    get_adapter,
)
from plugins.platform_metrics.adapters.bilibili import BilibiliCreatorAdapter
from plugins.platform_metrics.adapters.douyin import DouyinOpenAdapter
from plugins.platform_metrics.adapters.kuaishou import KuaishouOpenAdapter
from plugins.platform_metrics.adapters.weixin_video import WeixinVideoAdapter
from plugins.platform_metrics.adapters.xiaohongshu import (
    XiaohongshuShutiaoAdapter,
)
from plugins.platform_metrics.schema import SUPPORTED_PLATFORMS_WITH_ADAPTERS


# ──────────────────────────────────────────────────────────────────────────
# DouyinOpenAdapter (Task 1)
# ──────────────────────────────────────────────────────────────────────────


class TestDouyinOpenAdapter:
    """5 tests for DouyinOpenAdapter (OAuth2 platform)."""

    def test_class_attrs(self) -> None:
        assert DouyinOpenAdapter.name == "douyin"
        assert DouyinOpenAdapter.env_key == "DOUYIN_API_KEY"

    def test_not_activated_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DOUYIN_API_KEY", raising=False)
        adapter = DouyinOpenAdapter()
        assert adapter.is_activated() is False
        with pytest.raises(AdapterNotActivatedError) as exc_info:
            asyncio.run(adapter.fetch("v1"))
        assert "DOUYIN_API_KEY" in str(exc_info.value)

    def test_activated_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DOUYIN_API_KEY", "fake-token-abc")
        adapter = DouyinOpenAdapter()
        assert adapter.is_activated() is True

    def test_live_path_not_implemented(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DOUYIN_API_KEY", "fake-token-abc")
        adapter = DouyinOpenAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(adapter.fetch("variant-001"))
        assert "V9-FUTURE-01" in str(exc_info.value)

    def test_registered(self) -> None:
        assert "douyin" in ADAPTER_REGISTRY
        assert ADAPTER_REGISTRY["douyin"] is DouyinOpenAdapter


# ──────────────────────────────────────────────────────────────────────────
# KuaishouOpenAdapter (Task 1)
# ──────────────────────────────────────────────────────────────────────────


class TestKuaishouOpenAdapter:
    """5 tests for KuaishouOpenAdapter (OAuth2 platform)."""

    def test_class_attrs(self) -> None:
        assert KuaishouOpenAdapter.name == "kuaishou"
        assert KuaishouOpenAdapter.env_key == "KUAISHOU_API_KEY"

    def test_not_activated_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KUAISHOU_API_KEY", raising=False)
        adapter = KuaishouOpenAdapter()
        assert adapter.is_activated() is False
        with pytest.raises(AdapterNotActivatedError) as exc_info:
            asyncio.run(adapter.fetch("v1"))
        assert "KUAISHOU_API_KEY" in str(exc_info.value)

    def test_activated_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KUAISHOU_API_KEY", "fake-token-xyz")
        adapter = KuaishouOpenAdapter()
        assert adapter.is_activated() is True

    def test_live_path_not_implemented(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KUAISHOU_API_KEY", "fake-token-xyz")
        adapter = KuaishouOpenAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(adapter.fetch("variant-002"))
        assert "V9-FUTURE-01" in str(exc_info.value)

    def test_registered(self) -> None:
        assert "kuaishou" in ADAPTER_REGISTRY
        assert ADAPTER_REGISTRY["kuaishou"] is KuaishouOpenAdapter


# ──────────────────────────────────────────────────────────────────────────
# WeixinVideoAdapter (Task 2)
# ──────────────────────────────────────────────────────────────────────────


class TestWeixinVideoAdapter:
    """5 tests for WeixinVideoAdapter (cookie-based platform)."""

    def test_class_attrs(self) -> None:
        assert WeixinVideoAdapter.name == "weixin_video"
        assert WeixinVideoAdapter.env_key == "WEIXIN_VIDEO_API_KEY"

    def test_not_activated_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WEIXIN_VIDEO_API_KEY", raising=False)
        adapter = WeixinVideoAdapter()
        assert adapter.is_activated() is False
        with pytest.raises(AdapterNotActivatedError) as exc_info:
            asyncio.run(adapter.fetch("v1"))
        assert "WEIXIN_VIDEO_API_KEY" in str(exc_info.value)

    def test_activated_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEIXIN_VIDEO_API_KEY", "fake-cookie-string")
        adapter = WeixinVideoAdapter()
        assert adapter.is_activated() is True

    def test_live_path_not_implemented(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("WEIXIN_VIDEO_API_KEY", "fake-cookie-string")
        adapter = WeixinVideoAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(adapter.fetch("variant-003"))
        assert "V9-FUTURE-01" in str(exc_info.value)

    def test_registered(self) -> None:
        assert "weixin_video" in ADAPTER_REGISTRY
        assert ADAPTER_REGISTRY["weixin_video"] is WeixinVideoAdapter


# ──────────────────────────────────────────────────────────────────────────
# XiaohongshuShutiaoAdapter (Task 2)
# ──────────────────────────────────────────────────────────────────────────


class TestXiaohongshuShutiaoAdapter:
    """5 tests for XiaohongshuShutiaoAdapter (cookie-based platform)."""

    def test_class_attrs(self) -> None:
        assert XiaohongshuShutiaoAdapter.name == "xiaohongshu"
        assert XiaohongshuShutiaoAdapter.env_key == "XIAOHONGSHU_API_KEY"

    def test_not_activated_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XIAOHONGSHU_API_KEY", raising=False)
        adapter = XiaohongshuShutiaoAdapter()
        assert adapter.is_activated() is False
        with pytest.raises(AdapterNotActivatedError) as exc_info:
            asyncio.run(adapter.fetch("v1"))
        assert "XIAOHONGSHU_API_KEY" in str(exc_info.value)

    def test_activated_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XIAOHONGSHU_API_KEY", "fake-cookie-string")
        adapter = XiaohongshuShutiaoAdapter()
        assert adapter.is_activated() is True

    def test_live_path_not_implemented(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XIAOHONGSHU_API_KEY", "fake-cookie-string")
        adapter = XiaohongshuShutiaoAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(adapter.fetch("variant-004"))
        assert "V9-FUTURE-01" in str(exc_info.value)

    def test_registered(self) -> None:
        assert "xiaohongshu" in ADAPTER_REGISTRY
        assert ADAPTER_REGISTRY["xiaohongshu"] is XiaohongshuShutiaoAdapter


# ──────────────────────────────────────────────────────────────────────────
# BilibiliCreatorAdapter (Task 3)
# ──────────────────────────────────────────────────────────────────────────


class TestBilibiliCreatorAdapter:
    """5 tests for BilibiliCreatorAdapter (OAuth2 platform)."""

    def test_class_attrs(self) -> None:
        assert BilibiliCreatorAdapter.name == "bilibili"
        assert BilibiliCreatorAdapter.env_key == "BILIBILI_API_KEY"

    def test_not_activated_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BILIBILI_API_KEY", raising=False)
        adapter = BilibiliCreatorAdapter()
        assert adapter.is_activated() is False
        with pytest.raises(AdapterNotActivatedError) as exc_info:
            asyncio.run(adapter.fetch("v1"))
        assert "BILIBILI_API_KEY" in str(exc_info.value)

    def test_activated_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BILIBILI_API_KEY", "fake-token-bili")
        adapter = BilibiliCreatorAdapter()
        assert adapter.is_activated() is True

    def test_live_path_not_implemented(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BILIBILI_API_KEY", "fake-token-bili")
        adapter = BilibiliCreatorAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(adapter.fetch("variant-005"))
        assert "V9-FUTURE-01" in str(exc_info.value)

    def test_registered(self) -> None:
        assert "bilibili" in ADAPTER_REGISTRY
        assert ADAPTER_REGISTRY["bilibili"] is BilibiliCreatorAdapter


# ──────────────────────────────────────────────────────────────────────────
# Integration tests (Task 3)
# ──────────────────────────────────────────────────────────────────────────


class TestAdapterRegistryIntegration:
    """Plan 42-02 contract: 5 platforms registered."""

    def test_all_5_adapters_registered(self) -> None:
        assert set(ADAPTER_REGISTRY.keys()) >= {
            "douyin",
            "kuaishou",
            "weixin_video",
            "xiaohongshu",
            "bilibili",
        }

    def test_get_adapter_returns_correct_class(self) -> None:
        expected_env_keys = {
            "douyin": "DOUYIN_API_KEY",
            "kuaishou": "KUAISHOU_API_KEY",
            "weixin_video": "WEIXIN_VIDEO_API_KEY",
            "xiaohongshu": "XIAOHONGSHU_API_KEY",
            "bilibili": "BILIBILI_API_KEY",
        }
        for name, env_key in expected_env_keys.items():
            adapter = get_adapter(name)
            assert adapter.name == name
            assert adapter.env_key == env_key

    def test_get_adapter_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            get_adapter("twitter")  # type: ignore[arg-type]

    def test_registry_matches_supported_platforms(self) -> None:
        assert tuple(sorted(ADAPTER_REGISTRY.keys())) == tuple(
            sorted(SUPPORTED_PLATFORMS_WITH_ADAPTERS)
        )


# ──────────────────────────────────────────────────────────────────────────
# Cookie-based auth documentation (Task 2 contract)
# ──────────────────────────────────────────────────────────────────────────


class TestCookieBasedAuthDocumented:
    """T-2 contract: cookie-based platforms document the auth model.

    Asserts the literal string "cookie-based" appears in the module
    docstring of weixin_video + xiaohongshu (auth-model documentation).
    """

    def test_weixin_video_docstring_mentions_cookie(self) -> None:
        doc = WeixinVideoAdapter.__module__
        # __module__ is the module name; check the actual module docstring
        # via the imported module object.
        import plugins.platform_metrics.adapters.weixin_video as mod

        assert mod.__doc__ is not None
        assert "cookie-based" in mod.__doc__.lower(), (
            "weixin_video module docstring must document cookie-based auth"
        )

    def test_xiaohongshu_docstring_mentions_cookie(self) -> None:
        import plugins.platform_metrics.adapters.xiaohongshu as mod

        assert mod.__doc__ is not None
        assert "cookie-based" in mod.__doc__.lower(), (
            "xiaohongshu module docstring must document cookie-based auth"
        )

    def test_no_adapter_logs_env_value(self) -> None:
        """T-42-05 (Information Disclosure): no logging call includes the
        env var value. Grep-assert each adapter source for forbidden patterns.
        """
        import pathlib

        adapters_dir = pathlib.Path(
            __import__("plugins.platform_metrics.adapters", fromlist=["x"]).__file__
        ).parent
        forbidden_patterns = [
            # These patterns would leak the env var value into logs.
            re.compile(r"logger\.\w+\(.*os\.environ\.get\("),
            re.compile(r"logger\.\w+\(.*self\._?key"),
            re.compile(r"logger\.\w+\(f\".*\{.*env_key.*value"),
        ]
        for adapter_file in adapters_dir.glob("*.py"):
            if adapter_file.name in ("__init__.py", "base.py"):
                continue
            source = adapter_file.read_text(encoding="utf-8")
            for pat in forbidden_patterns:
                assert not pat.search(source), (
                    f"{adapter_file.name}: forbidden logging pattern {pat.pattern!r} "
                    f"found (T-42-05 Information Disclosure)"
                )
