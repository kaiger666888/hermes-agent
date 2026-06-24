---
phase: 33-observability-integration-close-out
verified: 2026-06-25T00:15:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 7/8
  gaps_closed:
    - "SC-7 test filter false-positive (caught README.md which IS the SC-6 deliverable). Fixed in commit 2ac9a31d3 — filter now excludes README.md per ROADMAP SC-7 scope (protects bundled <skill_id>/SKILL.md only, not suite-level docs)."
  gaps_remaining: []
  regressions: []
gaps: []
    reason: "TestByteIntactChecks.test_sc7_bundled_skill_unchanged FAILS (1/42 tests red). The test implements CONTEXT.md line 118 filter (grep -v _eval | grep -v _shared) which catches the legitimate README.md modification shipped by Plan 03 as an SC-6 deliverable. The underlying FOUND-08 invariant holds under the ROADMAP SC-7 contract (zero bundled SKILL.md / frontmatter / DAG changes), but the shipped test suite is internally inconsistent: PLAN 33-03 verification block (line 195) uses a different command that also excludes README.md and glossary.md, while the test code does not. SUMMARY 33-03 claims '42 passed in 1.15s' — actual run is 41 passed / 1 failed."
    artifacts:
      - path: "tests/hermes_cli/test_curator_stats.py"
        issue: "TestByteIntactChecks.test_sc7_bundled_skill_unchanged (line ~1108) filters `git diff --name-only v5.0..HEAD -- skills/movie-experts/` with `_eval/` and `_shared/` exclusion only — does NOT exclude README.md or _shared/glossary.md, so the README.md modification (Plan 03 SC-6 deliverable) shows up as a violation. Result: assertion `assert not violations` fails with `['skills/movie-experts/README.md']`."
    missing:
      - "Update test_sc7_bundled_skill_unchanged filter to exclude README.md and _shared/glossary.md (matching PLAN 33-03 line 195 verification command: `grep -v _eval | grep -v _shared | grep -v README.md | grep -v _shared/glossary.md`). OR tighten the assertion to inspect frontmatter bytes only (the actual ROADMAP SC-7 contract: zero expert_id/related_skills frontmatter edits). Either fix makes the test pass while preserving the FOUND-08 invariant guarantee."
      - "Re-run SUMMARY 33-03 self-check command (`python -m pytest tests/hermes_cli/test_curator_stats.py -x`) and correct the '42 passed' claim to reflect actual result."
deferred: []
human_verification:
  - test: "Live `hermes curator stats <skill_id>` visual review on a populated FeedbackStore"
    expected: "Dashboard renders meaningfully — verdict buckets with non-zero counts, patch history table populated, eval-score trend sparkline visible, exit code 0. Operator can read skill health at a glance."
    why_human: "Requires live data in ~/.hermes/skills/.feedback/ (operator must populate via /feedback or hermes feedback import) AND subjective visual review of rich.table output. Cannot be seeded by automated verification without bypassing the real ingest path. VALIDATION.md line 69 marks this Manual-Only."
  - test: "Architecture doc end-to-end read-through for new-operator onboarding clarity"
    expected: "A new operator reading `_shared/v6-feedback-loop-architecture.md` from top to bottom can understand: (a) what the feedback loop achieves, (b) the data flow from ingest to observe, (c) the JSON schema, (d) eval-gate thresholds, (e) human-in-loop boundaries, (f) module ownership, (g) where to find further references. No ambiguity, no broken cross-refs, no stale content."
    why_human: "Subjective documentation quality — grep can verify section presence but not clarity, narrative coherence, or onboarding effectiveness. VALIDATION.md line 70 marks this Manual-Only."
---

# Phase 33: Observability + Integration Close-out Verification Report

**Phase Goal:** Operators can observe feedback-driven learning health per-skill and across the whole movie-experts suite, and the v6.0 milestone ships a canonical architecture doc + skills-mapping sign-off + README/glossary close-out mirroring the v5.0 Phase 27 pattern.
**Verified:** 2026-06-24T23:28:55Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `hermes curator stats [skill_id]` emits per-skill dashboard (verdict buckets + patch history + eval score trend over N runs) — SC-1, OBS-01 | ✓ VERIFIED | `_cmd_stats` handler at `hermes_cli/curator.py:1171`; `_render_per_skill_dashboard` at `:891`; rich.table.Table with verdict rows; sparkline via `_sparkline` at `:825` using unicode blocks ▁▂▃▄▅▆▇█; `--runs N` default 10 limits trend depth. Behavioral spot-check with seeded {good:1, needs_work:1, bad:1} data rendered correct table + buckets. TestStatsPerSkill + TestRunsFlag green (4 tests). |
| 2 | `hermes curator stats --all` emits cross-skill view (top-N negative + zero-feedback list) — SC-2, OBS-02 | ✓ VERIFIED | `_render_cross_skill_view` at `hermes_cli/curator.py:1011`; parses `<skill>:<source>:<verdict>` bucket keys; computes `neg_count = needs_work + bad`; sorts desc, slices top-N; scans `~/.hermes/skills/movie-experts/` for bundled experts, derives zero-feedback set. Behavioral spot-check with seeded screenplay data → `top_negative=[{skill_id: screenplay, neg_count: 2}]`. TestStatsAll green (2 tests). |
| 3 | `hermes curator stats --by-source` emits verdict distribution by source (CLI / kais_aigc / manual) — SC-3, OBS-03 | ✓ VERIFIED | `_render_source_breakdown` at `hermes_cli/curator.py:1107`; iterates `_SOURCES = ("cli", "kais_aigc", "manual")` calling `store.summary(source=s)` per source; collapses verdicts. Behavioral spot-check → `by_source={cli:{good:1,needs_work:1,bad:1}, kais_aigc:{0,0,0}, manual:{0,0,0}}`. TestStatsBySource green (1 test). |
| 4 | `--json` emits counts only — no correction/output_snapshot/feedback_ids leakage (T-33-01) | ✓ VERIFIED | Per-skill JSON payload keys: `['skill_id', 'verdict_buckets', 'patch_count', 'eval_trend_count', 'recent_commit_shas']`. Behavioral spot-check with correction text seeded: `correction_in_payload=False`, `feedback_ids_present=False`. TestJsonOutput green (2 tests). |
| 5 | Empty FeedbackStore returns exit 0 + friendly "no feedback yet" message (T-33-05) | ✓ VERIFIED | `_empty_store_message()` at `:883` returns `"no feedback yet — run /feedback in a Hermes conversation or \`hermes feedback import <jsonl>\` to seed data"`. Behavioral spot-check on empty store: `rc=0`, message rendered. TestEmptyStore green (3 tests covering all 3 modes). |
| 6 | Canonical architecture doc `_shared/v6-feedback-loop-architecture.md` written, mirroring v86-pipeline-mapping.md — SC-4 | ✓ VERIFIED | File exists (305 lines). Metadata header (Source/Copyright/Last-verified 2026-06-25/verified_date 2026-06). 10 H2 sections (7 CONTEXT.md content + 3 v86 footer: Refresh Cadence, See Also, Source Citation). ASCII data-flow diagram with boxed pipeline stages (Operator → P28 → P29 → P30 → P31 → P32 → P33). No mermaid blocks. Bilingual CN+EN. Footer ownership line `*Owned by Phase 33 plan 33-02...*`. TestArchitectureDoc green (8 tests). |
| 7 | `skills-mapping.yaml` new `v6_ref_signoffs:` section mirrors v5 schema — SC-5 | ✓ VERIFIED | Section at line 295. Single entry for v6-feedback-loop-architecture.md with 10 fields (ref_path, expert_owner, phase_added=v6.0-phase-33, requirement=OBS-01, verified_date=2026-06-25, source, license_status=fair_use_paraphrase, line_count=305, signed_off_by=phase-33-doc-01, notes). v5_ref_signoffs byte-intact (still 2 entries). TestSkillsMappingV6 green (6 tests). |
| 8 | SC-7 FOUND-08 milestone-wide preservation: zero new expert_id dirs, zero DAG changes, zero frontmatter edits across 6 phases | ✓ VERIFIED (under ROADMAP contract) | Direct git diff verification: (a) zero SKILL.md modifications: `git diff --name-only v5.0..HEAD -- skills/movie-experts/ \| grep SKILL\.md$` → empty. (b) zero new expert_id dirs (add-filtered, excluding _eval/_shared/README/glossary) → empty. (c) zero frontmatter expert_id/related_skills edits on bundled SKILL.md → empty. (d) zero DAG rewiring → empty. README.md modification is the SC-6 deliverable (corpus tree update), not a FOUND-08 violation. **NOTE:** The shipped test `test_sc7_bundled_skill_unchanged` FAILS because it uses an inconsistent filter that catches README.md — see Gaps Summary. |
| 9 | SC-8 v5/v4 refs byte-intact milestone-wide (5 refs unchanged vs v5.0) | ✓ VERIFIED | `git diff --quiet v5.0..HEAD -- skills/movie-experts/_shared/{snowflake-method,e-konte-format,scamper-variations,dreamina-cli-baseline,v86-pipeline-mapping}.md` exit code 0. Line-count diff: 0. TestByteIntactChecks::test_sc8_v5_v4_refs_unchanged green. |
| 10 | Phase 33 ships a green test suite verifying SC-1..SC-8 (per VALIDATION.md + PLAN success_criteria "All tests green") | ✗ FAILED | `uv run python -m pytest tests/hermes_cli/test_curator_stats.py` → **41 passed, 1 failed** in 1.17s. TestByteIntactChecks::test_sc7_bundled_skill_unchanged fails (false positive on README.md). SUMMARY 33-03 claims "42 passed in 1.15s" — inaccurate. |

**Score:** 9/10 truths verified (counting Truth #10 as the failed one). Under the original 8-SC framing: 8/8 SC contracts satisfied, but the meta-deliverable "green test suite" is failed.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `hermes_cli/curator.py` | `_cmd_stats` handler + 6 helpers + subparser | ✓ VERIFIED | 1485 lines total; 8 new functions at lines 825-1231; subparser wired at lines 1435-1469 with 6 args + set_defaults(func=_cmd_stats). All helpers substantive (no stubs). |
| `tests/hermes_cli/test_curator_stats.py` | 14 test classes covering OBS-01/02/03 + SC-4/5/6/7/8 | ⚠️ MIXED | 14 classes present, 1161 lines, 42 tests. 41 green, 1 RED (TestByteIntactChecks::test_sc7_bundled_skill_unchanged). |
| `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` | Canonical v6 architecture doc | ✓ VERIFIED | 305 lines, 10 H2 sections, ASCII diagram, bilingual, v86 conventions. |
| `.planning/research/v2-pipeline-design/skills-mapping.yaml` | `v6_ref_signoffs:` section added | ✓ VERIFIED | Section at line 295, 1 entry mirroring 10-field v5 schema. v5 section byte-intact (2 entries unchanged). |
| `skills/movie-experts/README.md` | Corpus tree `_shared/` block lists v6 ref | ✓ VERIFIED | Line 425: `└── v6-feedback-loop-architecture.md (Phase 33 v6.0 NEW — feedback-loop canonical architecture ref)`. |
| `skills/movie-experts/_shared/glossary.md` | 4 new H3 bilingual entries + footer note | ✓ VERIFIED | `## v6.0 additions` H2 at line 487; 4 H3 entries (Curator Proposal/Eval Gate/Feedback Ingestion/Knowledge Evolution) in EN-first format; each with CN/EN/Context subsections; each cross-refs v6-feedback-loop-architecture.md; footer note explains EN-first shift. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `hermes_cli/curator.py:_cmd_stats` | `agent/feedback_store.py:FeedbackStore.summary` | lazy in-handler import + `summary(skill_id=..., source=...)` call | ✓ WIRED | Lines 1189, 1196: `from agent.feedback_store import FeedbackStore`; `store = FeedbackStore()`; summary called inside renderers at lines 906, 1019, 1117. Behavioral spot-check confirmed real data flows through. |
| `hermes_cli/curator.py:_cmd_stats` | `agent/curator_audit.py:read_audit` | lazy in-handler import + `read_audit(action="apply", skill=...)` call | ✓ WIRED | Line 1190: `from agent.curator_audit import read_audit`; called at line 923 inside `_render_per_skill_dashboard`. |
| `hermes_cli/curator.py:_cmd_stats` | `agent/evolution/__init__.py:read_queue` | lazy in-handler import + `read_queue(status="applied")` call | ✓ WIRED | Line 1191: `from agent.evolution import read_queue`; called at line 911 inside `_render_per_skill_dashboard`. |
| `hermes_cli/curator.py` module body | (none — runtime isolation) | zero module-level `agent.evolution` imports | ✓ WIRED | `grep -c "^from agent\.evolution\|^import agent\.evolution" hermes_cli/curator.py` → 0. P31 runtime-isolation invariant preserved. |
| `skills/movie-experts/_shared/glossary.md:v6 entries` | `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` | each entry's Context bullet cross-references the doc | ✓ WIRED | Each of 4 entries contains `[v6-feedback-loop-architecture.md](./v6-feedback-loop-architecture.md)` with section anchor. |
| `skills/movie-experts/README.md:corpus tree` | `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` | `_shared/` block lists the new ref | ✓ WIRED | README line 425 lists the v6 ref within the `_shared/` corpus tree block. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|----|
| `_render_per_skill_dashboard` | `verdicts` (collapsed counts) | `store.summary(skill_id=...)` → `_collapse_verdicts` | Yes (seeded test: {good:1, needs_work:1, bad:1}) | ✓ FLOWING |
| `_render_per_skill_dashboard` | `skill_patches` | `read_queue_fn(evolution_dir=..., status="applied")` filtered by skill_id | Yes (empty in test — no applied patches in tmp; path is wired + defensively try/except) | ✓ FLOWING |
| `_render_per_skill_dashboard` | `trend_entries` | `read_audit_fn(action="apply", skill=...)` filtered by `eval_score` truthy | Yes (empty in test — no audit entries; path is wired) | ✓ FLOWING |
| `_render_cross_skill_view` | `per_skill` | `store.summary()` → bucket key parse `<skill>:<source>:<verdict>` | Yes (seeded test: screenplay with neg_count=2) | ✓ FLOWING |
| `_render_source_breakdown` | `per_source` | `store.summary(source=s)` for s in {cli, kais_aigc, manual} → `_collapse_verdicts` | Yes (seeded test: cli has counts, others empty) | ✓ FLOWING |

All five renderers are wired to real data sources. No HOLLOW / STATIC / DISCONNECTED status. Empty results in test runs reflect empty upstream stores, not broken wiring.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Empty store per-skill returns exit 0 + friendly message | `_cmd_stats(Namespace(skill_id='screenplay', as_json=False))` on empty store | rc=0; stdout: "no feedback yet — run /feedback in a Hermes conversation or `hermes feedback import <jsonl>` to seed data" | ✓ PASS |
| Per-skill JSON with seeded {good,needs_work,bad} data | `_cmd_stats(Namespace(skill_id='screenplay', as_json=True))` after 3 record_feedback calls | rc=0; payload `{skill_id, verdict_buckets:{good:1,needs_work:1,bad:1}, patch_count:0, eval_trend_count:0, recent_commit_shas:[]}`; no `correction` / `feedback_ids` / `output_snapshot` keys | ✓ PASS |
| Per-skill human table renders | same as above with `as_json=False` | rc=0; rich.table with 3 verdict rows (good/needs_work/bad), counts 1/1/1, weighted 1.0/1.0/1.0 | ✓ PASS |
| Cross-skill JSON top-N negative | `_cmd_stats(Namespace(all_skills=True, as_json=True))` after seeding screenplay | rc=0; `top_negative=[{skill_id:'screenplay', neg_count:2}]`; zero_feedback=[] (tmp dir lacks bundled scan target — production would list bundled experts) | ✓ PASS |
| Source breakdown JSON | `_cmd_stats(Namespace(by_source=True, as_json=True))` after seeding cli source | rc=0; `by_source={cli:{good:1,needs_work:1,bad:1}, kais_aigc:{0,0,0}, manual:{0,0,0}}` | ✓ PASS |
| Full Phase 33 test suite | `uv run python -m pytest tests/hermes_cli/test_curator_stats.py` | **41 passed, 1 failed** in 1.17s (TestByteIntactChecks::test_sc7_bundled_skill_unchanged FAILED) | ✗ FAIL |
| Phase 28-32 regression | `uv run python -m pytest tests/agent/test_feedback_store.py tests/agent/test_feedback_schema.py tests/agent/test_audit_log.py tests/agent/evolution/ tests/hermes_cli/test_curator_cli.py` | 222 passed in 3.56s | ✓ PASS |
| Ruff PLW1514 on new code | `uv run ruff check hermes_cli/curator.py tests/hermes_cli/test_curator_stats.py` | All checks passed | ✓ PASS |
| Runtime isolation invariant | `grep -c "^from agent\.evolution\|^import agent\.evolution" hermes_cli/curator.py` | 0 | ✓ PASS |

### Probe Execution

Not applicable — Phase 33 does not declare or imply probe-based verification (no `scripts/*/tests/probe-*.sh` referenced in PLAN/SUMMARY).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| OBS-01 | 33-01 | Per-skill dashboard (`hermes curator stats [skill_id]`) | ✓ SATISFIED | `_render_per_skill_dashboard` at `hermes_cli/curator.py:891`; TestStatsPerSkill + TestRunsFlag green (4 tests); behavioral spot-check with seeded data rendered correct buckets + sparkline + patch history. |
| OBS-02 | 33-01 | Cross-skill view (`hermes curator stats --all`) | ✓ SATISFIED | `_render_cross_skill_view` at `hermes_cli/curator.py:1011`; TestStatsAll green (2 tests); behavioral spot-check produced correct top_negative list. |
| OBS-03 | 33-01 | Source breakdown (CLI/kais-aigc/manual) | ✓ SATISFIED | `_render_source_breakdown` at `hermes_cli/curator.py:1107`; TestStatsBySource green (1 test); behavioral spot-check produced correct per-source verdict distribution. |

No orphaned requirements. ROADMAP maps OBS-01/02/03 to Phase 33; all 3 are claimed by PLAN 33-01 and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|---------|--------|
| `hermes_cli/curator.py` | ~998 | `except (TypeError, ValueError): pass` in `_sparkline` deltas parsing | ℹ️ Info | Benign — standard Python pattern for safe float conversion; not a stub. No fix needed. |
| `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` | 236, 254 | "P31 placeholder" / "EVOL-02 placeholder uses stdlib difflib" | ℹ️ Info | Documentation of P31's design decision (P31 used stdlib difflib that P32 extended), not a debt marker in Phase 33 code. Accurate architectural narrative. |
| `.planning/research/v2-pipeline-design/skills-mapping.yaml` | 10 | `superseded_by: TBD` | ℹ️ Info | Pre-existing header field, NOT modified by Phase 33. Phase 33 only appended v6_ref_signoffs at file end (line 295+). |
| `skills/movie-experts/README.md` | 284, 389, 394 | "placeholder" references | ℹ️ Info | All in pre-existing unchanged regions (v1.5 expert gap notes, GAP-REPORT doc annotations). Not Phase 33 modifications. |
| `skills/movie-experts/_shared/glossary.md` | 257 | "provider-agnostic placeholders" | ℹ️ Info | Pre-existing prompt_injector entry; describes design intent, not a stub. Unchanged by Phase 33. |

No 🛑 Blocker debt markers. No ⚠️ Warning anti-patterns in Phase 33 additions. All flagged patterns are either benign Python idioms or pre-existing content in unchanged regions.

### Human Verification Required

#### 1. Live `hermes curator stats <skill_id>` visual review on populated FeedbackStore

**Test:** Populate `~/.hermes/skills/.feedback/` with real feedback (via `/feedback` slash command in a Hermes conversation, or `hermes feedback import <jsonl>` with a baseline batch). Then run `hermes curator stats <skill_id>` (e.g., `hermes curator stats screenplay`) and visually inspect the rendered rich.table dashboard.
**Expected:** Dashboard renders meaningfully — verdict buckets (good/needs_work/bad) with non-zero counts, weighted column reflecting time-decay, patch history table populated with patch_id + ts, eval-score trend sparkline using unicode block chars (▁▂▃▄▅▆▇█), "need more data for full trend" footer when fewer than `--runs` entries. Operator can read skill health at a glance.
**Why human:** Requires live data in `~/.hermes/skills/.feedback/` (operator must populate via real ingest path) AND subjective visual review of rich.table output. Automated verification seeds data directly via `FeedbackStore.record_feedback()` which bypasses the real ingest path; visual layout quality (column alignment, color styling, sparkline readability) cannot be asserted via grep. VALIDATION.md line 69 explicitly marks this as Manual-Only.

#### 2. Architecture doc end-to-end read-through for new-operator onboarding clarity

**Test:** Read `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` from top to bottom as if you were a new operator onboarding onto v6.0. Verify you can understand: (a) what the feedback loop achieves (Overview & Goal), (b) the data flow from Operator → ingest → store → gate → evolve → curate → observe (Data Flow + ASCII diagram), (c) the FeedbackRecord/PatchRecord/audit-log field contracts (JSON Schema Reference), (d) the eval-gate thresholds and where they're configured (Eval-Gate Thresholds), (e) the human-in-loop boundary between bundled and agent-created skills (Human-in-Loop Boundaries), (f) which module owns which phase's deliverable (Module Ownership Map), (g) where to find further references (Roadmap References + See Also).
**Expected:** No ambiguity, no broken cross-references, no stale content pointing at non-existent modules, ASCII diagram legible in both GitHub render and raw view, bilingual CN+EN prose reads naturally.
**Why human:** Subjective documentation quality. Grep can verify section presence (TestArchitectureDoc enforces 10 H2 sections, metadata header, ASCII diagram, no mermaid, bilingual CJK, See Also + Source Citation), but cannot assess clarity, narrative coherence, or onboarding effectiveness. VALIDATION.md line 70 explicitly marks this as Manual-Only.

### Gaps Summary

**One gap found — severity: WARNING (test-suite inconsistency, not a goal-blocker).**

The Phase 33 test suite ships with **41/42 tests green**. The single failing test, `TestByteIntactChecks::test_sc7_bundled_skill_unchanged`, is a **false positive**:

- The test implements the CONTEXT.md line 118 filter (`grep -v _eval | grep -v _shared`) to verify SC-7 (FOUND-08 milestone-wide preservation).
- Plan 03's own SC-6 deliverable modifies `skills/movie-experts/README.md` to add the v6 architecture doc to the corpus tree.
- The test's filter does NOT exclude `README.md`, so the legitimate documentation change shows up as a FOUND-08 violation: `AssertionError: SC-7 FAIL: ... ['skills/movie-experts/README.md']`.
- The PLAN 33-03 verification block (line 195) uses a DIFFERENT, more lenient command that adds `grep -v README.md | grep -v _shared/glossary.md` — this is the command SUMMARY 33-03 ran to claim "SC-7 PASS: 0". The test code does not match this lenient command.

**Underlying FOUND-08 invariant is preserved.** Direct verification of the ROADMAP SC-7 contract (line 135: "zero new expert_id directories created, zero DAG node changes, zero frontmatter `expert_id` / `related_skills` edits on bundled skills") returns:
- Zero SKILL.md modifications: `git diff --name-only v5.0..HEAD -- skills/movie-experts/ | grep SKILL\.md$` → empty
- Zero new expert_id dirs (add-filtered, excluding _eval/_shared/README/glossary) → empty
- Zero frontmatter expert_id/related_skills edits → empty
- Zero DAG rewiring → empty

So SC-7's actual contract holds; only the test's filter is broken.

**Why this is gaps_found, not passed:** The phase ships a test suite that doesn't pass on its own SC-7 verification. Per VALIDATION.md sampling contract ("Before `/gsd:verify-work`: Full regression + SC-7/SC-8 milestone-wide byte-intact checks") and PLAN 33-03 `<success_criteria>` ("All tests green; Ruff clean"), a green test suite is a Phase 33 deliverable. The fix is trivial (5-character change to the test filter), but until applied, the phase cannot be claimed complete. SUMMARY 33-03's self-check claim of "42 passed in 1.15s" is also inaccurate and should be corrected.

**Recommended fix (for `/gsd:plan-phase --gaps`):**

Update `tests/hermes_cli/test_curator_stats.py::TestByteIntactChecks::test_sc7_bundled_skill_unchanged` filter to match PLAN 33-03 line 195 verification command — exclude `README.md` and `_shared/glossary.md` as legitimate SC-6 documentation deliverables:

```python
violations = [
    p for p in changed
    if "_eval/" not in p
    and "_shared/" not in p
    and not p.endswith("README.md")
    and not p.endswith("_shared/glossary.md")
]
```

This realigns the test with both the PLAN verification block and the ROADMAP SC-7 contract (which scopes FOUND-08 to expert_id dirs / DAG / frontmatter, NOT documentation files). After this fix, all 42 tests will pass.

**Code-review warnings (3, non-blocking, documented in 33-REVIEW.md):**
- WR-01: `--all` and `--by-source` silently ignored when both passed alongside `skill_id` (UX ambiguity; no warning emitted)
- WR-02: `--all` zero-feedback list hardcoded to `movie-experts/` only (other skill categories not scanned)
- WR-03: `_render_source_breakdown` queries `store.summary()` 3 times — potential snapshot inconsistency if concurrent feedback write happens between calls

These are real observations but do not block OBS-01/02/03 goal achievement. They are tracked in `33-REVIEW.md` for future hardening.

---

_Verified: 2026-06-24T23:28:55Z_
_Verifier: Claude (gsd-verifier)_
