---
phase: 62
slug: expert-yaml-transform
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-08
---

# Phase 62 — Validation Strategy

> Per-phase validation contract for feedback sampling during the 12-expert SKILL.md → agent YAML transform.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python stdlib + `jsonschema==4.26.0` + `PyYAML==6.0.3` (no pytest needed — transform phase) |
| **Config file** | `pyproject.toml` (existing, no changes) |
| **Quick run command** | `python3 -c "import jsonschema, yaml, glob; schema=yaml.safe_load(open('.planning/research/v10-orchestrator-design/agents-schema.yaml','r',encoding='utf-8')); v=jsonschema.Draft202012Validator(schema); [v.validate(yaml.safe_load(open(p,'r',encoding='utf-8'))) for p in glob.glob('/home/kai/.hermes/agents/*.agent.yaml')]"` |
| **Full suite command** | `python3 scripts/validate_phase62_yamls.py` (12-YAML batch validation script — Wave 0 task) |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit (per-YAML write):** Run quick command on that single YAML — instant schema validation
- **After every plan wave (batch of 6 or 12):** Run full suite across all new YAMLs
- **Before `/gsd:verify-work`:** Full suite must be green + spot-check lineage SHA trace
- **Max feedback latency:** 5 seconds (per-YAML jsonschema validation is sub-second)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 62-01-01 | 01 (validator script) | 0 | EXPERT-02 | T-52-04 (undeclared field injection) | `additionalProperties: false` enforced via Draft202012Validator | unit | `python3 scripts/validate_phase62_yamls.py --help` exits 0 | ❌ W0 | ⬜ pending |
| 62-02-01 | 02 (batch A: 6 experts) | 1 | EXPERT-01 | — | 6 YAMLs exist at `~/.hermes/agents/{name}.agent.yaml` | smoke | `ls ~/.hermes/agents/{animation_studio,colorist,compliance_gate,creative_source,documentary_maker,performer}.agent.yaml \| wc -l` → 6 | ❌ W0 | ⬜ pending |
| 62-02-02 | 02 | 1 | EXPERT-02 | T-52-04 | All 6 YAMLs byte-pass `Draft202012Validator.validate()` | unit | `python3 scripts/validate_phase62_yamls.py --batch A` exits 0 | ❌ W0 | ⬜ pending |
| 62-02-03 | 02 | 1 | EXPERT-03 | — | All 6 YAMLs have `lineage.skill_sha256: <64-hex>` non-empty | unit | `grep -E "^  skill_sha256: [a-f0-9]{64}$" ~/.hermes/agents/{6 names}.agent.yaml \| wc -l` → 6 | ❌ W0 | ⬜ pending |
| 62-02-04 | 02 | 1 | EXPERT-03 | — | All 6 YAMLs `transform_notes` cite §2 rule IDs | unit | `grep -c "Rule IDs:" ~/.hermes/agents/{6 names}.agent.yaml \| awk -F: '{s+=$2} END {print s}'` → ≥6 | ❌ W0 | ⬜ pending |
| 62-03-01 | 03 (batch B: 6 experts incl. visual_executor) | 1 | EXPERT-01 | — | 6 YAMLs exist (incl. visual_executor with sub_steps expressed in persona) | smoke | `ls ~/.hermes/agents/{production,prompt_injector,scene_builder,script_auditor,storyboard_designer,visual_executor}.agent.yaml \| wc -l` → 6 | ❌ W0 | ⬜ pending |
| 62-03-02 | 03 | 1 | EXPERT-02 | T-52-04 | All 6 YAMLs byte-pass schema (sub_steps NOT a top-level field) | unit | `python3 scripts/validate_phase62_yamls.py --batch B` exits 0 | ❌ W0 | ⬜ pending |
| 62-03-03 | 03 | 1 | EXPERT-03 | — | visual_executor persona references sub_steps `[drawer, animator]` | unit | `grep -E "(drawer|animator)" ~/.hermes/agents/visual_executor.agent.yaml \| wc -l` → ≥2 | ❌ W0 | ⬜ pending |
| 62-04-01 | 04 (lineage + log + registry smoke) | 2 | EXPERT-03 | T-52-01 (YAML tag injection — source SKILL.md read via `safe_load`) | Spot-check visual_executor SHA traces to source SKILL.md | integration | `python3 -c "import hashlib; src=open('/data/workspace/kais-hermes-skills/skills/movie-experts/visual_executor/SKILL.md','rb').read(); import yaml; doc=yaml.safe_load(open('/home/kai/.hermes/agents/visual_executor.agent.yaml','r',encoding='utf-8')); assert doc['lineage']['skill_sha256']==hashlib.sha256(src).hexdigest()"` exits 0 | ❌ W0 | ⬜ pending |
| 62-04-02 | 04 | 2 | EXPERT-01 | — | 21 total agents loadable via v11.0 `agent/registry_loader.py` (no errors) | integration | `python3 -c "import sys; sys.path.insert(0,'.'); from agent.registry_loader import load_registry; r=load_registry(); assert len(r.agents)==21"` exits 0 | ❌ W0 | ⬜ pending |
| 62-04-03 | 04 | 2 | EXPERT-02 | — | Transform log emitted at `.planning/phases/62-expert-yaml-transform/62-TRANSFORM-LOG.md` citing per-agent rule IDs | smoke | `test -f .planning/phases/62-expert-yaml-transform/62-TRANSFORM-LOG.md && grep -c "rule_id:" .planning/phases/62-expert-yaml-transform/62-TRANSFORM-LOG.md` → 12 entries | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/validate_phase62_yamls.py` — batch validation script (`jsonschema.Draft202012Validator` against `agents-schema.yaml`, accepts `--batch A` / `--batch B` / no-flag=all 21)
- [ ] No pytest fixtures needed — transform phase uses inline `python3 -c` + script-based validation
- [ ] `pyproject.toml` already pins `PyYAML==6.0.3` + `jsonschema` (transitive via v11.0 deps) — no dep install needed

*Existing v11.0 infrastructure (`agent/registry_loader.py`) covers the integration smoke at task 62-04-02.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Persona text quality (first-person expert voice, preserves domain anchors) | EXPERT-03 (qualitative aspect) | LLM-judge or human review needed for tone/anchor preservation — schema only validates structure | Operator spot-reads 2-3 personas (e.g., visual_executor, colorist, prompt_injector) and confirms domain anchors present (e.g., visual_executor mentions drawer + animator + scene_step sequencing) |
| Transform log narrative coherence | EXPERT-03 (qualitative aspect) | Schema cannot judge whether rule ID citations are semantically correct per agent | Operator reads `62-TRANSFORM-LOG.md` and confirms each agent's cited rule IDs match its SKILL.md characteristics |

*All structural / quantitative behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (`scripts/validate_phase62_yamls.py`)
- [x] No watch-mode flags (single-shot validation)
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending planner/checker confirmation
