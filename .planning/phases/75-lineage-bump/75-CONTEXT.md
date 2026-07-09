# Phase 75: LINEAGE-BUMP - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning
**Mode:** Auto-generated (user prefers direct plan-phase dispatch; Claude's analyzed defaults below)

<domain>
## Phase Boundary

After all v14.0 SKILL.md edits are final (Phases 71-74 complete), the affected agent YAMLs at `~/.hermes/agents/` have their lineage fields regenerated (source_sha + transform_rule_id + transform_timestamp) by re-running the v13.0 P62 transform flow, with CI assertion `agent.yaml.source_sha == sha256(SKILL.md)` passing.

**ACTUAL SCOPE (corrected from ROADMAP "6 affected agents"):** 17 SKILL.md files were touched across Phases 71-74; 15 of those have agent.yaml files requiring regeneration. The other 2 (kais-movie-pipeline, kais-jimeng-cli) are skill-only and require no agent.yaml bump.

Requirements covered: XCUT-03 (lineage bump via v13.0 P62 transform flow).

**Final action of v14.0 SKILL.md-touching phases:** Curator `--live` freeze (imposed in Phase 70) is lifted only AFTER lineage bump completes.

**Out of scope:** Source_sha assertion on the 9 untouched experts (per ROADMAP SC#2 — they get NO bump); automation for full 15-agent bump (XCUT-05 deferred); agent.yaml structural changes (lineage fields only — persona body unchanged per v13.0 P62 contract).

</domain>

<decisions>
## Implementation Decisions

### Scope Enumeration (CORRECTED from ROADMAP "6")
- **17 SKILL.md files touched in v14.0** (verified via `git diff --name-only d9620369..HEAD | grep SKILL.md$`):
  - 15 active movie-expert skills (cinematographer, editor, audio_pipeline, visual_executor, character_designer, colorist, compliance_gate, continuity_auditor, creative_source, hook_retention, prompt_injector, screenplay, script_auditor, style_genome, theory_critic)
  - 2 skill-only (kais-movie-pipeline orchestration skill, kais-jimeng-cli tool skill)
- **15 agent.yaml regenerations required** (all 15 active movie-experts have agent.yaml at `~/.hermes/agents/`)
- **2 skill-only acknowledgments** (kais-movie-pipeline, kais-jimeng-cli — NO agent.yaml to bump; documented in bump report)
- **drawer**: DEPRECATED stub merged into visual_executor (Phase 14); NO agent.yaml; NO bump

### Transform Flow Execution
- **Script:** `/data/workspace/hermes-agent/scripts/transform_skill_to_agent.py` (v13.0 P62 transform flow)
- **Source SKILL.md paths:** Read from `/data/workspace/kais-hermes-skills/skills/movie-experts/<name>/SKILL.md` (15 files)
- **Target agent.yaml paths:** Write to `~/.hermes/agents/<name>.agent.yaml` (15 files)
- **Lineage fields updated:**
  - `lineage.skill_sha256`: SHA-256 of LF-normalized UTF-8 working-tree bytes of final v14.0 SKILL.md (algorithm at `scripts/transform_skill_to_agent.py:232-240`)
  - `lineage.transform_date`: ISO date `2026-07-10`
  - `lineage.transform_notes`: Free text with `Rule IDs:` substring; must cite `v14.0 P75 lineage bump (post Phases 71-74 SKILL.md edits)` for audit traceability
- **Persona body:** UNCHANGED per v13.0 P62 contract — transform script regenerates only lineage fields; persona stays at v13.0 P62 state

### CI Assertion
- **Assertion:** `agent.yaml.source_sha == sha256(SKILL.md)` for all 15 active agent.yaml files
- **Implementation:** New bash script `.planning/phases/75-lineage-bump/75-lineage-assert.sh` that:
  - For each of 15 active experts: compute `sha256(LF-normalized UTF-8 SKILL.md working-tree bytes)`; read `lineage.skill_sha256` from agent.yaml; assert equality; exit non-zero on mismatch
  - Mirrors 70-smoke.sh pattern
- **Skipped agents (NO bump, NO assertion):** drawer (DEPRECATED), kais-movie-pipeline (skill-only), kais-jimeng-cli (skill-only), plus the ~5 active experts NOT touched in v14.0 (none — all 15 canonical active were touched)

### Curator Freeze Release
- **Current state (Phase 70 imposed):** `config.yaml curator.enabled: false`, code-enforced at `hermes_cli/curator.py:270-272`
- **Release trigger:** Set `curator.enabled: true` in `~/.hermes/config.yaml` AFTER all 15 lineage bumps complete + 75-lineage-assert.sh exits 0
- **Final action of Phase 75:** Release is the last commit of the phase; afterwards curator `--live` can run without mid-bump race risk

### Claude's Discretion
- Exact `transform_notes` text per agent.yaml (within "must cite v14.0 P75 lineage bump" requirement)
- Whether to use transform_skill_to_agent.py in batch mode (if supported) or per-agent invocation
- Report format for 75-LINEAGE-BUMP-REPORT.md (lineage coverage table)
- Test framework for verifying transform script invocation (bash smoke vs pytest unit)

</decisions>

<canonical_refs>
## Canonical Refs (Phase 75 downstream agents MUST read)

**Hermes-agent repo:**
- `.planning/ROADMAP.md` — Phase 75 section (lines 106-118)
- `.planning/REQUIREMENTS.md` — XCUT-03 (lineage bump requirement)
- `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` — P70 baseline (6 SKILL.md hashes + 3 agent.yaml lineage + cross-repo pins); Pitfall 2 confirms "6 SKILL.md files, NOT 6 agent.yaml bumps"
- `scripts/transform_skill_to_agent.py` — v13.0 P62 transform script (lines 191-197 lineage field names; lines 232-240 sha256 algorithm)
- `~/.hermes/config.yaml` — curator.enabled flag location
- `hermes_cli/curator.py:270-272` — code-enforced freeze check

**Kais-hermes-skills repo (read-only at this point):**
- `skills/movie-experts/<15 experts>/SKILL.md` — final v14.0 SKILL.md sources (read by transform script)

**Agent YAML targets (write):**
- `~/.hermes/agents/<15 experts>.agent.yaml` — lineage fields regenerated

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`scripts/transform_skill_to_agent.py`** — v13.0 P62 transform script; handles SKILL.md → agent.yaml lineage regeneration; 5-step procedure documented in v10.0 04-MIGRATION-PATH.md
- **`70-smoke.sh` pattern** — Phase 70 bash smoke script skeleton for 75-lineage-assert.sh
- **`70-LINEAGE-INVENTORY.md`** — pre-v14.0 baseline; provides delta anchor (post_v14_SKILL_sha − agent_yaml.lineage.skill_sha256)

### Established Patterns
- **Lineage field names (canonical per P70 Pitfall 1):** `lineage.skill_sha256` (NOT `source_sha`), `lineage.transform_notes` (NOT `transform_rule_id`), `lineage.transform_date` (NOT `transform_timestamp`)
- **SHA-256 algorithm (P70):** sha256 of LF-normalized UTF-8 working-tree bytes (per `scripts/transform_skill_to_agent.py:232-240`); NOT git-committed blob hash
- **Cross-repo split:** SKILL.md in kais-hermes-skills (read-only at this point); agent.yaml in hermes-agent `~/.hermes/agents/`

### Integration Points
- Transform script reads SKILL.md from `/data/workspace/kais-hermes-skills/skills/movie-experts/<name>/SKILL.md`
- Transform script writes agent.yaml to `~/.hermes/agents/<name>.agent.yaml`
- CI assertion script reads both + compares lineage.skill_sha256

</code_context>

<specifics>
## Specific Ideas

- **Batch vs per-agent invocation:** If transform_skill_to_agent.py supports batch mode (e.g., `--all-active-experts` flag), prefer it for atomicity; else per-agent invocation with per-agent commit
- **75-LINEAGE-BUMP-REPORT.md:** Required artifact for Phase 76 VALIDATE audit; must include:
  - Pre-bump baseline (P70 inventory hashes)
  - Post-bump final hashes (this phase's output)
  - Delta decomposition (v14.0-introduced drift vs pre-existing drift per P70 Pitfall 3)
  - Lineage coverage row for Phase 76 milestone audit
- **Curator freeze release:** Must be LAST action; document in SUMMARY as "final action of Phase 75 per ROADMAP SC#4"
- **Pre-existing drift closure:** P70 captured cinematographer + audio_pipeline as MISMATCH (pre-v14.0 drift); Phase 75 closes both as side effect of re-transform

</specifics>

<deferred>
## Deferred Ideas

- **XCUT-05 (full 15-agent lineage bump automation):** v14.0 bumps 15 manually; automation for ongoing bumps deferred to v15+
- **Agent.yaml persona refresh:** v13.0 P62 personas are preserved; if SKILL.md body changes warrant persona re-derivation, that's a future phase (NOT this one — lineage fields only)
- **drawer agent.yaml creation:** drawer is DEPRECATED (merged into visual_executor Phase 14); creating a new drawer.agent.yaml would violate FOUND-08 frozen expert set
- **Real-time lineage drift detection:** Post-bump monitoring for future drift; v15+ concern

</deferred>
