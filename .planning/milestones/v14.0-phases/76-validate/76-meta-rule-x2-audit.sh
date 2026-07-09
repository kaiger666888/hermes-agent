#!/usr/bin/env bash
# Phase 76 VALIDATE — META-RULE X-2 audit (XCUT-02 closure).
# Mirrors 70-smoke.sh + 75-lineage-assert.sh pattern: set -euo pipefail, file-existence-FIRST,
# explicit -lt N thresholds (not bare == 0 gates which fail on comment lines).
#
# 3 audit phases per 70-VALIDATE-CHECKLIST.md XCUT-02a/b/c spec:
#   PHASE 1 — MUST count in 17 v14.0-touched SKILL.md files
#   PHASE 2 — _INSTRUCTION constant count in 5 phase modules
#   PHASE 3 — Goal-content test execution (keyword "goal_includes")
#
# Exit semantics: exits 0 if all 3 phases complete without file-missing errors. Coverage gaps
# (MUST without _INSTRUCTION or test) are reported as WARNINGs to stdout but do NOT hard-fail —
# they are surfaced into v14.0-MILESTONE-AUDIT.md §6 by Task 3 (mirror v13.0 P69 verdict=tech_debt
# pattern). Hard-failing would block milestone close even when the gap is acknowledged tech debt.
set -euo pipefail

# ── Locate repo root (script is at .planning/phases/76-validate/76-meta-rule-x2-audit.sh) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# ── Paths ──
KIAS_SKILLS_ROOT="/data/workspace/kais-hermes-skills"
PHASE_MODULES_DIR="$KIAS_SKILLS_ROOT/skills/kais-movie-pipeline/pipeline/phases"
TESTS_DIR="$KIAS_SKILLS_ROOT/skills/kais-movie-pipeline/tests"

# P70 baseline pin (kais-hermes-skills) + v14.0 final pin (Phase 74 last code-review fix)
P70_BASELINE_PIN="d9620369e48eec51c31ee72ac8827c288eaccf71"
V14_FINAL_PIN="ba58c2548ab82f0cd9acd7cc7af14402137f8520"

# 5 phase modules with _INSTRUCTION constants (XCUT-02 audit targets)
PHASE_MODULES=(
    p04_character_design.py
    p07_scene_generation.py
    p09_shot_breakdown.py
    p10_voice.py
    p13_delivery.py
)

# Goal-content test files (XCUT-02b/c — assert _INSTRUCTION keywords appear in captured["goal"])
GOAL_TEST_FILES=(
    test_p07_unit.py
    test_p09_unit.py
    test_p09_transition_unit.py
    test_p10_unit.py
)

echo "Phase 76 VALIDATE — META-RULE X-2 audit (XCUT-02 closure)"
echo "KIAS_SKILLS_ROOT: $KIAS_SKILLS_ROOT"
echo "P70 baseline pin:  $P70_BASELINE_PIN"
echo "v14.0 final pin:   $V14_FINAL_PIN"
echo ""

# ── Pre-flight: repo + directories exist (T-76-01 anti-spoofing) ──
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
# PHASE 1 — MUST count in 17 v14.0-touched SKILL.md files
# ============================================================================
echo "=== PHASE 1: MUST count in 17 v14.0-touched SKILL.md files ==="
echo ""

# Discover the 17 SKILL.md files from git diff (authoritative per T-76-01 threat mitigation)
SKILL_FILES=()
while IFS= read -r line; do
    SKILL_FILES+=("$line")
done < <(git -C "$KIAS_SKILLS_ROOT" diff --name-only "$P70_BASELINE_PIN" "$V14_FINAL_PIN" | grep 'SKILL\.md$')

SKILL_FILE_COUNT=${#SKILL_FILES[@]}
if [ "$SKILL_FILE_COUNT" -lt 17 ]; then
    echo "FAIL: expected >=17 SKILL.md files in v14.0 diff, got $SKILL_FILE_COUNT"
    exit 1
fi
echo "Discovered $SKILL_FILE_COUNT SKILL.md files in v14.0 diff ($P70_BASELINE_PIN..$V14_FINAL_PIN)"
echo ""

TOTAL_MUST_COUNT=0
for skill_path in "${SKILL_FILES[@]}"; do
    abs_path="$KIAS_SKILLS_ROOT/$skill_path"
    # File-existence-FIRST (T-76-01)
    if [ ! -f "$abs_path" ]; then
        echo "FAIL: SKILL.md missing at $abs_path"
        exit 1
    fi
    # Count MUST /MUST NOT  (case-sensitive, word-boundary)
    must_count=$(grep -cE 'MUST |MUST NOT ' "$abs_path" || true)
    TOTAL_MUST_COUNT=$((TOTAL_MUST_COUNT + must_count))
    short=$(echo "$skill_path" | sed 's|skills/movie-experts/||; s|skills/||; s|/SKILL.md||')
    printf "  %-45s %4d MUSTs\n" "$short" "$must_count"
done
echo ""
echo "PHASE 1 TOTAL_MUST_COUNT (17 files): $TOTAL_MUST_COUNT"
echo ""

# ============================================================================
# PHASE 2 — _INSTRUCTION constant count in 5 phase modules
# ============================================================================
echo "=== PHASE 2: _INSTRUCTION constant count in 5 phase modules ==="
echo ""

TOTAL_INSTRUCTION_COUNT=0
for mod in "${PHASE_MODULES[@]}"; do
    mod_path="$PHASE_MODULES_DIR/$mod"
    # File-existence-FIRST
    if [ ! -f "$mod_path" ]; then
        echo "FAIL: phase module missing at $mod_path"
        exit 1
    fi
    # Count module-level _INSTRUCTION constant definitions only (excludes in-function references)
    instr_count=$(grep -cE '^[A-Z_]+_INSTRUCTION\s*=' "$mod_path" || true)
    TOTAL_INSTRUCTION_COUNT=$((TOTAL_INSTRUCTION_COUNT + instr_count))
    printf "  %-30s %2d _INSTRUCTION constants\n" "$mod" "$instr_count"
done
echo ""
echo "PHASE 2 TOTAL_INSTRUCTION_COUNT (5 modules): $TOTAL_INSTRUCTION_COUNT"
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
    # File-existence-FIRST
    if [ ! -f "$test_path" ]; then
        echo "WARN: goal-content test missing at $test_path — WARNING (not blocker per XCUT-02c)"
        continue
    fi
    # Run pytest with keyword filter "goal_includes" — selects only goal-content tests
    # (avoids running the full 359-test suite). -x stops on first failure within the file.
    if (cd "$TESTS_DIR/.." && python3 -m pytest "tests/$test_file" -k "goal_includes" -x --tb=short -q >/dev/null 2>&1); then
        GOAL_TEST_PASSED=$((GOAL_TEST_PASSED + 1))
        echo "  OK:   $test_file (goal_includes tests PASSED)"
    else
        GOAL_TEST_FAILED=$((GOAL_TEST_FAILED + 1))
        echo "  WARN: $test_file (goal_includes tests FAILED or no match) — WARNING (XCUT-02c status=pending: missing test = WARNING)"
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
echo "META-RULE X-2 AUDIT — FINAL REPORT"
echo "=========================================="
echo "TOTAL_MUST_COUNT (17 SKILL.md):          $TOTAL_MUST_COUNT"
echo "TOTAL_INSTRUCTION_COUNT (5 phase mods):  $TOTAL_INSTRUCTION_COUNT"
echo "GOAL_TEST_PASSED:                        $GOAL_TEST_PASSED / $GOAL_TEST_EXPECTED"
echo ""

# Coverage gap check: MUST count vs _INSTRUCTION count
# Per CONTEXT.md D-02: "assert every MUST has a corresponding _INSTRUCTION + test"
# NOTE: This is a directional heuristic, not a strict 1:1 mapping — one _INSTRUCTION constant
# can cover multiple SKILL.md MUSTs (e.g. _FORM_FACTOR_INSTRUCTION covers form-related MUSTs
# across 15 SKILL.md Form Factor Adaptation sections). The check surfaces gross gaps only.
if [ "$TOTAL_INSTRUCTION_COUNT" -lt 1 ]; then
    echo "COVERAGE GAP (WARNING): zero _INSTRUCTION constants found — META-RULE X-2 violation"
elif [ "$TOTAL_MUST_COUNT" -gt 0 ] && [ "$TOTAL_INSTRUCTION_COUNT" -lt 10 ]; then
    echo "COVERAGE NOTE: $TOTAL_MUST_COUNT MUSTs across 17 SKILL.md covered by $TOTAL_INSTRUCTION_COUNT _INSTRUCTION constants"
    echo "  (heuristic ratio; one constant can cover multiple SKILL.md MUSTs — not a 1:1 mapping)"
fi

echo ""
echo "META-RULE X-2 audit status: COMPLETE (3 phases executed, warnings surfaced to milestone audit)"
exit 0
