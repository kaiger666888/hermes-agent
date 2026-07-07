# Phase 62: EXPERT-YAML-TRANSFORM - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart-discuss Sub-step 3 skip)

<domain>
## Phase Boundary

把 12 个 active expert 的 SKILL.md 从 `kais-hermes-skills` repo 全量 transform 成 `~/.hermes/agents/{name}.agent.yaml`,让 v11.0 已 ship 的 9 个 agent YAML 加上本批 12 个新 YAML,在 `~/.hermes/agents/` 下达成 **21 total**(9 已 ship + 12 新增),从而满足 v10.0 设计假设的「15 active DAG + redirect stubs 覆盖」。

**Transform 范围(12 个 active expert):**
`animation_studio / colorist / compliance_gate / creative_source / documentary_maker / performer / production / prompt_injector / scene_builder / script_auditor / storyboard_designer / visual_executor`

**Source(只读):** `/data/workspace/kais-hermes-skills/skills/movie-experts/{name}/SKILL.md`
**Target(本 phase 写入):** `~/.hermes/agents/{name}.agent.yaml`
**Transform rules:** `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md §2` 75-cell table(per-agent rule IDs cited in transform log)
**Schema:** `.planning/research/v10-orchestrator-design/agents-schema.yaml`(Draft 2020-12,Phase 45 stable,18 fields camelCase)

**Strictly out of scope:**
- 修改 kais-hermes-skills repo 的 SKILL.md(lineage invariants L1-L6,只读)
- 修改已 ship 的 9 个 agent YAML(它们 lineage 已 locked,不动)
- Agent registry load / round table smoke(Phase 63 处理)
- OBSERVABILITY metrics 收集(Phase 67 处理)

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation choices are at Claude's discretion — pure infrastructure phase per autonomous-smart-discuss Sub-step 3 detection:
- Goal keywords match: "transform", "migration"
- All 4 SCs are technical(file exists / jsonschema validate exits 0 / grep finds non-empty / per-agent transform log emitted)
- No user-facing behavior described

Use ROADMAP phase goal + success criteria + `04-MIGRATION-PATH.md §2` 75-cell transform table + existing 9 ship'd agent YAMLs as canonical patterns to guide decisions.

### Locked-from-prior-phases(v10.0 + v11.0)

以下决策已在 v10.0-v12.0 锁定,本 phase 直接沿用,不在 plan 中重新讨论:

- **Schema:** `agents-schema.yaml` Draft 2020-12,18 fields camelCase(Phase 45 stable)。`byte-pass jsonschema.Draft202012Validator.validate()` 是 SC#2 的硬约束
- **Lineage 字段必填:** `source_sha` + `transform_rule_id` + `transform_timestamp`(本 phase SC#3 硬约束)+ 已 ship YAML 使用的 `derived_from_skill_id` / `derived_from_repo` / `transform_date` / `skill_sha256` / `transform_notes`
- **default_invocation:** `mcp_tool`(active DAG agents)— 与已 ship 的 9 个 active expert YAML 一致;`skill_fallback` 仅用于 redirect stubs(本 phase 12 个全部 active,无 stub)
- **round_table_eligible:** `true`(12 个全部 active expert,与 screenplay/style_genome 等已 ship 一致)
- **memory_scope:** `per_agent`(v11.0 default,与已 ship 9 个一致)
- **Source SKILL.md 只读:** lineage invariants L1-L6(Phase 48-49)— 计算 SHA 但不修改源文件
- **Source repo path:** `/data/workspace/kais-hermes-skills/skills/movie-experts/{name}/SKILL.md`(post-v9.0 cross-repo migration,commit f10495332)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- **9 个已 ship agent YAML** at `~/.hermes/agents/`(`screenplay / style_genome / editor / cinematographer / character_designer / continuity_auditor / hook_retention / theory_critic / audio_pipeline`)— 作为 canonical 结构模板,本 phase 12 个新 YAML 应与它们 byte-compatible
- **agents-schema.yaml** at `.planning/research/v10-orchestrator-design/agents-schema.yaml`(Draft 2020-12,18 camelCase fields)— SC#2 lint target
- **04-MIGRATION-PATH.md §2** at `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` — 75-cell per-agent transform rule table(THE authoritative rules source)
- **Codebase maps** at `.planning/codebase/{ARCHITECTURE,CONVENTIONS,STRUCTURE,STACK,INTEGRATIONS,TESTING}.md`(v11.0 maps shipped)— 参考 CONVENTIONS.md for YAML 编码 / UTF-8 / lineage field conventions

### Established Patterns

- **YAML frontmatter:** PyYAML 6.0.3 + ruamel.yaml 0.18.17(已 ship 的 9 个 YAML 用 PyYAML dump + UTF-8 编码,block style)
- **Lineage field pattern:** `lineage: { derived_from_skill_id, derived_from_repo, transform_date, transform_notes, skill_sha256 }`(已 ship 9 个 YAML 的实际字段)— 本 phase 新增 `source_sha` + `transform_rule_id` + `transform_timestamp`(SC#3 要求)
- **Persona rewrite pattern:** `persona` field 不是简单复制 SKILL.md body,而是重写为 first-person expert voice(参考 `screenplay.agent.yaml` lines 5-18 的 persona rewrite 例子)
- **Hooks/contracts preservation:** 关键 contract(例如 HOOK-09 emotion_curve marker arrays)必须在 `transform_notes` 中显式标注「do NOT lose in transform」(screenplay YAML lines 31-34 是范例)
- **Tools whitelist:** active expert = `[hermes_llm, read_file, search_files, write_file, patch]`(参考 screenplay YAML lines 19-24);不同 expert 可能扩展(例如 visual_executor 可能需要 image_gen / scene_step tools)
- **`related_agents` 协作图:** 必须从 SKILL.md 的 `related_skills` 字段提取并改名为 `related_agents`,保持 graph connectivity(screenplay YAML lines 52-58 是范例)
- **`tags / metrics / prerequisites / platforms`** 沿用 SKILL.md frontmatter 字段(camelCase + lowercase hyphen tags)
- **SHA computation:** `skill_sha256` / `source_sha` = SHA-256 of source SKILL.md content at transform time(`hashlib.sha256(content.encode('utf-8')).hexdigest()`)

### Integration Points

- **`~/.hermes/agents/` registry loader:** Phase 63 会启动 agent registry 加载全部 21 agents,本 phase 产出的 12 个新 YAML 必须 byte-pass schema 才不会让 registry 加载失败
- **Round table executor:** Phase 63 SC#3 会用 `visual_executor` 作为最复杂 case(sub_steps: [drawer, animator])做 round table smoke — 本 phase 的 `visual_executor.agent.yaml` 必须正确表达 sub_steps 字段(若 schema 支持)
- **Lineage audit trail:** v10.0 design 假设 lineage 字段是 forward audit trail(source_sha 让任何 agent YAML 可追溯到源 SKILL.md commit);本 phase 必须为 12 个新 YAML 都 populate 这些字段

</code_context>

<specifics>
## Specific Ideas

No specific requirements — pure infrastructure phase. ROADMAP SCs and `04-MIGRATION-PATH.md §2` are authoritative. Plan should:

1. **Read 04-MIGRATION-PATH.md §2** first to extract the 75-cell per-agent transform rule table(rule IDs + per-expert transform specifics)
2. **Read 9 已 ship agent YAMLs** as structural templates(尤其 `screenplay.agent.yaml` 的 persona rewrite + hooks preservation patterns)
3. **For each of 12 experts:** read source SKILL.md → compute SHA → apply transform rules → write `~/.hermes/agents/{name}.agent.yaml` → verify byte-pass schema → emit per-agent transform log entry citing rule IDs
4. **Validation gate:** all 12 YAMLs byte-pass `jsonschema.Draft202012Validator.validate()` against `agents-schema.yaml`(SC#2)
5. **Lineage gate:** grep finds non-empty `source_sha` + `transform_rule_id` + `transform_timestamp` in all 12 files(SC#3);spot-check 1 traces back to source SKILL.md commit SHA

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase, scope is fully captured by ROADMAP SCs + 04-MIGRATION-PATH.md §2 transform rules.

</deferred>
