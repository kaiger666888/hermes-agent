# Stack Research — v2.0 PRFP (Pipeline Redesign from First Principles)

**Domain:** Design-doc derivation — source-materials + methodologies "stack" for first-principles reconstruction of the kais-movie-agent pipeline node set
**Researched:** 2026-06-16
**Confidence:** HIGH for corpus inventory + kais architecture history (direct filesystem + file reads); MEDIUM-HIGH for methodology citations (web-verified primary sources); MEDIUM for LLM-story-research (web search verified June 2026, mix of HIGH and LOW per reference)

> **Scope note:** Unlike v1 STACK.md (which recommended Hermes memory-plugin API surface, FLUX 2 image backends, MT-Bench eval harness, sqlite-vec), **v2.0 PRFP recommends ZERO code libraries**. The "stack" here is the source-material corpus + methodology canon that node-design phases will cite when justifying "why this node exists and not another."

---

## Executive Frame

The downstream consumer (roadmapper + node-design phases) needs to know:
1. **Where each piece of source material physically lives** — so phase planners can route design work to the right files without re-discovery.
2. **Which subsets of the corpus answer which first-principles questions** — so a node-design phase for "what does the user ultimately consume?" pulls different books than "where can AIGC genuinely add marginal value?"
3. **What methodologies are validated and citable** — so the "why this node" rationale is defensible, not hand-wavy.
4. **What v1 research can be reused vs discarded** — so the team doesn't re-do completed work or carry forward skill-build concerns that no longer apply.

Each source below is annotated with: physical location → which first-principles question it answers → confidence → recommended use in node design.

---

## 1. Primary Source Corpus — 102-Book Film Production Library

### 1.1 Physical location + verified inventory

**Root path:** `/home/kai/Downloads/100+本影视剪辑书/`

**Structure (verified 2026-06-16 by direct `ls`):**

| Path | Contents | Status |
|---|---|---|
| `converted/` | 102 MinerU-converted markdown books + 3 non-book entries (`logs`, `test-1`, `test-2`) → ~105 entries total; ~9.7M Chinese characters | Authoritative content source |
| `skills-影视创作/` | Pre-built 95+ skill markdown files organized by 6-stage taxonomy + orchestrator + case-studies | **Pre-mined synthesis** — these are distillations of the 102 books, not raw |
| `indexes/books-index.{md,json}` | Auto-generated index with per-book word count + first 15 TOC entries | Navigation aid |
| `indexes/全量审视-GAP分析报告.md` + `全量完成报告-v4.md` + `SKILL-校验报告-基于真实内容.md` + `skill-coverage-audit.json` | Pre-existing audit reports from the corpus build | **Cite for corpus-quality confidence** — don't re-audit |
| `scripts/{audit-coverage.py,batch-convert.sh,build-index.py}` | MinerU batch conversion + indexing toolchain | Reference only (no rebuild needed) |
| `影视创作经验总结-按阶段.md` | Top-level human-authored synthesis by stage | **HIGH-value citable source** — already pre-synthesized for stage-aligned thinking |
| `摄影后期社/`, `有氧周末/`, `更多访问www.zhoumovip.cn/` | Original raw download directories (pre-conversion) | Source provenance; do not cite directly |

**Total file count:** 105 entries in `converted/` (102 books + 3 metadata dirs). Index claims 102 books, ~9,727,839 Chinese characters.

### 1.2 Category breakdown (from `indexes/books-index.md`)

The corpus was MinerU-classified into 16 categories. Clustered by relevance to first-principles node design:

| Cluster | Books | First-principles node-design relevance |
|---|---|---|
| **剧本创作 (Screenwriting)** | 17 | **CRITICAL** — answers "what is a story kernel?" / "what does audience consume at the narrative layer?" |
| **电影理论 (Film theory)** | 12 | **CRITICAL** — answers "what is the irreducible nature of cinema?" (Bazin, Tarkovsky, formalism-vs-realism) |
| **导演表演 (Directing & Acting)** | 9 | HIGH — answers "what is the human-author intent layer that AIGC transforms?" |
| **电影教材 (Film textbooks)** | 7 | HIGH — answers "what is the canonical production pipeline a human would follow?" |
| **摄影照明 (Cinematography & Lighting)** | 6 | MEDIUM — execution-domain; relevant for "where does AI render vs human craft" |
| **导演研究 (Director studies)** | 6 | MEDIUM — auteur theory; relevant for style-genome node design |
| **案例分析 (Case studies)** | 5 | MEDIUM — concrete worked examples; useful for node I/O contract examples |
| **前期分镜 (Pre-viz & Storyboard)** | 4 | HIGH — pre-production node design |
| **制片发行 (Producing & Distribution)** | 4 | MEDIUM — distribution-layer node design; mostly live-action |
| **电影史 (Film history)** | 4 | LOW — background context; not load-bearing for node design |
| **剪辑后期 (Editing & Post)** | 3 | HIGH — post-production node design |
| **影评写作 (Criticism)** | 2 | LOW — analytical layer; not pipeline-relevant |
| **声音音效 (Sound)** | 2 | MEDIUM — audio-node design |
| **视觉美术 (Visual Design)** | 1 | MEDIUM |
| **类型/动画 (Genre/Animation)** | 1 | LOW |
| **纪录片 (Documentary)** | 1 | LOW (vertical) |
| **其他 (Other)** | 18 | Mixed; case-by-case. Includes 解读电影, 戏剧与电影的剧作理论与技巧 (劳逊 — HIGH value for drama theory), 并非冷漠的大自然 (塔可夫斯基 — HIGH for theory) |

**Tangential (deprioritize for node-design mining):** Film history (4), Criticism writing (2), Documentary (1), Genre/Animation (1). These inform culture/context but not pipeline structure.

**Concentrate node-design mining on:** 剧本创作 + 电影理论 + 导演表演 + 电影教材 + 前期分镜 + 剪辑后期 + the high-value "其他" books (劳逊, 塔可夫斯基-并非冷漠).

### 1.3 Pre-built skills-影视创作/ taxonomy (HIGH leverage — reuse, don't re-derive)

**Critical finding:** The corpus already ships a 95+ skill markdown tree at `/home/kai/Downloads/100+本影视剪辑书/skills-影视创作/` organized by the SAME 6-stage taxonomy. **This is a prior synthesis** of the 102 books — NOT raw material. Node-design phases should consult this as "what did a first-pass human-curated synthesis already conclude?" before deciding whether to re-derive from primary books.

| Subdirectory | Files (count) | Stage | Citable for node-design question |
|---|---|---|---|
| `00-orchestrator/` | 1 (`film-master-orchestrator.md`) | Meta | "What is the holistic creative-to-delivery orchestration layer?" — directly maps to pipeline-meta node |
| `01-剧本/` | 17 files | Screenwriting | "What is the narrative-intent node?"; hook-design, character-arc, dynamic-structure (O'Bannon), opening-design, scene-writing, subplot, world-building |
| `02-分镜/` | 11 files | Pre-viz & Directing | "What is the visualization node?"; cinematic-language-grammar, mise-en-scene-blocking, scene-deconstruction-method, shot-list-creation, storyboard-design, casting-direction, crew-hiring, equipment-planning, location-scouting, visual-reference-board |
| `03-拍摄/` | 20 files | Production & Cinematography | "What is the visual-execution node?"; acting-stanislavski-stella, action-choreography, actor-direction, animation-production, art-direction-process, camera-movement, cinematographer-masterclass, color-narrative-analysis, costume-makeup, drone-cinematography, lighting-design, lighting-equipment-operation, masterclass-lighting-cases, multicam-direction, on-set-sound-recording, production-design, second-unit-direction, shot-composition, vfx-physical-models, vfx-supervision |
| `04-后期/` | 14 files | Post-production | "What is the post-production node?"; adr-dialogue-replacement, color-grading-strategy, documentary-production-methods, editing-by-murch-rules, editing-rhythm-pacing, final-mix, foley-sfx-recording, murch-in-conversation, music-supervision, picture-lock-review, sound-layering-design, sound-sacred-bible, title-design, trailer-editing |
| `05-制片/` | 11 files | Producing | "What is the resource-allocation node?"; accounting-finance, budget-allocation, contract-negotiation, distribution-strategy, festival-strategy, filmmaking-full-handbook, financing-pitch, hollywood-studio-system, low-budget-filmmaking-uk, production-scheduling, project-development |
| `06-理论批评/` | 21 files | Theory & Criticism | "What is cinema at its essence?" (the first-principles root question); auteur-analysis, auteur-biographical-study, cinema-fundamentals, documentary-ethics, ethnographic-filmmaking, film-analysis, film-criticism-methodology, film-history-methods, film-history-timeline, film-philosophy-bazin, film-philosophy-tarkovsky, film-review-writing, film-theory-traditions, formalism-vs-realism, genre-conventions, modernism-benjamin-adorno, narrative-revolution-guo-xiaolu, national-cinema, psychoanalytic-film-theory, single-film-case-study, yamada-yoji-filmmaking |
| `case-studies/` | 3 files | Worked examples | "Concrete end-to-end pipeline examples"; case-01-短片创作全流程, case-02-长片剧本诊断, case-03-后期救片 |

**Total: ~95 skill files + 3 case studies pre-synthesized.** This is the single highest-leverage resource for node design — it represents a prior art synthesis that first-principles thinking should **deliberately diverge from or build upon**, exactly as the milestone context demands ("ignore existing 8 phases and 26 skills as starting bias; reconstruct from first principles").

### 1.4 Recommended mining strategy per first-principles question

| First-principles question (from PROJECT.md milestone context) | Primary corpus subset | Secondary corpus subset |
|---|---|---|
| "What does the audience ultimately consume?" | `01-剧本/` (narrative intent) + `06-理论批评/{cinema-fundamentals,film-philosophy-bazin,film-philosophy-tarkovsky}` (what cinema IS) + book 劳逊《戏剧与电影的剧作理论与技巧》 | `case-studies/case-01-短片创作全流程.md` |
| "Why do short dramas live or die in the first 3 seconds?" | NOT in corpus — corpus is feature-film oriented. Pair with v1 `hook_retention/references/three-second-hooks.md` (already integrated from external 短剧 sources) | Web research on 短剧 pacing (out of corpus scope) |
| "What determines microfilm quality?" | `04-后期/{editing-by-murch-rules,editing-rhythm-pacing,color-grading-strategy,final-mix,sound-layering-design}` + `03-拍摄/{cinematographer-masterclass,lighting-design,color-narrative-analysis}` | `02-分镜/{cinematic-language-grammar,mise-en-scene-blocking}` |
| "Where can AIGC genuinely add marginal value?" | NOT directly in corpus. INFER from: `04-后期/` (which post tasks are most repetitive?) + `03-拍摄/animation-production.md` + `05-制片/budget-allocation.md` (which human tasks are most expensive?) | Pair with kais-movie-agent architecture docs (Section 3) for actual AIGC integration points |
| "What can AI NOT replace?" | `06-理论批评/{film-philosophy-bazin,film-philosophy-tarkovsky,formalism-vs-realism}` (irreducible creative intent) + `01-剧本/{adaptation-writing,character-arc-design,dialogue-crafting}` (creative voice) + `03-拍摄/{acting-stanislavski-stella,actor-direction}` (performance truth) | Book 麦基《故事》, 芦苇剧本笔记 |

---

## 2. Already-Integrated project-corpus/ (9 Refs in hermes-agent)

### 2.1 Physical location + verified file list

**Path:** `/data/workspace/hermes-agent/skills/movie-experts/_shared/project-corpus/`

**Verified 2026-06-16 by direct `ls`:** 14 files (README + INTEGRATION-REPORT + 12 ref-content files). README claims "9 new ref files" — actual count is 12 content files. Discrepancy: README may count cluster-merged files differently. Treat the filesystem as authoritative.

| Ref file | Synthesizes which books | Node-design question it answers | Already concentrated enough? |
|---|---|---|---|
| `README.md` | 102-book index | Corpus navigation | YES — index |
| `INTEGRATION-REPORT.md` | Integration audit | Coverage / GAP tracking | YES |
| `theory-formalism-vs-realism.md` | Andrew / Agel / Balázs | "What is the essence of cinematic form?" — first-principles root | YES |
| `film-philosophy-bazin-tarkovsky.md` | Bazin / Tarkovsky / 七部半 | "What is cinema's irreducible ontology?" — first-principles root | YES |
| `psychoanalytic-film-theory.md` | 凝视的快感 / 好莱坞中的拉康 | Audience-reception layer | YES |
| `auteur-director-biographies.md` | 7 director biographies | Auteur-intent node design | YES |
| `film-criticism-methodology.md` | 戴锦华 / 如何写影评 / 外国批评文选 | Analytical methodology (not pipeline) | Partial — analytical only |
| `film-history-methods.md` | Allen / Oxford / Sadoul | Background; LOW pipeline relevance | Partial |
| `narrative-revolution-and-modernism.md` | 郭小橹 / 本雅明 / 阿多诺 | Modernism narrative — theoretical underpinning | YES |
| `cinematography-masterclass-and-grammar.md` | 阿里洪 / 100 手法 / 拉片子 / 拆解好电影 / 21 位大师 | Visual-language node design | YES |
| `lighting-equipment-and-design.md` | 照明器材 / 影视光线艺术 / 镜头在说话 / 狼图腾 | Lighting-intent node design | YES |
| `editing-sound-post.md` | 剪辑之道 / 魅力剪辑 / 音效圣经 / 视听 / 王竞六讲 | Post-production node design | YES |
| `production-chinese-and-low-budget.md` | 拍电影 / 制片手册 / 创意制片 / 好莱坞模式 / 英国基础 / 预算手册 | Resource-allocation node design | YES |
| `animation-disney-system.md` | 迪士尼的艺术 / 影视动画剧本赏析 | Animation-vertical node design | YES |
| `screenwriting-chinese-and-supplementary.md` | 芦苇 / 维基·金 / 刘天赐 / 编剧策略 / 奥班农 / 温斯顿 | Screenwriting node design (CN-specific) | YES |

### 2.2 Coverage assessment

**Strongly concentrated (READY for node-design citation without re-mining):**
- Theory root: `theory-formalism-vs-realism.md` + `film-philosophy-bazin-tarkovsky.md` + `narrative-revolution-and-modernism.md` → answers "what is cinema at its essence?"
- Craft execution: `cinematography-masterclass-and-grammar.md` + `lighting-equipment-and-design.md` + `editing-sound-post.md` + `animation-disney-system.md` → answers "what are the irreducible human craft operations?"
- Producing: `production-chinese-and-low-budget.md` → answers "what is the resource-allocation layer?"

**Needs re-mining from source books for v2.0:**
- **Screenwriting depth** — `screenwriting-chinese-and-supplementary.md` is concentrated but **underweights 短剧-specific screenwriting**. The 102 corpus is feature-film-oriented. For first-principles derivation of "what does the 短剧 audience consume?", pair this ref with v1 `screenplay/references/cn-shortdrama.md` (already integrated from external sources) + consider directly re-reading books -017 菲尔德, -026 麦基, -036 拉片子 from `converted/`.
- **Audience-reception / 短剧 retention** — `psychoanalytic-film-theory.md` is HIGH-level theory; **does not cover 短剧-specific retention craft**. Pair with v1 `hook_retention/` 4 refs.
- **AIGC marginal-value analysis** — NO project-corpus ref covers this. Must infer from craft-execution refs (which human tasks are most procedural?) + kais-movie-agent V8 architecture (where actual AIGC integration happens).

**Conclusion:** 9 of 12 content refs are concentrated enough to support node-design citation directly. 3 need supplementation from primary books or external v1 refs.

---

## 3. kais-movie-agent Historical Architecture (V2 → V6 → V8 Evolution)

### 3.1 Why this matters for first-principles derivation

Per PROJECT.md milestone context: "节点设计从 0 推:不预设现有 8 phases 和 26 skills,但产出后会跟它们做**对照分析**(用于识别覆盖缺口和 AIGC 转化机会,非实施)." The kais-movie-agent history is the **primary "what was tried before" dataset** that first-principles thinking must deliberately question.

### 3.2 Architecture evolution summary (from direct file reads)

| Version | Date | Phases/Steps | Key architectural move | File |
|---|---|---|---|---|
| **V1 (current ARCHITECTURE_AND_WORKFLOW.md)** | 2026-05-18 | 10 phases (requirement → art-direction → character → scenario → voice → scene → storyboard → camera → post-production → quality-gate) | Pipeline-as-code: `lib/pipeline.js` (576 lines) + `lib/phases/index.js` (1157 lines) + Git stage manager + HMAC callback server + Telegram notifications. Zero npm deps. GPU via gold-team (44 task types). | `docs/ARCHITECTURE_AND_WORKFLOW.md` |
| **V2 (REFACTOR-PLAN, 2026-05-18)** | 2026-05-18 | 11 phases | 7 changes: AI 熔断 on scenario (<60 fail), voice 前置 (audio-driven storyboard), character/art-bible/shot-list/voice-timeline/scene-assets structured asset bus, camera split (preview 33f/10step → final 81f/20step), scene on-demand dedup, structured shot-list enum | `docs/V2-REFACTOR-PLAN.md`, `docs/WORKFLOW.md` |
| **V4.1 (referenced in v6-architecture-notion.md)** | pre-2026-05-25 | 10 phases with renamed semantic identifiers (requirement-bible → soul-visual → soul-voice → geometry-bed → spatio-temporal-script → seed-skeleton → motion-preview → ai-preview → final-production → composition) | Semantic / philosophical naming convention shift ("soul", "geometry-bed", "spatio-temporal") | `docs/v6-architecture-notion.md` (cited as "current V4.1") |
| **V6 (Notion, retrieved 2026-05-25)** | 2026-05-25 | **20 steps in 2 halves** (Steps 1-11 创意立项, Steps 12-20 生产执行) | Major expansion: kais-soul-radar (pain point discovery) as Step 1, kais-script-agent (outline + script), Seedance 2.0 audio-driven video, CosyVoice2 voice locking, kais-consistency-agent cross-shot consistency, GPU Runtime Manager V5.1 stage-based scheduling, 3090/3060Ti dual-GPU split, feedback loops (max 3 iterations), asset library | `docs/v6-architecture-notion.md` |
| **V8 (2026-05-28)** | 2026-05-28 | 20 steps preserved | **Architectural collapse**: movie-agent Docker container **废弃**; orchestration fully收归 OpenClaw Agent (唯一 LLM). gold-team direct connect (`:8002`), Toonflow replaces review-platform (`:3000`). State = OpenClaw session + filesystem (no Pipeline API). | `docs/V8-ARCHITECTURE.md` |

### 3.3 Key historical thinking to deliberately question

The v2.0 first-principles exercise should explicitly question these inherited assumptions from V1-V8:

1. **"Pipeline = linear sequence of phases"** (V1, V2, V4.1, V6 all assume linear DAG). Question: is linearity actually required, or is it inherited from human film production workflow? What if some phases should be parallel or convergent?
2. **"Each phase produces JSON artifacts passed forward"** (asset bus pattern, V2+). Question: is JSON asset bus the right abstraction, or does it fragment the creative intent across 11+ files (art-bible, character-assets, voice-timeline, shot-list, scene-assets)?
3. **"Review checkpoints after each visual phase"** (V1+). Question: at what node does human review genuinely add marginal value vs slow the pipeline? V6 already split this into "creative立项" (human) vs "production execution" (AI).
4. **"Categorization by production stage"** (剧本/分镜/拍摄/后期/制片/理论 — same as skills-影视创作/ taxonomy). Question: is production-stage the right axis, or should it be creative-intent vs execution vs distribution?
5. **"20 steps is the right granularity"** (V6, V8). Question: from first principles, what is the minimum viable node count?
6. **"The LLM orchestrates everything"** (V8 collapse). Question: is full LLM orchestration actually optimal, or does it conflate creative-judgment nodes with mechanical-execution nodes?

### 3.4 Auxiliary docs worth consulting

| File | Contents | Use for v2.0 |
|---|---|---|
| `/data/workspace/kais-movie-agent/INTEGRATION.md` | Integration dev guidance | TBD — read if node-design needs cross-system I/O contract context |
| `/data/workspace/kais-movie-agent/README.md` | Current state with 7 sub-skills + sketch-pipeline (线稿 → 渲染 two-stage) | Shows current state of sub-skill fragmentation — supports "15+ sub-skills is too many" first-principles critique |
| `/data/workspace/kais-movie-agent/docs/4d-anchoring-design.md` + `4d-anchoring-integration-research.md` | 4D anchor system (depth/identity/lighting/temporal) — already partially integrated into hermes v1 character_designer / storyboard_designer | Reference for "what consistency model was already tried" |
| `/data/workspace/kais-movie-agent/DEPRECATED.md` | Deprecated paths | Avoid re-deriving anything already abandoned |
| `/data/workspace/kais-movie-agent/skills/` | 15 kais-* sub-skill directories (kais-anatomy-guard, kais-art-direction, kais-audience, kais-blender-pose, kais-camera, kais-character-design, kais-cinematography-planner, kais-movie-agent, kais-scenario-writer, kais-scene-design, kais-shooting-script, kais-storyboard-designer, kais-story-score, kais-topic-selector, kais-voice) | **Inherited fragmentation** — the v2.0 node set should consolidate, not preserve this 15-way split |

---

## 4. First-Principles Methodology Canon

### 4.1 Core methodology: Musk-style first-principles thinking

**What it is (from primary sources):** Boil a problem down to its most fundamental truths ("what do we know for sure is true?"), then reason up from there — explicitly refusing to reason by analogy ("this is how it's always been done").

**Concrete Musk references (cite ≥3):**

1. **Kevin Rose Foundation interview (2012)** — the canonical articulation. Musk: *"I tend to approach things from a physics framework. Physics teaches you to reason from first principles rather than by analogy."* Battery-cost example: rather than accept "$600/kWh market price", Musk computed raw material costs (cobalt, nickel, aluminum, carbon) → revealed batteries could be produced far cheaper.
   - Primary: [Elon Musk - Childhood and Work Philosophy (Foundation Series #3)](https://www.kevinrose.com/p/elon-musk-interview-kevin-reboots-the-old-foundation-series)
   - Quote source: [James Clear — "First Principles: Elon Musk on the Power of Thinking for Yourself"](https://jamesclear.com/first-principles)
   - Video: [YouTube — Elon Musk and Kevin Rose clip](https://www.youtube.com/watch?v=L-s_3b5fRd8)

2. **Walter Isaacson biography *Elon Musk* (2023)** — portrays first-principles thinking as Musk's defining "superpower." SpaceX example: Musk broke rocket cost down to raw materials (aluminum, titanium, copper, carbon fiber) → found materials were only ~2% of rocket price → revealed manufacturing inefficiency, not physics, drove cost. Tesla example: "humans drive with only visual input, so cameras should suffice" → first-principles rejection of LiDAR dependency.
   - Wikipedia: [Elon Musk (Isaacson book)](https://en.wikipedia.org/wiki/Elon_Musk_(Isaacson_book))
   - Reader synthesis: [HEY World — "Get back to first principles"](https://world.hey.com/charlietarr/get-back-to-first-principles-bd36d441)
   - Book notes: [Graham Mann — Book Notes: Elon Musk (Walter Isaacson)](https://grahammann.net/book-notes/elon-musk-walter-isaacson)
   - Lex Fridman interview transcript: [Walter Isaacson: Elon Musk, Steve Jobs, Einstein...](https://lexfridman.com/walter-isaacson-transcript/)
   - WSJ: [Elon Musk's Lessons From Hell: Five Commandments for Business](https://www.wsj.com/business/media/elon-musk-biography-walter-isaacson-951a47bd)

3. **Musk's distilled philosophy:** *"Physics is the law, everything else is a recommendation."* Cited across [FourMinuteBooks summary](https://fourminutebooks.com/elon-musk-summary-walter-isaacson/) and WSJ commandments.

4. **YouTube explainer (Musk himself):** [The First Principles Method Explained by Elon Musk](https://www.youtube.com/watch?v=NV3sBlRgzTI) — leap innovation rather than incremental improvement.

**Applied to kais-movie-agent v2.0 (template for node-design rationale):**

> "Rather than inheriting the 10-phase V1 / 20-step V6 / 15-sub-skill current pipeline by analogy ('this is how film production works'), we ask: what do we know for sure about (a) what the audience ultimately consumes, (b) what determines 短剧生死, (c) where AI's marginal value actually lies? From those fundamentals we re-derive the minimum node set."

### 4.2 Adjacent methodologies (cite ≥2)

1. **Aristotle — first principles (φυσικαὶ ἀρχαί)** — the original philosophical articulation. From *Physics* Book I and *Metaphysics* Book Δ (Delta): "first principles and causes are most knowable; for by reason of these all other things come to be known." Foundational proposition that cannot be deduced from any other. **Relevant to v2.0:** Aristotle distinguishes "more knowable to us" (familiar, analogous) from "more knowable by nature" (foundational truths) — exactly the distinction Musk's "first principles vs analogy" makes.
   - [First principle — Wikipedia](https://en.wikipedia.org/wiki/First_principle)
   - [Aristotle, Physics, I, 1 — Logos Virtual Library](http://www.logoslibrary.org/aristotle/physics/11.html) (Hardie & Gaye translation)
   - [Aristotle's Metaphysics — Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/aristotle-metaphysics/)
   - [Metaphysics Book Δ — MIT Internet Classics](https://classics.mit.edu/Aristotle/metaphysics.11.xi.html)
   - [Aristotle's Method of Understanding the First Principles of Natural Science — PhilArchive](https://philarchive.org/archive/MOUAMO-3)

2. **TRIZ (Theory of Inventive Problem Solving, Altshuller)** — instead of compromising on trade-offs, TRIZ eliminates contradictions by inventive principles derived from patent analysis. Uses 39×39 Contradiction Matrix → 40 Inventive Principles. **Relevant to v2.0:** when node-design surfaces a contradiction (e.g., "more creative control vs more automation"), TRIZ methodology suggests inventive principles (segmentation, asymmetry, nesting, etc.) rather than trade-off acceptance. Empirical finding: 20 of 40 principles address >75% of contradictions (IEEE paper).
   - [TRIZ — Wikipedia](https://en.wikipedia.org/wiki/TRIZ)
   - [TRIZ40.com — 40 Principles with examples](https://www.triz40.com/aff_Principles_TRIZ.php)
   - [Contradiction Matrix and the 40 Principles — The TRIZ Journal](https://the-trizjournal.com/contradiction-matrix-40-principles-innovative-problem-solving/)
   - [TRIZ: 40 Principles and Their Ranking by Contradiction Matrix — IEEE](https://ieeexplore.ieee.org/document/8226329/)

3. **(Tertiary) Jobs-style reduction** — Steve Jobs' product-design philosophy of subtractive refinement ("I'm proud of what we DON'T do"). Useful as a complementary lens to first-principles: derive what's necessary, then prune what's merely inherited. No single canonical reference; crystallized in Isaacson's *Steve Jobs* biography. **Relevant to v2.0:** after deriving the minimum node set from first principles, apply Jobs-style reduction to challenge whether each remaining node is truly necessary or just comfortably familiar.

4. **(Tertiary) Physics-inspired decomposition** — the general practice of decomposing a system to constituent interactions. Not a named methodology but the metaphysical substrate under both Musk and Aristotle. For v2.0: "what are the irreducible creative-material transformations a 短剧 undergoes from idea to consumed video?"

---

## 5. LLM Creative-Story-Generation Research (the "LLM 创意凝练" topic)

The user emphasized this dimension: "大模型如何产出**有创意且逻辑自洽**的故事框架". Below are 8 verified, citable references with URLs.

### 5.1 Plot consistency / plot-hole detection (the "逻辑自洽" half)

| # | Reference | URL | Confidence | Why it matters for v2.0 node design |
|---|---|---|---|---|
| 1 | **Plot Hole Detection as LLM reasoning benchmark** (2025) | https://arxiv.org/html/2504.11900v1 | MEDIUM-HIGH (arXiv preprint, OpenReview peer-review) | Plot holes as a proxy for evaluating LLM narrative reasoning. Provides framework for the "self-consistency check" node — any derived pipeline should include automated plot-hole detection before锁定 script. |
| 2 | **ConStory-Bench — Lost in Stories: Consistency Bugs in Long Story Generation by LLMs** | https://arxiv.org/html/2603.05890v1 + https://github.com/Picrew/ConStory-Bench | MEDIUM-HIGH (Microsoft Research, HuggingFace papers) | Benchmark + ConStory-Checker automated LLM-as-judge pipeline for contradiction detection in generated stories. Directly applicable as the methodology for "自洽性的检验机制" sub-document. |
| 3 | **CONFACTCHECK — Consistency Is the Key: Detecting Hallucinations in LLM Generated Outputs** | https://aclanthology.org/2025.findings-ijcnlp.129/ | MEDIUM (ACL Findings) | Hallucination detection via consistency checking without external KB. Applicable to "故事框架" generation where external fact-checking is impossible (fictional content). |

### 5.2 Story-kernel generation + narrative arc templates (the "创意凝练" half)

| # | Reference | URL | Confidence | Why it matters for v2.0 node design |
|---|---|---|---|---|
| 4 | **A Survey on LLMs for Story Generation** (EMNLP 2025 Findings) | https://aclanthology.org/2025.findings-emnlp.750.pdf | HIGH (EMNLP peer-reviewed) | Comprehensive survey. Proposes taxonomy: (a) independent story generation by LLM, (b) author-assistance paradigm. **Critical for v2.0**: justifies the choice between "AI fully generates" vs "AI assists human creative intent" — directly informs whether the creative-source node should be AI-autonomous or human-in-loop. |
| 5 | **Learning to Reason for Long-Form Story Generation** (OpenReview) | https://openreview.net/forum?id=dr3eg5ehR2 | MEDIUM (OpenReview, Mirella Lapata lineage) | Long-form plot + character arc consistency tracking via reasoning. Applicable to multi-episode 短剧 arc design (小程序剧 10-100 episodes). |
| 6 | **Awesome-Story-Generation** (curated GitHub repo, LLM-era focused) | https://github.com/yingpengma/Awesome-Story-Generation | MEDIUM-HIGH (actively maintained literature index) | One-stop literature review starting point. Use for phase-specific deep-dives into subtopics (planning, editing, evaluation). |

### 5.3 Creator-centric / scaffolding methods

| # | Reference | URL | Confidence | Why it matters for v2.0 node design |
|---|---|---|---|---|
| 7 | **Exploring Creator-Centric Methods for LLM-Assisted Interactive Narrative** (ACM) | https://dl.acm.org/doi/10.1145/3772318.3791362 | MEDIUM (ACM peer-reviewed) | Creator-side gaps: narrative logic planning, character consistency, interactive storytelling. Supports the "AI cannot replace creative intent" first-principles answer — AI assists, doesn't replace. |
| 8 | **Scaffolding the Story: An LLM-Based Assessment** (IASDR) | https://dl.designresearchsociety.org/cgi/viewcontent.cgi?article=1644&context=iasdr | MEDIUM (design research venue) | LLM-as-evaluator for writing assessment. Applicable to "fail modes" sub-topic — when does LLM-generated narrative fail quality bars? |

### 5.4 Recommended use in v2.0 LLM-创意凝练 sub-document

PROJECT.md milestone target #4 specifies a "单独子文档" recording: (a) 创意的本质, (b) 自洽性的检验机制, (c) LLM 凝练的 prompt 策略, (d) fail modes. Recommended reference mapping:

| Sub-topic | Primary reference(s) |
|---|---|
| 创意的本质 (nature of creativity) | Survey (#4) Section on independent vs author-assistance paradigm + Aristotle first-principles (§4.2) for "what is the irreducible creative act?" |
| 自洽性的检验机制 (consistency checking mechanism) | Plot-Hole Detection (#1) + ConStory-Bench (#2) + CONFACTCHECK (#3) |
| LLM 凝练的 prompt 策略 (prompt strategies) | Learning to Reason (#5) + Awesome-Story-Generation (#6) index → phase-specific deep dive |
| Fail modes | Scaffolding (#8) + ConStory-Bench consistency-bugs findings (#2) |

---

## 6. v1 Research Carryover Audit

The v1 research files (`.planning/research/{STACK,FEATURES,ARCHITECTURE,PITFALLS,SUMMARY}.md`) were scoped for **skill-building** (refs + SKILL.md + eval harness). v2.0 PRFP is **pipeline-design**. Below: per-file relevance audit.

### 6.1 Carryover table

| v1 File | Relevant for v2.0? | What to carry forward | What's obsolete |
|---|---|---|---|
| **v1 STACK.md** | **PARTIAL — mostly obsolete, two sections relevant** | §2 (Static Reference Corpus best practices — directory layout, citation/provenance format) applies if v2.0 produces any new markdown artifacts. §3 (AI Generation Tool Stack 2026-06) is **still current** — kais-movie-agent V8 lives in the same gold-team/FAL/Seedance ecosystem; v2.0 node-design's "where can AIGC add marginal value" must reference these real capabilities. | §1 (Hermes Memory Plugin API surface) — irrelevant for pipeline-design. §4 (LLM-as-judge eval harness) — irrelevant; v2.0 produces no eval. §5 (Vector DB choice) — irrelevant. |
| **v1 FEATURES.md** | **PARTIAL — feature inventory obsolete, capability-gap framing relevant** | §5 (Existing 14 Expert Enhancement Opportunities table) — informs "what is the inherited fragmentation?" critique. §6 (Bilingual Authoring Patterns) — relevant if v2.0 docs are bilingual. Capability-area framing (Cinematography / Hook&Retention / Production / Compliance) maps to v2.0's "what nodes does the inherited pipeline miss?" analysis. | Table-stakes / differentiators / anti-features per EXPERT-* — those were skill-build specs; v2.0 is pipeline-design. The v1 priority calls (build EXPERT-COMPLI first, etc.) are now executed history. |
| **v1 ARCHITECTURE.md** | **PARTIAL — DAG structure relevant, Hermes-integration patterns obsolete** | The 18-expert (now 26) collaboration DAG (creative_source root → style_genome → screenplay ↔ script_auditor → cinematographer → storyboard_designer → drawer/animator → lip_sync/voicer → mixer) is **directly the "current state"** v2.0 must deliberately question. Use as the "before" picture. | Hermes skill-system architecture (frontmatter, metadata.hermes, related_skills graph mechanism, three-tier system prompt caching) — implementation detail, irrelevant for pipeline-design. |
| **v1 PITFALLS.md** | **LOW relevance — execution pitfalls, not design pitfalls** | §3 (Short Drama AI Generation pitfalls: copyright, 平台审核, hook/retention mismatched to platform, 付费卡点 feels manipulative, 爆款公式 over-fitting) — **relevant** as constraints on derived nodes (e.g., a derived "compliance" node must exist because 平台审核 rejection is real). §6 (Project Management: 18-expert parallel execution collapse) — meta-pattern; relevant as warning against over-fragmenting node set. | §1 (RAG-Augmented Skills pitfalls), §2 (LLM-as-Judge), §4 (Bilingual Content), §5 (Hermes Framework Integration), §7 (AI tool version drift) — all skill-build concerns; v2.0 produces no skills, no eval, no Hermes integration. |
| **v1 SUMMARY.md** | **PARTIAL — phase-structure recommendations obsolete, key-findings synthesis relevant** | Key Findings #1-15 — specifically #2 (EXPERT-COMPLI is regulatory gate), #5 (verified current Hermes backend catalog), #8 (EXPERT-HOOK is commercial engine), #11 (snapshot-before-refactor protocol — analogue for "snapshot inherited pipeline before first-principles critique") — relevant as background. | Recommended Build Order (7 phases for skill-building), Phase Ordering Rationale, Research Flags (all phase-specific to skill-build work). |

### 6.2 Summary of carryover

**Carry forward:** AI generation tool stack inventory, inherited fragmentation state (26 experts + 15 kais sub-skills), inherited DAG structure, 短剧-specific pitfalls (copyright + 平台审核 + hook-craft), bilingual pattern.

**Discard:** Hermes memory plugin internals, eval harness mechanics, vector DB choice, per-skill table-stakes/differentiators, RAG-augmentation patterns, GLM overload warnings.

---

## 7. Recommended "Stack" Summary (One-Pager)

| Layer | Source / Methodology | Physical location | Why for v2.0 |
|---|---|---|---|
| **Primary corpus** | 102-book film library (MinerU-converted) | `/home/kai/Downloads/100+本影视剪辑书/converted/` (102 books, ~9.7M chars) + `/indexes/books-index.md` (16-category index) | Authoritative answer to "what is the irreducible human craft of cinema?" |
| **Pre-synthesized skill corpus** | skills-影视创作 6-stage taxonomy (95+ files) | `/home/kai/Downloads/100+本影视剪辑书/skills-影视创作/{00-orchestrator,01-剧本,02-分镜,03-拍摄,04-后期,05-制片,06-理论批评,case-studies}/` | The "prior synthesis" first-principles must deliberately diverge from or build on |
| **Already-integrated hermes corpus** | 12 project-corpus ref files | `skills/movie-experts/_shared/project-corpus/` | Concentrated answers to theory + craft + producing node-design questions |
| **Inherited pipeline history** | V1/V2/V4.1/V6/V8 architecture evolution | `/data/workspace/kais-movie-agent/docs/{ARCHITECTURE_AND_WORKFLOW,WORKFLOW,V2-REFACTOR-PLAN,v6-architecture-notion,V8-ARCHITECTURE}.md` + 15 kais-* sub-skills | The "what was tried" dataset — first-principles must explicitly question inherited assumptions |
| **Methodology canon — primary** | Musk first-principles (Kevin Rose 2012, Isaacson biography 2023) | URLs in §4.1 | The core methodology mandated by milestone context |
| **Methodology canon — adjacent** | Aristotle first principles + TRIZ contradiction matrix | URLs in §4.2 | Complementary lenses; Aristotle for "foundational truth" framing, TRIZ for contradiction-resolution when node-design surfaces trade-offs |
| **LLM story-gen research** | 8 references covering plot-hole detection, consistency benchmarks, story-generation surveys, creator-centric methods | URLs in §5 | The "LLM 创意凝练" sub-document evidence base |
| **v1 carryover** | v1 STACK §3 (AI tool stack), FEATURES §5-6, ARCHITECTURE DAG, PITFALLS §3, SUMMARY key findings | `.planning/research/{STACK,FEATURES,ARCHITECTURE,PITFALLS,SUMMARY}.md` | Background context for "where did we come from?" without re-doing completed work |

---

## What NOT to Recommend (v2.0 produces ZERO code)

Per milestone context, this STACK.md recommends **no code libraries, no infrastructure, no vector DBs, no frameworks**. The deliverable form is design docs. If a future phase needs implementation tech (when kais-movie-agent/.planning/ opens a corresponding phase), that's a separate STACK research effort.

| Avoid recommending | Why |
|---|---|
| Any npm package, Python package, or Docker config | Milestone produces zero code |
| Vector DB (sqlite-vec, Chroma, Qdrant) | Milestone produces zero infrastructure |
| LLM provider / model recommendations | Design-doc only; provider choices belong to implementation phases |
| Eval framework (MT-Bench, Ragas, DeepEval) | v2.0 has no eval — design docs only |
| Framework (FastAPI, LangChain, etc.) | Out of scope |

---

## Sources

### Primary (HIGH confidence — direct filesystem / file reads on 2026-06-16)

- `/home/kai/Downloads/100+本影视剪辑书/` — direct `ls` of root, `converted/` (105 entries), `skills-影视创作/` (8 subdirs), `indexes/`, `scripts/`
- `/home/kai/Downloads/100+本影视剪辑书/indexes/books-index.md` — 102-book index with 16-category breakdown + per-book word counts
- `/data/workspace/hermes-agent/skills/movie-experts/README.md` — 26-expert inventory (14 original + 4 Phase 1-5 + 5 Phase 7 + 3 Phase 8) + 9-ref project-corpus overview
- `/data/workspace/hermes-agent/skills/movie-experts/_shared/project-corpus/README.md` — 102-book integration index with skill→book mapping
- `/data/workspace/hermes-agent/skills/movie-experts/_shared/project-corpus/` — direct `ls` (14 files; README + INTEGRATION-REPORT + 12 content refs)
- `/data/workspace/kais-movie-agent/docs/{ARCHITECTURE_AND_WORKFLOW,WORKFLOW,V2-REFACTOR-PLAN,v6-architecture-notion,V8-ARCHITECTURE}.md` — direct file reads of all 5 architecture docs
- `/data/workspace/kais-movie-agent/README.md` — current 7-skill structure + sketch-pipeline
- `/data/workspace/kais-movie-agent/skills/` — direct `ls` (15 kais-* sub-skills)
- `/data/workspace/hermes-agent/.planning/PROJECT.md` — v2.0 milestone context (Current Milestone section)
- `/data/workspace/hermes-agent/.planning/MILESTONES.md` — v1 milestone history
- `/data/workspace/hermes-agent/.planning/research/{SUMMARY,STACK,FEATURES,PITFALLS}.md` — v1 carryover audit (ARCHITECTURE.md not read directly; assessed via SUMMARY references)

### Secondary (MEDIUM-HIGH confidence — WebSearch verified June 2026)

- [James Clear — First Principles: Elon Musk on the Power of Thinking for Yourself](https://jamesclear.com/first-principles) — Musk Kevin Rose quote
- [Elon Musk - Childhood and Work Philosophy (Foundation Series #3)](https://www.kevinrose.com/p/elon-musk-interview-kevin-reboots-the-old-foundation-series) — primary Foundation interview
- [First Principles Method Explained by Elon Musk — YouTube](https://www.youtube.com/watch?v=NV3sBlRgzTI) — Musk explainer video
- [Elon Musk (Isaacson book) — Wikipedia](https://en.wikipedia.org/wiki/Elon_Musk_(Isaacson_book)) — biography overview
- [Graham Mann — Book Notes: Elon Musk (Walter Isaacson)](https://grahammann.net/book-notes/elon-musk-walter-isaacson) — first-principles as Musk's superpower
- [Lex Fridman — Walter Isaacson transcript](https://lexfridman.com/walter-isaacson-transcript/) — first-principles discussion
- [WSJ — Elon Musk's Lessons From Hell: Five Commandments for Business](https://www.wsj.com/business/media/elon-musk-biography-walter-isaacson-951a47bd) — Isaacson insights
- [HEY World — Get back to first principles](https://world.hey.com/charlietarr/get-back-to-first-principles-bd36d441) — reader synthesis
- [FourMinuteBooks — Elon Musk Summary](https://fourminutebooks.com/elon-musk-summary-walter-isaacson/) — "Physics is the law" quote

### Methodology — Adjacent (MEDIUM-HIGH)

- [First principle — Wikipedia](https://en.wikipedia.org/wiki/First_principle) — Aristotle's foundational role
- [Aristotle, Physics, I, 1 — Logos Virtual Library](http://www.logoslibrary.org/aristotle/physics/11.html) — primary text (Hardie & Gaye)
- [Aristotle's Metaphysics — Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/aristotle-metaphysics/) — scholarly overview
- [TRIZ — Wikipedia](https://en.wikipedia.org/wiki/TRIZ) — Altshuller inventive-problem-solving overview
- [TRIZ40.com — 40 Principles](https://www.triz40.com/aff_Principles_TRIZ.php) — interactive matrix
- [Contradiction Matrix — The TRIZ Journal](https://the-trizjournal.com/contradiction-matrix-40-principles-innovative-problem-solving/) — methodology guide
- [IEEE — TRIZ 40 Principles Ranking](https://ieeexplore.ieee.org/document/8226329/) — empirical "20 of 40 cover 75%" finding

### LLM story-generation research (MEDIUM-HIGH)

- [Plot Hole Detection benchmark — arXiv 2504.11900](https://arxiv.org/html/2504.11900v1)
- [ConStory-Bench — arXiv 2603.05890](https://arxiv.org/html/2603.05890v1) + [GitHub](https://github.com/Picrew/ConStory-Bench)
- [CONFACTCHECK — ACL 2025 Findings](https://aclanthology.org/2025.findings-ijcnlp.129/)
- [Survey on LLMs for Story Generation — EMNLP 2025 Findings](https://aclanthology.org/2025.findings-emnlp.750.pdf)
- [Learning to Reason for Long-Form Story Generation — OpenReview](https://openreview.net/forum?id=dr3eg5ehR2)
- [Awesome-Story-Generation — GitHub](https://github.com/yingpengma/Awesome-Story-Generation)
- [Creator-Centric Methods for LLM-Assisted Interactive Narrative — ACM](https://dl.acm.org/doi/10.1145/3772318.3791362)
- [Scaffolding the Story: An LLM-Based Assessment — IASDR](https://dl.designresearchsociety.org/cgi/viewcontent.cgi?article=1644&context=iasdr)

---

*Stack research for: v2.0 PRFP — Pipeline Redesign from First Principles (kais-movie-agent node-set derivation)*
*Researched: 2026-06-16*
