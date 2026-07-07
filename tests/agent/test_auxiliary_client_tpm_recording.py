"""Integration tests for Phase 59 POOL-02: post-call record_usage wire-in.

Validates the integration between ``agent/auxiliary_client._capture_usage``
(Phase 58-01 chokepoint) and ``agent.credential_pool.record_usage`` (Phase
59-02 POOL-02):

* Successful aux-pool calls decrement the selected entry's remaining TPM
  by ``response.usage.total_tokens``.
* Error-path calls (no response.usage) do NOT mutate TPM state and do NOT
  crash.
* Default-pool calls do NOT touch aux-pool TPM (T-59-11-E mitigation).
* TPM state persists across ``load_aux_pool`` reloads (T-59-09-R
  cross-process consistency).

Context: see .planning/phases/59-aux-pool-isolation/59-02-PLAN.md Task 3
         and 59-CONTEXT.md decisions #4 + threat register T-59-09/11.

Test strategy: directly invoke ``_capture_usage`` with a fake response +
``_select_pool_entry`` to set ``_LAST_SELECTED_AUX_ENTRY_ID``, then verify
the aux pool's on-disk state reflects the consumed tokens. Avoids the
heavy ``call_llm`` mocking (network / provider resolution) by exercising
the integration chokepoint directly.
"""
from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest


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


def _make_usage_response(prompt: int, completion: int) -> SimpleNamespace:
    """Build a fake response with .choices[0].message + .usage for
    _validate_llm_response + _capture_usage."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
        usage=SimpleNamespace(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        ),
    )


@pytest.fixture(autouse=True)
def _reset_last_selected_aux_entry_id():
    """Reset the module-level _LAST_SELECTED_AUX_ENTRY_ID between tests so
    prior aux state never bleeds into the next test's assertions."""
    import agent.auxiliary_client as aux_mod

    saved = aux_mod._LAST_SELECTED_AUX_ENTRY_ID
    aux_mod._LAST_SELECTED_AUX_ENTRY_ID = None
    yield
    aux_mod._LAST_SELECTED_AUX_ENTRY_ID = saved


# ===========================================================================
# Task 3: Integration — _capture_usage → record_usage (5 tests)
# ===========================================================================


class TestCaptureUsageTpmRecording:
    """Validates the post-call TPM attribution wire-in."""

    # ---- Test 1: successful call records total_tokens against aux entry ---

    def test_successful_call_records_tokens_against_aux_entry(
        self, tmp_path, monkeypatch
    ):
        """Select an aux entry via _select_pool_entry → call _capture_usage
        with a fake response carrying total_tokens=1500 → the aux entry's
        ``tokens_this_minute == 1500`` afterwards."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.auxiliary_client import _select_pool_entry, _capture_usage
        from agent.credential_pool import load_aux_pool

        # Select an aux entry — this sets _LAST_SELECTED_AUX_ENTRY_ID.
        pool_exists, entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert pool_exists and entry is not None

        # Simulate a successful LLM response with 1500 total tokens.
        _capture_usage(_make_usage_response(prompt=1000, completion=500))

        # Re-load the pool from disk and verify the entry's TPM state.
        reloaded = load_aux_pool("zai")
        reloaded_entry = next(
            e for e in reloaded.entries() if e.id == entry.id
        )
        assert reloaded_entry.tokens_this_minute == 1500
        assert reloaded_entry.window_start is not None

    # ---- Test 2: error path with no response.usage → no recording, no crash

    def test_error_path_no_usage_no_mutation(self, tmp_path, monkeypatch):
        """When the LLM call errors and there is no response.usage,
        _capture_usage must not mutate TPM state and must not crash.

        Simulated by calling _capture_usage with a response that has
        ``usage=None`` — the function returns early without recording."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.auxiliary_client import _select_pool_entry, _capture_usage
        from agent.credential_pool import load_aux_pool

        _, entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert entry is not None

        # Response with no .usage — _capture_usage returns early.
        no_usage_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
        )
        # Deliberately does NOT raise.
        _capture_usage(no_usage_response)

        # TPM state must be unchanged.
        reloaded = load_aux_pool("zai")
        reloaded_entry = next(
            e for e in reloaded.entries() if e.id == entry.id
        )
        assert reloaded_entry.tokens_this_minute is None
        assert reloaded_entry.window_start is None

    # ---- Test 3: default-pool call does NOT attribute TPM ---------------

    def test_default_pool_call_does_not_attribute_tpm(
        self, tmp_path, monkeypatch
    ):
        """A default-pool _select_pool_entry call clears
        _LAST_SELECTED_AUX_ENTRY_ID, so the subsequent _capture_usage does
        NOT decrement any aux-pool entry's TPM (T-59-11-E mitigation)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        # Default pool: a single GLM_API_KEY.
        monkeypatch.setenv("GLM_API_KEY", "default_main")
        # Aux pool: a separate key.
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "aux_only")

        from agent.auxiliary_client import _select_pool_entry, _capture_usage
        from agent.credential_pool import load_aux_pool
        import agent.auxiliary_client as aux_mod

        # First select an aux entry to populate the tracker.
        _, aux_entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert aux_entry is not None
        assert aux_mod._LAST_SELECTED_AUX_ENTRY_ID is not None

        # Now select a default-pool entry — this MUST clear the tracker.
        _, default_entry = _select_pool_entry("zai", pool_name="default")
        assert default_entry is not None
        # Read the module-level value post-mutation (it's reassigned, not
        # mutated in place, so we must re-read via attribute access).
        assert aux_mod._LAST_SELECTED_AUX_ENTRY_ID is None

        # _capture_usage on a default-pool response must NOT touch the aux pool.
        _capture_usage(_make_usage_response(prompt=2000, completion=1000))

        aux_pool = load_aux_pool("zai")
        aux_entries = aux_pool.entries()
        # No aux entry should have TPM state mutated.
        for e in aux_entries:
            assert e.tokens_this_minute is None

    # ---- Test 4: multiple sequential calls accumulate within window ------

    def test_multiple_sequential_calls_accumulate(self, tmp_path, monkeypatch):
        """3 sequential aux calls consuming 5000 tokens each → the selected
        entry's tokens_this_minute == 15000 (assuming the window doesn't
        slide between calls — the autouse clock is not patched here, but
        the test runs well under 60s so the window stays open)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.auxiliary_client import _select_pool_entry, _capture_usage
        from agent.credential_pool import load_aux_pool

        # Single aux entry — all 3 calls hit the same entry.
        _, entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert entry is not None

        for _ in range(3):
            _capture_usage(_make_usage_response(prompt=2500, completion=2500))

        reloaded = load_aux_pool("zai")
        reloaded_entry = next(
            e for e in reloaded.entries() if e.id == entry.id
        )
        # Window did not slide (test runs in ~1s) → tokens accumulate to 15000.
        assert reloaded_entry.tokens_this_minute == 15000

    # ---- Test 5: TPM state persists across load_aux_pool reloads ---------

    def test_tpm_state_persists_across_reloads(self, tmp_path, monkeypatch):
        """After a call that consumes 5000 tokens, a fresh
        ``load_aux_pool("zai")`` returns a pool whose entry has
        ``tokens_this_minute == 5000`` — proves the persistence via
        ``_persist()`` called inside record_usage (T-59-09-R mitigation:
        cross-process consistency)."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
        _write_auth_store(tmp_path, {"version": 1, "credential_pool": {}})
        _clear_aux_env(monkeypatch)
        monkeypatch.setenv("GLM_AUX_API_KEY_1", "k1")

        from agent.auxiliary_client import _select_pool_entry, _capture_usage
        from agent.credential_pool import load_aux_pool

        _, entry = _select_pool_entry("zai", pool_name="auxiliary")
        assert entry is not None

        # First call: 5000 tokens consumed.
        _capture_usage(_make_usage_response(prompt=3000, completion=2000))

        # Reload the pool twice (simulating a parallel process).
        reloaded_1 = load_aux_pool("zai")
        reloaded_2 = load_aux_pool("zai")
        for reloaded in (reloaded_1, reloaded_2):
            r_entry = next(
                e for e in reloaded.entries() if e.id == entry.id
            )
            assert r_entry.tokens_this_minute == 5000
            assert r_entry.window_start is not None
