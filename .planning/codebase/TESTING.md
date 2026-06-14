# Testing Patterns

**Analysis Date:** 2026-06-14

## Test Framework

**Runner:**
- **pytest** `9.0.2` (declared in `[project.optional-dependencies] dev` of `pyproject.toml:90`).
- Plugins: `pytest-asyncio==1.3.0`, `pytest-timeout==2.4.0`.
- Config: `[tool.pytest.ini_options]` in `pyproject.toml:250-261`.
- **No pytest-xdist.** Replaced by per-file subprocess isolation (see "Test Runner" below).

**Assertion Library:**
- Plain `assert` statements. No `unittest.TestCase`-style asserts (`self.assertEqual`, etc. are absent).

**Run Commands:**
```bash
# Canonical runner — use this, not raw `pytest`. Activates venv, hermetic env,
# per-file subprocess isolation. Matches CI exactly.
scripts/run_tests.sh                                  # full suite
scripts/run_tests.sh -j 4                             # cap parallelism to 4 workers
scripts/run_tests.sh tests/agent/                     # discover only here
scripts/run_tests.sh tests/agent/ tests/acp/          # multiple roots
scripts/run_tests.sh tests/foo.py                     # single file
scripts/run_tests.sh tests/foo.py -- --tb=long        # path + pytest args
scripts/run_tests.sh -- -v --tb=long                  # pytest args only

# Direct pytest (when iterating on ONE file). Bypasses the hermetic env
# wrapper; safe only if you've already sourced the venv.
.venv/bin/python -m pytest tests/test_hermes_logging.py -v

# Integration / e2e (excluded from the default suite):
.venv/bin/python -m pytest tests/e2e/ -v --tb=short
.venv/bin/python -m pytest -m integration tests/        # opt-in marker

# Slice sharding (CI uses 6 slices):
scripts/run_tests_parallel.py --slice 1/6
```

**Default pytest args** (from `pyproject.toml:261`):
```
addopts = "-m 'not integration' --timeout=30 --timeout-method=signal"
```
- `-m 'not integration'` — integration tests (requiring real API keys / Modal) are skipped by default.
- `--timeout=30` — per-test 30-second hard cap, SIGALRM method (POSIX).
- `testpaths = ["tests"]` — discovery root.

## Test Runner Architecture

**Per-file subprocess isolation** is the central architectural choice. The canonical runner `scripts/run_tests_parallel.py`:
1. Discovers every `test_*.py` under `tests/` (excluding `integration/`, `e2e/`, `docker/` — see `_SKIP_PARTS` at `scripts/run_tests_parallel.py:72`).
2. Spawns one `python -m pytest <file>` subprocess per file with bounded parallelism (default: `os.cpu_count()`; override via `HERMES_TEST_WORKERS`).
3. Each file gets a fresh Python interpreter — **cross-file module-level state leakage is impossible**.
4. Per-file wall-clock cap (`_DEFAULT_FILE_TIMEOUT_SECONDS = 600.0`, overridable via `--file-timeout` / `HERMES_TEST_FILE_TIMEOUT`).
5. Duration cache persists last-observed subprocess times to `test_durations.json` so future runs (including CI slices) can balance sharding.

**Why per-file, not per-test or xdist?** Documented at `scripts/run_tests_parallel.py:10-24`:
- Per-test spawn overhead (~250ms × 17k tests = 70min CPU) blew the wall-clock budget.
- Per-file spawn (~250ms × ~850 files = ~3.5min) fits while still giving every file a fresh interpreter.
- xdist's persistent workers accumulate state across files — exactly the leakage class this design eliminates.

**Canonical shell wrapper** `scripts/run_tests.sh`:
- Activates venv (probes `.venv`, `venv`, `~/.hermes/hermes-agent/venv`).
- Uses `env -i` to start with an empty environment, then opts in only `PATH`, `HOME`, `TZ=UTC`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONHASHSEED=0`. **No credential env var can leak** — you'd have to explicitly add it.
- Loads `$HOME/.hermes/pytest_live_guard.py` if present (developer opt-in live-system guard).

**CI invocation** (`.github/workflows/tests.yml`):
```yaml
- name: Run tests (slice ${{ matrix.slice }}/6)
  run: |
    source .venv/bin/activate
    python scripts/run_tests_parallel.py --slice ${{ matrix.slice }}/6
  env:
    OPENROUTER_API_KEY: ""
    OPENAI_API_KEY: ""
    NOUS_API_KEY: ""
```
Matrix: 6 slices, uploaded as `test-durations-slice-N` artifacts and merged into a single duration cache on `main`.

## Test File Organization

**Location:** `tests/` at repo root, mirroring the source tree:

```
tests/
├── conftest.py                    # Root conftest — autouse hermetic env + live-system guard
├── test_<module>.py               # Tests for top-level modules (test_hermes_logging.py, test_utils_*.py)
├── agent/                         # Tests for the agent/ package
│   └── test_i18n.py, test_insights.py, ...
├── tools/                         # Tests for tools/ package (+ conftest.py with web_registry_populated fixture)
├── gateway/                       # Tests for gateway/ package
├── hermes_cli/                    # Tests for hermes_cli/ package
├── acp/, acp_adapter/             # Tests for ACP integration
├── plugins/                       # Plugin tests
├── providers/                     # Provider tests
├── cron/                          # Cron scheduler tests
├── tui_gateway/                   # TUI gateway tests
├── hermes_state/                  # State DB tests
├── scripts/                       # Installer / shell script tests
├── website/                       # Static-site tests
├── cli/                           # CLI command tests
├── run_agent/                     # End-to-end agent-loop tests
├── honcho_plugin/, openviking_plugin/   # Plugin-shape conformance tests
├── fakes/                         # Shared fake servers (e.g. fake_ha_server.py for Home Assistant)
├── integration/                   # SKIPPED by default — requires external services
├── e2e/                           # SKIPPED by default — full async platform flows (Telegram/Discord)
├── docker/                        # SKIPPED by default — runs against a prebuilt docker image in its own CI job
├── stress/                        # Concurrency / property-fuzzing / subprocess-e2e suite
└── run_interrupt_test.py          # Standalone interrupt-handling harness
```

**Naming:**
- Files: `test_<module>.py` or `test_<topic>.py`. Examples: `test_hermes_logging.py`, `test_trajectory_compressor.py`, `test_install_sh_symlink_stomp.py`.
- Classes: `class Test<Thing>:` grouping related tests. Example: `class TestSetupLogging:` at `tests/test_hermes_logging.py:64`.
- Functions: `test_<scenario>` with descriptive names. Examples: `test_no_hermes_home_returns_native`, `test_docker_profile_active`, `test_creates_log_directory`, `test_idempotent_no_duplicate_handlers`.

**Per-package conftests:** Several subdirectories have their own `conftest.py` for package-local fixtures (e.g. `tests/tools/conftest.py` registers web-search providers, `tests/e2e/conftest.py` mocks telegram/discord modules).

## Test Structure

**Suite Organization** — class-based grouping for related scenarios:

```python
# tests/test_hermes_constants.py:18
class TestGetDefaultHermesRoot:
    """Tests for get_default_hermes_root() — Docker/custom deployment awareness."""

    def test_no_hermes_home_returns_native(self, tmp_path, monkeypatch):
        """When HERMES_HOME is not set, returns ~/.hermes."""
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        assert get_default_hermes_root() == tmp_path / ".hermes"

    def test_hermes_home_is_docker(self, tmp_path, monkeypatch):
        """When HERMES_HOME points outside ~/.hermes (Docker), returns HERMES_HOME."""
        docker_home = tmp_path / "opt" / "data"
        docker_home.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(docker_home))
        assert get_default_hermes_root() == docker_home
```

Top-level (non-class) test functions are also common for short, focused tests:

```python
# tests/test_trajectory_compressor.py:33
def test_generate_summary_kimi_omits_temperature():
    """Kimi models should have temperature omitted — server manages it."""
    config = CompressionConfig(
        summarization_model="kimi-for-coding",
        temperature=0.3,
        ...
    )
    compressor = TrajectoryCompressor.__new__(TrajectoryCompressor)
    compressor.config = config
    compressor.logger = MagicMock()
    ...
    result = compressor._generate_summary("tool output", metrics)
    assert result.startswith("[CONTEXT SUMMARY]:")
    assert "temperature" not in compressor.client.chat.completions.create.call_args.kwargs
```

**Patterns:**
- **One assertion concept per test.** Tests like `test_creates_agent_log_handler` (at `tests/test_hermes_logging.py:72`) assert exactly one structural property.
- **Descriptive docstrings** on test methods explaining the *when/then* contract.
- **`monkeypatch` for env / attribute / syscall stubbing** — preferred over `unittest.mock.patch` for env vars and module attributes (auto-undoes on test exit).
- **`unittest.mock.patch` as context manager** for call-recording mocks. Example from `tests/test_model_tools.py:42-46`:
  ```python
  def test_tool_hooks_receive_session_and_tool_call_ids(self):
      with (
          patch("model_tools.registry.dispatch", return_value='{"ok":true}'),
          patch("hermes_cli.plugins.invoke_hook") as mock_invoke_hook,
      ):
          result = handle_function_call(
              "web_search",
              {"q": "test"},
              task_id="task-1",
              tool_call_id="call-1",
              session_id="session-1",
          )

      assert result == '{"ok":true}'
      assert mock_invoke_hook.call_args_list == [
          call("pre_tool_call", tool_name="web_search", ...),
          call("post_tool_call", tool_name="web_search", ..., duration_ms=ANY),
          call("transform_tool_result", tool_name="web_search", ...),
      ]
  ```

## Mocking

**Framework:** stdlib `unittest.mock` (no `pytest-mock` plugin). Imports:
```python
from unittest.mock import AsyncMock, MagicMock, patch, ANY, call
```

**Patterns:**

1. **`monkeypatch.setattr`** for replacing module attributes / functions / env vars. Auto-cleans on test exit:
   ```python
   # tests/test_model_tools.py:152
   monkeypatch.setattr("hermes_cli.plugins.invoke_hook", fake_invoke_hook)
   monkeypatch.setattr("model_tools.registry.dispatch", fake_dispatch)
   ```

2. **`monkeypatch.setattr` with a dotted string** to patch a name through a different module's namespace:
   ```python
   # tests/test_toolsets.py:43
   monkeypatch.setattr("tools.registry.registry", reg)
   ```

3. **`patch(...)` as context manager** when you need to assert call counts/args:
   ```python
   with patch("model_tools.registry.dispatch", return_value='{"ok":true}') as mock_dispatch:
       ...
   assert mock_dispatch.called
   ```

4. **`MagicMock()` + attribute stubbing** for SDK clients and rich objects:
   ```python
   # tests/test_trajectory_compressor.py:42-48
   compressor = TrajectoryCompressor.__new__(TrajectoryCompressor)
   compressor.config = config
   compressor.logger = MagicMock()
   compressor._use_call_llm = False
   compressor.client = MagicMock()
   compressor.client.chat.completions.create.return_value = SimpleNamespace(
       choices=[SimpleNamespace(message=SimpleNamespace(content="[CONTEXT SUMMARY]: ..."))]
   )
   ```

5. **`SimpleNamespace` for lightweight DTO stubs** — preferred over `MagicMock` when the code under test does attribute access (not method calls):
   ```python
   from types import SimpleNamespace
   fake_response = SimpleNamespace(
       choices=[SimpleNamespace(message=SimpleNamespace(content="..."))]
   )
   ```

6. **`AsyncMock`** for async functions/coroutines:
   ```python
   # tests/test_trajectory_compressor.py:499
   mock_client.chat.completions.create = AsyncMock(
       return_value=SimpleNamespace(
           choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
       )
   )
   ```

7. **Module-install mocking** for optional third-party libraries that may not be installed (telegram, discord):
   ```python
   # tests/e2e/conftest.py:30-55
   def _ensure_telegram_mock():
       """Install mock telegram modules so TelegramAdapter can be imported."""
       if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
           return  # Real library installed

       telegram_mod = MagicMock()
       telegram_mod.Update = MagicMock()
       ...
       for name in ("telegram", "telegram.constants", "telegram.ext", ...):
           sys.modules.setdefault(name, telegram_mod)
   ```

**What to Mock:**
- All HTTP/SDK clients (`model_tools.registry.dispatch`, `OpenAI`, Anthropic SDK).
- All env vars (the autouse conftest fixture blanks them; opt back in explicitly with `monkeypatch.setenv`).
- The filesystem **only when the test would otherwise mutate the real FS** — prefer `tmp_path` for real-file tests.
- `subprocess.run`, `os.kill`, `os.system`, `pty.spawn`, `asyncio.create_subprocess_*` — the autouse `_live_system_guard` fixture (`tests/conftest.py:537-841`) intercepts these and raises if a command would mutate the live gateway. Either mock explicitly or mark with `@pytest.mark.live_system_guard_bypass`.

**What NOT to Mock:**
- `pytest` itself, `tmp_path`, `monkeypatch`.
- The `RedactingFormatter` in logging tests — `tests/test_hermes_logging.py` exercises the real formatter.
- The real `i18n._load_catalog()` — `tests/agent/test_i18n.py` reads the real `locales/*.yaml` files to enforce catalog parity.

## Fixtures and Factories

**Framework-level autouse fixtures** (defined in `tests/conftest.py`):

1. **`_hermetic_environment`** (`tests/conftest.py:326-392`) — autouse, runs before every test:
   - Blanks every credential-shaped env var (`_CREDENTIAL_SUFFIXES` + `_CREDENTIAL_NAMES` — ~150 names covering all provider keys).
   - Blanks every behavioral `HERMES_*` var (`_HERMES_BEHAVIORAL_VARS` — ~80 names, including `HERMES_HOME_MODE`, `HERMES_INTERACTIVE`, kanban paths, platform allowlists).
   - Redirects `HERMES_HOME` to a per-test tempdir with `sessions/`, `cron/`, `memories/`, `skills/` subdirs.
   - Pins `TZ=UTC`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONHASHSEED=0` for deterministic locale/timezone/hash behavior.
   - Disables AWS IMDS lookups (`AWS_EC2_METADATA_DISABLED=true`) — saves ~2s/test on EC2-probe timeouts.
   - Resets the plugin manager singleton.

2. **`_live_system_guard`** (`tests/conftest.py:537-841`) — autouse. Wraps `os.kill`, `os.killpg`, `subprocess.{run,Popen,call,check_call,check_output,getoutput,getstatusoutput}`, `os.system`, `os.popen`, `pty.spawn`, `asyncio.create_subprocess_{exec,shell}` to refuse any command that would mutate the live `hermes-gateway` systemd unit or kill foreign processes. Bypass with `@pytest.mark.live_system_guard_bypass`.

3. **`_ensure_current_event_loop`** (`tests/conftest.py:451-493`) — autouse. Installs a fresh asyncio event loop for sync tests that call `asyncio.get_event_loop()`. Python 3.12+ no longer creates one lazily; this bridges that gap without interfering with `@pytest.mark.asyncio` tests.

**Reusable non-autouse fixtures** in `tests/conftest.py`:
- `tmp_dir` (`conftest.py:421`) — alias for `tmp_path`.
- `mock_config` (`conftest.py:427`) — minimal hermes config dict for unit tests:
  ```python
  @pytest.fixture()
  def mock_config():
      return {
          "model": "test/mock-model",
          "toolsets": ["terminal", "file"],
          "max_turns": 10,
          "terminal": {"backend": "local", "cwd": "/tmp", "timeout": 30},
          "compression": {"enabled": False},
          "memory": {"memory_enabled": False, "user_profile_enabled": False},
          "command_allowlist": [],
      }
  ```

**Per-file local fixtures** (defined inside the test file that needs them):
- `tests/test_hermes_logging.py:17-50` `_reset_logging_state` — autouse within the file, strips `RotatingFileHandler`s between tests so handler-count assertions are stable.
- `tests/test_hermes_logging.py:53-61` `hermes_home` — reads back the `HERMES_HOME` set by the autouse fixture.
- `tests/tools/conftest.py:46-50` `web_registry_populated` — registers all bundled web-search providers for one test then resets.

**Factory pattern** (test-local helpers, not fixtures):
```python
# tests/test_toolsets.py:11-18
def _dummy_handler(args, **kwargs):
    return "{}"


def _make_schema(name: str, description: str = "test tool"):
    return {
        "name": name,
        "description": description,
        "parameters": {"type": "object", "properties": {}},
    }
```

Use leading-underscore helper functions for in-file factories. Avoid pytest fixtures for one-off object construction — they're harder to parameterize and read.

**Fake servers** live in `tests/fakes/` (currently just `fake_ha_server.py` for Home Assistant webhook testing). Add a new `tests/fakes/fake_<service>.py` when multiple test files need the same mock HTTP/WS server.

## Coverage

**Requirements:** None enforced. No `coverage` / `pytest-cov` dependency declared. CI does not gate on coverage thresholds.

**View Coverage:** Not applicable — run an ad-hoc coverage report manually if needed:
```bash
.venv/bin/python -m pytest --cov=agent --cov=hermes_cli --cov-report=term-missing tests/agent/
```

## Test Types

**Unit Tests (default):**
- Live under `tests/test_*.py` and `tests/<package>/test_*.py`.
- Run by `scripts/run_tests_parallel.py` (the default suite).
- Fully hermetic: no real network, no real APIs, no real FS writes outside `tmp_path`.
- Example: `tests/test_hermes_logging.py` — exercises the real `setup_logging()` against a tempdir, asserts handler counts and rotation behavior.

**Integration Tests (opt-in via marker):**
- Marked `@pytest.mark.integration` — excluded by default via `addopts = "-m 'not integration'"`.
- Require external services (real API keys, Modal sandbox, docker daemon).
- Run in dedicated CI jobs: `tests/integration/`, `tests/docker/`.
- Run locally with `python -m pytest -m integration tests/`.

**E2E Tests (`tests/e2e/`):**
- Excluded from the default suite via `_SKIP_PARTS = {"integration", "e2e", "docker"}` (`scripts/run_tests_parallel.py:72`).
- Exercise full async message flows: `adapter.handle_message(event) → background task → GatewayRunner._handle_message → adapter.send()` — no LLM, no real platform connections.
- `tests/e2e/conftest.py` mocks `telegram` and `discord` modules via `sys.modules.setdefault`.
- CI: `.github/workflows/tests.yml` runs `python -m pytest tests/e2e/ -v --tb=short` in a dedicated job.

**Stress / Property Tests (`tests/stress/`):**
- Concurrency, mixed-workload, race-condition, property-fuzzing, and subprocess-e2e tests.
- Files: `test_concurrency.py`, `test_concurrency_reclaim_race.py`, `test_property_fuzzing.py`, `test_benchmarks.py`, `test_atypical_scenarios.py`, `test_subprocess_e2e.py`.
- Has its own `tests/stress/conftest.py` and a `_fake_worker.py` helper.

**Docker-image tests (`tests/docker/`):**
- Run against a freshly-built `nousresearch/hermes-agent:test` image via `HERMES_TEST_IMAGE` (avoiding rebuild).
- Live in their own CI job in `.github/workflows/docker-publish.yml` because the session-scoped `built_image` fixture's 3-7min build exceeds the 180s per-test pytest-timeout cap.

## Common Patterns

**Async Testing:**
```python
# Marker-based — pytest-asyncio
@pytest.mark.asyncio
async def test_generate_summary_async_handles_none_content():
    tc = _make_compressor()
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
        )
    )
    tc._get_async_client = MagicMock(return_value=mock_client)
    metrics = TrajectoryMetrics()

    summary = await tc._generate_summary_async("Turn content", metrics)

    assert summary == "[CONTEXT SUMMARY]:"
```
Use `AsyncMock` for async callables; `await` the result inside the test body. The autouse `_ensure_current_event_loop` fixture (`tests/conftest.py:451`) installs a loop so sync tests that internally call `asyncio.get_event_loop().run_until_complete(...)` still work.

**Error / Exception Testing:**
```python
def test_exception_returns_json_error():
    # Even if something goes wrong, should return valid JSON
    result = handle_function_call("web_search", None)  # None args may cause issues
    parsed = json.loads(result)
    assert isinstance(parsed, dict)
    assert "error" in parsed
    assert len(parsed["error"]) > 0
```
For tests that must assert a specific exception is raised, use `pytest.raises`:
```python
with pytest.raises(RuntimeError, match="live-system guard"):
    ...
```

**Catalog-parity testing** (i18n-specific, parametrized over every supported locale):
```python
# tests/agent/test_i18n.py:44-52
@pytest.mark.parametrize("lang", [l for l in i18n.SUPPORTED_LANGUAGES if l != "en"])
def test_catalog_keys_match_english(lang: str):
    """Every non-English catalog must have exactly the same key set as English."""
    en_keys = set(_flatten(_load_raw("en")).keys())
    lang_keys = set(_flatten(_load_raw(lang)).keys())
    missing = en_keys - lang_keys
    extra = lang_keys - en_keys
    assert not missing, f"{lang}.yaml missing keys: {sorted(missing)}"
    assert not extra, f"{lang}.yaml has keys not in en.yaml: {sorted(extra)}"
```

**Module-reload testing** (when the module's import has side effects):
```python
# tests/test_trajectory_compressor.py:19-30
def test_import_loads_env_from_hermes_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / ".env").write_text("OPENROUTER_API_KEY=from-hermes-home\n", encoding="utf-8")

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    sys.modules.pop("trajectory_compressor", None)
    importlib.import_module("trajectory_compressor")

    assert os.getenv("OPENROUTER_API_KEY") == "from-hermes-home"
```

## Test Markers

Registered markers (`pyproject.toml:252-255` and `tests/conftest.py:527-534`):
- **`@pytest.mark.integration`** — opt-in; requires external services. Excluded by default.
- **`@pytest.mark.real_concurrent_gate`** — opts out of an autouse stub that disables `_detect_concurrent_hermes_instances`. Used by tests that genuinely exercise the concurrent-instance detector.
- **`@pytest.mark.live_system_guard_bypass`** — opts out of the `_live_system_guard` autouse fixture. Use only for tests that need real signal delivery (e.g. PTY tests that SIGINT their own child).
- **`@pytest.mark.asyncio`** — pytest-asyncio marker for async tests.

Add new markers via `config.addinivalue_line("markers", ...)` in a `pytest_configure` hook (see `tests/conftest.py:527-534`), and declare them in `pyproject.toml:252` so they're recognized project-wide.

## Invariants Enforced by the Suite

These are the load-bearing invariants codified in `tests/conftest.py:1-20`:

1. **No credential env vars.** ~150 provider/credential env vars are unset before every test. Local developer keys cannot leak into assertions.
2. **Isolated HERMES_HOME.** Points to a per-test tempdir. Code reading `~/.hermes/*` via `get_hermes_home()` cannot see the real one.
3. **Deterministic runtime.** `TZ=UTC`, `LANG=C.UTF-8`, `PYTHONHASHSEED=0`.
4. **No `HERMES_SESSION_*` inheritance** — the agent's current gateway session must not leak into tests.

## Where to Add New Tests

**For a new module `<module>.py` at the repo root:** add `tests/test_<module>.py`.

**For a new module `<package>/<module>.py`:** add `tests/<package>/test_<module>.py`.

**For a regression test on a specific bug:** add a `tests/test_<area>.py` test named `test_<issue>_<symptom>` and cite the issue/PR in the docstring. Examples: `test_install_sh_symlink_stomp.py`, `test_install_sh_pythonpath_sanitization.py`.

**For a test requiring a fake HTTP/WS server:** add the server to `tests/fakes/` and import it from the test file.

**For an integration test (requires real API):** add under `tests/integration/` and mark `@pytest.mark.integration`. It will be skipped by default and run in a dedicated CI job.

**For an e2e platform test:** add under `tests/e2e/` and use the mock-install helpers from `tests/e2e/conftest.py`.

---

*Testing analysis: 2026-06-14*
