# v3.0 Milestone Validation Report

**Plan:** 18-01 (Phase 18 Wave 1/3 — audit-only)
**Audited:** 2026-06-17
**Scope:** VALIDATE-01 (FOUND-08 frozen-rule compliance) + VALIDATE-02 (backward-compat alias resolution) + ROADMAP §18 #1 reconciliation.
**Method:** Canonical enumeration (`find skills/movie-experts -maxdepth 2 -name 'SKILL.md' | grep -v '_eval\|_shared'`) followed by per-file frontmatter extraction + classification into 4 buckets. No SKILL.md content modified in this plan (audit-only). Any defect is surfaced for plan 18-03 to patch or document.

---

## Inventory Classification

Enumeration command (executed 2026-06-17):

```
$ find skills/movie-experts -maxdepth 2 -name 'SKILL.md' | grep -v '_eval\|_shared' | wc -l
31
```

31 SKILL.md files classified into exactly one of four buckets below. Per-file `expert_id`, `status`, `aliases`, `merged_into` / `folded_into` / `renamed_to`, `deprecated_reason`, `inheritance_targets` values were extracted from each file's YAML frontmatter (`metadata.hermes.*` nested fields included). Every file appears in exactly one bucket.

### Bucket 1 — ACTIVE (DAG pipeline-role)

Status field absent (active). Directory contains substantive content. expert_id is in the canonical 16-node set from `01-NODE-DAG.md §1.5`.

| # | Directory | expert_id | Notes |
|---|-----------|-----------|-------|
| 1 | `creative_source/` | `creative_source` | L0 root, preserved |
| 2 | `style_genome/` | `style_genome` | L1, preserved |
| 3 | `screenplay/` | `screenplay` | L1, preserved |
| 4 | `script_auditor/` | `script_auditor` | L1, preserved |
| 5 | `character_designer/` | `character_designer` | L1, preserved |
| 6 | `cinematographer/` | `cinematographer` | L2, preserved |
| 7 | `prompt_injector/` | `prompt_injector` | L2, NEW Phase 16 |
| 8 | `visual_executor/` | `visual_executor` | L3, NEW Phase 14 merge; `aliases: [drawer, animator]` |
| 9 | `audio_pipeline/` | `audio_pipeline` | L4, NEW Phase 15 merge; `aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` |
| 10 | `continuity_auditor/` | `continuity_auditor` | L3, renamed from `continuity` Phase 13; `aliases: [continuity]` |
| 11 | `editor/` | `editor` | L4, preserved |
| 12 | `colorist/` | `colorist` | L4, preserved |
| 13 | `hook_retention/` | `hook_retention` | L5, preserved |
| 14 | `compliance_gate/` | `compliance_gate` | L6, renamed from `compliance_marketing` Phase 13; `aliases: [compliance_marketing]` |
| 15 | `theory_critic/` | `theory_critic` | Vertical consultative, preserved |

**Count: 15** — not 16. See INVENTORY DEFECT VALIDATE-D1 below: `quality_gate` (the 16th canonical DAG node per `01-NODE-DAG.md §1.5`) has no corresponding `skills/movie-experts/quality_gate/` directory or SKILL.md on disk. This is a Phase 18 defect to resolve in plan 18-03 (either backfill `quality_gate/` or document explicitly that v3.0 shipped without it).

### Bucket 2 — ACTIVE (non-DAG vertical / deferred)

Status field absent (active). Valid experts that v3.0 did NOT migrate into the canonical 16-node DAG.

| # | Directory | expert_id | Notes |
|---|-----------|-----------|-------|
| 1 | `documentary_maker/` | `documentary_maker` | Phase 8 corpus-driven vertical, NOT in canonical DAG |
| 2 | `animation_studio/` | `animation_studio` | Phase 8 corpus-driven vertical, NOT in canonical DAG |
| 3 | `production/` | `production` | `skills-mapping.yaml` `not_in_new_dag`: `disposition: deferred` (FUTURE-09); v3.0 did NOT deprecate |

**Count: 3.**

### Bucket 3 — DEPRECATED (Phase 17)

`status: deprecated` + `metadata.hermes.deprecated: true` + `metadata.hermes.inheritance_targets: [...]` + `metadata.hermes.deprecated_reason:` present. Body content preserved intact (FOUND-08). Per REQUIREMENTS DEPRECATE-01/02/03.

| # | Directory | expert_id | status | inheritance_targets |
|---|-----------|-----------|--------|---------------------|
| 1 | `performer/` | `performer` | `deprecated` | `[character_designer, screenplay]` |
| 2 | `scene_builder/` | `scene_builder` | `deprecated` | `[cinematographer, style_genome]` |
| 3 | `storyboard_designer/` | `storyboard_designer` | `deprecated` | `[cinematographer]` |

**Count: 3.**

### Bucket 4 — REDIRECT STUB (preserves old expert_id per FOUND-08)

`status: renamed` OR `status: merged_into` OR `status: folded_into`. Body is a redirect notice pointing at the current SKILL.md. Old expert_id preserved per FOUND-08.

| # | Directory | expert_id | status | target | aliases |
|---|-----------|-----------|--------|--------|---------|
| 1 | `continuity/` | `continuity` | `renamed` | `continuity_auditor` | `[continuity_auditor]` |
| 2 | `compliance_marketing/` | `compliance_marketing` | `renamed` | `compliance_gate` | `[compliance_gate]` |
| 3 | `drawer/` | `drawer` | `merged_into` | `visual_executor` | `[visual_executor]` |
| 4 | `animator/` | `animator` | `merged_into` | `visual_executor` | `[visual_executor]` |
| 5 | `voicer/` | `voicer` | `merged_into` | `audio_pipeline` | `[audio_pipeline]` |
| 6 | `lip_sync/` | `lip_sync` | `merged_into` | `audio_pipeline` | `[audio_pipeline]` |
| 7 | `composer/` | `composer` | `merged_into` | `audio_pipeline` | `[audio_pipeline]` |
| 8 | `foley/` | `foley` | `merged_into` | `audio_pipeline` | `[audio_pipeline]` |
| 9 | `mixer/` | `mixer` | `merged_into` | `audio_pipeline` | `[audio_pipeline]` |
| 10 | `spatial_audio/` | `spatial_audio` | `folded_into` | `audio_pipeline` | `[audio_pipeline]` |

**Count: 10** — not 5. The ROADMAP §18 #1 figure of "5 aliases" undercounts: every old expert_id must have its own redirect stub directory + SKILL.md per FOUND-08 (1 dir per alias), but a single successor expert may carry multiple aliases (audio_pipeline carries 6). The "5 aliases" abstraction counts successor experts that received aliases (continuity_auditor, compliance_gate, visual_executor, audio_pipeline = 4) or some other grouping — neither maps to the on-disk stub count of 10. Reconciliation arithmetic in §Reconciliation Arithmetic below.

---

## FOUND-08 Compliance Audit

FOUND-08 frozen rule: "v1 expert_ids cannot be silently renamed / merged / deprecated." Every migration in Phase 13-17 must have: (a) an explicit redirect stub at the old expert_id, (b) `status:` field declaring the migration type, (c) the new expert's `metadata.hermes.aliases:` list containing the old expert_id. For deprecations (Phase 17) the pattern differs: status + `deprecated_reason` + `inheritance_targets` + preserved body content (no redirect stub needed because the directory is the original path).

### Redirect migrations (10) — verdict table

| Migration | Old expert_id | New expert_id | Stub present? | Stub `status:` | New `aliases:` lists old? | Verdict |
|-----------|---------------|---------------|---------------|----------------|---------------------------|---------|
| Phase 13 RENAME | `continuity` | `continuity_auditor` | yes (`continuity/SKILL.md`) | `renamed` | yes — `aliases: [continuity]` | **PASS** |
| Phase 13 RENAME | `compliance_marketing` | `compliance_gate` | yes (`compliance_marketing/SKILL.md`) | `renamed` | yes — `aliases: [compliance_marketing]` | **PASS** |
| Phase 14 MERGE | `drawer` | `visual_executor` | yes (`drawer/SKILL.md`) | `merged_into` | yes — `aliases: [drawer, animator]` | **PASS** |
| Phase 14 MERGE | `animator` | `visual_executor` | yes (`animator/SKILL.md`) | `merged_into` | yes — `aliases: [drawer, animator]` | **PASS** |
| Phase 15 MERGE | `voicer` | `audio_pipeline` | yes (`voicer/SKILL.md`) | `merged_into` | yes — `aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` | **PASS** |
| Phase 15 MERGE | `lip_sync` | `audio_pipeline` | yes (`lip_sync/SKILL.md`) | `merged_into` | yes — same 6-element aliases list | **PASS** |
| Phase 15 MERGE | `composer` | `audio_pipeline` | yes (`composer/SKILL.md`) | `merged_into` | yes — same 6-element aliases list | **PASS** |
| Phase 15 MERGE | `foley` | `audio_pipeline` | yes (`foley/SKILL.md`) | `merged_into` | yes — same 6-element aliases list | **PASS** |
| Phase 15 MERGE | `mixer` | `audio_pipeline` | yes (`mixer/SKILL.md`) | `merged_into` | yes — same 6-element aliases list | **PASS** |
| Phase 15 FOLD | `spatial_audio` | `audio_pipeline` | yes (`spatial_audio/SKILL.md`) | `folded_into` | yes — same 6-element aliases list | **PASS** |

**Redirect audit verdict: 10 / 10 PASS. Zero silent renames / merges / folds.**

### Deprecation migrations (3) — verdict table

| Migration | Deprecated expert_id | Inheritance targets | `status: deprecated` present? | `deprecated_reason` present? | `inheritance_targets` present? | Original body content preserved? | Verdict |
|-----------|----------------------|---------------------|-------------------------------|------------------------------|--------------------------------|-----------------------------------|---------|
| Phase 17 DEPRECATE | `performer` | `[character_designer, screenplay]` | yes | yes (CN prose) | yes | yes — `references/` intact, body readable | **PASS** |
| Phase 17 DEPRECATE | `scene_builder` | `[cinematographer, style_genome]` | yes | yes (CN prose) | yes | yes | **PASS** |
| Phase 17 DEPRECATE | `storyboard_designer` | `[cinematographer]` | yes | yes (CN prose) | yes | yes | **PASS** |

**Deprecation audit verdict: 3 / 3 PASS. Zero silent deprecations.**

### FOUND-08 overall verdict: **PASS (13 / 13 migrations)**

REQUIREMENTS VALIDATE-01 PASS — every rename / merge / fold / deprecation across Phases 13-17 has explicit mapping records in `skills-mapping.yaml`, explicit redirect / deprecation frontmatter on the old path, and explicit `aliases:` declaration on the new path. No silent migrations.

---

## Backward Compatibility Verification

REQUIREMENTS VALIDATE-02 mandates that every old expert_id reference still resolves via alias or redirect. The verification matrix below confirms each of the 13 legacy expert_ids (10 redirects + 3 deprecated) is discoverable from any consumer that references it.

### Redirect-stub legacy IDs (10) — alias resolution verification

For each legacy expert_id, grep across the entire `skills/movie-experts/` tree for `aliases:.*<old_id>` — at least one successor expert must declare the old id in its aliases list.

| Legacy expert_id | Resolved by (file containing `aliases: ...<old_id>...`) | Resolves? |
|-----------------|--------------------------------------------------------|-----------|
| `continuity` | `continuity_auditor/SKILL.md` (`aliases: [continuity]`) | **YES** |
| `compliance_marketing` | `compliance_gate/SKILL.md` (`aliases: [compliance_marketing]`) | **YES** |
| `drawer` | `visual_executor/SKILL.md` (`aliases: [drawer, animator]`) | **YES** |
| `animator` | `visual_executor/SKILL.md` (`aliases: [drawer, animator]`) | **YES** |
| `voicer` | `audio_pipeline/SKILL.md` (`aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]`) | **YES** |
| `lip_sync` | `audio_pipeline/SKILL.md` (same list) | **YES** |
| `composer` | `audio_pipeline/SKILL.md` (same list) | **YES** |
| `foley` | `audio_pipeline/SKILL.md` (same list) | **YES** |
| `mixer` | `audio_pipeline/SKILL.md` (same list) | **YES** |
| `spatial_audio` | `audio_pipeline/SKILL.md` (same list) | **YES** |

Additionally, each legacy expert_id still has its own redirect-stub directory + `SKILL.md` (`skills/movie-experts/<old_id>/SKILL.md`) preserving the old `expert_id:` field verbatim — so any transcript or historical prompt that references `expert:drawer` continues to resolve to a SKILL.md, not a 404.

### Deprecated legacy IDs (3) — related_skills cleanup verification

Per Phase 17-01, all consumer `related_skills` edges to deprecated experts should have been rewired to inheritance targets. Grep for the deprecated ID as a `related_skills` list entry (pattern `^- <deprecated_id>$` in YAML) in any non-`_eval`, non-`_shared`, non-self SKILL.md:

| Deprecated expert_id | New consumer references found (expected: 0) | Result |
|----------------------|---------------------------------------------|--------|
| `performer` | 0 | **CLEAN** |
| `scene_builder` | 0 | **CLEAN** |
| `storyboard_designer` | 0 | **CLEAN** |

The only surviving references to these IDs are: (a) the deprecated expert's own frontmatter (intentional, FOUND-08 preservation), (b) `_eval/baseline/` regression snapshots (frozen, must preserve point-in-time expert_id), (c) historical records in `skills-mapping.yaml` + plan SUMMARIES. All such references are intentional archival, not new strandings.

### Backward-compat overall verdict: **PASS (13 / 13 legacy IDs resolve)**

REQUIREMENTS VALIDATE-02 PASS — every legacy expert_id (10 redirects + 3 deprecated) is discoverable from any consumer via either (a) the successor's `aliases:` declaration or (b) the preserved self-referential directory + SKILL.md. Zero stranded references.

---

## Reconciliation Arithmetic

```
ACTIVE DAG pipeline-roles    : 15  (expected 16; see DEFECT VALIDATE-D1 below)
ACTIVE non-DAG (verticals)   :  3  (documentary_maker, animation_studio, production)
DEPRECATED (Phase 17)        :  3  (performer, scene_builder, storyboard_designer)
REDIRECT STUBS (FOUND-08)    : 10  (continuity, compliance_marketing, drawer,
                                    animator, voicer, lip_sync, composer, foley,
                                    mixer, spatial_audio)
                             ----
TOTAL SKILL.md files          : 31  (matches `find` output above)
```

**find command output:** 31. Arithmetic block: 15 + 3 + 3 + 10 = 31. Reconciliation **passes** — the on-disk inventory exactly matches the 4-bucket decomposition.

### Discrepancy vs ROADMAP §18 #1 (16 active + 5 aliases = 21)

ROADMAP §18 #1 (current text): *"grep returns 21 (16 active + 5 aliases); no orphan IDs"*. Actual on-disk reality is 31 SKILL.md files decomposed as 15 + 3 + 3 + 10. The 21-target was an early v3.0 estimate that does not match the post-Phase-17 state. The discrepancy is real and must be surfaced (per CONTEXT D-06 "no silent sign-off") rather than silently erased. Reasons the 21-target diverges from 31-reality:

1. **5 aliases → 10 redirect stubs.** The "5 aliases" abstraction appears to count successor experts that received aliases (`continuity_auditor`, `compliance_gate`, `visual_executor`, `audio_pipeline` = 4) plus an off-by-one, or some other coarse grouping. The actual on-disk reality is that FOUND-08 requires one redirect-stub directory per old expert_id, not per successor. There are 10 old expert_ids that were renamed / merged / folded (continuity, compliance_marketing, drawer, animator, voicer, lip_sync, composer, foley, mixer, spatial_audio), so there are 10 redirect stubs.

2. **16 active DAG → 15 on disk.** The 16-node canonical DAG (`01-NODE-DAG.md §1.5`) includes `quality_gate`, but no `quality_gate/` directory exists in `skills/movie-experts/`. The expert was specified in the v2.0 PRFP design suite but never materialized as a SKILL.md during v3.0 Phases 13-17. See DEFECT VALIDATE-D1 below.

3. **3 active non-DAG verticals never counted.** `documentary_maker`, `animation_studio`, and `production` are active experts that v3.0 did not migrate into the canonical DAG (Phase 8 corpus-driven verticals + skills-mapping.yaml `disposition: deferred` respectively). They exist on disk, they have valid `expert_id` frontmatter, but the 21-target assumed only DAG pipeline-roles + aliases would exist.

4. **3 deprecated experts still on disk.** Phase 17 deprecated `performer`, `scene_builder`, `storyboard_designer` but their directories + SKILL.md files remain (FOUND-08 preservation). The 21-target pre-dated Phase 17's deprecation decision and did not account for the deprecated-but-present experts.

**Recommended corrected ROADMAP §18 #1 criterion** (applied in plan 18-01 Task 3):

> `find skills/movie-experts -maxdepth 2 -name 'SKILL.md' | grep -v '_eval\|_shared' | wc -l` returns 31, decomposed as: 15 active DAG pipeline-roles (canonical 16 minus the unresolved `quality_gate` gap — DEFECT VALIDATE-D1) + 3 active non-DAG verticals (`documentary_maker`, `animation_studio`, `production`) + 3 deprecated (`performer`, `scene_builder`, `storyboard_designer`) + 10 redirect stubs preserving legacy expert_id per FOUND-08. Original v3.0 estimate was 21 (16 + 5 aliases); reconciled to actual on-disk inventory per Phase 18-01 VALIDATION-REPORT.md.

---

## Inventory Defects (surfaced for plan 18-03)

These are issues found during the audit that this plan does NOT patch (per the audit-only mandate). Plan 18-03 owns the patches or the explicit decision to defer.

### VALIDATE-D1 — Missing `quality_gate` expert (HIGH)

**Symptom:** `01-NODE-DAG.md §1.5` lists `quality_gate` as one of the 16 canonical DAG pipeline-roles (L6 quality gate, preserved from v1). The v2.0 PRFP design suite references `quality_gate` extensively (`skills-mapping.yaml`, `nodes.yaml`, `edges.yaml`, `02-NODE-SPECS.md`, `03-CORPUS-TRACEABILITY.md`, `corpus-trace.yaml`, `kais-migration-matrix.yaml`, plus Phase 7/9/18 PLAN files). But no `skills/movie-experts/quality_gate/` directory exists on disk. `grep -rl 'quality_gate' skills/movie-experts/` returns zero matches.

**Impact:** Bucket 1 (ACTIVE DAG) counts 15, not 16. The canonical 16-node DAG topology is not fully realized in the skill suite.

**Options for plan 18-03:**
(a) Backfill `skills/movie-experts/quality_gate/` with SKILL.md + minimal refs + edge sync to consumers (extends v3.0 scope).
(b) Document explicitly in ROADMAP + README that `quality_gate` is specified in v2.0 PRFP design but deferred to a future milestone (records the decision rather than backfilling).
(c) Reclassify the canonical DAG as 15 nodes by amending `01-NODE-DAG.md §1.5` (requires design-suite revision).

**Recommendation:** (b) — surface as a known deferral in README + ROADMAP §18. `quality_gate` as a separate skill directory adds limited value when L6 quality-gating is already partially realized inside `script_auditor` + `continuity_auditor` + `theory_critic` consumer edges; full materialization is a candidate for a post-v3.0 phase.

### VALIDATE-D2 — README footer count stale (LOW)

**Symptom:** `skills/movie-experts/README.md` Status line currently reads "18 expert_ids in codebase (15 active + 3 deprecated)" — a Phase-17 close-out artifact. After Phase 18-01 reconciliation the authoritative count is 31 SKILL.md files decomposed per the Reconciliation Arithmetic above.

**Impact:** Reader confusion about the canonical inventory count.

**Mitigation:** Plan 18-02 (documentation finalization) already owns the README inventory rewrite. Plan 18-01 surfaces this defect so 18-02 picks it up explicitly. No separate patch needed in 18-01.

---

## Cross-References

- **REQUIREMENTS.md** VALIDATE-01 — covered by §FOUND-08 Compliance Audit (verdict: PASS).
- **REQUIREMENTS.md** VALIDATE-02 — covered by §Backward Compatibility Verification (verdict: PASS).
- **ROADMAP.md** §18 #1 — corrected criterion applied in plan 18-01 Task 3 commit; original 21-target discrepancy documented above per CONTEXT D-06.
- **ROADMAP.md** §18 #6 — references this report's §FOUND-08 Compliance Audit (PASS).
- **ROADMAP.md** §18 #7 — references this report's §Backward Compatibility Verification (PASS).
- **skills-mapping.yaml** sign_off audit — all 6 sign_off_status entries read `signed_off` (Phase 13-17 close-outs complete).

---

*Report generated by Phase 18 Plan 01 audit task (2026-06-17). Source: on-disk `skills/movie-experts/` inventory + canonical mapping at `.planning/research/v2-pipeline-design/skills-mapping.yaml`. No SKILL.md content modified.*
