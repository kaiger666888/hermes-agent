# Phase 70: FOUNDATION-AUDIT - Research

**Researched:** 2026-07-09
**Domain:** Lineage baseline capture + curator freeze + cross-repo commit pin (GSD/planning + kais-hermes-skills SKILL.md inventory + agent.yaml lineage reconciliation)
**Confidence:** HIGH (all claims verified against live filesystem + codebase grep + v13.0 milestone audit; 3 critical discrepancies flagged for operator resolution)

## Summary

Phase 70 is a **read-only enumeration + freeze + checklist** phase — zero code changes, zero SKILL.md edits. Its job is to capture the pre-v14.0 lineage baseline so that Phase 75 (LINEAGE-BUMP) is deterministic and Phase 76 (VALIDATE) can assert `agent.yaml.source_sha == sha256(SKILL.md)` against a known anchor. The research surfaced **three critical discrepancies** between the roadmap's assumptions and the actual repo state that the planner MUST resolve before writing tasks — they change the scope of "6 affected agents" and reveal that lineage drift has ALREADY occurred between v13.0 P62 transform (2026-07-07/08) and today (2026-07-09).

**Primary recommendation:** The planner should treat the roadmap's "6 agents" list as a SKILL.md edit-list (correct), NOT an agent.yaml bump-list (incorrect — only 3 of the 6 have agent YAMLs today). The inventory must capture both the current SKILL.md hash AND the current agent.yaml `lineage.skill_sha256` for every name, so Phase 75 can distinguish "bump needed because SKILL.md changed in v14.0" from "drift already existed pre-v14.0". The curator freeze has two independent surfaces (skill curation + agent.yaml transform) that must both be addressed.

### Three Critical Discrepancies (read before planning)

1. **Terminology mismatch:** The roadmap/REQUIREMENTS say `source_sha` / `transform_rule_id` / `transform_timestamp`. The actual agent YAML schema (verified in `cinematographer.agent.yaml`, `editor.agent.yaml`, `audio_pipeline.agent.yaml`, `visual_executor.agent.yaml`, `prompt_injector.agent.yaml`) uses `lineage.skill_sha256` / `lineage.transform_date` / `lineage.transform_notes`. There is NO field named `source_sha`, `transform_rule_id`, or `transform_timestamp` anywhere in the codebase. The Phase 76 assertion `agent.yaml.source_sha == sha256(SKILL.md)` must be rewritten to `agent.yaml.lineage.skill_sha256 == sha256(SKILL.md)`.

2. **Only 3 of the 6 named SKILL.md files have agent YAMLs.** `cinematographer`, `editor`, `audio_pipeline` have agent YAMLs at `~/.hermes/agents/`. `drawer`, `kais-movie-pipeline`, `kais-jimeng-cli` do NOT — they are skills only (no native expert agent). `drawer` was merged into `visual_executor` in Phase 14 (its SKILL.md is a 654-byte DEPRECATED stub). The "6 affected agents" in the roadmap conflates SKILL.md edit-scope (6 files, correct) with agent.yaml bump-scope (3 existing + potentially visual_executor as drawer's successor = 3-4 agents, NOT 6). The planner must decide whether v14.0 creates new agent YAMLs for the 3 missing ones or treats them as skill-only edits with no lineage bump.

3. **Lineage drift has ALREADY occurred.** As of 2026-07-09, `cinematographer` agent.yaml records `skill_sha256=b4bcc9c6...` but the current SKILL.md hashes to `ebe9d3fa...` (MISMATCH). `audio_pipeline` agent.yaml records `fe59f7fa...` but current SKILL.md hashes to `e0470105...` (MISMATCH). `editor` matches (`bd5bf4a1...`). This means kais-hermes-skills SKILL.md files were edited AFTER the v13.0 P62 transform (2026-07-07) without re-bumping the agent YAMLs — exactly the PITFALL X-1 cascade the freeze is meant to prevent. Phase 70's inventory MUST capture this pre-existing drift so Phase 75 knows the delta is "v14.0 edits + pre-existing drift", not purely v14.0.

<user_constraints>
## User Constraints (from CONTEXT.md)

No `70-CONTEXT.md` exists for this phase (roadmap was just created 2026-07-09; no `/gsd:discuss-phase` ran). Constraints are inherited from:

### Locked Decisions (from ROADMAP.md + REQUIREMENTS.md — treated as locked)
- XCUT-01 is the sole requirement: "Phase 0 Lineage Impact Assessment enumerates every SKILL.md to be touched with current `source_sha` BEFORE any edits land; curator `--live` mode is frozen for milestone duration"
- Cross-repo topology: plan → `hermes-agent/.planning/`; code → `kais-hermes-skills/`
- SKILL.md L1-L6 read-only invariant exception破例 authorized per PROJECT.md for v14.0 (lineage regeneration mandatory per XCUT-03 in Phase 75)
- Lineage bump scope = 6 agents per roadmap (cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli) — **RESEARCH DISPUTES THIS: only 3 have agent YAMLs today; see Discrepancy #2**
- Phase 76 strictly LAST (mirror v10.0 P51 / v11.0 P56 / v12.0 P61 / v13.0 P69 pattern)

### Claude's Discretion
- Inventory file format (JSON vs YAML vs Markdown) — research recommends Markdown-with-embedded-JSON-block (see Architecture Patterns)
- Freeze mechanism (env var vs sentinel file vs STATE.md flag) — research recommends config flag (see Code Examples)
- Audit checklist document structure — research recommends 6-row table (see Validation Architecture)

### Deferred Ideas (OUT OF SCOPE)
- XCUT-05 (full 15-agent lineage bump automation) — deferred to v15+
- INFRA-04 async concurrency lift — deferred to v15+ (NOT lifted in v14.0)
- EVAL-06 dry-run-first change — the dry-run-first default STAYS; only the `--live` opt-in is frozen for v14.0
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| XCUT-01 | Phase 0 Lineage Impact Assessment enumerates every SKILL.md to be touched with current `source_sha` BEFORE any edits land; curator `--live` mode is frozen for milestone duration (per PITFALL X-1, X-4) | **Fully supported.** Research verified: (a) the 6 target SKILL.md files exist at known paths, (b) the canonical hash is `sha256(LF-normalized UTF-8 SKILL.md bytes)` per `scripts/transform_skill_to_agent.py:232`, (c) the curator `--live` flag is wired at `hermes_cli/curator.py:1459-1482` (`hermes curator evolve --live`) and delegates to `agent/curator.py:2093 run_curator_review(dry_run=False)`, (d) a config-flag freeze via `curator.enabled: false` + `curator.consolidate: false` is the safest restoration-across-sessions mechanism. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Lineage baseline inventory (SKILL.md hashes) | Planning artifacts (`.planning/`) | kais-hermes-skills repo (read-only source) | Inventory is a GSD planning doc consumed by Phase 75/76; SKILL.md files are read-only inputs from the cross-repo |
| Agent YAML lineage capture | `~/.hermes/agents/` (read-only enumeration) | Planning artifacts | Agent YAMLs are the runtime registry; their `lineage.skill_sha256` is the post-transform provenance record |
| Curator freeze enforcement | Runtime config (`~/.hermes/config.yaml`) | STATE.md (documentation of freeze) | Config is loaded by `agent/curator.py:_load_config()` at every curator call; STATE.md records the freeze for session-continuity but does NOT itself enforce it |
| Cross-repo commit pin | STATE.md (recorded field) | Git (the actual commits) | Pin is a documentation anchor in STATE.md that Phase 76 reads to verify cross-repo coordination |
| Audit checklist drafting | Planning artifacts (`.planning/phases/70-*/`) | Phase 76 VALIDATE (consumer) | Checklist is authored in Phase 70 and consumed/verified in Phase 76 |

## Standard Stack

No external packages are installed in this phase — it is pure documentation + read-only enumeration. The tools used are already in the repo.

### Core (already pinned, no install)
| Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `hashlib` | 3.13 | Compute `sha256(LF-normalized UTF-8 SKILL.md bytes)` | Matches `scripts/transform_skill_to_agent.py:232` canonical algorithm exactly |
| `PyYAML` | 6.0.3 | Parse agent.yaml frontmatter + SKILL.md YAML blocks | Already the repo's YAML parser (`[project]` deps) |
| Git CLI | system | Capture cross-repo baseline commit SHAs | Both repos are git-tracked |

### Supporting
| Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `scripts/transform_skill_to_agent.py` | existing | Reference for canonical hash algorithm + field mapping | Read-only reference for how Phase 75 will re-bump; do NOT invoke in Phase 70 |
| `agent/curator.py` | existing | Reference for freeze mechanism | Read-only reference for where `curator.enabled` is checked |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual `hashlib` computation | `scripts/transform_skill_to_agent.py --dry-run` | The script exists but is operator-invoked one-shot and writes YAMLs; for read-only inventory a 6-line Python snippet is safer (no side-effect risk) |
| Config flag for freeze | Sentinel file `~/.hermes/curator.FREEZE` | Sentinel is atomic but not discoverable via `hermes curator status`; config flag IS visible in status output |
| STATE.md for freeze | Config flag | STATE.md is documentation-only (parsed by humans + GSD); no code reads `.planning/STATE.md` at runtime to gate curator. Config flag is code-enforced. |

**Installation:** None. Zero new packages.

**Version verification:** N/A (no installs).

## Package Legitimacy Audit

> This phase installs zero external packages. Audit skipped — no packages to verify.

## Architecture Patterns

### System Architecture Diagram

```text
Phase 70 data flow (all read-only — zero writes outside .planning/):

  kais-hermes-skills repo                ~/.hermes/agents/               ~/.hermes/config.yaml
  (read-only source)                     (read-only enumeration)         (read + 1 write: freeze flag)
  ┌──────────────────────────┐           ┌────────────────────┐          ┌─────────────────────┐
  │ skills/movie-experts/    │           │ *.agent.yaml       │          │ curator:            │
  │   cinematographer/SKILL  │           │   lineage:         │          │   enabled: true→false│
  │   editor/SKILL           │           │     skill_sha256   │          │   consolidate: false│
  │   audio_pipeline/SKILL   │           │     transform_date │          └──────────┬──────────┘
  │   drawer/SKILL (DEPRECATED)│         │     transform_notes│                     │
  │ kais-movie-pipeline/SKILL│           │   expert_id        │                     │ freeze enforced
  │ kais-creative/           │           │   related_agents   │                     │ by agent/curator.py
  │   kais-jimeng-cli/SKILL  │           └─────────┬──────────┘                     │ :141 is_enabled()
  └──────────┬───────────────┘                     │                                │
             │                                     │                                │
             ▼                                     ▼                                ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────┐
  │  Phase 70 enumeration script (Python stdlib hashlib + yaml.safe_load)                │
  │  For each of 6 SKILL.md: sha256(LF-normalized UTF-8) → compare to agent.yaml hash    │
  └──────────────────────────────┬───────────────────────────────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────┐
  │  .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md                        │
  │  (Markdown table with embedded JSON block for Phase 76 machine-readable assertions)  │
  │                                                                                      │
  │  + STATE.md update: v14.0.freeze.curator=true + cross_repo_pins={hermes:SHA, kais:SHA│
  │  + 70-VALIDATE-CHECKLIST.md (6 rows for Phase 76)                                    │
  └──────────────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
.planning/phases/70-foundation-audit/
├── 70-RESEARCH.md              # this file
├── 70-01-PLAN.md               # planner emits (inventory + freeze + checklist)
├── 70-LINEAGE-INVENTORY.md     # the actual baseline capture (deliverable)
├── 70-VALIDATE-CHECKLIST.md    # Phase 76 audit checklist (deliverable)
└── 70-01-SUMMARY.md            # post-execution summary
```

### Pattern 1: Lineage Inventory File Format (Markdown + embedded JSON)
**What:** A single file that is BOTH human-readable (operator can eyeball) AND machine-parseable (Phase 76 can grep/parse).
**When to use:** When the downstream consumer (Phase 76) needs to run assertions but the operator also needs to read it.
**Example:**
```markdown
# v14.0 Lineage Impact Inventory — Phase 70 Baseline

**Captured:** 2026-07-09 (before any v14.0 SKILL.md edit)
**Cross-repo pins:** hermes-agent=`<sha>` kais-hermes-skills=`d9620369e48eec51c31ee72ac8827c288eaccf71`

## SKILL.md baseline (6 files)

| skill_id | SKILL.md path | sha256 (LF-norm UTF-8) | bytes | agent.yaml exists? | agent.yaml lineage.skill_sha256 | drift? |
|----------|---------------|------------------------|-------|--------------------|---------------------------------|--------|
| cinematographer | skills/movie-experts/cinematographer/SKILL.md | `ebe9d3fa...` | 40780 | YES | `b4bcc9c6...` (2026-07-07) | **YES (pre-existing)** |
| editor | skills/movie-experts/editor/SKILL.md | `bd5bf4a1...` | 30364 | YES | `bd5bf4a1...` (2026-07-07) | no |
| audio_pipeline | skills/movie-experts/audio_pipeline/SKILL.md | `e0470105...` | 72251 | YES | `fe59f7fa...` (2026-07-07) | **YES (pre-existing)** |
| drawer | skills/movie-experts/drawer/SKILL.md | `2c21f234...` | 654 | NO (merged into visual_executor) | n/a | n/a |
| kais-movie-pipeline | skills/kais-movie-pipeline/SKILL.md | `bf8b7f5a...` | 111743 | NO | n/a | n/a |
| kais-jimeng-cli | skills/kais-creative/kais-jimeng-cli/SKILL.md | `3a9576a6...` | 17098 | NO | n/a | n/a |

<!-- MACHINE-READABLE BLOCK (Phase 76 parses this) -->
```json
{
  "captured_at": "2026-07-09T00:00:00Z",
  "cross_repo_pins": {
    "hermes-agent": "846a8d7efe3428109ec8f4dc2a3f14bbcb2f4be1",
    "kais-hermes-skills": "d9620369e48eec51c31ee72ac8827c288eaccf71"
  },
  "skills": [
    {"skill_id": "cinematographer", "sha256": "ebe9d3fa8e6b4987d6db2cb6a96bdd407ed526bfe8ce27bb31f8bf41ae5b535b", "agent_yaml": "cinematographer.agent.yaml", "agent_skill_sha256": "b4bcc9c69163899d2a3d069c54d8a2a6a8d651a4fe76c256a397ec0cdc875244", "drift": true},
    ...
  ]
}
```
```

### Pattern 2: Curator Freeze via Config Flag (safest restoration mechanism)
**What:** Set `curator.enabled: false` in `~/.hermes/config.yaml` for v14.0 duration.
**When to use:** When the freeze must survive process restarts AND be discoverable via `hermes curator status`.
**Why over alternatives:**
- Env var `HERMES_CURATOR_FREEZE=1`: NOT restoration-safe — a new shell session loses it. Curator runs as a background daemon invoked by gateway/cron; env vars don't propagate reliably.
- Sentinel file `~/.hermes/curator.FREEZE`: Atomic and restart-safe, but NOT discoverable — `hermes curator status` doesn't check for sentinel files. Operator might forget it exists.
- **Config flag `curator.enabled: false`**: Loaded by `agent/curator.py:_load_config()` (line 125-138) on EVERY curator call. `is_enabled()` (line 141-144) returns `False`. `run_curator_review` is gated by `is_enabled()` at the CLI entry (`hermes_cli/curator.py:189`). Survives restarts (config.yaml is persistent). Visible in `hermes curator status` output. **This is the canonical freeze mechanism.**

**Example freeze application:**
```yaml
# ~/.hermes/config.yaml (operator-owned, persistent across sessions)
curator:
  enabled: false        # FROZEN for v14.0 per XCUT-01 (Phase 70); release post-Phase-75
  consolidate: false    # defense-in-depth: even if enabled flips, no LLM writes
```

**Example freeze release (Phase 75 final action):**
```bash
# Phase 75 releases the freeze AFTER lineage bump completes
# Operator edits ~/.hermes/config.yaml:
#   curator.enabled: true   (flip back)
# Then: hermes curator status  (verify ENABLED)
```

### Pattern 3: STATE.md Freeze Documentation (session-continuity, NOT enforcement)
**What:** Record the freeze in `.planning/STATE.md` so a future Claude session reads it on boot.
**When to use:** As a SECONDARY signal — the config flag is the real enforcement; STATE.md is the human/AI-readable record.
**Why:** STATE.md is NOT parsed by runtime code (verified: `grep -rn "STATE.md" agent/ hermes_cli/` returns zero hits in runtime paths — only `.planning/` tooling reads it). But GSD session-continuity reads STATE.md first. So a `v14.0.freeze` block in STATE.md ensures the next `/gsd:plan-phase` session knows the freeze is active.
**Example STATE.md addition:**
```markdown
## v14.0 Freeze Flags (active — set by Phase 70, released by Phase 75)

| flag | value | set_by | released_by | enforcement |
|------|-------|--------|-------------|-------------|
| curator.enabled | false | Phase 70 | Phase 75 (post-bump) | `~/.hermes/config.yaml` (code-enforced via `agent/curator.py:is_enabled()`) |
| curator.consolidate | false | Phase 70 | Phase 75 (post-bump) | `~/.hermes/config.yaml` (defense-in-depth) |
| cross_repo_pin.hermes-agent | `846a8d7e...` | Phase 70 | Phase 76 (assertion) | STATE.md record (documentation) |
| cross_repo_pin.kais-hermes-skills | `d9620369...` | Phase 70 | Phase 76 (assertion) | STATE.md record (documentation) |
```

### Anti-Patterns to Avoid
- **Capturing only the SKILL.md hash without the agent.yaml hash:** Phase 75 won't be able to distinguish v14.0-introduced drift from pre-existing drift. The inventory MUST have both columns.
- **Relying on STATE.md alone for the freeze:** STATE.md is documentation, not code-enforced. A stray `hermes curator run --consolidate` from another session would bypass it. Use config flag as primary, STATE.md as secondary.
- **Freezing via env var:** Curator runs as a gateway-spawned background daemon (per MEMORY.md `hermes-gateway-systemd.md`); env vars set in one shell don't propagate to the systemd-managed gateway process. Config flag is the only restart-safe mechanism.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA-256 of SKILL.md | Custom hash with different normalization | `scripts/transform_skill_to_agent.py:_compute_skill_sha256` algorithm (LF-normalize → UTF-8 encode → sha256) | Phase 75 will use this exact algorithm; any other normalization produces a different hash and the assertion fails |
| Curator freeze detection | New sentinel file or env var | `~/.hermes/config.yaml` `curator.enabled: false` | Already loaded by `agent/curator.py:_load_config()`; already visible in `hermes curator status`; restart-safe |
| Agent YAML enumeration | Walk `~/.hermes/agents/` manually with custom parser | `ls ~/.hermes/agents/*.agent.yaml` + `yaml.safe_load` | 21 files exist; the filename-stem invariant (agent name == filename without `.agent.yaml`) is load-bearing |

**Key insight:** Every mechanism Phase 70 needs already exists in the codebase. The phase is documentation + enumeration, NOT new tooling.

## Runtime State Inventory

> Phase 70 is NOT a rename/refactor/migration, but it DOES enumerate runtime state as its primary deliverable. Including the inventory here for completeness.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `~/.hermes/agents/*.agent.yaml` (21 files); each has `lineage.skill_sha256` field | **CAPTURE** current values for the 3 target agents (cinematographer, editor, audio_pipeline) + note the 3 missing (drawer→visual_executor, kais-movie-pipeline→none, kais-jimeng-cli→none) |
| Live service config | `~/.hermes/config.yaml` has `curator:` block (currently `enabled: true`, `consolidate: false` per default) | **WRITE** `enabled: false` for v14.0 freeze (Phase 70's only write to a runtime file) |
| OS-registered state | `hermes-gateway.service` (systemd user unit) runs the gateway which may invoke curator | No change needed — config flag is read live by curator; gateway restart NOT required (per MEMORY.md `hermes-gateway-systemd.md` + `feedback-venv-repair-restart-gateway.md` the gateway reads config at curator-call-time, not boot-time) |
| Secrets/env vars | None touched | n/a |
| Build artifacts | kais-hermes-skills repo has uncommitted changes (7 modified + several untracked per `git status`) | **CAPTURE** the HEAD SHA (`d9620369...`) as the baseline pin; uncommitted changes are pre-v14.0 operator work, NOT Phase 70's concern (Phase 70 is read-only on kais-hermes-skills) |

**The canonical question:** *After Phase 70 completes, what runtime systems still have state that Phase 75/76 needs to know about?*
- `~/.hermes/config.yaml` has `curator.enabled: false` (Phase 75 must flip back to `true`)
- `~/.hermes/agents/{cinematographer,editor,audio_pipeline}.agent.yaml` have the pre-v14.0 `lineage.skill_sha256` values (Phase 75 overwrites these)
- STATE.md records the cross-repo commit pins (Phase 76 asserts the pins still resolve)
- kais-hermes-skills HEAD sha `d9620369...` is the pre-v14.0 baseline (Phase 76 verifies post-v14.0 commits are descendants)

## Common Pitfalls

### Pitfall 1: Terminology Drift (source_sha vs skill_sha256)
**What goes wrong:** The roadmap/REQUIREMENTS use `source_sha` / `transform_rule_id` / `transform_timestamp`, but the actual agent YAML schema uses `lineage.skill_sha256` / `lineage.transform_date` / `lineage.transform_notes`. If Phase 75 or Phase 76 grep for `source_sha`, it finds nothing and the assertion silently passes (empty set).
**Why it happens:** The roadmap was authored from research SUMMARY which used generalized terminology; the actual schema field names come from `agents-schema.yaml` field #7 (v10.0 Phase 45) and were not cross-checked against the roadmap prose.
**How to avoid:** The inventory file and the Phase 76 checklist MUST use the canonical field name `lineage.skill_sha256`. The planner should encode the field name verbatim in every task action.
**Warning signs:** Any task that references `source_sha` without a parenthetical `(canonical: lineage.skill_sha256)` is suspect.

### Pitfall 2: Assuming "6 agents" Means 6 Agent YAMLs
**What goes wrong:** The roadmap says "6 affected agents (cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli)". If the planner creates 6 lineage-bump tasks, 3 of them will fail (no agent.yaml exists for drawer/kais-movie-pipeline/kais-jimeng-cli).
**Why it happens:** The roadmap conflates "SKILL.md files that will be edited" (6 — correct) with "agent YAMLs that need lineage bump" (3 today + possibly 3 new ones IF v14.0 decides to create them).
**How to avoid:** The planner must split the lineage-bump scope into: (a) 3 existing agent.yaml bumps (cinematographer, editor, audio_pipeline) + (b) 1 conditional bump (visual_executor IF its source SKILL.md is touched, since drawer is merged into it) + (c) 0-2 new agent.yaml creation decisions (kais-movie-pipeline, kais-jimeng-cli — these are orchestration/tool skills, not movie-expert agents; creating agent YAMLs for them may be out of v14.0 scope).
**Warning signs:** Any Phase 75 task that says "bump drawer.agent.yaml" or "bump kais-movie-pipeline.agent.yaml" without first creating the YAML is broken.

### Pitfall 3: Pre-Existing Lineage Drift (cinematographer + audio_pipeline)
**What goes wrong:** As of 2026-07-09, `cinematographer` and `audio_pipeline` agent.yaml `lineage.skill_sha256` values do NOT match the current SKILL.md hash. If Phase 75 only captures the post-v14.0 SKILL.md hash and asserts against the agent.yaml, it will "fix" drift it didn't introduce — making the v14.0 diff look larger than it is.
**Why it happens:** Someone edited the SKILL.md files in kais-hermes-skills between v13.0 P62 transform (2026-07-07) and now (2026-07-09) without re-running the transform. The kais-hermes-skills `git status` shows 7 modified + several untracked files — the drift source is likely those uncommitted edits.
**How to avoid:** Phase 70 inventory MUST capture BOTH the current SKILL.md hash AND the current agent.yaml lineage value. Phase 75 can then compute: `v14.0_introduced_drift = post_v14_SKILL_hash - pre_v14_SKILL_hash` (the actual v14.0 delta) separately from `total_drift = post_v14_SKILL_hash - agent_yaml_hash` (what the bump closes).
**Warning signs:** An inventory with only one hash column (either SKILL.md OR agent.yaml, not both).

### Pitfall 4: Sentinel/Env Freeze That Doesn't Survive Gateway Restart
**What goes wrong:** MEMORY.md `hermes-gateway-systemd.md` notes the gateway is systemd-managed (`Restart=always`). If the freeze is set via env var in the current shell, a gateway restart (or the daily restart cycle) loses it.
**Why it happens:** Curator is invoked by the gateway daemon, not just by manual `hermes curator run`. The gateway process inherits env from systemd, not from the operator's shell.
**How to avoid:** Use `~/.hermes/config.yaml` `curator.enabled: false` — config.yaml is a file, read fresh by `_load_config()` on every curator call, immune to process restarts.
**Warning signs:** Any freeze mechanism that requires "set this env var before starting the gateway".

### Pitfall 5: Capturing Only Committed State (Missing Uncommitted SKILL.md Edits)
**What goes wrong:** kais-hermes-skills has 7 modified + several untracked files RIGHT NOW. If the inventory captures `git show HEAD:skills/.../SKILL.md` (committed state), it misses the working-tree state that Phase 71-74 will actually edit.
**Why it happens:** `git rev-parse HEAD` gives the commit sha, but the actual file content the pipeline reads is the working-tree version.
**How to avoid:** The inventory MUST hash the working-tree file (`/data/workspace/kais-hermes-skills/skills/.../SKILL.md` as it exists on disk today), NOT the git-committed blob. The cross-repo commit pin (`d9620369...`) is a SEPARATE piece of metadata — it anchors "what commit was checked out when Phase 70 ran" for Phase 76's coordination check, but the lineage hash is against working-tree bytes.
**Warning signs:** An inventory that says `git_hash: <blob-sha>` instead of `sha256: <working-tree-hash>`.

## Code Examples

### Example 1: Canonical SHA-256 Computation (verified against transform script)
```python
# Source: scripts/transform_skill_to_agent.py:232-240 (VERIFIED via Read tool)
import hashlib
from pathlib import Path

def compute_skill_sha256(skill_md_path: str) -> str:
    """SHA-256 of LF-normalized SKILL.md content (canonical algorithm)."""
    content = Path(skill_md_path).read_text(encoding="utf-8")
    lf_content = content.replace("\r\n", "\n")  # CRLF → LF normalization
    return hashlib.sha256(lf_content.encode("utf-8")).hexdigest()

# Verified outputs for the 6 targets (computed 2026-07-09):
# cinematographer  → ebe9d3fa8e6b4987d6db2cb6a96bdd407ed526bfe8ce27bb31f8bf41ae5b535b
# editor           → bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77
# audio_pipeline   → e047010520e3cc4afea5bb0fe96dc1e0ff7826708ae421339305090ce0aeaa9f
# drawer           → 2c21f234380ca3fa1f918f733e3cb967d558cdc23b3cca2aedfcb6337682f1eb  (DEPRECATED stub)
# kais-movie-pipeline   → bf8b7f5a48624dea563b8e37e46adb793dba0006090b334583d757ff7879b7ea
# kais-jimeng-cli       → 3a9576a66a9567d64074fec278dceae97243f03e2607a902e2a5c4f6b6f4681b
```

### Example 2: Reading Agent YAML Lineage (verified against live files)
```python
# Source: agent.yaml schema verified via Read tool on 5 files (2026-07-09)
import yaml
from pathlib import Path

def read_agent_lineage(agent_name: str) -> dict:
    """Read lineage block from ~/.hermes/agents/<name>.agent.yaml."""
    path = Path.home() / ".hermes" / "agents" / f"{agent_name}.agent.yaml"
    if not path.exists():
        return {"exists": False}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    lin = data.get("lineage", {})
    return {
        "exists": True,
        "skill_sha256": lin.get("skill_sha256"),     # canonical field name
        "transform_date": lin.get("transform_date"),  # NOT "transform_timestamp"
        "transform_notes": lin.get("transform_notes"),
        "derived_from_skill_id": lin.get("derived_from_skill_id"),
    }

# Verified: cinematographer.skill_sha256 = b4bcc9c6... (MISMATCHES current SKILL.md ebe9d3fa...)
# Verified: editor.skill_sha256 = bd5bf4a1... (MATCHES current SKILL.md bd5bf4a1...)
# Verified: drawer/kais-movie-pipeline/kais-jimeng-cli → exists=False (NO agent.yaml)
```

### Example 3: Curator Freeze Application (config flag — verified mechanism)
```bash
# Source: agent/curator.py:125-144 (_load_config + is_enabled) — VERIFIED via Read tool
# Step 1: Read current config
python3 -c "import yaml; print(yaml.safe_load(open('$HOME/.hermes/config.yaml')))['curator']]"

# Step 2: Apply freeze (operator edits config.yaml)
# In ~/.hermes/config.yaml, under curator: block:
#   enabled: false        # was true (default)
#   consolidate: false    # was already false (default)

# Step 3: Verify freeze took effect
hermes curator status
# Expected output: "curator: DISABLED" (was "ENABLED")

# Step 4 (Phase 75 release): flip enabled back to true
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `run_curator_review(dry_run=False)` default (live writes) | `dry_run=True` default (EVAL-06 dry-run-first invariant) | Phase 55-03 (v11.0 P55) | Curator cannot accidentally trigger live writes; `--live` is explicit opt-in via `hermes curator evolve --live` |
| `curator.enabled` not in config | `curator.enabled` + `curator.consolidate` config flags | Phase 32 (v6.0) | Freeze mechanism exists and is restart-safe |
| Agent YAML lineage via manual transform | `scripts/transform_skill_to_agent.py` one-shot CLI | Phase 49 (v10.0 design) + Phase 62 (v13.0 execution) | Canonical transform procedure; Phase 75 re-runs this |
| `source_sha` terminology (roadmap prose) | `lineage.skill_sha256` (actual schema field) | Roadmap authored 2026-07-09 used generalized term; schema field name stable since Phase 45 (v10.0) | Planner + Phase 75 + Phase 76 MUST use `lineage.skill_sha256`, not `source_sha` |

**Deprecated/outdated:**
- `drawer` expert_id: DEPRECATED, merged into `visual_executor` (Phase 14 MERGE-01). Its SKILL.md is a 654-byte stub. Any lineage bump for "drawer" must target `visual_executor.agent.yaml` instead.
- `scene_builder` expert_id: absorbed into `cinematographer` (Phase 17). Legacy callers route via FOUND-08 expert_id map.
- `performer` / `composer` expert_ids: renamed to `character_designer` / `audio_pipeline` (CONTEXT.md decision #1, v3.0). Legacy names canonicalized via `LEGACY_NAME_MAP` in transform script.

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The 3 missing agent YAMLs (drawer, kais-movie-pipeline, kais-jimeng-cli) should NOT be created in v14.0 — they are skills, not native expert agents, and v14.0 scope is "bump existing" not "create new agents" | Discrepancy #2 + Pitfall 2 | If operator wants new agent YAMLs for these, Phase 75 scope expands. LOW risk — TRANS-04 explicitly forbids new expert_id per FOUND-08. |
| A2 | `curator.enabled: false` is sufficient to freeze ALL curator write paths (no separate `--live` escape hatch bypasses it) | Pattern 2 | If `hermes curator evolve --live` bypasses `is_enabled()`, freeze is incomplete. MEDIUM risk — code review of `hermes_cli/curator.py:274` shows `_cmd_evolve` checks `is_enabled()` at line 271, so this is VERIFIED not assumed. |
| A3 | The pre-existing lineage drift (cinematographer, audio_pipeline) is acceptable to carry into Phase 75 (Phase 75 will close it as a side effect of re-bumping) | Pitfall 3 | If operator wants the drift fixed BEFORE v14.0 starts, Phase 70 needs an extra task. LOW risk — drift is advisory per v10.0 §2.18 additive invariant (operator decides whether to re-transform). |
| A4 | kais-hermes-skills HEAD sha `d9620369...` is the correct baseline pin (uncommitted working-tree changes are pre-v14.0 operator work, not Phase 70's concern) | Runtime State Inventory | If the uncommitted changes are actually v14.0 work-in-progress, the pin is stale. LOW risk — the changes are to pipeline scripts (`canvas_sync.py`, `p09_shot_breakdown.py`), NOT to the 6 target SKILL.md files. |

**Note:** A2 was downgraded from ASSUMED to VERIFIED during research (confirmed via code read of `hermes_cli/curator.py:271`). Kept in table for traceability.

## Open Questions

1. **Should v14.0 create agent YAMLs for kais-movie-pipeline and kais-jimeng-cli?**
   - What we know: Both are skills-only today (no `~/.hermes/agents/*.agent.yaml`). They are orchestration/tool skills, not movie-expert agents. The v10.0-v13.0 arc created agent YAMLs only for the 15 movie-experts (FOUND-08 frozen set).
   - What's unclear: Does the XCUT-03 "lineage bump on 6 affected agents" requirement imply creating new agent YAMLs, or only bumping the 3 existing ones?
   - Recommendation: **Ask operator in discuss-phase or default to "bump 3 existing only"** (safer, preserves FOUND-08). The roadmap's "6 agents" is best interpreted as "6 SKILL.md files" not "6 agent.yaml bumps". TRANS-04 explicitly forbids new expert_id per FOUND-08, which supports this interpretation.

2. **Is the pre-existing lineage drift (cinematographer, audio_pipeline) intentional or a bug to fix?**
   - What we know: Both agent.yaml `skill_sha256` values mismatch the current SKILL.md hash. The drift was introduced between 2026-07-07 (P62 transform) and 2026-07-09 (today). kais-hermes-skills has 7 modified files in working tree.
   - What's unclear: Were the SKILL.md edits intentional post-v13.0 improvements that someone forgot to re-bump, or accidental?
   - Recommendation: **Capture in inventory as "pre-existing drift" and let Phase 75 close it.** Do NOT fix mid-Phase-70 (that would be a SKILL.md edit, violating the read-only enumeration scope). Flag in the inventory's drift column so the operator can decide.

3. **Does the gateway need a restart after setting `curator.enabled: false`?**
   - What we know: `agent/curator.py:_load_config()` reads config fresh on every call. But MEMORY.md `feedback-venv-repair-restart-gateway.md` warns that gateway processes cache lazy globals.
   - What's unclear: Whether the gateway's in-memory curator state includes a cached `enabled` flag.
   - Recommendation: **No restart needed** — `_load_config()` is called inside `is_enabled()`, `get_consolidate()`, etc. on every invocation (verified line 125-144). The gateway reads config at curator-call-time, not boot-time. But document this in the freeze task so the operator can verify via `hermes curator status`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | hashlib + yaml computation | ✓ | 3.13 (per `.venv`) | — |
| `PyYAML` | agent.yaml parsing | ✓ | 6.0.3 (pinned) | — |
| Git CLI | cross-repo commit pin capture | ✓ | system | — |
| kais-hermes-skills repo at `/data/workspace/kais-hermes-skills` | SKILL.md enumeration | ✓ | HEAD `d9620369...` | — |
| `~/.hermes/agents/` directory | agent.yaml enumeration | ✓ | 21 files present | — |
| `~/.hermes/config.yaml` | curator freeze application | ✓ | present (operator-owned) | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | N/A — Phase 70 is documentation-only; no unit tests (no code written) |
| Config file | n/a |
| Quick run command | `python3 scripts/verify_lineage_inventory.py` (Wave 0 — to be created by planner IF a programmatic checker is desired; otherwise manual operator review) |
| Full suite command | Manual operator verification: `cat .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` + `hermes curator status` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| XCUT-01a | Lineage Impact Inventory file exists at `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` | smoke | `test -f .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md && echo OK` | ❌ Wave 0 (created by phase execution) |
| XCUT-01b | Inventory lists all 6 target SKILL.md files with sha256 | smoke | `grep -c "skills/.*SKILL.md" .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` → expects 6 | ❌ Wave 0 |
| XCUT-01c | Inventory includes cross-repo commit pins for both repos | smoke | `grep "hermes-agent\|kais-hermes-skills" .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md \| grep -c sha` → expects >=2 | ❌ Wave 0 |
| XCUT-01d | Curator is disabled (freeze active) | smoke | `hermes curator status \| grep -q DISABLED` | ❌ Wave 0 (run after freeze task) |
| XCUT-01e | STATE.md records the freeze flags | smoke | `grep -q "v14.0.freeze\|curator.enabled.*false" .planning/STATE.md` | ❌ Wave 0 |
| XCUT-01f | Phase 76 VALIDATE checklist drafted with all 6 rows | smoke | `grep -c "^|" .planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` → expects >=6 data rows | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cat .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` (human review)
- **Per wave merge:** `hermes curator status` (verify freeze) + inventory completeness check
- **Phase gate:** All 6 smoke tests green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` — the primary deliverable (covers XCUT-01a/b/c)
- [ ] `.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` — Phase 76 audit checklist (covers XCUT-01f)
- [ ] STATE.md update with v14.0 freeze block (covers XCUT-01e)
- [ ] `~/.hermes/config.yaml` curator.enabled: false (covers XCUT-01d)

*(No test framework install needed — Phase 70 writes zero code files.)*

## Security Domain

> `security_enforcement` is not set in config.json (absent = enabled per default). Including this section. However, Phase 70's security surface is minimal — it's a read-only enumeration + one config flag flip.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a — Phase 70 does not touch auth |
| V3 Session Management | no | n/a |
| V4 Access Control | yes | The `~/.hermes/config.yaml` write (curator.enabled: false) is operator-owned; no privilege escalation. The inventory reads are all operator-owned paths. |
| V5 Input Validation | yes | The inventory file paths are hardcoded (not user-supplied); no injection risk. The sha256 computation is on trusted local files. |
| V6 Cryptography | yes (minimal) | SHA-256 used for content hashing (not security-critical — lineage provenance, not auth). `hashlib.sha256` is stdlib, not hand-rolled. |

### Known Threat Patterns for Phase 70

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Curator freeze bypass (operator runs `hermes curator evolve --live --skip-canary` during v14.0) | Tampering | Document in STATE.md that freeze is active; `--skip-canary` is audit-logged (per `hermes_cli/curator.py:344-349` canary_pass=None). Phase 76 VALIDATE checks audit log for any live-tick during v14.0 window. |
| Inventory tampering (someone edits the inventory file after Phase 70 to hide drift) | Tampering | The inventory is committed to git (hermes-agent repo); any post-Phase-70 edit shows in `git diff`. Phase 76 can re-compute hashes from the pinned kais-hermes-skills commit and compare. |

## Sources

### Primary (HIGH confidence)
- **Codebase inspection (2026-07-09):** `scripts/transform_skill_to_agent.py:232-240` — canonical SHA-256 algorithm (LF-normalize → UTF-8 → sha256). Field mapping at lines 179-219. `[VERIFIED: codebase grep + Read tool]`
- **Codebase inspection:** `agent/curator.py:88-118` (`load_state`, `save_state`, `is_paused`), `:125-204` (`_load_config`, `is_enabled`, `get_consolidate`), `:2093-2161` (`run_curator_review` with dry_run=True default). `[VERIFIED: Read tool full function bodies]`
- **Codebase inspection:** `hermes_cli/curator.py:187-247` (`_cmd_run`), `:250-428` (`_cmd_evolve` with `--live` flag wiring), `:1419-1682` (`register_cli` argparse). `[VERIFIED: Read tool full module]`
- **Live filesystem:** `~/.hermes/agents/*.agent.yaml` — 21 files enumerated; 5 read in full (cinematographer, editor, audio_pipeline, visual_executor, prompt_injector). Lineage fields confirmed: `lineage.skill_sha256` + `lineage.transform_date` + `lineage.transform_notes` (NOT `source_sha` / `transform_rule_id` / `transform_timestamp`). `[VERIFIED: Read tool + yaml.safe_load]`
- **Live filesystem:** `/data/workspace/kais-hermes-skills/` — repo confirmed at this path; HEAD `d9620369...`; remote `https://github.com/kaiger666888/kais-hermes-skills.git`; 6 target SKILL.md files located and hashed. `[VERIFIED: git log + git remote + hashlib computation]`
- **`.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` §2.18 + §6.1** — FOUND-08 preservation rules + 5-step transform procedure (read → sha256 → generate → write → record lineage). `[CITED: in-repo design doc]`
- **`.planning/research/v14-4track-upgrade/PITFALLS.md`** — X-1 (lineage cascade), X-2 (META-RULE), X-4 (curator drift), X-5 (INFRA-04), INFRA-04/EVAL-06 definitions. `[CITED: in-repo research]`
- **`.planning/milestones/v13.0-MILESTONE-AUDIT.md`** — `found08_preserved: n/a` for v13.0 (read-only invariant L1-L6 preserved); 15-expert set frozen; P62 transform flow is what Phase 75 re-runs. `[CITED: in-repo audit]`

### Secondary (MEDIUM confidence)
- **`hermes_cli/curator.py:271` (`_cmd_evolve` checks `is_enabled()`)** — confirms config flag freeze blocks even the `--live` path. `[VERIFIED: Read tool line 271]`
- **MEMORY.md notes** — `hermes-gateway-systemd.md` (gateway is systemd-managed), `feedback-venv-repair-restart-gateway.md` (gateway caches lazy globals), `feedback-glm-overload-reduce-concurrency.md` (INFRA-04 MAX_CONCURRENT_GL=1). `[CITED: auto-memory]`

### Tertiary (LOW confidence)
- None. All findings verified against primary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no installs, stdlib + existing pinned packages only
- Architecture: HIGH — all mechanisms verified against live codebase
- Pitfalls: HIGH — 3 critical discrepancies discovered via empirical filesystem inspection (not training-data assumptions)
- Terminology correction (source_sha → lineage.skill_sha256): HIGH — verified against 5 live agent.yaml files + transform script

**Research date:** 2026-07-09
**Valid until:** 2026-08-09 (30 days; stable — lineage schema + curator mechanism are post-v13.0 stable, no imminent changes)
