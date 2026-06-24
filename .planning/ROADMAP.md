# Roadmap: v6.0 — Self-Evolution & Feedback Loop

**Milestone:** v6.0 — Self-Evolution & Feedback Loop
**Started:** 2026-06-24
**Predecessor:** v5.0 kais-movie-agent V8.6 Adaptation (shipped 2026-06-19, 30/30 reqs, audit PASSED)
**Phase numbering:** Continues from v5.0 (which ended at Phase 27). v6.0 phases start at Phase 28. NOT reset.

**Core functional guarantee:** 每个 movie-expert skill 在给出意见后,都能接收到调用者的反馈,反馈经 eval-gated pipeline 驱动 SKILL.md / refs 持续改进。

**Paradigm shift (v5→v6):** From static knowledge curation to feedback-driven self-learning. **Scope expansion:** v6 (unlike v1-v5) DOES modify Hermes core (`agent/curator.py` extension + new feedback ingestion infrastructure). Pure-skill phases still occur (e.g. SKILL.md body patches teaching experts to REQUEST feedback), but core code touch is unavoidable per CURATE-01.

**Granularity:** standard (target 5-7 phases, 3-6 requirements per phase)
**Coverage:** 26 / 26 v1 requirements mapped (100%)

---

## Previous Milestones (archive)

- ✅ **v1 — Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15) — [Full archive](./milestones/v1-ROADMAP.md)
- ✅ **v2.0 PRFP — Pipeline Redesign from First Principles** — Phases 7-12 (shipped 2026-06-16) — design suite at `.planning/research/v2-pipeline-design/`
- ✅ **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (shipped 2026-06-17) — [Full archive](./milestones/v3.0-ROADMAP.md) · [Audit](./milestones/v3.0-MILESTONE-AUDIT.md)
- ✅ **v4.0 Methodology Backfill** — Phases 19-21 (shipped 2026-06-18) — [Full archive](./milestones/v4.0-ROADMAP.md) · [Audit](./milestones/v4.0-MILESTONE-AUDIT.md)
- ✅ **v5.0 kais-movie-agent V8.6 Adaptation** — Phases 22-27 (shipped 2026-06-19) — [Full archive](./milestones/v5.0-ROADMAP.md) · [Audit](./milestones/v5.0-MILESTONE-AUDIT.md)

---

## Phases

- [ ] **Phase 28: Feedback Ingestion MVP** - 多源反馈采集 (CLI / kais-aigc-platform / 手工) + 标准化 schema;核心功能担保落地
- [ ] **Phase 29: Feedback Store** - `~/.hermes/skills/.feedback/` 持久化 + 时间衰减权重 + 去重 + 索引
- [ ] **Phase 30: Eval Gate Reuse** - 扩展既有 `_eval/runner.py` 为 patch-vs-baseline gate + A/B 双盲 + regression detection
- [ ] **Phase 31: Knowledge Evolution Pipeline** - 反馈→候选知识点→候选 patch→review queue→human-in-loop approve→apply/rollback
- [ ] **Phase 32: Curator Upgrade + Audit** - 扩展 `agent/curator.py` 作用域到 bundled skill + patch audit log + operator CLI + 半自动路径
- [ ] **Phase 33: Observability + Integration Close-out** - per-skill dashboard + cross-skill view + source breakdown + canonical architecture doc + skills-mapping.yaml v6 sign-offs + README/glossary close-out

---

## Phase Details

### Phase 28: Feedback Ingestion MVP

**Goal:** Users (CLI operators + kais-aigc-platform审核系统 + 手工标注者) can submit structured feedback against any movie-expert output, and all feedback lands in a single normalized schema ready for downstream storage and learning.
**Depends on:** Nothing (first phase — core functional guarantee ships here)
**Requirements:** INGEST-01, INGEST-02, INGEST-03, INGEST-04, INGEST-05
**Success Criteria** (what must be TRUE):
  1. Operator can submit feedback inside a Hermes CLI conversation against any movie-expert output — verdict (`good` / `needs_work` / `bad`) + free-text correction + optional revised output are accepted and persisted to disk
  2. kais-aigc-platform review feedback (verdict + retry signal + modification diff) is ingestible via at least ONE of: file exchange / HTTP endpoint / webhook — concrete path chosen at plan-phase, but end-to-end ingest from a kais-aigc-platform-shaped source works
  3. A manual-labeling CLI subcommand supports batch import of historical outputs + labels (cold-start / baseline construction path works on ≥10 sample outputs)
  4. All three sources (CLI / kais-aigc / manual) emit the SAME JSON schema with fields `skill_id, expert_id, source, verdict, correction, output_snapshot, ts` — schema validation rejects malformed payloads with a clear error
  5. Every feedback record carries `output_snapshot` with the original LLM output sha256 + prompt + model + params metadata — enough to reproduce and dedupe later
**Scope note:** This is the must-have MVP. The exact kais-aigc接入方式 (file/HTTP/webhook) is a plan-phase decision, not a roadmap decision. The phase MUST ship a working ingest path; the choice of transport is not allowed to block the phase.
**Hermes-core touch:** Yes — new feedback-ingestion entrypoints / CLI subcommands / watchers under `~/.hermes/skills/.feedback/` ingest path. Not a pure-skill phase.
**Plans:** 1/2 plans executed
- [x] 28-01-PLAN.md — Feedback schema (FeedbackRecord + OutputSnapshot + validators) + snapshot capture + atomic write path (foundation)
- [ ] 28-02-PLAN.md — /feedback slash command + hermes feedback {import,watch,submit} CLI + kais file watcher + JSONL batch import (three ingest sources)

### Phase 29: Feedback Store

**Goal:** All ingested feedback persists durably, is queryable by Curator and dashboards, decays in weight over time, and is deduplicated so the same output snapshot cannot skew the learning signal.
**Depends on:** Phase 28 (needs the normalized schema + ingest path)
**Requirements:** STORE-01, STORE-02, STORE-03, STORE-04
**Success Criteria** (what must be TRUE):
  1. `~/.hermes/skills/.feedback/` directory exists with `skill_id/source/` sub-directory layout; feedback records append as jsonl files (one file per skill_id+source bucket)
  2. An `index.json` file is queryable by `skill_id` / `verdict` / `source` / `timestamp` — both the Curator (Phase 32) and dashboard (Phase 33) consume this single index, not parallel ad-hoc scans
  3. Feedback older than N days (default 90, configurable in `config.yaml`) is marked with reduced weight in the index — `weighted_count` differs from raw `count` for old buckets, so downstream aggregation honors decay
  4. Duplicate detection works: a second feedback with identical `output_snapshot.sha256` AND identical `verdict` is NOT double-counted; a second feedback with same sha256 but DIFFERENT verdict demotes the older record's weight (treated as a correction, not a fresh signal)
**Hermes-core touch:** Yes — new persistence layer under `~/.hermes/skills/.feedback/`. Pure data plumbing, no bundled-SKILL.md changes.
**Plans:** TBD

### Phase 30: Eval Gate Reuse

**Goal:** Any candidate patch to a bundled movie-expert skill can be automatically scored against the baseline using the existing `_eval/runner.py` MT-Bench position-swap harness, with clear pass/fail thresholds and regression guards — before the patch ever reaches a human reviewer.
**Depends on:** Phase 29 (needs stored `output_snapshot` baselines) — but the eval-gate CODE itself is disjoint from STORE code and can be developed in parallel
**Parallel-eligible with:** Phase 31 (EVOL) — disjoint file ownership: P30 extends `skills/movie-experts/_eval/runner.py` + adds gate scripts; P31 builds the patch-generation pipeline. They share only the JSON schema contract from P28.
**Requirements:** GATE-01, GATE-02, GATE-03, GATE-04
**Success Criteria** (what must be TRUE):
  1. A candidate patch enters the gate by calling `_eval/runner.py` (or a thin wrapper) in patch-vs-baseline mode on the existing benchmark prompts — no new harness is built, the v1 MT-Bench position-swap code is REUSED
  2. A patch whose mean score across benchmark prompts drops more than δ (default 0.3 on the 4-point rubric, configurable) below baseline is REJECTED at the gate and never enters the review queue — rejection is logged with score delta
  3. A/B double-blind comparison tool runs candidate patch vs baseline on the same prompt set with position swapping and emits a statistical-significance report (not just a raw score)
  4. Regression detection rejects the patch if ANY single prompt's score drops more than the per-prompt threshold (default 1.0) — even if the mean is acceptable, single-prompt regressions block merge
  5. **v5/v4 refs byte-intact check:** This phase touches only `_eval/runner.py` extension + new gate scripts — no changes to any bundled SKILL.md or `references/*.md` bytes (verified by sha256 snapshot diff against v5.0 close state)
**Hermes-core touch:** No — `_eval/` is offline developer tooling (per runner.py docstring: "This module is OFFLINE DEVELOPER TOOLING. It is not imported by the Hermes runtime and does not call `registry.register`"). Pure eval-tooling extension.
**Plans:** TBD

### Phase 31: Knowledge Evolution Pipeline

**Goal:** Accumulated feedback is transformed into candidate patches (unified diffs against SKILL.md / `references/*.md`) that an operator can review, approve, and apply with full rollback — closing the self-learning loop.
**Depends on:** Phase 29 (STORE — needs accumulated feedback) + Phase 30 (GATE — patches must pass eval before entering review queue)
**Requirements:** EVOL-01, EVOL-03, EVOL-04, EVOL-05
**Success Criteria** (what must be TRUE):
  1. An LLM-based aggregation pass reads accumulated feedback for a skill, identifies common "what should improve" themes, and emits structured candidate insights — each insight carries an evidence chain pointing to the specific feedback IDs that motivated it
  2. A patch review queue exists where the operator can inspect each pending patch with: source feedback chain, LLM extraction rationale, list of affected skills, and the eval-gate score from Phase 30
  3. **Every bundled movie-expert skill patch requires operator approval before apply** — the human-in-loop gate is non-bypassable for bundled skills (agent-created skills may take the semi-automatic path per Phase 32 CURATE-05, but bundled skills NEVER auto-apply)
  4. Patch apply performs an automatic git-commit with feedback IDs + eval score in the commit message; a rollback sub-command restores any historical version from the audit trail
  5. **FOUND-08 preservation check:** Every applied patch preserves the expert_id and related_skills frontmatter of the target SKILL.md byte-for-byte (no new expert_id created, no DAG node rewired) — verified per-patch before commit
  6. **v5/v4 refs byte-intact check (additive-only):** Patches to v4.0 methodology refs (snowflake-method.md / e-konte-format.md / scamper-variations.md) and v5.0 refs (dreamina-cli-baseline.md / v86-pipeline-mapping.md) are ADDITIVE only — existing bytes preserved, new knowledge appended alongside (mirrors v4.0 + v5.0 scope discipline)
**Hermes-core touch:** Mixed — pipeline orchestration code is new (under `~/.hermes/skills/.feedback/` tooling or a new module), but the patches it produces target bundled SKILL.md / refs (additive only). The git-commit + rollback machinery touches repo state.
**Plans:** TBD

### Phase 32: Curator Upgrade + Audit

**Goal:** The Curator (currently limited to archiving agent-created skills) gains the ability to scan accumulated feedback, produce candidate patches against bundled movie-expert skills via the EVOL-02 generator, log every action to a tamper-evident audit trail, and expose operator CLI commands for queue management — with a semi-automatic path for high-confidence agent-created skill patches.
**Depends on:** Phase 31 (needs the EVOL review queue + apply machinery) + Phase 29 (needs STORE for the feedback scan)
**Requirements:** CURATE-01, CURATE-02, CURATE-03, CURATE-04, CURATE-05, EVOL-02
**Success Criteria** (what must be TRUE):
  1. `agent/curator.py` `run_curator_review` scope is extended — when accumulated negative feedback for a bundled skill crosses the threshold (default ≥3 `needs_work`/`bad` across ≥2 sessions, configurable), the Curator automatically triggers the EVOL pipeline (using the EVOL-02 unified-diff generator) to produce candidate patches that land in the Phase 31 review queue (still subject to human-in-loop approve per EVOL-04)
  2. The EVOL-02 candidate-patch generator (knowledge point → unified diff against SKILL.md / `references/*.md`, preserving EN-structure + CN-prose bilingual style) is implemented and invoked by the Curator's proposal path
  3. Every patch action (propose / approve / reject / apply / rollback) is recorded in `~/.hermes/skills/.audit/` with operator identity, timestamp, associated feedback IDs, eval score, and git commit sha — the log is append-only and queryable
  4. Operator commands `hermes curator queue` (list pending patches), `hermes curator approve <id>`, and `hermes curator reject <id> <reason>` work end-to-end against the audit-backed queue
  5. Agent-created skills can take a semi-automatic path: when eval gate passes AND confidence score ≥ threshold (default 0.8), a patch may auto-apply (still writes audit log); this behavior is globally toggleable via config (default follows PROJECT.md MVP boundary — bundled NEVER auto, agent-created conditional)
  6. **Existing Curator behavior preserved:** The pre-v6 deterministic inactivity transitions + consolidation pass continue to work unchanged for agent-created skills — the bundled-skill proposal capability is ADDITIVE, not a replacement (regression test against pre-v6 curator behavior required)
**Hermes-core touch:** Yes — direct modification of `agent/curator.py` (extending `run_curator_review` + new proposal path) + implementation of the EVOL-02 diff generator. This is the unavoidable scope expansion flagged in PROJECT.md.
**Plans:** TBD

### Phase 33: Observability + Integration Close-out

**Goal:** Operators can observe feedback-driven learning health per-skill and across the whole movie-experts suite, and the v6.0 milestone ships a canonical architecture doc + skills-mapping sign-off + README/glossary close-out mirroring the v5.0 Phase 27 pattern.
**Depends on:** Phase 28-32 all complete (needs the full feedback loop running to surface meaningful stats)
**Requirements:** OBS-01, OBS-02, OBS-03 (+ integration close-out deliverables, no separate REQ-IDs)
**Success Criteria** (what must be TRUE):
  1. `hermes curator stats [skill_id]` emits a per-skill dashboard: feedback counts bucketed by verdict, patch history, eval score trend over the most recent N runs — operator can read skill health at a glance
  2. `hermes curator stats --all` emits a cross-skill view: which skills received the most negative feedback, which patches produced the largest score uplift, which skills have gone long stretches with zero feedback (a prompt-coverage-gap signal)
  3. A source breakdown view shows feedback volume + verdict distribution by source (CLI / kais-aigc-platform / manual) — operator can verify whether the kais-aigc-platform integration from Phase 28 is actually producing data
  4. **Canonical architecture doc:** `_shared/v6-feedback-loop-architecture.md` is written, documenting the full feedback loop (ingest → store → gate → evolve → curate → observe) with data flow diagrams, the JSON schema, the eval-gate thresholds, and the human-in-loop boundaries — mirrors the v5.0 `v86-pipeline-mapping.md` close-out pattern
  5. **skills-mapping.yaml v6 sign-offs:** A new `v6_ref_signoffs:` section is added (mirrors v4.0 `v4_ref_signoffs:` + v5.0 `v5_ref_signoffs:` schema) with entries for the new `_shared/v6-feedback-loop-architecture.md` ref, each carrying `verified_date` / `source` / `license_status`
  6. **README + glossary close-out:** `skills/movie-experts/README.md` corpus tree updated to list the new v6 ref; glossary gains H3 entries for the 4 new v6 terms (Feedback Ingestion / Knowledge Evolution / Eval Gate / Curator Proposal) following the bilingual `### Term / 中文术语` convention
  7. **FOUND-08 milestone-wide preservation check:** Across all 6 phases, zero new expert_id directories created, zero DAG node changes, zero frontmatter `expert_id` / `related_skills` edits on bundled skills — verified by sha256 snapshot diff against v5.0 close state
  8. **v5/v4 refs byte-intact milestone-wide check:** snowflake-method.md / e-konte-format.md / scamper-variations.md / dreamina-cli-baseline.md / v86-pipeline-mapping.md remain byte-intact across all of v6.0 (additive-only patches per EVOL-02 scope discipline)
**UI hint:** yes (dashboard + cross-skill view are operator-facing observability surfaces)
**Plans:** TBD

---

## Critical Path

```
Phase 28 (Feedback Ingestion MVP)  ← MUST run first (core functional guarantee)
        │
        ▼
Phase 29 (Feedback Store)          ← needs P28 normalized schema
        │
        ├──────────────┐
        ▼              ▼
Phase 30         Phase 31          ← P30 + P31 parallel-eligible (disjoint files:
(Eval Gate)      (Evolution        P30 = _eval/ extension; P31 = pipeline code)
        │         Pipeline)        share only the P28 JSON schema contract
        │              │
        └──────┬───────┘
               ▼
Phase 32 (Curator Upgrade)         ← needs P31 review queue + P29 feedback scan
               │                      + implements EVOL-02 diff generator invoked
               ▼                      by Curator's proposal path
Phase 33 (Observability + Close-out) ← MUST run last; references P28-32 + writes
                                       canonical doc + skills-mapping sign-offs
```

**Parallel-eligibility notes:**

- **Phase 30 ↔ Phase 31** — parallel-eligible. P30 extends `skills/movie-experts/_eval/runner.py` + adds gate scripts (offline developer tooling, no Hermes runtime touch). P31 builds the patch-generation pipeline under `~/.hermes/skills/.feedback/` tooling + new modules. Zero file ownership overlap. They coordinate via the shared JSON schema from P28. Critical path reflects this parallel wave.
- **Phase 28 ↔ Phase 29** — strictly sequential. P29 STORE cannot persist what P28 INGEST has not yet normalized.
- **Phase 32 ↔ anything** — NOT parallel. Curator upgrade consumes from P29 + P31 (review queue) + P30 (eval scores logged in audit).
- **Phase 33** — strictly last. Close-out references all prior phases + writes the canonical architecture doc.

---

## Coverage

**26 / 26 v1 requirements mapped (100%):**

| REQ-ID | Phase | Notes |
|--------|-------|-------|
| INGEST-01 | Phase 28 | CLI in-conversation feedback submission |
| INGEST-02 | Phase 28 | kais-aigc-platform接入 (transport choice at plan-phase) |
| INGEST-03 | Phase 28 | Single normalized JSON schema |
| INGEST-04 | Phase 28 | output_snapshot with sha256 + metadata |
| INGEST-05 | Phase 28 | Manual labeling CLI subcommand |
| STORE-01 | Phase 29 | `~/.hermes/skills/.feedback/` directory layout + jsonl |
| STORE-02 | Phase 29 | index.json queryable by skill_id/verdict/source/ts |
| STORE-03 | Phase 29 | Time-decay weight (default 90 days, configurable) |
| STORE-04 | Phase 29 | Dedup by sha256+verdict; correction demotion |
| GATE-01 | Phase 30 | Reuse `_eval/runner.py` for patch-vs-baseline |
| GATE-02 | Phase 30 | Pass threshold δ=0.3 on 4-point rubric |
| GATE-03 | Phase 30 | A/B double-blind position-swap + significance report |
| GATE-04 | Phase 30 | Per-prompt regression detection (threshold 1.0) |
| EVOL-01 | Phase 31 | LLM feedback→candidate insight aggregation |
| EVOL-02 | Phase 32 | Unified-diff patch generation (invoked by Curator proposal path) |
| EVOL-03 | Phase 31 | Patch review queue with evidence chains |
| EVOL-04 | Phase 31 | Human-in-loop approve for bundled skills (non-bypassable) |
| EVOL-05 | Phase 31 | Git-commit-on-apply + rollback subcommand |
| CURATE-01 | Phase 32 | Extend `agent/curator.py` to propose bundled-skill patches |
| CURATE-02 | Phase 32 | Auto-trigger EVOL on negative-feedback threshold |
| CURATE-03 | Phase 32 | `~/.hermes/skills/.audit/` tamper-evident log |
| CURATE-04 | Phase 32 | `hermes curator queue/approve/reject` CLI |
| CURATE-05 | Phase 32 | Agent-created skill semi-automatic path (confidence ≥ 0.8) |
| OBS-01 | Phase 33 | Per-skill dashboard (`hermes curator stats [skill_id]`) |
| OBS-02 | Phase 33 | Cross-skill view (`hermes curator stats --all`) |
| OBS-03 | Phase 33 | Source breakdown (CLI/kais-aigc/manual) |

**Coverage verification by category:**
- INGEST (5): all → Phase 28 ✓
- STORE (4): all → Phase 29 ✓
- GATE (4): all → Phase 30 ✓
- EVOL (5): 4 → Phase 31, 1 (EVOL-02) → Phase 32 ✓
- CURATE (5): all → Phase 32 ✓
- OBS (3): all → Phase 33 ✓
- Total: 26 / 26 mapped, 0 orphaned, 0 duplicated ✓

**Mapping clarification (EVOL-02 → Phase 32):** EVOL-02 (knowledge-point → candidate patch generation) is mapped to Phase 32 rather than Phase 31 because the candidate-patch generator is invoked BY the Curator's proposal path in practice (CURATE-01 extends curator to propose patches, which requires EVOL-02's diff generator as its engine). Phase 31 builds the review queue + approve/apply mechanics; Phase 32 wires the Curator as the trigger that produces patches via EVOL-02 and feeds them into the Phase 31 queue. This keeps the dependency graph clean: P31 builds the queue, P32 populates it via Curator + EVOL-02.

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 28. Feedback Ingestion MVP | 1/2 | In Progress|  |
| 29. Feedback Store | 0/? | Not started | - |
| 30. Eval Gate Reuse | 0/? | Not started | - |
| 31. Knowledge Evolution Pipeline | 0/? | Not started | - |
| 32. Curator Upgrade + Audit | 0/? | Not started | - |
| 33. Observability + Integration Close-out | 0/? | Not started | - |

---

*Last updated: 2026-06-24 — v6.0 Self-Evolution & Feedback Loop roadmap created (6 phases continuing from v5.0 Phase 27, 26/26 reqs mapped, Phase 28 ready for planning).*
