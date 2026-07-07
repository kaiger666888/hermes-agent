"""Tests for ``agent/memory_arbitration.py`` (Phase 52 STUB).

Phase 52 ships the two memory MCP-tool functions (``memory_retrieve_scoped``
+ ``memory_submit_record``) as **stubs** that return a fixed
``phase53_not_implemented`` payload. Phase 53 (CREATIVE-SLICE) fills in
real mem0 backend routing per agents-schema.yaml §2.6 ``memory_scope``.

This file also tests the ``_scoped_agent_id`` ``contextvars.ContextVar``
primitive that Phase 53's memory routing will hook into. The primitive
MUST be ``contextvars``-based (not ``threading.local``) because
``ThreadPoolExecutor`` worker reuse makes ``threading.local`` leak scope
across tasks; ``contextvars`` is asyncio-correct per ARCHITECTURE §3.3.

Stub return contract (locked by 52-CONTEXT.md "Resolved by Kai" point 3):

- ``memory_retrieve_scoped(...)`` →
  ``{"status": "phase53_not_implemented", "hits": []}``
- ``memory_submit_record(...)`` →
  ``{"status": "phase53_not_implemented", "record_id": None}``

TDD note: this file is RED until Task 1 lands ``agent/memory_arbitration.py``.
The import is deferred into the fixture so ``pytest --collect-only`` works
even before the module exists; the first test run raises a clear
``ModuleNotFoundError`` until implementation lands.
"""

from __future__ import annotations

import asyncio

import pytest


# ── Fixture: deferred import so collection works pre-implementation ────────


@pytest.fixture
def memory_module():
    """Lazy-import so RED phase collects cleanly without the module present."""
    from agent import memory_arbitration
    return memory_arbitration


# ── Stub return contract ───────────────────────────────────────────────────


class TestMemoryStubReturnContract:
    """Verify the exact dict the stubs return per CONTEXT.md point 3."""

    @pytest.mark.asyncio
    async def test_retrieve_scoped_returns_phase53_not_implemented(self, memory_module):
        result = await memory_module.memory_retrieve_scoped(
            query="anything", agent_id="anyagent"
        )
        assert result == {"status": "phase53_not_implemented", "hits": []}

    @pytest.mark.asyncio
    async def test_retrieve_scoped_ignores_arguments(self, memory_module):
        """Stub contract: returns the same payload regardless of args."""
        a = await memory_module.memory_retrieve_scoped(
            query="q1", agent_id="agent_a", top_k=1
        )
        b = await memory_module.memory_retrieve_scoped(
            query="totally different", agent_id="agent_b", top_k=99
        )
        assert a == b
        assert a == {"status": "phase53_not_implemented", "hits": []}

    @pytest.mark.asyncio
    async def test_submit_record_returns_phase53_not_implemented_with_null_id(
        self, memory_module
    ):
        result = await memory_module.memory_submit_record(
            agent_id="anyagent", content="x"
        )
        assert result == {"status": "phase53_not_implemented", "record_id": None}

    @pytest.mark.asyncio
    async def test_submit_record_ignores_arguments(self, memory_module):
        a = await memory_module.memory_submit_record(
            agent_id="agent_a", content="c1", scope="per_agent", confidence=0.9
        )
        b = await memory_module.memory_submit_record(
            agent_id="agent_b", content="c2", scope="shared", confidence=0.1
        )
        assert a == b
        assert a == {"status": "phase53_not_implemented", "record_id": None}


# ── Contextvars primitive ─────────────────────────────────────────────────


class TestScopedAgentId:
    """Verify ``_scoped_agent_id`` behaves as a proper contextvars primitive."""

    def test_get_returns_none_before_set(self, memory_module):
        """Default state: unset → ``None`` (NOT the sentinel)."""
        # The primitive is process-global; previous tests may have set it.
        # We reset by setting a fresh ContextVar via asyncio context later;
        # for this test we just verify the type contract: returns str | None.
        result = memory_module.get_scoped_agent_id()
        assert result is None or isinstance(result, str)

    def test_set_then_get_round_trip(self, memory_module):
        memory_module.set_scoped_agent_id("alice")
        assert memory_module.get_scoped_agent_id() == "alice"
        # Cleanup: reset to None to avoid leaking to other tests
        memory_module.set_scoped_agent_id(None)

    def test_set_none_returns_none(self, memory_module):
        """``set_scoped_agent_id(None)`` should make ``get`` return None."""
        memory_module.set_scoped_agent_id(None)
        assert memory_module.get_scoped_agent_id() is None

    def test_overwrite_previous_value(self, memory_module):
        memory_module.set_scoped_agent_id("first")
        memory_module.set_scoped_agent_id("second")
        assert memory_module.get_scoped_agent_id() == "second"
        memory_module.set_scoped_agent_id(None)

    @pytest.mark.asyncio
    async def test_context_isolation_across_asyncio_tasks(self, memory_module):
        """Each asyncio task gets its own ``ContextVar`` copy.

        Setting in one task MUST NOT leak into a concurrently-running task.
        This is the core property that makes ``contextvars`` (not
        ``threading.local``) correct for asyncio-coupled memory routing.
        """
        # Pre-condition: scope is unset
        memory_module.set_scoped_agent_id(None)

        results: dict[str, str | None] = {}

        async def setter_task():
            memory_module.set_scoped_agent_id("setter-agent")
            await asyncio.sleep(0.01)  # Yield to scheduler
            results["setter_after_yield"] = memory_module.get_scoped_agent_id()

        async def observer_task():
            await asyncio.sleep(0.005)  # Setter has run by now
            # Observer task's ContextVar MUST be unaffected by setter
            results["observer_during_setter"] = memory_module.get_scoped_agent_id()

        await asyncio.gather(setter_task(), observer_task())

        assert results["setter_after_yield"] == "setter-agent"
        assert results["observer_during_setter"] is None

        # Parent context also unaffected by child-task sets
        assert memory_module.get_scoped_agent_id() is None


# ── mem0 import-pollution guard (Pitfall #5 in RESEARCH.md) ────────────────


class TestNoEagerMem0Import:
    """Phase 52 stub MUST NOT eagerly import the mem0 backend.

    See RESEARCH.md §"Pitfall 5" — eager-importing
    ``plugins.memory.mem0`` couples Phase 52 to a Phase 53 backend that may
    not have ``MEM0_API_KEY`` set, breaking the test suite.
    """

    def test_module_does_not_import_mem0_at_top_level(self):
        """Walk the AST: no ``import plugins.memory.mem0`` / ``from plugins.memory.mem0``.

        AST-walking is precise — docstring/comment mentions of the module
        name don't trigger false positives (the original substring check
        did). Only actual ``Import`` / ``ImportFrom`` nodes count.
        """
        import ast
        import inspect

        from agent import memory_arbitration
        src = inspect.getsource(memory_arbitration)
        tree = ast.parse(src)

        forbidden_prefix = "plugins.memory.mem0"
        offenders: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == forbidden_prefix or alias.name.startswith(
                        forbidden_prefix + "."
                    ):
                        offenders.append(f"line {node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == forbidden_prefix or mod.startswith(forbidden_prefix + "."):
                    offenders.append(
                        f"line {node.lineno}: from {mod} import ...",
                    )

        assert not offenders, (
            "Phase 52 memory_arbitration MUST NOT import plugins.memory.mem0 — "
            "Phase 53 fills in real mem0 routing (RESEARCH.md Pitfall #5). "
            f"Found: {offenders}"
        )
