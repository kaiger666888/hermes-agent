# Phase 2: EXPERT-HOOK (Commercial Engine) - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 builds the `hook_retention` expert end-to-end — the commercial engine that ensures 短剧 content produced by the suite is cinematically correct AND commercially viable. This expert owns 3-second hook design, 付费卡点 (paywall cliffhanger) placement, per-platform 爆款公式 branching, and the 钩子/爽点/卡点 marker schema that integrates with `screenplay.emotion_curve`.

Phase 2 also closes the compliance contract left open by Phase 1: when compliance_marketing flagged paywall-related constraints (per-platform 付费机制 rules), HOOK is the consumer. After Phase 2, the suite can produce commercially-optimized 短剧 end-to-end.

In scope:
- Author `skills/movie-experts/hook_retention/SKILL.md` (bilingual EN YAML + CN prose, per-platform branching)
- Author 4 reference files:
  - `references/three-second-hooks.md` (5-type taxonomy × 3 examples + frame-by-frame + 5-tier scoring)
  - `references/conflict-escalation.md` (阶梯式升级 + 击中点 / 爽点 placement density)
  - `references/paywall-design.md` (3-5 卡点 per 10 ep + 3-tier strength + 完播率 1.5x/≤3s rules + 转发 triggers)
  - `references/vertical-pacing.md` (竖屏 faster cut density + BGM-driven sync with composer.coupled_beat + 字幕 design language)
- Author 5 eval prompts (1 per 爆款公式 branch + 1 general)
- Define `钩子 / 爽点 / 卡点` JSON marker schema for screenplay.emotion_curve integration
- Wire bidirectional related_skills edges: ↔ screenplay (hook rewrites), ↔ editor (retention pacing), ↔ compliance_marketing (close Phase 1 contract), → composer (BGM sync)

Out of scope:
- Phase 3 screenplay deep-refactor (HOOK leaves a stable marker schema contract)
- Phase 4 EXPERT-CINE camera framing for hooks (separate concern; HOOK only references "visual jolt" abstractly)
- N≥20 full eval run (Phase 6)
- Automated 完播率 telemetry ingestion (no new infra)
- BGM composition itself (composer expert's domain; HOOK only specifies sync requirements)

</domain>

<decisions>
## Implementation Decisions

### Hook Taxonomy & 3-Second Hook Design
- **5 hook types:** 情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩
- **3-second frame-by-frame structure:**
  - **0-1s:** Attention-grab — visual/audio jolt (sudden movement, loud sound, shocking image)
  - **1-2s:** Context-establish — who/where/what's-at-stake in 1 sentence equivalent
  - **2-3s:** Hook-pin — explicit promise of payoff ("you won't believe what happens next")
- **5-tier strength scoring:** 🎯 bullseye / ✅ strong / ⚠️ weak / ❌ broken / 💀 anti-hook
- **3 concrete examples per type (15 total)** — each example includes setup, frame-by-frame breakdown, expected 完播率 impact

### 付费卡点 (Paywall Cliffhanger) Strategy
- **Density:** Min 3-5 卡点 per 10-episode 短剧; ≥1 hard 卡点 at end of every paid episode; soft 卡点 mid-episode optional
- **3-tier strength scoring:** 🟢 must-watch-next / 🟡 curious-but-skippable / 🔴 weak-resolve
- **完播率 optimization rules:**
  - **1.5x pace rule** — average cut every 1.5 seconds
  - **≤3s dead air** — no silent/static stretches > 3 seconds
  - **BGM-driven sync** — cuts align with composer.coupled_beat timestamps
- **5 转发 trigger categories:** 情感共鸣 / 反转冲击 / 共识认同 / 视觉震撼 / 实用价值

### Per-Platform 爆款公式 Branching
- **5 distinct branches:**
  - 抖音-男频 (action/power/revenge themes; faster cuts; harder 卡点)
  - 抖音-女频 (romance/family/emotional themes; softer hooks; emotional 卡点)
  - 快手-草根 (slice-of-life/relatable; grassroots aesthetic; community-driven hooks)
  - 小程序剧-长集数 (longer episodes 3-5 min; serialized 卡点 across episodes)
  - 通用 fallback (when platform unknown)
- **Fixed 5-field schema per branch:** `核心动机 / 情感曲线 / 节奏密度 / 付费卡点位置 / 典型案例`
- **Cross-link to Phase 1 viral-element-catalog.md:** each branch entry references 情感钩/冲突钩/etc. taxonomy + risk badges (🟢🟡🔴)
- **5 eval prompts (1 per branch + 1 general)**

### Screenplay Integration & Output Schema
- **3 marker types:** `钩子` (hook anchor) / `爽点` (payoff peak) / `卡点` (cliffhanger)
- **JSON schema per marker:**
  ```json
  {
    "type": "钩子" | "爽点" | "卡点",
    "timestamp": "MM:SS",
    "intensity": 1-5,
    "setup_callback": "what earlier scene set this up",
    "payoff_callback": "what later scene resolves this"
  }
  ```
- **Bidirectional screenplay edge:** HOOK outputs markers → screenplay.emotion_curve; screenplay scene-list → HOOK for hook insertion point recommendations
- **Bidirectional editor edge:** HOOK pacing rules → editor.cut_density; editor.cut_decisions → HOOK for 卡点 validation

### Claude's Discretion
- Exact wording of frame-by-frame breakdowns in 15 examples
- Specific timestamps in 完播率 optimization examples
- Concrete numbers for per-platform 节奏密度 (within 1.5x rule constraint)
- Order of refs in `## References` table
- Final wording of eval prompts (shape is fixed by Phase 0 judge_prompt.md template)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 0 + 1)
- **`skills/movie-experts/_shared/glossary.md`** — Already has 钩子/卡点/爆款/男频/女频/完播率 entries; HOOK refs link rather than duplicate
- **`skills/movie-experts/_shared/SKILL-LAYOUT.md`** — Reference anatomy spec (Source/Copyright/Last-verified/Summary/Heuristics)
- **`skills/movie-experts/_shared/RAG-INVOCATION-PATTERN.md`** — Provider-agnostic pattern for HOOK's RAG calls
- **`skills/movie-experts/_shared/known-external-models.yaml`** — 77-entry allowlist
- **`skills/movie-experts/_shared/platform-comparison.md`** — Cross-platform matrix from Phase 1; HOOK can extend with 节奏密度 column if useful
- **`skills/movie-experts/compliance_marketing/references/viral-element-catalog.md`** — Phase 1 爆款 catalog; HOOK cross-links to this
- **`skills/movie-experts/compliance_marketing/references/platform-specs-{douyin,kuaishou,miniprogram}.md`** — Phase 1 platform rules; HOOK 爆款公式 branches consume these
- **`scripts/verify_skill_references.py`** — Lints HOOK SKILL.md; must exit 0
- **`skills/movie-experts/_eval/runner.py`** — HOOK eval prompts must be runnable through it
- **`skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml`** — Pattern for eval prompt YAML

### Established Patterns
- **SKILL.md frontmatter** schema (from compliance_marketing/SKILL.md): name / description / version / author / license / platforms / prerequisites.tools / metadata.hermes.{tags, related_skills, expert_id, metrics}
- **`## References` table** at top of every SKILL.md (Phase 0 FOUND-07 contract)
- **Provider-agnostic tokens** in SKILL.md body (NO hardcoded `fact_store` / `mem0_search` / `cosyvoice_api` — conditional phrasing only per Phase 1 CR-03 lesson)
- **CN prose with EN headers** for bilingual content
- **Per-platform branching** with H3 subsections (Phase 1 pattern from compliance_marketing)

### Integration Points
- **`skills/movie-experts/hook_retention/`** — New expert directory
- **2 existing experts need `related_skills` APPEND updates:** screenplay, editor (and compliance_marketing — close Phase 1 contract by adding HOOK there too)
- **`skills/movie-experts/_eval/prompts/hook_retention_demo.yaml`** — New prompt file (5 prompts)
- **Backward-compat HARD RULE:** Don't modify any existing `expert_id`; only ADD hook_retention to related_skills arrays
- **HOOK must close Phase 1 contract:** compliance_marketing SKILL.md already lists `hook_retention` one-directionally; Phase 2 must reciprocate (add compliance_marketing to HOOK's related_skills array AND optionally update compliance_marketing to formalize the bidirectional edge)

</code_context>

<specifics>
## Specific Ideas

- **3-second hook examples should span diverse genres:** romance / revenge / family / mystery / comedy — at least 1 example per type per genre for max reuse
- **付费卡点 examples should include both hard (episode-ending) and soft (mid-episode) variants** — at least 2 hard + 1 soft per scenario
- **完播率 1.5x rule should include exceptions:** emotional close-ups may extend to 4-5s; BGM swells may extend cuts; document when to break the rule
- **5 爆款公式 branches should each include ≥ 2 典型案例** (real or composite) — concrete enough for downstream agents to pattern-match
- **钩子/爽点/卡点 markers should support multi-episode callbacks** — `setup_callback` may reference prior episode; `payoff_callback` may reference future episode
- **At least 2 of 5 eval prompts must involve 🟡 risk-level 爆款 elements** — exercises HOOK's compliance-aware design (cross-link to Phase 1 risk badges)
- **HOOK should explicitly cite Phase 1 platform-spec refs** for per-platform 付费机制 rules — single source of truth

</specifics>

<deferred>
## Deferred Ideas

- **Automated 完播率 telemetry ingestion** — Out of scope per "no new infra"; HOOK only documents the rules, doesn't measure
- **BGM composition itself** — Composer expert's domain; HOOK only specifies sync requirements (cut aligns with coupled_beat)
- **EXPERT-CINE camera framing for hooks** — Phase 4; HOOK references "visual jolt" abstractly without prescribing focal length / camera move
- **N≥20 full eval run** — Phase 6; HOOK ships 5 prompts
- **Per-platform-specific 通用 fallback enrichment** — Phase 6 polish
- **A/B test framework for hook variants** — Out of v1 scope
- **Real-time hook performance dashboard** — Out of v1 scope

</deferred>
