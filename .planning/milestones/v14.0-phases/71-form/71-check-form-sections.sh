#!/usr/bin/env bash
# Phase 71 FORM Plan 02 smoke runner — asserts all 15 canonical active movie-expert
# SKILL.md files have a "## Form Factor Adaptation" H2 section.
# Usage: bash .planning/phases/71-form/71-check-form-sections.sh
set -euo pipefail
# Exits 0 only if all 15 canonical active experts have the section. Hard-fails on
# first missing section, undefined var, or pipe failure.
#
# Canonical 15 active DAG experts per RESEARCH §15-Expert Tier Classification.
# Deprecated stubs (drawer / scene_builder / storyboard_designer / animator /
# voicer / composer / foley / mixer / spatial_audio / lip_sync / performer /
# continuity) are deliberately NOT enumerated — they are 654-byte redirect stubs
# (status: merged_into) and patching them is wasted work per PITFALL 3.

# ── Locate repo root (script is at .planning/phases/71-form/71-check-form-sections.sh) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 71 FORM Plan 02 smoke — 15-expert ## Form Factor Adaptation section presence"
echo "Repo root: $REPO_ROOT"
echo "KHS root:  $KHS_ROOT"
echo ""

# ── Canonical 15 active DAG experts (per RESEARCH §15-Expert Tier Classification) ──
EXPERTS=(
    hook_retention
    creative_source
    screenplay
    script_auditor
    character_designer
    cinematographer
    style_genome
    prompt_injector
    visual_executor
    continuity_auditor
    audio_pipeline
    editor
    colorist
    compliance_gate
    theory_critic
)

EXPECTED_COUNT=${#EXPERTS[@]}
FOUND_COUNT=0
FAILED_EXPERTS=()

for expert in "${EXPERTS[@]}"; do
    skill_file="$KHS_ROOT/skills/movie-experts/$expert/SKILL.md"
    if [ ! -f "$skill_file" ]; then
        echo "FAIL: $expert — SKILL.md missing at $skill_file"
        FAILED_EXPERTS+=("$expert")
        continue
    fi
    if grep -q "^## Form Factor Adaptation" "$skill_file"; then
        echo "OK: $expert — has ## Form Factor Adaptation"
        FOUND_COUNT=$((FOUND_COUNT + 1))
    else
        echo "FAIL: $expert — missing ## Form Factor Adaptation section"
        FAILED_EXPERTS+=("$expert")
    fi
done

echo ""
echo "Section count: $FOUND_COUNT / $EXPECTED_COUNT"

if [ "$FOUND_COUNT" -lt "$EXPECTED_COUNT" ]; then
    echo ""
    echo "FAIL: Missing sections for: ${FAILED_EXPERTS[*]}"
    echo "Phase 71 Plan 02 smoke status: FAILED"
    exit 1
fi

echo ""
echo "Phase 71 Plan 02 smoke status: ALL 15 EXPERTS HAVE ## Form Factor Adaptation"
