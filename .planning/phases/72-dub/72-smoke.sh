#!/usr/bin/env bash
# Phase 72 DUB smoke runner — 11 assertions (DUB-01..05 + XCUT-02). Usage: bash .planning/phases/72-dub/72-smoke.sh
set -euo pipefail
# Exits 0 only if all 11 sub-claims pass. Hard-fails on first error, undefined var, or pipe failure.
# Each assertion maps to Phase 72 deliverables across Plan 72-01/02/03.
# Does NOT invoke live Docker / ComfyUI / gold-team (those are operator-action handoff probes
# documented in cosyvoice-deployment.md Healthcheck section).

# ── Locate repo roots ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 72 DUB smoke — 11 assertions"
echo "Repo root: $REPO_ROOT"
echo "KHS root:  $KHS_ROOT"
echo ""

# ============================================================================
# DUB-01a: ComfyUI AIIA CosyVoice workflow JSON exists (Plan 72-02 Task 1)
# ============================================================================
if [ ! -f "$KHS_ROOT/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json" ]; then
    echo "FAIL: DUB-01a — cosyvoice-comfyui.json missing"
    exit 1
fi
echo "OK: DUB-01a — cosyvoice-comfyui.json exists"

# ============================================================================
# DUB-01b: cosyvoice-deployment.md has >= 5 H2 sections (Plan 72-03 Task 1)
# ============================================================================
DEPLOY_SECTIONS=$(grep -c "^## " "$KHS_ROOT/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md" || true)
if [ "$DEPLOY_SECTIONS" -lt 5 ]; then
    echo "FAIL: DUB-01b — expected >=5 H2 sections in cosyvoice-deployment.md, got $DEPLOY_SECTIONS"
    exit 1
fi
echo "OK: DUB-01b — $DEPLOY_SECTIONS H2 sections in cosyvoice-deployment.md (>= 5)"

# ============================================================================
# DUB-02a: validate_tts_engine_division importable from store.py (Plan 72-01 Task 1)
# ============================================================================
if ! python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from store import validate_tts_engine_division; print('OK')" 2>/dev/null; then
    echo "FAIL: DUB-02a — validate_tts_engine_division not importable from store.py"
    exit 1
fi
echo "OK: DUB-02a — validate_tts_engine_division importable"

# ============================================================================
# DUB-02b: TTS_ENGINE_VALUES frozenset exists in store.py (Plan 72-01 Task 1)
# ============================================================================
TTS_ENGINE_VALUES_COUNT=$(grep -c "TTS_ENGINE_VALUES" "$KHS_ROOT/plugins/pipeline_state/store.py" || true)
if [ "$TTS_ENGINE_VALUES_COUNT" -lt 1 ]; then
    echo "FAIL: DUB-02b — TTS_ENGINE_VALUES not found in store.py, got $TTS_ENGINE_VALUES_COUNT"
    exit 1
fi
echo "OK: DUB-02b — TTS_ENGINE_VALUES found in store.py ($TTS_ENGINE_VALUES_COUNT occurrences)"

# ============================================================================
# DUB-03a: TTS_ENGINE_VALUES contains ltx_native + cosyvoice (Plan 72-01 Task 1)
# ============================================================================
if ! python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from store import TTS_ENGINE_VALUES; assert 'ltx_native' in TTS_ENGINE_VALUES and 'cosyvoice' in TTS_ENGINE_VALUES" 2>/dev/null; then
    echo "FAIL: DUB-03a — TTS_ENGINE_VALUES missing ltx_native or cosyvoice"
    exit 1
fi
echo "OK: DUB-03a — TTS_ENGINE_VALUES contains ltx_native + cosyvoice"

# ============================================================================
# DUB-03b: dub_validators.py exists (Plan 72-01 Task 2 — validate_voice_clone_ref)
# ============================================================================
if [ ! -f "$KHS_ROOT/plugins/pipeline_state/dub_validators.py" ]; then
    echo "FAIL: DUB-03b — dub_validators.py missing"
    exit 1
fi
echo "OK: DUB-03b — dub_validators.py exists"

# ============================================================================
# DUB-04a: SKILL.md IndexTTS2 demoted to DEPRECATED/fallback (Plan 72-02 Task 3)
# ============================================================================
DUB04_COUNT=$(grep -A2 "IndexTTS2" "$KHS_ROOT/skills/kais-movie-pipeline/SKILL.md" | grep -ci "deprecated\|fallback" || true)
if [ "$DUB04_COUNT" -lt 1 ]; then
    echo "FAIL: DUB-04a — IndexTTS2 not marked DEPRECATED/fallback in SKILL.md, got $DUB04_COUNT"
    exit 1
fi
echo "OK: DUB-04a — IndexTTS2 marked DEPRECATED/fallback in SKILL.md ($DUB04_COUNT matches)"

# ============================================================================
# DUB-05a: VERSION.json exists with tts.cosyvoice_default_variant field (Plan 72-03 Task 2)
# ============================================================================
if ! python3 -c "import json; d=json.load(open('$KHS_ROOT/VERSION.json')); assert 'cosyvoice_default_variant' in d.get('tts', {})" 2>/dev/null; then
    echo "FAIL: DUB-05a — VERSION.json missing tts.cosyvoice_default_variant"
    exit 1
fi
echo "OK: DUB-05a — VERSION.json has tts.cosyvoice_default_variant"

# ============================================================================
# DUB-05b: cosyvoice-benchmark.md template exists (Plan 72-03 Task 3)
# ============================================================================
if [ ! -f "$KHS_ROOT/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md" ]; then
    echo "FAIL: DUB-05b — cosyvoice-benchmark.md missing"
    exit 1
fi
echo "OK: DUB-05b — cosyvoice-benchmark.md exists"

# ============================================================================
# XCUT-02a: _TTS_ENGINE_INSTRUCTION constant in p10_voice.py (Plan 72-02 Task 4)
# ============================================================================
XCUT02A_COUNT=$(grep -c "_TTS_ENGINE_INSTRUCTION" "$KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py" || true)
if [ "$XCUT02A_COUNT" -lt 1 ]; then
    echo "FAIL: XCUT-02a — _TTS_ENGINE_INSTRUCTION not found in p10_voice.py, got $XCUT02A_COUNT"
    exit 1
fi
echo "OK: XCUT-02a — _TTS_ENGINE_INSTRUCTION found in p10_voice.py ($XCUT02A_COUNT occurrences)"

# ============================================================================
# XCUT-02b: "MUST propagate tts_engine" constraint in p10_voice.py (Plan 72-02 Task 4)
# ============================================================================
XCUT02B_COUNT=$(grep -c "MUST propagate tts_engine" "$KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p10_voice.py" || true)
if [ "$XCUT02B_COUNT" -lt 1 ]; then
    echo "FAIL: XCUT-02b — 'MUST propagate tts_engine' constraint not found in p10_voice.py"
    exit 1
fi
echo "OK: XCUT-02b — 'MUST propagate tts_engine' constraint present ($XCUT02B_COUNT occurrences)"

echo ""
echo "Phase 72 smoke status: ALL 11 ASSERTIONS PASSED"
