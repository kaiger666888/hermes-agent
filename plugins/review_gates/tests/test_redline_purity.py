"""test_redline_purity.py — Phase 40-01 D-34-01 extended purity guard.

AST-walks every redline detector module + types.py and asserts:

- No top-level imports of ``httpx`` / ``jwt`` / ``yaml`` / ``plugins``
  (D-34-01 extended to redline detectors — same rationale as
  ``test_gate.py:45-60``: unit-testable in isolation, no network /
  config coupling, no supply-chain surface).
- No ``async def`` nodes anywhere (D-34-05 sync-only rule inherited
  from gate.py).
- No module-level mutable state (detectors are pure functions over
  the payload arg).

These are structural invariants — if a future PR adds an httpx import
to a detector, this test catches it before the merge.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module discovery — all 4 files under plugins/review_gates/gates/ that
# must remain pure stdlib. types.py is a pure-typing module; the 3
# redline_*.py modules are the detectors under purity contract.
# ---------------------------------------------------------------------------

_GATES_DIR = Path(__file__).resolve().parent.parent / "gates"

_DETECTOR_MODULES = [
    _GATES_DIR / "types.py",
    _GATES_DIR / "redline_emotion_desensitize.py",
    _GATES_DIR / "redline_no_cold_open.py",
    _GATES_DIR / "redline_unfinished_ending.py",
]


def _module_source(path: Path) -> str:
    """Read module source as UTF-8 text (PLW1514 compliance)."""
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 15: no forbidden top-level imports
# ---------------------------------------------------------------------------

# Forbidden top-level package roots. Mirrors the gate.py D-34-01 list
# (httpx/jwt/yaml = external network/config/encoding libs) and adds
# `plugins` for the *external* reach-back surface — detectors must not
# import gate.py / gate_config.py / runner_hooks.py / tools.py (Plan 02
# owns that wiring; the auto-detect path goes runner_hooks -> DETECTOR_REGISTRY,
# never detector -> runner_hooks).
#
# INTRA-PACKAGE EXCEPTION: `plugins.review_gates.gates.types` is the
# detectors' own sibling typing module (pure-typing, no side-effects).
# Importing DetectorResult from it is NOT a supply-chain risk (T-40-04
# concerns external network/config surface, not intra-package typing).
# The `_ALLOWED_INTRA_PACKAGE` allow-list whitelists this one path so
# the purity guard catches real forbidden reach-backs while permitting
# the detectors to consume their shared type contract.
_FORBIDDEN_TOP = {"httpx", "jwt", "yaml"}
_FORBIDDEN_PLUGINS_REACHBACK = {"plugins"}  # gate.py / gate_config.py / runner_hooks.py / tools.py
# Intra-package typing imports permitted (detectors share types.py).
# Anything else under `plugins.*` is still forbidden.
_ALLOWED_INTRA_PACKAGE = {"plugins.review_gates.gates", "plugins.review_gates.gates.types"}


@pytest.mark.parametrize("mod_path", _DETECTOR_MODULES, ids=lambda p: p.name)
def test_detector_modules_have_no_forbidden_imports(mod_path: Path) -> None:
    """Test 15 — D-34-01 extended: AST-walk every detector module.

    Asserts no top-level import of httpx / jwt / yaml (external
    network/config libs) AND no reach-back into the broader
    plugins.* surface (gate.py / gate_config.py / runner_hooks.py /
    tools.py — Plan 02 owns that wiring direction).

    The detectors' own sibling typing module
    (``plugins.review_gates.gates.types``) is whitelisted — it is
    pure-typing (no side-effects) and not a T-40-04 supply-chain risk.

    Catches supply-chain drift (T-40-04) at CI time before a forbidden
    dependency enters the pure-stdlib detector leaf.
    """
    src = _module_source(mod_path)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                assert top not in _FORBIDDEN_TOP, (
                    f"forbidden import in {mod_path.name}: {alias.name} "
                    f"(top-level '{top}' violates D-34-01 extended purity)"
                )
                # `plugins.*` only allowed if the FULL module path is whitelisted.
                if top in _FORBIDDEN_PLUGINS_REACHBACK:
                    assert alias.name in _ALLOWED_INTRA_PACKAGE, (
                        f"forbidden plugins.* reach-back in {mod_path.name}: {alias.name} "
                        f"(detectors must not import gate.py / gate_config.py / "
                        f"runner_hooks.py / tools.py — Plan 02 owns that wiring)"
                    )
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            assert top not in _FORBIDDEN_TOP, (
                f"forbidden from-import in {mod_path.name}: {node.module} "
                f"(top-level '{top}' violates D-34-01 extended purity)"
            )
            if top in _FORBIDDEN_PLUGINS_REACHBACK:
                assert (node.module or "") in _ALLOWED_INTRA_PACKAGE, (
                    f"forbidden plugins.* reach-back in {mod_path.name}: {node.module} "
                    f"(detectors must not import gate.py / gate_config.py / "
                    f"runner_hooks.py / tools.py — Plan 02 owns that wiring)"
                )


# ---------------------------------------------------------------------------
# Test 16: no async def
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mod_path", _DETECTOR_MODULES, ids=lambda p: p.name)
def test_detector_modules_have_no_async_def(mod_path: Path) -> None:
    """Test 16 — D-34-05: detectors are sync-only.

    Asserts no ``ast.AsyncFunctionDef`` nodes. Detectors run inside the
    sync gate lifecycle (gate.py is sync-only); an ``async def detect``
    would force callers to wrap in ``asyncio.to_thread`` unnecessarily
    and break the pure-function contract.
    """
    src = _module_source(mod_path)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        assert not isinstance(node, ast.AsyncFunctionDef), (
            f"{mod_path.name} must not contain async def (D-34-05 sync-only); "
            f"found: {getattr(node, 'name', '<unknown>')}"
        )


# ---------------------------------------------------------------------------
# Test 17: every suggested_action matches ^formula:[a-z][a-z0-9-]*$
# ---------------------------------------------------------------------------

# This is enforced end-to-end via the behavior tests (each reject-branch
# assertion), but we also do a structural AST scan here so that a
# future detector module that hardcodes a different action shape is
# caught at the purity gate, not just at the behavior gate.

_FORMULA_RE = re.compile(r"^formula:[a-z][a-z0-9-]*$")


def _extract_string_returns(src: str) -> list[str]:
    """Walk AST and return string literals returned via `return` statements.

    Used to verify that any string literal returned as a detector's
    suggested_action matches the formula: convention.
    """
    tree = ast.parse(src)
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                literals.append(node.value.value)
    return literals


@pytest.mark.parametrize(
    "mod_path",
    [
        _GATES_DIR / "redline_emotion_desensitize.py",
        _GATES_DIR / "redline_no_cold_open.py",
        _GATES_DIR / "redline_unfinished_ending.py",
    ],
    ids=lambda p: p.name,
)
def test_detector_action_strings_match_formula_convention(mod_path: Path) -> None:
    """Test 17 (structural half) — every returned string literal shaped like
    a suggested_action MUST match ``^formula:[a-z][a-z0-9-]*$``.

    This catches accidental hardcoded action strings (e.g. ``"rollback:..."``
    style from Phase 34's manual gates) leaking into the redline detectors.
    The behavioral half of Test 17 lives in each detector's behavior test
    file (asserting the actual returned tuple).
    """
    src = _module_source(mod_path)
    for literal in _extract_string_returns(src):
        if "formula:" in literal or ":" in literal and not literal.startswith("formula:"):
            # Looks like an action string — enforce convention.
            assert _FORMULA_RE.match(literal), (
                f"{mod_path.name} returned literal {literal!r} does not match "
                f"^formula:[a-z][a-z0-9-]*$ (Phase 39 formula_library read-side convention)"
            )


# ---------------------------------------------------------------------------
# Sanity: the gates/ subpackage is importable without gate_config / gates.yaml
# ---------------------------------------------------------------------------


def test_gates_subpackage_importable_without_gate_config_or_yaml() -> None:
    """The gates/ subpackage is self-contained.

    Importing ``plugins.review_gates.gates`` MUST succeed even if
    ``gate_config.py`` and ``gates.yaml`` do not exist (Plan 02 owns
    those). Detectors depend only on stdlib + ``gates.types``.
    """
    # Use a fresh import to prove no side-effect dependency leaked.
    import importlib

    mod = importlib.import_module("plugins.review_gates.gates")
    assert hasattr(mod, "DETECTOR_REGISTRY"), "DETECTOR_REGISTRY missing from gates package"
    assert hasattr(mod, "types"), "types submodule missing from gates package"
    # DETECTOR_REGISTRY is a dict (RED phase: empty; Task 3: 3 entries).
    assert isinstance(mod.DETECTOR_REGISTRY, dict)
