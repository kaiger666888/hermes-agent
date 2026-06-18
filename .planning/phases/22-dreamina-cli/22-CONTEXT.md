# Phase 22: dreamina CLI 知识基线 - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous infrastructure-like phase)

<domain>
## Phase Boundary

Create `skills/movie-experts/_shared/dreamina-cli-baseline.md` — the cross-expert shared reference documenting dreamina CLI as the canonical image/video generation tool per kais-movie-agent V8.5. This ref unblocks downstream expert V8.6 sync phases (P23 VISUAL-02 + P25 AUDIO-02 both reference this baseline).

The ref must cover: (1) 6 dreamina CLI sub-commands with full signatures, (2) L1/L2/L3/L4 character asset library strategy, (3) async poll pattern (`--poll 0` submit + `dreamina query_result --submit_id` poll + `aria2c URL` download), (4) gold-team fallback path (gold-team now video/TTS/3D only — image generation does NOT go through gold-team), (5) explicit deprecation notice for jimeng-client.js.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation choices are at Claude's discretion — this is a pure knowledge-layer increment with scope fully defined by DREAMINA-01..05 in REQUIREMENTS.md. Source-of-truth is kais-movie-agent V8.5/V8.6 SKILL.md (`/data/workspace/kais-movie-agent/SKILL.md`).

Key constraints:
- **Single ref file** at `_shared/dreamina-cli-baseline.md` (NOT scattered across expert directories)
- **verified_date: 2026-06-19** stamped in header
- **LICENSE.md attribution row** added to `_shared/LICENSE.md` (or per-ref LICENSE if convention differs)
- **Bilingual format** following _shared convention (EN structure + CN prose/examples)
- **Source citations**: kais-movie-agent V8.5 commit `c22867d` + V8.6 commit `e41fa68` as primary; dreamina CLI docs (fair-use paraphrase) as secondary

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_shared/glossary.md` — EN↔CN bilingual glossary, will receive 3+ new H3 entries in P27
- `_shared/RAG-INVOCATION-PATTERN.md` — existing pattern for how experts invoke shared refs
- `_shared/SKILL-LAYOUT.md` — documents _shared/ ref conventions
- `_shared/known-external-models.yaml` — may need dreamina CLI entry (currently lists 33 model entries)

### Established Patterns
- v4.0 snowflake-method.md / e-konte-format.md / scamper-variations.md are recent exemplars of `_shared/` ref structure (header + sections + bilingual)
- Each ref carries verified_date + LICENSE attribution
- Refs use code blocks for command signatures, tables for parameter mappings

### Integration Points
- `_shared/dreamina-cli-baseline.md` will be referenced by:
  - P23 visual_executor/SKILL.md (VISUAL-02 dreamina CLI image2image/multimodal2video integration)
  - P25 audio_pipeline/SKILL.md (AUDIO-02 multimodal2video audio binding)
  - P27 _shared/v86-pipeline-mapping.md (canonical tool registry)

</code_context>

<specifics>
## Specific Ideas

The 6 dreamina CLI sub-commands per kais-movie-agent V8.5 SKILL.md (canonical tool registry):
- `dreamina text2image --prompt "..." --model_version 5.0 --ratio 16:9 --resolution_type 2k --poll 0`
- `dreamina image2image --images L1_face.png,L2_costume.png --prompt "..." --model_version 5.0 --ratio 3:4 --resolution_type 2k --poll 0`
- `dreamina multimodal2video --image L1_01.png --image L1_02.png --image scene.png --prompt "@Image1 provides identity..." --model_version seedance2.0fast --duration 5 --ratio 16:9 --poll 0`
- `dreamina multiframe2video --images frame1.png,frame2.png,frame3.png --transition-prompt "A to B" --transition-prompt "B to C" --poll 0`
- `dreamina frames2video --first ./start.png --last ./end.png --prompt "..." --model_version seedance2.0fast --duration 5 --poll 0`
- `dreamina image_upscale --image ./photo.png --resolution_type 4k --poll 0`

L1/L2/L3/L4 asset library strategy (per V8.5 §"角色一致性策略"):
- L1 身份锚点 (1-3 张面部/半身特写) → 角色参考 (Character Ref) — 锁定五官/骨相/发型/肤色,**永不更换**
- L2 造型卡片 (每套服装全身正面+侧面) → 智能参考 (Smart Ref) — 锁定服装/道具/造型
- L3 姿势包 (坐/站/走/跑等姿态) → 智能参考 — 动作参考
- L4 表情标定 (微笑/怒/惊/泪) → 智能参考 — 表情戏时使用

Key principle: 角色参考只传脸,智能参考传衣服/姿势. 不要混放!

</specifics>

<deferred>
## Deferred Ideas

- Live-run validation of dreamina CLI prompts against actual V8.6 pipeline run → FUTURE-10 (deferred to operator per REQUIREMENTS.md)
- Automated drift detection between kais-movie-agent V-number and hermes-agent internal knowledge → FUTURE-11 (tooling not yet built)

</deferred>
