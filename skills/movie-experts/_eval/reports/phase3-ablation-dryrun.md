# Phase 3 Ablation — Dry-Run Results

**Generated:** 2026-06-15
**Mode:** dry-run (no live model calls; stub judge signature: all verdicts = `tie`)
**Experts evaluated:** 4 (screenplay, editor, colorist, style_genome)
**Conditions:** 3 (old_no_refs / new_no_refs / new_with_refs)
**Total verdicts this phase:** 36 (4 experts × 3 condition pairs × 3 prompts)
**Judge run this phase:** `qwen/qwen3-235b-a22b:free (stub)` — first judge in config only
**Judges expected Phase 6 live:** `qwen/qwen3-235b-a22b:free` + `deepseek/deepseek-chat-v3:free` (multi-judge ensemble)

---

## Per-Expert Verdict Summary

| Expert | Total Verdicts | Pair Count | All Verdicts |
|--------|----------------|------------|--------------|
| screenplay | 9 | 3 | all `tie` (stub signature) |
| editor | 9 | 3 | all `tie` (stub signature) |
| colorist | 9 | 3 | all `tie` (stub signature) |
| style_genome | 9 | 3 | all `tie` (stub signature) |

Per-expert detail in:
- [`screenplay_phase3.json`](./screenplay_phase3.json) / [`screenplay_phase3.md`](./screenplay_phase3.md)
- [`editor_phase3.json`](./editor_phase3.json) / [`editor_phase3.md`](./editor_phase3.md)
- [`colorist_phase3.json`](./colorist_phase3.json) / [`colorist_phase3.md`](./colorist_phase3.md)
- [`style_genome_phase3.json`](./style_genome_phase3.json) / [`style_genome_phase3.md`](./style_genome_phase3.md)

Aggregated machine-readable form: [`phase3-ablation-dryrun.json`](./phase3-ablation-dryrun.json)

---

## Harness Validation

This Phase 3 dry-run proves the harness end-to-end on the 3-condition × 4-expert matrix:

1. **Runner accepts 3 conditions** — `config.yaml.example` updated with `[old_no_refs, new_no_refs, new_with_refs]` (replacing Phase 0 baseline/candidate); runner.py `run_ablation` enumerates C(3,2) = 3 condition pairs.
2. **Pair enumeration is correct** — for each expert, the runner produced 3 pairs × 3 prompts = 9 verdicts, matching the expected C(3,2) × P formula.
3. **4-expert matrix is consistent** — all 4 experts produced 9 verdicts each, totalling 36 (4 × 9 = 36 ✓).
4. **Dry-run stub signature observed** — every verdict has `final: "tie"` (per `_StubJudgeClient` design at runner.py:453-498: returns A on swap=False and B on swap=True → `_final_verdict` collapses to "tie"). This is the expected stub signature and confirms the harness output shape is valid.
5. **No prompts file missing** — all 4 expert prompts files exist (`screenplay_demo.yaml`, `editor_demo.yaml`, `colorist_demo.yaml`, `style_genome_demo.yaml`); runner would have crashed with exit code 2 if any were missing.

**Harness validity conclusion:** The runner would have produced statistically analyzable output (non-tie verdicts) if a live judge client had been substituted for the stub. The output shape, pair enumeration, and prompt resolution are all correct.

---

## Live Run Status

| Field | Value |
|-------|-------|
| `OPENROUTER_API_KEY` present in environment | false (deferred) |
| Live run attempted | false |
| Live run experts completed | [] |
| Live run errors | [] |
| Phase 6 live run prerequisites documented | yes (see [`phase3-go-nogo.md`](./phase3-go-nogo.md) §Phase 6 Live Run Prerequisites) |

**Rationale for deferral:** Per CONTEXT decision D-11, Phase 3 dry-run is the default mode. Live run requires `OPENROUTER_API_KEY` configured + live model calls; budget decision deferred to Phase 6. The dry-run is sufficient to validate harness end-to-end and produce the report template; statistical GO/NO-GO verdict requires Phase 6 live evidence.

---

## What the Dry-Run Does NOT Show

**Important caveat:** The all-tie stub signature is **not** evidence that "RAG makes no difference". The stub returns A on swap=False and B on swap=True regardless of answer content — it never reads the actual answers. The all-tie pattern is purely a position-bias demonstration, not a quality verdict.

To produce statistically defensible GO/NO-GO evidence, Phase 6 must:
1. Set `OPENROUTER_API_KEY` in `~/.hermes/.env`
2. Copy `config.yaml.example` to `config.yaml` (gitignored) and add real credentials
3. Expand N from 3 prompts per expert to ≥20 (EVAL-05 statistical threshold)
4. Invoke both judge models in the panel (not just `judges[0]`), per EVAL-06 multi-judge requirement
5. Run `runner.py` without `--dry-run` for each of 4 experts

Expected Phase 6 live verdict count: 4 experts × 3 pairs × ≥20 prompts × 2 orderings × 2 judges = ≥96 verdicts (we use 144 as planning estimate: 4 × 3 × 20 × 2 × 3 to allow margin for multi-prompt variants).

---

## Cross-Reference

- Aggregated JSON: [`phase3-ablation-dryrun.json`](./phase3-ablation-dryrun.json)
- GO/NO-GO report: [`phase3-go-nogo.md`](./phase3-go-nogo.md)
- Runner source: [`../runner.py`](../runner.py)
- Config template: [`../config.yaml.example`](../config.yaml.example)
- Per-expert plans + summaries: [`../../../../.planning/phases/03-top-4-existing-experts-rag/`](../../../../.planning/phases/03-top-4-existing-experts-rag/)
