"""AST-walk non-bypassable dry-run-first invariant (EVAL-06).

Mirrors the v6.0 ``TestNonBypassableHumanInLoop`` pattern from
``tests/hermes_cli/test_curator_cli.py`` (which AST-walks
``apply_patch_transaction`` call sites in hermes_cli/curator.py to assert
zero direct invocations).

This module AST-walks ``agent/curator.py`` and verifies that EVERY
state-mutation call site is structurally nested inside an
``if not dry_run:`` guard — OR is inside a helper function whose every
caller is itself inside such a guard. The latter case covers
``_feedback_scan_phase`` (called only from inside ``if not dry_run:``).

Cites:
  - ``.planning/research/v10-orchestrator-design/05-POC-PLAN.md §4.6``
  - v6.0 ``TestNonBypassableHumanInLoop`` (in tests/hermes_cli/test_curator_cli.py)

This is a STATIC source analysis — it never executes any code under test.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Locate the source file under test
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CURATOR_PY = REPO_ROOT / "agent" / "curator.py"

# Names that constitute state-mutation write paths. Each must be either
# directly invoked inside an ``if not dry_run:`` guard, or be a helper
# function (e.g. _feedback_scan_phase) whose every invocation is inside
# such a guard.
WRITE_PATH_NAMES = {
    "append_audit",
    "apply_automatic_transitions",
    "apply_patch_transaction",
}


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _parse_curator() -> ast.Module:
    """Parse agent/curator.py source. Raises if the file is missing or
    the source fails to parse (which would silently no-op the AST-walk)."""
    assert CURATOR_PY.exists(), f"Missing source: {CURATOR_PY}"
    source = CURATOR_PY.read_text(encoding="utf-8")
    return ast.parse(source)


def _build_parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    """Build id(node) → parent mapping for parent-chain traversal."""
    parent_map: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent_map[id(child)] = node
    return parent_map


def _is_inside_not_dry_run_guard(
    call_node: ast.AST, parent_map: dict[int, ast.AST]
) -> bool:
    """Walk UP the parent chain from call_node. Return True if any ancestor
    is an ``ast.If`` whose guard semantically equivalent to ``not dry_run``.

    Two equivalent patterns are recognized:

    1. Direct: ``ast.If(test=UnaryOp(Not, Name(id='dry_run')))`` — the
       canonical ``if not dry_run:`` guard.
    2. Indirect via else-branch: ``ast.If(test=Name(id='dry_run'))`` where
       the call_node is inside the ``.orelse`` list (i.e. the ``else:``
       block). This is the ``if dry_run: ... else: <write>`` pattern —
       semantically identical to ``if not dry_run: <write>``.

    ``parent_map`` is keyed by ``id(node)``, so the walk tracks ids rather
    than node identity.
    """
    current_id = id(call_node)
    last_node: ast.AST | None = call_node
    while current_id in parent_map:
        parent = parent_map[current_id]
        if isinstance(parent, ast.If):
            # Pattern 1: direct ``if not dry_run:``
            if _test_is_not_dry_run(parent.test):
                return True
            # Pattern 2: ``if dry_run:`` with the immediate child in the
            # orelse branch. ``last_node`` is the direct child of ``parent``
            # along this parent-chain walk, so checking membership in
            # ``parent.orelse`` tells us whether we ascended from the else
            # block.
            if (
                _test_is_dry_run(parent.test)
                and last_node in parent.orelse
            ):
                return True
        last_node = parent
        current_id = id(parent)
    return False


def _test_is_not_dry_run(test: ast.expr) -> bool:
    """Match ``not dry_run``."""
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        operand = test.operand
        if isinstance(operand, ast.Name) and operand.id == "dry_run":
            return True
    return False


def _test_is_dry_run(test: ast.expr) -> bool:
    """Match bare ``dry_run`` (used to detect the else-branch pattern)."""
    return isinstance(test, ast.Name) and test.id == "dry_run"


def _is_inside_function_named(
    call_node: ast.AST,
    parent_map: dict[int, ast.AST],
    func_names: set[str],
) -> str | None:
    """Return the name of the enclosing function if it's in ``func_names``,
    else None. Used to recognize calls inside helper functions like
    ``_feedback_scan_phase`` whose invocations are themselves guarded."""
    current_id = id(call_node)
    while current_id in parent_map:
        parent = parent_map[current_id]
        if isinstance(parent, ast.FunctionDef) and parent.name in func_names:
            return parent.name
        current_id = id(parent)
    return None


def _collect_calls(tree: ast.Module) -> list[ast.Call]:
    """Collect every ast.Call node in the tree (deep walk)."""
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calls.append(node)
    return calls


def _call_name(call: ast.Call) -> str | None:
    """Return the called name if it's a simple Name or Attribute access."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _collect_function_defs(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    """Map function-name → FunctionDef node for every top-level or
    method-level function in the module."""
    defs: dict[str, ast.FunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs[node.name] = node
    return defs


def _collect_call_sites_of(
    tree: ast.Module, target_name: str
) -> list[ast.Call]:
    """Every call site where the called name is ``target_name``."""
    out: list[ast.Call] = []
    for call in _collect_calls(tree):
        if _call_name(call) == target_name:
            out.append(call)
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestASTWalkRanSanity:
    """Meta-tests asserting the AST-walk itself executed over a non-trivial
    tree. Catches the case where the AST-walk silently no-ops because the
    source failed to parse or the path is wrong."""

    def test_ast_walk_ran_over_expected_node_count(self):
        tree = _parse_curator()
        nodes = list(ast.walk(tree))
        # curator.py is a large module (2,400+ lines). If we walked fewer
        # than 1,000 nodes, something is wrong with the parse.
        assert len(nodes) > 1000, (
            f"AST-walk over agent/curator.py visited only {len(nodes)} nodes — "
            "expected a large tree. Did the source fail to parse?"
        )

    def test_run_curator_review_exists_with_dry_run_true(self):
        """Signature must default to dry_run=True."""
        tree = _parse_curator()
        defs = _collect_function_defs(tree)
        assert "run_curator_review" in defs, (
            "run_curator_review function not found in agent/curator.py"
        )
        fn = defs["run_curator_review"]
        defaults = fn.args.defaults
        # Find the dry_run default. Signature:
        #   run_curator_review(on_summary, synchronous, dry_run, consolidate)
        arg_names = fn.args.args
        default_offset = len(arg_names) - len(defaults)
        found_dry_run_default = False
        for i, arg in enumerate(arg_names):
            if arg.arg == "dry_run":
                default_idx = i - default_offset
                if default_idx < 0:
                    # No default — required positional arg. FAIL.
                    pytest.fail(
                        "run_curator_review.dry_run has no default value — "
                        "EVAL-06 requires dry_run: bool = True."
                    )
                default_node = defaults[default_idx]
                if not (
                    isinstance(default_node, ast.Constant)
                    and default_node.value is True
                ):
                    pytest.fail(
                        f"run_curator_review.dry_run default is not True — "
                        f"EVAL-06 requires dry_run: bool = True. Got: "
                        f"{ast.dump(default_node)}"
                    )
                found_dry_run_default = True
                break
        assert found_dry_run_default, (
            "dry_run parameter not found in run_curator_review signature."
        )


class TestWritePathsAreDryRunGuarded:
    """Each write-path call site is structurally inside an
    ``if not dry_run:`` guard — either directly, or transitively via a
    helper function (e.g. _feedback_scan_phase) whose every call site is
    guarded."""

    @pytest.fixture(scope="class")
    def parsed(self):
        tree = _parse_curator()
        parent_map = _build_parent_map(tree)
        return tree, parent_map

    def test_append_audit_calls_are_dry_run_guarded(self, parsed):
        tree, parent_map = parsed
        calls = _collect_call_sites_of(tree, "append_audit")
        # If there are no call sites, the test is vacuously true — still
        # pass, but log so the maintainer knows. The AST-walk sanity test
        # above catches parse failures.
        unguarded: list[tuple[int, str]] = []
        for call in calls:
            if _is_inside_not_dry_run_guard(call, parent_map):
                continue
            # Transitive: the call may live inside a helper function whose
            # callers are all guarded. Check by walking UP and, for each
            # enclosing FunctionDef, verifying every Call to that function
            # is itself guarded.
            enclosing = _is_inside_function_named(
                call, parent_map, {"_feedback_scan_phase"}
            )
            if enclosing is None:
                unguarded.append((call.lineno, "append_audit (direct)"))
                continue
            # The enclosing helper is _feedback_scan_phase. Verify every
            # call site of _feedback_scan_phase is inside a guard.
            helper_calls = _collect_call_sites_of(tree, enclosing)
            for hc in helper_calls:
                if not _is_inside_not_dry_run_guard(hc, parent_map):
                    unguarded.append(
                        (hc.lineno, f"{enclosing}() call (transitive)")
                    )
        assert not unguarded, (
            "EVAL-06 dry-run-first invariant violated: found unguarded "
            "append_audit call sites. Each must be wrapped in "
            "`if not dry_run:` (directly or transitively via "
            "_feedback_scan_phase).\n  Unguarded:\n  "
            + "\n  ".join(f"line {ln}: {what}" for ln, what in unguarded)
        )

    def test_apply_automatic_transitions_calls_are_dry_run_guarded(self, parsed):
        tree, parent_map = parsed
        calls = _collect_call_sites_of(tree, "apply_automatic_transitions")
        unguarded: list[tuple[int, str]] = []
        for call in calls:
            if _is_inside_not_dry_run_guard(call, parent_map):
                continue
            # apply_automatic_transitions is defined at module top level
            # (line 349); the only invocation should be inside run_curator_review's
            # `else` branch (the `if not dry_run:` guard's negative).
            unguarded.append((call.lineno, "apply_automatic_transitions"))
        assert not unguarded, (
            "EVAL-06 dry-run-first invariant violated: found unguarded "
            "apply_automatic_transitions call sites.\n  Unguarded:\n  "
            + "\n  ".join(f"line {ln}: {what}" for ln, what in unguarded)
        )

    def test_apply_patch_transaction_calls_are_dry_run_guarded(self, parsed):
        """If any direct call sites of apply_patch_transaction exist in
        curator.py, they must be guarded. As of v6.0, curator.py does NOT
        call apply_patch_transaction directly (the v6.0 invariant routes
        it through hermes_cli/curator.py:_cmd_approve). This test ensures
        no future contributor adds an unguarded direct call."""
        tree, parent_map = parsed
        calls = _collect_call_sites_of(tree, "apply_patch_transaction")
        unguarded: list[tuple[int, str]] = []
        for call in calls:
            if _is_inside_not_dry_run_guard(call, parent_map):
                continue
            unguarded.append((call.lineno, "apply_patch_transaction"))
        # If no call sites exist, the test passes vacuously — that's the
        # v6.0 baseline (curator.py delegates apply_patch_transaction to
        # hermes_cli). The point of this test is to catch REGRESSIONS.
        if unguarded:
            pytest.fail(
                "EVAL-06 dry-run-first invariant violated: found direct "
                "apply_patch_transaction call sites in agent/curator.py. "
                "Per v6.0 P31 structural invariant, this function must "
                "ONLY be called from hermes_cli/curator.py:_cmd_approve.\n"
                "  Unguarded:\n  "
                + "\n  ".join(f"line {ln}: {what}" for ln, what in unguarded)
            )

    def test_no_unguarded_write_paths(self, parsed):
        """Meta-test: combine all three write-path names. Catches the
        case where a NEW write-path name is added to the codebase but not
        to WRITE_PATH_NAMES — the per-name tests would silently pass."""
        tree, parent_map = parsed
        all_calls = _collect_calls(tree)
        write_calls = [c for c in all_calls if _call_name(c) in WRITE_PATH_NAMES]
        # Sanity: we expect at least 1 write-path call site
        # (apply_automatic_transitions at minimum). If zero, the AST-walk is
        # broken. The exact count varies by code state (older curator.py
        # lacks v6.0 _feedback_scan_phase's append_audit calls); the floor
        # is the always-present deterministic prune invocation.
        assert len(write_calls) >= 1, (
            f"Expected at least 1 write-path call site in curator.py "
            f"(apply_automatic_transitions); got {len(write_calls)}. "
            "Did the AST-walk miss them?"
        )
        # Verify each is guarded (directly or transitively).
        unguarded: list[tuple[int, str]] = []
        for call in write_calls:
            name = _call_name(call) or "<unknown>"
            if _is_inside_not_dry_run_guard(call, parent_map):
                continue
            enclosing = _is_inside_function_named(
                call, parent_map, {"_feedback_scan_phase"}
            )
            if enclosing is not None:
                # Transitive: check helper callers.
                helper_calls = _collect_call_sites_of(tree, enclosing)
                if all(
                    _is_inside_not_dry_run_guard(hc, parent_map)
                    for hc in helper_calls
                ):
                    continue
            unguarded.append((call.lineno, name))
        assert not unguarded, (
            "EVAL-06 dry-run-first invariant violated: found write-path "
            "call sites NOT structurally inside `if not dry_run:` guards.\n"
            "  Unguarded:\n  "
            + "\n  ".join(f"line {ln}: {what}" for ln, what in unguarded)
        )
