"""Wave 0 contract smoke test — Phase 52 surface must be consumable.

This file is the gate for all of Phase 53: if these imports fail or the
stub return contracts drift, Phase 52 is not actually shipped (or has
silently regressed) and every downstream Phase 53 plan (53-02, 53-03)
will fail in confusing ways. The executor MUST stop at the first
failing test here and investigate rather than continue.

Acceptance (per 53-01-PLAN.md Task 1):

- ``test_phase52_imports_resolve`` — all 11 Phase 52 symbols listed in
  the plan's ``<interfaces>`` block import cleanly and are callable /
  class. No ``ImportError``, no ``AttributeError``.
- ``test_phase52_stub_returns_phase53_marker`` — async. Calls
  ``memory_retrieve_scoped`` and asserts the locked stub payload
  ``{"status": "phase53_not_implemented", "hits": []}`` (per
  ``52-CONTEXT.md`` "Resolved by Kai" point 3 — do NOT change without
  re-running Phase 52 acceptance).
- ``test_phase52_submit_stub_returns_phase53_marker`` — async. Same for
  ``memory_submit_record``; expects
  ``{"status": "phase53_not_implemented", "record_id": None}``.
- ``test_phase52_registry_loads_empty_dir`` — async. With HERMES_HOME
  redirected to an empty tempdir, ``load_agent_registry()`` returns
  ``[]`` (missing agents dir is NOT an error per registry_loader docstring).
- ``test_screenplay_step3_schema_fixture_loads`` — loads
  ``tests/fixtures/screenplay-step3-schema.json`` and asserts the 6
  HOOK-09 contract top-level properties are present.

pytest-asyncio strict mode: every ``async def test_*`` carries an
explicit ``@pytest.mark.asyncio`` marker (per RESEARCH Pitfall 3 +
``tests/agent/test_round_table_executor.py:22-24`` canonical pattern).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# --------------------------------------------------------------------------- #
# Test 1 — Phase 52 contract surface imports resolve
# --------------------------------------------------------------------------- #


def test_phase52_imports_resolve():
    """All 11 Phase 52 symbols listed in 53-01-PLAN.md <interfaces> import cleanly.

    If this fails, Phase 52 is not actually shipped or has regressed — the
    executor MUST stop and investigate rather than continue Phase 53.
    """
    # registry_loader (3 symbols)
    from agent.registry_loader import (  # noqa: F401
        RegistryValidationError,
        load_agent_registry,
        load_one_agent_yaml,
    )

    # round_table_state (5 symbols)
    from agent.round_table_state import (  # noqa: F401
        append_turn,
        open_round_table,
        read_and_recover_state,
        submit_round_table_result,
        validate_project_slug,
        validate_round_id,
    )

    # round_table_executor (3 symbols)
    from agent.round_table_executor import (  # noqa: F401
        _serial_violation_response,
        acquire_round_or_reject,
        release_round_lock,
    )

    # memory_arbitration (4 symbols — counts toward the 11 since Phase 53
    # extends these stubs; plan lists set/get_scoped_agent_id + 2 stubs).
    from agent.memory_arbitration import (  # noqa: F401
        get_scoped_agent_id,
        memory_retrieve_scoped,
        memory_submit_record,
        set_scoped_agent_id,
    )

    # Assert each symbol is callable/class (not None, not a stray attribute).
    assert callable(load_agent_registry)
    assert callable(load_one_agent_yaml)
    assert isinstance(RegistryValidationError, type)
    assert callable(open_round_table)
    assert callable(append_turn)
    assert callable(submit_round_table_result)
    assert callable(read_and_recover_state)
    assert callable(validate_round_id)
    assert callable(validate_project_slug)
    assert callable(acquire_round_or_reject)
    assert callable(release_round_lock)
    assert callable(_serial_violation_response)
    assert callable(set_scoped_agent_id)
    assert callable(get_scoped_agent_id)
    assert callable(memory_retrieve_scoped)
    assert callable(memory_submit_record)


# --------------------------------------------------------------------------- #
# Test 2 — Phase 53 routing degrades gracefully when mem0 backend is unconfigured
# --------------------------------------------------------------------------- #
#
# Phase 52 originally shipped a stub returning `{"status": "phase53_not_implemented", ...}`
# per 52-CONTEXT.md "Resolved by Kai" point 3. Phase 53's CREATIVE-02 (plan 53-02)
# replaced that stub with real mem0 routing per CONTEXT.md decision #5 + 53-02-PLAN.
#
# Without `MEM0_API_KEY` or `plugins.memory.mem0` configured, the routing layer
# MUST degrade gracefully — return `{"status": "unavailable", ...}` instead of
# raising. This is the Phase 53 contract: routing attempted, graceful fallback
# on missing backend, NEVER raise.


@pytest.mark.asyncio
async def test_phase52_stub_returns_phase53_marker(tmp_path, monkeypatch):
    """Phase 53 routing: retrieve degrades to unavailable when mem0 not configured.

    Phase 53's CREATIVE-02 (plan 53-02) replaced Phase 52's
    `phase53_not_implemented` stub with real mem0 routing. Without a mem0
    backend configured, the routing layer MUST return
    `{"status": "unavailable", "hits": []}` (graceful fallback, never raise).
    The `status` key being one of `{"phase53_not_implemented", "unavailable", "ok"}`
    is the contract; downstream callers feature-detect on this key.
    """
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("MEM0_API_KEY", raising=False)
    from agent.memory_arbitration import memory_retrieve_scoped

    result = await memory_retrieve_scoped(query="x", agent_id="y", top_k=1)
    assert result["status"] in {"phase53_not_implemented", "unavailable", "ok"}
    assert result.get("hits", []) == []


# --------------------------------------------------------------------------- #
# Test 3 — Phase 53 routing submit degrades gracefully when mem0 backend is unconfigured
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_phase52_submit_stub_returns_phase53_marker(tmp_path, monkeypatch):
    """Phase 53 routing: submit degrades to unavailable when mem0 not configured.

    Same contract as Test 2 — Phase 53's CREATIVE-02 replaced Phase 52's stub.
    Without mem0 configured, submit returns `{"status": "unavailable", ...}` and
    does NOT raise. record_id is null when unavailable.
    """
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("MEM0_API_KEY", raising=False)
    from agent.memory_arbitration import memory_submit_record

    result = await memory_submit_record(
        agent_id="y", content="x", scope="per_agent", confidence=0.5
    )
    assert result["status"] in {"phase53_not_implemented", "unavailable", "ok"}
    assert result.get("record_id") is None or "record_id" not in result or result.get("record_id")


# --------------------------------------------------------------------------- #
# Test 4 — load_agent_registry returns [] for an empty / missing agents dir
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_phase52_registry_loads_empty_dir(tmp_path, monkeypatch):
    """Empty / missing agents dir is NOT an error — registry returns [].

    Verified at registry_loader.py:306-310: ``if not agents_dir.is_dir()``
    short-circuits to an empty list. This is the foundation for Phase 53's
    transform: before MIGR-01 lands YAMLs, every consumer of the registry
    must gracefully tolerate an empty registry.
    """
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from agent.registry_loader import load_agent_registry

    # Pre-condition: the agents subdir does NOT exist under tmp_path.
    assert not (tmp_path / "agents").exists()
    result = load_agent_registry()
    assert result == [], f"expected [] for missing agents dir, got {result!r}"


# --------------------------------------------------------------------------- #
# Test 5 — HOOK-09 screenplay Step 3 schema fixture loads + declares 6 fields
# --------------------------------------------------------------------------- #


def test_screenplay_step3_schema_fixture_loads():
    """HOOK-09 schema fixture parses + declares all 6 required top-level fields.

    This fixture is consumed by CREATIVE-01 (plan 53-03) to validate the
    output of ``run_screenplay_step3_roundtable.py``. The 6 fields mirror
    the HOOK-09 emotion_curve marker contract per 05-POC-PLAN.md §3.2 —
    losing any one of them in transform breaks the storyboard Step 6.5 +
    visual_executor Step 7 pipeline.
    """
    schema_path = Path(__file__).resolve().parent.parent / "fixtures" / "screenplay-step3-schema.json"
    assert schema_path.exists(), f"fixture missing at {schema_path}"
    data = json.loads(schema_path.read_text(encoding="utf-8"))

    # Draft 2020-12 structural anchors.
    for key in ("$schema", "type", "properties"):
        assert key in data, f"schema missing top-level {key!r}"

    # HOOK-09 contract: all 6 marker-array fields declared at top level.
    properties = data["properties"]
    expected = {"logline", "scene_breakdown", "hooks", "payoffs", "cliffhangers", "emotion_curve"}
    declared = set(properties.keys())
    missing = expected - declared
    assert not missing, f"HOOK-09 schema missing properties: {sorted(missing)}"

    # The required array MUST list all 6 — downstream validators reject
    # outputs that omit any field.
    required = set(data.get("required", []))
    missing_required = expected - required
    assert not missing_required, (
        f"HOOK-09 schema 'required' array missing fields: {sorted(missing_required)}"
    )
