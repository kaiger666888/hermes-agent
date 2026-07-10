---
phase: 81-xcut-04b-cloud-engine-bootstrap
reviewed: 2026-07-10T19:30:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 81: Code Review Report

**Reviewed:** 2026-07-10T19:30:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the XCUT-04b Cloud Engine Bootstrap deliverables: the opt-in check script (`check_cloud_engine_optin.py`), its test suite, and the bootstrap reference doc. The script is well-structured and the test coverage is broad (23 tests, all passing), but two BLOCKER issues exist:

1. **Crash on non-dict `cloud_engines` block** — the extraction logic at lines 150-164 sits OUTSIDE the try/except, violating the documented "NEVER crashes" contract (D-06).
2. **Routing logic mismatch** — `TRANSITION_ENGINE_MAP["motion_vector_match"]` omits Vidu as a cloud fallback, contradicting `transition-engine-routing.md` which lists "Hailuo / Vidu" as co-primary engines.

Additional warnings cover doc inconsistencies (TRANS-10 deferral version contradicts itself within the same file), the confusing `primary_engine` semantics in fallback cases, a stray `verified_date:` line in the bootstrap doc, and the missing sys.path bootstrap (mirrors sibling pattern but still fragile).

## Critical Issues

### CR-01: Crash on non-dict `cloud_engines` block violates "NEVER crashes" contract (D-06)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py:150-164`
**Issue:** The try/except at lines 138-148 wraps the YAML load and the `config.get("cloud_engines")` call, but the value-extraction block at lines 150-164 is OUTSIDE the try/except. If the operator writes a non-dict value for `cloud_engines` (e.g., `cloud_engines: [a, b]` as a list, `cloud_engines: "foo"` as a string, or `cloud_engines: 42` as a scalar), `cloud_block` will be a `CommentedSeq` / string / int, and line 152 `cloud_block.get("hailuo_api_key")` raises `AttributeError`, crashing the script with a traceback.

This directly violates the documented contract on line 121: *"NEVER crashes — informational only."* The docstring (lines 119-122) and D-06 explicitly require graceful degradation to defaults on any config malformation. Verified via reproduction: `cloud_engines: [a, b]` in YAML produces `CommentedSeq` which has no `.get()` method.

The test suite does not cover this case — `test_invalid_yaml` only tests corrupt YAML syntax (parse failure), not a successfully-parsed but wrongly-typed `cloud_engines` value.

**Fix:** Wrap the extraction block in the existing try/except (preferred — single guard for all config-read failures), OR add an `isinstance(cloud_block, dict)` guard before extraction:

```python
# Option A: extend the existing try/except to cover extraction
    if config_path.exists():
        try:
            yaml = YAML()
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.load(f)
            if config is not None and isinstance(config, dict):
                cloud_block = config.get("cloud_engines")
                if cloud_block is not None and not isinstance(cloud_block, dict):
                    logger.warning(
                        "cloud_engines block is %s, expected dict — ignoring",
                        type(cloud_block).__name__,
                    )
                    cloud_block = None
        except Exception as exc:
            logger.warning(
                "Failed to read cloud_engines from config.yaml: %s", exc
            )
            cloud_block = None
```

Also add a test: `test_cloud_engines_is_list` / `test_cloud_engines_is_string` writing a non-dict block and asserting defaults are returned without crash.

### CR-02: `motion_vector_match` routing omits Vidu fallback, contradicts routing doc

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py:76`
**Issue:** `TRANSITION_ENGINE_MAP["motion_vector_match"]` is `("hailuo", "ffmpeg_motion_based_cut")` — Vidu is absent. The companion routing doc `transition-engine-routing.md:31` declares the primary engine as "Hailuo / Vidu (motion-vector generation is cloud-native strength; opt-in via `cloud_engines.hailuo_api_key` / `cloud_engines.vidu_api_key`)". Both Hailuo and Vidu are listed as cloud options with ffmpeg motion-based cut as the final fallback.

Consequence: if the operator opts in Vidu but not Hailuo, the script reports `motion_vector_match` as unavailable (falling back to ffmpeg), when per the routing doc Vidu should serve as the cloud engine. The operator sees misleading availability data. Test 13 (`test_all_engines_opted_in`) only checks the all-opted-in case and does not catch this because it doesn't test the vidu-only scenario for `motion_vector_match`.

**Fix:** Add `"vidu"` to the chain between hailuo and the ffmpeg fallback:

```python
TRANSITION_ENGINE_MAP: dict[str, tuple[str, ...]] = {
    "match_cut_shared_object": ("wan22", "ffmpeg_manual_cut"),
    "match_cut_shared_landscape": ("hailuo", "vidu", "ffmpeg_manual_cut"),
    "motion_vector_match": ("hailuo", "vidu", "ffmpeg_motion_based_cut"),  # vidu added
}
```

Add a test asserting vidu acts as cloud fallback for `motion_vector_match` when hailuo is not opted in (mirror `test_hailuo_not_opted_vidu_fallback` but for `motion_vector_match`).

## Warnings

### WR-01: `primary_engine` column shows active engine, not primary, when fallback triggers — misleading Rich table

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py:325`
**Issue:** Line 325 sets `"primary_engine": primary if available else active_engine`. When the primary engine is not opted in, `primary_engine` is overwritten with `active_engine` (the fallback). The Rich table column is labeled "Primary Engine" (line 389), but the cell displays the fallback engine, not the primary.

Example: for `match_cut_shared_object` when wan22 is not installed, the table shows `Primary Engine = ffmpeg_manual_cut`, `Available = No`, `Fallback = fallback: ffmpeg_manual_cut`. The operator sees "Primary Engine: ffmpeg_manual_cut" + "Available: No" — internally contradictory. The column name implies "what the primary engine IS", but the cell reports what WILL BE USED, while `Available=False` signals the primary is absent.

Tests are silent on this: `test_hailuo_not_opted_vidu_fallback` asserts `available is False` and vidu in fallback, but does not assert `primary_engine` value. `test_no_cloud_engines_ffmpeg_fallback` asserts `available is False` and ffmpeg in fallback, also silent on `primary_engine`.

**Fix:** Either (a) always report the true primary in `primary_engine` regardless of availability (rename column to "Primary Engine (declared)"), or (b) rename the field to `active_engine` and update the column label to "Active Engine":

```python
# Option (a): keep primary_engine as the declared primary, always
transitions.append({
    "transition_method": method,
    "primary_engine": primary,  # declared primary, even if not available
    "available": available,
    "fallback": fallback_desc or "—",
})
```

### WR-02: `transition-engine-routing.md` internally contradicts TRANS-10 deferral version (v15+ vs v16+)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/transition-engine-routing.md:143`
**Issue:** The same doc states TRANS-10 is deferred to "v15+" on lines 77 and 97, but line 143 says "deferred to v16+". The bootstrap doc (`cloud-engine-bootstrap.md:210`) also says "v16+". The operator reading this doc cannot determine which milestone TRANS-10 targets.

**Fix:** Pick one version and apply it consistently across both docs. Given the bootstrap doc (the newer deliverable) says v16+, update lines 77, 93, and 97 of `transition-engine-routing.md` to say "v16+":

```markdown
**Declarative routing only — NO runtime LLM decisions (TRANS-10 deferred to v16+).**
```

### WR-03: Missing sys.path bootstrap — script relies on editable install of hermes-agent

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py:37`
**Issue:** The script imports `from hermes_constants import get_hermes_home` at line 37, but `hermes_constants.py` does not exist anywhere in the kais-hermes-skills repo (verified via `find`). The module only lives in `/data/workspace/hermes-agent/hermes_constants.py`. The sibling script `apply_vision_verify_thresholds.py:79-84` has a sys.path bootstrap block (even though it suffers the same fragility — the bootstrap inserts kais-hermes-skills root, not hermes-agent root). `check_cloud_engine_optin.py` has NO bootstrap.

The script currently works only because the developer's environment has `pip install -e .` on hermes-agent (editable install exposes `hermes_constants` globally via `__editable__.hermes_agent-0.15.1.finder.__path_hook__`). In a fresh CI container, another developer's machine, or a deployment without the editable install, running `python scripts/check_cloud_engine_optin.py` raises `ModuleNotFoundError: No module named 'hermes_constants'`.

This is NOT a hard crash in the current dev environment, but it is a latent portability defect. The script is documented as a standalone CLI tool (`python scripts/check_cloud_engine_optin.py`) and will fail in any environment where hermes-agent is not pip-installed.

**Fix:** Either (a) add a sys.path bootstrap mirroring `apply_vision_verify_thresholds.py:79-84` (inserts `_REPO_ROOT` but this still won't find hermes_constants — needs to also locate the hermes-agent sibling repo), or (b) vendor a minimal `get_hermes_home()` fallback into the script (e.g., `os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))`), or (c) document that hermes-agent must be pip-installed as a prerequisite in the bootstrap doc's Verification section.

### WR-04: Stray `verified_date: 2026-07` line in bootstrap doc prose — invalid YAML

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md:6`
**Issue:** Line 6 contains `verified_date: 2026-07` as a bare line in the markdown body (between `**Last-verified:** 2026-07-10` on line 5 and `## Summary` on line 8). This is not valid YAML frontmatter (no `---` delimiters) and looks like a stray metadata field that was intended for frontmatter but ended up in prose. It renders as literal text in the rendered markdown.

**Fix:** Either move it into a proper YAML frontmatter block at the top of the file (with `---` delimiters), or delete it (the `**Last-verified:**` field on line 5 already carries the verification date):

```markdown
# Either delete line 6, or add frontmatter:
---
verified_date: 2026-07
last_verified: 2026-07-10
---
```

### WR-05: `_ENV_VAR_ALIASES` is private but `ENV_VAR_MAP` is public — inconsistent API surface

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py:60-71`
**Issue:** `ENV_VAR_MAP` (line 60) is exported in `__all__` (line 46); `_ENV_VAR_ALIASES` (line 68) is private (underscore prefix, not in `__all__`). Both are configuration constants that downstream consumers (e.g., a routing subagent) may need to enumerate accepted env vars. A consumer that reads `ENV_VAR_MAP` to list accepted env vars will miss `MINIMAX_API_KEY` (the alias), producing an incomplete picture. If a downstream routing module needs to validate env var names, it cannot access the alias list through the public API.

**Fix:** Either (a) rename to `ENV_VAR_ALIASES` (no underscore) and add to `__all__`, or (b) expose a single combined lookup function `get_accepted_env_vars(engine) -> list[str]` that merges primary + aliases:

```python
def get_accepted_env_vars(engine: str) -> list[str]:
    """Return primary + alias env var names for an engine."""
    primary = ENV_VAR_MAP.get(engine)
    aliases = _ENV_VAR_ALIASES.get(engine, [])
    return ([primary] if primary else []) + aliases
```

## Info

### IN-01: `main` imported in test but never called directly — unused import

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py:56`
**Issue:** The test file imports `main` (line 56) but never calls `main()` directly — all CLI tests use `subprocess.run`. The import is dead. Harmless but adds noise.

**Fix:** Remove `main` from the import list on line 51-57.

### IN-02: No test for whitespace-only API key in config

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py`
**Issue:** The script handles whitespace-only keys correctly (`str(hailuo_val).strip()` on line 156 filters them out), but no test verifies this. A config with `hailuo_api_key: "   "` (whitespace only) should fall through to env var fallback, not be treated as opted-in. Coverage gap.

**Fix:** Add a test:

```python
def test_whitespace_only_key_in_config(self, tmp_path, monkeypatch):
    """Config has whitespace-only hailuo_api_key → treated as not set."""
    _write_config(tmp_path, {"hailuo_api_key": "   "})
    monkeypatch.setattr(optin, "get_hermes_home", lambda: str(tmp_path))
    monkeypatch.delenv("HAILUO_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    config = load_cloud_engines_config()
    assert config["hailuo_api_key"] is None
    assert config["_source"]["hailuo"] == "not_set"
```

### IN-03: No test for `wan22_comfyui_node_enabled` as non-boolean (e.g., string "true")

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py`
**Issue:** The script uses strict `is True` check (line 162). If an operator writes `wan22_comfyui_node_enabled: "true"` (quoted string) or `wan22_comfyui_node_enabled: True` (capital T, which ruamel.yaml YAML 1.2 parses as string, not boolean), the opt-in silently fails. No test documents this strictness. An operator who writes `"yes"` or `"True"` will be confused why the engine shows as not opted in.

**Fix:** Add a test documenting the strict-boolean requirement:

```python
def test_wan22_string_true_not_opted_in(self, tmp_path, monkeypatch):
    """wan22_comfyui_node_enabled: 'true' (string) → NOT opted in (strict bool)."""
    _write_config(tmp_path, {"wan22_comfyui_node_enabled": "true"})
    monkeypatch.setattr(optin, "get_hermes_home", lambda: str(tmp_path))
    config = load_cloud_engines_config()
    assert config["wan22_comfyui_node_enabled"] is False
```

### IN-04: Bootstrap doc example calculation uses "15 cloud transitions" while notes say "10-20" — minor ambiguity

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md:255,279`
**Issue:** The cost table (line 255) uses "15 cloud transitions per episode" as the basis. The notes section (line 279) says "A typical 213-shot episode may have only 10-20 cloud-routed transitions." The 15 figure is within range but the two sections use different framings (fixed vs range) without cross-reference. Minor ambiguity for an operator filling in the worksheet.

**Fix:** Add a parenthetical in the table: "15 cloud transitions (typical — adjust to your episode's actual count; see Notes below)".

---

_Reviewed: 2026-07-10T19:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
