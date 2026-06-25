---
name: tmux-agents
description: "Manage background coding agents in tmux sessions. Spawn Claude Code, Codex, Gemini, or other agents; check progress; get results."
version: 1.0.0
author: "Hermes Agent + clawdhub upstream"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, tmux, Background-Worker, Session-Management, Delegation, Parallel, Ollama]
    related_skills: [claude-code, codex, opencode, hermes-agent, coding-agent]
---

# Tmux Agents

Run coding agents in persistent tmux sessions. They work in the background while you do other things.

## Prerequisites

- **tmux:** installed (`apt install tmux` / `brew install tmux`).
- **At least one coding-agent CLI** for spawning: `claude`, `codex`, `gemini`, or an Ollama-backed variant. See the `claude-code`, `codex`, and `opencode` skills for install + auth details. For unified tmux-backed delegation across Codex / Claude Code / Pi / OpenCode, use the sibling `coding-agent` skill.
- **For local (free) agents:** Ollama installed + a coding model pulled (e.g. `ollama pull glm-4.7-flash`).

## Available Agents

Inventory of agents typically spawned via this skill. For per-agent install + auth deep-dives, invoke the dedicated skill (`claude-code`, `codex`, `opencode`).

### Cloud Agents (API credits)

| Agent | Command | Best For |
|-------|---------|----------|
| **claude** | Claude Code | Complex coding, refactoring, full projects |
| **codex** | OpenAI Codex | Quick edits, auto-approve mode |
| **gemini** | Google Gemini | Research, analysis, documentation |

### Local Agents (FREE via Ollama)

| Agent | Command | Best For |
|-------|---------|----------|
| **ollama-claude** | Claude Code + Ollama | Long experiments, heavy refactoring |
| **ollama-codex** | Codex + Ollama | Extended coding sessions |

Local agents use your machine's GPU — no API costs, great for experimentation!

## Operations

This skill exposes four core operations: **spawn**, **list**, **attach**, and **check (get results)**. Each is documented below with the hermes-native `terminal(command="...")` invocation pattern.

### Spawn a new agent session

The inline tmux equivalent of the upstream `scripts/spawn.sh` helper:

```
terminal(command="tmux new-session -d -s hermes-<task>-<rand4> -x 200 -y 50 -c /path/to/repo 'claude --dangerously-skip-permissions \"<task>\"'", pty=true)
```

Concrete examples (one per agent type, using the `hermes-<task>-<rand4>` session naming convention):

```
# Cloud (uses API credits)
terminal(command="tmux new-session -d -s hermes-fixbug-a1b2 -x 200 -y 50 -c /path/to/repo 'claude --dangerously-skip-permissions \"Fix login validation\"'", pty=true)

terminal(command="tmux new-session -d -s hermes-refactor-c3d4 -x 200 -y 50 -c /path/to/repo 'codex \"Refactor the auth module\"'", pty=true)

terminal(command="tmux new-session -d -s hermes-research-e5f6 -x 200 -y 50 -c /path/to/repo 'gemini \"Research caching strategies\"'", pty=true)

# Local (FREE — uses Ollama-backed Claude Code)
terminal(command="tmux new-session -d -s hermes-experiment-g7h8 -x 200 -y 50 -c /path/to/repo 'ollama-claude \"Rewrite entire test suite\"'", pty=true)
```

> **Upstream note:** The original `scripts/spawn.sh <name> <task> [agent]` helper (from the clawdhub source) bundles this same tmux invocation with friendlier argument parsing. It is not migrated into the hermes-agent repo; if you've cloned the upstream repo locally, `./skills/tmux-agents/scripts/spawn.sh <name> <task> [agent]` is equivalent.

### List running sessions

```
terminal(command="tmux list-sessions", pty=false)
```

> **Upstream note:** `scripts/status.sh` provides a formatted overview of all agent sessions; not migrated into hermes-agent.

### Check on a session (get results)

Capture recent pane output (the "get-results" operation):

```
terminal(command="tmux capture-pane -t hermes-fixbug-a1b2 -p -S -50", pty=true)
```

The `-S -50` flag grabs the last 50 lines. Increase the range for longer-running sessions.

> **Upstream note:** `scripts/check.sh <name>` wraps `tmux capture-pane` with formatting; not migrated into hermes-agent.

### Attach to watch live

```
terminal(command="tmux attach -t hermes-fixbug-a1b2", pty=true)
```

Detach with `Ctrl+B`, then `D`. The session keeps running in the background.

### Other operations

**Send additional instructions** to a running session:

```
terminal(command="tmux send-keys -t hermes-fixbug-a1b2 -l -- \"Now add unit tests for the fix\" && tmux send-keys -t hermes-fixbug-a1b2 Enter", pty=true)
```

**Kill a session** when done:

```
terminal(command="tmux kill-session -t hermes-fixbug-a1b2", pty=true)
```

## When to Use Local vs Cloud

| Scenario | Recommendation |
|----------|----------------|
| Quick fix, time-sensitive | Cloud (faster) |
| Expensive task, budget matters | Local |
| Long experiment, might fail | Local |
| Production code review | Cloud (smarter) |
| Learning/exploring | Local |
| Heavy refactoring | Local |

## Parallel Agents

Run multiple agents simultaneously. Mix and match cloud + local:

```
terminal(command="tmux new-session -d -s hermes-backend-j9k0 -x 200 -y 50 -c /path/to/repo 'claude --dangerously-skip-permissions \"Implement user API\"'", pty=true)
terminal(command="tmux new-session -d -s hermes-frontend-l1m2 -x 200 -y 50 -c /path/to/repo 'ollama-codex \"Build login form\"'", pty=true)
terminal(command="tmux new-session -d -s hermes-docs-n3o4 -x 200 -y 50 -c /path/to/repo 'gemini \"Write API documentation\"'", pty=true)
terminal(command="tmux new-session -d -s hermes-tests-p5q6 -x 200 -y 50 -c /path/to/repo 'ollama-claude \"Write all unit tests\"'", pty=true)
```

Check all at once:

```
terminal(command="tmux list-sessions", pty=false)
```

## Ollama Setup

Local agents require Ollama with a coding model:

```
# Pull recommended model
ollama pull glm-4.7-flash

# Configure tools (one-time)
ollama launch claude --model glm-4.7-flash --config
ollama launch codex --model glm-4.7-flash --config
```

## Tips

- Sessions persist even if hermes-agent restarts (tmux is the process owner, not the agent runtime).
- Use local agents for risky/experimental work.
- Use cloud for production-critical tasks.
- Check `tmux list-sessions` (or `tmux ls`) to see all active work.
- Kill sessions when done to free resources.

## Coexistence with other autonomous-ai-agents skills

This skill manages the **session lifecycle** of background coding agents (spawn / list / attach / get-results). For the unified delegation layer that picks between Codex / Claude Code / Pi / OpenCode with a structured notification block, use the sibling `coding-agent` skill. For single-agent deep-dives (full CLI surface area for one tool), invoke the dedicated skill (`claude-code`, `codex`, `opencode`, or `hermes-agent`) directly.
