---
phase: 00-audit-eval-skeleton-blocker-gate
plan: 03
subsystem: eval-harness
tags: [eval, llm-as-judge, mt-bench, position-swap, ablation, openrouter, animator]
requires:
  - 00-02 (baseline snapshots — runner loads PROVENANCE shape from snapshot.py)
  - 00-04 (phantom ref cleanup — animator baseline still has wan22_video pre-cleanup; current SKILL.md cleaned)
provides:
  - "_eval/runner.py: MT-Bench position-swap LLM-as-judge harness with N>=2 ablation"
  - "_eval/judge_prompt.md: 4-dimension CoT judge template with <decision> tag"
  - "_eval/config.yaml.example: 2-judge open-weight panel via OpenRouter"
  - "_eval/prompts/animator_demo.yaml: 3 demo prompts (vertical framing, motion-emotion, cross-shot consistency)"
  - "_eval/tests/test_runner.py: 12-test pytest suite (position-swap, ablation, parser, temp pin)"
affects:
  - "Phase 3 REFACTOR: uses this harness to measure RAG uplift on refactored skills"
  - "Phase 6 EVAL: full N>=20 benchmark will extend runner.py with live test-model invocation"
tech-stack:
  added: []
  patterns:
    - "MT-Bench position-swap (disagreement resolves to tie — position-bias mitigation)"
    - "Pairwise ablation over N>=2 conditions (itertools.combinations)"
    - "Judge temperature hard-pinned at module-constant level (DEFAULT_TEMPERATURE=0.0)"
    - "Stub/dry-run client for SC #3 acceptance without API key"
key-files:
  created:
    - skills/movie-experts/_eval/runner.py
    - skills/movie-experts/_eval/judge_prompt.md
    - skills/movie-experts/_eval/config.yaml.example
    - skills/movie-experts/_eval/prompts/animator_demo.yaml
    - skills/movie-experts/_eval/tests/test_runner.py
    - skills/movie-experts/_eval/reports/animator_demo.json
    - skills/movie-experts/_eval/reports/animator_demo.md
    - skills/movie-experts/_eval/reports/README.md
  modified: []
decisions:
  - "Position-swap tie rule: disagreement between A/B and B/A orderings resolves to tie (MT-Bench pattern)"
  - "Stub judge in dry-run deliberately emits A-then-B disagreement to demonstrate the tie rule"
  - "Judge temperature is a module-level constant, not a config field — EVAL-03 hard-pin"
  - "SC #3 acceptance: dry-run output shape is sufficient evidence; live API run deferred to Phase 6"
metrics:
  duration: 6m24s
  completed: 2026-06-15T04:40:36Z
  tasks: 3
  files: 8
---

# Phase 00 Plan 03: MT-Bench Position-Swap LLM-as-Judge Harness Summary

Built the credibility anchor for every "RAG uplift" claim in Phase 3/5/6 — an MT-Bench-style position-swap LLM-as-judge harness with ablation capability, proven end-to-end on the animator expert via dry-run.

## What Was Built

**`runner.py` (616 lines)** — the harness core:
- `parse_judge_decision(raw_text)` — regex-extracts `<decision>A|B|tie</decision>` (case-insensitive); defaults to `"tie"` when no tag found (T-00-11 fail-safe).
- `build_judge_messages(prompt, answer_a, answer_b, swap)` — renders the Jinja2 judge prompt template + constructs a blind user message labeling answers "1" and "2" (never reveals which condition produced which).
- `build_judge_kwargs(messages, model, swap)` — **EVAL-03 hard-pin**: `temperature=0.0` is a literal module constant, not configurable. `swap` rides through `extra_body` so the judge client (real or mock) can record which ordering it saw without polluting the OpenAI schema.
- `run_position_swap(...)` — calls the judge twice (A-first then B-first), parses both decisions, collapses via `_final_verdict`: agreement on A → `A_wins`, agreement on B → `B_wins`, anything else → `tie` (position-bias signal).
- `run_ablation(conditions, prompts, judge_client, judge_model)` — EVAL-04: enumerates all C(N,2) pairs over N>=2 condition labels via `itertools.combinations`, runs position-swap for each pair × prompt.
- `format_results(verdicts, judge_label)` — returns `(json_dict, markdown_table)` where JSON has `{total_comparisons, verdicts}` and Markdown has columns `prompt_id | pair | winner | judge`.
- `main()` — argparse CLI with `--config`, `--expert`, `--dry-run`, `--output-json`, `--output-md`. `--dry-run` uses `_StubJudgeClient` which deliberately emits A/B-vs-B/A disagreement → `final="tie"`, demonstrating the position-swap output shape without burning real API quota.

**`judge_prompt.md`** — Jinja2 template positioning the judge as a real 短剧 craft veteran. Four evaluation dimensions:
1. `industry_accuracy` (行业准确度) — does the answer match real-world short-drama craft? Penalties for hallucinated tools, wrong platform constraints, fabricated citations.
2. `professional_depth` (专业深度) — concrete heuristics + numeric ranges vs hand-wavy advice.
3. `actionability` (可执行性) — could a real creator act on this today with the tools they have?
4. `language_quality` (语言质量) — bilingual consistency (EN structure + CN examples).

Each dimension scored 1-5 with one-sentence justification. Final `<decision>A|B|tie</decision>` tag with overall reasoning. Explicit position-bias guard paragraph.

**`config.yaml.example`** — 2-judge open-weight panel via OpenRouter for cross-vendor diversity (EVAL-06):
- `qwen/qwen3-235b-a22b:free` (Alibaba Qwen3 235B)
- `deepseek/deepseek-chat-v3:free` (DeepSeek V3)

Declares 2 ablation conditions (`baseline`, `candidate`) for Phase 0 demo. Phase 3 will extend to 3: `old_no_refs`, `new_no_refs`, `new_with_refs`.

**`prompts/animator_demo.yaml`** — 3 demo prompts covering the animator's distinct craft axes:
- `anim-001` — vertical-screen framing (9:16 constraint, horizontal-dolly-vs-vertical-axis tradeoff)
- `anim-002` — motion-emotion mapping (stillness vs turmoil; motion_intensity + velocity_curve specs)
- `anim-003` — cross-shot consistency (I-frame locking, motion_tags, drift detection across 6 episodes)

**`tests/test_runner.py` (207 lines, 12 tests)** — `MockJudgeClient` returns canned decisions keyed on the `swap` flag, so unit tests make zero real API calls. Covers: decision parsing (5 variants including case-insensitivity and no-tag default), position-swap disagreement→tie, consistent winner, 3-condition pairwise ablation (6 verdicts), JSON+Markdown format shape, and the EVAL-03 temperature pin.

## Demo Run Output (Dry-Run)

OPENROUTER_API_KEY was not set during this execution. Per 00-03-PLAN.md SC #3 acceptance bar, dry-run output shape is sufficient evidence (SC #3 validates output *shape* — presence of `ordering_ab` + `ordering_ba` fields and the position-swap comparison structure — NOT winner quality).

```
[runner] INFO loaded 3 prompts for expert 'animator'
[runner] INFO dry-run: using stub judge client (no API calls)
[runner] INFO ablation produced 3 verdicts (2 conditions x 3 prompts)
total_comparisons=3 expert=animator judge=qwen/qwen3-235b-a22b:free dry_run=True
```

Sample verdict (`animator_demo.json`):

```json
{
  "prompt_id": "anim-001",
  "ordering_ab": "A",
  "ordering_ba": "B",
  "final": "tie",
  "pair": ["baseline", "candidate"],
  "judge": "qwen/qwen3-235b-a22b:free"
}
```

The stub deliberately emits A when A is first (`swap=False`) and B when B is first (`swap=True`) — the classic position-bias pattern. `_final_verdict` correctly collapses this disagreement to `tie`, demonstrating that the harness does NOT trust a single ordering.

Markdown report (`animator_demo.md`):

```
| prompt_id | pair | winner | judge |
|-----------|------|--------|-------|
| anim-001 | baseline vs candidate | tie | qwen/qwen3-235b-a22b:free |
| anim-002 | baseline vs candidate | tie | qwen/qwen3-235b-a22b:free |
| anim-003 | baseline vs candidate | tie | qwen/qwen3-235b-a22b:free |
```

## Verification Results

| Check | Result |
|-------|--------|
| pytest suite | 12/12 passing |
| dry-run produces non-empty JSON+MD | OK (727 bytes JSON, 289 bytes MD) |
| EVAL-03 temperature hard-pin | 3 grep hits (constant + docstring references) |
| EVAL-09 zero registry.register AST calls | OK (verified at AST level — docstring mentions don't count) |
| CLAUDE.md PLW1514 (every open() has encoding=) | OK |
| No new pyproject.toml deps | OK (diff vs base commit ebdc0e2f8 is empty) |
| judge_prompt.md names all 4 dimensions | OK |
| config.yaml.example declares 2+ open-weight judges | OK (qwen + deepseek) |
| runner.py min 150 lines | OK (616 lines) |
| test_runner.py min 50 lines | OK (207 lines) |
| SC #3: both orderings present in JSON | OK (3/3 verdicts have ordering_ab + ordering_ba) |

## TDD Gate Compliance

This plan used task-level TDD (`tdd="true"` on Tasks 1 and 2). Gate sequence in git log:

1. `test(00-03): add failing tests for eval runner position-swap` — RED gate (commit `ec70b04e2`). Tests collected 0 items / 1 error with `ModuleNotFoundError: No module named 'runner'`.
2. `feat(00-03): implement runner.py MT-Bench skeleton + judge prompt` — GREEN gate (commit `ff8d5f59c`). All 12 tests pass.
3. `feat(00-03): animator demo prompts + harness validation report` — non-TDD Task 3 (commit `7e901f9e0`).

No REFACTOR commit needed — implementation was clean on first GREEN pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Created minimal prompts stub during Task 2 to unblock dry-run verification**
- **Found during:** Task 2 verify step
- **Issue:** The plan's Task 2 verify command (`runner.py --expert animator --dry-run ...`) requires `_eval/prompts/animator_demo.yaml` to exist, but Task 2's `<files>` list does not include it. The file is authored in Task 3.
- **Fix:** Created a minimal 1-prompt stub (`anim-001` only) during Task 2 so the dry-run smoke test could execute. Task 3 then replaced it with the full 3-prompt version.
- **Files modified:** `skills/movie-experts/_eval/prompts/animator_demo.yaml` (created in Task 2 commit `ff8d5f59c`, enriched in Task 3 commit `7e901f9e0`).
- **Commit:** included in `ff8d5f59c`.

**2. [Non-deviation — test count] Plan said "6 tests"; implementation has 12.**
- **Found during:** Task 1 implementation.
- **Issue:** The plan's `<behavior>` block enumerates 6 logical scenarios (`test_parse_judge_decision_extracts_tag`, `test_position_swap_runs_both_orderings`, etc.). I split each scenario into focused pytest methods (e.g. `test_parse_judge_decision_extracts_tag_A`, `_B`, `_tie`, `_case_insensitive`, `_no_tag_defaults_to_tie` = 5 methods for one scenario).
- **Decision:** This is idiomatic pytest style (one assertion per method, granular failure reporting) and matches the existing `test_snapshot.py` style. Not a deviation — same coverage, finer granularity. All 6 plan-listed scenarios are covered.

### Auth Gates

**OPENROUTER_API_KEY unset** — live demo fell back to `--dry-run` per SC #3 acceptance bar. Not a blocker; this is the documented fallback path. Future operators running Phase 6 full eval must set `OPENROUTER_API_KEY` (https://openrouter.ai/keys) before invoking `runner.py` without `--dry-run`.

## Threat Model Compliance

All 6 threats in the plan's `<threat_model>` register are addressed:

| Threat | Disposition | Status |
|--------|-------------|--------|
| T-00-09 OPENROUTER_API_KEY logged | mitigate | OK — key passed directly to OpenAI constructor; never logged; warning message when missing is redacted |
| T-00-10 prompt injection | accept | OK — runner is offline dev tooling; prompts authored by trusted dev (EVAL-09 boundary) |
| T-00-11 malformed judge response | mitigate | OK — `parse_judge_decision` defaults to "tie"; logged as warning |
| T-00-12 non-deterministic judge | mitigate | OK — `temperature=0.0` hard-pinned via module constant (EVAL-03) |
| T-00-13 OpenRouter rate limit | accept | OK — free-tier throttling acceptable for Phase 0; Phase 6 adds retry/backoff |
| T-00-SC no new packages | accept | OK — uses only `openai`, `pyyaml`, `jinja2` (all pre-pinned in pyproject.toml) |

## Known Stubs

The committed `reports/animator_demo.{json,md}` files contain **dry-run stub verdicts**, not real LLM judge output. The stub deliberately emits position-bias disagreement (A-then-B) to demonstrate the tie rule. These are committed only as SC #3 shape-evidence. `reports/README.md` documents this status so future operators don't mistake them for real eval results. Real judge runs require `OPENROUTER_API_KEY` and are deferred to Phase 6.

## Operator Setup (for Phase 6 live runs)

To run the harness with real LLM judges:

```bash
# 1. Get an OpenRouter API key (free tier sufficient for skeleton demo)
#    https://openrouter.ai/keys

# 2. Set the env var (do NOT commit it)
export OPENROUTER_API_KEY=sk-or-v1-...

# 3. Run the harness against the animator demo
python skills/movie-experts/_eval/runner.py \
    --config skills/movie-experts/_eval/config.yaml.example \
    --expert animator \
    --output-json skills/movie-experts/_eval/reports/animator_live.json \
    --output-md skills/movie-experts/_eval/reports/animator_live.md

# 4. (Optional) dry-run to validate config + prompts without API calls
python skills/movie-experts/_eval/runner.py --expert animator --dry-run ...
```

Phase 6 will additionally wire `test_model` in `config.yaml.example` to a real provider from `cli-config.yaml` so the test model (the SKILL being evaluated) generates real answers, not stubs.

## Self-Check: PASSED

**Files exist:**
- `skills/movie-experts/_eval/runner.py` — FOUND (616 lines)
- `skills/movie-experts/_eval/judge_prompt.md` — FOUND
- `skills/movie-experts/_eval/config.yaml.example` — FOUND
- `skills/movie-experts/_eval/prompts/animator_demo.yaml` — FOUND
- `skills/movie-experts/_eval/tests/test_runner.py` — FOUND (207 lines)
- `skills/movie-experts/_eval/reports/animator_demo.json` — FOUND
- `skills/movie-experts/_eval/reports/animator_demo.md` — FOUND
- `skills/movie-experts/_eval/reports/README.md` — FOUND

**Commits exist:**
- `ec70b04e2` — test(00-03): RED phase
- `ff8d5f59c` — feat(00-03): GREEN phase (runner.py + judge prompt + config)
- `7e901f9e0` — feat(00-03): demo prompts + reports
