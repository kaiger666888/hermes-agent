# Pitfalls Research — AI Short-Drama Skill Suite (movie-experts v2)

**Domain:** RAG-augmented skill experts for AI 短剧/微电影 creation (Hermes Agent subsystem)
**Researched:** 2026-06-15
**Overall confidence:** HIGH (grounded in actual `skills/movie-experts/` files + Hermes codebase concerns + well-known LLM-as-judge research)

---

## Summary

This project stacks **seven compounding risk dimensions**: (1) RAG quality vs prompt bloat, (2) LLM-as-judge eval validity, (3) Chinese short-drama domain specifics (copyright, 平台审核, platform-algorithm divergence), (4) bilingual EN/CN drift, (5) Hermes integration edge cases, (6) project-management over-reach (18 experts at once), and (7) **the most urgent** — existing skills already contain concrete factual errors (phantom `wan22_video` plugin that does not exist in `plugins/video_gen/`; fabricated "168K controlled performance tokens" claim in performer/SKILL.md) that will silently propagate into refs and poison downstream experts if not fixed first. The single biggest delivery risk is **refusing to time-box**: trying all 18 experts in parallel will collapse under corpus-curation workload and GLM overload (already demonstrated 2/4 mapper failures per milestone context).

---

## Pitfalls by Category

### 1. RAG-Augmented Skills

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **Refs bloat SKILL.md context window** | High | refs/ folder > 50KB per expert; SKILL.md starts citing ref filenames in-body; quality thresholds reference external material | Hard cap: SKILL.md ≤ 12KB in-body; refs loaded via memory-plugin query on demand, not preloaded | REFS-A, EXPERT-* |
| **Poor retrieval quality (semantic mismatch)** | High | judge scores "uses ref" but output contradicts ref content; refs include generic theory but lack specific 数字 (3-秒 hook, 付费卡点 timing) | Curate refs with concrete, citable specifics — not textbooks; pair every ref with a "how to cite this" example in SKILL.md | CORPUS-01, REFS-A |
| **Outdated refs (AI tool versions drift fast)** | Critical | refs cite specific FLUX / Wan / CosyVoice versions older than current; drawer references generic "FLUX" while Hermes ships FLUX 2 | Pin a quarterly ref-refresh cadence in DOC-01; in each ref header, mark `version_verified_against: <tool-version>` and `last_verified: YYYY-MM`; treat missing version stamp as review blocker | CORPUS-01, DOC-01 |
| **Generic refs add no value** | Medium | ref reads like Wikipedia summary; judge cannot distinguish ref-augmented from non-augmented output | Reject refs during AUDIT-01 that merely restate common knowledge; require each ref to contain ≥ 1 concrete heuristic not in base model training (e.g., "抖音 完播率 drops at 7s for romance genre — front-load conflict before 5s") | AUDIT-01, REFS-A |
| **Conflicting refs across experts** | Medium | drawer ref says "总 LoRA weight ≤ 1.5"; animator ref says "use single LoRA only"; colorist vs drawer disagree on color_intent schema | Add cross-expert ref-consistency check to EVAL-01; maintain a shared `glossary.md` under `skills/movie-experts/` defining all terms + parameter ranges | REFS-A, EVAL-01 |
| **RAG masks weak prompts** | High | judge scores "improvement" but ablation (refs off) shows baseline prompt was the real weakness | EVAL-01 MUST include ablation runs: (a) old SKILL no refs, (b) new SKILL no refs, (c) new SKILL + refs. If (b)→(c) gap < (a)→(b) gap, refs are theater — fix prompt first | EVAL-01 |
| **Memory plugin not installed → silent no-RAG** | High | skill works but produces generic output; no error surfaced; user assumes "skill is broken" | SKILL.md must include a **probing instruction**: "Before answering, check if memory plugin is available; if not, surface a warning 'running in static-refs-only mode' and proceed with refs/ folder" — graceful degradation must be **explicit, not silent** | REFACTOR-A, all EXPERT-* |
| **Phantom model references (already present in v1)** | Critical | `animator/SKILL.md` references `wan22_video` but `plugins/video_gen/` contains only `fal` and `xai` — no wan22 plugin; performer claims "168K controlled performance tokens" (no such mechanism exists) | AUDIT-01 MUST grep every SKILL.md against `plugins/`, `agent/`, and tool registry; every tool/model reference must resolve to an actual installed provider. Add a CI lint script: `scripts/verify_skill_references.py` | AUDIT-01 (do FIRST) |

### 2. LLM-as-Judge Double-Blind Eval

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **Positional bias (~45% preference flip on order swap)** | High | A-vs-B and B-vs-A produce opposite winners for same pair; judge prefers "first presented" disproportionately | Per MT-Bench / Chatbot Arena findings: (1) run BOTH orderings for every pair, (2) report concordance rate, (3) discard pairs where order matters as "tie-noise" | EVAL-01 |
| **Prompt sensitivity** | High | judge rubric tweaks flip 20%+ of verdicts | Lock judge prompt in version control; treat rubric as fixed for a full eval cycle; report evals under a specific judge-prompt commit hash | EVAL-01 |
| **Judge recognizes style fingerprints** | Medium | judge systematically prefers outputs with EN-vs-CN ratio matching its own training; judges familiar with 短剧 patterns over-reward genre conformity | Use a model DIFFERENT from the skill-execution model as judge (avoid GLM judging GLM); consider an open-weight panel (Qwen-Max, GLM, Claude) and report cross-model agreement | EVAL-01 |
| **Single judge vs panel** | High | single-judge verdicts treated as ground truth | v1: panel of 2 (cheap + expensive). Report agreement rate. If < 70%, escalate to 3rd judge. Single-judge acceptable ONLY for triage, never for go/no-go on launch | EVAL-01 |
| **Small-sample statistics (N too low)** | Critical | judging 5 prompts per skill and declaring "winner"; p-values never computed | Minimum N=20 prompts per skill per condition for paired comparison; report effect size (Cohen's d or win-rate + 95% CI via bootstrap); declare "no significant difference" if CI crosses 0 | EVAL-01 |
| **Judge self-preference (GLM judging GLM)** | High | judge disproportionately favors outputs from same model family | Use orthogonal judge: skill runs on GLM-5.x → judge on Claude/Qwen-Max (or vice versa); document judge model in every eval report | EVAL-01 |
| **Metric drift across skills** | Medium | each skill invents own quality dimensions, so cross-skill comparison impossible | Define a shared rubric skeleton (e.g., 专业度 / 可执行性 / 一致性 / 创新性, each 1-5) that every skill eval instantiates with skill-specific sub-criteria | EVAL-01 |
| **Reviewer cherry-picks prompts** | Medium | benchmark prompts lean toward expert's strengths | Prompts authored by a DIFFERENT person than the skill author; prompts reviewed by third party before eval runs | EVAL-01 |

### 3. Short Drama (短剧) AI Generation

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **Copyright on existing 短剧 samples** | Critical | CORPUS-01 ingests full 短剧 episodes from 抖音/快手; refs reproduce > 30s of dialogue | STRICT policy: use only (a) creator-licensed samples with written permission stored in `refs/LICENSE/`, (b) fair-use excerpts ≤ 30s with attribution, (c) public-domain / 短剧 references provided by platform official guides. Store license provenance per-ref. **Copyright infringement on 短剧 is a real lawsuit risk in CN.** | CORPUS-01 (BLOCKER for any sample source) |
| **平台审核 rejection patterns (CN content compliance)** | Critical | generated 短剧 includes 涉政/涉黄/暴力/封建迷信/医疗/金融 content → 平台审核 rejects or 整改 | EXPERT-COMPLI MUST encode current (2026) 平台审核 rules from each major platform's published guidelines: 抖音/快手/微信视频号/小程序剧. Update quarterly. Refs must cite specific platform rule numbers, not paraphrase | EXPERT-COMPLI |
| **Hook / retention mismatched to platform algorithm (抖音 vs 快手 differ)** | High | EXPERT-HOOK outputs single "universal hook formula" ignoring platform | EXPERT-HOOK must branch per platform: 抖音 (前3秒强冲突, 7秒完播率, 算法偏好强情绪), 快手 (老铁文化, 信任前置, 算法偏好真实感), 小程序剧 (付费卡点位置, 集数结构, 投流 ROI). Refs must document platform divergence explicitly | EXPERT-HOOK |
| **付费卡点 design feels manipulative** | High | user feedback "强行卡点"; cliffhanger positions feel arbitrary; users churn after first paid episode | EXPERT-HOOK must include 付费卡点 伦理准则: 卡点必须服务叙事而非纯商业; avoid 卡点 at < 30s into episode; document user-churn risks per 卡点 pattern | EXPERT-HOOK |
| **爆款公式 over-fitting** | Medium | EXPERT-HOOK only knows 3 爆款公式 from 2024; all outputs converge to same template | Track ≥ 10 distinct 爆款公式 in refs; rotate recommendation; flag when skill output cluster-similarity > 0.7 (compute via judge pairwise similarity) | EXPERT-HOOK, CORPUS-01 |
| **竖屏 composition issues** | Medium | drawer/animator output uses 16:9 composition for 竖屏 短剧 (9:16) | EXPERT-CINE must enforce 9:16 compositional rules as default for 短剧 context; coordinate with drawer (override default 1024x1024 → 768x1344 or similar) | EXPERT-CINE, drawer refactor |
| **小程序剧 vs 平台短剧 conflation** | Medium | single "短剧 expert" treats 小程序剧 (集数制, 付费解锁) the same as 平台短剧 (单集, 流量分成) | EXPERT-HOOK and EXPERT-COMPLI must explicitly distinguish the two product forms; refs must mark which form they apply to | EXPERT-HOOK, EXPERT-COMPLI |

### 4. Bilingual Content (EN / CN)

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **Translation drift between EN/CN** | High | EN section says X, CN paragraph says Y; metric names differ between languages | Single source of truth: EN YAML metadata is canonical; CN prose must reference the same metric IDs; bilingual review checklist in DOC-01 | BILINGUAL-01 |
| **CN cultural context lost in EN** | Medium | EN reader sees "Hook & Retention" but lacks context on 抖音 algorithm specifics; EN community assumes Netflix-style retention | EN sections must include "CN context" callouts when a concept is platform-specific to Chinese 短剧; do NOT translate 短剧 as "short drama" without gloss | BILINGUAL-01 |
| **EN community resistance to "Chinese-first" content** | Medium | PRs from Hermes upstream complain "too China-specific"; EN users can't relate to 抖音/快手 specifics | Frame as: skill is **bilingual-capable**, EN core works for general short-film; CN-specific content is in `refs/cn/` and gated behind `if 短剧-context`. Make CN-first content clearly optional, not default | BILINGUAL-01, DOC-01 |
| **Domain term inconsistency** | High | 运镜 vs "camera movement" vs "cinematography" used interchangeably; 抽卡 left as pinyin in EN sections | Maintain `glossary.md` (EN term ↔ CN term ↔ definition ↔ preferred form per skill) — this is a load-bearing artifact, treat as first-class | BILINGUAL-01, DOC-01 |
| **Refs written in CN only, EN contributors blocked** | Medium | EN contributor opens ref file, sees only 中文, gives up | Refs default to CN (per project decision), but each ref must include a 2-3 sentence EN abstract at top + EN term mapping table. Full translation out of scope | CORPUS-01, BILINGUAL-01 |

### 5. Hermes Framework Integration

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **`_ra()` lazy-import pattern mishandled** | Medium | skill tries to import memory plugin eagerly at skill-load time → slows Hermes startup; or imports in module scope → breaks skill discovery | Skills are pure markdown — no Python imports. Memory plugin access is via **prompted instruction** ("if you can query memory, do X") not via direct API. SKILL.md authors MUST NOT assume Python execution context | REFACTOR-A, EXPERT-* |
| **Skill loading edge cases** | Medium | new expert not picked up by Hermes skill discovery; metadata.hermes schema validation fails | Add a `scripts/lint_skill_metadata.py` that validates every SKILL.md frontmatter against the documented schema; run before commit. Per CONCERNS.md, skills execute arbitrary Python at import — but movie-experts are markdown-only, so risk is purely metadata | DOC-01 |
| **Memory plugin not always installed (graceful degradation)** | High | user without memory plugin sees skill fail or produce no output; no warning surfaced | SKILL.md must explicitly instruct: "If memory plugin unavailable, fall back to refs/ folder and emit a warning to user." Graceful degradation is **explicit**, never silent | REFACTOR-A, all EXPERT-* |
| **Backward compat: existing 14 experts widely referenced** | Critical | changing `expert_id` or restructuring `related_skills` graph breaks downstream user workflows | HARD RULE (per PROJECT.md Key Decisions): existing `expert_id` values are FROZEN; new experts append, never rename; `related_skills` additions OK, deletions require migration note in DOC-01 | REFACTOR-A (audit before refactor) |
| **Single-external-provider limit in MemoryManager** | Medium | memory plugin only supports one external vector provider; project assumes multi-source RAG | Confirm with Hermes core: is the limit real? If yes, document in DOC-01 that movie-experts use a single memory namespace; do not architect for multi-provider fusion in v1 | DOC-01 (verify with Hermes) |
| **Skill schema validation not enforced** | Medium | new SKILL.md has typo in `metadata.hermes.tags`, silently fails to register | Pre-commit hook: validate YAML frontmatter against JSON schema (PROJECT.md should define this). Without enforcement, errors ship silently | DOC-01 |
| **Skills Guard flags refs as injection** | Low | Hermes' Skills Guard scanner (per CONCERNS.md §Security) flags ref content that looks like prompt injection | Run Skills Guard over `skills/movie-experts/references/` during AUDIT-01; if flagged, document why content is intentional (e.g., example prompts that LOOK like injection but are teaching material) | AUDIT-01 |

### 6. Project Management

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **Trying all 18 experts at once** | Critical | roadmap has single "do all 18" phase; no sequencing; reviewer overwhelmed | Phase the work: (P1) AUDIT + fix phantom refs in existing 14 [BLOCKER], (P2) REFACTOR + REFS for 3-4 highest-value experts (screenplay, drawer, animator, EXPERT-HOOK), (P3) the rest. NEVER parallelize all 18 | Roadmap design |
| **Breaking user workflows with refactors** | High | REFACTOR-A changes output schema of existing expert; downstream user pipelines break | REFACTOR-A must produce a `MIGRATION.md` per expert documenting schema changes; preserve old field names as deprecated aliases for one release cycle | REFACTOR-A |
| **RAG on skills that don't need it** | Medium | refactoring foley/spatial_audio with extensive refs but those skills are procedural and have minimal "industry knowledge" gap | AUDIT-01 must explicitly classify each of 14 experts as: (a) needs deep refs, (b) needs light refs, (c) needs no refs (procedural only). Do NOT refactor uniformly | AUDIT-01 |
| **Eval harness more complex than skills evaluated** | High | EVAL-01 takes longer than any single expert; harness has its own bugs | Time-box EVAL-01 to a maximum of N weeks. v1 eval = ONE judge script, ONE rubric template, batch runner. No fancy UI. Ship simple, iterate | EVAL-01 |
| **GLM overload with parallel agents** | High | milestone context already notes "2/4 mapper failures" from GLM overload | NEVER run > 2 GLM-heavy skills in parallel during REFACTOR. Sequential per-expert refactor preferred. Document GLM context-budget per skill in DOC-01 | All phases |
| **Scope creep into Hermes core** | Medium | "we need to add a memory plugin feature" or "let's tweak skill discovery" | PROJECT.md already excludes this — but mid-project pressure will tempt. ANY commit touching `agent/`, `gateway/`, `plugins/` outside `skills/movie-experts/` is OUT OF SCOPE — escalate, do not implement | All phases |
| **Corpus curation overwhelms single contributor** | High | CORPUS-01 4 sources × 18 experts = 72 source-expert cells; one person cannot curate all | Phase CORPUS-01: (P1) 1 source × 4 experts as proof; (P2) scale to 2 sources × 8 experts; (P3) full 4×18. Do NOT commit to full grid upfront | CORPUS-01 |
| **"Deep refactor" decision lacks measurable justification** | Medium | PROJECT.md commits to "deep refactor not light enhancement" but no baseline metric exists to prove depth | EVAL-01 must run on EXISTING 14 skills BEFORE any REFACTOR. Establish baseline. If baseline shows experts are already adequate, downgrade REFACTOR scope | EVAL-01 (must precede REFACTOR-A) |

### 7. AI Generation Tool Version Drift (URGENT — already broken in v1)

| Pitfall | Severity | Warning Signs | Prevention | Phase |
|---------|----------|---------------|------------|-------|
| **drawer/SKILL.md references FLUX 1.x workflows** | High | drawer cites "FLUX" without version; LoRA workflow assumes FLUX 1.x API; Hermes may ship FLUX 2 with different LoRA interface | AUDIT-01: grep `skills/movie-experts/drawer/SKILL.md` for all versioned tool references; verify against current Hermes plugin versions; update or mark as "needs verification" | AUDIT-01 |
| **animator/SKILL.md references phantom `wan22_video` plugin** | Critical | `plugins/video_gen/` contains only `fal` and `xai` — NO `wan22` plugin; skill outputs `model: wan22_video` which will fail at execution time | Either (a) add `plugins/video_gen/wan22/` (out of scope per PROJECT.md), OR (b) rewrite animator to reference ACTUAL available video providers (fal, xai). Verified: `ls plugins/video_gen/` → `fal xai` only | AUDIT-01 (BLOCKER) |
| **performer/SKILL.md claims "168K controlled performance tokens"** | High | claim is fabricated — no mechanism in Hermes provides 168K controlled tokens; misleading metric in description (line 3) and header | Strip the claim. Replace with actual mechanism: "ExBxSxP 4D parametric encoding for character performance design" (the matrix is real, the token count is invented) | AUDIT-01 |
| **CosyVoice / other audio tool versions drift** | Medium | voicer/SKILL.md may reference specific TTS model versions | Same audit pattern: grep, verify, update | AUDIT-01 |
| **Refs cite versioned tool features that get deprecated** | High | CORPUS-01 ingests a 2024 article on Wan2.2 best practices; Wan2.5 ships in 2026 with breaking changes | Every ref header MUST include `tool_version: <X>`, `verified_date: <YYYY-MM>`, `deprecated_risk: low/medium/high`. Refs with `high` deprecated_risk get quarterly re-review | CORPUS-01, REFS-A |
| **Tool name typos / aliases** | Medium | skill says "wan2.2" in prose but "wan22_video" in params; or "Cosy Voice" vs "CosyVoice" | `glossary.md` MUST define canonical tool names; lint script flags deviations | DOC-01, AUDIT-01 |
| **Provider capability drift** | Medium | drawer assumes FLUX supports negative prompts (some versions don't); animator assumes fal supports 6s clips (provider limit may differ) | Per-provider capability matrix in `refs/tool_capabilities.md` updated quarterly | CORPUS-01 |

---

## Top 5 Critical Risks

1. **Phantom model references already shipped (P0 BLOCKER)** — `animator/SKILL.md` emits `model: wan22_video` but no such plugin exists; `performer/SKILL.md` advertises fabricated "168K controlled tokens". If these propagate into refs/ and downstream experts, the entire suite's credibility collapses. **AUDIT-01 must run a reference-verification pass FIRST, before any new expert is built.**

2. **Copyright infringement on 短剧 samples (legal blocker)** — Chinese 短剧 copyright enforcement is active (2024-2026 saw multiple 高额判决). Ingesting 抖音/快手 episodes without license → real lawsuit exposure for project maintainers. CORPUS-01 must enforce license provenance per-ref, not per-folder.

3. **LLM-as-judge eval invalidity (decisions made on noise)** — Without (a) both orderings, (b) N ≥ 20, (c) cross-model panel, (d) ablation against no-RAG baseline, every "improvement" claim is unfounded. Worse: PROJECT.md commits to deep refactor based on presumed gaps — if baseline eval shows experts are already adequate, the entire REFACTOR-A scope is unjustified.

4. **18-expert parallel execution collapse** — Milestone context already notes "2/4 mapper failures from GLM overload". Scaling to 18 experts in parallel guarantees cascading failures. Phase strictly: AUDIT (4 wks) → REFACTOR 4 highest-value (6 wks) → REFS for those 4 (parallel, 4 wks) → EVAL (2 wks) → decide go/no-go before touching remaining 10 + 4 new.

5. **平台审核 non-compliance in generated 短剧** — EXPERT-COMPLI is a CN legal exposure surface. If it generates content that violates 抖音/快手 content rules, downstream users face 账号封禁 / 内容下架 / 行政处罚. Refs MUST cite current platform-published guidelines (not blog summaries), updated quarterly.

---

## Phase-Specific Warnings (mapped to PROJECT.md Active items)

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **AUDIT-01** | Discovery is shallow — team audits prompt quality but skips tool-reference verification | Add a `scripts/verify_skill_references.py` that greps every model/tool name in SKILL.md against actual `plugins/` inventory. Make AUDIT-01 BLOCK on this script passing. |
| **REFACTOR-A** | Refactor breaks backward compat on `expert_id` / `related_skills` | HARD FREEZE on existing `expert_id` strings; refactor may edit prompt body, metrics, thresholds — NOT identifiers |
| **REFS-A** | Refs become "Wikipedia summaries" with no citable specifics | Each ref must contain ≥ 1 concrete heuristic / number / rule that is NOT in the base model's training distribution. Reject during PR review. |
| **EXPERT-CINE** | Overlaps with existing scene_builder (机位规划) and animator (动态执行) | EXPERT-CINE owns **镜头语言** (semantics); scene_builder owns **空间布局** (geometry); animator owns **动态执行** (motion). Document boundary in DOC-01 before writing SKILL.md |
| **EXPERT-HOOK** | Treats 短剧 as monolithic; ignores 抖音 vs 快手 vs 小程序剧 divergence | First section of EXPERT-HOOK SKILL.md must be "Platform Branching" — every hook pattern tagged with applicable platform |
| **EXPERT-PROD** | Reinvents scene_builder / continuity capabilities | EXPERT-PROD owns **制作管理** (casting, scheduling, 服化道) — explicitly NOT camera/blocking (that's scene_builder) and NOT shot continuity (that's continuity) |
| **EXPERT-COMPLI** | Generates 平台审核 advice from training data (stale) — 2026 platform rules differ from 2024 | Refs MUST cite official platform guideline URLs + version dates. EXPERT-COMPLI output MUST include a "reviewed against <guideline version>" attestation. |
| **CORPUS-01** | Copyright exposure from 短剧 sample source | Per-ref LICENSE.md required; samples > 30s require written creator permission stored in repo |
| **BILINGUAL-01** | Translation drift over time as EN and CN sections evolve independently | Single-source: EN YAML metadata canonical; CI lint verifies CN prose references same metric IDs |
| **EVAL-01** | Single-judge, low-N, no-ablation → noise treated as signal | Mandatory: both orderings, N ≥ 20, panel of 2+ judges, ablation vs no-RAG baseline |
| **DOC-01** | Documentation drifts from actual skill behavior | DOC-01 auto-generated from SKILL.md frontmatter where possible; manual sections reviewed at every phase transition |

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| RAG pitfalls | HIGH | Standard RAG failure modes; verified against actual SKILL.md content |
| LLM-as-judge pitfalls | HIGH | MT-Bench / Chatbot Arena positional-bias findings are well-documented |
| 短剧 domain pitfalls | MEDIUM | Based on general CN short-video knowledge; specific 2026 platform rules need verification at EXPERT-COMPLI phase |
| Bilingual pitfalls | HIGH | Standard cross-lingual content drift |
| Hermes integration | MEDIUM | Some claims (single-external-provider limit) need verification against Hermes core code |
| Project management | HIGH | Self-evident from milestone context (GLM overload already observed) |
| Version drift | HIGH | **Verified directly**: `ls plugins/video_gen/` shows only `fal xai` — `wan22_video` does NOT exist |

---

## Open Questions (flag for phase-specific research)

1. Does Hermes MemoryManager truly support only one external vector provider? Needs verification against `agent/memory_*.py` or equivalent before DOC-01 finalizes architecture description.
2. What is the canonical 短剧 sample source with permissive license? (Public-domain 短剧 are rare; creator-licensed samples require outreach.)
3. Does Hermes ship FLUX 1.x or FLUX 2? (drawer's LoRA workflow assumption depends on this — needs `plugins/image_gen/` inventory.)
4. Current (2026-Q2) 抖音/快手/视频号 published content guideline versions for EXPERT-COMPLI refs.
5. Should EVAL-01 use open-weight judges (Qwen-Max, GLM, Yi) or also include Claude/GPT-4o for diversity? Trade-off: cost vs bias-diversity.
6. Is the "168K controlled tokens" claim in performer/SKILL.md a typo for some real concept, or pure fabrication? (Likely fabricated — strip in AUDIT-01.)

---

*Sources: direct file inspection of `skills/movie-experts/{drawer,animator,performer}/SKILL.md`, `plugins/video_gen/` directory listing, `.planning/codebase/CONCERNS.md`, `.planning/PROJECT.md`. LLM-as-judge positional-bias finding from MT-Bench research lineage (well-known, LOW risk of being outdated). 短剧 / 平台审核 domain specifics based on Chinese short-video ecosystem knowledge as of 2026-Q2.*
