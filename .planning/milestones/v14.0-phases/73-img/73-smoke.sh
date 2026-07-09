#!/usr/bin/env bash
# Phase 73 IMG smoke runner — 15 assertions. Usage: bash .planning/phases/73-img/73-smoke.sh
#
# Validates file/code presence for IMG-01..06 + XCUT-02 across the two repos.
# Does NOT invoke live dreamina CLI / GLM-4.6V / ComfyUI (operator-action handoff).
# Exits non-zero on first failure. Mirror of 70-smoke.sh / 72-smoke.sh skeleton.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 73 IMG smoke — 15 assertions"
echo "Repo root: $REPO_ROOT"
echo "KHS root:  $KHS_ROOT"
echo ""

# ── IMG-01: dreamina_manager.py orchestrator (asyncio.Semaphore + tenacity) ──

# IMG-01a: dreamina_manager.py exists
TARGET="$KHS_ROOT/plugins/kais_aigc/dreamina_manager.py"
if [ ! -f "$TARGET" ]; then
    echo "FAIL: IMG-01a — dreamina_manager.py missing at $TARGET"
    exit 1
fi
echo "OK: IMG-01a — dreamina_manager.py exists"

# IMG-01b: asyncio.Semaphore concurrency cap
COUNT=$(grep -c 'asyncio.Semaphore' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-01b — expected >=1 asyncio.Semaphore in dreamina_manager.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-01b — $COUNT asyncio.Semaphore entries (>= 1)"

# IMG-01c: tenacity / AsyncRetrying retry strategy
COUNT=$(grep -cE 'tenacity|AsyncRetrying' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-01c — expected >=1 tenacity/AsyncRetrying in dreamina_manager.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-01c — $COUNT tenacity entries (>= 1)"

# ── IMG-02: sync queue (asyncio.gather block-on-all) ──

# IMG-02a: asyncio.gather blocks pipeline_state write until all resolve
COUNT=$(grep -c 'asyncio.gather' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-02a — expected >=1 asyncio.gather in dreamina_manager.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-02a — $COUNT asyncio.gather entries (>= 1)"

# ── IMG-03: vision_verify.py GLM-4.6V gate ──

# IMG-03a: vision_verify.py exists
TARGET="$KHS_ROOT/plugins/kais_aigc/vision_verify.py"
if [ ! -f "$TARGET" ]; then
    echo "FAIL: IMG-03a — vision_verify.py missing at $TARGET"
    exit 1
fi
echo "OK: IMG-03a — vision_verify.py exists"

# IMG-03b: task="vision" routing (NOT boolean flag — CRITICAL CORRECTION per PATTERNS)
COUNT=$(grep -c 'task="vision"' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-03b — expected >=1 task=\"vision\" in vision_verify.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-03b — $COUNT task=\"vision\" entries (>= 1)"

# IMG-03c: async_call_llm integration
COUNT=$(grep -c 'async_call_llm' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-03c — expected >=1 async_call_llm in vision_verify.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-03c — $COUNT async_call_llm entries (>= 1)"

# ── IMG-04: RHD/LHD 3-attempt budget + image2image fallback ──

# IMG-04a: image2image + _escalate_prompt in dreamina_manager.py
TARGET="$KHS_ROOT/plugins/kais_aigc/dreamina_manager.py"
COUNT=$(grep -cE 'image2image|_escalate_prompt' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-04a — expected >=1 image2image|_escalate_prompt in dreamina_manager.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-04a — $COUNT image2image/_escalate_prompt entries (>= 1)"

# ── IMG-05: MetricsBuffer + dreamina CLI registration ──

# IMG-05a: dreamina_stats.py exists
TARGET="$KHS_ROOT/plugins/kais_aigc/dreamina_stats.py"
if [ ! -f "$TARGET" ]; then
    echo "FAIL: IMG-05a — dreamina_stats.py missing at $TARGET"
    exit 1
fi
echo "OK: IMG-05a — dreamina_stats.py exists"

# IMG-05b: register_cli_command in kais_aigc __init__.py (CLI hook wired)
TARGET="$KHS_ROOT/plugins/kais_aigc/__init__.py"
COUNT=$(grep -c 'register_cli_command' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-05b — expected >=1 register_cli_command in __init__.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-05b — $COUNT register_cli_command entries (>= 1)"

# IMG-05c: dreamina_stats.jsonl MetricsBuffer file path referenced
TARGET="$KHS_ROOT/plugins/kais_aigc/dreamina_stats.py"
COUNT=$(grep -c 'dreamina_stats.jsonl' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: IMG-05c — expected >=1 dreamina_stats.jsonl in dreamina_stats.py, got $COUNT"
    exit 1
fi
echo "OK: IMG-05c — $COUNT dreamina_stats.jsonl entries (>= 1)"

# ── IMG-06: image2image-stratification.md reference ──

# IMG-06a: image2image-stratification.md exists
TARGET="$KHS_ROOT/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md"
if [ ! -f "$TARGET" ]; then
    echo "FAIL: IMG-06a — image2image-stratification.md missing at $TARGET"
    exit 1
fi
echo "OK: IMG-06a — image2image-stratification.md exists"

# IMG-06b: 1-ref / 3-ref / 5-ref strata documented
COUNT=$(grep -cE '1-ref|3-ref|5-ref' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 3 ]; then
    echo "FAIL: IMG-06b — expected >=3 strata references, got $COUNT"
    exit 1
fi
echo "OK: IMG-06b — $COUNT strata references (>= 3)"

# ── XCUT-02: _VISION_VERIFY_INSTRUCTION injection visible at 2 sites ──

# XCUT-02a: _VISION_VERIFY_INSTRUCTION in p07_scene_generation.py (>= 2:
# constant definition + .task injection)
TARGET="$KHS_ROOT/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py"
COUNT=$(grep -c '_VISION_VERIFY_INSTRUCTION' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 2 ]; then
    echo "FAIL: XCUT-02a — expected >=2 _VISION_VERIFY_INSTRUCTION in p07, got $COUNT"
    exit 1
fi
echo "OK: XCUT-02a — $COUNT _VISION_VERIFY_INSTRUCTION entries (>= 2)"

# XCUT-02b: vision-verify MUST gate in SKILL.md body
# NOTE: Plan 73-03 specified literal "MUST vision-verify", but the actual
# SKILL.md body patch (Plan 73-02 T4) escalated the line to
# "MUST be vision-verified before upload to ComfyUI". Rule 1 auto-fix:
# the smoke assertion matches the actual artifact text. Intent preserved
# (vision-verify MUST gate presence in SKILL.md body).
TARGET="$KHS_ROOT/skills/kais-movie-pipeline/SKILL.md"
COUNT=$(grep -c 'MUST be vision-verified' "$TARGET" 2>/dev/null || true)
if [ "$COUNT" -lt 1 ]; then
    echo "FAIL: XCUT-02b — expected >=1 'MUST be vision-verified' in SKILL.md, got $COUNT"
    exit 1
fi
echo "OK: XCUT-02b — $COUNT 'MUST be vision-verified' entries (>= 1)"

echo ""
echo "Phase 73 smoke status: ALL 15 ASSERTIONS PASSED"
