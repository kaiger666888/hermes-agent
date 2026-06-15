---
status: partial
phase: 06-full-eval-bilingual-readme
source: [06-SUMMARY.md]
started: 2026-06-15T15:14:35Z
updated: 2026-06-15T15:15:30Z
---

## Current Test

[testing paused — 10 items outstanding]

User redirected from verify-work to /gsd-complete-milestone at Test 1
before any checkpoint was answered. Tests below were generated but not
verified. Resume via `/gsd-verify-work 6` if milestone sign-off later
requires acceptance evidence.

## Tests

### 1. Top-level README published and substantive
expected: `skills/movie-experts/README.md` exists, is well-formed markdown, renders as a coherent document (>5KB). H1 + opening paragraphs describe the v1/v1.5 expert suite and RAG-augmented core value.
result: [pending]

### 2. Expert inventory table complete
expected: README contains a markdown table listing every v1 expert with columns for Expert / Chinese Name / Role / Refs. Count matches the v1.5 deliverable scope (18 experts: 14 original + 4 new — compliance_marketing, hook_retention, cinematographer, production).
result: [pending]

### 3. Production DAG collaboration graph present
expected: README contains an ASCII / visual DAG showing expert relationships (root, downstream edges, bottleneck/audit nodes). Captures the production pipeline from style_genome → final output.
result: [pending]

### 4. RAG usage guide section
expected: README has a "RAG Usage Guide" section documenting three paths: (a) static refs as default authoritative source, (b) optional memory plugin invocation, (c) provider-agnostic invocation as a hard constraint. Should NOT hardcode a single provider's tool name.
result: [pending]

### 5. Live-run procedure documented (EVAL-04 deferral)
expected: README contains a 6-step operator procedure for executing the Phase 6 live eval: (1) configure API key, (2) copy config.yaml.example → config.yaml, (3) expand prompts ≥20 per expert, (4) multi-judge ensemble, (5) execute per-expert runs, (6) aggregate + apply GO criteria. Steps are concrete shell commands or copy-pasteable instructions.
result: [pending]

### 6. Phase 3 dry-run + GO/NO-GO referenced
expected: README links to `_eval/reports/phase3-ablation-dryrun.md` and `_eval/reports/phase3-go-nogo.md`. Both target files exist and contain the 36-verdict dry-run summary + CONDITIONAL GO status.
result: [pending]

### 7. Bilingual consistency section
expected: README has a "Bilingual Consistency" section documenting: (a) EN↔CN glossary at `_shared/glossary.md`, (b) the format convention (EN frontmatter + EN structure + CN prose), (c) results of the Phase 6 manual spot-check (canonical CN terms used, metric IDs preserved, expert_id values frozen).
result: [pending]

### 8. File layout tree present
expected: README contains a tree view of `skills/movie-experts/` showing each expert directory + `_eval/` + `_shared/` and key files. Tree should match what's actually on disk (18 expert dirs, runner.py, config.yaml.example, prompts/, baseline/, reports/).
result: [pending]

### 9. Deferred work explicitly listed
expected: README (or linked SUMMARY) explicitly documents deferred items: live-run execution, N≥20 prompt expansion, multi-judge ensemble invocation, full bilingual lint pass, and any others. Operator reading the README can tell what's done vs deferred without reading STATE.md.
result: [pending]

### 10. SUMMARY.md reflects current v1.5 state
expected: `.planning/phases/06-full-eval-bilingual-readme/06-SUMMARY.md` accurately reflects what shipped. Specifically, the "17-expert" framing in the SUMMARY's Objective paragraph should be reconciled with the README's "18-expert v1.5 complete" claim, OR the discrepancy should be explained (SUMMARY was written before Phase 5 v1.5 finished).
result: [pending]

## Summary

total: 10
passed: 0
issues: 0
pending: 10
skipped: 0

## Gaps

[none yet]
