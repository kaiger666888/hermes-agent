# Coding Conventions

**Analysis Date:** 2026-06-14

This document describes the conventions that production code and tests in the
hermes-agent monorepo follow. It is written for future Claude instances adding
code to the repo — follow these patterns when writing or editing files.

## Naming Patterns

**Files (Python):**
- `snake_case.py` for all modules. Examples: `error_classifier.py`, `hermes_logging.py`, `trajectory_compressor.py`, `run_agent.py`.
- Top-level modules live at the repo root (`cli.py`, `utils.py`, `hermes_state.py`, `model_tools.py`, `toolsets.py`). Subpackage modules live under their package (`agent/insights.py`, `gateway/session.py`, `hermes_cli/config.py`).
- Test files: `tests/test_<module>.py` or `tests/<package>/test_<topic>.py`. Examples: `tests/test_hermes_logging.py`, `tests/agent/test_i18n.py`, `tests/test_trajectory_compressor.py`.
- Test class files: `tests/test_<thing>.py` containing one or more `class Test<Thing>:` groups.

**Files (TS/JS):** Live under `apps/`, `website/`, `web/`, `ui-tui/`. Names are `kebab-case.ts` / `PascalCase.tsx` per component. Not the focus of this Python-centric map; conventions here apply to the Python surface.

**Functions:**
- `snake_case` for all functions and methods. Examples: `setup_logging()`, `classify_api_error()`, `get_default_hermes_root()`, `_extract_status_code()`.
- Private helpers are prefixed with a single underscore: `_classify_402()`, `_load_catalog()`, `_normalize_lang()`.
- Async functions follow the same naming; no `async_` prefix or `_async` suffix convention. Callers know they are async from `await`.

**Variables:**
- `snake_case` for locals and module globals. Module-level constants are `UPPER_SNAKE_CASE`: `SUPPORTED_LANGUAGES`, `DEFAULT_LANGUAGE`, `_NOISY_LOGGERS`, `_CREDENTIAL_SUFFIXES`, `TRUTHY_STRINGS`.
- Module-private singletons are prefixed `_`: `_logging_initialized`, `_session_context`, `_catalog_cache`.

**Types & Classes:**
- `PascalCase` for classes: `ClassifiedError`, `FailoverReason`, `CompressionConfig`, `TrajectoryMetrics`, `InsightsEngine`.
- Enums subclass `enum.Enum` with lowercase values: `FailoverReason.auth = "auth"`, `FailoverReason.context_overflow = "context_overflow"`.
- Dataclasses for structured records — see `@dataclass class ClassifiedError` in `agent/error_classifier.py:69`.
- Test classes: `class TestXxx:` with methods `test_<scenario>`. See `tests/test_hermes_constants.py:18` (`class TestGetDefaultHermesRoot:`).

**Type hints:**
- Public API functions and class attributes are type-hinted. Internal helpers may omit annotations when obvious.
- Mixing legacy and PEP 604 syntax is acceptable: `agent/i18n.py` uses `str | None` (modern); `agent/error_classifier.py` uses `from __future__ import annotations` + `Optional[int]`. Prefer `from __future__ import annotations` at the top of new modules to enable PEP 604 / PEP 585 generics on Python 3.11.
- Return-type annotations are encouraged on public functions: `def get_language() -> str:`, `def t(key: str, ...) -> str:`.

## Code Style

**Formatting:**
- **No Black / autopep8 / yapf.** Formatting is enforced manually; the only automated linter is **Ruff** with a very narrow ruleset.
- Indent: 4 spaces. Line length: ~100 chars (soft; longer lines tolerated when comments explain non-obvious code).
- Quoting: double quotes for strings (`"foo"`, `"PascalCase"`). Single quotes appear occasionally in older code; do not introduce new ones.

**Linting:**
- **Ruff** `0.15.10` (declared in `[project.optional-dependencies] dev`). Config in `pyproject.toml:270`:
  ```toml
  [tool.ruff]
  preview = true  # required for PLW1514 (unspecified-encoding) — preview rule

  [tool.ruff.lint]
  select = ["PLW1514"]   # the ONLY enforced rule
  ```
- **PLW1514 (`unspecified-encoding`)** is the single load-bearing rule. It forces every `open()` / `read_text()` / `write_text()` to pass an explicit `encoding="utf-8"`. Rationale (from `pyproject.toml:274`): Windows defaults to cp1252 and silently corrupts non-ASCII content. Examples of compliant usage from `agent/i18n.py:141`:
  ```python
  with path.open("r", encoding="utf-8") as f:
      raw = yaml.safe_load(f) or {}
  ```
- Per-file ignores (`pyproject.toml:283`):
  - `tests/**` — may intentionally exercise locale-encoding edge cases.
  - `skills/**`, `optional-skills/**`, `plugins/**` — partially user-authored.
- **Type checker:** `ty` `0.0.21` (Astral's experimental type checker). Runs in CI as an **advisory diff** (not blocking). Configuration:
  ```toml
  [tool.ty.environment]
  python-version = "3.13"
  [tool.ty.rules]
  unknown-argument = "warn"
  redundant-cast = "ignore"
  ```
- CI workflow: `.github/workflows/lint.yml` — `Lint (ruff + ty)`. The `ruff check .` step blocks merge; the `ty` step is advisory.

**Style invariants to apply:**
- Add `encoding="utf-8"` to every text-mode `open()`, even in tests where it would be optional under Ruff's ignore. Defensive against Windows.
- No `from x import *`. Always explicit imports.
- Use `from __future__ import annotations` at the top of new modules for forward-compat type syntax.

## Import Organization

**Order (observed in `agent/i18n.py:31-38`, `agent/error_classifier.py:12-17`, `hermes_logging.py:30-37`):**
1. `from __future__ import annotations` (when used — top of file)
2. Standard library (`import logging`, `import os`, `import threading`, `from pathlib import Path`, `from typing import Any`)
3. Third-party (`import yaml`, `import pytest`)
4. Local application (`from hermes_constants import get_hermes_home`, `from agent.redact import RedactingFormatter`)

Within each group, imports are alphabetical, with `import x` preceding `from x import y`.

**Lazy imports for circular-dependency avoidance:** Heavy or cycle-prone imports happen inside functions, not at module top. Example from `hermes_logging.py:223`:
```python
def setup_logging(...):
    ...
    # Lazy import to avoid circular dependency at module load time.
    from agent.redact import RedactingFormatter
```
And `hermes_logging.py:348`:
```python
def __init__(self, *args, **kwargs):
    from hermes_cli.config import is_managed
    self._managed = is_managed()
```
**Do this for new modules that touch both `agent.*` and `hermes_cli.*`** — these two packages have known import cycles.

**Path Aliases:** None. All imports are absolute (`from agent.error_classifier import ...`). No `sys.path` hacks in production code; tests do insert `PROJECT_ROOT` into `sys.path` once in `tests/conftest.py:30`.

## Error Handling

**Centralized error classification:** API errors flow through `agent/error_classifier.py`. Production code (`run_agent.py`, `agent/conversation_loop.py`) calls `classify_api_error()` instead of inline string matching:

```python
from agent.error_classifier import classify_api_error, ClassifiedError

classified: ClassifiedError = classify_api_error(
    exc,
    provider=provider_name,
    model=model_slug,
    approx_tokens=token_count,
    context_length=context_window,
)
if classified.should_compress:
    # trigger context compression path
elif classified.should_rotate_credential:
    # rotate from credential pool
elif not classified.retryable:
    # abort or fallback
```

The classifier returns a `@dataclass ClassifiedError` (`agent/error_classifier.py:69`) with boolean recovery hints (`retryable`, `should_compress`, `should_rotate_credential`, `should_fallback`). Pattern lists (`_BILLING_PATTERNS`, `_RATE_LIMIT_PATTERNS`, `_CONTEXT_OVERFLOW_PATTERNS`, etc.) are module-level frozensets/lists — extend those rather than adding new `if "..." in msg:` branches at call sites.

**try/except usage:**
- Catch specific exception types, not bare `except:`. The classifier walks `__cause__` / `__context__` chains (`error_classifier.py:1219-1233`) — preserve chains with `raise X from cause`.
- Use `(ExcA, ExcB, ExcC)` tuples for related exceptions. Example from `utils.py:277-280`:
  ```python
  try:
      return json.loads(text)
  except (json.JSONDecodeError, TypeError, ValueError):
      return default
  ```
- **`except Exception:` is acceptable** for best-effort fallback paths where the goal is "don't crash". Always log the exception. Example from `agent/i18n.py:143-147`:
  ```python
  try:
      import yaml
      with path.open("r", encoding="utf-8") as f:
          raw = yaml.safe_load(f) or {}
  except Exception as exc:
      logger.warning("Failed to load i18n catalog %s: %s", path, exc)
      ...
      return {}
  ```
- `except BaseException:` is used **only** when cleanup must run even on `KeyboardInterrupt`/`SystemExit`. Example: temp-file cleanup in `utils.py:141-148` re-raises after unlinking the partial temp file. Do not adopt this pattern casually.
- On `except`, **always bind the exception to a name** (`except X as exc:`) and include it in the log message (`logger.warning("...: %s", exc)`). Do not swallow silently.

**Atomic file writes:** Use `utils.atomic_json_write()` / `utils.atomic_yaml_write()` / `utils.atomic_roundtrip_yaml_update()` for any write to a config/state file the user might also edit. These helpers use `tempfile.mkstemp` + `fsync` + `os.replace`, preserve symlinks, and restore file modes. See `utils.py:61-264`.

**Defensive `getattr` for SDK exceptions:** Different SDKs expose status/body/code under different attribute names. Walk the chain defensively (see `_extract_status_code` at `error_classifier.py:1217-1233`).

## Logging

**Framework:** Python stdlib `logging`. **No structured-logging library** (no structlog, no loguru). All loggers are name-scoped via `logging.getLogger(__name__)` at the top of every module:

```python
import logging
logger = logging.getLogger(__name__)
```

**Entry point:** `hermes_logging.setup_logging()` (`hermes_logging.py:166`) — called once at CLI/gateway startup. Idempotent (`_logging_initialized` sentinel). Creates rotating file handlers under `~/.hermes/logs/`:
- `agent.log` — INFO+, all activity (catch-all)
- `errors.log` — WARNING+, triage log
- `gateway.log` — gateway-component records only (`mode="gateway"`)
- `gui.log` — dashboard / TUI-gateway records only (`mode="gui"`)

**Secrets redaction:** All handlers wrap a `RedactingFormatter` (`agent/redact.py`, lazy-imported). Never log raw API keys, tokens, or `auth.json` payloads. The formatter scrubs known secret patterns at emit time.

**Session context:** `set_session_context(session_id)` / `clear_session_context()` (`hermes_logging.py:76-87`) attach a thread-local `[session_id]` tag to every subsequent log line on that thread, via a global `LogRecord` factory (`_install_session_record_factory()`, installed at import time). Call `set_session_context()` at the start of `run_conversation()`.

**Patterns:**
- Use `logger.debug()` for routine diagnostic noise (HTTP retries, keychain probes, cache hits). See `agent/anthropic_adapter.py:826,830,840,892,957,980,990,993`.
- Use `logger.warning()` for recoverable misconfiguration (missing i18n catalog, failed chmod, refresh failure).
- Use `logger.error()` / `logger.exception()` only for genuine failures that need operator attention. Most API errors flow through `error_classifier.py` and surface as warnings with the classified reason.
- **Lazy %-formatting** — always pass args positionally: `logger.warning("Failed: %s", exc)`, never f-strings in log calls. Lets the logging framework skip formatting when the level is filtered out.
- Third-party noisy loggers (`openai`, `httpx`, `urllib3`, `asyncio`, `modal`, `websockets`, etc.) are pinned to `WARNING` — see `_NOISY_LOGGERS` at `hermes_logging.py:54-69`. Add new chatty libraries there rather than filtering per-call.

**Component routing:** `_ComponentFilter` (`hermes_logging.py:130-142`) routes records by logger-name prefix. Prefixes are declared in `COMPONENT_PREFIXES` (`hermes_logging.py:147-159`): `gateway`, `agent`, `tools`, `cli`, `cron`, `gui`. **Name new gateway-platform loggers `gateway.platforms.<name>`** so they route to `gateway.log` correctly.

## i18n

**Scope (deliberately thin):** Only the highest-impact static user-facing strings are translated — CLI approval prompts, gateway slash-command replies, restart-drain notices. Agent-generated output, log lines, error tracebacks, tool outputs, and slash-command descriptions stay in English. See the docstring on `agent/i18n.py:1-29`.

**Catalog files:** `locales/<lang>.yaml` at repo root. Flat dotted-key space (`approval.choose_long`, `gateway.draining`). YAML nesting is for human readability; the loader flattens it.

**Supported languages:** `SUPPORTED_LANGUAGES` tuple in `agent/i18n.py:42-45` — `en`, `zh`, `zh-hant`, `ja`, `de`, `es`, `fr`, `tr`, `uk`, `af`, `ko`, `it`, `ga`, `pt`, `ru`, `hu`. Locale files: `locales/{en,zh,zh-hant,ja,de,es,fr,tr,uk,af,ko,it,ga,pt,ru,hu}.yaml`.

**Usage pattern** (`agent/i18n.py:208-249`):
```python
from agent.i18n import t

# current language (env > config > default)
print(t("approval.choose_long"))

# with str.format placeholders
print(t("gateway.draining", count=3))

# explicit override
print(t("approval.choose_long", lang="zh"))
```

**Language resolution order:**
1. Explicit `lang=` arg to `t()`
2. `HERMES_LANGUAGE` env var
3. `display.language` in `config.yaml`
4. `"en"` (baseline)

**Aliases:** `_LANGUAGE_ALIASES` (`i18n.py:50-81`) maps common alternate spellings (`"chinese" → "zh"`, `"japanese" → "ja"`, `"jp" → "ja"`, `"zh-CN" → "zh"`). Extend this rather than adding branches in callers.

**Adding a new language:**
1. Add the code to `SUPPORTED_LANGUAGES`.
2. Create `locales/<code>.yaml` mirroring `en.yaml`'s key structure exactly.
3. Add aliases to `_LANGUAGE_ALIASES` if users are likely to type a different spelling.

**Adding a new translatable string:**
1. Add the key to **every** `locales/*.yaml` in the same commit.
2. `tests/agent/test_i18n.py:38-52` enforces catalog parity — `test_all_locales_exist` and `test_catalog_keys_match_english` will fail the build if a locale is missing or has extra/missing keys.
3. `test_catalog_placeholders_match_english` (`tests/agent/test_i18n.py:55-74`) enforces that every translated value uses the same `{placeholder}` tokens as English — prevents runtime `KeyError` on bad translations.

**Cache invalidation:** `i18n._config_language_cached()` is `@lru_cache(maxsize=1)`; call `reset_language_cache()` (`i18n.py:186`) after `save_config()` if the process needs to pick up a changed `display.language`.

## Type Hints Usage

- **Required** on public functions and class `__init__` signatures. Encouraged on private helpers.
- Use `from __future__ import annotations` for forward references and PEP 604 unions (`str | None`) on Python 3.11+.
- Use `typing.Any` sparingly — prefer narrower types or generics.
- Module-level typed constants: `_CREDENTIAL_SUFFIXES: tuple[str, ...] = (...)` (`tests/conftest.py:57`), `_NOISY_LOGGERS` (`hermes_logging.py:54`).
- Frozen sets for lookup tables: `_TRANSPORT_ERROR_TYPES = frozenset({...})` (`error_classifier.py:365`).

## Docstring Style

**Module docstrings** are mandatory and substantive — they explain scope, rationale, and key invariants. Examples: `agent/error_classifier.py:1-10`, `hermes_logging.py:1-28`, `agent/i18n.py:1-29`, `tests/conftest.py:1-20`. A new module without a docstring is a style violation.

**Function docstrings** use a freeform summary line followed by an optional expanded section. Sphinx-style `Args:` / `Returns:` / `Raises:` sections appear in some modules (`hermes_logging.py:175-207`, `utils.py:97-108`); numpydoc-style `Parameters` / `Returns` sections appear in others (`i18n.py:209-225`). **Both are accepted**; pick one and stay consistent within a file.

**Block comments** are used heavily to explain *why* non-obvious code exists. Examples:
- The supply-chain pinning rationale at `pyproject.toml:14-33`.
- The live-system guard rationale at `tests/conftest.py:496-522`.
- The pattern-list ordering rationale at `error_classifier.py:533-547`.

When adding defensive code (a workaround, a CVE pin, a flake fix), include a block comment citing the issue/PR and the failure mode it prevents.

**Inline comments** use `#` with a single leading space. Emoji and box-drawing chars are used sparingly for section dividers within long files (`# ── Error taxonomy ───` at `error_classifier.py:22`).

## Function Design

- **Single responsibility.** The classifier pipeline in `error_classifier.py` is decomposed into `_classify_by_status`, `_classify_by_error_code`, `_classify_by_message`, `_classify_400`, `_classify_402` — each ~50 lines, testable in isolation.
- **Keyword-only args** for public functions with many optional knobs. Example: `setup_logging(*, hermes_home, log_level, max_size_mb, backup_count, mode, force)` at `hermes_logging.py:166`. Use `*` to force callers to name arguments.
- **Default to returning structured objects over tuples.** `ClassifiedError` dataclass (`error_classifier.py:69`) rather than `(reason, retryable, should_compress, ...)`.
- **Helpers return `None` to signal "no classification"**, which the caller treats as "try the next classifier". See `_classify_by_status` returning `Optional[ClassifiedError]` (`error_classifier.py:725-878`).
- **Size guideline:** Functions over ~80 lines are candidates for extraction. The codebase tolerates longer functions when they're a flat switch-dispatch (e.g. `_classify_by_status`), but pushes back on nested logic.

## Module Design

**Exports:** Use `__all__` for modules with a public surface. Example: `agent/i18n.py:252-258`:
```python
__all__ = [
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "t",
    "get_language",
    "reset_language_cache",
]
```
For modules where "everything starting with `_` is private" is obvious, `__all__` may be omitted.

**Barrel files:** Not used. Subpackages (`agent/`, `tools/`, `gateway/`, `hermes_cli/`) do not have an `__init__.py` that re-exports everything. Import the specific module path: `from agent.error_classifier import classify_api_error`, never `from agent import classify_api_error`.

**Module-level singletons:** Acceptable when they're genuinely process-global (logger caches, plugin managers, registries). Examples:
- `hermes_logging._logging_initialized` (`hermes_logging.py:42`)
- `agent/i18n._catalog_cache` + `_catalog_lock` (`i18n.py:83-84`)
- `tools/registry.registry` (the global `ToolRegistry`)

Tests reset these via `_reset_for_tests()` helpers or via `monkeypatch.setattr(module, "_singleton", None)` in autouse fixtures. See `tests/conftest.py:385-388` for the plugin-manager reset pattern.

## Skill File Conventions (SKILL.md)

Skills are markdown files with **YAML frontmatter**. The `movie-experts/*` skills (added 2026-06-01) follow the canonical schema. Path pattern: `skills/<category>/<skill-name>/SKILL.md` or `optional-skills/<category>/<skill-name>/SKILL.md`.

**Frontmatter schema:**
```yaml
---
name: style_genome              # required, snake_case, matches directory name
description: "<one-line summary>"  # required, double-quoted, includes role
version: 1.0.0                  # semver
author: Hermes Agent            # or individual author
license: MIT                    # SPDX identifier
platforms: [linux, macos, windows]   # list of supported platforms
prerequisites:
  tools: [hermes_llm]           # required runtime tools
metadata:
  hermes:
    tags: [...]                 # search/discovery tags (snake-case-with-hyphens)
    related_skills: [...]       # other skill `name`s this one collaborates with
    expert_id: <name>           # unique expert identifier (matches `name`)
    metrics: [...]              # measurable quality dimensions this expert owns
---
```

**`metadata.hermes` sub-schema** (the Hermes-specific extension):
- **`tags`**: List of lowercase hyphen-separated tags for skill search and discovery. Examples from `skills/movie-experts/style_genome/SKILL.md:12`: `[movie, style, director, genre, visual-dna, style-blending, cross-module]`.
- **`related_skills`**: List of `name`s of skills that this expert collaborates with in a pipeline. Drives cross-skill recommendation and DAG ordering. Example from `style_genome/SKILL.md:13`: `[screenplay, drawer, colorist, editor, composer, scene_builder, performer, continuity]`.
- **`expert_id`**: Stable identifier used by the worker-agent `/decide` endpoint to match an incoming request to this expert. Usually equal to `name`. Example: `expert_id: style_genome`.
- **`metrics`**: Quality dimensions the expert is accountable for, used by evaluation pipelines. Example from `style_genome/SKILL.md:15`: `[style_consistency, gene_extraction_accuracy, blend_coherence, cross_module_alignment]`.

**Body conventions** (from the 14 movie-experts skills):
- `# <Name> Expert (<Chinese name>)` — H1 with bilingual title.
- `## When to use this skill` — trigger conditions.
- `## Role & Philosophy` — 3-5 bullets.
- `## Core Capabilities` — bullet list.
- `## Output Format` — bulleted list of JSON artifact filenames this expert produces (`style_genome.json`, `style_blend_protocol.json`, ...).
- `## Key Parameters` — nested subsections per parameter group, with H3 (`###`) headers and bullet lists of ranges/defaults.

See `skills/movie-experts/style_genome/SKILL.md`, `skills/movie-experts/animator/SKILL.md`, `skills/movie-experts/editor/SKILL.md` for canonical examples.

## Anti-Patterns to Avoid

- **Bare `except:`** — always catch specific types or `except Exception:`.
- **`open()` without `encoding=`** — Ruff will block the merge.
- **`Path.home() / ".hermes"`** in production code — use `get_hermes_home()` from `hermes_constants` instead. The conftest fixture redirects `HERMES_HOME` per-test; `Path.home()` bypasses that and leaks into real `~/.hermes`.
- **`os.kill(pid, sig)` or `subprocess.run(["systemctl", "restart", ...])` in tests** without explicit mocking — the autouse `_live_system_guard` fixture (`tests/conftest.py:537-841`) raises `RuntimeError`. Mock both `find_gateway_pids` and `os.kill`, or mark the test with `@pytest.mark.live_system_guard_bypass`.
- **Inline string-matching for API errors** at call sites — route through `classify_api_error()`.
- **`f"..."` in `logger.x(...)` calls** — use `%s` positional args.

---

*Convention analysis: 2026-06-14*
