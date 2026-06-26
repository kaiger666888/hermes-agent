---
name: auto-dev
description: "Automated full-stack development pipeline. Orchestrates research → MVP planning → repo creation → coding-agent delegation (Claude Code / Codex / OpenCode / Pi via tmux). Use when user says 'auto dev', '自动开发', '从零开始做一个', '帮我实现一个项目', or provides a project idea that needs full implementation from scratch."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Auto-Dev, Full-Stack, MVP, Orchestration, Coding-Agent, GSD]
    category: software-development
    related_skills: [coding-agent, tmux-agents, plan, hermes-agent-skill-authoring]
---

# Auto-Dev Pipeline

Hermes as PM/Orchestrator, coding-agent as Developer (Claude Code / Codex / OpenCode / Pi running in tmux). Fully autonomous loop until human verification.

## Pipeline Phases

### Phase 1: Research (deep-research skill)

Use the `deep-research` skill with `thinking_depth=medium` and `search_rounds=2-3` to scope the MVP:

```
Topic: "[user's task description] — MVP implementation research"
Focus: technical feasibility, tech stack options, key challenges, existing solutions
Goal: simplest path to a working MVP
```

Synthesize research into a concise MVP route (1 paragraph + bullet points).

### Phase 2: Repo Init

1. `gh repo create <project-name> --private --description "..."`
2. `git clone` to a workspace dir **outside** the hermes-agent repo (NEVER run auto-dev inside `~/Projects/hermes-agent` — see `coding-agent` hard rules)
3. Create `docs/archi/` structure:
   - `docs/archi/REQUIREMENTS.md` - Feature requirements (user stories, acceptance criteria)
   - `docs/archi/ARCHITECTURE.md` - Tech stack, component diagram, data flow
   - `docs/archi/MVP-PLAN.md` - Phased implementation plan with milestones
4. Git commit + push

Template references: see `references/templates.md` for `REQUIREMENTS.md` / `ARCHITECTURE.md` / `MVP-PLAN.md` skeletons.

### Phase 3: GSD Project Initialization (hermes-native)

In the new project repo (NOT hermes-agent), run hermes' native GSD workflow directly. Hermes is the primary agent, so there is no ACPX intermediary — hermes invokes `/gsd:new-project` as a slash command:

```
/gsd:new-project
```

Answer the AskUserQuestion prompts (hermes can answer autonomously in YOLO mode — see `references/gsd-commands.md`):

- Workspace mode: YOLO (auto-execute, no per-step confirmation) — fits auto-dev's autonomous loop
- Phase granularity: Standard (5-8 phases) — balanced for MVP
- Model profile: Balanced (Sonnet-class) — cost/quality balance

This creates:
- `.planning/config.json` (YOLO mode, balanced profile, standard granularity)
- `.planning/PROJECT.md` (generated from the user's idea + Phase 1 research)
- `.planning/STATE.md` (initial state)
- `.planning/ROADMAP.md` (after research→requirements→roadmap phases complete)

Then run `/gsd:research-phase`, `/gsd:requirements`, `/gsd:roadmap` (or let `/gsd:autonomous` chain them — see Phase 4).

### Phase 4: Coding-Agent Delegation (tmux-backed)

Spawn a coding worker via the `coding-agent` skill — it picks the right CLI (Claude Code / Codex / OpenCode / Pi) and wraps the entire tmux session lifecycle with a structured notification block.

**Spawn form (from coding-agent skill):**

```bash
PROMPT=$(mktemp -t hermes-worker-prompt.XXXXXX)
cat >"$PROMPT" <<'EOF'
Task: Execute /gsd:autonomous --from 1 to complete all phases of the project roadmap.

Notification route:
- channel: <notifyChannel>
- target: <notifyTarget>
- account: <notifyAccount or omit>
- reply_to: <notifyReplyTo or omit>
- thread_id: <notifyThreadId or omit>

When finished, send exactly one completion or failure message via the active gateway delivery channel (Telegram / Discord / Slack / etc.). Use channel=<channel>, target='<target>', and the brief result text. Add account/reply-to/thread-id only if present above.
Do not rely on heartbeat, system events, or notify-on-exit hooks.
EOF

SESSION="hermes-$(echo $TASK | head -c20 | tr ' ' '-' | tr -cd 'a-zA-Z0-9-')-$(head -c4 /dev/urandom | xxd -p)"

terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/to/project/repo 'claude --permission-mode bypassPermissions --print < \"$PROMPT\"'", pty=true)
```

Verify the session spawned:

```
terminal(command="tmux has-session -t '$SESSION' 2>/dev/null && echo 'OK: $SESSION running' || echo 'FAIL: $SESSION not found'", pty=true)
```

For Codex / OpenCode / Pi variants, see the `coding-agent` skill launch forms.

#### Monitor Loop

**Strategy A: /gsd:autonomous (推荐 - 最省交互)**
- Coding worker runs `/gsd:autonomous` which chains discuss → plan → execute for every remaining phase
- Hermes periodically checks via `tmux capture-pane -t '$SESSION' -p -S -50` or `/gsd:progress`
- Best for: clear requirements, MVP-scale projects

**Strategy B: Phase-by-phase control**
- Hermes sends `/gsd:discuss-phase N --auto` → `/gsd:plan-phase N --auto` → `/gsd:execute-phase N` per phase via tmux send-keys
- Inspect output between phases before advancing
- Best for: tighter control / harder projects

**Strategy C: /gsd:quick (small tasks)**
- For trivial work inside a phase: `/gsd:quick <task description>`
- Skips full milestone pipeline

#### Steering Decision Framework

| Coding worker output | Hermes action |
|---|---|
| Phase 完成等待输入 | `tmux send-keys -t '$SESSION' -l '/gsd:next' && tmux send-keys -t '$SESSION' Enter` |
| Error / build fail | `tmux send-keys -t '$SESSION' -l '/gsd:debug <error>' && tmux send-keys -t '$SESSION' Enter` |
| "需要你确认 X" | Decide autonomously based on requirements (YOLO mode should prevent this) |
| 上下文快满警告 | `/gsd:pause-work` → wait → `/gsd:resume-work` |
| `/gsd:autonomous` 完成 | `/gsd:verify-work` |
| 项目全部完成 | `/gsd:ship` → Phase 5 |
| 卡住 (3+ retries) | `/gsd:forensics` 分析，必要时通知人类 |

#### Context Continuity (关键)

**不要手动 /clear + 发摘要！** GSD 自带机制：
1. `/gsd:pause-work` — 保存完整上下文到 .planning/
2. `/clear` — 清空 worker 上下文
3. `/gsd:resume-work` — 从 .planning/ 恢复完整上下文

### Phase 5: Human Verification

When all milestones are complete:
1. Run tests if any: `cd <repo> && npm test / pytest etc.`
2. Summarize what was built with repo link
3. Notify human: "项目开发完成，请 review: <repo-url>"
4. Wait for human feedback
5. If changes needed → back to Phase 4 with specific feedback via tmux send-keys

## Hard Constraints

- **Never run inside hermes-agent's own repo.** Always clone/create a separate workspace dir. The `coding-agent` skill forbids this — auto-dev inherits the rule.
- **Always create private repos by default** (`gh repo create --private`).
- **Never commit secrets or API keys.**
- **Capture a real notification route before spawning** — copy the notification block from the active gateway channel (Telegram/Discord/Slack) at spawn time.
- **Maximum 10 steering rounds without human check-in** — notify progress after 10 rounds.
- **If any phase fails 3 times, stop and notify human** — don't keep retrying with the same broken approach.

## Key Commands Reference

```bash
# Phase 1: Research via deep-research skill (invoked as a slash skill)
/skill deep-research

# Phase 2: Repo create
gh repo create <name> --private --description "MVP: ..."

# Phase 3: GSD init (hermes-native slash commands, NO ACPX intermediary)
/gsd:new-project
/gsd:autonomous        # or /gsd:discuss-phase N → /gsd:plan-phase N → /gsd:execute-phase N

# Phase 4: Spawn coding worker (coding-agent skill handles tmux session)
#   see skills/autonomous-ai-agents/coding-agent/SKILL.md for full spawn forms

# Monitoring (from coding-agent + tmux-agents skills)
terminal(command="tmux capture-pane -t '$SESSION' -p -S -50", pty=true)   # check output
terminal(command="tmux has-session -t '$SESSION' && echo running || echo done", pty=true)
terminal(command="tmux send-keys -t '$SESSION' -l -- 'next instruction' && tmux send-keys -t '$SESSION' Enter", pty=true)
terminal(command="tmux kill-session -t '$SESSION'", pty=true)
```

For the full GSD command reference (52 subcommands), see `references/gsd-commands.md`.

## When to use which skill

- **`auto-dev` (this skill)** — full pipeline from idea → repo → MVP → verified build. Use when given a greenfield project idea.
- **`coding-agent`** — just spawn a coding worker for an existing task in an existing repo. Use when the project already exists.
- **`plan`** — just write an implementation plan (no execution). Use when the user wants a plan, not a build.
- **`tmux-agents`** — manage multiple background coding sessions at the lifecycle level (list/attach/status/kill). Use for multi-session coordination.

## Prerequisites

- **Hermes slash commands** available (`/gsd:new-project`, `/gsd:autonomous`, etc.) — provided by the GSD skills plugin
- **tmux installed** — required for background session persistence (`apt install tmux` / `brew install tmux`)
- **At least one of** Claude Code / Codex / OpenCode / Pi CLIs installed and authenticated — see `coding-agent` skill for per-CLI install links
- **GitHub CLI (`gh`)** installed and authenticated — for repo creation in Phase 2
- **A hermes gateway delivery channel active** (Telegram / Discord / Slack) — for completion notifications from the coding worker
