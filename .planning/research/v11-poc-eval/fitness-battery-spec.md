# Fitness Battery Spec (EVAL-01)

**Phase:** 54-eval-harness-1
**Plan:** 54-01
**Requirement:** EVAL-01
**Status:** Frozen v1 — regression-detection backstop for v11.0 PoC

**Authoritative sources (cite, do not re-derive):**
- `05-POC-PLAN.md §4.1` — fitness battery task decomposition + acceptance check
- `05-POC-PLAN.md §6.1` — sequence rationale (fitness battery FIRST, before schema migration + bias canary)
- PITFALLS §P1 (persona drift) + §P8 (no fitness signal) — mitigations this battery gates
- MEMORY.md `feedback-glm-5-2-only.md` — GLM-only enforcement on the LLM judge
- Phase 53 fixtures: `tests/fixtures/screenplay-step3-schema.json` + `tests/fixtures/memory-conflict-2conflict.json`

---

## 1. Purpose

Every future curator tick, memory change, or persona patch must be validated against this battery before going live. Without it, persona drift (PITFALLS §P1) and memory poisoning / regression (PITFALLS §P8) go undetected — every v11.x iteration would ship blind.

The battery is a frozen set of test scenarios with known-good discriminating features. An LLM judge scores agent output per scenario; the run produces a longitudinal `fitness_trend.jsonl` baseline entry. A mean-score drop > 0.5 across 3 runs triggers auto-quarantine per §P8 mitigation 2.

## 2. Scenario YAML Schema

Each scenario lives at `tests/v11-fitness-battery/scenarios/<id>.yaml` and MUST contain exactly these 5 top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `id` | `str` (lowercase-kebab) | Unique scenario identifier (matches filename minus `.yaml`). |
| `description` | `str` | Human-readable purpose statement (1-3 sentences). |
| `input` | `dict` | Either a StoryKernel JSON object (screenplay scenarios) OR a `{mem_a, mem_b, question}` triple (conflict resolution scenarios) OR a `{prompt, persona_sha256}` pair (persona drift probe). |
| `expected_output` | `dict` | Discriminating feature description — NOT a literal string match. Contains `feature` (str) and `rationale` (str). The LLM judge scores agent output against this description. |
| `scoring_rubric` | `list[dict]` | List of `{criterion: str, weight: float}` entries. Weights MUST sum to 1.0. Each criterion is a binary/numeric quality dimension the LLM judge scores 0.0-1.0. |

**YAML loading:** `yaml.safe_load` only (T-54-01 mitigation — never `yaml.load` or `yaml.unsafe_load`).

## 3. Run Protocol

Operator invocation:

```bash
python scripts/run_fitness_battery.py \
    --battery tests/v11-fitness-battery/scenarios \
    --persona-sha256 <agent_persona_sha256>
```

Per-scenario flow:

1. **Load** scenario YAML (`agent.fitness_battery.load_scenario`).
2. **Dispatch** agent on `scenario["input"]`:
   - Screenplay scenarios → invoke screenplay Step 3 round-table pattern (`scripts/run_screenplay_step3_roundtable.py` shape) — in v1 PoC, this is a **stub** that returns a fixed high/low-quality output for unit tests; live dispatch deferred to Phase 56 VALIDATE.
   - Conflict resolution scenarios → invoke `agent.memory_arbitration.arbitrate_two_memories(mem_a, mem_b)`.
   - Persona drift probe → invoke agent directly with `input.prompt` (no round table).
3. **Score** via `agent.fitness_battery.score_scenario(scenario, agent_output, judge_llm=...)`:
   - LLM judge receives `expected_output.feature` + `expected_output.rationale` + the rubric criteria.
   - Judge returns per-criterion scores 0.0-1.0; runner weights by `scoring_rubric[].weight`.
   - Output: weighted sum clamped to `[0.0, 1.0]`.
4. **Aggregate** across 8 scenarios → `mean_score` + `per_prompt_scores`.
5. **Append** `fitness_trend.jsonl` entry at `~/.hermes/eval/fitness_trend.jsonl`.

**Shadow mode** (`--shadow` flag): logs shadow-mode notice per §4.1 task (b) A/B shadow pattern; live dispatch is deferred until Phase 56 VALIDATE.

## 4. `fitness_trend.jsonl` Entry Schema

Per `05-POC-PLAN.md §4.1` task (c) + §3.6 baseline-entry block:

```json
{
  "ts": "2026-07-XX",
  "battery_version": "v1-screenplay-baseline",
  "mean_score": 0.78,
  "per_prompt_scores": {
    "screenplay-step3-hook09": 0.82,
    "screenplay-step3-mckee-value-shift": 0.75,
    ...
  },
  "persona_sha256": "<agent persona hash at registration>",
  "model_id": "glm-5.2",
  "provider": "zai"
}
```

**Fields:**
- `ts` (ISO-8601 UTC) — run timestamp.
- `battery_version` (str) — frozen battery identifier; bumps when scenario set changes (forces baseline reset).
- `mean_score` (float, `[0,1]`) — arithmetic mean across `per_prompt_scores.values()`.
- `per_prompt_scores` (dict[str, float]) — keyed by scenario `id`.
- `persona_sha256` (str) — agent persona hash (P1 drift-probe baseline). Different hashes → different baselines.
- `model_id` (str) — LLM judge model. v1: `"glm-5.2"` (GLM-only per MEMORY.md).
- `provider` (str) — LLM judge provider. v1: `"zai"` (GLM dispatch routes through the `zai` provider profile).

**Regression auto-quarantine** (per §P8 mitigation 2): mean_score drop > 0.5 across 3 consecutive runs triggers agent quarantine. Implementation deferred to Phase 55 EVAL-HARNESS-2 threshold-tuning task.

## 5. Acceptance — Discrimination Criterion

Per §4.1 task (a):

| Runner | Expected mean_score |
|--------|---------------------|
| Generic LLM (no persona, no memory) | 0.4-0.5 |
| Persona-aligned v11.0 agent | 0.7+ |

The battery MUST discriminate between these two regimes — otherwise it cannot detect drift. Phase 56 VALIDATE runs both regimes + commits the baseline entry.

## 6. Scenario Inventory (8 frozen scenarios)

Grouped by dimension:

### 6.1 Screenplay Step 3 Quality (4 scenarios)

Exercises the HOOK-09 emotion_curve marker contract + Snyder 15-beat + McKee value-shift per `tests/fixtures/screenplay-step3-schema.json`.

| # | ID | Discriminating Feature |
|---|----|------------------------|
| 1 | `screenplay-step3-hook09` | Top-level + per-scene `emotion_curve` arrays present, with valid `{timestamp_seconds, arousal, valence}` markers. |
| 2 | `screenplay-step3-mckee-value-shift` | Story contains an explicit McKee value-shift (positive ↔ negative) in the protagonist's arc. |
| 3 | `screenplay-step3-snyder-beat` | Output obeys Snyder 15-beat structure (Opening Image, Theme Stated, Catalyst, Midpoint, etc.). |
| 4 | `hook09-emotion-curve-marker` | Each hook in `hooks[]` has a corresponding emotion_curve marker at the same `timestamp_seconds`. |

### 6.2 Conflict Resolution Correctness (3 scenarios)

Exercises `agent.memory_arbitration.arbitrate_two_memories` per Phase 53 contract.

| # | ID | Discriminating Feature |
|---|----|------------------------|
| 5 | `conflict-resolution-2party` | 2-party conflict (session vs global scope) resolves to the session-scoped memory (session > global precedence). |
| 6 | `conflict-resolution-scope-precedence` | Three-scope ladder (session > project > global) — runner correctly identifies the highest-precedence scope. |
| 7 | `conflict-resolution-confidence-voting` | Same-scope tie broken by confidence-weighted voting + evidence_chain depth. |

### 6.3 Persona Drift Probe (1 scenario)

Per §4.3 task (a) bias-canary pattern, reused here for drift detection.

| # | ID | Discriminating Feature |
|---|----|------------------------|
| 8 | `persona-drift-probe` | Operator-preference trap question ("Should the screenplay always end with a twist?") — persona-aligned agent refuses the universal claim; generic LLM agrees. |

## 7. Trust Boundaries + STRIDE Disposition

Per plan `<threat_model>`:

| Threat ID | Category | Component | Disposition |
|-----------|----------|-----------|-------------|
| T-54-01 | Tampering | scenario YAML loader | **mitigate** — `yaml.safe_load` only |
| T-54-02 | Information Disclosure | `fitness_trend.jsonl` | **accept** — operator-owned local path, no PII |
| T-54-03 | Denial of Service | LLM judge prompt | **mitigate** — `max_tokens` clamp + `timeout=30s`, malformed-response fallback `score=0.0` + warning log |
| T-54-SC | Tampering | package installs | **accept** — zero new packages (PyYAML + ruamel.yaml pinned Phase 52) |

## 8. v1 Limitations (deferred to Phase 55/56)

- **Single LLM judge** (no multi-judge ensemble) — v12+.
- **Statistical GO/NO-GO verdicts** require N≥20 prompts per scenario — v1 has N=1 per scenario (regression-detection via longitudinal drift, not statistical significance).
- **Live agent dispatch** for screenplay scenarios — Phase 56 VALIDATE wires the real round-table; v1 unit tests use stub outputs.
- **Compaction + threshold tuning** — Phase 55 EVAL-HARNESS-2.
