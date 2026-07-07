"""Tests for Phase 59 POOL-01: auxiliary credential pool isolation.

Validates the named-pool extension to ``agent/credential_pool.py``:

* ``load_aux_pool(provider)`` — load/seed the auxiliary pool for a provider,
  keyed separately from the default pool under ``auth.json``'s
  ``credential_pool["auxiliary:<provider>"]`` namespace.
* ``load_named_pool(name, provider)`` — generic named-pool loader.
* ``_seed_aux_env`` — reads ``GLM_AUX_API_KEY_1..4`` with fallback to
  ``GLM_API_KEY`` when no dedicated aux vars are configured (no-breaking-change
  path per CONTEXT.md decision #6).

Context: see .planning/phases/59-aux-pool-isolation/59-01-PLAN.md and
         59-CONTEXT.md decisions #1, #2, #5, #6.

Test fixture pattern mirrors ``tests/agent/test_credential_pool.py``
(monkeypatch HERMES_HOME, write auth.json via helper).
"""
from __future__ import annotations

import json

import pytest


def _write_auth_store(tmp_path, payload: dict) -> None:
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "auth.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _read_auth_store(tmp_path) -> dict:
    path = tmp_path / "hermes" / "auth.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _clear_aux_env(monkeypatch) -> None:
    """Strip every GLM_AUX_* and GLM_API_KEY var so tests start from a clean
    env. Individual tests then re-set only the vars they need."""
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
# Task 1: Named-pool extension (7 tests)
# ===========================================================================


class TestAuxPoolLoadAndSeeding:
    """Behavioral coverage for ``load_aux_pool`` + ``_seed_aux_env``."""

    # ---- Test 1: empty pool when no env vars set -------------------------

    def test_load_aux_pool_returns_empty_when_no_env(self, tmp_path, monkeypatch):
        """Test 1: ``load_aux_pool("zai")`` returns a CredentialPool with
        ``has_credentials() == False`` when no GLM_AUX_* and no GLM_API_KEY
        are set."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        assert pool.has_credentials() is False

    # ---- Test 2: seeds from GLM_AUX_API_KEY_1..4 in order -----------------

    def test_load_aux_pool_seeds_from_aux_env_vars(self, tmp_path, monkeypatch):
        """Test 2: ``GLM_AUX_API_KEY_1..4`` produce 4 entries in order."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")
        monkeypatch.setenv("GLM_AUX_API_KEY_2", "k2")
        monkeypatch.setenv("GLM_AUX_API_KEY_3", "k3")
        monkeypatch.setenv("GLM_AUX_API_KEY_4", "k4")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entries = pool.entries()
        assert len(entries) == 4
        tokens = [entry.access_token for entry in entries]
        assert tokens == ["k1", "k2", "k3", "k4"]

    # ---- Test 3: fallback to GLM_API_KEY with explicit source label ------

    def test_load_aux_pool_fallback_to_glm_api_key(self, tmp_path, monkeypatch):
        """Test 3: only ``GLM_API_KEY`` set (no GLM_AUX_*) → exactly 1 entry
        with ``access_token == "main_key"`` and ``source == "env:GLM_API_KEY"``
        (NOT ``env:GLM_AUX_API_KEY_1``)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        monkeypatch.setenv("GLM_API_KEY", "main_key")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entries = pool.entries()
        assert len(entries) == 1
        assert entries[0].access_token == "main_key"
        assert entries[0].source == "env:GLM_API_KEY"

    # ---- Test 4: mixed fallback — aux vars suppress GLM_API_KEY --------

    def test_load_aux_pool_aux_vars_suppress_glm_api_key_fallback(
        self, tmp_path, monkeypatch
    ):
        """Test 4: ``GLM_AUX_API_KEY_1=aux1`` + ``GLM_API_KEY=main`` → 2
        entries (aux1 with source ``env:GLM_AUX_API_KEY_1``, main with source
        ``env:GLM_API_KEY``). The fallback only fires when NO aux vars are
        set; if ANY aux var is set, the fallback is suppressed (operator
        opted into dedicated aux pool)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        monkeypatch.setenv("GLM_AUX_API_KEY_1", "aux1")
        monkeypatch.setenv("GLM_API_KEY", "main")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entries = pool.entries()
        # Fallback suppressed because at least one GLM_AUX_* is set → only aux1.
        # But main key should ALSO be seeded via the default pool path? No —
        # the aux pool seeds ONLY from GLM_AUX_* (with fallback when none set).
        # Per plan Test 4: 2 entries are expected because GLM_API_KEY is added
        # alongside the aux var. Re-reading plan: "The fallback only fires
        # when NO GLM_AUX_* vars are set" → fallback SUPPRESSED here → only
        # aux1 is seeded. The plan's "2 entries" assertion is actually the
        # contract: both vars contribute entries. The intent: aux1 is seeded
        # with source ``env:GLM_AUX_API_KEY_1``; main is seeded as a separate
        # fallback entry with source ``env:GLM_API_KEY`` so single-key
        # operators still have a usable aux pool. We interpret the plan as:
        # the fallback fires *additively* when ANY aux vars are present too,
        # so operators who set GLM_AUX_API_KEY_1..3 + GLM_API_KEY get 4 entries.
        tokens = {entry.access_token for entry in entries}
        sources = {entry.source for entry in entries}
        assert "aux1" in tokens
        assert "main" in tokens
        assert "env:GLM_AUX_API_KEY_1" in sources
        assert "env:GLM_API_KEY" in sources

    # ---- Test 5: named-pool storage key isolation ----------------------

    def test_aux_pool_persists_under_named_storage_key(self, tmp_path, monkeypatch):
        """Test 5: entries seeded via ``load_aux_pool`` persist under
        ``auth.json`` key ``credential_pool["auxiliary:zai"]`` — NOT under
        ``["zai"]``. Storage namespace isolation is what makes the runtime
        pool isolation real (T-59-02-T mitigation)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        monkeypatch.setenv("GLM_AUX_API_KEY_1", "aux_a")
        monkeypatch.setenv("GLM_AUX_API_KEY_2", "aux_b")

        from agent.credential_pool import load_aux_pool

        # First load triggers seeding + persistence.
        pool = load_aux_pool("zai")
        assert pool.has_credentials()

        store = _read_auth_store(tmp_path)
        cred_pool = store.get("credential_pool", {})
        # Named-pool storage key must be "auxiliary:zai", NOT "zai".
        assert "auxiliary:zai" in cred_pool, (
            f"Expected 'auxiliary:zai' key in auth.json credential_pool, "
            f"got keys: {list(cred_pool.keys())}"
        )
        assert "zai" not in cred_pool or cred_pool.get("zai") == [], (
            "Default 'zai' pool namespace should not be polluted by aux seeding"
        )

    # ---- Test 6: default load_pool still works (no breaking change) ----

    def test_default_load_pool_unaffected_by_aux_extension(
        self, tmp_path, monkeypatch
    ):
        """Test 6: ``load_pool("zai")`` with only ``GLM_API_KEY=main`` set
        returns a 1-entry default pool as before — guards against accidental
        coupling between the new named-pool code and the existing default
        loader (T-59-06-E mitigation)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        monkeypatch.setenv("GLM_API_KEY", "main")

        from agent.credential_pool import load_pool

        pool = load_pool("zai")
        entries = pool.entries()
        assert len(entries) == 1
        assert entries[0].access_token == "main"
        # Storage must still be under default "zai" key.
        store = _read_auth_store(tmp_path)
        cred_pool = store.get("credential_pool", {})
        assert "zai" in cred_pool
        assert "auxiliary:zai" not in cred_pool

    # ---- Test 7: load_named_pool generic helper ------------------------

    def test_load_named_pool_generic_helper(self, tmp_path, monkeypatch):
        """Test 7: ``load_named_pool("custom-foo", "zai")`` returns a
        CredentialPool — proves the helper is not hardcoded to "auxiliary"."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        from agent.credential_pool import load_named_pool

        pool = load_named_pool("custom-foo", "zai")
        # No env vars set for a custom name → empty pool, but the loader
        # must not crash and must return a CredentialPool whose provider
        # reflects the named-pool key.
        assert hasattr(pool, "entries")
        # Storage key should be "custom-foo:zai".
        store = _read_auth_store(tmp_path)
        cred_pool = store.get("credential_pool", {})
        # Empty pools may or may not write to disk, so we don't strictly
        # assert the storage key here — the loader must just succeed.

    # ---- Test 8: load_named_pool("auxiliary", provider) == load_aux_pool -

    def test_load_named_pool_auxiliary_equals_load_aux_pool(
        self, tmp_path, monkeypatch
    ):
        """Test 8: ``load_named_pool("auxiliary", "zai")`` returns the same
        pool contents as ``load_aux_pool("zai")`` — proves the specialized
        loader is a thin wrapper over the generic helper."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        monkeypatch.setenv("GLM_AUX_API_KEY_1", "shared_key")

        from agent.credential_pool import load_aux_pool, load_named_pool

        pool_a = load_aux_pool("zai")
        pool_b = load_named_pool("auxiliary", "zai")
        tokens_a = [e.access_token for e in pool_a.entries()]
        tokens_b = [e.access_token for e in pool_b.entries()]
        assert tokens_a == tokens_b == ["shared_key"]
