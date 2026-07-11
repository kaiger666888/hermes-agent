---
phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto
verified: 2026-07-10T21:30:00Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
---

# Phase 82: XCUT-04c Cost Tracking + XCUT-05 Lineage Auto Verification Report

**Phase Goal:** GLM-4.6V token spend is tracked alongside latency/success metrics with a CLI surface, and the 15-agent lineage bump is automated into a single script closing the v14.0 XCUT-05 deferral.
**Verified:** 2026-07-10T21:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth (from ROADMAP success criteria) | Status     | Evidence       |
| --- | ------------------------------------ | ---------- | -------------- |
| 1   | `dreamina_stats.py` MetricsBuffer tracks per-batch GLM-4.6V token spend (`input_tokens` + `output_tokens` + `estimated_cost_usd`) alongside existing per-task latency / success rate | ✓ VERIFIED | DreaminaTaskMetrics (dreamina_stats.py:81-85) has all 3 new fields with default=0 (backward compat). vision_verify._extract_usage (vision_verify.py:155-192) normalizes OpenAI SDK usage across all forms. dreamina_manager._compute_cost_usd (dreamina_manager.py:87-157) reads config + $3/$8 defaults. record_metric (dreamina_manager.py:236-249) writes all 3 token fields. |
| 2   | User can run `hermes glm stats` CLI subcommand to see monthly GLM-4.6V aggregate spend + per-stratum breakdown, reusing Rich table formatting from `hermes dreamina stats` | ✓ VERIFIED | dreamina_stats.py has register_glm_cli, _glm_command, _cmd_glm_stats, _aggregate_glm_metrics, _emit_glm_rich, _emit_glm_json (lines 295-477). __init__.py:84-102 registers `glm` CLI via ctx.register_cli_command. End-to-end dispatch test (no-sub → help/0, stats --json → valid JSON, stats --month filter → empty Rich table) passed. |
| 3   | User can run `python scripts/bump_all_agent_lineage.py` to automate the full 15-agent lineage bump (wraps `transform_skill_to_agent.py` + handles Track B 6 v13.0 P62 manual cases) | ✓ VERIFIED | bump_all_agent_lineage.py exists (672 lines). ACTIVE_EXPERTS_15 = 15 (9 Track A + 6 Track B). Track A delegates to transform_one (line 535). Track B uses transform_track_b_one (line 568). validate_all calls load_one_agent_yaml (line 601). main() exits 0 on full success, 1 on partial. Structure test passed: 15 == 9 + 6, A∩B = ∅. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py` | DreaminaTaskMetrics 3 new token fields + register_glm_cli + GLM CLI functions | ✓ VERIFIED | 479 lines. DreaminaTaskMetrics.input_tokens/output_tokens/estimated_cost_usd (lines 81-85, default=0). register_glm_cli (line 295), _glm_command (323), _cmd_glm_stats (335), _aggregate_glm_metrics (361), _emit_glm_rich (421), _emit_glm_json (471). __all__ includes register_glm_cli + _glm_command. |
| `/data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py` | _extract_usage helper + usage key in verify_image_content/verify_batch returns | ✓ VERIFIED | _extract_usage (line 155-192) handles prompt_tokens/input_tokens/dict/None. verify_image_content returns usage key (line 238 cache-hit 0/0, line 272 real). verify_batch returns usage per-image (line 322 cache-hit, line 371 real). |
| `/data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py` | _compute_cost_usd + usage capture in _generate_one_with_verify + record_metric token fields | ✓ VERIFIED | _compute_cost_usd (line 87-157) with config.yaml glm_46v.pricing + $3/$8 defaults (_DEFAULT_INPUT_USD_PER_1M=3.0, _DEFAULT_OUTPUT_USD_PER_1M=8.0). Usage captured in all 4 return paths (lines 376, 414, 437, 458). record_metric writes input_tokens + output_tokens + estimated_cost_usd (lines 246-248). |
| `/data/workspace/kais-hermes-skills/plugins/kais_aigc/__init__.py` | ctx.register_cli_command for "glm" namespace | ✓ VERIFIED | Lines 84-102 register glm CLI with setup_fn=register_glm_cli, handler_fn=_glm_command. Existing dreamina registration (lines 65-82) unchanged. |
| `/data/workspace/hermes-agent/scripts/bump_all_agent_lineage.py` | ACTIVE_EXPERTS_15 + bump_track_a + bump_track_b + validate_all + main | ✓ VERIFIED | 672 lines. ACTIVE_EXPERTS_15 (line 122) = TRACK_A_EXPERTS (9) + TRACK_B_EXPERTS (6). bump_track_a (512), bump_track_b (546), transform_track_b_one (353), validate_all (579), main (610). All 6 Track B persona builders + TRACK_B_TOOLS + TRACK_B_TRANSFORM_NOTES present. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| vision_verify.verify_image_content | dreamina_manager._generate_one_with_verify | usage dict in return value | ✓ WIRED | dreamina_manager.py:383 calls verify_image_content; line 397 extracts usage via `(vr or {}).get("usage", ...)` |
| dreamina_manager._generate_one_with_verify | dreamina_stats.record_metric | input_tokens + output_tokens + estimated_cost_usd in metric dict | ✓ WIRED | dreamina_manager.py:246-248 reads result["usage"]["input_tokens"] etc. and writes via record_metric |
| dreamina_stats.register_glm_cli | __init__.py ctx.register_cli_command | setup_fn=register_glm_cli, handler_fn=_glm_command | ✓ WIRED | __init__.py:86-102 imports both + registers with name="glm" |
| _glm_command | read_metrics | reads dreamina_stats.jsonl MetricsBuffer | ✓ WIRED | _cmd_glm_stats (line 337) calls read_metrics(_metrics_file()) |
| bump_all_agent_lineage.bump_track_a | transform_skill_to_agent.transform_one | calls transform_one for each Track A expert | ✓ WIRED | bump_all_agent_lineage.py:535 `data = transform_one(expert, skill_path)` |
| bump_all_agent_lineage.validate_all | agent.registry_loader.load_one_agent_yaml | validates all 15 YAMLs | ✓ WIRED | bump_all_agent_lineage.py:601 `load_one_agent_yaml(target)` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| dreamina_manager.batch_submit record_metric | result["usage"], result["estimated_cost_usd"] | vision_verify return + _compute_cost_usd | Yes — real GLM-4.6V API usage extracted from response | ✓ FLOWING |
| _emit_glm_rich / _emit_glm_json | monthly_data, stratum_data | _aggregate_glm_metrics(read_metrics(...)) | Yes — reads actual JSONL entries (or empty if no data) | ✓ FLOWING |
| bump_all_agent_lineage transform_track_b_one | data dict (18 fields) | KIAS_SKILLS_ROOT/<name>/SKILL.md parse | Yes — reads real SKILL.md files (test_all_15_have_skill_md verifies) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Backward compat: DreaminaTaskMetrics without token fields | `python -c "from plugins.kais_aigc.dreamina_stats import DreaminaTaskMetrics; m = DreaminaTaskMetrics(submit_id='x', stratum='1-ref', latency_ms=100, success=True, retries=0, vision_verified=False, ts='2026-07-10T00:00:00Z'); print(m.input_tokens, m.output_tokens, m.estimated_cost_usd)"` | "0 0 0.0" | ✓ PASS |
| Explicit token fields constructible | (same script, m2 with input_tokens=100, output_tokens=50, estimated_cost_usd=0.0007) | "100 50 0.0007" | ✓ PASS |
| _aggregate_glm_metrics monthly + stratum + legacy | Synthetic 3-entry list (2 with tokens, 1 legacy) | monthly={2026-06, 2026-07}, 2026-07 sum=300/150/0.003, no_token_count=1 | ✓ PASS |
| _glm_command dispatch (no-sub/stats-json/month-filter) | argparse mock + read_metrics patch | no-sub → help+rc0; stats --json → {"monthly":{},"stratum":{}} + rc0; stats --month=2026-07 → empty Rich table + rc0 | ✓ PASS |
| _compute_cost_usd default pricing | `_compute_cost_usd(1000000, 0)` and `_compute_cost_usd(0, 1000000)` | 3.0 and 8.0 ($3/$8 per 1M) | ✓ PASS |
| ACTIVE_EXPERTS_15 structure | `python -c "...from bump_all_agent_lineage import ACTIVE_EXPERTS_15, TRACK_A_EXPERTS, TRACK_B_EXPERTS; assert len(ACTIVE_EXPERTS_15)==15 and len(TRACK_A_EXPERTS)==9 and len(TRACK_B_EXPERTS)==6 and len(set(TRACK_A_EXPERTS)&set(TRACK_B_EXPERTS))==0"` | passes | ✓ PASS |
| Track 1 tests (kais_aigc) | `cd kais-hermes-skills && .venv/python -m pytest plugins/kais_aigc/tests/{test_dreamina_stats,test_vision_verify,test_dreamina_manager}.py -q` | 50 passed in 0.76s | ✓ PASS |
| Track 2 tests (bump script) | `python -m pytest tests/agent/test_bump_all_agent_lineage.py -q` | 46 passed in 1.68s | ✓ PASS |

### Probe Execution

No probes declared for this phase (not a migration/tooling phase). Step 7c SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| XCUT-04c-INSTRUMENT | 82-01-PLAN | dreamina_stats.py MetricsBuffer tracks per-batch GLM-4.6V token spend (input_tokens + output_tokens + estimated_cost_usd) alongside existing per-task latency/success rate | ✓ SATISFIED | DreaminaTaskMetrics 3 new fields + vision_verify usage extraction + dreamina_manager capture + record_metric writing. All wired end-to-end. |
| XCUT-04c-CLI | 82-02-PLAN | User can run `hermes glm stats` CLI subcommand (monthly aggregate + per-stratum breakdown, Rich table) | ✓ SATISFIED | register_glm_cli + _glm_command + _aggregate_glm_metrics + _emit_glm_rich + _emit_glm_json. CLI registered in __init__.py via ctx.register_cli_command. --json + --month flags work. |
| XCUT-05-AUTO | 82-03-PLAN | User can run `python scripts/bump_all_agent_lineage.py` to automate full 15-agent lineage bump | ✓ SATISFIED | bump_all_agent_lineage.py with ACTIVE_EXPERTS_15 (9+6), Track A delegates to transform_one, Track B uses transform_track_b_one, validate_all via load_one_agent_yaml, main() exit 0/1. |

No orphaned requirements found — all Phase 82 requirement IDs in REQUIREMENTS.md are claimed by plans and verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers in any of the 5 modified files. No stub returns, no empty implementations, no hardcoded empty data flowing to render. |

### Human Verification Required

None. All 3 success criteria are programmatically verifiable and were verified via test runs, behavioral spot-checks, and data-flow tracing. The CLI surface (`hermes glm stats`) is invoked through the plugin registration pattern that is already proven by the existing `hermes dreamina stats` subcommand — the operator invocation of `hermes glm stats` at the shell is a mechanical corollary of the verified registration, not a separate behavioral risk.

### Gaps Summary

No gaps found. All 3 roadmap success criteria verified with substantive code (no stubs), complete wiring (all key links connected), and flowing data (real token usage extracted from API responses + real SKILL.md content read by bump script). 96/96 tests pass (50 Track 1 + 46 Track 2). Backward compatibility preserved (DreaminaTaskMetrics without token fields yields 0/0/0.0 defaults). No debt markers, no orphaned requirements, no deferred items.

The pre-existing `test_canvas_sync_integration.py::test_save_v2_bodies_carry_phase_node_ids` failure noted in deferred-items.md is OUT of Phase 82 scope (canvas sync subsystem, verified pre-existing via git stash, unrelated to cost tracking or lineage bump).

---

_Verified: 2026-07-10T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
