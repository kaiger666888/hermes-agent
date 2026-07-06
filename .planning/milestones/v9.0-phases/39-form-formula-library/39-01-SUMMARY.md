---
phase: 39-form-formula-library
plan: 01
subsystem: plugins/formula_library
tags: [plugin, pydantic, formula-library, lookup, tdd]
requires:
  - "Pydantic v2 (pydantic==2.13.4 — Hermes core dep, no new install)"
  - "plugins/review_gates/* (mirrored register(ctx) pattern)"
  - "hermes_cli/plugins.py PluginContext.register_tool API"
provides:
  - "plugins/formula_library/ plugin scaffold (FORM-01)"
  - "Pydantic Formula / FormulaLibrary / PlatformFit / Citation schema (FORM-02)"
  - "formula_lookup tool registration + FORMULA_LOOKUP_SCHEMA (FORM-04 lookup half)"
  - "lookup_formulas ranking engine (top-k by platform_fit, FORM-04)"
  - "load_library with module-level cache for default plugin library/ dir"
affects:
  - "Plan 39-02 (10 seed formulas) — schema.py validates every library/*.json"
  - "Plan 39-03 (SKILL.md wiring) — calls formula_lookup via _handle_formula_lookup"
  - "Phase 42 DATA (formula_tuning_loop) — write-back target uses FormulaLibrary"
tech-stack:
  added: []
  patterns:
    - "Standalone plugin pattern (kind: standalone, opt-in via plugins.enabled) — mirrors plugins/review_gates"
    - "Pydantic v2 Literal-typed enums for FORM-02 matrix axes (5 genres x 2 moods x 6 platforms x 5 hook types)"
    - "Lazy import in handler (_handle_formula_lookup imports lookup_formulas inside function body) for clean module load order"
    - "Module-level cache (_LIBRARY_CACHE) for default library dir; explicit library_dir arg bypasses cache for tests"
    - "Degrade-gracefully load_from_dir: per-file failures logged + skipped, never aborts whole load"
    - "Keyword-only args (* separator) on public lookup_formulas / load_library functions"
key-files:
  created:
    - plugins/formula_library/plugin.yaml
    - plugins/formula_library/__init__.py
    - plugins/formula_library/schema.py
    - plugins/formula_library/tools.py
    - plugins/formula_library/lookup.py
    - plugins/formula_library/tests/__init__.py
    - plugins/formula_library/tests/test_schema.py
    - plugins/formula_library/tests/test_lookup.py
  modified: []
decisions:
  - "D-39-01-1: Schema uses Literal types (not Enum) for FORM-02 matrix axes — Pydantic v2 Literal produces cleaner JSON-schema enum generation for tools.py + preserves Chinese string values without serialization wrappers."
  - "D-39-01-2: load_from_dir degrades gracefully on per-file failure (warning + skip) rather than failing fast — operator can fix one bad file without losing the rest of the library. Mirrors _discover_expert_ids pattern in agent/feedback_schema.py:117."
  - "D-39-01-3: Tie-break in lookup_formulas is formula_id ascending (deterministic for tests). eval_score was considered as a tiebreak but rejected — eval_score is null for all 10 seed formulas and adds nondeterminism once populated."
  - "D-39-01-4: Module-level cache (_LIBRARY_CACHE) keyed on default dir only; explicit library_dir bypasses cache. Tests reset _LIBRARY_CACHE = None in setup_method for isolation."
  - "D-39-01-5: _handle_formula_lookup lazy-imports lookup_formulas inside the function body so tools.py imports cleanly even before lookup.py exists (forward compatibility + avoids circular imports)."
metrics:
  duration: "~35 minutes"
  completed: "2026-06-26"
  tasks: 2
  files-created: 8
  files-modified: 0
  tests-passing: 34
---

# Phase 39 Plan 01: Formula Library Plugin Scaffold + Lookup Engine Summary

Shipped a discoverable Pydantic v2 formula_library plugin (scaffold + schema + ranking lookup engine) — the foundational layer Plans 02 (seed data) and 03 (SKILL.md wiring) build on. Schema validates all 10 of Plan 02's parallel-shipped seed formulas; lookup returns top-k ranked by platform_fit.

## What Was Built

### Plugin scaffold (FORM-01)
- **plugin.yaml** (7 lines): `name: formula_library`, `version: "0.1.0"`, `kind: standalone`, `provides_tools: [formula_lookup]`. Mirrors `plugins/review_gates/plugin.yaml` shape exactly.
- **__init__.py** (48 lines): exports `register(ctx)` entrypoint that iterates `_TOOLS` calling `ctx.register_tool(name=..., toolset="formula_library", schema=..., handler=..., check_fn=None, emoji=...)`. Identical pattern to `plugins/review_gates/__init__.py`.

### Pydantic v2 schema (FORM-02) — `schema.py`
All 11 FORM-02 fields validated:
- `formula_id: str`
- `genre: Literal["都市奇幻","悬疑反转","家庭情感","校园青春","职场商战"]`
- `mood: Literal["轻喜剧","虐心"]`
- `pacing: str`
- `hook_pattern: Literal["emotional","suspense","conflict","contrast","emotional_peak"]` (5 types per `three-second-hooks.md`)
- `characters: list[str]` (non-empty validator)
- `runtime_sec: int` (60–600 range validator)
- `platform_fit: list[PlatformFit]` (non-empty validator)
- `citation: Citation` (required — CLAUDE.md copyright hard-constraint)
- `verified_date: date`
- `eval_score: Optional[float] = None` (None default per FORM-02 spec; populated by v6.0 eval gate)

Nested models:
- **PlatformFit**: `platform: Literal["抖音","快手","B站","小红书","视频号","红果"]` + `fit_score: float` (0.0–1.0 validator).
- **Citation**: `source: str`, `source_type: Literal["notion","public-book","kais-benchmark"]`, `fair_use_status: Literal["verbatim-spec","paraphrased","derived-analysis"]`, `verified_date: date`.

`FormulaLibrary` helpers:
- `by_id(formula_id) -> Formula | None`
- `filter(*, genre, mood) -> list[Formula]` (strict exact-match)
- `load_from_dir(library_dir: Path) -> FormulaLibrary` classmethod — globs `*.json`, validates each via Formula, **degrades gracefully** on per-file failure (warning + skip, never aborts load). Missing dir → empty library.

### Lookup engine (FORM-04 lookup half) — `lookup.py`
- **`load_library(library_dir=None) -> FormulaLibrary`**: default = `Path(__file__).resolve().parent / "library"` with module-level cache `_LIBRARY_CACHE`; explicit `library_dir` bypasses cache.
- **`lookup_formulas(*, genre, mood, platform, top_k=3) -> list[Formula]`**: strict genre+mood filter, ranks by `platform_fit[platform].fit_score` desc, missing platform entry treated as 0.0, ties broken by `formula_id` ascending (deterministic for tests), empty library returns empty list (no exception).

### Tool handler — `tools.py`
- **`FORMULA_LOOKUP_SCHEMA`** dict: declares `genre` (enum 5), `mood` (enum 2), `platform` (enum 6), `top_k` (int default 3). Required: `[genre, mood, platform]`.
- **`_handle_formula_lookup(args)`**: validates required args, lazy-imports `lookup_formulas`, returns `tool_result({formulas, count, query})` on success or `tool_error({missing, received})` on missing args.

## Test Coverage (34 tests, all GREEN)

### test_schema.py (20 tests)
- **TestFormulaValidation** (13): valid formula, missing citation raises, invalid genre/mood/hook_pattern raises, fit_score out-of-range / negative raises, eval_score None/float/default behaviors, runtime_sec 60–600 range.
- **TestCitationValidation** (3): valid citation, invalid source_type raises, invalid fair_use_status raises.
- **TestFormulaLibrary** (4): by_id lookup (hit + miss), filter strict on genre+mood, load_from_dir skips invalid (graceful), load_from_dir missing dir returns empty.

### test_lookup.py (14 tests)
- **TestLookupRanking** (8): ranked by platform_fit descending, strict filter, empty result on no match, empty library, top_k respected, default top_k=3, ties broken by formula_id ascending, missing platform entry treated as 0.0.
- **TestLoadLibrary** (2): explicit dir bypasses cache, missing default dir returns empty.
- **TestHandlerDispatch** (4): tool_result envelope shape, missing required arg returns tool_error, top_k override, empty result returns empty list.

## TDD Gate Sequence (verified in git log)

| Gate | Commit | Message |
|------|--------|---------|
| RED  | `c00b750eb` | `test(phase-39-01): add failing tests for Formula schema + lookup engine` |
| GREEN Task 1 | `59745810c` | `feat(phase-39-01): plugin scaffold + Pydantic schema (FORM-01 + FORM-02)` |
| GREEN Task 2 | `4a12f8be8` | `feat(phase-39-01): lookup.py ranking engine (FORM-04 lookup half)` |

RED failed as expected (ModuleNotFoundError for `plugins.formula_library.{schema,lookup}`). Both GREENs flipped their respective test sets to passing. No REFACTOR needed — implementation is already minimal + clean.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test file authoring bugs in test_schema.py RED gate**
- **Found during:** Task 1 GREEN run
- **Issue:** Two test cases had authoring bugs: (a) `test_fit_score_out_of_range_raises` constructed `PlatformFit(fit_score=1.5)` directly, which raised *before* the `with pytest.raises` block (the raise was on the line setting `kw["platform_fit"]`, not inside the `with`); (b) `test_load_from_dir_skips_invalid` used `json.dumps(formula_kwargs, default=str)` which stringified nested `PlatformFit`/`Citation` Pydantic objects via `repr()` instead of serializing them as dicts.
- **Fix:** (a) Pass fit_score via raw dict `{"platform": "抖音", "fit_score": 1.5}` so validation runs at `Formula.model_validate` time inside the `with` block. (b) Build the valid Formula via `Formula.model_validate(...)` first, then `json.dumps(formula.model_dump(mode="json"))` for proper nested-dict serialization.
- **Files modified:** `plugins/formula_library/tests/test_schema.py` (only test file — no source changes)
- **Commit:** `59745810c`

### Race Condition with Parallel Plans (resolved, no plan deviations)

**2. [Operational] Parallel-plan git index race condition**
- **Context:** Plan 39-02 (Wave 1 parallel) and Phase 40 (parallel) committed concurrently with this plan, causing the initial Task 1 GREEN commit (`651e248a8`) to sweep up unrelated files from other plans' working trees (Plan 02's SUMMARY.md, Plan 02's modified PLAN.md, Phase 40's `plugins/review_gates/gates/`).
- **Resolution:** Reset the contaminated commit (`git reset --mixed HEAD~1`), cherry-picked Plan 02's legitimate SUMMARY commit (`477a8f308`) back onto history, re-staged only my Task 1 files (`git add -- <explicit paths>`), recommitted cleanly as `59745810c`. Plan 02's work is intact; Phase 40's work was committed independently by its own agent (`32605925b`).
- **Lesson:** When parallel agents share a branch, `git status --short` must be checked for already-staged files before each `git commit`. The CLAUDE.md "never use `git add -A`" rule is necessary but not sufficient — parallel agent staging must be filtered out.

No other deviations. Plan executed as written; scope held to `plugins/formula_library/{plugin.yaml,__init__.py,schema.py,tools.py,lookup.py,tests/}`. Zero edits to Plan 02 / Plan 03 / other-phase files.

## Quality Gates

- [x] All FORM-02 schema fields present with correct Pydantic types (11/11)
- [x] formula_lookup returns top-3 ranked by platform_fit (verified end-to-end against Plan 02 real seed data)
- [x] All tests GREEN (34/34: 20 schema + 14 lookup)
- [x] plugin.yaml valid against hermes_cli/plugins.py PluginManifest schema (kind=standalone, name/version/author/provides_tools fields present, parseable by existing loader)
- [x] Zero edits to Plan 39-02 / 39-03 / other-phase files (scope boundary held)

## End-to-End Verification

Verified the full chain against Plan 02's 10 parallel-shipped seed formulas:
```
schema name: formula_lookup
required: ['genre', 'mood', 'platform']
lib size: 10
top-3 results: ['urban-fantasy-light-01']  # only 1 都市奇幻/轻喜剧 seed
handler: count=1, top formula_id=urban-fantasy-light-01
handler error: formula_lookup requires genre
  registered: formula_lookup toolset=formula_library
OK end-to-end
```

All 10 Plan 02 seed formulas load cleanly via `FormulaLibrary.load_from_dir()`. 5 genres × 2 moods matrix coverage verified.

## Self-Check: PASSED

Files verified to exist:
- FOUND: plugins/formula_library/plugin.yaml
- FOUND: plugins/formula_library/__init__.py
- FOUND: plugins/formula_library/schema.py
- FOUND: plugins/formula_library/tools.py
- FOUND: plugins/formula_library/lookup.py
- FOUND: plugins/formula_library/tests/__init__.py
- FOUND: plugins/formula_library/tests/test_schema.py
- FOUND: plugins/formula_library/tests/test_lookup.py

Commits verified in git log:
- FOUND: c00b750eb (test — RED)
- FOUND: 59745810c (feat Task 1 — GREEN)
- FOUND: 4a12f8be8 (feat Task 2 — GREEN)
