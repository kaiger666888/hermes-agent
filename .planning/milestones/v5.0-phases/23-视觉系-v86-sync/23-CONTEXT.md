# Phase 23: 视觉系 V8.6 sync - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous infrastructure-like phase)

<domain>
## Phase Boundary

Update 6 视觉系 experts' SKILL.md body to reference V8.6 Step positions and document dreamina CLI integration per kais-movie-agent V8.6 canonical mapping. Scope = body-only patches (add V8.6 Pipeline Sync section + dreamina CLI cross-references), no frontmatter changes, no new files.

**Target experts (6):** visual_executor / prompt_injector / character_designer / cinematographer / colorist / style_genome

</domain>

<decisions>
## Implementation Decisions

### Patch Pattern

For each of the 6 expert SKILL.md files, **append a new H2 section** `## V8.6 Pipeline Sync (Phase 23 v5.0)` near the end of the file (before `## What NOT to do` or at file end). This mirrors the v4.0 patch pattern (e.g. `### E-Konte Field Extraction (Optional Input) — Phase 20 v4.0` in visual_executor/SKILL.md line 99).

The new section contains:
1. **V8.6 Step Positions** — table mapping this expert to its V8.6 Step role(s)
2. **dreamina CLI Integration** (visual experts only) — cross-reference to `_shared/dreamina-cli-baseline.md` with specific sub-commands used
3. **Atomic Step Mergers Affecting This Expert** — note any V8.6 step combinations (e.g. Step 7 视觉+风格化 merges 4 experts into one atomic op)
4. **V8.4 Historical Context** — if the expert was created/renamed/merged in V8.4, document that lineage
5. **Cross-References** — link to other v5.0 phases (Phase 22 baseline + Phase 27 mapping)

### Per-Expert V8.6 Mapping (from kais-movie-agent V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查")

| Expert | V8.6 Step | Co-Experts | dreamina CLI Usage |
|--------|-----------|------------|-------------------|
| visual_executor | Step 4 (主角设计+资产库) + Step 5 (场景设计) + Step 7 (视觉种子+风格化) | character_designer (4) / cinematographer+style_genome (5) / prompt_injector+style_genome+colorist (7) | image2image (drawer) / multimodal2video, multiframe2video, frames2video (animator) |
| prompt_injector | Step 7 pre-node (V8.4 NEW) | visual_executor + style_genome + colorist | N/A (translates intent → dreamina-compatible model_prompts) |
| character_designer | Step 4 (主角设计+资产库) | visual_executor | N/A (defines L1-L4 contract; visual_executor generates) |
| cinematographer | Step 5 (场景设计) + Step 6 (运镜+终审) + Step 8 (运镜+节奏) | style_genome+visual_executor (5) / screenplay+script_auditor (6) / editor (8) | N/A (shot intent layer; V8.4 folded scene_builder + storyboard_designer here) |
| colorist | Step 7 (视觉种子+风格化) | visual_executor + prompt_injector + style_genome | N/A (color intent encoding feeds prompt_injector) |
| style_genome | Step 2.5 (前置) + Step 5 (场景设计) + Step 7 (视觉种子+风格化) | creative_source+screenplay (2.5 upstream) / cinematographer+visual_executor (5) / visual_executor+prompt_injector+colorist (7) | N/A (5D style vector feeds downstream) |

### Claude's Discretion

- Exact wording of new sections is at Claude's discretion — bilingual format per CLAUDE.md (EN structure + CN prose)
- Section header format: `## V8.6 Pipeline Sync (Phase 23 v5.0)` to mirror v4.0 patch pattern
- Tables use the same column structure as existing v4.0 patches
- All cross-references use relative paths (`../_shared/dreamina-cli-baseline.md`)

</decisions>

<code_context>
## Existing Code Insights

### v4.0 Patch Precedents (mirror these patterns)
- `visual_executor/SKILL.md:99` — `### E-Konte Field Extraction (Optional Input) — Phase 20 v4.0`
- `cinematographer/SKILL.md:177` — `## E-Konte as Intermediate Format (Phase 20 v4.0)`
- `style_genome/SKILL.md:170` — `## SCAMPER Variation Layer (Stacked on style_blend)`
- All v4.0 patches preserve byte-identical frontmatter + do NOT touch existing sections

### Section Insertion Points
- **visual_executor**: After `## Sub-step: Animator (Video Generation)` section content, before file end (currently ends ~line 337 with What NOT to do / Quality Thresholds)
- **prompt_injector**: After `## Collaboration` (line 248), before `## Changelog` (line 264)
- **character_designer**: After `## Collaboration` (line 248), before `## What NOT to do` (line 263)
- **cinematographer**: Replace or extend `## Pipeline Position` (line 234) — add V8.6 subsection
- **colorist**: After `## Collaboration` (line 168), before `## What NOT to do` (line 178)
- **style_genome**: Replace or extend `## Pipeline Position` (line 255) — add V8.6 subsection

### Integration Points
- All 6 patches cross-reference `_shared/dreamina-cli-baseline.md` (Phase 22 deliverable, already shipped)
- All 6 patches will be referenced by `_shared/v86-pipeline-mapping.md` (Phase 27 deliverable)
- FOUND-08 frozen rule: zero frontmatter changes, zero expert_id renames, zero DAG modifications

</code_context>

<specifics>
## Specific Ideas

### V8.6 Step Mapping Reference (from kais-movie-agent V8.6 SKILL.md)

V8.6 管线精简 25→13 步,关键合并:
- **Step 1**: hook_retention 共鸣+主题一步到位(原 Step 1+2)
- **Step 2**: creative_source+screenplay 框架+大纲一步到位(原 Step 2.5+3)
- **Step 3**: screenplay+script_auditor 剧本+审计原子操作(原 Step 5+5B+6)
- **Step 6**: screenplay+cinematographer+script_auditor 运镜+终审(原 Step 11+12)
- **Step 7**: visual_executor+prompt_injector+style_genome+colorist 视觉+风格化(原 Step 13A+15)
- **Step 11**: audio_pipeline BGM+音效+口型统一(原 Step 18+17B)

V8.6 审核门 12→8 个,用户等待轮次减半。Expert 调用 15→10 次。

### dreamina CLI Cross-Reference Pattern (for visual experts)

```markdown
### dreamina CLI Integration

视觉生成走 dreamina CLI(`_shared/dreamina-cli-baseline.md`):

| 子步骤 | dreamina 子命令 | 参考图用法 |
|-------|----------------|-----------|
| drawer (image gen) | `dreamina text2image` / `dreamina image2image` | L1+L2 双参考(`--images L1.png,L2.png`) |
| animator (video gen) | `dreamina multimodal2video` / `multiframe2video` / `frames2video` | L1+scene 绑定(`@Image1 provides identity...`) |

**禁止**推荐 jimeng-client.js(V8.5 废弃)或 gold-team `image_draw`(仅 DEGRADE 路径)。
```

</specifics>

<deferred>
## Deferred Ideas

- Live-run validation of V8.6 pipeline integration prompts → FUTURE-10 (deferred to operator)
- Automated cross-expert drift detection → FUTURE-11 (tooling not yet built)

</deferred>
