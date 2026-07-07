"""Integration tests for Phase 59 POOL-01: auxiliary_client pool_name kwarg +
isolation from default pool exhaustion.

Validates the wire-in changes:

* ``agent/auxiliary_client._select_pool_entry(provider, pool_name="default")``
  dispatches to ``load_named_pool`` when ``pool_name != "default"``.
* ``agent/glm_throttle.acquire_slot(task, pool_name="auxiliary")`` accepts
  the metadata kwarg without breaking.
* Test 1 (isolation) is the LOAD-BEARING test from CONTEXT.md "Specific
  Ideas" #3: exhausting the default pool does NOT prevent the aux pool
  from selecting a usable key — directly verifies the v11.0 smoke-test
  §3.1 failure-mode fix.
"""
from __future__ import annotations

import json
import time

import pytest


def _write_auth_store(tmp_path, payload: dict) -> None:
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "auth.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _clear_glm_env(monkeypatch) -> None:
    for var in (
        "GLM_AUX_API_KEY_1",
        "GLM_AUX_API_KEY_2",
        "GLM_AUX_API_KEY_3",
        "GLM_AUX_API_KEY_4",
        "GLM_API_KEY",
        "ZAI_API_KEY",
        "Z_AI_API_KEY",
        "GLM_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)


# ===========================================================================
# Task 2: Integration — auxiliary_client + glm_throttle pool_name (5 tests)
# ===========================================================================


class TestAuxPoolIsolation:
    """Integration coverage for the named-pool dispatch in auxiliary_client."""

    # ---- Test 1: isolation (LOAD-BEARING) --------------------------------

    def test_aux_pool_isolation_from_default_exhaustion(self, tmp_path, monkeypatch):
        """Test 1 (CONTEXT.md "Specific Ideas" #3): seed the default pool
        for ``zai`` with 2 entries and mark BOTH exhausted via
        ``mark_exhausted_and_rotate(status_code=429)``. Seed the aux pool
        with 2 separate entries. Call:

        - ``_select_pool_entry("zai", pool_name="default")`` → ``(True, None)``
          (default pool exists but has no available entries).
        - ``_select_pool_entry("zai", pool_name="auxiliary")`` → ``(True, <entry>)``
          with the entry's ``access_token`` in the aux-key set.

        This is the v11.0 §3.1 failure-mode fix: gateway burst exhausts main
        pool keys but the round table still gets credentials from the aux pool.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _clear_glm_env(monkeypatch)

        # Default pool: 2 entries, both exhausted via 429 (cooldown 1h).
        now = time.time()
        _write_auth_store(
            tmp_path,
            {
                "version": 1,
                "credential_pool": {
                    "zai": [
                        {
                            "id": "main-1",
                            "label": "main_key_1",
                            "auth_type": "api_key",
                            "priority": 0,
                            "source": "manual",
                            "access_token": "MAIN_KEY_1",
                            "last_status": "exhausted",
                            "last_status_at": now,
                            "last_error_code": 429,
                        },
                        {
                            "id": "main-2",
                            "label": "main_key_2",
                            "auth_type": "api_key",
                            "priority": 1,
                            "source": "manual",
                            "access_token": "MAIN_KEY_2",
                            "last_status": "exhausted",
                            "last_status_at": now,
                            "last_error_code": 429,
                        },
                    ],
                    # Aux pool: 2 separate keys, both fresh.
                    "auxiliary:zai": [
                        {
                            "id": "aux-1",
                            "label": "aux_key_1",
                            "auth_type": "api_key",
                            "priority": 0,
                            "source": "env:GLM_AUX_API_KEY_1",
                            "access_token": "AUX_KEY_1",
                        },
                        {
                            "id": "aux-2",
                            "label": "aux_key_2",
                            "auth_type": "api_key",
                            "priority": 1,
                            "source": "env:GLM_AUX_API_KEY_2",
                            "access_token": "AUX_KEY_2",
                        },
                    ],
                },
            },
        )

        from agent.auxiliary_client import _select_pool_entry

        # Default pool — both entries exhausted, select() returns None.
        pool_exists, entry = _select_pool_entry("zai", pool_name="default")
        assert pool_exists is True, "Default pool must exist (2 entries seeded)"
        assert entry is None, (
            "Default pool is fully exhausted — select() must return None. "
            f"Got entry with token: {getattr(entry, 'access_token', None)!r}"
        )

        # Aux pool — must still return a usable entry.
        pool_exists_aux, entry_aux = _select_pool_entry("zai", pool_name="auxiliary")
        assert pool_exists_aux is True, "Aux pool must exist (2 entries seeded)"
        assert entry_aux is not None, (
            "Aux pool must select an entry even when the default pool is "
            "fully exhausted — this is the v11.0 §3.1 fix."
        )
        assert entry_aux.access_token in {"AUX_KEY_1", "AUX_KEY_2"}, (
            f"Selected aux entry must be one of the dedicated aux keys, "
            f"got: {entry_aux.access_token!r}"
        )

    # ---- Test 2: pool_name kwarg plumbing --------------------------------

    def test_pool_name_kwarg_routes_to_named_pool(self, tmp_path, monkeypatch):
        """Test 2: ``_select_pool_entry("zai")`` (no kwarg) uses default pool.
        ``_select_pool_entry("zai", pool_name="auxiliary")`` uses aux pool.
        Verify the selected entries differ when the pools have different keys."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _clear_glm_env(monkeypatch)

        _write_auth_store(
            tmp_path,
            {
                "version": 1,
                "credential_pool": {
                    "zai": [
                        {
                            "id": "default-1",
                            "label": "default_key",
                            "auth_type": "api_key",
                            "priority": 0,
                            "source": "manual",
                            "access_token": "DEFAULT_KEY",
                        },
                    ],
                    "auxiliary:zai": [
                        {
                            "id": "aux-1",
                            "label": "aux_key",
                            "auth_type": "api_key",
                            "priority": 0,
                            "source": "env:GLM_AUX_API_KEY_1",
                            "access_token": "AUX_KEY",
                        },
                    ],
                },
            },
        )

        from agent.auxiliary_client import _select_pool_entry

        # Default pool selection.
        _, default_entry = _select_pool_entry("zai")
        assert default_entry is not None
        assert default_entry.access_token == "DEFAULT_KEY"

        # Aux pool selection — different key.
        _, aux_entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert aux_entry is not None
        assert aux_entry.access_token == "AUX_KEY"

    # ---- Test 3: acquire_slot accepts pool_name without breaking ---------

    def test_acquire_slot_accepts_pool_name_kwarg(self, monkeypatch):
        """Test 3: ``acquire_slot(task)`` and ``acquire_slot(task,
        pool_name="auxiliary")`` must both succeed without raising. The
        ``pool_name`` arg is metadata-only — it does not change throttle
        behavior."""
        # Reset throttle state so prior tests don't bleed in.
        from agent.glm_throttle import acquire_slot, reset_for_testing

        reset_for_testing()
        try:
            # Default pool_name (= "auxiliary" per Phase 59 default).
            acquire_slot("test_round_table_opinion")
            # Explicit pool_name.
            acquire_slot("test_round_table_opinion", pool_name="auxiliary")
            # Even a custom pool_name — should not raise (metadata only).
            acquire_slot("test_round_table_opinion", pool_name="custom-foo")
        finally:
            reset_for_testing()

    # ---- Test 4: fallback path (single GLM_API_KEY, no aux vars) --------

    def test_aux_pool_fallback_single_glm_api_key(self, tmp_path, monkeypatch):
        """Test 4: ``_select_pool_entry("zai", pool_name="auxiliary")`` with
        only ``GLM_API_KEY=main`` returns ``(True, <entry>)`` with
        ``access_token == "main"``. Proves single-key operators are not
        broken when the auxiliary code path runs."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _clear_glm_env(monkeypatch)
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})

        monkeypatch.setenv("GLM_API_KEY", "main")

        from agent.auxiliary_client import _select_pool_entry

        pool_exists, entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert pool_exists is True
        assert entry is not None
        assert entry.access_token == "main"

    # ---- Test 5: no breaking change — default kwarg preserves callers ----

    def test_default_pool_name_preserves_existing_callers(
        self, tmp_path, monkeypatch
    ):
        """Test 5: existing ``_select_pool_entry(provider)`` calls without
        ``pool_name`` must still work against the default pool. Uses
        monkeypatch to swap ``load_pool`` to a stub returning a known entry,
        verifies the stub is consulted (NOT ``load_named_pool``)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _clear_glm_env(monkeypatch)
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})

        # Build a stub pool with a sentinel entry.
        class _StubEntry:
            access_token = "STUB_DEFAULT_TOKEN"
            source = "stub"

        class _StubPool:
            def has_credentials(self) -> bool:
                return True

            def select(self):
                return _StubEntry()

        # Patch load_pool at the auxiliary_client module's import reference.
        import agent.auxiliary_client as aux_mod

        original_load_pool = getattr(aux_mod, "load_pool", None)
        monkeypatch.setattr(aux_mod, "load_pool", lambda _p: _StubPool())

        try:
            from agent.auxiliary_client import _select_pool_entry

            pool_exists, entry = _select_pool_entry("zai")
            assert pool_exists is True
            assert entry is not None
            assert entry.access_token == "STUB_DEFAULT_TOKEN"
        finally:
            if original_load_pool is not None:
                aux_mod.load_pool = original_load_pool
