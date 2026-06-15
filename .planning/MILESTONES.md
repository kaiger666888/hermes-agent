# Milestones

## v1 — Movie-Experts Suite v2 (Shipped: 2026-06-15)

**Phases completed:** 7 phases (0-6) · **Plans:** 15 · **Tasks:** 25
**Tag:** `v1`
**Known deferred items at close:** 6 (see [STATE.md § Deferred Items](./STATE.md#deferred-items))

**One sentence:** RAG-augmented 18-expert movie-making skill suite (14 refactored + 4 new) covering 短剧 / 微电影 creation end-to-end, with MT-Bench position-swap eval harness and operator-deferred live statistical run.

### Key accomplishments

- **Phase 0 — Audit + Eval Skeleton:** Stripped 5 phantom refs (`wan22_video`, "168K controlled tokens", FLUX 1.x samplers, AudioLDM-2, CosyVoice) from existing 14 SKILL.md files. Built byte-exact snapshot tool (sha256 + git sha + ISO 8601) + MT-Bench position-swap eval harness (`runner.py` 616 lines, `judge_prompt.md` 4-dimension rubric, 3-condition ablation template). Captured 14 pre-refactor baselines as the eval anchor.
- **Phase 1 — EXPERT-COMPLI (Legal Gate):** Built `compliance_marketing` expert end-to-end — 5 refs (cn-content-rules covering 网信办 AI 标识办法 2025-09-01 + AI 漫剧 备案 regime 2026-04-01 + 3 platform specs 抖音/快手/小程序剧 + 8-category 红线 + 5-type 爆款 taxonomy) + bilingual SKILL.md + 5 eval prompts. Wired bidirectionally into 4 existing experts.
- **Phase 2 — EXPERT-HOOK (Commercial Engine):** Built `hook_retention` expert — 4 refs (`three-second-hooks`, `conflict-escalation`, `paywall-design` with 卡点 density + 3-tier 🟢🟡🔴 strength, `vertical-pacing` with multi-platform variation) + SKILL.md + 5 eval prompts.
- **Phase 3 — Top-4 RAG:** Deep-refactored screenplay / editor / colorist / style_genome with 5 curated refs each (20 total refs, ~400KB). Ran 36-verdict dry-run producing `_eval/reports/phase3-ablation-dryrun.md` + `_eval/reports/phase3-go-nogo.md` (CONDITIONAL GO — deferred to Phase 6 live run for statistical evidence).
- **Phase 4 — EXPERT-CINE (Camera Language):** Built `cinematographer` expert — boundary doc vs scene_builder / animator / editor authored BEFORE SKILL.md to prevent scope creep. 4 refs (shot-grammar, axis-rules, vertical-screen-framing, camera-motion-catalog) + SKILL.md + 3 prompts + 7 peer related_skills updates.
- **Phase 5 — Remaining 10 + EXPERT-PROD (v1.5):** Built `production` expert (AI-relevant subset only per PROD-07 — character LoRA spec, wardrobe, lighting intent, GPU budget, asset reuse; NOT live-action). 5 refs + SKILL.md + 3 prompts + 8 peer edges. Light-uplifted remaining 10 existing experts (2 refs each = 20 total). Carried forward all Phase 0 phantom strips.
- **Phase 6 — Full Eval + Bilingual + README:** Published top-level `skills/movie-experts/README.md` documenting 18-expert collaboration DAG + RAG usage guide (static refs / memory plugin / provider-agnostic) + Phase 6 live-run procedure (6-step operator runbook) + bilingual consistency section + file layout tree. Live run deferred to operator (requires `OPENROUTER_API_KEY` + budget).

### Shipped artifacts

- 18 expert directories under `skills/movie-experts/` (14 original refactored + 4 new)
- 58 markdown refs (~1.2MB cited fair-use content), all with LICENSE.md + `Last-verified: 2026-06-15` stamps
- `_eval/` harness: `runner.py`, `snapshot.py`, `judge_prompt.md`, `config.yaml.example`, 9 prompt files, `baseline/` × 14, `reports/` × 40+
- `_shared/`: `glossary.md` (EN↔CN), `known-external-models.yaml` (33-entry allowlist), `platform-comparison.md`, `RAG-INVOCATION-PATTERN.md`, `SKILL-LAYOUT.md`
- Top-level `README.md` (297 lines, 20KB)

### Known gaps at close

- Phase 6 UAT not executed (10 checkpoints paused at user redirect — see `06-UAT.md`)
- Phase 1 VERIFICATION `human_needed` — CN legal content + platform-spec thresholds + judge prompt quality + glossary completeness all require human/expert review
- Live-run statistical GO/NO-GO deferred to operator per CONTEXT D-11 (budget decision)

See `.planning/milestones/v1-ROADMAP.md` for full phase details and `.planning/milestones/v1-REQUIREMENTS.md` for requirement outcomes.

---
