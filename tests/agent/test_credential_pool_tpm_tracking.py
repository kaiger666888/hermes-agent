"""Tests for Phase 59 POOL-02: per-key TPM sliding-window tracking.

Validates the TPM-tracking extension to ``agent/credential_pool.py``:

* ``TPM_CAP_PER_KEY_GLM`` module constant (200_000) — hardcoded per
  CONTEXT.md deferred list ("hardcode at GLM 200K/key for v12.0").
* ``PooledCredential.tokens_this_minute`` + ``window_start`` Optional
  fields — aux-pool entries lazy-init on first use; default-pool entries
  keep ``None`` (TPM tracking is aux-pool-only).
* ``CredentialPool.select_freshest_tpm()`` — returns the entry with the
  most remaining TPM (does NOT go through ``_select_unlocked``).
* ``CredentialPool.record_usage(entry_id, tokens)`` — sliding 60s window;
  resets when ``now - window_start >= 60s``; accumulates otherwise.

Context: see .planning/phases/59-aux-pool-isolation/59-02-PLAN.md
         and 59-CONTEXT.md decisions #3, #4 + deferred list.

Test fixture pattern mirrors ``tests/agent/test_credential_pool_aux_isolation.py``.
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


def _clear_aux_env(monkeypatch) -> None:
    """Strip every GLM_AUX_* and GLM_API_KEY var so tests start from a clean env."""
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
# Task 1: TPM tracking fields + sliding-window reset logic (7 tests)
# ===========================================================================


class TestTpmTrackingBasics:
    """Behavioral coverage for the TPM-window data + CredentialPool methods."""

    # ---- Test 1: fresh aux entry has tokens_this_minute=None + window_start=None

    def test_fresh_aux_entry_has_none_tpm_fields(self, tmp_path, monkeypatch):
        """Test 1: ``load_aux_pool("zai")`` with ``GLM_AUX_API_KEY_1=k1`` returns
        a pool whose entry has ``tokens_this_minute is None`` and
        ``window_start is None`` — TPM fields lazy-init on first record_usage."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entries = pool.entries()
        assert len(entries) == 1
        assert entries[0].tokens_this_minute is None
        assert entries[0].window_start is None

    # ---- Test 2: record_usage on fresh entry initializes the window

    def test_record_usage_initializes_window(self, tmp_path, monkeypatch):
        """Test 2: ``record_usage(entry_id, 5000)`` on a fresh entry sets
        ``tokens_this_minute == 5000`` and ``window_start`` within 1s of now."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entry = pool.entries()[0]
        before = time.monotonic()
        pool.record_usage(entry.id, 5000)
        after = time.monotonic()

        # Re-read the entry from the pool (record_usage mutates state).
        updated = next(e for e in pool.entries() if e.id == entry.id)
        assert updated.tokens_this_minute == 5000
        assert updated.window_start is not None
        assert before - 1.0 <= updated.window_start <= after + 1.0

    # ---- Test 3: sliding window resets after 60s

    def test_sliding_window_resets_after_60s(self, tmp_path, monkeypatch):
        """Test 3: when ``window_start`` is 61s in the past, record_usage
        RESETS the window rather than accumulating (CONTEXT.md decision #3)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entry = pool.entries()[0]
        # Manually stale the window: 61s ago, with 150_000 tokens consumed.
        stale_start = time.monotonic() - 61.0
        # Use replace() via direct mutation through the dataclass — record_usage
        # reads entry.window_start to decide reset vs accumulate.
        from dataclasses import replace
        stale_entry = replace(entry, tokens_this_minute=150_000, window_start=stale_start)
        # Swap into the pool's internal list so record_usage sees the stale state.
        pool._entries = [stale_entry]
        before = time.monotonic()
        pool.record_usage(entry.id, 5000)
        after = time.monotonic()

        updated = next(e for e in pool.entries() if e.id == entry.id)
        # Window slid — fresh count, not 155_000.
        assert updated.tokens_this_minute == 5000
        assert updated.window_start is not None
        assert before - 1.0 <= updated.window_start <= after + 1.0

    # ---- Test 4: no reset within the window — tokens accumulate

    def test_record_usage_accumulates_within_window(self, tmp_path, monkeypatch):
        """Test 4: when ``window_start`` is 30s ago (still inside the 60s
        window), record_usage ADDS to tokens_this_minute; window_start unchanged."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entry = pool.entries()[0]
        # Half-window-old state: 30s ago, 100_000 tokens consumed.
        from dataclasses import replace
        recent_start = time.monotonic() - 30.0
        recent_entry = replace(
            entry, tokens_this_minute=100_000, window_start=recent_start
        )
        pool._entries = [recent_entry]
        pool.record_usage(entry.id, 5000)

        updated = next(e for e in pool.entries() if e.id == entry.id)
        assert updated.tokens_this_minute == 105_000
        # window_start must NOT have moved (still ~30s ago, not reset to now).
        assert abs(updated.window_start - recent_start) < 0.5

    # ---- Test 5: TPM_CAP_PER_KEY_GLM constant exists with correct value

    def test_tpm_cap_constant_exists(self):
        """Test 5: ``TPM_CAP_PER_KEY_GLM == 200_000`` per CONTEXT.md deferred list
        ('Configurable per-key TPM cap — hardcode at GLM 200K/key for v12.0')."""
        from agent.credential_pool import TPM_CAP_PER_KEY_GLM

        assert TPM_CAP_PER_KEY_GLM == 200_000

    # ---- Test 6: default pool entries NOT affected by TPM fields

    def test_default_pool_entries_unaffected_by_tpm_fields(
        self, tmp_path, monkeypatch
    ):
        """Test 6: ``load_pool("zai")`` (default pool) with ``GLM_API_KEY=k``
        returns entries whose ``tokens_this_minute is None`` and
        ``window_start is None`` — TPM tracking is aux-pool-only, and the
        default ``select()`` does NOT consult TPM."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_API_KEY", "k")

        from agent.credential_pool import load_pool

        pool = load_pool("zai")
        entries = pool.entries()
        assert len(entries) == 1
        assert entries[0].tokens_this_minute is None
        assert entries[0].window_start is None
        # The default select() path must NOT consult TPM.
        selected = pool.select()
        assert selected is not None
        assert selected.tokens_this_minute is None

    # ---- Test 7: record_usage on unknown entry_id is a no-op + debug log

    def test_record_usage_unknown_entry_is_noop(self, tmp_path, monkeypatch, caplog):
        """Test 7: ``record_usage("nonexistent-id", 1000)`` does not raise and
        does not mutate any entry. A debug-level log line is emitted."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        entries_before = pool.entries()
        tokens_before = [(e.id, e.tokens_this_minute) for e in entries_before]

        with caplog.at_level("DEBUG", logger="agent.credential_pool"):
            pool.record_usage("nonexistent-id", 1000)

        # No mutation.
        tokens_after = [(e.id, e.tokens_this_minute) for e in pool.entries()]
        assert tokens_before == tokens_after
        # Debug log emitted (best-effort — grep the captured records).
        debug_lines = [
            r for r in caplog.records
            if "nonexistent-id" in (r.getMessage() or "")
        ]
        assert debug_lines, "Expected a debug log mentioning the unknown entry_id"


# ===========================================================================
# Bonus: select_freshest_tpm behavior (covered by plan Task 2 integration but
# proven here in isolation for the GREEN gate).
# ====================================================================================


class TestSelectFreshestTpm:
    """Behavioral coverage for ``CredentialPool.select_freshest_tpm``."""

    def test_select_freshest_returns_highest_remaining_tpm(
        self, tmp_path, monkeypatch
    ):
        """With 2 entries where one has consumed 90% of cap and the other
        only 10%, select_freshest_tpm returns the less-consumed one."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")
        monkeypatch.setenv("GLM_AUX_API_KEY_2", "k2")

        from agent.credential_pool import load_aux_pool, TPM_CAP_PER_KEY_GLM
        from dataclasses import replace

        pool = load_aux_pool("zai")
        entries = sorted(pool.entries(), key=lambda e: e.access_token)
        # Make k1 heavily consumed (180_000 of 200_000), k2 lightly (20_000).
        now = time.monotonic()
        heavy = replace(entries[0], tokens_this_minute=180_000, window_start=now)
        light = replace(entries[1], tokens_this_minute=20_000, window_start=now)
        pool._entries = [heavy, light]

        selected = pool.select_freshest_tpm()
        assert selected is not None
        assert selected.access_token == "k2"

    def test_select_freshest_returns_none_when_pool_empty(
        self, tmp_path, monkeypatch
    ):
        """Empty aux pool returns None from select_freshest_tpm."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        from agent.credential_pool import load_aux_pool

        pool = load_aux_pool("zai")
        assert pool.select_freshest_tpm() is None
