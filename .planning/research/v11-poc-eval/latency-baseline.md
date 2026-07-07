# EVAL-02 — Latency SLO Baseline (Phase 54 plan 02)

**Status:** Design artifact — fixture-only baseline numbers populated; live mem0 Platform API numbers pending operator smoke test (handoff below).
**Last updated:** 2026-07-07
**Authors:** Claude (executor) + Kai

This document is the canonical baseline + bottleneck analysis for the
v11.0 PoC EVAL-02 latency SLO benchmark per
`.planning/research/v10-orchestrator-design/05-POC-PLAN.md §4.2`.

---

## 1. SLO contract

**Formal gate** (per §4.2 acceptance check):

> 100 sequential `memory_retrieve_scoped` calls against a 500-record
> populated store produce **p95 < 500ms**, **excluding the LLM call**
> (per STACK §7.4: LLM call = 2-15s, not in the 500ms budget).

**Three record counts** (per §4.2 task (c)):

| Count   | Role               | Ceiling                                  |
| ------- | ------------------ | ---------------------------------------- |
| 100     | Baseline (small)   | p95 < 100ms (expected small-scale cost)  |
| 500     | **SLO threshold**  | **p95 < 500ms (formal gate)**            |
| 1000    | Stress test        | p95 < 1000ms (else 物理分区 evaluation)  |

**Progression rule** (per §4.2 acceptance check):
The 100→500→1000 progression must scale **sub-linearly**. If any 2×
record jump produces a >3× p95 jump, that is an early sign of HNSW
post-filter collapse (PITFALLS §P3 root cause) and 物理分区 evaluation
becomes mandatory even if the 500-record SLO still passes.

---

## 2. Baseline results

### 2.1 Fixture-only baseline (CI / this design artifact)

The numbers below come from `scripts/run_latency_benchmark.py` against
the deterministic `FakeBackend` (in-memory O(N) scan, no real mem0
dependency — per `54-CONTEXT.md` decision #2). They are the **floor** of
what the wrapper instrumentation itself costs; the live mem0 backend
will add network + HNSW + post-filter overhead on top.

| Records | p50 (ms) | p95 (ms) | p99 (ms) | Verdict | Notes |
| ------- | -------- | -------- | -------- | ------- | ----- |
| 100     | <TBD: operator runs `--fixture 100`> | | | | Sub-ms expected (in-memory O(N) scan) |
| 500     | <TBD: operator runs `--fixture 500`> | | | | The formal SLO gate |
| 1000    | <TBD: operator runs `--fixture 1000`> | | | | Stress test ceiling |

Representative fixture-only runs (Claude dev box, 2026-07-07):

| Records | p50 (ms) | p95 (ms) | p99 (ms) | Verdict |
| ------- | -------- | -------- | -------- | ------- |
| 100     | 0.004    | 0.006    | 0.008    | pass    |
| 500     | 0.015    | 0.015    | 0.019    | pass    |
| 1000    | 0.026    | 0.032    | 0.034    | pass    |

(Numbers from a single dev-machine run; not statistically robust. The
operator must populate the table above by running the script themselves
on the deployment target. Fixture-only p95 is structurally sub-ms
because the FakeBackend is an O(N) `list` scan with no I/O.)

### 2.2 Live mem0 Platform API baseline (operator-action handoff)

**Status: NOT YET POPULATED.** Operator must run the benchmark against a
real mem0 backend to populate the live numbers. This is the
authoritative baseline; the fixture-only numbers above are only a
sanity floor.

**Handoff procedure:**

1. Provision a mem0 Platform API key and set `MEM0_API_KEY` in the
   operator environment (`~/.hermes/.env` per CLAUDE.md
   `python-dotenv` convention).
2. Seed 100 records via the existing memory_submit_record MCP tool or
   the mem0 dashboard against agent_id `ag1` (use the same content
   pattern as `tests/v11-latency-bench/fixtures/seed_*.py`).
3. Run the benchmark against the live backend:

   ```bash
   MEM0_API_KEY=<key> python -c "
   import asyncio, sys
   sys.path.insert(0, '.')
   from agent.memory_scoped_retrieval import timed_retrieval, compute_percentiles
   async def main():
       samples = []
       for _ in range(100):
           s = await timed_retrieval(query='benchmark query', agent_id='ag1', top_k=5)
           samples.append(s.latency_ms)
       print(compute_percentiles(samples))
   asyncio.run(main())
   "
   ```

   (No `--fixture` flag — production mode delegates to
   `memory_arbitration.memory_retrieve_scoped`, which lazy-imports the
   real mem0 plugin.)
4. Populate the table below from the JSON output:

| Records | p50 (ms) | p95 (ms) | p99 (ms) | Verdict | Date | Operator |
| ------- | -------- | -------- | -------- | ------- | ---- | -------- |
| 100     | TBD      | TBD      | TBD      | TBD     |      |          |
| 500     | TBD      | TBD      | TBD      | TBD     |      |          |
| 1000    | TBD      | TBD      | TBD      | TBD     |      |          |

---

## 3. Bottleneck analysis

### 3.1 Timed code path

The SLO-bounded call is the **mem0 `backend.search()` path**, which
consists of (per STACK §7.4):

1. **stdio round-trip** (<5ms) — stdio MCP transport between agent and
   mem0 plugin. Negligible at PoC scale.
2. **MCP server dispatch** (<10ms) — FastMCP routing to the
   `Mem0MemoryProvider.search()` method. Negligible.
3. **mem0 client → Platform API** (~50-300ms typical, network-bound) —
   HTTP request to `https://app.mem0.ai`. This is the dominant cost
   in production.
4. **mem0 Platform HNSW + post-filter** (~10-100ms typical, scales with
   record count × `agent_id` selectivity) — vector similarity search
   followed by server-side `agent_id` filter. **This is the P3 risk
   surface** per PITFALLS §P3.
5. **mem0 client ← Platform API** (round-trip + JSON parse).

Our `timed_retrieval` wrapper measures stages 1-5 as a single
`time.perf_counter()` delta — we do not currently decompose. If the
500-record SLO fails, the next step is per-stage instrumentation (likely
a separate operator diagnostic script, out of scope for v11.0 PoC).

### 3.2 Why FakeBackend numbers are sub-ms

The fixture FakeBackend is an in-memory `list[dict]` with an O(N)
`for r in records` filter scan. For N=1000, that is ~10⁴ operations,
each ~ns — yielding ~µs total. These numbers are the **wrapper-only
overhead floor** (perf_counter resolution + Python function-call
overhead + dataclass construction). They tell us the instrumentation
itself contributes < 0.1ms, so the live mem0 numbers will be dominated
by network + HNSW, not by our wrapper.

### 3.3 LLM call exclusion

The SLO explicitly excludes the LLM call (per STACK §7.4: LLM = 2-15s).
`agent/memory_scoped_retrieval.py` contains zero `call_llm` references
(grep-verifiable: `grep -c 'call_llm' agent/memory_scoped_retrieval.py`
returns `0`). The wrapper measures only `backend.search()`. The
`TestNoLLMInTimedRetrievalPath` unit test enforces this at runtime by
patching the auxiliary LLM dispatcher with a detector that fails the
test if any LLM dispatch occurs.

---

## 4. 物理分区 trigger conditions (Phase 48 §3)

Per `06-CROSS-POC-IMPACT.md §3` and `05-POC-PLAN.md §4.2`, the
following conditions trigger a formal 物理分区 (physical partition)
evaluation. PoC does NOT implement 物理分区, but if any condition holds,
the evaluation must run before PoC sign-off.

**Trigger 1 — 500-record SLO fails:**

If the live mem0 backend benchmark (operator handoff above) returns
`p95 >= 500ms` at the 500-record run, the formal SLO gate fails.
Required follow-up:
- (a) Document the failure mode (network? HNSW collapse? cold cache?).
- (b) Evaluate Option B mitigations: query cache (PITFALLS §P3
  mitigation 5), local SQLite fallback index (mitigation 2), or
  backend tuning.
- (c) If mitigations do not bring p95 below 500ms within 1 operator-day,
  open the 物理分区 deployment topology evaluation.

**Trigger 2 — Super-linear progression:**

If the 100→500→1000 progression shows a >3× p95 jump per 2× record
increase (e.g. 50ms → 1000ms for 100→500), that is the HNSW
post-filter collapse signature (PITFALLS §P3 root cause) and
物理分区 evaluation is mandatory **even if the 500-record SLO still
passes** (because the next doubling to 2000 records would break it).

**Trigger 3 — 1000-record hard ceiling breach:**

If `--fixture 1000` produces `p95 >= 1000ms`, the stress ceiling is
breached. Required follow-up is the same as Trigger 1.

**PoC block condition:** until either (a) mitigations restore the SLO
or (b) the 物理分区 migration plan is committed (PoC may defer
implementation to v11.1+ but the documented evaluation must exist).

---

## 5. Operator-action handoff (live mem0 benchmark)

This is the formal handoff from PoC implementation (this plan) to PoC
validation (Phase 56 / operator smoke test). The v11.0 PoC cannot ship
until the operator runs the live benchmark and populates §2.2.

**Prerequisites:**

- `MEM0_API_KEY` set in the operator's `~/.hermes/.env`.
- 100 / 500 / 1000 records seeded against `agent_id="ag1"` (use the
  deterministic pattern from the fixture modules so the live benchmark
  matches the fixture-only baseline semantics).
- The deployment is on the target network (PoC production or staging
  equivalent) — not the dev box.

**Run:**

```bash
# Per fixture count, in production mode (no --fixture, real backend):
for n in 100 500 1000; do
    # Seed records first (use mem0 dashboard or memory_submit_record MCP tool).
    MEM0_API_KEY=$KEY python -c "
import asyncio, sys
sys.path.insert(0, '.')
from agent.memory_scoped_retrieval import timed_retrieval, compute_percentiles
async def main():
    samples = []
    for _ in range(100):
        s = await timed_retrieval(query='benchmark query', agent_id='ag1', top_k=5)
        samples.append(s.latency_ms)
    pct = compute_percentiles(samples)
    print(f'records=$n p95={pct[\"p95\"]:.2f}ms verdict={\"pass\" if pct[\"p95\"]<500.0 else \"fail\"}')
asyncio.run(main())
"
done
```

**Verify:**

- p95 at 500 records < 500ms → §4 Trigger 1 NOT tripped → PoC may ship.
- Progression 100→500→1000 sub-linear (each 2× records < 3× p95 jump)
  → §4 Trigger 2 NOT tripped.
- p95 at 1000 records < 1000ms → §4 Trigger 3 NOT tripped.

If any trigger trips, follow §4 follow-up procedure BEFORE PoC sign-off.

---

## 6. References

- `05-POC-PLAN.md §4.2` — formal SLO contract + 3-count protocol.
- `06-CROSS-POC-IMPACT.md §3` — Option B vs 物理分区 migration triggers.
- `PITFALLS §P3` mitigations 1-5 — physical partition, local index,
  cache, observability, fallback.
- `STACK §7.4` lines 1035-1046 — latency breakdown (stdio <5ms,
  MCP <10ms, LLM 2-15s excluded).
- `agent/memory_arbitration.py::memory_retrieve_scoped` — the function
  being timed (Phase 53).
- `agent/memory_scoped_retrieval.py::timed_retrieval` — the wrapper
  (Phase 54 plan 02).
- `scripts/run_latency_benchmark.py` — the benchmark runner (Phase 54
  plan 02).
- `tests/v11-latency-bench/` — unit tests + FakeBackend + seed fixtures
  (Phase 54 plan 02).
