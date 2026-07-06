# Pitfalls Research — v10.0 Per-Agent Scoped Memory + Curator-Driven Self-Evolution

**Domain:** Per-agent scoped memory systems + curator-driven cross-project self-evolution (Hermes-native expert agents)
**Researched:** 2026-07-06
**Confidence:** HIGH (cross-verified against v6.0 shipped Hermes codebase + 6+ industry projects with documented failure modes)

---

## Scope & Method

This file documents pitfalls specific to **per-agent scoped memory + curator-driven self-evolution** — the load-bearing feature of v10.0 (PROJECT.md decision #6). Failures here collapse the new agent form back into "renamed SKILL.md files."

Each pitfall includes:
- **Trigger condition** — when it manifests
- **Industry case** — at least one documented real-world failure (MemGPT/Letta, mem0, LangChain, AutoGen, ReConcile, MINJA, Echoleak)
- **Concrete mitigation** — schema field / config knob / ast-walk invariant, NOT "be careful"
- **Phase flag** — which downstream v10.0/v11.0 design document must address it

**Hermes context inventory (what already ships, do NOT re-invent):**
- `agent/curator.py` — `_feedback_scan_phase` (CURATE-01..05), `apply_automatic_transitions` (deterministic inactivity prune), `_run_llm_review` (umbrella-building fork), audit-log via `agent/curator_audit.py` (sha256-chained JSONL).
- `agent/feedback_store.py` — `FeedbackStore` with bucketed JSONL, sha256 dedup + correction semantics, linear time-decay `weight = max(0.1, 1.0 − age_days / 180)`, `_superseded_record_ids` set.
- `agent/evolution/*` — LLM aggregation (`insights.py`), unified-diff generation (`diff_generator.py` + `evol02_generator.py`), additive-only `apply_patch_transaction` (`apply.py`), JSONL review queue (`queue.py`).
- `plugins/memory/mem0/__init__.py` — `Mem0MemoryProvider` with circuit breaker (5 consecutive failures → 120s cooldown), `user_id` + `agent_id` filter model, async `sync_turn` for non-blocking server-side fact extraction.
- `_eval/gate.py` — MT-Bench position-swap eval gate (δ=0.3 mean + 1.0 per-prompt regression), stdlib paired-t (no scipy dep).
- `TestNonBypassableHumanInLoop` ast-walk — `apply_patch_transaction` only callable from `hermes_cli/feedback.py:_cmd_approve`.

---

## Critical Pitfalls (rewrite-class)

### Pitfall 1: Persona Drift — agent forgets its role after accumulating memory

**What goes wrong:**
A `screenplay` agent ingests 200+ memory records over 10 projects. After enough curator-driven updates, the agent stops behaving like a screenplay expert and starts behaving like a generic "creative writing helper" — its outputs become broader, less technically precise, and its `expert_id` no longer matches observed behavior. The agent's identity has been silently rewritten by accumulated memory.

**Why it happens:**
- Every memory write appends a fact; curator updates grow `SKILL.md` additively. The persona prompt is a fixed YAML field, but the *effective* persona is `(persona prompt + injected memory block + curator-patched SKILL.md body)`. Without an invariant protecting the original persona, the additive mass slowly dilutes it.
- LLMs are documented to weight recent / heavily-injected context more than the system prompt when both are present (the "context waterfall" effect). MemGPT's hierarchical memory was specifically designed to mitigate this (core memory = persona, archival = facts), but Letta's own benchmark notes that even core memory gets rewritten/compacted over long sessions.
- The arxiv paper *Black-box Persona Drift Detection for Production LLM Agents* (2605.09863v1) cites MemGPT/Letta as a canonical example of the architecture class that still suffers this failure mode.

**Concrete mitigations:**

1. **Persona hash invariant in agent registry.** Every agent YAML has a frozen `persona_sha256` computed at registration. Curator-driven patches MUST NOT alter lines inside the `## Role & Philosophy` / `## Core Capabilities` sections (matching the existing SKILL.md section grammar). Add a `_check_persona_section_intact(post_patch_text, pre_patch_text) -> bool` to the existing `agent/evolution/apply.py:additive_only_check` pipeline. Reject the patch if the diff touches those sections.
2. **Periodic persona-drift probe.** Once per N runs (config: `agent.persona_drift_probe_period: 50`), send a fixed battery of 3 benchmark prompts (stored under `_eval/persona_probes/{agent}.yaml`) to the agent and run a 4-dim MT-Bench position-swap against the persona baseline. If mean_delta < −0.3 → flag in curator stats; auto-quarantine recent memory writes.
3. **Tiered memory mirroring MemGPT's core/archival split.** Define two memory tiers in the agent schema:
   - `core_memory` (small, persona-aligned, manually curated) — projected into the system prompt.
   - `archival_memory` (large, auto-curated) — retrieved on demand via mem0 search.
   Curator can write only to `archival_memory`. `core_memory` edits require operator approval (mirrors v6.0 bundled-skill gating).
4. **Persona-versioned memory records.** Every memory record carries `persona_version` (the agent's `persona_sha256` at write time). At retrieve time, weight memory by `persona_version_match ? 1.0 : 0.3`. Memory written under persona v1 doesn't dominate behavior under persona v2.

**Industry case:**
- **Letta/MemGPT**: hierarchical core/archival memory is the mitigation; the luhuidev.medium article "Memory Drift in Long-Running Agents" explicitly identifies "rewritten, compressed, and merged" memories as the degradation vector. Letta's *Memory Blocks* blog post acknowledges "limitations of current approaches for applications requiring long-term memory and coherence."
- **LangChain**: `ConversationSummaryMemory` progressively abstracts older turns — the running summary drifts away from the original persona vocabulary, a known trade-off documented in aurelio.ai's memory guide.

**Warning signs:**
- `hermes curator stats <agent_id>` shows feedback verdict trending toward `needs_work` over the last 20 runs after a long stable period.
- Per-prompt eval gate scores show >1.0 regression on prompts that previously passed.
- Operator perception: "the agent used to be sharp, now it's vague."

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (persona_sha256, core_memory, archival_memory fields), `02-ROUND-TABLE-PROTOCOL.md` (persona-drift probe scheduling).

---

### Pitfall 2: Stale Memory — agent cites platform rules / API quirks that no longer apply

**What goes wrong:**
The `compliance_gate` agent learned in 2026-Q2 that "抖音禁止前 3 秒出现 logo." By 2026-Q4 the platform guideline changed. The agent's memory still cites the old rule. Outputs get rejected by the platform. The operator loses trust in the agent's expertise.

**Why it happens:**
- Memory has no TTL by default. mem0 stores facts as flat natural-language strings "for fast retrieval" — there's no built-in notion of fact expiration. The mem0 production guide explicitly says "identity design is the hardest part" but doesn't address time-decay of the *correctness* of facts (only Hermes's `feedback_store.py` decays *weights*, not fact validity).
- Curator-driven updates are additive by design (v6.0 invariant). The system accumulates rules over time but rarely invalidates them. There's no "this fact is now wrong" signal unless a feedback `verdict=bad` with a `correction` text happens to mention the obsolete rule.
- Domain knowledge (platform guidelines, model APIs, tool versions) has a half-life. Memory systems designed for "user preferences" (which are stable) fail when applied to "domain rules" (which decay).

**Concrete mitigations:**

1. **Memory TTL field on every record.** Schema: `expires_at: datetime | None`. For domain-rule memories, the curator MUST set `expires_at = now + 90 days` (config: `memory.default_domain_ttl_days: 90`). For preference memories, `expires_at = None` (never expires). Retrieve-time filter: `WHERE expires_at IS NULL OR expires_at > now()`.
2. **Last-verified stamps mirroring v1 ref convention.** Every ref in `_shared/` already carries `verified_date: 2026-06`. Apply the same convention to memory records: `verified_at: datetime`, `verification_source: str` (URL / commit SHA / operator name). Curator's periodic re-verification pass (new phase) walks memories with `verified_at > 90 days` and flags them for re-verification.
3. **External-change detection hooks.** For domain-rule memories that cite an upstream URL (e.g. platform guideline page), the curator's re-verification pass fetches the URL, hashes the response, compares to `source_content_sha256`. If changed, the memory is auto-quarantined pending operator review.
4. **Supersession semantics (already shipped in v6.0 — extend it).** `feedback_store.py:_mark_superseded` already tracks supersession events for the same `sha256 + different verdict`. Extend the agent-memory layer with a `supersedes_memory_id` field so a new fact can explicitly invalidate an old one: `screenplay` learns "FLUX 2 replaces FLUX 1.x" → curator writes a new memory with `supersedes_memory_id=<old FLUX 1 memory>`. Retrieve-time filter excludes superseded memories (mirrors `_superseded_record_ids` set in `feedback_store.py`).
5. **Time-decay applied to confidence, not just weight.** v6.0 `compute_weight(ts)` decays retrieval weight. Extend the schema with `confidence: float [0,1]` that decays independently: `confidence(now) = base_confidence * exp(-age_days / half_life_days)`. Domain rules have `half_life_days = 90`; preferences have `half_life_days = 3650`. Below `confidence = 0.1`, memory is auto-archived.

**Industry case:**
- **mem0**: flat natural-language strings with no TTL — known weakness. The mem0 blog "How Mem0 Gives Stateless Edge Agents Long-Term Memory" explicitly says identity/namespace design is the hardest part and doesn't address fact decay.
- **LangChain `ConversationSummaryMemory`**: the running summary never invalidates old facts, just compresses them — facts that were once true become permanently embedded in the summary even after the world changes.

**Warning signs:**
- Agent output cites an API/tool version that has been bumped (e.g. references "FLUX 1.x" after FLUX 2 ship — exactly the v1 phantom-ref issue that triggered the original 5-phantom-ref cleanup).
- Platform rejection rate rises after a platform policy change.
- `hermes curator stats` shows recent feedback `verdict=bad` citing the same rule repeatedly.

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (memory record schema: `expires_at`, `verified_at`, `supersedes_memory_id`, `confidence`, `half_life_days`), `05-POC-PLAN.md` (re-verification pass as PoC acceptance criterion).

---

### Pitfall 3: Scoped Retrieval Performance Collapse — per-agent namespace kills mem0 query latency

**What goes wrong:**
Each of the 18 movie-expert agents gets its own memory scope. Naive implementation: every `mem0_search` query passes `filters={"user_id": user_id, "agent_id": agent_id}`. With 18 agents × 100 projects × 500 records/project = 900K records total, but per-agent queries return 5 records. Vector index performance collapses because the HNSW graph was built globally; per-agent filtering happens post-retrieval, scanning 50-100× more nodes than necessary.

**Why it happens:**
- mem0's filter model is `user_id` + `agent_id` + `run_id`. The documented scaling pattern is "scoping by user_id, agent_id, and run_id keeps a fleet of agents organized" — but this assumes per-user partitioning at the index level, not ad-hoc post-filtering. The actual mem0 Platform API behavior on filtered queries at scale is not well-documented; the 502-error bug fixed in the SDK changelog (filters as top-level fields) suggests the filter path has had production issues.
- Per-agent scoping is a Hermes-specific usage pattern. mem0's reference deployments are per-user (chatbot memory), where one user has thousands of records. The 18-expert-agents × 100-projects matrix is closer to a multi-tenant SaaS workload, which is not mem0's design center.
- The circuit breaker in `Mem0MemoryProvider` (`_BREAKER_THRESHOLD = 5`, `_BREAKER_COOLDOWN_SECS = 120`) means performance issues that cause timeouts cascade into "memory unavailable" rather than "memory slow" — the system fails opaque instead of failing fast.

**Concrete mitigations:**

1. **Physical partitioning over logical filtering.** Don't rely on mem0's `agent_id` filter alone. Use one mem0 project/workspace per agent (mem0 supports workspace-level isolation). The filter `user_id` then narrows within the agent's workspace. This requires 18 mem0 workspaces but gives O(per-agent-records) retrieval instead of O(all-records) post-filter.
2. **Local SQLite-backed scope index.** Mirror per-agent memory metadata (not embeddings) in `~/.hermes/agents/{name}/memory_index.db`. Pre-filter candidate memory IDs locally using `(agent_id, project_id, expires_at, supersedes_memory_id IS NULL)` SQL query, then pass the ID list to mem0 for re-ranking. Reduces mem0 query load by 50-100×.
3. **Per-agent memory budget cap.** Hard cap: each agent's active memory set ≤ 500 records (config: `agent.memory.max_records: 500`). Above the cap, the curator's consolidation pass merges low-confidence / old records into a single summary record. Mirrors LangChain's `ConversationTokenBufferMemory` hard ceiling pattern.
4. **Read-path latency SLO + observability.** Add `_latency_ms` field to every memory retrieval log entry. Stats CLI exposes p50/p95/p99 per agent. If p95 > 500ms, the circuit breaker trips earlier and the agent falls back to static `refs/` only (graceful degradation, not silent failure).
5. **Cache common queries.** Per-agent LRU cache of (query_sha256 → memory_results) with TTL = 1 hour. For repetitive round-table turns ("what's your take on X?", "what are the rules for Y?"), cache hits avoid the mem0 round-trip entirely.

**Industry case:**
- **mem0**: documented 502-error bug when `user_id`/`agent_id`/`run_id` sent as top-level request fields — the filter path has had production issues (SDK changelog).
- **LangChain `VectorStoreRetrieverMemory`**: known to degrade on filtered retrieval at scale because most vector stores do post-filtering, not pre-filtering. The "filter at retrieve time" pattern is documented in the LangChain memory types overview as a trade-off.

**Warning signs:**
- p95 memory retrieval latency > 1s in curator stats.
- Circuit breaker (`_BREAKER_THRESHOLD`) trips repeatedly for one agent but not others.
- Operator perception: "the agent is slow to respond when memory is enabled."

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`memory.max_records` field), `05-POC-PLAN.md` (latency SLO as acceptance criterion), `06-CROSS-REPO-IMPACT.md` (per-agent mem0 workspace provisioning).

---

### Pitfall 4: Cross-Project Memory Leakage — agent applies project-A learning inappropriately to project B

**What goes wrong:**
The `style_genome` agent works on Project P1 (an art-house short film) and learns "the audience responds well to muted color palettes and slow pacing." The operator then starts Project P2 (a high-energy TikTok vertical short drama) and the agent, retrieving all its memory, applies the P1 learning. P2's output is wrong for the new context.

**Why it happens:**
- mem0's filter model is per-user, not per-project. There's no `project_id` filter at the API level by default. The Mem0MemoryProvider shipped in v7.0 only filters by `user_id` + `agent_id`.
- The "agent gets smarter with more projects" value prop (PROJECT.md decision #6) creates pressure to share memory cross-project. But not all memory transfers cleanly.
- This is the classic cross-tenant isolation problem. Steve Kinney's research note: *"Isolation into a memory system designed as single-tenant is painful. Per-tenant storage is cheap. Cross-tenant data leaks are not."*

**Concrete mitigations:**

1. **Three-tier scoping in the agent schema.** Memory record carries `scope: "global" | "project" | "session"`:
   - `global`: applies to all projects (e.g. "FLUX 2 generates better faces than FLUX 1"). Eligible for cross-project retrieval.
   - `project`: scoped to one project (e.g. "this project's protagonist is introspective, prefers muted palette"). Project-scoped retrieval only.
   - `session`: ephemeral, single-conversation (mirrors current `run_id` semantics).
   Retrieve API takes `(agent_id, project_id?, scope_filter)` and SQL-filters accordingly.
2. **Default scope = `project`.** Curator's memory-write path defaults new memories to `scope="project"` unless the curator's LLM aggregation explicitly classifies it as cross-project (`scope="global"` with rationale). Conservative default prevents inappropriate cross-project transfer.
3. **Per-project override layer.** When the agent runs in Project P2, it retrieves: global memory + project-P2 memory. Project-P1 memory is invisible unless explicitly tagged `global`. Mirrors the "memory firewall" pattern recommended in micheallanham's tiered-architecture Substack.
4. **Project-ID required in retrieve call.** API contract: `retrieve(query, agent_id, project_id)` — `project_id` is required, not optional. Forces every caller to declare the project context. Round-table protocol passes `project_id` to every participant.
5. **Cross-project memory promotion gate.** A memory can be promoted from `scope="project"` to `scope="global"` only via curator review with operator approval (mirrors v6.0 `apply_patch_transaction` gating). Test invariant: `_check_global_scope_promotion_eligible(memory_record) -> bool` returns True only if (a) the memory has been cited in 3+ distinct projects AND (b) the curator's LLM aggregated it as cross-project-applicable with confidence ≥ 0.8.

**Industry case:**
- **mem0**: no built-in project/tenant concept; `user_id` + `agent_id` + `run_id` is the only scoping axis. Production users have rolled their own `namespace` field as a workaround (mem0 edge-agents blog).
- **Giskard "Cross Session Leak"**: documented as a real vulnerability class — "sensitive information from one user's session bleeds into another user's session." Same failure mode, just at user-level instead of project-level.
- **Echoleak (2024)**: cited in New America's AI agents & memory brief — a prompt hidden in an email caused an agent to leak private information from prior conversations. Cross-context bleed is a documented attack vector, not just a quality issue.

**Warning signs:**
- Agent in Project P2 references characters / palette / style from Project P1.
- Operator feedback: "why does the agent keep bringing up the other project?"
- Curator stats show one agent's memory retrieval is dominated by records written in a different project context.

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`scope: global|project|session` field, `project_id` required), `02-ROUND-TABLE-PROTOCOL.md` (project_id propagation in round-table turns).

---

### Pitfall 5: Curator Failure Modes — false-deletion, hallucinated-writes, bias-amplification

**What goes wrong:**
The curator's automated memory-update pass makes three classes of error:

- **False negative (deletes valuable memory):** Curator's LLM judges memory record #423 ("LTX2.3 fails on multi-character scenes with >2 faces") as obsolete based on a 6-month-old timestamp, but the memory is still accurate. The deletion loses hard-won operational knowledge.
- **Hallucinated write:** Curator's LLM, aggregating feedback, writes "operators have reported that drawer agent should always use seed=42 for reproducibility" — but no operator ever said that. The LLM confabulated a pattern from noisy feedback. The hallucinated rule then degrades all future drawer outputs.
- **Bias amplification:** Curator's feedback aggregation weighs negative feedback heavily (the `verdict in ("needs_work", "bad")` filter in `_scan_for_hot_skills`). One operator who gave 10× more negative feedback than positive has their preferences over-represented in the curator's output. The agent becomes tuned to one operator's taste.

**Why it happens:**
- LLM aggregation is lossy. v6.0 `aggregate_feedback` in `agent/evolution/insights.py` is an LLM call with a prompt; there's no statistical guard on what the LLM emits.
- The 3-feedback threshold (`DEFAULT_FEEDBACK_THRESHOLD_COUNT = 3`) is low. With 3 negative feedbacks, an insight is generated. With small samples, the LLM can confabulate patterns.
- The auto-apply eligibility check in v6.0 requires `confidence ≥ 0.8 + evidence_count ≥ 3 + mean_delta ≥ 0.1` (gated through eval). But the curator's *proposal* path (which writes to the review queue) has weaker gates — it just needs the LLM to emit an insight.
- Single-operator feedback bias is structural. The schema has no concept of "operator diversity" — `FeedbackRecord.source ∈ {cli, kais_aigc, manual}` doesn't distinguish operators.

**Concrete mitigations:**

1. **Never hard-delete.** Curator can only `archive` memory records (set `status="archived"`), mirroring the v1-v6 curator invariant "Never auto-deletes — only archives." Archived records stay retrievable for audit; restore is one CLI call.
2. **Hallucination guard: citation coverage ≥ N.** Every curator-generated memory write must include `evidence_chain: list[feedback_record_id]` with at least N=3 distinct feedback records supporting it. The curator's LLM is prompted to cite; post-hoc, `_check_evidence_coverage(new_memory, evidence_chain) -> bool` verifies each cited record's text actually overlaps the new memory semantically (embedding cosine ≥ 0.7). Failures are rejected.
3. **Operator diversity score.** Extend `FeedbackRecord` schema with `operator_id: str` (default `"default"`). Before generating an insight, `_check_operator_diversity(feedback_records, min_distinct_operators=2)` requires at least 2 distinct operators in the evidence chain. Single-operator feedback can't drive automated memory writes.
4. **Bias canary in eval gate.** The v6.0 eval gate (`gate.py:decide_verdict`) already runs MT-Bench position-swap. Add a "bias canary" prompt set: 5 prompts explicitly designed to surface single-operator preferences. If the patch improves operator-A's prompts but regresses on operator-B-equivalent prompts, the gate fails.
5. **Dry-run-first invariant (already shipped).** v6.0 `CURATOR_DRY_RUN_BANNER` enforces "DO NOT call skill_manage with action=patch, create, delete" on dry runs. Extend to memory writes: curator's memory-write path is dry-run by default, requires explicit `--apply-memory` flag for live writes. Same ast-walk invariant pattern as `TestNonBypassableHumanInLoop`.
6. **Bias audit log entry.** Every memory write records `evidence_operator_ids: list[str]` and `evidence_record_count: int` in the audit log. `hermes curator stats --bias-audit` surfaces over-represented operators.

**Industry case:**
- **Letta/MemGPT**: curator/consolidator LLM is documented to occasionally rewrite core memory with hallucinated facts. The Letta blog *Memory Blocks* acknowledges that compaction loses information.
- **AutoGen**: shared-state discussion (#7144) notes that agents operating from a common specification can amplify single-agent biases into the shared state.
- **Mem0**: server-side LLM fact extraction is the core feature; the mem0 security blog explicitly recommends "auditing extracted memories for hallucination" as a best practice.

**Warning signs:**
- Audit log shows memory writes with `evidence_record_count < 3`.
- `hermes curator stats --bias-audit` shows one `operator_id` in >50% of evidence chains.
- Operator perception: "the agent makes decisions based on rules I never gave it."

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`evidence_chain`, `evidence_operator_ids`, `status="archived"` fields), `05-POC-PLAN.md` (bias canary as PoC acceptance criterion).

---

### Pitfall 6: Memory Poisoning — malicious or wrong feedback permanently corrupts agent behavior

**What goes wrong:**
An operator (or an attacker who has compromised the feedback channel) deliberately submits `FeedbackRecord` entries with misleading corrections: "the screenplay agent should always end scenes with a twist, even for horror." The curator's aggregation picks this up, writes it as a memory record, and the agent now applies the wrong rule forever. The attack is stateful — the poisoning survives across sessions, restarts, and operator switches.

**Why it happens:**
- Memory poisoning is distinguished from prompt injection by being persistent. The MINJA (Memory INJection Attack) research demonstrates that attackers can inject malicious records using only queries and output observations — no direct memory write access needed.
- v6.0 `FeedbackStore` validates schema (Pydantic) but doesn't validate semantic content. The `correction: str` field accepts any text. The sha256 dedup only catches identical outputs — it doesn't catch semantically-equivalent attacks phrased differently.
- The `agent/curator_audit.py` log is tamper-evident (sha256-chained) — but tamper-evidence ≠ tamper-prevention. It detects after-the-fact that the chain was modified; it doesn't prevent a malicious write from entering the chain in the first place.

**Concrete mitigations:**

1. **Operator identity attestation.** Extend `FeedbackRecord` with `operator_signature: str` (HMAC over record fields using operator-specific key). The feedback ingestion validates the signature. Anonymous feedback is rejected by default (config: `feedback.require_signed: true`). This raises the bar from "anyone with CLI access can poison" to "requires operator key compromise."
2. **Outlier detection on feedback patterns.** Periodic job (curator stats phase) computes per-operator feedback distribution: verdict ratios, correction length, semantic similarity to existing memory. Operators whose feedback pattern deviates >2σ from the population mean are flagged for review. Mirrors anomaly detection in fraud systems.
3. **Memory-write rate-limit per operator.** No operator can write more than N memory-influencing records per day (config: `feedback.daily_memory_write_cap: 20`). Prevents bulk-poisoning attacks.
4. **Two-operator approval for high-impact memory.** Memory records that would change agent behavior on >50% of future prompts (estimated via embedding-based prompt coverage) require sign-off from a second operator. Mirrors dual-control patterns in security engineering.
5. **Tamper-evidence already shipped — extend to memory.** The v6.0 `curator_audit.py` sha256-chained JSONL covers `propose`/`apply`/`reject`/`rollback` actions. Extend the schema to cover memory writes (`action="memory_write"`). `hermes curator audit-log --verify` then catches tampering with memory history too.
6. **Quarantine on detected poisoning.** If the outlier detection flags an operator, all memory records with that operator in `evidence_operator_ids` are auto-quarantined (status=`quarantined`, excluded from retrieval) pending review. Mirrors incident-response patterns.

**Industry case:**
- **MINJA** (NeurIPS 2025): Memory INJection Attacks via Query-Only Interaction. Demonstrates that attackers can inject malicious records into agent memory using only queries. Direct cited precedent.
- **Palo Alto Unit 42**: "When AI Remembers Too Much" — demonstrates indirect prompt injection poisoning long-term memory in agents. Stateful attack vector.
- **Promptfoo LLM Security DB**: documents a specific vulnerability in RAG-based LLM agents where attackers inject malicious demonstrations.
- **OWASP LLM01:2025 Prompt Injection**: official OWASP guidance places prompt injection (which subsumes memory poisoning) as the #1 LLM application risk.

**Warning signs:**
- Audit log shows memory writes from operators not in the known operator list.
- One operator's feedback verdicts are 100% `bad` (attempts to drive negative learning).
- Agent behavior changes radically after a single session's feedback.
- `hermes curator audit-log --verify` reports chain breaks.

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`operator_signature`, `status="quarantined"` fields), `05-POC-PLAN.md` (outlier detection job as PoC acceptance criterion), `06-CROSS-REPO-IMPACT.md` (operator key management).

---

### Pitfall 7: Round-Table Memory Conflict — agents disagree because their memories disagree

**What goes wrong:**
In a round table, the `screenplay` agent (memory: "test audiences in this project respond well to bittersweet endings") and the `theory_critic` agent (memory: "tragedy endings test 23% better than bittersweet across all projects") reach contradictory conclusions. The round table deadlocks or, worse, the loudest-memory agent wins by sheer volume of citations rather than correctness.

**Why it happens:**
- Each agent has its own scoped memory. There's no memory-reconciliation layer across agents. Conflicts surface only at round-table time, when it's too late to fix the underlying disagreement.
- ReConcile (ACL 2024) demonstrates that round-table consensus among diverse agents improves reasoning, but the *Multi-Agent Debate with Memory Masking* paper (OpenReview) explicitly studies robustness to wrong memories from previous rounds — without explicit conflict resolution, the debate is contaminated.
- Hermes's current architecture (v1-v9) doesn't have round tables. v10.0 introduces them. There's no shipped conflict-resolution protocol.

**Concrete mitigations:**

1. **Memory annotation in round-table turns.** When an agent cites a memory in its turn, the citation includes `memory_id`, `confidence`, `scope` (global/project/session), and `evidence_record_count`. Other agents can challenge: "I disagree with memory_id #423 because my memory_id #612 contradicts it." This makes disagreement explicit and traceable.
2. **Coordinator (Hermes) arbitrates conflicts.** Per PROJECT.md decision #7, "Hermes 控 turn_order / max_rounds / schema / early_stop_rule." Add a memory-conflict-arbitration responsibility: when two agents cite conflicting memories, Hermes (the coordinator) extracts both cited memories, runs a comparator LLM pass ("which is more applicable in this project context?"), and broadcasts the resolution to all participants.
3. **Scope precedence rules.** When conflicts arise, scope precedence is: `session` > `project` > `global`. A project-scoped memory ("this project's audience prefers X") overrides a global-scoped memory ("audiences in general prefer Y"). The arbitration LLM is told the scope precedence and resolves accordingly.
4. **Confidence-weighted voting.** When N agents in a round table disagree, vote weighted by memory `confidence` field. If `screenplay` cites a 0.95-confidence project memory and `theory_critic` cites a 0.6-confidence global memory, screenplay's vote weighs more. Ties broken by coordinator.
5. **Conflict log for curator review.** Every round-table conflict is logged with both cited memories, the resolution, and the rationale. Curator's periodic pass reviews high-frequency conflicts (same memory pair conflicting >3 times) and may promote one to global scope or quarantine the loser.

**Industry case:**
- **ReConcile** (ACL 2024, arxiv 2309.13007): multi-model round-table consensus framework. Notes that without explicit consensus mechanisms, debates devolve into the loudest agent winning.
- **Multi-Agent Debate with Memory Masking** (OpenReview EdTt8nMAMA): explicitly studies the failure mode where wrong memories from previous debate rounds contaminate future rounds.
- **RoundTable** (arxiv 2411.07161v2): investigates group decision-making in decentralized MAS; notes that without structured arbitration, collective decisions are no better than individual ones.

**Warning signs:**
- Round table consistently deadlocks on the same topic across multiple sessions.
- One agent's citations dominate round-table outcomes (the "loud memory" effect).
- `hermes curator stats --conflict-log` shows the same memory pair conflicting >3 times.

**Phase to address:** `02-ROUND-TABLE-PROTOCOL.md` (memory citation schema in turns, coordinator arbitration rule, scope-precedence rule, conflict log).

---

### Pitfall 8: No Fitness Signal — agent might be getting worse, not better, and you can't tell

**What goes wrong:**
v10.0's value prop is "agent gets smarter with more projects." But there's no baseline measurement system. After 3 months of curator-driven evolution, you can't answer the question: "Is the `screenplay` agent actually better than it was 3 months ago?" The operator *feels* it's better, but there's no data. Worse, the operator might be wrong — silent regression.

**Why it happens:**
- v6.0 ships an eval gate (`gate.py:decide_verdict`) for *patch-vs-baseline* comparison, but the baseline is per-patch (rebuilt each time). There's no longitudinal baseline across patches.
- The eval gate caches a baseline (`scores.json`) but it's over-written on each `--rebuild-baseline`. There's no historical trend.
- "Agent fitness" is a fuzzier concept than "patch quality." A patch can improve one prompt and regress another. Aggregating to "agent fitness" requires a canonical prompt battery that doesn't drift.
- GetMaxim research notes agent A/B tests typically need 10,000+ trajectories per arm to distinguish real quality lift from model stochasticity — well beyond Hermes's scale.

**Concrete mitigations:**

1. **Frozen fitness battery per agent.** Each agent YAML declares `fitness_battery: path/to/battery.yaml` — a set of 10-20 prompts designed to exercise the agent's core capabilities. The battery is FROZEN at agent registration; changes require a new `persona_sha256`. Run on every curator tick + on demand via `hermes agent fitness <agent_id>`.
2. **Longitudinal fitness trend in audit log.** Every fitness run appends to `~/.hermes/agents/{name}/fitness_trend.jsonl`: `{ts, battery_version, mean_score, per_prompt_scores, persona_sha256}`. `hermes curator stats <agent_id> --fitness-trend` renders a sparkline. Regression (mean_score drop > 0.5 across 3 consecutive runs) triggers auto-quarantine of recent memory writes.
3. **A/B shadow mode.** Before applying a curator-driven memory change, the curator runs the fitness battery in shadow mode against (a) the current memory set and (b) the proposed memory set. If (b) regresses on any prompt by >1.0, the change is auto-rejected and queued for operator review.
4. **Distinguishing agent-drift from model-drift.** When the underlying LLM is updated (e.g. GLM 5.2 → 5.3), fitness scores may shift for reasons unrelated to memory evolution. Every fitness run records `model_id` and `provider`. Trend analysis groups by `model_id` to isolate memory-driven fitness changes from model-driven fitness changes.
5. **Fitness battery review cadence.** The battery itself can drift in relevance. Once per quarter, the operator reviews the battery prompts: are they still exercising the agent's current scope? Mirrors the v1 ref 90-day refresh cadence convention.

**Industry case:**
- **Label Studio "How to Evaluate Agent Memory"**: identifies four competencies memory agents need (accurate retrieval, test-time learning, long-range understanding, conflict resolution) and structures evals for each — directly applicable to fitness battery design.
- **Shaped.ai "A/B Testing Retrieval"**: documents Recall@K, NDCG, and other evaluation metrics for proving agents are getting better. Quantitative rigor over gut feel.
- **GetMaxim "A/B Testing Strategies for AI Agents"**: documents the 10,000-trajectories-per-arm rule of thumb. Sets expectations — at Hermes scale (handful of operators), fitness signals will be noisy.

**Warning signs:**
- No fitness_trend.jsonl exists for an agent.
- Mean fitness score has trended down over the last 5 runs.
- Per-prompt scores show high variance (some prompts always regress after curator updates).
- Operator perception of "agent is better" doesn't match the data.

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`fitness_battery` field, `fitness_trend.jsonl` location convention), `05-POC-PLAN.md` (fitness battery as PoC acceptance criterion, regression auto-quarantine).

---

### Pitfall 9: Memory Size Growth — context window overflows, summarization loses detail

**What goes wrong:**
Each project generates N memory records. With 18 agents × 100 projects × 200 records/project = 360K records system-wide. Even at per-agent scope, one agent may accumulate 20K records. Injecting all of them into every prompt overflows the context window. Naive summarization (a la LangChain `ConversationSummaryMemory`) loses operational detail — the summary says "operator has preferences about pacing" but loses the specific "operator said 2-minute scenes work better than 3-minute for this project type."

**Why it happens:**
- Memory accumulates monotonically. Without active compaction, growth is unbounded.
- Summarization is lossy. The LangChain trade-off is documented: `ConversationBufferMemory` keeps everything (context overflow) vs `ConversationSummaryMemory` compresses (loses detail). `ConversationSummaryBufferMemory` is the hybrid but requires careful threshold tuning.
- mem0's design assumes server-side semantic search returns only relevant memories on demand — but if the retrieve call returns 50 records because everything is "relevant," you're back to context overflow.

**Concrete mitigations:**

1. **Per-agent memory budget cap (already in Pitfall 3, reinforcing).** `agent.memory.max_records: 500`. Above the cap, curator's compaction pass must run.
2. **Three-tier compaction strategy.** Inspired by MemGPT's core/archival split + LangChain's hybrid:
   - **Tier 1 (core, ≤10 records):** always injected into prompt. Manually curated. The agent's "personality + hard rules."
   - **Tier 2 (working, ≤100 records):** retrieved on demand via mem0 search. Top-5 results injected. The agent's "recent operational context."
   - **Tier 3 (archival, ≤10000 records):** full history. Retrieved only via explicit tool call (`memory_recall`) for deep research. The agent's "long-term archive."
3. **Additive summarization with citation preservation.** When curator compacts 10 working-tier records into 1 summary record, the summary preserves `source_record_ids: list[record_id]`. The summary is a new record with `compaction: true`; the originals are archived (not deleted). If the summary is later found wrong, the originals can be restored.
4. **Semantic dedup beyond sha256.** v6.0 `FeedbackStore` dedups on `sha256` (exact text match). Memory dedup needs semantic match: `_check_semantic_duplicate(new_memory_text, existing_records) -> Optional[record_id]` using embedding cosine ≥ 0.92. Prevents 10 phrasings of the same rule from inflating the record count.
5. **Compaction log entry in audit log.** Every compaction records `compacted_record_ids`, `summary_record_id`, `pre_compaction_count`, `post_compaction_count`. `hermes curator stats --compaction-history` shows the trend.

**Industry case:**
- **LangChain**: `ConversationSummaryBufferMemory` is the canonical hybrid solution. Documented trade-off between token cost and detail loss.
- **MemGPT/Letta**: hierarchical memory (core/archival) is the architectural answer. The Memory Blocks blog acknowledges the limitations of flat memory approaches for long-term coherence.
- **mem0**: server-side fact extraction includes dedup, but the mem0 production guide acknowledges that "identity design is the hardest part" — without careful namespace/scope design, the fact store grows unbounded.

**Warning signs:**
- Per-agent memory record count > 1000.
- mem0 search returns >20 results for typical queries.
- LLM context window utilization >80% on every turn (memory is crowding out reasoning).
- Compaction pass hasn't run in >30 days (curator stats).

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (memory tier schema: core/working/archival, `max_records` per tier), `05-POC-PLAN.md` (compaction pass as PoC acceptance criterion).

---

### Pitfall 10: Privacy / Data Leakage — agent memory exposes project A's secrets in project B's round table

**What goes wrong:**
The `production` agent works on Project P1, which is under NDA with a client. Memory records include client name, budget, casting choices. Project P2 is a public-facing project. In a P2 round table, the `production` agent retrieves all its memory — including P1's NDA details — and cites them in the discussion. The NDA is breached.

**Why it happens:**
- Without per-project memory isolation (Pitfall 4), all of an agent's memory is eligible for retrieval in any context.
- Even with project scoping, the round-table coordinator may aggregate cross-project context for synthesis. If the coordinator's prompt includes "consult all your relevant experience," the agent may surface cross-project memory it shouldn't.
- Cross-session leak is a documented LLM vulnerability class. The Giskard "Cross Session Leak" guide identifies the same failure mode at user-level; project-level leakage is the same pattern one layer down.
- The "Echoleak" incident (2024): a prompt hidden in an email caused an agent to leak private information from prior conversations. Round-table discussions are an equivalent surface — a malicious project-P2 prompt could exfiltrate project-P1 memory.

**Concrete mitigations:**

1. **Per-project memory scoping (Pitfall 4 prerequisite).** Without this, privacy is impossible. `scope="project"` records are retrieveable only when `project_id` matches the current context.
2. **ND flag on memory records.** Schema field `confidentiality: "public" | "internal" | "confidential" | "nda"`. Default for new memories is `internal`. Records marked `confidential` or `nda` are:
   - Excluded from cross-project retrieval (even if scope="global").
   - Excluded from round-table coordinator's synthesis unless all participants are authorized.
   - Redacted in `hermes curator stats` JSON output (mirrors v6.0 T-33-01: stats --json emits counts only, no correction text, because corrections may contain PII).
3. **Ingestion-time redaction.** Memory write path runs `_redact_pii(text) -> text` before storing. Uses a regex + entity-recognition pass (similar to Presidio). Patterns: email addresses, phone numbers, ID numbers, project codenames from a denylist. Redacted text is stored; original is held in an encrypted vault (only retrievable via explicit operator command).
4. **Round-table confidentiality propagation.** When the coordinator initiates a round table, it broadcasts the project's confidentiality level to all participants. Participants filter their memory retrieval: `retrieve(query, project_id, confidentiality_filter="≤ current project's level")`. An agent working on a public project can't surface `confidential` memories from prior projects.
5. **Cross-project memory access audit.** Every retrieve call that returns records with `project_id != current_project_id` is logged. `hermes curator stats --cross-project-access` shows the trend. Spikes indicate either misconfiguration or active exfiltration.
6. **Right-to-be-forgotten.** Operator can purge all memory records for a project via `hermes agent memory purge --project P1`. Cascades to all agents, all scopes, including archival. Audit log records the purge event with the original record count.

**Industry case:**
- **Giskard "Cross Session Leak"**: documented data-exfiltration vulnerability class. Direct parallel at user-level.
- **Rafter "AI Agent Data Leakage"**: research showing "secrets stored in LLM context have a 78% chance of eventual exposure." Memory is essentially persistent context.
- **Orca Security "Bringing Memory to AI"**: covers security risks of MCP / A2A / agent context protocols — round-table equivalent surfaces.
- **Echoleak (2024)**: prompt hidden in content caused cross-conversation data leakage. Cited in New America's AI agents & memory brief.

**Warning signs:**
- Audit log shows cross-project memory retrieval increasing over time.
- Round-table outputs reference project codenames from unrelated projects.
- Operator (or client) reports unauthorized information disclosure.
- Ingestion-time redaction log shows consistently high PII detection rates (indicates sensitive content is reaching the memory layer).

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`confidentiality` field, redaction schema), `02-ROUND-TABLE-PROTOCOL.md` (confidentiality propagation, cross-project access filter), `06-CROSS-REPO-IMPACT.md` (PII vault provisioning).

---

## Moderate Pitfalls

### Pitfall 11: Memory Recall ≠ Memory Use — agent retrieves memory but ignores it

**What goes wrong:**
Memory is retrieved and injected into the prompt, but the LLM doesn't actually use it. The agent produces output that contradicts its own cited memory. Operator loses trust.

**Why it happens:**
- LLMs don't reliably attend to all context. Memory injected at the bottom of a long prompt may be ignored (the "lost in the middle" effect).
- The system prompt doesn't tell the agent how to use memory. Without explicit instructions ("if memory contradicts your default behavior, memory wins"), the LLM defaults to its pretrained priors.

**Concrete mitigations:**
1. Memory injection at top of system prompt, not bottom. Mem0MemoryProvider.`system_prompt_block()` is already positioned to do this — extend it for per-agent memory.
2. Explicit memory-use instruction in agent YAML: `memory_use_policy: "Memory records override defaults. If a retrieved memory contradicts your training, the memory wins for this project."`
3. Memory citation requirement in output schema: agent output includes `cited_memory_ids: list[memory_id]`. If the agent produces output without citing applicable memory, the eval gate flags it.

**Industry case:** MemGPT's core memory is explicitly injected at the top of the context for this reason.

**Phase to address:** `01-AGENT-REGISTRY-SCHEMA.md` (`memory_use_policy` field), `02-ROUND-TABLE-PROTOCOL.md` (citation requirement in turn schema).

---

### Pitfall 12: Cross-Agent Memory Contamination via Shared mem0 Workspace

**What goes wrong:**
Multiple agents share one mem0 workspace (to save infrastructure cost). One agent's memory bleeds into another agent's retrieval due to filter misconfiguration or workspace-wide semantic match.

**Why it happens:**
- mem0 workspaces are billable; temptation to consolidate.
- `Mem0MemoryProvider` filter model uses `user_id` + `agent_id`. If two agents share `user_id`, cross-agent retrieval is possible if the filter is incomplete.

**Concrete mitigations:**
1. One workspace per agent ( Pitfall 3 mitigation, reinforcing).
2. `agent_id` is REQUIRED on every memory write and every retrieve. API contract enforced at the MemoryProvider layer, not at the caller.
3. Periodic invariant test: `_check_workspace_isolation(agent_A, agent_B)` runs a retrieve for agent_A using agent_B's ID and asserts zero results.

**Industry case:** LinkedIn "When AI Memories Collide" — documents cross-agent data leakage from improperly isolated memories.

**Phase to address:** `06-CROSS-REPO-IMPACT.md` (workspace provisioning), `01-AGENT-REGISTRY-SCHEMA.md` (`mem0_workspace_id` field).

---

### Pitfall 13: Curator Loop Runaway — feedback threshold too low, curator proposes patches constantly

**What goes wrong:**
`DEFAULT_FEEDBACK_THRESHOLD_COUNT = 3` is low. In an active project, 3 negative feedbacks accumulate in a day. Curator runs nightly, generates patches nightly, fills the review queue with low-quality candidates. Operator drowns in review work and starts rubber-stamping approvals.

**Why it happens:**
- Thresholds were calibrated for v6.0 scale (single project). v10.0 has 18 agents × 100 projects = much higher feedback volume.
- No backpressure: the curator doesn't know the review queue is full.

**Concrete mitigations:**
1. Adaptive thresholds: `feedback_threshold_count = max(3, active_projects * 2)`. Scales with project count.
2. Queue-depth backpressure: if review queue > 50 pending patches, curator pauses proposal generation. Stats CLI surfaces the backlog.
3. Auto-reject old pending patches: pending patches older than 30 days are auto-rejected (status=`expired`). Forces operator to keep up or accept that old proposals lapse.

**Industry case:** v6.0 shipped with this threshold; the issue scales with v10.0's broader scope. Not a new industry precedent — an internal scaling concern.

**Phase to address:** `05-POC-PLAN.md` (threshold tuning as PoC parameter).

---

### Pitfall 14: Schema Migration Breaks Memory Store

**What goes wrong:**
v11.0 PoC adds `confidentiality` field to memory records. Existing 20K records have no `confidentiality` field. Read path fails or, worse, defaults to `public` for records that should be `confidential`.

**Why it happens:**
- Memory schema evolves. Backward compatibility is hard.
- The shipped v6.0 `_INDEX_VERSION = 1` in `feedback_store.py` is a forward-compat hook but only for `index.json`, not for record schema.

**Concrete mitigations:**
1. Schema version on every record: `schema_version: int`. Read path tolerates older versions; migration job backfills.
2. Migration safety: default unknown fields to the safest value, not the most permissive. Unknown `confidentiality` → `confidential` (not `public`).
3. Migration script with dry-run: `hermes agent memory migrate --dry-run` shows what would change before applying.

**Industry case:** Mem0 SDK changelog documents 502-error bug from mishandled fields — schema migration hazards are real in memory systems.

**Phase to address:** `04-MIGRATION-PATH.md` (schema migration plan), `05-POC-PLAN.md` (migration dry-run as acceptance criterion).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| `01-AGENT-REGISTRY-SCHEMA.md` | Persona drift (1) + Stale memory (2) + Cross-project leakage (4) + Privacy (10) | `persona_sha256` + memory tier schema + `scope`/`confidentiality`/`expires_at` fields |
| `02-ROUND-TABLE-PROTOCOL.md` | Memory conflict (7) + Privacy (10) + Recall-vs-use (11) | Citation schema, coordinator arbitration, scope precedence, confidentiality propagation |
| `04-MIGRATION-PATH.md` | Schema migration (14) | Schema-version field, safe defaults, dry-run migration |
| `05-POC-PLAN.md` | All pitfalls (PoC must demonstrate mitigations work) | Fitness battery, latency SLO, bias canary, compaction pass, threshold tuning — all as acceptance criteria |
| `06-CROSS-REPO-IMPACT.md` | Cross-agent contamination (12) + Privacy vault (10) | One mem0 workspace per agent, PII vault provisioning |

---

## Risk Register Summary (for v11.0 PoC plan)

| ID | Pitfall | Severity (H/M/L) | Mitigation cost (H/M/L) | PoC-acceptable deferral? |
|----|---------|------------------|------------------------|--------------------------|
| P1 | Persona drift | HIGH | M (persona hash + drift probe) | NO — load-bearing |
| P2 | Stale memory | HIGH | M (TTL + verified_at) | NO — load-bearing |
| P3 | Scoped retrieval perf | HIGH | H (per-agent workspace) | YES — can ship with single workspace, scale later |
| P4 | Cross-project leakage | HIGH | M (scope field + project_id required) | NO — load-bearing |
| P5 | Curator failure modes | HIGH | M (evidence coverage + operator diversity) | NO — load-bearing |
| P6 | Memory poisoning | HIGH | H (signed feedback + outlier detection) | PARTIAL — signed feedback is PoC must; outlier detection can defer |
| P7 | Round-table conflict | MEDIUM | M (coordinator arbitration) | NO — round-table is v10.0 core feature |
| P8 | No fitness signal | HIGH | M (fitness battery + trend) | NO — load-bearing |
| P9 | Memory size growth | MEDIUM | M (tier compaction) | YES — single-project PoC won't hit scale |
| P10 | Privacy / leakage | HIGH | H (redaction + confidentiality + vault) | PARTIAL — confidentiality field is PoC must; full PII vault can defer |
| P11 | Recall ≠ use | LOW | L (memory_use_policy) | YES — easy post-PoC addition |
| P12 | Cross-agent contamination | MEDIUM | M (workspace isolation) | YES — single-agent PoC won't hit |
| P13 | Curator runaway | LOW | L (adaptive thresholds) | YES — easy post-PoC tuning |
| P14 | Schema migration | MEDIUM | M (schema_version + safe defaults) | NO — must ship with v11 |

---

## Industry Reference Summary

| Project / Source | Cited For | Confidence |
|-----------------|-----------|------------|
| **MemGPT / Letta** (Packer et al. 2023; letta.com/blog) | Hierarchical memory (core/archival); persona drift; compaction loss | HIGH — Letta's own blog acknowledges these limits |
| **mem0** (mem0.ai/blog, docs.mem0.ai) | Namespace / identity design; 502-error filter bug; security best practices | HIGH — primary source for mem0-specific patterns |
| **LangChain** (ConversationBufferMemory / SummaryMemory / TokenBufferMemory docs + GitHub issue #16448) | Token explosion; summary-vs-detail trade-off; hybrid strategies | HIGH — well-documented trade-offs |
| **AutoGen** (microsoft/autogen discussion #7144; memori Labs blog) | Shared state handling; multi-agent context pollution | MEDIUM — discussion threads, not formal docs |
| **ReConcile** (ACL 2024, arxiv 2309.13007) | Round-table consensus among diverse agents | HIGH — peer-reviewed |
| **Multi-Agent Debate with Memory Masking** (OpenReview EdTt8nMAMA) | Robustness to wrong memories in debate rounds | MEDIUM — peer-reviewed |
| **MINJA** (NeurIPS 2025, arxiv 2606.04329v1) | Memory injection attacks via query-only interaction | HIGH — peer-reviewed |
| **Palo Alto Unit 42** (unit42.paloaltonetworks.com) | Persistent memory poisoning from indirect prompt injection | HIGH — vendor research |
| **OWASP LLM01:2025 Prompt Injection** | Industry-standard prompt injection taxonomy | HIGH — OWASP authoritative |
| **Giskard "Cross Session Leak"** | Cross-session / cross-tenant data exfiltration vulnerability class | HIGH — vendor research |
| **Label Studio "How to Evaluate Agent Memory"** | Four competencies for memory agent eval (fitness battery design) | MEDIUM — vendor blog, well-researched |
| **GetMaxim "A/B Testing Strategies"** | 10,000-trajectories-per-arm rule for statistical significance | MEDIUM — vendor blog |
| **Echoleak incident (2024)** | Cross-conversation data leakage via prompt injection | MEDIUM — incident report cited in New America brief |

---

## Sources (Verifiable URLs)

**Industry documentation (HIGH confidence):**
- mem0 official: https://docs.mem0.ai/changelog/sdk (502-error bug fix)
- mem0 blog (identity/namespace): https://mem0.ai/blog/remote-memory-for-ai-agents-running-at-the-edge
- mem0 blog (security): https://mem0.ai/blog/ai-memory-security-best-practices
- Letta blog (memory blocks): https://www.letta.com/blog/memory-blocks/
- Letta blog (benchmarking): https://www.letta.com/blog/benchmarking-ai-agent-memory/
- LangChain ConversationSummaryBufferMemory: https://langchain-doc.readthedocs.io/en/latest/modules/memory/types/summary_buffer.html
- LangChain ConversationTokenBufferMemory: https://reference.langchain.com/python/langchain-classic/memory/token_buffer/ConversationTokenBufferMemory
- OWASP LLM01:2025: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Palo Alto Unit 42 (memory poisoning): https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/

**Peer-reviewed research (HIGH confidence):**
- ReConcile (ACL 2024): https://aclanthology.org/2024.acl-long.381/
- MINJA systematic study: https://arxiv.org/html/2606.04329v1
- Black-box Persona Drift Detection: https://arxiv.org/html/2605.09863v1
- AutoGen paper: https://ar5iv.labs.arxiv.org/html/2308.08155
- RoundTable (decentralized MAS): https://arxiv.org/html/2411.07161v2

**Vendor / community research (MEDIUM confidence):**
- Giskard Cross Session Leak: https://www.giskard.ai/knowledge/cross-session-leak-when-your-ai-assistant-becomes-a-data-breach
- Label Studio agent memory eval: https://labelstud.io/learningcenter/how-to-evaluate-agent-memory/
- GetMaxim A/B testing: https://www.getmaxim.ai/articles/a-b-testing-strategies-for-ai-agents-how-to-optimize-performance-and-quality/
- Shaped.ai A/B testing retrieval: https://www.shaped.ai/blog/ab-testing-retrieval-how-to-prove-your-agent-is-getting-better
- Multi-Agent Debate with Memory Masking: https://openreview.net/forum?id=EdTt8nMAMA
- Rafter AI agent data leakage: https://rafter.so/blog/ai-agent-data-leakage-secrets-management
- Multi-agent memory engineering (MongoDB): https://medium.com/mongodb/why-multi-agent-systems-need-memory-engineering-153a81f8d5be

**Hermes internal (HIGH confidence, codebase-grounded):**
- `agent/curator.py` — v6.0 `_feedback_scan_phase` + `_run_llm_review`
- `agent/feedback_store.py` — `FeedbackStore` with sha256 dedup, time-decay, supersession
- `agent/evolution/*` — insights, diff_generator, apply, queue, evol02_generator
- `agent/curator_audit.py` — sha256-chained JSONL audit log
- `plugins/memory/mem0/__init__.py` — `Mem0MemoryProvider` with circuit breaker, user_id+agent_id filters
- `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` (kais-hermes-skills repo) — canonical v6.0 architecture
- `.planning/PROJECT.md` — v10.0 7 locked design decisions

---

*Owned by v10.0 design milestone phase 44. Cross-referenced by `01-AGENT-REGISTRY-SCHEMA.md` (memory schema fields), `02-ROUND-TABLE-PROTOCOL.md` (memory conflict resolution), `05-POC-PLAN.md` (PoC risk register). No parallel phase touches this file.*
