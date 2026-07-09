# Phase 70: FOUNDATION-AUDIT - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 6 (4 markdown/bash/config deliverables + 2 optional/existing reference files to read)
**Analogs found:** 5 / 6 (1 deliverable has NO template — hand-rolled from RESEARCH.md spec)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` | markdown-deliverable (table + embedded JSON) | read-only enumeration → human + machine parse | `.planning/milestones/v13.0-MILESTONE-AUDIT.md` §2 + §3 (phase table + traceability matrix) | exact (table format) |
| `.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` | markdown-checklist (Phase 76 input) | hand-off doc → downstream phase gate | `.planning/milestones/v11.0-phases/55-VALIDATION.md` "Per-Task Verification Map" + "Wave 0 Requirements" | role-match (no exact template — hand-rolled) |
| `.planning/phases/70-foundation-audit/70-smoke.sh` | bash-smoke-runner | request-response (exit-code reporting) | `scripts/run_tests.sh` (set -euo pipefail + REPO_ROOT pattern) | role-match |
| `.planning/STATE.md` (edited — append) | markdown-state-record | append-only | `.planning/STATE.md` existing "Decisions (v14.0)" + "Hard Constraints Preserved" + "Risk Register" sections | exact (same file — append block) |
| `~/.hermes/config.yaml` (edited — flip 1 flag) | runtime-config (YAML) | config-read at runtime | current `~/.hermes/config.yaml:457-467` `curator:` block (verified) | exact (same file — set `enabled: false`) |
| `scripts/verify_lineage_inventory.py` (optional) | python-cli-smoke-checker | file-I/O (read SKILL.md + agent.yaml → sha256 compare → exit code) | `scripts/transform_skill_to_agent.py` (sha256 algorithm) + `scripts/run_milestone_audit.py` (argparse + main) | role-match |

## Pattern Assignments

### `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` (markdown-deliverable, table + JSON)

**Analog:** `.planning/milestones/v13.0-MILESTONE-AUDIT.md` §2 (phase-by-phase table) + §3 (requirements traceability matrix)

**Table format to copy** (from `v13.0-MILESTONE-AUDIT.md:116-125`):
```markdown
## §2 — Phase-by-Phase Audit Table

| Phase | Name | Status | Reqs | Evidence |
|-------|------|--------|------|---------|
| 62 | EXPERT-YAML-TRANSFORM | passed-human_needed (7/7 truths) | EXPERT-01..03 ✓ | `scripts/validate_phase62_yamls.py` exits 0 with `OK: 21/21`; ... |
```

**Apply to LINEAGE-INVENTORY** — 6-row schema per RESEARCH.md Pattern 1 (lines 144-174):
```markdown
| skill_id | SKILL.md path | sha256 (LF-norm UTF-8) | bytes | agent.yaml exists? | agent.yaml lineage.skill_sha256 | drift? |
|----------|---------------|------------------------|-------|--------------------|---------------------------------|--------|
```

**Embedded JSON block pattern** — copy the fenced ` ```json ` block structure from RESEARCH.md Pattern 1 lines 161-174 (machine-readable block for Phase 76 grep/parse).

**CRITICAL field-name invariant (RESEARCH Pitfall 1):** Use `lineage.skill_sha256` everywhere. The roadmap says `source_sha` but the actual schema (verified against 5 live agent YAMLs + transform script) uses `lineage.skill_sha256`. Planner MUST encode `lineage.skill_sha256` verbatim — any `source_sha` reference without parenthetical `(canonical: lineage.skill_sha256)` is suspect.

**Pre-existing drift handling (RESEARCH Pitfall 3):** The inventory MUST capture BOTH (a) current SKILL.md working-tree hash AND (b) current agent.yaml `lineage.skill_sha256` so Phase 75 can distinguish v14.0-introduced drift from pre-existing drift (cinematographer + audio_pipeline ALREADY mismatch as of 2026-07-09).

---

### `.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` (markdown-checklist for Phase 76)

**Analog:** `.planning/milestones/v11.0-phases/55-VALIDATION.md` "Per-Task Verification Map" (lines 36-46) + "Wave 0 Requirements" (lines 50-57)

**Table format to copy** (from `55-VALIDATION.md`):
```markdown
## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Command | Status |
|---------|------|------|-------------|-----------|---------|--------|
| 55-01-01 | 01 | 1 | EVAL-04 | unit | `pytest tests/v11-compaction/ -x` | ⬜ |
```

**Wave 0 Requirements format** (from `55-VALIDATION.md:50-57`):
```markdown
## Wave 0 Requirements

- [ ] `tests/v11-compaction/` (NEW dir + 600-record fixture)
- [ ] `tests/v11-schema-migration/` (NEW dir + 30-record fixture across 3 buckets)
```

**Apply to VALIDATE-CHECKLIST** — 6-row table per RESEARCH.md Validation Architecture > Phase Requirements → Test Map (lines 419-426). Each row maps XCUT-01 sub-claim (a/b/c/d/e/f) to smoke command:
```markdown
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| XCUT-01a | Lineage Impact Inventory file exists | smoke | `test -f .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md && echo OK` | ❌ Wave 0 |
| XCUT-01b | Inventory lists all 6 target SKILL.md files with sha256 | smoke | `grep -c "skills/.*SKILL.md" .../70-LINEAGE-INVENTORY.md` → expects 6 | ❌ Wave 0 |
| ... | ... | ... | ... | ... |
```

**Status glyphs convention** (from `55-VALIDATION.md`): `⬜ pending · ✅ green · ❌ red · ⚠️ flaky`.

---

### `.planning/phases/70-foundation-audit/70-smoke.sh` (bash-smoke-runner)

**Analog:** `scripts/run_tests.sh` (canonical test runner pattern) + `scripts/kill_modal.sh` (simpler smoke + grep + exit-code pattern)

**Bash idiom to copy** (from `scripts/run_tests.sh:29-33`):
```bash
#!/usr/bin/env bash
# <one-line purpose>
# Usage:
#   scripts/70-smoke.sh           # full smoke
#   scripts/70-smoke.sh -v        # verbose

set -euo pipefail

# ── Locate repo root ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"   # up from .planning/phases/70-*
```

**Grep pattern + exit-code idiom** (from `scripts/kill_modal.sh:11-21`):
```bash
# Each check: grep → expect count → echo OK/FAIL → exit non-zero on miss
COUNT=$(grep -c "skills/.*SKILL.md" "$REPO_ROOT/.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md" || true)
if [ "$COUNT" -lt 6 ]; then
    echo "FAIL: expected >=6 SKILL.md entries, got $COUNT"
    exit 1
fi
echo "OK: $COUNT SKILL.md entries in inventory"
```

**Final summary line** (from `kill_modal.sh:32-34`):
```bash
echo ""
echo "Phase 70 smoke status:"
# one-line summary
```

**CLAUDE.md compliance:**
- Use `set -uo pipefail` (kill_modal.sh pattern) OR `set -euo pipefail` (run_tests.sh pattern). Prefer `-euo` for smoke (hard fail on first error per Phase 70 read-only invariant).
- Always quote paths with `$VAR` inside double quotes.
- No `cat << 'EOF'` heredoc creation — bash here is read-only checks.

---

### `.planning/STATE.md` (edited — append v14.0.freeze block)

**Analog:** `.planning/STATE.md` itself — append a new section modeled on existing structure.

**Append-point:** After the "### Hard Constraints Preserved (v14.0)" section (lines 88-93) OR after the "### Blockers / Risks (v14.0 — active)" table (lines 148-158). Best fit: NEW section between Risk Register and Pending Todos, titled `### v14.0 Freeze Flags (active)`.

**Pattern to copy** (RESEARCH.md Pattern 3, lines 206-215):
```markdown
### v14.0 Freeze Flags (active — set by Phase 70, released by Phase 75)

| flag | value | set_by | released_by | enforcement |
|------|-------|--------|-------------|-------------|
| curator.enabled | false | Phase 70 | Phase 75 (post-bump) | `~/.hermes/config.yaml` (code-enforced via `agent/curator.py:is_enabled()`) |
| curator.consolidate | false | Phase 70 | Phase 75 (post-bump) | `~/.hermes/config.yaml` (defense-in-depth) |
| cross_repo_pin.hermes-agent | `846a8d7e...` | Phase 70 | Phase 76 (assertion) | STATE.md record (documentation) |
| cross_repo_pin.kais-hermes-skills | `d9620369...` | Phase 70 | Phase 76 (assertion) | STATE.md record (documentation) |
```

**Frontmatter consideration:** STATE.md has YAML frontmatter (lines 1-14) with `last_updated` + `last_activity` + progress counters. The Phase 70 edit should bump `last_activity: 2026-07-09` and (if executing) bump `completed_phases: 0 → 1` after Phase 70 ships. The freeze-block append itself does NOT touch frontmatter — it's a body section.

---

### `~/.hermes/config.yaml` (edited — flip `curator.enabled: true → false`)

**Analog:** the file itself — read lines 457-467, flip one boolean.

**Current state (verified via grep 2026-07-09):**
```yaml
# ~/.hermes/config.yaml:457-467
curator:
  enabled: true        # ← Phase 70 flips this to false
  interval_hours: 168
  min_idle_hours: 2
  stale_after_days: 30
  archive_after_days: 90
  consolidate: false   # already false (default) — defense-in-depth already in place
  prune_builtins: true
  backup:
    enabled: true
    keep: 5
```

**Target state (Phase 70 write):**
```yaml
curator:
  enabled: false       # FROZEN for v14.0 per XCUT-01 (Phase 70); release post-Phase-75
  interval_hours: 168
  # ...rest unchanged
```

**Exact YAML path:** `curator.enabled` (top-level key `curator`, sub-key `enabled`). Single-line edit.

**Enforcement mechanism** (RESEARCH.md Pattern 2, lines 177-199): `agent/curator.py:_load_config()` reads config fresh on every call. `is_enabled()` returns `False`. `run_curator_review` is gated. Survives gateway restarts (config.yaml is persistent on disk; NOT in-memory cached).

**Release:** Phase 75 (post-bump) flips back to `true`.

**Threat model** (RESEARCH.md A2 — VERIFIED not assumed): `hermes_cli/curator.py:271` `_cmd_evolve` also checks `is_enabled()` — so `hermes curator evolve --live` cannot bypass the freeze. The freeze is complete.

---

### `scripts/verify_lineage_inventory.py` (optional Wave 0 helper)

**Analogs (two combined):**
1. `scripts/transform_skill_to_agent.py` — canonical sha256 algorithm + read pattern
2. `scripts/run_milestone_audit.py` — argparse + main() + REPO_ROOT pattern

**Imports pattern** (from `scripts/transform_skill_to_agent.py:38-62`):
```python
from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

# Make the agent.* imports resolvable when invoked directly
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
```

**Canonical SHA-256 algorithm to copy verbatim** (from `scripts/transform_skill_to_agent.py:232-240`):
```python
def _compute_skill_sha256(content: str) -> str:
    """SHA-256 of LF-normalized SKILL.md content (Phase 49 §2.1 edge case).

    Per RESEARCH Pitfall 7: CRLF checkouts on Windows would produce a
    different hash than CI's LF hash, triggering phantom drift in
    curator's later detection pass. Normalize before hashing.
    """
    lf_content = content.replace("\r\n", "\n")
    return hashlib.sha256(lf_content.encode("utf-8")).hexdigest()
```

**Read + yaml.safe_load pattern for agent.yaml lineage** (from RESEARCH.md Example 2, lines 306-329):
```python
def read_agent_lineage(agent_name: str) -> dict:
    path = Path.home() / ".hermes" / "agents" / f"{agent_name}.agent.yaml"
    if not path.exists():
        return {"exists": False}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    lin = data.get("lineage", {})
    return {
        "exists": True,
        "skill_sha256": lin.get("skill_sha256"),      # canonical — NOT source_sha
        "transform_date": lin.get("transform_date"),
    }
```

**argparse + main + exit code** (from `scripts/run_milestone_audit.py:50-58, 62`):
```python
from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 70 lineage inventory smoke checker")
    parser.add_argument("--inventory", type=Path, default=REPO_ROOT / ".planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md")
    args = parser.parse_args()
    # ... checks ...
    return 0  # or 1 on miss

if __name__ == "__main__":
    sys.exit(main())
```

**CLAUDE.md compliance (mandatory):**
- `from __future__ import annotations` at top
- `encoding="utf-8"` on every `open()` / `read_text()` / `write_text()` (Ruff PLW1514)
- `get_hermes_home()` from `hermes_constants` (NEVER `Path.home()` — conftest redirect breaks it)
- `except X as exc:` with bound name; `logger.warning("...: %s", exc)` lazy %-format
- snake_case for functions/modules; PascalCase for classes

---

## Reference Code Map (not modified, but load-bearing for planner)

### `scripts/transform_skill_to_agent.py:179-240` — canonical lineage schema + sha256

**Planner use:** Phase 75 will re-run this exact transform. Phase 70's inventory hash column MUST match this algorithm byte-for-byte (LF-normalize → UTF-8 → sha256). Any divergence produces phantom drift in Phase 76's assertion.

**Lineage schema dict** (`scripts/transform_skill_to_agent.py:191-197`):
```python
"lineage": {
    "derived_from_skill_id": meta.get("expert_id", expert_name),
    "derived_from_repo": "kais-hermes-skills",
    "transform_date": date.today().isoformat(),
    "transform_notes": transform_notes,
    "skill_sha256": skill_sha,
},
```

**Canonical hash algorithm** (lines 232-240, extracted above in verify_lineage_inventory.py section).

**Field-name canonicalization** (RESEARCH Pitfall 1):
- ROADMAP says `source_sha` → CANONICAL is `lineage.skill_sha256`
- ROADMAP says `transform_rule_id` → CANONICAL is `lineage.transform_notes` (carries "Rule IDs:" substring)
- ROADMAP says `transform_timestamp` → CANONICAL is `lineage.transform_date` (ISO date, not full timestamp)

### `agent/curator.py:125-204` — config-load + freeze-flag check

**Planner use (threat_model reference):** Phase 70's freeze flag MUST be enforced by code in this range. Exact line numbers for the planner to cite in task actions:

- Line 125-138: `_load_config()` — reads `~/.hermes/config.yaml` `curator:` block fresh on every call (NOT cached at module import). Catches `(TypeError, ValueError, OSError, json.JSONDecodeError)` defensively.
- Line 141-144: `is_enabled()` — returns `bool(cfg.get("enabled", True))`. Returns `False` when `curator.enabled: false` is set.
- Line 191-204: `get_consolidate()` — returns `bool(cfg.get("consolidate", DEFAULT_CONSOLIDATE))`. Defaults to `False`. Already in the desired state — no Phase 70 action needed beyond documentation.

**Threat-model close-out:** `hermes_cli/curator.py:271` (`_cmd_evolve`) also calls `is_enabled()` — verified per RESEARCH A2. The `--live` flag cannot bypass the freeze.

---

## Shared Patterns

### Curator Freeze Flag Check

**Source:** `agent/curator.py:125-144`
**Apply to:** `.planning/STATE.md` v14.0.freeze documentation block + `70-VALIDATE-CHECKLIST.md` XCUT-01d row (smoke `hermes curator status | grep -q DISABLED`).

```python
# agent/curator.py:141-144 — the exact code that gates the freeze
def is_enabled() -> bool:
    """Default ON when no config says otherwise."""
    cfg = _load_config()
    return bool(cfg.get("enabled", True))
```

### SHA-256 Canonical Algorithm

**Source:** `scripts/transform_skill_to_agent.py:232-240`
**Apply to:** `70-LINEAGE-INVENTORY.md` hash column + `scripts/verify_lineage_inventory.py` (if created) + Phase 75 LINEAGE-BUMP re-transform + Phase 76 VALIDATE assertion.

```python
lf_content = content.replace("\r\n", "\n")
return hashlib.sha256(lf_content.encode("utf-8")).hexdigest()
```

**Verified hash values for 6 targets (2026-07-09, from RESEARCH.md Example 1 lines 296-302):**
| skill_id | sha256 (LF-norm UTF-8) | drift vs agent.yaml? |
|----------|------------------------|----------------------|
| cinematographer | `ebe9d3fa8e6b4987d6db2cb6a96bdd407ed526bfe8ce27bb31f8bf41ae5b535b` | **YES (pre-existing)** — agent.yaml has `b4bcc9c6...` |
| editor | `bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77` | no — matches `bd5bf4a1...` |
| audio_pipeline | `e047010520e3cc4afea5bb0fe96dc1e0ff7826708ae421339305090ce0aeaa9f` | **YES (pre-existing)** — agent.yaml has `fe59f7fa...` |
| drawer | `2c21f234380ca3fa1f918f733e3cb967d558cdc23b3cca2aedfcb6337682f1eb` | n/a (DEPRECATED stub; no agent.yaml — drawer merged into visual_executor) |
| kais-movie-pipeline | `bf8b7f5a48624dea563b8e37e46adb793dba0006090b334583d757ff7879b7ea` | n/a (skill-only, no agent.yaml) |
| kais-jimeng-cli | `3a9576a66a9567d64074fec278dceae97243f03e2607a902e2a5c4f6b6f4681b` | n/a (skill-only, no agent.yaml) |

### Bash Smoke Runner Idiom

**Source:** `scripts/run_tests.sh:29-33` + `scripts/kill_modal.sh:11-21`
**Apply to:** `70-smoke.sh` (all 6 XCUT-01 smoke checks in one script).

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# grep → count → expect → exit code
COUNT=$(grep -c "<pattern>" "<path>" || true)
[ "$COUNT" -ge <expected> ] || { echo "FAIL: ..."; exit 1; }
echo "OK: ..."
```

### Markdown Table + Embedded JSON Pattern

**Source:** `.planning/milestones/v13.0-MILESTONE-AUDIT.md` §2 + §3 + RESEARCH.md Pattern 1 (lines 144-174)
**Apply to:** `70-LINEAGE-INVENTORY.md` (the primary deliverable).

Dual-format: human-readable table (operator eyeballs drift column) + machine-readable ` ```json ` fenced block at the bottom (Phase 76 parses with `yaml.safe_load` or `json.loads`).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `70-VALIDATE-CHECKLIST.md` (full template) | markdown-checklist | hand-off doc → phase gate | No prior `.planning/**/CHECKLIST*.md` exists in the repo. Closest analog is the "Per-Task Verification Map" + "Wave 0 Requirements" pattern in `55-VALIDATION.md` / `53-VALIDATION.md` — but those are validation STRATEGY docs (per-task test map), not downstream-phase audit CHECKLISTS. Planner should hand-roll from RESEARCH.md Validation Architecture > Phase Requirements → Test Map (lines 419-426) which already specifies the 6 XCUT-01 rows. |

## Metadata

**Analog search scope:**
- `.planning/` (top-level + `milestones/v*-phases/*/` historical phase docs)
- `.planning/milestones/v{9,10,11,12,13}.0-MILESTONE-AUDIT.md` (5 milestone audits scanned)
- `scripts/*.sh` (3 bash scripts inspected: `run_tests.sh`, `kill_modal.sh`, `install.sh`)
- `scripts/*.py` (3 Python scripts inspected for argparse + main + sha256: `transform_skill_to_agent.py`, `run_milestone_audit.py`, `compute_fitness_baseline.py`)
- `agent/curator.py` (config-load + freeze-flag lines 80-204)
- `~/.hermes/config.yaml` (curator block lines 457-467)

**Files scanned:** ~25 files
**Pattern extraction date:** 2026-07-09

**Coverage summary:**
- 4 deliverables with exact analog (LINEAGE-INVENTORY table format, STATE.md append, config.yaml flag flip, verify_lineage_inventory.py sha256 algorithm)
- 1 deliverable with role-match analog (70-smoke.sh — bash idiom is clear but no Phase-70-shaped smoke exists yet)
- 1 deliverable with NO analog (70-VALIDATE-CHECKLIST.md — hand-rolled from RESEARCH spec; no prior checklist template in repo)
