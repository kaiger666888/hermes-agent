"""CREATIVE-01 — unit tests for the real-GLM ``get_agent_opinion`` body.

Plan 53-03 Task 1: replace Phase 52's ``"[phase52_placeholder]"`` opinion
with a real ``auxiliary_client.call_llm(task="round_table_opinion",
provider="glm")`` dispatch, wire in scoped memory retrieval, and preserve
the T-52-15 try/finally lock contract + INFRA-04 serial enforcement.

Coverage (6 tests, all ``@pytest.mark.asyncio`` per RESEARCH Pitfall 3):

1. ``test_get_agent_opinion_returns_real_glm_opinion`` — mocked
   ``call_llm``; returned JSON ``opinion`` field is the mocked content
   (NOT ``"[phase52_placeholder]"``).
2. ``test_get_agent_opinion_uses_round_table_opinion_task`` — mocked
   ``call_llm``; assert invoked with ``task="round_table_opinion"`` AND
   ``provider="glm"`` (MEMORY.md ``feedback-glm-5-2-only.md`` enforcement).
3. ``test_get_agent_opinion_sets_scoped_agent_id_before_memory_call`` —
   spy on ``set_scoped_agent_id``; assert it was called with the
   panelist's ``agent_id`` BEFORE ``memory_retrieve_scoped`` and called
   with ``None`` in the finally cleanup (RESEARCH Pitfall 5).
4. ``test_get_agent_opinion_preserves_try_finally_lock_contract`` —
   mocked ``call_llm`` raises; assert ``release_round_lock`` was still
   called exactly once (T-52-15 DoS mitigation preserved).
5. ``test_get_agent_opinion_serial_violation_unchanged`` — concurrent
   ``asyncio.gather`` for same ``round_id`` (in the test only): one
   returns 429 ``serial_violation``, the other succeeds (Phase 52
   contract preserved).
6. ``test_get_agent_opinion_appends_turn_with_opinion`` — after a
   successful call, read the state file and assert
   ``state["turns"][-1]["opinion"]`` equals the mocked GLM response
   (NOT ``[phase52_placeholder]``).

These tests require ``get_agent_opinion`` to be importable as a
module-level async function in ``mcp_serve``. Phase 52 shipped it as a
nested function inside ``create_mcp_server()``; plan 53-03 lifts it
(module-level wrapper, ``create_mcp_server`` re-registers it via
``@mcp.tool()``) so it can be unit-tested directly. The Phase 52 contract
is preserved — the FastMCP server still registers the same tool name with
the same docstring.

pytest-asyncio strict mode: every ``async def test_*`` carries an
explicit ``@pytest.mark.asyncio`` marker (per RESEARCH Pitfall 3 +
``tests/agent/test_round_table_executor.py:22-24`` canonical pattern).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest


# --------------------------------------------------------------------------- #
# Helpers — write a minimal valid screenplay agent YAML fixture for persona
# --------------------------------------------------------------------------- #


_SCREENPLAY_AGENT_YAML = """\
name: screenplay
description: |
  Screenplay expert for testing.
version: "1.0.0"
persona: |
  You are the screenplay expert (编剧). Contribute your expert slice.
tools:
  - hermes_llm
  - read_file
  - search_files
  - write_file
  - patch
memory_scope: per_agent
lineage:
  derived_from_skill_id: screenplay
  derived_from_repo: kais-hermes-skills
  transform_date: "2026-07-07"
  transform_notes: |
    HOOK-09 emotion_curve marker arrays remain contract-load-bearing.
  skill_sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
tags:
  - movie
  - screenplay
expert_id: screenplay
metrics:
  - hook_density
related_agents: []
evolution_log: []
fitness_score: null
platforms:
  - linux
  - macos
  - windows
round_table_eligible: true
default_invocation: mcp_tool
"""


def _seed_screenplay_agent_yaml(hermes_home: Path) -> None:
    """Drop a minimal valid screenplay YAML at {hermes_home}/agents/."""
    agents_dir = hermes_home / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "screenplay.agent.yaml").write_text(
        _SCREENPLAY_AGENT_YAML, encoding="utf-8"
    )


def _open_round(
    project_slug: str = "screenplay-step3-poc",
    round_id: str = "round-test-0001",
    question: str = "Generate screenplay Step 3 for the test logline.",
) -> dict[str, Any]:
    """Build the kwargs for round_table_open (returns args ready to **)."""
    return {
        "project_slug": project_slug,
        "question": question,
        "panelist_agent_ids": ["screenplay", "cinematographer"],
        "caller": "test_run_screenplay_step3",
    }


class _MockResponse:
    """Minimal stand-in for the OpenAI ChatCompletion response shape."""

    def __init__(self, content: str) -> None:
        # Match the only attribute the production code reads:
        # response.choices[0].message.content
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": content})()})()]


# --------------------------------------------------------------------------- #
# Test 1 — get_agent_opinion returns the real mocked-GLM opinion
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_agent_opinion_returns_real_glm_opinion(tmp_path, monkeypatch):
    """Returned JSON ``opinion`` field equals the mocked GLM response.

    Phase 52 returned ``"[phase52_placeholder]"``; Phase 53 must return the
    real LLM-generated text.
    """
    import mcp_serve
    import agent.auxiliary_client

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _seed_screenplay_agent_yaml(tmp_path)

    expected_opinion = (
        "Scene 1 establishes the protagonist's emotional baseline "
        "with a quiet cold-open..."
    )

    call_log: list[dict[str, Any]] = []

    def _mock_call_llm(*args, **kwargs):
        call_log.append({"args": args, "kwargs": kwargs})
        return _MockResponse(expected_opinion)

    monkeypatch.setattr(agent.auxiliary_client, "call_llm", _mock_call_llm)

    # Open a round
    open_resp = await mcp_serve.round_table_open(
        round_id="round-opinion-0001",
        **_open_round(),
    )
    open_data = json.loads(open_resp)
    assert "error" not in open_data, f"round_table_open failed: {open_data}"

    opinion_resp = await mcp_serve.get_agent_opinion(
        round_id="round-opinion-0001",
        project_slug="screenplay-step3-poc",
        agent_id="screenplay",
        topic="Screenplay Step 3 scene design",
        panel_context=None,
    )
    opinion_data = json.loads(opinion_resp)
    assert opinion_data.get("status") == "ok"
    assert opinion_data["opinion"] == expected_opinion
    assert opinion_data["opinion"] != "[phase52_placeholder]"


# --------------------------------------------------------------------------- #
# Test 2 — call_llm is invoked with task + provider locked to GLM
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_agent_opinion_uses_round_table_opinion_task(tmp_path, monkeypatch):
    """``call_llm`` receives ``task="round_table_opinion"`` + ``provider="glm"``.

    MEMORY.md ``feedback-glm-5-2-only.md`` mandates GLM-only for these
    auxiliary tasks; Phase 53 must NOT rely on the auto-chain (Pitfall 6).
    """
    import mcp_serve
    import agent.auxiliary_client

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _seed_screenplay_agent_yaml(tmp_path)

    calls: list[dict[str, Any]] = []

    def _mock_call_llm(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return _MockResponse("ok")

    monkeypatch.setattr(agent.auxiliary_client, "call_llm", _mock_call_llm)

    await mcp_serve.round_table_open(
        round_id="round-task-0001",
        **_open_round(),
    )
    await mcp_serve.get_agent_opinion(
        round_id="round-task-0001",
        project_slug="screenplay-step3-poc",
        agent_id="screenplay",
        topic="design the scene",
    )
    assert len(calls) == 1
    kwargs = calls[0]["kwargs"]
    # task may be positional or keyword — accept either
    task_value = kwargs.get("task") or (
        calls[0]["args"][0] if calls[0]["args"] else None
    )
    assert task_value == "round_table_opinion", (
        f"task must be 'round_table_opinion' (got {task_value!r})"
    )
    assert kwargs.get("provider") == "glm", (
        f"provider must be 'glm' (got {kwargs.get('provider')!r})"
    )


# --------------------------------------------------------------------------- #
# Test 3 — set_scoped_agent_id called BEFORE memory_retrieve_scoped + cleared in finally
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_agent_opinion_sets_scoped_agent_id_before_memory_call(
    tmp_path, monkeypatch
):
    """ContextVar ordering: set BEFORE memory retrieve, cleared in finally.

    RESEARCH Pitfall 5: skipping this leaks namespace routing across panelist
    boundaries. The set MUST happen before any ``memory_retrieve_scoped``
    call, and MUST be cleared to ``None`` on every exit path (finally).
    """
    import mcp_serve
    import agent.auxiliary_client
    import agent.memory_arbitration
    from agent.memory_arbitration import set_scoped_agent_id

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _seed_screenplay_agent_yaml(tmp_path)

    set_calls: list[Any] = []
    mem_calls: list[Any] = []

    original_set = set_scoped_agent_id

    def _spy_set(agent_id):
        set_calls.append(agent_id)
        original_set(agent_id)

    async def _spy_mem(*args, **kwargs):
        # Record the scoped value AT the moment memory_retrieve was called.
        from agent.memory_arbitration import get_scoped_agent_id

        mem_calls.append(
            {"scoped_at_call": get_scoped_agent_id(), "kwargs": kwargs}
        )
        return {"status": "unavailable", "hits": []}

    monkeypatch.setattr(agent.memory_arbitration, "set_scoped_agent_id", _spy_set)
    monkeypatch.setattr(
        agent.memory_arbitration, "memory_retrieve_scoped", _spy_mem
    )
    monkeypatch.setattr(
        agent.auxiliary_client,
        "call_llm",
        lambda *a, **kw: _MockResponse("anything"),
    )

    await mcp_serve.round_table_open(
        round_id="round-scope-0001",
        **_open_round(),
    )
    await mcp_serve.get_agent_opinion(
        round_id="round-scope-0001",
        project_slug="screenplay-step3-poc",
        agent_id="screenplay",
        topic="design the scene",
    )

    # The FIRST set_scoped_agent_id call must have happened with the
    # panelist agent_id BEFORE memory_retrieve_scoped was invoked.
    assert len(set_calls) >= 1, "set_scoped_agent_id was never called"
    assert set_calls[0] == "screenplay"
    assert len(mem_calls) == 1, (
        f"expected 1 memory_retrieve call, got {len(mem_calls)}"
    )
    assert mem_calls[0]["scoped_at_call"] == "screenplay", (
        "memory_retrieve_scoped ran WITHOUT the ContextVar set"
    )
    # And the finally block must have cleared it to None
    assert set_calls[-1] is None, (
        f"finally cleanup did not clear ContextVar (last set call: {set_calls[-1]!r})"
    )


# --------------------------------------------------------------------------- #
# Test 4 — T-52-15 try/finally lock contract preserved (release even on exception)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_agent_opinion_preserves_try_finally_lock_contract(
    tmp_path, monkeypatch
):
    """On ``call_llm`` exception, ``release_round_lock`` still runs once.

    Phase 52's T-52-15 (DoS) mitigation: per-roundId lock MUST release on
    every path — happy, error, AND CancelledError. Without finally, an
    exception permanently blocks that roundId (Pitfall 2).
    """
    import mcp_serve
    import agent.auxiliary_client
    import agent.round_table_executor

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _seed_screenplay_agent_yaml(tmp_path)

    def _boom(*args, **kwargs):
        raise RuntimeError("GLM API timeout")

    monkeypatch.setattr(agent.auxiliary_client, "call_llm", _boom)

    release_calls: list[str] = []
    original_release = agent.round_table_executor.release_round_lock

    async def _spy_release(round_id: str) -> None:
        release_calls.append(round_id)
        await original_release(round_id)

    monkeypatch.setattr(
        agent.round_table_executor, "release_round_lock", _spy_release
    )
    # Also patch the symbol imported inside mcp_serve if applicable.
    monkeypatch.setattr(
        "agent.round_table_executor.release_round_lock", _spy_release
    )

    await mcp_serve.round_table_open(
        round_id="round-finally-0001",
        **_open_round(),
    )

    # The opinion call must propagate the exception (or return an error).
    # Either way the lock MUST have been released exactly once.
    try:
        await mcp_serve.get_agent_opinion(
            round_id="round-finally-0001",
            project_slug="screenplay-step3-poc",
            agent_id="screenplay",
            topic="test",
        )
    except RuntimeError:
        pass  # acceptable — propagation path

    assert len(release_calls) == 1, (
        f"release_round_lock must be called exactly once on exception path; "
        f"got {len(release_calls)} calls (roundIds: {release_calls})"
    )
    assert release_calls[0] == "round-finally-0001"


# --------------------------------------------------------------------------- #
# Test 5 — INFRA-04 serial violation behavior preserved
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_agent_opinion_serial_violation_unchanged(tmp_path, monkeypatch):
    """Concurrent calls for same round_id: one wins, one gets 429.

    Phase 52 INFRA-04 + SC#4 hard constraint — strict serial per roundId.
    Production NEVER calls these concurrently; the test does so to verify
    the contract is preserved after Phase 53's body change.
    """
    import mcp_serve
    import agent.auxiliary_client

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _seed_screenplay_agent_yaml(tmp_path)

    call_count = {"n": 0}

    def _slow_call_llm(*args, **kwargs):
        call_count["n"] += 1
        # Yield point — lets the second coroutine race into the lock check
        # while the first is still inside the body.
        import time

        time.sleep(0.05)
        return _MockResponse(f"opinion-{call_count['n']}")

    monkeypatch.setattr(agent.auxiliary_client, "call_llm", _slow_call_llm)

    await mcp_serve.round_table_open(
        round_id="round-serial-0001",
        **_open_round(),
    )

    # Two concurrent calls to the SAME round_id.
    results = await asyncio.gather(
        mcp_serve.get_agent_opinion(
            round_id="round-serial-0001",
            project_slug="screenplay-step3-poc",
            agent_id="screenplay",
            topic="topic-A",
        ),
        mcp_serve.get_agent_opinion(
            round_id="round-serial-0001",
            project_slug="screenplay-step3-poc",
            agent_id="screenplay",
            topic="topic-B",
        ),
        return_exceptions=True,
    )

    parsed = []
    for r in results:
        if isinstance(r, Exception):
            parsed.append({"exception": str(r)})
        else:
            parsed.append(json.loads(r))

    # Exactly one must succeed, exactly one must report serial_violation
    statuses = [p.get("status") or p.get("error") for p in parsed]
    serial_ones = [p for p in parsed if "serial" in str(p).lower() or "429" in str(p)]
    ok_ones = [p for p in parsed if p.get("status") == "ok"]
    assert len(serial_ones) == 1, (
        f"expected exactly 1 serial_violation result, got {len(serial_ones)}; "
        f"results: {parsed}"
    )
    assert len(ok_ones) == 1, (
        f"expected exactly 1 ok result, got {len(ok_ones)}; results: {parsed}"
    )


# --------------------------------------------------------------------------- #
# Test 6 — state file records the real opinion (not the placeholder)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_agent_opinion_appends_turn_with_opinion(tmp_path, monkeypatch):
    """After a successful call, ``state["turns"][-1]["opinion"]`` is the GLM text.

    Phase 52 wrote ``"[phase52_placeholder]"`` into the state file. Phase 53
    must write the real LLM-generated opinion so the driver script can
    harvest 9 distinct opinions for downstream synthesis.
    """
    import mcp_serve
    import agent.auxiliary_client
    from hermes_constants import get_hermes_home
    from agent.round_table_state import read_and_recover_state

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _seed_screenplay_agent_yaml(tmp_path)

    expected = "Real screenplay opinion: cold-open with protagonist's morning ritual."

    monkeypatch.setattr(
        agent.auxiliary_client,
        "call_llm",
        lambda *a, **kw: _MockResponse(expected),
    )

    await mcp_serve.round_table_open(
        round_id="round-state-0001",
        **_open_round(),
    )
    await mcp_serve.get_agent_opinion(
        round_id="round-state-0001",
        project_slug="screenplay-step3-poc",
        agent_id="screenplay",
        topic="scene 1 design",
    )

    state_path = (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / "screenplay-step3-poc"
        / "round_tables"
        / "round-state-0001.json"
    )
    assert state_path.exists(), f"state file not written at {state_path}"
    state = read_and_recover_state(state_path)
    turns = state.get("turns", [])
    assert len(turns) == 1, f"expected 1 turn, got {len(turns)}"
    assert turns[0]["opinion"] == expected, (
        f"state turn opinion must be the GLM response; "
        f"got {turns[0]['opinion']!r}"
    )
    assert turns[0]["opinion"] != "[phase52_placeholder]"
    assert turns[0]["panelistId"] == "screenplay"
