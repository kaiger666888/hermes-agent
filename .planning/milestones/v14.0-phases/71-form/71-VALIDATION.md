---
phase: 71
slug: form
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 71 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (python 3.11+, already pinned in `kais-hermes-skills/pyproject.toml`); bash smoke script for lineage assertions |
| **Config file** | `kais-hermes-skills/pyproject.toml` `[tool.pytest.ini_options]` (existing); `kais-hermes-skills/tests/` (existing) |
| **Quick run command** | `cd /data/workspace/kais-hermes-skills && python -m pytest tests/test_pipeline_state.py tests/test_form_factor.py -x -q` |
| **Full suite command** | `cd /data/workspace/kais-hermes-skills && python -m pytest tests/ -x -q && bash .planning/phases/71-form/71-smoke.sh` |
| **Estimated runtime** | ~15 seconds (quick); ~45 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command (pytest on touched test files)
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green AND `71-smoke.sh` must exit 0
- **Max feedback latency:** 15 seconds (quick) / 45 seconds (full)

---

## Per-Task Verification Map

> Tasks IDs follow `{phase}-{plan}-{task}` convention. Plan A = 71-01, Plan B = 71-02, Plan C = 71-03.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 71-01-01 | 01 (Foundation) | 1 | FORM-01 | — | PipelineState accepts `form_factor="landscape"` / `"portrait"`; rejects unknown values via Pydantic ValidationError | unit | `python -m pytest tests/test_pipeline_state.py::test_form_factor_field -xvs` | ❌ W0 | ⬜ pending |
| 71-01-02 | 01 | 1 | FORM-01 | — | Old episode JSON without `form_factor` key loads cleanly, defaults to `"portrait"` | unit | `python -m pytest tests/test_pipeline_state.py::test_backward_compat_no_form_factor -xvs` | ❌ W0 | ⬜ pending |
| 71-01-03 | 01 | 1 | FORM-01 | — | Episode JSON with per-shot `form_factor` override is REJECTED by validator (episode-level invariant) | unit | `python -m pytest tests/test_pipeline_state.py::test_reject_per_shot_form_factor -xvs` | ❌ W0 | ⬜ pending |
| 71-01-04 | 01 | 1 | FORM-05 | — | `grep -rn "MSR_FC=17"` returns 0 hits across `skills/` (5 doc locations swept: SKILL.md:446, p11-single-shot-orchestration.md:75+85, post-production-audit.md:156, ltx-msr-workflow-spec.md:121) | bash | `bash -c '! grep -rn "MSR_FC=17" skills/'` | ❌ W0 | ⬜ pending |
| 71-01-05 | 01 | 1 | FORM-05 | — | `MSR_FC=41` is canonical in docs (template script already has `MSR_FC_DEFAULT = 41` at line 67) | grep | `grep -rn "MSR_FC=41" skills/ | wc -l` ≥ 5 | ❌ W0 | ⬜ pending |
| 71-01-06 | 01 | 1 | FORM-01 | — | LTX-MSR template accepts `--form-factor landscape` and resolves to `width=1280 height=704`; `--form-factor portrait` resolves to `width=704 height=1280` | unit | `python -m pytest tests/test_ltx_msr_template.py::test_form_factor_resolution_mapping -xvs` | ❌ W0 | ⬜ pending |
| 71-01-07 | 01 | 2 | FORM-03 | — | `skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` exists, ≥150 lines, mirrors 5-section structure of vertical-screen-framing.md | bash | `test -f skills/movie-experts/cinematographer/references/horizontal-screen-framing.md && wc -l skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` | ❌ W0 | ⬜ pending |
| 71-01-08 | 01 | 2 | FORM-03 | — | horizontal-screen-framing.md has all 5 H2 section headers (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region) | grep | `grep -c "^## " skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` ≥ 5 | ❌ W0 | ⬜ pending |
| 71-01-09 | 01 | 2 | FORM-02 (partial) | — | Pipeline orchestrator (`kais-movie-pipeline/SKILL.md` line 40) reads `form_factor` from PipelineState; drops "All 15 movie-experts assume this form" claim | grep | `grep -c "All 15 movie-experts assume" skills/kais-movie-pipeline/SKILL.md` == 0 | ❌ W0 | ⬜ pending |
| 71-02-01 | 02 (15 patches) | 1 | FORM-02 | — | All 15 active movie-expert SKILL.md files have `## Form Factor Adaptation` section (canonical 15: hook_retention, creative_source, screenplay, script_auditor, character_designer, cinematographer, style_genome, prompt_injector, visual_executor, continuity_auditor, audio_pipeline, editor, colorist, compliance_gate, theory_critic) | bash | `bash .planning/phases/71-form/71-check-form-sections.sh` exits 0 | ❌ W0 | ⬜ pending |
| 71-02-02 | 02 | 1 | FORM-02 | — | Tier 1 experts (cinematographer, visual_executor, editor — full form-critical set per research) have substantive dual-branch (≥15 lines) | bash | `for expert in cinematographer visual_executor editor; do wc -l skills/movie-experts/$expert/SKILL.md; done` (each ≥ baseline + 15) | ❌ W0 | ⬜ pending |
| 71-02-03 | 02 | 1 | FORM-02 | — | Tier 3 experts (audio_pipeline, colorist — form-agnostic per research) have explicit stub section saying "form-agnostic" | grep | `grep -l "form-agnostic" skills/movie-experts/audio_pipeline/SKILL.md skills/movie-experts/colorist/SKILL.md` exits 0 | ❌ W0 | ⬜ pending |
| 71-02-04 | 02 | 1 | FORM-02 | — | Cinematographer Step 3 (Composition per Shot) branches on `form_factor` and loads right ref (horizontal vs vertical) | grep | `grep -A 10 "Step 3" skills/movie-experts/cinematographer/SKILL.md | grep -c "form_factor"` ≥ 1 | ❌ W0 | ⬜ pending |
| 71-03-01 | 03 (Step 14) | 1 | FORM-04 | — | `references/platform-master-slicing.md` has 4-cell matrix section covering all 4 combinations (16:9→9:16 / 9:16→16:9 / 16:9→16:9 / 9:16→9:16) | grep | `grep -cE "16:9.*9:16|9:16.*16:9|portrait.*landscape|landscape.*portrait" skills/kais-movie-pipeline/references/platform-master-slicing.md` ≥ 4 | ❌ W0 | ⬜ pending |
| 71-03-02 | 03 | 1 | FORM-04 | — | Step 14 reframe math unit test: portrait→portrait = pass-through; landscape→landscape = pass-through; portrait→landscape = letterbox/reframe; landscape→portrait = center-crop with saliency | unit | `python -m pytest tests/test_step14_reframe_matrix.py -xvs` | ❌ W0 | ⬜ pending |
| 71-03-03 | 03 | 2 | FORM-04 | — | 8 sample-frame fixtures committed under `_eval/form_factor_step14/` (4 cells × before/after) | bash | `ls _eval/form_factor_step14/*.png 2>/dev/null | wc -l` ≥ 8 | ❌ W0 | ⬜ pending |
| 71-03-04 | 03 | 1 | FORM-04 | — | Regression: existing vertical-master behavior preserved (cell portrait→portrait now explicit; existing Step 14 tests still green) | unit | `python -m pytest tests/test_step14_existing.py -xvs` (pre-existing tests) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `kais-hermes-skills/tests/test_pipeline_state.py` — extend existing or create new; stubs for FORM-01 tests (form_factor_field / backward_compat_no_form_factor / reject_per_shot_form_factor)
- [ ] `kais-hermes-skills/tests/test_ltx_msr_template.py` — stub for `--form-factor` resolution mapping (extend if exists)
- [ ] `kais-hermes-skills/tests/test_step14_reframe_matrix.py` — new file; 4-cell matrix tests
- [ ] `kais-hermes-skills/_eval/form_factor_step14/` — new directory; 8 sample-frame fixtures (can be placeholder PNGs initially)
- [ ] `.planning/phases/71-form/71-check-form-sections.sh` — bash script enumerating 15 canonical active experts and asserting each SKILL.md has `## Form Factor Adaptation` section
- [ ] `.planning/phases/71-form/71-smoke.sh` — top-level smoke script (XCUT-01 style) running all assertions

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| horizontal-screen-framing.md content quality (real-film citations under fair-use) | FORM-03 | Subjective quality + license review | Operator reads the ref end-to-end; confirms citations are correctly attributed per CLAUDE.md copyright constraint |
| Tier 1 SKILL.md dual-branch substantive content (not just stub) | FORM-02 | Per-expert content depth is judgment-based | Operator reads 3 Tier 1 experts' `## Form Factor Adaptation` sections; confirms dual-branch rules differ meaningfully between landscape/portrait |
| Step 14 sample-frame fixtures visual correctness | FORM-04 | Visual regression is manual by design | Operator reviews 8 frames; confirms reframe logic preserved primary info in each cell |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s (full suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
