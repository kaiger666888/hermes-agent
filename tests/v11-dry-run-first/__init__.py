"""EVAL-06 dry-run-first invariant tests.

Verifies that ``agent/curator.py::run_curator_review`` defaults to
``dry_run=True`` and that all state-mutation code paths are structurally
gated by ``if not dry_run:`` guards.

Mirrors the v6.0 ``TestNonBypassableHumanInLoop`` pattern from
``tests/hermes_cli/test_curator_cli.py`` (AST-walk over
``apply_patch_transaction`` call sites) — applied to the EVAL-06
dry_run guard.

Cites:
  - ``.planning/research/v10-orchestrator-design/05-POC-PLAN.md §4.6``
    (Dry-Run-First Invariant contract)
  - ``.planning/phases/55-eval-harness-2/55-03-PLAN.md`` (this plan)
"""
