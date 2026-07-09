---
phase: 71-form
verified: 2026-07-09T19:30:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Operator reads horizontal-screen-framing.md end-to-end and confirms the 6 real-film citations (Grand Budapest Hotel / Revenant / Drive / Shining / 1917 / Lawrence of Arabia) are correctly attributed as analytical references under fair use, not reproductions"
    expected: "No copyrighted reproductions; citations are paraphrased framing/composition discussion only; LICENSE.md cross-reference intact"
    why_human: "Subjective content-quality + license review per VALIDATION.md Manual-Only row 1; CLAUDE.md copyright constraint cannot be grep-checked"
  - test: "Operator reads Tier 1 dual-branch sections in cinematographer / visual_executor / editor / character_designer and confirms landscape vs portrait rules differ meaningfully (not just string substitution)"
    expected: "Each of 4 Tier 1 sections has distinct numeric thresholds (power points / headroom % / shot scale distribution / dreamina dims / eye-trace %) per form, not 9:16 text with 'landscape' swapped in"
    why_human: "Per-expert content depth is judgment-based per VALIDATION.md Manual-Only row 2"
  - test: "Operator reviews the 8 sample-frame fixtures under _eval/form_factor_step14/ and confirms each before/after pair visually demonstrates the correct cell algorithm (pass-through identical for A/B; pillarbox bars for C; center-crop preserving subject for D)"
    expected: "All 8 PNGs render non-corrupt and visually consistent with their cell algorithm; README.md generation instructions reproducible"
    why_human: "Visual regression is manual by design per VALIDATION.md Manual-Only row 3"
---

# Phase 71: FORM Verification Report

**Phase Goal:** Users can author a kais-movie-pipeline project in either landscape 16:9 or portrait 9:16 form factor, with the pipeline reading `form_factor` as a first-class project meta and each expert emitting form-aware creative rules instead of hardcoded `9:16` assumptions.
**Verified:** 2026-07-09T19:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | User can set `form_factor` (`landscape` / `portrait`) at project level via `PipelineState.form_factor`, with `portrait` default preserving existing-project backward-compat (ROADMAP SC-1, FORM-01) | ✓ VERIFIED | `plugins/pipeline_state/store.py:79` declares `form_factor: Literal["landscape", "portrait"] = "portrait"`; `__post_init__` at L81-93 raises `ValueError` on unknown values; tests `test_old_json_defaults_to_portrait` + `test_landscape_round_trip` + `test_invalid_form_factor_raises` all PASS. Old episode JSON round-trips as portrait (auto-whitelisted via `_STATE_FIELDS`). |
| 2 | Each of 15 active movie-expert SKILL.md files has `## Form Factor Adaptation` section with dual-branch rules replacing hardcoded 9:16 (ROADMAP SC-2, FORM-02) | ✓ VERIFIED | `bash 71-check-form-sections.sh` exits 0 with `Section count: 15 / 15`. Tier 1 (cinematographer 25L / visual_executor 19L / editor 23L / character_designer 19L — all ≥15L); Tier 2 (5 experts × 8L with portrait+landscape literals); Tier 3 (6 form-agnostic stubs). Deprecated stubs (drawer/scene_builder/...) NOT touched. |
| 3 | User can read `references/horizontal-screen-framing.md` as landscape companion to `vertical-screen-framing.md` (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region) (ROADMAP SC-3, FORM-03) | ✓ VERIFIED | File exists at `cinematographer/references/horizontal-screen-framing.md`; 226 lines (≥150 required); 9 H2 sections including all 5 FORM-03-required (Power Points L20 / Headroom L55 / 字幕 Safe Area L83 / Per-Platform Framing Divergence L113 / Horizontal Camera Move L143). Fair-use attribution block at L3-4 + L226. Real film citations (Grand Budapest Hotel, Revenant, Drive, Shining, 1917, Lawrence of Arabia). **Content quality itself requires human review — see Human Verification.** |
| 4 | Step 14 platform-master-slicing correctly resolves 4-cell reframe matrix (master × target form factor) without quality degradation (ROADMAP SC-4, FORM-04) | ✓ VERIFIED | `platform-master-slicing.md:170` has `## 4-Cell Reframe Matrix (FORM-04 v14.0)` H2 with 4-row table (all 4 cells named); Cell D mandatory saliency-scan contract + ffmpeg `cropdetect` zero-dep default documented; `_step14_reframe_math.py` pure-function helper mirrors markdown spec; `test_step14_reframe_matrix.py` has 20 tests (4 base cells + 12 parity-invariant + 2 auto-derive + 2 square-master rejection) — all PASS. Cell D asserts `saliency_scan_required=True` (T-71-08 mitigation). |
| 5 | `kais-movie-pipeline/SKILL.md` line 446 stale `MSR_FC=17` corrected to canonical `MSR_FC=41` (ROADMAP SC-5, FORM-05) | ✓ VERIFIED | `SKILL.md:446` reads `MSR_FC=41` (canonical per A/B test). Also swept in `p11-single-shot-orchestration.md:75,85` + `post-production-audit.md:156` + `ltx-msr-workflow-spec.md:67,121` + `p11_video_render.py:74` (auto-found bugfix). 10+ canonical `MSR_FC=41` occurrences across skills/. See Warnings for 3 preserved historical/narrative occurrences. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `kais-hermes-skills/plugins/pipeline_state/store.py` | `form_factor` field + `validate_form_factor_invariant()` + `__post_init__` validator | ✓ VERIFIED | L37 Literal import; L75-79 field with portrait default; L81-93 __post_init__ raises ValueError on invalid; L111-138 recursive invariant scan. Tests `test_old_json_defaults_to_portrait`, `test_landscape_round_trip`, `test_invalid_form_factor_raises`, `test_rejects_per_shot_form_factor` PASS. |
| `kais-hermes-skills/skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` | 16:9 landscape ref mirroring vertical twin 5-section structure, ≥150 lines | ✓ VERIFIED | 226 lines; 9 H2 sections (5 core + JSON Schema + Anti-Patterns + Glossary + Summary); citations with fair-use attribution. |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_form_factor.py` | Unit tests for FORM-01 + XCUT-02 | ✓ VERIFIED | 5 tests (FORM-01: backward-compat, round-trip, invalid-value, per-shot invariant; XCUT-02: p09 goal injection assertion). All PASS. |
| `kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py` | `--form-factor` argparse helper mapping to width/height | ✓ VERIFIED | L71-73 `_FORM_FACTOR_RESOLUTION = {"portrait": (704, 1280), "landscape": (1280, 704)}`; L627-628 argparse `choices=["landscape","portrait"]`; L664-669 derive width/height when explicit override absent. |
| `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` | `_FORM_FACTOR_INSTRUCTION` injected into `.task(steps=)` + `.constraints()` | ✓ VERIFIED | L80-83 `_FORM_FACTOR_INSTRUCTION` constant; L376 `.task(steps=[])` injection; L399 `.constraints()` consolidated constraint (MUST read form_factor). Test `test_p09_goal_includes_form_factor_instruction` PASS. |
| `kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md` | 4-cell reframe matrix section | ✓ VERIFIED | `## 4-Cell Reframe Matrix (FORM-04 v14.0)` H2 at L170; 4-row table covering all combinations; saliency-scan requirement + ffmpeg CLI examples per cell; regression note (existing vertical-master = Cell A made explicit); D1-D4 sections preserved (additive only). |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py` | 4 unit tests on reframe math per cell | ✓ VERIFIED | 20 tests total: 4 base cells (A/B/C/D) + 12 parity-invariant + 2 auto-derive + 2 square-master rejection. All PASS. Cell D asserts `saliency_scan_required=True`. |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/_step14_reframe_math.py` | Pure-function reframe math helper | ✓ VERIFIED | 169 lines; `plan_reframe()` dispatches to 4 cells; `_round_even()` ensures ffmpeg yuv420p parity (CR-01 fix); `_master_form_factor()` rejects square masters with ValueError (WR-03 fix). |
| `kais-hermes-skills/_eval/form_factor_step14/` | 8 sample-frame fixtures (4 cells × before/after) | ✓ VERIFIED | 8 PNGs present: `cell_a_portrait_to_portrait_{before,after}.png`, `cell_b_landscape_to_landscape_*`, `cell_c_portrait_to_landscape_*`, `cell_d_landscape_to_portrait_*`. README.md documents generation + UAT. **Visual correctness requires human review — see Human Verification.** |
| `.planning/phases/71-form/71-check-form-sections.sh` | Bash smoke script asserting all 15 canonical experts | ✓ VERIFIED | Executable; enumerates exactly 15 canonical active experts (no deprecated stubs); exits 0 with `Section count: 15 / 15`. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `plugins/pipeline_state/store.py` | `p09_shot_breakdown.py` | `_FORM_FACTOR_INSTRUCTION` constant injected into `.task(steps=[...])` goal f-string | ✓ WIRED | `grep -c "_FORM_FACTOR_INSTRUCTION" p09_shot_breakdown.py` = 2 (L80 definition + L376 injection). `test_p09_goal_includes_form_factor_instruction` asserts `form_factor` AND `MUST read form_factor` in captured goal. |
| `cinematographer/SKILL.md Step 3` | `references/horizontal-screen-framing.md` | `form_factor` dispatch branch (landscape case) | ✓ WIRED | L178-180 Step 3 branches on `form_factor` from `pipeline_state` context: portrait → vertical-screen-framing.md, landscape → horizontal-screen-framing.md. Anti-pattern at L364 explicitly marks dispatch as load-bearing. |
| `cinematographer/SKILL.md Step 3` | `references/vertical-screen-framing.md` | `form_factor` dispatch branch (portrait case) | ✓ WIRED | Same Step 3 block (L179). |
| `platform-master-slicing.md 4-cell matrix` | `PipelineState.form_factor` | Matrix reads `master_form_factor × target_platform_form_factor` | ✓ WIRED | L172 "When `PipelineState.form_factor` parameterizes the master ... branches on `master_form_factor × target_platform_form_factor`". Pattern `form_factor` present. |
| `platform-master-slicing.md Cell D` | ffmpeg cropdetect (saliency scan) | Center-crop + saliency requirement | ✓ WIRED | L197 "ffmpeg `cropdetect` filter 作为 zero-dep default"; L212-219 ffmpeg CLI example; Cell D test asserts `saliency_scan_required=True`. |
| `ltx_msr_batch_render.py` argparse | `_FORM_FACTOR_RESOLUTION` dict | `--form-factor` resolution derivation | ✓ WIRED | L627-628 argparse + L668-669 dict lookup resolves width/height when explicit override absent. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `PipelineState` | `form_factor` | Episode JSON or explicit construction | Yes — strict enum, default "portrait" | ✓ FLOWING |
| `p09_shot_breakdown` goal | `captured["goal"]` | `_FORM_FACTOR_INSTRUCTION` constant | Yes — MUST keyword + concrete power points | ✓ FLOWING |
| `plan_reframe()` output | `crop_x`, `pad_x`, `saliency_scan_required` | Pure-function math from master/target dims | Yes — deterministic ffmpeg crop/pad coords | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| All form_factor + reframe matrix tests green | `python3 -m pytest test_form_factor.py test_step14_reframe_matrix.py -v` | 25 passed in 0.27s | ✓ PASS |
| p09 regression (no regression from _FORM_FACTOR_INSTRUCTION injection) | `python3 -m pytest test_p09_unit.py -v` | 8 passed in 0.24s | ✓ PASS |
| 71-check-form-sections.sh exits 0 (15/15 sections) | `bash 71-check-form-sections.sh` | exit=0; 15/15 OK | ✓ PASS |
| MSR_FC=17 absent from canonical sweep scope | `grep -rn "MSR_FC=17" skills/kais-movie-pipeline/ \| grep -v ltx-msr-single-shot-prompt-construction` | 0 hits | ✓ PASS |
| MSR_FC=41 canonical across sweep locations | `grep -rc "MSR_FC=41" skills/ \| grep -v ':0$'` | 10+ files with hits (≥5 required) | ✓ PASS |
| horizontal-screen-framing.md meets depth requirement | `wc -l` + `grep -c "^## "` | 226 lines, 9 H2 sections (≥5 required) | ✓ PASS |
| 8 sample-frame fixtures present | `ls _eval/form_factor_step14/*.png \| wc -l` | 8 | ✓ PASS |
| All 19 claimed kais-hermes-skills commits exist | `git cat-file -e $sha^{commit}` for 19 shas | 19/19 FOUND | ✓ PASS |
| hermes-agent smoke script commit exists | `git cat-file -e cf8ca0ea5^{commit}` | FOUND | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — Phase 71 does not declare probe-based verification (`scripts/*/tests/probe-*.sh`); verification uses pytest + bash smoke script (71-check-form-sections.sh) which were executed under Behavioral Spot-Checks.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| FORM-01 | 71-01 | `PipelineState.form_factor` field (`landscape`/`portrait`), default `portrait` | ✓ SATISFIED | store.py L75-79 + __post_init__ + 4 unit tests PASS |
| FORM-02 | 71-02 | 15 movie-expert SKILL.md files with `## Form Factor Adaptation` section | ✓ SATISFIED | 71-check-form-sections.sh exits 0; 15/15 sections; tier depth met (4 Tier 1 ≥15L / 5 Tier 2 ~8L / 6 Tier 3 form-agnostic) |
| FORM-03 | 71-01 | `horizontal-screen-framing.md` mirroring `vertical-screen-framing.md` 5-section structure | ✓ SATISFIED | 226 lines, 9 H2 sections, all 5 FORM-03-required present + real film citations with fair-use attribution |
| FORM-04 | 71-03 | Step 14 4-cell reframe matrix without quality degradation | ✓ SATISFIED | `## 4-Cell Reframe Matrix` H2 in platform-master-slicing.md; 20 reframe-math tests PASS; Cell D saliency-scan contract; 8 sample-frame fixtures |
| FORM-05 | 71-01 | `MSR_FC=17` → `MSR_FC=41` per A/B test | ✓ SATISFIED | 5 canonical sweep locations + 1 auto-found code bugfix; `MSR_FC=41` canonical across 10+ files |

**Orphaned requirements:** None. REQUIREMENTS.md maps FORM-01..05 to Phase 71; all 5 IDs claimed by plan frontmatter (71-01: FORM-01/03/05; 71-02: FORM-02; 71-03: FORM-04) and satisfied in codebase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `skills/kais-movie/kais-aigc-platform/references/ltx-video-workflows.md` | 733 | MSR_FC=17 in shell-script example with `# replace 17 with actual msr_fc value` comment | ℹ️ Info | Out-of-scope file (different subsystem `kais-movie/kais-aigc-platform/`, not `kais-movie-pipeline/`); comment explicitly marks value as variable placeholder, not canonical assertion. PLAN 71-01 scope enumerated 5 files; this file was NOT in scope. Not a gap. |

No `TBD` / `FIXME` / `XXX` / `placeholder` / `coming soon` / `not yet implemented` debt markers in any phase-modified file (10 files scanned).

No empty-handler stubs (`return null`, `return []`, `=> {}`, `console.log only`) in phase-modified files.

### Human Verification Required

Per VALIDATION.md §Manual-Only Verifications (3 rows) + Step 8 analysis:

### 1. Horizontal-screen-framing.md citation + license review (FORM-03)

**Test:** Operator reads `horizontal-screen-framing.md` end-to-end and confirms the 6 real-film citations (Grand Budapest Hotel / Revenant / Drive / Shining / 1917 / Lawrence of Arabia) are correctly attributed as analytical references under fair use, not reproductions.
**Expected:** No copyrighted reproductions; citations are paraphrased framing/composition discussion only; LICENSE.md cross-reference intact (L4).
**Why human:** Subjective content-quality + license review per VALIDATION.md Manual-Only row 1; CLAUDE.md copyright constraint cannot be grep-checked. Automated spot-check confirmed structure (5 sections, attribution block exists); only a human can confirm the citations are non-infringing.

### 2. Tier 1 dual-branch substance review (FORM-02)

**Test:** Operator reads the 4 Tier 1 `## Form Factor Adaptation` sections (cinematographer L340 / visual_executor L460 / editor L307 / character_designer L438) and confirms landscape vs portrait rules differ meaningfully (not just string substitution).
**Expected:** Each section has distinct numeric thresholds (power points / headroom % / shot scale distribution / dreamina dims / eye-trace %) per form, not 9:16 text with "landscape" swapped in. Tier 1 line counts already verified ≥15L.
**Why human:** Per-expert content depth is judgment-based per VALIDATION.md Manual-Only row 2. Automated check confirmed line count + dual-branch literal strings; only a human can confirm the landscape rules are substantively correct.

### 3. Step 14 sample-frame visual correctness (FORM-04)

**Test:** Operator reviews the 8 sample-frame PNGs under `_eval/form_factor_step14/` and confirms each before/after pair visually demonstrates the correct cell algorithm.
**Expected:** Cell A/B before==after (pass-through); Cell C after has pillarbox bars visible; Cell D after preserves subject in horizontal center. README.md generation instructions reproducible from `ffmpeg testsrc2`.
**Why human:** Visual regression is manual by design per VALIDATION.md Manual-Only row 3. Automated check confirmed 8 PNGs exist + naming convention; only a human can confirm the images visually demonstrate the reframe algorithm.

### Gaps Summary

No structural gaps. All 5 FORM requirements have automated verification PASSING:
- FORM-01: schema + 4 unit tests green
- FORM-02: 15/15 smoke script + tier depth
- FORM-03: 226-line ref with 5 FORM-03-required sections + citations
- FORM-04: 4-cell matrix + 20 unit tests + 8 fixtures
- FORM-05: 5 canonical sweep locations + 1 auto-found code bugfix

The status is `human_needed` because VALIDATION.md §Manual-Only declares 3 verification items that are structurally unautomatable (subjective citation quality, per-expert content depth, visual regression). These are NOT gaps in the implementation — they are the standard human-gate items for any creative-content phase.

### Notes

**On VALIDATION.md test-path discrepancy:** VALIDATION.md (pre-execution draft) lists test commands like `python -m pytest tests/test_pipeline_state.py::test_form_factor_field`. The actual tests landed in `skills/kais-movie-pipeline/tests/test_form_factor.py` with slightly different test names (e.g., `test_old_json_defaults_to_portrait` vs `test_backward_compat_no_form_factor`). The VALIDATION.md was a pre-execution Nyquist plan; the executor consolidated tests into a single new file. This is a documentation drift, NOT a gap — the substance of every VALIDATION task ID 71-01-01 through 71-03-04 is verified by the tests that actually landed.

**On out-of-scope MSR_FC=17 occurrence:** `skills/kais-movie/kais-aigc-platform/references/ltx-video-workflows.md:733` contains `MSR_FC=17` in a shell-script example block with the explicit comment `# replace 17 with actual msr_fc value`. This is NOT a stale canonical assertion — it's a variable placeholder in an instructional code block. PLAN 71-01 scope enumerated 5 specific files in `skills/kais-movie-pipeline/`; this file is in `skills/kais-movie/kais-aigc-platform/` (a different subsystem). Recommended follow-up: a future phase or ops task can sweep `kais-aigc-platform/` references if desired, but this is explicitly outside Phase 71's scope.

---

_Verified: 2026-07-09T19:30:00Z_
_Verifier: Claude (gsd-verifier)_
