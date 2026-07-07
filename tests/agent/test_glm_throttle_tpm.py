"""Tests for Phase 59 POOL-02: tpm_warning emission in acquire_slot.

Validates the aux-pool TPM check that ``agent/glm_throttle.acquire_slot``
runs BEFORE the existing token-bucket refill loop (CONTEXT.md decision #4):

* When ALL aux-pool keys are below the configured ``tpm_warning_threshold``
  (default 10%), emit a ``tpm_warning`` log + brief sleep until the window
  slides.
* When at least one key has remaining TPM above the threshold, no warning.
* Failures in the TPM check (loader crash, empty pool) must NOT break the
  underlying token-bucket RPM pacing — TPM is a refinement, not a hard
  gate.
* ``pool_name="default"`` callers skip the TPM check entirely (Phase 59-02
  is aux-pool-only).

Context: see .planning/phases/59-aux-pool-isolation/59-02-PLAN.md Task 2
         and 59-CONTEXT.md decision #4.

Test fixture pattern mirrors ``tests/agent/test_glm_throttle.py``.
"""
from __future__ import annotations

import json
import time

import pytest

# Import will fail until agent/glm_throttle.py exposes the new symbols.
from agent.glm_throttle import (  # noqa: E402
    acquire_slot,
    reset_for_testing,
)


def _write_auth_store(tmp_path, payload: dict) -> None:
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "auth.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _clear_aux_env(monkeypatch) -> None:
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


@pytest.fixture(autouse=True)
def _isolate_glm_throttle_state(monkeypatch):
    """Reset throttle bucket registry + control the clock.

    Fake clock starts at t=1000.0; ``time.sleep`` advances the fake clock so
    blocking-acquire loops terminate without real waits. ``time.monotonic``
    inside ``agent.glm_throttle`` AND ``agent.credential_pool`` (TPM window)
    is patched so both see the same controllable time.
    """
    reset_for_testing()
    _now = [1000.0]

    def _fake_monotonic() -> float:
        return _now[0]

    def _fake_sleep(seconds: float) -> None:
        _now[0] += float(seconds)

    import agent.glm_throttle as _throttle_mod

    monkeypatch.setattr(_throttle_mod.time, "monotonic", _fake_monotonic)
    monkeypatch.setattr(_throttle_mod.time, "sleep", _fake_sleep)

    # Patch credential_pool's time.monotonic too — TpmWindow / pool_tpm_status
    # reads it via module-level lookup.
    import agent.credential_pool as _cp_mod

    monkeypatch.setattr(_cp_mod.time, "monotonic", _fake_monotonic)

    yield
    reset_for_testing()


# ===========================================================================
# Task 2: tpm_warning emission in acquire_slot (5 tests)
# ===========================================================================


class TestAcquireSlotTpmWarning:
    """Validates the TPM-check branch in ``acquire_slot``."""

    # ---- Test 1: tpm_warning emitted when all aux keys below threshold ---

    def test_tpm_warning_when_all_keys_below_threshold(
        self, tmp_path, monkeypatch, caplog
    ):
        """Both aux entries consumed ≥90% of cap → acquire_slot emits
        a ``tpm_warning`` log line + brief sleep. ``time.sleep`` is patched
        via the autouse fixture so no real wall-clock wait happens."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")
        monkeypatch.setenv("GLM_AUX_API_KEY_2", "k2")

        from agent.credential_pool import load_aux_pool, TPM_CAP_PER_KEY_GLM
        from dataclasses import replace

        # Pre-seed the pool on disk so acquire_slot's TPM check can load it.
        pool = load_aux_pool("zai")
        entries = sorted(pool.entries(), key=lambda e: e.access_token)
        now = time.monotonic()
        heavy_a = replace(
            entries[0],
            tokens_this_minute=int(TPM_CAP_PER_KEY_GLM * 0.95),
            window_start=now,
        )
        heavy_b = replace(
            entries[1],
            tokens_this_minute=int(TPM_CAP_PER_KEY_GLM * 0.95),
            window_start=now,
        )
        # Persist heavy state to disk so the fresh load_named_pool call
        # inside acquire_slot sees it.
        from agent.credential_pool import write_credential_pool

        write_credential_pool(
            "auxiliary:zai",
            [heavy_a.to_dict(), heavy_b.to_dict()],
        )

        with caplog.at_level("WARNING", logger="agent.glm_throttle"):
            acquire_slot("round_table_opinion", pool_name="auxiliary")

        warning_records = [
            r for r in caplog.records if "tpm_warning" in (r.getMessage() or "")
        ]
        assert warning_records, (
            "Expected a 'tpm_warning' log line when all aux keys below threshold"
        )

    # ---- Test 2: no warning when at least one key has remaining TPM ------

    def test_no_warning_when_one_key_has_remaining_tpm(
        self, tmp_path, monkeypatch, caplog
    ):
        """One entry at 5% remaining, one at 80% remaining → no tpm_warning."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")
        monkeypatch.setenv("GLM_AUX_API_KEY_2", "k2")

        from agent.credential_pool import (
            load_aux_pool,
            TPM_CAP_PER_KEY_GLM,
            write_credential_pool,
        )
        from dataclasses import replace

        pool = load_aux_pool("zai")
        entries = sorted(pool.entries(), key=lambda e: e.access_token)
        now = time.monotonic()
        heavy = replace(
            entries[0],
            tokens_this_minute=int(TPM_CAP_PER_KEY_GLM * 0.95),
            window_start=now,
        )
        light = replace(
            entries[1],
            tokens_this_minute=int(TPM_CAP_PER_KEY_GLM * 0.20),
            window_start=now,
        )
        write_credential_pool(
            "auxiliary:zai",
            [heavy.to_dict(), light.to_dict()],
        )

        with caplog.at_level("WARNING", logger="agent.glm_throttle"):
            acquire_slot("round_table_opinion", pool_name="auxiliary")

        warning_records = [
            r for r in caplog.records if "tpm_warning" in (r.getMessage() or "")
        ]
        assert not warning_records, (
            "Should NOT emit tpm_warning when at least one key has TPM remaining"
        )

    # ---- Test 3: no warning + no crash when aux pool is empty ------------

    def test_no_warning_when_aux_pool_empty(
        self, tmp_path, monkeypatch, caplog
    ):
        """No GLM_AUX_* + no GLM_API_KEY → aux pool empty → acquire_slot
        does NOT crash and does NOT emit tpm_warning (debug-log only)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        with caplog.at_level("DEBUG", logger="agent.glm_throttle"):
            acquire_slot("round_table_opinion", pool_name="auxiliary")

        warning_records = [
            r for r in caplog.records if "tpm_warning" in (r.getMessage() or "")
        ]
        assert not warning_records, (
            "Empty aux pool should not trigger tpm_warning"
        )

    # ---- Test 4: TPM check failure does not break token-bucket acquire ---

    def test_tpm_check_failure_does_not_break_acquire(
        self, tmp_path, monkeypatch, caplog
    ):
        """When ``load_named_pool`` raises, acquire_slot must still return
        normally — the token bucket continues to pace RPM correctly."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        # Force load_named_pool to raise inside acquire_slot.
        import agent.glm_throttle as _mod

        def _boom(*args, **kwargs):
            raise RuntimeError("simulated pool load failure")

        monkeypatch.setattr(_mod, "_check_aux_pool_tpm", _boom)

        # Must not raise.
        acquire_slot("round_table_opinion", pool_name="auxiliary")
        # If we reach here, the token-bucket path survived the TPM-check
        # failure. (Test passes by virtue of not raising.)

    # ---- Test 5: pool_name="default" skips the TPM check entirely --------

    def test_default_pool_name_skips_tpm_check(
        self, tmp_path, monkeypatch
    ):
        """``acquire_slot("non_aux_task", pool_name="default")`` does not
        invoke the aux-pool TPM check at all — verified by monkeypatching
        the check helper and asserting it was never called."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)

        import agent.glm_throttle as _mod

        calls = []

        def _tracking_check(pool_name: str) -> None:
            calls.append(pool_name)
            # Should NEVER be called for pool_name="default".
            assert pool_name != "default", (
                "TPM check must not run for pool_name='default'"
            )

        monkeypatch.setattr(_mod, "_check_aux_pool_tpm", _tracking_check)

        acquire_slot("non_aux_task", pool_name="default")

        assert calls == [], (
            "TPM check helper must not be invoked for pool_name='default'"
        )
