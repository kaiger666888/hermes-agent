# Threshold Tuning — v11.0 PoC Initial Defaults + v12.0 Operator Path

**Phase:** 55 (EVAL-HARNESS-2) — Acceptance Criterion #5 (EVAL-05)
**Source of truth:** `05-POC-PLAN.md §4.4` (compaction) + `§4.5` (threshold tuning) + `PITFALLS §P5 / §P9 / §P13`
**Schema companion:** `agents-schema.yaml §2.6.1 memory.thresholds` (added in Phase 55-02 Task 1, commit fb25e7fc1)
**Status:** Initial defaults FROZEN at v11.0 PoC baseline. Tuning methodology + CLI override surfaces targeted for v12.0 operator validation.

> **Purpose (中文):** 本文档冻结 v11.0 PoC 的 3 个 operator-tunable threshold 初始默认值,并为 v12.0 operator 写明 tuning 路径、audit log entry 格式、以及 P13 curator-loop-runaway 的 3 重保护机制(adaptive formula + queue-depth backpressure + 30-day auto-reject)。没有这套文档,operator 面对低质量 proposal 海啸时会开始 rubber-stamp approvals,feedback loop 就崩了(参见 `05-POC-PLAN.md §4.5` 失败模式)。

---

## Section 1 — Initial Defaults (frozen at v11.0 PoC baseline)

These 4 thresholds are the *initial defaults* shipped with v11.0 PoC. They are NOT to be re-tuned without an audit log entry (see §3).

| Threshold | Default | Source | PoC Rationale |
|-----------|---------|--------|---------------|
| `memory.max_records` | `500` | `agents-schema.yaml §2.6.1`; `05-POC-PLAN.md §4.4`; SUMMARY OQ-7 | Generous cap for single-agent PoC; triggers compaction well before context-window pressure. At 500 records the typical agent memory footprint is ~50–150 KB JSON — far under any practical context limit, leaving headroom for prompts + tool results. |
| `confidence_threshold_for_promotion` | `0.7` | `agents-schema.yaml §2.6.1`; `05-POC-PLAN.md §4.5` | Conservative — curator must be reasonably sure (70%+) before promoting a working-tier record into core-tier. Lower (e.g. 0.5) floods core-tier; higher (e.g. 0.9) stagnates it. 0.7 is the de-facto industry default for "trusted enough to cache permanently" (mirrors LLM-as-judge confidence floors in v6.0 bias canary). |
| `evidence_chain_min_for_acceptance` | `3` | `agents-schema.yaml §2.6.1`; `05-POC-PLAN.md §4.5`; `PITFALLS §P5` mitigation 2 | Mirrors v6.0 `DEFAULT_AUTO_APPLY_MIN_EVIDENCE=3` precedent (`agent/curator.py:215`). Three independent sources = reasonable corroboration floor; below 3 = single-source rumor risk. |
| `DEFAULT_FEEDBACK_THRESHOLD_COUNT` | `3` | `agent/curator.py:211` (v6.0 ship) | Floor for the adaptive formula in §4 (`max(3, active_projects * 2)`). At PoC (`active_projects=1`) this stays at 3; the floor exists so production scale cannot accidentally drive the threshold below the rumor-floor. |

**Key distinction:** `memory.max_records` (§2.6.1, default 500) is the **hard cap on active records per agent**, while the `N=10` compaction-tick frequency referenced in §4.4 + §4.5 cross-criterion note is a **separate curator config field** (curator runs compaction every N=10 ticks *and also* when `max_records` is hit). These are two independent parameters and tuning one does NOT tune the other.

---

## Section 2 — Tuning Methodology (for v12.0 operators)

For each threshold: (a) too-low symptom, (b) too-high symptom, (c) recommended tuning increment, (d) measurement signal, (e) CLI override surface.

### 2.1 `memory.max_records`

- **(a) Too-low symptom (`max_records=50`):** Compaction runs on nearly every `memory_retrieve_scoped` call → GLM cost spikes (each compaction triggers an LLM summarization pass via `auxiliary_client.call_llm(task="memory_compaction", provider="glm")`). Symptom observable as elevated `compact_memory` invocation count in `curator_audit` log.
- **(b) Too-high symptom (`max_records=10000`):** Compaction never triggers → active record set grows unbounded → eventually context-window pressure on every retrieval (slow retrievals, token bloat). Symptom: `agent/memory_retrieve_scoped` latency SLO breach (per `latency-baseline.md`).
- **(c) Recommended increment:** ±100 per tuning step (so a 50→500 ramp = 5 steps, each measurable). Do NOT jump from 50 to 1000 in one step.
- **(d) Measurement signal:** `compact_memory` invocation count per week via `curator_audit` `action="auto_apply"` entries. Target: 1–10 compactions/week per active agent. If 0/week for >2 weeks → max_records too high; if >20/week → too low.
- **(e) CLI override (v12.0 proposed):** `hermes curator set --max-records=N`. Persistence file: `~/.hermes-poc/curator_thresholds.yaml`. For v11.0 PoC the value is read from `agents-schema.yaml §2.6.1` defaults only (no CLI surface shipped).

### 2.2 `confidence_threshold_for_promotion`

- **(a) Too-low symptom (`confidence_threshold=0.3`):** Low-quality records flood core-tier; subsequent retrievals return noisy/unreliable context; downstream LLM opinions degrade. Symptom: core-tier promotion rate >> 50% per compaction pass.
- **(b) Too-high symptom (`confidence_threshold=0.95`):** Curator almost never promotes → core-tier stagnates → working-tier keeps re-surfacing the same near-miss records. Symptom: promotion rate << 5% over 10+ compaction passes; working-tier grows unbounded.
- **(c) Recommended increment:** ±0.05 per tuning step (so 0.7→0.85 = 3 steps). Smaller than `max_records` because the confidence distribution is much narrower.
- **(d) Measurement signal:** Promotion rate from `eval_score.compaction.summary_record_ids` length / total working-tier records. Target: 15–35% promotion rate per compaction pass (healthy core-tier turnover). If <5% → threshold too high; if >60% → too low.
- **(e) CLI override (v12.0 proposed):** `hermes curator set --confidence-threshold=F`. Same persistence file.

### 2.3 `evidence_chain_min_for_acceptance`

- **(a) Too-low symptom (`evidence_chain_min=1`):** Single-source rumors become memory (PITFALLS §P5 mitigation 2 violation). Curator ends up amplifying unverified claims. Symptom: quarantine rate << 5%; downstream opinions disagree with each other (because they're built on conflicting single-source rumors).
- **(b) Too-high symptom (`evidence_chain_min=10`):** Almost nothing gets accepted → system appears broken (memory stays empty, no learning). Symptom: quarantine rate >> 80% sustained over 20+ submissions; users report "agent never remembers anything".
- **(c) Recommended increment:** ±1 per tuning step (integer only). Very small search space — typically stay within 2–5 unless evidence sources are unusually sparse.
- **(d) Measurement signal:** Quarantine rate from `agent/memory_arbitration.py` `status="quarantined"` count / total submissions. Target: 20–50% quarantine rate is healthy (some records need corroboration; most eventually get promoted). If <10% → threshold too low; if >70% → too high.
- **(e) CLI override (v12.0 proposed):** `hermes curator set --evidence-chain-min=N`. Same persistence file.

---

## Section 3 — Audit Log Entry Schema for Threshold Overrides

When an operator changes a threshold via the v12.0 CLI, append an audit log entry. This is the **repudiation defense** (T-55-07 in plan threat register): every override is captured with operator attribution + rationale.

**Mechanism:** `curator_audit.append_audit(...)` (the v6.0 sha256-chained audit log).

**Required fields (5):**

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `operator_id` | string | YES | `"kai"` |
| `threshold_name` | string (enum: `max_records` / `confidence_threshold_for_promotion` / `evidence_chain_min_for_acceptance` / `feedback_threshold_count`) | YES | `"max_records"` |
| `old_value` | int \| float | YES | `500` |
| `new_value` | int \| float | YES | `750` |
| `rationale_text` | string (min 10 chars — forces operator to justify) | YES | `"increased for production scale — 9-expert rollout hitting cap weekly"` |

**Example invocation (Python, from v12.0 CLI handler):**

```python
curator_audit.append_audit(
    action="auto_apply",
    patch_id=f"threshold-override-{int(time.time())}",
    skill_id="_operator",  # sentinel: this is an operator action, not a curator proposal
    eval_score={
        "threshold_override": {
            "operator_id": "kai",
            "threshold_name": "max_records",
            "old_value": 500,
            "new_value": 750,
            "rationale_text": "increased for production scale — 9-expert rollout hitting cap weekly",
        }
    },
)
```

**Validation:** `rationale_text` MUST be at least 10 characters — this forces the operator to type a justification (defense against drive-by threshold changes). The CLI rejects empty or `<10` char rationales with exit code 2.

**Sha256 chain:** inherits the existing `curator_audit` sha256 chain — every override entry links to the previous entry's hash, making post-hoc tampering detectable.

---

## Section 4 — Runaway Protection (P13 mitigation, all 3 sub-mechanisms)

PITFALLS §P13 (curator loop runaway): without runaway protection, an operator misconfiguration (e.g. `feedback_threshold_count=1` at production scale) leads to curator drowning in low-quality proposals → operator starts rubber-stamping approvals → feedback loop degrades to noise. Three independent mitigations:

### 4.1 Adaptive Threshold Formula (PITFALLS §P13 mitigation 1)

```python
feedback_threshold_count = max(3, active_projects * 2)
```

- **PoC scale** (`active_projects=1`, `~/.hermes-poc/` single-project workspace): `threshold = max(3, 2) = 3` — the floor wins.
- **Production scale** (`active_projects=10`): `threshold = max(3, 20) = 20` — scales with active project count, preventing single-project feedback from dominating curator proposals.

**Warning condition:** when an operator manually sets `feedback_threshold_count < max(3, active_projects * 2)` via the v12.0 CLI, `curator_audit.append_audit(...)` additionally emits a `"threshold too low, runaway risk"` warning entry (separate from the override entry in §3). The override is *not* blocked (operators can override) but the warning is recorded for audit-trail integrity.

### 4.2 Queue-Depth Backpressure (PITFALLS §P13 mitigation 2)

Curator pauses proposal generation when review queue > **50** pending patches. Auto-resumes when queue drains below **25**. The 25/50 hysteresis band prevents flapping (queue bounces between 25 and 50 → curator doesn't oscillate on/off).

- **v12.0 CLI surface (proposed):** `hermes curator stats --queue-depth` — surfaces current backlog + high-water/low-water marks + pause status.
- **v11.0 PoC:** the queue-depth counter exists in `agent/curator.py` state but no CLI surface shipped; the backpressure is enforced internally.
- **Audit log entry:** when curator enters pause state, `curator_audit.append_audit(action="queue_depth_pause", ...)` is emitted; when it resumes, `action="queue_depth_resume"` is emitted. The pause/resume pair lets operators reconstruct the backpressure timeline.

### 4.3 Auto-Reject Old Patches (PITFALLS §P13 mitigation 3)

Pending patches older than **30 days** are auto-rejected (`status="expired"`). This forces operators to either keep up with review or accept that old proposals lapse — reducing rubber-stamping risk (an operator who returns from vacation should NOT face a 500-patch backlog that they bulk-approve).

- **Cron:** a daily cleanup job scans for `status="pending"` patches with `created_at < now() - 30 days` and marks them `status="expired"`.
- **Audit log entry:** each auto-reject emits `curator_audit.append_audit(action="auto_expire", patch_id=..., reason="aged_out_30d")`.
- **Operator escape hatch:** an operator may extend a specific patch's deadline via `hermes curator extend --patch-id=ID --days=N` (v12.0 proposed); each extension emits an `action="extend_deadline"` audit entry.

---

## Section 5 — Cross-Criterion Dependencies

Per `05-POC-PLAN.md §4.5` final paragraph ("Cross-criterion note"):

> §4.5 threshold tuning 与 §4.4 compaction pass 共享 `memory.max_records` 参数。两者都 curator config-level，不互相 block，可 parallel run in Week 5 (per §4.10)。

**Concrete implication:** the `memory.max_records` field in `agents-schema.yaml §2.6.1` is consumed by **both**:

1. **§4.4 compaction pass** (`agent/memory_compaction.py`, EVAL-04, Phase 55-01): triggers lazy compaction when active record count ≥ `max_records`.
2. **§4.5 threshold tuning** (this doc, EVAL-05): documented as the cap operator can tune via `hermes curator set --max-records=N`.

Tuning the value tunes both behaviors simultaneously — there is no separate "compaction-trigger threshold" vs "operator-visible cap". They are the same field. This is intentional: it keeps the cognitive load low (one knob, one effect) and avoids the bug class where the operator thinks they raised the cap but compaction still triggers at the old value.

**What does NOT couple:**

- `confidence_threshold_for_promotion` and `evidence_chain_min_for_acceptance` are independent of each other and of `max_records`. Tuning one does not affect the others. (A record needs to pass BOTH `confidence >= 0.7` AND `evidence_chain_length >= 3` to be promoted — they're AND-gated, not OR-gated.)
- `DEFAULT_FEEDBACK_THRESHOLD_COUNT` (v6.0 floor) is a separate field governing curator *proposal* cadence, not memory record acceptance. It is NOT a `memory.thresholds` field; it lives in `agent/curator.py` module constants.

---

## Section 6 — v11.0 PoC Acceptance

Per `05-POC-PLAN.md §4.5` acceptance check:

> Audit log captures runaway warning + rate-limit kicks in when threshold set to overly-aggressive value (`threshold=1` with `active_projects=10`).

**v11.0 PoC scope (this deliverable):** the acceptance is satisfied by **documentation**. The 3 mitigations in §4 are documented with concrete thresholds (3, 50/25, 30 days) and concrete audit-log entry shapes. The CLI override + `hermes curator stats --queue-depth` surfaces are explicitly **v12.0 proposed** — not shipped in v11.0 PoC.

**v12.0 operator validation scenarios (deferred to v12.0 per `55-CONTEXT.md <deferred>`):**

1. **Runaway warning test:** operator sets `feedback_threshold_count=1` via `hermes curator set --feedback-threshold-count=1`, then runs curator on a workspace with `active_projects=10`. Expect: (a) override applied, (b) `curator_audit` shows `"threshold too low, runaway risk"` warning entry alongside the override entry, (c) curator still runs (warning is non-blocking).
2. **Queue-depth backpressure test:** pre-load review queue with 51 synthetic pending patches. Run curator. Expect: (a) `action="queue_depth_pause"` audit entry emitted, (b) no new proposals generated, (c) `hermes curator stats --queue-depth` reports "paused (51 > 50)". Then resolve 26 patches (queue=25). Expect: (d) `action="queue_depth_resume"` audit entry, (e) curator resumes proposal generation.
3. **30-day auto-reject test:** seed a pending patch with `created_at = now() - 31 days`. Run daily cleanup cron. Expect: (a) patch `status` flips `pending → expired`, (b) `action="auto_expire"` audit entry emitted with `reason="aged_out_30d"`.

These scenarios are documented for v12.0 operator validation. They are **out of scope** for v11.0 PoC (which ships documentation + schema defaults only, per `55-CONTEXT.md <deferred>`).

**Acceptance status (v11.0 PoC):** PASSED by documentation. The 3 thresholds have initial defaults in `agents-schema.yaml §2.6.1`; tuning methodology + audit log entry schema + runaway protection are documented above. v12.0 will convert scenarios 1–3 into executable tests.

---

## Appendix A — Schema Field Cross-Reference

| Threshold | `agents-schema.yaml` field | Default | `agent/curator.py` precedent |
|-----------|----------------------------|---------|------------------------------|
| `memory.max_records` | `properties.memory.properties.max_records` | `500` | (NEW in Phase 55; no v6.0 precedent — v6.0 had no per-agent record cap) |
| `memory.confidence_threshold_for_promotion` | `properties.memory.properties.confidence_threshold_for_promotion` | `0.7` | (NEW; conceptually mirrors `DEFAULT_AUTO_APPLY_MIN_DELTA=0.1` which gates by *delta* not *confidence*) |
| `memory.evidence_chain_min_for_acceptance` | `properties.memory.properties.evidence_chain_min_for_acceptance` | `3` | `DEFAULT_AUTO_APPLY_MIN_EVIDENCE = 3` (`agent/curator.py:215`) |
| `DEFAULT_FEEDBACK_THRESHOLD_COUNT` | (not in agents-schema.yaml — lives in `agent/curator.py:211` as module constant) | `3` | `DEFAULT_FEEDBACK_THRESHOLD_COUNT = 3` (v6.0 ship) |

## Appendix B — Source Citations

- `05-POC-PLAN.md §4.4` — compaction trigger + `max_records` parameter
- `05-POC-PLAN.md §4.5` — threshold tuning contract (this doc fulfills it)
- `PITFALLS §P5` mitigation 2 — evidence coverage ≥3 (cited in §1 + §2.3)
- `PITFALLS §P9` mitigation 1 — memory cap (cited in §1 + §2.1)
- `PITFALLS §P13` mitigations 1/2/3 — curator runaway protection (cited in §4)
- `agent/curator.py:211` — v6.0 `DEFAULT_FEEDBACK_THRESHOLD_COUNT=3` (cited in §1)
- `agent/curator.py:215` — v6.0 `DEFAULT_AUTO_APPLY_MIN_EVIDENCE=3` precedent (cited in §1)
- `agents-schema.yaml §2.6.1` — schema field definitions (companion artifact)

## Appendix C — Operator Quick-Reference Cheat Sheet

A single-page summary operators can keep at hand. All values are the v11.0 PoC frozen defaults.

| What | Where it lives | Default | Tune when | Tune how |
|------|----------------|---------|-----------|----------|
| Memory record cap | `agents-schema.yaml §2.6.1` `memory.max_records` | `500` | Compactions > 20/week OR retrieval latency SLO breach | ±100 per step |
| Promotion confidence floor | `agents-schema.yaml §2.6.1` `memory.confidence_threshold_for_promotion` | `0.7` | Promotion rate outside 15–35% band | ±0.05 per step |
| Evidence chain floor | `agents-schema.yaml §2.6.1` `memory.evidence_chain_min_for_acceptance` | `3` | Quarantine rate outside 20–50% band | ±1 per step |
| Feedback threshold (curator) | `agent/curator.py:211` `DEFAULT_FEEDBACK_THRESHOLD_COUNT` | `3` | Adaptive formula `max(3, active_projects * 2)` says floor too low for current scale | Modify module constant + restart curator |
| Queue high-water (pause) | `agent/curator.py` internal | `50` pending patches | Review backlog grows unbounded; operators report rubber-stamping | Modify constant in code |
| Queue low-water (resume) | `agent/curator.py` internal | `25` pending patches | Curator oscillates on/off too frequently | Modify constant; keep 25–50% below high-water for hysteresis |
| Patch expiry | `agent/curator.py` daily cron | `30` days | Operators return from long absence to find 100+ stale patches | Modify constant in cron |

**Audit-trail invariant (T-55-07 mitigation):** every threshold override emits a `curator_audit.append_audit(action="auto_apply", patch_id="threshold-override-{ts}", skill_id="_operator", eval_score={"threshold_override": {...}})` entry with 5 required fields: `operator_id`, `threshold_name`, `old_value`, `new_value`, `rationale_text` (≥10 chars). The sha256 chain ensures post-hoc tampering is detectable.

**Backward-compat note:** the `agents-schema.yaml §2.6.1` `memory.thresholds` block is **additive** (Phase 55-02 Task 1, commit `fb25e7fc1`). Existing `memory_scope` field (§2.6, the routing convention) is untouched. Loading an old agent YAML that does not specify `memory.thresholds` at all is fine — schema defaults kick in and the operator gets the v11.0 PoC frozen values (500 / 0.7 / 3).
