"""Phase 38 regression test — OpenClaw / Toonflow / Node.js decoupling.

SC#1 (OPENCLAW-REMOVE-01): zero openclaw / Toonflow / sessions_spawn(runtime="acp")
    references in executable code across the 4 v5.0 deliverable dirs.
SC#3 (OPENCLAW-REMOVE-03): zero Node.js runtime dependency
    (require() / subprocess.run([...node]) / import package.json) in the same scope.
T-38-01 mitigation: DEPRECATED.md migration guide points to a live SKILL.md.

Approach mirrors the Phase 37 precedent
(test_canvas_sync_integration.py::TestNoLegacyReferences):
  * AST walk skips docstring Constant ids — docstrings that declare "no
    openclaw" are documentation, not code references.
  * Test files (``test_*.py``) are excluded from the scan target list —
    they necessarily reference the forbidden names by virtue of asserting
    their absence (``pattern = re.compile(r"openclaw|...")``). Including
    them would make the test self-failing.
  * Production code (the actual deliverables) is the only scan target.
"""

import ast
import pathlib
import re

# Resolve hermes-agent repo root from this test file's location:
# plugins/kais_aigc/tests/test_openclaw_decoupled.py -> 3 parents up = repo root.
HERMES_ROOT = pathlib.Path(__file__).resolve().parents[3]

V5_DELIVERABLE_DIRS = [
    HERMES_ROOT / "skills" / "kais-movie-pipeline",
    HERMES_ROOT / "plugins" / "kais_aigc",
    HERMES_ROOT / "plugins" / "pipeline_state",
    HERMES_ROOT / "plugins" / "review_gates",
]

# Only executable Python code is in scope — docs (.md) are not scanned.
EXECUTABLE_SUFFIX = ".py"

# Test files necessarily mention the forbidden names to assert their absence.
# Excluding them prevents the test from being self-failing on its own source.
# (Same convention as Phase 37's TestNoLegacyReferences.)
TEST_FILE_RE = re.compile(r"^test_.*\.py$", re.IGNORECASE)


def _iter_production_files(directory):
    """Yield production .py files under directory.

    Skips test files (``test_*.py``) and __pycache__ artifacts. Test files
    legitimately reference the forbidden names while asserting their absence,
    so scanning them would make any regression test self-failing.
    """
    for p in directory.rglob("*"):
        if not p.is_file() or p.suffix != EXECUTABLE_SUFFIX:
            continue
        if TEST_FILE_RE.match(p.name):
            continue
        if "__pycache__" in p.parts:
            continue
        yield p


def _docstring_constant_ids(tree):
    """Return the Python id() set of docstring Constant AST nodes in ``tree``.

    A docstring is the first statement of Module / FunctionDef /
    AsyncFunctionDef / ClassDef, when that statement is a bare string
    expression. Phase 37 precedent.
    """
    ids = set()
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.Module, ast.FunctionDef,
                               ast.AsyncFunctionDef, ast.ClassDef)):
            if parent.body and isinstance(parent.body[0], ast.Expr):
                expr = parent.body[0]
                if isinstance(expr.value, ast.Constant) and isinstance(
                    expr.value.value, str
                ):
                    ids.add(id(expr.value))
    return ids


def _scan_ast(path, pattern):
    """Yield (path, lineno, snippet) for AST string/Name nodes matching
    ``pattern``, skipping docstring constants."""
    source = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        # Fallback to raw line grep — better to false-positive than miss.
        for line_num, line in enumerate(source.splitlines(), 1):
            if pattern.search(line):
                yield path, line_num, line.strip()
        return

    skip_ids = _docstring_constant_ids(tree)
    for node in ast.walk(tree):
        if id(node) in skip_ids:
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            match = pattern.search(node.value)
            if match:
                yield path, getattr(node, "lineno", "?"), match.group(0)
        elif isinstance(node, ast.Name) and pattern.search(node.id):
            yield path, node.lineno, node.id


def test_openclaw_references_zero_in_v5_deliverables():
    """SC#1 + OPENCLAW-REMOVE-01.

    Asserts zero executable-code references to openclaw / Toonflow /
    sessions_spawn(runtime="acp") across the 4 v5.0 deliverable dirs.
    Docstrings (AST-skipped) and test files (path-skipped) are exempt.
    """
    pattern = re.compile(
        r'openclaw|toonflow|sessions_spawn\(runtime=["\']acp',
        re.IGNORECASE,
    )
    hits = []
    missing_dirs = []
    for d in V5_DELIVERABLE_DIRS:
        if not d.exists():
            missing_dirs.append(str(d))
            continue
        for path in _iter_production_files(d):
            for hit_path, lineno, snippet in _scan_ast(path, pattern):
                hits.append(f"{hit_path}:{lineno}: '{snippet}'")

    assert not missing_dirs, (
        f"SC#1 setup error — v5.0 deliverable dirs missing:\n"
        f"{chr(10).join(missing_dirs)}"
    )
    assert not hits, (
        f"SC#1 violation — openclaw/Toonflow code refs in v5.0 deliverables:\n"
        f"{chr(10).join(hits)}"
    )


def test_no_nodejs_runtime_dependency_in_v5_deliverables():
    """SC#3 + OPENCLAW-REMOVE-03.

    Asserts zero Node.js runtime dependency patterns in executable code across
    the 4 v5.0 deliverable dirs:
      - CommonJS ``require(...)`` (Node-only module loader)
      - ``subprocess.run([... "node", ...])`` / ``subprocess.run("node ...")``
      - ``import package.json`` / ``from package.json`` (JSON-as-module is Node)
      - ``child_process`` / ``npm install`` (Node ecosystem)
    Test files and docstrings are exempt (same exemption rationale as SC#1).
    """
    pattern = re.compile(
        r'require\(|'
        r'subprocess\.run\(\s*\[?\s*["\']node|'
        r'\bimport\s+package\.json|'
        r'\bfrom\s+package\.json|'
        r'child_process|'
        r'\bnpm\s+install',
        re.IGNORECASE,
    )
    hits = []
    for d in V5_DELIVERABLE_DIRS:
        if not d.exists():
            continue  # already asserted in SC#1 test
        for path in _iter_production_files(d):
            for hit_path, lineno, snippet in _scan_ast(path, pattern):
                hits.append(f"{hit_path}:{lineno}: '{snippet}'")

    assert not hits, (
        f"SC#3 violation — Node.js runtime dependency in v5.0 deliverables:\n"
        f"{chr(10).join(hits)}"
    )


def test_deprecated_md_points_to_live_skill():
    """T-38-01 mitigation.

    The migration guide in kais-movie-agent/DEPRECATED.md is the canonical
    pointer for future operators. Asserts that:
      1. DEPRECATED.md mentions the hermes-agent skill path.
      2. The referenced SKILL.md actually exists on disk.
    Prevents the migration guide from drifting to a wrong/deleted path.
    """
    deprecated_md = pathlib.Path(
        "/data/workspace/kais-movie-agent/DEPRECATED.md"
    )
    assert deprecated_md.exists(), (
        f"T-38-01 setup error — {deprecated_md} not found"
    )
    content = deprecated_md.read_text(encoding="utf-8", errors="ignore")
    assert "hermes-agent/skills/kais-movie-pipeline" in content, (
        "T-38-01 violation — DEPRECATED.md does not point to "
        "hermes-agent/skills/kais-movie-pipeline"
    )
    skill_md = pathlib.Path(
        "/data/workspace/hermes-agent/skills/kais-movie-pipeline/SKILL.md"
    )
    assert skill_md.exists(), (
        f"T-38-01 violation — DEPRECATED.md points to non-existent {skill_md}"
    )
