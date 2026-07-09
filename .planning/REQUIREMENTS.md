# Requirements: Hermes Agent — v14.0 kais-movie-pipeline 4-Track Upgrade

**Defined:** 2026-07-09
**Core Value:** 让 hermes-agent 成为 Kai 的主 agent:v1-v6 movie-experts + v7-v9 openclaw+kais-movie-pipeline 迁移 + v10-v13 编排架构弧线已 shipped。v14.0 回到 kais-movie-pipeline 把 4 项核心生成环节升级到 production-grade(横竖双 default 形态 / CosyVoice 配音 / dreamina 深度集成 / 三层转场协作)。

**Source:** 用户 4-feature 请求(2026-07-09)+ `.planning/research/v14-4track-upgrade/SUMMARY.md`(4 parallel researcher + synthesizer 产出)。

---

## v14.0 Requirements

Requirements for v14.0 milestone. Each maps to roadmap phases (Phase 70+, continuing from v13.0 Phase 69)。

### FORM — 横竖并行双 default 参数化

- [x] **FORM-01**: User can specify project-level `form_factor` (`landscape_16_9` / `portrait_9:16`) via `PipelineState.form_factor` field, defaulting to `portrait` for backwards-compat with existing projects
- [x] **FORM-02**: Each of 15 active movie-expert skills has a `## Form Factor Adaptation` section with dual-branch (landscape/portrait) creative rules, replacing hardcoded `9:16` assumptions
- [x] **FORM-03**: User can read `references/horizontal-screen-framing.md` for landscape creative rules (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region), mirroring existing `vertical-screen-framing.md`
- [x] **FORM-04**: Step 14 platform-master-slicing handles 4-cell reframe matrix (`master_form_factor × target_platform_form_factor`: 16:9→9:16 / 9:16→16:9 / 16:9→16:9 / 9:16→9:16) without quality degradation
- [x] **FORM-05**: `kais-movie-pipeline/SKILL.md` line 446 stale `MSR_FC=17` corrected to canonical `MSR_FC=41` per 2026-07-01 A/B test (incidental tech-debt fix, not a standalone feature)

### DUB — CosyVoice + LTX 2.3 native audio 协调

- [ ] **DUB-01**: User can generate TTS via CosyVoice 2.0-0.5B as P10 default (replacing IndexTTS2) through ComfyUI `filliptm/ComfyUI_FL-CosyVoice3` node + `audio_pipeline/references/workflows/cosyvoice-comfyui.json`
- [ ] **DUB-02**: Schema validator rejects configurations where both LTX 2.3 native audio AND CosyVoice overlay are enabled for the same shot (prevents doubled audio / phase cancellation / lip-sync mismatch per PITFALL D-1)
- [ ] **DUB-03**: User can attach `voice_clone_reference_wav` (3-10s reference audio) per character in `pipeline_state.episode_id.character_voice_presets`; system fails fast with explicit error if missing when CosyVoice clone mode is selected
- [ ] **DUB-04**: IndexTTS2 ComfyUI node remains installed and accessible as DEPRECATED fallback path (CosyVoice failure → IndexTTS2 fallback; node not removed)
- [ ] **DUB-05**: Operator has A/B benchmark report comparing CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 on 3-5 kais-movie-pipeline reference dialogue lines; default variant recorded in `VERSION.json` with rationale

### IMG — dreamina cli 深度集成升级

- [ ] **IMG-01**: User can submit dreamina batch image generation via `dreamina_manager.py` orchestrator with `asyncio.Semaphore(10)` + `tenacity` retry + sync queue model (block on poll-all-before-deadline)
- [ ] **IMG-02**: `dreamina_manager.py` blocks `pipeline_state` write until ALL retries resolve (fixes SKILL.md line 619 pitfall — no missing reference images in P11 video render)
- [ ] **IMG-03**: Reference images are vision-verified via GLM-4.6V (content match + directional match e.g. LHD/RHD) before ComfyUI upload; vision-verify is a mandatory gate, not optional (fixes line 561 pitfall)
- [ ] **IMG-04**: RHD/LHD-type prompt failures are systematically mitigated via 3-attempt budget (prompt-engineering + verify-retry + image2image fallback) with documented expected success rate (fixes line 570 pitfall)
- [ ] **IMG-05**: User can run `hermes dreamina stats` CLI to see per-task latency / success rate / cost dashboard (SLA tracking via local MetricsBuffer)
- [ ] **IMG-06**: image2image workflow is standardized across the pipeline (reference image count + strength parameter + retry budget per ref-count stratum: 1-ref / 3-ref / 5-ref)

### TRANSITION — 创作+数据+生成三层协作

- [ ] **TRANS-01**: Cinematographer E-Konte Layer 5 schema is extended with `transition_method` (12-value enum: `hard_cut / dissolve / wipe / fade / match_cut_shared_object / match_cut_shared_landscape / motion_vector_match / color_match / j_cut / l_cut / whip_pan / none`) + `visual_hook` (具体连接元素) + `camera_continuity` (`pan_to / zoom_to / dolly_through / whip_pan / match_cut_on_motion / none`)
- [ ] **TRANS-02**: `next_shot_link` is refactored from string id to structured object `{shot_id, transition_method, visual_hook, camera_continuity, generation_path}` with backward-compat reader that coerces old string form to default `{transition_method: "hard_cut", ...}` for existing projects
- [ ] **TRANS-03**: User can write `transition_design.json` as a first-class asset, registered in 3 systems: asset-bus Phase 36 slot + canvas sync `_PHASE_OUTPUT_MAP` + zod enum (canvas-renderability per PITFALL T-4)
- [ ] **TRANS-04**: Field-level ownership split is documented in BOTH `cinematographer/SKILL.md` (Step 9 owns creative intent: `transition_method` / `visual_hook` / `camera_continuity`) AND `editor/SKILL.md` (Step 13 owns post-production execution: `cut_duration_frames` / `dissolve_curve` / `match_cut_alignment_point`); updated in the SAME phase (FOUND-08 preservation — NO new `transition_designer` expert)
- [ ] **TRANS-05**: User can read `references/transition-design.md` for the 12-type transition taxonomy mapped to execution paths (generation-time / post-production / hybrid) with concrete examples
- [ ] **TRANS-06**: Per-transition engine routing rule is documented in `references/transition-engine-routing.md`: Wan2.2 14B FLF2V for local match-cut via shared object / Hailuo 02 i2v Pro + Vidu keyframe-to-video for cloud Chinese-content backups (opt-in via operator API key) / ffmpeg xfade for dissolve/wipe/fade/J-cut/L-cut fallback / **LTX-2.3 FLF path evaluated per-transition (NOT assumed incapable — per SUMMARY reconciled conflict #1)**
- [ ] **TRANS-07**: LTX-2.3 FLF + ICLoRA combined workflow is validated on 1-2 reference shots (research-scope only — NOT pipeline-integrated); validation report documents whether combined workflow is production-ready or deferred to v15+

### Cross-cutting — 强制基础设施(milestone coherence 必需)

- [x] **XCUT-01**: Phase 0 Lineage Impact Assessment enumerates every SKILL.md to be touched with current `source_sha` BEFORE any edits land; curator `--live` mode is frozen for milestone duration (per PITFALL X-1, X-4)
- [ ] **XCUT-02**: Every MUST/MUST NOT added to SKILL.md is also encoded as a `_INSTRUCTION` constant in the relevant phase module's `goal` f-string with a test asserting the keyword appears in `captured["goal"]` (META-RULE X-2 prevention — "文档有规则,代码没执行"silently failure 防护)
- [ ] **XCUT-03**: Phase 5 Lineage Bump re-runs v13.0 P62 transform flow on 6 affected agents (`cinematographer / editor / audio_pipeline / drawer / kais-movie-pipeline / kais-jimeng-cli`); CI assertion `agent.yaml.source_sha == sha256(SKILL.md)` passes for all 6
- [ ] **XCUT-04**: Operator-action handoffs are documented in milestone audit: (a) CosyVoice `voice_clone_reference_wav` per character (3-10s samples); (b) Hailuo/Vidu API keys (opt-in for cloud transition engines); (c) vision-verify API cost budget (GLM-4.6V batch calls at production scale)

---

## Future Requirements (v15+)

Acknowledged but deferred. Tracked for roadmap visibility.

### FORM (defer)
- **FORM-06**: per-shot `form_factor` override (anti-pattern — project-level lock only; cross-shot consistency collapse risk)
- **FORM-07**: auto-`form_factor` inference from screenplay content (unreliable, ~40% wrong per FEATURES research)

### DUB (defer)
- **DUB-06**: real-time TTS streaming during video generation (race-condition architecture needed; current sync model sufficient)
- **DUB-07**: CosyVoice 2 `instruct2` fine-grained per-line control (emotion + speed + volume per line) — P2 differentiator; defer until CosyVoice 2 baseline proven in v14.0
- **DUB-08**: cross-shot voice_identity dimension in `continuity_auditor` (5th dimension)

### IMG (defer)
- **IMG-07**: auto-scaling concurrency (current 10-parallel is validated stable; auto-tune adds complexity without payoff until quota wall hit)
- **IMG-08**: multi-model routing (dreamina 5.0 vs Seedance 2.0 vs other) — defer until v14.0 dreamina_manager pattern proven
- **IMG-09**: vision-verify false-positive threshold calibration (research gap — needs production data to tune)

### TRANSITION (defer)
- **TRANS-08**: AI-generated whip pan transitions (current generation engines unreliable for cross-shot motion-vector continuity)
- **TRANS-09**: custom transition types beyond 12-value taxonomy (industry-standard taxonomy sufficient; avoid over-engineering)
- **TRANS-10**: per-transition runtime LLM routing decisions (INFRA-04 serial constraint violation risk; v14.0 uses declarative rules only)
- **TRANS-11**: LTX-2.3 FLF + ICLoRA combined workflow **production rollout** (research-scope validation in TRANS-07; production rollout gated by validation result, defer to v15+ if not turnkey)

### Cross-cutting (defer)
- **XCUT-05**: full 15-agent lineage bump automation (v14.0 bumps 6; automation for full 15 deferred until meaningful)

---

## Out of Scope

Explicitly excluded from v14.0. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| IndexTTS2 full retirement | Loses fallback path; kept as DEPRECATED per DUB-04 |
| Voice cloning from unauthorized audio samples | Legal/ethical; operator must provide owned reference audio per DUB-03 |
| FLUX local image fallback | Kai-forbidden per existing pipeline rule (SKILL.md line 519); dreamina cli is sole image engine |
| Fully autonomous image gen with no operator review | ~5-10% wrong content; vision-verify mandatory gate but final review remains human |
| Parallel concurrency > 12 for dreamina cli | 20-parallel = 95% success rate per SKILL.md line 622; >12 exceeds validated safe zone |
| New `transition_designer` expert_id | FOUND-08 violation (frozen 15-expert set); resolved via field-level ownership split per TRANS-04 |
| LTX FLF+ICLoRA combined workflow production rollout | Research-scope validation only in TRANS-07; v15+ if validation passes |
| INFRA-04 serial constraint lift | Out of scope for v14.0; preserved per MEMORY.md `feedback-glm-overload-reduce-concurrency.md` |
| EVAL-06 dry-run-first change | Out of scope for v14.0; curator `--live` stays opt-in (frozen during v14.0 per XCUT-01) |
| 15-expert production tuning | v13.0 carryforward; Phase 64 live-eval operator-handoff drives v15+ decision |
| Physical partition (mem0 split) | v13.0 carryforward; Phase 64 EVAL-02 data drives v15+ decision |
| Per-shot `form_factor` mixing | Cross-shot consistency collapse; project-level lock only |
| Auto-`form_factor` inference from screenplay | Unreliable (~40% wrong); explicit project meta only |
| Real-time TTS streaming during video gen | Race-condition architecture; current sync queue model sufficient |
| Cross-engine runtime LLM routing decisions for transitions | INFRA-04 violation risk; declarative rules only in v14.0 |

---

## Traceability

Which phases cover which requirements. Filled by roadmapper 2026-07-09.

| Requirement | Phase | Status |
|-------------|-------|--------|
| XCUT-01 | Phase 70 (FOUNDATION-AUDIT) | Complete (all 6 sub-rows a-f shipped: a/b/c via Plan 01 inventory, d/e via Plan 02 freeze, f via Plan 03 checklist). Phase 70 ready for verification. |
| FORM-01 | Phase 71 (FORM) | Complete (Plan 71-01) |
| FORM-02 | Phase 71 (FORM) | Complete (Plan 71-02) |
| FORM-03 | Phase 71 (FORM) | Complete (Plan 71-01) |
| FORM-04 | Phase 71 (FORM) | Complete (Plan 71-03) |
| FORM-05 | Phase 71 (FORM) | Complete (Plan 71-01) |
| DUB-01 | Phase 72 (DUB) | In Progress (Plan 72-01: validator enables routing; Plan 72-02 wires workflow JSON + healthcheck) |
| DUB-02 | Phase 72 (DUB) | In Progress (Plan 72-01: validate_tts_engine_division shipped; Plan 72-02 wires p10_voice pre-flight) |
| DUB-03 | Phase 72 (DUB) | In Progress (Plan 72-01: validate_voice_clone_ref + schema field + fail-fast shipped; Plan 72-02 wires workflow submission) |
| DUB-04 | Phase 72 (DUB) | In Progress (Plan 72-01: DEPRECATED warning + progress metadata shipped; Plan 72-02 wires healthcheck-based auto-fallback) |
| DUB-05 | Phase 72 (DUB) | Pending |
| IMG-01 | Phase 73 (IMG) | Pending |
| IMG-02 | Phase 73 (IMG) | Pending |
| IMG-03 | Phase 73 (IMG) | Pending |
| IMG-04 | Phase 73 (IMG) | Pending |
| IMG-05 | Phase 73 (IMG) | Pending |
| IMG-06 | Phase 73 (IMG) | Pending |
| TRANS-01 | Phase 74 (TRANSITION) | Pending |
| TRANS-02 | Phase 74 (TRANSITION) | Pending |
| TRANS-03 | Phase 74 (TRANSITION) | Pending |
| TRANS-04 | Phase 74 (TRANSITION) | Pending |
| TRANS-05 | Phase 74 (TRANSITION) | Pending |
| TRANS-06 | Phase 74 (TRANSITION) | Pending |
| TRANS-07 | Phase 74 (TRANSITION) | Pending |
| XCUT-03 | Phase 75 (LINEAGE-BUMP) | Pending |
| XCUT-02 | Phase 76 (VALIDATE) | Pending |
| XCUT-04 | Phase 76 (VALIDATE) | Pending |

**Coverage:**
- v14.0 requirements: 26 total (FORM-01..05 + DUB-01..05 + IMG-01..06 + TRANS-01..07 + XCUT-01..04)
- Mapped to phases: 26/26 ✓
- Unmapped: 0

**Phase distribution:**
- Phase 70 (FOUNDATION-AUDIT): 1 req (XCUT-01)
- Phase 71 (FORM): 5 reqs (FORM-01..05)
- Phase 72 (DUB): 5 reqs (DUB-01..05)
- Phase 73 (IMG): 6 reqs (IMG-01..06)
- Phase 74 (TRANSITION): 7 reqs (TRANS-01..07)
- Phase 75 (LINEAGE-BUMP): 1 req (XCUT-03)
- Phase 76 (VALIDATE): 2 reqs (XCUT-02, XCUT-04)

---

*Requirements defined: 2026-07-09*
*Source: 用户 4-feature request + `.planning/research/v14-4track-upgrade/SUMMARY.md` (HIGH confidence)*
*Last updated: 2026-07-09 — Phase 71 (FORM) COMPLETE: all 5 FORM reqs satisfied (FORM-01 Plan 71-01, FORM-02 Plan 71-02, FORM-03 Plan 71-01, FORM-04 Plan 71-03, FORM-05 Plan 71-01). Phase 70 (1 req) + Phase 71 (5 reqs) = 6/26 v14.0 reqs satisfied. Phase 72 (DUB) ∥ Phase 73 (IMG) parallel next.*
