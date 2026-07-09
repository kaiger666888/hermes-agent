#!/usr/bin/env bash
# Phase 75 LINEAGE-BUMP assertion — 15 active movie-expert sha256 equality check.
# Mirrors 70-smoke.sh pattern: set -euo pipefail, file-existence-FIRST, explicit
# -lt N thresholds (not bare == 0). Exits 0 on 15/15 PASSED, exits 1 on first mismatch.
# Each assertion maps to XCUT-03 (lineage.skill_sha256 == sha256(SKILL.md LF-norm UTF-8)).
set -euo pipefail

# ── Locate repo root (script is at .planning/phases/75-lineage-bump/75-lineage-assert.sh) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# ── Paths ──
KIAS_SKILLS_ROOT="/data/workspace/kais-hermes-skills/skills/movie-experts"
AGENTS_DIR="$HOME/.hermes/agents"

# 15 active movie-expert agents (NOT drawer — DEPRECATED; NOT kais-movie-pipeline /
# kais-jimeng-cli — skill-only, no agent.yaml). Order is alphabetical-ish for readability.
EXPERTS=(
    cinematographer
    editor
    audio_pipeline
    screenplay
    hook_retention
    theory_critic
    character_designer
    continuity_auditor
    style_genome
    visual_executor
    colorist
    compliance_gate
    creative_source
    prompt_injector
    script_auditor
)

echo "Phase 75 lineage assertion — 15 active movie-expert sha256 equality check"
echo "KIAS_SKILLS_ROOT: $KIAS_SKILLS_ROOT"
echo "AGENTS_DIR:       $AGENTS_DIR"
echo ""

# ── Pre-flight: file-existence-FIRST checks (T-75-03 anti-tampering) ──
if [ ! -d "$KIAS_SKILLS_ROOT" ]; then
    echo "FAIL: KIAS_SKILLS_ROOT missing at $KIAS_SKILLS_ROOT"
    exit 1
fi
if [ ! -d "$AGENTS_DIR" ]; then
    echo "FAIL: AGENTS_DIR missing at $AGENTS_DIR"
    exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0

for expert in "${EXPERTS[@]}"; do
    skill_md="$KIAS_SKILLS_ROOT/$expert/SKILL.md"
    agent_yaml="$AGENTS_DIR/$expert.agent.yaml"

    # Per-expert file-existence-FIRST
    if [ ! -f "$skill_md" ]; then
        echo "FAIL: $expert — SKILL.md missing at $skill_md"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi
    if [ ! -f "$agent_yaml" ]; then
        echo "FAIL: $expert — agent.yaml missing at $agent_yaml"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    # Compute sha256 of LF-normalized UTF-8 working-tree bytes (canonical
    # algorithm per scripts/transform_skill_to_agent.py:232-240).
    skill_sha=$(python3 -c "
import hashlib
content = open('$skill_md', encoding='utf-8').read()
print(hashlib.sha256(content.replace('\r\n', '\n').encode('utf-8')).hexdigest())
")

    # Extract lineage.skill_sha256 from agent.yaml (strip quotes/whitespace).
    # head -1 guards against duplicate matches; sed extracts value after 'skill_sha256:'.
    agent_sha=$(grep 'skill_sha256:' "$agent_yaml" | head -1 | sed "s/.*skill_sha256:[\"' ]*//;s/[\"'].*//")

    if [ "$skill_sha" = "$agent_sha" ]; then
        echo "OK:   $expert — skill=${skill_sha:0:12}... agent=${agent_sha:0:12}... MATCH"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL: $expert — skill=${skill_sha:0:12}... agent=${agent_sha:0:12}... MISMATCH"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
echo "Phase 75 lineage assertion: ${PASS_COUNT}/${#EXPERTS[@]} PASSED, ${FAIL_COUNT} FAILED"

# Explicit threshold gate (NOT bare == 0 per planner anti-pattern rule).
if [ "$FAIL_COUNT" -lt 1 ]; then
    echo "Phase 75 lineage status: ALL ${#EXPERTS[@]} ASSERTIONS PASSED"
    exit 0
else
    echo "Phase 75 lineage status: FAILED — ${FAIL_COUNT} mismatches detected"
    exit 1
fi
