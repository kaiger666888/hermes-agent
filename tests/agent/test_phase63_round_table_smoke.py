"""SC#3 visual_executor round-table smoke for Phase 63.

Mock LLM by default (deterministic); live GLM opt-in via
``HERMES_PHASE63_LIVE_SMOKE=1`` env var. Mock path is SC#3 authoritative
per ``63-RESEARCH.md`` G3 Option A. The ``conftest.py:95``
``_CREDENTIAL_NAMES`` tuple strips ``GLM_API_KEY`` per-test, making the
mock MANDATORY for hermetic CI — the live test is operator opt-in only.

Lifecycle exercised (per ``63-03-PLAN.md`` <objective>):

    open_round_table (state_dir computed by _compute_state_dir)
        -> await get_agent_opinion(agent_id="visual_executor")
        -> submit_round_table_result (seal with status="completed")

Constraints honored:
- Pitfall #3 (GLM_API_KEY stripped): mock applied UNCONDITIONALLY in the
  authoritative test, NOT conditionally.
- Pitfall #4 (minItems=2 panelists): stage BOTH visual_executor +
  cinematographer YAMLs. Only call ``get_agent_opinion`` for
  visual_executor (SC#3 only needs one agent's non-empty response).
- Pitfall #6 (registry cache reset): invalidate
  ``registry_loader._REGISTRY_CACHE`` between tests via ``monkeypatch``.
- INFRA-04 serial constraint: no parallel-dispatch primitives — sequential
  ``await get_agent_opinion(...)`` only (acceptance grep for gather must
  return 0).
- CLAUDE.md: ``encoding="utf-8"`` on every ``open()`` / ``read_text()``,
  ``snake_case``, ``from __future__ import annotations``, uses
  ``get_hermes_home()`` rather than ``Path.home`` concatenation.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

import pytest


# ── Constants ────────────────────────────────────────────────────────────────

# Real YAMLs staged READ-ONLY from the live ~/.hermes/agents/ tree.
# WR-01 fix (review): compute dynamically via Path.home() instead of
# hardcoding '/home/kai/...'. conftest.py's _hermetic_environment fixture
# redirects HERMES_HOME but NOT HOME (see conftest.py:347-353), so
# Path.home() still resolves to the real user's home — '/home/kai' on
# Kai's machine, '/home/runner' in CI, etc. Combined with the
# pytest.skip (not pytest.fail) fallback in _seed_visual_executor_yamls,
# tests degrade gracefully to SKIPPED on machines without Phase 62's
# 21 shipped YAMLs, instead of HARD-FAILING.
# Naming (IN-04): leading underscore — module-private per CLAUDE.md.
_REAL_AGENTS_DIR = Path.home() / ".hermes" / "agents"

# The smoke target project slug. Passed as project_id to open_round_table
# AND as project_slug to get_agent_opinion — they MUST match because
# mcp_serve.get_agent_opinion computes state_path from the slug (lines
# 758-765 of mcp_serve.py).
SMOKE_PROJECT_SLUG = "phase63-smoke"

# Phase 63 CONTEXT.md <specifics>: fixture prompt exercising
# visual_executor's persona-declared drawer + animator sub_steps +
# dreamina CLI capability (synthesis-only — no real image gen).
SMOKE_QUESTION = (
    "Given the screenplay scene 'INT. COFFEE SHOP - DAY (first meeting)', "
    "describe how you would execute shot 1 visually."
)

# Two panelists required (round-table-state-schema.yaml minItems=2).
# visual_executor is the SC#3 smoke target; cinematographer is the
# related_agent collaborator that satisfies the minItems=2 constraint
# (per the related_agents edge in both YAMLs). Only visual_executor is
# asked for an opinion — the second panelist is along for the ride.
PANELIST_AGENT_IDS = ["visual_executor", "cinematographer"]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_visual_executor_yamls(tmp_path) -> None:
    """Stage real visual_executor + cinematographer YAMLs into the
    redirected HERMES_HOME's ``agents/`` directory.

    The autouse ``_hermetic_environment`` fixture (conftest.py:327)
    redirects HERMES_HOME to ``tmp_path / "hermes_test"`` and pre-creates
    ``sessions/``, ``cron/``, ``memories/``, ``skills/`` — but NOT
    ``agents/``, so we mkdir it here.

    Also invalidates the ``registry_loader._REGISTRY_CACHE`` so the next
    ``load_agent_registry()`` call picks up the freshly-staged YAMLs
    instead of returning a stale cached entry from an earlier test
    (RESEARCH Pitfall #6).

    Args:
        tmp_path: pytest's per-test tmp_path fixture. The redirected
            HERMES_HOME is ``tmp_path / "hermes_test"`` (set by the
            autouse _hermetic_environment fixture).
    """
    from hermes_constants import get_hermes_home

    agents_dir = get_hermes_home() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    for agent_id in PANELIST_AGENT_IDS:
        src = _REAL_AGENTS_DIR / f"{agent_id}.agent.yaml"
        if not src.exists():
            # WR-01 fix (review): SKIP not FAIL. The Phase 62 deliverable
            # (21 YAMLs at ~/.hermes/agents/) is only present on Kai's
            # machine. On any other developer machine, CI runner, or
            # Docker container, _REAL_AGENTS_DIR points to a path that
            # doesn't have these YAMLs. Hard-failing breaks hermetic-test
            # invariant (conftest.py:8-12) and breaks CI. Skip lets the
            # test degrade gracefully — the operator sees "skipped:
            # required fixture YAML missing" and knows Phase 62 isn't
            # installed locally.
            pytest.skip(
                f"Required fixture YAML missing: {src}. Phase 62 deliverable "
                f"(21 agent YAMLs) not installed in real ~/.hermes/agents/. "
                f"Install Phase 62 deliverables or run on Kai's machine."
            )
        shutil.copyfile(src, agents_dir / f"{agent_id}.agent.yaml")

    # Pitfall #6: invalidate the module-level registry cache so the
    # staged YAMLs are picked up on the next load. Mirrors the
    # test_mcp_serve_round_table.py:80-83 pattern.
    try:
        from agent import registry_loader

        registry_loader._REGISTRY_CACHE = None
    except Exception as exc:
        # registry_loader may not be importable in some environments;
        # the smoke still works because get_agent_opinion reads the
        # persona directly from the YAML via _load_persona_for_agent.
        # WR-03 fix (review): bind the exception and emit a debug log so
        # a future refactor that renames _REGISTRY_CACHE surfaces clearly
        # instead of silently proceeding with a stale cache.
        import logging as _logging

        _logging.getLogger(__name__).debug(
            "registry_loader cache reset skipped: %s", exc
        )


def _mock_call_llm(monkeypatch) -> None:
    """Patch ``auxiliary_client.call_llm`` to return a deterministic
    opinion string containing the visual_executor persona keywords
    (``drawer`` + ``animator``).

    The mock response shape mirrors the canonical pattern in
    ``tests/agent/test_mcp_serve_round_table.py:88-117`` — a synthetic
    ``FakeResponse`` instance whose ``choices[0].message.content`` is
    the opinion text. ``get_agent_opinion`` extracts content via
    ``str(response.choices[0].message.content)`` (mcp_serve.py:874), so
    the shape MUST expose those attributes.

    This mock is ALWAYS applied in the authoritative test path
    (Pitfall #3: GLM_API_KEY is stripped by conftest, so an unmocked
    call would raise). The live test path does NOT call this helper.
    """
    from agent import auxiliary_client

    def _fake_call_llm(*args, **kwargs):
        agent_id = kwargs.get("agent_id") or (args[0] if args else "test")
        # Deterministic opinion containing persona keywords so the live
        # test's keyword assertion (drawer/animator) can be reused
        # against the mock if needed.
        content = (
            f"[TEST MOCK] {agent_id} opinion on shot 1: use drawer sub_step "
            f"for FLUX 2 first_frame, then animator sub_step for veo3.1 "
            f"video gen."
        )
        return type(
            "FakeResponse",
            (),
            {
                "content": content,
                "choices": [
                    type(
                        "FakeChoice",
                        (),
                        {
                            "message": type(
                                "FakeMsg", (), {"content": content}
                            )(),
                            "finish_reason": "stop",
                        },
                    )
                ],
                "usage": {"total_tokens": 10},
            },
        )()

    monkeypatch.setattr(auxiliary_client, "call_llm", _fake_call_llm)


def _compute_state_dir() -> Path:
    """Return the round_tables state dir that BOTH ``open_round_table``
    and ``get_agent_opinion`` use.

    MUST match the path computed inside
    ``mcp_serve.get_agent_opinion`` (lines 758-765):

        get_hermes_home() / "agents" / ".runtime" / project_slug /
            "round_tables"

    If this diverges, ``get_agent_opinion`` returns 404
    ``round_not_found`` because the state file is at a different path
    than where it looks. The same SMOKE_PROJECT_SLUG MUST be passed to
    both ``open_round_table`` (as ``project_id``) and
    ``get_agent_opinion`` (as ``project_slug``).
    """
    from hermes_constants import get_hermes_home

    return (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / SMOKE_PROJECT_SLUG
        / "round_tables"
    )


# ── Test class ───────────────────────────────────────────────────────────────


class TestVisualExecutorSmoke:
    """SC#3 visual_executor round-table smoke.

    The mock-mode test is authoritative — it proves the full 3-step
    lifecycle (open -> opinion -> submit) works with the most complex
    agent (sub_steps expressed in persona text per Phase 62 Pitfall #2).

    The live-mode test is operator opt-in — it requires
    ``HERMES_PHASE63_LIVE_SMOKE=1`` AND ``GLM_API_KEY`` to be set, and
    is otherwise SKIPPED (never fails CI).
    """

    @pytest.mark.asyncio
    async def test_round_table_produces_nonempty_opinion(
        self, monkeypatch, tmp_path
    ):
        """SC#3 authoritative: mock LLM, verify visual_executor produces
        a non-empty opinion via the full round-table lifecycle.

        Lifecycle:
            1. Seed visual_executor + cinematographer YAMLs.
            2. Mock auxiliary_client.call_llm (Pitfall #3 — mandatory).
            3. open_round_table (status="open").
            4. await get_agent_opinion(agent_id="visual_executor").
            5. submit_round_table_result (status="completed").
            6. Read final state file; assert turns[-1]["opinion"] is a
               non-empty string.
        """
        from agent.round_table_state import (
            open_round_table,
            submit_round_table_result,
        )
        from mcp_serve import get_agent_opinion

        # 1. Stage YAMLs (Pitfall #4: BOTH agents for minItems=2).
        _seed_visual_executor_yamls(tmp_path)

        # 2. Mock LLM (Pitfall #3 — ALWAYS applied, never conditional).
        _mock_call_llm(monkeypatch)

        # 3. Open round table with a unique UUIDv4 round_id.
        round_id = str(uuid.uuid4())
        open_result = open_round_table(
            state_dir=_compute_state_dir(),
            round_id=round_id,
            project_id=SMOKE_PROJECT_SLUG,
            question=SMOKE_QUESTION,
            panelist_agent_ids=PANELIST_AGENT_IDS,
            caller="test_phase63_smoke",
        )
        assert open_result.get("roundId") == round_id, (
            f"open_round_table did not return roundId: {open_result}"
        )
        assert open_result.get("status") == "open", (
            f"open_round_table did not return status=open: {open_result}"
        )

        # 4. Get visual_executor's opinion. This appends a Turn to the
        # state file via append_turn (round_table_state.py:417). The
        # opinion field on the returned dict matches turns[-1]["opinion"]
        # in the state file.
        opinion_raw = await get_agent_opinion(
            round_id=round_id,
            project_slug=SMOKE_PROJECT_SLUG,
            agent_id="visual_executor",
            topic=SMOKE_QUESTION,
        )
        opinion_result = json.loads(opinion_raw)
        assert "error" not in opinion_result, (
            f"get_agent_opinion returned error: {opinion_result}"
        )
        assert opinion_result.get("status") == "ok"
        opinion_text = opinion_result.get("opinion", "")
        assert isinstance(opinion_text, str) and len(opinion_text) > 0, (
            f"opinion must be non-empty string, got: {opinion_text!r}"
        )

        # 5. Seal the round table (terminal transition).
        state_path = _compute_state_dir() / f"{round_id}.json"
        final = submit_round_table_result(
            state_path=state_path,
            conclusion="[TEST] visual_executor + cinematographer synthesis",
            cited_memories=[],
            closed_by="test_phase63_smoke",
        )
        assert final.get("status") == "completed", (
            f"submit did not complete: {final}"
        )

        # 6. Re-read state file from disk and assert the last turn's
        # opinion field is non-empty. Per round_table_state.py:417-437
        # (append_turn), the Turn shape is:
        #   {turnIndex, panelistId, opinion, citedMemoryIds, submittedAt}
        state_on_disk = json.loads(
            state_path.read_text(encoding="utf-8")
        )
        assert state_on_disk.get("status") == "completed"
        turns = state_on_disk.get("turns", [])
        assert len(turns) >= 1, (
            f"expected >=1 turn in state file, got {len(turns)}"
        )
        last_turn_opinion = turns[-1].get("opinion", "")
        assert isinstance(last_turn_opinion, str) and last_turn_opinion.strip(), (
            f"turns[-1].opinion must be non-empty, got: {last_turn_opinion!r}"
        )
        # Sanity: the opinion came from visual_executor (panelistId).
        assert turns[-1].get("panelistId") == "visual_executor", (
            f"expected panelistId=visual_executor, got: {turns[-1].get('panelistId')!r}"
        )

    @pytest.mark.skipif(
        not os.environ.get("HERMES_PHASE63_LIVE_SMOKE"),
        reason="live smoke opt-in via HERMES_PHASE63_LIVE_SMOKE=1",
    )
    @pytest.mark.asyncio
    async def test_live_round_table(self, monkeypatch, tmp_path):
        """OPTIONAL operator-confidence live GLM smoke.

        Requires BOTH ``HERMES_PHASE63_LIVE_SMOKE=1`` AND ``GLM_API_KEY``
        to be set. If either is missing, pytest.skip (never fails CI).

        Otherwise identical to the mock test, EXCEPT:
          - Real ``auxiliary_client.call_llm`` dispatch (no mock).
          - Additional keyword assertion: the opinion text contains
            ``drawer`` OR ``animator`` (proves the persona's sub_steps
            semantic was exercised by real GLM).
        """
        if "GLM_API_KEY" not in os.environ:
            pytest.skip(
                "GLM_API_KEY not set — operator must provide for live smoke"
            )

        from agent.round_table_state import (
            open_round_table,
            submit_round_table_result,
        )
        from mcp_serve import get_agent_opinion

        _seed_visual_executor_yamls(tmp_path)
        # NO _mock_call_llm — let real GLM dispatch happen.

        round_id = str(uuid.uuid4())
        open_result = open_round_table(
            state_dir=_compute_state_dir(),
            round_id=round_id,
            project_id=SMOKE_PROJECT_SLUG,
            question=SMOKE_QUESTION,
            panelist_agent_ids=PANELIST_AGENT_IDS,
            caller="test_phase63_smoke_live",
        )
        assert open_result.get("roundId") == round_id
        assert open_result.get("status") == "open"

        opinion_raw = await get_agent_opinion(
            round_id=round_id,
            project_slug=SMOKE_PROJECT_SLUG,
            agent_id="visual_executor",
            topic=SMOKE_QUESTION,
        )
        opinion_result = json.loads(opinion_raw)
        assert "error" not in opinion_result, (
            f"live get_agent_opinion returned error: {opinion_result}"
        )

        state_path = _compute_state_dir() / f"{round_id}.json"
        submit_round_table_result(
            state_path=state_path,
            conclusion="[LIVE] visual_executor + cinematographer synthesis",
            cited_memories=[],
            closed_by="test_phase63_smoke_live",
        )

        # Live-only: assert the persona's sub_steps semantic was
        # exercised by real GLM (proves the persona is robust enough
        # that GLM picks up the drawer/animator vocabulary).
        opinion_lower = opinion_result.get("opinion", "").lower()
        assert "drawer" in opinion_lower or "animator" in opinion_lower, (
            f"live opinion must mention drawer or animator sub_step, "
            f"got: {opinion_result.get('opinion', '')!r}"
        )

        state_on_disk = json.loads(
            state_path.read_text(encoding="utf-8")
        )
        assert state_on_disk.get("status") == "completed"
        turns = state_on_disk.get("turns", [])
        assert len(turns) >= 1
        assert turns[-1].get("opinion", "").strip()

    def test_open_round_table_idempotent_on_duplicate(self, tmp_path):
        """Idempotency sanity: calling open_round_table twice with the
        same round_id returns 409 Conflict on the second call.

        Proves the idempotent open contract from round_table_state.py:339
        — ``state_path.exists()`` guard short-circuits to a 409 dict
        instead of raising or overwriting.

        WR-05 fix (review): no _seed_visual_executor_yamls call here —
        open_round_table only writes the state file (round_table_state.py:404
        state_dir.mkdir), it does NOT read persona YAMLs. The seed was
        wasted I/O and introduced a hard dependency on Kai's home dir
        (per WR-01) for no functional reason. The state dir is created
        on-demand by open_round_table itself.
        """
        from agent.round_table_state import open_round_table

        round_id = str(uuid.uuid4())
        state_dir = _compute_state_dir()

        # First open — succeeds.
        first = open_round_table(
            state_dir=state_dir,
            round_id=round_id,
            project_id=SMOKE_PROJECT_SLUG,
            question=SMOKE_QUESTION,
            panelist_agent_ids=PANELIST_AGENT_IDS,
            caller="test_phase63_smoke_idempotency",
        )
        assert "roundId" in first, (
            f"first open should succeed, got: {first}"
        )
        assert first.get("status") == "open"

        # Second open — MUST return 409 round_already_open.
        second = open_round_table(
            state_dir=state_dir,
            round_id=round_id,
            project_id=SMOKE_PROJECT_SLUG,
            question=SMOKE_QUESTION,
            panelist_agent_ids=PANELIST_AGENT_IDS,
            caller="test_phase63_smoke_idempotency",
        )
        assert second.get("error") == "round_already_open", (
            f"second open should return round_already_open, got: {second}"
        )
        assert second.get("status") == 409, (
            f"second open should return status=409, got: {second}"
        )
