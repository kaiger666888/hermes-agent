# Phase 0: AUDIT + Eval Skeleton (BLOCKER GATE) - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 0 establishes the credibility anchor for the entire Movie-Experts Suite v2 build: it eliminates phantom references already shipping in the 14 existing SKILL.md files, captures a reproducible pre-refactor baseline, and builds the LLM-as-judge double-blind harness skeleton so every subsequent "improvement" claim in Phases 1-6 is statistically defensible.

This phase is the BLOCKER GATE — no other phase starts until it passes.

In scope:
- Audit 14 existing experts → produce GAP-REPORT.md per expert
- Strip phantom refs (`wan22_video`, fabricated "168K controlled tokens", FLUX 1.x sampler params)
- Build `scripts/verify_skill_references.py` CI lint
- Build `_eval/{runner,snapshot,judge_prompt}` skeleton + 1 demo run
- Capture baseline snapshots × 14
- Publish `_shared/glossary.md` EN↔CN dictionary skeleton
- Document standard skill layout + provider-agnostic RAG invocation pattern
- Preserve all 14 `expert_id` values unchanged

Out of scope:
- Full N≥20 eval runs (deferred to Phase 6)
- Deep refactoring of any expert (Phase 3, 5)
- New expert creation (Phase 1, 2, 4)
- RAG corpus content authoring (Phase 3+)

</domain>

<decisions>
## Implementation Decisions

### Eval Harness Scope
- Skeleton + 1 sample-expert demo (proves harness works per SC #3)
- Custom MT-Bench implementation ≤200 LOC using only existing Hermes deps (`openai`, `pyyaml`, `jinja2`) — no new packages per EVAL-08
- Output format: JSON (for downstream tooling/re-runs) + Markdown summary (for human review per EVAL-07)
- Location: `skills/movie-experts/_eval/` — co-located with skills it evaluates; NOT registered in Hermes tool registry per EVAL-09 (offline developer tooling only)

### Judge Panel Composition
- Open-weight panel via OpenRouter free tier (e.g., Qwen3-235B, DeepSeek-V3) — zero variable cost during dev; satisfies cross-vendor diversity per EVAL-06
- 2 judges minimum per comparison (meets EVAL-06 floor; tie = no win handles disagreement)
- Judge temperature pinned at 0 (greedy decoding for determinism per EVAL-03)
- Judge prompt: CoT reasoning followed by `<decision>A|B|tie</decision>` tag for predictable parsing

### Phantom Reference Handling
- "Phantom" = any model/tool/sampler/concept name not present in `plugins/` inventory or known external canon
- Detection: regex over SKILL.md for model-name-shaped tokens (`[a-z][a-z0-9_]+(?:_video|_turbo|_[0-9]+[bB])`), validated against allowlist auto-built from `plugins/*/plugin.yaml`
- Handling: case-by-case in GAP-REPORT — strip if fabricated (e.g., "168K controlled tokens"), rewrite if concept valid but vendor wrong (e.g., `wan22_video` → `<video_gen_primary>` placeholder)
- Allowlist governance: auto-generated from `plugins/*/plugin.yaml` at lint time + manual override file `_shared/known-external-models.yaml` for non-plugin models (Sora, Veo, etc.)
- Provider-agnostic token convention: `<video_gen_primary>`, `<image_gen_primary>` placeholders in SKILL.md body (per PROJECT.md "Provider-agnostic RAG invocation" hard rule); specific model names appear only in refs (which can be versioned)

### GAP-REPORT Format & Baseline Snapshot Strategy
- GAP-REPORT structure per expert: `<phantoms>` / `<knowledge_gaps>` / `<prompt_weak_points>` / `<stale_metrics>` / `<missing_refs_topics>` — matches FOUND-01 spec; downstream Phase 3/5 can grep specific sections
- Baseline snapshot = full SKILL.md copy + frontmatter hash + git SHA + timestamp (provenance for reproducibility)
- Baseline location: `skills/movie-experts/_eval/baseline/<expert>/SKILL.md`
- Baseline tag: `eval-baseline-v1` (single tag; v2 only if Phase 3 RAG uplift triggers re-baseline)

### Claude's Discretion
- Specific Python style within `runner.py`/`snapshot.py`/`verify_skill_references.py` (function decomposition, argparse vs fire, async vs sync)
- Judge prompt wording details (the 4-anchor CoT structure)
- Exact regex pattern for phantom detection (refined during implementation)
- Order of experts to process (alphabetical default)
- Whether to include sample eval prompts in Phase 0 or defer to Phase 1+ (default: defer, Phase 0 only proves harness runs)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **14 existing SKILL.md files** under `skills/movie-experts/{animator,colorist,composer,continuity,drawer,editor,foley,mixer,performer,scene_builder,screenplay,spatial_audio,style_genome,voicer}/` — these are the audit targets AND baseline snapshot sources
- **`plugins/image_gen/{fal,krea,openai,openai-codex,xai}/plugin.yaml`** — 5 real image providers (allowlist source)
- **`plugins/video_gen/{fal,xai}/plugin.yaml`** — 2 real video providers (allowlist source; note: NO `wan22_video` exists)
- **`.planning/codebase/STACK.md`** — confirms Python 3.11+, OpenAI SDK 2.24.0, PyYAML 6.0.3, Jinja2 3.1.6 are all available (no new deps needed for harness)
- **`pyproject.toml`** — `[dev]` extra has pytest 9.0.2 + Ruff 0.15.10; `[tool.ruff.lint]` only enables `PLW1514` (must add `encoding="utf-8"` to every `open()`)

### Established Patterns
- **SKILL.md frontmatter schema** — `name`, `description`, `version`, `author`, `license`, `platforms`, `prerequisites.tools`, `metadata.hermes.{tags, related_skills, expert_id, metrics}` (see `performer/SKILL.md` for reference)
- **Plugin manifest schema** — `plugin.yaml` declares provider tool/model catalog; can be parsed with `ruamel.yaml` or `pyyaml`
- **`hermes_constants.get_hermes_home()`** — canonical state root; tests redirect via `HERMES_HOME` env var
- **Three-tier prompt caching** — not relevant to offline eval harness but informs that we should NOT cache judge prompts across runs (deterministic re-runs)
- **Ruff PLW1514** — every `open()` call must specify `encoding="utf-8"` or CI fails

### Integration Points
- **`skills/movie-experts/_eval/`** — new directory; NOT auto-discovered by skill loader (loader only finds `SKILL.md` files), so safe from accidental registration
- **`scripts/verify_skill_references.py`** — repo-root script; CI workflow at `.github/workflows/lint.yml` should add it as a step (but adding the CI step itself may be Phase 6 polish — Phase 0 only requires the script exists and runs)
- **`skills/movie-experts/_shared/glossary.md`** — new shared doc; future experts reference this for EN↔CN term consistency
- **Baseline snapshots** consumed by `_eval/snapshot.py` and later by Phase 3/6 ablation comparisons

</code_context>

<specifics>
## Specific Ideas

- The `verify_skill_references.py` script MUST produce machine-readable output (JSON) AND human-readable (Markdown summary) — downstream GAP-REPORT generation needs structured data, operators need readable diffs
- The `judge_prompt.md` template should anchor on 4 evaluation dimensions: (1) **industry_accuracy** (does output match real-world 短剧 craft?), (2) **professional_depth** (concrete heuristics vs hand-wavy advice?), (3) **actionability** (can a creator act on this?), (4) **language_quality** (bilingual consistency, no awkward phrasing)
- The 1 sample-expert demo should pick an expert with KNOWN phantom refs (animator with `wan22_video` or performer with "168K controlled tokens") so the demo doubles as validation that phantoms were stripped
- Glossary skeleton must include at minimum: 运镜 / hook / 卡点 / 爆款 / 男频 / 女频 / 完播率 / 付费卡点 / 钩子 / 爽点 / 击中点 / 镜头语言 / 景别 / 视角 / 轴线 / 调度 — per SC #5

</specifics>

<deferred>
## Deferred Ideas

- **CI integration of `verify_skill_references.py`** into `.github/workflows/lint.yml` — Phase 0 produces the script; wiring it into CI gate is Phase 6 polish (when README + full eval land)
- **N≥20 full eval runs** — Phase 6 (after all experts refactored)
- **Statistical significance reporting** (CIs, p-values) — Phase 3 GO/NO-GO gate and Phase 6 final report
- **Vector RAG (memory plugin) integration** — Phase 3 RAG uplift experiments only
- **Glossary expansion beyond core 16 terms** — Phase 1+ as each new expert needs more terms
- **Auto-generated allowlist refresh hook** — Phase 6 polish (when plugin inventory stabilizes)

</deferred>
