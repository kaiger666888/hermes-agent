"""Smoke test for the kais_aigc plugin (Phase 31 skeleton).

Verifies the five contracts the skeleton must satisfy so Phase 32 can swap in
real HTTP clients without renegotiating the tool surface:

1. ``plugin.yaml`` manifest parses and declares the expected 4-tool surface.
2. ``__init__.py`` and ``tools.py`` import without errors (no missing deps,
   no circular imports).
3. ``register(ctx)`` registers exactly 4 tools with ``toolset="kais_aigc"``
   and well-formed schemas.
4. Every stub handler returns valid ``tool_result()`` JSON with
   ``status="not_implemented"`` and the correct plugin/tool identity.
5. ``python -c "from plugins.kais_aigc import register"`` succeeds — the
   literal ROADMAP SC#3 check ("entry module smoke-imports").
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

PLUGIN_NAME = "kais_aigc"
# tests/test_smoke.py -> parents[0]=tests, parents[1]=kais_aigc, parents[2]=plugins,
# parents[3]=hermes-agent root.
PLUGIN_DIR = Path(__file__).resolve().parents[1]
PLUGINS_DIR = Path(__file__).resolve().parents[2]
HERMES_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_TOOLS = [
    "kais_gold_team_submit",
    "kais_review_submit",
    "kais_canvas_sync",
    "kais_jimeng_call",
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
    # Importing __init__ exercises the `from plugins.kais_aigc.tools import ...`
    # line, which requires the hermes-agent root on sys.path so the absolute
    # import resolves. Same for tools.py's `from tools.registry import ...`.
    saved_path = list(sys.path)
    sys.path.insert(0, str(HERMES_ROOT))
    try:
        init_mod = _load_module("_smoke_kais_aigc_init", PLUGIN_DIR / "__init__.py")
        assert hasattr(init_mod, "register"), "register() must be exported"

        tools_mod = _load_module(
            "_smoke_kais_aigc_tools", PLUGIN_DIR / "tools.py",
        )
        # Spot-check a few symbols the register loop depends on.
        for symbol in (
            "KAIS_GOLD_TEAM_SUBMIT_SCHEMA",
            "KAIS_REVIEW_SUBMIT_SCHEMA",
            "KAIS_CANVAS_SYNC_SCHEMA",
            "KAIS_JIMENG_CALL_SCHEMA",
            "_handle_kais_gold_team_submit",
            "_handle_kais_review_submit",
            "_handle_kais_canvas_sync",
            "_handle_kais_jimeng_call",
        ):
            assert hasattr(tools_mod, symbol), f"tools.py missing symbol: {symbol}"
    finally:
        sys.path[:] = saved_path


def test_register_registers_4_tools_with_correct_toolset():
    """Test 3: register(ctx) registers exactly 4 tools with toolset=kais_aigc."""
    saved_path = list(sys.path)
    sys.path.insert(0, str(HERMES_ROOT))
    try:
        mod = _load_module("_smoke_kais_aigc_init_reg", PLUGIN_DIR / "__init__.py")
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


def test_handlers_return_not_implemented_json():
    """Test 4: every stub handler returns valid tool_result() JSON with
    status=not_implemented and the correct plugin/tool identity."""
    saved_path = list(sys.path)
    sys.path.insert(0, str(HERMES_ROOT))
    try:
        mod = _load_module("_smoke_kais_aigc_init_h", PLUGIN_DIR / "__init__.py")
    finally:
        sys.path[:] = saved_path

    # Build {tool_name: handler} from the _TOOLS tuple declared in __init__.py.
    name_to_handler = {name: handler for name, _schema, handler, _emoji in mod._TOOLS}
    assert set(name_to_handler) == set(EXPECTED_TOOLS), (
        f"_TOOLS names mismatch: {set(name_to_handler)} != {set(EXPECTED_TOOLS)}"
    )

    sample_args = {"sample": "args", "task_type": "image_draw"}
    for tool_name, handler in name_to_handler.items():
        result = handler(sample_args)
        assert isinstance(result, str), (
            f"{tool_name}: handler must return a string, got {type(result).__name__}"
        )
        parsed = json.loads(result)  # raises if not valid JSON
        assert parsed["status"] == "not_implemented", (
            f"{tool_name}: status={parsed.get('status')!r}, expected 'not_implemented'"
        )
        assert parsed["plugin"] == PLUGIN_NAME, (
            f"{tool_name}: plugin={parsed.get('plugin')!r}, expected {PLUGIN_NAME!r}"
        )
        assert parsed["tool"] == tool_name, (
            f"{tool_name}: tool field={parsed.get('tool')!r}"
        )
        assert parsed.get("implementing_phase"), (
            f"{tool_name}: implementing_phase must be non-empty"
        )
        assert parsed.get("args_received") == sample_args, (
            f"{tool_name}: args_received must echo the input args dict"
        )


def test_python_dash_c_import_succeeds():
    """Test 5: literal ROADMAP SC#3 check — `python -c "from plugins.kais_aigc
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
