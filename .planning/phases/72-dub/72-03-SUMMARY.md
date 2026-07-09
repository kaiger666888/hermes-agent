---
phase: 72-dub
plan: 03
subsystem: dub (TTS / voice layer — docs + VERSION.json + benchmark template + migration mapping + smoke runner)
tags: [dub, tts, cosyvoice, indextts2, version-json, benchmark, migration, smoke, deployment-doc, dub-01, dub-03, dub-05]
requires: [72-01 (validate_tts_engine_division + voice clone schema), 72-02 (workflow JSON + SKILL.md demotion + XCUT-02)]
provides:
  - cosyvoice-deployment.md dual-path deployment doc (DUB-01 — ComfyUI AIIA + gold-team CosyVoice-300M)
  - VERSION.json top-level repo meta with tts.cosyvoice_default_variant lock site (DUB-05)
  - cosyvoice-benchmark.md A/B benchmark TEMPLATE for operator-action handoff (DUB-05)
  - indextts2-to-cosyvoice-migration.md voice_preset → CosyVoice mapping (DUB-03)
  - 72-smoke.sh 11-assertion XCUT-01 smoke runner for Phase 76 VALIDATE
affects:
  - Phase 76 VALIDATE (72-smoke.sh is the Phase 72 XCUT-01 audit input)
  - DUB-05 operator-action handoff (operator runs A/B benchmark + locks VERSION.json)
tech-stack:
  added: []  # zero new packages — markdown + JSON + bash only
  patterns:
    - Ref Twin Authoring (cosyvoice-deployment.md mirrors comfyui-indextts2-setup.md 9-section structure + 3 CosyVoice-specific additions)
    - Greenfield meta file (VERSION.json — no prior top-level repo meta; RESEARCH confirmed find returned 0 results)
    - Operator-action handoff template (cosyvoice-benchmark.md — skeleton only, data deferred per DUB-05 locked decision)
    - Smoke script grep/file/python-import assertions (mirrors 70-smoke.sh skeleton)
key-files:
  created:
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md
    - kais-hermes-skills/VERSION.json
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md
    - kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md
    - .planning/phases/72-dub/72-smoke.sh
decisions:
  - "VERSION.json at top-level kais-hermes-skills/ (NOT skills-scoped) — RESEARCH confirmed no existing VERSION.json"
  - "tts.cosyvoice_default_variant defaults null — DUB-05 operator-action handoff (NOT auto-pick-lower-WER)"
  - "cosyvoice-benchmark.md is a TEMPLATE (operator fills actual A/B data) — scope guardrail preserved, no pre-filled numbers"
  - "cosyvoice-deployment.md documents BOTH paths: ComfyUI AIIA Fun-CosyVoice3-0.5B-2512 (SOTA) + gold-team CosyVoice-300M (operational)"
  - "indextts2-to-cosyvoice-migration.md anti-pattern: CosyVoice zero-shot clone has NO IndexTTS2 equivalent (fundamentally different mechanisms)"
  - "72-smoke.sh does NOT invoke live Docker/ComfyUI/gold-team — those are operator-action handoff probes documented in deployment doc Healthcheck section"
metrics:
  duration: ~7min
  completed: 2026-07-09
  tasks: 4
  files_created: 5
  files_modified: 0
  tests_added: 0
  commits: 5 (4 kais-hermes-skills + 1 hermes-agent)
---

# Phase 72 Plan 03: Docs + VERSION.json + Benchmark Template + Migration Mapping + Smoke Runner Summary

DUB-01 dual-path deployment doc (cosyvoice-deployment.md — 286 lines mirroring indextts2 twin + 3 CosyVoice-specific sections) + DUB-05 VERSION.json top-level repo meta (greenfield — tts.cosyvoice_default_variant defaults null for operator-action handoff) + DUB-05 cosyvoice-benchmark.md A/B benchmark TEMPLATE (120 lines — operator fills actual data) + DUB-03 indextts2-to-cosyvoice-migration.md (voice_preset mapping table + emotion slider → instruct_text + clone anti-pattern) + 72-smoke.sh 11-assertion XCUT-01 smoke runner for Phase 76 VALIDATE.

## What Was Built

### Task 1: cosyvoice-deployment.md (commit a626256)

**`skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md`** (NEW — 286 lines) — Structural twin of `comfyui-indextts2-setup.md` with 11 H2 sections:

- **9 mirrored sections** (per PATTERNS.md twin mapping): Title+Source+Context+Container name (with de-phantom note: gold-team CosyVoice-300M already operational), Node Overview table (AIIA_CosyVoice_ModelLoader/TTS/VoiceConversion), Voice Presets (base_gender + dialect + emotion + instruct_text + reference_audio), Emotion Control (enum tags + free-form Chinese instruct_text), Working API-Format Workflow (embeds cosyvoice-comfyui.json JSON block), Dependency Setup (verify in-container note — no invented dep names), Non-blocking Batch Submission (python requests + ComfyUI /prompt + /history poll), Alternative: Gold-team TTS (CosyVoice-300M IS operational — de-phantom'd), Model Location (Fun-CosyVoice3-0.5B-2512 paths).
- **3 CosyVoice-specific sections** (no IndexTTS2 analog): GPU VRAM Budget (~2GB baseline, ~3GB with RL; LTX-MSR ~23GB concurrent contention per PITFALL D-5), Healthcheck (ComfyUI `/object_info/AIIA_CosyVoice_TTS` + gold-team `/api/v1/engines` + references probe-tts-routing.sh), Known Issues (silent-output detection, gold-team permission denied, reference_audio path resolution, RL model VRAM spike, multi-emotion segment detection).
- **Vendor note:** AIIA nodes (already installed) — NOT filliptm/ComfyUI_FL-CosyVoice3 (NOT installed per RESEARCH Critical Correction #1).

### Task 2: VERSION.json (commit 88249db)

**`kais-hermes-skills/VERSION.json`** (NEW — top-level, greenfield) — Pipeline-wide default variant lock meta:

- `schema_version: "1.0"`, `pipeline_version: "v14.0"`, `_comment` explaining the operator-action handoff protocol.
- `tts.cosyvoice_default_variant: null` — DUB-05 operator-action handoff lock site. Acceptable post-benchmark values: `"fun_cosyvoice_3.0_0.5B_2512"`, `"cosyvoice_2.0_0.5B"`, `"cosyvoice_300M_gold_team"`.
- `tts.lock_date: null` + `tts.lock_rationale: null` — operator fills after A/B benchmark review.
- `tts.alternative_tested: [...]` — 3 variants the operator should A/B test per DUB-05.
- `tts.benchmark_report_path: "skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md"` — links to the benchmark template.

**jq path note:** The plan's acceptance criterion used `jq -e '.tts.cosyvoice_default_variant'` which returns exit 1 on null (jq `-e` treats null as falsy). Corrected form `jq -e '.tts.cosyvoice_default_variant == null'` exits 0, confirming the field exists and is null. Per plan critical_context self-correcting note.

### Task 3: cosyvoice-benchmark.md (commit 94a9f40)

**`skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md`** (NEW — 120 lines) — TEMPLATE the operator fills after running DUB-05 A/B benchmark:

- **Benchmark Protocol:** 5-step process (select 3-5 lines covering emotional range → generate via each variant → evaluate MOS/WER/subjective → record results → lock VERSION.json).
- **Reference Dialogue Lines:** 5 placeholder slots (`<operator fills: line text + emotion tag + expected duration + speaker character>`). Selection guidance: span emotional/voiceover/fast/slow/technical mix.
- **Variants Tested table:** 3 variant rows pre-filled with model_dir paths (cosyvoice_2.0_0.5B → TBD; fun_cosyvoice_3.0_0.5B_2512 → /root/ComfyUI/models/cosyvoice/; cosyvoice_300M_gold_team → :8002).
- **A/B Results table:** 9+ empty rows for (line_id, variant) combinations. 26 `<operator fills>` placeholders — scope guardrail preserved (NO pre-filled numbers).
- **Default Lock Decision:** operator manually picks variant (NOT auto-pick-lower-WER per CONTEXT DUB-05). Lock instructions update VERSION.json.
- **Open Questions:** DUB-06 (real-time streaming), DUB-07 (instruct2 fine-grained), multi-speaker dialog, cross-shot voice_identity (v15+).

### Task 4: indextts2-to-cosyvoice-migration.md (commit df71fde) + 72-smoke.sh (commit 3a8949bf0)

**`skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md`** (NEW — 74 lines) — 3 sections:

1. **Voice Preset Mapping Table:** 6 rows mapping IndexTTS2 voice_preset + emotion sliders → CosyVoice base_gender + emotion + instruct_text. Covers Female_HQ/Male_HQ/Female/Male + sad/calm/happy/melancholic/afraid/surprised combinations.
2. **Emotion Slider → Instruct Text:** prose section explaining the translation heuristic (high slider value ≥0.5 → emotion enum + Chinese prosody description). Tradeoff: CosyVoice instruct_text is more expressive but less reproducible.
3. **Anti-Pattern: Voice Clone Has No IndexTTS2 Equivalent:** documents that CosyVoice zero-shot clone (`reference_audio` input) is a fundamentally different mechanism from IndexTTS2 voice_preset. Migration options: preset migration (zero operator action) vs clone migration (DUB-03 operator-action handoff).

**`.planning/phases/72-dub/72-smoke.sh`** (NEW — 124 lines, executable) — Phase 72 XCUT-01 smoke runner with 11 assertions:
- DUB-01a: cosyvoice-comfyui.json exists
- DUB-01b: cosyvoice-deployment.md >= 5 H2 sections
- DUB-02a: validate_tts_engine_division importable from store.py
- DUB-02b: TTS_ENGINE_VALUES in store.py
- DUB-03a: TTS_ENGINE_VALUES contains ltx_native + cosyvoice
- DUB-03b: dub_validators.py exists
- DUB-04a: SKILL.md IndexTTS2 marked DEPRECATED/fallback
- DUB-05a: VERSION.json has tts.cosyvoice_default_variant
- DUB-05b: cosyvoice-benchmark.md exists
- XCUT-02a: _TTS_ENGINE_INSTRUCTION in p10_voice.py
- XCUT-02b: "MUST propagate tts_engine" constraint in p10_voice.py

All 11 assertions verified PASS against kais-hermes-skills HEAD `df71fde`. Does NOT invoke live Docker/ComfyUI/gold-team (operator-action handoff probes documented in deployment doc Healthcheck section).

## Commits

### kais-hermes-skills repo

| Hash | Message | Task |
|------|---------|------|
| a626256 | docs(72-03): add cosyvoice-deployment.md (DUB-01 dual-path deployment doc) | 1 |
| 88249db | feat(72-03): add top-level VERSION.json (DUB-05 default lock site) | 2 |
| 94a9f40 | docs(72-03): add cosyvoice-benchmark.md template (DUB-05 A/B benchmark) | 3 |
| df71fde | docs(72-03): add indextts2-to-cosyvoice-migration.md (DUB-03 migration mapping) | 4 |

**kais-hermes-skills HEAD:** `1320728` (Plan 72-02 complete) → `df71fde` (Plan 72-03 complete)

### hermes-agent repo

| Hash | Message | Task |
|------|---------|------|
| 3a8949bf0 | feat(72-03): add Phase 72 smoke runner (11 XCUT-01 assertions) | 4 |

## Deviations from Plan

None - plan executed exactly as written. The jq path inconsistency (`.cosyvoice_default_variant` first form vs `.tts.cosyvoice_default_variant` corrected form) was noted in the plan critical_context as a self-correcting issue; the corrected nested path was used throughout execution.

## Operator-Action Handoff Items (Phase 76 VALIDATE inputs — XCUT-04)

These items are documented in the deliverables but NOT implemented in code — they require operator action:

### DUB-03: Voice Clone Reference Wavs
- **What:** Operator sources 3-10s clean voice_clone_reference_wav per character.
- **Where:** `assets/<episode>/voice_refs/<character>.wav` (relative path from project root).
- **Validation:** `validate_voice_clone_ref(path)` — enforces 3-10s duration, wav format, >=16kHz sample rate. Implemented in Plan 72-01 Task 2.
- **Handoff doc:** `cosyvoice-deployment.md` §Known Issues (reference_audio path resolution) + `indextts2-to-cosyvoice-migration.md` §Anti-Pattern (clone migration option).

### DUB-05: A/B Benchmark Execution + Default Lock
- **What:** Operator runs A/B benchmark on 3-5 representative Chinese dialogue lines across 3 CosyVoice variants, then locks the default.
- **Where:** Use `cosyvoice-benchmark.md` template (Plan 72-03 Task 3). Record results in the A/B Results table.
- **Lock:** Edit `VERSION.json` — set `tts.cosyvoice_default_variant` to the chosen variant, `tts.lock_date` to benchmark close date, `tts.lock_rationale` to 1-2 sentence summary.
- **NOT auto-pick-lower-WER:** Per CONTEXT DUB-05 locked decision — audio quality ≠ WER. Operator manually picks after side-by-side review.

## TDD Gate Compliance

N/A — Plan 72-03 has no `tdd="true"` frontmatter. All tasks are `type="auto"` documentation + JSON + bash creation. No RED/GREEN cycle required. Verification via file-existence + grep-count + bash syntax check + smoke script execution (all PASS).

## Known Stubs

None. All deliverables are complete documentation/template/meta files. The `<operator fills>` placeholders in `cosyvoice-benchmark.md` are intentional template slots (DUB-05 operator-action handoff), not code stubs.

## Test Results

```
VALIDATION 72-03-01: cosyvoice-deployment.md — 286 lines (>= 100) PASS
VALIDATION 72-03-02: VERSION.json tts.cosyvoice_default_variant — PASS (null, operator-action handoff)
VALIDATION 72-03-03: cosyvoice-benchmark.md — 120 lines (>= 50) PASS
VALIDATION 72-03-04: indextts2-to-cosyvoice-migration.md — exists PASS
VALIDATION 72-03-05: operator-action handoff documented — voice_clone_reference_wav referenced in this SUMMARY PASS

72-smoke.sh: ALL 11 ASSERTIONS PASSED (DUB-01a/b, DUB-02a/b, DUB-03a/b, DUB-04a, DUB-05a/b, XCUT-02a/b)
```

## Self-Check: PASSED

**Files exist:**
- FOUND: kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md (286 lines)
- FOUND: kais-hermes-skills/VERSION.json (16 lines, valid JSON)
- FOUND: kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md (120 lines)
- FOUND: kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/indextts2-to-cosyvoice-migration.md (74 lines)
- FOUND: .planning/phases/72-dub/72-smoke.sh (124 lines, executable, bash syntax valid)

**Commits exist:**
- FOUND: a626256 (kais-hermes-skills — cosyvoice-deployment.md)
- FOUND: 88249db (kais-hermes-skills — VERSION.json)
- FOUND: 94a9f40 (kais-hermes-skills — cosyvoice-benchmark.md)
- FOUND: df71fde (kais-hermes-skills — indextts2-to-cosyvoice-migration.md)
- FOUND: 3a8949bf0 (hermes-agent — 72-smoke.sh)
