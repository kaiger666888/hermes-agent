---
phase: 71-form
reviewed: 2026-07-09T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p11_video_render.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/_step14_reframe_math.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_form_factor.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/visual_executor/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/editor/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/character_designer/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/horizontal-screen-framing.md
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Phase 71: Code Review Report

**Reviewed:** 2026-07-09
**Depth:** standard
**Files Reviewed:** 13 (cross-repo: kais-hermes-skills @ HEAD 3c97902, baseline d9620369)
**Status:** issues_found

## Summary

Phase 71 (form-factor support v14.0) adds a `form_factor: Literal["landscape", "portrait"]` episode-level field, strict-enum validation, a 4-cell reframe matrix, dual-branch Form Factor Adaptation sections across 4 SKILL.md files, a new horizontal-screen-framing.md ref, and the canonical LTX MSR_FC default fix (17 → 41). The implementation is largely sound: the `__post_init__` validator is strict (no fuzzy matching), the `validate_form_factor_invariant` recursively rejects per-shot overrides, the XCUT-02 dual injection (`.task()` + `.constraints()`) is correctly applied, and the new 9 unit tests all pass.

However, I found one BLOCKER correctness bug in the reframe math (odd `crop_x` breaks ffmpeg), several quality gaps (stale docstrings claiming MSR_FC=17 when the default is 41, missing `encoding="utf-8"` on `open()`, a docstring/method-name mismatch in `_atomic_write_text`), and a meaningful test-coverage hole (the auto-derive branch of `plan_reframe` — when `target_width`/`target_height` are omitted — is exercised by zero tests despite producing materially different output dimensions).

Cross-repo safety verified: `git diff d9620369..HEAD --name-only` on kais-hermes-skills shows no touches under `~/.hermes/agents/*.agent.yaml` (Phase 75 scope respected). The diff is confined to plugins/pipeline_state/, skills/kais-movie-pipeline/, skills/movie-experts/, and a new `_eval/form_factor_step14/` fixtures directory.

## Critical Issues

### CR-01: Cell D center-crop can emit odd `crop_x`, breaking ffmpeg yuv420p

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/_step14_reframe_math.py:188`
**Issue:**

`crop_x = (master_width - crop_width) // 2` can produce an odd integer when `master_width` is odd (or even-but-mismatched with `crop_width`). ffmpeg's `crop` filter requires even `X` for most YUV pixel formats (yuv420p / yuv444p). An odd `crop_x` will fail or silently shift chroma samples, corrupting the Cell D variant.

Reproduction (verified by running the code):
```
master_width=1922 -> crop_x = (1922 - 608) // 2 = 657  # ODD — ffmpeg rejects
master_width=1923 -> crop_x = (1923 - 608) // 2 = 657  # ODD
```

`crop_width` is always even (via `_round_even`), and `master_height` / `target_width` are also even in the tested cases. But `master_width` is sourced from `master.mp4` metadata at runtime — any non-even master width triggers this. Cinema masters are typically 1920/3840 (even), but cropped/preview masters (e.g. 1281×720 letterbox-rejects, operator-supplied stock footage) can be odd. The Cell D path is the load-bearing reframe for landscape-master → portrait-variant delivery (抖音竖屏 / 小程序剧), so a silent ffmpeg failure here blocks platform delivery.

The same parity risk applies to Cell C's `pad_x = (target_width - content_width) // 2` when `target_width` is odd.

**Fix:**

Round all coordinate outputs to even — not just dimensions:

```python
def _round_even(n: float) -> int:
    """ffmpeg requires even dimensions AND coordinates for most YUV pixel formats."""
    return int(round(n)) + (int(round(n)) % 2)

# In Cell D:
crop_x = _round_even((master_width - crop_width) / 2)
# In Cell C:
pad_x = _round_even((target_width - content_width) / 2)
```

Add a regression test asserting `crop_x % 2 == 0` and `pad_x % 2 == 0` for master widths 1920, 1921, 1922, 1923. (The current test suite only covers `master_width=1920`, which coincidentally yields `crop_x=656` — even, masking the bug.)

## Warnings

### WR-01: Stale docstring claims "ALWAYS 17" while MSR_FC default is 41

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py:119`
**Issue:**

The Phase 71 fix correctly bumped `MSR_FC_DEFAULT = 41` and the module-level docstring at line 67 ("was 17 before A/B test"). But the docstring for `build_msr_workflow()` at line 119 still says:

```
msr_fc: Conditioning frame count — ALWAYS 17.
```

This is contradicted by the function signature (which accepts arbitrary `msr_fc`), the constant `MSR_FC_DEFAULT = 41`, the CLI default `--msr-fc default=MSR_FC_DEFAULT`, and the module docstring ("trimmed post-generation"). An operator or subagent reading `help(build_msr_workflow)` will conclude they must pass `msr_fc=17`, silently overriding the A/B-test winner and degrading identity conditioning. Subagents load this template via `skill_view` and follow docstring guidance literally — a stale "ALWAYS 17" will produce worse-than-A/B-baseline renders.

**Fix:**

```python
msr_fc: Conditioning frame count (default 41 per A/B test; plugin allows [17, 25, 33, 41]).
```

### WR-02: Cell C and Cell D auto-derive branches have zero test coverage

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py` (missing cases)
**Issue:**

`plan_reframe()` accepts optional `target_width` / `target_height`. All 4 existing tests pass explicit dimensions:

```python
plan_reframe(1080, 1920, "landscape", target_width=1920, target_height=1080)
```

But the implementation has a distinct auto-derive branch when these are `None`:

```python
if target_height is None:
    target_height = master_height  # Cell C
# ...
if target_width is None:
    target_width = _round_even(target_height * 16 / 9)  # Cell C → 3414 for master 1080×1920
```

For a portrait 1080×1920 master with no explicit target, Cell C auto-derives `out_width=3414, out_height=1920` — a wildly different output canvas than the tested 1920×1080. The math is correct (verified by hand), but no test pins it. If a future refactor swaps the formula (e.g. uses `master_width` instead of `master_height` as the base), no test will fail.

Step 14 in production invokes `plan_reframe` without explicit target dimensions in the common case (the platform master derives target from the source aspect, not from per-variant overrides). The untested branch is the production-default branch.

**Fix:**

Add 2 tests mirroring the existing ones but omitting `target_width`/`target_height`:

```python
def test_cell_c_portrait_to_landscape_letterbox_auto_derive():
    plan = plan_reframe(1080, 1920, "landscape")  # no target_width/height
    assert plan.cell == "C_letterbox"
    assert plan.out_width == 3414  # round_even(1920 * 16/9)
    assert plan.out_height == 1920  # defaults to master_height
    assert plan.pad_x == 1167  # (3414 - 1080) // 2
    # ... etc

def test_cell_d_landscape_to_portrait_center_crop_auto_derive():
    plan = plan_reframe(1920, 1080, "portrait")
    assert plan.out_width == 1080  # defaults to master_height
    assert plan.out_height == 1920  # defaults to master_width
    # ... etc
```

### WR-03: Square / 1:1 masters silently classified as landscape

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/_step14_reframe_math.py:67-69`
**Issue:**

`_is_portrait(w, h)` returns `h > w`. For a square master (`w == h`), this returns `False`, so `_master_form_factor` classifies it as `"landscape"`. A square master then routes through Cell B (landscape → landscape pass-through) or Cell D (landscape → portrait center-crop) — neither of which is semantically correct for a 1:1 master.

Square masters are rare but real: Instagram-feed legacy 1:1 video, operator-supplied stock inserts, and AI image-gen 1024×1024 first-frames used as master proxies. Cell B pass-through would emit a 1:1 "landscape" variant, which downstream `platform-master-slicing.md` will then attempt to deliver as a 16:9 variant — failing the T-38-03 aspect-ratio consistency check at the consumer side (Phase 42 DATA), but only after wasted compute.

**Fix:**

Either (a) make `_master_form_factor` reject 1:1 explicitly:

```python
def _master_form_factor(master_width: int, master_height: int) -> FormFactor:
    if master_width == master_height:
        raise ValueError(
            f"Square master ({master_width}×{master_height}) has no form factor; "
            f"Step 14 reframe requires portrait or landscape master."
        )
    return "portrait" if master_height > master_width else "landscape"
```

or (b) document the assumption in the module docstring: "Square masters are treated as landscape; operator must pre-crop to 9:16 or 16:9."

### WR-04: `open()` calls missing `encoding="utf-8"` (PLW1514 / CLAUDE.md defense rule)

**Files:**
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p11_video_render.py:376`
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py:433` (load_shot_list)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py:794` (meta_path write)

**Issue:**

Three text-mode `open()` calls omit `encoding="utf-8"`. On Windows, the default encoding is cp1252 — any meta JSON or shot-list JSON containing Chinese characters (shot_id `S03_SH01_老林` is common in this project; the meta path write at line 794 emits `ensure_ascii=False`) will silently corrupt.

CLAUDE.md mandates: *"Add `encoding="utf-8"` to every text-mode `open()`, even in tests where it would be optional under Ruff's ignore. Defensive against Windows."* Although kais-hermes-skills is a separate repo without its own Ruff config, the project convention is project-wide and this code runs on Windows (CLAUDE.md: "Linux / macOS / Windows / Termux — all first-class").

The p11 cache-hit path is especially load-bearing: `_try_cache_hit` reads `<shot_id>_meta.json` to decide whether to skip a 75-450s GPU render. If the meta file was written by a prior Windows run with cp1252 encoding, the `json.load(f)` on line 377 will raise `UnicodeDecodeError`, the broad `except Exception` on line 399 swallows it, the function returns `None`, and the shot is needlessly re-rendered — wasting GPU time.

**Fix:**

```python
# p11_video_render.py:376
with open(meta, encoding="utf-8") as f:

# ltx_msr_batch_render.py:433
with open(path, encoding="utf-8") as f:

# ltx_msr_batch_render.py:794
with open(meta_path, "w", encoding="utf-8") as f:
```

### WR-05: `_atomic_write_text` pre-generates a tmp name it never uses (dead code + misleading comment)

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py:157-175`
**Issue:**

The function computes `tmp_name` and `tmp_path` (lines 157-161) using `os.getpid() + ms timestamp + os.urandom(3).hex`, then immediately discards them and uses the `tmp_str` returned by `tempfile.mkstemp()` (line 162). The comment on lines 165-167 explains this ("mkstemp already picked a unique name — close our pre-generated one"), but the pre-generation code is dead: `tmp_path` is never referenced after assignment.

The comment also misleads: it claims the pre-generation is there to "avoid race between two writers generating identical pid+ms+rand names" — but the pre-generated name was the one at risk of collision, and `mkstemp` solves it independently. The dead `tmp_name` computation implies the function does collision avoidance that it doesn't actually do (it relies entirely on `mkstemp`).

**Fix:**

Delete the dead `tmp_name` / `tmp_path` computation (lines 157-161) and the misleading comment. The `mkstemp` call is the only path that matters:

```python
def _atomic_write_text(path: Path, data: str) -> None:
    """Atomic write via tempfile.mkstemp + os.replace.

    mkstemp guarantees a unique fd+path atomically. os.replace is atomic
    on POSIX (single-filesystem rename(2)).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(
        prefix=f"{path.name}.tmp.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        os.close(fd)
    except OSError:
        pass
    with open(tmp_str, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp_str, str(path))
```

### WR-06: `build_msr_workflow` docstring describes `msr_fc` semantics for an old workflow

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py:106-131`
**Issue:**

Beyond the "ALWAYS 17" stale value (WR-01), the docstring's "Wiring note" references node IDs (`[5,0]/[6,0]`) that belong to a different (older) workflow variant. The current `build_msr_workflow` body uses `[7,0]/[7,1]` (LTXVConditioning outputs) and the wiring note is accurate about what NOT to do, but a subagent reading the docstring + body will see the warning references node IDs that don't appear in the returned workflow dict under those numbers (Nodes 5/6 are CLIPTextEncode in the current body, not conditioning outputs). The note is correct in spirit but confuses anyone trying to verify the wiring.

**Fix:**

Rewrite the wiring note to reference current node IDs, or remove the specific `[5,0]/[6,0]` reference and say: "Node 9 (LTXAddVideoICLoRAGuide) positive/negative inputs MUST reference Node 7 (LTXVConditioning outputs `[7,0]`/`[7,1]`), NOT the raw CLIPTextEncode outputs. Using raw text-encode outputs skips frame_rate conditioning and degrades motion quality."

## Info

### IN-01: `validate_form_factor_invariant` has no `__post_init__`-style runtime hook

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py:112-141`
**Issue:**

`validate_form_factor_invariant()` is a pure function that must be called explicitly by callers (currently only the test). The dataclass's `__post_init__` enforces the enum value, but does NOT call `validate_form_factor_invariant(state.phases)` — meaning a state file loaded from disk with per-shot `form_factor` overrides in `phases` will pass `__post_init__` cleanly and only fail if a caller remembers to invoke the invariant check. The docstring says "allowing per-shot overrides would break LTX-MSR ICLoRA reference conditioning" — but nothing in the load path enforces this.

This is currently safe because the only writer of `state.phases` is `save_checkpoint`, which writes `{status, completed_at, result}` (no `form_factor` key). But if a future phase writes a per-shot `form_factor` into `result`, the invariant will silently pass at load time.

**Fix:** Either call `validate_form_factor_invariant(self)` at the end of `__post_init__` (defensive), or add a load-time assertion in `PipelineStateStore.load()` after constructing the state.

### IN-02: `__post_init__` validator raises `ValueError` but test also accepts `TypeError`

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_form_factor.py:121`
**Issue:**

```python
with pytest.raises((ValueError, TypeError)):
    PipelineState(episode="x", form_factor="square")
```

The validator at `store.py:91` raises `ValueError` only. The `TypeError` in the test's tuple is dead — `form_factor="square"` is a valid `str`, so no `TypeError` path exists. The test is overly permissive: if a future refactor accidentally swallows `ValueError` and raises something else (or nothing), the test would still pass against `TypeError`. Tighten to `pytest.raises(ValueError)`.

### IN-03: `_FORM_FACTOR_INSTRUCTION` text says "load vertical-screen-framing.md" but cinematographer Step 3 only conditionally dispatches

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py:80-89`
**Issue:**

The instruction tells the subagent: "Portrait (9:16) ... load vertical-screen-framing.md. Landscape (16:9) ... load horizontal-screen-framing.md." This matches cinematographer/SKILL.md Step 3 dispatch (verified at SKILL.md:178-180). However, the instruction is part of the **p09 goal string**, which goes to the **cinematographer subagent** — and the subagent does NOT see SKILL.md at runtime (META-RULE X-2). So the subagent gets the instruction to "load vertical-screen-framing.md" without the SKILL.md telling it how/when. The instruction itself is self-contained enough to be actionable, but if a subagent fails to load the ref (e.g. `skill_view` returns 404), there's no fallback. Consider adding a quality-gate check that the loaded ref content contains expected keywords (e.g. "power points", "headroom") before accepting the delegate_task output.

### IN-04: `_atomic_write_text` lacks `fsync` — documented but worth re-stating

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py:152-154`
**Issue:**

The docstring explicitly says "no explicit fsync ... matching behavior preserves the perf profile and the durability contract callers already rely on." This is a conscious decision and matches Node.js behavior. Flagging only because a half-written `.pipeline-state.json` after a power loss (where `os.replace` completed in the page cache but never hit disk) will corrupt an episode — and the project's own `D-33-02` rationale says "a half-written state file corrupts an entire episode." `os.replace` is atomic at the filesystem-metadata level, but without `fsync` before `replace`, the new file's data may not be durable. Low risk in practice (operator notices power loss, re-runs), but worth a one-line `os.fsync(f.fileno())` before the `with` block exits if the project ever cares about crash durability.

### IN-05: Cinematographer Step 6 ("Vertical Framing Intent") is unconditional for landscape

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md:183`
**Issue:**

Step 6 reads: "Vertical Framing Intent — Per shot, define power_point + headroom + subtitle_zone + platform_target." This is the existing pre-Phase-71 line and applies unconditionally. For landscape episodes, this step name is misleading (landscape uses horizontal rule-of-thirds, not "vertical framing"). Phase 71's Step 3 dispatch correctly branches, but Step 6 does not. A landscape subagent following the workflow literally would produce a `vertical_framing_intent.json` artifact whose contents are horizontal — confusing for downstream consumers. Consider renaming to "Form-Factor Framing Intent" or branching Step 6 on `form_factor` like Step 3.

---

## Cross-Cutting Observations (not findings, just context for the orchestrator)

**XCUT-02 dual injection verified:** `_FORM_FACTOR_INSTRUCTION` appears in BOTH `.task(steps=[...])` (p09_shot_breakdown.py:376) AND `.constraints([...])` (p09_shot_breakdown.py:399, merged into the cross-cutting-params constraint). The 7-constraint budget (`MAX_CONSTRAINTS = 7` in `_prompt_template.py:62`) is exactly at the limit — adding any future constraint will require refactoring (e.g. merging two constraints). The test `test_p09_goal_includes_form_factor_instruction` correctly verifies both the `form_factor` keyword and the `MUST read form_factor` enforceable-phrasing substring are present in the captured goal.

**Cross-repo safety verified:** `git diff d9620369e48eec51c31ee72ac8827c288eaccf71..HEAD --name-only` on kais-hermes-skills shows 34 files changed — all under `plugins/pipeline_state/`, `skills/kais-movie-pipeline/`, `skills/movie-experts/`, and `_eval/form_factor_step14/`. No touches under `~/.hermes/agents/*.agent.yaml` (Phase 75 scope respected). The `_eval/form_factor_step14/` fixtures (8 PNG before/after pairs) are committed but not in the review file list — they're binary artifacts, not source.

**Test execution verified:** All 9 new tests pass in 0.24s (`pytest test_form_factor.py test_step14_reframe_matrix.py`). The `tmp_state_store` fixture from conftest.py:104-111 is correctly consumed by `test_old_json_defaults_to_portrait` and `test_landscape_round_trip`.

**Ref quality verified:** `horizontal-screen-framing.md` has all 5 promised H2 sections (16:9 Power Points, Headroom Standards, Subtitle Safe Area, Per-Platform Framing Divergence, Horizontal Camera Move Correction) plus 3 bonus sections (JSON Schema, Anti-Patterns, Glossary). Real film citations present (Grand Budapest Hotel, The Revenant, Drive, The Shining, 1917) all marked "analytical reference, fair use." Fair-use attribution header is present and accurate. Source provenance footer lists Blain Brown 2016 / Mercado 2010 / Bordwell & Thompson 2020 / Netflix Timed Text Style Guide / YouTube Creator Academy.

**4-cell matrix verified:** `platform-master-slicing.md` §4-Cell Reframe Matrix (lines 170-225) correctly defines all 4 cells (A passthrough / B passthrough / C letterbox / D center-crop+saliency), includes the regression note (Cell A = existing vertical-master behavior), the saliency-scan requirement for Cell D (T-71-08 mitigation), ffmpeg CLI examples per cell, and threat-model notes. Cell D's mandatory saliency scan is the load-bearing T-71-08 mitigation and is correctly asserted in `test_cell_d_landscape_to_portrait_center_crop`.

**Subprocess safety verified:** `ltx_msr_batch_render.py:412` uses `subprocess.run(cmd, capture_output=True, timeout=120)` with `cmd` as a list (no `shell=True`). The cmd is built from `input_path` which is `output_path.replace(".mp4", "_trimmed.mp4")` — derived from `os.path.join(output_dir, f"{shot_id}.mp4")`. `shot_id` comes from the shot-list JSON. If an attacker controls the shot-list JSON (e.g. via a malicious episode), `shot_id="../../etc/cron.d/payload"` would write outside `output_dir`. This is a path-traversal vector, but the threat model assumes the operator controls the shot-list JSON (it's a local file, not network input). Worth noting but not a finding for this project's trust model.

---

_Reviewed: 2026-07-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
