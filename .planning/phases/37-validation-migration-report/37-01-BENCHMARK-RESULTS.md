---
phase: 37-validation-migration-report
authored: 2026-06-25
status: structural-pass / runtime-deferred-to-operator
requirements_covered: [VALIDATE-01, VALIDATE-02]
---

# Phase 37 — Structural Benchmark Results

**Authored:** 2026-06-25
**Status:** structural-pass / runtime-deferred-to-operator
**Scope:** VALIDATE-01 (skill benchmarks) + VALIDATE-02 (SOUL.md routing)

## Scope Clarification

Per `37-CONTEXT.md` decisions (Smart Discuss Auto-Accept — infrastructure classification), VALIDATE-01 and VALIDATE-02 live-runtime testing is **operator-scope**, not phase-scope. The reasons are honest and architectural:

- **VALIDATE-01 live runtime** requires a live tmux server + the relevant coding-agent CLIs (`claude` / `codex` / `opencode` / `pi`) actually installed and authenticated in the operator environment. Phase 37 is a documentation/validation phase without a live agent execution context.
- **VALIDATE-02 live runtime** requires an active hermes-agent conversation where the operator issues prompts and observes routing behavior. Phase 37 has no launched agent runtime.

Phase 37 therefore validates **structural preconditions** — file presence, frontmatter validity, invocation-form presence, rule completeness — and documents the runtime smoke-test commands for operator handoff. This is a **SCOPED BOUNDARY**, not a gap or failure: the plan acknowledges the operator-environment constraints up front (see `37-CONTEXT.md` §"VALIDATE-01" and §"VALIDATE-02" Limitation Acknowledgment) and hands off the runtime half with concrete commands in §"Operator Smoke-Test Commands" below.

This split mirrors the verifier decision in `35-VERIFICATION.md` (status: human_needed — structural all-pass, 2 SC require runtime observation) and `36-VERIFICATION.md` (status: human_needed — tooling-only, live run deferred to operator). Phase 37 inherits the same boundary for VALIDATE-01 and VALIDATE-02.

## VALIDATE-01 — Skill Benchmarks (Structural)

### coding-agent

**Benchmark prompt (per `37-CONTEXT.md` §VALIDATE-01):** "use claude code to fix a typo in README.md"
**Expected behavior:** skill discoverable + delegation command form documented.

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| File exists + line count | `[ -f skills/autonomous-ai-agents/coding-agent/SKILL.md ] && wc -l` | 160 lines | PASS |
| Frontmatter parses as valid YAML | `python3 -c "import yaml; yaml.safe_load(...)"` | `FRONTMATTER: OK` (exit 0) | PASS |
| 4 delegation targets documented | `grep -cE '^\*\*(Claude Code\|Codex\|OpenCode\|Pi):\*\*$'` | 4 | PASS |
| tmux launch form present (≥ 4) | `grep -cE 'terminal\(command="tmux new-session'` | 5 | PASS |
| Skill discoverable via dir walk | `find skills/autonomous-ai-agents -maxdepth 2 -name SKILL.md` | 6/6 skills (coding-agent included) | PASS |

**Delegation targets verified at launch blocks:**

- `**Claude Code:**` — `terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'claude --permission-mode bypassPermissions --print < \"$PROMPT\"'", pty=true)`
- `**Codex:**` — `terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'codex exec - < \"$PROMPT\"'", pty=true)`
- `**OpenCode:**` — `terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'opencode run < \"$PROMPT\"'", pty=true)`
- `**Pi:**` — `terminal(command="tmux new-session -d -s '$SESSION' -x 200 -y 50 -c /path/repo 'pi -p \"$(cat \"$PROMPT\")\"'", pty=true)`

Benchmark prompt "use claude code to fix a typo in README.md" → **STRUCTURAL: PASS** (skill discoverable; Claude Code launch block present at the documented invocation form). **RUNTIME: OPERATOR-SMOKE-TEST** (live tmux spawn + `claude` CLI fire requires operator environment — see §Operator Smoke-Test Commands).

### tmux-agents

**Benchmark prompt (per `37-CONTEXT.md` §VALIDATE-01):** "spawn a coding agent named test-session to do X"
**Expected behavior:** spawn form documented + skill discoverable.

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| File exists + line count | `[ -f skills/autonomous-ai-agents/tmux-agents/SKILL.md ] && wc -l` | 166 lines | PASS |
| Frontmatter parses as valid YAML | `python3 -c "import yaml; yaml.safe_load(...)"` | `FRONTMATTER: OK` (exit 0) | PASS |
| 4 H3 operations documented | `grep -cE '^### (Spawn\|List\|Check\|Attach)'` | 4 | PASS |
| tmux invocations present (≥ 8) | `grep -cE 'terminal\(command="tmux'` | 15 | PASS |
| Skill discoverable via dir walk | `find skills/autonomous-ai-agents -maxdepth 2 -name SKILL.md` | 6/6 skills (tmux-agents included) | PASS |

**Operations verified:**

- `### Spawn a new agent session` — `terminal(command="tmux new-session -d -s hermes-<task>-<rand4> -x 200 -y 50 -c /path/to/repo 'claude --dangerously-skip-permissions \"<task>\"'", pty=true)`
- `### List running sessions` — `terminal(command="tmux list-sessions", pty=false)`
- `### Check on a session (get results)` — `terminal(command="tmux capture-pane -t hermes-fixbug-a1b2 -p -S -50", pty=true)`
- `### Attach to watch live` — `terminal(command="tmux attach -t hermes-fixbug-a1b2", pty=true)`

Benchmark prompt "spawn a coding agent named test-session to do X" → **STRUCTURAL: PASS** (skill discoverable; spawn form documented at L49-55 with `hermes-<task>-<rand4>` session naming). **RUNTIME: OPERATOR-SMOKE-TEST** (live `tmux new-session` execution requires operator environment — see §Operator Smoke-Test Commands).

### Discoverability (both skills)

```
$ find skills/autonomous-ai-agents -maxdepth 2 -name SKILL.md | sort
skills/autonomous-ai-agents/claude-code/SKILL.md
skills/autonomous-ai-agents/codex/SKILL.md
skills/autonomous-ai-agents/coding-agent/SKILL.md
skills/autonomous-ai-agents/hermes-agent/SKILL.md
skills/autonomous-ai-agents/opencode/SKILL.md
skills/autonomous-ai-agents/tmux-agents/SKILL.md
```

**Result:** 6/6 skills discoverable via directory walk (the 4 existing + 2 migrated). **STRUCTURAL: PASS**. Hermes' skill discovery walk (`tools/skills_tool.py` per CLAUDE.md §"Skills loader") finds all 6 by virtue of the `SKILL.md` filename and directory layout; no registry edit required.

## VALIDATE-02 — SOUL.md Routing (Structural)

**Operator-state file:** `~/.hermes/SOUL.md` (4519 bytes, last modified 2026-06-25).

### Immediate-execution

**Benchmark prompts (per `37-CONTEXT.md` §VALIDATE-02):** "draw a cat", "tts hello world"
**Expected:** rule present + 6 trigger tokens listed.

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 即时执行 header present | `grep -nE '即时执行' ~/.hermes/SOUL.md` | L9: `### 即时执行命令 (Immediate Execution — Local Skill)` | PASS |
| 6 trigger tokens listed on the Triggers line | `grep -E '^- Triggers: .*(draw.*video.*tts.*run.*status.*queue)' ~/.hermes/SOUL.md` | match at L11 (all 6 tokens enumerated) | PASS |
| Routes-to line present | `grep -E 'Routes to: local AIGC skill execution' ~/.hermes/SOUL.md` | match at L12 | PASS |

Benchmark prompt "draw a cat" → **STRUCTURAL: PASS** (rule present, `draw` token in the trigger list, routes-to local AIGC skill execution). **RUNTIME: OPERATOR-SMOKE-TEST** (live routing observation requires hermes conversation — see §Operator Smoke-Test Commands).

### Cognitive

**Benchmark prompts (per `37-CONTEXT.md` §VALIDATE-02):** "帮我设计剧本", "记住这个角色"
**Expected:** rule present with skill-discovery / mem0 / curator routing guidance.

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 认知 header present | `grep -nE '认知' ~/.hermes/SOUL.md` | L17: `### 认知类命令 (Cognitive — MCP / Memory / Skill)` | PASS |
| 5 sub-routes documented | `grep -cE '^#### ' ~/.hermes/SOUL.md` | 5 (规划/剧本类 / 记忆写入 / 记忆读取 / 复盘反思 / 学习进化) | PASS |
| 帮我设计 → skill-discovery | `grep -A2 '帮我设计' ~/.hermes/SOUL.md` | routes to skill discovery for planning/screenplay/scene-builder skills | PASS |
| 记住 → mem0 | `grep -A2 '记住' ~/.hermes/SOUL.md` | routes to memory write via mem0 backend | PASS |

Benchmark prompt "帮我设计剧本" → **STRUCTURAL: PASS** (cognitive rule present, `帮我设计` token listed under 规划/剧本类 sub-route routing to skill discovery). Benchmark prompt "记住这个角色" → **STRUCTURAL: PASS** (`记住` token listed under 记忆写入 sub-route routing to mem0). **RUNTIME: OPERATOR-SMOKE-TEST** for both.

### Expert-management

**Benchmark prompt:** "/expert"
**Expected:** rule present with curator/skill-discovery routing.

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 专家管理 header present | `grep -nE '专家管理' ~/.hermes/SOUL.md` | L61: `### 专家管理命令 (Expert Management)` | PASS |
| /expert trigger + curator routing | `grep -B1 -A1 '/expert' ~/.hermes/SOUL.md` | `/expert` triggers; routes to hermes slash commands + curator | PASS |

Benchmark prompt "/expert" → **STRUCTURAL: PASS** (rule present at L61-66, routes to curator-based expert management). **RUNTIME: OPERATOR-SMOKE-TEST**.

### Default

**Benchmark prompt (per `37-CONTEXT.md` §VALIDATE-02):** "今天天气怎么样"
**Expected:** default route to configured LLM (NOT GLM-4-flash hardcoded).

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 默认 header present | `grep -nE '默认' ~/.hermes/SOUL.md` | L69: `### 默认 (Default)` | PASS |
| GLM-4-flash literal absent (negative check) | `! grep -q "GLM-4-flash" ~/.hermes/SOUL.md` | 0 hits (absent as required) | PASS |
| Generic "configured local LLM" routing | `grep -E 'configured local LLM' ~/.hermes/SOUL.md` | match at L72 ("Routes to: configured local LLM (per cli-config.yaml model:)") | PASS |

Benchmark prompt "今天天气怎么样" → **STRUCTURAL: PASS** (default rule present at L69-73, routes to configured LLM, `GLM-4-flash` correctly dropped per `35-01-TRANSFORMATION-NOTE.md` §6). **RUNTIME: OPERATOR-SMOKE-TEST**.

### Non-destructive contract

Verifies the original Hermes identity was preserved byte-for-byte and the integration is properly source-tagged (per Phase 35 SC #3).

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Original Hermes identity preserved | `head -1 ~/.hermes/SOUL.md` | `You are Hermes Agent, an intelligent AI assistant created by Nous Research. You are helpful, knowledgeable, and direct. ... Be targeted and efficient in your exploration and investigations.` (515 bytes, full original paragraph) | PASS |
| 手/脑 two-agent framing dropped | `grep -c '你是"手"' ~/.hermes/SOUL.md` | 0 hits (absent as required) | PASS |
| Source tag `openclaw 迁移` count (≥ 5 required) | `grep -c "openclaw 迁移" ~/.hermes/SOUL.md` | 9 | PASS |
| Date tag `2026-06-25` count (≥ 5 required) | `grep -c "2026-06-25" ~/.hermes/SOUL.md` | 10 | PASS |

**Result:** Non-destructive contract holds. Original 515-byte Hermes identity preserved verbatim as Section A (opening paragraph pre-H2); all openclaw-origin routing rules source-tagged with both provenance (`openclaw 迁移`) and date (`2026-06-25`); the openclaw-specific `GLM-4-flash` literal and two-agent "手/脑" framing are correctly dropped (per `35-01-TRANSFORMATION-NOTE.md` §2 and §6). **STRUCTURAL: PASS**.

## Operator Smoke-Test Commands (Deferred Runtime Validation)

Each item: command + expected output + why-deferred. Run after Phase 37 closure to confirm runtime behavior end-to-end.

### 1. coding-agent live spawn

**Command (pick one delegation target — Claude Code shown):**
```
# From a hermes-agent conversation, trigger the coding-agent skill, e.g.:
# "use claude code to fix a typo in README.md"
# The skill should fire the documented launch form:
terminal(command="tmux new-session -d -s 'hermes-fixtypo-abcd' -x 200 -y 50 -c /path/repo 'claude --permission-mode bypassPermissions --print < \"$PROMPT\"'", pty=true)

# Verify the session is actually running:
terminal(command="tmux has-session -t 'hermes-fixtypo-abcd' 2>/dev/null && echo 'OK: running' || echo 'FAIL: not found'", pty=true)
```
**Expected:** `tmux has-session` returns exit code 0; the spawned Claude Code worker begins processing the prompt.
**WHY DEFERRED:** requires operator environment (live hermes runtime + tmux installed + `claude` CLI installed and authenticated). Structural preconditions verified above (file present, 4 delegation targets documented, invocation form syntactically valid).

### 2. tmux-agents live spawn / list / attach

**Commands:**
```
# Spawn:
terminal(command="tmux new-session -d -s hermes-test-session-a1b2 -x 200 -y 50 -c /path/to/repo 'claude --dangerously-skip-permissions \"echo hello\"'", pty=true)

# List (expect the new session to appear):
terminal(command="tmux list-sessions", pty=false)

# Get results (capture recent output):
terminal(command="tmux capture-pane -t hermes-test-session-a1b2 -p -S -50", pty=true)

# Cleanup:
terminal(command="tmux kill-session -t hermes-test-session-a1b2", pty=true)
```
**Expected:** `tmux list-sessions` includes `hermes-test-session-a1b2`; `capture-pane` shows pane content; kill-session returns exit 0.
**WHY DEFERRED:** requires live tmux server + coding-agent CLI in operator environment.

### 3. SOUL.md live routing

**Commands (issue from a hermes-agent conversation):**
```
# Immediate-execution (expect local skill invocation, NOT free-form LLM answer):
> draw a cat

# Default (expect default LLM chat — general-knowledge response):
> 今天天气怎么样

# Cognitive (expect skill-discovery / memory surface to fire):
> 帮我设计剧本
```
**Expected:** the three prompt classes route differently — immediate triggers AIGC skill execution, default goes to configured LLM, cognitive surfaces skill-discovery / mem0 / curator. Observe the routing split.
**WHY DEFERRED:** requires live hermes-agent runtime conversation; grep cannot verify behavioral routing. Matches `35-VERIFICATION.md` Human Verification items #1 and #2 verbatim.

### 4. Skill invocation smoke-test

**Commands (issue from a hermes-agent conversation):**
```
# Trigger coding-agent (expect skill discovery + delegation form to fire):
> use claude code to fix a typo in README.md

# Trigger tmux-agents (expect skill discovery + spawn form to fire):
> spawn a coding agent named test-session to review PR #123
```
**Expected:** the agent recognizes the skill trigger, surfaces the skill, and proposes the documented `terminal(command="tmux new-session ...")` form.
**WHY DEFERRED:** requires live hermes-agent runtime + tmux + agent CLIs. Structural skill discoverability verified above.

## Summary

| # | Check | Result |
|---|-------|--------|
| 1 | coding-agent exists (160 lines, valid YAML, 4 delegation targets) | STRUCTURAL: PASS |
| 2 | coding-agent invocation forms documented (5 tmux new-session occurrences) | STRUCTURAL: PASS |
| 3 | coding-agent discoverable via directory walk | STRUCTURAL: PASS |
| 4 | coding-agent live delegation chain (tmux spawn + CLI fire) | RUNTIME: OPERATOR-SMOKE-TEST |
| 5 | tmux-agents exists (166 lines, valid YAML, 4 H3 operations) | STRUCTURAL: PASS |
| 6 | tmux-agents invocation forms documented (15 tmux occurrences) | STRUCTURAL: PASS |
| 7 | tmux-agents discoverable via directory walk | STRUCTURAL: PASS |
| 8 | tmux-agents live spawn/list/attach/get-results | RUNTIME: OPERATOR-SMOKE-TEST |
| 9 | SOUL.md 即时执行 rule present with 6 trigger tokens | STRUCTURAL: PASS |
| 10 | SOUL.md 认知 rule present with 5 sub-routes | STRUCTURAL: PASS |
| 11 | SOUL.md 专家管理 rule present | STRUCTURAL: PASS |
| 12 | SOUL.md 默认 rule present; GLM-4-flash correctly dropped | STRUCTURAL: PASS |
| 13 | SOUL.md non-destructive contract (original Hermes identity preserved + source/date tagged) | STRUCTURAL: PASS |
| 14 | SOUL.md live routing observation across 3 prompt classes | RUNTIME: OPERATOR-SMOKE-TEST |

**Closing statement:** Structural preconditions for VALIDATE-01 and VALIDATE-02 are fully met — every grep/wc check returns the expected value, every frontmatter parses, every routing category is present with source + date tagging, and the non-destructive contract holds. Runtime verification (live tmux spawn, live hermes routing observation) is honestly handed off to the operator per the scoped-boundary decision in `37-CONTEXT.md` §"VALIDATE-01 Limitation Acknowledgment" and §"VALIDATE-02 Limitation Acknowledgment". The runtime deferral is a SCOPED BOUNDARY, not a gap — the structural preconditions documented here are the load-bearing artifacts; the runtime commands in §"Operator Smoke-Test Commands" complete the loop in the operator environment.
