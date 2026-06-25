"""Integration tests: hermes-agent PluginManager discovers + loads ``kais_aigc``.

These tests exercise the *real* loader code path
(``hermes_cli.plugins.PluginManager.discover_and_load``) against the
bundled-plugins directory. They are deliberately NOT unit tests of
``register(ctx)`` in isolation (Plan 31-01 already proved that); they prove
the end-to-end discovery manifest-parse → enabled-gate → module-import →
register() → tool-count pipeline works for this plugin.

Three orthogonal states are asserted:

1. **Default (opt-in) state** — plugin is discovered, manifest parses, but
   ``enabled == False`` and ``error`` mentions "not enabled" because
   ``kind: standalone`` plugins require explicit ``plugins.enabled`` opt-in.
2. **Enabled + loaded** — when ``plugins.enabled`` includes the plugin name,
   the loader imports ``__init__.py`` and calls ``register(ctx)``; the plugin
   reports ``enabled == True`` and ``tools == 5`` (the five tools declared
   in ``tools.py`` — Phase 37-03 added ``kais_canvas_sync_register``).
3. **Disabled-list wins** — when the plugin appears in BOTH
   ``plugins.enabled`` AND ``plugins.disabled``, the deny-list takes
   precedence; ``enabled == False`` and ``error`` mentions "disabled".
"""

from __future__ import annotations

import pytest

from hermes_cli import plugins as plugin_module
from hermes_cli.plugins import get_plugin_manager


PLUGIN_NAME = "kais_aigc"


def _find_entry(listing: list[dict]) -> dict:
    """Return the ``list_plugins()`` entry whose ``name`` matches our plugin."""
    for entry in listing:
        if entry["name"] == PLUGIN_NAME:
            return entry
    pytest.fail(f"{PLUGIN_NAME!r} not present in list_plugins() output")


def test_discovery_default_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default state: discovered + manifest parsed, but not enabled.

    Proves the manifest was found in the bundled-plugins scan and parsed
    successfully. A standalone plugin without an ``plugins.enabled`` entry
    shows up as ``enabled=False`` with an error mentioning "not enabled".
    """
    # Ensure neither allow-list nor deny-list mentions our plugin.
    monkeypatch.setattr(plugin_module, "_get_enabled_plugins", lambda: set())
    monkeypatch.setattr(plugin_module, "_get_disabled_plugins", lambda: set())

    manager = get_plugin_manager()
    manager.discover_and_load(force=True)

    entry = _find_entry(manager.list_plugins())
    assert entry["source"] == "bundled", (
        f"{PLUGIN_NAME} should be discovered as a bundled plugin, "
        f"got source={entry['source']!r}"
    )
    assert entry["enabled"] is False, (
        f"{PLUGIN_NAME} should default to enabled=False (standalone opt-in), "
        f"got enabled={entry['enabled']!r}"
    )
    assert entry["error"] is not None and "not enabled" in entry["error"], (
        f"{PLUGIN_NAME} default-state error should mention 'not enabled', "
        f"got error={entry['error']!r}"
    )
    # tools=0 because register() was never called (plugin not loaded).
    assert entry["tools"] == 0


def test_enable_and_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enabled state: plugin is loaded and ``register(ctx)`` runs.

    With ``plugins.enabled`` containing our plugin name (and no deny-list
    entry), the loader imports ``__init__.py``, calls ``register(ctx)``,
    and the plugin reports ``enabled=True``, ``error=None``, and
    ``tools == 5`` (one per ``ctx.register_tool`` call — Phase 37-03 added
    ``kais_canvas_sync_register`` as the 5th tool).
    """
    monkeypatch.setattr(
        plugin_module, "_get_enabled_plugins", lambda: {PLUGIN_NAME}
    )
    monkeypatch.setattr(plugin_module, "_get_disabled_plugins", lambda: set())

    manager = get_plugin_manager()
    manager.discover_and_load(force=True)

    entry = _find_entry(manager.list_plugins())
    assert entry["enabled"] is True, (
        f"{PLUGIN_NAME} should be enabled when listed in plugins.enabled, "
        f"got enabled={entry['enabled']!r} error={entry['error']!r}"
    )
    assert entry["error"] is None, (
        f"{PLUGIN_NAME} loaded successfully should have error=None, "
        f"got error={entry['error']!r}"
    )
    assert entry["tools"] == 5, (
        f"{PLUGIN_NAME} register(ctx) should register exactly 5 tools "
        f"(kais_gold_team_submit / kais_review_submit / kais_canvas_sync / "
        f"kais_canvas_sync_register / kais_jimeng_call), "
        f"got tools={entry['tools']!r}"
    )


def test_disabled_wins_over_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deny-list precedence: disabled always wins over enabled.

    When a plugin appears in BOTH ``plugins.enabled`` and
    ``plugins.disabled``, the loader must skip it (deny-list wins). The
    plugin shows up as ``enabled=False`` with an error mentioning
    "disabled".
    """
    monkeypatch.setattr(
        plugin_module, "_get_enabled_plugins", lambda: {PLUGIN_NAME}
    )
    monkeypatch.setattr(
        plugin_module, "_get_disabled_plugins", lambda: {PLUGIN_NAME}
    )

    manager = get_plugin_manager()
    manager.discover_and_load(force=True)

    entry = _find_entry(manager.list_plugins())
    assert entry["enabled"] is False, (
        f"{PLUGIN_NAME} in deny-list must be enabled=False even if also "
        f"in allow-list, got enabled={entry['enabled']!r}"
    )
    assert entry["error"] is not None and "disabled" in entry["error"], (
        f"{PLUGIN_NAME} deny-listed error should mention 'disabled', "
        f"got error={entry['error']!r}"
    )
    # tools=0 because the loader short-circuited before calling register().
    assert entry["tools"] == 0
