---
name: coding-agent
description: "Delegate coding work to Codex, Claude Code, OpenCode, or Pi as background tmux workers; not simple edits or read-only code lookup."
version: 1.0.0
author: "Hermes Agent + openclaw upstream"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Delegation, tmux, Codex, Claude-Code, OpenCode, Pi, Background-Worker]
    related_skills: [claude-code, codex, opencode, hermes-agent, tmux-agents]
---

# Coding Agent (tmux mode)

Use for background feature builds, PR reviews, large refactors, and issue-to-PR loops. Do not use for simple edits or read-only code lookup.

All subagents run inside persistent tmux sessions. This means they survive gateway restarts, SSH disconnects, and can be inspected with `tmux attach`.

## Hard rules

- Always launch inside a tmux session using `spawn_tmux` below.
- Use session name format: `hermes-<short-task-name>-<random4>`.
- Claude Code: use `claude --permission-mode bypassPermissions --print`.
- Codex, Pi, OpenCode: run inside tmux with PTY (tmux provides PTY natively).
- Capture a real notification route before spawning.
- Worker must send exactly one completion or failure message via the platform-appropriate delivery channel captured at spawn time (e.g. the active Telegram/Discord/Slack gateway channel).
- Do not rely on heartbeat, system events, or notify-on-exit hooks.
- Monitor with `tmux capture-pane` or `check.sh`; do not kill slow workers without cause.
- If user asked for a specific agent, use that agent.
- If worker fails/hangs, respawn or ask; do not silently hand-code instead.
- Never checkout branches or run background coding agents inside the hermes-agent repo itself (`~/Projects/hermes-agent` or wherever the repo lives); use an isolated checkout.

## Notification block

Append this shape to every worker prompt with real values:

```text
Notification route:
- channel: <notifyChannel>
- target: <notifyTarget>
- account: <notifyAccount or omit>
- reply_to: <notifyReplyTo or omit>
- thread_id: <notifyThreadId or omit>

When finished, send exactly one completion or failure message via the active gateway delivery channel (Telegram / Discord / Slack / etc.). Use channel=<channel>, target='<target>', and the brief result text. Add account/reply-to/thread-id only when present above.
Do not rely on heartbeat, system events, or notify-on-exit hooks.
```

If no trustworthy route exists, say completion auto-notify is unavailable.

## Prerequisites

- **tmux:** installed (`apt install tmux` / `brew install tmux`). Background sessions depend on it.
- **At least one of** the four coding-agent CLIs:
  - `claude` — see the `claude-code` skill for install + auth
  - `codex` — see the `codex` skill
  - `opencode` — see the `opencode` skill
  - `pi` — install per upstream Pi docs
- **Hermes gateway delivery channel active** (for completion notifications) — e.g. a Telegram/Discord/Slack session reachable from the running hermes-agent.

## Launch forms (tmux)

Write the worker prompt to a temp file first. This avoids shell quoting bugs when the required notification block contains quotes or newlines.

```bash
PROMPT=$(mktemp -t hermes-worker-prompt.XXXXXX)
cat >"$PROMPT" <<'EOF'
Task.
<notification block>
EOF
SESSION="hermes-$(echo $TASK | head -c20 | tr ' ' '-' | tr -cd 'a-zA-Z0-9-')-$(head -c4 /dev/urandom | xxd -p)"
printf 'session: %s  prompt: %s\n' "$SESSION" "$PROMPT"
```

Then launch in a tmux session:

**Claude Code:**

```
terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'claude --permission-mode bypassPermissions --print < \"$PROMPT\"'", pty=true)
```

**Codex:**

```
terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'codex exec - < \"$PROMPT\"'", pty=true)
```

**OpenCode:**

```
terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'opencode run < \"$PROMPT\"'", pty=true)
```

**Pi:**

```
terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'pi -p \"$(cat \"$PROMPT\")\"'", pty=true)
```

After spawning, verify the session exists:

```
terminal(command="tmux has-session -t '$SESSION' 2>/dev/null && echo 'OK: $SESSION running' || echo 'FAIL: $SESSION not found'", pty=true)
```

## Monitoring commands

```
# Check output (last N lines)
terminal(command="tmux capture-pane -t '$SESSION' -p -S -50", pty=true)

# Check if still running
terminal(command="tmux has-session -t '$SESSION' 2>/dev/null && echo running || echo done", pty=true)

# Send additional instructions
terminal(command="tmux send-keys -t '$SESSION' -l -- 'additional instruction' && tmux send-keys -t '$SESSION' Enter", pty=true)

# Send Ctrl-C to interrupt
terminal(command="tmux send-keys -t '$SESSION' C-c", pty=true)

# Kill session
terminal(command="tmux kill-session -t '$SESSION'", pty=true)
```

For an overview of all agent sessions, see the `tmux-agents` skill.

## Long issue-to-PR work

1. Create/reuse a GitHub issue as durable spec.
2. Include issue URL, repo, base branch, expected PR, proof, and notification route.
3. Tell worker to branch, implement, test, run review until no accepted actionable findings, open PR.
4. Return issue URL and session name immediately.
5. Monitor with `tmux capture-pane`; cancel with `tmux kill-session`.

## Scratch work (no existing repo)

```bash
SCRATCH=$(mktemp -d)
git -C "$SCRATCH" init
PROMPT=$(mktemp -t hermes-worker-prompt.XXXXXX)
cat >"$PROMPT" <<'EOF'
Build X.
<notification block>
EOF
SESSION="hermes-scratch-$(head -c4 /dev/urandom | xxd -p)"
terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c '$SCRATCH' 'codex exec - < \"$PROMPT\"'", pty=true)
```

## Status to user

- Say what started, where, and the tmux session name.
- Update only on milestone, worker question, error, user action needed, or finish.
- If killed, say why.
- Tell user they can watch with: `tmux attach -t <session-name>`

## Coexistence with other autonomous-ai-agents skills

This skill is the **unified delegation layer** for spawning background coding workers in tmux. For single-agent deep-dives (Claude Code / Codex / OpenCode standalone with full surface-area docs), invoke the dedicated skill (`claude-code`, `codex`, `opencode`, or `hermes-agent`) directly. For tmux session lifecycle management (spawn/list/attach/status across multiple agents), use the sibling `tmux-agents` skill.
