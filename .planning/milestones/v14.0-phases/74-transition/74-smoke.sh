#!/usr/bin/env bash
# Phase 74 TRANSITION smoke runner — 17 assertions (TRANS-01..07 + XCUT-02). Usage: bash .planning/phases/74-transition/74-smoke.sh
set -euo pipefail
# Exits 0 only if all sub-claims pass. Hard-fails on first error, undefined var, or pipe failure.
# Each assertion maps to one row in 74-VALIDATION.md Per-Task Verification Map. Phase 76 VALIDATE
# re-runs this as a sanity check (XCUT-01 style per 70-smoke.sh skeleton).
#
# This script does NOT invoke live Docker / ComfyUI / Wan2.2 / Hailuo / Vidu (operator-action
# handoff per XCUT-04b). Live integration probes are documented in transition-engine-routing.md
# for operator pre-flight use.

# ── Locate repo roots ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 74 TRANSITION smoke — 17 assertions"
echo "Repo root: $REPO_ROOT"
echo "KHS root:  $KHS_ROOT"
echo ""

# =============================================================================
# TRANS-01: E-Konte Layer 5 schema extension (12-value enum + visual_hook + camera_continuity)
# =============================================================================

# TRANS-01a: e-konte-format.md references transition_method (the new 12-value field name)
EKONTE="$KHS_ROOT/skills/movie-experts/cinematographer/references/e-konte-format.md"
if [ ! -f "$EKONTE" ]; then
    echo "FAIL: TRANS-01a — e-konte-format.md missing at $EKONTE"
    exit 1
fi
COUNT=$(grep -c "transition_method" "$EKONTE" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-01a — expected >=1 'transition_method' in e-konte-format.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-01a — $COUNT 'transition_method' references in e-konte-format.md (>= 1)"

# TRANS-01b: e-konte-format.md documents the 12-value enum / 12-type taxonomy
COUNT=$(grep -c "12-value enum\|12-type taxonomy\|12-value\|12-type" "$EKONTE" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-01b — expected >=1 '12-value'/'12-type' in e-konte-format.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-01b — $COUNT '12-value'/'12-type' references in e-konte-format.md (>= 1)"

# =============================================================================
# TRANS-02: next_shot_link structured object migration with backward-compat reader
# =============================================================================

# TRANS-02a: load_next_shot_link('shot_02') returns transition_method=='hard_cut' (legacy coercion)
if ! python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from transition_schema import load_next_shot_link; r = load_next_shot_link('shot_02'); assert r['transition_method'] == 'hard_cut'" 2>/dev/null; then
    echo "FAIL: TRANS-02a — load_next_shot_link('shot_02') did not return transition_method=='hard_cut'"
    exit 1
fi
echo "OK: TRANS-02a — load_next_shot_link legacy string coercion works"

# TRANS-02b: _TRANSITION_METHOD_SET has exactly 12 values (enum cardinality sanity)
if ! python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from transition_schema import _TRANSITION_METHOD_SET; assert len(_TRANSITION_METHOD_SET) == 12" 2>/dev/null; then
    echo "FAIL: TRANS-02b — _TRANSITION_METHOD_SET len != 12"
    exit 1
fi
echo "OK: TRANS-02b — _TRANSITION_METHOD_SET has 12 values"

# =============================================================================
# TRANS-03: transition-design first-class asset (3-system registration)
# =============================================================================

# TRANS-03a: ASSET_SCHEMA contains 'transition-design' slot (system 1: asset bus)
if ! python3 -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from asset_bus import ASSET_SCHEMA; assert 'transition-design' in ASSET_SCHEMA" 2>/dev/null; then
    echo "FAIL: TRANS-03a — 'transition-design' not in ASSET_SCHEMA"
    exit 1
fi
echo "OK: TRANS-03a — transition-design slot registered in ASSET_SCHEMA"

# TRANS-03b: canvas_sync.py _PHASE_OUTPUT_MAP references transition_design (system 2: canvas)
CANVAS_SYNC="$KHS_ROOT/plugins/kais_aigc/canvas_sync.py"
if [ ! -f "$CANVAS_SYNC" ]; then
    echo "FAIL: TRANS-03b — canvas_sync.py missing at $CANVAS_SYNC"
    exit 1
fi
COUNT=$(grep -c "transition_design" "$CANVAS_SYNC" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-03b — expected >=1 'transition_design' in canvas_sync.py, got $COUNT"
    exit 1
fi
echo "OK: TRANS-03b — $COUNT 'transition_design' references in canvas_sync.py (>= 1)"

# =============================================================================
# TRANS-04: field-level ownership split (FOUND-08 preserved — no new expert_id)
# =============================================================================

# TRANS-04a: cinematographer SKILL.md cites creative-intent fields
CINEMATOGRAPHER="$KHS_ROOT/skills/movie-experts/cinematographer/SKILL.md"
if [ ! -f "$CINEMATOGRAPHER" ]; then
    echo "FAIL: TRANS-04a — cinematographer SKILL.md missing at $CINEMATOGRAPHER"
    exit 1
fi
COUNT=$(grep -c "transition_method\|visual_hook\|camera_continuity" "$CINEMATOGRAPHER" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-04a — expected >=1 creative-intent field in cinematographer SKILL.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-04a — $COUNT creative-intent field references in cinematographer SKILL.md (>= 1)"

# TRANS-04b: editor SKILL.md cites post-production execution fields
EDITOR="$KHS_ROOT/skills/movie-experts/editor/SKILL.md"
if [ ! -f "$EDITOR" ]; then
    echo "FAIL: TRANS-04b — editor SKILL.md missing at $EDITOR"
    exit 1
fi
COUNT=$(grep -c "cut_duration_frames\|dissolve_curve\|match_cut_alignment_point" "$EDITOR" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-04b — expected >=1 execution field in editor SKILL.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-04b — $COUNT execution field references in editor SKILL.md (>= 1)"

# =============================================================================
# TRANS-05: transition-design.md 12-type taxonomy ref
# =============================================================================

# TRANS-05a: transition-design.md exists
TD_REF="$KHS_ROOT/skills/movie-experts/cinematographer/references/transition-design.md"
if [ ! -f "$TD_REF" ]; then
    echo "FAIL: TRANS-05a — transition-design.md missing at $TD_REF"
    exit 1
fi
echo "OK: TRANS-05a — transition-design.md exists"

# TRANS-05b: transition-design.md contains >= 3 canonical transition_method values (taxonomy sanity)
COUNT=$(grep -c "match_cut_shared_object\|whip_pan\|j_cut" "$TD_REF" || true)
if [ "$COUNT" -lt 3 ]; then
    echo "FAIL: TRANS-05b — expected >=3 canonical transition_method values in transition-design.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-05b — $COUNT canonical transition_method values in transition-design.md (>= 3)"

# =============================================================================
# TRANS-06: transition-engine-routing.md declarative per-transition routing
# =============================================================================

# TRANS-06a: transition-engine-routing.md exists
ROUTING_REF="$KHS_ROOT/skills/kais-movie-pipeline/references/transition-engine-routing.md"
if [ ! -f "$ROUTING_REF" ]; then
    echo "FAIL: TRANS-06a — transition-engine-routing.md missing at $ROUTING_REF"
    exit 1
fi
echo "OK: TRANS-06a — transition-engine-routing.md exists"

# TRANS-06b: routing table cites Wan2.2 (local match-cut engine)
COUNT=$(grep -c "Wan2.2" "$ROUTING_REF" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-06b — expected >=1 'Wan2.2' in transition-engine-routing.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-06b — $COUNT 'Wan2.2' references in transition-engine-routing.md (>= 1)"

# TRANS-06c: routing table cites ffmpeg xfade (post-production fallback for dissolve/wipe/fade)
COUNT=$(grep -c "ffmpeg xfade" "$ROUTING_REF" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-06c — expected >=1 'ffmpeg xfade' in transition-engine-routing.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-06c — $COUNT 'ffmpeg xfade' references in transition-engine-routing.md (>= 1)"

# =============================================================================
# TRANS-07: LTX-2.3 FLF + ICLoRA combined workflow validation report template
# =============================================================================

# TRANS-07a: ltx-flf-iclora-validation.md exists (research-scope template)
LTX_VAL="$KHS_ROOT/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md"
if [ ! -f "$LTX_VAL" ]; then
    echo "FAIL: TRANS-07a — ltx-flf-iclora-validation.md missing at $LTX_VAL"
    exit 1
fi
LINES=$(wc -l < "$LTX_VAL")
if [ "$LINES" -lt 80 ]; then
    echo "FAIL: TRANS-07a — ltx-flf-iclora-validation.md expected >=80 lines, got $LINES"
    exit 1
fi
echo "OK: TRANS-07a — ltx-flf-iclora-validation.md exists ($LINES lines, >= 80)"

# TRANS-07b: validation template documents ICLoRA (PITFALL T-1 orthogonality)
COUNT=$(grep -c "ICLoRA" "$LTX_VAL" || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: TRANS-07b — expected >=1 'ICLoRA' in ltx-flf-iclora-validation.md, got $COUNT"
    exit 1
fi
echo "OK: TRANS-07b — $COUNT 'ICLoRA' references in ltx-flf-iclora-validation.md (>= 1)"

# =============================================================================
# XCUT-02: META-RULE X-2 _INSTRUCTION injection (3-site pattern: constant + .task + .constraints)
# =============================================================================

# XCUT-02a: p09_shot_breakdown.py references _TRANSITION_DESIGN_INSTRUCTION (>=2: definition + .task injection)
P09="$KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py"
if [ ! -f "$P09" ]; then
    echo "FAIL: XCUT-02a — p09_shot_breakdown.py missing at $P09"
    exit 1
fi
COUNT=$(grep -c "_TRANSITION_DESIGN_INSTRUCTION" "$P09" || true)
if [ "$COUNT" -lt 2 ]; then
    echo "FAIL: XCUT-02a — expected >=2 '_TRANSITION_DESIGN_INSTRUCTION' in p09_shot_breakdown.py (definition + .task), got $COUNT"
    exit 1
fi
echo "OK: XCUT-02a — $COUNT '_TRANSITION_DESIGN_INSTRUCTION' references in p09 (>= 2)"

# XCUT-02b: p13_delivery.py references _EDITOR_TRANSITION_EXECUTION_INSTRUCTION or _TRANSITION_DESIGN_INSTRUCTION (>=2)
P13="$KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py"
if [ ! -f "$P13" ]; then
    echo "FAIL: XCUT-02b — p13_delivery.py missing at $P13"
    exit 1
fi
COUNT=$(grep -c "_EDITOR_TRANSITION_EXECUTION_INSTRUCTION\|_TRANSITION_DESIGN_INSTRUCTION" "$P13" || true)
if [ "$COUNT" -lt 2 ]; then
    echo "FAIL: XCUT-02b — expected >=2 _INJECTION references in p13_delivery.py (definition + .task), got $COUNT"
    exit 1
fi
echo "OK: XCUT-02b — $COUNT _INJECTION references in p13_delivery.py (>= 2)"

# =============================================================================
# Phase 74 smoke complete
# =============================================================================

echo ""
echo "Phase 74 smoke status: ALL 17 ASSERTIONS PASSED"
