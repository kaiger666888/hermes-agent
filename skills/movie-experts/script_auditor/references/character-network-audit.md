# Character Network Audit (角色网络审计)

**Source:** Propp *Morphology of the Folktale* (1928) character-function typology + 短剧 character-network analysis (蝉妈妈 role-frequency reports 2024-2026).
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Quantitative rubric for scoring Dimension 4 (Character Network, 20 points) of the script audit. Evaluates whether the script has a clear protagonist, a strong antagonist relationship, and well-defined character functions.

## Heuristics

### Sub-metric 1: Protagonist identifiability (7 points)

**Composite metric:**
- `出场频率 = scenes_with_protagonist / total_scenes`
- `对话量占比 = protagonist_dialogue_lines / total_dialogue_lines`

**Health zone (both 男频 and 女频):**

| Metric | Healthy zone | Penalty outside zone |
|---|---|---|
| 出场频率 | 0.6-0.85 | < 0.6 → 主角缺席感;> 0.85 → 单人独白剧 |
| 对话量占比 | 0.40-0.60 | < 0.40 → 主角失声;> 0.60 → 抢戏 |

**Scoring:**
- Both metrics in health zone → 7
- One metric outside zone (mild) → 5
- One metric outside zone (severe) → 3
- Both outside zone → 1

### Sub-metric 2: Antagonist relationship (7 points)

**Required: explicit antagonist character with:**
- ≥ 1 direct confrontation with protagonist
- ≥ 1 scene where antagonist's goal conflicts with protagonist's goal
- ≥ 1 escalation across the episode/season

**Scoring:**
- Antagonist present + all 3 requirements → 7
- Antagonist present + 2 of 3 → 5
- Antagonist present + 1 of 3 → 3
- No明确 antagonist → 1

**Penalty:**
- 无明确对手角色 → -5 to base score
- Antagonist appears only in climax (no setup) → -3
- Antagonist's motivation unexplained → -2

### Sub-metric 3: Character functional clarity (6 points)

**Propp character-function typology (adapted for 短剧):**

| Function | Description |
|---|---|
| Hero / 主角 | Drives plot, audience identification point |
| Villain / 反派 | Opposes hero, creates central conflict |
| Donor / 援助者 | Provides resource/info to hero |
| Helper / 帮手 | Assists hero throughout |
| Princess / 目标 | Hero's goal object (person, status, truth) |
| Dispatcher / 任务发起者 | Sends hero on quest |
| False Hero / 伪英雄 | Impersonates hero, creates mistrust |
| Narrator / 旁白 | Provides exposition |

**Scoring criteria:**
- Every character has明确 functional role → 6
- 1-2 minor characters with unclear function → 4
- 3+ characters with unclear function → 2
- > 5 characters AND ≥ 3 with unclear function → 1

**Hard rule (character overload):**
- ≥ 5 characters with模糊 function → -3 (cognitive overload)
- ≥ 8 characters total (excluding background) → -2 (audience can't track)

### Special case: 男频 vs 女频 character expectations

**男频 短剧 character expectations:**
- Protagonist dialogue share leans 0.50-0.60 (power-fantasy narrative)
- Antagonist is个人 rival, not systemic force
- Donor/Helper often a romantic interest (or mentor figure)
- Princess-equivalent often a social status goal

**女频 短剧 character expectations:**
- Protagonist dialogue share leans 0.45-0.55 (often more ensemble)
- Antagonist often a romantic rival or in-law
- Donor often female friend / family
- Princess-equivalent often romantic / familial reconciliation

### Deduction rules

| Violation | Penalty |
|---|---|
| 无明确对手角色 | -5 |
| 主角在关键场景(高潮 / 卡点)缺席 | -4 |
| 角色 ≥ 5 个且功能模糊 | -3 |
| 角色 ≥ 8 个总数 | -2 |
| Antagonist motivation 完全未交待 | -2 |
| 主角对话占比 < 40% 或 > 60% | -2 |

### Hit-pattern reference (Top 10%)

| Metric | Mean | Std |
|---|---|---|
| 主角出场频率 | 0.74 | 0.06 |
| 主角对话占比 | 0.52 | 0.04 |
| 角色 total count | 4.2 | 1.1 |
| Function clarity rate | 95% | 4% |

### Miss-pattern reference (Bottom 30%)

| Metric | Mean | Std |
|---|---|---|
| 主角出场频率 | 0.48 | 0.12 |
| 主角对话占比 | 0.31 or 0.71 | bimodal |
| 角色 total count | 7.5 | 2.0 |
| Function clarity rate | 58% | 12% |

---

## Cross-references

- [`../../screenplay/references/dialogue-craft.md`](../../screenplay/references/dialogue-craft.md) — Dialogue density thresholds align with protagonist dialogue share
- [`../../performer/SKILL.md`](../../performer/SKILL.md) — Performer expert consumes character function assignments for body-language intensity calibration
