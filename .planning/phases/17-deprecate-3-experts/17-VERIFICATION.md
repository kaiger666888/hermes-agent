---
phase: 17-deprecate-3-experts
verified: 2026-06-17T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 17: Deprecate 3 Experts — Verification Report

**Phase Goal:** A reader can find 3 deprecated experts (`performer`, `scene_builder`, `storyboard_designer`) each marked `status: deprecated` with redirect annotations pointing to their inheritance targets (character_designer + screenplay / cinematographer + style_genome / cinematographer composition_lock respectively), and old expert_ids preserved for backward compatibility.

**Verified:** 2026-06-17
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | `performer/SKILL.md` marked `status: deprecated` + redirect to `character_designer` + `screenplay` | VERIFIED | `status: deprecated` line 10; `inheritance_targets: [character_designer, screenplay]` line 19; `> ⚠️ DEPRECATED (Phase 17 v3.0, 2026-06-17)` blockquote line 24 with both targets named; CN `deprecated_reason:` line 18 |
| 2   | `scene_builder/SKILL.md` marked `status: deprecated` + redirect to `cinematographer` + `style_genome` | VERIFIED | `status: deprecated` line 10; `inheritance_targets: [cinematographer, style_genome]` line 19; body blockquote line 24; CN rationale line 18 |
| 3   | `storyboard_designer/SKILL.md` marked `status: deprecated` + redirect to `cinematographer` (composition_lock sub-task per Phase 7 §3.4 D3.4) | VERIFIED | `status: deprecated` line 10; `inheritance_targets: [cinematographer]` line 19; body blockquote line 24 cites "Phase 7 §3.4 D3.4"; CN rationale line 18 |
| 4   | Each deprecated SKILL.md retains original expert_id + body content (FOUND-08 backward compat) | VERIFIED | `expert_id: performer`/`scene_builder`/`storyboard_designer` preserved at frontmatter line 15; body content line counts 168/186/301 with 11 key body sections each; git diff vs `d8cda9140~1` for performer shows +10 / -0 lines (zero deletions, pure additive); internal `related_skills:` lists unchanged in the 3 deprecated files (FOUND-08 v1 graph frozen) |
| 5   | `metadata.hermes.deprecated: true` + `metadata.hermes.deprecated_reason: <CN prose>` per deprecation rationale | VERIFIED | All 3 files: `deprecated: true` at frontmatter line 17 + `deprecated_reason:` with CN prose at line 18; YAML parses cleanly via `yaml.safe_load` for all 3 — schema: `{status=deprecated, expert_id=correct, deprecated=True, targets=correct}` |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `skills/movie-experts/performer/SKILL.md` | deprecated expert w/ full markers + FOUND-08 body preserved | VERIFIED | All 5 frontmatter keys + body blockquote + 168 lines body intact (11 sections); git diff confirms additive-only |
| `skills/movie-experts/scene_builder/SKILL.md` | same pattern, target cinematographer+style_genome | VERIFIED | All markers present; 186 lines body; 11 sections preserved |
| `skills/movie-experts/storyboard_designer/SKILL.md` | same pattern, target cinematographer | VERIFIED | All markers present; 301 lines body; 11 sections preserved; Phase 7 §3.4 D3.4 cited |
| `skills/movie-experts/README.md` | 3 DEPRECATED markers + sub-section + DAG cleanup + footer count | VERIFIED | `### 3 Deprecated Experts (Phase 17 — 2026-06-17)` sub-section at line 112 with 3-row rationale table; 3 inline `⚠️ DEPRECATED Phase 17` markers on inventory rows (lines 66/67/89); legend note line 206; footer "18 expert_ids in codebase (15 active + 3 deprecated)" lines 5 + 462; active DAG (text format) contains 0 deprecated IDs |
| `skills/movie-experts/_shared/glossary.md` | 6 deprecation annotations on body prose | VERIFIED | 6 `deprecated Phase 17` annotations across contexts (镜头语言 / 轴线 / 调度 / 男主女主 / Phase 7 header / 分镜); no new top-level entries (correct per plan) |
| `.planning/research/v2-pipeline-design/skills-mapping.yaml` | 3 entries signed_off (performer, scene_builder, storyboard_designer); production UNCHANGED | VERIFIED | All 3 deprecate_candidate entries have `sign_off_status: signed_off` + `signed_off_at: 2026-06-17` + `signed_off_by: phase-17` + `action_for_v21: "FULFILLED in v3.0 ..."` prose; production entry remains `disposition: deferred` (correctly NOT signed off); total signed_off count = 6 (≥3 new + prior) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| performer/SKILL.md frontmatter | character_designer + screenplay | `metadata.hermes.inheritance_targets` | WIRED | `inheritance_targets: [character_designer, screenplay]` (line 19) |
| scene_builder/SKILL.md frontmatter | cinematographer + style_genome | `metadata.hermes.inheritance_targets` | WIRED | `inheritance_targets: [cinematographer, style_genome]` (line 19) |
| storyboard_designer/SKILL.md frontmatter | cinematographer | `metadata.hermes.inheritance_targets` | WIRED | `inheritance_targets: [cinematographer]` (line 19) |
| Consumer SKILL.md related_skills | inheritance targets | related_skills YAML lists | WIRED | 0 non-deprecated consumers list any of performer/scene_builder/storyboard_designer in related_skills; 8 consumer files updated (character_designer, screenplay, cinematographer, style_genome, visual_executor, audio_pipeline, editor, production, animation_studio); body prose in 7 consumer files annotated with "Phase 17 v3.0: was X" / "replaces deprecated Phase 17 X" |
| skills-mapping.yaml deprecate entries | Phase 17 sign-off | `sign_off_status` field | WIRED | All 3 entries signed_off; traceability chain ROADMAP §17 → DEPRECATE-01/02/03 → skills-mapping.yaml → README → glossary complete |

### Data-Flow Trace (Level 4)

Not applicable — phase produces static documentation (markdown frontmatter + body prose). No runtime data flow to trace. All "data" (expert_ids, inheritance targets, rationale prose) is YAML/markdown literals verified directly via grep + YAML parse.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| YAML frontmatter parses without error on all 3 files | `python3 -c "import yaml; yaml.safe_load(open(f).read().split('---')[1])"` × 3 | All 3 parsed successfully with expected keys | PASS |
| Internal FOUND-08 graph preserved in deprecated files | `git diff d8cda9140~1 d8cda9140 -- skills/movie-experts/performer/SKILL.md \| grep -c "^-"` | 0 deletions (10 additions only) | PASS |
| No consumer file retains stale related_skills edges | Loop over 18 non-deprecated consumers, grep `related_skills:` for deprecated IDs | 0 hits | PASS |
| Mermaid/text DAG no longer shows deprecated IDs as active | `awk '/```text/,/```/' README.md \| grep -c "performer\|scene_builder\|storyboard_designer"` | 0 | PASS |
| Commits in SUMMARY exist in git history | `git cat-file -t 1bec1f530 f38d8c254` | Both exist as commit objects | PASS |

### Probe Execution

Not applicable — Phase 17 has no `scripts/*/tests/probe-*.sh` probes declared in PLANs. Pure markdown/YAML artifact phase; deterministic grep + YAML parse substitutes for probes.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DEPRECATE-01 | 17-01, 17-02 | Deprecate performer (fold into character_designer + screenplay) | SATISFIED | performer/SKILL.md fully deprecated; skills-mapping.yaml signed_off; README + glossary annotated |
| DEPRECATE-02 | 17-01, 17-02 | Deprecate scene_builder (fold into cinematographer + style_genome) | SATISFIED | scene_builder/SKILL.md fully deprecated; sign-off + inventory + glossary complete |
| DEPRECATE-03 | 17-01, 17-02 | Deprecate storyboard_designer (fold into cinematographer composition_lock) | SATISFIED | storyboard_designer/SKILL.md fully deprecated; Phase 7 §3.4 D3.4 cited; sign-off + inventory complete |

No orphaned requirements in REQUIREMENTS.md mapped to Phase 17.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | No TBD/FIXME/XXX unreferenced markers; no TODO/HACK/PLACEHOLDER; no empty returns or hardcoded empty data in the 3 modified deprecated files; YAML parses cleanly |

### Human Verification Required

None. Phase 17 is a pure markdown + YAML deprecation pass. All truths are deterministic and verified via grep + YAML parse + git diff. No UI behavior, no runtime state, no external service integration requiring human eyes.

### Gaps Summary

No gaps found. All 5 ROADMAP §17 Success Criteria met:

1. `performer/SKILL.md` `status: deprecated` + redirect to `character_designer` + `screenplay` — VERIFIED
2. `scene_builder/SKILL.md` `status: deprecated` + redirect to `cinematographer` + `style_genome` — VERIFIED
3. `storyboard_designer/SKILL.md` `status: deprecated` + redirect to `cinematographer` (composition_lock sub-task per Phase 7 §3.4 D3.4) — VERIFIED
4. Each deprecated SKILL.md retains original expert_id + body content (FOUND-08) — VERIFIED (additive-only git diff: +10/-0 for performer; expert_id preserved at frontmatter line 15; 11 body sections each)
5. `metadata.hermes.deprecated: true` + `metadata.hermes.deprecated_reason: <CN prose>` per deprecation rationale — VERIFIED

Consumer rewiring also complete: 0 non-deprecated consumers retain stale related_skills edges; 7 consumer files carry thorough Phase 17 body prose annotations. README + glossary + skills-mapping.yaml close-out artifacts (Plan 02) all in place. Phase 18 can proceed to reconcile the canonical 21-expert topology.

---

_Verified: 2026-06-17_
_Verifier: Claude (gsd-verifier)_
