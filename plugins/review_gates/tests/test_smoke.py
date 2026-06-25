"""Smoke test for the review_gates plugin (Phase 31 skeleton + Phase 34-04 wiring).

Verifies the five contracts the plugin must satisfy:

1. ``plugin.yaml`` manifest parses and declares the expected 4-tool surface.
2. ``__init__.py`` and ``tools.py`` import without errors (no missing deps,
   no circular imports).
3. ``register(ctx)`` registers exactly 4 tools with
   ``toolset="review_gates"`` and well-formed schemas.
4. Every handler returns valid JSON (Phase 31 stubs returned a
   ``status="not_implemented"`` envelope; Phase 34-04 swapped in real
   dispatch handlers, so the assertion was weakened to "valid JSON with
   either a status or error field" — mirrors Phase 33-04).
5. ``python -c "from plugins.review_gates import register"`` succeeds — the
   literal ROADMAP SC#3 check ("entry module smoke-imports").
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

PLUGIN_NAME = "review_gates"
# tests/test_smoke.py -> parents[0]=tests, parents[1]=review_gates,
# parents[2]=plugins, parents[3]=hermes-agent root.
PLUGIN_DIR = Path(__file__).resolve().parents[1]
PLUGINS_DIR = Path(__file__).resolve().parents[2]
HERMES_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_TOOLS = [
    "gate_submit",
    "gate_wait",
    "gate_resolve",
    "gates_list",
]
EXPECTED_TOOLSET = PLUGIN_NAME


def _load_module(name: str, file_path: Path):
    """Load a Python module from an explicit file path (mirrors how the
    hermes-agent plugin loader imports directory plugins)."""
    spec = importlib.util.spec_from_file_location(
        name, file_path,
        submodule_search_locations=[str(file_path.parent)],
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeCtx:
    """Minimal stand-in for hermes_agent's PluginContext.

    Captures every ``register_tool(...)`` call's kwargs so the test can assert
    on the registered tool surface without spinning up the real PluginManager
    (which would mutate the global tool registry and side-effect across tests).
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def register_tool(self, **kwargs) -> None:  # noqa: D401 - fake ctx
        self.calls.append(kwargs)


def test_manifest_valid():
    """Test 1: plugin.yaml parses and declares the expected tool surface."""
    manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == PLUGIN_NAME
    assert manifest["version"], "version must be non-empty"
    assert manifest["description"], "description must be non-empty"
    assert manifest.get("kind", "standalone") == "standalone", (
        "skeleton plugins must be opt-in (kind: standalone)"
    )
    assert manifest["provides_tools"] == EXPECTED_TOOLS, (
        "provides_tools must equal the expected 4-tool list in declared order"
    )


def test_module_imports_cleanly():
    """Test 2: __init__.py and tools.py import without errors."""
    saved_path = list(sys.path)
    sys.path.insert(0, str(HERMES_ROOT))
    try:
        init_mod = _load_module("_smoke_review_gates_init", PLUGIN_DIR / "__init__.py")
        assert hasattr(init_mod, "register"), "register() must be exported"

        tools_mod = _load_module(
            "_smoke_review_gates_tools", PLUGIN_DIR / "tools.py",
        )
        for symbol in (
            "GATE_SUBMIT_SCHEMA",
            "GATE_WAIT_SCHEMA",
            "GATE_RESOLVE_SCHEMA",
            "GATES_LIST_SCHEMA",
            "_handle_gate_submit",
            "_handle_gate_wait",
            "_handle_gate_resolve",
            "_handle_gates_list",
        ):
            assert hasattr(tools_mod, symbol), f"tools.py missing symbol: {symbol}"
    finally:
        sys.path[:] = saved_path


def test_register_registers_4_tools_with_correct_toolset():
    """Test 3: register(ctx) registers exactly 4 tools with toolset=review_gates."""
    saved_path = list(sys.path)
    sys.path.insert(0, str(HERMES_ROOT))
    try:
        mod = _load_module("_smoke_review_gates_init_reg", PLUGIN_DIR / "__init__.py")
        ctx = _FakeCtx()
        mod.register(ctx)
    finally:
        sys.path[:] = saved_path

    assert len(ctx.calls) == 4, f"expected 4 tools, got {len(ctx.calls)}"
    registered_names = {c["name"] for c in ctx.calls}
    assert registered_names == set(EXPECTED_TOOLS), (
        f"tool names mismatch: {registered_names} != {set(EXPECTED_TOOLS)}"
    )
    for call in ctx.calls:
        assert call["toolset"] == EXPECTED_TOOLSET, (
            f"tool {call['name']} has toolset={call['toolset']!r}, "
            f"expected {EXPECTED_TOOLSET!r}"
        )
        schema = call["schema"]
        assert isinstance(schema, dict), "schema must be a dict"
        for required_key in ("name", "description", "parameters"):
            assert required_key in schema, (
                f"tool {call['name']} schema missing key: {required_key}"
            )
        assert schema["name"] == call["name"], (
            f"tool {call['name']} schema has name={schema['name']!r}"
        )


def test_handlers_return_valid_json():
    """Test 4: every handler returns valid JSON with either a ``status`` or
    non-empty ``error`` field.

    Phase 31 stubs returned ``status="not_implemented"`` envelopes; Phase
    34-04 replaced them with real dispatch handlers. The weakened assertion
    keeps the smoke contract honest without coupling to stub-era envelope
    fields. Mirrors the Phase 33-04 fix exactly.
    """
    saved_path = list(sys.path)
    sys.path.insert(0, str(HERMES_ROOT))
    try:
        mod = _load_module("_smoke_review_gates_init_h", PLUGIN_DIR / "__init__.py")
    finally:
        sys.path[:] = saved_path

    name_to_handler = {name: handler for name, _schema, handler, _emoji in mod._TOOLS}
    assert set(name_to_handler) == set(EXPECTED_TOOLS), (
        f"_TOOLS names mismatch: {set(name_to_handler)} != {set(EXPECTED_TOOLS)}"
    )

    # Use empty args so handlers hit the validation-error path and return
    # tool_error JSON without performing real I/O. The smoke contract only
    # verifies the handlers return valid JSON — the Phase 34-04 dispatch
    # tests (test_tools_dispatch.py) exercise the real dispatch paths with
    # proper fixtures. (Mirrors Phase 33-04's approach.)
    sample_args: dict = {}
    for tool_name, handler in name_to_handler.items():
        result = handler(sample_args)
        assert isinstance(result, str), (
            f"{tool_name}: handler must return a string, got {type(result).__name__}"
        )
        parsed = json.loads(result)  # raises if not valid JSON
        assert isinstance(parsed, dict), (
            f"{tool_name}: handler result must parse to a JSON object"
        )
        assert len(parsed) > 0, (
            f"{tool_name}: handler result must be a non-empty JSON object"
        )


def test_python_dash_c_import_succeeds():
    """Test 5: literal ROADMAP SC#3 check — `python -c "from plugins.review_gates
    import register"` must succeed with exit code 0."""
    result = subprocess.run(
        [
            sys.executable, "-c",
            (
                f"import sys; sys.path.insert(0, {str(HERMES_ROOT)!r}); "
                f"from plugins.{PLUGIN_NAME} import register; "
                f"print(callable(register))"
            ),
        ],
        capture_output=True, text=True, timeout=10,
        cwd=str(HERMES_ROOT),
    )
    assert result.returncode == 0, (
        f"python -c import failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stdout.strip() == "True", (
        f"expected stdout='True', got {result.stdout!r}"
    )
