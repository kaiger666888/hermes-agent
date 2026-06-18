# LICENSE — _shared/ cross-expert references

**Scope:** This LICENSE.md governs the v5.0+ reference files under `skills/movie-experts/_shared/` that explicitly declare `_shared/LICENSE.md` as their attribution registry. Currently governed:
- `dreamina-cli-baseline.md` (Phase 22 / v5.0)

Forward-looking: `_shared/` will accumulate more refs in Phase 27 (`v86-pipeline-mapping.md`), and that ref will append its own row to this file in Phase 27.

Pre-existing `_shared/` refs (`glossary.md` / `known-external-models.yaml` / `RAG-INVOCATION-PATTERN.md` / `SKILL-LAYOUT.md` / `quality-rubric.md` / `platform-comparison.md` / `cognitive-resonance-metrics.md`) are governed implicitly by virtue of being under `_shared/` but do not require individual rows in this LICENSE — they predate this convention (v1-v4.0), and their copyright status is established in their own file headers.

**Last-verified:** 2026-06-19
**verified_date:** 2026-06

---

## Copyright Status Summary

All `_shared/` refs covered by this LICENSE are authored under **Fair Use** (17 U.S.C. §107) or are original Hermes Agent analytical work. None reproduce copyrighted material beyond brief factual API signatures and explicitly-attributed fair-use citations (≤ 50 words per ref).

---

## Per-Ref Attribution

### `dreamina-cli-baseline.md` (Phase 22 / v5.0)

- **Source:** kais-movie-agent V8.5 SKILL.md (commit `c22867d`, 2026-06-18) + V8.6 SKILL.md (commit `e41fa68`, 2026-06-18), both at `/data/workspace/kais-movie-agent/SKILL.md`. Primary source sections: §"V8.5 更新" + §工具映射 + §"L1/L2 双参考角色一致性系统" + §"图片生成默认引擎".
- **Copyright status:** Fair Use —
  1. dreamina CLI command signatures (command name + CLI flags + parameter values) are factual API surface of an external tool, not copyrightable expression;
  2. the L1/L2/L3/L4 asset library strategy is an original Hermes Agent analytical encoding layer (4-tier classification, layer → API entry mapping, golden-standard heuristics) — not reproduced from any single kais-movie-agent copyrighted document;
  3. the async poll pattern + gold-team fallback path are factual integration descriptions of open-source kais-movie-agent pipeline behavior;
  4. the jimeng-client.js deprecation notice references the upstream project's own `@deprecated` annotation.
  No verbatim reproduction of kais-movie-agent prose beyond brief factual API signatures and the explicitly-attributed V8.5 update notes (≤ 50 words total, fair-use citation context).
- **Specific notes:** "dreamina" CLI name and the 6 sub-command names (`text2image` / `image2image` / `multimodal2video` / `multiframe2video` / `frames2video` / `image_upscale`) are factual API surface of the consumer-side tool. "jimeng-client.js" deprecation status is the upstream project's own annotation. L1 身份锚点 / L2 造型卡片 / L3 姿势包 / L4 表情标定 CN terms are factual classification labels of the upstream asset-library convention.
- **license_status:** `fair_use_paraphrase` (mirrors v4.0 INTEGRATION-04 pattern; to be re-declared in Phase 27 `skills-mapping.yaml` `v5_ref_signoffs` section).

---

## Author Warrant

The L1-L4 4-tier classification + golden-standard heuristics + Hermes expert guidance subsections are original analytical work by Hermes Agent. The dreamina CLI command signatures + flag values are factual API surface transcribed from the upstream open-source kais-movie-agent project (commit `c22867d` / `e41fa68`).

---

## Refresh Cadence

This LICENSE is re-verified whenever any governed `_shared/` ref is added or substantively updated. Per-ref `Last-verified:` stamps in each governed ref's header provide per-ref audit granularity (quarterly re-verification per `_shared/` convention).

**Drift triggers for `dreamina-cli-baseline.md`** (per ref's own Refresh Cadence section):
1. New dreamina CLI sub-command added
2. kais-movie-agent V-number bump
3. gold-team task-type catalog changes
4. jimeng-client.js fully removed from kais-movie-agent `lib/`

---

## Out of Scope

This LICENSE governs **only** the per-ref attribution + copyright status for `_shared/` refs. It does NOT govern:
- (a) Pre-existing `_shared/` refs (`glossary.md` etc.) which carry their own header copyright
- (b) Per-expert `references/LICENSE.md` files (those are governed per-expert; see e.g. `style_genome/references/LICENSE.md`)
- (c) The LICENSE of the upstream kais-movie-agent project itself (which is its own copyright concern)

---

*Owned by Phase 22 plan 22-01 (dreamina CLI 知识基线). No parallel plan touches this LICENSE.md file. Phase 27 will append additional rows when new `_shared/` refs are created.*
