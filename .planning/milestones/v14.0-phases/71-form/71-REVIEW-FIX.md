---
phase: 71-form
fixed_at: 2026-07-09T18:00:00Z
review_path: .planning/phases/71-form/71-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 71: Code Review Fix Report

**Fixed at:** 2026-07-09T18:00:00Z
**Source review:** `.planning/phases/71-form/71-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (1 Critical + 6 Warning per default `fix_scope: critical_warning`)
- Fixed: 7
- Skipped: 0
- Info findings (5) deferred per default scope

**Cross-repo topology:**
- All 7 fixes target `/data/workspace/kais-hermes-skills/` (separate git repo)
- Fixer ran inside isolated worktree `/tmp/sv-71-reviewfix-LS3yMZ` on branch `gsd-reviewfix/71-613547` (off `master` @ `3c97902`)
- REVIEW-FIX.md is the ONLY hermes-agent-side artifact (this file); commits live in kais-hermes-skills repo

**Test verification:**
- Pre-fix: 9 tests passing (4 reframe matrix + 5 form_factor)
- Post-fix: 25 tests passing (20 reframe matrix + 5 form_factor) — 16 new tests added across CR-01, WR-02, WR-03
- Full suite re-run after every fix; no regressions introduced

## Fixed Issues

### CR-01: Cell D center-crop can emit odd `crop_x`, breaking ffmpeg yuv420p

**Files modified:** `skills/kais-movie-pipeline/tests/_step14_reframe_math.py`, `skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py`
**Commit:** `c009ff5` (kais-hermes-skills repo)
**Applied fix:**

Routed `crop_x` (Cell D) and `pad_x` (Cell C) through the existing `_round_even()` helper. The original `// 2` floor division produced odd values for odd master/target widths (e.g. `master_width=1922 -> crop_x=657`), which ffmpeg's `crop`/`pad` filters reject for yuv420p or silently shift chroma for yuv444p.

Specific changes:
- Expanded `_round_even()` docstring to clarify it covers both dimensions AND coordinates (ffmpeg yuv420p semantics)
- Cell D `crop_x = _round_even((master_width - crop_width) / 2)` — previously `// 2`
- Cell C `pad_x = _round_even((target_width - content_width) / 2)` — previously `// 2`
- Added 12 parametrized regression tests sweeping even+odd master/target widths (1920, 1921, 1922, 1923, 3414, 3415, 3416) to pin the parity invariant

Logic verification: 16/16 tests pass. Math verified by hand and by running the actual function with odd inputs. This finding is a real correctness bug (not a logic-only fix), so the commit status is `fixed` (not `fixed: requires human verification`).

### WR-01: Stale docstring claims "ALWAYS 17" while MSR_FC default is 41

**Files modified:** `skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py`
**Commit:** `b1f0065` (kais-hermes-skills repo)
**Applied fix:**

Updated `build_msr_workflow()` docstring at line 119 from `msr_fc: Conditioning frame count — ALWAYS 17.` to `msr_fc: Conditioning frame count (default 41 per A/B test; plugin allows [17, 25, 33, 41]).`. Now consistent with `MSR_FC_DEFAULT = 41`, the CLI `--msr-fc default=MSR_FC_DEFAULT`, and the module-level docstring ("was 17 before A/B test"). Subagents reading `help(build_msr_workflow)` will no longer be misled into overriding the A/B-test winner.

### WR-02: Cell C and Cell D auto-derive branches have zero test coverage

**Files modified:** `skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py`
**Commit:** `eaa09a0` (kais-hermes-skills repo)
**Applied fix:**

Added 2 new tests that exercise `plan_reframe()` without explicit `target_width`/`target_height` — the production-default branch (Step 14 derives target from source aspect, not per-variant overrides). The auto-derive branch yields materially different output canvas than the explicit-target tests (Cell C auto-derive = 3414x1920 vs tested 1920x1080).

- `test_cell_c_portrait_to_landscape_letterbox_auto_derive`: pins `out_width=3414`, `out_height=1920`, `pad_x=1168` (also load-bearing CR-01 fix point — plain `// 2` would return 1167 ODD)
- `test_cell_d_landscape_to_portrait_center_crop_auto_derive`: pins `out_width=1080`, `out_height=1920`, `crop_x=656`

Math verified by running the function before writing the assertions. A future refactor swapping `master_width` for `master_height` as the auto-derive base will now fail loudly.

### WR-03: Square / 1:1 masters silently classified as landscape

**Files modified:** `skills/kais-movie-pipeline/tests/_step14_reframe_math.py`, `skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py`
**Commit:** `f880dd0` (kais-hermes-skills repo)
**Applied fix:**

Chose option (a) from REVIEW.md: reject square masters at the classifier boundary with `ValueError` rather than silently treating them as landscape. Matches the strict-enum precedent set by `PipelineState.form_factor` (D-01: no fuzzy matching, no warnings-and-continue).

Changes:
- `_master_form_factor()` now raises `ValueError` with a message instructing the operator to pre-crop to 9:16 or 16:9 before invoking Step 14
- Added docstring explaining real-world square sources (Instagram 1:1, stock inserts, AI image-gen 1024x1024 first-frames)
- Added 2 regression tests: `test_square_master_rejected` (single target) + `test_square_master_rejected_regardless_of_target` (sweeps both target_form_factor values, verifying rejection happens at classifier boundary before cell selection)

Logic verification: existing Cell A/B/C/D tests still pass (none use square masters); the new tests confirm the ValueError is raised with the expected "Square master" message.

### WR-04: `open()` calls missing `encoding="utf-8"` (PLW1514 / CLAUDE.md defense rule)

**Files modified:** `skills/kais-movie-pipeline/pipeline/phases/p11_video_render.py`, `skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py`
**Commit:** `fa3f73f` (kais-hermes-skills repo)
**Applied fix:**

Added `encoding="utf-8"` to all 3 text-mode `open()` calls identified in REVIEW.md:

- `p11_video_render.py:376` — `_try_cache_hit` meta JSON read (load-bearing: cp1252 corruption here silently triggers full GPU re-render via swallowed `UnicodeDecodeError`)
- `ltx_msr_batch_render.py:433` — `load_shot_list` JSON read
- `ltx_msr_batch_render.py:794` — `ltx_batch_meta.json` write (writes `ensure_ascii=False`, so Chinese shot_ids are emitted as raw UTF-8 bytes)

Binary-mode `open(..., "rb")` and `open(..., "wb")` calls in the same files correctly omit `encoding` (binary mode doesn't use it). Verified via grep: no remaining text-mode `open()` without `encoding="utf-8"` in either file.

### WR-05: `_atomic_write_text` pre-generates a tmp name it never uses (dead code + misleading comment)

**Files modified:** `plugins/pipeline_state/store.py`
**Commit:** `44ef740` (kais-hermes-skills repo)
**Applied fix:**

Deleted the dead `tmp_name` / `tmp_path` computation (lines 157-161) and the misleading comment that claimed the pre-generation was for collision avoidance. The function actually relies entirely on `tempfile.mkstemp()` for uniqueness (O_CREAT|O_EXCL atomically guarantees a unique fd+path). The dead code implied collision avoidance that wasn't actually performed.

Also:
- Removed the now-unused `import time` (only consumer was the dead `tmp_name` computation, which used `time.time()`)
- Updated docstring to reflect reality ("mkstemp guarantees a unique fd+path atomically — no pre-generation needed")

Verification: `form_factor` tests (which use `PipelineStateStore.save()` -> `_atomic_write_text`) still pass — 5/5 green.

### WR-06: `build_msr_workflow` docstring wiring note references stale node IDs

**Files modified:** `skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py`
**Commit:** `5772f55` (kais-hermes-skills repo)
**Applied fix:**

Rewrote the "Wiring note (CRITICAL)" in `build_msr_workflow()` docstring to spell out both the CORRECT reference (`[7,0]`/`[7,1]` = Node 7 LTXVConditioning outputs) AND the INCORRECT reference (`[5,0]`/`[6,0]` = raw CLIPTextEncode outputs from Nodes 5/6). The original note cited `[5,0]/[6,0]` without clarifying those were the wrong choice — a subagent reading the docstring + body together would see Nodes 5/6 referenced without realizing they were the anti-pattern.

The note now matches the actual workflow body (Node 9 inputs reference `[7, 0]`/`[7, 1]`, not `[5, 0]`/`[6, 0]`) and is unambiguous about which reference is correct vs incorrect. Matches the WR-06 fix guidance verbatim.

---

_Fixed: 2026-07-09T18:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
_Worktree: `/tmp/sv-71-reviewfix-LS3yMZ` on branch `gsd-reviewfix/71-613547` (kais-hermes-skills repo)_
_All 25 tests passing post-fix (16 added across CR-01/WR-02/WR-03; 9 pre-existing). No regressions._
