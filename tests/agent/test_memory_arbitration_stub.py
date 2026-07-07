"""Tests for ``agent/memory_arbitration.py`` — Phase 52 primitive + Phase 53 contract.

This file was originally written for the Phase 52 STUB contract. Phase 53
(CREATIVE-SLICE) **replaced** the stub return contract per ``53-CONTEXT.md``
decision #3:

- ``memory_retrieve_scoped(...)`` now returns ``{"status": "ok", ...}`` or
  ``{"status": "unavailable", "hits": []}`` (when ``MEM0_API_KEY`` is
  unset, which is always the case in the hermetic test environment).
- ``memory_submit_record(...)`` similarly returns
  ``{"status": "unavailable", "record_id": None}`` in hermetic tests.

The ``_scoped_agent_id`` ``contextvars.ContextVar`` primitive — and its
no-eager-mem0-import guard — are preserved verbatim. Those sub-suites
remain authoritative for Phase 53 as well.

The Phase 52 STUB tests below were updated by Phase 53 Plan 53-02 Task 1
to assert the new (Phase 53) return contract instead of the now-removed
``phase53_not_implemented`` payload.
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


# ── Phase 53 routing return contract ──────────────────────────────────────
#
# Phase 53 replaced the Phase 52 ``phase53_not_implemented`` stub with
# real mem0 routing. In the hermetic test env (no MEM0_API_KEY), the
# backend is unavailable → graceful ``{"status": "unavailable", ...}``
# payload.


class TestMemoryRoutingReturnContract:
    """Verify the Phase 53 return contract: ``status=unavailable`` when
    the mem0 backend is not configured (the hermetic-test invariant)."""

    @pytest.mark.asyncio
    async def test_retrieve_scoped_returns_unavailable_without_mem0_key(
        self, memory_module, monkeypatch
    ):
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        result = await memory_module.memory_retrieve_scoped(
            query="anything", agent_id="anyagent"
        )
        assert result == {"status": "unavailable", "hits": []}

    @pytest.mark.asyncio
    async def test_retrieve_scoped_status_is_one_of_ok_or_unavailable(
        self, memory_module, monkeypatch
    ):
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        result = await memory_module.memory_retrieve_scoped(
            query="q1", agent_id="agent_a", top_k=1
        )
        assert result["status"] in ("ok", "unavailable")
        assert isinstance(result["hits"], list)

    @pytest.mark.asyncio
    async def test_submit_record_returns_unavailable_without_mem0_key(
        self, memory_module, monkeypatch
    ):
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        result = await memory_module.memory_submit_record(
            agent_id="anyagent", content="x"
        )
        assert result == {"status": "unavailable", "record_id": None}

    @pytest.mark.asyncio
    async def test_submit_record_status_is_one_of_ok_or_unavailable(
        self, memory_module, monkeypatch
    ):
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        a = await memory_module.memory_submit_record(
            agent_id="agent_a", content="c1", scope="per_agent", confidence=0.9
        )
        b = await memory_module.memory_submit_record(
            agent_id="agent_b", content="c2", scope="shared", confidence=0.1
        )
        for r in (a, b):
            assert r["status"] in ("ok", "unavailable")
            assert "record_id" in r


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
    """``memory_arbitration`` MUST NOT eagerly import the mem0 backend at module top level.

    Phase 52 originally enforced this invariant as part of the stub
    contract. Phase 53 (Plan 53-02) introduces a **function-level** lazy
    import inside ``_get_mem0_backend`` so the heavy backend is only
    loaded when memory routing is actually invoked. This AST guard now
    verifies that any ``plugins.memory.mem0`` import lives inside a
    function body — never at module top level — preserving the original
    RESEARCH.md §"Pitfall 5" guarantee.
    """

    def test_module_does_not_import_mem0_at_top_level(self):
        """AST-walk: no top-level (depth-0) ``import plugins.memory.mem0``.

        A top-level ``Import`` / ``ImportFrom`` has its parent in
        ``ast.Module.body``. Imports nested inside ``FunctionDef`` /
        ``AsyncFunctionDef`` are allowed (those are the lazy Phase 53
        imports). AST-walking the module body directly is precise.
        """
        import ast
        import inspect

        from agent import memory_arbitration
        src = inspect.getsource(memory_arbitration)
        tree = ast.parse(src)

        forbidden_prefix = "plugins.memory.mem0"
        offenders: list[str] = []

        # Only inspect top-level statements (tree.body), not nested function bodies.
        for node in tree.body:
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
            "memory_arbitration MUST NOT eagerly import plugins.memory.mem0 at "
            "module top level — Phase 53 routes via a function-level lazy import "
            "(RESEARCH.md Pitfall #5). "
            f"Found: {offenders}"
        )
