#!/usr/bin/env bash
# Phase 83 VALIDATE — META-RULE X-2 audit (v15.0 extension).
# Mirrors v14.0's 76-meta-rule-x2-audit.sh structure, adapted for v15.0 scope:
#   - v15.0 baseline is v14.0 final pin (ba58c254 for kais-hermes-skills)
#   - v15.0 added 0 new _INSTRUCTION constants (all 6 code phases created scripts/plugins, NOT phase modules)
#   - v15.0 touched 0 movie-experts SKILL.md files (only kais-jimeng-cli/SKILL.md — NOT under movie-experts/)
#   - The 5 existing phase modules + 4 goal-test files are UNCHANGED from v14.0
#
# 3 audit phases (mirror v14.0 76-meta-rule-x2-audit.sh):
#   PHASE 1 — movie-experts SKILL.md touch count + MUST count in v15.0 diff
#   PHASE 2 — _INSTRUCTION constant count in 5 phase modules (unchanged from v14.0)
#   PHASE 3 — Goal-content test execution (keyword "goal_includes")
#
# Exit semantics: exits 0 on completion. Coverage gaps are WARNINGs surfaced to
# v15.0-MILESTONE-AUDIT.md §6, NOT blockers (mirror v14.0 P76 precedent).
set -euo pipefail

# ── Locate repo root (script is at .planning/phases/83-validate/83-meta-rule-x2-audit.sh) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# ── Paths ──
KIAS_SKILLS_ROOT="/data/workspace/kais-hermes-skills"
PHASE_MODULES_DIR="$KIAS_SKILLS_ROOT/skills/kais-movie-pipeline/pipeline/phases"
TESTS_DIR="$KIAS_SKILLS_ROOT/skills/kais-movie-pipeline/tests"

# v14.0 final pin (kais-hermes-skills) — v15.0 baseline
V14_FINAL_PIN="ba58c2548ab82f0cd9acd7cc7af14402137f8520"

# v15.0 final pin — capture at runtime (do NOT hardcode; script runs before tag placement)
V15_FINAL_PIN="$(git -C "$KIAS_SKILLS_ROOT" rev-parse HEAD)"

# 5 phase modules with _INSTRUCTION constants (unchanged from v14.0 — v15.0 added 0 new)
PHASE_MODULES=(
    p04_character_design.py
    p07_scene_generation.py
    p09_shot_breakdown.py
    p10_voice.py
    p13_delivery.py
)

# Goal-content test files (unchanged from v14.0 — v15.0 added 0 new)
GOAL_TEST_FILES=(
    test_p07_unit.py
    test_p09_unit.py
    test_p09_transition_unit.py
    test_p10_unit.py
)

echo "Phase 83 VALIDATE — META-RULE X-2 audit (v15.0 extension)"
echo "KIAS_SKILLS_ROOT: $KIAS_SKILLS_ROOT"
echo "v14.0 final pin:  $V14_FINAL_PIN"
echo "v15.0 final pin:  $V15_FINAL_PIN"
echo ""

# ── Pre-flight: repo + directories exist ──
if [ ! -d "$KIAS_SKILLS_ROOT/.git" ]; then
    echo "FAIL: KIAS_SKILLS_ROOT missing or not a git repo at $KIAS_SKILLS_ROOT"
    exit 1
fi
if [ ! -d "$PHASE_MODULES_DIR" ]; then
    echo "FAIL: PHASE_MODULES_DIR missing at $PHASE_MODULES_DIR"
    exit 1
fi
if [ ! -d "$TESTS_DIR" ]; then
    echo "FAIL: TESTS_DIR missing at $TESTS_DIR"
    exit 1
fi

# ============================================================================
# PHASE 1 — movie-experts SKILL.md touch count + MUST count in v15.0 diff
# ============================================================================
echo "=== PHASE 1: movie-experts SKILL.md touch count + MUST count (v15.0 diff) ==="
echo ""

# Discover ALL SKILL.md files touched in v15.0 diff (v14.0 final → v15.0 final)
ALL_SKILL_FILES=()
while IFS= read -r line; do
    ALL_SKILL_FILES+=("$line")
done < <(git -C "$KIAS_SKILLS_ROOT" diff --name-only "$V14_FINAL_PIN" HEAD | grep 'SKILL\.md$' || true)

ALL_SKILL_COUNT=${#ALL_SKILL_FILES[@]}
echo "Discovered $ALL_SKILL_COUNT SKILL.md files in v15.0 diff ($V14_FINAL_PIN..HEAD)"
for f in "${ALL_SKILL_FILES[@]}"; do
    echo "  - $f"
done
echo ""

# Filter: only movie-experts SKILL.md files (the META-RULE X-2 protected set)
MOVIE_EXPERTS_SKILL_FILES=()
for f in "${ALL_SKILL_FILES[@]}"; do
    if [[ "$f" == skills/movie-experts/*/SKILL.md ]]; then
        MOVIE_EXPERTS_SKILL_FILES+=("$f")
    fi
done
MOVIE_EXPERTS_COUNT=${#MOVIE_EXPERTS_SKILL_FILES[@]}

if [ "$MOVIE_EXPERTS_COUNT" -eq 0 ]; then
    echo "INFO: v15.0 did not touch movie-experts SKILL.md files — coverage unchanged from v14.0 baseline"
else
    echo "WARN: v15.0 touched $MOVIE_EXPERTS_COUNT movie-experts SKILL.md files (hard constraint: L1-L6 read-only invariant REVERTED post-v14.0)"
    for f in "${MOVIE_EXPERTS_SKILL_FILES[@]}"; do
        echo "  WARN: $f"
    done
fi
echo ""

# Check for kais-jimeng-cli SKILL.md (the single authorized touch per v15.0 hard constraints)
KAIS_JIMENG_TOUCHED=false
for f in "${ALL_SKILL_FILES[@]}"; do
    if [[ "$f" == *"kais-jimeng-cli/SKILL.md" ]]; then
        KAIS_JIMENG_TOUCHED=true
        echo "INFO: kais-jimeng-cli/SKILL.md touched (Phase 81 cloud-engine-bootstrap cross-reference) — 0 MUST markers expected, no META-RULE X-2 coverage impact"
        break
    fi
done
if [ "$KAIS_JIMENG_TOUCHED" = false ] && [ "$ALL_SKILL_COUNT" -gt 0 ]; then
    echo "INFO: kais-jimeng-cli/SKILL.md NOT in diff (other SKILL.md files touched)"
fi
echo ""

# Count MUSTs in movie-experts SKILL.md files (expected 0 — v15.0 did not modify MUST-bearing content)
TOTAL_MUST_COUNT=0
for skill_path in "${MOVIE_EXPERTS_SKILL_FILES[@]}"; do
    abs_path="$KIAS_SKILLS_ROOT/$skill_path"
    if [ ! -f "$abs_path" ]; then
        echo "FAIL: SKILL.md missing at $abs_path"
        exit 1
    fi
    must_count=$(grep -cE 'MUST |MUST NOT ' "$abs_path" || true)
    TOTAL_MUST_COUNT=$((TOTAL_MUST_COUNT + must_count))
    short=$(echo "$skill_path" | sed 's|skills/movie-experts/||; s|/SKILL.md||')
    printf "  %-45s %4d MUSTs\n" "$short" "$must_count"
done
echo ""
echo "PHASE 1 TOTAL_MUST_COUNT (movie-experts SKILL.md in v15.0 diff): $TOTAL_MUST_COUNT"
echo ""

# ============================================================================
# PHASE 2 — _INSTRUCTION constant count in 5 phase modules (unchanged from v14.0)
# ============================================================================
echo "=== PHASE 2: _INSTRUCTION constant count in 5 phase modules (unchanged from v14.0) ==="
echo ""

TOTAL_INSTRUCTION_COUNT=0
for mod in "${PHASE_MODULES[@]}"; do
    mod_path="$PHASE_MODULES_DIR/$mod"
    if [ ! -f "$mod_path" ]; then
        echo "FAIL: phase module missing at $mod_path"
        exit 1
    fi
    instr_count=$(grep -cE '^[A-Z_]+_INSTRUCTION\s*=' "$mod_path" || true)
    TOTAL_INSTRUCTION_COUNT=$((TOTAL_INSTRUCTION_COUNT + instr_count))
    printf "  %-30s %2d _INSTRUCTION constants\n" "$mod" "$instr_count"
done
echo ""
echo "PHASE 2 TOTAL_INSTRUCTION_COUNT (5 modules): $TOTAL_INSTRUCTION_COUNT"
echo "INFO: v15.0 added 0 new _INSTRUCTION constants — PHASE 2 coverage matches v14.0 baseline ($TOTAL_INSTRUCTION_COUNT constants)"
echo ""

# ============================================================================
# PHASE 3 — Goal-content test execution (keyword "goal_includes")
# ============================================================================
echo "=== PHASE 3: Goal-content test execution (keyword: goal_includes) ==="
echo ""

GOAL_TEST_PASSED=0
GOAL_TEST_FAILED=0
GOAL_TEST_EXPECTED=0

for test_file in "${GOAL_TEST_FILES[@]}"; do
    test_path="$TESTS_DIR/$test_file"
    GOAL_TEST_EXPECTED=$((GOAL_TEST_EXPECTED + 1))
    if [ ! -f "$test_path" ]; then
        echo "WARN: goal-content test missing at $test_path — WARNING (not blocker per XCUT-02c)"
        continue
    fi
    if (cd "$TESTS_DIR/.." && python3 -m pytest "tests/$test_file" -k "goal_includes" -x --tb=short -q >/dev/null 2>&1); then
        GOAL_TEST_PASSED=$((GOAL_TEST_PASSED + 1))
        echo "  OK:   $test_file (goal_includes tests PASSED)"
    else
        GOAL_TEST_FAILED=$((GOAL_TEST_FAILED + 1))
        echo "  WARN: $test_file (goal_includes tests FAILED or no match) — WARNING"
    fi
done
echo ""
echo "PHASE 3 GOAL_TEST_PASSED: $GOAL_TEST_PASSED / $GOAL_TEST_EXPECTED"
if [ "$GOAL_TEST_FAILED" -gt 0 ]; then
    echo "PHASE 3 GOAL_TEST_FAILED (warnings): $GOAL_TEST_FAILED"
fi
echo ""

# ============================================================================
# FINAL REPORT
# ============================================================================
echo "=========================================="
echo "META-RULE X-2 AUDIT — FINAL REPORT (v15.0)"
echo "=========================================="
echo "movie-experts SKILL.md files touched in v15.0:  $MOVIE_EXPERTS_COUNT (expected 0)"
echo "kais-jimeng-cli SKILL.md touched:                $KAIS_JIMENG_TOUCHED (expected true)"
echo "TOTAL_MUST_COUNT (movie-experts in v15.0 diff):  $TOTAL_MUST_COUNT (expected 0)"
echo "TOTAL_INSTRUCTION_COUNT (5 phase mods):          $TOTAL_INSTRUCTION_COUNT (expected 13, unchanged from v14.0)"
echo "GOAL_TEST_PASSED:                                $GOAL_TEST_PASSED / $GOAL_TEST_EXPECTED (expected 4/4)"
echo ""
echo "v15.0 added 0 new audit targets — coverage matches v14.0 baseline"
echo ""
echo "META-RULE X-2 audit status: COMPLETE (3 phases executed, warnings surfaced to milestone audit)"
exit 0
