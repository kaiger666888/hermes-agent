# Phase 72: DUB - Research

**Researched:** 2026-07-09
**Domain:** CosyVoice TTS integration + LTX 2.3 native audio division rule + voice clone reference schema
**Confidence:** HIGH for code claims (all verified against live `kais-hermes-skills` HEAD `5772f55` + live Docker containers + live gold-team API); MEDIUM for CosyVoice node recommendation (two competing implementations, divergent from CONTEXT.md); LOW for CosyVoice 2 vs 3 A/B benchmark (operator-action handoff)

## Summary

Phase 72 (DUB) upgrades the kais-movie-pipeline voice layer so that CosyVoice 3.0 (Fun-CosyVoice3-0.5B-2512, already downloaded in the `comfyui-primary` container) becomes the explicit P10 default TTS engine, the schema strictly forbids CosyVoice overlay + LTX 2.3 native dialogue both firing on the same shot (PITFALL D-1 BLOCKER), per-character voice clone reference wavs have a fail-fast schema home, and the operator locks the default variant via a `VERSION.json` field after A/B benchmarking.

The phase is **content-authoring + light-Python heavy** — 4 new refs (cosyvoice-deployment, migration map, benchmark template, workflow JSON), 2 schema additions (PipelineState.tts_engine if we choose state-level, OR shot-list entry-level — this research recommends entry-level), 1 new validator function, 1 P10 phase-module `_TTS_ENGINE_INSTRUCTION` injection (XCUT-02 mirror of FORM-01 pattern), and 1 optional VERSION.json schema. **Zero new Python packages.** All deps already pinned (stdlib) or already Docker-resident (CosyVoice AIIA nodes + Fun-CosyVoice3-0.5B-2512 model).

**Primary recommendation:** Three plans in order — Plan A (Foundation: Shot schema `tts_engine` field + `@dataclass`-level validator + `character_bible.4d_anchor.voice` extension for `voice_clone_reference_wav` + VERSION.json schema + cosyvoice-deployment.md ref + cn-tts-model-matrix.md update); Plan B (`tts_batch.py` + `gold-team-tts-batch.py` extension with `tts_engine` routing + fail-fast on missing wav + `_TTS_ENGINE_INSTRUCTION` injection in p10_voice.py + probe-tts-routing.sh extension + SKILL.md patches); Plan C (A/B benchmark scaffolding + DEPRECATED labeling for IndexTTS2 + smoke tests for division rule + operator-action handoff doc).

**Three critical corrections to CONTEXT.md** (researcher flagging for plan-checker / discuss-phase reconciliation BEFORE planning lands):

1. **ComfyUI node recommendation is wrong.** CONTEXT.md locks `filliptm/ComfyUI_FL-CosyVoice3` and a node name `FLCosyVoice3Instruct2`. Live verification shows: (a) that node is NOT installed in `comfyui-primary` (last GitHub commit ~Jan 2025); (b) the already-installed `ComfyUI_AIIA` package provides `AIIA_CosyVoice_TTS` + `AIIA_CosyVoice_ModelLoader` (same vendor as the existing IndexTTS2 integration); (c) `Fun-CosyVoice3-0.5B-2512` model is ALREADY downloaded at `/root/ComfyUI/models/cosyvoice/`. **Plan A should use the AIIA node (already working) OR explicitly install filliptm and migrate — but the latter is a major scope expansion.** Researcher recommends AIIA.

2. **CosyVoice is NOT new.** The gold-team `tts-tracker` engine already routes `tts_zh` to `CosyVoice-300M` by default (verified via `/api/v1/engines` live call + probe-tts-routing.sh de-phantom note + gold-team-tts-api.md line 124 "for `tts_zh`, this resolved to `CosyVoice-300M` in practice"). SKILL.md:457 says "Use ComfyUI IndexTTS2" but the LIVE default is CosyVoice-300M. DUB-01 should be reframed as "upgrade CosyVoice-300M (gold-team default) to Fun-CosyVoice3-0.5B (SOTA) + document the division rule + add schema enforcement", NOT "replace IndexTTS2".

3. **No Pydantic Shot model exists.** CONTEXT.md's `@model_validator(mode='after')` on Shot assumes Pydantic BaseModel. Verified: `PipelineState` is a stdlib `@dataclass`; **shots are plain dicts** flowing through asset-bus slots (`shot-list`, `script-draft`). The division rule needs a **standalone validator function** (mirroring the existing `validate_form_factor_invariant(state)` pattern at `store.py:111-140`), NOT a Pydantic decorator.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **ComfyUI node:** `filliptm/ComfyUI_FL-CosyVoice3` — **RESEARCH CORRECTION: live container has `ComfyUI_AIIA` CosyVoice nodes instead (already working); filliptm is NOT installed. See Critical Correction #1 above.**
- **Workflow JSON:** new `cosyvoice-comfyui.json` in `audio_pipeline/references/workflows/`
- **Deployment doc:** new `cosyvoice-deployment.md` in `audio_pipeline/references/voicer/`
- **Pre-flight healthcheck gate:** `GET http://localhost:8188/object_info/<cosyvoice_node>` — auto-fallback to IndexTTS2 if missing. NOT hard fail.
- **GPU VRAM budget:** Document CosyVoice 2.0-0.5B (~1.5GB) vs 3.0 (~3GB) requirements
- **Schema-enforced division rule (DUB-02):** `@model_validator(mode='after')` on Shot — **RESEARCH CORRECTION: Shot is a plain dict, not Pydantic. Use `validate_tts_engine_division(shot_list)` function pattern (mirrors `validate_form_factor_invariant` at store.py:111). See Critical Correction #3.**
- **Engine selection rule (declarative):** `tts_engine: Literal["ltx_native", "cosyvoice", "indextts2_fallback"]` on Shot
- **Error behavior:** `ValidationError` equivalent — for plain-dict Shots, use `ValueError` with the CONTEXT.md-specified message format
- **Storage pattern for voice_clone_reference_wav:** `character_bible.json` per-character — **RESEARCH VERIFICATION: schema is `value.characters[].4d_anchor.voice` (currently free-text description); extend with `voice_clone_reference_wav: str | None` sibling field.**
- **Fail-fast on missing + CosyVoice clone mode:** `ValueError("voice_clone_reference_wav missing for character_id=X...")` — no silent fallback
- **Validation helper:** `validate_voice_clone_ref(path)` — 3-10s length, wav format, ≥16kHz sample rate
- **Migration mapping:** IndexTTS2 `voice_preset` (sad/calm/happy/melancholic) → CosyVoice voice profile at `indextts2-to-cosyvoice-migration.md`
- **DUB-04 fallback trigger:** CosyVoice failure OR `/object_info` healthcheck fail → auto-fallback to IndexTTS2 with DEPRECATED warning
- **DEPRECATED labeling:** log + workflow metadata tag + CLI dashboard visibility
- **DUB-05 benchmark:** operator-provided 3-5 reference dialogue lines; recorded as `cosyvoice_default_variant` field in `VERSION.json`
- **XCUT-02 _INSTRUCTION injection:** `_TTS_ENGINE_INSTRUCTION` constant in p10_voice.py

### Claude's Discretion
- Exact wording of CosyVoice workflow JSON node graph
- Exact deployment doc structure
- Which 3-5 reference dialogue lines the operator picks for DUB-05
- GPU VRAM budget numbers (verify against CosyVoice 2.0-0.5B actual usage)
- Test framework for `validate_voice_clone_ref()` (pytest vs standalone script)
- Whether to extend `_eval/` or create `_eval/dub_voice_clone/`

### Deferred Ideas (OUT OF SCOPE)
- DUB-06 real-time TTS streaming during video gen
- DUB-07 CosyVoice 2 instruct2 fine-grained per-line control
- DUB-08 cross-shot voice_identity dimension in continuity_auditor
- Full retirement of IndexTTS2 ComfyUI node (kept DEPRECATED indefinitely)
- Multi-voice SRT dubbing wrapper for CosyVoice (currently one character per invocation)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DUB-01 | CosyVoice 2.0-0.5B as P10 default via ComfyUI | `## Existing ComfyUI CosyVoice State` — AIIA CosyVoice nodes already installed + Fun-CosyVoice3-0.5B-2512 downloaded; `## Workflow JSON Pattern` — `AIIA_CosyVoice_TTS` input schema verified; deployment doc template from `comfyui-indextts2-setup.md` |
| DUB-02 | Schema validator rejects LTX native + CosyVoice overlay on same shot | `## Division Rule Placement` — Shot is plain dict; `validate_tts_engine_division(shot_list)` function pattern; `validate_form_factor_invariant` precedent at store.py:111 |
| DUB-03 | `voice_clone_reference_wav` per character in `character_bible.json` | `## character_bible.json Schema` — envelope-wrapped V3 format; extend `4d_anchor` with sibling field; fail-fast via `validate_voice_clone_ref()` helper |
| DUB-04 | IndexTTS2 DEPRECATED fallback path preserved | `## Fallback Chain Logic` — `tts_engine: "indextts2_fallback"` enum value; auto-fallback on healthcheck fail; DEPRECATED warning metadata |
| DUB-05 | A/B benchmark report + `VERSION.json` default lock | `## VERSION.json Schema` — file does NOT exist (needs creation); `cosyvoice_default_variant` field schema; benchmark report at `audio_pipeline/references/voicer/cosyvoice-benchmark.md` |
| XCUT-02 | `_TTS_ENGINE_INSTRUCTION` constant in p10_voice.py goal f-string | `## p10_voice.py Current State` — module exists; `_FORM_FACTOR_INSTRUCTION` precedent in p09; mirror XCUT-02 test pattern from test_form_factor.py |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Phase 72 operates under the cross-repo topology (planning in `hermes-agent`, code in `kais-hermes-skills`). Load-bearing directives:

- **Skill File Conventions:** `tags` / `related_skills` / `expert_id` / `metrics` frontmatter FROZEN (FOUND-08). Plan B body-edits to `audio_pipeline/SKILL.md` + `kais-movie-pipeline/SKILL.md` MUST NOT mutate frontmatter. `[VERIFIED: live SKILL.md frontmatter]`
- **Deliverable form:** "仅 skill 内容(refs + SKILL.md + eval scripts),不改 Hermes 核心 Python/JS 代码". Plan A's `validate_tts_engine_division()` in `pipeline_state/store.py` is in a skill-bundled plugin, NOT Hermes core. Compliant. `[VERIFIED: plugins/pipeline_state/ is under kais-hermes-skills]`
- **Compatibility:** "不破坏现有 14 专家的 expert_id 与 related_skills 协作图". `audio_pipeline` SKILL.md body edits preserve frontmatter. `[CITED: CLAUDE.md Constraints]`
- **Language:** SKILL.md bilingual (EN YAML + CN prose). New refs follow the same convention. `[CITED: CLAUDE.md]`
- **Ruff PLW1514:** Every `open()` must pass `encoding="utf-8"`. New Python (`validate_voice_clone_ref`, `validate_tts_engine_division`) must comply. `[CITED: CLAUDE.md Code Style]`
- **Cross-repo split:** Code + refs + Python plugins in `kais-hermes-skills`; GSD planning in `hermes-agent/.planning/`. Phase 72 touches NOTHING in hermes-agent except `.planning/`. `[CITED: v9.0+ cross-repo topology]`

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| TTS synthesis (actual audio generation) | Docker container `comfyui-primary` (ComfyUI :8188) | Docker container `kais-gold-team` (:8002 tts-tracker) | Both already host CosyVoice models; pipeline routes via either ComfyUI workflow JSON or gold-team async task API |
| `tts_engine` field storage & validation | Python stdlib dataclass + standalone validator function | `pipeline_state/store.py` (additive helper) | Shot is plain dict; PipelineState already has `validate_form_factor_invariant` precedent |
| Division rule enforcement (DUB-02) | Validator function over `shot-list` slot | p10_voice.py pre-flight check | Plain-dict Shots require function-level validation, not Pydantic decorators |
| `voice_clone_reference_wav` schema | `character-bible` asset-bus slot (p04) | p10 voice reads it via asset_bus_read | Extend `4d_anchor` with sibling field; p04 emits, p10 consumes |
| Operator pre-flight healthcheck | `scripts/probe-tts-routing.sh` | Plan B executor verifies | Bash probe pattern already exists; extend for `AIIA_CosyVoice_TTS` ComfyUI check |
| IndexTTS2 fallback chain | `tts_batch.py` + `gold-team-tts-batch.py` template scripts | p10_voice.py goal f-string guidance | Templates already exist; extend with `tts_engine` switch + auto-fallback wrapper |
| DEPRECATED visibility | Workflow metadata tag + log warning + (optional) CLI dashboard | — | Mirror IMG-05 SLA dashboard pattern; minimum viable = log + metadata |
| `_TTS_ENGINE_INSTRUCTION` propagation | p10_voice.py goal f-string | test_dub.py captured["goal"] assertion | XCUT-02 META-RULE X-2 pattern from Phase 71 FORM |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `dataclasses` | 3.11+ | `PipelineState` (existing); new validators use plain functions, NOT new dataclasses | Already in use (`store.py:35`) `[VERIFIED: store.py:35]` |
| Python stdlib `typing.Literal` | 3.8+ | `tts_engine: Literal["ltx_native", "cosyvoice", "indextts2_fallback"]` type hint on shot dict | Already used in store.py:37 `[VERIFIED: store.py:37]` |
| Python stdlib `json` + `pathlib` | stdlib | `validate_voice_clone_ref()` path + wav header parsing | Already in use across pipeline |
| Python stdlib `wave` | stdlib | Read wav header for sample_rate + duration validation | Zero new dep; stdlib since Python 1.x |
| pytest | (no root pyproject on kais-hermes-skills side) | Unit tests for division rule + voice_clone_ref validation + p10 goal injection | Existing convention (`skills/kais-movie-pipeline/tests/`) `[VERIFIED: tests/ dir]` |
| ffmpeg CLI | already in stack | Probe wav duration (alt to stdlib `wave`) + volumedetect for silent-output check | Already in pipeline; required by gold-team-tts-batch.py `[VERIFIED: gold-team-tts-batch.py:74-86]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `AIIA_CosyVoice_TTS` ComfyUI node | already installed in `comfyui-primary` | ComfyUI workflow JSON TTS generation via CosyVoice 3.0 | DUB-01 default path (recommended over filliptm alternative — see Critical Correction #1) `[VERIFIED: docker exec + object_info API 2026-07-09]` |
| gold-team `tts-tracker` engine | already online (:8002) | Async TTS task API; current de facto default routes to CosyVoice-300M | Alternative to ComfyUI; useful for batch submission + when ComfyUI is contending with LTX-MSR video render `[VERIFIED: /api/v1/engines live call 2026-07-09]` |
| `filliptm/ComfyUI_FL-CosyVoice3` | NOT installed | Alternative ComfyUI node | DO NOT USE in Plan A — adds install scope + last GitHub commit ~Jan 2025; researcher-flagged deviation from CONTEXT.md |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `AIIA_CosyVoice_TTS` (installed) | `filliptm/ComfyUI_FL-CosyVoice3` (CONTEXT.md pick) | AIIA already works + same vendor as IndexTTS2 (consistency); filliptm has `Instruct2` node + multi-speaker Dialog but is NOT installed and adds install risk. Plan A should use AIIA unless operator explicitly mandates filliptm migration. |
| Plain-dict Shot schema | Pydantic BaseModel | Codebase uses plain dict for shots throughout (asset-bus slots). Migrating to Pydantic is out-of-scope for Phase 72. |
| Standalone `validate_tts_engine_division()` function | `@model_validator(mode='after')` (CONTEXT.md) | Pydantic decorator requires Pydantic model; Shot is plain dict. Function pattern matches existing `validate_form_factor_invariant` precedent. |
| stdlib `wave` module for wav validation | `pydub` / `librosa` | Zero new dep; wav header is a fixed 44-byte structure; stdlib is sufficient for sample_rate + duration checks |
| ComfyUI workflow JSON TTS path | gold-team async task API | ComfyUI: synchronous in-pipeline, shares GPU with LTX-MSR (contention risk per PITFALL D-5). gold-team: async + dedicated engine pool but routes to CosyVoice-300M (NOT 3.0). **Recommendation: ComfyUI for v3.0 SOTA, gold-team for batch convenience.** |

**Installation:**
```bash
# Zero new Python packages. Phase 72 installs nothing at the Python layer.
# Docker-side: ComfyUI CosyVoice already installed (AIIA package + Fun-CosyVoice3-0.5B-2512 model).
# To verify (operator sanity check before first run):
docker exec comfyui-primary ls /root/ComfyUI/custom_nodes/ComfyUI_AIIA/aiia_cosyvoice_nodes.py
docker exec comfyui-primary ls /root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512/
curl -s http://127.0.0.1:8188/object_info | python3 -c "import json,sys; d=json.load(sys.stdin); print([k for k in d if 'CosyVoice' in k])"
# Expected output: ['AIIA_CosyVoice_ModelLoader', 'AIIA_CosyVoice_VoiceConversion', 'AIIA_CosyVoice_TTS']
```

**Version verification:** All verified 2026-07-09 via live Docker exec + ComfyUI `/object_info` API + gold-team `/api/v1/engines` API.

## Package Legitimacy Audit

Phase 72 installs **zero external packages** (Python) and **zero new ComfyUI custom nodes** (Docker-side, since AIIA CosyVoice is already installed). The Package Legitimacy Gate is therefore satisfied trivially.

*If Plan A elects to install `filliptm/ComfyUI_FL-CosyVoice3` (NOT recommended):* the planner must add a `checkpoint:human-verify` task before `git clone` inside the container, since the package is community-maintained with last GitHub activity ~Jan 2025. Tag as `[ASSUMED]` pending operator confirmation.

## Architecture Patterns

### System Architecture Diagram

```text
Episode PipelineState (.pipeline-state.json)
    │
    ▼
pipeline.runner ──▶ p10_voice.run()
    │                       │
    │                       ├── Reads shot-list slot (plain list[dict])
    │                       │   └── Each shot dict gains new field: tts_engine (DUB-02)
    │                       │
    │                       ├── Reads character-bible slot (envelope V3)
    │                       │   └── value.characters[].4d_anchor.voice_clone_reference_wav (NEW, DUB-03)
    │                       │
    │                       ├── Pre-flight: validate_tts_engine_division(shot_list)  ← NEW
    │                       │   └── Rejects if any shot has both ltx_native + cosyvoice flags
    │                       │
    │                       ├── Injects _TTS_ENGINE_INSTRUCTION into goal f-string  ← NEW (XCUT-02)
    │                       │
    │                       └── Delegates to audio_pipeline (voicer sub-step)
    │
    ├─▶ TTS routing decision per shot:
    │     ├── tts_engine="ltx_native"     → skip TTS; LTX prompt carries dialogue; LTXVEmptyLatentAudio fills audio latent
    │     ├── tts_engine="cosyvoice"      → submit ComfyUI AIIA_CosyVoice_TTS workflow (DUB-01)
    │     │                                  fail-fast if voice_clone_reference_wav missing (DUB-03)
    │     └── tts_engine="indextts2_fallback" → ComfyUI AIIA_IndexTTS2_TTS (DUB-04, DEPRECATED)
    │
    ├─▶ Healthcheck pre-flight (probe-tts-routing.sh extended)
    │     ├── GET :8188/object_info/AIIA_CosyVoice_TTS  → CosyVoice online?
    │     └── If missing → log warning + auto-fallback to indextts2_fallback
    │
    └─▶ Output written to voice-clips slot (per-shot)
          └── Clip metadata: engine field records actual engine used
                              DEPRECATED flag set when indextts2_fallback fired (DUB-04 visibility)

VERSION.json (NEW, top-level repo file)
    └── cosyvoice_default_variant: "fun_cosyvoice_3.0_0.5B_2512" | "cosyvoice_2.0_0.5B"  ← DUB-05 lock
```

### Recommended Project Structure
```
kais-hermes-skills/
├── VERSION.json                                    # Plan A: NEW (top-level repo file, DUB-05 lock target)
├── plugins/pipeline_state/
│   └── store.py                                    # Plan A: +validate_tts_engine_division() function
├── skills/
│   ├── kais-movie-pipeline/
│   │   ├── SKILL.md                                # Plan B: line 457 IndexTTS2 → CosyVoice primary, IndexTTS2 DEPRECATED fallback
│   │   ├── templates/
│   │   │   ├── tts_batch.py                        # Plan B: extend with tts_engine routing + CosyVoice path
│   │   │   └── gold-team-tts-batch.py              # (existing script in audio_pipeline/scripts/) — Plan B: add --engine flag
│   │   ├── pipeline/phases/
│   │   │   └── p10_voice.py                        # Plan B: +_TTS_ENGINE_INJECTION constant + .task/.constraints injection
│   │   ├── references/
│   │   │   └── comfyui-indextts2-setup.md          # UNCHANGED (DEPRECATED reference; preserved for fallback)
│   │   └── tests/
│   │       └── test_dub.py                         # Plan A/C: NEW (division rule + voice_clone_ref + p10 goal injection)
│   └── movie-experts/audio_pipeline/
│       ├── SKILL.md                                # Plan B: line 78 + 100 TTS matrix refs updated; CosyVoice de-phantom'd as SOTA
│       ├── references/voicer/
│       │   ├── cn-tts-model-matrix.md              # Plan A: extend with CosyVoice 2.0/3.0 row; mark gold-team CosyVoice-300M as current default
│       │   ├── gold-team-tts-api.md                # Plan A: add note that auto route → CosyVoice-300M (already documented line 124)
│       │   ├── cosyvoice-deployment.md             # Plan A: NEW (mirror comfyui-indextts2-setup.md structure)
│       │   ├── cosyvoice-comfyui.json              # Plan A: NEW workflow JSON using AIIA_CosyVoice_TTS
│       │   ├── indextts2-to-cosyvoice-migration.md # Plan A: NEW voice_preset → instruct_text mapping
│       │   └── cosyvoice-benchmark.md              # Plan C: NEW (operator-filled A/B benchmark report template)
│       └── scripts/
│           └── probe-tts-routing.sh                # Plan B: extend with ComfyUI AIIA_CosyVoice_TTS /object_info check
└── (hermes-agent repo: NO CHANGES in Phase 72 — lineage bump is Phase 75)
```

### Pattern 1: Plain-Dict Schema Validation (DUB-02)
**What:** Add `tts_engine` field to Shot dicts + standalone validator function (NOT Pydantic model — codebase uses plain dict for shots).
**When:** Any new per-shot invariant where the codebase lacks a Pydantic Shot model.
**Example:**
```python
# Source: derived from existing validate_form_factor_invariant pattern at store.py:111-140
# Plan A adds this function to plugins/pipeline_state/store.py (or a new validators.py module):

TTS_ENGINE_VALUES = frozenset({"ltx_native", "cosyvoice", "indextts2_fallback"})

def validate_tts_engine_division(shot_list: list[dict]) -> None:
    """Reject shots that enable BOTH ltx_native_dialogue AND cosyvoice_overlay.

    Per PITFALL D-1 (BLOCKER): if both fire for the same shot, the result is
    doubled audio / phase cancellation / lip-sync mismatch. This validator
    enforces the DUB-02 division rule at pre-flight time (called from p10_voice.run()
    before any TTS submission).

    Raises:
        ValueError: if any shot has conflicting flags.
    """
    for shot in shot_list:
        sid = shot.get("shot_id", "<unknown>")
        tts_engine = shot.get("tts_engine", "cosyvoice")  # default per CONTEXT.md
        ltx_native_dialogue = shot.get("ltx_native_dialogue", False)
        cosyvoice_overlay = shot.get("cosyvoice_overlay", False)

        if tts_engine not in TTS_ENGINE_VALUES:
            raise ValueError(
                f"Shot {sid}: tts_engine must be one of {sorted(TTS_ENGINE_VALUES)}, "
                f"got {tts_engine!r} (DUB-02 strict enum — no fuzzy matching)."
            )

        if ltx_native_dialogue and cosyvoice_overlay:
            raise ValueError(
                f"Shot {sid}: cannot enable both ltx_native_dialogue AND "
                f"cosyvoice_overlay (DUB-02 / PITFALL D-1 — doubled audio / "
                f"phase cancellation / lip-sync mismatch)."
            )

        # Consistency: if ltx_native_dialogue=True, tts_engine MUST be "ltx_native"
        if ltx_native_dialogue and tts_engine != "ltx_native":
            raise ValueError(
                f"Shot {sid}: ltx_native_dialogue=True but tts_engine={tts_engine!r}; "
                f"must be 'ltx_native' (DUB-02 consistency check)."
            )
```

### Pattern 2: Voice Clone Reference Wav Fail-Fast (DUB-03)
**What:** Extend `character_bible.json` schema with `voice_clone_reference_wav` field; validate path + wav format before TTS submission.
**When:** Any TTS path that uses CosyVoice clone mode (requires reference audio).
**Example:**
```python
# Source: stdlib wave module; mirrors gold-team-tts-batch.py volumedetect pattern
# Plan A adds this helper:

import wave
import contextlib
from pathlib import Path

def validate_voice_clone_ref(path: str | Path) -> tuple[float, int]:
    """Validate a voice_clone_reference_wav file meets DUB-03 requirements.

    Returns:
        (duration_sec, sample_rate_hz) tuple on success.

    Raises:
        FileNotFoundError: path does not exist.
        ValueError: format not wav, duration outside 3-10s, or sample_rate < 16kHz.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"voice_clone_reference_wav missing for path={path}. "
            f"Operator action: provide 3-10s clean sample. See DUB phase operator-action checklist."
        )
    if p.suffix.lower() != ".wav":
        raise ValueError(f"voice_clone_reference_wav must be .wav format, got {p.suffix}")

    with contextlib.closing(wave.open(str(p), "rb")) as wf:
        n_frames = wf.getnframes()
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()

    duration = n_frames / sample_rate if sample_rate else 0.0
    if not (3.0 <= duration <= 10.0):
        raise ValueError(
            f"voice_clone_reference_wav duration must be 3-10s, got {duration:.2f}s"
        )
    if sample_rate < 16000:
        raise ValueError(
            f"voice_clone_reference_wav sample_rate must be >= 16kHz, got {sample_rate}Hz"
        )
    if n_channels != 1:
        # Mono preferred; stereo acceptable but warn
        pass  # Soft warn — CosyVoice accepts stereo but mono is canonical
    return duration, sample_rate
```

### Pattern 3: XCUT-02 `_TTS_ENGINE_INSTRUCTION` Injection
**What:** Define module constant in p10_voice.py + inject via `.task(steps=[...])` AND `.constraints([...])`; assert via goal-content test.
**When:** Any MUST added to SKILL.md that subagents must act on (META-RULE X-2).
**Example:**
```python
# Source: mirror of _FORM_FACTOR_INJECTION pattern from Phase 71 (p09_shot_breakdown.py)
# Plan B adds to p10_voice.py near the top (after INPUT_SLOTS / OUTPUT_SLOTS):

_TTS_ENGINE_INSTRUCTION = (
    "TTS ENGINE ROUTING (mandatory — MUST propagate tts_engine selection from each Shot): "
    "For each shot, read shot.tts_engine. "
    "If 'ltx_native': skip TTS generation (LTX prompt carries dialogue via LTXVEmptyLatentAudio). "
    "If 'cosyvoice': submit ComfyUI AIIA_CosyVoice_TTS workflow with reference_audio from "
    "character_bible.4d_anchor.voice_clone_reference_wav; FAIL FAST if reference missing. "
    "If 'indextts2_fallback': submit ComfyUI AIIA_IndexTTS2_TTS workflow + log DEPRECATED warning. "
    "Per DUB-02 / PITFALL D-1: NEVER allow both ltx_native dialogue AND cosyvoice overlay on the same shot."
)

# Then in run(), extend the GoalBuilder.task() block:
.task(steps=[
    "Load expert via skill_view(name='audio_pipeline')",
    "Generate TTS voice clips for narration + dialogue per shot",
    "Match voice durations to shot-list durations from p09",
    f"{_TTS_ENGINE_INSTRUCTION}",   # NEW Plan B XCUT-02
    # ... existing steps ...
])

# And extend .constraints():
.constraints([
    "MUST match shot durations from p09 shot_list",
    "MUST use script-draft text from p03 (no ad-libbing)",
    "MUST propagate tts_engine selection per shot (ltx_native / cosyvoice / indextts2_fallback)",  # NEW
    # ... existing constraints ...
])
```

### Pattern 4: VERSION.json Default Lock (DUB-05)
**What:** New top-level `VERSION.json` records benchmark-locked default variant.
**When:** DUB-05 close-out after operator A/B review.
**Example:**
```json
{
  "schema_version": "1.0",
  "pipeline_version": "v14.0",
  "tts": {
    "cosyvoice_default_variant": "fun_cosyvoice_3.0_0.5B_2512",
    "lock_date": "2026-07-XX",
    "lock_rationale": "Operator A/B benchmark on 5 reference lines. See audio_pipeline/references/voicer/cosyvoice-benchmark.md.",
    "alternative_tested": "cosyvoice_2.0_0.5B",
    "benchmark_report_path": "skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md"
  }
}
```

### Anti-Patterns to Avoid
- **Installing `filliptm/ComfyUI_FL-CosyVoice3` when AIIA is already working:** adds install scope + risk; researcher-flagged deviation from CONTEXT.md. Use AIIA unless operator mandates filliptm. `[VERIFIED: AIIA nodes registered in live /object_info API]`
- **Pydantic `@model_validator` on Shot:** Shot is plain dict in the codebase. Use standalone validator function. `[VERIFIED: shot-list schema in p09_shot_breakdown.py:381 — plain dict]`
- **Silent fallback to generic voice on missing `voice_clone_reference_wav`:** defeats cloning purpose. Must fail-fast per CONTEXT.md D-02 mitigation #2. `[CITED: PITFALLS.md D-2]`
- **Demoting gold-team CosyVoice-300M as "phantom":** it's the de facto zh engine per probe-tts-routing.sh de-phantom note. The phantom was the v1 SKILL.md CosyVoice-300M reference in `audio_pipeline` — gold-team CosyVoice-300M is REAL and OPERATIONAL. `[VERIFIED: probe-tts-routing.sh lines 5-7; gold-team-tts-api.md line 124]`
- **Assuming `voice_clone_reference_wav` goes in PipelineState:** it's per-character, not per-episode. Belongs in `character-bible` slot (p04 asset). `[VERIFIED: asset-bus-schema.md character-bible entry]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTS synthesis | Custom TTS inference code | ComfyUI `AIIA_CosyVoice_TTS` node OR gold-team `/api/v1/tasks` | Both already deployed; ComfyUI has GPU sharing with LTX-MSR; gold-team has async batch queue |
| Wav header parsing | Byte-level struct.unpack | stdlib `wave` module | Fixed 44-byte RIFF header is well-tested in stdlib; no need for pydub/librosa |
| Wav duration probe | Custom frame counting | stdlib `wave` + `contextlib.closing` OR ffmpeg `ffprobe` | Both already in stack; ffmpeg pattern already used in `gold-team-tts-batch.py:67-71` |
| Silent-output detection | Custom RMS calculation | ffmpeg `volumedetect` filter | Already implemented in `gold-team-tts-batch.py:74-86`; mean_volume < -60 dB = silent |
| ComfyUI workflow submission | Custom HTTP client | `requests.post(f"{COMFY_URL}/prompt", json={"prompt": wf})` | Existing pattern in `comfyui-indextts2-setup.md:333-356` Non-blocking Batch Submission |
| Voice cloning reference audio | Audio fingerprinting / speaker embedding | CosyVoice zero-shot clone (built into the node) | AIIA_CosyVoice_TTS accepts `reference_audio` input natively; 3-30s sample per node README |

**Key insight:** Phase 72 is mostly content authoring (4 new refs + 2 SKILL.md patches) + 2 small Python helpers (validator functions). The "integration" with CosyVoice is largely already done — the AIIA node is installed, the Fun-CosyVoice3 model is downloaded, the gold-team engine routes to CosyVoice by default. The work is **making the existing CosyVoice capability explicit, schema-enforced, and benchmark-locked**, not building new TTS plumbing.

## Runtime State Inventory

> Phase 72 adds schema fields + validator functions. Not a rename/refactor phase, but touches persistent state (character-bible.json, PipelineState, episode shot-lists).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data — episode `.pipeline-assets/character-bible.json` | Existing episodes (formc-test-01, ep-chameleon-comedy, ep-chameleon-rage) have `4d_anchor.voice` as free-text description; NO `voice_clone_reference_wav` field | None — `voice_clone_reference_wav` is additive with `None` default. Old character-bibles load cleanly; CosyVoice clone mode fails-fast (DUB-03 operator-action handoff) until operator sources wavs. `[VERIFIED: formc-test-01/.pipeline-assets/character-bible.json envelope V3 format]` |
| Stored data — `.pipeline-state.json` | Existing episode state files do NOT have a top-level `tts_engine` field | None — `tts_engine` is per-SHOT (inside `shot-list` slot), NOT per-episode on PipelineState. No PipelineState schema change needed. Old episodes load cleanly. |
| Stored data — shot-list slot | Existing shot-lists have NO `tts_engine` field per shot | Migration: when p10_voice encounters a shot missing `tts_engine`, default to `"cosyvoice"` per CONTEXT.md. No migration script needed — read-time default. |
| Live service config — ComfyUI :8188 | `AIIA_CosyVoice_TTS` node already registered; `Fun-CosyVoice3-0.5B-2512` model already downloaded at `/root/ComfyUI/models/cosyvoice/` | None — already operational. Plan A deployment doc records the install procedure for reproducibility. `[VERIFIED: docker exec + /object_info API 2026-07-09]` |
| Live service config — gold-team :8002 | `tts-tracker` engine online; supports `tts_zh` task type; models include CosyVoice-300M, GPT-SoVITS, Chatterbox-Turbo | None — gold-team already routes `tts_zh` → CosyVoice-300M by default. `[VERIFIED: /api/v1/engines live call 2026-07-09]` |
| OS-registered state | None — Phase 72 registers no OS-level services, cron jobs, or systemd units | None |
| Secrets/env vars | None — no env var changes; ComfyUI :8188 and gold-team :8002 URLs already documented in existing refs | None |
| Build artifacts | None — Phase 72 adds no compiled artifacts | None |

**Nothing found that blocks execution.** All migrations are forward-compatible by construction (additive fields with defaults).

## Common Pitfalls

### Pitfall 1: CONTEXT.md ComfyUI node mismatch (RESEARCH CORRECTION)
**What goes wrong:** CONTEXT.md locks `filliptm/ComfyUI_FL-CosyVoice3` + node `FLCosyVoice3Instruct2`. Live container has `ComfyUI_AIIA` package with `AIIA_CosyVoice_TTS` / `AIIA_CosyVoice_ModelLoader` instead. The `filliptm` node is NOT installed (last GitHub activity ~Jan 2025).
**Why it happens:** CONTEXT.md was authored from STACK.md research which surveyed ComfyUI nodes theoretically; researcher did not verify against live container state.
**How to avoid:** Plan A uses the already-installed AIIA nodes. If operator explicitly mandates `filliptm` migration, that becomes a separate scope-expansion task (install + test + document divergent node API). Researcher recommends AIIA path.
**Warning signs:** Plan executor runs `docker exec comfyui-primary ls /root/ComfyUI/custom_nodes/ | grep cosy` and finds `ComfyUI_AIIA/aiia_cosyvoice_nodes.py` but NOT `ComfyUI_FL-CosyVoice3/`.

### Pitfall 2: CosyVoice "new default" framing is partly wrong
**What goes wrong:** CONTEXT.md / REQUIREMENTS.md frame DUB-01 as "CosyVoice replacing IndexTTS2 as default". Live verification shows gold-team `tts-tracker` already routes `tts_zh` → `CosyVoice-300M` by default (de facto). SKILL.md:457 says IndexTTS2 but operators have been using CosyVoice-300M via gold-team for weeks.
**Why it happens:** Pipeline docs (SKILL.md:457) lagged behind the gold-team deployment.
**How to avoid:** Reframe DUB-01 as "upgrade CosyVoice-300M (current gold-team default) → Fun-CosyVoice3-0.5B (SOTA via ComfyUI AIIA node) + document the existing CosyVoice path explicitly + add schema enforcement". The work is documentation + schema hardening, NOT new integration.
**Warning signs:** Plan B executor edits SKILL.md:457 and finds existing text already references CosyVoice in surrounding sections (gold-team-tts-api.md mentions CosyVoice-300M as auto-route).

### Pitfall 3: LTX native audio detection requires new explicit field
**What goes wrong:** DUB-02 division rule needs to know whether a shot has LTX native dialogue enabled. Verified: NO `lip_sync_required` or `has_dialogue` or `ltx_native_dialogue` field exists in the current Shot schema. LTX native audio is implicit — dialogue text in `ltx_prompt` gets synthesized via `LTXVEmptyLatentAudio` node.
**Why it happens:** LTX native audio was an emergent property of prompt content, not a declared flag.
**How to avoid:** Plan A adds `ltx_native_dialogue: bool = False` AND `tts_engine: Literal[...]` as NEW explicit Shot fields. The cinematographer (p09) or operator declares intent; p10 enforces the division rule.
**Warning signs:** Plan executor tries to infer "LTX native" from `ltx_prompt` text content — unreliable. Explicit declaration is the correct path.

### Pitfall 4: `@model_validator` assumes Pydantic Shot model that doesn't exist
**What goes wrong:** CONTEXT.md specifies `@model_validator(mode='after')` on Shot. Shot is a plain dict, not a Pydantic BaseModel. PipelineState is a stdlib `@dataclass` (also not Pydantic).
**Why it happens:** CONTEXT.md author assumed Pydantic stack from Hermes core, but kais-movie-pipeline uses stdlib only.
**How to avoid:** Use standalone `validate_tts_engine_division(shot_list: list[dict])` function, mirroring `validate_form_factor_invariant(state: PipelineState)` at store.py:111-140. Called from p10_voice.run() pre-flight.

### Pitfall 5: CosyVoice + LTX-MSR concurrent GPU contention (PITFALL D-5)
**What goes wrong:** P10 (TTS) and P11 (video render) both submit to ComfyUI :8188. CosyVoice ~3GB VRAM + LTX-MSR ~23GB VRAM on RTX 3090 (24GB) = OOM crash.
**How to avoid:** Document hard rule: P10 and P11 MUST NOT run concurrently on same ComfyUI instance. Use gold-team async API as alternative when LTX-MSR is active (different engine pool, dedicated 8GB VRAM). `[CITED: PITFALLS.md D-5]`

### Pitfall 6: gold-team CosyVoice-300M trailing-punctuation silent output bug
**What goes wrong:** CosyVoice-300M occasionally returns ~0.04-0.08s silent WAV for text ending in `。！？.!?` or containing mid-text `……`. Task still reports `status: completed`.
**How to avoid:** Already mitigated in `gold-team-tts-batch.py:144-167` (silent-output detection + auto-retry with punctuation stripped). Plan A's deployment doc must document this known issue + point to the existing mitigation.

## Code Examples

### character_bible.json extension (DUB-03)

```json
// Source: derived from live formc-test-01/.pipeline-assets/character-bible.json (envelope V3 format)
// Plan A extends the 4d_anchor with a sibling voice_clone_reference_wav field:

{
  "value": {
    "characters": [
      {
        "name": "_sharer",
        "role": "protagonist",
        "archetype": "catalyst",
        "age_range": "young_adult",
        "4d_anchor": {
          "identity": "...",
          "arc": "...",
          "voice": "疲惫无奈的低声线，苦笑多，台词多为自嘲和对镜头的旁白。",
          "visual": "...",
          "voice_clone_reference_wav": "assets/voice_refs/sharer.wav"   // NEW v14.0 (DUB-03)
        },
        "style_prefix": "..."
      }
    ]
  },
  "derived_from": "p04_character_design",
  "content_hash": "...",
  "schema_version": "1.1"  // bump from 1.0 to 1.1 for DUB-03 additive field
}
```

### AIIA_CosyVoice_TTS ComfyUI Workflow JSON (DUB-01)

```json
// Source: derived from live AIIA_CosyVoice_TTS INPUT_TYPES (verified via /object_info 2026-07-09)
// Plan A new file: skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-comfyui.json

{
  "1": {
    "class_type": "AIIA_CosyVoice_ModelLoader",
    "inputs": {
      "model_dir": "/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512",
      "use_fp16": true,
      "use_rl_model": false
    }
  },
  "2": {
    "class_type": "AIIA_CosyVoice_TTS",
    "inputs": {
      "model": ["1", 0],
      "tts_text": "你的中文对白文本",
      "instruct_text": "语速自然，情感饱满，温柔的旁白质感。",
      "base_gender": "Female",
      "dialect": "None (Auto)",
      "emotion": "None (Neutral)",
      "speed": 1.0,
      "seed": 42,
      "reference_audio": ["3", 0]
    }
  },
  "3": {
    "class_type": "LoadAudio",
    "inputs": {
      "audio": "voice_refs/sharer.wav"
    }
  },
  "4": {
    "class_type": "PreviewAudio",
    "inputs": {
      "audio": ["2", 0]
    }
  }
}
```

### p10_voice.py pre-flight check (Plan B)

```python
# Source: derived from existing p10_voice.py lines 77-92 (inputs gathering)
# Plan B adds after line 80 (script_draft read):

# Pre-flight DUB-02 division rule validation (Plan A function, Plan B wire-up)
from plugins.pipeline_state.store import validate_tts_engine_division
try:
    validate_tts_engine_division(shot_list)
except ValueError as exc:
    # Re-raise with phase context; p10 refuses to run if division rule violated
    raise ValueError(f"p10_voice pre-flight failed: {exc}") from exc

# Pre-flight DUB-03 voice_clone_reference_wav validation (only for cosyvoice shots)
from pathlib import Path
from .dub_validators import validate_voice_clone_ref  # Plan A new module
character_bible = asset_bus_read("character-bible") or {}
chars_by_name = {
    c.get("name"): c
    for c in (character_bible.get("value", character_bible).get("characters", []))
}
for shot in shot_list:
    if shot.get("tts_engine") == "cosyvoice":
        char_name = shot.get("speaker") or shot.get("character")
        char = chars_by_name.get(char_name, {})
        wav_path = char.get("4d_anchor", {}).get("voice_clone_reference_wav")
        if not wav_path:
            raise ValueError(
                f"voice_clone_reference_wav missing for character_id={char_name} "
                f"(shot {shot.get('shot_id')}). Operator action: provide 3-10s "
                f"clean sample at assets/voice_refs/{char_name}.wav. "
                f"See DUB phase operator-action checklist."
            )
        validate_voice_clone_ref(wav_path)  # raises on invalid format / duration / sample_rate
```

### Probe-tts-routing.sh extension (Plan B)

```bash
# Source: existing skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh
# Plan B adds a new ComfyUI CosyVoice healthcheck block:

# === ComfyUI CosyVoice node healthcheck (DUB-01 / DUB-04 fallback gate) ===
COMFY_URL="http://127.0.0.1:8188"
COSY_NODES=$(curl -s -m 5 "$COMFY_URL/object_info" 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    cosy = [k for k in d.keys() if 'CosyVoice' in k]
    print(','.join(cosy) if cosy else 'NONE')
except Exception:
    print('ERROR')
")

if [[ "$COSY_NODES" == "NONE" || "$COSY_NODES" == "ERROR" ]]; then
    echo "WARN: ComfyUI CosyVoice node NOT available ($COSY_NODES). Auto-fallback to indextts2_fallback (DEPRECATED)."
    # Per DUB-04: auto-fallback, NOT hard fail
    TTS_ENGINE_DEFAULT="indextts2_fallback"
else
    echo "OK: ComfyUI CosyVoice nodes available: $COSY_NODES"
    TTS_ENGINE_DEFAULT="cosyvoice"
fi
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SKILL.md:457 "Use ComfyUI IndexTTS2" | gold-team `tts-tracker` engine auto-routes `tts_zh` → CosyVoice-300M | ~2026-07-04 | Docs lagged deployment; DUB-01 makes the CosyVoice default explicit + upgrades to v3.0 SOTA `[VERIFIED: gold-team-tts-api.md:124]` |
| `audio_pipeline/SKILL.md` "CosyVoice-300M is phantom" | CosyVoice de-phantom'd: CosyVoice-300M operational in gold-team; Fun-CosyVoice3-0.5B-2512 in ComfyUI | 2026-07-06 per probe-tts-routing.sh comment | Plan A must update cn-tts-model-matrix.md to reflect reality `[VERIFIED: probe-tts-routing.sh:5-7]` |
| Shot schema had no `tts_engine` field | Plan A adds `tts_engine: Literal[...]` + `ltx_native_dialogue: bool` per shot | v14.0 Phase 72 | Old shot-lists default to `"cosyvoice"` + `ltx_native_dialogue=False` at read time |
| `character_bible.4d_anchor.voice` was free-text only | Plan A adds `voice_clone_reference_wav` sibling field | v14.0 Phase 72 | Old character-bibles load cleanly (field defaults to None) |
| No VERSION.json existed | Plan A creates VERSION.json with `cosyvoice_default_variant` lock | v14.0 Phase 72 | DUB-05 benchmark gate has a home |

**Deprecated/outdated:**
- SKILL.md:457 IndexTTS2-as-default: still works but flagged DEPRECATED in Plan B; CosyVoice primary
- `filliptm/ComfyUI_FL-CosyVoice3` (CONTEXT.md pick): NOT installed; researcher recommends AIIA instead

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | AIIA CosyVoice node is sufficient for DUB-01 (operator does not mandate filliptm migration) | Standard Stack, Code Examples | If operator mandates filliptm, Plan A scope expands significantly (install + new workflow JSON + document divergent node API). Researcher recommends confirming with operator before Plan A execution. |
| A2 | `tts_engine` field is per-shot (inside shot-list), NOT per-episode on PipelineState | Architecture Patterns | If wrong (should be episode-level), the division rule validator location changes but the function logic is identical. Plan A can adapt. |
| A3 | VERSION.json should be top-level in kais-hermes-skills repo | Pattern 4 | If there's a conventional location elsewhere (e.g., skills/kais-movie-pipeline/VERSION.json), plan adjusts. Researcher found no existing VERSION.json. |
| A4 | gold-team CosyVoice-300M is "good enough" as fallback when ComfyUI is contending with LTX-MSR | Common Pitfalls 5 | If gold-team CosyVoice-300M quality is unacceptable, operator must serialize P10/P11 or accept IndexTTS2 as fallback. Deferred to DUB-05 benchmark data. |
| A5 | AIIA_CosyVoice_TTS supports zero-shot voice cloning via `reference_audio` input | Code Examples | Verified from live INPUT_TYPES: `"reference_audio": ("AUDIO",)` in optional inputs. HIGH confidence. |
| A6 | `Fun-CosyVoice3-0.5B-2512` is the correct model for CosyVoice 3.0 (December 2025 release) | Standard Stack | Verified from `/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512/` directory + cosyvoice3.yaml present. HIGH confidence. |
| A7 | `validate_voice_clone_ref()` belongs in a new `dub_validators.py` module (not store.py) | Code Examples | If store.py is the conventional home for validators, plan adjusts. Researcher recommends separate module to keep store.py focused on state I/O. |

## Open Questions (RESOLVED)

All 4 open questions below are **RESOLVED** in `72-CONTEXT.md <decisions>` (RESEARCH-corrected). Markers below formalize the resolution for Dimension 11 compliance.

1. **Should Plan A use AIIA nodes (already installed) or install filliptm (CONTEXT.md pick)?**
   - What we know: AIIA is working + same vendor as IndexTTS2; filliptm is NOT installed + last GitHub commit ~Jan 2025.
   - What's unclear: whether operator has explicit preference for filliptm's `Instruct2` / multi-speaker `Dialog` nodes.
   - Recommendation: **Use AIIA** (default). Flag as deviation from CONTEXT.md for plan-checker / discuss-phase reconciliation. If operator mandates filliptm, escalate as scope-expansion.
   - **RESOLVED: Use AIIA** per CONTEXT.md decision "ComfyUI node: AIIA_CosyVoice_TTS + AIIA_CosyVoice_ModelLoader (CORRECTED from original filliptm/ComfyUI_FL-CosyVoice3 per RESEARCH live verification)".

2. **Should `tts_engine` field live on Shot dict or on PipelineState?**
   - What we know: CONTEXT.md implies per-shot ("for the same shot"). PipelineState is episode-level.
   - Recommendation: per-Shot (inside `shot-list` slot). Confirmed by division rule semantics (DUB-02 is per-shot).
   - **RESOLVED: Per-Shot fields** per CONTEXT.md decision "Shot dict gets 2 new fields (NOT PipelineState): tts_engine + ltx_native_dialogue — both via .get(key, default) for backward compat".

3. **Should VERSION.json be top-level or skills-scoped?**
   - What we know: No existing VERSION.json anywhere in repo.
   - Recommendation: top-level `kais-hermes-skills/VERSION.json` (matches conventional placement for project meta).
   - **RESOLVED: Top-level `kais-hermes-skills/VERSION.json`** per CONTEXT.md decision "VERSION.json is NEW at top-level kais-hermes-skills/VERSION.json — no existing VERSION.json".

4. **Is gold-team CosyVoice-300M an acceptable fallback for ComfyUI when GPU contention?**
   - What we know: CosyVoice-300M is the auto-route for `tts_zh`. Quality difference vs Fun-CosyVoice3-0.5B is documented in STACK.md (test-zh SS 1.7% vs 1.21%).
   - Recommendation: Yes for draft/placeholder; No for production final voice. Documented in Plan A deployment doc + DUB-05 benchmark report.
   - **RESOLVED: Yes for fallback** per CONTEXT.md decision "gold-team CosyVoice-300M (already operational at :8002) — Phase 72 PROMOTES existing path to P10 default + adds ComfyUI AIIA path as alternative; NOT a greenfield integration".

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | validator functions, stdlib `wave` | ✓ | 3.13 | — |
| pytest | Plan A unit tests | ✓ | via hermes-agent venv | standalone script |
| ffmpeg CLI | silent-output detection + duration probe | ✓ | in Docker stack | — |
| ComfyUI :8188 | AIIA_CosyVoice_TTS workflow (DUB-01 primary path) | ✓ | running container `comfyui-primary` | gold-team :8002 async API (CosyVoice-300M) |
| gold-team :8002 | Async TTS batch API (DUB-01 alt path + DUB-04 fallback pool) | ✓ | running container `kais-gold-team` | — |
| Docker container `comfyui-primary` | CosyVoice model + node host | ✓ | verified 2026-07-09 | — |
| `AIIA_CosyVoice_TTS` node | ComfyUI workflow JSON TTS | ✓ | installed in `ComfyUI_AIIA` package | `filliptm/ComfyUI_FL-CosyVoice3` (NOT installed; scope expansion) |
| `Fun-CosyVoice3-0.5B-2512` model | CosyVoice 3.0 SOTA | ✓ | `/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512/` | CosyVoice-300M (gold-team default; lower quality) |
| `AIIA_IndexTTS2_TTS` node | DUB-04 DEPRECATED fallback | ✓ | installed in `ComfyUI_AIIA` package | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None — all required deps available and verified live.

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json`. This section is REQUIRED.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (stdlib; no separate pyproject on kais-hermes-skills side) |
| Config file | `skills/kais-movie-pipeline/tests/conftest.py` (shared fixtures: `mock_delegate_factory`, `tmp_asset_bus`, `tmp_state_store`, `fake_registry`, `make_fake_phase`) |
| Quick run command | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/test_dub.py -x` |
| Full suite command | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/ -x` |

`[VERIFIED: conftest.py exists with documented fixtures; test_p09_unit.py demonstrates delegate_task injection + captured["goal"] assertion pattern]`

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DUB-01 | ComfyUI CosyVoice node present (AIIA or filliptm) | smoke | `curl -s http://127.0.0.1:8188/object_info \| python3 -c "import json,sys; d=json.load(sys.stdin); assert any('CosyVoice' in k for k in d)"` | ❌ Wave 0 (bash one-liner) |
| DUB-01 | cosyvoice-comfyui.json workflow exists | smoke | `test -f skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-comfyui.json` | ❌ Wave 0 |
| DUB-01 | cosyvoice-deployment.md exists with ≥5 sections | smoke | `grep -c "^## " skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md` returns ≥ 5 | ❌ Wave 0 |
| DUB-02 | Division rule rejects both-on shot | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_division_rejects_both_on -x` | ❌ Wave 0 |
| DUB-02 | Division rule allows ltx_native only | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_division_allows_ltx_native_only -x` | ❌ Wave 0 |
| DUB-02 | Division rule allows cosyvoice only | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_division_allows_cosyvoice_only -x` | ❌ Wave 0 |
| DUB-02 | Division rule allows both-off (silence/SFX) | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_division_allows_both_off -x` | ❌ Wave 0 |
| DUB-02 | Division rule enforces tts_engine literal enum | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_division_rejects_invalid_tts_engine -x` | ❌ Wave 0 |
| DUB-03 | validate_voice_clone_ref accepts valid 5s wav | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_voice_clone_ref_accepts_valid -x` | ❌ Wave 0 |
| DUB-03 | validate_voice_clone_ref rejects missing file | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_voice_clone_ref_rejects_missing -x` | ❌ Wave 0 |
| DUB-03 | validate_voice_clone_ref rejects <3s wav | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_voice_clone_ref_rejects_short -x` | ❌ Wave 0 |
| DUB-03 | validate_voice_clone_ref rejects <16kHz | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_voice_clone_ref_rejects_low_sr -x` | ❌ Wave 0 |
| DUB-04 | DEPRECATED warning logged on fallback trigger | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_indextts2_fallback_logs_deprecated -x` | ❌ Wave 0 |
| DUB-05 | VERSION.json exists with cosyvoice_default_variant field | smoke | `python -c "import json; d=json.load(open('VERSION.json')); assert 'cosyvoice_default_variant' in d.get('tts', {})"` | ❌ Wave 0 |
| DUB-05 | cosyvoice-benchmark.md exists | smoke | `test -f skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md` | ❌ Wave 0 (template; operator fills) |
| XCUT-02 | `_TTS_ENGINE_INSTRUCTION` injected into p10 goal | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py::test_p10_goal_includes_tts_engine_instruction -x` | ❌ Wave 0 |
| Cross | cn-tts-model-matrix.md updated with CosyVoice 2.0/3.0 row | smoke | `grep -c "Fun-CosyVoice3" skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` returns ≥ 1 | ❌ Wave 0 |
| Cross | SKILL.md:457 IndexTTS2 demoted to DEPRECATED fallback | smoke | `grep -A2 "IndexTTS2" skills/kais-movie-pipeline/SKILL.md \| grep -ci "deprecated\|fallback"` returns ≥ 1 | ❌ Wave 0 |

### Sampling Rate (Nyquist Dimension 8 — Sample-Rate Analysis)

Phase 72 has two distinct signal classes requiring different sampling rates:

**Signal Class 1: Python behavior** (division rule, voice_clone_ref validation, goal injection)
- **Frequency characteristics:** Changes per-task-commit; deterministic; runs in <2s
- **Required sample rate:** Per-task-commit (Nyquist = 2× fastest expected change)
- **Sampler:** pytest unit tests (`test_dub.py::test_*`)
- **Sample size:** ~12 unit tests, <2s total runtime
- **Rationale:** Division rule + wav validation are pure functions; once written they rarely change but MUST be correct on every commit. Per-task sampling catches regressions immediately.

**Signal Class 2: Markdown content presence** (refs created, SKILL.md patches, matrix updated)
- **Frequency characteristics:** Changes per-wave-merge (refs are authored in batches); text content
- **Required sample rate:** Per-wave-merge (lower frequency OK; markdown doesn't have intermediate states)
- **Sampler:** bash grep smoke checks (`grep -c "Fun-CosyVoice3"`, `test -f cosyvoice-deployment.md`)
- **Sample size:** ~6 grep assertions
- **Rationale:** Markdown presence is binary (exists / doesn't); sampling per-commit aliases because no intermediate states exist.

**Signal Class 3: Live integration** (ComfyUI node presence, gold-team engine health)
- **Frequency characteristics:** Changes on Docker restart or container rebuild; rare
- **Required sample rate:** Per-phase-gate (before `/gsd:verify-work`)
- **Sampler:** smoke script with live curl probes
- **Rationale:** Docker state is environmental, not code; sampling per-task is wasteful.

**Anti-aliasing guard:** If only Signal Class 1 (pytest) is sampled, markdown drift goes undetected (FORM-02-style failure). If only Signal Class 2 (grep) is sampled, Python regressions slip through. BOTH rates are mandatory.

- **Per task commit:** `python -m pytest skills/kais-movie-pipeline/tests/test_dub.py -x` (Signal Class 1)
- **Per wave merge:** Full pipeline test suite + grep smoke checks (Signal Classes 1 + 2)
- **Phase gate (before `/gsd:verify-work`):** Full suite green + all grep smoke + live Docker integration probes (Signal Classes 1 + 2 + 3)

### Wave 0 Gaps

- [ ] `skills/kais-movie-pipeline/tests/test_dub.py` — NEW file covering DUB-02 division rule (5 tests) + DUB-03 voice_clone_ref validation (4 tests) + XCUT-02 p10 goal injection (1 test) + DUB-04 DEPRECATED fallback logging (1 test). ~11 tests.
- [ ] `skills/kais-movie-pipeline/tests/conftest.py` extension — add `tmp_wav_file` fixture for voice_clone_ref tests (generate a valid 5s 16kHz mono wav via stdlib `wave` + numpy-free sine wave, OR use ffmpeg `f lavfi -i sine=...`)
- [ ] No framework install needed — pytest already available via hermes-agent venv

*(If no other gaps: existing `conftest.py` fixtures cover PipelineState round-trip testing via `tmp_state_store` — reuse it.)*

## Security Domain

> Phase 72 has no authentication, session, or untrusted-network surface. `voice_clone_reference_wav` is operator-sourced; the system validates format/duration/sample_rate but does NOT verify ownership (per CLAUDE.md Constraints: "operator must provide owned reference audio").

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no auth |
| V3 Session Management | no | N/A — no sessions |
| V4 Access Control | no | N/A — no privileged ops |
| V5 Input Validation | yes | `Literal["ltx_native", "cosyvoice", "indextts2_fallback"]` strict enum on `tts_engine`; `validate_voice_clone_ref()` rejects invalid wav format / duration / sample_rate |
| V6 Cryptography | no | N/A — no crypto |
| V12 Files & Resources | yes | `validate_voice_clone_ref()` validates local file path before passing to ComfyUI / gold-team; rejects symlinks to system paths (defensive check optional) |

### Known Threat Patterns for DUB stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid `tts_engine` string in shot-list JSON (typo or LLM hallucination) | Tampering | `Literal` enum + `validate_tts_engine_division()` rejects unknown values; no fuzzy matching (CONTEXT.md locked decision) |
| Path traversal via `voice_clone_reference_wav` (e.g., `../../etc/passwd`) | Tampering | `validate_voice_clone_ref()` should canonicalize path via `Path.resolve()` + verify result stays inside `assets/voice_refs/` directory (defensive; Plan A implementation detail) |
| Copyright infringement via unauthorized voice clone sample | Repudiation (legal) | CLAUDE.md Constraints: "operator must provide owned reference audio". validate_voice_clone_ref validates FORMAT not ownership. Documented as operator-action handoff per DUB-03. |

## Sources

### Primary (HIGH confidence — verified live 2026-07-09)

**Codebase (kais-hermes-skills @ HEAD 5772f55):**
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py` — full read (312 lines). PipelineState `@dataclass`, `validate_form_factor_invariant()` precedent (lines 111-140), `_STATE_FIELDS` auto-derivation (line 108), `load()` forward-compat filter (line 227).
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py` — full read (234 lines). Gold-team API goal f-string (lines 117-147), schema enum including "IndexTTS2|CosyVoice|..." (line 152), `delegate_task` pattern.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` — lines 370-470. Shot schema (`shot_list` plain dict with shot_id/intent/duration_sec/audio_cue/ltx_prompt), `_FORM_FACTOR_INSTRUCTION` precedent.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/tts_batch.py` — full read (152 lines). Current default: Qwen3-TTS via gold-team API (port 8002); `VOICE_MAP` per-character structure.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/comfyui-indextts2-setup.md` — full read (371 lines). 9-step dependency fix pattern + ComfyUI workflow JSON template + Non-blocking Batch Submission pattern.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/SKILL.md` — lines 1-200. 6 sub-steps (voicer/lip_sync/composer/foley/mixer/spatial_audio), TTS Provider API params (lines 162-175), CosyVoice-300M phantom note (line 174), `<tts_primary>` placeholder convention.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` — full read (112 lines). 6-provider capability matrix (MiniMax/ElevenLabs/Voxtral/Gemini/Edge/NeuTTS), CosyVoice phantom strip note, 5s voice cloning sample protocol.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/gold-team-tts-api.md` — full read (248 lines). Async task API contract, `/api/v1/engines` endpoint, CosyVoice-300M as auto-route for `tts_zh` (line 124), 8 documented pitfalls (silent-output, trailing punctuation, ellipsis bug).
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh` — full read (76 lines). CosyVoice de-phantom note (lines 5-7), gold-team log tail pattern, task status polling.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/gold-team-tts-batch.py` — full read (185 lines). Batch submit-then-poll pattern, silent-output detection + retry (Pitfall #7 mitigation), duration matching via ffmpeg atempo/trim/apad.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/GAP-REPORT.md` — full read. CosyVoice-300M stale version note (line 21), missing `cosyvoice-deployment.md` ref (line 58).
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` — lines 420-540. IndexTTS2 as P10 default (line 457), Generation Engine Selection authoritative source rule (line 433), gold-team env vars, GLM rate limit pitfall.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/episodes/formc-test-01/.pipeline-assets/character-bible.json` — schema inspection. Envelope V3 format (`value.characters[].4d_anchor.{identity,arc,voice,visual}`), 3 characters, voice field is free-text description.

**Live Docker + API verification (2026-07-09):**
- `docker exec comfyui-primary ls /root/ComfyUI/custom_nodes/` — AIIA package present; `filliptm` NOT present.
- `curl -s http://127.0.0.1:8188/object_info` — `AIIA_CosyVoice_ModelLoader`, `AIIA_CosyVoice_VoiceConversion`, `AIIA_CosyVoice_TTS` nodes registered.
- `docker exec comfyui-primary head -100 /root/ComfyUI/custom_nodes/ComfyUI_AIIA/aiia_cosyvoice_nodes.py` — V1/V2/V3 auto-detection via yaml config file, RL model switching logic, Matcha-TTS cache clearing.
- `docker exec comfyui-primary sed -n '662,720p' .../aiia_cosyvoice_nodes.py` — `AIIA_CosyVoice_TTS.INPUT_TYPES()` requires `model, tts_text, instruct_text, base_gender, dialect, emotion, spk_id, speed, seed`; optional `reference_audio`. Emotion tags supported. Multi-emotion segment detection.
- `docker exec comfyui-primary ls /root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512/` — model fully downloaded (flow.pt, hift.pt, llm.base.pt, llm.pt, cosyvoice3.yaml, etc.).
- `curl -s http://127.0.0.1:8002/api/v1/engines` — `tts-tracker` engine online, models: `["GPT-SoVITS","Chatterbox-Turbo","CosyVoice-300M"]`. `local-comfyui` engine offline but lists `cosyvoice` among its models.

### Secondary (MEDIUM confidence)
- [filliptm/ComfyUI_FL-CosyVoice3 GitHub README](https://github.com/filliptm/ComfyUI_FL-CosyVoice3) — node list (`Instruct2`, `Save Speaker`, `Speaker Clone`, `Speaker Instruct2`), 3-30s reference protocol, "CosyVoice-300M won't work well" warning, last commit ~Jan 2025. Used for CONTEXT.md reconciliation but NOT for Plan A recommendation.
- `.planning/research/v14-4track-upgrade/STACK.md` — CosyVoice 2.0-0.5B selection rationale, filliptm recommendation (overridden by live verification in this research).
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — D-1 (BLOCKER doubled audio), D-2 (BLOCKER operator wavs), D-3 (WARNING ComfyUI dep hell), D-5 (WARNING GPU contention), D-6 (WARNING backward-compat).

### Tertiary (LOW confidence — needs validation)
- CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0-0.5B-2512 A/B quality in actual kais-movie-pipeline Chinese dialogue scenarios — `[ASSUMED]` from STACK.md README SS numbers (75.7% vs 78.0%). DUB-05 operator benchmark will validate.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; AIIA CosyVoice verified live; gold-team CosyVoice-300M verified live
- Architecture (plain-dict Shot validator): HIGH — verified against `store.py:111-140` precedent + `p09_shot_breakdown.py:381` Shot schema
- ComfyUI node recommendation: MEDIUM — AIIA (HIGH confidence working) vs filliptm (MEDIUM confidence from CONTEXT.md, NOT installed); researcher recommends AIIA
- CosyVoice 2 vs 3 benchmark: LOW — no empirical pipeline data yet; DUB-05 operator-action handoff
- LTX native audio detection mechanism: HIGH — verified NO existing flag; Plan A must add `ltx_native_dialogue: bool` explicit field

**Cross-repo:**
- hermes-agent HEAD = `b6e09c241` (per git status snapshot)
- kais-hermes-skills HEAD = `5772f55` (verified 2026-07-09)

**Research date:** 2026-07-09
**Valid until:** 2026-08-08 (30 days — stable; the only currency risk is Docker container state change or ComfyUI node upgrade, both operator-controlled)
