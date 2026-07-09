#!/usr/bin/env bash
# Phase 70 FOUNDATION-AUDIT smoke runner — 6 XCUT-01 assertions (XCUT-01a-f). Usage: bash .planning/phases/70-foundation-audit/70-smoke.sh
set -euo pipefail
# Exits 0 only if all 6 sub-claims pass. Hard-fails on first error, undefined var, or pipe failure.
# Each assertion maps to one row in 70-VALIDATE-CHECKLIST.md. Phase 76 VALIDATE re-runs this as a sanity check.

# ── Locate repo root (script is at .planning/phases/70-foundation-audit/70-smoke.sh) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

INVENTORY="$REPO_ROOT/.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md"
VALIDATE_CHECKLIST="$REPO_ROOT/.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md"
STATE_MD="$REPO_ROOT/.planning/STATE.md"
CONFIG_YAML="$HOME/.hermes/config.yaml"

echo "Phase 70 FOUNDATION-AUDIT smoke — 6 XCUT-01 assertions"
echo "Repo root: $REPO_ROOT"
echo ""

# XCUT-01a: Lineage Impact Inventory file exists
if [ ! -f "$INVENTORY" ]; then
    echo "FAIL: XCUT-01a — inventory file missing at $INVENTORY"
    exit 1
fi
echo "OK: XCUT-01a — inventory file exists"

# XCUT-01b: Inventory lists all 6 target SKILL.md files with sha256
INVENTORY_COUNT=$(grep -c 'skills/.*SKILL\.md' "$INVENTORY" || true)
if [ "$INVENTORY_COUNT" -lt 6 ]; then
    echo "FAIL: XCUT-01b — expected >=6 SKILL.md entries in inventory, got $INVENTORY_COUNT"
    exit 1
fi
echo "OK: XCUT-01b — $INVENTORY_COUNT SKILL.md entries in inventory (>= 6)"

# XCUT-01c: Inventory includes cross-repo commit pins for both repos
#           (both hermes-agent AND kais-hermes-skills must appear)
if ! grep -qE 'hermes-agent' "$INVENTORY"; then
    echo "FAIL: XCUT-01c — 'hermes-agent' cross-repo pin missing from inventory"
    exit 1
fi
if ! grep -qE 'kais-hermes-skills' "$INVENTORY"; then
    echo "FAIL: XCUT-01c — 'kais-hermes-skills' cross-repo pin missing from inventory"
    exit 1
fi
echo "OK: XCUT-01c — cross-repo pins for both repos present"

# XCUT-01d: Curator freeze active (config.yaml curator.enabled: false)
#           Config-flag grep (not CLI) so the assertion works without a running hermes CLI.
if [ ! -f "$CONFIG_YAML" ]; then
    echo "FAIL: XCUT-01d — config.yaml missing at $CONFIG_YAML"
    exit 1
fi
if ! grep -A1 "^curator:" "$CONFIG_YAML" | grep -q "enabled: false"; then
    echo "FAIL: XCUT-01d — curator.enabled is not false in $CONFIG_YAML"
    exit 1
fi
echo "OK: XCUT-01d — curator freeze active (curator.enabled: false)"

# XCUT-01e: STATE.md records the v14.0 Freeze Flags block
if ! grep -q "v14.0 Freeze Flags" "$STATE_MD"; then
    echo "FAIL: XCUT-01e — 'v14.0 Freeze Flags' block missing from STATE.md"
    exit 1
fi
echo "OK: XCUT-01e — v14.0 Freeze Flags block present in STATE.md"

# XCUT-01f: Phase 76 VALIDATE checklist drafted with >= 6 table rows
if [ ! -f "$VALIDATE_CHECKLIST" ]; then
    echo "FAIL: XCUT-01f — VALIDATE-CHECKLIST.md missing at $VALIDATE_CHECKLIST"
    exit 1
fi
CHECKLIST_ROWS=$(grep -c '^|' "$VALIDATE_CHECKLIST" || true)
if [ "$CHECKLIST_ROWS" -lt 6 ]; then
    echo "FAIL: XCUT-01f — expected >=6 table rows in VALIDATE-CHECKLIST.md, got $CHECKLIST_ROWS"
    exit 1
fi
echo "OK: XCUT-01f — $CHECKLIST_ROWS table rows in VALIDATE-CHECKLIST.md (>= 6)"

echo ""
echo "Phase 70 smoke status: ALL 6 XCUT-01 ASSERTIONS PASSED"
