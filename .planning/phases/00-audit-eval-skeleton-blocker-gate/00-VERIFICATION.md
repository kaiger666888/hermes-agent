---
phase: 00-audit-eval-skeleton-blocker-gate
verified: 2026-06-15T13:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
gaps_resolved:
  - truth: "No unreferenced TBD/FIXME/XXX debt markers in Phase 0 deliverables (debt-marker gate)"
    status: resolved
    resolution: "Replaced the 'See Phase 3 reference anatomy doc (TBD)' marker in skills/movie-experts/_shared/SKILL-LAYOUT.md:112 with an inline 'Reference file anatomy' H2 section defining the Source/Copyright/Last-verified/Summary/Heuristics column structure. No forward-reference remains."
human_verification:
  - test: "Judge prompt quality review (industry_accuracy, professional_depth, actionability, language_quality dimensions)"
    expected: "judge_prompt.md CoT template elicits nuanced 短剧-craft judgments, not generic LLM-evaluator output; penalty structure for hallucinated tools / fabricated citations is actionable"
    why_human: "grep can verify the 4 dimensions are NAMED in the template, but only a human 短剧 craft expert can judge whether the prompts actually elicit discriminating judgments (vs producing uniform ties regardless of answer quality). The dry-run demo deliberately emits position-bias ties — no real judge signal has been observed yet."
  - test: "GAP-REPORT knowledge_gaps depth review (per-expert)"
    expected: "Each of the 14 GAP-REPORTs surfaces 3-6 concrete knowledge gaps grounded in real 短剧 craft (not generic LLM boilerplate); missing_refs_topics proposes actionable reference file topics that Phase 3/5 can build"
    why_human: "Structure (5 section headers present) is verified by grep, but content quality — whether the gaps are insightful vs filler — requires domain expertise. A 短剧 creator or producer should sample 2-3 GAP-REPORTs to confirm the audit captured real weaknesses."
  - test: "Glossary term completeness and EN<->CN correctness"
    expected: "All 24 glossary entries have accurate CN term + accurate EN translation + accurate usage context; no false friends (e.g., 卡点 ≠ 'rhythm point'; it specifically means paywall cliffhanger in 短剧 context)"
    why_human: "grep verifies 15/15 required terms are present as substrings, but bilingual accuracy — especially for terms with multiple CN meanings — requires native speaker verification."
  - test: "Phantom replacement tokens preserve expert comprehensibility"
    expected: "After stripping wan22_video -> <video_gen_primary> and 168K controlled tokens -> ExBxSxP description, the animator + performer SKILL.md still produce sensible LLM behavior when invoked"
    why_human: "Static grep confirms phantoms are gone and placeholders are present, but whether an LLM actually understands <video_gen_primary> as 'use whatever video gen model the runtime has' vs emitting the literal placeholder string requires a live invocation test."
  - test: "Operational risk: _eval/baseline/<expert>/SKILL.md may shadow canonical SKILL.md in Hermes skill loader"
    expected: "When skills are synced to ~/.hermes/skills/ via setup-hermes.sh (cp -rn) or skills_sync.py, the byte-exact baseline copies under _eval/baseline/ sort BEFORE the cleaned-up canonical copies (because '_' < lowercase letters in ASCII), and may win the skill-loader dedup race — serving users the stale/phantom-laden baseline instead of the cleaned-up skill"
    why_human: "This is a runtime behavior concern that does NOT violate any Phase 0 success criterion (all 5 SCs are about file existence/state, verified PASSED). The baseline copies are byte-exact BY DESIGN (SC #2 contract). The risk is architectural: Hermes core loader does not exclude _eval/_shared from discovery. Requires human decision: (a) accept the risk (operators must add _eval, _shared to a future exclusion list — but that requires a Hermes core change outside this project's scope per CLAUDE.md '不改 Hermes 核心'), (b) rename baseline copies to a non-SKILL.md filename (breaks the byte-exact contract), or (c) document the operational mitigation (operators must NOT point external_dirs at the repo skills/ tree, or must manually exclude _eval/ from sync). Needs human judgement on the right tradeoff."
---

# Phase 0: AUDIT + Eval Skeleton (BLOCKER GATE) Verification Report

**Phase Goal:** Eliminate phantom references in all 14 existing SKILL.md files; capture a pre-refactor baseline; build the eval harness skeleton so every subsequent "improvement" claim is statistically defensible.
**Verified:** 2026-06-15T13:05:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | `scripts/verify_skill_references.py` exists and reports zero phantom refs across all 14 SKILL.md files | VERIFIED | `python3 scripts/verify_skill_references.py --strict` exits 0 with output: `audit complete: 0 phantom reference(s) across 14 skill file(s); allowlist size=77`. Both required phantoms (`wan22_video` in animator, `168K controlled tokens` in performer) are stripped from canonical SKILL.md (grep -c returns 0). Phantom denylist hard-block in place post CR-01 fix (line 76, 305). |
| 2 | `_eval/baseline/<expert>/SKILL.md` snapshot exists for all 14 existing experts, tagged `eval-baseline-v1` | VERIFIED | `ls skills/movie-experts/_eval/baseline/` shows 14 expert dirs (animator, colorist, composer, continuity, drawer, editor, foley, mixer, performer, scene_builder, screenplay, spatial_audio, style_genome, voicer). Each has `SKILL.md` + `PROVENANCE.json`. Programmatic check: all 14 PROVENANCE files have `tag=eval-baseline-v1`, all 7 required keys present, all `expert_id` values match directory name. |
| 3 | `_eval/runner.py` produces valid position-swap (both A/B and B/A) comparison output on at least one sample expert | VERIFIED | Behavioral spot-check: `python3 _eval/runner.py --expert animator --dry-run --output-json /tmp/v.json --output-md /tmp/v.md` exits 0, produces JSON with `total_comparisons=3` and 3 verdicts each containing `ordering_ab=A, ordering_ba=B, final=tie` (the stub deliberately emits A/B disagreement to demonstrate the tie rule). Markdown table has columns `prompt_id \| pair \| winner \| judge`. |
| 4 | `GAP-REPORT.md` exists for all 14 experts documenting phantom findings, knowledge gaps, prompt weak points, stale metrics, missing refs topics | VERIFIED | `ls skills/movie-experts/*/GAP-REPORT.md \| wc -l` returns 14. Per-expert section check: all 14 GAP-REPORTs have all 5 required section headers (`<phantoms>`, `<knowledge_gaps>`, `<prompt_weak_points>`, `<stale_metrics>`, `<missing_refs_topics>`). animator GAP-REPORT references `wan22_video`; performer GAP-REPORT references `168K`. Each header references baseline tag `eval-baseline-v1`. |
| 5 | `_shared/glossary.md` skeleton published with core EN↔CN term dictionary | VERIFIED | File exists (142 lines). Programmatic check: all 15 SC #5 required terms present (运镜, 钩子, 卡点, 爆款, 男频, 女频, 完播率, 付费卡点, 爽点, 击中点, 镜头语言, 景别, 视角, 轴线, 调度). 24 total H3 entries (>= 16 required). Each entry has CN/EN/Context structure. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `scripts/verify_skill_references.py` | Phantom detector CI lint, ≥150 lines, exports main/build_allowlist/scan_skill_file | VERIFIED | 512 lines. AST-check confirms `main`, `build_allowlist`, `scan_skill_file`, `format_report`, `Finding` dataclass exported. `_PHANTOM_DENYLIST` hard-block in place. |
| `scripts/tests/test_verify_skill_references.py` | Pytest coverage, ≥60 lines | VERIFIED | 390 lines, 11 tests. Includes denylist-override-prevention tests (CR-01 fix). |
| `skills/movie-experts/_shared/known-external-models.yaml` | Manual override allowlist with sora + 12+ entries | VERIFIED | 23 entries (sora, veo, kling, runway, flux, stable_audio, cosyvoice, minimax, qwen, deepseek, yi, glm, elevenlabs, musicgen, pixverse, recraft, nano-banana, grok-imagine, z-image, gpt-image-1.5/2, synthesis_model, audioldm-2, audiogen). Each with provenance note. |
| `skills/movie-experts/_eval/snapshot.py` | Capture/verify tool, ≥120 lines | VERIFIED | 465 lines. Public exports: `compute_provenance`, `capture_baselines`, `verify_baselines`, `main`. CR-02 fix (untracked-expert RuntimeError) + WR-08 fix (PROVENANCE schema validation) both landed. |
| `skills/movie-experts/_eval/tests/test_snapshot.py` | Pytest coverage, ≥50 lines | VERIFIED | 282 lines, 9 tests including untracked-dir + missing-keys + wrong-tag coverage. |
| `skills/movie-experts/_eval/runner.py` | MT-Bench position-swap harness, ≥150 lines | VERIFIED | 647 lines. Exports: `main`, `run_position_swap`, `run_ablation`, `parse_judge_decision`, `format_results`. `DEFAULT_TEMPERATURE = 0.0` hard-pinned (EVAL-03). WR-03 + WR-04 + WR-09 fixes landed. |
| `skills/movie-experts/_eval/judge_prompt.md` | CoT template with `<decision>` tag + 4 dimensions | VERIFIED | Contains 3 `<decision>` references + all 4 dimensions (industry_accuracy, professional_depth, actionability, language_quality) named. |
| `skills/movie-experts/_eval/config.yaml.example` | Example config declaring 2+ open-weight judges via OpenRouter | VERIFIED | YAML parses. `judge.models`: qwen/qwen3-235b-a22b:free + deepseek/deepseek-chat-v3:free. 2 ablation conditions (baseline, candidate). |
| `skills/movie-experts/_eval/prompts/animator_demo.yaml` | 3 demo prompts for animator expert | VERIFIED | Parses with `expert_id: animator` and 3 prompts (anim-001, anim-002, anim-003). |
| `skills/movie-experts/_eval/tests/test_runner.py` | Pytest coverage, ≥50 lines | VERIFIED | 322 lines, 13 tests covering parser + position-swap + ablation + temp pin + fail-fast + markdown escape. |
| `skills/movie-experts/_shared/glossary.md` | EN↔CN dictionary with 运镜 + ≥16 entries | VERIFIED | 142 lines, 24 H3 entries, all 15 required terms present. |
| `skills/movie-experts/_shared/SKILL-LAYOUT.md` | Standard layout spec, ≥40 lines | VERIFIED | 113 lines, 8 H2 sections. Documents required/optional/forbidden files + naming + frontmatter schema. (Contains 1 unreferenced TBD — see Gaps.) |
| `skills/movie-experts/_shared/RAG-INVOCATION-PATTERN.md` | Provider-agnostic RAG contract, ≥40 lines | VERIFIED | 102 lines, 10 H2 sections. References `mem0_search`, `fact_store`, conditional phrasing, graceful degradation. |
| `skills/movie-experts/<expert>/GAP-REPORT.md` × 14 | Per-expert audit findings, 5 sections each | VERIFIED | All 14 files exist, each with all 5 required section headers. animator references wan22_video; performer references 168K. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `verify_skill_references.py` | `plugins/*/plugin.yaml` | PyYAML load at runtime | WIRED | `_walk_plugin_yamls` accepts both `.yaml` and `.yml` (WR-07 fix). Live run produces `allowlist size=77`. |
| `verify_skill_references.py` | `_shared/known-external-models.yaml` | PyYAML load manual overrides | WIRED | Scanner merges 23 override entries with plugin-derived tokens. |
| `snapshot.py` | `<expert>/SKILL.md` | Path read at capture time | WIRED | 14 baselines captured with byte-exact copies. |
| `snapshot.py` | `git rev-parse HEAD` | subprocess | WIRED | `_current_git_sha` returns 40-char SHA, falls back to "uncommitted" on error. All 14 PROVENANCE records carry real git_sha `817953459c809b4f91e3be0208c8832314e2d026`. |
| `runner.py` | `_eval/baseline/<expert>/SKILL.md` (tag eval-baseline-v1) | PROVENANCE shape | WIRED | `DEFAULT_TAG = "eval-baseline-v1"` constant in runner.py (line referenced). |
| `runner.py` | `judge_prompt.md` | Jinja2 template render | WIRED | 2 jinja2 references in runner.py; judge_prompt.md has 3 `<decision>` tag anchors. |
| `_eval/` Python modules | Hermes tool registry | registry.register call | NOT_WIRED (correct) | AST scan confirms zero `registry.register(...)` calls in `_eval/runner.py` and `_eval/snapshot.py` — EVAL-09 satisfied. |
| `<expert>/SKILL.md` (post-cleanup) | `verify_skill_references.py --strict` | Lint gate | WIRED | `--strict` exits 0 across all 14 files. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `_eval/runner.py` demo report | `verdicts` list | `_StubJudgeClient` in dry-run mode | Yes (stub verdicts, position-bias pattern) | FLOWING (stub) — Real judge data deferred to Phase 6 (live `OPENROUTER_API_KEY` runs). `reports/README.md` documents this as "DRY-RUN stub verdicts, not real LLM judge output." |
| `_eval/snapshot.py` PROVENANCE | `sha256`, `git_sha` | `hashlib.sha256(file_bytes)` + `subprocess git rev-parse HEAD` | Yes (real file hashes + real commit SHA) | FLOWING |
| `verify_skill_references.py` findings | `Finding` list | Regex scan of real `skills/movie-experts/*/SKILL.md` + allowlist merge from real `plugins/*` + `_shared/known-external-models.yaml` | Yes (live scan, allowlist size=77) | FLOWING |
| `GAP-REPORT.md` `<phantoms>` section | phantom findings | Output of `verify_skill_references.py` JSON | Yes (animator: 5 wan2/wan22_video findings; performer: 1 168K finding) | FLOWING |
| `_shared/glossary.md` | term entries | Manually authored | Yes (24 hand-curated entries with provenance) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phantom detector exits 0 under --strict | `python3 scripts/verify_skill_references.py --strict` | exit 0, "0 phantom reference(s)" | PASS |
| Snapshot tool captures 14 baselines | `python3 _eval/snapshot.py capture` (verified via existing baseline tree) | 14 dirs with SKILL.md + PROVENANCE.json | PASS |
| Snapshot verify detects drift | `python3 _eval/snapshot.py verify` | Reports drift on all 14 (expected — 00-04 modified all 14 post-capture) | PASS (drift IS the proof of cleanup per plan note) |
| Runner dry-run produces valid output | `python3 _eval/runner.py --expert animator --dry-run --output-json /tmp/v.json --output-md /tmp/v.md` | exit 0, total_comparisons=3, both orderings present | PASS |
| Test suite passes | `uv run pytest scripts/tests/ skills/movie-experts/_eval/tests/ -q` | 41 passed in 0.71s | PASS |
| expert_id preservation (FOUND-08) | Per-expert YAML parse of frontmatter | 14/14 expert_id values match directory name | PASS |

### Probe Execution

Step 7c SKIPPED — Phase 0 PLAN/SUMMARY do not declare probe scripts, and no `scripts/*/tests/probe-*.sh` conventional probes exist. The Phase 0 verification surface is covered by `verify_skill_references.py --strict` (the gate) and the pytest suite.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| FOUND-01 | 00-04 | 14 GAP-REPORT.md files with knowledge gaps + weak points + stale metrics + missing refs | SATISFIED | 14 files exist, each with 5 required sections. |
| FOUND-02 | 00-01 | verify_skill_references.py CI lint greps model/tool names against plugins/ inventory | SATISFIED | Script runs, allowlist=77 tokens (50 plugin-derived + 23 manual + 3 stopwords + 4 added in 00-04). |
| FOUND-03 | 00-04 | Phantom refs stripped (no wan22_video, no 168K, no FLUX 1.x sampler params) | SATISFIED | `grep -c "wan22_video" animator/SKILL.md` = 0; `grep -c "168K controlled" performer/SKILL.md` = 0; full-dir scan returns 0. |
| FOUND-04 | 00-02 | Pre-refactor baseline snapshot at `_eval/baseline/<expert>/SKILL.md`, tagged eval-baseline-v1 | SATISFIED | 14 baselines, all with correct tag, all 7 PROVENANCE fields present. |
| FOUND-05 | 00-04 | Standard skill layout documented and enforced | SATISFIED | `_shared/SKILL-LAYOUT.md` (113 lines, 8 H2 sections) covers required/optional/forbidden files + naming + frontmatter. |
| FOUND-06 | 00-01, 00-04 | Provider-agnostic RAG invocation pattern documented | SATISFIED | `_shared/RAG-INVOCATION-PATTERN.md` (102 lines) references mem0_search/fact_store forbidden patterns + conditional phrasing + graceful degradation. |
| FOUND-07 | 00-04 | References table at top of every SKILL.md (Ref / When to Read / Contents columns) | SATISFIED | All 14 SKILL.md contain `## References` header + `| Ref | When to Read | Contents |` table row. |
| FOUND-08 | 00-01, 00-02, 00-04 | All 14 expert_id values preserved unchanged | SATISFIED | YAML parse of all 14 frontmatters: expert_id matches directory name 14/14. PROVENANCE.json expert_id matches 14/14. |
| FOUND-09 | 00-04 | `_shared/glossary.md` EN↔CN term dictionary published | SATISFIED | 24 H3 entries, all 15 required terms (运镜/hook/卡点/爆款/男频/女频/完播率/付费卡点/爽点/击中点/镜头语言/景别/视角/轴线/调度) present. |
| EVAL-01 | 00-03 | `_eval/runner.py` implements MT-Bench position-swap (both A/B and B/A; disagreement = tie) | SATISFIED | runner.py implements `run_position_swap` calling judge twice (swap=False then swap=True), `_final_verdict` collapses disagreement to tie. Unit tests + dry-run demo confirm. |
| EVAL-02 | 00-02 | `_eval/snapshot.py` captures/reads baseline snapshots tagged eval-baseline-v1 | SATISFIED | `BASELINE_TAG = "eval-baseline-v1"` constant. capture + verify modes both functional. |
| EVAL-03 | 00-03 | CoT judge template with judge temperature pinned at 0 | SATISFIED | `DEFAULT_TEMPERATURE = 0.0` module constant, `build_judge_kwargs` always passes `temperature=DEFAULT_TEMPERATURE`. No config field exposes temperature. Unit test `test_judge_temperature_is_zero` passes. |
| EVAL-04 | 00-03 | Ablation comparison capability (N>=2 conditions, pairwise) | SATISFIED | `run_ablation` uses `itertools.combinations` over condition labels. Demo runs 2 conditions x 3 prompts = 3 verdicts. Unit test covers 3-condition ablation (6 verdicts). |
| EVAL-08 | 00-02, 00-03 | Harness uses only existing Hermes deps (openai, pyyaml, jinja2) — no new packages | SATISFIED | `git diff pyproject.toml` shows no dependency additions. snapshot.py uses stdlib only (hashlib, subprocess, json, pathlib, datetime, argparse). runner.py uses openai + pyyaml + jinja2 (all pre-pinned). |
| EVAL-09 | 00-03 | `_eval/` is NOT registered in Hermes tool registry | SATISFIED | AST scan of `_eval/runner.py` + `_eval/snapshot.py` confirms zero `registry.register(...)` calls. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `skills/movie-experts/_shared/SKILL-LAYOUT.md` | 112 | `TBD` (unreferenced — line says "Phase 3 reference anatomy doc (TBD)" but cites no formal tracking ID like issue #, PR #, DEF-*) | BLOCKER | Debt-marker gate violation. Completion of the forward-referenced "Phase 3 reference anatomy doc" is not auditable from this marker. Either remove the forward-reference, add a formal tracking ID, or inline the anatomy spec. |
| `skills/movie-experts/_shared/SKILL-LAYOUT.md` | 113 | "placeholders" prose | Info | Legitimate use of the word "placeholder" to describe the `<video_gen_primary>` token convention. Not a stub indicator. |
| `skills/movie-experts/_shared/RAG-INVOCATION-PATTERN.md` | 68-82 | "Placeholder token conventions" section | Info | Legitimate — documents the `<video_gen_primary>` etc. token convention, with Phase 3/5 resolution path documented. Not a stub. |
| `_eval/reports/animator_demo.{json,md}` | all | "DRY-RUN stub verdicts" | Info | Intentional — `reports/README.md` documents these as shape-evidence only (SC #3 contract), not real judge output. Stub verdicts are the documented fallback for missing OPENROUTER_API_KEY. |

### Human Verification Required

#### 1. Judge Prompt Quality Review

**Test:** Have a 短剧 craft expert (or someone with vertical-short-drama production experience) read `_eval/judge_prompt.md` and judge whether the 4 dimensions (industry_accuracy, professional_depth, actionability, language_quality) and the penalty structure for hallucinated tools / fabricated citations would actually elicit discriminating judgments between a baseline answer and a RAG-uplifted answer.
**Expected:** The template should reward concrete heuristics + numeric ranges over hand-wavy advice, and penalize hallucinated tool names / fabricated citations heavily enough that a phantom-containing baseline would lose to a cleaned-up candidate.
**Why human:** grep can verify the 4 dimensions are NAMED, but only a domain expert can judge whether the prompts actually discriminate. The dry-run demo emits uniform ties by design — no real judge signal has been observed.

#### 2. GAP-REPORT Knowledge Gaps Depth Review

**Test:** Sample 2-3 GAP-REPORTs (suggest: screenplay, editor, colorist — the deep-refactor candidates per ROADMAP Phase 3) and review the `<knowledge_gaps>` + `<missing_refs_topics>` sections for concrete, actionable craft insights vs generic LLM filler.
**Expected:** Each gap names a specific craft topic (e.g., "Save the Cat beat sheet integration", "Murch Rule of Six", "短剧 pacing density 1.5-2x horizontal rate") rather than generic advice like "improve pacing".
**Why human:** Structure (5 headers present) is grep-verifiable, but content depth requires domain expertise.

#### 3. Glossary Bilingual Accuracy

**Test:** Have a native CN speaker review all 24 glossary entries for translation accuracy, especially for terms with multiple CN meanings (e.g., 卡点 must specifically mean "paywall cliffhanger" in 短剧 context, not the literal "rhythm point").
**Expected:** Each entry's CN term, EN translation, and Context fields are accurate and unambiguous for 短剧 production use.
**Why human:** grep verifies term presence as substrings, but bilingual accuracy — especially false friends — requires native fluency.

#### 4. Phantom Replacement Token Comprehensibility

**Test:** Invoke the animator + performer skills in a live Hermes session (with a real LLM) and confirm the `<video_gen_primary>` / `<video_gen_preview>` placeholders and the ExBxSxP description produce coherent model behavior — i.e., the LLM understands these as "use whatever video gen model the runtime has" rather than emitting the literal placeholder string.
**Expected:** LLM responses reference concrete runtime-available models (per the allowlist) or ask clarifying questions about available models, rather than echoing `<video_gen_primary>` verbatim.
**Why human:** Static grep confirms phantoms stripped + placeholders present, but whether an LLM actually comprehends the placeholder convention requires a live invocation.

#### 5. Operational Risk: _eval/baseline Shadowing (Architectural WARNING)

**Test:** Configure Hermes with `skills.external_dirs` pointing at the repo `skills/` tree (or run `setup-hermes.sh` which does `cp -rn skills/* ~/.hermes/skills/`), then invoke `/skills` or similar listing. Confirm whether the discovered "animator" skill is the cleaned-up canonical version or the stale `_eval/baseline/animator/SKILL.md` (which still contains `wan22_video`).
**Expected:** The cleaned-up canonical version wins; users do not accidentally load the phantom-laden baseline.
**Why human:** The Hermes skill loader's `EXCLUDED_SKILL_DIRS` does NOT include `_eval` or `_shared`. Path-sort order puts `_eval/baseline/animator/SKILL.md` BEFORE `animator/SKILL.md` (because `_` < lowercase letters in ASCII), so the baseline would WIN the `seen_names` dedup race and serve users the stale/phantom-laden copy. This does NOT violate any Phase 0 SC (all SCs are file-existence/state checks, all PASS), but poses a real operational risk that the project's "不改 Hermes 核心 Python/JS 代码" constraint makes non-trivial to fix. Needs human decision on the right tradeoff (operator-facing docs vs filename rename vs core exclusion list).
**Recommended mitigation options for the human to decide:**
- (a) Accept the risk and document operator-facing guidance: "do NOT configure `skills.external_dirs` to point at the repo `skills/` tree; manually copy `skills/movie-experts/<expert>/` (without `_eval`/`_shared`) to `~/.hermes/skills/movie-experts/`".
- (b) Rename `_eval/baseline/<expert>/SKILL.md` to `_eval/baseline/<expert>/SKILL.md.baseline` (breaks the byte-exact contract — would need a capture-side rename).
- (c) Add `_eval`, `_shared` to `EXCLUDED_SKILL_DIRS` in `agent/skill_utils.py` — but this requires a Hermes core change that the project constraints forbid.
- (d) Move baselines outside `skills/` (e.g., to `.eval-cache/baseline/`) so they're not under the skills tree at all — cleanest but requires updating snapshot.py + runner.py default paths.

### Gaps Summary

**1 gap blocking clean PASS:**

**Gap 1 (BLOCKER — debt-marker gate violation):** `skills/movie-experts/_shared/SKILL-LAYOUT.md:112` contains an unreferenced `TBD` marker: `"See Phase 3 reference anatomy doc (TBD)."`. The line references a future phase but no formal tracking ID (issue #, PR #, DEF-*). Per the debt-marker gate rule, unreferenced TBD/FIXME/XXX markers are blockers because completion is not auditable. The forward-referenced "Phase 3 reference anatomy doc" is real (Phase 3 ROADMAP REFACTOR-08 references "Each ref contains ≥ 1 concrete heuristic/number/rule NOT in base model training"), but the marker itself does not cite a tracking ID.

**Fix options** (any one closes the gap):
1. Replace `(TBD)` with a tracking reference: `"See Phase 3 reference anatomy doc (tracked in REFACTOR-08 — Phase 3 ROADMAP)."`.
2. Drop the forward-reference entirely and link to existing content: `"See `_shared/RAG-INVOCATION-PATTERN.md` for the placeholder token convention."`.
3. Inline the anatomy spec as a new H2 section in SKILL-LAYOUT.md (e.g., `## Reference File Anatomy`) so no future doc is required.

**Architectural WARNING (not a gap, not blocking):** The `_eval/baseline/<expert>/SKILL.md` byte-exact copies (SC #2 contract) may shadow the cleaned-up canonical SKILL.md in the Hermes skill loader because `EXCLUDED_SKILL_DIRS` does not exclude `_eval`/`_shared`, and `_` sorts before lowercase letters. This is a runtime behavior concern that does not violate any Phase 0 SC (all SCs are file-state checks, all PASS). Documented in human_verification #5 for human decision on the right mitigation tradeoff.

---

_Verified: 2026-06-15T13:05:00Z_
_Verifier: Claude (gsd-verifier)_
