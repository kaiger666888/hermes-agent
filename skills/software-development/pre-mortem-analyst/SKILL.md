---
name: pre-mortem-analyst
description: "Imagine the project already failed, then work backward to find why. More powerful than risk assessment because it assumes failure is certain. Use when user says 'pre-mortem', 'premortem', 'imagine this failed', 'what could go wrong', 'risk analysis', 'before we launch', 'stress test', 'what would kill this', 'project risks'."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Pre-Mortem, Risk-Analysis, Project-Planning, Prospective-Hindsight, Decision-Making]
    category: software-development
    related_skills: [plan, thinking-partner, requesting-code-review]
---

# Pre-Mortem Analyst

## Why Pre-Mortem > Risk Assessment

**Risk Assessment:** "What MIGHT go wrong?" → Optimism bias filters answers
**Pre-Mortem:** "It's 6 months later. It FAILED. Why?" → Liberates honest analysis

Research: Pre-mortems increase problem identification by 30%.

## The Process

1. **Set the scene:** "It's [date]. This has failed completely."
2. **Brainstorm causes:** List 10+ failure reasons (no filtering)
3. **Categorize:** People, Process, Technology, External
4. **Rate:** Likelihood × Impact (H/M/L)
5. **Prevent:** Top 3 get specific mitigation actions
6. **Monitor:** Define early warning signs

## Output Format

```
PROJECT: [Name]
FAILURE SCENARIO: "It's [date]. [Project] has completely failed."

WHY IT FAILED:

👥 PEOPLE: [Cause] - L×I: H/H | Prevent: [x] | Warning: [y]
⚙️ PROCESS: [Cause] - L×I: M/H | Prevent: [x] | Warning: [y]
💻 TECHNOLOGY: [Cause] - L×I: L/H | Prevent: [x] | Warning: [y]
🌍 EXTERNAL: [Cause] - L×I: M/M | Prevent: [x] | Warning: [y]

TOP 3 PRIORITIES:
1. [Risk] → [Specific action]
2. [Risk] → [Specific action]
3. [Risk] → [Specific action]

WARNING SIGNS TO MONITOR:
□ [Early indicator 1]
□ [Early indicator 2]
```

## Common Failure Categories

| Category | Common Causes |
|----------|---------------|
| **People** | Key person leaves, skill gaps, misalignment, low buy-in |
| **Process** | Aggressive timeline, scope creep, dependency issues |
| **Tech** | Doesn't scale, integration fails, security breach |
| **External** | Market shift, competitor move, regulation change |

## Integration

Compounds with:
- **`thinking-partner`** → Explore problem space before pre-mortem to surface hidden assumptions
- **`plan`** → Use pre-mortem output to inform plan risk-mitigation tasks
- **`requesting-code-review`** → Pre-mortem technology risks often surface as code-review priorities
- **First-principles decomposer** → Question hidden assumptions
- **Inversion strategist** → Create systematic avoidance strategies

## References

- `references/framework.md` — Detailed methodology: psychology, facilitation, 10 universal failure modes, prevention hierarchy
- `references/examples.md` — 3 worked pre-mortems (GolfTab launch, TISA Eindhoven school, TeddySnaps premium) + quick template
