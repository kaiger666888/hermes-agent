# Domain Pitfalls — v14.0 kais-movie-pipeline 4-Track Upgrade

**Domain:** Adding FORM (form_factor parameterization) / DUB (CosyVoice + LTX native audio) / IMG (dreamina cli depth) / TRANSITION (3-layer) to the existing production-grade kais-movie-pipeline V8.6.
**Researched:** 2026-07-09
**Overall confidence:** HIGH (cross-verified against kais-movie-pipeline SKILL.md, existing refs, MILESTONES.md v1-v13 history, FEATURES.md/STACK.md sibling docs in this research directory, LTX capability matrix + workflow registry)

**Key context for readers:** kais-movie-pipeline is a 13-step AI short film pipeline currently hardened to vertical 9:16 (hardcoded in ~5 places), IndexTTS2 default TTS, dreamina cli 10-parallel validated, LTX-2.3 LiconMSR default video engine. v14.0 adds 4 features on top of this shipped, production-tested system. Most pitfalls below are **integration surprises** — the kind of regressions that pass unit tests but surface only at production scale.

---

## Severity Legend

- **BLOCKER** — will silently break production, corrupt data, or violate a milestone-level invariant (FOUND-08 / INFRA-04 / EVAL-06 / lineage L1-L6)
- **WARNING** — will cause measurable quality regression or operator friction; address in design phase
- **WATCH** — edge case; flag for spike validation but unlikely to block

---

## Cross-Cutting Pitfalls (apply to ALL 4 tracks)

### PITFALL X-1: SKILL.md lineage invalidation cascade — **BLOCKER · LINEAGE L1-L6 VIOLATION RISK**

**What goes wrong:** v14.0 explicitly breaks the v10.0 L1-L6 invariant ("kais-hermes-skills SKILL.md read-only"). PROJECT.md pre-authorizes this exception. BUT the exception is narrow — it covers **deliberate SKILL.md edits in v14.0 phase scope**, not accidental drift. Every SKILL.md touched by FORM (15 experts), DUB (audio_pipeline + aigc-platform), TRANSITION (cinematographer + editor + aigc-platform) must (a) regenerate `source_sha` (sha256 of new body), (b) update `transform_rule_id` (citing the v14.0 phase), (c) update `transform_timestamp`, then (d) propagate to `~/.hermes/agents/*.agent.yaml` by re-running the v13.0 P62 transform flow.

**Why it happens:** v13.0 P62 made `agent.yaml` files a **derived artifact** — they are never edited directly. If v14.0 edits SKILL.md without re-running the transform, `agent.yaml` becomes stale. The round-table executor / agent registry then loads personas that contradict the actual SKILL.md body (e.g., a SKILL.md with `form_factor` branching but an `agent.yaml` persona still saying "vertical 9:16 only"). Silent. No log, no warning.

**Consequences:**
- Agent registry loads stale persona → round table recommends form-agnostic shots using stale vertical-only instructions → quality regression indistinguishable from model failure
- Lineage audit (`jsonschema.Draft202012Validator`) fails at next milestone close → BLOCKER for v14.0 audit pass
- If curator self-evolution (EVAL-06, dry-run default) picks up the drift, it may generate diff patches against the stale `agent.yaml` → compound corruption

**Prevention:**
1. **Phase 0 (or first SKILL.md-touching phase)** must run a lineage impact assessment: enumerate every SKILL.md to be touched, list its current `source_sha`, mark for re-transform.
2. After all SKILL.md edits land, re-run the v13.0 P62 transform pipeline (`transform_skill_to_agent_yaml`) over the affected files.
3. Add a CI assertion: for each v14.0-touched SKILL.md, `agent.yaml` source_sha must equal SKILL.md body sha256. (`grep source_sha ~/.hermes/agents/*.agent.yaml | diff - <(sha256sum skills/.../SKILL.md)`)
4. The milestone audit must include a lineage-coverage row.

**Detection:** Audit script in milestone close-out: compare SKILL.md body hashes vs `agent.yaml.source_sha`. Any mismatch is a BLOCKER.

**Phase that should address:** **Phase 0** (lineage impact assessment) + final VALIDATE phase (audit).

---

### PITFALL X-2: "文档有规则,代码没执行" META-RULE regression — **BLOCKER · MOST-RECURRING BUG PATTERN**

**What goes wrong:** This is the #1 documented bug pattern in the existing pipeline (cited 4× in SKILL.md "What NOT to do"). Every rule written into SKILL.md / `references/*.md` that requires the subagent to DO something must ALSO be encoded as a `_SOME_INSTRUCTION` module-level constant injected into the phase module's `goal` f-string, with a test assertion that the keyword appears in `captured["goal"]`. If v14.0 adds rules like "form_factor MUST be propagated to shot_intent" or "transition_design.json MUST be emitted" only in SKILL.md, the rule silently won't fire.

**Why it happens:** Subagents see only the goal string passed to `delegate_task`. They never read SKILL.md at runtime. Documentation is advisory without code backing.

**Consequences (v14-specific scenarios):**
- FORM: 15 SKILL.md files get a `## Form Factor Adaptation` section, but if phase modules (P06 shot_breakdown, P11 video_render) don't inject `form_factor` into the goal, subagents keep generating vertical-only shot intent
- TRANSITION: `references/transition-design.md` defines `transition_method` + `visual_hook` schema, but if P09 goal doesn't mention them, cinematographer emits only the existing `next_shot_link: "shot_02"` (string, not structured object) → transition_design.json silently missing
- DUB: `voice_preset` per-character in `pipeline_state`, but P10 goal never asks for it → IndexTTS2 default voice used

**Prevention (enforce pattern from v5.0 + v6.0 P31):**
1. Every MUST/MUST NOT added to SKILL.md in v14.0 → extract as `_INSTRUCTION` constant in the relevant phase `.py`
2. Inject constant into `goal` via f-string in `GoalBuilder` (`[CONSTRAINTS]` segment, MUST-prefixed for `count_constraints()` to detect — see `references/prompt-design-standards.md`)
3. Test: `tests/test_<phase>.py::test_goal_includes_<keyword>` asserts keyword present in captured goal
4. CI gate: any PR that adds a new MUST to SKILL.md without a matching test assertion fails lint

**Detection:** Diff SKILL.md MUST count vs `count_constraints()` output per phase. Mismatch > 0 → WARNING.

**Phase that should address:** Each track-specific phase (FORM P70+, DUB P72+, IMG P71+, TRANSITION P73+).

---

### PITFALL X-3: Cross-repo PR coordination drift (hermes-agent ↔ kais-hermes-skills) — **WARNING**

**What goes wrong:** v14.0 explicitly revives the v9.0 cross-repo workflow (plan → `hermes-agent/.planning/`, code → `kais-hermes-skills/`). The two repos are not in lockstep — the planning doc may reference a SKILL.md section that doesn't yet exist in the code repo, or a code change may ship before the planning doc records the lineage impact.

**Why it happens:** PR review happens in two repos with different reviewers/CI. A merge in one repo doesn't trigger validation in the other.

**Consequences:**
- Audit at milestone close finds planning doc references a SKILL.md state that doesn't match HEAD
- `transform_rule_id` cites wrong phase number
- Cross-repo regression: a SKILL.md fix lands in kais-hermes-skills, but the corresponding `agent.yaml` re-transform in `~/.hermes/` is run against an older pull → drift

**Prevention:**
1. Pin both repos to specific commit shas at phase transition (record in `.planning/STATE.md`)
2. Define a single "v14.0 source-of-truth pointer": hermes-agent `.planning/STATE.md` records the kais-hermes-skills commit hash that the current phase touched
3. VALIDATE phase at end of milestone runs `git -C /data/workspace/kais-hermes-skills rev-parse HEAD` and asserts it matches STATE.md

**Detection:** Cross-repo link check in VALIDATE phase.

**Phase that should address:** VALIDATE (final) phase + each phase's transition.

---

### PITFALL X-4: EVAL-06 / curator self-evolution picks up v14.0 SKILL.md changes — **WARNING · EVAL-06**

**What goes wrong:** Curator (per v6.0 P32 + v13.0 P65) has a feedback-scan phase that proposes additive diffs to SKILL.md / refs based on operator feedback. v14.0 ships SKILL.md changes (FORM adaptation, DUB voice_preset, TRANSITION schema) on a timescale of weeks. If the curator live-tick (`--live` flag, default dry-run per EVAL-06) runs mid-milestone, it may (a) propose conflicting edits to the same sections being rewritten, or (b) emit a diff patch that references the OLD schema (`next_shot_link: "shot_02"` string) and reverts v14.0's structured-object migration.

**Why it happens:** Curator reads a SKILL.md snapshot at tick-time. If the v14.0 phase has landed FORM changes but not yet TRANSITION changes, the curator's diff may try to "fix" TRANSITION using feedback that pre-dates the schema migration.

**Consequences:**
- `apply_patch_transaction` (v6.0 P31, non-bypassable human-in-loop) catches most — but the diff queue fills with noise
- Sha256-chained audit log records a "correction" that's actually a regression
- Operator confusion: "did I approve this?"

**Prevention:**
1. **Keep EVAL-06 dry-run-first** — do NOT flip `--live` during v14.0 execution window. PROJECT.md confirms this is preserved.
2. During v14.0 SKILL.md-touching phases, run curator with explicit "skip these files" list (extended from `additive_only_check` rule)
3. Phase 0 should emit a v14.0 in-flight file registry shared with the curator

**Detection:** Curator pre-tick bias canary (v12.0 EVAL-03 + v13.0 P65) — extend with v14.0 form_factor / transition_design records.

**Phase that should address:** Phase 0 + each SKILL.md-touching phase.

---

### PITFALL X-5: INFRA-04 serial constraint violation via parallel transition engine calls — **BLOCKER · INFRA-04**

**What goes wrong:** PROJECT.md confirms INFRA-04 (serial execution, GLM 4-key rotation, `MAX_CONCURRENT_GL=1` per MEMORY.md `feedback-glm-overload-reduce-concurrency.md`) is preserved. The TRANSITION track's "generation layer" (Step C) contemplates routing to Kling / Runway / Pika / Hailuo / Vidu / Wan-FLF2V. If multiple transition calls fan out in parallel — even via different engines — they may share the same GLM call budget (transition routing decisions are LLM-made).

**Why it happens:** "Different engine = different rate limit" is intuitive but wrong: the LLM (GLM) is the orchestrator deciding routing, so even non-GLM generation engines (e.g., Wan-FLF2V local render) carry GLM overhead for prompt construction and selection.

**Consequences:**
- 5 parallel transition engine calls → 5 parallel GLM routing decisions → HTTP 429 → `delegate_task` silently returns empty content (the v9.0 P05 silent-failure symptom)
- Pipeline stall masquerades as transition engine failure

**Prevention:**
1. Keep ALL transition engine calls under the existing `glm_concurrent` semaphore (`pipeline/ratelimit.py`) — even non-GLM engines, because the routing decision itself is GLM
2. Do NOT introduce a separate semaphore for transition engines unless profiling proves it's safe (it isn't, given current GLM overload)
3. `Wan-FLF2V` local renders can fan out (they're GPU-bound not GLM-bound), but the routing decision before each render must be serialized

**Detection:** Existing 429 retry wrapper (`retry_on_429`, max_retries=3, 60s backoff) catches the symptom; root cause is concurrency > 1.

**Phase that should address:** TRANSITION generation-layer phase (P73+).

---

## FORM Track Pitfalls (form_factor parameterization)

### PITFALL F-1: 16:9 ≠ "just resize 9:16" — creative assumptions break silently — **BLOCKER**

**What goes wrong:** Multiple creative-side assumptions baked into the current vertical-only pipeline do not survive a width/height swap:

| Assumption | Current (9:16) | Broken when 16:9 | Why |
|---|---|---|---|
| **Power points** | (1/3, 1/4) / (2/3, 1/4) — higher eye-line | Falls back to horizontal rule-of-thirds (1/3, 1/3) — wrong for vertical subjects, and "wrong direction" framing regression | Per `cinematographer/references/vertical-screen-framing.md` §9:16 Power Points 修正 (load-bearing) |
| **Headroom** | 5-10% (FS/MS), tight | Horizontal headroom is 8-15%, loose | Same ref §Headroom |
| **Subtitle safe area** | Lower-center 65-85% / upper-center 15-35%, never face zone 35-65% | 16:9 face zone differs; subtitle placement must re-derive | Same ref §字幕 safe area 5 个区 |
| **Camera move priority** | Tilt + crane + vertical tracking preferred; horizontal pan forbidden | 16:9 prefers horizontal pan/tracking; vertical tilt de-emphasized | Same ref §Camera Move 修正 |
| **Shot-scale distribution** | MCU 30-40% (vertical bias) | 16:9 standard distribution: WS+FS higher share, MCU ~25% | `shot-grammar.md` §短剧 shot-scale 分布 |
| **Eye-trace** | Vertical ~27% tightening | Horizontal ~30% (per editor Murch Rule of Six) | `editor/SKILL.md` line 212 |

**Why it happens:** The cinematographer's `vertical-screen-framing.md` is explicitly **vertical-only** ("不适用于横屏 cinema"). There is no `horizontal-screen-framing.md` companion. A naive form_factor parameterization renders the cinematographer's reference stale when `form_factor = landscape_16_9`.

**Consequences:** Silent quality regression — landscape output looks "off" to a human cinematographer but passes all unit tests (because all unit tests are vertical-only). Detected only at operator UAT, wasting a render cycle.

**Prevention:**
1. **Author `references/horizontal-screen-framing.md`** as a new ref BEFORE parameterizing form_factor (FORM track Phase 1 deliverable)
2. Each form-aware SKILL.md needs a `## Form Factor Adaptation` section with explicit dual-branch rules (NOT a single "if landscape, swap X" — too brittle)
3. Cinematographer workflow step 3 (Composition per Shot) MUST branch on `form_factor` and load the right ref
4. Add eval prompts under `_eval/` with landscape variants — the current eval harness is vertical-only

**Detection:** Unit test asserting `form_factor` appears in cinematographer `goal`; integration test running one shot landscape, one portrait, checking different power_point values.

**Phase that should address:** FORM Phase 1 (refs authoring) + FORM Phase 2 (SKILL.md patches).

---

### PITFALL F-2: Step 14 platform slicing — changing MASTER form_factor breaks variant aspect ratios — **BLOCKER**

**What goes wrong:** Step 14 (v9.0 P38 SLICE) takes 1 master.mp4 and emits 7 platform variants (抖音竖屏/横屏、快手、B 站、小红书、视频号、红果) with 3 aspect ratios. The current contract assumes `master.mp4 = vertical 9:16` — vertical variants are lossless, horizontal variants (抖音横屏) are reframe-with-crop. If the master becomes landscape 16:9 (the new default per PROJECT.md), the reframe math inverts: horizontal variants are lossless, but vertical variants now need crop-and-scale that may cut off subjects framed for horizontal.

**Why it happens:** `references/platform-master-slicing.md` (v9.0, 346 lines) encodes reframe matrices assuming vertical master. Changing master form_factor without revisiting every cell silently produces bad crops.

**Consequences:**
- Vertical platform variants from landscape master: subject heads cropped if framed horizontal-rule-of-thirds (eyes at 1/3 from top → cropped to 1/4 in vertical reframe)
- Operator gets 7 variants, 4 of which are unwatchable — discovered only after a full 39-shot render (~64 min)
- Re-slicing from master is cheap, but re-rendering the master isn't

**Prevention:**
1. Step 14 contract must branch on `master_form_factor` × `target_platform_form_factor` (4 combinations: portrait→portrait, portrait→landscape, landscape→portrait, landscape→landscape) with explicit reframe rules per cell
2. Each of 7 platforms has a known expected form — re-derive per cell rather than assume
3. Add regression tests: 1 landscape master + 1 portrait master → assert all 7 variants have correct framing

**Detection:** Smoke test comparing variant aspect ratios vs platform specs.

**Phase that should address:** FORM Phase that touches Step 14.

---

### PITFALL F-3: LLM-driven experts produce form-agnostic output that doesn't fit either form_factor cleanly — **WARNING**

**What goes wrong:** Experts like `screenplay`, `hook_retention`, `creative_source` are largely form-agnostic — they emit story beats, emotion curves, hook patterns. But some of their outputs are implicitly form-bound: hook_retention's "first 3 seconds" hook assumes vertical phone viewing (vertical scroll-stop dynamic); for landscape YouTube/TV delivery, hook structure differs (longer establishing, different eye-leads). If we don't bifurcate, we get a "form-agnostic hook" that's actually a vertical hook mis-applied to landscape.

**Why it happens:** These experts were authored vertical-first (per v1 PROJECT.md: "Chinese-market 短剧 / 微电影 vertical 9:16"). Their `references/*.md` (e.g., `three-second-hooks.md`, `vertical-pacing.md`) encode vertical assumptions in the prose.

**Consequences:**
- Landscape output gets vertical-flavored hooks → lower YouTube completion rate
- Or worse: the experts refuse to produce landscape output ("I only know 短剧 vertical") and the pipeline falls back to LLM-generic defaults

**Prevention:**
1. Audit each of the 15 experts for form-implicit assumptions (FORM Phase 1 deliverable)
2. For experts that are truly form-agnostic (e.g., `style_genome`, `creative_source`), document that explicitly in SKILL.md
3. For form-bound experts (e.g., `hook_retention`, `cinematographer`), add form-specific guidance in SKILL.md
4. Do NOT try to make every expert form-aware — most are form-agnostic by design, and forcing form_factor into them is scope creep

**Detection:** Per-expert audit matrix.

**Phase that should address:** FORM Phase 1 (audit) + Phase 2 (per-expert patches).

---

### PITFALL F-4: LTX-MSR render params — 16:9 default ≠ "currently works for 16:9" — **WATCH**

**What goes wrong:** PROJECT.md and STACK.md note that `ltx_msr_batch_render.py` currently hardcodes `width=1280 height=704` (16:9). So 16:9 "already works." But 9:16 needs `width=704 height=1280` — and the conditioning frame count `MSR_FC=17` is independent of aspect ratio, BUT the post-generation trim formula `total_frames = duration_sec × 24 + msr_fc` may produce differently-shaped artifacts at 9:16 (vertical pixels are heavier in some codecs). Not a blocker, but flag for spike.

**Why it happens:** The 16:9 path is validated (39-shot Volvo batch). The 9:16 path through LTX-2.3 has been used (silly-cat-30s session 2026-07-04), but not in a full 13-step pipeline run.

**Consequences:** Minor — likely just a render-time / VRAM differential.

**Prevention:** Spike: one full 9:16 render with all v14.0 changes applied, before opening milestone audit.

**Detection:** Compare VRAM/latency vs 16:9 baseline.

**Phase that should address:** FORM validation phase.

---

## DUB Track Pitfalls (CosyVoice default + LTX 2.3 native audio coordination)

### PITFALL D-1: CosyVoice + LTX 2.3 native audio BOTH enabled → doubled audio / phase issues / lip-sync mismatch — **BLOCKER**

**What goes wrong:** Per PROJECT.md, the intended division is: **LTX native** for synchronized dialogue + lip-sync (existing path, line 566+); **CosyVoice** for post-production TTS overlay (旁白 / voiceover / emotion prosody 重场景). But this division is policy, not enforcement. If both fire for the same shot:
- Dialogue gets rendered twice (once native in LTX prompt, once CosyVoice overlay) → phase cancellation / echo
- Lip-sync desync: LTX lip movement matches native audio; CosyVoice overlay has slightly different timing → "bad dub" effect
- BGM mixing (P12) doesn't know which audio is authoritative → wrong ducking target

**Why it happens:** No schema-level enforcement. The pipeline currently has `audio_cue` field in `shot_intent` and `tts_engine` field (new in v14.0 per PROJECT.md). A shot with `audio_cue.dialogue = "..."` AND `tts_engine = cosyvoice` is valid by schema but wrong by policy.

**Consequences:** Ruined episode. The operator hears doubled dialogue. Re-rendering P11 (native audio) is ~98s/shot × 39 shots = 64 min wasted.

**Prevention:**
1. Define `tts_engine` selection rule as data: `if shot.has_dialogue AND shot.lip_sync_required → tts_engine = ltx_native`; `if shot.is_voiceover OR shot.no_on_screen_character → tts_engine = cosyvoice`; `indextts2_fallback` only if CosyVoice fails
2. Schema validator rejects `tts_engine = cosyvoice` for shots with `lip_sync_required = true`
3. P12 composition phase (`references/p12-composition-workflow.md`) must check `tts_engine` per-shot and route to the right audio source
4. Add unit test: assert no shot has `ltx_native_dialogue AND cosyvoice_overlay` simultaneously

**Detection:** P10 pre-flight check before LTX render.

**Phase that should address:** DUB integration phase.

---

### PITFALL D-2: CosyVoice 2 voice cloning needs reference audio per character — operator-action blocker — **BLOCKER (OPERATOR-ACTION)**

**What goes wrong:** CosyVoice 2 zero-shot voice cloning requires a 3-10 second reference audio clip per character voice. Without it, CosyVoice falls back to a generic preset voice (defeating the purpose of cloning). The pipeline currently has `voice_preset` (IndexTTS2 emotion slider value) — this is NOT a reference audio path.

**Why it happens:** IndexTTS2 used pre-baked emotion presets (`sad`/`calm`/`happy`/`melancholic`) — no per-character audio. CosyVoice 2 changes the contract: each character in `character_bible.json` needs a `voice_clone_reference_wav` field pointing to a recorded sample.

**Consequences:**
- First episode run after v14.0 ship → CosyVoice has no reference wavs → falls back to generic voice → all characters sound identical → operator reports "voice regression"
- Operator has to source 3-10s clean samples for every character (often 5-10 per episode) BEFORE running pipeline — unblocking dependency

**Prevention:**
1. **MUST be documented as an operator-action-handoff** (like v9.0's V9-FUTURE-01/02 platform API keys + LTX GPU testing). v14.0 ships the schema (`character_bible.voice_clone_reference_wav`), operator sources the wavs.
2. `templates/tts_batch.py` MUST fail fast with explicit error: `"voice_clone_reference_wav missing for character_id=X. Operator action: provide 3-10s clean sample at <path>. See DUB phase operator-action checklist."` (NOT a silent fallback)
3. Voice preset migration (IndexTTS2 emotion → CosyVoice 2 instruct mode) MUST be a documented mapping table, not an opaque runtime conversion. Operator can audit.
4. PROJECT.md Constraints already acknowledge "新增 CosyVoice 集成" — must explicitly call out the per-character wav dependency

**Detection:** Pre-flight checklist in P10.

**Phase that should address:** DUB phase (with operator-handoff documentation in SUMMARY).

---

### PITFALL D-3: ComfyUI CosyVoice custom node dependency hell — community-maintained, breaking changes, abandoned repos — **WARNING**

**What goes wrong:** STACK.md picks `filliptm/ComfyUI_FL-CosyVoice3` as the integration node. ComfyUI custom nodes are community-maintained and frequently:
- Break on ComfyUI core upgrades (the existing `comfyui-indextts2-setup.md` documents 9 dependency-install steps — CosyVoice likely similar)
- Get abandoned (the existing pipeline has documented abandoned-node history: `LTXVGemmaCLIPModelLoader` failed on FP8 Gemma, `DualCLIPLoader` is the working alternative — per SKILL.md line 523)
- Have hidden hard-fork dependencies (e.g., require specific `comfyui-primary` docker image version)

**Why it happens:** The ComfyUI ecosystem has no semantic versioning contract. A node update can change its API surface silently.

**Consequences:**
- v14.0 ships → 2 months later ComfyUI core updates → CosyVoice node breaks → P10 TTS silently fails → pipeline stalls at P10 gate
- Debugging requires deep ComfyUI internals knowledge (existing pipeline has multiple `docker restart comfyui-primary` + dependency fix cycles documented)

**Prevention:**
1. **Pin the ComfyUI docker image + custom node commit hash** in the operator setup doc (mirror `comfyui-indextts2-setup.md`)
2. Provide a fallback path: `tts_engine = indextts2_fallback` MUST trigger automatically if CosyVoice node returns errors on healthcheck (`/object_info` endpoint)
3. Add a "CosyVoice node healthcheck" step in pre-flight: GET `http://localhost:8188/object_info/AIIA_IndexTTS2_TTS` (existing) + new `GET .../FLCosyVoice3Instruct2` — if missing, log warning + fall back to IndexTTS2
4. **SKILL.md pitfall addition:** "CosyUI CosyVoice node pinning" parallel to the existing "ComfyUI source patches do NOT hot-reload" pitfall (line 522)

**Detection:** Pre-flight healthcheck before first CosyVoice submission.

**Phase that should address:** DUB phase (`references/comfyui-cosyvoice-setup.md` authoring).

---

### PITFALL D-4: Emotion control mismatch — IndexTTS2 sliders do NOT map cleanly to CosyVoice 2 instruct2 modes — **WARNING**

**What goes wrong:** STACK.md asserts a clean mapping: IndexTTS2 `sad/calm/happy/melancholic` 8-emotion → CosyVoice 2 `instruct mode` text instructions (`[ sadness=0.3 ]`, `[ calm=0.2 ]`). Reality is messier:

| IndexTTS2 emotion slider | CosyVoice 2 equivalent | Mapping fidelity |
|---|---|---|
| `sad` (0.0-1.0) | `[ sadness=X ]` text instruction | HIGH — direct |
| `calm` | `[ calm=X ]` | HIGH |
| `happy` | `[ happy=X ]` | MEDIUM — CosyVoice 2 "happy" is more subdued; needs prosody hint |
| `melancholic` | No direct equivalent — needs `[ sadness=0.5, calm=0.3 ]` composite | LOW — lossy |
| `angry` (if used) | `[ anger=X ]` but with strong distortion risk | LOW |

**Why it happens:** CosyVoice 2's instruct mode is text-prompt-based; IndexTTS2's is slider-based. Continuous slider → discrete text token is inherently lossy.

**Consequences:** Voice character shifts subtly across migration — operator may report "character sounds different." Hard to debug without A/B samples.

**Prevention:**
1. Document the mapping table explicitly (STACK.md has started this — finish it)
2. For each IndexTTS2 preset in active use, generate an A/B comparison sample (IndexTTS2 vs CosyVoice 2 mapped) for operator sign-off BEFORE defaulting CosyVoice
3. Keep IndexTTS2 fallback available for cases where the mapping is too lossy (`melancholic` especially)
4. Project reconstruction (re-running an old episode with v14.0) — voice will differ; document this as a known breaking change in `VERSION.json`

**Detection:** A/B listening test.

**Phase that should address:** DUB phase validation.

---

### PITFALL D-5: TTS batch submission to ComfyUI :8188 contends with LTX-MSR video batch — GPU contention crashes ComfyUI — **WARNING**

**What goes wrong:** P10 (TTS) and P11 (video render) both submit to ComfyUI :8188. The existing GLM rate limit (`MAX_CONCURRENT_GL=1`) controls LLM concurrency, but **GPU concurrency is different**. P11 with `parallel_shots` set + P10 firing TTS in parallel can exceed VRAM (existing `ltx_msr` ~23GB + CosyVoice ~3-5GB + ACE-Step BGM ~6GB > 24GB on RTX 3090/4090).

**Why it happens:** The pipeline DAG has P10 → P11 (sequential at phase level), but `templates/ltx_msr_batch_render.py` and `templates/tts_batch.py` are designed to run in background (`run_in_background=True`). An operator may run them concurrently to save wall time, not realizing the GPU budget.

**Consequences:**
- CUDA OOM → ComfyUI crash → both batches fail mid-flight
- Recovery requires `docker restart comfyui-primary` + re-submit (existing pitfall, line 522)

**Prevention:**
1. **Document hard rule:** P10 and P11 MUST NOT run concurrently on the same ComfyUI instance. Sequence them.
2. Add GPU semaphore at the orchestrator level: `MAX_CONCURRENT_GPU_JOBS=1` config
3. `templates/tts_batch.py` should refuse to start if `ltx_msr_batch_render.py` lockfile present (`/tmp/kais_comfyui_gpu.lock`)
4. Consider separate ComfyUI instances for TTS vs video (longer-term — VRAM bifurcation)

**Detection:** Pre-flight GPU free-memory check; refuse to submit if `nvidia-smi` shows < 3GB free.

**Phase that should address:** DUB phase + IMG (templates) phase.

---

### PITFALL D-6: Voice preset library migration without backwards-compat breaks existing project reconstruction — **WARNING**

**What goes wrong:** `pipeline_state.episode_id.voice_preset` is a v14.0 new field. Old projects (Volvo, silly-cat-30s, 星渊纪) don't have it. Re-opening an old project post-v14.0 either (a) errors on missing field, or (b) silently defaults to CosyVoice generic voice, breaking reconstruction fidelity.

**Why it happens:** Pipeline state schema migration. Forward-compat is straightforward; backward-compat needs explicit handling.

**Consequences:**
- Old projects can't be re-rendered (re-opening volvo and re-running P10 → CosyVoice generic voice → character voice changes)
- Or worse: re-render produces different audio → canvas node mismatch → broken provenance

**Prevention:**
1. `voice_preset` MUST be nullable + have explicit default `tts_engine = indextts2_fallback` for pre-v14.0 projects
2. Project archival format (`VERSION.json`) records `tts_engine_at_creation`; re-opening preserves that engine
3. Migration script: scan existing `pipeline-state.json` files, add `tts_engine = "indextts2_fallback"` (or `ltx_native` for shots with `has_dialogue=true`), record in audit log

**Detection:** Schema validator with versioned defaults.

**Phase that should address:** DUB phase + VALIDATE.

---

## IMG Track Pitfalls (dreamina cli depth upgrade)

### PITFALL I-1: Vision-verify as mandatory gate becomes a throughput bottleneck — **WARNING**

**What goes wrong:** PROJECT.md escalates the vision-verify pitfall (line 561: "dreamina 生成内容可能完全错误") to a MANDATORY gate: "未 verify 不允许 upload 到 ComfyUI." This is correct for quality but introduces a serial bottleneck: every dreamina image must be vision-analyzed before next step. At 10-parallel dreamina + 1-serial vision-verify, the gate serializes the whole batch.

**Why it happens:** Vision-verify is a separate GLM-4.6V call (per STACK.md). It's not free: ~2-5s per image + GLM rate limit. 39 reference images × 3s = ~2 min added serially; 213-shot sci-fi epic × 5 refs/shot × 3s = ~53 min.

**Consequences:**
- Pipeline wall time increases 20-50% for image-heavy projects
- Operators may disable the gate to hit deadlines → unverified references → poisoned batch (the original pitfall re-emerges)

**Prevention:**
1. Vision-verify MUST be parallel-capable: batch N images per GLM-4.6V call (multi-image message) — 4-8 images per call cuts overhead 4-8x
2. **Confidence-gated enforcement:** vision-verify flags "low confidence" cases (ambiguous response, content mismatch > 30%) for human review; high-confidence passes auto
3. The gate is "mandatory" for shots going to P11 (video render), but **advisory** for early-iteration reference images (where operator will review on canvas anyway)
4. Cache vision-verify results (sha256-keyed) so re-running same image doesn't re-verify

**Detection:** Wall-time profiling.

**Phase that should address:** IMG phase (orchestrator design).

---

### PITFALL I-2: Vision-verify false positives — mandatory gate becomes a friction point — **WARNING**

**What goes wrong:** Vision analysis is **known unreliable** for image content assessment (per existing SKILL.md line 574, validated 2026-06-28): "vision_analyze on extracted video frames produces contradictory, reasoning-based (not perception-based) descriptions. The same frame analyzed twice with different questions yields opposite conclusions." Although that finding is about video frames, the same unreliability applies to dreamina images. A mandatory gate that's 20% wrong becomes 20% friction.

**Why it happens:** Vision models reason about content rather than perceive it. Asymmetric errors: false negative ("this is a hand-holding-phone image, not a baby in car seat" when it IS a baby) wastes a re-generation cycle.

**Consequences:**
- 1 in 5 reference images flagged as "wrong content" when actually correct → dreamina re-generation → wasted parallel slot + ~2.2s/image
- Operator loses trust in the gate, disables it

**Prevention:**
1. Vision-verify should return content description + confidence + structured fields (subject_count, scene_type), NOT a binary "correct/wrong" verdict
2. Comparison logic: vision-verify output vs prompt intent (parsed) — if `prompt_intent.subject = "baby in car seat"` AND `vision_report.subject = "baby in car seat"` → PASS; only flag mismatch
3. **Never auto-reject based on vision alone** — surface to operator with side-by-side (vision description + actual image thumbnail on canvas) for human review
4. Mandatory gate = "vision-verify has RUN", not "vision-verify has APPROVED". The artifact is the audit trail; the decision is operator's.

**Detection:** Vision-verify disagreement rate; operator UAT.

**Phase that should address:** IMG phase + VALIDATE.

---

### PITFALL I-3: Async retry vs sync queue — pipeline_state write before async retry completes → manual backfill needed — **BLOCKER**

**What goes wrong:** STACK.md recommends `tenacity==9.1.4` (already pinned) for auto-retry. But `tenacity`'s retry is sync (or async-with-event-loop). If dreamina submission is fire-and-forget (non-blocking `subprocess.Popen` per existing `dreamina_gen_image.py` pattern), retry-on-failure happens AFTER the pipeline_state has already moved on. The failed task is recorded as "submitted" not "completed", and downstream phases (P11 video render) consume a missing reference image.

**Why it happens:** The existing pattern (line 521) is "non-blocking submission + batch poll". `tenacity` wraps a function call — but if you don't `await`/join the result, the retry doesn't propagate.

**Consequences:**
- P11 video render fails because ref image is missing → silent retry of LTX render → ComfyUI cache returns phantom success (existing pitfall, line 628)
- Canvas offline backfill needed (existing procedure, line 548, validated 2026-06-30)
- Manual backfill: "after generating visual assets, update pipeline-state.json immediately" (existing pitfall, line 619)

**Prevention:**
1. Dreamina orchestrator MUST use a sync queue model: submit N non-blocking, then BLOCK on poll-all-before-deadline. If any fails, retry that one (with `tenacity`) BEFORE returning control to pipeline.
2. pipeline_state write happens AFTER all retries succeed or exhausted — never before
3. If retry exhausted, write failure record (not silent skip) → P11 refuses to render that shot with explicit error: "reference image generation failed; operator action required"
4. Test: simulate dreamina 5xx response on 1 of 10 parallel submissions; assert orchestrator retries + records final state correctly

**Detection:** Failure-injection integration test.

**Phase that should address:** IMG phase (`plugins/kais_aigc/dreamina_orchestrator.py` design).

---

### PITFALL I-4: RHD/LHD bug mitigation — prompt template alone doesn't fix it (vision-verify + retry is mandatory) — **WARNING**

**What goes wrong:** PROJECT.md escalates line 570 RHD/LHD mitigation to "prompt 模板 + verify-retry 循环." But the existing pitfall (line 570) is explicit: "even an explicit prompt like 'left-hand drive, steering wheel on the left side' frequently produces a right-hand drive image." Prompting alone has already been validated as insufficient.

**Why it happens:** dreamina's training data biases. The model has strong prior toward RHD regardless of prompt strength.

**Consequences:** Without vision-verify-driven retry, RHD output slips through, poisons the LTX batch (Volvo V2 lesson, line 570).

**Prevention:**
1. The mitigation MUST be: (1) prompt with LHD emphasis + (2) vision-verify with explicit "left-hand drive? yes/no" question + (3) retry with `image2image` from a confirmed LHD reference if vision says RHD
2. Retry budget: 3 attempts (validated empirically — usually 2nd attempt succeeds)
3. If 3 attempts all produce RHD, flag for operator (give up on auto-fix)
4. This pattern (prompt + vision-verify + image2image retry) generalizes to other dreamina unreliability cases (gender, age, scene type)

**Detection:** RHD/LHD audit on first batch of any new project.

**Phase that should address:** IMG phase (orchestrator) + SKILL.md pitfall update.

---

### PITFALL I-5: Production-grade SLA tracking — adding observability adds GLM overhead — **WATCH**

**What goes wrong:** PROJECT.md asks for "latency / success rate / cost / quota per task" SLA tracking. Naive implementation: each metric emits a GLM log call → GLM rate limit violation (INFRA-04). Metrics collection MUST stay sync/local (per v13.0 P67 INFRA-04 preservation).

**Why it happens:** The v13.0 P67 observability backend (MetricsBuffer ring buffer) is the model — sync `@contextmanager`, no `asyncio.gather`. v14.0 IMG SLA tracking must follow same pattern.

**Consequences:**
- Naive `logger.info(per_call)` is fine (filtered log)
- Naive "emit event to GLM aggregator" is NOT fine — adds N GLM calls per dreamina submission

**Prevention:**
1. SLA tracking MUST write to local JSONL/SQLite, not GLM
2. Aggregate to dashboard only at phase-end (one GLM call summarizing)
3. Follow v13.0 P67 pattern exactly: `MetricsBuffer` ring buffer + per-phase summary

**Detection:** INFRA-04 audit at VALIDATE.

**Phase that should address:** IMG phase.

---

### PITFALL I-6: image2image workflow standardization — different reference image counts need different retry strategies — **WATCH**

**What goes wrong:** PROJECT.md asks for "image2image workflow 标准化: reference image → output 全链路 (含 prompt 模板 + reference 数量 + strength 参数)." Different shot types need different reference counts:
- L1 character turnaround: 1 reference (the turnaround sheet)
- L2 scene fitting: 2 references (character + scene)
- Multi-angle scene: 5 references (top-down + 4 views)
- Vehicle ref: 1 reference

If retry strategy is "always retry once on failure," a 5-reference image2image is far more likely to fail than 1-reference — wasting retry budget unevenly.

**Why it happens:** Reference count scales complexity non-linearly. Dreamina's tolerance for N references degrades around 4-5.

**Consequences:** Uneven failure rates; hard to set sane defaults.

**Prevention:**
1. Retry budget per shot-type: 1-ref shots → 2 retries max; 5-ref shots → 4 retries max
2. Strength parameter (`strength=0.4-0.7`) tuned per shot-type
3. Document explicitly in `references/dreamina-image2image-workflow.md`

**Detection:** Failure-rate stratified by ref count.

**Phase that should address:** IMG phase.

---

## TRANSITION Track Pitfalls (3-layer creative + data + generation)

### PITFALL T-1: LTX-MSR ICLoRA is identity preservation, NOT first/last frame transition — **CRITICAL ASSUMPTION CORRECTION (PARTIAL)**

**What PROJECT.md says:** "Step A — Verify LTX-MSR first/last frame capability (预期 NO, ICLoRA 是 identity conditioning)."

**What research found (HIGH confidence):** The assumption is **partially wrong**. LTX-2.3 has TWO ORTHOGONAL capabilities:

| Capability | Workflow | Node | Purpose |
|---|---|---|---|
| **Identity preservation** (ICLoRA) | `ltx/msr` (LiconMSR) | `LiconMSR` + `LTXAddVideoICLoRAGuide` + `LTXICLoRALoaderModelOnly` | Cross-shot character identity (up to 5 refs) |
| **First/Last frame conditioning** (FLF) | `ltx/fflf` + `ltx/singularityFFLF` | `LTXVImgToVideoInplace` + `LTXVAddGuide` (fflf) or 76-node mega-pipeline (singularityFFLF) | Define explicit start + end frames; transitions |

**Critical limitation (verified against `references/ltx-capability-matrix.md`):** These are SEPARATE workflows. You can EITHER have multi-reference identity OR first/last frame conditioning — NOT BOTH simultaneously. There is no "MSR+FFLF combined" workflow.

**Consequences for TRANSITION track:**
- For transition shots that need cross-shot character consistency → must use MSR (existing path, no transition-specific conditioning)
- For transition shots that need explicit "frame A → frame B" interpolation → must use FLF (NO character identity from previous shot — drift risk)
- Cannot have both → trade-off per shot

**Pitfall:** If TRANSITION track design assumes "LTX can do both," the design fails at implementation.

**Prevention:**
1. Phase A (verify) MUST verify the no-combined-workflow assumption by checking ComfyUI workflow registry (`/history` for `singularityFFLF`) and LTX-Video GitHub
2. Per-transition routing rule: `IF transition needs identity continuity → MSR + post-production match-cut`; `IF transition needs frame-interpolation → FLF + accept identity drift risk OR use post-production match-cut`
3. **Generation layer (Step C) is RESEARCH scope per PROJECT.md**, not implementation — the finding feeds into the design doc, not into immediate pipeline code

**Detection:** ComfyUI workflow JSON inspection.

**Phase that should address:** TRANSITION research/design phase (likely Phase 73).

---

### PITFALL T-2: Cinematographer vs editor ownership conflict for transition design — **BLOCKER · FOUND-08 RISK**

**What goes wrong:** Both cinematographer AND editor currently own parts of transition design:
- **cinematographer** owns E-Konte Layer 5 `cut_transition_type: hard_cut/dissolve/wipe/fade` + `next_shot_link` field (`e-konte-format.md` line 125) — this is **creative intent** at shot-design time (Step 6/8/9)
- **editor** owns "Transition Design" workflow step 7 — this is **post-production cutting decision** (Step 13) per editor SKILL.md line 197: "Transition Design — Determine transition type and duration between shots; match cut 优先在场景转换处"

PROJECT.md proposes expanding cinematographer ownership to include `transition_method` (montage cut / match-cut via shared object / etc.) + `visual_hook` + `camera_continuity` — creative-layer fields. This expands cinematographer's territory into space that editor also claims.

**Why it happens:** The current ownership line is blurry. Editor's "transition design" step 7 operates on cinematographer's `cut_transition_type` field — it's downstream consumption, not independent design. But PROJECT.md's new fields (`visual_hook`, `camera_continuity`) could be read as either creative intent (cinematographer) or post-production notes (editor).

**Consequences:**
- FOUND-08 violation risk: if we introduce a new `transition_designer` expert_id, that's a forbidden expert change (deprecation of storyboard_designer / scene_builder / performer was irreversible per Phase 17 promise; new additions are equally restricted)
- Scope creep: editor SKILL.md would need updates too (changing another expert's territory → broader SKILL.md touches → lineage impact cascade)
- Schema confusion: if `transition_design.json` is emitted by cinematographer, editor may overwrite or ignore

**Prevention:**
1. **Do NOT create a new `transition_designer` expert** (FOUND-08 violation). The creative layer expands `cinematographer` (specifically `composition_lock` sub-task / E-Konte Layer 5 extension), and the post-production layer stays in `editor`. This is the existing pattern.
2. **Explicit ownership table** in `references/transition-design.md`:
   - Creative intent fields (`transition_method`, `visual_hook`, `camera_continuity`): **cinematographer** (Step 6/8/9)
   - Post-production execution fields (`cut_duration_frames`, `dissolve_curve`, `match_cut_alignment_point`): **editor** (Step 13)
3. Schema: `transition_design.json` is **emitted by cinematographer at Step 9**, **consumed by editor at Step 13** (additive, like `shot_intent.json` flow). Editor does NOT modify, only annotates execution notes.
4. Update both `cinematographer/SKILL.md` and `editor/SKILL.md` in the same phase to reflect the explicit split
5. Test: continuity_auditor must check both layers (cinematographer intent + editor execution) — but report separately

**Detection:** Cross-expert field-ownership audit at VALIDATE.

**Phase that should address:** TRANSITION design phase + careful SKILL.md patches.

---

### PITFALL T-3: Schema migration `next_shot_link: "shot_02"` (string) → structured object breaks existing pipeline — **BLOCKER**

**What goes wrong:** E-Konte Layer 5 currently has `next_shot_link: "shot_02"` as a string id (cinematographer/references/e-konte-format.md line 333). PROJECT.md asks: "扩展 `next_shot_link` 为结构化对象（不是 string id）". Any existing pipeline-state.json (Volvo, silly-cat, 星渊纪) has the string form. Migration is breaking.

**Why it happens:** Schema evolution. Forward-only migration would invalidate all old projects' reconstruction.

**Consequences:**
- `pipeline_state.json` from pre-v14.0 projects → `next_shot_link` is string → new code expects object → `KeyError` or silent skip
- Canvas nodes referencing old shot_ids via string link → orphaned
- Continuity_auditor, editor workflow step 7 — all consume this field → all need migration

**Prevention:**
1. **Backward-compat reader:** code reads `next_shot_link` — if string, coerce to `{"shot_id": value, "transition_method": "hard_cut", "visual_hook": null, ...}` (defaults); if dict, use directly
2. **Migration script** (Phase 0 of TRANSITION): scan all `pipeline-state.json` in `runs/*/`, upgrade string→dict with defaults, write `migration_v14_transition.json` audit log
3. Writer always emits the dict form
4. Test: pre-migration `pipeline-state.json` fixture → reader returns dict → existing consumers don't crash

**Detection:** CI schema-validator with v1 + v14 fixtures.

**Phase that should address:** TRANSITION Phase 1 (schema migration).

---

### PITFALL T-4: transition_design.json as new first-class asset — must be registered in Phase 38 slots or canvas won't render it — **BLOCKER**

**What goes wrong:** The pipeline has an asset-bus schema (`references/asset-bus-schema.md`) where each phase has declared output slots (Phase 38 v9.0 SLICE was the last to register new slots). A new `transition_design.json` first-class asset must be registered in:
1. Asset bus slot registry (`ASSET_SCHEMA`)
2. `_PHASE_OUTPUT_MAP` in `canvas_sync.py` (per v9.0 commit `da87ddc` pattern)
3. Phase 38 slot lifecycle (write → read → append)
4. v2 canvas zod enum (`_V2_VALID_NODE_TYPES`) — if it's a new node type

If any of these registrations is missed, the asset exists on disk but is invisible:
- Canvas sync silently fails (existing pitfall: `try/except` swallow-all, line 563/587)
- Infinite canvas shows 0 transition nodes
- Operator: "where's my transition design?"

**Why it happens:** Asset bus + canvas + schema validation are 3 separate systems. Adding a new asset type requires touching all 3.

**Consequences:** Invisible work — silent failure is the documented #1 canvas pitfall (4 separate entries in SKILL.md).

**Prevention:**
1. **Discovery first:** in TRANSITION Phase 1, audit all 3 registration points (asset bus, canvas sync, zod enum)
2. Define `transition_design.json` schema explicitly (emit from P09, consume by P13 editor)
3. Add to `_PHASE_OUTPUT_MAP["p09"]` list of tracked output keys
4. If a new canvas node type is needed (`type: "transition"`), update `_V2_VALID_NODE_TYPES` AND `flowGraphToCanvas()` AND `CanvasNodeType` TypeScript union (existing pattern, line 613)
5. Test: end-to-end canvas smoke (P09 emits transition_design.json → canvas shows transition node)

**Detection:** Canvas sync integration test.

**Phase that should address:** TRANSITION implementation phase.

---

### PITFALL T-5: Transition engine API rate limits / quota — Kling / Runway / Pika free-tier limits — **WARNING (OPERATOR-ACTION)**

**What goes wrong:** TRANSITION generation layer Step B surveys Kling / Runway Gen-3 / Pika / Hailuo / Vidu / Wan2.2 variants. Most have aggressive free-tier limits:
- **Kling:** free tier ~6 renders/day on klingai.com (region-restricted; CN access via different path)
- **Runway Gen-3:** $0.05/second of generated video — 5s transition × 30 transitions = $7.50 per episode — sustainable for one episode, expensive for 30-episode 短剧 series
- **Pika:** free tier ~30 renders/day (via fal.ai relay, additional hop)
- **Hailuo 02:** free tier exists but rate-limited
- **Vidu:** free tier in CN
- **Wan2.2 14B FLF2V:** local ComfyUI (already in stack per STACK.md) — unlimited but GPU-bound

**Why it happens:** Transition generation is fundamentally expensive — each transition shot is a full video generation.

**Consequences:**
- v14.0 design contemplates multi-engine routing, but if operator hasn't provisioned API keys (operator-action-handoff per v9.0 pattern), routing falls back to post-production ffmpeg dissolve/wipe/fade → entire generation layer unused
- Cost surprise: $200+ for a 30-episode series if Runway default

**Prevention:**
1. **Wan2.2 14B FLF2V as DEFAULT** (local ComfyUI, no API key, no per-render cost) per STACK.md recommendation
2. Cloud engines (Kling/Runway/Hailuo/Vidu) are **opt-in**, require operator to set API key + budget
3. Routing rule: `IF wan_flf2v_succeeds → use it`; `ELSE IF operator_api_key_present AND budget_remaining → use cloud engine per preference`; `ELSE → post-production fallback`
4. Document as **operator-action-handoff** in v14.0 SUMMARY (parallel to v9.0 V9-FUTURE-01/02)
5. Never make cloud engines a hard dependency — generation layer must degrade gracefully to post-production

**Detection:** Pre-flight API key check; operator cost report per episode.

**Phase that should address:** TRANSITION generation-layer phase + operator-action-handoff doc.

---

### PITFALL T-6: Cross-engine routing complexity — LTX-MSR for some transitions, FLF2V for others, post-production for the rest — **WARNING**

**What goes wrong:** Three generation paths (MSR for identity, FLF2V for frame-interp, post-production ffmpeg for simple dissolve) × N transitions per episode × cross-engine state tracking = combinatorial complexity. Easy to lose track of which transition went where.

**Why it happens:** Each engine has different I/O contracts (MSR wants ref1-ref5, FLF2V wants firstFrame+lastFrame, post-prod wants cut+transition_type). Per-transition routing decision is itself an LLM call (GLM rate limit risk, INFRA-04).

**Consequences:**
- Canvas shows transitions from 3 different engines with inconsistent style → operator confusion
- Provenance tracking breaks: "where did this transition come from?"
- Retry/failure recovery is engine-specific — generic retry doesn't work

**Prevention:**
1. `transition_design.json` MUST record `engine` + `engine_call_params` per transition (provenance field)
2. Per-transition routing rule (extending `video-engine-comparison.md §Selection Rules`) is **declarative**, not LLM-decided at runtime: `IF transition_method == "match-cut via shared object" AND shared_object_visible_in_both_frames → MSR`; `IF transition_method == "frame-interpolation" → FLF2V`; `ELSE → post-production`
3. The routing rule is encoded in a `_ROUTING_RULE` constant (per META-RULE X-2) so the subagent sees it
4. Engine clients share a common interface (Protocol class) for submit/poll/result

**Detection:** Routing-rule audit; provenance field validation.

**Phase that should address:** TRANSITION generation phase.

---

### PITFALL T-7: Voice continuity across transitions — TTS engine switching mid-transition breaks character voice — **WARNING**

**What goes wrong:** If transition A uses LTX native audio (synced dialogue) and transition B (immediately after) uses CosyVoice overlay (voiceover), the character's voice character may shift. Cross-engine voice continuity is hard.

**Why it happens:** Voice cloning reference audio is per-character (PITFALL D-2), but each engine (LTX native vs CosyVoice) processes it differently.

**Consequences:** Operator: "the character sounds like two different people across the cut."

**Prevention:**
1. Within a scene, ALL dialogue shots use the same `tts_engine` (no mid-scene switching)
2. Voice continuity check in continuity_auditor (existing 4-dimension audit extended to 5): face_identity, wardrobe_figure, color_temperature, scene_environment, **voice_identity**
3. Cross-engine voice A/B test before milestone close (operator UAT)

**Detection:** continuity_auditor 5-dim check.

**Phase that should address:** TRANSITION + DUB coordination phase.

---

### PITFALL T-8: Transition design too creative — cinematographer designs intent that no engine can execute — **WARNING**

**What goes wrong:** Creative-layer fields (`visual_hook: "the teacup shatters into a thousand mirrored fragments, each reflecting a different memory"` — an extreme example) may have no engine capable of rendering it. Even top-tier Runway Gen-3 / Sora 2 would struggle; LTX-2.3 definitely cannot.

**Why it happens:** Cinematographer (LLM) is creative without execution-awareness. No constraint check between intent and engine capability.

**Consequences:**
- Generation layer fails silently or produces garbage
- Operator frustration: "the design was beautiful but the video doesn't match"

**Prevention:**
1. **Engine capability matrix** in `references/video-engine-comparison.md` (extend existing doc): what each engine CAN and CANNOT do for transitions
2. **Physics precheck extension:** existing `physics_precheck` (Phase 39 v6.0) — extend to check transition feasibility. "match-cut via shared object" requires shared_object present in both frames; "motion-vector match" requires camera motion continuity
3. If cinematographer's design exceeds engine capability, **degrade gracefully to post-production equivalent** ("match-cut via shared object" → editor does manual cut on action at shared object frame)
4. Document fallback paths explicitly per transition_method

**Detection:** physics_precheck (existing) + transition feasibility extension.

**Phase that should address:** TRANSITION design + generation phases.

---

## Phase-Specific Warnings Summary

| Phase Topic | Likely Pitfall | Severity | Mitigation |
|---|---|---|---|
| Phase 0 / lineage impact assessment | X-1 (lineage cascade), X-4 (curator drift) | BLOCKER / WARNING | Audit all SKILL.md to be touched; freeze curator `--live` |
| FORM Phase 1 (refs authoring) | F-1 (creative assumptions break), F-3 (form-agnostic LLM output) | BLOCKER / WARNING | Author `horizontal-screen-framing.md` first; audit 15 experts |
| FORM Phase (Step 14) | F-2 (variant aspect ratios) | BLOCKER | 4-cell reframe matrix per master × platform |
| DUB phase | D-1 (doubled audio), D-2 (operator wavs), D-3 (ComfyUI dep hell), D-6 (project reconstruction) | BLOCKER × 2 / WARNING × 2 | Schema enforcement + operator-handoff + dependency pinning |
| IMG phase (orchestrator) | I-1 (vision-verify bottleneck), I-3 (async retry write order) | WARNING / BLOCKER | Batch vision-verify; sync queue model |
| IMG phase (templates) | I-4 (RHD/LHD), D-5 (GPU contention) | WARNING | Verify-retry loop; P10/P11 sequencing |
| TRANSITION design phase | T-1 (LTX FLF assumption), T-2 (cinematographer vs editor), T-3 (schema migration), T-4 (canvas registration) | BLOCKER × 3 / CRITICAL ASSUMPTION | Verify LTX workflow registry; explicit ownership table; backward-compat reader; 3-system registration |
| TRANSITION generation phase | T-5 (API quota), T-6 (routing complexity), T-7 (voice continuity), T-8 (creative exceeds capability) | WARNING × 4 | Wan-FLF2V default; declarative routing; voice continuity audit; physics_precheck extension |
| VALIDATE phase | All cross-cutting (X-1, X-2, X-3) | BLOCKER | Lineage audit, META-RULE test count, cross-repo commit pin |

---

## Invariant Violation Quick-Reference

**Found-08 violations to PREVENT (BLOCKER if violated):**
- Creating new `expert_id` for transition design (use cinematographer + editor ownership split instead)
- Silently renaming / removing existing `next_shot_link` field (use backward-compat reader)
- Mutating `expert_id` / `related_skills` / `status` frontmatter in any SKILL.md (preserve byte-identical)

**INFRA-04 violations to PREVENT (BLOCKER if violated):**
- Adding `asyncio.gather` for parallel transition engine calls (keep sync `@contextmanager` pattern from v13.0 P67)
- Adding per-metric GLM log calls in IMG SLA tracking (use local MetricsBuffer)
- Lifting `MAX_CONCURRENT_GL` above 1 during v14.0 execution

**EVAL-06 violations to PREVENT (BLOCKER if violated):**
- Flipping curator `--live` mid-milestone (preserve dry-run default)
- Skipping pre-tick bias canary before curator runs on v14.0-touched files

**Lineage L1-L6 violations to PREVENT (BLOCKER if violated):**
- Editing `~/.hermes/agents/*.agent.yaml` directly without re-running v13.0 P62 transform
- Failing to update `source_sha` / `transform_rule_id` / `transform_timestamp` on touched SKILL.md
- Letting `agent.yaml.source_sha` drift from `sha256(SKILL.md body)` (CI assertion needed)

---

## Sources

**Primary (HIGH confidence, local files):**
- `/data/workspace/hermes-agent/.planning/PROJECT.md` — v14.0 milestone definition + 4-track scope
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` — 30+ documented existing pitfalls (line 507-691) including the recurring META-RULE pattern
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` — shot intent + E-Konte Layer 5 ownership, `next_shot_link` field
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md` — Layer 5 schema with `cut_transition_type` + `next_shot_link`
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/vertical-screen-framing.md` — vertical-only framing rules (load-bearing for FORM pitfalls)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/editor/SKILL.md` — editor's existing transition design ownership (workflow step 7, line 197)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-capability-matrix.md` — LTX MSR vs FLF orthogonality (T-1 finding)
- `/data/workspace/kais-hermes-skills/skills/kais-movie/kais-aigc-platform/references/ltx-video-workflows.md` — workflow registry including `fflf` + `singularityFFLF` (T-1 verification)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/video-engine-comparison.md` — existing selection rules + Wan2.2-Animate role
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/prompt-design-standards.md` — GoalBuilder 6-segment template + MUST/MUST NOT count_constraints
- `/data/workspace/hermes-agent/.planning/MILESTONES.md` — FOUND-08 / INFRA-04 / EVAL-06 history across v1-v13

**Sibling research docs (this directory):**
- `.planning/research/v14-4track-upgrade/STACK.md` — CosyVoice 2.0-0.5B selection rationale, ComfyUI node pick, Wan2.2 FLF2V recommendation
- `.planning/research/v14-4track-upgrade/FEATURES.md` — feature landscape + LTX FLF correction (T-1 corroboration)

**Memory (Kai's preferences, persistent):**
- `~/.claude/projects/.../MEMORY.md` — `feedback-glm-overload-reduce-concurrency.md` (INFRA-04 + MAX_CONCURRENT_GL=1), `hermes-native-expert-agents.md` (agent vs skill separation), `notion-architecture-3.md` (lineage invariants)

**Confidence gaps (flagged for spike validation):**
- T-1 LTX MSR+FLF orthogonality: HIGH confidence (verified via capability matrix + workflow registry), but the no-combined-workflow claim should be re-verified against ComfyUI workflow registry at execution time
- D-3 ComfyUI CosyVoice node maturity: MEDIUM (STACK.md notes "v3 才 7 个月大, ComfyUI 节点实测反馈少") — first install may surface dependency surprises
- I-6 image2image reference count scaling: WATCH (no public data on dreamina's N-ref tolerance)
