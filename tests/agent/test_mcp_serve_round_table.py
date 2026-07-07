"""Integration tests for the 7 v11.0 round-table MCP tools (Phase 52 INFRA-02).

These tests exercise the 7 ``@mcp.tool()`` closures registered inside
``create_mcp_server()``:

- ``agents_list`` — registry browse (delegates to ``registry_loader``)
- ``agent_describe`` — single-agent full YAML
- ``round_table_open`` — lifecycle step 1 (creates state file)
- ``get_agent_opinion`` — lifecycle step 2 (appends a placeholder Turn)
- ``submit_round_table_result`` — lifecycle step 3 (flips status=completed)
- ``memory_retrieve_scoped`` — Phase 53 stub
- ``memory_submit_record`` — Phase 53 stub

Acceptance contract coverage:

- **SC#1 (MCP half)** — ``agents_list`` returns the test-coordinator fixture.
- **SC#2** — full lifecycle round trip against a synthetic agent; final
  state file has ``status="completed"``.
- **INFRA-02** — all 7 tool names registered exactly per CONTEXT.md
  "Resolved by Kai" point 1 (NOT the stale ``02-ROUND-TABLE-PROTOCOL.md §5`` list).

Live-system guard mitigation (RESEARCH.md §"Pitfall 7")
-------------------------------------------------------
The autouse ``_live_system_guard`` fixture in ``tests/conftest.py:539`` AST-
inspects test functions for ``os.kill`` / ``subprocess.run`` patterns.
Calling ``create_mcp_server()`` is safe — it instantiates ``EventBridge()``
WITHOUT calling ``.start()`` (so no polling thread spawns, no SessionDB
I/O happens, no system calls fire). If the guard still trips, mark the
test with ``@pytest.mark.live_system_guard_bypass`` (last resort).

TDD note: this file is RED until Task 3 wires the 7 closures into
``create_mcp_server()``. The fixture defers ``create_mcp_server`` import
so collection succeeds before the closures exist; tests then fail because
the tool name is absent from the tool manager's ``_tools`` dict.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import pytest


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"
VALID_FIXTURE = FIXTURES_DIR / "test-coordinator.agent.yaml"


# ── Fixture: create_mcp_server with an un-started EventBridge ──────────────


@pytest.fixture
def mcp_server(monkeypatch, tmp_path):
    """Build a fresh ``FastMCP`` instance with the 7 round-table tools registered.

    Pre-setup:
    1. Redirect ``HERMES_HOME`` to a per-test subdir (the autouse
       ``_hermetic_environment`` already does this; we just stage agent
       YAMLs into the redirected home's ``agents/`` dir).
    2. Copy the test-coordinator fixture into ``agents/``.
    3. Instantiate ``EventBridge()`` WITHOUT calling ``.start()`` (so no
       background polling thread spawns, no live SessionDB I/O happens,
       no system calls trip the live-system guard).
    4. Call ``create_mcp_server(event_bridge=bridge)`` and return the
       ``FastMCP`` instance.
    """
    from hermes_constants import get_hermes_home
    from mcp_serve import create_mcp_server, EventBridge

    # Stage the test-coordinator fixture into the redirected HERMES_HOME
    agents_dir = get_hermes_home() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(VALID_FIXTURE, agents_dir / "test-coordinator.agent.yaml")

    # Force registry_loader to reload now that the fixture is in place
    try:
        from agent import registry_loader
        monkeypatch.setattr(registry_loader, "_REGISTRY_CACHE", None)
    except Exception:
        pass

    bridge = EventBridge()  # NOT started — safe for live-system guard
    server = create_mcp_server(event_bridge=bridge)
    return server


def _invoke(server, tool_name: str, **kwargs) -> dict[str, Any]:
    """Invoke a registered @mcp.tool() closure by name; return parsed JSON.

    Uses direct ``_tool_manager._tools[name].fn`` access which returns
    the closure's raw return value (a JSON string). Sync for sync tools,
    async for async tools — caller awaits if necessary.
    """
    tools = server._tool_manager._tools
    assert tool_name in tools, (
        f"Tool {tool_name!r} not registered. Available: {sorted(tools.keys())}"
    )
    return tools[tool_name].fn


async def _ainvoke(server, tool_name: str, **kwargs) -> dict[str, Any]:
    """Async variant of ``_invoke`` for ``async def`` MCP tools."""
    fn = _invoke(server, tool_name)
    raw = await fn(**kwargs)
    return json.loads(raw)


def _sinvoke(server, tool_name: str, **kwargs) -> dict[str, Any]:
    """Sync variant of ``_invoke`` for ``def`` (non-async) MCP tools."""
    fn = _invoke(server, tool_name)
    raw = fn(**kwargs)
    return json.loads(raw)


# ── Test class ─────────────────────────────────────────────────────────────


class TestMcpRoundTableIntegration:
    """INFRA-02 SC#1 (MCP half) + SC#2 (lifecycle) + memory stub invocation."""

    # ── SC#1: agents_list returns the staged fixture ──────────────────────

    def test_agents_list_returns_json(self, mcp_server):
        """SC#1 (MCP half): ``agents_list`` returns the test-coordinator fixture."""
        result = _sinvoke(mcp_server, "agents_list")
        assert result["count"] == 1, f"expected 1 agent, got {result}"
        agents = result["agents"]
        assert agents[0]["name"] == "test-coordinator"
        # Summary fields per CONTEXT.md tool spec
        assert "description" in agents[0]
        assert "version" in agents[0]
        assert "tags" in agents[0]

    def test_agents_list_with_tag_filter(self, mcp_server):
        """Tag filter narrows the list."""
        # test-coordinator has tag "test-fixture"
        matched = _sinvoke(mcp_server, "agents_list", tag="test-fixture")
        assert matched["count"] == 1
        unmatched = _sinvoke(mcp_server, "agents_list", tag="nonexistent-tag")
        assert unmatched["count"] == 0

    # ── agent_describe ────────────────────────────────────────────────────

    def test_agent_describe_returns_yaml(self, mcp_server):
        """``agent_describe`` returns the full agent dict (incl. persona)."""
        result = _sinvoke(mcp_server, "agent_describe", name="test-coordinator")
        assert "agent" in result, f"expected 'agent' key, got {result}"
        agent = result["agent"]
        assert agent["name"] == "test-coordinator"
        # Full persona must be present (broader than just summary)
        assert "persona" in agent, "agent_describe must return full persona"
        assert len(agent["persona"]) > 0

    def test_agent_describe_unknown_returns_404(self, mcp_server):
        """``agent_describe`` for a nonexistent agent returns a 404 error."""
        result = _sinvoke(mcp_server, "agent_describe", name="nonexistent")
        assert result.get("status") == 404
        assert result.get("error") == "agent_not_found"
        assert result.get("name") == "nonexistent"

    # ── WR-02 fix: typed registry_validation_failed responses ────────────

    def test_agents_list_returns_typed_400_on_malformed_fixture(self, monkeypatch, tmp_path):
        """WR-02: when registry_loader raises RegistryValidationError, the
        MCP closure returns a typed 400 ``registry_validation_failed``
        response with structured ``json_path`` + ``invalid_field`` instead
        of collapsing the schema violation into a generic 500 ``open_failed``.

        Test strategy: drop the existing ``malformed.agent.yaml`` fixture
        (which omits ``persona`` — surfaces at ``$.persona``) into the
        redirected HERMES_HOME, force-reload the registry, and assert the
        typed error response. The fixture is already shipped under
        ``tests/agent/fixtures/agents/``.
        """
        # Build a fresh server fixture with the malformed YAML staged in
        # — mirror the mcp_server fixture but ADD the malformed file.
        from hermes_constants import get_hermes_home
        from mcp_serve import create_mcp_server, EventBridge

        agents_dir = get_hermes_home() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VALID_FIXTURE, agents_dir / "test-coordinator.agent.yaml")
        shutil.copyfile(FIXTURES_DIR / "malformed.agent.yaml", agents_dir / "malformed.agent.yaml")

        # Force registry_loader to reload
        try:
            from agent import registry_loader
            monkeypatch.setattr(registry_loader, "_REGISTRY_CACHE", None)
        except Exception:
            pass

        bridge = EventBridge()
        server = create_mcp_server(event_bridge=bridge)

        result = _sinvoke(server, "agents_list")
        # WR-02 load-bearing assertions
        assert result.get("status") == 400, (
            f"expected 400 for malformed registry, got {result}"
        )
        assert result.get("error") == "registry_validation_failed", (
            f"expected error=registry_validation_failed, got {result.get('error')}"
        )
        # Structured fields (json_path + invalid_field) must be present so
        # callers don't have to regex the human-readable message.
        assert result.get("json_path") is not None, (
            "json_path MUST be present so callers can locate the schema violation"
        )
        assert result.get("invalid_field") is not None, (
            "invalid_field MUST be present so callers know which field failed"
        )
        # The malformed fixture omits persona — first sorted error cites $.persona
        assert "persona" in result.get("detail", ""), (
            f"expected persona citation in detail, got: {result.get('detail')}"
        )

    # ── memory stub invocation (Phase 53 placeholder) ─────────────────────

    @pytest.mark.asyncio
    async def test_memory_retrieve_scoped_stub_via_tool(self, mcp_server):
        """``memory_retrieve_scoped`` tool returns phase53_not_implemented stub."""
        result = await _ainvoke(
            mcp_server,
            "memory_retrieve_scoped",
            query="anything",
            agent_id="test-coordinator",
        )
        # The stub payload is documented in CONTEXT.md point 3
        assert result == {"status": "phase53_not_implemented", "hits": []}

    @pytest.mark.asyncio
    async def test_memory_submit_record_stub_via_tool(self, mcp_server):
        """``memory_submit_record`` tool returns phase53_not_implemented stub."""
        result = await _ainvoke(
            mcp_server,
            "memory_submit_record",
            agent_id="test-coordinator",
            content="a test memory",
        )
        assert result == {"status": "phase53_not_implemented", "record_id": None}

    # ── SC#2: lifecycle round trip ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_lifecycle_round_trip(self, mcp_server):
        """SC#2: round_table_open → get_agent_opinion → submit_round_table_result.

        Exercises the full lifecycle against a synthetic 2-panelist round
        table. Phase 52 returns a placeholder opinion (no real GLM call);
        Phase 53 will fill in the LLM dispatch.
        """
        from hermes_constants import get_hermes_home

        round_id = uuid.uuid4().hex
        project_slug = "test-slug"
        panelists = ["test-coordinator", "screenplay"]  # 2 panelists (minItems=2)

        # Step 1: open
        open_result = await _ainvoke(
            mcp_server,
            "round_table_open",
            round_id=round_id,
            project_slug=project_slug,
            question="What is the meaning of test?",
            panelist_agent_ids=panelists,
            caller="test-runner",
        )
        assert open_result["status"] == "open", f"open failed: {open_result}"
        assert open_result["roundId"] == round_id

        # Verify state file exists at the canonical path
        state_path = (
            get_hermes_home()
            / "agents"
            / ".runtime"
            / project_slug
            / "round_tables"
            / f"{round_id}.json"
        )
        assert state_path.exists(), f"state file not created at {state_path}"

        # Step 2: get_agent_opinion (Phase 52 returns placeholder)
        opinion_result = await _ainvoke(
            mcp_server,
            "get_agent_opinion",
            round_id=round_id,
            project_slug=project_slug,
            agent_id="test-coordinator",
            topic="Meaning of test",
        )
        assert opinion_result["status"] == "ok", f"opinion failed: {opinion_result}"
        assert opinion_result["opinion"] == "[phase52_placeholder]"
        assert opinion_result["agent_id"] == "test-coordinator"

        # Step 3: submit result — terminal transition
        submit_result = await _ainvoke(
            mcp_server,
            "submit_round_table_result",
            round_id=round_id,
            project_slug=project_slug,
            conclusion="Test conclusion.",
            cited_memories=[],
            closed_by="test-runner",
        )
        assert submit_result["status"] == "completed", (
            f"submit failed: {submit_result}"
        )

        # SC#2 contract: final state file has status="completed"
        with open(state_path, encoding="utf-8") as f:
            final_state = json.load(f)
        assert final_state["status"] == "completed", (
            f"final state not completed: {final_state['status']}"
        )
        # SC#2 atomicity: NEVER see status=in_progress (not in schema enum)
        assert final_state["status"] != "in_progress"
        assert "submitRoundTableResult" in final_state

    @pytest.mark.asyncio
    async def test_round_table_open_rejects_too_few_panelists(self, mcp_server):
        """Schema minItems=2 enforcement at open-time."""
        result = await _ainvoke(
            mcp_server,
            "round_table_open",
            round_id=uuid.uuid4().hex,
            project_slug="test-slug",
            question="Q?",
            panelist_agent_ids=["only-one"],  # minItems=2 violation
            caller="test-runner",
        )
        assert result.get("status") == 400
        assert result.get("error") == "panelists_min_2_required"

    @pytest.mark.asyncio
    async def test_round_table_open_rejects_bad_project_slug(self, mcp_server):
        """T-52-09 mitigation: path-traversal protection on project_slug."""
        # `..` substring must be rejected
        result = await _ainvoke(
            mcp_server,
            "round_table_open",
            round_id=uuid.uuid4().hex,
            project_slug="../etc/passwd",  # path traversal attempt
            question="Q?",
            panelist_agent_ids=["a", "b"],
            caller="test-runner",
        )
        assert result.get("status") == 400
        assert result.get("error") == "invalid_project_slug"

    # ── CR-01 fix: path-traversal rejection on round_id (3 closures) ──────

    @pytest.mark.asyncio
    async def test_round_table_open_rejects_path_traversal_round_id(self, mcp_server):
        """CR-01: ``round_table_open`` MUST reject path-traversal round_id.

        Without this guard, a malicious MCP client could pass
        ``round_id="../../etc/passwd"`` and cause ``open_round_table`` to
        create arbitrary directories + files under ``~/.hermes/``.
        """
        result = await _ainvoke(
            mcp_server,
            "round_table_open",
            round_id="../../etc/passwd",  # path traversal attempt
            project_slug="test-slug",
            question="Q?",
            panelist_agent_ids=["a", "b"],
            caller="test-runner",
        )
        assert result.get("status") == 400
        assert result.get("error") == "invalid_round_id"

    @pytest.mark.asyncio
    async def test_get_agent_opinion_rejects_path_traversal_round_id(self, mcp_server):
        """CR-01: ``get_agent_opinion`` MUST reject path-traversal round_id.

        ``get_agent_opinion`` builds ``state_path`` from the unvalidated
        ``round_id`` parameter; without validation it would read arbitrary
        files (information disclosure via the JSON decode error path).
        """
        result = await _ainvoke(
            mcp_server,
            "get_agent_opinion",
            round_id="../../etc/passwd",  # path traversal attempt
            project_slug="test-slug",
            agent_id="test-coordinator",
            topic="anything",
        )
        assert result.get("status") == 400
        assert result.get("error") == "invalid_round_id"

    @pytest.mark.asyncio
    async def test_submit_round_table_result_rejects_path_traversal_round_id(self, mcp_server):
        """CR-01: ``submit_round_table_result`` MUST reject path-traversal round_id.

        ``submit_round_table_result`` builds ``state_path`` from the
        unvalidated ``round_id`` parameter; without validation it would
        read + atomic-write arbitrary paths (worst case: arbitrary file
        creation via atomic_json_write's mkdir(parents=True)).
        """
        result = await _ainvoke(
            mcp_server,
            "submit_round_table_result",
            round_id="../../etc/passwd",  # path traversal attempt
            project_slug="test-slug",
            conclusion="done",
            cited_memories=[],
            closed_by="test-runner",
        )
        assert result.get("status") == 400
        assert result.get("error") == "invalid_round_id"

    @pytest.mark.asyncio
    async def test_round_table_open_rejects_non_uuid_round_id(self, mcp_server):
        """CR-01: round_id MUST be UUID-shaped (32 hex or 8-4-4-4-12).

        The ``round_table_open`` docstring promises "CC-generated UUID v4";
        this test guards against the lax pattern drifting back to a permissive
        regex that would weaken the path-traversal defense.
        """
        result = await _ainvoke(
            mcp_server,
            "round_table_open",
            round_id="not-a-uuid",  # not UUID v4 hex / canonical
            project_slug="test-slug",
            question="Q?",
            panelist_agent_ids=["a", "b"],
            caller="test-runner",
        )
        assert result.get("status") == 400
        assert result.get("error") == "invalid_round_id"

    @pytest.mark.asyncio
    async def test_submit_round_table_result_idempotent(self, mcp_server):
        """Second submit on a completed round returns 409 Conflict."""
        round_id = uuid.uuid4().hex
        # Open
        open_r = await _ainvoke(
            mcp_server, "round_table_open",
            round_id=round_id, project_slug="test-slug",
            question="Q?", panelist_agent_ids=["a", "b"], caller="t",
        )
        assert open_r["status"] == "open"
        # Submit once
        sub1 = await _ainvoke(
            mcp_server, "submit_round_table_result",
            round_id=round_id, project_slug="test-slug",
            conclusion="done", cited_memories=[], closed_by="t",
        )
        assert sub1["status"] == "completed"
        # Submit again — should get 409 round_not_open
        sub2 = await _ainvoke(
            mcp_server, "submit_round_table_result",
            round_id=round_id, project_slug="test-slug",
            conclusion="dup", cited_memories=[], closed_by="t",
        )
        assert sub2.get("status") == 409
        assert sub2.get("error") == "round_not_open"


# ── Serial enforcement (INFRA-04 / SC#4) via MCP tool surface ──────────────


class TestSerialEnforcementMcpIntegration:
    """SC#4 integration: concurrent ``get_agent_opinion`` for the same
    ``roundId`` is rejected with 429 + MEMORY.md citation when routed
    through the MCP tool surface (not just at the lock-primitive level).

    These tests complement ``tests/agent/test_round_table_executor.py``
    (which exercises ``acquire_round_or_reject`` directly) by verifying
    the lock is correctly wired INSIDE the ``get_agent_opinion`` closure.
    """

    @pytest.mark.asyncio
    async def test_concurrent_get_agent_opinion_rejected_with_429(self, mcp_server):
        """SC#4: when the per-roundId lock is already held, the MCP
        ``get_agent_opinion`` tool returns the 429 serial-violation
        response citing ``feedback-glm-overload-reduce-concurrency.md``.

        Test strategy: pre-acquire the lock via the public
        ``acquire_round_or_reject`` API (deterministic — guarantees the
        MCP tool call sees a held lock on its very first line). Then
        invoke ``get_agent_opinion`` and verify the rejection response.
        Release the lock at the end so the registry is clean for
        subsequent tests.
        """
        from agent.round_table_executor import (
            acquire_round_or_reject,
            release_round_lock,
        )

        # Open a fresh round table so the MCP tool would otherwise succeed.
        round_id = uuid.uuid4().hex
        project_slug = "test-slug"
        open_r = await _ainvoke(
            mcp_server, "round_table_open",
            round_id=round_id, project_slug=project_slug,
            question="Concurrent test?",
            panelist_agent_ids=["test-coordinator", "screenplay"],
            caller="test-runner",
        )
        assert open_r["status"] == "open"

        # Pre-acquire the per-roundId lock so the MCP tool call sees a
        # held lock on its very first line (deterministic race avoidance).
        held_lock = await acquire_round_or_reject(round_id)
        assert held_lock is not None, "test setup: pre-acquire must succeed"

        try:
            # Now invoke the MCP tool — must hit the rejection path
            # before any state file mutation.
            result = await _ainvoke(
                mcp_server, "get_agent_opinion",
                round_id=round_id, project_slug=project_slug,
                agent_id="test-coordinator", topic="concurrent test",
            )

            # SC#4 load-bearing assertions
            assert result.get("error") == "serial_violation", (
                f"expected serial_violation, got {result}"
            )
            assert result.get("status") == 429, (
                f"expected status=429, got {result}"
            )
            # Literal MEMORY.md policy citation — load-bearing per SC#4
            message = result.get("message", "")
            assert "feedback-glm-overload-reduce-concurrency.md" in message, (
                f"429 message must cite MEMORY.md policy file; got: {message}"
            )
        finally:
            # Cleanup so subsequent tests see a clean lock registry.
            await release_round_lock(round_id)

    @pytest.mark.asyncio
    async def test_get_agent_opinion_happy_path_unaffected_by_lock(self, mcp_server):
        """Regression: lock wiring must NOT break the happy path.

        The ``test_lifecycle_round_trip`` test in ``TestMcpRoundTableIntegration``
        already exercises ``get_agent_opinion`` end-to-end, so this test
        is technically redundant — but locking changes are subtle enough
        to warrant a focused regression that calls ``get_agent_opinion``
        once and confirms the response still reports ``status: ok`` with
        the placeholder opinion intact.
        """
        round_id = uuid.uuid4().hex
        project_slug = "test-slug"
        open_r = await _ainvoke(
            mcp_server, "round_table_open",
            round_id=round_id, project_slug=project_slug,
            question="Happy path?",
            panelist_agent_ids=["test-coordinator", "screenplay"],
            caller="test-runner",
        )
        assert open_r["status"] == "open"

        opinion_r = await _ainvoke(
            mcp_server, "get_agent_opinion",
            round_id=round_id, project_slug=project_slug,
            agent_id="test-coordinator", topic="happy path",
        )
        assert opinion_r["status"] == "ok", f"happy path broken: {opinion_r}"
        assert opinion_r["opinion"] == "[phase52_placeholder]"


# ── Tool registration census — guard against name drift ────────────────────


class TestToolRegistrationCensus:
    """INFRA-02 acceptance: all 7 v11.0 tool names registered exactly.

    The list is LOCKED by CONTEXT.md "Resolved by Kai" point 1. It
    intentionally diverges from the stale ``02-ROUND-TABLE-PROTOCOL.md §5``
    list — that divergence is by design and this test guards against
    accidental reversion.
    """

    EXPECTED_V11_TOOLS = {
        "round_table_open",
        "submit_round_table_result",
        "get_agent_opinion",
        "agents_list",
        "agent_describe",
        "memory_retrieve_scoped",
        "memory_submit_record",
    }

    def test_all_seven_v11_tools_registered(self, mcp_server):
        """The 7 v11.0 round-table tools must all be registered."""
        registered = set(mcp_server._tool_manager._tools.keys())
        missing = self.EXPECTED_V11_TOOLS - registered
        assert not missing, (
            f"Missing v11.0 MCP tools: {sorted(missing)}. "
            f"Registered: {sorted(registered)}"
        )

    def test_no_v10_stale_names_substituted(self, mcp_server):
        """Guard against accidental reversion to 02-ROUND-TABLE-PROTOCOL.md §5 names.

        Those names (get_agent_persona / get_agent_memory / submit_artifact /
        query_memory / run_python_phase) are NOT in the v11.0 PoC scope per
        CONTEXT.md "Resolved by Kai" point 1. Their presence would indicate
        the implementation followed the wrong design source.
        """
        registered = set(mcp_server._tool_manager._tools.keys())
        stale_v10_names = {
            "get_agent_persona",
            "get_agent_memory",
            "submit_artifact",
            "query_memory",
            "run_python_phase",
        }
        overlap = stale_v10_names & registered
        assert not overlap, (
            f"Stale v10.0 tool names registered (should NOT be): "
            f"{sorted(overlap)}. See CONTEXT.md point 1 — v11.0 PoC uses a "
            f"different (narrower) tool set than 02-ROUND-TABLE-PROTOCOL.md §5."
        )

    def test_total_tool_count_is_seventeen(self, mcp_server):
        """Existing 10 messaging tools + 7 new v11.0 tools = 17 total.

        Note: the plan / CONTEXT.md said "9 existing" but the actual
        pre-Phase-52 count is 10 (the plan omitted ``attachments_fetch``
        from its informal census). Verified by enumerating the registered
        tool set before adding any v11.0 closures.
        """
        registered = set(mcp_server._tool_manager._tools.keys())
        assert len(registered) == 17, (
            f"Expected 17 tools (10 messaging + 7 v11.0), got {len(registered)}: "
            f"{sorted(registered)}"
        )
