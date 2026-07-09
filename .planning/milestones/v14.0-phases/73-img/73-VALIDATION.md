---
phase: 73
slug: img
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 73 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (python 3.11+); bash smoke script for dreamina CLI + GLM-4.6V probes |
| **Config file** | `kais-hermes-skills/pyproject.toml` `[tool.pytest.ini_options]` (existing) |
| **Quick run command** | `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py plugins/kais_aigc/tests/test_vision_verify.py -x -q` |
| **Full suite command** | `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/kais_aigc/tests/ skills/kais-movie-pipeline/tests/test_p07_unit.py -x -q && bash .planning/phases/73-img/73-smoke.sh` |
| **Estimated runtime** | ~25 seconds (quick); ~70 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite green AND `73-smoke.sh` exits 0
- **Max feedback latency:** 25s (quick) / 70s (full)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 73-01-01 | 01 (Foundation) | 1 | IMG-01 | T-73-01 | `dreamina_manager.batch_generate()` uses `asyncio.Semaphore(10)` + tenacity retry + sync queue (blocks on poll-all-before-deadline) | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_semaphore_cap_10 -xvs` | ❌ W0 | ⬜ pending |
| 73-01-02 | 01 | 1 | IMG-01 | — | tenacity retry on `TimeoutError`, `ConnectionError`, dreamina transient errors; exponential backoff (1s,2s,4s,8s); max 4 retries | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_retry_strategy -xvs` | ❌ W0 | ⬜ pending |
| 73-01-03 | 01 | 1 | IMG-02 | — | `batch_generate()` blocks `pipeline_state` write until ALL retries resolve (no async write order bug) | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_blocks_until_all_resolve -xvs` | ❌ W0 | ⬜ pending |
| 73-01-04 | 01 | 1 | IMG-03 | T-73-02 | `vision_verify.verify_image_content(image_path, expected_content, directional_check)` calls GLM-4.6V via `auxiliary_client.async_call_llm(prefer_vision=True)` | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_verify_calls_glm -xvs` | ❌ W0 | ⬜ pending |
| 73-01-05 | 01 | 1 | IMG-03 | — | Vision-verify batches 4-8 images per GLM-4.6V call (per PITFALL I-1 mitigation #1) | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_batch_4_to_8_images -xvs` | ❌ W0 | ⬜ pending |
| 73-01-06 | 01 | 1 | IMG-03 | — | Vision-verify sha256-keyed cache prevents re-verifying same image within TTL (24h default) | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_cache_hits -xvs` | ❌ W0 | ⬜ pending |
| 73-01-07 | 01 | 1 | IMG-03 | — | Confidence-gated enforcement: low confidence (<70%) OR content mismatch (>30%) flagged for human review; high-confidence passes auto | unit | `python -m pytest plugins/kais_aigc/tests/test_vision_verify.py::test_confidence_gating -xvs` | ❌ W0 | ⬜ pending |
| 73-01-08 | 01 | 1 | IMG-05 | — | MetricsBuffer ring buffer at `~/.hermes/metrics/dreamina_stats.jsonl` (sync @contextmanager pattern per v13.0 P67 precedent) | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_stats.py::test_metrics_buffer_persist -xvs` | ❌ W0 | ⬜ pending |
| 73-02-01 | 02 (Integration) | 2 | IMG-04 | T-73-03 | RHD/LHD 3-attempt budget: attempt 1 (LHD prompt) → attempt 2 (stronger prompt + negative) → attempt 3 (image2image fallback) | unit | `python -m pytest plugins/kais_aigc/tests/test_dreamina_manager.py::test_rhd_lhd_3_attempt_budget -xvs` | ❌ W0 | ⬜ pending |
| 73-02-02 | 02 | 2 | IMG-04 | — | Vision-verify asks explicit `"left_hand_drive? yes/no"` question per PITFALL I-4 mitigation #2 | grep | `grep -c "left_hand_drive" plugins/kais_aigc/vision_verify.py` ≥ 1 | ❌ W0 | ⬜ pending |
| 73-02-03 | 02 | 2 | IMG-06 | — | `references/image2image-stratification.md` documents 1-ref / 3-ref / 5-ref strata with strength + retry budget per stratum | bash | `test -f skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md && grep -c "1-ref\|3-ref\|5-ref" skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md` ≥ 3 | ❌ W0 | ⬜ pending |
| 73-02-04 | 02 | 2 | IMG-05 | — | `hermes dreamina stats` CLI command registered via plugin context; outputs per-task latency / success rate / cost dashboard | grep | `grep -c "dreamina" plugins/kais_aigc/plugin.yaml` ≥ 1 AND `grep -c "register_cli_command\|dreamina_stats" plugins/kais_aigc/tools.py` ≥ 1 | ❌ W0 | ⬜ pending |
| 73-02-05 | 02 | 2 | XCUT-02 | — | `_VISION_VERIFY_INSTRUCTION` constant injected into p07_scene_images.py `.task(steps=)` AND `.constraints()` | grep | `grep -c "_VISION_VERIFY_INSTRUCTION" skills/kais-movie-pipeline/pipeline/phases/p07_scene_images.py` ≥ 2 | ❌ W0 | ⬜ pending |
| 73-02-06 | 02 | 2 | IMG-03 | — | SKILL.md pitfalls patched: vision-verify mandatory gate language at kais-movie-pipeline/SKILL.md line ~561 + kais-jimeng-cli/SKILL.md | grep | `grep -c "vision-verify.*mandatory\|mandatory.*vision-verify" skills/kais-movie-pipeline/SKILL.md skills/kais-creative/kais-jimeng-cli/SKILL.md` ≥ 1 | ❌ W0 | ⬜ pending |
| 73-02-07 | 02 | 2 | IMG-04 | — | SKILL.md RHD/LHD pitfall updated at kais-movie-pipeline/SKILL.md line ~570 to reference 3-attempt budget (Volvo V2 lesson) | grep | `grep -A 5 "RHD\|LHD\|left-hand drive\|right-hand drive" skills/kais-movie-pipeline/SKILL.md \| grep -c "3-attempt\|3 attempt"` ≥ 1 | ❌ W0 | ⬜ pending |
| 73-03-01 | 03 (Validation) | 2 | IMG-01 | — | Integration test: 3-shot batch generates via dreamina_manager, all 3 succeed, pipeline_state writes only after all resolve | integration | `python -m pytest plugins/kais_aigc/tests/test_integration.py::test_batch_e2e -xvs` | ❌ W0 | ⬜ pending |
| 73-03-02 | 03 | 2 | IMG-04 | — | Integration test: RHD prompt failure triggers verify-retry; second failure triggers image2image fallback; 3rd attempt either succeeds or surfaces operator-actionable error | integration | `python -m pytest plugins/kais_aigc/tests/test_integration.py::test_rhd_lhd_e2e -xvs` | ❌ W0 | ⬜ pending |
| 73-03-03 | 03 | 2 | XCUT-02 | — | Goal-content test asserts `_VISION_VERIFY_INSTRUCTION` keyword appears in `captured["goal"]` for p07_scene_images | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_p07_unit.py::test_goal_includes_vision_verify_instruction -xvs` | ❌ W0 | ⬜ pending |
| 73-03-04 | 03 | 2 | IMG-05 | — | `hermes dreamina stats` CLI invocation returns non-zero exit on missing data; formatted table on populated buffer | bash | `bash .planning/phases/73-img/73-smoke.sh` exits 0 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_manager.py` — new file; stubs for IMG-01/02/04 tests
- [ ] `kais-hermes-skills/plugins/kais_aigc/tests/test_vision_verify.py` — new file; stubs for IMG-03 tests
- [ ] `kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_stats.py` — new file; stubs for IMG-05 tests
- [ ] `kais-hermes-skills/plugins/kais_aigc/tests/test_integration.py` — new file; e2e integration tests
- [ ] `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p07_unit.py` — extend if exists, or new file; goal-content assertion
- [ ] `.planning/phases/73-img/73-smoke.sh` — top-level smoke script (XCUT-01 style)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GLM-4.6V vision-verify accuracy on dreamina-generated interior shots | IMG-03 (PITFALL I-2) | Requires actual dreamina-generated images + subjective content-match review | Operator runs `verify_image_content()` on 5-10 production images; records false-positive rate |
| RHD/LHD 3-attempt budget success rate ≥95% | IMG-04 | Requires actual dreamina RHD failure injection + 3-attempt budget execution at production scale | Operator runs 20-shot batch with RHD-prone prompts; counts attempts-to-success |
| GLM-4.6V batch calls cost at production scale (XCUT-04c) | IMG-03 + XCUT-04 | Requires production-scale image volume (213-shot × 5 refs) | Operator runs full project; documents GLM-4.6V API spend; records in milestone audit |
| `hermes dreamina stats` dashboard correctness on long history | IMG-05 | Requires accumulated MetricsBuffer data over multiple sessions | Operator runs 3+ pipeline sessions; verifies dashboard aggregates correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 70s (full suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
