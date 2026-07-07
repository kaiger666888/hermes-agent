# Phase 61: VALIDATE - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (milestone close-out — analog to v11.0 Phase 56 / v10.0 Phase 51)

<domain>
## Phase Boundary

v12.0 milestone close-out per REQUIREMENTS.md VALIDATE-01:

1. **Audit all 8 v12.0 reqs satisfied** — produce `.planning/milestones/v12.0-MILESTONE-AUDIT.md` with status PASS / tech_debt / FAIL.
2. **Re-run v11.0 SC#2 vertical slice smoke with hardening in place** — verify latency drops from 490s to <240s + zero `RateLimitError`. Document in `.planning/research/v12-poc-eval/production-smoke-report.md`.
3. **Aggregate Phase 60 deferred operator-action runbook** — surface the 2 live runs (mem0 p95 + fitness battery real-mode) for operator execution.
4. **Produce milestone audit verdict** — PASS / tech_debt / FAIL.

**Hard dependencies:** All previous v12.0 phases (57-60). STRICTLY LAST.

</domain>

<decisions>
## Implementation Decisions

### Locked

1. **Audit file location:** `.planning/milestones/v12.0-MILESTONE-AUDIT.md`
2. **Smoke report location:** `.planning/research/v12-poc-eval/production-smoke-report.md`
3. **Verdict vocabulary:** `passed | tech_debt | gaps_found | fail` (matches v11.0)
4. **Audit walks all 8 reqs:** ENDPOINT-01, THROTTLE-01, THROTTLE-02, POOL-01, POOL-02, EVAL-01, EVAL-02, VALIDATE-01
5. **Reuses `scripts/run_milestone_audit.py`** from Phase 56 (extend with v12.0 phase list)
6. **Operator-action aggregation:** Phase 60's 2 deferred runs + Phase 61's own SC#2 real-GLM smoke = 3 handoffs documented in §3 Operator-Action Runbook

### Claude's Discretion

- Audit script: extend `scripts/run_milestone_audit.py` with milestone version arg, OR new `scripts/run_v12_audit.py`. Recommend extend (single audit script).
- Real-GLM smoke (SC#2): can either run during VALIDATE itself OR mark as `human_needed` if no GLM budget. Recommend: try to run; if rate-limited, defer to operator.
- Verdict strategy: similar to v11.0 — `passed` if all 8 reqs verified at automated level + 3 operator-action items documented (runtime validations, not design gaps).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `.planning/milestones/v11.0-MILESTONE-AUDIT.md` — v11.0 audit format reference
- `scripts/run_milestone_audit.py` (Phase 56) — audit coverage matrix producer
- `.planning/phases/57-endpoint-routing/57-VERIFICATION.md`
- `.planning/phases/58-rpm-throttling/58-VERIFICATION.md`
- `.planning/phases/59-aux-pool-isolation/59-VERIFICATION.md`
- `.planning/phases/60-live-eval/60-VERIFICATION.md`
- `scripts/run_screenplay_step3_roundtable.py --smoke` (Phase 53 — SC#2 driver, now hardened by Phase 57+58+59)

### Integration Points

- `.planning/milestones/v12.0-MILESTONE-AUDIT.md` (NEW)
- `.planning/research/v12-poc-eval/production-smoke-report.md` (NEW)
- `.planning/REQUIREMENTS.md` traceability table (update 8 Status cells)
- `.planning/milestones/v12.0-ROADMAP.md` + `v12.0-REQUIREMENTS.md` (archive copies — created at complete-milestone)

</code_context>

<specifics>
## Specific Ideas

The 1 SC (per ROADMAP §Phase 61):

- **SC#1 (VALIDATE-01):** v12.0 milestone audit + production smoke with hardening in place. Audit verdict: PASS / tech_debt / FAIL.

**Smoke target:** <240s round table latency + zero RateLimitError (vs v11.0's 490s + 5x retry storm).

</specifics>

<deferred>
## Deferred Ideas

- Live GLM smoke may be deferred to operator if rate-limited during VALIDATE — mark `human_needed`.
- v13.0+ scope: 15-expert full transform, curator self-evolution loop, round table 异步并发, Option B 物理分区 migration.

</deferred>
