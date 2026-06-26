# /gsd Skill Command Reference

> 52 subcommands, typical workflow: new-project → discuss-phase → plan-phase → execute-phase → verify-work → ship

## Core Workflow (OpenClaw 应重点使用的)

| Command | Description | When OpenClaw Uses It |
|---------|-------------|----------------------|
| `/gsd:new-project` | Initialize project with PROJECT.md | Phase 3 启动时 |
| `/gsd:autonomous` | Run all remaining phases autonomously | **主力命令** - 自动 discuss→plan→execute |
| `/gsd:next` | Auto advance to next logical step | 推进流程 |
| `/gsd:progress` | Check progress, route to next action | 监控状态 |
| `/gsd:verify-work` | UAT validation | 里程碑完成时 |
| `/gsd:ship` | Create PR, review, merge | 最终交付 |
| `/gsd:pause-work` | Create context handoff | 上下文快满时 |
| `/gsd:resume-work` | Resume with full context | /clear 后恢复 |

## Context Management (关键 - 上下文快满时)

| Command | Description |
|---------|-------------|
| `/gsd:pause-work` | 保存当前上下文，创建 handoff |
| `/gsd:resume-work` | 从 handoff 恢复，含完整上下文 |
| `/gsd:session-report` | 生成会话报告 + token 用量 |
| `/gsd:thread` | 跨会话持久上下文 |

## Phase-Level Commands

| Command | Description |
|---------|-------------|
| `/gsd:discuss-phase` | Gather phase context through adaptive questioning |
| `/gsd:plan-phase` | Create detailed PLAN.md with verification loop |
| `/gsd:execute-phase` | Execute plans with wave-based parallelization |
| `/gsd:research-phase` | Research implementation approach |
| `/gsd:validate-phase` | Retroactive audit and fill gaps |
| `/gsd:add-phase` | Add phase to end of milestone |
| `/gsd:insert-phase` | Insert urgent work as decimal phase |
| `/gsd:ui-phase` | Generate UI-SPEC.md for frontend phases |

## Milestone Management

| Command | Description |
|---------|-------------|
| `/gsd:new-milestone` | Start new milestone cycle |
| `/gsd:complete-milestone` | Archive completed milestone |
| `/gsd:audit-milestone` | Audit against original intent |
| `/gsd:milestone-summary` | Generate comprehensive summary |

## Task Tracking

| Command | Description |
|---------|-------------|
| `/gsd:check-todos` | List pending todos |
| `/gsd:add-todo` | Capture task as todo |
| `/gsd:note` | Quick idea capture |
| `/gsd:add-backlog` | Add to backlog |
| `/gsd:review-backlog` | Review/promote backlog items |

## Workspaces & Parallel

| Command | Description |
|---------|-------------|
| `/gsd:workstreams` | Manage parallel workstreams |
| `/gsd:new-workspace` | Create isolated workspace |
| `/gsd:manager` | Interactive multi-phase command center |

## Utilities

| Command | Description |
|---------|-------------|
| `/gsd:do` | Auto-route text to right command |
| `/gsd:fast` | Execute trivial task inline, no overhead |
| `/gsd:quick` | Quick task with GSD guarantees |
| `/gsd:stats` | Project statistics |
| `/gsd:health` | Diagnose planning directory health |
| `/gsd:debug` | Systematic debugging with persistent state |
| `/gsd:forensics` | Post-mortem for failed workflows |
| `/gsd:settings` | Configure workflow toggles |
| `/gsd:set-profile` | Switch model profile |
| `/gsd:map-codebase` | Analyze codebase with parallel mappers |
| `/gsd:review` | Cross-AI peer review |
| `/gsd:add-tests` | Generate tests for completed phase |
| `/gsd:pr-branch` | Create clean PR branch |
| `/gsd:cleanup` | Archive completed phase directories |
| `/gsd:plant-seed` | Capture forward-looking idea with triggers |
| `/gsd:profile-user` | Generate developer behavioral profile |
| `/gsd:update` | Update GSD to latest version |
| `/gsd:reapply-patches` | Reapply local modifications after update |

## OpenClaw 交互策略

### 推荐流程 (auto-dev skill 应执行)

```
1. /gsd:new-project        → 初始化
2. /gsd:autonomous         → 自动跑完所有 phase (主力)
   或逐个控制:
   2a. /gsd:discuss-phase  → 收集上下文
   2b. /gsd:plan-phase     → 生成计划
   2c. /gsd:execute-phase  → 执行
3. /gsd:verify-work        → 验证
4. /gsd:ship               → 交付
```

### 上下文管理策略

```
上下文快满 → /gsd:pause-work → /clear → /gsd:resume-work
(比手动发摘要更可靠，GSD 自带完整的上下文恢复机制)
```

### /gsd:autonomous 是关键

这个命令会自动链式执行 discuss→plan→execute 每个剩余 phase。
OpenClaw 只需要：
1. 启动 /gsd:autonomous
2. 定期用 /gsd:progress 检查进度
3. 处理异常（卡住/错误）
4. 完成后 /gsd:verify-work → /gsd:ship
