# Requirements Archive: v1 Movie-Experts Suite v2

**Archived:** 2026-06-15
**Status:** ✓ SHIPPED — All 62 v1.5 requirements delivered across Phases 0-6.

> **Note on checkbox state:** The `[ ]` marks below are preserved verbatim from `.planning/REQUIREMENTS.md` at archive time. They do NOT indicate incomplete delivery — every requirement listed here was shipped in v1. See `.planning/MILESTONES.md` for the shipped artifact inventory and `.planning/STATE.md` § Deferred Items for the small set of operator-deferred follow-ups (live-run execution, CN legal review, etc.).

For current requirements, see `.planning/REQUIREMENTS.md`.

---

# Requirements: Movie-Experts Suite v2 — 短剧/微电影创作专家增强

**Defined:** 2026-06-15
**Core Value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases. Derived from `.planning/research/SUMMARY.md` Table Stakes + Recommended Build Order.

### FOUND — Foundation (Cross-Suite)

- [ ] **FOUND-01**: AUDIT-01 produced per-expert `GAP-REPORT.md` for all 14 existing experts (knowledge gaps, prompt weak points, stale metric, missing refs topics)
- [ ] **FOUND-02**: `scripts/verify_skill_references.py` CI lint greps every model/tool name in SKILL.md against `plugins/` inventory
- [ ] **FOUND-03**: Phantom references stripped/rewritten (no more `wan22_video`, no more "168K controlled tokens", no more FLUX 1.x sampler parameters)
- [ ] **FOUND-04**: Pre-refactor baseline snapshot exists at `_eval/baseline/<expert>/SKILL.md` for all 14 existing experts, tagged `eval-baseline-v1`
- [ ] **FOUND-05**: Standard skill layout documented and enforced (`SKILL.md` + `references/*.md` + `_eval/prompts/`)
- [ ] **FOUND-06**: Provider-agnostic RAG invocation pattern documented (no hard-coded tool names; conditional phrasing; graceful degradation when memory plugin absent)
- [ ] **FOUND-07**: References table present at top of every SKILL.md (When to Read + Contents columns per ref)
- [ ] **FOUND-08**: All 14 existing `expert_id` values preserved unchanged (backward-compat HARD RULE)
- [ ] **FOUND-09**: `_shared/glossary.md` EN↔CN term dictionary published (运镜/cinematography/camera movement, 钩子/hook, 卡点/paywall cliffhanger, 爆款/viral formula, 男频/女频, etc.)

### COMPLI — EXPERT-COMPLI (合规与宣发)

- [ ] **COMPLI-01**: `skills/movie-experts/compliance_marketing/SKILL.md` exists with bilingual content (EN structure + CN descriptions/examples)
- [ ] **COMPLI-02**: `references/cn-content-rules.md` covers 网信办 AI 标识办法 (2025-09-01) + AI 漫剧 备案 regime (2026-04-01) + 内容审核红线 checklist
- [ ] **COMPLI-03**: `references/platform-specs-douyin.md` with current (2026-Q2 verified) 抖音 creation/distribution rules
- [ ] **COMPLI-04**: `references/platform-specs-kuaishou.md` with current 快手 rules
- [ ] **COMPLI-05**: `references/platform-specs-miniprogram.md` with current 微信小程序剧 rules (incl. 付费机制 / 备案要求)
- [ ] **COMPLI-06**: `references/viral-element-catalog.md` flags 爆款 elements overlapping with 审核风险 + offers 降级方案
- [ ] **COMPLI-07**: 5 eval prompts cover diverse compliance scenarios (AI 标识 / 备案材料 / platform cuts / 红线 review / 未成年人保护)
- [ ] **COMPLI-08**: Bidirectional edges in related_skills graph to/from screenplay, editor, hook_retention, style_genome, drawer (for posters)
- [ ] **COMPLI-09**: All COMPLI refs carry `verified_date: YYYY-MM` stamp (quarterly refresh cadence documented)

### HOOK — EXPERT-HOOK (钩子与留存)

- [ ] **HOOK-01**: `skills/movie-experts/hook_retention/SKILL.md` exists with bilingual content
- [ ] **HOOK-02**: `references/three-second-hooks.md` covers hook taxonomy (情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩)
- [ ] **HOOK-03**: `references/conflict-escalation.md` covers 阶梯式升级 pacing + 击中点 / 爽点 placement density
- [ ] **HOOK-04**: `references/paywall-design.md` covers 付费卡点 placement (短剧 min 3-5 of 10 ep) + 完播率 optimization (1.5x pace rule, no >3s dead air) + 转发 triggers
- [ ] **HOOK-05**: `references/vertical-pacing.md` covers 竖屏 faster cut density + BGM-driven hook sync with `composer.coupled_beat` + 字幕 design language
- [ ] **HOOK-06**: Per-platform 爆款公式 branching in SKILL.md (抖音 男频/女频 / 快手 草根 / 小程序剧 long episodes)
- [ ] **HOOK-07**: Bidirectional edges in related_skills (↔ screenplay for hook rewrites; ↔ editor for retention pacing)
- [ ] **HOOK-08**: 3-5 eval prompts covering hook design / 卡点 placement / pacing for retention
- [ ] **HOOK-09**: Output schema markers documented (钩子/爽点/卡点) feeding into `screenplay.emotion_curve`

### REFACTOR — Top-4 Existing Experts RAG (深度重构 + refs)

- [ ] **REFACTOR-01**: `screenplay/SKILL.md` deep-refactored (RAG instructions + revised quality thresholds + refined metrics) with 4-6 curated refs (Save the Cat, Story by McKee, 短剧 pacing)
- [ ] **REFACTOR-02**: `editor/SKILL.md` deep-refactored with 4-6 refs (In the Blink of Eye / Murch Rule of Six, classical editing rhythm, montage theory, FxRxT axis compliance)
- [ ] **REFACTOR-03**: `colorist/SKILL.md` deep-refactored with 4-6 refs (If It's Purple / Bellantoni, Color Correction Look Book / Hurkman, 色彩心理学 cross-cultural CN variations)
- [ ] **REFACTOR-04**: `style_genome/SKILL.md` deep-refactored with 4-6 refs (expanded director archive 30-50 names, genre DNA, cross-cultural style)
- [ ] **REFACTOR-05**: 3 eval prompts per refactored expert (12 total)
- [ ] **REFACTOR-06**: Post-refactor eval comparison vs baseline produced for all 4 experts
- [ ] **REFACTOR-07**: Ablation comparison done (old-no-refs vs new-no-refs vs new-with-refs) per PITFALLS #8
- [ ] **REFACTOR-08**: Each ref contains ≥ 1 concrete heuristic/number/rule NOT in base model training (no Wikipedia summaries)

### CINE — EXPERT-CINE (运镜/摄影指导)

- [ ] **CINE-01**: `skills/movie-experts/cinematographer/SKILL.md` exists with bilingual content
- [ ] **CINE-02**: `references/shot-grammar.md` covers 景别 (shot size vocabulary) + 视角 (angle vocabulary) + composition systems (rule of thirds, Mise-en-scène checklist)
- [ ] **CINE-03**: `references/axis-rules.md` covers 180°/30° rules + eyeline match + match cut design
- [ ] **CINE-04**: `references/vertical-screen-framing.md` covers 9:16 composition rules + safe zones for 抖音/快手 UI overlays
- [ ] **CINE-05**: `references/camera-motion-catalog.md` covers movement vocabulary (dolly/pan/tilt/crane/tracking/handheld/steadicam) + camera-move → prompt-token mapping for video gen models (dolly-in ↔ "slow push-in" etc.) + movement-emotion dictionary
- [ ] **CINE-06**: AI-native lens constraints documented (which focal lengths render reliably in current FLUX 2 / Veo 3.1 / Kling v3 / Sora)
- [ ] **CINE-07**: Documented handoff boundary vs scene_builder (CINE=intent, scene_builder=feasibility) and animator (CINE=motion design, animator=execution) and editor (CINE=composition, editor=180° axis compliance)
- [ ] **CINE-08**: Edges in related_skills graph to scene_builder, animator, editor, screenplay, continuity, drawer, hook_retention
- [ ] **CINE-09**: 3-5 eval prompts covering shot design / camera-move selection / vertical framing / axis compliance

### EVAL — LLM-as-Judge Double-Blind Harness

- [ ] **EVAL-01**: `_eval/runner.py` implements MT-Bench position-swap pattern (every prompt runs in both A/B and B/A orderings; disagreement = tie)
- [ ] **EVAL-02**: `_eval/snapshot.py` captures/reads baseline snapshots tagged `eval-baseline-v1`
- [ ] **EVAL-03**: `_eval/judge_prompt.md` CoT judge template with judge temperature pinned at 0
- [ ] **EVAL-04**: Ablation comparison capability (3 conditions: old-no-refs / new-no-refs / new-with-refs)
- [ ] **EVAL-05**: N ≥ 20 prompts per expert (statistical significance threshold per PITFALLS)
- [ ] **EVAL-06**: Panel of ≥ 2 judges (cross-model diversity — recommended open-weight panel)
- [ ] **EVAL-07**: `_eval/reports/summary.md` aggregated comparison table for all evaluated experts
- [ ] **EVAL-08**: Harness uses only existing Hermes deps (`openai`, `pyyaml`, `jinja2`) — no new packages
- [ ] **EVAL-09**: `_eval/` is NOT registered in Hermes tool registry (offline developer tooling)

### DOC — Documentation & Bilingual Consistency

- [ ] **DOC-01**: `skills/movie-experts/README.md` exists with collaboration graph (18 experts) + RAG usage guide + eval results summary
- [ ] **DOC-02**: Bilingual consistency pass completed across all v1 skills (EN YAML canonical; CN prose references same metric IDs; CI lint verifies)
- [ ] **DOC-03**: Glossary cross-references verified (no orphan EN↔CN term pairs)
- [ ] **DOC-04**: `_shared/glossary.md` referenced from every SKILL.md needing bilingual context

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### REFACTOR-rest — Remaining 10 Existing Experts RAG

- **REFACTOR-rest-01**: `spatial_audio/SKILL.md` deep-refactored with refs (Dolby Atmos workflow, immersive sound design)
- **REFACTOR-rest-02**: `continuity/SKILL.md` deep-refactored with refs (cross-shot auditing heuristics, face/color/style matching)
- **REFACTOR-rest-03**: `foley/SKILL.md` deep-refactored with refs (Stable Audio Open workflow, 7D parametric design)
- **REFACTOR-rest-04**: `mixer/SKILL.md` deep-refactored with refs (Mixing Secrets for the Small Studio, LUFS standards)
- **REFACTOR-rest-05**: `voicer/SKILL.md` deep-refactored with refs (CosyVoice 3 deployment guide, MiniMax CN TTS, character voice consistency)
- **REFACTOR-rest-06**: `composer/SKILL.md` deep-refactored with refs (MusicGen workflow, Audio-Vision / Chion, On the Track)
- **REFACTOR-rest-07**: `performer/SKILL.md` deep-refactored with refs (An Actor Prepares / Stanislavski, ExBxSxP matrix refinement) — strip fabricated "168K tokens" claim
- **REFACTOR-rest-08**: `scene_builder/SKILL.md` deep-refactored with refs (Blender previz workflow, FxSxA scene matrix, camera-blocking patterns)
- **REFACTOR-rest-09**: `drawer/SKILL.md` deep-refactored with refs (FLUX 2 parameter surface, LoRA workflows, character consistency) — strip FLUX 1.x params
- **REFACTOR-rest-10**: `animator/SKILL.md` deep-refactored with refs (current video gen model behavior matrix, temporal consistency) — strip phantom `wan22_video`

### PROD — EXPERT-PROD (制作管理)

- **PROD-01**: `skills/movie-experts/production/SKILL.md` exists with AI-relevant subset only
- **PROD-02**: Casting / 选角 ref (character LoRA / reference image spec)
- **PROD-03**: 服化道 ref (per-scene wardrobe spec feeding `continuity`)
- **PROD-04**: Lighting intent layer ref
- **PROD-05**: GPU/render budget allocation ref (character-LoRA cost estimation, render-farm heuristics)
- **PROD-06**: Asset reuse plan ref (cross-shot/episode asset batching)
- **PROD-07**: Live-action subset (crews, permits, insurance) explicitly excluded

### VEC-RAG — Vector RAG Upgrade

- **VEC-RAG-01**: sqlite-vec integrated as v2 vector DB upgrade (replaces holographic HRR with learned embeddings)
- **VEC-RAG-02**: LanceDB fallback if multimodal (image+text) retrieval needed
- **VEC-RAG-03**: Automated corpus ingestion pipeline (replaces manual curation)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Hermes core Python/JS code changes | User explicitly chose "纯 skill + refs" delivery to control PR risk |
| New Python packages / external services | Scope control; existing Hermes capability sufficient |
| Standalone vector DB (Chroma/Qdrant/Pinecone) | Reuse existing memory plugin; new infra out of v1 scope |
| Automated corpus ingestion pipeline | v1 corpus is manually curated for quality; pipeline deferred to v2 (VEC-RAG-03) |
| New LLM provider or adapter | Unrelated to movie-experts enhancement |
| Dedicated web/desktop UI for the system | Used via existing Hermes UI; no UI duplication |
| Full Chinese rewrite of existing 14 SKILL.md | Bilingual strategy = EN structure + CN additions; preserve Hermes English community compat |
| Fine-tuning models on existing short drama samples | This is a RAG project, not a fine-tune project |
| Other creative skill categories (comfyui, manim, etc.) | Out of `skills/movie-experts/` scope |
| EXPERT-PROD live-action subset | Casting crews, permits, insurance — not relevant for AI-generated short drama |
| Hook metric prediction (完播率/转发率/付费率) | Requires platform data access (out of scope); EXPERT-HOOK does structural design only |
| Judge panel including commercial models (Claude/GPT-4o) | Cost vs bias-diversity trade-off; open-weight panel (Qwen-Max/GLM/Yi) for v1 |
| 短剧 sample sources requiring paid licenses | Copyright risk; v1 uses public-domain + fair-use excerpts ≤30s + creator-permission samples only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 0 | Pending |
| FOUND-02 | Phase 0 | Pending |
| FOUND-03 | Phase 0 | Pending |
| FOUND-04 | Phase 0 | Pending |
| FOUND-05 | Phase 0 | Pending |
| FOUND-06 | Phase 0 | Pending |
| FOUND-07 | Phase 0 | Pending |
| FOUND-08 | Phase 0 | Pending |
| FOUND-09 | Phase 0 | Pending |
| COMPLI-01 | Phase 1 | Pending |
| COMPLI-02 | Phase 1 | Pending |
| COMPLI-03 | Phase 1 | Pending |
| COMPLI-04 | Phase 1 | Pending |
| COMPLI-05 | Phase 1 | Pending |
| COMPLI-06 | Phase 1 | Pending |
| COMPLI-07 | Phase 1 | Pending |
| COMPLI-08 | Phase 1 | Pending |
| COMPLI-09 | Phase 1 | Pending |
| HOOK-01 | Phase 2 | Pending |
| HOOK-02 | Phase 2 | Pending |
| HOOK-03 | Phase 2 | Pending |
| HOOK-04 | Phase 2 | Pending |
| HOOK-05 | Phase 2 | Pending |
| HOOK-06 | Phase 2 | Pending |
| HOOK-07 | Phase 2 | Pending |
| HOOK-08 | Phase 2 | Pending |
| HOOK-09 | Phase 2 | Pending |
| REFACTOR-01 | Phase 3 | Pending |
| REFACTOR-02 | Phase 3 | Pending |
| REFACTOR-03 | Phase 3 | Pending |
| REFACTOR-04 | Phase 3 | Pending |
| REFACTOR-05 | Phase 3 | Pending |
| REFACTOR-06 | Phase 3 | Pending |
| REFACTOR-07 | Phase 3 | Pending |
| REFACTOR-08 | Phase 3 | Pending |
| CINE-01 | Phase 4 | Pending |
| CINE-02 | Phase 4 | Pending |
| CINE-03 | Phase 4 | Pending |
| CINE-04 | Phase 4 | Pending |
| CINE-05 | Phase 4 | Pending |
| CINE-06 | Phase 4 | Pending |
| CINE-07 | Phase 4 | Pending |
| CINE-08 | Phase 4 | Pending |
| CINE-09 | Phase 4 | Pending |
| EVAL-01 | Phase 0 (skeleton) / Phase 6 (full run) | Pending |
| EVAL-02 | Phase 0 | Pending |
| EVAL-03 | Phase 0 | Pending |
| EVAL-04 | Phase 3 (ablation per expert) / Phase 6 (full) | Pending |
| EVAL-05 | Phase 6 | Pending |
| EVAL-06 | Phase 6 | Pending |
| EVAL-07 | Phase 6 | Pending |
| EVAL-08 | Phase 0 | Pending |
| EVAL-09 | Phase 0 | Pending |
| DOC-01 | Phase 6 | Pending |
| DOC-02 | Phase 6 | Pending |
| DOC-03 | Phase 6 | Pending |
| DOC-04 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 46 total
- Mapped to phases: 46 (Phase 0: 14, Phase 1: 9, Phase 2: 9, Phase 3: 8, Phase 4: 9, Phase 6: 8 — note EVAL spans 0+6)
- Unmapped: 0

---
*Requirements defined: 2026-06-15*
*Last updated: 2026-06-15 after initialization (derived from research SUMMARY.md)*
