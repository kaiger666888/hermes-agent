# Requirements: Hermes Agent — Kai's Personal Agent Platform

**Defined:** 2026-06-25
**Core Value:** 让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备的代码委派、自动化集成、文档协作、个人身份与记忆能力(v7.0 迁移目标)。

## v7.0 Requirements — openclaw → hermes-agent Primary Agent Migration

**Goal:** 把 openclaw 作为主 agent 时的关键能力(skills / 身份记忆)迁移到 hermes-agent,让 hermes-agent 接管主 agent 角色时保持能力对等。

**Scope confirmation (与 Kai 2026-06-25 对齐):**
- ✓ Skills: coding-agent + tmux-agents(其他 openclaw skills 暂缓)
- ✓ Identity: SOUL.md 增强(单一 SOUL.md,不建多 profile)
- ✓ Memory: USER.md 迁移 + 133 个 openclaw memory .md 文件 ingest 到 mem0 backend
- ✗ Out: feishu-* skills、acp-router、provider config(models.json)、sessions runtime state、多 profile 机制

### SKILL — Skill Migration

- [x] **SKILL-01**: `coding-agent` skill 从 `openclaw/skills/coding-agent/SKILL.md` 迁到 `skills/autonomous-ai-agents/coding-agent/SKILL.md`,在 hermes-agent 中可被发现、可被触发,4 个委派目标(Codex / Claude Code / Pi / OpenCode)全部正常
- [x] **SKILL-02**: `tmux-agents` skill 从 `openclaw/skills/openclaw-skills-tmux-agents/SKILL.md` 迁到 `skills/autonomous-ai-agents/tmux-agents/SKILL.md`,spawn / list / attach / get-results 功能文档完整且适配 hermes 调用模式
- [x] **SKILL-03**: 两个迁后 skill 的 frontmatter 完整适配 hermes `metadata.hermes.*` schema,包括 `tags[]`、`related_skills[]`、`expert_id`(如适用)、`metrics[]`(如适用)
- [x] **SKILL-04**: 两个 skill 的 prerequisites 从 openclaw `metadata.openclaw.requires.{anyBins,config}` 格式映射到 hermes `prerequisites: {tools, commands, credentials}` 格式,无开放依赖

### SOUL — Identity Enhancement

- [x] **SOUL-01**: openclaw `~/.openclaw/SOUL.md` 中的 AIGC 路由规则(即时执行命令 / 认知类命令 / 专家管理命令 / 默认)提取并整合进 `~/.hermes/SOUL.md`,**不覆盖** hermes 原有默认 SOUL 内容
- [x] **SOUL-02**: 路由规则从 openclaw 触发模式(本地 skill / MCP 调用)适配为 hermes 触发模式(slash commands / skill invocation / MCP / 直接对话),并在 SOUL.md 中显式标注来源(openclaw 迁移)与适配日期
- [x] **SOUL-03**: 原 openclaw SOUL.md 完整保留为 backup(`~/.hermes/SOUL.md.openclaw-backup-2026-06-25`),并在 `.planning/` 下产出 transformation note 记录每条规则的迁移去向

### MEM — Memory Ingestion

- [x] **MEM-01**: openclaw `~/.openclaw/workspace/USER.md` 迁到 `~/.hermes/memories/USER.md`,以 hermes 兼容格式(可在 frontmatter 标注 openclaw-origin + 迁移日期)
- [x] **MEM-02**: openclaw `~/.openclaw/workspace/memory/*.md` 共 133 个文件(1.3MB)全部 ingest 到 hermes mem0 memory plugin(`plugins/memory/mem0/`),作为长期记忆条目存储
- [x] **MEM-03**: Spot-check 通过 —— 从 hermes agent 内发起 5 个采样查询(覆盖 AIGC 部署、ComfyUI、Trellis、ACE-Step、CosyVoice 等主题),mem0 backend 能返回相关 ingested 内容
- [x] **MEM-04**: Ingestion 幂等 —— 重新运行 ingestion 命令不产生重复条目(基于内容 hash 或 openclaw 文件路径 dedup)

### VALIDATE — Validation & Documentation

- [ ] **VALIDATE-01**: 每个迁后 skill 用至少 1 个 benchmark prompt 测试触发 + 委派链路,确认无回归
- [ ] **VALIDATE-02**: 增强 SOUL.md 在 3+ 个测试 prompt 上产生预期路由行为(即时命令走本地、认知命令走 MCP、默认走 LLM)
- [ ] **VALIDATE-03**: Migration report `.planning/milestones/v7.0-MIGRATION-REPORT.md` 文档化所有 transform 决策 + 显式 skipped items(feishu-* / acp-router / models.json / sessions)及理由

## Future Requirements

延后到后续 milestone,本次 v7.0 不交付:

### FEISHU (deferred from v7.0)

- **FEISHU-01**: feishu-doc / feishu-drive / feishu-perm / feishu-wiki 4 个 skill 迁移(可能在 v8.0 或与 hermes feishu plugin 一并设计)
- **FEISHU-02**: 是否合并为单 `feishu` skill 的 4 子动作 vs 保留 4 独立 skill 的设计决策延后

### AGENT (deferred from v7.0)

- **AGT-01**: 多 hermes profile 机制(对应 openclaw 7 agents)是否引入的决策延后;v7.0 采用单一 SOUL.md 增强路径
- **AGT-02**: acp-router 是否在 hermes-agent 中以其他形式存在(例如 hermes 自己作为 ACP server 而非 client)延后评估

### ACP (deferred from v7.0)

- **ACP-01**: acp-router skill 是否迁移的决策延后;初步判断是 openclaw 内部调度器,hermes 中无意义

## Out of Scope

显式排除,防止 scope creep:

| Feature | Reason |
|---------|--------|
| Provider keys / models.json 迁移 | Kai 手动处理(本次 milestone 启动前已确认) |
| Feishu channel config | Kai 手动处理 |
| ACP config | Kai 手动处理 |
| `workspace/` 下 GB 级 AIGC 产出文件 | 与 agent 能力无关,留原处 |
| `agents/<name>/sessions/` 迁移 | Runtime state,无迁移价值,迁移可能引入状态错乱 |
| `agents/<name>/agent/auth-profiles.json` 迁移 | 与 provider config 同步,Out of scope |
| Movie-experts 后续深化 | 在另一 repo(kais-movie-agent)处理 |
| openclaw 本身的 deprecation / shutdown | 不在 hermes-agent 仓库范围内 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SKILL-01 | Phase 34 | Complete |
| SKILL-02 | Phase 34 | Complete |
| SKILL-03 | Phase 34 | Complete |
| SKILL-04 | Phase 34 | Complete |
| SOUL-01 | Phase 35 | Complete |
| SOUL-02 | Phase 35 | Complete |
| SOUL-03 | Phase 35 | Complete |
| MEM-01 | Phase 36 | Complete |
| MEM-02 | Phase 36 | Complete |
| MEM-03 | Phase 36 | Complete |
| MEM-04 | Phase 36 | Complete |
| VALIDATE-01 | Phase 37 | Pending |
| VALIDATE-02 | Phase 37 | Pending |
| VALIDATE-03 | Phase 37 | Pending |

**Coverage:**
- v7.0 requirements: 14 total
- Mapped to phases: 14 / 14 ✓
- Unmapped: 0

**Phase assignments:**
- Phase 34 — Skills Migration (coding-agent + tmux-agents): SKILL-01, SKILL-02, SKILL-03, SKILL-04
- Phase 35 — SOUL.md Identity Enhancement: SOUL-01, SOUL-02, SOUL-03
- Phase 36 — Memory Ingestion (USER.md + 133 .md → mem0): MEM-01, MEM-02, MEM-03, MEM-04
- Phase 37 — Validation & Migration Report: VALIDATE-01, VALIDATE-02, VALIDATE-03

---
*Requirements defined: 2026-06-25*
*Last updated: 2026-06-25 — Traceability table filled after Step 10 roadmap creation (Phase 34-37 assigned, coverage 14/14 ✓).*
