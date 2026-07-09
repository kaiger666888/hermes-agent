---
phase: 72
slug: dub
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 72 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (python 3.11+); bash smoke script for live service probes |
| **Config file** | `kais-hermes-skills/pyproject.toml` `[tool.pytest.ini_options]` (existing) |
| **Quick run command** | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/test_dub_division.py skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py -x -q` |
| **Full suite command** | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/ -x -q && bash .planning/phases/72-dub/72-smoke.sh` |
| **Estimated runtime** | ~20 seconds (quick); ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command (pytest on touched test files)
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green AND `72-smoke.sh` must exit 0
- **Max feedback latency:** 20 seconds (quick) / 60 seconds (full)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 72-01-01 | 01 (Foundation) | 1 | DUB-02 | T-72-01 | `validate_tts_engine_division(shot_list)` rejects any shot with both `ltx_native_dialogue=True` AND `tts_engine='cosyvoice'` | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub_division.py::test_division_rejects_both_on -xvs` | ❌ W0 | ⬜ pending |
| 72-01-02 | 01 | 1 | DUB-02 | — | Validator allows each engine individually (ltx_native only / cosyvoice only / indextts2_fallback only) AND both-off | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub_division.py::test_division_allows_ltx_native_only -xvs` AND `::test_division_allows_cosyvoice_only -xvs` AND `::test_division_allows_both_off -xvs` | ❌ W0 | ⬜ pending |
| 72-01-03 | 01 | 1 | DUB-02 | — | Shot dict accepts new `tts_engine: Literal["ltx_native","cosyvoice","indextts2_fallback"]` field + `ltx_native_dialogue: bool` field with sensible defaults; rejects invalid tts_engine values | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub_division.py::test_division_rejects_invalid_tts_engine -xvs` | ❌ W0 | ⬜ pending |
| 72-01-04 | 01 | 1 | DUB-03 | — | `character_bible.json` V3 envelope accepts new `voice_clone_reference_wav` field as sibling to `4d_anchor.voice`; old JSON without field loads cleanly | unit | `python -m pytest skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py::test_character_bible_field_additive -xvs` | ❌ W0 | ⬜ pending |
| 72-01-05 | 01 | 1 | DUB-03 | — | `validate_voice_clone_ref(path)` accepts 3-10s wav at ≥16kHz; rejects <3s, >10s, mp3, <16kHz | unit | `python -m pytest skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py -k "validate_ref or reject" -xvs` | ❌ W0 | ⬜ pending |
| 72-01-06 | 01 | 1 | DUB-03 | — | `templates/tts_batch.py` fails fast with explicit operator-actionable error when CosyVoice clone mode selected + `voice_clone_reference_wav` missing | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub_division.py::test_cosyvoice_fail_fast_missing_ref -xvs` | ❌ W0 | ⬜ pending |
| 72-02-01 | 02 (Routing + DEPRECATED fallback) | 2 | DUB-01 | — | ComfyUI workflow JSON at `references/workflows/cosyvoice-comfyui.json` uses `AIIA_CosyVoice_TTS` + `AIIA_CosyVoice_ModelLoader` nodes (NOT filliptm) | grep | `grep -c "AIIA_CosyVoice" skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json` ≥ 2 | ❌ W0 | ⬜ pending |
| 72-02-02 | 02 | 2 | DUB-01 | — | Pre-flight healthcheck probes gold-team `/api/v1/engines` for CosyVoice-300M AND ComfyUI `/object_info/AIIA_CosyVoice_TTS`; falls back to IndexTTS2 with DEPRECATED warning if both missing | bash | `bash -c 'grep -c "CosyVoice-300M\|AIIA_CosyVoice_TTS" skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh'` ≥ 1 | ❌ W0 | ⬜ pending |
| 72-02-03 | 02 | 2 | DUB-04 | — | Auto-fallback on CosyVoice generation failure routes to IndexTTS2; DEPRECATED flag set in workflow metadata | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub_division.py::test_indextts2_fallback_logs_deprecated -xvs` | ❌ W0 | ⬜ pending |
| 72-02-04 | 02 | 2 | DUB-04 | — | `kais-movie-pipeline/SKILL.md` line 457 IndexTTS2 reference demoted to DEPRECATED fallback status | grep | `grep -A 5 "IndexTTS2" skills/kais-movie-pipeline/SKILL.md \| grep -c "DEPRECATED\|fallback"` ≥ 1 | ❌ W0 | ⬜ pending |
| 72-02-05 | 02 | 2 | XCUT-02 | — | `_TTS_ENGINE_INSTRUCTION` constant injected into p10_voice.py (or equivalent P10 module) `.task(steps=)` AND `.constraints()` | grep | `grep -c "_TTS_ENGINE_INSTRUCTION" skills/kais-movie-pipeline/pipeline/phases/p10_voice.py` ≥ 2 | ❌ W0 | ⬜ pending |
| 72-03-01 | 03 (Docs + VERSION.json) | 2 | DUB-01 | — | `cosyvoice-deployment.md` documents both paths: gold-team + ComfyUI AIIA; ≥100 lines | bash | `test -f skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md && wc -l skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md` ≥ 100 | ❌ W0 | ⬜ pending |
| 72-03-02 | 03 | 2 | DUB-05 | — | `VERSION.json` exists at `kais-hermes-skills/VERSION.json` with `cosyvoice_default_variant` field | bash | `test -f VERSION.json && jq -e '.cosyvoice_default_variant' VERSION.json` exits 0 | ❌ W0 | ⬜ pending |
| 72-03-03 | 03 | 2 | DUB-05 | — | `cosyvoice-benchmark.md` exists with benchmark report template (operator fills in actual A/B data); documents 3-5 dialogue lines + evaluation criteria | bash | `test -f skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md && wc -l skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md` ≥ 50 | ❌ W0 | ⬜ pending |
| 72-03-04 | 03 | 2 | DUB-03 | — | `indextts2-to-cosyvoice-migration.md` mapping table documents voice_preset (sad/calm/happy/melancholic) → CosyVoice profile migration | bash | `test -f skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md` | ❌ W0 | ⬜ pending |
| 72-03-05 | 03 | 2 | DUB-03 | — | Operator-action handoff doc references voice_clone_reference_wav per character (3-10s samples) — preserved for Phase 76 VALIDATE milestone audit | grep | `grep -c "voice_clone_reference_wav" .planning/phases/72-dub/72-SUMMARY.md` ≥ 1 (after execution) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_dub_division.py` — new file; stubs for DUB-02 validator tests + DUB-04 fallback tests (consolidated per planner)
- [ ] `kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_voice_clone_ref.py` — new file; stubs for DUB-03 validation tests
- [ ] `.planning/phases/72-dub/72-smoke.sh` — top-level smoke script (XCUT-01 style) running all assertions

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CosyVoice A/B benchmark on 3-5 reference dialogue lines (operator-provided) | DUB-05 | Operator-action handoff — requires actual audio files + subjective side-by-side review | Operator runs A/B benchmark using `cosyvoice-benchmark.md` template; records default variant in VERSION.json |
| `voice_clone_reference_wav` per character sourcing | DUB-03 | Operator-action handoff — requires operator to source 3-10s clean audio samples per character | Operator creates wavs at `assets/<episode>/voice_refs/<character>.wav`; runs `validate_voice_clone_ref()` to verify format |
| CosyVoice generation quality under concurrent LTX-2.3 GPU load | DUB-01 (PITFALL D-5) | Requires actual production-scale GPU contention test | Operator runs P10 + P11 in parallel on representative project; documents VRAM budget in cosyvoice-deployment.md |
| IndexTTS2 fallback path triggers correctly on actual CosyVoice failure | DUB-04 | Requires injecting real CosyVoice failure (stop service / corrupt input) | Operator triggers CosyVoice failure mid-batch; verifies IndexTTS2 fallback fires + DEPRECATED warning logged |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s (full suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
