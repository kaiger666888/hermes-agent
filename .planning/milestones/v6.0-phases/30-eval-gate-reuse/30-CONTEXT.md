# Phase 30: Eval Gate Reuse - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Any candidate patch to a bundled movie-expert skill (unified diff file) can be automatically scored against the existing v5.0 baseline using the existing `_eval/runner.py` MT-Bench position-swap harness. Patches whose mean score drops more than δ (default 0.3) below baseline are REJECTED at the gate; patches with any single-prompt regression > 1.0 are REJECTED even if mean is acceptable. Statistical-significance A/B report emitted per patch.

Covers requirements GATE-01..04. **Hermes-core touch: No** — `_eval/` is offline developer tooling per its module docstring ("OFFLINE DEVELOPER TOOLING... not imported by the Hermes runtime and does not call `registry.register`"). Pure eval-tooling extension.

**Parallel-eligible with Phase 31** (EVOL): P30 extends `skills/movie-experts/_eval/runner.py` + adds gate scripts; P31 builds patch-generation pipeline. They share only the JSON schema contract from P28. Zero file overlap.

</domain>

<decisions>
## Implementation Decisions

### Patch Input Format (GATE-01)
- **Unified diff file** (`.patch` / `.diff`) — candidate patch enters the gate as a unified diff. Gate applies it temporarily via `git apply --check` (validation) + `git apply` (actual), runs the eval, then reverts via `git apply -R` or `git checkout -- <files>`.
- Matches `git format-patch` / `git apply` conventions; compatible with Phase 31's EVOL diff generator (which emits unified diffs).
- In-memory patch dict and git branch ref rejected — former couples to EVOL internals, latter couples to git workflow and is harder to test.

### Baseline Source (GATE-01)
- **Use existing v5.0 baseline** from `skills/movie-experts/_eval/baseline/` — snapshot captured at v5.0 close (Phase 27). Gate uses cached baseline scores; lazy-populates on first run if missing.
- `--rebuild-baseline` CLI flag forces a fresh baseline run (operator-initiated, ~30 min for full benchmark).
- Re-run-each-time rejected — doubles LLM calls per patch (cost prohibitive). FeedbackStore baseline rejected — conflates feedback storage with eval baseline (messy separation).

### Threshold Configuration (GATE-02, GATE-04)
- **`_eval/gate_config.yaml`** — per-gate config file at `skills/movie-experts/_eval/gate_config.yaml`:
  ```yaml
  delta_threshold: 0.3         # Mean score drop allowed (4-point rubric)
  per_prompt_threshold: 1.0    # Max single-prompt regression
  min_prompts: 5               # Validity floor — patches scored on <N prompts rejected as inconclusive
  ab_positions: 2              # Position-swap rounds (1 = no swap, 2 = swap baseline/candidate)
  judge_model: "claude-sonnet-4-6"  # Override of _eval/runner.py default
  ```
- CLI flags override config: `--threshold-delta 0.3 --per-prompt-threshold 1.0 --min-prompts 5`.
- Defaults documented in `_eval/gate_config.yaml.example` (committed; actual `gate_config.yaml` is operator-local, not committed if it diverges).

### A/B Double-Blind Scope (GATE-03)
- **Reuse existing benchmark prompts** from `skills/movie-experts/_eval/prompts/` (MT-Bench position-swap set, ~20-30 prompts across skill domains).
- A/B comparison: run baseline + candidate on same prompt set with position swapping (2 rounds — baseline-first, candidate-first). LLM judge scores both blind.
- Statistical-significance report emitted at `skills/movie-experts/_eval/reports/<patch_id>.json` with: mean scores, per-prompt deltas, paired t-test p-value, verdict (`pass` / `fail_mean` / `fail_regression` / `inconclusive`).
- Expanding benchmark 2x is OUT OF SCOPE for P30 (future work). Full keyword scan is OUT OF SCOPE (too slow for automated gate).

### Gate CLI Surface

```bash
# Run gate on a candidate patch
hermes-skill-gate --patch candidate.patch --skill screenplay
# OR via direct script:
python skills/movie-experts/_eval/gate.py --patch candidate.patch --skill screenplay

# Force baseline rebuild
python skills/movie-experts/_eval/gate.py --rebuild-baseline --skill screenplay

# Override thresholds
python skills/movie-experts/_eval/gate.py --patch c.patch --skill drawer --threshold-delta 0.2
```

- Exit code: 0 = pass, 1 = fail_mean, 2 = fail_regression, 3 = inconclusive (too few prompts).
- Rejects logged to `skills/movie-experts/_eval/reports/<patch_id>.reject.json` with full score delta breakdown.

### Claude's Discretion
- Patch ID generation — Claude's call (recommend `f"{skill_id}_{ts_unix}_{sha256[:8]}"` for traceability).
- Revert strategy — `git apply -R` is cleaner but requires the patch file path; `git checkout -- <files>` is simpler if the patch touches one file. Plan-phase picks based on simplicity.
- Cache invalidation — baseline cache invalidated when `_eval/baseline/` sha256 changes OR when `_eval/prompts/` changes. Plan-phase decides exact mechanism.
- Report format versioning — start at `schema_version: 1`; bump on breaking changes.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/movie-experts/_eval/runner.py:1-400+` (v1 MT-Bench harness) — REUSE per GATE-01. Phase 30 extends (does NOT fork) with patch-vs-baseline mode.
- `skills/movie-experts/_eval/snapshot.py:1-200+` — EXPERT_DIRS, sha256 + git sha + ISO 8601 provenance. Direct reuse for patch verification (sha256 of patched file vs baseline).
- `skills/movie-experts/_eval/baseline/` — existing v5.0 baseline snapshots. Per-skill subdirs with cached scores.
- `skills/movie-experts/_eval/prompts/` — MT-Bench position-swap prompt set.
- `skills/movie-experts/_eval/judge_prompt.md` — LLM-as-judge prompt template.
- `skills/movie-experts/_eval/config.yaml.example` — existing eval config; Phase 30 adds `gate_config.yaml.example` alongside.

### Established Patterns
- stdlib-only constraint per `_eval/snapshot.py:14` — "stdlib only (no third-party packages)". Phase 30 honors this for new code (json, statistics, subprocess, pathlib).
- `argparse` for CLI — matches existing `_eval/snapshot.py` + `_eval/runner.py` patterns.
- pytest tests under `skills/movie-experts/_eval/tests/` — matches existing `test_runner.py` + `test_snapshot.py`.
- `encoding="utf-8"` on every `open()` — Ruff PLW1514.
- `from __future__ import annotations` — forward compat.

### Integration Points
- **Input:** Phase 31 EVOL pipeline emits candidate patches as `.patch` files → Phase 30 gate scores them → reject/pass verdict returned to EVOL for queue routing.
- **Output:** Gate reports at `_eval/reports/<patch_id>.json` consumed by Phase 31 review queue UI + Phase 32 Curator audit trail.
- **Hermes runtime:** ZERO integration — `_eval/` is offline tooling. No `registry.register`, no agent runtime imports.

</code_context>

<specifics>
## Specific Ideas

- The gate MUST be deterministic for a given patch + baseline + judge_model — same input produces same verdict. Random judge order is forbidden; position-swap rounds are explicit (ab_positions: 2 = two rounds, baseline-first then candidate-first).
- The "inconclusive" exit code (3) is for cases where < `min_prompts` prompts succeeded (e.g., LLM API failures mid-run). Operators see a clear "rerun with --rebuild-baseline" suggestion.
- Rejection logs at `_eval/reports/<patch_id>.reject.json` MUST include: per-prompt scores (baseline + candidate), deltas, paired-t p-value, threshold values used, judge_model, ts. Enough for operator to tune thresholds OR override rejection manually if needed.
- The gate is INVOKED BY Phase 31 (EVOL) and Phase 32 (Curator) — it does NOT run on its own. P30 ships the tool; downstream phases consume it.

</specifics>

<deferred>
## Deferred Ideas

- **Multi-judge ensemble** — FUTURE-V6-05 per STATE.md risks. v6 uses single-judge (matching v1 harness); multi-judge ensemble deferred.
- **Benchmark expansion** — Adding new MT-Bench prompts is future work. P30 ships with existing prompt set only.
- **Patch auto-tuning** — If a patch fails by small margin, gate could suggest "loosen threshold to X" — out of scope, operators tune manually.
- **Cross-skill patch validation** — A patch touching multiple skills (e.g., shared refs change) needs special handling. P30 assumes single-skill patches; multi-skill patches validated by running gate per-skill (operator's responsibility).
- **Live patch evaluation** — Running gate on a live skill (not via diff) is out of scope. Gate is patch-vs-baseline only.
- **Statistical power analysis** — Computing required N for significance is future work. v6 uses fixed prompt set.

</deferred>
